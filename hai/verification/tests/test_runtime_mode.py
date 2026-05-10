"""WP-RT-MODE-001: runtime-mode accessor contract."""

from __future__ import annotations

import pytest

from health_agent_infra.core.runtime_mode import (
    FULL_CONTRACT,
    HAI_RUNTIME_MODE_ENV,
    MECHANISMS_OFF_BY_MODE,
    NO_AGENT_SAFE,
    RuntimeModeError,
    SUPPORTED_RUNTIME_MODES,
    current_runtime_mode,
    mechanisms_off_for_mode,
)


def test_runtime_mode_defaults_to_full_contract() -> None:
    assert current_runtime_mode({}) == FULL_CONTRACT


@pytest.mark.parametrize("mode", SUPPORTED_RUNTIME_MODES)
def test_every_supported_runtime_mode_resolves(mode: str) -> None:
    assert current_runtime_mode({HAI_RUNTIME_MODE_ENV: mode}) == mode


def test_empty_runtime_mode_resolves_to_full_contract() -> None:
    assert current_runtime_mode({HAI_RUNTIME_MODE_ENV: "   "}) == FULL_CONTRACT


def test_unknown_runtime_mode_rejected() -> None:
    with pytest.raises(RuntimeModeError) as excinfo:
        current_runtime_mode({HAI_RUNTIME_MODE_ENV: "no_runtime"})

    msg = str(excinfo.value)
    assert HAI_RUNTIME_MODE_ENV in msg
    assert "no_runtime" in msg
    assert "no_runtime_enforcement" in msg


def test_mechanisms_off_mapping_covers_supported_modes() -> None:
    assert set(MECHANISMS_OFF_BY_MODE) == set(SUPPORTED_RUNTIME_MODES)
    assert mechanisms_off_for_mode(FULL_CONTRACT) == ()
    assert mechanisms_off_for_mode(NO_AGENT_SAFE) == ("agent_safe",)
