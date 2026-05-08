"""W46 — `hai stats --funnel` CLI surface."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


def _seed_event(
    conn: sqlite3.Connection,
    *,
    started_at: str,
    overall_status: str,
    missing_domains: list[str] | None = None,
) -> None:
    ctx = {
        "stage": "proposal_gate",
        "overall_status": overall_status,
        "expected_domains": ["recovery", "running", "sleep", "stress", "strength", "nutrition"],
        "present_domains": [],
        "missing_domains": missing_domains or [],
    }
    conn.execute(
        "INSERT INTO runtime_event_log "
        "(command, user_id, started_at, completed_at, status, exit_code, "
        " duration_ms, context_json) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "daily", "u_local_1", started_at, started_at,
            "ok" if overall_status == "complete" else "ok",
            0 if overall_status == "complete" else 0,
            150,
            json.dumps(ctx),
        ),
    )
    conn.commit()


def test_funnel_json_buckets_runs(tmp_path: Path, capsys):
    db = tmp_path / "state.db"
    initialize_database(db)
    today = datetime.now(timezone.utc).date().isoformat()
    conn = open_connection(db)
    try:
        _seed_event(conn, started_at=f"{today}T07:00:00Z", overall_status="complete")
        _seed_event(conn, started_at=f"{today}T08:00:00Z", overall_status="incomplete",
                    missing_domains=["sleep", "nutrition"])
        _seed_event(conn, started_at=f"{today}T09:00:00Z", overall_status="awaiting_proposals",
                    missing_domains=["recovery", "running", "sleep", "stress", "strength", "nutrition"])
    finally:
        conn.close()

    rc = cli_main([
        "stats", "--db-path", str(db),
        "--funnel", "--json",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["daily_run_count"] == 3
    assert payload["complete_count"] == 1
    assert payload["incomplete_count"] == 1
    assert payload["awaiting_proposals_count"] == 1
    assert payload["blocking_action_count"] == 2
    assert payload["overall_status_histogram"]["complete"] == 1
    assert payload["missing_domain_frequency"]["sleep"] == 2
    assert payload["missing_domain_frequency"]["nutrition"] == 2


def test_funnel_text_renders(tmp_path: Path, capsys):
    db = tmp_path / "state.db"
    initialize_database(db)

    rc = cli_main(["stats", "--db-path", str(db), "--funnel"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "# Daily-pipeline funnel" in out
    assert "Total `hai daily` invocations" in out
