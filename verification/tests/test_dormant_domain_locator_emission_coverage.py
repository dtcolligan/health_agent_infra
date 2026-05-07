"""W-PROV-2 acceptance #4 — cross-domain emission coverage.

Asserts **5 of 5 dormant domains** (running, sleep, stress, strength,
nutrition) produce ≥1 locator on a representative classification path.
Recovery is NOT in the denominator — its R6 conditional emission shipped
at v0.1.14 and is not under W-PROV-2's scope per F-PLAN-02.

This is the cross-domain summary regression. Per-domain detail tests
live in `test_<domain>_locator_emission.py`.
"""

from __future__ import annotations

from health_agent_infra.core.provenance.locator import validate_locator
from health_agent_infra.domains.nutrition.classify import (
    ClassifiedNutritionState,
)
from health_agent_infra.domains.nutrition.policy import (
    evaluate_nutrition_policy,
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
from health_agent_infra.domains.strength.classify import (
    ClassifiedStrengthState,
)
from health_agent_infra.domains.strength.policy import (
    evaluate_strength_policy,
)
from health_agent_infra.domains.stress.classify import (
    ClassifiedStressState,
)
from health_agent_infra.domains.stress.policy import (
    evaluate_stress_policy,
)


_FOR_DATE = "2026-05-07"
_USER = "u_local_1"
_VERSION_TODAY = "2026-05-07T18:00:00Z"


def _running_result():
    classified = ClassifiedRunningState(
        weekly_mileage_trend_band="moderate",
        hard_session_load_band="moderate",
        freshness_band="adequate",
        recovery_adjacent_band="ok",
        coverage_band="full",
        running_readiness_status="ready",
        readiness_score=0.7,
        uncertainty=tuple(),
    )
    return evaluate_running_policy(
        classified,
        {"acwr_ratio": 1.0},
        for_date_iso=_FOR_DATE,
        user_id=_USER,
        running_today_row_version=_VERSION_TODAY,
    )


def _sleep_result():
    classified = ClassifiedSleepState(
        sleep_debt_band="none",
        sleep_quality_band="adequate",
        sleep_timing_consistency_band="consistent",
        sleep_efficiency_band="adequate",
        coverage_band="full",
        sleep_status="recovered",
        sleep_score=0.7,
        sleep_efficiency_pct=92.0,
        uncertainty=tuple(),
    )
    return evaluate_sleep_policy(
        classified,
        {"sleep_history_hours_last_7": [8.0] * 7},
        for_date_iso=_FOR_DATE,
        user_id=_USER,
        sleep_state_versions={_FOR_DATE: _VERSION_TODAY},
    )


def _stress_result():
    classified = ClassifiedStressState(
        garmin_stress_band="moderate",
        manual_stress_band="moderate",
        body_battery_trend_band="stable",
        coverage_band="full",
        stress_state="balanced",
        stress_score=0.6,
        body_battery_delta=5,
        uncertainty=tuple(),
    )
    return evaluate_stress_policy(
        classified,
        {"stress_history_garmin_last_7": [40] * 7},
        for_date_iso=_FOR_DATE,
        user_id=_USER,
        stress_state_versions={_FOR_DATE: _VERSION_TODAY},
    )


def _strength_result():
    classified = ClassifiedStrengthState(
        recent_volume_band="moderate",
        freshness_band_by_group={},
        coverage_band="full",
        strength_status="ready",
        strength_score=0.7,
        volume_ratio=1.0,
        sessions_last_7d=4,
        sessions_last_28d=16,
        unmatched_exercise_tokens=tuple(),
        uncertainty=tuple(),
    )
    return evaluate_strength_policy(
        classified,
        for_date_iso=_FOR_DATE,
        user_id=_USER,
        strength_today_row_version=_VERSION_TODAY,
    )


def _nutrition_result():
    classified = ClassifiedNutritionState(
        calorie_balance_band="moderate",
        protein_sufficiency_band="adequate",
        hydration_band="adequate",
        micronutrient_coverage={},
        coverage_band="full",
        nutrition_status="balanced",
        nutrition_score=0.7,
        calorie_deficit_kcal=100.0,
        protein_ratio=1.0,
        hydration_ratio=1.0,
        derivation_path="nutrition_intake_raw",
        uncertainty=tuple(),
    )
    return evaluate_nutrition_policy(
        classified,
        for_date_iso=_FOR_DATE,
        user_id=_USER,
        nutrition_today_row_version=_VERSION_TODAY,
    )


def test_all_five_dormant_domains_emit_at_least_one_locator() -> None:
    results = {
        "running": _running_result(),
        "sleep": _sleep_result(),
        "stress": _stress_result(),
        "strength": _strength_result(),
        "nutrition": _nutrition_result(),
    }
    domains_emitting = {
        domain
        for domain, result in results.items()
        if result.evidence_locators is not None
        and len(result.evidence_locators) >= 1
    }
    assert domains_emitting == {
        "running", "sleep", "stress", "strength", "nutrition"
    }, (
        f"Expected 5 of 5 dormant domains to emit; "
        f"actually emitted: {sorted(domains_emitting)}"
    )


def test_every_emitted_locator_validates_against_w_prov_1_contract() -> None:
    results = [
        _running_result(),
        _sleep_result(),
        _stress_result(),
        _strength_result(),
        _nutrition_result(),
    ]
    total_locators = 0
    for result in results:
        assert result.evidence_locators is not None
        for loc in result.evidence_locators:
            validate_locator(loc)
            total_locators += 1
    # Always-emit baseline: 1 locator per domain × 5 domains = 5.
    assert total_locators >= 5


def test_every_emitted_locator_cites_an_accepted_state_table() -> None:
    """Negative side of W-PROV-1 — never a write-side audit-chain
    table. F-PHASE0-12. The validator catches it, but pin the
    cross-domain check explicitly so the contract is named.
    """
    results = [
        _running_result(),
        _sleep_result(),
        _stress_result(),
        _strength_result(),
        _nutrition_result(),
    ]
    forbidden = {
        "recommendation_log", "proposal_log", "daily_plan",
        "planned_recommendation", "intent_item", "target",
        "x_rule_firing", "review_outcome", "data_quality_daily",
        "runtime_event_log", "sync_run_log",
    }
    for result in results:
        assert result.evidence_locators is not None
        for loc in result.evidence_locators:
            assert loc["table"] not in forbidden, (
                f"locator cites forbidden write-side table {loc['table']!r}"
            )
