"""
export_data.py — Export health data to JSON for the dashboard.

Reads from:
  - data/clean/daily_hybrid.csv  (Garmin metrics)
  - data/activities.csv          (Garmin activities)
  - data/health_log.db           (Telegram bot nutrition data)

Outputs:
  - dashboard/dashboard_data.json

Run: python -m dashboard.export_data
"""

import csv
import json
import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_PATH = BASE_DIR / "dashboard" / "dashboard_data.json"

from garmin.readiness import build_all_readiness


def _read_csv(path: Path) -> list[dict]:
    """Read a CSV file into a list of dicts, converting numeric strings."""
    if not path.exists():
        return []
    with open(path) as f:
        rows = list(csv.DictReader(f))
    # Convert numeric-looking values
    for row in rows:
        for k, v in row.items():
            if v in ("", "None", None):
                row[k] = None
            else:
                try:
                    row[k] = float(v)
                    if row[k] == int(row[k]):
                        row[k] = int(row[k])
                except (ValueError, TypeError):
                    pass
    return rows


def _read_bot_db() -> dict:
    """Read nutrition and exercise data from the bot's SQLite database."""
    db_path = DATA_DIR / "health_log.db"
    if not db_path.exists():
        return {"daily_summaries": [], "meal_items": [], "exercises": [], "targets": {}}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    summaries = [dict(r) for r in conn.execute(
        "SELECT * FROM daily_summary ORDER BY date_for"
    ).fetchall()]

    meals = [dict(r) for r in conn.execute(
        "SELECT date_for, meal_type, item_name, calories, protein_g, carbs_g, fat_g "
        "FROM meal_items ORDER BY date_for, id"
    ).fetchall()]

    exercises = [dict(r) for r in conn.execute(
        "SELECT date_for, exercise_type, subtype, duration_min, intensity, calories_est "
        "FROM exercises ORDER BY date_for, id"
    ).fetchall()]

    # Exercise sets
    exercise_sets = []
    try:
        exercise_sets = [dict(r) for r in conn.execute(
            """SELECT es.date_for, e.exercise_type, e.subtype,
                      es.set_number, es.reps, es.weight_kg, es.is_pr
               FROM exercise_sets es
               JOIN exercises e ON e.id = es.exercise_id
               ORDER BY es.date_for, es.exercise_id, es.set_number"""
        ).fetchall()]
    except sqlite3.OperationalError:
        pass  # table might not exist yet

    # Gym daily summary
    gym_daily = []
    try:
        gym_daily = [dict(r) for r in conn.execute(
            """SELECT e.date_for,
                      COALESCE(SUM(e.duration_min), 0) AS total_duration,
                      COALESCE(SUM(es.weight_kg * es.reps), 0) AS total_volume,
                      COUNT(es.id) AS total_sets,
                      COALESCE(SUM(es.is_pr), 0) AS pr_count
               FROM exercises e
               LEFT JOIN exercise_sets es ON es.exercise_id = e.id
               GROUP BY e.date_for
               ORDER BY e.date_for"""
        ).fetchall()]
    except sqlite3.OperationalError:
        pass

    targets = {}
    try:
        for r in conn.execute("SELECT metric, value FROM targets").fetchall():
            targets[r["metric"]] = r["value"]
    except sqlite3.OperationalError:
        pass  # targets table might not exist yet

    conn.close()
    return {
        "daily_summaries": summaries,
        "meal_items": meals,
        "exercises": exercises,
        "exercise_sets": exercise_sets,
        "gym_daily": gym_daily,
        "targets": targets,
    }


def export():
    garmin_daily = _read_csv(DATA_DIR / "garmin" / "clean" / "daily_hybrid.csv")
    activities = _read_csv(DATA_DIR / "garmin" / "activities.csv")

    # Trim activities to relevant fields
    trimmed_activities = []
    for a in activities:
        trimmed_activities.append({
            "name": a.get("activityName"),
            "date": str(a.get("startTimeLocal", ""))[:10],
            "distance_km": round(a.get("distance", 0) / 1000, 2) if a.get("distance") else None,
            "duration_min": round(a.get("duration", 0) / 60, 1) if a.get("duration") else None,
            "calories": a.get("calories"),
            "avg_hr": a.get("averageHR"),
            "max_hr": a.get("maxHR"),
            "training_effect": a.get("aerobicTrainingEffect"),
        })

    bot_data = _read_bot_db()
    readiness = build_all_readiness()

    data = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "garmin_daily": garmin_daily,
        "readiness": readiness,
        "activities": trimmed_activities,
        "nutrition": bot_data["daily_summaries"],
        "meal_items": bot_data["meal_items"],
        "bot_exercises": bot_data["exercises"],
        "exercise_sets": bot_data["exercise_sets"],
        "gym_daily": bot_data["gym_daily"],
        "targets": bot_data["targets"],
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)

    print(f"Exported to {OUTPUT_PATH}")
    print(f"  Garmin daily: {len(garmin_daily)} days")
    print(f"  Activities: {len(trimmed_activities)}")
    print(f"  Nutrition days: {len(bot_data['daily_summaries'])}")
    print(f"  Meal items: {len(bot_data['meal_items'])}")


if __name__ == "__main__":
    export()
