# Project Decisions

**Status:** Canonical post-reframe decision log, 2026-05-08.

This file records project-level decisions made during the runtime-contract
reframe. It is the place to recover decisions that otherwise lived only in
conversation. It overrides historical HAI product plans when they conflict,
but it does not replace runtime-specific invariants in `AGENTS.md` or the
HAI operator docs under `docs/hai/`.

## Decision Index

| ID | Decision | Current effect |
|---|---|---|
| D-PROJ-001 | The repo is a runtime-contract research repo, not a HAI product repo. | Root docs lead with the paper, GovernedAgentBench, and the runtime contract. |
| D-PROJ-002 | The north star is governed local operation over sensitive user-owned data. | Health is a demonstrator, not the paper's topic. |
| D-PROJ-003 | HAI remains active as the first reference runtime. | Runtime work continues only when it supports the paper, benchmark, HAI paper-readiness, or maintenance. |
| D-PROJ-004 | GovernedAgentBench is the benchmark name and artifact. | Do not revive HACO-Bench naming without a new maintainer decision. |
| D-PROJ-005 | The paper title leads with the claim, not the benchmark. | Use "Runtime Contracts for Local Agents Over Sensitive User-Owned Data" as the working title package. |
| D-PROJ-006 | The paper is conservative and measurement-first. | Claims are conditional on benchmark results; null results narrow the claim. |
| D-PROJ-007 | The health boundary is part of the contract. | No diagnosis, treatment, prescribing, autonomous medical decisions, or private health rows in public fixtures. |
| D-PROJ-008 | Experiments include local, cloud, fine-tuned, rule, and scaffold-ablation conditions. | Avoid optimizing only for local-vs-cloud rhetoric. |
| D-PROJ-009 | The minimum benchmark path does not require all six HAI domains. | Prioritize task families that test the contract honestly; domain breadth is support evidence. |
| D-PROJ-010 | Documentation alignment is the current work gate. | If a cold agent would recover the old objective, fix docs before new implementation. |
| D-PROJ-011 | Current docs and historical provenance must stay separated. | Active docs live at root, `research/`, `benchmarks/`, and `docs/hai/`; `reporting/` is proof/history. |

## Open Project Decisions

These are intentionally not locked yet:

| ID | Question | Default until decided |
|---|---|---|
| OD-PROJ-001 | Which workshop or preprint venue is the target for the first public paper package? | Keep docs venue-neutral: "workshop / preprint push" means a public preprint plus GovernedAgentBench release candidate, with venue selected once results and CFPs are known. |
| OD-PROJ-002 | When does the HAI support lane resume v0.3+ work such as MCP and N-of-1 surfaces? | Defer unless the work is paper-critical, benchmark-critical, or explicitly reopened by the maintainer after the research push. |
| OD-PROJ-003 | Should the title keep "Model-Scale Study" before Tier 3 evidence exists? | Treat it as a working subtitle only. The final public title must match the achieved claim tier. |

## D-PROJ-001: Research Repo, Not HAI Product Repo

**Decision.** This repository is no longer best understood as "the HAI
product repo." It is a research-engineering repo studying runtime
contracts for bounded agents.

**Rationale.** The career and application leverage comes from a paper,
benchmark, and reproducible systems/evals artifact. HAI alone is strong
engineering, but the new objective is to extract the research artifact
from it.

**Implications.**

- The root `README.md` is research-facing.
- HAI operator documentation lives under `docs/hai/`.
- HAI v1 polish is subordinate unless it directly supports the paper,
  GovernedAgentBench, HAI paper-readiness, or reproducible baselines.

## D-PROJ-002: North Star

**Decision.** The north star is:

> Runtime contracts can make smaller local models viable operators for
> bounded workflows over sensitive user-owned data by moving authority,
> validation, and audit from the model into enforceable local software.

**Rationale.** This is broader than personal health and maps to
research-engineering work on agent safety, evals, and runtime governance.

**Implications.**

- Personal wellness is the first sensitive-data reference domain.
- The paper should generalize to bounded operation over structured
  user-owned data.
- The model proposes, routes, clarifies, and explains; the runtime owns
  truth, validation, mutation, policy, and audit.

## D-PROJ-003: HAI As Reference Runtime

**Decision.** HAI continues as active software, but its project role is
reference runtime and demonstrator.

**Rationale.** The runtime makes the paper testable. It also gives
reviewers a real system rather than a purely notional benchmark.

**Implications.**

- Keep HAI maintenance that protects the contract, tests, install path,
  privacy posture, and benchmark reproducibility.
