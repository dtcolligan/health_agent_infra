"""Harness MVP for executing structured operator actions against HAI.

This module intentionally has no model backend. It accepts a
hand-authored operator action, checks it against the frozen manifest
allowlist, executes HAI in a hermetic fixture environment, and records a
trajectory-shaped artifact for the deterministic scorer.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BENCHMARK_ROOT.parents[1]
MANIFEST_ROOT = BENCHMARK_ROOT / "manifests"
PROMPT_ROOT = BENCHMARK_ROOT / "prompts"
TASK_ROOT = BENCHMARK_ROOT / "tasks"

EXIT_CODE_NAMES = {
    0: "OK",
    1: "USER_INPUT",
    2: "TRANSIENT",
    3: "NOT_FOUND",
    4: "INTERNAL",
}


class HarnessError(RuntimeError):
    """Raised when an operator action cannot be safely executed."""


@dataclass(frozen=True)
class HarnessConfig:
    """Configuration for one harness execution."""

    fixture_root: Path
    output_dir: Path
    runtime_mode: str = "full_contract"
    model_class: str = "rule_baseline"
    system_id: str = "rule_baseline_v1"
    prompt_template_id: str = "deployment_full_v1"
    invocation_context: str = "rule_baseline"
    python_executable: str = sys.executable


def load_json(path: Path) -> dict[str, Any]:
    """Load one JSON object from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def load_task(path_or_id: str | Path) -> dict[str, Any]:
    """Load a benchmark task by path or task id."""

    path = Path(path_or_id)
    if path.exists():
        return load_json(path)
    matches = sorted(TASK_ROOT.glob(f"l[1-7]/{path_or_id}.json"))
    if len(matches) != 1:
        raise HarnessError(f"task not found or ambiguous: {path_or_id}")
    return load_json(matches[0])


def load_manifest_snapshot(snapshot_id: str) -> dict[str, Any]:
    """Load a frozen manifest snapshot by id."""

    path = MANIFEST_ROOT / f"{snapshot_id}.json"
    if not path.exists():
        raise HarnessError(f"manifest snapshot not found: {snapshot_id}")
    return load_json(path)


def action_to_argv(action: dict[str, Any]) -> list[str]:
    """Serialize a structured command action into HAI argv tokens."""

    if action.get("action_type") != "command":
        raise HarnessError("action_to_argv requires action_type='command'")
    command = action.get("command")
    args = action.get("args")
    if not isinstance(command, str) or not command.startswith("hai "):
        raise HarnessError("command actions must use a structured 'hai ...' command")
    if not isinstance(args, dict):
        raise HarnessError("command actions must carry an args object")

    argv = command.split()[1:]
    for flag, value in args.items():
        if not isinstance(flag, str) or not flag.startswith("--"):
            raise HarnessError(f"invalid flag name: {flag!r}")
        if value is False or value is None:
            continue
        if value is True:
            argv.append(flag)
            continue
        if isinstance(value, list):
            for item in value:
                argv.extend([flag, str(item)])
            continue
        argv.extend([flag, str(value)])
    return argv


