"""P2 — Female marathoner (32yo, performance-focused, endurance-only)."""

from __future__ import annotations

from .base import (
    NutritionDay,
    PersonaSpec,
    RunSession,
    established_expected_actions,
    established_forbidden_actions,
)


SPEC = PersonaSpec(
    persona_id="p2_female_marathoner",
    label="Female marathoner",
    description=(
        "32-year-old female, 62kg / 170cm, active. 5 endurance runs per "
        "week, marathon-prep cycle. Performance priority. 90-day history "
        "from full Garmin Connect. Stresses: female protein/HRV deltas, "
        "endurance-only domain, no strength confound."
    ),
    age=32,
    sex_at_birth="female",
    weight_kg=62.0,
    height_cm=170,
    activity_level="active",
    primary_goal="performance",
    goal_description="Marathon performance — sub-3:30 target",
    data_source="garmin",
    history_days=90,
    weekly_strength_count=0,
    weekly_running_count=5,
    typical_strength_split=[],
    sleep_window_target=("22:30", "06:30"),
    daily_kcal_target=2400,
    daily_protein_target_g=110,
    typical_run_distance_m=10000.0,
    typical_run_duration_s=3300,
    typical_run_avg_hr=152,
    typical_hrv_ms=68.0,
    typical_resting_hr=52,
    typical_sleep_hours=7.5,
    typical_sleep_score=82,
    today_planned_session="long",
    today_soreness="moderate",
    today_energy="moderate",
    today_stress_score=2,
    # W-AK / F-IR-03 inline declaration. Endurance-only profile;
    # no scenario-specific override — the established defaults apply.
    expected_actions=established_expected_actions(),
    forbidden_actions=established_forbidden_actions(),
    recorded_run_history=[
        RunSession(
            date_offset_days=1,
            distance_m=12000.0,
            duration_s=4080,
            avg_hr=155,
        ),
        RunSession(
            date_offset_days=3,
            distance_m=8000.0,
            duration_s=2760,
            avg_hr=148,
        ),
        RunSession(
            date_offset_days=5,
            distance_m=15000.0,
            duration_s=5100,
            avg_hr=150,
        ),
    ],
    recorded_nutrition_history=[
        NutritionDay(
            date_offset_days=0,
            calories=2350.0,
            protein_g=105.0,
            carbs_g=320.0,
            fat_g=75.0,
        ),
    ],
)
