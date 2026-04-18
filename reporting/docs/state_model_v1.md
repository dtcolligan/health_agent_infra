# State Model v1

Status: **authoritative** for the shipped `v0.1.0` rebuild.

The source of truth is the live SQLite schema under
`src/health_agent_infra/core/state/migrations/001..006.sql`. This
document is the human-readable map of that schema and of the runtime
rules that sit around it.

## Purpose

The state model exists to give the runtime durable, local memory.
Conversation context is not the source of truth. The source of truth is
the on-device SQLite database, which stores:

- raw evidence and user-reported intake
- accepted per-domain day-level state
- proposal and recommendation history
- synthesis audit rows
- review events and review outcomes

The agent resumes from local runtime state, not from chat memory alone.

## Layers

The runtime has four state layers:

1. **Raw evidence**
   - vendor- or user-authored facts
   - append-only, correction-linked where applicable
2. **Accepted state**
   - canonical per-day state the runtime reasons over
   - deterministically projected from raw evidence
3. **Decision state**
   - proposals, daily plans, X-rule firings, recommendations
4. **Outcome state**
   - scheduled reviews and recorded outcomes

## Current domains

Six domains are first-class in v1:

- recovery
- running
- sleep
- stress
- strength
- nutrition

Nutrition is macros-only in v1. No meal-level or food-taxonomy state is
part of the shipped schema.

## Persistence grammar

The runtime uses a hybrid grammar:

- **Raw evidence** is append-only, with supersession pointers for
  corrected rows where relevant.
- **Accepted state** is UPSERT-style canonical state keyed by date/user
  (and source where applicable), with projection metadata.
- **Decision and outcome state** is append-only or versioned by explicit
  identifiers.

This keeps auditability at the raw layer while letting the runtime read
one canonical row per domain/day.

## Raw evidence tables

These tables capture source truth before projection:

| Table | Purpose |
|---|---|
| `source_daily_garmin` | Full Garmin daily row for one date. |
| `nutrition_intake_raw` | Daily macro intake entries and corrections. |
| `stress_score_raw` | Subjective 1–5 stress entries and corrections. |
| `context_note_raw` | Free-text human-input notes. |
| `manual_readiness_raw` | Subjective soreness / energy / planned-session readiness input. |
| `gym_session` | Resistance-training session envelope. |
| `gym_set` | Individual sets within a session, optionally linked to `exercise_taxonomy`. |
| `running_session` | Reserved raw per-activity running table; declared but not populated in v1. |
| `goal` | User-declared goals, optionally domain-scoped. |

## Accepted state tables

These are the canonical tables the runtime reasons over:

| Table | Domain | Role |
|---|---|---|
| `accepted_recovery_state_daily` | recovery | Resting HR, HRV, load ratios, training-readiness components, recovery-facing daily state. |
| `accepted_running_state_daily` | running | Daily running distance/intensity/session aggregates. |
| `accepted_sleep_state_daily` | sleep | Sleep duration, composition, scores, and sleep-specific nightly state. |
| `accepted_stress_state_daily` | stress | Garmin all-day stress, manual stress, body battery, stress-specific daily state. |
| `accepted_resistance_training_state_daily` | strength | Sets, reps, total volume, muscle-group volume, estimated 1RM, unmatched tokens. |
| `accepted_nutrition_state_daily` | nutrition | Daily macros/hydration/meals count with `derivation_path='daily_macros'` in v1. |

Each accepted row carries projection metadata such as:

- `derived_from`
- `projected_at`
- `corrected_at`
- provenance fields propagated from the raw layer

## Taxonomy and supporting tables

| Table | Purpose |
|---|---|
| `exercise_taxonomy` | Canonical strength exercise names, aliases, muscle groups, equipment, source. |

There is **no** `food_taxonomy` table in v1. That was deferred by the
Phase 2.5 nutrition retrieval gate.

## Decision-state tables

These tables hold the agent/runtime decision chain:

| Table | Purpose |
|---|---|
| `proposal_log` | Validated `DomainProposal` rows emitted per domain. |
| `daily_plan` | One synthesized plan per `(for_date, user_id)` canonical key, with explicit supersession path. |
| `x_rule_firing` | Persisted X-rule firings, including tier, phase, orphan flag, source signals, and mutation JSON. |
| `recommendation_log` | Final bounded recommendations emitted by synthesis/writeback. |

Important invariants:

- `hai propose` validates proposal shape at the write boundary.
- `hai synthesize` atomically commits `daily_plan + x_rule_firing + N recommendations`.
- canonical reruns replace by `(for_date, user_id)` unless `--supersede`
  is used.

## Outcome-state tables

| Table | Purpose |
|---|---|
| `review_event` | Scheduled review prompts keyed to a recommendation. |
| `review_outcome` | Recorded review answers / outcomes. |

Review rows are domain-aware and support per-domain summaries.

## Missingness model

Snapshot/build-time missingness uses four states:

- `absent`
- `partial`
- `unavailable_at_source`
- `pending_user_input`

The runtime distinguishes these explicitly so the agent does not
fabricate data from nulls.

## Provenance model

The runtime tracks provenance with two separate concepts:

- `source`
  - where the fact came from (`garmin`, `user_manual`, etc.)
- `ingest_actor`
  - what transported it into the runtime (`garmin_csv_adapter`,
    `hai_cli_direct`, `claude_agent_v1`, etc.)

This distinction matters because the same source can arrive through
multiple transports over time.

## What is deliberately not in the v1 state model

- no meal-log raw table
- no food taxonomy
- no micronutrient accepted-state columns populated from real food data
- no hosted/multi-user tenancy layer
- no learned/adaptive memory layer
- no audio/voice-specific persistence layer

Human input may be typed directly or transcribed upstream, but in both
cases it enters the runtime through the same typed `hai intake ...`
surfaces and lands in the same raw tables.

## Where to read next

- `reporting/docs/architecture.md` — full pipeline
- `reporting/docs/x_rules.md` — synthesis rule catalogue
- `reporting/docs/non_goals.md` — scope boundaries
- `README.md` — repo-level overview
