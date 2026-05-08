"""M3 — migration 009 promotes ``daily_plan_id`` to a real column.

Contracts pinned:

  1. Migration 009 adds ``recommendation_log.daily_plan_id`` as a
     nullable TEXT column.
  2. The index ``idx_recommendation_log_daily_plan_id`` exists and is
     used by the natural ``WHERE daily_plan_id = ?`` lookup.
  3. Backfill: rows that existed pre-009 with ``daily_plan_id`` inside
     their ``payload_json`` are populated.
  4. Backfill: legacy rows (pre-synthesis recovery-only path) that
     have no ``daily_plan_id`` in payload_json stay NULL — the column
     is intentionally sparse, not invented.
  5. New writes via ``project_bounded_recommendation`` land the column
     as well as the payload copy.

Pre-M3 state is simulated by running migrations 001..008 only, seeding
rows with the legacy schema, then applying 009 against that DB.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    apply_pending_migrations,
    current_schema_version,
    initialize_database,
    open_connection,
)
from health_agent_infra.core.state.projector import (
    project_bounded_recommendation,
)
from health_agent_infra.core.state.store import discover_migrations


def _seed_at_v8(tmp_path: Path) -> Path:
    """Return a DB path with migrations 001..008 applied, NOT 009.

    Filters the packaged migration list to everything strictly before
    009. The test then runs 009 explicitly so the backfill + column
    addition are the *only* schema change between seeding and assertion.
    """

    db = tmp_path / "state.db"
    all_migrations = discover_migrations()
    pre_009 = [m for m in all_migrations if m[0] < 9]
    assert any(version == 8 for version, _, _ in pre_009), (
        "test assumes migration 008 exists (M2 shipped) — if it doesn't, "
        "this test's pre-state is different from what it claims to be"
    )
    conn = open_connection(db)
    try:
        applied = apply_pending_migrations(conn, migrations=pre_009)
        assert [v for v, _ in applied] == [m[0] for m in pre_009]
    finally:
        conn.close()
    return db


def _run_migration_009(db: Path) -> None:
    all_migrations = discover_migrations()
    nine = [m for m in all_migrations if m[0] == 9]
    assert len(nine) == 1, "expected exactly one migration 009"
    conn = open_connection(db)
    try:
        applied = apply_pending_migrations(conn, migrations=nine)
        assert applied == [(9, "009_recommendation_log_fk.sql")]
    finally:
        conn.close()


def _recommendation_columns(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = conn.execute("PRAGMA table_info(recommendation_log)").fetchall()
    return {row["name"]: dict(row) for row in rows}


def _insert_legacy_recommendation(
    conn: sqlite3.Connection,
    *,
    recommendation_id: str,
    daily_plan_id: str | None,
) -> None:
    """Insert a recommendation_log row using the pre-009 schema.

    payload_json carries ``daily_plan_id`` when provided; the column
    does not exist yet so we simply don't mention it in the INSERT.
    """

    payload = {
        "recommendation_id": recommendation_id,
        "user_id": "u_test",
        "for_date": "2026-04-17",
        "issued_at": "2026-04-17T10:00:00+00:00",
        "action": "proceed_with_planned_run",
        "confidence": "high",
        "bounded": True,
    }
    if daily_plan_id is not None:
        payload["daily_plan_id"] = daily_plan_id

    conn.execute(
        """
        INSERT INTO recommendation_log (
            recommendation_id, user_id, for_date, issued_at,
            action, confidence, bounded, payload_json,
            jsonl_offset, source, ingest_actor, agent_version,
            produced_at, validated_at, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            recommendation_id, "u_test", "2026-04-17",
            "2026-04-17T10:00:00+00:00",
            "proceed_with_planned_run", "high", 1,
            json.dumps(payload, sort_keys=True),
            None, "claude_agent_v1", "claude_agent_v1", None,
            "2026-04-17T10:00:00+00:00",
            "2026-04-17T10:00:01+00:00",
            "2026-04-17T10:00:01+00:00",
        ),
    )


# ---------------------------------------------------------------------------
# Column shape
# ---------------------------------------------------------------------------


def test_daily_plan_id_column_added_as_nullable_text(tmp_path: Path):
    db = _seed_at_v8(tmp_path)
    _run_migration_009(db)

    conn = open_connection(db)
    try:
        cols = _recommendation_columns(conn)
    finally:
        conn.close()

    assert "daily_plan_id" in cols, (
        f"migration 009 did not add daily_plan_id; columns = {sorted(cols)}"
    )
    col = cols["daily_plan_id"]
    assert col["type"].upper() == "TEXT"
    assert col["notnull"] == 0, (
        "daily_plan_id must be nullable — legacy writeback rows carry no "
        "plan id and should stay NULL after migration"
    )


