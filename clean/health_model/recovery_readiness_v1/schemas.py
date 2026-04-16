"""Typed schemas for recovery_readiness_v1.

Authoritative docs:
- reporting/docs/state_object_schema.md
- reporting/docs/recommendation_object_schema.md
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Literal, Optional

RecoveryStatus = Literal["recovered", "mildly_impaired", "impaired", "unknown"]
SleepDebt = Literal["none", "mild", "moderate", "elevated", "unknown"]
SorenessSignal = Literal["low", "moderate", "high", "unknown"]
BaselineBand = Literal["below", "at", "above", "well_above", "unknown"]
TrainingLoadBand = Literal["low", "moderate", "high", "spike", "unknown"]
CoverageBand = Literal["full", "partial", "sparse", "insufficient"]
Confidence = Literal["low", "moderate", "high"]
PolicyOutcome = Literal["allow", "soften", "block", "escalate"]

ActionKind = Literal[
    "proceed_with_planned_session",
    "downgrade_hard_session_to_zone_2",
    "downgrade_session_to_mobility_only",
    "rest_day_recommended",
    "defer_decision_insufficient_signal",
    "escalate_for_user_review",
]

STATE_SCHEMA_VERSION = "recovery_state.v1"
RECOMMENDATION_SCHEMA_VERSION = "training_recommendation.v1"


@dataclass
class CleanedEvidence:
    """Output of CLEAN layer. Inputs to STATE layer."""

    as_of_date: date
    user_id: str
    sleep_hours: Optional[float]
    sleep_record_id: Optional[str]
    resting_hr: Optional[float]
    resting_hr_record_id: Optional[str]
    resting_hr_baseline: Optional[float]
    hrv_ms: Optional[float]
    hrv_record_id: Optional[str]
    hrv_baseline: Optional[float]
    trailing_7d_training_load: Optional[float]
    training_load_baseline: Optional[float]
    soreness_self_report: Optional[SorenessSignal]
    energy_self_report: Optional[str]
    planned_session_type: Optional[str]
    manual_readiness_submission_id: Optional[str]
    active_goal: Optional[str]
    optional_context_note_ids: list[str] = field(default_factory=list)
    resting_hr_spike_days: int = 0


@dataclass
class SignalQuality:
    coverage: CoverageBand
    required_inputs_present: bool
    notes: list[str] = field(default_factory=list)


@dataclass
class InputsUsed:
    garmin_sleep_record_id: Optional[str]
    garmin_resting_hr_record_id: Optional[str]
    garmin_hrv_record_id: Optional[str]
    training_load_window: str
    manual_readiness_submission_id: Optional[str]
    optional_context_note_ids: list[str] = field(default_factory=list)


@dataclass
class RecoveryState:
    schema_version: str
    user_id: str
    computed_at: datetime
    as_of_date: date
    recovery_status: RecoveryStatus
    readiness_score: Optional[float]
    sleep_debt: SleepDebt
    soreness_signal: SorenessSignal
    resting_hr_vs_baseline: BaselineBand
    hrv_vs_baseline: BaselineBand
    training_load_trailing_7d: TrainingLoadBand
    active_goal: Optional[str]
    signal_quality: SignalQuality
    uncertainties: list[str]
    inputs_used: InputsUsed

    def to_dict(self) -> dict:
        data = asdict(self)
        data["computed_at"] = self.computed_at.isoformat()
        data["as_of_date"] = self.as_of_date.isoformat()
        return data


@dataclass
class PolicyDecision:
    rule_id: str
    decision: PolicyOutcome
    note: str


@dataclass
class StateRef:
    schema_version: str
    computed_at: datetime
    as_of_date: date
    hash: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "computed_at": self.computed_at.isoformat(),
            "as_of_date": self.as_of_date.isoformat(),
            "hash": self.hash,
        }


@dataclass
class FollowUp:
    review_at: datetime
    review_question: str
    review_event_id: str

    def to_dict(self) -> dict:
        return {
            "review_at": self.review_at.isoformat(),
            "review_question": self.review_question,
            "review_event_id": self.review_event_id,
        }


@dataclass
class TrainingRecommendation:
    schema_version: str
    recommendation_id: str
    user_id: str
    issued_at: datetime
    for_date: date
    state_ref: StateRef
    action: ActionKind
    action_detail: Optional[dict]
    rationale: list[str]
    confidence: Confidence
    uncertainty: list[str]
    follow_up: FollowUp
    policy_decisions: list[PolicyDecision]
    bounded: bool = True

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "recommendation_id": self.recommendation_id,
            "user_id": self.user_id,
            "issued_at": self.issued_at.isoformat(),
            "for_date": self.for_date.isoformat(),
            "state_ref": self.state_ref.to_dict(),
            "action": self.action,
            "action_detail": self.action_detail,
            "rationale": list(self.rationale),
            "confidence": self.confidence,
            "uncertainty": list(self.uncertainty),
            "follow_up": self.follow_up.to_dict(),
            "policy_decisions": [asdict(d) for d in self.policy_decisions],
            "bounded": self.bounded,
        }


@dataclass
class ReviewEvent:
    review_event_id: str
    recommendation_id: str
    user_id: str
    review_at: datetime
    review_question: str

    def to_dict(self) -> dict:
        return {
            "review_event_id": self.review_event_id,
            "recommendation_id": self.recommendation_id,
            "user_id": self.user_id,
            "review_at": self.review_at.isoformat(),
            "review_question": self.review_question,
        }


@dataclass
class ReviewOutcome:
    review_event_id: str
    recommendation_id: str
    user_id: str
    recorded_at: datetime
    followed_recommendation: bool
    self_reported_improvement: Optional[bool]
    free_text: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "review_event_id": self.review_event_id,
            "recommendation_id": self.recommendation_id,
            "user_id": self.user_id,
            "recorded_at": self.recorded_at.isoformat(),
            "followed_recommendation": self.followed_recommendation,
            "self_reported_improvement": self.self_reported_improvement,
            "free_text": self.free_text,
        }
