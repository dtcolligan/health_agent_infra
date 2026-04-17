"""Projection from typed dataclasses into SQLite state tables.

Phase 7A.2. Reads agent-authored artifacts (`TrainingRecommendation`,
`ReviewEvent`, `ReviewOutcome`) and inserts them into `recommendation_log`,
`review_event`, and `review_outcome`. Idempotent where the schema supports it
(recommendation_log + review_event have declared PKs; review_outcome is
append-only autoincrement and is deduplicated by reading the source JSONL
directly at reproject time).

Dual-write contract (per plan Pre-flight):
  - JSONL append is the audit boundary. Always happens first at the CLI.
  - Projector INSERT is best-effort; a failure here is recoverable via
    `hai state reproject` because the JSONL retains the durable record.
  - The projector never mutates JSONL.

Provenance (per state_model_v1.md §4):
  - recommendations: source='claude_agent_v1', ingest_actor='claude_agent_v1'
    by default (the agent both originates and transports the recommendation).
    Caller may override when a different agent identity is in use.
  - review events are runtime-generated and carry source='health_agent_infra',
    ingest_actor='health_agent_infra'.
  - review outcomes carry source='user_manual' + ingest_actor from the caller
    (typically 'claude_agent_v1' when the agent mediates).
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Optional

from health_agent_infra.core.schemas import (
    PolicyDecision,
    ReviewEvent,
    ReviewOutcome,
)
from health_agent_infra.domains.recovery.schemas import TrainingRecommendation


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bool_to_int(value: bool) -> int:
    return 1 if value else 0


def _opt_bool_to_int(value: Optional[bool]) -> Optional[int]:
    if value is None:
        return None
    return 1 if value else 0


def _is_stress_submission_id(rid: str) -> bool:
    """True for stress raw submission IDs (CLI naming: ``m_stress_*``)."""

    return rid.startswith("m_stress_")


def _is_intake_submission_id(rid: str) -> bool:
    """True for any user-intake submission id (``m_<kind>_<date>_*``)."""

    return rid.startswith("m_")


def _replace_dimension_in_derived_from(
    existing_json: Optional[str],
    *,
    new_ids: list[str],
    owns: callable,
) -> str:
    """Per-dimension slot replacement for ``derived_from``.

    ``accepted_recovery_state_daily`` is co-owned by the Garmin-clean
    flow and the manual-stress merge. Each projector owns one dimension
    of contributor IDs (Garmin batch IDs vs ``m_stress_*`` submission
    IDs). On UPDATE the projector replaces its own dimension's IDs with
    the latest contributors; other dimensions' IDs are preserved.

    The ``owns(id)`` predicate decides which existing IDs belong to the
    caller's dimension. The result:

      - clean → derived_from = [garmin_batch]
      - stress → derived_from = [garmin_batch, m_stress_x]   ← garmin preserved
      - clean again → derived_from = [garmin_batch_b, m_stress_x]  ← stress preserved
      - stress correction → derived_from = [garmin_batch_b, m_stress_y]
        (m_stress_x evicted: superseded raw rows no longer contribute to
        the current accepted row, and the merge function picks only the
        latest non-superseded raw to source from.)

    Robust against absent / malformed prior values.
    """

    existing: list[str] = []
    if existing_json:
        try:
            parsed = json.loads(existing_json)
            if isinstance(parsed, list):
                existing = [str(x) for x in parsed]
        except (TypeError, json.JSONDecodeError):
            existing = []
    surviving = [rid for rid in existing if not owns(rid)]
    merged = sorted(set(surviving) | set(new_ids or []))
    return json.dumps(merged, sort_keys=True)


# ---------------------------------------------------------------------------
# TrainingRecommendation -> recommendation_log
# ---------------------------------------------------------------------------

def project_recommendation(
    conn: sqlite3.Connection,
    recommendation: TrainingRecommendation,
    *,
    source: str = "claude_agent_v1",
    ingest_actor: str = "claude_agent_v1",
    agent_version: Optional[str] = None,
    produced_at: Optional[datetime] = None,
    jsonl_offset: Optional[int] = None,
) -> bool:
    """Insert a recommendation into recommendation_log.

    Idempotent on ``recommendation_id``: re-running does nothing and returns
    ``False``. First-time insert returns ``True``.

    ``produced_at`` defaults to the recommendation's ``issued_at`` (best
    available proxy until agents report a distinct "produced" timestamp).
    ``validated_at`` and ``projected_at`` are both stamped as now.
    """

    existing = conn.execute(
        "SELECT 1 FROM recommendation_log WHERE recommendation_id = ?",
        (recommendation.recommendation_id,),
    ).fetchone()
    if existing is not None:
        return False

    produced_iso = (
        produced_at.isoformat() if produced_at is not None
        else recommendation.issued_at.isoformat()
    )

    conn.execute(
        """
        INSERT INTO recommendation_log (
            recommendation_id, user_id, for_date, issued_at,
            action, confidence, bounded, payload_json,
            jsonl_offset, source, ingest_actor, agent_version,
            produced_at, validated_at, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            recommendation.recommendation_id,
            recommendation.user_id,
            recommendation.for_date.isoformat(),
            recommendation.issued_at.isoformat(),
            recommendation.action,
            recommendation.confidence,
            _bool_to_int(recommendation.bounded),
            json.dumps(recommendation.to_dict(), sort_keys=True),
            jsonl_offset,
            source,
            ingest_actor,
            agent_version,
            produced_iso,
            _now_iso(),
            _now_iso(),
        ),
    )
    conn.commit()
    return True


# ---------------------------------------------------------------------------
# ReviewEvent -> review_event
# ---------------------------------------------------------------------------

