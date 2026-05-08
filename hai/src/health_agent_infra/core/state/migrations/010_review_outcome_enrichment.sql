-- Migration 010 — review_outcome enrichment (M4 of the post-v0.1.0
-- hardening plan).
--
-- Adds six optional columns that widen the signal captured on a
-- review outcome. Every column is nullable by design: legacy outcomes
-- (pre-010) carry NULLs, and callers that want only the original
-- yes/no-improved shape stay working without touching anything.
--
-- The shape is intentionally conservative for v1 — it captures what a
-- future learning loop (deliberately deferred per non_goals.md) would
-- need without baking in the learning algorithm itself:
--
--   - ``completed`` — did the user finish the recommended session at
--     all. Distinct from ``followed_recommendation`` which asks
--     "did you do what we suggested" (including any modifications).
--     0 = did not complete, 1 = completed, NULL = not recorded.
--
--   - ``intensity_delta`` — relative intensity the user applied vs
--     the recommendation. TEXT because v1 consumers gather ordinal
--     strings (lighter/same/harder) rather than a continuous value;
--     aggregation maps known strings to ordinals.
--
--   - ``duration_minutes`` — actual session length. Nullable so
--     non-training reviews (e.g. stress check-ins, sleep reviews)
--     don't need to invent a value.
--
--   - ``pre_energy_score`` / ``post_energy_score`` — self-reported
--     energy on a 1–5 scale before and after the session. The delta
--     (post - pre) is the signal an aggregation reports.
--
--   - ``disagreed_firing_ids`` — JSON array of x_rule_firing.firing_id
--     the user marked as "I don't think this rule should have fired."
--     Stored as TEXT (JSON-encoded) to keep it flexible without a
--     second table. Empty array = no disagreements logged; NULL =
--     the disagreement question was not asked.
--
-- No indexes added. These columns are not hot-path join keys — they
-- are read in bulk by ``summarize_review_history`` and occasionally
-- per-outcome by the explain surface. A future index lands only if
-- a concrete query shape demands it.

ALTER TABLE review_outcome ADD COLUMN completed             INTEGER;
ALTER TABLE review_outcome ADD COLUMN intensity_delta       TEXT;
ALTER TABLE review_outcome ADD COLUMN duration_minutes      INTEGER;
ALTER TABLE review_outcome ADD COLUMN pre_energy_score      INTEGER;
ALTER TABLE review_outcome ADD COLUMN post_energy_score     INTEGER;
ALTER TABLE review_outcome ADD COLUMN disagreed_firing_ids  TEXT;
