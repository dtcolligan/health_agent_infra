"""W48 — code-owned review summary builder.

Pins the contracts for ``core/review/summary.build_review_summary``:

  1. Empty DB → all counts zero, tokens = [insufficient_denominator].
  2. 7-day vs 14-day window scoping (window_days override).
  3. Token rules: insufficient denominator, recent positive, recent
     negative, mixed, none of the above.
  4. Per-domain filter never bleeds rows from other domains.
  5. Aggregate dict rolls up all six v1 domains correctly.
  6. ``re_linked_from_recommendation_id`` increments
     ``relinked_outcome_count``.
  7. Threshold overrides (``policy.review_summary``) flow through.
  8. Snapshot integration: ``snapshot.<domain>.review_summary`` is
     populated by ``build_snapshot``.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.review.summary import (
    TOKEN_INSUFFICIENT_DENOMINATOR,
    TOKEN_MIXED,
    TOKEN_RECENT_NEGATIVE,
    TOKEN_RECENT_POSITIVE,
    build_review_summary,
)
from health_agent_infra.core.state import (
    build_snapshot,
    initialize_database,
    open_connection,
)

from _fixtures import make_outcome_chain, seed_outcome_chain


AS_OF = date(2026, 4, 24)
USER = "u_test"


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _seed_chain(
    conn: sqlite3.Connection,
    *,
    suffix: str,
    domain: str,
    for_date: date,
    followed: bool,
    improved: bool | None,
    relink_from: str | None = None,
    intensity_delta: str | None = None,
) -> None:
    chain = make_outcome_chain(
        recommendation_id=f"rec_{suffix}",
        review_event_id=f"rev_{suffix}",
        user_id=USER,
        domain=domain,
        for_date=for_date,
        issued_at=datetime.combine(
            for_date, datetime.min.time(), tzinfo=timezone.utc
        ).replace(hour=7),
        followed=followed,
        improved=improved,
        re_linked_from_recommendation_id=relink_from,
        intensity_delta=intensity_delta,
    )
    seed_outcome_chain(conn, **chain)


# ---------------------------------------------------------------------------
# Empty DB
# ---------------------------------------------------------------------------


def test_empty_db_returns_insufficient_denominator(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        summary = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="recovery",
        )
    finally:
        conn.close()

    assert summary["recorded_outcome_count"] == 0
    assert summary["followed_count"] == 0
    assert summary["tokens"] == [TOKEN_INSUFFICIENT_DENOMINATOR]
    assert summary["followed_recommendation_rate"] is None
    assert summary["self_reported_improvement_rate"] is None
    assert summary["domain"] == "recovery"
    assert summary["window"]["days"] == 7
    assert summary["window"]["start"] == "2026-04-18"
    assert summary["window"]["end"] == "2026-04-24"


# ---------------------------------------------------------------------------
# Token rules
# ---------------------------------------------------------------------------


def test_recent_positive_token_when_four_followed_improved(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        for i in range(4):
            _seed_chain(
                conn,
                suffix=f"p{i}",
                domain="running",
                for_date=AS_OF,
                followed=True,
                improved=True,
            )
        summary = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="running",
        )
    finally:
        conn.close()

    assert summary["followed_improved_count"] == 4
    assert TOKEN_RECENT_POSITIVE in summary["tokens"]
    assert TOKEN_INSUFFICIENT_DENOMINATOR not in summary["tokens"]


def test_recent_negative_token_when_four_followed_no_change(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        for i in range(4):
            _seed_chain(
                conn,
                suffix=f"n{i}",
                domain="recovery",
                for_date=AS_OF,
                followed=True,
                improved=False,
            )
        summary = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="recovery",
        )
    finally:
        conn.close()

    assert summary["followed_no_change_count"] == 4
    assert TOKEN_RECENT_NEGATIVE in summary["tokens"]


def test_mixed_token_when_improvement_rate_in_band(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        for i in range(3):
            _seed_chain(
                conn,
                suffix=f"mp{i}",
                domain="sleep",
                for_date=AS_OF,
                followed=True,
                improved=True,
            )
        for i in range(3):
            _seed_chain(
                conn,
                suffix=f"mn{i}",
                domain="sleep",
                for_date=AS_OF,
                followed=True,
                improved=False,
            )
        summary = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="sleep",
        )
    finally:
        conn.close()

    assert summary["followed_count"] == 6
    assert summary["self_reported_improvement_rate"] == pytest.approx(0.5)
    assert TOKEN_MIXED in summary["tokens"]


def test_insufficient_denominator_below_min(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        for i in range(2):
            _seed_chain(
                conn,
                suffix=f"u{i}",
                domain="stress",
                for_date=AS_OF,
                followed=True,
                improved=True,
            )
        summary = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="stress",
        )
    finally:
        conn.close()

    assert summary["followed_count"] == 2
    assert summary["tokens"] == [TOKEN_INSUFFICIENT_DENOMINATOR]


def test_clean_signal_no_token_emits_empty_list(tmp_path: Path):
    """Denominator met, no extreme — tokens list is empty."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        # 3 followed-improved, 0 followed-no-change → improvement rate 1.0
        # which is OUTSIDE the [0.4, 0.6] mixed band; below positive
        # threshold of 4 so no recent_positive either.
        for i in range(3):
            _seed_chain(
                conn,
                suffix=f"c{i}",
                domain="strength",
                for_date=AS_OF,
                followed=True,
                improved=True,
            )
        summary = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="strength",
        )
    finally:
        conn.close()

    assert summary["followed_count"] == 3
    assert summary["tokens"] == []


