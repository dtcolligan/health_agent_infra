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

This slice is still a docs/spec freeze, but it now reconciles doctrine against a tree that already contains bounded source-specific implementation and proof surfaces.

It freezes:
- which source families are in v1
- which lane each source enters through
- which canonical artifact families each source is expected to populate
- which source families are deferred, bridge/reference, or exploratory
- the platform-contract level expectation for resistance training
- the narrow flagship convergence target for this interval

This slice does not require new source-specific implementation. It classifies the live source-specific surfaces on the tree truthfully instead of pretending they do not exist.

## Flagship doctrine for this interval

The narrow flagship path `Garmin passive pull -> typed manual readiness intake -> deterministic normalization -> typed state -> policy -> bounded recommendation -> bounded local writeback -> review` was delivered 2026-04-16 as `recovery_readiness_v1`. See `clean/health_model/recovery_readiness_v1/` and the sibling proof bundles under `reporting/artifacts/flagship_loop_proof/2026-04-16-*`.

The older CLI-first lineage (`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`) remains in the tree as compatibility, not current flagship proof.

The **broader multi-source platform contract** that this source-scope doc names — full canonical artifact families (`source_record`, `provenance_record`, `sleep_daily`, `readiness_daily`, `training_session`, `daily_health_snapshot`) emitted across many source families — is **aspirational platform scope beyond the current flagship**. The flagship's Garmin adapter (`pull/garmin/recovery_readiness_adapter.py`) emits a narrow `CleanedEvidence` dict, not the full canonical family. Two adapter lineages coexist in the tree: the thin flagship adapter, and older broader surfaces that aspire to the platform contract.

This source-scope doc therefore distinguishes:
- flagship-delivered source families (Garmin + typed manual readiness, via the narrow `recovery_readiness_v1` slice)
- current-proof-but-broader manual surfaces (the older CLI-first lineage)
- bridge/reference source families (named in the platform contract, not flagship-critical)
- exploratory non-flagship connector surfaces (wger)

## Lane boundary summary

- `pull` owns source acquisition, import, raw receipts, and source-specific extraction for passive or machine-readable inputs.
- `clean` owns deterministic normalization into canonical artifact families, validation, and conflict expression.
- `merge_human_inputs` owns human-authored and semi-manual inputs such as typed manual readiness, voice notes, manual gym logs, manual subjective inputs, and manual context notes.

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

| Source family | v1 status | Entry lane | Doctrine role | Why in scope now | Expected canonical artifact families |
| --- | --- | --- | --- | --- | --- |
| Garmin | in_v1 | `pull` | flagship_target | passive-data anchor for the delivered flagship path; thin `recovery_readiness_v1` adapter emits `CleanedEvidence`; older broader surfaces aspire to the full canonical-family emission | `source_record`, `provenance_record`, `sleep_daily`, `readiness_daily`, `training_session`, `daily_health_snapshot` (broader-family aspiration; flagship slice emits narrower `CleanedEvidence` only) |
| typed manual readiness / subjective recovery inputs | in_v1 | `merge_human_inputs` | flagship_target | human-input anchor for the delivered flagship path, consumed by `clean_inputs` as a typed manual readiness dict; explicit/manual by design rather than implied through third-party tooling | `source_record`, `provenance_record`, `subjective_daily_input`, `readiness_daily`, `daily_health_snapshot` (broader-family aspiration; flagship slice consumes a narrower manual readiness dict only) |
| voice-note / broader manual human inputs | in_v1 | `merge_human_inputs` | current_proof_broader_manual_surface | the older CLI-first proof path uses voice-note intake; the narrower typed-readiness flagship (`recovery_readiness_v1`) does not depend on it | `source_record`, `provenance_record`, `subjective_daily_input`, `supplement_intake`, `lab_result`, `gym_set_record`, `training_session`, `nutrition_daily`, `daily_health_snapshot` |
| Cronometer | in_v1 | `pull` | bridge_reference | useful bounded nutrition and supplements bridge/reference source via export-first connector surfaces, but not required for flagship completion | `source_record`, `provenance_record`, `nutrition_daily`, `supplement_intake`, `daily_health_snapshot` |
| supplements | in_v1 | `merge_human_inputs` first, future `pull` allowed later | bridge_reference | valid manual fallback and backfill path whether or not Cronometer is present | `source_record`, `provenance_record`, `supplement_intake`, `daily_health_snapshot` |
| bloodwork | in_v1 | `merge_human_inputs` first, future `pull` allowed later | bridge_reference | important health-domain input, currently best treated as manual-first rather than a flagship dependency | `source_record`, `provenance_record`, `lab_result`, `daily_health_snapshot` |
| resistance training | in_v1 | `merge_human_inputs` first, future `pull` adapters allowed later | manual_first_non_flagship_connectors | manual structured logs inside Health Lab are the source-of-truth path for this freeze, while external gym connectors remain optional later convergence surfaces | `source_record`, `provenance_record`, `training_session`, `gym_set_record`, `exercise_catalog`, `exercise_alias`, `program_block`, `daily_health_snapshot` |
| wger | in_v1 | `pull` | exploratory_non_flagship_connector | useful bounded gym connector work with a live mock-backed proof bundle, but not the flagship source of truth and not required for flagship completion | `source_record`, `provenance_record`, `training_session`, `gym_set_record`, `exercise_catalog`, `exercise_alias`, `program_block`, `daily_health_snapshot` |
| Strava | in_v1 | `pull` | bridge_reference | still relevant for overlap contracts, but not part of the frozen flagship convergence target | `source_record`, `provenance_record`, `training_session`, `daily_health_snapshot` |
| Oura | in_v1 | `pull` | bridge_reference | high-value passive source family that can remain in the platform contract without becoming a flagship gate for this interval | `source_record`, `provenance_record`, `sleep_daily`, `readiness_daily`, `training_session`, `daily_health_snapshot` |

