"""P3 — Older recreational male runner (48yo)."""

from __future__ import annotations

from .base import (
    NutritionDay,
    PersonaSpec,
    RunSession,
    established_expected_actions,
    established_forbidden_actions,
)


SPEC = PersonaSpec(
    persona_id="p3_older_recreational",
    label="Older recreational",
    description=(
        "48-year-old male, 78kg / 178cm, moderate activity. 3-4 runs per "
        "week, recreational. Fat loss + general fitness goal. 12 months "
        "of intervals.icu history. Stresses: age threshold edge "
        "(Mifflin-St Jeor still valid 18-65), well-established history, "
        "lower training load than younger personas."
    ),
    age=48,
    sex_at_birth="male",
    weight_kg=78.0,
    height_cm=178,
    activity_level="moderate",
    primary_goal="fat_loss",
    goal_description="Recreational fitness; fat loss with general health priority",
    data_source="intervals_icu",
    history_days=365,
    weekly_strength_count=0,
    weekly_running_count=3,
    typical_strength_split=[],
    sleep_window_target=("22:00", "06:30"),
    daily_kcal_target=2300,
    daily_protein_target_g=120,
    typical_run_distance_m=6500.0,
    typical_run_duration_s=2500,
    typical_run_avg_hr=140,
    typical_hrv_ms=45.0,
    typical_resting_hr=58,
    typical_sleep_hours=7.0,
    typical_sleep_score=78,
    today_planned_session="easy_z2",
    today_soreness="low",
    today_energy="moderate",
    today_stress_score=2,
    # W-AK / F-IR-03 inline declaration. Established with year of
    # history; no scenario-specific override beyond the defaults.
    expected_actions=established_expected_actions(),
    forbidden_actions=established_forbidden_actions(),
    recorded_run_history=[
        RunSession(
            date_offset_days=2,
            distance_m=6000.0,
            duration_s=2400,
            avg_hr=141,
        ),
        RunSession(
            date_offset_days=5,
            distance_m=8000.0,
            duration_s=3300,
            avg_hr=138,
        ),
    ],
    recorded_nutrition_history=[
        NutritionDay(
            date_offset_days=0,
            calories=2100.0,
            protein_g=115.0,
            carbs_g=220.0,
            fat_g=75.0,
        ),
    ],
)
