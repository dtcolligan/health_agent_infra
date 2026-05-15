@AGENTS.md

# Claude Code session-start

Read in order: `PAPER.md` → `AGENTS.md`. The `@AGENTS.md` import above
keeps the operating contract visible on every session.

`PAPER.md` is the single source of truth for active scope, calendar,
decisions, mechanism inventory, hypotheses, model roster, threat
model, and engineering plan. Update it in place when those change;
do not create new planning files (D-13 in `PAPER.md` is binding).

## Common commands

```bash
uv run pytest hai/verification/tests -q
uvx mypy hai/src/health_agent_infra
uv run hai capabilities --json
uv run hai doctor
```

## Plan-mode triggers

- Editing `AGENTS.md` governance invariants or do-not-do list.
- Editing `PAPER.md` active decisions or mechanism inventory.
- Any `hai/src/health_agent_infra/cli/` change beyond a single
  help-text edit.

## Provenance

If you need to understand how a decision was reached or how HAI got
to v0.2.0, read `ARCHIVE/decisions_log.md` and `ARCHIVE/framing_v2/`.
These are not in the cold-start path.
