# GovernedAgentBench

GovernedAgentBench is the benchmark companion to *Deterministic
Software Contracts as Trusted Monitors in AI Control Protocols*. It
measures whether models can operate a governed runtime through its
public contract rather than relying on implicit prompt adherence,
private implementation knowledge, or free-form guessing.

The locked benchmark framing is contract-as-intervention with measured
model-scale substitution: the prompt is held constant, while the
runtime mode changes. Its load-bearing differentiation from
ST-WebAgentBench is runtime-mode intervention with mechanism-isolable
ablation under a held-constant prompt.

The benchmark is domain-general in framing. HAI is the first reference
runtime, and personal wellness is the first reference domain. The
benchmark explicitly treats clinical-boundary obedience as part of the
contract: reference-runtime tasks must not require diagnosis,
treatment, prescribing, or autonomous medical decisions.

The project-wide benchmark/evaluation strategy lives at
[`../../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`](../../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md).
The project-wide frame and decision log live at
[`../../project/FRAME.md`](../../project/FRAME.md) and
[`../../project/DECISIONS.md`](../../project/DECISIONS.md).

## Current Scope

This directory is the benchmark implementation space. The current
milestone is measurement-readiness: keep the offline scorer, harness,
synthetic fixtures, rule baseline, and report-generation path coherent
before Dom approves any model-backed run.

The implementation schedule is tracked in
[`../../research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md`](../../research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md).
The operational benchmark specs are:
[`BENCHMARK_SPEC.md`](BENCHMARK_SPEC.md),
[`OPERATOR_HARNESS_SPEC.md`](OPERATOR_HARNESS_SPEC.md),
[`SCORING_SPEC.md`](SCORING_SPEC.md), and
[`TASK_AUTHORING_GUIDE.md`](TASK_AUTHORING_GUIDE.md).

## Current State

As of 2026-05-10, this directory has the first measurement-readiness
substrate in place:

| Surface | Current state |
|---|---|
| Frozen manifests | 2 committed snapshots: current HAI v0.2.0 manifest snapshot at `benchmark/governed_agent_bench/manifests/hai_0_2_0.json` (≈ 189 KB, `agent_cli_contract.v2`) and stale drift snapshot `manifests/agent_cli_contract_v1_drift.json`. |
| Fixtures | Fixture plan plus six committed synthetic builders: `empty_user`, `ready_user_minimal`, `read_surface_user`, `governance_user`, `drift_user`, and `adversarial_user`. |
| Pilot tasks | 10 committed tasks: 2 each across L1, L2, L5, L6, and L7. |
| Recorded trajectories | 14 committed hand-authored seed trajectories: one passing and one failing trajectory for each of seven representative tasks, including L5 audit-reference and L7 drift exhibits. |
| Scorer | MVP deterministic offline scorer implemented under `scorer/core.py`, with schema/determinism and known-good/known-bad tests. |
| Harness | Model-agnostic harness implemented under `harness/`; supports structured operator actions, prompt rendering, runtime modes, hermetic subprocess execution, observation capture, and `mechanism_disabled` capture. |
| Baselines | Deterministic no-model `rule_baseline_v1` plus offline rule-baseline ablation runner. No local, cloud, or fine-tuned model baseline has been run. |
| Results | Evidence-table, SVG-figure, and error-taxonomy generators under `results/`; offline reproducibility command writes all derived artifacts. |
| Docs | Operator view, scaffold view, benchmark card, and offline reproducibility guide committed. |

This state is not a model-result claim. It records that offline
measurement scaffolding now exists, with known-good and known-bad
trajectories for deterministic scorer validation.

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
| `fixtures/` | Synthetic HAI fixture-state plans and later fixture builders. |
| `prompts/` | Held-constant deployment-realistic prompt template(s). |
| `trajectories/` | Hand-authored seed trajectories for scorer validation. |
| `harness/` | Model-agnostic action execution and trajectory capture. |
| `scorer/` | Offline scoring code and rubric helpers. |
| `baselines/` | Rule, local-model, cloud-model, and fine-tuned operator baselines. |
| `results/` | Evidence-table, figure, and error-taxonomy generation utilities. |
| `reports/` | Pilot and experiment reports. |
| `BENCHMARK_CARD.md` | Intended use, non-use, provenance, model-condition status, and limitations. |
| `BENCHMARK_SPEC.md` | Benchmark object, task levels, trajectory/score anatomy, and benchmark-card requirements. |
| `OPERATOR_HARNESS_SPEC.md` | Model-agnostic harness contract for non-Claude model evaluation. |
| `OPERATORS_VIEW.md` | What an operator sees through the harness. |
| `SCAFFOLD_VIEW.md` | What an experimenter sees when varying runtime modes. |
| `REPRODUCIBILITY.md` | Offline reproducibility command and artifacts. |
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
- Every ablatable runtime mechanism M4..M8 is load-bearing in at least
  one MVP task.
- The no-model rule baseline can regenerate trajectories, scores,
  evidence tables, figures, and an error taxonomy offline.

## Current Gate

`WP-MODEL-ROSTER-001` is the active Dom judgement gate. No
`model_roster.md` is committed, and no model-backed trajectory should be
produced until Dom approves a roster path or explicitly chooses a
rule-baseline-only workshop path.
