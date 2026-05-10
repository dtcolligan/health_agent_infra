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
from governed_agent_bench.harness import load_task  # noqa: E402


def test_rule_baseline_declares_action_sequence_for_each_mvp_task() -> None:
    task_ids = {
        "gab_l1_doctor_status_route",
        "gab_l1_today_json_route",
        "gab_l2_empty_today_user_input",
        "gab_l2_governance_pending_list",
        "gab_l5_today_faithful_summary",
        "gab_l5_explain_evidence_summary",
        "gab_l6_block_agent_commit",
        "gab_l6_refuse_diagnosis_request",
        "gab_l7_stale_missing_weekly_command",
        "gab_l7_stale_v1_manifest_shape",
    }

    for task_id in task_ids:
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
    assert report["task_count"] == 10
    assert report["routing_only"]["task_count"] == 2
    assert report["judgement"]["task_count"] == 8
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
