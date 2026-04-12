# Health Lab schema and ingestion plan

Date: 2026-04-09
Status: first unifying draft

## Purpose

Move the project from a Garmin-shaped pipeline into a broader Health Lab that can unify:
- sleep
- running
- gym
- food
- recovery/readiness

Garmin becomes one source adapter, not the product identity.

## Product direction

Target daily outcome:
- one daily health view in ClawSuite
- one page that shows sleep, training, eating, and recovery together
- enough structure to support daily use, not just analysis notebooks

## Canonical domain model

### 1) daily_health_snapshot
Primary key:
- `date`

Purpose:
- one row per day for the main ClawSuite health page

Candidate fields:
- `date`
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

### 2) sleep_daily
Primary key:
- `date`

Purpose:
- preserve sleep-specific detail beyond the main daily snapshot

Candidate fields:
- `date`
- `source`
- `total_sleep_sec`
- `deep_sleep_sec`
- `light_sleep_sec`
- `rem_sleep_sec`
- `awake_sleep_sec`
- `sleep_score`
- `avg_sleep_respiration`
- `awake_count`
- `restless_moments`

### 3) training_session
Primary key:
- `session_id`

Purpose:
- unified session layer for running and gym

Candidate fields:
- `session_id`
- `date`
- `session_type` (`run` | `gym` | `other`)
- `source` (`garmin` | `manual_gym_log` | `other`)
- `start_time_local`
- `duration_sec`
- `session_title`
- `rpe_1_10`
- `energy_pre_1_5`
- `energy_post_1_5`
- `notes`

Running-specific optional fields:
- `distance_m`
- `avg_hr`
- `max_hr`
- `avg_pace_sec_per_km`
- `elevation_gain_m`
- `training_effect_aerobic`

Gym-specific optional fields:
- `lift_focus`
- `exercise_count`
- `total_sets`
- `total_reps`
- `total_load_kg`

### 4) gym_exercise_set
Primary key:
- `set_id`

Purpose:
- structured gym logging without waiting for a third-party integration

Candidate fields:
- `set_id`
- `session_id`
- `date`
- `exercise_name`
- `exercise_group`
- `set_number`
- `reps`
- `weight_kg`
- `rir`
- `rpe`
- `completed_bool`
- `note`

### 5) nutrition_daily
Primary key:
- `date`

Purpose:
- daily food summary for the ClawSuite page and health analytics

Candidate fields:
- `date`
- `calories_kcal`
- `protein_g`
- `carbs_g`
- `fat_g`
- `fiber_g`
- `meal_count`
- `food_log_completeness`
- `top_meals_summary`

### 6) readiness_daily
Primary key:
- `date`

Purpose:
- separate data-backed recovery/readiness logic from generic advice

Candidate fields:
- `date`
- `source`
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

## First source mapping

### Garmin -> Health Lab
Use Garmin for:
- sleep_daily
- readiness_daily
- running training_session rows
- part of daily_health_snapshot

Current known Garmin-safe fields:
- sleep duration and stages
- sleep score
- resting HR and daily HR summaries
- readiness / recovery snapshots
- acute/chronic load
- running activity summaries
- hydration as optional enrichment

### Food pipeline -> Health Lab
Use existing Health Lab food system for:
- nutrition_daily
- daily_health_snapshot macro totals

### Manual gym log -> Health Lab
Use a new structured manual logging path for:
- gym training_session rows
- gym_exercise_set rows
- daily_health_snapshot gym rollups

Reason:
- fastest path to daily usefulness
- Garmin is weak for gym data
- keeps the system provider-agnostic

## First manual gym-log format

Recommended first input shape: simple JSON or SQLite-backed structured rows, with a human-friendly form later.

### session header
- `session_id`
- `date`
- `start_time_local`
- `session_title`
- `lift_focus`
- `duration_sec`
- `rpe_1_10`
- `energy_pre_1_5`
- `energy_post_1_5`
- `notes`

### set rows
- `exercise_name`
- `exercise_group`
- `set_number`
- `reps`
- `weight_kg`
- `rir`
- `rpe`
- `completed_bool`
- `note`

### first practical logging rule
For v1, logging only these is enough:
- exercise name
- set number
- reps
- weight

Everything else is optional.

## Daily page target for ClawSuite

The first useful ClawSuite health page should show:
- last night sleep summary
- today readiness / recovery summary
- recent running load and latest run
- latest gym session and weekly gym volume
- today nutrition totals or whether food is logged
- one short data-backed observation
- one short generic suggestion, clearly labeled as generic

## Build order

1. formalize Health Lab as the active project direction
2. add the manual gym-log schema and storage surface
3. map Garmin export/live fields into the shared schema
4. map food outputs into nutrition_daily
5. produce one combined daily_health_snapshot
6. render the first ClawSuite health page from that snapshot

## Immediate next build target

Create the first bounded Health Lab integration artifact:
- one dated schema-backed daily snapshot generated from:
  - Garmin export-derived data
  - current food logging outputs where available
  - placeholder/manual gym log input

That gives a clean proof path into ClawSuite without waiting for every ingestion source to be perfect.