def test_index_on_daily_plan_id_is_present(tmp_path: Path):
    db = _seed_at_v8(tmp_path)
    _run_migration_009(db)

    conn = open_connection(db)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'index' AND tbl_name = 'recommendation_log'"
        ).fetchall()
        index_names = {r["name"] for r in rows}
    finally:
        conn.close()

    assert "idx_recommendation_log_daily_plan_id" in index_names, (
        f"expected the new index; found: {sorted(index_names)}"
    )


def test_daily_plan_lookup_uses_new_index(tmp_path: Path):
    """EXPLAIN QUERY PLAN must show the explain-loader / cascade-delete
    WHERE clause hits the dedicated index, not a full table scan."""

    db = _seed_at_v8(tmp_path)
    _run_migration_009(db)

    conn = open_connection(db)
    try:
        plan = conn.execute(
            "EXPLAIN QUERY PLAN "
            "SELECT recommendation_id FROM recommendation_log "
            "WHERE daily_plan_id = ?",
            ("plan_2026-04-17_u_test",),
        ).fetchall()
        plan_text = "\n".join(row["detail"] for row in plan)
    finally:
        conn.close()

    assert "idx_recommendation_log_daily_plan_id" in plan_text, (
        f"daily_plan_id lookup should use the dedicated index; "
        f"got plan:\n{plan_text}"
    )


# ---------------------------------------------------------------------------
# Backfill behavior
# ---------------------------------------------------------------------------


def test_backfill_populates_column_from_payload_json(tmp_path: Path):
    db = _seed_at_v8(tmp_path)
    conn = open_connection(db)
    try:
        _insert_legacy_recommendation(
            conn, recommendation_id="rec_a",
            daily_plan_id="plan_2026-04-17_u_test",
        )
        _insert_legacy_recommendation(
            conn, recommendation_id="rec_b",
            daily_plan_id="plan_2026-04-18_u_test",
        )
        conn.commit()
    finally:
        conn.close()

    _run_migration_009(db)

    conn = open_connection(db)
    try:
        rows = dict(conn.execute(
            "SELECT recommendation_id, daily_plan_id FROM recommendation_log "
            "ORDER BY recommendation_id"
        ).fetchall())
    finally:
        conn.close()

    assert rows == {
        "rec_a": "plan_2026-04-17_u_test",
        "rec_b": "plan_2026-04-18_u_test",
    }


def test_backfill_leaves_legacy_rows_null(tmp_path: Path):
    """Rows with no daily_plan_id in payload_json (e.g. pre-synthesis
    recovery-only writeback output) remain NULL. The column is
    intentionally sparse."""

    db = _seed_at_v8(tmp_path)
    conn = open_connection(db)
    try:
        _insert_legacy_recommendation(
            conn, recommendation_id="rec_legacy", daily_plan_id=None,
        )
        conn.commit()
    finally:
        conn.close()

    _run_migration_009(db)

    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT daily_plan_id FROM recommendation_log "
            "WHERE recommendation_id = ?",
            ("rec_legacy",),
        ).fetchone()
    finally:
        conn.close()

    assert row["daily_plan_id"] is None


# ---------------------------------------------------------------------------
# Post-migration writer: the projector now populates the column
# ---------------------------------------------------------------------------


def test_project_bounded_recommendation_writes_column_after_migration(tmp_path: Path):
    db = _seed_at_v8(tmp_path)
    _run_migration_009(db)
    # At this point the DB is at v9 but not at packaged HEAD. Bring it
    # fully up to date (no-op if 009 is HEAD at the time this test
    # runs, forward-compatible if a later migration lands).
    initialize_database(db)

    recommendation = {
        "recommendation_id": "rec_new",
        "user_id": "u_test",
        "for_date": "2026-04-18",
        "issued_at": "2026-04-18T09:00:00+00:00",
        "action": "proceed_with_planned_run",
        "confidence": "high",
        "bounded": True,
        "domain": "running",
        "daily_plan_id": "plan_2026-04-18_u_test",
    }
    conn = open_connection(db)
    try:
        project_bounded_recommendation(conn, recommendation)
        row = conn.execute(
            "SELECT daily_plan_id FROM recommendation_log "
            "WHERE recommendation_id = ?",
            ("rec_new",),
        ).fetchone()
    finally:
        conn.close()

    assert row["daily_plan_id"] == "plan_2026-04-18_u_test"


def test_current_schema_version_at_head_is_at_least_nine(tmp_path: Path):
    """Pin the lower bound so adding migrations 010+ doesn't touch this
    file. The exact head lives in test_state_store."""

    db = tmp_path / "state.db"
    initialize_database(db)
    conn = open_connection(db)
    try:
        assert current_schema_version(conn) >= 9
    finally:
        conn.close()
