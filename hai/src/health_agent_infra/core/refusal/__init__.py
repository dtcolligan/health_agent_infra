"""Code-owned refusal contracts for runtime-governed outputs."""

from health_agent_infra.core.refusal.clinical import (
    BANNED_CLINICAL_PHRASES,
    ClinicalOutputDecision,
    ClinicalPhraseMatch,
    ClinicalRefusalError,
    enforce_clinical_output,
    evaluate_clinical_output,
    scan_clinical_phrases,
)
from health_agent_infra.core.refusal.agent_safe import (
    AGENT_CLASSIFIED_INVOCATION_CONTEXTS,
    HAI_INVOCATION_CONTEXT_ENV,
    INVOCATION_CONTEXT_AGENT,
    INVOCATION_CONTEXT_RULE_BASELINE,
    INVOCATION_CONTEXT_USER,
    SUPPORTED_INVOCATION_CONTEXTS,
    AgentSafeDecision,
    AgentSafeRefusalError,
    InvocationContextError,
    current_invocation_context,
    enforce_agent_safe_invocation,
    evaluate_agent_safe_invocation,
)
from health_agent_infra.core.refusal.envelope import (
    MECHANISM_DISABLED_MARKER_SCHEMA_VERSION,
    REFUSAL_ENVELOPE_SCHEMA_VERSION,
    build_mechanism_disabled_marker,
    build_refusal_envelope,
    envelope_to_json,
)

__all__ = [
    "BANNED_CLINICAL_PHRASES",
    "AGENT_CLASSIFIED_INVOCATION_CONTEXTS",
    "HAI_INVOCATION_CONTEXT_ENV",
    "INVOCATION_CONTEXT_AGENT",
    "INVOCATION_CONTEXT_RULE_BASELINE",
    "INVOCATION_CONTEXT_USER",
    "SUPPORTED_INVOCATION_CONTEXTS",
    "AgentSafeDecision",
    "AgentSafeRefusalError",
    "ClinicalOutputDecision",
    "ClinicalPhraseMatch",
    "ClinicalRefusalError",
    "InvocationContextError",
    "MECHANISM_DISABLED_MARKER_SCHEMA_VERSION",
    "REFUSAL_ENVELOPE_SCHEMA_VERSION",
    "build_mechanism_disabled_marker",
    "build_refusal_envelope",
    "current_invocation_context",
    "enforce_agent_safe_invocation",
    "enforce_clinical_output",
    "envelope_to_json",
    "evaluate_agent_safe_invocation",
    "evaluate_clinical_output",
    "scan_clinical_phrases",
]
