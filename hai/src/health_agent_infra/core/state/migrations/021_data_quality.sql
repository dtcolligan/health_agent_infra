-- Migration 021 — data_quality_daily table (v0.1.8 W51).
--
-- v0.1.8 § PLAN.md W51: first-class user surface answering "was this
-- recommendation data-limited?" Today the runtime tracks
-- `missingness` and provenance per domain inside snapshot blocks,
-- but there is no single ledger a user / agent can query without
-- reconstructing the snapshot. Lee et al. (PMC10654909) on
-- consumer-wearable accuracy supports surfacing data quality
-- explicitly rather than burying it inside per-domain uncertainty.
--
-- This also subsumes the v0.1.7 cold-start visibility gap
-- (REPORT.md gap I) — the `cold_start_window_state` column lets a
-- consumer answer "is this a first-week recommendation?" with one
-- query.
--
-- Per-source / per-domain rows: a single (user, date, domain) can
-- have multiple rows when more than one source contributed evidence
-- (e.g. recovery from garmin + intervals_icu).

CREATE TABLE data_quality_daily (
    user_id                     TEXT    NOT NULL,
    as_of_date                  TEXT    NOT NULL,
    domain                      TEXT    NOT NULL,
    source                      TEXT    NOT NULL,

    freshness_hours             REAL,
    coverage_band               TEXT,                       -- 'full' | 'partial' | 'sparse' | 'insufficient'
    missingness                 TEXT,                       -- 'absent' | 'unavailable_at_source' | 'pending_user_input' | composite

    source_unavailable          INTEGER NOT NULL DEFAULT 0
        CHECK (source_unavailable IN (0, 1)),
    user_input_pending          INTEGER NOT NULL DEFAULT 0
        CHECK (user_input_pending IN (0, 1)),
    suspicious_discontinuity    INTEGER NOT NULL DEFAULT 0
        CHECK (suspicious_discontinuity IN (0, 1)),

    cold_start_window_state     TEXT,                       -- 'in_window' | 'recently_closed' | 'post_cold_start'
    computed_at                 TEXT    NOT NULL,           -- ISO datetime

    PRIMARY KEY (user_id, as_of_date, domain, source)
);

CREATE INDEX idx_data_quality_daily_date
    ON data_quality_daily (user_id, as_of_date);

CREATE INDEX idx_data_quality_daily_domain
    ON data_quality_daily (user_id, domain, as_of_date);
