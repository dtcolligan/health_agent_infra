# Codex Plan Audit Response-Response — v0.1.17 PLAN.md, round 2

**Round:** 2
**Verdict (Codex):** PLAN_COHERENT_WITH_REVISIONS, **5 round-2 findings** (F-PLAN-R2-01..05); 6 of 11 round-1 findings CLOSED outright (F-PLAN-02 / F-PLAN-04 / F-PLAN-06 / F-PLAN-09 / F-PLAN-10 / F-PLAN-11); 5 CLOSED_WITH_RESIDUAL (F-PLAN-01 / F-PLAN-03 / F-PLAN-05 / F-PLAN-07 / F-PLAN-08) — the round-2 findings are the second-order followups for those 5.
**Halving signature:** **11 → 5** matches AGENTS.md empirical norm `10 → 5 → 3 → 0`. Round-3 prediction: 2-3 findings.
**Closure budget:** Codex recommended 0.5 session for round 3 — narrow scope, only the 5 R2 findings + a stale-status sweep.

**Triage summary.** All 5 round-2 findings AGREED. Zero rejected, zero partial, zero deferred.

**Audit-craft note.** Round 2 surfaced exactly the second-order class AGENTS.md "Audit-chain empirical settling shape" predicts: round-1 revisions either (a) named the wrong production code site (F-PLAN-R2-01 — I claimed CLI handlers as the classifier call site; actual call is in `core/state/snapshot.py:909`), (b) specified a contract the existing CLI doesn't expose (F-PLAN-R2-02 — `hai eval run` has no aggregate-percentage mode), (c) introduced a fork-defer branch that breaks downstream cycle assumptions (F-PLAN-R2-03 — v0.1.18 W-OB-2 hard-depends on W-29 closing), (d) failed to propagate a §3/§6 rule into per-WS acceptance (F-PLAN-R2-04 — snapshot lockstep), or (e) created stale source-doc citations during the F-PLAN-08 refresh (F-PLAN-R2-05 — tactical mixes 8891 and 9217 baselines). All five are audit-chain hygiene at the round-2 settling stage; none surface a new substantive scope question.

**Verifications below executed via grep / read against HEAD `df6a13c`. No tests run, no code changed (per audit-prompt constraint).**

---

## F-PLAN-R2-01 — W-D arm-2 plumbing path still wrong

**Verdict:** AGREED, applied.

**Verification.**

1. **Classifier call site.** `grep -n "classify_nutrition_state" src/health_agent_infra/core/state/snapshot.py src/health_agent_infra/cli.py`:
   - `core/state/snapshot.py:909` — `nutrition_classified = classify_nutrition_state(nutrition_signals)` (NO thresholds arg passed).
   - `cli.py` — only imports `build_snapshot`; never calls `classify_nutrition_state` directly.
   Codex right: production classifier call is in `build_snapshot()`, not in any CLI handler. My round-1 §2.I claim that `cmd_synthesize` / `cmd_state_snapshot` "call site" passes thresholds was wrong-shape.

2. **Threshold-override seam.** `src/health_agent_infra/domains/nutrition/classify.py:327`:
   ```python
   t = thresholds if thresholds is not None else load_thresholds()
   ```
   Treats non-None `thresholds` as the FULL tree. Subsequent reads at `:362-373` index into `t["classify"]["nutrition"]["targets"]`, `t["classify"]["nutrition"]["calorie_balance_band"]`, etc. Round-1 acceptance item 5 passed `{"classify": {"nutrition": {"projection_mode": "linear_extrapolation"}}}` — a partial dict that would replace the entire tree and KeyError on the very next access. Codex right.

3. **DEFAULT_THRESHOLDS shape.** `core/config.py:321-360` confirms `classify.nutrition` has `targets` (kcal/protein/hydration only — no `carbs_target_g`/`fat_target_g`/`projection_mode` leaves). Codex right: `projection_mode` is not a defaults leaf; "reachable without a code change" was wrong as written.

