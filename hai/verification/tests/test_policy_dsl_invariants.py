"""W-P: property-based invariants over the policy DSL (v0.1.11).

Hypothesis-driven assertions that hold across the input space of
each domain's `evaluate_*_policy`:

- `forced_action` (when not None) is in
  `core.validate.ALLOWED_ACTIONS_BY_DOMAIN[domain]`.
- `capped_confidence` (when not None) is one of "low" /
  "moderate" / "high".

The strategies generate ClassifiedXState dataclasses with valid
band-tuple values for each field. We don't need the band values to
be physically realistic — the policy logic should be safe over
every legal input combination.
"""

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from health_agent_infra.core.validate import ALLOWED_ACTIONS_BY_DOMAIN

from health_agent_infra.domains.recovery.classify import (
    ClassifiedRecoveryState,
)
from health_agent_infra.domains.recovery.policy import (
    evaluate_recovery_policy,
)
from health_agent_infra.domains.running.classify import (
    ClassifiedRunningState,
)
from health_agent_infra.domains.running.policy import (
    evaluate_running_policy,
)
from health_agent_infra.domains.sleep.classify import (
    ClassifiedSleepState,
)
from health_agent_infra.domains.sleep.policy import (
    evaluate_sleep_policy,
)
from health_agent_infra.domains.stress.classify import (
    ClassifiedStressState,
)
from health_agent_infra.domains.stress.policy import (
    evaluate_stress_policy,
)
from health_agent_infra.domains.strength.classify import (
    ClassifiedStrengthState,
)
from health_agent_infra.domains.strength.policy import (
    evaluate_strength_policy,
)
from health_agent_infra.domains.nutrition.classify import (
    ClassifiedNutritionState,
)
from health_agent_infra.domains.nutrition.policy import (
    evaluate_nutrition_policy,
)


VALID_CONFIDENCES = frozenset({"low", "moderate", "high"})


# ---------------------------------------------------------------------------
# Recovery
# ---------------------------------------------------------------------------


_RECOVERY_BANDS = st.fixed_dictionaries({
    "sleep_debt_band": st.sampled_from(["none", "minor", "moderate", "severe", "unknown"]),
    "resting_hr_band": st.sampled_from(["below_baseline", "baseline", "elevated", "very_elevated", "unknown"]),
    "hrv_band": st.sampled_from(["above_baseline", "baseline", "below_baseline", "very_low", "unknown"]),
    "training_load_band": st.sampled_from(["maintaining", "productive", "overreaching", "unknown"]),
    "soreness_band": st.sampled_from(["low", "moderate", "high", "unknown"]),
    "coverage_band": st.sampled_from(["full", "partial", "sparse", "insufficient"]),
    "recovery_status": st.sampled_from(["supportive", "neutral", "limiting", "unknown"]),
    "readiness_score": st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False)),
})


@given(_RECOVERY_BANDS)
@settings(max_examples=80, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_recovery_policy_forced_action_in_enum(bands):
    classified = ClassifiedRecoveryState(uncertainty=(), **bands)
    result = evaluate_recovery_policy(classified, raw_summary={})
    if result.forced_action is not None:
        assert result.forced_action in ALLOWED_ACTIONS_BY_DOMAIN["recovery"]
    if result.capped_confidence is not None:
        assert result.capped_confidence in VALID_CONFIDENCES


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------


_RUNNING_BANDS = st.fixed_dictionaries({
    "freshness_band": st.sampled_from(["fresh", "moderate", "fatigued", "unknown"]),
    "weekly_mileage_trend_band": st.sampled_from(["below", "baseline", "above", "unknown"]),
    "hard_session_load_band": st.sampled_from(["none", "low", "moderate", "high", "very_high"]),
    "recovery_adjacent_band": st.sampled_from(["supportive", "neutral", "limiting", "unknown"]),
    "coverage_band": st.sampled_from(["full", "partial", "sparse", "insufficient"]),
    "running_readiness_status": st.sampled_from(["ready", "conditional", "limited", "insufficient", "unknown"]),
    "readiness_score": st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False)),
})


@given(_RUNNING_BANDS)
@settings(max_examples=80, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_running_policy_forced_action_in_enum(bands):
    classified = ClassifiedRunningState(uncertainty=(), **bands)
    result = evaluate_running_policy(classified, running_signals={})
    if result.forced_action is not None:
        assert result.forced_action in ALLOWED_ACTIONS_BY_DOMAIN["running"]
    if result.capped_confidence is not None:
        assert result.capped_confidence in VALID_CONFIDENCES


# ---------------------------------------------------------------------------
# Sleep
# ---------------------------------------------------------------------------


_SLEEP_BANDS = st.fixed_dictionaries({
    "sleep_quality_band": st.sampled_from(["good", "fair", "poor", "unknown"]),
    "sleep_debt_band": st.sampled_from(["none", "minor", "moderate", "severe", "unknown"]),
    "sleep_efficiency_band": st.sampled_from(["good", "fair", "poor", "unknown"]),
    "sleep_efficiency_pct": st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False)),
    "sleep_timing_consistency_band": st.sampled_from(["consistent", "drifting", "erratic", "unknown"]),
    "coverage_band": st.sampled_from(["full", "partial", "sparse", "insufficient"]),
    "sleep_status": st.sampled_from(["adequate", "minor_deficit", "deficit", "insufficient", "unknown"]),
    "sleep_score": st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False)),
})


