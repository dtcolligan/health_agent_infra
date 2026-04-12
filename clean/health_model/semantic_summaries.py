from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Mapping


WRAPPED_FIELD_STATUSES = {"grounded", "inferred", "missing", "conflicted"}
SEMANTIC_DERIVATION_METHODS = {
    "none",
    "direct_rollup",
    "cross_source_merge",
    "coverage_classification",
    "band_estimation",
    "pattern_detection",
    "contextual_risk_flag",
}
SLEEP_TIMING_REGULARITY_MARKERS = {"regular", "slightly_irregular", "irregular"}
SLEEP_DISRUPTION_MARKERS = {"frequent_awakenings", "restless_sleep", "prolonged_awake_time"}
SUBJECTIVE_RECOVERY_STATES = {"recovered", "mixed", "strained"}
SUBJECTIVE_AMBIGUITY_MARKERS = {"partial_extraction", "conflicting_entries", "missing_subjective_entry"}
PASSIVE_ACTIVITY_MARKERS = {"steps_present", "active_minutes_present", "active_energy_present"}
TRAINING_COMPLETION_MARKERS = {"run_completed", "gym_session_logged", "passive_activity_only"}
SORENESS_STRAIN_MARKERS = {"reported_soreness_or_illness", "manual_body_signal_logged"}
TRAINING_LOAD_BANDS = {"none", "low", "moderate", "high"}
IMPORTANT_GAP_CODES = {
    "missing_sleep_window",
    "missing_sleep_duration",
    "missing_subjective_sleep_quality",
    "missing_subjective_entry",
    "missing_recovery_signal",
    "missing_passive_activity",
    "missing_intentional_training",
}
CONFLICT_CODES = {
    "conflicting_sleep_window",
    "conflicting_sleep_duration",
    "conflicting_subjective_entry",
    "conflicting_perceived_recovery",
    "conflicting_passive_activity",
}
CANONICAL_ID_PREFIXES = ("artifact_", "event_", "subjective_", "manual_")


@dataclass(frozen=True)
class WrappedField:
    status: str
    value: Any
    confidence_label: str
    confidence_score: float
    evidence_refs: list[str] = field(default_factory=list)
    derivation_method: str = "none"
    uncertainty_note: str | None = None

    def __post_init__(self) -> None:
        if self.status not in WRAPPED_FIELD_STATUSES:
            raise ValueError(f"Unsupported wrapped-field status: {self.status}")
        if self.derivation_method not in SEMANTIC_DERIVATION_METHODS:
            raise ValueError(f"Unsupported derivation method: {self.derivation_method}")
        if self.confidence_label not in {"high", "medium", "low"}:
            raise ValueError(f"Unsupported confidence label: {self.confidence_label}")
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0 inclusive")
        invalid_refs = [ref for ref in self.evidence_refs if not _is_canonical_ref(ref)]
        if invalid_refs:
            raise ValueError(f"evidence_refs must point to canonical IDs only: {invalid_refs}")


@dataclass(frozen=True)
class SummaryConfidence:
    confidence_label: str
    confidence_score: float
    evidence_refs: list[str] = field(default_factory=list)
    uncertainty_note: str | None = None

    def __post_init__(self) -> None:
        if self.confidence_label not in {"high", "medium", "low"}:
            raise ValueError(f"Unsupported confidence label: {self.confidence_label}")
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0 inclusive")
        invalid_refs = [ref for ref in self.evidence_refs if not _is_canonical_ref(ref)]
        if invalid_refs:
            raise ValueError(f"evidence_refs must point to canonical IDs only: {invalid_refs}")


@dataclass(frozen=True)
class ImportantGap:
    code: str
    detail: str
    evidence_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.code not in IMPORTANT_GAP_CODES:
            raise ValueError(f"Unsupported important gap code: {self.code}")


@dataclass(frozen=True)
class SemanticConflict:
    code: str
    detail: str
    evidence_refs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.code not in CONFLICT_CODES:
            raise ValueError(f"Unsupported conflict code: {self.code}")


@dataclass(frozen=True)
class SleepWindow:
    start_at: str
    end_at: str


@dataclass(frozen=True)
class PassiveActivitySemanticSlice:
    steps_count: WrappedField
    active_minutes: WrappedField
    active_energy_kcal: WrappedField
    markers: WrappedField


@dataclass(frozen=True)
class IntentionalTrainingSemanticSlice:
    run_session_count: WrappedField
    run_total_duration_minutes: WrappedField
    gym_session_count: WrappedField
    gym_exercise_set_count: WrappedField


