"""Contract tests for the manifest-level exit-code taxonomy."""

from __future__ import annotations

from health_agent_infra.cli import build_parser
from health_agent_infra.core.capabilities import build_manifest
from health_agent_infra.core.capabilities.walker import (
    ALLOWED_EXIT_CODES,
    EXIT_CODE_ORDER,
)


def test_manifest_exit_codes_match_runtime_vocabulary() -> None:
    manifest = build_manifest(build_parser())

    assert list(manifest["exit_codes"]) == list(EXIT_CODE_ORDER)
    assert set(manifest["exit_codes"]) == ALLOWED_EXIT_CODES
    assert all(manifest["exit_codes"].values())


def test_every_command_exit_code_is_enumerated() -> None:
    manifest = build_manifest(build_parser())
    allowed = set(manifest["exit_codes"])

    for command in manifest["commands"]:
        for code in command["exit_codes"]:
            assert code in allowed, f"{command['command']}: {code}"
