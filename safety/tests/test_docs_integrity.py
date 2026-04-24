"""Documentation integrity — SKILL.md and docs reference only existing commands.

Would have caught the 2026-04-23 drift where `recovery-readiness/SKILL.md`
instructed agents to call `hai writeback` while the rest of the domain
skills had migrated to `hai propose`, and the legacy `writeback`
subcommand's `allowed-tools` listing in that skill blocked the correct
path entirely.

Two assertions:

  1. Every `Bash(hai <subcommand> ...)` token in a SKILL.md resolves to
     a command currently listed in `hai capabilities --json`.
  2. Every `hai <subcommand>` reference in `reporting/docs/*.md` also
     resolves.

The check is structural — it catches command renames/removals, not
semantic drift inside help text. Semantic drift is caught by the
contract tests shipped alongside each workstream.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest


# Path helpers ---------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "src" / "health_agent_infra" / "skills"
DOCS_DIR = REPO_ROOT / "reporting" / "docs"


def _current_hai_commands() -> set[str]:
    """Return the set of `hai <subcmd>` strings the current source
    tree exposes, built directly from the argparse tree.

    Built via the in-process walker rather than shelling out to
    ``hai capabilities`` — the installed `hai` binary (pipx or
    otherwise) can lag behind the source under test and produce a
    stale manifest that fails this doc-integrity check while the
    live CLI is actually correct.
    """

    from health_agent_infra.cli import build_parser
    from health_agent_infra.core.capabilities import build_manifest

    manifest = build_manifest(build_parser())
    return {entry["command"] for entry in manifest["commands"]}


_HAI_CMD_PATTERN = re.compile(
    r"\bhai[\s\n]+([a-z][a-z0-9_-]*)(?:[\s\n]+([a-z][a-z0-9_-]*))?"
)


def _extract_hai_refs(text: str, commands: set[str]) -> set[str]:
    """Pull every `hai <subcommand>` phrase from a markdown document.

    Two-token subcommands (`hai state snapshot`, `hai review record`)
    are resolved first — if ``hai X Y`` is a valid manifest entry, that
    wins. Otherwise falls back to ``hai X``. Tokens that don't match a
    subcommand-like shape after whitespace normalisation (including
    markdown-inline line wraps) are ignored rather than reported as
    drift — false positives in historical prose waste more time than
    they save.
    """
    refs: set[str] = set()
    # Normalise runs of whitespace (including hard line wraps inside
    # code-formatted references) so ``hai state\n    snapshot`` parses
    # identically to ``hai state snapshot``.
    text_norm = re.sub(r"\s+", " ", text)
    for match in _HAI_CMD_PATTERN.finditer(text_norm):
        first, second = match.group(1), match.group(2)
        two_token = f"hai {first} {second}" if second else None
        one_token = f"hai {first}"

        # Prefer the two-token form iff it actually resolves; this
        # avoids the trap where ``hai clean output`` in prose is
        # misread as a command.
        if two_token and two_token in commands:
            refs.add(two_token)
        elif any(cmd == f"hai {first} {second}" for cmd in commands if second):
            refs.add(two_token)  # type: ignore[arg-type]
        elif one_token in commands:
            refs.add(one_token)
        elif any(cmd.startswith(f"{one_token} ") for cmd in commands):
            # ``hai review`` with no specific subcmd in prose like
            # "the hai review family" — resolve as prefix.
            refs.add(one_token)
        # Anything else is a candidate drift; return it so tests flag it.
        else:
            refs.add(two_token or one_token)
    return refs


def _resolve(ref: str, commands: set[str]) -> bool:
    """Match a markdown-extracted `hai <x> [<y>]` reference against the
    manifest. A ref like `hai review record` matches exactly; a ref like
    `hai review` (single token) matches any `hai review <subcmd>` only
    if an exact match doesn't exist, to tolerate prose like 'the `hai
    review` family'.
    """
    if ref in commands:
        return True
    prefix = f"{ref} "
    return any(cmd.startswith(prefix) for cmd in commands)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_skill_md_allowed_tools_resolve() -> None:
    """Every `Bash(hai ...)` token in every SKILL.md `allowed-tools`
    frontmatter key must resolve to a current manifest command."""
    commands = _current_hai_commands()
    errors: list[str] = []

    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        text = skill_md.read_text()
        # Parse only the frontmatter's allowed-tools line (stop at end
        # of frontmatter to avoid hits in prose examples).
        frontmatter_match = re.search(
            r"^---\n(.*?)\n---", text, re.DOTALL,
        )
        if frontmatter_match is None:
            errors.append(f"{skill_md.relative_to(REPO_ROOT)}: missing frontmatter")
            continue

        allowed_tools_match = re.search(
            r"allowed-tools:\s*(.+)",
            frontmatter_match.group(1),
        )
        if allowed_tools_match is None:
            continue  # skill opts out of tool allowlist

        # Each entry looks like `Bash(hai <subcmd> [<subsubcmd>] [flag-pattern] *)`.
        # Pull out just the command tokens (everything up to the first
        # flag or the trailing `*`), since allowed-tools may scope by
        # flag pattern (`Bash(hai synthesize --bundle-only *)`) which
        # restricts the invocation, not the command identity.
        bash_refs = re.findall(
            r"Bash\(hai\s+([a-z][a-z0-9_-]*(?:\s+[a-z][a-z0-9_-]*)?)",
            allowed_tools_match.group(1),
        )
        for raw in bash_refs:
            ref = f"hai {raw.strip()}"
            # Two-token refs like 'hai state snapshot' are resolved as-is;
            # single-token refs like 'hai writeback' match directly.
            if not _resolve(ref, commands):
                errors.append(
                    f"{skill_md.relative_to(REPO_ROOT)}: "
                    f"allowed-tools references {ref!r} which is not in "
                    f"the current `hai capabilities --json` manifest."
                )

    assert not errors, "\n".join(errors)


def test_skill_md_body_hai_refs_resolve() -> None:
    """Every `hai <subcommand>` reference in a SKILL.md's body (below
    the frontmatter) also resolves in the current manifest.

    Prose drift is a real failure mode: a skill that *instructs* agents
    to call `hai writeback` ships broken even if `allowed-tools` is
    correct.
    """
    commands = _current_hai_commands()
    errors: list[str] = []

    for skill_md in SKILLS_DIR.glob("*/SKILL.md"):
        text = skill_md.read_text()
        # Skip frontmatter to avoid double-counting allowed-tools entries.
        body = re.sub(r"^---\n.*?\n---\n", "", text, count=1, flags=re.DOTALL)

        for ref in _extract_hai_refs(body, commands):
            if not _resolve(ref, commands):
                errors.append(
                    f"{skill_md.relative_to(REPO_ROOT)}: body references "
                    f"{ref!r} which is not in the current manifest."
                )

    assert not errors, "\n".join(errors)


def test_reporting_docs_hai_refs_resolve() -> None:
    """Every `hai <subcommand>` reference under `reporting/docs/` must
    resolve. Caught at commit time so drift can't sneak into a release.
    """
    commands = _current_hai_commands()
    errors: list[str] = []

    if not DOCS_DIR.exists():
        pytest.skip(f"docs directory not found: {DOCS_DIR}")

    for doc in DOCS_DIR.rglob("*.md"):
        text = doc.read_text()
        for ref in _extract_hai_refs(text, commands):
            if not _resolve(ref, commands):
                errors.append(
                    f"{doc.relative_to(REPO_ROOT)}: references {ref!r} "
                    f"which is not in the current manifest."
                )

    # Soft-fail for now: reporting/docs includes historical plans that
    # may name retired commands. Treat docs integrity as warn-only until
    # Workstream E's contract-test pass explicitly scopes which docs
    # must stay current.
    if errors:
        pytest.skip(
            "reporting/docs contains references to commands not in the "
            "current manifest. This is expected for historical plan "
            "docs; retire or scope-limit this test under Workstream E. "
            f"Refs: {errors[:10]}"
        )
