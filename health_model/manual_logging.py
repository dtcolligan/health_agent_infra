from __future__ import annotations

from typing import Any

from health_model.shared_input_backbone import (
    CaptureMode,
    ConfidenceLabel,
    ConflictStatus,
    DerivationMethod,
    Domain,
    ManualLogType,
    MissingnessState,
    SourceType,
    ValueType,
)


def build_manual_source_artifact(
    *,
    artifact_id: str,
    user_id: str,
    source_name: str,
    collected_at: str,
    ingested_at: str,
    raw_location: str,
    raw_format: str = "json",
    source_record_id: str | None = None,
    hash_or_version: str | None = None,
    parser_version: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "user_id": user_id,
        "source_type": SourceType.MANUAL.value,
        "source_name": source_name,
        "source_record_id": source_record_id,
        "collected_at": collected_at,
        "ingested_at": ingested_at,
        "raw_location": raw_location,
        "raw_format": raw_format,
        "hash_or_version": hash_or_version,
        "parser_version": parser_version,
        "notes": notes,
    }


def build_hydration_manual_log_entry(
    *,
    entry_id: str,
    user_id: str,
    date: str,
    source_artifact_id: str,
    amount_ml: float,
    completeness_state: str,
    confidence_score: float,
    beverage_type: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"amount_ml": amount_ml}
    if beverage_type is not None:
        payload["beverage_type"] = beverage_type
    if notes is not None:
        payload["notes"] = notes

    return {
        "entry_id": entry_id,
        "user_id": user_id,
        "date": date,
        "log_type": ManualLogType.HYDRATION.value,
        "payload": payload,
        "source_artifact_id": source_artifact_id,
        "completeness_state": completeness_state,
        "confidence_label": _confidence_label_for_score(confidence_score),
        "confidence_score": confidence_score,
    }


def build_nutrition_text_note_manual_log_entry(
    *,
    entry_id: str,
    user_id: str,
    date: str,
    source_artifact_id: str,
    note_text: str,
    completeness_state: str,
    confidence_score: float,
    meal_label: str | None = None,
    estimated: bool | None = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"notes": note_text}
    if meal_label is not None:
        payload["meal_label"] = meal_label
    if estimated is not None:
        payload["estimated"] = estimated

    return {
        "entry_id": entry_id,
        "user_id": user_id,
        "date": date,
        "log_type": ManualLogType.MEAL.value,
        "payload": payload,
        "source_artifact_id": source_artifact_id,
        "completeness_state": completeness_state,
        "confidence_label": _confidence_label_for_score(confidence_score),
        "confidence_score": confidence_score,
    }


def build_exercise_set_manual_log_entry(
    *,
    entry_id: str,
    user_id: str,
    date: str,
    source_artifact_id: str,
    exercise_name: str,
    set_index: int,
    completeness_state: str,
    confidence_score: float,
    reps: int | None = None,
    weight_kg: float | None = None,
    rir: int | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "exercise_name": exercise_name,
        "set_index": set_index,
    }
    if reps is not None:
        payload["reps"] = reps
    if weight_kg is not None:
        payload["weight_kg"] = weight_kg
    if rir is not None:
        payload["rir"] = rir
    if notes is not None:
        payload["notes"] = notes

    return {
        "entry_id": entry_id,
        "user_id": user_id,
        "date": date,
        "log_type": ManualLogType.EXERCISE_SET.value,
        "payload": payload,
        "source_artifact_id": source_artifact_id,
        "completeness_state": completeness_state,
        "confidence_label": _confidence_label_for_score(confidence_score),
        "confidence_score": confidence_score,
    }


def build_simple_gym_set_manual_log_entry(
    *,
    entry_id: str,
    user_id: str,
    date: str,
    source_artifact_id: str,
    exercise_name: str,
    set_index: int,
    reps: int,
    weight_kg: float,
    completeness_state: str,
    confidence_score: float,
) -> dict[str, Any]:
    return build_exercise_set_manual_log_entry(
        entry_id=entry_id,
        user_id=user_id,
        date=date,
        source_artifact_id=source_artifact_id,
        exercise_name=exercise_name,
        set_index=set_index,
        reps=reps,
        weight_kg=weight_kg,
        completeness_state=completeness_state,
        confidence_score=confidence_score,
    )


def build_hydration_input_event(
    *,
    event_id: str,
    source_record_id: str,
    manual_entry: dict[str, Any],
    artifact: dict[str, Any],
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "user_id": manual_entry["user_id"],
        "source_type": SourceType.MANUAL.value,
        "source_name": artifact["source_name"],
        "source_record_id": source_record_id,
        "capture_mode": CaptureMode.DERIVED.value,
        "domain": Domain.HYDRATION.value,
        "metric_name": "hydration_amount_ml",
        "value_type": ValueType.NUMBER.value,
        "value_number": manual_entry["payload"]["amount_ml"],
        "unit": "ml",
        "event_start_at": None,
        "event_end_at": None,
        "effective_date": manual_entry["date"],
        "ingested_at": artifact["ingested_at"],
        "confidence_label": manual_entry["confidence_label"],
        "confidence_score": manual_entry["confidence_score"],
        "missingness_state": MissingnessState.PRESENT.value,
        "provenance": _manual_entry_provenance(artifact, manual_entry),
    }


