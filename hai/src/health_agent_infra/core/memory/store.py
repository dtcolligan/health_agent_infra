"""SQLite writer / reader for explicit user memory (migration 007).

Three public functions:

- :func:`insert_memory_entry` — append one row. Idempotent on
  ``memory_id``; re-insert returns False instead of raising.
- :func:`archive_memory_entry` — stamp ``archived_at`` on an active row.
  Returns False when the row is already archived or unknown.
- :func:`list_memory_entries` — read rows filtered by user / category /
  include_archived.

All writes go straight to the ``user_memory`` table. No JSONL audit
layer exists for user memory in v1 — the SQLite row is the canonical
record, mirroring ``exercise_taxonomy`` (migration 001) and the
read-only snapshot path (see ``state_model_v1.md`` §1 on single-origin
evidence). The table is the single source of truth the CLI writes and
the snapshot / explain readers read.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from health_agent_infra.core.memory.schemas import (
    UserMemoryEntry,
    validate_category,
    validate_domain,
    validate_value,
)


def insert_memory_entry(
    conn: sqlite3.Connection,
    entry: UserMemoryEntry,
    *,
    commit_after: bool = True,
) -> bool:
    """Append-only insert into ``user_memory``. Idempotent on ``memory_id``.

    Runs the :mod:`schemas` validators on ``category`` / ``value`` /
    ``domain`` before inserting — a caller that bypassed the CLI still
    gets the same invariant coverage.

    Returns ``True`` when a row was inserted, ``False`` when the
    ``memory_id`` was already present (common when reruns hit the same
    deterministic id twice).
    """

    validate_category(entry.category)
    validate_value(entry.value)
    domain = validate_domain(entry.domain)

    existing = conn.execute(
        "SELECT 1 FROM user_memory WHERE memory_id = ?",
        (entry.memory_id,),
    ).fetchone()
    if existing is not None:
        return False

    conn.execute(
        """
        INSERT INTO user_memory (
            memory_id, user_id, category, key, value, domain,
            created_at, archived_at,
            source, ingest_actor
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entry.memory_id,
            entry.user_id,
            entry.category,
            entry.key,
            entry.value,
            domain,
            entry.created_at.isoformat(),
            entry.archived_at.isoformat() if entry.archived_at else None,
            entry.source,
            entry.ingest_actor,
        ),
    )
    if commit_after:
        conn.commit()
    return True


def archive_memory_entry(
    conn: sqlite3.Connection,
    *,
    memory_id: str,
    archived_at: Optional[datetime] = None,
    commit_after: bool = True,
) -> bool:
    """Stamp ``archived_at`` on an active row.

    Returns ``True`` when a previously-active row was archived in this
    call, ``False`` when the id is unknown or the row is already
    archived. Callers can disambiguate "already archived" vs "unknown"
    via :func:`read_memory_entry`.

    The archive timestamp defaults to ``datetime.now(UTC)`` so the CLI
    does not need to pass it; tests inject a fixed value to keep row
    timestamps deterministic.
    """

    row = conn.execute(
        "SELECT archived_at FROM user_memory WHERE memory_id = ?",
        (memory_id,),
    ).fetchone()
    if row is None:
        return False
    if row["archived_at"] is not None:
        return False

    stamp = archived_at or datetime.now(timezone.utc)
    conn.execute(
        "UPDATE user_memory SET archived_at = ? WHERE memory_id = ?",
        (stamp.isoformat(), memory_id),
    )
    if commit_after:
        conn.commit()
    return True


def read_memory_entry(
    conn: sqlite3.Connection,
    *,
    memory_id: str,
) -> Optional[UserMemoryEntry]:
    """Return the single row for ``memory_id`` or ``None`` when absent."""

    row = conn.execute(
        """
        SELECT memory_id, user_id, category, key, value, domain,
               created_at, archived_at, source, ingest_actor
        FROM user_memory
        WHERE memory_id = ?
        """,
        (memory_id,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_entry(row)


def list_memory_entries(
    conn: sqlite3.Connection,
    *,
    user_id: Optional[str] = None,
    category: Optional[str] = None,
    include_archived: bool = False,
    as_of: Optional[datetime] = None,
) -> list[UserMemoryEntry]:
    """Return memory rows matching the filters, ordered by ``created_at``.

    Filters:

    - ``user_id`` — restrict to one user; ``None`` returns every user.
    - ``category`` — must be one of :data:`USER_MEMORY_CATEGORIES`;
      ``None`` returns every category. Any other value raises
      :class:`~health_agent_infra.core.memory.schemas.UserMemoryValidationError`.
    - ``include_archived`` — default ``False`` excludes rows whose
      ``archived_at`` is set. ``True`` returns every row.
    - ``as_of`` — optional point-in-time filter. When supplied, rows are
      included only when they were active at ``as_of``: ``created_at <=
      as_of`` AND (``archived_at IS NULL`` OR ``archived_at > as_of``).
      This is what the snapshot + explain surfaces use so a given plan's
      bundle reflects the memory that was active at its ``for_date``.

    Order is by ``created_at`` ascending so callers see the oldest
    memory first; the CLI (``hai memory list``) preserves this order.
    """

    if category is not None:
        validate_category(category)

    clauses: list[str] = []
    params: list[object] = []

    if user_id is not None:
        clauses.append("user_id = ?")
        params.append(user_id)
    if category is not None:
        clauses.append("category = ?")
        params.append(category)

    if as_of is not None:
        # Time-travel read: "active at as_of" means the row existed by
        # then (``created_at <= as_of``) AND was not yet archived
        # (``archived_at IS NULL`` OR ``archived_at > as_of``). This
        # subsumes ``include_archived`` — a row archived *after* as_of
        # was genuinely active at as_of and belongs in the bundle
        # regardless of the flag.
        as_of_iso = as_of.isoformat()
        clauses.append("created_at <= ?")
        params.append(as_of_iso)
        clauses.append("(archived_at IS NULL OR archived_at > ?)")
        params.append(as_of_iso)
    elif not include_archived:
        # No time filter: "active now" means archived_at is still NULL.
        clauses.append("archived_at IS NULL")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = (
        "SELECT memory_id, user_id, category, key, value, domain, "  # nosec B608 - clauses built only from internal predicate strings (no user input concatenated); user values bind through params.
        "       created_at, archived_at, source, ingest_actor "
        f"FROM user_memory {where} "
        "ORDER BY created_at, memory_id"
    )
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_entry(row) for row in rows]


def _row_to_entry(row: sqlite3.Row) -> UserMemoryEntry:
    return UserMemoryEntry(
        memory_id=row["memory_id"],
        user_id=row["user_id"],
        category=row["category"],
        key=row["key"],
        value=row["value"],
        domain=row["domain"],
        created_at=datetime.fromisoformat(row["created_at"]),
        archived_at=(
            datetime.fromisoformat(row["archived_at"])
            if row["archived_at"]
            else None
        ),
        source=row["source"],
        ingest_actor=row["ingest_actor"],
    )
