"""Tests for Phase 7D — hai state read + hai state snapshot.

Contract (per state_model_v1.md §§5–6 and plan 7D):
  - `hai state read --domain ...` returns rows from one canonical table,
    bounded by civil-date range. Primary use: operator / debug.
  - `hai state snapshot --as-of ...` returns the cross-domain object the
    agent consumes. Primary use: recovery-readiness skill.
  - Missingness per §5: absent | partial | unavailable_at_source |
    pending_user_input. 7D emits absent / partial / pending_user_input;
    unavailable_at_source distinction requires extra metadata landed in 7B.
  - pending_user_input fires for user-reported domains when as_of_date ==
    today's local civil date AND now_local < 23:30.

Out of scope: 7B richer recovery fields, 7C intake commands.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.state import (
    available_domains,
    build_snapshot,
    initialize_database,
    open_connection,
    read_domain,
)


USER = "u_test"
AS_OF = date(2026, 4, 17)


# ---------------------------------------------------------------------------
# Seeding helpers — insert rows directly via SQL since 7C intake CLIs don't
# exist yet. 7D is a read-surface test; it needs state to read.
# ---------------------------------------------------------------------------

def _seed_recovery(conn: sqlite3.Connection, *, as_of: date, user_id: str,
                    sleep_hours: float | None = 7.8,
                    resting_hr: float | None = 52.0,
                    hrv_ms: float | None = 48.0,
                    all_day_stress: int | None = 30,
                    manual_stress_score: int | None = 2,
                    acute_load: float | None = 400.0,
                    chronic_load: float | None = 380.0,
                    acwr_ratio: float | None = 1.05,
                    training_readiness_pct: float | None = 72.0,
                    body_battery_end_of_day: int | None = 65) -> None:
    conn.execute(
        """
        INSERT INTO accepted_recovery_state_daily (
            as_of_date, user_id,
            sleep_hours, resting_hr, hrv_ms, all_day_stress,
            manual_stress_score, acute_load, chronic_load,
            acwr_ratio, training_readiness_pct, body_battery_end_of_day,
            derived_from, source, ingest_actor, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            as_of.isoformat(), user_id,
            sleep_hours, resting_hr, hrv_ms, all_day_stress,
            manual_stress_score, acute_load, chronic_load,
            acwr_ratio, training_readiness_pct, body_battery_end_of_day,
            "[]", "garmin", "garmin_csv_adapter",
            "2026-04-17T06:00:00Z",
        ),
    )
    conn.commit()


def _seed_nutrition(conn: sqlite3.Connection, *, as_of: date, user_id: str,
                    calories: float = 2200.0, protein_g: float = 180.0) -> None:
    conn.execute(
        """
        INSERT INTO accepted_nutrition_state_daily (
            as_of_date, user_id, calories, protein_g, carbs_g, fat_g,
            hydration_l, meals_count,
            derived_from, source, ingest_actor, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            as_of.isoformat(), user_id, calories, protein_g, 260.0, 70.0,
            3.0, 3, "[]", "user_manual", "claude_agent_v1",
            "2026-04-17T19:00:00Z",
        ),
    )
    conn.commit()


def _seed_goal(conn: sqlite3.Connection, *, user_id: str, label: str,
                domain: str | None, started_on: date,
                ended_on: date | None = None) -> None:
    conn.execute(
        """
        INSERT INTO goal (goal_id, user_id, label, domain,
                          started_on, ended_on, created_at,
                          source, ingest_actor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"goal_{label}",
            user_id, label, domain,
            started_on.isoformat(),
            ended_on.isoformat() if ended_on else None,
            "2026-04-01T00:00:00Z",
            "user_manual", "claude_agent_v1",
        ),
    )
    conn.commit()


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


# ---------------------------------------------------------------------------
# read_domain — per-domain queries
# ---------------------------------------------------------------------------

