"""WP-RUNTIME-FIX-002 — the activation side door.

W57 reserves intent/target activation for an explicit user commit. `intent
commit` / `target commit` are gated by ``_w57_user_gate``, but an agent could
otherwise reach ``active`` through a side door: ``intent training add-session
--status active`` / ``target set --status active`` with the DEFAULT
``source='user_authored'`` is accepted by the store (it only rejects
``source='agent_proposed'`` + active), and those insert commands are
``agent_safe=True`` so the dispatch gate lets them through.

These tests pin the completeness fix: an agent-classified caller may not create
an active user-state row directly. Refuse under ``agent_safe`` in
``full_contract``; permit (with a mechanism_disabled marker) when the mechanism
is ablated; and never touch the ``user``-context path (a user authoring an
active row directly is legitimate).
"""

from __future__ import annotations

from contextlib import closing
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import initialize_database, open_connection


AS_OF = date(2026, 4, 26)
USER = "u_side_door"


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _hermetic(monkeypatch, tmp_path: Path, *, context: str, mode: str) -> None:
    # Redirect ALL state surfaces so the hermetic recipe check passes and the
    # only thing that can refuse is the gate under test (not a missing
    # HAI_STATE_DB), which would be a false pass.
    monkeypatch.setenv("HAI_HERMETIC", "1")
    monkeypatch.setenv("HAI_STATE_DB", str(tmp_path / "state.db"))
    monkeypatch.setenv("HAI_BASE_DIR", str(tmp_path / "base"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    monkeypatch.setenv("HAI_INVOCATION_CONTEXT", context)
    monkeypatch.setenv("HAI_RUNTIME_MODE", mode)


def _add_active_intent(db: Path) -> int:
    return cli_main([
        "intent", "training", "add-session",
        "--db-path", str(db), "--user-id", USER,
        "--scope-start", AS_OF.isoformat(),
        "--reason", "x", "--status", "active",
    ])


def _add_active_target(db: Path) -> int:
    return cli_main([
        "target", "set",
        "--db-path", str(db), "--user-id", USER,
        "--domain", "nutrition", "--target-type", "protein_g",
        "--value", "150", "--unit", "g",
        "--effective-from", AS_OF.isoformat(),
        "--reason", "x", "--status", "active",
    ])


def _count(db: Path, table: str, status: str) -> int:
    with closing(open_connection(db)) as conn:
        return conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE user_id = ? AND status = ?",
            (USER, status),
        ).fetchone()[0]


# --- full_contract: the side door is closed for an agent ----------------------

def test_agent_active_intent_refused_full_contract(tmp_path, monkeypatch):
    db = _init_db(tmp_path)
    _hermetic(monkeypatch, tmp_path, context="agent", mode="full_contract")
    rc = _add_active_intent(db)
    assert rc == exit_codes.USER_INPUT
    assert _count(db, "intent_item", "active") == 0


def test_agent_active_target_refused_full_contract(tmp_path, monkeypatch):
    db = _init_db(tmp_path)
    _hermetic(monkeypatch, tmp_path, context="agent", mode="full_contract")
    rc = _add_active_target(db)
    assert rc == exit_codes.USER_INPUT
    assert _count(db, "target", "active") == 0


def test_rule_baseline_context_also_refused(tmp_path, monkeypatch):
    db = _init_db(tmp_path)
    _hermetic(monkeypatch, tmp_path, context="rule_baseline", mode="full_contract")
    assert _add_active_intent(db) == exit_codes.USER_INPUT
    assert _count(db, "intent_item", "active") == 0


# --- ablation: the off cell must be able to execute the violation -------------

def test_agent_active_intent_executes_when_agent_safe_ablated(tmp_path, monkeypatch):
    db = _init_db(tmp_path)
    _hermetic(monkeypatch, tmp_path, context="agent", mode="no_runtime_enforcement")
    rc = _add_active_intent(db)
    assert rc == exit_codes.OK
    assert _count(db, "intent_item", "active") == 1


# --- user context: authoring an active row directly stays legitimate ----------

def test_user_active_intent_still_allowed(tmp_path, monkeypatch):
    db = _init_db(tmp_path)
    _hermetic(monkeypatch, tmp_path, context="user", mode="full_contract")
    rc = _add_active_intent(db)
    assert rc == exit_codes.OK
    assert _count(db, "intent_item", "active") == 1


# --- a legitimate agent PROPOSAL is unaffected --------------------------------

def test_agent_proposed_insert_unaffected(tmp_path, monkeypatch):
    db = _init_db(tmp_path)
    _hermetic(monkeypatch, tmp_path, context="agent", mode="full_contract")
    rc = cli_main([
        "intent", "training", "add-session",
        "--db-path", str(db), "--user-id", USER,
        "--scope-start", AS_OF.isoformat(),
        "--reason", "x", "--status", "proposed", "--source", "agent_proposed",
    ])
    assert rc == exit_codes.OK
    assert _count(db, "intent_item", "proposed") == 1
