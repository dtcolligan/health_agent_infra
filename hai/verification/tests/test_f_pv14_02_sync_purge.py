"""F-PV14-02 — `hai sync purge` surgical-cleanup CLI (v0.1.17 §2.G).

Acceptance per PLAN.md §2.G:

  1. Unit test: 3 fixture rows match → purge → exactly the 3 rows are
     gone + 1 runtime_event_log row written with command='sync purge'
     + context_json containing the deleted-row payloads.
  2. Refusal test: 6 rows match → CLI exits USER_INPUT, 0 rows deleted,
     0 runtime_event_log rows.
  3. --dry-run test: lists rows on stdout, 0 deleted, 0 runtime_event_log.
  4. Capabilities manifest entry: mutation='writes-state',
     agent_safe=False, idempotent='no', json_output=True.
"""

from __future__ import annotations

import io
import json
import sqlite3
from contextlib import closing, redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import initialize_database, open_connection


USER = "u_pv14"
SOURCE = "garmin_live"
FOR_DATE = "2026-02-10"


def _run(*argv: str) -> tuple[int, str, str]:
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    try:
        with redirect_stdout(out_buf), redirect_stderr(err_buf):
            rc = cli_main(list(argv))
    except SystemExit as exc:
        rc = int(exc.code) if isinstance(exc.code, int) else 2
    return rc, out_buf.getvalue(), err_buf.getvalue()


def _seed_sync_rows(db_path: Path, count: int) -> list[int]:
    """Seed N rows into sync_run_log and return their sync_ids."""

    ids: list[int] = []
    with closing(open_connection(db_path)) as conn:
        for i in range(count):
            cur = conn.execute(
                "INSERT INTO sync_run_log "
                "(source, user_id, mode, started_at, completed_at, "
                " status, rows_pulled, rows_accepted, duplicates_skipped, "
                " for_date) "
                "VALUES (?, ?, 'live', ?, ?, 'ok', 1, 1, 0, ?)",
                (
                    SOURCE, USER,
                    f"2026-02-10T0{i}:00:00Z",
                    f"2026-02-10T0{i}:00:01Z",
                    FOR_DATE,
                ),
            )
            ids.append(cur.lastrowid)
        conn.commit()
    return ids


def _row_count(db_path: Path, table: str) -> int:
    with closing(open_connection(db_path)) as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


# ---------------------------------------------------------------------------
# Acceptance test 1 — 3 fixture rows purged + audit logged
# ---------------------------------------------------------------------------


def test_purge_three_matched_rows_writes_audit(tmp_path):
    """3 fixture rows in sync_run_log match the selectors → purge
    deletes exactly those 3 rows and writes 1 runtime_event_log row."""

    db = tmp_path / "state.db"
    initialize_database(db)
    seeded_ids = _seed_sync_rows(db, count=3)
    assert _row_count(db, "sync_run_log") == 3

    rc, out, err = _run(
        "sync", "purge",
        "--source", SOURCE,
        "--for-date", FOR_DATE,
        "--db-path", str(db),
    )
    assert rc == exit_codes.OK, f"sync purge failed: rc={rc}, stderr={err[:200]}"

    payload = json.loads(out)
    assert payload["matched_count"] == 3
    assert payload["deleted_count"] == 3
    assert payload["dry_run"] is False
    assert payload["runtime_event_id"] is not None
    assert {r["sync_id"] for r in payload["matched_rows"]} == set(seeded_ids)

    # Exactly the 3 rows are gone.
    assert _row_count(db, "sync_run_log") == 0

    # Runtime audit row exists with the deleted payloads.
    with closing(open_connection(db)) as conn:
        audits = conn.execute(
            "SELECT command, status, exit_code, context_json "
            "FROM runtime_event_log WHERE command = 'sync purge'"
        ).fetchall()
    assert len(audits) == 1, f"expected 1 audit row, got {len(audits)}"
    audit = audits[0]
    assert audit["command"] == "sync purge"
    assert audit["status"] == "ok"
    assert audit["exit_code"] == 0
    ctx = json.loads(audit["context_json"])
    assert ctx["selectors"]["source"] == SOURCE
    assert ctx["selectors"]["for_date"] == FOR_DATE
    assert len(ctx["deleted_rows"]) == 3
    assert {r["sync_id"] for r in ctx["deleted_rows"]} == set(seeded_ids)


# ---------------------------------------------------------------------------
# Acceptance test 2 — refusal when selectors match >5 rows
# ---------------------------------------------------------------------------


