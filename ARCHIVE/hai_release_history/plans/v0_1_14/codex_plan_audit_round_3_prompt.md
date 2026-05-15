# Codex External Audit — v0.1.14 PLAN.md Round 3

> **Why this round.** D14 round 2 returned PLAN_COHERENT_WITH_REVISIONS
> with 7 findings (12 → 7, top of expected 5-7 band). All 7 ACCEPT;
> revisions applied 2026-05-01 across PLAN.md + tactical_plan + 5 CP
> files (110 insertions / 45 deletions). Round 3 is a tight
> verification pass.
>
> **Scope is narrower than round 2.** Audit:
>   1. Did each F-PLAN-R2-01..07 revision land cleanly?
>   2. Did the larger r2 revisions (§1.3.1 timing flip; §11.3 verdict-
>      scale split; full-path reconciliation citations) propagate to
>      all surfaces?
>   3. Spot-check 5+ remaining citations not covered in r1 or r2.
>   4. Are CP file headers and footers internally consistent post-r2?
>
> **Empirical context.** D14 prior at v0.1.13: 11 → 7 → 3 → 1-nit → 0
> (5 rounds for 17 W-ids). v0.1.14: round 1 = 12, round 2 = 7.
> Expected round 3: **0-2 findings**. If round 3 = 3+, audit chain is
> running long; PLAN's §3 ship gate ≤5-round acceptance still holds
> but maintainer should treat as a settling-shape signal.
>
> **Cycle position.** Pre-PLAN-open. Round-1 + round-2 revisions
> committed (`f761c19` + `<r2 sha>`). Phase 0 has not started. Audit
> is on the *plan document after r1+r2 revisions*.
>
> **You are starting fresh.** This prompt and the artifacts it cites
> are everything you need; do not assume context from a prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: cycle/v0.1.14
git log --oneline -5
# expect: 3 commits ahead of main:
#   <r2 sha>  v0.1.14 D14 r2: fixes for F-PLAN-R2-01..F-PLAN-R2-07
#   f761c19   v0.1.14 D14 r1: fixes for F-PLAN-01..F-PLAN-12
#   900092e   v0.1.14 pre-cycle ...
ls reporting/plans/v0_1_14/
# expect: PLAN.md, codex_plan_audit_prompt.md,
#         codex_plan_audit_response.md (r1 Codex),
#         codex_plan_audit_round_1_response.md (r1 maintainer),
#         codex_plan_audit_round_2_prompt.md,
#         codex_plan_audit_round_2_response.md (r2 Codex),
#         codex_plan_audit_round_2_response_response.md (r2 maintainer),
#         codex_plan_audit_round_3_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**.

---

## Step 1 — Read in this order

1. **`reporting/plans/v0_1_14/codex_plan_audit_round_2_response.md`**
   — your round-2 findings (F-PLAN-R2-01..F-PLAN-R2-07).
2. **`reporting/plans/v0_1_14/codex_plan_audit_round_2_response_response.md`**
   — maintainer disposition + named round-2 revisions per finding.
3. **`reporting/plans/v0_1_14/PLAN.md`** — the artifact post-r1+r2
   revisions. Read fully — short by D14 standards (<700 lines).
4. **`reporting/plans/tactical_plan_v0_1_x.md`** — verify §5.3
   sizing (32-45 days + arithmetic + 45-day scope-cut), §6.1
   full-path reconciliation citation, §11.3 + §11.4 D14/IR
   verdict-scale split.
5. **`reporting/plans/post_v0_1_13/cycle_proposals/`:** verify all
   5 CP files have round-2 footer updates (no remaining "pending"
   status); CP-W30-SPLIT body delta includes W58D claim-block.
6. **Spot-read one of these for citation continuity (your choice):**
   `reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`,
   `reporting/plans/v0_1_13/RELEASE_PROOF.md`, or `AGENTS.md`.

Cross-check that everything PLAN.md cites still exists at the cited
locations after r1+r2 revisions. Broken cross-references count as
findings.

---

## Step 2 — Round-3 audit questions

