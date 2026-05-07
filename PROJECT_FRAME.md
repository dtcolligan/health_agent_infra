# Project Frame

**Status:** Canonical project frame, 2026-05-07.

This repository is no longer best understood as "the HAI product
repo." It is a runtime-contract research repo with HAI as the first
reference runtime.

## North Star

Runtime contracts can make smaller local models viable operators for
bounded workflows over sensitive user-owned data by moving authority,
validation, and audit from the model into enforceable local software.

The model proposes, routes, clarifies, and explains. The runtime owns
truth, validation, mutation, policy, and audit.

## Active Artifacts

| Artifact | Role | Canonical docs |
|---|---|---|
| Runtime contract | The intervention: capabilities manifest, typed commands, mutation classes, `agent_safe`, schemas, proposal/commit separation, deterministic gates, policy, and audit. | `PROJECT_FRAME.md`, `research/runtime_contracts_paper/PAPER_FRAME.md`, `ARCHITECTURE.md` |
| HAI | Personal-wellness reference runtime, packaged as `health-agent-infra` and exposed through `hai`. | `reporting/docs/hai_reference_runtime.md`, `reporting/docs/`, `src/health_agent_infra/` |
| GovernedAgentBench | Benchmark artifact for contract-governed agent operation. | `benchmarks/governed_agent_bench/`, `research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md` |
| Paper | Research-engineering systems/evals paper. | `research/runtime_contracts_paper/` |

## Priority Order

Until the workshop / preprint push is complete, default priority is:

1. Paper-critical runtime contract documentation and stabilization.
2. GovernedAgentBench MVP: schemas, tasks, frozen manifests, scorer,
   baselines, and reports.
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
2. `AGENTS.md`
3. `research/runtime_contracts_paper/PAPER_FRAME.md`
4. `benchmarks/governed_agent_bench/README.md`
5. `README.md`
6. `ROADMAP.md`
7. `reporting/docs/hai_reference_runtime.md` if the task touches HAI
8. `reporting/docs/current_system_state.md`

Historical release plans under `reporting/plans/` explain how HAI got
here. They are not the default source of current project priority when
they disagree with this frame.
