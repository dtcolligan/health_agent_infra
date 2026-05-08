"""Phase 7C.1 — `hai intake gym` tests.

Contracts pinned:

  1. Per-set mode and bulk mode both produce the same row shape in
     gym_session + gym_set + accepted_resistance_training_state_daily.
  2. JSONL audit at <base_dir>/gym_sessions.jsonl is one line per set
     with session metadata inlined.
  3. Re-invocation with same args is idempotent (deterministic set_id
     + INSERT OR IGNORE semantics).
  4. Snapshot `gym.today.missingness='present'` after intake.
  5. Projection is atomic — mid-flight failure rolls back all three
     tables; JSONL stays (audit boundary).
  6. DB absent is fail-soft — JSONL still lands.
  7. `hai state reproject --base-dir <d>` reads gym_sessions.jsonl
     and rebuilds all three tables round-trip.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import (
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


# ---------------------------------------------------------------------------
# Per-set mode
# ---------------------------------------------------------------------------

def test_intake_gym_per_set_writes_jsonl_and_projects_db(tmp_path: Path, capsys):
    base, db = _init_intake_dirs(tmp_path)

    rc = cli_main([
        "intake", "gym",
        "--session-id", "bench_2026_04_17",
        "--session-name", "Bench day",
        "--exercise", "Bench Press",
        "--set-number", "1",
        "--weight-kg", "80.0",
        "--reps", "5",
        "--rpe", "7.0",
        "--as-of", AS_OF.isoformat(),
        "--user-id", USER,
        "--base-dir", str(base),
        "--db-path", str(db),
    ])
    assert rc == 0

    # JSONL line present with session metadata inline.
    jsonl = base / "gym_sessions.jsonl"
    assert jsonl.exists()
    lines = [json.loads(l) for l in jsonl.read_text().splitlines() if l.strip()]
    assert len(lines) == 1
    ln = lines[0]
    assert ln["session_id"] == "bench_2026_04_17"
    assert ln["session_name"] == "Bench day"
    assert ln["user_id"] == USER
    assert ln["as_of_date"] == AS_OF.isoformat()
    assert ln["set_number"] == 1
    assert ln["exercise_name"] == "Bench Press"
    assert ln["weight_kg"] == 80.0
    assert ln["reps"] == 5
    assert ln["rpe"] == 7.0
    assert ln["source"] == "user_manual"
    assert ln["ingest_actor"] == "hai_cli_direct"

    # DB has the session + set + accepted daily.
    conn = open_connection(db)
    try:
        sessions = conn.execute(
            "SELECT * FROM gym_session WHERE session_id = ?",
            ("bench_2026_04_17",),
        ).fetchall()
        sets = conn.execute(
            "SELECT * FROM gym_set WHERE session_id = ? ORDER BY set_number",
            ("bench_2026_04_17",),
        ).fetchall()
        accepted = conn.execute(
            "SELECT * FROM accepted_resistance_training_state_daily "
            "WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchall()
    finally:
        conn.close()

    assert len(sessions) == 1
    assert sessions[0]["session_name"] == "Bench day"
    assert sessions[0]["source"] == "user_manual"
    assert sessions[0]["ingest_actor"] == "hai_cli_direct"

    assert len(sets) == 1
    assert sets[0]["weight_kg"] == 80.0
    assert sets[0]["reps"] == 5
    assert sets[0]["rpe"] == 7.0
    # v0.1.15 W-GYM-SETID: set_id includes the exercise slug between
    # session_id and the zero-padded set_number to prevent multi-exercise
    # PK collisions.
    assert sets[0]["set_id"] == "set_bench_2026_04_17_bench press_001"

    assert len(accepted) == 1
    assert accepted[0]["session_count"] == 1
    assert accepted[0]["total_sets"] == 1
    assert accepted[0]["total_volume_kg_reps"] == pytest.approx(400.0)  # 80*5
    assert json.loads(accepted[0]["exercises"]) == ["Bench Press"]
    assert accepted[0]["corrected_at"] is None


def test_intake_gym_multiple_sets_same_session_accumulate(tmp_path: Path):
    """Re-invoking with the same session_id and a new set_number adds to
    the same session and the accepted aggregate tracks total volume."""

    base, db = _init_intake_dirs(tmp_path)
    common = [
        "intake", "gym",
        "--session-id", "bench_2026_04_17",
        "--session-name", "Bench day",
        "--exercise", "Bench Press",
        "--weight-kg", "80", "--reps", "5",
        "--as-of", AS_OF.isoformat(),
        "--user-id", USER,
        "--base-dir", str(base),
        "--db-path", str(db),
    ]
    assert cli_main(common + ["--set-number", "1"]) == 0
    assert cli_main(common + ["--set-number", "2"]) == 0
    assert cli_main(common + ["--set-number", "3"]) == 0

    conn = open_connection(db)
    try:
        sets = conn.execute(
            "SELECT set_number FROM gym_set WHERE session_id = ? "
            "ORDER BY set_number",
            ("bench_2026_04_17",),
        ).fetchall()
        accepted = conn.execute(
            "SELECT session_count, total_sets, total_volume_kg_reps "
            "FROM accepted_resistance_training_state_daily "
            "WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchone()
    finally:
        conn.close()

    assert [r["set_number"] for r in sets] == [1, 2, 3]
    assert accepted["session_count"] == 1
    assert accepted["total_sets"] == 3
    assert accepted["total_volume_kg_reps"] == pytest.approx(1200.0)  # 3*80*5


# ---------------------------------------------------------------------------
# Bulk mode
# ---------------------------------------------------------------------------

def test_intake_gym_bulk_mode_writes_all_sets(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    payload = {
        "session_id": "full_body_2026_04_17",
        "session_name": "Full body",
        "as_of_date": AS_OF.isoformat(),
        "notes": "Felt strong.",
        "sets": [
            {"set_number": 1, "exercise_name": "Squat", "weight_kg": 100, "reps": 5, "rpe": 7},
            {"set_number": 2, "exercise_name": "Squat", "weight_kg": 100, "reps": 5, "rpe": 7.5},
            {"set_number": 3, "exercise_name": "Bench Press", "weight_kg": 80, "reps": 5},
            {"set_number": 4, "exercise_name": "Row", "weight_kg": 70, "reps": 8},
        ],
    }
    p = tmp_path / "session.json"
    p.write_text(json.dumps(payload))

    rc = cli_main([
        "intake", "gym",
        "--session-json", str(p),
        "--user-id", USER,
        "--base-dir", str(base),
        "--db-path", str(db),
    ])
    assert rc == 0

    jsonl = base / "gym_sessions.jsonl"
    lines = [json.loads(l) for l in jsonl.read_text().splitlines() if l.strip()]
    assert len(lines) == 4
    assert all(ln["session_id"] == "full_body_2026_04_17" for ln in lines)

    conn = open_connection(db)
    try:
        sessions = conn.execute(
            "SELECT notes FROM gym_session WHERE session_id = ?",
            ("full_body_2026_04_17",),
        ).fetchall()
        sets_count = conn.execute(
            "SELECT COUNT(*) AS n FROM gym_set WHERE session_id = ?",
            ("full_body_2026_04_17",),
        ).fetchone()["n"]
        accepted = conn.execute(
            "SELECT session_count, total_sets, total_volume_kg_reps, exercises "
            "FROM accepted_resistance_training_state_daily "
            "WHERE as_of_date = ? AND user_id = ?",
            (AS_OF.isoformat(), USER),
        ).fetchone()
    finally:
        conn.close()

    assert sessions[0]["notes"] == "Felt strong."
    assert sets_count == 4
    assert accepted["total_sets"] == 4
    assert accepted["session_count"] == 1
    # Volume: 2*100*5 + 80*5 + 70*8 = 1000 + 400 + 560 = 1960
    assert accepted["total_volume_kg_reps"] == pytest.approx(1960.0)
    assert sorted(json.loads(accepted["exercises"])) == ["Bench Press", "Row", "Squat"]


def test_intake_gym_bulk_mode_rejects_malformed_json(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"session_id": "x"}))  # missing 'sets'
    rc = cli_main([
        "intake", "gym", "--session-json", str(bad),
        "--user-id", USER, "--base-dir", str(base), "--db-path", str(db),
    ])
    assert rc == exit_codes.USER_INPUT
    assert not (base / "gym_sessions.jsonl").exists()


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

def test_intake_gym_re_invocation_with_same_args_is_idempotent_on_db(tmp_path: Path):
    """Deterministic set_id + INSERT OR IGNORE semantics: running the same
    CLI twice with identical args produces one session + one set in the DB
    (JSONL log will contain two lines — the raw audit keeps every attempt)."""

    base, db = _init_intake_dirs(tmp_path)
    args = [
        "intake", "gym",
        "--session-id", "bench_x",
        "--exercise", "Bench", "--set-number", "1",
        "--weight-kg", "80", "--reps", "5",
        "--as-of", AS_OF.isoformat(), "--user-id", USER,
        "--base-dir", str(base), "--db-path", str(db),
    ]
    assert cli_main(args) == 0
    assert cli_main(args) == 0  # duplicate

    conn = open_connection(db)
    try:
        n_sessions = conn.execute(
            "SELECT COUNT(*) FROM gym_session WHERE session_id = 'bench_x'"
        ).fetchone()[0]
        n_sets = conn.execute(
            "SELECT COUNT(*) FROM gym_set WHERE session_id = 'bench_x'"
        ).fetchone()[0]
    finally:
        conn.close()

    assert n_sessions == 1
    assert n_sets == 1
    # JSONL still captures both submissions (audit is append-only):
    jsonl = base / "gym_sessions.jsonl"
    assert len(jsonl.read_text().splitlines()) == 2


# ---------------------------------------------------------------------------
# Snapshot integration
# ---------------------------------------------------------------------------

def test_intake_gym_snapshot_gym_domain_present_after_intake(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    assert cli_main([
        "intake", "gym",
        "--session-id", "s1", "--exercise", "Bench", "--set-number", "1",
        "--weight-kg", "80", "--reps", "5",
        "--as-of", AS_OF.isoformat(), "--user-id", USER,
        "--base-dir", str(base), "--db-path", str(db),
    ]) == 0

    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),
        )
    finally:
        conn.close()

    assert snap["gym"]["missingness"] == "present"
    assert snap["gym"]["today"]["session_count"] == 1
    assert snap["gym"]["today"]["total_sets"] == 1


# ---------------------------------------------------------------------------
# Atomicity — mid-flight projector failure rolls back the whole transaction
# ---------------------------------------------------------------------------

def test_intake_gym_projection_is_atomic_on_middle_failure(tmp_path, monkeypatch):
    """If the set projector raises mid-transaction, the session insert
    must roll back. JSONL already landed (audit boundary); reproject from
    that JSONL rebuilds cleanly."""

    base, db = _init_intake_dirs(tmp_path)

    import health_agent_infra.core.state as state_pkg

    def boom(*args, **kwargs):
        raise RuntimeError("injected gym_set projection failure")

    monkeypatch.setattr(state_pkg, "project_gym_set", boom)

    rc = cli_main([
        "intake", "gym",
        "--session-id", "s_fail", "--exercise", "Squat", "--set-number", "1",
        "--weight-kg", "100", "--reps", "5",
        "--as-of", AS_OF.isoformat(), "--user-id", USER,
        "--base-dir", str(base), "--db-path", str(db),
    ])
    # Fail-soft at CLI boundary.
    assert rc == 0

    # JSONL wrote — audit boundary is before the DB transaction.
    assert (base / "gym_sessions.jsonl").exists()
    assert len((base / "gym_sessions.jsonl").read_text().splitlines()) == 1

    conn = open_connection(db)
    try:
        # Everything rolled back.
        n_sessions = conn.execute(
            "SELECT COUNT(*) FROM gym_session"
        ).fetchone()[0]
        n_sets = conn.execute(
            "SELECT COUNT(*) FROM gym_set"
        ).fetchone()[0]
        n_accepted = conn.execute(
            "SELECT COUNT(*) FROM accepted_resistance_training_state_daily"
        ).fetchone()[0]
    finally:
        conn.close()

    assert n_sessions == 0, "gym_session row leaked past rollback"
    assert n_sets == 0
    assert n_accepted == 0


def test_intake_gym_db_absent_is_failsoft(tmp_path, capsys):
    """No DB file ⇒ JSONL still lands, stderr warning, exit 0."""

    base = tmp_path / "intake"
    base.mkdir(parents=True, exist_ok=True)
    missing_db = tmp_path / "no_such.db"

    rc = cli_main([
        "intake", "gym",
        "--session-id", "s1", "--exercise", "Bench", "--set-number", "1",
        "--weight-kg", "80", "--reps", "5",
        "--as-of", AS_OF.isoformat(), "--user-id", USER,
        "--base-dir", str(base), "--db-path", str(missing_db),
    ])
    assert rc == 0
    captured = capsys.readouterr()
    assert "projection skipped" in captured.err
    assert (base / "gym_sessions.jsonl").exists()


# ---------------------------------------------------------------------------
# Reproject round-trip
# ---------------------------------------------------------------------------

def test_state_reproject_rebuilds_gym_tables_from_jsonl(tmp_path: Path):
    """After writing gym intake, wipe the DB and run
    `hai state reproject --base-dir`. Every table is restored from JSONL."""

    base, db = _init_intake_dirs(tmp_path)
    # Two sessions on two days.
    payload_a = {
        "session_id": "sess_a", "session_name": "Day A",
        "as_of_date": "2026-04-17",
        "sets": [
            {"set_number": 1, "exercise_name": "Squat", "weight_kg": 100, "reps": 5},
            {"set_number": 2, "exercise_name": "Squat", "weight_kg": 100, "reps": 5},
        ],
    }
    payload_b = {
        "session_id": "sess_b", "session_name": "Day B",
        "as_of_date": "2026-04-18",
        "sets": [
            {"set_number": 1, "exercise_name": "Bench", "weight_kg": 80, "reps": 5},
        ],
    }
    pa = tmp_path / "a.json"; pa.write_text(json.dumps(payload_a))
    pb = tmp_path / "b.json"; pb.write_text(json.dumps(payload_b))
    assert cli_main([
        "intake", "gym", "--session-json", str(pa),
        "--user-id", USER, "--base-dir", str(base), "--db-path", str(db),
    ]) == 0
    assert cli_main([
        "intake", "gym", "--session-json", str(pb),
        "--user-id", USER, "--base-dir", str(base), "--db-path", str(db),
    ]) == 0

    # Wipe only the projected tables via reproject (it truncates).
    rc = cli_main([
        "state", "reproject",
        "--base-dir", str(base),
        "--db-path", str(db),
    ])
    assert rc == 0

    conn = open_connection(db)
    try:
        n_sess = conn.execute("SELECT COUNT(*) FROM gym_session").fetchone()[0]
        n_sets = conn.execute("SELECT COUNT(*) FROM gym_set").fetchone()[0]
        days = conn.execute(
            "SELECT as_of_date, session_count, total_sets "
            "FROM accepted_resistance_training_state_daily "
            "ORDER BY as_of_date"
        ).fetchall()
    finally:
        conn.close()

    assert n_sess == 2
    assert n_sets == 3
    assert [(r["as_of_date"], r["session_count"], r["total_sets"]) for r in days] == [
        ("2026-04-17", 1, 2),
        ("2026-04-18", 1, 1),
    ]


def test_state_reproject_gym_only_preserves_recommendation_rows(tmp_path: Path):
    """Scope-bug regression guard. With a recommendation already projected
    into the DB and only `gym_sessions.jsonl` present in the base-dir,
    reproject must rebuild gym tables but must NOT touch recommendation_log
    / review_event / review_outcome. The prior implementation truncated
    all projection tables unconditionally, silently wiping unrelated
    projected data."""

    from datetime import datetime as _dt
    from datetime import timezone as _tz
    from health_agent_infra.core.schemas import (
        FollowUp, ReviewEvent, ReviewOutcome,
    )
    from health_agent_infra.domains.recovery.schemas import TrainingRecommendation
    from health_agent_infra.core.state import (
        project_recommendation, project_review_event, project_review_outcome,
        reproject_from_jsonl,
    )

    db = _init_db(tmp_path)
    base = tmp_path / "intake"
    base.mkdir()

    # Seed the DB with a recommendation + review event + outcome — as if
    # `hai writeback` + `hai review schedule` + `hai review record` had
    # already projected, but the JSONL audit files happen not to be under
    # the same base_dir the gym flow uses.
    rec = TrainingRecommendation(
        schema_version="training_recommendation.v1",
        recommendation_id="rec_probe_01",
        user_id=USER,
        issued_at=_dt(2026, 4, 17, 8, 0, tzinfo=_tz.utc),
        for_date=AS_OF,
        action="proceed_with_planned_session",
        action_detail=None,
        rationale=["probe"],
        confidence="moderate",
        uncertainty=[],
        follow_up=FollowUp(
            review_at=_dt(2026, 4, 18, 7, 0, tzinfo=_tz.utc),
            review_question="q", review_event_id="rev_probe_01",
        ),
        policy_decisions=[],
        bounded=True,
    )
    ev = ReviewEvent(
        review_event_id="rev_probe_01", recommendation_id="rec_probe_01",
        user_id=USER,
        review_at=_dt(2026, 4, 18, 7, 0, tzinfo=_tz.utc),
        review_question="q",
    )
    outcome = ReviewOutcome(
        review_event_id="rev_probe_01", recommendation_id="rec_probe_01",
        user_id=USER,
        recorded_at=_dt(2026, 4, 18, 8, 0, tzinfo=_tz.utc),
        followed_recommendation=True,
        self_reported_improvement=True,
        free_text=None,
    )
    conn = open_connection(db)
    try:
        project_recommendation(conn, rec)
        project_review_event(conn, ev)
        project_review_outcome(conn, outcome)
    finally:
        conn.close()

    # Write a gym JSONL into base_dir (no recommendation_log.jsonl etc).
    (base / "gym_sessions.jsonl").write_text(json.dumps({
        "submission_id": "m_gym_x", "session_id": "s_gym",
        "user_id": USER, "as_of_date": AS_OF.isoformat(),
        "session_name": "Gym", "notes": None,
        "set_number": 1, "exercise_name": "Bench",
        "weight_kg": 80, "reps": 5, "rpe": None,
        "source": "user_manual", "ingest_actor": "hai_cli_direct",
        "submitted_at": "2026-04-17T10:00:00+00:00",
    }) + "\n")

    conn = open_connection(db)
    try:
        counts = reproject_from_jsonl(conn, base)
        rec_n = conn.execute("SELECT COUNT(*) FROM recommendation_log").fetchone()[0]
        ev_n = conn.execute("SELECT COUNT(*) FROM review_event").fetchone()[0]
        out_n = conn.execute("SELECT COUNT(*) FROM review_outcome").fetchone()[0]
        gym_n = conn.execute("SELECT COUNT(*) FROM gym_session").fetchone()[0]
        set_n = conn.execute("SELECT COUNT(*) FROM gym_set").fetchone()[0]
    finally:
        conn.close()

    # Gym group was rebuilt from JSONL:
    assert counts["gym_sessions"] == 1
    assert counts["gym_sets"] == 1
    assert gym_n == 1 and set_n == 1
    # Recommendation group was UNTOUCHED — this is the scope-fix contract:
    assert counts["recommendations"] == 0
    assert counts["review_events"] == 0
    assert counts["review_outcomes"] == 0
    assert rec_n == 1, "recommendation_log was silently wiped by gym-only reproject"
    assert ev_n == 1, "review_event was silently wiped by gym-only reproject"
    assert out_n == 1, "review_outcome was silently wiped by gym-only reproject"


def test_state_reproject_rec_only_preserves_gym_rows(tmp_path: Path):
    """Inverse scope guard. With gym rows projected, a reproject over a
    base_dir containing only recommendation JSONL must not truncate gym
    tables."""

    from health_agent_infra.core.state import reproject_from_jsonl

    base, db = _init_intake_dirs(tmp_path)
    # Seed gym rows via a full intake.
    assert cli_main([
        "intake", "gym",
        "--session-id", "pre_gym", "--exercise", "Squat", "--set-number", "1",
        "--weight-kg", "100", "--reps", "5",
        "--as-of", AS_OF.isoformat(), "--user-id", USER,
        "--base-dir", str(base), "--db-path", str(db),
    ]) == 0

    # Move gym_sessions.jsonl out of the way, drop a recommendation-only log.
    (base / "gym_sessions.jsonl").rename(tmp_path / "moved_gym.jsonl")
    (base / "recommendation_log.jsonl").write_text(json.dumps({
        "recommendation_id": "rec_rescope_01",
        "user_id": USER, "for_date": AS_OF.isoformat(),
        "issued_at": "2026-04-17T08:00:00+00:00",
        "action": "proceed_with_planned_session",
        "confidence": "moderate", "bounded": True,
        "rationale": ["rescope"],
        "uncertainty": [],
        "follow_up": {
            "review_at": "2026-04-18T07:00:00+00:00",
            "review_question": "q",
            "review_event_id": "rev_rescope_01",
        },
        "policy_decisions": [],
        "schema_version": "training_recommendation.v1",
        "action_detail": None,
    }) + "\n")

    conn = open_connection(db)
    try:
        counts = reproject_from_jsonl(conn, base)
        rec_n = conn.execute("SELECT COUNT(*) FROM recommendation_log").fetchone()[0]
        gym_n = conn.execute("SELECT COUNT(*) FROM gym_session").fetchone()[0]
        set_n = conn.execute("SELECT COUNT(*) FROM gym_set").fetchone()[0]
        accepted_n = conn.execute(
            "SELECT COUNT(*) FROM accepted_resistance_training_state_daily"
        ).fetchone()[0]
    finally:
        conn.close()

    # Recommendation group rebuilt:
    assert counts["recommendations"] == 1
    assert rec_n == 1
    # Gym group UNTOUCHED — gym_sessions.jsonl wasn't present this run:
    assert counts["gym_sessions"] == 0
    assert counts["gym_sets"] == 0
    assert gym_n == 1, "gym_session was silently wiped by recommendation-only reproject"
    assert set_n == 1
    assert accepted_n == 1


def test_state_reproject_accepts_gym_only_base_dir(tmp_path: Path):
    """Reproject must not refuse a base-dir that contains only gym
    JSONL — the fail-closed check covers any of the four expected logs."""

    from health_agent_infra.core.state import reproject_from_jsonl, ReprojectBaseDirError

    db = _init_db(tmp_path)
    base = tmp_path / "intake"
    base.mkdir()

    # Empty dir → still refuses
    conn = open_connection(db)
    try:
        with pytest.raises(ReprojectBaseDirError):
            reproject_from_jsonl(conn, base)
    finally:
        conn.close()

    # Drop a minimal gym JSONL → accepted.
    (base / "gym_sessions.jsonl").write_text(json.dumps({
        "submission_id": "m_gym_x",
        "session_id": "s_only",
        "user_id": USER,
        "as_of_date": AS_OF.isoformat(),
        "session_name": "x", "notes": None,
        "set_number": 1, "exercise_name": "Bench",
        "weight_kg": 80, "reps": 5, "rpe": None,
        "source": "user_manual", "ingest_actor": "hai_cli_direct",
        "submitted_at": "2026-04-17T10:00:00+00:00",
    }) + "\n")

    conn = open_connection(db)
    try:
        counts = reproject_from_jsonl(conn, base)
    finally:
        conn.close()
    assert counts["gym_sessions"] == 1
    assert counts["gym_sets"] == 1
