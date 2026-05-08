"""Stress-domain state classification — deterministic bands + scoring.

Phase 3 step 4. Mirrors the structure of ``domains.recovery.classify``,
``domains.running.classify``, and ``domains.sleep.classify``: a single
entry point ``classify_stress_state`` that consumes a ``stress_signals``
dict and returns a frozen ``ClassifiedStressState``. All numerical
decisions live here; the stress-regulation skill (SKILL.md) only writes
prose.

Bands:

- **garmin_stress_band** ∈ {low, moderate, high, very_high, unknown} —
  from Garmin's 0-100 ``garmin_all_day_stress``. Thresholds mirror the
  ``synthesis.x_rules.x7`` values so the Phase-3-step-5 X7 rewire can
  read this band directly without re-thresholding.
- **manual_stress_band** ∈ {low, moderate, high, very_high, unknown} —
  from the user's subjective 1-5 ``manual_stress_score``.
- **body_battery_trend_band** ∈ {improving, steady, declining, depleted,
  unknown} — from today's ``body_battery_end_of_day`` plus the previous
  day's ``body_battery_prev_day``. "depleted" fires on absolute body
  battery at or below ``depleted_max_bb`` regardless of delta.
- **coverage_band** ∈ {full, partial, sparse, insufficient}.
- **stress_state** ∈ {calm, manageable, elevated, overloaded, unknown} —
  composite verdict over every band.
- **stress_score** ∈ [0.0, 1.0] or None — None iff coverage=insufficient.
- **uncertainty**: tuple of dedup'd, sorted reason tokens.

Signal dict keys recognised:

  - ``garmin_all_day_stress`` (int, 0-100)
  - ``manual_stress_score`` (int, 1-5)
  - ``body_battery_end_of_day`` (int, 0-100)
  - ``body_battery_prev_day`` (int, 0-100; previous night's end-of-day)
  - ``stress_history_garmin_last_7`` (list of Optional[int]; the 7 days
    ending today — used by policy's R-sustained rule, carried on the
    classifier output for rationale via uncertainty tokens)

All keys are optional; absent keys propagate as ``unknown`` bands and
uncertainty tokens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds


GarminStressBand = str          # "low" | "moderate" | "high" | "very_high" | "unknown"
ManualStressBand = str          # "low" | "moderate" | "high" | "very_high" | "unknown"
BodyBatteryTrendBand = str      # "improving" | "steady" | "declining" | "depleted" | "unknown"
CoverageBand = str              # "full" | "partial" | "sparse" | "insufficient"
StressState = str               # "calm" | "manageable" | "elevated" | "overloaded" | "unknown"


@dataclass(frozen=True)
class ClassifiedStressState:
    garmin_stress_band: GarminStressBand
    manual_stress_band: ManualStressBand
    body_battery_trend_band: BodyBatteryTrendBand
    coverage_band: CoverageBand
    stress_state: StressState
    stress_score: Optional[float]  # None iff coverage=insufficient
    body_battery_delta: Optional[int]  # surfaced for rationale / audit
    uncertainty: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Band classifiers
# ---------------------------------------------------------------------------

def _classify_garmin_stress(
    score: Optional[int], t: dict[str, Any]
) -> tuple[GarminStressBand, list[str]]:
    if score is None:
        return "unknown", ["garmin_all_day_stress_unavailable"]
    cfg = t["classify"]["stress"]["garmin_stress_band"]
    if score >= cfg["very_high_min_score"]:
        return "very_high", []
    if score >= cfg["high_min_score"]:
        return "high", []
    if score >= cfg["moderate_min_score"]:
        return "moderate", []
    return "low", []


def _classify_manual_stress(
    score: Optional[int], t: dict[str, Any]
) -> tuple[ManualStressBand, list[str]]:
    if score is None:
        return "unknown", ["manual_stress_score_unavailable"]
    cfg = t["classify"]["stress"]["manual_stress_band"]
    if score >= cfg["very_high_min_score"]:
        return "very_high", []
    if score >= cfg["high_min_score"]:
        return "high", []
    if score >= cfg["moderate_min_score"]:
        return "moderate", []
    return "low", []


def _compute_body_battery_delta(
    today_bb: Optional[int], prev_bb: Optional[int]
) -> Optional[int]:
    if today_bb is None or prev_bb is None:
        return None
    return int(today_bb - prev_bb)


def _classify_body_battery_trend(
    today_bb: Optional[int],
    delta: Optional[int],
    t: dict[str, Any],
) -> tuple[BodyBatteryTrendBand, list[str]]:
    cfg = t["classify"]["stress"]["body_battery_trend_band"]
    tokens: list[str] = []

    if today_bb is None:
        tokens.append("body_battery_unavailable")
        return "unknown", tokens

    # "depleted" fires on absolute low body-battery regardless of delta.
    if today_bb <= cfg["depleted_max_bb"]:
        return "depleted", tokens

    if delta is None:
        tokens.append("body_battery_prev_day_unavailable")
        return "unknown", tokens

    if delta <= cfg["declining_max_delta"]:
        return "declining", tokens
    if delta > cfg["steady_max_delta"]:
        return "improving", tokens
    return "steady", tokens


def _classify_coverage(
    garmin_present: bool,
    manual_present: bool,
    body_battery_present: bool,
) -> CoverageBand:
    # Insufficient: no stress signal at all — no Garmin, no manual score.
    # Body battery alone is an indirect stress proxy and cannot anchor a
    # recommendation on its own, same spirit as sleep's R1 coverage gate.
    if not garmin_present and not manual_present:
        return "insufficient"
    # Sparse: exactly one of {garmin, manual} present AND no body_battery.
    if (garmin_present ^ manual_present) and not body_battery_present:
        return "sparse"
    # Partial: either (one of garmin/manual present + body_battery) OR
    # (both garmin+manual present but no body_battery).
    if (garmin_present and manual_present) and not body_battery_present:
        return "partial"
    if (garmin_present ^ manual_present) and body_battery_present:
        return "partial"
    # Full: garmin + manual + body_battery all present.
    return "full"


def _stress_state(
    garmin: GarminStressBand,
    manual: ManualStressBand,
    bb_trend: BodyBatteryTrendBand,
    coverage: CoverageBand,
) -> StressState:
    if coverage == "insufficient":
        return "unknown"
    overloaded_signals = sum([
        garmin == "very_high",
        manual == "very_high",
        bb_trend == "depleted",
    ])
    elevated_signals = sum([
        garmin == "high",
        manual == "high",
        bb_trend == "declining",
    ])
    mild_signals = sum([
        garmin == "moderate",
        manual == "moderate",
    ])
    favourable_signals = sum([
        garmin == "low",
        manual == "low",
        bb_trend == "improving",
    ])
    if overloaded_signals >= 1:
        return "overloaded"
    if elevated_signals >= 2 or (elevated_signals >= 1 and mild_signals >= 1):
        return "elevated"
    if elevated_signals >= 1 or mild_signals >= 2:
        return "manageable"
    if favourable_signals >= 2 and mild_signals == 0 and elevated_signals == 0:
        return "calm"
    return "manageable"


def _stress_score(
    garmin: GarminStressBand,
    manual: ManualStressBand,
    bb_trend: BodyBatteryTrendBand,
    coverage: CoverageBand,
    t: dict[str, Any],
) -> Optional[float]:
    if coverage == "insufficient":
        return None

    penalties = t["classify"]["stress"]["stress_score_penalty"]
    score = 1.0

    if garmin == "moderate":
        score -= penalties["garmin_moderate"]
    elif garmin == "high":
        score -= penalties["garmin_high"]
    elif garmin == "very_high":
        score -= penalties["garmin_very_high"]

    if manual == "moderate":
        score -= penalties["manual_moderate"]
    elif manual == "high":
        score -= penalties["manual_high"]
    elif manual == "very_high":
        score -= penalties["manual_very_high"]

    if bb_trend == "declining":
        score -= penalties["body_battery_declining"]
    elif bb_trend == "depleted":
        score -= penalties["body_battery_depleted"]
    elif bb_trend == "improving":
        score -= penalties["body_battery_improving"]  # negative → bonus

    return round(max(0.0, min(1.0, score)), 2)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def classify_stress_state(
    stress_signals: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
) -> ClassifiedStressState:
    """Classify today's stress signals into bands, state, and score.

    Args:
        stress_signals: dict bundling the stress-domain inputs. Recognised
            keys: ``garmin_all_day_stress``, ``manual_stress_score``,
            ``body_battery_end_of_day``, ``body_battery_prev_day``. All
            keys are optional; absent keys propagate as ``unknown`` bands
            and uncertainty tokens.
        thresholds: optional pre-loaded config dict. If None, loads via
            ``core.config.load_thresholds()``.

    Returns:
        ``ClassifiedStressState``. ``uncertainty`` is dedup'd + sorted.
    """

    t = thresholds if thresholds is not None else load_thresholds()
    uncertainty: list[str] = []

    garmin_score = stress_signals.get("garmin_all_day_stress")
    garmin_band, u = _classify_garmin_stress(garmin_score, t)
    uncertainty.extend(u)

    manual_score = stress_signals.get("manual_stress_score")
    manual_band, u = _classify_manual_stress(manual_score, t)
    uncertainty.extend(u)

    today_bb = stress_signals.get("body_battery_end_of_day")
    prev_bb = stress_signals.get("body_battery_prev_day")
    bb_delta = _compute_body_battery_delta(today_bb, prev_bb)
    bb_trend, u = _classify_body_battery_trend(today_bb, bb_delta, t)
    uncertainty.extend(u)

    coverage = _classify_coverage(
        garmin_present=(garmin_score is not None),
        manual_present=(manual_score is not None),
        body_battery_present=(today_bb is not None),
    )

    state = _stress_state(garmin_band, manual_band, bb_trend, coverage)
    score = _stress_score(garmin_band, manual_band, bb_trend, coverage, t)

    return ClassifiedStressState(
        garmin_stress_band=garmin_band,
        manual_stress_band=manual_band,
        body_battery_trend_band=bb_trend,
        coverage_band=coverage,
        stress_state=state,
        stress_score=score,
        body_battery_delta=bb_delta,
        uncertainty=tuple(sorted(set(uncertainty))),
    )
