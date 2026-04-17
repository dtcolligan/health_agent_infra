"""Tests for Phase 7A.1 — SQLite state store substrate.

Scope per the 7A.1 contract:
  - `hai state init` creates the DB file, applies migration 001, stamps
    schema_migrations.
  - `hai state migrate` is idempotent: re-running against a head DB applies
    nothing and leaves version untouched.
  - The bookkeeping table records every applied migration exactly once.
  - WAL mode + foreign keys are enabled on every new connection.

Out of scope (later phases): projection, dual-write, read CLIs, snapshot.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.state import (
    apply_pending_migrations,
    current_schema_version,
    initialize_database,
    open_connection,
    resolve_db_path,
)


# ---------------------------------------------------------------------------
# resolve_db_path
# ---------------------------------------------------------------------------

def test_resolve_db_path_prefers_explicit(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("HAI_STATE_DB", str(tmp_path / "env.db"))
    explicit = tmp_path / "explicit.db"
    assert resolve_db_path(explicit) == explicit


def test_resolve_db_path_honours_env_var(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("HAI_STATE_DB", str(tmp_path / "env.db"))
    assert resolve_db_path() == tmp_path / "env.db"


def test_resolve_db_path_falls_back_to_platform_default(monkeypatch):
    monkeypatch.delenv("HAI_STATE_DB", raising=False)
    resolved = resolve_db_path()
    assert resolved.name == "state.db"
    assert "health_agent_infra" in resolved.parts


# ---------------------------------------------------------------------------
# initialize_database
# ---------------------------------------------------------------------------

def test_initialize_database_creates_file_and_applies_all_migrations(tmp_path: Path):
    db_path = tmp_path / "new.db"
    assert not db_path.exists()

    resolved, applied = initialize_database(db_path)

    assert resolved == db_path
    assert db_path.exists()
    assert len(applied) >= 1
    # 001 must always be first; additional migrations accumulate after.
    assert applied[0] == (1, "001_initial.sql")
    versions = [v for v, _ in applied]
    assert versions == sorted(versions)


def test_initialize_database_creates_parent_dir_if_missing(tmp_path: Path):
    db_path = tmp_path / "nested" / "deep" / "state.db"
    assert not db_path.parent.exists()

    initialize_database(db_path)

    assert db_path.exists()


def test_initialize_database_is_idempotent(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    _resolved, applied_again = initialize_database(db_path)
    assert applied_again == []


# ---------------------------------------------------------------------------
# Version bookkeeping
# ---------------------------------------------------------------------------

def test_schema_migrations_has_one_row_per_applied_migration(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT version, filename FROM schema_migrations ORDER BY version"
        ).fetchall()
    finally:
        conn.close()

    assert [tuple(r) for r in rows] == [
        (1, "001_initial.sql"),
        (2, "002_rename_training_readiness_pct.sql"),
        (3, "003_synthesis_scaffolding.sql"),
    ]


def test_schema_migrations_not_duplicated_on_repeat_init(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    initialize_database(db_path)
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) AS n FROM schema_migrations").fetchone()["n"]
    finally:
        conn.close()

    assert count == 3


def test_current_schema_version_zero_on_empty_db(tmp_path: Path):
    db_path = tmp_path / "empty.db"
    conn = open_connection(db_path)
    try:
        assert current_schema_version(conn) == 0
    finally:
        conn.close()


def test_current_schema_version_matches_head_after_init(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        assert current_schema_version(conn) == 3
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# apply_pending_migrations
# ---------------------------------------------------------------------------

def test_apply_pending_migrations_no_op_at_head(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        applied = apply_pending_migrations(conn)
    finally:
        conn.close()

    assert applied == []


def test_apply_pending_migrations_runs_all_migrations_on_empty_db(tmp_path: Path):
    db_path = tmp_path / "state.db"
    conn = open_connection(db_path)
    try:
        applied = apply_pending_migrations(conn)
    finally:
        conn.close()

    # Applied in ascending version order. The list grows whenever we add a
    # new forward migration; test asserts head landed, not a specific count.
    assert len(applied) >= 1
    assert applied[0][0] == 1  # 001_initial first
    versions = [v for v, _ in applied]
    assert versions == sorted(versions), "migrations must apply in ascending order"


# ---------------------------------------------------------------------------
# Pragmas — WAL + FKs
# ---------------------------------------------------------------------------

def test_open_connection_enables_wal(tmp_path: Path):
    db_path = tmp_path / "state.db"
    conn = open_connection(db_path)
    try:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    finally:
        conn.close()
    assert mode == "wal"


def test_open_connection_enables_foreign_keys(tmp_path: Path):
    db_path = tmp_path / "state.db"
    conn = open_connection(db_path)
    try:
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    finally:
        conn.close()
    assert fk == 1


# ---------------------------------------------------------------------------
# Schema presence — all expected tables from migration 001 exist
# ---------------------------------------------------------------------------

EXPECTED_TABLES = {
    # bookkeeping
    "schema_migrations",
    # raw evidence
    "source_daily_garmin",
    "running_session",
    "gym_session",
    "gym_set",
    "nutrition_intake_raw",
    "stress_manual_raw",
    "context_note",
    # accepted state
    "accepted_recovery_state_daily",
    "accepted_running_state_daily",
    "accepted_resistance_training_state_daily",
    "accepted_nutrition_state_daily",
    "goal",
    # recommendation + review
    "recommendation_log",
    "review_event",
    "review_outcome",
}


def test_migration_001_creates_every_expected_table(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    finally:
        conn.close()

    present = {r["name"] for r in rows}
    missing = EXPECTED_TABLES - present
    assert missing == set(), f"migration 001 failed to create: {sorted(missing)}"


# ---------------------------------------------------------------------------
# CLI smoke — `hai state init` / `hai state migrate`
# ---------------------------------------------------------------------------

def test_cli_state_init_creates_db_and_reports_applied(tmp_path: Path, capsys):
    db_path = tmp_path / "state.db"
    rc = cli_main(["state", "init", "--db-path", str(db_path)])
    assert rc == 0
    assert db_path.exists()

    out = capsys.readouterr().out
    import json
    payload = json.loads(out)
    assert payload["db_path"] == str(db_path)
    created = payload["created"]
    # 001 must be first; any later migrations follow in ascending order.
    assert created[0] == [1, "001_initial.sql"]
    versions = [v for v, _ in created]
    assert versions == sorted(versions)


def test_cli_state_migrate_on_head_db_reports_empty_applied(tmp_path: Path, capsys):
    db_path = tmp_path / "state.db"
    cli_main(["state", "init", "--db-path", str(db_path)])
    capsys.readouterr()  # discard init output

    rc = cli_main(["state", "migrate", "--db-path", str(db_path)])
    assert rc == 0

    import json
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version_before"] == 3
    assert payload["schema_version_after"] == 3
    assert payload["applied"] == []


def test_cli_state_migrate_fails_cleanly_when_db_missing(tmp_path: Path, capsys):
    db_path = tmp_path / "absent.db"
    rc = cli_main(["state", "migrate", "--db-path", str(db_path)])
    assert rc == 2
    err = capsys.readouterr().err
    assert "state DB not found" in err


# ---------------------------------------------------------------------------
# Regression — foreign-key constraint actually bites when expected
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Atomicity — a failing migration must roll back cleanly
# ---------------------------------------------------------------------------

def test_broken_migration_rolls_back_ddl_and_bookkeeping(tmp_path: Path):
    """A migration that fails partway must leave the DB in exactly the state
    it was in before the migration started: no leftover tables from earlier
    statements in the same file, no schema_migrations row, pre-existing
    schema intact, version unchanged.

    This is the contract `hai state migrate` commits to. Without it, a
    partially-applied migration bricks the DB for future migrate calls.
    """

    from health_agent_infra.state.store import apply_pending_migrations

    # 1. Init a fresh DB so migration 001 is at head.
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    # 2. Construct a migration whose first statement would succeed in
    #    isolation, but whose second statement is malformed. If rollback
    #    works, the first statement's table must NOT persist.
    broken_sql = """
        CREATE TABLE experiment_table (x INTEGER);
        CREATE TABLE bad_syntax TABLE column);
    """
    broken_migration = [(99, "099_broken.sql", broken_sql)]

    conn = open_connection(db_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            apply_pending_migrations(conn, migrations=broken_migration)

        # schema_migrations did not record version 99
        rows = conn.execute(
            "SELECT version FROM schema_migrations WHERE version = 99"
        ).fetchall()
        assert rows == []

        # The successful first statement was rolled back — no leftover table.
        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'experiment_table'"
        ).fetchall()
        assert rows == [], "first statement in broken migration was not rolled back"

        # Pre-existing migration 001 tables still present.
        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'source_daily_garmin'"
        ).fetchall()
        assert len(rows) == 1

        # Version is still at head (pre-broken migration), not 99.
        assert current_schema_version(conn) == 3
    finally:
        conn.close()


def test_good_migration_after_a_rolled_back_broken_one_still_applies(tmp_path: Path):
    """After a rollback, the DB is reusable — a subsequent well-formed
    migration applies cleanly. Proves the DB isn't left in a 'stuck' state."""

    from health_agent_infra.state.store import apply_pending_migrations

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    broken = [(99, "099_broken.sql", "CREATE TABLE a (x INTEGER); CREATE TABLE bad TABLE;")]
    good = [(99, "099_good.sql", "CREATE TABLE recovery_marker (x INTEGER);")]

    conn = open_connection(db_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            apply_pending_migrations(conn, migrations=broken)

        applied = apply_pending_migrations(conn, migrations=good)
        assert applied == [(99, "099_good.sql")]

        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name = 'recovery_marker'"
        ).fetchall()
        assert len(rows) == 1
        assert current_schema_version(conn) == 99
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# SQL splitter — correctness against string literals + line comments
# ---------------------------------------------------------------------------

