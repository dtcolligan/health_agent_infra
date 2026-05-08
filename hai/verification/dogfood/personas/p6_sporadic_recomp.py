"""P6 — Sporadic male recomp (26yo, inconsistent logging, 4mo with gaps)."""

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
    persona_id="p6_sporadic_recomp",
    label="Sporadic recomp",
    description=(
        "26-year-old male, 72kg / 175cm, active. 2-3 inconsistent sessions "
        "per week (mix of strength and running). Recomp priority. 4 months "
        "of history with vacation + minor illness gaps. Stresses: sporadic "
        "logging behaviour, gap handling, missing-data robustness, "
        "classifier behaviour when history is uneven."
    ),
    age=26,
    sex_at_birth="male",
    weight_kg=72.0,
    height_cm=175,
    activity_level="moderate",
    primary_goal="recomp",
    goal_description="Recomp — slowly losing fat while keeping or gaining muscle",
    data_source="mixed",
    history_days=120,
    weekly_strength_count=2,
    weekly_running_count=2,
    typical_strength_split=["strength_upper", "strength_lower"],
    sleep_window_target=("23:30", "07:30"),
    daily_kcal_target=2500,
    daily_protein_target_g=140,
    typical_strength_volume_kg=4000.0,
    typical_run_distance_m=5500.0,
    typical_run_duration_s=2100,
    typical_run_avg_hr=152,
    typical_hrv_ms=58.0,
    typical_resting_hr=56,
    typical_sleep_hours=7.0,
    typical_sleep_score=75,
    sporadic_logging=True,
    history_gap_days=(20, 21, 22, 23, 24, 25, 26, 70, 71, 72),
    today_planned_session="strength_upper",
    today_soreness="low",
    today_energy="moderate",
    today_stress_score=3,
    # W-AK / F-IR-03 inline declaration. Sporadic logging stresses
    # missing-data robustness in the classifier, but the *expected*
    # action set is unchanged from defaults — the persona's gap
    # behaviour should produce defer or maintain, both already in
    # the established whitelist.
    expected_actions=established_expected_actions(),
    forbidden_actions=established_forbidden_actions(),
    recorded_strength_history=[
        StrengthSession(
            date_offset_days=3,
            session_type="strength_lower",
            total_volume_kg=4200.0,
        ),
    ],
    recorded_run_history=[
        RunSession(
            date_offset_days=6,
            distance_m=5000.0,
            duration_s=1980,
            avg_hr=148,
        ),
    ],
    recorded_nutrition_history=[
        NutritionDay(
            date_offset_days=0,
            calories=2480.0,
            protein_g=138.0,
            carbs_g=260.0,
            fat_g=82.0,
        ),
    ],
)
