"""SQLite seeders for ledger tables that already exist.

Only seeders for tables backed by an already-landed migration live here.
Intent / target / data_quality seeders land alongside their migrations
(W49 → 019, W50 → 020, W51 → 021).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Mapping

from health_agent_infra.core.schemas import ReviewEvent, ReviewOutcome
from health_agent_infra.core.state import (
    project_review_event,
    project_review_outcome,
)


# Columns inserted into ``recommendation_log``. Matches the table after
# migrations 001 (initial), 003 (synthesis scaffolding — adds ``domain``),
# and 009 (FK widening) have run.
_RECOMMENDATION_LOG_COLS = (
    "recommendation_id",
    "user_id",
    "for_date",
    "issued_at",
    "action",
    "confidence",
    "bounded",
    "payload_json",
    "jsonl_offset",
    "source",
    "ingest_actor",
    "agent_version",
    "produced_at",
    "validated_at",
    "projected_at",
    "domain",
)


def _parse_dt(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _to_review_event(event: Mapping[str, Any]) -> ReviewEvent:
    return ReviewEvent(
        review_event_id=event["review_event_id"],
        recommendation_id=event["recommendation_id"],
        user_id=event["user_id"],
        review_at=_parse_dt(event["review_at"]),
        review_question=event["review_question"],
        domain=event.get("domain", "recovery"),
    )


def _to_review_outcome(outcome: Mapping[str, Any]) -> ReviewOutcome:
    disagreed = outcome.get("disagreed_firing_ids")
    if isinstance(disagreed, str):
        # ``make_outcome_chain`` JSON-encodes the list before storage; round-trip
        # back to a Python list so ``project_review_outcome`` can re-encode.
        import json as _json

        disagreed = _json.loads(disagreed)

    def _to_bool(v: Any) -> Any:
        if v is None:
            return None
        return bool(v)

    return ReviewOutcome(
        review_event_id=outcome["review_event_id"],
        recommendation_id=outcome["recommendation_id"],
        user_id=outcome["user_id"],
        recorded_at=_parse_dt(outcome["recorded_at"]),
        followed_recommendation=bool(outcome["followed_recommendation"]),
        self_reported_improvement=_to_bool(
            outcome.get("self_reported_improvement")
        ),
        free_text=outcome.get("free_text"),
        domain=outcome.get("domain", "recovery"),
        completed=_to_bool(outcome.get("completed")),
        intensity_delta=outcome.get("intensity_delta"),
        duration_minutes=outcome.get("duration_minutes"),
        pre_energy_score=outcome.get("pre_energy_score"),
        post_energy_score=outcome.get("post_energy_score"),
        disagreed_firing_ids=disagreed,
        re_linked_from_recommendation_id=outcome.get(
            "re_linked_from_recommendation_id"
        ),
        re_link_note=outcome.get("re_link_note"),
    )


def seed_outcome_chain(
    conn: sqlite3.Connection,
    *,
    recommendation: Mapping[str, Any],
    event: Mapping[str, Any],
    outcome: Mapping[str, Any] | None = None,
) -> None:
    """Insert one ``recommendation_log + review_event + review_outcome`` chain.

    Pair with :func:`make_outcome_chain` — call as
    ``seed_outcome_chain(conn, **make_outcome_chain(...))``.

    ``outcome`` is optional so callers can seed a recommendation + event
    without a recorded outcome (the W48 ``pending`` and ``overdue`` review
    cases need this shape).
    """

    rec_values = tuple(recommendation[col] for col in _RECOMMENDATION_LOG_COLS)
    placeholders = ", ".join("?" for _ in _RECOMMENDATION_LOG_COLS)
    columns = ", ".join(_RECOMMENDATION_LOG_COLS)
    conn.execute(
        f"INSERT INTO recommendation_log ({columns}) VALUES ({placeholders})",
        rec_values,
    )

    project_review_event(conn, _to_review_event(event))

    if outcome is not None:
        project_review_outcome(conn, _to_review_outcome(outcome))

    conn.commit()
