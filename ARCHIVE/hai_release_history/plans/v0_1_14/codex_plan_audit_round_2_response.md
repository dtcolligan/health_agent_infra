# Codex Plan Audit Round 2 Response — v0.1.14 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS

**Round:** 2

**Round-1 follow-through summary:** Of the 12 round-1 findings, 9
revisions landed cleanly, 3 landed partially, and 0 failed to land
entirely. The partials are F-PLAN-02 sizing propagation, F-PLAN-10
CP-W30-SPLIT body text, and F-PLAN-11 CP verdict/status propagation.

## Findings

### F-PLAN-R2-01. 32-45 day sizing did not reach all summary surfaces

**Q-bucket:** R2-Q1  
**Severity:** unfinished-revision  
**Reference:** PLAN.md line 8; tactical_plan_v0_1_x.md lines 474-480  
**Argument:** F-PLAN-02 corrected the PLAN body to 32-45 days:
PLAN.md §1.2 reports 32-45 days at lines 72-74 and §5 reports
32-45 days at lines 443-459. But the PLAN metadata still says
`Estimated effort: 30-40 days` at line 8, and tactical_plan §5.3
still says `30-40 days` at lines 474-480. Those are the exact stale
round-down surfaces F-PLAN-02 was meant to remove.  
**Recommended response:** Revise PLAN.md line 8 and tactical_plan
§5.3 to 32-45 days, with the same 31.5-44.5 arithmetic note and
45-day scope-cut trigger used in PLAN.md §5.

### F-PLAN-R2-02. CP-W30-SPLIT still omits W58D claim-block in its proposed D4 delta

**Q-bucket:** R2-Q1 / R2-Q4  
**Severity:** unfinished-revision  
**Reference:** CP-W30-SPLIT.md lines 63-69; AGENTS.md lines 127-133;
tactical_plan_v0_1_x.md lines 629-634  
**Argument:** AGENTS.md D4 now correctly says W-30 waits for `W52 +
W58D claim-block (v0.2.0), W53 (v0.2.1), W58J (v0.2.2)` at lines
127-133, and tactical_plan §9.1 now matches at lines 629-634.
CP-W30-SPLIT's header also acknowledges the F-PLAN-10 correction at
lines 5-10. But the CP's own "Proposed delta — AGENTS.md D4" still
proposes `W52 v0.2.0, W53 v0.2.1, W58J v0.2.2` at lines 63-69,
omitting W58D claim-block again. That leaves the CP internally
inconsistent with the settled D4 text it is supposed to document.  
**Recommended response:** Update CP-W30-SPLIT lines 63-69 to the same
wording used in AGENTS.md D4: `W52 + W58D claim-block (v0.2.0), W53
(v0.2.1), W58J (v0.2.2)`.

### F-PLAN-R2-03. CP files still contain stale "pending" Round-N verdict sections

**Q-bucket:** R2-Q1 / R2-Q4  
**Severity:** unfinished-revision  
**Reference:** CP-2U-GATE-FIRST.md lines 131-133;
CP-MCP-THREAT-FORWARD.md lines 152-154;
CP-DO-NOT-DO-ADDITIONS.md lines 165-167; CP-PATH-A.md lines 262-264;
CP-W30-SPLIT.md lines 126-128  
**Argument:** F-PLAN-11 updated the top `Codex verdict:` field in all
five CP files, but each CP still has a later `Round-N codex verdict`
section saying `pending — CP not yet submitted to Codex review`.
That contradicts the new header status and PLAN.md §6 lines 514-517,
which says all five CP verdict fields update post-D14 round 1.  
**Recommended response:** Either delete the obsolete `Round-N codex
verdict` sections or replace each with the same applied-at-v0.1.14
D14 round-1 status used in the file header.

### F-PLAN-R2-04. Candidate-absence gate is earlier than the cycle pattern requires

**Q-bucket:** R2-Q2  
**Severity:** second-order-issue  
**Reference:** PLAN.md lines 101-123 and 155-159; AGENTS.md lines
163-174; PLAN.md line 421  
**Argument:** PLAN.md §1.3.1 says the OQ-I candidate must resolve
before Phase 0 can open and, if absent, option 1 is to defer Phase 0
until a candidate surfaces. AGENTS.md D14 says Phase 0 runs after the
PLAN is plan-audited and before the pre-implementation gate; the
implementation workstreams do not start until after that gate. The
candidate is required for W-2U-GATE, which is the first implementation
workstream, not for the internal sweep, audit-chain probe, or 12-persona
Phase 0 matrix. Requiring a candidate before Phase 0 opens can
unnecessarily block a useful D11 bug-hunt that does not depend on the
foreign user.  
**Recommended response:** Replace "before Phase 0 can open" / "by
Phase 0 gate" with "by the pre-implementation gate, before W-2U-GATE
opens." Option 1 should hold implementation or W-2U-GATE, not the
Phase 0 bug-hunt itself.

