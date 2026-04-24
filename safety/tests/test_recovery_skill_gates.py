"""Phase 1 rewrite contract tests for `skills/recovery-readiness/SKILL.md`.

Four gates the rewrite was held to:

1. The skill consumes `classified_state` and `policy_result`. No
   arithmetic, no rule evaluation, no mutation logic in markdown.
2. It honours `forced_action` and `capped_confidence` directly.
3. It emits only the frozen `TrainingRecommendation` shape.
4. It is under 100 lines without hiding determinism in prose.

Each test locks one gate so regressions during Phase 2+ (when the skill
might tempt us to fold new logic back in) fail fast.
"""

from __future__ import annotations

import re
from importlib.resources import files


def _skill_text() -> str:
    return files("health_agent_infra").joinpath(
        "skills", "recovery-readiness", "SKILL.md"
    ).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Gate 4 — under 100 lines
# ---------------------------------------------------------------------------

def test_gate_4_skill_under_100_lines():
    lines = _skill_text().splitlines()
    assert len(lines) < 100, (
        f"recovery-readiness SKILL.md is {len(lines)} lines; the Phase 1 "
        f"contract caps it at <100. Move determinism to code, not prose."
    )


# ---------------------------------------------------------------------------
# Gate 1 — consumes classified_state + policy_result; no arithmetic in markdown
# ---------------------------------------------------------------------------

def test_gate_1_skill_references_classified_state_and_policy_result():
    skill = _skill_text()
    assert "classified_state" in skill, (
        "Skill must consume classified_state (the runtime-computed bands + "
        "status + score + uncertainty). If it's absent, the skill is doing "
        "its own arithmetic."
    )
    assert "policy_result" in skill, (
        "Skill must consume policy_result (the runtime-evaluated R-rules). "
        "If it's absent, the skill is evaluating policy in prose."
    )


def test_gate_1_skill_names_classified_state_as_source_of_truth():
    skill = _skill_text()
    # Case-insensitive match lets us tolerate light rewording. We pin the
    # invariant that the skill explicitly does not re-derive bands.
    lower = skill.lower()
    assert "source of truth" in lower, (
        "Skill must explicitly name classified_state (and policy_result) as "
        "the source of truth so a reader cannot mistake the skill for the "
        "arithmetic layer."
    )


def test_gate_1_no_band_threshold_numbers_in_skill_prose():
    """Band-boundary thresholds (7.5h sleep, 1.15 RHR ratio, 1.4 load spike,
    etc.) live in `core/config.py`. If they appear in the skill prose the
    skill is duplicating — and drifting from — the classifier.
    """

    skill = _skill_text()
    # Numbers that were baked into the 315-line version and must NOT be
    # duplicated here. Match on digit boundaries to avoid false positives
    # on line numbers or anchors.
    banned_thresholds = [
        r"\b7\.5\b",         # sleep_debt_band none_min_hours
        r"\b1\.15\b",        # resting_hr well_above_ratio
        r"\b1\.05\b",        # resting_hr above_ratio
        r"\b0\.95\b",        # at_lower_ratio / hrv_below_max_ratio
        r"\b1\.02\b",        # hrv_above_min_ratio
        r"\b1\.10\b",        # hrv_well_above
        r"\b1\.40\b", r"\b1\.4\b",     # training_load spike_ratio
        r"\b0\.25\b",        # readiness_score sleep_debt_elevated penalty
        r"\b0\.15\b",        # readiness_score sleep_debt_moderate penalty
    ]
    for pattern in banned_thresholds:
        matches = re.findall(pattern, skill)
        assert not matches, (
            f"Skill prose contains banned threshold {pattern!r}: "
            f"{matches}. Thresholds belong in core/config.py, not markdown."
        )


def test_gate_1_no_readiness_score_arithmetic_in_skill():
    """The 315-line version had a full penalty table. The rewrite must
    reference readiness_score only as an already-computed field.
    """

    skill = _skill_text()
    lower = skill.lower()
    # Phrases that indicate penalty-table arithmetic.
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


