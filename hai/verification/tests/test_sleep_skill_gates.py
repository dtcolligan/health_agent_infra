"""Phase 3 step 3 contract tests for ``skills/sleep-quality/SKILL.md``.

Mirrors the four gates enforced on the recovery-readiness and
running-readiness skills:

  1. The skill consumes ``classified_state`` and ``policy_result``. No
     band arithmetic, no R-rule evaluation, no mutation logic in prose.
  2. It honours ``forced_action`` and ``capped_confidence`` directly.
  3. It emits only the ``SleepProposal`` shape (sleep's pre-synthesis
     write surface — no follow_up, no daily_plan_id).
  4. It is under 100 lines.

Locks the contract before step 5 wires sleep into snapshot + synthesis
so markdown cannot silently reabsorb deterministic logic.
"""

from __future__ import annotations

import re
from importlib.resources import files


def _skill_text() -> str:
    return files("health_agent_infra").joinpath(
        "skills", "sleep-quality", "SKILL.md"
    ).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Gate 4 — under 100 lines
# ---------------------------------------------------------------------------

def test_gate_4_skill_under_100_lines():
    lines = _skill_text().splitlines()
    assert len(lines) < 100, (
        f"sleep-quality SKILL.md is {len(lines)} lines; the Phase 3 "
        f"contract caps it at <100. Move determinism to code, not prose."
    )


# ---------------------------------------------------------------------------
# Gate 1 — consumes classified_state + policy_result; no arithmetic in markdown
# ---------------------------------------------------------------------------

def test_gate_1_skill_references_classified_state_and_policy_result():
    skill = _skill_text()
    assert "classified_state" in skill, (
        "Skill must consume classified_state. Without it, the skill is "
        "doing its own band arithmetic."
    )
    assert "policy_result" in skill, (
        "Skill must consume policy_result. Without it, the skill is "
        "evaluating R-rules in prose."
    )


def test_gate_1_skill_names_classified_state_as_source_of_truth():
    skill = _skill_text()
    lower = skill.lower()
    assert "source of truth" in lower, (
        "Skill must explicitly name classified_state (and policy_result) "
        "as the source of truth so a reader cannot mistake the skill for "
        "the arithmetic layer."
    )


def test_gate_1_no_band_threshold_numbers_in_skill_prose():
    """Band-boundary thresholds (sleep_debt 7.5/7.0/6.0, quality
    90/80/60, efficiency 90/85/75, consistency 30/60, penalties
    0.05/0.15/0.25/0.20/0.10/0.02/0.08, chronic-deprivation 4/6.0) live
    in ``core/config.py``. If they appear in the skill prose the skill
    is duplicating — and drifting from — the classifier / policy."""

    skill = _skill_text()
    banned_thresholds = [
        # sleep_debt_band boundaries
        r"\b7\.5\b",
        r"\b7\.0\b",
        r"\b6\.0\b",
        # sleep_quality_band boundaries (Garmin 0-100 scale)
        r"\b90\b",
        r"\b80\b",
        r"\b60\b",
        # sleep_efficiency_band boundaries
        r"\b85\b",
        r"\b75\b",
        # sleep_timing_consistency_band boundaries (stddev minutes).
        # 30 is also the target_shift_minutes detail value — the skill
        # legitimately surfaces that as action_detail. Don't ban it;
        # ban the less-ambiguous 60-min stddev boundary instead.
        # r"\b30\b",  # intentionally skipped — see above.
        # readiness_score penalties
        r"\b0\.05\b",
        r"\b0\.15\b",
        r"\b0\.25\b",
        r"\b0\.20\b",
        r"\b0\.10\b",
        r"\b0\.02\b",
        r"\b0\.08\b",
        # chronic-deprivation nights threshold
        r"\bfour nights\b",
        r"\b4 nights\b",
    ]
    for pattern in banned_thresholds:
        matches = re.findall(pattern, skill, flags=re.IGNORECASE)
        assert not matches, (
            f"Skill prose contains banned threshold {pattern!r}: "
            f"{matches}. Thresholds belong in core/config.py, not markdown."
        )


