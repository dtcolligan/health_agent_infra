"""Running domain — schemas, classify, policy.

Phase 2 step 1 landed the frozen typed shapes (``RunningProposal``,
``RunningRecommendation``) and the v1 action enum. Step 2 adds the
deterministic classifier and the three R-rules
(``require_min_coverage``, ``acwr_spike_escalation``,
``no_high_confidence_on_sparse_signal``). The running-readiness skill
arrives in step 3.
"""

from health_agent_infra.domains.running.classify import (
    ClassifiedRunningState,
    classify_running_state,
)
from health_agent_infra.domains.running.policy import (
    PolicyDecision,
    RunningPolicyResult,
    evaluate_running_policy,
)
from health_agent_infra.domains.running.schemas import (
    RUNNING_ACTION_KINDS,
    RUNNING_PROPOSAL_SCHEMA_VERSION,
    RUNNING_RECOMMENDATION_SCHEMA_VERSION,
    RunningActionKind,
    RunningProposal,
    RunningRecommendation,
)
from health_agent_infra.domains.running.signals import derive_running_signals

__all__ = [
    "ClassifiedRunningState",
    "PolicyDecision",
    "RUNNING_ACTION_KINDS",
    "RUNNING_PROPOSAL_SCHEMA_VERSION",
    "RUNNING_RECOMMENDATION_SCHEMA_VERSION",
    "RunningActionKind",
    "RunningPolicyResult",
    "RunningProposal",
    "RunningRecommendation",
    "classify_running_state",
    "derive_running_signals",
    "evaluate_running_policy",
]
