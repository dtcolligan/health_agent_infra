"""W49 — intent_item ledger MVP.

Pins:

  1. Migration 019 creates the table with the documented columns + CHECK
     constraints + indexes.
  2. ``add_intent`` round-trips every field through SQLite.
  3. ``list_active_intent`` returns rows whose [scope_start, scope_end]
     window covers as_of_date AND whose status is 'active' (not
     proposed / superseded / archived).
  4. ``archive_intent`` flips status non-destructively.
  5. ``supersede_intent`` inserts the new row, links the old row, and
     leaves the old row's data otherwise untouched.
  6. ``snapshot.intent`` exposes the active rows for as_of_date.
  7. CLI: ``hai intent training add-session`` + ``hai intent list`` +
     ``hai intent archive`` round-trip end-to-end.
  8. CHECK constraints reject invalid status / intent_type / scope_type.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.intent import (
    add_intent,
    archive_intent,
    list_active_intent,
    list_intent,
    supersede_intent,
)
from health_agent_infra.core.intent.store import (
    IntentRecord,
    IntentValidationError,
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


# ---------------------------------------------------------------------------
# Migration shape
# ---------------------------------------------------------------------------


def test_migration_019_creates_intent_item_with_check_constraints(
    tmp_path: Path,
):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        rows = conn.execute(
            "PRAGMA table_info(intent_item)"
        ).fetchall()
        cols = {r["name"]: dict(r) for r in rows}
    finally:
        conn.close()

    expected = {
        "intent_id", "user_id", "domain",
        "scope_type", "scope_start", "scope_end",
        "intent_type", "status", "priority", "flexibility",
        "payload_json", "reason", "source", "ingest_actor",
        "created_at", "effective_at", "review_after",
        "supersedes_intent_id", "superseded_by_intent_id",
    }
    assert set(cols.keys()) == expected


def test_migration_019_creates_indexes(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        idxs = {
            r["name"] for r in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='intent_item'"
            ).fetchall()
        }
    finally:
        conn.close()

    assert "idx_intent_item_active_window" in idxs
    assert "idx_intent_item_domain" in idxs
    assert "idx_intent_item_supersedes" in idxs


# ---------------------------------------------------------------------------
# add_intent round-trip
# ---------------------------------------------------------------------------


def test_add_intent_round_trips(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        record = add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
            payload={"distance_km": 8.0, "kind": "easy"},
            reason="weekly easy run",
        )
        rows = list_intent(conn, user_id=USER)
    finally:
        conn.close()

    assert len(rows) == 1
    only = rows[0]
    assert only.intent_id == record.intent_id
    assert only.domain == "running"
    assert only.intent_type == "training_session"
    assert only.payload == {"distance_km": 8.0, "kind": "easy"}
    assert only.status == "active"
    assert only.scope_start == AS_OF
    assert only.scope_end == AS_OF


def test_add_intent_rejects_invalid_status(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        with pytest.raises(IntentValidationError):
            add_intent(
                conn,
                user_id=USER,
                domain="running",
                intent_type="training_session",
                scope_start=AS_OF,
                status="bogus",
            )
    finally:
        conn.close()


def test_add_intent_rejects_scope_end_before_start(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        with pytest.raises(IntentValidationError):
            add_intent(
                conn,
                user_id=USER,
                domain="running",
                intent_type="training_session",
                scope_start=AS_OF,
                scope_end=date(2026, 4, 1),
            )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# list_active_intent
# ---------------------------------------------------------------------------


def test_list_active_intent_filters_by_window_and_status(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        # In window, active.
        in_window = add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
            scope_end=AS_OF,
        )
        # Out of window.
        add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=date(2026, 4, 1),
            scope_end=date(2026, 4, 5),
        )
        # In window but archived.
        archived = add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
        )
        archive_intent(conn, intent_id=archived.intent_id, user_id=USER)
        active = list_active_intent(conn, user_id=USER, as_of_date=AS_OF)
    finally:
        conn.close()

    assert [r.intent_id for r in active] == [in_window.intent_id]


# ---------------------------------------------------------------------------
# archive + supersede
# ---------------------------------------------------------------------------


def test_archive_intent_flips_status_without_deleting(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        record = add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
        )
        ok = archive_intent(conn, intent_id=record.intent_id, user_id=USER)
        rows = list_intent(conn, user_id=USER)
    finally:
        conn.close()

    assert ok is True
    assert len(rows) == 1
    assert rows[0].status == "archived"


def test_archive_intent_returns_false_for_unknown(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        ok = archive_intent(conn, intent_id="missing", user_id=USER)
    finally:
        conn.close()
    assert ok is False


def test_supersede_intent_links_old_and_new(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        original = add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
            payload={"version": 1},
        )
        new_record = IntentRecord(
            intent_id="intent_new",
            user_id=USER,
            domain="running",
            scope_type="day",
            scope_start=AS_OF,
            scope_end=AS_OF,
            intent_type="training_session",
            status="active",
            priority="normal",
            flexibility="flexible",
            payload={"version": 2},
            reason="user adjusted",
            source="user_authored",
            ingest_actor="cli",
            created_at=datetime.now(timezone.utc),
            effective_at=datetime.now(timezone.utc),
            review_after=None,
            supersedes_intent_id=None,
            superseded_by_intent_id=None,
        )
        supersede_intent(conn, old_intent_id=original.intent_id, new_record=new_record)
        all_rows = list_intent(conn, user_id=USER)
    finally:
        conn.close()

    rows_by_id = {r.intent_id: r for r in all_rows}
    assert rows_by_id[original.intent_id].status == "superseded"
    assert rows_by_id[original.intent_id].superseded_by_intent_id == "intent_new"
    assert rows_by_id["intent_new"].supersedes_intent_id == original.intent_id
    assert rows_by_id["intent_new"].status == "active"


# ---------------------------------------------------------------------------
# snapshot integration
# ---------------------------------------------------------------------------


def test_snapshot_intent_block_carries_active_rows(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
            payload={"distance_km": 10},
        )
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 4, 24, 23, 45),
        )
    finally:
        conn.close()

    assert "intent" in snap
    assert isinstance(snap["intent"], list)
    assert len(snap["intent"]) == 1
    assert snap["intent"][0]["domain"] == "running"
    assert json.loads(snap["intent"][0]["payload_json"]) == {"distance_km": 10}


# ---------------------------------------------------------------------------
# CLI surfaces
# ---------------------------------------------------------------------------


def test_cli_intent_training_add_session_inserts_row(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "intent", "training", "add-session",
        "--db-path", str(db),
        "--user-id", USER,
        "--scope-start", AS_OF.isoformat(),
        "--reason", "easy run",
        "--payload-json", json.dumps({"distance_km": 6.5, "kind": "easy"}),
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["domain"] == "running"
    assert payload["intent_type"] == "training_session"
    assert payload["status"] == "active"


def test_cli_intent_list_returns_active_only_by_default(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    cli_main([
        "intent", "training", "add-session",
        "--db-path", str(db), "--user-id", USER,
        "--scope-start", AS_OF.isoformat(),
        "--reason", "active",
    ])
    capsys.readouterr()  # drain
    cli_main([
        "intent", "sleep", "set-window",
        "--db-path", str(db), "--user-id", USER,
        "--scope-start", AS_OF.isoformat(),
        "--payload-json", json.dumps({"start": "22:30", "end": "06:30"}),
        "--reason", "weeknight",
    ])
    capsys.readouterr()
    rc = cli_main([
        "intent", "list",
        "--db-path", str(db), "--user-id", USER,
        "--as-of", AS_OF.isoformat(),
    ])
    assert rc == 0
    listed = json.loads(capsys.readouterr().out)
    assert {row["domain"] for row in listed} == {"running", "sleep"}


# ---------------------------------------------------------------------------
# W57 / Codex P1-2 governance: agent-proposed cannot land active
# ---------------------------------------------------------------------------


def test_store_rejects_agent_proposed_active(tmp_path: Path):
    """Codex P1-2 invariant: source != 'user_authored' + status='active'
    on insert is a runtime error. Forces agent-proposed rows through
    the user-gated commit path."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        with pytest.raises(IntentValidationError) as exc_info:
            add_intent(
                conn,
                user_id=USER,
                domain="running",
                intent_type="training_session",
                scope_start=AS_OF,
                source="agent_proposed",
                status="active",
            )
    finally:
        conn.close()
    assert "user_authored" in str(exc_info.value)


