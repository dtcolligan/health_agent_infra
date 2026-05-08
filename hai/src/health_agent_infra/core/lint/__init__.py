"""Regulated-claim lint surfaces (W-LINT, v0.1.13).

Public API re-exports the terms callers need most:

    >>> from health_agent_infra.core.lint import (
    ...     REGULATED_TERMS,
    ...     RegulatedClaimError,
    ...     RegulatedClaimViolation,
    ...     runtime_check,
    ...     scan_skill_text,
    ... )
"""

from health_agent_infra.core.lint.regulated_claims import (
    ALLOWLISTED_SKILLS,
    META_DOCUMENT_ALLOWLIST,
    META_DOCUMENT_PRAGMA,
    REGULATED_TERMS,
    RegulatedClaimError,
    RegulatedClaimViolation,
    runtime_check,
    scan_skill_text,
)

__all__ = [
    "ALLOWLISTED_SKILLS",
    "META_DOCUMENT_ALLOWLIST",
    "META_DOCUMENT_PRAGMA",
    "REGULATED_TERMS",
    "RegulatedClaimError",
    "RegulatedClaimViolation",
    "runtime_check",
    "scan_skill_text",
]
