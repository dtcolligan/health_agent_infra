"""Tests for ``classify_stress_state`` (Phase 3 step 4).

Covers each band's threshold boundaries (just-above vs just-below the
cutoff, plus exact-on-boundary cases that document which side wins),
missingness propagation, coverage transitions, state verdicts, and
stress-score arithmetic. Locks the contract before step 5 wires stress
into the snapshot + synthesis layers.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS, load_thresholds
from health_agent_infra.domains.stress.classify import (
    ClassifiedStressState,
    classify_stress_state,
)


def _signals(**overrides) -> dict:
    base = dict(
        garmin_all_day_stress=25,
        manual_stress_score=2,
        body_battery_end_of_day=70,
        body_battery_prev_day=65,
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Default thresholds wiring
# ---------------------------------------------------------------------------

def test_default_thresholds_carry_stress_classify_section():
    t = load_thresholds()
    assert "stress" in t["classify"]
    for key in (
        "garmin_stress_band",
        "manual_stress_band",
        "body_battery_trend_band",
        "stress_score_penalty",
    ):
        assert key in t["classify"]["stress"], (
            f"missing classify.stress.{key} in DEFAULT_THRESHOLDS"
        )


def test_default_thresholds_carry_stress_policy_section():
    t = load_thresholds()
    assert "stress" in t["policy"]
    assert "r_sustained_stress_days" in t["policy"]["stress"]
    assert "r_sustained_stress_min_score" in t["policy"]["stress"]


def test_garmin_stress_thresholds_align_with_x7_for_rewire():
    """Plan §2.2 X7 fires off a categorical stress band. The stress
    classifier will own this band after the Phase-3-step-5 rewire; its
    boundaries must match the existing synthesis.x_rules.x7 numeric
    thresholds so the rewire is mechanical."""

    t = load_thresholds()
    classify = t["classify"]["stress"]["garmin_stress_band"]
    x7 = t["synthesis"]["x_rules"]["x7"]
    assert classify["moderate_min_score"] == x7["moderate_min_score"]
    assert classify["high_min_score"] == x7["high_min_score"]
    assert classify["very_high_min_score"] == x7["very_high_min_score"]


# ---------------------------------------------------------------------------
# garmin_stress_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score,expected", [
    (0, "low"),
    (39, "low"),
    (40, "moderate"),
    (59, "moderate"),
    (60, "high"),
    (79, "high"),
    (80, "very_high"),
    (100, "very_high"),
])
def test_garmin_stress_band_boundaries(score, expected):
    result = classify_stress_state(_signals(garmin_all_day_stress=score))
    assert result.garmin_stress_band == expected


def test_garmin_stress_unknown_when_missing():
    result = classify_stress_state(_signals(garmin_all_day_stress=None))
    assert result.garmin_stress_band == "unknown"
    assert "garmin_all_day_stress_unavailable" in result.uncertainty


# ---------------------------------------------------------------------------
# manual_stress_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score,expected", [
    (1, "low"),
    (2, "low"),
    (3, "moderate"),
    (4, "high"),
    (5, "very_high"),
])
def test_manual_stress_band_boundaries(score, expected):
    result = classify_stress_state(_signals(manual_stress_score=score))
    assert result.manual_stress_band == expected


def test_manual_stress_unknown_when_missing():
    result = classify_stress_state(_signals(manual_stress_score=None))
    assert result.manual_stress_band == "unknown"
    assert "manual_stress_score_unavailable" in result.uncertainty


# ---------------------------------------------------------------------------
# body_battery_trend_band
# ---------------------------------------------------------------------------

def test_body_battery_depleted_fires_on_absolute_low_regardless_of_delta():
    result = classify_stress_state(
        _signals(body_battery_end_of_day=18, body_battery_prev_day=10)
    )
    assert result.body_battery_trend_band == "depleted"


def test_body_battery_depleted_fires_at_exact_threshold():
    result = classify_stress_state(
        _signals(body_battery_end_of_day=20, body_battery_prev_day=18)
    )
    assert result.body_battery_trend_band == "depleted"


@pytest.mark.parametrize("today,prev,expected", [
    (50, 70, "declining"),
    (50, 60, "declining"),
    (50, 59, "steady"),
    (50, 50, "steady"),
    (50, 41, "steady"),
    (50, 40, "steady"),
    (50, 39, "improving"),
    (80, 50, "improving"),
])
def test_body_battery_trend_delta_boundaries(today, prev, expected):
    result = classify_stress_state(
        _signals(body_battery_end_of_day=today, body_battery_prev_day=prev)
    )
    assert result.body_battery_trend_band == expected


def test_body_battery_trend_unknown_when_today_missing():
    result = classify_stress_state(_signals(body_battery_end_of_day=None))
    assert result.body_battery_trend_band == "unknown"
    assert "body_battery_unavailable" in result.uncertainty


def test_body_battery_trend_unknown_when_prev_day_missing_and_not_depleted():
    result = classify_stress_state(
        _signals(body_battery_end_of_day=70, body_battery_prev_day=None)
    )
    assert result.body_battery_trend_band == "unknown"
    assert "body_battery_prev_day_unavailable" in result.uncertainty


def test_body_battery_trend_depleted_overrides_missing_prev_day():
    """Depleted is an absolute condition — prev-day missingness must
    not veto it, otherwise critical depletion could be misread as
    'unknown' on the first day of data."""

    result = classify_stress_state(
        _signals(body_battery_end_of_day=15, body_battery_prev_day=None)
    )
    assert result.body_battery_trend_band == "depleted"


def test_body_battery_delta_surfaced_on_classified_state():
    result = classify_stress_state(
        _signals(body_battery_end_of_day=70, body_battery_prev_day=65)
    )
    assert result.body_battery_delta == 5


def test_body_battery_delta_none_when_either_side_missing():
    result = classify_stress_state(
        _signals(body_battery_end_of_day=70, body_battery_prev_day=None)
    )
    assert result.body_battery_delta is None


# ---------------------------------------------------------------------------
# coverage_band
# ---------------------------------------------------------------------------

def test_coverage_full_when_all_three_present():
    result = classify_stress_state(_signals())
    assert result.coverage_band == "full"


def test_coverage_insufficient_when_no_stress_signal():
    result = classify_stress_state(
        _signals(garmin_all_day_stress=None, manual_stress_score=None)
    )
    assert result.coverage_band == "insufficient"


def test_coverage_insufficient_even_with_body_battery_only():
    """Body battery alone is an indirect proxy and cannot anchor the
    recommendation — matches sleep's R1 spirit."""

    result = classify_stress_state(
        _signals(
            garmin_all_day_stress=None,
            manual_stress_score=None,
            body_battery_end_of_day=80,
            body_battery_prev_day=60,
        )
    )
    assert result.coverage_band == "insufficient"


