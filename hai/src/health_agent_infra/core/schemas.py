"""Core schemas: frozen write-surface contracts + runtime evidence/review types.

Two layers coexist here:

1. **Frozen write-surface contracts (new, Phase 1 step 5).** ``BoundedRecommendation``,
   ``DomainProposal``, and ``DailyPlan`` are the canonical payload contracts that
   Phase 2 synthesis will persist. Every per-domain recommendation class
   (starting with ``TrainingRecommendation`` in the recovery domain) must match
   the ``BoundedRecommendation`` field set; subclasses may narrow ``action`` to
   an enum but may not add or remove fields. ``DomainProposal`` is deliberately
   free of ``follow_up``, ``daily_plan_id``, and mutation fields — reviews are
   scheduled from recommendations (not proposals); synthesis assigns
   ``daily_plan_id``; X-rule mutations are applied mechanically by the runtime.
   Idempotency key for ``DailyPlan`` is ``(for_date, user_id)`` only;
   ``agent_version`` is recorded per row but NOT part of the uniqueness contract.
   ``superseded_by`` is the explicit opt-in to versioning, set only by
   ``hai synthesize --supersede``.

2. **Runtime evidence + review types (legacy, pre-Phase-1).** ``CleanedEvidence``,
   ``RawSummary``, ``PolicyDecision``, ``FollowUp``, ``ReviewEvent``,
   ``ReviewOutcome`` are cross-domain runtime contracts carried forward from the
   flagship recovery loop. Domain-specific recommendation shapes (e.g.
   ``TrainingRecommendation``) live under ``domains/<name>/schemas.py``.

The helper ``canonical_daily_plan_id(for_date, user_id)`` derives the stable
key; synthesis uses it when replacing the canonical committed plan atomically.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Literal, Optional


Confidence = Literal["low", "moderate", "high"]
PolicyOutcome = Literal["allow", "soften", "block", "escalate"]


RECOMMENDATION_SCHEMA_VERSION = "training_recommendation.v1"
EVIDENCE_SCHEMA_VERSION = "cleaned_evidence.v1"
RAW_SUMMARY_SCHEMA_VERSION = "raw_summary.v1"


# ---------------------------------------------------------------------------
# Frozen write-surface contracts (Phase 1 step 5).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PolicyDecisionRecord:
    rule_id: str
    decision: PolicyOutcome
    note: str


@dataclass(frozen=True)
class FollowUpRecord:
    review_at: datetime
    review_question: str
    review_event_id: str


BOUNDED_RECOMMENDATION_FIELDS: tuple[str, ...] = (
    "schema_version",
    "recommendation_id",
    "user_id",
    "issued_at",
    "for_date",
    "action",
    "action_detail",
    "rationale",
    "confidence",
    "uncertainty",
    "follow_up",
    "policy_decisions",
    "bounded",
    "daily_plan_id",
    "domain",
)


DOMAIN_PROPOSAL_FIELDS: tuple[str, ...] = (
    "schema_version",
    "proposal_id",
    "user_id",
    "for_date",
    "domain",
    "action",
    "action_detail",
    "rationale",
    "confidence",
    "uncertainty",
    "policy_decisions",
    "bounded",
    # Deliberately missing: follow_up (reviews schedule from recs, not
    # proposals), daily_plan_id (assigned by synthesis), any "mutation"
    # field (skills do not own mutation logic — runtime applies X-rules
    # mechanically per Codex round 2 boundary tightening).
)


DAILY_PLAN_FIELDS: tuple[str, ...] = (
    "daily_plan_id",
    "user_id",
    "for_date",
    "synthesized_at",
    "recommendation_ids",
    "proposal_ids",
    "x_rules_fired",
    "synthesis_meta",
    "superseded_by",
    "agent_version",
    # ``agent_version`` is intentionally recorded per row but NOT part
    # of the idempotency key — see ``canonical_daily_plan_id``.
)


@dataclass(frozen=True)
class BoundedRecommendation:
    """Canonical final artefact per domain after synthesis."""

    schema_version: str
    recommendation_id: str
    user_id: str
    issued_at: datetime
    for_date: date
    domain: str                                      # "recovery" | "running" | ...
    action: str                                      # subclasses narrow to a Literal enum
    action_detail: Optional[dict[str, Any]]
    rationale: tuple[str, ...]
    confidence: Confidence
    uncertainty: tuple[str, ...]
    follow_up: FollowUpRecord
    policy_decisions: tuple[PolicyDecisionRecord, ...]
    bounded: bool = True
    daily_plan_id: Optional[str] = None              # NULL pre-synthesis-commit, set after


@dataclass(frozen=True)
class DomainProposal:
    """Pre-synthesis payload emitted by a domain skill."""

    schema_version: str
    proposal_id: str
    user_id: str
    for_date: date
    domain: str
    action: str
    action_detail: Optional[dict[str, Any]]
    rationale: tuple[str, ...]
    confidence: Confidence
    uncertainty: tuple[str, ...]
    policy_decisions: tuple[PolicyDecisionRecord, ...]
    bounded: bool = True
    # Deliberate absence of follow_up + daily_plan_id + mutation fields.


@dataclass(frozen=True)
class DailyPlan:
    """Synthesis-run record linking proposals, firings, and recommendations."""

    daily_plan_id: str
    user_id: str
    for_date: date
    synthesized_at: datetime
    recommendation_ids: tuple[str, ...]
    proposal_ids: tuple[str, ...]
    x_rules_fired: tuple[str, ...]
    synthesis_meta: Optional[dict[str, Any]]
    agent_version: str                           # recorded per row, NOT part of idempotency key
    superseded_by: Optional[str] = None          # set only by `hai synthesize --supersede`


def canonical_daily_plan_id(for_date: date, user_id: str) -> str:
    """Return the stable canonical plan id for ``(for_date, user_id)``.

    Synthesis uses this id when replacing the canonical committed plan
    atomically. Changing the ``agent_version`` does not change this id;
    to produce a new plan alongside the old one, callers opt in via
    ``--supersede`` which assigns a fresh id with a ``_v<N>`` suffix.
    """

    return f"plan_{for_date.isoformat()}_{user_id}"


# ---------------------------------------------------------------------------
# Legacy runtime evidence + review types.
# ---------------------------------------------------------------------------


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
class ReviewEvent:
    review_event_id: str
    recommendation_id: str
    user_id: str
    review_at: datetime
    review_question: str
    # Defaults to "recovery" for backward-compat with v1 rows. The DB column
    # (migration 003) also backfills to 'recovery' for the same reason.
    domain: str = "recovery"

    def to_dict(self) -> dict:
        return {
            "review_event_id": self.review_event_id,
            "recommendation_id": self.recommendation_id,
            "user_id": self.user_id,
            "review_at": self.review_at.isoformat(),
            "review_question": self.review_question,
            "domain": self.domain,
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
    domain: str = "recovery"
    # M4 enrichment — every field is optional. Legacy outcomes and
    # callers that don't populate these stay unaffected.
    completed: Optional[bool] = None
    intensity_delta: Optional[str] = None
    duration_minutes: Optional[int] = None
    pre_energy_score: Optional[int] = None
    post_energy_score: Optional[int] = None
    disagreed_firing_ids: Optional[list[str]] = None
    # D1 §review_outcome re-link. When a review is recorded against a
    # recommendation whose owning plan has been superseded, the outcome
    # is persisted against the canonical-leaf plan's matching-domain
    # recommendation. ``re_linked_from_recommendation_id`` captures the
    # original target id; ``re_link_note`` is a short human-readable
    # explanation. Both are NULL on the common (non-superseded) path.
    re_linked_from_recommendation_id: Optional[str] = None
    re_link_note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "review_event_id": self.review_event_id,
            "recommendation_id": self.recommendation_id,
            "user_id": self.user_id,
            "recorded_at": self.recorded_at.isoformat(),
            "followed_recommendation": self.followed_recommendation,
            "self_reported_improvement": self.self_reported_improvement,
            "free_text": self.free_text,
            "domain": self.domain,
            "completed": self.completed,
            "intensity_delta": self.intensity_delta,
            "duration_minutes": self.duration_minutes,
            "pre_energy_score": self.pre_energy_score,
            "post_energy_score": self.post_energy_score,
            "disagreed_firing_ids": (
                list(self.disagreed_firing_ids)
                if self.disagreed_firing_ids is not None
                else None
            ),
            "re_linked_from_recommendation_id": self.re_linked_from_recommendation_id,
            "re_link_note": self.re_link_note,
        }
