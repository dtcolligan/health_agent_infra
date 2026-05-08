"""P9 — Older female endurance (W-O, v0.1.11).

Fills a gap the v0.1.10 8-persona matrix didn't cover: female,
age-50+, endurance-primary. Stresses the recovery + running domains
with longer recovery times and lower typical HRV; tests whether
the band thresholds calibrate sensibly across the older-athlete
shape.
"""

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
    persona_id="p9_older_female_endurance",
    label="Older female endurance",
    description=(
        "52-year-old female, 60kg / 165cm, very-active masters runner. "
        "Targets 5x/week running, 1x light strength, no high-intensity "
        "lifting. 14-day onboarding window, intervals.icu source. "
        "Stresses age-adjusted band calibration (lower typical HRV, "
        "higher RHR, longer recovery windows)."
    ),
    age=52,
    sex_at_birth="female",
    weight_kg=60.0,
    height_cm=165,
    activity_level="very_active",
    primary_goal="performance",
    goal_description="Masters marathon performance; injury-free training",
    data_source="intervals_icu",
    history_days=14,
    weekly_strength_count=1,
    weekly_running_count=5,
    typical_strength_split=["strength_full_body"],
    sleep_window_target=("22:30", "06:30"),
    daily_kcal_target=2200,
    daily_protein_target_g=85,
    typical_strength_volume_kg=2200.0,
    typical_run_distance_m=10000.0,
    typical_run_duration_s=3600,
    typical_run_avg_hr=140,
    # Age-adjusted: lower HRV centroid, higher RHR centroid.
    typical_hrv_ms=52.0,
    typical_resting_hr=58,
    typical_sleep_hours=7.2,
    typical_sleep_score=78,
    today_planned_session="easy",
    today_soreness="low",
    today_energy="moderate",
    today_stress_score=2,
    # W-AK / F-IR-03 inline declaration. Older female endurance —
    # downgrade actions are common (longer recovery times, lower
    # HRV baseline), but defaults already cover them.
    expected_actions=established_expected_actions(),
    forbidden_actions=established_forbidden_actions(),
    recorded_strength_history=[
        StrengthSession(
            date_offset_days=6,
            session_type="strength_full_body",
            total_volume_kg=2100.0,
            rpe_avg=6.0,
        ),
    ],
    recorded_run_history=[
        RunSession(
            date_offset_days=1,
            distance_m=8500.0,
            duration_s=3000,
            avg_hr=138,
        ),
        RunSession(
            date_offset_days=3,
            distance_m=12000.0,
            duration_s=4400,
            avg_hr=142,
        ),
        RunSession(
            date_offset_days=5,
            distance_m=6500.0,
            duration_s=2400,
            avg_hr=135,
        ),
    ],
    recorded_nutrition_history=[
        NutritionDay(
            date_offset_days=0,
            calories=2180.0,
            protein_g=88.0,
            carbs_g=275.0,
            fat_g=78.0,
        ),
    ],
)
