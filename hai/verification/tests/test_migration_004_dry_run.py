"""Phase 3 step 1 — `migration_004_dry_run_diff` safety gate.

Contract:

  1. On a DB at schema version 3 (pre-Phase-3), comparing current
     accepted_recovery columns against what reproject would produce from
     raw returns an empty mismatch list when the accepted values are
     consistent with raw. Every (as_of_date, user_id) row in
     accepted_recovery_state_daily is checked against source_daily_garmin
     and stress_manual_raw.

  2. When an accepted row holds a value that diverges from raw — a
     historical manual patch, a pre-Phase-3 bug's residue, or raw data
     drift — the helper lists the mismatch row-by-row, field-by-field.
     This is the operator's signal to reconcile before the migration
     runs forward.

  3. Running against a DB already at version 4 or higher raises —
     protects against misuse.

Runs against a *pre-004* DB constructed by replaying migrations 001–003
explicitly, so it exercises the exact pre-migration surface the gate is
designed to protect.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    apply_pending_migrations,
    current_schema_version,
    initialize_database,
    migration_004_dry_run_diff,
    open_connection,
)
from health_agent_infra.core.state.store import discover_migrations


USER = "u_test"
AS_OF = date(2026, 4, 17)


def _init_db_at_version_3(tmp_path: Path) -> Path:
    """Replay migrations 001–003 only, leaving the DB one step pre-Phase-3."""

    db = tmp_path / "state.db"
    all_migrations = discover_migrations()
    pre_004 = [m for m in all_migrations if m[0] < 4]
    conn = open_connection(db)
    try:
        apply_pending_migrations(conn, migrations=pre_004)
        assert current_schema_version(conn) == 3
    finally:
        conn.close()
    return db


def _seed_pre_004_recovery_row(
    conn: sqlite3.Connection,
    *,
    sleep_hours: float | None,
    all_day_stress: int | None,
    manual_stress_score: int | None,
    body_battery_end_of_day: int | None,
) -> None:
    conn.execute(
        """
        INSERT INTO accepted_recovery_state_daily (
            as_of_date, user_id,
            sleep_hours, resting_hr, hrv_ms, all_day_stress,
            manual_stress_score, acute_load, chronic_load, acwr_ratio,
            training_readiness_component_mean_pct, body_battery_end_of_day,
            derived_from, source, ingest_actor, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            AS_OF.isoformat(), USER,
            sleep_hours, 52.0, 48.0, all_day_stress,
            manual_stress_score, 400.0, 380.0, 1.053,
            76.0, body_battery_end_of_day,
            "[]", "garmin", "garmin_csv_adapter",
            "2026-04-17T06:00:00Z",
        ),
    )
    conn.commit()


