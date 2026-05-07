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
import re
import sqlite3
from datetime import date
from pathlib import Path

from health_agent_infra.core.review.prose_builder import (
    WeeklyAtom,
    WeeklyProseBundle,
    build_weekly_prose,
    load_primary_goal,
)
from health_agent_infra.core.review.weekly import (
    ACCEPTED_STATE_TABLES,
    DATA_QUALITY_CLASSIFICATIONS,
    TABLE_TO_DOMAIN,
    WeeklySyncRunRow,
    classify_sync_run_quality,
    compute_data_quality_rollup,
    evaluate_weekly_coverage,
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


# ---------------------------------------------------------------------------
# Tests 12-17 — prose-builder obligation hooks (W-EXPLAIN-UX-CARRY 1-6)
# ---------------------------------------------------------------------------


def _seed_full_week(conn: sqlite3.Connection) -> None:
    """Seed a full 7-day week (5 plan-days + 2 missing) with one
    recovery recommendation + an X9 firing on the same plan + a
    user_memory primary_goal entry. Used by the obligation hook
    tests that need real prose to assert against.
    """

    # 5 plan-days — over the abstain threshold so the prose builder
    # produces real sections.
    plan_dates = [
        "2026-04-27", "2026-04-28", "2026-04-29",
        "2026-04-30", "2026-05-01",
    ]
    for d in plan_dates:
        _insert_plan(
            conn,
            daily_plan_id=f"plan_{d}_full",
            for_date=d,
            superseded_by=None,
        )
        _insert_recommendation(
            conn,
            recommendation_id=f"rec_{d}_full",
            daily_plan_id=f"plan_{d}_full",
            for_date=d,
            domain="recovery",
            action="easy_recovery",
        )
    # X9 firing on the 04-28 plan (Phase B).
    conn.execute(
        "INSERT INTO x_rule_firing ("
        "  daily_plan_id, user_id, x_rule_id, tier, affected_domain, "
        "  trigger_note, mutation_json, source_signals_json, fired_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "plan_2026-04-28_full", USER, "X9", "adjust", "recovery",
            "training intensity bump", None, "{}",
            "2026-04-28T07:00:01Z",
        ),
    )
    # Phase A (X1a) firing on the 04-29 plan.
    conn.execute(
        "INSERT INTO x_rule_firing ("
        "  daily_plan_id, user_id, x_rule_id, tier, affected_domain, "
        "  trigger_note, mutation_json, source_signals_json, fired_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "plan_2026-04-29_full", USER, "X1a", "soften", "recovery",
            "sleep debt moderate", None, "{}",
            "2026-04-29T07:00:01Z",
        ),
    )
    # primary_goal in user_memory.
    conn.execute(
        "INSERT INTO user_memory ("
        "  memory_id, user_id, category, key, value, "
        "  domain, created_at, archived_at, source, ingest_actor"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "mem_goal_1", USER, "goal", "primary_goal",
            "lean cut while preserving strength",
            None, "2026-04-25T10:00:00Z", None,
            "user_manual", "claude_agent_v1",
        ),
    )
    conn.commit()


def _build_prose_for_full_week(
    conn: sqlite3.Connection,
    *,
    deferred_domains: list[str] | None = None,
) -> WeeklyProseBundle:
    agg = load_weekly_aggregation(
        conn, iso_week="2026-W18", user_id=USER,
    )
    coverage = evaluate_weekly_coverage(
        agg, coverage_threshold_days=5,
    )
    rollup = compute_data_quality_rollup(
        agg.sync_runs, stale_pull_hours=48,
    )
    return build_weekly_prose(
        conn, agg, coverage, rollup,
        deferred_domains=deferred_domains,
    )


def _all_atom_text(bundle: WeeklyProseBundle) -> str:
    return "\n".join(
        atom.atom_text
        for section in bundle.sections
        for atom in section.atoms
    )


