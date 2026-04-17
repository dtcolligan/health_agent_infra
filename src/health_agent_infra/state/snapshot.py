"""Cross-domain state snapshot + per-domain read surface.

Phase 7D. Two read APIs:

  - ``read_domain(conn, domain, since, until, user_id)`` — returns rows from
    one domain's canonical table within a civil-date range. For operator
    introspection, reporting, and debugging.

  - ``build_snapshot(conn, as_of_date, user_id, lookback_days)`` — returns
    the cross-domain object the agent consumes when producing a
    recommendation. Contains today's rows per domain plus a history window,
    all tagged with a missingness token per state_model_v1.md §5.

Field names in the returned dicts match the DB column names for the domain.
Skills reference these names directly; renames of DB columns must flow
through this surface, never bypass it.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Domain <-> table registry
# ---------------------------------------------------------------------------

# Each domain maps to a single canonical table in migration 001. A few
# domains aggregate across tables inside ``build_snapshot`` but the per-
# domain read uses only the primary table.
_DOMAIN_TABLES: dict[str, str] = {
    "recovery": "accepted_recovery_state_daily",
    "running": "accepted_running_state_daily",
    "gym": "accepted_resistance_training_state_daily",
    "nutrition": "accepted_nutrition_state_daily",
    "stress": "stress_manual_raw",
    "notes": "context_note",
    "recommendations": "recommendation_log",
    "reviews": "review_outcome",
    "goals": "goal",
}

# Column holding the civil-date filter per domain.
_DOMAIN_DATE_COLUMN: dict[str, str] = {
    "recovery": "as_of_date",
    "running": "as_of_date",
    "gym": "as_of_date",
    "nutrition": "as_of_date",
    "stress": "as_of_date",
    "notes": "as_of_date",
    "recommendations": "for_date",
    "reviews": "recorded_at",  # outcomes carry full timestamp; we compare prefix
    # goals handled specially (date-range overlap)
}

# Domains that carry a user_id column directly. `reviews` does via outcome.
_DOMAIN_HAS_USER_ID: dict[str, bool] = {
    "recovery": True,
    "running": True,
    "gym": True,
    "nutrition": True,
    "stress": True,
    "notes": True,
    "recommendations": True,
    "reviews": True,
    "goals": True,
}

# User-reported (vs passive) domains — these are candidates for the
# `pending_user_input` missingness token when the day is still in progress.
_USER_REPORTED_DOMAINS: frozenset[str] = frozenset({
    "gym", "nutrition", "stress", "notes",
})

# Default cutover: before 23:30 local on today's civil date, missing
# user-reported rows are `pending_user_input`; after, they're `partial` /
# `absent` as appropriate. See state_model_v1.md §5.
_PENDING_CUTOVER = time(hour=23, minute=30)

# Bookkeeping columns present on every canonical table. These never count
# toward `partial:<fields>` — a NULL `corrected_at` is load-bearing (means
# no correction has happened), not missing data.
_METADATA_COLUMNS: frozenset[str] = frozenset({
    "as_of_date",
    "user_id",
    "derived_from",
    "source",
    "ingest_actor",
    "projected_at",
    "corrected_at",
    "derivation_path",
})

# Per-domain "v1 required" fields — the fields a fully-populated v1 row is
# expected to carry. Fields outside this set are enrichment deferred to 7B
# (e.g. `training_readiness_pct`) or NULL-by-design (e.g. running's
# `session_count` when `derivation_path='garmin_daily'`). NULLs on non-
# required fields don't count toward `partial:<fields>`.
#
# When 7B lands, these sets grow; the snapshot surface stays the same.
_V1_REQUIRED_FIELDS: dict[str, frozenset[str]] = {
    "recovery": frozenset({
        "sleep_hours", "resting_hr", "hrv_ms", "all_day_stress",
        "manual_stress_score", "acute_load", "chronic_load", "acwr_ratio",
        "body_battery_end_of_day",
    }),
    "running": frozenset({
        "total_distance_m", "moderate_intensity_min", "vigorous_intensity_min",
    }),
    "gym": frozenset({
        "session_count", "total_sets",
    }),
    "nutrition": frozenset({
        "calories", "protein_g", "carbs_g", "fat_g",
    }),
}


def available_domains() -> list[str]:
    """Return the list of domain names ``read_domain`` accepts."""

    return sorted(_DOMAIN_TABLES.keys())


# ---------------------------------------------------------------------------
# read_domain — single domain, bounded by civil-date range
# ---------------------------------------------------------------------------

def read_domain(
    conn: sqlite3.Connection,
    *,
    domain: str,
    since: date,
    until: Optional[date] = None,
    user_id: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Return rows from one domain's canonical table within ``[since, until]``.

    For date-bearing domains, filters on the civil-date column. For
    ``goals``, returns every goal whose active interval overlaps the range
    (``started_on <= until`` and ``ended_on IS NULL OR ended_on >= since``).
    """

    if domain not in _DOMAIN_TABLES:
        raise ValueError(
            f"unknown domain: {domain!r}. known: {available_domains()}"
        )

    until = until if until is not None else since

    if domain == "goals":
        sql = (
            "SELECT * FROM goal "
            "WHERE started_on <= ? "
            "AND (ended_on IS NULL OR ended_on >= ?) "
        )
        params: list[Any] = [until.isoformat(), since.isoformat()]
        if user_id is not None:
            sql += "AND user_id = ? "
            params.append(user_id)
        sql += "ORDER BY started_on"
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    table = _DOMAIN_TABLES[domain]
    date_col = _DOMAIN_DATE_COLUMN[domain]

    if domain == "reviews":
        # recorded_at is an ISO-8601 timestamp; compare the date prefix.
        sql = (
            f"SELECT * FROM {table} "
            f"WHERE substr({date_col}, 1, 10) BETWEEN ? AND ? "
        )
    else:
        sql = f"SELECT * FROM {table} WHERE {date_col} BETWEEN ? AND ? "

    params = [since.isoformat(), until.isoformat()]
    if user_id is not None and _DOMAIN_HAS_USER_ID.get(domain, False):
        sql += "AND user_id = ? "
        params.append(user_id)

    sql += f"ORDER BY {date_col}"
    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# build_snapshot — cross-domain envelope the agent reads
