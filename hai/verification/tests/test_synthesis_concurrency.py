"""M7 — synthesis concurrency invariants.

Two threads call ``run_synthesis`` for the same ``(for_date, user_id)``
against the same DB file. SQLite's ``BEGIN IMMEDIATE`` (the guard the
synthesis transaction uses) must make exactly one winner: the other
thread either rolls back or queues. Final state must be consistent —
exactly one canonical plan, referenced by exactly one set of
recommendations / firings.

The contract is "whoever gets to commit first wins cleanly; the loser
does not partial-write." Which of the two wins is not specified —
either ordering is valid.
"""

from __future__ import annotations

import queue
import sqlite3
import threading
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
)
from health_agent_infra.core.synthesis import run_synthesis
from health_agent_infra.core.writeback.proposal import PROPOSAL_SCHEMA_VERSIONS


FOR_DATE = date(2026, 4, 17)
USER = "u_conc"


def _proposal() -> dict[str, Any]:
    return {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS["recovery"],
        "proposal_id": f"prop_{FOR_DATE}_{USER}_recovery_01",
        "user_id": USER,
        "for_date": FOR_DATE.isoformat(),
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "rationale": ["x"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "n"}],
        "bounded": True,
    }


def _quiet_snapshot() -> dict[str, Any]:
    return {
        "recovery": {
            "classified_state": {"sleep_debt_band": "none"},
            "today": {"acwr_ratio": 1.0},
        },
        "running": {},
    }


def test_two_threads_synthesising_same_day_produce_consistent_final_state(
    tmp_path: Path,
):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        project_proposal(conn, _proposal())
    finally:
        conn.close()

    # Two threads, each opening its own connection + calling
    # run_synthesis. A barrier makes sure both get to the write
    # transaction at the same time, maximising the chance of a lock
    # collision.
    barrier = threading.Barrier(2)
    results: queue.Queue = queue.Queue()

    def _runner():
        barrier.wait()
        conn = open_connection(db_path)
        # Short busy timeout: we want the loser to either fail fast or
        # queue briefly — not wait minutes on a test.
        conn.execute("PRAGMA busy_timeout = 2000")
        try:
            run_synthesis(
                conn, for_date=FOR_DATE, user_id=USER,
                snapshot=_quiet_snapshot(),
            )
            results.put(("ok", None))
        except sqlite3.OperationalError as exc:
            results.put(("locked", str(exc)))
        except Exception as exc:  # noqa: BLE001 — surface any other failure
            results.put(("error", f"{type(exc).__name__}: {exc}"))
        finally:
            conn.close()

    t1 = threading.Thread(target=_runner)
    t2 = threading.Thread(target=_runner)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    outcomes = [results.get() for _ in range(2)]
    statuses = [o[0] for o in outcomes]

    # Acceptable: both succeed (one queued behind the other via the
    # busy_timeout), or one wins and the other reports "locked". What's
    # NOT acceptable is an 'error' (e.g. inconsistency exception).
    assert "error" not in statuses, f"unexpected error outcomes: {outcomes}"

    # Post-condition: regardless of ordering, the DB has exactly one
    # canonical plan row for this (for_date, user_id) and its
    # recommendations are consistent (non-empty, all point to the same
    # plan id).
    canonical_id = canonical_daily_plan_id(FOR_DATE, USER)
    conn = open_connection(db_path)
    try:
        plans = conn.execute(
            "SELECT daily_plan_id FROM daily_plan WHERE user_id = ? "
            "AND for_date = ?",
            (USER, FOR_DATE.isoformat()),
        ).fetchall()
        assert len(plans) == 1, (
            f"expected exactly one canonical plan after two concurrent "
            f"synthesis calls; found {[dict(p) for p in plans]}"
        )
        assert plans[0]["daily_plan_id"] == canonical_id

        rec_plans = conn.execute(
            "SELECT DISTINCT daily_plan_id FROM recommendation_log "
            "WHERE user_id = ? AND for_date = ? AND daily_plan_id IS NOT NULL",
            (USER, FOR_DATE.isoformat()),
        ).fetchall()
        assert len(rec_plans) == 1, (
            f"recommendations reference multiple plans: "
            f"{[dict(r) for r in rec_plans]}"
        )
        assert rec_plans[0]["daily_plan_id"] == canonical_id
    finally:
        conn.close()
