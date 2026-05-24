"""Offline reproducibility runner for GovernedAgentBench.

This command intentionally runs only synthetic-fixture, no-model artifacts.
It does not call local or cloud model APIs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

BENCHMARK_ROOT = Path(__file__).resolve().parents[1]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.baselines import run_rule_baseline_ablation  # noqa: E402
from governed_agent_bench.baselines.rule_baseline import TASK_IDS  # noqa: E402
from governed_agent_bench.results import (  # noqa: E402
    write_error_taxonomy,
    write_evidence_tables,
    write_result_figures,
)
from governed_agent_bench.results.adversarial_summary import (  # noqa: E402
    build_adversarial_summary,
)
from governed_agent_bench.results.isolation_matrix import (  # noqa: E402
    build_isolation_matrix,
)
from governed_agent_bench.results.live_isolation import (  # noqa: E402
    build_live_isolation_matrix,
)


REPRO_SCHEMA_VERSION = "governed_agent_bench.offline_repro.v1"


def run_offline_repro(
    *,
    output_dir: Path,
    fixture_workspace: Path | None = None,
    task_ids: list[str] | None = None,
    python_executable: str = sys.executable,
    skip_live_isolation: bool = False,
) -> dict[str, Any]:
    """Run the offline rule-baseline reproducibility pipeline."""

    output_dir = output_dir.resolve()
    fixture_workspace = (
        fixture_workspace.resolve()
        if fixture_workspace is not None
        else output_dir / "fixtures"
    )
    run_dir = output_dir / "rule_baseline_ablation"
    table_dir = output_dir / "evidence_tables"
    figure_dir = output_dir / "figures"
    taxonomy_dir = output_dir / "error_taxonomy"
    isolation_dir = output_dir / "isolation_matrix"
    live_isolation_dir = output_dir / "live_isolation"
    adversarial_summary_dir = output_dir / "adversarial_summary"

    ablation_report = run_rule_baseline_ablation(
        output_dir=run_dir,
        fixture_workspace=fixture_workspace,
        task_ids=task_ids,
        python_executable=python_executable,
    )
    evidence_output = write_evidence_tables(
        run_dir=run_dir,
        output_dir=table_dir,
    )
    figures = write_result_figures(
        evidence_table_path=table_dir / "evidence_table.json",
        output_dir=figure_dir,
    )
    taxonomy = write_error_taxonomy(
        evidence_table_path=table_dir / "evidence_table.json",
        output_dir=taxonomy_dir,
    )

    isolation_matrix = build_isolation_matrix()
    isolation_dir.mkdir(parents=True, exist_ok=True)
    isolation_matrix_path = isolation_dir / "isolation_matrix.json"
    isolation_matrix_path.write_text(
        json.dumps(isolation_matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    live_isolation_matrix: dict[str, Any] | None = None
    live_isolation_matrix_path = live_isolation_dir / "live_isolation_matrix.json"
    if not skip_live_isolation:
        live_isolation_matrix = build_live_isolation_matrix(
            live_isolation_dir / "_work"
        )
        live_isolation_dir.mkdir(parents=True, exist_ok=True)
        live_isolation_matrix_path.write_text(
            json.dumps(live_isolation_matrix, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    adversarial_summary_dir.mkdir(parents=True, exist_ok=True)
    adversarial_summary = build_adversarial_summary(
        output_dir=adversarial_summary_dir
    )

    def _rel(path: str | Path) -> str:
        resolved = Path(path).resolve()
        if resolved.is_relative_to(output_dir):
            return resolved.relative_to(output_dir).as_posix()
        return resolved.as_posix()

    artifacts = {
        "rule_baseline_ablation_summary": _rel(
            run_dir / "rule_baseline_ablation_summary.json"
        ),
        "evidence_table_json": _rel(evidence_output["json_path"]),
        "evidence_table_csv": _rel(evidence_output["csv_path"]),
        "figures_manifest": _rel(figure_dir / "figures_manifest.json"),
        "error_taxonomy": _rel(taxonomy["json_path"]),
        "isolation_matrix": _rel(isolation_matrix_path),
        "adversarial_summary_aggregated_json": _rel(
            adversarial_summary_dir / "adversarial_summary_aggregated.json"
        ),
        "adversarial_summary_aggregated_csv": _rel(
            adversarial_summary_dir / "adversarial_summary_aggregated.csv"
        ),
        "adversarial_summary_per_trajectory_json": _rel(
            adversarial_summary_dir / "adversarial_summary_per_trajectory.json"
        ),
        "adversarial_summary_per_trajectory_csv": _rel(
            adversarial_summary_dir / "adversarial_summary_per_trajectory.csv"
        ),
    }
    if live_isolation_matrix is not None:
        artifacts["live_isolation_matrix"] = _rel(live_isolation_matrix_path)

    live_isolation_manifest = (
        {
            "schema_version": live_isolation_matrix["schema_version"],
            "evidence_tier": live_isolation_matrix["evidence_tier"],
            "live_count": live_isolation_matrix["live_count"],
            "all_live_isolated": live_isolation_matrix["all_live_isolated"],
            "live_labels": live_isolation_matrix["live_labels"],
            "skipped": False,
        }
        if live_isolation_matrix is not None
        else {"skipped": True, "reason": "skip_flag"}
    )

    manifest = {
        "schema_version": REPRO_SCHEMA_VERSION,
        "model_calls": False,
        "uses_private_data": False,
        "fixture_workspace": _rel(fixture_workspace),
        "output_dir": output_dir.as_posix(),
        "task_ids": task_ids or list(TASK_IDS),
        "artifacts": artifacts,
        "row_count": evidence_output["row_count"],
        "figure_count": figures["figure_count"],
        "violation_count": taxonomy["violation_count"],
        "runtime_modes": sorted(ablation_report["modes"]),
        "isolation_matrix": {
            "schema_version": isolation_matrix["schema_version"],
            "evidence_tier": isolation_matrix["evidence_tier"],
            "row_count": isolation_matrix["row_count"],
            "all_isolated": isolation_matrix["all_isolated"],
        },
        "live_isolation": live_isolation_manifest,
        "adversarial_summary": {
            "schema_version": adversarial_summary["schema_version"],
            "evidence_tier": adversarial_summary["evidence_tier"],
            "aggregated_count": adversarial_summary["aggregated_count"],
            "per_trajectory_count": adversarial_summary["per_trajectory_count"],
            "all_expected_failures_observed": adversarial_summary[
                "all_expected_failures_observed"
            ],
            "all_expected_violation_kinds_observed": adversarial_summary[
                "all_expected_violation_kinds_observed"
            ],
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "offline_repro_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _exit_code_for_manifest(manifest: dict[str, Any]) -> int:
    if manifest["isolation_matrix"]["all_isolated"] is False:
        return 1
    live_isolation = manifest["live_isolation"]
    if not live_isolation.get("skipped") and (
        live_isolation["all_live_isolated"] is False
    ):
        return 1
    adversarial_summary = manifest["adversarial_summary"]
    if (
        adversarial_summary["all_expected_failures_observed"] is False
        or adversarial_summary["all_expected_violation_kinds_observed"] is False
    ):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory for regenerated trajectories, scores, tables, and figures.",
    )
    parser.add_argument(
        "--fixture-workspace",
        type=Path,
        help="Optional fixture build directory. Defaults to <output-dir>/fixtures.",
    )
    parser.add_argument(
        "--task-id",
        action="append",
        dest="task_ids",
        help="Optional task id. Repeat to run a subset; omit for all MVP tasks.",
    )
    parser.add_argument(
        "--skip-live-isolation",
        action="store_true",
        help="Skip local hermetic live-isolation probes; static isolation still runs.",
    )
    args = parser.parse_args(argv)
    manifest = run_offline_repro(
        output_dir=args.output_dir,
        fixture_workspace=args.fixture_workspace,
        task_ids=args.task_ids,
        skip_live_isolation=args.skip_live_isolation,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return _exit_code_for_manifest(manifest)


if __name__ == "__main__":
    raise SystemExit(main())
