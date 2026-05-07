-- Migration 007 — explicit user memory (Phase D of the post-v0.1.0 roadmap).
--
-- Per `reporting/plans/historical/post_v0_1_roadmap.md` §5 Phase D and
-- `docs/hai/memory_model.md` §2.1, this adds the first-class
-- user-memory layer: goals, preferences, constraints, and durable
-- context notes as inspectable local SQLite state.
--
-- Why a single table with a `category` column rather than four tables:
--   - All four categories share the same audit shape (append-only rows
--     carrying value + optional key + optional domain scope + created_at
--     + archived_at).
--   - Read surfaces (snapshot + explain) emit one `user_memory` block
--     grouped by category; a single table keeps the read path a single
--     SELECT rather than four.
--   - The CHECK constraint pins the allowed enum — any drift surfaces
--     at INSERT, not at read time.
--
-- Semantics:
--   - Append-only. `hai memory set` always inserts a new row; to replace
--     a preference the operator archives the old one and sets a new one.
--     This mirrors the project-wide "no silent overwrites" invariant —
--     every change is visible as a distinct row + its archive timestamp.
--   - `archived_at IS NULL` marks an active entry; the read surfaces
--     filter on this column.
--   - `created_at` is the wall-clock moment the entry was recorded; it
--     is also the time-axis key the snapshot / explain readers use when
--     they need a point-in-time "memory active at plan date" view.
--   - `key` is optional: an operator may give a preference a short
--     handle (e.g. `primary_goal`, `injury_left_knee`) for later
--     reference, but it is not required and is not unique.
--   - `domain` is optional: an entry may be scoped to one of the six
--     domains (recovery / running / sleep / stress / strength /
--     nutrition) or left global.
--
-- Provenance columns follow the conventions in state_model_v1.md §4:
--   - `source` records the fact origin (typically 'user_manual').
--   - `ingest_actor` records what transported the fact (typically
--     'hai_cli_direct' or 'claude_agent_v1').
--
-- Policy invariant (re-stated from memory_model.md §2.1):
--   - Nothing in this layer feeds back into thresholds, classifiers,
--     policy, or X-rules. User memory is bounded read-only context
--     exposed to snapshot / explain / skills. It is not an adaptation
--     channel.

CREATE TABLE user_memory (
    memory_id       TEXT    PRIMARY KEY,
    user_id         TEXT    NOT NULL,
    category        TEXT    NOT NULL CHECK (category IN (
        'goal', 'preference', 'constraint', 'context'
    )),
    key             TEXT,
    value           TEXT    NOT NULL,
    domain          TEXT,
    created_at      TEXT    NOT NULL,
    archived_at     TEXT,

    source          TEXT    NOT NULL,
    ingest_actor    TEXT    NOT NULL
);

CREATE INDEX idx_user_memory_active
    ON user_memory (user_id, archived_at, category);

CREATE INDEX idx_user_memory_created_at
    ON user_memory (user_id, created_at);