def test_prose_header_echoes_primary_goal(tmp_path: Path):
    """W-EXPLAIN-UX-CARRY obligation #5 (F-EXPLAIN-05): weekly-
    review prose contains the user's primary_goal value as the
    first noun phrase of the body, sourced from user_memory.
    """

    conn = _db(tmp_path)
    try:
        _seed_full_week(conn)
        bundle = _build_prose_for_full_week(conn)
        assert bundle.primary_goal == "lean cut while preserving strength"
        # First section is the header; first atom is the goal echo.
        header = bundle.sections[0]
        assert header.section_id == "header"
        first_atom = header.atoms[0]
        assert first_atom.atom_id == "header.goal_echo"
        assert "lean cut while preserving strength" in first_atom.atom_text
    finally:
        conn.close()


def test_prose_no_xrule_id_outside_parens(tmp_path: Path):
    """W-EXPLAIN-UX-CARRY obligation #1 (F-EXPLAIN-01): weekly-
    review prose contains zero opaque `X<N>` rule-ID strings outside
    parentheses. `X9` and `X1a` from the seeded firings must surface
    only in `(X9)` / `(X1a)` audit citations.
    """

    conn = _db(tmp_path)
    try:
        _seed_full_week(conn)
        bundle = _build_prose_for_full_week(conn)
        text = _all_atom_text(bundle)
        # Find every "X<N>" or "X<Nx>" pattern in the prose.
        for match in re.finditer(r"X\d+[a-z]?", text):
            start = match.start()
            end = match.end()
            # Look for the nearest "(" before and ")" after — the
            # string must be inside a parenthetical group.
            before = text[:start]
            open_idx = before.rfind("(")
            close_idx = before.rfind(")")
            assert open_idx > close_idx, (
                f"raw rule-ID {match.group()} at offset {start} "
                f"appears outside parentheses in:\n{text}"
            )
            after = text[end:]
            assert ")" in after.split("\n", 1)[0], (
                f"raw rule-ID {match.group()} at offset {start} "
                f"is not closed by ')' on the same line:\n{text}"
            )
    finally:
        conn.close()


def test_prose_no_phase_a_b_raw_strings(tmp_path: Path):
    """W-EXPLAIN-UX-CARRY obligation #2 (F-EXPLAIN-02): markdown
    weekly-review never exposes raw `phase_a` / `phase_b` keys.
    The runtime concept surfaces as inline prose ("rules that
    shaped the recommendation" / "rules that adjusted the result
    after the skill ran").
    """

    conn = _db(tmp_path)
    try:
        _seed_full_week(conn)
        bundle = _build_prose_for_full_week(conn)
        text = _all_atom_text(bundle)
        assert "phase_a" not in text
        assert "phase_b" not in text
        # Inline prose IS present for the seeded firings.
        assert (
            "rules that shaped the recommendation" in text.lower()
            or "rules that adjusted the result" in text.lower()
        )
    finally:
        conn.close()


def test_prose_no_synthesis_meta_string(tmp_path: Path):
    """W-EXPLAIN-UX-CARRY obligation #3 (F-EXPLAIN-03): markdown
    weekly-review never contains the string `synthesis_meta`. The
    JSON render layer (step 5) keeps it; prose does not.
    """

    conn = _db(tmp_path)
    try:
        _seed_full_week(conn)
        bundle = _build_prose_for_full_week(conn)
        text = _all_atom_text(bundle)
        assert "synthesis_meta" not in text
    finally:
        conn.close()


def test_prose_no_raw_caveat_tokens(tmp_path: Path):
    """W-EXPLAIN-UX-CARRY obligation #4 P0 (F-EXPLAIN-04): no
    caveat-token string (e.g. `calorie_surplus_trend`,
    `resting_hr_spike_3_days_running`) appears in weekly-review
    prose. Rationale routes through translate_caveat.

    Test: seed a recommendation with a known caveat token in its
    rationale; assert the rendered prose contains the translation
    but NOT the raw token.
    """

    conn = _db(tmp_path)
    try:
        _seed_full_week(conn)
        # Override the 04-27 recommendation to carry a reason_token
        # in its rationale.
        conn.execute(
            "UPDATE recommendation_log SET payload_json = ? "
            "WHERE recommendation_id = 'rec_2026-04-27_full'",
            (json.dumps({
                "action": "easy_recovery",
                "domain": "recovery",
                "rationale": [
                    {"reason_token": "resting_hr_spike_3_days_running"},
                ],
            }),),
        )
        conn.commit()
        bundle = _build_prose_for_full_week(conn)
        text = _all_atom_text(bundle)
        # The raw token must NOT appear.
        assert "resting_hr_spike_3_days_running" not in text
        # The translated phrase MUST appear.
        assert (
            "resting heart rate has been elevated for 3 days running"
            in text
        )
    finally:
        conn.close()