@given(_SLEEP_BANDS)
@settings(max_examples=80, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_sleep_policy_forced_action_in_enum(bands):
    classified = ClassifiedSleepState(uncertainty=(), **bands)
    result = evaluate_sleep_policy(classified, sleep_signals={})
    if result.forced_action is not None:
        assert result.forced_action in ALLOWED_ACTIONS_BY_DOMAIN["sleep"]
    if result.capped_confidence is not None:
        assert result.capped_confidence in VALID_CONFIDENCES


# ---------------------------------------------------------------------------
# Stress
# ---------------------------------------------------------------------------


_STRESS_BANDS = st.fixed_dictionaries({
    "manual_stress_band": st.sampled_from(["low", "moderate", "elevated", "high", "unknown"]),
    "garmin_stress_band": st.sampled_from(["low", "moderate", "elevated", "high", "unknown"]),
    "body_battery_trend_band": st.sampled_from(["recovering", "stable", "declining", "depleted", "unknown"]),
    "body_battery_delta": st.one_of(st.none(), st.integers(min_value=-100, max_value=100)),
    "coverage_band": st.sampled_from(["full", "partial", "sparse", "insufficient"]),
    "stress_state": st.sampled_from(["manageable", "elevated", "insufficient", "unknown"]),
    "stress_score": st.one_of(st.none(), st.floats(min_value=0.0, max_value=10.0, allow_nan=False)),
})


@given(_STRESS_BANDS)
@settings(max_examples=80, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_stress_policy_forced_action_in_enum(bands):
    classified = ClassifiedStressState(uncertainty=(), **bands)
    result = evaluate_stress_policy(classified, stress_signals={})
    if result.forced_action is not None:
        assert result.forced_action in ALLOWED_ACTIONS_BY_DOMAIN["stress"]
    if result.capped_confidence is not None:
        assert result.capped_confidence in VALID_CONFIDENCES


# ---------------------------------------------------------------------------
# Strength
# ---------------------------------------------------------------------------


_STRENGTH_BANDS = st.fixed_dictionaries({
    "recent_volume_band": st.sampled_from(["very_low", "low", "moderate", "high", "very_high", "unknown"]),
    "freshness_band_by_group": st.just({}),
    "coverage_band": st.sampled_from(["full", "partial", "sparse", "insufficient"]),
    "strength_status": st.sampled_from(["progressing", "maintaining", "undertrained", "overreaching", "unknown"]),
    "strength_score": st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False)),
    "volume_ratio": st.one_of(st.none(), st.floats(min_value=0.0, max_value=10.0, allow_nan=False)),
    "sessions_last_7d": st.one_of(st.none(), st.integers(min_value=0, max_value=20)),
    "sessions_last_28d": st.one_of(st.none(), st.integers(min_value=0, max_value=60)),
    "unmatched_exercise_tokens": st.just(()),
})


@given(_STRENGTH_BANDS)
@settings(max_examples=80, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_strength_policy_forced_action_in_enum(bands):
    classified = ClassifiedStrengthState(uncertainty=(), **bands)
    result = evaluate_strength_policy(classified)
    if result.forced_action is not None:
        assert result.forced_action in ALLOWED_ACTIONS_BY_DOMAIN["strength"]
    if result.capped_confidence is not None:
        assert result.capped_confidence in VALID_CONFIDENCES


# ---------------------------------------------------------------------------
# Nutrition
# ---------------------------------------------------------------------------


_NUTRITION_BANDS = st.fixed_dictionaries({
    "calorie_balance_band": st.sampled_from(["high_deficit", "moderate_deficit", "balanced", "surplus", "unknown"]),
    "calorie_deficit_kcal": st.one_of(st.none(), st.floats(min_value=-2000.0, max_value=2000.0, allow_nan=False)),
    "protein_sufficiency_band": st.sampled_from(["very_low", "low", "met", "exceeds", "unknown"]),
    "protein_ratio": st.one_of(st.none(), st.floats(min_value=0.0, max_value=2.5, allow_nan=False)),
    "hydration_band": st.sampled_from(["adequate", "low", "very_low", "unknown"]),
    "hydration_ratio": st.one_of(st.none(), st.floats(min_value=0.0, max_value=2.0, allow_nan=False)),
    "micronutrient_coverage": st.sampled_from(["unavailable_at_source"]),
    "coverage_band": st.sampled_from(["full", "partial", "sparse", "insufficient"]),
    "nutrition_status": st.sampled_from(["adequate", "deficit", "extreme_deficiency", "surplus", "insufficient", "unknown"]),
    "nutrition_score": st.one_of(st.none(), st.floats(min_value=0.0, max_value=1.0, allow_nan=False)),
    "derivation_path": st.sampled_from(["daily_macros"]),
})


@given(_NUTRITION_BANDS)
@settings(max_examples=80, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_nutrition_policy_forced_action_in_enum(bands):
    classified = ClassifiedNutritionState(uncertainty=(), **bands)
    # nutrition policy needs an `is_end_of_day` flag and a `meals_count`;
    # default to end-of-day so the partial-day W-C gate doesn't suppress
    # findings.
    result = evaluate_nutrition_policy(
        classified, is_end_of_day=True, meals_count=4,
    )
    if result.forced_action is not None:
        assert result.forced_action in ALLOWED_ACTIONS_BY_DOMAIN["nutrition"]
    if result.capped_confidence is not None:
        assert result.capped_confidence in VALID_CONFIDENCES
