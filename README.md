# Health Agent Infra

**Health Agent Infra is a governed runtime for a multi-domain
personal health agent.** One Claude agent reads a cross-domain
state snapshot, emits per-domain proposals via domain skills, and a
synthesis skill reconciles them via codified cross-domain rules
into bounded per-domain recommendations validated at the ``hai
writeback`` boundary.

Its source of truth is a **local SQLite database on the user's
device**. That local state persists accepted daily state, proposal
history, synthesized plans, final recommendations, and review
outcomes across days, so the agent resumes from runtime state
rather than from chat memory alone.

It is not a chatbot, a wearable API, a general AI health app, or a
clinical product. It is infrastructure the agent consumes:
**deterministic Python tools** that ingest evidence, classify state,
apply policy, run synthesis, and persist recommendations, plus
**markdown skills** that instruct the agent in how to compose
rationale and surface uncertainty once actions are mechanically
constrained.

- Python = tools (data acquisition, projection, band classification,
  R-rule + X-rule evaluation, schema validation, atomic
  transactions, evals).
- Markdown = skills (judgment: picking from an already-constrained
  action set, composing rationale, surfacing uncertainty).
- The code-vs-skill boundary is tight and the plan documents it.
  Skills never change an action; code never writes prose.

## Six domains in v1

recovery · running · sleep · stress · strength · nutrition

Each ships per-domain schemas, classify, policy, a readiness skill,
and is wired into the synthesis X-rule catalogue. Nutrition is
macros-only in v1 (no meal-level / food taxonomy / micronutrient
inference) per the Phase 2.5 retrieval-gate outcome — see
[``reporting/docs/non_goals.md``](reporting/docs/non_goals.md).

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
  ATOMIC COMMIT: daily_plan + x_rule_firings + N recommendations
                                        │
                                        ▼
             hai review schedule / record / summary
```

- **Local state memory** — ``accepted_*_state_daily`` tables store
  the canonical per-domain day-level state the runtime reasons over.
- **Decision memory** — ``proposal_log``, ``daily_plan``,
  ``x_rule_firing``, and ``recommendation_log`` preserve what the
  agent proposed, what synthesis changed, and what was finally
  committed.
- **Outcome memory** — ``review_event`` and ``review_outcome``
  record how the plan went, so the history of decisions and outcomes
  stays on-device.

See [``reporting/docs/architecture.md``](reporting/docs/architecture.md)
for the full pipeline + code-vs-skill boundary.

## Install

```bash
pip install -e .              # local editable install
# or: pip install health-agent-infra
hai setup-skills              # copies skills into ~/.claude/skills/
hai state init                # creates the local on-device memory store
hai --help
```

## CLI surface

```
# Evidence + intake
hai pull [--live] --date <d>                   # Garmin CSV / live pull
hai clean --evidence-json <p>                  # raw → CleanedEvidence + RawSummary
hai intake gym|exercise|nutrition|stress|note|readiness ...

# State
hai state init | migrate | read | snapshot | reproject

# Per-domain debug
hai classify --domain <d> --evidence-json <p>
hai policy   --domain <d> --evidence-json <p>

# Agent flow
hai propose  --domain <d> --proposal-json <p>
hai synthesize --as-of <d> --user-id <u>

# Persistence + review
hai writeback --recommendation-json <p>
hai review schedule | record | summary [--domain <d>]

# Auth + config + helpers
hai auth garmin | status
hai config init | show
hai exercise search --query <free-text>

# Evals
hai eval run --domain <d> | --synthesis [--json]

hai setup-skills
```

## Read this repo in 5 minutes

1. **Architecture overview** — [`reporting/docs/architecture.md`](reporting/docs/architecture.md)
2. **X-rule catalogue** — [`reporting/docs/x_rules.md`](reporting/docs/x_rules.md)
3. **Non-goals (scope discipline)** — [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md)
4. **State schema** — [`reporting/docs/state_model_v1.md`](reporting/docs/state_model_v1.md)
5. **10-minute reading tour** — [`reporting/docs/tour.md`](reporting/docs/tour.md)
6. **Eval capture** — [`reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/`](reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/)

## Repo layout

```
src/health_agent_infra/
├── cli.py                          # hai dispatcher
├── core/
│   ├── schemas.py  validate.py  config.py
│   ├── synthesis.py  synthesis_policy.py
│   ├── writeback/  state/  clean/  pull/  review/
│   └── intake/
├── domains/
│   ├── recovery/  running/  sleep/  stress/  strength/  nutrition/
│   └── each: schemas.py classify.py policy.py [+ signals/intake]
├── skills/
│   ├── recovery-readiness/  running-readiness/  sleep-quality/
│   ├── stress-regulation/  strength-readiness/  nutrition-alignment/
│   ├── daily-plan-synthesis/
│   └── strength-intake/  merge-human-inputs/  writeback-protocol/
│       reporting/  safety/
└── data/garmin/export/              # committed CSV fixture
reporting/
├── docs/                            # architecture, x_rules, non_goals, ...
├── artifacts/flagship_loop_proof/   # eval runner captures
├── plans/                           # comprehensive rebuild plan + gates
└── experiments/                     # Phase 0.5 / 2.5 throwaway prototypes
safety/
├── tests/                           # 1200+ unit + contract + integration
└── evals/                           # Phase 6 eval framework (28 scenarios)
```

## What's proven in v1

- Six domains end-to-end: classify → policy → skill proposal →
  synthesis → writeback → review.
- Ten X-rule evaluators across two phases with atomic
  transactional commits.
- Garmin live pull via keyring (``hai auth garmin`` + ``hai pull
  --live``).
- Idempotent synthesis with optional ``--supersede`` versioning.
- 28 eval scenarios (18 domain + 10 synthesis) all green.
- 1200+ tests covering every band, every R-rule, every X-rule,
  atomic transaction semantics, writeback invariants, skill-boundary
  contracts.

## What's not

- Not a medical device, not hosted, not multi-user, not an ML
  loop. See [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md).
- Not meal-level nutrition in v1.
- Not a skill-narration eval harness yet (Phase 2.5 Track B
  Condition 3 deferred — see ``safety/evals/skill_harness_blocker.md``).
- Not an MCP-wrapper-integrated or skill-harness-eval-complete release yet.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The authoritative rebuild
plan lives at
``.claude/worktrees/hardcore-kare-a92e25/reporting/plans/comprehensive_rebuild_plan.md``.
