"""Phase 1 of the agent-operable runtime plan — the planned_recommendation
ledger is written by run_synthesis inside its atomic transaction.

Contracts pinned:

  1. Every proposal gets exactly one paired planned_recommendation row,
     scoped to the canonical daily_plan_id.
  2. The planned row carries the ORIGINAL (pre-X-rule) action and
     confidence from the source proposal — not the post-mutation values.
  3. When an X-rule fires (e.g. X1a softens a hard proposal under
     moderate sleep debt), adapted ≠ planned on the affected domain, and
     the delta corresponds to the x_rule_firing row.
  4. When no X-rule fires on a domain, planned == adapted for that
     domain's action/confidence.
  5. Re-running synthesis (canonical-plan replacement) cleanly removes
     the prior planned rows and writes a fresh set — no duplicates.
  6. The FK chain is walkable: planned.proposal_id → proposal_log,
     planned.daily_plan_id → daily_plan.

The invariant ``planned ⊕ firings = adapted`` is exercised via the
X1a softening path where the firing's mutation_json records exactly
the action transition we see between planned and adapted.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
)
from health_agent_infra.core.synthesis import run_synthesis
from health_agent_infra.core.writeback.proposal import PROPOSAL_SCHEMA_VERSIONS


FOR_DATE = date(2026, 4, 22)
USER = "u_plan"


def _make_proposal(
    domain: str, action: str, index: int, *, confidence: str = "high",
) -> dict:
    return {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS[domain],
        "proposal_id": f"prop_{FOR_DATE}_{USER}_{domain}_{index:02d}",
        "user_id": USER,
        "for_date": FOR_DATE.isoformat(),
        "domain": domain,
        "action": action,
        "action_detail": None,
        "rationale": [f"{domain}_baseline"],
        "confidence": confidence,
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "r1", "decision": "allow", "note": "n"},
        ],
        "bounded": True,
    }


def _snapshot_no_firings() -> dict:
    """A snapshot that triggers no X-rules — every domain looks clean."""
    return {
        "recovery": {
            "classified_state": {"sleep_debt_band": "low"},
            "today": {"acwr_ratio": 1.0},
        },
        "sleep": {"classified_state": {"sleep_debt_band": "low"}},
        "stress": {
            "classified_state": {"garmin_stress_band": "low"},
            "today_body_battery": 75,
        },
        "running": {},
    }


def _snapshot_x1a_fires() -> dict:
    """Moderate sleep debt → X1a softens every hard proposal."""
    return {
        "recovery": {
            "classified_state": {"sleep_debt_band": "moderate"},
            "today": {"acwr_ratio": 1.0},
        },
        "sleep": {"classified_state": {"sleep_debt_band": "moderate"}},
        "stress": {
            "classified_state": {"garmin_stress_band": "low"},
            "today_body_battery": 75,
        },
        "running": {},
    }


# ---------------------------------------------------------------------------
# Contract 1 + 5: one planned row per proposal; re-synthesize replaces cleanly
# ---------------------------------------------------------------------------


def test_one_planned_row_per_proposal(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    proposals = [
        _make_proposal("recovery", "proceed_with_planned_session", 1),
        _make_proposal("running", "proceed_with_planned_run", 2),
    ]
    conn = open_connection(db_path)
    try:
        for p in proposals:
            project_proposal(conn, p)
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_snapshot_no_firings(),
        )
        rows = conn.execute(
            "SELECT domain, proposal_id, daily_plan_id "
            "FROM planned_recommendation ORDER BY domain"
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 2
    domains = {r["domain"] for r in rows}
    assert domains == {"recovery", "running"}
    # Every row's proposal_id matches one of the input proposals.
    planned_prop_ids = {r["proposal_id"] for r in rows}
    assert planned_prop_ids == {p["proposal_id"] for p in proposals}


def test_resynthesize_replaces_planned_rows_cleanly(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    proposals = [
        _make_proposal("recovery", "proceed_with_planned_session", 1),
    ]
    conn = open_connection(db_path)
    try:
        for p in proposals:
            project_proposal(conn, p)
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_snapshot_no_firings(),
        )
        # Second run — canonical replacement.
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_snapshot_no_firings(),
        )
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM planned_recommendation"
        ).fetchone()["n"]
    finally:
        conn.close()

    assert count == 1, (
        f"re-synthesize must leave exactly one planned row per domain; "
        f"found {count}"
    )


# ---------------------------------------------------------------------------
# Contract 2 + 4: planned carries the ORIGINAL action, not the mutated one
# ---------------------------------------------------------------------------


def test_planned_equals_proposal_when_no_xrule_fires(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    proposal = _make_proposal("recovery", "proceed_with_planned_session", 1)
    conn = open_connection(db_path)
    try:
        project_proposal(conn, proposal)
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_snapshot_no_firings(),
        )
        planned = conn.execute(
            "SELECT action, confidence FROM planned_recommendation "
            "WHERE domain = 'recovery'"
        ).fetchone()
        adapted = conn.execute(
            "SELECT action, confidence FROM recommendation_log "
            "WHERE domain = 'recovery'"
        ).fetchone()
    finally:
        conn.close()

    assert planned["action"] == "proceed_with_planned_session"
    assert adapted["action"] == "proceed_with_planned_session"
    assert planned["action"] == adapted["action"]
    assert planned["confidence"] == adapted["confidence"]


# ---------------------------------------------------------------------------
# Contract 3: planned ⊕ firings = adapted under X1a
# ---------------------------------------------------------------------------


def test_planned_preserves_hard_action_when_x1a_softens_adapted(tmp_path: Path):
    """X1a (moderate sleep debt) softens a hard proposal. The planned row
    must keep the ORIGINAL hard action; the adapted row carries the
    softened one; the firing's mutation_json records the transition."""

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    proposal = _make_proposal("recovery", "proceed_with_planned_session", 1)
    conn = open_connection(db_path)
    try:
        project_proposal(conn, proposal)
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_snapshot_x1a_fires(),
        )
        planned = conn.execute(
            "SELECT action FROM planned_recommendation "
            "WHERE domain = 'recovery'"
        ).fetchone()
        adapted = conn.execute(
            "SELECT action FROM recommendation_log "
            "WHERE domain = 'recovery'"
        ).fetchone()
        firing = conn.execute(
            "SELECT x_rule_id, tier, mutation_json FROM x_rule_firing "
            "WHERE affected_domain = 'recovery'"
        ).fetchone()
    finally:
        conn.close()

    # Planned kept the ORIGINAL hard action from the proposal.
    assert planned["action"] == "proceed_with_planned_session"
    # Adapted was softened by X1a.
    assert adapted["action"] != "proceed_with_planned_session"
    # Firing records X1a on recovery with a soften tier and a recommended
    # mutation whose `action` matches the adapted (post-mutation) action.
    # The "from" side is what the planned row preserves — the original
    # proposal's action.
    assert firing["x_rule_id"] == "X1a"
    assert firing["tier"] == "soften"
    mutation = json.loads(firing["mutation_json"])
    assert mutation["action"] == adapted["action"], (
        "firing.mutation_json.action should equal the post-mutation "
        "recommendation action — this is the 'to' side of the transition"
    )


