-- Migration 026 — body_comp (W-B / v0.1.17 §2.H).
--
-- Stores user-authored body-composition measurements. v1 is intake-only:
-- no target rows (a `target_type='body_weight_kg'` extension is post-
-- v0.2.x scope), no wearable pull (manual intake only in v1).
--
-- Schema (per PLAN.md §2.H, F-PLAN-09 round-1 ratified):
--   - source enum is single-valued ('user_authored'); the manifest
--     declares `agent_safe=False` and the runtime trusts that
--     declaration. Future cycles can extend the enum + add a W57-style
--     commit gate if agent-proposed body-comp becomes a real use case.
--   - `as_of_date` is denormalised from `measured_at` so the active-day
--     query stays index-friendly without a date() function call.
--   - Multiple measurements per day are valid (fasted morning + post-meal
--     evening = different observations); idempotency is "append, not
--     replace" (OQ-4 round-1 disposition).
--
-- Indexes cover the two dominant read patterns:
--   - "what was the latest weight on day D?" (idx_body_comp_user_asof
--     + ORDER BY measured_at DESC LIMIT 1)
--   - "show me the time series" (idx_body_comp_user_measured)

CREATE TABLE body_comp (
  body_comp_id     TEXT PRIMARY KEY,
  user_id          TEXT NOT NULL,
  measured_at      TEXT NOT NULL,                  -- ISO8601 timestamp
  as_of_date       TEXT NOT NULL,                  -- YYYY-MM-DD
  weight_kg        REAL NOT NULL,
  body_fat_pct     REAL,                           -- optional (NULL allowed)
  source           TEXT NOT NULL DEFAULT 'user_authored'
                     CHECK(source = 'user_authored'),
  ingest_actor     TEXT NOT NULL DEFAULT 'cli',
  notes            TEXT,
  created_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_body_comp_user_asof
  ON body_comp(user_id, as_of_date);

CREATE INDEX idx_body_comp_user_measured
  ON body_comp(user_id, measured_at);
