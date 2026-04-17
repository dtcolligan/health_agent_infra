"""Tests for ``classify_running_state`` (Phase 2 step 2).

Covers each band's threshold boundaries (just-above vs just-below the cutoff,
plus exact-on-boundary cases that document which side wins), missingness
propagation, coverage transitions, status verdicts, and readiness-score
arithmetic. Locks the contract before snapshot wiring (step 3) and the
synthesis layer (step 4) start consuming this output.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS, load_thresholds
from health_agent_infra.domains.running.classify import (
    ClassifiedRunningState,
    classify_running_state,
)


def _signals(**overrides) -> dict:
    base = dict(
        weekly_mileage_m=50_000.0,
        weekly_mileage_baseline_m=50_000.0,
        recent_hard_session_count_7d=1,
        acwr_ratio=1.0,
        training_readiness_pct=70,
        sleep_debt_band="none",
        resting_hr_band="at",
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Default thresholds wiring
# ---------------------------------------------------------------------------

def test_default_thresholds_carry_running_classify_section():
    t = load_thresholds()
    assert "running" in t["classify"]
    for key in (
        "weekly_mileage_trend_band",
        "hard_session_load_band",
        "freshness_band",
        "recovery_adjacent_band",
        "readiness_score_penalty",
    ):
        assert key in t["classify"]["running"], (
            f"missing classify.running.{key} in DEFAULT_THRESHOLDS"
        )


def test_default_thresholds_carry_running_policy_section():
    t = load_thresholds()
    assert "running" in t["policy"]
    assert "r_acwr_spike_min_ratio" in t["policy"]["running"]


# ---------------------------------------------------------------------------
# weekly_mileage_trend_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "ratio,expected",
    [
        (0.0, "very_low"),
        (0.49, "very_low"),
        (0.5, "low"),       # boundary: lower-bound inclusive in next band
        (0.79, "low"),
        (0.8, "moderate"),
        (1.0, "moderate"),
        (1.19, "moderate"),
        (1.2, "high"),
        (1.49, "high"),
        (1.5, "very_high"),
        (3.0, "very_high"),
    ],
)
def test_weekly_mileage_trend_band_boundaries(ratio, expected):
    sig = _signals(weekly_mileage_ratio=ratio)
    # Ratio override path bypasses the m + baseline_m calc.
    assert classify_running_state(sig).weekly_mileage_trend_band == expected


def test_weekly_mileage_trend_unknown_when_baseline_missing():
    sig = _signals(weekly_mileage_baseline_m=None, weekly_mileage_ratio=None)
    c = classify_running_state(sig)
    assert c.weekly_mileage_trend_band == "unknown"
    assert "weekly_mileage_baseline_unavailable" in c.uncertainty


def test_weekly_mileage_trend_unknown_when_baseline_zero():
    sig = _signals(weekly_mileage_baseline_m=0.0, weekly_mileage_ratio=None)
    assert classify_running_state(sig).weekly_mileage_trend_band == "unknown"


def test_weekly_mileage_ratio_explicit_overrides_m_and_baseline():
    """The pre-computed ratio wins so callers can pass ratios derived from
    distance + a richer history without round-tripping through floats."""

    sig = _signals(
        weekly_mileage_m=10_000.0,
        weekly_mileage_baseline_m=10_000.0,  # implied ratio = 1.0
        weekly_mileage_ratio=1.4,            # explicit override → "high"
    )
    assert classify_running_state(sig).weekly_mileage_trend_band == "high"


# ---------------------------------------------------------------------------
# hard_session_load_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "count,expected",
    [
        (0, "none"),
        (1, "light"),
        (2, "moderate"),
        (3, "heavy"),
        (5, "heavy"),
    ],
)
def test_hard_session_load_band_boundaries(count, expected):
    sig = _signals(recent_hard_session_count_7d=count)
    assert classify_running_state(sig).hard_session_load_band == expected


def test_hard_session_load_unknown_when_count_missing():
    sig = _signals(recent_hard_session_count_7d=None)
    c = classify_running_state(sig)
    assert c.hard_session_load_band == "unknown"
    assert "hard_session_history_unavailable" in c.uncertainty


# ---------------------------------------------------------------------------
# freshness_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "acwr,expected",
    [
        (0.0, "fresh"),
        (0.79, "fresh"),
        (0.8, "neutral"),    # lower-bound inclusive in next band
        (1.0, "neutral"),
        (1.29, "neutral"),
        (1.3, "fatigued"),
        (1.49, "fatigued"),
        (1.5, "overreaching"),
        (3.0, "overreaching"),
    ],
)
def test_freshness_band_boundaries(acwr, expected):
    sig = _signals(acwr_ratio=acwr)
    assert classify_running_state(sig).freshness_band == expected


def test_freshness_unknown_when_acwr_missing():
    sig = _signals(acwr_ratio=None)
    c = classify_running_state(sig)
    assert c.freshness_band == "unknown"
    assert "acwr_unavailable" in c.uncertainty


def test_freshness_overreaching_aligns_with_x3b_threshold():
    """Plan §2.2 X3b: ACWR ≥ 1.5 → escalate. Locking the boundary here
    so a config drift breaks classify before it breaks synthesis."""

    sig = _signals(acwr_ratio=1.5)
    assert classify_running_state(sig).freshness_band == "overreaching"


def test_freshness_fatigued_aligns_with_x3a_band():
    """Plan §2.2 X3a: 1.3 ≤ ACWR < 1.5 → soften."""

    assert classify_running_state(_signals(acwr_ratio=1.3)).freshness_band == "fatigued"
    assert classify_running_state(_signals(acwr_ratio=1.49)).freshness_band == "fatigued"


# ---------------------------------------------------------------------------
# recovery_adjacent_band
# ---------------------------------------------------------------------------

def test_recovery_adjacent_favourable_requires_two_signals():
    sig = _signals(
        training_readiness_pct=80,  # ≥70 → favourable signal
        sleep_debt_band="none",     # → favourable signal
        resting_hr_band="above",    # neutral
    )
    assert classify_running_state(sig).recovery_adjacent_band == "favourable"


def test_recovery_adjacent_neutral_when_only_one_favourable_signal():
    sig = _signals(
        training_readiness_pct=80,  # favourable
        sleep_debt_band="mild",     # not favourable, not compromised
        resting_hr_band="above",    # neutral
    )
    assert classify_running_state(sig).recovery_adjacent_band == "neutral"


def test_recovery_adjacent_compromised_on_low_training_readiness():
    sig = _signals(
        training_readiness_pct=30,  # <40 → compromised
        sleep_debt_band="none",
        resting_hr_band="at",
    )
    assert classify_running_state(sig).recovery_adjacent_band == "compromised"


def test_recovery_adjacent_compromised_on_elevated_sleep_debt():
    sig = _signals(sleep_debt_band="elevated", training_readiness_pct=80)
    assert classify_running_state(sig).recovery_adjacent_band == "compromised"


def test_recovery_adjacent_compromised_on_well_above_rhr():
    sig = _signals(resting_hr_band="well_above", training_readiness_pct=80)
    assert classify_running_state(sig).recovery_adjacent_band == "compromised"


def test_recovery_adjacent_unknown_when_all_signals_missing():
    sig = _signals(
        training_readiness_pct=None,
        sleep_debt_band=None,
        resting_hr_band=None,
    )
    c = classify_running_state(sig)
    assert c.recovery_adjacent_band == "unknown"
    assert "recovery_adjacent_signals_unavailable" in c.uncertainty


def test_recovery_adjacent_treats_unknown_string_as_absent():
    """``unknown`` band tokens (from the recovery classifier) count the
    same as missing for the purpose of the compromised/favourable tally."""

    sig = _signals(
        training_readiness_pct=None,
        sleep_debt_band="unknown",
        resting_hr_band="unknown",
    )
    c = classify_running_state(sig)
    assert c.recovery_adjacent_band == "unknown"


# ---------------------------------------------------------------------------
# coverage_band
# ---------------------------------------------------------------------------

def test_coverage_full_when_all_signals_present():
    assert classify_running_state(_signals()).coverage_band == "full"


def test_coverage_insufficient_when_weekly_mileage_missing():
    sig = _signals(
        weekly_mileage_m=None, weekly_mileage_ratio=None,
    )
    assert classify_running_state(sig).coverage_band == "insufficient"


def test_coverage_insufficient_when_baseline_missing():
    sig = _signals(
        weekly_mileage_baseline_m=None, weekly_mileage_ratio=None,
    )
    assert classify_running_state(sig).coverage_band == "insufficient"


def test_coverage_sparse_when_acwr_missing():
    sig = _signals(acwr_ratio=None)
    assert classify_running_state(sig).coverage_band == "sparse"


def test_coverage_partial_when_hard_session_count_missing():
    sig = _signals(recent_hard_session_count_7d=None)
    assert classify_running_state(sig).coverage_band == "partial"


def test_coverage_partial_when_recovery_adjacent_signals_missing():
    sig = _signals(
        training_readiness_pct=None,
        sleep_debt_band=None,
        resting_hr_band=None,
    )
    assert classify_running_state(sig).coverage_band == "partial"


def test_explicit_ratio_satisfies_mileage_coverage_without_m_or_baseline():
    """A pre-computed ratio is sufficient to clear the mileage coverage gate
    even if the underlying m + baseline_m aren't supplied."""

    sig = _signals(
        weekly_mileage_m=None,
        weekly_mileage_baseline_m=None,
        weekly_mileage_ratio=1.0,
    )
    assert classify_running_state(sig).coverage_band != "insufficient"