4. **`cmd_state_snapshot` handler-group placement.** `reporting/docs/archive/cycle_artifacts/cli_boundary_table.md:99` places `cmd_state_snapshot` in `cli/handlers/state.py`, NOT `recommend.py`. Round-1 §2.I files-of-record had this wrong.

5. **`build_snapshot()` signature.** `core/state/snapshot.py:372` `def build_snapshot(...)` — does not currently accept a `thresholds` parameter. Round-1 PLAN's "thresholds override at the call site" needs an actual API extension or an internal merge step.

**Action.** §2.I rewritten end-to-end (round-2 close):

1. **Files of record updated.** Added `core/state/snapshot.py` (the actual classifier-call site, with the new internal merge step). Removed `cmd_state_snapshot` from `cli/handlers/recommend.py`; correctly attributed to `cli/handlers/state.py` per v0.1.13 boundary table. `cmd_synthesize` retained at `recommend.py` (correct).

2. **Plumbing path corrected.** The merge step lives **inside `build_snapshot()`**, not at a CLI handler. New shape:
   - `build_snapshot()` continues to call `compute_presence_block()` to derive `is_partial_day` + `target_status` (already in tree).
   - When `is_partial_day == true && target_status == "present"`, `build_snapshot()` calls the new helper `core/target/store.py::get_active_macro_targets(conn, user_id, as_of_date)` to fetch the four macro target values.
   - `build_snapshot()` then deep-merges those values into a fresh `load_thresholds()` tree under `classify.nutrition.targets` (replacing the kcal/protein defaults; adding `carbs_target_g`/`fat_target_g`).
   - `build_snapshot()` calls `classify_nutrition_state(nutrition_signals, thresholds=merged_tree)`.
   - When arm-2 conditions don't hold, `build_snapshot()` continues to call `classify_nutrition_state(nutrition_signals)` (no thresholds arg) — pre-W-D-arm-2 behaviour preserved.
   - **No public API change to `build_snapshot()`** (no new external arg); the merge is an internal branch. CLI handlers (`cmd_state_snapshot`, `cmd_synthesize`, `cmd_today`, `cmd_explain`) are unchanged.

3. **DEFAULT_THRESHOLDS extension.** `core/config.py` `DEFAULT_THRESHOLDS["classify"]["nutrition"]` extended with:
   - `"projection_mode": "target_anchored"` (default; alternative `"linear_extrapolation"` reachable via `thresholds.toml` user override OR via test-time threshold-tree construction).
   - No new `carbs_target_g` / `fat_target_g` defaults — those are absent in defaults; only flow in from user-committed `target` rows when arm-2 fires.

4. **Macro projection scope clarified.** v1 projects four macros (kcal, protein, carbs, fat) when target_status=present. **Band classification operates against the projection** for: `calorie_balance_band` (kcal), `protein_sufficiency_band` (protein). **Bands do not exist for carbs and fat** in v0.1.17 — projected_eod_carbs_g / projected_eod_fat_g are informational, surfaced in `hai explain` only. **Hydration is held observed** (no hydration target in W-C 4-row group).

5. **Acceptance items rewritten** (item 5 fixed; remaining items renumbered/clarified):
   - **Item 1** (target-row plumbing) unchanged — verifies `get_active_macro_targets()` returns the seeded values.
   - **Item 2** (projection emission) clarified — verifies `build_snapshot()` emits `projected_eod_kcal` + `projected_eod_protein_g` + `projected_eod_carbs_g` + `projected_eod_fat_g` AND `nutrition_status="aligned"` AND `calorie_balance_band="met"` against the projection (kcal + protein bands fire; carbs + fat are informational).
   - **Item 3** (arm-1 fallback) unchanged.
   - **Item 4** (day-closed fallthrough) unchanged.
   - **Item 5 rewritten:** "Linear-extrapolation reachability test" now passes a **deep-merged full thresholds tree** (built via `load_thresholds()` + override `classify.nutrition.projection_mode = "linear_extrapolation"`), not a partial dict. Asserts the linear shape emits when the tree carries the override; target-anchored emits otherwise. The `projection_mode` leaf must exist in `DEFAULT_THRESHOLDS` (per item above) so `load_thresholds()` returns a tree where the leaf is set; the test override flips the leaf without breaking the tree's structural completeness.
   - **Item 6** (`hai explain` rendering) unchanged.
   - **Item 7** (synthesis-policy integration) unchanged.

