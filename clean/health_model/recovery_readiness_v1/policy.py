"""POLICY layer.

Executable policy rules per reporting/docs/minimal_policy_rules.md.
Rules are pure functions. The evaluator runs them in the spec's order
and returns an audit trail used by the RECOMMEND layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from health_model.recovery_readiness_v1.schemas import (
    ActionKind,
    Confidence,
    PolicyDecision,
    RecoveryState,
)

DIAGNOSIS_BANNED_TOKENS = {
    "diagnosis",
    "diagnose",
    "diagnosed",
    "syndrome",
    "disease",
    "disorder",
    "condition",
    "infection",
    "illness",
    "sick",
}

ALLOWED_ACTIONS: set[ActionKind] = {
    "proceed_with_planned_session",
    "downgrade_hard_session_to_zone_2",
    "downgrade_session_to_mobility_only",
    "rest_day_recommended",
    "defer_decision_insufficient_signal",
    "escalate_for_user_review",
}


@dataclass
class Proposal:
    """A tentative recommendation that policy mutates via `soften` decisions."""

    action: ActionKind
    action_detail: Optional[dict]
    rationale: list[str]
    confidence: Confidence
    uncertainty: list[str]
    follow_up_present: bool
    follow_up_within_24h: bool


@dataclass
class PolicyEvaluation:
    decisions: list[PolicyDecision]
    mutated: Proposal
    blocked: bool
    escalate_to: Optional[ActionKind] = None
    escalate_detail: Optional[dict] = None


PolicyRuleFn = Callable[[RecoveryState, Proposal, "_Context"], Optional[PolicyDecision]]


@dataclass
class _Context:
    mutated: Proposal
    blocked: bool = False
    escalate_to: Optional[ActionKind] = None
    escalate_detail: Optional[dict] = None


def rule_require_min_coverage(state: RecoveryState, _: Proposal, ctx: _Context) -> Optional[PolicyDecision]:
    if state.signal_quality.coverage == "insufficient":
        ctx.blocked = True
        return PolicyDecision(
            rule_id="require_min_coverage",
            decision="block",
            note="coverage=insufficient; required inputs missing",
        )
    presence = (
        "required inputs present"
        if state.signal_quality.required_inputs_present
        else "required inputs partial"
    )
    return PolicyDecision(
        rule_id="require_min_coverage",
        decision="allow",
        note=f"coverage={state.signal_quality.coverage}, {presence}",
    )


def rule_no_diagnosis(state: RecoveryState, proposal: Proposal, ctx: _Context) -> Optional[PolicyDecision]:
    haystack = " ".join(proposal.rationale).lower()
    if proposal.action_detail:
        for v in proposal.action_detail.values():
            haystack += " " + str(v).lower()
    for token in DIAGNOSIS_BANNED_TOKENS:
        if token in haystack:
            ctx.blocked = True
            return PolicyDecision(
                rule_id="no_diagnosis",
                decision="block",
                note=f"diagnosis-shaped token detected: {token}",
            )
    return None


def rule_bounded_action_envelope(state: RecoveryState, proposal: Proposal, ctx: _Context) -> Optional[PolicyDecision]:
    if proposal.action not in ALLOWED_ACTIONS:
        ctx.blocked = True
        return PolicyDecision(
            rule_id="bounded_action_envelope",
            decision="block",
            note=f"action {proposal.action!r} not in v1 enum",
        )
    return None


def rule_review_required(state: RecoveryState, proposal: Proposal, ctx: _Context) -> Optional[PolicyDecision]:
    if not proposal.follow_up_present or not proposal.follow_up_within_24h:
        ctx.blocked = True
        return PolicyDecision(
            rule_id="review_required",
            decision="block",
            note="follow_up missing or review_at outside 24h window",
        )
    return None


def rule_no_high_confidence_on_sparse_signal(
    state: RecoveryState, proposal: Proposal, ctx: _Context
) -> Optional[PolicyDecision]:
    if state.signal_quality.coverage == "sparse" and proposal.confidence == "high":
        ctx.mutated.confidence = "moderate"
        softened_for = [u for u in state.uncertainties if u in ctx.mutated.uncertainty] or state.uncertainties
        note = "capped confidence to moderate on sparse signal"
        if softened_for:
            note += f" ({','.join(softened_for[:3])})"
        return PolicyDecision(
            rule_id="no_high_confidence_on_sparse_signal",
            decision="soften",
            note=note,
        )
    return None


def rule_resting_hr_spike_escalation(
    state: RecoveryState, proposal: Proposal, ctx: _Context
) -> Optional[PolicyDecision]:
    return None


POLICY_RULES: list[tuple[str, PolicyRuleFn]] = [
    ("require_min_coverage", rule_require_min_coverage),
    ("no_diagnosis", rule_no_diagnosis),
    ("bounded_action_envelope", rule_bounded_action_envelope),
    ("review_required", rule_review_required),
    ("no_high_confidence_on_sparse_signal", rule_no_high_confidence_on_sparse_signal),
    ("resting_hr_spike_escalation", rule_resting_hr_spike_escalation),
]


def evaluate_policy(
    state: RecoveryState,
    proposal: Proposal,
    *,
    rhr_spike_days: int,
) -> PolicyEvaluation:
    mutated = Proposal(
        action=proposal.action,
        action_detail=dict(proposal.action_detail) if proposal.action_detail else None,
        rationale=list(proposal.rationale),
        confidence=proposal.confidence,
        uncertainty=list(proposal.uncertainty),
        follow_up_present=proposal.follow_up_present,
        follow_up_within_24h=proposal.follow_up_within_24h,
    )
    ctx = _Context(mutated=mutated)

    decisions: list[PolicyDecision] = []
    for _, fn in POLICY_RULES:
        if ctx.blocked:
            break
        if fn is rule_resting_hr_spike_escalation:
            if rhr_spike_days >= 3:
                ctx.escalate_to = "escalate_for_user_review"
                ctx.escalate_detail = {
                    "reason_token": "resting_hr_spike_3_days_running",
                    "consecutive_days": rhr_spike_days,
                }
                decisions.append(
                    PolicyDecision(
                        rule_id="resting_hr_spike_escalation",
                        decision="escalate",
                        note=f"resting HR well above baseline {rhr_spike_days} days running",
                    )
                )
            continue
        decision = fn(state, proposal, ctx)
        if decision is not None:
            decisions.append(decision)

    return PolicyEvaluation(
        decisions=decisions,
        mutated=ctx.mutated,
        blocked=ctx.blocked,
        escalate_to=ctx.escalate_to,
        escalate_detail=ctx.escalate_detail,
    )
