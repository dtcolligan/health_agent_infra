"""End-to-end tests for ``hai synthesize`` (Phase 2 step 4).

Covers the invariants called out in plan §4 deliverable 3:

1. **Atomicity** — a mid-synthesis failure rolls back every write. No
   orphan ``daily_plan`` with missing recommendations, no orphan
   ``x_rule_firing`` referencing a non-committed plan.
2. **Canonical idempotency** — re-running on the same
   ``(for_date, user_id)`` atomically replaces the prior plan (old
   firings + recommendations deleted; new ones inserted; counts stay
   coherent).
3. **Supersession** — ``--supersede`` keeps both plans addressable;
   prior plan's ``synthesis_meta_json`` carries a ``superseded_by``
   pointer to the new one; new plan has a fresh ``_v<N>`` id.
4. **X-rule end-to-end** — at least one Phase A rule firing is
   exercised end-to-end (snapshot → firing → mutation on draft →
   persisted x_rule_firing row with matching mutation_json).
"""

from __future__ import annotations

import json
import sqlite3
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.core import exit_codes
from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
)
from health_agent_infra.core.synthesis import (
    SynthesisError,
    run_synthesis,
)
from health_agent_infra.core.synthesis_policy import (
    XRuleFiring,
    XRuleWriteSurfaceViolation,
)
from health_agent_infra.core.writeback.proposal import (
    PROPOSAL_SCHEMA_VERSIONS,
)


# ---------------------------------------------------------------------------
# Fixtures — synthetic snapshot + proposals, single-running-domain v1
# ---------------------------------------------------------------------------

def _fresh_db(tmp_path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


def _running_proposal(**overrides):
    base = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS["running"],
        "proposal_id": "prop_2026-04-17_u_local_1_running_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-17",
        "domain": "running",
        "action": "proceed_with_planned_run",
        "action_detail": None,
        "rationale": ["weekly_mileage_trend=moderate"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


def _quiet_snapshot():
    """A snapshot that fires no X-rules — baseline for atomicity tests."""
    return {
        "recovery": {
            "classified_state": {"sleep_debt_band": "none"},
            "today": {
                "acwr_ratio": 1.0,
                "body_battery_end_of_day": 75,
                "all_day_stress": 25,
            },
        },
        "running": {},
    }


def _x1a_triggering_snapshot():
    """sleep_debt=moderate → X1a fires, softens running to easy aerobic."""
    return {
        "recovery": {
            "classified_state": {"sleep_debt_band": "moderate"},
            "today": {
                "acwr_ratio": 1.0,
                "body_battery_end_of_day": 75,
                "all_day_stress": 25,
            },
        },
        "running": {},
    }


def _insert_proposal(db_path: Path, proposal: dict):
    conn = open_connection(db_path)
    try:
        project_proposal(conn, proposal)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Happy path — synthesis commits a daily_plan + recommendation + links proposal
# ---------------------------------------------------------------------------

def test_synthesize_writes_daily_plan_and_recommendation_and_links_proposal(tmp_path):
    db_path = _fresh_db(tmp_path)
    proposal = _running_proposal()
    _insert_proposal(db_path, proposal)

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_quiet_snapshot(),
        )
    finally:
        conn.close()

    assert result.daily_plan_id == canonical_daily_plan_id(date(2026, 4, 17), "u_local_1")
    assert result.recommendation_ids == ["rec_2026-04-17_u_local_1_running_01"]
    assert result.proposal_ids == [proposal["proposal_id"]]
    assert result.phase_a_firings == []
    assert result.phase_b_firings == []
    assert result.superseded_prior is None

    # Verify rows actually landed in the DB.
    conn = open_connection(db_path)
    try:
        plan_row = conn.execute(
            "SELECT * FROM daily_plan WHERE daily_plan_id = ?",
            (result.daily_plan_id,),
        ).fetchone()
        assert plan_row is not None
        assert plan_row["user_id"] == "u_local_1"
        assert plan_row["for_date"] == "2026-04-17"
        assert json.loads(plan_row["recommendation_ids_json"]) == result.recommendation_ids
        assert json.loads(plan_row["x_rules_fired_json"]) == []

        rec_row = conn.execute(
            "SELECT * FROM recommendation_log WHERE recommendation_id = ?",
            (result.recommendation_ids[0],),
        ).fetchone()
        assert rec_row is not None
        assert rec_row["domain"] == "running"
        assert rec_row["action"] == "proceed_with_planned_run"
        payload = json.loads(rec_row["payload_json"])
        assert payload["daily_plan_id"] == result.daily_plan_id
        assert payload["follow_up"]["review_event_id"].startswith("rev_")

        # Proposal now linked to plan.
        prop_row = conn.execute(
            "SELECT daily_plan_id FROM proposal_log WHERE proposal_id = ?",
            (proposal["proposal_id"],),
        ).fetchone()
        assert prop_row["daily_plan_id"] == result.daily_plan_id
    finally:
        conn.close()


def test_synthesize_refuses_when_no_proposals(tmp_path):
    db_path = _fresh_db(tmp_path)
    conn = open_connection(db_path)
    try:
        with pytest.raises(SynthesisError):
            run_synthesis(
                conn,
                for_date=date(2026, 4, 17),
                user_id="u_local_1",
                snapshot=_quiet_snapshot(),
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# X-rule end-to-end — X1a softens running proposal; firing persisted
# ---------------------------------------------------------------------------

def test_synthesize_x1a_firing_mutates_draft_and_persists_firing_row(tmp_path):
    db_path = _fresh_db(tmp_path)
    proposal = _running_proposal()
    _insert_proposal(db_path, proposal)

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_x1a_triggering_snapshot(),
        )

        assert [f.rule_id for f in result.phase_a_firings] == ["X1a"]

        rec_row = conn.execute(
            "SELECT action, payload_json FROM recommendation_log "
            "WHERE recommendation_id = ?",
            (result.recommendation_ids[0],),
        ).fetchone()
        # Phase A mutated the draft action from proceed → easy_aerobic.
        assert rec_row["action"] == "downgrade_to_easy_aerobic"
        payload = json.loads(rec_row["payload_json"])
        assert payload["action_detail"]["reason_token"] == "x1a_sleep_debt_trigger"

        firing_row = conn.execute(
            "SELECT x_rule_id, tier, affected_domain, mutation_json "
            "FROM x_rule_firing WHERE daily_plan_id = ?",
            (result.daily_plan_id,),
        ).fetchone()
        assert firing_row["x_rule_id"] == "X1a"
        assert firing_row["tier"] == "soften"
        assert firing_row["affected_domain"] == "running"
        mutation = json.loads(firing_row["mutation_json"])
        assert mutation["action"] == "downgrade_to_easy_aerobic"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Idempotency — canonical rerun replaces atomically
# ---------------------------------------------------------------------------

def test_synthesize_rerun_on_same_key_replaces_prior_plan(tmp_path):
    db_path = _fresh_db(tmp_path)
    proposal = _running_proposal()
    _insert_proposal(db_path, proposal)

    conn = open_connection(db_path)
    try:
        # First run: quiet snapshot → no firings.
        run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_quiet_snapshot(),
        )
        first_firing_count = conn.execute(
            "SELECT COUNT(*) AS c FROM x_rule_firing"
        ).fetchone()["c"]
        assert first_firing_count == 0

        # Second run: X1a snapshot → 1 firing.
        run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_x1a_triggering_snapshot(),
        )

        plan_count = conn.execute(
            "SELECT COUNT(*) AS c FROM daily_plan "
            "WHERE for_date = ? AND user_id = ?",
            ("2026-04-17", "u_local_1"),
        ).fetchone()["c"]
        # Replacement, not duplication.
        assert plan_count == 1

        rec_count = conn.execute(
            "SELECT COUNT(*) AS c FROM recommendation_log "
            "WHERE for_date = ? AND user_id = ?",
            ("2026-04-17", "u_local_1"),
        ).fetchone()["c"]
        assert rec_count == 1

        firing_count = conn.execute(
            "SELECT COUNT(*) AS c FROM x_rule_firing"
        ).fetchone()["c"]
        # Prior plan's 0 firings replaced by the X1a firing.
        assert firing_count == 1
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Supersession — --supersede keeps both plans addressable
# ---------------------------------------------------------------------------