def test_sql_splitter_respects_line_comments_and_string_literals():
    from health_agent_infra.state.store import _split_sql_statements

    sql = """
    -- a comment ; with a semicolon
    CREATE TABLE foo (
        name TEXT DEFAULT 'a;b;c',
        flag TEXT CHECK (flag IN ('on', 'off'))
    );
    CREATE INDEX idx_foo ON foo (name);
    """
    stmts = _split_sql_statements(sql)

    assert len(stmts) == 2
    assert stmts[0].startswith("CREATE TABLE foo")
    assert "'a;b;c'" in stmts[0]
    assert stmts[1].startswith("CREATE INDEX idx_foo")


def test_sql_splitter_handles_escaped_single_quote_in_string():
    from health_agent_infra.state.store import _split_sql_statements

    sql = "INSERT INTO t VALUES ('it''s'); CREATE TABLE u (x INTEGER);"
    stmts = _split_sql_statements(sql)

    assert len(stmts) == 2
    assert "'it''s'" in stmts[0]
    assert stmts[1].startswith("CREATE TABLE u")


def test_sql_splitter_ignores_empty_statements():
    from health_agent_infra.state.store import _split_sql_statements

    sql = ";;;CREATE TABLE foo (x INTEGER);;;"
    stmts = _split_sql_statements(sql)

    assert stmts == ["CREATE TABLE foo (x INTEGER)"]


