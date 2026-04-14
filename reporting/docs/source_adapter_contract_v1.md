# source adapter contract v1

This document freezes the shared v1 adapter contract for source work.

It defines how source adapters are allowed to acquire, identify, normalize, and prove data without changing the canonical bucket model.

This is a cross-source contract. It does not implement any source-specific adapter.

## Why this doc exists

The source scope, source registry, and canonical schema are not enough on their own.

The repo also needs one frozen contract for:
- adapter input assumptions
- raw receipt expectations
- idempotency expectations
- time normalization rules
- unit normalization rules
- stable source-ID rules
- provenance requirements
- missingness and confidence handling
- conflict-status handling
- proof artifact expectations
- exact `pull` vs `clean` vs `merge_human_inputs` responsibilities

## Current proof versus frozen target flagship

The current public proof path is still the broader CLI-first lineage:

`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`

The approved target flagship doctrine for later slices is:

`Garmin passive pull -> typed manual readiness intake -> deterministic normalization/bundle/context -> bounded recommendation -> bounded writeback`

This contract names many source families. That does not make them all flagship-critical.

For this doctrine interval:
- Garmin plus typed manual readiness is the frozen target flagship path
- Cronometer is a bridge/reference nutrition source, not a flagship-completion dependency
- manual structured gym logs are the source-of-truth path for resistance training
- `wger` is the only retained bounded exploratory non-flagship gym connector prototype

## Lane ownership contract

### `pull`

`pull` owns:
- authentication or local-import handshake where relevant
- acquisition of passive or machine-readable source data
- immutable or inspectable raw receipts
- source-specific extraction into source-local intermediate forms
- source metadata capture such as account, export batch, native record ID, and collection timestamps

`pull` does not own:
- canonical merged health facts
- downstream source-agnostic snapshots
- human-authored note entry

### `clean`

`clean` owns:
- deterministic normalization into canonical artifact families
- field validation
- unit normalization
- time normalization
- conflict expression
- merged day-level snapshot construction

`clean` does not own:
- external acquisition
- human-authored source entry
- speculative interpretation beyond deterministic normalization

### `merge_human_inputs`

`merge_human_inputs` owns:
- voice-note intake
- typed manual readiness intake
- manual logs
- manual subjective entries
- manual resistance-training entries
- manual context notes
- manual-first supplements and bloodwork entry surfaces in v1

`merge_human_inputs` does not own:
- passive third-party acquisition
- canonical downstream merged facts beyond its own human-input source artifacts and payloads before normalization in `clean`

These boundaries are mandatory and non-overlapping.

## Adapter input assumptions

A v1 source adapter may accept one of these raw input classes:
- third-party API responses
- offline export archives
- machine-readable files such as JSON or CSV
- human-input artifacts created inside `merge_human_inputs`

Every adapter must document:
- accepted raw input forms
- minimum required metadata
- rejection conditions for incomplete or malformed input
- whether the adapter is manual-first, pull-first, or supports both paths across time

## Raw receipt expectations

Every adapter path must preserve an inspectable raw receipt reference.

Minimum receipt requirements:
- `raw_location`
- `raw_format`
- `ingested_at`
- source name
- enough batch, artifact, or account metadata to reconstruct where the data came from

If the source is human-authored, the raw receipt may be a voice-note artifact, typed manual readiness artifact, transcript ref, uploaded report, or manual-entry artifact rather than an external export.

## Idempotency contract

Adapters must be idempotent with respect to the same raw receipt.

V1 rule:
- reprocessing the same raw receipt must reproduce the same `source_record_id` values and canonical artifact primary IDs, unless parser versioning intentionally changes them and that version shift is recorded
- repeated imports must not silently create duplicate canonical outputs for the same source record
- if an updated raw receipt supersedes an earlier one, the provenance chain must make that visible

## Time normalization rules

Adapters must normalize time explicitly.

V1 rules:
- preserve source-local timestamps when available
- record date-only artifacts with an explicit `date`
- if a timezone is known, preserve it or convert deterministically to the repo’s normalized representation
- if timezone is unknown, do not fabricate certainty; preserve the uncertainty in provenance or notes
- session overlap detection for Garmin and Strava must operate on normalized comparable time windows where available

## Unit normalization rules

Adapters must normalize units before emitting canonical artifacts.

V1 rules:
- canonical numeric fields must use one declared unit per field family
- if source units differ, conversion must happen in `clean`
- original unit context should remain inspectable through source records or provenance when relevant
- if a unit cannot be determined reliably, the normalized artifact must not fabricate a converted value

Examples:
- duration in seconds
- distance in meters
- load in kilograms
- nutrition energy in kcal

## Stable source-ID rules

Stable source IDs are mandatory.

V1 rules:
- every source family must define a reproducible `source_record_id`
- the ID must be stable across repeated processing of the same raw receipt
- the ID must include enough source-local identity to prevent collisions across sources
- one real-world source record may produce multiple canonical artifacts, all linked back to the same `source_record_id`

Registry-aligned examples:
- Garmin: `garmin:<export_batch_or_manifest>:<native_record_type>:<native_record_id_or_date>`
- Strava: `strava:<athlete_or_account>:activity:<native_activity_id>`
- Oura: `oura:<account>:<native_record_type>:<native_record_id_or_date>`
- human input: `human_input:<artifact_id>:<derived_record_kind>:<effective_date_or_local_key>`
- manual subjective recovery: `subjective:<source_artifact>:day:<date>`

## Provenance requirements

Every normalized artifact must carry provenance.