## Deferred but not required for this slice

The following are intentionally deferred as separate source-specific or family-specific design work:
- source-specific adapter docs beyond the v1 shared adapter contract
- a full `reporting/docs/resistance_training_model_v1.md`
- richer exercise identity catalog design
- detailed auth/storage handling per third-party service
- additional source-specific proof bundles beyond the bounded ones already on the tree
- making Cronometer, `wger`, or any other external connector a flagship-completion gate

## Placeholder-only status in this slice

This slice does not create any additional placeholder-only source families beyond the named in-scope set above.

A future source may be added later, but not without updating the source registry and preserving the same lane and provenance rules.

## Resistance-training v1 freeze

Resistance training is in v1 now.

The contract-level freeze is:
- manual structured logs inside `merge_human_inputs` are the current source-of-truth path for this doctrine interval
- `wger` is the retained bounded exploratory connector surface on the tree, but it remains non-flagship and not the source of truth
- the canonical normalized outputs are Health Lab owned objects, not connector-native objects
- the gym-domain core centers on `training_session`, `exercise_catalog`, `exercise_alias`, `gym_set_record`, and `program_block`
- derived metrics such as volume, estimated 1RM, weekly hard sets, density, and adherence remain Health Lab downstream concerns
- future imported lifting adapters must converge into the same canonical gym-domain objects rather than redefining the flagship source of truth

## Supplements coexistence expectation

Cronometer and manual supplements are both in scope for v1, but Cronometer is bridge/reference rather than flagship-critical.

The platform contract therefore freezes that:
- Cronometer is the preferred machine-readable source for `supplement_intake`
- manual supplements remain valid when Cronometer data is absent, incomplete, late, intentionally unused, or missing needed detail
- v1 must not silently merge or silently override overlapping Cronometer and manual supplement records
- overlap must resolve explicitly as `superseded` when deterministic duplicate handling is justified, or `coexists_conflicted` when ambiguity remains
- repeated processing must preserve distinct source identities unless explicit duplicate resolution has already been applied

## Garmin and Strava overlap expectation

Garmin and Strava are both in scope for v1.

The platform contract therefore freezes that:
- both may emit running or training evidence into `training_session`
- v1 must not silently double-count overlapping sessions
- unresolved overlap must remain explicit in provenance and conflict state instead of being guessed away

## Out of scope confirmation

This document does not:
- implement any new adapter
- widen existing connector implementation beyond the bounded surfaces already present
- restructure the repo beyond documenting the preferred source path shape
- add new canonical buckets
- require a full resistance-training deep spec in the same slice
- require `wger` or Cronometer for flagship completion
