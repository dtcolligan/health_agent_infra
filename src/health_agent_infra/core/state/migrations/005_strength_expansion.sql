-- Migration 005 — strength domain expansion (Phase 4 step 1).
--
-- Three moves in one migration (analogous to 004 for sleep/stress):
--   1. CREATE TABLE exercise_taxonomy and seed it with the ~80-lift
--      canonical catalogue shipped at
--      src/health_agent_infra/domains/strength/taxonomy_seed.csv.
--      The CSV is the human-editable reference; this migration is the
--      runtime source-of-truth. A test
--      (safety/tests/test_migration_005_taxonomy.py) locks them together
--      so future edits cannot silently diverge.
--   2. Expand accepted_resistance_training_state_daily with:
--        - total_reps                       (INTEGER)
--        - volume_by_muscle_group_json      (TEXT; JSON object keyed by
--                                            muscle_group → kg·reps)
--        - estimated_1rm_json               (TEXT; JSON object keyed by
--                                            exercise_id → Epley 1RM in kg)
--        - unmatched_exercise_tokens_json   (TEXT; JSON array of raw
--                                            exercise_name strings that
--                                            did not resolve against the
--                                            taxonomy — agent surfaces
--                                            these for catalogue
--                                            extension)
--      The pre-existing columns (session_count, total_sets,
--      total_volume_kg_reps, exercises) are preserved verbatim so the
--      minimal Phase 7C.1 projection path keeps working. The expanded
--      strength projector in Phase 4 step 2 will begin populating the
--      new columns.
--   3. Add exercise_id (nullable, FK → exercise_taxonomy.exercise_id)
--      on gym_set. Existing rows keep exercise_id = NULL — taxonomy
--      matching is best-effort at intake time and does not retroactively
--      mutate audit. Reproject can re-resolve historical free-text
--      exercise_name strings, but that path is owned by the projector,
--      not this migration.
--
-- Note on FKs added via ALTER TABLE: SQLite honours the REFERENCES
-- clause for *newly-inserted* rows while PRAGMA foreign_keys=ON; it
-- does NOT retroactively validate pre-existing rows, which is exactly
-- the semantics we want for a best-effort taxonomy match.


-- ============================================================================
-- 1. exercise_taxonomy (new seeded)
-- ============================================================================
-- aliases / secondary_muscle_groups are pipe-delimited strings, not
-- JSON arrays, to keep them trivially greppable from the CLI and the
-- narration skill. The parser in domains/strength handles the split.
--
-- source='seed' for canonical rows loaded by this migration; rows added
-- by `hai intake exercise` carry source='user_manual'.

