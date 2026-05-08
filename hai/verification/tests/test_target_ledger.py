"""W50 — target ledger MVP.

Pins:

  1. Migration 020 creates the table with documented columns + CHECK
     constraints + indexes.
  2. ``add_target`` round-trips every field through SQLite.
  3. ``list_active_target`` returns rows whose effective window covers
     as_of_date AND status is 'active'.
  4. ``archive_target`` flips status non-destructively.
  5. ``supersede_target`` inserts the new row + links the old row.
  6. ``snapshot.target`` exposes active rows for as_of_date.
  7. CLI: ``hai target set`` + ``hai target list`` + ``hai target
     archive`` round-trip end-to-end.
  8. CHECK constraints reject invalid status / target_type;
     validators reject bound + window inversions.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.state import (
    build_snapshot,
    initialize_database,
    open_connection,
)
from health_agent_infra.core.target import (
    add_target,
    archive_target,
    list_active_target,
    list_target,
    supersede_target,
)
from health_agent_infra.core.target.store import (
    TargetRecord,
    TargetValidationError,
)


USER = "u_test"
AS_OF = date(2026, 4, 24)


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


# ---------------------------------------------------------------------------
# Migration shape
# ---------------------------------------------------------------------------


def test_migration_020_creates_target_table(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        rows = conn.execute("PRAGMA table_info(target)").fetchall()
        cols = {r["name"] for r in rows}
    finally:
        conn.close()

    assert cols == {
        "target_id", "user_id", "domain", "target_type", "status",
        "value_json", "unit", "lower_bound", "upper_bound",
        "effective_from", "effective_to", "review_after",
        "reason", "source", "ingest_actor", "created_at",
        "supersedes_target_id", "superseded_by_target_id",
    }


def test_migration_020_creates_indexes(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        idxs = {
            r["name"] for r in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='target'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert "idx_target_active_window" in idxs
    assert "idx_target_domain_type" in idxs
    assert "idx_target_supersedes" in idxs


# ---------------------------------------------------------------------------
# add_target
# ---------------------------------------------------------------------------


def test_add_target_round_trips(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        rec = add_target(
            conn,
            user_id=USER,
            domain="nutrition",
            target_type="hydration_ml",
            value=3000,
            unit="ml",
            effective_from=AS_OF,
            reason="default daily hydration",
        )
        rows = list_target(conn, user_id=USER)
    finally:
        conn.close()

    assert len(rows) == 1
    assert rows[0].target_id == rec.target_id
    assert rows[0].domain == "nutrition"
    assert rows[0].target_type == "hydration_ml"
    assert rows[0].value == 3000
    assert rows[0].unit == "ml"


def test_add_target_rejects_invalid_target_type(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        with pytest.raises(TargetValidationError):
            add_target(
                conn,
                user_id=USER,
                domain="nutrition",
                target_type="ferrum_mg",  # not in v1 vocabulary
                value=15,
                unit="mg",
                effective_from=AS_OF,
            )
    finally:
        conn.close()


def test_add_target_rejects_inverted_bounds(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        with pytest.raises(TargetValidationError):
            add_target(
                conn,
                user_id=USER,
                domain="nutrition",
                target_type="protein_g",
                value=160,
                unit="g",
                effective_from=AS_OF,
                lower_bound=200.0,
                upper_bound=140.0,
            )
    finally:
        conn.close()


def test_add_target_rejects_inverted_effective_window(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        with pytest.raises(TargetValidationError):
            add_target(
                conn,
                user_id=USER,
                domain="sleep",
                target_type="sleep_duration_h",
                value=8,
                unit="h",
                effective_from=AS_OF,
                effective_to=date(2026, 4, 1),
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# list_active_target
# ---------------------------------------------------------------------------


def test_list_active_target_window_and_status(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        in_window = add_target(
            conn,
            user_id=USER,
            domain="nutrition",
            target_type="hydration_ml",
            value=3000,
            unit="ml",
            effective_from=AS_OF,
        )
        # Out of window.
        add_target(
            conn,
            user_id=USER,
            domain="nutrition",
            target_type="hydration_ml",
            value=2500,
            unit="ml",
            effective_from=date(2026, 1, 1),
            effective_to=date(2026, 1, 31),
        )
        # In window but archived.
        archived_target = add_target(
            conn,
            user_id=USER,
            domain="nutrition",
            target_type="protein_g",
            value=160,
            unit="g",
            effective_from=AS_OF,
        )
        archive_target(conn, target_id=archived_target.target_id, user_id=USER)
        active = list_active_target(conn, user_id=USER, as_of_date=AS_OF)
    finally:
        conn.close()

    assert [r.target_id for r in active] == [in_window.target_id]


# ---------------------------------------------------------------------------
# archive + supersede
# ---------------------------------------------------------------------------


def test_archive_target_flips_status(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        rec = add_target(
            conn,
            user_id=USER,
            domain="nutrition",
            target_type="hydration_ml",
            value=3000,
            unit="ml",
            effective_from=AS_OF,
        )
        ok = archive_target(conn, target_id=rec.target_id, user_id=USER)
        rows = list_target(conn, user_id=USER)
    finally:
        conn.close()

    assert ok is True
    assert len(rows) == 1
    assert rows[0].status == "archived"


def test_supersede_target_links_old_and_new(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        original = add_target(
            conn,
            user_id=USER,
            domain="nutrition",
            target_type="protein_g",
            value=140,
            unit="g",
            effective_from=AS_OF,
        )
        new_record = TargetRecord(
            target_id="target_new",
            user_id=USER,
            domain="nutrition",
            target_type="protein_g",
            status="active",
            value=170,
            unit="g",
            lower_bound=None,
            upper_bound=None,
            effective_from=AS_OF,
            effective_to=None,
            review_after=None,
            reason="bumped after lifting cycle",
            source="user_authored",
            ingest_actor="cli",
            created_at=datetime.now(timezone.utc),
            supersedes_target_id=None,
            superseded_by_target_id=None,
        )
        supersede_target(conn, old_target_id=original.target_id, new_record=new_record)
        rows = {r.target_id: r for r in list_target(conn, user_id=USER)}
    finally:
        conn.close()

    assert rows[original.target_id].status == "superseded"
    assert rows[original.target_id].superseded_by_target_id == "target_new"
    assert rows["target_new"].supersedes_target_id == original.target_id
    assert rows["target_new"].value == 170


# ---------------------------------------------------------------------------
# snapshot integration
# ---------------------------------------------------------------------------


def test_snapshot_target_block_carries_active_rows(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        add_target(
            conn,
            user_id=USER,
            domain="nutrition",
            target_type="hydration_ml",
            value=3000,
            unit="ml",
            effective_from=AS_OF,
        )
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 4, 24, 23, 45),
        )
    finally:
        conn.close()

    assert "target" in snap
    assert isinstance(snap["target"], list)
    assert len(snap["target"]) == 1
    assert snap["target"][0]["target_type"] == "hydration_ml"
    assert json.loads(snap["target"][0]["value_json"]) == {"value": 3000}


# ---------------------------------------------------------------------------
# CLI surfaces
# ---------------------------------------------------------------------------


def test_cli_target_set_inserts_row(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "target", "set",
        "--db-path", str(db),
        "--user-id", USER,
        "--domain", "nutrition",
        "--target-type", "hydration_ml",
        "--value", "3000",
        "--unit", "ml",
        "--effective-from", AS_OF.isoformat(),
        "--reason", "default",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["domain"] == "nutrition"
    assert payload["target_type"] == "hydration_ml"
    assert payload["status"] == "active"
    assert json.loads(payload["value_json"]) == {"value": 3000}


def test_cli_target_list_returns_active(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    cli_main([
        "target", "set",
        "--db-path", str(db), "--user-id", USER,
        "--domain", "nutrition", "--target-type", "protein_g",
        "--value", "160", "--unit", "g",
        "--effective-from", AS_OF.isoformat(),
        "--reason", "lifting cycle",
    ])
    capsys.readouterr()
    rc = cli_main([
        "target", "list",
        "--db-path", str(db), "--user-id", USER,
        "--as-of", AS_OF.isoformat(),
    ])
    assert rc == 0
    listed = json.loads(capsys.readouterr().out)
    assert len(listed) == 1
    assert listed[0]["target_type"] == "protein_g"


# ---------------------------------------------------------------------------
# W57 / Codex P1-2 governance: agent-proposed cannot land active
# ---------------------------------------------------------------------------


def test_target_store_rejects_agent_proposed_active(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        with pytest.raises(TargetValidationError) as exc_info:
            add_target(
                conn,
                user_id=USER,
                domain="nutrition",
                target_type="hydration_ml",
                value=3000,
                unit="ml",
                effective_from=AS_OF,
                source="agent_proposed",
                status="active",
            )
    finally:
        conn.close()
    assert "user_authored" in str(exc_info.value)


def test_commit_target_promotes_proposed_to_active(tmp_path: Path):
    from health_agent_infra.core.target import commit_target

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        record = add_target(
            conn,
            user_id=USER,
            domain="nutrition",
            target_type="hydration_ml",
            value=3000,
            unit="ml",
            effective_from=AS_OF,
            source="agent_proposed",
            status="proposed",
        )
        ok = commit_target(
            conn, target_id=record.target_id, user_id=USER,
        )
        rows = list_target(conn, user_id=USER)
    finally:
        conn.close()
    assert ok is True
    assert rows[0].status == "active"


def test_cli_target_set_rejects_agent_proposed_active(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "target", "set",
        "--db-path", str(db),
        "--user-id", USER,
        "--domain", "nutrition",
        "--target-type", "hydration_ml",
        "--value", "3000",
        "--unit", "ml",
        "--effective-from", AS_OF.isoformat(),
        "--reason", "agent suggestion",
        "--source", "agent_proposed",
        "--status", "active",
    ])
    assert rc != 0
    err = capsys.readouterr().err
    assert "agent_proposed" in err


def test_cli_target_commit_round_trips(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "target", "set",
        "--db-path", str(db),
        "--user-id", USER,
        "--domain", "nutrition",
        "--target-type", "hydration_ml",
        "--value", "3000",
        "--unit", "ml",
        "--effective-from", AS_OF.isoformat(),
        "--reason", "agent suggestion",
        "--source", "agent_proposed",
        "--status", "proposed",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    target_id = payload["target_id"]

    rc = cli_main([
        "target", "commit",
        "--db-path", str(db),
        "--user-id", USER,
        "--target-id", target_id,
        "--confirm",  # W57: non-interactive caller must opt in.
    ])
    assert rc == 0
    promoted = json.loads(capsys.readouterr().out)
    assert promoted == {"target_id": target_id, "status": "active"}


def test_agent_supersede_target_leaves_old_active_alone(tmp_path: Path):
    """Codex R2-2 invariant: agent-proposed target supersede inserts
    a proposed replacement + supersedes link, but leaves the old
    active row in place."""

    from health_agent_infra.core.target.store import TargetRecord

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        original = add_target(
            conn,
            user_id=USER,
            domain="nutrition",
            target_type="protein_g",
            value=140,
            unit="g",
            effective_from=AS_OF,
        )
        replacement = TargetRecord(
            target_id="target_agent_replacement",
            user_id=USER,
            domain="nutrition",
            target_type="protein_g",
            status="proposed",   # agent-proposed lands as proposed
            value=170,
            unit="g",
            lower_bound=None,
            upper_bound=None,
            effective_from=AS_OF,
            effective_to=None,
            review_after=None,
            reason="agent suggestion based on training load",
            source="agent_proposed",
            ingest_actor="claude_code",
            created_at=datetime.now(timezone.utc),
            supersedes_target_id=None,
            superseded_by_target_id=None,
        )
        supersede_target(
            conn, old_target_id=original.target_id, new_record=replacement,
        )
        rows_by_id = {r.target_id: r for r in list_target(conn, user_id=USER)}
    finally:
        conn.close()

    assert rows_by_id[original.target_id].status == "active"
    assert rows_by_id[original.target_id].superseded_by_target_id is None
    assert rows_by_id["target_agent_replacement"].status == "proposed"
    assert (
        rows_by_id["target_agent_replacement"].supersedes_target_id
        == original.target_id
    )


def test_commit_target_with_supersedes_link_atomically_deactivates_parent(
    tmp_path: Path,
):
    from health_agent_infra.core.target import commit_target
    from health_agent_infra.core.target.store import TargetRecord

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        original = add_target(
            conn,
            user_id=USER,
            domain="nutrition",
            target_type="protein_g",
            value=140,
            unit="g",
            effective_from=AS_OF,
        )
        replacement = TargetRecord(
            target_id="target_agent_replacement",
            user_id=USER, domain="nutrition",
            target_type="protein_g", status="proposed",
            value=170, unit="g",
            lower_bound=None, upper_bound=None,
            effective_from=AS_OF, effective_to=None, review_after=None,
            reason="agent suggestion", source="agent_proposed",
            ingest_actor="claude_code",
            created_at=datetime.now(timezone.utc),
            supersedes_target_id=None,
            superseded_by_target_id=None,
        )
        supersede_target(
            conn, old_target_id=original.target_id, new_record=replacement,
        )
        ok = commit_target(
            conn, target_id="target_agent_replacement", user_id=USER,
        )
        rows_by_id = {r.target_id: r for r in list_target(conn, user_id=USER)}
    finally:
        conn.close()

    assert ok is True
    assert rows_by_id["target_agent_replacement"].status == "active"
    assert rows_by_id[original.target_id].status == "superseded"
    assert (
        rows_by_id[original.target_id].superseded_by_target_id
        == "target_agent_replacement"
    )


def test_cli_target_archive_round_trips(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    cli_main([
        "target", "set",
        "--db-path", str(db), "--user-id", USER,
        "--domain", "nutrition", "--target-type", "calories_kcal",
        "--value", "2400", "--unit", "kcal",
        "--effective-from", AS_OF.isoformat(),
        "--reason", "to archive",
    ])
    payload = json.loads(capsys.readouterr().out)
    target_id = payload["target_id"]

    rc = cli_main([
        "target", "archive",
        "--db-path", str(db), "--user-id", USER,
        "--target-id", target_id,
        "--confirm",  # W57: archive of an active row is deactivation.
    ])
    assert rc == 0
    archived = json.loads(capsys.readouterr().out)
    assert archived == {"target_id": target_id, "status": "archived"}

    rc = cli_main([
        "target", "list",
        "--db-path", str(db), "--user-id", USER,
        "--as-of", AS_OF.isoformat(),
    ])
    assert rc == 0
    active = json.loads(capsys.readouterr().out)
    assert active == []
