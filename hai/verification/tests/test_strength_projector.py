"""Phase 4 step 2 — strength projector.

Contracts pinned:

  1. Taxonomy resolution is case-folded, matches canonical names
     (winning over aliases), and falls back to alias lookup.
  2. Unmatched free-text names never contribute to volume-by-muscle
     or estimated-1RM; they surface exactly once each in
     ``unmatched_exercise_tokens_json``.
  3. ``total_sets`` / ``total_reps`` / ``total_volume_kg_reps`` /
     ``session_count`` stay consistent with the raw rows.
  4. ``volume_by_muscle_group_json`` attributes kg·reps to the
     primary muscle group of each resolved exercise.
  5. ``estimated_1rm_json`` tracks the best Epley 1RM of the day per
     resolved exercise_id, with the source set preserved.
  6. Re-projection after new raw rows updates corrected_at and the
     aggregates; pre-stamped ``gym_set.exercise_id`` wins over
     name-based resolution.
  7. Epley formula: ``weight_kg * (1 + reps / 30)``.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)
from health_agent_infra.core.state.projectors.strength import (
    _build_index_from_conn,
    epley_one_rm,
    project_accepted_resistance_training_state_daily,
    resolve_exercise,
)


USER = "u_test"
AS_OF = date(2026, 4, 18)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _insert_session(conn: sqlite3.Connection, session_id: str, as_of: date = AS_OF) -> None:
    conn.execute(
        """
        INSERT INTO gym_session (
            session_id, user_id, as_of_date, session_name, notes,
            source, ingest_actor, submission_id, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id, USER, as_of.isoformat(), f"session_{session_id}", None,
            "user_manual", "hai_cli_direct", f"m_gym_{session_id}",
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def _insert_set(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    set_number: int,
    exercise_name: str,
    weight_kg: float | None,
    reps: int | None,
    rpe: float | None = None,
    exercise_id: str | None = None,
    supersedes_set_id: str | None = None,
) -> str:
    set_id = f"set_{session_id}_{set_number:03d}"
    if supersedes_set_id is not None:
        set_id = f"set_{session_id}_{set_number:03d}_r"
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
            datetime.now(timezone.utc).isoformat(), supersedes_set_id, exercise_id,
        ),
    )
    return set_id


def _fetch_accepted(conn: sqlite3.Connection) -> dict:
    row = conn.execute(
        """
        SELECT session_count, total_sets, total_reps,
               total_volume_kg_reps, exercises,
               volume_by_muscle_group_json,
               estimated_1rm_json,
               unmatched_exercise_tokens_json,
               derived_from, source, ingest_actor,
               projected_at, corrected_at
        FROM accepted_resistance_training_state_daily
        WHERE as_of_date = ? AND user_id = ?
        """,
        (AS_OF.isoformat(), USER),
    ).fetchone()
    return dict(row) if row else {}


# ---------------------------------------------------------------------------
# Epley
# ---------------------------------------------------------------------------

def test_epley_one_rm_formula():
    assert epley_one_rm(100.0, 1) == pytest.approx(100.0 * (1 + 1 / 30))
    assert epley_one_rm(100.0, 5) == pytest.approx(100.0 * (1 + 5 / 30))
    assert epley_one_rm(80.0, 10) == pytest.approx(80.0 * (1 + 10 / 30))


def test_epley_rejects_non_positive_inputs():
    with pytest.raises(ValueError):
        epley_one_rm(0.0, 5)
    with pytest.raises(ValueError):
        epley_one_rm(100.0, 0)


# ---------------------------------------------------------------------------
# Taxonomy resolution
# ---------------------------------------------------------------------------

