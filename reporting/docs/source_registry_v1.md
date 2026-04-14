# source registry v1

This document is the canonical v1 source registry for the Health Lab platform contract.

It freezes, per source:
- lane of entry
- source type
- support status
- doctrine role
- raw input form
- emitted canonical artifact families
- provenance requirements
- stable source-ID rule
- conflict partners
- per-source v1 done definition

Use this registry together with:
- `reporting/docs/v1_source_scope.md`
- `reporting/docs/canonical_health_schema_v1.md`
- `reporting/docs/source_adapter_contract_v1.md`

## Support status meanings

- `proof_complete`: supported with real repo-grounded proof on the live tree and current operator-facing documentation
- `prototype`: a live bounded implementation or proof surface exists on the tree, but maturity remains partial, mock-backed, fixture-backed, or otherwise explicitly non-flagship
- `planned`: intentionally named in the contract, but implementation has not started yet

## Current proof versus frozen target flagship

The current public proof path is still the broader CLI-first lineage:

`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`

The approved target flagship doctrine for later slices remains:

`Garmin passive pull -> typed manual readiness intake -> deterministic normalization/bundle/context -> bounded recommendation -> bounded writeback`

The typed manual readiness intake half of that target is now a live proof-bearing human-input surface on the tree, but this registry still does **not** claim that the full target flagship loop is already complete.

This registry therefore names both current-proof broader manual surfaces and the live typed-manual-readiness flagship-adjacent surface without claiming that every later flagship dependency is already fully implemented.

## Registry

