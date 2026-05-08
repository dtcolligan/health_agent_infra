-- Migration 014 — daily_plan forward-link for supersede chains.
--
-- Per D1 §Schema changes. The existing implementation stashes the
-- supersede pointer inside daily_plan.synthesis_meta_json as a JSON
-- attribute (`synthesis_meta_json.$.superseded_by`), which works but is
-- query-unfriendly: every "is this plan a leaf?" check requires a
-- json_extract. Canonical-leaf reads become the default query pattern
-- under D1, so we promote the attribute to a dedicated column.
--
-- Direction semantics (D1, aligned with migration 013 for proposal_log):
--   superseded_by_plan_id  — forward pointer, NULL iff canonical leaf.
--   superseded_at          — ISO-8601 stamp set when link is made.
--
-- Backfill: walk existing supersede attributes out of synthesis_meta_json
-- into the new columns. The JSON attribute is retained (not cleared) in
-- this migration so older code paths continue to work during the
-- migration window. A later cleanup can remove the JSON once every read
-- path has been migrated.

ALTER TABLE daily_plan ADD COLUMN superseded_by_plan_id TEXT;
ALTER TABLE daily_plan ADD COLUMN superseded_at TEXT;

UPDATE daily_plan
SET
  superseded_by_plan_id = json_extract(synthesis_meta_json, '$.superseded_by'),
  -- Use validated_at as a conservative backfill stamp; no better signal
  -- exists for when the supersede link was written in pre-014 rows.
  superseded_at = CASE
    WHEN json_extract(synthesis_meta_json, '$.superseded_by') IS NOT NULL
    THEN validated_at
    ELSE NULL
  END
WHERE json_extract(synthesis_meta_json, '$.superseded_by') IS NOT NULL;

CREATE INDEX idx_daily_plan_canonical
  ON daily_plan(for_date, user_id, superseded_by_plan_id);
