"""
clean_garmin.py — Extract daily metrics from raw Garmin JSON files.

Reads each day's JSON from data/raw_daily_json/ and pulls out a flat row
of the most useful daily-level signals. Skips days with no real data.
Outputs: data/clean/daily_hybrid.csv
"""

import os
import json
import glob
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "garmin")
RAW_DIR = os.path.join(DATA_DIR, "raw_daily_json")
OUT_DIR = os.path.join(DATA_DIR, "clean")
os.makedirs(OUT_DIR, exist_ok=True)


def safe_get(d, *keys, default=None):
    """Nested dict access that never throws."""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        elif isinstance(d, list) and isinstance(k, int) and k < len(d):
            d = d[k]
        else:
            return default
        if d is None:
            return default
    return d


def extract_day(raw: dict) -> dict:
    """Pull a flat dict of daily metrics from a single day's raw JSON."""
    metrics = raw.get("metrics", {})
    row = {"date": raw["date"]}

    # ── Sleep ──────────────────────────────────────────────────────────
    sleep_data = safe_get(metrics, "sleep", "data", default={})
    dto = safe_get(sleep_data, "dailySleepDTO", default={})

    row["sleep_total_sec"] = dto.get("sleepTimeSeconds")
    row["sleep_deep_sec"] = dto.get("deepSleepSeconds")
    row["sleep_rem_sec"] = dto.get("remSleepSeconds")
    row["sleep_light_sec"] = dto.get("lightSleepSeconds")
    row["sleep_awake_sec"] = dto.get("awakeSleepSeconds")
    row["sleep_nap_sec"] = dto.get("napTimeSeconds")

    # Sleep score
    row["sleep_score"] = safe_get(dto, "sleepScores", "overall", "value")

    # Sleep stage percentages (from Garmin's own calculation)
    row["sleep_deep_pct"] = safe_get(dto, "sleepScores", "deepPercentage", "value")
    row["sleep_rem_pct"] = safe_get(dto, "sleepScores", "remPercentage", "value")
    row["sleep_light_pct"] = safe_get(dto, "sleepScores", "lightPercentage", "value")

    # Sleep physiology
    row["avg_sleep_stress"] = dto.get("avgSleepStress")
    row["avg_sleep_hr"] = dto.get("avgHeartRate")
    row["awake_count"] = dto.get("awakeCount")

    # SpO2 during sleep
    row["avg_spo2_sleep"] = dto.get("averageSpO2Value")
    row["min_spo2_sleep"] = dto.get("lowestSpO2Value")

    # Respiration during sleep
    row["avg_respiration_sleep"] = dto.get("averageRespirationValue")
    row["min_respiration_sleep"] = dto.get("lowestRespirationValue")
    row["max_respiration_sleep"] = dto.get("highestRespirationValue")

    # Sleep timing
    sleep_start = dto.get("sleepStartTimestampLocal")
    sleep_end = dto.get("sleepEndTimestampLocal")
    if sleep_start and sleep_end:
        # Convert ms timestamps to hours
        row["sleep_start_epoch"] = sleep_start
        row["sleep_end_epoch"] = sleep_end
        # Bed time as fractional hour (e.g. 23.5 = 11:30 PM)
        from datetime import datetime
        try:
            st = datetime.fromtimestamp(sleep_start / 1000)
            en = datetime.fromtimestamp(sleep_end / 1000)
            row["bed_time_hour"] = st.hour + st.minute / 60
            row["wake_time_hour"] = en.hour + en.minute / 60
        except (OSError, ValueError):
            pass

    # Sleep need
    row["sleep_need_min"] = safe_get(dto, "sleepNeed", "actual")
    row["sleep_need_baseline_min"] = safe_get(dto, "sleepNeed", "baseline")

    # Sleep feedback
    row["sleep_feedback"] = dto.get("sleepScoreFeedback")
    row["sleep_insight"] = dto.get("sleepScoreInsight")
    row["breathing_disruption"] = dto.get("breathingDisruptionSeverity")

    # ── Stress ─────────────────────────────────────────────────────────
    stress_data = safe_get(metrics, "stress", "data", default={})
    if isinstance(stress_data, dict):
        row["stress_avg"] = stress_data.get("avgStressLevel")
        row["stress_max"] = stress_data.get("maxStressLevel")

    # ── Heart Rate ─────────────────────────────────────────────────────
    hr_data = safe_get(metrics, "heart_rate", "data", default={})
    if isinstance(hr_data, dict):
        row["resting_hr"] = hr_data.get("restingHeartRate")
        row["resting_hr_7d_garmin"] = hr_data.get("lastSevenDaysAvgRestingHeartRate")
        row["max_hr_day"] = hr_data.get("maxHeartRate")
        row["min_hr_day"] = hr_data.get("minHeartRate")

    # ── HRV ────────────────────────────────────────────────────────────
    hrv_data = safe_get(metrics, "hrv", "data", default={})
    hrv_summary = safe_get(hrv_data, "hrvSummary", default={})
    row["hrv_last_night"] = hrv_summary.get("lastNightAvg")
    row["hrv_last_night_5min_high"] = hrv_summary.get("lastNight5MinHigh")
    row["hrv_weekly_avg"] = hrv_summary.get("weeklyAvg")
    row["hrv_status"] = hrv_summary.get("status")

    # Also grab from sleep DTO (sometimes more reliable)
    if row["hrv_last_night"] is None:
        row["hrv_last_night"] = safe_get(sleep_data, "avgOvernightHrv")

    # ── Body Battery ───────────────────────────────────────────────────
    bb_data = safe_get(metrics, "body_battery", "data", default=[])
    if isinstance(bb_data, list) and bb_data:
        bb = bb_data[0]
        row["body_battery_charged"] = bb.get("charged")
        row["body_battery_drained"] = bb.get("drained")
    # Also from sleep DTO
    row["body_battery_change_sleep"] = safe_get(sleep_data, "bodyBatteryChange")

    # ── RHR (separate endpoint, fallback) ──────────────────────────────
    rhr_data = safe_get(metrics, "rhr", "data", default={})
    if isinstance(rhr_data, dict) and row.get("resting_hr") is None:
        row["resting_hr"] = safe_get(rhr_data, "allMetrics", "metricsMap", "WELLNESS_RESTING_HEART_RATE", 0, "value")

    # ── SpO2 (daily endpoint) ──────────────────────────────────────────
    spo2_data = safe_get(metrics, "spo2", "data", default={})
    if isinstance(spo2_data, dict) and row.get("avg_spo2_sleep") is None:
        row["avg_spo2_sleep"] = spo2_data.get("averageSpO2")

    # ── Respiration (daily endpoint) ───────────────────────────────────
    resp_data = safe_get(metrics, "respiration", "data", default={})
    if isinstance(resp_data, dict):
        if row.get("min_respiration_sleep") is None:
            row["min_respiration_sleep"] = resp_data.get("lowestRespirationValue")
        if row.get("max_respiration_sleep") is None:
            row["max_respiration_sleep"] = resp_data.get("highestRespirationValue")
        if row.get("avg_respiration_sleep") is None:
            row["avg_respiration_sleep"] = resp_data.get("avgSleepRespirationValue")

    # ── Training Readiness ─────────────────────────────────────────────
    tr_data = safe_get(metrics, "training_readiness", "data", default=[])
    if isinstance(tr_data, list) and tr_data:
        tr = tr_data[0]
        row["training_readiness_score"] = tr.get("score")
        row["training_readiness_level"] = tr.get("level")
        row["tr_sleep_score_pct"] = tr.get("sleepScoreFactorPercent")
        row["tr_recovery_time_hrs"] = tr.get("recoveryTime")
        row["tr_recovery_pct"] = tr.get("recoveryTimeFactorPercent")
        row["tr_acwr_pct"] = tr.get("acwrFactorPercent")
        row["tr_acute_load"] = tr.get("acuteLoad")
        row["tr_stress_history_pct"] = tr.get("stressHistoryFactorPercent")
        row["tr_hrv_pct"] = tr.get("hrvFactorPercent")
        row["tr_sleep_history_pct"] = tr.get("sleepHistoryFactorPercent")

    # ── Training Status / VO2 Max ──────────────────────────────────────
    ts_data = safe_get(metrics, "training_status", "data", default={})
    if isinstance(ts_data, dict):
        row["vo2max"] = safe_get(ts_data, "mostRecentVO2Max", "generic", "vo2MaxPreciseValue")
        row["training_status"] = safe_get(ts_data, "mostRecentTrainingStatus", "mostRecentTrainingStatus")

    # ── Endurance Score ────────────────────────────────────────────────
    es_data = safe_get(metrics, "endurance_score", "data", default={})
    if isinstance(es_data, dict):
        es_dto = es_data.get("enduranceScoreDTO")
        if isinstance(es_dto, dict):
            row["endurance_score"] = es_dto.get("overallScore")

    return row


