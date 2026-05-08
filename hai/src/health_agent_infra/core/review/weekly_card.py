"""Weekly claim-card carrier — W-EVCARD-WEEKLY (v0.2.0 §2.C).

Builds and persists ``weekly_claim_card`` rows. One row per
quantitative or comparative atomic claim in W52's prose. Qualitative
atoms emit no card per F-PLAN-10. The W52 weekly-review surface
(§2.D, separate workstream) consumes this module to emit cards as it
authors prose; W58D consumes the persisted cards via the canonical-
latest view.

Append-only audit history per Codex Q1 disposition: re-running W52
for the same week with corrected data produces a new row with a new
UUID-suffixed ``card_id`` and a newer ``computed_at``; superseded
cards remain. Idempotency is at the content level — same prose +
same derivation → same ``claim_id``, but a new row is appended only
if any field changed.

Payload separation per F-PHASE0-12:
  * ``locator_set_json`` — SourceRowLocator-shaped dicts validated
    against the W-PROV-1 whitelist (evidence + accepted-state
    tables only).
  * ``audit_refs_json`` — JSON object keyed by audit-chain table
    name; values are arrays of plain primary keys. NOT
    SourceRowLocator instances. Bypasses the W-PROV-1 whitelist
    intentionally; audit-chain rows are write-side, not evidence-
    side.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from typing import Any, Iterable, Optional

from health_agent_infra.core.provenance.locator import (
    LocatorValidationError,
    validate_locator,
)
from health_agent_infra.core.state.projectors._shared import _now_iso


WEEKLY_CARD_SCHEMA_VERSION = "weekly_claim_card.v1"

# CHECK constraint shape mirrors migration 028.
_VALID_ATOM_TYPES = frozenset({"quantitative", "comparative"})
_VALID_DERIVATION_PATHS = frozenset({"aggregate", "comparison", "literal"})


class WeeklyCardValidationError(ValueError):
    """Raised when a weekly-card field violates the schema contract."""

    def __init__(self, invariant: str, message: str) -> None:
        super().__init__(message)
        self.invariant = invariant


def compute_claim_id(
    *,
    iso_week: str,
    user_id: str,
    claim_atom_text: str,
    derivation_path: str,
    locator_set: Iterable[dict[str, Any]],
) -> str:
    """Compute a deterministic ``claim_id`` for a weekly atomic claim.

    Same content → same ``claim_id`` — the function is stable across
    runs of W52 against unchanged data. The hash domain includes the
    week, user, prose, derivation path, and the locator set
    (canonicalised). Changing any field yields a different
    ``claim_id``.

    Returns a hex string (SHA-256 truncated to 32 chars for storage
    compactness; collision probability at the per-week-per-user grain
    is astronomically negligible).
    """

    canonical_locators = json.dumps(
        sorted(
            (
                json.dumps(loc, sort_keys=True)
                for loc in locator_set
            )
        ),
        sort_keys=True,
    )
    payload = "".join((
        iso_week,
        user_id,
        claim_atom_text,
        derivation_path,
        canonical_locators,
    ))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return digest[:32]


def validate_weekly_card_fields(
    *,
    iso_week: str,
    claim_atom_text: str,
    atom_type: str,
    derivation_path: str,
    locator_set: list[dict[str, Any]],
    audit_refs: dict[str, Any],
) -> None:
    """Validate the structured fields of a weekly card before insert.

    Locator-set entries validate per W-PROV-1; audit_refs validate as
    an object whose values are lists of scalar (str/int) PKs or dict
    (composite-PK) entries. Atom type + derivation path enum
    enforcement mirrors the migration's CHECK constraint.
    """

    if atom_type not in _VALID_ATOM_TYPES:
        raise WeeklyCardValidationError(
            "atom_type_enum",
            f"atom_type must be one of {sorted(_VALID_ATOM_TYPES)}; "
            f"got {atom_type!r}",
        )

    if derivation_path not in _VALID_DERIVATION_PATHS:
        raise WeeklyCardValidationError(
            "derivation_path_enum",
            f"derivation_path must be one of "
            f"{sorted(_VALID_DERIVATION_PATHS)}; got {derivation_path!r}",
        )

    if not iso_week or len(iso_week) < 8:
        raise WeeklyCardValidationError(
            "iso_week_shape",
            f"iso_week must be non-empty YYYY-Www string; got {iso_week!r}",
        )

    if not claim_atom_text:
        raise WeeklyCardValidationError(
            "claim_atom_text",
            "claim_atom_text must be non-empty",
        )

    # Locator-set: each entry validates per W-PROV-1.
    if not isinstance(locator_set, list):
        raise WeeklyCardValidationError(
            "locator_set_shape",
            f"locator_set must be a list; got {type(locator_set).__name__}",
        )
    for idx, loc in enumerate(locator_set):
        try:
            validate_locator(loc)
        except LocatorValidationError as exc:
            raise WeeklyCardValidationError(
                "locator_set_entry",
                f"locator_set[{idx}] invalid: {exc}",
            ) from exc

    # Audit-refs: dict of table-name → list of PK refs (scalar or
    # composite-dict). NOT validated against the W-PROV-1 whitelist;
    # audit-chain tables intentionally bypass it (F-PHASE0-12).
    if not isinstance(audit_refs, dict):
        raise WeeklyCardValidationError(
            "audit_refs_shape",
            f"audit_refs must be a dict; got {type(audit_refs).__name__}",
        )
    for table, entries in audit_refs.items():
        if not isinstance(table, str):
            raise WeeklyCardValidationError(
                "audit_refs_key",
                f"audit_refs keys must be strings; got "
                f"{type(table).__name__}",
            )
        if not isinstance(entries, list):
            raise WeeklyCardValidationError(
                "audit_refs_entry_shape",
                f"audit_refs[{table!r}] must be a list; got "
                f"{type(entries).__name__}",
            )
        for jdx, pk in enumerate(entries):
            if not isinstance(pk, (str, int, dict)):
                raise WeeklyCardValidationError(
                    "audit_refs_pk_type",
                    f"audit_refs[{table!r}][{jdx}] must be "
                    f"str/int/dict (composite PK); got "
                    f"{type(pk).__name__}",
                )


def project_weekly_card(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    iso_week: str,
    claim_atom_text: str,
    atom_type: str,
    derivation_path: str,
    locator_set: list[dict[str, Any]],
    audit_refs: dict[str, Any],
    claim_id: Optional[str] = None,
    card_id: Optional[str] = None,
    computed_at: Optional[str] = None,
    source: str = "claude_agent_v1",
    ingest_actor: str = "claude_agent_v1",
    agent_version: Optional[str] = None,
    commit_after: bool = True,
) -> dict[str, Any]:
    """Insert a ``weekly_claim_card`` row.

    ``claim_id`` defaults to the deterministic hash from
    :func:`compute_claim_id`. ``card_id`` defaults to a fresh UUID
    suffix appended to the claim_id (preserves append-only audit
    history per Codex Q1: every re-run yields a new row even when
    the content is identical, but consumers can dedup at the
    canonical-latest view by ``MAX(computed_at)`` per claim_id).

    Returns the persisted-row dict.
    """

    validate_weekly_card_fields(
        iso_week=iso_week,
        claim_atom_text=claim_atom_text,
        atom_type=atom_type,
        derivation_path=derivation_path,
        locator_set=locator_set,
        audit_refs=audit_refs,
    )

    if claim_id is None:
        claim_id = compute_claim_id(
            iso_week=iso_week,
            user_id=user_id,
            claim_atom_text=claim_atom_text,
            derivation_path=derivation_path,
            locator_set=locator_set,
        )
    if card_id is None:
        # UUID-suffixed so re-runs append rather than collide on PK.
        card_id = f"wcc_{claim_id}_{uuid.uuid4().hex[:12]}"
    if computed_at is None:
        computed_at = _now_iso()

    conn.execute(
        """
        INSERT INTO weekly_claim_card (
            card_id, user_id, iso_week, claim_id,
            claim_atom_text, atom_type, derivation_path,
            locator_set_json, audit_refs_json, computed_at,
            source, ingest_actor, agent_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            card_id,
            user_id,
            iso_week,
            claim_id,
            claim_atom_text,
            atom_type,
            derivation_path,
            json.dumps(locator_set, sort_keys=True),
            json.dumps(audit_refs, sort_keys=True),
            computed_at,
            source,
            ingest_actor,
            agent_version,
        ),
    )
    if commit_after:
        conn.commit()

    return {
        "card_id": card_id,
        "user_id": user_id,
        "iso_week": iso_week,
        "claim_id": claim_id,
        "claim_atom_text": claim_atom_text,
        "atom_type": atom_type,
        "derivation_path": derivation_path,
        "locator_set": locator_set,
        "audit_refs": audit_refs,
        "computed_at": computed_at,
    }


