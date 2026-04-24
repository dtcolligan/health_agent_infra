"""Tests for the Intervals.icu pull adapter (`core/pull/intervals_icu.py`).

Scope:
  - Evidence-shape compatibility: Intervals.icu adapter emits the same
    top-level keys as the CSV and Garmin-live adapters.
  - Field mapping: Intervals.icu camelCase fields map to the canonical
    snake_case series shape the classifier consumes.
  - Per-field resilience: missing/zero values are skipped from series;
    sleep falls through sleepSecs → sleepHours → None.
  - raw_daily_row carries every RAW_DAILY_ROW_COLUMNS key; columns
    Intervals.icu does not provide remain None (so downstream projectors
    see a consistent shape regardless of source).
  - HTTP client assembles the correct URL, sets Basic auth with the literal
    ``API_KEY`` username, and raises ``IntervalsIcuError`` on non-2xx.

Tests inject a replay client for adapter-level tests; HTTP-level tests
use ``http.server`` + ``threading`` so no real Intervals.icu request ever
leaves the machine.
"""

from __future__ import annotations

import base64
import json
import threading
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from health_agent_infra.core.pull.auth import IntervalsIcuCredentials
from health_agent_infra.core.pull.intervals_icu import (
    RAW_DAILY_ROW_COLUMNS,
    HttpIntervalsIcuClient,
    IntervalsIcuActivity,
    IntervalsIcuAdapter,
    IntervalsIcuError,
    _parse_activities,
    build_default_client,
)
from health_agent_infra.core.pull.protocol import FlagshipPullAdapter


# ---------------------------------------------------------------------------
# Replay client for adapter-level tests
# ---------------------------------------------------------------------------

class ReplayWellnessClient:
    """Returns pre-seeded wellness + activities records. Records the queried range."""

    def __init__(
        self,
        records: list[dict],
        *,
        activities: list[dict] | None = None,
        activities_error: IntervalsIcuError | None = None,
    ):
        self._records = records
        self._activities = list(activities or [])
        self._activities_error = activities_error
        self.queried: list[tuple[date, date]] = []
        self.queried_activities: list[tuple[date, date]] = []

    def fetch_wellness_range(self, oldest: date, newest: date) -> list[dict]:
        self.queried.append((oldest, newest))
        return list(self._records)

    def fetch_activities_range(self, oldest: date, newest: date) -> list[dict]:
        self.queried_activities.append((oldest, newest))
        if self._activities_error is not None:
            raise self._activities_error
        return list(self._activities)


def _wellness(d: date, **fields) -> dict:
    base = {"id": d.isoformat()}
    base.update(fields)
    return base


# ---------------------------------------------------------------------------
# Evidence shape vs. canonical contract
# ---------------------------------------------------------------------------

def test_adapter_evidence_keys_match_canonical_contract():
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([
        _wellness(as_of, restingHR=58, hrv=42, atl=400, sleepSecs=27000),
    ])
    adapter = IntervalsIcuAdapter(client=client, history_days=0)
    pull = adapter.load(as_of)
    assert set(pull.keys()) == {
        "sleep", "resting_hr", "hrv", "training_load", "raw_daily_row", "activities"
    }


def test_adapter_conforms_to_flagship_pull_protocol():
    adapter = IntervalsIcuAdapter(client=ReplayWellnessClient([]))
    assert isinstance(adapter, FlagshipPullAdapter)
    assert adapter.source_name == "intervals_icu"


def test_adapter_queries_full_history_window():
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([])
    adapter = IntervalsIcuAdapter(client=client, history_days=14)
    adapter.load(as_of)
    assert client.queried == [(as_of - timedelta(days=14), as_of)]


# ---------------------------------------------------------------------------
# Sleep extraction
# ---------------------------------------------------------------------------

def test_sleep_extracted_from_sleep_secs():
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([_wellness(as_of, sleepSecs=27000)])
    adapter = IntervalsIcuAdapter(client=client, history_days=0)
    sleep = adapter.load(as_of)["sleep"]
    assert sleep is not None
    assert set(sleep.keys()) == {"record_id", "duration_hours"}
    assert sleep["record_id"] == "i_sleep_2026-04-17"
    assert sleep["duration_hours"] == 7.5  # 27000 / 3600