@dataclass(frozen=True)
class SleepSemanticSummary:
    summary_id: str
    user_id: str
    date: str
    summary_confidence: SummaryConfidence
    important_gaps: list[ImportantGap] = field(default_factory=list)
    conflicts: list[SemanticConflict] = field(default_factory=list)
    next_action: str | None = None
    primary_sleep_window: WrappedField = field(default_factory=lambda: _missing_field())
    total_sleep_duration_minutes: WrappedField = field(default_factory=lambda: _missing_field())
    subjective_sleep_quality: WrappedField = field(default_factory=lambda: _missing_field())
    sleep_timing_regularity_marker: WrappedField = field(default_factory=lambda: _missing_field())
    sleep_disruption_markers: WrappedField = field(default_factory=lambda: _missing_field())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SubjectiveStateSemanticSummary:
    summary_id: str
    user_id: str
    date: str
    summary_confidence: SummaryConfidence
    important_gaps: list[ImportantGap] = field(default_factory=list)
    conflicts: list[SemanticConflict] = field(default_factory=list)
    next_action: str | None = None
    energy: WrappedField = field(default_factory=lambda: _missing_field())
    stress: WrappedField = field(default_factory=lambda: _missing_field())
    mood: WrappedField = field(default_factory=lambda: _missing_field())
    perceived_recovery: WrappedField = field(default_factory=lambda: _missing_field())
    soreness_or_illness: WrappedField = field(default_factory=lambda: _missing_field())
    free_text_human_summary: WrappedField = field(default_factory=lambda: _missing_field())
    extraction_confidence: SummaryConfidence = field(default_factory=lambda: SummaryConfidence("low", 0.0))
    unresolved_ambiguity_markers: WrappedField = field(default_factory=lambda: _missing_field())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActivityTrainingSemanticSummary:
    summary_id: str
    user_id: str
    date: str
    summary_confidence: SummaryConfidence
    important_gaps: list[ImportantGap] = field(default_factory=list)
    conflicts: list[SemanticConflict] = field(default_factory=list)
    next_action: str | None = None
    passive_activity: PassiveActivitySemanticSlice = field(
        default_factory=lambda: PassiveActivitySemanticSlice(
            steps_count=_missing_field(),
            active_minutes=_missing_field(),
            active_energy_kcal=_missing_field(),
            markers=_missing_field(),
        )
    )
    intentional_training: IntentionalTrainingSemanticSlice = field(
        default_factory=lambda: IntentionalTrainingSemanticSlice(
            run_session_count=_missing_field(),
            run_total_duration_minutes=_missing_field(),
            gym_session_count=_missing_field(),
            gym_exercise_set_count=_missing_field(),
        )
    )
    training_load_estimate_band: WrappedField = field(default_factory=lambda: _missing_field())
    training_completion_markers: WrappedField = field(default_factory=lambda: _missing_field())
    soreness_or_strain_context: WrappedField = field(default_factory=lambda: _missing_field())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_sleep_semantic_summary(bundle: Mapping[str, Any], user_id: str, date: str) -> SleepSemanticSummary:
    events = _events_for(bundle, user_id=user_id, date=date, domain="sleep")
    subjective_entry = _subjective_entry_for(bundle, user_id=user_id, date=date)
    important_gaps: list[ImportantGap] = []
    conflicts: list[SemanticConflict] = []

    start_field = _single_event_value(events, "sleep_start")
    end_field = _single_event_value(events, "sleep_end")
    duration_field = _single_event_value(events, "sleep_duration_minutes")
    awake_count_field = _single_event_value(events, "awake_count")
    awake_minutes_field = _single_event_value(events, "awake_duration_minutes")
    restless_field = _single_event_value(events, "restless_moments")
    timing_regularity_field = _single_event_value(events, "sleep_timing_regularity_marker")

    primary_sleep_window = _build_sleep_window_field(start_field, end_field, conflicts)
    total_sleep_duration_minutes = _build_sleep_duration_field(duration_field, start_field, end_field, conflicts)
    subjective_sleep_quality = _build_subjective_sleep_quality_field(subjective_entry, important_gaps)
    sleep_timing_regularity_marker = _build_timing_regularity_field(timing_regularity_field)
    sleep_disruption_markers = _build_sleep_disruption_markers_field(awake_count_field, awake_minutes_field, restless_field)

    if primary_sleep_window.status == "missing":
        important_gaps.append(ImportantGap("missing_sleep_window", "No reliable primary sleep window was found."))
    if total_sleep_duration_minutes.status == "missing":
        important_gaps.append(ImportantGap("missing_sleep_duration", "No reliable total sleep duration was found."))

    confidence = _summary_confidence(
        [
            primary_sleep_window,
            total_sleep_duration_minutes,
            subjective_sleep_quality,
            sleep_timing_regularity_marker,
            sleep_disruption_markers,
        ]
    )

    return SleepSemanticSummary(
        summary_id=f"summary_sleep_{date}",
        user_id=user_id,
        date=date,
        summary_confidence=confidence,
        important_gaps=important_gaps,
        conflicts=conflicts,
        primary_sleep_window=primary_sleep_window,
        total_sleep_duration_minutes=total_sleep_duration_minutes,
        subjective_sleep_quality=subjective_sleep_quality,
        sleep_timing_regularity_marker=sleep_timing_regularity_marker,
        sleep_disruption_markers=sleep_disruption_markers,
    )


