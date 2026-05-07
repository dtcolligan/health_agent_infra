# Project Operating Model

**Status:** Canonical internal operating model, 2026-05-07.

This document exists because the project was heavily reframed. A future
agent should not need conversation memory to understand what the repo is
now optimizing for.

## Current Objective

Engineer this repository into a research project around runtime contracts
for local agents over sensitive user-owned data.

The near-term external artifact is not a polished HAI v1 product. It is a
research-engineering package:

1. a conservative paper;
2. GovernedAgentBench;
3. a documented runtime contract;
4. HAI as the reference implementation;
5. reproducible local/cloud/fine-tuned/ablation experiments.

## Current Work Gate

Before implementation work resumes, internal documentation should be good
enough that a cold agent can recover the new objective without chat
history.

This gate is not complete just because the root README is short. It is
complete when the control docs agree on:

- HAI is the reference runtime, not the whole project.
- Personal wellness is the demonstrator domain, not the paper topic.
- GovernedAgentBench is the benchmark artifact.
- The paper is conservative and measurement-first.
- Health safety is non-clinical by contract: no diagnosis, treatment,
  prescribing, or autonomous medical decisions.
- HAI v1 polish is subordinate unless paper-critical.
- Historical HAI plans are provenance, not current priority.

## Artifact Hierarchy

| Rank | Artifact | Why it exists | Primary docs |
|---|---|---|---|
| 1 | Paper frame | Defines the research claim and external audience. | `research/runtime_contracts_paper/PAPER_FRAME.md`, `research/runtime_contracts_paper/DRAFT_PAPER.md` |
| 2 | GovernedAgentBench | Makes the claim measurable and inspectable by others. | `benchmarks/governed_agent_bench/README.md`, `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md` |
| 3 | Runtime contract | The intervention being evaluated. | `PROJECT_FRAME.md`, `ARCHITECTURE.md`, `reporting/docs/agent_cli_contract.md` |
| 4 | HAI | Reference runtime and concrete demonstrator. | `reporting/docs/hai_reference_runtime.md`, `reporting/docs/current_system_state.md` |
| 5 | HAI v1 polish | Useful backlog only when it supports the research artifact. | `reporting/plans/` |

## Research Posture

The paper should read like research engineering, not product marketing.

- Lead with the architecture and measurement problem.
- State claims conditionally: "we test whether..." and "if supported by
  results...".
- Prefer fixed thresholds and pre-registered metrics over broad claims.
- Treat health as a sensitive-data reference domain, not a clinical topic.
- Report failures and null results cleanly.
- Avoid claiming that governance, auditability, or local-first posture is
  a consumer market by itself.

The intended reader is a research-engineering reviewer: someone evaluating
whether the repo contains a real system, a reproducible benchmark, fair
baselines, and a defensible empirical claim.

## Evaluation Scope

The empirical program should compare:

- local prompt-only models;
- local models with the live/frozen runtime contract;
- cloud prompt-only models;
- cloud models with the runtime contract;
- fine-tuned local operators;
- rule baselines;
- scaffold ablations.

Scaffold ablations should remove individual contract components, such as:

- no manifest;
- stale manifest;
- no `agent_safe`;
- no mutation classes;
- no exit-code semantics;
- no output schemas;
- no proposal gate;
- no audit/evidence references.

The main measurement question is whether contract-governed operation
improves safety-constrained task success and shifts the model-size
threshold for reliable bounded operation.

## Documentation Architecture

The repo should have a clear separation of concerns:

| Layer | Purpose |
|---|---|
| `README.md` | Public research-facing repo overview. |
| `PROJECT_FRAME.md` | Short canonical frame and priority order. |
| `PROJECT_OPERATING_MODEL.md` | Internal operating model and current work gate. |
| `HYPOTHESES.md` | Current research hypotheses, not old HAI product bets. |
| `ROADMAP.md` | Research-first roadmap. |
| `research/runtime_contracts_paper/` | Paper, evaluation strategy, implementation plan, and documentation audit. |
| `benchmarks/governed_agent_bench/` | Benchmark artifact. |
| `reporting/docs/hai_reference_runtime.md` | HAI operator/product manual. |
| `reporting/plans/` | HAI release history, support-lane backlog, and pre-reframe strategy provenance. |

Historical docs should not be rewritten to pretend they always had the
new frame. Instead, their headers and indexes should say what they are:
useful HAI provenance, not current project-wide strategy.

## Decision Rules

When choosing between tasks:

1. If a doc still teaches the wrong project objective, fix the doc first.
2. If a HAI task is required for the paper, benchmark, contract freeze, or
   reproducible baselines, keep it.
3. If a HAI task is product polish only, defer it until after the paper /
   benchmark push.
4. If a benchmark task requires private health rows, redesign the task.
5. If a paper claim requires clinical interpretation, remove or reframe it.
6. If a result is weak or null, preserve it and narrow the claim.

## What "Aligned" Means

A cold agent is aligned when it can answer these questions from repo docs
alone:

- What is the research claim?
- Why is HAI still in the repo?
- What is GovernedAgentBench supposed to measure?
- Which docs are current and which are historical?
- What runtime contract components are being evaluated?
- What model conditions are in scope?
- What safety boundaries are non-negotiable?
- Why is HAI v1 polish not the default next task?

Until those answers are obvious, documentation alignment remains the
current focus.
