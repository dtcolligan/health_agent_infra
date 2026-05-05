"""v0.1.9 B5 — pull/clean provenance + fail-closed semantics.

Codex 2026-04-26 caught four divergences between what the README
promises and what the runtime does:

  5a. ``hai daily`` bypassed ``sync_run_log``; only ``hai pull`` wrote
      it. Source-freshness telemetry was inconsistent across paths.
  5b. ``_project_clean_into_state`` swallowed DB projection failures as
      stderr warnings. ``hai daily`` could plan over stale or absent
      accepted-state rows without the caller knowing.
  5c. ``hai clean`` invented a fresh ``export_batch_id`` from wall-clock
      time on every projection. Replaying identical evidence produced
      new raw provenance rows.
  5d. The intervals.icu adapter swallowed ``/activities`` errors but
      never set ``last_pull_partial = True``. Running domain saw
      "no sessions today" instead of "sessions unknown".

This file pins the v0.1.9 closures.
"""

from __future__ import annotations

import json
from argparse import Namespace
from contextlib import closing
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from health_agent_infra.cli import (
    _evidence_hash,
    _project_clean_into_state,
    main as cli_main,
)
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import initialize_database, open_connection


AS_OF = date(2026, 4, 26)
USER = "u_b5"


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _sample_raw_row(distance_m: float = 0.0) -> dict:
    """Minimal Garmin-shaped raw row for projection."""

    return {
        "date": AS_OF.isoformat(),
        "steps": 4000,
        "distance_m": distance_m,
        "active_kcal": 200,
        "total_kcal": 1800,
        "moderate_intensity_min": 0,
        "vigorous_intensity_min": 0,
        "resting_hr": 60,
        "sleep_total_sec": 7 * 3600,
    }


# ---------------------------------------------------------------------------
# 5c — idempotent export_batch_id
# ---------------------------------------------------------------------------


def test_evidence_hash_is_deterministic_for_same_payload():
    """Two calls with identical raw_row + activities yield identical hash."""

    raw = _sample_raw_row()
    activities = [{"activity_id": "a1", "as_of_date": AS_OF.isoformat()}]
    h1 = _evidence_hash(raw, activities)
    h2 = _evidence_hash(raw, activities)
    assert h1 == h2
    assert len(h1) == 16


def test_evidence_hash_differs_when_evidence_changes():
    raw1 = _sample_raw_row(distance_m=1000.0)
    raw2 = _sample_raw_row(distance_m=2000.0)
    assert _evidence_hash(raw1, []) != _evidence_hash(raw2, [])


def test_clean_replay_idempotent_at_raw_provenance_layer(tmp_path: Path):
    """v0.1.9 B5 fix: replaying identical evidence produces ONE
    source_daily_garmin row, not two. Pre-v0.1.9 the wall-clock
    export_batch_id meant every replay minted a fresh row."""

    db = _init_db(tmp_path)
    raw_row = _sample_raw_row()

    # First projection.
    result1 = _project_clean_into_state(
        str(db),
        as_of_date=AS_OF,
        user_id=USER,
        raw_row=raw_row,
        activities=[],
    )
    assert result1["status"] == "ok"

    # Replay with byte-identical evidence.
    result2 = _project_clean_into_state(
        str(db),
        as_of_date=AS_OF,
        user_id=USER,
        raw_row=raw_row,
        activities=[],
    )
    assert result2["status"] == "ok"
    # Same export_batch_id on both runs (deterministic from content).
    assert result1["export_batch_id"] == result2["export_batch_id"]

    # Source-row table has exactly one row, not two.
    with closing(open_connection(db)) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM source_daily_garmin WHERE as_of_date = ?",
            (AS_OF.isoformat(),),
        ).fetchone()[0]
    assert count == 1, (
        f"replay produced {count} source_daily_garmin rows; "
        f"v0.1.9 B5 contract requires idempotent replay"
    )


# ---------------------------------------------------------------------------
# 5b — fail-closed projection (smoke at the helper level)
# ---------------------------------------------------------------------------


def test_project_returns_skipped_db_absent_when_db_missing(tmp_path: Path):
    """No DB → status='skipped_db_absent', not silent None."""

    result = _project_clean_into_state(
        str(tmp_path / "missing.db"),
        as_of_date=AS_OF,
        user_id=USER,
        raw_row=_sample_raw_row(),
        activities=[],
    )
    assert result["status"] == "skipped_db_absent"
    assert result["error"] is None


