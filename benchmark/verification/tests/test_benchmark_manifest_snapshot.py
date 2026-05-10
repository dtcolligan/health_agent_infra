"""Frozen HAI manifest snapshot contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

from health_agent_infra.cli import build_parser
from health_agent_infra.core.capabilities import build_manifest


SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[2]
    / "governed_agent_bench"
    / "manifests"
    / "hai_0_2_0.json"
)


def _load_snapshot() -> dict:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def test_hai_manifest_snapshot_envelope_shape() -> None:
    snapshot = _load_snapshot()

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
    snapshot = _load_snapshot()

    assert snapshot["manifest"] == build_manifest(build_parser())


def test_hai_manifest_snapshot_generated_at_is_the_only_volatile_field() -> None:
    first = _load_snapshot()
    second = _load_snapshot()
    first.pop("generated_at")
    second.pop("generated_at")

    assert first == second
