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
    DISALLOWED_COMMAND_RECORD,
    EXIT_CODE_NAMES,
    HarnessConfig,
    HarnessError,
    append_operator_action_steps,
    normalize_command_arg_keys,
    prepare_operator_run,
    trajectory_from_steps,
    write_trajectory_artifact,
)
from governed_agent_bench.model_roster import model_roster_hash

from .core import run_operator_action


_COMMAND_RE = re.compile(r"^hai [a-z0-9][a-z0-9_-]*(?: [a-z0-9][a-z0-9_-]*)*$")
_ARG_RE = re.compile(r"^(?:--)?[a-z0-9][a-z0-9_-]*$")
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


@dataclass
class ModelTurnResult:
    """One model turn's emitted text plus provider-call metadata.

    Provider adapters return this so ``run_agent_loop`` can stamp
    per-turn cost / token / wall-time metadata onto the model's action
    step without becoming provider-aware. A bare ``str`` return is still
    accepted (treated as text with all metadata absent / ``None``).

    ``harness_injected`` (audit fix A5) marks ``text`` as harness-authored
    failure bookkeeping (e.g. a retry-exhausted sentinel) rather than model
    output. The loop still records it in the trajectory (invalid_output
    step, ledger semantics unchanged) but never replays it to the model as
    an ASSISTANT message it did not emit; the failed turn reaches the model
    only as user-role harness feedback.
    """

    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd_estimate: float | None = None
    wall_time_ms: int | None = None
    retry_count: int = 0
    harness_injected: bool = False


ModelTurn = Callable[[list[dict[str, str]]], "str | ModelTurnResult"]
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
    wall_time_ms: int | None = None
    retry_count: int = 0


@dataclass
class AgentLoopResult:
    """Completed or partial result from a bounded model-action loop."""

    trajectory: dict[str, Any]
    turn_records: list[TurnRecord]
    messages: list[dict[str, str]]
    stop_reason: str | None


def _strip_code_fence(text: str) -> str:
    """Strip a single outer Markdown code fence if the output is fenced.

    Instruction-tuned models habitually wrap their JSON action in a
    ```json ... ``` fence. The fenced payload is byte-identical JSON, so
    removing the fence is an envelope normalization only: it does not alter
    the parsed action, and downstream validation (M4) still sees exactly the
    action the model emitted. Only a single outer fence is removed, and only
    when the output *starts* with a fence; text with prose around the JSON is
    left unchanged (that remains a genuine formatting failure, not something
    to leniently extract). Unfenced output is returned untouched, so existing
    raw-JSON trajectories parse identically.
    """

    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    lines = lines[1:]  # drop the opening fence line (``` or ```json)
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]  # drop the closing fence line
    return "\n".join(lines).strip()


