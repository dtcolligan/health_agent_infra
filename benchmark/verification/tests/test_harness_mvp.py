"""Harness MVP contract tests."""

from __future__ import annotations

import json
import subprocess
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
GOVERNANCE_TASK_ID = "gab_l6_block_agent_commit"
GOVERNANCE_BUILDER = (
    BENCHMARK_ROOT
    / "governed_agent_bench"
    / "fixtures"
    / "governance_user"
    / "build.py"
)


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
    assert trajectory["invocation_context"] == "rule_baseline"
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


def test_harness_requires_agent_context_for_model_backed_runs(tmp_path: Path) -> None:
    task = load_task(TASK_ID)

    with pytest.raises(HarnessError, match="requires invocation_context='agent'"):
        run_operator_action(
            task,
            {
                "action_type": "command",
                "command": "hai capabilities",
                "args": {"--json": True},
            },
            HarnessConfig(
                fixture_root=tmp_path / "fixture",
                output_dir=tmp_path / "out",
                model_class="local",
                invocation_context="rule_baseline",
            ),
        )


def test_harness_captures_mechanism_disabled_marker(tmp_path: Path) -> None:
    fixture_root = tmp_path / "governance_user"
    subprocess.run(
        [sys.executable, str(GOVERNANCE_BUILDER), str(fixture_root)],
        cwd=BENCHMARK_ROOT.parent,
        capture_output=True,
        text=True,
        check=True,
    )
    metadata = json.loads((fixture_root / "fixture_metadata.json").read_text())
    task = load_task(GOVERNANCE_TASK_ID)
    action = {
        "action_type": "command",
        "command": "hai intent commit",
        "args": {
            "--user-id": "gab_governance",
            "--intent-id": metadata["pending_intent_id"],
            "--confirm": True,
        },
        "reason": "Exercise no_agent_safe marker capture against fixture state.",
    }

    trajectory = run_operator_action(
        task,
        action,
        HarnessConfig(
            fixture_root=fixture_root,
            output_dir=tmp_path / "out",
            runtime_mode="no_agent_safe",
        ),
    )

    assert [step["step_type"] for step in trajectory["steps"]] == [
        "command",
        "mechanism_disabled",
        "observation",
    ]
    marker = trajectory["steps"][1]
    assert marker["mechanism"] == "agent_safe"
    assert marker["metadata"]["runtime_mode"] == "no_agent_safe"
    assert trajectory["steps"][-1]["exit_code"] == "OK"


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
