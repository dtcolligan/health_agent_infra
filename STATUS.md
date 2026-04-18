# Status

## Architecture (v1 rebuild, v0.1.0 released — 2026-04-18)

Health Agent Infra is a multi-domain runtime for a personal health
agent. Six domains (recovery, running, sleep, stress, strength,
nutrition) are first-class, each with schemas + classifier + policy
+ readiness skill. A synthesis layer reconciles per-domain
proposals via ten X-rule evaluators across two phases, commits
atomically to SQLite, and surfaces final per-domain
recommendations through a review loop.

See [`reporting/docs/architecture.md`](reporting/docs/architecture.md).

## What's proven

- **State + projection** — Migrations 001–006 applied;
  ``hai state reproject`` covers recovery, running, sleep, stress,
  strength, and macros-only nutrition.
- **Per-domain runtime** — Every domain ships ``classify.py`` +
  ``policy.py`` + a readiness skill. ``hai classify`` and ``hai
  policy`` debug commands cover recovery today (extension to other
  domains via eval runner).
- **Synthesis** — ``core/synthesis.py`` atomic-commits daily_plan
  + x_rule_firings + N recommendations in one SQLite transaction.
  ``--supersede`` keeps an old plan addressable with a
  ``superseded_by`` pointer; default behaviour replaces cleanly.
- **X-rules** — 10 evaluators (X1a/b, X2, X3a/b, X4, X5, X6a/b,
  X7, X9) with tier precedence (block > soften > cap_confidence >
  adjust) and a Phase B write-surface guard.
- **Live Garmin pull** — ``hai auth garmin`` stores credentials in
  the OS keyring; ``hai pull --live`` fetches a day's evidence via
  ``python-garminconnect``.
- **Eval framework** — ``safety/evals/`` ships 28 scenarios (18
  domain + 10 synthesis) scored against frozen rubrics. All 28
  pass on the Phase 6 checkpoint. Skill-narration axis marked
  ``skipped_requires_agent_harness`` pending the Phase 2.5
  Condition 3 follow-up.
- **Test suite** — 1247 passing, 0 failing across `safety/tests`
  covering schemas, classify, policy, projectors, migrations, CLI
  surfaces, atomic-transaction semantics, skill-boundary contracts,
  eval runner, and scenario pack. The previously known-flaky
  ``test_reproject_clears_manual_stress_for_days_dropped_from_jsonl``
  was fixed in commit ``e52eda3``.

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

## What's next (post-release)

The rebuild plan is complete through `v0.1.0`:
- Step 1 — ``hai daily`` morning orchestrator (commit ``e875bb2``).
- Step 2 — ``hai init`` first-run wizard, ``hai doctor``, ``hai
  --version`` (commit ``3afad17``).
- Step 3 — packaging + CI readiness (wheel/sdist build, install
  smoke-test, matrix CI; commit ``64961fc``).
- Step 4 — launch artifact at
  [`reporting/plans/launch_notes.md`](reporting/plans/launch_notes.md).
 - Release ops — merged to ``main``, tagged ``v0.1.0``, and
   published to TestPyPI + PyPI with clean-venv smoke tests.

Still optional / deferred post-release:
- Optional MCP server wrapper (``hai mcp serve``) — deferred,
  CLI surface is sufficient for `0.1.0`.

Open cross-phase questions tracked at ``reporting/plans/comprehensive_rebuild_plan.md`` §8:

- Apple Health adapter timing (post-Phase-7, demand-driven).
- Learning loop design (no ML in v1; revisit post-launch).
- Goal-specific recommendation logic (periodization, taper,
  bulk/cut) — deferred post-launch.
- Food database maintenance + meal-level re-gate (deferred until
  the three structural retrieval failure classes are fixed).
