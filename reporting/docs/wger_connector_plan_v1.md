# wger connector plan v1

This document defines the bounded v1 role of **wger** inside Health Lab.

Core rule:
- wger is a **gym-domain source system / component**
- wger is **not** the architecture
- Health Lab keeps its own canonical schema, provenance rules, and agent-facing contracts

## Why wger for v1

wger is a better v1 resistance-training source-system fit than a closed consumer UI because it is:
- open-source
- API-exposed
- more controllable as an integration substrate
- more aligned with the project thesis of agent-first health infrastructure over open and inspectable source systems

## v1 role

wger is the preferred v1 resistance-training connector source.

Interpretation:
- Garmin = recovery / activity / physiology
- wger = resistance training
- Cronometer = nutrition / supplements

## Architectural rule

Source systems are interchangeable.

Health Lab owns the canonical health evidence model.
Agent-facing tools must operate over Health Lab normalized state, not directly over wger-native schemas.

## Proposed repo surfaces

### pull
- `pull/sources/wger/`
  - source acquisition
  - raw receipts
  - auth/session handling if needed
  - incremental sync state
  - runtime durability and retry logic

### clean
- `clean/transforms/wger/` or `clean/transforms/resistance_training/`
  - deterministic mapping from wger source records into Health Lab canonical artifacts
  - provenance attachment
  - conflict expression if later multiple gym sources coexist

## Canonical targets

wger must map into Health Lab canonical objects, not become the canonical object model.

Primary canonical targets:
- `training_session`
- `exercise_catalog`
- `exercise_alias`
- `gym_set_record`
- `program_block`

Derived metrics expected around the same domain:
- volume
- estimated 1RM
- weekly hard sets
- density
- adherence

## v1 adapter contract intent

The wger adapter should:
- preserve stable source identity from wger receipts
- emit stable Health Lab canonical IDs
- attach provenance on every normalized output
- support incremental pull, not full-history refetch by default
- support durable resume after interruption
- keep source independence so another gym source can be added later without changing the canonical contract

## Non-goals for this slice

This document does not:
- make wger the only possible future gym source
- require Health Lab to mirror wger-native data structures exactly
- remove support for manual gym inputs as a fallback or coexistence path
- finalize every resistance-training metric formula in the same slice
