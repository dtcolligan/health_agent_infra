# HAI Reference Runtime

HAI is the personal-wellness reference runtime for the runtime-contract
research project. It is packaged as `health-agent-infra` and exposed
through the local `hai` CLI.

For the repo-wide research frame, start with
[`../../PROJECT_FRAME.md`](../../PROJECT_FRAME.md),
[`../../PROJECT_DECISIONS.md`](../../PROJECT_DECISIONS.md), and
[`../../PROJECT_OPERATING_MODEL.md`](../../PROJECT_OPERATING_MODEL.md).
This document is the HAI-specific reference-runtime operator manual.

## What HAI Is

HAI is the governed tool surface between a shell-capable host agent and
local user-owned state. A user talks to the host agent in natural
language; the agent invokes `hai`; the runtime validates, gates, mutates,
and records.

Personal wellness is the reference domain. The broader research claim is
contract-governed operation over sensitive user-owned structured data.

**Local-only by construction.** No telemetry, no hosted backend, no cloud
sync. State lives on your machine in SQLite plus JSONL audit logs;
credentials live in the OS keyring. The package never phones home. A host
agent provider may still receive whatever context you give that provider.
That is the only path data leaves the machine, and it is not something
`hai` controls.

![A user conversation flows into a shell-capable agent. The agent invokes the hai governed tool surface, which validates, gates, and audits every write before persisting to local SQLite state, JSONL audit logs, and the OS keyring/config. A direct write attempt from the agent to local state is shown crossed out at the boundary. A read-only return path through hai today, explain, review, and backup feeds back to the agent.](../../assets/product_boundary.png)

The agent proposes, explains, and asks for missing context. The wrapper
validates, gates, mutates, and records. Every persisted byte goes through
`hai`; nothing else has write authority.

Goals are user-owned, not agent-owned: the agent may propose intent or
training/nutrition target rows, but only the user can commit them. The
runtime enforces this mechanically: commit/archive paths are marked
`agent_safe == false` in the capabilities manifest.

## Why HAI Exists

Agentic AI in personal wellness fails when the agent is asked to be
everything at once: chat interface, memory layer, data interpreter,
planner, database, validator, and auditor. The same prompt that produces
good rationale on Monday can produce bad classification on Wednesday,
with no inspectable record of why.

HAI moves the durable parts into local Python behind a CLI the agent
calls: typed state, projection, classification, policy, validation, and
atomic commit. The model keeps conversation, clarification, uncertainty
surfacing, and prose rationale over a bounded action set.

![Two side-by-side panels. Left panel titled Agent does everything shows a single operator figure surrounded by an overlapping cluster of seven labeled circles: chat, memory, interpret, plan, validate, audit, DB; subtitle: non-deterministic, no audit trail. Right panel titled Agent + governed runtime shows the same operator figure connected through a labeled hai governed tool surface gateway to a tidy column of five separate boxes: typed state, deterministic classifiers, policy rules, atomic commits, audit log; subtitle: deterministic, reconstructable.](../../assets/why_this_exists.png)

The contract is one line:

> The agent proposes and explains; the runtime validates and commits.

## Concrete Runtime Shape

### What The Agent Narrates From

`hai today --format plain` against a fresh user emits a typed daily
surface for the agent to narrate from. The agent reads this; it does not
generate it.

Example shape:

```text
Today, 2026-04-24 - your first plan
===================================

6 prescriptions.

[PROCEED] Recovery - Proceed with your planned session.
-------------------------------------------------------

recovery_baseline.

Confidence: moderate.

Follow-up: How did today's recovery land?

...(five more prescriptions)...

Recorded as plan plan_2026-04-24_u_snap. This is your first plan -
confidence will sharpen as the system sees more of your training.
```

Six prescriptions, reason tokens, confidence labels, and follow-up
questions are computed from persisted state and deterministic rules.
Cold-start framing is computed from history length, not written by the
LLM.

### What Deterministic Cross-Domain Reasoning Looks Like

Eleven cross-domain X-rules sit between domain proposals and the final
plan. They mechanically mutate drafts before prose is written.

Example: X4 `lower-body-sequencing-softens-run`
([`x_rules.md`](x_rules.md)):

```text
Trigger: Yesterday's strength = heavy lower body AND running intervals/tempo proposed today.
Target: running.
Tier: soften.
Action: downgrade_to_easy_aerobic.
```

X-rules fire from typed state, land as rows in `x_rule_firing`, and are
reconstructable per day via `hai explain`.

