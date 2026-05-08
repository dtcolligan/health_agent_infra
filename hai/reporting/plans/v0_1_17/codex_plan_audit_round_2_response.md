# Codex Plan Audit Response — v0.1.17 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS — W-D arm-2, W-AH-2 eval-corpus gate, W-29 abort branch, CLI-snapshot lockstep, and LOC provenance need named revisions before cycle open.

**Round:** 2

## Round-1 closure verdicts (per F-PLAN-NN)

| Round-1 finding | Round-2 verdict | Note |
|---|---|---|
| F-PLAN-01 (W-D arm-2 plumbing+formula) | CLOSED_WITH_RESIDUAL | Formula and hydration scope are corrected, but the revised plumbing still names the wrong production call surface and the linear override test passes a partial threshold tree that the current D13 seam does not accept. See F-PLAN-R2-01. |
| F-PLAN-02 (scenario contract) | CLOSED | §2.C and §2.E now use `expected.classified`, `expected.policy.forced_action` / `fired_rule_ids`, and singular `tag`, matching `evals/runner.py`. Old `expected_*_token`, `expected_escalate_token`, and `tags[]` claims are retired except as historical "does not add" prose. |
| F-PLAN-03 (persona vs eval-corpus gate) | CLOSED_WITH_RESIDUAL | The mechanism is corrected from persona matrix to `hai eval run --scenario-set all`, but the new ≥95% pass-rate gate is not executable against the current CLI contract. See F-PLAN-R2-02. |
| F-PLAN-04 (W-AI-2 sequencing) | CLOSED | Commit gate is dynamic over the at-commit corpus; ship gate is end-of-cycle visibility. The separation is clear. |
| F-PLAN-05 (W-29 pre-flight gate) | CLOSED_WITH_RESIDUAL | The refreshed-boundary note is now a real gate, but the `do-not-split` fork-defer branch is not operational against v0.1.18 and the W-29 release-blocker/AGENTS.md closure claims. See F-PLAN-R2-03. |
| F-PLAN-06 (W-29 dest coverage) | CLOSED | `test_cli_handler_dispatch_smoke.py` closes the parser `dest` blind spot. "One non-default flag per moved handler group" is enough; the specific flags can be implementer-selected from the refreshed boundary note. |
| F-PLAN-07 (snapshot lockstep) | CLOSED_WITH_RESIDUAL | §3 and §6 now state per-CLI-surface lockstep, but §2.D / §2.G / §2.H do not carry the local acceptance gates consistently. See F-PLAN-R2-04. |
| F-PLAN-08 (source-doc refresh) | CLOSED_WITH_RESIDUAL | README line 3 and line 13 are refreshed and `wc -l src/health_agent_infra/cli.py` returns 9927. Tactical LOC provenance still has a stale/ambiguous 9217 baseline. See F-PLAN-R2-05. |
| F-PLAN-09 (W-B agent_safe) | CLOSED | `agent_safe=False`, single-valued `source='user_authored'`, and the explicit "no agent-proposal path" wording resolve the contradiction. The CHECK constraint is acceptable belt-and-braces for v1. |
| F-PLAN-10 (AGENTS.md provenance) | CLOSED | §3 now says append the W-29 closure sentence and remove only the cli.py lead clause from "Do Not Do"; this preserves the current AGENTS.md redestination chain and W-30 tail. |
| F-PLAN-11 (D15 tier sentence) | CLOSED | PLAN line 3 now quotes D15's `≥1 release-blocker workstream` and `≥10 days estimated` criteria correctly. The residual round-1 audit-trail sentence is useful, not blocking. |

## Round-2 findings (new — second-order)

### F-PLAN-R2-01. W-D arm-2 still lacks an executable threshold-plumbing contract

**Q-bucket:** QR2-1  
**Severity:** dependency-error / acceptance-criterion-weak  
**Reference:** PLAN.md §2.I lines 403-407, 415, 447; `src/health_agent_infra/core/state/snapshot.py:897-909`; `src/health_agent_infra/domains/nutrition/classify.py:327,361-373`; `src/health_agent_infra/core/config.py:321-373`

**Argument:** The round-1 formula bug is fixed, but the new plumbing path is still not executable as written.

The production path does not classify nutrition inside `cmd_synthesize` / `cmd_state_snapshot`. `build_snapshot()` computes the W-A presence block and calls `classify_nutrition_state(nutrition_signals)` directly in `core/state/snapshot.py:897-909`. PLAN §2.I files-of-record omit `core/state/snapshot.py`, and line 415 also places `cmd_state_snapshot` under `cli/handlers/recommend.py`; the v0.1.13 boundary table puts `cmd_state_snapshot` in `cli/handlers/state.py`. A CLI-handler-only edit would miss the actual classifier call unless the PLAN also changes the `build_snapshot()` API or the snapshot internals.