# ---------------------------------------------------------------------------

def build_snapshot(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str,
    lookback_days: int = 14,
    now_local: Optional[datetime] = None,
) -> dict[str, Any]:
    """Build the cross-domain snapshot object the agent consumes.

    ``now_local`` controls the `pending_user_input` vs `partial` / `absent`
    split per state_model_v1.md §5. Defaults to current local time. Tests
    inject a fixed value to exercise both sides of the 23:30 cutover.
    """

    if now_local is None:
        now_local = datetime.now()

    lookback_start = as_of_date - timedelta(days=max(0, lookback_days - 1))

    is_today = as_of_date == now_local.date()
    is_before_cutover = now_local.time() < _PENDING_CUTOVER

    def _daily_today(domain: str) -> tuple[Optional[dict], str]:
        """Return (today_row_or_none, missingness_token) for a daily-grain
        domain. Row is ``None`` when the underlying table has no row for
        (as_of_date, user_id)."""

        rows = read_domain(
            conn,
            domain=domain,
            since=as_of_date,
            until=as_of_date,
            user_id=user_id,
        )
        required = _V1_REQUIRED_FIELDS.get(domain)

        if rows:
            row = rows[0]
            if required is not None:
                null_fields = sorted(
                    k for k in required if row.get(k) is None
                )
            else:
                # No declared required-field set for this domain: fall back
                # to "everything non-metadata counts."
                null_fields = sorted(
                    k for k, v in row.items()
                    if v is None and k not in _METADATA_COLUMNS
                )

            if not null_fields:
                return row, "present"

            # User-reported domain, today before cutover, with some nulls:
            # surface as pending_user_input rather than partial. The user is
            # still logging; the gaps are expected to close by 23:30.
            if (
                is_today
                and is_before_cutover
                and domain in _USER_REPORTED_DOMAINS
            ):
                return row, f"pending_user_input:{','.join(null_fields)}"
            return row, f"partial:{','.join(null_fields)}"

        # No row. Decide absent vs pending_user_input.
        if (
            is_today
            and is_before_cutover
            and domain in _USER_REPORTED_DOMAINS
        ):
            return None, "pending_user_input"
        return None, "absent"

    def _history(domain: str) -> list[dict]:
        return read_domain(
            conn,
            domain=domain,
            since=lookback_start,
            until=as_of_date - timedelta(days=1),
            user_id=user_id,
        )

    # Passive (Garmin-backed) recovery/running: can only be `absent` or
    # `present`/`partial`; never `pending_user_input` (Garmin doesn't need
    # user action).
    recovery_today, recovery_mx = _daily_today("recovery")
    running_today, running_mx = _daily_today("running")

    # User-reported domains: follow the pending_user_input rule.
    gym_today, gym_mx = _daily_today("gym")
    nutrition_today, nutrition_mx = _daily_today("nutrition")

    goals_active = read_domain(
        conn,
        domain="goals",
        since=as_of_date,
        until=as_of_date,
        user_id=user_id,
    )

    # Recommendations + reviews: append-only, no missingness concept. Just
    # show the last N days.
    recent_recs = _history("recommendations")
    recent_revs = _history("reviews")

    # Notes are free-text; don't project daily missingness — just provide
    # whatever's in the lookback.
    recent_notes = _history("notes")

    # Stress is a derived view on accepted_recovery_state_daily — Garmin's
    # all_day_stress + the user-reported manual_stress_score live together
    # in that canonical row. The raw stress_manual_raw table exists for
    # audit (queryable via `hai state read --domain stress`) but the
    # snapshot pulls from the accepted row so the agent never sees
    # pre-projection submissions.
    today_garmin_stress: Optional[int] = None
    today_manual_stress: Optional[int] = None
    if isinstance(recovery_today, dict):
        today_garmin_stress = recovery_today.get("all_day_stress")
        today_manual_stress = recovery_today.get("manual_stress_score")

    stress_nulls: list[str] = []
    if today_garmin_stress is None:
        stress_nulls.append("all_day_stress")
    if today_manual_stress is None:
        stress_nulls.append("manual_stress_score")

    if not stress_nulls:
        stress_mx = "present"
    elif len(stress_nulls) == 2:
        # Neither signal present. Treat as absent, unless today is still in
        # progress and the user might still log — then pending_user_input.
        if is_today and is_before_cutover:
            stress_mx = "pending_user_input"
        else:
            stress_mx = "absent"
    else:
        # One signal present, the other null. Garmin-present + manual-null
        # must not flatten to `absent`: Garmin data is real evidence that
        # the manual gap alone defines.
        if (
            is_today
            and is_before_cutover
            and "manual_stress_score" in stress_nulls
        ):
            stress_mx = f"pending_user_input:{','.join(stress_nulls)}"
        else:
            stress_mx = f"partial:{','.join(stress_nulls)}"

    return {
        "schema_version": "state_snapshot.v1",
        "as_of_date": as_of_date.isoformat(),
        "user_id": user_id,
        "lookback_days": lookback_days,
        "history_range": [lookback_start.isoformat(), (as_of_date - timedelta(days=1)).isoformat()],
        "recovery": {
            "today": recovery_today,
            "history": _history("recovery"),
            "missingness": recovery_mx,
        },
        "running": {
            "today": running_today,
            "history": _history("running"),
            "missingness": running_mx,
        },
        "gym": {
            "today": gym_today,
            "history": _history("gym"),
            "missingness": gym_mx,
        },
        "nutrition": {
            "today": nutrition_today,
            "history": _history("nutrition"),
            "missingness": nutrition_mx,
        },
        "stress": {
            "today_garmin": today_garmin_stress,
            "today_manual": today_manual_stress,
            "missingness": stress_mx,
        },
        "notes": {
            "recent": recent_notes,
        },
        "goals_active": goals_active,
        "recommendations": {
            "recent": recent_recs,
        },
        "reviews": {
            "recent": recent_revs,
        },
    }
