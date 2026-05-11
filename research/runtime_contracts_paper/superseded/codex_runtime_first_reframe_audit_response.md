PLAN_INCOHERENT

### F-CDX-RFR-R1-01 — Active docs still teach the superseded prompt-first experiment

**Severity:** critical
**Audit question:** C3, E1, E2, E3, E4, E5, E6, J1, J2
**Where:** `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:19-25; `research/runtime_contracts_paper/PAPER_FRAME.md`:90-119; `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`:36-67,134-148; `research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md`:142-176; `research/runtime_contracts_paper/BASELINES_AND_ABLATIONS_PLAN.md`:15-44; `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`:33-45,128-139; `project/OPERATING_MODEL.md`:72-93; `project/HYPOTHESES.md`:13-40; `project/ROADMAP.md`:42-59; `README.md`:71-79
**Finding:** The reframe says the new execution document supersedes implicit prompt-first ordering, but the repo's active planning and benchmark docs still define the experiment as prompt-only versus manifest/contract prompting. This is not a harmless historical residue: `PAPER_FRAME.md` still frames the contribution around prompt-only baselines and manifest-grounded prompting; `RESEARCH_EVAL_STRATEGY.md` and `OPERATOR_HARNESS_SPEC.md` list `local_prompt_only`, `local_manifest`, `cloud_prompt_only`, and `cloud_manifest` as systems; `PROJECT_EXECUTION_PLAN.md` Milestones M3-M4 still require prompt-only and contract prompt templates; `BASELINES_AND_ABLATIONS_PLAN.md` still says each ablation changes one prompt/context feature. A future cold session can execute the old design and still appear to be following canonical docs.
**Suggested fix:** Update or explicitly tombstone the active prompt-first docs in the same reframe packet before any downstream implementation packet runs. At minimum, add dated supersession front matter to `PAPER_FRAME.md`, `RESEARCH_EVAL_STRATEGY.md`, `PROJECT_EXECUTION_PLAN.md`, `BASELINES_AND_ABLATIONS_PLAN.md`, and `OPERATOR_HARNESS_SPEC.md`, then replace their system tables with `runtime_mode x model_class` language.
**Provenance check:** I read the cited files on disk and verified the old condition names and prompt-only comparison language with `rg` and line-numbered file reads.

### F-CDX-RFR-R1-02 — The manifest v2 work violates the scheduled capabilities-manifest freeze

**Severity:** critical
**Audit question:** F5
**Where:** `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:185-227,443-448; `research/runtime_contracts_paper/WORK_PACKETS.md`:947-958; `AGENTS.md`:160-204,552-566; `project/DECISIONS.md`:7-9
**Finding:** Phase 3 plans a `agent_cli_contract.v2` manifest schema bump with new top-level taxonomies and explicit mechanism coverage, while `AGENTS.md` says not to freeze or mutate the capabilities-manifest schema before the scheduled v0.2.3 cycle. `project/DECISIONS.md` explicitly says project decisions do not replace AGENTS invariants. This makes the reframe unsafe to execute as written: the paper plan asks agents to do work the repo governance currently forbids.
**Suggested fix:** Keep HAI's product manifest at `agent_cli_contract.v1` for the frozen snapshot and put paper-only mechanism taxonomy in a benchmark-side snapshot envelope. If the maintainer really wants to change the HAI manifest schema before v0.2.3, that needs a new explicit governance decision before any WP-MAN packet is executable.
**Provenance check:** I verified the Phase 3 schema-bump language, the WP-MAN-006 output, and the AGENTS "Do Not Do" section forbidding premature capabilities-manifest schema freeze.

### F-CDX-RFR-R1-03 — The HAI product freeze is not authoritative on disk

**Severity:** major
**Audit question:** E5, J4
**Where:** `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:458-473; `project/DECISIONS.md`:13-29,233-297; `project/ROADMAP.md`:61-70; `hai/docs/current_system_state.md`:183-190
**Finding:** The prompt asserts that HAI is frozen as of 2026-05-08, that v0.2.0 is the reference snapshot, and that there is no v0.2.1 cycle. The authoritative on-disk decisions added by the reframe are D-PROJ-013 through D-PROJ-015, and they cover runtime-first evaluation, prompt constancy, and schema split; they do not record the product freeze/no-v0.2.1 rule. Meanwhile active docs still mention a v0.2.1 insight-ledger cycle and v0.2.3 capabilities-manifest schema freeze as future HAI support work. This leaves the freeze dependent on chat or memory, not the filesystem.
**Suggested fix:** Add an explicit on-disk project decision for the HAI freeze/no-release-ladder rule and update active roadmap/state docs to point HAI runtime defects through `WP-RUNTIME-FIX-NNN` only. Do not rely on the memory-side decision record for a rule this central.
**Provenance check:** I checked `project/DECISIONS.md` for D-PROJ-013..015 and verified that the freeze/no-v0.2.1 rule is not one of those decision records.

### F-CDX-RFR-R1-04 — `no_runtime` is a misnamed, confounded condition

**Severity:** major
**Audit question:** C2, G2
**Where:** `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:44-61,268-305; `benchmark/governed_agent_bench/schema/trajectory.schema.json`:35-45; `benchmark/governed_agent_bench/schema/score.schema.json`:35-45; `benchmark/governed_agent_bench/BENCHMARK_SPEC.md`:159-162
**Finding:** The plan defines `no_runtime` as "M4-M8 off" while M1 command envelope, M2 structured actions, and M3 harness allowlist remain on in every condition. That is not "no runtime"; it is "no HAI runtime enforcement beyond the harness envelope." A hostile reviewer can correctly say the baseline is still scaffolded by command parsing and allowlist enforcement, so the score gap cannot be attributed to the full runtime versus no runtime.
**Suggested fix:** Rename the enum to something like `no_runtime_enforcement` or `no_hai_enforcement_m4_m8`, and explicitly state that M1-M3 are held-constant harness infrastructure. If the intended baseline really disables M1-M3, then M1-M3 need schema support, task coverage, and separate ablations.
**Provenance check:** I verified the runtime_mode enums in both v2 schemas and the execution doc's statement that M1-M3 are always on.

