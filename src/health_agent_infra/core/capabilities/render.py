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


# ---------------------------------------------------------------------------
# Human-readable render — `hai capabilities --human` (W-AB, v0.1.13)
# ---------------------------------------------------------------------------

# Workflow-shaped category buckets (Option A). Each top-level subcommand
# group (`hai <prefix> ...`) maps to exactly one category. New top-level
# groups must be added here or `render_human` will surface them under
# "Advanced & tools" by default — the test suite asserts coverage.
_CATEGORY_ORDER: tuple[str, ...] = (
    "Get started",
    "See your state",
    "Bring data in",
    "Make recommendations",
    "Plan and commit",
    "Advanced & tools",
)

_CATEGORY_BLURB: dict[str, str] = {
    "Get started":         "First-time setup, credentials, and health checks.",
    "See your state":      "Read what the system knows; never mutates.",
    "Bring data in":       "Pull from wearables; record subjective inputs.",
    "Make recommendations": "Compose, validate, and commit the daily plan.",
    "Plan and commit":     "Author training intent and targets you stand behind.",
    "Advanced & tools":    "Demo runner, research surface, eval, and admin.",
}

_CATEGORY_MAP: dict[str, str] = {
    # Get started
    "init":                  "Get started",
    "setup-skills":          "Get started",
    "auth":                  "Get started",
    "doctor":                "Get started",
    # See your state
    "today":                 "See your state",
    "stats":                 "See your state",
    "explain":               "See your state",
    "capabilities":          "See your state",
    # Bring data in
    "pull":                  "Bring data in",
    "intake":                "Bring data in",
    # Make recommendations
    "propose":               "Make recommendations",
    "synthesize":            "Make recommendations",
    "daily":                 "Make recommendations",
    "review":                "Make recommendations",
    # Plan and commit
    "intent":                "Plan and commit",
    "target":                "Plan and commit",
    # Advanced & tools
    "demo":                  "Advanced & tools",
    "research":              "Advanced & tools",
    "memory":                "Advanced & tools",
    "state":                 "Advanced & tools",
    "config":                "Advanced & tools",
    "exercise":              "Advanced & tools",
    "planned-session-types": "Advanced & tools",
    "validate":              "Advanced & tools",
    "eval":                  "Advanced & tools",
    "clean":                 "Advanced & tools",
}

# Flags carried by every subcommand that don't inform a new user. Hidden
# from the human render so the per-command flag line shows the
# meaningful surface only.
_FLAGS_HIDDEN_FROM_HUMAN: frozenset[str] = frozenset({
    "--json",   # default-emit alias on capabilities; agent-doc convention elsewhere
    "--text",   # opt-out alias on JSON-default commands
    "--help",   # argparse default; never registered through annotate_contract anyway
})

_HUMAN_PREAMBLE = """\
# hai — quick reference

This is the at-a-glance overview of every `hai` subcommand grouped by
the workflow stage it belongs to. For the agent-facing JSON manifest
(authoritative), use `hai capabilities --json`. For the dense
contract-doc Markdown table (every annotation column), use
`hai capabilities --markdown`.
"""


def render_human(manifest: dict[str, Any]) -> str:
    """Return a one-page human-readable overview of the manifest.

    Output is deterministic: rows sort lexicographically within each
    category, categories render in `_CATEGORY_ORDER`, and the
    no-jargon style omits mutation/idempotent/JSON-mode columns. The
    target reader is a new user who has just run `pipx install
    health-agent-infra` and wants to understand the surface in under
    a minute.
    """

    # Bucket commands by category. An unmapped top-level prefix falls
    # through to "Advanced & tools" — that bucket is the safe default,
    # not a silent omission.
    buckets: dict[str, list[dict[str, Any]]] = {c: [] for c in _CATEGORY_ORDER}
    for row in manifest["commands"]:
        top = _top_level_prefix(row["command"])
        category = _CATEGORY_MAP.get(top, "Advanced & tools")
        buckets[category].append(row)

    lines: list[str] = [_HUMAN_PREAMBLE.rstrip(), ""]
    lines.append(
        f"*{len(manifest['commands'])} commands; "
        f"hai {manifest['hai_version']}*"
    )
    lines.append("")

    for category in _CATEGORY_ORDER:
        rows = buckets[category]
        if not rows:
            continue
        lines.append(f"## {category}")
        lines.append("")
        lines.append(f"_{_CATEGORY_BLURB[category]}_")
        lines.append("")
        for row in sorted(rows, key=lambda r: r["command"]):
            lines.append(_row_to_human(row))
        lines.append("")
    return "\n".join(lines)


def _top_level_prefix(command: str) -> str:
    """Return the first segment after `hai ` (e.g. `hai intent add` → `intent`)."""

    parts = command.split()
    return parts[1] if len(parts) > 1 else ""


def _row_to_human(row: dict[str, Any]) -> str:
    """Render one command row as a Markdown bullet with a one-line description."""

    description = (row["description"] or "").strip()
    # First sentence only — keeps the human render scannable. Falls back
    # to the full string if no sentence boundary is present.
    first_stop = description.find(". ")
    summary = description[: first_stop + 1] if first_stop >= 0 else description
    summary = " ".join(summary.split())

    flags = [
        f["name"]
        for f in row.get("flags") or []
        if f.get("name") and f["name"] not in _FLAGS_HIDDEN_FROM_HUMAN
    ]
    flag_suffix = ""
    if flags:
        # Cap at 4 to keep each row to two visual lines on an 80-col
        # terminal; the JSON manifest is the authoritative full list.
        shown = flags[:4]
        suffix = ", ".join(f"`{f}`" for f in shown)
        if len(flags) > 4:
            suffix += ", …"
        flag_suffix = f"  \n  Flags: {suffix}"

    return f"- **`{row['command']}`** — {summary}{flag_suffix}"
