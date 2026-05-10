"""W-30 — Capabilities-manifest schema-freeze regression test (test-only).

Per AGENTS.md "Settled Decisions" v0.1.12 CP2 + post-v0.1.13
CP-W30-SPLIT: the actual schema freeze ships at v0.2.3, but the
regression-test scaffold lands earlier (v0.1.17) so v0.2.x cycles can
build against a stable contract.

This test:
- Pins the structural keys of ``hai capabilities --json`` against an
  inline schema (top-level + per-command + per-flag).
- Asserts every required key is present with the expected type.
- Does NOT pin field VALUES — that's
  ``test_cli_parser_capabilities_regression.py``'s job.

Failure mode: a future cycle adds a per-command field without updating
this schema, the test fails, the cycle author updates the schema in
lockstep with the runtime change.

The schema is defined inline (not a separate snapshot file) so the
contract lives next to the test asserting it.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from typing import Any

from health_agent_infra.cli import main as cli_main


# ---------------------------------------------------------------------------
# Inline schema definitions (the contract).
# v0.1.17 W-30: regression-test scaffold; v0.2.3 will turn this into
# the actual freeze (no further additions without an explicit cycle
# proposal).
# ---------------------------------------------------------------------------


_TOP_LEVEL_REQUIRED: dict[str, type] = {
    "hai_version": str,
    "schema_version": str,
    "generated_by": str,
    "commands": list,
    "domain_proposal_contracts": dict,
    "refusals": list,
    "runtime_modes": list,
}


_COMMAND_REQUIRED: dict[str, Any] = {
    "command": str,
    "description": str,
    "flags": list,
    "mutation": str,
    "agent_safe": bool,
    "idempotent": str,
    "json_output": str,         # vocabulary: "default" | "json_only" | "off"
    "exit_codes": list,
}


# Optional per-command keys: present on some commands but not all.
_COMMAND_OPTIONAL: dict[str, Any] = {
    "output_schema": dict,
    "preconditions": list,
}


_FLAG_REQUIRED: dict[str, type] = {
    "name": str,
    "action": str,
    "help": (str, type(None)),       # may be None for flags without --help text
    "required": bool,
    "positional": bool,
    "nargs": (str, int, type(None)),
    "type": (str, type(None)),
    "default": (str, int, float, bool, list, dict, type(None)),
    "choices": (list, type(None)),
    "aliases": list,
}


# Optional keys that MAY appear on a flag (not all flags carry them).
# Asserting presence-when-present rather than required-everywhere.
_FLAG_OPTIONAL: dict[str, type] = {
    "choice_metadata": dict,        # only on flags with annotate_choice_metadata
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_manifest() -> dict[str, Any]:
    """Load the live manifest by invoking ``hai capabilities --json``."""

    out_buf = io.StringIO()
    with redirect_stdout(out_buf):
        rc = cli_main(["capabilities", "--json"])
    assert rc == 0, "hai capabilities --json must exit OK"
    return json.loads(out_buf.getvalue())


def _check_keys(
    obj: dict[str, Any],
    required: dict[str, type],
    label: str,
) -> list[str]:
    """Return error strings for missing keys / wrong types."""

    errors: list[str] = []
    for key, expected_type in required.items():
        if key not in obj:
            errors.append(f"{label}: missing required key {key!r}")
            continue
        value = obj[key]
        if not isinstance(value, expected_type):
            type_name = (
                expected_type.__name__
                if isinstance(expected_type, type)
                else " | ".join(t.__name__ for t in expected_type)
            )
            errors.append(
                f"{label}: key {key!r} expected {type_name}, "
                f"got {type(value).__name__}"
            )
    return errors


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_top_level_schema():
    """Manifest top-level has the required keys with the right types."""

    manifest = _load_manifest()
    errors = _check_keys(manifest, _TOP_LEVEL_REQUIRED, "top")
    assert not errors, "Top-level schema breach:\n" + "\n".join(errors)


def test_every_command_has_required_keys():
    """Each entry in ``commands[]`` has all required per-command keys."""

    manifest = _load_manifest()
    all_errors: list[str] = []
    for cmd in manifest["commands"]:
        label = f"commands[{cmd.get('command', '<no-command-key>')}]"
        all_errors.extend(_check_keys(cmd, _COMMAND_REQUIRED, label))
    assert not all_errors, (
        f"Per-command schema breach in {len(all_errors)} cases:\n"
        + "\n".join(all_errors[:20])
        + (f"\n  ... ({len(all_errors) - 20} more)" if len(all_errors) > 20 else "")
    )


def test_every_flag_has_required_keys():
    """Each entry in ``commands[].flags[]`` has all required per-flag keys."""

    manifest = _load_manifest()
    all_errors: list[str] = []
    for cmd in manifest["commands"]:
        cmd_label = cmd.get("command", "<no-command-key>")
        for flag in cmd["flags"]:
            label = f"{cmd_label} flag[{flag.get('name', '<no-name-key>')}]"
            all_errors.extend(_check_keys(flag, _FLAG_REQUIRED, label))
    assert not all_errors, (
        f"Per-flag schema breach in {len(all_errors)} cases:\n"
        + "\n".join(all_errors[:20])
        + (f"\n  ... ({len(all_errors) - 20} more)" if len(all_errors) > 20 else "")
    )


def test_optional_flag_keys_are_well_typed_when_present():
    """Optional keys (e.g. ``choice_metadata``) carry the expected type
    whenever they appear. Absent is acceptable; present-but-wrong-type
    is a contract breach."""

    manifest = _load_manifest()
    all_errors: list[str] = []
    for cmd in manifest["commands"]:
        cmd_label = cmd.get("command", "<no-command-key>")
        for flag in cmd["flags"]:
            for key, expected_type in _FLAG_OPTIONAL.items():
                if key not in flag:
                    continue
                value = flag[key]
                if not isinstance(value, expected_type):
                    label = f"{cmd_label} flag[{flag.get('name')}].{key}"
                    type_name = (
                        expected_type.__name__
                        if isinstance(expected_type, type)
                        else " | ".join(t.__name__ for t in expected_type)
                    )
                    all_errors.append(
                        f"{label}: expected {type_name}, "
                        f"got {type(value).__name__}"
                    )
    assert not all_errors, (
        "Optional-key schema breach:\n" + "\n".join(all_errors)
    )


def test_no_unexpected_top_level_keys():
    """Catches additions to the top-level shape that aren't in the
    schema yet. Failure mode: cycle author adds a top-level field
    without updating ``_TOP_LEVEL_REQUIRED``."""

    manifest = _load_manifest()
    extras = set(manifest.keys()) - set(_TOP_LEVEL_REQUIRED.keys())
    assert not extras, (
        f"Manifest carries unexpected top-level keys: {sorted(extras)}. "
        f"Add to _TOP_LEVEL_REQUIRED in this file (W-30) to ratify."
    )


def test_no_unexpected_per_command_keys():
    """Catches additions to the per-command shape."""

    manifest = _load_manifest()
    expected_keys = set(_COMMAND_REQUIRED.keys()) | set(_COMMAND_OPTIONAL.keys())
    all_extras: set[str] = set()
    for cmd in manifest["commands"]:
        all_extras.update(set(cmd.keys()) - expected_keys)
    assert not all_extras, (
        f"Commands carry unexpected keys: {sorted(all_extras)}. "
        f"Add to _COMMAND_REQUIRED or _COMMAND_OPTIONAL in this file "
        f"(W-30) to ratify."
    )


def test_optional_command_keys_are_well_typed_when_present():
    """Optional per-command keys (e.g. ``output_schema``,
    ``preconditions``) carry the expected type whenever they appear."""

    manifest = _load_manifest()
    all_errors: list[str] = []
    for cmd in manifest["commands"]:
        cmd_label = cmd.get("command", "<no-command-key>")
        for key, expected_type in _COMMAND_OPTIONAL.items():
            if key not in cmd:
                continue
            value = cmd[key]
            if not isinstance(value, expected_type):
                type_name = (
                    expected_type.__name__
                    if isinstance(expected_type, type)
                    else " | ".join(t.__name__ for t in expected_type)
                )
                all_errors.append(
                    f"{cmd_label}.{key}: expected {type_name}, "
                    f"got {type(value).__name__}"
                )
    assert not all_errors, (
        "Optional per-command schema breach:\n" + "\n".join(all_errors)
    )


def test_no_unexpected_per_flag_keys():
    """Catches additions to the per-flag shape."""

    manifest = _load_manifest()
    expected_keys = set(_FLAG_REQUIRED.keys()) | set(_FLAG_OPTIONAL.keys())
    all_extras: set[str] = set()
    for cmd in manifest["commands"]:
        for flag in cmd["flags"]:
            all_extras.update(set(flag.keys()) - expected_keys)
    assert not all_extras, (
        f"Flags carry unexpected keys: {sorted(all_extras)}. "
        f"Add to _FLAG_REQUIRED or _FLAG_OPTIONAL in this file (W-30) to ratify."
    )
