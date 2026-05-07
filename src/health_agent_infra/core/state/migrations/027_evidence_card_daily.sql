-- Migration 027 — recommendation_evidence_card (W-EVCARD-DAILY / v0.2.0 §2.B).
--
-- The daily evidence-card carrier. One row per recommendation_log row at
-- synthesis-commit time; carries the per-recommendation provenance payload
-- (decision, evidence, source_quality, provenance, conflicts, review lanes
-- per `reporting/plans/future_strategy_2026-04-29/review_codex.md:1480-1545`).
--
-- v0.2.0 ships the carrier; W52 weekly review consumes it; v0.2.2 W58J
-- judge harness consumes the daily-recommendation factuality lane. The
-- weekly claim-card surface (migration 028) is a SEPARATE table per
-- F-PHASE0-09 — daily and weekly cards have different keying contracts.
--
-- W-PROV-1 contract (source_row_provenance.md:42-46) preserved: the
-- `accepted_state_rows` and `raw_source_refs` arrays inside payload_json
-- carry SourceRowLocator-shaped dicts pointing at evidence + accepted-
-- state tables only. Write-side audit-chain references
-- (recommendation_id, planned_id, proposal_id, x_rule_firing.id) live in
-- separate payload-lane fields and are validated as plain primary keys,
-- NOT as SourceRowLocator instances. F-PHASE0-12.
--
-- Cardinality (per maintainer Q1 adjudication, default per-recommendation):
-- one card per row in `recommendation_log` at insert time. When a new
-- `planned_recommendation` supersedes an existing one, the new
-- recommendation_log row gets its own card; the old card remains as
-- audit history.
--
-- Atomic commit: the project layer writes cards INSIDE the synthesis
-- transaction post-recommendation-log + planned-recommendation rows;
-- rollback if any insert fails (acceptance #2 + #3).
--
-- Indexes cover the two dominant read patterns:
--   - "show me all evidence cards for the requested plan day" (W52
--     weekly review + `hai explain`'s consumer extension)
--   - "find the card behind a specific recommendation_id" (the
--     W58D factuality gate's audit-chain anchor)

-- FK semantics:
--   * daily_plan_id + recommendation_id are NOT NULL; the synthesis
--     transaction's delete_canonical_plan_cascade deletes evidence
--     cards explicitly BEFORE the recommendation_log + daily_plan
--     rows are deleted, so the FK never trips. No ON DELETE clause
--     because nothing should ever delete a card without going
--     through the cascade.
--   * planned_id + proposal_id use ON DELETE SET NULL so that any
--     post-hoc audit operation that prunes planned_recommendation
--     or proposal_log rows leaves the card as an audit-trail
--     record (with the optional refs nulled) rather than failing
--     the prune. The card itself is the persistent claim about
--     "what we recommended"; the planned + proposal rows are
--     pre-recommendation provenance.
CREATE TABLE recommendation_evidence_card (
  card_id              TEXT PRIMARY KEY,
  daily_plan_id        TEXT NOT NULL REFERENCES daily_plan(daily_plan_id),
  recommendation_id    TEXT NOT NULL REFERENCES recommendation_log(recommendation_id),
  planned_id           TEXT REFERENCES planned_recommendation(planned_id) ON DELETE SET NULL,
  proposal_id          TEXT REFERENCES proposal_log(proposal_id) ON DELETE SET NULL,
  user_id              TEXT NOT NULL,
  for_date             TEXT NOT NULL,
  domain               TEXT NOT NULL,
  schema_version       TEXT NOT NULL,
  payload_json         TEXT NOT NULL,
  computed_at          TEXT NOT NULL,
  source               TEXT NOT NULL,
  ingest_actor         TEXT NOT NULL,
  agent_version        TEXT
);
CREATE INDEX idx_evidence_card_for_date
  ON recommendation_evidence_card (for_date, user_id);
CREATE INDEX idx_evidence_card_recommendation
  ON recommendation_evidence_card (recommendation_id);
