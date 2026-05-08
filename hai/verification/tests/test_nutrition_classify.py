"""Nutrition-domain classifier tests (Phase 5 step 2, macros-only v1).

Pins the band boundaries + status / score composition that the
nutrition-alignment skill treats as source of truth. Mirrors
``test_strength_classify.py`` / ``test_sleep_classify.py`` in style:
each band has at-boundary + inside-band cases, and the composite
status/score falls out cleanly from the band inputs.

Derivation_path=daily_macros is the only v1 path; micronutrient_coverage
always resolves to ``unavailable_at_source`` regardless of other inputs.
"""

from __future__ import annotations

from typing import Any, Optional

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS, load_thresholds
from health_agent_infra.domains.nutrition.classify import (
    ClassifiedNutritionState,
    classify_nutrition_state,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _row(
    *,
    calories: Optional[float] = 2400.0,
    protein_g: Optional[float] = 140.0,
    carbs_g: Optional[float] = 280.0,
    fat_g: Optional[float] = 75.0,
    hydration_l: Optional[float] = 2.5,
    meals_count: Optional[int] = 3,
    derivation_path: Optional[str] = "daily_macros",
) -> dict[str, Any]:
    return {
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "hydration_l": hydration_l,
        "meals_count": meals_count,
        "derivation_path": derivation_path,
    }


def _classify(today_row: Optional[dict[str, Any]] = None, **extras) -> ClassifiedNutritionState:
    signals = {"today_row": today_row, **extras}
    return classify_nutrition_state(signals)


# ---------------------------------------------------------------------------
# Coverage band — insufficient / sparse / partial / full
# ---------------------------------------------------------------------------

def test_coverage_insufficient_when_no_row():
    c = _classify(None)
    assert c.coverage_band == "insufficient"
    assert c.nutrition_status == "unknown"
    assert c.nutrition_score is None


def test_coverage_sparse_when_row_but_no_optional_fields():
    c = _classify(_row(hydration_l=None, meals_count=None))
    assert c.coverage_band == "sparse"


def test_coverage_partial_when_row_with_one_optional_field():
    c = _classify(_row(hydration_l=None))
    assert c.coverage_band == "partial"
    c2 = _classify(_row(meals_count=None))
    assert c2.coverage_band == "partial"


def test_coverage_full_when_row_with_both_optional_fields():
    c = _classify(_row())
    assert c.coverage_band == "full"


def test_coverage_insufficient_when_core_macro_null():
    c = _classify(_row(calories=None))
    assert c.coverage_band == "insufficient"


# ---------------------------------------------------------------------------
# Calorie balance band
# ---------------------------------------------------------------------------

def test_calorie_band_met_near_target():
    c = _classify(_row(calories=2400.0))  # deficit = 0
    assert c.calorie_balance_band == "met"
    assert c.calorie_deficit_kcal == 0.0


def test_calorie_band_mild_deficit_at_100_kcal_below():
    c = _classify(_row(calories=2300.0))  # deficit = 100
    assert c.calorie_balance_band == "mild_deficit"


def test_calorie_band_moderate_deficit_at_300_kcal_below():
    c = _classify(_row(calories=2100.0))  # deficit = 300
    assert c.calorie_balance_band == "moderate_deficit"


def test_calorie_band_high_deficit_at_x2_threshold():
    """X2 trigger alignment: at exactly a 500-kcal deficit, the band is
    ``high_deficit`` — X2's deficit_kcal_min matches this boundary so the
    X-rule fires precisely when the classifier names high_deficit."""

    c = _classify(_row(calories=1900.0))  # deficit = 500
    assert c.calorie_balance_band == "high_deficit"


def test_calorie_band_surplus_at_300_kcal_above():
    c = _classify(_row(calories=2700.0))  # actual - target = +300
    assert c.calorie_balance_band == "surplus"


def test_calorie_band_unknown_when_calories_null():
    c = _classify({
        **_row(calories=None),
    })
    assert c.calorie_balance_band == "unknown"
    assert c.calorie_deficit_kcal is None


# ---------------------------------------------------------------------------
# Protein sufficiency band
# ---------------------------------------------------------------------------

def test_protein_band_met_at_target():
    c = _classify(_row(protein_g=140.0))
    assert c.protein_sufficiency_band == "met"
    assert c.protein_ratio == 1.0


def test_protein_band_low_below_target_but_above_x2_threshold():
    # 0.85 ratio = 119g at 140g target. Between 0.7 and 1.0 → low.
    c = _classify(_row(protein_g=119.0))
    assert c.protein_sufficiency_band == "low"


def test_protein_band_very_low_at_x2_threshold():
    """X2 trigger alignment: at exactly a 0.7 protein ratio the band
    lands in ``very_low`` — X2's protein_ratio_max matches this
    boundary so the X-rule fires precisely when the classifier names
    very_low."""

    # ratio = 0.65 < 0.7 → very_low.
    c = _classify(_row(protein_g=91.0))  # 91 / 140 = 0.65
    assert c.protein_sufficiency_band == "very_low"


def test_protein_band_unknown_when_protein_null():
    c = _classify(_row(protein_g=None))
    assert c.protein_sufficiency_band == "unknown"
    assert c.protein_ratio is None


# ---------------------------------------------------------------------------
# Hydration band — absent log is not a deficit
# ---------------------------------------------------------------------------

def test_hydration_band_met_at_target():
    c = _classify(_row(hydration_l=2.5))
    assert c.hydration_band == "met"


def test_hydration_band_low_below_threshold():
    # 1.5 / 2.5 = 0.6 < 0.75 → low.
    c = _classify(_row(hydration_l=1.5))
    assert c.hydration_band == "low"


def test_hydration_band_unknown_when_not_logged():
    """Absence of a hydration log must surface as unknown, not low —
    the user may have logged elsewhere or simply skipped the field."""

    c = _classify(_row(hydration_l=None))
    assert c.hydration_band == "unknown"
    assert "hydration_not_logged" in c.uncertainty


# ---------------------------------------------------------------------------
# Micronutrient coverage — always unavailable_at_source in v1
# ---------------------------------------------------------------------------

def test_micronutrient_coverage_unavailable_under_daily_macros():
    """The v1 derivation carries no micronutrient evidence. The classifier
    must emit ``unavailable_at_source`` regardless of macro values — the
    skill reads this to decide whether to surface micro rationale at all."""

    c = _classify(_row(derivation_path="daily_macros"))
    assert c.micronutrient_coverage == "unavailable_at_source"
    assert "micronutrients_unavailable_at_source" in c.uncertainty


def test_micronutrient_coverage_unknown_for_unrecognised_derivation():
    """Defensive — a malformed row with an unknown derivation_path
    surfaces loudly rather than silently classifying as available."""

    c = _classify(_row(derivation_path="hypothetical_meal_log"))
    assert c.micronutrient_coverage == "unknown"


def test_micronutrient_coverage_unknown_when_derivation_path_missing():
    c = _classify(_row(derivation_path=None))
    assert c.micronutrient_coverage == "unknown"


# ---------------------------------------------------------------------------
# Composite status + score
# ---------------------------------------------------------------------------

def test_status_aligned_when_all_bands_met():
    c = _classify(_row())
    assert c.nutrition_status == "aligned"
    assert c.nutrition_score is not None
    assert c.nutrition_score >= 0.95


def test_status_deficit_caloric_takes_precedence_over_protein_gap():
    """Precedence: a big calorie gap shows up as deficit_caloric even
    when protein is also low. The individual bands stay on the
    classified_state for the skill to read."""

    c = _classify(_row(calories=1900.0, protein_g=91.0))  # high deficit + very low protein
    assert c.nutrition_status == "deficit_caloric"
    assert c.calorie_balance_band == "high_deficit"
    assert c.protein_sufficiency_band == "very_low"


def test_status_protein_gap_when_calories_met_but_protein_low():
    c = _classify(_row(protein_g=119.0))
    assert c.nutrition_status == "protein_gap"


def test_status_under_hydrated_when_only_hydration_low():
    c = _classify(_row(hydration_l=1.5))
    assert c.nutrition_status == "under_hydrated"


def test_status_surplus_when_calories_well_above_target():
    c = _classify(_row(calories=2800.0))
    assert c.nutrition_status == "surplus"


def test_score_decreases_with_penalty_accumulation():
    """Higher-severity bands must produce a strictly lower score than
    mixed-severity combinations, so the skill + downstream policies
    can read ``score < 0.5`` as a real stress signal."""

    aligned = _classify(_row()).nutrition_score
    protein_gap = _classify(_row(protein_g=119.0)).nutrition_score
    high_deficit = _classify(_row(calories=1900.0, protein_g=91.0)).nutrition_score

    assert aligned is not None and protein_gap is not None and high_deficit is not None
    assert aligned > protein_gap > high_deficit


def test_score_none_when_coverage_insufficient():
    c = _classify(None)
    assert c.nutrition_score is None


# ---------------------------------------------------------------------------
# Thresholds + uncertainty
# ---------------------------------------------------------------------------

def test_custom_thresholds_override_defaults_without_mutation():
    """Load defaults, build a classifier with a user override that
    raises the protein target to 180g. At the same 140g raw protein,
    the band should flip from ``met`` to ``very_low``."""

    from copy import deepcopy
    t = deepcopy(DEFAULT_THRESHOLDS)
    t["classify"]["nutrition"]["targets"]["protein_target_g"] = 220.0

    c = classify_nutrition_state(
        {"today_row": _row(protein_g=140.0)}, thresholds=t,
    )
    # 140 / 220 = 0.636 < 0.7 → very_low
    assert c.protein_sufficiency_band == "very_low"

    # Defaults must not have drifted.
    assert DEFAULT_THRESHOLDS["classify"]["nutrition"]["targets"]["protein_target_g"] == 140.0


def test_uncertainty_is_sorted_and_deduplicated():
    c = _classify(_row(calories=None, protein_g=None, hydration_l=None, derivation_path=None))
    u = list(c.uncertainty)
    assert u == sorted(set(u))


def test_goal_domain_resistance_training_surfaces_on_uncertainty():
    c = _classify(_row(), goal_domain="resistance_training")
    assert "goal_domain_is_resistance_training" in c.uncertainty


# ---------------------------------------------------------------------------
# Load thresholds integration smoke
# ---------------------------------------------------------------------------

def test_load_thresholds_surfaces_nutrition_section():
    t = load_thresholds()
    nutrition = t["classify"]["nutrition"]
    assert nutrition["targets"]["calorie_target_kcal"] == 2400.0
    assert nutrition["targets"]["protein_target_g"] == 140.0
    assert nutrition["protein_sufficiency_band"]["very_low_max_ratio"] == 0.7
    assert nutrition["calorie_balance_band"]["high_deficit_min_kcal"] == 500.0