def _seed_source_daily_garmin(
    conn: sqlite3.Connection,
    *,
    sleep_deep_sec: int | None,
    sleep_light_sec: int | None,
    sleep_rem_sec: int | None,
    all_day_stress: int | None,
    body_battery: int | None,
) -> None:
    conn.execute(
        """
        INSERT INTO source_daily_garmin (
            as_of_date, user_id, export_batch_id, csv_row_index,
            source, ingest_actor, ingested_at,
            sleep_deep_sec, sleep_light_sec, sleep_rem_sec,
            all_day_stress, body_battery
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            AS_OF.isoformat(), USER, "batch_x", 0,
            "garmin", "garmin_csv_adapter", "2026-04-17T06:00:00Z",
            sleep_deep_sec, sleep_light_sec, sleep_rem_sec,
            all_day_stress, body_battery,
        ),
    )
    conn.commit()


def _seed_stress_manual_raw(
    conn: sqlite3.Connection, *, score: int,
) -> None:
    conn.execute(
        """
        INSERT INTO stress_manual_raw (
            submission_id, user_id, as_of_date,
            score, tags, source, ingest_actor, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"m_stress_2026-04-17_{score}",
            USER, AS_OF.isoformat(),
            score, None,
            "user_manual", "hai_cli_direct", "2026-04-17T14:00:00Z",
        ),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Happy path: accepted values match raw → no mismatches
# ---------------------------------------------------------------------------

def test_dry_run_diff_empty_when_accepted_matches_raw(tmp_path: Path):
    """A row produced cleanly from raw has no mismatches — the migration
    is safe to run forward."""

    db = _init_db_at_version_3(tmp_path)
    conn = open_connection(db)
    try:
        # sleep_hours = (5400 + 12600 + 5400) / 3600 = 6.5
        _seed_source_daily_garmin(
            conn,
            sleep_deep_sec=5400, sleep_light_sec=12600, sleep_rem_sec=5400,
            all_day_stress=30, body_battery=65,
        )
        _seed_stress_manual_raw(conn, score=3)
        _seed_pre_004_recovery_row(
            conn,
            sleep_hours=6.5, all_day_stress=30,
            manual_stress_score=3, body_battery_end_of_day=65,
        )
        diff = migration_004_dry_run_diff(conn)
    finally:
        conn.close()

    assert diff["migration"] == "004_sleep_stress_tables"
    assert diff["schema_version"] == 3
    assert diff["rows_checked"] == 1
    assert diff["mismatches"] == []


# ---------------------------------------------------------------------------
# Divergence: each moving column surfaces independently
# ---------------------------------------------------------------------------

def test_dry_run_diff_surfaces_sleep_hours_divergence(tmp_path: Path):
    """Accepted recovery holds sleep_hours that disagrees with raw —
    surfaces as a mismatch for sleep_hours."""

    db = _init_db_at_version_3(tmp_path)
    conn = open_connection(db)
    try:
        # Raw says 6.5; accepted says 8.0 (a manual patch, say).
        _seed_source_daily_garmin(
            conn,
            sleep_deep_sec=5400, sleep_light_sec=12600, sleep_rem_sec=5400,
            all_day_stress=30, body_battery=65,
        )
        _seed_pre_004_recovery_row(
            conn,
            sleep_hours=8.0, all_day_stress=30,
            manual_stress_score=None, body_battery_end_of_day=65,
        )
        diff = migration_004_dry_run_diff(conn)
    finally:
        conn.close()

    assert diff["rows_checked"] == 1
    sleep_mismatches = [m for m in diff["mismatches"] if m["field"] == "sleep_hours"]
    assert len(sleep_mismatches) == 1
    assert sleep_mismatches[0]["accepted_value"] == 8.0
    assert sleep_mismatches[0]["reprojected_value"] == pytest.approx(6.5, rel=0.01)


def test_dry_run_diff_surfaces_missing_raw_as_divergence(tmp_path: Path):
    """Accepted has a value but no raw exists — the reprojected value
    would be NULL, so the helper flags the divergence."""

    db = _init_db_at_version_3(tmp_path)
    conn = open_connection(db)
    try:
        _seed_pre_004_recovery_row(
            conn,
            sleep_hours=7.0, all_day_stress=30,
            manual_stress_score=4, body_battery_end_of_day=50,
        )
        # No source_daily_garmin row, no stress_manual_raw row — a
        # degenerate legacy state.
        diff = migration_004_dry_run_diff(conn)
    finally:
        conn.close()

    fields = {m["field"] for m in diff["mismatches"]}
    assert fields == {
        "sleep_hours", "all_day_stress",
        "manual_stress_score", "body_battery_end_of_day",
    }
    for m in diff["mismatches"]:
        assert m["reprojected_value"] is None
        assert m["accepted_value"] is not None


def test_dry_run_diff_surfaces_manual_score_divergence(tmp_path: Path):
    """Manual stress score on accepted != latest raw score — flagged."""

    db = _init_db_at_version_3(tmp_path)
    conn = open_connection(db)
    try:
        _seed_source_daily_garmin(
            conn,
            sleep_deep_sec=5400, sleep_light_sec=12600, sleep_rem_sec=5400,
            all_day_stress=30, body_battery=65,
        )
        _seed_stress_manual_raw(conn, score=3)
        _seed_pre_004_recovery_row(
            conn,
            sleep_hours=6.5, all_day_stress=30,
            manual_stress_score=5,  # diverges from raw's 3
            body_battery_end_of_day=65,
        )
        diff = migration_004_dry_run_diff(conn)
    finally:
        conn.close()

    manual_mismatches = [m for m in diff["mismatches"]
                          if m["field"] == "manual_stress_score"]
    assert len(manual_mismatches) == 1
    assert manual_mismatches[0]["accepted_value"] == 5
    assert manual_mismatches[0]["reprojected_value"] == 3


# ---------------------------------------------------------------------------
# Misuse guards
# ---------------------------------------------------------------------------

def test_dry_run_diff_rejects_when_already_at_version_4(tmp_path: Path):
    """Running the gate on a DB already past migration 004 is a bug —
    the helper is a pre-apply check."""

    db = tmp_path / "state.db"
    initialize_database(db)  # applies all migrations including 004
    conn = open_connection(db)
    try:
        assert current_schema_version(conn) >= 4
        with pytest.raises(RuntimeError) as exc:
            migration_004_dry_run_diff(conn)
        assert "already at schema version" in str(exc.value)
    finally:
        conn.close()


def test_dry_run_diff_rejects_on_empty_db(tmp_path: Path):
    """A DB with no migrations applied yet isn't a valid target either —
    needs at least migration 003 for the schema the gate compares against."""

    db_path = tmp_path / "empty.db"
    conn = open_connection(db_path)
    try:
        with pytest.raises(RuntimeError) as exc:
            migration_004_dry_run_diff(conn)
        assert "schema version" in str(exc.value)
    finally:
        conn.close()


def test_dry_run_diff_empty_db_at_version_3_checks_zero_rows(tmp_path: Path):
    """A fresh version-3 DB with no accepted rows has nothing to check —
    gate returns cleanly with rows_checked=0."""

    db = _init_db_at_version_3(tmp_path)
    conn = open_connection(db)
    try:
        diff = migration_004_dry_run_diff(conn)
    finally:
        conn.close()

    assert diff["schema_version"] == 3
    assert diff["rows_checked"] == 0
    assert diff["mismatches"] == []


# ---------------------------------------------------------------------------
# Orphan flag on x_rule_firing (Phase 2.5 Condition 1)
# ---------------------------------------------------------------------------

def test_migration_004_adds_orphan_column_to_x_rule_firing(tmp_path: Path):
    """Phase 2.5 independent-eval Condition 1 carries forward as a
    schema-level defense: every x_rule_firing row gets an `orphan`
    column, default 0. Current rules never emit orphans; the column is
    a safety net for future rules that fire on snapshot-only signals."""

    db = tmp_path / "state.db"
    initialize_database(db)
    conn = open_connection(db)
    try:
        cols = {r["name"]: r for r in conn.execute(
            "PRAGMA table_info(x_rule_firing)"
        ).fetchall()}
    finally:
        conn.close()

    assert "orphan" in cols
    assert cols["orphan"]["notnull"] == 1
    assert cols["orphan"]["dflt_value"] == "0"
