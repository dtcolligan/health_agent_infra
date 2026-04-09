from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SleepDaily:
    date: str
    source: str | None = None
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
    date: str
    source: str | None = None
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
    session_id: str
    date: str
    session_type: str
    source: str
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
    set_id: str
    session_id: str
    date: str
    exercise_name: str
    exercise_group: str | None = None
    set_number: int | None = None
    reps: int | None = None
    weight_kg: float | None = None
    rir: float | None = None
    rpe: float | None = None
    completed_bool: bool | None = None
    note: str | None = None


@dataclass
class NutritionDaily:
    date: str
    calories_kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    meal_count: int | None = None
    food_log_completeness: str | None = None
    top_meals_summary: str | None = None
    source: str | None = None


@dataclass
class DailyHealthSnapshot:
    date: str
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
    gym_exercise_sets: list[dict[str, Any]] = field(default_factory=list)
    nutrition_daily: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
