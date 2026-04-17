-- Migration 003 — synthesis scaffolding.
--
-- Adds the three tables the Phase 2+ synthesis layer writes to
-- (proposal_log, daily_plan, x_rule_firing) plus a `domain` column on the
-- three recommendation/review tables so every row carries its owning domain.
--
-- All additions are forward-only and idempotent at the migration-runner level:
-- the runner records applied versions in schema_migrations and skips on rerun.
--
-- Existing rows in recommendation_log / review_event / review_outcome get
-- backfilled to domain='recovery' via ALTER TABLE ... ADD COLUMN with a
-- NOT NULL DEFAULT, which SQLite applies to all current rows. Nothing in this
-- migration requires data rewrites or per-row updates.


-- ============================================================================
-- SYNTHESIS LAYER (new)
-- ============================================================================

-- Append-only log of per-domain proposals emitted by domain skills, before
-- synthesis reconciles them. One row per proposal. daily_plan_id is NULL
-- until synthesis links it; non-NULL afterwards.
CREATE TABLE proposal_log (
    proposal_id                 TEXT    PRIMARY KEY,
    daily_plan_id               TEXT,                       -- nullable until synthesis links
    user_id                     TEXT    NOT NULL,
    domain                      TEXT    NOT NULL,           -- 'recovery' | 'running' | 'sleep' | 'stress' | 'strength' | 'nutrition'
    for_date                    TEXT    NOT NULL,
    schema_version              TEXT    NOT NULL,           -- e.g. 'domain_proposal.v1'

    action                      TEXT    NOT NULL,
    confidence                  TEXT    NOT NULL,
    payload_json                TEXT    NOT NULL,           -- full DomainProposal JSON

    source                      TEXT    NOT NULL,           -- 'claude_agent_v1' etc
    ingest_actor                TEXT    NOT NULL,
    agent_version               TEXT,
    produced_at                 TEXT,
    validated_at                TEXT    NOT NULL,
    projected_at                TEXT    NOT NULL
);
CREATE INDEX idx_proposal_log_for_date ON proposal_log (for_date, user_id, domain);
CREATE INDEX idx_proposal_log_plan ON proposal_log (daily_plan_id);


-- Synthesis run output. One row per invocation of the synthesis skill. Links
-- the N recommendations it produced and records which X-rules fired.
CREATE TABLE daily_plan (
    daily_plan_id               TEXT    PRIMARY KEY,
    user_id                     TEXT    NOT NULL,
    for_date                    TEXT    NOT NULL,
    synthesized_at              TEXT    NOT NULL,

    recommendation_ids_json     TEXT    NOT NULL,           -- JSON array of recommendation_id strings
    proposal_ids_json           TEXT    NOT NULL,           -- JSON array of proposal_id strings (inputs)
    x_rules_fired_json          TEXT    NOT NULL,           -- JSON array of x_rule_id strings (summary of firings table)

    synthesis_meta_json         TEXT,                       -- optional metadata (firings_by_tier, domains_blocked, notes)

    source                      TEXT    NOT NULL,
    ingest_actor                TEXT    NOT NULL,
    agent_version               TEXT,
    validated_at                TEXT    NOT NULL,
    projected_at                TEXT    NOT NULL
);
CREATE INDEX idx_daily_plan_for_date ON daily_plan (for_date, user_id);


-- Audit record of each X-rule firing, one row per (daily_plan_id, x_rule_id,
-- affected_domain) triple. Supports cross-plan analysis like "how often has
-- X1a fired in the last 30 days."
CREATE TABLE x_rule_firing (
    firing_id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    daily_plan_id               TEXT    NOT NULL REFERENCES daily_plan (daily_plan_id),
    user_id                     TEXT    NOT NULL,
    x_rule_id                   TEXT    NOT NULL,           -- 'X1a' | 'X3b' | 'X6a' | ...
    tier                        TEXT    NOT NULL CHECK (tier IN ('soften', 'block', 'cap_confidence', 'adjust', 'restructure')),
    affected_domain             TEXT    NOT NULL,           -- which domain the firing mutated
    trigger_note                TEXT    NOT NULL,           -- human-readable trigger string (from xrule engine)
    mutation_json               TEXT,                       -- JSON object of recommended_mutation (may be NULL for cap_confidence)
    source_signals_json         TEXT,                       -- JSON object of which snapshot signals drove it
    fired_at                    TEXT    NOT NULL
);
CREATE INDEX idx_x_rule_firing_plan ON x_rule_firing (daily_plan_id);
CREATE INDEX idx_x_rule_firing_rule ON x_rule_firing (x_rule_id, fired_at);


-- ============================================================================
-- DOMAIN COLUMN ON EXISTING RECOMMENDATION + REVIEW TABLES
-- ============================================================================
--
-- Each existing recommendation / review row is retroactively labelled with
-- its owning domain. All v1 rows were produced by the recovery-readiness
-- skill, so the backfill default is 'recovery'. Future rows must set the
-- column explicitly per domain.

ALTER TABLE recommendation_log
    ADD COLUMN domain TEXT NOT NULL DEFAULT 'recovery';

ALTER TABLE review_event
    ADD COLUMN domain TEXT NOT NULL DEFAULT 'recovery';

ALTER TABLE review_outcome
    ADD COLUMN domain TEXT NOT NULL DEFAULT 'recovery';

CREATE INDEX idx_recommendation_log_domain ON recommendation_log (domain, for_date);
CREATE INDEX idx_review_event_domain ON review_event (domain, review_at);
CREATE INDEX idx_review_outcome_domain ON review_outcome (domain, recorded_at);