def load_canonical_latest_for_week(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    iso_week: str,
) -> list[dict[str, Any]]:
    """Return the canonical-latest view of weekly cards for the
    requested week — one row per ``(iso_week, user_id, claim_id)``,
    the row with maximum ``computed_at``.

    Superseded (historical) cards remain in ``weekly_claim_card`` but
    are NOT in this default view. Callers needing the full append-
    only history use :func:`load_full_history_for_week` (consumed by
    W52's ``--include-history`` flag).
    """

    sql = """
        SELECT card_id, user_id, iso_week, claim_id,
               claim_atom_text, atom_type, derivation_path,
               locator_set_json, audit_refs_json, computed_at
        FROM weekly_claim_card AS w1
        WHERE user_id = ? AND iso_week = ?
          AND computed_at = (
              SELECT MAX(computed_at)
              FROM weekly_claim_card AS w2
              WHERE w2.user_id = w1.user_id
                AND w2.iso_week = w1.iso_week
                AND w2.claim_id = w1.claim_id
          )
        ORDER BY claim_id ASC
    """
    rows = conn.execute(sql, (user_id, iso_week)).fetchall()
    return [_row_to_dict(row) for row in rows]


def load_full_history_for_week(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    iso_week: str,
) -> list[dict[str, Any]]:
    """Return every ``weekly_claim_card`` row for the requested week,
    including superseded entries. Order: claim_id then computed_at.
    Consumed by W52's ``--include-history`` flag (acceptance #9 in
    PLAN §2.D)."""

    sql = """
        SELECT card_id, user_id, iso_week, claim_id,
               claim_atom_text, atom_type, derivation_path,
               locator_set_json, audit_refs_json, computed_at
        FROM weekly_claim_card
        WHERE user_id = ? AND iso_week = ?
        ORDER BY claim_id ASC, computed_at ASC
    """
    rows = conn.execute(sql, (user_id, iso_week)).fetchall()
    return [_row_to_dict(row) for row in rows]


def _row_to_dict(row: Any) -> dict[str, Any]:
    """Convert a sqlite3 Row (or tuple) to a deserialised dict."""

    keys = (
        "card_id", "user_id", "iso_week", "claim_id",
        "claim_atom_text", "atom_type", "derivation_path",
        "locator_set_json", "audit_refs_json", "computed_at",
    )
    if hasattr(row, "keys"):
        out = {k: row[k] for k in keys}
    else:
        out = {k: row[i] for i, k in enumerate(keys)}
    out["locator_set"] = json.loads(out.pop("locator_set_json") or "[]")
    out["audit_refs"] = json.loads(out.pop("audit_refs_json") or "{}")
    return out