def main():
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.json")))
    rows = []

    for fpath in files:
        with open(fpath, "r") as f:
            raw = json.load(f)
        row = extract_day(raw)
        rows.append(row)

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)

    # Convert seconds to hours for readability
    sec_cols = [c for c in df.columns if c.endswith("_sec")]
    for c in sec_cols:
        hr_col = c.replace("_sec", "_hrs")
        df[hr_col] = pd.to_numeric(df[c], errors="coerce") / 3600
    df.drop(columns=sec_cols, inplace=True)

    # Drop rows with no real sleep data (pre-watch period)
    core_cols = ["sleep_total_hrs", "resting_hr", "hrv_last_night", "sleep_score"]
    has_data = df[core_cols].notna().any(axis=1)
    first_valid = df.loc[has_data, "date"].min()
    if pd.notna(first_valid):
        df = df[df["date"] >= first_valid].copy()
        df = df.reset_index(drop=True)

    # ── Rolling averages (7-day) ───────────────────────────────────────
    roll_cols = [
        "sleep_total_hrs", "sleep_score", "resting_hr",
        "hrv_last_night", "stress_avg", "training_readiness_score",
    ]
    for col in roll_cols:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce")
            df[f"{col}_7d_avg"] = s.rolling(7, min_periods=3).mean()

    # ── Readiness flag ─────────────────────────────────────────────────
    def flag(row):
        r = row.get("training_readiness_score")
        s = row.get("sleep_total_hrs")
        if pd.notna(r) and r < 50:
            return "red"
        if pd.notna(s) and s < 6:
            return "red"
        if pd.notna(r) and r >= 75 and pd.notna(s) and s >= 7:
            return "green"
        return "amber"

    df["readiness_flag"] = df.apply(flag, axis=1)

    out_path = os.path.join(OUT_DIR, "daily_hybrid.csv")
    df.to_csv(out_path, index=False)

    print(f"Wrote {len(df)} rows -> {out_path}")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"\nNon-null counts (top 30):")
    print(df.select_dtypes(include="number").notna().sum().sort_values(ascending=False).head(30))


if __name__ == "__main__":
    main()
