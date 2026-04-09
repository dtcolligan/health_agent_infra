from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "garmin" / "export"

EXPORT_FILES = {
    "uds": "DI_CONNECT/DI-Connect-Aggregator/UDSFile_",
    "sleep": "DI_CONNECT/DI-Connect-Wellness/" ,
    "readiness": "DI_CONNECT/DI-Connect-Metrics/TrainingReadinessDTO_",
    "acute_load": "DI_CONNECT/DI-Connect-Metrics/MetricsAcuteTrainingLoad_",
    "training_history": "DI_CONNECT/DI-Connect-Metrics/TrainingHistory_",
    "health_status": "DI_CONNECT/DI-Connect-Wellness/",
    "activities": "DI_CONNECT/DI-Connect-Fitness/",
    "hydration": "DI_CONNECT/DI-Connect-Aggregator/HydrationLogFile_",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize a Garmin GDPR export zip into repo-safe runtime datasets.")
    parser.add_argument("zip_path", help="Path to the Garmin export zip file")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Directory for derived runtime outputs (default: {DEFAULT_OUTPUT_DIR})",
    )
    return parser.parse_args()


def read_json_from_zip(zf: ZipFile, matcher: str, *, contains: str | None = None) -> Any:
    for name in zf.namelist():
        if not name.endswith(".json"):
            continue
        if matcher not in name:
            continue
        if contains and contains not in name:
            continue
        return json.loads(zf.read(name))
    raise FileNotFoundError(f"Missing export file matching {matcher!r} {contains or ''}".strip())


def load_export_frames(zip_path: Path) -> dict[str, pd.DataFrame]:
    with ZipFile(zip_path) as zf:
        uds = pd.DataFrame(read_json_from_zip(zf, EXPORT_FILES["uds"]))

        sleep_raw = read_json_from_zip(zf, EXPORT_FILES["sleep"], contains="sleepData")
        sleep = pd.DataFrame(
            [row for row in sleep_raw if isinstance(row, dict) and "calendarDate" in row]
        )

        readiness = pd.DataFrame(read_json_from_zip(zf, EXPORT_FILES["readiness"]))
        acute_load = pd.DataFrame(read_json_from_zip(zf, EXPORT_FILES["acute_load"]))
        training_history = pd.DataFrame(read_json_from_zip(zf, EXPORT_FILES["training_history"]))
        health_status = pd.DataFrame(read_json_from_zip(zf, EXPORT_FILES["health_status"], contains="healthStatusData"))

        activities_raw = read_json_from_zip(zf, EXPORT_FILES["activities"], contains="summarizedActivities")
        if isinstance(activities_raw, list):
            activities_raw = activities_raw[0]
        activities = pd.DataFrame(activities_raw.get("summarizedActivitiesExport", []))

        hydration = pd.DataFrame(read_json_from_zip(zf, EXPORT_FILES["hydration"]))

    return {
        "uds": uds,
        "sleep": sleep,
        "readiness": readiness,
        "acute_load": acute_load,
        "training_history": training_history,
        "health_status": health_status,
        "activities": activities,
        "hydration": hydration,
    }


def normalize_date(series: pd.Series) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce")
    numeric_mask = dt.isna()
    if numeric_mask.any():
        numeric = pd.to_numeric(series[numeric_mask], errors="coerce")
        dt.loc[numeric_mask] = pd.to_datetime(numeric, unit="ms", errors="coerce")
    return dt.dt.strftime("%Y-%m-%d")


def latest_per_date(df: pd.DataFrame, date_column: str = "date", sort_column: str | None = None) -> pd.DataFrame:
    if df.empty:
        return df
    if sort_column and sort_column in df.columns:
        df = df.sort_values([date_column, sort_column])
    return df.drop_duplicates(subset=[date_column], keep="last").reset_index(drop=True)


def extract_total_stress(stress_blob: Any) -> Any:
    if not isinstance(stress_blob, dict):
        return None
    for item in stress_blob.get("aggregatorList", []):
        if item.get("type") == "TOTAL":
            return item.get("averageStressLevel")
    return stress_blob.get("averageStressLevel")


def extract_body_battery(body_battery_blob: Any) -> Any:
    if not isinstance(body_battery_blob, dict):
        return None
    preferred = ["ENDOFDAY", "MOSTRECENT", "HIGHEST", "STARTOFDAY"]
    stats = body_battery_blob.get("bodyBatteryStatList", [])
    for kind in preferred:
        for item in stats:
            if item.get("bodyBatteryStatType") == kind:
                return item.get("statsValue")
    return body_battery_blob.get("chargedValue")