def test_read_domain_returns_rows_from_canonical_table(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_recovery(conn, as_of=AS_OF, user_id=USER)
        rows = read_domain(conn, domain="recovery", since=AS_OF, until=AS_OF, user_id=USER)
    finally:
        conn.close()

    assert len(rows) == 1
    assert rows[0]["as_of_date"] == "2026-04-17"
    assert rows[0]["sleep_hours"] == 7.8
    assert rows[0]["resting_hr"] == 52.0


def test_read_domain_honours_date_range(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        for d in [AS_OF - timedelta(days=i) for i in range(5)]:
            _seed_recovery(conn, as_of=d, user_id=USER)
        rows = read_domain(
            conn, domain="recovery",
            since=AS_OF - timedelta(days=2),
            until=AS_OF - timedelta(days=1),
            user_id=USER,
        )
    finally:
        conn.close()

    assert [r["as_of_date"] for r in rows] == ["2026-04-15", "2026-04-16"]


def test_read_domain_filters_by_user_id(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_recovery(conn, as_of=AS_OF, user_id="u_a")
        _seed_recovery(conn, as_of=AS_OF, user_id="u_b")
        rows_a = read_domain(conn, domain="recovery", since=AS_OF, until=AS_OF, user_id="u_a")
        rows_both = read_domain(conn, domain="recovery", since=AS_OF, until=AS_OF)
    finally:
        conn.close()

    assert len(rows_a) == 1
    assert rows_a[0]["user_id"] == "u_a"
    assert len(rows_both) == 2


def test_read_domain_unknown_domain_raises(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        with pytest.raises(ValueError) as exc:
            read_domain(conn, domain="not_a_domain", since=AS_OF)
        assert "unknown domain" in str(exc.value)
    finally:
        conn.close()


def test_read_domain_goals_returns_overlapping_active_goals(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_goal(conn, user_id=USER, label="strength_block",
                   domain="resistance_training",
                   started_on=date(2026, 4, 1))
        _seed_goal(conn, user_id=USER, label="retired",
                   domain="running",
                   started_on=date(2026, 3, 1),
                   ended_on=date(2026, 3, 31))
        rows = read_domain(conn, domain="goals", since=AS_OF, until=AS_OF, user_id=USER)
    finally:
        conn.close()

    labels = sorted(r["label"] for r in rows)
    assert labels == ["strength_block"]  # retired goal excluded (ended_on < since)


def test_read_domain_empty_table_returns_empty_list(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        rows = read_domain(conn, domain="gym", since=AS_OF, until=AS_OF, user_id=USER)
    finally:
        conn.close()
    assert rows == []


# ---------------------------------------------------------------------------
# build_snapshot — envelope shape + missingness
# ---------------------------------------------------------------------------

def test_snapshot_on_empty_db_marks_every_domain_absent(tmp_path: Path):
    """A fresh DB with no rows must surface `absent` for each daily domain.
    Looking at a past date (not today) → no pending_user_input."""

    db = _init_db(tmp_path)
    past_date = AS_OF - timedelta(days=30)

    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=past_date, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),  # later than past_date
        )
    finally:
        conn.close()

    for domain in ("recovery", "running", "gym", "nutrition"):
        assert snap[domain]["today"] is None
        assert snap[domain]["missingness"] == "absent"
    assert snap["stress"]["today_garmin"] is None
    assert snap["stress"]["today_manual"] is None
    assert snap["stress"]["missingness"] == "absent"
    assert snap["goals_active"] == []
    assert snap["notes"]["recent"] == []
    assert snap["recommendations"]["recent"] == []


def test_snapshot_surfaces_present_when_all_fields_populated(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_recovery(conn, as_of=AS_OF, user_id=USER,
                       manual_stress_score=2, acute_load=400.0, chronic_load=380.0)
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),
        )
    finally:
        conn.close()

    assert snap["recovery"]["today"]["sleep_hours"] == 7.8
    assert snap["recovery"]["missingness"] == "present"
    assert snap["stress"]["today_garmin"] == 30
    assert snap["stress"]["today_manual"] == 2


def test_snapshot_emits_partial_with_null_field_list(tmp_path: Path):
    """If a today row exists but some columns are NULL, missingness reports
    `partial:<field1>,<field2>` per state_model_v1.md §5."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_recovery(
            conn, as_of=AS_OF, user_id=USER,
            hrv_ms=None, acute_load=None, chronic_load=None,
        )
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),
        )
    finally:
        conn.close()

    mx = snap["recovery"]["missingness"]
    assert mx.startswith("partial:")
    # A few explicit fields we know are NULL — each should appear.
    for field in ("hrv_ms", "acute_load", "chronic_load"):
        assert field in mx


def test_snapshot_pending_user_input_on_today_before_cutover(tmp_path: Path):
    """User-reported domains (gym, nutrition, stress, notes) get
    pending_user_input on today's date before 23:30 local. Passive
    (Garmin-backed) recovery/running do not — they're `absent` instead."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            # now_local is same civil date, before 23:30
            now_local=datetime(AS_OF.year, AS_OF.month, AS_OF.day, 14, 30),
        )
    finally:
        conn.close()

    # Passive: absent, not pending_user_input
    assert snap["recovery"]["missingness"] == "absent"
    assert snap["running"]["missingness"] == "absent"
    # User-reported: pending_user_input
    assert snap["gym"]["missingness"] == "pending_user_input"
    assert snap["nutrition"]["missingness"] == "pending_user_input"
    assert snap["stress"]["missingness"] == "pending_user_input"


def test_snapshot_absent_on_today_after_cutover(tmp_path: Path):
    """After 23:30 local on today's civil date, user-reported gaps become
    `absent` — the logging window is closed."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            # same civil date, after 23:30
            now_local=datetime(AS_OF.year, AS_OF.month, AS_OF.day, 23, 45),
        )
    finally:
        conn.close()

    assert snap["gym"]["missingness"] == "absent"
    assert snap["nutrition"]["missingness"] == "absent"


def test_snapshot_history_window_matches_lookback_days(tmp_path: Path):
    """The lookback window ends the day before as_of_date and spans
    `lookback_days` days total."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        # Seed 10 consecutive days ending on AS_OF.
        for d in [AS_OF - timedelta(days=i) for i in range(10)]:
            _seed_recovery(conn, as_of=d, user_id=USER)
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER, lookback_days=5,
            now_local=datetime(2026, 5, 1, 10, 0),
        )
    finally:
        conn.close()

    history = snap["recovery"]["history"]
    # lookback_days=5 means window is [AS_OF-4, AS_OF] inclusive; history
    # excludes AS_OF itself (that's `today`). So we expect 4 rows.
    assert len(history) == 4
    history_dates = [r["as_of_date"] for r in history]
    assert history_dates == ["2026-04-13", "2026-04-14", "2026-04-15", "2026-04-16"]
    assert snap["history_range"] == ["2026-04-13", "2026-04-16"]


def test_snapshot_goals_active_returned(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_goal(conn, user_id=USER, label="strength_block",
                   domain="resistance_training",
                   started_on=date(2026, 4, 1))
        _seed_goal(conn, user_id=USER, label="5k_pace",
                   domain="running",
                   started_on=date(2026, 3, 1))
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),
        )
    finally:
        conn.close()

    labels = sorted(g["label"] for g in snap["goals_active"])
    assert labels == ["5k_pace", "strength_block"]