# ---------------------------------------------------------------------------
# Contract 6: FK chain is walkable
# ---------------------------------------------------------------------------


def test_planned_fks_resolve_to_existing_parents(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    proposal = _make_proposal("recovery", "proceed_with_planned_session", 1)
    conn = open_connection(db_path)
    try:
        project_proposal(conn, proposal)
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_snapshot_no_firings(),
        )
        # Walk the FK chain: planned → proposal_log → daily_plan.
        row = conn.execute(
            """
            SELECT pl.planned_id, pr.proposal_id, dp.daily_plan_id
              FROM planned_recommendation pl
              JOIN proposal_log        pr ON pr.proposal_id  = pl.proposal_id
              JOIN daily_plan          dp ON dp.daily_plan_id = pl.daily_plan_id
             WHERE pl.domain = 'recovery'
            """
        ).fetchone()
    finally:
        conn.close()

    assert row is not None, "FK join failed — planned row is orphaned"
    assert row["proposal_id"] == proposal["proposal_id"]


# ---------------------------------------------------------------------------
# Atomicity: planned rows and adapted rows land in the same transaction
# ---------------------------------------------------------------------------


def test_planned_and_adapted_counts_match_after_synthesis(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    proposals = [
        _make_proposal("recovery", "proceed_with_planned_session", 1),
        _make_proposal("running", "proceed_with_planned_run", 2),
        _make_proposal("sleep", "maintain_schedule", 3),
    ]
    conn = open_connection(db_path)
    try:
        for p in proposals:
            project_proposal(conn, p)
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_snapshot_no_firings(),
        )
        planned = conn.execute(
            "SELECT COUNT(*) AS n FROM planned_recommendation"
        ).fetchone()["n"]
        adapted = conn.execute(
            "SELECT COUNT(*) AS n FROM recommendation_log"
        ).fetchone()["n"]
    finally:
        conn.close()

    assert planned == len(proposals)
    assert adapted == len(proposals)
    assert planned == adapted
