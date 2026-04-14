from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from dataclasses import asdict
from pathlib import Path
from textwrap import shorten
from datetime import datetime, timezone
import sys

import pandas as pd

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from health_model.schemas import (
    DailyHealthSnapshot,
    ExerciseAlias,
    ExerciseCatalog,
    GymExerciseSet,
    GymSetRecord,
    NutritionDaily,
    ProvenanceRecord,
    ReadinessDaily,
    SleepDaily,
    SourceRecord,
    TrainingSession,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "pull" / "data" / "garmin" / "export"
DEFAULT_SUBJECTIVE_INPUT_PATH = PROJECT_ROOT / "pull" / "data" / "health"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "clean" / "data" / "health"
PARSER_VERSION = "garmin-source-hardening-v1"
MANUAL_GYM_SOURCE_NAME = "resistance_training"
MANUAL_GYM_PARSER_VERSION = "manual-form-normalization-v1"

READINESS_SCORE_MAP = {
    "VERY_LOW": 1,
    "LOW": 2,
    "MODERATE": 3,
    "HIGH": 4,
    "PRIMED": 5,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate flagship Health Lab daily snapshots from Garmin plus subjective inputs, with optional bridge enrichment when available.")
    parser.add_argument("--export-dir", default=str(DEFAULT_EXPORT_DIR))
    parser.add_argument("--gym-log-path", help="Optional manual gym log path for non-flagship enrichment.")
    parser.add_argument("--subjective-bundle-path", default=str(DEFAULT_SUBJECTIVE_INPUT_PATH), help="Shared-input bundle JSON or directory of shared_input_bundle_*.json files used for the required subjective flagship lane.")
    parser.add_argument("--db-path", help="Optional nutrition bridge database path.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--date", help="Optional YYYY-MM-DD target date. Defaults to latest available date across inputs.")
    parser.add_argument("--user-id", type=int, default=1, help="Intended nutrition user_id for SQLite nutrition loading. Defaults to 1.")
    parser.add_argument("--garmin-proof-dir", help="Optional directory for Garmin canonical proof artifacts.")
    parser.add_argument("--nutrition-proof-dir", help="Optional directory for nutrition canonical proof artifacts.")
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


def _stable_token(text: str, length: int = 16) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_batch_id(export_dir: Path) -> str:
    manifest_path = export_dir / "manifest.json"
    if manifest_path.exists():
        return _sha256_file(manifest_path)[:16]
    return _stable_token(str(export_dir.resolve()))


def _supporting_refs(export_dir: Path) -> list[str]:
    refs = []
    for name in ["manifest.json", "daily_summary_export.csv", "activities_export.csv"]:
        path = export_dir / name
        if path.exists():
            refs.append(path.as_posix())
    return refs


def _daily_source_record_id(export_dir: Path, date: str) -> str:
    return f"garmin:{_manifest_batch_id(export_dir)}:daily_summary:{date}"


def _activity_source_record_id(export_dir: Path, activity_id: int | str | None) -> str:
    return f"garmin:{_manifest_batch_id(export_dir)}:activity:{activity_id}"


def _provenance_record_id(source_record_id: str, artifact_family: str) -> str:
    return f"provenance_{artifact_family}_{_stable_token(source_record_id)}"


def _artifact_id(artifact_family: str, source_record_id: str) -> str:
    return f"{artifact_family}_{_stable_token(source_record_id)}"


def _nutrition_source_name(row: dict | None) -> str:
    raw_source = str((row or {}).get("source") or "health_log_sqlite_daily_summary").strip()
    return raw_source or "health_log_sqlite_daily_summary"


def _nutrition_source_record_id(row: dict | None, date: str) -> str:
    return f"nutrition:{_nutrition_source_name(row)}:day:{date}"


def _nutrition_provenance_record_id(source_record_id: str) -> str:
    return _provenance_record_id(source_record_id, "nutrition_daily")


def _nutrition_daily_id(source_record_id: str) -> str:
    return _artifact_id("nutrition_daily", source_record_id)


def _build_nutrition_source_record(db_path: Path, row: dict | None, date: str) -> SourceRecord:
    source_name = _nutrition_source_name(row)
    ingested_at = datetime.fromtimestamp(db_path.stat().st_mtime, tz=timezone.utc).isoformat() if db_path.exists() else None
    return SourceRecord(
        source_record_id=_nutrition_source_record_id(row, date),
        source_name=source_name,
        source_type="imported_food_pipeline",
        entry_lane="pull",
        raw_location=db_path.as_posix(),
        raw_format="sqlite",
        effective_date=date,
        ingested_at=ingested_at,
        hash_or_version=_sha256_file(db_path)[:16] if db_path.exists() else None,
        native_record_type="day_nutrition_summary",
        native_record_id=date,
    )


def _build_nutrition_provenance_record(db_path: Path, source_record: SourceRecord) -> ProvenanceRecord:
    supporting_refs = [db_path.as_posix(), f"{db_path.as_posix()}#daily_summary", f"{db_path.as_posix()}#meal_items"]
    return ProvenanceRecord(
        provenance_record_id=_nutrition_provenance_record_id(source_record.source_record_id),
        source_record_id=source_record.source_record_id,
        derivation_method="food_import_normalization",
        supporting_refs=supporting_refs,
        parser_version=PARSER_VERSION,
        conflict_status="none",
    )


def _snapshot_provenance_id(export_dir: Path, date: str) -> str:
    return f"provenance_daily_health_snapshot_{_stable_token(_daily_source_record_id(export_dir, date) + ':snapshot')}"


def _snapshot_id(export_dir: Path, date: str) -> str:
    return f"daily_health_snapshot_{_stable_token(_daily_source_record_id(export_dir, date) + ':snapshot')}"


def _build_source_record(export_dir: Path, native_record_type: str, native_record_id: str, *, effective_date: str | None = None) -> SourceRecord:
    source_record_id = (
        _daily_source_record_id(export_dir, native_record_id)
        if native_record_type == "daily_summary"
        else _activity_source_record_id(export_dir, native_record_id)
    )
    manifest_path = export_dir / "manifest.json"
    ingested_at = datetime.fromtimestamp(manifest_path.stat().st_mtime, tz=timezone.utc).isoformat() if manifest_path.exists() else None
    raw_location = (export_dir / ("daily_summary_export.csv" if native_record_type == "daily_summary" else "activities_export.csv")).as_posix()
    return SourceRecord(
        source_record_id=source_record_id,
        source_name="garmin",
        source_type="wearable",
        entry_lane="pull",
        raw_location=raw_location,
        raw_format="csv",
        effective_date=effective_date,
        ingested_at=ingested_at,
        hash_or_version=_manifest_batch_id(export_dir),
        native_record_type=native_record_type,
        native_record_id=native_record_id,
    )


def _build_provenance_record(export_dir: Path, source_record_id: str, artifact_family: str) -> ProvenanceRecord:
    return ProvenanceRecord(
        provenance_record_id=_provenance_record_id(source_record_id, artifact_family),
        source_record_id=source_record_id,
        derivation_method="wearable_normalization",
        supporting_refs=_supporting_refs(export_dir),
        parser_version=PARSER_VERSION,
        conflict_status="none",
    )


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


def load_manual_gym(path: Path | None) -> tuple[dict[str, list[dict]], list[str]]:
    if path is None or not path.exists():
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


def _subjective_bundle_paths(path: Path | None) -> list[Path]:
    if path is None or not path.exists():
        return []
    if path.is_file():
        return [path]
    return sorted(path.glob("shared_input_bundle_*.json"))


def _derived_subjective_source_record_id(entry: dict) -> str | None:
    explicit = entry.get("source_record_id")
    if explicit:
        return str(explicit)
    source_artifact_ids = entry.get("source_artifact_ids") or []
    if source_artifact_ids:
        return f"subjective:{source_artifact_ids[0]}:day:{entry['date']}"
    return None


def _derived_subjective_provenance_record_id(entry: dict, source_record_id: str | None) -> str | None:
    explicit = entry.get("provenance_record_id")
    if explicit:
        return str(explicit)
    if source_record_id:
        return f"provenance:{source_record_id}"
    return None


def load_subjective_entries(path: Path | None) -> tuple[dict[str, dict], list[str]]:
    mapped: dict[str, dict] = {}
    dates: list[str] = []

    for bundle_path in _subjective_bundle_paths(path):
        try:
            payload = json.loads(bundle_path.read_text())
        except json.JSONDecodeError:
            continue
        for raw_entry in payload.get("subjective_daily_entries", []):
            date = _truthy_date(raw_entry.get("date"))
            if not date:
                continue
            entry = dict(raw_entry)
            source_record_id = _derived_subjective_source_record_id(entry)
            entry.setdefault("source_record_id", source_record_id)
            entry.setdefault("provenance_record_id", _derived_subjective_provenance_record_id(entry, source_record_id))
            entry.setdefault("source_name", "manual_subjective_recovery")
            mapped[date] = entry
            dates.append(date)
    return mapped, dates


def build_subjective_daily(entry: dict | None, date: str) -> dict[str, object] | None:
    if not entry:
        return None
    return {
        "date": date,
        "source_name": entry.get("source_name") or "manual_subjective_recovery",
        "source_record_id": entry.get("source_record_id"),
        "provenance_record_id": entry.get("provenance_record_id"),
        "conflict_status": entry.get("conflict_status") or "none",
        "subjective_energy_1_5": safe_float(entry.get("energy_self_rating")),
        "subjective_soreness_1_5": safe_float(entry.get("soreness_today_1_to_5")),
        "subjective_stress_1_5": safe_float(entry.get("stress_self_rating")),
        "overall_day_note": entry.get("free_text_summary") or entry.get("unusual_constraints_or_stressors") or entry.get("training_intent_today"),
        "training_intent_today": entry.get("training_intent_today"),
        "readiness_input_type": entry.get("readiness_input_type"),
    }


def load_nutrition_rows(db_path: Path | None, user_id: int) -> tuple[dict[str, dict], list[str]]:
    if db_path is None or not db_path.exists():
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


def build_sleep(row: pd.Series, date: str, export_dir: Path) -> SleepDaily:
    total_sleep_sec = sum(v or 0 for v in [
        safe_float(row.get("sleep_deep_sec")),
        safe_float(row.get("sleep_light_sec")),
        safe_float(row.get("sleep_rem_sec")),
    ]) or None
    source_record = _build_source_record(export_dir, "daily_summary", date, effective_date=date)
    provenance = _build_provenance_record(export_dir, source_record.source_record_id, "sleep_daily")
    return SleepDaily(
        date=date,
        source="garmin_export",
        sleep_daily_id=_artifact_id("sleep_daily", source_record.source_record_id),
        source_name="garmin",
        source_record_id=source_record.source_record_id,
        provenance_record_id=provenance.provenance_record_id,
        conflict_status="none",
        total_sleep_sec=total_sleep_sec,
        deep_sleep_sec=safe_float(row.get("sleep_deep_sec")),
        light_sleep_sec=safe_float(row.get("sleep_light_sec")),
        rem_sleep_sec=safe_float(row.get("sleep_rem_sec")),
        awake_sleep_sec=safe_float(row.get("sleep_awake_sec")),
        sleep_score=safe_float(row.get("sleep_score_overall")),
        avg_sleep_respiration=safe_float(row.get("avg_sleep_respiration")),
        awake_count=safe_int(row.get("awake_count")),
    )


def build_readiness(row: pd.Series, date: str, export_dir: Path) -> ReadinessDaily:
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
    source_record = _build_source_record(export_dir, "daily_summary", date, effective_date=date)
    provenance = _build_provenance_record(export_dir, source_record.source_record_id, "readiness_daily")
    return ReadinessDaily(
        date=date,
        source="garmin_export",
        readiness_daily_id=_artifact_id("readiness_daily", source_record.source_record_id),
        source_name="garmin",
        source_record_id=source_record.source_record_id,
        provenance_record_id=provenance.provenance_record_id,
        conflict_status="none",
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


def build_running_sessions(activities: pd.DataFrame, date: str, export_dir: Path) -> list[TrainingSession]:
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
        native_activity_id = str(safe_int(row.get("activity_id")) or row.get("activity_id"))
        source_record = _build_source_record(export_dir, "activity", native_activity_id, effective_date=date)
        provenance = _build_provenance_record(export_dir, source_record.source_record_id, "training_session")
        if distance_m and duration_sec and distance_m > 0:
            pace = duration_sec / (distance_m / 1000.0)
        sessions.append(
            TrainingSession(
                session_id=f"garmin-run-{native_activity_id}",
                date=date,
                session_type="run",
                source="garmin_export",
                training_session_id=_artifact_id("training_session", source_record.source_record_id),
                source_name="garmin",
                source_record_id=source_record.source_record_id,
                provenance_record_id=provenance.provenance_record_id,
                conflict_status="none",
                start_time_local=str(row.get("start_time_local")) if row.get("start_time_local") is not None else None,
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


def _manual_session_key(session: dict, date: str, index: int) -> str:
    return str(session.get("session_key") or session.get("session_id") or f"{date}-session-{index}")


def _manual_set_key(raw_set: dict, index: int) -> str:
    explicit = raw_set.get("set_key") or raw_set.get("set_id")
    if explicit:
        return str(explicit)
    exercise_name = str(raw_set.get("exercise_name") or "set").strip().lower().replace(" ", "-")
    set_number = safe_int(raw_set.get("set_number"))
    if set_number is not None:
        return f"{exercise_name}-{set_number}"
    return f"{exercise_name}-{index}"


def _manual_training_session_id(source_artifact: str, session_key: str) -> str:
    return f"{MANUAL_GYM_SOURCE_NAME}:{source_artifact}:session:{session_key}"


def _manual_set_id(source_artifact: str, session_key: str, set_key: str) -> str:
    return f"{MANUAL_GYM_SOURCE_NAME}:{source_artifact}:set:{session_key}:{set_key}"


def _manual_training_provenance_id(source_artifact: str, session_key: str) -> str:
    return f"provenance:{MANUAL_GYM_SOURCE_NAME}:{source_artifact}:training_session:{session_key}"


def _manual_set_provenance_id(source_artifact: str, session_key: str, set_key: str) -> str:
    return f"provenance:{MANUAL_GYM_SOURCE_NAME}:{source_artifact}:gym_exercise_set:{session_key}:{set_key}"


def _manual_normalize_label(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip())


def _manual_slug(value: str) -> str:
    normalized = _manual_normalize_label(value).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug or "unknown"


def _manual_canonical_exercise_name(value: str) -> str:
    normalized = _manual_normalize_label(value)
    return normalized.title() if normalized else "Unknown"


def _manual_exercise_catalog_source_record_id(source_artifact: str, exercise_key: str) -> str:
    return f"{MANUAL_GYM_SOURCE_NAME}:{source_artifact}:exercise:{exercise_key}"


def _manual_exercise_catalog_id(source_artifact: str, exercise_key: str) -> str:
    return f"exercise_catalog:{MANUAL_GYM_SOURCE_NAME}:{source_artifact}:exercise:{exercise_key}"


def _manual_exercise_catalog_provenance_id(source_artifact: str, exercise_key: str) -> str:
    return f"provenance:{MANUAL_GYM_SOURCE_NAME}:{source_artifact}:exercise_catalog:{exercise_key}"


def _manual_exercise_alias_id(source_artifact: str, exercise_key: str, alias_slug: str) -> str:
    return f"exercise_alias:{MANUAL_GYM_SOURCE_NAME}:{source_artifact}:exercise:{exercise_key}:alias:{alias_slug}"


def _manual_gym_set_record_id(source_artifact: str, session_key: str, set_key: str) -> str:
    return f"gym_set_record:{MANUAL_GYM_SOURCE_NAME}:{source_artifact}:set:{session_key}:{set_key}"


def _manual_gym_set_record_provenance_id(source_artifact: str, session_key: str, set_key: str) -> str:
    return f"provenance:{MANUAL_GYM_SOURCE_NAME}:{source_artifact}:gym_set_record:{session_key}:{set_key}"


def build_manual_resistance_training_objects(
    session_payloads: list[dict],
    date: str,
    *,
    source_artifact: str = "manual_gym_sessions_fixture",
) -> tuple[list[TrainingSession], list[ExerciseCatalog], list[ExerciseAlias], list[GymSetRecord]]:
    sessions, _ = build_gym_sessions(session_payloads, date, source_artifact=source_artifact)
    exercise_state: dict[str, dict[str, object]] = {}
    gym_set_records: list[GymSetRecord] = []

    for session_index, session in enumerate(session_payloads, start=1):
        session_key = _manual_session_key(session, date, session_index)
        training_session_id = _manual_training_session_id(source_artifact, session_key)
        raw_sets = session.get("sets", [])
        for set_index, raw_set in enumerate(raw_sets, start=1):
            set_key = _manual_set_key(raw_set, set_index)
            raw_exercise_name = _manual_normalize_label(str(raw_set.get("exercise_name") or "unknown"))
            exercise_key = _manual_slug(raw_exercise_name)
            alias_slug = _manual_slug(raw_exercise_name)
            exercise_entry = exercise_state.setdefault(
                exercise_key,
                {
                    "canonical_name": _manual_canonical_exercise_name(raw_exercise_name),
                    "source_record_id": _manual_exercise_catalog_source_record_id(source_artifact, exercise_key),
                    "provenance_record_id": _manual_exercise_catalog_provenance_id(source_artifact, exercise_key),
                    "primary_muscle_groups": [],
                    "aliases": {},
                },
            )
            exercise_group = _manual_normalize_label(str(raw_set.get("exercise_group") or ""))
            if exercise_group:
                primary = exercise_entry["primary_muscle_groups"]
                if exercise_group.title() not in primary:
                    primary.append(exercise_group.title())
            exercise_entry["aliases"].setdefault(alias_slug, raw_exercise_name)
            gym_set_records.append(
                GymSetRecord(
                    gym_set_record_id=_manual_gym_set_record_id(source_artifact, session_key, set_key),
                    training_session_id=training_session_id,
                    date=date,
                    exercise_catalog_id=_manual_exercise_catalog_id(source_artifact, exercise_key),
                    source_name=MANUAL_GYM_SOURCE_NAME,
                    source_record_id=_manual_set_id(source_artifact, session_key, set_key),
                    provenance_record_id=_manual_gym_set_record_provenance_id(source_artifact, session_key, set_key),
                    conflict_status="none",
                    exercise_alias_id=_manual_exercise_alias_id(source_artifact, exercise_key, alias_slug),
                    set_number=safe_int(raw_set.get("set_number") or set_index),
                    reps=safe_int(raw_set.get("reps")),
                    weight_kg=safe_float(raw_set.get("weight_kg")),
                    rir=safe_float(raw_set.get("rir")),
                    rpe=safe_float(raw_set.get("rpe")),
                    completed_bool=raw_set.get("completed_bool"),
                    set_type=raw_set.get("set_type"),
                    note=raw_set.get("note") or raw_set.get("notes"),
                )
            )

    exercise_catalog = [
        ExerciseCatalog(
            exercise_catalog_id=_manual_exercise_catalog_id(source_artifact, exercise_key),
            canonical_exercise_name=str(payload["canonical_name"]),
            movement_pattern=None,
            source_name=MANUAL_GYM_SOURCE_NAME,
            source_record_id=str(payload["source_record_id"]),
            provenance_record_id=str(payload["provenance_record_id"]),
            conflict_status="none",
            equipment=None,
            primary_muscle_groups=list(payload["primary_muscle_groups"]) or None,
            secondary_muscle_groups=None,
            unilateral_bool=None,
            loaded_pattern=None,
        )
        for exercise_key, payload in sorted(exercise_state.items())
    ]
    exercise_alias = [
        ExerciseAlias(
            exercise_alias_id=_manual_exercise_alias_id(source_artifact, exercise_key, alias_slug),
            exercise_catalog_id=_manual_exercise_catalog_id(source_artifact, exercise_key),
            alias_name=str(alias_name),
            source_name=MANUAL_GYM_SOURCE_NAME,
            source_record_id=str(payload["source_record_id"]),
            provenance_record_id=str(payload["provenance_record_id"]),
            conflict_status="none",
            source_native_exercise_id=None,
            normalization_rule="manual_structured_name_passthrough",
            notes="manual_structured_gym_source_of_truth",
        )
        for exercise_key, payload in sorted(exercise_state.items())
        for alias_slug, alias_name in sorted(dict(payload["aliases"]).items())
    ]
    return sessions, exercise_catalog, exercise_alias, gym_set_records


def build_gym_sessions(session_payloads: list[dict], date: str, *, source_artifact: str = "manual_gym_sessions_fixture") -> tuple[list[TrainingSession], list[GymExerciseSet]]:
    sessions: list[TrainingSession] = []
    sets: list[GymExerciseSet] = []
    for session_index, session in enumerate(session_payloads, start=1):
        session_key = _manual_session_key(session, date, session_index)
        training_session_id = _manual_training_session_id(source_artifact, session_key)
        raw_sets = session.get("sets", [])
        total_sets = len(raw_sets)
        total_reps = sum(int(s.get("reps") or 0) for s in raw_sets)
        total_load = sum((float(s.get("reps") or 0) * float(s.get("weight_kg") or 0)) for s in raw_sets)
        exercise_names = [s.get("exercise_name") for s in raw_sets if s.get("exercise_name")]
        sessions.append(
            TrainingSession(
                session_id=session_key,
                date=date,
                session_type="gym",
                source="manual_gym_log",
                training_session_id=training_session_id,
                source_name=MANUAL_GYM_SOURCE_NAME,
                source_record_id=training_session_id,
                provenance_record_id=_manual_training_provenance_id(source_artifact, session_key),
                confidence_label="high",
                conflict_status="none",
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
        for set_index, raw_set in enumerate(raw_sets, start=1):
            set_key = _manual_set_key(raw_set, set_index)
            gym_exercise_set_id = _manual_set_id(source_artifact, session_key, set_key)
            sets.append(
                GymExerciseSet(
                    set_id=set_key,
                    session_id=session_key,
                    training_session_id=training_session_id,
                    gym_exercise_set_id=gym_exercise_set_id,
                    date=date,
                    exercise_name=raw_set.get("exercise_name", "unknown"),
                    source_name=MANUAL_GYM_SOURCE_NAME,
                    source_record_id=gym_exercise_set_id,
                    provenance_record_id=_manual_set_provenance_id(source_artifact, session_key, set_key),
                    confidence_label="high",
                    conflict_status="none",
                    exercise_group=raw_set.get("exercise_group"),
                    set_number=safe_int(raw_set.get("set_number") or set_index),
                    reps=safe_int(raw_set.get("reps")),
                    weight_kg=safe_float(raw_set.get("weight_kg")),
                    rir=safe_float(raw_set.get("rir")),
                    rpe=safe_float(raw_set.get("rpe")),
                    completed_bool=raw_set.get("completed_bool"),
                    note=raw_set.get("note"),
                )
            )
    return sessions, sets


def build_nutrition(nutrition_rows: dict[str, dict], db_path: Path | None, date: str) -> NutritionDaily:
    row = nutrition_rows.get(date)
    if not row:
        return NutritionDaily(date=date)

    source_record = _build_nutrition_source_record(db_path, row, date)
    provenance = _build_nutrition_provenance_record(db_path, source_record)
    return NutritionDaily(
        date=date,
        nutrition_daily_id=_nutrition_daily_id(source_record.source_record_id),
        source_name=source_record.source_name,
        source_record_id=source_record.source_record_id,
        provenance_record_id=provenance.provenance_record_id,
        conflict_status="none",
        calories_kcal=safe_float(row.get("total_calories")),
        protein_g=safe_float(row.get("total_protein_g")),
        carbs_g=safe_float(row.get("total_carbs_g")),
        fat_g=safe_float(row.get("total_fat_g")),
        fiber_g=safe_float(row.get("total_fiber_g")),
        meal_count=safe_int(row.get("meal_count")),
        food_log_completeness="logged" if safe_int(row.get("meal_count")) else "not_logged",
        top_meals_summary=row.get("top_meals_summary"),
    )


def _pick_target_date(
    daily: pd.DataFrame,
    gym_dates: list[str],
    nutrition_dates: list[str],
    subjective_dates: list[str],
    explicit_date: str | None,
    *,
    require_subjective: bool,
) -> str:
    if explicit_date:
        return explicit_date
    dates = []
    daily_dates: list[str] = []
    if not daily.empty:
        daily_dates = daily["date"].dropna().astype(str).tolist()
        dates.extend(daily_dates)
    dates.extend(gym_dates)
    dates.extend(nutrition_dates)
    dates.extend(subjective_dates)
    if require_subjective:
        overlapping_flagship_dates = sorted(set(daily_dates) & set(subjective_dates))
        if overlapping_flagship_dates:
            return overlapping_flagship_dates[-1]
    if not dates:
        raise ValueError("No input dates available for snapshot generation.")
    return max(dates)


def generate_snapshot(
    export_dir: Path,
    gym_log_path: Path | None,
    db_path: Path | None,
    target_date: str | None = None,
    user_id: int = 1,
    subjective_bundle_path: Path | None = None,
    require_subjective: bool = False,
) -> DailyHealthSnapshot:
    daily = load_csv(export_dir / "daily_summary_export.csv")
    activities = load_csv(export_dir / "activities_export.csv")
    hydration = load_csv(export_dir / "hydration_events_export.csv") if (export_dir / "hydration_events_export.csv").exists() else pd.DataFrame()

    daily["date"] = daily["date"].astype(str)
    activities["date"] = pd.to_datetime(activities["start_time_local"], errors="coerce").dt.strftime("%Y-%m-%d")

    gym_by_date, gym_dates = load_manual_gym(gym_log_path)
    manual_gym_source_artifact = gym_log_path.stem if gym_log_path else "manual_gym_sessions"
    nutrition_rows, nutrition_dates = load_nutrition_rows(db_path, user_id=user_id)
    subjective_entries, subjective_dates = load_subjective_entries(subjective_bundle_path)
    date = _pick_target_date(
        daily,
        gym_dates,
        nutrition_dates,
        subjective_dates,
        target_date,
        require_subjective=require_subjective,
    )

    daily_rows = daily[daily["date"] == date]
    daily_row = daily_rows.iloc[-1] if not daily_rows.empty else pd.Series(dtype=object)
    subjective_daily = build_subjective_daily(subjective_entries.get(date), date)

    if require_subjective and daily_rows.empty:
        raise ValueError(f"Required garmin lane not ready for target date {date}.")
    if require_subjective and subjective_daily is None:
        raise ValueError(f"Required subjective lane not ready for target date {date}.")

    sleep = build_sleep(daily_row, date, export_dir) if not daily_rows.empty else SleepDaily(date=date)
    readiness = build_readiness(daily_row, date, export_dir) if not daily_rows.empty else ReadinessDaily(date=date)
    running_sessions = build_running_sessions(activities, date, export_dir)
    manual_gym_sessions = gym_by_date.get(date, [])
    gym_sessions, gym_sets = build_gym_sessions(manual_gym_sessions, date, source_artifact=manual_gym_source_artifact)
    _, _, _, gym_set_records = build_manual_resistance_training_objects(
        manual_gym_sessions,
        date,
        source_artifact=manual_gym_source_artifact,
    ) if manual_gym_sessions else ([], [], [], [])
    nutrition = build_nutrition(nutrition_rows, db_path, date)

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
    if nutrition.source_name:
        data_backed_fields.extend(["food_logged_bool", "calories_kcal", "protein_g", "carbs_g", "fat_g"])
        if hydration_ml is not None:
            data_backed_fields.append("hydration_ml")
    else:
        generic_fields.append("nutrition_unavailable_in_v1")
    if gym_sessions:
        data_backed_fields.extend(["gym_sessions_count", "gym_total_sets", "gym_total_reps", "gym_total_load_kg"])
        generic_fields.append("manual_gym_log_non_flagship_enrichment_present")
    if subjective_daily:
        for field_name in ["subjective_energy_1_5", "subjective_soreness_1_5", "subjective_stress_1_5", "overall_day_note"]:
            if subjective_daily.get(field_name) is not None:
                data_backed_fields.append(field_name)
    elif require_subjective:
        generic_fields.append("subjective_required_for_flagship")
    if readiness.generic_guidance:
        generic_fields.append("readiness_daily.generic_guidance")

    snapshot = DailyHealthSnapshot(
        date=date,
        daily_health_snapshot_id=_snapshot_id(export_dir, date),
        provenance_record_id=_snapshot_provenance_id(export_dir, date),
        conflict_status="none",
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
        food_logged_bool=True if nutrition.source_name and (nutrition.meal_count or 0) > 0 else False if nutrition.source_name else None,
        calories_kcal=nutrition.calories_kcal,
        protein_g=nutrition.protein_g,
        carbs_g=nutrition.carbs_g,
        fat_g=nutrition.fat_g,
        hydration_ml=hydration_ml if nutrition.source_name else None,
        subjective_energy_1_5=safe_float(subjective_daily.get("subjective_energy_1_5")) if subjective_daily else None,
        subjective_soreness_1_5=safe_float(subjective_daily.get("subjective_soreness_1_5")) if subjective_daily else None,
        subjective_stress_1_5=safe_float(subjective_daily.get("subjective_stress_1_5")) if subjective_daily else None,
        overall_day_note=str(subjective_daily.get("overall_day_note")) if subjective_daily and subjective_daily.get("overall_day_note") is not None else None,
        data_backed_fields=sorted(set(data_backed_fields)),
        generic_fields=sorted(set(generic_fields)),
        source_flags={
            "garmin": not daily_rows.empty,
            "subjective": subjective_daily is not None,
            "cronometer": bool(nutrition.source_name),
            "manual_gym_log": bool(gym_sessions),
            "wger": False,
        },
        sleep_daily=asdict(sleep),
        readiness_daily=asdict(readiness),
        running_sessions=[asdict(s) for s in running_sessions],
        gym_sessions=[asdict(s) for s in gym_sessions],
        gym_set_records=[asdict(s) for s in gym_set_records],
        legacy_compatibility_aliases={"gym_exercise_sets": "gym_set_records"} if gym_sets else {},
        gym_exercise_sets=[asdict(s) for s in gym_sets],
        subjective_daily=subjective_daily,
        nutrition_daily=asdict(nutrition),
    )
    return snapshot


def write_outputs(snapshot: DailyHealthSnapshot, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    latest_path = output_dir / "daily_snapshot_latest.json"
    dated_path = output_dir / f"daily_snapshot_{snapshot.date}.json"
    payload_dict = snapshot.to_dict()
    payload_dict.setdefault("artifact_type", payload_dict.get("artifact_family", "daily_health_snapshot"))
    payload = json.dumps(payload_dict, indent=2)
    latest_path.write_text(payload)
    dated_path.write_text(payload)
    return latest_path, dated_path


def build_garmin_canonical_bundle(export_dir: Path, target_date: str) -> dict[str, object]:
    snapshot = generate_snapshot(
        export_dir=export_dir,
        gym_log_path=None,
        db_path=None,
        target_date=target_date,
        user_id=1,
    )
    source_records = [
        asdict(_build_source_record(export_dir, "daily_summary", target_date, effective_date=target_date)),
        *[
            asdict(_build_source_record(export_dir, "activity", session["session_id"].removeprefix("garmin-run-"), effective_date=target_date))
            for session in snapshot.running_sessions
        ],
    ]
    provenance_records = [
        asdict(_build_provenance_record(export_dir, snapshot.sleep_daily["source_record_id"], "sleep_daily")),
        asdict(_build_provenance_record(export_dir, snapshot.readiness_daily["source_record_id"], "readiness_daily")),
        *[
            asdict(_build_provenance_record(export_dir, session["source_record_id"], "training_session"))
            for session in snapshot.running_sessions
        ],
        {
            "artifact_family": "provenance_record",
            "provenance_record_id": snapshot.provenance_record_id,
            "source_record_id": snapshot.sleep_daily.get("source_record_id"),
            "derivation_method": "cross_source_merge",
            "supporting_refs": _supporting_refs(export_dir),
            "parser_version": PARSER_VERSION,
            "conflict_status": "none",
        },
    ]
    return {
        "source_record": source_records,
        "provenance_record": provenance_records,
        "sleep_daily": snapshot.sleep_daily,
        "readiness_daily": snapshot.readiness_daily,
        "training_session": snapshot.running_sessions,
        "daily_health_snapshot": snapshot.to_dict(),
    }


def build_nutrition_canonical_bundle(export_dir: Path, db_path: Path, target_date: str, user_id: int = 1) -> dict[str, object]:
    snapshot = generate_snapshot(
        export_dir=export_dir,
        gym_log_path=None,
        db_path=db_path,
        target_date=target_date,
        user_id=user_id,
    )
    nutrition_daily = snapshot.nutrition_daily or {}
    source_record = None
    provenance_record = None
    if nutrition_daily.get("source_record_id"):
        source_record = asdict(_build_nutrition_source_record(db_path, {"source": nutrition_daily.get("source_name")}, target_date))
        provenance_record = asdict(_build_nutrition_provenance_record(db_path, SourceRecord(**source_record)))
    return {
        "source_record": source_record,
        "provenance_record": provenance_record,
        "nutrition_daily": nutrition_daily,
        "daily_health_snapshot": snapshot.to_dict(),
        "manual_merge_policy": {
            "numeric_totals_source": "daily_summary",
            "manual_or_voice_note_behavior": "not_silently_merged_into_imported_numeric_totals",
            "meal_summary_derivation": "meal_items scoped to requested user/date",
        },
    }


def write_nutrition_proof_artifacts(export_dir: Path, db_path: Path, proof_dir: Path, target_date: str, user_id: int = 1) -> dict[str, str | list[str]]:
    proof_dir.mkdir(parents=True, exist_ok=True)
    bundle = build_nutrition_canonical_bundle(export_dir, db_path, target_date, user_id=user_id)

    source_record_path = proof_dir / "source_record.json"
    provenance_path = proof_dir / "provenance_record.json"
    nutrition_path = proof_dir / "nutrition_daily.json"
    snapshot_path = proof_dir / "daily_health_snapshot.json"
    coexistence_path = proof_dir / "manual_coexistence_policy.json"

    source_record_path.write_text(json.dumps(bundle["source_record"], indent=2))
    provenance_path.write_text(json.dumps(bundle["provenance_record"], indent=2))
    nutrition_path.write_text(json.dumps(bundle["nutrition_daily"], indent=2))
    snapshot_path.write_text(json.dumps(bundle["daily_health_snapshot"], indent=2))
    coexistence_path.write_text(json.dumps(bundle["manual_merge_policy"], indent=2))

    replay_bundle = build_nutrition_canonical_bundle(export_dir, db_path, target_date, user_id=user_id)
    stable_id_evidence = {
        "source_record_id": [bundle["source_record"]["source_record_id"], replay_bundle["source_record"]["source_record_id"]],
        "provenance_record_id": [bundle["provenance_record"]["provenance_record_id"], replay_bundle["provenance_record"]["provenance_record_id"]],
        "nutrition_daily_id": [bundle["nutrition_daily"]["nutrition_daily_id"], replay_bundle["nutrition_daily"]["nutrition_daily_id"]],
        "daily_health_snapshot_nutrition": [
            {
                "calories_kcal": bundle["daily_health_snapshot"]["calories_kcal"],
                "protein_g": bundle["daily_health_snapshot"]["protein_g"],
                "carbs_g": bundle["daily_health_snapshot"]["carbs_g"],
                "fat_g": bundle["daily_health_snapshot"]["fat_g"],
                "nutrition_daily_id": bundle["daily_health_snapshot"]["nutrition_daily"].get("nutrition_daily_id"),
            },
            {
                "calories_kcal": replay_bundle["daily_health_snapshot"]["calories_kcal"],
                "protein_g": replay_bundle["daily_health_snapshot"]["protein_g"],
                "carbs_g": replay_bundle["daily_health_snapshot"]["carbs_g"],
                "fat_g": replay_bundle["daily_health_snapshot"]["fat_g"],
                "nutrition_daily_id": replay_bundle["daily_health_snapshot"]["nutrition_daily"].get("nutrition_daily_id"),
            },
        ],
    }
    stable_id_path = proof_dir / "stable_id_evidence.json"
    stable_id_path.write_text(json.dumps(stable_id_evidence, indent=2))

    manifest = {
        "proof_target_date": target_date,
        "db_path": db_path.as_posix(),
        "export_dir": export_dir.as_posix(),
        "replay_command": f"PYTHONPATH=clean python3 clean/health_model/daily_snapshot.py --export-dir {export_dir.as_posix()} --db-path {db_path.as_posix()} --date {target_date} --user-id {user_id} --nutrition-proof-dir {proof_dir.as_posix()}",
        "sample_outputs": {
            "source_record": source_record_path.as_posix(),
            "provenance_record": provenance_path.as_posix(),
            "nutrition_daily": nutrition_path.as_posix(),
            "daily_health_snapshot": snapshot_path.as_posix(),
            "manual_coexistence_policy": coexistence_path.as_posix(),
            "stable_id_evidence": stable_id_path.as_posix(),
        },
    }
    manifest_path = proof_dir / "proof_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return {"proof_manifest": manifest_path.as_posix(), "sample_outputs": list(manifest["sample_outputs"].values())}


def write_garmin_proof_artifacts(export_dir: Path, proof_dir: Path, target_date: str) -> dict[str, str | list[str]]:
    proof_dir.mkdir(parents=True, exist_ok=True)
    bundle = build_garmin_canonical_bundle(export_dir, target_date)

    source_records_path = proof_dir / "source_record.json"
    provenance_path = proof_dir / "provenance_record.json"
    sleep_path = proof_dir / "sleep_daily.json"
    readiness_path = proof_dir / "readiness_daily.json"
    training_path = proof_dir / "training_session.json"
    snapshot_path = proof_dir / "daily_health_snapshot.json"

    source_records_path.write_text(json.dumps(bundle["source_record"], indent=2))
    provenance_path.write_text(json.dumps(bundle["provenance_record"], indent=2))
    sleep_path.write_text(json.dumps(bundle["sleep_daily"], indent=2))
    readiness_path.write_text(json.dumps(bundle["readiness_daily"], indent=2))
    training_path.write_text(json.dumps(bundle["training_session"], indent=2))
    snapshot_path.write_text(json.dumps(bundle["daily_health_snapshot"], indent=2))

    replay_bundle = build_garmin_canonical_bundle(export_dir, target_date)
    stable_id_evidence = {
        "sleep_daily_id": [bundle["sleep_daily"]["sleep_daily_id"], replay_bundle["sleep_daily"]["sleep_daily_id"]],
        "readiness_daily_id": [bundle["readiness_daily"]["readiness_daily_id"], replay_bundle["readiness_daily"]["readiness_daily_id"]],
        "training_session_ids": [
            [row["training_session_id"] for row in bundle["training_session"]],
            [row["training_session_id"] for row in replay_bundle["training_session"]],
        ],
        "daily_health_snapshot_id": [bundle["daily_health_snapshot"]["daily_health_snapshot_id"], replay_bundle["daily_health_snapshot"]["daily_health_snapshot_id"]],
        "source_record_ids": [
            [row["source_record_id"] for row in bundle["source_record"]],
            [row["source_record_id"] for row in replay_bundle["source_record"]],
        ],
    }
    stable_id_path = proof_dir / "stable_id_evidence.json"
    stable_id_path.write_text(json.dumps(stable_id_evidence, indent=2))

    manifest = {
        "proof_target_date": target_date,
        "export_dir": export_dir.as_posix(),
        "replay_command": f"PYTHONPATH=clean python3 clean/health_model/daily_snapshot.py --export-dir {export_dir.as_posix()} --date {target_date} --garmin-proof-dir {proof_dir.as_posix()}",
        "supporting_refs": _supporting_refs(export_dir),
        "sample_outputs": {
            "source_record": source_records_path.as_posix(),
            "provenance_record": provenance_path.as_posix(),
            "sleep_daily": sleep_path.as_posix(),
            "readiness_daily": readiness_path.as_posix(),
            "training_session": training_path.as_posix(),
            "daily_health_snapshot": snapshot_path.as_posix(),
            "stable_id_evidence": stable_id_path.as_posix(),
        },
    }
    manifest_path = proof_dir / "proof_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return {"proof_manifest": manifest_path.as_posix(), "sample_outputs": list(manifest["sample_outputs"].values())}


def build_manual_resistance_training_bundle(
    export_dir: Path,
    gym_log_path: Path,
    target_date: str,
) -> dict[str, object]:
    gym_by_date, _ = load_manual_gym(gym_log_path)
    source_artifact = gym_log_path.stem
    session_payloads = gym_by_date.get(target_date, [])
    training_sessions, exercise_catalog, exercise_alias, gym_set_records = build_manual_resistance_training_objects(
        session_payloads,
        target_date,
        source_artifact=source_artifact,
    )
    snapshot = generate_snapshot(
        export_dir=export_dir,
        gym_log_path=gym_log_path,
        db_path=None,
        target_date=target_date,
        user_id=1,
    )
    return {
        "manual_gym_session_input": json.loads(gym_log_path.read_text()),
        "training_sessions": [asdict(row) for row in training_sessions],
        "exercise_catalog": [asdict(row) for row in exercise_catalog],
        "exercise_alias": [asdict(row) for row in exercise_alias],
        "gym_set_record": [asdict(row) for row in gym_set_records],
        "daily_health_snapshot": snapshot.to_dict(),
    }


def write_manual_resistance_training_proof_artifacts(
    export_dir: Path,
    gym_log_path: Path,
    proof_dir: Path,
    target_date: str,
) -> dict[str, str | list[str]]:
    proof_dir.mkdir(parents=True, exist_ok=True)
    bundle = build_manual_resistance_training_bundle(export_dir, gym_log_path, target_date)

    manual_input_path = proof_dir / "manual_gym_session_input.json"
    training_sessions_path = proof_dir / "training_sessions.json"
    exercise_catalog_path = proof_dir / "exercise_catalog.json"
    exercise_alias_path = proof_dir / "exercise_alias.json"
    gym_set_record_path = proof_dir / "gym_set_record.json"
    snapshot_path = proof_dir / "daily_health_snapshot.json"

    manual_input_path.write_text(json.dumps(bundle["manual_gym_session_input"], indent=2))
    training_sessions_path.write_text(json.dumps(bundle["training_sessions"], indent=2))
    exercise_catalog_path.write_text(json.dumps({"rows": bundle["exercise_catalog"]}, indent=2))
    exercise_alias_path.write_text(json.dumps({"rows": bundle["exercise_alias"]}, indent=2))
    gym_set_record_path.write_text(json.dumps({"rows": bundle["gym_set_record"]}, indent=2))
    snapshot_path.write_text(json.dumps(bundle["daily_health_snapshot"], indent=2))

    replay_bundle = build_manual_resistance_training_bundle(export_dir, gym_log_path, target_date)
    stable_id_evidence = {
        "claim_level": "prototype",
        "replays_match": {
            "training_session_ids": [row["training_session_id"] for row in bundle["training_sessions"]] == [row["training_session_id"] for row in replay_bundle["training_sessions"]],
            "exercise_catalog_ids": [row["exercise_catalog_id"] for row in bundle["exercise_catalog"]] == [row["exercise_catalog_id"] for row in replay_bundle["exercise_catalog"]],
            "exercise_alias_ids": [row["exercise_alias_id"] for row in bundle["exercise_alias"]] == [row["exercise_alias_id"] for row in replay_bundle["exercise_alias"]],
            "gym_set_record_ids": [row["gym_set_record_id"] for row in bundle["gym_set_record"]] == [row["gym_set_record_id"] for row in replay_bundle["gym_set_record"]],
            "daily_health_snapshot_id": bundle["daily_health_snapshot"]["daily_health_snapshot_id"] == replay_bundle["daily_health_snapshot"]["daily_health_snapshot_id"],
            "daily_rollups": {
                "gym_sessions_count": bundle["daily_health_snapshot"]["gym_sessions_count"] == replay_bundle["daily_health_snapshot"]["gym_sessions_count"],
                "gym_total_sets": bundle["daily_health_snapshot"]["gym_total_sets"] == replay_bundle["daily_health_snapshot"]["gym_total_sets"],
                "gym_total_reps": bundle["daily_health_snapshot"]["gym_total_reps"] == replay_bundle["daily_health_snapshot"]["gym_total_reps"],
                "gym_total_load_kg": bundle["daily_health_snapshot"]["gym_total_load_kg"] == replay_bundle["daily_health_snapshot"]["gym_total_load_kg"],
            },
        },
        "first": {
            "training_session_ids": [row["training_session_id"] for row in bundle["training_sessions"]],
            "exercise_catalog_ids": [row["exercise_catalog_id"] for row in bundle["exercise_catalog"]],
            "exercise_alias_ids": [row["exercise_alias_id"] for row in bundle["exercise_alias"]],
            "gym_set_record_ids": [row["gym_set_record_id"] for row in bundle["gym_set_record"]],
            "daily_health_snapshot_id": bundle["daily_health_snapshot"]["daily_health_snapshot_id"],
            "gym_rollups": {
                "gym_sessions_count": bundle["daily_health_snapshot"]["gym_sessions_count"],
                "gym_total_sets": bundle["daily_health_snapshot"]["gym_total_sets"],
                "gym_total_reps": bundle["daily_health_snapshot"]["gym_total_reps"],
                "gym_total_load_kg": bundle["daily_health_snapshot"]["gym_total_load_kg"],
            },
            "source_flags": bundle["daily_health_snapshot"]["source_flags"],
        },
        "second": {
            "training_session_ids": [row["training_session_id"] for row in replay_bundle["training_sessions"]],
            "exercise_catalog_ids": [row["exercise_catalog_id"] for row in replay_bundle["exercise_catalog"]],
            "exercise_alias_ids": [row["exercise_alias_id"] for row in replay_bundle["exercise_alias"]],
            "gym_set_record_ids": [row["gym_set_record_id"] for row in replay_bundle["gym_set_record"]],
            "daily_health_snapshot_id": replay_bundle["daily_health_snapshot"]["daily_health_snapshot_id"],
            "gym_rollups": {
                "gym_sessions_count": replay_bundle["daily_health_snapshot"]["gym_sessions_count"],
                "gym_total_sets": replay_bundle["daily_health_snapshot"]["gym_total_sets"],
                "gym_total_reps": replay_bundle["daily_health_snapshot"]["gym_total_reps"],
                "gym_total_load_kg": replay_bundle["daily_health_snapshot"]["gym_total_load_kg"],
            },
            "source_flags": replay_bundle["daily_health_snapshot"]["source_flags"],
        },
    }
    stable_id_path = proof_dir / "stable_id_evidence.json"
    stable_id_path.write_text(json.dumps(stable_id_evidence, indent=2))

    manifest = {
        "proof_bundle_version": "phase-4-manual-gym-prototype-v2",
        "claim_level": "prototype",
        "claim": "manual-first Phase 4 resistance-training object layer emits training_session, exercise_catalog, exercise_alias, and gym_set_record while explicitly deferring program_block",
        "doctrine": {
            "manual_structured_gym_logs": "source_of_truth",
            "wger": "exploratory_non_flagship_only",
        },
        "target_date": target_date,
        "inputs": {
            "manual_gym_session_input": gym_log_path.as_posix(),
            "garmin_fixture_for_daily_snapshot_rollup": export_dir.as_posix(),
        },
        "live_surfaces": [
            "merge_human_inputs/manual_logs/manual_logging.py",
            "merge_human_inputs/examples/manual_gym_sessions.example.json",
            "clean/health_model/daily_snapshot.py",
            "clean/health_model/schemas.py",
            "safety/tests/test_manual_logging.py",
        ],
        "checked_in_artifacts": {
            "manual_gym_session_input": manual_input_path.as_posix(),
            "training_sessions": training_sessions_path.as_posix(),
            "exercise_catalog": exercise_catalog_path.as_posix(),
            "exercise_alias": exercise_alias_path.as_posix(),
            "gym_set_record": gym_set_record_path.as_posix(),
            "daily_health_snapshot": snapshot_path.as_posix(),
            "stable_id_evidence": stable_id_path.as_posix(),
        },
        "proof_summary": {
            "training_sessions_count": len(bundle["training_sessions"]),
            "exercise_catalog_count": len(bundle["exercise_catalog"]),
            "exercise_alias_count": len(bundle["exercise_alias"]),
            "gym_set_record_count": len(bundle["gym_set_record"]),
            "daily_snapshot_gym_sessions_count": bundle["daily_health_snapshot"]["gym_sessions_count"],
            "daily_snapshot_gym_total_sets": bundle["daily_health_snapshot"]["gym_total_sets"],
            "daily_snapshot_gym_total_reps": bundle["daily_health_snapshot"]["gym_total_reps"],
            "daily_snapshot_gym_total_load_kg": bundle["daily_health_snapshot"]["gym_total_load_kg"],
        },
        "smoke_check": "PYTHONPATH=clean:safety python3 -m unittest safety.tests.test_manual_logging",
        "limits": [
            "This is a manual-first prototype slice, not proof_complete for the full resistance-training source family.",
            "program_block remains explicitly deferred until real manual program metadata exists and is proved.",
            "No connector promotion is implied; wger stays exploratory and non-flagship.",
        ],
    }
    manifest_path = proof_dir / "proof_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return {
        "proof_manifest": manifest_path.as_posix(),
        "sample_outputs": [
            manual_input_path.as_posix(),
            training_sessions_path.as_posix(),
            exercise_catalog_path.as_posix(),
            exercise_alias_path.as_posix(),
            gym_set_record_path.as_posix(),
            snapshot_path.as_posix(),
            stable_id_path.as_posix(),
        ],
    }


def main() -> None:
    args = parse_args()
    export_dir = Path(args.export_dir)
    snapshot = generate_snapshot(
        export_dir=export_dir,
        gym_log_path=Path(args.gym_log_path) if args.gym_log_path else None,
        db_path=Path(args.db_path) if args.db_path else None,
        target_date=args.date,
        user_id=args.user_id,
        subjective_bundle_path=Path(args.subjective_bundle_path) if args.subjective_bundle_path else None,
        require_subjective=True,
    )
    latest_path, dated_path = write_outputs(snapshot, Path(args.output_dir))
    print(f"wrote {latest_path}")
    print(f"wrote {dated_path}")
    if args.garmin_proof_dir:
        proof = write_garmin_proof_artifacts(export_dir, Path(args.garmin_proof_dir), snapshot.date)
        print(f"wrote {proof['proof_manifest']}")
    if args.nutrition_proof_dir:
        proof = write_nutrition_proof_artifacts(export_dir, Path(args.db_path), Path(args.nutrition_proof_dir), snapshot.date, user_id=args.user_id)
        print(f"wrote {proof['proof_manifest']}")


if __name__ == "__main__":
    main()
