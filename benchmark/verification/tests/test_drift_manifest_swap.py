"""Direct contract pins for L7 stale-manifest refresh behavior."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.baselines import run_rule_baseline  # noqa: E402
from governed_agent_bench.harness import (  # noqa: E402
    load_json,
    load_manifest_snapshot,
)

# Private helper imports intentionally pin the drift-swap contract.
from governed_agent_bench.harness.core import (  # noqa: E402
    _manifest_id,
    _refreshed_manifest_snapshot,
)


DRIFT_TASK_IDS = (
    "gab_l7_drift",
    "gab_l7_drift",
)
DRIFT_MANIFEST_ID = "agent_cli_contract_v1_drift"
CURRENT_MANIFEST_ID = "hai_0_2_0"


def _task_path(task_id: str) -> Path:
    return (
        BENCHMARK_ROOT
        / "governed_agent_bench"
        / "tasks"
        / "l7"
        / f"{task_id}.json"
    )


def _manifest_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    payload = snapshot.get("manifest", snapshot)
    assert isinstance(payload, dict)
    return payload


@pytest.mark.parametrize("task_id", DRIFT_TASK_IDS)
def test_drift_l7_tasks_declare_drift_manifest_ref(task_id: str) -> None:
    task = load_json(_task_path(task_id))

    assert task["allowed_context"]["manifest_ref"] == DRIFT_MANIFEST_ID


@pytest.mark.parametrize("task_id", DRIFT_TASK_IDS)
def test_manifest_id_resolves_drift_for_l7_drift_tasks(task_id: str) -> None:
    task = load_json(_task_path(task_id))

    assert _manifest_id(task) == DRIFT_MANIFEST_ID


def test_load_manifest_snapshot_returns_drift_snapshot() -> None:
    drift_snapshot = load_manifest_snapshot(DRIFT_MANIFEST_ID)
    current_snapshot = load_manifest_snapshot(CURRENT_MANIFEST_ID)

    assert drift_snapshot != current_snapshot
    assert drift_snapshot["contract_schema_version"] == "agent_cli_contract.v1"
    assert current_snapshot["contract_schema_version"] == "agent_cli_contract.v2"


def test_drift_task_trajectory_carries_drift_manifest_snapshot_id(
    tmp_path: Path,
) -> None:
    report = run_rule_baseline(
        output_dir=tmp_path / "out",
        fixture_workspace=tmp_path / "fixtures",
        task_ids=["gab_l7_drift"],
    )

    row = report["tasks"][0]
    trajectory_path = tmp_path / "out" / row["trajectory_path"]
    trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))

    assert trajectory["task_id"] == "gab_l7_drift"
    assert trajectory["manifest_snapshot_id"] == DRIFT_MANIFEST_ID


def test_refreshed_manifest_snapshot_flips_drift_to_current() -> None:
    drift_snapshot = load_manifest_snapshot(DRIFT_MANIFEST_ID)
    current_snapshot = load_manifest_snapshot(CURRENT_MANIFEST_ID)
    current_payload = _manifest_payload(current_snapshot)

    refreshed = _refreshed_manifest_snapshot(
        "hai capabilities",
        json.dumps(current_payload),
    )

    assert refreshed is not None
    assert refreshed != drift_snapshot
    assert set(refreshed) == set(current_payload)
    assert refreshed["schema_version"] == current_payload["schema_version"]
    assert refreshed["schema_version"] == "agent_cli_contract.v2"
