PLAN_COHERENT_WITH_REVISIONS

### F-CDX-RFR-R2-01 — Runtime-mode naming drift reintroduced the old confusion [REGRESSION]

**Severity:** major
**Audit question:** A1, B5, E1, J1
**Where:** `project/DECISIONS.md`:295-313; `benchmark/governed_agent_bench/schema/trajectory.schema.json`:35-45; `benchmark/governed_agent_bench/schema/score.schema.json`:36-46; `benchmark/governed_agent_bench/schema/task.schema.json`:133-146; `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:55-75,103-110,121-141,536-549,572-576; `benchmark/governed_agent_bench/BENCHMARK_SPEC.md`:154-165; `research/runtime_contracts_paper/WORK_PACKETS.md`:1154-1170
**Finding:** The closeout renamed `no_runtime` to `no_runtime_enforcement` in the schemas and decisions, but the round-2 execution plan now says the mode previously named `no_runtime_enforcement` is renamed again to `no_runtime_enforcement_enforcement`. That string is not in any v2 schema. Separately, `BENCHMARK_SPEC.md` and `WP-MAN-004` still refer to the old `no_runtime` enum, and `BENCHMARK_SPEC.md` still says the v2 task fields are optional. This means a coding agent following the execution plan, the benchmark spec, or the schemas will recover different runtime-mode vocabularies.
**Suggested fix:** Declare the v2 schema enum as the single source of truth and normalize every active doc/packet to exactly `full_contract`, `no_validation`, `no_agent_safe`, `no_proposal_gate`, `no_refusal`, `no_audit_chain`, `no_runtime_enforcement`. Add a project or benchmark alignment test that fails on `no_runtime_enforcement_enforcement` and on bare `no_runtime` outside explicit historical prose.
**Provenance check:** I compared D-PROJ-017, all three schema enums, the execution plan, `BENCHMARK_SPEC.md`, and `WP-MAN-004`; the strings do not match.

### F-CDX-RFR-R2-02 — Supersession notes sit on top of still-active prompt-first bodies [ROUND-1 RESIDUAL]

**Severity:** major
**Audit question:** A3, H1, J1, J3
**Where:** `research/runtime_contracts_paper/PAPER_FRAME.md`:6-17,104-133; `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`:12-18,68-83,147-164; `research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md`:6-15,154-188,190-206; `research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md`:8-12,112-185,223-236; `project/OPERATING_MODEL.md`:6-12,81-102; `project/ROADMAP.md`:6-12,51-65,70-80,93-104; `project/HYPOTHESES.md`:41-62,77-98; `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`:90-104; `research/runtime_contracts_paper/DRAFT_PAPER.md`:92-97,286-329,341-349
**Finding:** The closeout says the 11 docs were tombstoned and body content made consistent, but several bodies still contain operative prompt-first instructions. `PAPER_FRAME.md` still lists manifest-grounded prompting and prompt-only baselines as a contribution and empirical tier. `RESEARCH_EVAL_STRATEGY.md` still lists "no manifest" and "stale manifest" as scaffold ablations and says fine-tuning should be evaluated with and without live manifest retrieval. `PROJECT_EXECUTION_PLAN.md`, `IMPLEMENTATION_PLAN.md`, `OPERATING_MODEL.md`, and `ROADMAP.md` still instruct agents to run prompt-only/local+manifest/cloud+manifest comparisons. `OPERATOR_HARNESS_SPEC.md` still says trajectories carry experiment `condition` and `model_id`. `DRAFT_PAPER.md` was not tombstoned and still has prompt-axis conditions and result tables. Header notes are not enough; a cold agent can still follow the body sections and execute the old design.
**Suggested fix:** Rewrite the body sections, not just the front matter. If old content must be preserved, move it under an explicitly titled "Retired Pre-Reframe Design" appendix and keep active sections runtime-first. Add an alignment test that fails on old prompt-axis condition names and prompt-first result tables outside retired/historical blocks.
**Provenance check:** I read the supersession notes and the body sections of the tombstoned docs, then ran residual searches for prompt-first strings outside `hai/reporting/plans/`.

### F-CDX-RFR-R2-03 — Agent/user invocation classification has no harness owner

**Severity:** major
**Audit question:** C1, C2, C3, K1
**Where:** `research/runtime_contracts_paper/WORK_PACKETS.md`:682-708,732-747,1388-1400; `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:346-360; `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`:134-144
**Finding:** `WP-DISPATCH-001` makes M5 depend on `HAI_INVOCATION_CONTEXT=agent`, defaulting to `user` when unset so the maintainer's daily loop is unaffected. But no harness packet or harness spec owns setting `HAI_INVOCATION_CONTEXT=agent` for model-driven benchmark subprocesses; the current harness-mode packet only exports `HAI_RUNTIME_MODE`. If the harness forgets this env var, every model-backed benchmark run is classified as `user`, and dispatch-level `agent_safe` enforcement is effectively off while trajectories still claim `full_contract`.
**Suggested fix:** Add the invocation-context export to `WP-HARNESS-MODE-001` or create a dedicated harness-context packet. Acceptance should assert that every model-backed subprocess gets `HAI_INVOCATION_CONTEXT=agent`, rule baselines get a documented classification, and trajectories or run manifests record the classification. Also state explicitly whether Claude Code daily-driver HAI calls are intentionally classified as `user` unless Dom opts in.
**Provenance check:** I searched the repo for `HAI_INVOCATION_CONTEXT`; it appears only in `WP-DISPATCH-001` and the round-2 prompt, not in harness packets or benchmark specs.