def test_sleep_falls_back_to_sleep_hours_when_secs_missing():
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([_wellness(as_of, sleepHours=7.25)])
    adapter = IntervalsIcuAdapter(client=client, history_days=0)
    sleep = adapter.load(as_of)["sleep"]
    assert sleep is not None
    assert sleep["duration_hours"] == 7.25


def test_sleep_none_when_neither_field_present():
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([_wellness(as_of)])
    adapter = IntervalsIcuAdapter(client=client, history_days=0)
    assert adapter.load(as_of)["sleep"] is None


def test_sleep_none_when_zero_or_negative():
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([_wellness(as_of, sleepSecs=0, sleepHours=0)])
    adapter = IntervalsIcuAdapter(client=client, history_days=0)
    assert adapter.load(as_of)["sleep"] is None


# ---------------------------------------------------------------------------
# Series fields (resting_hr, hrv, training_load)
# ---------------------------------------------------------------------------

def test_series_map_camelcase_to_canonical_keys():
    as_of = date(2026, 4, 17)
    prev = as_of - timedelta(days=1)
    client = ReplayWellnessClient([
        _wellness(prev, restingHR=60, hrv=45, atl=350),
        _wellness(as_of, restingHR=58, hrv=48, atl=400),
    ])
    adapter = IntervalsIcuAdapter(client=client, history_days=1)
    pull = adapter.load(as_of)

    assert pull["resting_hr"] == [
        {"date": prev.isoformat(), "bpm": 60.0, "record_id": f"i_rhr_{prev.isoformat()}"},
        {"date": as_of.isoformat(), "bpm": 58.0, "record_id": f"i_rhr_{as_of.isoformat()}"},
    ]
    assert pull["hrv"] == [
        {"date": prev.isoformat(), "rmssd_ms": 45.0, "record_id": f"i_hrv_{prev.isoformat()}"},
        {"date": as_of.isoformat(), "rmssd_ms": 48.0, "record_id": f"i_hrv_{as_of.isoformat()}"},
    ]
    assert pull["training_load"] == [
        {"date": prev.isoformat(), "load": 350.0, "record_id": f"i_load_{prev.isoformat()}"},
        {"date": as_of.isoformat(), "load": 400.0, "record_id": f"i_load_{as_of.isoformat()}"},
    ]


def test_series_skip_zero_and_none():
    as_of = date(2026, 4, 17)
    prev = as_of - timedelta(days=1)
    prev2 = as_of - timedelta(days=2)
    client = ReplayWellnessClient([
        _wellness(prev2, restingHR=0, hrv=None),
        _wellness(prev, restingHR=60, hrv=45),
        _wellness(as_of, restingHR=58, hrv=48, atl=400),
    ])
    adapter = IntervalsIcuAdapter(client=client, history_days=2)
    pull = adapter.load(as_of)
    # prev2 contributed nothing
    assert [r["date"] for r in pull["resting_hr"]] == [prev.isoformat(), as_of.isoformat()]
    assert [r["date"] for r in pull["hrv"]] == [prev.isoformat(), as_of.isoformat()]
    # training_load only on as_of
    assert [r["date"] for r in pull["training_load"]] == [as_of.isoformat()]


def test_series_sorted_chronologically_even_if_records_unordered():
    as_of = date(2026, 4, 17)
    prev = as_of - timedelta(days=2)
    mid = as_of - timedelta(days=1)
    # Records returned out of order:
    client = ReplayWellnessClient([
        _wellness(as_of, restingHR=58),
        _wellness(prev, restingHR=62),
        _wellness(mid, restingHR=60),
    ])
    adapter = IntervalsIcuAdapter(client=client, history_days=2)
    pull = adapter.load(as_of)
    assert [r["date"] for r in pull["resting_hr"]] == [
        prev.isoformat(), mid.isoformat(), as_of.isoformat()
    ]


# ---------------------------------------------------------------------------
# raw_daily_row — Garmin-shaped, None where unavailable
# ---------------------------------------------------------------------------

def test_raw_daily_row_has_every_canonical_column():
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([
        _wellness(as_of, restingHR=58, hrv=48, atl=400, ctl=380, sleepSecs=27000,
                  sleepScore=82, steps=9500),
    ])
    adapter = IntervalsIcuAdapter(client=client, history_days=0)
    row = adapter.load(as_of)["raw_daily_row"]
    assert row is not None
    # Every canonical column must be present (None if unavailable).
    for col in RAW_DAILY_ROW_COLUMNS:
        assert col in row, f"missing column {col}"


