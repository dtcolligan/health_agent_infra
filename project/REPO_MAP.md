# Repo Map

One-page orientation: what every top-level entry is, which owner lane it
belongs to, what is current versus historical, and where to look next.
Pair with [`../README.md`](../README.md) for the research-facing repo
overview and [`../hai/docs/hai_reference_runtime.md`](../hai/docs/hai_reference_runtime.md)
for the HAI operator manual.

## Physical Ownership Model

The top-level shape is owner-based:

| Owner | Owns |
|---|---|
| `project/` | Project memory, decisions, operating model, roadmap, hypotheses, repo map, and project-level alignment tests. |
| `hai/` | HAI implementation, HAI docs, HAI verification/evals, HAI assets, release proof, support-lane backlog, and historical HAI provenance. |
| `benchmark/` | GovernedAgentBench specs, schemas, tasks, manifests, scorer, baselines, reports, and benchmark-specific verification. |
| `research/` | Runtime-contract paper frame, framing-v2 orchestration, draft, prior art, claim ladder, experiment design, and release planning. |
| root | Tool-discovered entrypoints and repository metadata only. |

Root stays shallow because external tools expect certain files there:
`README.md`, `AGENTS.md`, `CLAUDE.md`, `pyproject.toml`, `uv.lock`,
`CHANGELOG.md`, citation/license/security/contribution files, CI
metadata, and small repository tooling scripts.

## Top-Level Entries

| Path | Class | What it is |
|---|---|---|
| [`../README.md`](../README.md) | root metadata | Research-facing repo overview, artifact map, current priority, and read-next links. |
| [`./`](./) | project lane | Current project memory: frame, decisions, operating model, roadmap, hypotheses, repo map, and project-level alignment tests. |
| [`../hai/`](../hai/) | HAI lane | Reference-runtime source, HAI docs, HAI verification/evals, HAI assets, HAI release proof, support-lane backlog, and historical HAI provenance. |
| [`../benchmark/`](../benchmark/) | benchmark lane | GovernedAgentBench specs, schemas, tasks, manifests, scorer, baselines, reports, and benchmark verification. |
| [`../research/`](../research/) | research lane | Runtime-contract paper frame, framing-v2 orchestration, draft, prior art, claim ladder, experiment design, and release-package planning. |
| [`../scripts/`](../scripts/) | root tooling | Small repository-level maintenance scripts that are not owned by the runtime package. |
| [`../CHANGELOG.md`](../CHANGELOG.md) | root metadata | Public release history. |
| [`../AGENTS.md`](../AGENTS.md) | root tool entrypoint | Agent-facing operating contract for Codex, Claude Code, and similar coding agents. |
| [`../CLAUDE.md`](../CLAUDE.md) | root tool entrypoint | Claude Code shim that imports `AGENTS.md` and adds Claude-specific notes. |
| [`../SECURITY.md`](../SECURITY.md) | root metadata | Vulnerability reporting and scope of trust. |
| [`../CITATION.cff`](../CITATION.cff) | root metadata | Citation metadata; DOI placeholders await manual Zenodo registration. |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | root metadata | Code-vs-skill mental model, how to add runtime code or a skill, before-PR checks. |
| [`../LICENSE`](../LICENSE) | root metadata | MIT license. |
| [`../pyproject.toml`](../pyproject.toml), [`../uv.lock`](../uv.lock) | root tool entrypoints | Packaging configuration and dependency lock at the highest level because Python packaging tools discover them there. |
| [`../.env.example`](../.env.example) | root metadata | Example environment file. |
| [`../.github/`](../.github/) | root tooling | CI workflows. |
| [`../.gitignore`](../.gitignore) | root metadata | Ignore rules. |

There should be no permanent root `src/`, root `docs/`, root
`verification/`, root `reporting/`, root `benchmarks/`, or root
`assets/` owner roots. Put another way: root `src/`, root `docs/`,
root `verification/`, root `reporting/`, root `benchmarks/`, and root
`assets/` are suspect. If one appears, decide whether it belongs under
`hai/`, `benchmark/`, `research/`, or `project/`.

## Lane Contents

