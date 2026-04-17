"""Invariant tests for the running domain schemas (Phase 2 step 1).

Locks the boundary properties for the new domain *before* synthesis activation
in Phase 2 step 4 starts mutating proposal/plan flows. Specifically:

  1. ``RunningProposal`` and ``RunningRecommendation`` conform exactly to the
     frozen field sets declared in ``health_agent_infra.core.schemas``
     (``DOMAIN_PROPOSAL_FIELDS`` / ``BOUNDED_RECOMMENDATION_FIELDS``). A new
     domain that drifted would silently break the synthesis writeback path.
  2. The action enum matches the plan §4 Phase 2 v1 list, so a typo or a
     premature addition (e.g. a 'restructure' action that the plan defers
     to synthesis judgment) is caught at test time, not at agent-output time.
  3. Skills do not own mutation logic — the proposal carries no banned
     mutation field, no ``follow_up``, no ``daily_plan_id``.
  4. ``domain`` is anchored to ``"running"`` and both shapes are frozen, so
     a Phase B post-synthesis mutation attempt would raise rather than
     silently mutate the recommendation.
  5. ``to_dict()`` round-trips cleanly so writeback / proposal_log JSON
     persistence in step 4 has a stable surface.
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
from health_agent_infra.domains.running.schemas import (
    RUNNING_ACTION_KINDS,
    RUNNING_PROPOSAL_SCHEMA_VERSION,
    RUNNING_RECOMMENDATION_SCHEMA_VERSION,
    RunningProposal,
    RunningRecommendation,
)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

USER = "u_local_1"
AS_OF = date(2026, 4, 17)


def _now() -> datetime:
    return datetime(2026, 4, 17, 12, 0, 0, tzinfo=timezone.utc)


def _follow_up() -> FollowUpRecord:
    return FollowUpRecord(
        review_at=_now(),
        review_question="Did today's run feel right?",
        review_event_id=f"rev_{AS_OF.isoformat()}_{USER}_running_01",
    )


def _decisions() -> tuple[PolicyDecisionRecord, ...]:
    return (
        PolicyDecisionRecord(
            rule_id="require_min_coverage", decision="allow", note="full",
        ),
    )


def _proposal(**overrides) -> RunningProposal:
    base = dict(
        schema_version=RUNNING_PROPOSAL_SCHEMA_VERSION,
        proposal_id=f"prop_{AS_OF.isoformat()}_{USER}_running_01",
        user_id=USER,
        for_date=AS_OF,
        action="proceed_with_planned_run",
        action_detail=None,
        rationale=("acwr=stable",),
        confidence="moderate",
        uncertainty=(),
        policy_decisions=_decisions(),
    )
    base.update(overrides)
    return RunningProposal(**base)


def _recommendation(**overrides) -> RunningRecommendation:
    base = dict(
        schema_version=RUNNING_RECOMMENDATION_SCHEMA_VERSION,
        recommendation_id=f"rec_{AS_OF.isoformat()}_{USER}_running",
        user_id=USER,
        issued_at=_now(),
        for_date=AS_OF,
        action="proceed_with_planned_run",
        action_detail=None,
        rationale=("acwr=stable",),
        confidence="high",
        uncertainty=(),
        follow_up=_follow_up(),
        policy_decisions=_decisions(),
    )
    base.update(overrides)
    return RunningRecommendation(**base)


def _field_names(cls) -> set[str]:
    assert is_dataclass(cls)
    return {f.name for f in fields(cls)}


# ---------------------------------------------------------------------------
# 1. Field-set conformance to frozen contracts
# ---------------------------------------------------------------------------

def test_running_proposal_field_set_matches_domain_proposal_contract():
    assert _field_names(RunningProposal) == set(DOMAIN_PROPOSAL_FIELDS)


def test_running_recommendation_field_set_matches_bounded_recommendation_contract():
    assert _field_names(RunningRecommendation) == set(BOUNDED_RECOMMENDATION_FIELDS)


# ---------------------------------------------------------------------------
# 2. Action enum exactly matches plan §4 Phase 2 v1 list
# ---------------------------------------------------------------------------

_EXPECTED_RUNNING_ACTIONS = (
    "proceed_with_planned_run",
    "downgrade_intervals_to_tempo",
    "downgrade_to_easy_aerobic",
    "cross_train_instead",
    "rest_day_recommended",
    "defer_decision_insufficient_signal",
    "escalate_for_user_review",
)


def test_running_action_kinds_match_plan_v1_list_exactly():
    """Plan §4 Phase 2 deliverable 2 fixes the enum. A drift here is a
    plan-violation, not a code-style nit — caught at test time so it
    can't reach an agent prompt or skill markdown."""

    assert RUNNING_ACTION_KINDS == _EXPECTED_RUNNING_ACTIONS


def test_running_action_kinds_count_is_seven():
    """Defensive: the count is part of the contract; a silently-added
    action would still pass the equality check above only if the test
    expectation were also drifted, but a mismatched count wouldn't."""

    assert len(RUNNING_ACTION_KINDS) == 7


