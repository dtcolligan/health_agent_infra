-- Migration 004 — promote sleep + stress to first-class accepted-state tables.
--
-- Phase 3 step 1. Before this migration runs, sleep_hours /
-- all_day_stress / manual_stress_score / body_battery_end_of_day live
-- as columns on accepted_recovery_state_daily. After it runs, they live
-- on two new domain-owned tables (accepted_sleep_state_daily,
-- accepted_stress_state_daily) and the recovery accepted table shrinks
-- to the signals that genuinely belong to the recovery domain
-- (resting_hr / hrv / training load / readiness components).
--
-- Three moves in one migration:
--   1. CREATE TABLE accepted_sleep_state_daily with the expanded shape
--      from state_model_v1 §2.3.
--   2. CREATE TABLE accepted_stress_state_daily with the shape from
--      state_model_v1 §2.3.
--   3. Backfill both new tables from existing accepted_recovery_state_daily
--      rows so every date that had a sleep_hours / stress value gets a row
--      in the new table. No row loss; no re-derivation from raw at migrate
--      time — that is what `hai state reproject --scope all` is for, and
--      the operator runs it post-migrate to backfill the richer columns
--      (sleep minute breakdowns, sleep scores, etc.) from source_daily_garmin.
--   4. DROP COLUMN the four moving fields from accepted_recovery_state_daily.
--   5. Add `orphan` column on x_rule_firing to defend the Phase 2.5 finding
--      (Condition 1): if a future X-rule emits a firing whose affected_domain
--      is not in the committing plan's proposal domains, the runtime stamps
--      orphan=1 instead of silently dropping.
--
-- Safety: the `hai state migrate --dry-run 004` helper must be run before
-- this migration commits. It reports any date where the existing
-- accepted_recovery values diverge from what the new sleep/stress
-- projectors would produce from raw. Non-empty diff means a manual
-- reconciliation step is needed before running the migration forward.


-- ============================================================================
-- 1. accepted_sleep_state_daily (new)
-- ============================================================================
-- sleep_hours is derived (sum of deep+light+rem in hours) and is
-- redundant with sleep_deep_min + sleep_light_min + sleep_rem_min, but
-- kept as a first-class column so classify / policy do not have to
-- recompute it on every read.
--
-- sleep_start_ts / sleep_end_ts / avg_sleep_hrv are v1.1 enrichments —
-- not in the Garmin daily CSV today, so they stay NULL in v1 but reserve
-- the columns so a later pull path can populate them without another
-- migration.

CREATE TABLE accepted_sleep_state_daily (
    as_of_date                  TEXT    NOT NULL,
    user_id                     TEXT    NOT NULL,

    sleep_hours                 REAL,
    sleep_score_overall         INTEGER,
    sleep_score_quality         INTEGER,
    sleep_score_duration        INTEGER,
    sleep_score_recovery        INTEGER,
    sleep_deep_min              REAL,
    sleep_light_min             REAL,
    sleep_rem_min               REAL,
    sleep_awake_min             REAL,
    awake_count                 INTEGER,
    sleep_start_ts              TEXT,
    sleep_end_ts                TEXT,
    avg_sleep_respiration       REAL,
    avg_sleep_stress            REAL,
    avg_sleep_hrv               REAL,

    derived_from                TEXT    NOT NULL,
    source                      TEXT    NOT NULL,
    ingest_actor                TEXT    NOT NULL,
    projected_at                TEXT    NOT NULL,
    corrected_at                TEXT,

    PRIMARY KEY (as_of_date, user_id)
);
CREATE INDEX idx_accepted_sleep_date ON accepted_sleep_state_daily (as_of_date, user_id);


-- ============================================================================
-- 2. accepted_stress_state_daily (new)
-- ============================================================================
-- garmin_all_day_stress is the renamed all_day_stress (Garmin's 0-100
-- day aggregate). manual_stress_score is the 1-5 user-reported rating.
-- stress_event_count / stress_tags_json are v1.1 enrichments — stays
-- NULL until Garmin stress-event pull or a richer intake shape lands.
-- body_battery_end_of_day moves out of recovery because body battery is
-- a stress/energy-reserve signal, not a recovery signal.

