"""M4 — review_outcome enrichment fields.

Contracts pinned:

  1. Legacy callers (no enriched kwargs) land rows with NULL on every
     new column; existing behavior is unchanged.
  2. ``record_review_outcome`` round-trips each enriched kwarg through
     the dataclass into the JSONL and DB projection.
  3. ``disagreed_firing_ids`` serializes as a JSON-encoded list in the
     DB column; NULL and empty-list are distinguishable
     ("not asked" vs "asked, no disagreement").
  4. ``summarize_review_history`` emits no ``enriched`` key when every
     outcome is legacy-shaped, and emits populated aggregates only when
     outcomes contribute to each respective count.
  5. The CLI's ``hai review record`` flags take precedence over the
     same keys in ``--outcome-json`` when both are present.
  6. Migration 010 adds the six columns as nullable.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.review.outcomes import (
    INTENSITY_DELTA_ORDINAL,
    record_review_outcome,
    summarize_review_history,
)
from health_agent_infra.core.schemas import (
    ReviewEvent,
    ReviewOutcome,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_review_event,
    project_review_outcome,
)


AS_OF = date(2026, 4, 17)
REVIEW_AT = datetime(2026, 4, 18, 7, 0, tzinfo=timezone.utc)
RECORDED_AT = datetime(2026, 4, 18, 19, 0, tzinfo=timezone.utc)


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _event(event_id: str = "rev_1", rec_id: str = "rec_1") -> ReviewEvent:
    return ReviewEvent(
        review_event_id=event_id,
        recommendation_id=rec_id,
        user_id="u_test",
        review_at=REVIEW_AT,
        review_question="Did the session feel appropriate?",
        domain="running",
    )


def _seed_event_and_fake_rec(conn: sqlite3.Connection, event: ReviewEvent) -> None:
    """Seed the recommendation_log + review_event rows the outcome FKs need.

    ReviewOutcome references both via FK, so the DB projection tests
    need a row in each upstream table.
    """

    conn.execute(
        """
        INSERT INTO recommendation_log (
            recommendation_id, user_id, for_date, issued_at,
            action, confidence, bounded, payload_json,
            jsonl_offset, source, ingest_actor, agent_version,
            produced_at, validated_at, projected_at, domain
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.recommendation_id, event.user_id, AS_OF.isoformat(),
            REVIEW_AT.isoformat(), "proceed_with_planned_run", "high", 1,
            "{}", None, "claude_agent_v1", "claude_agent_v1", None,
            REVIEW_AT.isoformat(), REVIEW_AT.isoformat(),
            REVIEW_AT.isoformat(), "running",
        ),
    )
    project_review_event(conn, event)


# ---------------------------------------------------------------------------
# Migration shape
# ---------------------------------------------------------------------------


