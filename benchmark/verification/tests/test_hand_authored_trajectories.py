"""Contract checks for static hand-authored benchmark trajectories."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.harness import load_manifest_snapshot, load_task  # noqa: E402


TRAJECTORY_ROOT = (
    BENCHMARK_ROOT / "governed_agent_bench" / "trajectories" / "hand_authored"
)
TRAJECTORY_SCHEMA = (
    BENCHMARK_ROOT / "governed_agent_bench" / "schema" / "trajectory.schema.json"
)
REQUIRED_TRAJECTORY_FIELDS = {
    "schema_version",
    "trajectory_id",
    "task_id",
    "system_id",
    "runtime_mode",
    "model_class",
    "manifest_snapshot_id",
    "prompt_template_id",
    "prompt_template_hash",
    "steps",
}


def _trajectories() -> list[tuple[Path, dict[str, Any]]]:
    return [
        (path, json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(TRAJECTORY_ROOT.glob("*.json"))
    ]


def test_hand_authored_trajectory_queue_has_pass_fail_pairs() -> None:
    trajectories = _trajectories()

    assert len(trajectories) == 10
    assert sum(path.name.endswith("_pass.json") for path, _ in trajectories) == 5
    assert sum(path.name.endswith("_fail.json") for path, _ in trajectories) == 5

    task_ids = {trajectory["task_id"] for _, trajectory in trajectories}
    assert len(task_ids) == 5
    for task_id in task_ids:
        matching = [
            path.name for path, row in trajectories if row["task_id"] == task_id
        ]
        assert sorted(matching) == [
            f"{task_id}_fail.json",
            f"{task_id}_pass.json",
        ]


def test_hand_authored_trajectories_match_v2_schema_surface() -> None:
    schema = json.loads(TRAJECTORY_SCHEMA.read_text(encoding="utf-8"))
    allowed_fields = set(schema["properties"])
    allowed_step_fields = set(schema["properties"]["steps"]["items"]["properties"])
    allowed_step_types = set(
        schema["properties"]["steps"]["items"]["properties"]["step_type"]["enum"]
    )

    for path, trajectory in _trajectories():
        assert REQUIRED_TRAJECTORY_FIELDS.issubset(trajectory), path
        assert set(trajectory).issubset(allowed_fields), path
        assert trajectory["schema_version"] == "governed_agent_bench.trajectory.v2"
        assert trajectory["runtime_mode"] == "full_contract"
        assert trajectory["model_class"] == "rule_baseline"
        assert "model_identity" not in trajectory
        assert trajectory["invocation_context"] == "rule_baseline"
        assert len(trajectory["prompt_template_hash"]) == 64
        assert len(trajectory.get("prompt_template_file_hash", "")) == 64
        assert trajectory["steps"], path

        for step in trajectory["steps"]:
            assert set(step).issubset(allowed_step_fields), path
            assert step["step_type"] in allowed_step_types, path
            if step["step_type"] == "command":
                assert step.get("command", "").startswith("hai "), path
                assert isinstance(step.get("args"), dict), path
            if step["step_type"] == "mechanism_disabled":
                assert step.get("mechanism") in {
                    "validation",
                    "agent_safe",
                    "proposal_gate",
                    "refusal",
                    "audit_chain",
                }


def test_hand_authored_trajectories_reference_existing_tasks_and_manifests() -> None:
    for path, trajectory in _trajectories():
        task = load_task(trajectory["task_id"])
        manifest = load_manifest_snapshot(trajectory["manifest_snapshot_id"])

        assert (
            task["allowed_context"]["manifest_ref"]
            == trajectory["manifest_snapshot_id"]
        ), path
        assert manifest["manifest_version"] == trajectory["manifest_snapshot_id"], path
        assert trajectory["prompt_template_id"] == "deployment_full_v1", path
