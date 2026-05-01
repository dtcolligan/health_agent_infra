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

Phase 3 step 2 split recovery / sleep / stress accepted-state writers out
into per-domain modules under :mod:`health_agent_infra.core.state.projectors`.
This module now owns raw writers, recommendation / review / plan writers,
and the reproject orchestration; the per-domain functions are imported
back and re-exported so external callers (CLI, synthesis, tests, and the
``core.state`` package surface) continue to work unchanged.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime
from typing import Optional

from health_agent_infra.core.schemas import (
    ReviewEvent,
    ReviewOutcome,
)
from health_agent_infra.core.state.projectors._shared import (
    _bool_to_int,
    _is_intake_submission_id,
    _is_stress_submission_id,
    _now_iso,
    _opt_bool_to_int,
)
from health_agent_infra.core.state.projectors.recovery import (
    project_accepted_recovery_state_daily,
)
from health_agent_infra.core.state.projectors.sleep import (
    project_accepted_sleep_state_daily,
)
from health_agent_infra.core.state.projectors.stress import (
    merge_manual_stress_into_accepted_recovery,
    merge_manual_stress_into_accepted_stress,
    project_accepted_stress_state_daily,
)
from health_agent_infra.core.state.projectors.strength import (
    project_accepted_resistance_training_state_daily,
)
from health_agent_infra.core.state.projectors.running_activity import (
    aggregate_activities_to_daily_rollup,
    project_activity,
    read_activities_for_date,
    read_activities_range,
)
from health_agent_infra.domains.recovery.schemas import TrainingRecommendation

