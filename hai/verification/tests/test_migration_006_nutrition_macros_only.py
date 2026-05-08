"""Phase 5 step 1 — migration 006 (macros-only nutrition derivation_path).

Contracts pinned:

  1. Migration 006 applies cleanly from head (pre-006 schema = 5). After
     ``initialize_database``, ``current_schema_version`` is 6.
  2. ``accepted_nutrition_state_daily`` gains a ``derivation_path`` column
     that is NOT NULL with default ``'daily_macros'``. Pre-existing rows
     created before the migration applied get the default backfilled.
  3. The v1 nutrition projector
     (``project_accepted_nutrition_state_daily``) writes
     ``derivation_path='daily_macros'`` explicitly on both INSERT and
     UPDATE. This is the writer-side invariant: v1 code never emits any
     other value.
  4. No meal_log / food_taxonomy tables are introduced — Phase 2.5's
     retrieval gate failed and the plan's meal-level deliverables are
     deferred. The pre-existing ``nutrition_intake_raw`` table is left
     verbatim.
  5. Pre-existing accepted nutrition columns (calories, protein_g,
     carbs_g, fat_g, hydration_l, meals_count, derived_from, source,
     ingest_actor, projected_at, corrected_at) are preserved — this
     migration is additive-only for v1.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    current_schema_version,
    initialize_database,
    open_connection,
)
from health_agent_infra.core.state.projector import (
    project_accepted_nutrition_state_daily,
    project_nutrition_intake_raw,
)


USER = "u_test"
AS_OF = date(2026, 4, 18)


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _nutrition_columns(conn: sqlite3.Connection) -> dict[str, dict]:
    """Return {column_name: {cid, type, notnull, dflt_value, pk}} for the
    accepted nutrition table."""

    rows = conn.execute(
        "PRAGMA table_info(accepted_nutrition_state_daily)"
    ).fetchall()
    return {row["name"]: dict(row) for row in rows}


# ---------------------------------------------------------------------------
# Schema shape
# ---------------------------------------------------------------------------

def test_head_schema_version_is_six_after_migration_006(tmp_path: Path):
    # Intent: migration 006 advances schema past 5. Head version moves
    # forward with each later migration (007 added user memory); this
    # test pins the lower bound rather than exact head so adding
    # migrations doesn't require touching every suite. The exact head
    # version lives in ``test_state_store``.
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        assert current_schema_version(conn) >= 6
    finally:
        conn.close()


def test_accepted_nutrition_gains_derivation_path_column(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        cols = _nutrition_columns(conn)
    finally:
        conn.close()

    assert "derivation_path" in cols, (
        f"migration 006 did not add derivation_path; columns = {sorted(cols)}"
    )
    col = cols["derivation_path"]
    assert col["type"].upper() == "TEXT"
    assert col["notnull"] == 1, "derivation_path must be NOT NULL"
    # The DDL default carries the quotes; strip to the literal value.
    dflt = col["dflt_value"]
    assert dflt is not None
    assert dflt.strip("'\"") == "daily_macros"


def test_preexisting_nutrition_columns_preserved(tmp_path: Path):
    """Migration 006 is additive-only for v1. Every column that existed
    pre-006 must still be present — this is the read-compatibility
    invariant the snapshot + projector rely on."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        cols = _nutrition_columns(conn)
    finally:
        conn.close()

    expected = {
        "as_of_date", "user_id",
        "calories", "protein_g", "carbs_g", "fat_g",
        "hydration_l", "meals_count",
        "derived_from", "source", "ingest_actor",
        "projected_at", "corrected_at",
    }
    missing = expected - set(cols)
    assert not missing, f"migration 006 dropped pre-existing columns: {sorted(missing)}"


