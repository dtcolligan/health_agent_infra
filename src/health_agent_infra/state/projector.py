"""Projection from typed dataclasses into SQLite state tables.

Phase 7A.2. Reads agent-authored artifacts (`TrainingRecommendation`,
`ReviewEvent`, `ReviewOutcome`) and inserts them into `recommendation_log`,
`review_event`, and `review_outcome`. Idempotent where the schema supports it
(recommendation_log + review_event have declared PKs; review_outcome is
append-only autoincrement and is deduplicated by reading the source JSONL
directly at reproject time).

Dual-write contract (per plan Pre-flight):
  - JSONL append is the audit boundary. Always happens first at the CLI.
  - Projector INSERT is best-effort; a failure here is recoverable via
    `hai state reproject` because the JSONL retains the durable record.
  - The projector never mutates JSONL.

Provenance (per state_model_v1.md §4):
  - recommendations: source='claude_agent_v1', ingest_actor='claude_agent_v1'
    by default (the agent both originates and transports the recommendation).
    Caller may override when a different agent identity is in use.
  - review events are runtime-generated and carry source='health_agent_infra',
    ingest_actor='health_agent_infra'.
  - review outcomes carry source='user_manual' + ingest_actor from the caller
    (typically 'claude_agent_v1' when the agent mediates).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from health_agent_infra.schemas import (
    PolicyDecision,
    ReviewEvent,
    ReviewOutcome,
    TrainingRecommendation,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bool_to_int(value: bool) -> int:
    return 1 if value else 0


def _opt_bool_to_int(value: Optional[bool]) -> Optional[int]:
    if value is None:
        return None
    return 1 if value else 0


# ---------------------------------------------------------------------------
# TrainingRecommendation -> recommendation_log
# ---------------------------------------------------------------------------

def project_recommendation(
    conn: sqlite3.Connection,
    recommendation: TrainingRecommendation,
    *,
    source: str = "claude_agent_v1",
    ingest_actor: str = "claude_agent_v1",
    agent_version: Optional[str] = None,
    produced_at: Optional[datetime] = None,
    jsonl_offset: Optional[int] = None,
) -> bool:
    """Insert a recommendation into recommendation_log.

    Idempotent on ``recommendation_id``: re-running does nothing and returns
    ``False``. First-time insert returns ``True``.

    ``produced_at`` defaults to the recommendation's ``issued_at`` (best
    available proxy until agents report a distinct "produced" timestamp).
    ``validated_at`` and ``projected_at`` are both stamped as now.
    """

    existing = conn.execute(
        "SELECT 1 FROM recommendation_log WHERE recommendation_id = ?",
        (recommendation.recommendation_id,),
    ).fetchone()
    if existing is not None:
        return False

    produced_iso = (
        produced_at.isoformat() if produced_at is not None
        else recommendation.issued_at.isoformat()
    )

    conn.execute(
        """
        INSERT INTO recommendation_log (
            recommendation_id, user_id, for_date, issued_at,
            action, confidence, bounded, payload_json,
            jsonl_offset, source, ingest_actor, agent_version,
            produced_at, validated_at, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            recommendation.recommendation_id,
            recommendation.user_id,
            recommendation.for_date.isoformat(),
            recommendation.issued_at.isoformat(),
            recommendation.action,
            recommendation.confidence,
            _bool_to_int(recommendation.bounded),
            json.dumps(recommendation.to_dict(), sort_keys=True),
            jsonl_offset,
            source,
            ingest_actor,
            agent_version,
            produced_iso,
            _now_iso(),
            _now_iso(),
        ),
    )
    conn.commit()
    return True


# ---------------------------------------------------------------------------
# ReviewEvent -> review_event
# ---------------------------------------------------------------------------

