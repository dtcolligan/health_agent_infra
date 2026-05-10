"""Offline reproducibility runner tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BENCHMARK_ROOT.parent
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.reproduce_offline import (  # noqa: E402
    REPRO_SCHEMA_VERSION,
    run_offline_repro,
)


SMOKE_TASKS = [
    "gab_l1_doctor_status_route",
    "gab_l2_empty_today_user_input",
]


def test_offline_repro_writes_complete_smoke_package(tmp_path: Path) -> None:
    manifest = run_offline_repro(
        output_dir=tmp_path / "out",
        fixture_workspace=tmp_path / "fixtures",
        task_ids=SMOKE_TASKS,
    )

    assert manifest["schema_version"] == REPRO_SCHEMA_VERSION
    assert manifest["model_calls"] is False
    assert manifest["uses_private_data"] is False
    assert manifest["task_ids"] == SMOKE_TASKS
    assert manifest["row_count"] == 3
    assert set(manifest["runtime_modes"]) == {"full_contract", "no_validation"}

    for path in manifest["artifacts"].values():
        assert Path(path).exists(), path
    recorded = json.loads(
        (tmp_path / "out" / "offline_repro_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert recorded == manifest


def test_offline_repro_cli_prints_manifest(tmp_path: Path) -> None:
    output_dir = tmp_path / "cli_out"
    result = subprocess.run(
        [
            sys.executable,
            "benchmark/governed_agent_bench/reproduce_offline.py",
            "--output-dir",
            str(output_dir),
            "--task-id",
            "gab_l1_doctor_status_route",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    manifest = json.loads(result.stdout)
    assert manifest["schema_version"] == REPRO_SCHEMA_VERSION
    assert manifest["model_calls"] is False
    assert manifest["row_count"] == 1
    assert (output_dir / "offline_repro_manifest.json").exists()
