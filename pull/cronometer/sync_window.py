from __future__ import annotations

from datetime import date, timedelta


def planned_dates(available_dates: list[str], *, last_successful_day: str | None) -> list[str]:
    days = sorted(available_dates)
    if not last_successful_day:
        return days
    overlap_start = (date.fromisoformat(last_successful_day) - timedelta(days=2)).isoformat()
    return [day for day in days if day >= overlap_start]
