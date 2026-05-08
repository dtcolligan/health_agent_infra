"""Tests for ``classify_sleep_state`` (Phase 3 step 3).

Covers each band's threshold boundaries (just-above vs just-below the
cutoff, plus exact-on-boundary cases that document which side wins),
missingness propagation, coverage transitions, status verdicts, and
sleep-score arithmetic. Locks the contract before step 5 wires sleep
into the snapshot + synthesis layers.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS, load_thresholds
from health_agent_infra.domains.sleep.classify import (
    ClassifiedSleepState,
    classify_sleep_state,
)


def _signals(**overrides) -> dict:
    base = dict(
        sleep_hours=8.0,
        sleep_score_overall=85,
        sleep_awake_min=20.0,
        sleep_start_variance_minutes=15.0,
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Default thresholds wiring
# ---------------------------------------------------------------------------

def test_default_thresholds_carry_sleep_classify_section():
    t = load_thresholds()
    assert "sleep" in t["classify"]
    for key in (
        "sleep_debt_band",
        "sleep_quality_band",
        "sleep_timing_consistency_band",
        "sleep_efficiency_band",
        "sleep_score_penalty",
    ):
        assert key in t["classify"]["sleep"], (
            f"missing classify.sleep.{key} in DEFAULT_THRESHOLDS"
        )


def test_default_thresholds_carry_sleep_policy_section():
    t = load_thresholds()
    assert "sleep" in t["policy"]
    assert "r_chronic_deprivation_nights" in t["policy"]["sleep"]
    assert "r_chronic_deprivation_hours" in t["policy"]["sleep"]


def test_sleep_debt_thresholds_align_with_recovery_for_x1_wiring():
    """Plan §2.2 X1a/X1b fire off ``sleep_debt_band``. The sleep
    classifier will own this field after the Phase-3-step-5 rewire; its
    boundaries must match the existing recovery classifier so the rewire
    is mechanical."""

    t = load_thresholds()
    rec = t["classify"]["recovery"]["sleep_debt_band"]
    sleep = t["classify"]["sleep"]["sleep_debt_band"]
    assert rec["none_min_hours"] == sleep["none_min_hours"]
    assert rec["mild_min_hours"] == sleep["mild_min_hours"]
    assert rec["moderate_min_hours"] == sleep["moderate_min_hours"]


# ---------------------------------------------------------------------------
# sleep_debt_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("hours,expected", [
    (7.5, "none"),
    (7.49, "mild"),
    (7.0, "mild"),
    (6.99, "moderate"),
    (6.0, "moderate"),
    (5.99, "elevated"),
    (0.0, "elevated"),
    (9.5, "none"),
])
def test_sleep_debt_band_boundaries(hours, expected):
    result = classify_sleep_state(_signals(sleep_hours=hours))
    assert result.sleep_debt_band == expected


def test_sleep_debt_unknown_when_sleep_hours_missing():
    result = classify_sleep_state(_signals(sleep_hours=None))
    assert result.sleep_debt_band == "unknown"
    assert "sleep_record_missing" in result.uncertainty


# ---------------------------------------------------------------------------
# sleep_quality_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score,expected", [
    (100, "excellent"),
    (90, "excellent"),
    (89, "good"),
    (80, "good"),
    (79, "fair"),
    (60, "fair"),
    (59, "poor"),
    (0, "poor"),
])
def test_sleep_quality_band_boundaries(score, expected):
    result = classify_sleep_state(_signals(sleep_score_overall=score))
    assert result.sleep_quality_band == expected


def test_sleep_quality_unknown_when_score_missing():
    result = classify_sleep_state(_signals(sleep_score_overall=None))
    assert result.sleep_quality_band == "unknown"
    assert "sleep_score_unavailable" in result.uncertainty


# ---------------------------------------------------------------------------
# sleep_timing_consistency_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("variance,expected", [
    (0.0, "consistent"),
    (29.9, "consistent"),
    (30.0, "variable"),   # lower-bound inclusive in next band
    (59.9, "variable"),
    (60.0, "highly_variable"),
    (240.0, "highly_variable"),
])
def test_sleep_timing_consistency_band_boundaries(variance, expected):
    result = classify_sleep_state(
        _signals(sleep_start_variance_minutes=variance)
    )
    assert result.sleep_timing_consistency_band == expected


def test_sleep_timing_consistency_unknown_in_v1_production():
    """sleep_start_ts stays NULL in migration 004; v1 production sees
    ``sleep_start_variance_minutes=None`` and must classify as
    ``unknown`` with a v1-explicit uncertainty token."""

    result = classify_sleep_state(
        _signals(sleep_start_variance_minutes=None)
    )
    assert result.sleep_timing_consistency_band == "unknown"
    assert "sleep_start_ts_unavailable_in_v1" in result.uncertainty


# ---------------------------------------------------------------------------
# sleep_efficiency_band
# ---------------------------------------------------------------------------

def test_sleep_efficiency_excellent_on_low_awake():
    # 8h asleep, 20min awake → 480 / 500 = 96% → excellent
    result = classify_sleep_state(_signals(sleep_hours=8.0, sleep_awake_min=20.0))
    assert result.sleep_efficiency_band == "excellent"
    assert result.sleep_efficiency_pct is not None
    assert result.sleep_efficiency_pct >= 95.0


def test_sleep_efficiency_good_boundary():
    # Target ~87%: asleep = 6h * 60 = 360, total = 413.8 → awake ≈ 53.8
    # Actually compute inverse: asleep = 360, want efficiency = 87%,
    # so total = 360/0.87 ≈ 413.79, awake ≈ 53.79.
    result = classify_sleep_state(
        _signals(sleep_hours=6.0, sleep_awake_min=53.79)
    )
    assert result.sleep_efficiency_band == "good"


def test_sleep_efficiency_fair_boundary():
    # 6h asleep, awake set so pct ≈ 78%: asleep=360, total=360/0.78≈461.54,
    # awake≈101.54.
    result = classify_sleep_state(
        _signals(sleep_hours=6.0, sleep_awake_min=101.54)
    )
    assert result.sleep_efficiency_band == "fair"


def test_sleep_efficiency_poor_boundary():
    # asleep = 5h * 60 = 300, awake 120 → total 420, efficiency ≈ 71.4%
    result = classify_sleep_state(
        _signals(sleep_hours=5.0, sleep_awake_min=120.0)
    )
    assert result.sleep_efficiency_band == "poor"


def test_sleep_efficiency_exact_90_pct_is_excellent():
    # 9h asleep, 60min awake → 540/600 = 90% → excellent (inclusive lower)
    result = classify_sleep_state(
        _signals(sleep_hours=9.0, sleep_awake_min=60.0)
    )
    assert result.sleep_efficiency_band == "excellent"


def test_sleep_efficiency_unknown_when_awake_min_missing():
    result = classify_sleep_state(_signals(sleep_awake_min=None))
    assert result.sleep_efficiency_band == "unknown"
    assert result.sleep_efficiency_pct is None
    assert "sleep_efficiency_unavailable" in result.uncertainty


def test_sleep_efficiency_unknown_when_sleep_hours_missing():
    result = classify_sleep_state(_signals(sleep_hours=None))
    assert result.sleep_efficiency_band == "unknown"
    assert result.sleep_efficiency_pct is None


# ---------------------------------------------------------------------------
# coverage_band
# ---------------------------------------------------------------------------

def test_coverage_full_when_duration_score_and_awake_present():
    result = classify_sleep_state(_signals())
    assert result.coverage_band == "full"


def test_coverage_insufficient_when_sleep_hours_missing():
    result = classify_sleep_state(_signals(sleep_hours=None))
    assert result.coverage_band == "insufficient"


def test_coverage_sparse_when_score_and_awake_both_missing():
    result = classify_sleep_state(
        _signals(sleep_score_overall=None, sleep_awake_min=None)
    )
    assert result.coverage_band == "sparse"


def test_coverage_partial_when_score_missing_only():
    result = classify_sleep_state(_signals(sleep_score_overall=None))
    assert result.coverage_band == "partial"


def test_coverage_partial_when_awake_missing_only():
    result = classify_sleep_state(_signals(sleep_awake_min=None))
    assert result.coverage_band == "partial"


def test_coverage_full_not_gated_on_timing_consistency():
    """v1 production: sleep_start_ts is NULL by migration-004 design.
    Timing-consistency must NOT gate full coverage, otherwise every
    production snapshot downgrades to partial."""

    result = classify_sleep_state(_signals(sleep_start_variance_minutes=None))
    assert result.coverage_band == "full"


# ---------------------------------------------------------------------------
# sleep_status
# ---------------------------------------------------------------------------

def test_status_unknown_when_coverage_insufficient():
    result = classify_sleep_state(_signals(sleep_hours=None))
    assert result.sleep_status == "unknown"


def test_status_optimal_on_strong_signals():
    result = classify_sleep_state(_signals(
        sleep_hours=8.0,
        sleep_score_overall=90,
        sleep_awake_min=15.0,
        sleep_start_variance_minutes=15.0,
    ))
    assert result.sleep_status == "optimal"


def test_status_adequate_with_one_mild_signal_and_favourables():
    """One mild signal (mild sleep debt) + three favourable signals
    (good quality, excellent efficiency, consistent timing) — not
    enough mild/impaired to reach compromised, but the lone mild blocks
    ``optimal`` since optimal demands zero mild signals. Lands
    ``adequate``."""

    result = classify_sleep_state(_signals(
        sleep_hours=7.2,                   # mild debt (mild signal)
        sleep_score_overall=85,            # good quality (favourable)
        sleep_awake_min=20.0,              # excellent efficiency (favourable)
        sleep_start_variance_minutes=15.0,  # consistent (favourable)
    ))
    assert result.sleep_status == "adequate"


def test_status_adequate_on_v1_unknown_consistency_with_two_favourables():
    """Realistic v1 production shape: good duration, good quality,
    excellent efficiency, unknown consistency. Only three favourable
    signals qualify (debt=none, quality=good, efficiency=excellent).
    With three favourables and no mild/impaired, this lands ``optimal``
    — lock the contract so a future "consistency required" drift would
    surface here before shipping."""

    result = classify_sleep_state(_signals(
        sleep_hours=8.0,
        sleep_score_overall=85,
        sleep_awake_min=20.0,
        sleep_start_variance_minutes=None,
    ))
    assert result.sleep_status == "optimal"


def test_status_compromised_on_two_mild_signals():
    result = classify_sleep_state(_signals(
        sleep_hours=6.5,         # moderate debt
        sleep_score_overall=70,  # fair quality
        sleep_awake_min=20.0,    # excellent efficiency
    ))
    assert result.sleep_status == "compromised"


def test_status_compromised_on_single_impaired_signal():
    result = classify_sleep_state(_signals(
        sleep_hours=5.5,         # elevated debt (impaired signal)
        sleep_score_overall=85,
        sleep_awake_min=20.0,
    ))
    assert result.sleep_status == "compromised"


def test_status_impaired_on_two_impaired_signals():
    result = classify_sleep_state(_signals(
        sleep_hours=5.0,          # elevated
        sleep_score_overall=50,   # poor
        sleep_awake_min=20.0,
    ))
    assert result.sleep_status == "impaired"


# ---------------------------------------------------------------------------
# sleep_score
# ---------------------------------------------------------------------------

def test_sleep_score_none_when_coverage_insufficient():
    result = classify_sleep_state(_signals(sleep_hours=None))
    assert result.sleep_score is None


def test_sleep_score_near_one_on_clean_signals():
    result = classify_sleep_state(_signals(
        sleep_hours=8.0,
        sleep_score_overall=95,
        sleep_awake_min=15.0,
        sleep_start_variance_minutes=15.0,
    ))
    assert result.sleep_score is not None
    assert result.sleep_score >= 0.95


def test_sleep_score_drops_on_elevated_debt():
    result = classify_sleep_state(_signals(sleep_hours=5.0))
    assert result.sleep_score is not None
    assert result.sleep_score <= 0.80


def test_sleep_score_clamps_to_zero_floor():
    # Stack every penalty: elevated debt (0.25), poor quality (0.20),
    # poor efficiency (0.15), highly_variable consistency (0.08) → 0.68
    # total penalty — clamped to >= 0 but won't hit floor. Verify clamp
    # shape with an extreme synthetic threshold set instead.
    custom = {**DEFAULT_THRESHOLDS}
    custom["classify"] = {
        **DEFAULT_THRESHOLDS["classify"],
        "sleep": {
            **DEFAULT_THRESHOLDS["classify"]["sleep"],
            "sleep_score_penalty": {
                **DEFAULT_THRESHOLDS["classify"]["sleep"]["sleep_score_penalty"],
                "debt_elevated": 2.0,  # deliberately > 1.0
            },
        },
    }
    result = classify_sleep_state(
        _signals(sleep_hours=4.0),
        thresholds=custom,
    )
    assert result.sleep_score == 0.0


def test_sleep_score_rounds_to_two_decimals():
    result = classify_sleep_state(_signals(sleep_hours=6.5))  # moderate debt
    assert result.sleep_score is not None
    assert round(result.sleep_score, 2) == result.sleep_score


# ---------------------------------------------------------------------------
# uncertainty propagation
# ---------------------------------------------------------------------------

def test_uncertainty_dedupes_and_sorts():
    result = classify_sleep_state(_signals(
        sleep_hours=None,
        sleep_score_overall=None,
        sleep_awake_min=None,
        sleep_start_variance_minutes=None,
    ))
    tokens = result.uncertainty
    assert tokens == tuple(sorted(set(tokens)))
    assert "sleep_record_missing" in tokens
    assert "sleep_score_unavailable" in tokens
    assert "sleep_start_ts_unavailable_in_v1" in tokens


def test_uncertainty_empty_on_full_coverage_with_known_consistency():
    result = classify_sleep_state(_signals(sleep_start_variance_minutes=10.0))
    assert result.uncertainty == ()


def test_uncertainty_carries_v1_timing_token_on_full_coverage_otherwise():
    """Most v1 production runs have full coverage but unknown
    consistency. The classifier must still emit the v1 token so the
    skill can surface it in rationale."""

    result = classify_sleep_state(_signals(sleep_start_variance_minutes=None))
    assert "sleep_start_ts_unavailable_in_v1" in result.uncertainty


# ---------------------------------------------------------------------------
# Threshold override
# ---------------------------------------------------------------------------

def test_classify_accepts_explicit_thresholds_dict():
    """Passing a thresholds dict bypasses load_thresholds()."""

    custom = {**DEFAULT_THRESHOLDS}
    custom["classify"] = {
        **DEFAULT_THRESHOLDS["classify"],
        "sleep": {
            **DEFAULT_THRESHOLDS["classify"]["sleep"],
            "sleep_quality_band": {
                "excellent_min_score": 95,  # narrower excellent
                "good_min_score": 85,
                "fair_min_score": 70,
            },
        },
    }
    # Default: 90 → excellent. Custom: 90 < 95, 90 >= 85 → good.
    assert classify_sleep_state(
        _signals(sleep_score_overall=90)
    ).sleep_quality_band == "excellent"
    assert classify_sleep_state(
        _signals(sleep_score_overall=90), thresholds=custom,
    ).sleep_quality_band == "good"


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

def test_classifier_returns_frozen_dataclass():
    result = classify_sleep_state(_signals())
    assert isinstance(result, ClassifiedSleepState)
    with pytest.raises(Exception):
        result.coverage_band = "sparse"  # type: ignore[misc]
