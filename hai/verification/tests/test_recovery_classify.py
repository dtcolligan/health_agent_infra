"""Tests for domains/recovery/classify.py — band classification + scoring.

Every band boundary tested on both sides. Uncertainty tokens validated.
Config-driven thresholds verified with override-via-argument.
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS
from health_agent_infra.domains.recovery.classify import (
    ClassifiedRecoveryState,
    classify_recovery_state,
)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _full_evidence(**overrides):
    base = {
        "sleep_hours": 8.0,
        "resting_hr": 52.0,
        "hrv_ms": 80.0,
        "soreness_self_report": "low",
    }
    base.update(overrides)
    return base


def _full_raw_summary(**overrides):
    base = {
        "resting_hr_baseline": 52.0,
        "resting_hr_ratio_vs_baseline": 1.0,
        "hrv_ratio_vs_baseline": 1.0,
        "trailing_7d_training_load": 400.0,
        "training_load_baseline": 400.0,
        "training_load_ratio_vs_baseline": 1.0,
        "resting_hr_spike_days": 0,
    }
    base.update(overrides)
    return base


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
])
def test_sleep_debt_band_boundaries(hours, expected):
    result = classify_recovery_state(
        _full_evidence(sleep_hours=hours),
        _full_raw_summary(),
    )
    assert result.sleep_debt_band == expected


def test_sleep_debt_band_missing_adds_uncertainty():
    result = classify_recovery_state(
        _full_evidence(sleep_hours=None),
        _full_raw_summary(),
    )
    assert result.sleep_debt_band == "unknown"
    assert "sleep_record_missing" in result.uncertainty


# ---------------------------------------------------------------------------
# resting_hr_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ratio,expected", [
    (0.90, "below"),
    (0.949, "below"),
    (0.95, "at"),
    (1.049, "at"),
    (1.05, "above"),
    (1.149, "above"),
    (1.15, "well_above"),
    (1.30, "well_above"),
])
def test_resting_hr_band_boundaries(ratio, expected):
    result = classify_recovery_state(
        _full_evidence(),
        _full_raw_summary(resting_hr_ratio_vs_baseline=ratio),
    )
    assert result.resting_hr_band == expected


def test_resting_hr_band_value_missing():
    result = classify_recovery_state(
        _full_evidence(resting_hr=None),
        _full_raw_summary(),
    )
    assert result.resting_hr_band == "unknown"
    assert "resting_hr_record_missing" in result.uncertainty


def test_resting_hr_band_baseline_missing():
    result = classify_recovery_state(
        _full_evidence(),
        _full_raw_summary(
            resting_hr_baseline=None,
            resting_hr_ratio_vs_baseline=None,
        ),
    )
    assert result.resting_hr_band == "unknown"
    assert "baseline_window_too_short" in result.uncertainty


# ---------------------------------------------------------------------------
# hrv_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ratio,expected", [
    (0.80, "below"),
    (0.95, "below"),
    (0.96, "at"),
    (1.019, "at"),
    (1.02, "above"),
    (1.099, "above"),
    (1.10, "well_above"),
    (1.30, "well_above"),
])
def test_hrv_band_boundaries(ratio, expected):
    result = classify_recovery_state(
        _full_evidence(),
        _full_raw_summary(hrv_ratio_vs_baseline=ratio),
    )
    assert result.hrv_band == expected


def test_hrv_band_missing():
    result = classify_recovery_state(
        _full_evidence(hrv_ms=None),
        _full_raw_summary(hrv_ratio_vs_baseline=None),
    )
    assert result.hrv_band == "unknown"
    assert "hrv_unavailable" in result.uncertainty


# ---------------------------------------------------------------------------
# training_load_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ratio,expected", [
    (0.69, "low"),
    (0.70, "moderate"),
    (1.099, "moderate"),
    (1.1, "high"),
    (1.399, "high"),
    (1.4, "spike"),
    (2.0, "spike"),
])
def test_training_load_band_ratio_boundaries(ratio, expected):
    result = classify_recovery_state(
        _full_evidence(),
        _full_raw_summary(training_load_ratio_vs_baseline=ratio),
    )
    assert result.training_load_band == expected


def test_training_load_band_absolute_fallback_high():
    result = classify_recovery_state(
        _full_evidence(),
        _full_raw_summary(
            trailing_7d_training_load=600.0,
            training_load_baseline=None,
            training_load_ratio_vs_baseline=None,
        ),
    )
    assert result.training_load_band == "high"
    assert "training_load_baseline_missing" in result.uncertainty


def test_training_load_band_absolute_fallback_moderate():
    result = classify_recovery_state(
        _full_evidence(),
        _full_raw_summary(
            trailing_7d_training_load=300.0,
            training_load_baseline=None,
            training_load_ratio_vs_baseline=None,
        ),
    )
    assert result.training_load_band == "moderate"


def test_training_load_band_absolute_fallback_low():
    result = classify_recovery_state(
        _full_evidence(),
        _full_raw_summary(
            trailing_7d_training_load=100.0,
            training_load_baseline=None,
            training_load_ratio_vs_baseline=None,
        ),
    )
    assert result.training_load_band == "low"


def test_training_load_band_trailing_missing():
    result = classify_recovery_state(
        _full_evidence(),
        _full_raw_summary(
            trailing_7d_training_load=None,
            training_load_baseline=None,
            training_load_ratio_vs_baseline=None,
        ),
    )
    assert result.training_load_band == "unknown"
    assert "training_load_window_incomplete" in result.uncertainty


# ---------------------------------------------------------------------------
# soreness
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value,expected", [
    ("low", "low"),
    ("moderate", "moderate"),
    ("high", "high"),
    (None, "unknown"),
    ("", "unknown"),
    ("unknown_string", "unknown"),
])
def test_soreness_passthrough_and_missing(value, expected):
    result = classify_recovery_state(
        _full_evidence(soreness_self_report=value),
        _full_raw_summary(),
    )
    assert result.soreness_band == expected
    if expected == "unknown":
        assert "manual_checkin_missing" in result.uncertainty


# ---------------------------------------------------------------------------
# coverage_band
# ---------------------------------------------------------------------------

def test_coverage_full_when_all_signals_present():
    result = classify_recovery_state(_full_evidence(), _full_raw_summary())
    assert result.coverage_band == "full"


def test_coverage_insufficient_when_sleep_missing():
    result = classify_recovery_state(
        _full_evidence(sleep_hours=None),
        _full_raw_summary(),
    )
    assert result.coverage_band == "insufficient"


def test_coverage_insufficient_when_soreness_missing():
    result = classify_recovery_state(
        _full_evidence(soreness_self_report=None),
        _full_raw_summary(),
    )
    assert result.coverage_band == "insufficient"


def test_coverage_sparse_when_training_load_missing():
    result = classify_recovery_state(
        _full_evidence(),
        _full_raw_summary(
            trailing_7d_training_load=None,
            training_load_baseline=None,
            training_load_ratio_vs_baseline=None,
        ),
    )
    assert result.coverage_band == "sparse"


def test_coverage_sparse_when_resting_hr_missing():
    result = classify_recovery_state(
        _full_evidence(resting_hr=None),
        _full_raw_summary(),
    )
    assert result.coverage_band == "sparse"


def test_coverage_partial_when_hrv_missing():
    result = classify_recovery_state(
        _full_evidence(hrv_ms=None),
        _full_raw_summary(hrv_ratio_vs_baseline=None),
    )
    assert result.coverage_band == "partial"


def test_coverage_partial_when_resting_hr_baseline_missing():
    result = classify_recovery_state(
        _full_evidence(),
        _full_raw_summary(
            resting_hr_baseline=None,
            resting_hr_ratio_vs_baseline=None,
        ),
    )
    assert result.coverage_band == "partial"


# ---------------------------------------------------------------------------
# recovery_status
# ---------------------------------------------------------------------------

def test_recovery_status_recovered_on_clean_signals():
    result = classify_recovery_state(_full_evidence(), _full_raw_summary())
    assert result.recovery_status == "recovered"


def test_recovery_status_mildly_impaired_on_one_impaired_signal():
    # sleep=elevated (impaired=1), everything else nominal.
    result = classify_recovery_state(
        _full_evidence(sleep_hours=5.5),
        _full_raw_summary(),
    )
    assert result.recovery_status == "mildly_impaired"


def test_recovery_status_mildly_impaired_on_two_mild_signals():
    # sleep=mild + soreness=moderate → mild=2.
    result = classify_recovery_state(
        _full_evidence(sleep_hours=7.2, soreness_self_report="moderate"),
        _full_raw_summary(),
    )
    assert result.recovery_status == "mildly_impaired"


def test_recovery_status_impaired_on_two_impaired_signals():
    result = classify_recovery_state(
        _full_evidence(sleep_hours=5.5, soreness_self_report="high"),
        _full_raw_summary(),
    )
    assert result.recovery_status == "impaired"


def test_recovery_status_unknown_when_coverage_insufficient():
    result = classify_recovery_state(
        _full_evidence(sleep_hours=None),
        _full_raw_summary(),
    )
    assert result.recovery_status == "unknown"


# ---------------------------------------------------------------------------
# readiness_score
# ---------------------------------------------------------------------------

def test_readiness_score_is_none_when_coverage_insufficient():
    result = classify_recovery_state(
        _full_evidence(sleep_hours=None),
        _full_raw_summary(),
    )
    assert result.readiness_score is None


def test_readiness_score_full_on_clean_signals():
    result = classify_recovery_state(_full_evidence(), _full_raw_summary())
    assert result.readiness_score == 1.0


def test_readiness_score_applies_sleep_moderate_penalty():
    result = classify_recovery_state(
        _full_evidence(sleep_hours=6.5),
        _full_raw_summary(),
    )
    assert result.readiness_score == 0.85  # 1.0 - 0.15


def test_readiness_score_applies_hrv_bonus():
    # hrv=above → -0.05 penalty (i.e. +0.05) but clamped at 1.0.
    result = classify_recovery_state(
        _full_evidence(),
        _full_raw_summary(hrv_ratio_vs_baseline=1.05),
    )
    assert result.readiness_score == 1.0  # already 1.0, bonus clamped


def test_readiness_score_all_penalties_sum_to_correct_value():
    # sleep_debt_elevated (0.25) + soreness_high (0.20) + rhr_well_above (0.20)
    # + hrv_below (0.15) + load_spike (0.15) = 0.95 penalty → score 0.05.
    result = classify_recovery_state(
        _full_evidence(sleep_hours=5.0, soreness_self_report="high"),
        _full_raw_summary(
            resting_hr=70.0,
            resting_hr_ratio_vs_baseline=1.30,
            hrv_ratio_vs_baseline=0.85,
            training_load_ratio_vs_baseline=1.5,
        ),
    )
    assert result.readiness_score == 0.05


def test_readiness_score_clamped_to_zero_when_penalties_exceed_one():
    # Boost each penalty past the default with an override to force clamp.
    override = {
        "classify": {
            "recovery": {
                "sleep_debt_band": DEFAULT_THRESHOLDS["classify"]["recovery"]["sleep_debt_band"],
                "resting_hr_band": DEFAULT_THRESHOLDS["classify"]["recovery"]["resting_hr_band"],
                "hrv_band": DEFAULT_THRESHOLDS["classify"]["recovery"]["hrv_band"],
                "training_load_band": DEFAULT_THRESHOLDS["classify"]["recovery"]["training_load_band"],
                "readiness_score_penalty": {
                    **DEFAULT_THRESHOLDS["classify"]["recovery"]["readiness_score_penalty"],
                    "sleep_debt_elevated": 0.95,  # inflated to drive below zero
                    "soreness_high": 0.95,
                },
            },
        },
        "policy": DEFAULT_THRESHOLDS["policy"],
        "synthesis": DEFAULT_THRESHOLDS["synthesis"],
    }
    result = classify_recovery_state(
        _full_evidence(sleep_hours=5.0, soreness_self_report="high"),
        _full_raw_summary(),
        thresholds=override,
    )
    assert result.readiness_score == 0.0


# ---------------------------------------------------------------------------
# Uncertainty dedup + sort
# ---------------------------------------------------------------------------

def test_uncertainty_is_deduplicated_and_sorted():
    result = classify_recovery_state(
        _full_evidence(sleep_hours=None, hrv_ms=None, resting_hr=None,
                       soreness_self_report=None),
        _full_raw_summary(
            hrv_ratio_vs_baseline=None,
            trailing_7d_training_load=None,
            training_load_baseline=None,
            training_load_ratio_vs_baseline=None,
        ),
    )
    assert list(result.uncertainty) == sorted(set(result.uncertainty))


# ---------------------------------------------------------------------------
# Config-driven behaviour
# ---------------------------------------------------------------------------

def test_threshold_override_shifts_sleep_band():
    override = {
        "classify": {
            "recovery": {
                "sleep_debt_band": {
                    "none_min_hours": 8.0,    # stricter
                    "mild_min_hours": 7.0,
                    "moderate_min_hours": 6.0,
                },
                "resting_hr_band": DEFAULT_THRESHOLDS["classify"]["recovery"]["resting_hr_band"],
                "hrv_band": DEFAULT_THRESHOLDS["classify"]["recovery"]["hrv_band"],
                "training_load_band": DEFAULT_THRESHOLDS["classify"]["recovery"]["training_load_band"],
                "readiness_score_penalty": DEFAULT_THRESHOLDS["classify"]["recovery"]["readiness_score_penalty"],
            },
        },
        "policy": DEFAULT_THRESHOLDS["policy"],
        "synthesis": DEFAULT_THRESHOLDS["synthesis"],
    }
    result = classify_recovery_state(
        _full_evidence(sleep_hours=7.7),
        _full_raw_summary(),
        thresholds=override,
    )
    # 7.7h is "none" at default 7.5 cutoff, "mild" at override 8.0 cutoff.
    assert result.sleep_debt_band == "mild"


# ---------------------------------------------------------------------------
# Frozen dataclass contract
# ---------------------------------------------------------------------------

def test_classified_state_is_frozen():
    result = classify_recovery_state(_full_evidence(), _full_raw_summary())
    with pytest.raises(Exception):
        result.sleep_debt_band = "elevated"
