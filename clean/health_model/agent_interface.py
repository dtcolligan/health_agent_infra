from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
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


ALLOWED_ATOMIC_APPEND_LOG_TYPES = {"meal", "hydration"}


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


class PersistedBundleAppendResponse(TypedDict, total=False):
    ok: bool
    bundle_path: str
    bundle: dict[str, Any] | None
    appended_fragment: BundleFragment | None
    validation: ValidationPayload
    error: ErrorPayload | None


class AppendRegenerateResponse(TypedDict, total=False):
    ok: bool
    bundle_path: str
    dated_artifact_path: str | None
    latest_artifact_path: str | None
    accepted_provenance: dict[str, list[str] | str]
    validation: ValidationPayload
    error: ErrorPayload | None


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


def load_persisted_bundle(*, bundle_path: str) -> dict[str, Any]:
    return json.loads(Path(bundle_path).read_text())



def write_persisted_bundle(*, bundle_path: str, bundle: dict[str, Any]) -> str:
    path = Path(bundle_path)
    validation = validate_shared_input_bundle(bundle)
    if not validation.is_valid:
        raise BundleValidationError(
            code="invalid_bundle",
            message="Shared input bundle failed validation.",
            validation=validation,
            details={"bundle_path": str(path)},
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")
    return str(path)



def append_bundle_fragment_to_persisted_bundle(
    *,
    bundle_path: str,
    fragment: BundleFragment,
    user_id: str,
    date: str,
) -> PersistedBundleAppendResponse:
    fragment_validation = validate_shared_input_bundle(fragment)
    if not fragment_validation.is_valid:
        return {
            "ok": False,
            "bundle_path": bundle_path,
            "bundle": None,
            "appended_fragment": fragment,
            "validation": _validation_payload(fragment_validation),
            "error": {
                "code": "invalid_bundle_fragment",
                "message": "Generated bundle fragment failed canonical validation.",
                "retryable": False,
                "details": {"user_id": user_id, "date": date},
            },
        }

    scoping_issues = _bundle_fragment_scoping_issues(fragment=fragment, user_id=user_id, date=date)
    if scoping_issues:
        validation = ValidationResult(bundle=None, schema_issues=[], semantic_issues=scoping_issues)
        return {
            "ok": False,
            "bundle_path": bundle_path,
            "bundle": None,
            "appended_fragment": fragment,
            "validation": _validation_payload(validation),
            "error": {
                "code": "bundle_fragment_scope_mismatch",
                "message": "Bundle fragment must match the requested user_id and date.",
                "retryable": False,
                "details": {"user_id": user_id, "date": date},
            },
        }

    base_bundle = load_persisted_bundle(bundle_path=bundle_path)
    merged_bundle = merge_bundle_fragments(base_bundle, fragment)
    merged_validation = validate_shared_input_bundle(merged_bundle)
    if not merged_validation.is_valid:
        return {
            "ok": False,
            "bundle_path": bundle_path,
            "bundle": None,
            "appended_fragment": fragment,
            "validation": _validation_payload(merged_validation),
            "error": {
                "code": "invalid_merged_bundle",
                "message": "Merged shared input bundle failed canonical validation.",
                "retryable": False,
                "details": {"user_id": user_id, "date": date},
            },
        }

    write_persisted_bundle(bundle_path=bundle_path, bundle=merged_bundle)
    return {
        "ok": True,
        "bundle_path": bundle_path,
        "bundle": merged_bundle,
        "appended_fragment": fragment,
        "validation": _validation_payload(merged_validation),
        "error": None,
    }



def append_fragment_and_regenerate_daily_context(
    *,
    bundle_path: str,
    output_dir: str,
    fragment: BundleFragment,
    user_id: str,
    date: str,
) -> AppendRegenerateResponse:
    fragment_validation = validate_shared_input_bundle(fragment)
    if not fragment_validation.is_valid:
        return {
            "ok": False,
            "bundle_path": bundle_path,
            "dated_artifact_path": None,
            "latest_artifact_path": None,
            "accepted_provenance": {},
            "validation": _validation_payload(fragment_validation),
            "error": {
                "code": "invalid_bundle_fragment",
                "message": "Generated bundle fragment failed canonical validation.",
                "retryable": False,
                "details": {"user_id": user_id, "date": date},
            },
        }

    scoping_issues = _bundle_fragment_scoping_issues(fragment=fragment, user_id=user_id, date=date)
    log_type_issues = _bundle_fragment_log_type_issues(fragment=fragment)
    semantic_issues = [*scoping_issues, *log_type_issues]
    if semantic_issues:
        validation = ValidationResult(bundle=None, schema_issues=[], semantic_issues=semantic_issues)
        error_code = "bundle_fragment_scope_mismatch" if scoping_issues else "unsupported_bundle_fragment"
        error_message = (
            "Bundle fragment must match the requested user_id and date."
            if scoping_issues
            else "Bundle fragment must contain only meal or hydration manual log entries."
        )
        return {
            "ok": False,
            "bundle_path": bundle_path,
            "dated_artifact_path": None,
            "latest_artifact_path": None,
            "accepted_provenance": {},
            "validation": _validation_payload(validation),
            "error": {
                "code": error_code,
                "message": error_message,
                "retryable": False,
                "details": {"user_id": user_id, "date": date},
            },
        }

    bundle_file = Path(bundle_path)
    original_bundle_text = bundle_file.read_text()
    base_bundle = json.loads(original_bundle_text)
    merged_bundle = merge_bundle_fragments(base_bundle, fragment)
    merged_validation = validate_shared_input_bundle(merged_bundle)
    if not merged_validation.is_valid:
        return {
            "ok": False,
            "bundle_path": bundle_path,
            "dated_artifact_path": None,
            "latest_artifact_path": None,
            "accepted_provenance": {},
            "validation": _validation_payload(merged_validation),
            "error": {
                "code": "invalid_merged_bundle",
                "message": "Merged shared input bundle failed canonical validation.",
                "retryable": False,
                "details": {"user_id": user_id, "date": date},
            },
        }

    try:
        from health_model.build_daily_context_artifact import build_daily_context_artifact

        write_persisted_bundle(bundle_path=bundle_path, bundle=merged_bundle)
        artifact_result = build_daily_context_artifact(
            bundle_path=bundle_path,
            user_id=user_id,
            date=date,
            output_dir=output_dir,
        )
    except Exception:
        bundle_file.write_text(original_bundle_text)
        raise

    return {
        "ok": True,
        "bundle_path": bundle_path,
        "dated_artifact_path": artifact_result["dated_path"],
        "latest_artifact_path": artifact_result["latest_path"],
        "accepted_provenance": _accepted_provenance_payload(fragment),
        "validation": _validation_payload(merged_validation),
        "error": None,
    }


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


class BundleValidationError(ValueError):
    def __init__(self, *, code: str, message: str, validation: ValidationResult, details: dict[str, Any] | None = None) -> None:
        self.code = code
        self.validation = validation
        self.details = details or {}
        super().__init__(message)



def _bundle_fragment_scoping_issues(*, fragment: BundleFragment, user_id: str, date: str) -> list[Any]:
    issues = []
    for index, artifact in enumerate(fragment.get("source_artifacts", [])):
        if artifact.get("user_id") != user_id:
            issues.append(_issue("user_id_mismatch", "Source artifact user_id must match the requested user_id.", f"source_artifacts[{index}].user_id"))
    for index, event in enumerate(fragment.get("input_events", [])):
        if event.get("user_id") != user_id:
            issues.append(_issue("user_id_mismatch", "Input event user_id must match the requested user_id.", f"input_events[{index}].user_id"))
        if event.get("effective_date") != date:
            issues.append(_issue("effective_date_mismatch", "Input event effective_date must match the requested date.", f"input_events[{index}].effective_date"))
    for index, entry in enumerate(fragment.get("subjective_daily_entries", [])):
        if entry.get("user_id") != user_id:
            issues.append(_issue("user_id_mismatch", "Subjective daily entry user_id must match the requested user_id.", f"subjective_daily_entries[{index}].user_id"))
        if entry.get("date") != date:
            issues.append(_issue("date_mismatch", "Subjective daily entry date must match the requested date.", f"subjective_daily_entries[{index}].date"))
    for index, entry in enumerate(fragment.get("manual_log_entries", [])):
        if entry.get("user_id") != user_id:
            issues.append(_issue("user_id_mismatch", "Manual log entry user_id must match the requested user_id.", f"manual_log_entries[{index}].user_id"))
        if entry.get("date") != date:
            issues.append(_issue("date_mismatch", "Manual log entry date must match the requested date.", f"manual_log_entries[{index}].date"))
    return issues



def _bundle_fragment_log_type_issues(*, fragment: BundleFragment) -> list[Any]:
    issues = []
    for index, entry in enumerate(fragment.get("manual_log_entries", [])):
        log_type = entry.get("log_type")
        if log_type not in ALLOWED_ATOMIC_APPEND_LOG_TYPES:
            issues.append(
                _issue(
                    "unsupported_manual_log_type",
                    "Manual log entry log_type must be meal or hydration for atomic append-and-regenerate.",
                    f"manual_log_entries[{index}].log_type",
                )
            )
    return issues


def _accepted_provenance_payload(fragment: BundleFragment) -> dict[str, list[str] | str]:
    return {
        "source_artifact_ids": [artifact["artifact_id"] for artifact in fragment.get("source_artifacts", [])],
        "input_event_ids": [event["event_id"] for event in fragment.get("input_events", [])],
        "subjective_entry_ids": [entry["entry_id"] for entry in fragment.get("subjective_daily_entries", [])],
        "manual_log_entry_ids": [entry["entry_id"] for entry in fragment.get("manual_log_entries", [])],
    }


def _issue(code: str, message: str, path: str) -> Any:
    from health_model.shared_input_backbone import ValidationIssue

    return ValidationIssue(code=code, message=message, path=path)



def _validation_payload(validation: ValidationResult) -> ValidationPayload:
    return {
        "is_valid": validation.is_valid,
        "schema_issues": [asdict(issue) for issue in validation.schema_issues],
        "semantic_issues": [asdict(issue) for issue in validation.semantic_issues],
    }


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
