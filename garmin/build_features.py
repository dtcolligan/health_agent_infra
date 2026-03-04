"""
build_features.py — Build ML-ready feature set from clean daily + activity data.

Reads: data/clean/daily_hybrid.csv, data/activities.csv
Outputs: data/model/daily_features.csv
"""

import os
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "garmin")
CLEAN_PATH = os.path.join(DATA_DIR, "clean", "daily_hybrid.csv")
ACTIVITIES_PATH = os.path.join(DATA_DIR, "activities.csv")
OUT_DIR = os.path.join(DATA_DIR, "model")
os.makedirs(OUT_DIR, exist_ok=True)


def rolling_slope(y: pd.Series) -> float:
    """Slope of linear fit over rolling window index."""
    y = pd.to_numeric(y, errors="coerce").dropna()
    n = len(y)
    if n < 4:
        return np.nan
    x = np.arange(n)
    return float(np.cov(x, y, bias=True)[0, 1] / np.var(x))


def aggregate_activities(act_path: str) -> pd.DataFrame:
    """Aggregate activities to one row per calendar day."""
    if not os.path.exists(act_path):
        return pd.DataFrame(columns=["date"])

    act = pd.read_csv(act_path)
    act["date"] = pd.to_datetime(act["startTimeLocal"], errors="coerce").dt.date
    act["date"] = pd.to_datetime(act["date"])

    # Distance in km
    act["distance_km"] = pd.to_numeric(act.get("distance", pd.Series(dtype=float)), errors="coerce") / 1000
    act["duration_min"] = pd.to_numeric(act.get("duration", pd.Series(dtype=float)), errors="coerce") / 60
    act["calories"] = pd.to_numeric(act.get("calories", pd.Series(dtype=float)), errors="coerce")
    act["averageHR"] = pd.to_numeric(act.get("averageHR", pd.Series(dtype=float)), errors="coerce")
    act["maxHR"] = pd.to_numeric(act.get("maxHR", pd.Series(dtype=float)), errors="coerce")
    act["training_load"] = pd.to_numeric(act.get("activityTrainingLoad", pd.Series(dtype=float)), errors="coerce")
    act["training_effect"] = pd.to_numeric(act.get("aerobicTrainingEffect", pd.Series(dtype=float)), errors="coerce")
    act["elevation_gain"] = pd.to_numeric(act.get("elevationGain", pd.Series(dtype=float)), errors="coerce")
    act["vigorous_min"] = pd.to_numeric(act.get("vigorousIntensityMinutes", pd.Series(dtype=float)), errors="coerce")
    act["moderate_min"] = pd.to_numeric(act.get("moderateIntensityMinutes", pd.Series(dtype=float)), errors="coerce")

    # Activity type
    act["activity_type"] = act.get("activityType.typeKey", pd.Series(dtype=str))

    daily = act.groupby("date").agg(
        act_count=("distance_km", "count"),
        act_total_distance_km=("distance_km", "sum"),
        act_total_duration_min=("duration_min", "sum"),
        act_total_calories=("calories", "sum"),
        act_avg_hr=("averageHR", "mean"),
        act_max_hr=("maxHR", "max"),
        act_total_training_load=("training_load", "sum"),
        act_max_training_effect=("training_effect", "max"),
        act_total_elevation_m=("elevation_gain", "sum"),
        act_vigorous_min=("vigorous_min", "sum"),
        act_moderate_min=("moderate_min", "sum"),
    ).reset_index()

    # Primary activity type for the day (longest duration)
    primary = act.sort_values("duration_min", ascending=False).groupby("date")["activity_type"].first().reset_index()
    primary.columns = ["date", "act_primary_type"]
    daily = daily.merge(primary, on="date", how="left")

    return daily


