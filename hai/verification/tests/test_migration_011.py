"""Phase 1 — migration 011 creates the planned_recommendation ledger.

Contracts pinned:

  1. Migration 011 creates the ``planned_recommendation`` table with the
     columns documented in §1 of
     ``hai/reporting/plans/historical/agent_operable_runtime_plan.md`` (per-domain rows,
     Option 2 locked).
  2. The three supporting indexes exist:
     - ``idx_planned_recommendation_daily_plan``
     - ``idx_planned_recommendation_for_date``
     - ``idx_planned_recommendation_proposal``
  3. ``daily_plan_id`` and ``proposal_id`` carry enforceable FK references
     (SQLite's ``foreign_keys`` pragma is on by default via
     ``open_connection``; inserts with unknown parent ids fail).
  4. ``action_detail_json`` is nullable — not every domain uses it.
  5. No backfill happens — legacy ``daily_plan`` rows from before 011
     legitimately lack a paired ``planned_recommendation`` row. The
     explain surface handles this via graceful two-state degradation.

Pre-011 state is simulated by running migrations 001..010 only, then
applying 011 against that DB.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    apply_pending_migrations,
    current_schema_version,
    initialize_database,
    open_connection,
)
from health_agent_infra.core.state.store import discover_migrations


def _seed_at_v10(tmp_path: Path) -> Path:
    """Return a DB path with migrations 001..010 applied, NOT 011."""

    db = tmp_path / "state.db"
    all_migrations = discover_migrations()
    pre_011 = [m for m in all_migrations if m[0] < 11]
    assert any(version == 10 for version, _, _ in pre_011), (
        "test assumes migration 010 exists — if it doesn't, this "
        "test's pre-state is different from what it claims to be"
    )
    conn = open_connection(db)
    try:
        applied = apply_pending_migrations(conn, migrations=pre_011)
        assert [v for v, _ in applied] == [m[0] for m in pre_011]
    finally:
        conn.close()
    return db


def _run_migration_011(db: Path) -> None:
    all_migrations = discover_migrations()
    eleven = [m for m in all_migrations if m[0] == 11]
    assert len(eleven) == 1, "expected exactly one migration 011"
    conn = open_connection(db)
    try:
        applied = apply_pending_migrations(conn, migrations=eleven)
        assert applied == [(11, "011_planned_recommendation.sql")]
    finally:
        conn.close()


def _columns(conn: sqlite3.Connection, table: str) -> dict[str, dict]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"]: dict(row) for row in rows}


# ---------------------------------------------------------------------------
# Table shape
# ---------------------------------------------------------------------------


def test_planned_recommendation_table_created(tmp_path: Path):
    db = _seed_at_v10(tmp_path)
    _run_migration_011(db)

    conn = open_connection(db)
    try:
        cols = _columns(conn, "planned_recommendation")
    finally:
        conn.close()

    expected = {
        "planned_id", "daily_plan_id", "proposal_id", "user_id", "for_date",
        "domain", "action", "confidence", "action_detail_json",
        "schema_version", "source", "ingest_actor", "agent_version",
        "captured_at",
    }
    assert set(cols) == expected, (
        f"unexpected columns; got {sorted(cols)}, want {sorted(expected)}"
    )


def test_primary_key_is_planned_id(tmp_path: Path):
    db = _seed_at_v10(tmp_path)
    _run_migration_011(db)
    conn = open_connection(db)
    try:
        cols = _columns(conn, "planned_recommendation")
    finally:
        conn.close()
    assert cols["planned_id"]["pk"] == 1


def test_action_detail_json_is_nullable(tmp_path: Path):
    """Not every domain uses action_detail — the column must accept NULL."""

    db = _seed_at_v10(tmp_path)
    _run_migration_011(db)
    conn = open_connection(db)
    try:
        cols = _columns(conn, "planned_recommendation")
    finally:
        conn.close()
    assert cols["action_detail_json"]["notnull"] == 0


def test_required_columns_are_not_null(tmp_path: Path):
    """Non-PK required columns must be NOT NULL. ``planned_id`` is the PK
    and SQLite's table_info reports notnull=0 for TEXT PRIMARY KEY columns
    (matches repo convention — see ``proposal_log.proposal_id`` in
    migration 003); PK uniqueness/non-null is enforced by the PK
    constraint itself, covered by the separate PK test."""

    db = _seed_at_v10(tmp_path)
    _run_migration_011(db)
    conn = open_connection(db)
    try:
        cols = _columns(conn, "planned_recommendation")
    finally:
        conn.close()
    for name in (
        "daily_plan_id", "proposal_id", "user_id", "for_date",
        "domain", "action", "confidence", "schema_version", "source",
        "ingest_actor", "captured_at",
    ):
        assert cols[name]["notnull"] == 1, (
            f"column {name} must be NOT NULL"
        )


# ---------------------------------------------------------------------------
# Indexes
# ---------------------------------------------------------------------------


def test_indexes_created(tmp_path: Path):
    db = _seed_at_v10(tmp_path)
    _run_migration_011(db)

    conn = open_connection(db)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'index' AND tbl_name = 'planned_recommendation'"
        ).fetchall()
        names = {r["name"] for r in rows}
    finally:
        conn.close()

    for expected in (
        "idx_planned_recommendation_daily_plan",
        "idx_planned_recommendation_for_date",
        "idx_planned_recommendation_proposal",
    ):
        assert expected in names, (
            f"expected index {expected!r}; got {sorted(names)}"
        )


def test_daily_plan_lookup_uses_index(tmp_path: Path):
    db = _seed_at_v10(tmp_path)
    _run_migration_011(db)
    conn = open_connection(db)
    try:
        plan = conn.execute(
            "EXPLAIN QUERY PLAN "
            "SELECT planned_id FROM planned_recommendation "
            "WHERE daily_plan_id = ?",
            ("plan_2026-04-22_u_test",),
        ).fetchall()
        plan_text = "\n".join(row["detail"] for row in plan)
    finally:
        conn.close()
    assert "idx_planned_recommendation_daily_plan" in plan_text, (
        f"expected dedicated index hit; got plan:\n{plan_text}"
    )


def test_for_date_domain_lookup_uses_index(tmp_path: Path):
    db = _seed_at_v10(tmp_path)
    _run_migration_011(db)
    conn = open_connection(db)
    try:
        plan = conn.execute(
            "EXPLAIN QUERY PLAN "
            "SELECT planned_id FROM planned_recommendation "
            "WHERE for_date = ? AND user_id = ? AND domain = ?",
            ("2026-04-22", "u_test", "recovery"),
        ).fetchall()
        plan_text = "\n".join(row["detail"] for row in plan)
    finally:
        conn.close()
    assert "idx_planned_recommendation_for_date" in plan_text, (
        f"expected dedicated index hit; got plan:\n{plan_text}"
    )


# ---------------------------------------------------------------------------
# FK enforcement
# ---------------------------------------------------------------------------


def _insert_planned_row(
    conn: sqlite3.Connection,
    *,
    planned_id: str,
    daily_plan_id: str,
    proposal_id: str,
) -> None:
    conn.execute(
        """
        INSERT INTO planned_recommendation (
            planned_id, daily_plan_id, proposal_id, user_id, for_date,
            domain, action, confidence, action_detail_json,
            schema_version, source, ingest_actor, agent_version, captured_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            planned_id, daily_plan_id, proposal_id, "u_test", "2026-04-22",
            "recovery", "proceed_with_planned_run", "high", None,
            "planned_recommendation.v1", "claude_agent_v1",
            "claude_agent_v1", None,
            "2026-04-22T10:00:00+00:00",
        ),
    )


