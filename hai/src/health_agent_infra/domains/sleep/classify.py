"""Sleep-domain state classification — deterministic bands + scoring.

Phase 3 step 3. Mirrors the structure of ``domains.recovery.classify``
and ``domains.running.classify``: a single entry point
``classify_sleep_state`` that consumes a ``sleep_signals`` dict and
returns a frozen ``ClassifiedSleepState``. All numerical decisions live
here; the sleep-quality skill (SKILL.md) only writes prose.

Bands:

- **sleep_debt_band** ∈ {none, mild, moderate, elevated, unknown} — from
  ``sleep_hours``. Thresholds and vocabulary aligned with
  ``recovery.classify.sleep_debt_band`` so the Phase-3-step-5 X1 rewire
  (X1a: moderate → soften; X1b: elevated → block) can flip to reading
  this field without re-thresholding.
- **sleep_quality_band** ∈ {excellent, good, fair, poor, unknown} —
  from Garmin's 0-100 ``sleep_score_overall``.
- **sleep_timing_consistency_band** ∈ {consistent, variable,
  highly_variable, unknown} — from ``sleep_start_variance_minutes`` (a
  pre-computed stddev of ``sleep_start_ts`` across recent nights). In
  v1 production the input is always None because ``sleep_start_ts`` is
  a v1.1 enrichment that stays NULL in migration 004 — the field is
  surfaced as ``unknown`` with ``sleep_start_ts_unavailable_in_v1`` in
  uncertainty. Tests may drive the signal directly to lock the band
  contract for v1.1.
- **sleep_efficiency_band** ∈ {excellent, good, fair, poor, unknown} —
  computed from ``sleep_hours`` × 60 / (sleep_hours × 60 +
  sleep_awake_min) × 100. Absent ``sleep_awake_min`` → ``unknown``.
- **coverage_band** ∈ {full, partial, sparse, insufficient}.
- **sleep_status** ∈ {optimal, adequate, compromised, impaired, unknown}
  — composite verdict over every band.
- **sleep_score** ∈ [0.0, 1.0] or None — None iff coverage=insufficient.
- **uncertainty**: tuple of dedup'd, sorted reason tokens.

Signal dict keys recognised:

  - ``sleep_hours`` (float)
  - ``sleep_score_overall`` (int, 0-100)
  - ``sleep_awake_min`` (float)
  - ``sleep_start_variance_minutes`` (float; optional pre-computed stddev)

All keys are optional; absent keys propagate as ``unknown`` bands and
uncertainty tokens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds


SleepDebtBand = str                 # "none" | "mild" | "moderate" | "elevated" | "unknown"
SleepQualityBand = str              # "excellent" | "good" | "fair" | "poor" | "unknown"
SleepTimingConsistencyBand = str    # "consistent" | "variable" | "highly_variable" | "unknown"
SleepEfficiencyBand = str           # "excellent" | "good" | "fair" | "poor" | "unknown"
CoverageBand = str                  # "full" | "partial" | "sparse" | "insufficient"
SleepStatus = str                   # "optimal" | "adequate" | "compromised" | "impaired" | "unknown"


@dataclass(frozen=True)
class ClassifiedSleepState:
    sleep_debt_band: SleepDebtBand
    sleep_quality_band: SleepQualityBand
    sleep_timing_consistency_band: SleepTimingConsistencyBand
    sleep_efficiency_band: SleepEfficiencyBand
    coverage_band: CoverageBand
    sleep_status: SleepStatus
    sleep_score: Optional[float]  # None iff coverage=insufficient
    sleep_efficiency_pct: Optional[float]  # surfaced for rationale / audit
    uncertainty: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Band classifiers
# ---------------------------------------------------------------------------

def _classify_sleep_debt(
    sleep_hours: Optional[float], t: dict[str, Any]
) -> tuple[SleepDebtBand, list[str]]:
    if sleep_hours is None:
        return "unknown", ["sleep_record_missing"]
    cfg = t["classify"]["sleep"]["sleep_debt_band"]
    if sleep_hours >= cfg["none_min_hours"]:
        return "none", []
    if sleep_hours >= cfg["mild_min_hours"]:
        return "mild", []
    if sleep_hours >= cfg["moderate_min_hours"]:
        return "moderate", []
    return "elevated", []


def _classify_sleep_quality(
    score: Optional[float], t: dict[str, Any]
) -> tuple[SleepQualityBand, list[str]]:
    if score is None:
        return "unknown", ["sleep_score_unavailable"]
    cfg = t["classify"]["sleep"]["sleep_quality_band"]
    if score >= cfg["excellent_min_score"]:
        return "excellent", []
    if score >= cfg["good_min_score"]:
        return "good", []
    if score >= cfg["fair_min_score"]:
        return "fair", []
    return "poor", []


def _classify_sleep_timing_consistency(
    variance_min: Optional[float], t: dict[str, Any]
) -> tuple[SleepTimingConsistencyBand, list[str]]:
    # v1 production will always hit this branch — sleep_start_ts is a
    # v1.1 enrichment and the migration-004 column stays NULL. Tests
    # drive the signal directly so the band contract is frozen for v1.1.
    if variance_min is None:
        return "unknown", ["sleep_start_ts_unavailable_in_v1"]
    cfg = t["classify"]["sleep"]["sleep_timing_consistency_band"]
    if variance_min < cfg["consistent_max_stddev_min"]:
        return "consistent", []
    if variance_min < cfg["variable_max_stddev_min"]:
        return "variable", []
    return "highly_variable", []


def _compute_efficiency_pct(
    sleep_hours: Optional[float], awake_min: Optional[float]
) -> Optional[float]:
    if sleep_hours is None or awake_min is None:
        return None
    asleep_min = sleep_hours * 60.0
    total = asleep_min + awake_min
    if total <= 0:
        return None
    return round(asleep_min / total * 100.0, 1)


def _classify_sleep_efficiency(
    efficiency_pct: Optional[float],
    sleep_hours_present: bool,
    awake_min_present: bool,
    t: dict[str, Any],
) -> tuple[SleepEfficiencyBand, list[str]]:
    if efficiency_pct is None:
        tokens: list[str] = []
        if not awake_min_present or not sleep_hours_present:
            tokens.append("sleep_efficiency_unavailable")
        return "unknown", tokens
    cfg = t["classify"]["sleep"]["sleep_efficiency_band"]
    if efficiency_pct >= cfg["excellent_min_pct"]:
        return "excellent", []
    if efficiency_pct >= cfg["good_min_pct"]:
        return "good", []
    if efficiency_pct >= cfg["fair_min_pct"]:
        return "fair", []
    return "poor", []


def _classify_coverage(
    sleep_hours_present: bool,
    sleep_score_present: bool,
    awake_min_present: bool,
) -> CoverageBand:
    # Insufficient: no headline duration signal — nothing else can
    # compensate. This is the R1 coverage gate's trigger condition.
    if not sleep_hours_present:
        return "insufficient"
    # Sparse: duration present but neither quality (score) nor
    # efficiency (awake_min) available. R5 sparse cap will fire.
    if not sleep_score_present and not awake_min_present:
        return "sparse"
    # Partial: duration + one of {score, efficiency}.
    if not sleep_score_present or not awake_min_present:
        return "partial"
    # Full: duration + score + efficiency. Timing consistency is NOT
    # a coverage-gating signal in v1 — sleep_start_ts is NULL by design
    # in migration 004 and its absence must not downgrade every
    # production snapshot to partial.
    return "full"


def _sleep_status(
    debt: SleepDebtBand,
    quality: SleepQualityBand,
    consistency: SleepTimingConsistencyBand,
    efficiency: SleepEfficiencyBand,
    coverage: CoverageBand,
) -> SleepStatus:
    if coverage == "insufficient":
        return "unknown"
    impaired_signals = sum([
        debt == "elevated",
        quality == "poor",
        efficiency == "poor",
    ])
    mild_signals = sum([
        debt in {"mild", "moderate"},
        quality == "fair",
        efficiency == "fair",
        consistency == "highly_variable",
    ])
    favourable_signals = sum([
        debt == "none",
        quality in {"excellent", "good"},
        efficiency in {"excellent", "good"},
        consistency == "consistent",
    ])
    if impaired_signals >= 2:
        return "impaired"
    if impaired_signals >= 1 or mild_signals >= 2:
        return "compromised"
    if favourable_signals >= 3 and mild_signals == 0:
        return "optimal"
    return "adequate"


def _sleep_score(
    debt: SleepDebtBand,
    quality: SleepQualityBand,
    consistency: SleepTimingConsistencyBand,
    efficiency: SleepEfficiencyBand,
    coverage: CoverageBand,
    t: dict[str, Any],
) -> Optional[float]:
    if coverage == "insufficient":
        return None

    penalties = t["classify"]["sleep"]["sleep_score_penalty"]
    score = 1.0

    if debt == "mild":
        score -= penalties["debt_mild"]
    elif debt == "moderate":
        score -= penalties["debt_moderate"]
    elif debt == "elevated":
        score -= penalties["debt_elevated"]

    if quality == "good":
        score -= penalties["quality_good"]  # small/negative (bonus) permitted
    elif quality == "fair":
        score -= penalties["quality_fair"]
    elif quality == "poor":
        score -= penalties["quality_poor"]
    elif quality == "excellent":
        score -= penalties["quality_excellent"]  # negative → bonus

    if efficiency == "fair":
        score -= penalties["efficiency_fair"]
    elif efficiency == "poor":
        score -= penalties["efficiency_poor"]
    elif efficiency == "excellent":
        score -= penalties["efficiency_excellent"]  # negative → bonus

    if consistency == "variable":
        score -= penalties["consistency_variable"]
    elif consistency == "highly_variable":
        score -= penalties["consistency_highly_variable"]

    return round(max(0.0, min(1.0, score)), 2)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def classify_sleep_state(
    sleep_signals: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
) -> ClassifiedSleepState:
    """Classify last night's sleep signals into bands, status, and score.

    Args:
        sleep_signals: dict bundling the sleep-domain inputs. Recognised
            keys: ``sleep_hours``, ``sleep_score_overall``,
            ``sleep_awake_min``, ``sleep_start_variance_minutes``. All
            keys are optional; absent keys propagate as ``unknown`` bands
            and uncertainty tokens.
        thresholds: optional pre-loaded config dict. If None, loads via
            ``core.config.load_thresholds()``.

    Returns:
        ``ClassifiedSleepState``. ``uncertainty`` is dedup'd + sorted.
    """

    t = thresholds if thresholds is not None else load_thresholds()
    uncertainty: list[str] = []

    sleep_hours = sleep_signals.get("sleep_hours")
    debt, u = _classify_sleep_debt(sleep_hours, t)
    uncertainty.extend(u)

    score_overall = sleep_signals.get("sleep_score_overall")
    quality, u = _classify_sleep_quality(score_overall, t)
    uncertainty.extend(u)

    variance_min = sleep_signals.get("sleep_start_variance_minutes")
    consistency, u = _classify_sleep_timing_consistency(variance_min, t)
    uncertainty.extend(u)

    awake_min = sleep_signals.get("sleep_awake_min")
    efficiency_pct = _compute_efficiency_pct(sleep_hours, awake_min)
    efficiency, u = _classify_sleep_efficiency(
        efficiency_pct,
        sleep_hours_present=(sleep_hours is not None),
        awake_min_present=(awake_min is not None),
        t=t,
    )
    uncertainty.extend(u)

    coverage = _classify_coverage(
        sleep_hours_present=(sleep_hours is not None),
        sleep_score_present=(score_overall is not None),
        awake_min_present=(awake_min is not None),
    )

    status = _sleep_status(debt, quality, consistency, efficiency, coverage)
    score = _sleep_score(debt, quality, consistency, efficiency, coverage, t)

    return ClassifiedSleepState(
        sleep_debt_band=debt,
        sleep_quality_band=quality,
        sleep_timing_consistency_band=consistency,
        sleep_efficiency_band=efficiency,
        coverage_band=coverage,
        sleep_status=status,
        sleep_score=score,
        sleep_efficiency_pct=efficiency_pct,
        uncertainty=tuple(sorted(set(uncertainty))),
    )
