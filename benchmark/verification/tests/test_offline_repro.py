"""Offline reproducibility runner checks for the sharp pipeline (D-37).

The reproduce pipeline is rule-baseline ablation -> evidence tables -> figures
-> error taxonomy. The positive-attribution apparatus (isolation matrices,
adversarial summary) was retired with the specify-vs-enforce reframe.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench import reproduce_offline  # noqa: E402

REPO_ROOT = BENCHMARK_ROOT.parents[0]

_EXPECTED_ARTIFACTS = {
    "rule_baseline_ablation_summary",
    "evidence_table_json",
    "evidence_table_csv",
    "figures_manifest",
    "error_taxonomy",
    "cell_contrasts",
}


def test_offline_repro_writes_sharp_manifest(tmp_path: Path) -> None:
    manifest = reproduce_offline.run_offline_repro(output_dir=tmp_path / "out")

    assert manifest["schema_version"] == reproduce_offline.REPRO_SCHEMA_VERSION
    assert manifest["model_calls"] is False
    assert manifest["uses_private_data"] is False
    assert set(manifest["artifacts"]) == _EXPECTED_ARTIFACTS
    for retired in ("isolation_matrix", "live_isolation", "adversarial_summary"):
        assert retired not in manifest
    assert manifest["row_count"] >= 1
    assert manifest["figure_count"] >= 1
    for rel in manifest["artifacts"].values():
        assert (tmp_path / "out" / rel).exists()


def test_offline_repro_exit_code_zero_on_complete_run(tmp_path: Path) -> None:
    manifest = reproduce_offline.run_offline_repro(output_dir=tmp_path / "out")
    assert reproduce_offline._exit_code_for_manifest(manifest) == 0


def test_offline_repro_exit_code_one_on_empty() -> None:
    assert reproduce_offline._exit_code_for_manifest(
        {"row_count": 0, "figure_count": 0}
    ) == 1


def test_offline_repro_cli_prints_manifest(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "benchmark/governed_agent_bench/reproduce_offline.py",
            "--output-dir",
            str(tmp_path / "cli"),
        ],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": "benchmark", "PATH": os.environ["PATH"]},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    printed = json.loads(result.stdout)
    assert printed["schema_version"] == reproduce_offline.REPRO_SCHEMA_VERSION
    assert set(printed["artifacts"]) == _EXPECTED_ARTIFACTS
