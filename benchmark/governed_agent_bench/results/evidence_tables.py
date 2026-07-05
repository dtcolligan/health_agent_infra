"""Deterministic evidence-table construction from score artifacts.

Consumes the shared run-layout reader (SF-1), so both the flat rule-baseline
layout (run_dir/scores + run_dir/trajectories) and the nested paid-pilot
layout (conditions/<system>/runtime_mode_<mode>/tasks/<task>/rep_XX.*) yield
the same normalized rows.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from governed_agent_bench.harness import load_task

from .cell_contrasts import cell_label, contract_arm_of
from .run_layout import RepRecord, load_rep_records


EVIDENCE_TABLE_SCHEMA_VERSION = "governed_agent_bench.evidence_table.v1"
CSV_COLUMNS = [
    "task_id",
    "level",
    "trajectory_id",
    "system_id",
    "model_class",
    "runtime_mode",
    "contract_arm",
    "cell",
    "load_bearing_mechanisms",
    "manifest_id",
    "prompt_template_id",
    "prompt_template_hash",
    "prompt_template_file_hash",
    "scorer_version",
    "scorer_config_hash",
    "overall_pass",
    "metric_count",
    "violation_count",
    "violation_kinds",
    "violations_json",
    "metrics_json",
]


def build_evidence_rows(run_dir: Path) -> list[dict[str, Any]]:
    """Build one normalized row per score/trajectory pair in a run dir."""

    rows = [_row_from_record(record) for record in load_rep_records(run_dir)]
    return sorted(
        rows,
        key=lambda row: (
            row["task_id"],
            row["runtime_mode"],
            row["system_id"],
            row["trajectory_id"],
        ),
    )


def write_evidence_tables(
    *,
    run_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Write JSON and CSV evidence tables from a score artifact directory."""

    rows = build_evidence_rows(run_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    table = {
        "schema_version": EVIDENCE_TABLE_SCHEMA_VERSION,
        "source_run_dir": str(run_dir),
        "row_count": len(rows),
        "rows": rows,
    }
    json_path = output_dir / "evidence_table.json"
    csv_path = output_dir / "evidence_table.csv"
    json_path.write_text(
        json.dumps(table, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in CSV_COLUMNS})
    return {
        "schema_version": "governed_agent_bench.evidence_table_output.v1",
        "row_count": len(rows),
        "json_path": json_path.as_posix(),
        "csv_path": csv_path.as_posix(),
    }


def _row_from_record(record: RepRecord) -> dict[str, Any]:
    score = record.score
    trajectory = record.trajectory
    task = load_task(record.task_id)
    violations = score.get("violations", [])
    violation_kinds = sorted({violation["kind"] for violation in violations})
    contract_arm = contract_arm_of(task)
    return {
        "task_id": score["task_id"],
        "level": task["level"],
        "trajectory_id": score["trajectory_id"],
        "system_id": score["system_id"],
        "model_class": score["model_class"],
        "runtime_mode": score["runtime_mode"],
        "contract_arm": contract_arm,
        "cell": cell_label(contract_arm, score["runtime_mode"]),
        "load_bearing_mechanisms": ",".join(
            str(value) for value in task.get("load_bearing_mechanisms", [])
        ),
        "manifest_id": score["manifest_version"],
        "prompt_template_id": trajectory["prompt_template_id"],
        "prompt_template_hash": trajectory["prompt_template_hash"],
        "prompt_template_file_hash": trajectory.get("prompt_template_file_hash", ""),
        "scorer_version": score["scorer_version"],
        "scorer_config_hash": score["scorer_config_hash"],
        "overall_pass": score["overall_pass"],
        "metric_count": len(score["metrics"]),
        "violation_count": len(violations),
        "violation_kinds": ",".join(violation_kinds),
        "violations_json": json.dumps(
            violations,
            sort_keys=True,
            separators=(",", ":"),
        ),
        "metrics_json": json.dumps(
            score["metrics"],
            sort_keys=True,
            separators=(",", ":"),
        ),
    }
