# Non-goals

What this project refuses to build. Stated explicitly so scope
discipline is load-bearing, not aspirational.

This file applies to HAI, the personal-wellness reference runtime. For
the paper, these boundaries are part of the evaluated runtime contract:
HAI is not clinical software and does not diagnose, treat, prescribe, or
make autonomous medical decisions.

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

## Not a broad multi-source fusion platform

- Two pull surfaces exist today: the committed Garmin-format CSV fixture and
  live intervals.icu. Garmin Connect live scraping is present but best-effort,
  rate-limited, and not the default supported live source.
- Apple Health, Oura, Whoop, Strava are NOT scoped for v1. The
  pull layer keeps a small adapter Protocol so another source is addable,
  but adding one is a product decision, not a background goal.

## Not meal-level nutrition in v1

Phase 2.5 retrieval-gate outcome (see
``reporting/plans/historical/phase_2_5_retrieval_gate.md``) compressed Phase 5
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

## Not a complete skill-narration eval harness yet

Phase 2.5 Track B Condition 3 attached a skill-harness follow-up to
Phase 3. v0.1.8 partially closes it with ``verification/evals/skill_harness/``
for recovery + running readiness outputs and
``verification/evals/synthesis_harness/`` for synthesis-skill output fixtures.
That is useful evidence, but not a complete skill-eval story: live transcript
capture is still operator-driven, no LLM-judge axis ships, four domain skills
remain uncovered, and live runs do not belong in normal CI. Deterministic
runtime evals (classify + policy + synthesis firings + mutations) remain the
fully scored packaged surface.

## Not a coach, a clinician, or a replacement for informed user
judgment

- No autonomous training plan generation. The runtime does not
  propose multi-day or multi-week training prescriptions on its own
  initiative. Daily recommendations shape or escalate whatever
  session the user already planned.
- No autonomous diet plan generation. The runtime does not propose
  meal plans, macro splits, or nutrition regimes. Nutrition
  recommendations adjust against the user's own goal.
- No mental-health surface, no crisis triage.

### What IS allowed (current v1 surface)

The above forbids *autonomous* prescriptions. The following user-
driven shapes are explicitly in scope and should not be confused
with plan generation:

- **User-authored intent.** A user (or an agent acting on the
  user's explicit instruction) records what they intend to do —
  planned sessions, sleep windows, rest days, travel, constraints.
  Persisted in the intent ledger (W49). The runtime reads intent
  to interpret outcomes; it does not invent intent.
- **User-authored targets.** A user records or confirms wellness
  targets — hydration, protein, calories, sleep duration / window,
  training-load aim. Persisted in the target ledger (W50) with
  reason, source, effective date, and review date. Targets are
  wellness support, not clinical prescriptions.
- **Agent-proposed intent / targets** are allowed only when (a)
  marked with ``source=agent_proposed`` (or equivalent), and (b)
  gated behind an explicit user commit path before becoming
  active. They never auto-promote.

### What may be allowed later, with new governance

Out of scope for the current v1 surface, listed here only so contributors do
not mistake it for "currently shipping":

- Bounded wellness plan suggestions inside fixed enums (e.g.
  "rest", "easy aerobic", "tempo"), surfaced as proposals that
  require user approval, are auditable, and supersede via the
  same archive/supersession discipline as intent and target rows.
- Outcome-derived target *review* prompts — never automatic
  target mutation.

Anything beyond those two items — model-driven training plans,
diet prescriptions, autonomous regimen design, hidden adaptation
from outcomes — remains explicitly out of scope.

## Not a broad integration platform

- `v0.1.15.1` is released and installable from PyPI.
- `hai init` and `hai doctor` ship in v1.
- An MCP server wrapper remains optional and deferred; the shipped
  surface is the `hai` CLI plus packaged skills.

## What is explicitly in-scope

Counterpoint for clarity — these ARE in v1:

- Six domains with classify + policy + skill per domain.
- Synthesis with 11 X-rules across two phases: 10 Phase A rules and
  one Phase B adjustment rule.
- Schema-validated boundaries for propose, synthesize, review, intake,
  intent, and target paths.
- Atomic SQLite transactions around daily_plan commits.
- Review loop with per-domain counts.
- Config-driven thresholds via platformdirs TOML.
- Evaluation framework at ``verification/evals/`` covering domain
  classify/policy + synthesis X-rules deterministically.