def test_synthesize_supersede_preserves_prior_plan_and_flips_pointer(tmp_path):
    db_path = _fresh_db(tmp_path)
    proposal = _running_proposal()
    _insert_proposal(db_path, proposal)

    canonical = canonical_daily_plan_id(date(2026, 4, 17), "u_local_1")

    conn = open_connection(db_path)
    try:
        first = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_quiet_snapshot(),
        )
        assert first.daily_plan_id == canonical

        second = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_x1a_triggering_snapshot(),
            supersede=True,
        )
        assert second.daily_plan_id == f"{canonical}_v2"
        assert second.superseded_prior == canonical

        # Both plan rows exist.
        plan_rows = conn.execute(
            "SELECT daily_plan_id, synthesis_meta_json FROM daily_plan "
            "WHERE for_date = ? AND user_id = ? "
            "ORDER BY daily_plan_id",
            ("2026-04-17", "u_local_1"),
        ).fetchall()
        assert [r["daily_plan_id"] for r in plan_rows] == [
            canonical, f"{canonical}_v2",
        ]

        # Prior plan's synthesis_meta_json now has superseded_by pointer.
        prior_meta = json.loads(plan_rows[0]["synthesis_meta_json"])
        assert prior_meta["superseded_by"] == f"{canonical}_v2"

        # Each plan's own recommendations exist separately.
        rec_count = conn.execute(
            "SELECT COUNT(*) AS c FROM recommendation_log "
            "WHERE for_date = ? AND user_id = ?",
            ("2026-04-17", "u_local_1"),
        ).fetchone()["c"]
        assert rec_count == 2
    finally:
        conn.close()


