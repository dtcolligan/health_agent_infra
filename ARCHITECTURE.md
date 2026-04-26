# Architecture

One-page architecture. For the full pipeline and every code-vs-skill seam,
see [`reporting/docs/architecture.md`](reporting/docs/architecture.md).

## Single Rule

The project has two surfaces:

- **Python runtime** (`src/health_agent_infra/`) - deterministic. Owns data
  acquisition, projection, classification, R-rules, X-rules, synthesis,
  validation, persistence, and the CLI.
- **Markdown skills** (`src/health_agent_infra/skills/`) - judgment. Own
  rationale prose, uncertainty surfacing, and clarification.

> Skills never change an action; code never writes prose.

## Daily Loop

```text
pull / intake -> projectors -> accepted_*_state_daily tables
                                      |
                                      v
                         hai state snapshot --as-of <date>
                                      |
                                      v
                     domain skills emit DomainProposal x 6
                                      |
                                      v
                              hai propose -> proposal_log
                                      |
                                      v
             Phase A X-rules apply mechanical draft mutations
                                      |
                                      v
                  optional daily-plan-synthesis rationale overlay
                                      |
                                      v
              Phase B X-rules adjust action_detail where allowed
                                      |
                                      v
      atomic commit: daily_plan + x_rule_firing
                   + planned_recommendation + recommendation_log
                                      |
                                      v
                         hai today / hai review record
```

`hai daily` ships the runtime-only path today. The synthesis skill overlay
is an opt-in two-pass path: `hai synthesize --bundle-only`, then
`hai synthesize --drafts-json <p>`.

## Memory Tiers

- **Local state memory** - `accepted_*_state_daily` tables store canonical
  per-domain day-level state.
- **Decision memory** - `proposal_log`, `planned_recommendation`,
  `daily_plan`, `x_rule_firing`, and `recommendation_log` preserve planned
  intent, mutations, and adapted recommendations.
- **Outcome memory** - `review_event` and `review_outcome` record what
  happened, on-device.

## Six Domains

`recovery - running - sleep - stress - strength - nutrition`

Each ships its own `domains/<d>/{schemas,classify,policy}.py` plus a
matching skill. The synthesis layer reconciles proposals through 10 X-rule
evaluators across two phases.

## Agent Contract

`hai capabilities --json` emits the authoritative machine-readable manifest
of every subcommand: mutation class, idempotency, JSON behavior, agent-safe
flag, exit codes, flags, and selected output schemas. The human mirror is
[`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md).

The `intent-router` skill consumes this manifest as the natural-language to
CLI mapping surface.

## Three-State Audit Chain

Every recommendation is reconcilable across persisted rows:

1. **`proposal_log`** - what a per-domain skill proposed.
2. **`planned_recommendation`** - the aggregate pre-X-rule plan.
3. **`daily_plan` + `recommendation_log`** - the adapted committed plan.

`hai explain` renders the chain from persisted rows alone. Every X-rule
firing carries a stable public slug plus a sentence-form explanation.

## Governance Invariants

- W57: agent-proposed intent/target activation requires explicit user commit.
- No autonomous training-plan or diet-plan generation.
- No clinical claims.
- Local-first package posture; no package telemetry.
- No write path bypasses the three-state audit chain.

Full agent-facing guidance is in [AGENTS.md](AGENTS.md).

## Read Deeper

- [`reporting/docs/architecture.md`](reporting/docs/architecture.md) - full pipeline
- [`reporting/docs/explainability.md`](reporting/docs/explainability.md) - three-state audit detail
- [`reporting/docs/x_rules.md`](reporting/docs/x_rules.md) - X-rule catalogue
- [`reporting/docs/state_model_v1.md`](reporting/docs/state_model_v1.md) - state schema
- [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md) - scope discipline
- [`reporting/docs/tour.md`](reporting/docs/tour.md) - 10-minute reading tour
