"""Tiny Phase 4 follow-up — `hai intake exercise`.

Contracts pinned:

  1. `hai intake exercise` inserts a `user_manual` row into
     `exercise_taxonomy`, generating a deterministic snake_case
     `exercise_id` from `--name` when none is provided.
  2. Re-running the exact same command is idempotent: rc=0,
     `inserted=false`, and the taxonomy still contains one row.
  3. Conflicting reuse of an existing taxonomy id or canonical name
     fails loudly (rc=2) instead of silently mutating the row.
  4. The inserted row is immediately visible to `hai exercise search`.
  5. Missing DB path fails with a friendly `state init` prompt.
"""

from __future__ import annotations

import json
from pathlib import Path

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.state import initialize_database, open_connection
from health_agent_infra.core import exit_codes


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def test_intake_exercise_inserts_user_manual_row_with_generated_id(
    tmp_path: Path, capsys
):
    db = _init_db(tmp_path)

    rc = cli_main([
        "intake", "exercise",
        "--name", "Jefferson Curl",
        "--primary-muscle-group", "hamstrings",
        "--secondary-muscle-groups", "glutes, core",
        "--category", "compound",
        "--equipment", "barbell",
        "--aliases", "jeff curl,jefferson",
        "--db-path", str(db),
    ])
    assert rc == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["inserted"] is True
    assert payload["exercise_id"] == "jefferson_curl"
    assert payload["source"] == "user_manual"
    assert payload["aliases"] == ["jeff curl", "jefferson"]
    assert payload["secondary_muscle_groups"] == ["glutes", "core"]

    conn = open_connection(db)
    try:
        row = conn.execute(
            """
            SELECT exercise_id, canonical_name, aliases,
                   primary_muscle_group, secondary_muscle_groups,
                   category, equipment, source
            FROM exercise_taxonomy
            WHERE exercise_id = ?
            """,
            ("jefferson_curl",),
        ).fetchone()
    finally:
        conn.close()

    assert row["canonical_name"] == "Jefferson Curl"
    assert row["aliases"] == "jeff curl|jefferson"
    assert row["primary_muscle_group"] == "hamstrings"
    assert row["secondary_muscle_groups"] == "glutes|core"
    assert row["category"] == "compound"
    assert row["equipment"] == "barbell"
    assert row["source"] == "user_manual"


def test_intake_exercise_is_idempotent_on_exact_rerun(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    argv = [
        "intake", "exercise",
        "--name", "Jefferson Curl",
        "--primary-muscle-group", "hamstrings",
        "--category", "compound",
        "--equipment", "barbell",
        "--db-path", str(db),
    ]

    assert cli_main(argv) == 0
    capsys.readouterr()
    assert cli_main(argv) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["inserted"] is False
    assert payload["exercise_id"] == "jefferson_curl"

    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM exercise_taxonomy WHERE exercise_id = ?",
            ("jefferson_curl",),
        ).fetchone()
    finally:
        conn.close()
    assert row["n"] == 1


def test_intake_exercise_rejects_conflicting_duplicate(tmp_path: Path, capsys):
    db = _init_db(tmp_path)

    assert cli_main([
        "intake", "exercise",
        "--name", "Jefferson Curl",
        "--primary-muscle-group", "hamstrings",
        "--category", "compound",
        "--equipment", "barbell",
        "--db-path", str(db),
    ]) == 0
    capsys.readouterr()

    rc = cli_main([
        "intake", "exercise",
        "--name", "Jefferson Curl",
        "--primary-muscle-group", "core",
        "--category", "isolation",
        "--equipment", "bodyweight",
        "--db-path", str(db),
    ])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "intake exercise rejected" in err
    assert "canonical_name" in err or "exercise_id" in err


def test_intake_exercise_surfaces_in_exercise_search(tmp_path: Path, capsys):
    db = _init_db(tmp_path)

    assert cli_main([
        "intake", "exercise",
        "--name", "Jefferson Curl",
        "--primary-muscle-group", "hamstrings",
        "--category", "compound",
        "--equipment", "barbell",
        "--aliases", "jeff curl",
        "--db-path", str(db),
    ]) == 0
    capsys.readouterr()

    rc = cli_main([
        "exercise", "search",
        "--query", "jeff curl",
        "--db-path", str(db),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["hits"][0]["exercise_id"] == "jefferson_curl"
    assert payload["hits"][0]["match_reason"] == "exact_alias"


def test_intake_exercise_missing_db_exits_nonzero(tmp_path: Path, capsys):
    db = tmp_path / "absent.db"
    rc = cli_main([
        "intake", "exercise",
        "--name", "Jefferson Curl",
        "--primary-muscle-group", "hamstrings",
        "--category", "compound",
        "--equipment", "barbell",
        "--db-path", str(db),
    ])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "state DB not found" in err
    assert "hai state init" in err


def test_intake_exercise_rejects_unknown_muscle_group(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "intake", "exercise",
        "--name", "Jefferson Curl",
        "--primary-muscle-group", "legs",
        "--category", "compound",
        "--equipment", "barbell",
        "--db-path", str(db),
    ])
    assert rc == exit_codes.USER_INPUT
    err = capsys.readouterr().err
    assert "--primary-muscle-group must be one of" in err
