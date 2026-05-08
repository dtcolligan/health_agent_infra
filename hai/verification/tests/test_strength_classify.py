"""Strength-domain classifier tests (Phase 4 step 3).

Pins:

  1. ``recent_volume_band`` boundary semantics: a value AT the boundary
     lands in the higher band (same convention as running /
     sleep-debt).
  2. ``freshness_band_by_group`` resolves each group independently
     against ``days_since_heavy``: 0 ⇒ fatigued, 1-2 ⇒ recent, ≥3 ⇒
     fresh, None ⇒ unknown.
  3. ``coverage_band`` gates on ``sessions_last_28d`` only; missing
     history → insufficient.
  4. ``strength_status`` composes from volume + coverage; insufficient
     coverage shortcircuits to ``unknown``.
  5. Unmatched-exercise tokens raise the ``unmatched_exercise_tokens_present``
     uncertainty and nudge the score down.
  6. ``goal_domain == 'resistance_training'`` surfaces a
     ``goal_domain_is_resistance_training`` uncertainty so the skill
     can lean into progression prose.
  7. ``strength_score`` is None iff coverage == 'insufficient'.
"""

from __future__ import annotations

from typing import Any

import pytest

from health_agent_infra.domains.strength.classify import (
    ClassifiedStrengthState,
    classify_strength_state,
)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _signals(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "volume_ratio_7d_vs_28d_week_mean": 1.0,
        "sessions_last_7d": 3,
        "sessions_last_28d": 12,
        "days_since_heavy_by_group": {
            "quads": 2,
            "chest": 3,
            "back": 4,
            "hamstrings": 0,
        },
        "unmatched_exercise_tokens": [],
        "today_volume_by_muscle_group": {"quads": 2000.0},
        "estimated_1rm_today": {"back_squat": {"estimated_1rm_kg": 130.0, "reps": 5, "weight_kg": 115.0}},
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# recent_volume_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "ratio, expected",
    [
        (0.3, "very_low"),
        (0.49, "very_low"),
        (0.5, "low"),        # boundary → higher band
        (0.79, "low"),
        (0.8, "moderate"),
        (1.19, "moderate"),
        (1.2, "high"),
        (1.49, "high"),
        (1.5, "very_high"),
        (2.0, "very_high"),
    ],
)
def test_recent_volume_band_boundaries(ratio: float, expected: str):
    state = classify_strength_state(_signals(volume_ratio_7d_vs_28d_week_mean=ratio))
    assert state.recent_volume_band == expected


def test_recent_volume_band_unknown_when_ratio_absent():
    state = classify_strength_state(_signals(volume_ratio_7d_vs_28d_week_mean=None))
    assert state.recent_volume_band == "unknown"
    assert "volume_baseline_unavailable" in state.uncertainty


# ---------------------------------------------------------------------------
# freshness_band_by_group
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "days, expected",
    [
        (0, "fatigued"),
        (1, "recent"),
        (2, "recent"),
        (3, "fresh"),
        (10, "fresh"),
        (None, "unknown"),
    ],
)
def test_freshness_band_per_group(days, expected):
    state = classify_strength_state(_signals(days_since_heavy_by_group={"quads": days}))
    assert state.freshness_band_by_group["quads"] == expected


def test_freshness_resolves_each_group_independently():
    state = classify_strength_state(
        _signals(days_since_heavy_by_group={
            "quads": 0, "hamstrings": 1, "chest": 3, "back": None,
        })
    )
    assert state.freshness_band_by_group == {
        "quads": "fatigued",
        "hamstrings": "recent",
        "chest": "fresh",
        "back": "unknown",
    }


def test_freshness_empty_dict_surfaces_uncertainty_token():
    state = classify_strength_state(_signals(days_since_heavy_by_group={}))
    assert state.freshness_band_by_group == {}
    assert "freshness_by_group_unavailable" in state.uncertainty


def test_freshness_none_surfaces_uncertainty_token():
    state = classify_strength_state(_signals(days_since_heavy_by_group=None))
    assert state.freshness_band_by_group == {}
    assert "freshness_by_group_unavailable" in state.uncertainty


# ---------------------------------------------------------------------------
# coverage_band
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "sessions_28d, expected",
    [
        (0, "insufficient"),
        (1, "insufficient"),
        (2, "insufficient"),
        (3, "sparse"),
        (4, "sparse"),
        (5, "partial"),
        (8, "partial"),
        (9, "full"),
        (20, "full"),
    ],
)
def test_coverage_band_boundaries(sessions_28d: int, expected: str):
    state = classify_strength_state(_signals(sessions_last_28d=sessions_28d))
    assert state.coverage_band == expected


def test_coverage_insufficient_when_sessions_history_absent():
    state = classify_strength_state(_signals(sessions_last_28d=None))
    assert state.coverage_band == "insufficient"
    assert "sessions_history_unavailable" in state.uncertainty


# ---------------------------------------------------------------------------
# strength_status composition
# ---------------------------------------------------------------------------

def test_strength_status_unknown_on_insufficient_coverage():
    state = classify_strength_state(_signals(sessions_last_28d=1))
    assert state.coverage_band == "insufficient"
    assert state.strength_status == "unknown"


