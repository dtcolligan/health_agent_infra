-- Migration 020 — target table (v0.1.8 W50).
--
-- v0.1.8 § PLAN.md W50: minimal user-authored target ledger so
-- hydration / protein / calorie / sleep-window / training-load
-- aims have units, dates, review semantics, provenance, and
-- supersession instead of living in prose memory only.
--
-- Outcomes never auto-mutate targets. Replacements use
-- `status='superseded'` + `superseded_by_target_id`, mirroring the
-- intent_item discipline (migration 019).
--
-- 17 fields per PLAN.md § 2 W50. status / target_type are TEXT with
-- CHECK constraints listing the v1 vocabulary.

CREATE TABLE target (
    target_id                   TEXT    PRIMARY KEY,
    user_id                     TEXT    NOT NULL,
    domain                      TEXT    NOT NULL,

    target_type                 TEXT    NOT NULL
        CHECK (target_type IN (
            'hydration_ml', 'protein_g', 'calories_kcal',
            'sleep_duration_h', 'sleep_window', 'training_load',
            'other'
        )),
    status                      TEXT    NOT NULL
        CHECK (status IN ('proposed', 'active', 'superseded', 'archived')),

    value_json                  TEXT    NOT NULL,           -- structured target value
    unit                        TEXT    NOT NULL,
    lower_bound                 REAL,
    upper_bound                 REAL,

    effective_from              TEXT    NOT NULL,           -- ISO civil date
    effective_to                TEXT,                       -- ISO civil date (NULL = open-ended)
    review_after                TEXT,                       -- ISO civil date

    reason                      TEXT    NOT NULL,
    source                      TEXT    NOT NULL,           -- 'user_authored' | 'agent_proposed'
    ingest_actor                TEXT    NOT NULL,
    created_at                  TEXT    NOT NULL,           -- ISO datetime

    supersedes_target_id        TEXT REFERENCES target (target_id),
    superseded_by_target_id     TEXT REFERENCES target (target_id)
);

-- Active-at-date queries: snapshot integration calls
-- "give me every active row whose effective window covers ``as_of_date``."
CREATE INDEX idx_target_active_window
    ON target (user_id, status, effective_from, effective_to);

-- Domain + type lookups for the user surface ("show me my hydration target").
CREATE INDEX idx_target_domain_type
    ON target (user_id, domain, target_type, status);

-- Supersession-chain audit.
CREATE INDEX idx_target_supersedes
    ON target (supersedes_target_id)
    WHERE supersedes_target_id IS NOT NULL;
