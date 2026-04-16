"""RECOMMEND layer.

Constructs a TrainingRecommendation from a RecoveryState under policy.
The layer reads only the state object and the CLEAN-layer spike-day count
required by the escalation policy rule.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from health_model.recovery_readiness_v1.policy import Proposal, evaluate_policy
from health_model.recovery_readiness_v1.schemas import (
    RECOMMENDATION_SCHEMA_VERSION,
    ActionKind,
    Confidence,
    FollowUp,
    PolicyDecision,
    RecoveryState,
    StateRef,
    TrainingRecommendation,
)


def build_training_recommendation(
    state: RecoveryState,
    *,
    now: Optional[datetime] = None,
    rhr_spike_days: int = 0,
    planned_session_type: Optional[str] = None,
    user_id: Optional[str] = None,
) -> TrainingRecommendation:
    now = now or datetime.now(timezone.utc)
    user_id = user_id or state.user_id

    review_at = _next_morning_utc(now)
    review_event_id = f"rev_{review_at.date().isoformat()}_{state.user_id}"
    recommendation_id = f"rec_{state.as_of_date.isoformat()}_{state.user_id}_01"

    proposed_action, proposed_detail, rationale, confidence = _propose(
        state=state, planned_session_type=planned_session_type
    )

    proposal = Proposal(
        action=proposed_action,
        action_detail=proposed_detail,
        rationale=rationale,
        confidence=confidence,
        uncertainty=list(state.uncertainties),
        follow_up_present=True,
        follow_up_within_24h=(review_at - now) <= timedelta(hours=24) + timedelta(minutes=1),
    )

    evaluation = evaluate_policy(state, proposal, rhr_spike_days=rhr_spike_days)

    final_action: ActionKind
    final_detail: Optional[dict]
    final_rationale: list[str]
    final_confidence: Confidence
    final_uncertainty: list[str]
    decisions: list[PolicyDecision] = list(evaluation.decisions)

    if evaluation.blocked:
        final_action = "defer_decision_insufficient_signal"
        final_detail = {"reason": "policy_block"}
        final_rationale = ["policy blocked substantive recommendation"] + list(state.uncertainties)
        final_confidence = "low"
        final_uncertainty = list(state.uncertainties)
    else:
        final_action = evaluation.mutated.action
        final_detail = evaluation.mutated.action_detail
        final_rationale = evaluation.mutated.rationale
        final_confidence = evaluation.mutated.confidence
        final_uncertainty = evaluation.mutated.uncertainty

        if evaluation.escalate_to is not None:
            final_action = evaluation.escalate_to
            final_detail = evaluation.escalate_detail

    review_question = _review_question(final_action)

    return TrainingRecommendation(
        schema_version=RECOMMENDATION_SCHEMA_VERSION,
        recommendation_id=recommendation_id,
        user_id=user_id,
        issued_at=now,
        for_date=state.as_of_date,
        state_ref=StateRef(
            schema_version=state.schema_version,
            computed_at=state.computed_at,
            as_of_date=state.as_of_date,
        ),
        action=final_action,
        action_detail=final_detail,
        rationale=final_rationale,
        confidence=final_confidence,
        uncertainty=sorted(set(final_uncertainty)),
        follow_up=FollowUp(
            review_at=review_at,
            review_question=review_question,
            review_event_id=f"{review_event_id}_{recommendation_id}",
        ),
        policy_decisions=decisions,
        bounded=True,
    )


def _propose(
    *,
    state: RecoveryState,
    planned_session_type: Optional[str],
) -> tuple[ActionKind, Optional[dict], list[str], Confidence]:
    """Produce the initial recommendation proposal before policy runs."""

    rationale: list[str] = []

    if state.signal_quality.coverage == "insufficient":
        return (
            "defer_decision_insufficient_signal",
            {"reason": "coverage_insufficient"},
            ["signal_quality.coverage=insufficient"],
            "low",
        )

    rationale.append(f"sleep_debt={state.sleep_debt}")
    rationale.append(f"soreness_signal={state.soreness_signal}")
    rationale.append(f"resting_hr_vs_baseline={state.resting_hr_vs_baseline}")
    rationale.append(f"training_load_trailing_7d={state.training_load_trailing_7d}")
    if state.hrv_vs_baseline != "unknown":
        rationale.append(f"hrv_vs_baseline={state.hrv_vs_baseline}")

    status = state.recovery_status
    base_confidence: Confidence
    if state.signal_quality.coverage == "full":
        base_confidence = "high"
    elif state.signal_quality.coverage == "partial":
        base_confidence = "moderate"
    else:
        base_confidence = "low"

    planned = (planned_session_type or "").lower()

    if status == "impaired":
        if planned in {"hard", "intervals", "race"}:
            return (
                "downgrade_session_to_mobility_only",
                {"reason_token": "impaired_recovery_with_hard_plan"},
                rationale,
                base_confidence,
            )
        return (
            "rest_day_recommended",
            {"suggested_activity": "walk_or_mobility"},
            rationale,
            base_confidence,
        )

    if status == "mildly_impaired":
        if planned in {"hard", "intervals", "race"}:
            return (
                "downgrade_hard_session_to_zone_2",
                {"target_intensity": "zone_2", "target_duration_minutes": 45},
                rationale,
                base_confidence,
            )
        return (
            "proceed_with_planned_session",
            {"caveat": "keep_effort_conversational"},
            rationale,
            base_confidence,
        )

    return ("proceed_with_planned_session", None, rationale, base_confidence)


def _next_morning_utc(now: datetime) -> datetime:
    target = (now + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
    if (target - now) > timedelta(hours=24):
        target = target - timedelta(days=1)
    return target


def _review_question(action: ActionKind) -> str:
    mapping: dict[ActionKind, str] = {
        "proceed_with_planned_session": "Did today's session feel appropriate for your recovery?",
        "downgrade_hard_session_to_zone_2": "Did yesterday's downgrade to Zone 2 improve how today feels?",
        "downgrade_session_to_mobility_only": "Did yesterday's mobility-only day help your recovery?",
        "rest_day_recommended": "Did yesterday's rest day help your recovery?",
        "defer_decision_insufficient_signal": "Did you decide on a session yesterday? How did it go?",
        "escalate_for_user_review": "You had a persistent signal we flagged. Did you take any action?",
    }
    return mapping[action]
