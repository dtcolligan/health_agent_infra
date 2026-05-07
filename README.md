# Runtime Contracts for Local Agents

This repository is organized around a research question: can runtime
contracts make smaller local models viable operators for bounded
workflows over sensitive user-owned data?

It contains three active artifacts:

| Artifact | Role |
|---|---|
| **Runtime contract** | The architecture/intervention: manifest, typed commands, mutation classes, `agent_safe`, schemas, proposal/commit separation, deterministic validation, policy gates, and audit. |
| **HAI** | The personal-wellness reference runtime, packaged as `health-agent-infra` and exposed through the local `hai` CLI. |
| **GovernedAgentBench** | The benchmark scaffold for measuring contract-governed agent operation. |

HAI is the first reference implementation. You talk to a
shell-capable agent; the agent invokes the local `hai` CLI. In
parallel, the runtime absorbs passive evidence - wearable data today
via intervals.icu, bloodwork and richer passive sources next - without
you having to narrate the data. `hai` is the governed tool surface
that tells the agent what it may do, which local substrates each
command may mutate, which outputs must validate, and which actions are
refused.

**Local-only by construction.** No telemetry, no hosted backend, no
cloud sync. State lives on your machine in SQLite + JSONL audit logs;
credentials live in the OS keyring. The package never phones home. A
host agent provider may still receive whatever context you give that
provider. That is the only path data leaves the machine, and it is not
something `hai` controls.

