"""D4 test #7 — nutrition never gets cold-start relaxation.

Unlike running / strength / stress, nutrition's defer is not lifted
for first-run users. D4 §Nutrition: "Macro targets genuinely require
a macros row; fabricating a recommendation without knowing what
someone ate is medically and behaviorally wrong."

Two shapes of assertion:

1. The nutrition policy's public signature does NOT accept a
   ``cold_start_context`` kwarg — so a future refactor can't silently
   add the relaxation. (Regression guard — `evaluate_nutrition_policy`
   should not mirror running/strength/stress's relaxation surface.)

2. On insufficient coverage, the nutrition policy forces defer
   regardless of what cold-start context the caller might wish it
   honoured.

Plus coverage of the cold-start-specific defer message used by
``hai today`` when ``nutrition.cold_start=True``.
"""

from __future__ import annotations

import inspect

import pytest

from health_agent_infra.core.narration import defer_unblock_hint
from health_agent_infra.core.narration.templates import (
    cold_start_nutrition_defer_hint,
)
from health_agent_infra.domains.nutrition.classify import (
    ClassifiedNutritionState,
)
from health_agent_infra.domains.nutrition.policy import (
    evaluate_nutrition_policy,
)


def _classified(coverage_band: str = "insufficient") -> ClassifiedNutritionState:
    return ClassifiedNutritionState(
        calorie_balance_band="unknown",
        protein_sufficiency_band="unknown",
        hydration_band="unknown",
        micronutrient_coverage="unavailable_at_source",
        coverage_band=coverage_band,
        nutrition_status="unknown",
        nutrition_score=None,
        calorie_deficit_kcal=None,
        protein_ratio=None,
        hydration_ratio=None,
        derivation_path=None,
        uncertainty=(),
    )


# ---------------------------------------------------------------------------
# Regression guard — nutrition policy does NOT have a cold-start hook
# ---------------------------------------------------------------------------


def test_evaluate_nutrition_policy_has_no_cold_start_kwarg():
    """D4 §Nutrition explicitly rejects cold-start relaxation. The
    public signature must not accept a ``cold_start_context`` kwarg —
    if a future refactor tries to add one, this test fires loudly and
    forces a D4 revisit rather than a silent capability change.
    """

    sig = inspect.signature(evaluate_nutrition_policy)
    assert "cold_start_context" not in sig.parameters, (
        "nutrition policy gained a cold_start_context kwarg — D4 "
        "§Nutrition rejected cold-start relaxation. Revisit the "
        "design doc before proceeding."
    )


def test_insufficient_coverage_forces_defer_without_cold_start_escape():
    """Insufficient coverage always produces the forced defer — no
    kwarg path to dodge it."""

    result = evaluate_nutrition_policy(_classified(coverage_band="insufficient"))
    assert result.forced_action == "defer_decision_insufficient_signal"


# ---------------------------------------------------------------------------
# Cold-start-specific defer message — "I'd be making it up"
# ---------------------------------------------------------------------------


def test_cold_start_nutrition_defer_hint_uses_explicit_language():
    """D4 §Nutrition specifies the exact framing: the user sees why
    we can't recommend, not a generic defer line."""

    hint = cold_start_nutrition_defer_hint()
    lowered = hint.lower()
    # Explicit that the system would be fabricating a recommendation.
    assert "made up" in lowered or "fabricate" in lowered or "making it up" in lowered
    # Points at the unblock command.
    assert "hai intake nutrition" in hint


def test_generic_defer_unblock_hint_still_exists_for_non_cold_start_nutrition():
    """A user who has graduated out of cold-start but still has no
    nutrition row today gets the generic defer hint, not the
    make-up-specific one."""

    generic = defer_unblock_hint("nutrition")
    assert "hai intake nutrition" in generic
    # Generic hint should not emit the cold-start framing.
    assert "made up" not in generic.lower()
    assert "making it up" not in generic.lower()
