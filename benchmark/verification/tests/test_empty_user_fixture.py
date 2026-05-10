"""`empty_user` fixture build contract."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER = (
    REPO_ROOT
    / "governed_agent_bench"
    / "fixtures"
    / "empty_user"
    / "build.py"
)


def _build(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BUILDER), str(root)],
        cwd=REPO_ROOT.parent,
        capture_output=True,
        text=True,
        check=True,
    )


def _fingerprint(db_path: Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        tables = [
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name"
            )
        ]
        counts = {
            table: conn.execute(f'SELECT COUNT(*) AS n FROM "{table}"').fetchone()["n"]
            for table in tables
        }
        schema_head = conn.execute(
            "SELECT MAX(version) AS v FROM schema_migrations"
        ).fetchone()["v"]
    finally:
        conn.close()
    return {
        "tables": tables,
        "counts": counts,
        "schema_head": schema_head,
    }


def test_empty_user_fixture_builds_initialized_empty_state(tmp_path: Path) -> None:
    root = tmp_path / "empty_user"
    result = _build(root)

    assert result.returncode == 0
    state_db = root / "state.db"
    assert state_db.exists()
    metadata = json.loads((root / "fixture_metadata.json").read_text())
    assert metadata["fixture_id"] == "empty_user"
    assert metadata["contains_private_data"] is False

    fingerprint = _fingerprint(state_db)
    assert fingerprint["schema_head"] >= 28
    allowed_static_tables = {"schema_migrations", "exercise_taxonomy"}
    nonempty = {
        table: count
        for table, count in fingerprint["counts"].items()
        if count and table not in allowed_static_tables
    }
    assert nonempty == {}


def test_empty_user_fixture_rebuild_is_logically_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    _build(first)
    _build(second)

    first_fingerprint = _fingerprint(first / "state.db")
    second_fingerprint = _fingerprint(second / "state.db")

    assert first_fingerprint == second_fingerprint


def test_empty_user_fixture_does_not_create_default_user_paths(
    tmp_path: Path,
) -> None:
    root = tmp_path / "empty_user"

    _build(root)

    home = root / "home"
    assert not (home / ".hai").exists()
    assert not (home / ".health_agent").exists()
