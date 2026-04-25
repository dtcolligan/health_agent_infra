"""Skill ↔ CLI drift checker.

For every SKILL.md under ``src/health_agent_infra/skills/``, scan
fenced code blocks for ``hai <subcommand>`` invocations and the
``--flag`` tokens that appear alongside them. Cross-reference each
(command, flag) pair against the authoritative
``hai capabilities --json`` manifest. Report any flag a skill mentions
that doesn't exist on the command, or where a documented value-hint
pattern (e.g. ``<0|1>``) diverges from the CLI's ``choices``.

This is the v0.1.6 W3 audit-driven safety net. Background:

  - The 2026-04-25 user session hit ``hai review record --completed
    0|1`` (intent-router skill) when the actual CLI takes
    ``--completed yes|no`` and an ``--outcome-json`` payload.
  - Codex r2 surfaced additional drifts: ``reporting`` skill says
    ``hai review summary --since <date>`` (no such flag); the
    ``daily-plan-synthesis`` skill's ``allowed-tools`` may not match
    its own body examples.

Drift accumulates silently between releases. This validator runs as
a pytest test (``safety/tests/test_skill_cli_drift.py``) so any new
divergence fails CI immediately.

Run from repo root::

    python3 scripts/check_skill_cli_drift.py

Exit code 0 when no drifts. Exit code 1 when any drift detected
(report on stdout, summary on stderr).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "src" / "health_agent_infra" / "skills"

_FLAG_RE = re.compile(r"--([a-z][a-z0-9-]*)")

_CHOICE_HINT_RE = re.compile(
    r"[<{\[]([a-z0-9_]+(?:[|,/][a-z0-9_]+)+)[>}\]]"
)


def load_capabilities() -> dict[str, dict]:
    """Run ``hai capabilities`` and return command → manifest entry."""

    proc = subprocess.run(
        ["hai", "capabilities"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(proc.stdout)
    return {c["command"]: c for c in data["commands"]}


def known_command_chains(capabilities: dict[str, dict]) -> list[str]:
    """Sorted list of full ``hai foo bar`` command chains, longest-
    first so multi-token chains match before their parents."""

    return sorted(
        (c.removeprefix("hai ") for c in capabilities),
        key=lambda s: -len(s),
    )


def _iter_code_blocks(text: str) -> Iterable[str]:
    """Yield each fenced code block body (without the fence lines).
    We only validate flags inside code blocks — prose mentions can be
    illustrative and shouldn't trigger drift findings."""

    in_block = False
    buf: list[str] = []
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            if in_block:
                yield "\n".join(buf)
                buf = []
                in_block = False
            else:
                in_block = True
            continue
        if in_block:
            buf.append(line)


def find_invocations(text: str, command_chains: list[str]) -> list[tuple[str, str]]:
    """Return list of (command_chain, scoped_window) tuples for each
    ``hai <command>`` invocation found in a fenced code block.

    Within a single code block, an invocation owns every line from
    itself up to (but not including) the next ``hai <command>``
    invocation in the same block. This keeps multi-line heredoc-style
    usages intact while preventing one invocation from swallowing
    flags from sibling commands listed below it.
    """

    out: list[tuple[str, str]] = []
    for block in _iter_code_blocks(text):
        block_lines = block.split("\n")
        invocation_starts: list[tuple[int, str]] = []
        for i, line in enumerate(block_lines):
            if "hai " not in line:
                continue
            for chain in command_chains:
                if f"hai {chain}" in line:
                    invocation_starts.append((i, chain))
                    break
        if not invocation_starts:
            continue
        for j, (start, chain) in enumerate(invocation_starts):
            end = (
                invocation_starts[j + 1][0]
                if j + 1 < len(invocation_starts)
                else len(block_lines)
            )
            window = "\n".join(block_lines[start:end])
            out.append((chain, window))
    return out


