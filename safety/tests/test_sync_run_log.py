"""Tests for the ``sync_run_log`` write API + freshness reader.

Covers:
  - ``begin_sync`` / ``complete_sync`` / ``fail_sync`` round trip.
  - The ``sync_run`` context manager stitches begin+complete on
    success and begin+fail on exception.
  - ``latest_successful_sync_per_source`` returns the right row per
    source (newest wins; non-ok rows ignored).
  - The ``idx_sync_run_log_source_user_date`` index is actually used
    by the freshness lookup (``EXPLAIN QUERY PLAN``).

Tests open the DB directly via ``initialize_database`` + a local seed
so they don't depend on the CLI sync-wrapping plumbing.
"""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    begin_sync,
    complete_sync,
    fail_sync,
    initialize_database,
    latest_successful_sync_per_source,
    open_connection,
    sync_run,
)


USER = "u_sync_test"


def _fresh_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


# ---------------------------------------------------------------------------
# Primitives: begin → complete / fail
# ---------------------------------------------------------------------------


def test_begin_then_complete_round_trip(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        sync_id = begin_sync(
            conn,
            source="garmin",
            user_id=USER,
            mode="csv",
            for_date=date(2026, 4, 17),
        )
        # Row is created immediately with status='failed' as pessimistic
        # default — a crash before complete_sync leaves a truthful trail.
        row_pre = conn.execute(
            "SELECT * FROM sync_run_log WHERE sync_id = ?", (sync_id,),
        ).fetchone()
        assert row_pre["status"] == "failed"
        assert row_pre["completed_at"] is None

        complete_sync(
            conn, sync_id,
            rows_pulled=1,
            rows_accepted=1,
            duplicates_skipped=0,
        )
        row = conn.execute(
            "SELECT * FROM sync_run_log WHERE sync_id = ?", (sync_id,),
        ).fetchone()
        assert row["source"] == "garmin"
        assert row["user_id"] == USER
        assert row["mode"] == "csv"
        assert row["status"] == "ok"
        assert row["completed_at"] is not None
        assert row["rows_pulled"] == 1
        assert row["rows_accepted"] == 1
        assert row["duplicates_skipped"] == 0
        assert row["for_date"] == "2026-04-17"
        assert row["error_class"] is None
    finally:
        conn.close()


def test_begin_then_fail_round_trip(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        sync_id = begin_sync(
            conn, source="garmin_live", user_id=USER, mode="live",
            for_date=date(2026, 4, 17),
        )
        fail_sync(
            conn, sync_id,
            error_class="GarminLiveError",
            error_message="upstream 503",
        )
        row = conn.execute(
            "SELECT * FROM sync_run_log WHERE sync_id = ?", (sync_id,),
        ).fetchone()
        assert row["status"] == "failed"
        assert row["error_class"] == "GarminLiveError"
        assert row["error_message"] == "upstream 503"
        assert row["completed_at"] is not None
        assert row["rows_pulled"] is None
    finally:
        conn.close()


def test_complete_sync_rejects_invalid_status(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        sync_id = begin_sync(conn, source="x", user_id=USER, mode="csv")
        with pytest.raises(ValueError):
            complete_sync(
                conn, sync_id,
                rows_pulled=0, rows_accepted=0, duplicates_skipped=0,
                status="bogus",
            )
    finally:
        conn.close()


def test_partial_status_round_trip(tmp_path):
    """'partial' is a valid terminal status — reserved for partial-day
    fetches (M6's retry-surface work)."""

    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        sync_id = begin_sync(conn, source="garmin_live", user_id=USER, mode="live")
        complete_sync(
            conn, sync_id,
            rows_pulled=3, rows_accepted=2, duplicates_skipped=0,
            status="partial",
        )
        row = conn.execute(
            "SELECT status FROM sync_run_log WHERE sync_id = ?", (sync_id,),
        ).fetchone()
        assert row["status"] == "partial"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


def test_sync_run_context_manager_completes_on_clean_exit(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        with sync_run(
            conn, source="nutrition_manual", user_id=USER,
            mode="manual", for_date=date(2026, 4, 17),
        ) as run:
            run["rows_pulled"] = 1
            run["rows_accepted"] = 1
            run["duplicates_skipped"] = 0

        rows = conn.execute(
            "SELECT * FROM sync_run_log WHERE source = ?",
            ("nutrition_manual",),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["status"] == "ok"
        assert rows[0]["rows_accepted"] == 1
    finally:
        conn.close()


def test_sync_run_context_manager_fails_on_exception(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        with pytest.raises(RuntimeError, match="boom"):
            with sync_run(
                conn, source="garmin_live", user_id=USER, mode="live",
            ):
                raise RuntimeError("boom")

        row = conn.execute(
            "SELECT * FROM sync_run_log WHERE source = ?", ("garmin_live",),
        ).fetchone()
        assert row["status"] == "failed"
        assert row["error_class"] == "RuntimeError"
        assert row["error_message"] == "boom"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Freshness reader
# ---------------------------------------------------------------------------


def test_latest_successful_sync_returns_newest_ok_per_source(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        # Three successful syncs for garmin, at different times. The
        # reader should return the newest. started_at is the ordering key.
        conn.execute(
            "INSERT INTO sync_run_log "
            "(source, user_id, mode, started_at, completed_at, status, "
            " rows_pulled, rows_accepted, duplicates_skipped) "
            "VALUES "
            "('garmin', ?, 'csv', '2026-04-15T10:00:00+00:00', '2026-04-15T10:00:05+00:00', 'ok', 1, 1, 0),"
            "('garmin', ?, 'csv', '2026-04-16T10:00:00+00:00', '2026-04-16T10:00:05+00:00', 'ok', 1, 1, 0),"
            "('garmin', ?, 'csv', '2026-04-17T10:00:00+00:00', '2026-04-17T10:00:05+00:00', 'ok', 1, 1, 0),"
            # An intervening failed run — must not surface.
            "('garmin', ?, 'csv', '2026-04-17T12:00:00+00:00', '2026-04-17T12:00:02+00:00', 'failed', NULL, NULL, NULL),"
            # A different user's row — filtered by user_id.
            "('garmin', 'other_user', 'csv', '2026-04-18T10:00:00+00:00', '2026-04-18T10:00:05+00:00', 'ok', 1, 1, 0),"
            # A second source for the same user.
            "('nutrition_manual', ?, 'manual', '2026-04-17T18:00:00+00:00', '2026-04-17T18:00:01+00:00', 'ok', 1, 1, 0)",
            (USER, USER, USER, USER, USER),
        )
        conn.commit()

        latest = latest_successful_sync_per_source(conn, user_id=USER)
        assert set(latest.keys()) == {"garmin", "nutrition_manual"}
        assert latest["garmin"]["completed_at"] == "2026-04-17T10:00:05+00:00"
        assert latest["nutrition_manual"]["completed_at"] == "2026-04-17T18:00:01+00:00"
    finally:
        conn.close()


def test_latest_successful_sync_empty_on_fresh_db(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        assert latest_successful_sync_per_source(conn, user_id=USER) == {}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Index usage — EXPLAIN QUERY PLAN asserts the index carries the load
# ---------------------------------------------------------------------------


def test_freshness_lookup_uses_source_user_date_index(tmp_path):
    """The (source, user_id, started_at DESC) index must cover the
    natural "most recent ok sync per (source, user)" query. Assert via
    EXPLAIN QUERY PLAN so a future change to the query shape (or an
    accidental DROP INDEX in a migration) surfaces here, not in a
    hai-doctor slowdown production discovers."""

    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        plan = conn.execute(
            "EXPLAIN QUERY PLAN "
            "SELECT * FROM sync_run_log "
            "WHERE source = ? AND user_id = ? AND status = 'ok' "
            "ORDER BY started_at DESC LIMIT 1",
            ("garmin", USER),
        ).fetchall()
        plan_text = "\n".join(row["detail"] for row in plan)
        assert "idx_sync_run_log_source_user_date" in plan_text, (
            f"freshness lookup should use idx_sync_run_log_source_user_date; "
            f"got plan:\n{plan_text}"
        )
    finally:
        conn.close()
