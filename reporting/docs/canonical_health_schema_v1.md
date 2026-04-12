# canonical health schema v1

This document freezes the normalized v1 artifact contract consumed downstream.

It aligns the platform contract with current repo-grounded schema surfaces, especially:
- `clean/health_model/schemas.py`
- `clean/health_model/shared_input_backbone.py`
- `merge_human_inputs/manual_logs/manual_logging.py`

This is a docs/spec freeze, not a claim that every field below is already implemented everywhere in code.

## Schema goals

The v1 schema must:
- preserve the canonical eight-bucket model
- give downstream retrieval source-agnostic normalized artifacts
- require traceable provenance for every normalized output
- keep lane boundaries explicit between `pull`, `clean`, and `merge_human_inputs`
- prevent cross-source schema drift before source-specific fanout

## Lane boundary confirmation

- `pull` emits raw receipts, source-local extracted records, and source metadata. It does not own canonical merged health facts.
- `clean` emits canonical normalized artifact families and conflict expression.
- `merge_human_inputs` emits human-authored source artifacts and manual-entry payloads that later normalize into the same canonical artifact families.

These responsibilities are non-overlapping.

## Shared enumerations grounded in current repo code

The following current enums are adopted as v1 contract concepts from `clean/health_model/shared_input_backbone.py`.

### `source_type`
- `wearable`
- `voice_note`
- `manual`
- `imported_food_pipeline`

### `capture_mode`
- `passive`
- `self_reported`
- `derived`

### `missingness_state`
- `present`
- `missing_not_provided`
- `missing_not_available_from_source`
- `missing_parse_failed`
- `missing_conflict_unresolved`

### `confidence_label`
- `high`
- `medium`
- `low`

### `derivation_method`
- `none`
- `voice_extraction`
- `wearable_normalization`
- `manual_form_normalization`
- `food_import_normalization`
- `cross_source_merge`

### `conflict_status`
- `none`
- `superseded`
- `coexists_conflicted`

## Canonical artifact families

The v1 normalized artifact families are:
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

## Common requirements for every normalized artifact

Every normalized artifact in v1 must have:
- `artifact_family`
- stable primary ID
- `effective_date` or event timestamp boundary
- `source_name`
- `source_record_id`
- `provenance_record_id`
- explicit `conflict_status`
- enough timestamps or date scope to support deterministic rebuilds

No normalized artifact may exist without traceable source linkage.

## Canonical entity definitions

### 1. `source_record`

Purpose:
- identify one source-originating record or receipt anchor from which normalized artifacts are derived

Required fields:
- `source_record_id`
- `source_name`
- `source_type`
- `entry_lane`
- `raw_location`
- `raw_format`
- `collected_at` or `effective_date`
- `ingested_at`
- `hash_or_version` when available
- `native_record_type`
- `native_record_id` when available

Notes:
- this family is the stable source-link anchor across all others
- it is conceptually aligned with `ArtifactModel` in `shared_input_backbone.py`

### 2. `provenance_record`

Purpose:
- describe how a normalized artifact was derived and what supports it

Required fields:
- `provenance_record_id`
- `source_record_id`
- `derivation_method`
- `supporting_refs`
- `parser_version` when available
- `conflict_status`

Notes:
- conceptually aligned with `ProvenanceModel` in `shared_input_backbone.py`
- every normalized artifact must point to exactly one primary provenance record

### 3. `sleep_daily`

Purpose:
- one day-level normalized sleep artifact

Required fields:
- `sleep_daily_id`
- `date`
- `source_name`
- `source_record_id`
- `provenance_record_id`
- `conflict_status`

Recommended v1 fields grounded in current `SleepDaily` dataclass:
- `total_sleep_sec`
- `deep_sleep_sec`
- `light_sleep_sec`
- `rem_sleep_sec`
- `awake_sleep_sec`
- `sleep_score`
- `avg_sleep_respiration`
- `awake_count`
- `restless_moments`

### 4. `readiness_daily`

Purpose:
- one day-level normalized readiness or recovery artifact

Required fields:
- `readiness_daily_id`
- `date`
- `source_name`
- `source_record_id`
- `provenance_record_id`
- `conflict_status`

