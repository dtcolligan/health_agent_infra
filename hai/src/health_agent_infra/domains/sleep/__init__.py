"""Sleep domain — schemas, classify, policy.

Phase 3 step 3. Sleep is now a first-class deterministic+judgment
split: classifier + policy own every numerical band and R-rule firing;
the sleep-quality skill owns judgment (rationale prose, action-matrix
selection, vendor cross-check). Step 5 will wire this domain into
``hai state snapshot`` + the synthesis layer and repoint X1
(sleep → training) at ``accepted_sleep_state_daily`` data.
"""

from health_agent_infra.domains.sleep.classify import (
    ClassifiedSleepState,
    classify_sleep_state,
)
from health_agent_infra.domains.sleep.policy import (
    PolicyDecision,
    SleepPolicyResult,
    evaluate_sleep_policy,
)
from health_agent_infra.domains.sleep.schemas import (
    SLEEP_ACTION_KINDS,
    SLEEP_PROPOSAL_SCHEMA_VERSION,
    SLEEP_RECOMMENDATION_SCHEMA_VERSION,
    SleepActionKind,
    SleepProposal,
    SleepRecommendation,
)
from health_agent_infra.domains.sleep.signals import derive_sleep_signals

__all__ = [
    "ClassifiedSleepState",
    "PolicyDecision",
    "SLEEP_ACTION_KINDS",
    "SLEEP_PROPOSAL_SCHEMA_VERSION",
    "SLEEP_RECOMMENDATION_SCHEMA_VERSION",
    "SleepActionKind",
    "SleepPolicyResult",
    "SleepProposal",
    "SleepRecommendation",
    "classify_sleep_state",
    "derive_sleep_signals",
    "evaluate_sleep_policy",
]
