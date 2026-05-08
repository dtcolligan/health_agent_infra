"""Phase 4 step 1 — migration 005 (strength expansion) + taxonomy seed.

Contracts pinned:

  1. After migration 005 applies, ``exercise_taxonomy`` has ≥80 rows,
     all with source='seed', and every canonical_name from
     ``domains/strength/taxonomy_seed.csv`` is present with matching
     primary_muscle_group / category / equipment / aliases fields.
  2. The migration SQL and the shipped CSV do not diverge: every row in
     the CSV appears in the DB with identical values; every seeded row
     in the DB has a matching CSV row. Future edits must update both.
  3. ``accepted_resistance_training_state_daily`` gains four new columns
     (``total_reps``, ``volume_by_muscle_group_json``,
     ``estimated_1rm_json``, ``unmatched_exercise_tokens_json``). The
     pre-existing columns (session_count, total_sets,
     total_volume_kg_reps, exercises) remain intact so the minimal
     7C.1 projection path keeps working.
  4. ``gym_set`` gains a nullable ``exercise_id`` column that references
     ``exercise_taxonomy(exercise_id)``. Historical rows keep NULL;
     inserting a new gym_set with a bogus exercise_id is rejected when
     PRAGMA foreign_keys=ON.
  5. CHECK constraints on exercise_taxonomy reject invalid category /
     equipment / source values.
"""

from __future__ import annotations

import csv
import sqlite3
import uuid
from datetime import date, datetime, timezone
from importlib.resources import files
from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    current_schema_version,
    initialize_database,
    open_connection,
)


USER = "u_test"
AS_OF = date(2026, 4, 18)


