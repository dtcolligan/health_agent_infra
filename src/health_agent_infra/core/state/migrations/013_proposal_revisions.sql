-- Migration 013 — proposal_log revision semantics.
--
-- Ratified in reporting/plans/v0_1_4/D1_re_author_semantics.md (Dom,
-- 2026-04-23): proposals support in-place revision with forward-linked
-- chains. Replaces the silent-skip-on-duplicate behaviour in
-- project_proposal (which silently dropped agent re-authoring).
--
-- Shape:
--   revision                   — 1-indexed version number within the
--                                chain keyed by
--                                (for_date, user_id, domain). Never
--                                decreases; strictly monotonic per chain.
--   superseded_by_proposal_id  — FK-style forward pointer. NULL iff this
--                                row is the canonical leaf of its chain
--                                (the "current" proposal). Non-NULL rows
--                                are history.
--   superseded_at              — ISO-8601 stamp set when the row is
--                                forward-linked. NULL when superseded_by
--                                is NULL.
--
-- Backfill semantics:
--   Every existing proposal_log row is a single-revision canonical leaf
--   by default. revision=1, superseded_by_proposal_id=NULL,
--   superseded_at=NULL. This matches the pre-migration reality where
--   every (for_date, user_id, domain) key had at most one row.
--
--   The 2026-04-23 demo session left the DB with exactly 6 proposals
--   for that date, all at revision=1 after the manual DELETE + re-post.
--   Earlier chains (if any) would have been invisible to this migration
--   because project_proposal silently skipped duplicates rather than
--   keeping history.
--
-- Index choice:
--   idx_proposal_log_canonical covers the dominant read pattern in
--   read_proposals_for_plan_key (post-revision) which will filter on
--   superseded_by_proposal_id IS NULL to isolate leaves.

ALTER TABLE proposal_log ADD COLUMN revision INTEGER NOT NULL DEFAULT 1;
ALTER TABLE proposal_log ADD COLUMN superseded_by_proposal_id TEXT
    REFERENCES proposal_log(proposal_id);
ALTER TABLE proposal_log ADD COLUMN superseded_at TEXT;

CREATE INDEX idx_proposal_log_canonical
  ON proposal_log(for_date, user_id, domain, superseded_by_proposal_id);
