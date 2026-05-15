# AGENTS.md

Operating contract for AI coding agents in this repo. Active scope,
calendar, hypotheses, mechanism inventory, and decisions live in
`PAPER.md`. This file covers governance, boundaries, and code-vs-skill
disciplines that bind every session regardless of who wrote it.

## What This Repo Is For

One artifact: an arXiv preprint of *Deterministic Software Contracts
as Trusted Monitors in AI Control Protocols* by 2026-09-30, with
GovernedAgentBench v1.0 released alongside. Read `PAPER.md` first.

Three active code surfaces:

- **Runtime contract** — the architecture/intervention. Lives in HAI.
- **GovernedAgentBench** — the benchmark measuring contract-governed
  agent operation under a held-constant prompt.
- **HAI** — the personal-wellness reference runtime. Frozen as a
  product per D-11 in `PAPER.md`. v0.2.0 PyPI is the pinned snapshot.

HAI runtime changes ship only via `WP-RUNTIME-FIX-NNN` packets in
service of preprint or benchmark work.

## Active Repo Path

This contract applies at `/Users/domcolligan/health_agent_infra/`. A
stale checkout exists at `~/Documents/health_agent_infra/` (months
behind). Run `pwd` and `git log -1` at session start before reading or
writing planning/source files.

## Code vs Skill

Two surfaces, exactly one lands per contribution.

- **Python runtime** (`hai/src/health_agent_infra/`) — deterministic,
  testable source of truth for data acquisition, projection,
  classification, R-rules, X-rules, synthesis, validation, persistence,
  and CLI behaviour.
- **Markdown skills** (`hai/src/health_agent_infra/skills/`) — judgment
  layer for rationale prose, uncertainty surfacing, clarification, and
  free-text intake routing.

Invariant: skills never mutate actions; code never improvises coaching
prose. By the time a skill runs, the runtime has already computed
`classified_state` and `policy_result`. A skill that re-derives a band,
score, R-rule, or X-rule firing is a bug.

## CLI Boundaries

Agents mutate state only through `hai`:

- `hai propose --domain <d> --proposal-json <p>`
- `hai synthesize --as-of <d> --user-id <u>`
- `hai review record --outcome-json <p>`
- `hai intake {gym,nutrition,stress,note,readiness,weight}`
- `hai intent commit --intent-id <id>` (user-gated, not agent-safe)
- `hai target commit --target-id <id>` (user-gated, not agent-safe)

Never write directly to `state.db`. The CLI contract is
`hai capabilities --json`; read it rather than guessing.

## Governance Invariants

1. **W57.** Agent cannot deactivate user-authored state without
   explicit user commit. Agent-proposed intent/target changes may be
   proposed, but activation/deactivation requires the user-gated
   commit path.
2. **No autonomous plan generation.** Runtime produces daily
   recommendations over user-authored intent. Not training plans or
   diet plans.
3. **No clinical claims.** No diagnosis-shaped language in
   recommendations or rationales. The `safety` skill defines the
   refusal boundary.
4. **Local-first.** State stays in the user's local DB. Package has
   no telemetry path. A hosted agent provider may receive context the
   user gives that provider.
5. **Three-state audit chain is load-bearing.** `proposal_log` →
   `planned_recommendation` → `daily_plan` + `recommendation_log` →
   `review_outcome` must reconcile through `hai explain`.
6. **No bool-as-int silent coercion.** Threshold-consumer sites must
   use `core.config.coerce_int / coerce_float / coerce_bool`. New
   code that constructs threshold dicts and bypasses
   `core.config.load_thresholds` is a code-review concern.

## Architectural Seams

| Concern | Lives in |
|---|---|
| New domain | `hai/src/health_agent_infra/domains/<d>/` + sibling skill |
| New pull source | `hai/src/health_agent_infra/core/pull/`; see `hai/docs/how_to_add_a_pull_adapter.md` |
| Cross-domain logic | `hai/src/health_agent_infra/core/synthesis.py` and `synthesis_policy.py` |
| New CLI command | `hai/src/health_agent_infra/cli/`; annotate capabilities metadata |
| New audit field | Add to write path and to `hai explain` rendering |
| New skill | `hai/src/health_agent_infra/skills/<name>/SKILL.md` |
| New persona archetype | `hai/verification/dogfood/personas/p<N>_<slug>.py` + register in `ALL_PERSONAS` |
| New threshold consumer | Always use `core.config.coerce_*` helpers |

## Test and Tooling Commands

```bash
uv run pytest hai/verification/tests -q
uv run pytest hai/verification/tests/test_<area>.py -q
uvx mypy hai/src/health_agent_infra              # project venv lacks mypy
uvx bandit -ll -r hai/src/health_agent_infra     # project venv lacks bandit
uvx --from build python -m build --wheel --sdist
uv run hai capabilities --json
uv run hai doctor
```

The project venv intentionally omits `mypy`, `bandit`, and `build`. Use
`uvx` to avoid mutating `uv.lock`.

## Do Not Do

- Do not bypass the `hai` CLI for mutations.
- Do not reopen the active D-NN decisions in `PAPER.md` without an
  explicit maintainer call. Historical D-PROJ / D-FRAME / D-PREPRINT
  decision chains live in `ARCHIVE/decisions_log.md`.
- Do not resurrect the NeurIPS 2027 main-conference target, the
  Paper-1+Engels merge, the full predeclared D-FRAME-020 roster, the
  USD 1,500 ceiling, the 50-trajectory adversarial layer, or the
  bounded HS empirical contrast as current scope.
- Do not compute bands, scores, R-rules, or X-rule firings inside a
  skill.
- Do not make clinical claims. No diagnosis, treatment, prescribing,
  or autonomous medical decisions.
- Do not generate training or diet plans.
- Do not deactivate user-authored state without explicit user commit.
- Do not import from `skills/` inside Python runtime code.
- Do not add a write path that bypasses the three-state audit chain.
- Do not open a PR or push autonomously.
- Do not add a wearable source until the per-domain evidence contract
  is broadened.
- Do not add micronutrient or food-taxonomy features.
- Do not treat raw SQLite reads as the normal inspection surface. Use
  `hai today`, `hai explain`, and `hai doctor`.
- Do not anchor a data path on Strava — directly or via an upstream
  that proxies Strava data. Strava's Nov 2024 API agreement prohibits
  AI/ML use; intervals.icu is the supported live source.
- Do not ship a mechanism that auto-loads MCP servers from project
  files. CVE-2025-59536 / CVE-2026-21852 demonstrate the
  autoload + token-exfiltration chain. Manual install + local stdio
  is the only allowed exposure path.
- Do not allow automatic threshold mutation by an LLM agent without
  an explicit user-commit step.
- Do not create new planning files in the active tree. Decisions
  update in place in `PAPER.md`; provenance archives go in `ARCHIVE/`.
  D-13 in `PAPER.md` makes this binding.
- Do not soften the external "AI control paper, AI safety umbrella"
  framing because scope is preprint, not main conference.

## When In Doubt

Read `PAPER.md` and this file. If still unclear, ask Dom rather than
guessing.
