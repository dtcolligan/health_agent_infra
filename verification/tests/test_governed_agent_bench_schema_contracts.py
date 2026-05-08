"""Guard schema invariants required by the research planning layer."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = REPO_ROOT / "benchmarks" / "governed_agent_bench" / "schema"


def _schema(name: str) -> dict:
    return json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))


def test_trajectory_records_structured_operator_actions() -> None:
    trajectory = _schema("trajectory.schema.json")
    step_properties = trajectory["properties"]["steps"]["items"]["properties"]

    assert "condition" in trajectory["required"]
    assert "args" in step_properties
    assert "reason" in step_properties
    assert "final_text" in step_properties


def test_task_metric_enum_matches_scoring_spec() -> None:
    task = _schema("task.schema.json")
    metrics = task["properties"]["metrics"]["items"]["enum"]

    assert "audit_reference_faithfulness" in metrics


def test_score_schema_records_reproducibility_anchors() -> None:
    trajectory = _schema("trajectory.schema.json")
    score = _schema("score.schema.json")

    for field in ("condition", "manifest_version", "scorer_version"):
        assert field in score["required"]

    assert (
        score["properties"]["condition"]["enum"]
        == trajectory["properties"]["condition"]["enum"]
    )
    assert "string" not in score["properties"]["metrics"][
        "additionalProperties"
    ]["properties"]["value"]["type"]