Minimum provenance contract:
- one primary `provenance_record_id`
- `derivation_method`
- supporting refs to the raw receipt or human-input artifact
- parser version when relevant
- explicit `conflict_status`

For manual subjective recovery v1, the primary provenance ID is derived as `provenance:<source_record_id>` and must remain stable on replay of the same source artifact and day.

Normalized artifacts without provenance are invalid in v1.

## Missingness and confidence handling

Adapters must treat missingness and confidence as explicit data, not hidden implementation detail.

### Missingness

Use the v1 missingness states:
- `present`
- `missing_not_provided`
- `missing_not_available_from_source`
- `missing_parse_failed`
- `missing_conflict_unresolved`

Rules:
- missing source fields must not be silently coerced to plausible values
- when a source never provides a field, mark it as not available rather than missing due to user behavior
- unresolved cross-source conflicts may surface as `missing_conflict_unresolved` where the canonical field cannot be stated safely

### Confidence

Use the v1 confidence labels:
- `high`
- `medium`
- `low`

Rules:
- passive machine-native fields are usually higher confidence than voice-extracted free text, but confidence is field- and context-dependent
- confidence should be preserved when human-input extraction creates normalized artifacts
- low-confidence normalization must still remain inspectable via provenance

## Conflict-status handling

Use the v1 conflict statuses:
- `none`
- `superseded`
- `coexists_conflicted`

Rules:
- `none` means no material conflict is known
- `superseded` means another record is the retained primary representation of the same real-world fact, but the superseded record remains traceable
- `coexists_conflicted` means multiple plausible records remain in tension and v1 preserves the ambiguity explicitly

### Supplements coexistence contract

This conflict rule is frozen for v1.

If Cronometer and manual supplements both describe what appears to be the same real-world supplement intake:
- Cronometer is the preferred machine-readable source and remains the default retained `pull` representation when it has trustworthy supplement detail
- manual supplements remain valid fallback and backfill inputs through `merge_human_inputs` when Cronometer is absent, incomplete, late, intentionally unused, or lacks needed detail
- v1 must not silently merge a Cronometer supplement record and a manual supplement record into one canonical fact
- v1 must not silently let manual supplement input override a Cronometer-derived intake
- deterministic duplicate resolution is allowed only when substance identity, effective date, and available time and dose anchors match closely enough to justify treating the pair as the same intake
- when deterministic duplicate resolution is applied, one retained primary canonical intake may remain `none` while the duplicate provenance path is marked `superseded`
- when the overlap cannot be resolved safely, the normalized supplement output must remain explicit about `coexists_conflicted`
- replay of the same Cronometer receipt or manual artifact must preserve the same source identities; cross-source overlap must never collapse source IDs by accident

That preference does not make Cronometer a flagship-completion dependency.

Recommended stable-ID patterns for this slice:
- Cronometer day anchor: `nutrition:cronometer:day:<date>`
- Cronometer supplement intake subkey: derived from the same day receipt family plus stable intake-local anchors
- manual supplement anchor: `supplement:<source_artifact_or_import>:<intake_timestamp_or_date>:<substance_key>`

### Garmin vs Strava overlap contract

This conflict rule is frozen for v1.

If Garmin and Strava both describe what appears to be the same real-world session:
- v1 must not silently count both as independent sessions downstream
- deterministic overlap resolution may mark one record as primary and the other as `superseded`
- if the overlap cannot be resolved safely, the normalized session output must remain explicit about `coexists_conflicted`
- downstream retrieval should consume canonical artifacts and provenance, not source-specific guesswork

## Per-source proof artifact expectations

Every source adapter path in v1 must have inspectable proof artifacts.

Minimum proof expectations:
- example raw receipt or bounded fixture reference
- expected emitted canonical artifact families
- proof of stable `source_record_id` behavior on repeated processing
- proof that provenance is attached
- proof of any declared conflict handling where overlap exists

For the supplements coexistence slice, the minimum inspectable proof bundle is:
- one Cronometer-only supplement example
- one manual-only fallback example
- one overlap example resolved explicitly as `superseded` or `coexists_conflicted`
- expected canonical `supplement_intake` outputs with `source_name`, `source_record_id`, `provenance_record_id`, and `conflict_status`
- one replay note showing that repeated processing preserves the same source IDs

Proof may be staged by source status:
- `proof_complete`: proof artifacts already exist and are reviewable
- `prototype`: bounded proof exists or is actively expected next
- `planned`: proof artifact path is reserved by contract but not yet implemented

## Output contract from adapters into canonical schema

No adapter may bypass the canonical schema contract.

V1 rule:
- source-specific inputs may vary freely
- canonical outputs must land only in the frozen artifact families defined in `canonical_health_schema_v1.md`
- source-specific novelty belongs in source records, provenance notes, or later bounded schema revisions, not ad hoc extra downstream artifact families

## Resistance-training contract note

Resistance training is in v1.

Adapter-level freeze:
- manual structured logging through `merge_human_inputs` is the required source-of-truth initial lane
- normalized outputs must be `training_session`, `gym_set_record`, `exercise_catalog`, `exercise_alias`, and `program_block`
- future imported lifting sources must converge into the same canonical outputs
- those external gym connectors remain non-flagship or exploratory in this doctrine interval
- deeper exercise taxonomy and progression logic are deferred to a later bounded spec

## Out-of-scope confirmation

This contract does not:
- implement a Strava adapter
- implement an Oura adapter
- redesign retrieval around source names
- require a new canonical bucket
- require a full resistance-training deep model in the same slice
- require Cronometer or any external gym connector for flagship completion
