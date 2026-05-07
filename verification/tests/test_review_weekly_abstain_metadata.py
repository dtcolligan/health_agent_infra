"""W52 step 2 — abstain-branch metadata is quantitative AND validated
via deterministic substitution from query output (PLAN §2.D acceptance
#2 + round-1 correction per F-PLAN-03).

The original PLAN framing said "no claim cards on abstain because the
abstain prose is non-quantitative"; the round-1 correction reframed:
the abstain prose IS quantitative, but it's validated via a stricter
deterministic-substitution path that doesn't go through prose
authoring. These tests pin that path:

  - Counts (`days_with_plans` integer) come from the SQL query result.
  - Threshold (`coverage_threshold`) is a literal substitution from
    `thresholds.toml` `policy.review_weekly.coverage_threshold_days`.
  - Date lists (`populated_dates`, `missing_dates`) are direct
    enumerations of the SQL result rows + the week's ISO-date set.

If the substitution is byte-stable AND the query is correct, the
abstain prose claim is correct. The structurally simpler path is
the reason no claim cards are written on abstain.

Plus the D13 threshold-injection-seam contract (acceptance #3): a
bool-shaped override for `coverage_threshold_days` is rejected at
`load_thresholds` boundary by `_validate_threshold_types`.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from health_agent_infra.core.config import (
    DEFAULT_THRESHOLDS,
    ConfigCoerceError,
    load_thresholds,
)
from health_agent_infra.core.review.weekly import (
    WeeklyCoverage,
    evaluate_weekly_coverage,
    load_weekly_aggregation,
)
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


USER = "u_w52_abstain"


def _db(tmp_path: Path) -> sqlite3.Connection:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return open_connection(db_path)


def _insert_canonical_plan(
    conn: sqlite3.Connection,
    *,
    daily_plan_id: str,
    for_date: str,
    user_id: str = USER,
) -> None:
    conn.execute(
        "INSERT INTO daily_plan ("
        "  daily_plan_id, user_id, for_date, synthesized_at, "
        "  recommendation_ids_json, proposal_ids_json, "
        "  x_rules_fired_json, synthesis_meta_json, source, "
        "  ingest_actor, agent_version, validated_at, projected_at, "
        "  superseded_by_plan_id, superseded_at"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)",
        (
            daily_plan_id, user_id, for_date,
            f"{for_date}T07:00:00Z",
            json.dumps([]), json.dumps([]), json.dumps([]),
            None,
            "claude_agent_v1", "claude_agent_v1", "0.2.0",
            f"{for_date}T07:00:00Z", f"{for_date}T07:00:01Z",
        ),
    )


# ---------------------------------------------------------------------------
# Test 1 — DEFAULT_THRESHOLDS includes the review_weekly block
# ---------------------------------------------------------------------------


def test_default_thresholds_include_review_weekly_block():
    """The threshold block must exist in `DEFAULT_THRESHOLDS` so a
    fresh install (no user TOML) has the abstain threshold available
    without a config-init step. Types must match the D13 contract:
    `coverage_threshold_days` strictly int, `data_quality_stale_pull_hours`
    strictly int (both consumed by integer arithmetic at call sites).
    """

    block = DEFAULT_THRESHOLDS["policy"]["review_weekly"]
    assert block["coverage_threshold_days"] == 5
    assert isinstance(block["coverage_threshold_days"], int)
    assert not isinstance(block["coverage_threshold_days"], bool)
    assert block["data_quality_stale_pull_hours"] == 48
    assert isinstance(block["data_quality_stale_pull_hours"], int)
    assert not isinstance(block["data_quality_stale_pull_hours"], bool)


# ---------------------------------------------------------------------------
# Test 2 — abstain branch fires under threshold
# ---------------------------------------------------------------------------


def test_evaluate_weekly_coverage_below_threshold_returns_insufficient_data(
    tmp_path: Path,
):
    """A week with 3 of 7 days populated and threshold 5 fires the
    abstain branch. The PLAN §2.D abstain prose template substitutes
    the integer 3 (days), 7 (week constant), 5 (threshold), the 3
    populated dates, and the 4 missing dates — all of which come
    from `WeeklyCoverage`.
    """

    conn = _db(tmp_path)
    try:
        # 2026-W18 = Mon 04-27 → Sun 05-03. Populate 3 of 7 days.
        _insert_canonical_plan(
            conn,
            daily_plan_id="plan_2026-04-27_u_w52_abstain",
            for_date="2026-04-27",
        )
        _insert_canonical_plan(
            conn,
            daily_plan_id="plan_2026-04-29_u_w52_abstain",
            for_date="2026-04-29",
        )
        _insert_canonical_plan(
            conn,
            daily_plan_id="plan_2026-05-01_u_w52_abstain",
            for_date="2026-05-01",
        )
        conn.commit()

        agg = load_weekly_aggregation(
            conn, iso_week="2026-W18", user_id=USER,
        )
        coverage = evaluate_weekly_coverage(
            agg, coverage_threshold_days=5,
        )

        assert coverage.weekly_status == "insufficient_data"
        assert coverage.days_with_plans == 3
        assert coverage.coverage_threshold == 5
        assert coverage.populated_dates == [
            "2026-04-27", "2026-04-29", "2026-05-01",
        ]
        assert coverage.missing_dates == [
            "2026-04-28", "2026-04-30", "2026-05-02", "2026-05-03",
        ]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 3 — abstain doesn't fire AT threshold (5/7 with threshold=5)
# ---------------------------------------------------------------------------


def test_evaluate_weekly_coverage_at_threshold_returns_ok(tmp_path: Path):
    """At exactly the threshold, the abstain branch does NOT fire.
    The PLAN says "fewer than `coverage_threshold` days" — strict
    less-than, not less-than-or-equal. 5 of 7 with threshold 5 is OK.
    """

    conn = _db(tmp_path)
    try:
        for d in ("2026-04-27", "2026-04-28", "2026-04-29",
                  "2026-04-30", "2026-05-01"):
            _insert_canonical_plan(
                conn,
                daily_plan_id=f"plan_{d}_u_w52_abstain",
                for_date=d,
            )
        conn.commit()

        agg = load_weekly_aggregation(
            conn, iso_week="2026-W18", user_id=USER,
        )
        coverage = evaluate_weekly_coverage(
            agg, coverage_threshold_days=5,
        )
        assert coverage.weekly_status == "ok"
        assert coverage.days_with_plans == 5
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 4 — multi-canonical day counts ONCE toward days_with_plans
# ---------------------------------------------------------------------------


def test_evaluate_weekly_coverage_multi_canonical_day_counts_once(
    tmp_path: Path,
):
    """F-PHASE0-07 multi-canonical day: two non-superseded plans on the
    same `for_date` count as ONE populated day for the abstain metric
    (the metric is "days with plan evidence", not "plans count"). Both
    plan rows still surface in `aggregation.canonical_plans`.
    """

    conn = _db(tmp_path)
    try:
        _insert_canonical_plan(
            conn,
            daily_plan_id="plan_2026-04-27_morning",
            for_date="2026-04-27",
        )
        _insert_canonical_plan(
            conn,
            daily_plan_id="plan_2026-04-27_evening",
            for_date="2026-04-27",
        )
        conn.commit()

        agg = load_weekly_aggregation(
            conn, iso_week="2026-W18", user_id=USER,
        )
        # Both plan rows surface in aggregation.
        assert len(agg.canonical_plans) == 2
        # But the day counts ONCE toward coverage.
        coverage = evaluate_weekly_coverage(
            agg, coverage_threshold_days=5,
        )
        assert coverage.days_with_plans == 1
        assert coverage.populated_dates == ["2026-04-27"]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 5 — D13 threshold-injection-seam rejects bool override
# ---------------------------------------------------------------------------


def test_load_thresholds_rejects_bool_override_for_coverage_threshold(
    tmp_path: Path,
):
    """Per D13 contract: `_validate_threshold_types` at
    `load_thresholds` boundary rejects bool overrides on numeric
    defaults. A user who writes
    `[policy.review_weekly] coverage_threshold_days = true` triggers
    `ConfigCoerceError` at load time, not silent bool-as-int coercion
    inside the abstain comparison (where True == 1 would lower the
    threshold from 5 to 1, silently disabling the abstain branch).
    """

    bad_toml = tmp_path / "thresholds.toml"
    bad_toml.write_text(
        '[policy.review_weekly]\n'
        'coverage_threshold_days = true\n'
    )
    with pytest.raises(ConfigCoerceError) as exc_info:
        load_thresholds(path=bad_toml)
    # Error message must name the offending dotted path.
    msg = str(exc_info.value)
    assert "review_weekly" in msg
    assert "coverage_threshold_days" in msg


# ---------------------------------------------------------------------------
# Test 6 — load_thresholds round-trips a valid integer override
# ---------------------------------------------------------------------------


def test_load_thresholds_applies_integer_override_for_coverage_threshold(
    tmp_path: Path,
):
    """Positive companion to test 5: a strict-integer override loads
    cleanly and the value flows through to `policy.review_weekly`.
    Confirms the threshold-injection seam is not over-zealous —
    legitimate integer overrides pass.
    """

    user_toml = tmp_path / "thresholds.toml"
    user_toml.write_text(
        '[policy.review_weekly]\n'
        'coverage_threshold_days = 7\n'  # override floor: require all 7 days
    )
    merged = load_thresholds(path=user_toml)
    assert merged["policy"]["review_weekly"]["coverage_threshold_days"] == 7
    assert merged["policy"]["review_weekly"]["data_quality_stale_pull_hours"] == 48
    # Type round-trips as int (not bool, not float).
    assert isinstance(
        merged["policy"]["review_weekly"]["coverage_threshold_days"],
        int,
    )
    assert not isinstance(
        merged["policy"]["review_weekly"]["coverage_threshold_days"],
        bool,
    )


# ---------------------------------------------------------------------------
# Test 7 — empty week is the boundary case (0 < threshold)
# ---------------------------------------------------------------------------


def test_evaluate_weekly_coverage_empty_week_is_insufficient_data(
    tmp_path: Path,
):
    """A week with no plan evidence is the most-abstaining case.
    `days_with_plans=0`, `populated_dates=[]`, `missing_dates` lists
    all 7 ISO-week dates in chronological order. This is the shape
    a user sees on a brand-new install before any `hai daily` runs.
    """

    conn = _db(tmp_path)
    try:
        agg = load_weekly_aggregation(
            conn, iso_week="2026-W18", user_id=USER,
        )
        coverage = evaluate_weekly_coverage(
            agg, coverage_threshold_days=5,
        )
        assert coverage.weekly_status == "insufficient_data"
        assert coverage.days_with_plans == 0
        assert coverage.populated_dates == []
        assert coverage.missing_dates == [
            "2026-04-27", "2026-04-28", "2026-04-29",
            "2026-04-30", "2026-05-01", "2026-05-02", "2026-05-03",
        ]
        # WeeklyCoverage is frozen — sanity check it's a dataclass
        # frozen instance (immutability part of the deterministic-
        # substitution contract).
        assert isinstance(coverage, WeeklyCoverage)
        with pytest.raises((AttributeError, TypeError)):
            coverage.weekly_status = "ok"  # type: ignore[misc]
    finally:
        conn.close()
