"""Strength-domain state classification — deterministic bands + scoring.

Phase 4 step 3. Mirrors the structure of ``domains.sleep.classify`` and
``domains.running.classify``: a single entry point
``classify_strength_state`` that consumes a ``strength_signals`` dict
and returns a frozen ``ClassifiedStrengthState``. All numerical
decisions live here; the strength-readiness skill (SKILL.md) only
writes prose.

Bands:

- **recent_volume_band** ∈ {very_low, low, moderate, high, very_high,
  unknown} — from ``volume_ratio_7d_vs_28d_week_mean`` = last-7d
  volume / (last-28d volume / 4). Aligned with the running
  weekly_mileage_trend_band so cross-domain prose stays consistent.
- **freshness_band_by_group** — dict keyed by muscle_group →
  {fresh, recent, fatigued, unknown}. Derived from
  ``days_since_heavy_by_group``. "fatigued" ⇒ hit today or yesterday
  (0 days). "recent" ⇒ 1-2 days. "fresh" ⇒ ≥3 days. "unknown" ⇒ no
  recorded heavy session in the window. X4 / X5 in synthesis read
  this directly to cap cross-domain hard sessions.
- **coverage_band** ∈ {insufficient, sparse, partial, full} — from
  ``sessions_last_28d``. Drives the R-coverage gate.
- **strength_status** ∈ {progressing, maintaining, undertrained,
  overreaching, unknown} — composite verdict over every band.
- **strength_score** ∈ [0.0, 1.0] or None — None iff
  ``coverage_band == 'insufficient'``. Lower score = more training
  stress; 1.0 = neutral-fresh.
- **uncertainty**: tuple of dedup'd, sorted reason tokens.

Signal dict keys recognised:

  - ``volume_ratio_7d_vs_28d_week_mean`` (float; ratio of last 7d
    kg·reps to (last 28d kg·reps / 4))
  - ``sessions_last_7d`` (int)
  - ``sessions_last_28d`` (int)
  - ``days_since_heavy_by_group`` (dict[str, Optional[int]])
  - ``unmatched_exercise_tokens`` (list[str]; free-text names that
    did not resolve against the taxonomy)
  - ``today_volume_by_muscle_group`` (dict[str, float]; today-only
    per-group volume, unused by classify but carried through for the
    skill's rationale prose)
  - ``estimated_1rm_today`` (dict[str, dict]; today-only 1RM best
    per resolved exercise_id)
  - ``goal_domain`` (optional str; when == 'resistance_training' the
    classifier flags ``goal_domain_is_resistance_training`` on
    uncertainty so the skill can surface progression tracking)

All keys are optional; absent keys propagate as ``unknown`` bands and
uncertainty tokens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds


RecentVolumeBand = str         # "very_low"|"low"|"moderate"|"high"|"very_high"|"unknown"
FreshnessBand = str            # "fresh"|"recent"|"fatigued"|"unknown"
CoverageBand = str             # "insufficient"|"sparse"|"partial"|"full"
StrengthStatus = str           # "progressing"|"maintaining"|"undertrained"|"overreaching"|"unknown"

# Authoritative enum surface — exposed via capabilities manifest at
# ``hai today`` per W-FCC (PLAN.md §2.9 / F-C-05). Adding a value here
# requires updating the classifier; the manifest contract test
# (``test_capabilities_strength_status_enum_surface``) keeps the
# manifest in sync.
STRENGTH_STATUS_VALUES: tuple[str, ...] = (
    "progressing",
    "maintaining",
    "undertrained",
    "overreaching",
    "unknown",
)


@dataclass(frozen=True)
class ClassifiedStrengthState:
    recent_volume_band: RecentVolumeBand
    freshness_band_by_group: dict[str, FreshnessBand]
    coverage_band: CoverageBand
    strength_status: StrengthStatus
    strength_score: Optional[float]  # None iff coverage=insufficient
    volume_ratio: Optional[float]
    sessions_last_7d: Optional[int]
    sessions_last_28d: Optional[int]
    unmatched_exercise_tokens: tuple[str, ...]
    uncertainty: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Band classifiers
# ---------------------------------------------------------------------------


def _classify_recent_volume(
    ratio: Optional[float], t: dict[str, Any]
) -> tuple[RecentVolumeBand, list[str]]:
    if ratio is None:
        return "unknown", ["volume_baseline_unavailable"]
    cfg = t["classify"]["strength"]["recent_volume_band"]
    if ratio < cfg["very_low_max_ratio"]:
        return "very_low", []
    if ratio < cfg["low_max_ratio"]:
        return "low", []
    if ratio < cfg["moderate_max_ratio"]:
        return "moderate", []
    if ratio < cfg["high_max_ratio"]:
        return "high", []
    return "very_high", []


def _classify_freshness_for_group(
    days_since_heavy: Optional[int], t: dict[str, Any]
) -> FreshnessBand:
    if days_since_heavy is None:
        return "unknown"
    cfg = t["classify"]["strength"]["freshness_band"]
    if days_since_heavy >= cfg["fresh_min_days_since_heavy"]:
        return "fresh"
    if days_since_heavy >= 1 and days_since_heavy <= cfg["recent_max_days_since_heavy"]:
        return "recent"
    # Boundary case: 0 days ⇒ fatigued (heavy session yesterday or today).
    if days_since_heavy <= 0:
        return "fatigued"
    # Fallback — should not be reachable given the above but kept defensive.
    return "fatigued"


def _classify_freshness_by_group(
    days_since_heavy_by_group: Optional[dict[str, Optional[int]]],
    t: dict[str, Any],
) -> tuple[dict[str, FreshnessBand], list[str]]:
    if not days_since_heavy_by_group:
        return {}, ["freshness_by_group_unavailable"]
    out: dict[str, FreshnessBand] = {}
    for group, days in days_since_heavy_by_group.items():
        out[group] = _classify_freshness_for_group(days, t)
    return out, []


def _classify_coverage(
    sessions_last_28d: Optional[int], t: dict[str, Any]
) -> tuple[CoverageBand, list[str]]:
    if sessions_last_28d is None:
        return "insufficient", ["sessions_history_unavailable"]
    cfg = t["classify"]["strength"]["coverage_band"]
    if sessions_last_28d <= cfg["insufficient_max_sessions_28d"]:
        return "insufficient", []
    if sessions_last_28d <= cfg["sparse_max_sessions_28d"]:
        return "sparse", []
    if sessions_last_28d <= cfg["partial_max_sessions_28d"]:
        return "partial", []
    return "full", []


def _strength_status(
    volume: RecentVolumeBand,
    coverage: CoverageBand,
) -> StrengthStatus:
    if coverage == "insufficient":
        return "unknown"
    if volume == "very_high":
        return "overreaching"
    if coverage == "sparse" or volume == "very_low":
        return "undertrained"
    if volume in {"low", "moderate"}:
        return "maintaining"
    if volume == "high":
        return "progressing"
    return "maintaining"


def _strength_score(
    volume: RecentVolumeBand,
    coverage: CoverageBand,
    has_unmatched: bool,
    t: dict[str, Any],
) -> Optional[float]:
    if coverage == "insufficient":
        return None

    penalties = t["classify"]["strength"]["strength_score_penalty"]
    score = 1.0

    if volume == "very_high":
        score -= penalties["recent_volume_very_high"]
    elif volume == "very_low":
        score -= penalties["recent_volume_very_low"]

    if coverage == "sparse":
        score -= penalties["coverage_sparse"]
    elif coverage == "partial":
        score -= penalties["coverage_partial"]

    if has_unmatched:
        score -= penalties["unmatched_exercise_present"]

    return round(max(0.0, min(1.0, score)), 2)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def classify_strength_state(
    strength_signals: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
) -> ClassifiedStrengthState:
    """Classify recent strength training signals into bands, status, score.

    Args:
        strength_signals: dict bundling the strength-domain inputs.
            Recognised keys described in module docstring. All keys
            are optional; absent keys propagate as ``unknown`` bands
            and uncertainty tokens.
        thresholds: optional pre-loaded config dict. If None, loads via
            ``core.config.load_thresholds()``.

    Returns:
        ``ClassifiedStrengthState``. ``uncertainty`` is dedup'd + sorted.
    """

    t = thresholds if thresholds is not None else load_thresholds()
    uncertainty: list[str] = []

    volume_ratio = strength_signals.get("volume_ratio_7d_vs_28d_week_mean")
    volume_band, u = _classify_recent_volume(volume_ratio, t)
    uncertainty.extend(u)

    sessions_last_7d = strength_signals.get("sessions_last_7d")
    sessions_last_28d = strength_signals.get("sessions_last_28d")

    coverage, u = _classify_coverage(sessions_last_28d, t)
    uncertainty.extend(u)

    days_since_heavy = strength_signals.get("days_since_heavy_by_group")
    freshness_by_group, u = _classify_freshness_by_group(days_since_heavy, t)
    uncertainty.extend(u)

    unmatched_list = list(strength_signals.get("unmatched_exercise_tokens") or [])
    has_unmatched = len(unmatched_list) > 0
    if has_unmatched:
        uncertainty.append("unmatched_exercise_tokens_present")

    goal_domain = strength_signals.get("goal_domain")
    if goal_domain == "resistance_training":
        uncertainty.append("goal_domain_is_resistance_training")

    status = _strength_status(volume_band, coverage)
    score = _strength_score(volume_band, coverage, has_unmatched, t)

    return ClassifiedStrengthState(
        recent_volume_band=volume_band,
        freshness_band_by_group=freshness_by_group,
        coverage_band=coverage,
        strength_status=status,
        strength_score=score,
        volume_ratio=volume_ratio,
        sessions_last_7d=sessions_last_7d,
        sessions_last_28d=sessions_last_28d,
        unmatched_exercise_tokens=tuple(sorted(set(unmatched_list))),
        uncertainty=tuple(sorted(set(uncertainty))),
    )
