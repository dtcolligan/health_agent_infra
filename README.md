# Runtime Contracts for Local Agents

This repository is a research project studying a runtime-governance
question:

> Can enforceable local software contracts make smaller local models
> viable operators for bounded workflows over sensitive user-owned data?

The core claim is not health-specific. HAI, the personal-wellness
runtime in this repo, is the first reference implementation used to make
the claim testable.

[![PyPI](https://img.shields.io/pypi/v/health-agent-infra)](https://pypi.org/project/health-agent-infra/)
[![Tests](https://img.shields.io/badge/tests-2943_passing-green)](hai/verification/tests/)
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
[`project/FRAME.md`](project/FRAME.md). The post-reframe decision log is
[`project/DECISIONS.md`](project/DECISIONS.md). The internal operating
model is [`project/OPERATING_MODEL.md`](project/OPERATING_MODEL.md). The
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
[`benchmark/governed_agent_bench/README.md`](benchmark/governed_agent_bench/README.md).

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

The full HAI operator and reference-runtime documentation is in
[`hai/docs/hai_reference_runtime.md`](hai/docs/hai_reference_runtime.md).

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
| `hai/` | HAI reference-runtime lane: implementation, HAI docs, HAI verification/evals, HAI assets, and HAI release proof/provenance. |
| `benchmark/` | GovernedAgentBench lane: benchmark specs, schemas, tasks, scorer, baselines, reports, and benchmark verification. |
| `research/` | Paper lane: paper frame, draft, prior art, claim ladder, experiment design, and release planning. |

Root is for tooling, entrypoints, and repository metadata only:
`README.md`, `AGENTS.md`, `CLAUDE.md`, `pyproject.toml`, `uv.lock`,
`CHANGELOG.md`, citation/license/security/contribution files, and CI
metadata. `AGENTS.md`, `CLAUDE.md`, `pyproject.toml`, and `uv.lock` stay
at root because external tools discover them there.

The physical tree now follows that owner model. The map below shows the
current top-level lanes and tool-discovered root files.

| Path | Purpose |
|---|---|
| [`project/`](project/) | Project frame, decisions, operating model, roadmap, hypotheses, repo map, and project-level alignment tests. |
| [`hai/`](hai/) | HAI source package, runtime docs, HAI verification/evals, HAI assets, release proof, and historical HAI provenance. |
| [`benchmark/`](benchmark/) | GovernedAgentBench specs, schemas, tasks, manifests, scorer, baselines, reports, and benchmark verification. |
| [`research/`](research/) | Paper frame, draft, implementation plan, prior art, claim ladder, and experiment planning. |
| [`AGENTS.md`](AGENTS.md), [`CLAUDE.md`](CLAUDE.md), [`pyproject.toml`](pyproject.toml), [`uv.lock`](uv.lock) | Root tool entrypoints and package metadata that external tools expect at the repository root. |

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

See [`project/ROADMAP.md`](project/ROADMAP.md) for the research-first roadmap.

## Read Next

| Reader | Best next docs |
|---|---|
| Research / benchmark reviewer | [`project/FRAME.md`](project/FRAME.md), [`project/DECISIONS.md`](project/DECISIONS.md), [`project/OPERATING_MODEL.md`](project/OPERATING_MODEL.md), [`project/HYPOTHESES.md`](project/HYPOTHESES.md), [`research/runtime_contracts_paper/PAPER_FRAME.md`](research/runtime_contracts_paper/PAPER_FRAME.md), [`research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md`](research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md), [`research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`](research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md), [`benchmark/governed_agent_bench/README.md`](benchmark/governed_agent_bench/README.md) |
| HAI user or operator | [`hai/docs/hai_reference_runtime.md`](hai/docs/hai_reference_runtime.md), [`hai/docs/current_system_state.md`](hai/docs/current_system_state.md), [`hai/docs/privacy.md`](hai/docs/privacy.md), [`hai/docs/non_goals.md`](hai/docs/non_goals.md) |
| Host-agent integrator | [`hai/docs/host_agent_contract.md`](hai/docs/host_agent_contract.md), [`hai/docs/agent_integration.md`](hai/docs/agent_integration.md), [`hai/docs/agent_cli_contract.md`](hai/docs/agent_cli_contract.md) |
| Runtime contributor | [`CONTRIBUTING.md`](CONTRIBUTING.md), [`hai/docs/architecture.md`](hai/docs/architecture.md), [`hai/docs/domains/README.md`](hai/docs/domains/README.md), [`hai/docs/x_rules.md`](hai/docs/x_rules.md) |
| Maintainer or release auditor | [`project/REPO_MAP.md`](project/REPO_MAP.md), [`hai/reporting/AUDIT.md`](hai/reporting/AUDIT.md), [`project/ROADMAP.md`](project/ROADMAP.md), [`CHANGELOG.md`](CHANGELOG.md), [`hai/reporting/plans/README.md`](hai/reporting/plans/README.md) |

## License

MIT. See [LICENSE](LICENSE).