6. **§2.I "Plumbing path" prose rewritten** to match the build_snapshot internal-merge shape; `cmd_synthesize` / `cmd_state_snapshot` "call site" language retired.

**Cross-doc fan-out.**
- §1.2 catalogue cell unchanged.
- §1.3 sequencing unchanged.
- §4 risk 6 rewritten to reflect the corrected plumbing (build_snapshot internal merge; no CLI-handler edit).
- §5 effort table unchanged at 2-3 days for W-D arm-2 (the merge step is internal to `build_snapshot()`; small).
- §6 ship gates W-D-arm-2-specific row updated to reflect the new helper + `projection_mode` default leaf.
- §8 OQ-5 unchanged (target-anchored ratified as v1 default; round-2-3 maintainer ratification expected).

---

## F-PLAN-R2-02 — ≥95% eval-corpus gate not executable through `hai eval run`

**Verdict:** AGREED, applied.

**Verification.**

`grep -nE "USER_INPUT|exit_code|failed" src/health_agent_infra/evals/cli.py | head -20` confirms Codex's claim:
- `cmd_eval_run()` returns OK only when `failed == 0`.
- `_run_all_scenario_sets()` runs each domain + synthesis sequentially; first non-zero status returns immediately; no aggregate numerator/denominator computed.
- `--json` output prints one payload per sub-run, not a single aggregate object.

So a "≥95% pass-rate" gate cannot be expressed through the current CLI. Either every fixture passes (100%) or the cycle fails. Round-1 PLAN's 95% tolerance was unaachievable without a CLI extension that wasn't scoped.