def test_purge_refuses_when_selectors_match_more_than_five_rows(tmp_path):
    """6 rows match → CLI exits USER_INPUT, 0 rows deleted, 0 audits."""

    db = tmp_path / "state.db"
    initialize_database(db)
    _seed_sync_rows(db, count=6)
    assert _row_count(db, "sync_run_log") == 6

    rc, out, err = _run(
        "sync", "purge",
        "--source", SOURCE,
        "--for-date", FOR_DATE,
        "--db-path", str(db),
    )
    assert rc == exit_codes.USER_INPUT, (
        f"sync purge should refuse on >5-row selector; rc={rc}, stderr={err[:200]}"
    )
    assert "refusing to purge" in err or "matches 6" in err, (
        f"refusal stderr should explain the cap: {err[:200]}"
    )

    # No rows deleted; no runtime_event_log audit row.
    assert _row_count(db, "sync_run_log") == 6
    assert _row_count(db, "runtime_event_log") == 0


# ---------------------------------------------------------------------------
# Acceptance test 3 — --dry-run is read-only
# ---------------------------------------------------------------------------


def test_purge_dry_run_lists_rows_without_deleting(tmp_path):
    """--dry-run lists the matching rows on stdout and writes 0 changes."""

    db = tmp_path / "state.db"
    initialize_database(db)
    seeded_ids = _seed_sync_rows(db, count=3)

    rc, out, err = _run(
        "sync", "purge",
        "--source", SOURCE,
        "--for-date", FOR_DATE,
        "--db-path", str(db),
        "--dry-run",
    )
    assert rc == exit_codes.OK, f"dry-run failed: rc={rc}, stderr={err[:200]}"

    payload = json.loads(out)
    assert payload["matched_count"] == 3
    assert payload["deleted_count"] == 0
    assert payload["dry_run"] is True
    assert payload["runtime_event_id"] is None
    assert {r["sync_id"] for r in payload["matched_rows"]} == set(seeded_ids)

    # No state mutation.
    assert _row_count(db, "sync_run_log") == 3
    assert _row_count(db, "runtime_event_log") == 0


# ---------------------------------------------------------------------------
# Acceptance test 4 — capabilities manifest annotation
# ---------------------------------------------------------------------------


def test_capabilities_manifest_registers_sync_purge_with_correct_annotations():
    """`hai capabilities --json` registers `hai sync purge` with
    mutation='writes-state', agent_safe=False, idempotent='no'."""

    rc, out, err = _run("capabilities", "--json")
    assert rc == exit_codes.OK
    manifest = json.loads(out)
    purge = next(
        (c for c in manifest["commands"] if c["command"] == "hai sync purge"),
        None,
    )
    assert purge is not None, "hai sync purge missing from capabilities manifest"
    assert purge["mutation"] == "writes-state", purge
    assert purge["agent_safe"] is False, purge
    assert purge["idempotent"] == "no", purge
    assert purge["json_output"] in ("default", "json_only"), purge


# ---------------------------------------------------------------------------
# Edge case — narrowing via --started-after still respects the cap
# ---------------------------------------------------------------------------


def test_purge_started_after_narrows_selection(tmp_path):
    """--started-after pre-cap-time leaves only N rows under the cap;
    --started-after far in the future matches 0 → still OK (0-row purge
    is a no-op, not a refusal)."""

    db = tmp_path / "state.db"
    initialize_database(db)
    _seed_sync_rows(db, count=4)
    # All 4 seeded rows have started_at like 2026-02-10T0X:00:00Z.

    # Narrow further: started_after the last row → 0 matches.
    rc, out, err = _run(
        "sync", "purge",
        "--source", SOURCE,
        "--for-date", FOR_DATE,
        "--started-after", "2027-01-01T00:00:00Z",
        "--db-path", str(db),
    )
    assert rc == exit_codes.OK, f"0-row purge should succeed: stderr={err[:200]}"
    payload = json.loads(out)
    assert payload["matched_count"] == 0
    assert payload["deleted_count"] == 0

    # Original 4 rows are intact; no audit row written.
    assert _row_count(db, "sync_run_log") == 4
    assert _row_count(db, "runtime_event_log") == 0


# ---------------------------------------------------------------------------
# Edge case — missing DB exits USER_INPUT cleanly
# ---------------------------------------------------------------------------


def test_purge_missing_db_returns_user_input(tmp_path):
    """No state.db → USER_INPUT exit with actionable hint."""

    missing = tmp_path / "no_such_db.db"
    rc, out, err = _run(
        "sync", "purge",
        "--source", SOURCE,
        "--db-path", str(missing),
    )
    assert rc == exit_codes.USER_INPUT, f"rc={rc}, stderr={err[:200]}"
    assert "state DB not found" in err or "hai state init" in err
