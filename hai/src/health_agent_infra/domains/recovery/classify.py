"""Recovery-domain state classification — deterministic bands + scoring.

Extracted from `skills/recovery-readiness/SKILL.md` (Phase 1 step 3). Every
numerical decision from the skill lives here; the skill retains only
judgment (rationale text, action-matrix mapping, goal-aware detail).

Bands:

- **sleep_debt_band**: {none, mild, moderate, elevated, unknown}, from
  `sleep_hours`.
- **resting_hr_band**: {below, at, above, well_above, unknown}, from
  `resting_hr_ratio_vs_baseline` (high = worse).
- **hrv_band**: {below, at, above, well_above, unknown}, from
  `hrv_ratio_vs_baseline` (low = worse).
- **training_load_band**: {low, moderate, high, spike, unknown}, from
  `training_load_ratio_vs_baseline`; falls back to absolute thresholds
  when baseline is missing.
- **soreness**: pass-through of `soreness_self_report` when present; else
  `unknown`.
- **coverage_band**: {full, partial, sparse, insufficient}.
- **recovery_status**: {recovered, mildly_impaired, impaired, unknown}
  from impaired/mild signal counts.
- **readiness_score**: 0.0-1.0 float, computed only when coverage is not
  insufficient.
- **uncertainty**: list[str] of tokens added as signals are missing.

`classify_recovery_state(evidence, raw_summary, thresholds=None) →
ClassifiedRecoveryState` is the single entry point; callers supply a
cleaned-evidence dict and a raw-summary dict (shape matches the stdout
of `hai clean`). Thresholds fall back to `core.config.load_thresholds()`
if not provided.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds


SleepDebtBand = str       # "none" | "mild" | "moderate" | "elevated" | "unknown"
RestingHrBand = str       # "below" | "at" | "above" | "well_above" | "unknown"
HrvBand = str             # "below" | "at" | "above" | "well_above" | "unknown"
TrainingLoadBand = str    # "low" | "moderate" | "high" | "spike" | "unknown"
SorenessBand = str        # "low" | "moderate" | "high" | "unknown"
CoverageBand = str        # "full" | "partial" | "sparse" | "insufficient"
RecoveryStatus = str      # "recovered" | "mildly_impaired" | "impaired" | "unknown"


@dataclass(frozen=True)
class ClassifiedRecoveryState:
    sleep_debt_band: SleepDebtBand
    resting_hr_band: RestingHrBand
    hrv_band: HrvBand
    training_load_band: TrainingLoadBand
    soreness_band: SorenessBand
    coverage_band: CoverageBand
    recovery_status: RecoveryStatus
    readiness_score: Optional[float]  # None if coverage=insufficient
    uncertainty: tuple[str, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Band classifiers
# ---------------------------------------------------------------------------

def _classify_sleep_debt(
    sleep_hours: Optional[float], t: dict[str, Any]
) -> tuple[SleepDebtBand, list[str]]:
    if sleep_hours is None:
        return "unknown", ["sleep_record_missing"]
    cfg = t["classify"]["recovery"]["sleep_debt_band"]
    if sleep_hours >= cfg["none_min_hours"]:
        return "none", []
    if sleep_hours >= cfg["mild_min_hours"]:
        return "mild", []
    if sleep_hours >= cfg["moderate_min_hours"]:
        return "moderate", []
    return "elevated", []


def _classify_resting_hr(
    resting_hr: Optional[float],
    baseline: Optional[float],
    ratio: Optional[float],
    t: dict[str, Any],
) -> tuple[RestingHrBand, list[str]]:
    if resting_hr is None:
        return "unknown", ["resting_hr_record_missing"]
    if baseline is None or ratio is None:
        return "unknown", ["baseline_window_too_short"]
    cfg = t["classify"]["recovery"]["resting_hr_band"]
    if ratio >= cfg["well_above_ratio"]:
        return "well_above", []
    if ratio >= cfg["above_ratio"]:
        return "above", []
    if ratio >= cfg["at_lower_ratio"]:
        return "at", []
    return "below", []


def _classify_hrv(
    hrv_ms: Optional[float],
    ratio: Optional[float],
    t: dict[str, Any],
) -> tuple[HrvBand, list[str]]:
    if hrv_ms is None or ratio is None:
        return "unknown", ["hrv_unavailable"]
    cfg = t["classify"]["recovery"]["hrv_band"]
    if ratio >= cfg["well_above_min_ratio"]:
        return "well_above", []
    if ratio >= cfg["above_min_ratio"]:
        return "above", []
    if ratio <= cfg["below_max_ratio"]:
        return "below", []
    return "at", []


def _classify_training_load(
    trailing: Optional[float],
    baseline: Optional[float],
    ratio: Optional[float],
    t: dict[str, Any],
) -> tuple[TrainingLoadBand, list[str]]:
    if trailing is None:
        return "unknown", ["training_load_window_incomplete"]
    cfg = t["classify"]["recovery"]["training_load_band"]
    if baseline is not None and ratio is not None:
        if ratio >= cfg["spike_ratio"]:
            return "spike", []
        if ratio >= cfg["high_ratio"]:
            return "high", []
        if ratio >= cfg["moderate_ratio"]:
            return "moderate", []
        return "low", []
    # Absolute fallback when baseline is missing.
    fallback = cfg["absolute_fallback"]
    if trailing >= fallback["high_load"]:
        return "high", ["training_load_baseline_missing"]
    if trailing >= fallback["moderate_load"]:
        return "moderate", ["training_load_baseline_missing"]
    return "low", ["training_load_baseline_missing"]


def _classify_soreness(value: Optional[str]) -> tuple[SorenessBand, list[str]]:
    if value is None or value not in {"low", "moderate", "high"}:
        return "unknown", ["manual_checkin_missing"]
    return value, []


def _classify_coverage(
    sleep_present: bool,
    soreness_present: bool,
    resting_hr_present: bool,
    training_load_present: bool,
    hrv_present: bool,
    resting_hr_baseline_present: bool,
) -> CoverageBand:
    if not sleep_present or not soreness_present:
        return "insufficient"
    if not resting_hr_present or not training_load_present:
        return "sparse"
    if not hrv_present or not resting_hr_baseline_present:
        return "partial"
    return "full"


def _recovery_status(
    sleep_debt: SleepDebtBand,
    soreness: SorenessBand,
    rhr: RestingHrBand,
    hrv: HrvBand,
    load: TrainingLoadBand,
    coverage: CoverageBand,
) -> RecoveryStatus:
    if coverage == "insufficient":
        return "unknown"
    impaired = sum([
        sleep_debt == "elevated",
        soreness == "high",
        rhr == "well_above",
        load == "spike",
    ])
    mild = sum([
        sleep_debt in {"mild", "moderate"},
        soreness == "moderate",
        rhr == "above",
        hrv == "below",
        load == "high",
    ])
    if impaired >= 2:
        return "impaired"
    if impaired >= 1 or mild >= 2:
        return "mildly_impaired"
    return "recovered"


def _readiness_score(
    sleep_debt: SleepDebtBand,
    soreness: SorenessBand,
    rhr: RestingHrBand,
    hrv: HrvBand,
    load: TrainingLoadBand,
    coverage: CoverageBand,
    t: dict[str, Any],
) -> Optional[float]:
    if coverage == "insufficient":
        return None

    penalties = t["classify"]["recovery"]["readiness_score_penalty"]
    score = 1.0

    if sleep_debt == "mild":
        score -= penalties["sleep_debt_mild"]
    elif sleep_debt == "moderate":
        score -= penalties["sleep_debt_moderate"]
    elif sleep_debt == "elevated":
        score -= penalties["sleep_debt_elevated"]

    if soreness == "moderate":
        score -= penalties["soreness_moderate"]
    elif soreness == "high":
        score -= penalties["soreness_high"]

    if rhr == "above":
        score -= penalties["resting_hr_above"]
    elif rhr == "well_above":
        score -= penalties["resting_hr_well_above"]
    elif rhr == "below":
        score -= penalties["resting_hr_below"]  # negative penalty = add

    if hrv == "below":
        score -= penalties["hrv_below"]
    elif hrv in {"above", "well_above"}:
        score -= penalties["hrv_above_or_well_above"]

    if load == "high":
        score -= penalties["load_high"]
    elif load == "spike":
        score -= penalties["load_spike"]

    # Clamp to [0.0, 1.0] then round to 2 decimals.
    return round(max(0.0, min(1.0, score)), 2)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def classify_recovery_state(
    evidence: dict[str, Any],
    raw_summary: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
) -> ClassifiedRecoveryState:
    """Classify today's recovery signals into bands, status, and score.

    Args:
        evidence: `cleaned_evidence` dict from `hai clean`.
        raw_summary: `raw_summary` dict from `hai clean`.
        thresholds: optional pre-loaded config dict. If None, loads via
            `core.config.load_thresholds()`.

    Returns:
        A `ClassifiedRecoveryState`. Uncertainty is deduplicated and
        sorted alphabetically.
    """

    t = thresholds if thresholds is not None else load_thresholds()
    uncertainty: list[str] = []

    sleep_hours = evidence.get("sleep_hours")
    sleep_debt, u = _classify_sleep_debt(sleep_hours, t)
    uncertainty.extend(u)

    resting_hr = evidence.get("resting_hr")
    rhr_baseline = raw_summary.get("resting_hr_baseline")
    rhr_ratio = raw_summary.get("resting_hr_ratio_vs_baseline")
    rhr_band, u = _classify_resting_hr(resting_hr, rhr_baseline, rhr_ratio, t)
    uncertainty.extend(u)

    hrv_ms = evidence.get("hrv_ms")
    hrv_ratio = raw_summary.get("hrv_ratio_vs_baseline")
    hrv_band, u = _classify_hrv(hrv_ms, hrv_ratio, t)
    uncertainty.extend(u)

    trailing = raw_summary.get("trailing_7d_training_load") or evidence.get(
        "trailing_7d_training_load"
    )
    load_baseline = raw_summary.get("training_load_baseline")
    load_ratio = raw_summary.get("training_load_ratio_vs_baseline")
    load_band, u = _classify_training_load(trailing, load_baseline, load_ratio, t)
    uncertainty.extend(u)

    soreness_band, u = _classify_soreness(evidence.get("soreness_self_report"))
    uncertainty.extend(u)

    coverage = _classify_coverage(
        sleep_present=(sleep_hours is not None),
        soreness_present=(soreness_band != "unknown"),
        resting_hr_present=(resting_hr is not None),
        training_load_present=(trailing is not None),
        hrv_present=(hrv_ms is not None),
        resting_hr_baseline_present=(rhr_baseline is not None),
    )

    status = _recovery_status(
        sleep_debt, soreness_band, rhr_band, hrv_band, load_band, coverage
    )
    score = _readiness_score(
        sleep_debt, soreness_band, rhr_band, hrv_band, load_band, coverage, t
    )

    dedup_sorted = tuple(sorted(set(uncertainty)))

    return ClassifiedRecoveryState(
        sleep_debt_band=sleep_debt,
        resting_hr_band=rhr_band,
        hrv_band=hrv_band,
        training_load_band=load_band,
        soreness_band=soreness_band,
        coverage_band=coverage,
        recovery_status=status,
        readiness_score=score,
        uncertainty=dedup_sorted,
    )
