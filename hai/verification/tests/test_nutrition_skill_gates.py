"""Phase 5 step 3 contract tests for ``skills/nutrition-alignment/SKILL.md``.

Mirrors the four gates enforced on recovery-readiness, running-readiness,
sleep-quality, stress-regulation, and strength-readiness:

  1. The skill consumes ``classified_state`` and ``policy_result``. No
     band arithmetic, no R-rule evaluation, no mutation logic in prose.
  2. It honours ``forced_action`` and ``capped_confidence`` directly.
  3. It emits only the ``NutritionProposal`` shape (nutrition's pre-
     synthesis write surface — no follow_up, no daily_plan_id).
  4. It is under 120 lines (slightly larger budget than sleep to carry
     the honest micronutrient-unavailability prose + the X9 note).

Plus three nutrition-specific gates:

  5. No micronutrient-specific actions / prose (Phase 2.5 retrieval-gate
     outcome — the data layer does not carry micronutrient evidence).
  6. The skill must honestly surface ``micronutrients_unavailable_at_source``
     rather than infer silence == alignment.
  7. The skill must not pre-bake X9's post-adjust; it is runtime-owned.
"""

from __future__ import annotations

import re
from importlib.resources import files


def _skill_text() -> str:
    return files("health_agent_infra").joinpath(
        "skills", "nutrition-alignment", "SKILL.md"
    ).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Gate 4 — under 120 lines
# ---------------------------------------------------------------------------

def test_gate_4_skill_under_120_lines():
    lines = _skill_text().splitlines()
    assert len(lines) < 120, (
        f"nutrition-alignment SKILL.md is {len(lines)} lines; the Phase 5 "
        f"contract caps it at <120. Move determinism to code, not prose."
    )


# ---------------------------------------------------------------------------
# Gate 1 — consumes classified_state + policy_result; no arithmetic in markdown
# ---------------------------------------------------------------------------

def test_gate_1_skill_references_classified_state_and_policy_result():
    skill = _skill_text()
    assert "classified_state" in skill
    assert "policy_result" in skill


def test_gate_1_skill_names_classified_state_as_source_of_truth():
    skill = _skill_text()
    lower = skill.lower()
    assert "source of truth" in lower, (
        "Skill must explicitly name classified_state (and policy_result) "
        "as the source of truth so a reader cannot mistake the skill for "
        "the arithmetic layer."
    )


def test_gate_1_no_band_threshold_numbers_in_skill_prose():
    """Band-boundary thresholds (calorie targets 2400, protein targets 140,
    hydration 2.5, protein ratio 0.7, deficit 500 / 300 / 100, penalties
    0.05 / 0.15 / 0.25 / 0.30 / 0.10) live in ``core/config.py``. If they
    appear in the skill prose the skill is duplicating — and drifting
    from — the classifier / policy."""

    skill = _skill_text()
    banned_thresholds = [
        # Default calorie target + protein target
        r"\b2400\b",
        r"\b140 ?g\b",
        # Hydration target (default 2.5 L). Ban the ratio 0.75 and the
        # deficit-band kcal boundaries; 2.5 itself is load-bearing as a
        # threshold number and must not appear.
        r"\b2\.5 ?l\b",
        # Calorie-balance band boundaries.
        r"\b500 kcal\b",
        r"\b300 kcal\b",
        r"\b100 kcal\b",
        # Protein-ratio X2 boundary
        r"\b0\.7\b",
        # Hydration ratio boundary
        r"\b0\.75\b",
        # Score penalties
        r"\b0\.05\b",
        r"\b0\.15\b",
        r"\b0\.25\b",
        r"\b0\.30\b",
    ]
    for pattern in banned_thresholds:
        matches = re.findall(pattern, skill, flags=re.IGNORECASE)
        assert not matches, (
            f"Skill prose contains banned threshold {pattern!r}: "
            f"{matches}. Thresholds belong in core/config.py, not markdown."
        )


