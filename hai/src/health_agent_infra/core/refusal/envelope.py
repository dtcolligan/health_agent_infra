"""Stable refusal-envelope helpers shared by runtime refusal seams."""

from __future__ import annotations

import json
from typing import Any


REFUSAL_ENVELOPE_SCHEMA_VERSION = "refusal_envelope.v1"
MECHANISM_DISABLED_MARKER_SCHEMA_VERSION = "mechanism_disabled_marker.v1"


def build_refusal_envelope(
    *,
    refusal_kind: str,
    mechanism: str,
    code: str,
    message: str,
    output_path: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the stable refusal payload emitted at runtime boundaries."""

    return {
        "schema_version": REFUSAL_ENVELOPE_SCHEMA_VERSION,
        "step_type": "refusal",
        "refusal_kind": refusal_kind,
        "mechanism": mechanism,
        "code": code,
        "message": message,
        "output_path": output_path,
        "details": details or {},
    }


def build_mechanism_disabled_marker(
    *,
    mechanism: str,
    runtime_mode: str,
    output_path: str,
    reason: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a stable marker for benchmark runs that bypass a mechanism."""

    return {
        "schema_version": MECHANISM_DISABLED_MARKER_SCHEMA_VERSION,
        "step_type": "mechanism_disabled",
        "mechanism": mechanism,
        "runtime_mode": runtime_mode,
        "output_path": output_path,
        "reason": reason,
        "details": details or {},
    }


def envelope_to_json(envelope: dict[str, Any]) -> str:
    """Serialize refusal envelopes and disabled markers deterministically."""

    return json.dumps(envelope, sort_keys=True)


__all__ = [
    "MECHANISM_DISABLED_MARKER_SCHEMA_VERSION",
    "REFUSAL_ENVELOPE_SCHEMA_VERSION",
    "build_mechanism_disabled_marker",
    "build_refusal_envelope",
    "envelope_to_json",
]
