"""running_activity projector + read helpers.

Per-session structural data sourced from intervals.icu's /activities
endpoint. Unlike ``accepted_running_state_daily``, which is a daily
rollup, each row here is one session — PK on the intervals.icu activity
id so re-pulls upsert cleanly.

Responsibilities:
  - ``project_activity`` — UPSERT a single ``IntervalsIcuActivity.as_dict()``
    payload into ``running_activity``. List fields are serialised to JSON
    text for SQLite storage and rehydrated by the reads.
  - ``read_activities_for_date`` + ``read_activities_range`` — typed reads
    the snapshot layer uses to attach per-session data to the running
    block.
  - ``aggregate_activities_to_daily_rollup`` — the bridge the ``hai clean``
    flow uses so ``accepted_running_state_daily`` (which the Phase 1
    classifier already reads) stops carrying nulls for distance +
    intensity minutes on days when activities exist.

Activities are upstream-owned (no manual override surface), so there's
no ``derived_from`` dimension negotiation like stress/recovery — the
upstream id IS the provenance.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from typing import Any, Iterable, Optional


_INSERT_COLUMNS = (
    "activity_id",
    "user_id",
    "as_of_date",
    "start_date_utc",
    "start_date_local",
    "source",
    "external_id",
    "activity_type",
    "name",
    "distance_m",
    "moving_time_s",
    "elapsed_time_s",
    "average_hr",
    "max_hr",
    "athlete_max_hr",
    "hr_zone_times_s_json",
    "hr_zones_bpm_json",
    "interval_summary_json",
    "trimp",
    "icu_training_load",
    "hr_load",
    "hr_load_type",
    "warmup_time_s",
    "cooldown_time_s",
    "lap_count",
    "average_speed_mps",
    "max_speed_mps",
    "pace_s_per_m",
    "average_cadence_spm",
    "average_stride_m",
    "calories",
    "total_elevation_gain_m",
    "total_elevation_loss_m",
    "feel",
    "icu_rpe",
    "session_rpe",
    "device_name",
    "raw_json",
    "ingest_actor",
    "ingested_at",
)


class ActivityProjectorInputError(ValueError):
    """Raised when an activity payload is missing keys the projector
    requires via direct dict access. v0.1.10 W-D introduced typed
    validation so the failure surface is explicit rather than a bare
    ``KeyError`` that bubbles up as a generic transaction rollback.
    """


_ACTIVITY_REQUIRED_KEYS = ("activity_id", "user_id", "as_of_date", "raw_json")


def _validate_activity_payload(activity: dict) -> None:
    """v0.1.10 W-D: enforce the implicit projector contract explicitly.

    The ``project_activity`` body uses direct subscript on
    ``activity_id``, ``user_id``, and ``raw_json`` — anything missing
    raises ``KeyError`` which the cmd_clean handler wraps in a generic
    "rolled back: 'user_id'" warning. That message hides the contract
    from users; this validator raises a typed error with the full
    missing-key set up front.
    """

    if not isinstance(activity, dict):
        raise ActivityProjectorInputError(
            f"activity must be a dict, got {type(activity).__name__}"
        )
    missing = [k for k in _ACTIVITY_REQUIRED_KEYS if k not in activity]
    if missing:
        raise ActivityProjectorInputError(
            f"activity missing required keys: {missing}. "
            f"Required: {list(_ACTIVITY_REQUIRED_KEYS)}"
        )


def project_activity(
    conn: sqlite3.Connection,
    *,
    activity: dict,
    ingest_actor: str = "intervals_icu_adapter",
    commit_after: bool = True,
) -> bool:
    """UPSERT one intervals.icu activity into ``running_activity``.

    ``activity`` is an ``IntervalsIcuActivity.as_dict()`` payload — the
    same shape the adapter emits and the JSONL log stores. List fields
    (``hr_zone_times_s``, ``hr_zones_bpm``, ``interval_summary``) are
    serialised to JSON text for SQLite storage; reads rehydrate them.

    Returns ``True`` on insert, ``False`` on replace.

    Raises ``ActivityProjectorInputError`` if the payload is missing
    a key the projector requires via direct dict access. v0.1.10 W-D
    introduced this validation surface so contract violations are
    explicit rather than presenting as generic ``KeyError`` rollbacks.
    """

    _validate_activity_payload(activity)

    now_iso = _now_iso()
    activity_id = activity["activity_id"]

    existing = conn.execute(
        "SELECT 1 FROM running_activity WHERE activity_id = ?",
        (activity_id,),
    ).fetchone()
    is_insert = existing is None

    values = (
        activity_id,
        activity["user_id"],
        activity["as_of_date"],
        activity.get("start_date_utc"),
        activity.get("start_date_local"),
        activity.get("source"),
        activity.get("external_id"),
        activity.get("activity_type"),
        activity.get("name"),
        activity.get("distance_m"),
        activity.get("moving_time_s"),
        activity.get("elapsed_time_s"),
        activity.get("average_hr"),
        activity.get("max_hr"),
        activity.get("athlete_max_hr"),
        _list_to_json(activity.get("hr_zone_times_s")),
        _list_to_json(activity.get("hr_zones_bpm")),
        _list_to_json(activity.get("interval_summary")),
        activity.get("trimp"),
        activity.get("icu_training_load"),
        activity.get("hr_load"),
        activity.get("hr_load_type"),
        activity.get("warmup_time_s"),
        activity.get("cooldown_time_s"),
        activity.get("lap_count"),
        activity.get("average_speed_mps"),
        activity.get("max_speed_mps"),
        activity.get("pace_s_per_m"),
        activity.get("average_cadence_spm"),
        activity.get("average_stride_m"),
        activity.get("calories"),
        activity.get("total_elevation_gain_m"),
        activity.get("total_elevation_loss_m"),
        activity.get("feel"),
        activity.get("icu_rpe"),
        activity.get("session_rpe"),
        activity.get("device_name"),
        activity["raw_json"],
        ingest_actor,
        now_iso,
    )

    placeholders = ", ".join("?" * len(_INSERT_COLUMNS))
    columns = ", ".join(_INSERT_COLUMNS)

    if is_insert:
        conn.execute(
            f"INSERT INTO running_activity ({columns}) VALUES ({placeholders})",  # nosec B608 - columns from _INSERT_COLUMNS constant; placeholders are literal "?" tokens.
            values,
        )
    else:
        # Full replace: intervals.icu can update a sync'd activity (rare
        # but happens — user edits RPE, adds feel, re-maps zones). The
        # upstream row is authoritative; we carry the new ``raw_json``.
        set_clause = ", ".join(
            f"{col} = ?" for col in _INSERT_COLUMNS if col != "activity_id"
        )
        conn.execute(
            f"UPDATE running_activity SET {set_clause} WHERE activity_id = ?",  # nosec B608 - set_clause built from _INSERT_COLUMNS constant; user values bind via params.
            (*values[1:], activity_id),
        )
    if commit_after:
        conn.commit()
    return is_insert


def read_activities_for_date(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    as_of_date: date,
    activity_type: Optional[str] = None,
) -> list[dict]:
    """Return activities for a single civil day, newest-first by start time.

    Pass ``activity_type="Run"`` to filter to running sessions only. List
    fields are rehydrated from their JSON text storage.
    """

    params: list[Any] = [user_id, as_of_date.isoformat()]
    sql = (
        "SELECT * FROM running_activity "
        "WHERE user_id = ? AND as_of_date = ?"
    )
    if activity_type is not None:
        sql += " AND activity_type = ?"
        params.append(activity_type)
    sql += " ORDER BY start_date_utc DESC, activity_id DESC"

    rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def read_activities_range(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    since: date,
    until: date,
    activity_type: Optional[str] = None,
) -> list[dict]:
    """Return activities in [since, until] inclusive, newest-first.

    Used by the snapshot layer to assemble ``running.activities_history``.
    """

    params: list[Any] = [user_id, since.isoformat(), until.isoformat()]
    sql = (
        "SELECT * FROM running_activity "
        "WHERE user_id = ? AND as_of_date BETWEEN ? AND ?"
    )
    if activity_type is not None:
        sql += " AND activity_type = ?"
        params.append(activity_type)
    sql += " ORDER BY as_of_date DESC, start_date_utc DESC, activity_id DESC"

    rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def aggregate_activities_to_daily_rollup(
    activities: Iterable[dict],
) -> dict:
    """Aggregate activities for a single day into the rollup shape that
    ``accepted_running_state_daily`` expects.

    Backfills the historical nulls the Garmin CSV / intervals.icu wellness
    streams never populated:

      - ``total_distance_m``      — sum of ``distance_m`` across activities
      - ``total_duration_s``      — sum of ``moving_time_s``
      - ``moderate_intensity_min``— HR zones 2+3 (seconds) / 60
      - ``vigorous_intensity_min``— HR zones 4+5+6+7 (seconds) / 60
      - ``session_count``         — len(activities)

    Returns None for any field the input couldn't support (e.g. intensity
    minutes when no activity carried ``hr_zone_times_s``). Caller merges
    these into the raw_daily_row before projecting.

    Convention: intervals.icu ``icu_hr_zone_times`` is 7 entries
    (Z1..Z7). Moderate = Z2+Z3. Vigorous = Z4+Z5+Z6+Z7. This matches
    Garmin's moderate/vigorous classification.
    """

    activities_list = list(activities)
    if not activities_list:
        return {
            "total_distance_m": None,
            "total_duration_s": None,
            "moderate_intensity_min": None,
            "vigorous_intensity_min": None,
            "session_count": None,
        }

    distance = _sum_or_none(a.get("distance_m") for a in activities_list)
    duration = _sum_or_none(a.get("moving_time_s") for a in activities_list)

    moderate_s: float = 0.0
    vigorous_s: float = 0.0
    any_zone_times = False
    for a in activities_list:
        zt = a.get("hr_zone_times_s")
        if not zt:
            continue
        any_zone_times = True
        # Safe indexing; zones shorter than 7 still count what's present.
        if len(zt) > 1:
            moderate_s += float(zt[1])
        if len(zt) > 2:
            moderate_s += float(zt[2])
        if len(zt) > 3:
            vigorous_s += sum(float(x) for x in zt[3:])

    return {
        "total_distance_m": distance,
        "total_duration_s": duration,
        "moderate_intensity_min": (moderate_s / 60.0) if any_zone_times else None,
        "vigorous_intensity_min": (vigorous_s / 60.0) if any_zone_times else None,
        "session_count": len(activities_list),
    }


# --------------------------------------------------------------------------- helpers


def _list_to_json(v: Any) -> Optional[str]:
    if v is None:
        return None
    return json.dumps(list(v), sort_keys=False)


def _json_to_list(v: Any) -> Optional[list]:
    if v is None:
        return None
    try:
        return json.loads(v)
    except (json.JSONDecodeError, TypeError):
        return None


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["hr_zone_times_s"] = _json_to_list(d.pop("hr_zone_times_s_json", None))
    d["hr_zones_bpm"] = _json_to_list(d.pop("hr_zones_bpm_json", None))
    d["interval_summary"] = _json_to_list(d.pop("interval_summary_json", None))
    return d


def _sum_or_none(values: Iterable[Any]) -> Optional[float]:
    s = 0.0
    saw_any = False
    for v in values:
        if v is None:
            continue
        if isinstance(v, bool):
            continue
        if not isinstance(v, (int, float)):
            continue
        s += float(v)
        saw_any = True
    return s if saw_any else None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
