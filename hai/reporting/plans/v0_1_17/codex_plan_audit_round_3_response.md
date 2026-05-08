# Codex Plan Audit Response — v0.1.17 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS — close in place after the three named stale/contract revisions below; no round 4 needed.

**Round:** 3

## Round-2 closure verdicts (per F-PLAN-R2-NN)

| Round-2 finding | Round-3 verdict | Note |
|---|---|---|
| F-PLAN-R2-01 (W-D arm-2 plumbing) | CLOSED_WITH_RESIDUAL | The production call site is now correctly `core/state/snapshot.py`, the merge is internal to `build_snapshot()`, and item 5 now uses a full threshold tree. Residual: W-D text still contains two stale/incorrect classifier details. See F-PLAN-R3-01. |
| F-PLAN-R2-02 (eval-corpus gate 100%) | CLOSED | §2.C + §6 now require OK exit / 100% pass, matching `evals/cli.py`'s `failed == 0` contract. The v0.1.14 35/35 baseline is verifiable in `v0_1_14/codex_implementation_review_round_3_response.md:10`. |
| F-PLAN-R2-03 (W-29 single-halt branch) | CLOSED | §2.A item 2 and §4 risk 1 now collapse `do-not-split` to halt-and-re-author, with downstream surfaces named. No remaining fork-defer/ship-without-W-29 branch found. |
| F-PLAN-R2-04 (per-WS snapshot lockstep) | CLOSED_WITH_RESIDUAL | §2.D, §2.G, and §2.H now have commit-local snapshot/markdown lockstep items. Residual: §6 still cites old acceptance item ranges for W-AI-2 and W-B. See F-PLAN-R3-02. |
| F-PLAN-R2-05 (LOC baseline) | CLOSED | Tactical line 49 and §5D row 703 now attribute 9217 to the v0.1.14 RELEASE_PROOF baseline, and PLAN §2.A distinguishes 8891 vs 9217 with source-doc paths. |

## Round-3 findings (new — third-order)

### F-PLAN-R3-01. W-D arm-2 has stale classifier-contract details

**Q-bucket:** QR3-1 / QR3-6  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.I lines 424, 453, 458; PLAN.md §4 line 519; `src/health_agent_infra/domains/nutrition/classify.py:85-87,139-157`; `src/health_agent_infra/core/state/snapshot.py:1183-1209`

**Argument:** The main F-PLAN-R2-01 plumbing fix is correct, but three W-D details still need cleanup.

First, acceptance item 2 asserts `protein_sufficiency_band="adequate"`. The current classifier's protein band vocabulary is `"met"|"low"|"very_low"|"unknown"`, and `_classify_protein_sufficiency()` returns `"met"` when the projected ratio is 1.0. A test written against `"adequate"` would fail for the wrong reason.

Second, §4 risk 6 still says §2.I specifies a helper plus "threshold-override at `cmd_synthesize` / `cmd_state_snapshot` call sites." That contradicts the corrected §2.I shape: CLI handlers consume `build_snapshot()` output, and the threshold merge is internal to `core/state/snapshot.py`.

Third, §2.I says `projected_eod_*` fields are emitted in the classified state, but the existing `ClassifiedNutritionState` dataclass and `_nutrition_classified_to_dict()` serializer do not have those fields today. That is implementable, but the PLAN should name the dataclass/serializer contract so the fields actually appear in `build_snapshot(...).nutrition.classified_state`, not only in a local classifier object.

**Recommended response:** Change item 2 to `protein_sufficiency_band="met"`. Update §4 risk 6 to the `build_snapshot()` internal-merge path. In §2.I files-of-record or acceptance item 2, explicitly say `ClassifiedNutritionState` and `_nutrition_classified_to_dict()` gain `projected_eod_kcal`, `projected_eod_protein_g`, `projected_eod_carbs_g`, and `projected_eod_fat_g`.

### F-PLAN-R3-02. §6 still cites pre-round-2 acceptance item ranges

**Q-bucket:** QR3-4 / QR3-6  
**Severity:** nit  
**Reference:** PLAN.md §2.D line 233, §2.H line 384, §6 lines 586-599

**Argument:** F-PLAN-R2-04 added commit-local snapshot lockstep as W-AI-2 acceptance item 7 and W-B acceptance item 7. The per-WS ship gates in §6 still say W-AI-2 commit-gate items **1-6** pass and W-B acceptance items **1-6** pass. That omits the new item 7 from the per-WS gate text, even though the standard gate and §2 acceptance lists are correct.

**Recommended response:** Update §6 to say W-AI-2 commit-gate items 1-7 pass, and W-B acceptance items 1-7 pass. Optionally append "including snapshot regeneration lockstep" to both bullets.

### F-PLAN-R3-03. Round-status and OQ prose still say round 2 is pending/carrying

**Q-bucket:** QR3-6  
**Severity:** nit / provenance-gap  
**Reference:** `reporting/plans/v0_1_17/README.md:3`; PLAN.md §2.I line 471; PLAN.md §8 lines 640, 644, 648

**Argument:** The revised PLAN is in D14 round 3, but several summary surfaces still describe the prior state. README line 3 says "round 2 pending." PLAN §8 says "Carrying to round 2," and OQ-5 / OQ-8 still say round-2 ratification is expected. The section header and §9 entry correctly say round 3, so this is stale status text rather than a substantive contradiction.

**Recommended response:** Update README status to "round 2 closed PLAN_COHERENT_WITH_REVISIONS, round 3 pending." Change §8's subheading to "Carrying to round 3." Update OQ-5 and OQ-8 to say round-3 ratification expected, or close them in the post-audit response if the maintainer accepts this round's dispositions.

## Open-question dispositions (round 3)

**OQ-1 — `hai sync` handler-group placement:** Keep open until W-29 Phase 1 boundary refresh. The current default (`state.py`, with `sync.py` available if the boundary note says so) is coherent.

**OQ-5 — W-D arm-2 projection-function default:** Close after F-PLAN-R3-01 is applied. Target-anchored default is coherent; linear extrapolation remains reachable through the full-tree `projection_mode` override once the wording nits are fixed.

**OQ-6 — W-AH-2 distribution:** Close. The 20/domain + 12-15 synthesis target is acceptable, and the 100% eval gate now matches the existing CLI.

**OQ-8 — W-29 atomic commit vs series:** Close. The 3-commit default plus per-commit acceptance items 4-7 is clear, and the `do-not-split` branch now halts for re-authoring.

## Closure recommendation

**Verdict:** PLAN_COHERENT_WITH_REVISIONS, close in place.

Must-fix revisions:

1. F-PLAN-R3-01 — fix W-D's `protein_sufficiency_band` expected value, stale §4 call-site prose, and projected-field serialization contract.
2. F-PLAN-R3-02 — update §6 W-AI-2 and W-B gate item ranges to include item 7.
3. F-PLAN-R3-03 — refresh README/§8 round-status wording.

These are single-pass text edits with no new workstream, no new test surface beyond already-planned W-D implementation tests, and no new governance question. After applying them, the maintainer can close D14 round 3 without scheduling round 4.