__all__ = [
    "ReprojectBaseDirError",
    "aggregate_activities_to_daily_rollup",
    "delete_canonical_plan_cascade",
    "latest_nutrition_submission_id",
    "link_proposal_to_plan",
    "mark_plan_superseded",
    "merge_manual_stress_into_accepted_recovery",
    "merge_manual_stress_into_accepted_stress",
    "project_accepted_nutrition_state_daily",
    "project_accepted_recovery_state_daily",
    "project_accepted_resistance_training_state_daily",
    "project_accepted_running_state_daily",
    "project_accepted_sleep_state_daily",
    "project_accepted_stress_state_daily",
    "project_activity",
    "project_bounded_recommendation",
    "project_context_note",
    "project_daily_plan",
    "project_gym_session",
    "project_gym_set",
    "project_manual_readiness_raw",
    "project_nutrition_intake_raw",
    "project_proposal",
    "project_recommendation",
    "project_review_event",
    "project_review_outcome",
    "project_source_daily_garmin",
    "project_stress_manual_raw",
    "project_x_rule_firing",
    "read_activities_for_date",
    "read_activities_range",
    "read_canonical_plan",
    "read_latest_manual_readiness",
    "read_proposals_for_plan_key",
    "reproject_from_jsonl",
]


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

    # M4 enrichment columns (migration 010). Every field is optional;
    # NULL means "not recorded" rather than any semantic default.
    # disagreed_firing_ids is JSON-encoded on write so the column can
    # stay a simple TEXT without a dedicated join table.
    disagreed_json = (
        json.dumps(list(outcome.disagreed_firing_ids))
        if outcome.disagreed_firing_ids is not None
        else None
    )
    cursor = conn.execute(
        """
        INSERT INTO review_outcome (
            review_event_id, recommendation_id, user_id, recorded_at,
            followed_recommendation, self_reported_improvement, free_text,
            domain, jsonl_offset, source, ingest_actor, projected_at,
            completed, intensity_delta, duration_minutes,
            pre_energy_score, post_energy_score, disagreed_firing_ids,
            re_linked_from_recommendation_id, re_link_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            _opt_bool_to_int(outcome.completed),
            outcome.intensity_delta,
            outcome.duration_minutes,
            outcome.pre_energy_score,
            outcome.post_energy_score,
            disagreed_json,
            outcome.re_linked_from_recommendation_id,
            outcome.re_link_note,
        ),
    )
    conn.commit()
    # F-A-11 fix per W-H1: lastrowid is Optional[int] in typeshed.
    last = cursor.lastrowid
    if last is None:
        raise RuntimeError("INSERT into review_outcome returned no rowid")
    return int(last)


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
        f"INSERT INTO source_daily_garmin ({columns_sql}) VALUES ({placeholders})",  # nosec B608 - columns_sql is built from the _SOURCE_DAILY_GARMIN_COLUMNS constant tuple; placeholders are literal "?" tokens.
        values,
    )
    if commit_after:
        conn.commit()
    return True


# ---------------------------------------------------------------------------
# Accepted recovery / sleep / stress state writers live in per-domain modules
# under core/state/projectors/. They are imported at the top of this file so
# existing call sites (CLI, synthesis, tests) continue to resolve them here.
# ---------------------------------------------------------------------------


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
    rollup: Optional[dict] = None,
) -> bool:
    """UPSERT one day's accepted running state with a derivation_path stamp.

    v0.1.11 W-R (Codex F-C-03 / F-CDX-IR-05): when a per-activity
    rollup is supplied (and carries non-None values for
    ``session_count`` / ``total_duration_s``), the projector stamps
    ``derivation_path='activity_rollup'`` and populates the formerly-
    NULL fields. Without a rollup (the legacy daily-aggregate path),
    behaviour matches v0.1.10: ``garmin_daily`` stamp, NULL session
    count + duration. The two paths are now distinguishable for
    audit + downstream consumers.

    The rollup shape comes from
    :func:`aggregate_activities_to_daily_rollup`; callers that don't
    have per-activity data (CSV adapter only) pass ``rollup=None``.

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

    # v0.1.11 W-R: choose derivation_path based on whether a rollup
    # supplied values the daily aggregate cannot. A rollup with a
    # populated session_count is the unambiguous "this row was
    # synthesised from per-activity data" signal.
    rollup_session_count = (
        rollup.get("session_count") if isinstance(rollup, dict) else None
    )
    rollup_total_duration_s = (
        rollup.get("total_duration_s") if isinstance(rollup, dict) else None
    )
    if rollup_session_count is not None:
        # The schema CHECK already reserves 'running_sessions' for the
        # per-session-derived path; reuse it rather than minting a new
        # value (which would require a CHECK-constraint migration).
        derivation_path = "running_sessions"
        session_count_value = rollup_session_count
        total_duration_value = rollup_total_duration_s
    else:
        derivation_path = "garmin_daily"
        session_count_value = None
        total_duration_value = None

    values = (
        raw_row.get("distance_m"),
        total_duration_value,
        raw_row.get("moderate_intensity_min"),
        raw_row.get("vigorous_intensity_min"),
        session_count_value,
        derivation_path,
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
    exercise_id: Optional[str] = None,
    supersedes_set_id: Optional[str] = None,
    commit_after: bool = True,
) -> bool:
    """Insert one gym_set. Idempotent on set_id (deterministic per session/number).

    Returns ``True`` on insert, ``False`` if the set_id already exists.
    Append-only raw grammar (state_model_v1.md §3): corrections pass a fresh
    set_id + ``supersedes_set_id`` pointing at the row being replaced.

    ``exercise_id`` is the best-effort taxonomy match stamped at intake
    time. NULL is legitimate when the intake surface cannot
    unambiguously resolve the free-text ``exercise_name`` against
    ``exercise_taxonomy``; the strength projector then re-resolves by
    name on every projection, so a NULL stamp does not starve
    downstream aggregates.
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
            ingested_at, supersedes_set_id, exercise_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            set_id, session_id, set_number, exercise_name,
            weight_kg, reps, rpe,
            _now_iso(), supersedes_set_id, exercise_id,
        ),
    )
    if commit_after:
        conn.commit()
    return True


def project_exercise_taxonomy_entry(
    conn: sqlite3.Connection,
    *,
    exercise_id: str,
    canonical_name: str,
    aliases: Optional[str],
    primary_muscle_group: str,
    secondary_muscle_groups: Optional[str],
    category: str,
    equipment: str,
    source: str = "user_manual",
    commit_after: bool = True,
) -> bool:
    """Insert one user-defined ``exercise_taxonomy`` row.

    Idempotent on the full row shape: re-submitting the exact same
    ``exercise_id`` / ``canonical_name`` / metadata tuple returns ``False``.
    Conflicting reuse of an existing id or canonical name raises
    ``sqlite3.IntegrityError`` so the CLI can fail loudly instead of
    silently mutating taxonomy rows.
    """

    def _fetch_by(field: str, value: str) -> Optional[sqlite3.Row]:
        # nosec B608 - field is whitelisted by the two literal call sites
        # below (`exercise_id`, `canonical_name`); user value binds via param.
        return conn.execute(
            f"""
            SELECT exercise_id, canonical_name, aliases,
                   primary_muscle_group, secondary_muscle_groups,
                   category, equipment, source
            FROM exercise_taxonomy
            WHERE {field} = ?
            """,  # nosec B608
            (value,),
        ).fetchone()

    by_id = _fetch_by("exercise_id", exercise_id)
    by_name = _fetch_by("canonical_name", canonical_name)

    if by_id is not None and by_name is not None and by_id["exercise_id"] != by_name["exercise_id"]:
        raise sqlite3.IntegrityError(
            "exercise taxonomy conflict: exercise_id and canonical_name map to different rows"
        )

    existing = by_id or by_name
    desired = {
        "exercise_id": exercise_id,
        "canonical_name": canonical_name,
        "aliases": aliases,
        "primary_muscle_group": primary_muscle_group,
        "secondary_muscle_groups": secondary_muscle_groups,
        "category": category,
        "equipment": equipment,
        "source": source,
    }

    if existing is not None:
        current = {
            "exercise_id": existing["exercise_id"],
            "canonical_name": existing["canonical_name"],
            "aliases": existing["aliases"],
            "primary_muscle_group": existing["primary_muscle_group"],
            "secondary_muscle_groups": existing["secondary_muscle_groups"],
            "category": existing["category"],
            "equipment": existing["equipment"],
            "source": existing["source"],
        }
        if current == desired:
            return False
        conflict_field = "exercise_id" if by_id is not None else "canonical_name"
        raise sqlite3.IntegrityError(
            f"exercise taxonomy conflict on existing {conflict_field}={desired[conflict_field]!r}"
        )

    conn.execute(
        """
        INSERT INTO exercise_taxonomy (
            exercise_id, canonical_name, aliases,
            primary_muscle_group, secondary_muscle_groups,
            category, equipment, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            exercise_id, canonical_name, aliases,
            primary_muscle_group, secondary_muscle_groups,
            category, equipment, source,
        ),
    )
    if commit_after:
        conn.commit()
    return True


