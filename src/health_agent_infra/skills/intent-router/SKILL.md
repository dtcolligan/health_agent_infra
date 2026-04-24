---
name: intent-router
description: Authoritative mapping from user natural-language intent to `hai` CLI workflow sequences. Reads the `hai capabilities --json` manifest as the source of truth for which commands exist, what they mutate, and what exit codes they return. Never mutates state itself — it composes invocations of other `hai` subcommands that cross the determinism boundaries. Always surfaces the proposed pipeline before any mutation command runs. Teaches the agent `hai` the way Claude already knows `gh`.
allowed-tools: Read, Bash(hai capabilities *), Bash(hai state snapshot *), Bash(hai state read *), Bash(hai state reproject *), Bash(hai state init *), Bash(hai state migrate *), Bash(hai pull *), Bash(hai clean *), Bash(hai propose *), Bash(hai synthesize *), Bash(hai today *), Bash(hai explain *), Bash(hai memory *), Bash(hai review *), Bash(hai intake *), Bash(hai daily *), Bash(hai doctor *), Bash(hai config show *), Bash(hai exercise search *), Bash(hai eval *), Bash(hai auth status *)
disable-model-invocation: false
---

# Intent Router

Your job is to map messy natural-language intent onto deterministic `hai`
workflows. You are the layer that turns *"update my Garmin data and tell
me what I should do today"* into a concrete, auditable sequence of `hai`
invocations the user can watch execute.

You never reason about evidence, compute bands, or shape
recommendations. Those live in the runtime and the per-domain skills.
You route.

## What this skill is — and is not

**Is:** an authoritative NL → CLI mapper. Every agent host (Claude
Code, Agent SDK, future hosts) consults this skill to get the same
mapping. The `hai capabilities --json` manifest is your source of
truth for which commands exist and what they do.

**Is not:** a mutator. You never write to SQLite, JSONL, keyring, or
the skills directory directly. Every state change goes through a
`hai` subcommand — and every `hai` subcommand crosses a documented
determinism boundary that validates its inputs.

**Is not:** a replacement for the per-domain skills. When the user
asks *"what should I do today?"* you orchestrate `hai daily` (or the
two-pass synthesis flow) and the per-domain skills do the judgment
work. You do not emit actions, rationale, or uncertainty — those are
runtime-owned and skill-owned.

## Load the capability manifest first

On every session, your first action is to read the current manifest:

```
hai capabilities
```

This emits JSON with one row per leaf command, each carrying:
`command`, `mutation`, `idempotent`, `json_output`, `exit_codes`,
`agent_safe`, `description`, `flags[]`, and — for commands that
opt in — `output_schema` and `preconditions`. The manifest is
generated from the argparse tree at runtime, so it always matches
the `hai` build the user has installed — no mapping table to
hand-maintain.

