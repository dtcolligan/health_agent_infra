"""Evidence-table generation tests."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.baselines import run_rule_baseline_ablation  # noqa: E402
from governed_agent_bench.results import (  # noqa: E402
    EVIDENCE_TABLE_SCHEMA_VERSION,
    build_evidence_rows,
    write_evidence_tables,
)


def test_evidence_tables_normalize_rule_ablation_scores(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    report = run_rule_baseline_ablation(
        output_dir=run_dir,
        fixture_workspace=tmp_path / "fixtures",
    )

    rows = build_evidence_rows(run_dir)

    assert len(rows) == report["run_count"]
    assert {row["runtime_mode"] for row in rows} >= {
        "full_contract",
        "no_validation",
        "no_agent_safe",
        "no_proposal_gate",
        "no_refusal",
        "no_audit_chain",
    }
    for row in rows:
        assert row["manifest_id"]
        assert row["runtime_mode"]
        assert row["scorer_config_hash"]
        assert len(row["prompt_template_hash"]) == 64
        assert len(row["prompt_template_file_hash"]) == 64


def test_write_evidence_tables_outputs_deterministic_json_and_csv(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run"
    output_dir = tmp_path / "tables"
    run_rule_baseline_ablation(
        output_dir=run_dir,
        fixture_workspace=tmp_path / "fixtures",
    )

    first = write_evidence_tables(run_dir=run_dir, output_dir=output_dir)
    first_json = (output_dir / "evidence_table.json").read_text(encoding="utf-8")
    second = write_evidence_tables(run_dir=run_dir, output_dir=output_dir)
    second_json = (output_dir / "evidence_table.json").read_text(encoding="utf-8")

    assert first == second
    assert first_json == second_json

    table = json.loads(first_json)
    assert table["schema_version"] == EVIDENCE_TABLE_SCHEMA_VERSION
    assert table["row_count"] == first["row_count"]
    assert first["json_path"].endswith("evidence_table.json")
    assert first["csv_path"].endswith("evidence_table.csv")

    with (output_dir / "evidence_table.csv").open(
        encoding="utf-8",
        newline="",
    ) as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == table["row_count"]
    assert {
        "task_id",
        "manifest_id",
        "runtime_mode",
        "prompt_template_hash",
        "scorer_config_hash",
    }.issubset(csv_rows[0])