# Accepted resistance-training projection moved to
# :mod:`health_agent_infra.core.state.projectors.strength` in Phase 4
# step 2. The orchestrator re-exports it via the top-level imports so
# existing callers (CLI, synthesis, reproject, tests) keep working
# unchanged.


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

    # Phase 5 step 1: v1 is macros-only. derivation_path is the marker
    # that separates today's pass-through aggregate from a future meal-log
    # derivation. Writer-side invariant: v1 only ever writes 'daily_macros'.
    derivation_path = "daily_macros"

    values = (
        latest["calories"], latest["protein_g"],
        latest["carbs_g"], latest["fat_g"],
        latest["hydration_l"], latest["meals_count"],
        derived_from_json, source, ingest_actor,
        now_iso,
        None if is_insert else now_iso,
        derivation_path,
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
                derivation_path,
                as_of_date, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                projected_at = ?, corrected_at = ?,
                derivation_path = ?
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


# ---------------------------------------------------------------------------
# merge_manual_stress_into_accepted_stress lives in
# ``core/state/projectors/stress.py`` alongside
# ``project_accepted_stress_state_daily``. The legacy alias
# ``merge_manual_stress_into_accepted_recovery`` is defined next to the real
# function and re-exported at the top of this module.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Manual readiness intake -> manual_readiness_raw (migration 015)
# ---------------------------------------------------------------------------


def project_manual_readiness_raw(
    conn: sqlite3.Connection,
    *,
    submission_id: str,
    user_id: str,
    as_of_date: date,
    soreness: str,
    energy: str,
    planned_session_type: str,
    active_goal: Optional[str],
    ingest_actor: str,
    supersedes_submission_id: Optional[str] = None,
    source: str = "user_manual",
    commit_after: bool = True,
) -> bool:
    """Append-only insert into ``manual_readiness_raw`` (D2 + migration 015).

    Idempotent on ``submission_id``: re-inserting the same id is a no-op
    (returns False). Same-day correction goes through a NEW submission id
    with ``supersedes_submission_id`` set; caller resolves the prior tail
    before invoking.

    CHECK constraints on soreness/energy enforce ``low|moderate|high``;
    invalid bands raise ``sqlite3.IntegrityError`` rather than silently
    persisting.
    """

    existing = conn.execute(
        "SELECT 1 FROM manual_readiness_raw WHERE submission_id = ?",
        (submission_id,),
    ).fetchone()
    if existing is not None:
        return False

    conn.execute(
        """
        INSERT INTO manual_readiness_raw (
            submission_id, user_id, as_of_date,
            soreness, energy, planned_session_type, active_goal,
            source, ingest_actor, ingested_at,
            supersedes_submission_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            submission_id, user_id, as_of_date.isoformat(),
            soreness, energy, planned_session_type, active_goal,
            source, ingest_actor, _now_iso(),
            supersedes_submission_id,
        ),
    )
    if commit_after:
        conn.commit()
    return True


def read_latest_manual_readiness(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    as_of_date: date,
) -> Optional[dict]:
    """Return the canonical (non-superseded) readiness row for ``(user, day)``.

    Used by ``hai pull`` to auto-read same-day readiness when no
    ``--manual-readiness-json`` override is passed (D2 §pull adapter
    integration). Returns ``None`` when no row exists, when every row
    for the day has been superseded (shouldn't happen in practice but
    treated honestly), or when the table itself predates migration 015.

    The "non-superseded leaf" selector uses a LEFT JOIN on
    ``supersedes_submission_id`` — the tail of the chain is the row
    whose ``submission_id`` no other row lists as its prior.
    """

    try:
        row = conn.execute(
            """
            SELECT r.submission_id, r.user_id, r.as_of_date,
                   r.soreness, r.energy, r.planned_session_type,
                   r.active_goal, r.ingested_at
            FROM manual_readiness_raw r
            LEFT JOIN manual_readiness_raw s
              ON s.supersedes_submission_id = r.submission_id
            WHERE r.user_id = ? AND r.as_of_date = ?
              AND s.submission_id IS NULL
            ORDER BY r.ingested_at DESC
            LIMIT 1
            """,
            (user_id, as_of_date.isoformat()),
        ).fetchone()
    except sqlite3.OperationalError:
        # Pre-migration-015 DB: no table yet. Treat as "nothing persisted."
        return None

    if row is None:
        return None

    payload = {
        "submission_id": row["submission_id"],
        "soreness": row["soreness"],
        "energy": row["energy"],
        "planned_session_type": row["planned_session_type"],
    }
    if row["active_goal"]:
        payload["active_goal"] = row["active_goal"]
    return payload


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


class ReprojectOrphansError(Exception):
    """Raised when reproject would orphan synthesis-side rows that are
    NOT JSONL-derived.

    Background (v0.1.6 W1 / B5): ``planned_recommendation.proposal_id``
    references ``proposal_log(proposal_id)`` (migration 011). The
    reproject's recommendation-group + proposals-group deletes don't
    cascade into ``planned_recommendation`` / ``daily_plan`` /
    ``x_rule_firing`` (those tables are computed by ``hai synthesize``,
    not by JSONL replay), so a naive truncate raises
    ``sqlite3.IntegrityError`` mid-transaction. Rather than crash, the
    reproject detects this BEFORE any destructive write and raises
    this exception with a message naming the row counts and the opt-in
    flag.

    Callers who genuinely want to wipe synthesis-side state and replay
    from JSONL pass ``cascade_synthesis=True`` (CLI:
    ``--cascade-synthesis``). They will need to re-run
    ``hai synthesize`` afterwards because the runtime cannot
    reconstruct ``daily_plan`` / ``x_rule_firing`` /
    ``planned_recommendation`` from JSONL alone — those tables are
    Phase A + Phase B outputs of the synthesis transaction.
    """


def reproject_from_jsonl(
    conn: sqlite3.Connection, base_dir, *,
    allow_empty: bool = False,
    cascade_synthesis: bool = False,
) -> dict:
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
    readiness_log = base / "readiness_manual.jsonl"

    # Phase B (v0.1.4): proposal JSONLs land per-domain. Without this group
    # the agent's `<domain>_proposals.jsonl` audit logs are decorative —
    # rebuilding the DB never restores proposal_log. Codex flagged this as
    # P1 #2 in the 2026-04-24 strategic report.
    proposal_logs = {
        domain: base / f"{domain}_proposals.jsonl"
        for domain in (
            "recovery", "running", "sleep", "strength", "stress", "nutrition",
        )
    }

    has_rec_group = any(p.exists() for p in (rec_log, events_log, outcomes_log))
    has_gym_group = gym_log.exists()
    has_nutrition_group = nutrition_log.exists()
    has_stress_group = stress_log.exists()
    has_notes_group = notes_log.exists()
    has_readiness_group = readiness_log.exists()
    has_proposals_group = any(p.exists() for p in proposal_logs.values())

    if not allow_empty and not (
        has_rec_group or has_gym_group or has_nutrition_group
        or has_stress_group or has_notes_group or has_readiness_group
        or has_proposals_group
    ):
        raise ReprojectBaseDirError(
            f"no audit JSONL files found under {base}. Expected at least "
            f"one of: recommendation_log.jsonl, review_events.jsonl, "
            f"review_outcomes.jsonl, gym_sessions.jsonl, "
            f"nutrition_intake.jsonl, stress_manual.jsonl, "
            f"context_notes.jsonl, readiness_manual.jsonl, "
            f"<domain>_proposals.jsonl. Refusing to "
            f"touch the projection tables. Pass allow_empty=True / "
            f"--allow-empty-reproject to override."
        )

    counts = {
        "recommendations": 0, "review_events": 0, "review_outcomes": 0,
        "gym_sessions": 0, "gym_sets": 0,
        "accepted_resistance_training_state_daily": 0,
        "nutrition_intake_raw": 0,
        "accepted_nutrition_state_daily": 0,
        "stress_manual_raw": 0,
        "accepted_stress_manual_merged": 0,
        "context_notes": 0,
        "manual_readiness_raw": 0,
        "proposals": 0,
        "proposals_skipped_invalid": 0,
    }

    conn.execute("BEGIN EXCLUSIVE")
    try:
        # v0.1.6 (W1 / B5): orphan-prevention before any destructive
        # delete. planned_recommendation FK references both proposal_log
        # (migration 011) and daily_plan; x_rule_firing FK references
        # daily_plan (migration 003). If the recommendation or proposals
        # group is being rebuilt while those synthesis-side tables are
        # populated, the destructive DELETEs trip
        # `sqlite3.IntegrityError: FOREIGN KEY constraint failed`
        # mid-transaction. Detect that BEFORE damage and either raise
        # ReprojectOrphansError (default) or sweep the synthesis tables
        # in dependency order (cascade_synthesis=True).
        if has_rec_group or has_proposals_group:
            synth_counts = {
                "planned_recommendation": conn.execute(
                    "SELECT COUNT(*) FROM planned_recommendation"
                ).fetchone()[0],
                "daily_plan": conn.execute(
                    "SELECT COUNT(*) FROM daily_plan"
                ).fetchone()[0],
                "x_rule_firing": conn.execute(
                    "SELECT COUNT(*) FROM x_rule_firing"
                ).fetchone()[0],
            }
            if any(synth_counts.values()):
                if not cascade_synthesis:
                    conn.execute("ROLLBACK")
                    raise ReprojectOrphansError(
                        f"reproject would orphan synthesis-side rows "
                        f"(planned_recommendation="
                        f"{synth_counts['planned_recommendation']}, "
                        f"daily_plan={synth_counts['daily_plan']}, "
                        f"x_rule_firing={synth_counts['x_rule_firing']}). "
                        f"These tables are NOT JSONL-derived — they're "
                        f"computed by `hai synthesize`. Two options: "
                        f"(a) if you only intended to refresh "
                        f"accepted_*_state tables, you don't need "
                        f"reproject — the intake commands project "
                        f"incrementally; (b) if you do want a full "
                        f"rebuild, pass --cascade-synthesis to delete "
                        f"the synthesis tables, then re-run "
                        f"`hai synthesize` afterwards to repopulate them."
                    )
                # Cascade: delete in dependency order. planned_recommendation
                # FKs into proposal_log + daily_plan; x_rule_firing FKs into
                # daily_plan. Delete the FK-bearers first; daily_plan is
                # cleared inside the rec_group block below.
                conn.execute("DELETE FROM planned_recommendation")
                conn.execute("DELETE FROM x_rule_firing")
        if has_rec_group:
            # Recommendation group: outcomes FK -> events FK -> recs. Delete
            # in reverse dependency order, then replay in forward order.
            conn.execute("DELETE FROM review_outcome")
            conn.execute("DELETE FROM review_event")
            conn.execute("DELETE FROM recommendation_log")
            if cascade_synthesis:
                # daily_plan is computed by `hai synthesize`, not from
                # JSONL. After cascade-cleanup of planned_recommendation
                # + x_rule_firing above, daily_plan has no inbound FKs
                # and can be safely cleared.
                conn.execute("DELETE FROM daily_plan")
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
        if has_readiness_group:
            # Readiness group: raw-only (no accepted layer to hygiene —
            # readiness feeds into hai pull's manual_readiness block, not
            # into a persisted accepted_readiness_state_daily). Simple
            # truncate + replay mirrors the clean-projector semantics.
            try:
                conn.execute("DELETE FROM manual_readiness_raw")
            except sqlite3.OperationalError:
                # DB predates migration 015; skip silently — nothing to
                # rebuild and the JSONL remains the audit boundary.
                pass
        if has_proposals_group:
            # Proposals group (Phase B): rebuild proposal_log from the
            # 6 per-domain JSONL audit logs.
            #
            # FK note: planned_recommendation.proposal_id REFERENCES
            # proposal_log(proposal_id) (migration 011). The
            # orphan-prevention block at the top of the transaction
            # has already deleted planned_recommendation when
            # cascade_synthesis=True, OR refused the reproject when
            # synthesis-side rows would be stranded — so by the time
            # we reach this DELETE, proposal_log has no live FK
            # children blocking the truncate.
            #
            # Note: a fresh reproject also resets daily_plan.proposal_ids_json
            # references logically — they remain in the JSON blob but won't
            # join to the new proposal_log unless the proposal_ids replay
            # produces the same chain (which it does for non-revised
            # chains). daily_plan itself is NOT rebuilt by reproject —
            # only by `hai synthesize`. Operators rebuilding the full
            # DB with --cascade-synthesis must rerun synthesis afterwards.
            conn.execute("DELETE FROM proposal_log")
        if has_stress_group:
            # Stress group (post-Phase-3): manual_stress_score now lives
            # on accepted_stress_state_daily, which is co-owned with the
            # Garmin-clean flow (garmin_all_day_stress +
            # body_battery_end_of_day come from clean). We can't truncate
            # accepted_stress_state_daily here — that would wipe Garmin
            # fields. Instead:
            #   1. Clear stress_manual_raw.
            #   2. Surgical hygiene: NULL out manual_stress_score +
            #      stress_tags_json on every accepted_stress row and
            #      strip stress submission IDs from derived_from. Without
            #      this step a day previously logged via stress but absent
            #      from the new JSONL would keep its old manual score,
            #      breaking the "accepted derives from raw" invariant.
            #   3. Replay raw stress rows.
            #   4. Re-merge per touched (day, user) — UPDATE only the
            #      manual fields for days present in the new JSONL; days
            #      dropped from the JSONL stay NULL.
            conn.execute("DELETE FROM stress_manual_raw")
            stress_orphans = conn.execute(
                "SELECT as_of_date, user_id, derived_from, source, ingest_actor "
                "FROM accepted_stress_state_daily "
                "WHERE manual_stress_score IS NOT NULL "
                "   OR stress_tags_json IS NOT NULL "
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
                # Provenance recovery: if a Garmin contributor remains in
                # derived_from but source/ingest_actor got flipped to the
                # manual dimension by a prior merge, restore them so the
                # row's provenance matches what's actually contributing
                # (state_model_v1.md §4). If no Garmin survives, leave
                # provenance as-is — the row carries no current evidence.
                has_garmin_survivor = any(
                    not _is_intake_submission_id(rid)
                    for rid in surviving_ids
                )
                if has_garmin_survivor and (
                    row["source"] != "garmin"
                    or row["ingest_actor"] != "garmin_csv_adapter"
                ):
                    conn.execute(
                        "UPDATE accepted_stress_state_daily SET "
                        "manual_stress_score = NULL, stress_tags_json = NULL, "
                        "derived_from = ?, "
                        "source = 'garmin', "
                        "ingest_actor = 'garmin_csv_adapter' "
                        "WHERE as_of_date = ? AND user_id = ?",
                        (surviving_json,
                         row["as_of_date"], row["user_id"]),
                    )
                else:
                    conn.execute(
                        "UPDATE accepted_stress_state_daily SET "
                        "manual_stress_score = NULL, stress_tags_json = NULL, "
                        "derived_from = ? "
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
                # v0.1.14 W-PROV-1: evidence_locators_json column.
                # JSONL rows pre-W-PROV-1 won't carry locators; .get
                # returns None and the column stays NULL.
                from health_agent_infra.core.provenance.locator import (
                    serialize_locators as _serialize_locators_jsonl,
                )
                _locators_payload = data.get("evidence_locators")
                _locators_json = (
                    _serialize_locators_jsonl(_locators_payload)
                    if _locators_payload
                    else None
                )
                conn.execute(
                    """
                    INSERT INTO recommendation_log (
                        recommendation_id, user_id, for_date, issued_at,
                        action, confidence, bounded, payload_json,
                        jsonl_offset, source, ingest_actor, agent_version,
                        produced_at, validated_at, projected_at,
                        daily_plan_id, evidence_locators_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        # JSONL rows predating M3 simply won't carry a
                        # daily_plan_id; .get returns None and the
                        # column stays NULL, matching the backfill's
                        # pre-M3 semantics.
                        data.get("daily_plan_id"),
                        _locators_json,
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
                        domain, jsonl_offset, source, ingest_actor, projected_at,
                        re_linked_from_recommendation_id, re_link_note
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        data.get("re_linked_from_recommendation_id"),
                        data.get("re_link_note"),
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
            # (Re-uses the days_touched name from the gym branch above;
            # mypy F-A-04 fix v0.1.12 W-H2: drop the redundant annotation
            # — same shape as line 1562.)
            days_touched = set()
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
                merge_manual_stress_into_accepted_stress(
                    conn,
                    as_of_date=_date.fromisoformat(as_of_iso),
                    user_id=user_id,
                    ingest_actor="hai_state_reproject",
                    commit_after=False,
                )
                counts["accepted_stress_manual_merged"] += 1

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

        if readiness_log.exists():
            # Readiness replay: raw-only replay. No accepted layer, no
            # merge step — ``hai pull`` auto-reads this table live per
            # D2, so the replay just has to reconstruct the raw rows.
            # Skipped quietly on pre-015 DBs (truncation above also
            # swallowed the OperationalError).
            for line_no, line in enumerate(
                readiness_log.read_text(encoding="utf-8").splitlines(), start=1,
            ):
                if not line.strip():
                    continue
                data = json.loads(line)
                try:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO manual_readiness_raw (
                            submission_id, user_id, as_of_date,
                            soreness, energy, planned_session_type, active_goal,
                            source, ingest_actor, ingested_at,
                            supersedes_submission_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            data["submission_id"], data["user_id"], data["as_of_date"],
                            data["soreness"], data["energy"],
                            data["planned_session_type"], data.get("active_goal"),
                            data.get("source", "user_manual"),
                            data.get("ingest_actor", "claude_agent_v1"),
                            data.get("submitted_at", _now_iso()),
                            data.get("supersedes_submission_id"),
                        ),
                    )
                except sqlite3.OperationalError:
                    # DB predates migration 015 — nothing to do.
                    break
                counts["manual_readiness_raw"] += 1

        if has_proposals_group:
            # Replay each domain's proposal JSONL in append order. The
            # JSONL preserves the agent's authoring sequence, so re-running
            # `project_proposal(replace=True)` per line correctly rebuilds
            # the D1 revision chain: first line on each chain key inserts
            # at revision=1; subsequent lines on the same chain key insert
            # at revision+1 with auto-generated proposal_id, and update the
            # prior leaf's `superseded_by_proposal_id` forward pointer.
            #
            # Validation: every line is parsed via `validate_proposal_dict`
            # before insertion. A line that fails validation is COUNTED as
            # skipped (not raised) so a single corrupt line in a long log
            # doesn't abort the whole reproject. Operators can grep the
            # final counts to confirm `proposals_skipped_invalid == 0` for
            # a clean restore.
            from health_agent_infra.core.writeback.proposal import (
                ProposalValidationError,
                validate_proposal_dict,
            )
            for domain in (
                "recovery", "running", "sleep",
                "strength", "stress", "nutrition",
            ):
                jsonl_path = proposal_logs[domain]
                if not jsonl_path.exists():
                    continue
                with jsonl_path.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            counts["proposals_skipped_invalid"] += 1
                            continue
                        try:
                            validate_proposal_dict(data, expected_domain=domain)
                        except ProposalValidationError:
                            counts["proposals_skipped_invalid"] += 1
                            continue
                        try:
                            project_proposal(
                                conn, data, replace=True, commit_after=False,
                            )
                        except ProposalReplaceRequired:
                            # Cannot happen — replace=True is the explicit
                            # override. Treated as defensive guard only.
                            counts["proposals_skipped_invalid"] += 1
                            continue
                        counts["proposals"] += 1

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return counts


# ---------------------------------------------------------------------------
# Proposal + DailyPlan + XRuleFiring projectors (Phase 2 step 4)
# ---------------------------------------------------------------------------

class ProposalReplaceRequired(ValueError):
    """Raised when a proposal is posted for a ``(for_date, user_id, domain)``
    chain that already has a canonical leaf and ``replace=False``.

    Per D1 (``reporting/plans/v0_1_4/D1_re_author_semantics.md``), silent
    skip on duplicate is the correctness hole that lets agent re-authoring
    disappear. The replacement is an explicit, loud rejection that the
    CLI surfaces as exit code ``USER_INPUT``.
    """

    def __init__(
        self,
        *,
        for_date: str,
        user_id: str,
        domain: str,
        leaf_proposal_id: str,
        leaf_revision: int,
    ) -> None:
        super().__init__(
            f"existing canonical proposal {leaf_proposal_id!r} "
            f"(revision {leaf_revision}) for ({for_date}, {user_id}, {domain}); "
            f"use --replace to revise."
        )
        self.for_date = for_date
        self.user_id = user_id
        self.domain = domain
        self.leaf_proposal_id = leaf_proposal_id
        self.leaf_revision = leaf_revision


# Fields that are runtime-assigned on each revision and therefore must be
# stripped before comparing two payloads for semantic equality. Preserves
# the "identical payload is a no-op under --replace" contract in D1 §
# Idempotency under identical replay.
_REVISION_VOLATILE_FIELDS: frozenset[str] = frozenset({"proposal_id"})


def _canonical_payload_bytes(payload: dict | str) -> bytes:
    """Canonicalise a proposal payload for semantic-equality comparison.

    Accepts either a dict (freshly authored) or the JSON string stored
    in ``payload_json``. Sorts keys, strips runtime-assigned fields
    (``proposal_id`` changes per revision), and returns UTF-8 bytes.
    """
    if isinstance(payload, str):
        data = json.loads(payload)
    else:
        data = dict(payload)
    for field in _REVISION_VOLATILE_FIELDS:
        data.pop(field, None)
    return json.dumps(data, sort_keys=True).encode("utf-8")


def _resolve_canonical_leaf(
    conn: sqlite3.Connection,
    *,
    for_date: str,
    user_id: str,
    domain: str,
) -> Optional[dict]:
    """Return the canonical leaf row for a ``(for_date, user_id, domain)``
    chain, or ``None`` if no proposal exists yet.

    Canonical leaf = ``superseded_by_proposal_id IS NULL``.
    """
    row = conn.execute(
        "SELECT proposal_id, revision, payload_json "
        "FROM proposal_log "
        "WHERE for_date = ? AND user_id = ? AND domain = ? "
        "AND superseded_by_proposal_id IS NULL",
        (for_date, user_id, domain),
    ).fetchone()
    if row is None:
        return None
    # sqlite3.Row supports both int-index and name access; normalise.
    return {
        "proposal_id": row["proposal_id"],
        "revision": row["revision"],
        "payload_json": row["payload_json"],
    }


def _insert_proposal_row(
    conn: sqlite3.Connection,
    proposal: dict,
    *,
    revision: int,
    source: str,
    ingest_actor: str,
    agent_version: Optional[str],
    produced_at: Optional[datetime],
    daily_plan_id: Optional[str],
    initial_superseded_by: Optional[str] = None,
) -> None:
    """Single INSERT into proposal_log for a proposal at given revision.

    Does not commit; caller owns transaction boundary. The revision
    chain bookkeeping (superseded_by pointer updates) is done by the
    caller where relevant.

    ``initial_superseded_by`` lets the revision flow seed the row with
    a self-pointer so the migration 018 partial unique index doesn't
    transiently see two canonical leaves during a multi-step revision
    update. Defaults to None for fresh-chain inserts (revision=1).
    """
    produced_iso = (
        produced_at.isoformat() if produced_at is not None else _now_iso()
    )
    superseded_at_initial = (
        _now_iso() if initial_superseded_by is not None else None
    )
    conn.execute(
        """
        INSERT INTO proposal_log (
            proposal_id, daily_plan_id, user_id, domain, for_date,
            schema_version, action, confidence, payload_json,
            source, ingest_actor, agent_version,
            produced_at, validated_at, projected_at,
            revision, superseded_by_proposal_id, superseded_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            revision,
            initial_superseded_by,
            superseded_at_initial,
        ),
    )


def project_proposal(
    conn: sqlite3.Connection,
    proposal: dict,
    *,
    source: str = "claude_agent_v1",
    ingest_actor: str = "claude_agent_v1",
    agent_version: Optional[str] = None,
    produced_at: Optional[datetime] = None,
    daily_plan_id: Optional[str] = None,
    replace: bool = False,
    commit_after: bool = True,
) -> bool:
    """Insert or revise a ``DomainProposal``-shaped dict in ``proposal_log``.

    Per D1 (``reporting/plans/v0_1_4/D1_re_author_semantics.md``):

    - No existing canonical leaf for ``(for_date, user_id, domain)`` →
      INSERT as revision=1, agent-authored ``proposal_id`` preserved.
      Return ``True``.
    - Existing canonical leaf, ``replace=False`` → raise
      :class:`ProposalReplaceRequired`. No DB changes.
    - Existing canonical leaf, ``replace=True``, payload semantically
      identical to the leaf (``_canonical_payload_bytes`` equal) →
      no-op, return ``False``. Preserves identical-replay idempotency.
    - Existing canonical leaf, ``replace=True``, payload differs →
      assign runtime proposal_id
      ``prop_<for_date>_<user_id>_<domain>_<revision:02d>`` at
      ``revision = leaf.revision + 1``, INSERT the new leaf, UPDATE
      the old leaf's ``superseded_by_proposal_id`` forward pointer.
      Both writes happen in the caller's transaction (``commit_after``
      controls the COMMIT).

    ``daily_plan_id`` stays NULL until ``hai synthesize`` links it;
    the synthesis transaction updates the row separately. Under D1,
    synthesis does **not** relink proposals on supersede — the leaf's
    link to its original plan is preserved; the new plan references
    proposals via ``proposal_ids_json``.
    """
    for_date = proposal["for_date"]
    user_id = proposal["user_id"]
    domain = proposal["domain"]

    leaf = _resolve_canonical_leaf(
        conn, for_date=for_date, user_id=user_id, domain=domain,
    )

    if leaf is None:
        # Fresh chain: revision=1, agent-authored proposal_id preserved.
        _insert_proposal_row(
            conn,
            proposal,
            revision=1,
            source=source,
            ingest_actor=ingest_actor,
            agent_version=agent_version,
            produced_at=produced_at,
            daily_plan_id=daily_plan_id,
        )
        if commit_after:
            conn.commit()
        return True

    if not replace:
        raise ProposalReplaceRequired(
            for_date=for_date,
            user_id=user_id,
            domain=domain,
            leaf_proposal_id=leaf["proposal_id"],
            leaf_revision=leaf["revision"],
        )

    # Replace path. First check semantic equality — identical replay
    # must not pollute the revision chain.
    if _canonical_payload_bytes(proposal) == _canonical_payload_bytes(
        leaf["payload_json"]
    ):
        if commit_after:
            conn.commit()
        return False

    # Real revision: assign the new proposal_id, link the chain forward,
    # then mark the new row as canonical leaf. The three-step ordering
    # below preserves migration 018's partial unique index invariant
    # (at most one canonical leaf per chain key) at every point in the
    # transaction:
    #
    #   1. INSERT new row with ``superseded_by = new_proposal_id`` (self-
    #      reference) — the row is committed but NOT a canonical leaf
    #      because superseded_by IS NOT NULL. Index ignores it.
    #   2. UPDATE old leaf's ``superseded_by`` to point at the new row.
    #      Old row stops being a canonical leaf (NOT NULL). Index OK
    #      with zero canonical leaves at this moment.
    #   3. UPDATE new row's ``superseded_by`` back to NULL. Now it IS the
    #      canonical leaf. Index OK with exactly one.
    #
    # An INSERT-then-UPDATE order without the self-pointer would trip
    # the partial index in step 1 (two NULL rows momentarily exist).
    new_revision = leaf["revision"] + 1
    new_proposal_id = (
        f"prop_{for_date}_{user_id}_{domain}_{new_revision:02d}"
    )
    proposal_for_new_leaf = dict(proposal, proposal_id=new_proposal_id)

    _insert_proposal_row(
        conn,
        proposal_for_new_leaf,
        revision=new_revision,
        source=source,
        ingest_actor=ingest_actor,
        agent_version=agent_version,
        produced_at=produced_at,
        daily_plan_id=daily_plan_id,
        initial_superseded_by=new_proposal_id,
    )
    conn.execute(
        "UPDATE proposal_log SET "
        "superseded_by_proposal_id = ?, superseded_at = ? "
        "WHERE proposal_id = ?",
        (new_proposal_id, _now_iso(), leaf["proposal_id"]),
    )
    conn.execute(
        "UPDATE proposal_log SET "
        "superseded_by_proposal_id = NULL, superseded_at = NULL "
        "WHERE proposal_id = ?",
        (new_proposal_id,),
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

    # v0.1.11 W-E: state_fingerprint column added in migration 022.
    # Allows run_synthesis to detect re-runs against unchanged state
    # and no-op rather than minting a fresh plan id with byte-
    # identical content.
    conn.execute(
        """
        INSERT INTO daily_plan (
            daily_plan_id, user_id, for_date, synthesized_at,
            recommendation_ids_json, proposal_ids_json, x_rules_fired_json,
            synthesis_meta_json,
            source, ingest_actor, agent_version,
            validated_at, projected_at,
            state_fingerprint
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            plan.get("state_fingerprint"),
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
    orphan: bool = False,
    commit_after: bool = True,
) -> int:
    """Insert one ``XRuleFiring`` (as dict) into ``x_rule_firing``.

    Returns the autogenerated ``firing_id``. Caller stamps ``daily_plan_id``
    + ``user_id`` because the firing dict itself doesn't carry plan linkage.

    ``orphan`` defaults to False. Migration 004 added the ``orphan`` column
    as the Phase-2.5 Condition-1 defensive check: a firing whose
    ``affected_domain`` is not among the committing plan's proposal
    domains is stamped ``orphan=1`` so it surfaces in audit queries
    instead of silently ending up as dead data. The current X-rule set
    (X1/X3/X6 via hard-proposal iteration, X7 over all proposals) cannot
    emit orphans by construction; ``run_synthesis`` computes the flag
    anyway so a regression shows up in the table rather than passing
    silently.
    """

    mutation = firing.get("recommended_mutation")
    signals = firing.get("source_signals") or {}

    cursor = conn.execute(
        """
        INSERT INTO x_rule_firing (
            daily_plan_id, user_id, x_rule_id, tier,
            affected_domain, trigger_note,
            mutation_json, source_signals_json, fired_at, orphan
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            1 if orphan else 0,
        ),
    )
    if commit_after:
        conn.commit()
    # F-A-11 fix per W-H1: lastrowid is Optional[int] in typeshed.
    last = cursor.lastrowid
    if last is None:
        raise RuntimeError("INSERT into x_rule_firing returned no rowid")
    return int(last)


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

    # M3: ``daily_plan_id`` is now a first-class column. The linkage
    # still lives in payload_json for audit completeness (and for the
    # JSONL reproject path that doesn't have the column at parse time
    # in older logs), but the column is the queryable join key.
    #
    # v0.1.14 W-PROV-1: ``evidence_locators_json`` is the typed
    # source-row provenance column. The same data lives in
    # payload_json["evidence_locators"] for audit completeness; the
    # column is the queryable / joinable surface that v0.2.0 W52
    # weekly review will consume.
    from health_agent_infra.core.provenance.locator import serialize_locators
    locators_payload = recommendation.get("evidence_locators")
    locators_json = serialize_locators(locators_payload) if locators_payload else None
    conn.execute(
        """
        INSERT INTO recommendation_log (
            recommendation_id, user_id, for_date, issued_at,
            action, confidence, bounded, payload_json,
            jsonl_offset, source, ingest_actor, agent_version,
            produced_at, validated_at, projected_at, domain,
            daily_plan_id, evidence_locators_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            recommendation.get("daily_plan_id"),
            locators_json,
        ),
    )
    if commit_after:
        conn.commit()


PLANNED_RECOMMENDATION_SCHEMA_VERSION = "planned_recommendation.v1"


def project_planned_recommendation(
    conn: sqlite3.Connection,
    planned: dict,
    *,
    source: str = "claude_agent_v1",
    ingest_actor: str = "claude_agent_v1",
    agent_version: Optional[str] = None,
    commit_after: bool = True,
) -> None:
    """Insert a pre-X-rule draft row into ``planned_recommendation``.

    Migration 011 introduced the aggregate "original plan" ledger — one row
    per (daily_plan_id, domain) capturing the recommendation shape **before**
    Phase A / Phase B mutations ran. ``run_synthesis`` calls this inside
    its atomic transaction, once per proposal, using a mechanical draft of
    the original (unmutated) proposal.

    Expected dict keys: ``planned_id``, ``daily_plan_id``, ``proposal_id``,
    ``user_id``, ``for_date``, ``domain``, ``action``, ``confidence``.
    Optional: ``action_detail`` (stored JSON-encoded), ``captured_at``
    (defaults to now).

    Not idempotent — ``delete_canonical_plan_cascade`` removes prior rows
    for the canonical plan before a re-synthesize, so a second call with
    the same ``planned_id`` is a programming error.
    """

    captured_at = planned.get("captured_at") or _now_iso()
    action_detail = planned.get("action_detail")
    conn.execute(
        """
        INSERT INTO planned_recommendation (
            planned_id, daily_plan_id, proposal_id, user_id, for_date,
            domain, action, confidence, action_detail_json,
            schema_version, source, ingest_actor, agent_version, captured_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            planned["planned_id"],
            planned["daily_plan_id"],
            planned["proposal_id"],
            planned["user_id"],
            planned["for_date"],
            planned["domain"],
            planned["action"],
            planned["confidence"],
            json.dumps(action_detail, sort_keys=True) if action_detail is not None else None,
            planned.get("schema_version", PLANNED_RECOMMENDATION_SCHEMA_VERSION),
            source,
            ingest_actor,
            agent_version,
            captured_at,
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
      2. ``planned_recommendation`` → references both ``daily_plan`` and
         ``proposal_log`` (FK); must be deleted before either parent row
         is altered
      3. ``recommendation_log`` → no FK to ``daily_plan`` but carries the
         id in ``payload_json``; deleted by explicit join
      4. ``daily_plan``
      5. Reset ``proposal_log.daily_plan_id`` on any rows that pointed here

    Callers compose this inside the synthesis BEGIN/COMMIT so either
    the whole replacement lands or nothing changes.
    """

    # M3: every recommendation for this plan carries daily_plan_id as a
    # proper column (migration 009). Pre-M3 rows were backfilled from
    # payload_json at migration time, so the column lookup finds every
    # row the previous json_extract path did.
    rec_rows = conn.execute(
        "SELECT recommendation_id FROM recommendation_log "
        "WHERE daily_plan_id = ?",
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
    # Migration 011 — planned_recommendation has FKs to both daily_plan
    # and proposal_log. Delete before the daily_plan row so the FK
    # doesn't trip, and before the proposal_log unlink below for the
    # same reason on any future deletion path.
    conn.execute(
        "DELETE FROM planned_recommendation WHERE daily_plan_id = ?",
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
    """Set ``daily_plan.superseded_by_plan_id`` (and the JSON attr, for
    backward-compat reads) on a prior plan.

    Used by ``hai synthesize --supersede`` when intentionally
    versioning rather than atomically replacing.

    Per D1 (``reporting/plans/v0_1_4/D1_re_author_semantics.md``) and
    migration 014, the authoritative forward pointer is the
    ``superseded_by_plan_id`` column. The
    ``synthesis_meta_json.$.superseded_by`` attribute continues to be
    written for the migration window so legacy reads keep working; it
    can be retired in a later cleanup.
    """

    conn.execute(
        "UPDATE daily_plan SET "
        "superseded_by_plan_id = ?, "
        "superseded_at = ?, "
        "synthesis_meta_json = json_set(COALESCE(synthesis_meta_json, '{}'), "
        "'$.superseded_by', ?) "
        "WHERE daily_plan_id = ?",
        (superseded_by, _now_iso(), superseded_by, daily_plan_id),
    )
    if commit_after:
        conn.commit()


def read_proposals_for_plan_key(
    conn: sqlite3.Connection,
    *,
    for_date: str,
    user_id: str,
    include_superseded: bool = False,
) -> list[dict]:
    """Return proposals in ``proposal_log`` for ``(for_date, user_id)``.

    Default (``include_superseded=False``) returns only canonical
    leaves (``superseded_by_proposal_id IS NULL``). This is what
    synthesis wants — the current per-domain proposal, not historical
    revisions. Per D1, synthesis over a revised day reads the latest
    leaf of each domain chain; older revisions are preserved for
    audit but not re-synthesized into new plans.

    ``include_superseded=True`` returns the full chain (leaves +
    superseded rows) for audit surfaces. ``hai explain --plan-version
    all`` uses this.
    """

    if include_superseded:
        sql = (
            "SELECT payload_json FROM proposal_log "
            "WHERE for_date = ? AND user_id = ? "
            "ORDER BY domain, revision, proposal_id"
        )
    else:
        sql = (
            "SELECT payload_json FROM proposal_log "
            "WHERE for_date = ? AND user_id = ? "
            "AND superseded_by_proposal_id IS NULL "
            "ORDER BY domain, proposal_id"
        )
    rows = conn.execute(sql, (for_date, user_id)).fetchall()
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
