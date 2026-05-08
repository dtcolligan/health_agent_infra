-- Migration 011 — planned_recommendation ledger (Phase 1 of the
-- agent-operable runtime plan; see
-- hai/reporting/plans/historical/agent_operable_runtime_plan.md §1).
--
-- Closes the audit chain at the aggregate level. Today the pipeline is:
--
--   proposal_log         (per-domain planned intent)
--       ↓   (X-rule firings mutate per-domain drafts in memory)
--   daily_plan           (aggregate adapted plan committed)
--   recommendation_log   (per-domain adapted recommendations committed)
--
-- What's missing is the pre-X-rule aggregate — the plan the synthesis
-- transaction would have committed if no X-rule had fired. That state
-- exists briefly in `run_synthesis` between
-- `_mechanical_draft(proposal, ...)` and `apply_phase_a`, then is lost.
-- An agent asked "what was the original plan, before the softening?"
-- has to reconstruct it by inverting `x_rule_firing.mutation_json`,
-- which is fragile (every X-rule edit is a potential silent regression).
--
-- This migration adds a first-class row per (daily_plan_id, domain) for
-- the pre-mutation recommendation shape, written atomically inside the
-- existing synthesis transaction. Mirrors `recommendation_log` columns
-- so diffs between planned and adapted are cheap (same schema on both
-- sides of the diff).
--
-- Schema choice: per-domain rows (Option 2 in the plan) rather than a
-- JSON blob (Option 1) or on-demand reconstruction (Option 3). Rationale:
--   - Option 2 mirrors recommendation_log's shape so `SELECT ... JOIN`
--     works naturally for the three-state view.
--   - Queryable cross-plan ("how often has recovery been softened from
--     hard this month?") without JSON extraction.
--   - The chain is fully walkable via FKs: proposal_log.proposal_id
--     ← planned_recommendation.proposal_id; daily_plan.daily_plan_id
--     ← planned_recommendation.daily_plan_id.
--   - ~6 rows per plan at per-day cadence; negligible space cost.
--
-- Backfill: none. The pre-mutation bundle cannot be reconstructed
-- correctly for historical plans (the drafts weren't captured). The
-- ledger starts at the migration boundary and grows forward. The
-- explain surface must degrade gracefully for legacy daily_plan rows
-- with no paired planned_recommendation rows — a "two-state view (adapted,
-- performed)" rather than the full three-state view.
--
-- FK semantics:
--   - daily_plan_id → daily_plan(daily_plan_id): NOT NULL. Every
--     planned_recommendation row is scoped to exactly one plan. Cascades
--     are handled by `delete_canonical_plan_cascade` in Python; we do
--     not set ON DELETE CASCADE at the SQL level to keep the cascade
--     logic in one place (matches how recommendation_log does it).
--   - proposal_id → proposal_log(proposal_id): NOT NULL. Every
--     per-domain planned row originated from exactly one proposal. This
--     is the "planned ← proposed" link that makes the full audit chain
--     walkable.
--
-- Invariant: for every (daily_plan_id, domain) pair with a
-- recommendation_log row post-synthesis, there should be a paired
-- planned_recommendation row written in the same atomic transaction.
-- Enforced by the synthesis write path, not the DB — legacy daily_plans
-- from before migration 011 legitimately lack a paired planned row.

CREATE TABLE planned_recommendation (
    planned_id                  TEXT    PRIMARY KEY,
    daily_plan_id               TEXT    NOT NULL REFERENCES daily_plan (daily_plan_id),
    proposal_id                 TEXT    NOT NULL REFERENCES proposal_log (proposal_id),
    user_id                     TEXT    NOT NULL,
    for_date                    TEXT    NOT NULL,
    domain                      TEXT    NOT NULL,

    action                      TEXT    NOT NULL,       -- pre-X-rule action from the source proposal
    confidence                  TEXT    NOT NULL,       -- pre-X-rule confidence
    action_detail_json          TEXT,                   -- pre-X-rule action_detail (nullable: not every domain uses it)

    schema_version              TEXT    NOT NULL,       -- e.g. 'planned_recommendation.v1'
    source                      TEXT    NOT NULL,       -- 'claude_agent_v1' etc
    ingest_actor                TEXT    NOT NULL,
    agent_version               TEXT,
    captured_at                 TEXT    NOT NULL        -- wall-clock moment of capture (= synthesis transaction commit time)
);

-- The two access patterns that matter:
--   1. "Show me the planned view for this plan" →
--      SELECT ... WHERE daily_plan_id = ?
--   2. "Show me the original action for this domain on this date" →
--      SELECT ... WHERE for_date = ? AND user_id = ? AND domain = ?
-- Both covered by the indexes below.

CREATE INDEX idx_planned_recommendation_daily_plan
    ON planned_recommendation (daily_plan_id);

CREATE INDEX idx_planned_recommendation_for_date
    ON planned_recommendation (for_date, user_id, domain);

CREATE INDEX idx_planned_recommendation_proposal
    ON planned_recommendation (proposal_id);
