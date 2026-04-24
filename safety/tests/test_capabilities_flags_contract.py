"""WS-C contract — every CLI flag reachable via ``--help`` appears in
``hai capabilities --json``'s ``flags[]``.

This is the structural gate that catches two failure modes:

1. A new ``add_argument`` landing without the walker knowing about
   its argparse action class (e.g. a custom action silently skipped
   by the action-name resolver).
2. An ``add_argument`` call where the walker's skip list is too
   aggressive — hiding a flag agents need to know about.

The assertion is directional: every flag argparse knows about must
appear in the manifest. Extra manifest entries would be caught by a
different test, but in practice the walker can't invent flags.
"""

from __future__ import annotations

from typing import Iterable

import pytest

from health_agent_infra.cli import build_parser
from health_agent_infra.core.capabilities import build_manifest
from health_agent_infra.core.capabilities.walker import (
    _subparsers_actions,
    _SKIP_ACTION_CLASSES,
)


def _walk_leaf_parsers():
    """Yield ``(command_path, leaf_parser)`` for every leaf in the
    argparse tree. Mirrors the walker's own traversal so the test is
    comparing apples to apples.
    """

    import argparse as _argparse

    def _walk(parser: _argparse.ArgumentParser, path: list[str]):
        sub_actions = _subparsers_actions(parser)
        if not sub_actions:
            defaults = parser._defaults
            if defaults.get("func") is not None:
                yield " ".join(path), parser
            return
        for sub in sub_actions:
            for name, child in sub.choices.items():
                yield from _walk(child, path + [name])

    root = build_parser()
    yield from _walk(root, ["hai"])


def _expected_flag_names(parser) -> set[str]:
    """Primary flag name per argparse action, matching the walker's
    primary-option-string convention (long form wins).
    """

    names: set[str] = set()
    for action in parser._actions:
        if isinstance(action, _SKIP_ACTION_CLASSES):
            continue
        if action.option_strings:
            long_forms = [s for s in action.option_strings if s.startswith("--")]
            names.add(long_forms[0] if long_forms else action.option_strings[0])
        else:
            # Positional — walker uses action.dest as the name.
            names.add(action.dest)
    return names


def test_every_flag_argparse_knows_about_appears_in_manifest():
    """For every leaf command, the set of flag names the walker emits
    must equal the set argparse would accept."""

    manifest = build_manifest(build_parser())
    manifest_by_cmd = {row["command"]: row for row in manifest["commands"]}

    for command, leaf in _walk_leaf_parsers():
        assert command in manifest_by_cmd, (
            f"{command!r} has a func=... handler but doesn't appear in "
            f"the manifest — is it missing annotate_contract()?"
        )
        row = manifest_by_cmd[command]
        manifest_names = {f["name"] for f in row["flags"]}
        expected = _expected_flag_names(leaf)

        missing_from_manifest = expected - manifest_names
        extra_in_manifest = manifest_names - expected

        assert not missing_from_manifest, (
            f"{command}: flags seen by argparse but missing from "
            f"manifest: {sorted(missing_from_manifest)}"
        )
        assert not extra_in_manifest, (
            f"{command}: manifest lists flags argparse doesn't know "
            f"about: {sorted(extra_in_manifest)}"
        )


def test_flag_entry_shape_is_stable():
    """Each flag entry carries the same set of keys. If a new key
    lands, it needs to land on every flag — otherwise consumers pattern-
    matching against the shape break silently.
    """

    expected_keys = {
        "name", "positional", "required", "type", "choices",
        "default", "help", "action", "nargs", "aliases",
    }
    manifest = build_manifest(build_parser())
    for row in manifest["commands"]:
        for flag in row["flags"]:
            assert set(flag) == expected_keys, (
                f"{row['command']}: flag {flag.get('name')!r} has keys "
                f"{set(flag)}; expected {expected_keys}"
            )


def test_positional_flags_when_present_are_marked_positional_and_required():
    """Positional arguments (no option_strings) must be marked
    ``positional=True`` and ``required=True`` (unless nargs='?').
    Argparse treats them that way, so the manifest should too.

    Note: the current hai CLI uses all-optional flags by convention
    (an agent-friendly choice — positionals are harder to discover
    via the manifest). This test asserts the contract for any
    positional that does land in the future; if zero positionals
    exist, the loop is simply vacuous, which is accurate."""

    manifest = build_manifest(build_parser())
    for row in manifest["commands"]:
        for flag in row["flags"]:
            if not flag["positional"]:
                continue
            assert not flag["name"].startswith("-"), (
                f"{row['command']}: positional flag name "
                f"{flag['name']!r} starts with '-' — looks like "
                f"a classification bug in the walker."
            )
            # Optional-positional (nargs='?') is the one case
            # where required is legitimately False.
            if flag["nargs"] != "?":
                assert flag["required"] is True, (
                    f"{row['command']}: positional flag "
                    f"{flag['name']!r} has nargs={flag['nargs']!r} "
                    f"but required={flag['required']}"
                )


def test_all_current_cli_flags_are_optional():
    """Current design convention — the hai CLI uses keyword flags
    exclusively so agents can discover them from the manifest. If
    this starts failing, the contract doc wording + intent-router
    assumptions need to grow positional-arg handling."""

    manifest = build_manifest(build_parser())
    positionals = [
        (row["command"], flag["name"])
        for row in manifest["commands"]
        for flag in row["flags"]
        if flag["positional"]
    ]
    assert positionals == [], (
        "CLI gained a positional flag — decide whether to keep it "
        "(and update the intent-router skill) or convert it to a "
        "keyword flag. Current positionals: "
        f"{positionals}"
    )


def test_store_true_and_store_false_flags_report_bool_type():
    """``store_true`` / ``store_false`` actions have ``.type = None``
    under the hood; the walker must infer ``bool`` from the action
    class so agents can build a correct input schema."""

    manifest = build_manifest(build_parser())
    saw_bool = False
    for row in manifest["commands"]:
        for flag in row["flags"]:
            if flag["action"] in ("store_true", "store_false"):
                saw_bool = True
                assert flag["type"] == "bool", (
                    f"{row['command']}: {flag['name']} is "
                    f"{flag['action']} but type={flag['type']!r}"
                )
    assert saw_bool, "CLI has no store_true / store_false flags — test vacuous."


def test_choices_are_serialised_as_json_lists():
    """``choices=range(1, 6)`` and similar iterables must be flattened
    into JSON-able lists on the manifest side."""

    import json

    manifest = build_manifest(build_parser())
    # Serialise the whole manifest; if any choices entry is non-JSON
    # (e.g. a bare ``range`` object), this blows up loudly.
    json.dumps(manifest)


def test_flag_default_is_json_safe():
    """Every ``default`` on a flag entry must be JSON-serialisable.
    Callable defaults get nulled so the manifest stays honest."""

    import json
    manifest = build_manifest(build_parser())
    for row in manifest["commands"]:
        for flag in row["flags"]:
            json.dumps(flag["default"])