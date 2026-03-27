"""Daily readiness and recovery scoring from Garmin feature data plus local health logs."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from .thresholds import (
    READINESS_LABELS,
    SLEEP_THRESHOLDS,
    HRV_THRESHOLDS,
    RESTING_HR_THRESHOLDS,
    STRESS_THRESHOLDS,
    RECOVERY_THRESHOLDS,
    TRAINING_READINESS_THRESHOLDS,
)
from .recommendations import get_recommendation_text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FEATURES_PATH = PROJECT_ROOT / "data" / "garmin" / "model" / "daily_features.csv"
DB_PATH = PROJECT_ROOT / "data" / "health_log.db"


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _driver(signal: str, direction: str, note: str, points: int) -> dict:
    return {
        "signal": signal,
        "direction": direction,
        "note": note,
        "points": points,
    }


def _load_bot_context() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    daily = pd.read_sql_query(
        "SELECT date_for, total_calories, total_protein_g, total_carbs_g, total_fat_g, exercise_min FROM daily_summary ORDER BY date_for",
        conn,
    )

    subjective = pd.read_sql_query(
        "SELECT date_for, metric, value FROM subjective ORDER BY date_for",
        conn,
    )
    conn.close()

    if daily.empty:
        return pd.DataFrame()

    daily["date"] = pd.to_datetime(daily["date_for"], errors="coerce")
    daily = daily.drop(columns=["date_for"])

    if not subjective.empty:
        subjective["date"] = pd.to_datetime(subjective["date_for"], errors="coerce")
        piv = subjective.pivot_table(index="date", columns="metric", values="value", aggfunc="mean").reset_index()
        piv.columns.name = None
        daily = daily.merge(piv, on="date", how="left")

    if "total_calories" in daily.columns:
        daily["total_calories_3d_mean"] = daily["total_calories"].rolling(3, min_periods=1).mean()
    if "total_protein_g" in daily.columns:
        daily["total_protein_g_3d_mean"] = daily["total_protein_g"].rolling(3, min_periods=1).mean()

    return daily


def score_readiness_row(row: pd.Series) -> dict:
    score = 70
    drivers: list[dict] = []

    sleep_hrs = _safe_float(row.get("sleep_total_hrs"))
    sleep_debt = _safe_float(row.get("sleep_debt_hrs"))
    hrv = _safe_float(row.get("hrv_last_night"))
    hrv_weekly = _safe_float(row.get("hrv_weekly_avg"))
    resting_hr = _safe_float(row.get("resting_hr"))
    resting_hr_mean = _safe_float(row.get("resting_hr_7d_mean"))
    stress = _safe_float(row.get("stress_avg"))
    recovery_hrs = _safe_float(row.get("tr_recovery_time_hrs"))
    acute_load = _safe_float(row.get("tr_acute_load"))
    training_readiness = _safe_float(row.get("training_readiness_score"))
    total_calories = _safe_float(row.get("total_calories"))
    calories_3d_mean = _safe_float(row.get("total_calories_3d_mean"))
    protein = _safe_float(row.get("total_protein_g"))
    exercise_min = _safe_float(row.get("exercise_min"))
    energy = _safe_float(row.get("energy"))
    mood = _safe_float(row.get("mood"))
    soreness = _safe_float(row.get("soreness"))

    if sleep_hrs is not None:
        if sleep_hrs >= SLEEP_THRESHOLDS["good_hours"]:
            score += 10
            drivers.append(_driver("sleep_total_hrs", "positive", f"Slept {sleep_hrs:.1f}h", 10))
        elif sleep_hrs < SLEEP_THRESHOLDS["poor_hours"]:
            score -= 15
            drivers.append(_driver("sleep_total_hrs", "negative", f"Only {sleep_hrs:.1f}h sleep", -15))
        elif sleep_hrs < SLEEP_THRESHOLDS["ok_hours"]:
            score -= 6
            drivers.append(_driver("sleep_total_hrs", "negative", f"Sleep slightly short at {sleep_hrs:.1f}h", -6))

    if sleep_debt is not None:
        if sleep_debt >= SLEEP_THRESHOLDS["debt_good"]:
            score += 4
            drivers.append(_driver("sleep_debt_hrs", "positive", "Sleep need mostly covered", 4))
        elif sleep_debt <= SLEEP_THRESHOLDS["debt_bad"]:
            score -= 10
            drivers.append(_driver("sleep_debt_hrs", "negative", f"Sleep debt {abs(sleep_debt):.1f}h", -10))

    if hrv is not None and hrv_weekly is not None and hrv_weekly > 0:
        delta = hrv - hrv_weekly
        if delta >= 0:
            score += 10
            drivers.append(_driver("hrv_last_night", "positive", "HRV at or above weekly average", 10))
        elif delta <= HRV_THRESHOLDS["bad_delta"]:
            score -= 12
            drivers.append(_driver("hrv_last_night", "negative", f"HRV well below weekly average ({delta:.1f})", -12))
        elif delta <= HRV_THRESHOLDS["near_weekly_delta"]:
            score -= 5
            drivers.append(_driver("hrv_last_night", "negative", f"HRV slightly below weekly average ({delta:.1f})", -5))

    if resting_hr is not None and resting_hr_mean is not None:
        drift = resting_hr - resting_hr_mean
        if drift >= RESTING_HR_THRESHOLDS["bad_elevated"]:
            score -= 10
            drivers.append(_driver("resting_hr", "negative", f"Resting HR elevated by {drift:.1f} bpm", -10))
        elif drift >= RESTING_HR_THRESHOLDS["mild_elevated"]:
            score -= 5
            drivers.append(_driver("resting_hr", "negative", f"Resting HR mildly elevated by {drift:.1f} bpm", -5))

    if stress is not None:
        if stress >= STRESS_THRESHOLDS["high"]:
            score -= 10
            drivers.append(_driver("stress_avg", "negative", f"High average stress ({stress:.0f})", -10))
        elif stress >= STRESS_THRESHOLDS["moderate"]:
            score -= 4
            drivers.append(_driver("stress_avg", "negative", f"Moderate stress ({stress:.0f})", -4))

    if recovery_hrs is not None:
        if recovery_hrs >= RECOVERY_THRESHOLDS["high_recovery_hours"]:
            score -= 8
            drivers.append(_driver("tr_recovery_time_hrs", "negative", f"Recovery debt still high ({recovery_hrs:.0f}h)", -8))
        elif recovery_hrs <= RECOVERY_THRESHOLDS["low_recovery_hours"]:
            score += 3
            drivers.append(_driver("tr_recovery_time_hrs", "positive", f"Recovery debt low ({recovery_hrs:.0f}h)", 3))

    if acute_load is not None:
        if acute_load >= RECOVERY_THRESHOLDS["high_load"]:
            score -= 6
            drivers.append(_driver("tr_acute_load", "negative", f"High acute load ({acute_load:.0f})", -6))
        elif acute_load >= RECOVERY_THRESHOLDS["moderate_load"]:
            score -= 3
            drivers.append(_driver("tr_acute_load", "negative", f"Moderate acute load ({acute_load:.0f})", -3))

    if training_readiness is not None:
        if training_readiness >= TRAINING_READINESS_THRESHOLDS["good"]:
            score += 8
            drivers.append(_driver("training_readiness_score", "positive", f"Garmin readiness strong ({training_readiness:.0f})", 8))
        elif training_readiness <= TRAINING_READINESS_THRESHOLDS["poor"]:
            score -= 8
            drivers.append(_driver("training_readiness_score", "negative", f"Garmin readiness low ({training_readiness:.0f})", -8))

    if total_calories is not None and calories_3d_mean is not None and calories_3d_mean > 0:
        ratio = total_calories / calories_3d_mean
        if ratio < 0.7:
            score -= 6
            drivers.append(_driver("total_calories", "negative", "Calories materially below recent intake", -6))
        elif ratio > 0.9:
            score += 2
            drivers.append(_driver("total_calories", "positive", "Calories roughly in line with recent intake", 2))

    if protein is not None:
        if protein >= 120:
            score += 4
            drivers.append(_driver("total_protein_g", "positive", f"Protein intake solid ({protein:.0f}g)", 4))
        elif protein < 80:
            score -= 4
            drivers.append(_driver("total_protein_g", "negative", f"Protein intake low ({protein:.0f}g)", -4))

    if exercise_min is not None and exercise_min >= 90:
        score -= 3
        drivers.append(_driver("exercise_min", "negative", f"High logged exercise duration ({exercise_min:.0f} min)", -3))

    if energy is not None:
        if energy >= 8:
            score += 4
            drivers.append(_driver("energy", "positive", f"Self-reported energy strong ({energy:.1f}/10)", 4))
        elif energy <= 4:
            score -= 6
            drivers.append(_driver("energy", "negative", f"Self-reported energy low ({energy:.1f}/10)", -6))

    if mood is not None and mood <= 4:
        score -= 3
        drivers.append(_driver("mood", "negative", f"Mood lower than usual ({mood:.1f}/10)", -3))

    if soreness is not None and soreness >= 7:
        score -= 5
        drivers.append(_driver("soreness", "negative", f"Soreness elevated ({soreness:.1f}/10)", -5))

    score = max(0, min(100, int(round(score))))

    if score >= READINESS_LABELS["green"]["min_score"]:
        label_info = READINESS_LABELS["green"]
    elif score >= READINESS_LABELS["amber"]["min_score"]:
        label_info = READINESS_LABELS["amber"]
    else:
        label_info = READINESS_LABELS["red"]

    top_drivers = sorted(drivers, key=lambda d: abs(d["points"]), reverse=True)[:5]
    reason_summary = "; ".join(d["note"] for d in top_drivers) if top_drivers else "Insufficient data for strong readiness drivers."

    return {
        "date": str(pd.to_datetime(row.get("date")).date()) if row.get("date") is not None else None,
        "readiness_score": score,
        "readiness_label": label_info["label"],
        "recommendation": label_info["recommendation"],
        "recommendation_text": get_recommendation_text(label_info["recommendation"]),
        "reason_summary": reason_summary,
        "drivers": top_drivers,
    }


def load_features_df(path: Path = FEATURES_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bot = _load_bot_context()
    if not bot.empty:
        df = df.merge(bot, on="date", how="left")
    return df.sort_values("date").reset_index(drop=True)


def get_readiness_for_date(date_for: str | None = None, path: Path = FEATURES_PATH) -> dict:
    df = load_features_df(path)
    if df.empty:
        return {"status": "error", "message": "No feature data available."}

    if date_for is None:
        row = df.iloc[-1]
    else:
        target = pd.to_datetime(date_for, errors="coerce")
        match = df.loc[df["date"] == target]
        if match.empty:
            return {"status": "error", "message": f"No readiness data for {date_for}."}
        row = match.iloc[-1]

    result = score_readiness_row(row)
    result["status"] = "ok"
    return result


def build_all_readiness(path: Path = FEATURES_PATH) -> list[dict]:
    df = load_features_df(path)
    if df.empty:
        return []
    return [score_readiness_row(row) for _, row in df.iterrows()]