### F-CDX-RFR-R1-05 — The constant "deployment_full" prompt is not specified tightly enough to reproduce

**Severity:** major
**Audit question:** C1
**Where:** `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:65-80,268-283; `project/DECISIONS.md`:255-275; `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`:33-45
**Finding:** The headline experiment depends on holding a "deployment-realistic full information" prompt constant, but the exact prompt artifact, included manifest fields, safety text, refusal wording, ordering, and hash are not specified on disk. The old operator-harness spec still describes prompt-only versus contract prompts, so two future benchmark runs could both claim `deployment_full` while using materially different instructions.
**Suggested fix:** Add a versioned prompt-template artifact and require every trajectory or run manifest to record its template id/hash, manifest snapshot id, and included runtime notes. Until that exists, the runtime-first claim is under-controlled.
**Provenance check:** I searched for the old prompt-condition names and read the new execution plan and operator harness spec; I found no exact `deployment_full` prompt template.

### F-CDX-RFR-R1-06 — Predeclared thresholds are asserted, not enforced

**Severity:** major
**Audit question:** A3
**Where:** `research/runtime_contracts_paper/CLAIM_LADDER.md`:30-40,82-109,141-170; `benchmark/governed_agent_bench/schema/score.schema.json`:64-94; `benchmark/governed_agent_bench/SCORING_SPEC.md`:120-124
**Finding:** Tier 1 and Tier 3 rely on frozen thresholds, but the score schema makes `scorer_config_hash` optional and allows per-metric `threshold` to be absent or null. `SCORING_SPEC.md` says thresholds should be recorded and not changed after results without versioning, but the schemas and tests do not enforce that discipline. That makes Tier 3 weakly falsifiable: the maintainer could pick lenient thresholds or move the smallest model definition after exploratory runs and still pass the schema.
**Suggested fix:** Require a committed scorer config hash and threshold references for all primary pass/fail metrics before any model run. Add schema/tests that reject benchmark scores for primary metrics without thresholds and record the threshold-config commit or immutable digest in every score.
**Provenance check:** I verified the `CLAIM_LADDER.md` threshold requirements, the optional score schema fields, and the scoring spec's threshold policy.

### F-CDX-RFR-R1-07 — The model-scale claim cannot be audited from the current schema

**Severity:** major
**Audit question:** C4, C5
**Where:** `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:82-92; `research/runtime_contracts_paper/CLAIM_LADDER.md`:141-192; `benchmark/governed_agent_bench/schema/trajectory.schema.json`:31-55; `benchmark/governed_agent_bench/schema/score.schema.json`:31-55
**Finding:** Tier 3 and Tier 4 need model-size comparisons, but the v2 schemas only encode broad `model_class` values (`local`, `cloud`, `fine_tuned_local`, `rule_baseline`) and optional free-form `model_id`. They do not encode parameter count, model family, quantization, provider snapshot, decoding settings, or a predeclared roster. Without those controls, a "small full_contract beats large no_runtime" result is vulnerable to model-selection and base-quality attacks.
**Suggested fix:** Add a benchmark run manifest or schema fields for predeclared model roster, parameter count, provider/version snapshot, quantization, context window, and decoding settings. Report a normalized "smallest model meeting threshold" only across a predeclared grid.
**Provenance check:** I read the schema enum definitions and the execution/claim ladder text that names local 1B/3B/7B/13B and cloud classes.

### F-CDX-RFR-R1-08 — M7 refusal is not purely aspirational in the current runtime

**Severity:** major
**Audit question:** B2
**Where:** `research/runtime_contracts_paper/MECHANISM_INVENTORY.md`:86-108; `hai/src/health_agent_infra/core/validate.py`:105-129,163-256,352-439; `hai/src/health_agent_infra/core/writeback/proposal.py`:121-270; `hai/src/health_agent_infra/skills/safety/README.md`:1-23; `hai/verification/tests/test_synthesis_safety_closure.py`:680-884
**Finding:** The inventory says a runtime-owned refusal seam does not exist and rates M7 as aspirational. That overstates the gap. HAI already has runtime-side validators that reject banned clinical tokens and shape violations for recommendations and proposal payloads, and the safety skill README points back to proposal/recommendation validators as the enforcement surface. What appears missing is a final-output refusal envelope for clinical advice, not all refusal-in-code.
**Suggested fix:** Split M7 into current runtime text/payload safety validation and future final-response refusal. Inventory the current validators as real mechanisms, then decide whether the benchmark needs a new final-output refusal seam or should treat existing validation as part of M4/M7.
**Provenance check:** I verified the banned-token validators, proposal validation code, safety skill README, and tests that exercise clinical-token rejection.

