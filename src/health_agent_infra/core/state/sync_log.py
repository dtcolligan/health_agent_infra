"""Sync-run bookkeeping — write + read helpers for ``sync_run_log``.

Three primitive functions (``begin_sync`` / ``complete_sync`` /
``fail_sync``) map 1:1 to the row lifecycle in migration 008 and cover
the write surface for every sync entry point. A thin context manager
(:func:`sync_run`) stitches them together so callers can wrap a block
without manual try/except scaffolding.

Callers that already manage their own transactions should call the
primitives directly; callers that want the "open row, do work, close
row" ergonomics should use the context manager. Both write to the same
table.

Reader: :func:`latest_successful_sync_per_source` returns the most
recent ``status='ok'`` row per source for a given user. The snapshot's
``sources`` freshness block consumes this.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Any, Iterator, Literal, Optional


SyncStatus = Literal["ok", "partial", "failed"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def begin_sync(
    conn: sqlite3.Connection,
    *,
    source: str,
    user_id: str,
    mode: str,
    for_date: Optional[date] = None,
) -> int:
    """Open a new sync row and return its ``sync_id``.

    The row is inserted with ``status='failed'`` as a pessimistic
    default — a crash between this call and a later :func:`complete_sync`
    leaves the row truthfully reflecting "we started and never
    confirmed." The row is finalised by a following :func:`complete_sync`
    or :func:`fail_sync`.
    """

    cursor = conn.execute(
        "INSERT INTO sync_run_log "
        "(source, user_id, mode, started_at, status, for_date) "
        "VALUES (?, ?, ?, ?, 'failed', ?)",
        (
            source,
            user_id,
            mode,
            _now_iso(),
            for_date.isoformat() if for_date is not None else None,
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def complete_sync(
    conn: sqlite3.Connection,
    sync_id: int,
    *,
    rows_pulled: Optional[int],
    rows_accepted: Optional[int],
    duplicates_skipped: Optional[int],
    status: SyncStatus = "ok",
) -> None:
    """Stamp ``completed_at`` + counts + final status on an open sync row.

    ``status`` defaults to ``'ok'``; pass ``'partial'`` for a fetch that
    succeeded on some field calls and failed on others (surface reserved
    for M6's partial-day recovery). ``'failed'`` is reachable but
    callers that already know they failed should call
    :func:`fail_sync` instead so the error_class / error_message columns
    get populated.
    """

    if status not in ("ok", "partial", "failed"):
        raise ValueError(
            f"complete_sync: status must be one of 'ok','partial','failed'; "
            f"got {status!r}"
        )
    conn.execute(
        "UPDATE sync_run_log SET "
        "  completed_at = ?, status = ?, "
        "  rows_pulled = ?, rows_accepted = ?, duplicates_skipped = ? "
        "WHERE sync_id = ?",
        (_now_iso(), status, rows_pulled, rows_accepted, duplicates_skipped, sync_id),
    )
    conn.commit()


def fail_sync(
    conn: sqlite3.Connection,
    sync_id: int,
    *,
    error_class: str,
    error_message: str,
) -> None:
    """Stamp ``completed_at`` + error metadata on an open sync row.

    ``status`` stays ``'failed'`` (the default from :func:`begin_sync`).
    """

    conn.execute(
        "UPDATE sync_run_log SET "
        "  completed_at = ?, status = 'failed', "
        "  error_class = ?, error_message = ? "
        "WHERE sync_id = ?",
        (_now_iso(), error_class, error_message, sync_id),
    )
    conn.commit()


@contextmanager
def sync_run(
    conn: sqlite3.Connection,
    *,
    source: str,
    user_id: str,
    mode: str,
    for_date: Optional[date] = None,
) -> Iterator[dict[str, Any]]:
    """Context manager wrapping begin/complete/fail.

    Yields a mutable dict the caller fills in before exit:

        with sync_run(conn, source="garmin", user_id=u, mode="csv") as run:
            ...do the work...
            run["rows_pulled"] = 1
            run["rows_accepted"] = 1
            run["duplicates_skipped"] = 0

    On normal exit the values present in the dict are passed to
    :func:`complete_sync` (missing keys → NULL columns). On exception
    :func:`fail_sync` is called with ``error_class = type(exc).__name__``
    and the exception's ``str()`` as the message. The exception then
    re-raises so callers can still handle it.
    """

    sync_id = begin_sync(
        conn,
        source=source,
        user_id=user_id,
        mode=mode,
        for_date=for_date,
    )
    run: dict[str, Any] = {
        "sync_id": sync_id,
        "rows_pulled": None,
        "rows_accepted": None,
        "duplicates_skipped": None,
        "status": "ok",
    }
    try:
        yield run
    except Exception as exc:
        fail_sync(
            conn,
            sync_id,
            error_class=type(exc).__name__,
            error_message=str(exc),
        )
        raise
    else:
        complete_sync(
            conn,
            sync_id,
            rows_pulled=run.get("rows_pulled"),
            rows_accepted=run.get("rows_accepted"),
            duplicates_skipped=run.get("duplicates_skipped"),
            status=run.get("status", "ok"),
        )


def latest_successful_sync_per_source(
    conn: sqlite3.Connection,
    *,
    user_id: str,
) -> dict[str, dict[str, Any]]:
    """Return ``{source: {"sync_id","started_at","completed_at",...}}``.

    One row per source: the most recent ``status='ok'`` run for
    ``user_id``. Sources that never completed successfully are absent
    from the result. Used by ``build_snapshot`` to fill the ``sources``
    freshness block.

    Robust to a DB that predates migration 008: returns an empty dict
    when the table is missing, so the snapshot surface stays alive.
    """

    try:
        rows = conn.execute(
            "SELECT s.* FROM sync_run_log s "
            "INNER JOIN ("
            "  SELECT source, MAX(started_at) AS mx "
            "  FROM sync_run_log "
            "  WHERE user_id = ? AND status = 'ok' "
            "  GROUP BY source"
            ") last ON s.source = last.source AND s.started_at = last.mx "
            "WHERE s.user_id = ? AND s.status = 'ok'",
            (user_id, user_id),
        ).fetchall()
    except sqlite3.OperationalError:
        return {}

    return {row["source"]: dict(row) for row in rows}