### What The Agent Reads As A Contract

Every command in `hai capabilities --json` carries mutation class,
agent-safety flag, idempotency mark, flags, and exit codes.

Trimmed example:

```json
{
  "command": "hai auth intervals-icu",
  "description": "Store Intervals.icu credentials in the OS keyring.",
  "agent_safe": false,
  "mutation": "writes-credentials",
  "idempotent": "yes",
  "exit_codes": ["OK", "USER_INPUT"],
  "flags": [
    {"name": "--athlete-id", "type": "str", "required": false},
    {"name": "--api-key-stdin", "type": "bool", "required": false}
  ]
}
```

`agent_safe: false` is mechanically enforced. The runtime refuses this
command under an agent token.

## What HAI Enables Today

| Capability | Working surface |
|---|---|
| Multi-domain data intake | Six domains: recovery, running, sleep, stress, strength, nutrition. Passive wearable data via intervals.icu and active intake via `hai intake`. |
| Local state database | User-owned SQLite database with schema-versioned migrations. |
| Daily report | `hai today` produces per-domain bands, source freshness, missing inputs, and committed-plan state. |
| Daily recommendation | Bounded `DomainProposal` rows reconciled by X-rules into one auditable daily plan. |
| Reconstructable audit chain | `hai explain` traces recommendation rows back through proposal, X-rule firing, planned, and final-plan state. |
| Source honesty | Stale data, fixture data, live-source failures, and missing credentials surface explicitly. |
| User-governed targets and intent | Agent-proposed goals require explicit user commit. |

## What HAI May Enable Next

| Capability | Status |
|---|---|
| Weekly review loop | v0.2.0 source tree includes evidence-card and weekly-claim-card substrate. |
| Bloodwork and richer passive intake | Future, using the same typed-evidence pattern. |
| Longer-horizon planning | Future, after daily and review loops are strong enough. |
| MCP-portable agent surface | Future; the capabilities manifest is structured for non-Claude hosts. |
| Personal-calibration evaluation | Future, measuring whether recommendations fit the individual user. |

Under the research-first roadmap, these are subordinate unless needed by
the paper, GovernedAgentBench, HAI paper-readiness, or reproducible baselines.

## Install And Quickstart

Day-to-day use is conversational: your host agent invokes `hai` for you.
Run these once yourself to confirm the install and local state path:

```bash
pipx install health-agent-infra
hai init --non-interactive
hai capabilities --human
hai doctor
hai daily
hai today
```

For guided onboarding:

```bash
hai init --guided
```

`hai init` is idempotent. On a TTY with incomplete onboarding, bare
`hai init` auto-promotes to the guided flow. Non-interactive callers can
avoid this using no TTY, `--non-interactive`, or
`HAI_INIT_NON_INTERACTIVE=1`.

`intervals_icu` is currently the only working live source. Without
credentials, `hai pull` falls back to a committed CSV fixture for demos
and smoke tests. Garmin Connect support exists but is rate-limited and
Cloudflare-blocked; the capabilities manifest marks it
`reliability == "unreliable"`.

After a fresh PyPI publish, CDN cache lag can briefly hide the newest
wheel. The pinned bypass form forces a fresh fetch:

```bash
pipx install --force \
  --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" \
  health-agent-infra
```

## Daily Workflow

`hai daily` is the current product loop. The agent runs it during a
morning conversation; the runtime executes deterministic stages and tells
the agent what still needs to happen.

1. `pull` fetches passive evidence and records sync freshness.
2. `clean` normalizes evidence into typed accepted-state rows.
3. `snapshot` builds the six-domain state bundle.
4. `gaps` reports missing user-closeable inputs.
5. `proposal_gate` reports whether bounded `DomainProposal` rows are
   still needed.

When proposals are needed, the agent uses the domain skills and writes
one bounded `DomainProposal` per expected domain with `hai propose`.
Then `hai daily` or `hai synthesize` completes the atomic commit.

The full integration contract is in
[`agent_integration.md`](agent_integration.md).

## Current HAI State

| Surface | Current value |
|---|---|
| Source package version | `0.2.0` (2026-05-07 source tree) |
| Schema head | migration `028` (`recommendation_evidence_card` + `weekly_claim_card`) |
| CLI surface | 68 annotated commands |
| Test gate at release | 2,943 passed, 4 skipped |
| Live source | intervals.icu only; Garmin marked `unreliable` |
| HAI posture | Maintainer-dogfooded reference runtime; foreign-user empirical scope deferred to v0.4 review per AGENTS.md D16. |
| Research posture | GovernedAgentBench scaffold exists; benchmark MVP and HAI paper-readiness engineering are next. |