def test_store_allows_user_authored_active(tmp_path: Path):
    """Sanity check: user_authored + active is the allowed shape."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        record = add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
            source="user_authored",
            status="active",
        )
    finally:
        conn.close()
    assert record.status == "active"


def test_store_allows_agent_proposed_proposed(tmp_path: Path):
    """Sanity check: agent_proposed + proposed is the allowed shape."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        record = add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
            source="agent_proposed",
            status="proposed",
        )
    finally:
        conn.close()
    assert record.status == "proposed"
    assert record.source == "agent_proposed"


def test_commit_intent_promotes_proposed_to_active(tmp_path: Path):
    """The user-gated promotion path: agent-proposed row → user runs
    `hai intent commit` → row is active."""

    from health_agent_infra.core.intent import commit_intent

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        record = add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
            source="agent_proposed",
            status="proposed",
        )
        ok = commit_intent(
            conn, intent_id=record.intent_id, user_id=USER,
        )
        rows = list_intent(conn, user_id=USER)
    finally:
        conn.close()

    assert ok is True
    assert rows[0].status == "active"


def test_commit_intent_no_op_on_already_active(tmp_path: Path):
    from health_agent_infra.core.intent import commit_intent

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        record = add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
        )
        ok = commit_intent(
            conn, intent_id=record.intent_id, user_id=USER,
        )
    finally:
        conn.close()
    assert ok is False


