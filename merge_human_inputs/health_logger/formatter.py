"""
formatter.py — Format parsed health data into human-readable text.
"""

from datetime import date, datetime


def _friendly_date(date_for: str) -> str:
    """'2026-03-02' -> '2 March'"""
    try:
        d = datetime.strptime(date_for, "%Y-%m-%d")
        return d.strftime("%-d %B")
    except ValueError:
        return date_for


def _round_cal(cal: int | float | None) -> str:
    """Round calories to nearest 5 for readability."""
    if cal is None:
        return "?"
    return str(round(cal / 5) * 5)


def _protein_str(protein_g: float | None) -> str | None:
    """Format protein, returning None if negligible (rounds to 0)."""
    if protein_g is None or protein_g <= 0:
        return None
    rounded = round(protein_g)
    if rounded == 0:
        return None
    return f"{rounded}g P"


def format_confirmation(parsed_data: dict, date_for: str) -> str:
    """Format a confirmation message showing what was just logged."""
    lines = [f"Logged for {_friendly_date(date_for)}:"]

    # Meals — one line per meal type, items joined with " + "
    meals = parsed_data.get("meals", [])
    if meals:
        lines.append("")
    for meal in meals:
        meal_type = meal["meal_type"].capitalize()
        item_parts = []
        for item in meal.get("items", []):
            cal = _round_cal(item.get("calories"))
            prot = _protein_str(item.get("protein_g"))
            name = item["item_name"]
            if prot:
                item_parts.append(f"{name} (~{cal} kcal, {prot})")
            else:
                item_parts.append(f"{name} (~{cal} kcal)")
        lines.append(f"{meal_type}: {' + '.join(item_parts)}")

    # Exercises
    if parsed_data.get("exercises"):
        lines.append("")
        for ex in parsed_data["exercises"]:
            parts = []
            if ex.get("subtype"):
                parts.append(ex["subtype"].capitalize())
            dur = ex.get("duration_min")
            if dur:
                parts.append(f"{dur} min")
            if ex.get("intensity"):
                parts.append(ex["intensity"])
            detail = ", ".join(parts)
            lines.append(f"{ex['exercise_type'].capitalize()}: {detail}")

    # Subjective
    if parsed_data.get("subjective"):
        lines.append("")
        sub_parts = []
        for sub in parsed_data["subjective"]:
            metric = sub["metric"].replace("_", " ").capitalize()
            val = sub.get("value")
            label = sub.get("label", "")
            if val is not None:
                sub_parts.append(f"{metric}: {val:.0f}/10 ({label})")
            else:
                sub_parts.append(f"{metric}: {label}")
        lines.append(" | ".join(sub_parts))

    return "\n".join(lines)


def format_summary(summary: dict | None, exercises: list[dict],
                   subjective: list[dict], date_for: str) -> str:
    """Format a daily summary message."""
    if summary is None:
        return f"No entries logged yet for {_friendly_date(date_for)}."

    cal = round(summary.get("total_calories", 0))
    pro = round(summary.get("total_protein_g", 0))
    carb = round(summary.get("total_carbs_g", 0))
    fat = round(summary.get("total_fat_g", 0))

    lines = [f"Day total: ~{cal:,} kcal | {pro}g P | {carb}g C | {fat}g F"]

    # Exercise summary
    ex_min = summary.get("exercise_min", 0)
    ex_types = summary.get("exercise_types", "")
    if ex_min and ex_min > 0:
        lines.append(f"Exercise: {ex_min} min {ex_types or ''}")

    # Subjective summary
    if subjective:
        sub_parts = []
        for sub in subjective:
            metric = sub["metric"].replace("_", " ").capitalize()
            val = sub.get("value")
            if val is not None:
                sub_parts.append(f"{metric}: {val:.0f}/10")
        if sub_parts:
            lines.append(" | ".join(sub_parts))

    return "\n".join(lines)


