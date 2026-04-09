from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

READINESS_SCORE_MAP = {
    "VERY_LOW": 1,
    "LOW": 2,
    "MODERATE": 3,
    "HIGH": 4,
    "PRIMED": 5,
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_DIR = PROJECT_ROOT / "data" / "garmin" / "export"
DEFAULT_REPORT_PATH = DEFAULT_EXPORT_DIR / "first_analysis_report.md"
DEFAULT_SUMMARY_PATH = DEFAULT_EXPORT_DIR / "first_analysis_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a first bounded analysis artifact from normalized Garmin export outputs.")
    parser.add_argument("--export-dir", default=str(DEFAULT_EXPORT_DIR), help=f"Directory containing normalized export outputs (default: {DEFAULT_EXPORT_DIR})")
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH), help=f"Markdown report path (default: {DEFAULT_REPORT_PATH})")
    parser.add_argument("--summary-path", default=str(DEFAULT_SUMMARY_PATH), help=f"JSON summary path (default: {DEFAULT_SUMMARY_PATH})")
    return parser.parse_args()


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def safe_float(value) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def safe_int(value) -> int | None:
    try:
        if pd.isna(value):
            return None
        return int(round(float(value)))
    except Exception:
        return None


def _delta(current, previous):
    current = safe_float(current)
    previous = safe_float(previous)
    if current is None or previous is None:
        return None
    return round(current - previous, 2)


def _classify_snapshot(latest_day: dict, recent_7_day_averages: dict) -> dict:
    readiness = (latest_day.get("training_readiness_level") or "UNKNOWN").upper()
    sleep_score = latest_day.get("sleep_score_overall")
    body_battery = latest_day.get("body_battery")
    steps = latest_day.get("steps")
    rolling_steps = recent_7_day_averages.get("steps")
    training_status = latest_day.get("training_status")

    positives = []
    cautions = []

    if sleep_score is not None and sleep_score >= 80:
        positives.append("sleep score is in a solid range")
    elif sleep_score is not None and sleep_score < 70:
        cautions.append("sleep score is soft enough to avoid calling this a hard-push day")

    if body_battery is not None and body_battery >= 60:
        positives.append("body battery suggests good available energy")
    elif body_battery is not None and body_battery < 40:
        cautions.append("body battery is subdued, so recovery may still be incomplete")

    if steps is not None and rolling_steps is not None and steps >= rolling_steps:
        positives.append("movement stayed at or above the recent weekly baseline")

    if training_status and str(training_status).upper() == "PRODUCTIVE":
        positives.append("Garmin marks the broader block as productive")

    if readiness in {"VERY_LOW", "LOW"}:
        cautions.append("training readiness is low, so intensity should stay conservative")

    if readiness in {"HIGH", "PRIMED"} and sleep_score is not None and sleep_score >= 80:
        label = "build-ready"
        headline = "Recovery looks supportive for normal training, with no obvious red flags in the latest snapshot."
    elif readiness in {"VERY_LOW", "LOW"}:
        label = "absorb-and-maintain"
        headline = "The latest day reads more like an absorb-the-work snapshot than a signal to push harder."
    else:
        label = "steady"
        headline = "The latest day looks broadly steady, with enough support for normal training if effort stays sensible."

    return {
        "label": label,
        "headline": headline,
        "positives": positives,
        "cautions": cautions,
        "disclaimer": "Conservative interpretation only, this is a descriptive training cue rather than medical advice.",
    }


def _build_visual_payload(daily: pd.DataFrame, running: pd.DataFrame) -> dict:
    ordered_daily = daily.sort_values("date").copy()
    ordered_daily["training_readiness_score"] = ordered_daily["training_readiness_level"].map(READINESS_SCORE_MAP)

    daily_points = []
    for _, row in ordered_daily.tail(21).iterrows():
        if pd.isna(row.get("date")):
            continue
        daily_points.append({
            "date": row["date"].strftime("%Y-%m-%d"),
            "steps": safe_int(row.get("steps")),
            "sleep_score": safe_int(row.get("sleep_score_overall")),
            "body_battery": safe_int(row.get("body_battery")),
            "resting_hr": safe_int(row.get("resting_hr")),
            "hrv": safe_int(row.get("health_hrv_value")),
            "readiness_level": row.get("training_readiness_level"),
            "readiness_score": safe_int(row.get("training_readiness_score")),
        })

    running_points = []
    if not running.empty:
        ordered_runs = running.sort_values("start_time_local").copy()
        for _, row in ordered_runs.tail(12).iterrows():
            if pd.isna(row.get("start_time_local")):
                continue
            running_points.append({
                "date": row["start_time_local"].strftime("%Y-%m-%d"),
                "distance_km": round(float(row["distance_m"]) / 1000, 2) if pd.notna(row.get("distance_m")) else None,
                "duration_min": round(float(row["duration_sec"]) / 60, 1) if pd.notna(row.get("duration_sec")) else None,
                "avg_hr": safe_int(row.get("avg_hr")),
                "training_load": safe_float(row.get("activity_training_load")),
            })

    return {
        "daily_points": daily_points,
        "running_points": running_points,
    }


