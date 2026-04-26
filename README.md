# Health Agent Infra

Health Agent Infra is a local-first governance runtime for personal-health
agents. It combines deterministic policy, typed state ledgers, packaged
skills, and a review loop so an LLM can help operate over health data
without owning the rules, state, or commit path.

Six domains - recovery, running, sleep, stress, strength, nutrition - are
classified by Python, bounded by policy rules, narrated by markdown skills,
and committed atomically to a local SQLite database.

[![PyPI](https://img.shields.io/pypi/v/health-agent-infra)](https://pypi.org/project/health-agent-infra/)
[![Tests](https://img.shields.io/badge/tests-2081_collected-green)](safety/tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What this is

A Claude Code agent reads a governed snapshot of your wearable and intake
data, emits per-domain proposals bounded by code-owned rules, and commits
auditable recommendations you review the next day. The runtime owns
mechanical decisions: classification bands, R-rules, X-rules, validation,
and transactional commits. Skills own rationale, uncertainty, and
clarification. **Skills never change an action; code never writes prose.**

The package stores state locally and has no telemetry path. Pull commands
only call the configured data source, currently intervals.icu or Garmin
Connect. If you drive the runtime with a hosted LLM agent, any context you
send to that host is governed by that host's data policy; Health Agent Infra
does not control the model provider.

**For** technical users comfortable with a CLI who want agent
recommendations they can audit, reproduce, and keep under local control.

- **Local-first runtime.** State lives in SQLite under your home directory.
  No account, no daemon, no hosted backend.
- **Governed, not generative.** Python owns deterministic policy; skills
  only narrate and ask for clarification over already-constrained actions.
- **Agent-operable by contract.** `hai capabilities --json` exposes every
  subcommand's mutation class, idempotency, JSON behavior, exit codes, and
  agent-safe flag. The `intent-router` skill maps natural-language intent to
  that contract.
- **Auditable by construction.** Pulls, accepted state, proposals, X-rule
  firings, final recommendations, and review outcomes persist in typed
  tables. Inspect with `hai today`, `hai explain --operator`, `hai doctor`,
  and `hai stats`; these surfaces reconcile supersede chains and hide schema
  churn that raw SQL will not.

v0.1.8 closed four external audit rounds before release. The release-by-
release audit index is in [AUDIT.md](AUDIT.md).

## Install

```bash
pipx install health-agent-infra                # or: pip install -e .
hai init --with-auth --with-first-pull         # scaffolds state + config + skills,
                                                # prompts for credentials,
                                                # backfills the last 7 days
hai daily                                       # orchestrates pull -> clean ->
                                                # snapshot -> gaps -> proposal gate;
                                                # the agent then posts proposals
hai today                                       # read today's plan in plain language
```

`--source` defaults to `intervals_icu` when credentials are configured, else
`csv` for the committed fixture. Garmin Connect live scraping remains
best-effort and rate-limited; use `--source garmin_live` only when you
explicitly want it. Set up intervals.icu auth with:

```bash
hai auth intervals-icu
```

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

## How `hai daily` actually completes

`hai daily` is the orchestrator the agent drives, not a single command that
finishes the full judgment loop alone:

1. `pull` fetches evidence from the configured source.
2. `clean` normalizes evidence into typed state rows.
3. `snapshot` builds the per-domain bundle skills consume.
4. `gaps` enumerates user-closeable intake gaps.
5. `proposal_gate` reports `awaiting_proposals`, `incomplete`, or
   `complete`.

When the gate is not `complete`, the agent invokes the per-domain readiness
skills, posts one `DomainProposal` per expected domain with
`hai propose --domain <d>`, then re-runs `hai daily`. `--domains <csv>`
narrows the expected set for partial-day runs. The full contract is in
[`reporting/docs/agent_integration.md`](reporting/docs/agent_integration.md).

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

Now / Next / Later lives in [ROADMAP.md](ROADMAP.md). The detailed,
audited release plan is
[`reporting/plans/multi_release_roadmap.md`](reporting/plans/multi_release_roadmap.md).

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
