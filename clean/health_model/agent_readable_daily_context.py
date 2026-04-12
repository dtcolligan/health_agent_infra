from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Iterable

from health_model.semantic_summaries import (
    ActivityTrainingSemanticSummary,
    SleepSemanticSummary,
    SubjectiveStateSemanticSummary,
    WrappedField,
    build_activity_training_semantic_summary,
    build_sleep_semantic_summary,
    build_subjective_state_semantic_summary,
)


def build_agent_readable_daily_context(bundle: dict[str, Any], user_id: str, date: str) -> dict[str, Any]:
    sleep_summary = build_sleep_semantic_summary(bundle, user_id=user_id, date=date)
    subjective_summary = build_subjective_state_semantic_summary(bundle, user_id=user_id, date=date)
    activity_summary = build_activity_training_semantic_summary(bundle, user_id=user_id, date=date)
    input_events = [
        event
        for event in bundle.get("input_events", [])
        if event.get("user_id") == user_id and event.get("effective_date") == date
    ]
    subjective_entries = [
        entry
        for entry in bundle.get("subjective_daily_entries", [])
        if entry.get("user_id") == user_id and entry.get("date") == date
    ]
    manual_log_entries = [
        entry
        for entry in bundle.get("manual_log_entries", [])
        if entry.get("user_id") == user_id and entry.get("date") == date
    ]

    signals = [
        *_sleep_signals(sleep_summary),
        *_subjective_signals(subjective_summary),
        *_activity_training_signals(activity_summary),
        *_manual_enrichment_signals(bundle.get("source_artifacts", []), input_events, manual_log_entries),
    ]
    important_gaps = _collect_gap_entries(
        [
            ("sleep", sleep_summary.important_gaps),
            ("subjective_state", subjective_summary.important_gaps),
            ("activity_training", activity_summary.important_gaps),
        ]
    )
    conflicts = _collect_conflict_entries(
        [
            ("sleep", sleep_summary.conflicts),
            ("subjective_state", subjective_summary.conflicts),
            ("activity_training", activity_summary.conflicts),
        ]
    )

    return {
        "context_id": f"agent_context_{user_id}_{date}",
        "artifact_type": "agent_readable_daily_context",
        "user_id": user_id,
        "date": date,
        "generated_from": {
            "source_artifact_ids": _source_artifact_ids_for_day(input_events, subjective_entries, manual_log_entries),
            "input_event_ids": sorted(
                event["event_id"]
                for event in input_events
            ),
            "subjective_entry_ids": sorted(
                entry["entry_id"]
                for entry in subjective_entries
            ),
            "manual_log_entry_ids": sorted(
                entry["entry_id"]
                for entry in manual_log_entries
            ),
        },
        "explicit_grounding": {
            "signal_status_counts": {
                "grounded": sum(1 for signal in signals if signal["status"] == "grounded"),
                "inferred": sum(1 for signal in signals if signal["status"] == "inferred"),
                "missing": sum(1 for signal in signals if signal["status"] == "missing"),
                "conflicted": sum(1 for signal in signals if signal["status"] == "conflicted"),
            },
            "signals": signals,
        },
        "important_gaps": important_gaps,
        "conflicts": conflicts,
        "semantic_context": {
            "sleep": sleep_summary.to_dict(),
            "subjective_state": subjective_summary.to_dict(),
            "activity_training": activity_summary.to_dict(),
        },
    }


def _sleep_signals(summary: SleepSemanticSummary) -> list[dict[str, Any]]:
    return [
        _signal_entry("sleep", "primary_sleep_window", summary.primary_sleep_window),
        _signal_entry("sleep", "total_sleep_duration_minutes", summary.total_sleep_duration_minutes),
        _signal_entry("sleep", "subjective_sleep_quality", summary.subjective_sleep_quality),
        _signal_entry("sleep", "sleep_timing_regularity_marker", summary.sleep_timing_regularity_marker),
        _signal_entry("sleep", "sleep_disruption_markers", summary.sleep_disruption_markers),
    ]


