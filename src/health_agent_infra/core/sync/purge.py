"""F-PV14-02 — surgical sync_run_log cleanup.

Per ``reporting/plans/post_v0_1_14/carry_over_findings.md`` §F-PV14-02.

Contract:
- Refuse unless the selectors resolve to ≤ ``MAX_PURGE_ROWS`` rows
  (default 5). Operator-friendly default-deny against bulk-delete
  footguns.
- On commit, write a single ``runtime_event_log`` row tagged
  ``sync_purge`` whose ``context_json`` carries the deleted-row payloads.
  The audit chain stays queryable post-purge.
- ``--dry-run`` returns the matched rows without committing or audit-logging.
- Out of scope: tables other than ``sync_run_log``; symmetric
  ``--db-path``/``--base-dir`` resolution (deferred to v0.1.19 W-FPV14-SYM
  per v0.1.15 IR F-IR-02).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional


# Default-deny safety cap. Above this, the CLI refuses to delete and
# directs the operator to inspect first. The constant lives here so the
# CLI handler and core helpers reference one source of truth.
MAX_PURGE_ROWS: int = 5


@dataclass(frozen=True)
class SyncRow:
    """One row from ``sync_run_log``, projected for the purge audit log."""

    sync_id: int
    source: str
    user_id: str
    mode: str
    started_at: str
    completed_at: Optional[str]
    status: str
    rows_pulled: Optional[int]
    rows_accepted: Optional[int]
    duplicates_skipped: Optional[int]
    for_date: Optional[str]
    error_class: Optional[str]
    error_message: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PurgeResult:
    """Return shape for ``purge_sync_rows``."""

    matched: tuple[SyncRow, ...]
    deleted_count: int
    runtime_event_id: Optional[int]
    dry_run: bool


class PurgeRefusedError(Exception):
    """Raised when selector resolution exceeds ``MAX_PURGE_ROWS``."""

    def __init__(self, count: int, cap: int = MAX_PURGE_ROWS) -> None:
        self.count = count
        self.cap = cap
        super().__init__(
            f"selector matches {count} sync_run_log row(s); refusing to "
            f"purge >{cap} rows in one invocation. Narrow the selector "
            f"(e.g. add --started-after) or invoke `hai sync purge` "
            f"once per affected source."
        )


def resolve_purge_selectors(
    conn: sqlite3.Connection,
    *,
    source: str,
    for_date: Optional[str] = None,
    started_after: Optional[str] = None,
    user_id: Optional[str] = None,
) -> tuple[SyncRow, ...]:
    """Return rows that the purge selectors resolve to. Read-only.

    Selectors compose as AND. ``source`` is required (the contract
    refuses to operate without a per-source scope; nuking all sources
    in one call is exactly the footgun the safety cap exists to
    prevent). ``for_date`` is the civil date the sync was *for*;
    ``started_after`` is an ISO-8601 lower bound on ``started_at``;
    ``user_id`` filters per-user rows.
    """

    where = ["source = ?"]
    params: list[Any] = [source]
    if for_date is not None:
        where.append("for_date = ?")
        params.append(for_date)
    if started_after is not None:
        where.append("started_at > ?")
        params.append(started_after)
    if user_id is not None:
        where.append("user_id = ?")
        params.append(user_id)

    sql = (
        "SELECT sync_id, source, user_id, mode, started_at, completed_at, "  # nosec B608 - WHERE clauses are literal predicates from this function's source; values bind via params.
        "       status, rows_pulled, rows_accepted, duplicates_skipped, "
        "       for_date, error_class, error_message "
        "FROM sync_run_log WHERE " + " AND ".join(where) + " "
        "ORDER BY sync_id"
    )
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    rows: list[SyncRow] = []
    for raw in cur.fetchall():
        row_dict = dict(zip(cols, raw))
        rows.append(SyncRow(**row_dict))
    return tuple(rows)


def purge_sync_rows(
    conn: sqlite3.Connection,
    *,
    source: str,
    for_date: Optional[str] = None,
    started_after: Optional[str] = None,
    user_id: Optional[str] = None,
    dry_run: bool = False,
    cap: int = MAX_PURGE_ROWS,
) -> PurgeResult:
    """Resolve selectors → enforce safety cap → optionally commit.

    Raises :class:`PurgeRefusedError` if the selector resolves to more
    than ``cap`` rows.

    On commit (``dry_run=False``):
      1. Deletes the matched rows from ``sync_run_log``.
      2. Inserts one row into ``runtime_event_log`` with
         ``command='sync purge'`` and ``context_json`` carrying the
         deleted payloads as JSON.

    On ``dry_run=True``: returns the matched rows without DELETE or
    audit insert.
    """

    matched = resolve_purge_selectors(
        conn,
        source=source,
        for_date=for_date,
        started_after=started_after,
        user_id=user_id,
    )

    if len(matched) > cap:
        raise PurgeRefusedError(len(matched), cap)

    if dry_run or not matched:
        return PurgeResult(
            matched=matched,
            deleted_count=0,
            runtime_event_id=None,
            dry_run=dry_run,
        )

    # Commit path. The DELETE + audit INSERT run inside one transaction
    # so an audit-write failure rolls the deletion back rather than
    # leaving the row removed without an audit trail.
    sync_ids = [r.sync_id for r in matched]
    placeholders = ",".join("?" for _ in sync_ids)
    with conn:  # transaction
        conn.execute(
            f"DELETE FROM sync_run_log WHERE sync_id IN ({placeholders})",  # nosec B608
            sync_ids,
        )
        now = datetime.now(timezone.utc).isoformat()
        context_json = json.dumps(
            {
                "selectors": {
                    "source": source,
                    "for_date": for_date,
                    "started_after": started_after,
                    "user_id": user_id,
                },
                "deleted_rows": [r.to_dict() for r in matched],
            },
            sort_keys=True,
        )
        cur = conn.execute(
            "INSERT INTO runtime_event_log "
            "(command, user_id, started_at, completed_at, status, "
            " exit_code, duration_ms, context_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "sync purge",
                user_id,
                now,
                now,
                "ok",
                0,
                0,
                context_json,
            ),
        )
        runtime_event_id = cur.lastrowid

    return PurgeResult(
        matched=matched,
        deleted_count=len(matched),
        runtime_event_id=runtime_event_id,
        dry_run=False,
    )
