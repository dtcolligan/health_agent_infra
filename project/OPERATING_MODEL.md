# Project Operating Model

**Status:** Canonical internal operating model, aligned to framing v2 on
2026-05-11.

This document exists because the project was heavily reframed. A future
agent should not need conversation memory to understand what the repo is
now optimizing for.

Project-level decisions are recorded in [`DECISIONS.md`](DECISIONS.md);
the current framing-v2 imports are D-PROJ-018 through D-PROJ-023.

## Current Objective

Engineer this repository around the merged NeurIPS 2027
main-conference paper:

**Deterministic Software Contracts as Trusted Monitors in AI Control
Protocols**

The research package has four active surfaces:

1. the merged paper and locked framing;
2. GovernedAgentBench as the measurement instrument;
3. HAI as the personal-wellness reference runtime;
4. reproducible baselines, mechanism ablations, Engels, and bounded
   LLM-monitor contrast runs.

HAI v1 product polish is subordinate unless it directly supports the
paper, benchmark, or reproducibility.

## Documentation-Alignment Gate

**Gate status on 2026-05-11: PARTIALLY MET.**

Phase 1 framing is closed. `framing_v2/CONVERGED.md` is the cold-start
authority for the paper frame and imports D-FRAME-001 through
D-FRAME-027.

Phase 2 documentation alignment is in progress:

| Batch | State |
|---|---|
| Batch 1, paper-planning files | Closed clean |
| Batch 2, benchmark spec + schemas | Closed clean |
| Batch 3, project cold-start files | In progress |
| Batch 4, HAI runtime docs | Pending |
| Batch 5, operating contracts | Pending |
| Batch 6, historical provenance | Pending |
| Audit-findings-closure batch | Pending |
| Final repo-wide audit | Pending |

The gate closes only after the remaining batches and final repo-wide
audit verify that cold-start docs, benchmark specs, HAI docs, and
operating contracts agree on the merged-paper story.

## Artifact Hierarchy

| Rank | Artifact | Why it exists | Primary docs |
|---|---|---|---|
| 1 | Locked framing | Defines the current title, target venue, threat model, mechanisms, model roster, thresholds, and scope. | `../research/runtime_contracts_paper/framing_v2/CONVERGED.md`, `../research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md` |
| 2 | Paper outline and planning files | Turn the locked framing into paper sections, claims, work packets, and execution plans. | `../research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md`, `../research/runtime_contracts_paper/PAPER_FRAME.md`, `../research/runtime_contracts_paper/CLAIM_LADDER.md`, `../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md` |
| 3 | GovernedAgentBench | Makes the runtime-mode intervention measurable and inspectable by others. | `../benchmark/governed_agent_bench/README.md`, `../benchmark/governed_agent_bench/BENCHMARK_SPEC.md`, `../benchmark/governed_agent_bench/SCORING_SPEC.md` |
| 4 | Runtime contract | The intervention being evaluated. | `FRAME.md`, `../hai/docs/runtime_contract_overview.md`, `../hai/docs/agent_cli_contract.md` |
| 5 | HAI | Reference runtime and concrete demonstrator. | `../hai/docs/hai_reference_runtime.md`, `../hai/docs/current_system_state.md` |
| 6 | HAI product polish | Useful backlog only when it supports the research artifact. | `../hai/reporting/plans/` |

Older paper drafts, pre-merge `PAPER_FRAME` bodies, and HAI release
plans are historical provenance when they disagree with the hierarchy
above.

## Research Posture

The paper should read like research engineering, not product marketing.

- Lead with the architecture and measurement problem.
- State claims conditionally until results exist.
- Prefer fixed thresholds, predeclared rosters, and committed scorer
  hashes over broad claims.
- Treat health as a sensitive-data reference domain, not a clinical
  topic.
- Report failures and null results cleanly.
- Avoid claiming that governance, auditability, or local-first posture
  is a consumer market by itself.

