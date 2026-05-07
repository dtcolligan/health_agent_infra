# Repo map

One-page orientation: what every top-level entry is, what is current
versus historical, and where to look next. Pair with
[`README.md`](README.md) for the product story and
[`reporting/docs/tour.md`](reporting/docs/tour.md) for the 10-minute
guided read.

## Top-level entries

| Path | Class | What it is |
|---|---|---|
| [`PROJECT_FRAME.md`](PROJECT_FRAME.md) | active docs | Canonical research framing and priority order for cold agents. |
| [`research/`](research/) | active research | Paper frame, draft, execution plan, and documentation-alignment audit for the runtime-contract / GovernedAgentBench direction. |
| [`benchmarks/`](benchmarks/) | active benchmark | GovernedAgentBench scaffold: schemas, tasks, manifests, scorer, baselines, and reports. |
| [`src/`](src/health_agent_infra/) | active runtime | The `health_agent_infra` Python package: CLI, core orchestration, per-domain logic, packaged skills, packaged eval framework, the committed Garmin CSV fixture. This is the shipped wheel. |
| [`reporting/`](reporting/) | HAI docs + proof + plans + frozen prototypes | HAI reference-runtime narrative material. See [`reporting/README.md`](reporting/README.md) for the four-subdir map. |
| [`verification/`](verification/) | active tests + active evals + legacy scripts | The repo verification surface: pytest suite, eval docs/scenarios, harnesses, drift checks, and legacy verification scripts. See [`verification/README.md`](verification/README.md) for the layout, including the symlinks into local generated data. |
| [`README.md`](README.md) | active docs | Repo overview, HAI install, CLI surface, roadmap pointers. |
| [`CHANGELOG.md`](CHANGELOG.md) | active docs | Public release history. |
| [`AGENTS.md`](AGENTS.md) | active docs | Agent-facing operating contract for Codex, Claude Code, and similar coding agents. |
| [`CLAUDE.md`](CLAUDE.md) | active docs | Claude Code shim that imports `AGENTS.md` and adds Claude-specific notes. |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | active docs | One-page architecture and links to deep docs. |
| [`AUDIT.md`](AUDIT.md) | active docs | Release-by-release audit-cycle index. |
| [`HYPOTHESES.md`](HYPOTHESES.md) | active docs | Five falsifiable roadmap hypotheses. |
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
| Understand the current objective | [`PROJECT_FRAME.md`](PROJECT_FRAME.md), then [`research/runtime_contracts_paper/PAPER_FRAME.md`](research/runtime_contracts_paper/PAPER_FRAME.md) |
| Understand the benchmark | [`benchmarks/governed_agent_bench/README.md`](benchmarks/governed_agent_bench/README.md) |
| Understand HAI as software | [`README.md`](README.md) |
| Know what is shipped right now | [`reporting/docs/current_system_state.md`](reporting/docs/current_system_state.md), then [`CHANGELOG.md`](CHANGELOG.md) and [`AUDIT.md`](AUDIT.md) |
| Take the guided 10-minute tour | [`reporting/docs/tour.md`](reporting/docs/tour.md) |
| Read the architecture | [`reporting/docs/architecture.md`](reporting/docs/architecture.md) |
| See how `hai explain` works (three-state audit) | [`reporting/docs/explainability.md`](reporting/docs/explainability.md) |
| Read the agent CLI contract | [`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md) |
| Add runtime code or a skill | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| See the forward roadmap | [`reporting/plans/README.md`](reporting/plans/README.md) (reading-order index for the planning tree) |
| Read the current roadmap | [`ROADMAP.md`](ROADMAP.md) |
| Read the HAI runtime backlog | [`reporting/plans/tactical_plan_v0_1_x.md`](reporting/plans/tactical_plan_v0_1_x.md) |
| Run the persona dogfood harness | [`verification/dogfood/README.md`](verification/dogfood/README.md) |
| Inspect proof / eval captures | [`reporting/artifacts/`](reporting/artifacts/) |
| See what was tried and discarded before v1 | [`reporting/experiments/`](reporting/experiments/) |

## Active vs historical at a glance

- **Active research frame**: `PROJECT_FRAME.md`,
  `research/runtime_contracts_paper/`, and
  `benchmarks/governed_agent_bench/`.
- **Active runtime**: `src/health_agent_infra/`.
- **Active docs**: `README.md`, `CHANGELOG.md`, `AGENTS.md`, `CLAUDE.md`,
  `ARCHITECTURE.md`, `AUDIT.md`, `HYPOTHESES.md`, `ROADMAP.md`,
  `SECURITY.md`, `CITATION.cff`, `CONTRIBUTING.md`, `REPO_MAP.md`,
  current docs directly under `reporting/docs/`
  (including `agent_cli_contract.md` — generated from `hai
  capabilities --json`; `current_system_state.md` is the current-truth
  summary),
  `reporting/plans/README.md` (HAI planning-tree reading-order index),
  `reporting/plans/post_v0_1_18/strategic_plan_v2.md` (HAI
  reference-runtime strategy before the research reframe),
  `reporting/plans/tactical_plan_v0_1_x.md` (HAI runtime backlog,
  with shipped-history sections that should be read as provenance),
  `reporting/plans/eval_strategy/`, `reporting/plans/success_framework_v1.md`,
  `reporting/plans/risks_and_open_questions.md`, and the current/future
  cycle workspaces, and between-cycle notes.
- **SUPERSEDED 2026-04-27**: `reporting/plans/historical/multi_release_roadmap.md` —
  preserved as historical provenance; do not act on its release
  schedule. Use the strategic + tactical plans above.
- **Active proof**:
  `reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/`.
- **Active tests + evals**: `verification/tests/`, `verification/evals/`,
  `verification/dogfood/` (the persona harness, NEW v0.1.10) — the
  packaged eval runner lives at `src/health_agent_infra/evals/`;
  `verification/evals/` retains dev-reference docs and the skill-harness
  pilot; `verification/dogfood/` drives synthetic personas through the
  full pipeline as permanent regression infrastructure.
- **Historical / archived (still on disk, clearly labelled)**:
  `reporting/docs/archive/doctrine/`,
  `reporting/docs/archive/cycle_artifacts/`,
  `reporting/docs/archive/merge_human_inputs/`,
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
