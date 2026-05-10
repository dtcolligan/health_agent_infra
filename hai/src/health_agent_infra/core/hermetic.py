"""Hermetic benchmark-mode guardrails.

``HAI_HERMETIC=1`` is the all-or-nothing mode used by
GovernedAgentBench. It allows local fixture state but refuses hidden
dependencies on the user's default state, OS keyring, or network.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from health_agent_infra.core.paths import DEFAULT_BASE_DIR
from health_agent_infra.core.state.store import DEFAULT_DB_PATH


HAI_HERMETIC_ENV = "HAI_HERMETIC"
HAI_STATE_DB_ENV = "HAI_STATE_DB"
HAI_BASE_DIR_ENV = "HAI_BASE_DIR"

_TRUTHY = frozenset({"1", "true", "yes", "on"})


class HermeticModeError(RuntimeError):
    """Raised when hermetic mode would touch a forbidden surface."""


def is_hermetic(env: Mapping[str, str] | None = None) -> bool:
    """Return True when ``HAI_HERMETIC`` is set to a truthy value."""

    source = os.environ if env is None else env
    return source.get(HAI_HERMETIC_ENV, "").strip().lower() in _TRUTHY


def require_hermetic_recipe(env: Mapping[str, str] | None = None) -> None:
    """Validate the all-or-nothing hermetic env recipe.

    Hermetic mode without both state redirections is refused before any
    CLI handler runs. This prevents benchmark/runtime-mode experiments
    from accidentally operating on the maintainer's default state tree.
    """

    source = os.environ if env is None else env
    if not is_hermetic(source):
        return

    missing: list[str] = []
    state_db = source.get(HAI_STATE_DB_ENV)
    base_dir = source.get(HAI_BASE_DIR_ENV)
    if not state_db:
        missing.append(HAI_STATE_DB_ENV)
    elif _expanded_path(state_db) == DEFAULT_DB_PATH.expanduser():
        missing.append(f"{HAI_STATE_DB_ENV}=<non-default path>")
    if not base_dir:
        missing.append(HAI_BASE_DIR_ENV)
    elif _expanded_path(base_dir) == DEFAULT_BASE_DIR.expanduser():
        missing.append(f"{HAI_BASE_DIR_ENV}=<non-default path>")

    if missing:
        joined = ", ".join(missing)
        raise HermeticModeError(
            "hermetic mode requires all state surfaces to be redirected: "
            f"set {joined}. HAI_HERMETIC=1 may not use default local state."
        )


def refuse_keyring_access(
    operation: str,
    env: Mapping[str, str] | None = None,
) -> None:
    """Refuse keyring reads/writes under hermetic mode."""

    if is_hermetic(env):
        raise HermeticModeError(
            f"hermetic mode refuses OS keyring access during {operation}"
        )


def refuse_network_access(operation: str) -> None:
    """Refuse network calls under hermetic mode."""

    if is_hermetic():
        raise HermeticModeError(
            f"hermetic mode refuses network access during {operation}"
        )


def _expanded_path(value: str) -> Path:
    return Path(value).expanduser()


__all__ = [
    "HAI_BASE_DIR_ENV",
    "HAI_HERMETIC_ENV",
    "HAI_STATE_DB_ENV",
    "HermeticModeError",
    "is_hermetic",
    "refuse_keyring_access",
    "refuse_network_access",
    "require_hermetic_recipe",
]
