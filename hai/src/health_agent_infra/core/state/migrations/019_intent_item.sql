-- Migration 019 — intent_item table (v0.1.8 W49).
--
-- v0.1.8 § PLAN.md W49: minimal user-authored intent ledger so a
-- review outcome can be interpreted against what the user said they
-- intended to do that day or week. Outcomes never mutate intent
-- automatically — every row is user-authored or explicitly
-- confirmed via the `hai intent` CLI surfaces (or an agent acting
-- on a user instruction with `source = 'agent_proposed'`).
--
-- Replacements use archive/supersession (`status = 'archived'` +
-- `superseded_by_intent_id`), not destructive update. This matches
-- the D1 plan-revision discipline so the ledger is auditable end-to-
-- end without JSONL replay.
--
-- All 17 fields per PLAN.md § 2 W49. status / scope_type /
-- intent_type / priority / flexibility are TEXT with CHECK
-- constraints listing the v1 vocabulary.

CREATE TABLE intent_item (
    intent_id                   TEXT    PRIMARY KEY,
    user_id                     TEXT    NOT NULL,
    domain                      TEXT    NOT NULL,

    scope_type                  TEXT    NOT NULL
        CHECK (scope_type IN ('day', 'week', 'date_range')),
    scope_start                 TEXT    NOT NULL,           -- ISO civil date
    scope_end                   TEXT    NOT NULL,           -- ISO civil date

    intent_type                 TEXT    NOT NULL
        CHECK (intent_type IN (
            'training_session', 'sleep_window', 'rest_day',
            'travel', 'constraint', 'other'
        )),
    status                      TEXT    NOT NULL
        CHECK (status IN ('proposed', 'active', 'superseded', 'archived')),
    priority                    TEXT    NOT NULL
        CHECK (priority IN ('low', 'normal', 'high')),
    flexibility                 TEXT    NOT NULL
        CHECK (flexibility IN ('fixed', 'flexible', 'optional')),

    payload_json                TEXT    NOT NULL,           -- structured detail
    reason                      TEXT    NOT NULL,
    source                      TEXT    NOT NULL,           -- 'user_authored' | 'agent_proposed' | ...
    ingest_actor                TEXT    NOT NULL,

    created_at                  TEXT    NOT NULL,           -- ISO datetime
    effective_at                TEXT    NOT NULL,           -- ISO datetime
    review_after                TEXT,                       -- ISO datetime (optional)

    supersedes_intent_id        TEXT REFERENCES intent_item (intent_id),
    superseded_by_intent_id     TEXT REFERENCES intent_item (intent_id)
);

-- Active-at-date queries are the hot path: snapshot integration calls
-- "give me every active row whose scope window covers ``as_of_date``."
-- Bracket the index off (user_id, status, scope_start) so the planner
-- can prune by user + active state before the date-range scan.
CREATE INDEX idx_intent_item_active_window
    ON intent_item (user_id, status, scope_start, scope_end);

-- Domain-scoped lookups (`hai intent training list`) and the per-domain
-- review interpretation path key off (user_id, domain, status).
CREATE INDEX idx_intent_item_domain
    ON intent_item (user_id, domain, status);

-- Supersession-chain audit: walk forward from any row to its canonical
-- leaf in O(1) hops via the index instead of a full table scan.
CREATE INDEX idx_intent_item_supersedes
    ON intent_item (supersedes_intent_id)
    WHERE supersedes_intent_id IS NOT NULL;
