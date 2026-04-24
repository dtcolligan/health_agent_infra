"""Running-domain signal derivation.

Phase 2 step 3. The running classifier in ``classify.py`` accepts a
pre-built ``running_signals`` dict; this module is the single place that
builds it from existing snapshot inputs (``raw_summary``, the running
history rows, and the recovery domain's ``classified_state``).

Keeping the derivation here — not in ``snapshot.py`` — preserves the
boundary that ``core/state/snapshot.py`` is a thin assembler that
*dispatches* to per-domain logic, rather than holding domain-specific
aggregation rules of its own.

Inputs come from the snapshot bundle:

  - ``raw_summary``: the ``hai clean`` deltas/ratios envelope. Carries
    the day's ACWR (``garmin_acwr_ratio``) and the locally-computed mean
    of Garmin's training readiness components
    (``training_readiness_component_mean_pct``).
  - ``running_today``: today's ``accepted_running_state_daily`` row, or
    ``None`` if no row.
  - ``running_history``: trailing rows from ``accepted_running_state_daily``
    excluding today, ordered by ``as_of_date``.
  - ``recovery_classified``: optional dict form of the recovery domain's
    classified state, used for ``sleep_debt_band`` / ``resting_hr_band``
    cross-domain peeks. ``None`` means recovery's bundle wasn't expanded;
    the running signals will mark those bands as missing.

Output is the dict shape ``classify_running_state`` already accepts; no
new keys, so step 2's tests stay valid.
"""

from __future__ import annotations

from typing import Any, Optional


# A "hard session" in v1 is a day with at least this many vigorous-intensity
# minutes. Aligned with WHO's vigorous-activity threshold and Garmin's own
# vigorous-zone definition; deliberately conservative so a single tempo
# block counts but a long easy effort with one fast strider does not.
_HARD_SESSION_VIGOROUS_MIN_THRESHOLD = 30