def test_gate_1_no_efficiency_arithmetic_in_skill():
    """The skill must reference sleep_efficiency_pct only as an
    already-computed field. No formulas for asleep / (asleep + awake)."""

    skill = _skill_text()
    lower = skill.lower()
    forbidden_phrases = [
        "asleep / (asleep",
        "sleep_hours * 60",
        "asleep_min / ",
        "divide by total in bed",
        "efficiency = ",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lower, (
            f"Skill prose contains efficiency arithmetic: {phrase!r}. "
            f"Efficiency computation lives in classify.py, not markdown."
        )


def test_gate_1_no_sleep_score_arithmetic_in_skill():
    """The skill must reference sleep_score only as an already-computed
    field. No penalty tables, no clamping prose, no scoring formulas."""

    skill = _skill_text()
    lower = skill.lower()
    forbidden_phrases = [
        "start at 1.0",
        "subtract from score",
        "add to score",
        "clamp to [0.0, 1.0]",
        "penalty (subtract",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lower, (
            f"Skill prose contains sleep-score arithmetic: {phrase!r}. "
            f"Scoring lives in classify.py, not markdown."
        )


def test_gate_1_no_rule_evaluation_in_skill():
    """The skill must not re-state R-rule logic. Policy firings come
    through ``policy_result``; skill does not second-guess them."""

    skill = _skill_text()
    lower = skill.lower()
    forbidden = [
        "count nights under",
        "at least 4 of the last 7",
        "count how many nights",
        "if coverage is insufficient, return",
        "if coverage is sparse, cap",
    ]
    for phrase in forbidden:
        assert phrase not in lower, (
            f"Skill prose re-evaluates an R-rule: {phrase!r}. "
            f"Policy lives in policy.py; skill consumes ``policy_result``."
        )


def test_gate_1_no_mutation_verbs_in_skill():
    """Skills do not own mutation logic. Runtime applies X-rule
    mutations; skill only writes rationale for an already-fixed action."""

    skill = _skill_text()
    lower = skill.lower()
    forbidden = [
        "apply x1",
        "apply x6",
        "apply the x-rule",
        "apply any x-rule",
        "skill applies",
        "mutate the action",
        "override the action",
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
    assert "forced_action" in skill, (
        "Skill must reference policy_result.forced_action. Without it, "
        "the skill would re-evaluate the R-rules and could disagree with "
        "the runtime's authoritative decision."
    )
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
    assert "capped_confidence" in skill, (
        "Skill must reference policy_result.capped_confidence. Without "
        "it, the sparse-signal cap is invisible to the skill."
    )
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
# Gate 3 — emits only the SleepProposal shape
# ---------------------------------------------------------------------------

def test_gate_3_skill_names_sleep_proposal_schema():
    skill = _skill_text()
    assert "SleepProposal" in skill, (
        "Skill output section must name the SleepProposal schema so "
        "the agent knows which frozen shape to emit. (Synthesis turns "
        "proposals into recommendations; the skill itself does not emit "
        "a SleepRecommendation.)"
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
    assert "follow_up" not in skill or "no follow_up" in lower or (
        "skip this step" in lower
    ), (
        "Skill must NOT instruct the agent to construct a follow_up — "
        "proposals carry none; reviews schedule from finalised "
        "recommendations after synthesis."
    )
    assert "daily_plan_id" not in skill, (
        "Skill must not mention daily_plan_id; synthesis assigns it."
    )


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


def test_gate_3_skill_lists_v1_action_enum_directly_or_references_it():
    """The action field is constrained to the v1 sleep enum. The skill
    must name at least 4 of the 5 actions so the contract is explicit
    in markdown."""

    skill = _skill_text()
    v1_actions = [
        "maintain_schedule",
        "prioritize_wind_down",
        "sleep_debt_repayment_day",
        "earlier_bedtime_target",
        "defer_decision_insufficient_signal",
    ]
    present = [a for a in v1_actions if a in skill]
    assert len(present) >= 4, (
        f"Skill should name at least 4 of the 5 v1 sleep actions; "
        f"found {len(present)}: {present}"
    )


def test_gate_3_skill_does_not_name_other_domain_action_enum():
    """Sleep has its own v1 enum. Naming recovery or running actions
    suggests the skill is crossing domain boundaries."""

    skill = _skill_text()
    foreign_actions = [
        "proceed_with_planned_session",
        "downgrade_hard_session_to_zone_2",
        "downgrade_session_to_mobility_only",
        "rest_day_recommended",
        "proceed_with_planned_run",
        "downgrade_intervals_to_tempo",
        "downgrade_to_easy_aerobic",
        "cross_train_instead",
    ]
    leaked = [a for a in foreign_actions if a in skill]
    assert not leaked, (
        f"Skill names other-domain action(s) {leaked}. Sleep has its "
        f"own v1 enum; do not cross the streams."
    )


def test_gate_3_skill_does_not_name_escalate_for_user_review():
    """Sleep's v1 enum omits ``escalate_for_user_review``. The skill
    must not instruct the agent to emit that action even under
    chronic-deprivation escalation — the remedial
    ``sleep_debt_repayment_day`` is the correct forced action; severity
    lives in the policy_decision tier."""

    skill = _skill_text()
    assert "escalate_for_user_review" not in skill, (
        "Skill must not name ``escalate_for_user_review`` — it is not "
        "in sleep's v1 action enum. Chronic-deprivation escalation "
        "forces ``sleep_debt_repayment_day`` with the severity carried "
        "by the ``escalate`` policy_decision tier."
    )


# ---------------------------------------------------------------------------
# Gate 1' — sleep-specific signal references
# ---------------------------------------------------------------------------

def test_skill_references_sleep_band_names():
    """The skill must name the sleep classifier's band fields so a
    rename in classify.py surfaces in this contract test, not at agent
    prompt time."""

    skill = _skill_text()
    required_band_names = [
        "sleep_debt_band",
        "sleep_quality_band",
        "sleep_timing_consistency_band",
        "sleep_efficiency_band",
        "sleep_status",
    ]
    missing = [b for b in required_band_names if b not in skill]
    assert not missing, (
        f"Skill is missing band-name references: {missing}. The skill's "
        f"contract is to consume these by name."
    )


def test_skill_references_sleep_signal_keys():
    """The signals dict is the runtime's bridge to the classifier. The
    skill must name at least a few signal keys so a rename would fail
    this test rather than silently break the agent's read."""

    skill = _skill_text()
    signal_keys = [
        "sleep_hours",
        "sleep_score_overall",
        "sleep_awake_min",
        "sleep_start_variance_minutes",
        "sleep_history_hours_last_7",
    ]
    present = [k for k in signal_keys if k in skill]
    assert len(present) >= 3, (
        f"Skill should reference at least 3 of the 5 signal keys; "
        f"found {len(present)}: {present}"
    )


# ---------------------------------------------------------------------------
# Invariants section present
# ---------------------------------------------------------------------------

def test_skill_includes_invariants_section():
    skill = _skill_text()
    assert "## Invariants" in skill or "# Invariants" in skill, (
        "Skill must have an Invariants section recording its contractual "
        "guarantees."
    )
