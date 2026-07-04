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
    write_cell_contrasts,
    write_error_taxonomy,
    write_evidence_tables,
    write_result_figures,
)


REPRO_SCHEMA_VERSION = "governed_agent_bench.offline_repro.v1"


def run_offline_repro(
    *,
    output_dir: Path,
    fixture_workspace: Path | None = None,
    task_ids: list[str] | None = None,
    python_executable: str = sys.executable,
) -> dict[str, Any]:
    """Run the offline rule-baseline reproducibility pipeline.

    Sharp pipeline (D-37): rule-baseline ablation -> evidence tables -> figures
    -> error taxonomy. The positive-attribution apparatus (static/live isolation
    matrices, the adversarial summary) was retired with the specify-vs-enforce
    reframe.
    """

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
    contrast_dir = output_dir / "cell_contrasts"

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
    contrasts = write_cell_contrasts(
        run_dir=run_dir,
        output_dir=contrast_dir,
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
        "cell_contrasts": _rel(contrasts["json_path"]),
    }

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
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "offline_repro_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _exit_code_for_manifest(manifest: dict[str, Any]) -> int:
    # Sharp pipeline (D-37): the acid test succeeds when the rule-baseline
    # ablation produced scored rows and figures. The isolation/adversarial
    # gates were retired with the positive-attribution apparatus.
    if manifest["row_count"] < 1 or manifest["figure_count"] < 1:
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
    args = parser.parse_args(argv)
    manifest = run_offline_repro(
        output_dir=args.output_dir,
        fixture_workspace=args.fixture_workspace,
        task_ids=args.task_ids,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return _exit_code_for_manifest(manifest)


if __name__ == "__main__":
    raise SystemExit(main())
