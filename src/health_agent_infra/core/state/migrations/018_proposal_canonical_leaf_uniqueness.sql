-- Migration 018 — partial unique index on proposal_log canonical leaves.
--
-- Codex 2026-04-24 review pushback: the application-level defensive
-- guard in run_synthesis raises SynthesisError if it sees > 1 canonical
-- leaf per (for_date, user_id, domain) chain key, but a DB-level
-- invariant is the belt-and-suspenders that prevents the situation
-- from existing in the first place. With this index in place, any code
-- path that tries to insert a second NULL-superseded_by row for an
-- existing chain key fails atomically at the SQLite layer, BEFORE
-- synthesis ever runs.
--
-- Partial index: only enforces uniqueness when ``superseded_by_proposal_id``
-- IS NULL. Old (superseded) revisions are intentionally allowed to
-- accumulate per chain key — that's the D1 revision-chain audit.
--
-- Idempotent across re-runs (CREATE UNIQUE INDEX IF NOT EXISTS); safe
-- to apply against a DB whose proposal_log is already D1-clean (one
-- canonical leaf per chain key by construction). Will fail loudly
-- against a DB that violates the invariant — exactly the failure mode
-- we want, since silent acceptance would let the next ``hai propose``
-- compound the corruption.

CREATE UNIQUE INDEX IF NOT EXISTS idx_proposal_log_canonical_leaf_unique
  ON proposal_log(for_date, user_id, domain)
  WHERE superseded_by_proposal_id IS NULL;
