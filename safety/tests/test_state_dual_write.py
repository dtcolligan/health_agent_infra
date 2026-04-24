"""Tests for Phase 7A.2 — dual-write + reproject.

Contract (per plan Pre-flight):
  - JSONL append is the audit boundary. Always happens first at the CLI.
  - DB projection is best-effort dual-write; failure => stderr warning + exit 0.
  - `hai state reproject` rebuilds the DB from JSONL idempotently.

Out of scope: projection on 7B's Garmin-derived tables, intake-domain dual-
writes (7C), snapshot (7D).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.schemas import (
    FollowUp,
    PolicyDecision,
    RECOMMENDATION_SCHEMA_VERSION,
    ReviewEvent,
    ReviewOutcome,
)
from health_agent_infra.domains.recovery.schemas import TrainingRecommendation
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_recommendation,
    project_review_event,
    project_review_outcome,
    reproject_from_jsonl,
)
from health_agent_infra.core.review.outcomes import record_review_outcome, schedule_review
from health_agent_infra.core import exit_codes


# D2: hai writeback was retired in v0.1.4. Tests that used it as a
# seed for `recommendation_log.jsonl` now write the JSONL line directly;
# tests that used it to land a DB row call ``project_recommendation``
# instead.
_WRITEBACK_ROOT_NAME = "writeback"


def _append_recommendation_jsonl(
    base_dir: Path, rec: TrainingRecommendation,
) -> None:
    """Write one recommendation_log.jsonl line. Idempotent on rec id.

    This matches the shape the retired ``perform_writeback`` used to
    produce, so the reproject path under test still sees a realistic
    JSONL audit file.
    """
    base_dir.mkdir(parents=True, exist_ok=True)
    log_path = base_dir / "recommendation_log.jsonl"
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            existing = json.loads(line)
            if existing.get("recommendation_id") == rec.recommendation_id:
                return
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec.to_dict(), sort_keys=True) + "\n")


AS_OF = datetime(2026, 4, 17, 7, 0, tzinfo=timezone.utc).date()
NOW = datetime(2026, 4, 17, 7, 15, tzinfo=timezone.utc)


def _sample_rec(rec_suffix: str = "01", user: str = "u_1") -> TrainingRecommendation:
    return TrainingRecommendation(
        schema_version=RECOMMENDATION_SCHEMA_VERSION,
        recommendation_id=f"rec_{AS_OF.isoformat()}_{user}_{rec_suffix}",
        user_id=user,
        issued_at=NOW,
        for_date=AS_OF,
        action="proceed_with_planned_session",
        action_detail={"active_goal": "strength_block"},
        rationale=["sleep_debt=none", "active_goal=strength_block"],
        confidence="high",
        uncertainty=[],
        follow_up=FollowUp(
            review_at=NOW.replace(day=18),
            review_question="Did today feel appropriate?",
            review_event_id=f"rev_2026-04-18_{user}_rec_{AS_OF.isoformat()}_{user}_{rec_suffix}",
        ),
        policy_decisions=[
            PolicyDecision(rule_id="require_min_coverage", decision="allow", note="ok"),
        ],
        bounded=True,
    )


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


# ---------------------------------------------------------------------------
# projector unit tests — direct calls, no CLI
# ---------------------------------------------------------------------------

def test_project_recommendation_inserts_row(tmp_path: Path):
    db = _init_db(tmp_path)
    rec = _sample_rec()

    conn = open_connection(db)
    try:
        inserted = project_recommendation(conn, rec)
        assert inserted is True

        row = conn.execute(
            "SELECT recommendation_id, user_id, for_date, action, confidence, "
            "bounded, source, ingest_actor, payload_json "
            "FROM recommendation_log WHERE recommendation_id = ?",
            (rec.recommendation_id,),
        ).fetchone()

        assert row is not None
        assert row["recommendation_id"] == rec.recommendation_id
        assert row["action"] == "proceed_with_planned_session"
        assert row["confidence"] == "high"
        assert row["bounded"] == 1
        assert row["source"] == "claude_agent_v1"
        assert row["ingest_actor"] == "claude_agent_v1"

        payload = json.loads(row["payload_json"])
        assert payload["recommendation_id"] == rec.recommendation_id
        assert payload["policy_decisions"][0]["rule_id"] == "require_min_coverage"
    finally:
        conn.close()


def test_project_recommendation_is_idempotent(tmp_path: Path):
    db = _init_db(tmp_path)
    rec = _sample_rec()

    conn = open_connection(db)
    try:
        assert project_recommendation(conn, rec) is True
        assert project_recommendation(conn, rec) is False  # already present

        count = conn.execute(
            "SELECT COUNT(*) AS n FROM recommendation_log WHERE recommendation_id = ?",
            (rec.recommendation_id,),
        ).fetchone()["n"]
        assert count == 1
    finally:
        conn.close()


def test_project_review_event_requires_recommendation_fk(tmp_path: Path):
    db = _init_db(tmp_path)
    event = ReviewEvent(
        review_event_id="rev_missing_fk",
        recommendation_id="rec_does_not_exist",
        user_id="u_1",
        review_at=NOW,
        review_question="?",
    )

    conn = open_connection(db)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            project_review_event(conn, event)
    finally:
        conn.close()


def test_project_review_event_inserts_after_recommendation_exists(tmp_path: Path):
    db = _init_db(tmp_path)
    rec = _sample_rec()
    event = ReviewEvent(
        review_event_id=rec.follow_up.review_event_id,
        recommendation_id=rec.recommendation_id,
        user_id=rec.user_id,
        review_at=rec.follow_up.review_at,
        review_question=rec.follow_up.review_question,
    )

    conn = open_connection(db)
    try:
        project_recommendation(conn, rec)
        inserted = project_review_event(conn, event)
        assert inserted is True
        assert project_review_event(conn, event) is False  # idempotent
    finally:
        conn.close()


def test_project_review_outcome_appends(tmp_path: Path):
    db = _init_db(tmp_path)
    rec = _sample_rec()
    event = ReviewEvent(
        review_event_id=rec.follow_up.review_event_id,
        recommendation_id=rec.recommendation_id,
        user_id=rec.user_id,
        review_at=rec.follow_up.review_at,
        review_question=rec.follow_up.review_question,
    )
    outcome = ReviewOutcome(
        review_event_id=event.review_event_id,
        recommendation_id=rec.recommendation_id,
        user_id=rec.user_id,
        recorded_at=NOW,
        followed_recommendation=True,
        self_reported_improvement=True,
        free_text="felt good",
    )

    conn = open_connection(db)
    try:
        project_recommendation(conn, rec)
        project_review_event(conn, event)
        oid_1 = project_review_outcome(conn, outcome)
        oid_2 = project_review_outcome(conn, outcome)  # append-only; does NOT dedup
        assert oid_2 > oid_1

        rows = conn.execute(
            "SELECT followed_recommendation, self_reported_improvement, free_text "
            "FROM review_outcome WHERE review_event_id = ?",
            (event.review_event_id,),
        ).fetchall()
        assert len(rows) == 2
        assert rows[0]["followed_recommendation"] == 1
        assert rows[0]["self_reported_improvement"] == 1
        assert rows[0]["free_text"] == "felt good"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI dual-write — hai review schedule / hai review record
#
# `hai writeback` was retired in v0.1.4; the canonical recommendation
# write path is now `hai synthesize`. These tests seed the DB directly
# via `project_recommendation` to satisfy the review_event FK so the
# review CLI dual-write is exercised in isolation.
# ---------------------------------------------------------------------------

def _write_rec_json(tmp_path: Path, rec: TrainingRecommendation) -> Path:
    path = tmp_path / "rec.json"
    path.write_text(json.dumps(rec.to_dict(), sort_keys=True), encoding="utf-8")
    return path


def _seed_recommendation_in_db(db: Path, rec: TrainingRecommendation) -> None:
    conn = open_connection(db)
    try:
        project_recommendation(conn, rec)
    finally:
        conn.close()


def test_cli_review_schedule_projects_event(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rec = _sample_rec()
    rec_file = _write_rec_json(tmp_path, rec)
    base_dir = tmp_path / _WRITEBACK_ROOT_NAME
    _seed_recommendation_in_db(db, rec)

    rc = cli_main([
        "review", "schedule",
        "--recommendation-json", str(rec_file),
        "--base-dir", str(base_dir),
        "--db-path", str(db),
    ])
    capsys.readouterr()
    assert rc == 0

    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT review_event_id, recommendation_id FROM review_event"
        ).fetchone()
        assert row["review_event_id"] == rec.follow_up.review_event_id
        assert row["recommendation_id"] == rec.recommendation_id
    finally:
        conn.close()


def test_cli_review_record_projects_outcome(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rec = _sample_rec()
    rec_file = _write_rec_json(tmp_path, rec)
    base_dir = tmp_path / _WRITEBACK_ROOT_NAME
    _seed_recommendation_in_db(db, rec)

    cli_main([
        "review", "schedule", "--recommendation-json", str(rec_file),
        "--base-dir", str(base_dir), "--db-path", str(db),
    ])
    capsys.readouterr()

    outcome_payload = {
        "review_event_id": rec.follow_up.review_event_id,
        "recommendation_id": rec.recommendation_id,
        "user_id": rec.user_id,
        "review_at": rec.follow_up.review_at.isoformat(),
        "review_question": rec.follow_up.review_question,
        "followed_recommendation": True,
        "self_reported_improvement": True,
        "free_text": "tracked",
        "recorded_at": NOW.replace(day=18).isoformat(),
    }
    outcome_file = tmp_path / "outcome.json"
    outcome_file.write_text(json.dumps(outcome_payload), encoding="utf-8")

    rc = cli_main([
        "review", "record",
        "--outcome-json", str(outcome_file),
        "--base-dir", str(base_dir),
        "--db-path", str(db),
    ])
    capsys.readouterr()
    assert rc == 0

    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT followed_recommendation, self_reported_improvement, free_text "
            "FROM review_outcome WHERE review_event_id = ?",
            (rec.follow_up.review_event_id,),
        ).fetchone()
        assert row["followed_recommendation"] == 1
        assert row["self_reported_improvement"] == 1
        assert row["free_text"] == "tracked"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Reproject — JSONL is the recovery source
# ---------------------------------------------------------------------------

def test_reproject_reads_all_three_jsonl_files_into_db(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    base = tmp_path / _WRITEBACK_ROOT_NAME
    base.mkdir(parents=True)
    rec = _sample_rec()

    # Simulate a user who wrote via JSONL-only (DB missing at the time) and
    # now wants to reproject into a fresh DB.
    _append_recommendation_jsonl(base, rec)
    event = schedule_review(rec, base_dir=base)
    record_review_outcome(
        event, base_dir=base,
        followed_recommendation=True,
        self_reported_improvement=True,
        free_text="catchup",
        now=NOW.replace(day=18),
    )

    # DB is empty (nothing was dual-written).
    conn = open_connection(db)
    try:
        assert conn.execute("SELECT COUNT(*) AS n FROM recommendation_log").fetchone()["n"] == 0
    finally:
        conn.close()

    # Reproject.
    rc = cli_main([
        "state", "reproject",
        "--base-dir", str(base),
        "--db-path", str(db),
    ])
    out = capsys.readouterr().out
    assert rc == 0

    report = json.loads(out)
    # The count keys expand as new domains land; this test pins the three
    # recommendation/review counts specifically, other keys may be present
    # (e.g. gym_sessions/gym_sets from 7C) and should be 0 since no gym
    # JSONL was written in this fixture.
    assert report["reprojected"]["recommendations"] == 1
    assert report["reprojected"]["review_events"] == 1
    assert report["reprojected"]["review_outcomes"] == 1
    for k, v in report["reprojected"].items():
        if k not in ("recommendations", "review_events", "review_outcomes"):
            assert v == 0, f"unexpected non-zero reproject count for {k}: {v}"

    conn = open_connection(db)
    try:
        assert conn.execute("SELECT COUNT(*) AS n FROM recommendation_log").fetchone()["n"] == 1
        assert conn.execute("SELECT COUNT(*) AS n FROM review_event").fetchone()["n"] == 1
        assert conn.execute("SELECT COUNT(*) AS n FROM review_outcome").fetchone()["n"] == 1
    finally:
        conn.close()


def test_reproject_is_idempotent(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    base = tmp_path / _WRITEBACK_ROOT_NAME
    base.mkdir(parents=True)
    rec = _sample_rec()
    _append_recommendation_jsonl(base, rec)
    event = schedule_review(rec, base_dir=base)
    record_review_outcome(
        event, base_dir=base,
        followed_recommendation=True,
        self_reported_improvement=True,
        now=NOW.replace(day=18),
    )

    cli_main([
        "state", "reproject",
        "--base-dir", str(base), "--db-path", str(db),
    ])
    capsys.readouterr()

    # Second reproject must yield identical row counts (and identical PKs).
    cli_main([
        "state", "reproject",
        "--base-dir", str(base), "--db-path", str(db),
    ])
    capsys.readouterr()

    conn = open_connection(db)
    try:
        rec_rows = conn.execute(
            "SELECT recommendation_id FROM recommendation_log ORDER BY recommendation_id"
        ).fetchall()
        assert [r["recommendation_id"] for r in rec_rows] == [rec.recommendation_id]

        ev_rows = conn.execute("SELECT review_event_id FROM review_event").fetchall()
        assert len(ev_rows) == 1

        out_rows = conn.execute("SELECT review_event_id FROM review_outcome").fetchall()
        assert len(out_rows) == 1
    finally:
        conn.close()


def test_reproject_fails_clearly_when_db_missing(tmp_path: Path, capsys):
    base = tmp_path / _WRITEBACK_ROOT_NAME
    base.mkdir(parents=True)
    absent_db = tmp_path / "never.db"

    rc = cli_main([
        "state", "reproject",
        "--base-dir", str(base),
        "--db-path", str(absent_db),
    ])
    err = capsys.readouterr().err
    assert rc == exit_codes.USER_INPUT
    assert "state DB not found" in err


def test_reproject_fails_clearly_when_base_dir_missing(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "state", "reproject",
        "--base-dir", str(tmp_path / "never"),
        "--db-path", str(db),
    ])
    err = capsys.readouterr().err
    assert rc == exit_codes.USER_INPUT
    assert "base-dir not found" in err


def test_reproject_refuses_when_base_dir_lacks_audit_logs(tmp_path: Path, capsys):
    """The exact failure mode the audit flagged: --base-dir points at an
    existing but empty/wrong directory. Previously this silently truncated
    the projection tables. Now it must refuse and leave the DB untouched."""

    from health_agent_infra.core.state import ReprojectBaseDirError

    # 1. Seed a DB with a recommendation so we can verify it isn't wiped.
    db = _init_db(tmp_path)
    rec = _sample_rec()
    conn = open_connection(db)
    try:
        project_recommendation(conn, rec)
        count_before = conn.execute(
            "SELECT COUNT(*) AS n FROM recommendation_log"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert count_before == 1

    # 2. Create an unrelated existing directory with no audit logs.
    wrong_dir = tmp_path / "some_unrelated_dir"
    wrong_dir.mkdir()
    (wrong_dir / "README.txt").write_text("not an audit log", encoding="utf-8")

    # 3. Direct-function call must raise without touching the DB.
    conn = open_connection(db)
    try:
        with pytest.raises(ReprojectBaseDirError):
            reproject_from_jsonl(conn, wrong_dir)

        count_after = conn.execute(
            "SELECT COUNT(*) AS n FROM recommendation_log"
        ).fetchone()["n"]
        assert count_after == count_before, "reproject must not wipe on empty base-dir"
    finally:
        conn.close()


def test_reproject_cli_fails_closed_on_empty_base_dir(tmp_path: Path, capsys):
    """Same failure mode, through the CLI. Must exit 2 with a clear stderr."""

    db = _init_db(tmp_path)
    rec = _sample_rec()
    conn = open_connection(db)
    try:
        project_recommendation(conn, rec)
    finally:
        conn.close()

    wrong_dir = tmp_path / "wrong"
    wrong_dir.mkdir()

    rc = cli_main([
        "state", "reproject",
        "--base-dir", str(wrong_dir),
        "--db-path", str(db),
    ])
    err = capsys.readouterr().err
    assert rc == exit_codes.USER_INPUT
    assert "reproject refused" in err
    assert "allow-empty-reproject" in err

    # DB unaffected.
    conn = open_connection(db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM recommendation_log"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert count == 1


def test_reproject_cli_allow_empty_flag_bypasses_the_guard(tmp_path: Path, capsys):
    """``--allow-empty-reproject`` skips the ReprojectBaseDirError check so
    the command runs against an empty dir without raising, but under the
    scoped-truncation contract (7C.1 patch) **nothing is truncated** unless
    its log group is present. An empty dir ⇒ no groups touched ⇒ existing
    projected data survives untouched.

    This is the safer replacement for the prior "empty dir wipes everything"
    behavior: callers who truly want to reset tables now do so explicitly
    (drop tables, or write a sentinel log to scope the wipe). That change
    eliminated the class of bug where a typo'd or empty base_dir silently
    nuked unrelated projection data."""

    db = _init_db(tmp_path)
    rec = _sample_rec()
    conn = open_connection(db)
    try:
        project_recommendation(conn, rec)
    finally:
        conn.close()

    empty_dir = tmp_path / "intentionally_empty"
    empty_dir.mkdir()

    rc = cli_main([
        "state", "reproject",
        "--base-dir", str(empty_dir),
        "--db-path", str(db),
        "--allow-empty-reproject",
    ])
    capsys.readouterr()
    assert rc == 0

    # The flag bypassed the guard — no error. And scope-safety held: the
    # recommendation stays because no recommendation log was present.
    conn = open_connection(db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM recommendation_log"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert count == 1, (
        "allow-empty + empty base-dir should no longer wipe tables; "
        "scoped truncation protects existing projected data"
    )


def test_reproject_runs_when_only_recommendation_log_present(tmp_path: Path, capsys):
    """The 'at least one expected JSONL' rule lets partially-populated
    base-dirs reproject. A common legitimate case: the user has written
    recommendations but never scheduled a review yet."""

    db = _init_db(tmp_path)
    base = tmp_path / _WRITEBACK_ROOT_NAME
    base.mkdir(parents=True)
    rec = _sample_rec()
    _append_recommendation_jsonl(base, rec)

    # Only recommendation_log.jsonl exists; review logs are absent.
    assert (base / "recommendation_log.jsonl").exists()
    assert not (base / "review_events.jsonl").exists()
    assert not (base / "review_outcomes.jsonl").exists()

    rc = cli_main([
        "state", "reproject",
        "--base-dir", str(base),
        "--db-path", str(db),
    ])
    out = capsys.readouterr().out
    assert rc == 0

    report = json.loads(out)
    assert report["reprojected"]["recommendations"] == 1
    assert report["reprojected"]["review_events"] == 0
    assert report["reprojected"]["review_outcomes"] == 0


def test_reproject_direct_function_is_atomic(tmp_path: Path):
    """reproject_from_jsonl wraps the rebuild in a transaction. If
    mid-reproject the JSONL has a corrupt line, the DB state must roll
    back to what it was before this call — not left half-wiped."""

    db = _init_db(tmp_path)
    base = tmp_path / _WRITEBACK_ROOT_NAME
    base.mkdir(parents=True)
    rec = _sample_rec()
    _append_recommendation_jsonl(base, rec)

    # Seed the DB with an initial projection.
    conn = open_connection(db)
    try:
        project_recommendation(conn, rec)
        count_before = conn.execute(
            "SELECT COUNT(*) AS n FROM recommendation_log"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert count_before == 1

    # Corrupt the JSONL — add a junk line the JSON parser will reject.
    rec_log = base / "recommendation_log.jsonl"
    rec_log.write_text(rec_log.read_text() + "{not valid json\n", encoding="utf-8")

    conn = open_connection(db)
    try:
        with pytest.raises(json.JSONDecodeError):
            reproject_from_jsonl(conn, base)

        # DB must be back to the pre-reproject state — the original row is
        # still there because the transaction rolled back.
        count_after = conn.execute(
            "SELECT COUNT(*) AS n FROM recommendation_log"
        ).fetchone()["n"]
        assert count_after == count_before
    finally:
        conn.close()
