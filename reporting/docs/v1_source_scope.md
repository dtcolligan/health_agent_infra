# v1 source scope

This document freezes the bounded v1 source scope for the Health Lab multi-source platform contract.

It preserves the canonical eight-bucket model:
- `pull`
- `clean`
- `merge_human_inputs`
- `research`
- `interpretation`
- `reporting`
- `writeback`
- `safety`

No additional canonical bucket is created by this spec.

## Purpose of this slice

This slice is docs/spec only.

It freezes:
- which source families are in v1
- which lane each source enters through
- which canonical artifact families each source is expected to populate
- which source families are deferred or placeholder-only
- the platform-contract level expectation for resistance training
- the preferred v1 connector trio: Garmin + wger + Cronometer

This slice does not add source-specific implementation.

## Lane boundary summary

- `pull` owns source acquisition, import, raw receipts, and source-specific extraction for passive or machine-readable inputs.
- `clean` owns deterministic normalization into canonical artifact families, validation, and conflict expression.
- `merge_human_inputs` owns human-authored and semi-manual inputs such as voice notes, manual gym logs, manual subjective inputs, and manual context notes.

These boundaries are non-overlapping.

## Canonical artifact families frozen for v1

The downstream normalized artifact families for v1 are:
- `source_record`
- `provenance_record`
- `sleep_daily`
- `readiness_daily`
- `training_session`
- `exercise_catalog`
- `exercise_alias`
- `gym_set_record`
- `program_block`
- `nutrition_daily`
- `supplement_intake`
- `lab_result`
- `subjective_daily_input`
- `daily_health_snapshot`

## v1 source decision table

| Source family | v1 status | Entry lane | Why in scope now | Expected canonical artifact families |
| --- | --- | --- | --- | --- |
| Garmin | in_v1 | `pull` | already grounded in repo docs, data, and current adapter reality, and now part of the frozen v1 trio | `source_record`, `provenance_record`, `sleep_daily`, `readiness_daily`, `training_session`, `daily_health_snapshot` |
| wger | in_v1 | `pull` | preferred open, controllable gym-domain source system for resistance training in v1 | `source_record`, `provenance_record`, `training_session`, `gym_set_record`, `exercise_catalog`, `exercise_alias`, `program_block`, `daily_health_snapshot` |
| Cronometer | in_v1 | `pull` | preferred nutrition and supplements source system in v1 via bounded export-first connector surfaces | `source_record`, `provenance_record`, `nutrition_daily`, `supplement_intake`, `daily_health_snapshot` |
| Strava | in_v1 | `pull` | required for cross-source training overlap contract, especially with Garmin, but not in the frozen first trio | `source_record`, `provenance_record`, `training_session`, `daily_health_snapshot` |
| supplements | in_v1 | `merge_human_inputs` first, future `pull` allowed later | still valid manual-first fallback even though Cronometer is the preferred source system | `source_record`, `provenance_record`, `supplement_intake`, `daily_health_snapshot` |
| bloodwork | in_v1 | `merge_human_inputs` first, future `pull` allowed later | important health-domain input, currently best treated as manual-first | `source_record`, `provenance_record`, `lab_result`, `daily_health_snapshot` |
| Oura | in_v1 | `pull` | high-value passive source family, must be covered by the platform contract before implementation | `source_record`, `provenance_record`, `sleep_daily`, `readiness_daily`, `training_session`, `daily_health_snapshot` |
| resistance training | in_v1 | `pull` via preferred `wger` source, manual fallback remains allowed | v1 gym domain should center on a controllable external source system while preserving source independence and fallback manual entry | `source_record`, `provenance_record`, `training_session`, `gym_set_record`, `exercise_catalog`, `exercise_alias`, `program_block`, `daily_health_snapshot` |
| manual subjective recovery inputs | in_v1 | `merge_human_inputs` | already a real lane responsibility and needed for daily context | `source_record`, `provenance_record`, `subjective_daily_input`, `daily_health_snapshot` |
| voice-note / manual human inputs | in_v1 | `merge_human_inputs` | already a canonical lane with voice-note intake and manual logging | `source_record`, `provenance_record`, `subjective_daily_input`, `supplement_intake`, `lab_result`, `gym_set_record`, `training_session`, `nutrition_daily`, `daily_health_snapshot` |

## Deferred but not required for this slice

The following are intentionally deferred as separate source-specific or family-specific design work:
- source-specific adapter docs beyond the v1 shared adapter contract
- a full `reporting/docs/resistance_training_model_v1.md`
- richer exercise identity catalog design
- detailed auth/storage handling per third-party service
- source-specific proof bundles beyond the contract-level proof expectations

## Placeholder-only status in this slice

This slice does not create any additional placeholder-only source families beyond the named in-scope set above.

A future source may be added later, but not without updating the source registry and preserving the same lane and provenance rules.

## Resistance-training v1 freeze

Resistance training is in v1 now.

The contract-level freeze is:
- the preferred v1 source-system entry lane is `pull` through `wger`
- manual logs remain a valid fallback and coexistence path, not the primary v1 assumption
- the canonical normalized outputs are Health Lab owned objects, not wger-native objects
- the gym-domain core now centers on `training_session`, `exercise_catalog`, `exercise_alias`, `gym_set_record`, and `program_block`
- derived metrics such as volume, estimated 1RM, weekly hard sets, density, and adherence remain Health Lab downstream concerns
- future imported lifting adapters must converge into the same canonical gym-domain objects

## Garmin and Strava overlap expectation

Garmin and Strava are both in scope for v1.

The platform contract therefore freezes that:
- both may emit running or training evidence into `training_session`
- v1 must not silently double-count overlapping sessions
- unresolved overlap must remain explicit in provenance and conflict state instead of being guessed away

## Out of scope confirmation

This document does not:
- implement any adapter
- restructure the repo beyond documenting the preferred source path shape
- add new canonical buckets
- require a full resistance-training deep spec in the same slice