def build_summary(export_dir: Path) -> dict:
    daily = load_csv(export_dir / "daily_summary_export.csv")
    activities = load_csv(export_dir / "activities_export.csv")
    hydration = load_csv(export_dir / "hydration_events_export.csv")
    health = load_csv(export_dir / "health_status_pivot_export.csv")

    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    activities["start_time_local"] = pd.to_datetime(activities["start_time_local"], errors="coerce")
    hydration["date"] = pd.to_datetime(hydration["date"], errors="coerce")
    health["date"] = pd.to_datetime(health["date"], errors="coerce")

    date_min = daily["date"].min()
    date_max = daily["date"].max()
    running = activities[activities["sport_type"].fillna("").str.upper() == "RUNNING"].copy()

    best_run = None
    latest_run = None
    if not running.empty:
        best_run_row = running.sort_values("distance_m", ascending=False).iloc[0]
        latest_run_row = running.sort_values("start_time_local").iloc[-1]
        best_run = {
            "date": best_run_row["start_time_local"].strftime("%Y-%m-%d") if pd.notna(best_run_row["start_time_local"]) else None,
            "distance_km": round(float(best_run_row["distance_m"]) / 1000, 2) if pd.notna(best_run_row["distance_m"]) else None,
            "duration_min": round(float(best_run_row["duration_sec"]) / 60, 1) if pd.notna(best_run_row["duration_sec"]) else None,
            "avg_hr": safe_int(best_run_row.get("avg_hr")),
            "training_load": safe_float(best_run_row.get("activity_training_load")),
        }
        latest_run = {
            "date": latest_run_row["start_time_local"].strftime("%Y-%m-%d") if pd.notna(latest_run_row["start_time_local"]) else None,
            "distance_km": round(float(latest_run_row["distance_m"]) / 1000, 2) if pd.notna(latest_run_row["distance_m"]) else None,
            "duration_min": round(float(latest_run_row["duration_sec"]) / 60, 1) if pd.notna(latest_run_row["duration_sec"]) else None,
            "avg_hr": safe_int(latest_run_row.get("avg_hr")),
            "training_load": safe_float(latest_run_row.get("activity_training_load")),
        }

    ordered_daily = daily.sort_values("date")
    latest = ordered_daily.iloc[-1]
    recent7 = ordered_daily.tail(7)
    previous7 = ordered_daily.tail(14).head(7)

    summary = {
        "date_range": {
            "start": date_min.strftime("%Y-%m-%d") if pd.notna(date_min) else None,
            "end": date_max.strftime("%Y-%m-%d") if pd.notna(date_max) else None,
            "days": safe_int((date_max - date_min).days + 1) if pd.notna(date_min) and pd.notna(date_max) else None,
        },
        "coverage": {
            "daily_rows": len(daily),
            "activity_rows": len(activities),
            "running_activity_rows": len(running),
            "hydration_rows": len(hydration),
            "health_rows": len(health),
        },
        "latest_day": {
            "date": latest["date"].strftime("%Y-%m-%d") if pd.notna(latest["date"]) else None,
            "steps": safe_int(latest.get("steps")),
            "sleep_score_overall": safe_int(latest.get("sleep_score_overall")),
            "training_readiness_level": latest.get("training_readiness_level"),
            "body_battery": safe_int(latest.get("body_battery")),
            "training_status": latest.get("training_status"),
        },
        "recent_7_day_averages": {
            "steps": safe_int(recent7["steps"].mean()),
            "sleep_score_overall": safe_int(recent7["sleep_score_overall"].mean()),
            "resting_hr": safe_int(recent7["resting_hr"].mean()),
            "body_battery": safe_int(recent7["body_battery"].mean()),
            "acute_load": safe_float(recent7["acute_load"].mean()),
        },
        "recent_7_day_vs_previous_7_day": {
            "steps_delta": _delta(recent7["steps"].mean(), previous7["steps"].mean()),
            "sleep_score_delta": _delta(recent7["sleep_score_overall"].mean(), previous7["sleep_score_overall"].mean()),
            "resting_hr_delta": _delta(recent7["resting_hr"].mean(), previous7["resting_hr"].mean()),
            "body_battery_delta": _delta(recent7["body_battery"].mean(), previous7["body_battery"].mean()),
        },
        "activity_summary": {
            "total_activities": len(activities),
            "total_running_distance_km": round(running["distance_m"].fillna(0).sum() / 1000, 2),
            "avg_running_distance_km": round(running["distance_m"].fillna(0).mean() / 1000, 2) if len(running) else None,
            "best_run": best_run,
            "latest_run": latest_run,
        },
        "signals": {
            "sleep_score_days_present": int(daily["sleep_score_overall"].notna().sum()),
            "training_readiness_days_present": int(daily["training_readiness_level"].notna().sum()),
            "hrv_days_present": int(daily.get("health_hrv_value", pd.Series(dtype=float)).notna().sum()),
            "hydration_events_with_estimated_sweat_loss": int(hydration["estimated_sweat_loss_ml"].fillna(0).gt(0).sum()),
        },
    }
    summary["interpretation"] = _classify_snapshot(summary["latest_day"], summary["recent_7_day_averages"])
    summary["visuals"] = _build_visual_payload(daily, running)
    return summary


