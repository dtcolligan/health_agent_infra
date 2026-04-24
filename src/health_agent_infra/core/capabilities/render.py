"""Render a manifest as Markdown for ``reporting/docs/agent_cli_contract.md``.

The markdown output is deterministic (rows sorted, no timestamps) so
the committed file only changes when the annotations themselves
change. Regenerated on commit via a packaged script; drift from the
manifest is a CI failure rather than a bug waiting to bite an agent.
"""

from __future__ import annotations

from typing import Any


_PREAMBLE = """\
# Agent CLI contract

**This file is generated. Do not edit by hand.** Source of truth is
the annotations on each ``add_parser`` call in
``src/health_agent_infra/cli.py``; regenerate with
``python -m health_agent_infra.core.capabilities.render --write`` or
by invoking ``hai capabilities --json`` and piping through the same
renderer.

Schema: see ``core/capabilities/walker.py``. Exit codes follow
``reporting/docs/cli_exit_codes.md``. Every handler is on the stable
taxonomy; the ``LEGACY_0_2`` sentinel is retained in the schema for
forward-compatibility but is not currently emitted.

**Per-command structured detail lives in the JSON manifest, not
this markdown.** Every row below also carries a ``flags[]`` array
(name / type / required / choices / default / help / aliases), and
selected high-traffic commands opt in to ``output_schema`` (JSON
shape per exit code) and ``preconditions`` (state that must exist
before invocation). Agents should ``hai capabilities`` and read the
JSON; this markdown is an at-a-glance overview for humans.

## Mutation classes

| Value | Meaning |
|---|---|
| ``read-only`` | No persistent writes of any kind. |
| ``writes-sync-log`` | Writes only ``sync_run_log`` rows. |
| ``writes-audit-log`` | Appends to JSONL audit logs (no main-DB writes). |
| ``writes-state`` | Writes to the primary state DB tables. |
| ``writes-memory`` | Writes to the ``user_memory`` table. |
| ``writes-skills-dir`` | Copies the packaged skills tree to ``~/.claude/skills/``. |
| ``writes-config`` | Writes a config / thresholds file on disk. |
| ``writes-credentials`` | Writes to the OS keyring. |
| ``interactive`` | Requires live human input; not agent-invocable. |

## Idempotency

| Value | Meaning |
|---|---|
| ``yes`` | Same inputs produce the same persisted state after every call. |
| ``yes-with-supersede`` | Idempotent via an explicit ``--supersede`` flag that versions. |
| ``no`` | Append-only, order-sensitive, or interactive. |
| ``n/a`` | Read-only; idempotency doesn't apply. |

## JSON output modes

| Value | Meaning |
|---|---|
| ``default`` | Emits JSON on stdout unconditionally. |
| ``opt-in`` | Emits JSON only when ``--json`` is passed. |
| ``opt-out`` | Emits JSON by default; ``--text`` suppresses. |
| ``none`` | Text output only. |
| ``dual`` | Supports both ``--json`` and ``--text`` explicitly. |

## Commands
"""


def render_markdown(manifest: dict[str, Any]) -> str:
    """Return the markdown doc for the given manifest."""

    lines: list[str] = [_PREAMBLE.rstrip()]
    lines.append("")
    lines.append(
        f"*{len(manifest['commands'])} commands; "
        f"hai {manifest['hai_version']}; "
        f"schema {manifest['schema_version']}*"
    )
    lines.append("")
    lines.append(
        "| Command | Mutation | Idempotent | JSON | Agent-safe | Exit codes | Description |"
    )
    lines.append("|---|---|---|---|---|---|---|")
    for row in manifest["commands"]:
        lines.append(_row_to_markdown(row))
    lines.append("")
    return "\n".join(lines)


def _row_to_markdown(row: dict[str, Any]) -> str:
    codes = ", ".join(f"``{c}``" for c in row["exit_codes"]) or "—"
    agent = "yes" if row["agent_safe"] else "no"
    description = (row["description"] or "").replace("|", "\\|")
    # Collapse newlines in description so the table row stays on one line.
    description = " ".join(description.split())
    return (
        f"| ``{row['command']}`` "
        f"| ``{row['mutation']}`` "
        f"| ``{row['idempotent']}`` "
        f"| ``{row['json_output']}`` "
        f"| {agent} "
        f"| {codes} "
        f"| {description} |"
    )
