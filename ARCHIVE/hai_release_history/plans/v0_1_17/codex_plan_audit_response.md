# Codex Plan Audit Response - v0.1.17 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS

**Round:** 1

## Findings

### F-PLAN-01. W-D arm-2 lacks target-value plumbing and its formula contradicts its acceptance tests

**Q-bucket:** Q4 / Q5 / Q8  
**Severity:** hidden-coupling / acceptance-criterion-weak  
**Reference:** PLAN.md §2.I, lines 388-418

**Argument:** W-D arm-2 is gated on W-A `is_partial_day` plus `target_status="present"` (PLAN.md:388-393), but the current W-A helper only returns the three-valued status; it does not return target values (`core/intake/presence.py:163-213`). The nutrition classifier currently reads calorie/protein/hydration targets from config defaults (`domains/nutrition/classify.py:361-393`), not from the `target` table, while PLAN acceptance asserts a seeded `target_kcal=3100` result (PLAN.md:415). That target value has no specified data path into the classifier or projection branch.

The provisional formula is also internally inconsistent. PLAN.md:403-410 defines:

```text
projected_eod_kcal = intake_so_far_kcal + (target_kcal - intake_so_far_kcal) * remaining_day_fraction_at_target_pace
remaining_day_fraction_at_target_pace = (target_kcal - intake_so_far_kcal) / target_kcal
```

For the named 1344/3100 case this yields about 2339 kcal, not 3100. Acceptance items 1 and 4 require `projected_eod_kcal == target_kcal` (PLAN.md:415, 418). Exact target calorie balance would classify as `met` under current thresholds (`config.py:333-345`, `classify.py:114-136`), but `nutrition_status="aligned"` still depends on protein/hydration bands (`classify.py:225-241`), and PLAN does not specify whether those are projected or seeded at target.

**Recommended response:** Revise §2.I before cycle open. Add a concrete target-value source contract: either W-A exposes active macro target values, or W-D arm-2 reads committed `target` rows directly, or the classifier receives explicit threshold overrides derived from target rows. Then define target-anchored projection as an executable formula that actually emits the asserted values, and state whether protein/carbs/fat/hydration are projected or held observed. Acceptance should assert both the target-row lookup and the projected classified fields, not only `nutrition_status`.

### F-PLAN-02. Scenario acceptance assumes fixture/harness fields that do not exist

**Q-bucket:** Q4 / Q5  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.C, lines 184-194; §2.E, lines 255-260

**Argument:** PLAN §2.C says new fixtures carry `tags` arrays and per-fixture `expected_*_token` assertions, and §2.E says W-AM-2 uses an `expected_escalate_token` field validated by the existing scenario-runner harness. Current scenario loading requires only `scenario_id`, `kind`, `description`, and `expected` (`evals/runner.py:71-86`). Current scoring reads `expected.classified` and `expected.policy` (`evals/runner.py:300-380`); it does not read `expected_*_token` or `expected_escalate_token`. Existing tagged fixtures use singular `"tag"`, not a `tags` array (`rec_004_should_escalate_compound_signals.json:35`, `run_004_should_escalate_acwr_max.json:25`).

This makes the acceptance surface weaker than stated: the planned fields can be authored without being evaluated unless W-AH-2/W-AM-2 also changes the harness, but PLAN.md:187 says the scenario-runner contract does not change.

**Recommended response:** Choose one shape and make it explicit. Either revise acceptance to the current executable contract (`expected.classified`, `expected.policy.forced_action`, `expected.policy.fired_rule_ids`, current `"tag"` field), or scope a small harness/schema update that validates `tags[]` and `expected_*_token` fields. If the latter is chosen, list the harness files and tests in §2.C/§2.E and include the migration of existing singular-tag fixtures.

### F-PLAN-03. W-AH-2's persona-matrix gate is not connected to the scenario corpus

**Q-bucket:** Q5 / Q7  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.C, line 194; §4 risk 7, line 477

**Argument:** W-AH-2 acceptance item 5 says "Persona-matrix replay against the post-W-AH-2 corpus" must catch regressions. The current persona runner drives isolated `hai` CLI workflows over persona specs (`verification/dogfood/runner.py:1-15`) and does not consume `src/health_agent_infra/evals/scenarios/`. Conversely, `hai eval run --scenario-set all` fans out domain+synthesis scenarios and explicitly skips judge-adversarial from "all" (`evals/cli.py:141-158`, `evals/cli.py:185-193`). The persona matrix is a valid release gate, but it will not mechanically catch a domain undershoot or broken scenario fixture caused by the W-AH-2 corpus expansion.

