"""Intent ledger CRUD layer (v0.1.8 W49).

Backed by ``intent_item`` (migration 019). The store enforces:

  - Replacements use ``status='superseded'`` + ``superseded_by_intent_id``,
    never destructive UPDATE on the original row.
  - Archive flips the active row to ``status='archived'`` (no
    successor); active-at-date queries skip both ``superseded`` and
    ``archived``.
  - Agent-authored rows must carry ``source != 'user_authored'`` (the
    common convention is ``source='agent_proposed'``); they MUST land
    with ``status='proposed'`` and require an explicit user-confirm
    step before becoming active. The CLI surface enforces that;
    library callers can write any status they want and the policy
    enforcement happens at the boundary.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Optional


_INTENT_COLUMNS = (
    "intent_id",
    "user_id",
    "domain",
    "scope_type",
    "scope_start",
    "scope_end",
    "intent_type",
    "status",
    "priority",
    "flexibility",
    "payload_json",
    "reason",
    "source",
    "ingest_actor",
    "created_at",
    "effective_at",
    "review_after",
    "supersedes_intent_id",
    "superseded_by_intent_id",
)


_VALID_STATUS = {"proposed", "active", "superseded", "archived"}
_VALID_SCOPE = {"day", "week", "date_range"}
_VALID_INTENT_TYPE = {
    "training_session", "sleep_window", "rest_day",
    "travel", "constraint", "other",
}
_VALID_PRIORITY = {"low", "normal", "high"}
_VALID_FLEX = {"fixed", "flexible", "optional"}


@dataclass
class IntentRecord:
    """In-memory intent_item row. ``payload`` is the decoded JSON; the
    DB column ``payload_json`` is the encoded form."""

    intent_id: str
    user_id: str
    domain: str
    scope_type: str
    scope_start: date
    scope_end: date
    intent_type: str
    status: str
    priority: str
    flexibility: str
    payload: dict[str, Any]
    reason: str
    source: str
    ingest_actor: str
    created_at: datetime
    effective_at: datetime
    review_after: Optional[datetime]
    supersedes_intent_id: Optional[str]
    superseded_by_intent_id: Optional[str]

    def to_row(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "user_id": self.user_id,
            "domain": self.domain,
            "scope_type": self.scope_type,
            "scope_start": self.scope_start.isoformat(),
            "scope_end": self.scope_end.isoformat(),
            "intent_type": self.intent_type,
            "status": self.status,
            "priority": self.priority,
            "flexibility": self.flexibility,
            "payload_json": json.dumps(self.payload, sort_keys=True),
            "reason": self.reason,
            "source": self.source,
            "ingest_actor": self.ingest_actor,
            "created_at": self.created_at.isoformat(),
            "effective_at": self.effective_at.isoformat(),
            "review_after": (
                self.review_after.isoformat()
                if self.review_after is not None
                else None
            ),
            "supersedes_intent_id": self.supersedes_intent_id,
            "superseded_by_intent_id": self.superseded_by_intent_id,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row | dict[str, Any]) -> "IntentRecord":
        d = dict(row)
        return cls(
            intent_id=d["intent_id"],
            user_id=d["user_id"],
            domain=d["domain"],
            scope_type=d["scope_type"],
            scope_start=date.fromisoformat(d["scope_start"]),
            scope_end=date.fromisoformat(d["scope_end"]),
            intent_type=d["intent_type"],
            status=d["status"],
            priority=d["priority"],
            flexibility=d["flexibility"],
            payload=json.loads(d.get("payload_json") or "{}"),
            reason=d.get("reason", ""),
            source=d["source"],
            ingest_actor=d["ingest_actor"],
            created_at=datetime.fromisoformat(d["created_at"]),
            effective_at=datetime.fromisoformat(d["effective_at"]),
            review_after=(
                datetime.fromisoformat(d["review_after"])
                if d.get("review_after") is not None
                else None
            ),
            supersedes_intent_id=d.get("supersedes_intent_id"),
            superseded_by_intent_id=d.get("superseded_by_intent_id"),
        )


class IntentValidationError(ValueError):
    """Raised when a candidate intent row fails the documented invariants."""


def _validate(record: IntentRecord) -> None:
    if record.status not in _VALID_STATUS:
        raise IntentValidationError(
            f"intent.status must be one of {_VALID_STATUS}; got {record.status!r}"
        )
    if record.scope_type not in _VALID_SCOPE:
        raise IntentValidationError(
            f"intent.scope_type must be one of {_VALID_SCOPE}; got {record.scope_type!r}"
        )
    if record.intent_type not in _VALID_INTENT_TYPE:
        raise IntentValidationError(
            f"intent.intent_type must be one of {_VALID_INTENT_TYPE}; got {record.intent_type!r}"
        )
    if record.priority not in _VALID_PRIORITY:
        raise IntentValidationError(
            f"intent.priority must be one of {_VALID_PRIORITY}; got {record.priority!r}"
        )
    if record.flexibility not in _VALID_FLEX:
        raise IntentValidationError(
            f"intent.flexibility must be one of {_VALID_FLEX}; got {record.flexibility!r}"
        )
    if record.scope_end < record.scope_start:
        raise IntentValidationError(
            "intent.scope_end must not precede scope_start"
        )
    # v0.1.8 W57 / Codex P1-2 invariant: agent-proposed rows MUST land
    # as `proposed`. They become `active` only via an explicit
    # user-confirmed `commit_intent` call, never via insert. This is
    # the runtime invariant the CLI surface depends on; enforce it at
    # the store so future code paths cannot bypass it.
    if record.source != "user_authored" and record.status == "active":
        raise IntentValidationError(
            f"intent.source={record.source!r} requires status='proposed' on insert; "
            f"only 'user_authored' may land directly as 'active'. "
            f"Use commit_intent() to promote a proposed row."
        )


def add_intent(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    domain: str,
    intent_type: str,
    scope_start: date,
    scope_end: Optional[date] = None,
    scope_type: str = "day",
    status: str = "active",
    priority: str = "normal",
    flexibility: str = "flexible",
    payload: Optional[dict[str, Any]] = None,
    reason: str = "",
    source: str = "user_authored",
    ingest_actor: str = "cli",
    effective_at: Optional[datetime] = None,
    review_after: Optional[datetime] = None,
    intent_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> IntentRecord:
    """Persist a new intent row. Returns the materialised record.

    ``intent_id`` defaults to a fresh UUID4. ``scope_end`` defaults to
    ``scope_start`` (single-day scope).
    """

    when = now or datetime.now(timezone.utc)
    record = IntentRecord(
        intent_id=intent_id or f"intent_{uuid.uuid4().hex[:12]}",
        user_id=user_id,
        domain=domain,
        scope_type=scope_type,
        scope_start=scope_start,
        scope_end=scope_end or scope_start,
        intent_type=intent_type,
        status=status,
        priority=priority,
        flexibility=flexibility,
        payload=payload or {},
        reason=reason,
        source=source,
        ingest_actor=ingest_actor,
        created_at=when,
        effective_at=effective_at or when,
        review_after=review_after,
        supersedes_intent_id=None,
        superseded_by_intent_id=None,
    )
    _validate(record)
    row = record.to_row()
    cols = ", ".join(_INTENT_COLUMNS)
    placeholders = ", ".join("?" for _ in _INTENT_COLUMNS)
    conn.execute(
        f"INSERT INTO intent_item ({cols}) VALUES ({placeholders})",  # nosec B608 - cols is built from the _INTENT_COLUMNS constant tuple; placeholders are literal "?" tokens.
        tuple(row[c] for c in _INTENT_COLUMNS),
    )
    conn.commit()
    return record


def list_intent(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    domain: Optional[str] = None,
    status: Optional[str] = None,
    intent_type: Optional[str] = None,
) -> list[IntentRecord]:
    """Return every intent row matching the filters, oldest first."""

    sql = "SELECT * FROM intent_item WHERE user_id = ?"
    params: list[Any] = [user_id]
    if domain is not None:
        sql += " AND domain = ?"
        params.append(domain)
    if status is not None:
        sql += " AND status = ?"
        params.append(status)
    if intent_type is not None:
        sql += " AND intent_type = ?"
        params.append(intent_type)
    sql += " ORDER BY created_at, intent_id"
    return [IntentRecord.from_row(r) for r in conn.execute(sql, params).fetchall()]


def list_active_intent(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    as_of_date: date,
    domain: Optional[str] = None,
) -> list[IntentRecord]:
    """Active intent whose scope window covers ``as_of_date``.

    Used by the snapshot integration so the agent reads what the user
    actually intended for the plan date, not every row in the ledger.
    """

    sql = (
        "SELECT * FROM intent_item "
        "WHERE user_id = ? "
        "  AND status = 'active' "
        "  AND scope_start <= ? AND scope_end >= ?"
    )
    params: list[Any] = [user_id, as_of_date.isoformat(), as_of_date.isoformat()]
    if domain is not None:
        sql += " AND domain = ?"
        params.append(domain)
    sql += " ORDER BY domain, created_at, intent_id"
    return [IntentRecord.from_row(r) for r in conn.execute(sql, params).fetchall()]


def commit_intent(
    conn: sqlite3.Connection,
    *,
    intent_id: str,
    user_id: str,
) -> bool:
    """Promote a `proposed` intent row to `active`. The W57-required
    user-gated commit path for agent-proposed rows.

    Returns True when a matching proposed row was found and promoted,
    False when no matching row existed or the row was not in the
    `proposed` state. Idempotent: re-running on an already-active row
    is a no-op (returns False).

    Codex R2-2 invariant: when the row being committed has
    ``supersedes_intent_id`` set, atomically flip the superseded
    parent to ``status='superseded'`` in the same transaction. This
    is the deferred deactivation that ``supersede_intent`` skipped
    for agent-proposed replacements; the user's commit is what
    authorises the parent's deactivation.
    """

    # Look up the row first so we can detect a superseded-parent
    # link before promoting. Using the same WHERE clause as the
    # UPDATE keeps the gate consistent.
    row = conn.execute(
        "SELECT supersedes_intent_id FROM intent_item "
        "WHERE intent_id = ? AND user_id = ? AND status = 'proposed'",
        (intent_id, user_id),
    ).fetchone()
    if row is None:
        return False

    parent_id = row["supersedes_intent_id"]

    cursor = conn.execute(
        "UPDATE intent_item SET status = 'active' "
        "WHERE intent_id = ? AND user_id = ? AND status = 'proposed'",
        (intent_id, user_id),
    )
    if cursor.rowcount > 0 and parent_id is not None:
        # Atomic deferred-supersede: the proposed row that had a
        # supersedes_intent_id pointer becomes active, and the parent
        # row it supersedes flips to superseded in the same commit.
        conn.execute(
            "UPDATE intent_item SET status = 'superseded', "
            "superseded_by_intent_id = ? "
            "WHERE intent_id = ? AND user_id = ?",
            (intent_id, parent_id, user_id),
        )
    conn.commit()
    return cursor.rowcount > 0


def archive_intent(
    conn: sqlite3.Connection,
    *,
    intent_id: str,
    user_id: str,
) -> bool:
    """Flip an existing row to ``status='archived'``. Returns ``True``
    when the row existed (and was either active/proposed/superseded);
    ``False`` if no matching row was found.
    """

    cursor = conn.execute(
        "UPDATE intent_item SET status = 'archived' "
        "WHERE intent_id = ? AND user_id = ?",
        (intent_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def supersede_intent(
    conn: sqlite3.Connection,
    *,
    old_intent_id: str,
    new_record: IntentRecord,
) -> IntentRecord:
    """Insert a replacement intent linked to ``old_intent_id``.

    User-authored supersede (``new_record.source == "user_authored"``)
    flips the old row to ``superseded`` immediately — the user is
    explicitly authorising both the new row and the deactivation in
    one call.

    Agent-proposed supersede (``new_record.source != "user_authored"``)
    inserts the new row as a *proposed* replacement and links its
    ``supersedes_intent_id`` to the old row, but does NOT touch the
    old row's status. The user-gated commit path (``commit_intent``)
    detects the link and atomically flips the old row to
    ``superseded`` at promotion time.

    Codex R2-2 invariant: an agent cannot deactivate a user's
    existing active row without explicit user commit.
    """

    new_record.supersedes_intent_id = old_intent_id
    _validate(new_record)
    row = new_record.to_row()
    cols = ", ".join(_INTENT_COLUMNS)
    placeholders = ", ".join("?" for _ in _INTENT_COLUMNS)
    conn.execute(
        f"INSERT INTO intent_item ({cols}) VALUES ({placeholders})",  # nosec B608 - cols is built from the _INTENT_COLUMNS constant tuple; placeholders are literal "?" tokens.
        tuple(row[c] for c in _INTENT_COLUMNS),
    )
    if new_record.source == "user_authored":
        conn.execute(
            "UPDATE intent_item SET status = 'superseded', "
            "superseded_by_intent_id = ? "
            "WHERE intent_id = ?",
            (new_record.intent_id, old_intent_id),
        )
    # Agent-proposed supersedes leave the old row alone; commit_intent
    # owns the atomic deactivate-on-promotion when supersedes_intent_id
    # is set on the row being committed.
    conn.commit()
    return new_record
