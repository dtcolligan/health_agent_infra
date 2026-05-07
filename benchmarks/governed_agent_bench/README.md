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

## Current Scope

This directory is the benchmark skeleton. The next milestone is an MVP
that can score recorded trajectories without running model backends.

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

## MVP Exit Criteria

- A frozen HAI manifest snapshot exists under `manifests/`.
- `schema/task.schema.json`, `schema/trajectory.schema.json`, and
  `schema/score.schema.json` validate hand-authored fixtures.
- At least 10 pilot tasks cover L1, L2, L5, L6, and L7.
- The scorer can grade recorded trajectories without network access or
  private health rows.