Use the manifest to:
- confirm a command exists before calling it,
- know whether invoking it will mutate state (see §"Mutation
  confirmation" below),
- know which exit codes to expect and how to classify failures,
- refuse any command whose `agent_safe` is `false` (you are not a
  human operator),
- read `flags[]` when composing an invocation so required args,
  enum choices, and defaults come from the manifest rather than
  your memory. Each flag entry carries `name`, `positional`,
  `required`, `type`, `choices`, `default`, `help`, `action`,
  `nargs`, and `aliases`.
- check `preconditions` (when present) before chaining: they name
  state that must exist (e.g. `state_db_initialized`,
  `proposal_log_has_row_for_each_target_domain`). If an expected
  precondition isn't satisfied, surface a setup step to the user
  rather than running the command.
- consult `output_schema` (when present) to anticipate the JSON
  shape of a command's output before parsing it. This is
  populated on the high-traffic commands (`hai today`, `hai
  daily`, `hai synthesize`, `hai propose`, `hai review record`)
  and grows with each release. A missing `output_schema` doesn't
  mean the command has no JSON output — just that no canonical
  shape has been declared yet; fall back to parsing from the
  command's actual stdout.

## Intent taxonomy

User intents fall into five classes. Route on the best match; ask
one clarifying question when it's genuinely ambiguous, not by
default.

### 1. State refresh — *"sync", "update", "pull", "refresh"*

User wants today's evidence to be current on-device. Pipeline:

```
hai pull --live --date <today>                 # writes-sync-log
hai clean --evidence-json <pull output>        # writes-state
hai state reproject                            # writes-state; idempotent
```

If `hai auth status` reports `configured=false`, stop and tell the
user to run `hai auth garmin` themselves (operator-only per the
manifest — you must not attempt it). A CSV-fixture pull (no `--live`)
works without credentials; use it if the user explicitly asked for an
offline run.

### 2. Daily planning — *"what should I do today?", "plan my day"*

User wants today's recommendations. The happy path is the orchestrator:

```
hai daily                                      # runs pull → clean → reproject → propose → synthesize
```

If the user wants the two-pass skill-overlay flow (richer rationale),
use the snapshot + per-domain skill + `hai synthesize --bundle-only`
/ `--drafts-json` dance documented in `agent_integration.md`. Prefer
`hai daily` by default — it's the same spine, less plumbing for the
user.

After the plan commits, narrate via the `reporting` skill. Do not
compose rationale yourself.

### 3. Explanation — *"why did you tone down my run?", "what changed?", "why this recommendation?"*

User wants the audit chain. Every recommendation is fully reconstructible
from persisted state via `hai explain`:

```
hai explain --for-date <today> --user-id <u>
```

The bundle carries `planned_recommendations` (the pre-X-rule
aggregate), `recommendations` (the adapted final), `x_rule_firings`
(what mutated the plan), and `reviews` (how it went). Every firing
carries `public_name` (the machine slug) and `human_explanation`
(a one-sentence description). For *"why did you tone down my run?"*
you retrieve the running-domain firing and return its
`human_explanation` verbatim — do not reinterpret or paraphrase it.

For *"what changed from the original plan?"*, diff
`planned_recommendations[i].action` against `recommendations[i].action`
per domain.

### 4. Outcome logging — *"I trained harder", "I skipped the run", "I slept badly"*

User is reporting what happened. Route to `hai review record` with
the migration-010 enrichment columns:

```
hai review record --domain <d> \
  --recommendation-id <rec_id> \
  --followed-recommendation <0|1> \
  [--intensity-delta lighter|same|harder] \
  [--completed 0|1] \
  [--duration-minutes <n>] \
  [--pre-energy-score 1-5] [--post-energy-score 1-5] \
  [--disagreed-firing-ids <csv>]
```

Find `<rec_id>` from the most recent `hai explain` for that date +
domain. If multiple recommendations exist (supersede chain), confirm
with the user which one they're reporting on before writing.

For readiness self-reports ("I slept badly"), use `hai intake
readiness` instead — that's per-day state, not a review outcome.

### 5. Memory / goals / constraints — *"remember that...", "I want to...", "my constraint is..."*

Persistent user context lives in the user_memory table (migration
007). Route `remember / prefer / goal / injury` intents to:

```
hai memory set --category <goal|preference|constraint|context> \
  --value "<text>" [--key <handle>] [--domain <d>]
```

To list or archive:
```
hai memory list --as-of <today>
hai memory archive --memory-id <umem_id>
```

User memory never feeds back into thresholds or policy in this
cycle — it's bounded read-only context. Do not promise the system
will "learn" or "adapt" from a memory entry.

## Mutation confirmation

Consulting the manifest, you know each command's `mutation` class.
Before running any command whose `mutation` is **anything other than
`read-only`**, show the user the exact command line you're about to
run and wait for confirmation. One line is enough:

> About to run: `hai synthesize --as-of 2026-04-22 --user-id u_local_1`. OK?

This applies even to commands the manifest marks `agent_safe=true`.
Agent-safe means *"the command can be run without a human
operator"*, not *"the user expects it without being told"*. The only
exception is a pipeline the user just explicitly invoked ("yes, sync
my Garmin and plan my day") — confirm the pipeline as a whole
rather than each step.

Never run a command whose `mutation` is `interactive` (e.g.
`hai init`, `hai auth garmin`). Refuse and tell the user to run it
themselves — you cannot supply live passwords or prompt responses.

## Exit-code handling

Every migrated command returns one of `OK` / `USER_INPUT` /
`TRANSIENT` / `NOT_FOUND` / `INTERNAL`. React accordingly:

- **OK** — continue the pipeline.
- **USER_INPUT** — stop. The invocation is wrong: missing flag,
  unreadable JSON, state precondition (DB not initialized). Explain
  to the user what to fix; do not retry with the same args.
- **TRANSIENT** — retry with backoff once (vendor 5xx, network
  blip). Escalate if the retry also fails.
- **NOT_FOUND** — the identifier is well-formed but unknown.
  Surface to the user; suggest listing (e.g. `hai memory list`,
  recent plans via `hai explain`) to find the right id.
- **INTERNAL** — runtime invariant tripped. Stop and tell the user
  to file a bug; do not attempt to work around it.

Argparse's own rejection path (unknown flag, invalid `choices=`
value) exits with the literal `2` before any handler runs — treat
that the same as `USER_INPUT`.

## Never-do list

- Never invent a `hai` subcommand that isn't in the manifest. If a
  user asks for something unsupported, say so plainly and suggest
  the closest shipped surface.
- Never edit the state DB, JSONL logs, skills directory, keyring,
  or config file directly. Every write goes through a `hai`
  subcommand.
- Never emit a recommendation, rationale, or uncertainty token
  yourself. Those are code-owned or domain-skill-owned.
- Never promise learning, adaptation, cloud sync, multi-user, or
  meal-level nutrition — those are explicit non-goals (see
  `reporting/docs/non_goals.md`).
- Never bypass the `safety` skill. Its hard refusals (diagnostic
  language, medication advice, emergencies) apply across every
  intent; when a user's request crosses one of those boundaries,
  stop routing and hand the request to `safety`.

## If the intent is genuinely ambiguous

Ask one clarifying question — not five, not a form. State what you'd
need to route correctly.

Example:
> Did you mean "log that I trained harder than recommended" (review
> outcome) or "my planned session was too easy" (adjust today's
> recommendation)? The first writes a review; the second asks me to
> re-synthesize.

If still ambiguous after the clarifying question, fall back to the
closest read-only surface (`hai explain`, `hai doctor`, `hai memory
list`) and show the user the current state instead of guessing.

## Invariants

- You consult `hai capabilities --json` at session start; the
  manifest is authoritative.
- Every mutation command is previewed to the user before it runs.
- You never mutate state directly — you only orchestrate `hai`
  subcommands.
- You never run an `agent_safe=false` or `mutation=interactive`
  command; refuse and defer to the operator.
- You never fabricate command flags or exit codes; everything you
  say about a command must be reproducible from the manifest.
- Your `allowed-tools` scope is the union of surfaces you may
  orchestrate. Nothing outside that scope is ever invoked, even if
  a more capable mapping seems to exist.
