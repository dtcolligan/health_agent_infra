# MCP scaffold — plan

- Author: Claude (Opus 4.7) with Dom Colligan
- Drafted: 2026-04-24
- Status: **plan only** (v0.1.4 stretch goal; code lands in v0.1.5+)
- Workstream: WS-C / non-goal for v0.1.4 per the README `§ Explicit non-goals`

---

## Goal

Expose the agent-safe `hai` CLI surface as an MCP (Model Context
Protocol) server so any agentic runtime — Claude Code, Claude Agent
SDK, Codex, future hosts — can drive the same deterministic runtime
that Claude Code drives today via `Bash(hai *)`.

The key insight: the capabilities manifest produced by
`hai capabilities --json` is already ~95% of an MCP tool-input
schema. WS-C's `flags[]`, `output_schema`, and `preconditions`
enrichment closes the remaining gap.

---

## The manifest → MCP tool mapping

Every leaf command in the manifest becomes one MCP tool. The tool
name is the command string with spaces collapsed
(`hai review record` → `hai_review_record`). Translation is
mechanical:

| Manifest field | MCP tool field |
|---|---|
| `command` | tool name (dashes → underscores) |
| `description` | tool description |
| `flags[]` | `inputSchema.properties` |
| `flags[].required` | `inputSchema.required[]` membership |
| `flags[].type` | JSON Schema `type` (str→string, int→integer, bool→boolean) |
| `flags[].choices` | JSON Schema `enum` |
| `flags[].default` | JSON Schema `default` |
| `flags[].help` | property `description` |
| `output_schema[exit_code]` | tool `outputSchema` (when present) |
| `agent_safe == false` | tool excluded from the server |
| `mutation` class | tool `annotations.readOnly`, `destructiveHint` |

Tools whose `mutation` is `interactive` (`hai init`) or whose
`agent_safe` is `false` do not ship in the MCP tool list. An MCP
client that needs those surfaces prompts the user to run them
directly.

---

## Scaffold file layout

```
src/health_agent_infra/mcp/
├── __init__.py
├── server.py              # MCP server entry point (stdio + sse transports)
├── tool_from_manifest.py  # Manifest row → MCP tool schema
├── handler.py             # Invoke the hai CLI for a given tool call
└── safeguards.py          # Mutation-confirm + preconditions gate
```

`server.py` is a thin wrapper around the anthropic MCP SDK (or the
community `mcp` package). Handlers shell out to `hai` subprocess-
style OR call `cli.main(argv)` in-process. In-process is faster and
keeps tracebacks legible, but subprocess gives the MCP runtime
isolation + kill-ability.

**Recommendation: in-process invocation** matching `safety/tests/e2e/conftest.py`'s existing `cli_main` pattern. Subprocess is a
v0.1.6 optimization if a single slow command blocks the server.

---

## Tool-call flow

1. Client sends `tools/call` with a name + inputs.
2. Server looks up the tool in the cached manifest.
3. `safeguards.py` runs:
   - If `preconditions` present, probe the DB / filesystem; if a
     precondition fails, return an MCP error with the specific
     precondition name so the client can surface the setup step.
   - If `mutation != "read-only"` and the client hasn't sent a
     `confirmed: true` side channel, return a dry-run preview
     (what command would run, what would mutate) rather than
     executing.
4. Inputs → argv list (match `flags[]` entries).
5. Call `cli.main(argv)` in a subprocess-like context to capture
   stdout / stderr / exit code.
6. If the exit code maps to OK, parse stdout as JSON using
   `output_schema` (when present); return as tool `content`.
7. If the exit code maps to a named failure (`USER_INPUT`,
   `NOT_FOUND`, etc.), return an MCP error with the exit code
   name so the client can pattern-match.

---

## Open questions (decide in v0.1.5)

1. **Transport.** stdio is enough for Claude Code; sse/HTTP needed
   if remote agents drive the server. Default to stdio; document
   sse as a follow-on.