def _extract_json_object(text: str) -> str | None:
    """Return the first balanced top-level ``{...}`` substring, or None.

    Envelope rescue for models that wrap their JSON action in prose (a common
    cross-model formatting habit). This is envelope normalization only: the
    extracted object is validated identically downstream, so M4 typed-command
    validation is unchanged. Pure prose with no balanced object returns None
    and remains a genuine formatting failure.
    """

    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse_model_action(response_text: str) -> dict[str, Any]:
    """Parse and validate the single JSON action emitted by a model."""

    text = _strip_code_fence(response_text)
    try:
        action = json.loads(text)
    except json.JSONDecodeError as exc:
        # Envelope rescue: a single JSON action wrapped in prose. Extraction
        # does not alter the action (M4 still validates it exactly); pure prose
        # with no balanced object stays a genuine failure.
        extracted = _extract_json_object(text)
        if extracted is None:
            raise HarnessError(f"model response is not a JSON object: {exc}") from exc
        try:
            action = json.loads(extracted)
        except json.JSONDecodeError as exc2:
            raise HarnessError(
                f"model response is not a JSON object: {exc2}"
            ) from exc2
    if not isinstance(action, dict):
        raise HarnessError("model response must be one JSON object")

    # Envelope normalization: an empty/null `final_text` on a command action
    # carries no information. Drop it so the command is not rejected for a bare
    # empty field. A non-empty final_text on a command stays a genuine failure
    # (the model tried to both act and narrate).
    if action.get("action_type") == "command" and action.get("final_text") in (
        "",
        None,
    ):
        action.pop("final_text", None)

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
    hide_stdout: bool = False,
) -> HarnessConfig:
    """Build a model-backed HarnessConfig from one roster condition.

    ``hide_stdout`` (task-level) withholds command stdout from the model's
    observation feedback, so the same task can be run sighted vs blind for the
    audit fabrication demonstration.
    """

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
        hide_stdout=hide_stdout,
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
        turn_output = model_turn(messages)
        turn_meta = (
            turn_output
            if isinstance(turn_output, ModelTurnResult)
            else ModelTurnResult(text=turn_output)
        )
        raw_output = turn_meta.text
        if not turn_meta.harness_injected:
            messages.append({"role": "assistant", "content": raw_output})
        first_step_index = len(steps)
        parsed_action: dict[str, Any] | None = None
        invalid_output: dict[str, str] | None = None
        turn_stop_reason: str | None = None

        try:
            parsed_action = parse_model_action(raw_output)
            if parsed_action.get("action_type") == "command":
                normalized, rewrites = normalize_command_arg_keys(
                    str(parsed_action.get("command")),
                    dict(parsed_action.get("args") or {}),
                    state.command_manifest_snapshot,
                )
                unresolved = [
                    key for key in normalized if not str(key).startswith("--")
                ]
                if unresolved:
                    # A key that is not a syntactic variant of any real flag
                    # stays an invalid arg (e.g. an invented flag name),
                    # rejected exactly as before the normalizer existed.
                    raise HarnessError(
                        f"model command arg key is invalid: {unresolved[0]!r}"
                    )
                parsed_action["args"] = normalized
                if rewrites:
                    parsed_action["_arg_key_normalizations"] = rewrites
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
                "content": _feedback_message([steps[-1]], _feedback_stdout_dir(config)),
            })
        else:
            # IC-1 (sweep-killer fix): in the model loop a manifest-disallowed
            # command is RECORDED as a rejected command step (measured model
            # behaviour feeding hallucinated_command_rate), never a raise that
            # would strand the remaining reps of the sweep. The authored /
            # rule-baseline path keeps the raise.
            append_operator_action_steps(
                parsed_action,
                config,
                state,
                steps,
                on_disallowed_command=DISALLOWED_COMMAND_RECORD,
            )
            action_type = parsed_action["action_type"]
            if action_type == "command":
                appended_steps = steps[first_step_index:]
                messages.append({
                    "role": "user",
                    "content": _feedback_message(appended_steps, config.output_dir),
                })
                if _has_crash_observation(appended_steps):
                    turn_stop_reason = STOP_REASON_SUBPROCESS_CRASH
            elif action_type == "refusal":
                turn_stop_reason = STOP_REASON_REFUSAL
            elif action_type == "final":
                turn_stop_reason = STOP_REASON_FINAL

        if len(steps) > first_step_index:
            _stamp_action_step_metadata(steps[first_step_index], turn_meta)
        trajectory_so_far = trajectory_from_steps(task, config, state, steps)
        record = TurnRecord(
            turn_index=turn_index,
            provider_outcome=PROVIDER_OUTCOME_OK,
            raw_output=raw_output,
            parsed_action=parsed_action,
            invalid_output=invalid_output,
            executed_step_ids=list(range(first_step_index, len(steps))),
            stop_reason=turn_stop_reason,
            prompt_tokens=turn_meta.prompt_tokens,
            completion_tokens=turn_meta.completion_tokens,
            cost_usd_estimate=turn_meta.cost_usd_estimate,
            wall_time_ms=turn_meta.wall_time_ms,
            retry_count=_coerce_retry_count(turn_meta.retry_count),
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


FEEDBACK_STDOUT_MAX_CHARS = 24000


def _read_observation_stdout(step: dict[str, Any], output_dir: Any) -> str | None:
    """Read a bounded head of an observation's stdout artifact for the model.

    The trajectory persists only ``stdout_ref`` (a path) to stay lean, but the
    model must see command output to act on it (WP-RUNTIME-FIX: without this a
    read-then-narrate task is unwinnable, since the agent receives only a file
    reference it cannot open). Returns None when there is no artifact.
    """

    ref = step.get("stdout_ref")
    if not ref or output_dir is None:
        return None
    try:
        text = (Path(output_dir) / ref).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if len(text) > FEEDBACK_STDOUT_MAX_CHARS:
        text = text[:FEEDBACK_STDOUT_MAX_CHARS] + "\n...[truncated]"
    return text


def _feedback_stdout_dir(config: Any) -> Any:
    """Observation-artifact dir to resolve stdout for the model, or None when
    the harness is configured to hide tool output (blind-vs-sighted demo)."""

    if getattr(config, "hide_stdout", False):
        return None
    return config.output_dir


def _feedback_message(
    steps: list[dict[str, Any]], output_dir: Any = None
) -> str:
    enriched: list[dict[str, Any]] = []
    for step in steps:
        if step.get("step_type") == "observation" and "stdout" not in step:
            stdout = _read_observation_stdout(step, output_dir)
            if stdout is not None:
                step = {**step, "stdout": stdout}
        enriched.append(step)
    return json.dumps({"steps": enriched}, indent=2, sort_keys=True)


def _coerce_metadata_value(value: Any) -> int | float | None:
    """Force a per-turn metadata value to a numeric scalar or ``None``.

    Runtime guard so only numbers (never paths, strings, or other
    adapter-supplied content) can enter the trajectory. ``bool`` is
    excluded because it is an ``int`` subclass but not a real metric.
    """

    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    return None


def _coerce_retry_count(value: Any) -> int:
    """Force ``retry_count`` to a non-bool, nonnegative int (default 0).

    Unlike the A4 four (nullable, provider-reported), retry_count is a
    harness-known count that is always present and definitionally 0 when
    no retry loop ran. The guard keeps a malformed ``ModelTurnResult``
    from injecting non-int / negative / bool junk into trajectory bytes.
    """

    if isinstance(value, bool):
        return 0
    if isinstance(value, int) and value >= 0:
        return value
    return 0


def _stamp_action_step_metadata(
    step: dict[str, Any],
    turn_meta: ModelTurnResult,
) -> None:
    """Attach per-turn model-call metadata to a model action step.

    The four A4 fields describe the model turn, so they live on the action
    step (``command`` / ``invalid_output`` / ``refusal`` / ``final``) and
    never on the observation step, keeping exactly one ``cost_usd_estimate``
    per turn for downstream per-mechanism cost rollups. ``retry_count``
    (WP-A5) joins them through the same seam but is always a concrete int.
    """

    metadata = step.setdefault("metadata", {})
    metadata["wall_time_ms"] = _coerce_metadata_value(turn_meta.wall_time_ms)
    metadata["prompt_tokens"] = _coerce_metadata_value(turn_meta.prompt_tokens)
    metadata["completion_tokens"] = _coerce_metadata_value(
        turn_meta.completion_tokens
    )
    metadata["cost_usd_estimate"] = _coerce_metadata_value(
        turn_meta.cost_usd_estimate
    )
    metadata["retry_count"] = _coerce_retry_count(turn_meta.retry_count)


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
