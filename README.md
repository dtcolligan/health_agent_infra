# Runtime Contracts for Local Agents

This repository is a research project studying a runtime-governance
question:

> Can enforceable local software contracts make smaller local models
> viable operators for bounded workflows over sensitive user-owned data?

The core claim is not health-specific. HAI, the personal-wellness
runtime in this repo, is the first reference implementation used to make
the claim testable.

[![PyPI](https://img.shields.io/pypi/v/health-agent-infra)](https://pypi.org/project/health-agent-infra/)
[![Tests](https://img.shields.io/badge/tests-2943_passing-green)](verification/tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Project Shape

| Artifact | Role | Status |
|---|---|---|
| **Runtime contract** | The intervention: capabilities manifest, typed commands, mutation classes, `agent_safe`, output schemas, proposal/commit separation, deterministic gates, policy, and audit. | Implemented in HAI; HAI is being engineered for paper use. |
| **GovernedAgentBench** | Benchmark for contract-governed agent operation over sensitive user-owned structured data. | Scaffold exists; measurement-readiness is next. |
| **HAI** | Personal-wellness reference runtime, packaged as `health-agent-infra` and exposed through the local `hai` CLI. | Working maintainer-dogfooded runtime at source version `0.2.0`. |
| **Paper** | Research-engineering systems/evals paper around local governed agents and model-scale reduction. | Frame locked; empirical design and benchmark buildout in progress. |

The canonical internal project-memory file is
[`PROJECT_FRAME.md`](PROJECT_FRAME.md). The post-reframe decision log is
[`PROJECT_DECISIONS.md`](PROJECT_DECISIONS.md). The internal operating
model is [`PROJECT_OPERATING_MODEL.md`](PROJECT_OPERATING_MODEL.md). The
locked paper frame lives at
[`research/runtime_contracts_paper/PAPER_FRAME.md`](research/runtime_contracts_paper/PAPER_FRAME.md).

## Research Thesis

Large language models are useful operators, but weak sources of durable
truth. In sensitive workflows, the model should not also be the database,
validator, policy engine, migration layer, and auditor.

This repo tests a different division of labor:

- the **model** proposes, routes, clarifies, and explains;
- the **runtime** owns truth, validation, mutation, policy, and audit.

The paper's conservative claim form is measurement-first: runtime
contracts may reduce the model capability required for bounded operation
by moving reliability out of the model and into enforceable local
software.

## What The Contract Contains

The contract is the unit of intervention. In HAI today it includes:

- a machine-readable capabilities manifest;
- explicit `agent_safe` markings for every command;
- mutation classes and idempotency metadata;
- typed command arguments and output schemas;
- proposal/commit separation for user-owned goals, targets, and plans;
- deterministic validation gates and exit-code semantics;
- local SQLite state plus JSONL audit logs;
- non-clinical policy boundaries in the health reference domain.

The agent does not guess what it may do. It reads the manifest and acts
through the runtime.

## GovernedAgentBench

GovernedAgentBench is the benchmark artifact. It should become the
research-engineering object that another lab can inspect, run, and extend.

The intended benchmark compares systems under the same tasks and scorer:

- local models with and without the runtime contract;
- cloud models with and without the runtime contract;
- fine-tuned local operators;
- rule baselines;
- scaffold ablations such as no manifest, no output schemas, no
  proposal gate, stale manifest, and no audit references.

Start at
[`benchmarks/governed_agent_bench/README.md`](benchmarks/governed_agent_bench/README.md).

## HAI Reference Runtime

HAI is the concrete runtime used to make the architecture real. It is a
local-first personal-wellness system with six reference domains:
recovery, running, sleep, stress, strength, and nutrition.

It is not the paper's topic by itself. It is the demonstrator domain for
bounded operation over sensitive user-owned structured data.

Minimal HAI smoke loop:

```bash
pipx install health-agent-infra
hai init --non-interactive
hai capabilities --human
hai doctor
hai daily
hai today
```

The full HAI operator and product documentation is in
[`docs/hai/hai_reference_runtime.md`](docs/hai/hai_reference_runtime.md).

## Health Boundary

The health reference runtime is explicitly non-clinical:

- no diagnosis;
- no treatment;
- no prescribing;
- no autonomous medical decisions;
- no private health rows in public benchmark fixtures or training data.

This is part of the evaluated runtime contract, not a disclaimer placed
after the fact.

## Repository Shape

The intended repo architecture is owner-based:

| Owner lane | Purpose |
|---|---|
| `project/` | Project memory: frame, decisions, operating model, roadmap, hypotheses, repo map, and project-level alignment tests. |
| `hai/` | HAI reference-runtime lane: implementation, HAI docs, HAI verification/evals, and HAI release proof/provenance. |
| `benchmark/` | GovernedAgentBench lane: benchmark specs, schemas, tasks, scorer, baselines, reports, and benchmark verification. |
| `research/` | Paper lane: paper frame, draft, prior art, claim ladder, experiment design, and release planning. |

Root is for tooling, entrypoints, and repository metadata only:
`README.md`, `AGENTS.md`, `CLAUDE.md`, `pyproject.toml`, `uv.lock`,
`CHANGELOG.md`, citation/license/security/contribution files, and CI
metadata. `AGENTS.md`, `CLAUDE.md`, `pyproject.toml`, and `uv.lock` stay
at root because external tools discover them there.

The current physical tree is transitional. The map below shows the
current paths and their target owners.

| Path | Purpose |
|---|---|
| [`PROJECT_FRAME.md`](PROJECT_FRAME.md), [`PROJECT_DECISIONS.md`](PROJECT_DECISIONS.md), [`PROJECT_OPERATING_MODEL.md`](PROJECT_OPERATING_MODEL.md), [`HYPOTHESES.md`](HYPOTHESES.md), [`ROADMAP.md`](ROADMAP.md), [`REPO_MAP.md`](REPO_MAP.md) | Transitional project-control docs; target owner `project/`. |
| [`research/runtime_contracts_paper/`](research/runtime_contracts_paper/) | Paper frame, draft, implementation plan, and documentation audit; target owner `research/`. |
| [`benchmarks/governed_agent_bench/`](benchmarks/governed_agent_bench/) | GovernedAgentBench schemas, tasks, manifests, scorer, baselines, and reports; target owner `benchmark/`. |
| [`src/health_agent_infra/`](src/health_agent_infra/) | HAI reference-runtime source package; target owner `hai/`. |
| [`docs/hai/`](docs/hai/) | HAI runtime/operator documentation; target owner `hai/`. |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | HAI one-page architecture summary; target owner `hai/docs/`. |
| [`reporting/`](reporting/) | HAI release history, audit trail, pre-reframe strategy docs, and proof artifacts; target owner `hai/`. |
| [`AUDIT.md`](AUDIT.md) | HAI release-audit index; target owner `hai/reporting/`. |
| [`verification/`](verification/) | Transitional verification root. HAI tests/evals belong under `hai/verification/`; benchmark tests belong under `benchmark/verification/`; project alignment tests belong under `project/tests/`. |

## Current Priority

Until the workshop / preprint push is complete, default priority is:

1. Planning Gate 1: master execution specs and bounded work packets.
2. HAI paper-readiness engineering: make the reference runtime usable by
   the paper and benchmark.
3. GovernedAgentBench measurement-readiness: create a benchmark that can
   evaluate governed agent operation and prove it can score known-good
   and known-bad trajectories, so it can be the measurement instrument
   for baselines, models, and ablations.
4. Experiments: local models, cloud models, fine-tuned local operators,
   and scaffold ablations.
5. HAI reference-runtime maintenance needed by the paper.
6. HAI v1 polish only when it directly supports the paper or benchmark.

See [`ROADMAP.md`](ROADMAP.md) for the research-first roadmap.

## Read Next

| Reader | Best next docs |
|---|---|
| Research / benchmark reviewer | [`PROJECT_FRAME.md`](PROJECT_FRAME.md), [`PROJECT_DECISIONS.md`](PROJECT_DECISIONS.md), [`PROJECT_OPERATING_MODEL.md`](PROJECT_OPERATING_MODEL.md), [`HYPOTHESES.md`](HYPOTHESES.md), [`research/runtime_contracts_paper/PAPER_FRAME.md`](research/runtime_contracts_paper/PAPER_FRAME.md), [`research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md`](research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md), [`research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`](research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md), [`benchmarks/governed_agent_bench/README.md`](benchmarks/governed_agent_bench/README.md) |
| HAI user or operator | [`docs/hai/hai_reference_runtime.md`](docs/hai/hai_reference_runtime.md), [`docs/hai/current_system_state.md`](docs/hai/current_system_state.md), [`docs/hai/privacy.md`](docs/hai/privacy.md), [`docs/hai/non_goals.md`](docs/hai/non_goals.md) |
| Host-agent integrator | [`docs/hai/host_agent_contract.md`](docs/hai/host_agent_contract.md), [`docs/hai/agent_integration.md`](docs/hai/agent_integration.md), [`docs/hai/agent_cli_contract.md`](docs/hai/agent_cli_contract.md) |
| Runtime contributor | [`CONTRIBUTING.md`](CONTRIBUTING.md), [`docs/hai/architecture.md`](docs/hai/architecture.md), [`docs/hai/domains/README.md`](docs/hai/domains/README.md), [`docs/hai/x_rules.md`](docs/hai/x_rules.md) |
| Maintainer or release auditor | [`REPO_MAP.md`](REPO_MAP.md), [`AUDIT.md`](AUDIT.md), [`ROADMAP.md`](ROADMAP.md), [`CHANGELOG.md`](CHANGELOG.md), [`reporting/plans/README.md`](reporting/plans/README.md) |

## License

MIT. See [LICENSE](LICENSE).
