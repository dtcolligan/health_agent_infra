"""Target ledger CRUD layer (v0.1.8 W50). Mirrors the intent ledger
shape (W49) — replacements use archive/supersession, never destructive
UPDATE; outcomes never auto-mutate targets.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Optional

# W-D arm-2: get_active_macro_targets reuses the W-A target-type tuple
# so the active-window query stays in lockstep across surfaces.
from health_agent_infra.core.intake.presence import NUTRITION_MACRO_TARGET_TYPES


_TARGET_COLUMNS = (
    "target_id",
    "user_id",
    "domain",
    "target_type",
    "status",
    "value_json",
    "unit",
    "lower_bound",
    "upper_bound",
    "effective_from",
    "effective_to",
    "review_after",
    "reason",
    "source",
    "ingest_actor",
    "created_at",
    "supersedes_target_id",
    "superseded_by_target_id",
)


_VALID_STATUS = {"proposed", "active", "superseded", "archived"}
_VALID_TARGET_TYPE = {
    "hydration_ml", "protein_g", "calories_kcal",
    # v0.1.15 W-C (round-4 F-PHASE0-01 Option A): carbs_g + fat_g added
    # to support the `hai target nutrition` 4-row macro convenience
    # command. Migration 025 extends the SQL CHECK in lockstep.
    "carbs_g", "fat_g",
    "sleep_duration_h", "sleep_window", "training_load",
    "other",
}


@dataclass
class TargetRecord:
    target_id: str
    user_id: str
    domain: str
    target_type: str
    status: str
    value: Any
    unit: str
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    effective_from: date
    effective_to: Optional[date]
    review_after: Optional[date]
    reason: str
    source: str
    ingest_actor: str
    created_at: datetime
    supersedes_target_id: Optional[str]
    superseded_by_target_id: Optional[str]

    def to_row(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "user_id": self.user_id,
            "domain": self.domain,
            "target_type": self.target_type,
            "status": self.status,
            "value_json": json.dumps({"value": self.value}, sort_keys=True),
            "unit": self.unit,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "effective_from": self.effective_from.isoformat(),
            "effective_to": (
                self.effective_to.isoformat()
                if self.effective_to is not None
                else None
            ),
            "review_after": (
                self.review_after.isoformat()
                if self.review_after is not None
                else None
            ),
            "reason": self.reason,
            "source": self.source,
            "ingest_actor": self.ingest_actor,
            "created_at": self.created_at.isoformat(),
            "supersedes_target_id": self.supersedes_target_id,
            "superseded_by_target_id": self.superseded_by_target_id,
        }

    @classmethod
    def from_row(cls, row: sqlite3.Row | dict[str, Any]) -> "TargetRecord":
        d = dict(row)
        value_json = d.get("value_json") or "{}"
        decoded = json.loads(value_json)
        return cls(
            target_id=d["target_id"],
            user_id=d["user_id"],
            domain=d["domain"],
            target_type=d["target_type"],
            status=d["status"],
            value=decoded.get("value", decoded),
            unit=d["unit"],
            lower_bound=d.get("lower_bound"),
            upper_bound=d.get("upper_bound"),
            effective_from=date.fromisoformat(d["effective_from"]),
            effective_to=(
                date.fromisoformat(d["effective_to"])
                if d.get("effective_to") is not None
                else None
            ),
            review_after=(
                date.fromisoformat(d["review_after"])
                if d.get("review_after") is not None
                else None
            ),
            reason=d.get("reason", ""),
            source=d["source"],
            ingest_actor=d["ingest_actor"],
            created_at=datetime.fromisoformat(d["created_at"]),
            supersedes_target_id=d.get("supersedes_target_id"),
            superseded_by_target_id=d.get("superseded_by_target_id"),
        )


class TargetValidationError(ValueError):
    """Raised when a candidate target row fails the documented invariants."""


def _validate(record: TargetRecord) -> None:
    if record.status not in _VALID_STATUS:
        raise TargetValidationError(
            f"target.status must be one of {_VALID_STATUS}; got {record.status!r}"
        )
    if record.target_type not in _VALID_TARGET_TYPE:
        raise TargetValidationError(
            f"target.target_type must be one of {_VALID_TARGET_TYPE}; got {record.target_type!r}"
        )
    if (
        record.effective_to is not None
        and record.effective_to < record.effective_from
    ):
        raise TargetValidationError(
            "target.effective_to must not precede effective_from"
        )
    if (
        record.lower_bound is not None
        and record.upper_bound is not None
        and record.lower_bound > record.upper_bound
    ):
        raise TargetValidationError(
            "target.lower_bound must not exceed upper_bound"
        )
    # v0.1.8 W57 / Codex P1-2 invariant: agent-proposed targets MUST
    # land as `proposed`. They become `active` only via an explicit
    # user-confirmed `commit_target` call, never via insert.
    if record.source != "user_authored" and record.status == "active":
        raise TargetValidationError(
            f"target.source={record.source!r} requires status='proposed' on insert; "
            f"only 'user_authored' may land directly as 'active'. "
            f"Use commit_target() to promote a proposed row."
        )


def add_target(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    domain: str,
    target_type: str,
    value: Any,
    unit: str,
    effective_from: date,
    effective_to: Optional[date] = None,
    review_after: Optional[date] = None,
    lower_bound: Optional[float] = None,
    upper_bound: Optional[float] = None,
    status: str = "active",
    reason: str = "",
    source: str = "user_authored",
    ingest_actor: str = "cli",
    target_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> TargetRecord:
    """Persist a new target row. Returns the materialised record."""

    when = now or datetime.now(timezone.utc)
    record = TargetRecord(
        target_id=target_id or f"target_{uuid.uuid4().hex[:12]}",
        user_id=user_id,
        domain=domain,
        target_type=target_type,
        status=status,
        value=value,
        unit=unit,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        effective_from=effective_from,
        effective_to=effective_to,
        review_after=review_after,
        reason=reason,
        source=source,
        ingest_actor=ingest_actor,
        created_at=when,
        supersedes_target_id=None,
        superseded_by_target_id=None,
    )
    _validate(record)
    row = record.to_row()
    cols = ", ".join(_TARGET_COLUMNS)
    placeholders = ", ".join("?" for _ in _TARGET_COLUMNS)
    conn.execute(
        f"INSERT INTO target ({cols}) VALUES ({placeholders})",  # nosec B608 - cols from _TARGET_COLUMNS constant; placeholders are literal "?" tokens.
        tuple(row[c] for c in _TARGET_COLUMNS),
    )
    conn.commit()
    return record


def add_targets_atomic(
    conn: sqlite3.Connection,
    *,
    records: list[TargetRecord],
) -> list[TargetRecord]:
    """Insert multiple TargetRecords in a single BEGIN IMMEDIATE / COMMIT.

    v0.1.15 W-C (per Codex F-R4-01 disposition). The existing
    :func:`add_target` helper commits per call, which would split a
    4-row macro group across 4 separate transactions. This helper
    collects every row's INSERT inside one transaction so the
    `hai target nutrition` convenience command satisfies its atomicity
    contract: any single-row validation or constraint failure rolls
    back the whole group.

    Validates each record via the same :func:`_validate` invariant as
    :func:`add_target` (W57 source/status pairing, target_type +
    status enums, bounds). Validation runs BEFORE the BEGIN IMMEDIATE
    so an early failure doesn't acquire the write lock unnecessarily.

    Returns the list of materialised records on success. Raises
    :class:`TargetValidationError` on validation failure (no rows
    written). Raises :class:`sqlite3.IntegrityError` (and rolls back)
    on a SQL CHECK or PK violation surfaced at INSERT time.

    Used by ``cmd_target_nutrition`` only; existing per-row callers
    continue to use :func:`add_target`.
    """

    if not records:
        return []

    # Validate every record before any DB write — fail-fast on bad
    # input so we don't acquire a transaction lock just to roll back.
    for record in records:
        _validate(record)

    cols = ", ".join(_TARGET_COLUMNS)
    placeholders = ", ".join("?" for _ in _TARGET_COLUMNS)

    conn.execute("BEGIN IMMEDIATE")
    try:
        for record in records:
            row = record.to_row()
            conn.execute(
                f"INSERT INTO target ({cols}) VALUES ({placeholders})",  # nosec B608 - cols from _TARGET_COLUMNS constant; placeholders are literal "?" tokens.
                tuple(row[c] for c in _TARGET_COLUMNS),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return records


def list_target(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    domain: Optional[str] = None,
    status: Optional[str] = None,
    target_type: Optional[str] = None,
) -> list[TargetRecord]:
    """Return every target row matching the filters, oldest first."""

    sql = "SELECT * FROM target WHERE user_id = ?"
    params: list[Any] = [user_id]
    if domain is not None:
        sql += " AND domain = ?"
        params.append(domain)
    if status is not None:
        sql += " AND status = ?"
        params.append(status)
    if target_type is not None:
        sql += " AND target_type = ?"
        params.append(target_type)
    sql += " ORDER BY created_at, target_id"
    return [TargetRecord.from_row(r) for r in conn.execute(sql, params).fetchall()]


def list_active_target(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    as_of_date: date,
    domain: Optional[str] = None,
) -> list[TargetRecord]:
    """Active target rows whose effective window covers ``as_of_date``."""

    sql = (
        "SELECT * FROM target "
        "WHERE user_id = ? "
        "  AND status = 'active' "
        "  AND effective_from <= ? "
        "  AND (effective_to IS NULL OR effective_to >= ?)"
    )
    params: list[Any] = [user_id, as_of_date.isoformat(), as_of_date.isoformat()]
    if domain is not None:
        sql += " AND domain = ?"
        params.append(domain)
    sql += " ORDER BY domain, target_type, created_at, target_id"
    return [TargetRecord.from_row(r) for r in conn.execute(sql, params).fetchall()]


def commit_target(
    conn: sqlite3.Connection,
    *,
    target_id: str,
    user_id: str,
) -> bool:
    """Promote a `proposed` target row to `active`. The W57-required
    user-gated commit path for agent-proposed rows.

    Returns True when a matching proposed row was found and promoted,
    False otherwise. Idempotent.

    Codex R2-2 invariant: when the row being committed has
    ``supersedes_target_id`` set, atomically flip the superseded
    parent to ``status='superseded'`` in the same transaction. This
    is the deferred deactivation that ``supersede_target`` skipped
    for agent-proposed replacements.
    """

    row = conn.execute(
        "SELECT supersedes_target_id FROM target "
        "WHERE target_id = ? AND user_id = ? AND status = 'proposed'",
        (target_id, user_id),
    ).fetchone()
    if row is None:
        return False

    parent_id = row["supersedes_target_id"]

    cursor = conn.execute(
        "UPDATE target SET status = 'active' "
        "WHERE target_id = ? AND user_id = ? AND status = 'proposed'",
        (target_id, user_id),
    )
    if cursor.rowcount > 0 and parent_id is not None:
        conn.execute(
            "UPDATE target SET status = 'superseded', "
            "superseded_by_target_id = ? "
            "WHERE target_id = ? AND user_id = ?",
            (target_id, parent_id, user_id),
        )
    conn.commit()
    return cursor.rowcount > 0


def archive_target(
    conn: sqlite3.Connection,
    *,
    target_id: str,
    user_id: str,
) -> bool:
    cursor = conn.execute(
        "UPDATE target SET status = 'archived' "
        "WHERE target_id = ? AND user_id = ?",
        (target_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def supersede_target(
    conn: sqlite3.Connection,
    *,
    old_target_id: str,
    new_record: TargetRecord,
) -> TargetRecord:
    """Insert a replacement target linked to ``old_target_id``.

    Codex R2-2 invariant: an agent cannot deactivate a user's
    existing active row without explicit user commit. Same shape as
    ``supersede_intent``:

    - User-authored supersede flips the old row immediately.
    - Agent-proposed supersede inserts the new row as proposed +
      links ``supersedes_target_id`` to the old row, but leaves the
      old row alone. ``commit_target`` performs the atomic
      deactivate-on-promotion when the user commits.
    """

    new_record.supersedes_target_id = old_target_id
    _validate(new_record)
    row = new_record.to_row()
    cols = ", ".join(_TARGET_COLUMNS)
    placeholders = ", ".join("?" for _ in _TARGET_COLUMNS)
    conn.execute(
        f"INSERT INTO target ({cols}) VALUES ({placeholders})",  # nosec B608 - cols from _TARGET_COLUMNS constant; placeholders are literal "?" tokens.
        tuple(row[c] for c in _TARGET_COLUMNS),
    )
    if new_record.source == "user_authored":
        conn.execute(
            "UPDATE target SET status = 'superseded', "
            "superseded_by_target_id = ? "
            "WHERE target_id = ?",
            (new_record.target_id, old_target_id),
        )
    conn.commit()
    return new_record


def get_active_macro_targets(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    as_of_date: date,
) -> dict[str, float]:
    """W-D arm-2 (v0.1.17 §2.I) — fetch active macro target values for a day.

    Returns a dict keyed to match
    ``DEFAULT_THRESHOLDS["classify"]["nutrition"]["targets"]`` shape
    (extended for v0.1.17 with ``carbs_target_g`` + ``fat_target_g`` —
    those leaves don't exist in the v0.1.15.1 ``DEFAULT_THRESHOLDS``,
    so the merge in ``build_snapshot()`` adds them when arm-2 fires).

    Returned keys: ``calorie_target_kcal``, ``protein_target_g``,
    ``carbs_target_g``, ``fat_target_g``. A missing target_type produces
    a missing key — callers (the build_snapshot internal merge) decide
    whether partial-target arm-2 should still fire or fall through to
    arm-1 suppression.

    Mirrors the W-A active-window query at
    ``core/intake/presence.py:163-213`` (``compute_target_status``):
    same predicate + same index path. The two methods differ only in
    return shape — presence returns the enum string, this returns
    the value dict.
    """

    placeholders = ",".join("?" for _ in NUTRITION_MACRO_TARGET_TYPES)
    rows = conn.execute(
        # nosec B608 — placeholders are constant "?" derived from a
        # module constant; every value is bound. Same rationale as
        # NUTRITION_MACRO_TARGET_TYPES sites in core/intake/presence.py.
        f"SELECT target_type, value_json FROM target "
        f"WHERE user_id=? AND domain='nutrition' "
        f"AND target_type IN ({placeholders}) "
        f"AND status='active' AND superseded_by_target_id IS NULL "
        f"AND date(effective_from) <= date(?) "
        f"AND (effective_to IS NULL OR date(effective_to) >= date(?))",
        (user_id, *NUTRITION_MACRO_TARGET_TYPES,
         as_of_date.isoformat(), as_of_date.isoformat()),
    ).fetchall()

    # Map target_type → threshold-tree key.
    type_to_key = {
        "calories_kcal": "calorie_target_kcal",
        "protein_g":     "protein_target_g",
        "carbs_g":       "carbs_target_g",
        "fat_g":         "fat_target_g",
    }
    out: dict[str, float] = {}
    for raw in rows:
        target_type = raw["target_type"] if hasattr(raw, "keys") else raw[0]
        value_json = raw["value_json"] if hasattr(raw, "keys") else raw[1]
        key = type_to_key.get(target_type)
        if key is None:
            continue
        decoded = json.loads(value_json)
        value = decoded.get("value", decoded) if isinstance(decoded, dict) else decoded
        out[key] = float(value)
    return out
