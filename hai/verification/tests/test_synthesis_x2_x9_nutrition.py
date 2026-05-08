"""Phase 5 step 4 — X2 + X9 synthesis wiring tests (macros-only v1).

Covers:

  1. X2 (Phase A, soften): nutrition deficit / low protein softens hard
     strength + recovery proposals. Running is intentionally NOT an X2
     target (see synthesis_policy.evaluate_x2 docstring).
  2. X2 reads the nutrition classifier's output when the snapshot
     carries the Phase-5 nutrition block; falls back to computing
     against config targets from ``nutrition.today`` when the block
     wasn't expanded (e.g. on pre-step-4 snapshots).
  3. X9 (Phase B, adjust): the widened training-hard detection now
     includes strength, not just recovery/running.
  4. Tier precedence with X2 + other Phase-A rules.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS
from health_agent_infra.core.synthesis_policy import (
    XRuleFiring,
    apply_phase_a,
    apply_phase_b,
    evaluate_phase_a,
    evaluate_phase_b,
    evaluate_x2,
    evaluate_x9,
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
    calorie_deficit_kcal=None,
    protein_ratio=None,
    nutrition_today=None,
    use_classifier=True,
    planned_session_type: str | None = "hard",
):
    """Build a minimal Phase 5 snapshot carrying the nutrition block.

    When ``use_classifier`` is True (the normal path), the classifier
    fields are placed under ``nutrition.classified_state`` so X2 reads
    them directly. When False, only ``nutrition.today`` is populated
    and X2 must fall back to computing from that row against the
    config targets.

    ``planned_session_type`` defaults to ``"hard"`` so legacy X9 tests
    that pre-date the v0.1.4 precondition keep asserting their original
    behaviour. Pass ``None`` to exercise the "user hasn't planned
    anything" gate added in acceptance criterion #7.
    """

    nutrition: dict = {}
    if use_classifier and (calorie_deficit_kcal is not None or protein_ratio is not None):
        nutrition["classified_state"] = {
            "calorie_deficit_kcal": calorie_deficit_kcal,
            "protein_ratio": protein_ratio,
        }
    if nutrition_today is not None:
        nutrition["today"] = nutrition_today
    recovery: dict = {"classified_state": {}, "today": {}}
    if planned_session_type is not None:
        recovery["evidence"] = {"planned_session_type": planned_session_type}
    return {
        "recovery": recovery,
        "stress": {"today": {}},
        "running": {"history": []},
        "strength": {"history": []},
        "nutrition": nutrition,
    }


def _strength_hard_proposal(**overrides):
    base = {
        "schema_version": "strength_proposal.v1",
        "proposal_id": "prop_2026-04-18_u_local_1_strength_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-18",
        "domain": "strength",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "rationale": ["recent_volume_band=moderate"],
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
        "proposal_id": "prop_2026-04-18_u_local_1_recovery_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-18",
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


def _running_hard_proposal(**overrides):
    base = {
        "schema_version": "running_proposal.v1",
        "proposal_id": "prop_2026-04-18_u_local_1_running_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-18",
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


# ---------------------------------------------------------------------------
# X2 — deficit / low protein softens hard strength + recovery
# ---------------------------------------------------------------------------

def test_x2_fires_on_high_calorie_deficit_against_hard_strength():
    firings = evaluate_x2(
        _snapshot(calorie_deficit_kcal=500.0, protein_ratio=0.95),
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    f = firings[0]
    assert f.rule_id == "X2"
    assert f.tier == "soften"
    assert f.affected_domain == "strength"
    assert f.recommended_mutation["action"] == "downgrade_to_moderate_load"
    assert f.recommended_mutation["action_detail"]["reason_token"] == (
        "x2_nutrition_calorie_deficit"
    )


def test_x2_fires_on_very_low_protein_ratio_against_hard_strength():
    firings = evaluate_x2(
        _snapshot(calorie_deficit_kcal=100.0, protein_ratio=0.65),
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    assert firings[0].recommended_mutation["action_detail"]["reason_token"] == (
        "x2_nutrition_protein_gap"
    )


def test_x2_fires_on_both_triggers_combined_reason_token():
    firings = evaluate_x2(
        _snapshot(calorie_deficit_kcal=550.0, protein_ratio=0.65),
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    assert firings[0].recommended_mutation["action_detail"]["reason_token"] == (
        "x2_nutrition_deficit_and_protein_gap"
    )


def test_x2_fires_against_hard_recovery_too():
    firings = evaluate_x2(
        _snapshot(calorie_deficit_kcal=500.0, protein_ratio=0.95),
        [_recovery_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    assert firings[0].affected_domain == "recovery"
    assert firings[0].recommended_mutation["action"] == (
        "downgrade_hard_session_to_zone_2"
    )


def test_x2_does_not_target_running_in_v1():
    """Endurance fuelling is a different question than heavy-load
    training; X2 in v1 does not soften running proposals (see
    evaluate_x2 docstring)."""

    firings = evaluate_x2(
        _snapshot(calorie_deficit_kcal=700.0, protein_ratio=0.5),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x2_does_not_fire_below_thresholds():
    firings = evaluate_x2(
        _snapshot(calorie_deficit_kcal=200.0, protein_ratio=0.9),
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x2_skips_already_softened_strength_proposal():
    prop = _strength_hard_proposal(action="downgrade_to_moderate_load")
    firings = evaluate_x2(
        _snapshot(calorie_deficit_kcal=600.0, protein_ratio=0.5),
        [prop],
        _thresholds(),
    )
    assert firings == []


def test_x2_falls_back_to_today_row_when_classifier_absent():
    """Snapshots built without ``--evidence-json`` don't carry the
    nutrition classifier output on the block. X2 must still fire on
    ``nutrition.today`` against the config targets so the rule is
    evaluable on test fixtures + pre-step-4 snapshots."""

    # calorie target default = 2400; actual 1800 → deficit 600 (>=500).
    today = {
        "calories": 1800.0,
        "protein_g": 140.0,
        "carbs_g": 220.0,
        "fat_g": 60.0,
    }
    firings = evaluate_x2(
        _snapshot(nutrition_today=today, use_classifier=False),
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    assert firings[0].rule_id == "X2"


def test_x2_does_not_fire_when_nutrition_absent():
    firings = evaluate_x2(
        _snapshot(),  # no classifier, no today row
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x2_threshold_overridable_via_thresholds():
    """A user config can tighten X2's deficit threshold without code
    changes. At a 300-kcal trigger, a 300-kcal deficit now fires."""

    firings = evaluate_x2(
        _snapshot(calorie_deficit_kcal=300.0, protein_ratio=0.95),
        [_strength_hard_proposal()],
        _thresholds(**{"synthesis.x_rules.x2.deficit_kcal_min": 300.0}),
    )
    assert len(firings) == 1


# ---------------------------------------------------------------------------
# X2 + apply_phase_a — end-to-end proposal mutation
# ---------------------------------------------------------------------------

def test_x2_end_to_end_softens_strength_via_apply_phase_a():
    snap = _snapshot(calorie_deficit_kcal=600.0, protein_ratio=0.95)
    proposals = [_strength_hard_proposal()]
    firings = evaluate_phase_a(snap, proposals, _thresholds())

    mutated, fired = apply_phase_a(proposals[0], firings)
    assert mutated["action"] == "downgrade_to_moderate_load"
    assert "X2" in fired


# ---------------------------------------------------------------------------
# X9 — widened hard-training detection includes strength
# ---------------------------------------------------------------------------

def _nutrition_draft(**overrides):
    base = {
        "schema_version": "nutrition_recommendation.v1",
        "domain": "nutrition",
        "action": "maintain_targets",
        "action_detail": {"protein_target_g": 140},
    }
    base.update(overrides)
    return base


def _strength_draft_hard(**overrides):
    base = {
        "schema_version": "strength_recommendation.v1",
        "domain": "strength",
        "action": "proceed_with_planned_session",
        "action_detail": None,
    }
    base.update(overrides)
    return base


def _recovery_draft_hard(**overrides):
    base = {
        "schema_version": "training_recommendation.v1",
        "domain": "recovery",
        "action": "proceed_with_planned_session",
        "action_detail": None,
    }
    base.update(overrides)
    return base


def test_x9_fires_when_hard_strength_accompanies_nutrition_draft():
    """Phase 5 step 4 widens X9's training-hard detection from
    {recovery, running} to {recovery, running, strength}. A hard
    strength session post-synthesis now triggers the protein/carb
    target bump on the nutrition recommendation."""

    drafts = [_strength_draft_hard(), _nutrition_draft()]
    firings = evaluate_x9(_snapshot(), drafts, _thresholds())
    assert len(firings) == 1
    f = firings[0]
    assert f.rule_id == "X9"
    assert f.phase == "B"
    assert f.tier == "adjust"
    assert f.affected_domain == "nutrition"


def test_x9_still_fires_on_hard_recovery_alone():
    drafts = [_recovery_draft_hard(), _nutrition_draft()]
    firings = evaluate_x9(_snapshot(), drafts, _thresholds())
    assert len(firings) == 1


def test_x9_does_not_fire_when_strength_already_softened():
    drafts = [
        _strength_draft_hard(action="downgrade_to_moderate_load"),
        _nutrition_draft(),
    ]
    firings = evaluate_x9(_snapshot(), drafts, _thresholds())
    assert firings == []


def test_x9_does_not_fire_when_planned_session_type_is_null(tmp_path=None):
    """Acceptance criterion #7: X9 only fires when the user has
    explicitly planned a session. A bundle that looks hard on its face
    (recovery/running/strength proposals with their baseline-hard
    actions) no longer triggers a protein bump if no readiness intake
    has declared a planned session type.

    This blocks the pre-v0.1.4 footgun where a first-run user with no
    intake still got their nutrition nudged because the default
    proposals were "hard."
    """

    drafts = [_strength_draft_hard(), _nutrition_draft()]
    # planned_session_type=None exercises the new gate.
    firings = evaluate_x9(
        _snapshot(planned_session_type=None), drafts, _thresholds(),
    )
    assert firings == [], (
        "X9 fired despite no planned_session_type in evidence — "
        "precondition gate (#7) not enforced"
    )


def test_x9_fires_even_when_planned_session_type_is_non_hard_text():
    """The gate is strictly "non-null," not "hardness-matching."
    A user who states any planned session (e.g. ``"intervals"``,
    ``"easy"``, ``"rest"``) satisfies the precondition; the hardness
    check remains on the draft itself. Intent: don't overload the gate
    with a second round of string-parsing — readiness intake states
    intent; proposals state what the system recommends doing.
    """

    drafts = [_strength_draft_hard(), _nutrition_draft()]
    firings = evaluate_x9(
        _snapshot(planned_session_type="intervals_4x4_z4_z2"),
        drafts,
        _thresholds(),
    )
    assert len(firings) == 1
    assert firings[0].rule_id == "X9"


def test_x9_does_not_fire_when_planned_set_but_no_hard_training_draft():
    """Precondition is necessary but not sufficient. A bundle where
    every training draft has already been softened to a non-baseline
    action must not trigger X9 even if the user planned something
    hard, because the runtime's eventual plan isn't hard either."""

    softened_strength = _strength_draft_hard(action="downgrade_to_moderate_load")
    firings = evaluate_x9(
        _snapshot(planned_session_type="hard"),
        [softened_strength, _nutrition_draft()],
        _thresholds(),
    )
    assert firings == []


def test_x9_mutates_only_action_detail_not_action():
    drafts = [_strength_draft_hard(), _nutrition_draft()]
    firings = evaluate_phase_b(_snapshot(), drafts, _thresholds())
    assert len(firings) == 1

    mutated, fired = apply_phase_b(drafts[1], firings)
    # action is unchanged.
    assert mutated["action"] == "maintain_targets"
    # action_detail carries the X9 protein multiplier on top of prior contents.
    assert mutated["action_detail"]["protein_target_g"] == 140
    assert mutated["action_detail"]["protein_target_multiplier"] == 1.1
    assert fired == ["X9"]


# ---------------------------------------------------------------------------
# End-to-end: nutrition + strength proposals through the full synthesis
# policy pipeline. X2 softens strength; X9 fires on the softened draft?
# No — X9's hard-training check runs against DRAFTS (post-Phase-A), so a
# strength draft that X2 softened is no longer hard → X9 does not fire
# on strength. This is the invariant: X9 adjusts nutrition only when
# the FINAL training action is still hard.
# ---------------------------------------------------------------------------

def test_x2_softening_strength_prevents_x9_from_firing_on_nutrition():
    """Integration edge case: the same day has both a calorie deficit
    (X2 softens strength) and a nutrition draft. Because X2 removes
    strength's hard status in Phase A, X9 in Phase B sees no hard
    training draft and does not fire. This keeps X9 from bumping
    protein on a day the runtime has already de-prioritised the heavy
    session."""

    snap = _snapshot(calorie_deficit_kcal=600.0, protein_ratio=0.95)
    strength_prop = _strength_hard_proposal()
    nutrition_prop = {
        "schema_version": "nutrition_proposal.v1",
        "proposal_id": "prop_2026-04-18_u_local_1_nutrition_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-18",
        "domain": "nutrition",
        "action": "maintain_targets",
        "action_detail": None,
        "rationale": ["calorie_balance_band=mild_deficit"],
        "confidence": "moderate",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }

    phase_a = evaluate_phase_a(snap, [strength_prop, nutrition_prop], _thresholds())
    # X2 should have fired on strength.
    x2 = [f for f in phase_a if f.rule_id == "X2"]
    assert len(x2) == 1

    # Apply Phase A to produce drafts.
    drafts = []
    for p in (strength_prop, nutrition_prop):
        mutated, _ = apply_phase_a(p, phase_a)
        drafts.append(mutated)

    # Strength is no longer hard → X9 must not fire.
    phase_b = evaluate_phase_b(snap, drafts, _thresholds())
    assert phase_b == []


# ---------------------------------------------------------------------------
# End-to-end scenario through run_synthesis — nutrition + hard running
# produces a finalised nutrition recommendation with X9's protein bump
# merged into action_detail by the runtime.
# ---------------------------------------------------------------------------

def test_end_to_end_synthesis_nutrition_and_hard_running(tmp_path):
    """Scenario: the day carries a hard running proposal AND a nutrition
    ``maintain_targets`` proposal. Running is not an X2 target so the
    running draft stays hard through Phase A. Phase B sees a hard
    training draft plus a nutrition draft → X9 fires, merging the
    protein multiplier into nutrition.action_detail. Assert the
    plan + recommendation + firing rows all land atomically."""

    from datetime import date as _date
    from health_agent_infra.core.schemas import canonical_daily_plan_id
    from health_agent_infra.core.state import (
        initialize_database,
        open_connection,
        project_proposal,
    )
    from health_agent_infra.core.synthesis import run_synthesis

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    running_prop = _running_hard_proposal()
    nutrition_prop = {
        "schema_version": "nutrition_proposal.v1",
        "proposal_id": "prop_2026-04-18_u_local_1_nutrition_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-18",
        "domain": "nutrition",
        "action": "maintain_targets",
        "action_detail": {"protein_target_g": 140},
        "rationale": ["calorie_balance_band=met"],
        "confidence": "moderate",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }

    conn = open_connection(db_path)
    try:
        project_proposal(conn, running_prop)
        project_proposal(conn, nutrition_prop)
    finally:
        conn.close()

    # Build a snapshot shape consistent with the rest of this test file
    # — X2 must NOT fire, so nutrition is aligned; body_battery / stress
    # are quiet so X6/X7 stay silent; recovery's sleep_debt is none so
    # X1 stays silent.
    snapshot = {
        "recovery": {
            "classified_state": {"sleep_debt_band": "none"},
            "today": {"acwr_ratio": 1.0},
            # X9 precondition (v0.1.4 #7): user has explicitly planned a session.
            "evidence": {"planned_session_type": "hard"},
        },
        "stress": {"today": {}, "today_body_battery": 80, "today_garmin": 20},
        "running": {"history": []},
        "strength": {"history": []},
        "nutrition": {
            "classified_state": {
                "calorie_deficit_kcal": 0.0,
                "protein_ratio": 1.0,
            },
        },
    }

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=_date(2026, 4, 18),
            user_id="u_local_1",
            snapshot=snapshot,
        )
    finally:
        conn.close()

    assert result.daily_plan_id == canonical_daily_plan_id(
        _date(2026, 4, 18), "u_local_1",
    )
    assert sorted(result.recommendation_ids) == sorted([
        "rec_2026-04-18_u_local_1_running_01",
        "rec_2026-04-18_u_local_1_nutrition_01",
    ])
    # Phase A fired no rules (quiet snapshot).
    assert result.phase_a_firings == []
    # Phase B fired exactly X9 once.
    assert len(result.phase_b_firings) == 1
    f = result.phase_b_firings[0]
    assert f.rule_id == "X9"
    assert f.affected_domain == "nutrition"

    # Verify the nutrition recommendation row carries both the pre-
    # synthesis action_detail key AND the X9-merged multiplier.
    conn = open_connection(db_path)
    try:
        rec_row = conn.execute(
            "SELECT payload_json FROM recommendation_log "
            "WHERE recommendation_id = ?",
            ("rec_2026-04-18_u_local_1_nutrition_01",),
        ).fetchone()
    finally:
        conn.close()
    assert rec_row is not None
    payload = __import__("json").loads(rec_row["payload_json"])
    assert payload["action"] == "maintain_targets"
    assert payload["action_detail"]["protein_target_g"] == 140
    assert payload["action_detail"]["protein_target_multiplier"] == 1.1
    assert payload["action_detail"]["reason_token"] == "x9_training_intensity_bump"


def test_x2_softens_recovery_while_x9_fires_on_hard_running_elsewhere():
    """Complementary integration: a hard running draft remains hard
    after Phase A (X2 does not target running), so X9 still fires the
    nutrition protein bump via the running-is-hard path — even if X2
    softened the recovery proposal in the same plan."""

    snap = _snapshot(calorie_deficit_kcal=600.0, protein_ratio=0.95)
    recovery_prop = _recovery_hard_proposal()
    running_prop = _running_hard_proposal()
    nutrition_prop = {
        "schema_version": "nutrition_proposal.v1",
        "proposal_id": "prop_2026-04-18_u_local_1_nutrition_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-18",
        "domain": "nutrition",
        "action": "maintain_targets",
        "action_detail": None,
        "rationale": ["calorie_balance_band=met"],
        "confidence": "moderate",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }

    phase_a = evaluate_phase_a(
        snap, [recovery_prop, running_prop, nutrition_prop], _thresholds(),
    )
    # X2 softened recovery; running is not a Phase-A X2 target.
    x2_targets = sorted(f.affected_domain for f in phase_a if f.rule_id == "X2")
    assert x2_targets == ["recovery"]

    drafts = []
    for p in (recovery_prop, running_prop, nutrition_prop):
        mutated, _ = apply_phase_a(p, phase_a)
        drafts.append(mutated)

    # Running stayed hard → X9 fires on nutrition.
    phase_b = evaluate_phase_b(snap, drafts, _thresholds())
    assert len(phase_b) == 1
    assert phase_b[0].rule_id == "X9"
    assert phase_b[0].affected_domain == "nutrition"
