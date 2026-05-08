# GovernedAgentBench

GovernedAgentBench measures whether models can operate a governed
runtime through its public contract rather than relying on implicit
prompt adherence, private implementation knowledge, or free-form
guessing.

The benchmark is domain-general in framing. HAI is the first reference
runtime, and personal wellness is the first reference domain. The
benchmark explicitly treats clinical-boundary obedience as part of the
contract: reference-runtime tasks must not require diagnosis,
treatment, prescribing, or autonomous medical decisions.

The project-wide benchmark/evaluation strategy lives at
[`../../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`](../../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md).
The project-wide frame and decision log live at
[`../../PROJECT_FRAME.md`](../../PROJECT_FRAME.md) and
[`../../PROJECT_DECISIONS.md`](../../PROJECT_DECISIONS.md).

## Current Scope

This directory is the benchmark skeleton. The next milestone is
measurement-readiness: create a benchmark that can evaluate governed
agent operation and prove it can score known-good and known-bad
trajectories, so it can serve as the measurement instrument for
baselines, models, and ablations.

The implementation schedule is tracked in
[`../../research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md`](../../research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md).
The operational benchmark specs are:
[`BENCHMARK_SPEC.md`](BENCHMARK_SPEC.md),
[`OPERATOR_HARNESS_SPEC.md`](OPERATOR_HARNESS_SPEC.md),
[`SCORING_SPEC.md`](SCORING_SPEC.md), and
[`TASK_AUTHORING_GUIDE.md`](TASK_AUTHORING_GUIDE.md).

## Current State

As of 2026-05-08, this directory is intentionally a scaffold:

| Surface | Current state |
|---|---|
| Frozen manifests | 0 frozen manifests / 0 committed snapshots. First planned snapshot: `manifests/hai_0_2_0.json`. |
| Pilot tasks | 0 committed tasks. MVP target: at least 10 across L1, L2, L5, L6, and L7. |
| Recorded trajectories | 0 committed trajectories. |
| Scorer | README and schemas only; offline scoring code not yet implemented. |
| Baselines | README only; no rule, local-model, cloud-model, or fine-tuned baselines yet. |
| Reports | README only; no pilot report yet. |

This empty state is not a validity claim. It records that Planning Gate 1
currently precedes benchmark task authoring.

Task levels:

| Level | Focus |
|---|---|
| L1 | Intent-to-command routing |
| L2 | Setup and `USER_INPUT` recovery |
| L3 | Daily-loop orchestration |
| L4 | Schema-valid proposal generation |
| L5 | Faithful narration from runtime read surfaces |
| L6 | Governance preservation and adversarial refusal |
| L7 | Contract drift adaptation |

## Directory Map

| Path | Purpose |
|---|---|
| `schema/` | JSON schemas for tasks, trajectories, and scores. |
| `tasks/` | Benchmark tasks grouped by level. |
| `manifests/` | Frozen runtime contract snapshots used by benchmark tasks. |
| `scorer/` | Offline scoring code and rubric helpers. |
| `baselines/` | Rule, local-model, cloud-model, and fine-tuned operator baselines. |
| `reports/` | Pilot and experiment reports. |
| `BENCHMARK_SPEC.md` | Benchmark object, task levels, trajectory/score anatomy, and benchmark-card requirements. |
| `OPERATOR_HARNESS_SPEC.md` | Model-agnostic harness contract for non-Claude model evaluation. |
| `SCORING_SPEC.md` | Deterministic scoring metrics, violation taxonomy, pass logic, and thresholds. |
| `TASK_AUTHORING_GUIDE.md` | How to author L1-L7 tasks safely and scoreably. |

## Measurement-Readiness Exit Criteria

- A frozen HAI manifest snapshot exists under `manifests/`.
- `schema/task.schema.json`, `schema/trajectory.schema.json`, and
  `schema/score.schema.json` validate hand-authored fixtures.
- At least 10 pilot tasks cover L1, L2, L5, L6, and L7.
- The scorer can grade recorded trajectories without network access or
  private health rows.
- Known-good and known-bad trajectories produce expected pass/fail
  outcomes.
