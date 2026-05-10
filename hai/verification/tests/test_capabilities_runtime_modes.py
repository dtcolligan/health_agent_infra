"""WP-MAN-004: runtime-mode taxonomy in capabilities manifest."""

from __future__ import annotations

import json
from pathlib import Path

from health_agent_infra.cli import build_parser
from health_agent_infra.core.capabilities import build_manifest
from health_agent_infra.core.runtime_mode import (
    MECHANISMS_OFF_BY_MODE,
    SUPPORTED_RUNTIME_MODES,
)


_REPO_ROOT = Path(__file__).resolve().parents[3]
_TRAJECTORY_SCHEMA = (
    _REPO_ROOT / "benchmark" / "governed_agent_bench" / "schema"
    / "trajectory.schema.json"
)


def _runtime_modes() -> list[dict[str, object]]:
    return build_manifest(build_parser())["runtime_modes"]


def test_runtime_modes_match_runtime_mode_accessor() -> None:
    rows = _runtime_modes()

    assert [row["name"] for row in rows] == list(SUPPORTED_RUNTIME_MODES)
    by_name = {row["name"]: row for row in rows}
    for mode in SUPPORTED_RUNTIME_MODES:
        assert by_name[mode]["mechanisms_off"] == list(
            MECHANISMS_OFF_BY_MODE[mode]
        )
        assert isinstance(by_name[mode]["use_case"], str)
        assert by_name[mode]["use_case"]


def test_runtime_modes_match_trajectory_schema_enum() -> None:
    schema = json.loads(_TRAJECTORY_SCHEMA.read_text(encoding="utf-8"))
    trajectory_enum = schema["properties"]["runtime_mode"]["enum"]

    assert [row["name"] for row in _runtime_modes()] == trajectory_enum
