"""Project per-source / per-domain data-quality rows from snapshot evidence.

The projector reads an existing snapshot (``build_snapshot``) and
upserts one row per (user, date, domain, source) into
``data_quality_daily``. It does NOT recompute bands, missingness, or
cold-start status — every signal is sourced from the snapshot the
runtime already produced.

The ``cold_start_window_state`` column is constrained to be consistent
with ``snapshot.<domain>.cold_start`` per the W51 maintainer
refinement (`MAINTAINER_ANALYSIS.md` § 3.3): when ``cold_start = True``
the projector writes ``in_window``; otherwise it writes
``post_cold_start``. (``recently_closed`` is reserved for a future
reactive surface; v0.1.8 doesn't compute it.)
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from typing import Any, Optional


DOMAINS: tuple[str, ...] = (
    "recovery",
    "running",
    "sleep",
    "stress",
    "strength",
    "nutrition",
)


# Sources we project per domain. Recovery / running / sleep / stress /
# nutrition + strength all carry a "primary source" string per the
# data ledger; v0.1.8 surfaces one row per (domain, source) by reading
# the snapshot's `sources` block plus the per-domain default source.
_DOMAIN_DEFAULT_SOURCE: dict[str, str] = {
    "recovery": "garmin",
    "running": "garmin",
    "sleep": "garmin",
    "stress": "garmin",
    "strength": "user_manual",
    "nutrition": "user_manual",
}


def _coverage_band_from_block(block: dict[str, Any]) -> Optional[str]:
    """Resolve a domain block's coverage_band, preferring
    classified_state when present (full bundle), falling back to None."""

    classified = block.get("classified_state")
    if isinstance(classified, dict) and "coverage_band" in classified:
        return classified["coverage_band"]
    return None


def _missingness_from_block(block: dict[str, Any]) -> Optional[str]:
    return block.get("missingness")


def project_data_quality_for_date(
    conn: sqlite3.Connection,
    *,
    snapshot: dict[str, Any],
    now: Optional[datetime] = None,
    commit_after: bool = True,
) -> int:
    """Upsert one ``data_quality_daily`` row per (domain, source) from
    ``snapshot``. Returns the number of rows written.

    Idempotent: re-running on the same snapshot replaces the existing
    rows (PRIMARY KEY is (user_id, as_of_date, domain, source)).

    ``commit_after`` defaults to True for standalone callers; set to
    False when invoked inside an outer transaction (e.g. ``hai clean``)
    that wants to commit at its own boundary.
    """

    when = now or datetime.now(timezone.utc)
    user_id = snapshot["user_id"]
    as_of_date = snapshot["as_of_date"]
    sources_block = snapshot.get("sources") or {}

    written = 0
    for domain in DOMAINS:
        block = snapshot.get(domain) or {}
        cold_start = bool(block.get("cold_start", False))

        coverage_band = _coverage_band_from_block(block)
        missingness = _missingness_from_block(block)

        source = _DOMAIN_DEFAULT_SOURCE.get(domain, "user_manual")
        # Prefer the snapshot's freshness when available.
        source_freshness = sources_block.get(source) or {}
        freshness_hours = source_freshness.get("staleness_hours")

        source_unavailable = 0
        if missingness and "unavailable_at_source" in missingness:
            source_unavailable = 1
        user_input_pending = 0
        if missingness and "pending_user_input" in missingness:
            user_input_pending = 1

        cold_start_window_state = "in_window" if cold_start else "post_cold_start"

        conn.execute(
            """
            INSERT OR REPLACE INTO data_quality_daily (
                user_id, as_of_date, domain, source,
                freshness_hours, coverage_band, missingness,
                source_unavailable, user_input_pending,
                suspicious_discontinuity,
                cold_start_window_state, computed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, as_of_date, domain, source,
                freshness_hours, coverage_band, missingness,
                source_unavailable, user_input_pending,
                0,  # suspicious_discontinuity reserved for future detection
                cold_start_window_state, when.isoformat(),
            ),
        )
        written += 1

    if commit_after:
        conn.commit()
    return written


def read_data_quality_rows(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    since_date: Optional[date] = None,
    until_date: Optional[date] = None,
    domain: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Return rows matching the filters, ordered by (as_of_date, domain, source)."""

    sql = "SELECT * FROM data_quality_daily WHERE user_id = ?"
    params: list[Any] = [user_id]
    if since_date is not None:
        sql += " AND as_of_date >= ?"
        params.append(since_date.isoformat())
    if until_date is not None:
        sql += " AND as_of_date <= ?"
        params.append(until_date.isoformat())
    if domain is not None:
        sql += " AND domain = ?"
        params.append(domain)
    sql += " ORDER BY as_of_date, domain, source"
    return [dict(r) for r in conn.execute(sql, params).fetchall()]
