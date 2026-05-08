"""Stress-domain signal derivation.

Phase 3 step 5. Mirrors the Phase 2 ``domains.running.signals`` module
and the sibling ``domains.sleep.signals``: a single pure function that
builds the ``stress_signals`` dict ``classify_stress_state`` +
``evaluate_stress_policy`` consume from existing snapshot inputs.

Keeping derivation here — not in ``snapshot.py`` — preserves the
boundary that ``core/state/snapshot.py`` is a thin assembler that
dispatches to per-domain logic, rather than holding domain-specific
aggregation rules of its own.

Inputs come from the snapshot bundle:

  - ``stress_today``: today's ``accepted_stress_state_daily`` row, or
    ``None`` if no row.
  - ``stress_history``: trailing rows from
    ``accepted_stress_state_daily`` excluding today, oldest-to-newest.

Output is the dict shape ``classify_stress_state`` +
``evaluate_stress_policy`` already accept. Absent inputs become
``None`` entries; the classifier + policy translate those into
``unknown`` bands, uncertainty tokens, and no-op rules.
"""

from __future__ import annotations

from typing import Any, Optional


def derive_stress_signals(
    *,
    stress_today: Optional[dict[str, Any]],
    stress_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a ``stress_signals`` dict for stress classify + policy.

    Keys emitted:

      - ``garmin_all_day_stress`` / ``manual_stress_score`` /
        ``body_battery_end_of_day`` — direct reads off today's
        accepted-stress row.
      - ``body_battery_prev_day`` — body-battery end-of-day for
        yesterday, derived from the most-recent history row. None when
        no prior row exists.
      - ``stress_history_garmin_last_7`` — trailing 7 days of
        ``garmin_all_day_stress`` including today, most-recent last.
        Consumed by R-sustained-very-high-stress to count consecutive
        run length ending today.
    """

    garmin_all_day_stress = _pick(stress_today, "garmin_all_day_stress")
    manual_stress_score = _pick(stress_today, "manual_stress_score")
    body_battery_today = _pick(stress_today, "body_battery_end_of_day")

    body_battery_prev_day = _prev_body_battery(stress_history)
    history_garmin_last_7 = _trailing_garmin_history(
        stress_today=stress_today,
        stress_history=stress_history,
        window=7,
    )

    return {
        "garmin_all_day_stress": garmin_all_day_stress,
        "manual_stress_score": manual_stress_score,
        "body_battery_end_of_day": body_battery_today,
        "body_battery_prev_day": body_battery_prev_day,
        "stress_history_garmin_last_7": history_garmin_last_7,
    }


def _pick(row: Optional[dict[str, Any]], key: str) -> Optional[Any]:
    if row is None:
        return None
    return row.get(key)


def _prev_body_battery(
    stress_history: list[dict[str, Any]],
) -> Optional[int]:
    """Return yesterday's ``body_battery_end_of_day`` from history.

    History rows are oldest-to-newest per build_snapshot, so the last
    entry is the most-recent prior date. Returns None when history is
    empty or the most-recent entry has no body_battery value.
    """

    if not stress_history:
        return None
    last = stress_history[-1]
    value = last.get("body_battery_end_of_day")
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _trailing_garmin_history(
    *,
    stress_today: Optional[dict[str, Any]],
    stress_history: list[dict[str, Any]],
    window: int,
) -> list[Optional[int]]:
    """Return trailing ``window`` days of garmin_all_day_stress, most-recent last.

    Entries lacking the field are emitted as ``None`` to preserve the
    date-aligned layout R-sustained expects. When fewer than ``window``
    days are available, the result is shorter — R-sustained interprets
    the length as the actual window observed.
    """

    series: list[Optional[int]] = []
    for row in stress_history[-(window - 1):] if window > 1 else []:
        value = row.get("garmin_all_day_stress")
        series.append(int(value) if value is not None else None)
    if stress_today is not None:
        value = stress_today.get("garmin_all_day_stress")
        series.append(int(value) if value is not None else None)
    return series
