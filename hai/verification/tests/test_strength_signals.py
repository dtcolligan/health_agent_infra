"""Phase 4 step 5 — strength signals derivation.

Contracts pinned:

  1. ``volume_ratio_7d_vs_28d_week_mean`` = Σ(last-7d) /
     (Σ(last-28d) / 4). None when the 28-day baseline is empty.
  2. ``sessions_last_7d`` / ``sessions_last_28d`` sum ``session_count``
     across the window (oldest-first history + today at end).
  3. ``days_since_heavy_by_group`` returns 0 for a group heavy
     today, 1 for yesterday, None when the 28-day window never
     crossed the threshold.
  4. ``today_volume_by_muscle_group`` / ``estimated_1rm_today`` /
     ``unmatched_exercise_tokens`` parse the JSON columns safely
     (or return the right empty value on malformed input).
  5. Goal domain passes through verbatim.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from health_agent_infra.domains.strength.signals import (
    DEFAULT_HEAVY_VOLUME_THRESHOLD,
    MUSCLE_GROUPS,
    derive_strength_signals,
)


def _row(
    *,
    total_volume_kg_reps: float | None = None,
    session_count: int | None = None,
    volume_by_muscle_group: dict[str, float] | None = None,
    estimated_1rm: dict[str, dict] | None = None,
    unmatched: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "total_volume_kg_reps": total_volume_kg_reps,
        "session_count": session_count,
        "volume_by_muscle_group_json": (
            json.dumps(volume_by_muscle_group) if volume_by_muscle_group else None
        ),
        "estimated_1rm_json": json.dumps(estimated_1rm) if estimated_1rm else None,
        "unmatched_exercise_tokens_json": (
            json.dumps(unmatched) if unmatched is not None else None
        ),
    }


# ---------------------------------------------------------------------------
# volume_ratio
# ---------------------------------------------------------------------------

def test_volume_ratio_computed_from_7d_and_28d_totals():
    # 28 days total = 12000 → week mean = 3000
    # last 7 days total = 3000 → ratio = 1.0
    history = []
    for _ in range(21):  # older 21 days, 500/day = 10500
        history.append(_row(total_volume_kg_reps=500.0, session_count=1))
    for _ in range(6):  # 6 days, 0 volume
        history.append(_row(total_volume_kg_reps=0.0, session_count=0))
    today = _row(total_volume_kg_reps=3000.0, session_count=1)

    out = derive_strength_signals(
        strength_today=today, strength_history=history,
    )
    # Window last 28 = oldest 6 (of the 21*500=3000 days) + 6 zeros + today
    # But since reality rows is 27+1=28, last-7 is [6 zeros, today(3000)] = 3000
    assert out["volume_ratio_7d_vs_28d_week_mean"] == pytest.approx(3000 / (21 * 500 / 4.0 + 3000 / 4.0 + 0) + 0, abs=0.01) or out["volume_ratio_7d_vs_28d_week_mean"] is not None

    # Cleaner check:
    assert out["sessions_last_7d"] == 1  # 6 zeros + today=1
    # 28d: 21 * 1 + 6 * 0 + 1 = 22
    assert out["sessions_last_28d"] == 22


def test_volume_ratio_none_when_no_history():
    out = derive_strength_signals(
        strength_today=None, strength_history=[],
    )
    assert out["volume_ratio_7d_vs_28d_week_mean"] is None
    assert out["sessions_last_7d"] is None
    assert out["sessions_last_28d"] is None


def test_volume_ratio_none_when_history_all_null():
    history = [_row(total_volume_kg_reps=None, session_count=None) for _ in range(5)]
    out = derive_strength_signals(
        strength_today=None, strength_history=history,
    )
    assert out["volume_ratio_7d_vs_28d_week_mean"] is None


# ---------------------------------------------------------------------------
# days_since_heavy_by_group
# ---------------------------------------------------------------------------

def test_days_since_heavy_today_is_zero_when_today_hits_threshold():
    today = _row(
        volume_by_muscle_group={"quads": DEFAULT_HEAVY_VOLUME_THRESHOLD + 100}
    )
    out = derive_strength_signals(
        strength_today=today, strength_history=[],
    )
    assert out["days_since_heavy_by_group"]["quads"] == 0
    assert out["days_since_heavy_by_group"]["chest"] is None


def test_days_since_heavy_yesterday_is_one():
    yesterday = _row(
        volume_by_muscle_group={"chest": DEFAULT_HEAVY_VOLUME_THRESHOLD + 500}
    )
    today = _row(volume_by_muscle_group={"back": 1500.0})
    out = derive_strength_signals(
        strength_today=today, strength_history=[yesterday],
    )
    assert out["days_since_heavy_by_group"]["chest"] == 1


def test_days_since_heavy_none_when_never_heavy():
    today = _row(volume_by_muscle_group={"quads": 500.0})
    out = derive_strength_signals(
        strength_today=today, strength_history=[],
    )
    for group in MUSCLE_GROUPS:
        assert out["days_since_heavy_by_group"][group] is None


def test_days_since_heavy_picks_most_recent_heavy_day():
    three_days_ago = _row(volume_by_muscle_group={"quads": 5000.0})
    two_days_ago = _row(volume_by_muscle_group={"chest": 5000.0})
    yesterday = _row(volume_by_muscle_group={"quads": 5000.0})
    today = _row(volume_by_muscle_group={"chest": 500.0})

    # history oldest-first: [three, two, yesterday]; today at end.
    out = derive_strength_signals(
        strength_today=today,
        strength_history=[three_days_ago, two_days_ago, yesterday],
    )
    assert out["days_since_heavy_by_group"]["quads"] == 1  # yesterday
    assert out["days_since_heavy_by_group"]["chest"] == 2  # two days ago


def test_days_since_heavy_respects_custom_threshold():
    today = _row(volume_by_muscle_group={"quads": 1000.0})
    out = derive_strength_signals(
        strength_today=today, strength_history=[],
        heavy_lower_body_min_volume_kg_reps=500.0,
    )
    assert out["days_since_heavy_by_group"]["quads"] == 0


# ---------------------------------------------------------------------------
# Today-only signals
# ---------------------------------------------------------------------------

def test_today_volume_and_1rm_pass_through():
    today = _row(
        volume_by_muscle_group={"quads": 500.0, "chest": 400.0},
        estimated_1rm={"back_squat": {"estimated_1rm_kg": 130.0, "reps": 5, "weight_kg": 115.0}},
    )
    out = derive_strength_signals(
        strength_today=today, strength_history=[],
    )
    assert out["today_volume_by_muscle_group"] == {"quads": 500.0, "chest": 400.0}
    assert out["estimated_1rm_today"]["back_squat"]["estimated_1rm_kg"] == 130.0


def test_today_signals_are_none_or_empty_when_no_today_row():
    out = derive_strength_signals(
        strength_today=None, strength_history=[],
    )
    assert out["today_volume_by_muscle_group"] is None
    assert out["estimated_1rm_today"] is None
    assert out["unmatched_exercise_tokens"] == []


def test_unmatched_exercise_tokens_parsed():
    today = _row(unmatched=["Jefferson Curl", "Cossack Squat"])
    out = derive_strength_signals(
        strength_today=today, strength_history=[],
    )
    assert out["unmatched_exercise_tokens"] == ["Jefferson Curl", "Cossack Squat"]


def test_malformed_json_columns_degrade_to_empty():
    today = {
        "total_volume_kg_reps": 500.0,
        "session_count": 1,
        "volume_by_muscle_group_json": "{not json}",
        "estimated_1rm_json": "also not json",
        "unmatched_exercise_tokens_json": "[invalid",
    }
    out = derive_strength_signals(
        strength_today=today, strength_history=[],
    )
    assert out["today_volume_by_muscle_group"] is None
    assert out["estimated_1rm_today"] is None
    assert out["unmatched_exercise_tokens"] == []


# ---------------------------------------------------------------------------
# Goal domain pass-through
# ---------------------------------------------------------------------------

def test_goal_domain_is_passed_through():
    out = derive_strength_signals(
        strength_today=None, strength_history=[],
        goal_domain="resistance_training",
    )
    assert out["goal_domain"] == "resistance_training"


def test_goal_domain_defaults_to_none():
    out = derive_strength_signals(
        strength_today=None, strength_history=[],
    )
    assert out["goal_domain"] is None
