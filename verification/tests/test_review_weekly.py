"""W52 — `hai review weekly` aggregation queries (v0.2.0 §2.D).

Step 1 of W52 (commit 1 of 8): the 9 read-only aggregation loaders
in ``core/review/weekly.py`` produce a flat, typed
:class:`WeeklyAggregation` row set the prose builder + render layer
will consume. This test file covers aggregation correctness — the
five PLAN §2.D acceptance hooks that the queries themselves are
responsible for:

  - ISO-week date helper produces a 7-day Monday→Sunday set.
  - Canonical-leaf filter (``superseded_by_plan_id IS NULL``)
    surfaces only canonical plans (F-PHASE0-07 multi-canonical case
    surfaces both canonical rows; mid-chain rows are not surfaced).
  - recommendation_log scope filter is plan-id keyed.
  - review_outcome enrichments (mig 010) surface end-to-end.
  - Empty-week aggregation returns the empty-list shape with no
    crash and no fabricated rows.

Step 2+ commits add the abstain-branch + data-quality rollup +
prose builder + render + CLI tests.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from health_agent_infra.core.review.weekly import (
    ACCEPTED_STATE_TABLES,
    DATA_QUALITY_CLASSIFICATIONS,
    TABLE_TO_DOMAIN,
    WeeklySyncRunRow,
    classify_sync_run_quality,
    compute_data_quality_rollup,
    iso_week_dates,
    load_weekly_aggregation,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


USER = "u_w52_test"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return open_connection(db_path)


def _insert_plan(
    conn: sqlite3.Connection,
    *,
    daily_plan_id: str,
    for_date: str,
    superseded_by: str | None = None,
    rec_ids: list[str] | None = None,
    proposal_ids: list[str] | None = None,
    x_rules_fired: list[str] | None = None,
    user_id: str = USER,
) -> None:
    conn.execute(
        "INSERT INTO daily_plan ("
        "  daily_plan_id, user_id, for_date, synthesized_at, "
        "  recommendation_ids_json, proposal_ids_json, "
        "  x_rules_fired_json, synthesis_meta_json, source, "
        "  ingest_actor, agent_version, validated_at, projected_at, "
        "  superseded_by_plan_id, superseded_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            daily_plan_id, user_id, for_date,
            f"{for_date}T07:00:00Z",
            json.dumps(rec_ids or []),
            json.dumps(proposal_ids or []),
            json.dumps(x_rules_fired or []),
            None,
            "claude_agent_v1", "claude_agent_v1", "0.2.0",
            f"{for_date}T07:00:00Z", f"{for_date}T07:00:01Z",
            superseded_by,
            f"{for_date}T07:00:02Z" if superseded_by else None,
        ),
    )


def _insert_recommendation(
    conn: sqlite3.Connection,
    *,
    recommendation_id: str,
    daily_plan_id: str,
    for_date: str,
    domain: str = "recovery",
    action: str = "easy_recovery",
    user_id: str = USER,
) -> None:
    payload = {"action": action, "domain": domain, "rationale": []}
    conn.execute(
        "INSERT INTO recommendation_log ("
        "  recommendation_id, user_id, for_date, issued_at, action, "
        "  confidence, bounded, payload_json, source, ingest_actor, "
        "  agent_version, produced_at, validated_at, projected_at, "
        "  domain, daily_plan_id"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            recommendation_id, user_id, for_date,
            f"{for_date}T07:05:00Z",
            action, "high", 1, json.dumps(payload),
            "claude_agent_v1", "claude_agent_v1", "0.2.0",
            f"{for_date}T07:05:00Z", f"{for_date}T07:05:00Z",
            f"{for_date}T07:05:01Z",
            domain, daily_plan_id,
        ),
    )


def _insert_review_outcome(
    conn: sqlite3.Connection,
    *,
    review_event_id: str,
    recommendation_id: str,
    for_date: str,
    followed: int = 1,
    completed: int | None = 1,
    intensity_delta: str | None = "same",
    pre_energy: int | None = 3,
    post_energy: int | None = 4,
    user_id: str = USER,
) -> None:
    # The review_event row has a FK to recommendation_log; insert it first.
    conn.execute(
        "INSERT INTO review_event ("
        "  review_event_id, recommendation_id, user_id, review_at, "
        "  review_question, projected_at, domain"
        ") VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            review_event_id, recommendation_id, user_id,
            f"{for_date}T20:00:00Z",
            "How did the session go?",
            f"{for_date}T20:00:01Z",
            "recovery",
        ),
    )
    conn.execute(
        "INSERT INTO review_outcome ("
        "  review_event_id, recommendation_id, user_id, recorded_at, "
        "  followed_recommendation, self_reported_improvement, "
        "  free_text, source, ingest_actor, projected_at, domain, "
        "  completed, intensity_delta, duration_minutes, "
        "  pre_energy_score, post_energy_score, disagreed_firing_ids"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            review_event_id, recommendation_id, user_id,
            f"{for_date}T20:30:00Z",
            followed, 1, "felt good",
            "user_authored", "claude_agent_v1",
            f"{for_date}T20:30:01Z", "recovery",
            completed, intensity_delta, 45,
            pre_energy, post_energy, json.dumps([]),
        ),
    )


# ---------------------------------------------------------------------------
# Test 1 — ISO-week date helper
# ---------------------------------------------------------------------------


def test_iso_week_dates_returns_seven_dates_monday_to_sunday():
    """`iso_week_dates('2026-W18')` returns Mon 2026-04-27 → Sun 2026-05-03."""

    dates = iso_week_dates("2026-W18")
    assert dates == [
        date(2026, 4, 27),
        date(2026, 4, 28),
        date(2026, 4, 29),
        date(2026, 4, 30),
        date(2026, 5, 1),
        date(2026, 5, 2),
        date(2026, 5, 3),
    ]
    # First date is Monday (weekday() == 0); last is Sunday (== 6).
    assert dates[0].weekday() == 0
    assert dates[-1].weekday() == 6


# ---------------------------------------------------------------------------
# Test 2 — canonical-leaf filter (F-PHASE0-07)
# ---------------------------------------------------------------------------


def test_load_canonical_plans_filters_superseded_and_surfaces_multi_canonical(
    tmp_path: Path,
):
    """A week with one supersession chain (mid plan superseded by leaf)
    PLUS a multi-canonical day (two non-superseded plans on the same
    for_date) returns only the canonical-leaf rows for the chain AND
    BOTH rows for the multi-canonical day. F-PHASE0-07 explicitly
    forbids silent latest-wins on multi-canonical days.
    """

    conn = _db(tmp_path)
    try:
        # 2026-04-27 (Monday): chain of 2 plans, _v1 superseded by _v2.
        _insert_plan(
            conn,
            daily_plan_id="plan_2026-04-27_u_w52_test_v1",
            for_date="2026-04-27",
            superseded_by="plan_2026-04-27_u_w52_test_v2",
        )
        _insert_plan(
            conn,
            daily_plan_id="plan_2026-04-27_u_w52_test_v2",
            for_date="2026-04-27",
            superseded_by=None,
        )
        # 2026-04-29 (Wednesday): multi-canonical — two non-superseded
        # plans on the same date (the F-PHASE0-07 fixture shape).
        _insert_plan(
            conn,
            daily_plan_id="plan_2026-04-29_u_w52_test_morning",
            for_date="2026-04-29",
            superseded_by=None,
        )
        _insert_plan(
            conn,
            daily_plan_id="plan_2026-04-29_u_w52_test_evening",
            for_date="2026-04-29",
            superseded_by=None,
        )
        conn.commit()

        agg = load_weekly_aggregation(
            conn, iso_week="2026-W18", user_id=USER,
        )
        plan_ids = {p.daily_plan_id for p in agg.canonical_plans}
        assert plan_ids == {
            "plan_2026-04-27_u_w52_test_v2",
            "plan_2026-04-29_u_w52_test_morning",
            "plan_2026-04-29_u_w52_test_evening",
        }
        # Every surfaced row has superseded_by_plan_id NULL.
        for plan in agg.canonical_plans:
            assert plan.superseded_by_plan_id is None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 3 — recommendation_log scope filter
# ---------------------------------------------------------------------------


def test_load_recommendations_scoped_to_canonical_plan_ids(tmp_path: Path):
    """Recommendations link to canonical-leaf plans only. A
    recommendation written against a superseded plan id stays in
    the table but is NOT returned by the weekly aggregation, since
    the canonical-plan scope filter excludes it.
    """

    conn = _db(tmp_path)
    try:
        # Canonical leaf
        _insert_plan(
            conn,
            daily_plan_id="plan_canonical",
            for_date="2026-04-27",
            superseded_by=None,
        )
        # Superseded predecessor (with its own — orphaned — recommendation row)
        _insert_plan(
            conn,
            daily_plan_id="plan_superseded",
            for_date="2026-04-27",
            superseded_by="plan_canonical",
        )
        _insert_recommendation(
            conn,
            recommendation_id="rec_canonical",
            daily_plan_id="plan_canonical",
            for_date="2026-04-27",
            domain="recovery",
        )
        _insert_recommendation(
            conn,
            recommendation_id="rec_superseded",
            daily_plan_id="plan_superseded",
            for_date="2026-04-27",
            domain="recovery",
        )
        conn.commit()

        agg = load_weekly_aggregation(
            conn, iso_week="2026-W18", user_id=USER,
        )
        rec_ids = {r.recommendation_id for r in agg.recommendations}
        assert rec_ids == {"rec_canonical"}
        assert "rec_superseded" not in rec_ids
        # Domain + bounded round-trip cleanly.
        rec = agg.recommendations[0]
        assert rec.domain == "recovery"
        assert rec.bounded is True
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 4 — review_outcome enrichment columns surface
# ---------------------------------------------------------------------------


def test_load_review_outcomes_includes_mig_010_enrichments(tmp_path: Path):
    """Migration 010 added 6 enrichment columns to review_outcome
    (completed, intensity_delta, duration_minutes, pre/post_energy_score,
    disagreed_firing_ids). The weekly loader surfaces them all so the
    prose layer + W58D fact gate can read them.
    """

    conn = _db(tmp_path)
    try:
        _insert_plan(
            conn,
            daily_plan_id="plan_review",
            for_date="2026-04-28",
            superseded_by=None,
        )
        _insert_recommendation(
            conn,
            recommendation_id="rec_review",
            daily_plan_id="plan_review",
            for_date="2026-04-28",
        )
        _insert_review_outcome(
            conn,
            review_event_id="rev_event_1",
            recommendation_id="rec_review",
            for_date="2026-04-28",
            followed=1,
            completed=1,
            intensity_delta="same",
            pre_energy=2,
            post_energy=4,
        )
        conn.commit()

        agg = load_weekly_aggregation(
            conn, iso_week="2026-W18", user_id=USER,
        )
        assert len(agg.review_outcomes) == 1
        outcome = agg.review_outcomes[0]
        assert outcome.recommendation_id == "rec_review"
        assert outcome.followed_recommendation is True
        assert outcome.self_reported_improvement is True
        assert outcome.completed is True
        assert outcome.intensity_delta == "same"
        assert outcome.duration_minutes == 45
        assert outcome.pre_energy_score == 2
        assert outcome.post_energy_score == 4
        assert outcome.disagreed_firing_ids == []
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 5 — empty-week aggregation returns empty-list shape
# ---------------------------------------------------------------------------


def test_load_weekly_aggregation_on_empty_db_returns_empty_lists(
    tmp_path: Path,
):
    """A week with no committed state returns the empty-list shape:
    every list field is `[]`, no exception, no fabricated rows. The
    abstain-branch logic (commit 2) layers on top of this and only
    fires when canonical_plans is empty AND under-threshold; here
    we just verify the empty shape itself round-trips cleanly.
    """

    conn = _db(tmp_path)
    try:
        agg = load_weekly_aggregation(
            conn, iso_week="2026-W18", user_id=USER,
        )
        assert agg.iso_week == "2026-W18"
        assert agg.user_id == USER
        assert len(agg.week_dates) == 7
        assert agg.canonical_plans == []
        assert agg.recommendations == []
        assert agg.x_rule_firings == []
        assert agg.review_outcomes == []
        assert agg.evidence_cards == []
        assert agg.accepted_state_rows == []
        assert agg.data_quality_rows == []
        assert agg.sync_runs == []
        assert agg.runtime_events == []
        assert agg.intent_rows == []
        assert agg.target_rows == []
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 6 — accepted-state-table whitelist invariants
# ---------------------------------------------------------------------------


def _sync_run(
    *,
    sync_id: int,
    source: str,
    mode: str,
    started_at: str,
    for_date: str | None,
    user_id: str = USER,
) -> WeeklySyncRunRow:
    """Build a WeeklySyncRunRow stub for direct classifier testing."""
    return WeeklySyncRunRow(
        sync_id=sync_id,
        source=source,
        user_id=user_id,
        mode=mode,
        started_at=started_at,
        completed_at=started_at,
        status="ok",
        for_date=for_date,
    )


# ---------------------------------------------------------------------------
# Tests 7-10 — data-quality classifier (PLAN §2.D acceptance #5)
# ---------------------------------------------------------------------------


def test_classify_sync_run_csv_pull_with_old_for_date_is_stale_pull():
    """`mode='csv'` AND for_date older than 48h before started_at →
    `stale_pull`. The Garmin CSV adapter wrote data for a for_date
    already 48+h stale at sync time — the upstream export is lagging.
    """

    run = _sync_run(
        sync_id=1, source="garmin", mode="csv",
        started_at="2026-04-29T10:00:00Z",
        for_date="2026-04-26",  # 80h before started_at
    )
    out = classify_sync_run_quality(run, stale_pull_hours=48)
    assert out.classification == "stale_pull"
    assert out.gap_hours is not None and out.gap_hours > 48.0


def test_classify_sync_run_manual_intake_for_past_date_is_retrospective_manual():
    """`mode='manual'` AND for_date strictly before started_at civil
    date → `retrospective_manual`. The user deliberately backfilled.
    Distinguished from stale_pull because the gap is intentional.
    """

    run = _sync_run(
        sync_id=2, source="user_manual", mode="manual",
        started_at="2026-04-29T20:00:00Z",
        for_date="2026-04-27",  # 2 days back
    )
    out = classify_sync_run_quality(run, stale_pull_hours=48)
    assert out.classification == "retrospective_manual"


def test_classify_sync_run_same_day_is_fresh_regardless_of_mode():
    """Sync ran for the same civil date as started_at → `fresh`.
    Holds for both auto-pull (csv/live) and manual modes — a manual
    same-day log is not retrospective.
    """

    csv_today = _sync_run(
        sync_id=3, source="garmin", mode="csv",
        started_at="2026-04-29T10:00:00Z",
        for_date="2026-04-29",
    )
    manual_today = _sync_run(
        sync_id=4, source="user_manual", mode="manual",
        started_at="2026-04-29T20:00:00Z",
        for_date="2026-04-29",
    )
    assert classify_sync_run_quality(
        csv_today, stale_pull_hours=48,
    ).classification == "fresh"
    assert classify_sync_run_quality(
        manual_today, stale_pull_hours=48,
    ).classification == "fresh"


def test_classify_sync_run_unclassifiable_when_for_date_missing():
    """A sync_run_log row with NULL for_date (legitimate per
    migration 008 — not every source carries a civil-date frame)
    classifies as `unclassifiable`. Surfaced honestly, not silently
    dropped.
    """

    run = _sync_run(
        sync_id=5, source="garmin", mode="live",
        started_at="2026-04-29T10:00:00Z",
        for_date=None,
    )
    out = classify_sync_run_quality(run, stale_pull_hours=48)
    assert out.classification == "unclassifiable"
    assert out.gap_hours is None


def test_compute_data_quality_rollup_aggregates_counts_per_classification():
    """The rollup aggregates per-sync classifications into the four
    count buckets the prose layer cites for the week-level summary.
    """

    runs = [
        # 2 stale_pull (csv adapter lagging)
        _sync_run(
            sync_id=10, source="garmin", mode="csv",
            started_at="2026-04-29T10:00:00Z",
            for_date="2026-04-25",
        ),
        _sync_run(
            sync_id=11, source="intervals_icu", mode="live",
            started_at="2026-04-30T10:00:00Z",
            for_date="2026-04-26",
        ),
        # 1 retrospective_manual
        _sync_run(
            sync_id=12, source="user_manual", mode="manual",
            started_at="2026-04-30T20:00:00Z",
            for_date="2026-04-28",
        ),
        # 1 fresh
        _sync_run(
            sync_id=13, source="garmin", mode="csv",
            started_at="2026-04-30T10:00:00Z",
            for_date="2026-04-30",
        ),
        # 1 unclassifiable
        _sync_run(
            sync_id=14, source="garmin", mode="live",
            started_at="2026-04-30T10:00:00Z",
            for_date=None,
        ),
    ]
    rollup = compute_data_quality_rollup(runs, stale_pull_hours=48)
    assert rollup.threshold_hours == 48
    assert rollup.stale_pull_count == 2
    assert rollup.retrospective_manual_count == 1
    assert rollup.fresh_count == 1
    assert rollup.unclassifiable_count == 1
    # Plain-set assertion: every classification we emit is in the
    # frozen set of allowed classifications.
    for entry in rollup.per_sync:
        assert entry.classification in DATA_QUALITY_CLASSIFICATIONS


def test_accepted_state_tables_whitelist_covers_six_domains():
    """The whitelist must cover exactly the 6 domain accepted-state
    tables. If a future migration adds a 7th accepted-state table,
    this test forces a corresponding entry in the whitelist (and
    its TABLE_TO_DOMAIN mapping) — silent omission would leave a
    domain off the weekly view.
    """

    assert len(ACCEPTED_STATE_TABLES) == 6
    assert set(ACCEPTED_STATE_TABLES) == {
        "accepted_recovery_state_daily",
        "accepted_running_state_daily",
        "accepted_sleep_state_daily",
        "accepted_stress_state_daily",
        "accepted_resistance_training_state_daily",
        "accepted_nutrition_state_daily",
    }
    # Every whitelist entry has a domain mapping.
    for table in ACCEPTED_STATE_TABLES:
        assert table in TABLE_TO_DOMAIN
        assert TABLE_TO_DOMAIN[table] in {
            "recovery", "running", "sleep",
            "stress", "strength", "nutrition",
        }
