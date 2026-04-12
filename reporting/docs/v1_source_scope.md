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
- `gym_exercise_set`
- `nutrition_daily`
- `supplement_intake`
- `lab_result`
- `subjective_daily_input`
- `daily_health_snapshot`

## v1 source decision table

| Source family | v1 status | Entry lane | Why in scope now | Expected canonical artifact families |
| --- | --- | --- | --- | --- |
| Garmin | in_v1 | `pull` | already grounded in repo docs, data, and current adapter reality | `source_record`, `provenance_record`, `sleep_daily`, `readiness_daily`, `training_session`, `daily_health_snapshot` |
| Strava | in_v1 | `pull` | required for cross-source training overlap contract, especially with Garmin | `source_record`, `provenance_record`, `training_session`, `daily_health_snapshot` |
| nutrition system / imported food pipeline | in_v1 | `pull` | current repo already has nutrition domain surfaces and imported-food schema intent | `source_record`, `provenance_record`, `nutrition_daily`, `daily_health_snapshot` |
| supplements | in_v1 | `merge_human_inputs` first, future `pull` allowed later | important health-domain input, but likely manual-first in current v1 reality | `source_record`, `provenance_record`, `supplement_intake`, `daily_health_snapshot` |
| bloodwork | in_v1 | `merge_human_inputs` first, future `pull` allowed later | important health-domain input, currently best treated as manual-first | `source_record`, `provenance_record`, `lab_result`, `daily_health_snapshot` |
| Oura | in_v1 | `pull` | high-value passive source family, must be covered by the platform contract before implementation | `source_record`, `provenance_record`, `sleep_daily`, `readiness_daily`, `training_session`, `daily_health_snapshot` |
| resistance training | in_v1 | `merge_human_inputs` required initially | current repo already has manual gym logging and schema support that should be frozen at contract level | `source_record`, `provenance_record`, `training_session`, `gym_exercise_set`, `daily_health_snapshot` |
| manual subjective recovery inputs | in_v1 | `merge_human_inputs` | already a real lane responsibility and needed for daily context | `source_record`, `provenance_record`, `subjective_daily_input`, `daily_health_snapshot` |
| voice-note / manual human inputs | in_v1 | `merge_human_inputs` | already a canonical lane with voice-note intake and manual logging | `source_record`, `provenance_record`, `subjective_daily_input`, `supplement_intake`, `lab_result`, `gym_exercise_set`, `training_session`, `nutrition_daily`, `daily_health_snapshot` |

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
- the required initial entry lane is `merge_human_inputs`
- the canonical normalized outputs are `training_session` and `gym_exercise_set`
- manual logs and future imported lifting adapters must converge into those same canonical outputs
- exercise identity, session grouping, and progression metrics are real design obligations, but their deeper modeling spec is deferred to a separate bounded slice

## Garmin and Strava overlap expectation

Garmin and Strava are both in scope for v1.

The platform contract therefore freezes that:
- both may emit running or training evidence into `training_session`
- v1 must not silently double-count overlapping sessions
- unresolved overlap must remain explicit in provenance and conflict state instead of being guessed away

## Out of scope confirmation

This document does not:
- implement any adapter
- restructure the repo
- add new canonical buckets
- require a full resistance-training deep spec in the same slice
