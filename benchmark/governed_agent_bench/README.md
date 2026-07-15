# GovernedAgentBench

Benchmark companion to *Told or Enforced: When In-Context Contracts
Substitute for Runtime Enforcement in Agent Harnesses*.
Released as v1.0 on a GitHub tag alongside the 2026-09-30 arXiv preprint.

GovernedAgentBench crosses two levers per mechanism: whether a
constraint is specified in the in-context contract (told vs untold) and
whether the runtime enforces it (on vs off), measuring how much
constraint-respecting behavior comes from being told versus being
enforced. `PAPER.md` D-31/D-32/D-34 is authoritative for the design.

Project-wide scope, calendar, and decisions: [`/PAPER.md`](../../PAPER.md).
Full benchmark specification: [`SPEC.md`](SPEC.md). Task authoring:
[`TASK_AUTHORING.md`](TASK_AUTHORING.md).

## What It Measures

The benchmark measures mechanism-level effects of a deterministic
runtime contract around an agent across a per-mechanism 2x2. Two levers
are crossed: the runtime-enforcement axis (`runtime_mode`) and the
in-context specification axis (task field `contract_arm`, told|untold).
Scored task outcomes and contract violations are the responses.

Secondary use: the told-not-enforced cell (told, runtime off) doubles as a
disposition eval for agentic post-training, measuring the self-enforcement a
model supplies once told, separate from runtime enforcement (measure, not
train).

The enforcement axis compares `full_contract` against single-mechanism
disable modes:

| Mechanism | Full-contract behavior | Disable mode |
|---|---|---|
| M4 validation | Reject malformed commands and proposal payloads | `no_validation` |
| M5 `agent_safe` | Refuse agent-context dispatch of unsafe commands | `no_agent_safe` |
| M6 proposal gate | Require explicit user commit for gated state changes | `no_proposal_gate` |
| M7 refusal | Refuse clinical-boundary and forbidden requests | `no_refusal` |
| M8 audit evidence | Emit audit evidence for scored narration and traceability | `no_audit_chain` |

`no_runtime_enforcement` turns M4-M8 off together and is used as a
sanity floor, not as per-mechanism attribution evidence;
`gab_l6_agentsafe_untold` carries it as the all-off cell.

The specification axis withholds, in the `untold` arm, the manifest
facts that specify a task's load-bearing mechanism (M4 exit codes, M5
`agent_safe` flags, M6 mutation classes, M7 refusal taxonomy) and, for
M5/M7, the parameterized boundary-prose blocks in
`prompts/deployment_full_v2.md`; the `told` rendering is byte-preserved.
A separate `hide_stdout` field withholds command stdout from the model's
observation (blind observation); `gab_l5_audit_blind` is the blind twin
of `gab_l5_audit_told`.

Load-bearing differentiation from ST-WebAgentBench: a per-mechanism
specify-vs-enforce 2x2 that isolates whether constraint-respecting
behavior comes from in-context specification or from runtime
enforcement. The deployment prose is held byte-constant except the
parameterized told/untold blocks.

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
| Deterministic offline scorer / rule baseline | Scorer sensitivity, declared task coverage, offline pipeline mechanics and reproducibility | Model-backed capability claims |
| Model-backed 2x2 | Behavior of the locked model condition through the harness across the specify-vs-enforce cells | Universal claims across models, prompts, or domains |

The static oracle-pair and live-isolation tiers were retired in the
D-37 rebuild; the adversarial arm is future work. Paper claims must
preserve these labels. A transcript that is not converted into
trajectory JSON and scored offline is not benchmark evidence.

## Current State (preprint scope)

| Surface | State |
|---|---|
| Frozen manifests | 2 snapshots: `manifests/hai_0_2_0.json` (≈ 189 KB, `agent_cli_contract.v2`) + `manifests/agent_cli_contract_v1_drift.json` for L7 |
| Fixtures | 7 synthetic builders: `empty_user`, `ready_user_minimal`, `read_surface_user`, `governance_user`, `audit_pending_user`, `drift_user`, `adversarial_user` |
| Tasks | 36 tasks across L1, L2, L5, L6, L7 (L1:2, L2:6, L5:8, L6:19, L7:1); three scenario pairs per mechanism (D-39), each a labelled cell of the per-mechanism told/untold x on/off 2x2 |
| Cells | 72 task-cells / 288 reps at n=4 (from `runtime_modes_in_scope` x `contract_arm`) |
| Trajectories | 8 hand-authored seed trajectories (pass/fail pairs) at `trajectories/hand_authored/` for scorer validation |
| Scorer | Deterministic offline scorer at `scorer/core.py` with schema/determinism tests |
| Harness | Model-agnostic harness at `harness/` with structured operator actions, runtime-mode toggling, hermetic subprocess execution, `mechanism_disabled` capture |
| Baselines | Deterministic `rule_baseline_v1` + offline rule-baseline ablation runner. No model-backed baseline yet. |
| Reproducibility | Rule-baseline ablation -> evidence tables -> figures -> error taxonomy generators at `results/`; single offline command regenerates derived artifacts, fingerprinted by `REPRODUCIBILITY_GOLDEN.json` |

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
| `prompts/` | Deployment-realistic prompt base, held byte-constant except the parameterized told/untold blocks |
| `trajectories/` | Hand-authored seed trajectories for scorer validation |
| `harness/` | Action execution, trajectory capture, hermetic subprocess control |
| `scorer/` | Offline scoring code and rubric helpers |
| `baselines/` | Rule baseline + (future) model baselines |
| `results/` | Evidence-table, figure, error-taxonomy generators |
| `reports/` | Pilot and experiment reports |

## Measurement-Readiness Exit Criteria

- Frozen HAI manifest snapshot exists under `manifests/`.
- Task / trajectory / score schemas validate hand-authored fixtures.
- 36 tasks cover L1, L2, L5, L6, L7 as labelled 2x2 cells (three scenario pairs per mechanism, D-39).
- Scorer grades recorded trajectories without network access or private
  health rows.
- Known-good and known-bad trajectories produce expected outcomes.
- Every context-verifiable mechanism (M4-M7) carries a told/untold task
  pair; M8 audit and the L7 drift residual are covered.
- No-model rule baseline regenerates trajectories, scores, evidence
  tables, figures, and error taxonomy offline.

Preprint Option-B exit adds model-backed trajectories under the locked
roster across the specify-vs-enforce cells and preserves the
offline-scorer / model-backed evidence-tier labels.

## Current Gate

`WP-MODEL-ROSTER-001` is the active maintainer-judgement gate.
Per D-33 the working model is
`Qwen/Qwen3-235B-A22B-Instruct-2507-tput` (non-thinking MoE, Together
serverless), with `claude-sonnet-4-6` as the reliable fallback for
narration-heavy audit tests. `Qwen2.5-7B` (below the operate floor as
configured), `Qwen2.5-32B`, `Mistral-Small-24B`, `Gemma-3-27B`, and
`Gemma-4-31B` are excluded (see `/PAPER.md` Model Roster). Capability is a
bounded moderator, a small screened ladder above the operate floor, not a
scaling-law claim (D-34/D-36); the DR-9 7B→32B switch is retired. Cost
ceiling is USD 300 (D-06).

The machine-readable block in [`model_roster.md`](model_roster.md) still
carries the superseded `option_b_qwen25_7b_together` condition and must be
re-locked with vendor-verified Qwen3-235B provider fields before any
paper-claim run.

No model-backed trajectory runs until the pilot protocol locks.