def render_report(summary: dict) -> str:
    br = summary["activity_summary"].get("best_run") or {}
    return f"""# First Garmin export analysis

Internal runtime artifact generated from normalized Garmin export outputs.

## Coverage
- date range: {summary['date_range']['start']} -> {summary['date_range']['end']} ({summary['date_range']['days']} days)
- daily rows: {summary['coverage']['daily_rows']}
- activity rows: {summary['coverage']['activity_rows']}
- running activities: {summary['coverage']['running_activity_rows']}
- hydration rows: {summary['coverage']['hydration_rows']}
- health rows: {summary['coverage']['health_rows']}

## Latest day snapshot
- date: {summary['latest_day']['date']}
- steps: {summary['latest_day']['steps']}
- sleep score: {summary['latest_day']['sleep_score_overall']}
- body battery: {summary['latest_day']['body_battery']}
- training readiness: {summary['latest_day']['training_readiness_level']}
- training status: {summary['latest_day']['training_status']}

## Recent 7-day averages
- steps: {summary['recent_7_day_averages']['steps']}
- sleep score: {summary['recent_7_day_averages']['sleep_score_overall']}
- resting HR: {summary['recent_7_day_averages']['resting_hr']}
- body battery: {summary['recent_7_day_averages']['body_battery']}
- acute load: {summary['recent_7_day_averages']['acute_load']}

## Week-over-week change
- steps delta vs prior 7 days: {summary['recent_7_day_vs_previous_7_day']['steps_delta']}
- sleep score delta vs prior 7 days: {summary['recent_7_day_vs_previous_7_day']['sleep_score_delta']}
- resting HR delta vs prior 7 days: {summary['recent_7_day_vs_previous_7_day']['resting_hr_delta']}
- body battery delta vs prior 7 days: {summary['recent_7_day_vs_previous_7_day']['body_battery_delta']}

## Activity summary
- total activities: {summary['activity_summary']['total_activities']}
- total running distance: {summary['activity_summary']['total_running_distance_km']} km
- average running distance: {summary['activity_summary']['avg_running_distance_km']} km
- best run: {br.get('date')} | {br.get('distance_km')} km | {br.get('duration_min')} min | avg HR {br.get('avg_hr')} | load {br.get('training_load')}
- latest run: {summary['activity_summary']['latest_run'].get('date') if summary['activity_summary'].get('latest_run') else None} | {summary['activity_summary']['latest_run'].get('distance_km') if summary['activity_summary'].get('latest_run') else None} km | {summary['activity_summary']['latest_run'].get('duration_min') if summary['activity_summary'].get('latest_run') else None} min

## Interpretation
- label: {summary['interpretation']['label']}
- headline: {summary['interpretation']['headline']}
- positives: {', '.join(summary['interpretation']['positives']) or 'none'}
- cautions: {', '.join(summary['interpretation']['cautions']) or 'none'}
- note: {summary['interpretation']['disclaimer']}

## Signal availability
- sleep-score days present: {summary['signals']['sleep_score_days_present']}
- training-readiness days present: {summary['signals']['training_readiness_days_present']}
- HRV days present: {summary['signals']['hrv_days_present']}
- hydration events with estimated sweat loss: {summary['signals']['hydration_events_with_estimated_sweat_loss']}

## Why this matters
- proves the GDPR export can become a usable analysis surface inside `garmin_lab`
- gives a first bounded runtime artifact without requiring live Garmin login
- creates a clean base for richer readiness, dashboards, and interpretation passes
"""


def main() -> None:
    args = parse_args()
    export_dir = Path(args.export_dir)
    report_path = Path(args.report_path)
    summary_path = Path(args.summary_path)

    summary = build_summary(export_dir)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary))
    summary_path.write_text(json.dumps(summary, indent=2))

    print(f"wrote {report_path}")
    print(f"wrote {summary_path}")


if __name__ == "__main__":
    main()
