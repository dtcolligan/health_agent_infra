"""Accepted resistance-training state projector.

Phase 4 step 2. Replaces the minimal in-line projector shipped in 7C.1.
Reads every non-superseded ``gym_set`` for a given
``(as_of_date, user_id)``, resolves the free-text ``exercise_name``
against ``exercise_taxonomy`` (canonical + aliases, case-folded),
and writes the expanded shape of
``accepted_resistance_training_state_daily``:

  - ``session_count``                — distinct gym_session ids.
  - ``total_sets``                   — non-superseded set count.
  - ``total_reps``                   — sum of reps across those sets.
  - ``total_volume_kg_reps``         — Σ(weight_kg × reps) over sets
                                       where both are populated.
  - ``exercises``                    — free-text JSON list (preserved
                                       from 7C.1).
  - ``volume_by_muscle_group_json``  — JSON object keyed by
                                       taxonomy primary_muscle_group
                                       → kg·reps attributed to that
                                       group (primary-only attribution).
  - ``estimated_1rm_json``           — JSON object keyed by canonical
                                       exercise_id → best Epley 1RM
                                       of the day (value includes the
                                       source set).
  - ``unmatched_exercise_tokens_json`` — JSON list of the distinct
                                       free-text names that did not
                                       resolve against the taxonomy.
                                       Agent surfaces these for
                                       catalogue extension; they never
                                       participate in 1RM or
                                       muscle-group aggregation.

The projector never mutates raw: ``gym_set.exercise_id`` is populated
at intake time by the strength-intake path; historical rows with
``exercise_id = NULL`` are re-resolved by name on every projection so
that taxonomy extensions picked up after the fact still produce the
right aggregates.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Optional

from health_agent_infra.core.state.projectors._shared import _now_iso


# ---------------------------------------------------------------------------
# Taxonomy resolution — code-owned, deterministic, case-folded.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TaxonomyEntry:
    exercise_id: str
    canonical_name: str
    primary_muscle_group: str
    secondary_muscle_groups: tuple[str, ...]
    category: str
    equipment: str


def _norm(token: str) -> str:
    return token.strip().casefold()


def _split_pipe(value: Optional[str]) -> tuple[str, ...]:
    if value is None or value == "":
        return ()
    return tuple(p.strip() for p in value.split("|") if p.strip())


def _build_index_from_conn(conn: sqlite3.Connection) -> tuple[
    dict[str, TaxonomyEntry], dict[str, str]
]:
    """Load taxonomy + resolver index in one pass.

    Returns ``(taxonomy_by_id, resolver_index)`` where
    ``resolver_index[norm_token] = exercise_id``.
    """

    taxonomy: dict[str, TaxonomyEntry] = {}
    resolver: dict[str, str] = {}

    rows = conn.execute(
        """
        SELECT exercise_id, canonical_name, aliases,
               primary_muscle_group, secondary_muscle_groups,
               category, equipment
        FROM exercise_taxonomy
        ORDER BY exercise_id
        """
    ).fetchall()

    for r in rows:
        entry = TaxonomyEntry(
            exercise_id=r["exercise_id"],
            canonical_name=r["canonical_name"],
            primary_muscle_group=r["primary_muscle_group"],
            secondary_muscle_groups=_split_pipe(r["secondary_muscle_groups"]),
            category=r["category"],
            equipment=r["equipment"],
        )
        taxonomy[entry.exercise_id] = entry
        # Canonical name always wins on collision.
        resolver[_norm(entry.canonical_name)] = entry.exercise_id

    # Second pass: aliases, deterministic (ordered by exercise_id already).
    for r in rows:
        for alias in _split_pipe(r["aliases"]):
            norm = _norm(alias)
            if norm in resolver:
                continue  # canonical or earlier alias already claims this
            resolver[norm] = r["exercise_id"]

    return taxonomy, resolver


def resolve_exercise(
    name: str, resolver: dict[str, str]
) -> Optional[str]:
    """Return the exercise_id for a free-text name, or None if unmatched."""

    if not name:
        return None
    return resolver.get(_norm(name))


# ---------------------------------------------------------------------------
# 1RM — Epley formula.
# ---------------------------------------------------------------------------

def epley_one_rm(weight_kg: float, reps: int) -> float:
    """Epley estimate: ``weight_kg * (1 + reps / 30)``.

    Domain: reps > 0 and weight_kg > 0. Callers gate on both being
    populated before calling. Rounded to 0.1 kg at serialisation time.
    """

    if reps <= 0 or weight_kg <= 0:
        raise ValueError("epley_one_rm requires positive weight_kg and reps")
    return weight_kg * (1.0 + reps / 30.0)


# ---------------------------------------------------------------------------
# Main projector.
# ---------------------------------------------------------------------------

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

    Returns ``True`` on insert, ``False`` on update (corrected_at set).

    Superseded raw rows are excluded by checking whether each set_id
    appears in any other row's ``supersedes_set_id`` — matches 7C.1
    semantics; stays stable when set-level corrections land in a
    future CLI.

    **Provenance.** ``derived_from`` is a JSON list of session_ids that
    contributed. Auditors can JOIN back to gym_session for per-session
    provenance (source, ingest_actor, submission_id).
    """

    taxonomy, resolver = _build_index_from_conn(conn)

    rows = conn.execute(
        """
        SELECT
            gs.session_id,
            gset.set_id, gset.exercise_name, gset.exercise_id,
            gset.weight_kg, gset.reps
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
    free_text_exercises = sorted({r["exercise_name"] for r in rows})
    total_sets = len(rows)
    total_reps = sum((r["reps"] or 0) for r in rows) if rows else 0

    volume_values = [
        (r["weight_kg"] or 0) * (r["reps"] or 0)
        for r in rows
        if r["weight_kg"] is not None and r["reps"] is not None
    ]
    total_volume = round(sum(volume_values), 2) if volume_values else None

    # Volume by primary muscle group (only for resolved exercises).
    # Best Epley 1RM per resolved exercise_id.
    # Unmatched free-text names collected for audit.
    volume_by_group: dict[str, float] = {}
    best_by_exercise: dict[str, dict] = {}
    unmatched: set[str] = set()

    for r in rows:
        # Prefer a pre-stamped exercise_id (intake flow stamps it);
        # fall back to resolving from the free-text name so historical
        # rows pick up taxonomy matches on reproject.
        eid = r["exercise_id"] or resolve_exercise(
            r["exercise_name"], resolver
        )

        if eid is None or eid not in taxonomy:
            unmatched.add(r["exercise_name"])
            continue

        entry = taxonomy[eid]

        weight = r["weight_kg"]
        reps = r["reps"]
        if weight is not None and reps is not None and weight > 0 and reps > 0:
            vol = float(weight) * int(reps)
            volume_by_group[entry.primary_muscle_group] = round(
                volume_by_group.get(entry.primary_muscle_group, 0.0) + vol, 2
            )

            one_rm = epley_one_rm(float(weight), int(reps))
            prev = best_by_exercise.get(eid)
            if prev is None or one_rm > prev["estimated_1rm_kg"]:
                best_by_exercise[eid] = {
                    "estimated_1rm_kg": round(one_rm, 1),
                    "weight_kg": float(weight),
                    "reps": int(reps),
                }

    volume_by_group_json = (
        json.dumps(volume_by_group, sort_keys=True) if volume_by_group else None
    )
    estimated_1rm_json = (
        json.dumps(best_by_exercise, sort_keys=True)
        if best_by_exercise else None
    )
    unmatched_json = (
        json.dumps(sorted(unmatched), sort_keys=True) if unmatched else None
    )
    exercises_json = json.dumps(free_text_exercises, sort_keys=True)
    derived_from_json = json.dumps(session_ids, sort_keys=True)

    now_iso = _now_iso()

    existing = conn.execute(
        "SELECT 1 FROM accepted_resistance_training_state_daily "
        "WHERE as_of_date = ? AND user_id = ?",
        (as_of_date.isoformat(), user_id),
    ).fetchone()
    is_insert = existing is None

    values = (
        len(session_ids),
        total_sets,
        total_reps,
        total_volume,
        exercises_json,
        volume_by_group_json,
        estimated_1rm_json,
        unmatched_json,
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
                session_count, total_sets, total_reps,
                total_volume_kg_reps, exercises,
                volume_by_muscle_group_json, estimated_1rm_json,
                unmatched_exercise_tokens_json,
                derived_from, source, ingest_actor,
                projected_at, corrected_at,
                as_of_date, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
    else:
        conn.execute(
            """
            UPDATE accepted_resistance_training_state_daily SET
                session_count = ?, total_sets = ?, total_reps = ?,
                total_volume_kg_reps = ?, exercises = ?,
                volume_by_muscle_group_json = ?, estimated_1rm_json = ?,
                unmatched_exercise_tokens_json = ?,
                derived_from = ?, source = ?, ingest_actor = ?,
                projected_at = ?, corrected_at = ?
            WHERE as_of_date = ? AND user_id = ?
            """,
            values,
        )
    if commit_after:
        conn.commit()
    return is_insert
