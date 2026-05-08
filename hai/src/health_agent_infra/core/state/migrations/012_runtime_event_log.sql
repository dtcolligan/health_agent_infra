-- Migration 012 — runtime_event_log.
--
-- Records one row per user-facing CLI command invocation (`hai daily`
-- first; others opt in over time). Phase-A onboarding telemetry so a
-- user can answer "did I actually run `hai daily` this week?" from
-- their own local DB without any data leaving the device.
--
-- Distinct from sync_run_log (migration 008) on purpose:
--   - sync_run_log scope = external data acquisition (pull / intake).
--   - runtime_event_log scope = command invocations by the user/agent.
--   A single `hai daily` run may write multiple sync_run_log rows (one
--   per source-pull) but exactly one runtime_event_log row.
--
-- Row lifecycle parallels sync_run_log:
--   1. begin_event inserts with started_at + status='failed' (pessimistic).
--   2. On normal completion, complete_event stamps completed_at +
--      final status + exit_code + duration_ms + optional context_json.
--   3. On exception, fail_event stamps completed_at + error_class +
--      error_message; status stays 'failed'.
--
-- status is 'ok' or 'failed' only — no 'partial'. A command either
-- returned 0 ("ok") or did not ("failed"). The exit_code column carries
-- the exact taxonomy token (OK=0, USER_INPUT=2, TRANSIENT=75, etc.)
-- so downstream tools can distinguish soft failures (non-zero exit) from
-- crashes (exception recorded in error_class).
--
-- context_json is an opaque payload the caller fills in — e.g. for
-- `hai daily`, the overall_status + domain counts. Keeping it as
-- free-form JSON avoids a migration every time a command wants to
-- record a new field.
--
-- Index covers the two dominant read patterns:
--   - "show me the last N `hai daily` runs" (hai stats)
--   - "show me recent runs across all commands" (hai stats default)

CREATE TABLE runtime_event_log (
  event_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  command         TEXT NOT NULL,
  user_id         TEXT,
  started_at      TEXT NOT NULL,
  completed_at    TEXT,
  status          TEXT NOT NULL,
  exit_code       INTEGER,
  duration_ms     INTEGER,
  error_class     TEXT,
  error_message   TEXT,
  context_json    TEXT,
  CHECK (status IN ('ok', 'failed'))
);

CREATE INDEX idx_runtime_event_log_command_date
  ON runtime_event_log(command, started_at DESC);