def test_strength_status_overreaching_on_very_high_volume():
    state = classify_strength_state(
        _signals(volume_ratio_7d_vs_28d_week_mean=1.8, sessions_last_28d=12)
    )
    assert state.strength_status == "overreaching"


def test_strength_status_undertrained_on_very_low_volume():
    state = classify_strength_state(
        _signals(volume_ratio_7d_vs_28d_week_mean=0.3, sessions_last_28d=12)
    )
    assert state.strength_status == "undertrained"


def test_strength_status_undertrained_on_sparse_coverage_with_moderate_volume():
    state = classify_strength_state(
        _signals(volume_ratio_7d_vs_28d_week_mean=1.0, sessions_last_28d=3)
    )
    assert state.coverage_band == "sparse"
    assert state.strength_status == "undertrained"


def test_strength_status_progressing_on_high_volume_with_full_coverage():
    state = classify_strength_state(
        _signals(volume_ratio_7d_vs_28d_week_mean=1.3, sessions_last_28d=12)
    )
    assert state.strength_status == "progressing"


def test_strength_status_maintaining_on_moderate_volume():
    state = classify_strength_state(
        _signals(volume_ratio_7d_vs_28d_week_mean=1.0, sessions_last_28d=12)
    )
    assert state.strength_status == "maintaining"


# ---------------------------------------------------------------------------
# strength_score
# ---------------------------------------------------------------------------

def test_strength_score_none_on_insufficient_coverage():
    state = classify_strength_state(_signals(sessions_last_28d=1))
    assert state.strength_score is None


def test_strength_score_penalised_on_very_high_volume():
    clean = classify_strength_state(
        _signals(volume_ratio_7d_vs_28d_week_mean=1.0, sessions_last_28d=12)
    )
    spike = classify_strength_state(
        _signals(volume_ratio_7d_vs_28d_week_mean=1.8, sessions_last_28d=12)
    )
    assert spike.strength_score is not None
    assert clean.strength_score is not None
    assert spike.strength_score < clean.strength_score


def test_strength_score_penalised_on_sparse_coverage():
    clean = classify_strength_state(
        _signals(volume_ratio_7d_vs_28d_week_mean=1.0, sessions_last_28d=12)
    )
    sparse = classify_strength_state(
        _signals(volume_ratio_7d_vs_28d_week_mean=1.0, sessions_last_28d=3)
    )
    assert sparse.strength_score < clean.strength_score


def test_strength_score_penalised_on_unmatched_tokens():
    clean = classify_strength_state(_signals(unmatched_exercise_tokens=[]))
    dirty = classify_strength_state(_signals(unmatched_exercise_tokens=["Jefferson Curl"]))
    assert dirty.strength_score < clean.strength_score


def test_strength_score_between_zero_and_one():
    for ratio in [0.1, 0.5, 1.0, 1.3, 2.5]:
        for coverage in [3, 8, 20]:
            state = classify_strength_state(
                _signals(
                    volume_ratio_7d_vs_28d_week_mean=ratio,
                    sessions_last_28d=coverage,
                )
            )
            assert state.strength_score is not None
            assert 0.0 <= state.strength_score <= 1.0


# ---------------------------------------------------------------------------
# Uncertainty tokens
# ---------------------------------------------------------------------------

def test_unmatched_exercise_tokens_surface_uncertainty_flag():
    state = classify_strength_state(_signals(unmatched_exercise_tokens=["Phantom Lift"]))
    assert "unmatched_exercise_tokens_present" in state.uncertainty
    assert state.unmatched_exercise_tokens == ("Phantom Lift",)


def test_unmatched_exercise_tokens_deduped_and_sorted():
    state = classify_strength_state(
        _signals(unmatched_exercise_tokens=["Zebra Row", "Alpha Curl", "Alpha Curl"])
    )
    assert state.unmatched_exercise_tokens == ("Alpha Curl", "Zebra Row")


def test_goal_domain_resistance_training_raises_progression_flag():
    state = classify_strength_state(_signals(goal_domain="resistance_training"))
    assert "goal_domain_is_resistance_training" in state.uncertainty


def test_goal_domain_other_does_not_raise_flag():
    state = classify_strength_state(_signals(goal_domain="endurance"))
    assert "goal_domain_is_resistance_training" not in state.uncertainty


def test_uncertainty_is_sorted_and_deduped():
    state = classify_strength_state(
        _signals(
            volume_ratio_7d_vs_28d_week_mean=None,
            sessions_last_28d=None,
            unmatched_exercise_tokens=["x", "y"],
        )
    )
    assert state.uncertainty == tuple(sorted(state.uncertainty))
    assert len(set(state.uncertainty)) == len(state.uncertainty)


# ---------------------------------------------------------------------------
# Pass-through fields for the skill's rationale layer
# ---------------------------------------------------------------------------

def test_volume_ratio_and_session_counts_passed_through():
    state = classify_strength_state(
        _signals(
            volume_ratio_7d_vs_28d_week_mean=1.0,
            sessions_last_7d=4,
            sessions_last_28d=10,
        )
    )
    assert state.volume_ratio == 1.0
    assert state.sessions_last_7d == 4
    assert state.sessions_last_28d == 10
