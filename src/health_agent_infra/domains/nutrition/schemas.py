"""Nutrition domain schemas.

Phase 5 step 2, under the Phase 2.5 retrieval-gate outcome (macros-only).
Mirrors the sleep / stress / running / strength domain shape: frozen
typed ``NutritionProposal`` + ``NutritionRecommendation`` that conform
byte-for-byte to the Phase-1 write-surface contracts in
``health_agent_infra.core.schemas``
(``DOMAIN_PROPOSAL_FIELDS`` / ``BOUNDED_RECOMMENDATION_FIELDS``).

Action enum collapse vs the plan text. Plan §4 Phase 5 deliverable 6
lists parametrised templates ``address_deficit_<nutrient>`` and
``reduce_<nutrient>`` intended to cover micronutrient-specific guidance
in the full meal-level build. The Phase 2.5 retrieval gate landed under
the 60% threshold, so meal-level + the micronutrient evidence path
defer to a post-v1 release. The v1 enum is therefore the concrete
macros-only collapse of those templates — no speculative
nutrient-specific variants the data layer cannot support honestly.

Invariants enforced by ``safety/tests/test_nutrition_schemas.py``:

  - ``NUTRITION_ACTION_KINDS`` is the v1 macros-only enum (6 values).
  - ``NutritionProposal`` field set == ``DOMAIN_PROPOSAL_FIELDS``.
  - ``NutritionRecommendation`` field set == ``BOUNDED_RECOMMENDATION_FIELDS``.
  - Both shapes are frozen, ``domain`` defaults to ``"nutrition"``, and
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


NUTRITION_PROPOSAL_SCHEMA_VERSION = "nutrition_proposal.v1"
NUTRITION_RECOMMENDATION_SCHEMA_VERSION = "nutrition_recommendation.v1"


# v1 macros-only action enum. See module docstring for the collapse
# reasoning. Any future meal-level release re-opens the enum with an
# additive migration — existing v1 recommendations continue to validate.
NUTRITION_ACTION_KINDS: tuple[str, ...] = (
    "maintain_targets",
    "increase_protein_intake",
    "increase_hydration",
    "reduce_calorie_deficit",
    "defer_decision_insufficient_signal",
    "escalate_for_user_review",
)


NutritionActionKind = Literal[
    "maintain_targets",
    "increase_protein_intake",
    "increase_hydration",
    "reduce_calorie_deficit",
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
class NutritionProposal:
    """Pre-synthesis nutrition proposal — conforms to ``DomainProposal``.

    Emitted by the nutrition-alignment skill, validated and appended to
    ``proposal_log`` by ``hai propose``. Carries no mutation fields and
    no ``follow_up`` / ``daily_plan_id``.
    """

    schema_version: str
    proposal_id: str
    user_id: str
    for_date: date
    action: NutritionActionKind
    action_detail: Optional[dict[str, Any]]
    rationale: tuple[str, ...]
    confidence: Confidence
    uncertainty: tuple[str, ...]
    policy_decisions: tuple[PolicyDecisionRecord, ...]
    domain: Literal["nutrition"] = "nutrition"
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
class NutritionRecommendation:
    """Post-synthesis nutrition recommendation — conforms to
    ``BoundedRecommendation``.

    Written into ``recommendation_log`` as part of the atomic
    ``hai synthesize`` transaction. ``daily_plan_id`` is NULL pre-commit
    and set in the same transaction once synthesis assigns the canonical
    plan id.

    X9 (Phase B ``post_adjust``) is the one rule that may mutate the
    ``action_detail`` after synthesis assigns the final ``action`` — it
    may not change ``action`` itself. The guard is enforced in
    :mod:`health_agent_infra.core.synthesis_policy`.
    """

    schema_version: str
    recommendation_id: str
    user_id: str
    issued_at: datetime
    for_date: date
    action: NutritionActionKind
    action_detail: Optional[dict[str, Any]]
    rationale: tuple[str, ...]
    confidence: Confidence
    uncertainty: tuple[str, ...]
    follow_up: FollowUpRecord
    policy_decisions: tuple[PolicyDecisionRecord, ...]
    domain: Literal["nutrition"] = "nutrition"
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