def test_migration_010_adds_six_nullable_columns(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        rows = conn.execute("PRAGMA table_info(review_outcome)").fetchall()
        cols = {r["name"]: dict(r) for r in rows}
    finally:
        conn.close()

    for name in (
        "completed",
        "intensity_delta",
        "duration_minutes",
        "pre_energy_score",
        "post_energy_score",
        "disagreed_firing_ids",
    ):
        assert name in cols, f"migration 010 did not add {name}"
        assert cols[name]["notnull"] == 0, f"{name} must be nullable"


# ---------------------------------------------------------------------------
# Legacy-shape round trip — NULLs on every new column
# ---------------------------------------------------------------------------


def test_legacy_callers_land_nulls_on_enriched_columns(tmp_path: Path):
    db = _init_db(tmp_path)
    event = _event()
    conn = open_connection(db)
    try:
        _seed_event_and_fake_rec(conn, event)
    finally:
        conn.close()

    outcome = record_review_outcome(
        event,
        base_dir=tmp_path,
        followed_recommendation=True,
        self_reported_improvement=True,
        now=RECORDED_AT,
    )
    conn = open_connection(db)
    try:
        project_review_outcome(conn, outcome)
        row = conn.execute(
            "SELECT completed, intensity_delta, duration_minutes, "
            "pre_energy_score, post_energy_score, disagreed_firing_ids "
            "FROM review_outcome WHERE review_event_id = ?",
            (event.review_event_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row["completed"] is None
    assert row["intensity_delta"] is None
    assert row["duration_minutes"] is None
    assert row["pre_energy_score"] is None
    assert row["post_energy_score"] is None
    assert row["disagreed_firing_ids"] is None


# ---------------------------------------------------------------------------
# Full enriched round trip
# ---------------------------------------------------------------------------


def test_enriched_round_trip_through_jsonl_and_db(tmp_path: Path):
    db = _init_db(tmp_path)
    event = _event()
    conn = open_connection(db)
    try:
        _seed_event_and_fake_rec(conn, event)
    finally:
        conn.close()

    outcome = record_review_outcome(
        event,
        base_dir=tmp_path,
        followed_recommendation=True,
        self_reported_improvement=True,
        free_text="felt great",
        now=RECORDED_AT,
        completed=True,
        intensity_delta="harder",
        duration_minutes=52,
        pre_energy_score=3,
        post_energy_score=4,
        disagreed_firing_ids=["12", "18"],
    )

    jsonl_line = (tmp_path / "review_outcomes.jsonl").read_text().strip()
    payload = json.loads(jsonl_line)
    assert payload["completed"] is True
    assert payload["intensity_delta"] == "harder"
    assert payload["duration_minutes"] == 52
    assert payload["pre_energy_score"] == 3
    assert payload["post_energy_score"] == 4
    assert payload["disagreed_firing_ids"] == ["12", "18"]

    conn = open_connection(db)
    try:
        project_review_outcome(conn, outcome)
        row = conn.execute(
            "SELECT completed, intensity_delta, duration_minutes, "
            "pre_energy_score, post_energy_score, disagreed_firing_ids "
            "FROM review_outcome WHERE review_event_id = ?",
            (event.review_event_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row["completed"] == 1
    assert row["intensity_delta"] == "harder"
    assert row["duration_minutes"] == 52
    assert row["pre_energy_score"] == 3
    assert row["post_energy_score"] == 4
    # disagreed_firing_ids is JSON-encoded in TEXT so a future reader
    # can parse back to the list shape.
    assert json.loads(row["disagreed_firing_ids"]) == ["12", "18"]


def test_empty_disagreed_list_distinguishes_from_null(tmp_path: Path):
    """`disagreed_firing_ids = []` means 'asked, no disagreement'. NULL
    means 'question was not asked'. Both must land distinctly."""

    db = _init_db(tmp_path)
    event_a = _event(event_id="rev_a", rec_id="rec_a")
    event_b = _event(event_id="rev_b", rec_id="rec_b")
    conn = open_connection(db)
    try:
        _seed_event_and_fake_rec(conn, event_a)
        _seed_event_and_fake_rec(conn, event_b)
    finally:
        conn.close()

    a = record_review_outcome(
        event_a, base_dir=tmp_path,
        followed_recommendation=True, self_reported_improvement=True,
        now=RECORDED_AT, disagreed_firing_ids=[],
    )
    b = record_review_outcome(
        event_b, base_dir=tmp_path,
        followed_recommendation=True, self_reported_improvement=True,
        now=RECORDED_AT,
    )

    conn = open_connection(db)
    try:
        project_review_outcome(conn, a)
        project_review_outcome(conn, b)
        row_a = conn.execute(
            "SELECT disagreed_firing_ids FROM review_outcome "
            "WHERE review_event_id = ?", (event_a.review_event_id,),
        ).fetchone()
        row_b = conn.execute(
            "SELECT disagreed_firing_ids FROM review_outcome "
            "WHERE review_event_id = ?", (event_b.review_event_id,),
        ).fetchone()
    finally:
        conn.close()

    assert row_a["disagreed_firing_ids"] == "[]"
    assert row_b["disagreed_firing_ids"] is None


# ---------------------------------------------------------------------------
# summarize_review_history — enriched aggregates
# ---------------------------------------------------------------------------


def _outcome(**overrides) -> ReviewOutcome:
    base = dict(
        review_event_id="rev_1",
        recommendation_id="rec_1",
        user_id="u_test",
        recorded_at=RECORDED_AT,
        followed_recommendation=True,
        self_reported_improvement=True,
        free_text=None,
        domain="running",
    )
    base.update(overrides)
    return ReviewOutcome(**base)


def test_summary_omits_enriched_on_legacy_only_outcomes():
    outcomes = [
        _outcome(),
        _outcome(followed_recommendation=False, self_reported_improvement=None),
    ]
    summary = summarize_review_history(outcomes)
    assert "enriched" not in summary
    assert summary["total"] == 2


def test_summary_populates_enriched_when_any_outcome_carries_enrichment():
    outcomes = [
        _outcome(completed=True, intensity_delta="harder",
                 pre_energy_score=3, post_energy_score=4),
        _outcome(completed=False, intensity_delta="same",
                 pre_energy_score=4, post_energy_score=3),
        _outcome(completed=True),  # only completion, no intensity/energy
        _outcome(),  # legacy-only
    ]
    summary = summarize_review_history(outcomes)

    assert summary["total"] == 4
    enriched = summary["enriched"]

    assert enriched["completion_count"] == 3
    # 2 completed out of 3 → 2/3
    assert enriched["completion_rate"] == pytest.approx(2 / 3)

    assert enriched["intensity_delta_count"] == 2
    # harder + same → 1 + 0 → mean 0.5
    assert enriched["mean_intensity_delta"] == pytest.approx(
        (INTENSITY_DELTA_ORDINAL["harder"] + INTENSITY_DELTA_ORDINAL["same"]) / 2
    )

    assert enriched["energy_delta_count"] == 2
    # (4-3) + (3-4) / 2 = 0
    assert enriched["mean_energy_delta"] == pytest.approx(0.0)


def test_summary_emits_enriched_with_none_values_when_only_duration_is_set():
    """A single outcome recording only duration_minutes still activates
    the enriched block — but every per-field count is zero and the
    mean is None. This keeps 'I recorded something' and 'I recorded
    nothing' distinguishable without forcing the consumer to probe
    every optional field."""

    summary = summarize_review_history([_outcome(duration_minutes=45)])
    assert "enriched" in summary
    assert summary["enriched"]["completion_rate"] is None
    assert summary["enriched"]["mean_intensity_delta"] is None
    assert summary["enriched"]["mean_energy_delta"] is None


def test_summary_skips_unrecognised_intensity_delta_strings():
    """Unknown labels contribute to neither the mean nor the count —
    they are tracked as data we don't know how to ordinalise."""

    outcomes = [
        _outcome(intensity_delta="harder"),
        _outcome(intensity_delta="wibble"),
    ]
    summary = summarize_review_history(outcomes)
    assert summary["enriched"]["intensity_delta_count"] == 1
    assert summary["enriched"]["mean_intensity_delta"] == pytest.approx(
        INTENSITY_DELTA_ORDINAL["harder"]
    )


# ---------------------------------------------------------------------------
# CLI — flags override --outcome-json keys
# ---------------------------------------------------------------------------


def test_cli_review_record_flags_override_json(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    base_dir = tmp_path / "review_base"
    base_dir.mkdir()

    event = _event()
    conn = open_connection(db)
    try:
        _seed_event_and_fake_rec(conn, event)
    finally:
        conn.close()

    outcome_json = base_dir / "outcome.json"
    outcome_json.write_text(json.dumps({
        "review_event_id": event.review_event_id,
        "recommendation_id": event.recommendation_id,
        "user_id": event.user_id,
        "review_at": event.review_at.isoformat(),
        "review_question": event.review_question,
        "domain": event.domain,
        "followed_recommendation": True,
        "self_reported_improvement": True,
        "recorded_at": RECORDED_AT.isoformat(),
        # JSON supplies intensity_delta=same; CLI flag below should win.
        "intensity_delta": "same",
        "duration_minutes": 30,
    }))

    rc = cli_main([
        "review", "record",
        "--outcome-json", str(outcome_json),
        "--base-dir", str(base_dir),
        "--db-path", str(db),
        "--intensity-delta", "harder",
        "--completed", "yes",
        "--pre-energy", "2",
        "--post-energy", "4",
        "--disagreed-firings", "101,102",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["intensity_delta"] == "harder"    # flag overrode JSON
    assert payload["duration_minutes"] == 30         # JSON pass-through
    assert payload["completed"] is True
    assert payload["pre_energy_score"] == 2
    assert payload["post_energy_score"] == 4
    assert payload["disagreed_firing_ids"] == ["101", "102"]


def test_cli_review_record_disagreed_firings_empty_string_records_empty_list(
    tmp_path: Path, capsys,
):
    db = _init_db(tmp_path)
    base_dir = tmp_path / "review_base"
    base_dir.mkdir()

    event = _event()
    conn = open_connection(db)
    try:
        _seed_event_and_fake_rec(conn, event)
    finally:
        conn.close()

    outcome_json = base_dir / "outcome.json"
    outcome_json.write_text(json.dumps({
        "review_event_id": event.review_event_id,
        "recommendation_id": event.recommendation_id,
        "user_id": event.user_id,
        "review_at": event.review_at.isoformat(),
        "review_question": event.review_question,
        "domain": event.domain,
        "followed_recommendation": True,
        "self_reported_improvement": True,
        "recorded_at": RECORDED_AT.isoformat(),
    }))

    rc = cli_main([
        "review", "record",
        "--outcome-json", str(outcome_json),
        "--base-dir", str(base_dir),
        "--db-path", str(db),
        "--disagreed-firings", "",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["disagreed_firing_ids"] == []
