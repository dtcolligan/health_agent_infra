# Codex Work Inspection Index

**Status:** inspection guide for Codex autonomous work through commit
`6ce5f58 docs(research): add codex work inspection index`, with a
Claude Code audit-prompt pointer added 2026-05-10.

This file is a navigation aid. It does not replace
`AUTONOMOUS_PROJECT_EXECUTION_PLAN.md`, does not create a new project
status authority, and does not authorize model runs. Use it to inspect
what changed, where it lives, and what remains blocked.

## Start Here

Read these in order:

1. `research/runtime_contracts_paper/AUTONOMOUS_PROJECT_EXECUTION_PLAN.md`
   - the authoritative end-to-end plan, phase order, packet queue,
     acceptance evidence, commit boundaries, and stop gates.
2. `research/runtime_contracts_paper/AUTONOMOUS_GATE_HANDOFF.md`
   - the current completion audit and the reason execution is blocked.
3. `research/runtime_contracts_paper/CLAUDE_CODE_COMPREHENSIVE_AUDIT_PROMPT.md`
   - the adversarial review prompt for Claude Code to audit all Codex
     work before Dom reads it.
4. `research/runtime_contracts_paper/MODEL_ROSTER_DECISION_BRIEF.md`
   - the Dom decision needed before model-backed experiments or final
     claims.
5. `benchmark/governed_agent_bench/BENCHMARK_CARD.md`
   - the benchmark-facing summary of intended use, non-use, data
     provenance, tested condition, limitations, and reproducibility.
6. `benchmark/governed_agent_bench/REPRODUCIBILITY.md`
   - the offline rerun path for synthetic fixtures, rule baseline,
     scores, evidence tables, figures, and error taxonomy.

## What Was Organized

The repo is intentionally kept in the existing owner lanes:

| Lane | Purpose | Main inspection targets |
|---|---|---|
| `research/runtime_contracts_paper/` | Project plan, paper scaffolding, evidence interpretation, gate handoff. | Plan, handoff, decision brief, prior-art matrix, related-work draft, methods/system draft. |
| `benchmark/governed_agent_bench/` | GovernedAgentBench tasks, fixtures, harness, scorer, baseline, reports, benchmark docs. | README, benchmark card, fixtures, manifests, tasks, hand-authored trajectories, scorer, harness, results, reproducibility. |
| `benchmark/verification/tests/` | Benchmark verification and regression tests. | Schema, fixture, harness, scorer, baseline, results, and reproduction tests. |
| `hai/src/health_agent_infra/` | HAI runtime contract support surface. | Hermetic guard, runtime modes, refusal enforcement, `agent_safe`, manifest metadata. |
| `hai/verification/tests/` | HAI runtime verification. | Runtime mode, refusal, dispatch, manifest, and contract tests. |

No files were renamed or relocated as part of the inspection-index packet
itself. The later audit-response hardening renamed only the stale drift
manifest from `hai_0_1_18_drift.json` to
`agent_cli_contract_v1_drift.json` so the filename no longer contradicts
the embedded `hai_version`. Runtime and benchmark implementation changes
otherwise modify files in place.

## Current Gate

The active gate is `WP-MODEL-ROSTER-001`.

Current facts:

- `benchmark/governed_agent_bench/model_roster.md` does not exist.
- no model-backed trajectories have been produced;
- no local model inference, local model download, cloud model API, paid
  API, private health data, live credential, or live wearable data was
  used;
- `benchmark/governed_agent_bench/schema/model_roster.schema.json`
  defines the future roster format, but it is not a roster and does not
  authorize a run;
- further execution requires Dom to choose either a predeclared
  model-roster path or a rule-baseline-only T0 workshop path.

## Committed Work To Inspect

The core clean autonomous execution packet range starts at the plan
commit and runs through the inspection-index commit:

```bash
git log --oneline --reverse 2f0d95f^..HEAD
```

Packet groups:

| Group | Commits | What to inspect |
|---|---|---|
| Plan and queue | `2f0d95f`, `4044188`, `76b7408` | Authoritative project plan, completed-work ledger, next blocked packets. |
| HAI runtime substrate | `b81c29e` | Remaining runtime-mode off paths and mechanism-off markers. |
| Benchmark current state | `9e93dd2`, `2bedf67` | Benchmark README state aligned to actual fixture/task/scorer readiness. |
| Harness | `58ed8c7`, `906750e`, `01309f5`, `caad0b8` | Model-agnostic harness, invocation context, marker capture, deployment prompt rendering. |
| Benchmark validation | `28a1d7c`, `a9fdac9`, `a86ae9b` | Hand-authored trajectories, known-good/known-bad validation, load-bearing task coverage. |
| Baseline and ablation | `75af33f`, `3235d3e` | Rule baseline and offline ablation dry-run path. |
| Evidence generation | `28e217f`, `590b098`, `d0c14b8` | Evidence tables, reproducible SVG figures, error taxonomy. |
| Reproducibility | `e6f21cd` | Offline reproduction command and manifest. |
| Paper scaffolding | `3cdd69b`, `9d53167`, `8aff352` | Prior-art matrix, related-work draft, methods/system draft. |
| Benchmark documentation | `0c9b4e4`, `11ee252`, `b3e2eae` | Operator view, scaffold view, benchmark card. |
| Gate documentation | `dcb726c`, `66164ae`, `c76db96` | Gate handoff, model-roster decision brief, refreshed blocked-state audit. |
| Future roster format | `7b692f5` | Model roster schema and focused schema tests, without creating a roster. |
| Claude audit response | `9552b36`, `e390f3c`, `2373c93`, `2455967`, `0a98ffa`, `420511e` | Scorer coverage, shared clinical refusal phrases, L5/L7 exhibits, stale-manifest provenance cleanup, evidence-limit disclosures, adversarial-fixture reseeding. |

