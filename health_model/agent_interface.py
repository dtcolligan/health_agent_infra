from __future__ import annotations

from dataclasses import asdict
from typing import Any, Literal, TypedDict
from uuid import uuid4

from health_model.agent_readable_daily_context import build_agent_readable_daily_context
from health_model.manual_logging import (
    build_hydration_input_event,
    build_hydration_manual_log_entry,
    build_manual_logging_bundle,
    build_manual_source_artifact,
    build_nutrition_input_events,
    build_nutrition_text_note_manual_log_entry,
    build_simple_gym_set_manual_log_entry,
)
from health_model.shared_input_backbone import ValidationResult, validate_shared_input_bundle


class ValidationIssueDict(TypedDict):
    code: str
    message: str
    path: str


class ValidationPayload(TypedDict):
    is_valid: bool
    schema_issues: list[ValidationIssueDict]
    semantic_issues: list[ValidationIssueDict]


class ErrorPayload(TypedDict, total=False):
    code: str
    message: str
    retryable: bool
    details: dict[str, Any]


class BundleFragment(TypedDict):
    source_artifacts: list[dict[str, Any]]
    input_events: list[dict[str, Any]]
    subjective_daily_entries: list[dict[str, Any]]
    manual_log_entries: list[dict[str, Any]]


class IntakeProvenance(TypedDict, total=False):
    artifact_id: str
    entry_id: str
    event_id: str
    event_ids: list[str]


class IntakeResponse(TypedDict, total=False):
    ok: bool
    entry_kind: Literal["manual_log_entry"]
    artifact: dict[str, Any] | None
    entry: dict[str, Any] | None
    derived_events: list[dict[str, Any]]
    bundle_fragment: BundleFragment
    provenance: dict[str, Any]
    validation: ValidationPayload
    error: ErrorPayload | None


class BundleValidationResponse(TypedDict):
    ok: bool
    is_valid: bool
    schema_issues: list[ValidationIssueDict]
    semantic_issues: list[ValidationIssueDict]


class DailyContextErrorResponse(TypedDict):
    ok: Literal[False]
    error: ErrorPayload
    validation: ValidationPayload


def merge_bundle_fragments(*fragments: BundleFragment) -> dict[str, list[dict[str, Any]]]:
    bundle: dict[str, list[dict[str, Any]]] = {
        "source_artifacts": [],
        "input_events": [],
        "subjective_daily_entries": [],
        "manual_log_entries": [],
    }
    for fragment in fragments:
        bundle["source_artifacts"].extend(dict(artifact) for artifact in fragment.get("source_artifacts", []))
        bundle["input_events"].extend(dict(event) for event in fragment.get("input_events", []))
        bundle["subjective_daily_entries"].extend(
            dict(entry) for entry in fragment.get("subjective_daily_entries", [])
        )
        bundle["manual_log_entries"].extend(dict(entry) for entry in fragment.get("manual_log_entries", []))
    return bundle


def submit_nutrition_text_note(
    *,
    user_id: str,
    date: str,
    note_text: str,
    collected_at: str,
    ingested_at: str,
    raw_location: str,
    confidence_score: float,
    meal_label: str | None = None,
    estimated: bool = True,
    completeness_state: Literal["partial", "complete", "corrected"],
    source_name: str = "manual_nutrition_log",
    notes: str | None = None,
) -> IntakeResponse:
    artifact = _build_manual_artifact(
        user_id=user_id,
        source_name=source_name,
        collected_at=collected_at,
        ingested_at=ingested_at,
        raw_location=raw_location,
        notes=notes,
    )
    entry = build_nutrition_text_note_manual_log_entry(
        entry_id=_new_id("manual"),
        user_id=user_id,
        date=date,
        source_artifact_id=artifact["artifact_id"],
        note_text=note_text,
        meal_label=meal_label,
        estimated=estimated,
        completeness_state=completeness_state,
        confidence_score=confidence_score,
    )
    derived_events = build_nutrition_input_events(
        event_id_prefix=_new_id("event"),
        source_record_id=entry["entry_id"],
        manual_entry=entry,
        artifact=artifact,
    )
    bundle_fragment = build_manual_logging_bundle(
        source_artifact=artifact,
        manual_log_entries=[entry],
        input_events=derived_events,
    )
    return _finalize_intake_response(
        artifact=artifact,
        entry=entry,
        bundle_fragment=bundle_fragment,
        derived_events=derived_events,
    )


def submit_hydration_log(
    *,
    user_id: str,
    date: str,
    amount_ml: float,
    collected_at: str,
    ingested_at: str,
    raw_location: str,
    confidence_score: float,
    beverage_type: str | None = None,
    completeness_state: Literal["partial", "complete", "corrected"],
    source_name: str = "manual_hydration_log",
    notes: str | None = None,
) -> IntakeResponse:
    artifact = _build_manual_artifact(
        user_id=user_id,
        source_name=source_name,
        collected_at=collected_at,
        ingested_at=ingested_at,
        raw_location=raw_location,
        notes=notes,
    )
    entry = build_hydration_manual_log_entry(
        entry_id=_new_id("manual"),
        user_id=user_id,
        date=date,
        source_artifact_id=artifact["artifact_id"],
        amount_ml=amount_ml,
        beverage_type=beverage_type,
        completeness_state=completeness_state,
        confidence_score=confidence_score,
        notes=notes,
    )
    event = build_hydration_input_event(
        event_id=_new_id("event"),
        source_record_id=entry["entry_id"],
        manual_entry=entry,
        artifact=artifact,
    )
    bundle_fragment = build_manual_logging_bundle(
        source_artifact=artifact,
        manual_log_entries=[entry],
        input_events=[event],
    )
    return _finalize_intake_response(
        artifact=artifact,
        entry=entry,
        bundle_fragment=bundle_fragment,
        derived_events=[event],
    )


