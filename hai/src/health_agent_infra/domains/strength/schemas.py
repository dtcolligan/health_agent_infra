"""Strength domain schemas.

Phase 4 step 3. Mirrors the sleep / stress / running domain shape:
frozen typed ``StrengthProposal`` + ``StrengthRecommendation`` that
conform byte-for-byte to the Phase-1 write-surface contracts in
``health_agent_infra.core.schemas`` (``DOMAIN_PROPOSAL_FIELDS`` /
``BOUNDED_RECOMMENDATION_FIELDS``). They narrow ``action`` to
``StrengthActionKind`` and default ``domain`` to ``"strength"``.

Invariants enforced by ``verification/tests/test_strength_schemas.py``:

  - ``STRENGTH_ACTION_KINDS`` matches the plan §4 Phase 4 deliverable 5
    v1 enum exactly.
  - ``StrengthProposal`` field set == ``DOMAIN_PROPOSAL_FIELDS``.
  - ``StrengthRecommendation`` field set == ``BOUNDED_RECOMMENDATION_FIELDS``.
  - Both shapes are frozen, ``domain`` defaults to ``"strength"``, and
    the proposal carries no ``follow_up`` / ``daily_plan_id`` /
    mutation field.
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


STRENGTH_PROPOSAL_SCHEMA_VERSION = "strength_proposal.v1"
STRENGTH_RECOMMENDATION_SCHEMA_VERSION = "strength_recommendation.v1"


# v1 action enum per plan §4 Phase 4 deliverable 5.
STRENGTH_ACTION_KINDS: tuple[str, ...] = (
    "proceed_with_planned_session",
    "downgrade_to_technique_or_accessory",
    "downgrade_to_moderate_load",
    "rest_day_recommended",
    "defer_decision_insufficient_signal",
    "escalate_for_user_review",
)


StrengthActionKind = Literal[
    "proceed_with_planned_session",
    "downgrade_to_technique_or_accessory",
    "downgrade_to_moderate_load",
    "rest_day_recommended",
    "defer_decision_insufficient_signal",
    "escalate_for_user_review",
]


def _decisions_to_dicts(
    decisions: tuple[PolicyDecisionRecord, ...],
) -> list[dict[str, Any]]:
    return [
        {"rule_id": d.rule_id, "decision": d.decision, "note": d.note}
        for d in decisions
    ]


@dataclass(frozen=True)
class StrengthProposal:
    """Pre-synthesis strength proposal — conforms to ``DomainProposal``.

    Emitted by the strength-readiness skill, validated and appended to
    ``proposal_log`` by ``hai propose``. Carries no mutation fields and
    no ``follow_up`` / ``daily_plan_id``.
    """

    schema_version: str
    proposal_id: str
    user_id: str
    for_date: date
    action: StrengthActionKind
    action_detail: Optional[dict[str, Any]]
    rationale: tuple[str, ...]
    confidence: Confidence
    uncertainty: tuple[str, ...]
    policy_decisions: tuple[PolicyDecisionRecord, ...]
    domain: Literal["strength"] = "strength"
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
class StrengthRecommendation:
    """Post-synthesis strength recommendation — conforms to
    ``BoundedRecommendation``.

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
    action: StrengthActionKind
    action_detail: Optional[dict[str, Any]]
    rationale: tuple[str, ...]
    confidence: Confidence
    uncertainty: tuple[str, ...]
    follow_up: FollowUpRecord
    policy_decisions: tuple[PolicyDecisionRecord, ...]
    domain: Literal["strength"] = "strength"
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
