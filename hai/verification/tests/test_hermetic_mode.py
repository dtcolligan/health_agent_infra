"""WP-HRN-001: hermetic benchmark-mode guardrails."""

from __future__ import annotations

import json

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.hermetic import (
    HAI_BASE_DIR_ENV,
    HAI_HERMETIC_ENV,
    HAI_STATE_DB_ENV,
    HermeticModeError,
    require_hermetic_recipe,
)
from health_agent_infra.core.pull.auth import CredentialStore


class _RecordingKeyring:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def get_password(self, service: str, username: str) -> str | None:
        self.calls.append(("get", service, username))
        return None

    def set_password(self, service: str, username: str, password: str) -> None:
        self.calls.append(("set", service, username))

    def delete_password(self, service: str, username: str) -> None:
        self.calls.append(("delete", service, username))


def test_recipe_requires_state_and_base_redirection() -> None:
    env = {HAI_HERMETIC_ENV: "1"}

    with pytest.raises(HermeticModeError) as excinfo:
        require_hermetic_recipe(env)

    msg = str(excinfo.value)
    assert "hermetic mode" in msg
    assert HAI_STATE_DB_ENV in msg
    assert HAI_BASE_DIR_ENV in msg


def test_cli_refuses_hermetic_without_redirection(monkeypatch, capsys) -> None:
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.delenv(HAI_STATE_DB_ENV, raising=False)
    monkeypatch.delenv(HAI_BASE_DIR_ENV, raising=False)

    rc = cli_main(["capabilities", "--json"])

    err = capsys.readouterr().err
    assert rc == exit_codes.USER_INPUT
    assert "hermetic mode" in err
    assert HAI_STATE_DB_ENV in err
    assert HAI_BASE_DIR_ENV in err


def test_read_only_capabilities_succeeds_with_hermetic_recipe(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.setenv(HAI_STATE_DB_ENV, str(tmp_path / "state.db"))
    monkeypatch.setenv(HAI_BASE_DIR_ENV, str(tmp_path / "base"))

    rc = cli_main(["capabilities", "--json"])

    out = capsys.readouterr().out
    assert rc == exit_codes.OK
    payload = json.loads(out)
    assert payload["schema_version"].startswith("agent_cli_contract.")


def test_credential_store_refuses_keyring_before_backend_access() -> None:
    keyring = _RecordingKeyring()
    store = CredentialStore(
        backend=keyring,
        env={HAI_HERMETIC_ENV: "1"},
    )

    with pytest.raises(HermeticModeError) as excinfo:
        store.load_intervals_icu()

    assert "hermetic mode refuses OS keyring access" in str(excinfo.value)
    assert keyring.calls == []


def test_live_pull_refuses_before_state_mutation(monkeypatch, tmp_path, capsys) -> None:
    db_path = tmp_path / "fixture.db"
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.setenv(HAI_STATE_DB_ENV, str(db_path))
    monkeypatch.setenv(HAI_BASE_DIR_ENV, str(tmp_path / "base"))

    rc = cli_main([
        "pull",
        "--source",
        "intervals_icu",
        "--date",
        "2026-05-10",
    ])

    err = capsys.readouterr().err
    assert rc == exit_codes.USER_INPUT
    assert "hermetic mode refuses network access" in err
    assert "intervals_icu" in err
    assert not db_path.exists()
