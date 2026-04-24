"""M7 — migration + reproject round-trip.

Two invariants:

  1. ``initialize_database`` applied from scratch on two independent
     fresh DB files produces byte-equal schema + identical
     ``schema_migrations`` rows (modulo the auto-stamped
     ``applied_at`` timestamp). Pins "migrations are deterministic."

  2. Given a JSONL audit trail produced on DB1 via the CLI-level
     writeback + review flow, reprojecting that trail onto a second
     fresh DB reproduces identical ``recommendation_log`` /
     ``review_event`` / ``review_outcome`` rows (modulo the
     ``projected_at`` timestamp). This is what makes the JSONL the
     durable boundary it's documented to be.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.review.outcomes import (
    record_review_outcome,
    schedule_review,
)
from health_agent_infra.core.schemas import (
    FollowUp,
    PolicyDecision,
    RECOMMENDATION_SCHEMA_VERSION,
    ReviewEvent,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_recommendation,
    project_review_event,
    project_review_outcome,
    reproject_from_jsonl,
)
from health_agent_infra.domains.recovery.schemas import TrainingRecommendation


# D2: hai writeback was retired in v0.1.4. Tests that seeded the JSONL
# via perform_writeback now write the line directly — the reproject
# path still consumes a real recommendation_log.jsonl.
_WRITEBACK_ROOT_NAME = "writeback"


def _append_recommendation_jsonl(
    base_dir: Path, rec: TrainingRecommendation,
) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    log_path = base_dir / "recommendation_log.jsonl"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec.to_dict(), sort_keys=True) + "\n")


USER = "u_rt"
FOR_DATE = date(2026, 4, 17)
ISSUED_AT = datetime(2026, 4, 17, 6, 30, tzinfo=timezone.utc)
REVIEW_AT = datetime(2026, 4, 18, 7, 0, tzinfo=timezone.utc)
RECORDED_AT = datetime(2026, 4, 18, 19, 0, tzinfo=timezone.utc)


# Columns the write path stamps with wall-clock time. They legitimately
# diverge between DB1 and DB2 and must be excluded from equality checks.
_VOLATILE_COLUMNS: frozenset[str] = frozenset({
    "projected_at",
    "applied_at",
    "validated_at",
    "outcome_id",  # autoincrement, per-DB
    "jsonl_offset",  # reproject assigns sequential line numbers; different runs may differ
})


def _build_recommendation() -> TrainingRecommendation:
    return TrainingRecommendation(
        schema_version=RECOMMENDATION_SCHEMA_VERSION,
        recommendation_id=f"rec_{FOR_DATE.isoformat()}_{USER}_recovery",
        user_id=USER,
        issued_at=ISSUED_AT,
        for_date=FOR_DATE,
        action="proceed_with_planned_session",
        action_detail=None,
        rationale=["sleep=normal", "hrv=baseline"],
        confidence="high",
        uncertainty=[],
        follow_up=FollowUp(
            review_at=REVIEW_AT,
            review_question="Did today feel appropriate?",
            review_event_id=f"rev_{FOR_DATE.isoformat()}_{USER}_recovery",
        ),
        policy_decisions=[
            PolicyDecision(rule_id="r1", decision="allow", note="ok"),
        ],
        bounded=True,
    )


def _seed_db_from_jsonl_sources(
    db_path: Path,
    recommendation: TrainingRecommendation,
    base_dir: Path,
) -> None:
    """Seed DB1 the way the CLI does: append to recommendation_log.jsonl
    and project into DB; schedule + record review → JSONL + project."""

    initialize_database(db_path)
    _append_recommendation_jsonl(base_dir, recommendation)

    conn = open_connection(db_path)
    try:
        project_recommendation(conn, recommendation)
    finally:
        conn.close()

    event = schedule_review(recommendation, base_dir=base_dir, domain="recovery")
    outcome = record_review_outcome(
        event,
        base_dir=base_dir,
        followed_recommendation=True,
        self_reported_improvement=True,
        free_text="felt good",
        now=RECORDED_AT,
    )

    conn = open_connection(db_path)
    try:
        project_review_event(conn, event)
        project_review_outcome(conn, outcome)
    finally:
        conn.close()


def _strip(row: sqlite3.Row) -> dict:
    out = {k: row[k] for k in row.keys() if k not in _VOLATILE_COLUMNS}
    # payload_json carries no wall-clock fields that diverge here; keep it.
    return out


def _snapshot_audit_tables(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    snap: dict[str, list[dict]] = {}
    for table in ("recommendation_log", "review_event", "review_outcome"):
        rows = conn.execute(
            f"SELECT * FROM {table} ORDER BY 1"  # noqa: S608 — fixed list
        ).fetchall()
        snap[table] = [_strip(r) for r in rows]
    return snap


# ---------------------------------------------------------------------------
# Migration determinism
# ---------------------------------------------------------------------------


def test_two_fresh_dbs_have_identical_schema_and_migration_bookkeeping(tmp_path):
    db_a = tmp_path / "a.db"
    db_b = tmp_path / "b.db"
    initialize_database(db_a)
    initialize_database(db_b)

    def _schema(conn: sqlite3.Connection) -> list[tuple[str, str]]:
        rows = conn.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' "
            "ORDER BY type, name"
        ).fetchall()
        return [(r["type"], r["name"], r["sql"] or "") for r in rows]

    def _migrations(conn: sqlite3.Connection) -> list[tuple]:
        rows = conn.execute(
            "SELECT version, filename FROM schema_migrations ORDER BY version"
        ).fetchall()
        return [tuple(r) for r in rows]

    conn_a = open_connection(db_a)
    conn_b = open_connection(db_b)
    try:
        assert _schema(conn_a) == _schema(conn_b)
        assert _migrations(conn_a) == _migrations(conn_b)
    finally:
        conn_a.close()
        conn_b.close()


# ---------------------------------------------------------------------------
# JSONL → reproject round trip
# ---------------------------------------------------------------------------


def test_jsonl_reproject_onto_fresh_db_matches_original(tmp_path):
    base_dir = tmp_path / _WRITEBACK_ROOT_NAME
    db_one = tmp_path / "one.db"
    db_two = tmp_path / "two.db"

    recommendation = _build_recommendation()
    _seed_db_from_jsonl_sources(db_one, recommendation, base_dir)

    initialize_database(db_two)
    conn_two = open_connection(db_two)
    try:
        # Reproject from DB1's JSONL trail.
        reproject_from_jsonl(conn_two, base_dir)
    finally:
        conn_two.close()

    conn_one = open_connection(db_one)
    conn_two = open_connection(db_two)
    try:
        snap_one = _snapshot_audit_tables(conn_one)
        snap_two = _snapshot_audit_tables(conn_two)
    finally:
        conn_one.close()
        conn_two.close()

    assert snap_one == snap_two, (
        "reproject-from-JSONL did not reconstruct the same audit rows"
    )
