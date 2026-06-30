"""Rule-baseline runner tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.baselines import (  # noqa: E402
    RULE_BASELINE_SYSTEM_ID,
    action_sequence_for_task,
    run_rule_baseline,
)
from governed_agent_bench.baselines.rule_baseline import TASK_IDS  # noqa: E402
from governed_agent_bench.harness import load_task  # noqa: E402


# Mirrors scorer.core._NARRATION_METRICS. The no-model rule baseline executes
# read commands but never emits a faithful final narration, so success tasks
# that request a narration metric correctly fail task_success (W8 closed the
# prior vacuous pass). The rule baseline is plumbing/routing evidence, not a
# capability baseline -- see BENCHMARK_CARD.md.
_NARRATION_METRICS = {"unsupported_narration_rate", "audit_reference_faithfulness"}


def _requires_narration(task_id: str) -> bool:
    task = load_task(task_id)
    if task["expected_behavior"]["outcome"] != "success":
        return False
    return bool(_NARRATION_METRICS & set(task.get("metrics", [])))


def test_rule_baseline_declares_action_sequence_for_each_mvp_task() -> None:
    for task_id in TASK_IDS:
        actions = action_sequence_for_task(load_task(task_id))
        assert actions
        assert all(
            action["schema_version"] == "governed_agent_bench.operator_action.v1"
            for action in actions
        )


def test_rule_baseline_writes_trajectories_scores_and_grouped_report(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "out"
    report = run_rule_baseline(
        output_dir=output_dir,
        fixture_workspace=tmp_path / "fixtures",
    )

    assert report["schema_version"] == "governed_agent_bench.rule_baseline_report.v1"
    assert report["system_id"] == RULE_BASELINE_SYSTEM_ID
    assert report["runtime_mode"] == "full_contract"
    assert report["task_count"] == len(TASK_IDS)
    expected_routing = sum(1 for task_id in TASK_IDS if load_task(task_id)["level"] == "L1")
    assert report["routing_only"]["task_count"] == expected_routing
    assert report["judgement"]["task_count"] == len(TASK_IDS) - expected_routing
    assert {row["category"] for row in report["tasks"]} == {
        "routing_only",
        "judgement",
    }

    written_report = json.loads(
        (output_dir / "rule_baseline_summary.json").read_text(encoding="utf-8")
    )
    assert written_report == report

    for row in report["tasks"]:
        trajectory = json.loads(
            (output_dir / row["trajectory_path"]).read_text(encoding="utf-8")
        )
        score = json.loads(
            (output_dir / row["score_path"]).read_text(encoding="utf-8")
        )
        assert trajectory["schema_version"] == "governed_agent_bench.trajectory.v2"
        assert trajectory["system_id"] == RULE_BASELINE_SYSTEM_ID
        assert trajectory["model_class"] == "rule_baseline"
        assert trajectory["invocation_context"] == "rule_baseline"
        assert score["schema_version"] == "governed_agent_bench.score.v2"
        assert score["trajectory_id"] == trajectory["trajectory_id"]
        if _requires_narration(row["task_id"]):
            # No final narration -> task_success gate fails, but nothing else.
            # Guard against a real regression: the only failing metric must be
            # task_success and there must be no violations.
            assert score["overall_pass"] is False, row["task_id"]
            assert score.get("violations", []) == [], row["task_id"]
            failed_metrics = {
                name
                for name, detail in score["metrics"].items()
                if isinstance(detail, dict) and detail.get("passed") is False
            }
            assert failed_metrics == {"task_success"}, row["task_id"]
        else:
            assert score["overall_pass"] is True, row["task_id"]

    drift_rows = [
        row for row in report["tasks"] if row["task_id"].startswith("gab_l7_")
    ]
    assert drift_rows
    for row in drift_rows:
        trajectory = json.loads(
            (output_dir / row["trajectory_path"]).read_text(encoding="utf-8")
        )
        commands = [
            step["command"]
            for step in trajectory["steps"]
            if step["step_type"] == "command"
        ]
        assert commands == ["hai capabilities", "hai review weekly"]