def run_operator_action(
    task: dict[str, Any],
    action: dict[str, Any],
    config: HarnessConfig,
    *,
    write_trajectory: bool = True,
) -> dict[str, Any]:
    """Execute one operator action and return a trajectory dict."""

    _ensure_runtime_mode_in_scope(task, config.runtime_mode)
    _ensure_invocation_context(config)
    manifest_id = _manifest_id(task)
    manifest_snapshot = load_manifest_snapshot(manifest_id)
    prompt = render_prompt(task, manifest_snapshot, config.prompt_template_id)
    trajectory_id = _trajectory_id(task, action, config)
    steps: list[dict[str, Any]] = []

    action_type = action.get("action_type")
    if action_type == "command":
        command = _command_text(action)
        _ensure_command_allowed(command, manifest_snapshot)
        steps.append({
            "step_type": "command",
            "command": command,
            "args": dict(action.get("args") or {}),
            "reason": action.get("reason", ""),
        })
        completed = _run_hai(action, config)
        stdout_ref, stderr_ref = _write_observation_artifacts(
            completed,
            output_dir=config.output_dir,
            trajectory_id=trajectory_id,
            step_index=len(steps),
        )
        steps.extend(_mechanism_disabled_steps(completed.stderr))
        steps.append({
            "step_type": "observation",
            "exit_code": EXIT_CODE_NAMES.get(
                completed.returncode, f"EXIT_{completed.returncode}"
            ),
            "stdout_ref": stdout_ref,
            "stderr_ref": stderr_ref,
            "metadata": {"returncode": completed.returncode},
        })
    elif action_type == "refusal":
        steps.append({
            "step_type": "refusal",
            "reason": _required_string(action, "reason"),
            **({"final_text": action["final_text"]} if action.get("final_text") else {}),
        })
    elif action_type == "final":
        steps.append({
            "step_type": "final",
            "final_text": _required_string(action, "final_text"),
            **({"reason": action["reason"]} if action.get("reason") else {}),
        })
    else:
        raise HarnessError(f"unknown action_type: {action_type!r}")

    trajectory = {
        "schema_version": "governed_agent_bench.trajectory.v2",
        "trajectory_id": trajectory_id,
        "task_id": task["task_id"],
        "system_id": config.system_id,
        "runtime_mode": config.runtime_mode,
        "model_class": config.model_class,
        "manifest_snapshot_id": manifest_id,
        "prompt_template_id": config.prompt_template_id,
        "prompt_template_hash": prompt["prompt_template_hash"],
        "prompt_template_file_hash": prompt["prompt_template_file_hash"],
        "invocation_context": config.invocation_context,
        "steps": steps,
    }
    if write_trajectory:
        config.output_dir.mkdir(parents=True, exist_ok=True)
        path = config.output_dir / f"{trajectory_id}.json"
        path.write_text(
            json.dumps(trajectory, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return trajectory


def render_prompt(
    task: dict[str, Any],
    manifest_snapshot: dict[str, Any],
    template_id: str = "deployment_full_v1",
) -> dict[str, str]:
    """Render the deployment prompt and return text plus stable hashes."""

    template_path = PROMPT_ROOT / f"{template_id}.md"
    if not template_path.exists():
        raise HarnessError(f"prompt template not found: {template_id}")
    template_text = template_path.read_text(encoding="utf-8")
    system_template = _system_prompt_block(template_text)
    manifest_id = _manifest_id(task)
    manifest = manifest_snapshot.get("manifest", manifest_snapshot)
    rendered_system = system_template
    substitutions = {
        "{{manifest_snapshot_id}}": manifest_id,
        "{{manifest_json}}": _json_block(manifest),
        "{{refusal_taxonomy_json}}": _json_block(manifest.get("refusals", [])),
        "{{mutation_classes_json}}": _json_block(
            manifest.get("mutation_classes", [])
        ),
        "{{exit_code_taxonomy_json}}": _json_block(manifest.get("exit_codes", {})),
    }
    for placeholder, value in substitutions.items():
        rendered_system = rendered_system.replace(placeholder, value)
    rendered = f"{rendered_system}\nUSER:\n{task.get('user_prompt', '')}\n"
    return {
        "prompt_template_id": template_id,
        "prompt_template_file_hash": _sha256_text(template_text),
        "prompt_template_hash": _sha256_text(rendered),
        "rendered_prompt": rendered,
    }


def _run_hai(
    action: dict[str, Any],
    config: HarnessConfig,
) -> subprocess.CompletedProcess[str]:
    argv = action_to_argv(action)
    env = _subprocess_env(config)
    return subprocess.run(
        [config.python_executable, "-m", "health_agent_infra.cli", *argv],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _subprocess_env(config: HarnessConfig) -> dict[str, str]:
    fixture_root = config.fixture_root.resolve()
    env = os.environ.copy()
    env.update({
        "HAI_HERMETIC": "1",
        "HAI_STATE_DB": str(fixture_root / "state.db"),
        "HAI_BASE_DIR": str(fixture_root / "base"),
        "HAI_RUNTIME_MODE": config.runtime_mode,
        "HAI_INVOCATION_CONTEXT": config.invocation_context,
        "HOME": str(fixture_root / "home"),
        "XDG_CONFIG_HOME": str(fixture_root / "xdg_config"),
    })
    for dirname in ("base", "home", "xdg_config"):
        (fixture_root / dirname).mkdir(parents=True, exist_ok=True)
    return env


def _write_observation_artifacts(
    completed: subprocess.CompletedProcess[str],
    *,
    output_dir: Path,
    trajectory_id: str,
    step_index: int,
) -> tuple[str, str]:
    obs_dir = output_dir / "observations"
    obs_dir.mkdir(parents=True, exist_ok=True)
    stdout_rel = Path("observations") / f"{trajectory_id}_step{step_index}_stdout.txt"
    stderr_rel = Path("observations") / f"{trajectory_id}_step{step_index}_stderr.txt"
    (output_dir / stdout_rel).write_text(completed.stdout, encoding="utf-8")
    (output_dir / stderr_rel).write_text(completed.stderr, encoding="utf-8")
    return stdout_rel.as_posix(), stderr_rel.as_posix()


def _mechanism_disabled_steps(stderr: str) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for line in stderr.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("step_type") != "mechanism_disabled":
            continue
        steps.append({
            "step_type": "mechanism_disabled",
            "mechanism": payload["mechanism"],
            "metadata": payload,
        })
    return steps


def _ensure_runtime_mode_in_scope(task: dict[str, Any], runtime_mode: str) -> None:
    modes = task.get("runtime_modes_in_scope") or ["full_contract"]
    if runtime_mode not in modes:
        raise HarnessError(
            f"runtime_mode={runtime_mode!r} not in task scope {modes!r}"
        )


def _ensure_invocation_context(config: HarnessConfig) -> None:
    expected = "rule_baseline" if config.model_class == "rule_baseline" else "agent"
    if config.invocation_context != expected:
        raise HarnessError(
            f"model_class={config.model_class!r} requires "
            f"invocation_context={expected!r}; got {config.invocation_context!r}"
        )


def _ensure_command_allowed(
    command: str,
    manifest_snapshot: dict[str, Any],
) -> None:
    if command not in _manifest_commands(manifest_snapshot):
        raise HarnessError(f"command not allowed by manifest snapshot: {command}")


def _manifest_commands(manifest_snapshot: dict[str, Any]) -> set[str]:
    manifest = manifest_snapshot.get("manifest", manifest_snapshot)
    commands = set()
    for row in manifest.get("commands", []):
        name = row.get("name") or row.get("command")
        if name:
            commands.add(str(name))
    return commands


def _system_prompt_block(template_text: str) -> str:
    marker = "## System prompt"
    start = template_text.find(marker)
    if start < 0:
        raise HarnessError("prompt template missing system prompt section")
    fence_start = template_text.find("```", start)
    if fence_start < 0:
        raise HarnessError("prompt template missing opening fence")
    body_start = template_text.find("\n", fence_start)
    if body_start < 0:
        raise HarnessError("prompt template opening fence is malformed")
    fence_end = template_text.find("```", body_start + 1)
    if fence_end < 0:
        raise HarnessError("prompt template missing closing fence")
    return template_text[body_start + 1:fence_end].strip()


def _json_block(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True)


def _manifest_id(task: dict[str, Any]) -> str:
    try:
        return str(task["allowed_context"]["manifest_ref"])
    except KeyError as exc:
        raise HarnessError("task missing allowed_context.manifest_ref") from exc


def _command_text(action: dict[str, Any]) -> str:
    command = action.get("command")
    if not isinstance(command, str):
        raise HarnessError("command action missing command string")
    return command


def _required_string(action: dict[str, Any], key: str) -> str:
    value = action.get(key)
    if not isinstance(value, str) or not value:
        raise HarnessError(f"action missing required string: {key}")
    return value


def _trajectory_id(
    task: dict[str, Any],
    action: dict[str, Any],
    config: HarnessConfig,
) -> str:
    digest = hashlib.sha256(
        json.dumps(
            {
                "task_id": task["task_id"],
                "action": action,
                "runtime_mode": config.runtime_mode,
                "system_id": config.system_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()[:12]
    return f"{task['task_id']}_{config.system_id}_{digest}"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
