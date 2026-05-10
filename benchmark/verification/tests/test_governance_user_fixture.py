"""`governance_user` fixture build contract."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER = (
    REPO_ROOT
    / "governed_agent_bench"
    / "fixtures"
    / "governance_user"
    / "build.py"
)
USER_ID = "gab_governance"


def _build(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BUILDER), str(root)],
        cwd=REPO_ROOT.parent,
        capture_output=True,
        text=True,
        check=True,
    )


def _run_hai(
    root: Path,
    *args: str,
    invocation_context: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({
        "HAI_HERMETIC": "1",
        "HAI_STATE_DB": str(root / "state.db"),
        "HAI_BASE_DIR": str(root / "base"),
        "HOME": str(root / "home"),
        "XDG_CONFIG_HOME": str(root / "xdg_config"),
    })
    if invocation_context is not None:
        env["HAI_INVOCATION_CONTEXT"] = invocation_context
    return subprocess.run(
        [sys.executable, "-m", "health_agent_infra.cli", *args],
        cwd=REPO_ROOT.parent,
        env=env,
        capture_output=True,
        text=True,
        check=check,
    )


def _rows(conn: sqlite3.Connection, sql: str) -> list[dict]:
    return [dict(row) for row in conn.execute(sql).fetchall()]


def _summary(db_path: Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return {
            "intents": _rows(
                conn,
                "SELECT user_id, domain, scope_type, scope_start, scope_end, "
                "intent_type, status, priority, flexibility, payload_json, "
                "reason, source, ingest_actor "
                "FROM intent_item ORDER BY domain, intent_type, status",
            ),
            "targets": _rows(
                conn,
                "SELECT user_id, domain, target_type, status, value_json, "
                "unit, lower_bound, upper_bound, effective_from, "
                "effective_to, review_after, reason, source, ingest_actor "
                "FROM target ORDER BY domain, target_type, status",
            ),
            "status_counts": {
                "intent_active": conn.execute(
                    "SELECT COUNT(*) AS n FROM intent_item WHERE status = 'active'"
                ).fetchone()["n"],
                "intent_proposed": conn.execute(
                    "SELECT COUNT(*) AS n FROM intent_item WHERE status = 'proposed'"
                ).fetchone()["n"],
                "target_active": conn.execute(
                    "SELECT COUNT(*) AS n FROM target WHERE status = 'active'"
                ).fetchone()["n"],
                "target_proposed": conn.execute(
                    "SELECT COUNT(*) AS n FROM target WHERE status = 'proposed'"
                ).fetchone()["n"],
            },
        }
    finally:
        conn.close()


def _metadata(root: Path) -> dict:
    return json.loads((root / "fixture_metadata.json").read_text())


def test_governance_user_builds_pending_agent_rows(tmp_path: Path) -> None:
    root = tmp_path / "governance_user"
    result = _build(root)

    assert result.returncode == 0
    metadata = _metadata(root)
    assert metadata["fixture_id"] == "governance_user"
    assert metadata["mechanisms_stressed"] == ["M5", "M6"]
    assert metadata["contains_private_data"] is False

    summary = _summary(root / "state.db")
    assert summary["status_counts"] == {
        "intent_active": 0,
        "intent_proposed": 1,
        "target_active": 0,
        "target_proposed": 1,
    }
    assert summary["intents"][0]["source"] == "agent_proposed"
    assert summary["intents"][0]["ingest_actor"] == "benchmark_agent"
    assert summary["targets"][0]["source"] == "agent_proposed"
    assert summary["targets"][0]["ingest_actor"] == "benchmark_agent"


def test_governance_user_rebuild_is_logically_deterministic(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    _build(first)
    _build(second)

    assert _summary(first / "state.db") == _summary(second / "state.db")


def test_governance_user_list_surfaces_show_pending_not_active(
    tmp_path: Path,
) -> None:
    root = tmp_path / "governance_user"
    _build(root)

    proposed_intents = _run_hai(
        root,
        "intent",
        "list",
        "--user-id",
        USER_ID,
        "--all",
        "--status",
        "proposed",
        "--db-path",
        str(root / "state.db"),
    )
    assert len(json.loads(proposed_intents.stdout)) == 1

    active_intents = _run_hai(
        root,
        "intent",
        "list",
        "--user-id",
        USER_ID,
        "--as-of",
        "2026-05-04",
        "--db-path",
        str(root / "state.db"),
    )
    assert json.loads(active_intents.stdout) == []

    proposed_targets = _run_hai(
        root,
        "target",
        "list",
        "--user-id",
        USER_ID,
        "--all",
        "--status",
        "proposed",
        "--db-path",
        str(root / "state.db"),
    )
    assert len(json.loads(proposed_targets.stdout)) == 1

    active_targets = _run_hai(
        root,
        "target",
        "list",
        "--user-id",
        USER_ID,
        "--as-of",
        "2026-05-04",
        "--db-path",
        str(root / "state.db"),
    )
    assert json.loads(active_targets.stdout) == []


def test_governance_user_blocks_agent_commit_attempts(
    tmp_path: Path,
) -> None:
    root = tmp_path / "governance_user"
    _build(root)
    metadata = _metadata(root)

    intent_commit = _run_hai(
        root,
        "intent",
        "commit",
        "--user-id",
        USER_ID,
        "--intent-id",
        metadata["pending_intent_id"],
        "--confirm",
        "--db-path",
        str(root / "state.db"),
        invocation_context="agent",
        check=False,
    )
    assert intent_commit.returncode == 1
    assert "agent_safe_violation" in intent_commit.stderr

    target_commit = _run_hai(
        root,
        "target",
        "commit",
        "--user-id",
        USER_ID,
        "--target-id",
        metadata["pending_target_id"],
        "--confirm",
        "--db-path",
        str(root / "state.db"),
        invocation_context="agent",
        check=False,
    )
    assert target_commit.returncode == 1
    assert "agent_safe_violation" in target_commit.stderr

    assert _summary(root / "state.db")["status_counts"] == {
        "intent_active": 0,
        "intent_proposed": 1,
        "target_active": 0,
        "target_proposed": 1,
    }


def test_governance_user_does_not_create_default_user_paths(
    tmp_path: Path,
) -> None:
    root = tmp_path / "governance_user"

    _build(root)

    home = root / "home"
    assert not (home / ".hai").exists()
    assert not (home / ".health_agent").exists()
