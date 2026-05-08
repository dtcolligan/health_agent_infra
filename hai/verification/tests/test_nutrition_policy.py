"""Nutrition-domain policy tests (Phase 5 step 2, macros-only v1).

Pins the R-rule contract + forced-action / capped-confidence semantics
that the nutrition-alignment skill must honour. Mirrors
``test_strength_policy.py`` / ``test_sleep_policy.py`` in style: each
rule has allow + fire cases, the forced-action precedence is locked,
and the confidence cap is independent of action-forcing.

Three v1 rules:

  - ``require_min_coverage``
  - ``no_high_confidence_on_sparse_signal``
  - ``extreme_deficiency_escalation``
"""

from __future__ import annotations

from typing import Any, Optional

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS
from health_agent_infra.domains.nutrition.classify import (
    ClassifiedNutritionState,
    classify_nutrition_state,
)
from health_agent_infra.domains.nutrition.policy import (
    PolicyDecision,
    evaluate_nutrition_policy,
)


def _row(
    *,
    calories: Optional[float] = 2400.0,
    protein_g: Optional[float] = 140.0,
    hydration_l: Optional[float] = 2.5,
    meals_count: Optional[int] = 3,
    derivation_path: Optional[str] = "daily_macros",
) -> dict[str, Any]:
    return {
        "calories": calories,
        "protein_g": protein_g,
        "carbs_g": 280.0,
        "fat_g": 75.0,
        "hydration_l": hydration_l,
        "meals_count": meals_count,
        "derivation_path": derivation_path,
    }


def _classify(today_row: Optional[dict[str, Any]]) -> ClassifiedNutritionState:
    return classify_nutrition_state({"today_row": today_row})


def _rule(
    decisions: tuple[PolicyDecision, ...], rule_id: str,
) -> PolicyDecision:
    matches = [d for d in decisions if d.rule_id == rule_id]
    assert len(matches) == 1, (
        f"expected exactly one {rule_id} decision; got {len(matches)}"
    )
    return matches[0]


# ---------------------------------------------------------------------------
# R-coverage gate
# ---------------------------------------------------------------------------

def test_r_coverage_blocks_when_no_row():
    classified = _classify(None)
    result = evaluate_nutrition_policy(classified)
    cov = _rule(result.policy_decisions, "require_min_coverage")
    assert cov.decision == "block"
    assert result.forced_action == "defer_decision_insufficient_signal"


def test_r_coverage_allows_on_full_row():
    classified = _classify(_row())
    result = evaluate_nutrition_policy(classified)
    cov = _rule(result.policy_decisions, "require_min_coverage")
    assert cov.decision == "allow"
    assert result.forced_action is None


def test_r_coverage_allows_on_partial_row():
    # Row present, hydration not logged → coverage=partial; coverage gate allows.
    classified = _classify(_row(hydration_l=None))
    result = evaluate_nutrition_policy(classified)
    cov = _rule(result.policy_decisions, "require_min_coverage")
    assert cov.decision == "allow"


# ---------------------------------------------------------------------------
# R-sparse confidence cap
# ---------------------------------------------------------------------------

def test_r_sparse_caps_confidence_on_sparse_coverage():
    classified = _classify(_row(hydration_l=None, meals_count=None))
    result = evaluate_nutrition_policy(classified)
    sparse = _rule(result.policy_decisions, "no_high_confidence_on_sparse_signal")
    assert sparse.decision == "soften"
    assert result.capped_confidence == "moderate"


def test_r_sparse_caps_confidence_on_partial_coverage():
    """Partial coverage (one optional field missing) is still a
    confidence-capping signal in v1 — the user's full-context signal
    is incomplete even though classify can land a calorie/protein verdict."""

    classified = _classify(_row(hydration_l=None))
    result = evaluate_nutrition_policy(classified)
    assert result.capped_confidence == "moderate"


def test_r_sparse_allows_on_full_coverage():
    classified = _classify(_row())
    result = evaluate_nutrition_policy(classified)
    sparse = _rule(result.policy_decisions, "no_high_confidence_on_sparse_signal")
    assert sparse.decision == "allow"
    assert result.capped_confidence is None


# ---------------------------------------------------------------------------
# R-extreme-deficiency
# ---------------------------------------------------------------------------

