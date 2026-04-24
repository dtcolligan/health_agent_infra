-- Migration 016 — review_outcome re-link audit columns.
--
-- Per D1 §review_outcome behavior. When `hai review record` is called
-- against a recommendation whose plan has been superseded, the outcome
-- is re-linked to the canonical leaf plan's matching-domain
-- recommendation so the audit chain has no silent orphans. The original
-- recommendation id plus a short human-readable note are retained as
-- columns so the re-link is queryable (for the WS-E contract test
-- "no outcome points to a superseded rec") and inspectable without
-- round-tripping through the JSONL.
--
-- Both columns are nullable. An outcome recorded against a canonical
-- leaf (the common case) leaves them NULL, matching the shape of every
-- pre-016 row after backfill.
--
-- D1's text originally said "no schema change" for this behavior, but
-- we promote the re-link metadata to columns here because:
--   (a) the contract test is a one-line SQL join instead of a JSONL
--       reprojection, and
--   (b) `hai review summary` can surface re-link counts without
--       replaying the JSONL.

ALTER TABLE review_outcome ADD COLUMN re_linked_from_recommendation_id TEXT;
ALTER TABLE review_outcome ADD COLUMN re_link_note                     TEXT;

CREATE INDEX idx_review_outcome_relink
  ON review_outcome(re_linked_from_recommendation_id)
  WHERE re_linked_from_recommendation_id IS NOT NULL;
