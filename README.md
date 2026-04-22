# Health Agent Infra

**Health Agent Infra is a governed, agent-operable runtime for a
multi-domain personal health agent.** One Claude agent reads a
cross-domain state snapshot, emits per-domain proposals via domain
skills, and a synthesis skill reconciles them via codified
cross-domain rules into bounded per-domain recommendations validated
at atomic commit. Every CLI subcommand carries machine-readable
contract metadata (mutation class, idempotency, exit codes) that an
agent reads via ``hai capabilities --json``; an authoritative
``intent-router`` skill maps natural-language intent to deterministic
workflows against that contract. Every X-rule firing carries both a
stable slug and a sentence-form explanation an agent can narrate
verbatim.

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
  ATOMIC COMMIT: daily_plan + x_rule_firings
               + planned_recommendation (pre-X-rule aggregate)
               + N recommendation_log (adapted)
                                        │
                                        ▼
             hai review schedule / record / summary
```

- **Local state memory** — ``accepted_*_state_daily`` tables store
  the canonical per-domain day-level state the runtime reasons over.
- **Decision memory** — ``proposal_log`` (per-domain planned intent),
  ``planned_recommendation`` (aggregate pre-X-rule plan),
  ``daily_plan`` + ``x_rule_firing`` + ``recommendation_log``
  (aggregate adapted plan) preserve the full audit chain: what was
  originally planned, how X-rules mutated it, and what was finally
  committed.
- **Outcome memory** — ``review_event`` and ``review_outcome``
  record how the plan went, so the history of decisions and outcomes
  stays on-device.
- **Agent contract surface** — ``hai capabilities --json`` emits a
  machine-readable manifest of every subcommand; the markdown mirror
  lives at
  [``reporting/docs/agent_cli_contract.md``](reporting/docs/agent_cli_contract.md).
  The ``intent-router`` skill is authoritative for NL → CLI mapping
  against that contract.

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
hai daily                                      # morning orchestrator (pull→clean→reproject→propose→synthesize)

# Persistence + review
hai writeback --recommendation-json <p>  # recovery-only legacy direct path
hai review schedule | record | summary [--domain <d>]

# Agent contract + audit
hai capabilities [--markdown]                  # JSON manifest (or regenerate the contract doc)
hai explain --for-date <d> --user-id <u>       # three-state audit: planned → adapted → performed
hai memory set | list | archive                # explicit user memory (goals, preferences, constraints)

# Ops
hai doctor [--json]                            # runtime health + per-source freshness
hai init                                       # interactive first-run wizard

# Auth + config + helpers
hai auth garmin | status
hai config init | show
hai exercise search --query <free-text>

# Evals
hai eval run --domain <d> | --synthesis [--json]

hai setup-skills                               # copy 14 packaged skills into ~/.claude/skills/
```

## Read this repo in 5 minutes

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

## Repo layout

For a one-page orientation of every top-level entry (active vs
historical vs generated) see [`REPO_MAP.md`](REPO_MAP.md). The
package itself looks like this:

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
│   └── strength-intake/  merge-human-inputs/  writeback-protocol/
│       reporting/  safety/
├── evals/                          # packaged eval runner + scenarios
└── data/garmin/export/              # committed CSV fixture
reporting/                          # see reporting/README.md
├── docs/                            # architecture, x_rules, non_goals, ... (+ archive/)
├── artifacts/flagship_loop_proof/   # eval runner captures (+ archive/, phase_0/)
├── plans/                           # post-v0.1 roadmap + historical phase docs
└── experiments/                     # frozen Phase 0.5 / 2.5 prototypes
safety/                             # see safety/README.md
├── tests/                           # 1459 unit + contract + integration
├── evals/                           # eval-doc reference + skill-harness pilot
└── scripts/                         # legacy pre-rebuild demo shim (do not run)
merge_human_inputs/                 # docs + example payloads bucket; not a Python module
```

## What's proven

- Six domains end-to-end: classify → policy → skill proposal →
  synthesis → writeback → review.
- Ten X-rule evaluators across two phases with atomic
  transactional commits, each firing carrying a stable slug and a
  one-sentence `human_explanation` agents can narrate verbatim.
- Three-state audit chain: `proposal_log` → `planned_recommendation`
  (aggregate pre-X-rule intent, migration 011) → `daily_plan` +
  `recommendation_log` → `review_outcome`. `hai explain` renders
  all three states from persisted rows alone.
- Agent CLI contract: every subcommand annotated with mutation class,
  idempotency, JSON output, exit codes, agent-safe flag; machine-
  readable manifest at `hai capabilities --json`; markdown mirror
  at [`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md).
  Every handler on the stable exit-code taxonomy.
- Authoritative `intent-router` skill consumes the manifest as the
  NL → CLI mapping surface; deliberately scoped so mutation commands
  are previewed before they run.
- Skill-harness pilot: 7 frozen recovery scenarios, 6 with
  hand-authored reference transcripts scoring 2.0/2.0 on the
  token-presence rubric; live-mode backend opt-in via
  `HAI_SKILL_HARNESS_LIVE=1`.
- Garmin live pull via keyring (``hai auth garmin`` + ``hai pull
  --live``).
- Idempotent synthesis with optional ``--supersede`` versioning.
- 28 eval scenarios (18 domain + 10 synthesis) — all deterministic
  axes green.
- 1459 tests covering every band, every R-rule, every X-rule,
  atomic transaction semantics, writeback invariants, skill-boundary
  contracts, capabilities-manifest coverage + determinism, planned-
  ledger round-trip, three-state explain render.

## What's not

- Not a medical device, not hosted, not multi-user, not an ML
  loop. See [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md).
- Not meal-level nutrition in v1.
- Skill-narration eval harness is shipped as a pilot (Phase E +
  M8 Phase 4) but still opt-in; live-transcript capture remains
  operator-driven. See ``safety/evals/skill_harness_blocker.md``.
- Not an MCP-wrapper-integrated or skill-harness-eval-complete release yet.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). The authoritative rebuild
plan lives at
``.claude/worktrees/hardcore-kare-a92e25/reporting/plans/comprehensive_rebuild_plan.md``.
