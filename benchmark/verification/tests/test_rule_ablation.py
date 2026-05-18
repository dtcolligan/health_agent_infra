"""Rule-baseline runtime-mode ablation report tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.baselines import run_rule_baseline_ablation  # noqa: E402
from governed_agent_bench.baselines.rule_baseline import TASK_IDS  # noqa: E402
from governed_agent_bench.harness import load_task  # noqa: E402


EXPECTED_MECHANISMS = {
    "all_runtime_mechanisms",
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
