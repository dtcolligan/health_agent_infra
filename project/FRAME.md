# Project Frame

**Status:** Canonical project frame, aligned to framing v2 on
2026-05-11.

This repository is a runtime-contract research repo. HAI remains the
first reference runtime, but the active external artifact is the
merged paper plus GovernedAgentBench.

## Active Objective

The active objective is the NeurIPS 2027 main-conference paper:

**Deterministic Software Contracts as Trusted Monitors in AI Control
Protocols**

The headline frame is:

> A deterministic software contract operationalizes a safety spec as the
> trusted monitor in an AI control protocol for bounded agent operation.

The paper and benchmark come first. HAI is maintained as the
personal-wellness reference runtime when it stabilizes the contract,
unblocks GovernedAgentBench, or makes baseline runs reproducible.

## Lineage Anchor

The paper sits at the intersection of three literatures:

| Anchor | Role |
|---|---|
| AI control protocols, including Greenblatt et al. 2024 | Supplies the trusted-monitor / untrusted-operator vocabulary. |
| Safety specs, including OpenAI Model Spec, Anthropic Model Spec Midtraining, and Deliberative Alignment | Shows how safety behavior can be specified explicitly; this project tests executable software contracts as one implementation substrate. |
| LLM-monitor baselines, including Constitutional Classifiers and Hierarchical Summarization | Provides the direct contrast: model monitors are semantic and flexible; deterministic contracts are narrow, auditable, and mechanism-isolable. |

## Load-Bearing Claims

The paper is designed around three headline empirical claims:

1. **Mechanism-isolable ablations.** Holding the deployment prompt
   constant, toggling M4-M8 produces measurable per-mechanism
   contributions to safe bounded operation.
2. **Runtime-as-floor model-scale result.** Under the full contract,
   the smallest predeclared model passes all primary thresholds; under
   `no_runtime_enforcement`, a larger predeclared model fails at least
   one. The contract shifts the model-scale safety curve.
3. **Deterministic Guard on Engels Backdoor Code.** DRG-0 is added to
   the Engels et al. 2025 scaling-laws-for-oversight curve as a Guard
   with general Elo = 0, contingent on the July 2026 pilot gate.

The targeted adversarial layer is reported as a bounded
characterization result, not as a full control safety case.

## Threat Model

The locked threat model is capability failure plus a targeted
adversarial layer.

Capability failure covers fallible models that emit invalid commands,
hallucinated tool calls, malformed proposals, unsupported factual
claims, unsafe mutation attempts, missed refusals, or stale-manifest
behavior.

The targeted layer is 50 trajectories: refusal bypass, mutation
escalation, audit tampering, schema evasion, plus adaptive attacks
against DRG-0. It is not full attack-policy substitution and not a
claim about scheming or sandbagged frontier models.

## Mechanism Inventory

| ID | Mechanism | Ablation mode |
|---|---|---|
| M4 | Validation of typed commands and proposal payloads | `no_validation` |
| M5 | `agent_safe` dispatch refusal | `no_agent_safe` |
| M6 | W57 proposal/commit user gate | `no_proposal_gate` |
| M7 | Clinical-boundary refusal over proposal, recommendation, and text surfaces; JSON output exempt | `no_refusal` |
| M8 | Audit evidence emission | `no_audit_chain` |
| M9-TX | Transaction integrity | Held constant, non-ablatable |

M8 is evidence emission, not the whole audit chain. Atomic transaction
integrity remains M9-TX and is never ablated.

## Active Artifacts

| Artifact | Role | Canonical docs |
|---|---|---|
| Paper | Merged NeurIPS 2027 systems/evals paper. | `../research/runtime_contracts_paper/framing_v2/CONVERGED.md`, `../research/runtime_contracts_paper/PAPER_FRAME.md`, `../research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md` |
| GovernedAgentBench | Benchmark artifact for contract-governed agent operation and mechanism ablations. | `../benchmark/governed_agent_bench/README.md`, `../benchmark/governed_agent_bench/BENCHMARK_SPEC.md`, `../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md` |
| Runtime contract | The intervention: capabilities manifest, typed commands, mutation classes, `agent_safe`, schemas, proposal/commit separation, deterministic gates, policy, refusal, and audit evidence emission. | `FRAME.md`, `OPERATING_MODEL.md`, `../hai/docs/runtime_contract_overview.md` |
| HAI | Personal-wellness reference runtime, packaged as `health-agent-infra` and exposed through `hai`. | `../hai/docs/hai_reference_runtime.md`, `../hai/docs/`, `../hai/src/health_agent_infra/` |

## Priority Order

Default priority is:

1. Keep the merged-paper framing and Phase 2 documentation alignment
   coherent.
2. Make GovernedAgentBench measurement-ready for the locked
   `runtime_mode` intervention.
3. Stabilize HAI paper-readiness and the reference-runtime surfaces
   that support the paper, benchmark, manifests, fixtures, and
   reproducible baselines.
4. Run the predeclared experiments, including mechanism ablations,
   Engels, bounded Hierarchical Summarization contrast, and model-scale
   baselines.
5. Defer HAI product polish unless it is paper-critical.

## Health Boundary

HAI is a personal-wellness reference domain, not clinical software.

- No diagnosis.
- No treatment.
- No prescribing.
- No autonomous medical decisions.
- No private health rows in public benchmark fixtures or training data.

This boundary is part of the runtime contract being evaluated, not a
footer disclaimer.

## Paper Source-Of-Truth Order

Cold agents should resolve paper-framing questions in this order:

1. `../research/runtime_contracts_paper/framing_v2/CONVERGED.md`
2. `../research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`
3. `../research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md`
4. Batch-1 paper-planning files, especially
   `../research/runtime_contracts_paper/PAPER_FRAME.md`,
   `../research/runtime_contracts_paper/CLAIM_LADDER.md`, and
   `../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`
5. Batch-2 benchmark spec files under
   `../benchmark/governed_agent_bench/`

Older draft paper files and pre-merge planning docs are historical
provenance when they disagree with this ordering.

## Cold-Start Reading Rule

Cold agents should read in this order (matching AGENTS.md and CLAUDE.md
session-start ordering, which place the paper-framing source-of-truth
first):

1. `../research/runtime_contracts_paper/framing_v2/CONVERGED.md`
2. `../research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`
3. `project/FRAME.md` (this file)
4. `project/DECISIONS.md`
5. `project/OPERATING_MODEL.md`
6. `AGENTS.md`
7. `../research/runtime_contracts_paper/PAPER_FRAME.md`
8. `../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`
9. `../benchmark/governed_agent_bench/README.md`
10. `../benchmark/governed_agent_bench/BENCHMARK_SPEC.md` if the task
    touches benchmark design
11. `project/ROADMAP.md`
12. `../hai/docs/hai_reference_runtime.md` if the task touches HAI
13. `../hai/docs/current_system_state.md`

Historical release plans under `hai/reporting/plans/` explain how HAI
got here. They are not the default source of current project priority
when they disagree with this frame.
