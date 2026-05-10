"""`ready_user_minimal` fixture build contract."""

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
    / "ready_user_minimal"
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


def _rows(conn: sqlite3.Connection, sql: str) -> list[dict]:
    return [dict(row) for row in conn.execute(sql).fetchall()]


def _summary(db_path: Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return {
            "nutrition_raw_count": conn.execute(
                "SELECT COUNT(*) AS n FROM nutrition_intake_raw"
            ).fetchone()["n"],
            "accepted_nutrition": _rows(
                conn,
                "SELECT as_of_date, user_id, calories, protein_g, carbs_g, "
                "fat_g, hydration_l, meals_count, derivation_path "
                "FROM accepted_nutrition_state_daily ORDER BY as_of_date, user_id",
            ),
            "proposals": _rows(
                conn,
                "SELECT proposal_id, user_id, for_date, domain, action, "
                "confidence, schema_version, payload_json "
                "FROM proposal_log ORDER BY proposal_id",
            ),
            "plans": conn.execute("SELECT COUNT(*) AS n FROM daily_plan").fetchone()[
                "n"
            ],
        }
    finally:
        conn.close()


def test_ready_user_minimal_builds_expected_rows(tmp_path: Path) -> None:
    root = tmp_path / "ready_user_minimal"
    result = _build(root)

    assert result.returncode == 0
    metadata = json.loads((root / "fixture_metadata.json").read_text())
    assert metadata["fixture_id"] == "ready_user_minimal"
    assert metadata["contains_private_data"] is False

    summary = _summary(root / "state.db")
    assert summary["nutrition_raw_count"] == 1
    assert summary["accepted_nutrition"] == [
        {
            "as_of_date": "2026-04-23",
            "user_id": "gab_ready_user",
            "calories": 2200.0,
            "protein_g": 160.0,
            "carbs_g": 250.0,
            "fat_g": 70.0,
            "hydration_l": 2.5,
            "meals_count": 3,
            "derivation_path": "daily_macros",
        }
    ]
    assert len(summary["proposals"]) == 1
    proposal = summary["proposals"][0]
    assert proposal["proposal_id"] == "gab_ready_recovery_2026_04_23"
    assert proposal["domain"] == "recovery"
    assert proposal["action"] == "proceed_with_planned_session"
    assert proposal["confidence"] == "moderate"
    assert summary["plans"] == 0


def test_ready_user_minimal_rebuild_is_logically_deterministic(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    _build(first)
    _build(second)

    assert _summary(first / "state.db") == _summary(second / "state.db")


def test_ready_user_minimal_does_not_create_default_user_paths(
    tmp_path: Path,
) -> None:
    root = tmp_path / "ready_user_minimal"

    _build(root)

    home = root / "home"
    assert not (home / ".hai").exists()
    assert not (home / ".health_agent").exists()