| Source | Entry lane | Source type | Support status | Doctrine role | Raw input form | Emitted canonical artifact families | Provenance requirements | Stable source-ID rule | Conflict partners | Per-source v1 done definition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Garmin | `pull` | `wearable` | `proof_complete` | `flagship_target` | offline export zip, derived CSV/manifest runtime files | `source_record`, `provenance_record`, `sleep_daily`, `readiness_daily`, `training_session`, `daily_health_snapshot` | every normalized output must retain source name `garmin`, raw receipt reference, derivation method, and source record linkage | `garmin:<export_batch_or_manifest>:<native_record_type>:<native_record_id_or_date>` | Strava, typed manual readiness / subjective recovery inputs | done when raw Garmin export receipt is documented, canonical outputs are named, provenance is attached to every normalized record, overlap behavior with Strava is declared, and proof artifacts show deterministic import-to-normalization behavior |
| typed manual readiness / subjective recovery inputs | `merge_human_inputs` | `manual` | `proof_complete` | `flagship_target` | typed form entry, bounded manual form payload, or equivalent structured manual artifact | `source_record`, `provenance_record`, `subjective_daily_input`, `readiness_daily`, `daily_health_snapshot` | every normalized output must retain human-input artifact reference, derivation method, confidence, effective date, and explicit conflict status | `subjective:<source_artifact>:day:<date>` | Garmin, Oura, voice-note / broader manual human inputs | done when the typed/manual day-input path is documented, `subjective_daily_input` and any derived readiness emission are defined, provenance/confidence/conflict are attached, and proof artifacts show deterministic day-level reconstruction |
| voice-note / broader manual human inputs | `merge_human_inputs` | `voice_note` and `manual` | `prototype` | `current_proof_broader_manual_surface` | voice-note payloads, transcripts, manual log entries, uploaded notes | `source_record`, `provenance_record`, `subjective_daily_input`, `supplement_intake`, `lab_result`, `gym_set_record`, `training_session`, `nutrition_daily`, `daily_health_snapshot` | every normalized output must retain originating artifact ID, derivation method, confidence, and supporting refs | `human_input:<artifact_id>:<derived_record_kind>:<effective_date_or_local_key>` | Cronometer, supplements, bloodwork, resistance training, typed manual readiness / subjective recovery inputs | done when the originating human-input artifact is retained, every derived normalized record carries provenance and confidence, lane ownership stays inside `merge_human_inputs` until deterministic normalization in `clean`, proof artifacts show bounded artifact-to-output reconstruction, and current proof-complete lane presence is treated as narrower than full family coverage |
| Cronometer | `pull` | `imported_food_pipeline` | `prototype` | `bridge_reference` | export CSV receipts and bounded machine-readable nutrition logs | `source_record`, `provenance_record`, `nutrition_daily`, `supplement_intake`, `daily_health_snapshot` | every normalized output must retain source name `cronometer`, raw receipt reference, derivation method, date-level coverage statement, and supplement provenance back to the day receipt plus stable intake subkey | `nutrition:cronometer:day:<date>` and supplement/intake subkeys derived from the same receipt family | supplements, voice-note / broader manual human inputs | done when a daily nutrition receipt path is documented, bridge/reference `nutrition_daily` and `supplement_intake` emission is defined, provenance is attached, coexistence behavior is declared, and proof artifacts cover deterministic day rebuilds plus stable supplement replay IDs without turning Cronometer into a flagship gate |
| supplements | `merge_human_inputs` initially | `manual` | `prototype` | `bridge_reference` | manual entry, voice-note extraction, or later machine-readable import | `source_record`, `provenance_record`, `supplement_intake`, `daily_health_snapshot` | every normalized output must retain human-input artifact reference, derivation method, confidence, date/time as available, and explicit overlap provenance when Cronometer also describes the same substance/date | `supplement:<source_artifact_or_import>:<intake_timestamp_or_date>:<substance_key>` | Cronometer, voice-note / broader manual human inputs | done when the manual-first fallback/backfill intake path is documented, `supplement_intake` emission is defined, provenance and confidence are attached, and proof artifacts show bounded intake reconstruction from human inputs without silently merging or overriding Cronometer-derived records |
| bloodwork | `merge_human_inputs` initially | `manual` | `planned` | `bridge_reference` | manual entry, uploaded report, or later lab-system import | `source_record`, `provenance_record`, `lab_result`, `daily_health_snapshot` | every normalized output must retain artifact/report reference, derivation method, confidence, unit, and collection timestamp when known | `bloodwork:<source_artifact_or_lab>:<collection_date>:<panel_or_marker_key>` | voice-note / broader manual human inputs | done when manual-first report entry is documented, `lab_result` emission is defined, provenance is attached, units and timestamps are preserved, and proof artifacts show bounded report-to-result normalization |
| resistance training | `merge_human_inputs` first, future `pull` adapters allowed | `gym_domain` | `prototype` | `manual_first_non_flagship_connectors` | manual structured gym logs first, with optional later connector receipts as fallback or coexistence inputs | `source_record`, `provenance_record`, `training_session`, `exercise_catalog`, `exercise_alias`, `gym_set_record`, `program_block`, `daily_health_snapshot` | every normalized output must retain source artifact reference, derivation method, confidence, and stable workout/exercise/set linkage | `resistance_training:<source_or_fallback_artifact>:session:<session_key>` and stable catalog/set/program subkeys derived from canonical mapping | future gym sources, voice-note / broader manual human inputs | done when manual structured session and set intake are documented, canonical gym-domain emission is defined, provenance/session linkage is attached, and future connector mapping preserves the same Health Lab-owned objects rather than becoming the flagship source of truth |
| wger | `pull` | `resistance_training_platform` | `prototype` | `exploratory_non_flagship_connector` | API pull, export, or self-hosted database-backed receipts through the bounded adapter contract and mock-backed proof bundle | `source_record`, `provenance_record`, `training_session`, `exercise_catalog`, `exercise_alias`, `gym_set_record`, `program_block`, `daily_health_snapshot` | every normalized output must retain source name `wger`, raw receipt reference, derivation method, source record linkage, and stable workout/exercise/set linkage | `wger:<account_or_instance>:workout:<native_workout_id>` plus stable catalog/set subkeys derived from source receipts | resistance training, future gym sources, voice-note / broader manual human inputs | done when the bounded receipt path is documented, Health Lab canonical gym-domain objects are named, provenance/source-ID rules are frozen, proof artifacts show deterministic rebuilds from the same source receipts, the current mock-backed proof boundary is stated plainly, and the connector remains explicitly non-flagship for this doctrine interval |
| Strava | `pull` | `wearable` | `planned` | `bridge_reference` | API pull or exported activity files | `source_record`, `provenance_record`, `training_session`, `daily_health_snapshot` | every normalized output must retain source name `strava`, raw receipt reference, derivation method, and source record linkage | `strava:<athlete_or_account>:activity:<native_activity_id>` | Garmin | done when raw activity receipt contract is documented, canonical outputs are named, provenance/source-ID rule is frozen, Garmin overlap behavior is declared, and proof artifacts cover idempotent repeated import behavior |
| Oura | `pull` | `wearable` | `planned` | `bridge_reference` | API pull or exported sleep/readiness/activity files | `source_record`, `provenance_record`, `sleep_daily`, `readiness_daily`, `training_session`, `daily_health_snapshot` | every normalized output must retain source name `oura`, raw receipt reference, derivation method, and source record linkage | `oura:<account>:<native_record_type>:<native_record_id_or_date>` | Garmin, Strava, typed manual readiness / subjective recovery inputs | done when sleep/readiness/training receipt paths are documented, canonical outputs are named, provenance/source-ID rule is frozen, conflict partners are declared, and proof artifacts cover deterministic rebuilds from the same raw receipt |