def _subjective_signals(summary: SubjectiveStateSemanticSummary) -> list[dict[str, Any]]:
    signals = [
        _signal_entry("subjective_state", "energy", summary.energy),
        _signal_entry("subjective_state", "stress", summary.stress),
        _signal_entry("subjective_state", "mood", summary.mood),
        _signal_entry("subjective_state", "perceived_recovery", summary.perceived_recovery),
        _signal_entry("subjective_state", "soreness_or_illness", summary.soreness_or_illness),
        _signal_entry("subjective_state", "free_text_human_summary", summary.free_text_human_summary),
        _signal_entry("subjective_state", "unresolved_ambiguity_markers", summary.unresolved_ambiguity_markers),
    ]
    metadata_signal = getattr(summary, "normalization_metadata", None)
    if metadata_signal is not None:
        signals.append(_signal_entry("subjective_state", "subjective_daily_input_record", metadata_signal))
    return signals


def _activity_training_signals(summary: ActivityTrainingSemanticSummary) -> list[dict[str, Any]]:
    return [
        _signal_entry("activity_training", "passive_activity.steps_count", summary.passive_activity.steps_count),
        _signal_entry("activity_training", "passive_activity.active_minutes", summary.passive_activity.active_minutes),
        _signal_entry("activity_training", "passive_activity.active_energy_kcal", summary.passive_activity.active_energy_kcal),
        _signal_entry("activity_training", "passive_activity.markers", summary.passive_activity.markers),
        _signal_entry("activity_training", "intentional_training.run_session_count", summary.intentional_training.run_session_count),
        _signal_entry(
            "activity_training",
            "intentional_training.run_total_duration_minutes",
            summary.intentional_training.run_total_duration_minutes,
        ),
        _signal_entry("activity_training", "intentional_training.gym_session_count", summary.intentional_training.gym_session_count),
        _signal_entry(
            "activity_training",
            "intentional_training.gym_exercise_set_count",
            summary.intentional_training.gym_exercise_set_count,
        ),
        _signal_entry("activity_training", "training_load_estimate_band", summary.training_load_estimate_band),
        _signal_entry("activity_training", "training_completion_markers", summary.training_completion_markers),
        _signal_entry("activity_training", "soreness_or_strain_context", summary.soreness_or_strain_context),
    ]


