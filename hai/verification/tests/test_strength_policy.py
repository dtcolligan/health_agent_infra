"""Strength-domain R-rule policy tests (Phase 4 step 3).

Pins:

  1. ``require_min_coverage`` blocks + forces
     ``defer_decision_insufficient_signal`` iff ``coverage=insufficient``.
  2. ``no_high_confidence_on_sparse_signal`` softens + caps confidence
     to ``moderate`` iff ``coverage=sparse``.
  3. ``volume_spike_escalation`` escalates + forces
     ``escalate_for_user_review`` iff ``volume_ratio >=
     r_volume_spike_min_ratio``. Overrides an earlier R-coverage defer.
  4. ``unmatched_exercise_confidence_cap`` softens + caps confidence
     to ``moderate`` iff unmatched exercise tokens are present.
  5. Rule ordering: R-coverage and R-volume-spike both speak to
     action selection; R-sparse and R-unmatched only cap confidence.
     R-volume-spike wins over R-coverage when both would force an
     action.
"""

from __future__ import annotations

from typing import Optional

import pytest

from health_agent_infra.domains.strength.classify import (
    ClassifiedStrengthState,
)
from health_agent_infra.domains.strength.policy import (
    evaluate_strength_policy,
)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _state(
    *,
    coverage: str = "full",
    volume_ratio: Optional[float] = 1.0,
    unmatched: tuple[str, ...] = (),
) -> ClassifiedStrengthState:
    return ClassifiedStrengthState(
        recent_volume_band="moderate",
        freshness_band_by_group={"quads": "fresh"},
        coverage_band=coverage,
        strength_status="maintaining",
        strength_score=0.9,
        volume_ratio=volume_ratio,
        sessions_last_7d=3,
        sessions_last_28d=12,
        unmatched_exercise_tokens=unmatched,
        uncertainty=(),
    )


def _decisions_by_rule(result):
    return {d.rule_id: d for d in result.policy_decisions}


# ---------------------------------------------------------------------------
# R-coverage gate
# ---------------------------------------------------------------------------

def test_coverage_insufficient_blocks_and_forces_defer():
    state = _state(coverage="insufficient")
    result = evaluate_strength_policy(state)

    by_rule = _decisions_by_rule(result)
    cov = by_rule["require_min_coverage"]
    assert cov.decision == "block"
    assert result.forced_action == "defer_decision_insufficient_signal"


def test_coverage_allow_when_full_or_partial_or_sparse():
    for cov in ("full", "partial", "sparse"):
        state = _state(coverage=cov)
        result = evaluate_strength_policy(state)
        by_rule = _decisions_by_rule(result)
        assert by_rule["require_min_coverage"].decision == "allow"


# ---------------------------------------------------------------------------
# R-sparse confidence cap
# ---------------------------------------------------------------------------

def test_sparse_coverage_caps_confidence_to_moderate():
    state = _state(coverage="sparse")
    result = evaluate_strength_policy(state)

    by_rule = _decisions_by_rule(result)
    assert by_rule["no_high_confidence_on_sparse_signal"].decision == "soften"
    assert result.capped_confidence == "moderate"


def test_full_coverage_does_not_cap_confidence():
    state = _state(coverage="full")
    result = evaluate_strength_policy(state)
    by_rule = _decisions_by_rule(result)
    assert by_rule["no_high_confidence_on_sparse_signal"].decision == "allow"
    assert result.capped_confidence is None


def test_partial_coverage_does_not_cap_confidence():
    state = _state(coverage="partial")
    result = evaluate_strength_policy(state)
    by_rule = _decisions_by_rule(result)
    assert by_rule["no_high_confidence_on_sparse_signal"].decision == "allow"
    assert result.capped_confidence is None


# ---------------------------------------------------------------------------
# R-volume-spike escalation
# ---------------------------------------------------------------------------

def test_volume_ratio_below_threshold_allows():
    state = _state(coverage="full", volume_ratio=1.3)
    result = evaluate_strength_policy(state)
    by_rule = _decisions_by_rule(result)
    assert by_rule["volume_spike_escalation"].decision == "allow"
    assert result.forced_action is None


def test_volume_ratio_at_threshold_escalates():
    state = _state(coverage="full", volume_ratio=1.5)
    result = evaluate_strength_policy(state)
    by_rule = _decisions_by_rule(result)
    spike = by_rule["volume_spike_escalation"]
    assert spike.decision == "escalate"
    assert result.forced_action == "escalate_for_user_review"
    assert result.forced_action_detail is not None
    assert result.forced_action_detail["reason_token"] == "volume_spike_detected"
    assert result.forced_action_detail["volume_ratio"] == 1.5


def test_volume_ratio_above_threshold_escalates():
    state = _state(coverage="full", volume_ratio=2.0)
    result = evaluate_strength_policy(state)
    assert result.forced_action == "escalate_for_user_review"


def test_volume_ratio_none_does_not_escalate():
    state = _state(coverage="full", volume_ratio=None)
    result = evaluate_strength_policy(state)
    by_rule = _decisions_by_rule(result)
    assert by_rule["volume_spike_escalation"].decision == "allow"
    assert result.forced_action is None


def test_volume_spike_overrides_coverage_defer():
    """R-coverage would force defer; R-volume-spike forces escalate;
    the louder rule wins (matches sleep's chronic-deprivation → repay
    pattern and running's R-acwr-spike override)."""

    state = _state(coverage="insufficient", volume_ratio=2.0)
    result = evaluate_strength_policy(state)
    assert result.forced_action == "escalate_for_user_review"


# ---------------------------------------------------------------------------
# R-unmatched-exercise confidence cap
# ---------------------------------------------------------------------------

def test_unmatched_tokens_cap_confidence():
    state = _state(coverage="full", unmatched=("Jefferson Curl",))
    result = evaluate_strength_policy(state)
    by_rule = _decisions_by_rule(result)
    assert by_rule["unmatched_exercise_confidence_cap"].decision == "soften"
    assert result.capped_confidence == "moderate"


def test_no_unmatched_tokens_leaves_cap_null():
    state = _state(coverage="full", unmatched=())
    result = evaluate_strength_policy(state)
    by_rule = _decisions_by_rule(result)
    assert by_rule["unmatched_exercise_confidence_cap"].decision == "allow"
    assert result.capped_confidence is None


def test_unmatched_tokens_and_sparse_coverage_agree_on_cap_value():
    """Both cap to moderate; no tie to resolve."""

    state = _state(coverage="sparse", unmatched=("Phantom Lift",))
    result = evaluate_strength_policy(state)
    assert result.capped_confidence == "moderate"


# ---------------------------------------------------------------------------
# Audit completeness — every rule always emits a decision row
# ---------------------------------------------------------------------------

def test_every_rule_emits_a_decision():
    state = _state(coverage="full")
    result = evaluate_strength_policy(state)
    rule_ids = {d.rule_id for d in result.policy_decisions}
    assert rule_ids == {
        "require_min_coverage",
        "no_high_confidence_on_sparse_signal",
        "volume_spike_escalation",
        "unmatched_exercise_confidence_cap",
    }
