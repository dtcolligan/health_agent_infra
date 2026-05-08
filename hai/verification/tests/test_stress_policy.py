"""Tests for ``evaluate_stress_policy`` (Phase 3 step 4).

Locks every R-rule firing path: allow + block + escalate + soften,
plus the precedence rules (sustained-stress beats coverage-defer;
sparse cap is independent of action). Defaults vs explicit thresholds
both exercised.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS
from health_agent_infra.domains.stress.classify import (
    ClassifiedStressState,
    classify_stress_state,
)
from health_agent_infra.domains.stress.policy import (
    PolicyDecision,
    StressPolicyResult,
    evaluate_stress_policy,
)


def _signals(**overrides) -> dict:
    base = dict(
        garmin_all_day_stress=25,
        manual_stress_score=2,
        body_battery_end_of_day=70,
        body_battery_prev_day=65,
        # Seven days all below the high threshold → no sustained stress.
        stress_history_garmin_last_7=[20, 25, 30, 22, 18, 25, 25],
    )
    base.update(overrides)
    return base


def _decision(result: StressPolicyResult, rule_id: str) -> PolicyDecision:
    matches = [d for d in result.policy_decisions if d.rule_id == rule_id]
    assert len(matches) == 1, (
        f"expected exactly one decision for rule {rule_id!r}, got {len(matches)}"
    )
    return matches[0]


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------

def test_policy_returns_three_decisions_in_canonical_order():
    sig = _signals()
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    rule_ids = [d.rule_id for d in result.policy_decisions]
    assert rule_ids == [
        "require_min_coverage",
        "no_high_confidence_on_sparse_signal",
        "sustained_very_high_stress_escalation",
    ]


def test_clean_signals_yield_no_forced_action_or_cap():
    sig = _signals()
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    assert result.forced_action is None
    assert result.forced_action_detail is None
    assert result.capped_confidence is None
    for dec in result.policy_decisions:
        assert dec.decision == "allow", dec


# ---------------------------------------------------------------------------
# R: require_min_coverage
# ---------------------------------------------------------------------------

def test_coverage_gate_blocks_and_forces_defer_when_insufficient():
    sig = _signals(garmin_all_day_stress=None, manual_stress_score=None)
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    coverage = _decision(result, "require_min_coverage")
    assert coverage.decision == "block"
    assert "insufficient" in coverage.note
    assert result.forced_action == "defer_decision_insufficient_signal"


def test_coverage_gate_allows_on_partial():
    sig = _signals(manual_stress_score=None)
    classified = classify_stress_state(sig)
    assert classified.coverage_band == "partial"
    result = evaluate_stress_policy(classified, sig)

    coverage = _decision(result, "require_min_coverage")
    assert coverage.decision == "allow"
    assert result.forced_action is None


def test_coverage_gate_allows_on_full():
    sig = _signals()
    classified = classify_stress_state(sig)
    assert classified.coverage_band == "full"
    result = evaluate_stress_policy(classified, sig)

    coverage = _decision(result, "require_min_coverage")
    assert coverage.decision == "allow"


# ---------------------------------------------------------------------------
# R: no_high_confidence_on_sparse_signal
# ---------------------------------------------------------------------------

def test_sparse_cap_softens_when_coverage_sparse():
    sig = _signals(
        manual_stress_score=None,
        body_battery_end_of_day=None,
        body_battery_prev_day=None,
    )
    classified = classify_stress_state(sig)
    assert classified.coverage_band == "sparse"
    result = evaluate_stress_policy(classified, sig)

    cap = _decision(result, "no_high_confidence_on_sparse_signal")
    assert cap.decision == "soften"
    assert result.capped_confidence == "moderate"


def test_sparse_cap_allows_on_full_coverage():
    sig = _signals()
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    cap = _decision(result, "no_high_confidence_on_sparse_signal")
    assert cap.decision == "allow"
    assert result.capped_confidence is None


def test_sparse_cap_independent_of_forced_action():
    """Sparse cap should fire on confidence independently of whether
    any rule forced an action. Verifies the ``capped_confidence`` slot
    is never overwritten by later rules."""

    sig = _signals(
        manual_stress_score=None,
        body_battery_end_of_day=None,
        body_battery_prev_day=None,
        stress_history_garmin_last_7=[70, 70, 70, 70, 70, 70, 70],
    )
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    assert result.capped_confidence == "moderate"
    assert result.forced_action == "escalate_for_user_review"


# ---------------------------------------------------------------------------
# R: sustained_very_high_stress_escalation
# ---------------------------------------------------------------------------

def test_sustained_stress_fires_at_exact_5_days_run():
    sig = _signals(
        # Last 5 values at the threshold → run length = 5, triggers.
        stress_history_garmin_last_7=[10, 10, 60, 65, 70, 62, 60],
    )
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    sust = _decision(result, "sustained_very_high_stress_escalation")
    assert sust.decision == "escalate"
    assert result.forced_action == "escalate_for_user_review"
    assert result.forced_action_detail["reason_token"] == "sustained_very_high_stress"
    assert result.forced_action_detail["consecutive_days"] == 5


def test_sustained_stress_does_not_fire_on_4_day_run():
    sig = _signals(
        stress_history_garmin_last_7=[10, 10, 10, 65, 70, 62, 60],
    )
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    sust = _decision(result, "sustained_very_high_stress_escalation")
    assert sust.decision == "allow"
    assert result.forced_action is None


def test_sustained_stress_requires_contiguous_run_ending_today():
    """A 5-day high stretch earlier in the window but not including
    today must NOT escalate — the rule measures sustained-through-today
    stress, not any-5-in-7."""

    sig = _signals(
        stress_history_garmin_last_7=[70, 70, 70, 70, 70, 30, 30],
    )
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    sust = _decision(result, "sustained_very_high_stress_escalation")
    assert sust.decision == "allow"
    assert result.forced_action is None


def test_sustained_stress_treats_missing_day_as_break():
    """A missing entry in the trailing window breaks the run — the
    rule only counts explicit at-or-above-threshold days."""

    sig = _signals(
        stress_history_garmin_last_7=[65, 65, 65, None, 65, 65, 65],
    )
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    sust = _decision(result, "sustained_very_high_stress_escalation")
    # Trailing run (from today backwards) is 3 days, since None breaks.
    assert sust.decision == "allow"


def test_sustained_stress_escalation_overrides_coverage_defer():
    """When both coverage=insufficient AND sustained-stress fire, the
    louder signal wins — escalate with forced action
    ``escalate_for_user_review``, not ``defer_decision_insufficient_signal``."""

    sig = _signals(
        garmin_all_day_stress=None,
        manual_stress_score=None,
        stress_history_garmin_last_7=[70, 70, 70, 70, 70, 70, 70],
    )
    classified = classify_stress_state(sig)
    assert classified.coverage_band == "insufficient"
    result = evaluate_stress_policy(classified, sig)

    cov = _decision(result, "require_min_coverage")
    sust = _decision(result, "sustained_very_high_stress_escalation")

    assert cov.decision == "block"
    assert sust.decision == "escalate"
    assert result.forced_action == "escalate_for_user_review"


def test_sustained_stress_uses_explicit_thresholds():
    t = {
        "classify": DEFAULT_THRESHOLDS["classify"],
        "policy": {
            "stress": {
                "r_sustained_stress_days": 3,
                "r_sustained_stress_min_score": 50,
            },
        },
    }
    sig = _signals(
        stress_history_garmin_last_7=[20, 20, 20, 20, 55, 60, 70],
    )
    classified = classify_stress_state(sig, thresholds=t)
    result = evaluate_stress_policy(classified, sig, thresholds=t)

    sust = _decision(result, "sustained_very_high_stress_escalation")
    assert sust.decision == "escalate"
    assert result.forced_action_detail["consecutive_days"] == 3


def test_sustained_stress_empty_history_does_not_fire():
    sig = _signals(stress_history_garmin_last_7=[])
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    sust = _decision(result, "sustained_very_high_stress_escalation")
    assert sust.decision == "allow"


def test_sustained_stress_missing_history_does_not_fire():
    sig = _signals()
    del sig["stress_history_garmin_last_7"]
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    sust = _decision(result, "sustained_very_high_stress_escalation")
    assert sust.decision == "allow"


# ---------------------------------------------------------------------------
# Decision-record surface
# ---------------------------------------------------------------------------

def test_all_decisions_carry_non_empty_notes():
    """Every PolicyDecision carries a ``note`` string that explains
    the rule's result. Agents read this verbatim; it must never be empty."""

    sig = _signals()
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    for dec in result.policy_decisions:
        assert dec.note, f"decision {dec.rule_id} has empty note"
        assert len(dec.note) > 0


def test_forced_action_detail_present_on_sustained_escalation():
    sig = _signals(
        stress_history_garmin_last_7=[65, 65, 65, 65, 65, 65, 65],
    )
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    assert result.forced_action_detail is not None
    assert result.forced_action_detail["threshold_days"] == (
        DEFAULT_THRESHOLDS["policy"]["stress"]["r_sustained_stress_days"]
    )


def test_forced_action_detail_absent_on_coverage_defer():
    sig = _signals(garmin_all_day_stress=None, manual_stress_score=None)
    classified = classify_stress_state(sig)
    result = evaluate_stress_policy(classified, sig)

    # coverage-defer doesn't carry detail (same shape as sleep + running).
    assert result.forced_action == "defer_decision_insufficient_signal"
    assert result.forced_action_detail is None