def build_subjective_state_semantic_summary(bundle: Mapping[str, Any], user_id: str, date: str) -> SubjectiveStateSemanticSummary:
    entries = [
        entry
        for entry in bundle.get("subjective_daily_entries", [])
        if entry.get("user_id") == user_id and entry.get("date") == date
    ]
    important_gaps: list[ImportantGap] = []
    conflicts: list[SemanticConflict] = []

    if len(entries) > 1:
        refs = [entry["entry_id"] for entry in entries if entry.get("entry_id")]
        conflicts.append(
            SemanticConflict(
                "conflicting_subjective_entry",
                "Multiple subjective daily entries were present for the same user and date.",
                evidence_refs=refs,
            )
        )

    entry = entries[0] if entries else None
    energy = _entry_rating_field(entry, "energy_self_rating")
    stress = _entry_rating_field(entry, "stress_self_rating")
    mood = _entry_rating_field(entry, "mood_self_rating")
    soreness_or_illness = _entry_boolean_field(entry, "illness_or_soreness_flag")
    free_text_human_summary = _entry_string_field(entry, "free_text_summary")
    perceived_recovery = _build_perceived_recovery_field(bundle, entry, user_id, date, conflicts)
    unresolved_ambiguity_markers = _build_ambiguity_markers_field(entry, len(entries) > 1)

    if entry is None:
        important_gaps.append(ImportantGap("missing_subjective_entry", "No subjective daily entry was available for this day."))
    if perceived_recovery.status == "missing":
        important_gaps.append(ImportantGap("missing_recovery_signal", "Perceived recovery could not be grounded or safely inferred."))

    extraction_confidence = _entry_confidence(entry)
    summary_confidence = _summary_confidence(
        [energy, stress, mood, perceived_recovery, soreness_or_illness, free_text_human_summary, unresolved_ambiguity_markers],
        fallback=extraction_confidence,
    )

    return SubjectiveStateSemanticSummary(
        summary_id=f"summary_subjective_state_{date}",
        user_id=user_id,
        date=date,
        summary_confidence=summary_confidence,
        important_gaps=important_gaps,
        conflicts=conflicts,
        energy=energy,
        stress=stress,
        mood=mood,
        perceived_recovery=perceived_recovery,
        soreness_or_illness=soreness_or_illness,
        free_text_human_summary=free_text_human_summary,
        extraction_confidence=extraction_confidence,
        unresolved_ambiguity_markers=unresolved_ambiguity_markers,
    )


