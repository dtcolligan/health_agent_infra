"""Contract tests for the manifest-level mutation-class taxonomy."""

from __future__ import annotations

from health_agent_infra.cli import build_parser
from health_agent_infra.core.capabilities import build_manifest
from health_agent_infra.core.capabilities.walker import MUTATION_CLASSES


def test_manifest_mutation_classes_match_runtime_vocabulary() -> None:
    manifest = build_manifest(build_parser())

    entries = manifest["mutation_classes"]
    names = [entry["name"] for entry in entries]

    assert names == sorted(MUTATION_CLASSES)
    assert len(names) == len(set(names))
    assert all(entry["description"] for entry in entries)


def test_every_command_mutation_class_is_enumerated() -> None:
    manifest = build_manifest(build_parser())
    allowed = {entry["name"] for entry in manifest["mutation_classes"]}

    for command in manifest["commands"]:
        assert command["mutation_class"] in allowed, command["name"]


def test_manifest_rows_do_not_emit_legacy_mutation_key() -> None:
    manifest = build_manifest(build_parser())

    for command in manifest["commands"]:
        assert "mutation" not in command, command["name"]


def test_manifest_rows_do_not_emit_legacy_command_key() -> None:
    manifest = build_manifest(build_parser())

    for command in manifest["commands"]:
        assert "command" not in command, command["name"]
