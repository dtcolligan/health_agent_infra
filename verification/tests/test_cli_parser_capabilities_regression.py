"""W-29-prep (v0.1.13) — CLI parser + capabilities byte-stability regression.

This test scaffold exists to catch v0.1.14 W-29's mechanical cli.py
split from inadvertently altering the agent-CLI contract. The split
will rearrange the file (1 main + 1 shared + 11 handler-group
modules), but every subcommand's parser shape, every flag, every
contract annotation must stay byte-identical at the manifest level.

What we pin:

  1. **Capabilities manifest structural equality.** `hai capabilities
     --json` (excluding the volatile `hai_version` field) must match
     the snapshot at
     `verification/tests/snapshots/cli_capabilities_v0_1_13.json`.

  2. **Parser tree shape.** A deterministic textual summary of the
     parser tree (command names + flag names per leaf, no help text
     since argparse word-wrapping varies) must match
     `verification/tests/snapshots/cli_help_tree_v0_1_13.txt`.

The snapshot baseline was frozen AFTER v0.1.13's intentional CLI
surface changes landed (W-AB `--human` mode + W-AE `--deep` doctor
extension) per F-PLAN-11 sequencing. Until v0.1.14 W-29 ships, drift
in either snapshot signals an unintended surface change and is a
merge-blocking signal.

When you intentionally extend the CLI surface (post-W-29 cycles):
regenerate the snapshots in lockstep with the change.

  ```bash
  # Regenerate after intentional surface changes (with care):
  uv run hai capabilities --json > \\
      verification/tests/snapshots/cli_capabilities_v0_1_13.json
  uv run python -m verification.tests.snapshots.regen_help_tree
  ```
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from health_agent_infra.cli import build_parser
from health_agent_infra.core.capabilities import build_manifest


_SNAPSHOTS = Path(__file__).parent / "snapshots"
_CAPABILITIES_SNAPSHOT = _SNAPSHOTS / "cli_capabilities_v0_1_13.json"
_HELP_TREE_SNAPSHOT = _SNAPSHOTS / "cli_help_tree_v0_1_13.txt"


# Fields excluded from snapshot comparison. `hai_version` bumps every
# release; pinning the version here would force a snapshot update on
# every release without catching anything useful (the W-29 split won't
# touch the version).
_VOLATILE_FIELDS: frozenset[str] = frozenset({"hai_version"})


def _normalise_manifest(manifest: dict) -> dict:
    """Strip volatile fields so the comparison reflects shape, not version."""

    return {k: v for k, v in manifest.items() if k not in _VOLATILE_FIELDS}


def _parser_tree(parser: argparse.ArgumentParser) -> str:
    """Return a deterministic textual summary of the parser tree.

    Format: one line per leaf command; each line is `<command path>:
    <sorted flag list>`. Help text is intentionally omitted because
    argparse line-wraps it differently across Python versions and
    terminal widths — that's noise, not signal, for the W-29
    regression contract.
    """

    lines: list[str] = []
    _walk_subcommands(parser, "hai", lines)
    return "\n".join(sorted(lines)) + "\n"


def _walk_subcommands(
    parser: argparse.ArgumentParser,
    path: str,
    out: list[str],
) -> None:
    sub_actions = [
        a for a in parser._actions  # noqa: SLF001
        if isinstance(a, argparse._SubParsersAction)  # noqa: SLF001
    ]
    if not sub_actions:
        # Leaf — record this command and its flags.
        flags: list[str] = []
        for action in parser._actions:  # noqa: SLF001
            if not action.option_strings:
                continue
            for opt in action.option_strings:
                if opt.startswith("--"):
                    flags.append(opt)
        out.append(f"{path}: {','.join(sorted(set(flags)))}")
        return
    for sub_action in sub_actions:
        for name, sub_parser in sub_action.choices.items():
            _walk_subcommands(sub_parser, f"{path} {name}", out)


# ---------------------------------------------------------------------------
# Capabilities manifest stability
# ---------------------------------------------------------------------------


def test_capabilities_manifest_baseline_snapshot_exists():
    """Snapshot baseline must exist on disk; without it the test surface
    is meaningless. (W-29-prep deliverable.)"""

    assert _CAPABILITIES_SNAPSHOT.exists(), (
        f"missing snapshot at {_CAPABILITIES_SNAPSHOT}; regenerate via "
        f"`uv run hai capabilities --json > {_CAPABILITIES_SNAPSHOT}`"
    )


def test_capabilities_manifest_matches_snapshot_modulo_volatile_fields():
    """`hai capabilities --json` matches the v0.1.13-frozen baseline."""

    current = build_manifest(build_parser())
    snapshot = json.loads(_CAPABILITIES_SNAPSHOT.read_text())

    current_n = _normalise_manifest(current)
    snapshot_n = _normalise_manifest(snapshot)

    if current_n != snapshot_n:
        # Diagnostic prose for v0.1.14 W-29 / future-cycle authors: name
        # the divergence axes so the failure points at the right place
        # instead of dumping 140KB of JSON.
        added = set(c["command"] for c in current_n["commands"]) - set(
            c["command"] for c in snapshot_n["commands"]
        )
        removed = set(c["command"] for c in snapshot_n["commands"]) - set(
            c["command"] for c in current_n["commands"]
        )
        msg = ["capabilities manifest drift vs snapshot:"]
        if added:
            msg.append(f"  added commands: {sorted(added)}")
        if removed:
            msg.append(f"  removed commands: {sorted(removed)}")
        if not (added or removed):
            msg.append(
                "  no command-set drift — flags/contract annotations differ. "
                "Re-run with current_n vs snapshot_n manually to find the "
                "diverging row."
            )
        msg.append(
            "  if intentional, regenerate: "
            "`uv run hai capabilities --json > "
            f"{_CAPABILITIES_SNAPSHOT}`"
        )
        pytest.fail("\n".join(msg))


# ---------------------------------------------------------------------------
# Parser tree shape stability
# ---------------------------------------------------------------------------


def test_parser_tree_baseline_snapshot_exists():
    assert _HELP_TREE_SNAPSHOT.exists(), (
        f"missing snapshot at {_HELP_TREE_SNAPSHOT}; regenerate via the "
        f"helper described in the test module docstring"
    )


def test_parser_tree_matches_snapshot():
    """Parser shape (subcommand paths + flag names) is byte-stable.

    This is the regression that v0.1.14 W-29 (cli.py mechanical split)
    must not violate. The snapshot was frozen AFTER v0.1.13's
    intentional surface changes (W-AB + W-AE) landed.
    """

    current = _parser_tree(build_parser())
    snapshot = _HELP_TREE_SNAPSHOT.read_text()
    if current != snapshot:
        # Find the diverging lines for a useful diagnostic.
        cur_lines = set(current.splitlines())
        snap_lines = set(snapshot.splitlines())
        added = sorted(cur_lines - snap_lines)
        removed = sorted(snap_lines - cur_lines)
        msg = ["parser tree drift vs snapshot:"]
        if added:
            msg.append(f"  new/changed lines (cur): {added[:5]}")
        if removed:
            msg.append(f"  missing lines (snap): {removed[:5]}")
        msg.append(
            f"  if intentional, regenerate {_HELP_TREE_SNAPSHOT}"
        )
        pytest.fail("\n".join(msg))


# ---------------------------------------------------------------------------
# Sanity checks on the snapshot itself
# ---------------------------------------------------------------------------


def test_snapshot_command_count_is_at_least_v0_1_12_baseline():
    """v0.1.12 ship had 56 leaf commands. v0.1.13 keeps that surface or
    grows it (W-AB/W-AE add flags, not commands; intentional command
    additions in later cycles must regenerate the snapshot)."""

    snapshot = json.loads(_CAPABILITIES_SNAPSHOT.read_text())
    assert len(snapshot["commands"]) >= 56
