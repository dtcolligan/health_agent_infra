"""Rule-baseline runtime-mode ablation report tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.baselines import run_rule_baseline_ablation  # noqa: E402
from governed_agent_bench.harness import load_task  # noqa: E402


TASK_IDS = [
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
]
EXPECTED_MECHANISMS = {
    "validation",
    "agent_safe",
    "proposal_gate",
    "refusal",
    "audit_chain",
}


def test_rule_baseline_ablation_writes_offline_report(tmp_path: Path) -> None:
    report = run_rule_baseline_ablation(
        output_dir=tmp_path / "out",
        fixture_workspace=tmp_path / "fixtures",
    )

    expected_runs = sum(
        len(load_task(task_id)["runtime_modes_in_scope"]) for task_id in TASK_IDS
    )
    assert report["schema_version"] == "governed_agent_bench.rule_ablation_report.v1"
    assert report["model_class"] == "rule_baseline"
    assert report["task_count"] == len(TASK_IDS)
    assert report["run_count"] == expected_runs
    assert set(report["mechanisms"]) == EXPECTED_MECHANISMS
    assert report["modes"]["full_contract"]["run_count"] == len(TASK_IDS)

    written_report = json.loads(
        (tmp_path / "out" / "rule_baseline_ablation_summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert written_report == report

    for row in report["runs"]:
        trajectory_path = tmp_path / "out" / row["trajectory_path"]
        score_path = tmp_path / "out" / row["score_path"]
        assert trajectory_path.exists(), row
        assert score_path.exists(), row
        trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))
        score = json.loads(score_path.read_text(encoding="utf-8"))
        assert trajectory["runtime_mode"] == row["runtime_mode"]
        assert score["trajectory_id"] == trajectory["trajectory_id"]