2. **Mutation confirmation UX.** MCP tool-annotations carry
   `destructiveHint` as a boolean. The existing CLI uses a
   preview-then-confirm pattern. Mapping these cleanly needs a
   protocol decision: does the server enforce confirm, or does
   it trust the client?
3. **Multi-user.** Every tool-call currently takes `--user-id`.
   The MCP server could pin a user per connection or accept it
   per-call. Pinning is simpler; accept-per-call is more flexible.
4. **Streaming.** Long-running tools (`hai daily` on a slow pull)
   should stream progress. MCP supports tool-call progress
   notifications; we'd need to teach the cli to emit structured
   progress events, which is a separate feature.
5. **Credential access.** `hai auth garmin` writes to the OS
   keyring. MCP-hosted agents run in potentially unfamiliar
   contexts; prompting the user to run `hai auth garmin` directly
   is the safe default until we've thought through the security
   story.

---

## Dependencies before shipping the scaffold

Already landed:

- **`flags[]` enrichment** (WS-C) — every CLI arg is machine-
  readable. This is the biggest blocker; without it, tool input
  schemas are hand-written and drift.
- **`output_schema` + `preconditions`** (WS-C) — optional but
  valuable. Already populated on 5 high-traffic commands.
- **Stable exit-code taxonomy** — migrated months ago; MCP error
  mapping is a dict lookup.
- **`core.capabilities.build_manifest` is stable** — server
  imports it, no re-implementation needed.

Blocking:

- **Cross-agent invariants** for mutation confirmation — currently
  Claude Code surfaces a preview before `Bash(hai propose *)`
  executes, because the user sees the command. An MCP client
  without a visible command line needs a different contract.
- **A conformance test corpus** — replay recorded `hai` sessions
  through the MCP server + an MCP client; assert tool inputs
  match recorded argv and outputs match recorded JSON. Doable,
  not small.

---

## Delivery slices

**v0.1.5 slice 1 (minimum viable):**
- `server.py` over stdio, read-only tools only (`hai capabilities`,
  `hai today`, `hai explain`, `hai stats`, `hai doctor`,
  `hai state snapshot`). No mutation support.
- Proves the tool-from-manifest pipeline end-to-end without
  confronting the mutation-confirm design.

**v0.1.5 slice 2 (write path):**
- Add `hai propose`, `hai synthesize`, `hai review record`,
  `hai intake *` under an explicit `confirmed: true` input field.
- Write a `write-path MCP conformance` test category.

**v0.1.5 slice 3 (stretch):**
- Add orchestration tools (`hai daily`).
- Streaming progress events.
- Per-tool permission grants (the MCP client specifies which
  subset of tools the server exposes).

---

## Non-goals for v0.1.4

- No MCP server code ships in v0.1.4 itself; only this plan.
- No alternative client-library selection — the choice between
  the official anthropic MCP SDK and the community `mcp` package
  is a v0.1.5 decision.
- No MCP tool for `hai init` / `hai auth garmin` — those require
  human input and stay operator-mediated.

---

## Checklist for the agent who picks this up

- [ ] Verify `hai capabilities --json` is stable; bump
  `SCHEMA_VERSION` if the MCP schema diverges.
- [ ] Pin the MCP Python SDK version in `pyproject.toml`
  `[optional-dependencies] mcp = [...]`.
- [ ] Write `tool_from_manifest.py`. Test: every tool in the
  emitted MCP tool list corresponds 1:1 to a manifest command
  with `agent_safe=true`.
- [ ] Write `handler.py`. Test: round-trip a known command's argv
  + stdout through the handler; assert parity with direct
  `cli.main()` invocation.
- [ ] Write the slice-1 scaffold (read-only tools) and an E2E
  conformance test that drives `hai today` through the MCP
  server.
- [ ] Document the entry-point: `python -m health_agent_infra.mcp.server`.
- [ ] Update the intent-router skill with a note: "when the agent
  host supports MCP, the same manifest applies; the server
  exposes each agent_safe command as a tool."