def main():
    df = pd.read_csv(CLEAN_PATH)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)

    feats = pd.DataFrame()
    feats["date"] = df["date"]

    # ── Calendar features ──────────────────────────────────────────────
    feats["dow"] = df["date"].dt.dayofweek  # 0=Mon
    feats["is_weekend"] = feats["dow"].isin([5, 6]).astype(int)
    feats["week"] = df["date"].dt.isocalendar().week.astype(int)
    feats["month"] = df["date"].dt.month
    feats["days_since_start"] = (df["date"] - df["date"].min()).dt.days

    # ── Core daily signals ─────────────────────────────────────────────
    daily_cols = [
        "sleep_total_hrs", "sleep_deep_hrs", "sleep_rem_hrs",
        "sleep_light_hrs", "sleep_awake_hrs", "sleep_nap_hrs",
        "sleep_score", "sleep_deep_pct", "sleep_rem_pct", "sleep_light_pct",
        "avg_sleep_stress", "avg_sleep_hr", "awake_count",
        "avg_spo2_sleep", "min_spo2_sleep",
        "avg_respiration_sleep", "min_respiration_sleep",
        "resting_hr", "max_hr_day", "min_hr_day",
        "hrv_last_night", "hrv_last_night_5min_high", "hrv_weekly_avg",
        "body_battery_charged", "body_battery_drained",
        "stress_avg", "stress_max",
        "training_readiness_score",
        "tr_recovery_time_hrs", "tr_acute_load", "tr_acwr_pct",
        "vo2max",
        "bed_time_hour", "wake_time_hour",
    ]
    for c in daily_cols:
        if c in df.columns:
            feats[c] = pd.to_numeric(df[c], errors="coerce")

    # ── Derived sleep metrics ──────────────────────────────────────────
    if "sleep_total_hrs" in feats.columns and "sleep_need_min" in df.columns:
        need_hrs = pd.to_numeric(df["sleep_need_min"], errors="coerce") / 60
        feats["sleep_debt_hrs"] = feats["sleep_total_hrs"] - need_hrs

    if "body_battery_charged" in feats.columns and "body_battery_drained" in feats.columns:
        feats["body_battery_net"] = feats["body_battery_charged"] - feats["body_battery_drained"]

    # ── Rolling stats (7d, backward-looking) ───────────────────────────
    roll_cols = [
        "sleep_total_hrs", "sleep_score", "resting_hr",
        "hrv_last_night", "stress_avg", "training_readiness_score",
    ]
    for c in roll_cols:
        if c in feats.columns:
            s = feats[c]
            feats[f"{c}_7d_mean"] = s.rolling(7, min_periods=4).mean()
            feats[f"{c}_7d_std"] = s.rolling(7, min_periods=4).std()
            feats[f"{c}_7d_slope"] = s.rolling(7, min_periods=4).apply(rolling_slope, raw=False)

    # ── Lag features (yesterday) ───────────────────────────────────────
    lag_cols = ["sleep_total_hrs", "sleep_score", "resting_hr", "hrv_last_night", "stress_avg"]
    for c in lag_cols:
        if c in feats.columns:
            feats[f"{c}_lag1"] = feats[c].shift(1)

    # ── Day-over-day deltas ────────────────────────────────────────────
    for c in ["resting_hr", "hrv_last_night", "stress_avg"]:
        if c in feats.columns:
            feats[f"{c}_delta"] = feats[c].diff()

    # ── Merge activity data ────────────────────────────────────────────
    act_daily = aggregate_activities(ACTIVITIES_PATH)
    if not act_daily.empty:
        feats = feats.merge(act_daily, on="date", how="left")
        # Fill missing activity days with 0
        act_num_cols = [c for c in act_daily.columns if c != "date" and c != "act_primary_type"]
        for c in act_num_cols:
            if c in feats.columns:
                feats[c] = feats[c].fillna(0)

        # Rolling training load (7d cumulative)
        if "act_total_training_load" in feats.columns:
            feats["training_load_7d_sum"] = feats["act_total_training_load"].rolling(7, min_periods=1).sum()
            feats["training_load_7d_avg"] = feats["act_total_training_load"].rolling(7, min_periods=1).mean()

    # ── Target columns (next day) ──────────────────────────────────────
    if "readiness_flag" in df.columns:
        feats["target_readiness_flag_tomorrow"] = df["readiness_flag"].shift(-1)
    for c in ["sleep_total_hrs", "resting_hr", "sleep_score"]:
        if c in feats.columns:
            feats[f"target_{c}_tomorrow"] = feats[c].shift(-1)

    out_path = os.path.join(OUT_DIR, "daily_features.csv")
    feats.to_csv(out_path, index=False)
    print(f"Wrote {len(feats)} rows, {len(feats.columns)} columns -> {out_path}")
    print(f"\nColumn groups:")
    print(f"  Calendar: {len([c for c in feats.columns if c in ['dow','is_weekend','week','month','days_since_start']])}")
    print(f"  Sleep: {len([c for c in feats.columns if 'sleep' in c and 'target' not in c])}")
    print(f"  HR/HRV: {len([c for c in feats.columns if 'hr' in c.lower() or 'hrv' in c.lower()])}")
    print(f"  Activity: {len([c for c in feats.columns if c.startswith('act_') or 'training_load' in c])}")
    print(f"  Rolling/Lag: {len([c for c in feats.columns if '7d' in c or 'lag' in c or 'delta' in c])}")
    print(f"  Targets: {len([c for c in feats.columns if c.startswith('target_')])}")


if __name__ == "__main__":
    main()