The intended reader is a research-engineering reviewer evaluating
whether the repo contains a real system, a reproducible benchmark, fair
baselines, and a defensible empirical claim.

## Evaluation Scope

The empirical program varies `runtime_mode` over the canonical
seven-mode enum and varies `model_class` over `rule_baseline`, `local`,
`cloud`, and future-work `fine_tuned_local`. The
deployment-realistic prompt is held constant in every condition. Model
entries for paper-claim cells come from the predeclared roster and the
USD 1,500 model-API cost ceiling.

The seven runtime modes that drive mechanism ablations are:

- `full_contract` (M4-M8 plus M9-TX on);
- `no_validation` (M4 off);
- `no_agent_safe` (M5 off);
- `no_proposal_gate` (M6 off);
- `no_refusal` (M7 off);
- `no_audit_chain` (M8 off; M9-TX remains on);
- `no_runtime_enforcement` (M4-M8 off; M1-M3 and M9-TX remain on).

The main measurement question is whether deterministic contracts improve
safety-constrained task success and shift the model-scale safety curve
under the predeclared roster and thresholds.

## Threat Model And Mechanisms

The locked threat model is capability failure plus a targeted
adversarial layer: 50 trajectories spanning refusal bypass, mutation
escalation, audit tampering, schema evasion, and adaptive attacks
against DRG-0.

The mechanism inventory is:

- M4 validation;
- M5 `agent_safe` dispatch refusal;
- M6 W57 proposal/commit gate;
- M7 clinical-boundary refusal, JSON output exempt;
- M8 audit evidence emission;
- M9-TX transaction integrity, held constant.

This is a bounded trusted-monitor substrate, not a full control safety
case for scheming or sandbagged frontier models.

## Documentation Architecture

The repo architecture is owner-based, not support-function-based.
Verification and reporting live under the artifact they support.

| Layer | Purpose |
|---|---|
| root | Tooling, entrypoints, and repository metadata only: `README.md`, `AGENTS.md`, `CLAUDE.md`, `pyproject.toml`, `uv.lock`, `CHANGELOG.md`, citation/license/security/contribution files, and CI metadata. |
| `project/` | Project memory: frame, decisions, operating model, roadmap, hypotheses, repo map, and project-level doc-alignment tests. |
| `hai/` | HAI reference runtime: implementation, HAI docs, HAI verification/evals, HAI assets, release proof, support-lane backlog, and historical HAI provenance. |
| `benchmark/` | GovernedAgentBench: benchmark specs, schemas, tasks, manifests, scorer, baselines, reports, and benchmark-specific verification. |
| `research/` | Paper lane: locked framing, paper frame, draft, prior art, claim ladder, experiment design, and release-package planning. |

Historical docs should not be rewritten to pretend they always had the
new frame. Their headers and indexes should say what they are: useful
provenance, not current project-wide strategy.

## Decision Rules

When choosing between tasks:

1. If a doc still teaches the wrong project objective, fix the doc first.
2. If a HAI task is required for the paper, benchmark,
   HAI paper-readiness, or reproducible baselines, keep it.
3. If a HAI task is product polish only, defer it until after the paper
   and benchmark push.
4. If a benchmark task requires private health rows, redesign the task.
5. If a paper claim requires clinical interpretation, remove or reframe it.
6. If a result is weak or null, preserve it and narrow the claim.

## What "Aligned" Means

A cold agent is aligned when it can answer these questions from repo docs
alone:

- What is the merged paper title and venue?
- Which framing-v2 decisions are locked?
- Why is HAI still in the repo?
- What does GovernedAgentBench measure?
- Which docs are current and which are historical?
- What runtime contract components are being evaluated?
- What model roster and runtime modes are in scope?
- What threat model is in scope?
- What safety boundaries are non-negotiable?
- Why is HAI v1 polish not the default next task?

If future edits make those answers unclear, documentation alignment
becomes the first priority again.