For the terse current-state map, read
[`current_system_state.md`](current_system_state.md).

## Domains

| Domain | What it covers |
|---|---|
| recovery | HRV/RHR readiness, soreness, energy, recovery constraints |
| running | recent activities, load, ACWR, session readiness |
| sleep | duration, debt, deprivation risk, recovery interaction |
| stress | self-report and stress trend signals |
| strength | gym set intake, exercise taxonomy, volume spikes |
| nutrition | daily macro totals and target-aware suppression |

Domain breadth is not the research claim. The claim is that each domain
has typed state, known evidence inputs, classifier and policy boundaries,
provenance, and an auditable plan surface.

Nutrition is daily macros-only in v1, not meal-level tracking. Body
composition, micronutrients, clinical claims, and autonomous diet plans
are intentionally out of scope.

## Calibration

A fresh install can produce recommendations on day one, but personal
calibration requires history.

| Window | What to expect |
|---|---|
| Days 1-14 | Cold-start mode for running, strength, and stress; review recommendations consciously. |
| Days 14-28 | HRV and RHR baselines stabilize; recovery, sleep, and stress trends become useful. |
| Day 28+ | ACWR and strength volume ratios stop being mechanically inflated; trend bands begin carrying real signal. |
| Day ~90 | Steady-state personal calibration. |

Cold-start relaxation is asymmetric by design: running, strength, and
stress can soften some coverage blocks; recovery, sleep, and nutrition do
not relax into confident guesses when evidence is thin.

## Where Your Data Lives

| What | Default path | Override |
|---|---|---|
| State DB | `~/.local/share/health_agent_infra/state.db` | `$HAI_STATE_DB`, `--db-path` |
| Intake/proposal JSONL | `~/.health_agent/` | `$HAI_BASE_DIR`, `--base-dir` |
| Config | macOS: `~/Library/Application Support/hai/`; Linux: `~/.config/hai/` | `hai config init --path <p>` |

Run `hai doctor` to confirm resolved paths, schema version, source
freshness, credential status, and skill installation.

## Boundaries

HAI is health-agent infrastructure, not an autonomous doctor, coach,
dietitian, wearable platform, or cloud service.

- It does not diagnose, treat, prescribe, or make clinical claims.
- It does not make autonomous medical decisions.
- It does not let the agent silently activate goals, targets, intent, or
  final plans without the governed write path.
- It does not ask the LLM to be the database, validator, migration layer,
  source of truth, or policy engine.
- It does not replace wearables or source APIs; it records and governs
  the evidence they provide.
- It does not treat missing, stale, fixture, or unreliable data as
  equivalent to live evidence.

## Main Command Groups

These are the surfaces the agent invokes through the governed CLI. A
human can run them directly for inspection or debugging.

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

`intent commit`, `intent archive`, `target commit`, and `target archive`
are explicit user/operator authority paths. The capabilities manifest
marks them `agent_safe == false`, and the runtime refuses to execute them
under an agent token.

The authoritative command surface is generated at
[`agent_cli_contract.md`](agent_cli_contract.md) and from
`hai capabilities --json`.

## Read Next

| Reader | Best next docs |
|---|---|
| User trying the package | [`current_system_state.md`](current_system_state.md), [`privacy.md`](privacy.md), [`non_goals.md`](non_goals.md), [`backup_and_recovery.md`](backup_and_recovery.md) |
| Host-agent integrator | [`host_agent_contract.md`](host_agent_contract.md), [`agent_integration.md`](agent_integration.md), [`agent_cli_contract.md`](agent_cli_contract.md), [`../../ARCHITECTURE.md`](../../ARCHITECTURE.md) |
| Runtime contributor | [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md), [`architecture.md`](architecture.md), [`domains/README.md`](domains/README.md), [`x_rules.md`](x_rules.md) |
| Research / benchmark reviewer | [`../../PROJECT_FRAME.md`](../../PROJECT_FRAME.md), [`../../research/runtime_contracts_paper/PAPER_FRAME.md`](../../research/runtime_contracts_paper/PAPER_FRAME.md), [`../../benchmarks/governed_agent_bench/README.md`](../../benchmarks/governed_agent_bench/README.md) |
