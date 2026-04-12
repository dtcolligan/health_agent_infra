from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "date",
    "calories_kcal",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "meal_count",
    "food_log_completeness",
    "top_meals_summary",
}


@dataclass(frozen=True)
class ParsedExport:
    account_id: str
    rows_by_date: dict[str, dict]


def parse_daily_nutrition_export(receipt_path: Path, *, account_id: str) -> ParsedExport:
    frame = pd.read_csv(receipt_path)
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")
    rows_by_date: dict[str, dict] = {}
    for record in frame.to_dict(orient="records"):
        date = str(record["date"])
        rows_by_date[date] = {
            "date": date,
            "calories_kcal": float(record["calories_kcal"]),
            "protein_g": float(record["protein_g"]),
            "carbs_g": float(record["carbs_g"]),
            "fat_g": float(record["fat_g"]),
            "fiber_g": float(record["fiber_g"]),
            "meal_count": int(record["meal_count"]),
            "food_log_completeness": str(record["food_log_completeness"]),
            "top_meals_summary": str(record["top_meals_summary"]),
        }
    return ParsedExport(account_id=account_id, rows_by_date=rows_by_date)
