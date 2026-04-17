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
        "acute_load", "chronic_load", "acwr_ratio",
        "body_battery_end_of_day",
        # Phase 7B: locally-computed mean of five Garmin component pcts.
        # A missing value here means Garmin didn't record ≥1 component that
        # day — surfaced as `unavailable_at_source`, not `partial`.
        "training_readiness_component_mean_pct",
        # manual_stress_score is user-reported and must flow through
        # stress_manual_raw → accepted recovery (7C). Until 7C ships, a
        # clean-only pipeline cannot populate it, so it is NOT part of the
        # v1 "required for present" set. Its NULL-ness still surfaces via
        # the `stress` block's missingness token, which is the right place.
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
    evidence_bundle: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build the cross-domain snapshot object the agent consumes.

    ``now_local`` controls the `pending_user_input` vs `partial` / `absent`
    split per state_model_v1.md §5. Defaults to current local time. Tests
    inject a fixed value to exercise both sides of the 23:30 cutover.

    ``evidence_bundle`` is a ``dict`` matching the stdout of ``hai clean``
    (keys: ``cleaned_evidence``, ``raw_summary``). When supplied, the
    recovery block is expanded from ``{today, history, missingness}`` to
    the full Phase 1 per-domain bundle::

        recovery = {
            today, history, missingness,            # existing keys
            evidence, raw_summary,                  # from evidence_bundle
            classified_state, policy_result,        # derived via classify + policy
        }

    When the bundle is absent, the recovery block keeps its v1.0 shape so
    existing callers are unaffected. Other domains always keep their
    v1.0 shape until their own classify/policy lands.

    The plan's end-state is for ``hai state snapshot`` to derive the
    evidence bundle internally from stored raw data; that lands once the
    manual-readiness path is persisted (currently the readiness inputs
    only live in the transient ``hai pull`` evidence JSON).
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

            # Token choice per state_model_v1.md §5:
            #   - User-reported domain + today before cutover + null fields:
            #     the user is still logging; gaps are expected to close by
            #     23:30. Emit `pending_user_input:<fields>`.
            #   - User-reported domain + day closed: user had the whole day;
            #     the gaps are the final state. Emit `partial:<fields>`.
            #   - Passive domain (Garmin-backed): we queried the source and
            #     it didn't return that field. Emit `unavailable_at_source:
            #     <fields>` — the gap is the source's, not ours, and is
            #     qualitatively different from an incomplete-user-log
            #     `partial`. The agent reads this as "Garmin didn't record"
            #     rather than "data collection is still in progress."
            if domain in _USER_REPORTED_DOMAINS:
                if is_today and is_before_cutover:
                    return row, f"pending_user_input:{','.join(null_fields)}"
                return row, f"partial:{','.join(null_fields)}"
            return row, f"unavailable_at_source:{','.join(null_fields)}"

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

    garmin_null = today_garmin_stress is None
    manual_null = today_manual_stress is None

    # Stress blends two origins into one block: Garmin (passive) +
    # user_manual (user-reported). Missingness routes by origin per
    # state_model_v1.md §5:
    #   - Both present: `present`.
    #   - Both null + today/before-cutover: `pending_user_input` (user can
    #     still log; Garmin's absence doesn't resolve by user action, but
    #     we keep the bare token here since the user can still contribute).
    #   - Both null + day closed: `absent` (no stress evidence at all).
    #   - Garmin null only: `unavailable_at_source:all_day_stress` — the
    #     source was queried and didn't return. Independent of time-of-day.
    #   - Manual null only: routed by time. today/before-cutover →
    #     `pending_user_input:manual_stress_score`; day closed →
    #     `partial:manual_stress_score`.
    if not garmin_null and not manual_null:
        stress_mx = "present"
    elif garmin_null and manual_null:
        if is_today and is_before_cutover:
            stress_mx = "pending_user_input"
        else:
            stress_mx = "absent"
    elif garmin_null:
        stress_mx = "unavailable_at_source:all_day_stress"
    else:
        # manual_null only
        if is_today and is_before_cutover:
            stress_mx = "pending_user_input:manual_stress_score"
        else:
            stress_mx = "partial:manual_stress_score"

    recovery_block: dict[str, Any] = {
        "today": recovery_today,
        "history": _history("recovery"),
        "missingness": recovery_mx,
    }
    if evidence_bundle is not None:
        # Phase 1 full-bundle shape: add evidence + raw_summary +
        # classified_state + policy_result to the recovery block.
        # Import here (not at module top) to keep `core.schemas` /
        # `domains.recovery` out of the state package's import cycle at
        # load time.
        from health_agent_infra.domains.recovery import (
            classify_recovery_state,
            evaluate_recovery_policy,
        )

        cleaned = evidence_bundle.get("cleaned_evidence") or {}
        raw_summary = evidence_bundle.get("raw_summary") or {}
        classified = classify_recovery_state(cleaned, raw_summary)
        policy = evaluate_recovery_policy(classified, raw_summary)

        recovery_block["evidence"] = cleaned
        recovery_block["raw_summary"] = raw_summary
        recovery_block["classified_state"] = _classified_to_dict(classified)
        recovery_block["policy_result"] = _policy_to_dict(policy)

    return {
        "schema_version": "state_snapshot.v1",
        "as_of_date": as_of_date.isoformat(),
        "user_id": user_id,
        "lookback_days": lookback_days,
        "history_range": [lookback_start.isoformat(), (as_of_date - timedelta(days=1)).isoformat()],
        "recovery": recovery_block,
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


# ---------------------------------------------------------------------------
# Helpers for classified_state + policy_result serialisation
# ---------------------------------------------------------------------------

def _classified_to_dict(classified: Any) -> dict[str, Any]:
    """Convert a ClassifiedRecoveryState frozen dataclass to a plain dict.

    ``uncertainty`` comes off the dataclass as a tuple; snapshot emits it
    as a list for JSON-friendliness. Field names are preserved verbatim
    — they are the skill's contract.
    """

    return {
        "sleep_debt_band": classified.sleep_debt_band,
        "resting_hr_band": classified.resting_hr_band,
        "hrv_band": classified.hrv_band,
        "training_load_band": classified.training_load_band,
        "soreness_band": classified.soreness_band,
        "coverage_band": classified.coverage_band,
        "recovery_status": classified.recovery_status,
        "readiness_score": classified.readiness_score,
        "uncertainty": list(classified.uncertainty),
    }


def _policy_to_dict(policy: Any) -> dict[str, Any]:
    """Convert a RecoveryPolicyResult frozen dataclass to a plain dict."""

    return {
        "policy_decisions": [
            {"rule_id": d.rule_id, "decision": d.decision, "note": d.note}
            for d in policy.policy_decisions
        ],
        "forced_action": policy.forced_action,
        "forced_action_detail": policy.forced_action_detail,
        "capped_confidence": policy.capped_confidence,
    }