def test_raw_daily_row_populates_overlapping_fields():
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([
        _wellness(as_of, restingHR=58, hrv=48, atl=400, ctl=380,
                  sleepScore=82, sleepSecs=27000, steps=9500),
    ])
    adapter = IntervalsIcuAdapter(client=client, history_days=0)
    row = adapter.load(as_of)["raw_daily_row"]
    assert row["date"] == "2026-04-17"
    assert row["resting_hr"] == 58.0
    assert row["health_hrv_value"] == 48.0
    assert row["health_hr_value"] == 58.0
    assert row["acute_load"] == 400.0
    assert row["chronic_load"] == 380.0
    assert row["sleep_score_overall"] == 82.0
    assert row["sleep_total_sec"] == 27000.0
    assert row["steps"] == 9500.0


def test_raw_daily_row_sleep_total_sec_falls_back_to_sleep_hours():
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([
        _wellness(as_of, restingHR=58, sleepHours=7.5),  # no sleepSecs
    ])
    adapter = IntervalsIcuAdapter(client=client, history_days=0)
    row = adapter.load(as_of)["raw_daily_row"]
    assert row["sleep_total_sec"] == 7.5 * 3600.0


def test_raw_daily_row_sleep_total_sec_none_when_no_sleep_data():
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([_wellness(as_of, restingHR=58)])
    adapter = IntervalsIcuAdapter(client=client, history_days=0)
    row = adapter.load(as_of)["raw_daily_row"]
    assert row["sleep_total_sec"] is None


def test_raw_daily_row_leaves_garmin_only_fields_none():
    """Body Battery, training readiness, stress — Intervals.icu does not
    provide these. They must remain None so downstream classifiers fall
    back cleanly."""
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([_wellness(as_of, restingHR=58)])
    adapter = IntervalsIcuAdapter(client=client, history_days=0)
    row = adapter.load(as_of)["raw_daily_row"]
    for garmin_only in (
        "body_battery",
        "all_day_stress",
        "training_readiness_level",
        "training_readiness_hrv_pct",
        "sleep_deep_sec",
        "sleep_light_sec",
        "sleep_rem_sec",
        "acwr_status",
        "training_status",
    ):
        assert row[garmin_only] is None, f"{garmin_only} leaked a non-None value"


def test_raw_daily_row_none_when_no_record_for_as_of():
    as_of = date(2026, 4, 17)
    prev = as_of - timedelta(days=1)
    client = ReplayWellnessClient([_wellness(prev, restingHR=60)])
    adapter = IntervalsIcuAdapter(client=client, history_days=1)
    assert adapter.load(as_of)["raw_daily_row"] is None


# ---------------------------------------------------------------------------
# Partial-pull telemetry
# ---------------------------------------------------------------------------

def test_partial_flag_set_when_as_of_missing():
    as_of = date(2026, 4, 17)
    prev = as_of - timedelta(days=1)
    client = ReplayWellnessClient([_wellness(prev, restingHR=60)])
    adapter = IntervalsIcuAdapter(client=client, history_days=1)
    adapter.load(as_of)
    assert adapter.last_pull_partial is True
    assert adapter.last_pull_failed_days == [as_of.isoformat()]


def test_partial_flag_cleared_on_successful_pull():
    as_of = date(2026, 4, 17)
    # First load: missing as_of → partial
    client_missing = ReplayWellnessClient([])
    adapter = IntervalsIcuAdapter(client=client_missing, history_days=0)
    adapter.load(as_of)
    assert adapter.last_pull_partial is True

    # Rebind a complete client; partial must clear on next load
    adapter.client = ReplayWellnessClient([_wellness(as_of, restingHR=58)])
    adapter.load(as_of)
    assert adapter.last_pull_partial is False
    assert adapter.last_pull_failed_days == []


# ---------------------------------------------------------------------------
# HTTP client — URL, auth header, error handling
# ---------------------------------------------------------------------------

class _RecordingHandler(BaseHTTPRequestHandler):
    """Records inbound requests and responds with the seeded body."""

    # Class-level state so test can inspect after teardown.
    last_path: str = ""
    last_auth_header: str = ""
    response_status: int = 200
    response_body: bytes = b"[]"

    def log_message(self, format, *args):
        return  # silence noisy stderr in tests

    def do_GET(self):
        type(self).last_path = self.path
        type(self).last_auth_header = self.headers.get("Authorization", "")
        self.send_response(type(self).response_status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(type(self).response_body)))
        self.end_headers()
        self.wfile.write(type(self).response_body)


