# source registry v1

This document is the canonical v1 source registry for the Health Lab platform contract.

It freezes, per source:
- lane of entry
- source type
- support status
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

- `proof_complete`: supported with real repo-grounded proof and current operator-facing documentation
- `prototype`: in v1 contract scope, but implementation proof is still partial or pending
- `planned`: intentionally named in the contract, but implementation has not started yet

## Registry

| Source | Entry lane | Source type | Support status | Raw input form | Emitted canonical artifact families | Provenance requirements | Stable source-ID rule | Conflict partners | Per-source v1 done definition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Garmin | `pull` | `wearable` | `proof_complete` | offline export zip, derived CSV/manifest runtime files | `source_record`, `provenance_record`, `sleep_daily`, `readiness_daily`, `training_session`, `daily_health_snapshot` | every normalized output must retain source name `garmin`, raw receipt reference, derivation method, and source record linkage | `garmin:<export_batch_or_manifest>:<native_record_type>:<native_record_id_or_date>` | Strava, manual subjective recovery inputs | done when raw Garmin export receipt is documented, canonical outputs are named, provenance is attached to every normalized record, overlap behavior with Strava is declared, and proof artifacts show deterministic import-to-normalization behavior |
| Strava | `pull` | `wearable` | `planned` | API pull or exported activity files | `source_record`, `provenance_record`, `training_session`, `daily_health_snapshot` | every normalized output must retain source name `strava`, raw receipt reference, derivation method, and source record linkage | `strava:<athlete_or_account>:activity:<native_activity_id>` | Garmin | done when raw activity receipt contract is documented, canonical outputs are named, provenance/source-ID rule is frozen, Garmin overlap behavior is declared, and proof artifacts cover idempotent repeated import behavior |
| nutrition system / imported food pipeline | `pull` | `imported_food_pipeline` | `prototype` | imported nutrition database rows, files, or equivalent machine-readable food logs | `source_record`, `provenance_record`, `nutrition_daily`, `daily_health_snapshot` | every normalized output must retain source name, raw receipt reference, derivation method, and date-level coverage statement | `nutrition:<system_name_or_dataset>:day:<date>` | voice-note / manual human inputs | done when a daily nutrition receipt path is documented, `nutrition_daily` emission is defined, provenance is attached, manual-note coexistence behavior is declared, and proof artifacts cover deterministic day rebuilds |
| supplements | `merge_human_inputs` initially | `manual` | `prototype` | manual entry, voice-note extraction, or later machine-readable import | `source_record`, `provenance_record`, `supplement_intake`, `daily_health_snapshot` | every normalized output must retain human-input artifact reference, derivation method, confidence, and date/time as available | `supplement:<source_artifact_or_import>:<intake_timestamp_or_date>:<substance_key>` | voice-note / manual human inputs | done when manual-first intake path is documented, `supplement_intake` emission is defined, provenance and confidence are attached, and proof artifacts show bounded intake reconstruction from human inputs |
| bloodwork | `merge_human_inputs` initially | `manual` | `planned` | manual entry, uploaded report, or later lab-system import | `source_record`, `provenance_record`, `lab_result`, `daily_health_snapshot` | every normalized output must retain artifact/report reference, derivation method, confidence, unit, and collection timestamp when known | `bloodwork:<source_artifact_or_lab>:<collection_date>:<panel_or_marker_key>` | voice-note / manual human inputs | done when manual-first report entry is documented, `lab_result` emission is defined, provenance is attached, units and timestamps are preserved, and proof artifacts show bounded report-to-result normalization |
| Oura | `pull` | `wearable` | `planned` | API pull or exported sleep/readiness/activity files | `source_record`, `provenance_record`, `sleep_daily`, `readiness_daily`, `training_session`, `daily_health_snapshot` | every normalized output must retain source name `oura`, raw receipt reference, derivation method, and source record linkage | `oura:<account>:<native_record_type>:<native_record_id_or_date>` | Garmin, Strava | done when sleep/readiness/training receipt paths are documented, canonical outputs are named, provenance/source-ID rule is frozen, conflict partners are declared, and proof artifacts cover deterministic rebuilds from the same raw receipt |
| resistance training | `merge_human_inputs` required initially | `manual` | `prototype` | manual gym logs, voice-note extraction, future imported lifting data | `source_record`, `provenance_record`, `training_session`, `gym_exercise_set`, `daily_health_snapshot` | every normalized output must retain source artifact reference, derivation method, confidence, and stable session/set linkage | `resistance_training:<source_artifact_or_import>:session:<session_key>` and `resistance_training:<source_artifact_or_import>:set:<session_key>:<set_index_or_native_set_id>` | future imported lifting adapters, voice-note / manual human inputs | done when manual-first session and set intake are documented, `training_session` and `gym_exercise_set` emission is defined, provenance/session linkage is attached, and proof artifacts show stable rebuild of the same session and set identities |
| manual subjective recovery inputs | `merge_human_inputs` | `manual` | `prototype` | manual form entry or voice-note extraction | `source_record`, `provenance_record`, `subjective_daily_input`, `daily_health_snapshot` | every normalized output must retain human-input artifact reference, derivation method, confidence, and effective date | `subjective:<source_artifact>:day:<date>` | Garmin, Oura, voice-note / manual human inputs | done when daily subjective entry path is documented, `subjective_daily_input` emission is defined, provenance/confidence are attached, and proof artifacts show deterministic day-level reconstruction |
| voice-note / manual human inputs | `merge_human_inputs` | `voice_note` and `manual` | `prototype` | voice-note payloads, transcripts, manual log entries, uploaded notes | `source_record`, `provenance_record`, `subjective_daily_input`, `supplement_intake`, `lab_result`, `gym_exercise_set`, `training_session`, `nutrition_daily`, `daily_health_snapshot` | every normalized output must retain originating artifact ID, derivation method, confidence, and supporting refs | `human_input:<artifact_id>:<derived_record_kind>:<effective_date_or_local_key>` | nutrition system / imported food pipeline, supplements, bloodwork, resistance training, manual subjective recovery inputs | done when the originating human-input artifact is retained, every derived normalized record carries provenance and confidence, lane ownership stays inside `merge_human_inputs` until deterministic normalization in `clean`, proof artifacts show bounded artifact-to-output reconstruction, and current proof-complete lane presence is treated as narrower than full family coverage |

## Registry notes

### Lane ownership

- `voice-note / manual human inputs` is marked `prototype` overall because the broader derived-record family is not fully proved yet, even though the lane itself already has real proof-bearing surfaces in the repo.

- A source may have a future secondary acquisition path, but its v1 primary entry lane is the lane frozen above.
- `clean` is not an entry lane. It is the normalization lane after source entry.

### Provenance minimum

Every source in v1 must support:
- a stable `source_record_id`
- a traceable raw or human-input receipt reference
- an explicit derivation method
- explicit conflict status on normalized outputs

### Garmin and Strava conflict rule

Garmin and Strava are explicit conflict partners for `training_session`.

V1 rule:
- if two source records clearly describe the same real-world session, the system must not count both as independent training sessions downstream
- if deterministic resolution is possible, one normalized session may supersede the duplicate while preserving both provenance chains
- if deterministic resolution is not possible, the normalized output must carry explicit conflict state rather than silently duplicate or collapse the records

### Resistance-training note

Resistance training is in v1, but the deeper exercise-model spec is deferred.

That deferral does not remove the v1 requirement to emit stable `training_session` and `gym_exercise_set` artifacts with provenance.
