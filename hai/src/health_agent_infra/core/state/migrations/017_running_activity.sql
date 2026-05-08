-- Migration 017 — running_activity table.
--
-- Per-session structural record from the intervals.icu /activities endpoint.
-- Previously the intervals.icu adapter only hit /wellness.json, so running
-- domain signals could only see daily rollups with distance_m /
-- moderate_intensity_min / vigorous_intensity_min etc. always null. The
-- activities endpoint carries the actual session: HR zone times, interval
-- structure, TRIMP, warmup/cooldown splits, source of truth for distance and
-- duration.
--
-- PK is the intervals.icu activity id (string, e.g. "i142248964"). We do
-- NOT use an autoincrement surrogate because the upstream id is stable
-- across re-pulls, so upsert-on-conflict-replace gives us free idempotency
-- against the canonical upstream row. `external_id` carries the vendor-of-
-- vendor id (e.g. the Garmin Connect activity id) for cross-reference but
-- is not unique (intervals.icu dedupes differently than Garmin).
--
-- `raw_json` preserves the full upstream payload so downstream skills can
-- peek at fields the typed projection hasn't mapped yet. Cheap insurance:
-- intervals.icu evolves its activity schema, and re-running clean over the
-- raw JSON is free.

CREATE TABLE running_activity (
    activity_id              TEXT    PRIMARY KEY,
    user_id                  TEXT    NOT NULL,
    as_of_date               TEXT    NOT NULL,

    start_date_utc           TEXT,
    start_date_local         TEXT,
    source                   TEXT,
    external_id              TEXT,
    activity_type            TEXT,
    name                     TEXT,

    distance_m               REAL,
    moving_time_s            REAL,
    elapsed_time_s           REAL,
    average_hr               REAL,
    max_hr                   REAL,
    athlete_max_hr           REAL,

    hr_zone_times_s_json     TEXT,
    hr_zones_bpm_json        TEXT,
    interval_summary_json    TEXT,

    trimp                    REAL,
    icu_training_load        REAL,
    hr_load                  REAL,
    hr_load_type             TEXT,

    warmup_time_s            REAL,
    cooldown_time_s          REAL,
    lap_count                INTEGER,

    average_speed_mps        REAL,
    max_speed_mps            REAL,
    pace_s_per_m             REAL,
    average_cadence_spm      REAL,
    average_stride_m         REAL,

    calories                 REAL,
    total_elevation_gain_m   REAL,
    total_elevation_loss_m   REAL,

    feel                     INTEGER,
    icu_rpe                  INTEGER,
    session_rpe              REAL,
    device_name              TEXT,

    raw_json                 TEXT    NOT NULL,

    ingest_actor             TEXT    NOT NULL,
    ingested_at              TEXT    NOT NULL
);

CREATE INDEX idx_running_activity_user_date
  ON running_activity(user_id, as_of_date DESC);

CREATE INDEX idx_running_activity_type_date
  ON running_activity(user_id, activity_type, as_of_date DESC);
