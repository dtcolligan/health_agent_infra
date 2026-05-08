"""W-B: R-volume-spike minimum-coverage gate boundary tests.

Per Codex F-PLAN-10: a new `r_volume_spike_min_sessions_last_28d`
threshold (default 8) gates the spike rule. Below it, the rule
yields rather than escalating — sparse history can't produce a
meaningful spike ratio.

Plus the D12-coercer test: bool override of the threshold rejects.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from health_agent_infra.core.config import (
    DEFAULT_THRESHOLDS,
    coerce_int,
    ConfigCoerceError,
)
from health_agent_infra.domains.strength.classify import (
    ClassifiedStrengthState,
)
from health_agent_infra.domains.strength.policy import _r_volume_spike


def _state(*, ratio: float, sessions_28d: int | None) -> ClassifiedStrengthState:
    """Build a minimal ClassifiedStrengthState that exercises the gate.

    Fields that don't matter to the gate are filled with defaults; the
    coverage gate elsewhere may classify ``insufficient`` separately,
    but ``_r_volume_spike`` reads ``volume_ratio`` and
    ``sessions_last_28d`` directly.
    """
    return ClassifiedStrengthState(
        recent_volume_band="high",
        freshness_band_by_group={},
        coverage_band="full",
        strength_status="progressing",
        strength_score=0.7,
        volume_ratio=ratio,
        sessions_last_7d=2,
        sessions_last_28d=sessions_28d,
        unmatched_exercise_tokens=(),
    )


# ---------------------------------------------------------------------------
# Boundary tests at 7 / 8 / 9 sessions (default threshold = 8)
# ---------------------------------------------------------------------------


def test_below_threshold_yields_no_escalation():
    """sessions_last_28d=7 < 8 → spike rule yields, no forced action."""
    decision, forced_action, detail = _r_volume_spike(
        _state(ratio=4.0, sessions_28d=7),
        DEFAULT_THRESHOLDS,
    )
    assert decision.decision == "allow"
    assert forced_action is None
    assert detail is None
    assert "yielding" in decision.note
    assert "min_sessions_last_28d=8" in decision.note


def test_at_threshold_evaluates_spike():
    """sessions_last_28d=8 == threshold → spike rule fires when ratio >= 1.5."""
    decision, forced_action, detail = _r_volume_spike(
        _state(ratio=4.0, sessions_28d=8),
        DEFAULT_THRESHOLDS,
    )
    assert decision.decision == "escalate"
    assert forced_action == "escalate_for_user_review"
    assert detail == {
        "reason_token": "volume_spike_detected",
        "volume_ratio": 4.0,
        "threshold_ratio": 1.5,
    }


def test_above_threshold_evaluates_spike():
    """sessions_last_28d=9 > 8 → spike rule fires when ratio >= 1.5."""
    decision, forced_action, _ = _r_volume_spike(
        _state(ratio=2.0, sessions_28d=9),
        DEFAULT_THRESHOLDS,
    )
    assert decision.decision == "escalate"
    assert forced_action == "escalate_for_user_review"


def test_above_threshold_below_ratio_allows():
    """sessions_last_28d>=8 + ratio<1.5 → allow, no escalation."""
    decision, forced_action, _ = _r_volume_spike(
        _state(ratio=1.0, sessions_28d=10),
        DEFAULT_THRESHOLDS,
    )
    assert decision.decision == "allow"
    assert forced_action is None
    assert "below threshold=1.5" in decision.note


def test_unknown_sessions_yields():
    """sessions_last_28d=None (signal absent) → yield, not crash."""
    decision, forced_action, _ = _r_volume_spike(
        _state(ratio=4.0, sessions_28d=None),
        DEFAULT_THRESHOLDS,
    )
    assert decision.decision == "allow"
    assert forced_action is None
    assert "unknown" in decision.note


# ---------------------------------------------------------------------------
# Demo-run regression fixture (Dom's 2026-04-28 case)
# ---------------------------------------------------------------------------


def test_demo_run_2026_04_28_no_longer_escalates():
    """The 2026-04-28 demo run had sessions_last_28d=2, volume_ratio=4.0,
    favourable subjective signals. Pre-fix: R-volume-spike escalated.
    Post-fix: rule yields per the new gate."""
    decision, forced_action, _ = _r_volume_spike(
        _state(ratio=4.0, sessions_28d=2),
        DEFAULT_THRESHOLDS,
    )
    assert decision.decision == "allow"
    assert forced_action is None


# ---------------------------------------------------------------------------
# D12 coercer tests (Codex F-PLAN-10)
# ---------------------------------------------------------------------------


def test_coercer_accepts_int_threshold():
    assert coerce_int(8, name="test.path") == 8


def test_coercer_accepts_int_string():
    assert coerce_int("8", name="test.path") == 8


def test_coercer_rejects_bool_true():
    """bool(True) is technically int(1); coerce_int rejects to prevent
    silent bool-as-numeric coercion (D12 invariant)."""
    with pytest.raises(ConfigCoerceError):
        coerce_int(True, name="test.path")


def test_coercer_rejects_bool_false():
    with pytest.raises(ConfigCoerceError):
        coerce_int(False, name="test.path")


def test_threshold_with_bool_override_rejects_via_policy_path():
    """End-to-end: a bool-shaped threshold override flows through the
    coercer and rejects at policy invocation time."""
    bogus = copy.deepcopy(DEFAULT_THRESHOLDS)
    bogus["policy"]["strength"]["r_volume_spike_min_sessions_last_28d"] = True
    with pytest.raises(ConfigCoerceError):
        _r_volume_spike(_state(ratio=4.0, sessions_28d=10), bogus)
