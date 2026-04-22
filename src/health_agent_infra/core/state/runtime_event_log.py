"""Runtime event bookkeeping — write + read helpers for ``runtime_event_log``.

Mirror of :mod:`sync_log` scoped to CLI command invocations rather than
external sync acquisitions. Three primitive functions (``begin_event`` /
``complete_event`` / ``fail_event``) map 1:1 to the row lifecycle in
migration 012; a context manager (:func:`runtime_event`) stitches them
together and handles the common "open row, run body, close row" flow
including best-effort fallback when the DB doesn't exist yet (e.g.
before ``hai init`` has run).

Readers (:func:`recent_events`, :func:`command_summary`) back the
``hai stats`` view: they answer "did the user run `hai daily` this
week?" and "what's the failure rate?" from local data the user owns.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Literal, Optional


RuntimeStatus = Literal["ok", "failed"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def begin_event(
    conn: sqlite3.Connection,
    *,
    command: str,
    user_id: Optional[str] = None,
) -> int:
    """Open a new runtime event row; return its ``event_id``.

    Inserted with ``status='failed'`` — a crash between this call and a
    later completion leaves the row truthfully reflecting "we started
    and never confirmed." Finalised by a later :func:`complete_event`
    or :func:`fail_event`.
    """

    cursor = conn.execute(
        "INSERT INTO runtime_event_log "
        "(command, user_id, started_at, status) "
        "VALUES (?, ?, ?, 'failed')",
        (command, user_id, _now_iso()),
    )
    conn.commit()
    return int(cursor.lastrowid)


def complete_event(
    conn: sqlite3.Connection,
    event_id: int,
    *,
    status: RuntimeStatus,
    exit_code: Optional[int] = None,
    duration_ms: Optional[int] = None,
    context: Optional[dict[str, Any]] = None,
) -> None:
    """Stamp completion metadata + final status on an open runtime event.

    ``status`` is either 'ok' or 'failed'. Callers with an exception
    should use :func:`fail_event` instead so the error_class /
    error_message columns get populated.
    """

    if status not in ("ok", "failed"):
        raise ValueError(
            f"complete_event: status must be 'ok' or 'failed'; got {status!r}"
        )
    conn.execute(
        "UPDATE runtime_event_log SET "
        "  completed_at = ?, status = ?, "
        "  exit_code = ?, duration_ms = ?, context_json = ? "
        "WHERE event_id = ?",
        (
            _now_iso(),
            status,
            exit_code,
            duration_ms,
            json.dumps(context) if context is not None else None,
            event_id,
        ),
    )
    conn.commit()


def fail_event(
    conn: sqlite3.Connection,
    event_id: int,
    *,
    error_class: str,
    error_message: str,
    exit_code: Optional[int] = None,
    duration_ms: Optional[int] = None,
    context: Optional[dict[str, Any]] = None,
) -> None:
    """Stamp completion + exception metadata; status stays 'failed'."""

    conn.execute(
        "UPDATE runtime_event_log SET "
        "  completed_at = ?, status = 'failed', "
        "  exit_code = ?, duration_ms = ?, "
        "  error_class = ?, error_message = ?, context_json = ? "
        "WHERE event_id = ?",
        (
            _now_iso(),
            exit_code,
            duration_ms,
            error_class,
            error_message,
            json.dumps(context) if context is not None else None,
            event_id,
        ),
    )
    conn.commit()


@contextmanager
def runtime_event(
    db_path: Optional[Path],
    *,
    command: str,
    user_id: Optional[str] = None,
) -> Iterator[dict[str, Any]]:
    """Context manager wrapping begin/complete/fail.

    Best-effort: a missing DB file or a pre-migration-012 schema turns
    the block into a no-op so commands that run before state init (or
    against an old DB) still function. The caller fills the yielded dict
    to influence the finalisation:

        with runtime_event(db_path, command="daily", user_id=u) as evt:
            rc = _do_the_work()
            evt["exit_code"] = rc
            evt["context"] = {"overall_status": "complete"}

    On normal exit, status is derived from ``exit_code`` (0 → 'ok', else
    'failed') unless the caller overrides ``evt["status"]``. On
    exception, :func:`fail_event` is called with the exception's class
    and message; the exception then re-raises.
    """

    if db_path is None or not Path(db_path).exists():
        # DB doesn't exist — e.g. pre-init. Yield a harmless dict so the
        # body still runs; logging is just silently skipped.
        yield {"event_id": None, "exit_code": None, "context": None, "status": None}
        return

    # Local imports keep this module's test surface free of circular
    # dependencies on the broader state package.
    from health_agent_infra.core.state.store import open_connection

    try:
        conn = open_connection(Path(db_path))
    except sqlite3.Error:
        yield {"event_id": None, "exit_code": None, "context": None, "status": None}
        return

    try:
        try:
            event_id = begin_event(conn, command=command, user_id=user_id)
        except sqlite3.OperationalError:
            # Pre-migration-012 DB: silently skip logging.
            yield {"event_id": None, "exit_code": None, "context": None, "status": None}
            return

        started_dt = datetime.now(timezone.utc)
        ctx: dict[str, Any] = {
            "event_id": event_id,
            "exit_code": None,
            "context": None,
            "status": None,
        }
        try:
            yield ctx
        except Exception as exc:
            duration_ms = _elapsed_ms(started_dt)
            fail_event(
                conn,
                event_id,
                error_class=type(exc).__name__,
                error_message=str(exc),
                exit_code=ctx.get("exit_code"),
                duration_ms=duration_ms,
                context=ctx.get("context"),
            )
            raise
        else:
            duration_ms = _elapsed_ms(started_dt)
            # Explicit override wins; otherwise derive from exit_code.
            explicit_status = ctx.get("status")
            if explicit_status in ("ok", "failed"):
                final_status: RuntimeStatus = explicit_status  # type: ignore[assignment]
            else:
                exit_code = ctx.get("exit_code")
                final_status = "ok" if exit_code == 0 else "failed"
            complete_event(
                conn,
                event_id,
                status=final_status,
                exit_code=ctx.get("exit_code"),
                duration_ms=duration_ms,
                context=ctx.get("context"),
            )
    finally:
        conn.close()


def _elapsed_ms(started_dt: datetime) -> int:
    return int((datetime.now(timezone.utc) - started_dt).total_seconds() * 1000)


def recent_events(
    conn: sqlite3.Connection,
    *,
    command: Optional[str] = None,
    limit: int = 7,
) -> list[dict[str, Any]]:
    """Return the most recent runtime events (optionally filtered by command).

    Ordered newest → oldest. Robust to a DB that predates migration 012:
    returns an empty list so downstream rendering stays alive.
    """

    try:
        if command is not None:
            rows = conn.execute(
                "SELECT * FROM runtime_event_log "
                "WHERE command = ? "
                "ORDER BY started_at DESC LIMIT ?",
                (command, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM runtime_event_log "
                "ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    except sqlite3.OperationalError:
        return []
    return [dict(row) for row in rows]


def command_summary(conn: sqlite3.Connection) -> dict[str, dict[str, int]]:
    """Aggregate counts per (command, status).

    Returns a dict shaped ``{command: {"ok": N, "failed": M, "total": N+M}}``.
    Empty dict when the table is missing.
    """

    try:
        rows = conn.execute(
            "SELECT command, status, COUNT(*) AS n "
            "FROM runtime_event_log "
            "GROUP BY command, status"
        ).fetchall()
    except sqlite3.OperationalError:
        return {}

    summary: dict[str, dict[str, int]] = {}
    for row in rows:
        command = row["command"]
        status = row["status"]
        n = int(row["n"])
        bucket = summary.setdefault(command, {"ok": 0, "failed": 0, "total": 0})
        bucket[status] = n
        bucket["total"] += n
    return summary
