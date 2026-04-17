-- Migration 002 — rename `training_readiness_pct` to
-- `training_readiness_component_mean_pct` on accepted_recovery_state_daily.
--
-- The original name implied this column holds Garmin's own pre-computed
-- overall Training Readiness percentage. It does not: Garmin doesn't
-- export that overall number in daily_summary_export.csv, only the five
-- component pcts. The runtime computes a plain arithmetic mean as a
-- proxy, which can disagree with Garmin's own internal weighting (and
-- has been observed to disagree on real data — e.g. 2026-04-08 showed
-- training_readiness_level='LOW' while the computed mean was 70.0).
--
-- Renaming makes the provenance explicit at every use site. The stored
-- semantics (round(mean(5 components), 1); NULL if any component is
-- missing) are unchanged.

ALTER TABLE accepted_recovery_state_daily
    RENAME COLUMN training_readiness_pct TO training_readiness_component_mean_pct;
