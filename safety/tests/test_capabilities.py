"""Phase 2 — agent CLI contract manifest.

Contracts pinned:

  1. Every leaf subcommand carries a full annotation (mutation,
     idempotency, JSON output, agent_safe, at least one exit code).
     A new subcommand without annotations fails this test rather than
     silently shipping with a NULL-shaped contract row.

  2. The manifest is deterministic — walking twice produces
     byte-equal JSON. The committed contract doc can never drift from
     the code because it's regenerated from the same manifest.

  3. The manifest schema stays stable: known keys exist on every row,
     values come from the allowed enums.

  4. ``hai capabilities`` exits cleanly and emits a parseable manifest
     in JSON and markdown.

  5. Bad annotations fail at CLI-construction time — not at runtime —
     so a typo in an enum value is a merge-blocking error.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pytest

from health_agent_infra.cli import build_parser
from health_agent_infra.core.capabilities import (
    IDEMPOTENCY,
    JSON_OUTPUT_MODES,
    MUTATION_CLASSES,
    ContractAnnotationError,
    annotate_contract,
    build_manifest,
    walk_parser,
)
from health_agent_infra.core.capabilities.walker import (
    ALLOWED_EXIT_CODES,
    SCHEMA_VERSION,
    unannotated_commands,
)
from health_agent_infra.core.capabilities.render import render_markdown


# ---------------------------------------------------------------------------
# Coverage
# ---------------------------------------------------------------------------


def test_every_subcommand_is_annotated():
    """Every leaf subcommand must have full contract annotations. A new
    subcommand without annotations fails here — merge-blocking by design."""

    parser = build_parser()
    missing = unannotated_commands(parser)
    assert not missing, (
        f"subcommands missing contract annotations: {missing}. "
        "Add an `annotate_contract(...)` call after "
        "`subparser.set_defaults(func=...)` in cli.py."
    )


def test_manifest_has_at_least_one_command():
    """Paranoia check — the walker should find real commands, not an
    empty list from a bad argparse traversal."""

    manifest = build_manifest(build_parser())
    assert len(manifest["commands"]) > 0


def test_manifest_includes_expected_commands():
    """Spot-check that the headline audit-chain commands all appear —
    these are the commands agents will invoke most and their absence
    would signal a broken walker, not a legitimate contract state."""

    commands = {row["command"] for row in walk_parser(build_parser())}
    for expected in (
        "hai pull",
        "hai synthesize",
        "hai explain",
        "hai daily",
        "hai memory set",
        "hai review record",
        "hai capabilities",
    ):
        assert expected in commands, (
            f"expected command {expected!r} missing from manifest; "
            f"got {sorted(commands)[:5]}..."
        )


# ---------------------------------------------------------------------------
# Schema stability
# ---------------------------------------------------------------------------


def test_manifest_schema_version_is_stable():
    manifest = build_manifest(build_parser())
    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["schema_version"] == "agent_cli_contract.v1"


def test_manifest_rows_have_stable_keys():
    # Required keys every leaf row must carry. ``output_schema`` and
    # ``preconditions`` are optional agent hints (WS-C) and are only
    # emitted when an annotation supplied them — walked over via a
    # subset check rather than strict equality.
    required_keys = {
        "command", "description", "mutation", "idempotent",
        "json_output", "exit_codes", "agent_safe", "flags",
    }
    optional_keys = {"output_schema", "preconditions"}
    allowed_keys = required_keys | optional_keys
    for row in walk_parser(build_parser()):
        row_keys = set(row)
        missing = required_keys - row_keys
        extra = row_keys - allowed_keys
        assert not missing, (
            f"row for {row.get('command')!r} is missing required keys "
            f"{sorted(missing)}"
        )
        assert not extra, (
            f"row for {row.get('command')!r} has unexpected keys "
            f"{sorted(extra)}; allowed: {sorted(allowed_keys)}"
        )


def test_every_row_value_is_in_the_allowed_enum():
    for row in walk_parser(build_parser()):
        cmd = row["command"]
        assert row["mutation"] in MUTATION_CLASSES, (
            f"{cmd}: mutation={row['mutation']!r} not in allowed set"
        )
        assert row["idempotent"] in IDEMPOTENCY, (
            f"{cmd}: idempotent={row['idempotent']!r} not in allowed set"
        )
        assert row["json_output"] in JSON_OUTPUT_MODES, (
            f"{cmd}: json_output={row['json_output']!r} not in allowed set"
        )
        assert isinstance(row["agent_safe"], bool), (
            f"{cmd}: agent_safe={row['agent_safe']!r} is not a bool"
        )
        for code in row["exit_codes"]:
            assert code in ALLOWED_EXIT_CODES, (
                f"{cmd}: exit_code={code!r} not in {sorted(ALLOWED_EXIT_CODES)}"
            )


def test_manifest_is_deterministic():
    """Two walks produce equal manifests — a committed doc can never
    drift from the code it was generated from."""

    first = build_manifest(build_parser())
    second = build_manifest(build_parser())
    assert first == second


# ---------------------------------------------------------------------------
# annotate_contract validation
# ---------------------------------------------------------------------------


def _tiny_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    return parser


def test_annotate_rejects_unknown_mutation():
    with pytest.raises(ContractAnnotationError, match="mutation"):
        annotate_contract(
            _tiny_parser(),
            mutation="bogus",  # type: ignore[arg-type]
            idempotent="yes",
            json_output="default",
            exit_codes=("OK",),
            agent_safe=True,
        )


def test_annotate_rejects_unknown_idempotency():
    with pytest.raises(ContractAnnotationError, match="idempotency"):
        annotate_contract(
            _tiny_parser(),
            mutation="read-only",
            idempotent="maybe",  # type: ignore[arg-type]
            json_output="default",
            exit_codes=("OK",),
            agent_safe=True,
        )


def test_annotate_rejects_unknown_json_output():
    with pytest.raises(ContractAnnotationError, match="json_output"):
        annotate_contract(
            _tiny_parser(),
            mutation="read-only",
            idempotent="n/a",
            json_output="yaml",  # type: ignore[arg-type]
            exit_codes=("OK",),
            agent_safe=True,
        )


def test_annotate_rejects_unknown_exit_code():
    with pytest.raises(ContractAnnotationError, match="exit code"):
        annotate_contract(
            _tiny_parser(),
            mutation="read-only",
            idempotent="n/a",
            json_output="default",
            exit_codes=("BLARGH",),
            agent_safe=True,
        )


def test_annotate_rejects_migrated_command_without_ok():
    """A migrated command (no LEGACY_0_2) must emit OK on success. Forgetting
    to list it is almost always a bug."""

    with pytest.raises(ContractAnnotationError, match="OK"):
        annotate_contract(
            _tiny_parser(),
            mutation="read-only",
            idempotent="n/a",
            json_output="default",
            exit_codes=("USER_INPUT",),
            agent_safe=True,
        )


def test_annotate_accepts_legacy_marker():
    """LEGACY_0_2 alone is a valid exit_codes value for unmigrated handlers."""

    p = _tiny_parser()
    annotate_contract(
        p,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("LEGACY_0_2",),
        agent_safe=True,
    )
    assert p._defaults["_contract_exit_codes"] == ("LEGACY_0_2",)


# ---------------------------------------------------------------------------
# hai capabilities end-to-end
# ---------------------------------------------------------------------------


def test_hai_capabilities_emits_parseable_json():
    hai = Path(".venv/bin/hai")
    if not hai.exists():
        pytest.skip("editable install not available in this env")
    r = subprocess.run(
        [str(hai), "capabilities"],
        capture_output=True, text=True, check=True,
    )
    payload = json.loads(r.stdout)
    assert payload["schema_version"] == SCHEMA_VERSION
    assert len(payload["commands"]) >= 20
    # Shape check on one row.
    commands_by_name = {row["command"]: row for row in payload["commands"]}
    assert "hai explain" in commands_by_name
    explain = commands_by_name["hai explain"]
    assert explain["mutation"] == "read-only"
    assert "NOT_FOUND" in explain["exit_codes"]


def test_hai_capabilities_markdown_renders():
    hai = Path(".venv/bin/hai")
    if not hai.exists():
        pytest.skip("editable install not available in this env")
    r = subprocess.run(
        [str(hai), "capabilities", "--markdown"],
        capture_output=True, text=True, check=True,
    )
    assert r.stdout.startswith("# Agent CLI contract")
    assert "| Command | Mutation |" in r.stdout
    assert "``hai explain``" in r.stdout


def test_render_markdown_is_stable():
    """Render twice, expect byte-equal output. Matches the deterministic
    manifest guarantee — a contract doc committed from one machine must
    regenerate identically on another."""

    manifest = build_manifest(build_parser())
    first = render_markdown(manifest)
    second = render_markdown(manifest)
    assert first == second


# ---------------------------------------------------------------------------
# Committed contract doc stays in sync with the manifest
# ---------------------------------------------------------------------------


def test_committed_contract_doc_matches_generated():
    """The committed reporting/docs/agent_cli_contract.md must match
    what render_markdown produces now. If this fails, regenerate:

        hai capabilities --markdown > reporting/docs/agent_cli_contract.md

    and commit the result alongside whatever annotation change triggered
    the drift."""

    manifest = build_manifest(build_parser())
    current = render_markdown(manifest)
    path = Path("reporting/docs/agent_cli_contract.md")
    if not path.exists():
        pytest.skip("contract doc not present (non-checkout test env)")
    committed = path.read_text(encoding="utf-8")
    assert current == committed, (
        "agent_cli_contract.md has drifted from the manifest. "
        "Regenerate with: hai capabilities --markdown > "
        "reporting/docs/agent_cli_contract.md"
    )
