# State Model v1

Status: maintained human-readable map of the v1 runtime state model.
The **source of truth for exact DDL is the live SQLite schema** under
`hai/src/health_agent_infra/core/state/migrations/`. Schema head is 025
as of v0.1.15: `024_gym_set_id_with_exercise_slug` and
`025_target_macros_extension` are the latest deltas. Trust the
migration files for column-level authority; trust this doc for the
human-readable narrative and invariants.

## Purpose

The state model exists to give the runtime durable, local memory.
Conversation context is not the source of truth. The source of truth is
the on-device SQLite database, which stores:

- raw evidence and user-reported intake
- accepted per-domain day-level state
- proposal and recommendation history
- synthesis audit rows
- review events and review outcomes
- explicit user memory, intent, target, sync, runtime-event, and
  data-quality ledgers

The agent resumes from local runtime state, not from chat memory alone.

## Current schema head

Schema head is **025** as of v0.1.15.

- `024_gym_set_id_with_exercise_slug.sql` rewrites old-format
  `gym_set.set_id` values so set ids include the exercise slug and do
  not collide across exercises in the same session.
- `025_target_macros_extension.sql` recreates the existing `target`
  table with an extended `target_type` CHECK for `carbs_g` and
  `fat_g`; existing rows are copied forward byte-stable.

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
| `stress_manual_raw` | Subjective 1-5 stress entries and corrections. |
| `context_note` | Free-text human-input notes. |
| `manual_readiness_raw` | Subjective soreness / energy / planned-session readiness input. |
| `gym_session` | Resistance-training session envelope. |
| `gym_set` | Individual sets within a session, optionally linked to `exercise_taxonomy`. Since migration 024, default `set_id` includes the exercise slug to avoid multi-exercise set-number collisions. |
| `running_session` | Legacy raw per-activity running table from the initial schema. |
| `running_activity` | Current per-session running structure from intervals.icu activities. |
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
| `user_memory` | Durable goals, preferences, constraints, and context notes. |
| `intent_item` | User-authored or agent-proposed intent, with explicit commit/archive discipline. |
| `target` | User-authored or agent-proposed wellness targets, with explicit commit/archive discipline. Since migration 025, nutrition macro targets include `calories_kcal`, `protein_g`, `carbs_g`, and `fat_g`. |
| `sync_run_log` | Pull freshness and source status rows. |
| `runtime_event_log` | Per-command local runtime event rows for `hai stats`. |
| `data_quality_daily` | Per-domain coverage/missingness/cold-start ledger. |

There is **no** `food_taxonomy` table in v1. That was deferred by the
Phase 2.5 nutrition retrieval gate.

## Decision-state tables

These tables hold the agent/runtime decision chain. Together they
form the **three-state audit view**: `proposal_log` (per-domain
planned intent) → `planned_recommendation` (aggregate pre-X-rule
plan) → `daily_plan` + `x_rule_firing` + `recommendation_log`
(aggregate adapted plan).

| Table | Purpose |
|---|---|
| `proposal_log` | Validated `DomainProposal` rows emitted per domain. |
| `planned_recommendation` | Pre-X-rule aggregate bundle, one row per (daily_plan_id, domain). Mirrors `recommendation_log` shape with FKs to `daily_plan` and `proposal_log`. Added in migration 011 (M8 Phase 1). |
| `daily_plan` | One synthesized plan per `(for_date, user_id)` canonical key, with explicit supersession path. |
| `x_rule_firing` | Persisted X-rule firings, including tier, phase, orphan flag, source signals, and mutation JSON. |
| `recommendation_log` | Final bounded recommendations emitted by synthesis. |

Important invariants:

- `hai propose` validates proposal shape at the write boundary.
- `hai synthesize` atomically commits `daily_plan + x_rule_firing +
  planned_recommendation + recommendation_log` in one transaction.
  The `planned_recommendation` rows capture the output of
  `_mechanical_draft(original_proposal, ...)` before Phase A mutates
  anything, so `planned ⊕ firings = adapted` is verifiable from rows.
- Canonical reruns replace by `(for_date, user_id)` unless
  `--supersede` is used. `delete_canonical_plan_cascade` removes
  paired `planned_recommendation` rows so re-synthesis is clean.
- Legacy plans committed before migration 011 have no paired
  planned rows; `hai explain` degrades to a two-state view
  (adapted + performed) for those.
- Proposal chains and plan chains have canonical-leaf constraints so
  re-authoring and supersession remain walkable without cycles.

## Outcome-state tables

| Table | Purpose |
|---|---|
| `review_event` | Scheduled review prompts keyed to a recommendation. |
| `review_outcome` | Recorded review answers / outcomes. |

Review rows are domain-aware and support per-domain summaries.

## User memory, intent, target, and quality ledgers

These tables are runtime state, not hidden agent memory:

| Table | Purpose |
|---|---|
| `user_memory` | Append-only user-authored goals, preferences, constraints, and context, with archive timestamps. |
| `intent_item` | Planned sessions, sleep windows, and related intent. Agent-proposed rows require explicit user commit before becoming active. |
| `target` | Wellness targets such as hydration, protein, calories, sleep duration/window, and training-load aims. Agent-proposed rows require explicit user commit before becoming active. |
| `data_quality_daily` | Snapshot-visible per-domain coverage, missingness, source-unavailable, user-input-pending, and cold-start state. |
| `sync_run_log` | Source freshness and pull status. |
| `runtime_event_log` | Local command observability for `hai stats`; not package telemetry. |

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
  - where the fact came from (`garmin`, `intervals_icu`, `user_manual`, etc.)
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
- no agent-side memory store or vector database

Human input may be typed directly or transcribed upstream, but in both
cases it enters the runtime through the same typed `hai intake ...`
surfaces and lands in the same raw tables.

## Where to read next

- `hai/docs/architecture.md` — full pipeline
- `hai/docs/x_rules.md` — synthesis rule catalogue
- `hai/docs/non_goals.md` — scope boundaries
- `README.md` — repo-level overview