def extract_flags(window: str) -> list[tuple[str, str | None]]:
    """Return list of (flag_name, choice_hint_or_none) found in
    ``window``. A choice hint is any ``a|b|c`` pattern within 40
    characters after the flag."""

    out: list[tuple[str, str | None]] = []
    for m in _FLAG_RE.finditer(window):
        flag = m.group(1)
        tail = window[m.end():m.end() + 40]
        choice_match = _CHOICE_HINT_RE.search(tail)
        choice = choice_match.group(1) if choice_match else None
        out.append((flag, choice))
    return out


def check_drift(
    skill_path: Path, capabilities: dict[str, dict],
    chains: list[str],
) -> list[str]:
    """Return a list of human-readable drift findings for one SKILL."""

    findings: list[str] = []
    text = skill_path.read_text(encoding="utf-8")
    for chain, window in find_invocations(text, chains):
        cmd_key = f"hai {chain}"
        cmd = capabilities.get(cmd_key)
        if cmd is None:
            findings.append(
                f"  unknown command referenced: `{cmd_key}`"
            )
            continue
        cli_flags = {f["name"].removeprefix("--"): f for f in cmd.get("flags", [])}
        for flag, choice_hint in extract_flags(window):
            cli_flag = cli_flags.get(flag)
            if cli_flag is None:
                findings.append(
                    f"  `{cmd_key}` — skill mentions `--{flag}` "
                    f"but CLI has no such flag"
                )
                continue
            if choice_hint is not None:
                skill_choices = set(re.split(r"[|,/]", choice_hint))
                cli_choices = cli_flag.get("choices")
                if cli_choices is not None:
                    cli_choice_set = {str(c) for c in cli_choices}
                    if not skill_choices.issubset(cli_choice_set):
                        extras = skill_choices - cli_choice_set
                        findings.append(
                            f"  `{cmd_key} --{flag}` — skill choice "
                            f"hint `{choice_hint}` includes value(s) "
                            f"not in CLI choices "
                            f"`{sorted(cli_choice_set)}` "
                            f"(extras: {sorted(extras)})"
                        )
    return findings


def iter_skill_files() -> Iterable[Path]:
    return sorted(SKILLS_DIR.glob("*/SKILL.md"))


# ---------------------------------------------------------------------------
# v0.1.7 W25: allowed-tools frontmatter inspection
# ---------------------------------------------------------------------------
#
# Codex r2/r3 flagged that `daily-plan-synthesis` allows
# `Bash(hai synthesize --bundle-only *)` but its body example calls
# `hai synthesize --as-of <today> --user-id <u> --bundle-only` — putting
# `--bundle-only` AFTER other flags. If Claude Code's allowed-tools
# matcher is prefix-sensitive, the skill silently blocks its own
# documented command.
#
# We can't determine the matcher's exact semantics from outside Claude
# Code, but we CAN flag the suspicious pattern: when `allowed-tools`
# grants `Bash(hai foo --flag *)` and a body example shows `hai foo`
# WITHOUT `--flag` adjacent to the command, surface it as a suspicious
# drift. The maintainer can then either rewrite the example to put the
# specific flag first, or broaden the allowed-tools to `Bash(hai foo *)`.

_FRONTMATTER_RE = re.compile(
    r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL,
)
_ALLOWED_TOOLS_RE = re.compile(
    r"^allowed-tools:\s*(.+)$", re.MULTILINE,
)
_BASH_PERMISSION_RE = re.compile(
    r"Bash\(\s*(hai(?:\s+[a-z][a-z0-9_-]*)+)([^)]*)\)"
)


def parse_allowed_tools_frontmatter(text: str) -> list[str]:
    """Extract the ``allowed-tools:`` line from a SKILL.md frontmatter
    block. Returns the raw value string, or empty list when absent."""

    fm_match = _FRONTMATTER_RE.match(text)
    if not fm_match:
        return []
    fm_body = fm_match.group(1)
    allowed_match = _ALLOWED_TOOLS_RE.search(fm_body)
    if not allowed_match:
        return []
    # Comma-separated list of tool grants.
    raw = allowed_match.group(1).strip()
    return [tok.strip() for tok in raw.split(",") if tok.strip()]


