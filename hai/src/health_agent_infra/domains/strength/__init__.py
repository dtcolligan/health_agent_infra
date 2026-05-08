"""Strength domain — classify / policy / intake / taxonomy match.

Phase 4 lit up this namespace end-to-end: intake (7C.1), taxonomy
resolution (step 4), classify + policy (step 3), and snapshot signals
(step 5).
"""

from health_agent_infra.domains.strength.classify import (
    ClassifiedStrengthState,
    classify_strength_state,
)
from health_agent_infra.domains.strength.policy import (
    StrengthPolicyResult,
    evaluate_strength_policy,
)
from health_agent_infra.domains.strength.signals import (
    MUSCLE_GROUPS,
    derive_strength_signals,
)

__all__ = [
    "ClassifiedStrengthState",
    "MUSCLE_GROUPS",
    "StrengthPolicyResult",
    "classify_strength_state",
    "derive_strength_signals",
    "evaluate_strength_policy",
]