def test_snapshot_envelope_has_expected_top_level_keys(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),
        )
    finally:
        conn.close()

    expected = {
        "schema_version", "as_of_date", "user_id", "lookback_days",
        "history_range", "recovery", "running", "gym", "nutrition",
        "stress", "notes", "goals_active", "recommendations", "reviews",
    }
    assert expected.issubset(snap.keys())
    assert snap["schema_version"] == "state_snapshot.v1"


# ---------------------------------------------------------------------------
# CLI round-trip — hai state read / hai state snapshot
# ---------------------------------------------------------------------------

def test_cli_state_read_returns_envelope(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_recovery(conn, as_of=AS_OF, user_id=USER)
    finally:
        conn.close()

    rc = cli_main([
        "state", "read",
        "--domain", "recovery",
        "--since", AS_OF.isoformat(),
        "--user-id", USER,
        "--db-path", str(db),
    ])
    out = capsys.readouterr().out
    assert rc == 0

    envelope = json.loads(out)
    assert envelope["domain"] == "recovery"
    assert envelope["as_of_range"] == [AS_OF.isoformat(), AS_OF.isoformat()]
    assert envelope["user_id"] == USER
    assert len(envelope["rows"]) == 1


def test_cli_state_read_unknown_domain_fails_closed(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "state", "read",
        "--domain", "bogus",
        "--since", AS_OF.isoformat(),
        "--db-path", str(db),
    ])
    err = capsys.readouterr().err
    assert rc == 2
    assert "unknown domain" in err


def test_cli_state_read_missing_db_fails_closed(tmp_path: Path, capsys):
    absent = tmp_path / "nope.db"
    rc = cli_main([
        "state", "read",
        "--domain", "recovery",
        "--since", AS_OF.isoformat(),
        "--db-path", str(absent),
    ])
    err = capsys.readouterr().err
    assert rc == 2
    assert "state DB not found" in err


def test_cli_state_snapshot_returns_envelope(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_recovery(conn, as_of=AS_OF, user_id=USER)
        _seed_nutrition(conn, as_of=AS_OF, user_id=USER)
    finally:
        conn.close()

    rc = cli_main([
        "state", "snapshot",
        "--as-of", AS_OF.isoformat(),
        "--user-id", USER,
        "--db-path", str(db),
    ])
    out = capsys.readouterr().out
    assert rc == 0

    snap = json.loads(out)
    assert snap["as_of_date"] == AS_OF.isoformat()
    assert snap["user_id"] == USER
    assert snap["recovery"]["today"] is not None
    assert snap["nutrition"]["today"] is not None


def test_cli_state_snapshot_missing_db_fails_closed(tmp_path: Path, capsys):
    absent = tmp_path / "nope.db"
    rc = cli_main([
        "state", "snapshot",
        "--as-of", AS_OF.isoformat(),
        "--user-id", USER,
        "--db-path", str(absent),
    ])
    err = capsys.readouterr().err
    assert rc == 2
    assert "state DB not found" in err


def test_cli_state_snapshot_respects_lookback_days(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        for d in [AS_OF - timedelta(days=i) for i in range(10)]:
            _seed_recovery(conn, as_of=d, user_id=USER)
    finally:
        conn.close()

    rc = cli_main([
        "state", "snapshot",
        "--as-of", AS_OF.isoformat(),
        "--user-id", USER,
        "--lookback-days", "3",
        "--db-path", str(db),
    ])
    out = capsys.readouterr().out
    assert rc == 0

    snap = json.loads(out)
    # lookback_days=3 => window is [AS_OF-2, AS_OF]; history excludes today
    # => 2 history rows.
    assert len(snap["recovery"]["history"]) == 2


def test_available_domains_matches_plan_list():
    """Guard against accidental domain-name drift from state_model_v1.md §1."""

    expected = {
        "recovery", "running", "gym", "nutrition", "stress",
        "notes", "recommendations", "reviews", "goals",
    }
    assert set(available_domains()) == expected
