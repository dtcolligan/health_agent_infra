# Health Agent Infra

**A governed local agent runtime for personal health data.**
Claude Code + Garmin today; MCP-portable and multi-source on the roadmap.

A Claude Code agent reads your own health data, emits per-domain proposals
bounded by codified rules, and commits auditable recommendations you review
the next day. Every decision is logged to a local SQLite database on your
machine; nothing leaves your device.

**For** technical users comfortable with a CLI who use Claude Code and want
agent recommendations they can audit, reproduce, and keep local.

- **Local-first.** State lives in a SQLite file under your home directory. No
  cloud, no account, no remote telemetry.
- **Governed, not generative.** Python owns mechanical decisions
  (classification bands, policy rules, transactional commits); markdown
  skills own rationale and uncertainty. Skills never change an action; code
  never writes prose.
- **Agent-operable by contract.** Every CLI subcommand carries
  machine-readable contract metadata (mutation class, idempotency, exit
  codes) that an agent reads via `hai capabilities --json`. An authoritative
  `intent-router` skill maps natural-language intent to deterministic
  workflows; every X-rule firing carries a stable slug plus a sentence-form
  explanation the agent can narrate verbatim.
- **Auditable by construction.** Pulls, proposals, rule firings, synthesis,
  and final recommendations all land in typed tables. Inspect anytime with
  `hai today` (end-user prose), `hai explain --operator` (dense audit
  report), `hai doctor`, `hai stats`. Prefer these over reading the
  SQLite file directly — they reconcile supersede chains and hide
  schema churn, which plain SQL won't.

## Install

```bash
pipx install health-agent-infra                      # or: pip install -e .
hai init --with-auth --with-first-pull               # scaffolds state + config + skills,
                                                     # prompts for Garmin credentials,
                                                     # backfills the last 7 days
hai daily                                            # tomorrow morning: pull → clean → propose → synthesize → commit
hai today                                            # read today's plan in plain language
hai stats                                            # local funnel: syncs, recent runs, daily streak
```

