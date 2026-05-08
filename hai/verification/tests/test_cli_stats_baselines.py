"""W40 — `hai stats --baselines` CLI surface."""

from __future__ import annotations

import json
from pathlib import Path

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.state import initialize_database


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def test_baselines_json_emits_per_domain_block(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "stats",
        "--db-path", str(db),
        "--baselines",
        "--json",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["user_id"] == "u_local_1"
    assert "threshold_source" in payload
    assert set(payload["domains"].keys()) == {
        "recovery", "running", "sleep", "stress", "strength", "nutrition",
    }


def test_baselines_domain_filter_returns_one(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "stats",
        "--db-path", str(db),
        "--baselines",
        "--domain", "recovery",
        "--json",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert list(payload["domains"].keys()) == ["recovery"]


def test_baselines_text_renders_section_per_domain(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "stats",
        "--db-path", str(db),
        "--baselines",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "# Baselines" in out
    for domain in ("recovery", "running", "sleep", "stress", "strength", "nutrition"):
        assert f"## {domain}" in out