The same mismatch appears in risk 7: it estimates persona-matrix runtime growth from scenario corpus growth, but there is no current path where each persona runs the expanded eval corpus.

**Recommended response:** Replace the W-AH-2-specific persona-corpus gate with an eval-corpus gate: `hai eval run --scenario-set all` or equivalent per-domain test coverage after the expansion, plus `test_scenario_corpus_coverage.py` for counts. Keep the persona matrix as a standard substantive-cycle ship gate and runtime note, but do not claim it validates the scenario corpus unless the PLAN scopes a new persona-by-scenario replay harness.

### F-PLAN-04. W-AI-2 is sequenced as independent, but its acceptance depends on W-AH-2 and W-AM-2

**Q-bucket:** Q2 / Q5  
**Severity:** hidden-coupling  
**Reference:** PLAN.md §1.3, lines 69-72; §2.D, lines 221-222

**Argument:** PLAN §1.3 says W-AI-2 is mechanically independent of W-AH-2 and W-AM-2. Its first acceptance item, however, says `hai eval review list --corpus judge_adversarial` returns "the 31 judge_adversarial scenarios at HEAD + the post-W-AH-2 expansion + the W-AM-2 escalate fixtures" (PLAN.md:221-222). If W-AI-2 lands before W-AH-2/W-AM-2, a strict per-W-id acceptance test cannot pass as written. If the test is dynamic over the current corpus, then the phrase "post-W-AH-2 + W-AM-2" is a final ship gate, not W-AI-2's own commit gate.

**Recommended response:** Either sequence W-AI-2 after W-AH-2 and W-AM-2, or split the acceptance into two gates: W-AI-2 must list/filter/tag/export whatever corpus exists at its commit; the final §6 ship gate verifies that the completed W-AH-2/W-AM-2 additions appear in `hai eval review`.

### F-PLAN-05. W-29 pre-flight is named but not gated, and the abort path only covers LOC overflow

**Q-bucket:** Q2 / Q7  
**Severity:** acceptance-criterion-weak / absence  
**Reference:** PLAN.md §2.A, lines 122-129; §2.A acceptance, lines 130-146; §4 risk 1, line 465

**Argument:** PLAN §2.A correctly notices that the v0.1.13 boundary table is stale and tells the implementer to re-derive handler-group LOC before split commits. That step is not an acceptance item, does not name an artifact, and has no falsifiable trigger. The only explicit worst-case escalation is "if even the sub-split breaches 2500 LOC" (PLAN.md:465). The inherited boundary table also had a more fundamental `do-not-split` verdict for a wrong-shaped split, such as hidden shared state across handlers (`cli_boundary_table.md:228-236`). PLAN §2.A does not say what happens if the refreshed analysis finds that shape before any LOC ceiling is breached.

**Recommended response:** Add a W-29 acceptance/pre-flight gate that produces a refreshed boundary note or table before the split commit series starts: current command inventory, per-handler estimated LOC, shared-helper extraction list, contested groupings, and explicit `split` / `split-with-revisions` / `do-not-split` verdict. If the verdict is `do-not-split`, halt the cycle and revise PLAN.md through D14 before implementation.

### F-PLAN-06. W-29 byte-stability tests omit argparse `dest`, so a silent handler break can pass the named gate

**Q-bucket:** Q5  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.A acceptance, lines 132-134; `verification/tests/test_cli_parser_capabilities_regression.py`, lines 82-119 and 137-211

**Argument:** The existing parser-tree snapshot records only command paths and long flag names (`test_cli_parser_capabilities_regression.py:82-119`). The manifest walker records flag name, positional/required/type/choices/default/help/action/nargs/aliases, but not argparse `dest` for optional flags (`core/capabilities/walker.py:437-459`). A mechanical split could accidentally rename a flag's `dest` or handler namespace expectation while preserving the user-facing flag string and manifest shape. That would not be caught by acceptance items 2-4, and would only be caught if another command-specific test happens to execute that option.

**Recommended response:** Strengthen W-29 acceptance with either a W-29-only parser snapshot that includes `dest` for every action, or representative CLI smoke tests for each moved handler group using non-default flags. This does not need to change the public capabilities manifest schema; it can be an internal regression artifact.

### F-PLAN-07. Capabilities snapshot regeneration is both "lockstep" and "end of cycle"

**Q-bucket:** Q4 / Q5  
**Severity:** dependency-error  
**Reference:** PLAN.md §3, line 454; §6, line 519