### F-CDX-RFR-R2-04 — Dangerous ablation modes are not runtime-gated to hermetic state [ROUND-1 RESIDUAL]

**Severity:** major
**Audit question:** D1, D2, K1
**Where:** `research/runtime_contracts_paper/WORK_PACKETS.md`:805-844,942-1016,1203-1250,1263-1326; `hai/src/health_agent_infra/cli/__init__.py`:1500-1512,2307-2314
**Finding:** `WP-REFUSE-002` says `no_agent_safe` ablation is hermetic-only, and its tests include "attempting the no_agent_safe ablation without HAI_HERMETIC=1 raises a clear error." But the packet does not bind that error to a runtime-side guard in `HAI_RUNTIME_MODE`; `WP-HRN-002` only says the harness rejects omitting `HAI_HERMETIC=1` while setting `HAI_STATE_DB`, and `WP-HRN-001` checks the inverse case (`HAI_HERMETIC=1` without redirection). `WP-RT-MODE-002` still says user audit-chain safety is verified via invented `HAI_STATE_PATH` redirection. There is also no `--dry-run` flag on `hai intent commit`; the only nearby `--dry-run` is on sync purge. As scoped, a user or test can set `HAI_RUNTIME_MODE=no_agent_safe` outside hermetic mode unless a future implementer invents an unscoped runtime guard.
**Suggested fix:** Make the runtime-mode accessor reject all mechanism-disabling modes unless `HAI_HERMETIC=1` and required state/base-dir redirection are present, before any handler can mutate state. Update `WP-RT-MODE-001/002`, `WP-REFUSE-002`, and `WP-HRN-*` to name that guard explicitly and remove the `hai intent commit --dry-run` example unless a separate `WP-RUNTIME-FIX-NNN` adds such a flag.
**Provenance check:** I read the three relevant packet sections and grepped the CLI parser for `--dry-run`; `intent commit` has `--confirm` but no `--dry-run`.

### F-CDX-RFR-R2-05 — `deployment_full_v1` cannot render against v1 or stale manifest snapshots

**Severity:** major
**Audit question:** F1, F2, F3, K1
**Where:** `benchmark/governed_agent_bench/prompts/deployment_full_v1.md`:15-20,58-86,101-108; `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:249-291,443-458; `research/runtime_contracts_paper/WORK_PACKETS.md`:1439-1449
**Finding:** The prompt template requires `refusals`, `mutation_classes`, and `exit_codes` top-level taxonomies from the manifest snapshot. Those taxonomies are Phase 3 deliverables and do not exist in today's `agent_cli_contract.v1` snapshot. The L7 drift plan explicitly says the stale snapshot validates against its era's v1 schema, while the prompt template has no v1 compatibility path. The template also says "Exactly four placeholders" but lists five placeholders. Without a compatibility rule, the harness cannot render `deployment_full_v1` for either current pre-Phase-3 work or v0.1.18 stale-manifest drift tasks.
**Suggested fix:** Define one rendering contract: either every manifest snapshot envelope, including stale snapshots, is promoted with synthetic v2 taxonomy fields; or `deployment_full_v1` has an explicit v1 fallback; or L7 uses a distinct prompt template id. Also fix the placeholder count and distinguish template-file hash from rendered-prompt hash in the trajectory field description.
**Provenance check:** I read the prompt template, Phase 3 manifest-taxonomy deliverables, and Phase 7 drift acceptance criteria.

### F-CDX-RFR-R2-06 — Model-roster predeclaration still has no enforceable gate

**Severity:** major
**Audit question:** G1, G2, G3, K1
**Where:** `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:121-137; `research/runtime_contracts_paper/CLAIM_LADDER.md`:170-191,208-220; `benchmark/governed_agent_bench/schema/score.schema.json`:7-18,84-88; `benchmark/governed_agent_bench/model_roster.md` (missing)
**Finding:** The closeout names `model_roster.md` as deferred, but Tier 3 and Tier 4 depend on the roster being predeclared before model runs. There is no committed roster file, no packet that creates it, no roster hash in score or trajectory artifacts, and no exact Tier 4 curve-shift metric beyond an example. `scorer_config_hash` anchors thresholds, not the evaluated model grid. This leaves the roster-selection-bias issue only procedurally asserted; it is still possible to author the roster after partial runs and claim it was predeclared.
**Suggested fix:** Add `WP-MODEL-ROSTER-001` before any model-adapter or model-run packet. It should create `benchmark/governed_agent_bench/model_roster.md`, define the Tier 4 curve-shift metric exactly, and require a `model_roster_hash` in the run manifest or score artifact before model-backed trajectories are accepted.
**Provenance check:** I verified `model_roster.md` is absent and searched active docs/schemas for model-roster hash or an executable roster-authoring packet.

## No-Finding Notes

- The Draft 2020-12 conditional structure in the trajectory and score schemas is syntactically sound: the `if` clauses include the relevant `required` fields, and top-level `model_class` is required before the `else` branch can matter. The schema-contract tests are structural rather than instance-validation tests; that is worth hardening, but I did not count it as a separate finding because the schemas themselves express the intended constraints.
- The schema-contract suite does contain 13 `def test_...` functions, with no `skip` or `xfail` markers found by search.
- The HAI source paths cited by the rewritten `MECHANISM_INVENTORY.md` exist on disk, including `core/validate.py`, `core/writeback/proposal.py`, `cli/handlers/intent.py`, `core/synthesis.py`, `core/state/store.py`, `core/paths.py`, `core/demo/session.py`, and `verification/tests/contract/test_audit_chain_integrity.py`.
- I found no modified files under `hai/reporting/plans/`; the historical plans still appear to be treated as provenance rather than active closeout targets.
