"""Recovery domain schemas.

Houses the recovery-specific recommendation shape and its action enum. The
shared write-surface contracts (``BoundedRecommendation``, ``DomainProposal``,
``DailyPlan``) and cross-domain runtime types live under
``health_agent_infra.core.schemas``.

``TrainingRecommendation`` is the pre-synthesis recovery recommendation carried
forward from the flagship loop. The frozen ``BoundedRecommendation`` in core is
the Phase 2 target shape; ``TrainingRecommendation`` must match its field set
(subclasses may narrow ``action`` to an enum but may not add or remove fields).
The invariant tests in ``safety/tests/test_core_schemas.py`` enforce this.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from typing import Literal, Optional

from health_agent_infra.core.schemas import (
    Confidence,
    FollowUp,
    PolicyDecision,
)


ActionKind = Literal[
    "proceed_with_planned_session",
    "downgrade_hard_session_to_zone_2",
    "downgrade_session_to_mobility_only",
    "rest_day_recommended",
    "defer_decision_insufficient_signal",
    "escalate_for_user_review",
]


@dataclass
class TrainingRecommendation:
    """Agent-produced bounded recommendation.

    The agent composes this object from ``CleanedEvidence`` + ``RawSummary``
    by following the recovery-readiness skill. ``hai synthesize`` validates
    the shape before persisting — validation is the runtime's contract check
    on the agent's output.
    """

    schema_version: str
    recommendation_id: str
    user_id: str
    issued_at: datetime
    for_date: date
    action: ActionKind
    action_detail: Optional[dict]
    rationale: list[str]
    confidence: Confidence
    uncertainty: list[str]
    follow_up: FollowUp
    policy_decisions: list[PolicyDecision]
    bounded: bool = True

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "recommendation_id": self.recommendation_id,
            "user_id": self.user_id,
            "issued_at": self.issued_at.isoformat(),
            "for_date": self.for_date.isoformat(),
            "action": self.action,
            "action_detail": self.action_detail,
            "rationale": list(self.rationale),
            "confidence": self.confidence,
            "uncertainty": list(self.uncertainty),
            "follow_up": self.follow_up.to_dict(),
            "policy_decisions": [asdict(d) for d in self.policy_decisions],
            "bounded": self.bounded,
        }
