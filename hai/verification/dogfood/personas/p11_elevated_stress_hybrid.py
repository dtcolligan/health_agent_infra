"""P11 — Elevated-stress hybrid (W-O, v0.1.11).

Per Codex F-C-06: the v0.1.10 8-persona matrix was uniformly
low-stress (all reported stress_score 1-2). Stress-domain
classification logic was therefore under-tested. P11 reports
sustained elevated subjective stress AND low body-battery from
the wearable, so the stress classifier's elevated band fires
and the recommendation surface should propose
schedule_decompression_time (or equivalent) rather than
maintain_routine.
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
    persona_id="p11_elevated_stress_hybrid",
    label="Elevated-stress hybrid",
    description=(
        "28-year-old male, 78kg / 178cm, hybrid trainer (3x strength + "
        "2x running). Persistent elevated subjective stress (4-5/5 "
        "self-reports across the last 7 days) with low body-battery "
        "(<30) and high all-day-stress (50+) from Garmin. Stresses "
        "the stress domain's elevated-band path that the v0.1.10 "
        "matrix never exercised."
    ),
    age=28,
    sex_at_birth="male",
    weight_kg=78.0,
    height_cm=178,
    activity_level="active",
    primary_goal="performance",
    goal_description="Maintain training under work-stress; consider deload",
    # Garmin source so body_battery + all_day_stress populate.
    data_source="garmin",
    history_days=14,
    weekly_strength_count=3,
    weekly_running_count=2,
    typical_strength_split=["strength_upper", "strength_lower", "strength_sbd"],
    sleep_window_target=("23:00", "06:30"),
    daily_kcal_target=2900,
    daily_protein_target_g=140,
    typical_strength_volume_kg=4000.0,
    typical_run_distance_m=6000.0,
    typical_run_duration_s=2200,
    typical_run_avg_hr=152,
    typical_hrv_ms=58.0,  # Suppressed vs healthy baseline
    typical_resting_hr=64,  # Elevated vs typical young-adult baseline
    typical_sleep_hours=6.5,
    typical_sleep_score=68,
    today_planned_session="strength_lower",
    today_soreness="moderate",
    today_energy="low",
    today_stress_score=5,  # Maximum subjective stress
    # W-AK / F-IR-03 inline declaration. P11 is the elevated-stress
    # contract test: the stress domain may legitimately escalate
    # under sustained high subjective + wearable stress per W-O.
    # Override the established default to allow stress escalation;
    # remove escalate from the stress forbidden list for the same
    # reason. Other domains keep the default behaviour.
    expected_actions={
        **established_expected_actions(),
        "stress": [
            "maintain_routine",
            "add_low_intensity_recovery",
            "schedule_decompression_time",
            "escalate_for_user_review",
            "defer_decision_insufficient_signal",
        ],
    },
    forbidden_actions={
        **established_forbidden_actions(),
        # Stress escalation is the ALLOWED action under elevated load;
        # remove it from the blacklist this persona inherits.
        "stress": [],
    },
    recorded_strength_history=[
        StrengthSession(
            date_offset_days=2,
            session_type="strength_upper",
            total_volume_kg=4200.0,
            rpe_avg=8.5,
        ),
        StrengthSession(
            date_offset_days=5,
            session_type="strength_sbd",
            total_volume_kg=4500.0,
            rpe_avg=8.0,
        ),
    ],
    recorded_run_history=[
        RunSession(
            date_offset_days=1,
            distance_m=5500.0,
            duration_s=2100,
            avg_hr=158,
            feel=2,
        ),
    ],
    recorded_nutrition_history=[
        NutritionDay(
            date_offset_days=0,
            calories=2850.0,
            protein_g=142.0,
            carbs_g=290.0,
            fat_g=110.0,
        ),
    ],
)
