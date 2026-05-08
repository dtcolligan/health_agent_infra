-- Migration 028 — weekly_claim_card (W-EVCARD-WEEKLY / v0.2.0 §2.C).
--
-- The weekly evidence-card carrier consumed by W52 weekly review +
-- W58D deterministic factuality gate. One row per quantitative or
-- comparative atomic claim emitted by W52's prose builder. Qualitative
-- atoms emit no card (per F-PLAN-10 round-1 alignment + the
-- mechanical non-factual assertion in W52 acceptance #6).
--
-- Append-only audit history (Codex Q1 disposition, round-1 + maintainer
-- rigor preference per `feedback_pick_rigor_over_velocity.md`):
-- re-running W52 for the same week with corrected data produces a new
-- card row (new UUID-suffixed card_id, same claim_id, newer
-- computed_at); superseded cards remain. The latest card per
-- (iso_week, user_id, claim_id) is the canonical view; superseded
-- cards remain as audit history. The PRIMARY KEY is `card_id` only;
-- there is intentionally no UNIQUE constraint on (iso_week, user_id,
-- claim_id).
--
-- Payload separation per F-PHASE0-12: `locator_set_json` carries
-- SourceRowLocator-shaped dicts validated against the W-PROV-1
-- whitelist. `audit_refs_json` carries write-side primary-key
-- references as a JSON object with one key per audit-chain table —
-- these are NOT SourceRowLocator instances and bypass the W-PROV-1
-- whitelist (audit-chain rows are write-side, not evidence-side).
--
-- claim_id is a stable content hash; same prose content → same
-- claim_id. Re-running W52 for the same week with same data is
-- idempotent at the *content* level: a new row is appended only
-- when the prose or the underlying derivation changes.

CREATE TABLE weekly_claim_card (
  card_id              TEXT PRIMARY KEY,
  user_id              TEXT NOT NULL,
  iso_week             TEXT NOT NULL,
  claim_id             TEXT NOT NULL,
  claim_atom_text      TEXT NOT NULL,
  atom_type            TEXT NOT NULL,
  derivation_path      TEXT NOT NULL,
  locator_set_json     TEXT NOT NULL,
  audit_refs_json      TEXT NOT NULL,
  computed_at          TEXT NOT NULL,
  source               TEXT NOT NULL,
  ingest_actor         TEXT NOT NULL,
  agent_version        TEXT,
  CHECK (atom_type IN ('quantitative', 'comparative'))
);
CREATE INDEX idx_weekly_card_iso_week
  ON weekly_claim_card (iso_week, user_id);
CREATE INDEX idx_weekly_card_claim_id
  ON weekly_claim_card (claim_id, computed_at DESC);
