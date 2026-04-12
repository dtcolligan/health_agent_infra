from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from textwrap import shorten
import sys

import pandas as pd

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from health_model.schemas import (
    DailyHealthSnapshot,
    GymExerciseSet,
    NutritionDaily,
    ReadinessDaily,
    SleepDaily,
    TrainingSession,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "data" / "garmin" / "export"
DEFAULT_GYM_LOG_PATH = PROJECT_ROOT / "data" / "health" / "manual_gym_sessions.json"
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "health_log.db"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "health"

READINESS_SCORE_MAP = {
    "VERY_LOW": 1,
    "LOW": 2,
    "MODERATE": 3,
    "HIGH": 4,
    "PRIMED": 5,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Health Lab daily snapshots from available Garmin, gym, and nutrition inputs.")
    parser.add_argument("--export-dir", default=str(DEFAULT_EXPORT_DIR))
    parser.add_argument("--gym-log-path", default=str(DEFAULT_GYM_LOG_PATH))
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--date", help="Optional YYYY-MM-DD target date. Defaults to latest available date across inputs.")
    parser.add_argument("--user-id", type=int, default=1, help="Intended nutrition user_id for SQLite nutrition loading. Defaults to 1.")
    return parser.parse_args()


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def safe_float(value):
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except Exception:
        return None


def safe_int(value):
    if value is None or pd.isna(value):
        return None
    try:
        return int(round(float(value)))
    except Exception:
        return None


def _truthy_date(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _sqlite_tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {row[0] for row in rows}


def _sqlite_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def _build_top_meals_summary(conn: sqlite3.Connection, user_id: int, date_for: str) -> str | None:
    meal_item_columns = _sqlite_columns(conn, "meal_items")
    if not {"user_id", "date_for", "item_name"}.issubset(meal_item_columns):
        return None

    calories_expr = "COALESCE(SUM(calories), 0)" if "calories" in meal_item_columns else "0"
    rows = conn.execute(
        f"""
        SELECT item_name, {calories_expr} AS total_calories
        FROM meal_items
        WHERE user_id = ? AND date_for = ?
        GROUP BY item_name
        ORDER BY total_calories DESC, item_name ASC
        LIMIT 3
        """,
        (user_id, date_for),
    ).fetchall()
    if not rows:
        return None

    parts = []
    for item_name, total_calories in rows:
        if item_name is None:
            continue
        label = str(item_name).strip()
        if not label:
            continue
        if total_calories:
            label = f"{label} ({int(round(total_calories))} kcal)"
        parts.append(label)
    if not parts:
        return None
    return shorten(", ".join(parts), width=120, placeholder="...")


def load_manual_gym(path: Path) -> tuple[dict[str, list[dict]], list[str]]:
    if not path.exists():
        return {}, []

    payload = json.loads(path.read_text())
    sessions_by_date: dict[str, list[dict]] = {}
    dates: list[str] = []
    for session in payload.get("sessions", []):
        date = _truthy_date(session.get("date"))
        if not date:
            continue
        sessions_by_date.setdefault(date, []).append(session)
        dates.append(date)
    return sessions_by_date, dates


def load_nutrition_rows(db_path: Path, user_id: int) -> tuple[dict[str, dict], list[str]]:
    if not db_path.exists():
        return {}, []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        tables = _sqlite_tables(conn)
        rows = []
        source_name = None

        if "daily_summary" in tables:
            daily_summary_columns = _sqlite_columns(conn, "daily_summary")
            if {"user_id", "date_for", "total_calories", "total_protein_g", "total_carbs_g", "total_fat_g", "total_fiber_g", "meal_count"}.issubset(daily_summary_columns):
                rows = conn.execute(
                    """
                    SELECT date_for,
                           total_calories,
                           total_protein_g,
                           total_carbs_g,
                           total_fat_g,
                           total_fiber_g,
                           meal_count
                    FROM daily_summary
                    WHERE user_id = ?
                    ORDER BY date_for
                    """,
                    (user_id,),
                ).fetchall()
                source_name = "health_log_sqlite_daily_summary"

        if not rows and "meal_items" in tables:
            meal_item_columns = _sqlite_columns(conn, "meal_items")
            if {"user_id", "date_for", "item_name"}.issubset(meal_item_columns):
                calories_expr = "COALESCE(SUM(calories), 0)" if "calories" in meal_item_columns else "NULL"
                protein_expr = "COALESCE(SUM(protein_g), 0)" if "protein_g" in meal_item_columns else "NULL"
                carbs_expr = "COALESCE(SUM(carbs_g), 0)" if "carbs_g" in meal_item_columns else "NULL"
                fat_expr = "COALESCE(SUM(fat_g), 0)" if "fat_g" in meal_item_columns else "NULL"
                fiber_expr = "COALESCE(SUM(fiber_g), 0)" if "fiber_g" in meal_item_columns else "NULL"
                rows = conn.execute(
                    f"""
                    SELECT date_for,
                           {calories_expr} AS total_calories,
                           {protein_expr} AS total_protein_g,
                           {carbs_expr} AS total_carbs_g,
                           {fat_expr} AS total_fat_g,
                           {fiber_expr} AS total_fiber_g,
                           COUNT(*) AS meal_count
                    FROM meal_items
                    WHERE user_id = ?
                    GROUP BY user_id, date_for
                    ORDER BY date_for
                    """,
                    (user_id,),
                ).fetchall()
                source_name = "health_log_sqlite_meal_items"
    except sqlite3.Error:
        conn.close()
        return {}, []

    mapped = {}
    dates = []
    for row in rows:
        date_for = row["date_for"]
        if not date_for:
            continue
        payload = dict(row)
        payload["top_meals_summary"] = _build_top_meals_summary(conn, user_id, date_for) if "meal_items" in tables else None
        payload["source"] = source_name
        mapped[date_for] = payload
        dates.append(date_for)
    conn.close()
    return mapped, dates


def build_sleep(row: pd.Series, date: str) -> SleepDaily:
    total_sleep_sec = sum(v or 0 for v in [
        safe_float(row.get("sleep_deep_sec")),
        safe_float(row.get("sleep_light_sec")),
        safe_float(row.get("sleep_rem_sec")),
    ]) or None
    return SleepDaily(
        date=date,
        source="garmin_export",
        total_sleep_sec=total_sleep_sec,
        deep_sleep_sec=safe_float(row.get("sleep_deep_sec")),
        light_sleep_sec=safe_float(row.get("sleep_light_sec")),
        rem_sleep_sec=safe_float(row.get("sleep_rem_sec")),
        awake_sleep_sec=safe_float(row.get("sleep_awake_sec")),
        sleep_score=safe_float(row.get("sleep_score_overall")),
        avg_sleep_respiration=safe_float(row.get("avg_sleep_respiration")),
        awake_count=safe_int(row.get("awake_count")),
    )


def build_readiness(row: pd.Series, date: str) -> ReadinessDaily:
    label = row.get("training_readiness_level")
    recovery_hours = safe_float(row.get("training_recovery_time_hours"))
    observation = None
    if label and recovery_hours is not None:
        observation = f"Garmin export shows {label.lower()} readiness with about {recovery_hours:.1f} recovery hours remaining."
    guidance = None
    if label in {"VERY_LOW", "LOW"}:
        guidance = "Generic guidance: bias toward easier training or recovery work unless another trusted signal clearly says otherwise."
    elif label in {"HIGH", "PRIMED"}:
        guidance = "Generic guidance: normal training may be reasonable if soreness and schedule also line up."
    return ReadinessDaily(
        date=date,
        source="garmin_export",
        readiness_score=READINESS_SCORE_MAP.get(str(label).upper()) if label else None,
        readiness_label=label,
        sleep_factor=safe_float(row.get("training_readiness_sleep_pct")),
        hrv_factor=safe_float(row.get("training_readiness_hrv_pct")),
        stress_factor=safe_float(row.get("training_readiness_stress_pct")),
        training_load_factor=safe_float(row.get("training_readiness_load_pct")),
        recovery_hours_remaining=recovery_hours,
        data_backed_observation=observation,
        generic_guidance=guidance,
        caveat="Garmin export coverage is bounded and unsupported fields stay null.",
    )


def build_running_sessions(activities: pd.DataFrame, date: str) -> list[TrainingSession]:
    if activities.empty:
        return []
    day_runs = activities[activities["date"] == date].copy()
    if day_runs.empty:
        return []

    sessions = []
    for _, row in day_runs.iterrows():
        pace = None
        distance_m = safe_float(row.get("distance_m"))
        duration_sec = safe_float(row.get("duration_sec"))
        if distance_m and duration_sec and distance_m > 0:
            pace = duration_sec / (distance_m / 1000.0)
        sessions.append(
            TrainingSession(
                session_id=f"garmin-run-{safe_int(row.get('activity_id'))}",
                date=date,
                session_type="run",
                source="garmin_export",
                start_time_local=row.get("start_time_local"),
                duration_sec=duration_sec,
                session_title=row.get("activity_type") or row.get("sport_type"),
                distance_m=distance_m,
                avg_hr=safe_float(row.get("avg_hr")),
                max_hr=safe_float(row.get("max_hr")),
                avg_pace_sec_per_km=pace,
                elevation_gain_m=safe_float(row.get("elevation_gain_m")),
                training_effect_aerobic=safe_float(row.get("training_effect_aerobic")),
            )
        )
    return sessions


def build_gym_sessions(session_payloads: list[dict], date: str) -> tuple[list[TrainingSession], list[GymExerciseSet]]:
    sessions: list[TrainingSession] = []
    sets: list[GymExerciseSet] = []
    for session in session_payloads:
        session_id = session.get("session_id") or f"manual-gym-{date}-{len(sessions)+1}"
        raw_sets = session.get("sets", [])
        total_sets = len(raw_sets)
        total_reps = sum(int(s.get("reps") or 0) for s in raw_sets)
        total_load = sum((float(s.get("reps") or 0) * float(s.get("weight_kg") or 0)) for s in raw_sets)
        exercise_names = [s.get("exercise_name") for s in raw_sets if s.get("exercise_name")]
        sessions.append(
            TrainingSession(
                session_id=session_id,
                date=date,
                session_type="gym",
                source="manual_gym_log",
                start_time_local=session.get("start_time_local"),
                duration_sec=safe_float(session.get("duration_sec")),
                session_title=session.get("session_title"),
                rpe_1_10=safe_float(session.get("rpe_1_10")),
                energy_pre_1_5=safe_float(session.get("energy_pre_1_5")),
                energy_post_1_5=safe_float(session.get("energy_post_1_5")),
                notes=session.get("notes"),
                lift_focus=session.get("lift_focus"),
                exercise_count=len(set(exercise_names)),
                total_sets=total_sets,
                total_reps=total_reps,
                total_load_kg=round(total_load, 2) if total_sets else None,
            )
        )
        for idx, raw_set in enumerate(raw_sets, start=1):
            sets.append(
                GymExerciseSet(
                    set_id=raw_set.get("set_id") or f"{session_id}-set-{idx}",
                    session_id=session_id,
                    date=date,
                    exercise_name=raw_set.get("exercise_name", "unknown"),
                    exercise_group=raw_set.get("exercise_group"),
                    set_number=safe_int(raw_set.get("set_number") or idx),
                    reps=safe_int(raw_set.get("reps")),
                    weight_kg=safe_float(raw_set.get("weight_kg")),
                    rir=safe_float(raw_set.get("rir")),
                    rpe=safe_float(raw_set.get("rpe")),
                    completed_bool=raw_set.get("completed_bool"),
                    note=raw_set.get("note"),
                )
            )
    return sessions, sets


def build_nutrition(nutrition_rows: dict[str, dict], date: str) -> NutritionDaily:
    row = nutrition_rows.get(date)
    if not row:
        return NutritionDaily(date=date, source=None)
    return NutritionDaily(
        date=date,
        calories_kcal=safe_float(row.get("total_calories")),
        protein_g=safe_float(row.get("total_protein_g")),
        carbs_g=safe_float(row.get("total_carbs_g")),
        fat_g=safe_float(row.get("total_fat_g")),
        fiber_g=safe_float(row.get("total_fiber_g")),
        meal_count=safe_int(row.get("meal_count")),
        food_log_completeness="logged" if safe_int(row.get("meal_count")) else "not_logged",
        top_meals_summary=row.get("top_meals_summary"),
        source=row.get("source") or "health_log_sqlite",
    )


def _pick_target_date(daily: pd.DataFrame, gym_dates: list[str], nutrition_dates: list[str], explicit_date: str | None) -> str:
    if explicit_date:
        return explicit_date
    dates = []
    if not daily.empty:
        dates.extend(daily["date"].dropna().astype(str).tolist())
    dates.extend(gym_dates)
    dates.extend(nutrition_dates)
    if not dates:
        raise ValueError("No input dates available for snapshot generation.")
    return max(dates)


def generate_snapshot(export_dir: Path, gym_log_path: Path, db_path: Path, target_date: str | None = None, user_id: int = 1) -> DailyHealthSnapshot:
    daily = load_csv(export_dir / "daily_summary_export.csv")
    activities = load_csv(export_dir / "activities_export.csv")
    hydration = load_csv(export_dir / "hydration_events_export.csv") if (export_dir / "hydration_events_export.csv").exists() else pd.DataFrame()

    daily["date"] = daily["date"].astype(str)
    activities["date"] = pd.to_datetime(activities["start_time_local"], errors="coerce").dt.strftime("%Y-%m-%d")

    gym_by_date, gym_dates = load_manual_gym(gym_log_path)
    nutrition_rows, nutrition_dates = load_nutrition_rows(db_path, user_id=user_id)
    date = _pick_target_date(daily, gym_dates, nutrition_dates, target_date)

    daily_rows = daily[daily["date"] == date]
    daily_row = daily_rows.iloc[-1] if not daily_rows.empty else pd.Series(dtype=object)

    sleep = build_sleep(daily_row, date) if not daily_rows.empty else SleepDaily(date=date)
    readiness = build_readiness(daily_row, date) if not daily_rows.empty else ReadinessDaily(date=date)
    running_sessions = build_running_sessions(activities, date)
    gym_sessions, gym_sets = build_gym_sessions(gym_by_date.get(date, []), date)
    nutrition = build_nutrition(nutrition_rows, date)

    hydration_ml = None
    if not hydration.empty:
        hydration["date"] = pd.to_datetime(hydration["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        hydration_ml = safe_float(hydration.loc[hydration["date"] == date, "value_ml"].sum())
        if hydration_ml == 0:
            hydration_ml = None

    data_backed_fields = []
    generic_fields = []
    if not daily_rows.empty:
        data_backed_fields.extend([
            "sleep_duration_hours", "sleep_score", "sleep_awake_count", "resting_hr",
            "hrv_status", "body_battery_or_readiness", "readiness_label",
            "running_sessions_count", "running_volume_m",
        ])
    if hydration_ml is not None:
        data_backed_fields.append("hydration_ml")
    if gym_sessions:
        data_backed_fields.extend(["gym_sessions_count", "gym_total_sets", "gym_total_reps", "gym_total_load_kg"])
    if nutrition.source:
        data_backed_fields.extend(["food_logged_bool", "calories_kcal", "protein_g", "carbs_g", "fat_g"])
    else:
        generic_fields.append("nutrition_unavailable_in_v1")
    if readiness.generic_guidance:
        generic_fields.append("readiness_daily.generic_guidance")

    snapshot = DailyHealthSnapshot(
        date=date,
        sleep_duration_hours=round((sleep.total_sleep_sec or 0) / 3600, 2) if sleep.total_sleep_sec else None,
        sleep_score=sleep.sleep_score,
        sleep_awake_count=sleep.awake_count,
        resting_hr=safe_float(daily_row.get("resting_hr")) if not daily_rows.empty else None,
        hrv_status=daily_row.get("health_hrv_status") if not daily_rows.empty else None,
        body_battery_or_readiness=safe_float(daily_row.get("body_battery")) if not daily_rows.empty else None,
        readiness_label=readiness.readiness_label,
        running_sessions_count=len(running_sessions),
        running_volume_m=round(sum(s.distance_m or 0 for s in running_sessions), 2) if running_sessions else None,
        gym_sessions_count=len(gym_sessions),
        gym_total_sets=sum(s.total_sets or 0 for s in gym_sessions) if gym_sessions else None,
        gym_total_reps=sum(s.total_reps or 0 for s in gym_sessions) if gym_sessions else None,
        gym_total_load_kg=round(sum(s.total_load_kg or 0 for s in gym_sessions), 2) if gym_sessions else None,
        food_logged_bool=True if nutrition.source and (nutrition.meal_count or 0) > 0 else False if nutrition.source else None,
        calories_kcal=nutrition.calories_kcal,
        protein_g=nutrition.protein_g,
        carbs_g=nutrition.carbs_g,
        fat_g=nutrition.fat_g,
        hydration_ml=hydration_ml,
        data_backed_fields=sorted(set(data_backed_fields)),
        generic_fields=sorted(set(generic_fields)),
        source_flags={
            "garmin_export": not daily_rows.empty,
            "manual_gym_log": bool(gym_sessions),
            "nutrition_sqlite": bool(nutrition.source),
        },
        sleep_daily=asdict(sleep),
        readiness_daily=asdict(readiness),
        running_sessions=[asdict(s) for s in running_sessions],
        gym_sessions=[asdict(s) for s in gym_sessions],
        gym_exercise_sets=[asdict(s) for s in gym_sets],
        nutrition_daily=asdict(nutrition),
    )
    return snapshot


def write_outputs(snapshot: DailyHealthSnapshot, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_path = output_dir / "daily_snapshot_latest.json"
    dated_path = output_dir / f"daily_snapshot_{snapshot.date}.json"
    payload = json.dumps(snapshot.to_dict(), indent=2)
    latest_path.write_text(payload)
    dated_path.write_text(payload)
    return latest_path, dated_path


def main() -> None:
    args = parse_args()
    snapshot = generate_snapshot(
        export_dir=Path(args.export_dir),
        gym_log_path=Path(args.gym_log_path),
        db_path=Path(args.db_path),
        target_date=args.date,
        user_id=args.user_id,
    )
    latest_path, dated_path = write_outputs(snapshot, Path(args.output_dir))
    print(f"wrote {latest_path}")
    print(f"wrote {dated_path}")


if __name__ == "__main__":
    main()