def project_review_event(
    conn: sqlite3.Connection,
    event: ReviewEvent,
    *,
    source: str = "health_agent_infra",
    ingest_actor: str = "health_agent_infra",
) -> bool:
    """Insert a review event into review_event.

    Idempotent on ``review_event_id``. Returns ``True`` on first insert,
    ``False`` if already present.

    Note: review_event's schema has FKs requiring the referenced
    recommendation_id to exist. Caller must have projected the recommendation
    first, or the INSERT will fail with IntegrityError.
    """

    existing = conn.execute(
        "SELECT 1 FROM review_event WHERE review_event_id = ?",
        (event.review_event_id,),
    ).fetchone()
    if existing is not None:
        return False

    conn.execute(
        """
        INSERT INTO review_event (
            review_event_id, recommendation_id, user_id,
            review_at, review_question, domain, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.review_event_id,
            event.recommendation_id,
            event.user_id,
            event.review_at.isoformat(),
            event.review_question,
            event.domain,
            _now_iso(),
        ),
    )
    conn.commit()
    # Source/ingest_actor live in state_model_v1.md §4 but the review_event
    # table in migration 001 doesn't carry them as columns (events are
    # runtime-generated, not user- or agent-authored facts in the same sense).
    # Retained as function args so callers don't need to change when/if we
    # add those columns later.
    del source
    del ingest_actor
    return True


# ---------------------------------------------------------------------------
# ReviewOutcome -> review_outcome
# ---------------------------------------------------------------------------

def project_review_outcome(
    conn: sqlite3.Connection,
    outcome: ReviewOutcome,
    *,
    source: str = "user_manual",
    ingest_actor: str = "claude_agent_v1",
    jsonl_offset: Optional[int] = None,
) -> int:
    """Insert a review outcome. Returns the autoincremented outcome_id.

    review_outcome is append-only with an autoincrement PK — duplicate
    detection during reproject relies on (review_event_id, recorded_at)
    pair presence rather than a PK check. Normal dual-write from the CLI
    appends unconditionally; rely on the source JSONL being canonical.
    """

    cursor = conn.execute(
        """
        INSERT INTO review_outcome (
            review_event_id, recommendation_id, user_id, recorded_at,
            followed_recommendation, self_reported_improvement, free_text,
            domain, jsonl_offset, source, ingest_actor, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            outcome.review_event_id,
            outcome.recommendation_id,
            outcome.user_id,
            outcome.recorded_at.isoformat(),
            _bool_to_int(outcome.followed_recommendation),
            _opt_bool_to_int(outcome.self_reported_improvement),
            outcome.free_text,
            outcome.domain,
            jsonl_offset,
            source,
            ingest_actor,
            _now_iso(),
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


# ---------------------------------------------------------------------------
# Garmin raw daily row -> source_daily_garmin (raw evidence)
# ---------------------------------------------------------------------------

# Columns we persist into source_daily_garmin. Order matches migration 001.
# Any key in ``raw_row`` outside this list is ignored (defensive against CSV
# schema drift — new columns land via a later migration, not a silent write).
_SOURCE_DAILY_GARMIN_COLUMNS: tuple[str, ...] = (
    "steps", "distance_m", "active_kcal", "total_kcal",
    "moderate_intensity_min", "vigorous_intensity_min",
    "floors_ascended_m", "avg_environment_altitude_m",
    "resting_hr", "min_hr_day", "max_hr_day",
    "sleep_deep_sec", "sleep_light_sec", "sleep_rem_sec", "sleep_awake_sec",
    "avg_sleep_respiration", "avg_sleep_stress", "awake_count",
    "sleep_score_overall", "sleep_score_quality",
    "sleep_score_duration", "sleep_score_recovery",
    "all_day_stress", "body_battery",
    "training_readiness_level", "training_recovery_time_hours",
    "training_readiness_sleep_pct", "training_readiness_hrv_pct",
    "training_readiness_stress_pct", "training_readiness_sleep_history_pct",
    "training_readiness_load_pct", "training_readiness_hrv_weekly_avg",
    "training_readiness_valid_sleep",
    "acute_load", "chronic_load", "acwr_status", "acwr_status_feedback",
    "training_status", "training_status_feedback",
    "health_hrv_value", "health_hrv_status",
    "health_hrv_baseline_low", "health_hrv_baseline_high",
    "health_hr_value", "health_hr_status",
    "health_hr_baseline_low", "health_hr_baseline_high",
    "health_spo2_value", "health_spo2_status",
    "health_spo2_baseline_low", "health_spo2_baseline_high",
    "health_skin_temp_c_value", "health_skin_temp_c_status",
    "health_skin_temp_c_baseline_low", "health_skin_temp_c_baseline_high",
    "health_respiration_value", "health_respiration_status",
    "health_respiration_baseline_low", "health_respiration_baseline_high",
)


def project_source_daily_garmin(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str,
    raw_row: dict,
    export_batch_id: str,
    csv_row_index: int = 0,
    ingest_actor: str = "garmin_csv_adapter",
    supersedes_export_batch_id: Optional[str] = None,
    commit_after: bool = True,
) -> bool:
    """Append-only insert of one Garmin day-row into ``source_daily_garmin``.

    Returns ``True`` on insert, ``False`` if the (as_of_date, user_id,
    export_batch_id) PK already exists — re-running the same pull with the
    same batch id is a no-op. A genuinely-new pull with updated Garmin data
    should use a fresh ``export_batch_id`` so the correction lands as a new
    raw row (state_model_v1.md §3).

    ``commit_after`` defaults to True for standalone callers. Set False when
    composing multiple projector calls inside an outer transaction — the
    caller then owns the ``COMMIT`` / ``ROLLBACK`` lifecycle, guaranteeing
    all-or-nothing persistence across the composed projection.
    """

    existing = conn.execute(
        "SELECT 1 FROM source_daily_garmin WHERE as_of_date = ? AND user_id = ? "
        "AND export_batch_id = ?",
        (as_of_date.isoformat(), user_id, export_batch_id),
    ).fetchone()
    if existing is not None:
        return False

    values: list = [
        as_of_date.isoformat(), user_id, export_batch_id, csv_row_index,
        "garmin", ingest_actor, _now_iso(), supersedes_export_batch_id,
    ]
    for col in _SOURCE_DAILY_GARMIN_COLUMNS:
        values.append(raw_row.get(col))

    placeholders = ", ".join(["?"] * (8 + len(_SOURCE_DAILY_GARMIN_COLUMNS)))
    columns_sql = (
        "as_of_date, user_id, export_batch_id, csv_row_index, "
        "source, ingest_actor, ingested_at, supersedes_export_batch_id, "
        + ", ".join(_SOURCE_DAILY_GARMIN_COLUMNS)
    )
    conn.execute(
        f"INSERT INTO source_daily_garmin ({columns_sql}) VALUES ({placeholders})",
        values,
    )
    if commit_after:
        conn.commit()
    return True


# ---------------------------------------------------------------------------
# Accepted recovery state — UPSERT + corrected_at
# ---------------------------------------------------------------------------

def _sleep_hours_from_raw(raw_row: dict) -> Optional[float]:
    """Sum deep+light+rem sleep seconds, return hours. None if none present."""

    total_sec = 0.0
    seen = False
    for col in ("sleep_deep_sec", "sleep_light_sec", "sleep_rem_sec"):
        v = raw_row.get(col)
        if v is not None:
            total_sec += float(v)
            seen = True
    if not seen or total_sec <= 0:
        return None
    return round(total_sec / 3600.0, 2)


def _acwr_ratio_from_raw(raw_row: dict) -> Optional[float]:
    """Compute acute/chronic ratio when both fields present and chronic > 0."""

    acute = raw_row.get("acute_load")
    chronic = raw_row.get("chronic_load")
    if acute is None or chronic is None or chronic == 0:
        return None
    return round(float(acute) / float(chronic), 3)


_TRAINING_READINESS_COMPONENT_COLUMNS = (
    "training_readiness_sleep_pct",
    "training_readiness_hrv_pct",
    "training_readiness_stress_pct",
    "training_readiness_sleep_history_pct",
    "training_readiness_load_pct",
)


def _training_readiness_component_mean_pct_from_raw(raw_row: dict) -> Optional[float]:
    """Mean of the five Garmin readiness component pcts; None if any missing.

    **Not** Garmin's own overall readiness score. Garmin's CSV doesn't
    export that value, only the five dimension pcts and a categorical
    `training_readiness_level`. A plain arithmetic mean is the simplest
    summary; it can disagree with Garmin's categorical level because
    Garmin weights internally. Agents must treat this as a local proxy,
    cross-check against `training_readiness_level`, and surface any
    disagreement in their rationale.
    """

    vals: list[float] = []
    for col in _TRAINING_READINESS_COMPONENT_COLUMNS:
        v = raw_row.get(col)
        if v is None:
            return None
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            return None
    if not vals:
        return None
    return round(sum(vals) / len(vals), 1)


def project_accepted_recovery_state_daily(
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
    """UPSERT one day's accepted recovery state from a Garmin raw row.

    First write sets ``projected_at``; subsequent writes set ``corrected_at``
    per the hybrid correction grammar (state_model_v1.md §3). Returns
    ``True`` if this was an insert, ``False`` on update.

    **Scope.** Writes Garmin-sourced fields only.
    ``manual_stress_score`` is intentionally **not** written here — it is a
    user-reported fact that must land in ``stress_manual_raw`` first (so the
    raw→accepted audit chain holds), then be merged into this row by a
    separate projection step. That merge arrives with 7C's ``hai intake
    stress`` command. Until then, ``manual_stress_score`` stays NULL on
    every accepted recovery row written by this function.

    ``training_readiness_component_mean_pct`` is populated as the
    arithmetic mean of the five Garmin readiness component pcts (7B). It
    is **not** Garmin's own overall Training Readiness score — that number
    isn't exported in the daily CSV. None if any component is missing.

    ``commit_after``: set False when composing inside an outer transaction.
    """

    now_iso = _now_iso()
    new_ids = list(source_row_ids or [])

    existing = conn.execute(
        "SELECT derived_from FROM accepted_recovery_state_daily "
        "WHERE as_of_date = ? AND user_id = ?",
        (as_of_date.isoformat(), user_id),
    ).fetchone()
    is_insert = existing is None

    sleep_hours = _sleep_hours_from_raw(raw_row)
    acwr = _acwr_ratio_from_raw(raw_row)
    readiness_mean = _training_readiness_component_mean_pct_from_raw(raw_row)

    if is_insert:
        # Insert path: every column written, manual_stress_score=NULL
        # because no stress raw row exists yet for this day. A subsequent
        # `hai intake stress` will UPDATE it via the dedicated merge
        # projector below.
        derived_from_json = json.dumps(sorted(set(new_ids)), sort_keys=True)
        conn.execute(
            """
            INSERT INTO accepted_recovery_state_daily (
                sleep_hours, resting_hr, hrv_ms, all_day_stress,
                manual_stress_score, acute_load, chronic_load, acwr_ratio,
                training_readiness_component_mean_pct, body_battery_end_of_day,
                derived_from, source, ingest_actor,
                projected_at, corrected_at,
                as_of_date, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sleep_hours,
                raw_row.get("resting_hr"),
                raw_row.get("health_hrv_value"),
                raw_row.get("all_day_stress"),
                None,  # manual_stress_score — owned by stress_manual_raw flow
                raw_row.get("acute_load"),
                raw_row.get("chronic_load"),
                acwr,
                readiness_mean,
                raw_row.get("body_battery"),
                derived_from_json,
                source,
                ingest_actor,
                now_iso,
                None,  # corrected_at NULL on first insert
                as_of_date.isoformat(),
                user_id,
            ),
        )
    else:
        # Update path: only Garmin-sourced fields. manual_stress_score is
        # explicitly NOT in this UPDATE — preserves whatever value was
        # set by `hai intake stress`, even across Garmin re-pulls. This
        # closes the bug where re-running clean would silently wipe an
        # earlier stress merge.
        # derived_from: per-dimension slot replacement. The Garmin clean
        # owns the "non-intake" dimension — replace its prior contributor
        # IDs with the new ones, preserve any stress / nutrition slots.
        merged_derived = _replace_dimension_in_derived_from(
            existing["derived_from"],
            new_ids=new_ids,
            owns=lambda rid: not _is_intake_submission_id(rid),
        )
        conn.execute(
            """
            UPDATE accepted_recovery_state_daily SET
                sleep_hours = ?, resting_hr = ?, hrv_ms = ?, all_day_stress = ?,
                acute_load = ?, chronic_load = ?,
                acwr_ratio = ?, training_readiness_component_mean_pct = ?,
                body_battery_end_of_day = ?,
                derived_from = ?, source = ?, ingest_actor = ?,
                projected_at = ?, corrected_at = ?
            WHERE as_of_date = ? AND user_id = ?
            """,
            (
                sleep_hours,
                raw_row.get("resting_hr"),
                raw_row.get("health_hrv_value"),
                raw_row.get("all_day_stress"),
                raw_row.get("acute_load"),
                raw_row.get("chronic_load"),
                acwr,
                readiness_mean,
                raw_row.get("body_battery"),
                merged_derived,
                source,
                ingest_actor,
                now_iso,
                now_iso,  # corrected_at on update
                as_of_date.isoformat(),
                user_id,
            ),
        )
    if commit_after:
        conn.commit()
    return is_insert


# ---------------------------------------------------------------------------
# Accepted running state — UPSERT + corrected_at, derivation_path='garmin_daily'
# ---------------------------------------------------------------------------

def project_accepted_running_state_daily(
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
    """UPSERT one day's accepted running state with ``derivation_path='garmin_daily'``.

    In v1, running is synthesised from the daily Garmin aggregate
    (distance_m + intensity minutes). Per-activity ``running_session`` rows
    don't exist yet, so ``session_count`` and ``total_duration_s`` are NULL
    and snapshots must not flag them as partial (state_model_v1.md §8).

    ``commit_after``: set False when composing inside an outer transaction.
    """

    now_iso = _now_iso()
    derived_from_json = json.dumps(source_row_ids or [], sort_keys=True)

    existing = conn.execute(
        "SELECT 1 FROM accepted_running_state_daily "
        "WHERE as_of_date = ? AND user_id = ?",
        (as_of_date.isoformat(), user_id),
    ).fetchone()
    is_insert = existing is None

    values = (
        raw_row.get("distance_m"),
        None,  # total_duration_s — not in daily CSV; 7B-deferred enrichment
        raw_row.get("moderate_intensity_min"),
        raw_row.get("vigorous_intensity_min"),
        None,  # session_count — NULL by design on garmin_daily path
        "garmin_daily",
        derived_from_json,
        source,
        ingest_actor,
        now_iso,
        None if is_insert else now_iso,
        as_of_date.isoformat(),
        user_id,
    )

    if is_insert:
        conn.execute(
            """
            INSERT INTO accepted_running_state_daily (
                total_distance_m, total_duration_s,
                moderate_intensity_min, vigorous_intensity_min,
                session_count, derivation_path,
                derived_from, source, ingest_actor,
                projected_at, corrected_at,
                as_of_date, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
    else:
        conn.execute(
            """
            UPDATE accepted_running_state_daily SET
                total_distance_m = ?, total_duration_s = ?,
                moderate_intensity_min = ?, vigorous_intensity_min = ?,
                session_count = ?, derivation_path = ?,
                derived_from = ?, source = ?, ingest_actor = ?,
                projected_at = ?, corrected_at = ?
            WHERE as_of_date = ? AND user_id = ?
            """,
            values,
        )
    if commit_after:
        conn.commit()
    return is_insert


# ---------------------------------------------------------------------------
# Gym intake -> gym_session + gym_set (raw) + accepted_resistance_training_state_daily
# ---------------------------------------------------------------------------

def project_gym_session(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    user_id: str,
    as_of_date: date,
    session_name: Optional[str],
    notes: Optional[str],
    submission_id: str,
    ingest_actor: str,
    source: str = "user_manual",
    commit_after: bool = True,
) -> bool:
    """Insert one gym_session header row. Idempotent on session_id.

    Returns ``True`` on insert, ``False`` if the session_id already exists.
    A session is raw evidence; header metadata is immutable once logged.
    Corrections apply at the set level via ``supersedes_set_id``.
    """

    existing = conn.execute(
        "SELECT 1 FROM gym_session WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if existing is not None:
        return False

    conn.execute(
        """
        INSERT INTO gym_session (
            session_id, user_id, as_of_date, session_name, notes,
            source, ingest_actor, submission_id, ingested_at,
            supersedes_session_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id, user_id, as_of_date.isoformat(),
            session_name, notes,
            source, ingest_actor, submission_id, _now_iso(),
            None,
        ),
    )
    if commit_after:
        conn.commit()
    return True


def project_gym_set(
    conn: sqlite3.Connection,
    *,
    set_id: str,
    session_id: str,
    set_number: int,
    exercise_name: str,
    weight_kg: Optional[float],
    reps: Optional[int],
    rpe: Optional[float],
    supersedes_set_id: Optional[str] = None,
    commit_after: bool = True,
) -> bool:
    """Insert one gym_set. Idempotent on set_id (deterministic per session/number).

    Returns ``True`` on insert, ``False`` if the set_id already exists.
    Append-only raw grammar (state_model_v1.md §3): corrections pass a fresh
    set_id + ``supersedes_set_id`` pointing at the row being replaced.
    """

    existing = conn.execute(
        "SELECT 1 FROM gym_set WHERE set_id = ?",
        (set_id,),
    ).fetchone()
    if existing is not None:
        return False

    conn.execute(
        """
        INSERT INTO gym_set (
            set_id, session_id, set_number, exercise_name,
            weight_kg, reps, rpe,
            ingested_at, supersedes_set_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            set_id, session_id, set_number, exercise_name,
            weight_kg, reps, rpe,
            _now_iso(), supersedes_set_id,
        ),
    )
    if commit_after:
        conn.commit()
    return True


def project_accepted_resistance_training_state_daily(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str,
    ingest_actor: str,
    source: str = "user_manual",
    commit_after: bool = True,
) -> bool:
    """Recompute + UPSERT the day's accepted resistance-training aggregate.

    Aggregates every non-superseded gym_set via the row's session, filtered
    to (as_of_date, user_id). Superseded rows are excluded by checking
    whether their set_id appears as another row's ``supersedes_set_id`` —
    kept simple for v1 (no corrections in 7C.1's CLI, so this is
    forward-compatible when set-level corrections land).

    Returns ``True`` on insert, ``False`` on update (corrected_at set).

    **Provenance.** ``derived_from`` is a JSON list of session_ids that
    contributed. Auditors can JOIN back to gym_session for per-session
    provenance (source, ingest_actor, submission_id).
    """

    rows = conn.execute(
        """
        SELECT
            gs.session_id,
            gset.set_id, gset.exercise_name, gset.weight_kg, gset.reps
        FROM gym_session gs
        JOIN gym_set gset ON gset.session_id = gs.session_id
        WHERE gs.as_of_date = ? AND gs.user_id = ?
          AND gset.set_id NOT IN (
              SELECT supersedes_set_id FROM gym_set
              WHERE supersedes_set_id IS NOT NULL
          )
        """,
        (as_of_date.isoformat(), user_id),
    ).fetchall()

    session_ids = sorted({r["session_id"] for r in rows})
    exercises = sorted({r["exercise_name"] for r in rows})
    total_sets = len(rows)
    total_volume = None
    if rows:
        vol_values = [
            (r["weight_kg"] or 0) * (r["reps"] or 0)
            for r in rows
            if r["weight_kg"] is not None and r["reps"] is not None
        ]
        if vol_values:
            total_volume = round(sum(vol_values), 2)

    now_iso = _now_iso()
    derived_from_json = json.dumps(session_ids, sort_keys=True)
    exercises_json = json.dumps(exercises, sort_keys=True)

    existing = conn.execute(
        "SELECT 1 FROM accepted_resistance_training_state_daily "
        "WHERE as_of_date = ? AND user_id = ?",
        (as_of_date.isoformat(), user_id),
    ).fetchone()
    is_insert = existing is None

    values = (
        len(session_ids),
        total_sets,
        total_volume,
        exercises_json,
        derived_from_json,
        source,
        ingest_actor,
        now_iso,
        None if is_insert else now_iso,
        as_of_date.isoformat(),
        user_id,
    )

    if is_insert:
        conn.execute(
            """
            INSERT INTO accepted_resistance_training_state_daily (
                session_count, total_sets, total_volume_kg_reps, exercises,
                derived_from, source, ingest_actor,
                projected_at, corrected_at,
                as_of_date, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
    else:
        conn.execute(
            """
            UPDATE accepted_resistance_training_state_daily SET
                session_count = ?, total_sets = ?, total_volume_kg_reps = ?,
                exercises = ?, derived_from = ?, source = ?, ingest_actor = ?,
                projected_at = ?, corrected_at = ?
            WHERE as_of_date = ? AND user_id = ?
            """,
            values,
        )
    if commit_after:
        conn.commit()
    return is_insert


# ---------------------------------------------------------------------------
# Nutrition intake -> nutrition_intake_raw + accepted_nutrition_state_daily
# ---------------------------------------------------------------------------

def latest_nutrition_submission_id(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str,
) -> Optional[str]:
    """Return the most recent submission_id for ``(as_of_date, user_id)``.

    Follows the supersedes chain forward: returns the tail of the chain
    (the row NOT superseded by any other row). Used by the CLI to stamp
    ``supersedes_submission_id`` on new submissions so the correction
    chain stays well-formed.
    """

    row = conn.execute(
        """
        SELECT submission_id FROM nutrition_intake_raw nir
        WHERE nir.as_of_date = ? AND nir.user_id = ?
          AND nir.submission_id NOT IN (
              SELECT supersedes_submission_id FROM nutrition_intake_raw
              WHERE supersedes_submission_id IS NOT NULL
          )
        ORDER BY nir.ingested_at DESC
        LIMIT 1
        """,
        (as_of_date.isoformat(), user_id),
    ).fetchone()
    return row["submission_id"] if row else None


def project_nutrition_intake_raw(
    conn: sqlite3.Connection,
    *,
    submission_id: str,
    user_id: str,
    as_of_date: date,
    calories: float,
    protein_g: float,
    carbs_g: float,
    fat_g: float,
    hydration_l: Optional[float],
    meals_count: Optional[int],
    ingest_actor: str,
    supersedes_submission_id: Optional[str] = None,
    source: str = "user_manual",
    commit_after: bool = True,
) -> bool:
    """Append-only insert of one nutrition submission into
    ``nutrition_intake_raw``. Idempotent on submission_id.

    Corrections stamp ``supersedes_submission_id`` on the new row; the
    superseded row stays for audit.
    """

    existing = conn.execute(
        "SELECT 1 FROM nutrition_intake_raw WHERE submission_id = ?",
        (submission_id,),
    ).fetchone()
    if existing is not None:
        return False

    conn.execute(
        """
        INSERT INTO nutrition_intake_raw (
            submission_id, user_id, as_of_date,
            calories, protein_g, carbs_g, fat_g,
            hydration_l, meals_count,
            source, ingest_actor, ingested_at,
            supersedes_submission_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            submission_id, user_id, as_of_date.isoformat(),
            calories, protein_g, carbs_g, fat_g,
            hydration_l, meals_count,
            source, ingest_actor, _now_iso(),
            supersedes_submission_id,
        ),
    )
    if commit_after:
        conn.commit()
    return True


def project_accepted_nutrition_state_daily(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str,
    ingest_actor: str,
    source: str = "user_manual",
    commit_after: bool = True,
) -> bool:
    """Recompute + UPSERT the day's accepted nutrition state from the
    latest non-superseded raw row for ``(as_of_date, user_id)``.

    Returns ``True`` on insert, ``False`` on update. ``corrected_at`` is
    set on update, NULL on insert (hybrid correction grammar).

    ``derived_from`` lists the submission_id that drove this projection.
    Audit chain: follow ``supersedes_submission_id`` back through
    ``nutrition_intake_raw`` for history.
    """

    latest = conn.execute(
        """
        SELECT submission_id, calories, protein_g, carbs_g, fat_g,
               hydration_l, meals_count
        FROM nutrition_intake_raw nir
        WHERE nir.as_of_date = ? AND nir.user_id = ?
          AND nir.submission_id NOT IN (
              SELECT supersedes_submission_id FROM nutrition_intake_raw
              WHERE supersedes_submission_id IS NOT NULL
          )
        ORDER BY nir.ingested_at DESC
        LIMIT 1
        """,
        (as_of_date.isoformat(), user_id),
    ).fetchone()

    if latest is None:
        # No raw rows to derive from — leave the accepted row alone (no-op).
        # This can legitimately happen during reproject if every raw row is
        # superseded by a non-existent id, which shouldn't occur in
        # practice but is benign.
        return False

    existing = conn.execute(
        "SELECT 1 FROM accepted_nutrition_state_daily "
        "WHERE as_of_date = ? AND user_id = ?",
        (as_of_date.isoformat(), user_id),
    ).fetchone()
    is_insert = existing is None

    now_iso = _now_iso()
    derived_from_json = json.dumps([latest["submission_id"]], sort_keys=True)

    values = (
        latest["calories"], latest["protein_g"],
        latest["carbs_g"], latest["fat_g"],
        latest["hydration_l"], latest["meals_count"],
        derived_from_json, source, ingest_actor,
        now_iso,
        None if is_insert else now_iso,
        as_of_date.isoformat(), user_id,
    )

    if is_insert:
        conn.execute(
            """
            INSERT INTO accepted_nutrition_state_daily (
                calories, protein_g, carbs_g, fat_g,
                hydration_l, meals_count,
                derived_from, source, ingest_actor,
                projected_at, corrected_at,
                as_of_date, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
    else:
        conn.execute(
            """
            UPDATE accepted_nutrition_state_daily SET
                calories = ?, protein_g = ?, carbs_g = ?, fat_g = ?,
                hydration_l = ?, meals_count = ?,
                derived_from = ?, source = ?, ingest_actor = ?,
                projected_at = ?, corrected_at = ?
            WHERE as_of_date = ? AND user_id = ?
            """,
            values,
        )
    if commit_after:
        conn.commit()
    return is_insert


# ---------------------------------------------------------------------------
# Stress intake -> stress_manual_raw + accepted_recovery_state_daily merge
# ---------------------------------------------------------------------------

def project_stress_manual_raw(
    conn: sqlite3.Connection,
    *,
    submission_id: str,
    user_id: str,
    as_of_date: date,
    score: int,
    tags: Optional[list[str]],
    ingest_actor: str,
    supersedes_submission_id: Optional[str] = None,
    source: str = "user_manual",
    commit_after: bool = True,
) -> bool:
    """Append-only insert into ``stress_manual_raw``. Idempotent on submission_id.

    Score must be in 1–5 (CHECK enforced upstream at the CLI). Tags are
    JSON-encoded for storage when present (the column is TEXT).
    """

    existing = conn.execute(
        "SELECT 1 FROM stress_manual_raw WHERE submission_id = ?",
        (submission_id,),
    ).fetchone()
    if existing is not None:
        return False

    tags_json = json.dumps(tags, sort_keys=True) if tags else None

    conn.execute(
        """
        INSERT INTO stress_manual_raw (
            submission_id, user_id, as_of_date,
            score, tags,
            source, ingest_actor, ingested_at,
            supersedes_submission_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            submission_id, user_id, as_of_date.isoformat(),
            int(score), tags_json,
            source, ingest_actor, _now_iso(),
            supersedes_submission_id,
        ),
    )
    if commit_after:
        conn.commit()
    return True


def merge_manual_stress_into_accepted_recovery(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str,
    ingest_actor: str,
    commit_after: bool = True,
) -> bool:
    """Pull the latest non-superseded stress score from
    ``stress_manual_raw`` and merge it into
    ``accepted_recovery_state_daily.manual_stress_score``.

    Two cases:

      - Existing recovery row (likely from ``hai clean``): UPDATE only
        ``manual_stress_score`` + ``derived_from`` + provenance fields +
        ``corrected_at``. Garmin-sourced fields are preserved (the clean
        projector now also preserves manual_stress_score reciprocally,
        so the two flows compose without clobbering).
      - No recovery row yet (stress logged before clean): INSERT a
        minimal row with ``manual_stress_score`` populated and Garmin
        fields NULL. Snapshot will tag those Garmin fields as
        ``unavailable_at_source`` until ``hai clean`` fills them in.

    Returns ``True`` on insert, ``False`` on update.
    """

    latest = conn.execute(
        """
        SELECT submission_id, score
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
        "SELECT derived_from FROM accepted_recovery_state_daily "
        "WHERE as_of_date = ? AND user_id = ?",
        (as_of_date.isoformat(), user_id),
    ).fetchone()
    is_insert = existing is None

    now_iso = _now_iso()
    new_ids = [latest["submission_id"]]

    if is_insert:
        # Stress-first scenario: minimal row, Garmin fields NULL.
        conn.execute(
            """
            INSERT INTO accepted_recovery_state_daily (
                manual_stress_score,
                derived_from, source, ingest_actor,
                projected_at, corrected_at,
                as_of_date, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(latest["score"]),
                json.dumps(sorted(set(new_ids)), sort_keys=True),
                "user_manual", ingest_actor,
                now_iso, None,
                as_of_date.isoformat(), user_id,
            ),
        )
    else:
        # Merge into existing row: Garmin fields untouched, manual_stress_score
        # set, source/ingest reflect this most-recent write, derived_from
        # uses per-dimension slot replacement — strip prior stress IDs
        # (the previous m_stress_* contributor was superseded; only the
        # latest non-superseded raw stress row contributes to the current
        # accepted manual_stress_score), keep Garmin contributors, add
        # this submission. Per state_model_v1.md §4 derived_from lists
        # the raw rows that justify the CURRENT accepted values.
        merged_derived = _replace_dimension_in_derived_from(
            existing["derived_from"],
            new_ids=new_ids,
            owns=_is_stress_submission_id,
        )
        conn.execute(
            """
            UPDATE accepted_recovery_state_daily SET
                manual_stress_score = ?,
                derived_from = ?, source = ?, ingest_actor = ?,
                projected_at = ?, corrected_at = ?
            WHERE as_of_date = ? AND user_id = ?
            """,
            (
                int(latest["score"]),
                merged_derived,
                "user_manual", ingest_actor,
                now_iso, now_iso,
                as_of_date.isoformat(), user_id,
            ),
        )
    if commit_after:
        conn.commit()
    return is_insert


# ---------------------------------------------------------------------------
# Note intake -> context_note (append-only, no accepted layer)
# ---------------------------------------------------------------------------

def project_context_note(
    conn: sqlite3.Connection,
    *,
    note_id: str,
    user_id: str,
    as_of_date: date,
    recorded_at: datetime,
    text: str,
    tags: Optional[list[str]],
    ingest_actor: str,
    source: str = "user_manual",
    supersedes_note_id: Optional[str] = None,
    commit_after: bool = True,
) -> bool:
    """Append-only insert into ``context_note``. Idempotent on note_id.

    Notes have no accepted-layer projection — the raw row IS the
    canonical state per state_model_v1.md §1. Snapshot reads them via
    ``notes.recent``.
    """

    existing = conn.execute(
        "SELECT 1 FROM context_note WHERE note_id = ?",
        (note_id,),
    ).fetchone()
    if existing is not None:
        return False

    tags_json = json.dumps(tags, sort_keys=True) if tags else None

    conn.execute(
        """
        INSERT INTO context_note (
            note_id, user_id, as_of_date, recorded_at, text, tags,
            source, ingest_actor, ingested_at, supersedes_note_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            note_id, user_id, as_of_date.isoformat(),
            recorded_at.isoformat(), text, tags_json,
            source, ingest_actor, _now_iso(), supersedes_note_id,
        ),
    )
    if commit_after:
        conn.commit()
    return True


# ---------------------------------------------------------------------------
# Reprojection from JSONL audit logs
# ---------------------------------------------------------------------------

class ReprojectBaseDirError(Exception):
    """Raised when reproject is asked to rebuild from a base-dir that does
    not contain any of the expected audit JSONL files.

    Guards against the failure mode where a typo in ``--base-dir`` silently
    wipes the projection tables. Callers who genuinely want to reset the DB
    can opt into this via ``allow_empty=True``.
    """


def reproject_from_jsonl(conn: sqlite3.Connection, base_dir, *, allow_empty: bool = False) -> dict:
    """Rebuild projected tables from the JSONL audit logs under ``base_dir``.

    **Scoped truncation.** Tables are truncated and rebuilt per **log group**
    based on which JSONL files are present in ``base_dir``:

      - Recommendation group — any of ``recommendation_log.jsonl``,
        ``review_events.jsonl``, ``review_outcomes.jsonl`` present ⇒
        truncate + rebuild ``recommendation_log``, ``review_event``,
        ``review_outcome``.
      - Gym group — ``gym_sessions.jsonl`` present ⇒ truncate + rebuild
        ``gym_session``, ``gym_set``, ``accepted_resistance_training_state_daily``.

    Groups whose JSONLs are absent are **not touched**. This guards against
    the failure mode where a gym-only base_dir silently wipes unrelated
    recommendation data (the logs ship from independent flows).

    All truncation + replay happens inside one ``BEGIN EXCLUSIVE`` /
    ``COMMIT`` transaction; a mid-flight failure rolls back every group.
    Idempotent: re-running reproduces the same DB state.

    **Safety.** If none of the expected JSONL files exist, raises
    ``ReprojectBaseDirError`` before touching the DB, so a typo in the
    path can't silently wipe the projection tables. Pass
    ``allow_empty=True`` / ``--allow-empty-reproject`` to override —
    reserved for operators who explicitly want a full reset; note that
    even with ``allow_empty=True``, only groups whose JSONL is present
    get truncated. To fully wipe everything, the operator should drop
    tables manually.
    """

    from pathlib import Path

    base = Path(base_dir)
    rec_log = base / "recommendation_log.jsonl"
    events_log = base / "review_events.jsonl"
    outcomes_log = base / "review_outcomes.jsonl"
    gym_log = base / "gym_sessions.jsonl"
    nutrition_log = base / "nutrition_intake.jsonl"
    stress_log = base / "stress_manual.jsonl"
    notes_log = base / "context_notes.jsonl"

    has_rec_group = any(p.exists() for p in (rec_log, events_log, outcomes_log))
    has_gym_group = gym_log.exists()
    has_nutrition_group = nutrition_log.exists()
    has_stress_group = stress_log.exists()
    has_notes_group = notes_log.exists()

    if not allow_empty and not (
        has_rec_group or has_gym_group or has_nutrition_group
        or has_stress_group or has_notes_group
    ):
        raise ReprojectBaseDirError(
            f"no audit JSONL files found under {base}. Expected at least "
            f"one of: recommendation_log.jsonl, review_events.jsonl, "
            f"review_outcomes.jsonl, gym_sessions.jsonl, "
            f"nutrition_intake.jsonl, stress_manual.jsonl, "
            f"context_notes.jsonl. Refusing to touch the projection "
            f"tables. Pass allow_empty=True / --allow-empty-reproject to "
            f"override."
        )

    counts = {
        "recommendations": 0, "review_events": 0, "review_outcomes": 0,
        "gym_sessions": 0, "gym_sets": 0,
        "accepted_resistance_training_state_daily": 0,
        "nutrition_intake_raw": 0,
        "accepted_nutrition_state_daily": 0,
        "stress_manual_raw": 0,
        "accepted_recovery_manual_stress_merged": 0,
        "context_notes": 0,
    }

    conn.execute("BEGIN EXCLUSIVE")
    try:
        if has_rec_group:
            # Recommendation group: outcomes FK -> events FK -> recs. Delete
            # in reverse dependency order, then replay in forward order.
            conn.execute("DELETE FROM review_outcome")
            conn.execute("DELETE FROM review_event")
            conn.execute("DELETE FROM recommendation_log")
        if has_gym_group:
            # Gym group: gym_set FK -> gym_session. Accepted resistance
            # daily is derived and must be rebuilt alongside.
            conn.execute("DELETE FROM accepted_resistance_training_state_daily")
            conn.execute("DELETE FROM gym_set")
            conn.execute("DELETE FROM gym_session")
        if has_nutrition_group:
            # Nutrition group: no FK between raw and accepted; both
            # truncated together so replay repopulates both.
            conn.execute("DELETE FROM accepted_nutrition_state_daily")
            conn.execute("DELETE FROM nutrition_intake_raw")
        if has_stress_group:
            # Stress group: only stress_manual_raw is owned outright.
            # accepted_recovery_state_daily.manual_stress_score is a
            # MERGED column — co-owned with the Garmin-clean flow. We
            # don't truncate accepted_recovery_state_daily here (would
            # wipe Garmin fields). Instead:
            #   1. Clear stress_manual_raw.
            #   2. Surgical hygiene: NULL out manual_stress_score on every
            #      accepted_recovery row + strip stress submission IDs from
            #      derived_from. Without this step a day previously logged
            #      via stress but absent from the new JSONL would keep its
            #      old manual_stress_score, breaking the "accepted derives
            #      from raw" invariant.
            #   3. Replay raw stress rows.
            #   4. Re-merge per touched (day, user) — UPDATE only the
            #      manual_stress_score column for days present in the new
            #      JSONL; days dropped from the JSONL stay NULL.
            conn.execute("DELETE FROM stress_manual_raw")
            stress_orphans = conn.execute(
                "SELECT as_of_date, user_id, derived_from, source, ingest_actor "
                "FROM accepted_recovery_state_daily "
                "WHERE manual_stress_score IS NOT NULL "
                "   OR derived_from LIKE '%\"m_stress_%'"
            ).fetchall()
            for row in stress_orphans:
                surviving_ids: list[str] = []
                if row["derived_from"]:
                    try:
                        parsed = json.loads(row["derived_from"])
                        if isinstance(parsed, list):
                            surviving_ids = [
                                str(x) for x in parsed
                                if not _is_stress_submission_id(str(x))
                            ]
                    except (TypeError, json.JSONDecodeError):
                        pass
                surviving_json = json.dumps(
                    sorted(set(surviving_ids)), sort_keys=True,
                )
                # If the surviving contributors include a garmin-shaped ID,
                # source/ingest_actor must reflect that — leaving them at
                # 'user_manual'/'hai_cli_direct' (set by the now-evicted
                # stress merge) would violate state_model_v1.md §4. If no
                # garmin survives either (degenerate stress-only row that's
                # now empty), leave source/ingest as-is — the row carries
                # no current evidence and a future write will overwrite.
                has_garmin_survivor = any(
                    not _is_intake_submission_id(rid)
                    for rid in surviving_ids
                )
                if has_garmin_survivor and (
                    row["source"] != "garmin"
                    or row["ingest_actor"] != "garmin_csv_adapter"
                ):
                    conn.execute(
                        "UPDATE accepted_recovery_state_daily SET "
                        "manual_stress_score = NULL, derived_from = ?, "
                        "source = 'garmin', "
                        "ingest_actor = 'garmin_csv_adapter' "
                        "WHERE as_of_date = ? AND user_id = ?",
                        (surviving_json,
                         row["as_of_date"], row["user_id"]),
                    )
                else:
                    conn.execute(
                        "UPDATE accepted_recovery_state_daily SET "
                        "manual_stress_score = NULL, derived_from = ? "
                        "WHERE as_of_date = ? AND user_id = ?",
                        (surviving_json,
                         row["as_of_date"], row["user_id"]),
                    )
        if has_notes_group:
            # Notes have no accepted layer (raw IS canonical).
            conn.execute("DELETE FROM context_note")

        if rec_log.exists():
            for line_no, line in enumerate(rec_log.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                data = json.loads(line)
                conn.execute(
                    """
                    INSERT INTO recommendation_log (
                        recommendation_id, user_id, for_date, issued_at,
                        action, confidence, bounded, payload_json,
                        jsonl_offset, source, ingest_actor, agent_version,
                        produced_at, validated_at, projected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["recommendation_id"],
                        data["user_id"],
                        data["for_date"],
                        data["issued_at"],
                        data["action"],
                        data["confidence"],
                        1 if data.get("bounded", True) else 0,
                        json.dumps(data, sort_keys=True),
                        line_no,
                        data.get("source", "claude_agent_v1"),
                        data.get("ingest_actor", "claude_agent_v1"),
                        data.get("agent_version"),
                        data.get("produced_at", data["issued_at"]),
                        data.get("validated_at", _now_iso()),
                        _now_iso(),
                    ),
                )
                counts["recommendations"] += 1

        if events_log.exists():
            for line_no, line in enumerate(events_log.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                data = json.loads(line)
                conn.execute(
                    """
                    INSERT INTO review_event (
                        review_event_id, recommendation_id, user_id,
                        review_at, review_question, domain, projected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["review_event_id"],
                        data["recommendation_id"],
                        data["user_id"],
                        data["review_at"],
                        data["review_question"],
                        data.get("domain", "recovery"),
                        _now_iso(),
                    ),
                )
                counts["review_events"] += 1

        if outcomes_log.exists():
            for line_no, line in enumerate(outcomes_log.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                data = json.loads(line)
                conn.execute(
                    """
                    INSERT INTO review_outcome (
                        review_event_id, recommendation_id, user_id, recorded_at,
                        followed_recommendation, self_reported_improvement, free_text,
                        domain, jsonl_offset, source, ingest_actor, projected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["review_event_id"],
                        data["recommendation_id"],
                        data["user_id"],
                        data["recorded_at"],
                        1 if data["followed_recommendation"] else 0,
                        _opt_bool_to_int(data.get("self_reported_improvement")),
                        data.get("free_text"),
                        data.get("domain", "recovery"),
                        line_no,
                        data.get("source", "user_manual"),
                        data.get("ingest_actor", "claude_agent_v1"),
                        _now_iso(),
                    ),
                )
                counts["review_outcomes"] += 1

        if gym_log.exists():
            # Each line is one set submission with session metadata inline.
            # Sessions: inserted once on first mention, subsequent lines
            # referencing the same session_id are no-ops. Sets are inserted
            # on their set_id (deterministic on session_id + set_number for
            # first-time logging; corrections carry supersedes_set_id).
            seen_sessions: set[str] = set()
            days_touched: set[tuple[str, str]] = set()
            for line_no, line in enumerate(
                gym_log.read_text(encoding="utf-8").splitlines(), start=1,
            ):
                if not line.strip():
                    continue
                data = json.loads(line)
                session_id = data["session_id"]
                user_id = data["user_id"]
                as_of_iso = data["as_of_date"]

                if session_id not in seen_sessions:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO gym_session (
                            session_id, user_id, as_of_date, session_name, notes,
                            source, ingest_actor, submission_id, ingested_at,
                            supersedes_session_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            session_id, user_id, as_of_iso,
                            data.get("session_name"), data.get("notes"),
                            data.get("source", "user_manual"),
                            data.get("ingest_actor", "claude_agent_v1"),
                            data.get("submission_id"),
                            data.get("submitted_at", _now_iso()),
                            None,
                        ),
                    )
                    seen_sessions.add(session_id)
                    counts["gym_sessions"] += 1

                set_id = f"set_{session_id}_{int(data['set_number']):03d}"
                # If the JSONL explicitly carries a non-deterministic set_id
                # (e.g., a correction row with supersedes_set_id), honour it.
                if data.get("set_id"):
                    set_id = data["set_id"]
                conn.execute(
                    """
                    INSERT OR IGNORE INTO gym_set (
                        set_id, session_id, set_number, exercise_name,
                        weight_kg, reps, rpe,
                        ingested_at, supersedes_set_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        set_id, session_id, int(data["set_number"]),
                        data["exercise_name"],
                        data.get("weight_kg"), data.get("reps"), data.get("rpe"),
                        data.get("submitted_at", _now_iso()),
                        data.get("supersedes_set_id"),
                    ),
                )
                counts["gym_sets"] += 1
                days_touched.add((as_of_iso, user_id))

            # Rebuild every touched day's accepted resistance-training row.
            from datetime import date as _date
            for as_of_iso, user_id in sorted(days_touched):
                # Inline the accepted-state recomputation; we can't call the
                # public helper here because it would call conn.commit()
                # mid-transaction (commit_after=True default). Defensive:
                # explicitly pass commit_after=False.
                project_accepted_resistance_training_state_daily(
                    conn,
                    as_of_date=_date.fromisoformat(as_of_iso),
                    user_id=user_id,
                    ingest_actor="hai_state_reproject",
                    source="user_manual",
                    commit_after=False,
                )
                counts["accepted_resistance_training_state_daily"] += 1

        if nutrition_log.exists():
            # Nutrition replay: each line is one submission. The natural
            # `ingested_at` order in the raw table follows the line order
            # here (reproject stamps fresh timestamps). The correction
            # chain is preserved by replaying `supersedes_submission_id`
            # exactly as stored in JSONL.
            days_touched: set[tuple[str, str]] = set()
            for line_no, line in enumerate(
                nutrition_log.read_text(encoding="utf-8").splitlines(), start=1,
            ):
                if not line.strip():
                    continue
                data = json.loads(line)
                as_of_iso = data["as_of_date"]
                user_id = data["user_id"]
                conn.execute(
                    """
                    INSERT OR IGNORE INTO nutrition_intake_raw (
                        submission_id, user_id, as_of_date,
                        calories, protein_g, carbs_g, fat_g,
                        hydration_l, meals_count,
                        source, ingest_actor, ingested_at,
                        supersedes_submission_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["submission_id"], user_id, as_of_iso,
                        data.get("calories"), data.get("protein_g"),
                        data.get("carbs_g"), data.get("fat_g"),
                        data.get("hydration_l"), data.get("meals_count"),
                        data.get("source", "user_manual"),
                        data.get("ingest_actor", "claude_agent_v1"),
                        data.get("submitted_at", _now_iso()),
                        data.get("supersedes_submission_id"),
                    ),
                )
                counts["nutrition_intake_raw"] += 1
                days_touched.add((as_of_iso, user_id))

            from datetime import date as _date
            for as_of_iso, user_id in sorted(days_touched):
                project_accepted_nutrition_state_daily(
                    conn,
                    as_of_date=_date.fromisoformat(as_of_iso),
                    user_id=user_id,
                    ingest_actor="hai_state_reproject",
                    source="user_manual",
                    commit_after=False,
                )
                counts["accepted_nutrition_state_daily"] += 1

        if stress_log.exists():
            stress_days_touched: set[tuple[str, str]] = set()
            for line_no, line in enumerate(
                stress_log.read_text(encoding="utf-8").splitlines(), start=1,
            ):
                if not line.strip():
                    continue
                data = json.loads(line)
                as_of_iso = data["as_of_date"]
                user_id = data["user_id"]
                tags_payload = data.get("tags")
                if isinstance(tags_payload, list):
                    tags_str = json.dumps(tags_payload, sort_keys=True)
                else:
                    tags_str = tags_payload  # already-stringified or None
                conn.execute(
                    """
                    INSERT OR IGNORE INTO stress_manual_raw (
                        submission_id, user_id, as_of_date,
                        score, tags,
                        source, ingest_actor, ingested_at,
                        supersedes_submission_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["submission_id"], user_id, as_of_iso,
                        int(data["score"]), tags_str,
                        data.get("source", "user_manual"),
                        data.get("ingest_actor", "claude_agent_v1"),
                        data.get("submitted_at", _now_iso()),
                        data.get("supersedes_submission_id"),
                    ),
                )
                counts["stress_manual_raw"] += 1
                stress_days_touched.add((as_of_iso, user_id))

            from datetime import date as _date
            for as_of_iso, user_id in sorted(stress_days_touched):
                merge_manual_stress_into_accepted_recovery(
                    conn,
                    as_of_date=_date.fromisoformat(as_of_iso),
                    user_id=user_id,
                    ingest_actor="hai_state_reproject",
                    commit_after=False,
                )
                counts["accepted_recovery_manual_stress_merged"] += 1

        if notes_log.exists():
            for line_no, line in enumerate(
                notes_log.read_text(encoding="utf-8").splitlines(), start=1,
            ):
                if not line.strip():
                    continue
                data = json.loads(line)
                tags_payload = data.get("tags")
                if isinstance(tags_payload, list):
                    tags_str = json.dumps(tags_payload, sort_keys=True)
                else:
                    tags_str = tags_payload
                conn.execute(
                    """
                    INSERT OR IGNORE INTO context_note (
                        note_id, user_id, as_of_date, recorded_at, text, tags,
                        source, ingest_actor, ingested_at, supersedes_note_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        data["note_id"], data["user_id"], data["as_of_date"],
                        data["recorded_at"], data["text"], tags_str,
                        data.get("source", "user_manual"),
                        data.get("ingest_actor", "claude_agent_v1"),
                        data.get("recorded_at", _now_iso()),
                        data.get("supersedes_note_id"),
                    ),
                )
                counts["context_notes"] += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return counts


# ---------------------------------------------------------------------------
# Proposal + DailyPlan + XRuleFiring projectors (Phase 2 step 4)
# ---------------------------------------------------------------------------

def project_proposal(
    conn: sqlite3.Connection,
    proposal: dict,
    *,
    source: str = "claude_agent_v1",
    ingest_actor: str = "claude_agent_v1",
    agent_version: Optional[str] = None,
    produced_at: Optional[datetime] = None,
    daily_plan_id: Optional[str] = None,
    commit_after: bool = True,
) -> bool:
    """Insert a ``DomainProposal``-shaped dict into ``proposal_log``.

    Idempotent on ``proposal_id``: re-running is a no-op and returns
    ``False``. First-time insert returns ``True``.

    ``daily_plan_id`` stays NULL until ``hai synthesize`` links it; the
    synthesis transaction updates the row separately.

    ``commit_after=False`` lets callers compose this write into a larger
    transaction (used by :mod:`health_agent_infra.core.synthesis` where
    proposal linking happens inside the same BEGIN/COMMIT as daily_plan
    + recommendation insertion).
    """

    existing = conn.execute(
        "SELECT 1 FROM proposal_log WHERE proposal_id = ?",
        (proposal["proposal_id"],),
    ).fetchone()
    if existing is not None:
        return False

    produced_iso = produced_at.isoformat() if produced_at is not None else _now_iso()

    conn.execute(
        """
        INSERT INTO proposal_log (
            proposal_id, daily_plan_id, user_id, domain, for_date,
            schema_version, action, confidence, payload_json,
            source, ingest_actor, agent_version,
            produced_at, validated_at, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            proposal["proposal_id"],
            daily_plan_id,
            proposal["user_id"],
            proposal["domain"],
            proposal["for_date"],
            proposal["schema_version"],
            proposal["action"],
            proposal["confidence"],
            json.dumps(proposal, sort_keys=True),
            source,
            ingest_actor,
            agent_version,
            produced_iso,
            _now_iso(),
            _now_iso(),
        ),
    )
    if commit_after:
        conn.commit()
    return True


def link_proposal_to_plan(
    conn: sqlite3.Connection,
    *,
    proposal_id: str,
    daily_plan_id: str,
    commit_after: bool = True,
) -> None:
    """Set ``proposal_log.daily_plan_id`` for a proposal after synthesis links it."""

    conn.execute(
        "UPDATE proposal_log SET daily_plan_id = ? WHERE proposal_id = ?",
        (daily_plan_id, proposal_id),
    )
    if commit_after:
        conn.commit()


def project_daily_plan(
    conn: sqlite3.Connection,
    plan: dict,
    *,
    source: str = "claude_agent_v1",
    ingest_actor: str = "claude_agent_v1",
    commit_after: bool = True,
) -> None:
    """Insert one ``DailyPlan``-shaped dict into ``daily_plan``.

    Not idempotent on ``daily_plan_id``; the synthesis transaction deletes
    a prior canonical plan before calling this for replacement semantics.
    """

    conn.execute(
        """
        INSERT INTO daily_plan (
            daily_plan_id, user_id, for_date, synthesized_at,
            recommendation_ids_json, proposal_ids_json, x_rules_fired_json,
            synthesis_meta_json,
            source, ingest_actor, agent_version,
            validated_at, projected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            plan["daily_plan_id"],
            plan["user_id"],
            plan["for_date"],
            plan["synthesized_at"],
            json.dumps(list(plan.get("recommendation_ids") or []), sort_keys=True),
            json.dumps(list(plan.get("proposal_ids") or []), sort_keys=True),
            json.dumps(list(plan.get("x_rules_fired") or []), sort_keys=True),
            json.dumps(plan.get("synthesis_meta"), sort_keys=True) if plan.get("synthesis_meta") is not None else None,
            source,
            ingest_actor,
            plan.get("agent_version"),
            _now_iso(),
            _now_iso(),
        ),
    )
    if commit_after:
        conn.commit()


def project_x_rule_firing(
    conn: sqlite3.Connection,
    firing: dict,
    *,
    daily_plan_id: str,
    user_id: str,
    commit_after: bool = True,
) -> int:
    """Insert one ``XRuleFiring`` (as dict) into ``x_rule_firing``.

    Returns the autogenerated ``firing_id``. Caller stamps ``daily_plan_id``
    + ``user_id`` because the firing dict itself doesn't carry plan linkage.
    """

    mutation = firing.get("recommended_mutation")
    signals = firing.get("source_signals") or {}

    cursor = conn.execute(
        """
        INSERT INTO x_rule_firing (
            daily_plan_id, user_id, x_rule_id, tier,
            affected_domain, trigger_note,
            mutation_json, source_signals_json, fired_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            daily_plan_id,
            user_id,
            firing["rule_id"],
            firing["tier"],
            firing["affected_domain"],
            firing["trigger_note"],
            json.dumps(mutation, sort_keys=True) if mutation is not None else None,
            json.dumps(signals, sort_keys=True),
            _now_iso(),
        ),
    )
    if commit_after:
        conn.commit()
    return int(cursor.lastrowid)


def project_bounded_recommendation(
    conn: sqlite3.Connection,
    recommendation: dict,
    *,
    source: str = "claude_agent_v1",
    ingest_actor: str = "claude_agent_v1",
    agent_version: Optional[str] = None,
    commit_after: bool = True,
) -> None:
    """Insert a ``BoundedRecommendation``-shaped dict into ``recommendation_log``.

    The legacy :func:`project_recommendation` takes a ``TrainingRecommendation``
    dataclass (recovery-only, no ``daily_plan_id`` / ``domain`` at the Python
    level). This helper writes the Phase 2 multi-domain shape straight from
    a dict, carrying ``domain`` + ``daily_plan_id`` columns on migration 003.

    Not idempotent — synthesis drives uniqueness by deleting prior rows for
    the canonical plan before inserting, so a second call with the same
    ``recommendation_id`` is a programming error.
    """

    conn.execute(
        """
        INSERT INTO recommendation_log (
            recommendation_id, user_id, for_date, issued_at,
            action, confidence, bounded, payload_json,
            jsonl_offset, source, ingest_actor, agent_version,
            produced_at, validated_at, projected_at, domain
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            recommendation["recommendation_id"],
            recommendation["user_id"],
            recommendation["for_date"],
            recommendation["issued_at"],
            recommendation["action"],
            recommendation["confidence"],
            1 if recommendation.get("bounded", True) else 0,
            json.dumps(recommendation, sort_keys=True),
            None,
            source,
            ingest_actor,
            agent_version,
            recommendation["issued_at"],
            _now_iso(),
            _now_iso(),
            recommendation.get("domain", "recovery"),
        ),
    )
    if commit_after:
        conn.commit()


def delete_canonical_plan_cascade(
    conn: sqlite3.Connection,
    *,
    daily_plan_id: str,
    commit_after: bool = True,
) -> None:
    """Delete an existing canonical plan and every row that references it.

    Order matters under foreign-key enforcement:
      1. ``x_rule_firing`` → references ``daily_plan`` (FK)
      2. ``recommendation_log`` → no FK to ``daily_plan`` but carries the
         id in ``payload_json``; deleted by explicit join
      3. ``daily_plan``
      4. Reset ``proposal_log.daily_plan_id`` on any rows that pointed here

    Callers compose this inside the synthesis BEGIN/COMMIT so either
    the whole replacement lands or nothing changes.
    """

    # Every recommendation we wrote for this plan has daily_plan_id baked
    # into its payload_json. We stored the linkage there; now reverse it
    # by pulling the ids out of the JSON blob.
    rec_rows = conn.execute(
        "SELECT recommendation_id, payload_json FROM recommendation_log "
        "WHERE json_extract(payload_json, '$.daily_plan_id') = ?",
        (daily_plan_id,),
    ).fetchall()
    for row in rec_rows:
        conn.execute(
            "DELETE FROM review_outcome WHERE recommendation_id = ?",
            (row["recommendation_id"],),
        )
        conn.execute(
            "DELETE FROM review_event WHERE recommendation_id = ?",
            (row["recommendation_id"],),
        )
        conn.execute(
            "DELETE FROM recommendation_log WHERE recommendation_id = ?",
            (row["recommendation_id"],),
        )

    conn.execute(
        "DELETE FROM x_rule_firing WHERE daily_plan_id = ?",
        (daily_plan_id,),
    )
    conn.execute(
        "DELETE FROM daily_plan WHERE daily_plan_id = ?",
        (daily_plan_id,),
    )
    conn.execute(
        "UPDATE proposal_log SET daily_plan_id = NULL WHERE daily_plan_id = ?",
        (daily_plan_id,),
    )

    if commit_after:
        conn.commit()


def mark_plan_superseded(
    conn: sqlite3.Connection,
    *,
    daily_plan_id: str,
    superseded_by: str,
    commit_after: bool = True,
) -> None:
    """Set ``daily_plan.superseded_by`` on a prior plan.

    Used by ``hai synthesize --supersede`` to flip the pointer on the
    prior canonical plan when intentionally versioning rather than
    atomically replacing.
    """

    conn.execute(
        "UPDATE daily_plan SET "
        "synthesis_meta_json = json_set(COALESCE(synthesis_meta_json, '{}'), "
        "'$.superseded_by', ?) "
        "WHERE daily_plan_id = ?",
        (superseded_by, daily_plan_id),
    )
    if commit_after:
        conn.commit()


def read_proposals_for_plan_key(
    conn: sqlite3.Connection,
    *,
    for_date: str,
    user_id: str,
) -> list[dict]:
    """Return all proposals in ``proposal_log`` for ``(for_date, user_id)``.

    Includes proposals not yet linked to any plan (``daily_plan_id``
    NULL) and proposals linked to a prior plan (non-NULL). Synthesis
    consumes the union — it re-links matching ones into the new plan.
    """

    rows = conn.execute(
        "SELECT payload_json FROM proposal_log "
        "WHERE for_date = ? AND user_id = ? "
        "ORDER BY domain, proposal_id",
        (for_date, user_id),
    ).fetchall()
    return [json.loads(r["payload_json"]) for r in rows]


def read_canonical_plan(
    conn: sqlite3.Connection,
    *,
    daily_plan_id: str,
) -> Optional[dict]:
    """Return the daily_plan row as a dict, or None if not found."""

    row = conn.execute(
        "SELECT * FROM daily_plan WHERE daily_plan_id = ?",
        (daily_plan_id,),
    ).fetchone()
    if row is None:
        return None
    return dict(row)