# ---------------------------------------------------------------------------
# Window scoping
# ---------------------------------------------------------------------------


def test_window_days_excludes_outcomes_outside_window(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        # In-window (7 days back from 2026-04-24).
        for i in range(2):
            _seed_chain(
                conn,
                suffix=f"in{i}",
                domain="recovery",
                for_date=date(2026, 4, 22),
                followed=True,
                improved=True,
            )
        # Out-of-7d-window but inside 14d (9 days back from 2026-04-24).
        _seed_chain(
            conn,
            suffix="old",
            domain="recovery",
            for_date=date(2026, 4, 15),
            followed=True,
            improved=True,
        )
        summary7 = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="recovery",
            window_days=7,
        )
        summary14 = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="recovery",
            window_days=14,
        )
    finally:
        conn.close()

    assert summary7["recorded_outcome_count"] == 2
    assert summary14["recorded_outcome_count"] == 3


# ---------------------------------------------------------------------------
# Per-domain isolation + aggregate
# ---------------------------------------------------------------------------


def test_domain_filter_does_not_bleed_other_domains(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        for i in range(3):
            _seed_chain(
                conn,
                suffix=f"r{i}",
                domain="recovery",
                for_date=AS_OF,
                followed=True,
                improved=True,
            )
        for i in range(2):
            _seed_chain(
                conn,
                suffix=f"run{i}",
                domain="running",
                for_date=AS_OF,
                followed=True,
                improved=True,
            )
        recovery = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="recovery",
        )
        running = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="running",
        )
    finally:
        conn.close()

    assert recovery["recorded_outcome_count"] == 3
    assert running["recorded_outcome_count"] == 2


def test_aggregate_rolls_up_all_domains(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        for i in range(3):
            _seed_chain(
                conn,
                suffix=f"r{i}",
                domain="recovery",
                for_date=AS_OF,
                followed=True,
                improved=True,
            )
        for i in range(2):
            _seed_chain(
                conn,
                suffix=f"run{i}",
                domain="running",
                for_date=AS_OF,
                followed=True,
                improved=False,
            )
        bundle = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER,
        )
    finally:
        conn.close()

    assert set(bundle.keys()) == {
        "as_of_date", "window_days", "window_start", "window_end",
        "domains", "aggregate",
    }
    assert set(bundle["domains"].keys()) == {
        "recovery", "running", "sleep", "stress", "strength", "nutrition",
    }
    assert bundle["domains"]["recovery"]["recorded_outcome_count"] == 3
    assert bundle["domains"]["running"]["recorded_outcome_count"] == 2
    assert bundle["aggregate"]["recorded_outcome_count"] == 5


# ---------------------------------------------------------------------------
# Re-link counter
# ---------------------------------------------------------------------------


def test_relinked_outcome_count_increments(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _seed_chain(
            conn,
            suffix="rel",
            domain="recovery",
            for_date=AS_OF,
            followed=True,
            improved=True,
            relink_from="rec_original_superseded",
        )
        _seed_chain(
            conn,
            suffix="norel",
            domain="recovery",
            for_date=AS_OF,
            followed=True,
            improved=True,
        )
        summary = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="recovery",
        )
    finally:
        conn.close()

    assert summary["recorded_outcome_count"] == 2
    assert summary["relinked_outcome_count"] == 1


# ---------------------------------------------------------------------------
# Threshold override
# ---------------------------------------------------------------------------