[![PyPI](https://img.shields.io/pypi/v/health-agent-infra)](https://pypi.org/project/health-agent-infra/)
[![Tests](https://img.shields.io/badge/tests-2943_passing-green)](verification/tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Status - runtime-contract research monorepo, with HAI `0.2.0` as
> the current reference runtime.** HAI is working
> maintainer-dogfooded single-user software, packaged around Claude
> Code as the first compatible host. The 2,943-test gate, 68-command
> CLI surface, and end-to-end audit chain are maintainer-verified.
> GovernedAgentBench is a new benchmark scaffold; it is not yet a
> release-ready benchmark.

## Repository Map

| Path | Purpose |
|---|---|
| [`src/health_agent_infra/`](src/health_agent_infra/) | HAI reference runtime and Python package. |
| [`benchmarks/governed_agent_bench/`](benchmarks/governed_agent_bench/) | GovernedAgentBench schemas, tasks, scorer, baselines, manifests, and reports. |
| [`research/runtime_contracts_paper/`](research/runtime_contracts_paper/) | Paper frame, draft, and execution plan. |
| [`reporting/docs/`](reporting/docs/) | HAI runtime/operator documentation. |
| [`reporting/plans/`](reporting/plans/) | Historical release planning and audit trail. |

![A user conversation flows into a shell-capable agent. The agent invokes the hai governed tool surface, which validates, gates, and audits every write before persisting to local SQLite state, JSONL audit logs, and the OS keyring/config. A direct write attempt from the agent to local state is shown crossed out at the boundary. A read-only return path through hai today, explain, review, and backup feeds back to the agent.](assets/product_boundary.png)

The agent proposes, explains, and asks for missing context. The
wrapper validates, gates, mutates, and records. Every persisted byte
goes through `hai`; nothing else has write authority.

Goals are user-owned, not agent-owned: the agent may *propose*
intent or training/nutrition target rows, but only the user can
*commit* them (governance invariant W57). The runtime enforces this
mechanically — the commit/archive paths are marked
`agent_safe == false` in the capabilities manifest.

## Why this exists

Agentic AI in personal health fails when the agent is asked to be
everything at once — the chat interface, the memory layer, the
data interpreter, the planner, the database, the validator, and
the auditor. The same prompt that produces good rationale on
Monday produces bad classification on Wednesday, and there is no
inspectable record of why.

Personal health is the wrong domain to lose that record. Decisions
compound: today's training load shapes tomorrow's recovery, this
week's sleep debt shapes next week's stress capacity. If the agent
is the only thing that "remembers" what it told you yesterday, you
don't have an agent — you have a rolling guess.

Health Agent Infra moves the durable parts — typed state,
projection, classification, policy, validation, atomic commit —
into local Python behind a CLI the agent calls. The model keeps
its strengths: conversation, clarification, uncertainty surfacing,
and prose rationale over a bounded action set. The runtime keeps
its strengths: deterministic interpretation and a reconstructable
audit chain.

![Two side-by-side panels. Left panel titled Agent does everything shows a single operator figure surrounded by an overlapping cluster of seven labeled circles — chat, memory, interpret, plan, validate, audit, DB — with tangled crossing arrows; subtitle: non-deterministic, no audit trail. Right panel titled Agent + governed runtime shows the same operator figure connected through a labeled hai governed tool surface gateway to a tidy column of five separate boxes — typed state, deterministic classifiers, policy rules, atomic commits, audit log — with simple parallel arrows; subtitle: deterministic, reconstructable.](assets/why_this_exists.png)

The contract is one line:

> **The agent proposes and explains; the runtime validates and commits.**

That single boundary is what turns "an LLM with health context"
into software you can audit, reproduce, and trust across sessions.

## Concrete shape

Three artifacts — real outputs from this repo, not mock-ups —
that show what the boundary means in practice.

### What the agent narrates from

`hai today --format plain` against a fresh user (first plan, no
history yet — golden-tested at
[`verification/tests/snapshot/golden/green_day.txt`](verification/tests/snapshot/golden/green_day.txt)):

```text
Today, 2026-04-24 — your first plan
===================================

6 prescriptions.

[PROCEED] Recovery — Proceed with your planned session.
-------------------------------------------------------

recovery_baseline.

Confidence: moderate.

Follow-up: How did today's recovery land?

[PROCEED] Sleep — Stick with your usual sleep schedule tonight.
---------------------------------------------------------------

sleep_baseline.

Confidence: moderate.

…(four more prescriptions: Running, Strength, Stress, Nutrition)…

Recorded as plan plan_2026-04-24_u_snap. This is your first plan —
confidence will sharpen as the system sees more of your training.
Run `hai daily` again tomorrow to keep the chain going.
```

The agent reads this; it doesn't generate it. Six prescriptions
(one per domain) come from the runtime, with reason tokens
(`recovery_baseline`), confidence (`moderate`), and a routed
follow-up question. Cold-start framing ("first plan", "history
will accumulate") is computed from persisted day-count, not
written by the LLM.

### What deterministic cross-domain reasoning looks like

11 cross-domain X-rules sit between domain proposals and the
final plan. They mechanically mutate drafts before any prose is
written. Example — **X4 `lower-body-sequencing-softens-run`**
([`reporting/docs/x_rules.md`](reporting/docs/x_rules.md) line 54):

> **Trigger.** Yesterday's strength = heavy lower body **AND**
> running intervals/tempo proposed today.
> **Target.** running. **Tier.** soften.
> **Action.** → `downgrade_to_easy_aerobic`.
> **Human explanation** (surfaced by `hai explain`): "Yesterday's
> heavy lower-body strength means today's hard run is softened to
> an easy aerobic effort."

X-rules fire deterministically from typed state, land as rows in
`x_rule_firing`, and are reconstructable per-day via `hai
explain`. None of the reasoning above runs in the model.

### What the agent reads as a contract

Every command in `hai capabilities --json` carries its own
mutation class, agent-safety flag, idempotency mark, and exit
codes. One entry, trimmed for readability (full snapshot at
[`verification/tests/snapshots/cli_capabilities_v0_1_13.json`](verification/tests/snapshots/cli_capabilities_v0_1_13.json)):

```json
{
  "command":      "hai auth intervals-icu",
  "description":  "Store Intervals.icu credentials in the OS keyring. Interactive by default; operator-only (requires a live API key).",
  "agent_safe":   false,
  "mutation":     "writes-credentials",
  "idempotent":   "yes",
  "exit_codes":   ["OK", "USER_INPUT"],
  "flags": [
    {"name": "--athlete-id",    "type": "str",  "required": false},
    {"name": "--api-key-stdin", "type": "bool", "required": false},
    {"name": "--api-key-env",   "type": "str",  "required": false}
  ]
}
```

`agent_safe: false` is mechanically enforced — the runtime refuses
this command under an agent token. 60 commands carry this
contract. The agent doesn't guess what's safe; it reads the
manifest.

## What hai enables for AI in personal health

`hai` is the substrate. The agent is the operator. Together they
give an LLM the authority and scaffolding to do real work inside a
personal-health loop without being asked to *also* be the
database, the validator, or the auditor.

### Already achieved

| Capability | What's working today |
|---|---|
| Multi-domain data intake | Six domains — recovery, running, sleep, stress, strength, nutrition — accept passive wearable data via intervals.icu and active intake via `hai intake` (gym sets, readiness, stress, food, free-text notes). |
| Local health-state database | A user-owned SQLite database accumulates typed state across days, schema-versioned and migration-tracked. |
| Daily health report | A typed snapshot the agent narrates from `hai today`: per-domain bands, source freshness, missing inputs, and the committed plan. |
| Daily recommendation | Bounded `DomainProposal` rows reconciled by 11 cross-domain X-rules into one auditable daily plan, anchored in user-committed intent. |
| Reconstructable audit chain | Every recommendation traces back through proposal, X-rule firing, planned, and final-plan rows via `hai explain`. |
| Source honesty | Stale data, fixture data, live-source failures, and missing credentials surface to the agent instead of collapsing into "no data" prose. |
| User-governed targets and intent | Agent-proposed goals require explicit user commit (governance invariant W57). |

### What hai will enable next

| Capability | Status |
|---|---|
| Weekly review loop | v0.2.0 — uses preserved evidence, proposals, X-rule firings, and outcomes to surface what's drifting. |
| Bloodwork and richer passive intake | Future — extends the same typed-evidence pattern beyond wearables. |
| Longer-horizon planning | Future — built on top of validated daily state and review memory; not before the loops below it are strong. |
| MCP-portable agent surface | Future — the capability manifest is already structured for hosts other than Claude Code. |
| Personal-calibration evaluation | Future — measure whether recommendations actually fit the individual user, not just whether the system is internally consistent. |

## How it feels to use

![A five-panel storyboard. Panel 1 — User asks: speech bubble reading Plan today. I slept badly and my quads are sore. Panel 2 — Agent reads the contract: agent figure pointing to a labeled tag hai capabilities --json. Panel 3 — Runtime gates and classifies: a labeled gateway hai governed tool surface containing icons for pull (wearable watch silhouette), classify (bands), and commit (database with checkmark). Panel 4 — Agent narrates: agent speech bubble reading easy run, sleep priority, lower stress load. Panel 5 — User asks why: question mark icon, agent figure with arrow to a labeled tag hai explain, unrolling-paper audit-chain motif. Banner above reads: User experience is conversational. System architecture is not.](assets/how_it_feels.png)

## Install and quickstart

Day-to-day use is conversational — your host agent invokes `hai`
for you. Run these once yourself to confirm the install and wire
up the live data path:

```bash
pipx install health-agent-infra
hai init             # interactive: on a TTY with no prior setup, auto-promotes to the guided flow (prompts for intervals.icu creds, authors initial intent + target, runs first wellness pull)
hai capabilities --human
hai doctor
hai daily
hai today
```

**`hai init` default behaviour (v0.1.18+).** When stdin is a TTY AND
your onboarding is incomplete (no active intent or target), bare
`hai init` auto-promotes to the guided flow. The flow is idempotent
— safe to rerun; it skips steps that already have state. Once
onboarding is complete, bare `hai init` stays a non-interactive
scaffold-and-go.

**Opt-outs for non-interactive callers.** CI runners, agent harnesses,
and automation that need bare init regardless of TTY have three
opt-out paths:

- No TTY (the default for piped / redirected stdin) — auto-skips the
  guided promotion.
- `--non-interactive` flag on `hai init`.
- `HAI_INIT_NON_INTERACTIVE=1` env var.

**Explicit-force.** `hai init --guided` still works as the explicit
spelling; useful when you want guided onboarding even if your state
already has some rows (the flow itself remains idempotent).

`intervals_icu` is currently the only working live source. Without
credentials, `hai pull` falls back to a committed CSV fixture for
demos and smoke tests. Garmin Connect support exists but is
rate-limited and Cloudflare-blocked — the capabilities manifest
marks it `reliability == "unreliable"` and the runtime warns at
resolution time. macOS uses the OS keychain; Linux uses
`keyrings.alt` with a defensive fallback when no desktop keyring
backend is registered.

After a fresh PyPI publish, CDN cache lag can briefly hide the
newest wheel — the pinned bypass form forces a fresh fetch:

```bash
pipx install --force \
  --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" \
  health-agent-infra
```

## Daily workflow (agent-operated)

`hai daily` is the current product loop. The agent runs it on the
user's behalf during a morning conversation; the runtime executes
the deterministic stages and tells the agent what still needs to
happen.

1. `pull` fetches passive evidence (intervals.icu wearable data)
   and records sync freshness.
2. `clean` normalizes evidence into typed accepted-state rows.
3. `snapshot` builds the six-domain state bundle.
4. `gaps` reports missing user-closeable inputs (the agent asks
   the user only for what the runtime says it actually needs).
5. `proposal_gate` reports whether bounded `DomainProposal` rows
   are still needed.

When proposals are needed, the agent uses the domain skills and
writes one bounded `DomainProposal` per expected domain with `hai
propose`. Then `hai daily` or `hai synthesize` completes the
atomic commit.

The same state and provenance model is what the weekly review,
longer-horizon planning, and future evaluation surfaces will
build on. The full integration contract is in
[`reporting/docs/agent_integration.md`](reporting/docs/agent_integration.md).

## Where the product stands

| Surface | Current value |
|---|---|
| Package version | `0.1.18` (2026-05-06) |
| Schema head | migration `026` (`body_comp` table added v0.1.17; unchanged at v0.1.18) |
| CLI surface | 67 annotated commands |
| Test gate at release | 2,733 passed, 5 skipped |
| Live source | intervals.icu only; Garmin marked `unreliable` |
| Posture | maintainer-dogfooded; W-2U-INSTALL closed verbal-only by post-v0.1.18 foreign-machine session; W-2U-WEARABLE + W-2U-DOGFOOD deferred to v0.4 review per CP-2U-GATE-SPLIT (AGENTS.md D16); v0.2.0 next-active |

For the terse release-truth map, read
[`reporting/docs/current_system_state.md`](reporting/docs/current_system_state.md).

## Domains

The current runtime covers six daily domains:

| Domain | What it covers |
|---|---|
| recovery | HRV/RHR readiness, soreness, energy, recovery constraints |
| running | recent activities, load, ACWR, session readiness |
| sleep | duration, debt, deprivation risk, recovery interaction |
| stress | self-report and stress trend signals |
| strength | gym set intake, exercise taxonomy, volume spikes |
| nutrition | daily macro totals and target-aware suppression |

Domain breadth is not the main claim. The main claim is that each
domain has a typed state representation, known evidence inputs,
classifier and policy boundaries, provenance, and an auditable
plan surface. New domains follow that pattern rather than
becoming more prompt text.

Nutrition is daily macros-only in v1, not meal-level tracking.
Body composition, micronutrients, clinical claims, and autonomous
diet plans are intentionally out of scope.

## Calibration

A fresh install can produce recommendations on day one, but useful
personal calibration takes history.

| Window | What to expect |
|---|---|
| Days 1–14 | Cold-start mode for running, strength, and stress; review recommendations consciously. |
| Days 14–28 | HRV and RHR baselines stabilize; recovery, sleep, and stress trends become useful. |
| Day 28+ | ACWR and strength volume ratios stop being mechanically inflated; trend bands begin carrying real signal. |
| Day ~90 | Steady-state personal calibration. |

Cold-start relaxation is asymmetric by design: running, strength,
and stress can soften some coverage blocks; recovery, sleep, and
nutrition do not relax into confident guesses when evidence is
thin.

## Where your data lives

| What | Default path | Override |
|---|---|---|
| State DB | `~/.local/share/health_agent_infra/state.db` | `$HAI_STATE_DB`, `--db-path` |
| Intake/proposal JSONL | `~/.health_agent/` | `$HAI_BASE_DIR`, `--base-dir` |
| Config | macOS: `~/Library/Application Support/hai/`; Linux: `~/.config/hai/` | `hai config init --path <p>` |

Run `hai doctor` to confirm resolved paths, schema version, source
freshness, credential status, and skill installation.

## Boundaries

The project is health-agent infrastructure, not an autonomous
doctor, coach, dietitian, wearable platform, or cloud service.

- It does not diagnose, treat, or make clinical claims.
- It does not let the agent silently activate goals, targets,
  intent, or final plans without the governed write path.
- It does not ask the LLM to be the database, validator, migration
  layer, source of truth, or policy engine.
- It does not replace wearables or source APIs; it records and
  governs the evidence they provide.
- It does not treat missing, stale, fixture, or unreliable data as
  equivalent to live evidence.
- It does not solve every health-agent failure case yet. Weekly
  review, longer-horizon planning, richer personal-guidance evals,
  and broader source-quality policy are still staged work.

## Main command groups (what the agent calls)

These are the surfaces the agent invokes through the governed CLI.
A human can run them directly for inspection or debugging.

```bash
# Evidence and daily orchestration
hai pull [--source intervals_icu|garmin_live|csv] --date <d>
hai clean --evidence-json <p>
hai daily [--domains <csv>]

# Proposals and synthesis
hai propose --domain <d> --proposal-json <p>
hai synthesize --as-of <d> --user-id <u>
hai synthesize --bundle-only

# State and audit
hai today
hai explain --for-date <d> --user-id <u>
hai state init | migrate | read | snapshot | reproject
hai doctor | stats | capabilities

# Intake, review, targets
hai intake gym|exercise|nutrition|stress|note|readiness ...
hai review schedule | record | summary
hai intent training add-session | sleep set-window | list | commit | archive
hai target set | nutrition | list | commit | archive
```

`intent commit`, `intent archive`, `target commit`, and `target
archive` are explicit user/operator authority paths — the
capabilities manifest marks them `agent_safe == false`, and the
runtime refuses to execute them under an agent token. This is the
W57 governance invariant.

The authoritative command surface is generated at
[`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md)
and from `hai capabilities --json`.

## Read next

| Reader | Best next docs |
|---|---|
| User trying the package | [`reporting/docs/current_system_state.md`](reporting/docs/current_system_state.md), [`reporting/docs/privacy.md`](reporting/docs/privacy.md), [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md) |
| Host-agent integrator | [`reporting/docs/host_agent_contract.md`](reporting/docs/host_agent_contract.md), [`reporting/docs/agent_integration.md`](reporting/docs/agent_integration.md), [`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md), [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| Runtime contributor | [`CONTRIBUTING.md`](CONTRIBUTING.md), [`reporting/docs/architecture.md`](reporting/docs/architecture.md), [`reporting/docs/domains/README.md`](reporting/docs/domains/README.md), [`reporting/docs/x_rules.md`](reporting/docs/x_rules.md) |
| Maintainer or release auditor | [`REPO_MAP.md`](REPO_MAP.md), [`AUDIT.md`](AUDIT.md), [`ROADMAP.md`](ROADMAP.md), [`CHANGELOG.md`](CHANGELOG.md), [`reporting/plans/README.md`](reporting/plans/README.md) |

## License

MIT. See [LICENSE](LICENSE).
