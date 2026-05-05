"""W-B store helpers — body-composition measurement persistence.

Mirrors the shape of ``core/target/store.py`` but simpler: single-source
enum, no W57 commit gate, no agent-proposal path.

Validation per PLAN.md §2.H acceptance item 5:
- ``weight_kg`` must be in (20, 250) inclusive.
- ``body_fat_pct`` (optional) must be in (0, 75) when present.
- ``as_of_date`` must parse as ``YYYY-MM-DD``.
- ``measured_at`` must parse as ISO-8601 (with timezone).

Idempotency: append-only. A second invocation for the same
``(user_id, as_of_date)`` produces a second row, not an update —
fasted morning vs post-meal evening are different observations.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from typing import Any, Optional


_WEIGHT_KG_MIN: float = 20.0
_WEIGHT_KG_MAX: float = 250.0
_BODY_FAT_PCT_MIN: float = 0.0
_BODY_FAT_PCT_MAX: float = 75.0


class BodyCompValidationError(ValueError):
    """Raised when a body_comp record fails validation."""


@dataclass(frozen=True)
class BodyCompRecord:
    """One row from ``body_comp``."""

    body_comp_id: str
    user_id: str
    measured_at: datetime
    as_of_date: date
    weight_kg: float
    body_fat_pct: Optional[float]
    source: str
    ingest_actor: str
    notes: Optional[str]
    created_at: Optional[datetime]

    def to_row(self) -> dict[str, Any]:
        """Serialize for ``_emit_json`` output."""

        return {
            "body_comp_id": self.body_comp_id,
            "user_id": self.user_id,
            "measured_at": self.measured_at.isoformat(),
            "as_of_date": self.as_of_date.isoformat(),
            "weight_kg": self.weight_kg,
            "body_fat_pct": self.body_fat_pct,
            "source": self.source,
            "ingest_actor": self.ingest_actor,
            "notes": self.notes,
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
        }


def _validate(
    *,
    weight_kg: float,
    body_fat_pct: Optional[float],
) -> None:
    if not (_WEIGHT_KG_MIN <= weight_kg <= _WEIGHT_KG_MAX):
        raise BodyCompValidationError(
            f"weight_kg={weight_kg} out of range "
            f"({_WEIGHT_KG_MIN}, {_WEIGHT_KG_MAX})"
        )
    if body_fat_pct is not None and not (
        _BODY_FAT_PCT_MIN <= body_fat_pct <= _BODY_FAT_PCT_MAX
    ):
        raise BodyCompValidationError(
            f"body_fat_pct={body_fat_pct} out of range "
            f"({_BODY_FAT_PCT_MIN}, {_BODY_FAT_PCT_MAX})"
        )


def add_body_comp(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    measured_at: datetime,
    as_of_date: date,
    weight_kg: float,
    body_fat_pct: Optional[float] = None,
    ingest_actor: str = "cli",
    notes: Optional[str] = None,
) -> BodyCompRecord:
    """Insert one body_comp row. Validates before insert.

    ``source`` is always ``'user_authored'`` (the table CHECK enforces
    this; v1 ratification per F-PLAN-09 round-1).
    """

    _validate(weight_kg=weight_kg, body_fat_pct=body_fat_pct)

    body_comp_id = f"bc_{uuid.uuid4().hex[:12]}"
    now_utc = datetime.now(timezone.utc)
    record = BodyCompRecord(
        body_comp_id=body_comp_id,
        user_id=user_id,
        measured_at=measured_at,
        as_of_date=as_of_date,
        weight_kg=weight_kg,
        body_fat_pct=body_fat_pct,
        source="user_authored",
        ingest_actor=ingest_actor,
        notes=notes,
        created_at=now_utc,
    )
    with conn:
        conn.execute(
            "INSERT INTO body_comp ("
            "body_comp_id, user_id, measured_at, as_of_date, "
            "weight_kg, body_fat_pct, source, ingest_actor, notes, created_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                record.body_comp_id,
                record.user_id,
                record.measured_at.isoformat(),
                record.as_of_date.isoformat(),
                record.weight_kg,
                record.body_fat_pct,
                record.source,
                record.ingest_actor,
                record.notes,
                record.created_at.isoformat() if record.created_at else None,
            ),
        )
    return record


def list_body_comp(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    as_of_date: Optional[date] = None,
    since: Optional[date] = None,
    until: Optional[date] = None,
) -> tuple[BodyCompRecord, ...]:
    """List rows for a user. Filters compose as AND.

    If ``as_of_date`` is given, returns only rows for that day (ordered
    by measured_at ASC). If ``since`` / ``until`` are given, returns the
    inclusive-range slice. With no date filter, returns every row for
    the user.
    """

    where = ["user_id = ?"]
    params: list[Any] = [user_id]
    if as_of_date is not None:
        where.append("as_of_date = ?")
        params.append(as_of_date.isoformat())
    else:
        if since is not None:
            where.append("date(as_of_date) >= date(?)")
            params.append(since.isoformat())
        if until is not None:
            where.append("date(as_of_date) <= date(?)")
            params.append(until.isoformat())

    sql = (
        "SELECT body_comp_id, user_id, measured_at, as_of_date, "  # nosec B608 - WHERE clauses are literal predicates from this function's source; values bind via params.
        "  weight_kg, body_fat_pct, source, ingest_actor, notes, created_at "
        "FROM body_comp WHERE " + " AND ".join(where) + " "
        "ORDER BY measured_at ASC"
    )
    rows: list[BodyCompRecord] = []
    for raw in conn.execute(sql, params).fetchall():
        cols = [d[0] for d in conn.execute(sql + " LIMIT 0", params).description]
        row_dict = dict(zip(cols, raw))
        rows.append(BodyCompRecord(
            body_comp_id=row_dict["body_comp_id"],
            user_id=row_dict["user_id"],
            measured_at=datetime.fromisoformat(row_dict["measured_at"]),
            as_of_date=date.fromisoformat(row_dict["as_of_date"]),
            weight_kg=float(row_dict["weight_kg"]),
            body_fat_pct=(
                float(row_dict["body_fat_pct"])
                if row_dict["body_fat_pct"] is not None
                else None
            ),
            source=row_dict["source"],
            ingest_actor=row_dict["ingest_actor"],
            notes=row_dict["notes"],
            created_at=(
                datetime.fromisoformat(row_dict["created_at"])
                if row_dict["created_at"]
                else None
            ),
        ))
    return tuple(rows)
