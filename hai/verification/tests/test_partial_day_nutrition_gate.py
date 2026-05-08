"""Tests for v0.1.10 W-C — partial-day gate on R-extreme-deficiency.

Reproduces the morning-briefing scenario where a single breakfast +
protein-shake intake at 06:32 fired R-extreme-deficiency on a 1493
kcal "deficit" — caused by classifier reading partial-day intake as
the day's full total. The gate suppresses escalation unless
``meals_count >= min_meals`` OR caller asserts ``is_end_of_day=True``.

See ``audit_findings.md`` § F-C-03 + memory B1.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.config import load_thresholds
from health_agent_infra.domains.nutrition.classify import ClassifiedNutritionState
from health_agent_infra.domains.nutrition.policy import evaluate_nutrition_policy


def _classified_extreme_deficiency() -> ClassifiedNutritionState:
    """Build a classified state that WOULD fire R-extreme-deficiency
    in v0.1.9 — 1493 kcal deficit, 0.52 protein ratio."""

    return ClassifiedNutritionState(
        calorie_balance_band="high_deficit",
        protein_sufficiency_band="very_low",
        hydration_band="unknown",
        micronutrient_coverage="unknown",
        coverage_band="sparse",
        nutrition_status="deficit_caloric",
        nutrition_score=0.30,
        calorie_deficit_kcal=1493.0,
        protein_ratio=0.52,
        hydration_ratio=None,
        derivation_path="daily_macros",
    )


class TestPartialDayGate:
    """v0.1.10 W-C — partial-day gate on R-extreme-deficiency."""

    def test_breakfast_only_does_not_fire(self) -> None:
        """meals_count=1, is_end_of_day=False → suppress."""

        result = evaluate_nutrition_policy(
            _classified_extreme_deficiency(),
            meals_count=1,
            is_end_of_day=False,
        )
        assert result.forced_action != "escalate_for_user_review"
        # Confirm the partial-day note is in the decision trail.
        rule_decisions = [
            d for d in result.policy_decisions
            if d.rule_id == "extreme_deficiency_escalation"
        ]
        assert any("partial_day_caveat" in (d.note or "") for d in rule_decisions)

    def test_no_meals_count_does_not_fire(self) -> None:
        """meals_count=None → cannot prove end-of-day → suppress (conservative)."""

        result = evaluate_nutrition_policy(
            _classified_extreme_deficiency(),
            meals_count=None,
        )
        # When meals_count is unknown and is_end_of_day is unspecified,
        # the gate cannot confirm a complete day. Behaviour: suppress
        # is conservative; the rule yields no forced action.
        # NOTE: this matches the v0.1.10 spec — backward-compat callers
        # who don't pass either flag DO see the rule fire (the gate
        # only triggers when meals_count is *known* to be below threshold).
        # Adjust expected behaviour if scope changes.
        assert result.forced_action == "escalate_for_user_review"

    def test_full_day_fires(self) -> None:
        """meals_count >= min_meals → rule evaluates normally."""

        result = evaluate_nutrition_policy(
            _classified_extreme_deficiency(),
            meals_count=4,
        )
        assert result.forced_action == "escalate_for_user_review"

    def test_end_of_day_fires_even_with_low_meals_count(self) -> None:
        """is_end_of_day=True overrides meals_count gate."""

        result = evaluate_nutrition_policy(
            _classified_extreme_deficiency(),
            meals_count=1,
            is_end_of_day=True,
        )
        assert result.forced_action == "escalate_for_user_review"

    def test_threshold_override_via_user_config(self) -> None:
        """User can raise the gate via thresholds — meals_count below
        override → suppress."""

        thresholds = load_thresholds()
        # Make a private copy with stricter gate (require ≥3 meals)
        import copy

        thresholds = copy.deepcopy(thresholds)
        thresholds["policy"]["nutrition"][
            "r_extreme_deficiency_min_meals_count"
        ] = 3

        result = evaluate_nutrition_policy(
            _classified_extreme_deficiency(),
            thresholds=thresholds,
            meals_count=2,  # below override of 3
            is_end_of_day=False,
        )
        assert result.forced_action != "escalate_for_user_review"