def test_threshold_overrides_change_token_emission(tmp_path: Path):
    """Lowering ``recent_positive_threshold`` to 2 fires the token at 2
    followed-improved outcomes instead of 4."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        for i in range(2):
            _seed_chain(
                conn,
                suffix=f"o{i}",
                domain="recovery",
                for_date=AS_OF,
                followed=True,
                improved=True,
            )

        custom = {
            "policy": {
                "review_summary": {
                    "window_days": 7,
                    "min_denominator": 2,
                    "recent_negative_threshold": 4,
                    "recent_positive_threshold": 2,
                    "mixed_token_lower_bound": 0.4,
                    "mixed_token_upper_bound": 0.6,
                }
            }
        }
        summary = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="recovery",
            thresholds=custom,
        )
    finally:
        conn.close()

    assert TOKEN_RECENT_POSITIVE in summary["tokens"]


# ---------------------------------------------------------------------------
# Intensity-delta distribution
# ---------------------------------------------------------------------------


def test_intensity_delta_distribution_counts_known_labels(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        for i, delta in enumerate(("lighter", "lighter", "same", "harder")):
            _seed_chain(
                conn,
                suffix=f"d{i}_{delta}",
                domain="running",
                for_date=AS_OF,
                followed=True,
                improved=True,
                intensity_delta=delta,
            )
        summary = build_review_summary(
            conn, as_of_date=AS_OF, user_id=USER, domain="running",
        )
    finally:
        conn.close()

    dist = summary["intensity_delta_distribution"]
    assert dist["lighter"] == 2
    assert dist["same"] == 1
    assert dist["harder"] == 1
    assert dist["much_lighter"] == 0
    assert dist["much_harder"] == 0


# ---------------------------------------------------------------------------
# Snapshot integration
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Codex R3-1: runtime threshold resolver rejects bools
# ---------------------------------------------------------------------------


def test_runtime_resolver_rejects_bool_window_days(tmp_path: Path):
    """Codex R3-1 invariant: even when `hai config validate` is
    skipped, the runtime threshold resolver must refuse bool-shaped
    numeric overrides. Validator boundary + runtime boundary are
    defence-in-depth."""

    from health_agent_infra.core.review.summary import (
        ReviewSummaryThresholdError,
        _resolve_thresholds,
    )

    bad = {"policy": {"review_summary": {"window_days": True}}}
    with pytest.raises(ReviewSummaryThresholdError) as exc_info:
        _resolve_thresholds(bad)
    msg = str(exc_info.value)
    assert "window_days" in msg
    assert "bool" in msg
    assert "hai config validate" in msg


def test_runtime_resolver_rejects_bool_threshold(tmp_path: Path):
    from health_agent_infra.core.review.summary import (
        ReviewSummaryThresholdError,
        _resolve_thresholds,
    )

    bad = {
        "policy": {
            "review_summary": {"recent_negative_threshold": False}
        }
    }
    with pytest.raises(ReviewSummaryThresholdError):
        _resolve_thresholds(bad)


def test_runtime_resolver_rejects_bool_mixed_bound(tmp_path: Path):
    from health_agent_infra.core.review.summary import (
        ReviewSummaryThresholdError,
        _resolve_thresholds,
    )

    bad = {
        "policy": {
            "review_summary": {"mixed_token_upper_bound": True}
        }
    }
    with pytest.raises(ReviewSummaryThresholdError):
        _resolve_thresholds(bad)


def test_runtime_resolver_rejects_non_numeric_string(tmp_path: Path):
    """While we're guarding bools, also reject other non-numeric types
    (str, list, dict) that would otherwise reach int()/float() and
    raise an opaque TypeError. Defence-in-depth covers any wrong type."""

    from health_agent_infra.core.review.summary import (
        ReviewSummaryThresholdError,
        _resolve_thresholds,
    )

    bad = {"policy": {"review_summary": {"window_days": "seven"}}}
    with pytest.raises(ReviewSummaryThresholdError):
        _resolve_thresholds(bad)


def test_runtime_resolver_accepts_real_numbers(tmp_path: Path):
    """Sanity check: legitimate int + float values pass through."""

    from health_agent_infra.core.review.summary import _resolve_thresholds

    cfg = {
        "policy": {
            "review_summary": {
                "window_days": 14,
                "min_denominator": 5,
                "recent_negative_threshold": 3,
                "recent_positive_threshold": 3,
                "mixed_token_lower_bound": 0.3,
                "mixed_token_upper_bound": 0.7,
            }
        }
    }
    resolved = _resolve_thresholds(cfg)
    assert resolved["window_days"] == 14
    assert resolved["min_denominator"] == 5
    assert resolved["mixed_token_lower_bound"] == 0.3
    assert resolved["mixed_token_upper_bound"] == 0.7


def test_runtime_resolver_uses_defaults_when_keys_missing(tmp_path: Path):
    """Empty policy block falls back to ship-with defaults; no error."""

    from health_agent_infra.core.review.summary import _resolve_thresholds

    resolved = _resolve_thresholds({"policy": {"review_summary": {}}})
    assert resolved["window_days"] == 7
    assert resolved["min_denominator"] == 3


def test_snapshot_attaches_review_summary_per_domain(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        for i in range(3):
            _seed_chain(
                conn,
                suffix=f"s{i}",
                domain="running",
                for_date=AS_OF,
                followed=True,
                improved=True,
            )
        snap = build_snapshot(
            conn,
            as_of_date=AS_OF,
            user_id=USER,
            now_local=datetime(2026, 4, 24, 23, 45),
        )
    finally:
        conn.close()

    assert snap["schema_version"] == "state_snapshot.v2"
    for domain in ("recovery", "running", "sleep", "stress", "strength", "nutrition"):
        assert "review_summary" in snap[domain]
        assert snap[domain]["review_summary"]["domain"] == domain
    # The 3 running outcomes show up under running, not recovery.
    assert snap["running"]["review_summary"]["recorded_outcome_count"] == 3
    assert snap["recovery"]["review_summary"]["recorded_outcome_count"] == 0
