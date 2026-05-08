"""P4 — Strength-only male cutter (28yo, manual-only logging)."""

from __future__ import annotations

from .base import (
    NutritionDay,
    PersonaSpec,
    StrengthSession,
    established_expected_actions,
    established_forbidden_actions,
)


SPEC = PersonaSpec(
    persona_id="p4_strength_only_cutter",
    label="Strength-only cutter",
    description=(
        "28-year-old male, 95kg / 180cm (BMI ~29.3), very active. 4 strength "
        "sessions per week, no running. Fat loss priority, deliberate "
        "deficit. Manual-only logging — no wearable data. 60-day history. "
        "Stresses: high BMI, no wearable signals, no running domain pulls, "
        "manual-only intake reliability."
    ),
    age=28,
    sex_at_birth="male",
    weight_kg=95.0,
    height_cm=180,
    activity_level="very_active",
    primary_goal="fat_loss",
    goal_description="Fat loss while maintaining strength on a 4-day split",
    data_source="manual_only",
    history_days=60,
    weekly_strength_count=4,
    weekly_running_count=0,
    typical_strength_split=[
        "strength_upper",
        "strength_lower",
        "strength_push",
        "strength_back_biceps",
    ],
    sleep_window_target=("23:00", "07:00"),
    daily_kcal_target=2700,
    daily_protein_target_g=200,
    typical_strength_volume_kg=8000.0,
    typical_hrv_ms=50.0,
    typical_resting_hr=60,
    typical_sleep_hours=7.0,
    typical_sleep_score=72,
    today_planned_session="strength_upper",
    today_soreness="moderate",
    today_energy="moderate",
    today_stress_score=3,
    # W-AK / F-IR-03 inline declaration. Manual-only logging +
    # high-volume strength; defaults apply.
    expected_actions=established_expected_actions(),
    forbidden_actions=established_forbidden_actions(),
    recorded_strength_history=[
        StrengthSession(
            date_offset_days=1,
            session_type="strength_lower",
            total_volume_kg=9500.0,
        ),
        StrengthSession(
            date_offset_days=3,
            session_type="strength_push",
            total_volume_kg=6800.0,
        ),
        StrengthSession(
            date_offset_days=5,
            session_type="strength_upper",
            total_volume_kg=7400.0,
        ),
    ],
    recorded_nutrition_history=[
        NutritionDay(
            date_offset_days=0,
            calories=2680.0,
            protein_g=205.0,
            carbs_g=260.0,
            fat_g=78.0,
        ),
    ],
)
