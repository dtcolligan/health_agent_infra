# AGENTS.md - Health Agent Infra

Briefing for any AI coding agent opening a session in this repo. Read this
first; it is the project-specific operating contract.

## What This Project Is

Health Agent Infra is a local-first governance layer for personal-health
agents. A host agent reads governed snapshots, uses packaged skills to
compose bounded proposals, and relies on the Python runtime to validate,
reconcile, and commit decisions to local SQLite state.

The unit of shipping is a Python wheel (`health-agent-infra`) plus markdown
skills consumed by the agent at runtime. The maintainer's daily development
loop is Claude Code over this project's own `hai` CLI; the project is its
own dogfood.

Authoritative orientation:

- `README.md` - product story, install, CLI surface
- `ARCHITECTURE.md` - one-page architecture
- `REPO_MAP.md` - every top-level entry classified active/historical
- `reporting/docs/architecture.md` - full pipeline and code-vs-skill boundary
- `reporting/docs/non_goals.md` - scope discipline
- `reporting/plans/multi_release_roadmap.md` - release-by-release roadmap
- `AUDIT.md` - release-by-release audit index

## Code Vs Skill

The project has two surfaces. Every contribution lands in exactly one:

- **Python runtime** (`src/health_agent_infra/`) - deterministic, testable
  source of truth for data acquisition, projection, classification bands,
  R-rules, X-rules, synthesis, validation, persistence, and CLI behavior.
- **Markdown skills** (`src/health_agent_infra/skills/`) - judgment layer for
  rationale prose, uncertainty surfacing, clarification, and free-text intake
  routing.

The invariant:

> Skills never change an action; code never writes prose.

If it must be reproducible across model moods, it belongs in Python. If it
is phrasing, framing, or honest uncertainty, it belongs in a skill.

By the time a skill runs, the runtime has already computed
`classified_state` and `policy_result`. A skill that re-derives a band,
score, R-rule, or X-rule firing is a bug.

## CLI Boundaries

Skills and agents mutate state only through `hai`:

- `hai propose --domain <d> --proposal-json <p>` - validate and persist a
  domain proposal.
- `hai synthesize --as-of <d> --user-id <u>` - reconcile proposals and commit
  the daily plan atomically.
- `hai review record --outcome-json <p>` - log an outcome.
- `hai intake gym|nutrition|stress|note|readiness` - record user inputs.
- `hai intent commit --intent-id <id>` and `hai target commit --target-id
  <id>` - promote proposed intent/target rows; these are not agent-safe and
  require explicit user invocation.

Agents must not write directly to `state.db`. The CLI contract is
`hai capabilities --json`; read it rather than guessing.

## Six Domains

`recovery - running - sleep - stress - strength - nutrition`

Each has `domains/<d>/{schemas,classify,policy}.py` and a matching skill.
The synthesis layer (`core/synthesis.py` plus optional
`daily-plan-synthesis` overlay) reconciles the domains.

Nutrition is macros-only in v1. Do not propose food-taxonomy, meal-level, or
micronutrient features without a new scoped plan.

## Governance Invariants

1. **W57 - agent cannot deactivate user state without explicit user commit.**
   Agent-proposed intent/target changes may be proposed, but activation or
   deactivation requires the user-gated commit path.
2. **No autonomous plan generation.** The runtime produces daily
   recommendations over user-authored intent. It does not generate training
   plans or diet plans.
3. **No clinical claims.** No diagnosis-shaped language in recommendations or
   rationales. The safety skill defines the refusal boundary.
4. **Local-first package posture.** State stays in the user's local DB; the
   package has no telemetry path. A hosted agent provider may still receive
   context the user gives that provider.
5. **Three-state audit chain is load-bearing.** `proposal_log` ->
   `planned_recommendation` -> `daily_plan` + `recommendation_log` ->
   `review_outcome` must reconcile through `hai explain`.
