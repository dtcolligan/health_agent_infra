"""`read_surface_user` fixture build contract."""

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
    / "read_surface_user"
    / "build.py"
)
USER_ID = "u_local_1"
FINAL_DAY = "2026-05-03"
SNAPSHOT_DAY = "2026-05-04"
ISO_WEEK = "2026-W18"
DOMAINS = ["nutrition", "recovery", "running", "sleep", "strength", "stress"]


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
            "daily_plans": _rows(
                conn,
                "SELECT daily_plan_id, user_id, for_date, "
                "recommendation_ids_json, proposal_ids_json "
                "FROM daily_plan ORDER BY for_date",
            ),
            "proposal_domains": _rows(
                conn,
                "SELECT for_date, domain, action, confidence "
                "FROM proposal_log ORDER BY for_date, domain",
            ),
            "recommendation_domains": _rows(
                conn,
                "SELECT for_date, domain, action, confidence "
                "FROM recommendation_log ORDER BY for_date, domain",
            ),
            "nutrition": _rows(
                conn,
                "SELECT as_of_date, user_id, calories, protein_g, carbs_g, "
                "fat_g, hydration_l, meals_count, derivation_path "
                "FROM accepted_nutrition_state_daily ORDER BY as_of_date",
            ),
            "review_outcomes": _rows(
                conn,
                "SELECT review_event_id, recommendation_id, user_id, domain, "
                "recorded_at, followed_recommendation, "
                "self_reported_improvement, completed, intensity_delta, "
                "duration_minutes, pre_energy_score, post_energy_score "
                "FROM review_outcome ORDER BY recorded_at",
            ),
            "counts": {
                table: conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()[
                    "n"
                ]
                for table in (
                    "nutrition_intake_raw",
                    "proposal_log",
                    "daily_plan",
                    "recommendation_log",
                    "planned_recommendation",
                    "recommendation_evidence_card",
                    "review_event",
                    "review_outcome",
                )
            },
        }
    finally:
        conn.close()


def test_read_surface_user_builds_expected_week(tmp_path: Path) -> None:
    root = tmp_path / "read_surface_user"
    result = _build(root)

    assert result.returncode == 0
    metadata = json.loads((root / "fixture_metadata.json").read_text())
    assert metadata["fixture_id"] == "read_surface_user"
    assert metadata["mechanisms_stressed"] == ["M8"]
    assert metadata["contains_private_data"] is False

    summary = _summary(root / "state.db")
    assert summary["counts"] == {
        "nutrition_intake_raw": 7,
        "proposal_log": 42,
        "daily_plan": 7,
        "recommendation_log": 42,
        "planned_recommendation": 42,
        "recommendation_evidence_card": 42,
        "review_event": 7,
        "review_outcome": 7,
    }
    assert [row["for_date"] for row in summary["daily_plans"]] == [
        "2026-04-27",
        "2026-04-28",
        "2026-04-29",
        "2026-04-30",
        "2026-05-01",
        "2026-05-02",
        "2026-05-03",
    ]
    assert {row["domain"] for row in summary["proposal_domains"]} == set(DOMAINS)
    assert {row["domain"] for row in summary["recommendation_domains"]} == set(
        DOMAINS
    )
    assert len(summary["nutrition"]) == 7
    assert all(row["domain"] == "recovery" for row in summary["review_outcomes"])


def test_read_surface_user_rebuild_is_logically_deterministic(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    _build(first)
    _build(second)

    assert _summary(first / "state.db") == _summary(second / "state.db")


def test_read_surface_user_supports_read_surfaces(tmp_path: Path) -> None:
    root = tmp_path / "read_surface_user"
    _build(root)

    today = _run_hai(
        root,
        "today",
        "--as-of",
        FINAL_DAY,
        "--user-id",
        USER_ID,
        "--format",
        "json",
        "--db-path",
        str(root / "state.db"),
    )
    today_payload = json.loads(today.stdout)
    assert sorted(section["domain"] for section in today_payload["sections"]) == DOMAINS

    explain = _run_hai(
        root,
        "explain",
        "--as-of",
        FINAL_DAY,
        "--user-id",
        USER_ID,
        "--db-path",
        str(root / "state.db"),
    )
    explain_payload = json.loads(explain.stdout)
    assert sorted(rec["domain"] for rec in explain_payload["recommendations"]) == DOMAINS
    assert any(
        review["recommendation_id"]
        == f"rec_{FINAL_DAY}_{USER_ID}_recovery_01"
        for review in explain_payload["reviews"]
    )

    snapshot = _run_hai(
        root,
        "state",
        "snapshot",
        "--as-of",
        SNAPSHOT_DAY,
        "--user-id",
        USER_ID,
        "--db-path",
        str(root / "state.db"),
    )
    snapshot_payload = json.loads(snapshot.stdout)
    assert snapshot_payload["nutrition"]["data_quality"]["cold_start_window_state"]
    assert snapshot_payload["recovery"]["review_summary"]["recorded_outcome_count"] == 7
    assert snapshot_payload["recovery"]["review_summary"]["scheduled_review_count"] == 7

    weekly = _run_hai(
        root,
        "review",
        "weekly",
        "--week",
        ISO_WEEK,
        "--user-id",
        USER_ID,
        "--json",
        "--db-path",
        str(root / "state.db"),
    )
    weekly_payload = json.loads(weekly.stdout)
    assert weekly_payload["weekly_status"] == "ok"
    assert weekly_payload["coverage"]["days_with_plans"] == 7


def test_read_surface_user_does_not_create_default_user_paths(
    tmp_path: Path,
) -> None:
    root = tmp_path / "read_surface_user"

    _build(root)

    home = root / "home"
    assert not (home / ".hai").exists()
    assert not (home / ".health_agent").exists()
