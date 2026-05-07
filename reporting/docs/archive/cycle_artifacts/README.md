# Cycle artifact archive

This folder holds documents that were authored for a specific release
cycle or implementation workstream. They remain useful provenance, but
they are not current operating contracts.

When these files disagree with current docs, prefer:

- [`../../../../docs/hai/current_system_state.md`](../../../../docs/hai/current_system_state.md)
- [`../../../../docs/hai/architecture.md`](../../../../docs/hai/architecture.md)
- [`../../../../docs/hai/agent_cli_contract.md`](../../../../docs/hai/agent_cli_contract.md)
- the live SQLite migrations under `src/health_agent_infra/core/state/migrations/`
- the generated capabilities manifest from `hai capabilities --json`

| File | Origin | Current replacement |
|---|---|---|
| `calibration_eval_design.md` | v0.1.14 W-AL eval schema staging | Future eval-cycle PLAN / current eval docs |
| `cli_boundary_table.md` | v0.1.13 W-29-prep split plan | `docs/hai/agent_cli_contract.md` + future W-29 PLAN |
| `demo_flow.md` | v0.1.11 W-Z demo script | README quickstart + future demo rewrite |
| `explain_ux_review_2026_05.md` | v0.1.14 W-EXPLAIN-UX review | `docs/hai/explainability.md` + future explain pass |
| `onboarding_slo.md` | v0.1.13 W-AA target | `docs/hai/current_system_state.md` + release proofs |
| `source_row_provenance.md` | v0.1.14 W-PROV-1 design note | `docs/hai/state_model_v1.md` + future weekly-review docs |
| `supersede_domain_coverage.md` | v0.1.12 W-FBC design note | current synthesis tests and `docs/hai/state_model_v1.md` |
