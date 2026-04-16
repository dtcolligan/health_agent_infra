"""Synthetic PULL-shaped fixtures for demonstrating the flagship loop."""

from __future__ import annotations

from datetime import date, timedelta


def baseline_week(as_of: date, *, rhr_bpm: float = 52.0, hrv_ms: float = 70.0) -> tuple[list[dict], list[dict]]:
    """Return trailing 14-day resting HR and HRV series, stable at baseline."""

    rhr = []
    hrv = []
    for offset in range(14, 0, -1):
        d = as_of - timedelta(days=offset)
        rhr.append({"date": d.isoformat(), "bpm": rhr_bpm, "record_id": f"g_rhr_{d.isoformat()}"})
        hrv.append({"date": d.isoformat(), "rmssd_ms": hrv_ms, "record_id": f"g_hrv_{d.isoformat()}"})
    return rhr, hrv


def _load_week(as_of: date, *, daily_load: float) -> list[dict]:
    records = []
    for offset in range(28, -1, -1):
        d = as_of - timedelta(days=offset)
        records.append({"date": d.isoformat(), "load": daily_load, "record_id": f"g_load_{d.isoformat()}"})
    return records


def garmin_pull_fixture(
    as_of: date,
    *,
    scenario: str = "mildly_impaired_with_hard_plan",
) -> dict:
    """Return a raw-shaped Garmin bundle for the given scenario.

    Scenarios:
        - recovered_with_easy_plan
        - mildly_impaired_with_hard_plan
        - impaired_with_hard_plan
        - rhr_spike_three_days
        - insufficient_signal (missing sleep)
        - sparse_signal (missing hrv + low rhr data)
    """

    rhr_series, hrv_series = baseline_week(as_of)
    load_series = _load_week(as_of, daily_load=70.0)

    sleep = {
        "record_id": f"g_sleep_{(as_of - timedelta(days=0)).isoformat()}",
        "duration_hours": 7.8,
    }

    if scenario == "recovered_with_easy_plan":
        rhr_series.append({"date": as_of.isoformat(), "bpm": 51.0, "record_id": f"g_rhr_{as_of.isoformat()}"})
        hrv_series.append({"date": as_of.isoformat(), "rmssd_ms": 72.0, "record_id": f"g_hrv_{as_of.isoformat()}"})
        return {
            "sleep": sleep,
            "resting_hr": rhr_series,
            "hrv": hrv_series,
            "training_load": load_series,
        }

    if scenario == "mildly_impaired_with_hard_plan":
        sleep["duration_hours"] = 7.0
        rhr_series.append({"date": as_of.isoformat(), "bpm": 55.0, "record_id": f"g_rhr_{as_of.isoformat()}"})
        hrv_series.append({"date": as_of.isoformat(), "rmssd_ms": 66.0, "record_id": f"g_hrv_{as_of.isoformat()}"})
        for rec in load_series[-7:]:
            rec["load"] = 85.0
        return {
            "sleep": sleep,
            "resting_hr": rhr_series,
            "hrv": hrv_series,
            "training_load": load_series,
        }

    if scenario == "impaired_with_hard_plan":
        sleep["duration_hours"] = 5.4
        rhr_series.append({"date": as_of.isoformat(), "bpm": 62.0, "record_id": f"g_rhr_{as_of.isoformat()}"})
        hrv_series.append({"date": as_of.isoformat(), "rmssd_ms": 52.0, "record_id": f"g_hrv_{as_of.isoformat()}"})
        for rec in load_series[-7:]:
            rec["load"] = 140.0
        return {
            "sleep": sleep,
            "resting_hr": rhr_series,
            "hrv": hrv_series,
            "training_load": load_series,
        }

    if scenario == "rhr_spike_three_days":
        for offset in range(0, 3):
            d = as_of - timedelta(days=offset)
            rhr_series.append(
                {"date": d.isoformat(), "bpm": 64.0, "record_id": f"g_rhr_{d.isoformat()}"}
            )
            hrv_series.append(
                {"date": d.isoformat(), "rmssd_ms": 62.0, "record_id": f"g_hrv_{d.isoformat()}"}
            )
        return {
            "sleep": sleep,
            "resting_hr": rhr_series,
            "hrv": hrv_series,
            "training_load": load_series,
        }

    if scenario == "insufficient_signal":
        return {
            "sleep": None,
            "resting_hr": rhr_series,
            "hrv": hrv_series,
            "training_load": load_series,
        }

    if scenario == "sparse_signal":
        return {
            "sleep": sleep,
            "resting_hr": rhr_series,
            "hrv": [],
            "training_load": load_series,
        }

    raise ValueError(f"unknown scenario: {scenario}")


def manual_readiness_fixture(as_of: date, *, scenario: str) -> dict | None:
    """Return the matching manual readiness intake for the scenario."""

    common = {
        "submission_id": f"m_ready_{as_of.isoformat()}",
        "active_goal": "spring_10k_base_build",
    }

    if scenario == "recovered_with_easy_plan":
        return {**common, "soreness": "low", "energy": "high", "planned_session_type": "easy"}
    if scenario == "mildly_impaired_with_hard_plan":
        return {**common, "soreness": "moderate", "energy": "moderate", "planned_session_type": "hard"}
    if scenario == "impaired_with_hard_plan":
        return {**common, "soreness": "high", "energy": "low", "planned_session_type": "hard"}
    if scenario == "rhr_spike_three_days":
        return {**common, "soreness": "moderate", "energy": "moderate", "planned_session_type": "moderate"}
    if scenario == "insufficient_signal":
        return None
    if scenario == "sparse_signal":
        return {**common, "soreness": "moderate", "energy": "moderate", "planned_session_type": "moderate"}
    raise ValueError(f"unknown scenario: {scenario}")