def build_activity_training_semantic_summary(bundle: Mapping[str, Any], user_id: str, date: str) -> ActivityTrainingSemanticSummary:
    events = _events_for(bundle, user_id=user_id, date=date)
    manual_entries = [
        entry
        for entry in bundle.get("manual_log_entries", [])
        if entry.get("user_id") == user_id and entry.get("date") == date
    ]
    important_gaps: list[ImportantGap] = []
    conflicts: list[SemanticConflict] = []

    steps_field = _single_event_value(events, "steps_count")
    active_minutes_field = _single_event_value(events, "active_minutes")
    active_energy_field = _single_event_value(events, "active_energy_kcal")
    passive_markers = _build_passive_activity_markers_field(steps_field, active_minutes_field, active_energy_field)
    passive_activity = PassiveActivitySemanticSlice(
        steps_count=_numeric_event_field(steps_field),
        active_minutes=_numeric_event_field(active_minutes_field),
        active_energy_kcal=_numeric_event_field(active_energy_field),
        markers=passive_markers,
    )
    passive_conflict_refs = sorted(
        {
            ref
            for field in (
                passive_activity.steps_count,
                passive_activity.active_minutes,
                passive_activity.active_energy_kcal,
                passive_activity.markers,
            )
            if field.status == "conflicted"
            for ref in field.evidence_refs
        }
    )
    if passive_conflict_refs:
        conflicts.append(
            SemanticConflict(
                "conflicting_passive_activity",
                "Passive activity evidence conflicted across canonical events.",
                passive_conflict_refs,
            )
        )

    run_duration_events = _events_by_metric(events, "run_duration_minutes")
    run_session_ids = {event.get("source_record_id") or event["event_id"] for event in run_duration_events}
    run_total_duration = sum(float(event["value_number"]) for event in run_duration_events if event.get("value_number") is not None)
    run_duration_field = _wrap_numeric(
        status="grounded" if run_duration_events else "missing",
        value=run_total_duration if run_duration_events else None,
        evidence_refs=[event["event_id"] for event in run_duration_events],
        score=_average_event_score(run_duration_events),
        derivation_method="direct_rollup" if run_duration_events else "none",
        uncertainty_note=None if run_duration_events else "No run duration events were present.",
    )
    run_count_field = _wrap_numeric(
        status="grounded" if run_session_ids else "missing",
        value=len(run_session_ids) if run_session_ids else None,
        evidence_refs=[event["event_id"] for event in run_duration_events],
        score=_average_event_score(run_duration_events),
        derivation_method="direct_rollup" if run_session_ids else "none",
        uncertainty_note=None if run_session_ids else "No run sessions were present.",
    )

    gym_session_entries = [entry for entry in manual_entries if entry.get("log_type") == "gym_session"]
    gym_set_entries = [entry for entry in manual_entries if entry.get("log_type") == "exercise_set"]
    gym_session_field = _wrap_numeric(
        status="grounded" if gym_session_entries else "missing",
        value=len(gym_session_entries) if gym_session_entries else None,
        evidence_refs=[entry["entry_id"] for entry in gym_session_entries if entry.get("entry_id")],
        score=_average_manual_score(gym_session_entries),
        derivation_method="direct_rollup" if gym_session_entries else "none",
        uncertainty_note=None if gym_session_entries else "No manual gym sessions were logged.",
    )
    gym_set_field = _wrap_numeric(
        status="grounded" if gym_set_entries else "missing",
        value=len(gym_set_entries) if gym_set_entries else None,
        evidence_refs=[entry["entry_id"] for entry in gym_set_entries if entry.get("entry_id")],
        score=_average_manual_score(gym_set_entries),
        derivation_method="direct_rollup" if gym_set_entries else "none",
        uncertainty_note=None if gym_set_entries else "No manual exercise sets were logged.",
    )
    intentional_training = IntentionalTrainingSemanticSlice(
        run_session_count=run_count_field,
        run_total_duration_minutes=run_duration_field,
        gym_session_count=gym_session_field,
        gym_exercise_set_count=gym_set_field,
    )

    training_load_estimate_band = _build_training_load_band_field(run_total_duration, gym_session_entries, gym_set_entries)
    training_completion_markers = _build_training_completion_markers_field(passive_markers, run_session_ids, gym_session_entries)
    soreness_or_strain_context = _build_soreness_or_strain_context_field(bundle, manual_entries, user_id, date)

    if passive_markers.status == "missing":
        important_gaps.append(ImportantGap("missing_passive_activity", "No passive activity totals were available for this day."))
    if not run_session_ids and not gym_session_entries and not gym_set_entries:
        important_gaps.append(ImportantGap("missing_intentional_training", "No intentional training evidence was available for this day."))

    summary_confidence = _summary_confidence(
        [
            passive_activity.steps_count,
            passive_activity.active_minutes,
            passive_activity.active_energy_kcal,
            intentional_training.run_session_count,
            intentional_training.run_total_duration_minutes,
            intentional_training.gym_session_count,
            intentional_training.gym_exercise_set_count,
            training_load_estimate_band,
            training_completion_markers,
            soreness_or_strain_context,
        ]
    )

    return ActivityTrainingSemanticSummary(
        summary_id=f"summary_activity_training_{date}",
        user_id=user_id,
        date=date,
        summary_confidence=summary_confidence,
        important_gaps=important_gaps,
        conflicts=conflicts,
        passive_activity=passive_activity,
        intentional_training=intentional_training,
        training_load_estimate_band=training_load_estimate_band,
        training_completion_markers=training_completion_markers,
        soreness_or_strain_context=soreness_or_strain_context,
    )


def _events_for(bundle: Mapping[str, Any], user_id: str, date: str, domain: str | None = None) -> list[Mapping[str, Any]]:
    return [
        event
        for event in bundle.get("input_events", [])
        if event.get("user_id") == user_id
        and event.get("effective_date") == date
        and (domain is None or event.get("domain") == domain)
    ]


def _subjective_entry_for(bundle: Mapping[str, Any], user_id: str, date: str) -> Mapping[str, Any] | None:
    for entry in bundle.get("subjective_daily_entries", []):
        if entry.get("user_id") == user_id and entry.get("date") == date:
            return entry
    return None


def _events_by_metric(events: list[Mapping[str, Any]], metric_name: str) -> list[Mapping[str, Any]]:
    return [
        event
        for event in events
        if event.get("metric_name") == metric_name and event.get("missingness_state") == "present"
    ]


def _single_event_value(events: list[Mapping[str, Any]], metric_name: str) -> dict[str, Any]:
    matches = _events_by_metric(events, metric_name)
    if not matches:
        return {"status": "missing", "events": []}
    observed = {_event_scalar_value(event) for event in matches}
    if len(observed) > 1:
        return {"status": "conflicted", "events": matches}
    return {"status": "grounded", "events": matches, "value": observed.pop()}


def _build_sleep_window_field(start_field: Mapping[str, Any], end_field: Mapping[str, Any], conflicts: list[SemanticConflict]) -> WrappedField:
    if start_field["status"] == "conflicted" or end_field["status"] == "conflicted":
        refs = [event["event_id"] for event in start_field["events"]] + [event["event_id"] for event in end_field["events"]]
        conflicts.append(SemanticConflict("conflicting_sleep_window", "Sleep window evidence conflicted across canonical events.", refs))
        return _conflicted_field(refs, "cross_source_merge", "Sleep window evidence conflicted across canonical events.")
    if start_field["status"] != "grounded" or end_field["status"] != "grounded":
        return _missing_field("No complete grounded sleep window was available.")
    evidence_refs = [event["event_id"] for event in start_field["events"] + end_field["events"]]
    return WrappedField(
        status="grounded",
        value=SleepWindow(start_at=str(start_field["value"]), end_at=str(end_field["value"])),
        confidence_label=_label_from_score(min(_average_event_score(start_field["events"]), _average_event_score(end_field["events"]))),
        confidence_score=min(_average_event_score(start_field["events"]), _average_event_score(end_field["events"])),
        evidence_refs=evidence_refs,
        derivation_method="direct_rollup",
    )


