# Health Agent Infra

Health Agent Infra is a local governance runtime for agentic personal-health
software. It turns a natural-language health agent into a bounded operator:
you talk to the agent, the agent invokes the local `hai` CLI, and
deterministic Python owns rules, validation, state, and commits.

It is both a working single-user package and a reference architecture for
the code/skill split. It is not a chatbot or a hosted coaching app; it is the
boundary that lets an LLM work over health data without owning the policy
engine, the database, or the final write path.

[![PyPI](https://img.shields.io/pypi/v/health-agent-infra)](https://pypi.org/project/health-agent-infra/)
[![Tests](https://img.shields.io/badge/tests-2493_passing-green)](verification/tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What this is

A Claude Code agent is the intended operator. You ask it to check readiness,
log a gym session, explain yesterday's recommendation, or record how the day
went. The agent maps that request onto validated `hai` commands, reads a
governed snapshot, posts one bounded proposal per domain, and lets the runtime
commit the final plan atomically to local SQLite.

The core rule:

> Skills never mutate actions; code never improvises coaching prose.

Python owns classification bands, R-rules, X-rules, schema validation,
supersession, review linkage, and transactions. Markdown skills own rationale,
uncertainty, clarification, and natural-language handoff back to the user.

The package stores state locally and has no telemetry path. Pull commands
only call the configured data source, currently intervals.icu or Garmin
Connect. If you drive the runtime with a hosted LLM agent, any context you
send to that host is governed by that host's data policy; Health Agent Infra
does not control the model provider.

**For** technical users who want the convenience of a conversational health
agent without handing the model unchecked authority over personal health data.

## What ships today

| Surface | Shipped shape |
|---|---|
| Domains | 6: recovery, running, sleep, stress, strength, nutrition |
| Skills | 14 packaged markdown skills, including `intent-router` and `expert-explainer` |
| CLI contract | 56 annotated `hai` commands with mutation class, idempotency, JSON mode, exit codes, and agent-safety metadata |
| State | 22 SQLite migrations, local-only by default |
| Synthesis | 10 X-rule evaluators across two phases, committed in one transaction |
| Verification | 2493 passing tests, 12-persona harness, 5-path trusted-first-value acceptance matrix |

## Why it is different

- **Natural-language front end, deterministic write path.** The normal
  product loop is conversational, but every mutation routes through validated
  CLI commands and local transactions.
- **Local-first runtime.** State lives in SQLite under your home directory.
  No Health Agent Infra account, no daemon, no hosted backend.
- **Governed, not generative.** Python owns deterministic policy; skills
  only narrate and ask for clarification over already-constrained actions.
- **Agent-native by contract.** `hai capabilities --json` exposes every
  subcommand's mutation class, idempotency, JSON behavior, exit codes, and
  agent-safe flag. The `intent-router` skill maps natural-language intent to
  that contract, so the CLI is the agent's tool surface rather than a list of
  commands the user must memorize.
- **Auditable by construction.** Pulls, accepted state, proposals, X-rule
  firings, final recommendations, and review outcomes persist in typed
  tables. Inspect with `hai today`, `hai explain --operator`, `hai doctor`,
  and `hai stats`; these surfaces reconcile supersede chains and hide schema
  churn that raw SQL will not.

v0.1.13 ships public-surface hardening + onboarding (`hai capabilities --human`,
`hai doctor --deep` with 5-class probe-pull classification, `hai today` cold-start
prose, regulated-claim lint, declarative persona expected-actions, trusted-first-value
acceptance matrix). The release-by-release audit index is in [AUDIT.md](AUDIT.md).

## What the loop looks like

```text
User:  "Plan today, but I slept badly and my legs feel heavy."
Agent: Reads `hai capabilities`, logs the readiness note, runs `hai daily`.
Runtime: Pulls evidence, projects state, classifies six domains, applies R-rules.
Agent: Invokes domain skills and posts `DomainProposal` rows with `hai propose`.
Runtime: Applies X-rules, commits the plan atomically, schedules review.
User:  Reads `hai today`; asks "why did you soften the run?"
Agent: Runs `hai explain --operator` and answers from persisted rows.
```

## How the daily loop completes

`hai daily` is the orchestrator the agent drives. It does not finish the
full judgment loop in one call:

1. `pull` fetches evidence from the configured source and writes a
   `sync_run_log` row for freshness telemetry.
2. `clean` normalizes evidence into typed accepted-state rows. v0.1.9
   makes this fail-closed: a DB projection failure exits non-OK rather
   than silently leaving downstream callers with stale state.
3. `snapshot` builds the per-domain bundle, with `classified_state` and
   `policy_result` populated on every domain regardless of whether the
   caller passed an evidence bundle.
4. `gaps` enumerates user-closeable intake gaps.
5. `proposal_gate` reports `awaiting_proposals`, `incomplete`, or
   `complete`.

When the gate is not `complete`, the agent invokes the per-domain readiness
skills, posts one `DomainProposal` per expected domain with
`hai propose --domain <d>`, then re-runs `hai daily`. `--domains <csv>`
narrows the expected set for partial-day runs. Direct `hai synthesize`
enforces the same six-domain completeness gate by default — pass
`--domains ''` to opt out (rare; matches pre-v0.1.9 permissive behavior).

The full contract is in
[`reporting/docs/agent_integration.md`](reporting/docs/agent_integration.md).

## Install

The commands below are the agent-operable surface. You can run them by hand,
but the intended daily loop is natural language first: tell the agent what
you want, let it inspect `hai capabilities`, and let it invoke the right
validated command.

```bash quickstart
pipx install health-agent-infra                # or: pip install -e .
hai init                                       # scaffolds state + config + skills
hai auth intervals-icu                         # preferred live source
hai capabilities --human                       # one-page overview of every command
hai doctor                                     # check setup; --deep probes the live API
hai daily                                      # orchestrates pull -> clean ->
                                               # snapshot -> gaps -> proposal gate;
                                               # the agent then posts proposals
hai today                                      # read today's plan in plain language
```

`--source` defaults to `intervals_icu` when credentials are configured, else
`csv` for the committed fixture. Garmin Connect live scraping remains
best-effort and rate-limited; use `--source garmin_live` only when you
explicitly want it.

Run `hai capabilities --human` (v0.1.13+) for a one-page workflow-grouped
overview of every `hai` command. The agent-facing JSON manifest is
`hai capabilities --json`.

On macOS, credentials are stored in the OS keyring. The first `hai pull`
may ask for access; choose **Always Allow** if you want scripted runs such
as `hai daily` to continue without hanging on a prompt.

Full agent wiring notes live in
[`reporting/docs/agent_integration.md`](reporting/docs/agent_integration.md).

## Where your data lives

Everything the runtime stores stays on your machine. Three locations matter:

| What | Default path | Override |
|---|---|---|
| State DB | `~/.local/share/health_agent_infra/state.db` | `$HAI_STATE_DB`, `--db-path` |
| Intake / proposal JSONL | `~/.health_agent/` | `$HAI_BASE_DIR`, `--base-dir` |
| Config (`thresholds.toml`) | macOS: `~/Library/Application Support/hai/`; Linux: `~/.config/hai/` | `hai config init --path <p>` |

Run `hai doctor` to confirm resolved paths, schema version, source
freshness, and skill installation status. It also warns when the applied
migration set has gaps even if `MAX(version)` looks current.

## Troubleshooting

The five most common gotchas a new user hits, in order:

1. **`hai today` says "no plan for <date>"** — `hai daily` hasn't run yet
   today, or the proposal gate stopped at `awaiting_proposals` because the
   agent didn't post per-domain proposals. Run `hai daily` (let the agent
   drive it conversationally), or check `hai stats --funnel` to see where
   the pipeline stalled.

2. **`hai pull` returns HTTP 403** — two distinct root causes look
   identical at the `IntervalsIcuError` boundary. Run `hai doctor --deep`
   (v0.1.13+) — it classifies the failure into one of five outcome
   classes:
   - `CAUSE_1_CLOUDFLARE_UA` — Cloudflare bot-protection blocked the
     request at the edge (the credentials never reached intervals.icu).
     Patched in v0.1.12.1; if it re-fires, file an issue.
   - `CAUSE_2_CREDS` — intervals.icu rejected the credentials. Run
     `hai auth intervals-icu` to refresh.
   - `NETWORK` — DNS / TCP / TLS layer; verify connectivity.
   - `OTHER` — unclassified; consult
     [`reporting/docs/intervals_icu_403_triage.md`](reporting/docs/intervals_icu_403_triage.md).

3. **`hai doctor` says auth is OK but pulls fail** — the default `hai
   doctor` checks credential *presence* in the keyring, not whether the
   live API accepts them. Always run `hai doctor --deep` before a demo
   or after rotating keys; the deep check makes one live API call.

4. **A USER_INPUT exit with no useful message** — every USER_INPUT exit
   should print an actionable next-step (v0.1.13 W-AD audit pinned this
   surface). If you hit one without a hint, the message itself is a bug
   — file an issue.

5. **`hai today` looks confident but you have only a few days of data** —
   the cold-start window is the first 14 days for running, strength, and
   stress; recovery and sleep continue to defer when signal is thin.
   Bands and trends carry real signal around day 90. The plan calibration
   table below is the durable reference.

## Reading your plan

`hai today` is the non-agent-mediated user surface. It resolves supersede
chains and renders the canonical plan for a date:

```bash
hai today                         # today, markdown on TTY / plain elsewhere
hai today --as-of 2026-04-23      # specific date
hai today --domain recovery       # narrow to one domain
hai today --format json           # machine-readable
```

For dense audit output, use `hai explain --operator` or `hai explain`.
Both reconstruct the plan from persisted rows; they do not recompute the
runtime state.

## Recording your day

After the next day's run schedules review events, record how yesterday went:

```bash
hai review record --outcome-json <path>
hai review summary [--domain recovery]
```

Outcomes are append-only and re-link when a plan has been superseded. If
you recorded an outcome against the morning plan but re-authored the day
after lunch, `hai review record` routes the outcome to the canonical leaf's
matching-domain recommendation.

`followed_recommendation` and `self_reported_improvement` must be strict
booleans (`true` / `false`), not `"yes"`, `1`, or truthy strings.

Manual intake lives under:

```bash
hai intake gym|exercise|nutrition|stress|note|readiness ...
```

Nutrition is a daily total, not per-meal. Re-calling within the same day
creates a supersede chain; log it once at the end of the day.

## Six domains in v1

**recovery - running - sleep - stress - strength - nutrition**

Each domain ships schemas, classification bands, policy rules, and a
readiness skill. Synthesis reconciles proposals through 10 X-rule
evaluators across two phases. Nutrition is macros-only in v1; see
[`reporting/docs/non_goals.md`](reporting/docs/non_goals.md).

## Calibration timeline

A fresh install can produce recommendations on day one, but several signals
need history before they carry much meaning:

| Window | What works |
|---|---|
| Days 1-14 | Cold-start mode for running, strength, and stress. Expect to review flags consciously. |
| Day 14 | Cold-start window closes. HRV and RHR rolling baselines begin to stabilize. |
| Days 14-28 | Recovery, sleep, and stress become more calibrated against trailing-7d trend. |
| Day 28 | ACWR's chronic-load denominator is full. Strength `volume_ratio` stops mechanically reading as 4x. |
| Day 60+ | Trend bands start carrying real signal. |
| Around day 90 | Steady state; remaining uncertainty is structural rather than history-bounded. |

Code-derived marker: `COLD_START_THRESHOLD_DAYS = 14` in
`src/health_agent_infra/core/state/snapshot.py`. Cold-start relaxation is
asymmetric by design: running, strength, and stress can soften some
coverage blocks; recovery, sleep, and nutrition do not. Nutrition keeps
deferring on insufficient evidence rather than relaxing into a
low-confidence guess.

Permanent caveats:

- intervals.icu does not expose sleep efficiency, body battery, or Garmin
  all-day stress.
- v1 nutrition is macros-only, so micronutrient coverage is unavailable at
  source.

## What the system refuses to do

- No medical claims or diagnosis-shaped language.
- No autonomous training-plan or diet-plan generation.
- No state mutation without the relevant validated CLI path and, for
  agent-proposed intent/target activation, explicit user commit.
- No package telemetry or hosted state backend.
- No skill-side arithmetic for bands, scores, R-rules, or X-rules.

Full scope boundaries are in
[`reporting/docs/non_goals.md`](reporting/docs/non_goals.md) and
[SECURITY.md](SECURITY.md).

## CLI surface

This is the contract an agent operates after translating user intent from
natural language. Humans can use it directly for setup, debugging, and audit;
the normal product loop is still conversational.

```bash
# Evidence + intake
hai pull [--source intervals_icu|garmin_live|csv] --date <d>
hai clean --evidence-json <p>
hai intake gym|exercise|nutrition|stress|note|readiness ...

# Agent flow
hai daily [--domains <csv>]
hai propose --domain <d> --proposal-json <p>
hai synthesize --as-of <d> --user-id <u>
hai synthesize --bundle-only

# State + audit
hai state init | migrate | read | snapshot | reproject [--cascade-synthesis]
hai capabilities [--json | --markdown]
hai explain --for-date <d> --user-id <u>
hai today | hai doctor | hai stats

# Review, memory, intent, targets
hai review schedule | record | summary
hai memory set | list | archive
hai intent training add-session | training list | sleep set-window | list | archive
hai target set | list | archive

# Ops + research + evals
hai auth intervals-icu | garmin | status
hai config init | show | validate | diff
hai planned-session-types
hai research topics | search --topic <t>
hai eval run --domain <d> | --synthesis [--json]
hai setup-skills
```

The authoritative surface is `hai capabilities --markdown` or
[`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md).

## Roadmap

Now / Next / Later lives in [ROADMAP.md](ROADMAP.md). The detailed
release plan lives in
[`reporting/plans/tactical_plan_v0_1_x.md`](reporting/plans/tactical_plan_v0_1_x.md);
the strategic vision in
[`reporting/plans/strategic_plan_v1.md`](reporting/plans/strategic_plan_v1.md).
The earlier
[`reporting/plans/historical/multi_release_roadmap.md`](reporting/plans/historical/multi_release_roadmap.md)
is superseded as of 2026-04-27.

## Where to read next

- [ARCHITECTURE.md](ARCHITECTURE.md) - one-page architecture
- [AUDIT.md](AUDIT.md) - release audit index
- [HYPOTHESES.md](HYPOTHESES.md) - five falsifiable hypotheses
- [ROADMAP.md](ROADMAP.md) - Now / Next / Later
- [CONTRIBUTING.md](CONTRIBUTING.md) - code-vs-skill contribution rules
- [REPO_MAP.md](REPO_MAP.md) - every top-level entry classified
- [SECURITY.md](SECURITY.md) - vulnerability reporting and scope of trust
- [`reporting/docs/architecture.md`](reporting/docs/architecture.md) - full pipeline
- [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md) - scope discipline
- [`reporting/docs/x_rules.md`](reporting/docs/x_rules.md) - X-rule catalogue
- [`reporting/docs/tour.md`](reporting/docs/tour.md) - 10-minute reading tour

## Citing this work

See [CITATION.cff](CITATION.cff). If you are writing about the project's
claims rather than the package itself, use [HYPOTHESES.md](HYPOTHESES.md)
as the canonical statement of the bets and their falsification criteria.

## License

MIT. See [LICENSE](LICENSE).
