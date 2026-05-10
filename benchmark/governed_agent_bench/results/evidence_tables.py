"""Deterministic evidence-table construction from score artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from governed_agent_bench.harness import load_task


EVIDENCE_TABLE_SCHEMA_VERSION = "governed_agent_bench.evidence_table.v1"
CSV_COLUMNS = [
    "task_id",
    "level",
    "trajectory_id",
    "system_id",
    "model_class",
    "runtime_mode",
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

    score_paths = sorted((run_dir / "scores").glob("*.score.json"))
    if not score_paths:
        raise ValueError(f"no score files found under {run_dir / 'scores'}")
    rows = [_row_from_score(run_dir, path) for path in score_paths]
    return sorted(rows, key=lambda row: (row["task_id"], row["runtime_mode"]))


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


def _row_from_score(run_dir: Path, score_path: Path) -> dict[str, Any]:
    score = _load_json(score_path)
    trajectory_path = run_dir / "trajectories" / f"{score['trajectory_id']}.json"
    trajectory = _load_json(trajectory_path)
    _assert_score_trajectory_match(score, trajectory, score_path=score_path)
    task = load_task(score["task_id"])
    violations = score.get("violations", [])
    violation_kinds = sorted({violation["kind"] for violation in violations})
    return {
        "task_id": score["task_id"],
        "level": task["level"],
        "trajectory_id": score["trajectory_id"],
        "system_id": score["system_id"],
        "model_class": score["model_class"],
        "runtime_mode": score["runtime_mode"],
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


def _assert_score_trajectory_match(
    score: dict[str, Any],
    trajectory: dict[str, Any],
    *,
    score_path: Path,
) -> None:
    checks = {
        "trajectory_id": trajectory["trajectory_id"],
        "task_id": trajectory["task_id"],
        "system_id": trajectory["system_id"],
        "runtime_mode": trajectory["runtime_mode"],
        "model_class": trajectory["model_class"],
    }
    for key, expected in checks.items():
        if score[key] != expected:
            raise ValueError(f"{score_path}: score/trajectory mismatch for {key}")
    if score["manifest_version"] != trajectory["manifest_snapshot_id"]:
        raise ValueError(
            f"{score_path}: score manifest_version does not match trajectory"
        )


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError(f"required artifact not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
