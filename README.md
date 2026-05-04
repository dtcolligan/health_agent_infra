# Health Agent Infra

Health Agent Infra is the local plugin/runtime wrapper around a
shell-capable personal-health agent.

You talk to an agent. The agent invokes the local `hai` CLI. In
parallel, the runtime absorbs passive evidence — wearable data today
via intervals.icu, bloodwork and richer passive sources next —
without the user having to narrate the data. The agent remains the
conversational operator. `hai` is the governed tool surface that
tells the agent what it may do, which local substrates each command
may mutate, which outputs must validate, and which actions are
refused.

The package is working single-user software. It is currently packaged
and tested around Claude Code as the first compatible agent surface,
but the core contract is a local CLI plus machine-readable capability
manifest, not a Claude-only backend.

[![PyPI](https://img.shields.io/pypi/v/health-agent-infra)](https://pypi.org/project/health-agent-infra/)
[![Tests](https://img.shields.io/badge/tests-2631_passing-green)](verification/tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **Status.** Working maintainer-dogfooded software. Non-maintainer
> full-flow validation is pending: the recorded session against
> `health-agent-infra==0.1.15.1` is the empirical input that feeds
> v0.1.16. Treat headline claims as maintainer-verified, not yet
> independently reproduced.

![A user's health data goes through a shell-capable personal-health agent into the hai governed tool surface, which validates and gates writes to local SQLite state, JSONL audit logs, keyring/config, and validators. A direct write attempt from the agent is crossed out at the boundary.](assets/landing_hero.png)

## Product boundary

![A user conversation flows into a shell-capable agent. The agent invokes the hai governed tool surface, which validates, gates, and audits every write before persisting to local SQLite state, JSONL audit logs, and the OS keyring/config. A direct write attempt from the agent to local state is shown crossed out at the boundary. A read-only return path through hai today, explain, review, and backup feeds back to the agent.](assets/product_boundary.png)

The agent proposes, explains, and asks for missing context. The
wrapper validates, gates, mutates, and records. Every persisted byte
goes through `hai`; nothing else has write authority.

Goals are user-owned, not agent-owned: the agent may *propose* intent
or training/nutrition target rows, but only the user can *commit* them
(governance invariant W57). The runtime enforces this mechanically —
the commit/archive paths are marked `agent_safe == false` in the
capabilities manifest. See
[`reporting/docs/host_agent_contract.md`](reporting/docs/host_agent_contract.md)
for the host-agent operating rules.

## Two-minute on-ramp

These commands are for **inspection and setup** — verifying that the
package installed, that credentials are configured, and that the
runtime is healthy. The day-to-day surface is conversational: you
talk to a host agent (Claude Code or equivalent), the agent invokes
`hai` for you. Run these yourself once to confirm the install and to
wire up the live data path:

```bash
pipx install health-agent-infra
hai init
hai auth intervals-icu          # the only working live data path
hai capabilities --human
hai doctor
hai daily
hai today
```

> **intervals.icu is currently the only working live source.** The
> runtime treats it as the preferred wearable path; without
> credentials, `hai pull` falls back to the committed CSV fixture.
> Garmin live exists for completeness but is rate-limited and
> Cloudflare-blocked in practice — the capabilities manifest marks
> it `reliability == "unreliable"` and the runtime warns at
> resolution time.

Use the pinned CDN-bypass install only in the first few minutes after
a fresh PyPI publish:

```bash
pipx install --force --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" 'health-agent-infra==0.1.15.1'
```

The intended interface is an agent, but the runtime is normal local
software. `hai capabilities --json` is the contract the agent reads;
`hai doctor`, `hai daily`, `hai today`, and `hai explain` are the
first commands a human should inspect.

## Why this exists

Agentic AI in personal health fails when the agent is asked to be
everything at once — the chat interface, the memory layer, the data
interpreter, the planner, the database, the validator, and the
auditor. The same prompt that produces good rationale on Monday
produces bad classification on Wednesday, and there is no inspectable
record of why.

Personal health is the wrong domain to lose that record. Decisions
compound: today's training load shapes tomorrow's recovery, this
week's sleep debt shapes next week's stress capacity. If the agent is
the only thing that "remembers" what it told you yesterday, you don't
have an agent — you have a rolling guess.

Health Agent Infra moves the durable parts — typed state, projection,
classification, policy, validation, atomic commit — into local Python
behind a CLI the agent calls. The model keeps its strengths:
conversation, clarification, uncertainty surfacing, and prose
rationale over a bounded action set. The runtime keeps its strengths:
deterministic interpretation and a reconstructable audit chain.

![Two side-by-side panels. Left panel titled Agent does everything shows a single operator figure surrounded by an overlapping cluster of seven labeled circles — chat, memory, interpret, plan, validate, audit, DB — with tangled crossing arrows; subtitle: non-deterministic, no audit trail. Right panel titled Agent + governed runtime shows the same operator figure connected through a labeled hai governed tool surface gateway to a tidy column of five separate boxes — typed state, deterministic classifiers, policy rules, atomic commits, audit log — with simple parallel arrows; subtitle: deterministic, reconstructable.](assets/why_this_exists.png)

The contract is one line:

> **The agent proposes and explains; the runtime validates and commits.**

That single boundary is what turns "an LLM with health context" into
software you can audit, reproduce, and trust across sessions.

## What the product does

Health Agent Infra wraps an agentic personal-health workflow in local,
deterministic infrastructure. It gives the agent a governed CLI and a
SQLite-backed state layer for **passive data intake** (wearables today
via intervals.icu; bloodwork and other passive sources are the natural
next extension of the same typed-evidence pattern), **active intake**
(gym sets, food, readiness, stress, free-text notes), typed daily
projections, deterministic classifiers, policy rules, bounded
proposals, and auditable commits.

It also gives the agent operational surfaces that a plain chat agent
does not have: source freshness checks, credential diagnostics,
structured intake gaps, explicit user commit gates for targets and
intent, backup/restore/export, and an explanation surface that
reconstructs recommendations from persisted rows. Generated capability
docs, contract tests, scenario fixtures, and persona runs keep the
agent-facing surface from drifting silently as the runtime changes.

In practice:

1. The user converses with the agent about training, recovery, sleep,
   nutrition, stress, and missing context. In parallel, the runtime
   absorbs **passive evidence** — wearable pulls today, bloodwork and
   richer passive sources on the roadmap — without the user having
   to narrate the data.
2. The agent reads `hai capabilities --json` to understand exactly
   which commands are safe and what each command can mutate.
3. `hai` performs the local state operations: pulling or recording
   evidence, projecting typed rows, and preserving the health-state
   database.
4. Python code interprets the data with deterministic classifiers,
   policy rules, validation, and cross-domain X-rules.
5. Markdown skills help the agent explain uncertainty, ask better
   questions, and write rationale.
6. The runtime blocks missing or unsafe states, applies cross-domain
   adjustments, and performs the final state write.
7. Review, explanation, and recovery commands make the result
   inspectable after the fact.

The core rule:

> The agent can propose and explain; the runtime validates and commits.

## Where the product stands

The current published package is `health-agent-infra==0.1.15.1`
from 2026-05-03. It is the v0.1.15 single-user package plus a Linux
keyring hotfix.

| Area | Current state |
|---|---|
| Daily loop | Working and dogfooded: pull/clean/snapshot, intake gaps, proposal gate, synthesis, `hai today`. |
| State and audit | Local SQLite, 25 migrations, six accepted-state domains, proposal/planned/adapted/review rows. |
| Agent contract | 60 annotated commands with mutation class, idempotency, JSON behavior, exit codes, and agent-safety metadata. |
| Source handling | **intervals.icu is the live data path.** Garmin live is best-effort and structurally marked `reliability == "unreliable"` in the capabilities manifest. CSV fixture guarded from canonical state by default. |
| User-governed commits | Agent-proposed targets and intent rows require explicit non-agent `commit` / `archive` authority. |
| Review and explanation | `hai explain`, `hai review record`, and `hai review summary` reconstruct why a plan changed and how it landed. |
| Recovery and portability | `hai backup`, `hai restore`, and `hai export` preserve local state and refuse incompatible schema restores by default. |
| Future loops | Weekly review and longer-horizon planning are planned on top of the same provenance rows; they are not product loops yet. |
| External validation | PyPI package published; the recorded non-maintainer full-flow session is still pending and feeds v0.1.16. |

For the terse release-truth map, read
[`reporting/docs/current_system_state.md`](reporting/docs/current_system_state.md).

## What hai enables for AI in personal health

`hai` is the substrate. The agent is the operator. Together they give
an LLM the authority and scaffolding to do real work inside a
personal-health loop without being asked to *also* be the database,
the validator, or the auditor.

### Already achieved

| Capability | What's working today |
|---|---|
| Multi-domain data intake | Six domains — recovery, running, sleep, stress, strength, nutrition — accept passive wearable data via intervals.icu and active intake via `hai intake` (gym sets, readiness, stress, food, free-text notes). |
| Local health-state database | A user-owned SQLite database accumulates typed state across days, schema-versioned and migration-tracked (25 migrations, 60 annotated CLI commands). |
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

## Why it is different

- **Local state, not chat memory.** The system maintains a structured
  health-state database instead of asking the LLM to remember health
  history inside a conversation.
- **Deterministic interpretation.** Wearable data and manual intake
  are projected into typed state before recommendations are made.
- **Validated write path.** The agent cannot bypass the CLI contract
  to mutate state directly.
- **Source honesty.** Fixture data, live-source failures, stale syncs,
  and missing credentials are visible to the agent instead of being
  collapsed into vague "no data" prose.
- **Cross-domain planning without free-form authority.** X-rules let
  sleep, recovery, nutrition, stress, running, and strength constrain
  each other mechanically before prose is written.
- **User-governed commitments.** Agent-proposed targets and intent
  rows do not become active just because an agent suggested them.
- **Code and skills have separate jobs.** Python owns bands, R-rules,
  X-rules, validation, supersession, and commits. Markdown skills own
  explanation, uncertainty, and clarification.
- **Agent-native contract.** `hai capabilities --json` tells the agent
  exactly which commands exist, what they can mutate, and whether they
  are agent-safe.
- **Auditable by construction.** Use `hai today`,
  `hai explain --operator`, `hai doctor`, and `hai stats` instead of
  raw SQLite as the first inspection path; these commands resolve
  supersession chains and schema churn.

## Install

The intended interface is an agent, but these are normal CLI commands.
Humans run them directly for setup, inspection, debugging, and recovery;
normal planning use is agent-mediated through the same contract.

```bash quickstart
pipx install health-agent-infra
# OR for a dev checkout: pip install -e .
hai init
hai auth intervals-icu
hai capabilities --human
hai doctor
hai daily
hai today
```

Immediately after a new publish, PyPI CDN cache lag can briefly hide
the newest wheel. Use the pinned bypass form when you need the just
published version immediately:

```bash
pipx install --force --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" 'health-agent-infra==0.1.15.1'
```

**`intervals_icu` is the only working live source.** It's what the
runtime resolves to when credentials are present, what `hai daily`
pulls from, and what every persona run and demo uses. Run
`hai auth intervals-icu` once after `hai init` to wire it up.

Garmin Connect support exists for completeness but is best-effort —
Garmin login is rate-limited and frequently fails behind Cloudflare,
the capabilities manifest exposes
`commands[hai pull].flags[--source].choice_metadata.garmin_live.reliability == "unreliable"`,
and `hai pull --source garmin_live` emits a stderr warning at
resolution time. Use it only when you explicitly want that path.

If no live credentials are configured, the runtime falls back to the
committed CSV fixture for demos and smoke tests; fixture data is
guarded from canonical state by default and clearly labeled in
`hai doctor`.

On macOS, credentials use the OS keychain. On Linux, v0.1.15.1 includes
`keyrings.alt` and a defensive fallback so setup/status commands do not
crash when no desktop keyring backend is registered.

## Daily workflow (agent-operated)

`hai daily` is the current product loop. The **agent** runs it on the
user's behalf during a morning conversation; the runtime executes the
deterministic stages and tells the agent what still needs to happen.

1. `pull` fetches passive evidence (intervals.icu wearable data) and
   records sync freshness.
2. `clean` normalizes evidence into typed accepted-state rows.
3. `snapshot` builds the six-domain state bundle.
4. `gaps` reports missing user-closeable inputs (the agent asks the
   user only for what the runtime says it actually needs).
5. `proposal_gate` reports whether bounded `DomainProposal` rows are
   still needed.

When proposals are needed, the agent uses the domain skills and
writes one bounded `DomainProposal` per expected domain with `hai
propose`. Then `hai daily` or `hai synthesize` completes the atomic
commit. The user never types these commands in normal use — they are
what the agent invokes through the governed surface.

The daily loop is not the whole product; it is the first complete
agent-operable loop. The same state and provenance model is what the
weekly review, longer-horizon planning, and future evaluation surfaces
will build on.

The full integration contract is in
[`reporting/docs/agent_integration.md`](reporting/docs/agent_integration.md).

## Read and review surfaces (agent-called)

The read and review surfaces are part of the same agent-operable
contract — the agent calls them on the user's behalf during a
session, and a human can run them directly for inspection or
debugging.

- **Read surface** — `hai today` returns the committed daily plan
  (per-domain bands, sources, missing inputs); `hai explain` and
  `hai explain --operator` reconstruct *why* the plan looks the way
  it does from persisted proposal, X-rule, planned, and
  recommendation rows. Neither command recomputes the day from
  scratch; both are strictly read-only.
- **Review surface** — `hai review record` logs whether yesterday's
  recommendation was followed and whether it helped; `hai review
  summary` aggregates outcomes by domain. Rows are append-only; if
  the same day is re-authored, outcomes route to the canonical leaf
  recommendation. `followed_recommendation` and
  `self_reported_improvement` must be strict booleans.

The agent narrates from these surfaces. The user does not have to
memorise them.

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
classifier and policy boundaries, provenance, and an auditable plan
surface. New domains should follow that pattern rather than becoming
more prompt text.

Nutrition is daily macros-only in v1, not meal-level tracking. Body
composition, micronutrients, clinical claims, and autonomous diet
plans are intentionally out of scope.

## Calibration

A fresh install can produce recommendations on day one, but useful
personal calibration takes history.

| Window | What to expect |
|---|---|
| Days 1-14 | Cold-start mode for running, strength, and stress. Review recommendations consciously. |
| Day 14 | HRV and RHR rolling baselines begin to stabilize. |
| Days 14-28 | Recovery, sleep, and stress trend signals become more useful. |
| Day 28 | ACWR chronic load and strength volume ratios stop being mechanically inflated. |
| Day 60+ | Trend bands start carrying real signal. |
| Around day 90 | Steady-state personal calibration. |

Cold-start relaxation is asymmetric by design: running, strength, and
stress can soften some coverage blocks; recovery, sleep, and nutrition
do not relax into confident guesses when evidence is thin.

## Where your data lives

| What | Default path | Override |
|---|---|---|
| State DB | `~/.local/share/health_agent_infra/state.db` | `$HAI_STATE_DB`, `--db-path` |
| Intake/proposal JSONL | `~/.health_agent/` | `$HAI_BASE_DIR`, `--base-dir` |
| Config | macOS: `~/Library/Application Support/hai/`; Linux: `~/.config/hai/` | `hai config init --path <p>` |

Run `hai doctor` to confirm resolved paths, schema version, source
freshness, credential status, and skill installation.

## First-run notes

- `hai today` needs a committed plan. If there is no plan yet, run
  `hai daily`.
- If `hai daily` stops at `awaiting_proposals`, the agent still needs
  to post bounded domain proposals.
- `hai doctor --deep` performs live API checks; plain `hai doctor`
  checks local setup and credential presence.
- Garmin live is explicitly less reliable than intervals.icu.
- USER_INPUT exits should include the next action. If one does not,
  that is a bug.

## Boundaries

The project is health-agent infrastructure, not an autonomous doctor,
coach, dietitian, wearable platform, or cloud service.

- It does not diagnose, treat, or make clinical claims.
- It does not let the agent silently activate goals, targets, intent,
  or final plans without the governed write path.
- It does not ask the LLM to be the database, validator, migration
  layer, source-of-truth, or policy engine.
- It does not replace wearables or source APIs; it records and
  governs the evidence they provide.
- It does not treat missing, stale, fixture, or unreliable data as
  equivalent to live evidence.
- It does not solve every health-agent failure case yet. Weekly
  review, longer-horizon planning, richer personal guidance evals,
  and broader source-quality policy are still staged work.

## Main command groups (what the agent calls)

These are the surfaces the agent invokes through the governed CLI on
the user's behalf. A human can run them directly for inspection or
debugging; in normal use they are agent-operated.

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
are **explicit user/operator authority paths** — the capabilities
manifest marks them `agent_safe == false`, and the runtime refuses to
execute them under an agent token. This is the W57 governance
invariant.

The authoritative command surface is generated at
[`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md)
and from `hai capabilities --json`.

## Read next

| Reader | Best next docs |
|---|---|
| User trying the package | [`reporting/docs/current_system_state.md`](reporting/docs/current_system_state.md), [`reporting/docs/privacy.md`](reporting/docs/privacy.md), [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md) |
| Host-agent integrator | [`reporting/docs/host_agent_contract.md`](reporting/docs/host_agent_contract.md), [`reporting/docs/agent_integration.md`](reporting/docs/agent_integration.md), [`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md), [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| Runtime contributor | [`CONTRIBUTING.md`](CONTRIBUTING.md), [`reporting/docs/architecture.md`](reporting/docs/architecture.md), [`reporting/docs/domains/README.md`](reporting/docs/domains/README.md) |
| Maintainer or release auditor | [`REPO_MAP.md`](REPO_MAP.md), [`AUDIT.md`](AUDIT.md), [`ROADMAP.md`](ROADMAP.md), [`reporting/plans/README.md`](reporting/plans/README.md) |

## Roadmap and proof

- [ROADMAP.md](ROADMAP.md) - now, next, later.
- [AUDIT.md](AUDIT.md) - release audit index.
- [CHANGELOG.md](CHANGELOG.md) - public release history.
- [`reporting/docs/current_system_state.md`](reporting/docs/current_system_state.md) - current shipped truth.
- [`reporting/docs/architecture.md`](reporting/docs/architecture.md) - full architecture.
- [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md) - scope boundaries.
- [`reporting/docs/x_rules.md`](reporting/docs/x_rules.md) - cross-domain rule catalogue.
- [`reporting/docs/tour.md`](reporting/docs/tour.md) - 10-minute reading tour.

## License

MIT. See [LICENSE](LICENSE).