def test_coverage_sparse_when_only_garmin_and_no_body_battery():
    result = classify_stress_state(
        _signals(
            manual_stress_score=None,
            body_battery_end_of_day=None,
            body_battery_prev_day=None,
        )
    )
    assert result.coverage_band == "sparse"


def test_coverage_sparse_when_only_manual_and_no_body_battery():
    result = classify_stress_state(
        _signals(
            garmin_all_day_stress=None,
            body_battery_end_of_day=None,
            body_battery_prev_day=None,
        )
    )
    assert result.coverage_band == "sparse"


def test_coverage_partial_when_garmin_plus_bb_no_manual():
    result = classify_stress_state(
        _signals(manual_stress_score=None)
    )
    assert result.coverage_band == "partial"


def test_coverage_partial_when_garmin_and_manual_no_bb():
    result = classify_stress_state(
        _signals(body_battery_end_of_day=None, body_battery_prev_day=None)
    )
    assert result.coverage_band == "partial"


# ---------------------------------------------------------------------------
# stress_state composite verdict
# ---------------------------------------------------------------------------

def test_stress_state_unknown_on_insufficient_coverage():
    result = classify_stress_state(
        _signals(garmin_all_day_stress=None, manual_stress_score=None)
    )
    assert result.stress_state == "unknown"


def test_stress_state_calm_when_all_bands_favourable():
    """Garmin low + manual low + body_battery improving → calm."""

    result = classify_stress_state(
        _signals(
            garmin_all_day_stress=20,
            manual_stress_score=1,
            body_battery_end_of_day=80,
            body_battery_prev_day=50,  # improving
        )
    )
    assert result.stress_state == "calm"


