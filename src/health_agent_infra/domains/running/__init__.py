"""Running domain — schemas + (future) classify/policy.

Phase 2 step 1 lands only the frozen typed shapes
(``RunningProposal``, ``RunningRecommendation``) and the v1 action enum.
``classify.py`` and ``policy.py`` arrive in step 2; the running-readiness
skill arrives in step 3.
"""

from health_agent_infra.domains.running.schemas import (
    RUNNING_ACTION_KINDS,
    RUNNING_PROPOSAL_SCHEMA_VERSION,
    RUNNING_RECOMMENDATION_SCHEMA_VERSION,
    RunningActionKind,
    RunningProposal,
    RunningRecommendation,
)

__all__ = [
    "RUNNING_ACTION_KINDS",
    "RUNNING_PROPOSAL_SCHEMA_VERSION",
    "RUNNING_RECOMMENDATION_SCHEMA_VERSION",
    "RunningActionKind",
    "RunningProposal",
    "RunningRecommendation",
]
