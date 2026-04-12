from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError


class SourceType(str, Enum):
    WEARABLE = "wearable"
    VOICE_NOTE = "voice_note"
    MANUAL = "manual"
    IMPORTED_FOOD_PIPELINE = "imported_food_pipeline"


class CaptureMode(str, Enum):
    PASSIVE = "passive"
    SELF_REPORTED = "self_reported"
    DERIVED = "derived"


class Domain(str, Enum):
    SLEEP = "sleep"
    RUNNING = "running"
    GYM = "gym"
    NUTRITION = "nutrition"
    HYDRATION = "hydration"
    SUBJECTIVE = "subjective"
    CONTEXT = "context"


class MissingnessState(str, Enum):
    PRESENT = "present"
    MISSING_NOT_PROVIDED = "missing_not_provided"
    MISSING_NOT_AVAILABLE_FROM_SOURCE = "missing_not_available_from_source"
    MISSING_PARSE_FAILED = "missing_parse_failed"
    MISSING_CONFLICT_UNRESOLVED = "missing_conflict_unresolved"


class ConfidenceLabel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValueType(str, Enum):
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    ENUM = "enum"
    JSON = "json"


class RawFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    TXT = "txt"
    MD = "md"
    M4A = "m4a"
    MP3 = "mp3"
    WAV = "wav"
    OTHER = "other"


class ExtractionStatus(str, Enum):
    NOT_NEEDED = "not_needed"
    PENDING = "pending"
    PARTIAL = "partial"
    COMPLETE = "complete"
    FAILED = "failed"


class ManualLogType(str, Enum):
    GYM_SESSION = "gym_session"
    EXERCISE_SET = "exercise_set"
    MEAL = "meal"
    HYDRATION = "hydration"
    BODY_SIGNAL = "body_signal"
    CONTEXT_NOTE = "context_note"


class CompletenessState(str, Enum):
    PARTIAL = "partial"
    COMPLETE = "complete"
    CORRECTED = "corrected"


class DerivationMethod(str, Enum):
    NONE = "none"
    VOICE_EXTRACTION = "voice_extraction"
    WEARABLE_NORMALIZATION = "wearable_normalization"
    MANUAL_FORM_NORMALIZATION = "manual_form_normalization"
    FOOD_IMPORT_NORMALIZATION = "food_import_normalization"
    CROSS_SOURCE_MERGE = "cross_source_merge"


class ConflictStatus(str, Enum):
    NONE = "none"
    SUPERSEDED = "superseded"
    COEXISTS_CONFLICTED = "coexists_conflicted"


class ArtifactModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    artifact_id: str = Field(min_length=1, pattern=r"^artifact_")
    user_id: str = Field(min_length=1)
    source_type: SourceType
    source_name: str = Field(min_length=1)
    source_record_id: Optional[str] = None
    collected_at: AwareDatetime
    ingested_at: AwareDatetime
    raw_location: str = Field(min_length=1)
    raw_format: RawFormat
    hash_or_version: Optional[str] = None
    transcript_ref: Optional[str] = None
    parser_version: Optional[str] = None
    notes: Optional[str] = None


class ProvenanceModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    artifact_id: str = Field(min_length=1, pattern=r"^artifact_")
    derivation_method: DerivationMethod
    supporting_refs: list[str] = Field(default_factory=list)
    parser_version: Optional[str] = None
    conflict_status: ConflictStatus


class InputEventModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    event_id: str = Field(min_length=1, pattern=r"^event_")
    user_id: str = Field(min_length=1)
    source_type: SourceType
    source_name: str = Field(min_length=1)
    source_record_id: Optional[str] = None
    capture_mode: CaptureMode
    domain: Domain
    metric_name: str = Field(min_length=1)
    value_type: ValueType
    value_number: Optional[float] = None
    value_string: Optional[str] = None
    value_boolean: Optional[bool] = None
    value_json: Optional[dict[str, Any]] = None
    unit: Optional[str] = None
    event_start_at: Optional[AwareDatetime]
    event_end_at: Optional[AwareDatetime]
    effective_date: date
    ingested_at: AwareDatetime
    confidence_label: ConfidenceLabel
    confidence_score: float = Field(ge=0.0, le=1.0)
    missingness_state: MissingnessState
    uncertainty_note: Optional[str] = None
    provenance: ProvenanceModel


class SubjectiveDailyEntryModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    entry_id: str = Field(min_length=1, pattern=r"^subjective_")
    user_id: str = Field(min_length=1)
    date: date
    source_name: Optional[str] = None
    source_record_id: Optional[str] = None
    provenance_record_id: Optional[str] = None
    conflict_status: ConflictStatus = ConflictStatus.NONE
    energy_self_rating: Optional[int] = Field(default=None, ge=1, le=5)
    stress_self_rating: Optional[int] = Field(default=None, ge=1, le=5)
    mood_self_rating: Optional[int] = Field(default=None, ge=1, le=5)
    perceived_sleep_quality: Optional[int] = Field(default=None, ge=1, le=5)
    illness_or_soreness_flag: Optional[bool] = None
    free_text_summary: str
    extraction_status: ExtractionStatus
    source_artifact_ids: list[str] = Field(min_length=1)
    confidence_label: ConfidenceLabel
    confidence_score: float = Field(ge=0.0, le=1.0)


class ManualLogEntryModel(BaseModel):
    model_config = ConfigDict(extra="allow")

    entry_id: str = Field(min_length=1, pattern=r"^manual_")
    user_id: str = Field(min_length=1)
    date: date
    log_type: ManualLogType
    payload: dict[str, Any]
    source_artifact_id: str = Field(min_length=1, pattern=r"^artifact_")
    completeness_state: CompletenessState
    confidence_label: ConfidenceLabel
    confidence_score: float = Field(ge=0.0, le=1.0)


class SharedInputBundleModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_artifacts: list[ArtifactModel]
    input_events: list[InputEventModel]
    subjective_daily_entries: list[SubjectiveDailyEntryModel]
    manual_log_entries: list[ManualLogEntryModel]


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    path: str


@dataclass(frozen=True)
class ValidationResult:
    bundle: Optional[SharedInputBundleModel]
    schema_issues: list[ValidationIssue]
    semantic_issues: list[ValidationIssue]

    @property
    def is_valid(self) -> bool:
        return not self.schema_issues and not self.semantic_issues


def shared_input_bundle_json_schema() -> dict[str, Any]:
    return SharedInputBundleModel.model_json_schema()


def validate_shared_input_bundle(payload: dict[str, Any]) -> ValidationResult:
    try:
        bundle = SharedInputBundleModel.model_validate(payload)
    except ValidationError as exc:
        return ValidationResult(
            bundle=None,
            schema_issues=[
                ValidationIssue(
                    code="schema_validation_error",
                    message=error["msg"],
                    path=_format_error_path(error["loc"]),
                )
                for error in exc.errors()
            ],
            semantic_issues=[],
        )

    semantic_issues = _semantic_issues(bundle)
    return ValidationResult(bundle=bundle, schema_issues=[], semantic_issues=semantic_issues)


