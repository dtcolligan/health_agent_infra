"""Unit tests for Phase 2 step 4: synthesis X-rule evaluators.

Covers each rule's positive + negative case, tier precedence in
``apply_phase_a``, and the Phase B write-surface guard.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS
from health_agent_infra.core.synthesis_policy import (
    PHASE_B_TARGETS,
    XRuleFiring,
    XRuleWriteSurfaceViolation,
    apply_phase_a,
    apply_phase_b,
    evaluate_phase_a,
    evaluate_phase_b,
    evaluate_x1a,
    evaluate_x1b,
    evaluate_x3a,
    evaluate_x3b,
    evaluate_x6a,
    evaluate_x6b,
    evaluate_x7,
    evaluate_x9,
    guard_phase_b_mutation,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _thresholds(**overrides):
    cfg = deepcopy(DEFAULT_THRESHOLDS)
    for path, value in overrides.items():
        keys = path.split(".")
        cursor = cfg
        for k in keys[:-1]:
            cursor = cursor.setdefault(k, {})
        cursor[keys[-1]] = value
    return cfg


def _snapshot(
    *,
    sleep_debt_band=None,
    acwr_ratio=None,
    body_battery=None,
    all_day_stress=None,
    planned_session_type: str | None = "hard",
):
    """Build a minimal snapshot matching the Phase-3 block layout.

    Post-migration 004, body_battery and Garmin all-day-stress live on
    the stress block (`stress.today_body_battery`, `stress.today_garmin`).
    Synthesis policy reads them from there. Sleep_debt_band still comes
    off `recovery.classified_state.sleep_debt_band` in this helper —
    Phase 3 step 5 will move it to `sleep.classified_state.sleep_debt_band`
    once the sleep-domain classifier lands.

    ``planned_session_type`` defaults to ``"hard"`` so legacy X9 tests
    that pre-date the v0.1.4 precondition (acceptance criterion #7) keep
    asserting their original behaviour. Pass ``None`` to exercise the
    "user hasn't planned anything" gate.
    """

    recovery: dict = {"classified_state": {}, "today": {}}
    stress: dict = {"today": {}}
    if sleep_debt_band is not None:
        recovery["classified_state"]["sleep_debt_band"] = sleep_debt_band
    if acwr_ratio is not None:
        recovery["today"]["acwr_ratio"] = acwr_ratio
    if planned_session_type is not None:
        recovery["evidence"] = {"planned_session_type": planned_session_type}
    if body_battery is not None:
        stress["today_body_battery"] = body_battery
        stress["today"]["body_battery_end_of_day"] = body_battery
    if all_day_stress is not None:
        stress["today_garmin"] = all_day_stress
        stress["today"]["garmin_all_day_stress"] = all_day_stress
    return {"recovery": recovery, "stress": stress}


def _running_hard_proposal(**overrides):
    base = {
        "schema_version": "running_proposal.v1",
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


def _recovery_hard_proposal(**overrides):
    base = {
        "schema_version": "recovery_proposal.v1",
        "proposal_id": "prop_2026-04-17_u_local_1_recovery_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-17",
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "rationale": ["sleep_debt=none"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# X1a — sleep_debt=moderate softens hard sessions
# ---------------------------------------------------------------------------

def test_x1a_fires_on_moderate_sleep_debt_with_hard_running():
    firings = evaluate_x1a(
        _snapshot(sleep_debt_band="moderate"),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    assert firings[0].rule_id == "X1a"
    assert firings[0].tier == "soften"
    assert firings[0].affected_domain == "running"
    assert firings[0].recommended_mutation["action"] == "downgrade_to_easy_aerobic"


def test_x1a_does_not_fire_on_mild_sleep_debt():
    firings = evaluate_x1a(
        _snapshot(sleep_debt_band="mild"),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x1a_skips_already_softened_proposal():
    prop = _running_hard_proposal(action="downgrade_to_easy_aerobic")
    firings = evaluate_x1a(
        _snapshot(sleep_debt_band="moderate"),
        [prop],
        _thresholds(),
    )
    assert firings == []


def test_x1a_fires_against_recovery_domain_too():
    firings = evaluate_x1a(
        _snapshot(sleep_debt_band="moderate"),
        [_recovery_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    assert firings[0].affected_domain == "recovery"
    assert firings[0].recommended_mutation["action"] == "downgrade_hard_session_to_zone_2"


# ---------------------------------------------------------------------------
# X1b — elevated sleep_debt escalates hard sessions
# ---------------------------------------------------------------------------

def test_x1b_fires_on_elevated_sleep_debt():
    firings = evaluate_x1b(
        _snapshot(sleep_debt_band="elevated"),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    assert firings[0].tier == "block"
    assert firings[0].recommended_mutation["action"] == "escalate_for_user_review"


def test_x1b_does_not_fire_on_moderate_sleep_debt():
    firings = evaluate_x1b(
        _snapshot(sleep_debt_band="moderate"),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


# ---------------------------------------------------------------------------
# X3a — 1.3 ≤ acwr < 1.5 softens
# ---------------------------------------------------------------------------

def test_x3a_fires_in_ratio_band():
    firings = evaluate_x3a(
        _snapshot(acwr_ratio=1.4),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    assert firings[0].rule_id == "X3a"
    assert firings[0].tier == "soften"


def test_x3a_does_not_fire_below_lower_bound():
    firings = evaluate_x3a(
        _snapshot(acwr_ratio=1.25),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x3a_does_not_fire_at_upper_bound_reserved_for_x3b():
    firings = evaluate_x3a(
        _snapshot(acwr_ratio=1.5),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


# ---------------------------------------------------------------------------
# X3b — acwr ≥ 1.5 blocks
# ---------------------------------------------------------------------------

def test_x3b_fires_at_threshold():
    firings = evaluate_x3b(
        _snapshot(acwr_ratio=1.5),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    assert firings[0].tier == "block"
    assert firings[0].recommended_mutation["action"] == "escalate_for_user_review"


def test_x3b_does_not_fire_below_threshold():
    firings = evaluate_x3b(
        _snapshot(acwr_ratio=1.49),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


# ---------------------------------------------------------------------------
# X6a — body_battery < 30 softens (but not < 15 which is X6b territory)
# ---------------------------------------------------------------------------

def test_x6a_fires_on_depleted_body_battery():
    firings = evaluate_x6a(
        _snapshot(body_battery=25),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    assert firings[0].tier == "soften"


def test_x6a_does_not_fire_when_x6b_also_would():
    """Avoid double-downgrading: when body_battery is low enough for X6b,
    X6a yields so the block tier wins cleanly."""
    firings = evaluate_x6a(
        _snapshot(body_battery=10),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x6a_does_not_fire_above_threshold():
    firings = evaluate_x6a(
        _snapshot(body_battery=45),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


# ---------------------------------------------------------------------------
# X6b — body_battery < 15 blocks
# ---------------------------------------------------------------------------

def test_x6b_fires_on_critically_low_body_battery():
    firings = evaluate_x6b(
        _snapshot(body_battery=10),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    assert firings[0].tier == "block"


def test_x6b_does_not_fire_at_x6a_level():
    firings = evaluate_x6b(
        _snapshot(body_battery=25),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


# ---------------------------------------------------------------------------
# X7 — elevated stress caps confidence
# ---------------------------------------------------------------------------

def test_x7_fires_on_high_stress_and_caps_every_proposal():
    firings = evaluate_x7(
        _snapshot(all_day_stress=65),
        [_running_hard_proposal(), _recovery_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 2
    assert {f.affected_domain for f in firings} == {"running", "recovery"}
    assert {f.tier for f in firings} == {"cap_confidence"}
    assert all(f.recommended_mutation is None for f in firings)


def test_x7_fires_even_on_softened_proposals():
    """Confidence cap doesn't check whether a proposal is hard — it caps
    regardless so stress-driven uncertainty propagates to every domain."""
    prop = _running_hard_proposal(action="downgrade_to_easy_aerobic")
    firings = evaluate_x7(
        _snapshot(all_day_stress=85),  # very_high
        [prop],
        _thresholds(),
    )
    assert len(firings) == 1


def test_x7_does_not_fire_on_low_stress():
    firings = evaluate_x7(
        _snapshot(all_day_stress=30),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


# ---------------------------------------------------------------------------
# Phase A tolerates missing signals
# ---------------------------------------------------------------------------

def test_phase_a_no_firings_on_empty_snapshot():
    firings = evaluate_phase_a({}, [_running_hard_proposal()], _thresholds())
    assert firings == []


def test_phase_a_no_firings_on_empty_proposals():
    firings = evaluate_phase_a(
        _snapshot(acwr_ratio=1.6, body_battery=10, all_day_stress=95),
        [],
        _thresholds(),
    )
    assert firings == []


def test_phase_a_runs_every_evaluator():
    """Compound scenario: sleep_debt=moderate, acwr=1.52, body_battery=12,
    stress=high. Expect X1a, X3b, X6b, and X7 to fire (X6a and X3a suppressed
    by the more-severe variants)."""
    snap = _snapshot(
        sleep_debt_band="moderate",
        acwr_ratio=1.52,
        body_battery=12,
        all_day_stress=85,
    )
    firings = evaluate_phase_a(
        snap, [_running_hard_proposal()], _thresholds(),
    )
    fired_ids = sorted({f.rule_id for f in firings})
    assert fired_ids == ["X1a", "X3b", "X6b", "X7"]


# ---------------------------------------------------------------------------
# apply_phase_a: tier precedence
# ---------------------------------------------------------------------------

def test_apply_phase_a_block_beats_soften():
    proposal = _running_hard_proposal()
    firings = [
        XRuleFiring(
            rule_id="X1a",
            tier="soften",
            affected_domain="running",
            trigger_note="soften",
            recommended_mutation={
                "action": "downgrade_to_easy_aerobic",
                "action_detail": {"reason_token": "soft"},
            },
            source_signals={},
            phase="A",
        ),
        XRuleFiring(
            rule_id="X3b",
            tier="block",
            affected_domain="running",
            trigger_note="block",
            recommended_mutation={
                "action": "escalate_for_user_review",
                "action_detail": {"reason_token": "block"},
            },
            source_signals={},
            phase="A",
        ),
    ]
    mutated, fired = apply_phase_a(proposal, firings)
    assert mutated["action"] == "escalate_for_user_review"
    assert mutated["action_detail"]["reason_token"] == "block"
    assert sorted(fired) == ["X1a", "X3b"]


def test_apply_phase_a_cap_confidence_lowers_high_but_never_raises():
    proposal = _running_hard_proposal(confidence="high")
    cap = XRuleFiring(
        rule_id="X7",
        tier="cap_confidence",
        affected_domain="running",
        trigger_note="cap",
        recommended_mutation=None,
        source_signals={},
        phase="A",
    )
    mutated, _ = apply_phase_a(proposal, [cap])
    assert mutated["confidence"] == "moderate"

    # Already at moderate → no change.
    proposal2 = _running_hard_proposal(confidence="moderate")
    mutated2, _ = apply_phase_a(proposal2, [cap])
    assert mutated2["confidence"] == "moderate"

    # Already low → NEVER raised (cap is one-way).
    proposal3 = _running_hard_proposal(confidence="low")
    mutated3, _ = apply_phase_a(proposal3, [cap])
    assert mutated3["confidence"] == "low"


def test_apply_phase_a_firings_on_other_domain_are_ignored():
    proposal = _running_hard_proposal()
    other_domain_firing = XRuleFiring(
        rule_id="X1a",
        tier="soften",
        affected_domain="recovery",  # different domain
        trigger_note="",
        recommended_mutation={"action": "downgrade_hard_session_to_zone_2"},
        source_signals={},
        phase="A",
    )
    mutated, fired = apply_phase_a(proposal, [other_domain_firing])
    assert mutated["action"] == "proceed_with_planned_run"  # unchanged
    assert fired == []


def test_apply_phase_a_does_not_mutate_input():
    proposal = _running_hard_proposal()
    original = deepcopy(proposal)
    firing = XRuleFiring(
        rule_id="X1a",
        tier="soften",
        affected_domain="running",
        trigger_note="",
        recommended_mutation={
            "action": "downgrade_to_easy_aerobic",
            "action_detail": {"token": "x"},
        },
        source_signals={},
        phase="A",
    )
    apply_phase_a(proposal, [firing])
    assert proposal == original


# ---------------------------------------------------------------------------
# Phase B — write-surface guard
# ---------------------------------------------------------------------------

def test_phase_b_guard_rejects_non_B_phase():
    firing = XRuleFiring(
        rule_id="X9",
        tier="adjust",
        affected_domain="nutrition",
        trigger_note="",
        recommended_mutation={"action_detail": {}},
        source_signals={},
        phase="A",  # wrong!
    )
    with pytest.raises(XRuleWriteSurfaceViolation):
        guard_phase_b_mutation(firing)


def test_phase_b_guard_rejects_non_adjust_tier():
    firing = XRuleFiring(
        rule_id="X9",
        tier="soften",  # wrong!
        affected_domain="nutrition",
        trigger_note="",
        recommended_mutation={"action_detail": {}},
        source_signals={},
        phase="B",
    )
    with pytest.raises(XRuleWriteSurfaceViolation):
        guard_phase_b_mutation(firing)


def test_phase_b_guard_rejects_off_registry_domain():
    firing = XRuleFiring(
        rule_id="X9",
        tier="adjust",
        affected_domain="running",  # X9 only allowed for nutrition
        trigger_note="",
        recommended_mutation={"action_detail": {}},
        source_signals={},
        phase="B",
    )
    with pytest.raises(XRuleWriteSurfaceViolation):
        guard_phase_b_mutation(firing)


def test_phase_b_guard_rejects_action_mutation():
    firing = XRuleFiring(
        rule_id="X9",
        tier="adjust",
        affected_domain="nutrition",
        trigger_note="",
        recommended_mutation={
            "action": "escalate_for_user_review",
            "action_detail": {},
        },
        source_signals={},
        phase="B",
    )
    with pytest.raises(XRuleWriteSurfaceViolation):
        guard_phase_b_mutation(firing)


def test_phase_b_guard_rejects_none_mutation():
    firing = XRuleFiring(
        rule_id="X9",
        tier="adjust",
        affected_domain="nutrition",
        trigger_note="",
        recommended_mutation=None,
        source_signals={},
        phase="B",
    )
    with pytest.raises(XRuleWriteSurfaceViolation):
        guard_phase_b_mutation(firing)


def test_phase_b_guard_rejects_unregistered_rule_id():
    firing = XRuleFiring(
        rule_id="X99_not_registered",
        tier="adjust",
        affected_domain="nutrition",
        trigger_note="",
        recommended_mutation={"action_detail": {}},
        source_signals={},
        phase="B",
    )
    with pytest.raises(XRuleWriteSurfaceViolation):
        guard_phase_b_mutation(firing)


def test_phase_b_guard_accepts_valid_firing():
    firing = XRuleFiring(
        rule_id="X9",
        tier="adjust",
        affected_domain="nutrition",
        trigger_note="",
        recommended_mutation={"action_detail": {"target": 100}},
        source_signals={},
        phase="B",
    )
    # Does not raise.
    guard_phase_b_mutation(firing)


def test_phase_b_targets_registry_matches_implementation():
    """Lock the Phase B targets registry so a reviewer notices at review time
    if someone adds a rule id without also listing its legal target domains."""
    assert PHASE_B_TARGETS == {"X9": frozenset({"nutrition"})}


# ---------------------------------------------------------------------------
# X9 (Phase B) and apply_phase_b
# ---------------------------------------------------------------------------

def test_x9_returns_empty_without_nutrition_draft():
    # Today's domains don't include nutrition yet.
    drafts = [
        {
            "domain": "running",
            "action": "proceed_with_planned_run",
            "action_detail": None,
        },
    ]
    firings = evaluate_x9(_snapshot(), drafts, _thresholds())
    assert firings == []


def test_x9_fires_when_nutrition_draft_and_hard_training_present():
    drafts = [
        {
            "domain": "running",
            "action": "proceed_with_planned_run",
            "action_detail": None,
        },
        {
            "domain": "nutrition",
            "action": "maintain_targets",
            "action_detail": {"protein_target_g": 140},
        },
    ]
    firings = evaluate_x9(_snapshot(), drafts, _thresholds())
    assert len(firings) == 1
    assert firings[0].rule_id == "X9"
    assert firings[0].phase == "B"
    assert firings[0].tier == "adjust"
    assert firings[0].affected_domain == "nutrition"


def test_apply_phase_b_merges_action_detail_without_touching_action():
    draft = {
        "domain": "nutrition",
        "action": "maintain_targets",
        "action_detail": {"protein_target_g": 140},
    }
    firing = XRuleFiring(
        rule_id="X9",
        tier="adjust",
        affected_domain="nutrition",
        trigger_note="",
        recommended_mutation={
            "action_detail": {"protein_target_multiplier": 1.1},
        },
        source_signals={},
        phase="B",
    )
    mutated, fired = apply_phase_b(draft, [firing])
    assert mutated["action"] == "maintain_targets"  # unchanged
    assert mutated["action_detail"]["protein_target_g"] == 140  # preserved
    assert mutated["action_detail"]["protein_target_multiplier"] == 1.1  # merged in
    assert fired == ["X9"]


def test_apply_phase_b_rejects_malformed_firing_at_apply_time():
    """A firing that escapes evaluate_phase_b without going through the guard
    must still fail at apply_phase_b. Defense in depth."""
    draft = {"domain": "nutrition", "action": "maintain_targets", "action_detail": {}}
    malformed = XRuleFiring(
        rule_id="X9",
        tier="adjust",
        affected_domain="nutrition",
        trigger_note="",
        recommended_mutation={"action": "escalate_for_user_review"},  # illegal
        source_signals={},
        phase="B",
    )
    with pytest.raises(XRuleWriteSurfaceViolation):
        apply_phase_b(draft, [malformed])


# ---------------------------------------------------------------------------
# Phase 3 step 5 — X1 / X6 / X7 source-of-truth rewires
# ---------------------------------------------------------------------------
# These tests pin the contract that after Phase 3 step 5:
#   - X1 reads sleep_debt_band from the **sleep** block first, then falls
#     back to the recovery block (legacy path for snapshots built without
#     the sleep-domain expansion).
#   - X6 reads body_battery from the **stress** block
#     (``stress.today_body_battery``).
#   - X7 reads garmin_stress_band from the **stress** classified_state.


def _sleep_block(sleep_debt_band=None):
    block: dict = {"classified_state": {}}
    if sleep_debt_band is not None:
        block["classified_state"]["sleep_debt_band"] = sleep_debt_band
    return block


def _stress_block(
    *,
    classified_band=None,
    today_garmin=None,
    body_battery=None,
):
    block: dict = {"classified_state": {}, "today": {}}
    if classified_band is not None:
        block["classified_state"]["garmin_stress_band"] = classified_band
    if today_garmin is not None:
        block["today_garmin"] = today_garmin
        block["today"]["garmin_all_day_stress"] = today_garmin
    if body_battery is not None:
        block["today_body_battery"] = body_battery
        block["today"]["body_battery_end_of_day"] = body_battery
    return block


def test_x1a_reads_sleep_classified_state_as_primary_source():
    """Phase 3 step 5 rewire: when the sleep block carries a
    classified_state.sleep_debt_band, X1a triggers off that value —
    NOT off the recovery echo."""

    snapshot = {
        "sleep": _sleep_block(sleep_debt_band="moderate"),
        # Recovery block deliberately carries a contradicting value to
        # prove the sleep block is preferred.
        "recovery": {"classified_state": {"sleep_debt_band": "none"}, "today": {}},
    }
    firings = evaluate_x1a(snapshot, [_running_hard_proposal()], _thresholds())
    assert len(firings) == 1
    assert firings[0].rule_id == "X1a"


def test_x1a_falls_back_to_recovery_when_sleep_block_absent():
    """Backward-compat: snapshots built without --evidence-json carry
    only the recovery cross-domain echo; X1 still fires off it."""

    snapshot = {
        "recovery": {"classified_state": {"sleep_debt_band": "moderate"}, "today": {}},
        # No sleep block at all — mimics the v1.0 snapshot shape.
    }
    firings = evaluate_x1a(snapshot, [_running_hard_proposal()], _thresholds())
    assert len(firings) == 1


def test_x1a_sleep_block_without_classified_state_falls_back_to_recovery():
    """Defensive: a sleep block without classified_state (no expansion)
    doesn't poison the primary read — X1 keeps using recovery's echo."""

    snapshot = {
        "sleep": {"today": None, "history": [], "missingness": "absent"},
        "recovery": {"classified_state": {"sleep_debt_band": "moderate"}, "today": {}},
    }
    firings = evaluate_x1a(snapshot, [_running_hard_proposal()], _thresholds())
    assert len(firings) == 1


def test_x1b_reads_sleep_classified_state_as_primary_source():
    snapshot = {
        "sleep": _sleep_block(sleep_debt_band="elevated"),
        "recovery": {"classified_state": {"sleep_debt_band": "none"}, "today": {}},
    }
    firings = evaluate_x1b(snapshot, [_running_hard_proposal()], _thresholds())
    assert len(firings) == 1
    assert firings[0].tier == "block"


def test_x6a_reads_body_battery_from_stress_block():
    """Post-Phase-3: body_battery lives on stress, not recovery. X6a
    must read from stress.today_body_battery."""

    snapshot = {
        "stress": _stress_block(body_battery=25),
        "recovery": {"classified_state": {}, "today": {}},
    }
    firings = evaluate_x6a(snapshot, [_running_hard_proposal()], _thresholds())
    assert len(firings) == 1
    assert firings[0].source_signals["body_battery_end_of_day"] == 25


def test_x6b_reads_body_battery_from_stress_block():
    snapshot = {
        "stress": _stress_block(body_battery=10),
        "recovery": {"classified_state": {}, "today": {}},
    }
    firings = evaluate_x6b(snapshot, [_running_hard_proposal()], _thresholds())
    assert len(firings) == 1
    assert firings[0].tier == "block"


def test_x7_prefers_stress_classified_state_band_over_raw_score():
    """Phase 3 step 5: X7 reads stress.classified_state.garmin_stress_band
    as primary source. The raw-score fallback is defensive only — when
    the band is present, the raw score is NOT re-banded."""

    # Band says "high" (triggers); raw score says 10 (would be "low").
    # If X7 re-derived from raw, it wouldn't fire; it must honor the band.
    snapshot = {
        "stress": _stress_block(classified_band="high", today_garmin=10),
        "recovery": {"classified_state": {}, "today": {}},
    }
    firings = evaluate_x7(snapshot, [_running_hard_proposal()], _thresholds())
    assert len(firings) == 1
    assert firings[0].source_signals["stress_band"] == "high"


def test_x7_falls_back_to_raw_garmin_score_when_classified_state_missing():
    """When the stress block has no classified_state (v1.0 snapshot with
    no evidence bundle), X7 falls back to local banding of
    stress.today_garmin."""

    snapshot = {
        "stress": _stress_block(today_garmin=65),  # high band by thresholds
        "recovery": {"classified_state": {}, "today": {}},
    }
    firings = evaluate_x7(snapshot, [_running_hard_proposal()], _thresholds())
    assert len(firings) == 1