def _build_sleep_duration_field(
    duration_field: Mapping[str, Any],
    start_field: Mapping[str, Any],
    end_field: Mapping[str, Any],
    conflicts: list[SemanticConflict],
) -> WrappedField:
    if duration_field["status"] == "conflicted":
        refs = [event["event_id"] for event in duration_field["events"]]
        conflicts.append(SemanticConflict("conflicting_sleep_duration", "Sleep duration values conflicted across canonical events.", refs))
        return _conflicted_field(refs, "cross_source_merge", "Sleep duration values conflicted across canonical events.")
    if duration_field["status"] == "grounded":
        return _numeric_event_field(duration_field)
    if start_field["status"] == "grounded" and end_field["status"] == "grounded":
        start_at = datetime.fromisoformat(str(start_field["value"]).replace("Z", "+00:00"))
        end_at = datetime.fromisoformat(str(end_field["value"]).replace("Z", "+00:00"))
        minutes = (end_at - start_at).total_seconds() / 60.0
        evidence_refs = [event["event_id"] for event in start_field["events"] + end_field["events"]]
        return _wrap_numeric(
            status="inferred",
            value=minutes,
            evidence_refs=evidence_refs,
            score=min(_average_event_score(start_field["events"]), _average_event_score(end_field["events"])) * 0.9,
            derivation_method="direct_rollup",
            uncertainty_note="Computed from grounded sleep window because no direct duration event was present.",
        )
    return _missing_field("No reliable sleep duration evidence was available.")


def _build_subjective_sleep_quality_field(entry: Mapping[str, Any] | None, important_gaps: list[ImportantGap]) -> WrappedField:
    if entry is None or entry.get("perceived_sleep_quality") is None:
        important_gaps.append(ImportantGap("missing_subjective_sleep_quality", "Subjective sleep quality was not provided for this day."))
        return _missing_field("Subjective sleep quality was not provided.")
    evidence_refs = [entry["entry_id"]]
    score = float(entry.get("confidence_score", 0.0))
    return WrappedField(
        status="grounded",
        value=int(entry["perceived_sleep_quality"]),
        confidence_label=_label_from_score(score),
        confidence_score=score,
        evidence_refs=evidence_refs,
        derivation_method="none",
    )


def _build_timing_regularity_field(metric_field: Mapping[str, Any]) -> WrappedField:
    if metric_field["status"] != "grounded":
        return _missing_field("No grounded sleep timing regularity marker was available.")
    marker = str(metric_field["value"])
    if marker not in SLEEP_TIMING_REGULARITY_MARKERS:
        raise ValueError(f"Unsupported sleep timing regularity marker: {marker}")
    return WrappedField(
        status="grounded",
        value=marker,
        confidence_label=_label_from_score(_average_event_score(metric_field["events"])),
        confidence_score=_average_event_score(metric_field["events"]),
        evidence_refs=[event["event_id"] for event in metric_field["events"]],
        derivation_method="none",
    )


def _build_sleep_disruption_markers_field(
    awake_count_field: Mapping[str, Any],
    awake_minutes_field: Mapping[str, Any],
    restless_field: Mapping[str, Any],
) -> WrappedField:
    if any(field["status"] == "conflicted" for field in (awake_count_field, awake_minutes_field, restless_field)):
        refs = [
            event["event_id"]
            for field in (awake_count_field, awake_minutes_field, restless_field)
            for event in field["events"]
        ]
        return _conflicted_field(refs, "cross_source_merge", "Sleep disruption evidence conflicted across canonical events.")

    markers: list[str] = []
    evidence_refs: list[str] = []
    scores: list[float] = []

    if awake_count_field["status"] == "grounded" and float(awake_count_field["value"]) >= 3:
        markers.append("frequent_awakenings")
        evidence_refs.extend(event["event_id"] for event in awake_count_field["events"])
        scores.append(_average_event_score(awake_count_field["events"]))
    if restless_field["status"] == "grounded" and float(restless_field["value"]) >= 1:
        markers.append("restless_sleep")
        evidence_refs.extend(event["event_id"] for event in restless_field["events"])
        scores.append(_average_event_score(restless_field["events"]))
    if awake_minutes_field["status"] == "grounded" and float(awake_minutes_field["value"]) >= 30:
        markers.append("prolonged_awake_time")
        evidence_refs.extend(event["event_id"] for event in awake_minutes_field["events"])
        scores.append(_average_event_score(awake_minutes_field["events"]))

    for marker in markers:
        if marker not in SLEEP_DISRUPTION_MARKERS:
            raise ValueError(f"Unsupported sleep disruption marker: {marker}")

    if markers:
        score = min(scores)
        return WrappedField(
            status="grounded",
            value=sorted(set(markers)),
            confidence_label=_label_from_score(score),
            confidence_score=score,
            evidence_refs=sorted(set(evidence_refs)),
            derivation_method="pattern_detection",
        )
    if any(field["status"] == "grounded" for field in (awake_count_field, awake_minutes_field, restless_field)):
        refs = [
            event["event_id"]
            for field in (awake_count_field, awake_minutes_field, restless_field)
            for event in field["events"]
        ]
        return WrappedField(
            status="grounded",
            value=[],
            confidence_label=_label_from_score(min([_average_event_score(field["events"]) for field in (awake_count_field, awake_minutes_field, restless_field) if field["events"]], default=0.9)),
            confidence_score=min([_average_event_score(field["events"]) for field in (awake_count_field, awake_minutes_field, restless_field) if field["events"]], default=0.9),
            evidence_refs=sorted(set(refs)),
            derivation_method="pattern_detection",
            uncertainty_note="Disruption evidence was present but no bounded disruption marker threshold was met.",
        )
    return _missing_field("No grounded sleep disruption evidence was available.")


