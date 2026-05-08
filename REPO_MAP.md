# Repo map

One-page orientation: what every top-level entry is, which owner lane it
belongs to, what is current versus historical, and where to look next. Pair with
[`README.md`](README.md) for the research-facing repo overview and
[`docs/hai/hai_reference_runtime.md`](docs/hai/hai_reference_runtime.md)
for the HAI operator manual.

## Target ownership model

The target top-level shape is owner-based:

| Target owner | Owns |
|---|---|
| `project/` | Project memory, decisions, operating model, roadmap, hypotheses, repo map, and project-level alignment tests. |
| `hai/` | HAI implementation, HAI docs, HAI verification/evals, release proof, support-lane backlog, and historical HAI provenance. |
| `benchmark/` | GovernedAgentBench specs, schemas, tasks, manifests, scorer, baselines, reports, and benchmark-specific verification. |
| `research/` | Paper frame, draft, prior art, claim ladder, experiment design, and release planning. |

Root is for tool-discovered entrypoints and repository metadata only:
`README.md`, `AGENTS.md`, `CLAUDE.md`, `pyproject.toml`, `uv.lock`,
`CHANGELOG.md`, citation/license/security/contribution files, and CI
metadata.

The current physical tree is transitional. Do not infer the project
architecture from support-function roots such as `verification/` or
`reporting/`; those should be absorbed by their owner lanes in a future
bounded migration.

## Top-level entries

| Path | Class | What it is |
|---|---|---|
| [`PROJECT_FRAME.md`](PROJECT_FRAME.md) | transitional project docs | Canonical research framing and priority order for cold agents. Target owner: `project/`. |
| [`PROJECT_DECISIONS.md`](PROJECT_DECISIONS.md) | transitional project docs | Post-reframe project decision log: research-first identity, GovernedAgentBench naming, title package, experiment scope, and documentation architecture. Target owner: `project/`. |
| [`PROJECT_OPERATING_MODEL.md`](PROJECT_OPERATING_MODEL.md) | transitional project docs | Internal operating model for the post-reframe repo: documentation gate, artifact hierarchy, decision rules, and success conditions. Target owner: `project/`. |
| [`research/`](research/) | active research | Paper frame, draft, execution plan, and documentation-alignment audit for the runtime-contract / GovernedAgentBench direction. |
| [`benchmarks/`](benchmarks/) | transitional benchmark root | GovernedAgentBench scaffold: schemas, tasks, manifests, scorer, baselines, and reports. Target owner: `benchmark/`. |
| [`docs/`](docs/) | transitional docs root | Current docs that are not root-control material. `docs/hai/` is target-owned by `hai/`. |
| [`src/`](src/health_agent_infra/) | transitional runtime root | The `health_agent_infra` Python package: CLI, core orchestration, per-domain logic, packaged skills, packaged eval framework, the committed Garmin CSV fixture. Target owner: `hai/`. |
| [`reporting/`](reporting/) | transitional HAI provenance root | HAI release proof, audit trail, historical planning, legacy docs archive, and frozen prototypes. Target owner: `hai/reporting/`. |
| [`verification/`](verification/) | transitional verification root | HAI tests/evals, benchmark tests, project doc-alignment tests, harnesses, drift checks, and legacy verification scripts. Target owners: `hai/verification/`, `benchmark/verification/`, and `project/tests/`. |
| [`README.md`](README.md) | active docs | Research-facing repo overview, artifact map, current priority, and read-next links. |
| [`CHANGELOG.md`](CHANGELOG.md) | root metadata | Public release history. |
| [`AGENTS.md`](AGENTS.md) | active docs | Agent-facing operating contract for Codex, Claude Code, and similar coding agents. |
| [`CLAUDE.md`](CLAUDE.md) | active docs | Claude Code shim that imports `AGENTS.md` and adds Claude-specific notes. |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | transitional HAI docs | One-page HAI architecture summary and links to deep docs. Target owner: `hai/docs/`. |
| [`AUDIT.md`](AUDIT.md) | transitional HAI reporting | Release-by-release audit-cycle index. Target owner: `hai/reporting/`. |
| [`HYPOTHESES.md`](HYPOTHESES.md) | active docs | Current research hypotheses for runtime contracts, model scale, fine-tuning, benchmark generality, and non-clinical boundaries. |
| [`ROADMAP.md`](ROADMAP.md) | active docs | Now / Next / Later roadmap. |
| [`SECURITY.md`](SECURITY.md) | active docs | Vulnerability reporting and scope of trust. |
| [`CITATION.cff`](CITATION.cff) | active docs | Citation metadata; DOI placeholders await manual Zenodo registration. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | active docs | Code-vs-skill mental model, how to add runtime code or a skill, before-PR checks. |
| [`LICENSE`](LICENSE) | active | MIT. |
| `pyproject.toml`, `uv.lock` | active runtime | Packaging + lock. |
| `.env.example` | active runtime | Example env file. |
| `.github/` | active runtime infra | CI workflows. |
| `.gitignore` | active | Tracked. |

