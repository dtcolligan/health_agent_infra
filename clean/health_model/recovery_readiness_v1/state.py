"""STATE layer.

Builds a RecoveryState from a CleanedEvidence object. Deterministic.
Consumers (RECOMMEND) read only from the emitted state, not from raw evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from health_model.recovery_readiness_v1.schemas import (
    STATE_SCHEMA_VERSION,
    BaselineBand,
    CleanedEvidence,
    CoverageBand,
    InputsUsed,
    RecoveryState,
    RecoveryStatus,
    SignalQuality,
    SleepDebt,
    SorenessSignal,
    TrainingLoadBand,
)


def build_recovery_state(
    evidence: CleanedEvidence, *, now: Optional[datetime] = None
) -> RecoveryState:
    now = now or datetime.now(timezone.utc)

    uncertainties: list[str] = []

    sleep_debt = _derive_sleep_debt(evidence.sleep_hours, uncertainties)
    resting_hr_band = _derive_band(
        evidence.resting_hr,
        evidence.resting_hr_baseline,
        direction="high_is_bad",
        missing_token="resting_hr_record_missing",
        uncertainties=uncertainties,
    )
    hrv_band = _derive_band(
        evidence.hrv_ms,
        evidence.hrv_baseline,
        direction="low_is_bad",
        missing_token="hrv_unavailable",
        uncertainties=uncertainties,
    )
    soreness: SorenessSignal = evidence.soreness_self_report or "unknown"
    if evidence.soreness_self_report is None:
        uncertainties.append("manual_checkin_missing")

    load_band = _derive_training_load_band(
        evidence.trailing_7d_training_load, evidence.training_load_baseline, uncertainties
    )

    coverage = _derive_coverage(evidence, uncertainties)

    if coverage == "insufficient":
        recovery_status: RecoveryStatus = "unknown"
        readiness_score: Optional[float] = None
    else:
        recovery_status = _derive_recovery_status(
            sleep_debt=sleep_debt,
            soreness=soreness,
            resting_hr_band=resting_hr_band,
            hrv_band=hrv_band,
            load_band=load_band,
        )
        readiness_score = _derive_readiness_score(
            sleep_debt=sleep_debt,
            soreness=soreness,
            resting_hr_band=resting_hr_band,
            hrv_band=hrv_band,
            load_band=load_band,
        )

    notes: list[str] = []
    if evidence.hrv_ms is None and evidence.resting_hr is not None:
        notes.append("hrv not reported by source today")

    signal_quality = SignalQuality(
        coverage=coverage,
        required_inputs_present=_required_inputs_present(evidence),
        notes=notes,
    )

    inputs_used = InputsUsed(
        garmin_sleep_record_id=evidence.sleep_record_id,
        garmin_resting_hr_record_id=evidence.resting_hr_record_id,
        garmin_hrv_record_id=evidence.hrv_record_id,
        training_load_window="trailing_7d",
        manual_readiness_submission_id=evidence.manual_readiness_submission_id,
        optional_context_note_ids=list(evidence.optional_context_note_ids),
    )

    return RecoveryState(
        schema_version=STATE_SCHEMA_VERSION,
        user_id=evidence.user_id,
        computed_at=now,
        as_of_date=evidence.as_of_date,
        recovery_status=recovery_status,
        readiness_score=readiness_score,
        sleep_debt=sleep_debt,
        soreness_signal=soreness,
        resting_hr_vs_baseline=resting_hr_band,
        hrv_vs_baseline=hrv_band,
        training_load_trailing_7d=load_band,
        active_goal=evidence.active_goal,
        signal_quality=signal_quality,
        uncertainties=sorted(set(uncertainties)),
        inputs_used=inputs_used,
    )


def _required_inputs_present(evidence: CleanedEvidence) -> bool:
    return (
        evidence.sleep_hours is not None
        and evidence.resting_hr is not None
        and evidence.soreness_self_report is not None
        and evidence.trailing_7d_training_load is not None
    )


def _derive_sleep_debt(sleep_hours: Optional[float], uncertainties: list[str]) -> SleepDebt:
    if sleep_hours is None:
        uncertainties.append("sleep_record_missing")
        return "unknown"
    if sleep_hours >= 7.5:
        return "none"
    if sleep_hours >= 7.0:
        return "mild"
    if sleep_hours >= 6.0:
        return "moderate"
    return "elevated"


def _derive_band(
    value: Optional[float],
    baseline: Optional[float],
    *,
    direction: str,
    missing_token: str,
    uncertainties: list[str],
) -> BaselineBand:
    if value is None:
        uncertainties.append(missing_token)
        return "unknown"
    if baseline is None:
        uncertainties.append("baseline_window_too_short")
        return "unknown"

    if direction == "high_is_bad":
        ratio = value / baseline
        if ratio >= 1.15:
            return "well_above"
        if ratio >= 1.05:
            return "above"
        if ratio <= 0.95:
            return "below"
        return "at"
    else:
        ratio = value / baseline
        if ratio <= 0.85:
            return "below"
        if ratio <= 0.95:
            return "below"
        if ratio >= 1.10:
            return "well_above"
        if ratio >= 1.02:
            return "above"
        return "at"


def _derive_training_load_band(
    trailing: Optional[float],
    baseline: Optional[float],
    uncertainties: list[str],
) -> TrainingLoadBand:
    if trailing is None:
        uncertainties.append("training_load_window_incomplete")
        return "unknown"
    if baseline is None or baseline <= 0:
        uncertainties.append("baseline_window_too_short")
        if trailing >= 500:
            return "high"
        if trailing >= 200:
            return "moderate"
        return "low"
    ratio = trailing / baseline
    if ratio >= 1.4:
        return "spike"
    if ratio >= 1.1:
        return "high"
    if ratio >= 0.7:
        return "moderate"
    return "low"


def _derive_recovery_status(
    *,
    sleep_debt: SleepDebt,
    soreness: SorenessSignal,
    resting_hr_band: BaselineBand,
    hrv_band: BaselineBand,
    load_band: TrainingLoadBand,
) -> RecoveryStatus:
    impaired_signals = 0
    mild_signals = 0

    if sleep_debt == "elevated":
        impaired_signals += 1
    elif sleep_debt == "moderate":
        mild_signals += 1
    elif sleep_debt == "mild":
        mild_signals += 1

    if soreness == "high":
        impaired_signals += 1
    elif soreness == "moderate":
        mild_signals += 1

    if resting_hr_band == "well_above":
        impaired_signals += 1
    elif resting_hr_band == "above":
        mild_signals += 1

    if hrv_band == "below":
        mild_signals += 1
    elif hrv_band == "well_above":
        pass

    if load_band == "spike":
        impaired_signals += 1
    elif load_band == "high":
        mild_signals += 1

    if impaired_signals >= 2:
        return "impaired"
    if impaired_signals >= 1 or mild_signals >= 2:
        return "mildly_impaired"
    return "recovered"


def _derive_readiness_score(
    *,
    sleep_debt: SleepDebt,
    soreness: SorenessSignal,
    resting_hr_band: BaselineBand,
    hrv_band: BaselineBand,
    load_band: TrainingLoadBand,
) -> float:
    score = 1.0
    debt_penalty = {"none": 0.0, "mild": 0.05, "moderate": 0.15, "elevated": 0.25, "unknown": 0.0}
    sore_penalty = {"low": 0.0, "moderate": 0.10, "high": 0.20, "unknown": 0.0}
    rhr_penalty = {"below": -0.02, "at": 0.0, "above": 0.10, "well_above": 0.20, "unknown": 0.0}
    hrv_penalty = {"below": 0.15, "at": 0.0, "above": -0.05, "well_above": -0.05, "unknown": 0.0}
    load_penalty = {"low": 0.0, "moderate": 0.0, "high": 0.05, "spike": 0.15, "unknown": 0.0}

    score -= debt_penalty[sleep_debt]
    score -= sore_penalty[soreness]
    score -= rhr_penalty[resting_hr_band]
    score -= hrv_penalty[hrv_band]
    score -= load_penalty[load_band]

    return round(max(0.0, min(1.0, score)), 2)


def _derive_coverage(evidence: CleanedEvidence, uncertainties: list[str]) -> CoverageBand:
    if evidence.sleep_hours is None or evidence.soreness_self_report is None:
        return "insufficient"
    if evidence.resting_hr is None or evidence.trailing_7d_training_load is None:
        return "sparse"

    stale_or_low_quality = False
    if evidence.hrv_ms is None:
        stale_or_low_quality = True
    if evidence.resting_hr_baseline is None:
        stale_or_low_quality = True
    if stale_or_low_quality:
        return "partial"
    return "full"