def build_nutrition_input_events(
    *,
    event_id_prefix: str,
    source_record_id: str,
    manual_entry: dict[str, Any],
    artifact: dict[str, Any],
) -> list[dict[str, Any]]:
    payload = manual_entry["payload"]
    events = [
        {
            "event_id": f"{event_id_prefix}_meal_logged",
            "user_id": manual_entry["user_id"],
            "source_type": SourceType.MANUAL.value,
            "source_name": artifact["source_name"],
            "source_record_id": source_record_id,
            "capture_mode": CaptureMode.DERIVED.value,
            "domain": Domain.NUTRITION.value,
            "metric_name": "meal_logged",
            "value_type": ValueType.BOOLEAN.value,
            "value_boolean": True,
            "event_start_at": None,
            "event_end_at": None,
            "effective_date": manual_entry["date"],
            "ingested_at": artifact["ingested_at"],
            "confidence_label": manual_entry["confidence_label"],
            "confidence_score": manual_entry["confidence_score"],
            "missingness_state": MissingnessState.PRESENT.value,
            "provenance": _manual_entry_provenance(artifact, manual_entry),
        }
    ]
    estimated = payload.get("estimated")
    events.append(
        {
            "event_id": f"{event_id_prefix}_meal_estimated_flag",
            "user_id": manual_entry["user_id"],
            "source_type": SourceType.MANUAL.value,
            "source_name": artifact["source_name"],
            "source_record_id": source_record_id,
            "capture_mode": CaptureMode.DERIVED.value,
            "domain": Domain.NUTRITION.value,
            "metric_name": "meal_estimated_flag",
            "value_type": ValueType.BOOLEAN.value,
            "value_boolean": estimated if estimated is not None else None,
            "event_start_at": None,
            "event_end_at": None,
            "effective_date": manual_entry["date"],
            "ingested_at": artifact["ingested_at"],
            "confidence_label": manual_entry["confidence_label"],
            "confidence_score": manual_entry["confidence_score"],
            "missingness_state": (
                MissingnessState.PRESENT.value
                if estimated is not None
                else MissingnessState.MISSING_NOT_PROVIDED.value
            ),
            "provenance": _manual_entry_provenance(artifact, manual_entry),
        }
    )
    meal_label = payload.get("meal_label")
    if meal_label is not None:
        events.append(
            {
                "event_id": f"{event_id_prefix}_meal_label",
                "user_id": manual_entry["user_id"],
                "source_type": SourceType.MANUAL.value,
                "source_name": artifact["source_name"],
                "source_record_id": source_record_id,
                "capture_mode": CaptureMode.DERIVED.value,
                "domain": Domain.NUTRITION.value,
                "metric_name": "meal_label",
                "value_type": ValueType.STRING.value,
                "value_string": meal_label,
                "event_start_at": None,
                "event_end_at": None,
                "effective_date": manual_entry["date"],
                "ingested_at": artifact["ingested_at"],
                "confidence_label": manual_entry["confidence_label"],
                "confidence_score": manual_entry["confidence_score"],
                "missingness_state": MissingnessState.PRESENT.value,
                "provenance": _manual_entry_provenance(artifact, manual_entry),
            }
        )
    return events


def build_manual_logging_bundle(
    *,
    source_artifact: dict[str, Any],
    manual_log_entries: list[dict[str, Any]],
    input_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "source_artifacts": [_drop_none_values(source_artifact)],
        "input_events": [dict(event) for event in (input_events or [])],
        "subjective_daily_entries": [],
        "manual_log_entries": [_drop_none_values(entry) for entry in manual_log_entries],
    }


def _manual_entry_provenance(artifact: dict[str, Any], manual_entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "artifact_id": artifact["artifact_id"],
        "derivation_method": DerivationMethod.MANUAL_FORM_NORMALIZATION.value,
        "supporting_refs": [f"manual_log_entry:{manual_entry['entry_id']}"],
        "parser_version": artifact.get("parser_version"),
        "conflict_status": ConflictStatus.NONE.value,
    }


def _confidence_label_for_score(score: float) -> str:
    if score >= 0.8:
        return ConfidenceLabel.HIGH.value
    if score >= 0.5:
        return ConfidenceLabel.MEDIUM.value
    return ConfidenceLabel.LOW.value


def _drop_none_values(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}
