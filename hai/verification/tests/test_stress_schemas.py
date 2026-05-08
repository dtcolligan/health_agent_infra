"""Invariant tests for the stress domain schemas (Phase 3 step 4).

Locks the boundary properties for the new domain before step 5 wires
stress into the snapshot + synthesis layers. Specifically:

  1. ``StressProposal`` and ``StressRecommendation`` conform exactly to
     the frozen field sets declared in ``health_agent_infra.core.schemas``
     (``DOMAIN_PROPOSAL_FIELDS`` / ``BOUNDED_RECOMMENDATION_FIELDS``).
  2. The action enum matches the plan §4 Phase 3 deliverable 4 v1 list.
  3. Skills do not own mutation logic — the proposal carries no banned
     mutation field, no ``follow_up``, no ``daily_plan_id``.
  4. ``domain`` is anchored to ``"stress"`` and both shapes are frozen.
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
from health_agent_infra.domains.stress.schemas import (
    STRESS_ACTION_KINDS,
    STRESS_PROPOSAL_SCHEMA_VERSION,
    STRESS_RECOMMENDATION_SCHEMA_VERSION,
    StressProposal,
    StressRecommendation,
)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

USER = "u_local_1"
AS_OF = date(2026, 4, 18)


def _now() -> datetime:
    return datetime(2026, 4, 18, 12, 0, 0, tzinfo=timezone.utc)


def _follow_up() -> FollowUpRecord:
    return FollowUpRecord(
        review_at=_now(),
        review_question="Did today's stress feel manageable?",
        review_event_id=f"rev_{AS_OF.isoformat()}_{USER}_stress_01",
    )


def _decisions() -> tuple[PolicyDecisionRecord, ...]:
    return (
        PolicyDecisionRecord(
            rule_id="require_min_coverage", decision="allow", note="full",
        ),
    )


def _proposal(**overrides) -> StressProposal:
    base = dict(
        schema_version=STRESS_PROPOSAL_SCHEMA_VERSION,
        proposal_id=f"prop_{AS_OF.isoformat()}_{USER}_stress_01",
        user_id=USER,
        for_date=AS_OF,
        action="maintain_routine",
        action_detail=None,
        rationale=("garmin_stress=low",),
        confidence="moderate",
        uncertainty=(),
        policy_decisions=_decisions(),
    )
    base.update(overrides)
    return StressProposal(**base)


def _recommendation(**overrides) -> StressRecommendation:
    base = dict(
        schema_version=STRESS_RECOMMENDATION_SCHEMA_VERSION,
        recommendation_id=f"rec_{AS_OF.isoformat()}_{USER}_stress",
        user_id=USER,
        issued_at=_now(),
        for_date=AS_OF,
        action="maintain_routine",
        action_detail=None,
        rationale=("garmin_stress=low",),
        confidence="high",
        uncertainty=(),
        follow_up=_follow_up(),
        policy_decisions=_decisions(),
    )
    base.update(overrides)
    return StressRecommendation(**base)


def _field_names(cls) -> set[str]:
    assert is_dataclass(cls)
    return {f.name for f in fields(cls)}


# ---------------------------------------------------------------------------
# 1. Field-set conformance to frozen contracts
# ---------------------------------------------------------------------------

def test_stress_proposal_field_set_matches_domain_proposal_contract():
    assert _field_names(StressProposal) == set(DOMAIN_PROPOSAL_FIELDS)


def test_stress_recommendation_field_set_matches_bounded_recommendation_contract():
    assert _field_names(StressRecommendation) == set(BOUNDED_RECOMMENDATION_FIELDS)


# ---------------------------------------------------------------------------
# 2. Action enum exactly matches plan §4 Phase 3 v1 list
# ---------------------------------------------------------------------------

_EXPECTED_STRESS_ACTIONS = (
    "maintain_routine",
    "add_low_intensity_recovery",
    "schedule_decompression_time",
    "escalate_for_user_review",
    "defer_decision_insufficient_signal",
)


def test_stress_action_kinds_match_plan_v1_list_exactly():
    """Plan §4 Phase 3 deliverable 4 fixes the enum. A drift here is a
    plan-violation, not a code-style nit."""

    assert STRESS_ACTION_KINDS == _EXPECTED_STRESS_ACTIONS


def test_stress_action_kinds_count_is_five():
    assert len(STRESS_ACTION_KINDS) == 5


def test_stress_action_kinds_includes_escalate_for_user_review():
    """Unlike sleep, stress intentionally keeps
    ``escalate_for_user_review`` in v1 — sustained very-high stress is
    the R-escalation path and forces that action directly."""

    assert "escalate_for_user_review" in STRESS_ACTION_KINDS


def test_stress_proposal_accepts_each_v1_action():
    for action in STRESS_ACTION_KINDS:
        prop = _proposal(action=action)
        assert prop.action == action


def test_stress_recommendation_accepts_each_v1_action():
    for action in STRESS_ACTION_KINDS:
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


def test_stress_proposal_has_no_mutation_field():
    overlap = _field_names(StressProposal) & _BANNED_MUTATION_FIELDS
    assert not overlap, (
        f"StressProposal has a banned mutation field: {sorted(overlap)}. "
        "Skills do not own mutation logic — the runtime applies X-rule "
        "mutations via x_rule_firing rows, not via skill payloads."
    )


def test_stress_recommendation_has_no_mutation_field():
    overlap = _field_names(StressRecommendation) & _BANNED_MUTATION_FIELDS
    assert not overlap


def test_stress_proposal_has_no_follow_up():
    assert "follow_up" not in _field_names(StressProposal)


def test_stress_proposal_has_no_daily_plan_id_at_write_time():
    assert "daily_plan_id" not in _field_names(StressProposal)


def test_stress_recommendation_has_follow_up_and_daily_plan_id():
    rec_fields = _field_names(StressRecommendation)
    assert "follow_up" in rec_fields
    assert "daily_plan_id" in rec_fields


# ---------------------------------------------------------------------------
# 4. Domain anchored, shapes frozen
# ---------------------------------------------------------------------------

def test_stress_proposal_domain_defaults_to_stress():
    assert _proposal().domain == "stress"


def test_stress_recommendation_domain_defaults_to_stress():
    assert _recommendation().domain == "stress"


def test_stress_proposal_is_frozen():
    prop = _proposal()
    with pytest.raises(FrozenInstanceError):
        prop.action = "maintain_routine"  # type: ignore[misc]


def test_stress_recommendation_is_frozen():
    rec = _recommendation()
    with pytest.raises(FrozenInstanceError):
        rec.action = "maintain_routine"  # type: ignore[misc]


def test_stress_recommendation_daily_plan_id_defaults_to_none():
    assert _recommendation().daily_plan_id is None


def test_stress_recommendation_accepts_daily_plan_id_from_canonical_helper():
    pid = canonical_daily_plan_id(AS_OF, USER)
    rec = _recommendation(daily_plan_id=pid)
    assert rec.daily_plan_id == pid


# ---------------------------------------------------------------------------
# 5. to_dict round-trip surface stable for persistence
# ---------------------------------------------------------------------------

def test_stress_proposal_to_dict_keys_match_field_set():
    d = _proposal().to_dict()
    assert set(d.keys()) == set(DOMAIN_PROPOSAL_FIELDS)


def test_stress_recommendation_to_dict_keys_match_field_set():
    d = _recommendation().to_dict()
    assert set(d.keys()) == set(BOUNDED_RECOMMENDATION_FIELDS)


def test_stress_proposal_to_dict_serialises_dates_and_decisions():
    d = _proposal().to_dict()
    assert d["for_date"] == AS_OF.isoformat()
    assert d["domain"] == "stress"
    assert d["policy_decisions"] == [
        {"rule_id": "require_min_coverage", "decision": "allow", "note": "full"},
    ]


def test_stress_recommendation_to_dict_serialises_follow_up_record():
    d = _recommendation().to_dict()
    assert d["follow_up"]["review_question"] == (
        "Did today's stress feel manageable?"
    )
    assert d["follow_up"]["review_at"] == _now().isoformat()
    assert d["follow_up"]["review_event_id"] == (
        f"rev_{AS_OF.isoformat()}_{USER}_stress_01"
    )


def test_stress_recommendation_to_dict_carries_daily_plan_id_when_set():
    pid = canonical_daily_plan_id(AS_OF, USER)
    d = _recommendation(daily_plan_id=pid).to_dict()
    assert d["daily_plan_id"] == pid


def test_stress_proposal_and_recommendation_shapes_do_not_collide():
    proposal_fields = _field_names(StressProposal)
    rec_fields = _field_names(StressRecommendation)

    assert "recommendation_id" not in proposal_fields
    assert "proposal_id" not in rec_fields
    assert rec_fields - proposal_fields >= {
        "recommendation_id", "follow_up", "daily_plan_id", "issued_at",
    }
    assert proposal_fields - rec_fields >= {"proposal_id"}


# ---------------------------------------------------------------------------
# 6. Cross-domain purity: no sleep/running/recovery-only actions leak in
# ---------------------------------------------------------------------------

def test_stress_enum_does_not_contain_other_domain_actions():
    """Stress's enum must not borrow actions from recovery, running, or
    sleep. A cross-domain leak would allow the writeback validator to
    accept an action the stress skill shouldn't emit."""

    foreign_actions = {
        # recovery-only
        "proceed_with_planned_session",
        "downgrade_hard_session_to_zone_2",
        "downgrade_session_to_mobility_only",
        "rest_day_recommended",
        # running-only
        "proceed_with_planned_run",
        "downgrade_intervals_to_tempo",
        "downgrade_to_easy_aerobic",
        "cross_train_instead",
        # sleep-only
        "maintain_schedule",
        "prioritize_wind_down",
        "sleep_debt_repayment_day",
        "earlier_bedtime_target",
    }
    leaked = foreign_actions & set(STRESS_ACTION_KINDS)
    assert not leaked