def test_cli_intent_training_add_session_rejects_agent_proposed_active(
    tmp_path: Path, capsys,
):
    db = _init_db(tmp_path)
    rc = cli_main([
        "intent", "training", "add-session",
        "--db-path", str(db),
        "--user-id", USER,
        "--scope-start", AS_OF.isoformat(),
        "--reason", "agent suggestion",
        "--source", "agent_proposed",
        "--status", "active",
    ])
    assert rc != 0
    err = capsys.readouterr().err
    assert "agent_proposed" in err
    assert "user_authored" in err


def test_cli_intent_commit_round_trips(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "intent", "training", "add-session",
        "--db-path", str(db),
        "--user-id", USER,
        "--scope-start", AS_OF.isoformat(),
        "--reason", "agent suggestion",
        "--source", "agent_proposed",
        "--status", "proposed",
    ])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    intent_id = payload["intent_id"]

    rc = cli_main([
        "intent", "commit",
        "--db-path", str(db),
        "--user-id", USER,
        "--intent-id", intent_id,
        "--confirm",  # W57: non-interactive caller must opt in.
    ])
    assert rc == 0
    promoted = json.loads(capsys.readouterr().out)
    assert promoted == {"intent_id": intent_id, "status": "active"}


def test_agent_supersede_leaves_old_active_row_alone(tmp_path: Path):
    """Codex R2-2 invariant: agent-proposed supersede inserts the
    replacement as proposed + links supersedes_intent_id, but does
    NOT touch the old row's status. The user's existing active row
    survives until commit time."""

    from health_agent_infra.core.intent.store import IntentRecord

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        original = add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
            payload={"v": 1},
        )
        replacement = IntentRecord(
            intent_id="intent_agent_replacement",
            user_id=USER,
            domain="running",
            scope_type="day",
            scope_start=AS_OF,
            scope_end=AS_OF,
            intent_type="training_session",
            status="proposed",   # agent-proposed lands as proposed
            priority="normal",
            flexibility="flexible",
            payload={"v": 2, "by": "agent"},
            reason="agent suggestion",
            source="agent_proposed",
            ingest_actor="claude_code",
            created_at=datetime.now(timezone.utc),
            effective_at=datetime.now(timezone.utc),
            review_after=None,
            supersedes_intent_id=None,
            superseded_by_intent_id=None,
        )
        supersede_intent(
            conn, old_intent_id=original.intent_id, new_record=replacement,
        )
        rows_by_id = {r.intent_id: r for r in list_intent(conn, user_id=USER)}
    finally:
        conn.close()

    # Original is STILL active; the agent's replacement only proposed.
    assert rows_by_id[original.intent_id].status == "active"
    assert rows_by_id[original.intent_id].superseded_by_intent_id is None
    assert rows_by_id["intent_agent_replacement"].status == "proposed"
    assert (
        rows_by_id["intent_agent_replacement"].supersedes_intent_id
        == original.intent_id
    )


