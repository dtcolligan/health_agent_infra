"""CLEAN layer.

Consumes PULL-shaped raw inputs and emits a single CleanedEvidence object.
Deterministic, no interpretation, no recommendation.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Iterable, Optional

from health_model.recovery_readiness_v1.schemas import CleanedEvidence


def _coerce_date(value) -> date:
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)).date()


def _mean(values: Iterable[float]) -> Optional[float]:
    values = [v for v in values if v is not None]
    if not values:
        return None
    return sum(values) / len(values)


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
    """Turn raw source-shaped records into a typed CleanedEvidence object.

    Each raw-input collection is expected to be pre-pulled PULL-layer material:
    a dict for single records, a list of dicts for rolling windows. Missing
    values resolve to None in the cleaned object; the STATE layer is
    responsible for mapping None to `unknown` enums and raising uncertainty
    tokens.
    """

    as_of = _coerce_date(as_of_date)

    sleep_hours = None
    sleep_record_id = None
    if garmin_sleep:
        sleep_hours = garmin_sleep.get("duration_hours")
        sleep_record_id = garmin_sleep.get("record_id")

    rhr_latest = _dedupe_by_date(garmin_resting_hr_recent)
    today_rhr = None
    today_rhr_id = None
    rhr_history: list[float] = []
    for rec_date, rec in sorted(rhr_latest.items()):
        if rec_date == as_of:
            today_rhr = rec.get("bpm")
            today_rhr_id = rec.get("record_id")
        elif as_of - timedelta(days=14) <= rec_date < as_of:
            if rec.get("bpm") is not None:
                rhr_history.append(rec["bpm"])
    rhr_baseline = _mean(rhr_history)

    hrv_latest = _dedupe_by_date(garmin_hrv_recent)
    today_hrv = None
    today_hrv_id = None
    hrv_history: list[float] = []
    for rec_date, rec in sorted(hrv_latest.items()):
        if rec_date == as_of:
            today_hrv = rec.get("rmssd_ms")
            today_hrv_id = rec.get("record_id")
        elif as_of - timedelta(days=14) <= rec_date < as_of:
            if rec.get("rmssd_ms") is not None:
                hrv_history.append(rec["rmssd_ms"])
    hrv_baseline = _mean(hrv_history)

    load_values: list[float] = []
    for rec in garmin_training_load_7d:
        rec_date = _coerce_date(rec["date"])
        if as_of - timedelta(days=7) <= rec_date <= as_of:
            if rec.get("load") is not None:
                load_values.append(rec["load"])
    trailing_load = sum(load_values) if load_values else None

    older_values: list[float] = []
    for rec in garmin_training_load_7d:
        rec_date = _coerce_date(rec["date"])
        if as_of - timedelta(days=28) <= rec_date < as_of - timedelta(days=7):
            if rec.get("load") is not None:
                older_values.append(rec["load"])
    load_baseline_weekly = None
    if older_values:
        load_baseline_weekly = (sum(older_values) / len(older_values)) * 7 / max(len(older_values), 1)
        load_baseline_weekly = sum(older_values) / 3.0 if len(older_values) >= 21 else sum(older_values) / max(len(older_values) / 7.0, 1)

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

    spike_days = _count_rhr_spike_days(
        as_of=as_of, history=garmin_resting_hr_recent, baseline=rhr_baseline
    )

    return CleanedEvidence(
        as_of_date=as_of,
        user_id=user_id,
        sleep_hours=sleep_hours,
        sleep_record_id=sleep_record_id,
        resting_hr=today_rhr,
        resting_hr_record_id=today_rhr_id,
        resting_hr_baseline=rhr_baseline,
        hrv_ms=today_hrv,
        hrv_record_id=today_hrv_id,
        hrv_baseline=hrv_baseline,
        trailing_7d_training_load=trailing_load,
        training_load_baseline=load_baseline_weekly,
        soreness_self_report=soreness,
        energy_self_report=energy,
        planned_session_type=planned,
        manual_readiness_submission_id=manual_id,
        active_goal=active_goal,
        optional_context_note_ids=note_ids,
        resting_hr_spike_days=spike_days,
    )


def _dedupe_by_date(records: list[dict]) -> dict[date, dict]:
    """Map each record date to the last record seen for that date."""

    result: dict[date, dict] = {}
    for rec in records:
        result[_coerce_date(rec["date"])] = rec
    return result


WELL_ABOVE_RESTING_HR_RATIO = 1.15


def _count_rhr_spike_days(*, as_of: date, history: list[dict], baseline: Optional[float]) -> int:
    """Consecutive trailing days (including today) where resting HR is well_above baseline.

    The threshold matches the STATE layer's `well_above` band for resting HR
    (ratio >= 1.15), so this count and state.resting_hr_vs_baseline agree on
    what "well above" means.
    """

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