def test_stress_state_overloaded_on_very_high_garmin():
    result = classify_stress_state(_signals(garmin_all_day_stress=85))
    assert result.stress_state == "overloaded"


def test_stress_state_overloaded_on_depleted_body_battery():
    result = classify_stress_state(
        _signals(
            body_battery_end_of_day=15,
            body_battery_prev_day=25,
        )
    )
    assert result.stress_state == "overloaded"


def test_stress_state_elevated_on_high_garmin_plus_moderate_manual():
    result = classify_stress_state(
        _signals(garmin_all_day_stress=65, manual_stress_score=3)
    )
    assert result.stress_state == "elevated"


def test_stress_state_manageable_on_lone_moderate():
    result = classify_stress_state(
        _signals(garmin_all_day_stress=45, manual_stress_score=2)
    )
    # One moderate band, no elevated signals → manageable (not calm).
    assert result.stress_state == "manageable"


# ---------------------------------------------------------------------------
# stress_score arithmetic
# ---------------------------------------------------------------------------

def test_stress_score_is_none_when_coverage_insufficient():
    result = classify_stress_state(
        _signals(garmin_all_day_stress=None, manual_stress_score=None)
    )
    assert result.stress_score is None


def test_stress_score_full_on_clean_low_signals():
    result = classify_stress_state(
        _signals(
            garmin_all_day_stress=20,
            manual_stress_score=1,
            body_battery_end_of_day=80,
            body_battery_prev_day=50,  # improving → bonus
        )
    )
    # 1.0 - 0 - 0 - (-0.05) = 1.05, clamped to 1.0.
    assert result.stress_score == 1.0


def test_stress_score_penalised_on_very_high_garmin():
    result = classify_stress_state(
        _signals(
            garmin_all_day_stress=85,
            manual_stress_score=1,
            body_battery_end_of_day=60,
            body_battery_prev_day=55,  # steady
        )
    )
    # 1.0 - 0.30 (garmin very_high) = 0.70.
    assert result.stress_score == 0.70


def test_stress_score_clamped_on_stacked_penalties():
    result = classify_stress_state(
        _signals(
            garmin_all_day_stress=85,
            manual_stress_score=5,
            body_battery_end_of_day=15,
            body_battery_prev_day=30,
        )
    )
    # Stacked: 0.30 + 0.25 + 0.20 = 0.75 deducted → 0.25.
    assert result.stress_score == 0.25


# ---------------------------------------------------------------------------
# Thresholds come from config, not hard-coded
# ---------------------------------------------------------------------------

def test_thresholds_override_via_explicit_dict():
    t = {
        "classify": {
            "stress": {
                "garmin_stress_band": {
                    "moderate_min_score": 10,
                    "high_min_score": 20,
                    "very_high_min_score": 30,
                },
                "manual_stress_band": {
                    "moderate_min_score": 3,
                    "high_min_score": 4,
                    "very_high_min_score": 5,
                },
                "body_battery_trend_band": {
                    "depleted_max_bb": 20,
                    "declining_max_delta": -10,
                    "steady_max_delta": 10,
                },
                "stress_score_penalty": {
                    "garmin_moderate": 0.10,
                    "garmin_high": 0.20,
                    "garmin_very_high": 0.30,
                    "manual_moderate": 0.05,
                    "manual_high": 0.15,
                    "manual_very_high": 0.25,
                    "body_battery_declining": 0.10,
                    "body_battery_depleted": 0.20,
                    "body_battery_improving": -0.05,
                },
            },
        },
    }
    # With override, a score of 30 lands in very_high.
    result = classify_stress_state(_signals(garmin_all_day_stress=30), thresholds=t)
    assert result.garmin_stress_band == "very_high"


# ---------------------------------------------------------------------------
# Uncertainty surface
# ---------------------------------------------------------------------------

def test_uncertainty_is_sorted_and_deduped():
    result = classify_stress_state(
        _signals(
            garmin_all_day_stress=None,
            manual_stress_score=None,
            body_battery_end_of_day=None,
        )
    )
    assert list(result.uncertainty) == sorted(set(result.uncertainty))
    # All three missingness tokens should appear.
    assert "garmin_all_day_stress_unavailable" in result.uncertainty
    assert "manual_stress_score_unavailable" in result.uncertainty
    assert "body_battery_unavailable" in result.uncertainty
