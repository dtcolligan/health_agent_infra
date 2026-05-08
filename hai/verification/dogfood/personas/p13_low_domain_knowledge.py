"""P13 — Low-domain-knowledge user (v0.1.14 W-EXPLAIN-UX).

A 35-year-old casual exerciser with no athletics background, basic
English, smartphone-native but not CLI-native. They are the
canonical "would they understand the explain output?" persona.

Per v0.1.14 PLAN.md §2.C, P13 is **matrix-only** (covered by the
12+1 persona matrix smoke test) and is **not** part of the W-Vb-3
demo-replay residual (which owns P2..P12). Per F-PLAN-06, this is
deliberate: P13 surfaces UX confusion modes via matrix observation,
not via the demo-replay declarative-actions contract.

The expected_actions are deliberately permissive — the test isn't
"P13 gets a specific recommendation"; it's "the runtime doesn't
crash on a low-history user, refuses honestly when signal is
sparse, and the explain output is legible to a non-expert."
v0.1.15 W-2U-GATE will retest the same trajectories against an
actual foreign user; v0.1.14 ships the maintainer-substitute
baseline.
"""

from __future__ import annotations

from .base import (
    PersonaSpec,
    established_expected_actions,
    established_forbidden_actions,
)


SPEC = PersonaSpec(
    persona_id="p13_low_domain_knowledge",
    label="Low domain knowledge (W-EXPLAIN-UX)",
    description=(
        "35-year-old female, 64kg / 165cm, light activity. No athletics "
        "background; uses HAI to track readiness and basic nutrition. "
        "12 days of intervals.icu history (just signed up). Sporadic "
        "logging — about half the days have nutrition data. Stresses: "
        "thin history (R1 / sparse-coverage path), basic-English "
        "explain prose legibility, low domain knowledge for technical "
        "terms (zone 2, HRV, ACWR). Per v0.1.14 W-EXPLAIN-UX, this "
        "persona is the maintainer-substitute reader's lens — "
        "'would this user understand the explain output?' — and is "
        "matrix-only (no W-Vb-3 demo-replay coverage; foreign-user "
        "review carries forward to v0.1.15 W-2U-GATE)."
    ),
    age=35,
    sex_at_birth="female",
    weight_kg=64.0,
    height_cm=165,
    activity_level="light",
    primary_goal="general_fitness",
    goal_description=(
        "General health + occasional walks; not training for anything"
    ),
    data_source="intervals_icu",
    history_days=12,
    weekly_strength_count=0,
    weekly_running_count=1,
    typical_strength_split=[],
    sleep_window_target=("23:00", "07:00"),
    daily_kcal_target=1900,
    daily_protein_target_g=80,
    typical_run_distance_m=3000.0,
    typical_run_duration_s=1800,
    typical_run_avg_hr=145,
    typical_hrv_ms=42.0,
    typical_resting_hr=68,
    typical_sleep_hours=7.0,
    typical_sleep_score=75,
    sporadic_logging=True,
    today_planned_session="rest",
    today_soreness="low",
    today_energy="moderate",
    today_stress_score=3,
    # W-AK / F-IR-03 inline declaration. P13 has 12 days of history
    # so the established baseline applies; sparse-history personas
    # legitimately surface defer + maintain across most domains, but
    # the established whitelist already permits both.
    expected_actions=established_expected_actions(),
    forbidden_actions=established_forbidden_actions(),
)
