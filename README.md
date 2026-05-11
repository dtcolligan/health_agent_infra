# Deterministic Software Contracts as Trusted Monitors in AI Control Protocols

This repository is the active artifact for a NeurIPS 2027
main-conference target: deterministic software contracts as trusted
monitors in AI control protocols. The paper asks whether a local
runtime contract can operationalize a safety spec for bounded agent
operation, with HAI as the reference runtime and GovernedAgentBench as
the benchmark. The project is pre-pilot: it has an implemented
reference runtime, a benchmark scaffold, and a locked pilot protocol,
not paper results.

[![PyPI](https://img.shields.io/pypi/v/health-agent-infra)](https://pypi.org/project/health-agent-infra/)
[![Tests](https://img.shields.io/badge/tests-2943_passing-green)](hai/verification/tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Project Shape

| Artifact | Role | Status |
|---|---|---|
| **Paper** | Merged systems/evals submission: runtime-contract architecture + GovernedAgentBench + Engels Backdoor Code extension. | Phase 1 framing closed 2026-05-11; Phase 2 documentation alignment in progress; NeurIPS 2027 main-conference target. |
| **Runtime contract** | The intervention: capabilities manifest, typed commands, mutation classes, `agent_safe`, output schemas, proposal/commit separation, deterministic gates, policy, and audit evidence emission. | Implemented in HAI v0.2.0 as the reference runtime; product development is frozen except for paper-critical support. |
| **GovernedAgentBench** | Benchmark for contract-governed agent operation with runtime-mode intervention and mechanism-isolable ablation under a held-constant prompt. | Pre-measurement-ready scaffold; scorer, harness, schemas, and baselines are being aligned before model-backed runs. |
| **HAI** | Personal-wellness reference runtime, packaged as `health-agent-infra` and exposed through the local `hai` CLI. | Working maintainer-dogfooded runtime at source version `0.2.0`; reference snapshot for paper and benchmark work. |

The canonical paper-framing source of truth is
[`research/runtime_contracts_paper/framing_v2/CONVERGED.md`](research/runtime_contracts_paper/framing_v2/CONVERGED.md),
with the full decisions table in
[`research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`](research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md).
The canonical internal project-memory file is
[`project/FRAME.md`](project/FRAME.md). The post-reframe decision log is
[`project/DECISIONS.md`](project/DECISIONS.md). The internal operating
model is [`project/OPERATING_MODEL.md`](project/OPERATING_MODEL.md). The
locked paper frame lives at
[`research/runtime_contracts_paper/PAPER_FRAME.md`](research/runtime_contracts_paper/PAPER_FRAME.md).

## Status

- Phase 1 framing convergence closed on 2026-05-11 with D-FRAME-001..027
  locked in `framing_v2/CONVERGED.md`.
- Phase 2 documentation alignment is in progress.
- The Engels pilot in July 2026 is the merge-decision gate before full
  paper-claim runs.
- Submission target: NeurIPS 2027 main conference, May 2027 deadline.

## Research Thesis

Large language models are useful operators, but weak sources of durable
truth. In sensitive workflows, the model should not also be the database,
validator, policy engine, migration layer, and auditor.

This repo tests a different division of labor:

- the **model** proposes, routes, clarifies, and explains;
- the **runtime** owns truth, validation, mutation, policy, and audit.

The paper's conservative claim form is measurement-first: runtime
contracts may reduce the model capability required for bounded operation
by moving reliability out of the model and into an enforceable local
trusted-monitor substrate.

## What The Contract Contains

The contract is the unit of intervention. In HAI today it includes:

- a machine-readable capabilities manifest;
- explicit `agent_safe` markings for every command;
- mutation classes and idempotency metadata;
- typed command arguments and output schemas;
- proposal/commit separation for user-owned goals, targets, and plans;
- deterministic validation gates and exit-code semantics;
- local SQLite state plus JSONL audit evidence;
- non-clinical policy boundaries in the health reference domain.

The agent does not guess what it may do. It reads the manifest and acts
through the runtime.

## GovernedAgentBench

GovernedAgentBench is the benchmark artifact. It should become the
research-engineering object that another lab can inspect, run, and extend.

The intended benchmark compares systems under the same tasks, the
same scorer, and a held-constant deployment-realistic prompt. The
comparison axis is `runtime_mode` x `model_class`:

- the runtime contract enforced (`full_contract`) vs each runtime
  mechanism individually disabled (`no_validation`, `no_agent_safe`,
  `no_proposal_gate`, `no_refusal`, `no_audit_chain`, where
  `no_audit_chain` means M8 audit evidence emission disabled for
  artifact compatibility) vs runtime enforcement off
  (`no_runtime_enforcement`);
- across local models, cloud models, and (future-work) fine-tuned
  local operators;
- with rule baselines anchoring deterministic-routing tasks.

The runtime is the primary axis of variation; the prompt is held
constant. See
[`research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`](research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md)
and `project/DECISIONS.md` D-PROJ-018..023 for the durable record.

Start at
[`benchmark/governed_agent_bench/README.md`](benchmark/governed_agent_bench/README.md).

## HAI Reference Runtime

HAI is the concrete runtime used to make the architecture real. It is a
local-first personal-wellness system with six reference domains:
recovery, running, sleep, stress, strength, and nutrition.

It is not the paper's topic by itself. It is the demonstrator domain
for bounded agent operation in a non-clinical reference runtime.

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

Until Phase 2 documentation alignment closes and the July 2026 Engels
pilot decision gate runs, default priority is:

1. Complete framing-v2 documentation alignment across paper, benchmark,
   project, HAI, operating, and historical docs.
2. Keep GovernedAgentBench measurement-readiness coherent: schemas,
   scorer, harness, synthetic fixtures, rule baselines, reports, and
   runtime-mode ablations must be auditable before model-backed runs.
3. Prepare the Engels pilot protocol that decides whether the merged
   paper trajectory holds.
4. Run model, ablation, and bounded monitor-contrast experiments only
   after the relevant manifests, prompts, thresholds, and scorer configs
   are frozen.
5. Make HAI runtime support changes only when they stabilize the
   contract, unblock the benchmark, or make baselines reproducible.
6. Leave HAI product polish out of scope unless Dom explicitly marks it
   paper-critical.

See [`project/ROADMAP.md`](project/ROADMAP.md) for the research-first roadmap.

## Read Next

| Reader | Best next docs |
|---|---|
| Research / benchmark reviewer | [`research/runtime_contracts_paper/framing_v2/CONVERGED.md`](research/runtime_contracts_paper/framing_v2/CONVERGED.md), [`research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`](research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md), [`project/FRAME.md`](project/FRAME.md), [`project/DECISIONS.md`](project/DECISIONS.md), [`project/OPERATING_MODEL.md`](project/OPERATING_MODEL.md), [`project/HYPOTHESES.md`](project/HYPOTHESES.md), [`research/runtime_contracts_paper/PAPER_FRAME.md`](research/runtime_contracts_paper/PAPER_FRAME.md), [`research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md`](research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md), [`research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`](research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md), [`benchmark/governed_agent_bench/README.md`](benchmark/governed_agent_bench/README.md) |
| HAI user or operator | [`hai/docs/hai_reference_runtime.md`](hai/docs/hai_reference_runtime.md), [`hai/docs/current_system_state.md`](hai/docs/current_system_state.md), [`hai/docs/privacy.md`](hai/docs/privacy.md), [`hai/docs/non_goals.md`](hai/docs/non_goals.md) |
| Host-agent integrator | [`hai/docs/host_agent_contract.md`](hai/docs/host_agent_contract.md), [`hai/docs/agent_integration.md`](hai/docs/agent_integration.md), [`hai/docs/agent_cli_contract.md`](hai/docs/agent_cli_contract.md) |
| Runtime contributor | [`CONTRIBUTING.md`](CONTRIBUTING.md), [`hai/docs/architecture.md`](hai/docs/architecture.md), [`hai/docs/domains/README.md`](hai/docs/domains/README.md), [`hai/docs/x_rules.md`](hai/docs/x_rules.md) |
| Maintainer or release auditor | [`project/REPO_MAP.md`](project/REPO_MAP.md), [`hai/reporting/AUDIT.md`](hai/reporting/AUDIT.md), [`project/ROADMAP.md`](project/ROADMAP.md), [`CHANGELOG.md`](CHANGELOG.md), [`hai/reporting/plans/README.md`](hai/reporting/plans/README.md) |

## License

MIT. See [LICENSE](LICENSE).