def format_today_items(meals: list[dict], exercises: list[dict],
                       subjective: list[dict], date_for: str) -> str:
    """Format an itemised breakdown of everything logged for a date."""
    if not meals and not exercises and not subjective:
        return f"Nothing logged yet for {_friendly_date(date_for)}."

    lines = [f"Logged for {_friendly_date(date_for)}:"]

    # Group meals by meal_type
    if meals:
        from collections import defaultdict
        grouped = defaultdict(list)
        for item in meals:
            grouped[item["meal_type"]].append(item)

        lines.append("")
        for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
            items = grouped.get(meal_type, [])
            if not items:
                continue
            lines.append(f"{meal_type.capitalize()}:")
            for item in items:
                cal = _round_cal(item.get("calories"))
                prot = _protein_str(item.get("protein_g"))
                name = item["item_name"]
                qty = item.get("quantity_desc", "")
                entry = f"  {name}"
                if qty:
                    entry += f" ({qty})"
                entry += f" — ~{cal} kcal"
                if prot:
                    entry += f", {prot}"
                lines.append(entry)

    if exercises:
        lines.append("")
        lines.append("Exercise:")
        for ex in exercises:
            parts = [ex["exercise_type"].capitalize()]
            if ex.get("subtype"):
                parts.append(ex["subtype"])
            dur = ex.get("duration_min")
            if dur:
                parts.append(f"{dur} min")
            if ex.get("intensity"):
                parts.append(ex["intensity"])
            cal = ex.get("calories_est")
            detail = ", ".join(parts)
            if cal:
                detail += f" (~{cal} kcal)"
            lines.append(f"  {detail}")

    if subjective:
        lines.append("")
        lines.append("Wellness:")
        for sub in subjective:
            metric = sub["metric"].replace("_", " ").capitalize()
            val = sub.get("value")
            label = sub.get("label", "")
            if val is not None:
                lines.append(f"  {metric}: {val:.0f}/10 ({label})")
            else:
                lines.append(f"  {metric}: {label}")

    return "\n".join(lines)


def format_target_progress(summary: dict, targets: dict) -> str:
    """Format progress towards daily targets with visual bars.

    Args:
        summary: daily_summary row (total_calories, total_protein_g, etc.)
        targets: {metric: value} dict from the targets table
    """
    METRIC_TO_COLUMN = {
        "calories": "total_calories",
        "protein": "total_protein_g",
        "carbs": "total_carbs_g",
        "fat": "total_fat_g",
    }
    METRIC_UNITS = {
        "calories": "kcal",
        "protein": "g",
        "carbs": "g",
        "fat": "g",
    }

    lines = ["Targets:"]
    for metric, target_val in targets.items():
        col = METRIC_TO_COLUMN.get(metric)
        if col is None:
            continue
        actual = summary.get(col, 0) or 0
        unit = METRIC_UNITS.get(metric, "")
        pct = actual / target_val if target_val > 0 else 0

        # Visual bar: 10 chars wide
        filled = min(round(pct * 10), 10)
        bar = "█" * filled + "░" * (10 - filled)

        actual_str = f"{round(actual)}"
        target_str = f"{round(target_val)}"
        lines.append(f"  [{bar}] {actual_str}/{target_str}{unit} {metric}")

    if len(lines) == 1:
        return ""
    return "\n".join(lines)


def format_weekly_digest(week: dict, targets: dict, streak: int) -> str:
    """Format a 7-day weekly digest."""
    lines = [
        f"Weekly digest ({_friendly_date(week['start_date'])} – "
        f"{_friendly_date(week['end_date'])}):",
        f"Logged {week['days_logged']}/7 days",
        "",
        f"Avg daily: ~{round(week['avg_calories']):,} kcal | "
        f"{round(week['avg_protein'])}g P | "
        f"{round(week['avg_carbs'])}g C | "
        f"{round(week['avg_fat'])}g F",
    ]

    if week["total_exercise_min"] > 0:
        lines.append(
            f"Exercise: {week['total_exercise_min']} min across "
            f"{week['exercise_sessions']} session"
            f"{'s' if week['exercise_sessions'] != 1 else ''}"
        )

    # Target comparison (weekly avg vs daily targets)
    if targets:
        lines.append("")
        lines.append("Weekly avg vs targets:")
        metric_map = {
            "calories": ("avg_calories", "kcal"),
            "protein": ("avg_protein", "g"),
            "carbs": ("avg_carbs", "g"),
            "fat": ("avg_fat", "g"),
        }
        for metric, target_val in targets.items():
            key, unit = metric_map.get(metric, (None, ""))
            if key is None:
                continue
            avg = week.get(key, 0)
            diff = avg - target_val
            sign = "+" if diff > 0 else ""
            lines.append(
                f"  {metric.capitalize()}: ~{round(avg)}/{round(target_val)}{unit} "
                f"({sign}{round(diff)}{unit}/day)"
            )

    if streak > 1:
        lines.append(f"\n{streak}-day logging streak!")

    return "\n".join(lines)


def format_history(dates: list[str]) -> str:
    """Format a list of recent logged dates with their summaries."""
    from .db import get_daily_summary

    if not dates:
        return "No logged days yet."

    lines = ["Recent days:", ""]

    for d in dates:
        summary = get_daily_summary(d)
        if summary is None:
            continue
        cal = round(summary.get("total_calories", 0))
        pro = round(summary.get("total_protein_g", 0))
        ex_min = summary.get("exercise_min", 0)

        day_line = f"{_friendly_date(d)}: ~{cal:,} kcal, {pro}g P"
        if ex_min and ex_min > 0:
            ex_types = summary.get("exercise_types", "")
            day_line += f" | {ex_min} min {ex_types or 'exercise'}"
        lines.append(day_line)

    if len(lines) == 2:
        return "No logged days yet."

    return "\n".join(lines)