def _manual_enrichment_signals(
    source_artifacts: list[dict[str, Any]],
    input_events: list[dict[str, Any]],
    manual_log_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    meal_entries = [
        entry
        for entry in manual_log_entries
        if entry.get("log_type") == "meal"
    ]
    hydration_entries = [
        entry
        for entry in manual_log_entries
        if entry.get("log_type") == "hydration"
    ]
    hydration_events = [
        event
        for event in input_events
        if event.get("domain") == "hydration" and event.get("metric_name") == "hydration_amount_ml"
    ]
    nutrition_events = [
        event
        for event in input_events
        if event.get("domain") == "nutrition"
        and event.get("metric_name") in {"meal_logged", "meal_estimated_flag", "meal_label"}
    ]

    signals: list[dict[str, Any]] = []
    if meal_entries or nutrition_events:
        signals.append(_nutrition_signal(meal_entries, nutrition_events))
    if hydration_entries or hydration_events:
        signals.append(_hydration_signal(source_artifacts, hydration_entries, hydration_events))
    return signals


def _signal_entry(domain: str, signal_key: str, field: WrappedField) -> dict[str, Any]:
    return {
        "domain": domain,
        "signal_key": signal_key,
        "status": field.status,
        "value": _serialize(field.value),
        "confidence_label": field.confidence_label,
        "confidence_score": field.confidence_score,
        "evidence_refs": list(field.evidence_refs),
        "derivation_method": field.derivation_method,
        "uncertainty_note": field.uncertainty_note,
    }


def _collect_gap_entries(domain_pairs: Iterable[tuple[str, list[Any]]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for domain, domain_gaps in domain_pairs:
        for gap in domain_gaps:
            gaps.append(
                {
                    "domain": domain,
                    "code": gap.code,
                    "detail": gap.detail,
                    "evidence_refs": list(gap.evidence_refs),
                }
            )
    return gaps


def _collect_conflict_entries(domain_pairs: Iterable[tuple[str, list[Any]]]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    for domain, domain_conflicts in domain_pairs:
        for conflict in domain_conflicts:
            conflicts.append(
                {
                    "domain": domain,
                    "code": conflict.code,
                    "detail": conflict.detail,
                    "evidence_refs": list(conflict.evidence_refs),
                }
            )
    return conflicts


def _source_artifact_ids_for_day(
    input_events: Iterable[dict[str, Any]],
    subjective_entries: Iterable[dict[str, Any]],
    manual_log_entries: Iterable[dict[str, Any]],
) -> list[str]:
    source_artifact_ids: set[str] = set()
    for event in input_events:
        artifact_id = event.get("provenance", {}).get("artifact_id")
        if artifact_id:
            source_artifact_ids.add(artifact_id)
    for entry in subjective_entries:
        for artifact_id in entry.get("source_artifact_ids", []):
            if artifact_id:
                source_artifact_ids.add(artifact_id)
    for entry in manual_log_entries:
        artifact_id = entry.get("source_artifact_id")
        if artifact_id:
            source_artifact_ids.add(artifact_id)
    return sorted(source_artifact_ids)


def _nutrition_signal(
    meal_entries: list[dict[str, Any]],
    nutrition_events: list[dict[str, Any]],
) -> dict[str, Any]:
    canonical_meal_events = [
        event for event in nutrition_events if event.get("metric_name") == "meal_logged"
    ]
    estimated_events = [
        event
        for event in nutrition_events
        if event.get("metric_name") == "meal_estimated_flag" and event.get("missingness_state") == "present"
    ]
    meal_label_events = [
        event for event in nutrition_events if event.get("metric_name") == "meal_label"
    ]
    evidence_refs = sorted(
        [entry["entry_id"] for entry in meal_entries]
        + [event["event_id"] for event in nutrition_events]
    )
    supporting_records: list[dict[str, Any]] = [*meal_entries, *nutrition_events]
    confidence_label, confidence_score = _conservative_confidence(supporting_records)
    meal_labels = sorted(
        {
            event.get("value_string")
            for event in meal_label_events
            if event.get("value_string")
        }
    )
    note_texts = [
        entry.get("payload", {}).get("notes")
        for entry in meal_entries
        if entry.get("payload", {}).get("notes")
    ]
    estimated_entry_count = sum(
        1
        for event in estimated_events
        if event.get("value_boolean") is True
    )
    field = WrappedField(
        status="grounded",
        value={
            "meal_count": len(canonical_meal_events) or len(meal_entries),
            "meal_labels": meal_labels,
            "notes": note_texts,
            "estimated_entry_count": estimated_entry_count,
        },
        confidence_label=confidence_label,
        confidence_score=confidence_score,
        evidence_refs=evidence_refs,
        derivation_method="direct_rollup",
        uncertainty_note=(
            "Includes estimated manual meal notes; quantities remain approximate."
            if estimated_entry_count
            else None
        ),
    )
    return _signal_entry("nutrition", "manual_meal_logs", field)


def _hydration_signal(
    source_artifacts: list[dict[str, Any]],
    hydration_entries: list[dict[str, Any]],
    hydration_events: list[dict[str, Any]],
) -> dict[str, Any]:
    canonical_entries, canonical_events = _dedup_hydration_submission_replays(
        source_artifacts=source_artifacts,
        hydration_entries=hydration_entries,
        hydration_events=hydration_events,
    )
    evidence_refs = sorted(
        [entry["entry_id"] for entry in canonical_entries]
        + [event["event_id"] for event in canonical_events]
    )
    supporting_records: list[dict[str, Any]] = [*canonical_entries, *canonical_events]
    confidence_label, confidence_score = _conservative_confidence(supporting_records)
    beverage_types = sorted(
        {
            entry.get("payload", {}).get("beverage_type")
            for entry in canonical_entries
            if entry.get("payload", {}).get("beverage_type")
        }
    )
    total_amount_ml = sum(
        float(event["value_number"])
        for event in canonical_events
        if event.get("value_number") is not None
    )
    if total_amount_ml == 0:
        total_amount_ml = sum(
            float(entry.get("payload", {}).get("amount_ml", 0))
            for entry in canonical_entries
        )
    field = WrappedField(
        status="grounded",
        value={
            "total_amount_ml": total_amount_ml,
            "log_count": len(canonical_entries),
            "beverage_types": beverage_types,
        },
        confidence_label=confidence_label,
        confidence_score=confidence_score,
        evidence_refs=evidence_refs,
        derivation_method="direct_rollup",
        uncertainty_note=None,
    )
    return _signal_entry("hydration", "hydration_intake_ml", field)


def _dedup_hydration_submission_replays(
    *,
    source_artifacts: list[dict[str, Any]],
    hydration_entries: list[dict[str, Any]],
    hydration_events: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    artifact_by_id = {
        artifact["artifact_id"]: artifact
        for artifact in source_artifacts
        if artifact.get("artifact_id")
    }
    entry_by_id = {
        entry["entry_id"]: entry
        for entry in hydration_entries
        if entry.get("entry_id")
    }
    candidates: dict[tuple[Any, ...], dict[str, Any]] = {}

    for entry in hydration_entries:
        fingerprint = _hydration_submission_fingerprint(entry=entry, artifact=artifact_by_id.get(entry.get("source_artifact_id")))
        candidate = candidates.setdefault(fingerprint, {})
        candidate_entry = candidate.get("entry")
        if candidate_entry is None or _hydration_entry_sort_key(entry, artifact_by_id) > _hydration_entry_sort_key(
            candidate_entry,
            artifact_by_id,
        ):
            candidate["entry"] = entry

    for event in hydration_events:
        entry = _hydration_event_manual_entry(event, entry_by_id)
        artifact = artifact_by_id.get(event.get("provenance", {}).get("artifact_id"))
        fingerprint = _hydration_submission_fingerprint(entry=entry, artifact=artifact, event=event)
        candidate = candidates.setdefault(fingerprint, {})
        candidate_event = candidate.get("event")
        if candidate_event is None or _hydration_event_sort_key(event, artifact_by_id) > _hydration_event_sort_key(
            candidate_event,
            artifact_by_id,
        ):
            candidate["event"] = event
        if entry is not None:
            candidate_entry = candidate.get("entry")
            if candidate_entry is None or _hydration_entry_sort_key(entry, artifact_by_id) > _hydration_entry_sort_key(
                candidate_entry,
                artifact_by_id,
            ):
                candidate["entry"] = entry

    canonical_entries = [
        candidate["entry"]
        for _, candidate in sorted(candidates.items())
        if candidate.get("entry") is not None
    ]
    canonical_events = [
        candidate["event"]
        for _, candidate in sorted(candidates.items())
        if candidate.get("event") is not None
    ]
    return canonical_entries, canonical_events


def _hydration_submission_fingerprint(
    *,
    entry: dict[str, Any] | None,
    artifact: dict[str, Any] | None,
    event: dict[str, Any] | None = None,
) -> tuple[Any, ...]:
    payload = entry.get("payload", {}) if entry is not None else {}
    return (
        entry.get("user_id") if entry is not None else event.get("user_id") if event is not None else None,
        entry.get("date") if entry is not None else event.get("effective_date") if event is not None else None,
        artifact.get("source_name") if artifact is not None else event.get("source_name") if event is not None else None,
        artifact.get("raw_location") if artifact is not None else None,
        payload.get("amount_ml") if entry is not None else event.get("value_number") if event is not None else None,
        payload.get("beverage_type"),
        payload.get("notes"),
        entry.get("completeness_state") if entry is not None else None,
    )


def _hydration_event_manual_entry(
    event: dict[str, Any],
    entry_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    for ref in event.get("provenance", {}).get("supporting_refs", []):
        if not ref.startswith("manual_log_entry:"):
            continue
        entry = entry_by_id.get(ref.split(":", 1)[1])
        if entry is not None:
            return entry
    return None


def _hydration_entry_sort_key(
    entry: dict[str, Any],
    artifact_by_id: dict[str, dict[str, Any]],
) -> tuple[str, str, str]:
    artifact = artifact_by_id.get(entry.get("source_artifact_id"), {})
    return (
        str(artifact.get("ingested_at") or ""),
        str(artifact.get("artifact_id") or ""),
        str(entry.get("entry_id") or ""),
    )


def _hydration_event_sort_key(
    event: dict[str, Any],
    artifact_by_id: dict[str, dict[str, Any]],
) -> tuple[str, str, str]:
    artifact = artifact_by_id.get(event.get("provenance", {}).get("artifact_id"), {})
    return (
        str(event.get("ingested_at") or artifact.get("ingested_at") or ""),
        str(artifact.get("artifact_id") or ""),
        str(event.get("event_id") or ""),
    )


def _conservative_confidence(records: list[dict[str, Any]]) -> tuple[str, float]:
    score = min(float(record.get("confidence_score", 0.0)) for record in records)
    if score >= 0.8:
        return "high", score
    if score >= 0.5:
        return "medium", score
    return "low", score


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _serialize(inner) for key, inner in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _serialize(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [_serialize(item) for item in value]
    return value