**Argument:** The existing regression test compares the live manifest and parser tree to snapshot files on every pytest run (`test_cli_parser_capabilities_regression.py:137-172`, `:187-211`). PLAN §3 says intentional CLI additions regenerate the snapshot "in lockstep" (PLAN.md:454), but §6 says the snapshot is "regenerated against post-W-AI-2 + post-F-PV14-02 + post-W-B intentional adds at end of cycle" (PLAN.md:519). If W-AI-2, F-PV14-02, or W-B lands without the snapshot update in the same commit, the normal test gate is red until the end of the cycle.

**Recommended response:** Revise §6 to say each intentional CLI-surface commit updates the manifest/help-tree snapshots in the same commit (or in an immediately adjacent commit in the same W-id series). Preserve the W-29 gate as a pre-add comparison: W-29 must be byte-identical against the snapshot current at Phase 1 open; later intentional adds update the baseline as part of those W-ids.

### F-PLAN-08. Source-input docs cited by PLAN are stale on the v0.1.16 retirement and W-29 LOC

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md source inputs, lines 16 and 23; PLAN.md §9, lines 592-594

**Argument:** PLAN.md cites `v0_1_17/README.md` as the provisional catalogue and later says that README was updated to reflect precondition retirement and W-AH-2 honesty (PLAN.md:594). On disk, `v0_1_17/README.md:3` still says PLAN.md authors after v0.1.16 closes and v0.1.16 must absorb post-publish foreign-user findings. The same README still names W-29 as a 9217-line split (`README.md:13`), while `wc -l src/health_agent_infra/cli.py` returns 9927 and PLAN.md uses 9927. Tactical §5D also still says 9217 (`tactical_plan_v0_1_x.md:703`).

These stale source surfaces do not make the PLAN's own 9927 and no-precondition claims wrong, but they violate the provenance discipline AGENTS.md requires for cited planning surfaces.

**Recommended response:** Before open, either update `v0_1_17/README.md` and tactical §5D to the current 9927/no-v0.1.16-precondition wording, or revise PLAN.md to label those specific rows as historical/provisional and name the PLAN as the correcting source. The cleaner fix is a source-doc refresh.

### F-PLAN-09. W-B's provisional `agent_safe=True` conflicts with the "user-authored-only / block agents" default

**Q-bucket:** Q4 / Q6  
**Severity:** hidden-coupling  
**Reference:** PLAN.md §2.H, lines 342-343, 371, 380; AGENTS.md Governance Invariants, lines 104-106

**Argument:** PLAN §2.H's schema allows `source='agent_proposed'`, but the OQ-3 provisional default says no W57 gate, "User-authored-only," and "Agent invocations are blocked at the CLI layer if `--ingest-actor` resolves to an agent identifier" (PLAN.md:380). The acceptance item simultaneously sets the capabilities manifest to `agent_safe=True` (PLAN.md:371). If the command is agent-safe, a capable agent may invoke it; if the only block is a self-reported `--ingest-actor`, the agent can omit the flag and land through the default `cli` actor. If the command is truly user-authored-only, `agent_safe=True` is the wrong manifest annotation.

**Recommended response:** Resolve OQ-3 as a PLAN revision, not just an implementation-time choice. The simplest v1 shape is `agent_safe=False`, `source='user_authored'` only, and no `agent_proposed` enum until a commit path exists. If the maintainer wants agent invocation, add a real proposal/commit or trusted-actor mechanism and acceptance tests for it.

### F-PLAN-10. AGENTS.md closure edits would drop the W-29/W-30 provenance trail

**Q-bucket:** Q6  
**Severity:** settled-decision-conflict  
**Reference:** PLAN.md §3, lines 450-451; AGENTS.md, lines 137-162 and 438-449

**Argument:** The current AGENTS.md W29/W30 entry carries the full redestination chain: v0.1.12 CP1/CP2, v0.2.x CP-PATH-A/CP-W30-SPLIT, v0.1.14 -> v0.1.15, v0.1.15 -> v0.1.17, and the v0.1.16 cancellation insertion (`AGENTS.md:137-162`). PLAN §3 proposes replacing that with two short sentences. Likewise, the current "Do Not Do" entry includes a provenance tail for both cli.py split and W-30 freeze (`AGENTS.md:438-449`), while the proposed replacement is just "Do not freeze the capabilities manifest schema before its scheduled cycle (v0.2.3)."

The closure-side edit is directionally right, but as written it risks erasing the audit chain that justified why W-29 moved and why W-30 remains scheduled.

**Recommended response:** Revise §3 to say the ship-time AGENTS.md edit must preserve provenance. For Settled Decisions, append "W-29 closed at v0.1.17..." while retaining the W-30 v0.2.3 destination and origin chain. For Do Not Do, retire only the cli.py clause but keep the W-30 freeze prohibition plus its origin/destination provenance.