def _entry_rating_field(entry: Mapping[str, Any] | None, field_name: str) -> WrappedField:
    if entry is None or entry.get(field_name) is None:
        return _missing_field(f"{field_name} was not provided.")
    score = float(entry.get("confidence_score", 0.0))
    return WrappedField(
        status="grounded",
        value=int(entry[field_name]),
        confidence_label=_label_from_score(score),
        confidence_score=score,
        evidence_refs=[entry["entry_id"]],
        derivation_method="none",
    )


def _entry_boolean_field(entry: Mapping[str, Any] | None, field_name: str) -> WrappedField:
    if entry is None or entry.get(field_name) is None:
        return _missing_field(f"{field_name} was not provided.")
    score = float(entry.get("confidence_score", 0.0))
    return WrappedField(
        status="grounded",
        value=bool(entry[field_name]),
        confidence_label=_label_from_score(score),
        confidence_score=score,
        evidence_refs=[entry["entry_id"]],
        derivation_method="none",
    )


def _entry_string_field(entry: Mapping[str, Any] | None, field_name: str) -> WrappedField:
    if entry is None or not entry.get(field_name):
        return _missing_field(f"{field_name} was not provided.")
    score = float(entry.get("confidence_score", 0.0))
    return WrappedField(
        status="grounded",
        value=str(entry[field_name]),
        confidence_label=_label_from_score(score),
        confidence_score=score,
        evidence_refs=[entry["entry_id"]],
        derivation_method="none",
    )


def _build_perceived_recovery_field(
    bundle: Mapping[str, Any],
    entry: Mapping[str, Any] | None,
    user_id: str,
    date: str,
    conflicts: list[SemanticConflict],
) -> WrappedField:
    direct_events = _events_for(bundle, user_id=user_id, date=date, domain="subjective")
    direct_recovery = _single_event_value(direct_events, "perceived_recovery_state")
    if direct_recovery["status"] == "conflicted":
        refs = [event["event_id"] for event in direct_recovery["events"]]
        conflicts.append(
            SemanticConflict(
                "conflicting_perceived_recovery",
                "Perceived recovery evidence conflicted across canonical events.",
                refs,
            )
        )
        return _conflicted_field(refs, "cross_source_merge", "Perceived recovery evidence conflicted across canonical events.")
    if direct_recovery["status"] == "grounded":
        value = str(direct_recovery["value"])
        if value not in SUBJECTIVE_RECOVERY_STATES:
            raise ValueError(f"Unsupported subjective recovery state: {value}")
        return WrappedField(
            status="grounded",
            value=value,
            confidence_label=_label_from_score(_average_event_score(direct_recovery["events"])),
            confidence_score=_average_event_score(direct_recovery["events"]),
            evidence_refs=[event["event_id"] for event in direct_recovery["events"]],
            derivation_method="none",
        )
    if entry is None:
        return _missing_field("No subjective entry was available to infer perceived recovery.")

    sleep_quality = entry.get("perceived_sleep_quality")
    soreness = entry.get("illness_or_soreness_flag")
    if sleep_quality is None and soreness is None:
        return _missing_field("No safe recovery signal was present.")

    if sleep_quality is not None:
        if int(sleep_quality) >= 4 and soreness is not True:
            inferred = "recovered"
        elif int(sleep_quality) <= 2 or soreness is True:
            inferred = "strained"
        else:
            inferred = "mixed"
    else:
        inferred = "strained" if soreness is True else "mixed"

    score = max(float(entry.get("confidence_score", 0.0)) - 0.15, 0.0)
    return WrappedField(
        status="inferred",
        value=inferred,
        confidence_label=_label_from_score(score),
        confidence_score=score,
        evidence_refs=[entry["entry_id"]],
        derivation_method="band_estimation",
        uncertainty_note="Perceived recovery was inferred from subjective sleep quality and soreness signals because no direct recovery field exists in the canonical entry.",
    )


