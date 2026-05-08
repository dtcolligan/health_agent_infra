"""W51 — data quality ledger.

Pins:

  1. Migration 021 creates ``data_quality_daily`` with the documented
     columns + PK + indexes.
  2. ``project_data_quality_for_date`` writes one row per (domain,
     source) and is idempotent (PRIMARY KEY upsert).
  3. ``snapshot.<domain>.data_quality`` carries the projected fields
     even before the projector runs, since the snapshot reads them
     from in-memory state.
  4. CLI: ``hai stats --data-quality`` lazy-projects today and renders
     a JSON / markdown view.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.data_quality import (
    DOMAINS,
    project_data_quality_for_date,
    read_data_quality_rows,
)
from health_agent_infra.core.state import (
    build_snapshot,
    initialize_database,
    open_connection,
)


USER = "u_test"
AS_OF = date(2026, 4, 24)


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def test_migration_021_creates_data_quality_daily(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        rows = conn.execute(
            "PRAGMA table_info(data_quality_daily)"
        ).fetchall()
        cols = {r["name"] for r in rows}
    finally:
        conn.close()

    assert cols == {
        "user_id", "as_of_date", "domain", "source",
        "freshness_hours", "coverage_band", "missingness",
        "source_unavailable", "user_input_pending",
        "suspicious_discontinuity",
        "cold_start_window_state", "computed_at",
    }


def test_migration_021_creates_indexes(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        idxs = {
            r["name"] for r in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='data_quality_daily'"
            ).fetchall()
        }
    finally:
        conn.close()
    assert "idx_data_quality_daily_date" in idxs
    assert "idx_data_quality_daily_domain" in idxs


def test_snapshot_attaches_data_quality_block_per_domain(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 4, 24, 23, 45),
        )
    finally:
        conn.close()

    for domain in DOMAINS:
        assert "data_quality" in snap[domain]
        block = snap[domain]["data_quality"]
        assert "coverage_band" in block
        assert "missingness" in block
        assert "cold_start_window_state" in block
        assert isinstance(block["source_unavailable"], bool)
        assert isinstance(block["user_input_pending"], bool)


def test_projector_writes_and_is_idempotent(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 4, 24, 23, 45),
        )
        first = project_data_quality_for_date(conn, snapshot=snap)
        second = project_data_quality_for_date(conn, snapshot=snap)
        rows = read_data_quality_rows(conn, user_id=USER)
    finally:
        conn.close()

    # One row per domain (single source per domain in v0.1.8).
    assert first == len(DOMAINS)
    assert second == len(DOMAINS)
    assert len(rows) == len(DOMAINS)


def test_cli_data_quality_is_read_only_on_fresh_db(tmp_path: Path, capsys):
    """Codex P1-1 contract: hai stats --data-quality is read-only.
    A fresh DB with no `hai clean` runs returns empty rows — never
    triggers a hidden write to seed them."""

    db = _init_db(tmp_path)
    rc = cli_main([
        "stats",
        "--db-path", str(db),
        "--data-quality",
        "--json",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["user_id"] == "u_local_1"
    assert payload["since_days"] == 7
    assert isinstance(payload["rows"], list)
    # Fresh DB: no `hai clean` has run yet, so no data_quality_daily
    # rows exist. The stats surface honestly returns empty rather
    # than mutating to seed.
    assert payload["rows"] == []

    # Confirm the DB was NOT mutated by the read-only call.
    conn = open_connection(db)
    try:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM data_quality_daily"
        ).fetchone()["n"]
    finally:
        conn.close()
    assert count == 0, (
        "hai stats --data-quality is annotated read-only but mutated "
        "data_quality_daily — capability contract violation"
    )


def test_cli_data_quality_returns_rows_after_projection(tmp_path: Path, capsys):
    """When the projector has run (via build_snapshot +
    project_data_quality_for_date), the read-only stats surface
    returns the rows."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id="u_local_1",
            now_local=datetime(2026, 4, 24, 23, 45),
        )
        project_data_quality_for_date(conn, snapshot=snap)
    finally:
        conn.close()

    rc = cli_main([
        "stats",
        "--db-path", str(db),
        "--data-quality",
        "--since", "30",
        "--json",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["rows"]) == 6
    assert {r["domain"] for r in payload["rows"]} == set(DOMAINS)


def test_cli_data_quality_text_table_renders(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "stats",
        "--db-path", str(db),
        "--data-quality",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "# Data quality" in out
    assert "| Date | Domain | Source |" in out
