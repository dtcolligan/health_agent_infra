"""W-D arm-1 — nutrition partial-day classification suppression (v0.1.15).

Per `hai/reporting/plans/v0_1_15/PLAN.md` §2.E.

When `is_partial_day == True && target_status in ('absent', 'unavailable')`,
the nutrition classifier suppresses its output: emits
`nutrition_status='insufficient_data'` with reason `partial_day_no_target`
in the uncertainty tuple. The runtime explicitly refuses to classify
rather than misclassifying the partial-day intake against a config-baseline
target the user hasn't actually committed to.

W-D arm-1 fires when both signals are true. Per round-4 PLAN §2.B:
`is_partial_day` is the time + meal-count signal (target-independent);
`target_status` is the three-valued enum reading the existing `target`
table.

Acceptance per PLAN §2.E:

  1. 10am breakfast-only intake (1344 kcal, partial-day) with
     target_status='absent' → nutrition_status='insufficient_data',
     uncertainty includes 'partial_day_no_target'. Without W-D arm-1
     this misclassified as 'high_deficit'.
  2. 10am breakfast-only with target_status='unavailable' (no
     nutrition target rows for user) → same suppression.
  3. 19:00 day-closed intake (is_partial_day=False) with any
     target_status → classifies normally (existing behavior).
  4. 10am breakfast-only with target_status='present' → falls
     through to existing classifier (W-D arm-2 is deferred to
     v0.1.17; documented as known incomplete).
  5. No call-graph changes outside `domains/nutrition/`.
"""

from __future__ import annotations

import pytest

from health_agent_infra.domains.nutrition import classify_nutrition_state
from health_agent_infra.domains.nutrition.signals import (
    derive_nutrition_signals,
)


def _breakfast_only_today_row() -> dict:
    """The maintainer's 2026-05-02 evidence row: 1344 kcal at 10am
    after a 1-meal breakfast log."""
    return {
        "calories": 1344.0,
        "protein_g": 50.0,
        "carbs_g": 140.0,
        "fat_g": 60.0,
        "hydration_l": None,
        "meals_count": 1,
        "derivation_path": "daily_macros",
    }


def _evening_full_day_row() -> dict:
    """End-of-day row with 4 meals + full intake."""
    return {
        "calories": 3100.0,
        "protein_g": 165.0,
        "carbs_g": 350.0,
        "fat_g": 90.0,
        "hydration_l": 2.5,
        "meals_count": 4,
        "derivation_path": "daily_macros",
    }


# ---------------------------------------------------------------------------
# Acceptance test 1 — partial-day + absent target → suppression
# ---------------------------------------------------------------------------


def test_w_d_arm_1_suppresses_when_partial_day_and_target_absent():
    """PLAN §2.E acceptance 1: morning breakfast-only intake with
    target_status='absent' suppresses the classifier."""

    signals = derive_nutrition_signals(
        nutrition_today=_breakfast_only_today_row(),
        is_partial_day=True,
        target_status="absent",
    )
    result = classify_nutrition_state(signals)

    assert result.nutrition_status == "insufficient_data", (
        f"expected suppression to insufficient_data; got {result.nutrition_status}"
    )
    assert "partial_day_no_target" in result.uncertainty, (
        f"expected partial_day_no_target reason token; got {result.uncertainty}"
    )
    # Score is None because we explicitly refuse to score partial data.
    assert result.nutrition_score is None
    # Coverage band reflects the suppression.
    assert result.coverage_band in ("insufficient", "partial_day_no_target")


# ---------------------------------------------------------------------------
# Acceptance test 2 — partial-day + unavailable target → suppression
# ---------------------------------------------------------------------------


def test_w_d_arm_1_suppresses_when_partial_day_and_target_unavailable():
    """PLAN §2.E acceptance 2: target_status='unavailable' (no nutrition
    target rows for the user at all) is treated identically to 'absent'
    per OQ-7 ratification — both trigger suppression."""

    signals = derive_nutrition_signals(
        nutrition_today=_breakfast_only_today_row(),
        is_partial_day=True,
        target_status="unavailable",
    )
    result = classify_nutrition_state(signals)

    assert result.nutrition_status == "insufficient_data"
    assert "partial_day_no_target" in result.uncertainty


# ---------------------------------------------------------------------------
# Acceptance test 3 — day-closed → normal classification (no suppression)
# ---------------------------------------------------------------------------


def test_w_d_arm_1_does_not_suppress_when_day_is_closed():
    """PLAN §2.E acceptance 3: when is_partial_day=False (day closed),
    classifier runs normally regardless of target_status."""

    for target_status in ("present", "absent", "unavailable"):
        signals = derive_nutrition_signals(
            nutrition_today=_evening_full_day_row(),
            is_partial_day=False,
            target_status=target_status,
        )
        result = classify_nutrition_state(signals)
        assert result.nutrition_status != "insufficient_data", (
            f"day-closed intake with target_status={target_status} "
            f"should NOT be suppressed; got {result.nutrition_status}"
        )


