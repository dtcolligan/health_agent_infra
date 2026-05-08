"""Stress domain — schemas, classify, policy, intake.

Phase 3 step 4. Stress is now a first-class deterministic+judgment
split: classifier + policy own every numerical band and R-rule firing;
the stress-regulation skill owns judgment (rationale prose,
action-matrix selection). Step 5 will wire this domain into
``hai state snapshot`` + the synthesis layer and repoint X7
(stress → cap confidence) at ``accepted_stress_state_daily`` data via
the classified band.
"""

from health_agent_infra.domains.stress.classify import (
    ClassifiedStressState,
    classify_stress_state,
)
from health_agent_infra.domains.stress.policy import (
    PolicyDecision,
    StressPolicyResult,
    evaluate_stress_policy,
)
from health_agent_infra.domains.stress.schemas import (
    STRESS_ACTION_KINDS,
    STRESS_PROPOSAL_SCHEMA_VERSION,
    STRESS_RECOMMENDATION_SCHEMA_VERSION,
    StressActionKind,
    StressProposal,
    StressRecommendation,
)
from health_agent_infra.domains.stress.signals import derive_stress_signals

__all__ = [
    "ClassifiedStressState",
    "PolicyDecision",
    "STRESS_ACTION_KINDS",
    "STRESS_PROPOSAL_SCHEMA_VERSION",
    "STRESS_RECOMMENDATION_SCHEMA_VERSION",
    "StressActionKind",
    "StressPolicyResult",
    "StressProposal",
    "StressRecommendation",
    "classify_stress_state",
    "derive_stress_signals",
    "evaluate_stress_policy",
]