def test_project_returns_ok_status_on_success(tmp_path: Path):
    db = _init_db(tmp_path)
    result = _project_clean_into_state(
        str(db),
        as_of_date=AS_OF,
        user_id=USER,
        raw_row=_sample_raw_row(),
        activities=[],
    )
    assert result["status"] == "ok"
    assert result["export_batch_id"] is not None
    assert result["error"] is None


# ---------------------------------------------------------------------------
# 5a + 5d — daily sync status mirrors pull partial telemetry
# ---------------------------------------------------------------------------


class _PartialDailyAdapter:
    """Adapter stub: daily evidence lands, but the adapter reports partial."""

    source_name = "intervals_icu"

    def __init__(self) -> None:
        self.last_pull_partial = False

    def load(self, as_of: date) -> dict:
        self.last_pull_partial = True
        return {
            "raw_daily_row": _sample_raw_row(),
            "activities": [],
            "sleep": None,
            "resting_hr": [],
            "hrv": [],
            "training_load": [],
        }


def test_daily_sync_row_records_partial_when_adapter_partial(tmp_path: Path):
    """``hai daily`` must preserve the adapter's partial-pull status in
    sync_run_log, matching ``hai pull``. Otherwise an intervals.icu
    activities failure can look like a fully fresh source row."""

    from health_agent_infra.cli import _daily_pull_and_project

    db = _init_db(tmp_path)
    args = Namespace(
        source="intervals_icu",
        live=False,
        db_path=str(db),
        history_days=14,
    )

    # W-29.2.9: `_build_intervals_icu_adapter` lives in cli.handlers.pull_clean.
    # `_daily_pull_and_project` (still in cli/__init__.py) references the
    # cli-side re-export binding, so both must be patched until W-29.2.11
    # moves _daily_pull_and_project to cli/handlers/recommend.py.
    with patch(
        "health_agent_infra.cli.handlers.pull_clean._build_intervals_icu_adapter",
        return_value=_PartialDailyAdapter(),
    ), patch(
        "health_agent_infra.cli._build_intervals_icu_adapter",
        return_value=_PartialDailyAdapter(),
    ):
        source_name, projected, _bundle = _daily_pull_and_project(
            args, as_of=AS_OF, user_id=USER, db_path=db,
        )

    assert source_name == "intervals_icu"
    assert projected is True

    with closing(open_connection(db)) as conn:
        row = conn.execute(
            "SELECT source, status, rows_pulled, rows_accepted "
            "FROM sync_run_log WHERE source = ?",
            ("intervals_icu",),
        ).fetchone()

    assert row is not None
    assert dict(row) == {
        "source": "intervals_icu",
        "status": "partial",
        "rows_pulled": 1,
        "rows_accepted": 1,
    }


# ---------------------------------------------------------------------------
# 5d — intervals.icu activities failure flags partial pull
# ---------------------------------------------------------------------------


class _ActivitiesFailingClient:
    """Replay client that raises on activities, succeeds on wellness."""

    def __init__(self, wellness_records):
        self._wellness = wellness_records

    def fetch_wellness_range(self, oldest, newest):
        return self._wellness

    def fetch_activities_range(self, oldest, newest):
        from health_agent_infra.core.pull.intervals_icu import IntervalsIcuError
        raise IntervalsIcuError("simulated /activities 503")


def test_intervals_icu_activities_failure_sets_partial_flag():
    """v0.1.9 B5 fix: an activities-endpoint failure now sets
    ``last_pull_partial = True``. Pre-v0.1.9 the run looked successful
    even though running-activity data was missed."""

    from health_agent_infra.core.pull.intervals_icu import IntervalsIcuAdapter

    client = _ActivitiesFailingClient(wellness_records=[
        {"id": AS_OF.isoformat(), "restingHR": 60, "sleepSecs": 25200},
    ])
    adapter = IntervalsIcuAdapter(client=client, history_days=2)

    payload = adapter.load(AS_OF)

    # Wellness data still landed.
    assert payload["raw_daily_row"] is not None
    # But the partial flag is now lit.
    assert adapter.last_pull_partial is True, (
        "activities failure should mark the pull partial; pre-v0.1.9 "
        "this stayed False and running-domain data silently degraded"
    )
    # Sentinel still recorded for diagnostics.
    sentinel_logged = any(
        "activities_endpoint" in failure
        for failure in adapter.last_pull_failed_days
    )
    assert sentinel_logged
