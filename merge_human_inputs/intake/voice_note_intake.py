from __future__ import annotations

from typing import Any, Mapping

from health_model.shared_input_backbone import (
    CaptureMode,
    ConfidenceLabel,
    ConflictStatus,
    DerivationMethod,
    Domain,
    ExtractionStatus,
    MissingnessState,
    SourceType,
    ValueType,
)


def build_voice_note_source_artifact(
    *,
    artifact_id: str,
    user_id: str,
    collected_at: str,
    ingested_at: str,
    raw_location: str,
    raw_format: str,
    transcript_ref: str,
    source_name: str = "daily_voice_note",
    source_record_id: str | None = None,
    hash_or_version: str | None = None,
    parser_version: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    return _drop_none_values(
        {
            "artifact_id": artifact_id,
            "user_id": user_id,
            "source_type": SourceType.VOICE_NOTE.value,
            "source_name": source_name,
            "source_record_id": source_record_id,
            "collected_at": collected_at,
            "ingested_at": ingested_at,
            "raw_location": raw_location,
            "raw_format": raw_format,
            "hash_or_version": hash_or_version,
            "transcript_ref": transcript_ref,
            "parser_version": parser_version,
            "notes": notes,
        }
    )


def build_voice_note_input_event(
    *,
    event_id: str,
    user_id: str,
    artifact: Mapping[str, Any],
    source_record_id: str,
    domain: str,
    metric_name: str,
    value_type: str,
    effective_date: str,
    confidence_score: float,
    supporting_refs: list[str],
    value: Any = None,
    unit: str | None = None,
    missingness_state: str = "present",
    uncertainty_note: str | None = None,
    event_start_at: str | None = None,
    event_end_at: str | None = None,
    derivation_method: str = "voice_extraction",
    conflict_status: str = "none",
) -> dict[str, Any]:
    missingness = MissingnessState(missingness_state)
    typed_value = _typed_event_value(value_type=value_type, value=value, unit=unit, missingness=missingness)

    event = _drop_none_values(
        {
            "event_id": event_id,
            "user_id": user_id,
            "source_type": SourceType.VOICE_NOTE.value,
            "source_name": artifact["source_name"],
            "source_record_id": source_record_id,
            "capture_mode": CaptureMode.DERIVED.value,
            "domain": Domain(domain).value,
            "metric_name": metric_name,
            "value_type": ValueType(value_type).value,
            "value_number": typed_value["value_number"],
            "value_string": typed_value["value_string"],
            "value_boolean": typed_value["value_boolean"],
            "value_json": typed_value["value_json"],
            "unit": typed_value["unit"],
            "effective_date": effective_date,
            "ingested_at": artifact["ingested_at"],
            "confidence_label": _confidence_label_for_score(confidence_score),
            "confidence_score": confidence_score,
            "missingness_state": missingness.value,
            "uncertainty_note": uncertainty_note,
            "provenance": {
                "artifact_id": artifact["artifact_id"],
                "derivation_method": DerivationMethod(derivation_method).value,
                "supporting_refs": supporting_refs,
                "parser_version": artifact.get("parser_version"),
                "conflict_status": ConflictStatus(conflict_status).value,
            },
        }
    )
    event["event_start_at"] = event_start_at
    event["event_end_at"] = event_end_at
    return event


def build_subjective_daily_entry_from_voice_note(
    *,
    entry_id: str,
    user_id: str,
    date: str,
    source_artifact_id: str,
    free_text_summary: str,
    extraction_status: str,
    confidence_score: float,
    energy_self_rating: int | None = None,
    stress_self_rating: int | None = None,
    mood_self_rating: int | None = None,
    perceived_sleep_quality: int | None = None,
    illness_or_soreness_flag: bool | None = None,
) -> dict[str, Any]:
    return _drop_none_values(
        {
            "entry_id": entry_id,
            "user_id": user_id,
            "date": date,
            "energy_self_rating": energy_self_rating,
            "stress_self_rating": stress_self_rating,
            "mood_self_rating": mood_self_rating,
            "perceived_sleep_quality": perceived_sleep_quality,
            "illness_or_soreness_flag": illness_or_soreness_flag,
            "free_text_summary": free_text_summary,
            "extraction_status": ExtractionStatus(extraction_status).value,
            "source_artifact_ids": [source_artifact_id],
            "confidence_label": _confidence_label_for_score(confidence_score),
            "confidence_score": confidence_score,
        }
    )


def build_voice_note_intake_bundle(
    *,
    source_artifact: dict[str, Any],
    input_events: list[dict[str, Any]] | None = None,
    subjective_daily_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    subjective_entries = []
    if subjective_daily_entry is not None:
        subjective_entries.append(_drop_none_values(subjective_daily_entry))

    return {
        "source_artifacts": [_drop_none_values(source_artifact)],
        "input_events": list(input_events or []),
        "subjective_daily_entries": subjective_entries,
        "manual_log_entries": [],
    }


def canonicalize_voice_note_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    note = payload["voice_note"]
    artifact = build_voice_note_source_artifact(
        artifact_id=payload["artifact_id"],
        user_id=payload["user_id"],
        source_name=note.get("source_name", "daily_voice_note"),
        source_record_id=note.get("source_record_id"),
        collected_at=note["collected_at"],
        ingested_at=note["ingested_at"],
        raw_location=note["raw_location"],
        raw_format=note["raw_format"],
        hash_or_version=note.get("hash_or_version"),
        transcript_ref=payload["transcript"]["transcript_ref"],
        parser_version=payload.get("parser_version") or note.get("parser_version"),
        notes=note.get("notes"),
    )
    input_events = [
        build_voice_note_input_event(
            event_id=event_spec["event_id"],
            user_id=payload["user_id"],
            artifact=artifact,
            source_record_id=event_spec["source_record_id"],
            domain=event_spec["domain"],
            metric_name=event_spec["metric_name"],
            value_type=event_spec["value_type"],
            value=event_spec.get("value"),
            unit=event_spec.get("unit"),
            effective_date=event_spec["effective_date"],
            confidence_score=event_spec["confidence_score"],
            supporting_refs=list(event_spec.get("supporting_refs", [])),
            missingness_state=event_spec.get("missingness_state", "present"),
            uncertainty_note=event_spec.get("uncertainty_note"),
            event_start_at=event_spec.get("event_start_at"),
            event_end_at=event_spec.get("event_end_at"),
            derivation_method=event_spec.get("derivation_method", "voice_extraction"),
            conflict_status=event_spec.get("conflict_status", "none"),
        )
        for event_spec in payload.get("derived_events", [])
    ]

    subjective_entry = None
    if payload.get("subjective_entry") is not None:
        entry = payload["subjective_entry"]
        subjective_entry = build_subjective_daily_entry_from_voice_note(
            entry_id=entry["entry_id"],
            user_id=payload["user_id"],
            date=entry["date"],
            source_artifact_id=artifact["artifact_id"],
            free_text_summary=entry["free_text_summary"],
            extraction_status=entry["extraction_status"],
            confidence_score=entry["confidence_score"],
            energy_self_rating=entry.get("energy_self_rating"),
            stress_self_rating=entry.get("stress_self_rating"),
            mood_self_rating=entry.get("mood_self_rating"),
            perceived_sleep_quality=entry.get("perceived_sleep_quality"),
            illness_or_soreness_flag=entry.get("illness_or_soreness_flag"),
        )

    return build_voice_note_intake_bundle(
        source_artifact=artifact,
        input_events=input_events,
        subjective_daily_entry=subjective_entry,
    )


def _typed_event_value(*, value_type: str, value: Any, unit: str | None, missingness: MissingnessState) -> dict[str, Any]:
    if missingness is not MissingnessState.PRESENT:
        return {
            "value_number": None,
            "value_string": None,
            "value_boolean": None,
            "value_json": None,
            "unit": None,
        }

    typed_value = ValueType(value_type)
    if typed_value is ValueType.NUMBER:
        return {
            "value_number": float(value),
            "value_string": None,
            "value_boolean": None,
            "value_json": None,
            "unit": unit,
        }
    if typed_value in {ValueType.STRING, ValueType.ENUM}:
        return {
            "value_number": None,
            "value_string": str(value),
            "value_boolean": None,
            "value_json": None,
            "unit": None,
        }
    if typed_value is ValueType.BOOLEAN:
        if not isinstance(value, bool):
            raise ValueError("Boolean voice-note values must be bool.")
        return {
            "value_number": None,
            "value_string": None,
            "value_boolean": value,
            "value_json": None,
            "unit": None,
        }
    if typed_value is ValueType.JSON:
        if not isinstance(value, dict):
            raise ValueError("JSON voice-note values must be objects.")
        return {
            "value_number": None,
            "value_string": None,
            "value_boolean": None,
            "value_json": value,
            "unit": None,
        }
    raise ValueError(f"Unsupported value_type: {value_type}")


def _confidence_label_for_score(score: float) -> str:
    if score >= 0.8:
        return ConfidenceLabel.HIGH.value
    if score >= 0.5:
        return ConfidenceLabel.MEDIUM.value
    return ConfidenceLabel.LOW.value


def _drop_none_values(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}
