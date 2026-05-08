# Project Operating Model

**Status:** Canonical internal operating model, 2026-05-08.

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
3. a paper-ready HAI runtime slice: manifest, command behavior,
   fixtures, stable outputs, and safety boundary;
4. HAI as the maintained reference implementation;
5. reproducible local/cloud/fine-tuned/ablation experiments.

## Current Work Gate

Before implementation work resumes, internal documentation and execution
planning should be good enough that a cold agent can recover the new
objective without chat history and then pick up a bounded work packet
without making strategic decisions.

This gate is not complete just because the root README is short. It is
complete when the control docs agree on:

- HAI is the reference runtime, not the whole project.
- Personal wellness is the demonstrator domain, not the paper topic.
- GovernedAgentBench is the benchmark artifact.
- `DECISIONS.md` records the project-level decisions that would
  otherwise depend on conversation memory.
- The paper is conservative and measurement-first.
- Health safety is non-clinical by contract: no diagnosis, treatment,
  prescribing, or autonomous medical decisions.
- HAI v1 polish is subordinate unless paper-critical.
- Historical HAI plans are provenance, not current priority.

## Artifact Hierarchy

| Rank | Artifact | Why it exists | Primary docs |
|---|---|---|---|
| 1 | Paper frame | Defines the research claim and external audience. | `../research/runtime_contracts_paper/PAPER_FRAME.md`, `../research/runtime_contracts_paper/DRAFT_PAPER.md` |
| 2 | GovernedAgentBench | Makes the claim measurable and inspectable by others. | `../benchmark/governed_agent_bench/README.md`, `../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md` |
| 3 | Runtime contract | The intervention being evaluated. | `FRAME.md`, `../hai/docs/runtime_contract_overview.md`, `../hai/docs/agent_cli_contract.md` |
| 4 | HAI | Reference runtime and concrete demonstrator. | `../hai/docs/hai_reference_runtime.md`, `../hai/docs/current_system_state.md` |
| 5 | HAI v1 polish | Useful backlog only when it supports the research artifact. | `../hai/reporting/plans/` |

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

The repo architecture is owner-based, not
support-function-based. Verification and reporting should live under the
artifact they support; they are not project-level artifacts by
themselves.

Physical shape:

| Layer | Purpose |
|---|---|
| root | Tooling, entrypoints, and repository metadata only: `README.md`, `AGENTS.md`, `CLAUDE.md`, `pyproject.toml`, `uv.lock`, `CHANGELOG.md`, citation/license/security/contribution files, and CI metadata. |
| `project/` | Project memory: frame, decisions, operating model, roadmap, hypotheses, repo map, and project-level doc-alignment tests. |
| `hai/` | HAI reference runtime: implementation, HAI docs, HAI verification/evals, HAI assets, release proof, support-lane backlog, and historical HAI provenance. |
| `benchmark/` | GovernedAgentBench: benchmark specs, schemas, tasks, manifests, scorer, baselines, reports, and benchmark-specific verification. |
| `research/` | Paper lane: paper frame, draft, prior art, claim ladder, experiment design, and release-package planning. |

Historical docs should not be rewritten to pretend they always had the
new frame. Instead, their headers and indexes should say what they are:
useful HAI provenance, not current project-wide strategy.

Do not move these owner lanes casually. A future structural change must
update packaging, pytest discovery, CI, imports, generated-doc paths, and
links together.

## Decision Rules

When choosing between tasks:

1. If a doc still teaches the wrong project objective, fix the doc first.
2. If a HAI task is required for the paper, benchmark,
   HAI paper-readiness, or reproducible baselines, keep it.
3. If a HAI task is product polish only, defer it until after the paper /
   benchmark push.
4. If a benchmark task requires private health rows, redesign the task.
5. If a paper claim requires clinical interpretation, remove or reframe it.
6. If a result is weak or null, preserve it and narrow the claim.

## What "Aligned" Means

A cold agent is aligned when it can answer these questions from repo docs
alone:

- What is the research claim?
- Which project-level decisions are locked?
- Why is HAI still in the repo?
- What is GovernedAgentBench supposed to measure?
- Which docs are current and which are historical?
- What runtime contract components are being evaluated?
- What model conditions are in scope?
- What safety boundaries are non-negotiable?
- Why is HAI v1 polish not the default next task?

Those answers are now encoded in the control docs and guarded by tests.
If future edits make them unclear, documentation alignment becomes the
first priority again.

## Planning Gate 1

After documentation alignment, the next gate is end-to-end
research-program planning. Implementation should resume only when the repo
contains:

- a master execution plan;
- claim ladder;
- prior-art positioning plan;
- HAI paper-readiness plan;
- benchmark specification;
- operator-harness specification;
- scoring specification;
- task-authoring guide;
- baseline and ablation plan;
- work packets with allowed files, dependencies, acceptance criteria,
  tests, and non-goals.

These live under `../research/runtime_contracts_paper/` and
`../benchmark/governed_agent_bench/`.

The documentation-alignment gate remains open until cold-start docs make
the owner model and current paths unambiguous.
