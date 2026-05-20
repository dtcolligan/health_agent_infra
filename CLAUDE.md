@AGENTS.md

# Claude Code session-start

Read in order: `PAPER.md` → `AGENTS.md`. The `@AGENTS.md` import above
keeps the operating contract visible on every session.

`PAPER.md` is the single source of truth for active scope, calendar,
decisions, mechanism inventory, hypotheses, model roster, threat
model, and engineering plan. Update it in place when those change;
do not create new planning files (D-13 in `PAPER.md` is binding).

## Multi-agent default

Other agents (Codex and possibly others) work this tree in parallel.
Default posture per AGENTS.md "How We Work": confirm whose work is in
the tree before editing, audit handoffs rather than trusting summaries,
and stage only what you authored this session.

## Common commands

```bash
PYTHONPATH=benchmark uv run pytest -q benchmark/verification/tests
PYTHONPATH=benchmark uv run python benchmark/governed_agent_bench/reproduce_offline.py --output-dir /tmp/gab_offline_repro
uv run pytest hai/verification/tests -q
MYPYPATH=benchmark:hai/src uvx mypy --explicit-package-bases benchmark/governed_agent_bench
uvx mypy hai/src/health_agent_infra
uv run hai capabilities --json
```

## Plan-mode triggers

- Editing `AGENTS.md` governance invariants or do-not-do list.
- Editing `PAPER.md` active decisions or mechanism inventory.
- Starting model-backed benchmark runs.
- Any commit that bundles files you did not author this session.
- Any `hai/src/health_agent_infra/cli/` change beyond a single
  help-text edit.

## Provenance

If you need to understand how a decision was reached or how HAI got
to v0.2.0, read `ARCHIVE/decisions_log.md` and `ARCHIVE/framing_v2/`.
These are not in the cold-start path.
