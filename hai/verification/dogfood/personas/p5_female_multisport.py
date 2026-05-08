"""P5 — Female multi-sport (35yo, triathlon + S&C, mixed sources)."""

from __future__ import annotations

from .base import (
    CrossSession,
    NutritionDay,
    PersonaSpec,
    RunSession,
    StrengthSession,
    established_expected_actions,
    established_forbidden_actions,
)


SPEC = PersonaSpec(
    persona_id="p5_female_multisport",
    label="Female multi-sport",
    description=(
        "35-year-old female, 64kg / 168cm, very active. Triathlon training "
        "(swim + bike + run) plus 2 S&C sessions per week. Performance "
        "priority. Mixed data sources — Garmin for run/bike + manual for "
        "swim. 6 months of history. Stresses: cross-train coverage, "
        "mixed-source data reconciliation, female competitive athlete."
    ),
    age=35,
    sex_at_birth="female",
    weight_kg=64.0,
    height_cm=168,
    activity_level="very_active",
    primary_goal="performance",
    goal_description="Olympic-distance triathlon performance",
    data_source="mixed",
    history_days=180,
    weekly_strength_count=2,
    weekly_running_count=3,
    typical_strength_split=["strength_lower", "strength_upper"],
    sleep_window_target=("22:00", "06:00"),
    daily_kcal_target=2600,
    daily_protein_target_g=130,
    typical_strength_volume_kg=3500.0,
    typical_run_distance_m=8000.0,
    typical_run_duration_s=2700,
    typical_run_avg_hr=148,
    typical_hrv_ms=60.0,
    typical_resting_hr=50,
    typical_sleep_hours=7.5,
    typical_sleep_score=82,
    cross_sessions_per_week=4,
    cross_kind="cycling",
    today_planned_session="cross_train",
    today_soreness="low",
    today_energy="high",
    today_stress_score=2,
    # W-AK / F-IR-03 inline declaration. Multi-sport with
    # cross-domain coverage; defaults apply.
    expected_actions=established_expected_actions(),
    forbidden_actions=established_forbidden_actions(),
    recorded_run_history=[
        RunSession(
            date_offset_days=2,
            distance_m=10000.0,
            duration_s=3300,
            avg_hr=150,
        ),
    ],
    recorded_strength_history=[
        StrengthSession(
            date_offset_days=4,
            session_type="strength_lower",
            total_volume_kg=4000.0,
        ),
    ],
    recorded_cross_history=[
        CrossSession(
            date_offset_days=1,
            kind="cycling",
            duration_s=5400,
            avg_hr=140,
        ),
        CrossSession(
            date_offset_days=3,
            kind="swimming",
            duration_s=2700,
            avg_hr=130,
        ),
    ],
    recorded_nutrition_history=[
        NutritionDay(
            date_offset_days=0,
            calories=2580.0,
            protein_g=132.0,
            carbs_g=320.0,
            fat_g=80.0,
        ),
    ],
)
