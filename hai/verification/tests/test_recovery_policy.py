"""Tests for domains/recovery/policy.py — R1, R5, R6 mechanical gates.

Every rule evaluated in every branch (allow / block / soften / escalate).
Forced-action precedence (R6 over R1) verified.
"""

from __future__ import annotations

from health_agent_infra.domains.recovery.classify import ClassifiedRecoveryState
from health_agent_infra.domains.recovery.policy import (
    PolicyDecision,
    RecoveryPolicyResult,
    evaluate_recovery_policy,
)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _classified(**overrides):
    base = dict(
        sleep_debt_band="none",
        resting_hr_band="at",
        hrv_band="at",
        training_load_band="moderate",
        soreness_band="low",
        coverage_band="full",
        recovery_status="recovered",
        readiness_score=0.95,
        uncertainty=tuple(),
    )
    base.update(overrides)
    return ClassifiedRecoveryState(**base)


def _find(policy_result: RecoveryPolicyResult, rule_id: str) -> PolicyDecision:
    for decision in policy_result.policy_decisions:
        if decision.rule_id == rule_id:
            return decision
    raise AssertionError(f"rule_id {rule_id!r} not found in {policy_result}")


# ---------------------------------------------------------------------------
# R1 — require_min_coverage
# ---------------------------------------------------------------------------

def test_r1_allows_on_full_coverage():
    result = evaluate_recovery_policy(
        _classified(coverage_band="full"),
        raw_summary={"resting_hr_spike_days": 0},
    )
    dec = _find(result, "require_min_coverage")
    assert dec.decision == "allow"
    assert result.forced_action is None


def test_r1_blocks_on_insufficient_coverage():
    result = evaluate_recovery_policy(
        _classified(coverage_band="insufficient", readiness_score=None),
        raw_summary={"resting_hr_spike_days": 0},
    )
    dec = _find(result, "require_min_coverage")
    assert dec.decision == "block"
    assert result.forced_action == "defer_decision_insufficient_signal"


def test_r1_allows_on_sparse_and_partial():
    for cov in ("sparse", "partial"):
        result = evaluate_recovery_policy(
            _classified(coverage_band=cov),
            raw_summary={"resting_hr_spike_days": 0},
        )
        dec = _find(result, "require_min_coverage")
        assert dec.decision == "allow", f"coverage={cov} should allow"


# ---------------------------------------------------------------------------
# R5 — no_high_confidence_on_sparse_signal
# ---------------------------------------------------------------------------

def test_r5_softens_confidence_on_sparse():
    result = evaluate_recovery_policy(
        _classified(
            coverage_band="sparse",
            uncertainty=("training_load_window_incomplete",),
        ),
        raw_summary={"resting_hr_spike_days": 0},
    )
    dec = _find(result, "no_high_confidence_on_sparse_signal")
    assert dec.decision == "soften"
    assert result.capped_confidence == "moderate"
    assert "training_load_window_incomplete" in dec.note


def test_r5_allows_on_full_coverage():
    result = evaluate_recovery_policy(
        _classified(coverage_band="full"),
        raw_summary={"resting_hr_spike_days": 0},
    )
    dec = _find(result, "no_high_confidence_on_sparse_signal")
    assert dec.decision == "allow"
    assert result.capped_confidence is None


def test_r5_allows_on_partial_coverage():
    """Partial is not sparse; skill starts at moderate already."""
    result = evaluate_recovery_policy(
        _classified(coverage_band="partial"),
        raw_summary={"resting_hr_spike_days": 0},
    )
    dec = _find(result, "no_high_confidence_on_sparse_signal")
    assert dec.decision == "allow"
    assert result.capped_confidence is None


# ---------------------------------------------------------------------------
# R6 — resting_hr_spike_escalation
# ---------------------------------------------------------------------------

def test_r6_allows_when_spike_days_below_threshold():
    result = evaluate_recovery_policy(
        _classified(),
        raw_summary={"resting_hr_spike_days": 2},
    )
    dec = _find(result, "resting_hr_spike_escalation")
    assert dec.decision == "allow"
    assert result.forced_action is None


def test_r6_escalates_at_threshold():
    result = evaluate_recovery_policy(
        _classified(),
        raw_summary={"resting_hr_spike_days": 3},
    )
    dec = _find(result, "resting_hr_spike_escalation")
    assert dec.decision == "escalate"
    assert result.forced_action == "escalate_for_user_review"
    assert result.forced_action_detail == {
        "reason_token": "resting_hr_spike_3_days_running",
        "consecutive_days": 3,
    }


def test_r6_escalates_above_threshold():
    result = evaluate_recovery_policy(
        _classified(),
        raw_summary={"resting_hr_spike_days": 7},
    )
    assert result.forced_action == "escalate_for_user_review"
    assert result.forced_action_detail["consecutive_days"] == 7


def test_r6_allows_when_spike_days_missing():
    result = evaluate_recovery_policy(
        _classified(),
        raw_summary={},  # no resting_hr_spike_days at all
    )
    dec = _find(result, "resting_hr_spike_escalation")
    assert dec.decision == "allow"
    assert "unavailable" in dec.note


# ---------------------------------------------------------------------------
# Rule interaction — R6 escalation overrides R1 defer
# ---------------------------------------------------------------------------

def test_r6_escalation_overrides_r1_block():
    """If coverage is insufficient AND spike is ≥3, R6 wins.

    The escalation is the more actionable signal than a defer — it tells
    the user 'something is persistently off', even when full signals
    aren't present.
    """

    result = evaluate_recovery_policy(
        _classified(coverage_band="insufficient", readiness_score=None),
        raw_summary={"resting_hr_spike_days": 5},
    )
    assert result.forced_action == "escalate_for_user_review"
    # But R1 still fired as a block and is recorded.
    r1 = _find(result, "require_min_coverage")
    assert r1.decision == "block"
    r6 = _find(result, "resting_hr_spike_escalation")
    assert r6.decision == "escalate"


# ---------------------------------------------------------------------------
# Threshold override
# ---------------------------------------------------------------------------

def test_r6_threshold_is_config_driven():
    override = {
        "classify": {"recovery": {}},
        "policy": {"recovery": {"r6_resting_hr_spike_days_threshold": 5}},
        "synthesis": {"x_rules": {}},
    }
    # Spike days = 4; below override threshold of 5.
    result = evaluate_recovery_policy(
        _classified(),
        raw_summary={"resting_hr_spike_days": 4},
        thresholds=override,
    )
    assert result.forced_action is None

    # Now at threshold.
    result = evaluate_recovery_policy(
        _classified(),
        raw_summary={"resting_hr_spike_days": 5},
        thresholds=override,
    )
    assert result.forced_action == "escalate_for_user_review"


# ---------------------------------------------------------------------------
# PolicyResult shape invariants
# ---------------------------------------------------------------------------

def test_every_evaluation_produces_three_decisions():
    """R1, R5, R6 each always fire — allow or otherwise — so every call
    must record exactly three PolicyDecision rows."""

    result = evaluate_recovery_policy(
        _classified(),
        raw_summary={"resting_hr_spike_days": 0},
    )
    rule_ids = [d.rule_id for d in result.policy_decisions]
    assert set(rule_ids) == {
        "require_min_coverage",
        "no_high_confidence_on_sparse_signal",
        "resting_hr_spike_escalation",
    }