def test_synthesize_third_supersede_picks_v3(tmp_path):
    db_path = _fresh_db(tmp_path)
    proposal = _running_proposal()
    _insert_proposal(db_path, proposal)

    canonical = canonical_daily_plan_id(date(2026, 4, 17), "u_local_1")

    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=date(2026, 4, 17), user_id="u_local_1",
            snapshot=_quiet_snapshot(),
        )
        run_synthesis(
            conn, for_date=date(2026, 4, 17), user_id="u_local_1",
            snapshot=_x1a_triggering_snapshot(), supersede=True,
        )
        third = run_synthesis(
            conn, for_date=date(2026, 4, 17), user_id="u_local_1",
            snapshot=_quiet_snapshot(), supersede=True,
        )
        assert third.daily_plan_id == f"{canonical}_v3"
    finally:
        conn.close()


def test_synthesize_supersede_targets_canonical_leaf_not_chain_head(tmp_path):
    """D1 test #5: after v1 → v2, a third ``--supersede`` points v3's
    back-pointer at v2 (the leaf at time of synthesis), not at the
    canonical chain head.

    The pre-fix bug overwrote ``v1.superseded_by_plan_id`` on every
    supersede call, breaking the forward chain so ``hai explain --plan-version all``
    skipped intermediate revisions. Regression test for that path.
    """

    db_path = _fresh_db(tmp_path)
    proposal = _running_proposal()
    _insert_proposal(db_path, proposal)

    canonical = canonical_daily_plan_id(date(2026, 4, 17), "u_local_1")
    v2_id = f"{canonical}_v2"
    v3_id = f"{canonical}_v3"

    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=date(2026, 4, 17), user_id="u_local_1",
            snapshot=_quiet_snapshot(),
        )
        second = run_synthesis(
            conn, for_date=date(2026, 4, 17), user_id="u_local_1",
            snapshot=_x1a_triggering_snapshot(), supersede=True,
        )
        assert second.daily_plan_id == v2_id
        assert second.superseded_prior == canonical

        third = run_synthesis(
            conn, for_date=date(2026, 4, 17), user_id="u_local_1",
            snapshot=_quiet_snapshot(), supersede=True,
        )
        assert third.daily_plan_id == v3_id
        # Back-pointer must be v2 (the leaf at time-of-synth), not v1.
        assert third.superseded_prior == v2_id

        # Forward chain intact: v1 → v2 → v3 → NULL.
        rows = conn.execute(
            "SELECT daily_plan_id, superseded_by_plan_id "
            "FROM daily_plan WHERE for_date = ? AND user_id = ? "
            "ORDER BY daily_plan_id",
            ("2026-04-17", "u_local_1"),
        ).fetchall()
        chain = {r["daily_plan_id"]: r["superseded_by_plan_id"] for r in rows}
        assert chain == {canonical: v2_id, v2_id: v3_id, v3_id: None}
    finally:
        conn.close()


def test_synthesize_supersede_does_not_relink_prior_plan_proposals(tmp_path):
    """D1 test #7 root-cause: ``--supersede`` leaves
    ``proposal_log.daily_plan_id`` pointed at whichever plan first
    consumed each proposal.

    Pre-fix, supersede re-linked proposals forward to the new plan,
    which meant explain reads via the FK silently lost the superseded
    plan's inputs. After the fix, the proposal row keeps its original
    linkage; the new plan's join to its proposals lives in
    ``daily_plan.proposal_ids_json``.
    """

    db_path = _fresh_db(tmp_path)
    proposal = _running_proposal()
    _insert_proposal(db_path, proposal)

    canonical = canonical_daily_plan_id(date(2026, 4, 17), "u_local_1")

    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=date(2026, 4, 17), user_id="u_local_1",
            snapshot=_quiet_snapshot(),
        )
        # After v1, the proposal is linked to v1.
        prop_row = conn.execute(
            "SELECT daily_plan_id FROM proposal_log WHERE proposal_id = ?",
            (proposal["proposal_id"],),
        ).fetchone()
        assert prop_row["daily_plan_id"] == canonical

        # Supersede → v2. Proposal row must keep pointing at v1.
        run_synthesis(
            conn, for_date=date(2026, 4, 17), user_id="u_local_1",
            snapshot=_x1a_triggering_snapshot(), supersede=True,
        )
        prop_row = conn.execute(
            "SELECT daily_plan_id FROM proposal_log WHERE proposal_id = ?",
            (proposal["proposal_id"],),
        ).fetchone()
        assert prop_row["daily_plan_id"] == canonical, (
            "supersede incorrectly relinked proposal_log.daily_plan_id "
            "forward to the new leaf, orphaning the prior plan's proposals"
        )

        # Both plans store the proposal id in proposal_ids_json — that's
        # the join key explain uses.
        plan_rows = conn.execute(
            "SELECT daily_plan_id, proposal_ids_json FROM daily_plan "
            "WHERE for_date = ? AND user_id = ? "
            "ORDER BY daily_plan_id",
            ("2026-04-17", "u_local_1"),
        ).fetchall()
        stored_ids = {
            r["daily_plan_id"]: json.loads(r["proposal_ids_json"])
            for r in plan_rows
        }
        assert proposal["proposal_id"] in stored_ids[canonical]
        assert proposal["proposal_id"] in stored_ids[f"{canonical}_v2"]
    finally:
        conn.close()