6. **Review-summary bool-as-int hardening.** `followed_recommendation`,
   `self_reported_improvement`, and `policy.review_summary` runtime threshold
   values reject bool-shaped numeric inputs. Global threshold-runtime type
   hardening remains v0.1.9 backlog.

## Settled Decisions - Do Not Reopen Casually

These were decided across audit cycles. If you think one needs revisiting,
write a cycle proposal in `reporting/plans/`; do not act unilaterally.

- **W37 original shape is dead.** Skills do not compute review-outcome
  pattern tokens. W48 replaced it with code-owned
  `core/review/summary.py`.
- **W39 narrowed.** Threshold override loading already exists. v0.1.8 scope
  was validation/diff/auditability, not re-implementation.
- **W47 is cut.** Keep release-proof/changelog discipline, but do not add a
  working-tree-sensitive changelog test.
- **W29 / W30 deferred.** Do not split `cli.py`. Do not freeze the
  capabilities manifest schema yet.
- **Garmin Connect is not the default live source.** Login is rate-limited
  and unreliable. Default to intervals.icu when configured.
- **Nutrition v1 is macros-only.**
- **No `STATUS.md`.** Status lives in CHANGELOG, AUDIT, ROADMAP, and
  ARCHITECTURE; do not resurrect a parallel status file without a new
  maintainer decision.

## Release Cycle Expectation

Substantive releases run structured Codex audit/response rounds under
`reporting/plans/v0_1_X/`. v0.1.8 stabilized the four-round pattern:

1. `PLAN.md` names the release scope.
2. `codex_audit_prompt.md` -> `codex_audit_response.md` records round 1.
3. Maintainer response files address findings with code changes, deferrals,
   or explicit disagreement.
4. Subsequent implementation-review rounds continue until the verdict is
   `SHIP` or `SHIP_WITH_NOTES`.
5. `RELEASE_PROOF.md` and `REPORT.md` record the final state.

Do not ship a substantive release without release proof. Smaller doc-only
changes can be scoped by Dom, but do not silently weaken the audit
convention.

## Test Commands

```bash
uv run pytest safety/tests -q
uv run pytest safety/tests/test_<area>.py -q
uv run python -m build --wheel --sdist     # if packaging changed
uv run hai capabilities --json             # if CLI surface changed
uv run hai doctor                          # if migrations/state changed
```

CI runs `safety/tests/`. The suite includes docs and skill/CLI drift checks.

## Architectural Seams

| Concern | Lives in |
|---|---|
| New domain | `src/health_agent_infra/domains/<d>/` plus a sibling skill |
| New pull source | `src/health_agent_infra/core/pull/`; see `reporting/docs/how_to_add_a_pull_adapter.md` |
| Cross-domain logic | `src/health_agent_infra/core/synthesis.py` and `synthesis_policy.py` |
| New CLI command | `src/health_agent_infra/cli.py`; annotate capabilities metadata |
| New audit field | Add to the write path and to `hai explain` rendering |
| New skill | `src/health_agent_infra/skills/<name>/SKILL.md` with valid frontmatter |

## Do Not Do

- Do not bypass the `hai` CLI for mutations.
- Do not compute bands, scores, R-rules, or X-rule firings inside a skill.
- Do not make clinical claims.
- Do not generate training or diet plans.
- Do not deactivate user-authored state without explicit user commit.
- Do not import from `skills/` inside Python runtime code.
- Do not add a write path that bypasses the three-state audit chain.
- Do not open a PR or push autonomously.
- Do not add a wearable source until the per-domain evidence contract is
  broadened.
- Do not split `cli.py` or freeze the capabilities manifest schema in this
  cycle.
- Do not add micronutrient or food-taxonomy features.
- Do not treat raw SQLite reads as the normal inspection surface; use
  `hai today`, `hai explain`, and `hai doctor`.

## When In Doubt

Read `README.md`, `REPO_MAP.md`, `reporting/docs/architecture.md`,
`reporting/docs/non_goals.md`, then the current cycle's plan. If still
unclear, ask Dom rather than guessing.