def submit_gym_set(
    *,
    user_id: str,
    date: str,
    exercise_name: str,
    set_index: int,
    reps: int,
    weight_kg: float,
    collected_at: str,
    ingested_at: str,
    raw_location: str,
    confidence_score: float,
    completeness_state: Literal["partial", "complete", "corrected"],
    source_name: str = "manual_gym_log",
) -> IntakeResponse:
    artifact = _build_manual_artifact(
        user_id=user_id,
        source_name=source_name,
        collected_at=collected_at,
        ingested_at=ingested_at,
        raw_location=raw_location,
    )
    entry = build_simple_gym_set_manual_log_entry(
        entry_id=_new_id("manual"),
        user_id=user_id,
        date=date,
        source_artifact_id=artifact["artifact_id"],
        exercise_name=exercise_name,
        set_index=set_index,
        reps=reps,
        weight_kg=weight_kg,
        completeness_state=completeness_state,
        confidence_score=confidence_score,
    )
    bundle_fragment = build_manual_logging_bundle(
        source_artifact=artifact,
        manual_log_entries=[entry],
    )
    return _finalize_intake_response(
        artifact=artifact,
        entry=entry,
        bundle_fragment=bundle_fragment,
        derived_events=[],
    )


def build_daily_context(
    *,
    bundle: dict[str, Any],
    user_id: str,
    date: str,
) -> dict[str, Any] | DailyContextErrorResponse:
    validation = validate_shared_input_bundle(bundle)
    if not validation.is_valid:
        return {
            "ok": False,
            "error": {
                "code": "invalid_bundle",
                "message": "Shared input bundle failed validation.",
                "retryable": False,
                "details": {"user_id": user_id, "date": date},
            },
            "validation": _validation_payload(validation),
        }
    return build_agent_readable_daily_context(bundle, user_id=user_id, date=date)


def validate_bundle(*, bundle: dict[str, Any]) -> BundleValidationResponse:
    validation = validate_shared_input_bundle(bundle)
    payload = _validation_payload(validation)
    return {
        "ok": True,
        "is_valid": payload["is_valid"],
        "schema_issues": payload["schema_issues"],
        "semantic_issues": payload["semantic_issues"],
    }


def _build_manual_artifact(
    *,
    user_id: str,
    source_name: str,
    collected_at: str,
    ingested_at: str,
    raw_location: str,
    notes: str | None = None,
) -> dict[str, Any]:
    return build_manual_source_artifact(
        artifact_id=_new_id("artifact"),
        user_id=user_id,
        source_name=source_name,
        collected_at=collected_at,
        ingested_at=ingested_at,
        raw_location=raw_location,
        notes=notes,
    )


def _finalize_intake_response(
    *,
    artifact: dict[str, Any],
    entry: dict[str, Any],
    bundle_fragment: BundleFragment,
    derived_events: list[dict[str, Any]],
) -> IntakeResponse:
    validation = validate_shared_input_bundle(bundle_fragment)
    if not validation.is_valid:
        response: IntakeResponse = {
            "ok": False,
            "entry_kind": "manual_log_entry",
            "artifact": artifact,
            "entry": entry,
            "bundle_fragment": bundle_fragment,
            "provenance": _provenance_payload(artifact, entry, derived_events),
            "validation": _validation_payload(validation),
            "error": {
                "code": "invalid_bundle_fragment",
                "message": "Generated bundle fragment failed canonical validation.",
                "retryable": False,
            },
        }
        if derived_events:
            response["derived_events"] = derived_events
        return response

    response = {
        "ok": True,
        "entry_kind": "manual_log_entry",
        "artifact": artifact,
        "entry": entry,
        "bundle_fragment": bundle_fragment,
        "provenance": _provenance_payload(artifact, entry, derived_events),
        "validation": _validation_payload(validation),
        "error": None,
    }
    if derived_events:
        response["derived_events"] = derived_events
    return response


def _provenance_payload(
    artifact: dict[str, Any],
    entry: dict[str, Any],
    derived_events: list[dict[str, Any]],
) -> IntakeProvenance:
    provenance: IntakeProvenance = {
        "artifact_id": artifact["artifact_id"],
        "entry_id": entry["entry_id"],
    }
    if derived_events:
        provenance["event_id"] = derived_events[0]["event_id"]
        provenance["event_ids"] = [event["event_id"] for event in derived_events]
    return provenance


def _validation_payload(validation: ValidationResult) -> ValidationPayload:
    return {
        "is_valid": validation.is_valid,
        "schema_issues": [asdict(issue) for issue in validation.schema_issues],
        "semantic_issues": [asdict(issue) for issue in validation.semantic_issues],
    }


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