def test_explain_resolves_superseded_plan_proposals_via_json_array(tmp_path):
    """D1 test #7: ``hai explain <plan_v1>`` still shows the proposals
    that fed v1, even after ``--supersede`` creates v2.

    Asserts the explain bundle for the superseded plan resolves its
    proposals — the whole point of switching from the FK-based load
    path to the ``proposal_ids_json`` array stored on the plan row.
    """

    from health_agent_infra.core.explain import load_bundle_by_daily_plan_id

    db_path = _fresh_db(tmp_path)
    proposal = _running_proposal()
    _insert_proposal(db_path, proposal)

    canonical = canonical_daily_plan_id(date(2026, 4, 17), "u_local_1")
    v2_id = f"{canonical}_v2"

    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=date(2026, 4, 17), user_id="u_local_1",
            snapshot=_quiet_snapshot(),
        )
        run_synthesis(
            conn, for_date=date(2026, 4, 17), user_id="u_local_1",
            snapshot=_x1a_triggering_snapshot(), supersede=True,
        )

        v1_bundle = load_bundle_by_daily_plan_id(
            conn, daily_plan_id=canonical,
        )
        v2_bundle = load_bundle_by_daily_plan_id(conn, daily_plan_id=v2_id)

        v1_ids = {p.proposal_id for p in v1_bundle.proposals}
        v2_ids = {p.proposal_id for p in v2_bundle.proposals}
        assert proposal["proposal_id"] in v1_ids, (
            "superseded plan's proposals went missing from explain"
        )
        assert proposal["proposal_id"] in v2_ids
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Atomicity — mid-synthesis failure leaves DB unchanged
# ---------------------------------------------------------------------------

def test_synthesize_atomicity_rolls_back_on_mid_write_failure(tmp_path, monkeypatch):
    """Simulate a failure mid-synthesis and verify nothing persists.

    We monkeypatch ``project_bounded_recommendation`` to raise after the
    daily_plan row was inserted and several x_rule_firing rows were
    inserted — the rollback must evict all of them.
    """

    db_path = _fresh_db(tmp_path)
    proposal = _running_proposal()
    _insert_proposal(db_path, proposal)

    from health_agent_infra.core import synthesis as synth_module

    real_fn = synth_module.project_bounded_recommendation

    def _fail(*args, **kwargs):
        raise sqlite3.OperationalError("simulated mid-write failure")

    monkeypatch.setattr(synth_module, "project_bounded_recommendation", _fail)

    conn = open_connection(db_path)
    try:
        with pytest.raises(sqlite3.OperationalError):
            run_synthesis(
                conn,
                for_date=date(2026, 4, 17),
                user_id="u_local_1",
                snapshot=_x1a_triggering_snapshot(),
            )

        plan_count = conn.execute(
            "SELECT COUNT(*) AS c FROM daily_plan"
        ).fetchone()["c"]
        assert plan_count == 0, "daily_plan row leaked past rollback"

        firing_count = conn.execute(
            "SELECT COUNT(*) AS c FROM x_rule_firing"
        ).fetchone()["c"]
        assert firing_count == 0, "x_rule_firing row leaked past rollback"

        rec_count = conn.execute(
            "SELECT COUNT(*) AS c FROM recommendation_log"
        ).fetchone()["c"]
        assert rec_count == 0, "recommendation_log row leaked past rollback"

        prop_row = conn.execute(
            "SELECT daily_plan_id FROM proposal_log WHERE proposal_id = ?",
            (proposal["proposal_id"],),
        ).fetchone()
        assert prop_row["daily_plan_id"] is None, (
            "proposal_log.daily_plan_id leaked past rollback"
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Skill overlay — rationale + uncertainty + review_question flow through
# ---------------------------------------------------------------------------

def test_synthesize_applies_skill_drafts_overlay(tmp_path):
    db_path = _fresh_db(tmp_path)
    proposal = _running_proposal()
    _insert_proposal(db_path, proposal)

    skill_drafts = [
        {
            "recommendation_id": "rec_2026-04-17_u_local_1_running_01",
            "rationale": ["composed_by_skill", "x1a_sleep_debt_moderate"],
            "uncertainty": ["sleep_capped_confidence"],
            "follow_up": {"review_question": "Did the easy run help?"},
        },
    ]

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_x1a_triggering_snapshot(),
            skill_drafts=skill_drafts,
        )

        rec_row = conn.execute(
            "SELECT payload_json FROM recommendation_log "
            "WHERE recommendation_id = ?",
            (result.recommendation_ids[0],),
        ).fetchone()
        payload = json.loads(rec_row["payload_json"])
        assert payload["rationale"] == [
            "composed_by_skill", "x1a_sleep_debt_moderate",
        ]
        assert payload["uncertainty"] == ["sleep_capped_confidence"]
        assert payload["follow_up"]["review_question"] == "Did the easy run help?"
    finally:
        conn.close()


