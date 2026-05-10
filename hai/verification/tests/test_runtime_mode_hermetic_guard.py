"""WP-RT-MODE-001: non-full runtime modes are hermetic-only."""

from __future__ import annotations

import json

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.hermetic import (
    HAI_BASE_DIR_ENV,
    HAI_HERMETIC_ENV,
    HAI_STATE_DB_ENV,
)
from health_agent_infra.core.runtime_mode import (
    HAI_RUNTIME_MODE_ENV,
    FULL_CONTRACT,
    SUPPORTED_RUNTIME_MODES,
)


MECHANISM_DISABLING_MODES = tuple(
    mode for mode in SUPPORTED_RUNTIME_MODES if mode != FULL_CONTRACT
)


@pytest.mark.parametrize("mode", MECHANISM_DISABLING_MODES)
def test_non_full_mode_requires_hermetic(monkeypatch, capsys, mode: str) -> None:
    monkeypatch.setenv(HAI_RUNTIME_MODE_ENV, mode)
    monkeypatch.delenv(HAI_HERMETIC_ENV, raising=False)
    monkeypatch.delenv(HAI_STATE_DB_ENV, raising=False)
    monkeypatch.delenv(HAI_BASE_DIR_ENV, raising=False)

    rc = cli_main(["capabilities", "--json"])

    err = capsys.readouterr().err
    assert rc == exit_codes.USER_INPUT
    assert HAI_RUNTIME_MODE_ENV in err
    assert mode in err
    assert f"{HAI_HERMETIC_ENV}=1" in err


def test_non_full_mode_requires_state_redirection(monkeypatch, capsys) -> None:
    monkeypatch.setenv(HAI_RUNTIME_MODE_ENV, "no_agent_safe")
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.delenv(HAI_STATE_DB_ENV, raising=False)
    monkeypatch.delenv(HAI_BASE_DIR_ENV, raising=False)

    rc = cli_main(["capabilities", "--json"])

    err = capsys.readouterr().err
    assert rc == exit_codes.USER_INPUT
    assert "hermetic mode" in err
    assert HAI_STATE_DB_ENV in err
    assert HAI_BASE_DIR_ENV in err


@pytest.mark.parametrize("mode", SUPPORTED_RUNTIME_MODES)
def test_all_modes_allowed_with_hermetic_recipe(
    monkeypatch,
    tmp_path,
    capsys,
    mode: str,
) -> None:
    monkeypatch.setenv(HAI_RUNTIME_MODE_ENV, mode)
    monkeypatch.setenv(HAI_HERMETIC_ENV, "1")
    monkeypatch.setenv(HAI_STATE_DB_ENV, str(tmp_path / f"{mode}.db"))
    monkeypatch.setenv(HAI_BASE_DIR_ENV, str(tmp_path / f"{mode}_base"))

    rc = cli_main(["capabilities", "--json"])

    out = capsys.readouterr().out
    assert rc == exit_codes.OK
    assert json.loads(out)["schema_version"].startswith("agent_cli_contract.")
