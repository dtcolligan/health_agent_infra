"""W-R: running-rollup provenance + completeness (Codex F-C-03 / F-CDX-IR-05).

Per-activity-rollup-derived rows now stamp
``derivation_path='activity_rollup'`` and populate ``session_count`` +
``total_duration_s``. Daily-aggregate-only rows still stamp
``garmin_daily`` with NULL on those fields (legacy path preserved).
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core.state import open_connection
from health_agent_infra.core.state.projector import (
    project_accepted_running_state_daily,
)
from health_agent_infra.core.state.projectors.running_activity import (
    aggregate_activities_to_daily_rollup,
)
from health_agent_infra.core.state.store import initialize_database


@pytest.fixture
def fresh_db(tmp_path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


def _read_running_row(db_path: Path, as_of: date, user_id: str) -> dict:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM accepted_running_state_daily "
            "WHERE as_of_date = ? AND user_id = ?",
            (as_of.isoformat(), user_id),
        ).fetchone()
        return dict(row) if row else {}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Garmin-daily path: NULL session_count, derivation_path='garmin_daily'
# ---------------------------------------------------------------------------


def test_no_rollup_supplied_uses_garmin_daily_stamp(fresh_db):
    """Legacy CSV-only path: no rollup → derivation_path 'garmin_daily',
    session_count + total_duration_s NULL (per state_model_v1.md §8)."""
    conn = open_connection(fresh_db)
    try:
        project_accepted_running_state_daily(
            conn,
            as_of_date=date(2026, 4, 28),
            user_id="u_local_1",
            raw_row={
                "distance_m": 5000,
                "moderate_intensity_min": 10,
                "vigorous_intensity_min": 20,
            },
            rollup=None,
        )
    finally:
        conn.close()
    row = _read_running_row(fresh_db, date(2026, 4, 28), "u_local_1")
    assert row["derivation_path"] == "garmin_daily"
    assert row["session_count"] is None
    assert row["total_duration_s"] is None
    assert row["total_distance_m"] == 5000


# ---------------------------------------------------------------------------
# Rollup path: derivation_path='activity_rollup', fields populated
# ---------------------------------------------------------------------------


def test_rollup_with_session_count_uses_activity_rollup_stamp(fresh_db):
    """Per-activity rollup → derivation_path 'activity_rollup',
    session_count + total_duration_s populated from the rollup."""
    activities = [
        {
            "as_of_date": "2026-04-28",
            "distance_m": 5000,
            "moving_time_s": 1800,
            "hr_zone_times_s": [60, 120, 180, 600, 0, 0, 0],
        },
    ]
    rollup = aggregate_activities_to_daily_rollup(activities)
    assert rollup["session_count"] == 1
    assert rollup["total_duration_s"] == 1800

    conn = open_connection(fresh_db)
    try:
        project_accepted_running_state_daily(
            conn,
            as_of_date=date(2026, 4, 28),
            user_id="u_local_1",
            raw_row={"distance_m": 5000},
            rollup=rollup,
        )
    finally:
        conn.close()
    row = _read_running_row(fresh_db, date(2026, 4, 28), "u_local_1")
    assert row["derivation_path"] == "running_sessions"
    assert row["session_count"] == 1
    assert row["total_duration_s"] == 1800


def test_empty_activities_rollup_falls_back_to_garmin_daily(fresh_db):
    """Empty activities → rollup with all-None fields → projector
    falls back to garmin_daily stamp."""
    rollup = aggregate_activities_to_daily_rollup([])
    assert rollup["session_count"] is None

    conn = open_connection(fresh_db)
    try:
        project_accepted_running_state_daily(
            conn,
            as_of_date=date(2026, 4, 28),
            user_id="u_local_1",
            raw_row={"distance_m": 5000},
            rollup=rollup,
        )
    finally:
        conn.close()
    row = _read_running_row(fresh_db, date(2026, 4, 28), "u_local_1")
    assert row["derivation_path"] == "garmin_daily"
    assert row["session_count"] is None


def test_two_activities_aggregate_correctly(fresh_db):
    """Two activities on the same day → session_count=2, durations summed."""
    activities = [
        {
            "as_of_date": "2026-04-28",
            "distance_m": 5000,
            "moving_time_s": 1500,
            "hr_zone_times_s": None,
        },
        {
            "as_of_date": "2026-04-28",
            "distance_m": 3000,
            "moving_time_s": 1000,
            "hr_zone_times_s": None,
        },
    ]
    rollup = aggregate_activities_to_daily_rollup(activities)
    assert rollup["session_count"] == 2
    assert rollup["total_duration_s"] == 2500
    assert rollup["total_distance_m"] == 8000

    conn = open_connection(fresh_db)
    try:
        project_accepted_running_state_daily(
            conn,
            as_of_date=date(2026, 4, 28),
            user_id="u_local_1",
            raw_row={"distance_m": 8000},
            rollup=rollup,
        )
    finally:
        conn.close()
    row = _read_running_row(fresh_db, date(2026, 4, 28), "u_local_1")
    assert row["derivation_path"] == "running_sessions"
    assert row["session_count"] == 2
    assert row["total_duration_s"] == 2500
