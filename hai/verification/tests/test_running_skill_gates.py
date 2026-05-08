"""Phase 2 step 3 contract tests for ``skills/running-readiness/SKILL.md``.

Mirrors the four gates that ``test_recovery_skill_gates.py`` enforces on
the recovery-readiness skill:

  1. The skill consumes ``classified_state`` and ``policy_result``. No
     band arithmetic, no R-rule evaluation, no mutation logic in markdown.
  2. It honours ``forced_action`` and ``capped_confidence`` directly.
  3. It emits only the ``RunningProposal`` shape (running's pre-synthesis
     write surface — no follow_up, no daily_plan_id).
  4. It is under 100 lines.

Locks the contract before synthesis activation in step 4 starts asking
the skill harder questions.
"""

from __future__ import annotations

import re
from importlib.resources import files


def _skill_text() -> str:
    return files("health_agent_infra").joinpath(
        "skills", "running-readiness", "SKILL.md"
    ).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Gate 4 — under 100 lines
# ---------------------------------------------------------------------------

def test_gate_4_skill_under_100_lines():
    lines = _skill_text().splitlines()
    assert len(lines) < 100, (
        f"running-readiness SKILL.md is {len(lines)} lines; the Phase 2 "
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
    """Band-boundary thresholds (mileage 0.5/0.8/1.2/1.5, ACWR 1.3/1.5,
    training_readiness 70/40, score penalties 0.05/0.15/0.30) live in
    ``core/config.py``. If they appear in the skill prose the skill is
    duplicating — and drifting from — the classifier.
    """

    skill = _skill_text()
    banned_thresholds = [
        # weekly_mileage_trend_band boundaries
        r"\b0\.5\b",
        r"\b0\.8\b",
        r"\b1\.2\b",
        # freshness_band boundaries (overlap with X3a/X3b)
        r"\b1\.3\b",
        r"\b1\.5\b",
        # recovery_adjacent thresholds
        r"\b70\b",
        r"\b40\b",
        # readiness_score penalties
        r"\b0\.05\b",
        r"\b0\.15\b",
        r"\b0\.30\b",
        r"\b0\.20\b",
        r"\b0\.02\b",
        # hard-session vigorous threshold (signals.py constant)
        r"\b30\b",
    ]
    for pattern in banned_thresholds:
        matches = re.findall(pattern, skill)
        assert not matches, (
            f"Skill prose contains banned threshold {pattern!r}: "
            f"{matches}. Thresholds belong in core/config.py and "
            f"signals.py, not markdown."
        )


def test_gate_1_no_readiness_score_arithmetic_in_skill():
    """The skill must reference readiness_score only as an already-computed
    field. No penalty tables, no clamping prose, no scoring formulas.
    """

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
            f"Skill prose contains readiness-score arithmetic: {phrase!r}. "
            f"Scoring lives in classify.py, not markdown."
        )


