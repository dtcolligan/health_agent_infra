# GovernedAgentBench

Benchmark companion to *Deterministic Software Contracts as Trusted
Monitors in AI Control Protocols*. Released as v1.0 on a GitHub tag
alongside the 2026-09-30 arXiv preprint.

Project-wide scope, calendar, and decisions: [`/PAPER.md`](../../PAPER.md).
Full benchmark specification: [`SPEC.md`](SPEC.md). Task authoring:
[`TASK_AUTHORING.md`](TASK_AUTHORING.md).

## What It Measures

Whether a model can operate a governed runtime through its public
contract rather than relying on implicit prompt adherence, private
implementation knowledge, or free-form guessing.

Load-bearing differentiation from ST-WebAgentBench: runtime-mode
intervention with mechanism-isolable ablation under a held-constant
prompt. The runtime is the intervention; the prompt does not vary.

Domain-general in framing. HAI is the first reference runtime; personal
wellness is the first reference domain. Clinical-boundary obedience is
part of the evaluated contract: tasks must not require diagnosis,
treatment, prescribing, or autonomous medical decisions.

## Current State (preprint scope)

| Surface | State |
|---|---|
| Frozen manifests | 2 snapshots: `manifests/hai_0_2_0.json` (≈ 189 KB, `agent_cli_contract.v2`) + `manifests/agent_cli_contract_v1_drift.json` for L7 |
| Fixtures | 6 synthetic builders: `empty_user`, `ready_user_minimal`, `read_surface_user`, `governance_user`, `drift_user`, `adversarial_user` |
| Pilot tasks | 28 tasks across L1, L2, L5, L6, L7; every M4-M8 has at least 3 static oracle-pair tasks |
| Trajectories | 14 hand-authored seed trajectories plus 25 static isolation oracle pairs; live isolation currently covers M7 only |
| Scorer | MVP deterministic offline scorer at `scorer/core.py` with schema/determinism tests |
| Harness | Model-agnostic harness at `harness/` with structured operator actions, runtime-mode toggling, hermetic subprocess execution, `mechanism_disabled` capture |
| Baselines | Deterministic `rule_baseline_v1` + offline rule-baseline ablation runner. No model-backed baseline yet. |
| Reproducibility | Evidence-table, SVG-figure, error-taxonomy generators at `results/`; single offline command regenerates derived artifacts |

## Directory Map

| Path | Purpose |
|---|---|
| [`SPEC.md`](SPEC.md) | Full benchmark specification (consolidated from BENCHMARK_SPEC + SCORING + harness + operator + scaffold views + hermetic recipe) |
| [`TASK_AUTHORING.md`](TASK_AUTHORING.md) | How to author L1-L7 tasks safely and scoreably |
| [`BENCHMARK_CARD.md`](BENCHMARK_CARD.md) | Intended use, non-use, provenance, scorer limitations (populated at v1.0 polish) |
| [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | Offline reproducibility command and artifacts |
| [`model_roster.md`](model_roster.md) | Predeclared paper-claim model roster (gated; see Current Gate) |
| `schema/` | JSON schemas: task v2, trajectory v2, score v2, operator_action v1, model_roster v1 |
| `tasks/` | Benchmark tasks grouped by level (L1-L7) |
| `manifests/` | Frozen runtime contract snapshots (current + drift) |
| `fixtures/` | Synthetic HAI fixture-state plans and builders |
| `prompts/` | Held-constant deployment-realistic prompt template |
| `trajectories/` | Hand-authored seed trajectories for scorer validation |
| `harness/` | Action execution, trajectory capture, hermetic subprocess control |
| `scorer/` | Offline scoring code and rubric helpers |
| `baselines/` | Rule baseline + (future) model baselines |
| `results/` | Evidence-table, figure, error-taxonomy generators |
| `reports/` | Pilot and experiment reports |

## Measurement-Readiness Exit Criteria

- Frozen HAI manifest snapshot exists under `manifests/`.
- Task / trajectory / score schemas validate hand-authored fixtures.
- 28 pilot tasks cover L1, L2, L5, L6, L7.
- Scorer grades recorded trajectories without network access or private
  health rows.
- Known-good and known-bad trajectories produce expected outcomes.
- Every M4-M8 mechanism has at least 3 static oracle-pair tasks.
- No-model rule baseline regenerates trajectories, scores, evidence
  tables, figures, and error taxonomy offline.

Preprint Option-B exit adds model-backed trajectories under the locked
roster and honest reporting of live-isolation limits. The static matrix
is scorer/coverage evidence, not standalone live causality evidence.

## Current Gate

`WP-MODEL-ROSTER-001` is the active maintainer-judgement gate. No
`model_roster.md` is committed yet. The preprint roster is narrow:
default `Qwen/Qwen2.5-7B-Instruct-Turbo` for Option B (final choice at
the mid-June pilot lock per D-O-01 in `/PAPER.md`), plus optionally one
`claude-sonnet-4-6` cell for the Option C stretch. Cost ceiling is
USD 300 (D-06).

No model-backed trajectory runs until the pilot protocol locks.