### F-CDX-RFR-R1-09 — M5 `agent_safe` is not a general runtime enforcement mechanism

**Severity:** major
**Audit question:** B3, B5
**Where:** `hai/docs/hai_reference_runtime.md`:57-63,330-333; `hai/src/health_agent_infra/cli/handlers/intent.py`:180-246; `hai/src/health_agent_infra/cli/handlers/target.py`:168-235; `hai/src/health_agent_infra/cli/handlers/intake.py`:1184-1189; `hai/src/health_agent_infra/cli/__init__.py`:1508-1547,1655-1694,2100-2125,2274-2323
**Finding:** The docs present `agent_safe=false` as mechanically enforced, but the source shows enforcement is concentrated in W57 intent/target commit/archive gates. Other commands are annotated `agent_safe=False` in the CLI manifest while the handler comments say the runtime trusts the manifest or expects the agent not to invoke them. That means an ablation called `no_agent_safe` is not disabling one central mechanism; it is partly disabling W57 gates and partly disabling an external harness/manifest convention.
**Suggested fix:** Either build and test a central dispatch-level `agent_safe` enforcement seam before treating M5 as ablatable, or narrow M5's definition to the W57 user-gate mechanism and remove unsupported claims about general `agent_safe=false` enforcement.
**Provenance check:** I checked the CLI parser annotations and handler implementations for intent, target, intake weight, and sync purge paths.

### F-CDX-RFR-R1-10 — M5 and M6 are not independently meaningful on the write path yet

**Severity:** major
**Audit question:** B3
**Where:** `research/runtime_contracts_paper/MECHANISM_INVENTORY.md`:55-85,134-146; `hai/src/health_agent_infra/cli/handlers/intent.py`:180-246; `hai/src/health_agent_infra/cli/handlers/target.py`:168-295; `hai/docs/runtime_contract_overview.md`:21-30,128-157; `hai/docs/architecture.md`:393-417
**Finding:** The reframe treats `agent_safe` and `proposal_gate` as separate ablations, but on the user-gated commit path they are functionally entangled. The current W57 commit/archive enforcement prevents autonomous promotion of proposed intent/target rows; target nutrition ingestion uses agent actors to create proposed rather than active rows; commit/archive then go through the same user gate. Turning off `agent_safe` can make the proposal gate irrelevant for the critical mutation, and turning off the proposal gate requires changing source/status semantics that are tied to user authority.
**Suggested fix:** Phase 1 must either prove a real decoupling seam with tests or merge M5/M6 into a single write-authority mechanism for headline evidence. Do not claim independent mechanism ranking until the code has independent switches.
**Provenance check:** I traced the W57 user gate and target agent actor source/status handling in the CLI handlers and compared them to the inventory's provisional coupling graph.

### F-CDX-RFR-R1-11 — `HAI_STATE_PATH` is not an existing isolation boundary and would miss global state

**Severity:** major
**Audit question:** B4
**Where:** `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:229-266; `research/runtime_contracts_paper/WORK_PACKETS.md`:984-999; `hai/src/health_agent_infra/core/state/store.py`:26-61; `hai/src/health_agent_infra/core/paths.py`:25-59; `hai/src/health_agent_infra/core/config.py`:664-686,834-852; `hai/src/health_agent_infra/core/pull/auth.py`:3-9; `hai/src/health_agent_infra/core/demo/session.py`:1-36,202-335
**Finding:** The plan assumes `HAI_STATE_PATH` redirection is enough to isolate benchmark audit-chain writes. HAI does not currently use `HAI_STATE_PATH`; it uses `HAI_STATE_DB` for the SQLite DB, `HAI_BASE_DIR` for file-backed state, platform config paths for thresholds/config, and keyring/env for credentials. There is an existing demo marker mechanism that isolates DB, base dir, and config, but the plan does not name it. As written, benchmark-mode audit-chain disabling can still touch user config or auth surfaces even if the DB is redirected.
**Suggested fix:** Define a hermetic benchmark environment in terms of existing resolvers (`HAI_STATE_DB`, `HAI_BASE_DIR`, config path/marker, no network/auth) or introduce `HAI_STATE_PATH` as a tested umbrella over all of them. Treat keyring, config, and pull credentials as explicit non-write surfaces in hermetic mode.
**Provenance check:** I verified the resolver environment variables and the demo session marker implementation in HAI source.

### F-CDX-RFR-R1-12 — The v2 schemas do not encode the invariants the spec says are mandatory

**Severity:** major
**Audit question:** D2, D3, D4
**Where:** `benchmark/governed_agent_bench/BENCHMARK_SPEC.md`:64-95,154-168; `benchmark/governed_agent_bench/schema/task.schema.json`:7-18,117-147; `benchmark/governed_agent_bench/schema/trajectory.schema.json`:62-102; `benchmark/governed_agent_bench/schema/score.schema.json`:95-130; `benchmark/verification/tests/test_governed_agent_bench_schema_contracts.py`:17-78
**Finding:** The benchmark spec says every MVP task must populate `load_bearing_mechanisms` and `runtime_modes_in_scope`, but the task schema makes both optional. The trajectory schema allows `step_type=mechanism_disabled` without a `mechanism`, and also allows `mechanism` on unrelated steps. The score schema allows `mechanism_disabled_unexpected` violations without a `mechanism`. The tests only check that fields exist and enums align, not that these invariants hold.
**Suggested fix:** Add JSON Schema conditionals or separate MVP-task schema checks: require load-bearing fields for benchmark tasks in scope, require `mechanism` when `step_type == mechanism_disabled`, and require `mechanism` for `mechanism_disabled_unexpected` violations. Add negative tests for all three failures.
**Provenance check:** I compared the spec language, schemas, and schema-contract tests line by line.

### F-CDX-RFR-R1-13 — `harness_allowlist` leaks a held-constant mechanism into task load-bearing coverage

**Severity:** major
**Audit question:** B5, D1
**Where:** `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:29-61; `benchmark/governed_agent_bench/schema/task.schema.json`:117-130; `benchmark/governed_agent_bench/schema/trajectory.schema.json`:93-101; `benchmark/governed_agent_bench/schema/score.schema.json`:115-129
**Finding:** The task schema's `load_bearing_mechanisms` enum includes `harness_allowlist`, while trajectory and score mechanism enums only include M4-M8. The execution plan says M3 harness allowlist is held constant and not part of the runtime axis. A task can therefore declare a load-bearing mechanism that has no runtime-mode ablation and cannot be represented in `mechanism_disabled` steps or violation records.
**Suggested fix:** Remove `harness_allowlist` from `load_bearing_mechanisms` for v2, or split task metadata into `held_constant_controls` and `ablatable_mechanisms`. Do not mix M3 into the M4-M8 ablation coverage rule.
**Provenance check:** I verified the enum values in all three v2 schemas and the execution doc's M1-M3 held-constant definition.