def test_synthesize_ignores_skill_attempt_to_change_action(tmp_path):
    """Skill cannot override Phase A outcomes. Action is runtime-owned."""

    db_path = _fresh_db(tmp_path)
    proposal = _running_proposal()
    _insert_proposal(db_path, proposal)

    skill_drafts = [
        {
            "recommendation_id": "rec_2026-04-17_u_local_1_running_01",
            # Skill tries to UN-soften the action. Runtime must ignore.
            "action": "proceed_with_planned_run",
            "action_detail": {"skill_injected": True},
            "confidence": "high",
            "rationale": ["skill_overlay"],
        },
    ]

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_x1a_triggering_snapshot(),
            skill_drafts=skill_drafts,
        )
        rec_row = conn.execute(
            "SELECT action, payload_json FROM recommendation_log "
            "WHERE recommendation_id = ?",
            (result.recommendation_ids[0],),
        ).fetchone()
        # Phase A's mutation stands; skill override silently ignored.
        assert rec_row["action"] == "downgrade_to_easy_aerobic"
        payload = json.loads(rec_row["payload_json"])
        assert "skill_injected" not in (payload.get("action_detail") or {})
        # But rationale overlay did land.
        assert payload["rationale"] == ["skill_overlay"]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Phase 3 step 5 — 4-domain end-to-end synthesis
# ---------------------------------------------------------------------------

def _recovery_proposal(**overrides):
    base = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS["recovery"],
        "proposal_id": "prop_2026-04-17_u_local_1_recovery_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-17",
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "rationale": ["readiness=recovered"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


def _sleep_proposal(**overrides):
    base = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS["sleep"],
        "proposal_id": "prop_2026-04-17_u_local_1_sleep_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-17",
        "domain": "sleep",
        "action": "maintain_schedule",
        "action_detail": None,
        "rationale": ["sleep_status=optimal"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


def _stress_proposal(**overrides):
    base = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS["stress"],
        "proposal_id": "prop_2026-04-17_u_local_1_stress_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-17",
        "domain": "stress",
        "action": "maintain_routine",
        "action_detail": None,
        "rationale": ["stress_state=calm"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


def _four_domain_snapshot_calm():
    """Snapshot where no X-rule fires — all 4 proposals pass through."""

    return {
        "recovery": {
            "classified_state": {"sleep_debt_band": "none"},
            "today": {"acwr_ratio": 1.0},
        },
        "sleep": {
            "classified_state": {"sleep_debt_band": "none"},
            "today": {"sleep_hours": 8.0},
        },
        "stress": {
            "classified_state": {"garmin_stress_band": "low"},
            "today": {
                "garmin_all_day_stress": 25,
                "body_battery_end_of_day": 75,
            },
            "today_garmin": 25,
            "today_body_battery": 75,
        },
        "running": {},
    }


def _four_domain_snapshot_stressful():
    """Snapshot where X1a (sleep moderate) + X7 (stress high) fire.

    Drives the plan's "X1 and X6 fire correctly" acceptance by showing
    that X1 reads from the sleep block (not recovery) and X7 reads from
    stress.classified_state.garmin_stress_band.
    """

    return {
        "recovery": {
            # Deliberate contradiction with sleep block to prove which
            # one X1 reads from.
            "classified_state": {"sleep_debt_band": "none"},
            "today": {"acwr_ratio": 1.0},
        },
        "sleep": {
            "classified_state": {"sleep_debt_band": "moderate"},
            "today": {"sleep_hours": 6.5},
        },
        "stress": {
            "classified_state": {"garmin_stress_band": "high"},
            "today": {
                "garmin_all_day_stress": 65,
                "body_battery_end_of_day": 45,
            },
            "today_garmin": 65,
            "today_body_battery": 45,
        },
        "running": {},
    }


def test_synthesize_four_domain_scenario_commits_four_recommendations(tmp_path):
    """Plan §4 Phase 3 deliverable 5: end-to-end agent run emits 4
    proposals and 4 final recommendations linked by daily_plan_id."""

    db_path = _fresh_db(tmp_path)
    for proposal in [
        _recovery_proposal(),
        _running_proposal(),
        _sleep_proposal(),
        _stress_proposal(),
    ]:
        _insert_proposal(db_path, proposal)

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_four_domain_snapshot_calm(),
        )

        assert len(result.recommendation_ids) == 4
        assert len(result.proposal_ids) == 4

        rows = conn.execute(
            "SELECT domain, payload_json FROM recommendation_log "
            "WHERE json_extract(payload_json, '$.daily_plan_id') = ? "
            "ORDER BY domain",
            (result.daily_plan_id,),
        ).fetchall()
        domains = [r["domain"] for r in rows]
        assert sorted(domains) == ["recovery", "running", "sleep", "stress"]

        # Every recommendation carries the same daily_plan_id.
        for row in rows:
            payload = json.loads(row["payload_json"])
            assert payload["daily_plan_id"] == result.daily_plan_id
    finally:
        conn.close()


def test_synthesize_four_domain_x1a_reads_sleep_block_in_e2e_flow(tmp_path):
    """End-to-end confirmation that X1a fires from sleep.classified_state,
    not recovery's echo, during real synthesis. The snapshot sets
    recovery's band to 'none' and sleep's band to 'moderate'; X1a must
    fire (sleep is the source of truth) and soften the running proposal."""

    db_path = _fresh_db(tmp_path)
    for proposal in [
        _recovery_proposal(),
        _running_proposal(),
        _sleep_proposal(),
        _stress_proposal(),
    ]:
        _insert_proposal(db_path, proposal)

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_four_domain_snapshot_stressful(),
        )
        fired_ids = sorted({f.rule_id for f in result.phase_a_firings})
        # X1a (sleep=moderate) softens both recovery and running hard
        # proposals; X7 (stress=high) caps confidence on all four.
        assert "X1a" in fired_ids
        assert "X7" in fired_ids

        # Running was softened by X1a.
        running_row = conn.execute(
            "SELECT action FROM recommendation_log "
            "WHERE domain = 'running' "
            "  AND json_extract(payload_json, '$.daily_plan_id') = ?",
            (result.daily_plan_id,),
        ).fetchone()
        assert running_row["action"] == "downgrade_to_easy_aerobic"

        # Every domain's recommendation had confidence capped by X7.
        all_rows = conn.execute(
            "SELECT domain, confidence FROM recommendation_log "
            "WHERE json_extract(payload_json, '$.daily_plan_id') = ?",
            (result.daily_plan_id,),
        ).fetchall()
        for row in all_rows:
            assert row["confidence"] == "moderate"
    finally:
        conn.close()


def test_synthesize_four_domain_x7_caps_sleep_and_stress_proposals(tmp_path):
    """X7 fires one firing per proposal's domain — including sleep and
    stress themselves. Persisted firings cover all four domains."""

    db_path = _fresh_db(tmp_path)
    for proposal in [
        _recovery_proposal(),
        _running_proposal(),
        _sleep_proposal(),
        _stress_proposal(),
    ]:
        _insert_proposal(db_path, proposal)

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_four_domain_snapshot_stressful(),
        )

        x7_rows = conn.execute(
            "SELECT affected_domain FROM x_rule_firing "
            "WHERE daily_plan_id = ? AND x_rule_id = 'X7'",
            (result.daily_plan_id,),
        ).fetchall()
        domains = sorted(r["affected_domain"] for r in x7_rows)
        assert domains == ["recovery", "running", "sleep", "stress"]
    finally:
        conn.close()


