"""P12 — Vacation-returner (W-O, v0.1.11).

Tests classifier behaviour after a deliberate data discontinuity:
14 days of normal training, then a 14-day gap (vacation, no
wearable, no training), then today is "back to baseline."
The stress-test is whether the bands degrade gracefully under
the discontinuity rather than firing false-spike escalations on
the first session back.

W-B's volume-spike-coverage gate (this same cycle) addresses the
strength-side spike-on-first-session-back pattern, so P12 is the
acceptance-test fixture for that fix at the matrix level.
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
    persona_id="p12_vacation_returner",
    label="Vacation-returner",
    description=(
        "35-year-old female, 65kg / 168cm. Trained normally for 14 "
        "days, then took 14 days off (vacation, no wearable). Today "
        "is the first day back. Stresses classifier behaviour across "
        "a deliberate data discontinuity. Expected: defer / yield "
        "rather than spike-escalate."
    ),
    age=35,
    sex_at_birth="female",
    weight_kg=65.0,
    height_cm=168,
    activity_level="moderate",
    primary_goal="performance",
    goal_description="Resume base building after vacation",
    data_source="intervals_icu",
    # 28 days of history — but the middle 14 are gap days.
    history_days=28,
    history_gap_days=tuple(range(1, 15)),  # offsets 1..14 = the gap window
    weekly_strength_count=2,
    weekly_running_count=3,
    typical_strength_split=["strength_full_body", "strength_upper"],
    sleep_window_target=("22:30", "06:30"),
    daily_kcal_target=2300,
    daily_protein_target_g=105,
    typical_strength_volume_kg=2500.0,
    typical_run_distance_m=6000.0,
    typical_run_duration_s=2300,
    typical_run_avg_hr=148,
    typical_hrv_ms=68.0,
    typical_resting_hr=58,
    typical_sleep_hours=7.5,
    typical_sleep_score=82,
    today_planned_session="easy",
    today_soreness="low",
    today_energy="high",
    today_stress_score=2,
    # W-AK / F-IR-03 inline declaration. Returning from a 14-day
    # gap; defer + downgrade are the desirable shapes (the bands
    # should not false-spike on first session back). Defaults cover
    # both, no override needed.
    expected_actions=established_expected_actions(),
    forbidden_actions=established_forbidden_actions(),
    # Pre-vacation training history (offsets 15..28).
    recorded_strength_history=[
        StrengthSession(
            date_offset_days=16,
            session_type="strength_full_body",
            total_volume_kg=2400.0,
        ),
        StrengthSession(
            date_offset_days=20,
            session_type="strength_upper",
            total_volume_kg=2200.0,
        ),
    ],
    recorded_run_history=[
        RunSession(
            date_offset_days=15,
            distance_m=5500.0,
            duration_s=2100,
            avg_hr=146,
        ),
        RunSession(
            date_offset_days=18,
            distance_m=7000.0,
            duration_s=2700,
            avg_hr=150,
        ),
    ],
    recorded_nutrition_history=[
        NutritionDay(
            date_offset_days=0,
            calories=2280.0,
            protein_g=108.0,
            carbs_g=280.0,
            fat_g=85.0,
        ),
    ],
)
