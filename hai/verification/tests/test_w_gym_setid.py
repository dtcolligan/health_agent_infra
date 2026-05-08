"""W-GYM-SETID — gym_set PK collision fix (v0.1.15).

Per `hai/reporting/plans/v0_1_15/PLAN.md` §2.A:

The pre-W-GYM-SETID `deterministic_set_id(session_id, set_number)` returned
`f"set_{session_id}_{set_number:03d}"`. Multi-exercise sessions where set
numbers restart per exercise (a leg+back day with Deadlift sets 1-3, Back
Squat sets 1-3, Hamstring Curl sets 1-3, Pull-up sets 1-2) silently dropped
sets 4-11 via INSERT OR IGNORE because the set_ids collided.

Fix shape: `deterministic_set_id(session_id, exercise_name_slug, set_number)`
returns `f"set_{session_id}_{exercise_name_slug}_{set_number:03d}"` where
`exercise_name_slug = _norm_token(exercise_name) = exercise_name.strip().casefold()`
(matches `_norm` from `core/state/projectors/strength.py:66` per F-PHASE0-03).

Acceptance per PLAN §2.A:

  1. Multi-exercise fixture lands every set in `gym_set` with a unique PK;
     `accepted_resistance_training_state_daily` aggregates all 4 exercises.
  2. Migration 024 rewrites existing single-exercise rows' set_ids to the
     new format; supersession chains intact.
  3. Migration 024 does NOT recover JSONL-dropped rows; recovery is the
     operator-only `hai state reproject` path.
  4. `hai state reproject` against a multi-exercise JSONL fixture against
     a post-migration DB recovers all 11 sets to `gym_set`.
  5. `hai backup` round-trip on the post-migration DB preserves `gym_set`.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)
from health_agent_infra.core.state.store import (
    apply_pending_migrations,
    current_schema_version,
)


USER = "u_test"
AS_OF = date(2026, 5, 2)
SESSION_ID = "leg_back_2026_05_02"
FIXTURE = Path(__file__).parent / "fixtures" / "multi_exercise_session.jsonl"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _init_intake_dirs(tmp_path: Path) -> tuple[Path, Path]:
    base = tmp_path / "intake"
    base.mkdir(parents=True, exist_ok=True)
    db = _init_db(tmp_path)
    return base, db


def _seed_jsonl(base_dir: Path, fixture: Path = FIXTURE) -> Path:
    """Copy the multi-exercise fixture into base_dir as gym_sessions.jsonl."""
    target = base_dir / "gym_sessions.jsonl"
    target.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Acceptance test 1 — multi-exercise PK uniqueness via bulk intake
# ---------------------------------------------------------------------------


def test_multi_exercise_session_writes_every_set_unique_pk(tmp_path: Path):
    """Per PLAN §2.A acceptance test 1: every set lands in gym_set with a
    unique PK; accepted_resistance_training_state_daily aggregates all 4
    exercises and computes correct volume_by_muscle_group."""

    base, db = _init_intake_dirs(tmp_path)

    # Build a bulk-mode payload from the fixture (intake reads --session-json,
    # not raw JSONL files, so we transcribe the fixture rows into a session
    # payload). The fixture is the canonical record of the maintainer's
    # 2026-05-02 leg+back session shape (4 exercises × 11 total sets).
    fixture_rows = [
        json.loads(line)
        for line in FIXTURE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    payload = {
        "session_id": SESSION_ID,
        "session_name": fixture_rows[0]["session_name"],
        "as_of_date": AS_OF.isoformat(),
        "notes": fixture_rows[0]["notes"],
        "sets": [
            {
                "set_number": r["set_number"],
                "exercise_name": r["exercise_name"],
                "weight_kg": r["weight_kg"],
                "reps": r["reps"],
                "rpe": r["rpe"],
            }
            for r in fixture_rows
        ],
    }
    payload_path = tmp_path / "session.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")

    rc = cli_main([
        "intake", "gym",
        "--session-json", str(payload_path),
        "--user-id", USER,
        "--base-dir", str(base),
        "--db-path", str(db),
    ])
    assert rc == 0

    conn = open_connection(db)
    try:
        sets = conn.execute(
            "SELECT set_id, set_number, exercise_name FROM gym_set "
            "WHERE session_id = ? ORDER BY set_id",
            (SESSION_ID,),
        ).fetchall()
        accepted = conn.execute(
            "SELECT exercises, total_sets, volume_by_muscle_group_json "
            "FROM accepted_resistance_training_state_daily "
            "WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchone()
    finally:
        conn.close()

    # Pre-W-GYM-SETID: only 3 rows landed (Deadlift sets 1-3); sets 4-11
    # were silently dropped via INSERT OR IGNORE on the colliding PK.
    # Post-fix: all 11 distinct (exercise, set_number) tuples land.
    assert len(sets) == 11, (
        f"expected 11 unique sets, got {len(sets)} — PK collision regression"
    )
    set_ids = [r["set_id"] for r in sets]
    assert len(set(set_ids)) == 11, "set_ids not unique across rows"

    # Spot-check the set_id format: contains the exercise slug between
    # session_id and the zero-padded set_number.
    deadlift_set_1 = next(
        r["set_id"] for r in sets
        if r["exercise_name"] == "Deadlift" and r["set_number"] == 1
    )
    assert deadlift_set_1 == f"set_{SESSION_ID}_deadlift_001", (
        f"unexpected set_id format: {deadlift_set_1}"
    )

    # accepted aggregate covers all 4 exercises (not just Deadlift).
    assert accepted["total_sets"] == 11
    exercises = sorted(json.loads(accepted["exercises"]))
    assert exercises == sorted([
        "Back Squat", "Deadlift", "Hamstring Curl", "Pull-up",
    ]), f"missing exercises in aggregate: {exercises}"


# ---------------------------------------------------------------------------
# Acceptance test 2 — migration 024 rewrites existing single-exercise rows
# ---------------------------------------------------------------------------


def test_migration_024_rewrites_existing_set_ids_with_supersession_intact(
    tmp_path: Path,
):
    """Per PLAN §2.A acceptance test 2: existing single-exercise rows in
    `gym_set` survive migration 024 with set_ids rewritten to the new
    format; supersession chains preserved."""

    db_path = tmp_path / "state.db"

    # Seed a pre-migration-024 DB: apply migrations 1..23 only, then insert
    # rows in the OLD set_id format (no exercise slug).
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        from health_agent_infra.core.state.store import discover_migrations
        all_migrations = discover_migrations()
        pre_024 = [m for m in all_migrations if m[0] < 24]
        apply_pending_migrations(conn, pre_024)

        # Seed a single-exercise session (set numbers 1, 2, 3 for Bench).
        conn.execute(
            "INSERT INTO gym_session (session_id, user_id, as_of_date, "
            "session_name, notes, source, ingest_actor, submission_id, "
            "ingested_at, supersedes_session_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("bench_2026_05_01", USER, "2026-05-01", "Bench day", None,
             "user_manual", "cli", "m_gym_x", "2026-05-01T10:00:00+00:00", None),
        )
        # Old-format set_ids: set_<session>_<NNN>
        conn.execute(
            "INSERT INTO gym_set (set_id, session_id, set_number, "
            "exercise_name, weight_kg, reps, rpe, ingested_at, "
            "supersedes_set_id) VALUES (?,?,?,?,?,?,?,?,?)",
            ("set_bench_2026_05_01_001", "bench_2026_05_01", 1,
             "Bench Press", 80.0, 5, 7.0,
             "2026-05-01T10:00:00+00:00", None),
        )
        conn.execute(
            "INSERT INTO gym_set (set_id, session_id, set_number, "
            "exercise_name, weight_kg, reps, rpe, ingested_at, "
            "supersedes_set_id) VALUES (?,?,?,?,?,?,?,?,?)",
            ("set_bench_2026_05_01_002", "bench_2026_05_01", 2,
             "Bench Press", 80.0, 5, 7.5,
             "2026-05-01T10:01:00+00:00", None),
        )
        # A correction row that supersedes set 002.
        conn.execute(
            "INSERT INTO gym_set (set_id, session_id, set_number, "
            "exercise_name, weight_kg, reps, rpe, ingested_at, "
            "supersedes_set_id) VALUES (?,?,?,?,?,?,?,?,?)",
            ("correction_001", "bench_2026_05_01", 2,
             "Bench Press", 82.5, 5, 8.0,
             "2026-05-01T10:02:00+00:00", "set_bench_2026_05_01_002"),
        )
        conn.commit()

        assert current_schema_version(conn) == 23

        # Apply migration 024 only.
        m024 = [m for m in all_migrations if m[0] == 24]
        assert m024, "migration 024 must exist"
        apply_pending_migrations(conn, m024)
        assert current_schema_version(conn) == 24

        # Verify rows survived with new set_ids and supersession reference.
        rows = conn.execute(
            "SELECT set_id, supersedes_set_id, set_number "
            "FROM gym_set WHERE session_id = ? ORDER BY ingested_at",
            ("bench_2026_05_01",),
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 3, f"expected 3 rows post-migration, got {len(rows)}"

    # Rows that were in the OLD deterministic format are rewritten to
    # include the bench-press slug. The correction row used a custom opaque
    # set_id ("correction_001") and is preserved as-is per the correction-
    # row contract (custom set_ids are intentionally non-deterministic;
    # rewriting them by the slug derivation would collide with the row
    # they supersede).
    deterministic_rows = [
        r for r in rows if not r["set_id"].startswith("correction_")
    ]
    assert len(deterministic_rows) == 2, (
        f"expected 2 OLD-format rows to be rewritten, got {len(deterministic_rows)}"
    )
    assert all("bench press" in r["set_id"] for r in deterministic_rows), (
        f"deterministic set_ids should include exercise slug: "
        f"{[r['set_id'] for r in deterministic_rows]}"
    )

    correction = next(r for r in rows if r["set_id"].startswith("correction_"))
    assert correction["set_id"] == "correction_001", (
        "correction row's custom set_id must be preserved across the migration"
    )
    # The correction's supersedes_set_id reference IS rewritten to point at
    # the NEW-format set_id of the row it supersedes.
    superseded_target = next(
        r for r in deterministic_rows if r["set_number"] == 2
    )
    assert correction["supersedes_set_id"] == superseded_target["set_id"], (
        f"supersession chain broken: correction supersedes "
        f"{correction['supersedes_set_id']!r} but the rewritten target is "
        f"{superseded_target['set_id']!r}"
    )


# ---------------------------------------------------------------------------
# Acceptance test 3 — migration 024 does NOT recover JSONL-dropped rows
# ---------------------------------------------------------------------------


def test_migration_024_does_not_recover_jsonl_dropped_rows(tmp_path: Path):
    """Per PLAN §2.A acceptance test 3: rows that exist in the JSONL audit
    log but were silently dropped at intake (pre-W-GYM-SETID PK collision)
    are NOT recovered by migration 024 alone. Recovery is the operator-only
    `hai state reproject --cascade-synthesis` path documented in §4 risk 3.
    """

    db_path = tmp_path / "state.db"
    base_dir = tmp_path / "intake"
    base_dir.mkdir()

    # Seed a pre-024 DB with only 3 rows (the Deadlift trio that survived the
    # PK collision in the maintainer's actual leg+back state). The remaining
    # 8 sets in JSONL are NOT in the DB — exactly the production state at
    # PLAN §2.A repro evidence.
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        from health_agent_infra.core.state.store import discover_migrations
        all_migrations = discover_migrations()
        pre_024 = [m for m in all_migrations if m[0] < 24]
        apply_pending_migrations(conn, pre_024)

        conn.execute(
            "INSERT INTO gym_session (session_id, user_id, as_of_date, "
            "session_name, notes, source, ingest_actor, submission_id, "
            "ingested_at, supersedes_session_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (SESSION_ID, USER, AS_OF.isoformat(), "Leg + back", "leg+back day",
             "user_manual", "cli", "m_gym_x",
             "2026-05-02T10:00:00+00:00", None),
        )
        for set_num in (1, 2, 3):
            conn.execute(
                "INSERT INTO gym_set (set_id, session_id, set_number, "
                "exercise_name, weight_kg, reps, rpe, ingested_at, "
                "supersedes_set_id) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    f"set_{SESSION_ID}_{set_num:03d}", SESSION_ID, set_num,
                    "Deadlift", 140.0, 5, 7.0 + 0.5 * (set_num - 1),
                    f"2026-05-02T10:0{set_num - 1}:00+00:00", None,
                ),
            )
        conn.commit()

        # Seed the full 11-set JSONL alongside the dropped-row state.
        _seed_jsonl(base_dir)

        # Apply migration 024 — must not silently re-read JSONL.
        m024 = [m for m in all_migrations if m[0] == 24]
        apply_pending_migrations(conn, m024)

        # Post-migration row count is still 3 (the 8 dropped JSONL sets were
        # NOT recovered by the schema migration).
        post_count = conn.execute(
            "SELECT COUNT(*) AS n FROM gym_set WHERE session_id = ?",
            (SESSION_ID,),
        ).fetchone()["n"]
    finally:
        conn.close()

    assert post_count == 3, (
        f"migration 024 must not recover JSONL-dropped rows; got {post_count} "
        f"rows post-migration (expected 3 — the original surviving Deadlift "
        f"trio). Recovery is the operator-only `hai state reproject` path."
    )


# ---------------------------------------------------------------------------
# Acceptance test 4 — `hai state reproject` recovers all 11 sets
# ---------------------------------------------------------------------------


def test_reproject_recovers_full_multi_exercise_jsonl_post_migration(
    tmp_path: Path,
):
    """Per PLAN §2.A acceptance test 4: `hai state reproject --base-dir
    <fixture-path> --cascade-synthesis` against a post-migration DB
    recovers all 11 sets from the multi-exercise JSONL fixture.
    """

    base, db = _init_intake_dirs(tmp_path)
    _seed_jsonl(base)

    rc = cli_main([
        "state", "reproject",
        "--base-dir", str(base),
        "--db-path", str(db),
        "--cascade-synthesis",
    ])
    assert rc == 0, f"reproject failed: rc={rc}"

    conn = open_connection(db)
    try:
        sets = conn.execute(
            "SELECT set_id, exercise_name, set_number FROM gym_set "
            "WHERE session_id = ? ORDER BY set_id",
            (SESSION_ID,),
        ).fetchall()
    finally:
        conn.close()

    assert len(sets) == 11, (
        f"reproject must recover all 11 JSONL sets; got {len(sets)}"
    )
    set_ids = {r["set_id"] for r in sets}
    assert len(set_ids) == 11, "reproject produced duplicate set_ids"
    # Every set_id includes the exercise slug.
    assert all(
        any(slug in sid for slug in (
            "deadlift", "back squat", "hamstring curl", "pull-up",
        ))
        for sid in set_ids
    ), f"reproject produced set_ids without exercise slug: {set_ids}"


# ---------------------------------------------------------------------------
# Acceptance test 5 — `hai backup` round-trip preserves gym_set
# ---------------------------------------------------------------------------


def test_backup_roundtrip_preserves_gym_set_post_migration(tmp_path: Path):
    """Per PLAN §2.A acceptance test 5: `hai backup` round-trip on the
    post-migration DB preserves the new-format gym_set rows."""

    base, db = _init_intake_dirs(tmp_path)
    _seed_jsonl(base)
    # Land all 11 sets via reproject first.
    rc = cli_main([
        "state", "reproject",
        "--base-dir", str(base),
        "--db-path", str(db),
        "--cascade-synthesis",
    ])
    assert rc == 0

    # Take a backup.
    bundle = tmp_path / "backup.tar.gz"
    rc = cli_main([
        "backup",
        "--db-path", str(db),
        "--base-dir", str(base),
        "--dest", str(bundle),
    ])
    assert rc == 0, f"backup failed: rc={rc}"
    assert bundle.exists(), "backup bundle not created"

    # Restore into a fresh location.
    restore_db = tmp_path / "restored_state.db"
    restore_base = tmp_path / "restored_intake"
    restore_base.mkdir()
    rc = cli_main([
        "restore",
        "--bundle", str(bundle),
        "--db-path", str(restore_db),
        "--base-dir", str(restore_base),
    ])
    assert rc == 0, f"restore failed: rc={rc}"

    conn = open_connection(restore_db)
    try:
        rows = conn.execute(
            "SELECT set_id FROM gym_set WHERE session_id = ? ORDER BY set_id",
            (SESSION_ID,),
        ).fetchall()
    finally:
        conn.close()

    assert len(rows) == 11, (
        f"backup round-trip lost gym_set rows; got {len(rows)} after "
        f"restore (expected 11)"
    )