def _build_ambiguity_markers_field(entry: Mapping[str, Any] | None, has_conflict: bool) -> WrappedField:
    markers: list[str] = []
    refs: list[str] = []
    if entry is None:
        markers.append("missing_subjective_entry")
    else:
        refs.append(entry["entry_id"])
        if entry.get("extraction_status") == "partial":
            markers.append("partial_extraction")
    if has_conflict:
        markers.append("conflicting_entries")

    for marker in markers:
        if marker not in SUBJECTIVE_AMBIGUITY_MARKERS:
            raise ValueError(f"Unsupported subjective ambiguity marker: {marker}")

    if markers:
        return WrappedField(
            status="grounded",
            value=sorted(set(markers)),
            confidence_label="medium",
            confidence_score=0.6 if has_conflict else 0.75,
            evidence_refs=refs,
            derivation_method="coverage_classification",
        )
    return WrappedField(
        status="grounded",
        value=[],
        confidence_label="high",
        confidence_score=0.95,
        evidence_refs=refs,
        derivation_method="coverage_classification",
    )


def _entry_confidence(entry: Mapping[str, Any] | None) -> SummaryConfidence:
    if entry is None:
        return SummaryConfidence("low", 0.0, uncertainty_note="No subjective daily entry was available.")
    score = float(entry.get("confidence_score", 0.0))
    return SummaryConfidence(
        confidence_label=_label_from_score(score),
        confidence_score=score,
        evidence_refs=[entry["entry_id"]],
    )


def _numeric_event_field(metric_field: Mapping[str, Any]) -> WrappedField:
    if metric_field["status"] == "conflicted":
        refs = [event["event_id"] for event in metric_field["events"]]
        return _conflicted_field(refs, "cross_source_merge", "Canonical event values conflicted.")
    if metric_field["status"] != "grounded":
        return _missing_field("No grounded canonical event value was available.")
    return _wrap_numeric(
        status="grounded",
        value=float(metric_field["value"]),
        evidence_refs=[event["event_id"] for event in metric_field["events"]],
        score=_average_event_score(metric_field["events"]),
        derivation_method="none",
        uncertainty_note=None,
    )


def _build_passive_activity_markers_field(
    steps_field: Mapping[str, Any],
    active_minutes_field: Mapping[str, Any],
    active_energy_field: Mapping[str, Any],
) -> WrappedField:
    if any(field["status"] == "conflicted" for field in (steps_field, active_minutes_field, active_energy_field)):
        refs = [
            event["event_id"]
            for field in (steps_field, active_minutes_field, active_energy_field)
            for event in field["events"]
        ]
        return _conflicted_field(refs, "cross_source_merge", "Passive activity totals conflicted across canonical events.")

    markers: list[str] = []
    refs: list[str] = []
    scores: list[float] = []
    if steps_field["status"] == "grounded":
        markers.append("steps_present")
        refs.extend(event["event_id"] for event in steps_field["events"])
        scores.append(_average_event_score(steps_field["events"]))
    if active_minutes_field["status"] == "grounded":
        markers.append("active_minutes_present")
        refs.extend(event["event_id"] for event in active_minutes_field["events"])
        scores.append(_average_event_score(active_minutes_field["events"]))
    if active_energy_field["status"] == "grounded":
        markers.append("active_energy_present")
        refs.extend(event["event_id"] for event in active_energy_field["events"])
        scores.append(_average_event_score(active_energy_field["events"]))

    for marker in markers:
        if marker not in PASSIVE_ACTIVITY_MARKERS:
            raise ValueError(f"Unsupported passive activity marker: {marker}")

    if not markers:
        return _missing_field("No passive activity totals were available.")
    return WrappedField(
        status="grounded",
        value=sorted(set(markers)),
        confidence_label=_label_from_score(min(scores)),
        confidence_score=min(scores),
        evidence_refs=sorted(set(refs)),
        derivation_method="coverage_classification",
    )


def _build_training_load_band_field(
    run_total_duration_minutes: float,
    gym_session_entries: list[Mapping[str, Any]],
    gym_set_entries: list[Mapping[str, Any]],
) -> WrappedField:
    refs = [entry["entry_id"] for entry in gym_session_entries + gym_set_entries if entry.get("entry_id")]
    score = _average_manual_score(gym_session_entries + gym_set_entries) if gym_session_entries or gym_set_entries else 0.0

    if run_total_duration_minutes <= 0 and not gym_session_entries and not gym_set_entries:
        return WrappedField(
            status="grounded",
            value="none",
            confidence_label="high",
            confidence_score=0.95,
            evidence_refs=[],
            derivation_method="band_estimation",
            uncertainty_note="No intentional training evidence was present.",
        )

    gym_load_points = len(gym_session_entries) * 45 + len(gym_set_entries) * 5
    load_points = run_total_duration_minutes + gym_load_points
    if load_points < 45:
        band = "low"
    elif load_points < 120:
        band = "moderate"
    else:
        band = "high"

    return WrappedField(
        status="inferred",
        value=band,
        confidence_label=_label_from_score(max(score, 0.6)),
        confidence_score=max(score, 0.6),
        evidence_refs=refs,
        derivation_method="band_estimation",
        uncertainty_note="Training load is intentionally expressed as a band rather than a precise score.",
    )


