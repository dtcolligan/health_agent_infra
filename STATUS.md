# Status

## Architecture (v1 rebuild, v0.1.0 released — 2026-04-18; M8 agent-operable cycle — 2026-04-22)

Health Agent Infra is a **governed, agent-operable runtime** for a
multi-domain personal health agent. Six domains (recovery, running,
sleep, stress, strength, nutrition) are first-class, each with
schemas + classifier + policy + readiness skill. A synthesis layer
reconciles per-domain proposals via ten X-rule evaluators across
two phases, commits atomically to SQLite alongside a pre-mutation
`planned_recommendation` ledger, and surfaces final per-domain
recommendations through a review loop. Every CLI subcommand carries
machine-readable contract metadata (`hai capabilities --json`); an
authoritative `intent-router` skill maps natural-language intent to
deterministic workflows against that contract.

See [`reporting/docs/architecture.md`](reporting/docs/architecture.md)
and [`reporting/plans/agent_operable_runtime_plan.md`](reporting/plans/agent_operable_runtime_plan.md).

## What's proven

- **State + projection** — Migrations 001–006 applied;
  ``hai state reproject`` covers recovery, running, sleep, stress,
  strength, and macros-only nutrition.
- **Per-domain runtime** — Every domain ships ``classify.py`` +
  ``policy.py`` + a readiness skill. ``hai classify`` and ``hai
  policy`` debug commands cover recovery today (extension to other
  domains via eval runner).
- **Synthesis** — ``core/synthesis.py`` atomic-commits daily_plan +
  x_rule_firings + N recommendations + N planned_recommendation rows
  (the pre-X-rule aggregate ledger, migration 011) in one SQLite
  transaction. ``--supersede`` keeps an old plan addressable with a
  ``superseded_by`` pointer; default behaviour replaces cleanly.
- **Three-state audit chain** — `proposal_log` → `planned_recommendation`
  → `daily_plan` + `recommendation_log` → `review_outcome` is fully
  walkable from persisted rows alone. `hai explain` renders all three
  states side-by-side; every X-rule firing carries a machine-readable
  slug (`sleep-debt-softens-hard`) plus a sentence-form
  `human_explanation` an agent can narrate verbatim.
- **Agent CLI contract** — `hai capabilities --json` emits a
  manifest of every subcommand (mutation class, idempotency, JSON
  output, exit codes, agent-safe flag). Markdown mirror committed at
  [`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md).
  Every handler is on the stable `OK` / `USER_INPUT` / `TRANSIENT` /
  `NOT_FOUND` / `INTERNAL` taxonomy; no `LEGACY_0_2` sentinels remain.
- **Intent routing** — the `intent-router` skill consumes the
  capabilities manifest and maps natural-language intent to CLI
  workflows. Authoritative for every agent host.
- **X-rules** — 10 evaluators (X1a/b, X2, X3a/b, X4, X5, X6a/b,
  X7, X9) with tier precedence (block > soften > cap_confidence >
  adjust) and a Phase B write-surface guard.
- **Live Garmin pull** — ``hai auth garmin`` stores credentials in
  the OS keyring; ``hai pull --live`` fetches a day's evidence via
  ``python-garminconnect``.
- **Eval framework** — packaged at
  ``src/health_agent_infra/evals/`` (runner + CLI + scenarios +
  rubrics ship inside the wheel; ``hai eval run`` works from any
  cwd in any install). 28 scenarios total (18 domain + 10
  synthesis) scored against frozen rubrics. All deterministic
  axes pass on the Phase 6 checkpoint; the skill-narration axis is
  marked ``skipped_requires_agent_harness`` per scenario, pending
  the Phase 2.5 Condition 3 follow-up.
- **Test suite** — 1459 passing, 0 failing across `safety/tests`
  covering schemas, classify, policy, projectors, migrations (001–011),
  CLI surfaces, atomic-transaction semantics, skill-boundary contracts,
  eval runner, scenario pack, capabilities-manifest coverage +
  determinism, planned-ledger round-trip (`planned ⊕ firings =
  adapted`), three-state explain render, X-rule sentence registry,
  and the skill-harness replay shim (6 of 7 recovery branches
  transcript-covered).

## Install

```bash
pip install -e .
hai setup-skills
hai state init
hai --help
```

See [`README.md`](README.md) for the full subcommand list and
[`reporting/docs/agent_integration.md`](reporting/docs/agent_integration.md)
for Claude Code / Agent SDK wiring.

## Non-goals

- Not a clinical product or medical device.
- Not hosted or multi-user.
- Not an ML / learning loop (review records outcomes; does not
  feed back).
- Not a multi-source fusion platform (Garmin + user intake only
  in v1).
- Not meal-level nutrition / food taxonomy / micronutrient
  inference in v1 (deferred post-Phase-2.5 retrieval-gate).
- Not a skill-narration eval harness yet (deferred).

See [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md) for
the full list with rationale.

## Phase progression

| Phase | Scope | Status |
|---|---|---|
| 0 | Preflight on existing system | complete |
| 0.5 | Synthesis feasibility prototype | complete (GO for Phase 1) |
| 1 | Core reshape + recovery classify/policy | complete |
| 2 | Running + synthesis activation + live pull | complete |
| 2.5 | Retrieval gate + independent eval pack | complete (macros-only nutrition; GO for Phase 3) |
| 3 | Sleep + stress domains | complete |
| 4 | Strength domain | complete (+ ``hai intake exercise`` follow-up) |
| 5 | Nutrition domain (macros-only) | complete |
| 6 | Eval harness + docs | complete |
| 7 | Polish + publish | complete (`v0.1.0` released) |
| 8 | Agent-operable runtime cycle | complete (see `reporting/plans/agent_operable_runtime_plan.md`) |

## What's next (post-M8)

The M8 cycle shipped every essential from
[`reporting/plans/agent_operable_runtime_plan.md`](reporting/plans/agent_operable_runtime_plan.md)
(Phases 1–5). The post-v0.1 roadmap's A–D are also complete; E, F, G are
status-updated in [`reporting/plans/post_v0_1_roadmap.md`](reporting/plans/post_v0_1_roadmap.md).

Explicitly deferred follow-ups (in priority order):

- **Phase M — active protocol layer.** Revisit only after the
  planned-snapshot ledger has accumulated a cycle of data that shows
  what durable multi-day intent is actually load-bearing. See the M8
  plan §5.
- **Skill-harness live-transcript capture.** Pilot shipped
  hand-authored reference transcripts for 6 of 7 recovery branches;
  capturing live transcripts via `HAI_SKILL_HARNESS_LIVE=1` is an
  operator-driven step (needs API key / Claude Code session).
- **Second-domain skill-harness expansion** (sleep / stress /
  running). Runner is recovery-coupled; generalising it is a
  meaningful refactor.
- **LLM-judge rubric axis.** Rubric reserves space; ship deferred.
- **Optional MCP server wrapper.** CLI surface is sufficient today.
- **Apple Health adapter.** Demand-driven; no work planned.
- **Learning loop / goal-specific periodization / meal-level
  nutrition.** Non-goals in this cycle; revisit with explicit RFC.
