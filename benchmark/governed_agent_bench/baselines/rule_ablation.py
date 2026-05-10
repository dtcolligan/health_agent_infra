"""Offline runtime-mode ablation dry run for the rule baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from governed_agent_bench.harness import (
    HarnessConfig,
    load_manifest_snapshot,
    load_task,
    run_operator_actions,
)
from governed_agent_bench.scorer import score_trajectory

from .rule_baseline import (
    RULE_BASELINE_SYSTEM_ID,
    TASK_IDS,
    action_sequence_for_task,
    fixture_for_task,
)


REPORT_SCHEMA_VERSION = "governed_agent_bench.rule_ablation_report.v1"
MODE_TO_MECHANISM = {
    "no_validation": "validation",
    "no_agent_safe": "agent_safe",
    "no_proposal_gate": "proposal_gate",
    "no_refusal": "refusal",
    "no_audit_chain": "audit_chain",
    "no_runtime_enforcement": "all_runtime_mechanisms",
}


def run_rule_baseline_ablation(
    *,
    output_dir: Path,
    fixture_workspace: Path,
    task_ids: list[str] | None = None,
    python_executable: str = sys.executable,
) -> dict[str, Any]:
    """Run rule-baseline trajectories for every task runtime mode in scope."""

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
        for runtime_mode in task["runtime_modes_in_scope"]:
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

    report = _build_report(records)
    (output_dir / "rule_baseline_ablation_summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _build_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "system_id": RULE_BASELINE_SYSTEM_ID,
        "model_class": "rule_baseline",
        "run_count": len(records),
        "task_count": len({row["task"]["task_id"] for row in records}),
        "modes": _mode_summary(records),
        "mechanisms": _mechanism_summary(records),
        "runs": [_run_row(row) for row in records],
    }


def _mode_summary(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    modes: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        modes.setdefault(row["trajectory"]["runtime_mode"], []).append(row)
    return {
        mode: {
            "run_count": len(rows),
            "pass_count": sum(1 for row in rows if row["score"]["overall_pass"]),
            "fail_count": sum(1 for row in rows if not row["score"]["overall_pass"]),
            "task_ids": [row["task"]["task_id"] for row in rows],
        }
        for mode, rows in sorted(modes.items())
    }


def _mechanism_summary(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mechanisms: dict[str, list[dict[str, Any]]] = {}
    for row in records:
        mechanism = MODE_TO_MECHANISM.get(row["trajectory"]["runtime_mode"])
        if mechanism is not None:
            mechanisms.setdefault(mechanism, []).append(row)
    return {
        mechanism: {
            "off_mode": rows[0]["trajectory"]["runtime_mode"],
            "run_count": len(rows),
            "pass_count": sum(1 for row in rows if row["score"]["overall_pass"]),
            "fail_count": sum(1 for row in rows if not row["score"]["overall_pass"]),
            "task_ids": [row["task"]["task_id"] for row in rows],
        }
        for mechanism, rows in sorted(mechanisms.items())
    }


def _run_row(row: dict[str, Any]) -> dict[str, Any]:
    trajectory = row["trajectory"]
    disabled = [
        step["mechanism"]
        for step in trajectory["steps"]
        if step["step_type"] == "mechanism_disabled"
    ]
    return {
        "task_id": row["task"]["task_id"],
        "level": row["task"]["level"],
        "runtime_mode": trajectory["runtime_mode"],
        "load_bearing_mechanisms": row["task"]["load_bearing_mechanisms"],
        "mechanism_disabled": disabled,
        "overall_pass": row["score"]["overall_pass"],
        "trajectory_path": row["trajectory_path"],
        "score_path": row["score_path"],
    }
