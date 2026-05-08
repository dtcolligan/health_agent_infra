"""Tests for the live Garmin pull adapter (`core/pull/garmin_live.py`).

Scope:
  - Adapter evidence-shape compatibility: live-adapter output matches the
    CSV adapter's shape on the same synthetic daily row.
  - Window assembly: adapter calls ``fetch_day`` once per day across
    ``history_days + 1`` dates and builds series in chronological order.
  - Per-field resilience: missing/None fields in the upstream response
    degrade cleanly (no crashes, ``raw_daily_row`` still emitted).
  - ``build_default_client`` raises ``GarminLiveError`` cleanly when
    ``garminconnect`` isn't importable, rather than leaking the
    ImportError.

The real ``garminconnect`` module is never imported by these tests — the
adapter depends on ``GarminLiveClient`` Protocol so we inject in-memory
clients.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from health_agent_infra.core.pull.auth import GarminCredentials
from health_agent_infra.core.pull.garmin_live import (
    RAW_DAILY_ROW_COLUMNS,
    GarminLiveAdapter,
    GarminLiveError,
    build_default_client,
)
from health_agent_infra.core.pull.protocol import FlagshipPullAdapter


# ---------------------------------------------------------------------------
# Fake clients
# ---------------------------------------------------------------------------

class ReplayClient:
    """Returns pre-seeded per-date rows. Records which dates were queried."""

    def __init__(self, rows_by_date: dict[date, dict]):
        self._rows = rows_by_date
        self.queried: list[date] = []

    def fetch_day(self, day: date) -> dict:
        self.queried.append(day)
        return dict(self._rows.get(day, {}))


def _day_row(d: date, **fields) -> dict:
    base = {"date": d.isoformat()}
    base.update(fields)
    return base


# ---------------------------------------------------------------------------
# Evidence shape vs. CSV adapter
# ---------------------------------------------------------------------------

def test_live_adapter_evidence_keys_match_csv_contract():
    """Live adapter must return the exact top-level key set the CSV
    adapter emits. Downstream code keys on these names."""

    as_of = date(2026, 4, 17)
    client = ReplayClient({as_of: _day_row(as_of, resting_hr=58, health_hrv_value=42,
                                           acute_load=400,
                                           sleep_deep_sec=3600,
                                           sleep_light_sec=10800,
                                           sleep_rem_sec=5400)})
    adapter = GarminLiveAdapter(client=client, history_days=0)
    pull = adapter.load(as_of)
    assert set(pull.keys()) == {
        "sleep", "resting_hr", "hrv", "training_load", "raw_daily_row"
    }


def test_live_adapter_conforms_to_flagship_pull_protocol():
    adapter = GarminLiveAdapter(client=ReplayClient({}))
    assert isinstance(adapter, FlagshipPullAdapter)
    assert adapter.source_name == "garmin_live"


def test_live_adapter_sleep_shape_matches_csv():
    """sleep dict shape: {record_id, duration_hours} or None."""
    as_of = date(2026, 4, 17)
    client = ReplayClient({as_of: _day_row(
        as_of,
        sleep_deep_sec=3600,
        sleep_light_sec=10800,
        sleep_rem_sec=5400,
    )})
    adapter = GarminLiveAdapter(client=client, history_days=0)
    sleep = adapter.load(as_of)["sleep"]
    assert sleep is not None
    assert set(sleep.keys()) == {"record_id", "duration_hours"}
    assert sleep["record_id"] == "g_sleep_2026-04-17"
    # 3600+10800+5400 = 19800 sec = 5.5h
    assert sleep["duration_hours"] == 5.5


def test_live_adapter_sleep_none_when_all_stages_missing():
    as_of = date(2026, 4, 17)
    client = ReplayClient({as_of: _day_row(as_of)})  # no sleep fields
    adapter = GarminLiveAdapter(client=client, history_days=0)
    assert adapter.load(as_of)["sleep"] is None


def test_live_adapter_series_skip_zero_and_missing():
    """Series helpers must mirror CSV adapter behavior: skip None and 0."""
    as_of = date(2026, 4, 17)
    prev = as_of - timedelta(days=1)
    prev2 = as_of - timedelta(days=2)
    client = ReplayClient({
        prev2: _day_row(prev2, resting_hr=0, health_hrv_value=None),  # both skipped
        prev: _day_row(prev, resting_hr=60, health_hrv_value=45),
        as_of: _day_row(as_of, resting_hr=58, health_hrv_value=48,
                        acute_load=400),
    })
    adapter = GarminLiveAdapter(client=client, history_days=2)
    pull = adapter.load(as_of)
    rhr = pull["resting_hr"]
    hrv = pull["hrv"]
    load = pull["training_load"]
    # Two rhr entries (prev, as_of); zero dropped.
    assert [r["bpm"] for r in rhr] == [60.0, 58.0]
    assert all(set(r.keys()) == {"date", "bpm", "record_id"} for r in rhr)
    assert [r["rmssd_ms"] for r in hrv] == [45.0, 48.0]
    assert [r["load"] for r in load] == [400.0]


def test_live_adapter_queries_full_window():
    as_of = date(2026, 4, 17)
    client = ReplayClient({})
    adapter = GarminLiveAdapter(client=client, history_days=14)
    adapter.load(as_of)
    # 15 days total: history_days + 1 (inclusive of as_of).
    assert len(client.queried) == 15
    assert client.queried[0] == as_of - timedelta(days=14)
    assert client.queried[-1] == as_of


def test_live_adapter_raw_daily_row_contains_canonical_column_keys():
    """Even when upstream gives sparse data, raw_daily_row has the full
    canonical key set so downstream code sees the same shape as CSV."""
    as_of = date(2026, 4, 17)
    client = ReplayClient({as_of: _day_row(as_of, resting_hr=58)})
    adapter = GarminLiveAdapter(client=client, history_days=0)
    raw = adapter.load(as_of)["raw_daily_row"]
    assert raw is not None
    # All canonical columns present; missing ones = None.
    missing = [c for c in RAW_DAILY_ROW_COLUMNS if c not in raw]
    assert missing == []
    assert raw["resting_hr"] == 58
    assert raw["sleep_deep_sec"] is None
    assert raw["date"] == "2026-04-17"


def test_live_adapter_raw_daily_row_none_when_as_of_row_absent():
    """If fetch_day returns empty for as_of, raw_daily_row should be the
    'missing-cells' row — not None — because _normalise_row always fills."""
    # The normaliser injects date even on empty input, so _extract_raw_daily_row
    # finds a matching row; all fields are None except date. This matches
    # the CSV adapter behavior when the CSV has a blank row for the date.
    as_of = date(2026, 4, 17)
    client = ReplayClient({})  # no rows at all
    adapter = GarminLiveAdapter(client=client, history_days=0)
    raw = adapter.load(as_of)["raw_daily_row"]
    assert raw is not None
    assert raw["date"] == "2026-04-17"
    assert raw["resting_hr"] is None


# ---------------------------------------------------------------------------
# Evidence-shape equivalence: live vs. CSV on synthetic row
# ---------------------------------------------------------------------------

def test_live_evidence_shape_parity_with_csv_on_synthetic_row(tmp_path):
    """Construct a synthetic CSV with the same numeric row the live adapter
    would produce, and assert both adapters emit byte-equivalent sleep +
    series + raw_daily_row subsets for overlapping keys."""

    import pandas as pd

    from health_agent_infra.core.pull.garmin import load_recovery_readiness_inputs

    as_of = date(2026, 4, 17)
    prev = as_of - timedelta(days=1)
    row_as_of = {
        "date": as_of.isoformat(),
        "resting_hr": 58,
        "health_hrv_value": 48,
        "acute_load": 400,
        "sleep_deep_sec": 3600,
        "sleep_light_sec": 10800,
        "sleep_rem_sec": 5400,
    }
    row_prev = {
        "date": prev.isoformat(),
        "resting_hr": 60,
        "health_hrv_value": 45,
        "acute_load": 380,
    }

    # Write CSV with these two rows. All other CSV columns omitted; pandas
    # will treat them as missing on read, which matches the live adapter's
    # None semantics.
    export_dir = tmp_path / "garmin" / "export"
    export_dir.mkdir(parents=True)
    csv_path = export_dir / "daily_summary_export.csv"
    pd.DataFrame([row_prev, row_as_of]).to_csv(csv_path, index=False)
    csv_pull = load_recovery_readiness_inputs(
        as_of, export_dir=export_dir, history_days=1
    )

    # Live adapter: feed the same two rows through ReplayClient.
    client = ReplayClient({prev: row_prev, as_of: row_as_of})
    live_pull = GarminLiveAdapter(client=client, history_days=1).load(as_of)

    # Sleep dicts are identical.
    assert live_pull["sleep"] == csv_pull["sleep"]
    # Series are identical sequences.
    assert live_pull["resting_hr"] == csv_pull["resting_hr"]
    assert live_pull["hrv"] == csv_pull["hrv"]
    assert live_pull["training_load"] == csv_pull["training_load"]
    # For raw_daily_row, check the keys common to both adapters carry the
    # same values. Live has the canonical fixed key set; CSV has whatever
    # the CSV header supplied, which is a subset here.
    for k, v in csv_pull["raw_daily_row"].items():
        assert live_pull["raw_daily_row"].get(k) == v, k


# ---------------------------------------------------------------------------
# build_default_client — bounded blocker on ImportError
# ---------------------------------------------------------------------------

def test_build_default_client_raises_live_error_when_garminconnect_missing(monkeypatch):
    """Simulate missing garminconnect by forcing an ImportError inside the
    helper. Must surface as GarminLiveError with actionable text."""

    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "garminconnect":
            raise ImportError("simulated: no garminconnect")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(GarminLiveError) as exc_info:
        build_default_client(GarminCredentials("alice@example.com", "pw"))
    assert "python-garminconnect" in str(exc_info.value)


def test_build_default_client_wraps_login_failure(monkeypatch):
    """A login exception from the upstream library must surface as a
    GarminLiveError with the original message chained — not leak the
    upstream type to CLI callers."""

    import sys
    import types

    class FakeGarmin:
        def __init__(self, email, password):
            self.email = email
            self.password = password

        def login(self):
            raise RuntimeError("auth blocked")

    fake_module = types.ModuleType("garminconnect")
    fake_module.Garmin = FakeGarmin
    monkeypatch.setitem(sys.modules, "garminconnect", fake_module)

    with pytest.raises(GarminLiveError) as exc_info:
        build_default_client(GarminCredentials("alice@example.com", "pw"))
    assert "Garmin login failed" in str(exc_info.value)
    assert "auth blocked" in str(exc_info.value)


def test_build_default_client_returns_usable_client(monkeypatch):
    """Happy path: the returned client satisfies fetch_day(date) -> dict."""

    import sys
    import types

    class FakeGarmin:
        def __init__(self, email, password):
            self._logged_in = False

        def login(self):
            self._logged_in = True

        def get_stats(self, iso):
            return {"totalSteps": 10, "restingHeartRate": 60}

        def get_sleep_data(self, iso):
            return {}

        def get_hrv_data(self, iso):
            return {}

        def get_training_readiness(self, iso):
            return []

        def get_training_status(self, iso):
            return {}

    fake_module = types.ModuleType("garminconnect")
    fake_module.Garmin = FakeGarmin
    monkeypatch.setitem(sys.modules, "garminconnect", fake_module)

    client = build_default_client(GarminCredentials("alice@example.com", "pw"))
    row = client.fetch_day(date(2026, 4, 17))
    assert row["date"] == "2026-04-17"
    assert row["steps"] == 10
    assert row["resting_hr"] == 60
