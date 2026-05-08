"""CLEAN layer — deterministic normalization + raw-number aggregation.

Consumes PULL-shaped raw inputs and emits two typed objects:

- ``CleanedEvidence`` — typed record of the day's inputs (sleep, HR, HRV,
  trailing training load, manual readiness fields). Missing source fields
  stay as ``None``; no fabrication.
- ``RawSummary`` — deltas, ratios, counts, and coverage fractions over a
  14-day window. No bands, no classifications, no scores.

The agent reads both, plus the recovery-readiness skill, to produce a
``TrainingRecommendation``. Classification is explicitly out of scope for
this module.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable, Optional

from health_agent_infra.core.schemas import (
    CleanedEvidence,
    RAW_SUMMARY_SCHEMA_VERSION,
    RawSummary,
)


WELL_ABOVE_RESTING_HR_RATIO = 1.15


def _coerce_date(value) -> date:
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)).date()


def _mean(values: Iterable[float]) -> Optional[float]:
    values = [v for v in values if v is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _ratio(value: Optional[float], baseline: Optional[float]) -> Optional[float]:
    if value is None or baseline is None or baseline == 0:
        return None
    return value / baseline


def _dedupe_by_date(records: list[dict]) -> dict[date, dict]:
    result: dict[date, dict] = {}
    for rec in records:
        result[_coerce_date(rec["date"])] = rec
    return result


def clean_inputs(
    *,
    user_id: str,
    as_of_date: date | str,
    garmin_sleep: Optional[dict],
    garmin_resting_hr_recent: list[dict],
    garmin_hrv_recent: list[dict],
    garmin_training_load_7d: list[dict],
    manual_readiness: Optional[dict],
    optional_context_notes: Optional[list[dict]] = None,
) -> CleanedEvidence:
    """Turn raw source-shaped records into a typed CleanedEvidence object."""

    as_of = _coerce_date(as_of_date)

    sleep_hours = None
    sleep_record_id = None
    if garmin_sleep:
        sleep_hours = garmin_sleep.get("duration_hours")
        sleep_record_id = garmin_sleep.get("record_id")

    rhr_latest = _dedupe_by_date(garmin_resting_hr_recent)
    today_rhr = None
    today_rhr_id = None
    for rec_date, rec in rhr_latest.items():
        if rec_date == as_of:
            today_rhr = rec.get("bpm")
            today_rhr_id = rec.get("record_id")
            break

    hrv_latest = _dedupe_by_date(garmin_hrv_recent)
    today_hrv = None
    today_hrv_id = None
    for rec_date, rec in hrv_latest.items():
        if rec_date == as_of:
            today_hrv = rec.get("rmssd_ms")
            today_hrv_id = rec.get("record_id")
            break

    load_values: list[float] = []
    for rec in garmin_training_load_7d:
        rec_date = _coerce_date(rec["date"])
        if as_of - timedelta(days=7) <= rec_date <= as_of:
            if rec.get("load") is not None:
                load_values.append(rec["load"])
    trailing_load = sum(load_values) if load_values else None

    soreness = None
    energy = None
    planned = None
    manual_id = None
    active_goal = None
    if manual_readiness:
        soreness = manual_readiness.get("soreness")
        energy = manual_readiness.get("energy")
        planned = manual_readiness.get("planned_session_type")
        manual_id = manual_readiness.get("submission_id")
        active_goal = manual_readiness.get("active_goal")

    note_ids = [n["note_id"] for n in (optional_context_notes or []) if n.get("note_id")]

    return CleanedEvidence(
        as_of_date=as_of,
        user_id=user_id,
        sleep_hours=sleep_hours,
        sleep_record_id=sleep_record_id,
        resting_hr=today_rhr,
        resting_hr_record_id=today_rhr_id,
        hrv_ms=today_hrv,
        hrv_record_id=today_hrv_id,
        trailing_7d_training_load=trailing_load,
        soreness_self_report=soreness,
        energy_self_report=energy,
        planned_session_type=planned,
        manual_readiness_submission_id=manual_id,
        active_goal=active_goal,
        optional_context_note_ids=note_ids,
    )


def build_raw_summary(
    *,
    user_id: str,
    as_of_date: date | str,
    garmin_sleep: Optional[dict],
    garmin_resting_hr_recent: list[dict],
    garmin_hrv_recent: list[dict],
    garmin_training_load_7d: list[dict],
    raw_daily_row: Optional[dict] = None,
) -> RawSummary:
    """Compute a RawSummary of deltas/ratios/counts/coverage fractions.

    Pure aggregation. No bands, no classifications, no interpretation.
    The agent reads these numbers and decides what they mean.

    ``raw_daily_row`` is the full Garmin CSV row for ``as_of_date`` (as
    produced by the pull adapter's ``raw_daily_row`` key). When provided,
    the Garmin-richness fields (all_day_stress, body_battery, intensity
    minutes, distance, acwr ratio/status, training-readiness components)
    are populated from it. When absent, those fields stay None — older
    callers still work unchanged.
    """

    as_of = _coerce_date(as_of_date)

    # Sleep
    sleep_hours = garmin_sleep.get("duration_hours") if garmin_sleep else None
    # Sleep baseline: no window history in the current PULL shape, so baseline
    # is only available when a caller pre-computes it. For v1 we leave it None
    # unless extended. Keep the field for schema stability.
    sleep_baseline = None
    sleep_debt = None
    # If we had a baseline, sleep_debt = max(0, baseline - sleep_hours).

    # Resting HR + baseline + ratio
    rhr_latest = _dedupe_by_date(garmin_resting_hr_recent)
    today_rhr = None
    rhr_history: list[float] = []
    for rec_date, rec in sorted(rhr_latest.items()):
        bpm = rec.get("bpm")
        if rec_date == as_of:
            today_rhr = bpm
        elif as_of - timedelta(days=14) <= rec_date < as_of and bpm is not None:
            rhr_history.append(bpm)
    rhr_baseline = _mean(rhr_history)
    rhr_ratio = _ratio(today_rhr, rhr_baseline)

    # RHR spike days — consecutive trailing days (including today) where RHR
    # is >= 1.15 * baseline. Agent uses this for R6 (escalate).
    spike_days = _count_rhr_spike_days(as_of=as_of, history=garmin_resting_hr_recent, baseline=rhr_baseline)

    # HRV + baseline + ratio
    hrv_latest = _dedupe_by_date(garmin_hrv_recent)
    today_hrv = None
    hrv_history: list[float] = []
    for rec_date, rec in sorted(hrv_latest.items()):
        ms = rec.get("rmssd_ms")
        if rec_date == as_of:
            today_hrv = ms
        elif as_of - timedelta(days=14) <= rec_date < as_of and ms is not None:
            hrv_history.append(ms)
    hrv_baseline = _mean(hrv_history)
    hrv_ratio = _ratio(today_hrv, hrv_baseline)

    # Training load — trailing 7 days, and baseline = older 21-day window / 3
    trailing_values: list[float] = []
    older_values: list[float] = []
    for rec in garmin_training_load_7d:
        rec_date = _coerce_date(rec["date"])
        load = rec.get("load")
        if load is None:
            continue
        if as_of - timedelta(days=7) <= rec_date <= as_of:
            trailing_values.append(load)
        elif as_of - timedelta(days=28) <= rec_date < as_of - timedelta(days=7):
            older_values.append(load)
    trailing_load = sum(trailing_values) if trailing_values else None
    load_baseline = sum(older_values) / 3.0 if len(older_values) >= 21 else None
    load_ratio = _ratio(trailing_load, load_baseline)

    # Coverage fractions — what fraction of the last 7 days had a record for
    # each signal. Agent uses these to decide coverage band.
    cov_sleep = 1.0 if sleep_hours is not None else 0.0  # single-day field
    cov_rhr = _coverage_fraction(as_of=as_of, dated_records=garmin_resting_hr_recent, window=7)
    cov_hrv = _coverage_fraction(as_of=as_of, dated_records=garmin_hrv_recent, window=7)
    cov_load = _coverage_fraction(as_of=as_of, dated_records=garmin_training_load_7d, window=7)

    garmin_fields = _extract_garmin_richness(raw_daily_row)

    return RawSummary(
        schema_version=RAW_SUMMARY_SCHEMA_VERSION,
        as_of_date=as_of,
        user_id=user_id,
        sleep_hours=sleep_hours,
        sleep_baseline_hours=sleep_baseline,
        sleep_debt_hours=sleep_debt,
        resting_hr=today_rhr,
        resting_hr_baseline=rhr_baseline,
        resting_hr_ratio_vs_baseline=rhr_ratio,
        resting_hr_spike_days=spike_days,
        hrv_ms=today_hrv,
        hrv_baseline=hrv_baseline,
        hrv_ratio_vs_baseline=hrv_ratio,
        trailing_7d_training_load=trailing_load,
        training_load_baseline=load_baseline,
        training_load_ratio_vs_baseline=load_ratio,
        coverage_sleep_fraction=cov_sleep,
        coverage_rhr_fraction=cov_rhr,
        coverage_hrv_fraction=cov_hrv,
        coverage_training_load_fraction=cov_load,
        **garmin_fields,
    )


# Phase 7B — Garmin-native today-only signals pulled from the raw CSV row.
_GARMIN_READINESS_COMPONENT_COLUMNS = (
    "training_readiness_sleep_pct",
    "training_readiness_hrv_pct",
    "training_readiness_stress_pct",
    "training_readiness_sleep_history_pct",
    "training_readiness_load_pct",
)


def _extract_garmin_richness(raw_daily_row: Optional[dict]) -> dict:
    """Pull today-only Garmin-native fields from the full CSV row.

    Returns a dict keyed by ``RawSummary`` field names, suitable for
    ``**kwargs``-expansion. When ``raw_daily_row`` is None (older callers
    or pull failures), returns defaults — every field None. Numeric
    coercions are defensive: CSV can arrive with stringified values or
    pandas/numpy types.
    """

    if not raw_daily_row:
        return {}

    def _int(key: str) -> Optional[int]:
        v = raw_daily_row.get(key)
        if v is None:
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    def _float(key: str) -> Optional[float]:
        v = raw_daily_row.get(key)
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _str(key: str) -> Optional[str]:
        v = raw_daily_row.get(key)
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    # Garmin's native acute/chronic ratio — separate from training_load
    # ratio computed from RawSummary's trailing-vs-21-day-baseline series.
    acute = _float("acute_load")
    chronic = _float("chronic_load")
    garmin_acwr = None
    if acute is not None and chronic is not None and chronic != 0:
        garmin_acwr = round(acute / chronic, 3)

    # Local mean of the 5 component pcts when all present; None if any
    # component is missing. Garmin does NOT export an overall Training
    # Readiness pct in the daily CSV — only components + the categorical
    # level. The mean is NOT Garmin's own weighting; it can disagree with
    # `training_readiness_level`. The skill surfaces that disagreement
    # rather than hiding it behind a single "overall" number.
    components = [_float(col) for col in _GARMIN_READINESS_COMPONENT_COLUMNS]
    component_mean_pct = (
        # mypy: we already gated on `all(c is not None)`, but mypy
        # cannot narrow list comprehension elements; explicit cast.
        round(sum(c for c in components if c is not None) / len(components), 1)
        if all(c is not None for c in components)
        else None
    )

    return {
        "all_day_stress": _int("all_day_stress"),
        "body_battery_end_of_day": _int("body_battery"),
        "total_distance_m": _float("distance_m"),
        "moderate_intensity_min": _int("moderate_intensity_min"),
        "vigorous_intensity_min": _int("vigorous_intensity_min"),
        "garmin_acwr_ratio": garmin_acwr,
        "acwr_status": _str("acwr_status"),
        "training_readiness_level": _str("training_readiness_level"),
        "training_readiness_component_mean_pct": component_mean_pct,
        "training_readiness_sleep_pct": components[0],
        "training_readiness_hrv_pct": components[1],
        "training_readiness_stress_pct": components[2],
        "training_readiness_sleep_history_pct": components[3],
        "training_readiness_load_pct": components[4],
    }


def _coverage_fraction(*, as_of: date, dated_records: list[dict], window: int) -> float:
    """Fraction of the trailing `window` days (including as_of) with a record."""

    seen_dates: set[date] = set()
    for rec in dated_records:
        try:
            d = _coerce_date(rec["date"])
        except (KeyError, ValueError):
            continue
        if as_of - timedelta(days=window - 1) <= d <= as_of:
            seen_dates.add(d)
    return len(seen_dates) / float(window)


def _count_rhr_spike_days(*, as_of: date, history: list[dict], baseline: Optional[float]) -> int:
    """Consecutive trailing days (including today) where resting HR is >= 1.15 * baseline."""

    if baseline is None:
        return 0
    by_date = {d: rec["bpm"] for d, rec in _dedupe_by_date(history).items() if rec.get("bpm") is not None}
    threshold = baseline * WELL_ABOVE_RESTING_HR_RATIO
    days = 0
    cursor = as_of
    while True:
        bpm = by_date.get(cursor)
        if bpm is None or bpm < threshold:
            break
        days += 1
        cursor = cursor - timedelta(days=1)
    return days