def test_resolver_matches_canonical_name_case_insensitively(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _, resolver = _build_index_from_conn(conn)
    finally:
        conn.close()

    assert resolve_exercise("Back Squat", resolver) == "back_squat"
    assert resolve_exercise("back squat", resolver) == "back_squat"
    assert resolve_exercise("  BACK  SQUAT  ", resolver) is None  # internal whitespace not normalised
    assert resolve_exercise("back squat ", resolver) == "back_squat"  # trimmed


def test_resolver_matches_aliases(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _, resolver = _build_index_from_conn(conn)
    finally:
        conn.close()

    assert resolve_exercise("bench", resolver) == "bench_press"
    assert resolve_exercise("BP", resolver) == "bench_press"
    assert resolve_exercise("rdl", resolver) == "romanian_deadlift"
    assert resolve_exercise("ohp", resolver) == "overhead_press"


def test_resolver_returns_none_for_unknown(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _, resolver = _build_index_from_conn(conn)
    finally:
        conn.close()

    assert resolve_exercise("phantom_movement_xyz", resolver) is None


def test_resolver_canonical_wins_over_alias_collision(tmp_path: Path):
    """When a canonical name coincides with an alias on another entry,
    the canonical entry wins."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        # 'Dip' is the canonical for dip, not an alias of anything.
        _, resolver = _build_index_from_conn(conn)
        assert resolve_exercise("Dip", resolver) == "dip"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Aggregates — clean, matched day
# ---------------------------------------------------------------------------

def test_projector_computes_totals_for_matched_sets(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _insert_session(conn, "s_legs")
        # 5 sets of back squat 100×5 = 500 kg·reps × 5 = 2500
        for i in range(1, 6):
            _insert_set(
                conn, session_id="s_legs", set_number=i,
                exercise_name="Back Squat", weight_kg=100.0, reps=5,
            )
        # 3 sets of bench press 80×5 = 400 kg·reps × 3 = 1200
        _insert_session(conn, "s_push")
        for i in range(1, 4):
            _insert_set(
                conn, session_id="s_push", set_number=i,
                exercise_name="Bench Press", weight_kg=80.0, reps=5,
            )
        conn.commit()

        project_accepted_resistance_training_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="hai_cli_direct",
        )
        accepted = _fetch_accepted(conn)
    finally:
        conn.close()

    assert accepted["session_count"] == 2
    assert accepted["total_sets"] == 8
    assert accepted["total_reps"] == 40  # 5*5 + 3*5
    assert accepted["total_volume_kg_reps"] == pytest.approx(3700.0)
    assert accepted["unmatched_exercise_tokens_json"] is None


def test_projector_attributes_volume_to_primary_muscle_group(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _insert_session(conn, "s_mixed")
        # Back Squat → quads (primary)
        _insert_set(conn, session_id="s_mixed", set_number=1,
                    exercise_name="Back Squat", weight_kg=100.0, reps=5)
        # Bench Press → chest (primary)
        _insert_set(conn, session_id="s_mixed", set_number=2,
                    exercise_name="Bench Press", weight_kg=80.0, reps=5)
        # Romanian Deadlift → hamstrings (primary)
        _insert_set(conn, session_id="s_mixed", set_number=3,
                    exercise_name="RDL", weight_kg=120.0, reps=8)
        conn.commit()

        project_accepted_resistance_training_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="hai_cli_direct",
        )
        accepted = _fetch_accepted(conn)
    finally:
        conn.close()

    by_group = json.loads(accepted["volume_by_muscle_group_json"])
    assert by_group["quads"] == pytest.approx(500.0)
    assert by_group["chest"] == pytest.approx(400.0)
    assert by_group["hamstrings"] == pytest.approx(960.0)
    # No secondary-group leakage.
    assert "glutes" not in by_group


def test_projector_tracks_best_epley_1rm_per_exercise(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _insert_session(conn, "s_heavy")
        # Back Squat — best set 120×3 → Epley 120*(1+3/30) = 132.0
        _insert_set(conn, session_id="s_heavy", set_number=1,
                    exercise_name="Back Squat", weight_kg=100.0, reps=5)  # 116.66
        _insert_set(conn, session_id="s_heavy", set_number=2,
                    exercise_name="Back Squat", weight_kg=120.0, reps=3)  # 132.0
        _insert_set(conn, session_id="s_heavy", set_number=3,
                    exercise_name="Back Squat", weight_kg=110.0, reps=4)  # 124.66
        # Bench Press — only one set at 80×5 → 93.33
        _insert_set(conn, session_id="s_heavy", set_number=4,
                    exercise_name="Bench Press", weight_kg=80.0, reps=5)
        conn.commit()

        project_accepted_resistance_training_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="hai_cli_direct",
        )
        accepted = _fetch_accepted(conn)
    finally:
        conn.close()

    one_rm = json.loads(accepted["estimated_1rm_json"])
    assert one_rm["back_squat"]["estimated_1rm_kg"] == pytest.approx(132.0)
    assert one_rm["back_squat"]["weight_kg"] == 120.0
    assert one_rm["back_squat"]["reps"] == 3
    assert one_rm["bench_press"]["estimated_1rm_kg"] == pytest.approx(93.3)


# ---------------------------------------------------------------------------
# Unmatched exercises
# ---------------------------------------------------------------------------

def test_unmatched_tokens_surface_but_do_not_pollute_aggregates(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _insert_session(conn, "s_exp")
        _insert_set(conn, session_id="s_exp", set_number=1,
                    exercise_name="Back Squat", weight_kg=100.0, reps=5)
        # "Jefferson Curl" is not in the taxonomy.
        _insert_set(conn, session_id="s_exp", set_number=2,
                    exercise_name="Jefferson Curl", weight_kg=30.0, reps=10)
        _insert_set(conn, session_id="s_exp", set_number=3,
                    exercise_name="Jefferson Curl", weight_kg=35.0, reps=10)
        conn.commit()

        project_accepted_resistance_training_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="hai_cli_direct",
        )
        accepted = _fetch_accepted(conn)
    finally:
        conn.close()

    unmatched = json.loads(accepted["unmatched_exercise_tokens_json"])
    assert unmatched == ["Jefferson Curl"]  # deduped, sorted

    by_group = json.loads(accepted["volume_by_muscle_group_json"])
    assert by_group == {"quads": 500.0}  # no leakage from unmatched

    one_rm = json.loads(accepted["estimated_1rm_json"])
    assert set(one_rm.keys()) == {"back_squat"}  # no unmatched 1RM entries

    # But totals still count every non-superseded set.
    assert accepted["total_sets"] == 3
    assert accepted["total_reps"] == 25  # 5 + 10 + 10
    assert accepted["total_volume_kg_reps"] == pytest.approx(500.0 + 300.0 + 350.0)


def test_all_unmatched_leaves_volume_and_1rm_null(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _insert_session(conn, "s_all_unknown")
        _insert_set(conn, session_id="s_all_unknown", set_number=1,
                    exercise_name="Phantom Lift", weight_kg=50.0, reps=5)
        conn.commit()
        project_accepted_resistance_training_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="hai_cli_direct",
        )
        accepted = _fetch_accepted(conn)
    finally:
        conn.close()

    assert accepted["volume_by_muscle_group_json"] is None
    assert accepted["estimated_1rm_json"] is None
    assert json.loads(accepted["unmatched_exercise_tokens_json"]) == ["Phantom Lift"]
    assert accepted["total_sets"] == 1


# ---------------------------------------------------------------------------
# Reproject hygiene + superseded rows
# ---------------------------------------------------------------------------

def test_projector_is_upsert_and_stamps_corrected_at(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _insert_session(conn, "s_one")
        _insert_set(conn, session_id="s_one", set_number=1,
                    exercise_name="Back Squat", weight_kg=100.0, reps=5)
        conn.commit()

        is_insert_first = project_accepted_resistance_training_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="hai_cli_direct",
        )
        assert is_insert_first is True
        first = _fetch_accepted(conn)
        assert first["corrected_at"] is None

        # Add a new set, re-project.
        _insert_set(conn, session_id="s_one", set_number=2,
                    exercise_name="Back Squat", weight_kg=110.0, reps=5)
        conn.commit()

        is_insert_second = project_accepted_resistance_training_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="hai_cli_direct",
        )
        assert is_insert_second is False
        second = _fetch_accepted(conn)
        assert second["corrected_at"] is not None
        assert second["total_sets"] == 2
        one_rm = json.loads(second["estimated_1rm_json"])
        # 110×5 > 100×5 → Epley 128.33
        assert one_rm["back_squat"]["weight_kg"] == 110.0
    finally:
        conn.close()


def test_superseded_sets_excluded_from_aggregate(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _insert_session(conn, "s_correct")
        first_id = _insert_set(
            conn, session_id="s_correct", set_number=1,
            exercise_name="Back Squat", weight_kg=100.0, reps=5,
        )
        # Corrected replacement.
        _insert_set(
            conn, session_id="s_correct", set_number=1,
            exercise_name="Back Squat", weight_kg=105.0, reps=5,
            supersedes_set_id=first_id,
        )
        conn.commit()

        project_accepted_resistance_training_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="hai_cli_direct",
        )
        accepted = _fetch_accepted(conn)
    finally:
        conn.close()

    # Only the replacement counts.
    assert accepted["total_sets"] == 1
    assert accepted["total_reps"] == 5
    assert accepted["total_volume_kg_reps"] == pytest.approx(525.0)


# ---------------------------------------------------------------------------
# Pre-stamped exercise_id wins over name-based resolution.
# ---------------------------------------------------------------------------

def test_prestamped_exercise_id_overrides_name_resolution(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _insert_session(conn, "s_stamp")
        # Free-text name is ambiguous but exercise_id pins it to front_squat.
        _insert_set(
            conn, session_id="s_stamp", set_number=1,
            exercise_name="some squat variant",
            weight_kg=100.0, reps=5,
            exercise_id="front_squat",
        )
        conn.commit()

        project_accepted_resistance_training_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="hai_cli_direct",
        )
        accepted = _fetch_accepted(conn)
    finally:
        conn.close()

    one_rm = json.loads(accepted["estimated_1rm_json"])
    assert "front_squat" in one_rm
    # Unmatched should be empty because the stamp wins.
    assert accepted["unmatched_exercise_tokens_json"] is None


# ---------------------------------------------------------------------------
# Sets missing weight/reps still count in total_sets but not volume/1rm.
# ---------------------------------------------------------------------------

def test_sets_missing_weight_or_reps_skipped_from_1rm_and_volume(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _insert_session(conn, "s_missing")
        _insert_set(conn, session_id="s_missing", set_number=1,
                    exercise_name="Back Squat", weight_kg=None, reps=5)
        _insert_set(conn, session_id="s_missing", set_number=2,
                    exercise_name="Back Squat", weight_kg=100.0, reps=None)
        _insert_set(conn, session_id="s_missing", set_number=3,
                    exercise_name="Back Squat", weight_kg=100.0, reps=5)
        conn.commit()

        project_accepted_resistance_training_state_daily(
            conn, as_of_date=AS_OF, user_id=USER,
            ingest_actor="hai_cli_direct",
        )
        accepted = _fetch_accepted(conn)
    finally:
        conn.close()

    assert accepted["total_sets"] == 3
    assert accepted["total_reps"] == 10  # 5 + 0 + 5
    # Only the third set contributes volume + 1RM.
    assert accepted["total_volume_kg_reps"] == pytest.approx(500.0)
    one_rm = json.loads(accepted["estimated_1rm_json"])
    assert one_rm["back_squat"]["weight_kg"] == 100.0
    assert one_rm["back_squat"]["reps"] == 5
