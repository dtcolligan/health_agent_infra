"""Invariant tests for the frozen write-surface schemas.

These tests lock in the three boundary properties asked for during the
Codex round-2 review *before* Phase 2 synthesis ships:

1. **Skills do not own mutation logic.** ``DomainProposal`` has no
   field whose name suggests the skill can record a mutation it
   applied. The runtime applies mutations via ``x_rule_firing`` rows,
   not via a skill-supplied payload.

2. **Phase A vs Phase B write boundaries stay separate.**
   ``DomainProposal`` (Phase A input) has no ``follow_up`` and no
   ``daily_plan_id`` at write time. ``BoundedRecommendation``
   (Phase B output) has both. The shapes are distinct enough that a
   proposal cannot be smuggled through a recommendation-validating
   writeback and vice-versa.

3. **Canonical-plan replacement semantics are unambiguous.**
   ``canonical_daily_plan_id(for_date, user_id)`` is deterministic on
   its two inputs only — ``agent_version`` is never part of the key.
   Changing the agent version does not produce a new canonical plan;
   supersession is an explicit opt-in (modeled on the ``superseded_by``
   field).

The tests also lock the field lists against accidental drift and
verify the new shapes match the existing ``TrainingRecommendation``
where they overlap.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import date, datetime, timezone

import pytest

from health_agent_infra.core.schemas import (
    BOUNDED_RECOMMENDATION_FIELDS,
    BoundedRecommendation,
    DAILY_PLAN_FIELDS,
    DOMAIN_PROPOSAL_FIELDS,
    DailyPlan,
    DomainProposal,
    FollowUpRecord,
    PolicyDecisionRecord,
    canonical_daily_plan_id,
)
from health_agent_infra.domains.recovery.schemas import TrainingRecommendation


# ---------------------------------------------------------------------------
# Builders — minimal, default-everything so individual tests can vary one axis
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime(2026, 4, 17, 12, 0, 0, tzinfo=timezone.utc)


def _follow_up() -> FollowUpRecord:
    return FollowUpRecord(
        review_at=_now(),
        review_question="Did today feel right?",
        review_event_id="rev_2026-04-17_u_local_1_rec_1",
    )


def _decisions() -> tuple[PolicyDecisionRecord, ...]:
    return (
        PolicyDecisionRecord(rule_id="require_min_coverage", decision="allow", note="full"),
    )


def _recommendation(**overrides):
    base = dict(
        schema_version="training_recommendation.v1",
        recommendation_id="rec_2026-04-17_u_local_1_recovery",
        user_id="u_local_1",
        issued_at=_now(),
        for_date=date(2026, 4, 17),
        domain="recovery",
        action="proceed_with_planned_session",
        action_detail=None,
        rationale=("sleep_debt=none",),
        confidence="high",
        uncertainty=(),
        follow_up=_follow_up(),
        policy_decisions=_decisions(),
    )
    base.update(overrides)
    return BoundedRecommendation(**base)


def _proposal(**overrides):
    base = dict(
        schema_version="domain_proposal.v1",
        proposal_id="prop_2026-04-17_u_local_1_recovery_01",
        user_id="u_local_1",
        for_date=date(2026, 4, 17),
        domain="recovery",
        action="proceed_with_planned_session",
        action_detail=None,
        rationale=("sleep_debt=none",),
        confidence="moderate",
        uncertainty=(),
        policy_decisions=_decisions(),
    )
    base.update(overrides)
    return DomainProposal(**base)


def _daily_plan(**overrides):
    base = dict(
        daily_plan_id=canonical_daily_plan_id(date(2026, 4, 17), "u_local_1"),
        user_id="u_local_1",
        for_date=date(2026, 4, 17),
        synthesized_at=_now(),
        recommendation_ids=("rec_1", "rec_2"),
        proposal_ids=("prop_1", "prop_2"),
        x_rules_fired=("X1a",),
        synthesis_meta=None,
        agent_version="claude_opus_4_7",
    )
    base.update(overrides)
    return DailyPlan(**base)


# ---------------------------------------------------------------------------
# Frozen-ness (Phase B output cannot be mutated after construction)
# ---------------------------------------------------------------------------

def test_bounded_recommendation_is_frozen():
    rec = _recommendation()
    with pytest.raises(FrozenInstanceError):
        rec.action = "rest_day_recommended"  # type: ignore[misc]


def test_domain_proposal_is_frozen():
    prop = _proposal()
    with pytest.raises(FrozenInstanceError):
        prop.action = "rest_day_recommended"  # type: ignore[misc]


def test_daily_plan_is_frozen():
    plan = _daily_plan()
    with pytest.raises(FrozenInstanceError):
        plan.superseded_by = "plan_other"  # type: ignore[misc]


def test_policy_decision_is_frozen():
    d = PolicyDecisionRecord(rule_id="r1", decision="allow", note="ok")
    with pytest.raises(FrozenInstanceError):
        d.note = "changed"  # type: ignore[misc]


def test_follow_up_is_frozen():
    f = _follow_up()
    with pytest.raises(FrozenInstanceError):
        f.review_question = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Field-list invariants — lock against accidental drift
# ---------------------------------------------------------------------------

def _field_names(cls) -> set[str]:
    assert is_dataclass(cls)
    return {f.name for f in fields(cls)}


def test_bounded_recommendation_fields_match_declared_tuple():
    assert _field_names(BoundedRecommendation) == set(BOUNDED_RECOMMENDATION_FIELDS)


def test_domain_proposal_fields_match_declared_tuple():
    assert _field_names(DomainProposal) == set(DOMAIN_PROPOSAL_FIELDS)


def test_daily_plan_fields_match_declared_tuple():
    assert _field_names(DailyPlan) == set(DAILY_PLAN_FIELDS)


# ---------------------------------------------------------------------------
# INVARIANT 1 — Skills do not own mutation logic
# ---------------------------------------------------------------------------

# Field names a skill-authored payload MUST NOT carry. If a field with any
# of these names appears on DomainProposal or BoundedRecommendation, a
# future skill could smuggle a mutation into the persistence layer under
# the guise of "the skill applied it already."
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


def test_domain_proposal_has_no_mutation_field():
    present = _field_names(DomainProposal)
    overlap = present & _BANNED_MUTATION_FIELDS
    assert not overlap, (
        f"DomainProposal has a banned mutation field: {sorted(overlap)}. "
        f"Skills do not own mutation logic — the runtime applies X-rule "
        f"mutations via x_rule_firing rows, not via skill-supplied payloads."
    )


def test_bounded_recommendation_has_no_mutation_field():
    present = _field_names(BoundedRecommendation)
    overlap = present & _BANNED_MUTATION_FIELDS
    assert not overlap, (
        f"BoundedRecommendation has a banned mutation field: {sorted(overlap)}"
    )


# ---------------------------------------------------------------------------
# INVARIANT 2 — Phase A vs Phase B write boundaries stay separate
# ---------------------------------------------------------------------------

def test_domain_proposal_has_no_follow_up_field():
    """Proposals never schedule reviews; recommendations do."""
    assert "follow_up" not in _field_names(DomainProposal)


def test_domain_proposal_has_no_daily_plan_id_at_write_time():
    """daily_plan_id is assigned by synthesis when proposals are linked
    into a plan — it is not part of the proposal's own write surface.
    """
    assert "daily_plan_id" not in _field_names(DomainProposal)


def test_bounded_recommendation_has_follow_up_field():
    """The Phase B output does schedule a review."""
    assert "follow_up" in _field_names(BoundedRecommendation)


def test_bounded_recommendation_has_daily_plan_id_field():
    """Recommendations carry their plan linkage; it is NULL pre-commit
    and set after the synthesis transaction commits.
    """
    assert "daily_plan_id" in _field_names(BoundedRecommendation)


def test_bounded_recommendation_daily_plan_id_defaults_to_none():
    rec = _recommendation()
    assert rec.daily_plan_id is None


def test_bounded_recommendation_accepts_daily_plan_id_after_synthesis():
    pid = canonical_daily_plan_id(date(2026, 4, 17), "u_local_1")
    rec = _recommendation(daily_plan_id=pid)
    assert rec.daily_plan_id == pid


def test_proposal_and_recommendation_shapes_do_not_collide():
    """A DomainProposal cannot accidentally be a BoundedRecommendation.

    The shapes differ in both field NAME (recommendation_id vs
    proposal_id) and field SET (follow_up, daily_plan_id) so a writeback
    pipeline validating one will never accept the other.
    """

    proposal_fields = _field_names(DomainProposal)
    rec_fields = _field_names(BoundedRecommendation)

    assert "recommendation_id" not in proposal_fields
    assert "proposal_id" not in rec_fields
    # Fields unique to recommendations:
    assert rec_fields - proposal_fields >= {
        "recommendation_id", "follow_up", "daily_plan_id",
    }
    # Fields unique to proposals:
    assert proposal_fields - rec_fields >= {"proposal_id"}


# ---------------------------------------------------------------------------
# INVARIANT 3 — Canonical-plan replacement semantics are unambiguous
# ---------------------------------------------------------------------------

def test_canonical_daily_plan_id_is_deterministic_on_date_and_user():
    pid_a = canonical_daily_plan_id(date(2026, 4, 17), "u_local_1")
    pid_b = canonical_daily_plan_id(date(2026, 4, 17), "u_local_1")
    assert pid_a == pid_b


def test_canonical_daily_plan_id_differs_across_dates():
    pid_a = canonical_daily_plan_id(date(2026, 4, 17), "u_local_1")
    pid_b = canonical_daily_plan_id(date(2026, 4, 18), "u_local_1")
    assert pid_a != pid_b


def test_canonical_daily_plan_id_differs_across_users():
    pid_a = canonical_daily_plan_id(date(2026, 4, 17), "u_local_1")
    pid_b = canonical_daily_plan_id(date(2026, 4, 17), "u_local_2")
    assert pid_a != pid_b


def test_canonical_daily_plan_id_does_not_consume_agent_version():
    """Sanity: the helper signature doesn't take agent_version, full stop.

    A bug in synthesis that added agent_version to the key would have
    to change this helper's signature — caught by type checkers and by
    this test which pins the callable to exactly two positional args.
    """

    import inspect
    sig = inspect.signature(canonical_daily_plan_id)
    params = list(sig.parameters)
    assert params == ["for_date", "user_id"]


def test_daily_plan_records_agent_version_but_two_plans_with_different_versions_share_key():
    """agent_version is recorded per row but is NOT part of uniqueness.

    Two plans for the same (for_date, user_id) with different
    agent_versions would collide on daily_plan_id — that's the intended
    behaviour: reruns replace atomically, they do NOT implicitly version.
    """

    plan_a = _daily_plan(agent_version="claude_opus_4_7")
    plan_b = _daily_plan(agent_version="claude_sonnet_5_0_future")
    assert plan_a.daily_plan_id == plan_b.daily_plan_id
    assert plan_a.agent_version != plan_b.agent_version


def test_daily_plan_superseded_by_defaults_to_none():
    """Supersession is an explicit opt-in; the default canonical plan
    has no ``superseded_by`` pointer.
    """

    plan = _daily_plan()
    assert plan.superseded_by is None


def test_daily_plan_can_point_at_its_successor():
    """``--supersede`` sets this field on the prior canonical plan."""
    plan = _daily_plan(superseded_by="plan_2026-04-17_u_local_1_v2")
    assert plan.superseded_by == "plan_2026-04-17_u_local_1_v2"


# ---------------------------------------------------------------------------
# Existing TrainingRecommendation still validates (no regression)
# ---------------------------------------------------------------------------

def test_training_recommendation_field_names_overlap_bounded_recommendation():
    """The existing TrainingRecommendation shape is a strict subset-plus-some
    of BoundedRecommendation. Specifically, every field on
    TrainingRecommendation has a same-named field on BoundedRecommendation
    (modulo the two new fields: ``daily_plan_id`` + ``domain``).
    """

    training_fields = _field_names(TrainingRecommendation)
    bounded_fields = _field_names(BoundedRecommendation)

    # Every field on the legacy shape is present on the new shape.
    missing_in_bounded = training_fields - bounded_fields
    assert not missing_in_bounded, (
        f"BoundedRecommendation is missing legacy fields: {sorted(missing_in_bounded)}"
    )

    # BoundedRecommendation additions vs legacy.
    additions = bounded_fields - training_fields
    assert additions == {"daily_plan_id", "domain"}, (
        f"Unexpected additions on BoundedRecommendation: {sorted(additions)}"
    )


def test_bounded_recommendation_rationale_is_tuple_not_list():
    """Freezing wrapped mutable-default-factory bugs: rationale is a tuple
    on the new shape so the frozen invariant is meaningful.
    """

    rec = _recommendation(rationale=("a", "b"))
    assert isinstance(rec.rationale, tuple)
    # Can't assign a new tuple either.
    with pytest.raises(FrozenInstanceError):
        rec.rationale = ("c",)  # type: ignore[misc]


def test_domain_proposal_uncertainty_is_tuple():
    prop = _proposal(uncertainty=("hrv_unavailable",))
    assert isinstance(prop.uncertainty, tuple)
