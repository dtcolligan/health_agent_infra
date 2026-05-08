"""Accepted stress state projector.

Writes the Garmin-sourced portion of ``accepted_stress_state_daily``
(all-day stress + body-battery EoD) and merges the latest non-superseded
``stress_manual_raw`` submission into the same row. Co-ownership uses
the per-dimension ``derived_from`` hygiene shared with recovery: the
Garmin clean owns the non-intake dimension, and stress intake owns the
``m_stress_*`` dimension.

Pre-Phase-3 :func:`merge_manual_stress_into_accepted_stress` wrote to
``accepted_recovery_state_daily``; migration 004 moved the
``manual_stress_score`` column onto the dedicated stress table and the
function moved with it. The legacy name survives as an alias for one
deprecation window.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from typing import Optional

from health_agent_infra.core.state.projectors._shared import (
    _is_intake_submission_id,
    _is_stress_submission_id,
    _now_iso,
    _replace_dimension_in_derived_from,
)


def project_accepted_stress_state_daily(
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
    """UPSERT the Garmin-sourced portion of one day's accepted stress state.

    Writes ``garmin_all_day_stress`` (from raw ``all_day_stress``) and
    ``body_battery_end_of_day`` (from raw ``body_battery``). The
    user-reported ``manual_stress_score`` is owned by
    :func:`merge_manual_stress_into_accepted_stress` and is never touched
    here — on UPDATE, any pre-existing manual score is preserved, same
    per-dimension ownership pattern we use for recovery (now just for
    sleep/stress co-ownership if it arises) and nutrition.

    ``stress_event_count`` and ``stress_tags_json`` are v1.1 enrichments;
    they stay NULL on Garmin-only writes.
    """

    now_iso = _now_iso()
    new_ids = list(source_row_ids or [])

    existing = conn.execute(
        "SELECT derived_from FROM accepted_stress_state_daily "
        "WHERE as_of_date = ? AND user_id = ?",
        (as_of_date.isoformat(), user_id),
    ).fetchone()
    is_insert = existing is None

    if is_insert:
        derived_from_json = json.dumps(sorted(set(new_ids)), sort_keys=True)
        conn.execute(
            """
            INSERT INTO accepted_stress_state_daily (
                garmin_all_day_stress, manual_stress_score,
                stress_event_count, stress_tags_json,
                body_battery_end_of_day,
                derived_from, source, ingest_actor,
                projected_at, corrected_at,
                as_of_date, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                raw_row.get("all_day_stress"),
                None,  # manual_stress_score — owned by stress_manual_raw flow
                None,  # stress_event_count — v1.1
                None,  # stress_tags_json — v1.1 (manual tags flow through merge)
                raw_row.get("body_battery"),
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
        # Preserve manual_stress_score + stress_tags_json across Garmin
        # re-pulls by never touching them in the UPDATE. The clean flow
        # owns the Garmin dimension of derived_from; the intake flow
        # owns the m_stress_* dimension.
        merged_derived = _replace_dimension_in_derived_from(
            existing["derived_from"],
            new_ids=new_ids,
            owns=lambda rid: not _is_intake_submission_id(rid),
        )
        conn.execute(
            """
            UPDATE accepted_stress_state_daily SET
                garmin_all_day_stress = ?,
                body_battery_end_of_day = ?,
                derived_from = ?, source = ?, ingest_actor = ?,
                projected_at = ?, corrected_at = ?
            WHERE as_of_date = ? AND user_id = ?
            """,
            (
                raw_row.get("all_day_stress"),
                raw_row.get("body_battery"),
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


def merge_manual_stress_into_accepted_stress(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str,
    ingest_actor: str,
    commit_after: bool = True,
) -> bool:
    """Pull the latest non-superseded stress score from
    ``stress_manual_raw`` and merge it into
    ``accepted_stress_state_daily.manual_stress_score``.

    Two cases:

      - Existing stress row (likely from ``hai clean``): UPDATE only
        ``manual_stress_score`` + ``stress_tags_json`` +
        ``derived_from`` + provenance fields + ``corrected_at``.
        Garmin-sourced fields (``garmin_all_day_stress``,
        ``body_battery_end_of_day``) are preserved by omission.
      - No stress row yet (stress logged before clean): INSERT a
        minimal row with manual fields populated and Garmin fields NULL.
        Snapshot will tag the Garmin fields as ``unavailable_at_source``
        until ``hai clean`` fills them in.

    Returns ``True`` on insert, ``False`` on update. (Pre-Phase-3 this
    function wrote to accepted_recovery_state_daily; migration 004 moved
    the manual_stress_score column onto the new stress table and this
    function moves with it. The legacy name survives as an alias at the
    module export level for one deprecation window — see
    ``core/state/__init__.py``.)
    """

    latest = conn.execute(
        """
        SELECT submission_id, score, tags
        FROM stress_manual_raw smr
        WHERE smr.as_of_date = ? AND smr.user_id = ?
          AND smr.submission_id NOT IN (
              SELECT supersedes_submission_id FROM stress_manual_raw
              WHERE supersedes_submission_id IS NOT NULL
          )
        ORDER BY smr.ingested_at DESC
        LIMIT 1
        """,
        (as_of_date.isoformat(), user_id),
    ).fetchone()

    if latest is None:
        # No raw rows to merge from — defensive no-op (shouldn't happen
        # in the normal flow since the CLI projects raw THEN merges).
        return False

    existing = conn.execute(
        "SELECT derived_from FROM accepted_stress_state_daily "
        "WHERE as_of_date = ? AND user_id = ?",
        (as_of_date.isoformat(), user_id),
    ).fetchone()
    is_insert = existing is None

    now_iso = _now_iso()
    new_ids = [latest["submission_id"]]
    tags_value = latest["tags"]  # stored as JSON string or None

    if is_insert:
        # Stress-first scenario: minimal row, Garmin fields NULL.
        conn.execute(
            """
            INSERT INTO accepted_stress_state_daily (
                garmin_all_day_stress, manual_stress_score,
                stress_event_count, stress_tags_json,
                body_battery_end_of_day,
                derived_from, source, ingest_actor,
                projected_at, corrected_at,
                as_of_date, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                None,  # garmin_all_day_stress — no clean yet
                int(latest["score"]),
                None,  # stress_event_count — v1.1
                tags_value,
                None,  # body_battery_end_of_day — no clean yet
                json.dumps(sorted(set(new_ids)), sort_keys=True),
                "user_manual", ingest_actor,
                now_iso, None,
                as_of_date.isoformat(), user_id,
            ),
        )
    else:
        merged_derived = _replace_dimension_in_derived_from(
            existing["derived_from"],
            new_ids=new_ids,
            owns=_is_stress_submission_id,
        )
        conn.execute(
            """
            UPDATE accepted_stress_state_daily SET
                manual_stress_score = ?,
                stress_tags_json = ?,
                derived_from = ?, source = ?, ingest_actor = ?,
                projected_at = ?, corrected_at = ?
            WHERE as_of_date = ? AND user_id = ?
            """,
            (
                int(latest["score"]),
                tags_value,
                merged_derived,
                "user_manual", ingest_actor,
                now_iso, now_iso,
                as_of_date.isoformat(), user_id,
            ),
        )
    if commit_after:
        conn.commit()
    return is_insert


# Legacy alias: kept so any in-transit imports during Phase 3 continue to
# work. The body above writes to accepted_stress_state_daily now.
merge_manual_stress_into_accepted_recovery = merge_manual_stress_into_accepted_stress
