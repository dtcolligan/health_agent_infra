"""Phase 7C.2 — `hai intake nutrition` tests.

Contracts pinned:

  1. One invocation writes one JSONL line + one nutrition_intake_raw row +
     one accepted_nutrition_state_daily row.
  2. Re-running for the same (as_of_date, user_id) creates a NEW raw row
     with supersedes_submission_id pointing at the prior tail; the
     accepted row UPSERTs with corrected_at set.
  3. Missing required macros (--calories, --protein-g, --carbs-g, --fat-g)
     are rejected at the CLI boundary.
  4. Snapshot `nutrition.today.missingness='present'` after full intake.
  5. Projection is atomic — mid-flight failure rolls back both tables.
  6. DB absent is fail-soft — JSONL still lands.
  7. `hai state reproject --base-dir <d>` reads nutrition_intake.jsonl
     and rebuilds both tables round-trip.
  8. Nutrition-only reproject preserves other log groups' data.
  9. Other-group reproject preserves nutrition rows.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.state import (
    build_snapshot,
    initialize_database,
    open_connection,
    read_domain,
)


USER = "u_test"
AS_OF = date(2026, 4, 17)


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _init_intake_dirs(tmp_path: Path) -> tuple[Path, Path]:
    base = tmp_path / "intake"
    base.mkdir(parents=True, exist_ok=True)
    db = _init_db(tmp_path)
    return base, db


def _args(base: Path, db: Path, *, as_of: str = AS_OF.isoformat(),
          calories: float = 2200, protein: float = 180,
          carbs: float = 260, fat: float = 70) -> list[str]:
    return [
        "intake", "nutrition",
        "--calories", str(calories),
        "--protein-g", str(protein),
        "--carbs-g", str(carbs),
        "--fat-g", str(fat),
        "--as-of", as_of,
        "--user-id", USER,
        "--base-dir", str(base),
        "--db-path", str(db),
    ]


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_intake_nutrition_writes_jsonl_and_projects_both_tables(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    rc = cli_main(_args(base, db))
    assert rc == 0

    jsonl = base / "nutrition_intake.jsonl"
    lines = [json.loads(l) for l in jsonl.read_text().splitlines() if l.strip()]
    assert len(lines) == 1
    line = lines[0]
    assert line["user_id"] == USER
    assert line["as_of_date"] == AS_OF.isoformat()
    assert line["calories"] == 2200
    assert line["protein_g"] == 180
    assert line["carbs_g"] == 260
    assert line["fat_g"] == 70
    assert line["source"] == "user_manual"
    assert line["ingest_actor"] == "hai_cli_direct"
    assert line["supersedes_submission_id"] is None

    conn = open_connection(db)
    try:
        raw = conn.execute(
            "SELECT submission_id, calories, protein_g, supersedes_submission_id "
            "FROM nutrition_intake_raw WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchall()
        accepted = conn.execute(
            "SELECT calories, protein_g, carbs_g, fat_g, "
            "       derived_from, corrected_at, source, ingest_actor "
            "FROM accepted_nutrition_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchall()
    finally:
        conn.close()

    assert len(raw) == 1
    assert raw[0]["calories"] == 2200
    assert raw[0]["supersedes_submission_id"] is None

    assert len(accepted) == 1
    row = accepted[0]
    assert row["calories"] == 2200
    assert row["protein_g"] == 180
    assert row["carbs_g"] == 260
    assert row["fat_g"] == 70
    assert row["corrected_at"] is None  # first insert
    assert row["source"] == "user_manual"
    assert row["ingest_actor"] == "hai_cli_direct"
    # derived_from carries the raw submission_id
    derived = json.loads(row["derived_from"])
    assert derived == [raw[0]["submission_id"]]


def test_intake_nutrition_emits_envelope_with_ids(tmp_path: Path, capsys):
    base, db = _init_intake_dirs(tmp_path)
    rc = cli_main(_args(base, db))
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["user_id"] == USER
    assert out["as_of_date"] == AS_OF.isoformat()
    assert out["supersedes_submission_id"] is None
    assert out["submission_id"].startswith(f"m_nut_{AS_OF.isoformat()}_")


# ---------------------------------------------------------------------------
# Corrections
# ---------------------------------------------------------------------------

def test_intake_nutrition_second_run_stamps_supersedes_and_corrected_at(tmp_path: Path):
    """Second run for same day:
       - new raw row with supersedes_submission_id pointing at prior
       - accepted row UPSERTed with corrected_at set
       - accepted values reflect the NEW submission"""

    base, db = _init_intake_dirs(tmp_path)
    assert cli_main(_args(base, db, calories=2200, protein=180)) == 0
    assert cli_main(_args(base, db, calories=2400, protein=190)) == 0

    conn = open_connection(db)
    try:
        raws = conn.execute(
            "SELECT submission_id, calories, supersedes_submission_id "
            "FROM nutrition_intake_raw "
            "WHERE user_id = ? AND as_of_date = ? ORDER BY ingested_at",
            (USER, AS_OF.isoformat()),
        ).fetchall()
        accepted = conn.execute(
            "SELECT calories, protein_g, corrected_at, derived_from "
            "FROM accepted_nutrition_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    # Two raw rows, second supersedes first:
    assert len(raws) == 2
    first_id = raws[0]["submission_id"]
    second_id = raws[1]["submission_id"]
    assert raws[0]["supersedes_submission_id"] is None
    assert raws[1]["supersedes_submission_id"] == first_id

    # Accepted row reflects the latest (non-superseded) submission:
    assert accepted["calories"] == 2400
    assert accepted["protein_g"] == 190
    assert accepted["corrected_at"] is not None
    assert json.loads(accepted["derived_from"]) == [second_id]


def test_intake_nutrition_third_run_chains_correction(tmp_path: Path):
    """Three-correction chain: each new submission supersedes the prior tail."""

    base, db = _init_intake_dirs(tmp_path)
    assert cli_main(_args(base, db, calories=2200)) == 0
    assert cli_main(_args(base, db, calories=2300)) == 0
    assert cli_main(_args(base, db, calories=2400)) == 0

    conn = open_connection(db)
    try:
        raws = conn.execute(
            "SELECT submission_id, calories, supersedes_submission_id "
            "FROM nutrition_intake_raw "
            "WHERE user_id = ? AND as_of_date = ? ORDER BY ingested_at",
            (USER, AS_OF.isoformat()),
        ).fetchall()
        accepted_cals = conn.execute(
            "SELECT calories FROM accepted_nutrition_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()["calories"]
    finally:
        conn.close()

    assert len(raws) == 3
    # Chain: first.supersedes is NULL; each subsequent supersedes the
    # immediately-previous.
    assert raws[0]["supersedes_submission_id"] is None
    assert raws[1]["supersedes_submission_id"] == raws[0]["submission_id"]
    assert raws[2]["supersedes_submission_id"] == raws[1]["submission_id"]
    assert accepted_cals == 2400


# ---------------------------------------------------------------------------
# Validation at the CLI boundary
# ---------------------------------------------------------------------------

def test_intake_nutrition_missing_required_macro_is_rejected(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    # Argparse required=True on all 4 macros — argparse raises SystemExit(2).
    with pytest.raises(SystemExit) as excinfo:
        cli_main([
            "intake", "nutrition",
            "--calories", "2200",
            "--protein-g", "180",
            # carbs-g missing
            "--fat-g", "70",
            "--as-of", AS_OF.isoformat(),
            "--user-id", USER,
            "--base-dir", str(base),
            "--db-path", str(db),
        ])
    assert excinfo.value.code == 2
    assert not (base / "nutrition_intake.jsonl").exists()


def test_intake_nutrition_negative_value_is_rejected(tmp_path: Path, capsys):
    base, db = _init_intake_dirs(tmp_path)
    rc = cli_main([
        "intake", "nutrition",
        "--calories", "-100",
        "--protein-g", "180", "--carbs-g", "260", "--fat-g", "70",
        "--as-of", AS_OF.isoformat(), "--user-id", USER,
        "--base-dir", str(base), "--db-path", str(db),
    ])
    assert rc == 2
    assert "must be >= 0" in capsys.readouterr().err
    assert not (base / "nutrition_intake.jsonl").exists()


# ---------------------------------------------------------------------------
# Optional fields
# ---------------------------------------------------------------------------

def test_intake_nutrition_optional_fields_propagate(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    rc = cli_main(_args(base, db) + ["--hydration-l", "3.2", "--meals-count", "4"])
    assert rc == 0
    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT hydration_l, meals_count FROM accepted_nutrition_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()
    assert row["hydration_l"] == 3.2
    assert row["meals_count"] == 4


# ---------------------------------------------------------------------------
# Snapshot integration
# ---------------------------------------------------------------------------

def test_intake_nutrition_snapshot_nutrition_present_after_intake(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    assert cli_main(_args(base, db)) == 0
    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),  # day well-closed
        )
    finally:
        conn.close()
    assert snap["nutrition"]["missingness"] == "present"
    assert snap["nutrition"]["today"]["calories"] == 2200
    assert snap["nutrition"]["today"]["protein_g"] == 180


# ---------------------------------------------------------------------------
# Atomicity
# ---------------------------------------------------------------------------

def test_intake_nutrition_projection_is_atomic_on_middle_failure(tmp_path, monkeypatch):
    """If the accepted-state projector raises mid-transaction, the
    nutrition_intake_raw insert must roll back."""

    base, db = _init_intake_dirs(tmp_path)
    import health_agent_infra.state as state_pkg

    def boom(*args, **kwargs):
        raise RuntimeError("injected accepted nutrition projection failure")

    monkeypatch.setattr(
        state_pkg, "project_accepted_nutrition_state_daily", boom,
    )

    rc = cli_main(_args(base, db))
    assert rc == 0  # fail-soft

    # JSONL captured (audit boundary was before DB transaction).
    assert (base / "nutrition_intake.jsonl").exists()
    assert len((base / "nutrition_intake.jsonl").read_text().splitlines()) == 1

    conn = open_connection(db)
    try:
        n_raw = conn.execute(
            "SELECT COUNT(*) FROM nutrition_intake_raw"
        ).fetchone()[0]
        n_accepted = conn.execute(
            "SELECT COUNT(*) FROM accepted_nutrition_state_daily"
        ).fetchone()[0]
    finally:
        conn.close()
    assert n_raw == 0, "nutrition_intake_raw leaked past rollback"
    assert n_accepted == 0


def test_intake_nutrition_db_absent_is_failsoft(tmp_path: Path, capsys):
    base = tmp_path / "intake"
    base.mkdir()
    missing_db = tmp_path / "none.db"
    rc = cli_main(_args(base, missing_db))
    assert rc == 0
    assert "projection skipped" in capsys.readouterr().err
    # JSONL still landed:
    assert (base / "nutrition_intake.jsonl").exists()


# ---------------------------------------------------------------------------
# Reproject
# ---------------------------------------------------------------------------

def test_state_reproject_rebuilds_nutrition_tables_from_jsonl(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    # Two days, two submissions per day (correction chain).
    assert cli_main(_args(base, db, as_of="2026-04-17", calories=2200)) == 0
    assert cli_main(_args(base, db, as_of="2026-04-17", calories=2400)) == 0
    assert cli_main(_args(base, db, as_of="2026-04-18", calories=2100)) == 0

    rc = cli_main([
        "state", "reproject",
        "--base-dir", str(base),
        "--db-path", str(db),
    ])
    assert rc == 0

    conn = open_connection(db)
    try:
        raw_count = conn.execute(
            "SELECT COUNT(*) FROM nutrition_intake_raw"
        ).fetchone()[0]
        days = conn.execute(
            "SELECT as_of_date, calories FROM accepted_nutrition_state_daily "
            "ORDER BY as_of_date"
        ).fetchall()
        # Check correction chain preserved on 2026-04-17:
        chain = conn.execute(
            "SELECT supersedes_submission_id FROM nutrition_intake_raw "
            "WHERE as_of_date = ? ORDER BY ingested_at",
            ("2026-04-17",),
        ).fetchall()
    finally:
        conn.close()

    assert raw_count == 3
    assert [(r["as_of_date"], r["calories"]) for r in days] == [
        ("2026-04-17", 2400),  # latest non-superseded wins
        ("2026-04-18", 2100),
    ]
    # First row of 2026-04-17 has no predecessor; second supersedes first.
    assert chain[0]["supersedes_submission_id"] is None
    assert chain[1]["supersedes_submission_id"] is not None


def test_state_reproject_nutrition_only_preserves_other_groups(tmp_path: Path):
    """Regression guard for the 7C.1 scope fix extended to nutrition:
    reprojecting a base_dir that contains only nutrition_intake.jsonl
    must not touch gym or recommendation tables."""

    from datetime import datetime as _dt
    from datetime import timezone as _tz
    from health_agent_infra.schemas import FollowUp, TrainingRecommendation
    from health_agent_infra.state import (
        project_recommendation, reproject_from_jsonl,
    )

    db = _init_db(tmp_path)
    base = tmp_path / "intake"
    base.mkdir()

    # Seed a recommendation AND a gym session (directly via SQL to keep
    # their audit JSONLs out of base_dir).
    rec = TrainingRecommendation(
        schema_version="training_recommendation.v1",
        recommendation_id="rec_probe",
        user_id=USER,
        issued_at=_dt(2026, 4, 17, 8, tzinfo=_tz.utc),
        for_date=AS_OF,
        action="proceed_with_planned_session",
        action_detail=None, rationale=["x"], confidence="moderate",
        uncertainty=[],
        follow_up=FollowUp(
            review_at=_dt(2026, 4, 18, 7, tzinfo=_tz.utc),
            review_question="q", review_event_id="rev_probe",
        ),
        policy_decisions=[], bounded=True,
    )
    conn = open_connection(db)
    try:
        project_recommendation(conn, rec)
        # Seed a gym_session + gym_set + accepted directly so they exist
        # without a gym JSONL in base_dir.
        conn.execute(
            "INSERT INTO gym_session (session_id, user_id, as_of_date, "
            "session_name, source, ingest_actor, submission_id, ingested_at) "
            "VALUES ('s_pre', ?, ?, 'pre', 'user_manual', 'hai_cli_direct', "
            "'m_pre', '2026-04-17T10:00:00+00:00')",
            (USER, AS_OF.isoformat()),
        )
        conn.execute(
            "INSERT INTO gym_set (set_id, session_id, set_number, "
            "exercise_name, weight_kg, reps, ingested_at) "
            "VALUES ('set_s_pre_001', 's_pre', 1, 'Bench', 80, 5, "
            "'2026-04-17T10:00:00+00:00')"
        )
        conn.execute(
            "INSERT INTO accepted_resistance_training_state_daily "
            "(as_of_date, user_id, session_count, total_sets, "
            "total_volume_kg_reps, exercises, derived_from, source, "
            "ingest_actor, projected_at) "
            "VALUES (?, ?, 1, 1, 400, '[\"Bench\"]', '[\"s_pre\"]', "
            "'user_manual', 'hai_cli_direct', '2026-04-17T10:00:00+00:00')",
            (AS_OF.isoformat(), USER),
        )
        conn.commit()
    finally:
        conn.close()

    # Drop ONLY nutrition JSONL into base_dir.
    (base / "nutrition_intake.jsonl").write_text(json.dumps({
        "submission_id": "m_nut_only",
        "user_id": USER, "as_of_date": AS_OF.isoformat(),
        "calories": 2200, "protein_g": 180, "carbs_g": 260, "fat_g": 70,
        "hydration_l": None, "meals_count": None,
        "source": "user_manual", "ingest_actor": "hai_cli_direct",
        "submitted_at": "2026-04-17T10:00:00+00:00",
        "supersedes_submission_id": None,
    }) + "\n")

    conn = open_connection(db)
    try:
        counts = reproject_from_jsonl(conn, base)
        rec_n = conn.execute("SELECT COUNT(*) FROM recommendation_log").fetchone()[0]
        gym_n = conn.execute("SELECT COUNT(*) FROM gym_session").fetchone()[0]
        set_n = conn.execute("SELECT COUNT(*) FROM gym_set").fetchone()[0]
        nut_n = conn.execute("SELECT COUNT(*) FROM nutrition_intake_raw").fetchone()[0]
    finally:
        conn.close()

    # Nutrition rebuilt, other groups untouched:
    assert counts["nutrition_intake_raw"] == 1
    assert counts["recommendations"] == 0
    assert counts["gym_sessions"] == 0
    assert rec_n == 1, "recommendation_log wiped by nutrition-only reproject"
    assert gym_n == 1, "gym_session wiped by nutrition-only reproject"
    assert set_n == 1
    assert nut_n == 1


def test_state_reproject_other_group_only_preserves_nutrition_rows(tmp_path: Path):
    """Inverse: gym-only reproject must not touch existing nutrition rows."""

    base, db = _init_intake_dirs(tmp_path)
    # Seed nutrition via the full CLI (writes nutrition_intake.jsonl).
    assert cli_main(_args(base, db, calories=2000)) == 0

    # Move nutrition JSONL out so the reproject doesn't see it.
    (base / "nutrition_intake.jsonl").rename(tmp_path / "moved_nut.jsonl")
    # Drop a gym JSONL.
    (base / "gym_sessions.jsonl").write_text(json.dumps({
        "submission_id": "m", "session_id": "sx", "user_id": USER,
        "as_of_date": AS_OF.isoformat(), "session_name": "x", "notes": None,
        "set_number": 1, "exercise_name": "Bench",
        "weight_kg": 80, "reps": 5, "rpe": None,
        "source": "user_manual", "ingest_actor": "hai_cli_direct",
        "submitted_at": "2026-04-17T10:00:00+00:00",
    }) + "\n")

    from health_agent_infra.state import reproject_from_jsonl

    conn = open_connection(db)
    try:
        counts = reproject_from_jsonl(conn, base)
        nut_raw = conn.execute(
            "SELECT COUNT(*) FROM nutrition_intake_raw"
        ).fetchone()[0]
        nut_accepted = conn.execute(
            "SELECT calories FROM accepted_nutrition_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    assert counts["gym_sessions"] == 1
    assert counts["nutrition_intake_raw"] == 0  # group not touched
    assert nut_raw == 1, "nutrition_intake_raw wiped by gym-only reproject"
    assert nut_accepted["calories"] == 2000
