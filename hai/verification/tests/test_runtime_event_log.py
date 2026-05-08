"""Tests for ``runtime_event_log`` (migration 012) + primitives + context manager.

Exercises the row lifecycle directly against a fresh DB, plus the
graceful-degradation paths (DB missing, pre-migration schema) so callers
that adopt the context manager don't have to add defensive checks of
their own.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    begin_event,
    command_summary,
    complete_event,
    fail_event,
    initialize_database,
    open_connection,
    recent_events,
    runtime_event,
)


def _fresh_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


def test_begin_event_inserts_pessimistic_failed_row(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        event_id = begin_event(conn, command="daily", user_id="u_local_1")
        assert event_id >= 1

        row = conn.execute(
            "SELECT * FROM runtime_event_log WHERE event_id = ?", (event_id,),
        ).fetchone()
        # Pessimistic default: status='failed', completed_at unset.
        assert row["command"] == "daily"
        assert row["user_id"] == "u_local_1"
        assert row["status"] == "failed"
        assert row["completed_at"] is None
        assert row["exit_code"] is None
    finally:
        conn.close()


def test_complete_event_stamps_ok_status_and_counts(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        event_id = begin_event(conn, command="daily", user_id="u")
        complete_event(
            conn, event_id,
            status="ok", exit_code=0, duration_ms=1234,
            context={"overall_status": "complete"},
        )
        row = conn.execute(
            "SELECT * FROM runtime_event_log WHERE event_id = ?", (event_id,),
        ).fetchone()
        assert row["status"] == "ok"
        assert row["exit_code"] == 0
        assert row["duration_ms"] == 1234
        assert row["completed_at"] is not None
        assert json.loads(row["context_json"]) == {"overall_status": "complete"}
    finally:
        conn.close()


def test_complete_event_rejects_invalid_status(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        event_id = begin_event(conn, command="daily")
        with pytest.raises(ValueError, match="status must be"):
            complete_event(conn, event_id, status="weird")  # type: ignore[arg-type]
    finally:
        conn.close()


def test_fail_event_records_exception_metadata(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        event_id = begin_event(conn, command="daily", user_id="u")
        fail_event(
            conn, event_id,
            error_class="RuntimeError",
            error_message="kaboom",
            exit_code=1,
            duration_ms=42,
        )
        row = conn.execute(
            "SELECT * FROM runtime_event_log WHERE event_id = ?", (event_id,),
        ).fetchone()
        assert row["status"] == "failed"
        assert row["error_class"] == "RuntimeError"
        assert row["error_message"] == "kaboom"
        assert row["exit_code"] == 1
        assert row["duration_ms"] == 42
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


def test_runtime_event_happy_path_writes_ok_row(tmp_path):
    db_path = _fresh_db(tmp_path)

    with runtime_event(db_path, command="daily", user_id="u") as evt:
        evt["exit_code"] = 0
        evt["context"] = {"overall_status": "complete"}

    conn = open_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM runtime_event_log ORDER BY event_id"
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 1
    row = rows[0]
    assert row["command"] == "daily"
    assert row["status"] == "ok"
    assert row["exit_code"] == 0
    assert row["duration_ms"] is not None
    assert json.loads(row["context_json"]) == {"overall_status": "complete"}


def test_runtime_event_nonzero_exit_code_marks_failed(tmp_path):
    db_path = _fresh_db(tmp_path)

    with runtime_event(db_path, command="daily", user_id="u") as evt:
        evt["exit_code"] = 2  # USER_INPUT

    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM runtime_event_log ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    assert row["status"] == "failed"
    assert row["exit_code"] == 2
    # Non-zero exit != exception, so error_class stays NULL.
    assert row["error_class"] is None


def test_runtime_event_exception_records_and_reraises(tmp_path):
    db_path = _fresh_db(tmp_path)

    with pytest.raises(RuntimeError, match="boom"):
        with runtime_event(db_path, command="daily", user_id="u"):
            raise RuntimeError("boom")

    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM runtime_event_log ORDER BY event_id DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    assert row["status"] == "failed"
    assert row["error_class"] == "RuntimeError"
    assert row["error_message"] == "boom"


def test_runtime_event_on_missing_db_is_noop(tmp_path):
    """No DB at path → yield dict but never attempt to insert."""

    missing = tmp_path / "does-not-exist.db"
    with runtime_event(missing, command="daily", user_id="u") as evt:
        evt["exit_code"] = 0

    # No file materialised as a side-effect.
    assert not missing.exists()


def test_runtime_event_on_none_db_is_noop(tmp_path):
    with runtime_event(None, command="daily", user_id="u") as evt:
        evt["exit_code"] = 0
    # Nothing to assert beyond "didn't raise."


def test_runtime_event_on_pre_migration_db_is_noop(tmp_path):
    """A DB present but missing migration 012 still runs the body."""

    db_path = tmp_path / "old.db"
    conn = sqlite3.connect(db_path)
    # Create a minimal schema_migrations table but DON'T apply migration 012.
    conn.execute(
        "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, filename TEXT)"
    )
    conn.commit()
    conn.close()

    with runtime_event(db_path, command="daily", user_id="u") as evt:
        evt["exit_code"] = 0

    # runtime_event_log was never created; the body ran to completion anyway.
    conn = sqlite3.connect(db_path)
    try:
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        conn.close()
    assert "runtime_event_log" not in tables


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------


def test_recent_events_returns_newest_first(tmp_path):
    db_path = _fresh_db(tmp_path)

    for i in range(5):
        with runtime_event(db_path, command="daily", user_id="u") as evt:
            evt["exit_code"] = 0

    conn = open_connection(db_path)
    try:
        events = recent_events(conn, command="daily", limit=3)
    finally:
        conn.close()

    assert len(events) == 3
    # Descending by started_at — the most-recently-inserted event is first.
    started_ats = [e["started_at"] for e in events]
    assert started_ats == sorted(started_ats, reverse=True)


def test_recent_events_filters_by_command(tmp_path):
    db_path = _fresh_db(tmp_path)

    with runtime_event(db_path, command="daily") as e:
        e["exit_code"] = 0
    with runtime_event(db_path, command="init") as e:
        e["exit_code"] = 0
    with runtime_event(db_path, command="daily") as e:
        e["exit_code"] = 0

    conn = open_connection(db_path)
    try:
        only_daily = recent_events(conn, command="daily", limit=10)
        all_events = recent_events(conn, limit=10)
    finally:
        conn.close()

    assert len(only_daily) == 2
    assert all(e["command"] == "daily" for e in only_daily)
    assert len(all_events) == 3


def test_command_summary_counts_ok_vs_failed(tmp_path):
    db_path = _fresh_db(tmp_path)

    # Two daily ok, one daily failed (via exception), one init ok.
    with runtime_event(db_path, command="daily") as e:
        e["exit_code"] = 0
    with runtime_event(db_path, command="daily") as e:
        e["exit_code"] = 0
    with pytest.raises(RuntimeError):
        with runtime_event(db_path, command="daily"):
            raise RuntimeError("x")
    with runtime_event(db_path, command="init") as e:
        e["exit_code"] = 0

    conn = open_connection(db_path)
    try:
        summary = command_summary(conn)
    finally:
        conn.close()

    assert summary["daily"] == {"ok": 2, "failed": 1, "total": 3}
    assert summary["init"] == {"ok": 1, "failed": 0, "total": 1}


def test_recent_events_empty_on_fresh_db(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        assert recent_events(conn) == []
        assert command_summary(conn) == {}
    finally:
        conn.close()
