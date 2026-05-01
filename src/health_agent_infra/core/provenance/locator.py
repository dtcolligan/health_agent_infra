"""Source-row locator — typed pointer to a row in the evidence layer.

v0.1.14 W-PROV-1. Schema and rules at
`reporting/docs/source_row_provenance.md`.

A locator names a single row (or a single column of a single row)
in a whitelisted evidence-or-accepted-state table. Consumers
(`hai explain`, v0.2.0 W58D) resolve the locator back to its row
to verify a quantitative claim.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Optional


# v0.1.14 demo whitelist — recovery domain only. Other domains add
# entries here as they adopt locator emission. Keep alphabetised by
# table name for deterministic error messages.
_ALLOWED_TABLES_PK: dict[str, tuple[str, ...]] = {
    "accepted_recovery_state_daily": ("as_of_date", "user_id"),
    "source_daily_garmin": (
        "as_of_date",
        "user_id",
        "export_batch_id",
        "csv_row_index",
    ),
}


class LocatorValidationError(ValueError):
    """Raised when a locator dict violates the schema contract."""

    def __init__(self, invariant: str, message: str) -> None:
        super().__init__(message)
        self.invariant = invariant


@dataclass(frozen=True)
class SourceRowLocator:
    """Typed locator. Field semantics: see source_row_provenance.md."""

    table: str
    pk: dict[str, Any]
    row_version: str
    column: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return locator_to_dict(self)


def locator_to_dict(loc: SourceRowLocator) -> dict[str, Any]:
    """Stable dict shape — `column` omitted when None for byte-stable JSON."""

    out: dict[str, Any] = {
        "table": loc.table,
        "pk": dict(sorted(loc.pk.items())),
        "row_version": loc.row_version,
    }
    if loc.column is not None:
        out["column"] = loc.column
    return out


def validate_locator(d: Any) -> None:
    """Validate a locator dict against the W-PROV-1 contract.

    Raises :class:`LocatorValidationError` on the first violation.
    """

    if not isinstance(d, dict):
        raise LocatorValidationError(
            "shape", f"locator must be dict; got {type(d).__name__}"
        )

    required = {"table", "pk", "row_version"}
    missing = required - set(d.keys())
    if missing:
        raise LocatorValidationError(
            "required_fields", f"missing: {sorted(missing)}"
        )

    table = d["table"]
    if not isinstance(table, str):
        raise LocatorValidationError(
            "table_str", f"table must be str; got {type(table).__name__}"
        )
    if table not in _ALLOWED_TABLES_PK:
        raise LocatorValidationError(
            "table_whitelist",
            f"table {table!r} not in v0.1.14 whitelist "
            f"{sorted(_ALLOWED_TABLES_PK)}",
        )

    pk = d["pk"]
    if not isinstance(pk, dict):
        raise LocatorValidationError(
            "pk_object", f"pk must be object; got {type(pk).__name__}"
        )
    expected_pk_cols = set(_ALLOWED_TABLES_PK[table])
    actual_pk_cols = set(pk.keys())
    if expected_pk_cols != actual_pk_cols:
        raise LocatorValidationError(
            "pk_shape",
            f"pk columns mismatch for table {table!r}: "
            f"expected {sorted(expected_pk_cols)}, got {sorted(actual_pk_cols)}",
        )
    for k, v in pk.items():
        if not isinstance(v, (str, int, float)):
            raise LocatorValidationError(
                "pk_value_scalar",
                f"pk[{k!r}] must be scalar (str/int/float); "
                f"got {type(v).__name__}",
            )

    row_version = d["row_version"]
    if not isinstance(row_version, str):
        raise LocatorValidationError(
            "row_version_str",
            f"row_version must be str; got {type(row_version).__name__}",
        )

    column = d.get("column")
    if column is not None and not isinstance(column, str):
        raise LocatorValidationError(
            "column_str",
            f"column must be str or absent; got {type(column).__name__}",
        )


def dedupe_locators(locators: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicates. Order-preserving (first occurrence wins).

    Two locators are duplicates when (table, sorted-pk-pairs, column)
    match. row_version is intentionally NOT part of the dedup key —
    if the same row is cited twice with different row_versions, the
    second is dropped (the first wins; the caller is expected to
    cite the row_version they actually consulted).
    """

    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for loc in locators:
        validate_locator(loc)
        key = (
            loc["table"],
            tuple(sorted(loc["pk"].items())),
            loc.get("column"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(loc)
    return out


def serialize_locators(locators: Optional[list[dict[str, Any]]]) -> Optional[str]:
    """Serialise a locator list to a JSON string suitable for the
    ``recommendation_log.evidence_locators_json`` column. Returns
    None on empty / None inputs (the column accepts NULL)."""

    if not locators:
        return None
    cleaned = [locator_to_dict_from_input(loc) for loc in dedupe_locators(locators)]
    return json.dumps(cleaned, sort_keys=True)


def deserialize_locators(blob: Optional[str]) -> list[dict[str, Any]]:
    """Inverse of :func:`serialize_locators`. NULL → empty list."""

    if not blob:
        return []
    parsed = json.loads(blob)
    if not isinstance(parsed, list):
        raise LocatorValidationError(
            "shape", "serialised locators must be a JSON list"
        )
    for entry in parsed:
        validate_locator(entry)
    return parsed


def locator_to_dict_from_input(d: dict[str, Any]) -> dict[str, Any]:
    """Normalise an already-validated locator dict into the canonical
    sorted-pk shape used for storage."""

    out: dict[str, Any] = {
        "table": d["table"],
        "pk": dict(sorted(d["pk"].items())),
        "row_version": d["row_version"],
    }
    if d.get("column") is not None:
        out["column"] = d["column"]
    return out


def resolve_locator(
    conn: sqlite3.Connection,
    locator: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """Resolve a locator to its current DB row.

    Returns a dict of {column_name: value} for every column on the
    row, or None if the row no longer exists. Does NOT compare
    row_version — the caller decides whether to detect drift.
    """

    validate_locator(locator)
    table = locator["table"]
    pk_cols = _ALLOWED_TABLES_PK[table]
    pk_values = tuple(locator["pk"][c] for c in pk_cols)
    where_clause = " AND ".join(f"{c} = ?" for c in pk_cols)
    sql = f"SELECT * FROM {table} WHERE {where_clause}"  # nosec B608 — table from whitelist, columns are PK metadata not user input
    cur = conn.execute(sql, pk_values)
    columns = [d[0] for d in cur.description]
    row = cur.fetchone()
    if row is None:
        return None
    return dict(zip(columns, row))


def render_locators_markdown(locators: list[dict[str, Any]]) -> str:
    """Render a locator list as a bulleted markdown list.

    Empty input returns the empty string. Each locator becomes one
    bullet of the form `- {table} / {pk-tuple} / {column-or-row}`.
    """

    if not locators:
        return ""
    lines: list[str] = []
    for loc in locators:
        validate_locator(loc)
        pk_pairs = ", ".join(f"{k}={v}" for k, v in sorted(loc["pk"].items()))
        column = loc.get("column") or "<row>"
        lines.append(f"- {loc['table']} / {pk_pairs} / {column}")
    return "\n".join(lines)