### R3-Q1. Did each round-2 revision land correctly?

For each F-PLAN-R2-01..07, verify the revision is present in the
artifact and reads as intended:

- **F-PLAN-R2-01 (32-45 sizing):** PLAN.md line 8 metadata should say
  `Estimated effort: 32-45 days` (not 30-40). tactical_plan §5.3
  should say "32-45 days" + arithmetic note (31.5-44.5) + 45-day
  scope-cut trigger. **Search the entire repo for any remaining
  `30-40 days` reference** to v0.1.14 — if any exists outside
  audit-chain history, file as `unfinished-revision`.
- **F-PLAN-R2-02 (CP-W30-SPLIT body delta):** CP-W30-SPLIT.md
  "Proposed delta — AGENTS.md D4" body should now include "W52 +
  W58D claim-block (v0.2.0), W53 (v0.2.1), W58J (v0.2.2)" — the
  same wording AGENTS.md D4 has.
- **F-PLAN-R2-03 (CP file footers):** all 5 CP files should have
  no remaining `pending — CP not yet submitted to Codex review`
  text in their `Round-N codex verdict` footer sections. Each
  footer should describe applied-at-v0.1.14-D14-round-1 status
  with round-2 corrections noted where relevant.
- **F-PLAN-R2-04 (candidate gate timing):** PLAN §1.3.1 hard rule
  should say "by the **pre-implementation gate**" (not "Phase 0
  gate"); Option 1 should "Hold W-2U-GATE / implementation. Phase
  0 bug-hunt may proceed" (not "Defer Phase 0"). PLAN §2.A
  candidate-absence cross-ref should match the §1.3.1 update.
- **F-PLAN-R2-05 (D14 round-count cross-refs):** PLAN §4 risks row
  "D14 exceeds 5 rounds" mitigation should reference §3 ship gate +
  §5 D14 expectation; should NOT reference §1.3.1. PLAN §6 should
  say "per §3 ship gate" not "per §1.4 acceptance."
- **F-PLAN-R2-06 (full-path reconciliation citations):** PLAN §2.B
  should cite `reporting/plans/future_strategy_2026-04-29/reconciliation.md`
  §4 C10 (full path). tactical_plan §6.1 should cite the same file
  §4 C8 (full path). No bare "reconciliation §4 C8/C10" should
  remain.
- **F-PLAN-R2-07 (tactical §11.3 verdict-scale split):** tactical
  §11.3 should describe D14 PLAN-audit with PLAN_COHERENT scale.
  §11.4 should describe IR phase with SHIP scale. No mixing.

For any revision that didn't land or landed incorrectly, file as
`unfinished-revision`.

### R3-Q2. Did the larger r2 revisions propagate to all surfaces?

**§1.3.1 timing flip (Phase 0 gate → pre-implementation gate)**.
Round 2 changed the gate semantics. Audit:

- §2.A should match §1.3.1 (candidate by pre-implementation gate).
- §4 risks "W-2U-GATE candidate doesn't materialize" row should
  reference §1.3.1 procedure correctly.
- The §1.3.1 option 1 wording ("Hold W-2U-GATE / implementation.
  Phase 0 bug-hunt may proceed") — does it cleanly describe the
  state where Phase 0 has run + completed but pre-implementation
  gate withholds W-2U-GATE start?
- Any other PLAN section referencing "Phase 0" + "candidate" should
  reflect the new timing.

**§11.3 verdict-scale split.** Audit:

- §11.3 D14 phase + §11.4 IR phase: do they read coherently as
  *sequential phases* (D14 first, IR after cycle opens), not as
  alternative descriptions of the same audit?
- AGENTS.md D14 + AGENTS.md cycle pattern (lines 223-240) should
  match the new §11.3 D14 description.
- Any remaining §11.x reference to "SHIP / SHIP_WITH_NOTES /
  DO_NOT_SHIP" outside §11.4 IR phase context is orphan.

**Full-path reconciliation citations.** Audit:

- The 2026-04-29 reconciliation file `§4 C8` and `§4 C10` should
  actually exist at those locations; verify on disk.
- Any other citation in the artifact pointing at "reconciliation"
  unqualified by file path should still be checked — the round-2
  fix was scoped to the two found instances; round 3 should sweep.

### R3-Q3. Spot-check 5+ remaining citations not covered in r1/r2

Round 1 + 2 sampled some citations. Round 3 widens further:

- AGENTS.md "Patterns the cycles have validated" (Provenance
  discipline / Summary-surface sweep) — verify PLAN.md §6 cites
  these correctly when describing cycle compliance.
- ROADMAP.md "Now / Next" sections — verify they're consistent
  with the v0.1.14 PLAN scope (14 W-ids + Path A v0.2.x).
- Any URL in PLAN.md / tactical_plan / strategic_plan / AGENTS.md
  that round 1/2 didn't already check.
- AGENTS.md D11 + D14 line ranges cited in PLAN.md §6 — verify on
  disk.

If any citation fails verification, file as `provenance-failure`.

### R3-Q4. CP file consistency post-r2

After F-PLAN-R2-03 footers + F-PLAN-R2-02 body delta, all 5 CP
files should be internally consistent. Audit:

| CP | Header verdict | Footer Round-N | Body delta consistent with applied state |
|---|---|---|---|
| CP-2U-GATE-FIRST | applied at D14 r1 | applied + r2 timing fix noted | implemented in PLAN §1.3 + §1.3.1 + §2.A |
| CP-MCP-THREAT-FORWARD | applied at D14 r1 | applied | strategic_plan Wave 3 staging |
| CP-DO-NOT-DO-ADDITIONS | applied at D14 r1 | applied | AGENTS.md "Do Not Do" 3 bullets |
| CP-PATH-A | applied at D14 r1 | applied + §11.3 fix noted | tactical §6/§7/§8/§9 split |
| CP-W30-SPLIT | applied at D14 r1 | applied + W58D fix noted | AGENTS.md D4 + Do Not Do line + body delta updated |

Any inconsistency between header / footer / body / actually-applied
delta is a `settled-decision-conflict`.

### R3-Q5. Empirical-settling shape

Note your round-3 finding count.

- **0 findings:** Verdict PLAN_COHERENT — cycle ready for Phase 0.
- **1-2 findings (nits):** PLAN_COHERENT_WITH_REVISIONS but trivial;
  maintainer can apply as a final sweep without round 4.
- **3-5 findings:** PLAN_COHERENT_WITH_REVISIONS warranting round 4.
  Still within ≤5-round acceptance.
- **6+ findings:** Audit chain not converging; recommend maintainer
  re-scope per PLAN §3 ship gate before round 5 fires.

D14 prior at v0.1.13: 11 → 7 → 3 → 1-nit → 0 (round 3 was 3,
round 4 was 1-nit). v0.1.14 round-3 expected: 0-2 (slightly tighter
than v0.1.13 because v0.1.14's r1+r2 revisions were more mechanical).

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_14/codex_plan_audit_round_3_response.md`:

```markdown
# Codex Plan Audit Round 3 Response — v0.1.14 PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS | PLAN_INCOHERENT

**Round:** 3

**Round-2 follow-through summary:** <of the 7 round-2 findings, how
many revisions landed cleanly, how many partial, how many didn't land>

## Findings

### F-PLAN-R3-01. <short title>

**Q-bucket:** R3-Q1 / R3-Q2 / R3-Q3 / R3-Q4 / R3-Q5
**Severity:** unfinished-revision | second-order-issue | provenance-failure |
settled-decision-conflict | nit
**Reference:** <file>:<line>
**Argument:** <citation-grounded>
**Recommended response:** <revise as follows / accept / disagree with reason>

### F-PLAN-R3-02. ...

## Empirical-settling note (per R3-Q5)

<one paragraph: round-3 finding count, recommendation on whether to
close at round 3 (PLAN_COHERENT or COHERENT_WITH_REVISIONS) or continue
to round 4>
```

**If verdict = PLAN_COHERENT:** state explicitly that the cycle is
ready for Phase 0 (D11) bug-hunt.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — cycle ready for Phase 0; D14 chain closes at
  round 3 (4 rounds total — within 4-5 expected).
- **PLAN_COHERENT_WITH_REVISIONS** — name must-fix findings;
  maintainer applies; round 4 verifies (or closes at round 3 if
  findings are nit-class).
- **PLAN_INCOHERENT** — do not open. **Highly unlikely** at round 3
  given r1+r2 verdicts were both PLAN_COHERENT_WITH_REVISIONS with
  zero strategic-posture issues.

---

## Step 5 — Out of scope

- Re-auditing PLAN's strategic posture (settled at round 1).
- Re-auditing the 14-W-id catalogue + scope (settled at round 1).
- Re-auditing Path A vs Path B (settled at OQ-B 2026-05-01).
- Re-auditing F-PLAN-01..F-PLAN-12 round-1 closures (settled at
  round 2 follow-through summary: 9 clean / 3 partial / 0 missed).
- Code changes against this PLAN (Phase 0 hasn't started).

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14 r1] Codex plan audit ← done; 12 findings
  [D14 r1 revisions] applied + committed (f761c19) ← done
  [D14 r2] Codex plan audit ← done; 7 findings
  [D14 r2 revisions] applied + committed ← done
  [D14 r3] Codex plan audit ← you are here
  Maintainer round-3 response (likely close path: PLAN_COHERENT)
  ...

Phase 0 (D11):
  Internal sweep
  Audit-chain probe
  Persona matrix (12 personas pre-W-EXPLAIN-UX P13)
  Optional Codex external bug-hunt
  → audit_findings.md consolidates

Pre-implementation gate:
  W-2U-GATE candidate must be on file by this gate (per PLAN §1.3.1
  post-r2 timing)
  revises-scope findings may revise PLAN (loop back to D14)
  aborts-cycle findings may end the cycle

PLAN.md → opens cycle

Implementation rounds (IR):
  ... until SHIP / SHIP_WITH_NOTES

RELEASE_PROOF.md + REPORT.md → ship to PyPI
```

Estimated round-3 review duration: 1 short session. Round 3 is
verification; if it closes clean, no further D14 rounds.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_14/codex_plan_audit_round_3_response.md`
  (new) — your findings.
- `reporting/plans/v0_1_14/PLAN.md` (revisions, if warranted) —
  maintainer applies in response.
- `reporting/plans/tactical_plan_v0_1_x.md`,
  `reporting/plans/strategic_plan_v1.md`, `AGENTS.md`,
  `reporting/plans/post_v0_1_13/cycle_proposals/CP-*.md` (revisions
  to round-2 revisions, if warranted).
- `reporting/plans/v0_1_14/codex_plan_audit_round_4_prompt.md`
  (only if round 4 is warranted).

**No code changes.** No test runs. No state mutations.

---

## Reference: pre-conceded falsifiers

Round 1 + round 2 conceded these; they remain pre-conceded in
round 3:

- W-2U-GATE structural P0 blocker → cycle reshapes around fix per §1.3.
- W-2U-GATE candidate doesn't materialize → §1.3.1 procedure fires
  (revised at r2: gate is pre-implementation, not Phase 0).
- W-PROV-1 schema design needs major change → split substrate +
  features.
- W-29 split breaks capabilities snapshot → rollback (§3 byte-
  identical gate).
- W-Vb-3 partial-closes again → honest naming with v0.1.15
  destination.
- W-EXPLAIN-UX foreign user unavailable → §1.3.1 fallback.
- Cycle exceeds 45-day budget → defer one of W-AM/W-AN/W-FRESH-EXT.
- D14 exceeds 5 rounds → maintainer re-scopes per §3 ship gate.

If round 3 finds evidence supporting any of these *as currently
manifesting*, the corresponding workstream / acceptance criterion
adjusts automatically. Surface things round-1 + round-2 *didn't*
concede AND that the round-2 revisions *introduced*.

If round 3 finds nothing: that's the close path. Verdict
PLAN_COHERENT; cycle ready for Phase 0.