## Registry notes

### Lane ownership

- `voice-note / broader manual human inputs` is marked `prototype` overall because the broader derived-record family is not fully proved yet, even though the lane itself already has real proof-bearing surfaces in the repo.
- `typed manual readiness / subjective recovery inputs` is the frozen human-input half of the target flagship doctrine and now has live repo-grounded proof, even though exact later field extensions and writeback details remain separate contract work.
- `resistance training` is now marked `prototype` because the manual-first session/set path, canonical `training_session` plus `gym_exercise_set` emission, and daily snapshot gym rollups are live on the tree, but the broader exercise-model family is not yet surfaced honestly enough to call `proof_complete`.
- `wger` remains the bounded exploratory connector surface retained on the tree. It does not change the manual-first flagship doctrine.
- A source may have a future secondary acquisition path, but its v1 primary entry lane is the lane frozen above.
- `clean` is not an entry lane. It is the normalization lane after source entry.

### Provenance minimum

Every source in v1 must support:
- a stable `source_record_id`
- a traceable raw or human-input receipt reference
- an explicit derivation method
- explicit conflict status on normalized outputs

### Supplements coexistence rule

Cronometer is the preferred v1 machine-readable source for `supplement_intake`, but that does not make it a flagship-completion dependency.

V1 rules:
- if a supplement intake is present in Cronometer receipt data, that Cronometer-derived intake is the primary `pull` representation for that fact
- manual supplements remain valid fallback and backfill inputs through `merge_human_inputs` when Cronometer is absent, incomplete, late, intentionally unused, or missing needed detail
- a manual supplement record and a Cronometer supplement record must not silently merge into one canonical fact and manual input must not silently override Cronometer
- deterministic duplicate resolution is allowed only when substance identity, effective date, and available time/dose anchors match closely enough to justify one retained primary record, the non-retained provenance path must then be marked `superseded`
- when those anchors are missing or ambiguous, the records must remain visible with explicit `coexists_conflicted` status rather than inferred collapse
- manual and Cronometer supplement records must retain distinct source identities unless deterministic duplicate resolution has already been applied

### Garmin and Strava conflict rule

Garmin and Strava are explicit conflict partners for `training_session`.

V1 rule:
- if two source records clearly describe the same real-world session, the system must not count both as independent training sessions downstream
- if deterministic resolution is possible, one normalized session may supersede the duplicate while preserving both provenance chains
- if deterministic resolution is not possible, the normalized output must carry explicit conflict state rather than silently duplicate or collapse the records

### Resistance-training note

Resistance training is in v1, but the deeper exercise-model spec is still partially deferred.

That does not remove the v1 requirement to emit stable `training_session`, `exercise_catalog`, `exercise_alias`, `gym_set_record`, and `program_block` artifacts with provenance.

For this doctrine interval:
- manual structured Health Lab logs are the source-of-truth path
- future external gym connectors must converge into the same canonical objects
- those external connectors remain non-flagship until separately proved and approved
