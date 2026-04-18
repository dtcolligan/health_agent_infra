"""Tests for ``evaluate_sleep_policy`` (Phase 3 step 3).

Locks every R-rule firing path: allow + block + escalate + soften,
plus the precedence rules (chronic deprivation beats coverage-defer;
sparse cap is independent of action). Defaults vs explicit thresholds
both exercised.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS
from health_agent_infra.domains.sleep.classify import (
    ClassifiedSleepState,
    classify_sleep_state,
)
from health_agent_infra.domains.sleep.policy import (
    PolicyDecision,
    SleepPolicyResult,
    evaluate_sleep_policy,
)


def _signals(**overrides) -> dict:
    base = dict(
        sleep_hours=8.0,
        sleep_score_overall=85,
        sleep_awake_min=20.0,
        sleep_start_variance_minutes=15.0,
        # Seven nights all >= 7h → no chronic deprivation.
        sleep_history_hours_last_7=[8.0, 7.5, 7.8, 8.0, 7.2, 8.0, 7.5],
    )
    base.update(overrides)
    return base


def _decision(result: SleepPolicyResult, rule_id: str) -> PolicyDecision:
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
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)

    rule_ids = [d.rule_id for d in result.policy_decisions]
    assert rule_ids == [
        "require_min_coverage",
        "no_high_confidence_on_sparse_signal",
        "chronic_deprivation_escalation",
    ]


def test_clean_signals_yield_no_forced_action_or_cap():
    sig = _signals()
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)

    assert result.forced_action is None
    assert result.forced_action_detail is None
    assert result.capped_confidence is None
    for dec in result.policy_decisions:
        assert dec.decision == "allow", dec


# ---------------------------------------------------------------------------
# R: require_min_coverage
# ---------------------------------------------------------------------------

def test_coverage_gate_blocks_and_forces_defer_when_insufficient():
    sig = _signals(sleep_hours=None)
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)

    coverage = _decision(result, "require_min_coverage")
    assert coverage.decision == "block"
    assert "insufficient" in coverage.note
    assert result.forced_action == "defer_decision_insufficient_signal"


def test_coverage_gate_allows_on_partial():
    sig = _signals(sleep_score_overall=None)
    classified = classify_sleep_state(sig)
    assert classified.coverage_band == "partial"
    result = evaluate_sleep_policy(classified, sig)

    coverage = _decision(result, "require_min_coverage")
    assert coverage.decision == "allow"
    assert result.forced_action is None


def test_coverage_gate_allows_on_sparse():
    sig = _signals(sleep_score_overall=None, sleep_awake_min=None)
    classified = classify_sleep_state(sig)
    assert classified.coverage_band == "sparse"
    result = evaluate_sleep_policy(classified, sig)

    coverage = _decision(result, "require_min_coverage")
    assert coverage.decision == "allow"


# ---------------------------------------------------------------------------
# R: no_high_confidence_on_sparse_signal
# ---------------------------------------------------------------------------

def test_sparse_cap_softens_and_caps_to_moderate():
    sig = _signals(sleep_score_overall=None, sleep_awake_min=None)
    classified = classify_sleep_state(sig)
    assert classified.coverage_band == "sparse"
    result = evaluate_sleep_policy(classified, sig)

    cap = _decision(result, "no_high_confidence_on_sparse_signal")
    assert cap.decision == "soften"
    assert "moderate" in cap.note
    assert result.capped_confidence == "moderate"


def test_sparse_cap_allows_on_full_coverage():
    sig = _signals()
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)

    cap = _decision(result, "no_high_confidence_on_sparse_signal")
    assert cap.decision == "allow"
    assert result.capped_confidence is None


def test_sparse_cap_does_not_fire_on_partial():
    sig = _signals(sleep_score_overall=None)
    classified = classify_sleep_state(sig)
    assert classified.coverage_band == "partial"
    result = evaluate_sleep_policy(classified, sig)

    cap = _decision(result, "no_high_confidence_on_sparse_signal")
    assert cap.decision == "allow"
    assert result.capped_confidence is None


def test_sparse_cap_note_includes_uncertainty_tokens():
    sig = _signals(sleep_score_overall=None, sleep_awake_min=None)
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)
    cap = _decision(result, "no_high_confidence_on_sparse_signal")
    assert "sleep_score_unavailable" in cap.note
    assert "sleep_efficiency_unavailable" in cap.note


# ---------------------------------------------------------------------------
# R: chronic_deprivation_escalation
# ---------------------------------------------------------------------------

def test_chronic_deprivation_escalates_at_default_threshold():
    """Default: 4 nights <6h in last 7 → escalate. Forces
    ``sleep_debt_repayment_day`` (sleep has no ``escalate_for_user_review``
    in its v1 enum; the severity is carried in the decision tier)."""

    sig = _signals(sleep_history_hours_last_7=[5.0, 5.5, 5.8, 5.9, 7.5, 8.0, 7.0])
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)

    chron = _decision(result, "chronic_deprivation_escalation")
    assert chron.decision == "escalate"
    assert result.forced_action == "sleep_debt_repayment_day"
    assert result.forced_action_detail is not None
    assert result.forced_action_detail["reason_token"] == "chronic_deprivation_detected"
    assert result.forced_action_detail["short_nights"] == 4
    assert result.forced_action_detail["threshold_nights"] == 4
    assert result.forced_action_detail["threshold_hours"] == 6.0


def test_chronic_deprivation_does_not_fire_at_three_short_nights():
    sig = _signals(sleep_history_hours_last_7=[5.0, 5.5, 5.9, 7.0, 7.5, 8.0, 7.0])
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)

    chron = _decision(result, "chronic_deprivation_escalation")
    assert chron.decision == "allow"
    assert result.forced_action is None


def test_chronic_deprivation_boundary_inclusive_exactly_six_hours():
    """Threshold is strict inequality (<6h). A night at exactly 6h is
    NOT a short night."""

    sig = _signals(sleep_history_hours_last_7=[6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0])
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)
    chron = _decision(result, "chronic_deprivation_escalation")
    assert chron.decision == "allow"


def test_chronic_deprivation_fires_at_five_short_nights():
    sig = _signals(sleep_history_hours_last_7=[5.0, 5.0, 5.5, 5.5, 5.9, 7.0, 7.0])
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)
    chron = _decision(result, "chronic_deprivation_escalation")
    assert chron.decision == "escalate"
    assert result.forced_action_detail["short_nights"] == 5


def test_chronic_deprivation_handles_missing_history_with_allow():
    sig = _signals(sleep_history_hours_last_7=[])
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)
    chron = _decision(result, "chronic_deprivation_escalation")
    assert chron.decision == "allow"
    assert result.forced_action is None


def test_chronic_deprivation_treats_none_entries_as_non_deprivation():
    """Missing nights do not count toward the short-night tally — R1 is
    the authoritative gate for missing-data escalation, not R-chronic."""

    sig = _signals(
        sleep_history_hours_last_7=[None, None, None, 5.0, 5.5, 5.8, 5.9],
    )
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)
    chron = _decision(result, "chronic_deprivation_escalation")
    # Only 4 non-None short nights. Exactly at threshold → escalate.
    assert chron.decision == "escalate"
    assert result.forced_action_detail["short_nights"] == 4


def test_chronic_deprivation_thresholds_respect_explicit_override():
    sig = _signals(sleep_history_hours_last_7=[5.5, 5.5, 7.0, 7.0, 7.0, 7.0, 7.0])
    classified = classify_sleep_state(sig)

    # Default: only 2 short nights → allow.
    default_result = evaluate_sleep_policy(classified, sig)
    assert _decision(default_result, "chronic_deprivation_escalation").decision == "allow"

    # Tightened: 2 short nights is enough to escalate.
    tight = {**DEFAULT_THRESHOLDS}
    tight["policy"] = {
        **DEFAULT_THRESHOLDS["policy"],
        "sleep": {
            "r_chronic_deprivation_nights": 2,
            "r_chronic_deprivation_hours": 6.0,
        },
    }
    tight_result = evaluate_sleep_policy(classified, sig, thresholds=tight)
    assert _decision(tight_result, "chronic_deprivation_escalation").decision == "escalate"
    assert tight_result.forced_action == "sleep_debt_repayment_day"


# ---------------------------------------------------------------------------
# Precedence: chronic deprivation beats coverage-defer
# ---------------------------------------------------------------------------

def test_chronic_deprivation_overrides_coverage_defer_when_both_fire():
    """If today's sleep_hours is missing (coverage=insufficient) AND the
    last 7 nights show chronic deprivation, the louder escalation
    signal wins. Coverage still records its own block decision."""

    sig = _signals(
        sleep_hours=None,
        sleep_history_hours_last_7=[5.0, 5.5, 5.8, 5.9, 7.5, 8.0, 7.0],
    )
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)

    coverage = _decision(result, "require_min_coverage")
    chron = _decision(result, "chronic_deprivation_escalation")

    assert coverage.decision == "block"
    assert chron.decision == "escalate"
    assert result.forced_action == "sleep_debt_repayment_day"
    assert result.forced_action_detail is not None
    assert result.forced_action_detail["reason_token"] == "chronic_deprivation_detected"


# ---------------------------------------------------------------------------
# Cap independent of action
# ---------------------------------------------------------------------------

def test_cap_fires_alongside_chronic_escalate():
    """Sparse coverage capping confidence can coexist with chronic
    deprivation forcing an action — they operate on orthogonal axes."""

    sig = _signals(
        sleep_score_overall=None,
        sleep_awake_min=None,  # forces sparse
        sleep_history_hours_last_7=[5.0, 5.5, 5.8, 5.9, 7.0, 7.0, 7.0],
    )
    classified = classify_sleep_state(sig)
    assert classified.coverage_band == "sparse"
    result = evaluate_sleep_policy(classified, sig)

    assert result.capped_confidence == "moderate"
    assert result.forced_action == "sleep_debt_repayment_day"


# ---------------------------------------------------------------------------
# Frozen result
# ---------------------------------------------------------------------------

def test_policy_result_is_frozen():
    sig = _signals()
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)
    with pytest.raises(Exception):
        result.forced_action = "maintain_schedule"  # type: ignore[misc]


def test_policy_decisions_are_frozen():
    sig = _signals()
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)
    with pytest.raises(Exception):
        result.policy_decisions[0].note = "tampered"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Type & decision-tier vocabulary
# ---------------------------------------------------------------------------

_ALLOWED_TIERS = {"allow", "soften", "block", "escalate"}


def test_every_decision_uses_allowed_tier_vocabulary():
    sig = _signals(
        sleep_hours=None,
        sleep_history_hours_last_7=[5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0],
    )
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)
    for dec in result.policy_decisions:
        assert dec.decision in _ALLOWED_TIERS, dec


def test_chronic_escalation_forces_remedial_action_not_escalate_for_user_review():
    """Sleep's v1 enum deliberately omits ``escalate_for_user_review``.
    The R-chronic rule must force the remedial ``sleep_debt_repayment_day``
    action (not the recovery/running-style escalate action) while still
    recording ``escalate`` as the decision tier for audit."""

    sig = _signals(sleep_history_hours_last_7=[5.0, 5.0, 5.0, 5.0, 7.0, 7.0, 7.0])
    classified = classify_sleep_state(sig)
    result = evaluate_sleep_policy(classified, sig)
    assert result.forced_action == "sleep_debt_repayment_day"
    assert result.forced_action != "escalate_for_user_review"