Recommended v1 fields grounded in current `ReadinessDaily` dataclass:
- `readiness_score`
- `readiness_label`
- `sleep_factor`
- `hrv_factor`
- `stress_factor`
- `training_load_factor`
- `recovery_hours_remaining`
- `data_backed_observation`
- `generic_guidance`
- `caveat`

### 5. `training_session`

Purpose:
- one normalized session-level training artifact across running and resistance training

Required fields:
- `training_session_id`
- `date`
- `session_type`
- `source_name`
- `source_record_id`
- `provenance_record_id`
- `conflict_status`

Recommended v1 fields grounded in current `TrainingSession` dataclass:
- `start_time_local`
- `duration_sec`
- `session_title`
- `distance_m`
- `avg_hr`
- `max_hr`
- `avg_pace_sec_per_km`
- `elevation_gain_m`
- `training_effect_aerobic`
- `rpe_1_10`
- `energy_pre_1_5`
- `energy_post_1_5`
- `notes`
- `lift_focus`
- `exercise_count`
- `total_sets`
- `total_reps`
- `total_load_kg`

Contract rule:
- Garmin, Strava, Oura, manual resistance logs, and future lifting imports must all converge on this artifact family when they describe a session.

### 6. `exercise_catalog`

Purpose:
- one canonical exercise definition artifact owned by Health Lab, not by any single source system

Required fields:
- `exercise_catalog_id`
- `canonical_exercise_name`
- `movement_pattern` when known
- `source_name`
- `source_record_id`
- `provenance_record_id`
- `conflict_status`

Recommended v1 fields:
- `equipment`
- `primary_muscle_groups`
- `secondary_muscle_groups`
- `unilateral_bool`
- `loaded_pattern`

### 7. `exercise_alias`

Purpose:
- one source-specific or colloquial exercise naming alias that resolves to a canonical exercise definition

Required fields:
- `exercise_alias_id`
- `exercise_catalog_id`
- `alias_name`
- `source_name`
- `source_record_id`
- `provenance_record_id`
- `conflict_status`

Recommended v1 fields:
- `source_native_exercise_id`
- `normalization_rule`
- `notes`

### 8. `gym_set_record`

Purpose:
- one normalized resistance-training set artifact

Required fields:
- `gym_set_record_id`
- `training_session_id`
- `date`
- `exercise_catalog_id` or canonical exercise reference
- `source_name`
- `source_record_id`
- `provenance_record_id`
- `conflict_status`

Recommended v1 fields:
- `exercise_alias_id`
- `set_number`
- `reps`
- `weight_kg`
- `rir`
- `rpe`
- `completed_bool`
- `set_type`
- `note`

Contract rule:
- manual and future imported lifting sources must normalize into the same set artifact family.

### 9. `program_block`

Purpose:
- one normalized training-program or block-level artifact that can anchor workout intent, progression context, and adherence tracking

Required fields:
- `program_block_id`
- `source_name`
- `source_record_id`
- `provenance_record_id`
- `conflict_status`
- `start_date` or effective boundary

Recommended v1 fields:
- `block_name`
- `goal`
- `split_type`
- `planned_frequency`
- `adherence_status`

### 10. `nutrition_daily`

Purpose:
- one day-level normalized nutrition artifact

Required fields:
- `nutrition_daily_id`
- `date`
- `source_name`
- `source_record_id`
- `provenance_record_id`
- `conflict_status`

Recommended v1 fields grounded in current `NutritionDaily` dataclass:
- `calories_kcal`
- `protein_g`
- `carbs_g`
- `fat_g`
- `fiber_g`
- `meal_count`
- `food_log_completeness`
- `top_meals_summary`

### 11. `supplement_intake`

Purpose:
- one normalized supplement or medication-style intake event

Required fields:
- `supplement_intake_id`
- `effective_date`
- `source_name`
- `source_record_id`
- `provenance_record_id`
- `conflict_status`
- `substance_name`

Recommended v1 fields:
- `dose_value`
- `dose_unit`
- `taken_at`
- `notes`
- `confidence_label`