def _semantic_issues(bundle: SharedInputBundleModel) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    artifacts_by_id = {artifact.artifact_id: artifact for artifact in bundle.source_artifacts}
    subjective_daily_keys: set[tuple[str, date]] = set()
    transcript_required_artifact_ids: set[str] = set()

    issues.extend(_detect_duplicate_primary_ids(bundle.source_artifacts, "artifact_id", "source_artifacts"))
    issues.extend(_detect_duplicate_primary_ids(bundle.input_events, "event_id", "input_events"))
    issues.extend(_detect_duplicate_primary_ids(bundle.subjective_daily_entries, "entry_id", "subjective_daily_entries"))
    issues.extend(_detect_duplicate_primary_ids(bundle.manual_log_entries, "entry_id", "manual_log_entries"))

    for index, event in enumerate(bundle.input_events):
        artifact = artifacts_by_id.get(event.provenance.artifact_id)
        if artifact is None:
            issues.append(_issue("missing_artifact_link", "Linked provenance artifact does not exist.", f"input_events[{index}].provenance.artifact_id"))
        else:
            if event.user_id != artifact.user_id:
                issues.append(_issue("user_id_mismatch", "Event user_id must match the linked artifact user_id.", f"input_events[{index}].user_id"))
            if event.source_type != artifact.source_type:
                issues.append(_issue("source_type_mismatch", "Event source_type must match the linked artifact source_type.", f"input_events[{index}].source_type"))
            if event.source_name != artifact.source_name:
                issues.append(_issue("source_name_mismatch", "Event source_name should match the linked artifact source_name.", f"input_events[{index}].source_name"))

        issues.extend(_validate_input_event_values(event, index))

        if event.capture_mode is CaptureMode.PASSIVE and event.source_type is not SourceType.WEARABLE:
            issues.append(_issue("passive_requires_wearable", "Passive capture_mode is only allowed for wearable source_type.", f"input_events[{index}].capture_mode"))
        if event.capture_mode is CaptureMode.DERIVED and event.provenance.derivation_method is DerivationMethod.NONE:
            issues.append(_issue("derived_requires_derivation_method", "Derived events must declare a non-none derivation_method.", f"input_events[{index}].provenance.derivation_method"))
        if event.capture_mode is CaptureMode.SELF_REPORTED and event.source_type not in {SourceType.VOICE_NOTE, SourceType.MANUAL}:
            issues.append(_issue("self_reported_source_type_invalid", "Self-reported events must come from voice_note or manual sources.", f"input_events[{index}].source_type"))
        if not _confidence_label_matches_score(event.confidence_label, event.confidence_score):
            issues.append(_issue("confidence_label_score_mismatch", "confidence_label must map to confidence_score using the frozen thresholds.", f"input_events[{index}].confidence_label"))
        if event.event_start_at is not None:
            local_date = event.event_start_at.date().isoformat()
            if local_date != event.effective_date.isoformat() and not _has_cross_midnight_note(event.uncertainty_note):
                issues.append(_issue("effective_date_mismatch", "effective_date must match the local date from event_start_at unless cross-midnight normalization is documented.", f"input_events[{index}].effective_date"))
        if event.source_type is SourceType.VOICE_NOTE or event.capture_mode is CaptureMode.DERIVED and event.provenance.derivation_method is DerivationMethod.VOICE_EXTRACTION:
            transcript_required_artifact_ids.add(event.provenance.artifact_id)
        if event.provenance.conflict_status is ConflictStatus.SUPERSEDED and artifact is None:
            issues.append(_issue("superseded_event_not_traceable", "Superseded events must still reference an existing artifact.", f"input_events[{index}].provenance.artifact_id"))
        issues.extend(_detect_semantic_override_fields(event, index, "input_events"))

    for index, entry in enumerate(bundle.subjective_daily_entries):
        key = (entry.user_id, entry.date)
        if key in subjective_daily_keys:
            issues.append(_issue("duplicate_subjective_daily_entry", "Only one subjective_daily_entry is allowed per user_id and date.", f"subjective_daily_entries[{index}].entry_id"))
        subjective_daily_keys.add(key)

        rating_values = (
            entry.energy_self_rating,
            entry.stress_self_rating,
            entry.mood_self_rating,
            entry.perceived_sleep_quality,
        )
        for artifact_id in entry.source_artifact_ids:
            artifact = artifacts_by_id.get(artifact_id)
            if artifact is None:
                issues.append(_issue("missing_artifact_link", "Subjective entry source_artifact_ids must reference existing artifacts.", f"subjective_daily_entries[{index}].source_artifact_ids"))
                continue
            if entry.user_id != artifact.user_id:
                issues.append(_issue("user_id_mismatch", "Subjective entry user_id must match the linked artifact user_id.", f"subjective_daily_entries[{index}].user_id"))
            if artifact.source_type not in {SourceType.VOICE_NOTE, SourceType.MANUAL}:
                issues.append(_issue("subjective_source_type_invalid", "Subjective entries may only cite voice_note or manual artifacts.", f"subjective_daily_entries[{index}].source_artifact_ids"))
            if artifact.source_type is SourceType.VOICE_NOTE:
                transcript_required_artifact_ids.add(artifact_id)

        if entry.extraction_status is ExtractionStatus.FAILED:
            if any(value is not None for value in rating_values):
                issues.append(_issue("failed_subjective_has_ratings", "Failed subjective extraction must leave all rating fields null.", f"subjective_daily_entries[{index}]"))
            if entry.confidence_label is ConfidenceLabel.HIGH:
                issues.append(_issue("failed_subjective_high_confidence", "Failed subjective extraction cannot carry high confidence.", f"subjective_daily_entries[{index}].confidence_label"))
        if not _confidence_label_matches_score(entry.confidence_label, entry.confidence_score):
            issues.append(_issue("confidence_label_score_mismatch", "confidence_label must map to confidence_score using the frozen thresholds.", f"subjective_daily_entries[{index}].confidence_label"))
        if entry.source_record_id is not None and not entry.source_record_id.startswith("subjective:"):
            issues.append(_issue("invalid_subjective_source_record_id", "subjective source_record_id must follow subjective:<source_artifact>:day:<date>.", f"subjective_daily_entries[{index}].source_record_id"))
        if entry.provenance_record_id is not None and entry.source_record_id is not None:
            expected_provenance_record_id = f"provenance:{entry.source_record_id}"
            if entry.provenance_record_id != expected_provenance_record_id:
                issues.append(_issue("subjective_provenance_mismatch", "subjective provenance_record_id must be derived from source_record_id.", f"subjective_daily_entries[{index}].provenance_record_id"))
        issues.extend(_detect_semantic_override_fields(entry, index, "subjective_daily_entries"))

    for index, entry in enumerate(bundle.manual_log_entries):
        artifact = artifacts_by_id.get(entry.source_artifact_id)
        if artifact is None:
            issues.append(_issue("missing_artifact_link", "Manual log entry source_artifact_id must reference an existing artifact.", f"manual_log_entries[{index}].source_artifact_id"))
        else:
            if entry.user_id != artifact.user_id:
                issues.append(_issue("user_id_mismatch", "Manual log entry user_id must match the linked artifact user_id.", f"manual_log_entries[{index}].user_id"))
            if artifact.source_type is not SourceType.MANUAL:
                issues.append(_issue("manual_entry_source_type_invalid", "Manual log entries must link to artifacts with source_type=manual.", f"manual_log_entries[{index}].source_artifact_id"))
        issues.extend(_validate_manual_payload(entry, index))
        if not _confidence_label_matches_score(entry.confidence_label, entry.confidence_score):
            issues.append(_issue("confidence_label_score_mismatch", "confidence_label must map to confidence_score using the frozen thresholds.", f"manual_log_entries[{index}].confidence_label"))
        issues.extend(_validate_manual_completeness(entry, index))
        issues.extend(_detect_semantic_override_fields(entry, index, "manual_log_entries"))

    for index, artifact in enumerate(bundle.source_artifacts):
        if artifact.artifact_id in transcript_required_artifact_ids and not artifact.transcript_ref:
            issues.append(_issue("missing_transcript_ref", "Voice note artifacts that back transcript-derived data must include transcript_ref.", f"source_artifacts[{index}].transcript_ref"))
        issues.extend(_detect_semantic_override_fields(artifact, index, "source_artifacts"))

    return issues