def test_running_proposal_accepts_each_v1_action():
    for action in RUNNING_ACTION_KINDS:
        prop = _proposal(action=action)
        assert prop.action == action


def test_running_recommendation_accepts_each_v1_action():
    for action in RUNNING_ACTION_KINDS:
        rec = _recommendation(action=action)
        assert rec.action == action


# ---------------------------------------------------------------------------
# 3. Skills-don't-own-mutation invariants on the new shapes
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


def test_running_proposal_has_no_mutation_field():
    overlap = _field_names(RunningProposal) & _BANNED_MUTATION_FIELDS
    assert not overlap, (
        f"RunningProposal has a banned mutation field: {sorted(overlap)}. "
        "Skills do not own mutation logic — the runtime applies X-rule "
        "mutations via x_rule_firing rows, not via skill payloads."
    )


def test_running_recommendation_has_no_mutation_field():
    overlap = _field_names(RunningRecommendation) & _BANNED_MUTATION_FIELDS
    assert not overlap


def test_running_proposal_has_no_follow_up():
    assert "follow_up" not in _field_names(RunningProposal)


def test_running_proposal_has_no_daily_plan_id_at_write_time():
    assert "daily_plan_id" not in _field_names(RunningProposal)


def test_running_recommendation_has_follow_up_and_daily_plan_id():
    rec_fields = _field_names(RunningRecommendation)
    assert "follow_up" in rec_fields
    assert "daily_plan_id" in rec_fields


# ---------------------------------------------------------------------------
# 4. Domain anchored, shapes frozen
# ---------------------------------------------------------------------------

def test_running_proposal_domain_defaults_to_running():
    assert _proposal().domain == "running"


def test_running_recommendation_domain_defaults_to_running():
    assert _recommendation().domain == "running"


def test_running_proposal_is_frozen():
    prop = _proposal()
    with pytest.raises(FrozenInstanceError):
        prop.action = "rest_day_recommended"  # type: ignore[misc]


def test_running_recommendation_is_frozen():
    rec = _recommendation()
    with pytest.raises(FrozenInstanceError):
        rec.action = "rest_day_recommended"  # type: ignore[misc]


def test_running_recommendation_daily_plan_id_defaults_to_none():
    assert _recommendation().daily_plan_id is None


def test_running_recommendation_accepts_daily_plan_id_from_canonical_helper():
    pid = canonical_daily_plan_id(AS_OF, USER)
    rec = _recommendation(daily_plan_id=pid)
    assert rec.daily_plan_id == pid


# ---------------------------------------------------------------------------
# 5. to_dict round-trip surface stable for step-4 persistence
# ---------------------------------------------------------------------------

def test_running_proposal_to_dict_keys_match_field_set():
    """``to_dict()`` is the persistence surface ``hai propose`` will append
    to ``proposal_log``. Drifting keys is the exact bug class that breaks
    reproject / replay; lock it here."""

    d = _proposal().to_dict()
    assert set(d.keys()) == set(DOMAIN_PROPOSAL_FIELDS)


def test_running_recommendation_to_dict_keys_match_field_set():
    d = _recommendation().to_dict()
    assert set(d.keys()) == set(BOUNDED_RECOMMENDATION_FIELDS)


def test_running_proposal_to_dict_serialises_dates_and_decisions():
    d = _proposal().to_dict()
    assert d["for_date"] == AS_OF.isoformat()
    assert d["domain"] == "running"
    assert d["policy_decisions"] == [
        {"rule_id": "require_min_coverage", "decision": "allow", "note": "full"},
    ]


def test_running_recommendation_to_dict_serialises_follow_up_record():
    d = _recommendation().to_dict()
    assert d["follow_up"]["review_question"] == "Did today's run feel right?"
    assert d["follow_up"]["review_at"] == _now().isoformat()
    assert d["follow_up"]["review_event_id"] == (
        f"rev_{AS_OF.isoformat()}_{USER}_running_01"
    )


def test_running_recommendation_to_dict_carries_daily_plan_id_when_set():
    pid = canonical_daily_plan_id(AS_OF, USER)
    d = _recommendation(daily_plan_id=pid).to_dict()
    assert d["daily_plan_id"] == pid


def test_running_proposal_and_recommendation_shapes_do_not_collide():
    """A RunningProposal is not a RunningRecommendation. The shapes differ
    in identifier name (proposal_id vs recommendation_id) and in the
    follow_up + daily_plan_id fields, so a writeback validating one will
    never silently accept the other."""

    proposal_fields = _field_names(RunningProposal)
    rec_fields = _field_names(RunningRecommendation)

    assert "recommendation_id" not in proposal_fields
    assert "proposal_id" not in rec_fields
    assert rec_fields - proposal_fields >= {
        "recommendation_id", "follow_up", "daily_plan_id", "issued_at",
    }
    assert proposal_fields - rec_fields >= {"proposal_id"}
