-- v0.1.11 W-E: daily_plan.state_fingerprint
--
-- Records a deterministic hash of the synthesis inputs (proposal
-- payloads + snapshot fingerprint surfaces) at commit time. A
-- subsequent run_synthesis call compares against this column to
-- decide between no-op (same state → return existing plan) and
-- auto-supersession (state materially changed → write `_v<N>`).
--
-- Codex F-PLAN-R2-04 read-consistency contract is preserved at the
-- run_synthesis layer; this column is a write-side derivation only.
--
-- Backwards-compatible additive. Existing rows get NULL; the
-- comparison code treats NULL-fingerprint as "always re-synthesize"
-- so legacy plans don't trigger spurious no-ops.

ALTER TABLE daily_plan ADD COLUMN state_fingerprint TEXT;