CREATE TABLE accepted_stress_state_daily (
    as_of_date                  TEXT    NOT NULL,
    user_id                     TEXT    NOT NULL,

    garmin_all_day_stress       INTEGER,
    manual_stress_score         INTEGER,
    stress_event_count          INTEGER,
    stress_tags_json            TEXT,
    body_battery_end_of_day     INTEGER,

    derived_from                TEXT    NOT NULL,
    source                      TEXT    NOT NULL,
    ingest_actor                TEXT    NOT NULL,
    projected_at                TEXT    NOT NULL,
    corrected_at                TEXT,

    PRIMARY KEY (as_of_date, user_id)
);
CREATE INDEX idx_accepted_stress_date ON accepted_stress_state_daily (as_of_date, user_id);


-- ============================================================================
-- 3. Backfill both new tables from existing accepted_recovery rows
-- ============================================================================
-- Every recovery row with a sleep_hours value contributes one sleep row.
-- Every recovery row with any stress or body-battery signal contributes
-- one stress row. We copy only the moving columns; the richer sleep
-- fields (deep/light/rem minutes, scores) stay NULL and are filled in
-- by `hai state reproject --scope all` post-migrate.
--
-- derived_from, source, ingest_actor, projected_at, corrected_at are
-- copied verbatim so the audit chain survives the move. A fresh
-- projection round will overwrite them with the correct per-domain
-- dimension contributors, but until then the backfilled rows are valid.

INSERT INTO accepted_sleep_state_daily (
    as_of_date, user_id, sleep_hours,
    derived_from, source, ingest_actor, projected_at, corrected_at
)
SELECT
    as_of_date, user_id, sleep_hours,
    derived_from, source, ingest_actor, projected_at, corrected_at
FROM accepted_recovery_state_daily
WHERE sleep_hours IS NOT NULL;

INSERT INTO accepted_stress_state_daily (
    as_of_date, user_id,
    garmin_all_day_stress, manual_stress_score, body_battery_end_of_day,
    derived_from, source, ingest_actor, projected_at, corrected_at
)
SELECT
    as_of_date, user_id,
    all_day_stress, manual_stress_score, body_battery_end_of_day,
    derived_from, source, ingest_actor, projected_at, corrected_at
FROM accepted_recovery_state_daily
WHERE all_day_stress IS NOT NULL
   OR manual_stress_score IS NOT NULL
   OR body_battery_end_of_day IS NOT NULL;


-- ============================================================================
-- 4. Shrink accepted_recovery_state_daily
-- ============================================================================
-- SQLite 3.35+ supports DROP COLUMN. One statement per column so the
-- migration splitter (which keys on a single terminating semicolon) can
-- handle each drop independently.

ALTER TABLE accepted_recovery_state_daily DROP COLUMN sleep_hours;
ALTER TABLE accepted_recovery_state_daily DROP COLUMN all_day_stress;
ALTER TABLE accepted_recovery_state_daily DROP COLUMN manual_stress_score;
ALTER TABLE accepted_recovery_state_daily DROP COLUMN body_battery_end_of_day;


-- ============================================================================
-- 5. Orphan-firing defense on x_rule_firing
-- ============================================================================
-- Phase 2.5 independent-eval Condition 1. Current X-rule evaluators
-- iterate the proposal list to emit firings, so orphans cannot occur by
-- construction — but future rules that fire on snapshot-only signals
-- could reintroduce them. Stamp the invariant into the schema so a
-- future regression surfaces as orphan=1 rows instead of silently
-- dropped firings.

ALTER TABLE x_rule_firing ADD COLUMN orphan INTEGER NOT NULL DEFAULT 0
    CHECK (orphan IN (0, 1));
CREATE INDEX idx_x_rule_firing_orphan ON x_rule_firing (orphan, fired_at);
