-- Migration 015 — manual_readiness_raw table.
--
-- Per D2 §Per-domain landing tables. The existing
-- `hai intake readiness` command emitted JSON to stdout for agent
-- composition with `hai pull --manual-readiness-json`, but did not
-- persist. That caused the 2026-04-23 footgun where users running
-- `hai intake readiness` reasonably expected the classifier to pick
-- up the new signal, and it didn't.
--
-- Shape parallels stress_manual_raw and nutrition_intake_raw so the
-- new table slots cleanly into the existing intake-projector pattern.
--
-- D1's described migrations 015 and 016 were behavioral-only
-- (recommendation_log and review_outcome re-link logic) with no SQL
-- changes. This migration takes the next available number to stay
-- contiguous with the applied-in-sequence runner.

CREATE TABLE manual_readiness_raw (
    submission_id            TEXT    PRIMARY KEY,
    user_id                  TEXT    NOT NULL,
    as_of_date               TEXT    NOT NULL,

    soreness                 TEXT    NOT NULL,
    energy                   TEXT    NOT NULL,
    planned_session_type     TEXT    NOT NULL,
    active_goal              TEXT,

    source                   TEXT    NOT NULL,
    ingest_actor             TEXT    NOT NULL,
    ingested_at              TEXT    NOT NULL,
    supersedes_submission_id TEXT,

    CHECK (soreness IN ('low','moderate','high')),
    CHECK (energy   IN ('low','moderate','high'))
);

CREATE INDEX idx_manual_readiness_raw_date
  ON manual_readiness_raw(user_id, as_of_date DESC);