def test_gate_1_no_mutation_verbs_in_skill():
    """Codex round-2: skills do not own mutation logic. Runtime applies
    X-rule mutations; skill only writes rationale for an already-fixed
    action. Verbs that suggest a skill applies a mutation are banned.
    """

    skill = _skill_text()
    lower = skill.lower()
    # Phrases associated with skill-applied mutation (the anti-pattern).
    forbidden = [
        "apply x1",          # "apply X1a / X1b ..."
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
        "Skill must reference policy_result.forced_action. Without it, the "
        "skill would re-evaluate R1 / R6 and could disagree with the "
        "runtime's authoritative decision."
    )
    # The skill must state it short-circuits the action matrix on a
    # forced action — otherwise the force is cosmetic.
    lower = skill.lower()
    assert (
        "skip the action matrix" in lower
        or "short-circuit" in lower
        or "use it" in lower
    ), (
        "Skill must explicitly state that a set forced_action bypasses the "
        "action matrix — otherwise the runtime's block/escalate decisions "
        "can be overridden by skill judgment."
    )


def test_gate_2_skill_honours_capped_confidence():
    skill = _skill_text()
    assert "capped_confidence" in skill, (
        "Skill must reference policy_result.capped_confidence. Without it, "
        "R5's sparse-signal cap is invisible to the skill and confidence "
        "can escape its ceiling."
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
# Gate 3 — emits only the frozen RecoveryProposal shape via `hai propose`
# ---------------------------------------------------------------------------
#
# Pre-D2 this gate asserted TrainingRecommendation + `hai writeback`. The
# v0.1.4 D2 contract unified the six domain skills around `hai propose`;
# the recovery-readiness SKILL.md was rewritten to match. See
# reporting/plans/v0_1_4/D2_intake_write_paths.md.

def test_gate_3_skill_names_recovery_proposal_schema():
    skill = _skill_text()
    assert "RecoveryProposal" in skill, (
        "Skill output section must name the RecoveryProposal schema "
        "so the agent knows which frozen shape to emit."
    )
    assert "hai propose" in skill, (
        "Skill must route output through hai propose for validation "
        "(the legacy hai writeback path was retired in v0.1.4 D2)."
    )
    assert "hai writeback" not in skill, (
        "Skill must not instruct agents to use the retired hai writeback "
        "command. Retired in v0.1.4 D2."
    )


def test_gate_3_skill_copies_policy_decisions_verbatim():
    """`policy_decisions` comes from the runtime; the skill must pass it
    through unchanged. Editing or adding new rows invalidates the audit
    chain.
    """

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
    """The action field is constrained. The skill either (a) enumerates the
    enum inline, or (b) refers to ``hai writeback``'s validation as the
    gate. Both are acceptable; what's NOT acceptable is vague language
    that leaves the enum ambiguous.
    """

    skill = _skill_text()
    # Required: at least 4 of the 6 v1 actions named in the skill. Full
    # set: proceed_with_planned_session, downgrade_hard_session_to_zone_2,
    # downgrade_session_to_mobility_only, rest_day_recommended,
    # defer_decision_insufficient_signal, escalate_for_user_review.
    v1_actions = [
        "proceed_with_planned_session",
        "downgrade_hard_session_to_zone_2",
        "downgrade_session_to_mobility_only",
        "rest_day_recommended",
        "defer_decision_insufficient_signal",
        "escalate_for_user_review",
    ]
    present = [a for a in v1_actions if a in skill]
    assert len(present) >= 4, (
        f"Skill should name at least 4 of the 6 v1 actions; found "
        f"{len(present)}: {present}"
    )


# ---------------------------------------------------------------------------
# Invariants section present (the skill's own guardrails)
# ---------------------------------------------------------------------------

def test_skill_includes_invariants_section():
    """The rewrite explicitly records invariants the skill must hold.
    Without them, a future edit could silently violate the gates.
    """

    skill = _skill_text()
    assert "## Invariants" in skill or "# Invariants" in skill, (
        "Skill must have an Invariants section recording its contractual "
        "guarantees (no arithmetic, no rule evaluation, no mutation, "
        "bounded action enum, no fabrication)."
    )
