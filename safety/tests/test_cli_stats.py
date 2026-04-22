"""Tests for ``hai stats`` + the ``cmd_daily`` instrumentation hook.

``hai stats`` is a read-only local summary of sync_run_log (freshness
per source) and runtime_event_log (recent commands, daily streak). The
command never leaves the device; it reads the DB the user already owns.

The ``cmd_daily`` tests here check the *wrapping* behavior: every
invocation writes one runtime_event_log row regardless of outcome
(awaiting_proposals, complete, failed), so downstream streak + freshness
math is sound.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import (
    begin_sync,
    complete_sync,
    initialize_database,
    open_connection,
)


def _fresh_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


def _stats_argv(db_path: Path, *extra: str) -> list[str]:
    return ["stats", "--db-path", str(db_path), *extra]


# ---------------------------------------------------------------------------
# hai stats — fresh DB / missing DB
# ---------------------------------------------------------------------------


def test_stats_requires_existing_db(tmp_path, capsys):
    missing = tmp_path / "absent.db"
    rc = cli_main(["stats", "--db-path", str(missing)])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "hai init" in err


def test_stats_json_missing_db_reports_status(tmp_path, capsys):
    missing = tmp_path / "absent.db"
    rc = cli_main(["stats", "--db-path", str(missing), "--json"])
    assert rc == exit_codes.USER_INPUT
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "db_missing"
    assert "hai init" in payload["hint"]


def test_stats_fresh_db_renders_empty_sections(tmp_path, capsys):
    db_path = _fresh_db(tmp_path)
    rc = cli_main(_stats_argv(db_path))
    assert rc == 0
    out = capsys.readouterr().out
    # Text view names each section even when it's empty.
    assert "Sync freshness" in out
    assert "Recent runs" in out
    assert "Command summary" in out
    assert "Daily streak: 0" in out


def test_stats_fresh_db_json_shape(tmp_path, capsys):
    db_path = _fresh_db(tmp_path)
    rc = cli_main(_stats_argv(db_path, "--json"))
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)

    assert set(payload.keys()) >= {
        "db_path", "user_id", "sync_freshness",
        "recent_events", "command_summary", "daily_streak_days",
    }
    assert payload["sync_freshness"] == {}
    assert payload["recent_events"] == []
    assert payload["command_summary"] == {}
    assert payload["daily_streak_days"] == 0


# ---------------------------------------------------------------------------
# hai stats — with real sync + event data
# ---------------------------------------------------------------------------


def test_stats_reports_sync_freshness_per_source(tmp_path, capsys):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        # Two successful syncs against the same source: the most recent wins.
        s1 = begin_sync(conn, source="garmin_live", user_id="u_local_1",
                        mode="live", for_date=date(2026, 4, 20))
        complete_sync(conn, s1, rows_pulled=1, rows_accepted=1,
                      duplicates_skipped=0, status="ok")
        s2 = begin_sync(conn, source="garmin_live", user_id="u_local_1",
                        mode="live", for_date=date(2026, 4, 21))
        complete_sync(conn, s2, rows_pulled=1, rows_accepted=1,
                      duplicates_skipped=0, status="ok")
        # Different source.
        s3 = begin_sync(conn, source="garmin", user_id="u_local_1",
                        mode="csv", for_date=date(2026, 4, 21))
        complete_sync(conn, s3, rows_pulled=1, rows_accepted=1,
                      duplicates_skipped=0, status="ok")
    finally:
        conn.close()

    rc = cli_main(_stats_argv(db_path, "--json"))
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)

    fresh = payload["sync_freshness"]
    assert set(fresh.keys()) == {"garmin_live", "garmin"}
    assert fresh["garmin_live"]["for_date"] == "2026-04-21"
    assert fresh["garmin_live"]["mode"] == "live"
    assert fresh["garmin"]["mode"] == "csv"


def test_stats_reports_recent_events_after_daily_runs(tmp_path, capsys, monkeypatch):
    """A successful `hai daily` run writes a runtime_event_log row."""

    db_path = _fresh_db(tmp_path)

    # Run hai daily with --skip-pull --skip-reviews so no Garmin dep is needed.
    # There are no proposals, so the run exits with awaiting_proposals (rc=0),
    # still a successful invocation for our purposes.
    rc = cli_main([
        "daily",
        "--db-path", str(db_path),
        "--base-dir", str(tmp_path / "runtime"),
        "--skip-pull",
        "--skip-reviews",
    ])
    assert rc == 0
    capsys.readouterr()  # discard daily output

    rc = cli_main(_stats_argv(db_path, "--json"))
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)

    events = payload["recent_events"]
    assert len(events) == 1
    assert events[0]["command"] == "daily"
    assert events[0]["status"] == "ok"
    assert events[0]["exit_code"] == 0
    assert events[0]["duration_ms"] is not None
    # Command summary agrees.
    assert payload["command_summary"]["daily"]["ok"] == 1


def test_stats_limit_caps_recent_events(tmp_path, capsys):
    """--limit N trims the recent_events window."""

    db_path = _fresh_db(tmp_path)

    # Run hai daily five times.
    for _ in range(5):
        cli_main(["daily", "--db-path", str(db_path),
                  "--base-dir", str(tmp_path / "runtime"),
                  "--skip-pull", "--skip-reviews"])
        capsys.readouterr()

    rc = cli_main(_stats_argv(db_path, "--json", "--limit", "3"))
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["recent_events"]) == 3
    assert payload["command_summary"]["daily"]["total"] == 5


def test_stats_daily_streak_counts_consecutive_ok_days(tmp_path, capsys):
    """Streak is consecutive UTC calendar days with >=1 successful daily run."""

    db_path = _fresh_db(tmp_path)

    # Insert three runtime_event_log rows by hand, one per day for the
    # last 3 days (including today). Going via cli_main would collapse
    # them onto today's date.
    today = datetime.now(timezone.utc).date()
    conn = open_connection(db_path)
    try:
        for offset in (2, 1, 0):
            day = today - timedelta(days=offset)
            started = datetime.combine(day, datetime.min.time(),
                                       tzinfo=timezone.utc)
            conn.execute(
                "INSERT INTO runtime_event_log "
                "(command, user_id, started_at, completed_at, status, exit_code) "
                "VALUES ('daily', 'u_local_1', ?, ?, 'ok', 0)",
                (started.isoformat(), started.isoformat()),
            )
        conn.commit()
    finally:
        conn.close()

    rc = cli_main(_stats_argv(db_path, "--json"))
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["daily_streak_days"] == 3


def test_stats_daily_streak_breaks_on_gap(tmp_path, capsys):
    db_path = _fresh_db(tmp_path)

    today = datetime.now(timezone.utc).date()
    conn = open_connection(db_path)
    try:
        # today + day-2 (gap on day-1) → streak is 1, not 3.
        for offset in (2, 0):
            day = today - timedelta(days=offset)
            started = datetime.combine(day, datetime.min.time(),
                                       tzinfo=timezone.utc)
            conn.execute(
                "INSERT INTO runtime_event_log "
                "(command, user_id, started_at, completed_at, status, exit_code) "
                "VALUES ('daily', 'u_local_1', ?, ?, 'ok', 0)",
                (started.isoformat(), started.isoformat()),
            )
        conn.commit()
    finally:
        conn.close()

    rc = cli_main(_stats_argv(db_path, "--json"))
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["daily_streak_days"] == 1


def test_stats_daily_streak_zero_when_today_missing(tmp_path, capsys):
    db_path = _fresh_db(tmp_path)

    today = datetime.now(timezone.utc).date()
    conn = open_connection(db_path)
    try:
        # Ran yesterday and day-before, but not today. Streak is 0.
        for offset in (2, 1):
            day = today - timedelta(days=offset)
            started = datetime.combine(day, datetime.min.time(),
                                       tzinfo=timezone.utc)
            conn.execute(
                "INSERT INTO runtime_event_log "
                "(command, user_id, started_at, completed_at, status, exit_code) "
                "VALUES ('daily', 'u_local_1', ?, ?, 'ok', 0)",
                (started.isoformat(), started.isoformat()),
            )
        conn.commit()
    finally:
        conn.close()

    rc = cli_main(_stats_argv(db_path, "--json"))
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["daily_streak_days"] == 0


# ---------------------------------------------------------------------------
# cmd_daily instrumentation — wrapper must write one row per invocation
# ---------------------------------------------------------------------------


def test_daily_wrapper_records_awaiting_proposals_as_ok(tmp_path, capsys):
    db_path = _fresh_db(tmp_path)

    rc = cli_main(["daily", "--db-path", str(db_path),
                   "--base-dir", str(tmp_path / "runtime"),
                   "--skip-pull", "--skip-reviews"])
    assert rc == 0
    capsys.readouterr()

    conn = open_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM runtime_event_log ORDER BY event_id"
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 1
    assert rows[0]["command"] == "daily"
    assert rows[0]["status"] == "ok"
    assert rows[0]["exit_code"] == 0


def test_daily_wrapper_records_failure_when_db_missing(tmp_path, capsys):
    """Pre-init: `hai daily` bails with USER_INPUT. The wrapper no-ops
    silently because the DB doesn't exist — no row to write."""

    missing = tmp_path / "never.db"
    rc = cli_main(["daily", "--db-path", str(missing),
                   "--base-dir", str(tmp_path / "runtime")])
    assert rc == exit_codes.USER_INPUT
    # Silently skipped logging — no DB was created as a side-effect.
    assert not missing.exists()
