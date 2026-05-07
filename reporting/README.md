# reporting/

HAI reference-runtime narrative material. The runtime itself lives in
[`../src/health_agent_infra/`](../src/health_agent_infra/); nothing
under `reporting/` is imported by the package.

Project-wide research framing now lives outside this tree:
[`../PROJECT_FRAME.md`](../PROJECT_FRAME.md),
[`../research/runtime_contracts_paper/`](../research/runtime_contracts_paper/),
and [`../benchmarks/governed_agent_bench/`](../benchmarks/governed_agent_bench/).
Use `reporting/` for HAI runtime docs, release proof, and historical
planning provenance.

This directory has four subdirectories, each with a distinct role.

## Subdirectories

| Path | Class | Role |
|---|---|---|
| [`docs/`](docs/) | active HAI docs (with `archive/` for pre-rebuild doctrine) | HAI reference-runtime documentation: operator manual, current system state, architecture, x-rules, non-goals, state model, tour, extension paths, positioning, query taxonomy, memory model, explainability, grounded-expert scope. Start at [`docs/README.md`](docs/README.md). |
| [`artifacts/`](artifacts/) | active proof + archived bundles | The sole canonical checked-in proof root. Active proof is the multi-domain eval capture under `flagship_loop_proof/`; older single-domain bundles live under `archive/`; the Phase 0 preflight capture is preserved under `phase_0/`. See [`artifacts/README.md`](artifacts/README.md). |
| [`plans/`](plans/) | mixed HAI strategy + release history + historical archive | HAI runtime strategic/tactical docs, per-cycle audit folders (`v0_1_*`, `v0_2_*`), historical superseded docs under `historical/`, and deep strategy reviews under dated subdirs. See [`plans/README.md`](plans/README.md). |
| [`experiments/`](experiments/) | historical / archived prototypes | Throwaway prototypes from Phase 0.5 and Phase 2.5 that decided whether to commit to specific architectural bets. Frozen as proof of those decisions; **not** living code. See [`experiments/README.md`](experiments/README.md). |

## Active vs historical inside `plans/`

| File / dir | Status |
|---|---|
| [`plans/post_v0_1_18/strategic_plan_v2.md`](plans/post_v0_1_18/strategic_plan_v2.md) | HAI reference-runtime strategy before the research reframe |
| [`plans/strategic_plan_v1.md`](plans/strategic_plan_v1.md) | superseded — preserved as v2 source evidence |
| [`plans/tactical_plan_v0_1_x.md`](plans/tactical_plan_v0_1_x.md) | HAI runtime backlog and release history |
| [`plans/eval_strategy/v1.md`](plans/eval_strategy/v1.md) | active — how correctness is measured |
| [`plans/success_framework_v1.md`](plans/success_framework_v1.md) | active — how project value is measured |
| [`plans/risks_and_open_questions.md`](plans/risks_and_open_questions.md) | active — what could derail + decisions needed |
| [`plans/v0_1_15/`](plans/v0_1_15/) | frozen — package release, published 2026-05-03. |
| [`plans/v0_1_15_1/`](plans/v0_1_15_1/) | frozen — latest hotfix cycle (Linux keyring fall-through, 2026-05-03). |
| [`plans/v0_1_16/`](plans/v0_1_16/) | frozen — cancelled 2026-05-04. |
| [`plans/v0_1_17/`](plans/v0_1_17/) | frozen — maintainability + eval consolidation, shipped 2026-05-05. |
| [`plans/post_v0_1_10/`](plans/post_v0_1_10/) | historical — between-cycles handoff (demo + Phase 4 audit plans) |
| [`plans/post_v0_1_13/`](plans/post_v0_1_13/) | active — post-v0.1.13 strategic research + audit chain + 5 CPs |
| [`plans/post_v0_1_14/`](plans/post_v0_1_14/) | active — post-v0.1.14 carry-over findings (F-PV14-01/02 → v0.1.15) |
| [`plans/post_v0_1_15/`](plans/post_v0_1_15/) | active — post-v0.1.15 internal-docs audit and between-cycle notes |
| [`plans/future_strategy_2026-04-29/`](plans/future_strategy_2026-04-29/) | historical — Claude/Codex deep strategy review + reconciliation |
| [`plans/historical/`](plans/historical/) | superseded — 9 pre-2026-04-27 planning docs (multi_release_roadmap, post_v0_1_roadmap, agent_operable_runtime_plan, launch_notes, skill_harness_rfc, phase_0_*, phase_2_5_*). Provenance only. |
| [`plans/docs_overhaul/codex_review.md`](plans/docs_overhaul/codex_review.md) | historical — docs-overhaul review record |

Historical plan documents are kept on purpose: they explain *why* the
runtime has the shape it does (e.g. why nutrition is macros-only, why
synthesis is a single skill rather than a multi-agent debate). Treat
them as decision history, not a backlog.

## What is intentionally not here

- No runtime code. Anything imported by the wheel lives under
  [`../src/health_agent_infra/`](../src/health_agent_infra/).
- No tests or evals. Those live under
  [`../verification/`](../verification/) (with the eval runner itself packaged
  inside the wheel at `src/health_agent_infra/evals/`).
- No generated outputs. The eval CSVs / SQLite DBs the runtime emits
  during local use go under the gitignored top-level `data/` and
  `artifacts/` directories, not here.