CREATE TABLE exercise_taxonomy (
    exercise_id                 TEXT    PRIMARY KEY,
    canonical_name              TEXT    NOT NULL UNIQUE,
    aliases                     TEXT,                 -- pipe-delimited
    primary_muscle_group        TEXT    NOT NULL,
    secondary_muscle_groups     TEXT,                 -- pipe-delimited
    category                    TEXT    NOT NULL CHECK (category IN ('compound', 'isolation')),
    equipment                   TEXT    NOT NULL CHECK (equipment IN (
                                    'barbell', 'dumbbell', 'cable',
                                    'bodyweight', 'machine', 'kettlebell'
                                )),
    source                      TEXT    NOT NULL DEFAULT 'seed'
                                   CHECK (source IN ('seed', 'user_manual')),
    created_at                  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_exercise_taxonomy_primary ON exercise_taxonomy (primary_muscle_group);


-- ============================================================================
-- 2. Seed the taxonomy (~80 canonical lifts)
-- ============================================================================
-- Kept in sync with domains/strength/taxonomy_seed.csv by a dedicated
-- test. If you edit this block, edit the CSV too (and vice versa).

INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('back_squat', 'Back Squat', 'back squat|squat|barbell squat|bs|high bar squat|low bar squat', 'quads', 'glutes|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('front_squat', 'Front Squat', 'front squat|fsq', 'quads', 'glutes|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('goblet_squat', 'Goblet Squat', 'goblet squat', 'quads', 'glutes|core', 'compound', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('bulgarian_split_squat', 'Bulgarian Split Squat', 'bulgarian split squat|bss|split squat|bulgarian', 'quads', 'glutes|hamstrings|core', 'compound', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('hack_squat', 'Hack Squat', 'hack squat', 'quads', 'glutes', 'compound', 'machine', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('leg_press', 'Leg Press', 'leg press', 'quads', 'glutes|hamstrings', 'compound', 'machine', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('overhead_squat', 'Overhead Squat', 'overhead squat|ohsq', 'quads', 'glutes|core|shoulders', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('zercher_squat', 'Zercher Squat', 'zercher squat', 'quads', 'glutes|core|back', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('conventional_deadlift', 'Conventional Deadlift', 'deadlift|conventional deadlift|dl|bb dl', 'hamstrings', 'glutes|back|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('sumo_deadlift', 'Sumo Deadlift', 'sumo deadlift|sumo dl', 'glutes', 'hamstrings|back|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('romanian_deadlift', 'Romanian Deadlift', 'romanian deadlift|rdl', 'hamstrings', 'glutes|back', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('trap_bar_deadlift', 'Trap Bar Deadlift', 'trap bar deadlift|tbdl|trap bar|hex bar deadlift', 'quads', 'glutes|hamstrings|back', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('stiff_leg_deadlift', 'Stiff Leg Deadlift', 'stiff leg deadlift|sldl|stiff legged deadlift', 'hamstrings', 'glutes|back', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('good_morning', 'Good Morning', 'good morning|gm', 'hamstrings', 'glutes|back', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('kettlebell_swing', 'Kettlebell Swing', 'kettlebell swing|kb swing|swing', 'glutes', 'hamstrings|back|core', 'compound', 'kettlebell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('hip_thrust', 'Hip Thrust', 'hip thrust|barbell hip thrust|bb hip thrust', 'glutes', 'hamstrings|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('glute_bridge', 'Glute Bridge', 'glute bridge|bridge', 'glutes', 'hamstrings|core', 'compound', 'bodyweight', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('cable_pull_through', 'Cable Pull Through', 'pull through|cable pull through', 'glutes', 'hamstrings|back', 'compound', 'cable', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('walking_lunge', 'Walking Lunge', 'walking lunge|lunges|lunge', 'quads', 'glutes|hamstrings|core', 'compound', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('reverse_lunge', 'Reverse Lunge', 'reverse lunge', 'quads', 'glutes|hamstrings', 'compound', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('step_up', 'Step Up', 'step up|step ups', 'quads', 'glutes|hamstrings', 'compound', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('leg_extension', 'Leg Extension', 'leg extension|leg ext', 'quads', NULL, 'isolation', 'machine', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('leg_curl', 'Leg Curl', 'leg curl|lying leg curl|seated leg curl|hamstring curl', 'hamstrings', NULL, 'isolation', 'machine', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('nordic_curl', 'Nordic Curl', 'nordic curl|nordics', 'hamstrings', 'glutes|core', 'isolation', 'bodyweight', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('standing_calf_raise', 'Standing Calf Raise', 'standing calf raise|calf raise|calves', 'calves', NULL, 'isolation', 'machine', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('seated_calf_raise', 'Seated Calf Raise', 'seated calf raise', 'calves', NULL, 'isolation', 'machine', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('bench_press', 'Bench Press', 'bench press|bench|barbell bench|bp|flat bench', 'chest', 'triceps|shoulders', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('incline_bench_press', 'Incline Bench Press', 'incline bench press|incline bench|incline bp', 'chest', 'triceps|shoulders', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('decline_bench_press', 'Decline Bench Press', 'decline bench press|decline bench', 'chest', 'triceps|shoulders', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('dumbbell_bench_press', 'Dumbbell Bench Press', 'dumbbell bench press|db bench|db bp', 'chest', 'triceps|shoulders', 'compound', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('dumbbell_incline_press', 'Incline Dumbbell Press', 'incline dumbbell press|incline db press|incline db bench', 'chest', 'triceps|shoulders', 'compound', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('close_grip_bench_press', 'Close Grip Bench Press', 'close grip bench|cgbp|close grip bp', 'triceps', 'chest|shoulders', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('overhead_press', 'Overhead Press', 'overhead press|ohp|shoulder press|military press|strict press', 'shoulders', 'triceps|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('push_press', 'Push Press', 'push press', 'shoulders', 'triceps|core|quads', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('dumbbell_shoulder_press', 'Dumbbell Shoulder Press', 'dumbbell shoulder press|db shoulder press|db ohp', 'shoulders', 'triceps', 'compound', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('arnold_press', 'Arnold Press', 'arnold press', 'shoulders', 'triceps', 'compound', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('machine_chest_press', 'Machine Chest Press', 'machine chest press|chest press machine', 'chest', 'triceps|shoulders', 'compound', 'machine', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('dip', 'Dip', 'dip|dips', 'triceps', 'chest|shoulders', 'compound', 'bodyweight', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('push_up', 'Push Up', 'push up|pushup|push-up', 'chest', 'triceps|shoulders|core', 'compound', 'bodyweight', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('pull_up', 'Pull Up', 'pull up|pullup|pull-up', 'back', 'biceps|core', 'compound', 'bodyweight', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('chin_up', 'Chin Up', 'chin up|chinup|chin-up', 'back', 'biceps|core', 'compound', 'bodyweight', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('lat_pulldown', 'Lat Pulldown', 'lat pulldown|pulldown', 'back', 'biceps', 'compound', 'cable', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('barbell_row', 'Barbell Row', 'barbell row|bent over row|bb row|row', 'back', 'biceps|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('pendlay_row', 'Pendlay Row', 'pendlay row', 'back', 'biceps|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('dumbbell_row', 'Dumbbell Row', 'dumbbell row|db row|one arm row', 'back', 'biceps', 'compound', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('seated_cable_row', 'Seated Cable Row', 'seated row|cable row|seated cable row', 'back', 'biceps', 'compound', 'cable', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('t_bar_row', 'T-Bar Row', 't bar row|t-bar row|tbar row', 'back', 'biceps', 'compound', 'machine', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('face_pull', 'Face Pull', 'face pull', 'shoulders', 'back', 'isolation', 'cable', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('barbell_shrug', 'Barbell Shrug', 'shrug|barbell shrug', 'back', NULL, 'isolation', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('dumbbell_shrug', 'Dumbbell Shrug', 'db shrug|dumbbell shrug', 'back', NULL, 'isolation', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('barbell_curl', 'Barbell Curl', 'barbell curl|bb curl|bicep curl', 'biceps', NULL, 'isolation', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('dumbbell_curl', 'Dumbbell Curl', 'dumbbell curl|db curl', 'biceps', NULL, 'isolation', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('hammer_curl', 'Hammer Curl', 'hammer curl', 'biceps', NULL, 'isolation', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('preacher_curl', 'Preacher Curl', 'preacher curl', 'biceps', NULL, 'isolation', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('incline_dumbbell_curl', 'Incline Dumbbell Curl', 'incline curl|incline db curl', 'biceps', NULL, 'isolation', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('cable_curl', 'Cable Curl', 'cable curl', 'biceps', NULL, 'isolation', 'cable', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('tricep_pushdown', 'Tricep Pushdown', 'tricep pushdown|pushdown|cable pushdown', 'triceps', NULL, 'isolation', 'cable', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('skull_crusher', 'Skull Crusher', 'skull crusher|skullcrusher|lying tricep extension', 'triceps', NULL, 'isolation', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('overhead_tricep_extension', 'Overhead Tricep Extension', 'overhead tricep extension|oh tri ext|french press', 'triceps', NULL, 'isolation', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('tricep_kickback', 'Tricep Kickback', 'kickback|tricep kickback', 'triceps', NULL, 'isolation', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('lateral_raise', 'Lateral Raise', 'lateral raise|side raise|lat raise|db lateral', 'shoulders', NULL, 'isolation', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('front_raise', 'Front Raise', 'front raise', 'shoulders', NULL, 'isolation', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('rear_delt_fly', 'Rear Delt Fly', 'rear delt fly|rear delt raise|reverse fly', 'shoulders', 'back', 'isolation', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('upright_row', 'Upright Row', 'upright row', 'shoulders', 'back', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('dumbbell_fly', 'Dumbbell Fly', 'dumbbell fly|db fly|chest fly', 'chest', NULL, 'isolation', 'dumbbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('cable_fly', 'Cable Fly', 'cable fly|cable crossover', 'chest', NULL, 'isolation', 'cable', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('pec_deck', 'Pec Deck', 'pec deck|machine fly', 'chest', NULL, 'isolation', 'machine', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('plank', 'Plank', 'plank', 'core', NULL, 'isolation', 'bodyweight', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('sit_up', 'Sit Up', 'sit up|situp|sit-up', 'core', NULL, 'isolation', 'bodyweight', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('hanging_leg_raise', 'Hanging Leg Raise', 'hanging leg raise|leg raise', 'core', NULL, 'isolation', 'bodyweight', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('cable_crunch', 'Cable Crunch', 'cable crunch', 'core', NULL, 'isolation', 'cable', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('russian_twist', 'Russian Twist', 'russian twist', 'core', NULL, 'isolation', 'bodyweight', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('ab_rollout', 'Ab Rollout', 'ab rollout|rollout', 'core', NULL, 'isolation', 'bodyweight', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('weighted_sit_up', 'Weighted Sit Up', 'weighted sit up', 'core', NULL, 'isolation', 'bodyweight', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('power_clean', 'Power Clean', 'power clean|clean', 'quads', 'hamstrings|glutes|back|shoulders|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('hang_clean', 'Hang Clean', 'hang clean', 'quads', 'hamstrings|glutes|back|shoulders|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('clean_and_jerk', 'Clean and Jerk', 'clean and jerk|c&j', 'quads', 'hamstrings|glutes|back|shoulders|triceps|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('snatch', 'Snatch', 'snatch|power snatch', 'quads', 'hamstrings|glutes|back|shoulders|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('push_jerk', 'Push Jerk', 'push jerk', 'shoulders', 'quads|triceps|core', 'compound', 'barbell', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('cable_lateral_raise', 'Cable Lateral Raise', 'cable lateral raise|cable side raise', 'shoulders', NULL, 'isolation', 'cable', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('reverse_pec_deck', 'Reverse Pec Deck', 'reverse pec deck', 'shoulders', 'back', 'isolation', 'machine', 'seed');
INSERT INTO exercise_taxonomy (exercise_id, canonical_name, aliases, primary_muscle_group, secondary_muscle_groups, category, equipment, source) VALUES ('machine_row', 'Machine Row', 'machine row|seated machine row', 'back', 'biceps', 'compound', 'machine', 'seed');


-- ============================================================================
-- 3. Expand accepted_resistance_training_state_daily
-- ============================================================================
-- SQLite 3.35+ ALTER TABLE ADD COLUMN. One statement per column so the
-- migration splitter (which keys on a single terminating semicolon)
-- handles each add independently.

ALTER TABLE accepted_resistance_training_state_daily ADD COLUMN total_reps INTEGER;
ALTER TABLE accepted_resistance_training_state_daily ADD COLUMN volume_by_muscle_group_json TEXT;
ALTER TABLE accepted_resistance_training_state_daily ADD COLUMN estimated_1rm_json TEXT;
ALTER TABLE accepted_resistance_training_state_daily ADD COLUMN unmatched_exercise_tokens_json TEXT;


-- ============================================================================
-- 4. Add nullable exercise_id FK on gym_set
-- ============================================================================
-- Best-effort taxonomy linkage. Historical rows stay NULL; the strength
-- projector (Phase 4 step 2) resolves exercise_name against the
-- taxonomy and writes exercise_id for new rows. Reproject can re-resolve
-- historical rows — that path is owned by the projector, not this
-- migration.

ALTER TABLE gym_set ADD COLUMN exercise_id TEXT REFERENCES exercise_taxonomy (exercise_id);
CREATE INDEX idx_gym_set_exercise_id ON gym_set (exercise_id);
