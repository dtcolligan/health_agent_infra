# Codex External Audit — v0.1.14 PLAN.md Round 4

> **Why this round.** D14 round 3 returned PLAN_COHERENT_WITH_REVISIONS
> with 3 findings (12 → 7 → 3, mirroring v0.1.13's 11 → 7 → 3 → 1-nit
> → 0 settling shape). All 3 ACCEPT; revisions applied + committed
> across ROADMAP.md + PLAN.md + tactical_plan + 3 new audit-chain
> files (23 insertions / 2 deletions).
>
> **Round 4 is a verification pass aimed at closing the chain.**
> Expected outcome: **PLAN_COHERENT** (0 findings) or
> **PLAN_COHERENT_WITH_REVISIONS with a single nit**. Any finding
> count ≥2 is a settling-shape signal worth surfacing.
>
> **Scope is the narrowest yet.** Audit:
>   1. Did each F-PLAN-R3-01..03 revision land cleanly?
>   2. One final sweep for residuals across the cumulative r1+r2+r3
>      chain (sizing, candidate-gate timing, reconciliation
>      citations, CP file consistency).
>   3. Confirm cycle is ready for Phase 0 (D11) bug-hunt.
>
> **Empirical context.** D14 prior at v0.1.13: 11 → 7 → 3 → 1-nit → 0
> (5 rounds for 17 W-ids). v0.1.14: 12 → 7 → 3. If round 4 = 0,
> chain closes at 4 rounds = mid-band of 4-5 expected. If round 4
> = 1 nit, maintainer applies without re-running D14 (effective
> close at round 4).
>
> **Cycle position.** Pre-PLAN-open. Round-1, round-2, and round-3
> revisions all committed on `cycle/v0.1.14`. Phase 0 has not
> started. Audit is on the *plan document after r1+r2+r3
> revisions*.
>
> **You are starting fresh.** This prompt and the artifacts it
> cites are everything you need; do not assume context from a prior
> session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: cycle/v0.1.14
git log --oneline -5
# expect: 4 commits ahead of main:
#   <r3 sha>  v0.1.14 D14 r3: fixes for F-PLAN-R3-01..F-PLAN-R3-03
#   <r2 sha>  v0.1.14 D14 r2: fixes for F-PLAN-R2-01..F-PLAN-R2-07
#   f761c19   v0.1.14 D14 r1: fixes for F-PLAN-01..F-PLAN-12
#   900092e   v0.1.14 pre-cycle ...
ls reporting/plans/v0_1_14/
# expect: PLAN.md + 10 audit-chain files (4 prompts: r1/r2/r3/r4;
#         3 Codex responses: r1/r2/r3; 3 maintainer responses:
#         r1/r2/r3; round 4 prompt is this file)
# Total: 11 entries.
```

If any don't match, **stop and surface the discrepancy**.

---

## Step 1 — Read in this order

1. **`reporting/plans/v0_1_14/codex_plan_audit_round_3_response.md`**
   — your round-3 findings (F-PLAN-R3-01..03).
2. **`reporting/plans/v0_1_14/codex_plan_audit_round_3_response_response.md`**
   — maintainer disposition + named round-3 revisions per finding.
3. **`reporting/plans/v0_1_14/PLAN.md`** — the artifact post-r1+r2+r3.
   Read the §4 risks register row + §7 provenance convention note
   carefully; skim the rest.
4. **`ROADMAP.md`** — verify v0.1.14 row says 32-45 days.
5. **`reporting/plans/tactical_plan_v0_1_x.md`** — verify §13
   provenance convention note matches PLAN §7.
6. **Spot-read one of these for citation continuity (your choice):**
   `reporting/plans/post_v0_1_13/cycle_proposals/CP-PATH-A.md`,
   `AGENTS.md` "Patterns the cycles have validated" section, or
   `reporting/plans/v0_1_13/RELEASE_PROOF.md`.

---

## Step 2 — Round-4 audit questions

### R4-Q1. Did each round-3 revision land correctly?

For each F-PLAN-R3-01..03, verify the revision:

- **F-PLAN-R3-01 (ROADMAP sizing):** ROADMAP.md should say "32-45
  days" for the v0.1.14 line. Search the *active* part of ROADMAP
  for any remaining `30-40` reference (audit-chain commit messages
  / historical sections may retain it; only flag active prose).
- **F-PLAN-R3-02 (§4 risks timing):** PLAN.md §4 risks row
  "W-2U-GATE candidate doesn't materialize" trigger should say
  "pre-implementation gate" (not "Phase 0 gate"); mitigation should
  say "hold W-2U-GATE / implementation (Phase 0 may proceed)" + the
  three §1.3.1 options.
- **F-PLAN-R3-03 (reconciliation row-label convention):** PLAN.md §7
  + tactical_plan §13 should each have a convention-note paragraph
  saying A/L/C/D row labels refer to
  `reporting/plans/future_strategy_2026-04-29/reconciliation.md`
  unless full path stated. Both notes should reference the
  post-v0.1.13 reconciliation file by name to disambiguate.

For any revision that didn't land, file as `unfinished-revision`.

### R4-Q2. Final sweep for residuals across the cumulative chain

This is the chain's last opportunity to surface stale references.
Sweep for:

- **Sizing:** any "30-40 days" reference to v0.1.14 in active prose
  anywhere in the repo. Use grep across `*.md` excluding
  audit-chain commit-message-shaped files.
- **Candidate-gate timing:** any "Phase 0 gate" reference paired
  with "candidate" / "OQ-I" / "W-2U-GATE candidate" semantics
  (lone "Phase 0" references in cycle-pattern descriptions are
  fine; only flag the candidate-pairing pattern).
- **Reconciliation citations:** the round-3 fix used a convention
  note rather than inline path qualification. Verify the note is
  *visible enough* — i.e., it appears prominently in PLAN §7 and
  tactical §13 such that a reader hitting an inline "reconciliation
  A2" citation will resolve it correctly. If the note is buried,
  flag as `provenance-failure` with severity nit.
- **CP file consistency:** all 5 CP files should have updated
  headers + footers + body deltas. No remaining "pending" status.
  No remaining inconsistency between header verdict and footer
  Round-N status.
- **Verdict scales:** tactical_plan §11.3 D14 phase + §11.4 IR
  phase should still read coherently after the r2 split. No
  remaining mixing of PLAN_COHERENT and SHIP scales.

### R4-Q3. Is the cycle ready for Phase 0?

PLAN.md §6 + AGENTS.md D11 describe Phase 0 as: internal sweep
(pytest, ruff, mypy, bandit) + audit-chain probe + 12-persona
matrix + optional Codex external bug-hunt → `audit_findings.md`.

This is downstream work, not in scope for this audit. But verify:

- PLAN.md §6 + tactical_plan §11.1 describe Phase 0 consistently.
- PLAN.md §1.3.1 is clear that Phase 0 may proceed without the
  W-2U-GATE candidate; only implementation start is gated.
- No PLAN section assumes Phase 0 has already run or assumes it
  produces results not actually produced by the named D11 sweep.

If PLAN's Phase 0 framing is internally inconsistent or
contradicts AGENTS.md D11, file as `settled-decision-conflict`.

### R4-Q4. Empirical-settling shape

Note your round-4 finding count.

- **0 findings:** Verdict **PLAN_COHERENT**. Cycle ready for Phase
  0 (D11) bug-hunt. D14 chain closes at 4 rounds.
- **1 finding (nit):** PLAN_COHERENT_WITH_REVISIONS but trivial.
  Maintainer applies without re-running D14. Chain effectively
  closes at round 4.
- **2 findings:** PLAN_COHERENT_WITH_REVISIONS warranting round 5.
  Still within PLAN §3 ≤5-round acceptance gate (the upper bound).
- **3+ findings:** Audit chain not converging at expected rate.
  Surface as a settling-shape concern; recommend maintainer review
  whether the round-3 revisions introduced new drift.

D14 prior at v0.1.13: round 4 was 1 nit; round 5 was 0
(PLAN_COHERENT). v0.1.14 round-4 expected: 0 ideally, 1 nit
acceptable.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_14/codex_plan_audit_round_4_response.md`:

```markdown
# Codex Plan Audit Round 4 Response — v0.1.14 PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS | PLAN_INCOHERENT

**Round:** 4

**Round-3 follow-through summary:** <of the 3 round-3 findings, how
many revisions landed cleanly, how many partial, how many didn't
land>

## Findings

### F-PLAN-R4-01. <short title>

**Q-bucket:** R4-Q1 / R4-Q2 / R4-Q3 / R4-Q4
**Severity:** unfinished-revision | provenance-failure |
settled-decision-conflict | nit
**Reference:** <file>:<line>
**Argument:** <citation-grounded>
**Recommended response:** <revise as follows / accept / disagree>

### F-PLAN-R4-02. ...

## Empirical-settling note (per R4-Q4)

<one paragraph: round-4 finding count, recommendation on close vs
round 5>
```

**If verdict = PLAN_COHERENT:** state explicitly that the cycle is
ready for Phase 0 (D11) bug-hunt. The D14 chain is closed.

**If verdict = PLAN_COHERENT_WITH_REVISIONS with a single nit:**
the maintainer may apply the nit without re-running D14;
recommend "close at round 4 with nit applied" if findings are
trivially mechanical.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — D14 chain closes at round 4 (4 rounds total,
  mid-band of 4-5 expected). Cycle ready for Phase 0.