def test_r_extreme_deficiency_escalates_on_big_deficit_and_very_low_protein():
    """The combination is the overreaching-deficit signal. Individually,
    either triggers the band verdict; together, they force the escalate
    action."""

    classified = _classify(_row(calories=1900.0, protein_g=91.0))
    result = evaluate_nutrition_policy(classified)
    extreme = _rule(result.policy_decisions, "extreme_deficiency_escalation")
    assert extreme.decision == "escalate"
    assert result.forced_action == "escalate_for_user_review"
    assert result.forced_action_detail is not None
    assert result.forced_action_detail["reason_token"] == "extreme_deficiency_detected"
    assert result.forced_action_detail["calorie_deficit_kcal"] == 500.0


def test_r_extreme_deficiency_allows_when_only_calorie_deficit_high():
    classified = _classify(_row(calories=1900.0, protein_g=140.0))
    result = evaluate_nutrition_policy(classified)
    extreme = _rule(result.policy_decisions, "extreme_deficiency_escalation")
    assert extreme.decision == "allow"
    assert result.forced_action is None


def test_r_extreme_deficiency_allows_when_only_protein_very_low():
    classified = _classify(_row(protein_g=91.0))
    result = evaluate_nutrition_policy(classified)
    extreme = _rule(result.policy_decisions, "extreme_deficiency_escalation")
    assert extreme.decision == "allow"
    assert result.forced_action is None


def test_r_extreme_deficiency_allows_when_signals_missing():
    """Classifier's band=unknown does NOT escalate — absence of evidence
    is not evidence of extreme deficiency."""

    classified = _classify(_row(calories=None, protein_g=None))
    result = evaluate_nutrition_policy(classified)
    extreme = _rule(result.policy_decisions, "extreme_deficiency_escalation")
    assert extreme.decision == "allow"


# ---------------------------------------------------------------------------
# Precedence: R-extreme-deficiency overrides R-coverage defer
# ---------------------------------------------------------------------------

def test_r_extreme_deficiency_overrides_coverage_defer_when_both_fire():
    """Manufactured edge case — malformed row where calories + protein
    are concrete but optional fields are both null AND we fabricate
    a scenario where R-coverage would have fired. Since coverage=sparse
    is an allow (not a block), this is mostly a safety documentation
    test — R-coverage blocks only when coverage=insufficient (no row or
    null core macros), which by construction means no calorie_deficit
    value, so R-extreme-deficiency cannot fire. The test codifies that
    contract: you cannot have both a block defer AND an escalate at once."""

    classified = _classify(None)  # no row → coverage=insufficient
    result = evaluate_nutrition_policy(classified)
    # R-coverage blocks + forces defer; R-extreme-deficiency cannot
    # trigger without calorie_deficit so it allows.
    assert result.forced_action == "defer_decision_insufficient_signal"


# ---------------------------------------------------------------------------
# Deterministic + config-driven
# ---------------------------------------------------------------------------

def test_custom_thresholds_tighten_extreme_deficiency_trigger():
    from copy import deepcopy
    t = deepcopy(DEFAULT_THRESHOLDS)
    # Lower the deficit threshold — 300 kcal instead of 500.
    t["policy"]["nutrition"]["r_extreme_deficiency_min_calorie_deficit_kcal"] = 300.0

    classified = classify_nutrition_state(
        {"today_row": _row(calories=2100.0, protein_g=91.0)},  # 300 kcal deficit
        thresholds=t,
    )
    result = evaluate_nutrition_policy(classified, thresholds=t)
    assert result.forced_action == "escalate_for_user_review"

    # Defaults must not have drifted.
    assert (
        DEFAULT_THRESHOLDS["policy"]["nutrition"][
            "r_extreme_deficiency_min_calorie_deficit_kcal"
        ]
        == 500.0
    )


def test_policy_result_is_immutable():
    """Frozen dataclass contract — the skill cannot mutate the policy
    result after reading it."""

    classified = _classify(_row())
    result = evaluate_nutrition_policy(classified)
    with pytest.raises(Exception):
        result.forced_action = "rest_day_recommended"  # type: ignore[misc]


def test_policy_decisions_ordered_by_evaluation_sequence():
    classified = _classify(_row())
    result = evaluate_nutrition_policy(classified)
    rule_ids = [d.rule_id for d in result.policy_decisions]
    assert rule_ids == [
        "require_min_coverage",
        "extreme_deficiency_escalation",
        "no_high_confidence_on_sparse_signal",
    ]
