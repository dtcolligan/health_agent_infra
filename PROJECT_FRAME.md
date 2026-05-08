# Project Frame

**Status:** Canonical project frame, 2026-05-08.

This repository is no longer best understood as "the HAI product
repo." It is a runtime-contract research repo with HAI as the first
reference runtime.

## North Star

Runtime contracts can make smaller local models viable operators for
bounded workflows over sensitive user-owned data by moving authority,
validation, and audit from the model into enforceable local software.

The model proposes, routes, clarifies, and explains. The runtime owns
truth, validation, mutation, policy, and audit.

## Decision Log

Project-level decisions from the reframe are recorded in
[`PROJECT_DECISIONS.md`](PROJECT_DECISIONS.md). Use that file to recover
decisions that would otherwise depend on conversation memory: the
research-first repo identity, GovernedAgentBench naming, title package,
measurement posture, health boundary, experiment scope, MVP domain scope,
and documentation architecture.

## Active Artifacts

| Artifact | Role | Canonical docs |
|---|---|---|
| Runtime contract | The intervention: capabilities manifest, typed commands, mutation classes, `agent_safe`, schemas, proposal/commit separation, deterministic gates, policy, and audit. | `PROJECT_FRAME.md`, `PROJECT_OPERATING_MODEL.md`, `research/runtime_contracts_paper/PAPER_FRAME.md`, `ARCHITECTURE.md` |
| HAI | Personal-wellness reference runtime, packaged as `health-agent-infra` and exposed through `hai`. | `docs/hai/hai_reference_runtime.md`, `docs/hai/`, `src/health_agent_infra/` |
| GovernedAgentBench | Benchmark artifact for contract-governed agent operation. | `benchmarks/governed_agent_bench/`, `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`, `research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md` |
| Paper | Research-engineering systems/evals paper. | `research/runtime_contracts_paper/`, `HYPOTHESES.md` |

## Target Repo Shape

The target top-level ownership model is:

- `project/` — project memory and repo governance.
- `hai/` — HAI reference runtime, HAI docs, HAI verification, and HAI
  reporting/provenance.
- `benchmark/` — GovernedAgentBench and its verification.
- `research/` — paper and experiment-planning artifacts.

The current physical layout has not yet been migrated. `src/`,
`docs/hai/`, `verification/`, `reporting/`, and `benchmarks/` should be
read as transitional paths whose target owners are documented in
`PROJECT_OPERATING_MODEL.md` and `REPO_MAP.md`.

## Priority Order

Until the workshop / preprint push is complete, default priority is:

1. HAI paper-readiness engineering: make the reference runtime usable by
   the paper and benchmark.
2. GovernedAgentBench measurement-readiness: create a benchmark that can
   evaluate governed agent operation and prove it can score known-good
   and known-bad trajectories, so it can support paper experiments.
3. Experiments: local models, cloud models, fine-tuned local operators,
   and scaffold ablations.
4. HAI reference-runtime maintenance needed by the paper.
5. HAI v1 polish only when it directly supports the paper or benchmark.

This is not a cancellation of HAI. It is a sequencing decision: HAI is
the demonstrator; the benchmark and paper are the research-engineering
artifacts.

## Health Boundary

HAI is a personal-wellness reference domain, not clinical software.

- No diagnosis.
- No treatment.
- No prescribing.
- No autonomous medical decisions.
- No private health rows in public benchmark fixtures or training data.

This boundary is part of the runtime contract being evaluated, not a
footer disclaimer.

## Documentation Rule

Cold agents should read in this order:

1. `PROJECT_FRAME.md`
2. `PROJECT_DECISIONS.md`
3. `PROJECT_OPERATING_MODEL.md`
4. `AGENTS.md`
5. `research/runtime_contracts_paper/PAPER_FRAME.md`
6. `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`
7. `research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md`
8. `research/runtime_contracts_paper/HAI_PAPER_READINESS_PLAN.md` if
   the task touches HAI runtime work
9. `research/runtime_contracts_paper/WORK_PACKETS.md` before assigning
   implementation work
10. `benchmarks/governed_agent_bench/README.md`
11. `benchmarks/governed_agent_bench/BENCHMARK_SPEC.md` if the task
    touches benchmark design
12. `README.md`
13. `ROADMAP.md`
14. `docs/hai/hai_reference_runtime.md` if the task touches HAI
15. `docs/hai/current_system_state.md`

Historical release plans under `reporting/plans/` explain how HAI got
here. They are not the default source of current project priority when
they disagree with this frame.
