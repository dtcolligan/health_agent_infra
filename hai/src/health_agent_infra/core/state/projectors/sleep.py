"""Accepted sleep state projector.

Maps the sleep-related columns of ``source_daily_garmin`` into the
dedicated ``accepted_sleep_state_daily`` table introduced by
migration 004. Prior to Phase 3 these fields lived on
``accepted_recovery_state_daily``; the split promotes sleep to a
first-class domain with its own accepted-state row.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from typing import Optional

from health_agent_infra.core.state.projectors._shared import (
    _is_intake_submission_id,
    _now_iso,
    _replace_dimension_in_derived_from,
)


def _sleep_hours_from_raw(raw_row: dict) -> Optional[float]:
    """Sum deep+light+rem sleep seconds, return hours. Falls back to
    sleep_total_sec when stage breakdown is unavailable (e.g. Intervals.icu
    provides duration but not stages)."""

    total_sec = 0.0
    seen = False
    for col in ("sleep_deep_sec", "sleep_light_sec", "sleep_rem_sec"):
        v = raw_row.get(col)
        if v is not None:
            total_sec += float(v)
            seen = True
    if not seen:
        fallback = raw_row.get("sleep_total_sec")
        if fallback is not None:
            try:
                total_sec = float(fallback)
                seen = total_sec > 0
            except (TypeError, ValueError):
                pass
    if not seen or total_sec <= 0:
        return None
    return round(total_sec / 3600.0, 2)


def _sleep_minutes_from_sec(raw_row: dict, col: str) -> Optional[float]:
    value = raw_row.get(col)
    if value is None:
        return None
    try:
        return round(float(value) / 60.0, 1)
    except (TypeError, ValueError):
        return None


def project_accepted_sleep_state_daily(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str,
    raw_row: dict,
    source_row_ids: Optional[list[str]] = None,
    source: str = "garmin",
    ingest_actor: str = "garmin_csv_adapter",
    commit_after: bool = True,
) -> bool:
    """UPSERT one day's accepted sleep state from a Garmin raw row.

    Maps the Garmin daily fields that describe sleep:

      - ``sleep_hours`` = (deep + light + rem) / 3600, rounded to 2dp.
      - minute breakdowns from the raw ``sleep_{deep,light,rem,awake}_sec``
        columns, rounded to 0.1 min.
      - score overall / quality / duration / recovery pass through.
      - awake_count, avg_sleep_respiration, avg_sleep_stress pass through.
      - ``sleep_start_ts``, ``sleep_end_ts``, ``avg_sleep_hrv`` are v1.1
        enrichments and stay NULL in v1.

    Behaves like
    :func:`.recovery.project_accepted_recovery_state_daily`: first insert
    stamps projected_at; subsequent updates stamp corrected_at.
    ``commit_after=False`` lets callers compose inside an outer
    transaction (the clean flow writes recovery + sleep + stress +
    running under one BEGIN/COMMIT).
    """

    now_iso = _now_iso()
    new_ids = list(source_row_ids or [])

    existing = conn.execute(
        "SELECT derived_from FROM accepted_sleep_state_daily "
        "WHERE as_of_date = ? AND user_id = ?",
        (as_of_date.isoformat(), user_id),
    ).fetchone()
    is_insert = existing is None

    sleep_hours = _sleep_hours_from_raw(raw_row)
    deep_min = _sleep_minutes_from_sec(raw_row, "sleep_deep_sec")
    light_min = _sleep_minutes_from_sec(raw_row, "sleep_light_sec")
    rem_min = _sleep_minutes_from_sec(raw_row, "sleep_rem_sec")
    awake_min = _sleep_minutes_from_sec(raw_row, "sleep_awake_sec")

    values = (
        sleep_hours,
        raw_row.get("sleep_score_overall"),
        raw_row.get("sleep_score_quality"),
        raw_row.get("sleep_score_duration"),
        raw_row.get("sleep_score_recovery"),
        deep_min, light_min, rem_min, awake_min,
        raw_row.get("awake_count"),
        None,  # sleep_start_ts (v1.1 enrichment)
        None,  # sleep_end_ts
        raw_row.get("avg_sleep_respiration"),
        raw_row.get("avg_sleep_stress"),
        None,  # avg_sleep_hrv (v1.1 enrichment)
    )

    if is_insert:
        derived_from_json = json.dumps(sorted(set(new_ids)), sort_keys=True)
        conn.execute(
            """
            INSERT INTO accepted_sleep_state_daily (
                sleep_hours,
                sleep_score_overall, sleep_score_quality,
                sleep_score_duration, sleep_score_recovery,
                sleep_deep_min, sleep_light_min, sleep_rem_min, sleep_awake_min,
                awake_count, sleep_start_ts, sleep_end_ts,
                avg_sleep_respiration, avg_sleep_stress, avg_sleep_hrv,
                derived_from, source, ingest_actor,
                projected_at, corrected_at,
                as_of_date, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                *values,
                derived_from_json,
                source,
                ingest_actor,
                now_iso,
                None,
                as_of_date.isoformat(),
                user_id,
            ),
        )
    else:
        merged_derived = _replace_dimension_in_derived_from(
            existing["derived_from"],
            new_ids=new_ids,
            owns=lambda rid: not _is_intake_submission_id(rid),
        )
        conn.execute(
            """
            UPDATE accepted_sleep_state_daily SET
                sleep_hours = ?,
                sleep_score_overall = ?, sleep_score_quality = ?,
                sleep_score_duration = ?, sleep_score_recovery = ?,
                sleep_deep_min = ?, sleep_light_min = ?,
                sleep_rem_min = ?, sleep_awake_min = ?,
                awake_count = ?, sleep_start_ts = ?, sleep_end_ts = ?,
                avg_sleep_respiration = ?, avg_sleep_stress = ?, avg_sleep_hrv = ?,
                derived_from = ?, source = ?, ingest_actor = ?,
                projected_at = ?, corrected_at = ?
            WHERE as_of_date = ? AND user_id = ?
            """,
            (
                *values,
                merged_derived,
                source,
                ingest_actor,
                now_iso,
                now_iso,
                as_of_date.isoformat(),
                user_id,
            ),
        )
    if commit_after:
        conn.commit()
    return is_insert