Prefer the non-interactive path? Run `hai init` on its own, then `hai auth
garmin` separately. `hai init` is idempotent and safe to re-run. Full CLI
surface in
[`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md).

**macOS Keychain note.** `hai auth garmin` and `hai auth intervals-icu`
store credentials in the OS keyring. On macOS, the first time
`hai pull --live` reads those credentials the system prompts you to
allow access. Click **Always Allow** — otherwise every subsequent
pull re-prompts and scripted runs (including `hai daily`) will hang
waiting for a keyboard. The corresponding success messages from
`hai auth` print a one-line stderr hint as a reminder.

## Reading your plan

`hai today` is the non-agent-mediated user surface — it reads the
canonical plan for a date (resolving supersede chains automatically)
and renders prose in the voice the `reporting` skill specifies:
top-matter → 2–4 sentence summary → six per-domain sections → footer
pointing at the next review.

```bash
hai today                         # today, markdown on TTY / plain elsewhere
hai today --as-of 2026-04-23      # specific date
hai today --domain recovery       # narrow to one domain
hai today --format json           # machine-readable (same shape, no prose)
```

Defer domains (insufficient signal) surface a domain-specific
follow-up question and an **unblock hint** naming the `hai intake …`
command that would give tomorrow's plan the signal it needs — see
[`reporting/plans/v0_1_4/D3_user_surface.md`](reporting/plans/v0_1_4/D3_user_surface.md)
for the voice contract.

For debug-level audit dumps, use `hai explain --operator` (dense
field-by-field text) or `hai explain` (JSON). Both consume the same
explain bundle `hai today` reads — they just render it differently.

## Recording your day

After tomorrow's `hai daily` schedules a review event for each rec,
log how yesterday went:

```bash
hai review record --outcome-json <path> \
                  --base-dir <base_dir> \
                  --db-path <state.db>

hai review summary --base-dir <base_dir> [--domain recovery]
```

Outcomes are append-only and **auto-re-link** when a plan has been
superseded — if you recorded an outcome against the morning plan but
re-authored the day after lunch, `hai review record` routes the
outcome to the canonical leaf's matching-domain rec. See the
`review-protocol` skill for the full payload shape.

Manual intake surfaces (stress score, gym sessions, nutrition macros,
readiness self-reports) all live under `hai intake <domain>`; they
persist to their per-domain raw tables so the next `hai daily` picks
them up automatically.

## Six domains in v1

**recovery · running · sleep · stress · strength · nutrition**

Each domain ships its own schemas, classification bands, policy rules, and a
readiness skill, and is wired into the synthesis X-rule catalogue that
reconciles across domains. Nutrition is macros-only in v1 — see
[`reporting/docs/non_goals.md`](reporting/docs/non_goals.md).

## Local-first runtime at a glance

```
pull / intake  →  projectors  →  accepted_*_state_daily tables
                                        │
                                        ▼
                         hai state snapshot --as-of <date>
                                        │
                                        ▼
                 domain skills emit DomainProposal × 6
                                        │ hai propose
                                        ▼
                              proposal_log
                                        │
                                        ▼
   Phase A X-rules (X1–X7) → runtime applies mutations to drafts
                                        │
                                        ▼
             daily-plan-synthesis skill overlays rationale
                                        │
                                        ▼
         Phase B X-rules (X9) → action_detail adjustments
                                        │
                                        ▼
  ATOMIC COMMIT: daily_plan + x_rule_firings
               + planned_recommendation (pre-X-rule aggregate)
               + N recommendation_log (adapted)
                                        │
                                        ▼
             hai today (read) / hai review record (write)
```

- **Local state memory** — ``accepted_*_state_daily`` tables store the
  canonical per-domain day-level state the runtime reasons over.
- **Decision memory** — ``proposal_log`` (per-domain planned intent),
  ``planned_recommendation`` (aggregate pre-X-rule plan), ``daily_plan`` +
  ``x_rule_firing`` + ``recommendation_log`` (aggregate adapted plan)
  preserve the full audit chain: what was originally planned, how X-rules
  mutated it, and what was finally committed.
- **Outcome memory** — ``review_event`` and ``review_outcome`` record how
  the plan went, so the history of decisions and outcomes stays on-device.
- **Agent contract surface** — ``hai capabilities --json`` emits a
  machine-readable manifest of every subcommand; the markdown mirror lives
  at
  [``reporting/docs/agent_cli_contract.md``](reporting/docs/agent_cli_contract.md).
  The ``intent-router`` skill is authoritative for NL → CLI mapping against
  that contract.

See [`reporting/docs/architecture.md`](reporting/docs/architecture.md) for
the full pipeline and the code-vs-skill boundary.

## Roadmap

- **Runtime portability via MCP.** Expose the agent-safe CLI surface as an
  MCP server so any agentic runtime (Claude Code, Codex, others) can drive
  it. Today the project is Claude Code–native; the CLI contract is already
  annotated agent-safe vs. interactive, which maps cleanly onto MCP tool
  schemas.
- **Multi-source wearables.** Apple Health, Oura, Whoop. The adapter
  protocol (`core/pull/protocol.py`) is already source-agnostic; the
  per-domain evidence contract needs to broaden before additional sources
  land. Community adapters welcome — see
  [`reporting/docs/how_to_add_a_pull_adapter.md`](reporting/docs/how_to_add_a_pull_adapter.md).
- **Skill-narration eval harness.** Live-mode pilot shipped (Phase E +
  M8 Phase 4); broader scenario coverage still to come. See
  `safety/evals/skill_harness_blocker.md`.

## What this is not

- Not a medical device, not hosted, not multi-user, not an ML loop. See
  [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md).
- Not meal-level nutrition in v1 — macros only.
- Not an MCP server yet (see Roadmap).
- Not an MCP-wrapper-integrated or skill-harness-eval-complete release yet.

## Dig deeper

1. **Positioning & role map** — [`reporting/docs/personal_health_agent_positioning.md`](reporting/docs/personal_health_agent_positioning.md)
2. **Query taxonomy** — [`reporting/docs/query_taxonomy.md`](reporting/docs/query_taxonomy.md)
3. **Memory model** — [`reporting/docs/memory_model.md`](reporting/docs/memory_model.md)
4. **Architecture overview** — [`reporting/docs/architecture.md`](reporting/docs/architecture.md)
5. **Explainability surface (three-state audit)** — [`reporting/docs/explainability.md`](reporting/docs/explainability.md)
6. **Agent CLI contract (generated manifest)** — [`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md)
7. **X-rule catalogue + sentence explanations** — [`reporting/docs/x_rules.md`](reporting/docs/x_rules.md)
8. **Non-goals (scope discipline)** — [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md)
9. **State schema** — [`reporting/docs/state_model_v1.md`](reporting/docs/state_model_v1.md)
10. **10-minute reading tour** — [`reporting/docs/tour.md`](reporting/docs/tour.md)
11. **Extension path — pull adapter** — [`reporting/docs/how_to_add_a_pull_adapter.md`](reporting/docs/how_to_add_a_pull_adapter.md)
12. **Extension path — new domain** — [`reporting/docs/how_to_add_a_domain.md`](reporting/docs/how_to_add_a_domain.md)
13. **Agent-operable runtime plan (M8 cycle)** — [`reporting/plans/agent_operable_runtime_plan.md`](reporting/plans/agent_operable_runtime_plan.md)
14. **Eval capture** — [`reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/`](reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/)

## CLI surface