### F-CDX-RFR-R1-14 — Reframe work packets are not template-complete

**Severity:** major
**Audit question:** F1, F3
**Where:** `project/OPERATING_MODEL.md`:156-172; `research/runtime_contracts_paper/WORK_PACKETS.md`:17-32,699-757,893-910,960-999,1020-1025,1090-1127
**Finding:** The packet template requires explicit inputs, outputs, allowed files, forbidden files, dependencies, acceptance criteria, tests, manual review, and non-goals. Several new reframe packets do not meet that bar. Examples: `WP-MAN-003` has only goal/output/dependencies; `WP-HRN-001` and `WP-HRN-002` omit several required sections; `WP-FIX-002` through `WP-FIX-006` are placeholders; the docs-alignment packets are summarized without the full execution contract. `WP-INV-001` is better structured, but still leaves ambiguous rating decisions (`coupled` versus `aspirational`) to the implementing agent without a decision rule.
**Suggested fix:** Expand every active packet to the full template before assignment. Move placeholders to a future backlog section that is clearly not executable. Add a rating rubric for `WP-INV-001`: if the current product code cannot be toggled without creating new runtime code, the rating is `aspirational`; if it can be toggled only by touching shared state or another mechanism, it is `coupled`.
**Provenance check:** I read the packet template and sampled the new reframe packets against each required section.

### F-CDX-RFR-R1-15 — Packet dependencies are internally inconsistent

**Severity:** major
**Audit question:** F2, F4
**Where:** `research/runtime_contracts_paper/WORK_PACKETS.md`:79-108,699-757,859-958
**Finding:** The dependency graph is not clean enough for parallel execution. `WP-HAI-001` says runtime work is blocked by the manifest packets, but its `Dependencies` field only says "Planning Gate complete." `WP-MAN-001` and `WP-MAN-002` have no dependencies even though Phase 3 is downstream of Phase 2 runtime-mode/refusal decisions in the execution plan. `WP-MAN-006` depends on `WP-MAN-001..005`, making the manifest series a transitive chain rather than six independent packets. This is not necessarily wrong, but the packet metadata currently hides the chain.
**Suggested fix:** Rewrite the WP-MAN graph explicitly. A defensible chain is `WP-INV-001 -> Phase 2 runtime seams -> WP-MAN-001/002 -> WP-MAN-003/004/005 -> WP-MAN-006 -> WP-HAI-001`. If a packet can run in parallel, state the exact stable inputs that make that true.
**Provenance check:** I read the packet dependency fields and compared them to the execution plan's phase ordering.

### F-CDX-RFR-R1-16 — The `no_agent_safe` acceptance test asks for a W57 violation

**Severity:** major
**Audit question:** F5
**Where:** `research/runtime_contracts_paper/WORK_PACKETS.md`:811-825; `AGENTS.md`:137-158,540-548; `hai/src/health_agent_infra/cli/handlers/intent.py`:180-246
**Finding:** `WP-REFUSE-002` says autonomous invocation of `hai intent commit` should be refused under `full_contract` but succeed with a `mechanism_disabled` marker under `no_agent_safe`. That is exactly the W57 invariant AGENTS says must remain load-bearing: only the user may promote intent/target proposals. Even if this is meant to happen only in a hermetic benchmark, the packet as written normalizes a product-invariant violation as acceptance criteria.
**Suggested fix:** State that `no_agent_safe` success is only permitted inside hermetic benchmark mode and can never run against user state, or use a non-mutating fixture/dry-run path to prove the marker behavior. The packet must not ask a coding agent to make autonomous real-state commits succeed.
**Provenance check:** I verified the W57 invariant in AGENTS and the current intent commit user gate in the CLI handler.