def test_prose_locator_cited_lead_in(tmp_path: Path):
    """W-EXPLAIN-UX-CARRY obligation #6 (F-EXPLAIN-07): every claim
    with `evidence_locators` is preceded by prose that names at
    least one of the locator's pk-fields.
    """

    conn = _db(tmp_path)
    try:
        _seed_full_week(conn)
        # Stamp a locator on the 04-28 recommendation.
        locator = {
            "table": "accepted_recovery_state_daily",
            "pk": {"as_of_date": "2026-04-28", "user_id": USER},
            "row_version": "2026-04-28T07:00:00Z",
        }
        conn.execute(
            "UPDATE recommendation_log "
            "SET evidence_locators_json = ? "
            "WHERE recommendation_id = 'rec_2026-04-28_full'",
            (json.dumps([locator]),),
        )
        conn.commit()
        bundle = _build_prose_for_full_week(conn)
        text = _all_atom_text(bundle)
        # The lead-in names the date pk-field (April 28).
        assert "April 28" in text
        # And it precedes the recommendation atom.
        rec_atom = next(
            atom
            for section in bundle.sections
            for atom in section.atoms
            if atom.atom_id.endswith("rec_2026-04-28_full")
        )
        assert rec_atom.atom_text.startswith("Looking at")
        assert "April 28" in rec_atom.atom_text
    finally:
        conn.close()


def test_prose_abstain_branch_emits_no_sections(tmp_path: Path):
    """When coverage.weekly_status == 'insufficient_data', the prose
    bundle's sections list is empty (the render layer surfaces the
    abstain template directly from coverage metadata; no claim
    cards on abstain).
    """

    conn = _db(tmp_path)
    try:
        # Seed only 2 plan days — under the 5-day threshold.
        for d in ("2026-04-27", "2026-04-29"):
            _insert_plan(
                conn,
                daily_plan_id=f"plan_{d}_partial",
                for_date=d,
            )
        conn.commit()

        agg = load_weekly_aggregation(
            conn, iso_week="2026-W18", user_id=USER,
        )
        coverage = evaluate_weekly_coverage(
            agg, coverage_threshold_days=5,
        )
        rollup = compute_data_quality_rollup(
            agg.sync_runs, stale_pull_hours=48,
        )
        bundle = build_weekly_prose(conn, agg, coverage, rollup)
        assert coverage.weekly_status == "insufficient_data"
        assert bundle.sections == []
        # The bundle still carries the coverage + rollup so the
        # render layer can produce the abstain template.
        assert bundle.coverage is coverage
    finally:
        conn.close()


def test_prose_load_primary_goal_returns_none_when_unset(tmp_path: Path):
    """`load_primary_goal` returns None when no active primary_goal
    exists in user_memory (honest abstain — never fabricated).
    """

    conn = _db(tmp_path)
    try:
        assert load_primary_goal(conn, user_id=USER) is None
        # Insert a goal then archive it; load returns None again.
        conn.execute(
            "INSERT INTO user_memory ("
            "  memory_id, user_id, category, key, value, "
            "  domain, created_at, archived_at, source, ingest_actor"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "mem_archived", USER, "goal", "primary_goal",
                "old goal", None, "2026-04-01T10:00:00Z",
                "2026-04-25T10:00:00Z",
                "user_manual", "claude_agent_v1",
            ),
        )
        conn.commit()
        # Archived → load_primary_goal still returns None.
        assert load_primary_goal(conn, user_id=USER) is None
    finally:
        conn.close()