def project_review_event(
    conn: sqlite3.Connection,
    event: ReviewEvent,
    *,
    source: str = "health_agent_infra",
    ingest_actor: str = "health_agent_infra",
) -> bool:
    """Insert a review event into review_event.

    Idempotent on ``review_event_id``. Returns ``True`` on first insert,
    ``False`` if already present.

    Note: review_event's schema has FKs requiring the referenced
    recommendation_id to exist. Caller must have projected the recommendation
    first, or the INSERT will fail with IntegrityError.
    """

    existing = conn.execute(
        "SELECT 1 FROM review_event WHERE review_event_id = ?",
        (event.review_event_id,),
    ).fetchone()
    if existing is not None:
        return False

    conn.execute(
        """
        INSERT INTO review_event (
            review_event_id, recommendation_id, user_id,
            review_at, review_question, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            event.review_event_id,
            event.recommendation_id,
            event.user_id,
            event.review_at.isoformat(),
            event.review_question,
            _now_iso(),
        ),
    )
    conn.commit()
    # Source/ingest_actor live in state_model_v1.md §4 but the review_event
    # table in migration 001 doesn't carry them as columns (events are
    # runtime-generated, not user- or agent-authored facts in the same sense).
    # Retained as function args so callers don't need to change when/if we
    # add those columns later.
    del source
    del ingest_actor
    return True


# ---------------------------------------------------------------------------
# ReviewOutcome -> review_outcome
# ---------------------------------------------------------------------------

def project_review_outcome(
    conn: sqlite3.Connection,
    outcome: ReviewOutcome,
    *,
    source: str = "user_manual",
    ingest_actor: str = "claude_agent_v1",
    jsonl_offset: Optional[int] = None,
) -> int:
    """Insert a review outcome. Returns the autoincremented outcome_id.

    review_outcome is append-only with an autoincrement PK — duplicate
    detection during reproject relies on (review_event_id, recorded_at)
    pair presence rather than a PK check. Normal dual-write from the CLI
    appends unconditionally; rely on the source JSONL being canonical.
    """

    cursor = conn.execute(
        """
        INSERT INTO review_outcome (
            review_event_id, recommendation_id, user_id, recorded_at,
            followed_recommendation, self_reported_improvement, free_text,
            jsonl_offset, source, ingest_actor, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            outcome.review_event_id,
            outcome.recommendation_id,
            outcome.user_id,
            outcome.recorded_at.isoformat(),
            _bool_to_int(outcome.followed_recommendation),
            _opt_bool_to_int(outcome.self_reported_improvement),
            outcome.free_text,
            jsonl_offset,
            source,
            ingest_actor,
            _now_iso(),
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


# ---------------------------------------------------------------------------
# Reprojection from JSONL audit logs
# ---------------------------------------------------------------------------

class ReprojectBaseDirError(Exception):
    """Raised when reproject is asked to rebuild from a base-dir that does
    not contain any of the expected audit JSONL files.

    Guards against the failure mode where a typo in ``--base-dir`` silently
    wipes the projection tables. Callers who genuinely want to reset the DB
    can opt into this via ``allow_empty=True``.
    """


def reproject_from_jsonl(conn: sqlite3.Connection, base_dir, *, allow_empty: bool = False) -> dict:
    """Rebuild recommendation_log / review_event / review_outcome from the
    JSONL audit logs under ``base_dir``.

    Truncates the three projected tables inside a single transaction, then
    walks the three JSONL files in PK-dependency order (recommendations →
    events → outcomes) and reprojects each line. Idempotent: running twice
    produces the same DB state.

    ``base_dir`` is the writeback root (same directory `hai writeback`
    appends to).

    **Safety.** If none of the three expected JSONL files exist in
    ``base_dir``, the function raises ``ReprojectBaseDirError`` before
    touching the DB, so a typo in the path can't silently wipe the
    projection tables. Pass ``allow_empty=True`` to override — reserved for
    the rare case where an operator explicitly wants to reset the DB tables.
    """

    from pathlib import Path

    base = Path(base_dir)
    rec_log = base / "recommendation_log.jsonl"
    events_log = base / "review_events.jsonl"
    outcomes_log = base / "review_outcomes.jsonl"

    if not allow_empty:
        expected = (rec_log, events_log, outcomes_log)
        if not any(p.exists() for p in expected):
            raise ReprojectBaseDirError(
                f"no audit JSONL files found under {base}. Expected at least "
                f"one of: recommendation_log.jsonl, review_events.jsonl, "
                f"review_outcomes.jsonl. Refusing to truncate the projection "
                f"tables. Pass allow_empty=True / --allow-empty-reproject to "
                f"override."
            )

    counts = {"recommendations": 0, "review_events": 0, "review_outcomes": 0}

    conn.execute("BEGIN EXCLUSIVE")
    try:
        # Order matters: outcomes FK -> events FK -> recommendations. Delete
        # in reverse dependency order.
        conn.execute("DELETE FROM review_outcome")
        conn.execute("DELETE FROM review_event")
        conn.execute("DELETE FROM recommendation_log")

        if rec_log.exists():
            for line_no, line in enumerate(rec_log.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                data = json.loads(line)
                conn.execute(
                    """
                    INSERT INTO recommendation_log (
                        recommendation_id, user_id, for_date, issued_at,
                        action, confidence, bounded, payload_json,
                        jsonl_offset, source, ingest_actor, agent_version,
                        produced_at, validated_at, projected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["recommendation_id"],
                        data["user_id"],
                        data["for_date"],
                        data["issued_at"],
                        data["action"],
                        data["confidence"],
                        1 if data.get("bounded", True) else 0,
                        json.dumps(data, sort_keys=True),
                        line_no,
                        data.get("source", "claude_agent_v1"),
                        data.get("ingest_actor", "claude_agent_v1"),
                        data.get("agent_version"),
                        data.get("produced_at", data["issued_at"]),
                        data.get("validated_at", _now_iso()),
                        _now_iso(),
                    ),
                )
                counts["recommendations"] += 1

        if events_log.exists():
            for line_no, line in enumerate(events_log.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                data = json.loads(line)
                conn.execute(
                    """
                    INSERT INTO review_event (
                        review_event_id, recommendation_id, user_id,
                        review_at, review_question, projected_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["review_event_id"],
                        data["recommendation_id"],
                        data["user_id"],
                        data["review_at"],
                        data["review_question"],
                        _now_iso(),
                    ),
                )
                counts["review_events"] += 1

        if outcomes_log.exists():
            for line_no, line in enumerate(outcomes_log.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                data = json.loads(line)
                conn.execute(
                    """
                    INSERT INTO review_outcome (
                        review_event_id, recommendation_id, user_id, recorded_at,
                        followed_recommendation, self_reported_improvement, free_text,
                        jsonl_offset, source, ingest_actor, projected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["review_event_id"],
                        data["recommendation_id"],
                        data["user_id"],
                        data["recorded_at"],
                        1 if data["followed_recommendation"] else 0,
                        _opt_bool_to_int(data.get("self_reported_improvement")),
                        data.get("free_text"),
                        line_no,
                        data.get("source", "user_manual"),
                        data.get("ingest_actor", "claude_agent_v1"),
                        _now_iso(),
                    ),
                )
                counts["review_outcomes"] += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return counts
