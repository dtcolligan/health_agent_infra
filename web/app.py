"""
app.py — Flask web interface for the health logger.

Thin HTTP layer over the existing bot.parser + bot.db modules.
Run with: python -m web.app
"""

import json
import os
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

from bot.config import get_user_date, DB_PATH
from garmin.readiness import get_readiness_for_date
from garmin.coaching import get_daily_coaching_summary
from garmin.analyze_export import build_summary
from bot.parser import parse_health_message
from bot.db import (
    init_db, save_message, update_message_json, save_entries,
    get_daily_summary, get_meal_items, get_exercise_entries,
    get_subjective_entries, get_targets, set_target,
    get_recent_dates, get_logging_streak, delete_last_entry, delete_item,
    get_weekly_summary, get_exercise_sets, get_gym_summary,
    get_exercise_history, get_all_time_prs, get_muscle_groups,
)

app = Flask(__name__, static_folder="static")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
GARMIN_EXPORT_DIR = PROJECT_ROOT / "data" / "garmin" / "export"


def _build_day_response(date_for: str, confirmation=None) -> dict:
    """Build a full day state response for the frontend."""
    summary = get_daily_summary(date_for)
    meals = get_meal_items(date_for)
    exercises = get_exercise_entries(date_for)
    subjective = get_subjective_entries(date_for)
    targets = get_targets()
    streak = get_logging_streak(date_for)

    exercise_sets = get_exercise_sets(date_for)
    gym_summary = get_gym_summary(date_for)
    prs = get_all_time_prs()
    muscle_groups = get_muscle_groups(date_for)

    resp = {
        "date": date_for,
        "day_summary": summary,
        "meals": meals,
        "exercises": exercises,
        "exercise_sets": exercise_sets,
        "gym_summary": gym_summary,
        "prs": prs,
        "muscle_groups": muscle_groups,
        "subjective": subjective,
        "targets": targets,
        "streak": streak,
    }
    if confirmation is not None:
        resp["confirmation"] = confirmation
    return resp


# --- Static files ---

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/dashboard")
def dashboard():
    dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "dashboard")
    return send_from_directory(dashboard_dir, "dashboard.html")


@app.route("/garmin-export")
def garmin_export_dashboard():
    dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "dashboard")
    return send_from_directory(dashboard_dir, "garmin_export.html")


@app.route("/dashboard_data.json")
@app.route("/dashboard/dashboard_data.json")
def dashboard_data():
    dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "dashboard")
    return send_from_directory(dashboard_dir, "dashboard_data.json")


@app.route("/api/garmin/export-overview")
def garmin_export_overview():
    if not GARMIN_EXPORT_DIR.exists():
        return jsonify({"status": "missing", "message": "Normalized Garmin export outputs were not found."}), 404

    try:
        return jsonify({"status": "ok", "summary": build_summary(GARMIN_EXPORT_DIR)})
    except FileNotFoundError as exc:
        return jsonify({"status": "missing", "message": f"Required export artifact missing: {exc}"}), 404


# --- API routes ---

@app.route("/api/log", methods=["POST"])
def log_entry():
    """Parse and save a health message."""
    data = request.json
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"status": "error", "message": "No message provided"}), 400

    date_for = data.get("date") or get_user_date()

    msg_id = save_message(raw_text=message, date_for=date_for)

    # Parse via Claude
    result = parse_health_message(message, date_for)
    raw_json = result.get("raw_response", json.dumps(result))
    update_message_json(msg_id, raw_json)

    if result["type"] == "clarification":
        return jsonify({"status": "clarification", "question": result["question"]})

    if result["type"] == "error":
        return jsonify({"status": "error", "message": result["message"]}), 400

    # Check for content
    parsed = result["data"]
    has_content = parsed.get("meals") or parsed.get("exercises") or parsed.get("subjective")

    if not has_content:
        return jsonify({
            "status": "empty",
            "message": "I didn't spot any food, exercise, or wellness info in that message.",
        })

    # Save structured data
    save_entries(msg_id, parsed, date_for)

    resp = _build_day_response(date_for, confirmation=parsed)
    resp["status"] = "logged"
    return jsonify(resp)


@app.route("/api/today")
def today():
    """Get today's full state."""
    date_for = get_user_date()
    return jsonify(_build_day_response(date_for))


@app.route("/api/day/<date_for>")
def day(date_for: str):
    """Get a specific day's full state."""
    return jsonify(_build_day_response(date_for))


@app.route("/api/history")
def history():
    """Get recent days with summaries."""
    dates = get_recent_dates(limit=14)
    days = []
    for d in dates:
        summary = get_daily_summary(d)
        if summary:
            days.append({"date": d, **summary})
    return jsonify({"days": days})


@app.route("/api/gym-history")
def gym_history():
    """Get recent gym stats for chart."""
    days = get_exercise_history(limit=14)
    return jsonify({"days": days})


@app.route("/api/readiness/today")
def readiness_today():
    """Get latest readiness assessment from engineered Garmin features."""
    return jsonify(get_readiness_for_date())


@app.route("/api/readiness/<date_for>")
def readiness_for_date(date_for: str):
    """Get readiness assessment for a specific date."""
    return jsonify(get_readiness_for_date(date_for))


@app.route("/api/coaching/today")
def coaching_today():
    """Get a user-facing daily coaching summary."""
    return jsonify(get_daily_coaching_summary())


@app.route("/api/coaching/<date_for>")
def coaching_for_date(date_for: str):
    """Get a user-facing daily coaching summary for a specific date."""
    return jsonify(get_daily_coaching_summary(date_for))


@app.route("/api/undo", methods=["POST"])
def undo():
    """Delete last entry for a date."""
    data = request.json or {}
    date_for = data.get("date") or get_user_date()
    deleted = delete_last_entry(date_for)
    if deleted:
        resp = _build_day_response(date_for)
        resp["status"] = "undone"
        resp["deleted_text"] = deleted[:80]
        return jsonify(resp)
    return jsonify({"status": "nothing", "message": "Nothing to undo."})


@app.route("/api/delete-item", methods=["POST"])
def delete_item_route():
    """Delete a single meal item, exercise, or subjective entry."""
    data = request.json or {}
    item_id = data.get("id")
    item_type = data.get("type")

    if not item_id or item_type not in ("meal", "exercise", "subjective"):
        return jsonify({"status": "error", "message": "Missing id or invalid type"}), 400

    result = delete_item(int(item_id), item_type)
    if result is None:
        return jsonify({"status": "error", "message": "Item not found"}), 404

    resp = _build_day_response(result["date_for"])
    resp["status"] = "deleted"
    resp["deleted_name"] = result["deleted_name"]
    return jsonify(resp)


@app.route("/api/targets", methods=["GET"])
def get_targets_route():
    """Get current targets."""
    return jsonify(get_targets())


@app.route("/api/targets", methods=["POST"])
def set_targets_route():
    """Set a target."""
    data = request.json
    metric = data.get("metric", "").lower()
    value = data.get("value")

    valid = {"calories", "protein", "carbs", "fat", "duration", "volume", "sets"}
    if metric not in valid:
        return jsonify({"error": f"Invalid metric. Options: {', '.join(valid)}"}), 400

    try:
        value = float(value)
    except (TypeError, ValueError):
        return jsonify({"error": "Value must be a number"}), 400

    if value <= 0:
        return jsonify({"error": "Value must be positive"}), 400

    set_target(metric, value)
    return jsonify({"status": "ok", "targets": get_targets()})


# --- Startup ---

if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()
    print(f"Health Logger Web UI: http://localhost:5001")
    app.run(debug=True, port=5001)