### 12. `lab_result`

Purpose:
- one normalized bloodwork or lab-result artifact

Required fields:
- `lab_result_id`
- `effective_date` or `collected_at`
- `source_name`
- `source_record_id`
- `provenance_record_id`
- `conflict_status`
- `marker_name`
- `value`
- `unit`

Recommended v1 fields:
- `panel_name`
- `reference_range`
- `abnormal_flag`
- `sample_type`
- `notes`
- `confidence_label`

### 13. `subjective_daily_input`

Purpose:
- one day-level normalized subjective or self-reported daily artifact

Required fields:
- `subjective_daily_input_id`
- `date`
- `source_name`
- `source_record_id`
- `provenance_record_id`
- `conflict_status`

Recommended v1 fields grounded in `SubjectiveDailyEntryModel`:
- `energy_self_rating`
- `stress_self_rating`
- `mood_self_rating`
- `perceived_sleep_quality`
- `illness_or_soreness_flag`
- `free_text_summary`
- `confidence_label`
- `confidence_score`

Manual subjective recovery v1 stable-ID rule:
- `source_record_id = subjective:<source_artifact>:day:<date>`
- `provenance_record_id = provenance:<source_record_id>`

In this slice, any `perceived_recovery` value remains downstream-only derivation and is not a new canonical source field inside `subjective_daily_input`.

### 14. `daily_health_snapshot`

Purpose:
- one downstream day-level merged snapshot across normalized artifacts

Required fields:
- `daily_health_snapshot_id`
- `date`
- `provenance_record_id`
- `conflict_status`

Recommended v1 fields grounded in current `DailyHealthSnapshot` dataclass:
- `sleep_duration_hours`
- `sleep_score`
- `sleep_awake_count`
- `resting_hr`
- `hrv_status`
- `body_battery_or_readiness`
- `readiness_label`
- `running_sessions_count`
- `running_volume_m`
- `gym_sessions_count`
- `gym_total_sets`
- `gym_total_reps`
- `gym_total_load_kg`
- `food_logged_bool`
- `calories_kcal`
- `protein_g`
- `carbs_g`
- `fat_g`
- `hydration_ml`
- `subjective_energy_1_5`
- `subjective_soreness_1_5`
- `subjective_stress_1_5`
- `overall_day_note`
- `data_backed_fields`
- `generic_fields`
- `source_flags`

Contract rule:
- this artifact is downstream and source-agnostic. It may summarize multiple upstream source records, but it must preserve traceable provenance and conflict expression.

## Source-ID alignment rules

The schema-level source-ID rule is:
- every normalized artifact must carry a stable `source_record_id`
- `source_record_id` must be reproducible from the same raw or human-input receipt
- if one real-world event produces multiple canonical outputs, each output may share the same `source_record_id` while retaining its own artifact-family-specific primary ID
- no normalized artifact may invent an opaque untraceable source key

## Provenance alignment rules

The schema-level provenance rule is:
- every normalized artifact must reference exactly one primary `provenance_record`
- the provenance record must name the derivation method
- the provenance record must include supporting refs sufficient for inspection
- conflict state must be visible through provenance and carried onto the normalized artifact

## Garmin and Strava conflict rule

For overlapping training evidence from Garmin and Strava:
- duplicate real-world sessions must not remain as silent double-counted downstream facts
- if deterministic reconciliation succeeds, one normalized `training_session` may be retained as primary while the duplicate is marked `superseded` in provenance
- if reconciliation remains uncertain, the affected normalized output must be marked `coexists_conflicted`

## Resistance-training v1 boundary

The schema freeze for resistance training is now centered on:
- `training_session` as the session-level normalized output
- `exercise_catalog` as the canonical exercise-definition layer
- `exercise_alias` as the source-to-canonical exercise bridge
- `gym_set_record` as the set-level normalized output
- `program_block` as the bounded programming-context layer
- stable linkage from sets to sessions and exercises
- provenance and confidence preservation across wger, manual fallback, and future imported sources

A deeper metric or programming model can still expand later, but these gym-domain objects are now the v1 center of gravity.
