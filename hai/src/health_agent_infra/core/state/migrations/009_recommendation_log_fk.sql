-- Migration 009 — recommendation_log.daily_plan_id column (M3 of the
-- post-v0.1.0 hardening plan).
--
-- Problem solved. Until now the linkage between ``recommendation_log``
-- and ``daily_plan`` lived inside the recommendation's ``payload_json``
-- blob. Readers that needed the join (the explain bundle loader,
-- the cascade-delete path in ``delete_canonical_plan_cascade``) had to
-- ``json_extract(payload_json, '$.daily_plan_id')`` on every row — not
-- indexable, not enforceable, and subtle to grep for.
--
-- This migration lifts the id into a proper column + index so the
-- join is a regular B-tree lookup and the relationship is visible in
-- the schema rather than hidden inside a JSON string.
--
-- SQLite specifics.
--   - We add the column as nullable. A strict ``NOT NULL`` would
--     require a default for the backfill UPDATE and would tangle the
--     legacy ``project_recommendation`` path (writeback) which has no
--     plan id. Nullable + "set on insert where known, leave NULL
--     otherwise" keeps the write surface honest.
--   - We do not retrofit an actual foreign-key constraint. SQLite
--     cannot add FKs to an existing table in place (it would require
--     a rebuild-and-rename). The invariant is enforced by the write
--     path instead: ``project_bounded_recommendation`` and the JSONL
--     reproject path now pass ``daily_plan_id`` as a kwarg, and
--     ``delete_canonical_plan_cascade`` reads by column on the way
--     out. Any future FK retrofit would happen in a dedicated
--     "rebuild recommendation_log with FK" migration.
--
-- Backfill. Every existing recommendation that was synthesised via
-- ``run_synthesis`` already carries ``daily_plan_id`` inside its
-- payload; we copy it out. Legacy writeback-produced rows (pre-3
-- recovery-only path) have no ``daily_plan_id`` in payload and stay
-- NULL after the backfill — which is correct, they belong to no plan.

ALTER TABLE recommendation_log
  ADD COLUMN daily_plan_id TEXT;

UPDATE recommendation_log
   SET daily_plan_id = json_extract(payload_json, '$.daily_plan_id')
 WHERE daily_plan_id IS NULL;

CREATE INDEX idx_recommendation_log_daily_plan_id
  ON recommendation_log(daily_plan_id);
