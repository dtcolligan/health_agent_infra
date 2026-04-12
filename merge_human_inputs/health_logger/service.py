"""
service.py — Transport-agnostic business logic for the health logger.

Every function returns plain data (dicts/strings). The web layer calls these
and decides how to render the response (JSON, HTML, etc.).
"""

import json
import re
from datetime import datetime, timedelta

from .config import get_user_date
from .parser import parse_health_message
from .db import (save_message, update_message_json, save_entries,
                 get_daily_summary, get_subjective_entries, get_exercise_entries,
                 get_meal_items, get_recent_dates, delete_last_entry,
                 get_targets, set_target, get_logging_streak, get_weekly_summary)
from .formatter import (format_confirmation, format_summary, format_history,
                        format_today_items, format_target_progress,
                        format_weekly_digest)

# Valid target metrics and their display names
VALID_TARGETS = {
    "calories": "Calories (kcal)",
    "protein": "Protein (g)",
    "carbs": "Carbs (g)",
    "fat": "Fat (g)",
}


def get_help_text() -> str:
    """Return the help/welcome text."""
    return (
        "Hey! I'm your health logger. Just send me a message describing "
        "what you ate, any exercise you did, and how you're feeling.\n\n"
        "Example: \"Had porridge for breakfast, sandwich for lunch, "
        "pasta for dinner. Did a 30 min run. Energy was good.\"\n\n"
        "Tips:\n"
        "- Start a message with \"yesterday:\" to log for yesterday\n"
        "- Messages between midnight and 4 AM auto-log to yesterday"
    )


def get_summary() -> str:
    """Return today's summary text."""
    date_for = get_user_date()
    summary = get_daily_summary(date_for)
    exercises = get_exercise_entries(date_for)
    subjective = get_subjective_entries(date_for)
    targets = get_targets()
    streak = get_logging_streak(date_for)

    text = format_summary(summary, exercises, subjective, date_for)

    if targets and summary:
        text += "\n\n" + format_target_progress(summary, targets)

    if streak > 1:
        text += f"\n\n{streak}-day streak!"

    return text


def get_today_items() -> str:
    """Return itemised breakdown of today's log."""
    date_for = get_user_date()
    meals = get_meal_items(date_for)
    exercises = get_exercise_entries(date_for)
    subjective = get_subjective_entries(date_for)
    return format_today_items(meals, exercises, subjective, date_for)


def get_target_text(args: list[str] | None = None) -> str:
    """View or set targets. Returns response text.

    Args:
        args: None or [] to view, ["metric", "value"] to set.
    """
    args = args or []

    if not args:
        targets = get_targets()
        if not targets:
            return (
                "No targets set yet.\n\n"
                "Set one with: /target protein 120\n"
                "Options: " + ", ".join(VALID_TARGETS.keys())
            )
        lines = ["Your daily targets:", ""]
        for metric, value in targets.items():
            display = VALID_TARGETS.get(metric, metric.capitalize())
            lines.append(f"  {display}: {value:.0f}")
        return "\n".join(lines)

    if len(args) < 2:
        return (
            "Usage: /target <metric> <value>\n"
            "Example: /target protein 120\n"
            "Options: " + ", ".join(VALID_TARGETS.keys())
        )

    metric = args[0].lower()
    if metric not in VALID_TARGETS:
        return (
            f"Unknown target \"{metric}\". Options: "
            + ", ".join(VALID_TARGETS.keys())
        )

    try:
        value = float(args[1])
    except ValueError:
        return f"\"{args[1]}\" isn't a number."

    if value <= 0:
        return "Target must be a positive number."

    set_target(metric, value)
    display = VALID_TARGETS[metric]
    return f"Target set: {display} = {value:.0f}/day"


def undo_last_entry() -> str:
    """Delete the most recent logged entry. Returns response text."""
    date_for = get_user_date()
    deleted = delete_last_entry(date_for)
    if deleted:
        summary = get_daily_summary(date_for)
        exercises = get_exercise_entries(date_for)
        subjective = get_subjective_entries(date_for)
        day_text = format_summary(summary, exercises, subjective, date_for)
        preview = deleted[:60] + ("..." if len(deleted) > 60 else "")
        return (
            f"Deleted last entry (\"{preview}\")\n\n"
            f"Updated totals:\n{day_text}"
        )
    return "Nothing to undo — no entries logged today."


def get_history_text() -> str:
    """Return recent days overview."""
    dates = get_recent_dates(limit=7)
    if not dates:
        return "No logged days yet."
    return format_history(dates)


def get_week_text() -> str:
    """Return 7-day digest with averages."""
    date_for = get_user_date()
    week = get_weekly_summary(date_for)
    if week is None:
        return "No data in the last 7 days yet."
    targets = get_targets()
    streak = get_logging_streak(date_for)
    return format_weekly_digest(week, targets, streak)


def _extract_date_override(text: str) -> tuple[str, str]:
    """Check if the message starts with a date override like 'yesterday:'.

    Returns (date_for, cleaned_text).
    """
    lower = text.lower().strip()

    if re.match(r"^yesterday\s*[:\-]\s*", lower):
        cleaned = re.sub(r"^yesterday\s*[:\-]\s*", "", text, flags=re.IGNORECASE).strip()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return yesterday, cleaned

    return get_user_date(), text


def log_message(user_text: str) -> str:
    """Parse and log a health message. Returns response text.

    This is the main entry point — takes raw user text,
    parses it via Claude, saves to DB, returns formatted response.
    """
    date_for, cleaned_text = _extract_date_override(user_text)

    # 1. Save raw message (audit trail)
    msg_id = save_message(
        raw_text=user_text,
        date_for=date_for,
    )

    # 2. Parse via Claude
    result = parse_health_message(cleaned_text, date_for)

    # Store the raw Claude response for debugging
    raw_json = result.get("raw_response", json.dumps(result))
    update_message_json(msg_id, raw_json)

    # 3. Handle result type
    if result["type"] == "clarification":
        return f"Quick question: {result['question']}"

    if result["type"] == "error":
        return (
            f"Sorry, I had trouble parsing that. Could you rephrase?\n\n"
            f"({result['message'][:100]})"
        )

    # 4. Check if Claude found anything to log
    data = result["data"]
    has_content = (data.get("meals") or data.get("exercises")
                   or data.get("subjective"))

    if not has_content:
        return (
            "I didn't spot any food, exercise, or wellness info in that message. "
            "Just send me what you ate, any exercise, or how you're feeling!"
        )

    # 5. Save structured data to SQLite
    save_entries(msg_id, data, date_for)

    # 6. Build response
    summary = get_daily_summary(date_for)
    exercises = get_exercise_entries(date_for)
    subjective = get_subjective_entries(date_for)
    targets = get_targets()

    confirmation = format_confirmation(data, date_for)
    day_summary = format_summary(summary, exercises, subjective, date_for)
    response_text = f"{confirmation}\n\n---\n{day_summary}"

    if targets and summary:
        response_text += "\n\n" + format_target_progress(summary, targets)

    return response_text