def _insert_daily_plan_row(
    conn: sqlite3.Connection, *, daily_plan_id: str,
) -> None:
    """Insert the minimum daily_plan row needed to satisfy the FK."""
    conn.execute(
        """
        INSERT INTO daily_plan (
            daily_plan_id, user_id, for_date, synthesized_at,
            recommendation_ids_json, proposal_ids_json, x_rules_fired_json,
            synthesis_meta_json, source, ingest_actor, agent_version,
            validated_at, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            daily_plan_id, "u_test", "2026-04-22",
            "2026-04-22T10:00:00+00:00",
            "[]", "[]", "[]", None,
            "claude_agent_v1", "claude_agent_v1", None,
            "2026-04-22T10:00:00+00:00",
            "2026-04-22T10:00:00+00:00",
        ),
    )


def _insert_proposal_row(
    conn: sqlite3.Connection, *, proposal_id: str,
) -> None:
    """Insert the minimum proposal_log row needed to satisfy the FK."""
    conn.execute(
        """
        INSERT INTO proposal_log (
            proposal_id, daily_plan_id, user_id, domain, for_date,
            schema_version, action, confidence, payload_json,
            source, ingest_actor, agent_version, produced_at,
            validated_at, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            proposal_id, None, "u_test", "recovery", "2026-04-22",
            "domain_proposal.v1", "proceed_with_planned_run", "high",
            "{}",
            "claude_agent_v1", "claude_agent_v1", None, None,
            "2026-04-22T10:00:00+00:00",
            "2026-04-22T10:00:00+00:00",
        ),
    )


