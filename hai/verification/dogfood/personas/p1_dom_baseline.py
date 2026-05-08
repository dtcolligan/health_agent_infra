"""P1 — Dom-baseline (control)."""

from __future__ import annotations

from .base import (
    NutritionDay,
    PersonaSpec,
    RunSession,
    StrengthSession,
    established_expected_actions,
    established_forbidden_actions,
)


SPEC = PersonaSpec(
    persona_id="p1_dom_baseline",
    label="Dom-baseline (control)",
    description=(
        "19-year-old male, 84kg / 185cm, very active. 3 strength + 3 running "
        "per week, alternating. Performance + recomp priority. 14-day "
        "onboarding window, intervals.icu source. Reproduces known B1-B7 "
        "findings. Lowest expected new-bug yield; highest regression value."
    ),
    age=19,
    sex_at_birth="male",
    weight_kg=84.0,
    height_cm=185,
    activity_level="very_active",
    primary_goal="performance",
    goal_description="Improve performance (priority); secondary: muscle gain + fat loss",
    data_source="intervals_icu",
    history_days=14,
    weekly_strength_count=3,
    weekly_running_count=3,
    typical_strength_split=["strength_upper", "strength_lower", "strength_sbd"],
    sleep_window_target=("22:00", "07:00"),
    daily_kcal_target=3300,
    daily_protein_target_g=160,
    typical_strength_volume_kg=4500.0,
    typical_run_distance_m=7500.0,
    typical_run_duration_s=2800,
    typical_run_avg_hr=148,
    typical_hrv_ms=85.0,
    typical_resting_hr=48,
    typical_sleep_hours=8.0,
    typical_sleep_score=85,
    today_planned_session="strength_upper",
    today_soreness="low",
    today_energy="high",
    today_stress_score=1,
    # W-AK / F-IR-03 inline declaration. P1 is the baseline control
    # — established profile, no scenario-specific overrides — so the
    # default established whitelist + forbidden set apply directly.
    expected_actions=established_expected_actions(),
    forbidden_actions=established_forbidden_actions(),
    recorded_strength_history=[
        StrengthSession(
            date_offset_days=4,
            session_type="strength_upper",
            total_volume_kg=4200.0,
        ),
    ],
    recorded_run_history=[
        RunSession(
            date_offset_days=4,
            distance_m=6746.0,
            duration_s=2400,
            avg_hr=155,
        ),
    ],
    recorded_nutrition_history=[
        NutritionDay(
            date_offset_days=0,
            calories=3266.0,
            protein_g=176.0,
            carbs_g=334.0,
            fat_g=136.0,
        ),
    ],
)
