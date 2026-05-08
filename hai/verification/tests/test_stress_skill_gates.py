"""Phase 3 step 4 contract tests for ``skills/stress-regulation/SKILL.md``.

Mirrors the four gates enforced on the recovery-readiness,
running-readiness, and sleep-quality skills:

  1. The skill consumes ``classified_state`` and ``policy_result``. No
     band arithmetic, no R-rule evaluation, no mutation logic in prose.
  2. It honours ``forced_action`` and ``capped_confidence`` directly.
  3. It emits only the ``StressProposal`` shape (stress's pre-synthesis
     write surface — no follow_up, no daily_plan_id).
  4. It is under 100 lines.

Locks the contract before step 5 wires stress into snapshot + synthesis
so markdown cannot silently reabsorb deterministic logic.
"""

from __future__ import annotations

import re
from importlib.resources import files


def _skill_text() -> str:
    return files("health_agent_infra").joinpath(
        "skills", "stress-regulation", "SKILL.md"
    ).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Gate 4 — under 100 lines
# ---------------------------------------------------------------------------

def test_gate_4_skill_under_100_lines():
    lines = _skill_text().splitlines()
    assert len(lines) < 100, (
        f"stress-regulation SKILL.md is {len(lines)} lines; the Phase 3 "
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
    """Band-boundary thresholds (garmin 40/60/80, manual 3/4/5, body
    battery depleted 20 / declining -10 / steady 10, penalties
    0.05/0.10/0.15/0.20/0.25/0.30/0.02, sustained-stress 5/60) live in
    ``core/config.py``. If they appear in the skill prose the skill is
    duplicating — and drifting from — the classifier / policy."""

    skill = _skill_text()
    banned_thresholds = [
        # garmin_stress_band boundaries
        r"\b40\b",
        # 60 and 80 are also the body-battery "depleted" detail values
        # and other small ints used incidentally in prose. Ban the
        # less-ambiguous 40 / manual 1-5 mapping prose instead.
        # manual_stress_band score-to-band mapping
        r"1-2\s*low",
        r"\b3\s*=\s*moderate\b",
        r"\b4\s*=\s*high\b",
        r"\b5\s*=\s*very",
        # penalty table
        r"\b0\.05\b",
        r"\b0\.10\b",
        r"\b0\.15\b",
        r"\b0\.20\b",
        r"\b0\.25\b",
        r"\b0\.30\b",
        # sustained-stress days threshold
        r"\bfive days\b",
        r"\b5 days\b",
        r"\b5 consecutive\b",
    ]
    for pattern in banned_thresholds:
        matches = re.findall(pattern, skill, flags=re.IGNORECASE)
        assert not matches, (
            f"Skill prose contains banned threshold {pattern!r}: "
            f"{matches}. Thresholds belong in core/config.py, not markdown."
        )


def test_gate_1_no_delta_arithmetic_in_skill():
    """The skill must reference body_battery_delta only as an
    already-computed field. No formulas for today - prev."""

    skill = _skill_text()
    lower = skill.lower()
    forbidden_phrases = [
        "today_bb - prev",
        "today - prev",
        "bb_end_of_day - prev",
        "delta = ",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lower, (
            f"Skill prose contains delta arithmetic: {phrase!r}. "
            f"Delta computation lives in classify.py, not markdown."
        )


def test_gate_1_no_stress_score_arithmetic_in_skill():
    """The skill must reference stress_score only as an already-computed
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
            f"Skill prose contains stress-score arithmetic: {phrase!r}. "
            f"Scoring lives in classify.py, not markdown."
        )


def test_gate_1_no_rule_evaluation_in_skill():
    """The skill must not re-state R-rule logic. Policy firings come
    through ``policy_result``; skill does not second-guess them."""

    skill = _skill_text()
    lower = skill.lower()
    forbidden = [
        "count consecutive days",
        "count how many days",
        "if coverage is insufficient, return",
        "if coverage is sparse, cap",
        "count days above",
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
        "apply x6",
        "apply x7",
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
# Gate 3 — emits only the StressProposal shape
# ---------------------------------------------------------------------------

def test_gate_3_skill_names_stress_proposal_schema():
    skill = _skill_text()
    assert "StressProposal" in skill, (
        "Skill output section must name the StressProposal schema so "
        "the agent knows which frozen shape to emit. (Synthesis turns "
        "proposals into recommendations; the skill itself does not emit "
        "a StressRecommendation.)"
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
    """The action field is constrained to the v1 stress enum. The skill
    must name at least 4 of the 5 actions so the contract is explicit
    in markdown."""

    skill = _skill_text()
    v1_actions = [
        "maintain_routine",
        "add_low_intensity_recovery",
        "schedule_decompression_time",
        "escalate_for_user_review",
        "defer_decision_insufficient_signal",
    ]
    present = [a for a in v1_actions if a in skill]
    assert len(present) >= 4, (
        f"Skill should name at least 4 of the 5 v1 stress actions; "
        f"found {len(present)}: {present}"
    )


def test_gate_3_skill_does_not_name_other_domain_action_enum():
    """Stress has its own v1 enum. Naming recovery, running, or sleep
    actions suggests the skill is crossing domain boundaries."""

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
        "maintain_schedule",
        "prioritize_wind_down",
        "sleep_debt_repayment_day",
        "earlier_bedtime_target",
    ]
    leaked = [a for a in foreign_actions if a in skill]
    assert not leaked, (
        f"Skill names other-domain action(s) {leaked}. Stress has its "
        f"own v1 enum; do not cross the streams."
    )


# ---------------------------------------------------------------------------
# Gate 1' — stress-specific signal references
# ---------------------------------------------------------------------------

def test_skill_references_stress_band_names():
    """The skill must name the stress classifier's band fields so a
    rename in classify.py surfaces in this contract test, not at agent
    prompt time."""

    skill = _skill_text()
    required_band_names = [
        "garmin_stress_band",
        "manual_stress_band",
        "body_battery_trend_band",
        "stress_state",
    ]
    missing = [b for b in required_band_names if b not in skill]
    assert not missing, (
        f"Skill is missing band-name references: {missing}. The skill's "
        f"contract is to consume these by name."
    )


def test_skill_references_stress_signal_keys():
    """The signals dict is the runtime's bridge to the classifier. The
    skill must name at least a few signal keys so a rename would fail
    this test rather than silently break the agent's read."""

    skill = _skill_text()
    signal_keys = [
        "garmin_all_day_stress",
        "manual_stress_score",
        "body_battery_end_of_day",
        "body_battery_prev_day",
        "stress_history_garmin_last_7",
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
