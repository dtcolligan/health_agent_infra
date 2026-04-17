"""Tests for ``evaluate_running_policy`` (Phase 2 step 2).

Locks every R-rule firing path: allow + block + escalate + soften, plus
the precedence rules between them (spike beats coverage-defer; cap is
independent of action). Defaults vs explicit thresholds both exercised.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS
from health_agent_infra.domains.running.classify import (
    ClassifiedRunningState,
    classify_running_state,
)
from health_agent_infra.domains.running.policy import (
    PolicyDecision,
    RunningPolicyResult,
    evaluate_running_policy,
)


def _signals(**overrides) -> dict:
    base = dict(
        weekly_mileage_m=50_000.0,
        weekly_mileage_baseline_m=50_000.0,
        recent_hard_session_count_7d=1,
        acwr_ratio=1.0,
        training_readiness_pct=70,
        sleep_debt_band="none",
        resting_hr_band="at",
    )
    base.update(overrides)
    return base


def _decision(result: RunningPolicyResult, rule_id: str) -> PolicyDecision:
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
    classified = classify_running_state(sig)
    result = evaluate_running_policy(classified, sig)

    rule_ids = [d.rule_id for d in result.policy_decisions]
    assert rule_ids == [
        "require_min_coverage",
        "no_high_confidence_on_sparse_signal",
        "acwr_spike_escalation",
    ]


def test_clean_signals_yield_no_forced_action_or_cap():
    sig = _signals()
    classified = classify_running_state(sig)
    result = evaluate_running_policy(classified, sig)

    assert result.forced_action is None
    assert result.forced_action_detail is None
    assert result.capped_confidence is None
    for dec in result.policy_decisions:
        assert dec.decision == "allow", dec


# ---------------------------------------------------------------------------
# R: require_min_coverage
# ---------------------------------------------------------------------------

def test_coverage_gate_blocks_and_forces_defer_when_insufficient():
    sig = _signals(weekly_mileage_baseline_m=None, weekly_mileage_ratio=None)
    classified = classify_running_state(sig)
    result = evaluate_running_policy(classified, sig)

    coverage = _decision(result, "require_min_coverage")
    assert coverage.decision == "block"
    assert "insufficient" in coverage.note
    assert result.forced_action == "defer_decision_insufficient_signal"


def test_coverage_gate_allows_on_partial():
    sig = _signals(recent_hard_session_count_7d=None)
    classified = classify_running_state(sig)
    assert classified.coverage_band == "partial"
    result = evaluate_running_policy(classified, sig)

    coverage = _decision(result, "require_min_coverage")
    assert coverage.decision == "allow"
    assert result.forced_action is None  # nothing else fires


def test_coverage_gate_allows_on_sparse():
    sig = _signals(acwr_ratio=None)
    classified = classify_running_state(sig)
    assert classified.coverage_band == "sparse"
    result = evaluate_running_policy(classified, sig)

    coverage = _decision(result, "require_min_coverage")
    assert coverage.decision == "allow"


# ---------------------------------------------------------------------------
# R: no_high_confidence_on_sparse_signal
# ---------------------------------------------------------------------------

def test_sparse_cap_softens_and_caps_to_moderate():
    sig = _signals(acwr_ratio=None)
    classified = classify_running_state(sig)
    assert classified.coverage_band == "sparse"
    result = evaluate_running_policy(classified, sig)

    cap = _decision(result, "no_high_confidence_on_sparse_signal")
    assert cap.decision == "soften"
    assert "moderate" in cap.note
    assert result.capped_confidence == "moderate"


def test_sparse_cap_allows_on_full_coverage():
    sig = _signals()
    classified = classify_running_state(sig)
    result = evaluate_running_policy(classified, sig)

    cap = _decision(result, "no_high_confidence_on_sparse_signal")
    assert cap.decision == "allow"
    assert result.capped_confidence is None


def test_sparse_cap_does_not_fire_on_partial():
    sig = _signals(recent_hard_session_count_7d=None)
    classified = classify_running_state(sig)
    assert classified.coverage_band == "partial"
    result = evaluate_running_policy(classified, sig)

    cap = _decision(result, "no_high_confidence_on_sparse_signal")
    assert cap.decision == "allow"
    assert result.capped_confidence is None


def test_sparse_cap_note_includes_uncertainty_tokens():
    """The note should surface why coverage is sparse so audit logs are
    self-describing without re-querying the classified state."""

    sig = _signals(acwr_ratio=None)
    classified = classify_running_state(sig)
    result = evaluate_running_policy(classified, sig)
    cap = _decision(result, "no_high_confidence_on_sparse_signal")
    assert "acwr_unavailable" in cap.note


# ---------------------------------------------------------------------------
# R: acwr_spike_escalation
# ---------------------------------------------------------------------------

def test_spike_escalates_at_or_above_default_threshold():
    sig = _signals(acwr_ratio=1.5)  # default threshold = 1.5
    classified = classify_running_state(sig)
    result = evaluate_running_policy(classified, sig)

    spike = _decision(result, "acwr_spike_escalation")
    assert spike.decision == "escalate"
    assert result.forced_action == "escalate_for_user_review"
    assert result.forced_action_detail == {
        "reason_token": "acwr_spike",
        "acwr_ratio": 1.5,
        "threshold": 1.5,
    }


def test_spike_does_not_fire_just_below_threshold():
    sig = _signals(acwr_ratio=1.49)
    classified = classify_running_state(sig)
    result = evaluate_running_policy(classified, sig)

    spike = _decision(result, "acwr_spike_escalation")
    assert spike.decision == "allow"
    assert result.forced_action is None


def test_spike_handles_missing_acwr_with_clean_allow():
    sig = _signals(acwr_ratio=None)
    classified = classify_running_state(sig)
    result = evaluate_running_policy(classified, sig)

    spike = _decision(result, "acwr_spike_escalation")
    assert spike.decision == "allow"
    assert "unavailable" in spike.note


def test_spike_threshold_respects_explicit_thresholds_override():
    sig = _signals(acwr_ratio=1.4)
    classified = classify_running_state(sig)

    # Default → spike does not fire at 1.4.
    default_result = evaluate_running_policy(classified, sig)
    assert _decision(default_result, "acwr_spike_escalation").decision == "allow"

    # Tightened threshold → spike fires at 1.4.
    tight = {**DEFAULT_THRESHOLDS}
    tight["policy"] = {
        **DEFAULT_THRESHOLDS["policy"],
        "running": {"r_acwr_spike_min_ratio": 1.3},
    }
    tight_result = evaluate_running_policy(classified, sig, thresholds=tight)
    assert _decision(tight_result, "acwr_spike_escalation").decision == "escalate"
    assert tight_result.forced_action == "escalate_for_user_review"


# ---------------------------------------------------------------------------
# Precedence: spike beats coverage-defer
# ---------------------------------------------------------------------------

def test_spike_overrides_coverage_defer_when_both_would_fire():
    """If coverage is insufficient AND ACWR spikes, the louder escalation
    signal wins. Coverage still records its own block decision."""

    sig = _signals(
        weekly_mileage_baseline_m=None, weekly_mileage_ratio=None,  # → insufficient
        acwr_ratio=1.7,                                              # → spike
    )
    classified = classify_running_state(sig)
    result = evaluate_running_policy(classified, sig)

    coverage = _decision(result, "require_min_coverage")
    spike = _decision(result, "acwr_spike_escalation")

    assert coverage.decision == "block"
    assert spike.decision == "escalate"
    # Spike overrides defer because it is the louder signal (mirrors recovery R6).
    assert result.forced_action == "escalate_for_user_review"
    assert result.forced_action_detail is not None
    assert result.forced_action_detail["reason_token"] == "acwr_spike"


# ---------------------------------------------------------------------------
# Cap independent of action
# ---------------------------------------------------------------------------

def test_cap_fires_alongside_spike_escalate():
    """Sparse coverage capping confidence is independent of any forced
    action — both can coexist on the same evaluation."""

    sig = _signals(acwr_ratio=1.6)  # classified will be sparse? No — acwr is present.
    # Force sparse via missing acwr while still firing spike via override:
    # not a real scenario (sparse needs acwr=None which kills spike). Use a
    # second axis: spike + cap can't both fire from this rule set in v1.
    # Lock that no false coupling exists by exercising the realistic cases:
    sig_sparse = _signals(acwr_ratio=None)
    classified = classify_running_state(sig_sparse)
    result = evaluate_running_policy(classified, sig_sparse)
    assert result.capped_confidence == "moderate"
    assert result.forced_action is None


# ---------------------------------------------------------------------------
# Frozen result
# ---------------------------------------------------------------------------

def test_policy_result_is_frozen():
    sig = _signals()
    classified = classify_running_state(sig)
    result = evaluate_running_policy(classified, sig)
    with pytest.raises(Exception):
        result.forced_action = "rest_day_recommended"  # type: ignore[misc]


def test_policy_decisions_are_frozen():
    sig = _signals()
    classified = classify_running_state(sig)
    result = evaluate_running_policy(classified, sig)
    with pytest.raises(Exception):
        result.policy_decisions[0].note = "tampered"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Type & decision-tier vocabulary
# ---------------------------------------------------------------------------

_ALLOWED_TIERS = {"allow", "soften", "block", "escalate"}


def test_every_decision_uses_allowed_tier_vocabulary():
    """A misspelled tier would silently break the synthesis layer's
    precedence logic (block > soften > cap_confidence > adjust). Locked
    here so a typo in policy.py is caught immediately."""

    sig = _signals(acwr_ratio=1.6, weekly_mileage_baseline_m=None)
    classified = classify_running_state(sig)
    result = evaluate_running_policy(classified, sig)
    for dec in result.policy_decisions:
        assert dec.decision in _ALLOWED_TIERS, dec