| You want to | Start at |
|---|---|
| Understand the current objective | [`FRAME.md`](FRAME.md), then [`DECISIONS.md`](DECISIONS.md), then [`OPERATING_MODEL.md`](OPERATING_MODEL.md), then [`../research/runtime_contracts_paper/framing_v2/CONVERGED.md`](../research/runtime_contracts_paper/framing_v2/CONVERGED.md) |
| Understand the locked paper framing | [`../research/runtime_contracts_paper/framing_v2/CONVERGED.md`](../research/runtime_contracts_paper/framing_v2/CONVERGED.md), then [`../research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`](../research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md), then [`../research/runtime_contracts_paper/PAPER_FRAME.md`](../research/runtime_contracts_paper/PAPER_FRAME.md) |
| Understand the benchmark | [`../benchmark/governed_agent_bench/README.md`](../benchmark/governed_agent_bench/README.md), then [`../benchmark/governed_agent_bench/BENCHMARK_SPEC.md`](../benchmark/governed_agent_bench/BENCHMARK_SPEC.md) |
| Understand HAI as software | [`../hai/docs/hai_reference_runtime.md`](../hai/docs/hai_reference_runtime.md), then [`../hai/docs/tour.md`](../hai/docs/tour.md) |
| Know what is shipped right now | [`../hai/docs/current_system_state.md`](../hai/docs/current_system_state.md), then [`../CHANGELOG.md`](../CHANGELOG.md) and [`../hai/reporting/AUDIT.md`](../hai/reporting/AUDIT.md) |
| Take the guided 10-minute HAI tour | [`../hai/docs/tour.md`](../hai/docs/tour.md) |
| Read the runtime architecture | [`../hai/docs/architecture.md`](../hai/docs/architecture.md) and [`../hai/docs/runtime_contract_overview.md`](../hai/docs/runtime_contract_overview.md) |
| Read the agent CLI contract | [`../hai/docs/agent_cli_contract.md`](../hai/docs/agent_cli_contract.md) |
| Add runtime code or a skill | [`../CONTRIBUTING.md`](../CONTRIBUTING.md) |
| Read the current roadmap | [`ROADMAP.md`](ROADMAP.md) |
| Read the HAI support-lane backlog | [`../hai/reporting/plans/tactical_plan_v0_1_x.md`](../hai/reporting/plans/tactical_plan_v0_1_x.md) |
| Run the persona dogfood harness | [`../hai/verification/dogfood/README.md`](../hai/verification/dogfood/README.md) |
| Inspect HAI proof / eval captures | [`../hai/reporting/artifacts/`](../hai/reporting/artifacts/) |

## Active Vs Historical

- **Active project lane:** `project/FRAME.md`, `project/DECISIONS.md`,
  `project/OPERATING_MODEL.md`, `project/HYPOTHESES.md`,
  `project/ROADMAP.md`, `project/REPO_MAP.md`, and `project/tests/`.
- **Active research lane:** `research/runtime_contracts_paper/`,
  including `framing_v2/`.
- **Active framing provenance:** `research/runtime_contracts_paper/framing_v2/round_*/`
  subdirectories. These are active provenance for the locked paper
  framing, not current work queues unless an orchestration prompt says
  otherwise.
- **Active benchmark lane:** `benchmark/governed_agent_bench/` and
  `benchmark/verification/`.
- **Active HAI lane:** `hai/src/health_agent_infra/`, `hai/docs/`,
  `hai/verification/`, `hai/assets/`, and `hai/reporting/`.
- **Historical HAI provenance:** `hai/reporting/plans/historical/`,
  `hai/reporting/docs/archive/`, `hai/reporting/artifacts/archive/`,
  `hai/reporting/artifacts/phase_0/`, and older cycle workspaces under
  `hai/reporting/plans/`.
- **Root/tooling docs:** `README.md`, `CHANGELOG.md`, `AGENTS.md`,
  `CLAUDE.md`, `SECURITY.md`, `CITATION.cff`, `CONTRIBUTING.md`,
  `pyproject.toml`, `uv.lock`, `.github/`, and `scripts/`.

Historical docs should stay historically honest. They may reference old
paths, release names, and pre-reframe strategy, but their indexes and
headers must make clear that current project priority is defined by
`project/`, `research/`, `benchmark/`, and the HAI support lane.

## Local-Generated / Non-Canonical

These may exist on disk but are not part of the repo structure. They are
ignored, generated, or environment-local:

- `.venv/`, `.pytest_cache/`, `__pycache__/` - Python tooling caches.
- `build/`, `dist/` - wheel/sdist build outputs.
- `.claude/` - local Claude Code state.
- `data/`, `artifacts/` at root - local runtime data, if present.

If you find a checked-in top-level path that is not classified above,
treat it as suspect and check git history before trusting it.