def _validate_input_event_values(event: InputEventModel, index: int) -> list[ValidationIssue]:
    populated = {
        "value_number": event.value_number is not None,
        "value_string": event.value_string is not None,
        "value_boolean": event.value_boolean is not None,
        "value_json": event.value_json is not None,
    }
    expected = {
        ValueType.NUMBER: "value_number",
        ValueType.STRING: "value_string",
        ValueType.ENUM: "value_string",
        ValueType.BOOLEAN: "value_boolean",
        ValueType.JSON: "value_json",
    }[event.value_type]
    issues: list[ValidationIssue] = []

    if event.missingness_state is not MissingnessState.PRESENT:
        if any(populated.values()):
            issues.append(_issue("missing_event_has_value", "Events with missingness_state != present must not populate value fields.", f"input_events[{index}]"))
        return issues

    if sum(1 for is_set in populated.values() if is_set) != 1 or not populated[expected]:
        issues.append(_issue("value_field_exclusivity_violation", "Exactly one value_* field must be populated according to value_type.", f"input_events[{index}]"))
    return issues


def _validate_manual_payload(entry: ManualLogEntryModel, index: int) -> list[ValidationIssue]:
    payload = entry.payload
    path = f"manual_log_entries[{index}].payload"
    issues: list[ValidationIssue] = []

    if entry.log_type is ManualLogType.GYM_SESSION:
        issues.extend(_validate_optional_datetime(payload, "session_start_at", path))
        issues.extend(_validate_optional_datetime(payload, "session_end_at", path))
        issues.extend(_validate_optional_string(payload, "session_label", path))
        if "exercise_names" in payload and not _is_string_list(payload["exercise_names"]):
            issues.append(_issue("invalid_manual_payload_shape", "gym_session.exercise_names must be an array of strings when present.", f"{path}.exercise_names"))
        issues.extend(_validate_optional_string(payload, "notes", path))
    elif entry.log_type is ManualLogType.EXERCISE_SET:
        if not _is_non_empty_string(payload.get("exercise_name")):
            issues.append(_issue("invalid_manual_payload_shape", "exercise_set payload requires exercise_name.", f"{path}.exercise_name"))
        set_index = payload.get("set_index")
        if not isinstance(set_index, int) or set_index < 1:
            issues.append(_issue("invalid_manual_payload_shape", "exercise_set payload requires set_index >= 1.", f"{path}.set_index"))
        if "reps" in payload and (not isinstance(payload["reps"], int) or payload["reps"] < 0):
            issues.append(_issue("invalid_manual_payload_shape", "exercise_set.reps must be an integer >= 0.", f"{path}.reps"))
        if "weight_kg" in payload and not _is_non_negative_number(payload["weight_kg"]):
            issues.append(_issue("invalid_manual_payload_shape", "exercise_set.weight_kg must be a number >= 0.", f"{path}.weight_kg"))
        if "rir" in payload and (not isinstance(payload["rir"], int) or not 0 <= payload["rir"] <= 5):
            issues.append(_issue("invalid_manual_payload_shape", "exercise_set.rir must be an integer between 0 and 5.", f"{path}.rir"))
        issues.extend(_validate_optional_string(payload, "notes", path))
    elif entry.log_type is ManualLogType.MEAL:
        issues.extend(_validate_optional_string(payload, "meal_label", path))
        if "items" in payload and not _is_string_list(payload["items"]):
            issues.append(_issue("invalid_manual_payload_shape", "meal.items must be an array of strings when present.", f"{path}.items"))
        if "estimated" in payload and not isinstance(payload["estimated"], bool):
            issues.append(_issue("invalid_manual_payload_shape", "meal.estimated must be a boolean when present.", f"{path}.estimated"))
        issues.extend(_validate_optional_string(payload, "notes", path))
    elif entry.log_type is ManualLogType.HYDRATION:
        amount_ml = payload.get("amount_ml")
        if not _is_positive_number(amount_ml):
            issues.append(_issue("invalid_manual_payload_shape", "hydration.amount_ml must be a number > 0.", f"{path}.amount_ml"))
        issues.extend(_validate_optional_string(payload, "beverage_type", path))
        issues.extend(_validate_optional_string(payload, "notes", path))
    elif entry.log_type is ManualLogType.BODY_SIGNAL:
        if not _is_non_empty_string(payload.get("signal_type")):
            issues.append(_issue("invalid_manual_payload_shape", "body_signal payload requires signal_type.", f"{path}.signal_type"))
        if "severity" in payload and (not isinstance(payload["severity"], int) or not 1 <= payload["severity"] <= 5):
            issues.append(_issue("invalid_manual_payload_shape", "body_signal.severity must be an integer between 1 and 5.", f"{path}.severity"))
        issues.extend(_validate_optional_string(payload, "notes", path))
    elif entry.log_type is ManualLogType.CONTEXT_NOTE:
        issues.extend(_validate_optional_string(payload, "label", path))
        if not _is_non_empty_string(payload.get("notes")):
            issues.append(_issue("invalid_manual_payload_shape", "context_note payload requires a non-empty notes field.", f"{path}.notes"))

    return issues


