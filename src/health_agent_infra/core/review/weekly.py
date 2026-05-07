"""Weekly aggregation queries — W52 (v0.2.0 §2.D).

Read-only loaders gathering per-week state for ``hai review weekly``.
Every plan-scoped query filters on ``superseded_by_plan_id IS NULL``
(per F-PHASE0-07) so the canonical-leaf set is the default view.
Multi-canonical days (two non-superseded plans on the same
``for_date`` — e.g. the 2026-04-24 5-version chain in maintainer
state) surface BOTH rows; the prose layer disposes them with the
literal "multiple plans on this day" prose, not silent latest-wins.

Nine logical queries per PLAN §2.D:
  Q1. ``daily_plan`` rows for the week (canonical-leaf only).
  Q2. ``recommendation_log`` rows linked to those plans.
  Q3. ``x_rule_firing`` rows linked to those plans.
  Q4. ``review_outcome`` rows linked to those recommendations.
  Q5. ``accepted_*_state_daily`` rows (fans across 6 domain tables)
      keyed by ``(as_of_date, user_id)`` for the week.
  Q6. ``data_quality_daily`` rows + ``sync_run_log`` + ``runtime_event_log``
      for the week's data-quality lane.
  Q7. ``intent_item`` rows active during the week.
  Q8. ``target`` rows active during the week.
  Q9. ``recommendation_evidence_card`` rows for the recommendations
      (W-EVCARD-DAILY consumer).

Output is a flat, typed :class:`WeeklyAggregation` row set the
prose builder + render layer consume. W-EXPLAIN-UX-CARRY consumption
lives in ``prose_builder.py``, not here.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional


# Mirrors the W-PROV-1 whitelist for accepted-state tables (verified
# at ``core/provenance/locator.py:_ALLOWED_TABLES_PK`` after v0.2.0
# W-PROV-2's whitelist extension). Order is stable for byte-deterministic
# query iteration.
ACCEPTED_STATE_TABLES: tuple[str, ...] = (
    "accepted_recovery_state_daily",
    "accepted_running_state_daily",
    "accepted_sleep_state_daily",
    "accepted_stress_state_daily",
    "accepted_resistance_training_state_daily",
    "accepted_nutrition_state_daily",
)

# Domain mapping for accepted-state tables. The "strength" domain
# label maps to the ``accepted_resistance_training_state_daily`` table
# (verified at migration 001 line 281); other domains 1-to-1 with the
# table prefix. Used by the prose layer to render per-domain sections.
TABLE_TO_DOMAIN: dict[str, str] = {
    "accepted_recovery_state_daily": "recovery",
    "accepted_running_state_daily": "running",
    "accepted_sleep_state_daily": "sleep",
    "accepted_stress_state_daily": "stress",
    "accepted_resistance_training_state_daily": "strength",
    "accepted_nutrition_state_daily": "nutrition",
}


# ---------------------------------------------------------------------------
# ISO-week helper
# ---------------------------------------------------------------------------


def iso_week_dates(iso_week: str) -> list[date]:
    """Return the 7 civil dates of the ISO week.

    ``iso_week`` is a string of shape ``YYYY-Www`` (e.g. ``2026-W18``).
    Days are returned in chronological order (Monday → Sunday) using
    ``date.fromisocalendar`` so leap-week semantics match the stdlib.
    """

    if len(iso_week) != 8 or iso_week[4:6] != "-W":
        raise ValueError(
            f"iso_week must be 'YYYY-Www' (8 chars, 'W' at index 5); "
            f"got {iso_week!r}"
        )
    try:
        year = int(iso_week[:4])
        week = int(iso_week[6:8])
    except ValueError as exc:
        raise ValueError(
            f"iso_week must be 'YYYY-Www' with numeric year+week; "
            f"got {iso_week!r}"
        ) from exc
    return [date.fromisocalendar(year, week, dow) for dow in range(1, 8)]


# ---------------------------------------------------------------------------
# Typed row dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CanonicalPlanRow:
    daily_plan_id: str
    user_id: str
    for_date: str
    synthesized_at: str
    recommendation_ids: list[str]
    proposal_ids: list[str]
    x_rules_fired: list[str]
    synthesis_meta: Optional[dict[str, Any]]
    superseded_by_plan_id: Optional[str]
    superseded_at: Optional[str]


@dataclass(frozen=True)
class WeeklyRecommendation:
    recommendation_id: str
    daily_plan_id: Optional[str]
    user_id: str
    for_date: str
    domain: str
    action: str
    confidence: str
    bounded: bool
    issued_at: str
    payload: dict[str, Any]
    evidence_locators: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class WeeklyXRuleFiring:
    firing_id: int
    daily_plan_id: str
    user_id: str
    x_rule_id: str
    tier: str
    affected_domain: str
    trigger_note: str
    mutation: Optional[Any]
    source_signals: dict[str, Any]
    fired_at: str


@dataclass(frozen=True)
class WeeklyReviewOutcome:
    outcome_id: int
    review_event_id: str
    recommendation_id: str
    user_id: str
    domain: str
    recorded_at: str
    followed_recommendation: bool
    self_reported_improvement: Optional[bool]
    completed: Optional[bool]
    intensity_delta: Optional[str]
    duration_minutes: Optional[int]
    pre_energy_score: Optional[int]
    post_energy_score: Optional[int]
    disagreed_firing_ids: list[int]
    free_text: Optional[str]


@dataclass(frozen=True)
class WeeklyEvidenceCard:
    card_id: str
    daily_plan_id: str
    recommendation_id: str
    domain: str
    schema_version: str
    payload: dict[str, Any]
    computed_at: str


@dataclass(frozen=True)
class WeeklyAcceptedStateRow:
    table: str
    domain: str
    as_of_date: str
    user_id: str
    columns: dict[str, Any]


@dataclass(frozen=True)
class WeeklyDataQualityRow:
    user_id: str
    as_of_date: str
    domain: str
    source: str
    freshness_hours: Optional[float]
    coverage_band: Optional[str]
    missingness: Optional[str]
    source_unavailable: bool
    user_input_pending: bool
    suspicious_discontinuity: bool
    cold_start_window_state: Optional[str]
    computed_at: str


@dataclass(frozen=True)
class WeeklySyncRunRow:
    sync_id: int
    source: str
    user_id: str
    mode: str
    started_at: str
    completed_at: Optional[str]
    status: str
    for_date: Optional[str]


@dataclass(frozen=True)
class WeeklyRuntimeEventRow:
    event_id: int
    command: str
    user_id: Optional[str]
    started_at: str
    completed_at: Optional[str]
    status: str
    exit_code: Optional[int]


@dataclass(frozen=True)
class WeeklyIntentRow:
    intent_id: str
    user_id: str
    domain: str
    scope_type: str
    scope_start: str
    scope_end: str
    intent_type: str
    status: str
    priority: str
    flexibility: str
    payload: dict[str, Any]
    reason: str
    source: str
    effective_at: str


@dataclass(frozen=True)
class WeeklyTargetRow:
    target_id: str
    user_id: str
    domain: str
    target_type: str
    status: str
    value: Any
    unit: str
    lower_bound: Optional[float]
    upper_bound: Optional[float]
    effective_from: str
    effective_to: Optional[str]
    reason: str


@dataclass(frozen=True)
class WeeklyCoverage:
    """Coverage decision for the week — drives the abstain branch.

    Per PLAN §2.D, this is the structurally simpler validation path:
    the prose layer reads the populated counts, threshold value, and
    date lists directly, so the rendered abstain prose is a literal
    substitution from query output (counts + dates) plus a literal
    substitution from `thresholds.toml` (threshold). No prose
    authoring sits between the data and the rendered string, which
    is why the abstain branch writes no claim cards (validation is
    by construction; W58D is unnecessary on this path).

    `weekly_status` is `"insufficient_data"` when fewer days have
    canonical plans than the configured threshold; otherwise `"ok"`.
    Multi-canonical days (F-PHASE0-07: two non-superseded plans on
    the same `for_date`) count once toward `days_with_plans` — the
    metric is "days with plan evidence", not "plans count".
    """

    weekly_status: str
    iso_week: str
    days_with_plans: int
    coverage_threshold: int
    populated_dates: list[str]
    missing_dates: list[str]


@dataclass(frozen=True)
class WeeklyAggregation:
    """All loaded rows for one week, deterministically structured."""

    iso_week: str
    user_id: str
    week_dates: list[str]
    canonical_plans: list[CanonicalPlanRow]
    recommendations: list[WeeklyRecommendation]
    x_rule_firings: list[WeeklyXRuleFiring]
    review_outcomes: list[WeeklyReviewOutcome]
    evidence_cards: list[WeeklyEvidenceCard]
    accepted_state_rows: list[WeeklyAcceptedStateRow]
    data_quality_rows: list[WeeklyDataQualityRow]
    sync_runs: list[WeeklySyncRunRow]
    runtime_events: list[WeeklyRuntimeEventRow]
    intent_rows: list[WeeklyIntentRow]
    target_rows: list[WeeklyTargetRow]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def evaluate_weekly_coverage(
    aggregation: WeeklyAggregation,
    *,
    coverage_threshold_days: int,
) -> WeeklyCoverage:
    """Determine whether the week has enough plan evidence to render
    quantitative prose, or should fall through to the
    ``insufficient_data`` abstain branch.

    Per PLAN §2.D acceptance #2, the abstain branch fires when fewer
    than ``coverage_threshold_days`` of the 7 ISO-week days carry a
    canonical (non-superseded) daily_plan. Multi-canonical days count
    once toward the day count — both rows surface in the aggregation
    but the coverage metric is "days with plan evidence".

    The returned :class:`WeeklyCoverage` carries the four substitution
    inputs the abstain prose template needs (per PLAN §2.D abstain
    output shape): ``days_with_plans``, ``coverage_threshold``,
    ``populated_dates``, ``missing_dates``. The substitution is
    deterministic — same week + same DB → byte-identical metadata.

    The threshold value is passed in (D13 trust-by-design contract).
    Production callers resolve it via
    ``core.config.load_thresholds()['policy']['review_weekly']
    ['coverage_threshold_days']`` so type validation runs at the
    threshold-injection seam, not here.
    """

    populated_dates = sorted({plan.for_date for plan in aggregation.canonical_plans})
    populated_set = set(populated_dates)
    missing_dates = [d for d in aggregation.week_dates if d not in populated_set]
    days_with_plans = len(populated_dates)
    weekly_status = (
        "insufficient_data"
        if days_with_plans < coverage_threshold_days
        else "ok"
    )
    return WeeklyCoverage(
        weekly_status=weekly_status,
        iso_week=aggregation.iso_week,
        days_with_plans=days_with_plans,
        coverage_threshold=coverage_threshold_days,
        populated_dates=populated_dates,
        missing_dates=missing_dates,
    )


def load_weekly_aggregation(
    conn: sqlite3.Connection,
    *,
    iso_week: str,
    user_id: str,
) -> WeeklyAggregation:
    """Run all 9 aggregation queries for one ``(iso_week, user_id)``.

    Plan-scoped queries (Q1-Q4 + Q9) filter on
    ``superseded_by_plan_id IS NULL``; the date-keyed queries (Q5-Q8)
    + active-window queries (Q7-Q8 ledger reads) are unaffected by
    supersession. The returned :class:`WeeklyAggregation` is a flat,
    typed row set the prose builder + render layer consume.
    """

    week_dates = iso_week_dates(iso_week)
    week_date_strs = [d.isoformat() for d in week_dates]

    canonical_plans = _load_canonical_plans(
        conn, user_id=user_id, week_dates=week_date_strs,
    )
    plan_ids = [p.daily_plan_id for p in canonical_plans]

    recommendations = _load_recommendations_for_plans(conn, plan_ids)
    rec_ids = [r.recommendation_id for r in recommendations]

    return WeeklyAggregation(
        iso_week=iso_week,
        user_id=user_id,
        week_dates=week_date_strs,
        canonical_plans=canonical_plans,
        recommendations=recommendations,
        x_rule_firings=_load_firings_for_plans(conn, plan_ids),
        review_outcomes=_load_outcomes_for_recommendations(conn, rec_ids),
        evidence_cards=_load_evidence_cards_for_plans(conn, plan_ids),
        accepted_state_rows=_load_accepted_state_for_week(
            conn, user_id=user_id, week_dates=week_date_strs,
        ),
        data_quality_rows=_load_data_quality_for_week(
            conn, user_id=user_id, week_dates=week_date_strs,
        ),
        sync_runs=_load_sync_runs_for_week(
            conn, user_id=user_id, week_dates=week_date_strs,
        ),
        runtime_events=_load_runtime_events_for_week(
            conn, user_id=user_id, week_dates=week_date_strs,
        ),
        intent_rows=_load_intent_active_in_week(
            conn, user_id=user_id, week_dates=week_date_strs,
        ),
        target_rows=_load_target_active_in_week(
            conn, user_id=user_id, week_dates=week_date_strs,
        ),
    )


# ---------------------------------------------------------------------------
# Q1 — daily_plan canonical-leaf
# ---------------------------------------------------------------------------


def _load_canonical_plans(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    week_dates: list[str],
) -> list[CanonicalPlanRow]:
    """Q1 — daily_plan rows for the week, filtered on
    ``superseded_by_plan_id IS NULL`` (F-PHASE0-07). Multi-canonical
    days surface both rows (no silent latest-wins).
    """

    if not week_dates:
        return []
    placeholders = ",".join(["?"] * len(week_dates))
    rows = conn.execute(
        f"SELECT daily_plan_id, user_id, for_date, synthesized_at, "  # nosec B608 - placeholders are literal "?" tokens; week_dates bind through params, not f-string.
        f"       recommendation_ids_json, proposal_ids_json, "
        f"       x_rules_fired_json, synthesis_meta_json, "
        f"       superseded_by_plan_id, superseded_at "
        f"FROM daily_plan "
        f"WHERE user_id = ? AND for_date IN ({placeholders}) "
        f"  AND superseded_by_plan_id IS NULL "
        f"ORDER BY for_date ASC, synthesized_at ASC, daily_plan_id ASC",
        (user_id, *week_dates),
    ).fetchall()
    return [
        CanonicalPlanRow(
            daily_plan_id=row["daily_plan_id"],
            user_id=row["user_id"],
            for_date=row["for_date"],
            synthesized_at=row["synthesized_at"],
            recommendation_ids=_loads_or_empty(
                row["recommendation_ids_json"], list,
            ),
            proposal_ids=_loads_or_empty(
                row["proposal_ids_json"], list,
            ),
            x_rules_fired=_loads_or_empty(
                row["x_rules_fired_json"], list,
            ),
            synthesis_meta=_loads_or_none(row["synthesis_meta_json"]),
            superseded_by_plan_id=row["superseded_by_plan_id"],
            superseded_at=row["superseded_at"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Q2 — recommendation_log scoped to canonical-leaf plan ids
# ---------------------------------------------------------------------------


def _load_recommendations_for_plans(
    conn: sqlite3.Connection,
    plan_ids: list[str],
) -> list[WeeklyRecommendation]:
    """Q2 — recommendation_log rows for the canonical-leaf plan id
    set. Domain column lives on the row (mig 003); evidence_locators
    live in the dedicated column (mig 023) with payload_json fallback
    for legacy rows per ``_load_recommendations_for_plan`` precedent.
    """

    if not plan_ids:
        return []
    placeholders = ",".join(["?"] * len(plan_ids))
    rows = conn.execute(
        f"SELECT recommendation_id, daily_plan_id, user_id, for_date, "  # nosec B608 - placeholders are literal "?" tokens; plan_ids bind through params, not f-string.
        f"       domain, action, confidence, bounded, payload_json, "
        f"       issued_at, evidence_locators_json "
        f"FROM recommendation_log "
        f"WHERE daily_plan_id IN ({placeholders}) "
        f"ORDER BY for_date ASC, domain ASC, recommendation_id ASC",
        plan_ids,
    ).fetchall()
    out: list[WeeklyRecommendation] = []
    for row in rows:
        payload = _loads_or_empty(row["payload_json"], dict)
        locators_blob = (
            row["evidence_locators_json"]
            if "evidence_locators_json" in row.keys() else None
        )
        if locators_blob:
            evidence_locators = _loads_or_empty(locators_blob, list)
        else:
            evidence_locators = list(payload.get("evidence_locators") or [])
        out.append(
            WeeklyRecommendation(
                recommendation_id=row["recommendation_id"],
                daily_plan_id=row["daily_plan_id"],
                user_id=row["user_id"],
                for_date=row["for_date"],
                domain=row["domain"],
                action=row["action"],
                confidence=row["confidence"],
                bounded=bool(row["bounded"]),
                issued_at=row["issued_at"],
                payload=payload,
                evidence_locators=evidence_locators,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Q3 — x_rule_firing scoped to canonical-leaf plan ids
# ---------------------------------------------------------------------------


def _load_firings_for_plans(
    conn: sqlite3.Connection,
    plan_ids: list[str],
) -> list[WeeklyXRuleFiring]:
    """Q3 — x_rule_firing rows scoped to plan ids. Tier + affected
    domain expose Phase A vs Phase B classification (W-EXPLAIN-UX
    obligation #2)."""

    if not plan_ids:
        return []
    placeholders = ",".join(["?"] * len(plan_ids))
    rows = conn.execute(
        f"SELECT firing_id, daily_plan_id, user_id, x_rule_id, tier, "  # nosec B608 - placeholders are literal "?" tokens; plan_ids bind through params, not f-string.
        f"       affected_domain, trigger_note, mutation_json, "
        f"       source_signals_json, fired_at "
        f"FROM x_rule_firing "
        f"WHERE daily_plan_id IN ({placeholders}) "
        f"ORDER BY daily_plan_id ASC, fired_at ASC, firing_id ASC",
        plan_ids,
    ).fetchall()
    return [
        WeeklyXRuleFiring(
            firing_id=row["firing_id"],
            daily_plan_id=row["daily_plan_id"],
            user_id=row["user_id"],
            x_rule_id=row["x_rule_id"],
            tier=row["tier"],
            affected_domain=row["affected_domain"],
            trigger_note=row["trigger_note"],
            mutation=_loads_or_none(row["mutation_json"]),
            source_signals=_loads_or_empty(
                row["source_signals_json"], dict,
            ),
            fired_at=row["fired_at"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Q4 — review_outcome scoped to recommendation ids
# ---------------------------------------------------------------------------


def _load_outcomes_for_recommendations(
    conn: sqlite3.Connection,
    rec_ids: list[str],
) -> list[WeeklyReviewOutcome]:
    """Q4 — review_outcome rows scoped to recommendation ids.
    Includes the v0.1.x enrichments (mig 010): completed,
    intensity_delta, duration_minutes, pre/post_energy_score,
    disagreed_firing_ids.
    """

    if not rec_ids:
        return []
    placeholders = ",".join(["?"] * len(rec_ids))
    rows = conn.execute(
        f"SELECT outcome_id, review_event_id, recommendation_id, "  # nosec B608 - placeholders are literal "?" tokens; rec_ids bind through params, not f-string.
        f"       user_id, domain, recorded_at, "
        f"       followed_recommendation, self_reported_improvement, "
        f"       completed, intensity_delta, duration_minutes, "
        f"       pre_energy_score, post_energy_score, "
        f"       disagreed_firing_ids, free_text "
        f"FROM review_outcome "
        f"WHERE recommendation_id IN ({placeholders}) "
        f"ORDER BY recorded_at ASC, outcome_id ASC",
        rec_ids,
    ).fetchall()
    return [
        WeeklyReviewOutcome(
            outcome_id=row["outcome_id"],
            review_event_id=row["review_event_id"],
            recommendation_id=row["recommendation_id"],
            user_id=row["user_id"],
            domain=row["domain"],
            recorded_at=row["recorded_at"],
            followed_recommendation=bool(row["followed_recommendation"]),
            self_reported_improvement=(
                bool(row["self_reported_improvement"])
                if row["self_reported_improvement"] is not None else None
            ),
            completed=(
                bool(row["completed"])
                if row["completed"] is not None else None
            ),
            intensity_delta=row["intensity_delta"],
            duration_minutes=row["duration_minutes"],
            pre_energy_score=row["pre_energy_score"],
            post_energy_score=row["post_energy_score"],
            disagreed_firing_ids=_loads_or_empty(
                row["disagreed_firing_ids"], list,
            ),
            free_text=row["free_text"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Q5 — accepted_*_state_daily fan-out across 6 domain tables
# ---------------------------------------------------------------------------


def _load_accepted_state_for_week(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    week_dates: list[str],
) -> list[WeeklyAcceptedStateRow]:
    """Q5 — fan-out across the 6 ``accepted_*_state_daily`` tables.

    Table names cannot be parameterised in SQLite, so we iterate the
    whitelist (:data:`ACCEPTED_STATE_TABLES`) and run one SELECT per
    table. Each SELECT uses ``SELECT *`` (the columns vary across
    domains; the prose layer only reads what it needs by table key).
    """

    if not week_dates:
        return []
    placeholders = ",".join(["?"] * len(week_dates))
    out: list[WeeklyAcceptedStateRow] = []
    for table in ACCEPTED_STATE_TABLES:
        # Whitelist guarantees `table` is a literal allowed name; no
        # binding into the f-string is needed.
        try:
            rows = conn.execute(
                f"SELECT * FROM {table} "  # nosec B608 - table comes from compile-time whitelist ACCEPTED_STATE_TABLES; user_id + week_dates bind through params.
                f"WHERE user_id = ? AND as_of_date IN ({placeholders}) "
                f"ORDER BY as_of_date ASC",
                (user_id, *week_dates),
            ).fetchall()
        except sqlite3.OperationalError:
            # Table may not exist on a legacy DB that hasn't applied
            # migrations 003 / 004 / 006 yet. Degrade gracefully.
            continue
        domain = TABLE_TO_DOMAIN[table]
        for row in rows:
            cols = {k: row[k] for k in row.keys()}
            out.append(WeeklyAcceptedStateRow(
                table=table,
                domain=domain,
                as_of_date=row["as_of_date"],
                user_id=row["user_id"],
                columns=cols,
            ))
    return out


# ---------------------------------------------------------------------------
# Q6 — data_quality_daily for the week
# ---------------------------------------------------------------------------


def _load_data_quality_for_week(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    week_dates: list[str],
) -> list[WeeklyDataQualityRow]:
    """Q6 — data_quality_daily rows for the week. The data-quality
    rollup (stale_pull vs retrospective_manual) is computed at the
    prose layer using the joined sync_run_log + runtime_event_log
    rows; this loader only reads the dq table itself.
    """

    if not week_dates:
        return []
    placeholders = ",".join(["?"] * len(week_dates))
    rows = conn.execute(
        f"SELECT user_id, as_of_date, domain, source, "  # nosec B608 - placeholders are literal "?" tokens; week_dates bind through params, not f-string.
        f"       freshness_hours, coverage_band, missingness, "
        f"       source_unavailable, user_input_pending, "
        f"       suspicious_discontinuity, cold_start_window_state, "
        f"       computed_at "
        f"FROM data_quality_daily "
        f"WHERE user_id = ? AND as_of_date IN ({placeholders}) "
        f"ORDER BY as_of_date ASC, domain ASC, source ASC",
        (user_id, *week_dates),
    ).fetchall()
    return [
        WeeklyDataQualityRow(
            user_id=row["user_id"],
            as_of_date=row["as_of_date"],
            domain=row["domain"],
            source=row["source"],
            freshness_hours=row["freshness_hours"],
            coverage_band=row["coverage_band"],
            missingness=row["missingness"],
            source_unavailable=bool(row["source_unavailable"]),
            user_input_pending=bool(row["user_input_pending"]),
            suspicious_discontinuity=bool(row["suspicious_discontinuity"]),
            cold_start_window_state=row["cold_start_window_state"],
            computed_at=row["computed_at"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Q7 — sync_run_log for the week (data-quality lane)
# ---------------------------------------------------------------------------


def _load_sync_runs_for_week(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    week_dates: list[str],
) -> list[WeeklySyncRunRow]:
    """Q7 — sync_run_log rows whose ``for_date`` falls in the week
    OR whose ``started_at`` date prefix falls in the week. Both
    matter for data-quality classification: a stale_pull row may
    have ``for_date < started_at - 48h`` (per F-PLAN-04) while a
    retrospective_manual row may have ``mode='manual'`` and any
    ``for_date < started_at``.
    """

    if not week_dates:
        return []
    placeholders = ",".join(["?"] * len(week_dates))
    week_start = week_dates[0]
    # `started_at` LIKE clause matches the ISO date prefix; week-
    # spanning runs surface even when for_date is NULL.
    week_end = week_dates[-1]
    rows = conn.execute(
        f"SELECT sync_id, source, user_id, mode, started_at, "  # nosec B608 - placeholders are literal "?" tokens; week_dates bind through params, not f-string.
        f"       completed_at, status, for_date "
        f"FROM sync_run_log "
        f"WHERE user_id = ? AND ("
        f"      for_date IN ({placeholders}) "
        f"   OR substr(started_at, 1, 10) BETWEEN ? AND ?"
        f") "
        f"ORDER BY started_at ASC, sync_id ASC",
        (user_id, *week_dates, week_start, week_end),
    ).fetchall()
    return [
        WeeklySyncRunRow(
            sync_id=row["sync_id"],
            source=row["source"],
            user_id=row["user_id"],
            mode=row["mode"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            status=row["status"],
            for_date=row["for_date"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Q8 — runtime_event_log for the week (command-cadence lane)
# ---------------------------------------------------------------------------


def _load_runtime_events_for_week(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    week_dates: list[str],
) -> list[WeeklyRuntimeEventRow]:
    """Q8 — runtime_event_log rows whose ``started_at`` date prefix
    falls in the week. Used by the prose layer to surface "you ran
    ``hai daily`` 3 of 7 days" cadence claims (W-EXPLAIN-UX
    obligation backdrop).
    """

    if not week_dates:
        return []
    week_start = week_dates[0]
    week_end = week_dates[-1]
    rows = conn.execute(
        "SELECT event_id, command, user_id, started_at, completed_at, "
        "       status, exit_code "
        "FROM runtime_event_log "
        "WHERE (user_id = ? OR user_id IS NULL) "
        "  AND substr(started_at, 1, 10) BETWEEN ? AND ? "
        "ORDER BY started_at ASC, event_id ASC",
        (user_id, week_start, week_end),
    ).fetchall()
    return [
        WeeklyRuntimeEventRow(
            event_id=row["event_id"],
            command=row["command"],
            user_id=row["user_id"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            status=row["status"],
            exit_code=row["exit_code"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Q9 — intent_item active during the week
# ---------------------------------------------------------------------------


def _load_intent_active_in_week(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    week_dates: list[str],
) -> list[WeeklyIntentRow]:
    """Q9 (intent half) — intent_item rows whose
    ``[scope_start, scope_end]`` window overlaps the week. Active
    statuses only; superseded/archived ledger rows are filtered out
    so the weekly view sees the user's currently-acknowledged intent.
    """

    if not week_dates:
        return []
    week_start = week_dates[0]
    week_end = week_dates[-1]
    rows = conn.execute(
        "SELECT intent_id, user_id, domain, scope_type, scope_start, "
        "       scope_end, intent_type, status, priority, flexibility, "
        "       payload_json, reason, source, effective_at "
        "FROM intent_item "
        "WHERE user_id = ? "
        "  AND status IN ('proposed', 'active') "
        "  AND scope_start <= ? AND scope_end >= ? "
        "ORDER BY scope_start ASC, intent_id ASC",
        (user_id, week_end, week_start),
    ).fetchall()
    return [
        WeeklyIntentRow(
            intent_id=row["intent_id"],
            user_id=row["user_id"],
            domain=row["domain"],
            scope_type=row["scope_type"],
            scope_start=row["scope_start"],
            scope_end=row["scope_end"],
            intent_type=row["intent_type"],
            status=row["status"],
            priority=row["priority"],
            flexibility=row["flexibility"],
            payload=_loads_or_empty(row["payload_json"], dict),
            reason=row["reason"],
            source=row["source"],
            effective_at=row["effective_at"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Q9 (target half) — target active during the week
# ---------------------------------------------------------------------------


def _load_target_active_in_week(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    week_dates: list[str],
) -> list[WeeklyTargetRow]:
    """Q9 (target half) — target rows whose
    ``[effective_from, effective_to]`` window overlaps the week.
    ``effective_to IS NULL`` means open-ended (still active).
    """

    if not week_dates:
        return []
    week_start = week_dates[0]
    week_end = week_dates[-1]
    rows = conn.execute(
        "SELECT target_id, user_id, domain, target_type, status, "
        "       value_json, unit, lower_bound, upper_bound, "
        "       effective_from, effective_to, reason "
        "FROM target "
        "WHERE user_id = ? "
        "  AND status IN ('proposed', 'active') "
        "  AND effective_from <= ? "
        "  AND (effective_to IS NULL OR effective_to >= ?) "
        "ORDER BY effective_from ASC, target_id ASC",
        (user_id, week_end, week_start),
    ).fetchall()
    return [
        WeeklyTargetRow(
            target_id=row["target_id"],
            user_id=row["user_id"],
            domain=row["domain"],
            target_type=row["target_type"],
            status=row["status"],
            value=_loads_or_none(row["value_json"]),
            unit=row["unit"],
            lower_bound=row["lower_bound"],
            upper_bound=row["upper_bound"],
            effective_from=row["effective_from"],
            effective_to=row["effective_to"],
            reason=row["reason"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Q9 (final) — recommendation_evidence_card scoped to plan ids
# ---------------------------------------------------------------------------


def _load_evidence_cards_for_plans(
    conn: sqlite3.Connection,
    plan_ids: list[str],
) -> list[WeeklyEvidenceCard]:
    """Q9 (evidence-card half) — recommendation_evidence_card rows
    scoped to canonical-leaf plan ids. Returns an empty list on a DB
    that hasn't applied migration 027 (legacy / pre-W-EVCARD-DAILY).
    """

    if not plan_ids:
        return []
    placeholders = ",".join(["?"] * len(plan_ids))
    try:
        rows = conn.execute(
            f"SELECT card_id, daily_plan_id, recommendation_id, domain, "  # nosec B608 - placeholders are literal "?" tokens; plan_ids bind through params, not f-string.
            f"       schema_version, payload_json, computed_at "
            f"FROM recommendation_evidence_card "
            f"WHERE daily_plan_id IN ({placeholders}) "
            f"ORDER BY daily_plan_id ASC, domain ASC, computed_at ASC",
            plan_ids,
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    return [
        WeeklyEvidenceCard(
            card_id=row["card_id"],
            daily_plan_id=row["daily_plan_id"],
            recommendation_id=row["recommendation_id"],
            domain=row["domain"],
            schema_version=row["schema_version"],
            payload=_loads_or_empty(row["payload_json"], dict),
            computed_at=row["computed_at"],
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# JSON deserialisation helpers
# ---------------------------------------------------------------------------


def _loads_or_empty(blob: Optional[str], kind: type) -> Any:
    if not blob:
        return kind()
    try:
        parsed = json.loads(blob)
    except (TypeError, ValueError):
        return kind()
    if not isinstance(parsed, kind):
        return kind()
    return parsed


def _loads_or_none(blob: Optional[str]) -> Any:
    if not blob:
        return None
    try:
        return json.loads(blob)
    except (TypeError, ValueError):
        return None
