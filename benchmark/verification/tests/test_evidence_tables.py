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
    # D-48: the only in-scope runtime modes are full_contract plus the two 2x2
    # off modes, no_runtime_enforcement (mutation gate) and no_refusal.
    assert {row["runtime_mode"] for row in rows} == {
        "full_contract",
        "no_runtime_enforcement",
        "no_refusal",
    }
    for row in rows:
        assert row["manifest_id"]
        assert row["runtime_mode"]
        assert row["scorer_config_hash"]
        assert len(row["prompt_template_hash"]) == 64
        assert len(row["prompt_template_file_hash"]) == 64
        assert row["contract_arm"] in {"told", "untold"}
        assert row["cell"] in {"A", "B", "C", "D", "sanity_floor"}

    # Cell labelling is derived from contract_arm x runtime_mode. The clinical
    # refusal constraint (off = no_refusal) is the constraint whose off mode is
    # NOT the all-off floor, so it populates all four A/B/C/D cells in the global
    # table; no_runtime_enforcement is the standalone sanity floor.
    by_cell = {(r["task_id"], r["runtime_mode"]): r["cell"] for r in rows}
    assert by_cell[("gab_l6_refusal_told", "full_contract")] == "A"
    assert by_cell[("gab_l6_refusal_told", "no_refusal")] == "B"
    assert by_cell[("gab_l6_refusal_untold", "full_contract")] == "C"
    assert by_cell[("gab_l6_refusal_untold", "no_refusal")] == "D"
    assert (
        by_cell[("gab_l6_agentsafe_untold", "no_runtime_enforcement")]
        == "sanity_floor"
    )


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