@pytest.fixture
def local_server():
    """Spin up a loopback HTTP server for the HTTP client tests."""

    # Reset state between tests.
    _RecordingHandler.last_path = ""
    _RecordingHandler.last_auth_header = ""
    _RecordingHandler.response_status = 200
    _RecordingHandler.response_body = b"[]"

    server = HTTPServer(("127.0.0.1", 0), _RecordingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}", _RecordingHandler
    finally:
        server.shutdown()
        server.server_close()


def test_http_client_uses_basic_auth_with_literal_api_key_username(local_server):
    base_url, handler = local_server
    client = HttpIntervalsIcuClient(
        credentials=IntervalsIcuCredentials(athlete_id="i123", api_key="sekret"),
        base_url=base_url,
    )
    client.fetch_wellness_range(date(2026, 4, 17), date(2026, 4, 17))

    expected = "Basic " + base64.b64encode(b"API_KEY:sekret").decode("ascii")
    assert handler.last_auth_header == expected


def test_http_client_assembles_wellness_range_url(local_server):
    base_url, handler = local_server
    client = HttpIntervalsIcuClient(
        credentials=IntervalsIcuCredentials(athlete_id="i123", api_key="sekret"),
        base_url=base_url,
    )
    client.fetch_wellness_range(date(2026, 4, 10), date(2026, 4, 17))

    assert handler.last_path.startswith("/api/v1/athlete/i123/wellness.json?")
    assert "oldest=2026-04-10" in handler.last_path
    assert "newest=2026-04-17" in handler.last_path


def test_http_client_returns_parsed_json_array(local_server):
    base_url, handler = local_server
    handler.response_body = json.dumps([
        {"id": "2026-04-17", "restingHR": 58, "hrv": 48},
    ]).encode("utf-8")
    client = HttpIntervalsIcuClient(
        credentials=IntervalsIcuCredentials(athlete_id="i123", api_key="sekret"),
        base_url=base_url,
    )
    records = client.fetch_wellness_range(date(2026, 4, 17), date(2026, 4, 17))
    assert records == [{"id": "2026-04-17", "restingHR": 58, "hrv": 48}]


def test_http_client_raises_on_http_error(local_server):
    base_url, handler = local_server
    handler.response_status = 401
    handler.response_body = b"Unauthorized"
    client = HttpIntervalsIcuClient(
        credentials=IntervalsIcuCredentials(athlete_id="i123", api_key="bad"),
        base_url=base_url,
    )
    with pytest.raises(IntervalsIcuError) as exc_info:
        client.fetch_wellness_range(date(2026, 4, 17), date(2026, 4, 17))
    # Must mention status; must NOT leak the api_key.
    assert "401" in str(exc_info.value)
    assert "bad" not in str(exc_info.value)


def test_http_client_raises_on_malformed_json(local_server):
    base_url, handler = local_server
    handler.response_body = b"not json"
    client = HttpIntervalsIcuClient(
        credentials=IntervalsIcuCredentials(athlete_id="i123", api_key="sekret"),
        base_url=base_url,
    )
    with pytest.raises(IntervalsIcuError):
        client.fetch_wellness_range(date(2026, 4, 17), date(2026, 4, 17))


def test_http_client_raises_when_response_is_not_array(local_server):
    base_url, handler = local_server
    handler.response_body = b'{"error": "some object"}'
    client = HttpIntervalsIcuClient(
        credentials=IntervalsIcuCredentials(athlete_id="i123", api_key="sekret"),
        base_url=base_url,
    )
    with pytest.raises(IntervalsIcuError):
        client.fetch_wellness_range(date(2026, 4, 17), date(2026, 4, 17))


def test_build_default_client_returns_http_client():
    creds = IntervalsIcuCredentials(athlete_id="i123", api_key="sekret")
    client = build_default_client(creds)
    assert isinstance(client, HttpIntervalsIcuClient)


# ---------------------------------------------------------------------------
# Activities parser — maps live-shape Garmin Connect run
# ---------------------------------------------------------------------------

