"""P10 — Adolescent recreational (W-O, v0.1.11).

Below the supported user spec band (the v1 system targets adults).
The expected behaviour is graceful failure / explicit
out-of-supported-set surfacing — this persona is the
contract test for the boundary, not "produces good
recommendations."

If the harness produces actionable recommendations for P10,
that's a product issue worth reviewing: are we over-recommending
to under-spec users, or do the bands generalise honestly?
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
    persona_id="p10_adolescent_recreational",
    label="Adolescent recreational",
    description=(
        "17-year-old male, 65kg / 170cm, light recreational sport "
        "(school PE + weekend pickup). Below the v1 supported user "
        "spec band; harness contract test for graceful out-of-set "
        "behaviour. 14-day onboarding window."
    ),
    age=17,
    sex_at_birth="male",
    weight_kg=65.0,
    height_cm=170,
    activity_level="light",
    primary_goal="maintenance",
    goal_description="General fitness; not training for anything specific",
    data_source="intervals_icu",
    history_days=14,
    weekly_strength_count=0,
    weekly_running_count=1,
    typical_strength_split=[],
    sleep_window_target=("23:30", "07:30"),
    daily_kcal_target=2400,
    daily_protein_target_g=70,
    typical_run_distance_m=4000.0,
    typical_run_duration_s=1500,
    typical_run_avg_hr=160,
    # Adolescent: higher HRV, lower RHR, more sleep.
    typical_hrv_ms=85.0,
    typical_resting_hr=52,
    typical_sleep_hours=8.5,
    typical_sleep_score=85,
    sporadic_logging=True,
    today_planned_session="rest",
    today_soreness="low",
    today_energy="high",
    today_stress_score=2,
    # W-AK / F-IR-03 inline declaration. P10 is the under-spec
    # adolescent boundary contract; defaults apply but the persona's
    # purpose is observing graceful behaviour, not pinning a sharper
    # whitelist.
    expected_actions=established_expected_actions(),
    forbidden_actions=established_forbidden_actions(),
    recorded_run_history=[
        RunSession(
            date_offset_days=4,
            distance_m=3500.0,
            duration_s=1320,
            avg_hr=165,
        ),
    ],
    recorded_nutrition_history=[
        NutritionDay(
            date_offset_days=0,
            calories=2350.0,
            protein_g=72.0,
            carbs_g=320.0,
            fat_g=80.0,
        ),
    ],
)
