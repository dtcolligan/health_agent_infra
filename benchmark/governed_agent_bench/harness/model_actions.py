"""Model-emitted operator action plumbing.

This module intentionally performs no provider calls. It validates a
model response as one operator action, attaches roster-derived model
identity, and delegates execution to the existing hermetic harness.
Provider clients can stay thin transport adapters around this surface.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from governed_agent_bench.harness.core import HarnessConfig, HarnessError
from governed_agent_bench.model_roster import model_roster_hash

from .core import run_operator_action


_COMMAND_RE = re.compile(r"^hai [a-z0-9][a-z0-9_-]*(?: [a-z0-9][a-z0-9_-]*)*$")
_ARG_RE = re.compile(r"^--[a-z0-9][a-z0-9-]*$")
_ALLOWED_ACTION_FIELDS = {
    "schema_version",
    "action_type",
    "command",
    "args",
    "reason",
    "final_text",
}
_ACTION_TYPES = {"command", "refusal", "final"}
_ARG_SCALAR_TYPES = (str, int, float, bool, type(None))


def parse_model_action(response_text: str) -> dict[str, Any]:
    """Parse and validate the single JSON action emitted by a model."""

    try:
        action = json.loads(response_text.strip())
    except json.JSONDecodeError as exc:
        raise HarnessError(f"model response is not a JSON object: {exc}") from exc
    if not isinstance(action, dict):
        raise HarnessError("model response must be one JSON object")

    extra = sorted(set(action) - _ALLOWED_ACTION_FIELDS)
    if extra:
        raise HarnessError(f"model action has unsupported fields: {extra}")
    action_type = action.get("action_type")
    if action_type not in _ACTION_TYPES:
        raise HarnessError(f"model action has invalid action_type: {action_type!r}")
    schema_version = action.get("schema_version")
    if schema_version is not None and schema_version != (
        "governed_agent_bench.operator_action.v1"
    ):
        raise HarnessError(f"model action has invalid schema_version: {schema_version!r}")

    if action_type == "command":
        _validate_command_action(action)
    elif action_type == "refusal":
        _validate_refusal_action(action)
    else:
        _validate_final_action(action)
    return action


def harness_config_for_roster_condition(
    condition: dict[str, Any],
    *,
    fixture_root: Path,
    output_dir: Path,
    runtime_mode: str,
    claim_tier: str = "T3",
    roster_hash: str | None = None,
    python_executable: str = sys.executable,
) -> HarnessConfig:
    """Build a model-backed HarnessConfig from one roster condition."""

    return HarnessConfig(
        fixture_root=fixture_root,
        output_dir=output_dir,
        runtime_mode=runtime_mode,
        model_class=str(condition["model_class"]),
        system_id=str(condition["system_id"]),
        prompt_template_id=str(condition["prompt_id"]),
        invocation_context="agent",
        python_executable=python_executable,
        model_identity=model_identity_from_roster_condition(condition),
        claim_tier=claim_tier,
        model_roster_hash=roster_hash or model_roster_hash(),
    )


def model_identity_from_roster_condition(
    condition: dict[str, Any],
) -> dict[str, Any]:
    """Convert roster condition fields into trajectory model_identity."""

    return {
        "model_family": condition["model_family"],
        "model_id": condition["model_id"],
        "parameter_count": condition["parameter_count"],
        "quantization": condition["quantization"],
        "provider_snapshot": (
            f"{condition['provider']}@{condition['provider_snapshot_date']}"
        ),
        "decoding_settings": condition["decoding_settings"],
    }


def run_model_response_action(
    task: dict[str, Any],
    response_text: str,
    config: HarnessConfig,
    *,
    write_trajectory: bool = True,
) -> dict[str, Any]:
    """Parse one model action response and execute/record it."""

    return run_operator_action(
        task,
        parse_model_action(response_text),
        config,
        write_trajectory=write_trajectory,
    )


def _validate_command_action(action: dict[str, Any]) -> None:
    command = action.get("command")
    args = action.get("args")
    if not isinstance(command, str) or _COMMAND_RE.fullmatch(command) is None:
        raise HarnessError(f"model command is not a structured hai command: {command!r}")
    if not isinstance(args, dict):
        raise HarnessError("model command action requires args object")
    if "final_text" in action:
        raise HarnessError("model command action must not include final_text")
    for key, value in args.items():
        if not isinstance(key, str) or _ARG_RE.fullmatch(key) is None:
            raise HarnessError(f"model command arg key is invalid: {key!r}")
        _validate_arg_value(key, value)


def _validate_refusal_action(action: dict[str, Any]) -> None:
    if not isinstance(action.get("reason"), str) or not action["reason"]:
        raise HarnessError("model refusal action requires reason")
    if "command" in action or "args" in action:
        raise HarnessError("model refusal action must not include command or args")


def _validate_final_action(action: dict[str, Any]) -> None:
    if not isinstance(action.get("final_text"), str) or not action["final_text"]:
        raise HarnessError("model final action requires final_text")
    if "command" in action or "args" in action:
        raise HarnessError("model final action must not include command or args")


def _validate_arg_value(key: str, value: Any) -> None:
    if isinstance(value, _ARG_SCALAR_TYPES):
        return
    if isinstance(value, list) and all(
        isinstance(item, (str, int, float, bool)) for item in value
    ):
        return
    raise HarnessError(f"model command arg value is invalid for {key!r}: {value!r}")