def _validate_manual_completeness(entry: ManualLogEntryModel, index: int) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    path = f"manual_log_entries[{index}]"

    if entry.log_type is ManualLogType.EXERCISE_SET and entry.completeness_state is CompletenessState.COMPLETE:
        if "reps" not in entry.payload:
            issues.append(
                _issue(
                    "manual_completeness_mismatch",
                    "exercise_set entries marked complete must include reps so completeness remains explicit and honest.",
                    f"{path}.completeness_state",
                )
            )
    if entry.log_type is ManualLogType.MEAL and entry.completeness_state is CompletenessState.COMPLETE:
        if "notes" not in entry.payload and "items" not in entry.payload:
            issues.append(
                _issue(
                    "manual_completeness_mismatch",
                    "meal entries marked complete must include notes or items so nutrition capture stays explicit and honest.",
                    f"{path}.completeness_state",
                )
            )

    return issues


def _validate_optional_datetime(payload: dict[str, Any], field_name: str, path: str) -> list[ValidationIssue]:
    if field_name not in payload or payload[field_name] is None:
        return []
    try:
        _parse_datetime(payload[field_name])
    except ValueError:
        return [_issue("invalid_manual_payload_shape", f"{field_name} must be an ISO 8601 datetime when present.", f"{path}.{field_name}")]
    return []