def test_synthesize_firings_are_not_flagged_orphan_when_domains_match(tmp_path):
    """Phase 2.5 Condition 1: the orphan column defaults to 0 for every
    firing whose affected_domain matches a committing proposal. Current
    rules can't emit orphans by construction — this test pins that."""

    db_path = _fresh_db(tmp_path)
    for proposal in [
        _recovery_proposal(),
        _running_proposal(),
        _sleep_proposal(),
        _stress_proposal(),
    ]:
        _insert_proposal(db_path, proposal)

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_four_domain_snapshot_stressful(),
        )

        rows = conn.execute(
            "SELECT orphan FROM x_rule_firing WHERE daily_plan_id = ?",
            (result.daily_plan_id,),
        ).fetchall()
        assert rows  # at least one firing committed
        assert all(r["orphan"] == 0 for r in rows)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Phase 2.5 Condition 2 — cap + adjust stacking (Phase A X7 + Phase B X9)
# ---------------------------------------------------------------------------
# The synthesis runtime supports a cap-then-adjust cycle end-to-end:
# Phase A X7 caps confidence on every proposal (including a synthetic
# nutrition proposal); Phase B X9 then adjusts the nutrition
# recommendation's action_detail upward because the training plan is
# still hard. Prior to this test, `guard_phase_b_mutation` was exercised
# at the unit level but the full A→B cycle had no integration coverage
# because nutrition is not submittable via the validated proposal path
# yet (that lands in Phase 5).
#
# This test inserts a synthetic nutrition proposal directly via
# `project_proposal` (which does no schema validation) — the plan's
# test-only shim per the Phase 2.5 Condition 2 follow-up. Once Phase 5
# lands a full nutrition submission path, this test can be rewritten to
# drive the shared CLI instead of the direct projector call.