def test_meal_level_tables_do_not_exist(tmp_path: Path):
    """Phase 2.5's retrieval gate failed; meal_log + food_taxonomy defer
    to a post-v1 release. Make sure migration 006 did NOT silently
    introduce either surface — a reviewer catches drift here instead of
    in production data shape."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        names = {
            r["name"] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert "meal_log" not in names
    assert "food_taxonomy" not in names


# ---------------------------------------------------------------------------
# Projector writes derivation_path='daily_macros'
# ---------------------------------------------------------------------------

def _seed_raw_submission(conn: sqlite3.Connection, *, submission_id: str,
                         calories: float, protein_g: float) -> None:
    assert project_nutrition_intake_raw(
        conn,
        submission_id=submission_id,
        user_id=USER,
        as_of_date=AS_OF,
        calories=calories,
        protein_g=protein_g,
        carbs_g=250,
        fat_g=70,
        hydration_l=2.0,
        meals_count=3,
        ingest_actor="test_actor",
        commit_after=False,
    )


def test_projector_stamps_daily_macros_on_insert(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_raw_submission(conn, submission_id="sub_001", calories=2100, protein_g=150)
        is_insert = project_accepted_nutrition_state_daily(
            conn,
            as_of_date=AS_OF,
            user_id=USER,
            ingest_actor="test_actor",
            commit_after=False,
        )
        assert is_insert is True

        row = conn.execute(
            "SELECT derivation_path, calories, corrected_at "
            "FROM accepted_nutrition_state_daily "
            "WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchone()
    finally:
        conn.close()

    assert row is not None
    assert row["derivation_path"] == "daily_macros"
    assert row["calories"] == 2100
    assert row["corrected_at"] is None


def test_projector_stamps_daily_macros_on_correction_update(tmp_path: Path):
    """On re-projection (supersession / correction path), the projector
    must re-stamp derivation_path='daily_macros' alongside the rest of
    the UPDATE — never leave the column value to drift."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_raw_submission(conn, submission_id="sub_001", calories=2100, protein_g=150)
        project_accepted_nutrition_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="test_actor", commit_after=False,
        )

        # Second submission supersedes the first; re-project.
        conn.execute(
            """
            INSERT INTO nutrition_intake_raw (
                submission_id, user_id, as_of_date,
                calories, protein_g, carbs_g, fat_g,
                hydration_l, meals_count,
                source, ingest_actor, ingested_at,
                supersedes_submission_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            """,
            ("sub_002", USER, AS_OF.isoformat(),
             2400, 180, 260, 75, 2.3, 3,
             "user_manual", "test_actor", "sub_001"),
        )
        is_insert = project_accepted_nutrition_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="test_actor", commit_after=False,
        )
        assert is_insert is False  # update

        row = conn.execute(
            "SELECT derivation_path, calories, corrected_at "
            "FROM accepted_nutrition_state_daily "
            "WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchone()
    finally:
        conn.close()

    assert row["derivation_path"] == "daily_macros"
    assert row["calories"] == 2400
    assert row["corrected_at"] is not None


# ---------------------------------------------------------------------------
# Snapshot carries derivation_path through on the nutrition.today block
# ---------------------------------------------------------------------------

def test_snapshot_nutrition_today_carries_derivation_path(tmp_path: Path):
    from health_agent_infra.core.state import build_snapshot

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_raw_submission(conn, submission_id="sub_001", calories=2100, protein_g=150)
        project_accepted_nutrition_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="test_actor", commit_after=True,
        )
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 4, 19, 10, 0),
        )
    finally:
        conn.close()

    today = snap["nutrition"]["today"]
    assert today is not None
    assert today["derivation_path"] == "daily_macros"


def test_snapshot_missingness_ignores_derivation_path(tmp_path: Path):
    """derivation_path is metadata, not required evidence. A row with full
    macros + derivation_path='daily_macros' should emit missingness='present'
    even though derivation_path is a new column."""

    from health_agent_infra.core.state import build_snapshot

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_raw_submission(conn, submission_id="sub_001", calories=2100, protein_g=150)
        project_accepted_nutrition_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="test_actor", commit_after=True,
        )
        # Snapshot "tomorrow" so the day is closed and missingness resolves.
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 4, 19, 10, 0),
        )
    finally:
        conn.close()

    assert snap["nutrition"]["missingness"] == "present"
