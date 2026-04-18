"""Nutrition domain — intake / classify / policy / signals.

Phase 5 lit up classify + policy + signals under the Phase 2.5 retrieval-
gate outcome: v1 is macros-only (meal-level intake + USDA food taxonomy
defer to a post-v1 release). Intake (``hai intake nutrition``) was
shipped in 7C.2 and remains the canonical v1 path for daily-macro
logging.
"""

from health_agent_infra.domains.nutrition.classify import (
    ClassifiedNutritionState,
    classify_nutrition_state,
)
from health_agent_infra.domains.nutrition.policy import (
    NutritionPolicyResult,
    evaluate_nutrition_policy,
)
from health_agent_infra.domains.nutrition.signals import (
    derive_nutrition_signals,
)

__all__ = [
    "ClassifiedNutritionState",
    "NutritionPolicyResult",
    "classify_nutrition_state",
    "derive_nutrition_signals",
    "evaluate_nutrition_policy",
]
