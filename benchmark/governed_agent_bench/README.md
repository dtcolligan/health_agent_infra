# GovernedAgentBench

Benchmark companion to *Told or Enforced: Separating the Contributions
of In-Context Contracts and Runtime Enforcement in Agent Harnesses*.
Released as v1.0 on a GitHub tag alongside the 2026-09-30 arXiv preprint.

GovernedAgentBench separates two levers per mechanism: whether a
constraint is specified in the in-context contract and whether the runtime
enforces it, measuring how much constraint-respecting behavior comes from
being told versus being enforced. (The detailed methodology sections below
are mid-sync to this 2x2 framing; `PAPER.md` D-31/D-32 is authoritative.)

Project-wide scope, calendar, and decisions: [`/PAPER.md`](../../PAPER.md).
Full benchmark specification: [`SPEC.md`](SPEC.md). Task authoring:
[`TASK_AUTHORING.md`](TASK_AUTHORING.md).

## What It Measures

The benchmark measures mechanism-level effects of a deterministic
runtime contract around an agent. Runtime mode is the treatment; scored
task outcomes and contract violations are the responses.

The primary comparison is `full_contract` against single-mechanism
disable modes:

| Mechanism | Full-contract behavior | Disable mode |
|---|---|---|
| M4 validation | Reject malformed commands and proposal payloads | `no_validation` |
| M5 `agent_safe` | Refuse agent-context dispatch of unsafe commands | `no_agent_safe` |
| M6 proposal gate | Require explicit user commit for gated state changes | `no_proposal_gate` |
| M7 refusal | Refuse clinical-boundary and forbidden requests | `no_refusal` |
| M8 audit evidence | Emit audit evidence for scored narration and traceability | `no_audit_chain` |

`no_runtime_enforcement` turns M4-M8 off together and is used as a
sanity floor, not as per-mechanism attribution evidence.

Load-bearing differentiation from ST-WebAgentBench: runtime-mode
intervention with mechanism-isolable ablation under a held-constant
prompt. The runtime is the intervention; the prompt does not vary.

The benchmark evaluates whether the model can operate through the
public contract rather than relying on implicit prompt adherence,
private implementation knowledge, or free-form guessing. It does not
score free-form coaching quality.

HAI is the reference runtime instantiation and personal wellness is the
reference domain. The benchmark is designed to admit other runtimes in
future work. Clinical-boundary obedience is part of the evaluated
contract: tasks must not require diagnosis, treatment, prescribing, or
autonomous medical decisions.

## Evidence Tiers

GovernedAgentBench separates evidence tiers by design:

| Tier | What it supports | What it does not support |
|---|---|---|
| Static oracle pairs | Scorer sensitivity, declared task coverage, marker-contamination checks | Live runtime causality |
| Live runtime probes | Targeted hermetic HAI behavior under M4-M8 disable paths | Model behavior on the 28-task suite |
| Rule baseline | Offline pipeline mechanics and deterministic reproducibility | Model-backed capability claims |
| Model-backed trajectories | Behavior of the locked model condition through the harness | Universal claims across models, prompts, or domains |

Paper claims must preserve these labels. A transcript that is not
converted into trajectory JSON and scored offline is not benchmark
evidence.

## Current State (preprint scope)

| Surface | State |
|---|---|
| Frozen manifests | 2 snapshots: `manifests/hai_0_2_0.json` (≈ 189 KB, `agent_cli_contract.v2`) + `manifests/agent_cli_contract_v1_drift.json` for L7 |
| Fixtures | 6 synthetic builders: `empty_user`, `ready_user_minimal`, `read_surface_user`, `governance_user`, `drift_user`, `adversarial_user` |
| Pilot tasks | 28 tasks across L1, L2, L5, L6, L7; every M4-M8 has at least 3 static oracle-pair tasks |
| Trajectories | 18 hand-authored seed trajectories plus 25 static isolation oracle pairs; targeted live isolation probes cover M4-M8 |
| Scorer | Deterministic offline scorer at `scorer/core.py` with schema/determinism tests |
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
- Targeted hermetic live probes cover every M4-M8 disable path.
- No-model rule baseline regenerates trajectories, scores, evidence
  tables, figures, and error taxonomy offline.

Preprint Option-B exit adds model-backed trajectories under the locked
roster and preserves evidence-tier labels. The static matrix is
scorer/coverage evidence, not standalone live causality evidence; the
live matrix is targeted runtime-probe evidence, not model-result
evidence.

## Current Gate

`WP-MODEL-ROSTER-001` is the active maintainer-judgement gate.
[`model_roster.md`](model_roster.md) is committed as a draft, aligned
to the narrow preprint roster in `/PAPER.md`: default
`Qwen/Qwen2.5-7B-Instruct-Turbo` for Option B (final choice at the
mid-June pilot lock per D-O-01), `Qwen/Qwen2.5-32B-Instruct` as the
fallback if 7B saturates, and optionally one `claude-sonnet-4-6` cell
for the Option C stretch. Cost ceiling is USD 300 (D-06).

Dom must freeze the roster before any paper-claim run. No model-backed trajectory runs until the pilot protocol locks.