## Local-generated / non-canonical (not part of repo shape)

These exist on disk but are not the repo's structure. They are
either ignored, generated, or environment-local:

- `.venv/`, `.pytest_cache/`, `__pycache__/` — Python tooling caches.
- `build/`, `dist/` — wheel/sdist build outputs (`uv run python -m build`).
- `.claude/` — local Claude Code state (gitignored).
- `data/`, `artifacts/` (root, untracked) — local runtime data the
  `verification/data` and `verification/artifacts` symlinks point at when
  present. See [`verification/README.md`](verification/README.md).

If `ls` shows one of these, it is a local artifact, not part of the
checked-in repo shape.

## Where to start reading

| You want to | Start at |
|---|---|
| Understand the current objective | [`PROJECT_FRAME.md`](PROJECT_FRAME.md), then [`PROJECT_DECISIONS.md`](PROJECT_DECISIONS.md), then [`PROJECT_OPERATING_MODEL.md`](PROJECT_OPERATING_MODEL.md), then [`research/runtime_contracts_paper/PAPER_FRAME.md`](research/runtime_contracts_paper/PAPER_FRAME.md) |
| Understand the benchmark | [`benchmarks/governed_agent_bench/README.md`](benchmarks/governed_agent_bench/README.md), then [`research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`](research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md) |
| Understand HAI as software | [`docs/hai/hai_reference_runtime.md`](docs/hai/hai_reference_runtime.md), then [`docs/hai/tour.md`](docs/hai/tour.md) |
| Know what is shipped right now | [`docs/hai/current_system_state.md`](docs/hai/current_system_state.md), then [`CHANGELOG.md`](CHANGELOG.md) and [`AUDIT.md`](AUDIT.md) |
| Take the guided 10-minute tour | [`docs/hai/tour.md`](docs/hai/tour.md) |
| Read the architecture | [`docs/hai/architecture.md`](docs/hai/architecture.md) |
| See how `hai explain` works (three-state audit) | [`docs/hai/explainability.md`](docs/hai/explainability.md) |
| Read the agent CLI contract | [`docs/hai/agent_cli_contract.md`](docs/hai/agent_cli_contract.md) |
| Add runtime code or a skill | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| See the forward roadmap | [`reporting/plans/README.md`](reporting/plans/README.md) (reading-order index for the planning tree) |
| Read the current roadmap | [`ROADMAP.md`](ROADMAP.md) |
| Read the HAI runtime backlog | [`reporting/plans/tactical_plan_v0_1_x.md`](reporting/plans/tactical_plan_v0_1_x.md) |
| Run the persona dogfood harness | [`verification/dogfood/README.md`](verification/dogfood/README.md) |
| Inspect proof / eval captures | [`reporting/artifacts/`](reporting/artifacts/) |
| See what was tried and discarded before v1 | [`reporting/experiments/`](reporting/experiments/) |