def _load_seed_csv() -> list[dict]:
    csv_path = files("health_agent_infra").joinpath(
        "domains", "strength", "taxonomy_seed.csv"
    )
    with csv_path.open("r", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _fetch_taxonomy_rows(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.execute(
        """
        SELECT exercise_id, canonical_name, aliases,
               primary_muscle_group, secondary_muscle_groups,
               category, equipment, source
        FROM exercise_taxonomy
        ORDER BY exercise_id
        """
    )
    return [dict(r) for r in cur.fetchall()]


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


# ---------------------------------------------------------------------------
# Table presence + row count
# ---------------------------------------------------------------------------

def test_head_schema_version_is_at_least_five(tmp_path: Path):
    # After Phase 5 step 1 landed migration 006, head is 6; this test
    # locks that every migration up to and including 005 has applied,
    # not the exact head version.
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        assert current_schema_version(conn) >= 5
    finally:
        conn.close()


def test_exercise_taxonomy_seeded_with_at_least_eighty_rows(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM exercise_taxonomy WHERE source = 'seed'"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert count >= 80, f"expected ≥80 seeded rows, got {count}"


# ---------------------------------------------------------------------------
# CSV ↔ DB lockstep
# ---------------------------------------------------------------------------

def test_taxonomy_csv_and_migration_are_in_lockstep(tmp_path: Path):
    """Every CSV row must match a seeded DB row exactly, and every
    seeded DB row must correspond to a CSV row. Editing the migration
    without editing the CSV (or vice versa) surfaces here as a diff
    instead of silent drift."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        db_rows = _fetch_taxonomy_rows(conn)
    finally:
        conn.close()

    db_seed = {r["exercise_id"]: r for r in db_rows if r["source"] == "seed"}
    csv_rows = _load_seed_csv()
    csv_by_id = {r["exercise_id"]: r for r in csv_rows}

    assert set(db_seed) == set(csv_by_id), (
        f"seed rows diverge.\n"
        f"in DB not CSV: {sorted(set(db_seed) - set(csv_by_id))}\n"
        f"in CSV not DB: {sorted(set(csv_by_id) - set(db_seed))}"
    )

    def _normalise_optional(value: str | None) -> str | None:
        if value is None or value == "":
            return None
        return value

    for eid, csv_row in csv_by_id.items():
        db_row = db_seed[eid]
        assert db_row["canonical_name"] == csv_row["canonical_name"], eid
        assert _normalise_optional(db_row["aliases"]) == _normalise_optional(
            csv_row["aliases"]
        ), eid
        assert (
            db_row["primary_muscle_group"] == csv_row["primary_muscle_group"]
        ), eid
        assert _normalise_optional(
            db_row["secondary_muscle_groups"]
        ) == _normalise_optional(csv_row["secondary_muscle_groups"]), eid
        assert db_row["category"] == csv_row["category"], eid
        assert db_row["equipment"] == csv_row["equipment"], eid


# ---------------------------------------------------------------------------
# Accepted table expansion
# ---------------------------------------------------------------------------

EXPECTED_NEW_COLUMNS = {
    "total_reps",
    "volume_by_muscle_group_json",
    "estimated_1rm_json",
    "unmatched_exercise_tokens_json",
}

PRESERVED_COLUMNS = {
    "session_count",
    "total_sets",
    "total_volume_kg_reps",
    "exercises",
}


def test_accepted_resistance_gains_expected_columns(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        cols = {
            r["name"]
            for r in conn.execute(
                "PRAGMA table_info(accepted_resistance_training_state_daily)"
            ).fetchall()
        }
    finally:
        conn.close()

    missing_new = EXPECTED_NEW_COLUMNS - cols
    assert missing_new == set(), f"new columns missing: {sorted(missing_new)}"
    missing_preserved = PRESERVED_COLUMNS - cols
    assert missing_preserved == set(), (
        f"pre-existing columns lost: {sorted(missing_preserved)}"
    )


# ---------------------------------------------------------------------------
# gym_set.exercise_id FK
# ---------------------------------------------------------------------------

def _make_session(conn: sqlite3.Connection, session_id: str) -> None:
    conn.execute(
        """
        INSERT INTO gym_session (
            session_id, user_id, as_of_date, session_name, notes,
            source, ingest_actor, submission_id, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id, USER, AS_OF.isoformat(), "legs day", None,
            "user_manual", "hai_cli_direct", f"m_gym_{session_id}",
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def test_gym_set_exercise_id_nullable(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _make_session(conn, "s1")
        conn.execute(
            """
            INSERT INTO gym_set (
                set_id, session_id, set_number, exercise_name,
                weight_kg, reps, rpe, ingested_at, exercise_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "set_s1_001", "s1", 1, "Bench Press",
                80.0, 5, 7.0,
                datetime.now(timezone.utc).isoformat(),
                None,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT exercise_id FROM gym_set WHERE set_id = ?",
            ("set_s1_001",),
        ).fetchone()
        assert row["exercise_id"] is None
    finally:
        conn.close()


def test_gym_set_exercise_id_accepts_valid_fk(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _make_session(conn, "s2")
        conn.execute(
            """
            INSERT INTO gym_set (
                set_id, session_id, set_number, exercise_name,
                weight_kg, reps, rpe, ingested_at, exercise_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "set_s2_001", "s2", 1, "Back Squat",
                100.0, 5, 8.0,
                datetime.now(timezone.utc).isoformat(),
                "back_squat",
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT exercise_id FROM gym_set WHERE set_id = ?",
            ("set_s2_001",),
        ).fetchone()
        assert row["exercise_id"] == "back_squat"
    finally:
        conn.close()


def test_gym_set_exercise_id_rejects_unknown_fk(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        _make_session(conn, "s3")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO gym_set (
                    set_id, session_id, set_number, exercise_name,
                    weight_kg, reps, rpe, ingested_at, exercise_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "set_s3_001", "s3", 1, "Phantom Lift",
                    100.0, 5, 8.0,
                    datetime.now(timezone.utc).isoformat(),
                    "does_not_exist",
                ),
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CHECK constraints on exercise_taxonomy
# ---------------------------------------------------------------------------

def test_exercise_taxonomy_rejects_bad_category(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO exercise_taxonomy (
                    exercise_id, canonical_name, aliases,
                    primary_muscle_group, secondary_muscle_groups,
                    category, equipment, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "bad_cat", "Bad Cat", None, "quads", None,
                    "hybrid", "barbell", "user_manual",
                ),
            )
    finally:
        conn.close()


def test_exercise_taxonomy_rejects_bad_equipment(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO exercise_taxonomy (
                    exercise_id, canonical_name, aliases,
                    primary_muscle_group, secondary_muscle_groups,
                    category, equipment, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "bad_equip", "Bad Equip", None, "quads", None,
                    "compound", "band", "user_manual",
                ),
            )
    finally:
        conn.close()


def test_exercise_taxonomy_allows_user_manual_source(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        conn.execute(
            """
            INSERT INTO exercise_taxonomy (
                exercise_id, canonical_name, aliases,
                primary_muscle_group, secondary_muscle_groups,
                category, equipment, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "user_defined_lift", "User Defined Lift",
                "udf|userlift", "quads", None,
                "compound", "barbell", "user_manual",
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT source FROM exercise_taxonomy WHERE exercise_id = ?",
            ("user_defined_lift",),
        ).fetchone()
        assert row["source"] == "user_manual"
    finally:
        conn.close()