GARMIN_RUN_SAMPLE: dict = {
    "id": "i142248964",
    "external_id": "22628799588",
    "source": "GARMIN_CONNECT",
    "start_date": "2026-04-23T10:21:28Z",
    "start_date_local": "2026-04-23T11:21:28",
    "type": "Run",
    "name": "East Lothian Running",
    "distance": 6746.21,
    "moving_time": 2399,
    "elapsed_time": 2400,
    "average_heartrate": 155,
    "max_heartrate": 182,
    "athlete_max_hr": 202,
    "icu_hr_zone_times": [1312, 254, 550, 282, 0, 0, 0],
    "icu_hr_zones": [154, 163, 172, 182, 187, 192, 202],
    "interval_summary": ["4x 9m29s 156bpm", "1x 2m7s 146bpm"],
    "trimp": 67.496635,
    "icu_training_load": 39,
    "hr_load": 39,
    "hr_load_type": "HRSS",
    "icu_warmup_time": 300,
    "icu_cooldown_time": 300,
    "icu_lap_count": 5,
    "average_speed": 2.81,
    "max_speed": 3.667,
    "pace": 2.8120925,
    "average_cadence": 83.94948,
    "average_stride": 1.0049231,
    "calories": 520,
    "total_elevation_gain": 23.436192,
    "total_elevation_loss": 24.395403,
    "feel": 3,
    "icu_rpe": 7,
    "session_rpe": 279,
    "device_name": "Garmin Forerunner 265",
}


def test_parse_activities_maps_garmin_run_sample_faithfully():
    parsed = _parse_activities([GARMIN_RUN_SAMPLE], user_id="u_local_1")
    assert len(parsed) == 1
    a = parsed[0]
    assert a.activity_id == "i142248964"
    assert a.user_id == "u_local_1"
    assert a.as_of_date == "2026-04-23"  # derived from start_date_local
    assert a.source == "GARMIN_CONNECT"
    assert a.external_id == "22628799588"
    assert a.activity_type == "Run"
    assert a.distance_m == 6746.21
    assert a.moving_time_s == 2399.0
    assert a.hr_zone_times_s == [1312, 254, 550, 282, 0, 0, 0]
    assert a.interval_summary == ["4x 9m29s 156bpm", "1x 2m7s 146bpm"]
    assert a.trimp == pytest.approx(67.496635)
    assert a.warmup_time_s == 300.0
    assert a.cooldown_time_s == 300.0
    assert a.lap_count == 5
    assert a.device_name == "Garmin Forerunner 265"


def test_parse_activities_uses_start_date_utc_when_local_missing():
    rec = dict(GARMIN_RUN_SAMPLE)
    rec.pop("start_date_local")
    parsed = _parse_activities([rec], user_id="u_local_1")
    assert parsed[0].as_of_date == "2026-04-23"


def test_parse_activities_skips_records_without_id():
    rec = dict(GARMIN_RUN_SAMPLE)
    rec.pop("id")
    assert _parse_activities([rec], user_id="u_local_1") == []


def test_parse_activities_skips_records_without_parseable_date():
    rec = dict(GARMIN_RUN_SAMPLE)
    rec["start_date"] = "not a date"
    rec["start_date_local"] = None
    assert _parse_activities([rec], user_id="u_local_1") == []


def test_parse_activities_distance_falls_back_to_icu_distance():
    rec = dict(GARMIN_RUN_SAMPLE)
    rec.pop("distance")
    rec["icu_distance"] = 5000.0
    parsed = _parse_activities([rec], user_id="u_local_1")
    assert parsed[0].distance_m == 5000.0


def test_parse_activities_preserves_raw_json_for_unmapped_fields():
    rec = dict(GARMIN_RUN_SAMPLE)
    rec["some_future_field"] = {"nested": [1, 2, 3]}
    parsed = _parse_activities([rec], user_id="u_local_1")
    raw = json.loads(parsed[0].raw_json)
    assert raw["some_future_field"] == {"nested": [1, 2, 3]}


def test_parse_activities_sorts_by_date_then_start_time_then_id():
    a_later_day = dict(GARMIN_RUN_SAMPLE, id="i_z", start_date_local="2026-04-24T06:00:00", start_date="2026-04-24T05:00:00Z")
    a_earlier = dict(GARMIN_RUN_SAMPLE, id="i_a", start_date_local="2026-04-23T08:00:00", start_date="2026-04-23T07:00:00Z")
    a_midday = dict(GARMIN_RUN_SAMPLE, id="i_m", start_date_local="2026-04-23T12:00:00", start_date="2026-04-23T11:00:00Z")
    parsed = _parse_activities([a_later_day, a_midday, a_earlier], user_id="u_local_1")
    assert [a.activity_id for a in parsed] == ["i_a", "i_m", "i_z"]