- Defer new user-product breadth unless it is paper-critical.
- Do not delete historical HAI plans; classify them as provenance or
  support-lane backlog.

## D-PROJ-004: GovernedAgentBench

**Decision.** The benchmark is named GovernedAgentBench.

**Rationale.** The name leads with governed operation rather than health,
which keeps the benchmark aligned with the research claim.

**Implications.**

- Use `benchmarks/governed_agent_bench/` as the benchmark root.
- Use GovernedAgentBench in the paper, roadmap, eval strategy, and
  reports.
- Do not reopen HACO-Bench naming without an explicit maintainer
  decision.

## D-PROJ-005: Title Leads With Claim

**Decision.** The working paper title package is:

**Runtime Contracts for Local Agents Over Sensitive User-Owned Data**

**Subtitle:** A Personal-Wellness Reference Runtime, GovernedAgentBench,
and Model-Scale Study

**Rationale.** The benchmark matters, but the paper should lead with the
research claim and architecture. GovernedAgentBench is the evaluation
artifact supporting that claim.

**Current caveat.** "Model-Scale Study" is a working subtitle, not a
promise of a Tier 3 result. The final public title must match the
achieved evidence tier.

## D-PROJ-006: Conservative Measurement Posture

**Decision.** The paper should be conservative and measurement-first.

**Rationale.** The aim is not to assert that runtime contracts prove a
grand thesis. The aim is to measure whether the contract improves bounded
operation, reduces unsafe behavior, and shifts the model-size threshold
under fixed metrics.

**Implications.**

- Prefer "we test whether..." over "we show..." until results exist.
- Predefine metrics and thresholds before interpreting outcomes.
- Report weak or null results honestly and narrow the claim.
- Do not rely on product anecdotes as the primary evidence.

## D-PROJ-007: Non-Clinical Health Boundary

**Decision.** The health boundary is part of the evaluated contract.

**Rationale.** The reference runtime touches wellness data. The research
claim must not depend on diagnosis, treatment, prescribing, or autonomous
medical decisions.

**Implications.**

- Public fixtures and fine-tuning data must not include private health
  rows.
- Benchmark tasks must not require clinical interpretation.
- Clinical-boundary obedience is a scored behavior, not a footnote.

## D-PROJ-008: Experimental Scope

**Decision.** The empirical program includes:

- rule baselines;
- local prompt-only models;
- local models with manifest / contract access;
- cloud prompt-only models;
- cloud models with manifest / contract access;
- fine-tuned local operators;
- fine-tuned local operators with live manifest access;
- scaffold ablations.

**Rationale.** The motivation is bounded operation over sensitive data.
Local models sharpen the privacy, cost, and deployment story, but the
benchmark must separate model capability from runtime governance.

## D-PROJ-009: Domain Scope For MVP

**Decision.** The minimum benchmark and paper path does not require all
six HAI domains.

**Rationale.** The empirical claim is about contract-governed operation,
not wellness-domain coverage. A smaller domain set can be sufficient if
the task families test command validity, schema validity, mutation
boundaries, refusal, evidence faithfulness, recovery, and drift.

**Implications.**

- Do not add domains or data sources before submission merely to make HAI
  feel more product-complete.
- Use six-domain breadth as demonstrator evidence when it is cheap and
  already present.
- Prioritize benchmark task families over domain count.

## D-PROJ-010: Documentation Alignment Gate

**Decision.** Internal documentation alignment is the current gate before
substantial new implementation.

**Rationale.** The project was reframed heavily. If a fresh session
recovers the old objective, future work will optimize the wrong target.

**Exit condition.** A cold agent can answer from repo docs alone:

- What is the research claim?
- What is the runtime contract?
- What does GovernedAgentBench measure?
- Why is HAI still active?
- Which docs are current versus historical?
- What is out of scope before submission?
- What empirical systems are compared?
- What health boundary is non-negotiable?

## D-PROJ-011: Documentation Architecture

**Decision.** The repo separates current docs from historical provenance.

**Current roots.**

- Root control docs: project frame, decisions, operating model, roadmap,
  hypotheses, architecture, contribution rules.
- `research/runtime_contracts_paper/`: paper and eval strategy.
- `benchmarks/governed_agent_bench/`: benchmark artifact.
- `docs/hai/`: HAI reference-runtime documentation.
- `reporting/`: release proof, historical plans, archives, and frozen
  prototypes.

**Implications.**

- Do not add new current HAI docs under `reporting/docs/`.
- Do not rewrite historical cycle records to pretend they had the new
  frame.
- Fix indexes and active control docs when old plans might be mistaken
  for current priority.
