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
    "sleep": "accepted_sleep_state_daily",
    # Phase 3: stress points at the new accepted table; pre-Phase-3 it
    # pointed at the raw stress_manual_raw. The raw table is still
    # queryable via SQL for debugging; read_domain surfaces the accepted
    # canonical state the agent consumes.
    "stress": "accepted_stress_state_daily",
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
    "sleep": "as_of_date",
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
    "sleep": True,
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
        "resting_hr", "hrv_ms",
        "acute_load", "chronic_load", "acwr_ratio",
        # Phase 7B: locally-computed mean of five Garmin component pcts.
        # A missing value here means Garmin didn't record ≥1 component that
        # day — surfaced as `unavailable_at_source`, not `partial`.
        "training_readiness_component_mean_pct",
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
    # Phase 3: sleep + stress are first-class domains. sleep_hours is the
    # headline signal; the minute breakdowns and scores are enrichments
    # and NULLs on them do not count as partial. Stress's required set is
    # the co-owned pair: Garmin's all-day stress (passive) plus the user
    # manual score routes missingness separately via the stress block
    # assembler below.
    "sleep": frozenset({
        "sleep_hours",
    }),
    "stress": frozenset({
        "garmin_all_day_stress",
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
    (keys: ``cleaned_evidence``, ``raw_summary``). When supplied:

      - The **recovery** block is expanded from ``{today, history,
        missingness}`` to the full per-domain bundle::

            recovery = {
                today, history, missingness,
                evidence, raw_summary,
                classified_state, policy_result,
            }

      - The **running** block is expanded with derived signals + classify
        + policy (Phase 2 step 3)::

            running = {
                today, history, missingness,
                signals,
                classified_state, policy_result,
            }

      - The **sleep** and **stress** blocks are expanded with derived
        signals + classify + policy (Phase 3 step 5)::

            sleep = {
                today, history, missingness,
                signals,
                classified_state, policy_result,
            }
            stress = {
                today, history, missingness,
                today_garmin, today_manual, today_body_battery,
                signals,
                classified_state, policy_result,
            }

        X1a / X1b read ``sleep.classified_state.sleep_debt_band``; X7
        reads ``stress.classified_state.garmin_stress_band``; X6 reads
        body-battery off ``stress.today_body_battery``.

    When the bundle is absent, these blocks keep their v1.0 shape so
    existing callers are unaffected. Other domains keep v1.0 shape until
    their own classify/policy lands.

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

    # Passive (Garmin-backed) recovery/running/sleep: can only be
    # `absent` or `present`/`partial`; never `pending_user_input`
    # (Garmin doesn't need user action).
    recovery_today, recovery_mx = _daily_today("recovery")
    running_today, running_mx = _daily_today("running")
    sleep_today, sleep_mx = _daily_today("sleep")

    # User-reported domains: follow the pending_user_input rule.
    gym_today, gym_mx = _daily_today("gym")
    nutrition_today, nutrition_mx = _daily_today("nutrition")
    strength_today, strength_mx = gym_today, gym_mx
    strength_history = _history("gym")

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

    # User memory (Phase D) — goals / preferences / constraints / durable
    # context notes that were active at end-of-day UTC on ``as_of_date``.
    # Exposed as a bounded read-only block; never consumed by policy or
    # X-rules (see memory_model.md §2.1 + roadmap §3.1 decision 4).
    user_memory_block = _user_memory_block(conn, as_of_date=as_of_date, user_id=user_id)

    # Sources freshness (M2) — per-source last-successful sync timestamp +
    # staleness against as_of_date. Source of truth is sync_run_log
    # (migration 008); consumers can answer "how fresh is the evidence
    # I'm reasoning over?" without reading JSONL files. Empty dict on a
    # pre-008 DB — the block is still present, just unpopulated.
    sources_block = _sources_block(conn, as_of_date=as_of_date, user_id=user_id)

    # Stress (Phase 3): first-class domain on its own accepted table.
    # Two origins co-own it: Garmin (garmin_all_day_stress +
    # body_battery_end_of_day) and user_manual (manual_stress_score).
    # Missingness routes by origin per state_model_v1.md §5:
    #   - Both present: `present`.
    #   - Both null + today/before-cutover: `pending_user_input` (user
    #     can still log; Garmin's absence doesn't resolve by user action
    #     but we keep the bare token since the user can still contribute).
    #   - Both null + day closed: `absent`.
    #   - Garmin null only: `unavailable_at_source:garmin_all_day_stress`.
    #   - Manual null only: routed by time —
    #     `pending_user_input:manual_stress_score` pre-cutover,
    #     `partial:manual_stress_score` post-cutover.
    stress_rows = read_domain(
        conn,
        domain="stress",
        since=as_of_date,
        until=as_of_date,
        user_id=user_id,
    )
    stress_today = stress_rows[0] if stress_rows else None
    today_garmin_stress = stress_today.get("garmin_all_day_stress") if stress_today else None
    today_manual_stress = stress_today.get("manual_stress_score") if stress_today else None
    today_body_battery = stress_today.get("body_battery_end_of_day") if stress_today else None

    garmin_null = today_garmin_stress is None
    manual_null = today_manual_stress is None

    if not garmin_null and not manual_null:
        stress_mx = "present"
    elif garmin_null and manual_null:
        if is_today and is_before_cutover:
            stress_mx = "pending_user_input"
        else:
            stress_mx = "absent"
    elif garmin_null:
        stress_mx = "unavailable_at_source:garmin_all_day_stress"
    else:
        # manual_null only
        if is_today and is_before_cutover:
            stress_mx = "pending_user_input:manual_stress_score"
        else:
            stress_mx = "partial:manual_stress_score"

    recovery_history = _history("recovery")
    running_history = _history("running")
    sleep_history = _history("sleep")
    stress_history = _history("stress")

    recovery_block: dict[str, Any] = {
        "today": recovery_today,
        "history": recovery_history,
        "missingness": recovery_mx,
    }
    running_block: dict[str, Any] = {
        "today": running_today,
        "history": running_history,
        "missingness": running_mx,
    }
    sleep_block: dict[str, Any] = {
        "today": sleep_today,
        "history": sleep_history,
        "missingness": sleep_mx,
    }
    stress_block: dict[str, Any] = {
        "today": stress_today,
        "history": stress_history,
        "missingness": stress_mx,
        # Convenience accessors so synthesis_policy and skills can read
        # the day's stress signals without unpacking `today`. These
        # mirror the pre-Phase-3 `today_garmin` / `today_manual` shape
        # and add `today_body_battery` which moved onto the stress
        # block with migration 004.
        "today_garmin": today_garmin_stress,
        "today_manual": today_manual_stress,
        "today_body_battery": today_body_battery,
    }

    # Strength block — Phase 4 step 5 promotes the existing "gym" raw
    # aggregate read into a first-class domain block with classify +
    # policy + signals derivation (when an evidence_bundle is
    # supplied). The legacy top-level "gym" key is preserved further
    # down for pre-Phase-4 snapshot consumers.
    strength_block: dict[str, Any] = {
        "today": strength_today,
        "history": strength_history,
        "missingness": strength_mx,
    }

    # Nutrition block — Phase 5 step 4 promotes the existing pass-through
    # "nutrition" daily-grain read into a first-class domain block with
    # classify + policy + signals derivation (when an evidence_bundle is
    # supplied). Macros-only scope per the Phase 2.5 retrieval-gate
    # outcome; micronutrient_coverage on classified_state always resolves
    # to 'unavailable_at_source'. The separate top-level "nutrition" key
    # on the return dict is preserved verbatim for any pre-Phase-5
    # snapshot consumer that read it directly.
    nutrition_history = _history("nutrition")
    nutrition_block: dict[str, Any] = {
        "today": nutrition_today,
        "history": nutrition_history,
        "missingness": nutrition_mx,
    }

    if evidence_bundle is not None:
        # Full-bundle shape: per-domain expansion with classify + policy.
        # Imports happen here (not at module top) so `core.schemas` /
        # `domains.*` stay out of the state package's import cycle at
        # load time.
        from health_agent_infra.domains.recovery import (
            classify_recovery_state,
            evaluate_recovery_policy,
        )
        from health_agent_infra.domains.running import (
            classify_running_state,
            derive_running_signals,
            evaluate_running_policy,
        )
        from health_agent_infra.domains.sleep import (
            classify_sleep_state,
            derive_sleep_signals,
            evaluate_sleep_policy,
        )
        from health_agent_infra.domains.stress import (
            classify_stress_state,
            derive_stress_signals,
            evaluate_stress_policy,
        )
        from health_agent_infra.domains.strength import (
            classify_strength_state,
            derive_strength_signals,
            evaluate_strength_policy,
        )
        from health_agent_infra.domains.nutrition import (
            classify_nutrition_state,
            derive_nutrition_signals,
            evaluate_nutrition_policy,
        )

        cleaned = evidence_bundle.get("cleaned_evidence") or {}
        raw_summary = evidence_bundle.get("raw_summary") or {}

        # Recovery (Phase 1).
        recovery_classified = classify_recovery_state(cleaned, raw_summary)
        recovery_policy = evaluate_recovery_policy(recovery_classified, raw_summary)
        recovery_block["evidence"] = cleaned
        recovery_block["raw_summary"] = raw_summary
        recovery_block["classified_state"] = _classified_to_dict(recovery_classified)
        recovery_block["policy_result"] = _policy_to_dict(recovery_policy)

        # Running (Phase 2 step 3). Reuses recovery's classified_state
        # for the cross-domain peek (sleep_debt_band + resting_hr_band)
        # so a single `--evidence-json` invocation lights up both domains.
        running_signals = derive_running_signals(
            raw_summary,
            running_today=running_today,
            running_history=running_history,
            recovery_classified=recovery_block["classified_state"],
        )
        running_classified = classify_running_state(running_signals)
        running_policy = evaluate_running_policy(running_classified, running_signals)
        running_block["signals"] = running_signals
        running_block["classified_state"] = _running_classified_to_dict(running_classified)
        running_block["policy_result"] = _policy_to_dict(running_policy)

        # Sleep (Phase 3 step 5). Source of truth for sleep_debt_band is
        # now the sleep domain; X1a / X1b in synthesis_policy prefer
        # this block's classified_state.sleep_debt_band over the
        # recovery cross-domain echo.
        sleep_signals = derive_sleep_signals(
            sleep_today=sleep_today,
            sleep_history=sleep_history,
            evidence=cleaned,
        )
        sleep_classified = classify_sleep_state(sleep_signals)
        sleep_policy = evaluate_sleep_policy(sleep_classified, sleep_signals)
        sleep_block["signals"] = sleep_signals
        sleep_block["classified_state"] = _sleep_classified_to_dict(sleep_classified)
        sleep_block["policy_result"] = _policy_to_dict(sleep_policy)

        # Stress (Phase 3 step 5). Source of truth for garmin_stress_band
        # is the stress domain; X7 in synthesis_policy prefers this
        # block's classified_state.garmin_stress_band over the local
        # fallback banding. X6 reads body-battery from stress.today_*.
        stress_signals = derive_stress_signals(
            stress_today=stress_today,
            stress_history=stress_history,
        )
        stress_classified = classify_stress_state(stress_signals)
        stress_policy = evaluate_stress_policy(stress_classified, stress_signals)
        stress_block["signals"] = stress_signals
        stress_block["classified_state"] = _stress_classified_to_dict(stress_classified)
        stress_block["policy_result"] = _policy_to_dict(stress_policy)

        # Strength (Phase 4 step 5). X3a/X3b in synthesis read from
        # ``strength.classified_state.recent_volume_band`` + proposal
        # domain registry; X4 reads ``strength.history`` directly for
        # yesterday's heavy-lower-body signal; X5 reads
        # ``running.history`` for yesterday's long-run signal but
        # targets strength proposals, which depend on the strength
        # block being present in the bundle.
        strength_signals = derive_strength_signals(
            strength_today=strength_today,
            strength_history=strength_history,
            goal_domain=(goals_active[0]["domain"] if goals_active else None),
        )
        strength_classified = classify_strength_state(strength_signals)
        strength_policy = evaluate_strength_policy(strength_classified)
        strength_block["signals"] = strength_signals
        strength_block["classified_state"] = _strength_classified_to_dict(strength_classified)
        strength_block["policy_result"] = _policy_to_dict(strength_policy)

        # Nutrition (Phase 5 step 4). X2 in synthesis reads
        # ``nutrition.classified_state.calorie_deficit_kcal`` +
        # ``protein_ratio`` to decide whether to soften hard
        # training proposals; X9 (Phase B) reads the finalised
        # training action and mutates the nutrition recommendation's
        # action_detail. Both paths require the nutrition block to
        # carry classified_state in the snapshot when the bundle is
        # supplied. goal_domain is reserved for post-v1 goal-aware
        # targets — the v1 classifier ignores it.
        nutrition_signals = derive_nutrition_signals(
            nutrition_today=nutrition_today,
            goal_domain=(goals_active[0]["domain"] if goals_active else None),
        )
        nutrition_classified = classify_nutrition_state(nutrition_signals)
        nutrition_policy = evaluate_nutrition_policy(nutrition_classified)
        nutrition_block["signals"] = nutrition_signals
        nutrition_block["classified_state"] = _nutrition_classified_to_dict(nutrition_classified)
        nutrition_block["policy_result"] = _policy_to_dict(nutrition_policy)

    return {
        "schema_version": "state_snapshot.v1",
        "as_of_date": as_of_date.isoformat(),
        "user_id": user_id,
        "lookback_days": lookback_days,
        "history_range": [lookback_start.isoformat(), (as_of_date - timedelta(days=1)).isoformat()],
        "recovery": recovery_block,
        "running": running_block,
        "sleep": sleep_block,
        "stress": stress_block,
        "strength": strength_block,
        "gym": {
            "today": gym_today,
            "history": _history("gym"),
            "missingness": gym_mx,
        },
        "nutrition": nutrition_block,
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
        "user_memory": user_memory_block,
        "sources": sources_block,
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


def _running_classified_to_dict(classified: Any) -> dict[str, Any]:
    """Convert a ClassifiedRunningState frozen dataclass to a plain dict.

    Field names are the running-readiness skill's contract; do not rename
    here without updating the skill.
    """

    return {
        "weekly_mileage_trend_band": classified.weekly_mileage_trend_band,
        "hard_session_load_band": classified.hard_session_load_band,
        "freshness_band": classified.freshness_band,
        "recovery_adjacent_band": classified.recovery_adjacent_band,
        "coverage_band": classified.coverage_band,
        "running_readiness_status": classified.running_readiness_status,
        "readiness_score": classified.readiness_score,
        "uncertainty": list(classified.uncertainty),
    }


def _sleep_classified_to_dict(classified: Any) -> dict[str, Any]:
    """Convert a ClassifiedSleepState frozen dataclass to a plain dict.

    Field names are the sleep-quality skill's contract; do not rename
    here without updating the skill. ``sleep_debt_band`` is the field
    X1a / X1b read via ``sleep.classified_state.sleep_debt_band``.
    """

    return {
        "sleep_debt_band": classified.sleep_debt_band,
        "sleep_quality_band": classified.sleep_quality_band,
        "sleep_timing_consistency_band": classified.sleep_timing_consistency_band,
        "sleep_efficiency_band": classified.sleep_efficiency_band,
        "coverage_band": classified.coverage_band,
        "sleep_status": classified.sleep_status,
        "sleep_score": classified.sleep_score,
        "sleep_efficiency_pct": classified.sleep_efficiency_pct,
        "uncertainty": list(classified.uncertainty),
    }


def _stress_classified_to_dict(classified: Any) -> dict[str, Any]:
    """Convert a ClassifiedStressState frozen dataclass to a plain dict.

    Field names are the stress-regulation skill's contract; do not
    rename here without updating the skill. ``garmin_stress_band`` is
    the field X7 reads via ``stress.classified_state.garmin_stress_band``.
    """

    return {
        "garmin_stress_band": classified.garmin_stress_band,
        "manual_stress_band": classified.manual_stress_band,
        "body_battery_trend_band": classified.body_battery_trend_band,
        "coverage_band": classified.coverage_band,
        "stress_state": classified.stress_state,
        "stress_score": classified.stress_score,
        "body_battery_delta": classified.body_battery_delta,
        "uncertainty": list(classified.uncertainty),
    }


def _strength_classified_to_dict(classified: Any) -> dict[str, Any]:
    """Convert a ClassifiedStrengthState frozen dataclass to a plain dict.

    Field names are the strength-readiness skill's contract; do not
    rename here without updating the skill. ``recent_volume_band``
    feeds X3a/X3b; ``freshness_band_by_group`` is the richer read that
    X4/X5 may consume directly in Phase 5+ if needed. For v1 X4/X5
    synthesis reads ``strength.history`` and ``running.history``
    directly, not the classified state — the classifier is the skill's
    source of truth, not synthesis_policy's.
    """

    return {
        "recent_volume_band": classified.recent_volume_band,
        "freshness_band_by_group": dict(classified.freshness_band_by_group),
        "coverage_band": classified.coverage_band,
        "strength_status": classified.strength_status,
        "strength_score": classified.strength_score,
        "volume_ratio": classified.volume_ratio,
        "sessions_last_7d": classified.sessions_last_7d,
        "sessions_last_28d": classified.sessions_last_28d,
        "unmatched_exercise_tokens": list(classified.unmatched_exercise_tokens),
        "uncertainty": list(classified.uncertainty),
    }


def _nutrition_classified_to_dict(classified: Any) -> dict[str, Any]:
    """Convert a ClassifiedNutritionState frozen dataclass to a plain dict.

    Field names are the nutrition-alignment skill's contract; do not
    rename here without updating the skill. ``calorie_deficit_kcal`` and
    ``protein_ratio`` feed X2 (nutrition deficit softens training);
    ``micronutrient_coverage`` is always ``unavailable_at_source`` under
    the macros-only v1 derivation. For v1 X2 reads these fields
    directly, mirroring the pattern used for X3 (strength proposals)
    and X4/X5 (cross-domain history reads) — the classifier is the
    skill's source of truth, not synthesis_policy's.
    """

    return {
        "calorie_balance_band": classified.calorie_balance_band,
        "protein_sufficiency_band": classified.protein_sufficiency_band,
        "hydration_band": classified.hydration_band,
        "micronutrient_coverage": classified.micronutrient_coverage,
        "coverage_band": classified.coverage_band,
        "nutrition_status": classified.nutrition_status,
        "nutrition_score": classified.nutrition_score,
        "calorie_deficit_kcal": classified.calorie_deficit_kcal,
        "protein_ratio": classified.protein_ratio,
        "hydration_ratio": classified.hydration_ratio,
        "derivation_path": classified.derivation_path,
        "uncertainty": list(classified.uncertainty),
    }


def _sources_block(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str,
) -> dict[str, Any]:
    """Return ``{source: {last_successful_sync_at, staleness_hours}}`` for
    every source that has ever completed a sync for ``user_id``.

    Staleness is measured from the end of ``as_of_date`` (00:00 UTC on
    the following day) so historical snapshots don't report absurd
    "3 years stale" values for evidence that was fresh when the plan
    ran. A negative staleness (sync completed *after* as_of_date ends)
    is possible for backfill runs; we let it through rather than
    clamping, because the honest signal "this evidence was recorded
    after the civil date it describes" is the kind of thing an auditor
    might want to flag.

    Pre-008 DB: ``latest_successful_sync_per_source`` returns an empty
    dict, and this function mirrors that shape so the snapshot stays
    alive on older DBs.
    """

    from health_agent_infra.core.state.sync_log import (
        latest_successful_sync_per_source,
    )

    rows_by_source = latest_successful_sync_per_source(conn, user_id=user_id)
    if not rows_by_source:
        return {}

    # Reference point: 00:00 UTC on the day AFTER as_of_date (i.e. the
    # instant as_of_date ends). Using end-of-day gives a stable anchor
    # that doesn't drift between test runs or across timezones.
    anchor = datetime.combine(
        as_of_date + timedelta(days=1), time.min, tzinfo=timezone.utc,
    )

    out: dict[str, Any] = {}
    for source, row in rows_by_source.items():
        completed_at_str = row.get("completed_at") or row.get("started_at")
        if not completed_at_str:
            # Shouldn't happen — the query filters on status='ok' which
            # requires complete_sync to have stamped completed_at. Fall
            # through rather than raising so one malformed row doesn't
            # blow up the whole snapshot.
            out[source] = {
                "last_successful_sync_at": None,
                "staleness_hours": None,
            }
            continue
        try:
            completed_at = datetime.fromisoformat(completed_at_str)
        except ValueError:
            out[source] = {
                "last_successful_sync_at": completed_at_str,
                "staleness_hours": None,
            }
            continue
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=timezone.utc)
        staleness_hours = (anchor - completed_at).total_seconds() / 3600.0
        out[source] = {
            "last_successful_sync_at": completed_at.isoformat(),
            "staleness_hours": round(staleness_hours, 2),
        }
    return out


def _user_memory_block(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str,
) -> dict[str, Any]:
    """Return the snapshot's user-memory block for ``as_of_date``.

    Imported lazily (same pattern as the per-domain classify/policy
    imports further up) so the memory module stays out of the state
    package's module-load cycle when the snapshot surface is unused.

    Robust to a DB that predates migration 007: if the ``user_memory``
    table is missing the block degrades to an empty, honestly-shaped
    bundle rather than crashing the snapshot. An operator on that DB
    can fix it with ``hai state migrate``; in the meantime every other
    snapshot surface stays alive.
    """

    from health_agent_infra.core.memory import (
        build_user_memory_bundle,
        bundle_to_dict,
    )

    try:
        bundle = build_user_memory_bundle(
            conn, user_id=user_id, as_of=as_of_date,
        )
    except sqlite3.OperationalError:
        return {
            "as_of": None,
            "counts": {
                "goal": 0, "preference": 0, "constraint": 0,
                "context": 0, "total": 0,
            },
            "entries": [],
        }
    return bundle_to_dict(bundle)


def _policy_to_dict(policy: Any) -> dict[str, Any]:
    """Convert a {Recovery,Running}PolicyResult frozen dataclass to a plain dict.

    Both per-domain results carry the same field set
    (``policy_decisions`` + ``forced_action`` + ``forced_action_detail`` +
    ``capped_confidence``); a single helper handles both.
    """

    return {
        "policy_decisions": [
            {"rule_id": d.rule_id, "decision": d.decision, "note": d.note}
            for d in policy.policy_decisions
        ],
        "forced_action": policy.forced_action,
        "forced_action_detail": policy.forced_action_detail,
        "capped_confidence": policy.capped_confidence,
    }