The threshold override acceptance is also malformed. `classify_nutrition_state()` treats a non-None `thresholds` argument as the full threshold tree (`t = thresholds`) and then indexes `t["classify"]["nutrition"]["targets"]`. PLAN §2.I item 5 passes only `{"classify": {"nutrition": {"projection_mode": "linear_extrapolation"}}}`. That omits `targets`, `calorie_balance_band`, `protein_sufficiency_band`, and `hydration_band`; the current seam will KeyError before reaching a projection branch. `DEFAULT_THRESHOLDS` has no `projection_mode` leaf today, so "reachable without a code change" is not accurate.

**Recommended response:** Revise §2.I to name `core/state/snapshot.py` as the production plumbing file of record, or explicitly add a `build_snapshot(..., thresholds=...)` / `build_snapshot(..., nutrition_thresholds=...)` API change. State that active macro targets are deep-merged into a full `load_thresholds()` tree under `classify.nutrition.targets`, not passed as a flat or partial dict. Add a default `classify.nutrition.projection_mode = "target_anchored"` leaf or make item 5 pass a full merged threshold tree. Correct the handler file mapping for `cmd_state_snapshot`.

### F-PLAN-R2-02. The ≥95% eval-corpus gate is not supported by `hai eval run`

**Q-bucket:** QR2-2  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.C line 192, §6 lines 552 and 570; `src/health_agent_infra/evals/cli.py:68-97,141-158`

**Argument:** The revised gate says `hai eval run --scenario-set all` returns a ≥95% pass-rate. The current CLI does not expose that contract. `cmd_eval_run()` returns OK only when `failed == 0`; any failed scenario returns `USER_INPUT`. `_run_all_scenario_sets()` runs each domain and synthesis set sequentially and returns the first non-zero status; it does not compute one aggregate numerator/denominator. With `--json`, it prints one payload per sub-run rather than a single aggregate object.

So the proposed 95% gate cannot pass through the current command: 94%, 95%, and 99% with any failure all return non-zero, while 100% is the only OK path. The PLAN also does not cite a v0.1.14 full-corpus pass-rate baseline, so 95% is not anchored to a known existing floor.

**Recommended response:** Either make the gate match the current executable contract (`hai eval run --scenario-set all` returns OK / 100% pass after W-AH-2) or add a scoped implementation item for an aggregate summary mode/test helper that computes pass-rate and intentionally accepts ≥95%. If the 95% tolerance stays, cite the baseline and name how failures can be named-deferred without violating §2.C item 1's per-domain count floor.

### F-PLAN-R2-03. The W-29 `do-not-split` fork-defer branch breaks downstream cycle assumptions

**Q-bucket:** QR2-4  
**Severity:** plan-incoherence / hidden-coupling  
**Reference:** PLAN.md §2.A line 126, §4 risk 1 line 495, §7 line 606; `reporting/plans/v0_1_18/README.md:57-60`; PLAN.md §3 lines 480-481 and §6 lines 561-565

**Argument:** The new abort path has two branches: halt and re-shape, or convert W-29 to `fork-deferred -> v0.1.18+ W-29-3` while Phase 2 + Phase 3 ship without W-29. The second branch is not operational as written.

v0.1.18 explicitly hard-depends on v0.1.17 closing with the W-29 cli.py split in tree before W-OB-2 touches the `hai init` handler. PLAN §7 repeats that dependency. If W-29 slips while Phase 2/3 ship, v0.1.18 cannot open as currently scoped; the downstream cycle and tactical row need a reshape.

The branch also conflicts with this PLAN's own closure surfaces. W-29 is the only release-blocker, §6 has W-29-specific release-blocker gates, and §3's AGENTS.md edits append "W-29 closed" and retire the cli.py-split "Do Not Do" clause. If v0.1.17 ships without W-29, those edits cannot happen and the tier / ship claim / downstream dependency text all change.

**Recommended response:** Make `do-not-split` a true cycle halt unless and until PLAN.md is re-authored. If the maintainer wants the "ship Phase 2/3 without W-29" branch, spell out the required re-authoring: remove W-29 as release-blocker, remove §3 W-29 closure and cli.py-clause retirement, revise §6 gates, update README/tactical/v0.1.18 dependency text, and assign an explicit destination cycle for W-29-3.

### F-PLAN-R2-04. Snapshot lockstep is not propagated into the CLI-surface workstream gates

**Q-bucket:** QR2-5  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §3 line 484, §6 lines 549-550; §2.D lines 222-228; §2.G lines 313-319; §2.H lines 372-379

