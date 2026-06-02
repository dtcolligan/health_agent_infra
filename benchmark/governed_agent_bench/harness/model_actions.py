"""Model-emitted operator action plumbing.

This module intentionally performs no provider calls. It validates a
model response as one operator action, attaches roster-derived model
identity, and delegates execution to the existing hermetic harness.
Provider clients can stay thin transport adapters around this surface.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

from governed_agent_bench.harness.core import (
    EXIT_CODE_NAMES,
    HarnessConfig,
    HarnessError,
    append_operator_action_steps,
    prepare_operator_run,
    trajectory_from_steps,
    write_trajectory_artifact,
)
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
AFTER_TURN_CONTINUE = "continue"
AFTER_TURN_STOP = "stop"
PROVIDER_OUTCOME_OK = "ok"
STOP_REASON_AFTER_TURN = "after_turn_stop"
STOP_REASON_FINAL = "final"
STOP_REASON_REFUSAL = "refusal"
STOP_REASON_MAX_TURNS = "max_turns"
STOP_REASON_SUBPROCESS_CRASH = "subprocess_crash"

AfterTurnDecision = Literal["continue", "stop"] | None
ModelTurn = Callable[[list[dict[str, str]]], str]
AfterTurn = Callable[["TurnRecord", dict[str, Any]], AfterTurnDecision]


@dataclass
class TurnRecord:
    """One model turn's parsed/invalid result and appended trajectory steps."""

    turn_index: int
    provider_outcome: str
    raw_output: str | None
    parsed_action: dict[str, Any] | None
    invalid_output: dict[str, str] | None
    executed_step_ids: list[int]
    stop_reason: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd_estimate: float | None = None
    elapsed_ms: int | None = None


@dataclass
class AgentLoopResult:
    """Completed or partial result from a bounded model-action loop."""

    trajectory: dict[str, Any]
    turn_records: list[TurnRecord]
    messages: list[dict[str, str]]
    stop_reason: str | None


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


def run_agent_loop(
    task: dict[str, Any],
    config: HarnessConfig,
    model_turn: ModelTurn,
    *,
    max_turns: int = 7,
    rep: int = 0,
    after_turn: AfterTurn | None = None,
    write_trajectory: bool = True,
) -> AgentLoopResult:
    """Run a bounded provider-neutral model-action loop for one task."""

    if max_turns < 1:
        raise HarnessError("max_turns must be at least 1")
    if rep < 0:
        raise HarnessError("rep must be non-negative")
    trajectory_id = _agent_loop_trajectory_id(task, config, rep)
    state = prepare_operator_run(task, config, trajectory_id=trajectory_id)
    messages = _messages_from_rendered_prompt(state.prompt["rendered_prompt"])
    steps: list[dict[str, Any]] = []
    turn_records: list[TurnRecord] = []
    stop_reason: str | None = None

    for turn_index in range(max_turns):
        raw_output = model_turn(messages)
        messages.append({"role": "assistant", "content": raw_output})
        first_step_index = len(steps)
        parsed_action: dict[str, Any] | None = None
        invalid_output: dict[str, str] | None = None
        turn_stop_reason: str | None = None

        try:
            parsed_action = parse_model_action(raw_output)
        except HarnessError as exc:
            invalid_output = {
                "raw_output": raw_output,
                "parse_error": str(exc),
            }
            steps.append({
                "step_type": "invalid_output",
                **invalid_output,
            })
            messages.append({
                "role": "user",
                "content": _feedback_message([steps[-1]]),
            })
        else:
            append_operator_action_steps(parsed_action, config, state, steps)
            action_type = parsed_action["action_type"]
            if action_type == "command":
                appended_steps = steps[first_step_index:]
                messages.append({
                    "role": "user",
                    "content": _feedback_message(appended_steps),
                })
                if _has_crash_observation(appended_steps):
                    turn_stop_reason = STOP_REASON_SUBPROCESS_CRASH
            elif action_type == "refusal":
                turn_stop_reason = STOP_REASON_REFUSAL
            elif action_type == "final":
                turn_stop_reason = STOP_REASON_FINAL

        trajectory_so_far = trajectory_from_steps(task, config, state, steps)
        record = TurnRecord(
            turn_index=turn_index,
            provider_outcome=PROVIDER_OUTCOME_OK,
            raw_output=raw_output,
            parsed_action=parsed_action,
            invalid_output=invalid_output,
            executed_step_ids=list(range(first_step_index, len(steps))),
            stop_reason=turn_stop_reason,
        )
        turn_records.append(record)

        decision = (
            after_turn(record, trajectory_so_far)
            if after_turn is not None
            else AFTER_TURN_CONTINUE
        )
        if decision not in {AFTER_TURN_CONTINUE, AFTER_TURN_STOP, None}:
            raise HarnessError(f"after_turn returned unsupported decision: {decision!r}")
        if decision == AFTER_TURN_STOP and turn_stop_reason is None:
            record.stop_reason = STOP_REASON_AFTER_TURN
            turn_stop_reason = STOP_REASON_AFTER_TURN
        if turn_stop_reason is not None:
            stop_reason = turn_stop_reason
            break
    else:
        stop_reason = STOP_REASON_MAX_TURNS
        if turn_records:
            turn_records[-1].stop_reason = STOP_REASON_MAX_TURNS

    trajectory = trajectory_from_steps(task, config, state, steps)
    if write_trajectory:
        write_trajectory_artifact(trajectory, config)
    return AgentLoopResult(
        trajectory=trajectory,
        turn_records=turn_records,
        messages=messages,
        stop_reason=stop_reason,
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


def _messages_from_rendered_prompt(rendered_prompt: str) -> list[dict[str, str]]:
    marker = "\nUSER:\n"
    try:
        system_text, user_text = rendered_prompt.rsplit(marker, 1)
    except ValueError as exc:
        raise HarnessError("rendered deployment prompt missing USER block") from exc
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


def _feedback_message(steps: list[dict[str, Any]]) -> str:
    return json.dumps({"steps": steps}, indent=2, sort_keys=True)


def _has_crash_observation(steps: list[dict[str, Any]]) -> bool:
    normalized = set(EXIT_CODE_NAMES.values())
    for step in steps:
        if step.get("step_type") != "observation":
            continue
        exit_code = step.get("exit_code")
        if isinstance(exit_code, str) and exit_code not in normalized:
            return True
    return False


def _agent_loop_trajectory_id(
    task: dict[str, Any],
    config: HarnessConfig,
    rep: int,
) -> str:
    state = prepare_operator_run(
        task,
        config,
        trajectory_id=f"{task['task_id']}_{config.system_id}_pending",
    )
    digest = hashlib.sha256(
        json.dumps(
            {
                "task_id": task["task_id"],
                "system_id": config.system_id,
                "runtime_mode": config.runtime_mode,
                "prompt_template_hash": state.prompt["prompt_template_hash"],
                "rep": rep,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:12]
    return f"{task['task_id']}_{config.system_id}_rep{rep}_{digest}"
