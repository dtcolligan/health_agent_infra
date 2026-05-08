"""W57 runtime-gate contract tests (v0.1.9 B1).

Pin the runtime invariant the v0.1.9 audit cycle closed: every
intent/target activation OR deactivation handler refuses
non-interactive callers without ``--confirm``.

AGENTS.md W57 reserves these mutations for an explicit user commit.
The capabilities manifest declares the four affected handlers
``agent_safe=False``; this test file proves the runtime enforces
the same posture independent of the manifest.

Coverage:
  1. Manifest assertion: every W57 handler has ``agent_safe=False``.
  2. Runtime assertion: each handler refuses non-tty + no --confirm
     with a USER_INPUT exit code and zero state mutation.
  3. Runtime assertion: each handler accepts ``--confirm`` and
     completes the state transition.
  4. Runtime assertion: archive specifically refuses non-confirmed
     calls — the bug Codex caught (archive was ``agent_safe=True``
     and could deactivate active user state without a gate).
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.cli import build_parser, main as cli_main
from health_agent_infra.core.capabilities import build_manifest
from health_agent_infra.core.state import initialize_database, open_connection


AS_OF = date(2026, 4, 26)
USER = "u_w57"


W57_HANDLERS: tuple[str, ...] = (
    "hai intent commit",
    "hai intent archive",
    "hai target commit",
    "hai target archive",
)


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _seed_proposed_intent(db: Path) -> str:
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
    with closing(open_connection(db)) as conn:
        row = conn.execute(
            "SELECT intent_id FROM intent_item WHERE user_id = ? "
            "AND status = 'proposed' ORDER BY created_at DESC LIMIT 1",
            (USER,),
        ).fetchone()
    assert row is not None
    return row[0]


def _seed_active_intent(db: Path) -> str:
    rc = cli_main([
        "intent", "training", "add-session",
        "--db-path", str(db),
        "--user-id", USER,
        "--scope-start", AS_OF.isoformat(),
        "--reason", "user authored",
    ])
    assert rc == 0
    with closing(open_connection(db)) as conn:
        row = conn.execute(
            "SELECT intent_id FROM intent_item WHERE user_id = ? "
            "AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (USER,),
        ).fetchone()
    assert row is not None
    return row[0]


def _seed_proposed_target(db: Path) -> str:
    rc = cli_main([
        "target", "set",
        "--db-path", str(db), "--user-id", USER,
        "--domain", "nutrition", "--target-type", "calories_kcal",
        "--value", "2400", "--unit", "kcal",
        "--effective-from", AS_OF.isoformat(),
        "--reason", "agent",
        "--source", "agent_proposed",
        "--status", "proposed",
    ])
    assert rc == 0
    with closing(open_connection(db)) as conn:
        row = conn.execute(
            "SELECT target_id FROM target WHERE user_id = ? "
            "AND status = 'proposed' ORDER BY created_at DESC LIMIT 1",
            (USER,),
        ).fetchone()
    assert row is not None
    return row[0]


def _seed_active_target(db: Path) -> str:
    rc = cli_main([
        "target", "set",
        "--db-path", str(db), "--user-id", USER,
        "--domain", "nutrition", "--target-type", "protein_g",
        "--value", "150", "--unit", "g",
        "--effective-from", AS_OF.isoformat(),
        "--reason", "user authored",
    ])
    assert rc == 0
    with closing(open_connection(db)) as conn:
        row = conn.execute(
            "SELECT target_id FROM target WHERE user_id = ? "
            "AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (USER,),
        ).fetchone()
    assert row is not None
    return row[0]


def _intent_status(db: Path, intent_id: str) -> str:
    with closing(open_connection(db)) as conn:
        row = conn.execute(
            "SELECT status FROM intent_item WHERE intent_id = ?",
            (intent_id,),
        ).fetchone()
    assert row is not None
    return row[0]


def _target_status(db: Path, target_id: str) -> str:
    with closing(open_connection(db)) as conn:
        row = conn.execute(
            "SELECT status FROM target WHERE target_id = ?",
            (target_id,),
        ).fetchone()
    assert row is not None
    return row[0]


# ---------------------------------------------------------------------------
# 1. Manifest invariant — agent_safe=False on every W57 handler.
# ---------------------------------------------------------------------------


def test_w57_handlers_are_not_agent_safe_in_manifest():
    """The capabilities manifest must declare every W57 handler
    ``agent_safe=False``. Codex 2026-04-26 caught a real regression
    where ``hai intent archive`` and ``hai target archive`` were
    ``agent_safe=True``. This test pins the corrected state.
    """

    manifest = build_manifest(build_parser())
    by_command = {row["command"]: row for row in manifest["commands"]}

    leaks: list[tuple[str, bool]] = []
    for cmd in W57_HANDLERS:
        assert cmd in by_command, f"{cmd!r} missing from manifest"
        flag = by_command[cmd]["agent_safe"]
        if flag is not False:
            leaks.append((cmd, flag))

    assert leaks == [], (
        f"W57 handlers must be agent_safe=False; found leaks: {leaks}"
    )


def test_w57_handlers_carry_confirm_flag():
    """Every W57 handler must expose ``--confirm`` so non-interactive
    callers (test harnesses, scripts the user explicitly authored)
    have a way to opt in to the mutation. Without the flag, the gate
    has no escape valve and tests cannot exercise these handlers."""

    manifest = build_manifest(build_parser())
    by_command = {row["command"]: row for row in manifest["commands"]}

    missing: list[str] = []
    for cmd in W57_HANDLERS:
        flag_names = {f["name"] for f in by_command[cmd]["flags"]}
        if "--confirm" not in flag_names:
            missing.append(cmd)
    assert missing == [], (
        f"W57 handlers missing --confirm flag: {missing}"
    )


# ---------------------------------------------------------------------------
# 2. Runtime gate — non-tty + no --confirm rejects with USER_INPUT
#    AND leaves state unchanged.
# ---------------------------------------------------------------------------


def test_intent_commit_refuses_without_confirm(tmp_path: Path):
    db = _init_db(tmp_path)
    intent_id = _seed_proposed_intent(db)
    pre = _intent_status(db, intent_id)

    rc = cli_main([
        "intent", "commit",
        "--db-path", str(db), "--user-id", USER,
        "--intent-id", intent_id,
    ])
    assert rc == 1, f"expected USER_INPUT, got {rc}"
    assert _intent_status(db, intent_id) == pre, (
        "intent_item.status changed despite gate refusal"
    )


def test_intent_archive_refuses_without_confirm(tmp_path: Path):
    """Archive of an active row IS deactivation per W57. Codex 2026-04-26."""

    db = _init_db(tmp_path)
    intent_id = _seed_active_intent(db)
    pre = _intent_status(db, intent_id)
    assert pre == "active"

    rc = cli_main([
        "intent", "archive",
        "--db-path", str(db), "--user-id", USER,
        "--intent-id", intent_id,
    ])
    assert rc == 1, f"expected USER_INPUT, got {rc}"
    assert _intent_status(db, intent_id) == "active", (
        "intent_item.status flipped despite gate refusal — W57 leak"
    )


def test_target_commit_refuses_without_confirm(tmp_path: Path):
    db = _init_db(tmp_path)
    target_id = _seed_proposed_target(db)
    pre = _target_status(db, target_id)

    rc = cli_main([
        "target", "commit",
        "--db-path", str(db), "--user-id", USER,
        "--target-id", target_id,
    ])
    assert rc == 1
    assert _target_status(db, target_id) == pre


def test_target_archive_refuses_without_confirm(tmp_path: Path):
    """Codex 2026-04-26: archive was ``agent_safe=True`` and could
    deactivate an active user-authored target with no gate. Pin the
    fix."""

    db = _init_db(tmp_path)
    target_id = _seed_active_target(db)
    assert _target_status(db, target_id) == "active"

    rc = cli_main([
        "target", "archive",
        "--db-path", str(db), "--user-id", USER,
        "--target-id", target_id,
    ])
    assert rc == 1
    assert _target_status(db, target_id) == "active", (
        "target.status flipped despite gate refusal — W57 leak"
    )


# ---------------------------------------------------------------------------
# 3. Runtime gate — --confirm permits the mutation.
# ---------------------------------------------------------------------------


def test_intent_commit_accepts_confirm_flag(tmp_path: Path):
    db = _init_db(tmp_path)
    intent_id = _seed_proposed_intent(db)

    rc = cli_main([
        "intent", "commit",
        "--db-path", str(db), "--user-id", USER,
        "--intent-id", intent_id,
        "--confirm",
    ])
    assert rc == 0
    assert _intent_status(db, intent_id) == "active"


def test_intent_archive_accepts_confirm_flag(tmp_path: Path):
    db = _init_db(tmp_path)
    intent_id = _seed_active_intent(db)

    rc = cli_main([
        "intent", "archive",
        "--db-path", str(db), "--user-id", USER,
        "--intent-id", intent_id,
        "--confirm",
    ])
    assert rc == 0
    assert _intent_status(db, intent_id) == "archived"


def test_target_commit_accepts_confirm_flag(tmp_path: Path):
    db = _init_db(tmp_path)
    target_id = _seed_proposed_target(db)

    rc = cli_main([
        "target", "commit",
        "--db-path", str(db), "--user-id", USER,
        "--target-id", target_id,
        "--confirm",
    ])
    assert rc == 0
    assert _target_status(db, target_id) == "active"


def test_target_archive_accepts_confirm_flag(tmp_path: Path):
    db = _init_db(tmp_path)
    target_id = _seed_active_target(db)

    rc = cli_main([
        "target", "archive",
        "--db-path", str(db), "--user-id", USER,
        "--target-id", target_id,
        "--confirm",
    ])
    assert rc == 0
    assert _target_status(db, target_id) == "archived"
