-- Migration 008 — sync_run_log (M2 of the post-v0.1.0 hardening plan).
--
-- Records one row per sync entry point invocation (``hai pull`` +
-- ``hai intake *``) so freshness ("when did each source last succeed?")
-- is a single SELECT away instead of requiring the operator to scan
-- JSONL files. See the hardening plan §M2.
--
-- Row lifecycle:
--   1. ``begin_sync`` inserts with ``started_at`` + ``status='failed'``
--      (pessimistic default — a crash between begin and complete leaves
--      the row in a truthful "we started and never confirmed" state).
--   2. On success, ``complete_sync`` updates ``completed_at`` +
--      ``status='ok'`` (or ``'partial'`` for partial-success fetches
--      deferred to M6) + the three counts.
--   3. On exception, ``fail_sync`` stamps ``completed_at`` +
--      ``error_class`` + ``error_message``; ``status`` stays
--      ``'failed'``.
--
-- Counts (``rows_pulled``, ``rows_accepted``, ``duplicates_skipped``)
-- are nullable: not every source has a meaningful count. For a
-- single-day Garmin pull, ``rows_pulled=1`` (the raw daily row is the
-- unit); for a gym intake, ``rows_pulled=len(sets)``. Callers that
-- don't produce meaningful counts leave them NULL rather than inventing
-- zeros.
--
-- ``for_date`` is the civil date the sync was *for* (the ``as_of``
-- argument). It is NULL when a sync doesn't carry a civil-date frame.
--
-- The index covers the snapshot's freshness query:
--   "SELECT ... FROM sync_run_log
--    WHERE source = ? AND user_id = ? AND status = 'ok'
--    ORDER BY started_at DESC LIMIT 1"
-- The (source, user_id, started_at DESC) leading keys match that
-- predicate exactly; status is filtered post-index-scan but the
-- working set per (source, user_id) is small.

CREATE TABLE sync_run_log (
  sync_id            INTEGER PRIMARY KEY AUTOINCREMENT,
  source             TEXT NOT NULL,
  user_id            TEXT NOT NULL,
  mode               TEXT NOT NULL,
  started_at         TEXT NOT NULL,
  completed_at       TEXT,
  status             TEXT NOT NULL,
  rows_pulled        INTEGER,
  rows_accepted      INTEGER,
  duplicates_skipped INTEGER,
  for_date           TEXT,
  error_class        TEXT,
  error_message      TEXT,
  CHECK (status IN ('ok','partial','failed'))
);

CREATE INDEX idx_sync_run_log_source_user_date
  ON sync_run_log(source, user_id, started_at DESC);