# ---------------------------------------------------------------------------
# Acceptance test 4 — partial-day + present target → fall-through
# ---------------------------------------------------------------------------


def test_w_d_arm_1_fall_through_when_partial_day_and_target_present():
    """PLAN §2.E acceptance 4: when target_status='present' and
    is_partial_day=True, the classifier falls through to existing
    behavior (W-D arm-2 end-of-day projection is deferred to v0.1.17;
    documented as known incomplete in PLAN §4 risk 4)."""

    signals = derive_nutrition_signals(
        nutrition_today=_breakfast_only_today_row(),
        is_partial_day=True,
        target_status="present",
    )
    result = classify_nutrition_state(signals)

    # NOT suppressed — falls through to existing classifier behavior
    # (which currently treats the row as if end-of-day; the W-D arm-2
    # projection is the v0.1.17 fix).
    assert result.nutrition_status != "insufficient_data", (
        "partial_day=true + target_status=present should fall through, "
        "not suppress (W-D arm-2 deferred to v0.1.17)"
    )


# ---------------------------------------------------------------------------
# Backwards-compat: W-D arm-1 inputs are optional
# ---------------------------------------------------------------------------


def test_classify_unchanged_when_w_d_arm_1_signals_are_omitted():
    """Backwards-compat: omitting is_partial_day / target_status produces
    identical output to the pre-W-D classifier (existing call-sites that
    haven't been wired to W-A yet are not regressed)."""

    today_row = _evening_full_day_row()
    signals_with = derive_nutrition_signals(
        nutrition_today=today_row,
        is_partial_day=False,
        target_status=None,
    )
    signals_without = derive_nutrition_signals(
        nutrition_today=today_row,
    )
    a = classify_nutrition_state(signals_with)
    b = classify_nutrition_state(signals_without)
    assert a.nutrition_status == b.nutrition_status
    assert a.calorie_balance_band == b.calorie_balance_band
    assert a.nutrition_score == b.nutrition_score


# ---------------------------------------------------------------------------
# Snapshot-side wiring: W-A presence signals threaded through
# ---------------------------------------------------------------------------


def test_snapshot_wiring_passes_w_a_signals_into_nutrition_classifier(
    tmp_path,
):
    """The snapshot path is the production daily-pipeline route. After
    W-D arm-1 lands, the snapshot's `nutrition.classified_state` should
    reflect the partial-day suppression when the W-A signals indicate
    it. End-to-end: seed a partial-day breakfast row + no nutrition
    targets → snapshot's nutrition status is 'insufficient_data'."""

    from datetime import date, datetime, timezone
    from pathlib import Path
    import sqlite3

    from health_agent_infra.core.state import (
        build_snapshot,
        initialize_database,
        open_connection,
    )

    db = tmp_path / "state.db"
    initialize_database(db)

    user = "u_test"
    today = date(2026, 5, 3)

    # Seed a breakfast-only nutrition row.
    conn = sqlite3.connect(str(db))
    try:
        conn.execute(
            "INSERT INTO nutrition_intake_raw "
            "(submission_id, user_id, as_of_date, calories, protein_g, "
            "carbs_g, fat_g, hydration_l, meals_count, source, "
            "ingest_actor, ingested_at, supersedes_submission_id) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "m_nut_test", user, today.isoformat(),
                1344.0, 50.0, 140.0, 60.0, None, 1,
                "user_manual", "cli",
                datetime.now(timezone.utc).isoformat(), None,
            ),
        )
        # Also project into accepted_nutrition_state_daily so build_snapshot
        # finds it.
        conn.execute(
            "INSERT INTO accepted_nutrition_state_daily "
            "(as_of_date, user_id, calories, protein_g, carbs_g, fat_g, "
            "hydration_l, meals_count, derived_from, source, "
            "ingest_actor, projected_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                today.isoformat(), user, 1344.0, 50.0, 140.0, 60.0,
                None, 1, "m_nut_test", "user_manual",
                "cli", datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    conn = open_connection(db)
    try:
        # Force is_partial_day=True via build_snapshot's now_local override
        # if available; otherwise the test relies on the snapshot's own
        # time-aware derivation. We pass a partial-day morning timestamp.
        snap = build_snapshot(
            conn,
            as_of_date=today,
            user_id=user,
            evidence_bundle=None,
            now_local=datetime(2026, 5, 3, 10, 17),
        )
    finally:
        conn.close()

    nutrition_block = snap.get("nutrition") or {}
    classified = nutrition_block.get("classified_state") or {}
    # Partial-day breakfast with no nutrition targets in the table
    # → snapshot reports nutrition_status='insufficient_data'.
    assert classified.get("nutrition_status") == "insufficient_data", (
        f"snapshot wiring should propagate W-D arm-1 suppression; "
        f"got nutrition_status={classified.get('nutrition_status')!r}"
    )
