"""Frozen HAI manifest snapshot contract."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest


MANIFEST_DIR = (
    Path(__file__).resolve().parents[2]
    / "governed_agent_bench"
    / "manifests"
)
CURRENT_SNAPSHOT_PATH = MANIFEST_DIR / "hai_0_2_0.json"
STALE_SNAPSHOT_PATH = MANIFEST_DIR / "agent_cli_contract_v1_drift.json"
STALE_BUILDER_PATH = MANIFEST_DIR / "build_stale_manifest_snapshot.py"
HAI_ENV_KEYS = (
    "HAI_RUNTIME_MODE",
    "HAI_HERMETIC",
    "HAI_STATE_DB",
    "HAI_BASE_DIR",
    "HAI_INVOCATION_CONTEXT",
)


def _load_snapshot(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_stale_builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "build_stale_manifest_snapshot",
        STALE_BUILDER_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _live_manifest_via_cli() -> dict:
    env = os.environ.copy()
    for key in HAI_ENV_KEYS:
        env.pop(key, None)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "health_agent_infra.cli",
            "capabilities",
            "--json",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_hai_manifest_snapshot_envelope_shape() -> None:
    snapshot = _load_snapshot(CURRENT_SNAPSHOT_PATH)

    assert snapshot["schema_version"] == "governed_agent_bench.manifest_snapshot.v1"
    assert snapshot["manifest_version"] == "hai_0_2_0"
    assert snapshot["generated_by"] == "uv run hai capabilities --json"
    assert re.fullmatch(r"[0-9a-f]{40}", snapshot["source_commit"])
    assert snapshot["hai_version"] == snapshot["manifest"]["hai_version"]
    assert (
        snapshot["contract_schema_version"]
        == snapshot["manifest"]["schema_version"]
        == "agent_cli_contract.v2"
    )


def test_hai_manifest_snapshot_matches_live_manifest() -> None:
    snapshot = _load_snapshot(CURRENT_SNAPSHOT_PATH)

    assert snapshot["manifest"] == _live_manifest_via_cli()


def test_hai_manifest_snapshot_generated_at_is_the_only_volatile_field() -> None:
    first = _load_snapshot(CURRENT_SNAPSHOT_PATH)
    second = _load_snapshot(CURRENT_SNAPSHOT_PATH)
    first.pop("generated_at")
    second.pop("generated_at")

    assert first == second


def test_stale_hai_manifest_snapshot_envelope_shape() -> None:
    snapshot = _load_snapshot(STALE_SNAPSHOT_PATH)

    assert snapshot["schema_version"] == "governed_agent_bench.manifest_snapshot.v1"
    assert snapshot["manifest_version"] == "agent_cli_contract_v1_drift"
    assert snapshot["generated_by"] == (
        "uv run python benchmark/governed_agent_bench/manifests/"
        "build_stale_manifest_snapshot.py"
    )
    assert snapshot["drift_role"] == "stale_manifest_for_l7"
    assert re.fullmatch(r"[0-9a-f]{40}", snapshot["source_commit"])
    assert (
        snapshot["source_manifest_path"]
        == "verification/tests/snapshots/cli_capabilities_v0_1_13.json"
    )
    assert snapshot["hai_version"] == snapshot["manifest"]["hai_version"]
    assert (
        snapshot["contract_schema_version"]
        == snapshot["manifest"]["schema_version"]
        == "agent_cli_contract.v1"
    )


def test_stale_hai_manifest_snapshot_is_v1_shaped() -> None:
    snapshot = _load_snapshot(STALE_SNAPSHOT_PATH)
    manifest = snapshot["manifest"]

    assert len(manifest["commands"]) == 67
    assert "command" in manifest["commands"][0]
    assert "mutation" in manifest["commands"][0]
    assert "name" not in manifest["commands"][0]
    assert "mutation_class" not in manifest["commands"][0]
    assert "runtime_modes" not in manifest
    assert "refusals" not in manifest


def test_stale_hai_manifest_snapshot_is_reproducible_from_historical_commit() -> None:
    snapshot = _load_snapshot(STALE_SNAPSHOT_PATH)
    builder = _load_stale_builder()

    try:
        manifest = builder.load_historical_manifest()
    except subprocess.CalledProcessError as exc:
        pytest.skip(
            "historical source commit is unavailable in this checkout; "
            f"git show exited with {exc.returncode}"
        )
    regenerated = builder.build_snapshot(
        manifest,
        generated_at=snapshot["generated_at"],
    )

    assert regenerated == snapshot