**Action.** Tightened gate to **100% pass**. Cite the v0.1.14 baseline: at v0.1.14 ship, the 35-fixture corpus passed cleanly (the cycle wouldn't have shipped otherwise; `hai eval run --scenario-set all` returned OK). 100% is the inherited contract.

**Rationale for tightening (not extending CLI):** Adding a `--summary` mode + aggregate-percentage helper to `hai eval run` is real scope-creep — it would belong in W-AI-2 (`hai eval review` is the eval-tooling WS) but isn't currently in W-AI-2's surface. Cleaner to:
1. Tighten W-AH-2 acceptance to 100% pass-rate.
2. Force the per-scenario validation discipline (per F-PLAN-02 + the v0.1.14 W-AM lesson — "Fixtures that fail their own expected blocks are dropped + logged in the W-AH-2 commit message as runtime-contract findings, not silently shipped").
3. If a fixture genuinely can't fire its expected block after iteration, drop + log; don't ship a 99% corpus that breaks the gate.

**§2.C item 5 rewritten.** Was "≥95% pass-rate" → now "**100% pass-rate**: `hai eval run --scenario-set all` returns OK exit code (matches the existing CLI's `failed == 0` contract per `evals/cli.py:cmd_eval_run`). v0.1.14 baseline: 35-fixture corpus passed at 100% at ship; W-AH-2 inherits the 100% contract and grows the corpus 35 → 132+ within that contract."

**§6 ship gates rewritten:** "≥95% pass-rate" → "100% pass-rate (matches existing `hai eval run` exit-code contract)."

**§4 risk 7 unchanged** (was about runtime expansion, not pass-rate).

**OQ-6 disposition update:** Codex agreed with 20/domain + 12-15 synthesis distribution; the 100%-pass tightening doesn't change the distribution call. OQ-6 closes at round 3 if maintainer agrees.

**Aggregate-percentage helper deferral.** The `--summary` mode for `hai eval run` is a candidate for v0.1.18+ or v0.2.x scope. Not pulled forward into v0.1.17.

---

## F-PLAN-R2-03 — `do-not-split` fork-defer branch breaks downstream cycle assumptions

**Verdict:** AGREED, applied.

**Verification.**

1. **v0.1.18 hard dependency.** `reporting/plans/v0_1_18/README.md:57-60`: "v0.1.17 must close so W-29 cli.py split is in tree before W-OB-2 (default-flip touches the `hai init` argparse handler; pre-split would create merge conflicts; post-split lands cleanly in the appropriate handler-group module)." Confirmed: v0.1.18 hard-depends on W-29 closing.

2. **PLAN §7 self-citation.** PLAN §7 names the same v0.1.18 dependency: "**W-OB-2 default-flip explicitly depends on the W-29 cli.py split landing first**." Confirmed.

3. **Closure-surface entanglement.** Round-1 PLAN's `do-not-split` fork-defer branch said "Phase 2 + Phase 3 ship without W-29; release-blocker status converts at PLAN re-author time." But:
   - W-29 is the cycle's only release-blocker (§1.2 catalogue Severity column, §6 release-blocker gates).
   - §3 ship-time AGENTS.md edits append `W-29 closed at v0.1.17` and retire the cli.py-split "Do Not Do" clause — both impossible if W-29 doesn't ship.
   - §7 enumerates v0.1.18 as out-of-scope but doesn't anticipate v0.1.18 sliding due to a v0.1.17 W-29 deferral.
   - README + tactical §5D + tactical §5E v0.1.18 row all carry the assumption that W-29 closes at v0.1.17.
   
   The fork-defer branch as written would silently invalidate ~10 cross-doc surfaces. Not operational.

**Action.** Collapsed §2.A acceptance item 2 to a **single halt-and-re-author branch**. The `do-not-split` outcome triggers cycle hold; PLAN re-authors through D14 with all of the following reconsidered:
- W-29 release-blocker status (drops or rescopes).
- §3 ship-time AGENTS.md edits (append + clause-removal don't fire).
- §6 W-29-specific release-blocker gates (drop).
- §7 v0.1.18 dependency text (renegotiate with v0.1.18 PLAN.md author at that cycle's open).
- README + tactical §5D + tactical §5E rows (refresh).
- W-29-3 destination cycle (assigned during PLAN re-author).

The "Phase 2 + Phase 3 ship without W-29" branch is removed. Phase 2/3 would still depend on W-29 mechanically (W-AI-2 / F-PV14-02 / W-B all add CLI surfaces post-W-29 split; without the split, they merge into pre-split cli.py and create the exact merge friction §1.3 sequencing was designed to prevent). Halt-and-re-author is the only safe shape.

**§2.A acceptance item 2 rewritten:** "**`do-not-split` abort path.** If item 1 returns `do-not-split`, the cycle halts at Phase 1 open. PLAN.md re-authors through D14 round 2+ before resuming, with all of the following reconsidered: W-29 release-blocker status, §3 ship-time AGENTS.md edits, §6 W-29-specific release-blocker gates, §7 v0.1.18 dependency text, README + tactical §5D rows, and W-29-3 destination cycle assignment. Cycle does NOT silently degrade to no-op or to ship-Phase-2/3-without-W-29 (round-2 F-PLAN-R2-03 retired that branch as unsafe — Phase 2/3 W-AI-2 / F-PV14-02 / W-B all add CLI surfaces that depend on the split landing first)."

**§4 risk 1 rewritten** to remove the (a) fork-deferred branch. Now reads: "If the refreshed verdict is `do-not-split`, §2.A acceptance item 2 halts the cycle; PLAN re-authors through D14 round 2+. Branches (b) sub-split and (c) escalate-for-re-shape are unchanged from round 1."

**§7 unchanged** — v0.1.18 dependency text still names W-29 as v0.1.17's responsibility; the halt-and-re-author branch handles the cross-cycle reshape if needed.

---

## F-PLAN-R2-04 — Snapshot lockstep not in per-WS acceptance

**Verdict:** AGREED, applied.

**Action.** Added an acceptance item to each of §2.D (W-AI-2), §2.G (F-PV14-02), §2.H (W-B):

- **§2.D W-AI-2 acceptance commit-gate, new item 7:** "Snapshot regeneration lockstep: the W-AI-2 commit regenerates `verification/tests/snapshots/cli_capabilities_v0_1_13.json`, `verification/tests/snapshots/cli_help_tree_v0_1_13.txt`, AND `reporting/docs/agent_cli_contract.md` in the **same commit** as the `hai eval review` surface adds. `test_cli_parser_capabilities_regression.py` runs clean against the regenerated snapshots."
- **§2.G F-PV14-02 acceptance, item 5 expanded:** Was "`hai capabilities --markdown` regenerates with the new entry" → now "Snapshot regeneration lockstep: the F-PV14-02 commit regenerates the JSON manifest snapshot, the parser-tree snapshot, AND the markdown contract in the same commit as the `hai sync purge` surface adds."
- **§2.H W-B acceptance, new item 7:** Same shape — JSON manifest + parser-tree + markdown regeneration in the same commit as the `hai intake weight` surface adds.

**Cross-check against §2.A W-29 acceptance items 4-6:** W-29's byte-stability gate is the **pre-add comparison** (against the snapshot current at Phase 1 open). The Phase 2/3 CLI-surface adds **regenerate** the snapshot per their own commits. The two contracts don't conflict — W-29 doesn't drift the snapshot, and Phase 2/3 explicitly drift it in lockstep with the surface change.

---

## F-PLAN-R2-05 — Tactical LOC baseline mixed (8891 vs 9217)

**Verdict:** AGREED, applied.

**Verification.**

- `wc -l src/health_agent_infra/cli.py` → 9927 (current).
- `reporting/docs/archive/cycle_artifacts/cli_boundary_table.md:55` → "cli.py total LOC | 8891" (v0.1.13 W-29-prep baseline).
- `reporting/plans/v0_1_14/RELEASE_PROOF.md:25` → "cli.py 9217-line mechanical split with byte-stable manifest preservation deemed too high-risk" (v0.1.14 deferred-W-29 baseline).
- Round-1 source-doc refresh (F-PLAN-08 fix) updated tactical §5D row 703 with "9217 LOC at v0.1.13 W-29-prep" — Codex caught: that's misattributed. 9217 was v0.1.14 RELEASE_PROOF, not v0.1.13 W-29-prep. The correct W-29-prep number is 8891.
- `reporting/plans/tactical_plan_v0_1_x.md:49` (top cycle table row) still says "9217-line mechanical split" — also stale.

**Action.**

1. **Tactical §5D row 703 revised** — changed from "was 9217 LOC at v0.1.13 W-29-prep" to "was 9217 LOC at v0.1.14 RELEASE_PROOF deferred-W-29 baseline (the v0.1.13 W-29-prep boundary-table baseline was 8891 LOC; 9217 reflects the post-v0.1.13-ship + W-AA + W-FBC-2 + intra-v0.1.13 surface adds — see boundary table at `reporting/docs/archive/cycle_artifacts/cli_boundary_table.md:55`)." Provenance now correct + dual-baseline difference explicit.
2. **Tactical line 49 (top cycle table row) updated** — from "W-29 cli.py 9217-line mechanical split" to "W-29 cli.py 9927-line mechanical split (was 9217 LOC at v0.1.14 RELEASE_PROOF deferral baseline; +710 LOC across v0.1.14/v0.1.15/v0.1.15.1 surface adds)."
3. **PLAN §2.A pre-flight prose extended** with one sentence distinguishing the two baselines: "Two historical baselines exist: 8891 LOC at v0.1.13 W-29-prep boundary-table author-time (the archived `reporting/docs/archive/cycle_artifacts/cli_boundary_table.md:55`), and 9217 LOC at v0.1.14 RELEASE_PROOF deferred-W-29 cite. Both are correctly cited in their respective source docs; PLAN uses 8891 as the boundary-table baseline (the table is the architectural spec; 8891 is its baseline); tactical §5D / line 49 use 9217 as the v0.1.14 deferral baseline."

---

## OQ disposition table (round-2 update)

| OQ | Round-1 Codex opinion | Round-2 Codex opinion | Round-2 disposition |
|---|---|---|---|
| OQ-1 (`hai sync` placement) | "Acceptable; decide after refreshed boundary table" | "Agree with revised default: start with `state.py`; let refreshed boundary note choose `sync.py` if state.py is muddy" | **Held to W-29 Phase 1 close** — pending boundary-note evidence. |
| OQ-5 (W-D arm-2 default) | "Hold pending F-PLAN-01" | "Do not ratify until F-PLAN-R2-01 fixed" | **Held to round 3** — F-PLAN-R2-01 fixed at this round-2 edit; round-3 maintainer ratification expected. |
| OQ-6 (W-AH-2 distribution) | "Acceptable post-harness fix" | "Agree with 20/domain + 12-15 synthesis after harness correction; remaining issue is eval-corpus gate" | **Closeable at round 3** — F-PLAN-R2-02 fixed at this round-2 edit; distribution ratification carries forward. |
| OQ-8 (W-29 commit shape) | "Prefer 3-commit; acceptance must be explicit" | "Agree with 3-commit; per-commit acceptance is now clear; do-not-split branch needs reshape (R2-03)" | **Closeable at round 3** — F-PLAN-R2-03 fixed at this round-2 edit; OQ-8 default ratifies. |

§8 list shrinks from 4 → 4 (no closures yet; round 3 should close OQ-5 + OQ-6 + OQ-8 if revisions hold).

---

## Round 3 expectations

**Recommended next-round budget:** 0.5 session (Codex closure recommendation).

**Surfaces Codex should re-check (narrow):**
- Revised W-D arm-2 §2.I (build_snapshot internal-merge shape; cmd_state_snapshot handler-group correction; full-tree threshold-merge in acceptance item 5; projection_mode default added to DEFAULT_THRESHOLDS prose).
- Revised W-AH-2 §2.C item 5 + §6 (100% pass-rate, not ≥95%).
- Revised §2.A item 2 + §4 risk 1 (single halt-and-re-author branch).
- New per-WS snapshot acceptance items in §2.D / §2.G / §2.H.
- Revised tactical §5D row 703 + tactical line 49 (LOC baseline corrected).
- Revised PLAN §2.A pre-flight prose (dual-baseline note).
- Stale-status / citation sweep across PLAN + README + tactical (Codex's "quick stale-status/citation sweep" closure note).

**Empirical settling:** AGENTS.md `10 → 5 → 3 → 0` halving signature predicts ~2-3 round-3 findings (likely close-in-place nits or third-order from round-2 revisions). >3 round-3 findings would indicate the round-2 revisions over-corrected; ≤3 → close in place at round 3.

---

## Change-set summary

| File | Action |
|---|---|
| `reporting/plans/v0_1_17/PLAN.md` | 5 finding-driven revisions; §2.I rewritten end-to-end (build_snapshot internal merge; cmd_state_snapshot in state.py; full-tree threshold acceptance); §2.C item 5 + §6 100%-pass tightening; §2.A item 2 + §4 risk 1 single-halt branch; §2.D + §2.G + §2.H per-WS snapshot lockstep; §2.A pre-flight dual-baseline note; §9 round-2 close entry; §8 OQ list updated. |
| `reporting/plans/tactical_plan_v0_1_x.md` | §5D row 703 baseline correction + provenance prose; line 49 top-row LOC update. |
| `reporting/plans/v0_1_17/codex_plan_audit_round_2_response_response.md` | This file. |
| `reporting/plans/v0_1_17/codex_plan_audit_round_3_prompt.md` | Round 3 kickoff (per AGENTS.md D14 + Dom's auto-draft feedback memory). |

**Provenance.** This response-response authored 2026-05-04 against HEAD `df6a13c`. PLAN + tactical revisions land in this same edit pass; no separate commit yet (Phase 0 hasn't opened — D14 round 3 fires first).
