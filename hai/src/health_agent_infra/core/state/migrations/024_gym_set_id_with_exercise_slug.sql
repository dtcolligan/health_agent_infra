-- Migration 024 — gym_set.set_id format extension to include exercise slug.
--
-- v0.1.15 W-GYM-SETID. The pre-024 deterministic_set_id format
-- `set_{session_id}_{set_number:03d}` collided whenever a session contained
-- multiple exercises with overlapping set numbers (the common multi-exercise
-- case — every exercise restarts at set 1). INSERT OR IGNORE silently
-- dropped sets 2..N. New format includes the normalized exercise_name slug
-- (`exercise_name.strip().casefold()`, mirroring `_norm` at
-- `core/state/projectors/strength.py:66`) so each (session, exercise,
-- set_number) is uniquely addressable.
--
-- Migration scope (per PLAN §2.A):
--   * In scope: existing `gym_set` rows whose set_id matches the OLD
--     deterministic format `set_{session_id}_{set_number:03d}` get
--     rewritten to the new format. Supersession references that point
--     at those rewritten rows are updated in lockstep.
--   * Preserved as-is: rows with custom user-supplied set_ids
--     (correction rows that ship via bulk JSON `--session-json` per
--     `domains/strength/intake.py:96-105`). These are opaque by design,
--     do not match the OLD format predicate, and would collide with
--     post-rewrite rows if rewritten by the same derivation. Their
--     incoming supersession references are still rewritten to the new
--     target id.
--   * Out of scope: rows that exist in `gym_sessions.jsonl` but were
--     silently dropped at intake. Recovery is the operator-only
--     `hai state reproject --base-dir <d> --cascade-synthesis` path
--     (handler `cmd_state_reproject` at `cli.py:4111`).
--
-- The OLD-format predicate `set_id = 'set_' || session_id || '_' ||
-- printf('%03d', set_number)` is the precise filter. Rows already in
-- NEW format (e.g., re-runs) won't match either, so the migration is
-- idempotent under repeat application.

-- Step 1: Rewrite supersedes_set_id references that point at rows whose
-- set_id matches the OLD format. Custom-id supersession targets keep
-- their existing reference.
UPDATE gym_set
SET supersedes_set_id = (
    SELECT 'set_' || target.session_id || '_' ||
           LOWER(TRIM(target.exercise_name)) || '_' ||
           printf('%03d', target.set_number)
    FROM gym_set AS target
    WHERE target.set_id = gym_set.supersedes_set_id
      AND target.set_id = 'set_' || target.session_id || '_'
                          || printf('%03d', target.set_number)
)
WHERE supersedes_set_id IS NOT NULL
  AND supersedes_set_id IN (
      SELECT set_id FROM gym_set
      WHERE set_id = 'set_' || session_id || '_'
                     || printf('%03d', set_number)
  );

-- Step 2: Rewrite each row's own set_id where it matches the OLD format.
-- SQLite's LOWER and TRIM cover ASCII; existing taxonomy is English
-- exercise names so the ASCII-only branch matches Python's .casefold()
-- exactly. Non-ASCII names (out-of-scope at v0.1.15) would diverge from
-- intake-time slugs.
UPDATE gym_set
SET set_id = 'set_' || session_id || '_' ||
             LOWER(TRIM(exercise_name)) || '_' ||
             printf('%03d', set_number)
WHERE set_id = 'set_' || session_id || '_' || printf('%03d', set_number);
