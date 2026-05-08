"""W38 — `hai stats --outcomes` CLI surface.

Pins:

  1. ``hai stats --outcomes --json`` emits the per-domain + aggregate
     dict shape from ``build_review_summary`` (visibility-only).
  2. ``--domain <d>`` returns one summary keyed under ``summary``.
  3. ``--since <N>`` overrides the rolling window.
  4. Markdown table mode (no ``--json``) renders one row per domain
     plus an aggregate row.
  5. ``hai capabilities --json`` documents the new flags.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)

from _fixtures import make_outcome_chain, seed_outcome_chain


def _seed_chain(
    conn: sqlite3.Connection,
    *,
    suffix: str,
    domain: str,
    for_date: date,
    followed: bool,
    improved: bool | None,
) -> None:
    chain = make_outcome_chain(
        recommendation_id=f"rec_{suffix}",
        review_event_id=f"rev_{suffix}",
        user_id="u_local_1",
        domain=domain,
        for_date=for_date,
        issued_at=datetime.combine(
            for_date, datetime.min.time(), tzinfo=timezone.utc
        ).replace(hour=7),
        followed=followed,
        improved=improved,
    )
    seed_outcome_chain(conn, **chain)


def _seed_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    today = datetime.now(timezone.utc).date()
    conn = open_connection(db)
    try:
        for i in range(3):
            _seed_chain(
                conn,
                suffix=f"r{i}",
                domain="recovery",
                for_date=today,
                followed=True,
                improved=True,
            )
        for i in range(2):
            _seed_chain(
                conn,
                suffix=f"run{i}",
                domain="running",
                for_date=today,
                followed=True,
                improved=False,
            )
    finally:
        conn.close()
    return db


def test_outcomes_json_aggregate_default(tmp_path: Path, capsys):
    db = _seed_db(tmp_path)
    rc = cli_main([
        "stats",
        "--db-path", str(db),
        "--outcomes",
        "--json",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["user_id"] == "u_local_1"
    assert payload["window_days"] == 7
    assert set(payload["domains"].keys()) == {
        "recovery", "running", "sleep", "stress", "strength", "nutrition",
    }
    assert payload["domains"]["recovery"]["recorded_outcome_count"] == 3
    assert payload["domains"]["running"]["recorded_outcome_count"] == 2
    assert payload["aggregate"]["recorded_outcome_count"] == 5


def test_outcomes_json_domain_filter(tmp_path: Path, capsys):
    db = _seed_db(tmp_path)
    rc = cli_main([
        "stats",
        "--db-path", str(db),
        "--outcomes",
        "--domain", "recovery",
        "--json",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)

    assert payload["domain"] == "recovery"
    assert "summary" in payload
    assert payload["summary"]["domain"] == "recovery"
    assert payload["summary"]["recorded_outcome_count"] == 3


def test_outcomes_since_overrides_window(tmp_path: Path, capsys):
    db = _seed_db(tmp_path)
    rc = cli_main([
        "stats",
        "--db-path", str(db),
        "--outcomes",
        "--since", "30",
        "--json",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["window_days"] == 30


def test_outcomes_text_renders_table(tmp_path: Path, capsys):
    db = _seed_db(tmp_path)
    rc = cli_main([
        "stats",
        "--db-path", str(db),
        "--outcomes",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "# Review outcome summary" in out
    assert "| Domain |" in out
    assert "| recovery |" in out
    assert "| aggregate |" in out


def test_outcomes_text_with_domain_filter_one_row(tmp_path: Path, capsys):
    db = _seed_db(tmp_path)
    rc = cli_main([
        "stats",
        "--db-path", str(db),
        "--outcomes",
        "--domain", "running",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "| running |" in out
    # Other domains and aggregate row are NOT present in single-domain mode.
    assert "| recovery |" not in out
    assert "| aggregate |" not in out


def test_outcomes_invalid_domain_rejected(tmp_path: Path, capsys):
    db = _seed_db(tmp_path)
    with pytest.raises(SystemExit):
        cli_main([
            "stats",
            "--db-path", str(db),
            "--outcomes",
            "--domain", "fitness",  # not a valid v1 domain
        ])
    err = capsys.readouterr().err
    assert "fitness" in err or "invalid choice" in err
