# Host Agent Contract

**Audience.** A shell-capable host agent (Claude Code, Codex, Anthropic
Agent SDK, an open equivalent, or a future MCP client) wiring up
Health Agent Infra for the first time. The maintainer's daily-driver
host is Claude Code; nothing on this page is Claude-specific.

**One-line frame.** Health Agent Infra is the local plugin/runtime
wrapper around a personal-health agent. The agent stays the
conversational operator. `hai` is the governed tool surface that
declares what commands exist, which substrates each command may
mutate, what each output must validate against, and which authority
the runtime refuses to grant the agent.

This page consolidates what an integrator currently has to assemble
from `AGENTS.md`, [`agent_integration.md`](agent_integration.md),
[`agent_cli_contract.md`](agent_cli_contract.md),
[`glossary.md`](glossary.md), and the packaged skills. It is the read
that lets a host agent operate the runtime safely without re-reading
six docs every session.

For the universal coding-agent operating contract (used by Codex /
Claude Code in the maintainer's working tree itself) read
[`AGENTS.md`](../../AGENTS.md). This file is the **operating** read for
*hosting* the runtime; `AGENTS.md` is the operating read for
*contributing* to the runtime.

## 1. Read the manifest first

Every session must start by reading the machine-readable command
contract:

```bash
hai capabilities --json
```

The manifest emits, per subcommand (verbatim JSON field names):

- `command` (e.g. `hai propose`) - the canonical invocation string.
- `mutation` - one of the declared mutation values (`read-only`,
  `writes-sync-log`, `writes-state`, `writes-memory`,
  `writes-skills-dir`, `writes-credentials`, `writes-config`,
  `interactive`; the schema also reserves `writes-audit-log`, which no
  command currently emits — proposal/review writes pair audit logging
  with state writes and land as `writes-state`). See section 2. **In
  this doc's prose, "mutation class" is the concept name; the JSON
  field is literally `mutation`.**
- `agent_safe` - boolean. See section 4.
- `idempotent` - `yes`, `no`, `yes-with-replace`. Determines whether
  retry on TRANSIENT exit is safe.
- `json_output` - whether stdout is structured. Read it before
  parsing.
- `exit_codes` - the subset of the runtime's stable taxonomy this
  command emits.
- `flags` - flag schema, including `choice_metadata` blocks (e.g.
  `--source` flags carry `garmin_live.reliability == "unreliable"`).

The manifest is authoritative. If a command is not in the manifest, it
does not exist for the agent. Do not guess; do not improvise.

The human mirror at
[`agent_cli_contract.md`](agent_cli_contract.md) is regenerated from
this manifest on every release. The
[`intent-router`](../../src/health_agent_infra/skills/intent-router/SKILL.md)
skill exists specifically to read the manifest as its source of truth.

## 2. Mutation classes - operational meaning

Every `hai` subcommand declares a mutation value (the JSON field is
literally `mutation`; this doc calls the concept "mutation class").
The class is an operational contract, not documentation decoration.
The runtime defines nine classes in the manifest schema; eight
currently appear on at least one command, and `writes-audit-log` is
schema-reserved:

| Class | What it may touch | Operational meaning for the agent |
|---|---|---|
| `read-only` | Stdout, or a caller-named output file (e.g. backup destination) | Safe to retry. Never mutates SQLite, JSONL, keyring, or config. Examples: `hai today`, `hai explain`, `hai stats`, `hai capabilities`, `hai doctor`, `hai backup`, `hai export`. |
| `writes-sync-log` | `sync_run_log` freshness rows only | Pull-class command; appends a sync record without mutating canonical state. Example: `hai pull`. |
| `writes-audit-log` | JSONL audit logs (no primary state mutation) | Reserved class in the manifest schema; proposal / review writes currently pair audit logging with state writes (i.e. land as `writes-state`). |
| `writes-state` | SQLite state DB plus governed JSONL audit sidecars | Atomic at the single-command level. May fail with `USER_INPUT` (validator rejection) or `TRANSIENT` (DB lock). Never retry blindly on `USER_INPUT`. Examples: `hai intake *`, `hai propose`, `hai synthesize`, `hai review record`, `hai target *`, `hai state *` write paths. |
| `writes-memory` | The `user_memory` ledger | Append-only with archive timestamps; agent may write but should never replace silently. Examples: `hai memory set`, `hai memory archive`. |
| `writes-skills-dir` | Local skills install directory under `~/.claude/skills/` (or `--dest`) | Setup-time only; not a runtime path. Example: `hai setup-skills`. |
| `writes-credentials` | OS keyring, or null backend on Linux without a registered backend | Requires explicit user action; do not pass credentials through the agent. Examples: `hai auth intervals-icu`, `hai auth garmin`, `hai auth remove`. |
| `writes-config` | Threshold/config files under `~/.config/hai/` (override via `hai config init --path`) | Safe but determinism-affecting. After a config change, read `hai config diff` before next decisioning. Example: `hai config init`. |
| `interactive` | Live human setup flow | **Not agent-invocable.** Examples: `hai init` (use the `--guided` form when the user runs it themselves). |

The classes also map directly onto skill `allowed-tools` frontmatter:
each packaged skill scopes itself to a specific mutation class +
command pattern. A skill with
`allowed-tools: [Bash(hai propose --domain recovery *)]` cannot mutate
config, credentials, memory, or skills-dir at all, by construction.

## 3. The proposal-gate three-state machine

`hai daily` is the normal driver loop. Run it, fill missing proposals
if it asks for them, run it again. The orchestrator surfaces a
`proposal_gate` block with one of three states:

| State | What happened | What the agent does next |
|---|---|---|
| `awaiting_proposals` | No proposals in `proposal_log` for `(for_date, user_id)` | Read the snapshot. For each expected domain, invoke the per-domain readiness skill, compose a `DomainProposal`, validate locally, and call `hai propose --domain <d> --proposal-json <p>`. Then re-invoke `hai daily`. |
| `incomplete` | Some proposals present, at least one missing | The state carries a `hint` field listing the missing domains. Post proposals only for the named missing domains, then re-invoke `hai daily`. Do not re-post proposals already in `proposal_log`. |
| `complete` | All expected proposals present | The runtime advances to synthesis (Phase A -> optional skill overlay -> Phase B -> atomic commit). The agent narrates the result via `hai today` / `hai explain`. |

Two important consequences:

- The agent must not skip `hai daily`'s proposal gate to invoke
  `hai synthesize` directly. `hai synthesize` will refuse with
  `USER_INPUT` if no proposals exist for the day.
- The agent must not re-post a proposal for a domain already in
  `proposal_log`. Use `--supersede` only when the user explicitly
  asks to re-author the day.

## 4. `agent_safe` and what is *not* agent-safe

A command marked `agent_safe == false` in the manifest is one the
host agent must not invoke unprompted. The user must explicitly
request the action. The two main classes of `agent_safe == false`
commands today:

- **W57-gated commits.** `hai intent commit`, `hai intent archive`,
  `hai target commit`, `hai target archive`. The agent may **propose**
  intent or target rows (which land in a `proposed` state); only the
  user may **activate** or **deactivate** them. See section 6.
- **Credential mutation.** `hai auth intervals-icu`, `hai auth garmin`,
  `hai auth remove`. The user runs these; the agent does not pass
  secrets through the chat surface.

`agent_safe == true` does **not** mean ungated or unvalidated. It
means "safe to invoke when the upstream conditions are met." Every
agent-safe mutation is still validated at its determinism boundary;
schema rejection still produces `USER_INPUT`.

## 5. Exit-code handling - never retry blindly

Every `hai` subcommand returns from a stable taxonomy. The taxonomy
is exhaustive at [`cli_exit_codes.md`](cli_exit_codes.md); the
agent-relevant rules:

| Exit | Meaning | Agent response |
|---|---|---|
| `OK` | Success | Continue. If `json_output`, parse stdout. |
| `USER_INPUT` | Caller-fixable: bad flag, missing user-supplied state, validator rejection, or governed refusal. Stderr carries an `invariant=<id>` tag. | **Do not retry blindly.** Read the invariant id; ask the user for the missing state; or run the next safe setup command. Examples: validator says `followed_recommendation_must_be_bool` -> ask user yes/no, do not pass `"yes"` as a string. |
| `TRANSIENT` | Recoverable I/O issue (DB lock, network blip). Idempotency tells you whether to retry. | If `idempotent: yes` or `idempotent: yes-with-replace`, retry once with backoff. If `idempotent: no`, surface the failure to the user. |
| `NOT_FOUND` | A requested entity does not exist (e.g. `hai explain` for a date with no plan). | Tell the user; do not fabricate a plan. |
| `INTERNAL` | Runtime bug. | Surface to user with the stderr trace. Do not work around. |

The fourth gate `hai daily` exposes (proposal completeness) is
*operationally* a USER_INPUT-shaped halt: the agent must do work (post
proposals) before re-invoking. See section 3.

`USER_INPUT` covers three operationally distinct sub-cases that all
share the exit class. Distinguish them by reading the `invariant=<id>`
stderr tag (and, for argparse-style failures, the leading `usage:`
line):

- **Argparse / caller-shape errors** — missing required flag, bad
  enum value, malformed JSON. Stderr opens with `usage: hai ...`
  followed by the flag the parser rejected. Fix by adjusting the
  invocation; do not ask the user.
- **Validator-rejection errors** — payload reached the determinism
  boundary (`hai propose` / `hai synthesize` / `hai review record` /
  intake) and an invariant fired. Stderr carries `invariant=<id>`
  (e.g. `invariant=followed_recommendation_must_be_bool`,
  `invariant=action_enum`). Fix by asking the user for the right
  value or correcting the agent-side payload — never coerce.
- **Governed refusals** — the runtime refused to take an action that
  would violate a governance invariant (W57 commit/archive without
  user gate, fixture-data into canonical state without explicit
  opt-in, clinical-claim language). Surface the refusal to the user
  verbatim; do not retry through a "looser" path.

`TRANSIENT` is a separate class: I/O hiccup, not caller error. It is
the only retry-allowed exit (governed by the manifest's `idempotent`
field).

## 6. W57 in plain language

The runtime refuses to let the agent silently activate or deactivate
the user's goals.

- The user authors `intent_item` and `target` rows directly via
  `hai intent` / `hai target` subcommands; these land active.
- The agent may *propose* `intent_item` and `target` rows by writing
  rows in a `proposed` state. **Activation requires a user-gated
  commit (`hai intent commit` / `hai target commit`).** Archival
  works the same way: agent-proposed archive does not deactivate; the
  user must commit the archive.
- The W57 invariant is mechanically enforced: the commit/archive
  subcommands are marked `agent_safe == false`, and the underlying
  state functions reject mutation paths that bypass the user gate.

The reason: an agent must not be able to silently change what the
user is trying to do. Intent and target are user-owned; the runtime
is the wrapper, not the principal.

## 7. Source freshness and fixture-vs-live

Three hard rules:

- **Live sources.** `intervals_icu` is the supported live source.
  Configure with `hai auth intervals-icu`; verify with
  `hai auth status`.
- **Garmin live is structurally marked unreliable.** The capabilities
  manifest exposes
  `commands[hai pull].flags[--source].choice_metadata.garmin_live`
  with `reliability == "unreliable"`, `reason`, and
  `prefer_instead == "intervals_icu"`. `_resolve_pull_source` emits a
  stderr warning at resolution time. An agent reading the manifest
  must pattern-match on `choice_metadata`, not the help-text prose.
- **CSV fixture is default-deny.** The committed CSV fixture is for
  demos and smoke tests. It is not a default for canonical state. The
  `hai pull` and `hai daily` paths refuse to canonicalise CSV-fixture
  evidence into the production state DB without explicit opt-in or a
  demo / non-canonical destination.

The agent must not paper over missing live evidence with fixture
rows. Coverage gaps are surfaced as `coverage_band` and `missingness`
on the snapshot; honour them rather than fabricating.

## 8. What the agent must never do

| Never | Enforcement | Rationale |
|---|---|---|
| Edit SQLite or JSONL files directly | Skills are sandboxed via `allowed-tools`; runtime mutation surfaces are the only sanctioned path | Bypass would corrupt the audit chain and skip validators |
| Invent an action outside the per-domain v1 enum | `core/writeback/proposal.py :: validate_proposal_dict` rejects with `invariant=action_enum` | Recommendation actions are bounded for governance |
| Override `policy_result.forced_action` or `capped_confidence` | Runtime stamps these into the snapshot; skills consume; proposal validator rejects mismatched action | R-rules are mechanical, not advisory |
| Activate or deactivate user intent/target rows | `agent_safe == false`; W57 enforcement at the state-function boundary | User owns goals; agent owns conversation |
| Use diagnosis-shaped or clinical language | `safety` skill prompt + lint at proposal/recommendation boundary | Not a medical device |
| Treat fixture evidence as canonical | `hai pull` / `hai daily` default-deny on CSV; explicit opt-in required | Honest source tracking |
| Treat missing evidence as confidence | `coverage_band == insufficient` forces `defer_decision_insufficient_signal`; sparse coverage caps confidence at moderate | Calibration over-confidence is the dominant failure mode |
| Recompute classifier bands or X-rule firings inside a skill | `hai state snapshot` already computed `classified_state` and `policy_result` | Skill leakage into code's territory |
| Auto-tune thresholds from review outcomes | No code path exists; ROADMAP "Explicitly Out Of Scope" + W57 | Hidden learning loop violates auditability |

## 9. The audit chain the agent narrates from

Every committed plan reconciles across four persisted layers. Read
them rather than re-deriving:

1. `proposal_log` - what the per-domain skill proposed.
2. `planned_recommendation` - the aggregate pre-X-rule plan,
   captured inside the synthesis transaction.
3. `daily_plan` + `x_rule_firing` + `recommendation_log` - the final
   adapted plan with its mutation history.
4. `review_event` + `review_outcome` - what happened next morning.

`hai explain --for-date <d> --user-id <u>` renders the chain from
persisted rows alone. It opens no write transaction, recomputes
nothing, and fabricates nothing. See
[`explainability.md`](explainability.md).

When the user asks "why did you tone down my run?" the agent reads
`hai explain` and narrates the firing's `human_explanation` verbatim
- never improvises.

**Get IDs from persisted surfaces; never invent them.** When the
agent needs a `recommendation_id`, `daily_plan_id`,
`review_event_id`, `intent_id`, or `target_id` to feed into the next
command (e.g. `hai review record --outcome-json` carrying a
`review_event_id`), it must read that id from `hai today`,
`hai explain`, the relevant `hai stats` view, or the manifest-
declared JSON output of the previous mutation. It must not generate
ids client-side, fuzzy-match on substrings, or reuse an id from a
different `(for_date, user_id)`. The runtime assigns canonical ids;
the agent's job is to thread them, not author them.

## 10. Skills are part of the contract

The fourteen markdown skills under
`src/health_agent_infra/skills/` are not prose decoration. They are
operational boundaries.

- Each skill declares `allowed-tools` in its frontmatter; that scope
  is what the host agent must respect when delegating.
- Six readiness skills (one per domain) own *judgment*: choose an
  action from the already-bounded enum, compose rationale referencing
  the snapshot's bands, surface uncertainty.
- `daily-plan-synthesis` reconciles per-domain proposals into a
  joint daily-plan rationale - composition only, no mutation.
- `intent-router` is the natural-language -> CLI workflow mapper.
  Read the capabilities manifest as truth; never compose mutations
  from intuition.
- `safety` defines refusal language and clinical-claim boundary.
- `merge-human-inputs`, `strength-intake`, `review-protocol`,
  `reporting`, `expert-explainer` are cross-cutting.

A skill that runs arithmetic the runtime already ran is a bug. A
runtime path that improvises coaching prose is a bug. The boundary
is mutual.

## 11. Quick reference

```bash
# Discover the contract (JSON field names are `command` and `mutation`)
hai capabilities --json | jq '.commands[] | {command, mutation, agent_safe}'

# Verify local setup
hai doctor

# Daily loop driver
hai daily --as-of <YYYY-MM-DD>            # may stop at proposal gate
# (post any missing DomainProposals)
hai propose --domain <d> --proposal-json <p>
hai daily --as-of <YYYY-MM-DD>            # advance through synthesis

# Read what was committed
hai today
hai explain --for-date <YYYY-MM-DD> --user-id <u>
hai explain --for-date <YYYY-MM-DD> --user-id <u> --operator   # dense audit-chain dump

# Record outcomes the next morning
hai review record --outcome-json <p>
hai review summary --domain <d>
```

The full command list with mutation classes and agent-safe flags is
generated at
[`agent_cli_contract.md`](agent_cli_contract.md). The wider
architecture sits at [`architecture.md`](architecture.md). The state
shape is at [`state_model_v1.md`](state_model_v1.md). Refusal
specifics live in the [`safety` skill](../../src/health_agent_infra/skills/safety/SKILL.md).