def parse_hai_permissions(allowed_tools: list[str]) -> list[tuple[str, str]]:
    """Pull out (command_chain, flag_pattern_after_command) for each
    `Bash(hai ...)` permission. ``command_chain`` is the command after
    the leading ``hai`` (e.g. ``synthesize`` or ``intake gym``);
    ``flag_pattern_after_command`` is whatever appears after the
    command chain inside the parens (e.g. ``--bundle-only *`` for
    `Bash(hai synthesize --bundle-only *)`).

    Returns empty list when no hai permissions are granted.
    """

    out: list[tuple[str, str]] = []
    for tok in allowed_tools:
        m = _BASH_PERMISSION_RE.search(tok)
        if not m:
            continue
        # group(1) includes "hai " prefix per the regex; strip it so
        # downstream code can reuse `find_invocations(text, [chain])`
        # without double-counting the prefix.
        command_chain = m.group(1).strip()
        if command_chain.startswith("hai "):
            command_chain = command_chain[len("hai "):].strip()
        tail = m.group(2).strip()
        out.append((command_chain, tail))
    return out


def check_allowed_tools_consistency(
    skill_path: Path, capabilities: dict[str, dict],
) -> list[str]:
    """W25: when allowed-tools grants `Bash(hai foo --bar *)` (a
    flag-constrained pattern), check that every body example of
    `hai foo` either starts with `--bar` immediately after the
    command OR is broader than the permission scope.

    This is a heuristic — we can't confirm Claude Code's exact
    matcher behaviour from outside. False positives are tolerable
    because the fix is always safe: either reorder the example or
    broaden the permission.
    """

    findings: list[str] = []
    text = skill_path.read_text(encoding="utf-8")
    allowed = parse_allowed_tools_frontmatter(text)
    perms = parse_hai_permissions(allowed)
    # Only flag-constrained permissions matter here; bare
    # `Bash(hai foo *)` without a specific flag accepts any ordering.
    constrained = [(c, t) for c, t in perms
                   if t and not t.lstrip().startswith("*")
                   and "--" in t]
    if not constrained:
        return findings
    for command_chain, tail in constrained:
        # Extract the leading flag(s) from the permission tail.
        # E.g. "--bundle-only *" → ["--bundle-only"].
        permission_flags = [
            t for t in re.findall(r"--[a-z][a-z0-9-]*", tail)
        ]
        if not permission_flags:
            continue
        # Walk body examples for this command chain.
        for chain_in_text, window in find_invocations(text, [command_chain]):
            if chain_in_text != command_chain:
                continue
            # Look at the portion of the window AFTER `hai <chain>`.
            tail_window = window.split(f"hai {command_chain}", 1)[-1]
            # Strip leading whitespace + backslash continuations.
            stripped = tail_window.lstrip(" \\\n")
            # Does the example start with one of the permission flags?
            starts_with_perm_flag = any(
                stripped.startswith(flag) for flag in permission_flags
            )
            if not starts_with_perm_flag:
                findings.append(
                    f"  `hai {command_chain}` example in {skill_path.name} "
                    f"does not begin with the permission-required flag(s) "
                    f"{permission_flags} — Claude Code's allowed-tools "
                    f"matcher may block the example. Either reorder the "
                    f"example to put {permission_flags[0]} first, or "
                    f"broaden the permission to `Bash(hai {command_chain} *)`."
                )
    return findings


def main() -> int:
    capabilities = load_capabilities()
    chains = known_command_chains(capabilities)

    total_findings = 0
    for skill_path in iter_skill_files():
        # Flag-mismatch (existing W3 check) + allowed-tools order
        # heuristic (new W25 check) both report into the same per-file
        # block.
        findings = check_drift(skill_path, capabilities, chains)
        findings.extend(check_allowed_tools_consistency(
            skill_path, capabilities,
        ))
        if findings:
            rel = skill_path.relative_to(REPO_ROOT)
            print(f"\n{rel}:")
            for f in findings:
                print(f)
            total_findings += len(findings)

    if total_findings == 0:
        print("OK: no skill ↔ CLI drift detected.")
        return 0
    print(
        f"\n{total_findings} drift finding(s) across the skill tree.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