def test_parse_activities_as_dict_roundtrip_is_json_safe():
    parsed = _parse_activities([GARMIN_RUN_SAMPLE], user_id="u_local_1")
    blob = json.dumps(parsed[0].as_dict())  # must not raise
    back = json.loads(blob)
    assert back["activity_id"] == "i142248964"
    assert back["hr_zone_times_s"] == [1312, 254, 550, 282, 0, 0, 0]


# ---------------------------------------------------------------------------
# Adapter — activities surface
# ---------------------------------------------------------------------------

def test_adapter_surfaces_activities_from_client():
    as_of = date(2026, 4, 23)
    client = ReplayWellnessClient(
        [_wellness(as_of, restingHR=58)],
        activities=[GARMIN_RUN_SAMPLE],
    )
    adapter = IntervalsIcuAdapter(client=client, history_days=0, user_id="u_local_1")
    pull = adapter.load(as_of)
    assert len(pull["activities"]) == 1
    assert pull["activities"][0]["activity_id"] == "i142248964"
    assert pull["activities"][0]["user_id"] == "u_local_1"
    assert pull["activities"][0]["distance_m"] == 6746.21


def test_adapter_queries_activities_over_same_window_as_wellness():
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([], activities=[])
    adapter = IntervalsIcuAdapter(client=client, history_days=7)
    adapter.load(as_of)
    assert client.queried_activities == [(as_of - timedelta(days=7), as_of)]


def test_adapter_returns_empty_activities_on_endpoint_error():
    """A failed /activities endpoint must not break the wellness pull."""
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient(
        [_wellness(as_of, restingHR=58)],
        activities_error=IntervalsIcuError("HTTP 404 Not Found"),
    )
    adapter = IntervalsIcuAdapter(client=client, history_days=0)
    pull = adapter.load(as_of)
    assert pull["activities"] == []
    assert pull["raw_daily_row"] is not None
    # Failure surfaces on telemetry so dogfooders can see the gap.
    assert any(
        s.startswith("activities_endpoint:") for s in adapter.last_pull_failed_days
    )


def test_adapter_defaults_user_id_to_u_local_1():
    as_of = date(2026, 4, 17)
    client = ReplayWellnessClient([], activities=[GARMIN_RUN_SAMPLE])
    adapter = IntervalsIcuAdapter(client=client, history_days=0)
    pull = adapter.load(as_of)
    assert pull["activities"][0]["user_id"] == "u_local_1"


# ---------------------------------------------------------------------------
# HTTP client — /activities endpoint
# ---------------------------------------------------------------------------

def test_http_client_fetch_activities_assembles_url(local_server):
    base_url, handler = local_server
    client = HttpIntervalsIcuClient(
        credentials=IntervalsIcuCredentials(athlete_id="i123", api_key="sekret"),
        base_url=base_url,
    )
    client.fetch_activities_range(date(2026, 4, 16), date(2026, 4, 23))
    assert handler.last_path.startswith("/api/v1/athlete/i123/activities?")
    assert "oldest=2026-04-16" in handler.last_path
    assert "newest=2026-04-23" in handler.last_path


def test_http_client_fetch_activities_raises_on_error(local_server):
    base_url, handler = local_server
    handler.response_status = 500
    handler.response_body = b"server error"
    client = HttpIntervalsIcuClient(
        credentials=IntervalsIcuCredentials(athlete_id="i123", api_key="sekret"),
        base_url=base_url,
    )
    with pytest.raises(IntervalsIcuError) as exc_info:
        client.fetch_activities_range(date(2026, 4, 17), date(2026, 4, 17))
    assert "activities" in str(exc_info.value).lower()
    assert "500" in str(exc_info.value)


def test_http_client_fetch_activities_returns_parsed_array(local_server):
    base_url, handler = local_server
    handler.response_body = json.dumps([GARMIN_RUN_SAMPLE]).encode("utf-8")
    client = HttpIntervalsIcuClient(
        credentials=IntervalsIcuCredentials(athlete_id="i123", api_key="sekret"),
        base_url=base_url,
    )
    records = client.fetch_activities_range(date(2026, 4, 23), date(2026, 4, 23))
    assert records[0]["id"] == "i142248964"