def test_gate_1_no_signal_aggregation_in_skill():
    """signals.py owns weekly mileage summing, baseline scaling, and hard-
    session counting. The skill must not describe how those numbers are
    derived — only consume them as ``signals.<name>`` reads.
    """

    skill = _skill_text()
    lower = skill.lower()
    forbidden_phrases = [
        "sum of",
        "trailing 28",
        "trailing 4 weeks",
        "trailing-week mean",
        "scale by",
        "divided by",
        "average over",
        "count of days",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lower, (
            f"Skill prose describes signal aggregation: {phrase!r}. "
            f"That logic lives in signals.py; the skill consumes the "
            f"derived ``signals`` block as-is."
        )


def test_gate_1_no_mutation_verbs_in_skill():
    """Skills do not own mutation logic. Runtime applies X-rule mutations;
    skill only writes rationale for an already-fixed action.
    """

    skill = _skill_text()
    lower = skill.lower()
    forbidden = [
        "apply x1",
        "apply x3",
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
        "the action matrix — otherwise the runtime's block/escalate "
        "decisions can be overridden by skill judgment."
    )


def test_gate_2_skill_honours_capped_confidence():
    skill = _skill_text()
    assert "capped_confidence" in skill, (
        "Skill must reference policy_result.capped_confidence. Without "
        "it, the sparse-signal cap is invisible to the skill and "
        "confidence can escape its ceiling."
    )
    lower = skill.lower()
    assert (
        "lowers but never raises" in lower
        or "never raises" in lower
        or "lowers the default" in lower
    ), (
        "Skill must describe the one-directional semantics of "
        "capped_confidence (lowers only), so a future rewrite doesn't "
        "accidentally treat it as a floor."
    )


# ---------------------------------------------------------------------------
# Gate 3 — emits only the RunningProposal shape
# ---------------------------------------------------------------------------

def test_gate_3_skill_names_running_proposal_schema():
    skill = _skill_text()
    assert "RunningProposal" in skill, (
        "Skill output section must name the RunningProposal schema so "
        "the agent knows which frozen shape to emit. (Synthesis turns "
        "proposals into recommendations; the skill itself does not emit "
        "a RunningRecommendation.)"
    )
    assert "hai propose" in skill, (
        "Skill must route output through hai propose for validation + "
        "proposal_log persistence (Phase 2 step 4)."
    )


def test_gate_3_skill_does_not_emit_recommendation_or_follow_up():
    """Proposals carry no ``follow_up`` and no ``daily_plan_id``. The
    skill must not instruct the agent to construct either — synthesis
    owns those fields.
    """

    skill = _skill_text()
    lower = skill.lower()
    # The skill MAY mention "RunningRecommendation" only in a guarding
    # context (e.g. "synthesis emits a recommendation, not the skill").
    # Stricter: the skill must not give the agent a recipe for
    # constructing one.
    assert "follow_up" not in skill or "no follow_up" in lower or (
        "skip this step" in lower
    ), (
        "Skill must NOT instruct the agent to construct a follow_up — "
        "proposals carry none; reviews schedule from finalised "
        "recommendations after synthesis."
    )
    # daily_plan_id is assigned by synthesis.
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
    """The action field is constrained to the v1 running enum. The skill
    must name at least 4 of the 7 actions so the contract is explicit
    in markdown.
    """

    skill = _skill_text()
    v1_actions = [
        "proceed_with_planned_run",
        "downgrade_intervals_to_tempo",
        "downgrade_to_easy_aerobic",
        "cross_train_instead",
        "rest_day_recommended",
        "defer_decision_insufficient_signal",
        "escalate_for_user_review",
    ]
    present = [a for a in v1_actions if a in skill]
    assert len(present) >= 4, (
        f"Skill should name at least 4 of the 7 v1 running actions; "
        f"found {len(present)}: {present}"
    )


def test_gate_3_skill_does_not_name_recovery_action_enum():
    """Running has its own v1 enum. Naming a recovery-only action (e.g.
    ``downgrade_hard_session_to_zone_2``) suggests the skill is reusing
    recovery's matrix; the writeback layer would reject it.
    """

    skill = _skill_text()
    recovery_only_actions = [
        "downgrade_hard_session_to_zone_2",
        "downgrade_session_to_mobility_only",
        "proceed_with_planned_session",  # recovery's analogue of proceed_with_planned_run
    ]
    leaked = [a for a in recovery_only_actions if a in skill]
    assert not leaked, (
        f"Skill names recovery-only action(s) {leaked}. Running has its "
        f"own v1 enum; do not cross the streams."
    )


# ---------------------------------------------------------------------------
# Gate 1' — running-specific signal references
# ---------------------------------------------------------------------------

def test_skill_references_running_band_names():
    """The skill must name the running classifier's band fields so a
    rename in classify.py surfaces in this contract test, not at agent
    prompt time.
    """

    skill = _skill_text()
    required_band_names = [
        "weekly_mileage_trend_band",
        "hard_session_load_band",
        "freshness_band",
        "recovery_adjacent_band",
        "running_readiness_status",
    ]
    missing = [b for b in required_band_names if b not in skill]
    assert not missing, (
        f"Skill is missing band-name references: {missing}. The skill's "
        f"contract is to consume these by name."
    )


def test_skill_references_running_signal_keys():
    """The signals dict is the runtime's bridge to the classifier. The
    skill must name at least one signal key (even just to say "consume
    via signals.<name>") so a renamed key would fail this test rather
    than silently break the agent's read.
    """

    skill = _skill_text()
    signal_keys = [
        "weekly_mileage_m",
        "weekly_mileage_baseline_m",
        "recent_hard_session_count_7d",
        "acwr_ratio",
        "training_readiness_pct",
        "sleep_debt_band",
        "resting_hr_band",
    ]
    present = [k for k in signal_keys if k in skill]
    assert len(present) >= 4, (
        f"Skill should reference at least 4 of the 7 signal keys; "
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