# ---------------------------------------------------------------------------
# running_readiness_status
# ---------------------------------------------------------------------------

def test_status_unknown_when_coverage_insufficient():
    sig = _signals(weekly_mileage_baseline_m=None, weekly_mileage_ratio=None)
    assert classify_running_state(sig).running_readiness_status == "unknown"


def test_status_hold_on_overreaching_freshness():
    sig = _signals(acwr_ratio=1.6)
    assert classify_running_state(sig).running_readiness_status == "hold"


def test_status_hold_on_compromised_recovery_with_high_mileage_trend():
    sig = _signals(
        training_readiness_pct=30,
        weekly_mileage_ratio=1.3,  # high band
    )
    assert classify_running_state(sig).running_readiness_status == "hold"


def test_status_ready_on_clean_signals():
    sig = _signals(
        acwr_ratio=1.0, training_readiness_pct=80, sleep_debt_band="none",
        recent_hard_session_count_7d=1,
    )
    assert classify_running_state(sig).running_readiness_status == "ready"


def test_status_conditional_when_hard_session_load_heavy_but_otherwise_ok():
    """Heavy session load downgrades to conditional even with clean recovery."""

    sig = _signals(
        acwr_ratio=1.0, training_readiness_pct=80, sleep_debt_band="none",
        recent_hard_session_count_7d=4,
    )
    assert classify_running_state(sig).running_readiness_status == "conditional"


