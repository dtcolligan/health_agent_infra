"""Smoke tests for the v0.1.8 fixture factory.

Per ``hai/reporting/plans/v0_1_8/PLAN.md`` § 0 the fixture-factory landed
ahead of the W49 / W50 / W51 migrations so the ~80–120 v0.1.8 tests
have a stable seeding API. These smoke tests pin two contracts:

  1. Each builder returns a complete dict with the column shape PLAN.md
     § 2 specifies; kwarg overrides flow through unchanged.
  2. ``seed_outcome_chain`` round-trips through SQLite against the
     already-landed ``recommendation_log`` / ``review_event`` /
     ``review_outcome`` tables.

If a future migration changes one of the schemas, the relevant builder
needs the same change here AND a corresponding seeder addition before
W48–W51 tests can rely on the helper.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.state import initialize_database, open_connection

from _fixtures import (
    make_data_quality_row,
    make_intent_row,
    make_outcome_chain,
    make_target_row,
    seed_outcome_chain,
)


# ---------------------------------------------------------------------------
# make_intent_row — W49 / migration 019
# ---------------------------------------------------------------------------


_INTENT_KEYS = {
    "intent_id",
    "user_id",
    "domain",
    "scope_type",
    "scope_start",
    "scope_end",
    "intent_type",
    "status",
    "priority",
    "flexibility",
    "payload_json",
    "reason",
    "source",
    "ingest_actor",
    "created_at",
    "effective_at",
    "review_after",
    "supersedes_intent_id",
    "superseded_by_intent_id",
}


def test_make_intent_row_default_shape_matches_plan_w49():
    row = make_intent_row()

    assert set(row) == _INTENT_KEYS
    assert row["status"] == "active"
    assert row["scope_start"] == row["scope_end"]  # day-scoped default
    assert json.loads(row["payload_json"]) == {}


def test_make_intent_row_overrides_flow_through():
    row = make_intent_row(
        intent_id="intent_42",
        domain="strength",
        intent_type="rest_day",
        status="archived",
        payload={"note": "deload"},
        supersedes_intent_id="intent_41",
    )

    assert row["intent_id"] == "intent_42"
    assert row["domain"] == "strength"
    assert row["intent_type"] == "rest_day"
    assert row["status"] == "archived"
    assert json.loads(row["payload_json"]) == {"note": "deload"}
    assert row["supersedes_intent_id"] == "intent_41"


# ---------------------------------------------------------------------------
# make_target_row — W50 / migration 020
# ---------------------------------------------------------------------------


_TARGET_KEYS = {
    "target_id",
    "user_id",
    "domain",
    "target_type",
    "status",
    "value_json",
    "unit",
    "lower_bound",
    "upper_bound",
    "effective_from",
    "effective_to",
    "review_after",
    "reason",
    "source",
    "ingest_actor",
    "created_at",
    "supersedes_target_id",
    "superseded_by_target_id",
}


def test_make_target_row_default_shape_matches_plan_w50():
    row = make_target_row()

    assert set(row) == _TARGET_KEYS
    assert row["status"] == "active"
    assert row["target_type"] == "hydration_ml"
    assert json.loads(row["value_json"]) == {"value": 3000}


def test_make_target_row_overrides_flow_through():
    row = make_target_row(
        target_id="target_7",
        target_type="protein_g",
        value=160,
        unit="g",
        lower_bound=140.0,
        upper_bound=180.0,
        effective_from=date(2026, 5, 1),
    )

    assert row["target_id"] == "target_7"
    assert row["target_type"] == "protein_g"
    assert json.loads(row["value_json"]) == {"value": 160}
    assert row["lower_bound"] == 140.0
    assert row["upper_bound"] == 180.0
    assert row["effective_from"] == "2026-05-01"


# ---------------------------------------------------------------------------
# make_data_quality_row — W51 / migration 021
# ---------------------------------------------------------------------------


_DQ_KEYS = {
    "user_id",
    "as_of_date",
    "domain",
    "source",
    "freshness_hours",
    "coverage_band",
    "missingness",
    "source_unavailable",
    "user_input_pending",
    "suspicious_discontinuity",
    "cold_start_window_state",
    "computed_at",
}


def test_make_data_quality_row_default_shape_matches_plan_w51():
    row = make_data_quality_row()

    assert set(row) == _DQ_KEYS
    assert row["coverage_band"] == "full"
    assert row["cold_start_window_state"] == "post_cold_start"
    assert row["source_unavailable"] == 0


def test_make_data_quality_row_overrides_flow_through():
    row = make_data_quality_row(
        domain="sleep",
        coverage_band="sparse",
        missingness="pending_user_input",
        user_input_pending=1,
        cold_start_window_state="in_window",
    )

    assert row["domain"] == "sleep"
    assert row["coverage_band"] == "sparse"
    assert row["missingness"] == "pending_user_input"
    assert row["user_input_pending"] == 1
    assert row["cold_start_window_state"] == "in_window"


# ---------------------------------------------------------------------------
# make_outcome_chain + seed_outcome_chain — W48 / existing tables
# ---------------------------------------------------------------------------


def test_make_outcome_chain_returns_consistent_triplet():
    chain = make_outcome_chain(
        recommendation_id="rec_99",
        review_event_id="rev_99",
        domain="running",
    )

    assert set(chain) == {"recommendation", "event", "outcome"}
    assert chain["recommendation"]["recommendation_id"] == "rec_99"
    assert chain["event"]["recommendation_id"] == "rec_99"
    assert chain["event"]["review_event_id"] == "rev_99"
    assert chain["outcome"]["review_event_id"] == "rev_99"
    assert chain["outcome"]["recommendation_id"] == "rec_99"
    # all three carry the same domain so the FK chain is internally
    # consistent for the W48 per-domain summary tests.
    assert (
        chain["recommendation"]["domain"]
        == chain["event"]["domain"]
        == chain["outcome"]["domain"]
        == "running"
    )


def test_make_outcome_chain_followed_and_improved_overrides():
    chain = make_outcome_chain(followed=False, improved=None)

    assert chain["outcome"]["followed_recommendation"] == 0
    assert chain["outcome"]["self_reported_improvement"] is None


def test_make_outcome_chain_enrichment_round_trips():
    chain = make_outcome_chain(
        completed=True,
        intensity_delta="harder",
        duration_minutes=52,
        pre_energy_score=3,
        post_energy_score=4,
        disagreed_firing_ids=["12", "18"],
    )

    outcome = chain["outcome"]
    assert outcome["completed"] == 1
    assert outcome["intensity_delta"] == "harder"
    assert outcome["duration_minutes"] == 52
    assert outcome["pre_energy_score"] == 3
    assert outcome["post_energy_score"] == 4
    assert json.loads(outcome["disagreed_firing_ids"]) == ["12", "18"]


def test_seed_outcome_chain_round_trips_through_sqlite(tmp_path: Path):
    db = tmp_path / "state.db"
    initialize_database(db)

    chain = make_outcome_chain(
        recommendation_id="rec_smoke",
        review_event_id="rev_smoke",
        domain="running",
        followed=True,
        improved=False,
        intensity_delta="lighter",
    )

    conn = open_connection(db)
    try:
        seed_outcome_chain(conn, **chain)

        rec_row = conn.execute(
            "SELECT recommendation_id, action, domain "
            "FROM recommendation_log WHERE recommendation_id = ?",
            ("rec_smoke",),
        ).fetchone()
        event_row = conn.execute(
            "SELECT review_event_id, recommendation_id, domain "
            "FROM review_event WHERE review_event_id = ?",
            ("rev_smoke",),
        ).fetchone()
        outcome_row = conn.execute(
            "SELECT review_event_id, recommendation_id, "
            "followed_recommendation, self_reported_improvement, "
            "intensity_delta, domain "
            "FROM review_outcome WHERE review_event_id = ?",
            ("rev_smoke",),
        ).fetchone()
    finally:
        conn.close()

    assert rec_row["recommendation_id"] == "rec_smoke"
    assert rec_row["action"] == "proceed_with_planned_run"
    assert rec_row["domain"] == "running"

    assert event_row["recommendation_id"] == "rec_smoke"
    assert event_row["domain"] == "running"

    assert outcome_row["recommendation_id"] == "rec_smoke"
    assert outcome_row["followed_recommendation"] == 1
    assert outcome_row["self_reported_improvement"] == 0
    assert outcome_row["intensity_delta"] == "lighter"
    assert outcome_row["domain"] == "running"


def test_seed_outcome_chain_supports_pending_review_without_outcome(
    tmp_path: Path,
):
    """W48's ``pending`` / ``overdue`` review cases seed rec + event but
    no outcome — the seeder must accept that shape."""

    db = tmp_path / "state.db"
    initialize_database(db)

    chain = make_outcome_chain(
        recommendation_id="rec_pending",
        review_event_id="rev_pending",
        domain="recovery",
    )

    conn = open_connection(db)
    try:
        seed_outcome_chain(
            conn,
            recommendation=chain["recommendation"],
            event=chain["event"],
            outcome=None,
        )

        outcomes = conn.execute(
            "SELECT outcome_id FROM review_outcome "
            "WHERE review_event_id = ?",
            ("rev_pending",),
        ).fetchall()
        rec_count = conn.execute(
            "SELECT COUNT(*) AS c FROM recommendation_log "
            "WHERE recommendation_id = ?",
            ("rec_pending",),
        ).fetchone()["c"]
    finally:
        conn.close()

    assert outcomes == []
    assert rec_count == 1
