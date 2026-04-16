"""Adapter from the committed Garmin CSV export into recovery_readiness_v1 shape.

The flagship loop consumes evidence through ``clean_inputs()``, which accepts a
fixed dict shape (see ``clean.health_model.recovery_readiness_v1.clean``).
This adapter reads the already-committed offline Garmin export under
``pull/data/garmin/export/`` and emits that same shape, so the flagship can run
end-to-end on real evidence without changing any downstream schema or logic.

Bounds per the Phase 2 plan:
    - no live API calls
    - no new credentials
    - no new contracts — adapter-only
    - one source, one day, one user
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd


DEFAULT_EXPORT_DIR = Path(__file__).resolve().parents[2] / "pull" / "data" / "garmin" / "export"


def load_recovery_readiness_inputs(
    as_of: date,
    *,
    export_dir: Optional[Path] = None,
    history_days: int = 14,
) -> dict:
    """Return a PULL-shaped dict compatible with ``clean_inputs()``.

    Args:
        as_of: the target date for the flagship run.
        export_dir: directory containing ``daily_summary_export.csv``. Defaults
            to the repo-local committed export.
        history_days: trailing window used for baselines and training load.

    Returns:
        ``{"sleep": {...} | None, "resting_hr": [...], "hrv": [...],
           "training_load": [...]}``, matching the synthetic fixture shape.
    """

    export_dir = export_dir or DEFAULT_EXPORT_DIR
    daily_summary_path = export_dir / "daily_summary_export.csv"
    if not daily_summary_path.exists():
        raise FileNotFoundError(f"daily_summary_export.csv not found in {export_dir}")

    df = pd.read_csv(daily_summary_path)
    df["date"] = pd.to_datetime(df["date"]).dt.date

    window_start = as_of - timedelta(days=history_days)
    window = df[(df["date"] >= window_start) & (df["date"] <= as_of)].copy()
    window = window.sort_values("date")

    sleep = _extract_sleep(window, as_of)
    resting_hr = _series_from_column(window, column="resting_hr", out_field="bpm", record_prefix="g_rhr")
    hrv = _series_from_column(window, column="health_hrv_value", out_field="rmssd_ms", record_prefix="g_hrv")
    training_load = _series_from_column(window, column="acute_load", out_field="load", record_prefix="g_load")

    return {
        "sleep": sleep,
        "resting_hr": resting_hr,
        "hrv": hrv,
        "training_load": training_load,
    }


def _extract_sleep(window: pd.DataFrame, as_of: date) -> Optional[dict]:
    as_of_rows = window[window["date"] == as_of]
    if len(as_of_rows) != 1:
        return None
    row = as_of_rows.iloc[0]
    total_sec = 0.0
    seen = False
    for col in ("sleep_deep_sec", "sleep_light_sec", "sleep_rem_sec"):
        v = row.get(col)
        if pd.notna(v):
            total_sec += float(v)
            seen = True
    if not seen or total_sec <= 0:
        return None
    return {
        "record_id": f"g_sleep_{as_of.isoformat()}",
        "duration_hours": round(total_sec / 3600.0, 2),
    }


def _series_from_column(
    window: pd.DataFrame,
    *,
    column: str,
    out_field: str,
    record_prefix: str,
) -> list[dict]:
    out: list[dict] = []
    for _, row in window.iterrows():
        v = row.get(column)
        if not pd.notna(v) or v == 0:
            continue
        d = row["date"].isoformat()
        out.append({"date": d, out_field: float(v), "record_id": f"{record_prefix}_{d}"})
    return out


def default_manual_readiness(
    as_of: date,
    *,
    active_goal: str = "spring_10k_base_build",
    soreness: str = "moderate",
    energy: str = "moderate",
    planned_session_type: str = "moderate",
) -> dict:
    """Return a neutral manual readiness intake for the real-slice capture.

    Real manual readiness comes from a typed intake surface in a production
    flow. For the Phase 2 proof capture, a neutral default lets the flagship
    run end-to-end over real Garmin evidence without fabricating subjective
    detail.
    """

    return {
        "submission_id": f"m_ready_real_{as_of.isoformat()}",
        "active_goal": active_goal,
        "soreness": soreness,
        "energy": energy,
        "planned_session_type": planned_session_type,
    }
