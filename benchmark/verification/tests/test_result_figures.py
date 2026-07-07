"""Deterministic result-figure tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.baselines import run_rule_baseline_ablation  # noqa: E402
from governed_agent_bench.results import (  # noqa: E402
    FIGURE_SCHEMA_VERSION,
    write_evidence_tables,
    write_result_figures,
)


def test_result_figures_are_deterministic_svg_outputs(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    table_dir = tmp_path / "tables"
    figure_dir = tmp_path / "figures"
    run_rule_baseline_ablation(
        output_dir=run_dir,
        fixture_workspace=tmp_path / "fixtures",
    )
    write_evidence_tables(run_dir=run_dir, output_dir=table_dir)

    first = write_result_figures(
        evidence_table_path=table_dir / "evidence_table.json",
        output_dir=figure_dir,
    )
    first_svg = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(figure_dir.glob("*.svg"))
    }
    second = write_result_figures(
        evidence_table_path=table_dir / "evidence_table.json",
        output_dir=figure_dir,
    )
    second_svg = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(figure_dir.glob("*.svg"))
    }

    assert first == second
    assert first_svg == second_svg
    assert first["schema_version"] == FIGURE_SCHEMA_VERSION
    assert first["figure_count"] == 2
    assert set(first_svg) == {"pass_by_level.svg", "pass_by_runtime_mode.svg"}
    assert "full_contract" in first_svg["pass_by_runtime_mode.svg"]
    # D-48: no_validation is no longer ablated; the in-scope off modes are
    # no_runtime_enforcement and no_refusal.
    assert "no_refusal" in first_svg["pass_by_runtime_mode.svg"]
    assert "L6" in first_svg["pass_by_level.svg"]

    manifest = json.loads(
        (figure_dir / "figures_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest == first
