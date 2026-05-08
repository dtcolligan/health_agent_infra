"""Running domain schemas.

Per Phase 2 step 1, the running domain ships **frozen** typed shapes that
conform to the Phase-1 write-surface contracts in
``health_agent_infra.core.schemas`` (``BoundedRecommendation`` /
``DomainProposal``). They narrow ``action`` to ``RunningActionKind`` and
default ``domain`` to ``"running"``; field sets are otherwise byte-identical
to ``BOUNDED_RECOMMENDATION_FIELDS`` / ``DOMAIN_PROPOSAL_FIELDS``.

Why frozen here when ``TrainingRecommendation`` is still legacy-mutable: the
frozen contracts are the Phase-2 target shape, and the recovery legacy shape
is awaiting its own migration (folded into synthesis activation, step 4).
Landing the new domain on the legacy shape would cost a second migration
later for no gain.

Contract invariants enforced by ``verification/tests/test_running_schemas.py``:

  - ``RUNNING_ACTION_KINDS`` matches the plan §4 Phase 2 v1 enum exactly.
  - ``RunningProposal`` field set == ``DOMAIN_PROPOSAL_FIELDS``.
  - ``RunningRecommendation`` field set == ``BOUNDED_RECOMMENDATION_FIELDS``.
  - Both shapes are frozen, ``domain`` defaults to ``"running"``, and the
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


RUNNING_PROPOSAL_SCHEMA_VERSION = "running_proposal.v1"
RUNNING_RECOMMENDATION_SCHEMA_VERSION = "running_recommendation.v1"


# v1 action enum per plan §4 Phase 2 deliverable 2. Kept as a tuple constant
# in addition to the ``Literal`` so tests and the synthesis runtime can
# iterate / membership-check without re-parsing the type alias.
RUNNING_ACTION_KINDS: tuple[str, ...] = (
    "proceed_with_planned_run",
    "downgrade_intervals_to_tempo",
    "downgrade_to_easy_aerobic",
    "cross_train_instead",
    "rest_day_recommended",
    "defer_decision_insufficient_signal",
    "escalate_for_user_review",
)


RunningActionKind = Literal[
    "proceed_with_planned_run",
    "downgrade_intervals_to_tempo",
    "downgrade_to_easy_aerobic",
    "cross_train_instead",
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
class RunningProposal:
    """Pre-synthesis running proposal — conforms to ``DomainProposal``.

    Emitted by the running-readiness skill, validated and appended to
    ``proposal_log`` by ``hai propose`` (Phase 2 step 4). The runtime
    applies any X-rule mutations mechanically; the proposal itself
    carries no mutation fields and no ``follow_up`` / ``daily_plan_id``.
    """

    schema_version: str
    proposal_id: str
    user_id: str
    for_date: date
    action: RunningActionKind
    action_detail: Optional[dict[str, Any]]
    rationale: tuple[str, ...]
    confidence: Confidence
    uncertainty: tuple[str, ...]
    policy_decisions: tuple[PolicyDecisionRecord, ...]
    domain: Literal["running"] = "running"
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
class RunningRecommendation:
    """Post-synthesis running recommendation — conforms to ``BoundedRecommendation``.

    Written into ``recommendation_log`` as part of the atomic
    ``hai synthesize`` transaction (Phase 2 step 4). ``daily_plan_id`` is
    NULL pre-commit and set in the same transaction once synthesis assigns
    the canonical plan id.
    """

    schema_version: str
    recommendation_id: str
    user_id: str
    issued_at: datetime
    for_date: date
    action: RunningActionKind
    action_detail: Optional[dict[str, Any]]
    rationale: tuple[str, ...]
    confidence: Confidence
    uncertainty: tuple[str, ...]
    follow_up: FollowUpRecord
    policy_decisions: tuple[PolicyDecisionRecord, ...]
    domain: Literal["running"] = "running"
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
