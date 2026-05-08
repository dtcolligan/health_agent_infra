"""Stress domain schemas.

Phase 3 step 4. Mirrors the sleep / running / recovery shape: frozen
typed ``StressProposal`` + ``StressRecommendation`` that conform
byte-for-byte to the Phase-1 write-surface contracts in
``health_agent_infra.core.schemas`` (``DOMAIN_PROPOSAL_FIELDS`` /
``BOUNDED_RECOMMENDATION_FIELDS``). They narrow ``action`` to
``StressActionKind`` and default ``domain`` to ``"stress"``.

Invariants enforced by ``verification/tests/test_stress_schemas.py``:

  - ``STRESS_ACTION_KINDS`` matches the plan §4 Phase 3 deliverable 4
    v1 enum exactly.
  - ``StressProposal`` field set == ``DOMAIN_PROPOSAL_FIELDS``.
  - ``StressRecommendation`` field set == ``BOUNDED_RECOMMENDATION_FIELDS``.
  - Both shapes are frozen, ``domain`` defaults to ``"stress"``, and the
    proposal carries no ``follow_up`` / ``daily_plan_id`` / mutation field.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal, Optional

from health_agent_infra.core.schemas import (
    Confidence,
    FollowUpRecord,
    PolicyDecisionRecord,
)


STRESS_PROPOSAL_SCHEMA_VERSION = "stress_proposal.v1"
STRESS_RECOMMENDATION_SCHEMA_VERSION = "stress_recommendation.v1"


# v1 action enum per plan §4 Phase 3 deliverable 4. Unlike sleep, stress
# keeps ``escalate_for_user_review`` — sustained very-high stress is the
# R-escalation path and forces that action directly.
STRESS_ACTION_KINDS: tuple[str, ...] = (
    "maintain_routine",
    "add_low_intensity_recovery",
    "schedule_decompression_time",
    "escalate_for_user_review",
    "defer_decision_insufficient_signal",
)


StressActionKind = Literal[
    "maintain_routine",
    "add_low_intensity_recovery",
    "schedule_decompression_time",
    "escalate_for_user_review",
    "defer_decision_insufficient_signal",
]


def _decisions_to_dicts(
    decisions: tuple[PolicyDecisionRecord, ...],
) -> list[dict[str, Any]]:
    return [
        {"rule_id": d.rule_id, "decision": d.decision, "note": d.note}
        for d in decisions
    ]


@dataclass(frozen=True)
class StressProposal:
    """Pre-synthesis stress proposal — conforms to ``DomainProposal``.

    Emitted by the stress-regulation skill, validated and appended to
    ``proposal_log`` by ``hai propose`` (step 5 wiring). Carries no
    mutation fields and no ``follow_up`` / ``daily_plan_id``.
    """

    schema_version: str
    proposal_id: str
    user_id: str
    for_date: date
    action: StressActionKind
    action_detail: Optional[dict[str, Any]]
    rationale: tuple[str, ...]
    confidence: Confidence
    uncertainty: tuple[str, ...]
    policy_decisions: tuple[PolicyDecisionRecord, ...]
    domain: Literal["stress"] = "stress"
    bounded: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "proposal_id": self.proposal_id,
            "user_id": self.user_id,
            "for_date": self.for_date.isoformat(),
            "domain": self.domain,
            "action": self.action,
            "action_detail": self.action_detail,
            "rationale": list(self.rationale),
            "confidence": self.confidence,
            "uncertainty": list(self.uncertainty),
            "policy_decisions": _decisions_to_dicts(self.policy_decisions),
            "bounded": self.bounded,
        }


@dataclass(frozen=True)
class StressRecommendation:
    """Post-synthesis stress recommendation — conforms to ``BoundedRecommendation``.

    Written into ``recommendation_log`` as part of the atomic
    ``hai synthesize`` transaction. ``daily_plan_id`` is NULL pre-commit
    and set in the same transaction once synthesis assigns the canonical
    plan id.
    """

    schema_version: str
    recommendation_id: str
    user_id: str
    issued_at: datetime
    for_date: date
    action: StressActionKind
    action_detail: Optional[dict[str, Any]]
    rationale: tuple[str, ...]
    confidence: Confidence
    uncertainty: tuple[str, ...]
    follow_up: FollowUpRecord
    policy_decisions: tuple[PolicyDecisionRecord, ...]
    domain: Literal["stress"] = "stress"
    bounded: bool = True
    daily_plan_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "recommendation_id": self.recommendation_id,
            "user_id": self.user_id,
            "issued_at": self.issued_at.isoformat(),
            "for_date": self.for_date.isoformat(),
            "domain": self.domain,
            "action": self.action,
            "action_detail": self.action_detail,
            "rationale": list(self.rationale),
            "confidence": self.confidence,
            "uncertainty": list(self.uncertainty),
            "follow_up": {
                "review_at": self.follow_up.review_at.isoformat(),
                "review_question": self.follow_up.review_question,
                "review_event_id": self.follow_up.review_event_id,
            },
            "policy_decisions": _decisions_to_dicts(self.policy_decisions),
            "bounded": self.bounded,
            "daily_plan_id": self.daily_plan_id,
        }
