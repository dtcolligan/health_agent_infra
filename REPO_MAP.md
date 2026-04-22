# Repo map

One-page orientation: what every top-level entry is, what is current
versus historical, and where to look next. Pair with
[`README.md`](README.md) for the product story and
[`reporting/docs/tour.md`](reporting/docs/tour.md) for the 10-minute
guided read.

## Top-level entries

| Path | Class | What it is |
|---|---|---|
| [`src/`](src/health_agent_infra/) | active runtime | The `health_agent_infra` Python package: CLI, core orchestration, per-domain logic, packaged skills, packaged eval framework, the committed Garmin CSV fixture. This is the shipped wheel. |
| [`reporting/`](reporting/) | active docs + proof + plans + frozen prototypes | All non-runtime narrative material. See [`reporting/README.md`](reporting/README.md) for the four-subdir map. |
| [`safety/`](safety/) | active tests + active evals + legacy scripts | All test and eval material plus a small set of legacy scripts. See [`safety/README.md`](safety/README.md) for the layout, including the symlinks into local generated data. |
| [`merge_human_inputs/`](merge_human_inputs/) | docs + examples bucket (intentional historical anchor) | Not a Python module. Holds a README and example payloads for the human-input intake surface. The bucket name is preserved as a mental-model anchor from the original eight-bucket framing; the typed-intake logic itself is now an agent concern owned by the `merge-human-inputs` skill. See [`merge_human_inputs/README.md`](merge_human_inputs/README.md). |
| [`README.md`](README.md) | active docs | Product overview, install, CLI surface, repo layout, what's proven. |
| [`STATUS.md`](STATUS.md) | active docs | Current shipped phase, what's tested, what's deferred. |
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
  `safety/data` and `safety/artifacts` symlinks point at when present.
  See [`safety/README.md`](safety/README.md).

If `ls` shows one of these, it is a local artifact, not part of the
checked-in repo shape.

## Where to start reading

| You want to | Start at |
|---|---|
| Understand what the project is | [`README.md`](README.md) |
| Know what is shipped right now | [`STATUS.md`](STATUS.md) |
| Take the guided 10-minute tour | [`reporting/docs/tour.md`](reporting/docs/tour.md) |
| Read the architecture | [`reporting/docs/architecture.md`](reporting/docs/architecture.md) |
| See how `hai explain` works (three-state audit) | [`reporting/docs/explainability.md`](reporting/docs/explainability.md) |
| Read the agent CLI contract | [`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md) |
| Add runtime code or a skill | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| See the current-cycle plan (M8 agent-operable runtime) | [`reporting/plans/agent_operable_runtime_plan.md`](reporting/plans/agent_operable_runtime_plan.md) |
| See the prior cycle plan (post-v0.1) | [`reporting/plans/post_v0_1_roadmap.md`](reporting/plans/post_v0_1_roadmap.md) |
| Inspect proof / eval captures | [`reporting/artifacts/`](reporting/artifacts/) |
| See what was tried and discarded before v1 | [`reporting/experiments/`](reporting/experiments/) |

## Active vs historical at a glance

- **Active runtime**: `src/health_agent_infra/`.
- **Active docs**: `README.md`, `STATUS.md`, `CONTRIBUTING.md`,
  `REPO_MAP.md`, everything directly under `reporting/docs/`
  (including `agent_cli_contract.md` — generated from `hai
  capabilities --json`),
  `reporting/plans/agent_operable_runtime_plan.md` (the M8 cycle
  plan), `reporting/plans/post_v0_1_roadmap.md` (superseded but
  retained for historical context),
  `reporting/plans/launch_notes.md`,
  `reporting/plans/skill_harness_rfc.md`.
- **Active proof**:
  `reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/`.
- **Active tests + evals**: `safety/tests/`, `safety/evals/` (the
  packaged eval runner lives at `src/health_agent_infra/evals/`;
  `safety/evals/` retains dev-reference docs and the skill-harness
  pilot).
- **Historical / archived (still on disk, clearly labelled)**:
  `reporting/docs/archive/doctrine/`, `reporting/artifacts/archive/`,
  `reporting/artifacts/phase_0/`, `reporting/experiments/`,
  `reporting/plans/phase_0_findings.md`,
  `reporting/plans/phase_0_5_synthesis_prototype.md`,
  `reporting/plans/phase_2_5_retrieval_gate.md`,
  `reporting/plans/phase_2_5_independent_eval.md`,
  `safety/scripts/`.

If you find a path that is not classified above, treat it as
suspect and check git log before trusting it.