### F-PLAN-11. The D15 tier rationale is honest in outcome but misstates the threshold

**Q-bucket:** Q9  
**Severity:** nit  
**Reference:** PLAN.md first block, line 3; AGENTS.md D15, lines 233-236

**Argument:** The substantive tier is correct: W-29 is a release-blocker and the effort estimate is 25-40 days, either of which independently satisfies D15 (`AGENTS.md:233-236`). But PLAN.md line 3 says the catalogue has ">= 3 governance/state-model/audit-chain edits per AGENTS.md D15." D15 says ">=3 governance or audit-chain edits"; it does not count generic state-model changes as tier triggers. PLAN §3 has two direct AGENTS.md governance edits; W-30's test scaffold is not itself a governance edit.

**Recommended response:** Simplify the tier sentence to: substantive because W-29 is a release-blocker and estimated effort is >=10 days. Mention W-B schema/state-model and audit-chain doc edits as scope facts, not as the D15 threshold.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-29 | FIX | Needs a gated refreshed boundary table, stronger parser-dest coverage, and per-CLI-add snapshot sequencing. |
| W-30 | PASS | Test-only scaffold is in scope; do not count it as a governance edit. |
| W-AH-2 | FIX | Scenario fixture/harness contract and persona-matrix coupling need revision before open. |
| W-AI-2 | FIX | Acceptance depends on post-W-AH/W-AM corpus while sequencing says independent. |
| W-AM-2 | FIX | `expected_escalate_token`/tag contract does not match current runner/fixtures unless harness work is scoped. |
| W-Vb-4 | PASS | Scope and partial-closure naming are honest; document runtime, but do not tie it to scenario corpus unless a new harness exists. |
| F-PV14-02 | PASS | Source contract is encoded; snapshot update must land in the same CLI-surface commit. |
| W-B | FIX | Decide `agent_safe`/W57/user-authored-only semantics before open. |
| W-D arm-2 | FIX | Needs target-value plumbing and a corrected projection formula. |
| W-C-EQP | PASS | Source and acceptance match the named v0.1.15 IR residual. |

## Open questions for maintainer

**OQ-1 - `hai sync` handler placement:** Provisional `state.py` is acceptable, but decide after the W-29 refreshed boundary table. If state.py is near the LOC ceiling or conceptually muddy, use `sync.py`.

**OQ-2 - W-AI-2 persistence path:** Agree with user local state dir. A packaged data dir would be wrong for mutable per-user triage.

**OQ-3 - W-B W57/agent-safe shape:** Provisional default is wrong as written if it keeps `agent_safe=True`. Prefer `agent_safe=False`, user-authored-only v1, and no `agent_proposed` source until a commit/proposal path exists.

**OQ-4 - W-B same-day collision:** Agree with append. It matches measurement reality; list/latest semantics can be explicit.

**OQ-5 - W-D projection default:** Do not ratify until F-PLAN-01 is fixed. Target-anchored may be acceptable, but the formula must actually emit target and the plan must specify macro target-value plumbing.

**OQ-6 - W-AH-2 distribution:** 20/domain plus 12-15 synthesis is acceptable only after the harness/schema contract is corrected. The plan should require small-batch validation per v0.1.14 REPORT.md §5.3.

**OQ-7 - W-AM-2 mechanisation:** If the plan stays on the current `expected.policy` contract, no new helper is required. If it wants `expected_escalate_token`, then a small validation helper or harness extension should be scoped.

**OQ-8 - W-29 commit shape:** Prefer the 3-commit series for reviewability, but acceptance should be explicit about whether every stage must pass or only the final W-29 series must pass. Byte-stability is required at final W-29 closure before any intentional CLI additions.

## Closure recommendation

Verdict: **PLAN_COHERENT_WITH_REVISIONS**. Do not open Phase 0 until the PLAN revisions for F-PLAN-01 through F-PLAN-11 land, with F-PLAN-01 through F-PLAN-10 treated as must-fix and F-PLAN-11 as close-in-place.

Recommended next-round budget: one focused D14 round after revisions. Round 2 should re-check only the revised W-D arm-2 target/projection contract, W-AH/W-AM scenario harness wording, W-AI sequencing, W-29 pre-flight/snapshot gates, W-B agent-safe semantics, and AGENTS.md closure wording.

No tests were run for this audit, per the prompt's "No test runs" constraint. Evidence above is from source/document reads plus `wc -l`/directory listings.
