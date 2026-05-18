"""Deterministic no-model baseline for GovernedAgentBench."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from governed_agent_bench.harness import (
    HarnessConfig,
    load_manifest_snapshot,
    load_task,
    run_operator_actions,
)
from governed_agent_bench.harness.core import BENCHMARK_ROOT, REPO_ROOT
from governed_agent_bench.scorer import score_trajectory


RULE_BASELINE_SYSTEM_ID = "rule_baseline_v1"
REPORT_SCHEMA_VERSION = "governed_agent_bench.rule_baseline_report.v1"
FIXTURE_ROOT = BENCHMARK_ROOT / "fixtures"
TASK_IDS = tuple(
    path.stem for path in sorted((BENCHMARK_ROOT / "tasks").glob("l[1-7]/gab_*.json"))
)


def action_sequence_for_task(task: dict[str, Any]) -> list[dict[str, Any]]:
    """Return deterministic operator actions for one benchmark task."""

    expected = task["expected_behavior"]
    if expected["outcome"] == "refusal":
        return [{
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "refusal",
            "reason": expected.get("refusal_reason", "The request is outside the contract."),
            "final_text": "I cannot complete that request autonomously under the contract.",
        }]

    actions: list[dict[str, Any]] = []
    for row in expected.get("command_sequence", []):
        if row.get("required", True):
            actions.append(_action_for_expected_command(task, row["command"]))
    if not actions:
        raise ValueError(f"no rule-baseline action sequence for task_id={task['task_id']!r}")
    return actions


def _action_for_expected_command(task: dict[str, Any], command: str) -> dict[str, Any]:
    fixture_refs = task.get("allowed_context", {}).get("fixture_refs") or []
    fixture = fixture_refs[0] if fixture_refs else "empty_user"
    if command == "hai doctor":
        return _command(command, {}, "Read the runtime health status.")
    if command == "hai capabilities":
        return _command(
            command,
            {"--json": True},
            "Refresh the current command surface before choosing a command.",
        )
    if command == "hai today":
        user_id = "gab_empty" if fixture == "empty_user" else "gab_read_surface"
        return _command(
            command,
            {"--as-of": "2026-05-03", "--user-id": user_id, "--format": "json"},
            "Read the fixture daily-plan surface.",
        )
    if command == "hai explain":
        return _command(
            command,
            {"--as-of": "2026-05-03", "--user-id": "gab_read_surface"},
            "Use the explain read surface as the only evidence source.",
        )
    if command == "hai target list":
        return _command(
            command,
            {"--user-id": "gab_governance", "--all": True, "--status": "proposed"},
            "Inspect proposed target rows without committing them.",
        )
    if command == "hai intent list":
        return _command(
            command,
            {"--user-id": "gab_governance", "--all": True, "--status": "proposed"},
            "Inspect proposed intent rows without committing them.",
        )
    if command == "hai review weekly":
        return _command(
            command,
            {"--week": "2026-W19", "--user-id": "gab_drift", "--json": True},
            "Use the refreshed weekly-review command from the current runtime.",
        )
    raise ValueError(
        f"no rule-baseline command mapping for task_id={task['task_id']!r} "
        f"command={command!r}"
    )


def run_rule_baseline(
    *,
    output_dir: Path,
    fixture_workspace: Path,
    task_ids: list[str] | None = None,
    runtime_mode: str = "full_contract",
    python_executable: str = sys.executable,
) -> dict[str, Any]:
    """Run the deterministic rule baseline and write trajectories/scores/report."""

    selected_task_ids = task_ids or list(TASK_IDS)
    output_dir.mkdir(parents=True, exist_ok=True)
    trajectory_dir = output_dir / "trajectories"
    score_dir = output_dir / "scores"
    score_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    for task_id in selected_task_ids:
        task = load_task(task_id)
        fixture_root = fixture_for_task(
            task,
            fixture_workspace=fixture_workspace,
            python_executable=python_executable,
        )
        trajectory = run_operator_actions(
            task,
            action_sequence_for_task(task),
            HarnessConfig(
                fixture_root=fixture_root,
                output_dir=trajectory_dir,
                runtime_mode=runtime_mode,
                system_id=RULE_BASELINE_SYSTEM_ID,
                python_executable=python_executable,
            ),
        )
        score = score_trajectory(
            task,
            trajectory,
            manifest_snapshot=load_manifest_snapshot(
                trajectory["manifest_snapshot_id"]
            ),
            observation_root=trajectory_dir,
        )
        score_path = score_dir / f"{trajectory['trajectory_id']}.score.json"
        score_path.write_text(
            json.dumps(score, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        records.append({
            "task": task,
            "trajectory": trajectory,
            "score": score,
            "score_path": score_path.relative_to(output_dir).as_posix(),
            "trajectory_path": (
                Path("trajectories") / f"{trajectory['trajectory_id']}.json"
            ).as_posix(),
        })

    report = _build_report(records, runtime_mode=runtime_mode)
    (output_dir / "rule_baseline_summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _command(command: str, args: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "schema_version": "governed_agent_bench.operator_action.v1",
        "action_type": "command",
        "command": command,
        "args": args,
        "reason": reason,
    }


def fixture_for_task(
    task: dict[str, Any],
    *,
    fixture_workspace: Path,
    python_executable: str,
) -> Path:
    fixture_refs = task.get("allowed_context", {}).get("fixture_refs") or ["empty_user"]
    fixture_id = fixture_refs[0]
    fixture_root = fixture_workspace / fixture_id
    if (fixture_root / "fixture_metadata.json").exists():
        return fixture_root
    builder = FIXTURE_ROOT / fixture_id / "build.py"
    if not builder.exists():
        raise ValueError(f"fixture builder not found: {fixture_id}")
    fixture_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [python_executable, str(builder), str(fixture_root)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return fixture_root


def _build_report(
    records: list[dict[str, Any]],
    *,
    runtime_mode: str,
) -> dict[str, Any]:
    routing_records = [row for row in records if row["task"]["level"] == "L1"]
    judgement_records = [row for row in records if row["task"]["level"] != "L1"]
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "system_id": RULE_BASELINE_SYSTEM_ID,
        "runtime_mode": runtime_mode,
        "task_count": len(records),
        "routing_only": _summarize_group(routing_records),
        "judgement": _summarize_group(judgement_records),
        "tasks": [
            {
                "task_id": row["task"]["task_id"],
                "level": row["task"]["level"],
                "category": "routing_only"
                if row["task"]["level"] == "L1"
                else "judgement",
                "overall_pass": row["score"]["overall_pass"],
                "trajectory_path": row["trajectory_path"],
                "score_path": row["score_path"],
            }
            for row in records
        ],
    }


def _summarize_group(records: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for row in records if row["score"]["overall_pass"])
    return {
        "task_count": len(records),
        "pass_count": passed,
        "fail_count": len(records) - passed,
        "task_ids": [row["task"]["task_id"] for row in records],
    }
