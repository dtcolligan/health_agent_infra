"""Strength-domain signal derivation.

Phase 4 step 5. Mirrors the sleep / stress / running signals modules:
a single pure function that builds the ``strength_signals`` dict
``classify_strength_state`` + ``evaluate_strength_policy`` consume.

Inputs come from the snapshot's strength block:

  - ``strength_today``: today's ``accepted_resistance_training_state_daily``
    row, or ``None`` if no row.
  - ``strength_history``: trailing rows from the same table excluding
    today, ordered by ``as_of_date`` (oldest-first per snapshot
    convention).
  - ``goal_domain``: optional string — the user's current goal domain
    if any; when ``"resistance_training"`` the classifier lifts the
    ``goal_domain_is_resistance_training`` flag so the skill can lean
    into progression prose.
  - ``heavy_lower_body_min_volume_kg_reps``: threshold a muscle group's
    daily volume must meet to count as "heavy" for
    ``days_since_heavy_by_group``. Config-driven so user TOML can tune.

Output is the dict shape ``classify_strength_state`` already accepts.
Absent inputs become ``None`` / empty-collection entries; the classifier
translates those into ``unknown`` bands and uncertainty tokens.
"""

from __future__ import annotations

import json
from typing import Any, Optional


DEFAULT_HEAVY_VOLUME_THRESHOLD = 2000.0  # kg·reps — a 4×5 set of 100kg
MUSCLE_GROUPS = (
    "quads", "hamstrings", "glutes", "calves",
    "chest", "back", "shoulders", "biceps", "triceps", "core",
)


def derive_strength_signals(
    *,
    strength_today: Optional[dict[str, Any]],
    strength_history: list[dict[str, Any]],
    goal_domain: Optional[str] = None,
    heavy_lower_body_min_volume_kg_reps: float = DEFAULT_HEAVY_VOLUME_THRESHOLD,
) -> dict[str, Any]:
    """Build a ``strength_signals`` dict for classify + policy.

    Keys emitted:

      - ``volume_ratio_7d_vs_28d_week_mean`` — Σ(last 7 days'
        total_volume_kg_reps) / mean-weekly(last 28 days'
        total_volume_kg_reps). ``None`` when the 28-day baseline is
        zero (no history to compare against).
      - ``sessions_last_7d`` — sum of ``session_count`` across today +
        the trailing 6 days.
      - ``sessions_last_28d`` — sum of ``session_count`` across today +
        the trailing 27 days.
      - ``days_since_heavy_by_group`` — dict keyed by the canonical
        muscle-group set (``quads``, ``hamstrings``, …). Value = number
        of days between today and the most recent day whose
        ``volume_by_muscle_group_json[group]`` met the heavy threshold.
        ``0`` = heavy today; ``1`` = yesterday; ``None`` = never in
        the 28-day window.
      - ``today_volume_by_muscle_group`` — parsed today-only per-group
        volume dict, or ``None``.
      - ``estimated_1rm_today`` — parsed today-only 1RM dict, or
        ``None``.
      - ``unmatched_exercise_tokens`` — parsed today-only list of
        unresolved exercise names. Carried through to the classifier
        so the ``unmatched_exercise_tokens_present`` flag lights up.
      - ``goal_domain`` — passed through.
    """

    rows = list(strength_history)
    if strength_today is not None:
        rows = rows + [strength_today]
    # rows is now oldest-first; today is at rows[-1] if present.

    total_28d = _sum_volume(rows[-28:])
    total_7d = _sum_volume(rows[-7:])
    volume_ratio = None
    if total_28d is not None and total_28d > 0:
        volume_ratio = round(total_7d / (total_28d / 4.0), 3) if total_7d is not None else 0.0

    sessions_last_7d = _sum_sessions(rows[-7:])
    sessions_last_28d = _sum_sessions(rows[-28:])

    days_since_heavy = _days_since_heavy_by_group(
        rows=rows,
        heavy_threshold=heavy_lower_body_min_volume_kg_reps,
    )

    today_volume = _parse_json_obj(
        strength_today.get("volume_by_muscle_group_json")
        if strength_today else None
    )
    today_1rm = _parse_json_obj(
        strength_today.get("estimated_1rm_json")
        if strength_today else None
    )
    unmatched = _parse_json_list(
        strength_today.get("unmatched_exercise_tokens_json")
        if strength_today else None
    )

    return {
        "volume_ratio_7d_vs_28d_week_mean": volume_ratio,
        "sessions_last_7d": sessions_last_7d,
        "sessions_last_28d": sessions_last_28d,
        "days_since_heavy_by_group": days_since_heavy,
        "today_volume_by_muscle_group": today_volume,
        "estimated_1rm_today": today_1rm,
        "unmatched_exercise_tokens": unmatched,
        "goal_domain": goal_domain,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sum_volume(rows: list[dict[str, Any]]) -> Optional[float]:
    """Sum ``total_volume_kg_reps`` across rows. Returns None when no
    rows carry a value."""

    total = 0.0
    seen = False
    for row in rows:
        v = row.get("total_volume_kg_reps")
        if v is not None:
            total += float(v)
            seen = True
    return total if seen else None


def _sum_sessions(rows: list[dict[str, Any]]) -> Optional[int]:
    """Sum ``session_count`` across rows. Returns None when no rows
    carry a value (distinguishes 'no history' from 'zero sessions')."""

    total = 0
    seen = False
    for row in rows:
        v = row.get("session_count")
        if v is not None:
            total += int(v)
            seen = True
    return total if seen else None


def _parse_json_obj(value: Any) -> Optional[dict[str, Any]]:
    if not value:
        return None
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else None
    except (TypeError, json.JSONDecodeError):
        return None


def _parse_json_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(v) for v in parsed]
        return []
    except (TypeError, json.JSONDecodeError):
        return []


def _days_since_heavy_by_group(
    *,
    rows: list[dict[str, Any]],
    heavy_threshold: float,
) -> dict[str, Optional[int]]:
    """For each muscle group, return days since the most recent heavy
    day in ``rows``. 0 = heavy today; 1 = yesterday; None = never
    inside the window.

    ``rows`` is oldest-first; today is ``rows[-1]``. We walk it newest-
    first so the first hit per group wins.
    """

    out: dict[str, Optional[int]] = {g: None for g in MUSCLE_GROUPS}
    if not rows:
        return out

    for days_ago, row in enumerate(reversed(rows)):
        vol = _parse_json_obj(row.get("volume_by_muscle_group_json"))
        if not vol:
            continue
        for group in MUSCLE_GROUPS:
            if out[group] is not None:
                continue
            g_vol = vol.get(group)
            if g_vol is not None and float(g_vol) >= heavy_threshold:
                out[group] = days_ago
    return out
