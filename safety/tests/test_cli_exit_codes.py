"""Pin the CLI exit-code taxonomy for every migrated handler.

Covers the five codes defined in
``src/health_agent_infra/core/exit_codes.py`` and the handlers migrated
in M1: ``hai pull``, ``hai auth garmin``, ``hai auth status``,
``hai synthesize``, ``hai explain``. Every non-migrated handler is
intentionally absent — their rc contract remains the pre-M1 mix until
a follow-up PR migrates them.

Tests here assert *only* on return codes. They are paired with the
domain-specific suites (``test_cli_explain.py``, ``test_cli_synthesize.py``,
``test_cli_pull_live_and_auth.py``) which continue to assert on
stdout / stderr payloads.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from health_agent_infra import cli as cli_mod
from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.pull.auth import CredentialStore
from health_agent_infra.core.pull.garmin_live import GarminLiveError


# ---------------------------------------------------------------------------
# Constants contract
# ---------------------------------------------------------------------------


def test_exit_code_values_are_stable():
    """Numeric values are a public contract — any change breaks callers."""

    assert exit_codes.OK == 0
    assert exit_codes.USER_INPUT == 1
    assert exit_codes.TRANSIENT == 2
    assert exit_codes.NOT_FOUND == 3
    assert exit_codes.INTERNAL == 4


def test_exit_code_values_are_unique():
    values = [
        exit_codes.OK,
        exit_codes.USER_INPUT,
        exit_codes.TRANSIENT,
        exit_codes.NOT_FOUND,
        exit_codes.INTERNAL,
    ]
    assert len(values) == len(set(values))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeKeyring:
    def __init__(self):
        self._data: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):
        return self._data.get((service, username))

    def set_password(self, service, username, password):
        self._data[(service, username)] = password

    def delete_password(self, service, username):
        self._data.pop((service, username), None)


def _fake_store(env=None) -> CredentialStore:
    return CredentialStore(backend=_FakeKeyring(), env=env or {})


def _init_state_db(tmp_path: Path) -> Path:
    """Invoke ``hai state init`` via ``cli_main`` to stand up a fresh DB."""

    db_path = tmp_path / "state.db"
    rc = cli_main(["state", "init", "--db-path", str(db_path)])
    assert rc == exit_codes.OK
    return db_path


# ---------------------------------------------------------------------------
# hai explain
# ---------------------------------------------------------------------------


def test_explain_conflicting_selectors_returns_user_input(tmp_path, capsys):
    db_path = _init_state_db(tmp_path)
    capsys.readouterr()  # discard state-init stdout

    rc = cli_main([
        "explain",
        "--daily-plan-id", "plan_whatever",
        "--for-date", "2026-04-17",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
    ])
    assert rc == exit_codes.USER_INPUT


def test_explain_no_selectors_returns_user_input(tmp_path, capsys):
    db_path = _init_state_db(tmp_path)
    capsys.readouterr()

    rc = cli_main(["explain", "--db-path", str(db_path)])
    assert rc == exit_codes.USER_INPUT


def test_explain_missing_db_returns_user_input(tmp_path, capsys):
    missing = tmp_path / "does_not_exist.db"
    rc = cli_main([
        "explain",
        "--daily-plan-id", "plan_whatever",
        "--db-path", str(missing),
    ])
    assert rc == exit_codes.USER_INPUT


def test_explain_unknown_plan_id_returns_not_found(tmp_path, capsys):
    db_path = _init_state_db(tmp_path)
    capsys.readouterr()

    rc = cli_main([
        "explain",
        "--daily-plan-id", "plan_2099-01-01_ghost",
        "--db-path", str(db_path),
    ])
    assert rc == exit_codes.NOT_FOUND


# ---------------------------------------------------------------------------
# hai synthesize
# ---------------------------------------------------------------------------


def test_synthesize_missing_db_returns_user_input(tmp_path, capsys):
    missing = tmp_path / "nope.db"
    rc = cli_main([
        "synthesize",
        "--as-of", "2026-04-17",
        "--user-id", "u_local_1",
        "--db-path", str(missing),
    ])
    assert rc == exit_codes.USER_INPUT


def test_synthesize_bundle_only_and_drafts_conflict_returns_user_input(
    tmp_path, capsys,
):
    db_path = _init_state_db(tmp_path)
    capsys.readouterr()
    drafts = tmp_path / "drafts.json"
    drafts.write_text("[]", encoding="utf-8")

    rc = cli_main([
        "synthesize",
        "--as-of", "2026-04-17",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
        "--bundle-only",
        "--drafts-json", str(drafts),
    ])
    assert rc == exit_codes.USER_INPUT


def test_synthesize_unreadable_drafts_returns_user_input(tmp_path, capsys):
    db_path = _init_state_db(tmp_path)
    capsys.readouterr()
    missing_drafts = tmp_path / "not_there.json"

    rc = cli_main([
        "synthesize",
        "--as-of", "2026-04-17",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
        "--drafts-json", str(missing_drafts),
    ])
    assert rc == exit_codes.USER_INPUT


def test_synthesize_non_array_drafts_returns_user_input(tmp_path, capsys):
    db_path = _init_state_db(tmp_path)
    capsys.readouterr()
    drafts = tmp_path / "bad_drafts.json"
    drafts.write_text('{"not": "an array"}', encoding="utf-8")

    rc = cli_main([
        "synthesize",
        "--as-of", "2026-04-17",
        "--user-id", "u_local_1",
        "--db-path", str(db_path),
        "--drafts-json", str(drafts),
    ])
    assert rc == exit_codes.USER_INPUT


# ---------------------------------------------------------------------------
# hai pull --live
# ---------------------------------------------------------------------------


def test_pull_live_missing_credentials_returns_user_input(monkeypatch):
    store = _fake_store()
    monkeypatch.setattr(
        cli_mod.CredentialStore,
        "default",
        classmethod(lambda cls: store),
    )

    rc = cli_main(["pull", "--live", "--date", "2026-04-17"])
    assert rc == exit_codes.USER_INPUT


def test_pull_live_adapter_error_returns_transient(monkeypatch):
    store = _fake_store()
    store.store_garmin("alice@example.com", "s3cret")
    monkeypatch.setattr(
        cli_mod.CredentialStore,
        "default",
        classmethod(lambda cls: store),
    )

    class _ExplodingAdapter:
        source_name = "garmin_live"

        def load(self, as_of):
            raise GarminLiveError("vendor 503 — try again later")

    monkeypatch.setattr(
        cli_mod, "_build_live_adapter", lambda args: _ExplodingAdapter(),
    )

    rc = cli_main(["pull", "--live", "--date", "2026-04-17"])
    assert rc == exit_codes.TRANSIENT


# ---------------------------------------------------------------------------
# hai auth garmin
# ---------------------------------------------------------------------------


def test_auth_garmin_missing_env_var_returns_user_input(monkeypatch):
    store = _fake_store()
    monkeypatch.setattr(
        cli_mod.CredentialStore,
        "default",
        classmethod(lambda cls: store),
    )
    monkeypatch.delenv("HAI_EXIT_CODE_TEST_PW", raising=False)

    rc = cli_main([
        "auth", "garmin",
        "--email", "alice@example.com",
        "--password-env", "HAI_EXIT_CODE_TEST_PW",
    ])
    assert rc == exit_codes.USER_INPUT


def test_auth_garmin_empty_stdin_password_returns_user_input(monkeypatch):
    store = _fake_store()
    monkeypatch.setattr(
        cli_mod.CredentialStore,
        "default",
        classmethod(lambda cls: store),
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n"))

    rc = cli_main([
        "auth", "garmin",
        "--email", "alice@example.com",
        "--password-stdin",
    ])
    assert rc == exit_codes.USER_INPUT
