"""Offline reproducibility runner tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BENCHMARK_ROOT.parent
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench import reproduce_offline  # noqa: E402
from governed_agent_bench.reproduce_offline import (  # noqa: E402
    REPRO_SCHEMA_VERSION,
    run_offline_repro,
)


SMOKE_TASKS = [
    "gab_l1_doctor_status_route",
    "gab_l2_empty_today_user_input",
]


def _static_matrix(*, all_isolated: bool = True) -> dict[str, Any]:
    return {
        "schema_version": "governed_agent_bench.isolation_matrix.v1",
        "evidence_tier": "static_oracle_pairs",
        "row_count": 1,
        "all_isolated": all_isolated,
        "rows": [],
    }


def _live_matrix(*, all_live_isolated: bool = True) -> dict[str, Any]:
    return {
        "schema_version": "governed_agent_bench.live_isolation.v1",
        "evidence_tier": "live_runtime_probe",
        "live_count": 1,
        "all_live_isolated": all_live_isolated,
        "live_labels": ["validation"],
        "rows": [],
    }


def _mock_isolation_builders(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        reproduce_offline, "build_isolation_matrix", lambda: _static_matrix()
    )
    monkeypatch.setattr(
        reproduce_offline,
        "build_live_isolation_matrix",
        lambda workspace: _live_matrix(),
    )


def test_offline_repro_writes_complete_smoke_package(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _mock_isolation_builders(monkeypatch)

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

    out_dir = tmp_path / "out"
    for path in manifest["artifacts"].values():
        assert not Path(path).is_absolute(), path
        assert (out_dir / path).exists(), path
    recorded = json.loads(
        (tmp_path / "out" / "offline_repro_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert recorded == manifest


def test_offline_repro_default_runs_full_evidence(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    _mock_isolation_builders(monkeypatch)

    manifest = run_offline_repro(
        output_dir=tmp_path / "out",
        fixture_workspace=tmp_path / "fixtures",
        task_ids=SMOKE_TASKS,
    )

    out_dir = tmp_path / "out"
    for artifact_key in ("isolation_matrix", "live_isolation_matrix"):
        path = Path(manifest["artifacts"][artifact_key])
        assert not path.is_absolute()
        assert (out_dir / path).exists()

    assert manifest["isolation_matrix"] == {
        "schema_version": "governed_agent_bench.isolation_matrix.v1",
        "evidence_tier": "static_oracle_pairs",
        "row_count": 1,
        "all_isolated": True,
    }
    assert manifest["live_isolation"] == {
        "schema_version": "governed_agent_bench.live_isolation.v1",
        "evidence_tier": "live_runtime_probe",
        "live_count": 1,
        "all_live_isolated": True,
        "live_labels": ["validation"],
        "skipped": False,
    }


def test_offline_repro_skip_live_isolation_opts_out(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        reproduce_offline, "build_isolation_matrix", lambda: _static_matrix()
    )

    def fail_live_isolation(workspace: Path) -> dict[str, Any]:
        raise AssertionError(f"live isolation should have been skipped: {workspace}")

    monkeypatch.setattr(
        reproduce_offline, "build_live_isolation_matrix", fail_live_isolation
    )

    manifest = run_offline_repro(
        output_dir=tmp_path / "out",
        fixture_workspace=tmp_path / "fixtures",
        task_ids=SMOKE_TASKS,
        skip_live_isolation=True,
    )

    assert "isolation_matrix" in manifest["artifacts"]
    assert "live_isolation_matrix" not in manifest["artifacts"]
    assert manifest["live_isolation"] == {"skipped": True, "reason": "skip_flag"}


def test_offline_repro_non_isolation_exits_one(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(
        reproduce_offline,
        "build_isolation_matrix",
        lambda: _static_matrix(all_isolated=False),
    )
    monkeypatch.setattr(
        reproduce_offline,
        "build_live_isolation_matrix",
        lambda workspace: _live_matrix(),
    )

    output_dir = tmp_path / "out"
    exit_code = reproduce_offline.main([
        "--output-dir",
        str(output_dir),
        "--task-id",
        "gab_l1_doctor_status_route",
    ])

    assert exit_code == 1
    recorded = json.loads(
        (output_dir / "offline_repro_manifest.json").read_text(encoding="utf-8")
    )
    assert recorded["isolation_matrix"]["all_isolated"] is False
    assert recorded["live_isolation"]["all_live_isolated"] is True


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
            "--skip-live-isolation",
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
    assert manifest["live_isolation"] == {"skipped": True, "reason": "skip_flag"}
    assert (output_dir / "offline_repro_manifest.json").exists()
