"""W-PROV-2 nutrition-domain locator emission.

PLAN §2.A acceptance #2 + #4. Asserts the hybrid emission contract for
nutrition (single-day rule, partial-day suppression preserves the
always-emit row-level locator).
"""

from __future__ import annotations

from health_agent_infra.core.provenance.locator import validate_locator
from health_agent_infra.domains.nutrition.classify import (
    ClassifiedNutritionState,
)
from health_agent_infra.domains.nutrition.policy import (
    evaluate_nutrition_policy,
)


def _classified_nutrition(
    *, calorie_deficit_kcal: float = 100.0, protein_ratio: float = 1.0
) -> ClassifiedNutritionState:
    return ClassifiedNutritionState(
        calorie_balance_band="moderate",
        protein_sufficiency_band="adequate",
        hydration_band="adequate",
        micronutrient_coverage={},
        coverage_band="full",
        nutrition_status="balanced",
        nutrition_score=0.7,
        calorie_deficit_kcal=calorie_deficit_kcal,
        protein_ratio=protein_ratio,
        hydration_ratio=1.0,
        derivation_path="nutrition_intake_raw",
        uncertainty=tuple(),
    )


def test_legacy_signature_emits_no_locators() -> None:
    result = evaluate_nutrition_policy(_classified_nutrition())
    assert result.evidence_locators is None


def test_always_emit_nutrition_row_locator_on_normal_path() -> None:
    result = evaluate_nutrition_policy(
        _classified_nutrition(),
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        nutrition_today_row_version="2026-05-07T20:00:00Z",
    )
    assert result.forced_action is None
    assert result.evidence_locators is not None
    assert len(result.evidence_locators) == 1
    loc = result.evidence_locators[0]
    assert loc["table"] == "accepted_nutrition_state_daily"
    assert loc["pk"] == {"as_of_date": "2026-05-07", "user_id": "u_local_1"}
    assert "column" not in loc
    validate_locator(loc)


def test_extreme_deficiency_emits_row_plus_calories_plus_protein_locators() -> None:
    # Trigger: deficit >= 500 AND protein_ratio < 0.7
    result = evaluate_nutrition_policy(
        _classified_nutrition(calorie_deficit_kcal=800.0, protein_ratio=0.5),
        meals_count=4,
        is_end_of_day=True,
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        nutrition_today_row_version="2026-05-07T20:00:00Z",
    )
    assert result.forced_action == "escalate_for_user_review"
    assert result.forced_action_detail is not None
    assert (
        result.forced_action_detail["reason_token"]
        == "extreme_deficiency_detected"
    )
    assert result.evidence_locators is not None
    assert len(result.evidence_locators) == 3
    row_loc, cal_loc, pro_loc = result.evidence_locators
    assert "column" not in row_loc
    assert cal_loc["column"] == "calories"
    assert pro_loc["column"] == "protein_g"
    assert cal_loc["pk"] == row_loc["pk"]
    assert pro_loc["pk"] == row_loc["pk"]
    for loc in result.evidence_locators:
        validate_locator(loc)


def test_partial_day_suppression_keeps_row_level_locator() -> None:
    # Same trigger conditions BUT meals_count=1 + is_end_of_day=False
    # → rule yields with partial_day_caveat. Always-emit row-level
    # locator stays; column-level citations are skipped.
    result = evaluate_nutrition_policy(
        _classified_nutrition(calorie_deficit_kcal=800.0, protein_ratio=0.5),
        meals_count=1,
        is_end_of_day=False,
        for_date_iso="2026-05-07",
        user_id="u_local_1",
        nutrition_today_row_version="2026-05-07T20:00:00Z",
    )
    # Rule did NOT fire
    assert result.forced_action is None
    assert result.evidence_locators is not None
    assert len(result.evidence_locators) == 1
    assert "column" not in result.evidence_locators[0]
