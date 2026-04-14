from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SourceRecord:
    artifact_family: str = "source_record"
    source_record_id: str = ""
    source_name: str = ""
    source_type: str = ""
    entry_lane: str = ""
    raw_location: str = ""
    raw_format: str = ""
    effective_date: str | None = None
    collected_at: str | None = None
    ingested_at: str | None = None
    hash_or_version: str | None = None
    native_record_type: str | None = None
    native_record_id: str | None = None


@dataclass
class ProvenanceRecord:
    artifact_family: str = "provenance_record"
    provenance_record_id: str = ""
    source_record_id: str = ""
    derivation_method: str = ""
    supporting_refs: list[str] = field(default_factory=list)
    parser_version: str | None = None
    conflict_status: str = "none"


@dataclass
class SleepDaily:
    artifact_family: str = "sleep_daily"
    date: str = ""
    source: str | None = None
    sleep_daily_id: str | None = None
    source_name: str | None = None
    source_record_id: str | None = None
    provenance_record_id: str | None = None
    conflict_status: str = "none"
    total_sleep_sec: float | None = None
    deep_sleep_sec: float | None = None
    light_sleep_sec: float | None = None
    rem_sleep_sec: float | None = None
    awake_sleep_sec: float | None = None
    sleep_score: float | None = None
    avg_sleep_respiration: float | None = None
    awake_count: int | None = None
    restless_moments: int | None = None


@dataclass
class ReadinessDaily:
    artifact_family: str = "readiness_daily"
    date: str = ""
    source: str | None = None
    readiness_daily_id: str | None = None
    source_name: str | None = None
    source_record_id: str | None = None
    provenance_record_id: str | None = None
    conflict_status: str = "none"
    readiness_score: float | None = None
    readiness_label: str | None = None
    sleep_factor: float | None = None
    hrv_factor: float | None = None
    stress_factor: float | None = None
    training_load_factor: float | None = None
    recovery_hours_remaining: float | None = None
    data_backed_observation: str | None = None
    generic_guidance: str | None = None
    caveat: str | None = None


@dataclass
class TrainingSession:
    artifact_family: str = "training_session"
    session_id: str = ""
    date: str = ""
    session_type: str = ""
    source: str = ""
    training_session_id: str | None = None
    source_name: str | None = None
    source_record_id: str | None = None
    provenance_record_id: str | None = None
    confidence_label: str | None = None
    conflict_status: str = "none"
    start_time_local: str | None = None
    duration_sec: float | None = None
    session_title: str | None = None
    rpe_1_10: float | None = None
    energy_pre_1_5: float | None = None
    energy_post_1_5: float | None = None
    notes: str | None = None
    distance_m: float | None = None
    avg_hr: float | None = None
    max_hr: float | None = None
    avg_pace_sec_per_km: float | None = None
    elevation_gain_m: float | None = None
    training_effect_aerobic: float | None = None
    lift_focus: str | None = None
    exercise_count: int | None = None
    total_sets: int | None = None
    total_reps: int | None = None
    total_load_kg: float | None = None


@dataclass
class GymExerciseSet:
    # Legacy compatibility-only set surface retained for downstream replay stability.
    # Canonical set-level truth is GymSetRecord / `gym_set_record`.
    artifact_family: str = "gym_exercise_set"
    set_id: str = ""
    session_id: str = ""
    training_session_id: str | None = None
    gym_exercise_set_id: str | None = None
    date: str = ""
    exercise_name: str = ""
    source_name: str | None = None
    source_record_id: str | None = None
    provenance_record_id: str | None = None
    confidence_label: str | None = None
    conflict_status: str = "none"
    compatibility_status: str = "legacy_compatibility_only"
    canonical_artifact_family: str = "gym_set_record"
    exercise_group: str | None = None
    set_number: int | None = None
    reps: int | None = None
    weight_kg: float | None = None
    rir: float | None = None
    rpe: float | None = None
    completed_bool: bool | None = None
    note: str | None = None


@dataclass
class ExerciseCatalog:
    artifact_family: str = "exercise_catalog"
    exercise_catalog_id: str | None = None
    canonical_exercise_name: str = ""
    movement_pattern: str | None = None
    source_name: str | None = None
    source_record_id: str | None = None
    provenance_record_id: str | None = None
    conflict_status: str = "none"
    equipment: list[str] | None = None
    primary_muscle_groups: list[str] | None = None
    secondary_muscle_groups: list[str] | None = None
    unilateral_bool: bool | None = None
    loaded_pattern: str | None = None


@dataclass
class ExerciseAlias:
    artifact_family: str = "exercise_alias"
    exercise_alias_id: str | None = None
    exercise_catalog_id: str | None = None
    alias_name: str = ""
    source_name: str | None = None
    source_record_id: str | None = None
    provenance_record_id: str | None = None
    conflict_status: str = "none"
    source_native_exercise_id: str | None = None
    normalization_rule: str | None = None
    notes: str | None = None


@dataclass
class GymSetRecord:
    artifact_family: str = "gym_set_record"
    gym_set_record_id: str | None = None
    training_session_id: str | None = None
    date: str = ""
    exercise_catalog_id: str | None = None
    source_name: str | None = None
    source_record_id: str | None = None
    provenance_record_id: str | None = None
    conflict_status: str = "none"
    exercise_alias_id: str | None = None
    set_number: int | None = None
    reps: int | None = None
    weight_kg: float | None = None
    rir: float | None = None
    rpe: float | None = None
    completed_bool: bool | None = None
    set_type: str | None = None
    note: str | None = None


@dataclass
class NutritionDaily:
    artifact_family: str = "nutrition_daily"
    date: str = ""
    nutrition_daily_id: str | None = None
    source_name: str | None = None
    source_record_id: str | None = None
    provenance_record_id: str | None = None
    conflict_status: str = "none"
    calories_kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    meal_count: int | None = None
    food_log_completeness: str | None = None
    top_meals_summary: str | None = None


@dataclass
class DailyHealthSnapshot:
    artifact_family: str = "daily_health_snapshot"
    date: str = ""
    daily_health_snapshot_id: str | None = None
    provenance_record_id: str | None = None
    conflict_status: str = "none"
    sleep_duration_hours: float | None = None
    sleep_score: float | None = None
    sleep_awake_count: int | None = None
    resting_hr: float | None = None
    hrv_status: str | None = None
    body_battery_or_readiness: float | None = None
    readiness_label: str | None = None
    running_sessions_count: int | None = None
    running_volume_m: float | None = None
    gym_sessions_count: int | None = None
    gym_total_sets: int | None = None
    gym_total_reps: int | None = None
    gym_total_load_kg: float | None = None
    food_logged_bool: bool | None = None
    calories_kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    hydration_ml: float | None = None
    subjective_energy_1_5: float | None = None
    subjective_soreness_1_5: float | None = None
    subjective_stress_1_5: float | None = None
    overall_day_note: str | None = None
    data_backed_fields: list[str] = field(default_factory=list)
    generic_fields: list[str] = field(default_factory=list)
    source_flags: dict[str, bool] = field(default_factory=dict)
    sleep_daily: dict[str, Any] | None = None
    readiness_daily: dict[str, Any] | None = None
    running_sessions: list[dict[str, Any]] = field(default_factory=list)
    gym_sessions: list[dict[str, Any]] = field(default_factory=list)
    gym_set_records: list[dict[str, Any]] = field(default_factory=list)
    legacy_compatibility_aliases: dict[str, str] = field(default_factory=dict)
    gym_exercise_sets: list[dict[str, Any]] = field(default_factory=list)
    subjective_daily: dict[str, Any] | None = None
    nutrition_daily: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