### F-CDX-RFR-R1-17 — Tier 5 reintroduces the prompt-axis experiment the reframe dropped

**Severity:** major
**Audit question:** A4, C4, G3
**Where:** `research/runtime_contracts_paper/CLAIM_LADDER.md`:194-215,235-246; `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:94-102,458-473,512-523; `research/runtime_contracts_paper/WORK_PACKETS.md`:1175-1195
**Finding:** Tier 5 is framed as a fine-tuned local model "with live manifest/context" versus the same model "without manifest access." That is the prompt/context ablation the reframe says is no longer a headline experiment. The execution plan also defers fine-tuning, but the claim ladder still keeps Tier 5 as the top of the same ladder and the future packet list does not preserve a concrete fine-tuning data-generation packet. This leaves the workshop floor ambiguous: either fine-tuning is truly deferred, or the plan has quietly preserved the old manifest-axis experiment at the top tier.
**Suggested fix:** Move Tier 5 to a clearly separate future defense-in-depth appendix, or rewrite it as a runtime-first fine-tuning question with the prompt still held constant. If preserving optionality matters, author a dormant packet now for dataset generation and preregistration, but mark it out of scope for the current workshop floor.
**Provenance check:** I read the Tier 5 claim text, the execution plan's "not varied" and deferral sections, and the future-packet placeholders.

### F-CDX-RFR-R1-18 — The risk register and calendar omit known first-order risks

**Severity:** major
**Audit question:** G1, G2, G3, G4, H1, H2, H3
**Where:** `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:480-510; `AGENTS.md`:241-271; `project/OPERATING_MODEL.md`:156-172
**Finding:** The plan names five risks and estimates 9-12 weeks, but it omits API/model drift, reproducibility across machines, schema forward-compatibility once public, review/audit rounds, and the cost of discovering extensive mechanism coupling in Phase 1. The critical path is also longer than the plan admits: inventory -> runtime switches/refusal -> manifest snapshot -> hermetic harness -> prompt template -> load-bearing tasks -> scorer/runs -> paper artifacts. AGENTS already records the empirical 10 -> 5 -> 3 -> 0 audit-settling shape, yet the calendar does not budget 2-4 weeks for plan-audit loops.
**Suggested fix:** Add a calendar section with explicit review-round buffer and a failure plan for "Phase 1 finds extensive coupling." Reorder scope cuts by implementation dependency, not by conceptual niceness: cutting aspirational final-output refusal or collapsing M5/M6 may be cheaper than cutting audit-chain ablation after the harness has already been built around audit markers.
**Provenance check:** I read the risk profile, calendar-honesty section, and AGENTS planning-audit guidance.

### F-CDX-RFR-R1-19 — M8 audit-chain ablation ignores transaction integrity as a separate mechanism

**Severity:** major
**Audit question:** B1, B5, I1
**Where:** `research/runtime_contracts_paper/MECHANISM_INVENTORY.md`:110-132,148-156; `hai/src/health_agent_infra/core/synthesis.py`:5-22,767-844,1061-1076,1137-1279; `hai/src/health_agent_infra/core/state/projector.py`:2183-2502; `hai/verification/tests/contract/test_audit_chain_integrity.py`:11-20,44-118,208-323
**Finding:** The inventory treats audit-chain as one mechanism and leaves state DB transaction integrity out of scope, but HAI's write safety is not just evidence references. `run_synthesis` validates before the transaction, uses an exclusive transaction, rolls back on failure, writes daily plans, recommendation logs, rule firings, planned recommendations, evidence cards, and proposal links as one graph; the audit-chain tests verify referential integrity across that graph. Disabling "audit_chain" without separately protecting transaction atomicity can corrupt the very safety property the benchmark is trying to observe.
**Suggested fix:** Add transaction integrity as a held-constant mechanism or a separate non-ablatable runtime invariant. If it becomes ablatable, it deserves its own mechanism id and fixtures; if it is held constant, `no_audit_chain` must be defined narrowly as disabling evidence-reference requirements/consumption, not atomic state graph writes.
**Provenance check:** I traced `run_synthesis`, projector writes, and the audit-chain integrity contract tests in HAI source.

### F-CDX-RFR-R1-20 — The claim ladder still contains stale prompt-only wording

**Severity:** minor
**Audit question:** A2
**Where:** `research/runtime_contracts_paper/CLAIM_LADDER.md`:19-29,82-109,111-139
**Finding:** The ladder's "core operational form" still says the system is compared with "prompt-only operation." That wording is no longer true for the headline experiment, which compares runtime modes with full prompt information held constant. The tier guardrails are otherwise stricter than the old plan, but this sentence gives the paper permission to slide back into prompt-only language.
**Suggested fix:** Replace "prompt-only operation" with "the same prompt/model under weaker runtime enforcement" and add a forbidden-phrasing guard for "prompt-only baseline" in Tier 1/Tier 2 unless it is explicitly labeled as future defense-in-depth.
**Provenance check:** I read the claim ladder and compared its core-question language to D-PROJ-013 and D-PROJ-014 in `project/DECISIONS.md`.

## Search Results And Closing Observations