def test_foreign_key_enforced_between_review_outcome_and_event(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO review_outcome "
                "(review_event_id, recommendation_id, user_id, recorded_at, "
                " followed_recommendation, source, ingest_actor, projected_at) "
                "VALUES ('rev_missing', 'rec_missing', 'u', "
                "        '2026-04-17T00:00:00Z', 1, 'claude_agent_v1', "
                "        'claude_agent_v1', '2026-04-17T00:00:00Z')"
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Migration 003 — synthesis scaffolding
# ---------------------------------------------------------------------------

def test_migration_003_creates_synthesis_tables(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        names = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert {"proposal_log", "daily_plan", "x_rule_firing"}.issubset(names)


def test_migration_003_adds_domain_column_with_recovery_default(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        for table in ("recommendation_log", "review_event", "review_outcome"):
            cols = {
                row["name"]: row
                for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
            }
            assert "domain" in cols, f"domain column missing on {table}"
            assert cols["domain"]["notnull"] == 1
            assert cols["domain"]["dflt_value"] == "'recovery'"
    finally:
        conn.close()


def test_migration_003_x_rule_firing_tier_check_constraint(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        # Seed a daily_plan row so the FK constraint is satisfied.
        conn.execute(
            "INSERT INTO daily_plan "
            "(daily_plan_id, user_id, for_date, synthesized_at, "
            " recommendation_ids_json, proposal_ids_json, x_rules_fired_json, "
            " source, ingest_actor, validated_at, projected_at) "
            "VALUES ('plan_1', 'u', '2026-04-17', '2026-04-17T00:00:00Z', "
            "        '[]', '[]', '[]', 'claude_agent_v1', 'claude_agent_v1', "
            "        '2026-04-17T00:00:00Z', '2026-04-17T00:00:00Z')"
        )
        # Valid tier passes.
        conn.execute(
            "INSERT INTO x_rule_firing "
            "(daily_plan_id, user_id, x_rule_id, tier, affected_domain, "
            " trigger_note, fired_at) "
            "VALUES ('plan_1', 'u', 'X1a', 'soften', 'running', 't', "
            "        '2026-04-17T00:00:00Z')"
        )
        # Invalid tier raises.
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO x_rule_firing "
                "(daily_plan_id, user_id, x_rule_id, tier, affected_domain, "
                " trigger_note, fired_at) "
                "VALUES ('plan_1', 'u', 'X1a', 'banana', 'running', 't', "
                "        '2026-04-17T00:00:00Z')"
            )
    finally:
        conn.close()
