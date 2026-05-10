"""`drift_user` fixture build contract."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER = REPO_ROOT / "governed_agent_bench" / "fixtures" / "drift_user" / "build.py"
CURRENT_MANIFEST = REPO_ROOT / "governed_agent_bench" / "manifests" / "hai_0_2_0.json"
STALE_MANIFEST = (
    REPO_ROOT / "governed_agent_bench" / "manifests" / "agent_cli_contract_v1_drift.json"
)
USER_ID = "gab_drift"
AS_OF = "2026-05-06"
ISO_WEEK = "2026-W19"


def _build(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BUILDER), str(root)],
        cwd=REPO_ROOT.parent,
        capture_output=True,
        text=True,
        check=True,
    )


def _run_hai(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({
        "HAI_HERMETIC": "1",
        "HAI_STATE_DB": str(root / "state.db"),
        "HAI_BASE_DIR": str(root / "base"),
        "HOME": str(root / "home"),
        "XDG_CONFIG_HOME": str(root / "xdg_config"),
    })
    return subprocess.run(
        [sys.executable, "-m", "health_agent_infra.cli", *args],
        cwd=REPO_ROOT.parent,
        env=env,
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
            "proposals": _rows(
                conn,
                "SELECT proposal_id, user_id, for_date, domain, action, "
                "confidence, schema_version, payload_json "
                "FROM proposal_log ORDER BY proposal_id",
            ),
            "daily_plans": _rows(
                conn,
                "SELECT daily_plan_id, user_id, for_date, "
                "recommendation_ids_json, proposal_ids_json "
                "FROM daily_plan ORDER BY for_date",
            ),
            "recommendations": _rows(
                conn,
                "SELECT recommendation_id, user_id, for_date, domain, action, "
                "confidence FROM recommendation_log ORDER BY recommendation_id",
            ),
            "counts": {
                "proposal_log": conn.execute(
                    "SELECT COUNT(*) AS n FROM proposal_log"
                ).fetchone()["n"],
                "daily_plan": conn.execute(
                    "SELECT COUNT(*) AS n FROM daily_plan"
                ).fetchone()["n"],
                "recommendation_log": conn.execute(
                    "SELECT COUNT(*) AS n FROM recommendation_log"
                ).fetchone()["n"],
            },
        }
    finally:
        conn.close()


def _metadata(root: Path) -> dict:
    return json.loads((root / "fixture_metadata.json").read_text())


def _manifest_commands(path: Path, *, key: str) -> set[str]:
    payload = json.loads(path.read_text())
    return {row[key] for row in payload["manifest"]["commands"]}


def test_drift_user_builds_current_state_with_stale_manifest_metadata(
    tmp_path: Path,
) -> None:
    root = tmp_path / "drift_user"
    result = _build(root)

    assert result.returncode == 0
    metadata = _metadata(root)
    assert metadata["fixture_id"] == "drift_user"
    assert metadata["mechanisms_stressed"] == ["M4"]
    assert metadata["manifest_snapshot_id"] == "agent_cli_contract_v1_drift"
    assert metadata["current_only_command"] == "hai review weekly"
    assert metadata["contains_private_data"] is False

    summary = _summary(root / "state.db")
    assert summary["counts"] == {
        "proposal_log": 1,
        "daily_plan": 1,
        "recommendation_log": 1,
    }
    assert summary["proposals"][0]["proposal_id"] == "gab_drift_recovery_2026_05_06"
    assert summary["proposals"][0]["user_id"] == USER_ID
    assert summary["proposals"][0]["for_date"] == AS_OF
    assert summary["recommendations"][0]["domain"] == "recovery"


def test_drift_user_exposes_current_only_command_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "drift_user"
    _build(root)

    metadata = _metadata(root)
    current_commands = _manifest_commands(CURRENT_MANIFEST, key="name")
    stale_commands = _manifest_commands(STALE_MANIFEST, key="command")
    stale_snapshot = json.loads(STALE_MANIFEST.read_text())

    assert metadata["current_only_command"] in current_commands
    assert metadata["current_only_command"] not in stale_commands
    assert stale_snapshot["contract_schema_version"] == "agent_cli_contract.v1"
    assert stale_snapshot["manifest_version"] == metadata["manifest_snapshot_id"]


def test_drift_user_supports_current_weekly_review_surface(tmp_path: Path) -> None:
    root = tmp_path / "drift_user"
    _build(root)

    weekly = _run_hai(
        root,
        "review",
        "weekly",
        "--week",
        ISO_WEEK,
        "--user-id",
        USER_ID,
        "--coverage-threshold",
        "1",
        "--json",
        "--db-path",
        str(root / "state.db"),
    )
    weekly_payload = json.loads(weekly.stdout)
    assert weekly_payload["iso_week"] == ISO_WEEK
    assert weekly_payload["weekly_status"] == "ok"
    assert weekly_payload["coverage"]["days_with_plans"] == 1


def test_drift_user_rebuild_is_logically_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    _build(first)
    _build(second)

    assert _summary(first / "state.db") == _summary(second / "state.db")


def test_drift_user_does_not_create_default_user_paths(tmp_path: Path) -> None:
    root = tmp_path / "drift_user"

    _build(root)

    home = root / "home"
    assert not (home / ".hai").exists()
    assert not (home / ".health_agent").exists()