def test_gate_1_no_score_arithmetic_in_skill():
    skill = _skill_text()
    lower = skill.lower()
    forbidden_phrases = [
        "start at 1.0",
        "subtract from score",
        "add to score",
        "clamp to [0.0, 1.0]",
        "penalty (subtract",
        "deficit = target -",
        "protein_ratio = ",
        "hydration_ratio = ",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lower, (
            f"Skill prose contains arithmetic: {phrase!r}. "
            f"Computation lives in classify.py, not markdown."
        )


def test_gate_1_no_rule_evaluation_in_skill():
    skill = _skill_text()
    lower = skill.lower()
    forbidden = [
        "if coverage is insufficient, return",
        "if coverage is sparse, cap",
        "count how many",
        "at least the deficit threshold",
        "if both the calorie deficit and protein ratio",
    ]
    for phrase in forbidden:
        assert phrase not in lower, (
            f"Skill prose re-evaluates an R-rule: {phrase!r}. "
            f"Policy lives in policy.py; skill consumes ``policy_result``."
        )


def test_gate_1_no_mutation_verbs_in_skill():
    skill = _skill_text()
    lower = skill.lower()
    forbidden = [
        "apply x2",
        "apply x9",
        "apply the x-rule",
        "skill applies",
        "mutate the action",
        "override the action",
        "pre-bake x9",
    ]
    for phrase in forbidden:
        assert phrase not in lower, (
            f"Skill contains mutation-application prose: {phrase!r}. "
            f"Runtime owns X-rule application; skill owns rationale + "
            f"action-matrix only."
        )


# ---------------------------------------------------------------------------
# Gate 2 — honours forced_action + capped_confidence
# ---------------------------------------------------------------------------

def test_gate_2_skill_honours_forced_action_directly():
    skill = _skill_text()
    assert "forced_action" in skill
    lower = skill.lower()
    assert (
        "skip the action matrix" in lower
        or "short-circuit" in lower
        or "use it" in lower
    ), (
        "Skill must explicitly state that a set forced_action bypasses "
        "the action matrix."
    )


def test_gate_2_skill_honours_capped_confidence():
    skill = _skill_text()
    assert "capped_confidence" in skill
    lower = skill.lower()
    assert (
        "lowers but never raises" in lower
        or "never raises" in lower
        or "lowers the default" in lower
    ), (
        "Skill must describe the one-directional semantics of "
        "capped_confidence (lowers only)."
    )


# ---------------------------------------------------------------------------
# Gate 3 — emits only the NutritionProposal shape
# ---------------------------------------------------------------------------

def test_gate_3_skill_names_nutrition_proposal_schema():
    skill = _skill_text()
    assert "NutritionProposal" in skill, (
        "Skill output section must name the NutritionProposal schema so "
        "the agent knows which frozen shape to emit. (Synthesis turns "
        "proposals into recommendations; the skill itself does not emit "
        "a NutritionRecommendation.)"
    )
    assert "hai propose" in skill, (
        "Skill must route output through hai propose for validation + "
        "proposal_log persistence."
    )


def test_gate_3_skill_does_not_emit_recommendation_or_follow_up():
    """Proposals carry no ``follow_up`` and no ``daily_plan_id``. The
    skill must not instruct the agent to construct either — synthesis
    owns those fields."""

    skill = _skill_text()
    lower = skill.lower()
    # follow_up may appear in prose referencing "no follow_up" / "skip";
    # daily_plan_id must never appear outside the X9 discussion.
    if "daily_plan_id" in skill:
        # allow only in a short explanatory sentence; not as an
        # instruction to set it
        banned_daily_plan_prose = [
            "set daily_plan_id",
            "include daily_plan_id",
            "assign daily_plan_id",
        ]
        for phrase in banned_daily_plan_prose:
            assert phrase not in lower


def test_gate_3_skill_copies_policy_decisions_verbatim():
    skill = _skill_text()
    lower = skill.lower()
    assert (
        "policy_decisions" in skill
        and ("verbatim" in lower or "unchanged" in lower or "do not re-edit" in lower)
    ), (
        "Skill must copy policy_result.policy_decisions into the output "
        "verbatim — it is the runtime's audit record, not skill-editable."
    )


def test_gate_3_skill_lists_v1_action_enum():
    skill = _skill_text()
    v1_actions = [
        "maintain_targets",
        "increase_protein_intake",
        "increase_hydration",
        "reduce_calorie_deficit",
        "defer_decision_insufficient_signal",
        "escalate_for_user_review",
    ]
    present = [a for a in v1_actions if a in skill]
    assert len(present) >= 5, (
        f"Skill should name at least 5 of the 6 v1 nutrition actions; "
        f"found {len(present)}: {present}"
    )


def test_gate_3_skill_does_not_name_other_domain_action_enum():
    skill = _skill_text()
    foreign_actions = [
        "proceed_with_planned_session",
        "downgrade_hard_session_to_zone_2",
        "downgrade_session_to_mobility_only",
        "proceed_with_planned_run",
        "downgrade_intervals_to_tempo",
        "downgrade_to_easy_aerobic",
        "cross_train_instead",
        "sleep_debt_repayment_day",
        "earlier_bedtime_target",
        "prioritize_wind_down",
        "maintain_schedule",
        "downgrade_to_moderate_load",
        "downgrade_to_technique_or_accessory",
    ]
    leaked = [a for a in foreign_actions if a in skill]
    assert not leaked, (
        f"Skill names other-domain action(s) {leaked}. Nutrition has "
        f"its own v1 enum; do not cross the streams."
    )


# ---------------------------------------------------------------------------
# Gate 5 — no micronutrient-specific actions/prose (Phase 2.5 retrieval-gate)
# ---------------------------------------------------------------------------

def test_gate_5_skill_has_no_parametrised_micronutrient_actions():
    """The plan-text ``address_deficit_<micro>`` / ``reduce_<micro>``
    variants were collapsed out of the v1 enum — the data layer does
    not carry micronutrient evidence. The skill must not resurrect
    them in prose."""

    skill = _skill_text()
    lower = skill.lower()
    banned_actions = [
        "address_deficit_iron",
        "address_deficit_magnesium",
        "address_deficit_vitamin",
        "address_deficit_sodium",
        "address_deficit_calcium",
        "reduce_sodium",
        "reduce_sugar",
        "reduce_saturated_fat",
    ]
    for action in banned_actions:
        assert action not in skill and action not in lower, (
            f"Skill names micronutrient-specific action {action!r}. "
            f"The Phase 2.5 retrieval-gate outcome means the data layer "
            f"does not carry micronutrient evidence in v1 — there is no "
            f"honest classifier signal to back such an action."
        )


def test_gate_5_skill_forbids_micronutrient_rationale_claims():
    """No 'iron low,' no 'vitamin D inadequate,' no
    sodium-potassium ratio commentary."""

    skill = _skill_text()
    lower = skill.lower()
    forbidden_claims = [
        "iron low",
        "iron inadequate",
        "vitamin d inadequate",
        "vitamin d low",
        "sodium potassium ratio",
        "magnesium deficiency",
        "calcium deficiency",
        "fiber sufficiency",
    ]
    for claim in forbidden_claims:
        assert claim not in lower, (
            f"Skill prose claims micronutrient status {claim!r} but the "
            f"data layer does not carry that evidence in v1."
        )


# ---------------------------------------------------------------------------
# Gate 6 — skill surfaces micronutrient unavailability honestly
# ---------------------------------------------------------------------------

def test_gate_6_skill_references_unavailable_at_source_for_micros():
    skill = _skill_text()
    assert "unavailable_at_source" in skill, (
        "Skill must surface the honest ``unavailable_at_source`` token "
        "for micronutrient coverage so silence is not misread as "
        "alignment."
    )
    assert "micronutrient" in skill.lower(), (
        "Skill must name the micronutrient-coverage limitation in prose "
        "so a reader knows v1 speaks only to macros + hydration."
    )


# ---------------------------------------------------------------------------
# Gate 7 — X9 is runtime-owned; skill must not pre-bake it
# ---------------------------------------------------------------------------

def test_gate_7_skill_explains_x9_as_runtime_owned():
    skill = _skill_text()
    lower = skill.lower()
    assert "x9" in lower, (
        "Skill must reference X9 so the agent understands that a training-"
        "intensity bump appears in the final recommendation's "
        "action_detail — not in the proposal the skill emits."
    )
    assert "runtime" in lower or "downstream" in lower, (
        "Skill must describe X9 as runtime-owned / downstream so the "
        "skill does not try to anticipate its effect."
    )
    # And explicitly — don't tell the agent to anticipate X9.
    forbidden_prebake = [
        "anticipate x9",
        "bake x9",
        "apply x9 yourself",
        "include x9's adjustment",
    ]
    for phrase in forbidden_prebake:
        assert phrase not in lower


# ---------------------------------------------------------------------------
# Frontmatter shape
# ---------------------------------------------------------------------------

def test_skill_frontmatter_declares_name_and_allowed_tools():
    skill = _skill_text()
    assert skill.startswith("---"), "skill must open with YAML frontmatter"
    header = skill.split("---", 2)[1]
    assert "name: nutrition-alignment" in header
    assert "allowed-tools:" in header
    assert "hai propose" in header, (
        "allowed-tools must include hai propose so the skill can persist "
        "its output without a free-form Bash call."
    )