def derive_running_signals(
    raw_summary: dict[str, Any],
    *,
    running_today: Optional[dict[str, Any]],
    running_history: list[dict[str, Any]],
    recovery_classified: Optional[dict[str, Any]] = None,
    activities_today: Optional[list[dict[str, Any]]] = None,
    activities_history: Optional[list[dict[str, Any]]] = None,
    as_of_date: Optional[str] = None,
) -> dict[str, Any]:
    """Build a ``running_signals`` dict for ``classify_running_state``.

    Aggregations:

      - ``weekly_mileage_m``: sum of ``total_distance_m`` over today + the
        6 most recent history days. ``None`` when no day in that window
        has distance data.
      - ``weekly_mileage_baseline_m``: trailing-week mean over the most
        recent 28 days of running data, scaled to a single week. When
        fewer than 28 days are available, falls back to a scaled average
        over what's present (``mean_per_day * 7``); when fewer than 7 days
        are available, returns ``None`` so the classifier marks coverage
        as insufficient.
      - ``recent_hard_session_count_7d``: count of days in the last 7
        whose ``vigorous_intensity_min`` clears the hard-session
        threshold. ``None`` when no day in the window has that field
        populated (so the classifier can mark ``hard_session_history_unavailable``
        rather than confuse "0 hard sessions" with "no data").
      - ``acwr_ratio`` / ``training_readiness_pct``: pulled directly off
        ``raw_summary``.
      - ``sleep_debt_band`` / ``resting_hr_band``: pulled off
        ``recovery_classified`` when present.

    V0.1.4 adds structural per-session signals from the intervals.icu
    ``/activities`` stream (``activities_today``, ``activities_history``).
    These are carried through alongside the rollup-based aggregations so
    policy or skill code can reason about session structure without
    re-reading the DB:

      - ``z4_plus_seconds_today`` / ``z4_plus_seconds_7d``: seconds spent
        in HR zones ≥4 today and across the trailing 7 days. More precise
        than ``vigorous_intensity_min`` (minute-bucketed) when present.
      - ``last_hard_session_days_ago``: days since the most recent
        session whose zone-4+ time cleared the hard threshold. ``None``
        when no hard session in the visible window.
      - ``today_interval_summary``: today's ``interval_summary`` list
        verbatim (e.g. ``['4x 9m29s 156bpm']``) — skills use this for
        planned-vs-actual match reasoning.
    """

    # Gather distances in ascending recency order: history (oldest→newest)
    # then today, then reverse for "newest first" iteration.
    distance_series_newest_first: list[Optional[float]] = []
    if running_today is not None:
        distance_series_newest_first.append(running_today.get("total_distance_m"))
    for row in reversed(running_history):
        distance_series_newest_first.append(row.get("total_distance_m"))

    # Same for vigorous-intensity minutes (used for hard-session counting).
    vigorous_series_newest_first: list[Optional[int]] = []
    if running_today is not None:
        vigorous_series_newest_first.append(running_today.get("vigorous_intensity_min"))
    for row in reversed(running_history):
        vigorous_series_newest_first.append(row.get("vigorous_intensity_min"))

    weekly_mileage_m = _sum_window(distance_series_newest_first, window=7)
    weekly_mileage_baseline_m = _baseline_weekly_mileage(distance_series_newest_first)
    recent_hard_count = _count_hard_sessions(vigorous_series_newest_first, window=7)

    sleep_debt_band: Optional[str] = None
    resting_hr_band: Optional[str] = None
    if recovery_classified is not None:
        sleep_debt_band = recovery_classified.get("sleep_debt_band")
        resting_hr_band = recovery_classified.get("resting_hr_band")

    activities_today = activities_today or []
    activities_history = activities_history or []

    z4_plus_today = _sum_z4_plus_seconds(activities_today)
    z4_plus_7d = _sum_z4_plus_seconds_window(
        activities_today, activities_history, window_days=7,
    )
    last_hard_days_ago = _last_hard_session_days_ago(
        activities_today, activities_history, as_of_date=as_of_date,
    )
    today_interval_summary = _first_non_empty_interval_summary(activities_today)

    return {
        "weekly_mileage_m": weekly_mileage_m,
        "weekly_mileage_baseline_m": weekly_mileage_baseline_m,
        "recent_hard_session_count_7d": recent_hard_count,
        "acwr_ratio": raw_summary.get("garmin_acwr_ratio"),
        "training_readiness_pct": raw_summary.get(
            "training_readiness_component_mean_pct"
        ),
        "sleep_debt_band": sleep_debt_band,
        "resting_hr_band": resting_hr_band,
        "z4_plus_seconds_today": z4_plus_today,
        "z4_plus_seconds_7d": z4_plus_7d,
        "last_hard_session_days_ago": last_hard_days_ago,
        "today_interval_summary": today_interval_summary,
        "activity_count_14d": len(activities_today) + len(activities_history),
    }


def _sum_window(
    series_newest_first: list[Optional[float]],
    *,
    window: int,
) -> Optional[float]:
    """Sum the first ``window`` non-None entries; None if the window is empty."""

    values = [v for v in series_newest_first[:window] if v is not None]
    if not values:
        return None
    return float(sum(values))


def _baseline_weekly_mileage(
    distance_series_newest_first: list[Optional[float]],
) -> Optional[float]:
    """Return a per-week baseline mileage scaled from trailing data.

    Prefers a trailing-28d sample (4 full weeks) when available; falls
    back to scaling whatever ≥7 days are present. Returns None when fewer
    than 7 days of distance data exist.
    """

    full_window = [v for v in distance_series_newest_first[:28] if v is not None]
    if len(full_window) >= 28:
        return sum(full_window) / 4.0  # 28 days → 4 weeks
    if len(full_window) >= 7:
        return (sum(full_window) / len(full_window)) * 7.0
    return None


def _count_hard_sessions(
    vigorous_series_newest_first: list[Optional[int]],
    *,
    window: int,
) -> Optional[int]:
    """Count days with ``vigorous_intensity_min`` >= threshold over the window.

    Returns None when no day in the window has the field populated — the
    classifier maps that to ``hard_session_history_unavailable`` so a
    "we don't know" outcome is not silently coerced to "0 sessions."
    """

    window_slice = vigorous_series_newest_first[:window]
    populated = [v for v in window_slice if v is not None]
    if not populated:
        return None
    return sum(1 for v in populated if v >= _HARD_SESSION_VIGOROUS_MIN_THRESHOLD)