```
# Evidence + intake
hai pull [--live] --date <d>                   # Garmin CSV / live pull
hai clean --evidence-json <p>                  # raw → CleanedEvidence + RawSummary
hai intake gym|exercise|nutrition|stress|note|readiness ...

# State
hai state init | migrate | read | snapshot | reproject

# Per-domain debug: use `hai state snapshot --evidence-json <p>` —
# emits classified_state + policy_result for every domain in one call.

# Agent flow (use `hai daily` for the whole loop)
hai daily                                       # morning orchestrator (pull→clean→reproject→propose→synthesize)
hai propose  --domain <d> --proposal-json <p>
hai synthesize --as-of <d> --user-id <u>

# Persistence + review
hai review schedule | record | summary [--domain <d>]

# Agent contract + audit
hai capabilities [--markdown]                   # JSON manifest (or regenerate the contract doc)
hai explain --for-date <d> --user-id <u>        # three-state audit: planned → adapted → performed
hai memory set | list | archive                 # explicit user memory (goals, preferences, constraints)

# Ops
hai init [--with-auth] [--with-first-pull]      # first-run wizard (idempotent)
hai doctor [--json]                             # runtime health + per-source freshness
hai stats [--json]                              # local funnel (sync + command history, daily streak)

# Auth + config + helpers
hai auth garmin | status
hai config init | show
hai exercise search --query <free-text>

# Evals
hai eval run --domain <d> | --synthesis [--json]

hai setup-skills                                # copy packaged skills into ~/.claude/skills/
```

## Repo layout

For a one-page orientation of every top-level entry (active vs historical vs
generated) see [`REPO_MAP.md`](REPO_MAP.md). The package itself:

```
src/health_agent_infra/
├── cli.py                          # hai dispatcher
├── core/
│   ├── schemas.py  validate.py  config.py
│   ├── synthesis.py  synthesis_policy.py
│   ├── writeback/  state/  clean/  pull/  review/
│   ├── memory/  explain/  research/
│   └── intake/
├── domains/
│   ├── recovery/  running/  sleep/  stress/  strength/  nutrition/
│   └── each: schemas.py classify.py policy.py [+ signals/intake]
├── skills/
│   ├── recovery-readiness/  running-readiness/  sleep-quality/
│   ├── stress-regulation/  strength-readiness/  nutrition-alignment/
│   ├── daily-plan-synthesis/  intent-router/  expert-explainer/
│   └── strength-intake/  merge-human-inputs/  review-protocol/
│       reporting/  safety/
├── evals/                          # packaged eval runner + scenarios
└── data/garmin/export/              # committed CSV fixture
reporting/                          # see reporting/README.md
├── docs/                            # architecture, x_rules, non_goals, ...
├── artifacts/flagship_loop_proof/   # eval runner captures
├── plans/                           # post-v0.1 roadmap + historical phase docs
└── experiments/                     # frozen Phase 0.5 / 2.5 prototypes
safety/                             # see safety/README.md
├── tests/                           # 1489 unit + contract + integration
├── evals/                           # eval-doc reference + skill-harness pilot
└── scripts/                         # legacy pre-rebuild demo shim
```

## What's proven

- Six domains end-to-end: classify → policy → skill proposal → synthesis →
  review.
- Ten X-rule evaluators across two phases with atomic transactional commits,
  each firing carrying a stable slug and a one-sentence `human_explanation`
  agents can narrate verbatim.
- Three-state audit chain: `proposal_log` → `planned_recommendation`
  (aggregate pre-X-rule intent, migration 011) → `daily_plan` +
  `recommendation_log` → `review_outcome`. `hai explain` renders all three
  states from persisted rows alone.
- Agent CLI contract: every subcommand annotated with mutation class,
  idempotency, JSON output, exit codes, agent-safe flag; machine-readable
  manifest at `hai capabilities --json`; markdown mirror at
  [`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md).
  Every handler on the stable exit-code taxonomy.
- Authoritative `intent-router` skill consumes the manifest as the NL → CLI
  mapping surface; deliberately scoped so mutation commands are previewed
  before they run.
- Skill-harness pilot: 7 frozen recovery scenarios, 6 with hand-authored
  reference transcripts scoring 2.0/2.0 on the token-presence rubric;
  live-mode backend opt-in via `HAI_SKILL_HARNESS_LIVE=1`.
- Local onboarding + engagement telemetry (migration 012 `runtime_event_log`)
  surfaced via `hai stats`. No data leaves the device.
- Garmin live pull via OS keyring (`hai auth garmin` + `hai pull --live`).
- Idempotent synthesis with optional `--supersede` versioning.
- 28 eval scenarios (18 domain + 10 synthesis) — all deterministic axes green.
- **1489 tests** covering every band, every R-rule, every X-rule, atomic
  transaction semantics, proposal/synthesis invariants, skill-boundary contracts,
  capabilities-manifest coverage + determinism, planned-ledger round-trip,
  three-state explain render, and the new runtime_event_log + hai stats
  paths.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).
