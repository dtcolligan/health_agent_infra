"""Regression test for the v0.1.6 W7 fix: ``--base-dir`` is now
optional on every ``hai intake *``, ``hai propose``, ``hai review *``,
``hai daily``, and ``hai state reproject`` subcommand. Resolution
order: explicit > ``$HAI_BASE_DIR`` env var > ``~/.health_agent``.

Background: the 2026-04-25 user session hit "every intake command
requires --base-dir" friction — fresh users had no way to know the
canonical location. The fix mirrors ``resolve_db_path`` in
``core/state/store.py``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from health_agent_infra.core.paths import (
    DEFAULT_BASE_DIR,
    resolve_base_dir,
)


def test_default_is_home_health_agent():
    assert DEFAULT_BASE_DIR == Path.home() / ".health_agent"


def test_explicit_arg_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("HAI_BASE_DIR", "/should/be/ignored")
    assert resolve_base_dir(str(tmp_path)) == tmp_path


def test_env_var_used_when_no_explicit(tmp_path, monkeypatch):
    monkeypatch.setenv("HAI_BASE_DIR", str(tmp_path))
    assert resolve_base_dir(None) == tmp_path


def test_default_used_when_neither_provided(monkeypatch):
    monkeypatch.delenv("HAI_BASE_DIR", raising=False)
    assert resolve_base_dir(None) == DEFAULT_BASE_DIR


def test_explicit_path_object_works(tmp_path):
    assert resolve_base_dir(tmp_path) == tmp_path


def test_tilde_expansion(monkeypatch):
    monkeypatch.delenv("HAI_BASE_DIR", raising=False)
    result = resolve_base_dir("~/somedir")
    assert str(result).startswith(str(Path.home()))


# ---------------------------------------------------------------------------
# CLI integration: each subcommand can run without --base-dir
# ---------------------------------------------------------------------------

def test_cli_intake_stress_works_without_base_dir_flag(tmp_path, monkeypatch):
    """Smoke test: hai intake stress --score 3 (no --base-dir) writes
    to $HAI_BASE_DIR via the new resolver."""

    from health_agent_infra.cli import main as cli_main

    monkeypatch.setenv("HAI_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("HAI_STATE_DB", str(tmp_path / "state.db"))

    rc = cli_main([
        "intake", "stress",
        "--score", "3",
        "--as-of", "2026-04-25",
        "--user-id", "u_test",
    ])
    assert rc == 0
    # Audit log landed at the resolved base-dir.
    assert (tmp_path / "stress_manual.jsonl").exists()


def test_cli_intake_note_works_without_base_dir_flag(tmp_path, monkeypatch):
    from health_agent_infra.cli import main as cli_main

    monkeypatch.setenv("HAI_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("HAI_STATE_DB", str(tmp_path / "state.db"))

    rc = cli_main([
        "intake", "note",
        "--text", "test note from default base-dir",
        "--as-of", "2026-04-25",
        "--user-id", "u_test",
    ])
    assert rc == 0
    assert (tmp_path / "context_notes.jsonl").exists()