## Active vs historical at a glance

- **Active project frame** (target owner `project/`): `PROJECT_FRAME.md`,
  `PROJECT_DECISIONS.md`, `PROJECT_OPERATING_MODEL.md`, `HYPOTHESES.md`,
  `ROADMAP.md`, and `REPO_MAP.md`.
- **Active research lane**: `research/runtime_contracts_paper/`.
- **Active benchmark lane** (target owner `benchmark/`):
  `benchmarks/governed_agent_bench/`.
- **Active HAI lane** (target owner `hai/`): `src/health_agent_infra/`,
  `docs/hai/`, HAI-specific `verification/`, and `reporting/`.
- **Active root/tooling docs**: `README.md`, `CHANGELOG.md`, `AGENTS.md`, `CLAUDE.md`,
  `ARCHITECTURE.md`, `AUDIT.md`, `PROJECT_OPERATING_MODEL.md`,
  `HYPOTHESES.md`, `ROADMAP.md`, `SECURITY.md`, `CITATION.cff`,
  `CONTRIBUTING.md`, `REPO_MAP.md`,
  current docs directly under `docs/hai/`
  (including `agent_cli_contract.md` — generated from `hai
  capabilities --json`; `current_system_state.md` is the current-truth
  summary),
  `reporting/plans/README.md` (HAI planning-tree reading-order index),
  `reporting/plans/post_v0_1_18/strategic_plan_v2.md` (pre-reframe HAI
  reference-runtime strategy, provenance/support-lane only),
  `reporting/plans/tactical_plan_v0_1_x.md` (HAI runtime backlog,
  with shipped-history sections that should be read as provenance),
  `reporting/plans/eval_strategy/`,
  `reporting/plans/success_framework_v1.md`, and
  `reporting/plans/risks_and_open_questions.md` (all HAI support-lane
  docs, not current project-wide research strategy), plus the
  current/future cycle workspaces and between-cycle notes.
- **SUPERSEDED 2026-04-27**: `reporting/plans/historical/multi_release_roadmap.md` —
  preserved as historical provenance; do not act on its release
  schedule. Use the strategic + tactical plans above.
- **Active proof**:
  `reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/`.
- **Transitional tests + evals**: `verification/tests/`, `verification/evals/`,
  `verification/dogfood/` (the persona harness, NEW v0.1.10). These are
  not a permanent top-level project artifact; they should migrate by
  owner (`hai/verification/`, `benchmark/verification/`,
  `project/tests/`). Today, the
  packaged eval runner lives at `src/health_agent_infra/evals/`;
  `verification/evals/` retains dev-reference docs and the skill-harness
  pilot; `verification/dogfood/` drives synthetic personas through the
  full pipeline as permanent regression infrastructure.
- **Historical / archived (still on disk, clearly labelled)**:
  `reporting/docs/archive/doctrine/`,
  `reporting/docs/archive/cycle_artifacts/`,
  `reporting/docs/archive/merge_human_inputs/`,
  `reporting/docs/launch/`,
  `reporting/artifacts/archive/`, `reporting/artifacts/phase_0/`,
  `reporting/experiments/`,
  `reporting/plans/docs_overhaul/codex_review.md`,
  `reporting/plans/historical/` (9 superseded planning docs:
  `launch_notes.md`, `skill_harness_rfc.md`, `phase_0_findings.md`,
  `phase_0_5_synthesis_prototype.md`, `phase_2_5_retrieval_gate.md`,
  `phase_2_5_independent_eval.md`, `agent_operable_runtime_plan.md`,
  `post_v0_1_roadmap.md`, `multi_release_roadmap.md`),
  `reporting/plans/future_strategy_2026-04-29/` (Claude/Codex deep
  strategy review + reconciliation),
  `verification/scripts/`.

If you find a path that is not classified above, treat it as
suspect and check git log before trusting it.
