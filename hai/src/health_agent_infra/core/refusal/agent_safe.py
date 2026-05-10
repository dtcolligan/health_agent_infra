"""Runtime refusal for agent attempts to invoke non-agent-safe commands."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from health_agent_infra.core.refusal.envelope import (
    build_mechanism_disabled_marker,
    build_refusal_envelope,
)
from health_agent_infra.core.runtime_mode import (
    current_runtime_mode,
    mechanisms_off_for_mode,
)


HAI_INVOCATION_CONTEXT_ENV = "HAI_INVOCATION_CONTEXT"
INVOCATION_CONTEXT_AGENT = "agent"
INVOCATION_CONTEXT_USER = "user"
SUPPORTED_INVOCATION_CONTEXTS: tuple[str, ...] = (
    INVOCATION_CONTEXT_USER,
    INVOCATION_CONTEXT_AGENT,
)

_MECHANISM = "agent_safe"
_REFUSAL_KIND = "agent_safe_violation"


@dataclass(frozen=True)
class AgentSafeDecision:
    """Decision produced by the dispatch-time agent-safe guard."""

    allowed: bool
    invocation_context: str
    refusal_envelope: dict[str, object] | None = None
    mechanism_disabled_marker: dict[str, object] | None = None


class InvocationContextError(RuntimeError):
    """Raised when ``HAI_INVOCATION_CONTEXT`` is not recognised."""


class AgentSafeRefusalError(ValueError):
    """Raised when an agent-classified caller invokes an unsafe command."""

    def __init__(self, envelope: dict[str, object]) -> None:
        self.envelope = envelope
        super().__init__(str(envelope))


def current_invocation_context(env: Mapping[str, str] | None = None) -> str:
    """Return the caller context, defaulting to explicit user authority."""

    source = os.environ if env is None else env
    context = source.get(HAI_INVOCATION_CONTEXT_ENV, INVOCATION_CONTEXT_USER)
    context = context.strip().lower()
    if not context:
        context = INVOCATION_CONTEXT_USER
    if context not in SUPPORTED_INVOCATION_CONTEXTS:
        allowed = ", ".join(SUPPORTED_INVOCATION_CONTEXTS)
        raise InvocationContextError(
            f"unknown {HAI_INVOCATION_CONTEXT_ENV}={context!r}; "
            f"supported values: {allowed}"
        )
    return context


def evaluate_agent_safe_invocation(
    *,
    command: str,
    agent_safe: bool,
    env: Mapping[str, str] | None = None,
) -> AgentSafeDecision:
    """Return the dispatch decision for one command invocation."""

    context = current_invocation_context(env)
    if context != INVOCATION_CONTEXT_AGENT or agent_safe:
        return AgentSafeDecision(allowed=True, invocation_context=context)

    runtime_mode = current_runtime_mode(env)
    details = {
        "command": command,
        "agent_safe": agent_safe,
        "invocation_context": context,
    }
    if _MECHANISM in mechanisms_off_for_mode(runtime_mode):
        return AgentSafeDecision(
            allowed=True,
            invocation_context=context,
            mechanism_disabled_marker=build_mechanism_disabled_marker(
                mechanism=_MECHANISM,
                runtime_mode=runtime_mode,
                output_path=command,
                reason="agent_safe dispatch refusal disabled by runtime mode",
                details=details,
            ),
        )

    envelope = build_refusal_envelope(
        refusal_kind=_REFUSAL_KIND,
        mechanism=_MECHANISM,
        code="agent_invoked_unsafe_command",
        message=(
            "runtime refused agent-classified caller invoking an "
            "agent_safe=false command"
        ),
        output_path=command,
        details=details,
    )
    return AgentSafeDecision(
        allowed=False,
        invocation_context=context,
        refusal_envelope=envelope,
    )


def enforce_agent_safe_invocation(
    *,
    command: str,
    agent_safe: bool,
    env: Mapping[str, str] | None = None,
) -> AgentSafeDecision:
    """Raise ``AgentSafeRefusalError`` unless dispatch may proceed."""

    decision = evaluate_agent_safe_invocation(
        command=command,
        agent_safe=agent_safe,
        env=env,
    )
    if not decision.allowed:
        assert decision.refusal_envelope is not None
        raise AgentSafeRefusalError(decision.refusal_envelope)
    return decision


__all__ = [
    "HAI_INVOCATION_CONTEXT_ENV",
    "INVOCATION_CONTEXT_AGENT",
    "INVOCATION_CONTEXT_USER",
    "SUPPORTED_INVOCATION_CONTEXTS",
    "AgentSafeDecision",
    "AgentSafeRefusalError",
    "InvocationContextError",
    "current_invocation_context",
    "enforce_agent_safe_invocation",
    "evaluate_agent_safe_invocation",
]
