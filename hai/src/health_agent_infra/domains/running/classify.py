"""Running-domain state classification — deterministic bands + scoring.

Phase 2 step 2. Mirrors the structure of
``health_agent_infra.domains.recovery.classify``: a single entry point,
``classify_running_state``, that consumes a ``running_signals`` dict and
returns a frozen ``ClassifiedRunningState``. All numerical decisions live
here; the running-readiness skill (step 3) only writes prose.

Bands:

- **weekly_mileage_trend_band** ∈ {very_low, low, moderate, high, very_high, unknown}
  — from ``weekly_mileage_ratio`` (current 7d / trailing 28d-week-mean
  baseline).
- **hard_session_load_band** ∈ {none, light, moderate, heavy, unknown}
  — from ``recent_hard_session_count_7d``.
- **freshness_band** ∈ {fresh, neutral, fatigued, overreaching, unknown}
  — from ``acwr_ratio``. Aligned with X3a (1.3-1.5 → fatigued/soften)
  and X3b (≥1.5 → overreaching/block) so synthesis can read the band
  directly without re-classifying.
- **recovery_adjacent_band** ∈ {favourable, neutral, compromised, unknown}
  — composite over recovery signals (training_readiness_pct,
  sleep_debt_band, resting_hr_band). Lets the running domain consume a
  one-token recovery signal without depending on the full recovery
  classify result.
- **coverage_band** ∈ {full, partial, sparse, insufficient} — same
  contract as recovery: ``insufficient`` blocks via the R-coverage gate,
  ``sparse`` caps confidence via the R-sparse rule.
- **running_readiness_status** ∈ {ready, conditional, hold, unknown}
  — composite verdict over freshness + recovery_adjacent + coverage.
- **readiness_score** ∈ [0.0, 1.0] or None — None iff coverage=insufficient.
- **uncertainty**: tuple of dedup'd, sorted reason tokens.

Inputs are always pre-computed by the snapshot bundler (step 3); step 2
ships the classifier plus tests with hand-built dicts so the threshold
contract is locked before snapshot wiring lands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds


WeeklyMileageTrendBand = str   # "very_low" | "low" | "moderate" | "high" | "very_high" | "unknown"
HardSessionLoadBand = str      # "none" | "light" | "moderate" | "heavy" | "unknown"
FreshnessBand = str            # "fresh" | "neutral" | "fatigued" | "overreaching" | "unknown"
RecoveryAdjacentBand = str     # "favourable" | "neutral" | "compromised" | "unknown"
CoverageBand = str             # "full" | "partial" | "sparse" | "insufficient"
RunningReadinessStatus = str   # "ready" | "conditional" | "hold" | "unknown"


@dataclass(frozen=True)
class ClassifiedRunningState:
    weekly_mileage_trend_band: WeeklyMileageTrendBand
    hard_session_load_band: HardSessionLoadBand
    freshness_band: FreshnessBand
    recovery_adjacent_band: RecoveryAdjacentBand
    coverage_band: CoverageBand
    running_readiness_status: RunningReadinessStatus
    readiness_score: Optional[float]
    uncertainty: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Band classifiers
# ---------------------------------------------------------------------------

def _resolve_weekly_mileage_ratio(
    weekly_m: Optional[float],
    baseline_m: Optional[float],
    explicit_ratio: Optional[float],
) -> Optional[float]:
    if explicit_ratio is not None:
        return explicit_ratio
    if weekly_m is None or baseline_m is None or baseline_m <= 0:
        return None
    return weekly_m / baseline_m


def _classify_weekly_mileage_trend(
    ratio: Optional[float],
    t: dict[str, Any],
) -> tuple[WeeklyMileageTrendBand, list[str]]:
    if ratio is None:
        return "unknown", ["weekly_mileage_baseline_unavailable"]
    cfg = t["classify"]["running"]["weekly_mileage_trend_band"]
    if ratio < cfg["very_low_max_ratio"]:
        return "very_low", []
    if ratio < cfg["low_max_ratio"]:
        return "low", []
    if ratio < cfg["moderate_max_ratio"]:
        return "moderate", []
    if ratio < cfg["high_max_ratio"]:
        return "high", []
    return "very_high", []


def _classify_hard_session_load(
    count: Optional[int],
    t: dict[str, Any],
) -> tuple[HardSessionLoadBand, list[str]]:
    if count is None:
        return "unknown", ["hard_session_history_unavailable"]
    cfg = t["classify"]["running"]["hard_session_load_band"]
    if count <= 0:
        return "none", []
    if count <= cfg["light_max_count"]:
        return "light", []
    if count <= cfg["moderate_max_count"]:
        return "moderate", []
    return "heavy", []


def _classify_freshness(
    acwr_ratio: Optional[float],
    t: dict[str, Any],
) -> tuple[FreshnessBand, list[str]]:
    if acwr_ratio is None:
        return "unknown", ["acwr_unavailable"]
    cfg = t["classify"]["running"]["freshness_band"]
    if acwr_ratio < cfg["fresh_max_ratio"]:
        return "fresh", []
    if acwr_ratio < cfg["neutral_max_ratio"]:
        return "neutral", []
    if acwr_ratio < cfg["fatigued_max_ratio"]:
        return "fatigued", []
    return "overreaching", []


def _classify_recovery_adjacent(
    training_readiness_pct: Optional[float],
    sleep_debt_band: Optional[str],
    resting_hr_band: Optional[str],
    t: dict[str, Any],
) -> tuple[RecoveryAdjacentBand, list[str]]:
    cfg = t["classify"]["running"]["recovery_adjacent_band"]
    inputs_present = sum(
        x is not None and x != "unknown"
        for x in (training_readiness_pct, sleep_debt_band, resting_hr_band)
    )
    if inputs_present == 0:
        return "unknown", ["recovery_adjacent_signals_unavailable"]

    compromised_signals = sum([
        training_readiness_pct is not None
        and training_readiness_pct < cfg["compromised_max_training_readiness_pct"],
        sleep_debt_band in {"moderate", "elevated"},
        resting_hr_band == "well_above",
    ])
    favourable_signals = sum([
        training_readiness_pct is not None
        and training_readiness_pct >= cfg["favourable_min_training_readiness_pct"],
        sleep_debt_band in {"none"},
        resting_hr_band in {"below", "at"},
    ])

    if compromised_signals >= 1:
        return "compromised", []
    # Require at least two favourable signals to call it favourable; otherwise neutral.
    if favourable_signals >= 2:
        return "favourable", []
    return "neutral", []


def _classify_coverage(
    weekly_mileage_present: bool,
    weekly_mileage_baseline_present: bool,
    acwr_present: bool,
    hard_session_count_present: bool,
    recovery_adjacent_any_present: bool,
    *,
    activity_count_14d: Optional[int] = None,
) -> CoverageBand:
    # Structural-activity relaxation (v0.1.4): when the intervals.icu
    # /activities pull has delivered enough recent sessions, we know the
    # user is actively running even if the 28-day distance-series baseline
    # isn't fully populated. Three quality activities in the window is the
    # lowest count where a weekly baseline derived from structural data
    # beats "no baseline at all." This keeps the classifier from forcing a
    # defer when the wearable clearly shows consistent running load.
    if (
        activity_count_14d is not None
        and activity_count_14d >= 3
        and weekly_mileage_present
    ):
        weekly_mileage_baseline_present = True

    # Insufficient: cannot establish a mileage trend at all.
    if not weekly_mileage_present or not weekly_mileage_baseline_present:
        return "insufficient"
    # Sparse: no ACWR (the freshness signal the synthesis layer wants).
    if not acwr_present:
        return "sparse"
    # Partial: hard-session history or recovery-adjacent missing.
    if not hard_session_count_present or not recovery_adjacent_any_present:
        return "partial"
    return "full"


def _running_readiness_status(
    freshness: FreshnessBand,
    recovery_adjacent: RecoveryAdjacentBand,
    mileage_trend: WeeklyMileageTrendBand,
    hard_session_load: HardSessionLoadBand,
    coverage: CoverageBand,
) -> RunningReadinessStatus:
    if coverage == "insufficient":
        return "unknown"
    if freshness == "overreaching":
        return "hold"
    if recovery_adjacent == "compromised" and mileage_trend in {"high", "very_high"}:
        return "hold"
    if (
        freshness in {"fresh", "neutral"}
        and recovery_adjacent in {"favourable", "neutral"}
        and hard_session_load != "heavy"
    ):
        return "ready"
    return "conditional"


def _readiness_score(
    mileage_trend: WeeklyMileageTrendBand,
    hard_session_load: HardSessionLoadBand,
    freshness: FreshnessBand,
    recovery_adjacent: RecoveryAdjacentBand,
    coverage: CoverageBand,
    t: dict[str, Any],
) -> Optional[float]:
    if coverage == "insufficient":
        return None

    penalties = t["classify"]["running"]["readiness_score_penalty"]
    score = 1.0

    if mileage_trend == "high":
        score -= penalties["mileage_trend_high"]
    elif mileage_trend == "very_high":
        score -= penalties["mileage_trend_very_high"]

    if hard_session_load == "moderate":
        score -= penalties["hard_session_load_moderate"]
    elif hard_session_load == "heavy":
        score -= penalties["hard_session_load_heavy"]

    if freshness == "fatigued":
        score -= penalties["freshness_fatigued"]
    elif freshness == "overreaching":
        score -= penalties["freshness_overreaching"]
    elif freshness == "fresh":
        score -= penalties["freshness_fresh"]  # negative penalty = bonus

    if recovery_adjacent == "compromised":
        score -= penalties["recovery_adjacent_compromised"]
    elif recovery_adjacent == "favourable":
        score -= penalties["recovery_adjacent_favourable"]  # negative = bonus

    return round(max(0.0, min(1.0, score)), 2)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def classify_running_state(
    running_signals: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
) -> ClassifiedRunningState:
    """Classify today's running signals into bands, status, and score.

    Args:
        running_signals: dict bundling the running-domain inputs. Recognised keys:
            ``weekly_mileage_m``, ``weekly_mileage_baseline_m``,
            ``weekly_mileage_ratio`` (optional pre-computed override),
            ``recent_hard_session_count_7d``, ``acwr_ratio``,
            ``training_readiness_pct``, ``sleep_debt_band``,
            ``resting_hr_band``. All keys are optional; absent keys
            propagate as ``unknown`` bands and uncertainty tokens.
        thresholds: optional pre-loaded config dict. If None, loads via
            ``core.config.load_thresholds()``.

    Returns:
        ``ClassifiedRunningState``. ``uncertainty`` is dedup'd + sorted.
    """

    t = thresholds if thresholds is not None else load_thresholds()
    uncertainty: list[str] = []

    weekly_m = running_signals.get("weekly_mileage_m")
    weekly_baseline_m = running_signals.get("weekly_mileage_baseline_m")
    explicit_ratio = running_signals.get("weekly_mileage_ratio")
    weekly_ratio = _resolve_weekly_mileage_ratio(
        weekly_m, weekly_baseline_m, explicit_ratio,
    )
    mileage_band, u = _classify_weekly_mileage_trend(weekly_ratio, t)
    uncertainty.extend(u)

    hard_count = running_signals.get("recent_hard_session_count_7d")
    hard_band, u = _classify_hard_session_load(hard_count, t)
    uncertainty.extend(u)

    acwr = running_signals.get("acwr_ratio")
    freshness, u = _classify_freshness(acwr, t)
    uncertainty.extend(u)

    tr_pct = running_signals.get("training_readiness_pct")
    sleep_debt = running_signals.get("sleep_debt_band")
    rhr = running_signals.get("resting_hr_band")
    recovery_adjacent, u = _classify_recovery_adjacent(tr_pct, sleep_debt, rhr, t)
    uncertainty.extend(u)

    coverage = _classify_coverage(
        weekly_mileage_present=(weekly_m is not None or explicit_ratio is not None),
        weekly_mileage_baseline_present=(
            weekly_baseline_m is not None or explicit_ratio is not None
        ),
        acwr_present=(acwr is not None),
        hard_session_count_present=(hard_count is not None),
        recovery_adjacent_any_present=(
            tr_pct is not None or sleep_debt is not None or rhr is not None
        ),
        activity_count_14d=running_signals.get("activity_count_14d"),
    )

    status = _running_readiness_status(
        freshness, recovery_adjacent, mileage_band, hard_band, coverage,
    )
    score = _readiness_score(
        mileage_band, hard_band, freshness, recovery_adjacent, coverage, t,
    )

    return ClassifiedRunningState(
        weekly_mileage_trend_band=mileage_band,
        hard_session_load_band=hard_band,
        freshness_band=freshness,
        recovery_adjacent_band=recovery_adjacent,
        coverage_band=coverage,
        running_readiness_status=status,
        readiness_score=score,
        uncertainty=tuple(sorted(set(uncertainty))),
    )