Useful inspection commands:

```bash
git show --stat 2f0d95f
git show --stat 58ed8c7
git show --stat 75af33f
git show --stat e6f21cd
git show --stat 66164ae
git show --stat 7b692f5
git show --stat c76db96
```

## Artifact Map

| Question | Read |
|---|---|
| What is the end-to-end plan? | `research/runtime_contracts_paper/AUTONOMOUS_PROJECT_EXECUTION_PLAN.md` |
| What is done, blocked, and why? | `research/runtime_contracts_paper/AUTONOMOUS_GATE_HANDOFF.md` |
| What should Claude Code use to audit Codex's work? | `research/runtime_contracts_paper/CLAUDE_CODE_COMPREHENSIVE_AUDIT_PROMPT.md` |
| What decision does Dom need to make? | `research/runtime_contracts_paper/MODEL_ROSTER_DECISION_BRIEF.md` |
| What would a future model roster have to contain? | `benchmark/governed_agent_bench/schema/model_roster.schema.json` |
| What is the benchmark? | `benchmark/governed_agent_bench/BENCHMARK_CARD.md` |
| How do I rerun the offline evidence path? | `benchmark/governed_agent_bench/REPRODUCIBILITY.md` |
| How are model/operator actions represented? | `benchmark/governed_agent_bench/schema/operator_action.schema.json` |
| How are trajectories scored? | `benchmark/governed_agent_bench/scorer/core.py` |
| What tasks exist? | `benchmark/governed_agent_bench/tasks/` |
| What synthetic users exist? | `benchmark/governed_agent_bench/fixtures/` |
| What example trajectories prove the scorer? | `benchmark/governed_agent_bench/trajectories/hand_authored/` |
| What rule baseline was run? | `benchmark/governed_agent_bench/baselines/rule_baseline.py` |
| What figures/tables/taxonomy are generated? | `benchmark/governed_agent_bench/results/` |
| What paper text exists so far? | `research/runtime_contracts_paper/RELATED_WORK_DRAFT.md` and `research/runtime_contracts_paper/METHODS_SYSTEM_DRAFT.md` |

## Verification Commands

Focused checks for the latest gate and schema organization:

```bash
uv run pytest benchmark/verification/tests/test_model_roster_schema.py -q
test ! -e benchmark/governed_agent_bench/model_roster.md
```

Broader benchmark checks used during the work:

```bash
uv run pytest benchmark/verification/tests -q
uv run pytest benchmark/verification/tests/test_governed_agent_bench_schema_contracts.py benchmark/verification/tests/test_offline_repro.py -q
```

Offline reproduction path:

```bash
uv run python benchmark/governed_agent_bench/reproduce_offline.py \
  --output-dir /tmp/gab_offline_repro
```

## Dirty Worktree Note

The worktree contains modified and untracked files that predate this
inspection index and remain user-owned. Do not use plain `git diff` as
a clean view of Codex work. Inspect committed packets with `git show`
or compare the packet range explicitly.

Recommended committed-work views:

```bash
git log --oneline --reverse 2f0d95f^..HEAD
git diff --stat 2f0d95f^..HEAD
git diff --name-only 2f0d95f^..HEAD
```

## What Is Not Done

The project is not workshop-complete. These are intentionally blocked
until Dom judgement:

- `benchmark/governed_agent_bench/model_roster.md`;
- local model adapter and local model runs;
- cloud model adapter and any paid/cloud API run;
- claim-ladder upgrade from rule-baseline-only evidence;
- results/discussion text that interprets model performance;
- final audit and submission-ready package.

## Next Decision

Dom should choose one path:

1. **Predeclared model-roster path:** approve exact models, provider,
   local/cloud status, compute, budget, data boundary, decoding
   settings, and failure reporting. Codex can then create
   `model_roster.md` before any model-backed trajectory.
2. **Rule-baseline-only workshop path:** approve a narrower T0 paper
   based on the runtime substrate, benchmark, deterministic scorer,
   rule baseline, ablations, and reproducibility package.