def normalize_uuid(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("uuid")
    return value


def build_daily_summary(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    uds = frames["uds"].copy()
    uds["date"] = normalize_date(uds["calendarDate"])
    uds["allDayStress"] = uds["allDayStress"].apply(extract_total_stress)
    uds["bodyBattery"] = uds["bodyBattery"].apply(extract_body_battery)
    daily = uds.rename(
        columns={
            "totalSteps": "steps",
            "totalDistanceMeters": "distance_m",
            "activeKilocalories": "active_kcal",
            "totalKilocalories": "total_kcal",
            "moderateIntensityMinutes": "moderate_intensity_min",
            "vigorousIntensityMinutes": "vigorous_intensity_min",
            "restingHeartRate": "resting_hr",
            "minHeartRate": "min_hr_day",
            "maxHeartRate": "max_hr_day",
            "floorsAscendedInMeters": "floors_ascended_m",
            "allDayStress": "all_day_stress",
            "bodyBattery": "body_battery",
            "averageMonitoringEnvironmentAltitude": "avg_environment_altitude_m",
        }
    )[
        [
            "date",
            "steps",
            "distance_m",
            "active_kcal",
            "total_kcal",
            "moderate_intensity_min",
            "vigorous_intensity_min",
            "resting_hr",
            "min_hr_day",
            "max_hr_day",
            "floors_ascended_m",
            "all_day_stress",
            "body_battery",
            "avg_environment_altitude_m",
        ]
    ]
    daily = latest_per_date(daily)

    sleep = frames["sleep"].copy()
    sleep["date"] = normalize_date(sleep["calendarDate"])
    sleep_scores = pd.json_normalize(sleep["sleepScores"]).add_prefix("sleep_score_")
    sleep = pd.concat([sleep.drop(columns=["sleepScores"]), sleep_scores], axis=1).rename(
        columns={
            "deepSleepSeconds": "sleep_deep_sec",
            "lightSleepSeconds": "sleep_light_sec",
            "remSleepSeconds": "sleep_rem_sec",
            "awakeSleepSeconds": "sleep_awake_sec",
            "averageRespiration": "avg_sleep_respiration",
            "avgSleepStress": "avg_sleep_stress",
            "awakeCount": "awake_count",
            "sleep_score_overallScore": "sleep_score_overall",
            "sleep_score_qualityScore": "sleep_score_quality",
            "sleep_score_durationScore": "sleep_score_duration",
            "sleep_score_recoveryScore": "sleep_score_recovery",
        }
    )[
        [
            "date",
            "sleep_deep_sec",
            "sleep_light_sec",
            "sleep_rem_sec",
            "sleep_awake_sec",
            "avg_sleep_respiration",
            "avg_sleep_stress",
            "awake_count",
            "sleep_score_overall",
            "sleep_score_quality",
            "sleep_score_duration",
            "sleep_score_recovery",
        ]
    ]
    sleep = latest_per_date(sleep)

    readiness = frames["readiness"].copy()
    readiness["date"] = normalize_date(readiness["calendarDate"])
    readiness["training_recovery_time_hours"] = pd.to_numeric(readiness.get("recoveryTime"), errors="coerce") / 60.0
    readiness = readiness.rename(
        columns={
            "level": "training_readiness_level",
            "sleepScoreFactorPercent": "training_readiness_sleep_pct",
            "hrvFactorPercent": "training_readiness_hrv_pct",
            "stressHistoryFactorPercent": "training_readiness_stress_pct",
            "sleepHistoryFactorPercent": "training_readiness_sleep_history_pct",
            "acwrFactorPercent": "training_readiness_load_pct",
            "hrvWeeklyAverage": "training_readiness_hrv_weekly_avg",
            "validSleep": "training_readiness_valid_sleep",
        }
    )[
        [
            "date",
            "training_readiness_level",
            "training_recovery_time_hours",
            "training_readiness_sleep_pct",
            "training_readiness_hrv_pct",
            "training_readiness_stress_pct",
            "training_readiness_sleep_history_pct",
            "training_readiness_load_pct",
            "training_readiness_hrv_weekly_avg",
            "training_readiness_valid_sleep",
        ]
    ]
    readiness = latest_per_date(readiness, sort_column="training_recovery_time_hours")

    acute = frames["acute_load"].copy()
    acute["date"] = normalize_date(acute["calendarDate"])
    acute = acute.rename(
        columns={
            "dailyTrainingLoadAcute": "acute_load",
            "dailyTrainingLoadChronic": "chronic_load",
            "acwrStatus": "acwr_status",
            "acwrStatusFeedback": "acwr_status_feedback",
        }
    )[["date", "acute_load", "chronic_load", "acwr_status", "acwr_status_feedback"]]
    acute = latest_per_date(acute, sort_column="acute_load")

    training = frames["training_history"].copy()
    training["date"] = normalize_date(training["calendarDate"])
    training = training.rename(
        columns={
            "trainingStatus": "training_status",
            "trainingStatus2FeedbackPhrase": "training_status_feedback",
        }
    )[["date", "training_status", "training_status_feedback"]]
    training = latest_per_date(training)

    health = build_health_pivot(frames["health_status"])

    merged = daily.merge(sleep, on="date", how="left")
    merged = merged.merge(readiness, on="date", how="left")
    merged = merged.merge(acute, on="date", how="left")
    merged = merged.merge(training, on="date", how="left")
    merged = merged.merge(health, on="date", how="left")
    return merged.sort_values("date").reset_index(drop=True)


def build_health_pivot(health_status: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in health_status.to_dict(orient="records"):
        date = normalize_date(pd.Series([row.get("calendarDate")])).iloc[0]
        entry: dict[str, Any] = {"date": date}
        for metric in row.get("metrics", []):
            metric_type = str(metric.get("type", "")).lower()
            if not metric_type:
                continue
            prefix = f"health_{metric_type}"
            entry[f"{prefix}_value"] = metric.get("value")
            entry[f"{prefix}_status"] = metric.get("status")
            entry[f"{prefix}_baseline_low"] = metric.get("baselineLowerLimit")
            entry[f"{prefix}_baseline_high"] = metric.get("baselineUpperLimit")
        rows.append(entry)
    health = pd.DataFrame(rows)
    if health.empty:
        return pd.DataFrame(columns=["date"])
    return health.drop_duplicates(subset=["date"]).sort_values("date")


def build_activities_export(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    activities = frames["activities"].copy()
    if activities.empty:
        return pd.DataFrame()

    activities["start_time_local"] = pd.to_datetime(activities["startTimeLocal"], unit="ms", errors="coerce")
    activities["start_time_gmt"] = pd.to_datetime(activities["startTimeGmt"], unit="ms", errors="coerce")
    activities["duration"] = pd.to_numeric(activities["duration"], errors="coerce") / 1000.0
    activities["distance"] = pd.to_numeric(activities["distance"], errors="coerce") / 100.0
    activities["elevationGain"] = pd.to_numeric(activities["elevationGain"], errors="coerce") / 100.0
    activities["avgSpeed"] = pd.to_numeric(activities["avgSpeed"], errors="coerce") * 10.0
    activities["maxSpeed"] = pd.to_numeric(activities["maxSpeed"], errors="coerce") * 10.0
    return activities.rename(
        columns={
            "activityId": "activity_id",
            "activityType": "activity_type",
            "sportType": "sport_type",
            "duration": "duration_sec",
            "distance": "distance_m",
            "avgHr": "avg_hr",
            "maxHr": "max_hr",
            "avgSpeed": "avg_speed",
            "maxSpeed": "max_speed",
            "elevationGain": "elevation_gain_m",
            "aerobicTrainingEffect": "training_effect_aerobic",
            "avgRunCadence": "avg_run_cadence",
            "activityTrainingLoad": "activity_training_load",
        }
    )[
        [
            "activity_id",
            "start_time_local",
            "start_time_gmt",
            "activity_type",
            "sport_type",
            "duration_sec",
            "distance_m",
            "calories",
            "avg_hr",
            "max_hr",
            "avg_speed",
            "max_speed",
            "steps",
            "elevation_gain_m",
            "training_effect_aerobic",
            "avg_run_cadence",
            "activity_training_load",
        ]
    ].sort_values("start_time_local").reset_index(drop=True)


def build_hydration_export(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    hydration = frames["hydration"].copy()
    if hydration.empty:
        return pd.DataFrame()
    hydration["date"] = normalize_date(hydration["calendarDate"])
    hydration["timestamp_local"] = pd.to_datetime(hydration["timestampLocal"], errors="coerce")
    hydration["uuid"] = hydration["uuid"].apply(normalize_uuid)
    return hydration.rename(
        columns={
            "valueInML": "value_ml",
            "estimatedSweatLossInML": "estimated_sweat_loss_ml",
            "measuredSweatLossInML": "measured_sweat_loss_ml",
            "hydrationSource": "hydration_source",
            "activityId": "activity_id",
        }
    )[
        [
            "uuid",
            "date",
            "timestamp_local",
            "hydration_source",
            "value_ml",
            "estimated_sweat_loss_ml",
            "measured_sweat_loss_ml",
            "activity_id",
        ]
    ].sort_values(["date", "timestamp_local"]).reset_index(drop=True)


def write_outputs(output_dir: Path, daily: pd.DataFrame, activities: pd.DataFrame, hydration: pd.DataFrame, health: pd.DataFrame) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    daily.to_csv(output_dir / "daily_summary_export.csv", index=False)
    activities.to_csv(output_dir / "activities_export.csv", index=False)
    hydration.to_csv(output_dir / "hydration_events_export.csv", index=False)
    health.to_csv(output_dir / "health_status_pivot_export.csv", index=False)

    manifest = {
        "daily_summary_export.csv": int(len(daily)),
        "activities_export.csv": int(len(activities)),
        "hydration_events_export.csv": int(len(hydration)),
        "health_status_pivot_export.csv": int(len(health)),
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    zip_path = Path(args.zip_path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    frames = load_export_frames(zip_path)
    daily = build_daily_summary(frames)
    activities = build_activities_export(frames)
    hydration = build_hydration_export(frames)
    health = build_health_pivot(frames["health_status"])
    write_outputs(output_dir, daily, activities, hydration, health)

    print(f"Wrote derived export datasets to {output_dir}")
    for path in sorted(output_dir.iterdir()):
        print(path.name)


if __name__ == "__main__":
    main()
