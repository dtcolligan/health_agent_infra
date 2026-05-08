"""P7 — High-volume hybrid male (41yo, 18mo Garmin history, ultra-prep)."""

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
    persona_id="p7_high_volume_hybrid",
    label="High-volume hybrid",
    description=(
        "41-year-old male, 70kg / 178cm, very active. 6 endurance sessions "
        "+ 2 strength per week — peak ultra-marathon training cycle. "
        "Performance priority. Full Garmin Connect history, 18 months. "
        "Stresses: training-load ceiling, ACWR extremes, established "
        "athlete with deep history, classifier behaviour at the high end."
    ),
    age=41,
    sex_at_birth="male",
    weight_kg=70.0,
    height_cm=178,
    activity_level="very_active",
    primary_goal="performance",
    goal_description="50-mile ultra peak — high-volume base + speed",
    data_source="garmin",
    history_days=540,
    weekly_strength_count=2,
    weekly_running_count=6,
    typical_strength_split=["strength_lower", "strength_upper"],
    sleep_window_target=("21:30", "05:30"),
    daily_kcal_target=3400,
    daily_protein_target_g=130,
    typical_strength_volume_kg=2800.0,
    typical_run_distance_m=14000.0,
    typical_run_duration_s=4500,
    typical_run_avg_hr=145,
    typical_hrv_ms=72.0,
    typical_resting_hr=42,
    typical_sleep_hours=7.0,
    typical_sleep_score=80,
    today_planned_session="long",
    today_soreness="moderate",
    today_energy="moderate",
    today_stress_score=2,
    # W-AK / F-IR-03 inline declaration. High-volume hybrid stresses
    # ACWR extremes; downgrade actions are expected, but the
    # established defaults already cover those.
    expected_actions=established_expected_actions(),
    forbidden_actions=established_forbidden_actions(),
    recorded_run_history=[
        RunSession(
            date_offset_days=1,
            distance_m=15000.0,
            duration_s=4800,
            avg_hr=148,
        ),
        RunSession(
            date_offset_days=2,
            distance_m=8000.0,
            duration_s=2640,
            avg_hr=140,
        ),
        RunSession(
            date_offset_days=4,
            distance_m=20000.0,
            duration_s=6600,
            avg_hr=142,
        ),
    ],
    recorded_strength_history=[
        StrengthSession(
            date_offset_days=3,
            session_type="strength_lower",
            total_volume_kg=3000.0,
        ),
    ],
    recorded_nutrition_history=[
        NutritionDay(
            date_offset_days=0,
            calories=3450.0,
            protein_g=132.0,
            carbs_g=480.0,
            fat_g=95.0,
        ),
    ],
)
