"""Typed schemas for health_agent_infra.

The runtime emits clean structured state (``CleanedEvidence``, ``RawSummary``),
validates agent-produced recommendations against ``TrainingRecommendation``,
and persists review events/outcomes. All classification, policy, and
recommendation-shaping judgment lives in skills — see ``skills/``.

``PolicyDecision`` and ``ActionKind`` are retained because the agent names
them in its output: ``PolicyDecision`` records which rule fired and with
what outcome; ``ActionKind`` is the enum the agent must pick from.
``Confidence`` is also retained as the agent's confidence field.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Literal, Optional

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

RECOMMENDATION_SCHEMA_VERSION = "training_recommendation.v1"
EVIDENCE_SCHEMA_VERSION = "cleaned_evidence.v1"
RAW_SUMMARY_SCHEMA_VERSION = "raw_summary.v1"


@dataclass
class CleanedEvidence:
    """Output of CLEAN layer — typed record of a day's inputs."""

    as_of_date: date
    user_id: str
    sleep_hours: Optional[float]
    sleep_record_id: Optional[str]
    resting_hr: Optional[float]
    resting_hr_record_id: Optional[str]
    hrv_ms: Optional[float]
    hrv_record_id: Optional[str]
    trailing_7d_training_load: Optional[float]
    soreness_self_report: Optional[str]
    energy_self_report: Optional[str]
    planned_session_type: Optional[str]
    manual_readiness_submission_id: Optional[str]
    active_goal: Optional[str]
    optional_context_note_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["as_of_date"] = self.as_of_date.isoformat()
        return data


@dataclass
class RawSummary:
    """Output of CLEAN layer — raw deltas / ratios / counts / coverage fractions.

    Deterministic. No bands, no classifications, no scores. The agent reads
    these numbers and applies judgment via the recovery-readiness skill.

    Garmin-richness fields (7B) are today-only (no baseline/ratio yet);
    they surface the vendor's own scores and aggregates so the skill can
    cross-check its own bands against pre-computed vendor judgment.
    """

    schema_version: str
    as_of_date: date
    user_id: str

    sleep_hours: Optional[float]
    sleep_baseline_hours: Optional[float]
    sleep_debt_hours: Optional[float]

    resting_hr: Optional[float]
    resting_hr_baseline: Optional[float]
    resting_hr_ratio_vs_baseline: Optional[float]
    resting_hr_spike_days: int

    hrv_ms: Optional[float]
    hrv_baseline: Optional[float]
    hrv_ratio_vs_baseline: Optional[float]

    trailing_7d_training_load: Optional[float]
    training_load_baseline: Optional[float]
    training_load_ratio_vs_baseline: Optional[float]

    coverage_sleep_fraction: float
    coverage_rhr_fraction: float
    coverage_hrv_fraction: float
    coverage_training_load_fraction: float

    # Phase 7B — Garmin-native signals (today only; no baseline in v1).
    all_day_stress: Optional[int] = None
    body_battery_end_of_day: Optional[int] = None

    # Running-aggregate proxies (daily-grain; see accepted_running_state).
    total_distance_m: Optional[float] = None
    moderate_intensity_min: Optional[int] = None
    vigorous_intensity_min: Optional[int] = None

    # Garmin's native acute-chronic ratio + its banded status label.
    garmin_acwr_ratio: Optional[float] = None
    acwr_status: Optional[str] = None

    # Garmin Training Readiness — five exported component pcts plus a
    # locally-computed mean. Garmin does NOT export its own overall
    # Training Readiness pct in the daily CSV; only the five component
    # pcts and the categorical level. training_readiness_component_mean_pct
    # is a plain arithmetic mean of the five components (no Garmin-style
    # weighting). When any component is missing, the mean is None.
    # training_readiness_level preserves Garmin's categorical band (e.g.
    # "High", "LOW") — that IS vendor-authored and can disagree with the
    # local mean.
    training_readiness_level: Optional[str] = None
    training_readiness_component_mean_pct: Optional[float] = None
    training_readiness_sleep_pct: Optional[float] = None
    training_readiness_hrv_pct: Optional[float] = None
    training_readiness_stress_pct: Optional[float] = None
    training_readiness_sleep_history_pct: Optional[float] = None
    training_readiness_load_pct: Optional[float] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["as_of_date"] = self.as_of_date.isoformat()
        return data


@dataclass
class PolicyDecision:
    rule_id: str
    decision: PolicyOutcome
    note: str


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
    """Agent-produced bounded recommendation.

    The agent composes this object from ``CleanedEvidence`` + ``RawSummary``
    by following the recovery-readiness skill. ``hai writeback`` validates
    the shape before persisting — validation is the runtime's contract check
    on the agent's output.
    """

    schema_version: str
    recommendation_id: str
    user_id: str
    issued_at: datetime
    for_date: date
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