def _validate_optional_string(payload: dict[str, Any], field_name: str, path: str) -> list[ValidationIssue]:
    if field_name not in payload or payload[field_name] is None:
        return []
    if not _is_non_empty_string(payload[field_name]):
        return [_issue("invalid_manual_payload_shape", f"{field_name} must be a non-empty string when present.", f"{path}.{field_name}")]
    return []


def _detect_duplicate_primary_ids(models: list[BaseModel], field_name: str, family: str) -> list[ValidationIssue]:
    seen: dict[str, int] = {}
    issues: list[ValidationIssue] = []
    for index, model in enumerate(models):
        value = getattr(model, field_name)
        if value in seen:
            issues.append(
                _issue(
                    "duplicate_primary_id",
                    f"{family} IDs must be unique within their object family.",
                    f"{family}[{index}].{field_name}",
                )
            )
            continue
        seen[value] = index
    return issues


def _detect_semantic_override_fields(model: BaseModel, index: int, family: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    allowed_fields = set(model.__class__.model_fields.keys())
    extra_keys = set(model.model_extra or {})
    forbidden_prefixes = (
        "missingness_",
        "confidence_",
        "timestamp_",
        "event_start_",
        "event_end_",
        "effective_date_",
        "ingested_at_",
        "collected_at_",
    )
    for key in extra_keys:
        if key in allowed_fields:
            continue
        if key.startswith(forbidden_prefixes):
            issues.append(_issue("semantic_override_field_present", "Canonical objects may not add fields that redefine missingness, confidence, or timestamp semantics.", f"{family}[{index}].{key}"))
    return issues


def _format_error_path(loc: tuple[Any, ...]) -> str:
    path = []
    for part in loc:
        if isinstance(part, int):
            path[-1] = f"{path[-1]}[{part}]"
        else:
            path.append(str(part))
    return ".".join(path)


def _issue(code: str, message: str, path: str) -> ValidationIssue:
    return ValidationIssue(code=code, message=message, path=path)


def _confidence_label_matches_score(label: ConfidenceLabel, score: float) -> bool:
    if score >= 0.8:
        return label is ConfidenceLabel.HIGH
    if score >= 0.5:
        return label is ConfidenceLabel.MEDIUM
    return label is ConfidenceLabel.LOW


def _has_cross_midnight_note(note: Optional[str]) -> bool:
    if not note:
        return False
    lowered = note.lower()
    return "cross-midnight" in lowered and "normalization" in lowered


def _parse_datetime(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("datetime must be a string")
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("datetime must include timezone information")
    return parsed


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _is_non_negative_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0
