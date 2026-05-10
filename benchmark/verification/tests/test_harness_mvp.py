"""Harness MVP contract tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.harness import (  # noqa: E402
    HarnessConfig,
    HarnessError,
    action_to_argv,
    load_task,
    run_operator_action,
)


TASK_ID = "gab_l1_doctor_status_route"


def _config(tmp_path: Path, *, runtime_mode: str = "full_contract") -> HarnessConfig:
    return HarnessConfig(
        fixture_root=tmp_path / "fixture",
        output_dir=tmp_path / "out",
        runtime_mode=runtime_mode,
    )


def test_action_to_argv_serializes_structured_args() -> None:
    argv = action_to_argv({
        "action_type": "command",
        "command": "hai today",
        "args": {
            "--as-of": "2026-05-03",
            "--user-id": "gab_read_surface",
            "--format": "json",
            "--json": True,
            "--skip": False,
            "--domain": ["recovery", "running"],
        },
    })

    assert argv == [
        "today",
        "--as-of",
        "2026-05-03",
        "--user-id",
        "gab_read_surface",
        "--format",
        "json",
        "--json",
        "--domain",
        "recovery",
        "--domain",
        "running",
    ]


def test_harness_executes_allowed_hai_command_and_writes_trajectory(
    tmp_path: Path,
) -> None:
    task = load_task(TASK_ID)
    action = {
        "schema_version": "governed_agent_bench.operator_action.v1",
        "action_type": "command",
        "command": "hai capabilities",
        "args": {"--json": True},
        "reason": "Read the governed command surface.",
    }

    trajectory = run_operator_action(task, action, _config(tmp_path))

    assert trajectory["schema_version"] == "governed_agent_bench.trajectory.v2"
    assert trajectory["task_id"] == TASK_ID
    assert trajectory["runtime_mode"] == "full_contract"
    assert trajectory["manifest_snapshot_id"] == "hai_0_2_0"
    assert trajectory["steps"][0]["step_type"] == "command"
    observation = trajectory["steps"][-1]
    assert observation["step_type"] == "observation"
    assert observation["exit_code"] == "OK"

    trajectory_path = _config(tmp_path).output_dir / f"{trajectory['trajectory_id']}.json"
    assert json.loads(trajectory_path.read_text(encoding="utf-8")) == trajectory
    stdout_ref = _config(tmp_path).output_dir / observation["stdout_ref"]
    assert json.loads(stdout_ref.read_text(encoding="utf-8"))["schema_version"] == (
        "agent_cli_contract.v2"
    )


def test_harness_blocks_commands_absent_from_manifest(tmp_path: Path) -> None:
    task = load_task(TASK_ID)

    with pytest.raises(HarnessError, match="not allowed"):
        run_operator_action(
            task,
            {
                "action_type": "command",
                "command": "hai imaginary",
                "args": {},
            },
            _config(tmp_path),
        )


def test_harness_refuses_out_of_scope_runtime_mode(tmp_path: Path) -> None:
    task = load_task(TASK_ID)

    with pytest.raises(HarnessError, match="not in task scope"):
        run_operator_action(
            task,
            {
                "action_type": "command",
                "command": "hai capabilities",
                "args": {"--json": True},
            },
            _config(tmp_path, runtime_mode="no_refusal"),
        )


def test_harness_records_refusal_and_final_actions_without_subprocess(
    tmp_path: Path,
) -> None:
    task = load_task(TASK_ID)

    refusal = run_operator_action(
        task,
        {
            "action_type": "refusal",
            "reason": "The requested action is outside the governed surface.",
            "final_text": "I cannot do that.",
        },
        _config(tmp_path),
    )
    final = run_operator_action(
        task,
        {
            "action_type": "final",
            "final_text": "The runtime contract was inspected.",
            "reason": "No further action is needed.",
        },
        _config(tmp_path),
    )

    assert refusal["steps"] == [
        {
            "step_type": "refusal",
            "reason": "The requested action is outside the governed surface.",
            "final_text": "I cannot do that.",
        }
    ]
    assert final["steps"] == [
        {
            "step_type": "final",
            "final_text": "The runtime contract was inspected.",
            "reason": "No further action is needed.",
        }
    ]