Old condition names remain in active benchmark docs: `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`:133-138 lists `local_prompt_only`, `local_manifest`, `cloud_prompt_only`, `cloud_manifest`, and `fine_tuned_local_manifest`. The new execution document also mentions the old names at `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`:439-441, but that use is intentional historical/drop language.

Prompt-only and no-manifest language remains broadly distributed in active docs, including `README.md`:71-79, `project/OPERATING_MODEL.md`:72-93, `project/HYPOTHESES.md`:13-40, `project/ROADMAP.md`:42-59, `research/runtime_contracts_paper/PAPER_FRAME.md`:90-119, `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`:36-67,134-148, `research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md`:105-124,164-179,216-234, `research/runtime_contracts_paper/BASELINES_AND_ABLATIONS_PLAN.md`:15-44, and `benchmark/governed_agent_bench/baselines/README.md`:9-14.

I found no active references to `governed_agent_bench.trajectory.v1`, `governed_agent_bench.score.v1`, or `governed_agent_bench.task.v1` in the repo search. The `agent_cli_contract.v1` references in HAI docs are a separate manifest-version issue, not a GovernedAgentBench schema-version issue.

Historical `hai/reporting/plans/` files mostly function as provenance, but they still reinforce the scheduled v0.2.3 capabilities-manifest freeze. Examples include `hai/reporting/plans/tactical_plan_v0_1_x.md`:55 and `hai/reporting/plans/v0_2_0/README.md`:114. Those historical docs should not be rewritten casually, but active docs need enough front-matter to prevent a future session from treating old prompt-first and manifest-freeze planning as current paper execution guidance.

---

## Closure Status (annotated 2026-05-11, framing-v2 doc alignment)

This audit was authored against the pre-merge runtime-first reframe.
On 2026-05-11, the project completed the framing-v2 orchestration:
Phase 1 closed all paper-framing decisions (D-FRAME-001..027 in
`research/runtime_contracts_paper/framing_v2/CONVERGED.md`); Phase 2
documentation alignment batches 1-6 propagated the locked framing
across paper-planning files, benchmark spec + schemas, project
cold-start docs, HAI runtime docs (light touch), operating contracts
(AGENTS.md / CLAUDE.md / README.md), and historical-provenance
supersession headers.

The 20 findings below are closed against that merged framing:

| Finding | Severity | Closure | Provenance |
|---|---|---|---|
| F-CDX-RFR-R1-01 (prompt-first residue in active docs) | critical | **Closed** | Phase 2 batches 1+2+3+5. PAPER_FRAME / RESEARCH_EVAL_STRATEGY / PROJECT_EXECUTION_PLAN / BASELINES_AND_ABLATIONS_PLAN / HAI_PAPER_READINESS_EXECUTION rewritten in batch 1; OPERATOR_HARNESS_SPEC + baselines/README in batch 2; project/OPERATING_MODEL + HYPOTHESES + ROADMAP in batch 3; README.md in batch 5. Prompt-axis framing replaced with `runtime_mode × model_class` per D-FRAME-007 + D-FRAME-026. |
| F-CDX-RFR-R1-02 (manifest v2 violates v0.2.3 freeze) | critical | **Superseded** | D-PROJ-016 (HAI frozen 2026-05-08) retires the v0.2.3 release ladder entirely; the v0.2.3 capabilities-manifest freeze entry in AGENTS.md "Settled Decisions" is now historical. Paper-side schema work lives in GovernedAgentBench schemas, not HAI capabilities manifest. AGENTS.md "Do Not Do" entry on premature manifest freeze was retired by D-PROJ-016 + D-PROJ-017. |
| F-CDX-RFR-R1-03 (HAI freeze not authoritative on disk) | major | **Closed** | Phase 2 batch 3 appended D-PROJ-018..023 to `project/DECISIONS.md`; D-PROJ-016 freeze is now referenced from multiple cold-start docs. project/ROADMAP.md updated to route HAI runtime defects through WP-RUNTIME-FIX-NNN only; hai/docs/current_system_state.md batch-4-updated to mark v0.2.1 insight-ledger row superseded by D-PROJ-016. |
| F-CDX-RFR-R1-04 (`no_runtime` misnamed) | major | **Closed** | Phase 2 batch 2 schema work. `runtime_mode` enum now uses `no_runtime_enforcement` (not `no_runtime`); the seven enum values are `full_contract / no_validation / no_agent_safe / no_proposal_gate / no_refusal / no_audit_chain / no_runtime_enforcement`. M1-M3 explicitly held constant per D-FRAME-017 mechanism inventory. Verified in trajectory.schema.json and task.schema.json `load_bearing_mechanisms` description ("Held-constant harness controls M1-M3 are not part of this enum"). |
| F-CDX-RFR-R1-05 (deployment_full prompt not specified) | major | **Closed** | The prompt artifact exists on disk at `benchmark/governed_agent_bench/prompts/deployment_full_v1.md` (committed at `caad0b8 feat(benchmark): add deployment prompt rendering`). The file specifies: 5 named substitutions + 2-hash discipline (file-hash + rendered-hash) + manifest-shape promotion rule + byte-frozen stability commitment + reproducibility rules. Phase 2 batch 2 OPERATOR_HARNESS_SPEC.md documents the template name + hash discipline. **No carry-over needed.** |
| F-CDX-RFR-R1-06 (predeclared thresholds not enforced) | major | **Closed** | Phase 2 batch 2 schema tightening. `score.schema.json` now requires `scorer_config_hash` at top level (line 16); per-metric `threshold` is required in per-metric required arrays (lines 109, 117-119); `claim_tier` is required at top level (per F-AUDIT-4-04 audit closure); T3/T4 conditional requires `model_roster_hash` (lines 180-184). SCORING_SPEC.md batch 2 added AND-pass rule + 7 critical violations + per-metric threshold table per D-FRAME-021. 15/15 schema-contract tests pass. **Pre-pilot polish drafted:** `benchmark/governed_agent_bench/scorer_config.paper_v1.json` drafted 2026-05-11 with status `"draft"`; maintainer must compute SHA-256 + freeze before paper-claim runs. |
| F-CDX-RFR-R1-07 (model-scale claim unauditable) | major | **Closed** | Phase 2 batch 2 schema tightening. trajectory.schema.json now requires `model_identity` for non-`rule_baseline` trajectories (allOf entry: `if model_class != rule_baseline then required: [model_identity]`); model_identity structure has `model_family / parameter_count / quantization / provider_snapshot / decoding_settings`. D-FRAME-020 locks the 6 Houdinis + 3 Guards roster with all required fields. **Pre-pilot polish drafted:** `benchmark/governed_agent_bench/model_roster.md` drafted 2026-05-11 with status `"draft"`; maintainer must verify against live vendor docs + compute SHA-256 + freeze before paper-claim runs. |
| F-CDX-RFR-R1-08 (M7 refusal not purely aspirational) | major | **Closed** | Phase 1 round 3 audit verified M7 seam exists in `core/refusal/clinical.py:20-50, 110-166` (evaluate_clinical_output + enforce_clinical_output) + recommendation validation at `core/validate.py:109-115, 231-239`. D-FRAME-017 reframes M7 as narrow clinical-boundary refusal (JSON exempt per F-AUDIT-3-03). Phase 2 batches 1+2 propagated the narrowed scope. Original finding's "purely aspirational" framing was stale. |
| F-CDX-RFR-R1-09 (M5 not general runtime enforcement) | major | **Closed** | Phase 1 round 3 audit verified M5 seam exists: `_agent_safe_gate` at `cli/__init__.py:3181-3227` is a dispatch-time mechanism; `enforce_agent_safe_invocation` at `core/refusal/agent_safe.py:76-141`. D-FRAME-017 treats M5 as a real dispatch-level mechanism. D-FRAME-022 attack policy includes refusal-bypass (vs M7) and mutation-escalation (vs M5+M6) as separate trajectory types. Original finding was source-accurate at the time but stale post the runtime-first work. |
| F-CDX-RFR-R1-10 (M5 + M6 not independently meaningful) | major | **Closed** | Phase 1 round 3 audit verified M5/M6 separability with invocation-context discipline. Phase 2 batch 2 OPERATOR_HARNESS_SPEC.md documents `HAI_INVOCATION_CONTEXT` discipline per attack trajectory (line 153+) and adaptive-vs-DRG-0 30-attempt protocol. D-FRAME-022 keeps M5 and M6 as separate attack targets (mutation-escalation tests M5+M6 combined, but invocation context separates which mechanism fires). |
| F-CDX-RFR-R1-11 (HAI_STATE_PATH not an isolation boundary) | major | **Closed** | Phase 2 batch 2 OPERATOR_HARNESS_SPEC.md documents hermetic-mode requirements. Per round 3 audit, `core/runtime_mode.py:95-108` `require_runtime_mode_allowed` hermetic guard exists. **Carry-over to pre-pilot execution:** validate the hermetic-mode resolver list (HAI_STATE_DB + HAI_BASE_DIR + config path + no network/auth) is implemented end-to-end before §7-§8 runs against synthetic fixtures. |
| F-CDX-RFR-R1-12 (v2 schemas don't encode mandatory invariants) | major | **Closed** | Phase 2 batch 2 schema tightening. `load_bearing_mechanisms` + `runtime_modes_in_scope` are now required in task.schema.json. trajectory steps require `mechanism` when `step_type == mechanism_disabled`; score violations require `mechanism` for `mechanism_disabled_unexpected` (per batch 2 EDITS_SUMMARY). 15/15 schema-contract tests pass independently. |
| F-CDX-RFR-R1-13 (harness_allowlist leaks held-constant mechanism) | major | **Closed** | Phase 2 batch 2 schema tightening. task.schema.json `load_bearing_mechanisms` description now explicitly says "Mechanisms enumerated here MUST appear in the trajectory/score mechanism enum (M4-M8). Held-constant harness controls (M1-M3) are not part of this enum." `harness_allowlist` is treated as held-constant per D-FRAME-017 M9-TX style separation. |
| F-CDX-RFR-R1-14 (work packets not template-complete) | major | **Partially closed; carry-over** | Phase 2 batch 1 revised WORK_PACKETS.md (~365 diff lines) adding Phase 2 batches + DRG + Engels + HS + Audit packets. **Carry-over to a dedicated packet-template-completeness sub-batch OR pre-pilot work-packet hardening pass:** verify every active packet (especially WP-MAN-003, WP-HRN-001/002, WP-FIX-002..006) meets the full template (inputs/outputs/allowed/forbidden/deps/acceptance/tests/manual-review/non-goals) before assignment. |
| F-CDX-RFR-R1-15 (packet dependencies inconsistent) | major | **Partially closed; carry-over** | Phase 2 batch 1 revised WORK_PACKETS.md dependencies. **Carry-over:** explicit dependency-graph review pass needed before packet assignment, especially WP-MAN-* chain documented as transitive rather than independent. Same sub-batch as F-14. |
| F-CDX-RFR-R1-16 (`no_agent_safe` acceptance asks for W57 violation) | major | **Closed** | Phase 2 batch 2 OPERATOR_HARNESS_SPEC.md documents that non-`full_contract` runtime modes require hermetic fixture state per `core/runtime_mode.py:95-108`. D-FRAME-022 attack-policy table makes hermetic-fixture-only adjudication explicit for mutation-escalation trajectories. WP-REFUSE-002 (if still in WORK_PACKETS.md) is now scoped to hermetic benchmark mode only. |
| F-CDX-RFR-R1-17 (Tier 5 reintroduces prompt-axis) | major | **Closed** | Phase 2 batch 1 CLAIM_LADDER.md rewritten. D-FRAME-027 (Paper 2 = S1 fine-tuning of bounded operators) reframes the fine-tuning question as scale-substitution-after-runtime-floor, NOT as prompt-axis. Paper 1 keeps `fine_tuned_local` as a schema slot (D-FRAME-027 req 2) but the ladder explicitly marks it as future-work-only with no performance claims in paper 1. |
| F-CDX-RFR-R1-18 (risk register + calendar omit first-order risks) | major | **Closed** | Phase 2 batch 3 project/ROADMAP.md updated with merged-paper calendar including Sonnet 4 retirement binding (2026-06-15) + pilot decision gate (Aug 2026). framing_v2/CONVERGED.md captures the empirical settling shapes (4-round D14, 3-round IR) and the escape-valve pattern (3 consecutive SHIP_WITH_NOTES with 0 paper-§-level findings). Phase 2 batch 5 added the framing-v2 orchestration pattern to AGENTS.md "Patterns the cycles have validated." Scope-cut precommit lives in D-FRAME-011 (pilot null-result revert) + D-FRAME-024 (HS cap-miss demotion). |
| F-CDX-RFR-R1-19 (M8 audit-chain ignores transaction integrity) | major | **Closed** | Phase 1 round 3 D-FRAME-017 explicitly renamed M8 to "audit evidence emission" and added M9-TX (transaction integrity) as a held-constant non-ablatable mechanism. Phase 2 batches 1+2+5 propagated the M8 rename + M9-TX held-constant designation across PAPER_FRAME, CLAIM_LADDER, BASELINES_AND_ABLATIONS_PLAN, RESEARCH_EVAL_STRATEGY, BENCHMARK_SPEC, SCORING_SPEC, and AGENTS.md "Settled Decisions" D22. |
| F-CDX-RFR-R1-20 (claim ladder stale prompt-only wording) | minor | **Closed** | Phase 2 batch 1 CLAIM_LADDER.md rewritten. The "prompt-only operation" framing is retired; the new core-question language is "the same prompt held constant under weaker runtime enforcement." Forbidden-phrasing discipline in CLAIM_LADDER acceptance prose. |

### Carry-over to pre-pilot execution (not blocking Phase 2)

Three execution-side artifacts need to be committed before §7-§8
paper-claim runs but are NOT doc-alignment items:

- **F-CDX-RFR-R1-05 residual:** commit `benchmark/governed_agent_bench/prompts/deployment_full_v1.md`.
- **F-CDX-RFR-R1-06 residual:** commit `benchmark/governed_agent_bench/scorer_config.paper_v1.json`.
- **F-CDX-RFR-R1-07 residual:** commit `benchmark/governed_agent_bench/model_roster.md` with frozen D-FRAME-020 roster + May 2026 pricing snapshot date.

Plus one Phase 2 carry-over needing a dedicated test-alignment
sub-batch OR rolling into the final audit:

- **Stale tests:** `project/tests/test_project_reframe_docs_alignment.py` has 2 tests
  asserting pre-reframe strings ("HAI Paper-Readiness Engineering",
  pre-framing-v2 title) that the merged-paper framing intentionally
  retired. Not blocking; the assertions need updating to reflect the
  merged framing.

Plus packet-template completeness (F-CDX-RFR-R1-14 + F-CDX-RFR-R1-15
partial closures) which is a WORK_PACKETS.md hardening pass.

### Phase 2 batch closure log

| Batch | Files | Lines | Status |
|---|---|---|---|
| 1 — paper planning | 8 | +1,374 / -779 | Closed clean 2026-05-11 |
| 2 — benchmark spec + schemas | 6 named + 1 collateral | +372 / -64 | Closed clean; 15/15 schema-contract tests pass |
| 3 — project cold-start | 6 | +737 / -332 | Closed clean; A2/B1 sweep clean |
| 4 — HAI runtime docs (light) | 5 | +28 / -13 | Closed clean; HAI freeze honored |
| 5 — operating contracts | 3 | +268 / -94 | Closed clean; D19-D27 in AGENTS.md |
| 6 — historical provenance | 4 | +48 / -0 | Closed clean; supersession headers only |
| **Audit-findings-closure** | this file | +closure section | **Closed by this annotation 2026-05-11** |
