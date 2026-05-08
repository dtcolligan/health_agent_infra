"""Pure dict builders for v0.1.8 ledger rows.

Each builder takes defaults that produce a valid, complete row and lets
callers override individual fields by kwarg. Returned dicts mirror the
column names declared in ``reporting/plans/v0_1_8/PLAN.md`` § 2 so that
callers writing today against the future shape don't drift when
migrations 019 / 020 / 021 land.

The builders deliberately do NOT touch SQLite. Seeding lives in
``seeders.py`` and is gated on the matching migration existing in
``src/health_agent_infra/core/state/migrations``.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any, Optional


# Default user / dates used across the builders. Pulled in from the
# session bootstrap dates already used by the v0.1.7 test fixtures
# (``date(2026, 4, 17)`` is the canonical "yesterday" the recovery suite
# anchors against).
_DEFAULT_USER = "u_test"
_DEFAULT_DATE = date(2026, 4, 18)
_DEFAULT_NOW = datetime(2026, 4, 18, 7, 0, tzinfo=timezone.utc)


def _iso(value: datetime | date | str | None) -> Optional[str]:
    """Render dates / datetimes as ISO 8601, leaving strings + None alone."""

    if value is None or isinstance(value, str):
        return value
    return value.isoformat()


# ---------------------------------------------------------------------------
# W49 — intent_item (migration 019, not yet landed)
# ---------------------------------------------------------------------------


def make_intent_row(
    *,
    intent_id: str = "intent_1",
    user_id: str = _DEFAULT_USER,
    domain: str = "running",
    scope_type: str = "day",
    scope_start: date | str = _DEFAULT_DATE,
    scope_end: date | str | None = None,
    intent_type: str = "training_session",
    status: str = "active",
    priority: str = "normal",
    flexibility: str = "flexible",
    payload: dict[str, Any] | None = None,
    payload_json: str | None = None,
    reason: str = "user-stated plan for the day",
    source: str = "user_authored",
    ingest_actor: str = "cli",
    created_at: datetime | str = _DEFAULT_NOW,
    effective_at: datetime | str = _DEFAULT_NOW,
    review_after: datetime | str | None = None,
    supersedes_intent_id: Optional[str] = None,
    superseded_by_intent_id: Optional[str] = None,
) -> dict[str, Any]:
    """Build one ``intent_item`` row dict (W49, migration 019)."""

    if payload_json is None:
        payload_json = json.dumps(payload if payload is not None else {})
    if scope_end is None:
        scope_end = scope_start

    return {
        "intent_id": intent_id,
        "user_id": user_id,
        "domain": domain,
        "scope_type": scope_type,
        "scope_start": _iso(scope_start),
        "scope_end": _iso(scope_end),
        "intent_type": intent_type,
        "status": status,
        "priority": priority,
        "flexibility": flexibility,
        "payload_json": payload_json,
        "reason": reason,
        "source": source,
        "ingest_actor": ingest_actor,
        "created_at": _iso(created_at),
        "effective_at": _iso(effective_at),
        "review_after": _iso(review_after),
        "supersedes_intent_id": supersedes_intent_id,
        "superseded_by_intent_id": superseded_by_intent_id,
    }


# ---------------------------------------------------------------------------
# W50 — target (migration 020, not yet landed)
# ---------------------------------------------------------------------------


def make_target_row(
    *,
    target_id: str = "target_1",
    user_id: str = _DEFAULT_USER,
    domain: str = "nutrition",
    target_type: str = "hydration_ml",
    status: str = "active",
    value: Any = 3000,
    value_json: str | None = None,
    unit: str = "ml",
    lower_bound: Optional[float] = None,
    upper_bound: Optional[float] = None,
    effective_from: date | str = _DEFAULT_DATE,
    effective_to: date | str | None = None,
    review_after: date | str | None = None,
    reason: str = "baseline hydration target",
    source: str = "user_authored",
    ingest_actor: str = "cli",
    created_at: datetime | str = _DEFAULT_NOW,
    supersedes_target_id: Optional[str] = None,
    superseded_by_target_id: Optional[str] = None,
) -> dict[str, Any]:
    """Build one ``target`` row dict (W50, migration 020)."""

    if value_json is None:
        value_json = json.dumps({"value": value})

    return {
        "target_id": target_id,
        "user_id": user_id,
        "domain": domain,
        "target_type": target_type,
        "status": status,
        "value_json": value_json,
        "unit": unit,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "effective_from": _iso(effective_from),
        "effective_to": _iso(effective_to),
        "review_after": _iso(review_after),
        "reason": reason,
        "source": source,
        "ingest_actor": ingest_actor,
        "created_at": _iso(created_at),
        "supersedes_target_id": supersedes_target_id,
        "superseded_by_target_id": superseded_by_target_id,
    }


# ---------------------------------------------------------------------------
# W51 — data_quality_daily (migration 021, not yet landed)
# ---------------------------------------------------------------------------


def make_data_quality_row(
    *,
    user_id: str = _DEFAULT_USER,
    as_of_date: date | str = _DEFAULT_DATE,
    domain: str = "recovery",
    source: str = "garmin",
    freshness_hours: Optional[float] = 12.0,
    coverage_band: str = "full",
    missingness: str = "absent",
    source_unavailable: int = 0,
    user_input_pending: int = 0,
    suspicious_discontinuity: int = 0,
    cold_start_window_state: str = "post_cold_start",
    computed_at: datetime | str = _DEFAULT_NOW,
) -> dict[str, Any]:
    """Build one ``data_quality_daily`` row dict (W51, migration 021)."""

    return {
        "user_id": user_id,
        "as_of_date": _iso(as_of_date),
        "domain": domain,
        "source": source,
        "freshness_hours": freshness_hours,
        "coverage_band": coverage_band,
        "missingness": missingness,
        "source_unavailable": source_unavailable,
        "user_input_pending": user_input_pending,
        "suspicious_discontinuity": suspicious_discontinuity,
        "cold_start_window_state": cold_start_window_state,
        "computed_at": _iso(computed_at),
    }


# ---------------------------------------------------------------------------
# W48 / W38 — recommendation_log → review_event → review_outcome chain
# (tables already exist; seeder in seeders.py inserts the result.)
# ---------------------------------------------------------------------------


def make_outcome_chain(
    *,
    recommendation_id: str = "rec_1",
    review_event_id: str = "rev_1",
    user_id: str = _DEFAULT_USER,
    domain: str = "running",
    for_date: date | str = _DEFAULT_DATE,
    issued_at: datetime | str = _DEFAULT_NOW,
    review_at: datetime | str | None = None,
    recorded_at: datetime | str | None = None,
    action: str = "proceed_with_planned_run",
    confidence: str = "high",
    bounded: int = 1,
    payload: dict[str, Any] | None = None,
    payload_json: str | None = None,
    review_question: str = "Did the session feel appropriate?",
    followed: bool = True,
    improved: Optional[bool] = True,
    free_text: Optional[str] = None,
    completed: Optional[bool] = None,
    intensity_delta: Optional[str] = None,
    duration_minutes: Optional[int] = None,
    pre_energy_score: Optional[int] = None,
    post_energy_score: Optional[int] = None,
    disagreed_firing_ids: Optional[list[str]] = None,
    re_linked_from_recommendation_id: Optional[str] = None,
    re_link_note: Optional[str] = None,
    source: str = "claude_agent_v1",
    ingest_actor: str = "claude_agent_v1",
) -> dict[str, dict[str, Any]]:
    """Build a ``{recommendation, event, outcome}`` triplet for review tests.

    The three dicts share ``user_id``, ``domain``, ``recommendation_id``,
    and ``review_event_id`` so the FK chain is internally consistent. Any
    field can be overridden via kwargs; the enrichment fields default to
    NULL so legacy-shape outcomes round-trip too.

    Returns a dict (not a tuple) so consumers can call
    ``seed_outcome_chain(conn, **chain)`` without positional coupling.
    """

    if review_at is None:
        review_at = (
            issued_at
            if isinstance(issued_at, str)
            else issued_at.replace(hour=19)
        )
    if recorded_at is None:
        recorded_at = review_at
    if payload_json is None:
        payload_json = json.dumps(payload if payload is not None else {})

    recommendation = {
        "recommendation_id": recommendation_id,
        "user_id": user_id,
        "for_date": _iso(for_date),
        "issued_at": _iso(issued_at),
        "action": action,
        "confidence": confidence,
        "bounded": bounded,
        "payload_json": payload_json,
        "jsonl_offset": None,
        "source": source,
        "ingest_actor": ingest_actor,
        "agent_version": ingest_actor,
        "produced_at": _iso(issued_at),
        "validated_at": _iso(issued_at),
        "projected_at": _iso(issued_at),
        "domain": domain,
    }

    event = {
        "review_event_id": review_event_id,
        "recommendation_id": recommendation_id,
        "user_id": user_id,
        "review_at": _iso(review_at),
        "review_question": review_question,
        "domain": domain,
    }

    outcome = {
        "review_event_id": review_event_id,
        "recommendation_id": recommendation_id,
        "user_id": user_id,
        "recorded_at": _iso(recorded_at),
        "followed_recommendation": int(bool(followed)),
        "self_reported_improvement": (
            None if improved is None else int(bool(improved))
        ),
        "free_text": free_text,
        "domain": domain,
        "completed": (None if completed is None else int(bool(completed))),
        "intensity_delta": intensity_delta,
        "duration_minutes": duration_minutes,
        "pre_energy_score": pre_energy_score,
        "post_energy_score": post_energy_score,
        "disagreed_firing_ids": (
            json.dumps(disagreed_firing_ids)
            if disagreed_firing_ids is not None
            else None
        ),
        "re_linked_from_recommendation_id": re_linked_from_recommendation_id,
        "re_link_note": re_link_note,
        "source": source,
        "ingest_actor": ingest_actor,
        "projected_at": _iso(recorded_at),
    }

    return {
        "recommendation": recommendation,
        "event": event,
        "outcome": outcome,
    }
