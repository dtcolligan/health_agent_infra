"""W-AB (v0.1.13) — `hai capabilities --human` mode contracts.

Contracts pinned:

  1. The `--human` flag is registered and exposed by the parser.

  2. Every command in the JSON manifest appears exactly once in the
     human render. A silent omission would leave a new user thinking
     a command does not exist; the `_CATEGORY_MAP` "Advanced & tools"
     fallback exists to prevent that.

  3. Every top-level subcommand prefix the live parser registers is
     mapped explicitly in `_CATEGORY_MAP`. Adding a new top-level
     group without a category mapping is a merge-blocking signal —
     the bucket choice is a product decision, not a reflex default.

  4. Categories render in the documented order.

  5. The render is deterministic — two invocations produce byte-equal
     output. (Same property the agent-facing manifest pins.)

  6. The render's overall shape is reasonable: it is markdown-shaped
     (not JSON), it carries the version + command count header, and
     it is not absurdly long.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from health_agent_infra.cli import build_parser
from health_agent_infra.core.capabilities import build_manifest
from health_agent_infra.core.capabilities.render import (
    _CATEGORY_BLURB,
    _CATEGORY_MAP,
    _CATEGORY_ORDER,
    _top_level_prefix,
    render_human,
)


# ---------------------------------------------------------------------------
# Parser surface
# ---------------------------------------------------------------------------


def test_human_flag_is_registered_on_capabilities_parser():
    """`hai capabilities --human` must parse without error."""

    parser = build_parser()
    args = parser.parse_args(["capabilities", "--human"])
    assert getattr(args, "human", False) is True


def test_human_flag_does_not_collide_with_markdown_flag():
    """Both flags can be passed; --human takes precedence by handler order
    so the user's intent ('I want the human view') wins. The parser does
    not raise."""

    parser = build_parser()
    args = parser.parse_args(["capabilities", "--human", "--markdown"])
    assert getattr(args, "human", False) is True
    assert getattr(args, "markdown", False) is True


# ---------------------------------------------------------------------------
# Coverage — every command appears, every top-level prefix is mapped
# ---------------------------------------------------------------------------


def test_every_command_appears_in_human_render():
    """No command may silently fall off the human render — a new user
    would never know it existed."""

    manifest = build_manifest(build_parser())
    rendered = render_human(manifest)
    for row in manifest["commands"]:
        assert f"`{row['command']}`" in rendered, (
            f"command {row['command']!r} missing from human render"
        )


def test_every_top_level_prefix_is_explicitly_mapped():
    """Every top-level subcommand prefix the live parser registers must
    be present in `_CATEGORY_MAP`. The "Advanced & tools" fallback in
    `render_human` exists for safety; it is NOT a license to leave new
    groups uncategorised. Adding a new top-level group is a product
    decision, not a default."""

    manifest = build_manifest(build_parser())
    prefixes = {_top_level_prefix(row["command"]) for row in manifest["commands"]}
    prefixes.discard("")
    unmapped = prefixes - _CATEGORY_MAP.keys()
    assert not unmapped, (
        f"top-level subcommand prefix(es) missing from _CATEGORY_MAP: "
        f"{sorted(unmapped)}. Add an explicit row to _CATEGORY_MAP "
        f"in core/capabilities/render.py."
    )


def test_category_map_only_references_known_categories():
    """Every value in `_CATEGORY_MAP` must be one of `_CATEGORY_ORDER`.
    A typo would produce a category section the renderer skips."""

    for prefix, category in _CATEGORY_MAP.items():
        assert category in _CATEGORY_ORDER, (
            f"_CATEGORY_MAP[{prefix!r}] = {category!r} is not in _CATEGORY_ORDER"
        )


def test_category_blurb_covers_every_category():
    """Each `_CATEGORY_ORDER` entry must have a `_CATEGORY_BLURB` entry."""

    for category in _CATEGORY_ORDER:
        assert category in _CATEGORY_BLURB, (
            f"_CATEGORY_BLURB missing entry for {category!r}"
        )


# ---------------------------------------------------------------------------
# Ordering + determinism
# ---------------------------------------------------------------------------


def test_categories_render_in_documented_order():
    """Sections must render in `_CATEGORY_ORDER`. A user reads top-down;
    the order encodes the workflow narrative (start → see state → bring
    data in → recommend → plan → advanced)."""

    manifest = build_manifest(build_parser())
    rendered = render_human(manifest)

    last_pos = -1
    for category in _CATEGORY_ORDER:
        marker = f"## {category}"
        if marker not in rendered:
            # A category may be empty in some manifest configurations;
            # `render_human` skips those. That's fine — but if it appears,
            # it must appear AFTER the previous category that did.
            continue
        pos = rendered.index(marker)
        assert pos > last_pos, (
            f"category {category!r} rendered at position {pos}, "
            f"before a previously-rendered category (last_pos={last_pos})"
        )
        last_pos = pos


def test_human_render_is_deterministic():
    """Two consecutive renders of the same manifest must be byte-equal.
    The manifest itself is already deterministic (test_capabilities.py
    pins this); the human formatter must not reintroduce nondeterminism."""

    manifest = build_manifest(build_parser())
    a = render_human(manifest)
    b = render_human(manifest)
    assert a == b


# ---------------------------------------------------------------------------
# Output shape
# ---------------------------------------------------------------------------


def test_human_render_is_markdown_not_json():
    """The output is human prose, not the JSON manifest."""

    manifest = build_manifest(build_parser())
    rendered = render_human(manifest)
    assert rendered.startswith("# hai — quick reference")
    # Negative: must not parse as JSON.
    try:
        json.loads(rendered)
    except json.JSONDecodeError:
        pass  # expected
    else:
        assert False, "human render unexpectedly parses as JSON"


def test_human_render_carries_version_and_command_count():
    """The header must surface the package version + command count so a
    user reading a printout knows which build it describes."""

    manifest = build_manifest(build_parser())
    rendered = render_human(manifest)
    assert manifest["hai_version"] in rendered
    assert f"{len(manifest['commands'])} commands" in rendered


def test_human_render_has_reasonable_length():
    """The human render is meant as a one-page-ish reference. We accept
    a wide range — small enough that it isn't the dense agent doc, large
    enough to cover all commands with descriptions and flags."""

    manifest = build_manifest(build_parser())
    rendered = render_human(manifest)
    line_count = rendered.count("\n")
    assert 50 < line_count < 400, (
        f"human render line count {line_count} outside expected range "
        f"(50, 400). Check whether a category got dropped or a row "
        f"started spanning multiple paragraphs."
    )


# ---------------------------------------------------------------------------
# CLI invocation
# ---------------------------------------------------------------------------


def test_cli_capabilities_human_invocation_exits_clean():
    """`hai capabilities --human` must exit 0 and produce non-empty output
    starting with the human-render preamble."""

    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-m", "health_agent_infra.cli", "capabilities", "--human"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"hai capabilities --human exited {result.returncode}; "
        f"stderr={result.stderr!r}"
    )
    assert result.stdout.startswith("# hai — quick reference")


def test_cli_capabilities_default_still_emits_json():
    """The default invocation (no flag) must remain JSON. --human must
    not silently change the default surface — agents depend on the
    JSON manifest."""

    repo_root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-m", "health_agent_infra.cli", "capabilities"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "agent_cli_contract.v1"
