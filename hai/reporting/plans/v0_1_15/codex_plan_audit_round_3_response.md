# Codex Plan Audit Response — v0.1.15 PLAN.md (Round 3)

**Verdict:** PLAN_COHERENT_WITH_REVISIONS. The round-3 PLAN is coherent enough to open after in-place edits. The remaining issues are summary/fan-out drift, not scope or dependency failures.

**Round:** 3

**Closure recommendation:** close in-place. Finding count is 3, and all are nit or acceptance-criterion-weak severity; no round 4 is needed unless the maintainer chooses to re-audit after applying these edits.

## Round-2 finding closure verification

| Round-2 finding | Status | Round-3 verification |
|---|---|---|
| F-PLAN-R2-01 | CLOSED_WITH_RESIDUAL | PLAN §2.B/§2.E now use typed `target_status` and W-D arm-1 suppresses on `absent`/`unavailable`. Residual: PLAN §4 risks still use old `target_present` wording. See F-PLAN-R3-01. |
| F-PLAN-R2-02 | CLOSED | PLAN §1.2, §5, v0_1_15 README, and tactical §5B now align on 16-25 days, 2-4 D14 rounds, W-GYM-SETID 1.5-3d, and W-2U-GATE 4-7d. |
| F-PLAN-R2-03 | CLOSED_WITH_RESIDUAL | Core 16-slot accounting is now correct in PLAN §1.4 and v0_1_17 README. Residual stale provenance/status strings remain in PLAN header/§9 and tactical §5B. See F-PLAN-R3-03. |
| F-PLAN-R2-04 | CLOSED_WITH_RESIDUAL | The findings doc has a clear SUPERSEDED header and honestly preserves the original F-AV-01 example. Residual: PLAN §9 says the example was updated, which contradicts the chosen preservation shape. See F-PLAN-R3-03. |
| F-PLAN-R2-05 | CLOSED_WITH_RESIDUAL | PLAN §2.G now makes threshold breach P0 and excludes capabilities-manifest changes from cheap P1 fixes. Residual: tactical §5B still describes maintainer-intervention breach as P1. See F-PLAN-R3-02. |
| F-PLAN-R2-06 | CLOSED_WITH_RESIDUAL | PLAN §4.5 now names truthful cleanup paths: full restore or leave cosmetic rows; no selective restore path remains. Residual: the cited CLI range is the restore parser flags, not the `cmd_restore` handler. See F-PLAN-R3-03. |
| F-PLAN-R2-07 | CLOSED_WITH_RESIDUAL | PLAN §6 and tactical archive bullets now include the install record, transcript, state snapshot, package shape, and P-tier disposition. Residual: PLAN §2.G still says "tagged commit" despite OQ-8 choosing commit SHA only. See F-PLAN-R3-02. |

## New findings (round 3)

### F-PLAN-R3-01. PLAN §4 still uses the old `target_present` contract

**Q-bucket:** Q-R3.1.a / Q-R3.2.a  
**Severity:** nit  
**Reference:** PLAN.md §4 lines 216-217; PLAN.md §2.B lines 125-135; PLAN.md §2.E lines 151-161

**Argument:** The canonical W-A/W-D contract is now coherent: `target_status: "present" | "absent" | "unavailable"` and W-D arm-1 fires on `target_status in ("absent", "unavailable")`. PLAN §4 risks still say W-D reads `target_present`, W-D fires on `!target_present`, and W-A emits `target_present: "unavailable"`. That reintroduces the exact type-mixing language round 2 removed, even though the implementation sections are correct.

**Recommended response:** Update §4 risk items 1-2 to use `target_status`, not `target_present`, and explicitly say the table-missing pre-W-C branch is implemented as catch-and-emit `unavailable` for the read-side query.

### F-PLAN-R3-02. Gate contract still drifts in §2.G and tactical §5B

**Q-bucket:** Q-R3.1.e / Q-R3.1.g / Q-R3.2.c  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.G line 183; PLAN.md §6 lines 261-269; tactical_plan_v0_1_x.md §5B lines 616-620

**Argument:** OQ-8 chooses commit SHA only, and PLAN §6 correctly says the candidate package is built from the final branch commit with install-record SHA. PLAN §2.G still says "post-merge to main, tagged commit", leaving the tag ambiguity F-PLAN-R2-07 was meant to remove. Tactical §5B also still says maintainer intervention beyond the one allowed question is P1, while PLAN §2.G now correctly classifies any acceptance-1 threshold breach as P0. Those are summary-surface drifts, but they touch the load-bearing gate contract.

**Recommended response:** In §2.G, replace "tagged commit" with "commit SHA recorded in the install record; no gate-candidate tag required." In tactical §5B, make threshold breach P0 and define P1 as trust-degrading findings within a threshold-met session.

### F-PLAN-R3-03. Final provenance and citation cleanup is still needed

**Q-bucket:** Q-R3.1.c / Q-R3.1.d / Q-R3.1.f / Q-R3.5.c  
**Severity:** nit  
**Reference:** PLAN.md header lines 3-4; PLAN.md §4 line 223; PLAN.md §9 lines 303 and 308; tactical_plan_v0_1_x.md §5B line 578 and §5D line 735; src/health_agent_infra/cli.py lines 4289-4321 and 8588-8599

**Argument:** A few provenance/citation strings still reflect older rounds. The PLAN header says "D14 round-2 ready" and "15-slot" even though this is round 3 and the canonical count is 16 slots. PLAN §9 says "deferred 8 W-ids + W-D arm-2" and says F-PLAN-R2-04 updated the F-AV-01 example, but the maintainer intentionally preserved that example behind a SUPERSEDED header. PLAN §4 refers to `F-PLAN-R2-11`, which does not exist; it was a round-2 closing open question, not a finding. Tactical §5B still says "D14 round-1 in flight", and tactical §5D has `w0.2.0`. Finally, PLAN §4.5 cites `cli.py:8588-8599` as the restore verification range; that range shows restore parser flags, while `cmd_restore` itself is at `cli.py:4289-4321`. The parser citation is useful, but the PLAN should label it accurately or cite both ranges.

**Recommended response:** Apply a single final doc-freshness pass: update the PLAN header/status/provenance bullets, fix the nonexistent F-PLAN-R2-11 reference, correct tactical status/typo strings, and change the restore citation to "parser flags at `cli.py:8588-8599`; handler at `cli.py:4289-4321`."

## Open questions answered (Codex opinions on OQ-7, OQ-8, OQ-9)

**OQ-7, `target_status="unavailable"` semantics:** suppress is the right v0.1.15 default. It is honest for partial-day/no-target data and avoids a hard fail before target setup exists in the user's flow. I would not add an `N`-day blocker for this cycle. If `unavailable` persists, the host-agent prose can recommend setting a nutrition target, but the gate should not require W-D to fail closed.

**OQ-8, gate-candidate tag shape:** commit SHA only is the right default. The install record gives exact reproducibility without adding tag lifecycle bookkeeping. The only required edit is to remove the stale "tagged commit" phrase from §2.G.

**OQ-9, candidate-withdrawal mid-cycle:** the pre-Phase-3 procedure is right. If the candidate aborts during Phase 3, the existing acceptance criterion already fails because no full session reaches `synthesized`; archive the partial transcript as non-gate evidence, fix/retry if the abort is product-caused, or re-enter the §4.6 decision tree if the candidate is no longer available. Adding that as one clarifying sentence would be useful but does not require another audit round.

## Open questions for maintainer (new from round 3)

None. The three findings above are close-in-place cleanup items.
