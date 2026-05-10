"""Operator action schema invariants."""

from __future__ import annotations

import json
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = BENCHMARK_ROOT / "governed_agent_bench" / "schema"


def _schema() -> dict:
    return json.loads(
        (SCHEMA_ROOT / "operator_action.schema.json").read_text(encoding="utf-8")
    )


def _conditional_for(schema: dict, action_type: str) -> dict:
    for clause in schema["allOf"]:
        if clause["if"]["properties"]["action_type"]["const"] == action_type:
            return clause
    raise AssertionError(f"missing conditional for {action_type}")


def test_operator_action_schema_declares_closed_action_surface() -> None:
    schema = _schema()

    assert schema["additionalProperties"] is False
    assert schema["required"] == ["action_type"]
    assert schema["properties"]["action_type"]["enum"] == [
        "command",
        "refusal",
        "final",
    ]
    assert schema["properties"]["schema_version"]["const"] == (
        "governed_agent_bench.operator_action.v1"
    )


def test_command_action_requires_structured_hai_command_and_args() -> None:
    schema = _schema()
    command = schema["properties"]["command"]
    args = schema["properties"]["args"]
    clause = _conditional_for(schema, "command")

    assert command["pattern"].startswith("^hai ")
    assert "shell" in command["description"].lower()
    assert args["type"] == "object"
    assert args["propertyNames"]["pattern"] == "^--[a-z0-9][a-z0-9-]*$"
    assert args["additionalProperties"]["$ref"] == "#/$defs/arg_value"
    assert clause["then"]["required"] == ["command", "args"]
    assert clause["then"]["not"] == {"required": ["final_text"]}


def test_refusal_action_requires_reason_and_no_command_payload() -> None:
    clause = _conditional_for(_schema(), "refusal")

    assert clause["then"]["required"] == ["reason"]
    assert {"required": ["command"]} in clause["then"]["not"]["anyOf"]
    assert {"required": ["args"]} in clause["then"]["not"]["anyOf"]


def test_final_action_requires_final_text_and_no_command_payload() -> None:
    clause = _conditional_for(_schema(), "final")

    assert clause["then"]["required"] == ["final_text"]
    assert {"required": ["command"]} in clause["then"]["not"]["anyOf"]
    assert {"required": ["args"]} in clause["then"]["not"]["anyOf"]


def test_schema_readme_maps_actions_to_trajectory_steps() -> None:
    readme = (SCHEMA_ROOT / "README.md").read_text(encoding="utf-8")

    assert "operator_action.schema.json" in readme
    assert 'action_type: "command"' in readme
    assert 'step_type: "command"' in readme
    assert 'action_type: "refusal"' in readme
    assert 'step_type: "refusal"' in readme
    assert 'action_type: "final"' in readme
    assert 'step_type: "final"' in readme