def _synthetic_nutrition_proposal(**overrides):
    base = {
        # nutrition is NOT in SUPPORTED_DOMAINS yet; this is deliberate —
        # the shim bypasses validation so the A→B cycle has coverage
        # before Phase 5 wires up the full submission path.
        "schema_version": "nutrition_proposal.v1",
        "proposal_id": "prop_2026-04-17_u_local_1_nutrition_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-17",
        "domain": "nutrition",
        "action": "maintain_targets",
        "action_detail": {"protein_target_g": 140},
        "rationale": ["nutrition=on_track"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


def _x7_only_snapshot():
    """Stress=high fires X7 (caps confidence); no sleep/ACWR/body-battery
    trigger so recovery's training stays hard and X9 can fire Phase B."""

    return {
        "recovery": {
            "classified_state": {"sleep_debt_band": "none"},
            "today": {"acwr_ratio": 1.0},
            # X9 precondition (v0.1.4 #7): user has explicitly planned a session.
            "evidence": {"planned_session_type": "hard"},
        },
        "sleep": {"classified_state": {"sleep_debt_band": "none"}, "today": {}},
        "stress": {
            "classified_state": {"garmin_stress_band": "high"},
            "today": {
                "garmin_all_day_stress": 65,
                "body_battery_end_of_day": 75,
            },
            "today_garmin": 65,
            "today_body_battery": 75,
        },
        "running": {},
    }


def test_synthesize_cap_plus_adjust_stacking_nutrition_shim(tmp_path):
    """Phase A X7 caps confidence → Phase B X9 adjusts nutrition
    action_detail. Full cycle coverage for the Phase 2.5 Condition 2
    follow-up."""

    db_path = _fresh_db(tmp_path)
    # Real recovery proposal (validated, hard action) + synthetic
    # nutrition proposal (shim, bypasses validation).
    _insert_proposal(db_path, _recovery_proposal())
    _insert_proposal(db_path, _synthetic_nutrition_proposal())

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_x7_only_snapshot(),
        )

        phase_a_ids = sorted({f.rule_id for f in result.phase_a_firings})
        phase_b_ids = sorted({f.rule_id for f in result.phase_b_firings})
        assert "X7" in phase_a_ids
        assert phase_b_ids == ["X9"]

        # Recovery's confidence capped to moderate by Phase A X7.
        recovery_row = conn.execute(
            "SELECT confidence FROM recommendation_log "
            "WHERE domain = 'recovery' "
            "  AND json_extract(payload_json, '$.daily_plan_id') = ?",
            (result.daily_plan_id,),
        ).fetchone()
        assert recovery_row["confidence"] == "moderate"

        # Nutrition's action_detail adjusted by Phase B X9.
        nutrition_row = conn.execute(
            "SELECT action, payload_json FROM recommendation_log "
            "WHERE domain = 'nutrition' "
            "  AND json_extract(payload_json, '$.daily_plan_id') = ?",
            (result.daily_plan_id,),
        ).fetchone()
        assert nutrition_row is not None
        # Phase B only touches action_detail — action stays put.
        assert nutrition_row["action"] == "maintain_targets"
        payload = json.loads(nutrition_row["payload_json"])
        detail = payload["action_detail"]
        # Original key preserved; X9's adjustment merged in.
        assert detail["protein_target_g"] == 140
        assert detail["protein_target_multiplier"] == 1.1
        assert detail["reason_token"] == "x9_training_intensity_bump"

        # Both Phase A and Phase B firings persisted, linked to the plan.
        firing_rows = conn.execute(
            "SELECT x_rule_id, tier FROM x_rule_firing "
            "WHERE daily_plan_id = ? ORDER BY x_rule_id, tier",
            (result.daily_plan_id,),
        ).fetchall()
        fired_ids = [r["x_rule_id"] for r in firing_rows]
        assert "X7" in fired_ids
        assert "X9" in fired_ids
    finally:
        conn.close()


def test_synthesize_stamps_orphan_when_firing_domain_not_in_proposals(tmp_path):
    """Defensive orphan flag: a firing whose affected_domain is NOT
    among the committing proposal set is stamped ``orphan=1``. We
    exercise the code path by injecting a synthetic firing via a
    monkeypatch; current rules can't produce the case by construction,
    which is exactly why we want the defensive monitor."""

    db_path = _fresh_db(tmp_path)
    _insert_proposal(db_path, _recovery_proposal())  # only one proposal

    import health_agent_infra.core.synthesis as synthesis_mod
    from health_agent_infra.core.synthesis_policy import XRuleFiring

    # Force Phase A to emit a firing against "strength" — a domain NOT
    # in the committing proposals. The orphan column must capture this.
    def _fake_phase_a(snapshot, proposals, thresholds):
        return [
            XRuleFiring(
                rule_id="X_FAKE",
                tier="cap_confidence",
                affected_domain="strength",
                trigger_note="synthetic orphan for defensive-monitor test",
                recommended_mutation=None,
                source_signals={},
                phase="A",
            ),
        ]

    original = synthesis_mod.evaluate_phase_a
    synthesis_mod.evaluate_phase_a = _fake_phase_a
    try:
        conn = open_connection(db_path)
        try:
            result = run_synthesis(
                conn,
                for_date=date(2026, 4, 17),
                user_id="u_local_1",
                snapshot=_four_domain_snapshot_calm(),
            )
            orphan_row = conn.execute(
                "SELECT affected_domain, orphan FROM x_rule_firing "
                "WHERE daily_plan_id = ? AND x_rule_id = 'X_FAKE'",
                (result.daily_plan_id,),
            ).fetchone()
            assert orphan_row is not None
            # Strength is a supported domain as of the Phase 7 closure wire-up,
            # but orphan status is about "in THIS plan's proposal set" — we
            # only inserted a recovery proposal, so a firing targeting
            # strength remains orphan.
            assert orphan_row["affected_domain"] == "strength"
            assert orphan_row["orphan"] == 1
        finally:
            conn.close()
    finally:
        synthesis_mod.evaluate_phase_a = original


# ---------------------------------------------------------------------------
# Phase 7 closure — strength as a real proposal/synthesis-participating domain
# ---------------------------------------------------------------------------

def _strength_proposal(**overrides):
    base = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS["strength"],
        "proposal_id": "prop_2026-04-17_u_local_1_strength_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-17",
        "domain": "strength",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "rationale": ["recent_volume_trend=steady"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


def test_synthesize_emits_strength_recommendation_with_correct_schema(tmp_path):
    """A strength proposal on a quiet snapshot yields a committed
    strength recommendation: correct schema_version, domain, and
    domain-aware review question."""

    db_path = _fresh_db(tmp_path)
    _insert_proposal(db_path, _strength_proposal())

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=date(2026, 4, 17),
            user_id="u_local_1",
            snapshot=_quiet_snapshot(),
        )
    finally:
        conn.close()

    # One recommendation, linked to the canonical plan.
    assert result.recommendation_ids == ["rec_2026-04-17_u_local_1_strength_01"]
    assert result.phase_a_firings == []
    assert result.phase_b_firings == []

    conn = open_connection(db_path)
    try:
        rec_row = conn.execute(
            "SELECT action, domain, payload_json FROM recommendation_log "
            "WHERE recommendation_id = ?",
            (result.recommendation_ids[0],),
        ).fetchone()
        assert rec_row is not None
        assert rec_row["domain"] == "strength"
        assert rec_row["action"] == "proceed_with_planned_session"
        payload = json.loads(rec_row["payload_json"])
        assert payload["schema_version"] == "strength_recommendation.v1"
        # Domain-aware override kicks in for strength's shared
        # ``proceed_with_planned_session`` action — recovery's recovery-
        # framed prompt does NOT leak onto the strength recommendation.
        assert payload["follow_up"]["review_question"] == (
            "Did today's planned strength session feel appropriate?"
        )
        # Proposal was linked to the committed plan.
        prop_row = conn.execute(
            "SELECT daily_plan_id FROM proposal_log WHERE proposal_id = ?",
            ("prop_2026-04-17_u_local_1_strength_01",),
        ).fetchone()
        assert prop_row["daily_plan_id"] == result.daily_plan_id
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# --bundle-only — read-only skill seam
# ---------------------------------------------------------------------------


def test_cli_synthesize_bundle_only_emits_bundle_without_committing(
    tmp_path, capsys,
):
    """``hai synthesize --bundle-only`` returns (snapshot, proposals,
    phase_a_firings) and writes no daily_plan / recommendation rows.

    The flag is the contract the daily-plan-synthesis skill relies on:
    read the bundle, compose a rationale overlay, call back with
    --drafts-json. Verifying the read-only path stays truthful is the
    guard against regressing back into the --bundle-only-missing state
    that shipped in v0.1.0.
    """

    from health_agent_infra.cli import main as cli_main

    db_path = _fresh_db(tmp_path)
    _insert_proposal(db_path, _running_proposal())

    rc = cli_main([
        "synthesize",
        "--as-of", "2026-04-17",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
        "--bundle-only",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert set(payload.keys()) == {"snapshot", "proposals", "phase_a_firings"}
    assert len(payload["proposals"]) == 1
    assert payload["proposals"][0]["domain"] == "running"

    # Read-only: no daily_plan row persisted.
    conn = open_connection(db_path)
    try:
        row = conn.execute("SELECT COUNT(*) AS n FROM daily_plan").fetchone()
        assert row["n"] == 0
    finally:
        conn.close()


def test_cli_synthesize_bundle_only_rejects_conflicting_flags(
    tmp_path, capsys,
):
    """--bundle-only is mutually exclusive with --drafts-json and
    --supersede because those mutate state. Reject loudly rather than
    silently ignoring."""

    from health_agent_infra.cli import main as cli_main

    db_path = _fresh_db(tmp_path)
    drafts_path = tmp_path / "drafts.json"
    drafts_path.write_text("[]")

    rc = cli_main([
        "synthesize",
        "--as-of", "2026-04-17",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
        "--bundle-only",
        "--drafts-json", str(drafts_path),
    ])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "bundle-only" in err.lower()