### F-PLAN-R2-05. D14 round-count rescope references point at the candidate-absence procedure

**Q-bucket:** R2-Q2 / R2-Q3  
**Severity:** second-order-issue  
**Reference:** PLAN.md lines 420, 437, and 461-464; PLAN.md lines
101-123 and 493-495  
**Argument:** The §4 risks row for `D14 exceeds 5 rounds` points to
`§1.3 sequencing constraint + §1.3.1 candidate-absence procedure` at
line 437. But §1.3.1 is about absence of the W-2U-GATE candidate; it
does not define the D14 round-count rescope lever. The correct
round-count gate is already in §3 at line 420 and §5 at lines 461-464.
There is a second stale cross-reference in §6: line 495 says the
4-5-round expectation is "per §1.4 acceptance," but §1.4 is the
deferrals table, not an acceptance section.  
**Recommended response:** Point the D14-exceeds-5 mitigation to the §3
D14 plan-audit gate and §5 D14 expectation. Remove the §1.3.1
cross-reference from the D14 round-count row, and replace "§1.4
acceptance" with "§3 ship gate" or "§5 D14 expectation."

### F-PLAN-R2-06. Evidence-card and source-row citations do not name the actual reconciliation file

**Q-bucket:** R2-Q3  
**Severity:** provenance-failure  
**Reference:** PLAN.md lines 183-185; tactical_plan_v0_1_x.md lines
499-504; reporting/plans/post_v0_1_13/reconciliation.md lines 1-6;
reporting/plans/future_strategy_2026-04-29/reconciliation.md lines
140-151  
**Argument:** PLAN.md says `Reconciliation §4 C10` names source-row
locators, and tactical_plan §6.1 says `recommendation_evidence_card.v1`
comes from `reconciliation C8`. The current PLAN's named reconciliation
input is `reporting/plans/post_v0_1_13/reconciliation.md`, but that file
has no C8 or C10 rows. The C8/C10 rows do exist in
`reporting/plans/future_strategy_2026-04-29/reconciliation.md` at lines
149-151. This is a provenance problem rather than a strategy problem:
the citation is real, but the file path is not named where ambiguity now
matters.  
**Recommended response:** Qualify both citations with the full
`future_strategy_2026-04-29/reconciliation.md` path and the relevant
C-row. For example: `future_strategy_2026-04-29/reconciliation.md §4
C8/C10`.

### F-PLAN-R2-07. Tactical §11 still uses implementation-review verdicts for a PLAN audit phase

**Q-bucket:** R2-Q2 / R2-Q3  
**Severity:** settled-decision-conflict  
**Reference:** tactical_plan_v0_1_x.md lines 706-740; AGENTS.md lines
223-240  
**Argument:** F-PLAN-07's renumbering itself landed: §11 subheads are
11.1-11.6, and the old 8.x labels are gone. But after the renumber,
§11 still says the Codex audit of PLAN.md returns `SHIP /
SHIP_WITH_NOTES / DO_NOT_SHIP` at lines 731-734. AGENTS.md splits the
cycle into D14 plan-audit, which returns `PLAN_COHERENT` /
`PLAN_COHERENT_WITH_REVISIONS` / `PLAN_INCOHERENT` at lines 223-225,
and later implementation-review rounds, which return `SHIP` or
`SHIP_WITH_NOTES` at lines 236-240. The tactical playbook now mixes the
two verdict scales.  
**Recommended response:** Revise tactical §11.3 to describe D14
PLAN.md audit with the PLAN_COHERENT verdict scale, then keep SHIP /
SHIP_WITH_NOTES for the later implementation-review phase.

## Empirical-settling note (per R2-Q5)

Round 2 found 7 issues after 12 round-1 findings. That is at the top
of the expected 5-7 band and warrants a round 3, but the findings are
mostly mechanical propagation and citation fixes rather than evidence
that the 14-W-id scope is incoherent. Because F-PLAN-R2-05 finds that
§1.3.1 is not the right D14 round-count rescope lever, the recommended
path is targeted revision plus round-3 verification, with rescope
reserved for a round-3 finding count that remains materially above the
empirical settling curve.
