"""Tests for the running_activity projector + read helpers.

Covers:
  - ``project_activity`` upserts cleanly; re-projecting the same activity_id
    is idempotent and carries upstream edits (RPE, feel, zones) into state.
  - ``read_activities_for_date`` + ``read_activities_range`` filter by
    user + date + optional activity_type and rehydrate list fields.
  - ``aggregate_activities_to_daily_rollup`` sums distance/duration and
    derives moderate/vigorous intensity minutes from HR zone times.

The upstream shape mirrors ``IntervalsIcuActivity.as_dict()``. Activities
are upstream-owned, so there's no manual merge path — tests focus on the
single-writer semantics.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    aggregate_activities_to_daily_rollup,
    initialize_database,
    open_connection,
    project_activity,
    read_activities_for_date,
    read_activities_range,
)


# ---------------------------------------------------------------------------
# Fixture payloads
# ---------------------------------------------------------------------------

_UNSET = object()


def _activity(
    *,
    activity_id: str = "i1",
    user_id: str = "u_local_1",
    as_of: str = "2026-04-23",
    activity_type: str = "Run",
    distance_m: float | None = 6746.21,
    moving_time_s: float = 2399.0,
    hr_zone_times_s=_UNSET,
    hr_zones_bpm=_UNSET,
    interval_summary=_UNSET,
    start_date_utc: str | None = None,
    **overrides,
) -> dict:
    if hr_zone_times_s is _UNSET:
        hr_zone_times_s = [1312, 254, 550, 282, 0, 0, 0]
    if hr_zones_bpm is _UNSET:
        hr_zones_bpm = [154, 163, 172, 182, 187, 192, 202]
    if interval_summary is _UNSET:
        interval_summary = ["4x 9m29s 156bpm", "1x 2m7s 146bpm"]
    base = {
        "activity_id": activity_id,
        "user_id": user_id,
        "as_of_date": as_of,
        "start_date_utc": start_date_utc or f"{as_of}T10:00:00Z",
        "start_date_local": f"{as_of}T11:00:00",
        "source": "GARMIN_CONNECT",
        "external_id": "g_ext_1",
        "activity_type": activity_type,
        "name": "East Lothian Running",
        "distance_m": distance_m,
        "moving_time_s": moving_time_s,
        "elapsed_time_s": moving_time_s + 1.0,
        "average_hr": 155.0,
        "max_hr": 182.0,
        "athlete_max_hr": 202.0,
        "hr_zone_times_s": hr_zone_times_s,
        "hr_zones_bpm": hr_zones_bpm,
        "interval_summary": interval_summary,
        "trimp": 67.5,
        "icu_training_load": 39.0,
        "hr_load": 39.0,
        "hr_load_type": "HRSS",
        "warmup_time_s": 300.0,
        "cooldown_time_s": 300.0,
        "lap_count": 5,
        "average_speed_mps": 2.81,
        "max_speed_mps": 3.667,
        "pace_s_per_m": 2.81,
        "average_cadence_spm": 84.0,
        "average_stride_m": 1.0,
        "calories": 520.0,
        "total_elevation_gain_m": 23.4,
        "total_elevation_loss_m": 24.4,
        "feel": 3,
        "icu_rpe": 7,
        "session_rpe": 279.0,
        "device_name": "Garmin Forerunner 265",
        "raw_json": "{}",
    }
    base.update(overrides)
    return base


@pytest.fixture
def db(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    conn = open_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# project_activity — insert + upsert
# ---------------------------------------------------------------------------

def test_project_activity_first_insert_returns_true(db):
    is_insert = project_activity(db, activity=_activity())
    assert is_insert is True

    row = db.execute(
        "SELECT activity_id, distance_m, moving_time_s FROM running_activity"
    ).fetchone()
    assert row["activity_id"] == "i1"
    assert row["distance_m"] == pytest.approx(6746.21)
    assert row["moving_time_s"] == 2399.0


def test_project_activity_repull_is_idempotent(db):
    project_activity(db, activity=_activity())
    is_insert = project_activity(db, activity=_activity())
    assert is_insert is False

    # One row only.
    count = db.execute("SELECT COUNT(*) AS n FROM running_activity").fetchone()["n"]
    assert count == 1


def test_project_activity_upsert_carries_upstream_edits(db):
    project_activity(db, activity=_activity(feel=2, icu_rpe=5))
    project_activity(db, activity=_activity(feel=4, icu_rpe=8))

    row = db.execute(
        "SELECT feel, icu_rpe FROM running_activity WHERE activity_id = 'i1'"
    ).fetchone()
    assert row["feel"] == 4
    assert row["icu_rpe"] == 8


def test_project_activity_serialises_list_fields_as_json(db):
    project_activity(db, activity=_activity(
        hr_zone_times_s=[100, 200, 300, 400, 0, 0, 0],
        interval_summary=["warmup 10m", "8x 400m"],
    ))
    row = db.execute(
        "SELECT hr_zone_times_s_json, interval_summary_json FROM running_activity"
    ).fetchone()
    assert json.loads(row["hr_zone_times_s_json"]) == [100, 200, 300, 400, 0, 0, 0]
    assert json.loads(row["interval_summary_json"]) == ["warmup 10m", "8x 400m"]


def test_project_activity_handles_null_list_fields(db):
    project_activity(db, activity=_activity(
        hr_zone_times_s=None,
        hr_zones_bpm=None,
        interval_summary=None,
    ))
    row = db.execute(
        "SELECT hr_zone_times_s_json, hr_zones_bpm_json, interval_summary_json "
        "FROM running_activity"
    ).fetchone()
    assert row["hr_zone_times_s_json"] is None
    assert row["hr_zones_bpm_json"] is None
    assert row["interval_summary_json"] is None


# ---------------------------------------------------------------------------
# read_activities_for_date
# ---------------------------------------------------------------------------

def test_read_activities_for_date_returns_matching_rows(db):
    project_activity(db, activity=_activity(activity_id="i_a", as_of="2026-04-23"))
    project_activity(db, activity=_activity(activity_id="i_b", as_of="2026-04-22"))
    project_activity(db, activity=_activity(activity_id="i_c", as_of="2026-04-23"))

    rows = read_activities_for_date(
        db, user_id="u_local_1", as_of_date=date(2026, 4, 23),
    )
    assert {r["activity_id"] for r in rows} == {"i_a", "i_c"}


def test_read_activities_for_date_rehydrates_list_fields(db):
    project_activity(db, activity=_activity(
        hr_zone_times_s=[10, 20, 30, 40, 0, 0, 0],
        interval_summary=["a", "b"],
    ))
    rows = read_activities_for_date(
        db, user_id="u_local_1", as_of_date=date(2026, 4, 23),
    )
    assert rows[0]["hr_zone_times_s"] == [10, 20, 30, 40, 0, 0, 0]
    assert rows[0]["interval_summary"] == ["a", "b"]
    # Raw json-column columns are NOT surfaced
    assert "hr_zone_times_s_json" not in rows[0]


def test_read_activities_for_date_filters_by_type(db):
    project_activity(db, activity=_activity(activity_id="i_run", activity_type="Run"))
    project_activity(db, activity=_activity(activity_id="i_ride", activity_type="Ride"))

    runs = read_activities_for_date(
        db, user_id="u_local_1", as_of_date=date(2026, 4, 23),
        activity_type="Run",
    )
    assert [r["activity_id"] for r in runs] == ["i_run"]


def test_read_activities_for_date_isolates_by_user(db):
    project_activity(db, activity=_activity(activity_id="i_me", user_id="u_local_1"))
    project_activity(db, activity=_activity(activity_id="i_them", user_id="u_other"))

    rows = read_activities_for_date(
        db, user_id="u_local_1", as_of_date=date(2026, 4, 23),
    )
    assert [r["activity_id"] for r in rows] == ["i_me"]


# ---------------------------------------------------------------------------
# read_activities_range
# ---------------------------------------------------------------------------

def test_read_activities_range_inclusive_on_both_ends(db):
    project_activity(db, activity=_activity(activity_id="i_a", as_of="2026-04-20"))
    project_activity(db, activity=_activity(activity_id="i_b", as_of="2026-04-23"))
    project_activity(db, activity=_activity(activity_id="i_c", as_of="2026-04-26"))

    rows = read_activities_range(
        db, user_id="u_local_1",
        since=date(2026, 4, 20), until=date(2026, 4, 23),
    )
    assert {r["activity_id"] for r in rows} == {"i_a", "i_b"}


def test_read_activities_range_newest_first(db):
    project_activity(db, activity=_activity(
        activity_id="i_old", as_of="2026-04-20",
        start_date_utc="2026-04-20T10:00:00Z",
    ))
    project_activity(db, activity=_activity(
        activity_id="i_new", as_of="2026-04-23",
        start_date_utc="2026-04-23T10:00:00Z",
    ))
    rows = read_activities_range(
        db, user_id="u_local_1",
        since=date(2026, 4, 20), until=date(2026, 4, 23),
    )
    assert [r["activity_id"] for r in rows] == ["i_new", "i_old"]


# ---------------------------------------------------------------------------
# aggregate_activities_to_daily_rollup
# ---------------------------------------------------------------------------

def test_aggregate_empty_returns_all_nulls():
    out = aggregate_activities_to_daily_rollup([])
    assert out == {
        "total_distance_m": None,
        "total_duration_s": None,
        "moderate_intensity_min": None,
        "vigorous_intensity_min": None,
        "session_count": None,
    }


def test_aggregate_single_run_derives_intensity_minutes():
    # Z1=1312s (Z1 not counted), Z2=254s, Z3=550s → moderate = 804s = 13.4 min
    # Z4=282s, Z5=0, Z6=0, Z7=0 → vigorous = 282s = 4.7 min
    activity = _activity(
        hr_zone_times_s=[1312, 254, 550, 282, 0, 0, 0],
        distance_m=6746.21,
        moving_time_s=2399.0,
    )
    out = aggregate_activities_to_daily_rollup([activity])
    assert out["total_distance_m"] == pytest.approx(6746.21)
    assert out["total_duration_s"] == 2399.0
    assert out["moderate_intensity_min"] == pytest.approx((254 + 550) / 60.0)
    assert out["vigorous_intensity_min"] == pytest.approx(282 / 60.0)
    assert out["session_count"] == 1


def test_aggregate_two_sessions_sum_distance_and_intensity():
    a = _activity(
        activity_id="i_morning",
        distance_m=5000.0, moving_time_s=1800.0,
        hr_zone_times_s=[600, 200, 400, 600, 0, 0, 0],
    )
    b = _activity(
        activity_id="i_evening",
        distance_m=3000.0, moving_time_s=1200.0,
        hr_zone_times_s=[0, 100, 100, 0, 0, 0, 0],
    )
    out = aggregate_activities_to_daily_rollup([a, b])
    assert out["total_distance_m"] == 8000.0
    assert out["total_duration_s"] == 3000.0
    assert out["moderate_intensity_min"] == pytest.approx((200 + 400 + 100 + 100) / 60.0)
    assert out["vigorous_intensity_min"] == pytest.approx(600 / 60.0)
    assert out["session_count"] == 2


def test_aggregate_returns_none_for_intensity_when_no_zone_times():
    activity = _activity(
        hr_zone_times_s=None, distance_m=5000.0, moving_time_s=1800.0,
    )
    out = aggregate_activities_to_daily_rollup([activity])
    # Distance + duration still aggregate; intensity minutes must be None
    # (caller shouldn't conflate "no zone data" with "zero vigorous minutes").
    assert out["total_distance_m"] == 5000.0
    assert out["moderate_intensity_min"] is None
    assert out["vigorous_intensity_min"] is None


def test_aggregate_tolerates_partial_distance_data():
    """Mixed — one activity has distance, one doesn't. Sum the ones that do."""
    a = _activity(activity_id="i_a", distance_m=4000.0)
    b = _activity(activity_id="i_b", distance_m=None)
    out = aggregate_activities_to_daily_rollup([a, b])
    assert out["total_distance_m"] == 4000.0
    assert out["session_count"] == 2


def test_aggregate_handles_short_zone_array_gracefully():
    """Some upstream feeds report fewer than 7 zones. Don't crash."""
    activity = _activity(hr_zone_times_s=[100, 200, 300])
    out = aggregate_activities_to_daily_rollup([activity])
    # Moderate = Z2 (200) + Z3 (300) = 500s → 8.33 min
    assert out["moderate_intensity_min"] == pytest.approx(500 / 60.0)
    # Vigorous = whatever is beyond index 3 → nothing in this short array
    assert out["vigorous_intensity_min"] == pytest.approx(0.0)
