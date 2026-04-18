# Non-goals

What this project refuses to build. Stated explicitly so scope
discipline is load-bearing, not aspirational.

## Not a medical device

- No diagnostic output. The runtime interprets observed state — it
  does not claim the presence or absence of any condition.
- No clinical-grade claims. Bands, scores, and escalations are for
  training-adjustment support; they are not biomarkers.
- No provider integration (no EHR, no lab results, no prescription
  interaction surface).

## Not a hosted product

- No server-side runtime. Everything runs locally against the
  user's machine + user-owned credentials.
- No multi-user support. The schema carries a ``user_id`` field but
  always resolves to a single local user. Auth, row-level isolation,
  and tenant separation are not scoped.
- No cloud sync, no backup service, no fleet telemetry.

## Not a chatbot UI

- No voice interface, no mobile app, no web UI. The agent surface
  is a typed conversation in Claude Code (or any equivalent agent
  runtime) plus the ``hai`` CLI.
- No always-on listening, no push notifications.

## Not a learning loop (yet)

- The runtime records review outcomes but does NOT feed them back
  into confidence calibration, threshold tuning, or any ML model.
- ``hai review summary`` counts outcomes; it does not adjust future
  recommendations.
- A minimal learning loop is an explicit deferred open question —
  see the rebuild plan §8.

## Not a multi-source fusion platform

- One wearable source in v1: Garmin (CSV fixture + optional live
  pull via ``python-garminconnect``).
- Apple Health, Oura, Whoop, Strava are NOT scoped for v1. The
  pull layer is structured around a ``FlagshipPullAdapter`` Protocol
  so a second source is addable, but adding one is a product
  decision, not a background goal.

## Not meal-level nutrition in v1

Phase 2.5 retrieval-gate outcome (see
``reporting/plans/phase_2_5_retrieval_gate.md``) compressed Phase 5
to macros-only:

- No ``hai intake meal`` command.
- No ``meal_log`` raw table.
- No ``food_taxonomy`` import (USDA FoodData Central deferred).
- No ``skills/nutrition-intake/SKILL.md``.
- No ``hai food search`` command.
- No meal-level derivation path in the nutrition projector —
  ``accepted_nutrition_state_daily.derivation_path`` is exclusively
  ``'daily_macros'`` in v1.

Micronutrient classification therefore always resolves to
``micronutrient_coverage = 'unavailable_at_source'``. X-rules
dependent on micronutrient signals (iron / magnesium / etc) do not
fire — they degrade to ``unavailable`` rather than inferring
deficiency from absence.

Meal-level returns to a release plan only after the three
structural failure classes flagged in the gate findings (aliasing,
composite decomposition, canonical-generic preference) are fixed
and a re-gate passes strict top-1 ≥ 80%.

## Not a skill-narration eval harness (yet)

Phase 2.5 Track B Condition 3 attached a skill-harness follow-up to
Phase 3; Phase 6 inherits the gap rather than pretending to close
it. See ``safety/evals/skill_harness_blocker.md`` for the explicit
blockers (live agent runtime, non-determinism + judge rubric, CI
secret handling). Deterministic runtime evals (classify + policy +
synthesis firings + mutations) are fully scored; skill-layer
rationale prose is marked ``skipped_requires_agent_harness`` per
scenario until the harness lands.

## Not a coach, a clinician, or a replacement for informed user
judgment

- No training plan generation. Recommendations shape or escalate
  whatever session the user already planned.
- No diet plan generation. Nutrition recommendations adjust targets
  against the user's own goal, not a prescribed regime.
- No mental-health surface, no crisis triage.

## Not polished for general install

- Source checkout install is supported (``pip install -e .``); a
  wheel install + PyPI publish is scoped for Phase 7.
- First-run wizard (``hai init``) + MCP server wrapper are Phase 7
  deliverables, not v1.

## What is explicitly in-scope

Counterpoint for clarity — these ARE in v1:

- Six domains with classify + policy + skill per domain.
- Synthesis with 10 X-rule evaluators across two phases.
- Schema-validated writeback at three points (propose,
  synthesize, writeback).
- Atomic SQLite transactions around daily_plan commits.
- Review loop with per-domain counts.
- Config-driven thresholds via platformdirs TOML.
- Evaluation framework at ``safety/evals/`` covering domain
  classify/policy + synthesis X-rules deterministically.
