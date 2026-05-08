-- Migration 025 — extend target.target_type CHECK with carbs_g + fat_g.
--
-- v0.1.15 W-C (round-4 F-PHASE0-01 Option A revision). The original
-- §2.D contract proposed a NEW `nutrition_target` table; the Phase 0
-- internal sweep showed the existing `target` table (migration 020,
-- v0.1.8 W50) is already domain-agnostic, already W57-gates commit
-- via cmd_target_commit, and already in production use for the
-- maintainer's nutrition rows (calories_kcal=3100, protein_g=160).
-- The cleaner shape is to extend the existing CHECK rather than
-- build a parallel table.
--
-- SQLite does not support `ALTER TABLE ... DROP CONSTRAINT` or
-- modifying a CHECK constraint in place, so the standard recreate-
-- and-copy idiom applies: rename target → target_old; recreate target
-- with the extended CHECK; copy rows; drop target_old; rebuild the
-- three indexes from migration 020.
--
-- Existing rows survive byte-stable on every column. The maintainer's
-- live state (3 nutrition rows) carries over unchanged.
--
-- Note on migration numbering: PLAN §2.D round-4 draft cited "024"
-- but v0.1.15 W-GYM-SETID claimed 024 first; W-C lands at 025. PLAN
-- §2.D + v0.1.17 README updated in this same change-set.

ALTER TABLE target RENAME TO target_old;

CREATE TABLE target (
    target_id                   TEXT    PRIMARY KEY,
    user_id                     TEXT    NOT NULL,
    domain                      TEXT    NOT NULL,

    target_type                 TEXT    NOT NULL
        CHECK (target_type IN (
            'hydration_ml', 'protein_g', 'calories_kcal',
            'carbs_g', 'fat_g',
            'sleep_duration_h', 'sleep_window', 'training_load',
            'other'
        )),
    status                      TEXT    NOT NULL
        CHECK (status IN ('proposed', 'active', 'superseded', 'archived')),

    value_json                  TEXT    NOT NULL,
    unit                        TEXT    NOT NULL,
    lower_bound                 REAL,
    upper_bound                 REAL,

    effective_from              TEXT    NOT NULL,
    effective_to                TEXT,
    review_after                TEXT,

    reason                      TEXT    NOT NULL,
    source                      TEXT    NOT NULL,
    ingest_actor                TEXT    NOT NULL,
    created_at                  TEXT    NOT NULL,

    supersedes_target_id        TEXT REFERENCES target (target_id),
    superseded_by_target_id     TEXT REFERENCES target (target_id)
);

INSERT INTO target (
    target_id, user_id, domain, target_type, status,
    value_json, unit, lower_bound, upper_bound,
    effective_from, effective_to, review_after,
    reason, source, ingest_actor, created_at,
    supersedes_target_id, superseded_by_target_id
)
SELECT
    target_id, user_id, domain, target_type, status,
    value_json, unit, lower_bound, upper_bound,
    effective_from, effective_to, review_after,
    reason, source, ingest_actor, created_at,
    supersedes_target_id, superseded_by_target_id
FROM target_old;

DROP TABLE target_old;

CREATE INDEX idx_target_active_window
    ON target (user_id, status, effective_from, effective_to);

CREATE INDEX idx_target_domain_type
    ON target (user_id, domain, target_type, status);

CREATE INDEX idx_target_supersedes
    ON target (supersedes_target_id)
    WHERE supersedes_target_id IS NOT NULL;