def test_status_conditional_on_fatigued_freshness_clean_recovery():
    """Fatigued is not yet hold-worthy on its own — synthesis can still
    propose downgrade. Status reports conditional."""

    sig = _signals(acwr_ratio=1.4)
    assert classify_running_state(sig).running_readiness_status == "conditional"


# ---------------------------------------------------------------------------
# readiness_score
# ---------------------------------------------------------------------------

def test_readiness_score_none_when_coverage_insufficient():
    sig = _signals(weekly_mileage_baseline_m=None, weekly_mileage_ratio=None)
    assert classify_running_state(sig).readiness_score is None


def test_readiness_score_clean_signals_at_or_near_one():
    sig = _signals()
    score = classify_running_state(sig).readiness_score
    assert score is not None
    assert 0.95 <= score <= 1.0


def test_readiness_score_overreaching_drops_significantly():
    sig = _signals(acwr_ratio=1.6)
    score = classify_running_state(sig).readiness_score
    assert score is not None
    assert score <= 0.75


def test_readiness_score_clamps_to_zero_floor():
    """Stack every penalty; result must clamp to >=0.0."""

    sig = _signals(
        weekly_mileage_ratio=2.0,   # very_high → 0.15
        recent_hard_session_count_7d=5,  # heavy → 0.15
        acwr_ratio=1.6,             # overreaching → 0.30
        training_readiness_pct=10,  # compromised → 0.20
    )
    score = classify_running_state(sig).readiness_score
    assert score is not None
    assert 0.0 <= score <= 1.0


def test_readiness_score_rounds_to_two_decimals():
    sig = _signals(weekly_mileage_ratio=1.3)  # high → 0.05 penalty
    score = classify_running_state(sig).readiness_score
    assert score is not None
    # No more than 2 decimal digits.
    assert round(score, 2) == score


# ---------------------------------------------------------------------------
# uncertainty propagation
# ---------------------------------------------------------------------------

def test_uncertainty_dedupes_and_sorts():
    sig = _signals(
        weekly_mileage_baseline_m=None,
        weekly_mileage_ratio=None,
        acwr_ratio=None,
        recent_hard_session_count_7d=None,
        training_readiness_pct=None,
        sleep_debt_band=None,
        resting_hr_band=None,
    )
    tokens = classify_running_state(sig).uncertainty
    assert tokens == tuple(sorted(set(tokens)))
    assert "weekly_mileage_baseline_unavailable" in tokens
    assert "acwr_unavailable" in tokens
    assert "hard_session_history_unavailable" in tokens
    assert "recovery_adjacent_signals_unavailable" in tokens


def test_uncertainty_empty_on_full_coverage():
    assert classify_running_state(_signals()).uncertainty == ()


# ---------------------------------------------------------------------------
# Threshold override path
# ---------------------------------------------------------------------------

def test_classify_accepts_explicit_thresholds_dict():
    """Passing a thresholds dict bypasses load_thresholds(); a tweaked
    config takes effect immediately."""

    custom = {**DEFAULT_THRESHOLDS}
    custom["classify"] = {
        **DEFAULT_THRESHOLDS["classify"],
        "running": {
            **DEFAULT_THRESHOLDS["classify"]["running"],
            "freshness_band": {
                "fresh_max_ratio": 0.5,    # narrower fresh band
                "neutral_max_ratio": 1.1,  # narrower neutral band → 1.2 falls into fatigued
                "fatigued_max_ratio": 1.3,
            },
        },
    }
    sig = _signals(acwr_ratio=1.2)
    # Default thresholds → 1.2 < 1.3, so neutral.
    assert classify_running_state(sig).freshness_band == "neutral"
    # Custom thresholds → 1.1 ≤ 1.2 < 1.3, so fatigued.
    assert classify_running_state(sig, thresholds=custom).freshness_band == "fatigued"


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

def test_classifier_returns_frozen_dataclass():
    c = classify_running_state(_signals())
    assert isinstance(c, ClassifiedRunningState)
    with pytest.raises(Exception):
        c.coverage_band = "sparse"  # type: ignore[misc]