# --------------------------------------------------------------------------- activity-level helpers


# A session is "hard" in the structural sense when zone-4+ time clears
# this threshold. 10 minutes is conservative — catches a 4×4 threshold
# block, but a single Z4 strider (~1 min) stays out.
_HARD_SESSION_Z4_PLUS_SECONDS = 600


def _sum_z4_plus_seconds(activities: list[dict]) -> Optional[int]:
    """Sum hr_zone_times_s[3:] across activities. None if no zone data."""

    total = 0
    saw_any = False
    for a in activities:
        zt = a.get("hr_zone_times_s")
        if not zt:
            continue
        saw_any = True
        if len(zt) > 3:
            for v in zt[3:]:
                if isinstance(v, (int, float)):
                    total += int(v)
    return total if saw_any else None


def _sum_z4_plus_seconds_window(
    activities_today: list[dict],
    activities_history: list[dict],
    *,
    window_days: int,
) -> Optional[int]:
    """Sum zone-4+ seconds across today + ``window_days-1`` history days.

    History is assumed newest-first (the snapshot layer orders it that
    way). When no activities in the window carry zone data, returns
    None rather than 0 so skills can distinguish "light week" from
    "we don't know."
    """

    in_window = list(activities_today)
    # Cap the history to reasonable window size (by activity count, not
    # civil-day filtering — the window_days semantics here is a soft
    # guard; the snapshot already bounded the lookback).
    in_window.extend(activities_history[: window_days * 3])
    return _sum_z4_plus_seconds(in_window)


def _last_hard_session_days_ago(
    activities_today: list[dict],
    activities_history: list[dict],
    *,
    as_of_date: Optional[str] = None,
) -> Optional[int]:
    """Return days-ago of the most recent hard session, or None.

    "Hard" means zone-4+ seconds >= _HARD_SESSION_Z4_PLUS_SECONDS for a
    single session. Walks today → history in recency order and returns
    the first match's civil-day distance from the plan date.

    **Codex r2 fix** — previously the function anchored the gap to the
    first historical activity's date when no activity today existed.
    That caused "yesterday's hard session" to report as
    ``last_hard_session_days_ago = 0`` instead of 1 on days the user
    didn't train. The anchor is now ``as_of_date`` (the snapshot's
    plan date) whenever the caller provides it; the fallback to the
    first activity's date is kept only for call sites that don't (yet)
    pass it.
    """

    from datetime import date as date_cls

    def _hard(a: dict) -> bool:
        zt = a.get("hr_zone_times_s")
        if not zt or len(zt) <= 3:
            return False
        z4_plus = sum(int(v) for v in zt[3:] if isinstance(v, (int, float)))
        return z4_plus >= _HARD_SESSION_Z4_PLUS_SECONDS

    # Anchor the gap to the plan date when provided. Falls back to the
    # first-seen activity's as_of_date only when as_of_date is absent,
    # which is the legacy behaviour.
    today_iso: Optional[str] = as_of_date
    if today_iso is None:
        if activities_today:
            today_iso = activities_today[0].get("as_of_date")
        elif activities_history:
            today_iso = activities_history[0].get("as_of_date")
    if today_iso is None:
        return None
    try:
        today_date = date_cls.fromisoformat(today_iso)
    except ValueError:
        return None

    # Today's activities count as days_ago=0 iff they land on today_date.
    for a in activities_today:
        if not _hard(a):
            continue
        try:
            a_date = date_cls.fromisoformat(a.get("as_of_date", ""))
        except ValueError:
            continue
        if a_date == today_date:
            return 0

    for a in activities_history:
        if not _hard(a):
            continue
        try:
            a_date = date_cls.fromisoformat(a.get("as_of_date", ""))
        except ValueError:
            continue
        gap = (today_date - a_date).days
        if gap >= 0:
            return gap
    return None


def _first_non_empty_interval_summary(
    activities: list[dict],
) -> Optional[list[str]]:
    """Return the first non-empty interval_summary list, or None."""

    for a in activities:
        summary = a.get("interval_summary")
        if summary:
            return list(summary)
    return None