def test_fk_to_daily_plan_rejects_unknown_id(tmp_path: Path):
    """Inserting a planned row whose daily_plan_id doesn't exist must fail."""

    db = _seed_at_v10(tmp_path)
    _run_migration_011(db)
    conn = open_connection(db)
    try:
        _insert_proposal_row(conn, proposal_id="prop_x")
        with pytest.raises(sqlite3.IntegrityError):
            _insert_planned_row(
                conn,
                planned_id="planned_x",
                daily_plan_id="plan_does_not_exist",
                proposal_id="prop_x",
            )
    finally:
        conn.close()


def test_fk_to_proposal_log_rejects_unknown_id(tmp_path: Path):
    """Inserting a planned row whose proposal_id doesn't exist must fail."""

    db = _seed_at_v10(tmp_path)
    _run_migration_011(db)
    conn = open_connection(db)
    try:
        _insert_daily_plan_row(conn, daily_plan_id="plan_x")
        with pytest.raises(sqlite3.IntegrityError):
            _insert_planned_row(
                conn,
                planned_id="planned_x",
                daily_plan_id="plan_x",
                proposal_id="prop_does_not_exist",
            )
    finally:
        conn.close()


def test_valid_fks_allow_insert(tmp_path: Path):
    """Sanity: with both parent rows present, the insert succeeds."""

    db = _seed_at_v10(tmp_path)
    _run_migration_011(db)
    conn = open_connection(db)
    try:
        _insert_daily_plan_row(conn, daily_plan_id="plan_x")
        _insert_proposal_row(conn, proposal_id="prop_x")
        _insert_planned_row(
            conn,
            planned_id="planned_x",
            daily_plan_id="plan_x",
            proposal_id="prop_x",
        )
        row = conn.execute(
            "SELECT planned_id, daily_plan_id, proposal_id "
            "FROM planned_recommendation WHERE planned_id = ?",
            ("planned_x",),
        ).fetchone()
    finally:
        conn.close()
    assert dict(row) == {
        "planned_id": "planned_x",
        "daily_plan_id": "plan_x",
        "proposal_id": "prop_x",
    }


# ---------------------------------------------------------------------------
# Schema-version HEAD
# ---------------------------------------------------------------------------


def test_schema_version_at_head_is_at_least_eleven(tmp_path: Path):
    """Pin the lower bound. The exact head lives in test_state_store."""

    db = tmp_path / "state.db"
    initialize_database(db)
    conn = open_connection(db)
    try:
        assert current_schema_version(conn) >= 11
    finally:
        conn.close()