def _build_training_completion_markers_field(
    passive_markers: WrappedField,
    run_session_ids: set[str],
    gym_session_entries: list[Mapping[str, Any]],
) -> WrappedField:
    markers: list[str] = []
    refs = list(passive_markers.evidence_refs)
    if run_session_ids:
        markers.append("run_completed")
    if gym_session_entries:
        markers.append("gym_session_logged")
        refs.extend(entry["entry_id"] for entry in gym_session_entries if entry.get("entry_id"))
    if passive_markers.status == "grounded" and not run_session_ids and not gym_session_entries:
        markers.append("passive_activity_only")

    for marker in markers:
        if marker not in TRAINING_COMPLETION_MARKERS:
            raise ValueError(f"Unsupported training completion marker: {marker}")

    if not markers:
        return _missing_field("No passive or intentional activity markers were available.")
    return WrappedField(
        status="grounded",
        value=sorted(set(markers)),
        confidence_label="high",
        confidence_score=0.9,
        evidence_refs=sorted(set(refs)),
        derivation_method="coverage_classification",
    )


def _build_soreness_or_strain_context_field(
    bundle: Mapping[str, Any],
    manual_entries: list[Mapping[str, Any]],
    user_id: str,
    date: str,
) -> WrappedField:
    refs: list[str] = []
    markers: list[str] = []
    subjective_entry = _subjective_entry_for(bundle, user_id=user_id, date=date)
    if subjective_entry and subjective_entry.get("illness_or_soreness_flag") is True:
        markers.append("reported_soreness_or_illness")
        refs.append(subjective_entry["entry_id"])

    body_signals = [entry for entry in manual_entries if entry.get("log_type") == "body_signal"]
    if body_signals:
        markers.append("manual_body_signal_logged")
        refs.extend(entry["entry_id"] for entry in body_signals if entry.get("entry_id"))

    for marker in markers:
        if marker not in SORENESS_STRAIN_MARKERS:
            raise ValueError(f"Unsupported soreness/strain marker: {marker}")

    if not markers:
        return _missing_field("No soreness or strain context was available.")
    return WrappedField(
        status="grounded",
        value=sorted(set(markers)),
        confidence_label="medium",
        confidence_score=0.8,
        evidence_refs=sorted(set(refs)),
        derivation_method="contextual_risk_flag",
    )


def _summary_confidence(fields: list[WrappedField], fallback: SummaryConfidence | None = None) -> SummaryConfidence:
    available = [field for field in fields if field.status in {"grounded", "inferred", "conflicted"}]
    if not available:
        return fallback or SummaryConfidence("low", 0.0, uncertainty_note="No semantic fields were grounded or safely inferred.")
    score = min(field.confidence_score for field in available)
    refs = sorted({ref for field in available for ref in field.evidence_refs})
    return SummaryConfidence(
        confidence_label=_label_from_score(score),
        confidence_score=score,
        evidence_refs=refs,
    )


def _wrap_numeric(
    *,
    status: str,
    value: float | int | None,
    evidence_refs: list[str],
    score: float,
    derivation_method: str,
    uncertainty_note: str | None,
) -> WrappedField:
    return WrappedField(
        status=status,
        value=value,
        confidence_label=_label_from_score(score),
        confidence_score=score,
        evidence_refs=evidence_refs,
        derivation_method=derivation_method,
        uncertainty_note=uncertainty_note,
    )


def _missing_field(note: str | None = None) -> WrappedField:
    return WrappedField(
        status="missing",
        value=None,
        confidence_label="low",
        confidence_score=0.0,
        evidence_refs=[],
        derivation_method="none",
        uncertainty_note=note,
    )


def _conflicted_field(refs: list[str], derivation_method: str, note: str) -> WrappedField:
    return WrappedField(
        status="conflicted",
        value=None,
        confidence_label="low",
        confidence_score=0.25,
        evidence_refs=sorted(set(refs)),
        derivation_method=derivation_method,
        uncertainty_note=note,
    )


def _event_scalar_value(event: Mapping[str, Any]) -> Any:
    if event.get("value_number") is not None:
        return float(event["value_number"])
    if event.get("value_string") is not None:
        return str(event["value_string"])
    if event.get("value_boolean") is not None:
        return bool(event["value_boolean"])
    if event.get("value_json") is not None:
        return event["value_json"]
    return None


def _average_event_score(events: list[Mapping[str, Any]]) -> float:
    if not events:
        return 0.0
    return sum(float(event.get("confidence_score", 0.0)) for event in events) / len(events)


def _average_manual_score(entries: list[Mapping[str, Any]]) -> float:
    if not entries:
        return 0.0
    return sum(float(entry.get("confidence_score", 0.0)) for entry in entries) / len(entries)


def _label_from_score(score: float) -> str:
    if score >= 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def _is_canonical_ref(value: str) -> bool:
    return isinstance(value, str) and value.startswith(CANONICAL_ID_PREFIXES)
