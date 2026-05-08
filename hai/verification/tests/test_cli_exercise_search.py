"""Phase 4 step 4 — `hai exercise search` CLI + intake stamping.

Contracts pinned:

  1. `hai exercise search --query <name>` returns a top-N list of
     ranked taxonomy hits with exercise_id, canonical_name,
     aliases, primary/secondary muscle groups, category, equipment,
     score, and match_reason. Empty query → empty hits (rc=0).
  2. When the state DB is absent, `hai exercise search` prints a
     friendly error to stderr and exits rc=2.
  3. `hai intake gym` stamps ``gym_set.exercise_id`` on sets whose
     exercise_name resolves to an ``exact`` or ``alias`` taxonomy
     match. Ambiguous / no-match names leave exercise_id NULL, which
     is still OK because the projector re-resolves by name.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


USER = "u_test"
AS_OF = date(2026, 4, 18)


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


# ---------------------------------------------------------------------------
# exercise search CLI
# ---------------------------------------------------------------------------

def test_exercise_search_exact_canonical_surfaces_as_top_hit(tmp_path: Path, capsys):
    db = _init_db(tmp_path)

    rc = cli_main([
        "exercise", "search",
        "--query", "Back Squat",
        "--db-path", str(db),
    ])
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["query"] == "Back Squat"
    assert payload["hits"][0]["exercise_id"] == "back_squat"
    assert payload["hits"][0]["match_reason"] == "exact_canonical"
    assert payload["hits"][0]["canonical_name"] == "Back Squat"
    # Muscle group + equipment are surfaced.
    assert payload["hits"][0]["primary_muscle_group"] == "quads"
    assert payload["hits"][0]["equipment"] == "barbell"


def test_exercise_search_alias_hits(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "exercise", "search",
        "--query", "rdl",
        "--db-path", str(db),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["hits"][0]["exercise_id"] == "romanian_deadlift"
    assert payload["hits"][0]["match_reason"] == "exact_alias"


def test_exercise_search_limit_is_honoured(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "exercise", "search",
        "--query", "press",
        "--limit", "3",
        "--db-path", str(db),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["hits"]) <= 3


def test_exercise_search_empty_query_returns_empty(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "exercise", "search",
        "--query", "",
        "--db-path", str(db),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["hits"] == []


def test_exercise_search_missing_db_exits_nonzero(tmp_path: Path, capsys):
    db = tmp_path / "absent.db"
    rc = cli_main([
        "exercise", "search",
        "--query", "Back Squat",
        "--db-path", str(db),
    ])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "state DB not found" in err


# ---------------------------------------------------------------------------
# intake stamping — exercise_id set when resolution is confident
# ---------------------------------------------------------------------------

def test_intake_gym_stamps_exercise_id_on_exact_match(tmp_path: Path):
    base = tmp_path / "intake"
    base.mkdir(parents=True, exist_ok=True)
    db = _init_db(tmp_path)

    rc = cli_main([
        "intake", "gym",
        "--session-id", "s_exact",
        "--session-name", "Legs",
        "--exercise", "Back Squat",
        "--set-number", "1",
        "--weight-kg", "100.0",
        "--reps", "5",
        "--as-of", AS_OF.isoformat(),
        "--user-id", USER,
        "--base-dir", str(base),
        "--db-path", str(db),
    ])
    assert rc == 0

    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT exercise_id FROM gym_set WHERE session_id = ?",
            ("s_exact",),
        ).fetchone()
    finally:
        conn.close()
    assert row["exercise_id"] == "back_squat"


def test_intake_gym_stamps_exercise_id_on_alias_match(tmp_path: Path):
    base = tmp_path / "intake"
    base.mkdir(parents=True, exist_ok=True)
    db = _init_db(tmp_path)

    rc = cli_main([
        "intake", "gym",
        "--session-id", "s_alias",
        "--exercise", "rdl",
        "--set-number", "1",
        "--weight-kg", "120.0",
        "--reps", "8",
        "--as-of", AS_OF.isoformat(),
        "--user-id", USER,
        "--base-dir", str(base),
        "--db-path", str(db),
    ])
    assert rc == 0

    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT exercise_id FROM gym_set WHERE session_id = ?",
            ("s_alias",),
        ).fetchone()
    finally:
        conn.close()
    assert row["exercise_id"] == "romanian_deadlift"


def test_intake_gym_leaves_exercise_id_null_on_no_match(tmp_path: Path):
    base = tmp_path / "intake"
    base.mkdir(parents=True, exist_ok=True)
    db = _init_db(tmp_path)

    rc = cli_main([
        "intake", "gym",
        "--session-id", "s_unknown",
        "--exercise", "Jefferson Curl",
        "--set-number", "1",
        "--weight-kg", "30.0",
        "--reps", "10",
        "--as-of", AS_OF.isoformat(),
        "--user-id", USER,
        "--base-dir", str(base),
        "--db-path", str(db),
    ])
    assert rc == 0

    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT exercise_id, exercise_name FROM gym_set "
            "WHERE session_id = ?",
            ("s_unknown",),
        ).fetchone()
    finally:
        conn.close()
    assert row["exercise_id"] is None
    # But the free-text name is preserved for the projector.
    assert row["exercise_name"] == "Jefferson Curl"
