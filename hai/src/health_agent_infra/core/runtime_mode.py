"""Runtime-mode selection for benchmark scaffold ablations.

This module owns only mode resolution and the safety guard. Individual
mechanism off-paths are added by WP-RT-MODE-002.
"""

from __future__ import annotations

import os
from typing import Mapping

from health_agent_infra.core.hermetic import (
    HAI_HERMETIC_ENV,
    is_hermetic,
    require_hermetic_recipe,
)


HAI_RUNTIME_MODE_ENV = "HAI_RUNTIME_MODE"

FULL_CONTRACT = "full_contract"
NO_VALIDATION = "no_validation"
NO_AGENT_SAFE = "no_agent_safe"
NO_PROPOSAL_GATE = "no_proposal_gate"
NO_REFUSAL = "no_refusal"
NO_AUDIT_CHAIN = "no_audit_chain"
NO_RUNTIME_ENFORCEMENT = "no_runtime_enforcement"

SUPPORTED_RUNTIME_MODES: tuple[str, ...] = (
    FULL_CONTRACT,
    NO_VALIDATION,
    NO_AGENT_SAFE,
    NO_PROPOSAL_GATE,
    NO_REFUSAL,
    NO_AUDIT_CHAIN,
    NO_RUNTIME_ENFORCEMENT,
)

MECHANISMS_OFF_BY_MODE: dict[str, tuple[str, ...]] = {
    FULL_CONTRACT: (),
    NO_VALIDATION: ("validation",),
    NO_AGENT_SAFE: ("agent_safe",),
    NO_PROPOSAL_GATE: ("proposal_gate",),
    NO_REFUSAL: ("refusal",),
    NO_AUDIT_CHAIN: ("audit_chain",),
    NO_RUNTIME_ENFORCEMENT: (
        "validation",
        "agent_safe",
        "proposal_gate",
        "refusal",
        "audit_chain",
    ),
}


class RuntimeModeError(RuntimeError):
    """Raised when ``HAI_RUNTIME_MODE`` is unknown or unsafe."""


def current_runtime_mode(env: Mapping[str, str] | None = None) -> str:
    """Return the selected runtime mode, defaulting to ``full_contract``."""

    source = os.environ if env is None else env
    mode = source.get(HAI_RUNTIME_MODE_ENV, FULL_CONTRACT).strip()
    if not mode:
        mode = FULL_CONTRACT
    if mode not in SUPPORTED_RUNTIME_MODES:
        allowed = ", ".join(SUPPORTED_RUNTIME_MODES)
        raise RuntimeModeError(
            f"unknown {HAI_RUNTIME_MODE_ENV}={mode!r}; supported values: {allowed}"
        )
    return mode


def mechanisms_off_for_mode(mode: str) -> tuple[str, ...]:
    """Return the mechanisms disabled by a supported runtime mode."""

    if mode not in MECHANISMS_OFF_BY_MODE:
        allowed = ", ".join(SUPPORTED_RUNTIME_MODES)
        raise RuntimeModeError(
            f"unknown runtime mode {mode!r}; supported values: {allowed}"
        )
    return MECHANISMS_OFF_BY_MODE[mode]


def mechanism_is_disabled(
    mechanism: str,
    env: Mapping[str, str] | None = None,
) -> bool:
    """Return whether ``mechanism`` is disabled by the current mode."""

    return mechanism in mechanisms_off_for_mode(current_runtime_mode(env))


def require_runtime_mode_allowed(env: Mapping[str, str] | None = None) -> None:
    """Reject mechanism-disabling modes outside hermetic fixture state."""

    source = os.environ if env is None else env
    mode = current_runtime_mode(source)
    if mode == FULL_CONTRACT:
        return

    if not is_hermetic(source):
        raise RuntimeModeError(
            f"{HAI_RUNTIME_MODE_ENV}={mode!r} disables runtime enforcement and "
            f"requires {HAI_HERMETIC_ENV}=1 plus redirected fixture state."
        )
    require_hermetic_recipe(source)


__all__ = [
    "FULL_CONTRACT",
    "HAI_RUNTIME_MODE_ENV",
    "MECHANISMS_OFF_BY_MODE",
    "NO_AGENT_SAFE",
    "NO_AUDIT_CHAIN",
    "NO_PROPOSAL_GATE",
    "NO_REFUSAL",
    "NO_RUNTIME_ENFORCEMENT",
    "NO_VALIDATION",
    "RuntimeModeError",
    "SUPPORTED_RUNTIME_MODES",
    "current_runtime_mode",
    "mechanism_is_disabled",
    "mechanisms_off_for_mode",
    "require_runtime_mode_allowed",
]
