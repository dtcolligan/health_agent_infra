"""Invariant tests for the nutrition domain schemas (Phase 5 step 2).

Locks the boundary properties for the macros-only nutrition domain
before step 4 wires nutrition into the snapshot + synthesis layers.

  1. ``NutritionProposal`` and ``NutritionRecommendation`` conform
     exactly to the frozen field sets declared in
     ``health_agent_infra.core.schemas`` (``DOMAIN_PROPOSAL_FIELDS`` /
     ``BOUNDED_RECOMMENDATION_FIELDS``).
  2. The action enum matches the v1 macros-only collapse (Phase 2.5
     retrieval-gate outcome — see domains/nutrition/schemas.py module
     docstring).
  3. Skills do not own mutation logic — the proposal carries no banned
     mutation field, no ``follow_up``, no ``daily_plan_id``.
  4. ``domain`` is anchored to ``"nutrition"`` and both shapes are
     frozen.
  5. ``to_dict()`` round-trips cleanly so writeback / proposal_log JSON
     persistence has a stable surface.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import date, datetime, timezone

import pytest

from health_agent_infra.core.schemas import (
    BOUNDED_RECOMMENDATION_FIELDS,
    DOMAIN_PROPOSAL_FIELDS,
    FollowUpRecord,
    PolicyDecisionRecord,
    canonical_daily_plan_id,
)
from health_agent_infra.domains.nutrition.schemas import (
    NUTRITION_ACTION_KINDS,
    NUTRITION_PROPOSAL_SCHEMA_VERSION,
    NUTRITION_RECOMMENDATION_SCHEMA_VERSION,
    NutritionProposal,
    NutritionRecommendation,
)


USER = "u_local_1"
AS_OF = date(2026, 4, 18)


def _now() -> datetime:
    return datetime(2026, 4, 18, 12, 0, 0, tzinfo=timezone.utc)


def _follow_up() -> FollowUpRecord:
    return FollowUpRecord(
        review_at=_now(),
        review_question="Did today's macros land near your targets?",
        review_event_id=f"rev_{AS_OF.isoformat()}_{USER}_nutrition_01",
    )


def _decisions() -> tuple[PolicyDecisionRecord, ...]:
    return (
        PolicyDecisionRecord(
            rule_id="require_min_coverage", decision="allow", note="full",
        ),
    )


def _proposal(**overrides) -> NutritionProposal:
    base = dict(
        schema_version=NUTRITION_PROPOSAL_SCHEMA_VERSION,
        proposal_id=f"prop_{AS_OF.isoformat()}_{USER}_nutrition_01",
        user_id=USER,
        for_date=AS_OF,
        action="maintain_targets",
        action_detail=None,
        rationale=("calorie_balance_band=met",),
        confidence="moderate",
        uncertainty=(),
        policy_decisions=_decisions(),
    )
    base.update(overrides)
    return NutritionProposal(**base)


def _recommendation(**overrides) -> NutritionRecommendation:
    base = dict(
        schema_version=NUTRITION_RECOMMENDATION_SCHEMA_VERSION,
        recommendation_id=f"rec_{AS_OF.isoformat()}_{USER}_nutrition",
        user_id=USER,
        issued_at=_now(),
        for_date=AS_OF,
        action="maintain_targets",
        action_detail=None,
        rationale=("calorie_balance_band=met",),
        confidence="high",
        uncertainty=(),
        follow_up=_follow_up(),
        policy_decisions=_decisions(),
    )
    base.update(overrides)
    return NutritionRecommendation(**base)


def _field_names(cls) -> set[str]:
    assert is_dataclass(cls)
    return {f.name for f in fields(cls)}


# ---------------------------------------------------------------------------
# 1. Field-set conformance to frozen contracts
# ---------------------------------------------------------------------------

def test_nutrition_proposal_field_set_matches_domain_proposal_contract():
    assert _field_names(NutritionProposal) == set(DOMAIN_PROPOSAL_FIELDS)


def test_nutrition_recommendation_field_set_matches_bounded_recommendation_contract():
    assert _field_names(NutritionRecommendation) == set(BOUNDED_RECOMMENDATION_FIELDS)


# ---------------------------------------------------------------------------
# 2. Action enum exactly matches v1 macros-only collapse
# ---------------------------------------------------------------------------

_EXPECTED_NUTRITION_ACTIONS = (
    "maintain_targets",
    "increase_protein_intake",
    "increase_hydration",
    "reduce_calorie_deficit",
    "defer_decision_insufficient_signal",
    "escalate_for_user_review",
)


def test_nutrition_action_kinds_match_macros_only_v1_list_exactly():
    assert NUTRITION_ACTION_KINDS == _EXPECTED_NUTRITION_ACTIONS


def test_nutrition_action_kinds_count_is_six():
    assert len(NUTRITION_ACTION_KINDS) == 6


def test_nutrition_action_kinds_exclude_meal_level_variants():
    """Phase 2.5 retrieval gate failed, so no parametrised
    ``address_deficit_<micro>`` / ``reduce_<micro>`` variants can
    appear in v1 — the data layer does not carry micronutrient
    evidence."""

    for action in NUTRITION_ACTION_KINDS:
        assert "address_deficit_" not in action
        # ``reduce_calorie_deficit`` is legitimate (macros); anything
        # else matching reduce_<x> where x is a micronutrient is not.
        assert action in _EXPECTED_NUTRITION_ACTIONS


def test_nutrition_proposal_accepts_each_v1_action():
    for action in NUTRITION_ACTION_KINDS:
        prop = _proposal(action=action)
        assert prop.action == action


def test_nutrition_recommendation_accepts_each_v1_action():
    for action in NUTRITION_ACTION_KINDS:
        rec = _recommendation(action=action)
        assert rec.action == action


# ---------------------------------------------------------------------------
# 3. Skills-don't-own-mutation invariants
# ---------------------------------------------------------------------------

_BANNED_MUTATION_FIELDS = {
    "x_rule_mutations_applied",
    "x_rule_mutations_applied_by_skill",
    "synthesis_mutation",
    "applied_mutation",
    "skill_applied_mutations",
    "mutation",
    "mutations",
    "overrides",
    "skill_override",
}


def test_nutrition_proposal_has_no_mutation_field():
    overlap = _field_names(NutritionProposal) & _BANNED_MUTATION_FIELDS
    assert not overlap, (
        f"NutritionProposal has a banned mutation field: {sorted(overlap)}. "
        "Skills do not own mutation logic — the runtime applies X-rule "
        "mutations via x_rule_firing rows, not via skill payloads."
    )


def test_nutrition_recommendation_has_no_mutation_field():
    overlap = _field_names(NutritionRecommendation) & _BANNED_MUTATION_FIELDS
    assert not overlap


def test_nutrition_proposal_has_no_follow_up():
    assert "follow_up" not in _field_names(NutritionProposal)


def test_nutrition_proposal_has_no_daily_plan_id_at_write_time():
    assert "daily_plan_id" not in _field_names(NutritionProposal)


def test_nutrition_recommendation_has_follow_up_and_daily_plan_id():
    rec_fields = _field_names(NutritionRecommendation)
    assert "follow_up" in rec_fields
    assert "daily_plan_id" in rec_fields


# ---------------------------------------------------------------------------
# 4. Domain anchored, shapes frozen
# ---------------------------------------------------------------------------

def test_nutrition_proposal_domain_defaults_to_nutrition():
    assert _proposal().domain == "nutrition"


def test_nutrition_recommendation_domain_defaults_to_nutrition():
    assert _recommendation().domain == "nutrition"


def test_nutrition_proposal_is_frozen():
    prop = _proposal()
    with pytest.raises(FrozenInstanceError):
        prop.action = "rest_day_recommended"  # type: ignore[misc]


def test_nutrition_recommendation_is_frozen():
    rec = _recommendation()
    with pytest.raises(FrozenInstanceError):
        rec.action = "rest_day_recommended"  # type: ignore[misc]


def test_nutrition_recommendation_daily_plan_id_defaults_to_none():
    assert _recommendation().daily_plan_id is None


def test_nutrition_recommendation_accepts_daily_plan_id_from_canonical_helper():
    pid = canonical_daily_plan_id(AS_OF, USER)
    rec = _recommendation(daily_plan_id=pid)
    assert rec.daily_plan_id == pid


# ---------------------------------------------------------------------------
# 5. to_dict round-trip surface stable for persistence
# ---------------------------------------------------------------------------

def test_nutrition_proposal_to_dict_keys_match_field_set():
    d = _proposal().to_dict()
    assert set(d.keys()) == set(DOMAIN_PROPOSAL_FIELDS)


def test_nutrition_recommendation_to_dict_keys_match_field_set():
    d = _recommendation().to_dict()
    assert set(d.keys()) == set(BOUNDED_RECOMMENDATION_FIELDS)


def test_nutrition_proposal_to_dict_serialises_dates_and_decisions():
    d = _proposal().to_dict()
    assert d["for_date"] == AS_OF.isoformat()
    assert d["domain"] == "nutrition"
    assert d["policy_decisions"] == [
        {"rule_id": "require_min_coverage", "decision": "allow", "note": "full"},
    ]


def test_nutrition_recommendation_to_dict_serialises_follow_up_record():
    d = _recommendation().to_dict()
    assert d["follow_up"]["review_question"] == (
        "Did today's macros land near your targets?"
    )
    assert d["follow_up"]["review_at"] == _now().isoformat()
    assert d["follow_up"]["review_event_id"] == (
        f"rev_{AS_OF.isoformat()}_{USER}_nutrition_01"
    )


def test_nutrition_recommendation_to_dict_carries_daily_plan_id_when_set():
    pid = canonical_daily_plan_id(AS_OF, USER)
    d = _recommendation(daily_plan_id=pid).to_dict()
    assert d["daily_plan_id"] == pid


def test_nutrition_proposal_and_recommendation_shapes_do_not_collide():
    proposal_fields = _field_names(NutritionProposal)
    rec_fields = _field_names(NutritionRecommendation)

    assert "recommendation_id" not in proposal_fields
    assert "proposal_id" not in rec_fields
    assert rec_fields - proposal_fields >= {
        "recommendation_id", "follow_up", "daily_plan_id", "issued_at",
    }