- **PLAN_COHERENT_WITH_REVISIONS** — maintainer applies findings;
  if trivial nits, close at round 4; if substantive, round 5
  verifies.
- **PLAN_INCOHERENT** — **highly unlikely** at round 4 given the
  consistent settling pattern. If it fires, the audit chain is
  pathological and re-scope per PLAN §3 is warranted.

---

## Step 5 — Out of scope

- Re-auditing PLAN's strategic posture, scope, Path A, settled
  decisions — all stable across r1+r2+r3.
- Re-auditing F-PLAN-01..F-PLAN-12 (round 1) or F-PLAN-R2-01..07
  (round 2) closures — round-2 follow-through summary settled the
  former; round-3 follow-through summary settled the latter.
- Code changes (Phase 0 hasn't started).

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14 r1] 12 findings ← done
  [D14 r1 revisions] committed (f761c19) ← done
  [D14 r2] 7 findings ← done
  [D14 r2 revisions] committed ← done
  [D14 r3] 3 findings ← done
  [D14 r3 revisions] committed ← done
  [D14 r4] Codex plan audit ← you are here
  Maintainer round-4 response (likely close path)
  ... if PLAN_COHERENT, chain closes here

Phase 0 (D11):
  Internal sweep + audit-chain probe + 12-persona matrix +
  optional Codex external bug-hunt → audit_findings.md

Pre-implementation gate:
  W-2U-GATE candidate must be on file (per PLAN §1.3.1
  pre-implementation-gate timing)
  revises-scope findings may revise PLAN (loop back to D14)
  aborts-cycle findings may end the cycle

PLAN.md → opens cycle → implementation → IR → SHIP → ship to PyPI
```

Estimated round-4 review duration: very short session. Round 4 is
the close path; if it surfaces nothing, no further D14 rounds.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_14/codex_plan_audit_round_4_response.md`
  (new) — your findings.
- `reporting/plans/v0_1_14/PLAN.md` (revisions, if warranted) —
  maintainer applies. **Likely no revisions needed.**
- `reporting/plans/v0_1_14/codex_plan_audit_round_5_prompt.md`
  (only if round 5 is warranted — unlikely).

**No code changes.** No test runs. No state mutations.

---

## Reference: pre-conceded falsifiers

All r1+r2+r3 falsifiers remain pre-conceded:

- W-2U-GATE structural P0 blocker → cycle reshapes per §1.3.
- W-2U-GATE candidate doesn't materialize → §1.3.1 procedure
  fires (gate is pre-implementation, not Phase 0).
- W-PROV-1 schema design needs major change → split substrate +
  features.
- W-29 split breaks capabilities snapshot → rollback (§3
  byte-identical gate).
- W-Vb-3 partial-closes again → honest naming with v0.1.15
  destination.
- W-EXPLAIN-UX foreign user unavailable → §1.3.1 fallback.
- Cycle exceeds 45-day budget → defer one of W-AM/W-AN/W-FRESH-EXT.
- D14 exceeds 5 rounds → re-scope per §3 ship gate.

If round 4 surfaces zero findings: that's the close path. Verdict
PLAN_COHERENT; cycle ready for Phase 0. No further D14 rounds for
v0.1.14.

If round 4 surfaces 1 nit: maintainer applies without re-running.
Effective close at round 4.

If round 4 surfaces 2+ findings: signal that round-3 revisions
introduced new drift (the convention-note approach for
F-PLAN-R3-03 is the most likely source — verify the note's
visibility + completeness was sufficient).