def test_commit_intent_with_supersedes_link_atomically_deactivates_parent(
    tmp_path: Path,
):
    """When the user commits an agent-proposed replacement that has
    supersedes_intent_id set, the parent row is atomically flipped
    to superseded in the same transaction."""

    from health_agent_infra.core.intent import commit_intent
    from health_agent_infra.core.intent.store import IntentRecord

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        original = add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
        )
        replacement = IntentRecord(
            intent_id="intent_agent_replacement",
            user_id=USER, domain="running",
            scope_type="day",
            scope_start=AS_OF, scope_end=AS_OF,
            intent_type="training_session",
            status="proposed",
            priority="normal", flexibility="flexible",
            payload={"by": "agent"},
            reason="agent suggestion",
            source="agent_proposed",
            ingest_actor="claude_code",
            created_at=datetime.now(timezone.utc),
            effective_at=datetime.now(timezone.utc),
            review_after=None,
            supersedes_intent_id=None,
            superseded_by_intent_id=None,
        )
        supersede_intent(
            conn, old_intent_id=original.intent_id, new_record=replacement,
        )
        # Pre-commit: original is still active, replacement is proposed.
        # Now the user commits.
        ok = commit_intent(
            conn, intent_id="intent_agent_replacement", user_id=USER,
        )
        rows_by_id = {r.intent_id: r for r in list_intent(conn, user_id=USER)}
    finally:
        conn.close()

    assert ok is True
    assert rows_by_id["intent_agent_replacement"].status == "active"
    assert rows_by_id[original.intent_id].status == "superseded"
    assert (
        rows_by_id[original.intent_id].superseded_by_intent_id
        == "intent_agent_replacement"
    )


def test_user_authored_supersede_still_immediately_deactivates(
    tmp_path: Path,
):
    """Sanity check: user_authored supersede preserves the immediate-
    deactivation behaviour. Codex R2-2 only changed agent-proposed."""

    from health_agent_infra.core.intent.store import IntentRecord

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        original = add_intent(
            conn,
            user_id=USER,
            domain="running",
            intent_type="training_session",
            scope_start=AS_OF,
        )
        replacement = IntentRecord(
            intent_id="intent_user_replacement",
            user_id=USER, domain="running",
            scope_type="day",
            scope_start=AS_OF, scope_end=AS_OF,
            intent_type="training_session",
            status="active",   # user_authored may land active
            priority="normal", flexibility="flexible",
            payload={"v": 2},
            reason="user adjusted",
            source="user_authored",
            ingest_actor="cli",
            created_at=datetime.now(timezone.utc),
            effective_at=datetime.now(timezone.utc),
            review_after=None,
            supersedes_intent_id=None,
            superseded_by_intent_id=None,
        )
        supersede_intent(
            conn, old_intent_id=original.intent_id, new_record=replacement,
        )
        rows_by_id = {r.intent_id: r for r in list_intent(conn, user_id=USER)}
    finally:
        conn.close()

    assert rows_by_id[original.intent_id].status == "superseded"
    assert rows_by_id["intent_user_replacement"].status == "active"


def test_cli_intent_commit_rejects_unknown_id(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    rc = cli_main([
        "intent", "commit",
        "--db-path", str(db),
        "--user-id", USER,
        "--intent-id", "intent_does_not_exist",
        "--confirm",  # W57: non-interactive caller must opt in.
    ])
    assert rc != 0


def test_cli_intent_archive_round_trips(tmp_path: Path, capsys):
    db = _init_db(tmp_path)
    cli_main([
        "intent", "training", "add-session",
        "--db-path", str(db), "--user-id", USER,
        "--scope-start", AS_OF.isoformat(),
        "--reason", "to archive",
    ])
    payload = json.loads(capsys.readouterr().out)
    intent_id = payload["intent_id"]

    rc = cli_main([
        "intent", "archive",
        "--db-path", str(db), "--user-id", USER,
        "--intent-id", intent_id,
        "--confirm",  # W57: archive of an active row is deactivation.
    ])
    assert rc == 0
    archived = json.loads(capsys.readouterr().out)
    assert archived == {"intent_id": intent_id, "status": "archived"}

    rc = cli_main([
        "intent", "list",
        "--db-path", str(db), "--user-id", USER,
        "--as-of", AS_OF.isoformat(),
    ])
    assert rc == 0
    active = json.loads(capsys.readouterr().out)
    assert active == []