**Argument:** §3 and §6 now state the correct lockstep rule: every intentional CLI-surface commit regenerates the manifest snapshot, parser-tree snapshot, and markdown contract in the same commit. But the three CLI-surface workstreams do not all carry that rule locally.

W-AI-2 acceptance item 5 names the capabilities manifest annotation but not snapshot regeneration. F-PV14-02 item 5 names `hai capabilities --markdown` only, not the JSON snapshot or parser-tree snapshot. W-B acceptance has the manifest annotation but no snapshot or markdown regeneration item. A final ship gate would catch the mismatch eventually, but F-PLAN-07's point was commit-local lockstep, and the per-W-id acceptance lists are what implementers execute.

**Recommended response:** Add an acceptance item to §2.D, §2.G, and §2.H: the W-id commit regenerates `verification/tests/snapshots/cli_capabilities_v0_1_13.json`, `verification/tests/snapshots/cli_help_tree_v0_1_13.txt`, and `reporting/docs/agent_cli_contract.md` in the same commit as the CLI change. F-PV14-02's existing markdown-only item should be expanded rather than left as a partial duplicate.

### F-PLAN-R2-05. LOC provenance still mixes the 8891 and 9217 baselines

**Q-bucket:** QR2-6 / QR2-10  
**Severity:** provenance-gap  
**Reference:** PLAN.md §2.A line 122; `reporting/plans/tactical_plan_v0_1_x.md:49,703`; `reporting/docs/archive/cycle_artifacts/cli_boundary_table.md:55`; `reporting/plans/v0_1_14/RELEASE_PROOF.md:25`

**Argument:** The README refresh is correct: line 13 cites 9927 LOC, and `wc -l src/health_agent_infra/cli.py` returns 9927. PLAN §2.A also correctly uses 8891 as the v0.1.13 W-29-prep boundary-table baseline.

The tactical plan still creates a provenance mismatch. §5D row 703 says "was 9217 LOC at v0.1.13 W-29-prep"; the boundary-table doc says W-29-prep measured 8891 LOC. 9217 is the v0.1.14 RELEASE_PROOF deferred W-29 baseline, not the W-29-prep boundary-audit baseline. The top tactical cycle table also still describes v0.1.17 as "W-29 cli.py 9217-line mechanical split" at line 49. Without a dual-baseline note, the source docs look contradictory.

**Recommended response:** Revise tactical §5D row 703 to say either "8891 LOC at v0.1.13 W-29-prep" or "9217 LOC at v0.1.14 RELEASE_PROOF/v0.1.15 carry-forward baseline." Update the tactical top row to 9927. Optionally add one sentence to PLAN §2.A distinguishing the two historical baselines: 8891 for the archived boundary table, 9217 for the v0.1.14 deferred-release-proof snapshot.

## Open-question dispositions

**OQ-1 — `hai sync` handler-group placement:** Agree with the revised default: start with `state.py`, but let the W-29 refreshed boundary note choose `sync.py` if `state.py` is conceptually muddy or near the LOC ceiling.

**OQ-5 — W-D arm-2 projection-function default:** Do not ratify until F-PLAN-R2-01 is fixed. The target-anchored default is semantically acceptable for v1 and hydration is honestly held observed, but the threshold/config path must be made executable before the default is settled.

**OQ-6 — W-AH-2 distribution:** Agree with 20 per domain + 12-15 synthesis after the harness-contract correction. The remaining issue is the eval-corpus gate: either require 100% under the existing CLI or implement a real aggregate ≥95% gate.

**OQ-8 — W-29 atomic commit vs series:** Agree with the 3-commit default. The per-commit acceptance wording is now clear enough for the split branch. The `do-not-split` branch still needs the downstream reshape called out in F-PLAN-R2-03.

## Closure recommendation

**Verdict:** PLAN_COHERENT_WITH_REVISIONS.

Must-fix before open:

1. F-PLAN-R2-01 — revise W-D arm-2 plumbing to name the actual snapshot/classifier call path and use a full merged threshold tree.
2. F-PLAN-R2-02 — make the eval-corpus gate executable: current CLI 100% OK path, or scoped aggregate ≥95% implementation with baseline.
3. F-PLAN-R2-03 — make the W-29 `do-not-split` branch a true re-authoring halt, or spell out all downstream edits needed to ship without W-29.
4. F-PLAN-R2-04 — add local snapshot/markdown regeneration acceptance items to W-AI-2, F-PV14-02, and W-B.
5. F-PLAN-R2-05 — repair the tactical LOC baseline wording and update the stale 9217 top-row summary.

Round-2 produced 5 findings, which matches the expected halving shape. Recommended next step: apply the revisions and run a narrow D14 round 3 focused only on the five findings above plus a quick stale-status/citation sweep. Budget: 0.5 session.
