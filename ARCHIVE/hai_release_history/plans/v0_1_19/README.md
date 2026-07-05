# v0.1.19 cycle — CANCELLED

**Status:** Cancelled 2026-05-06 per CP-2U-GATE-SPLIT
(`reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md`) + AGENTS.md D16.

## Why cancelled

The cycle was scoped as **empirical-by-design** against a wearable-
bearing foreign-user session. v0.1.16 cancelled when its named
candidate (name redacted; coursemate) became unavailable on 2026-05-04;
v0.1.19 inherited the empirical scope after a v0.1.18 onboarding-
quality cycle was inserted to close the install→first-plan gap before
re-exposing it to a foreign user.

On 2026-05-06 the maintainer surfaced two facts in chat:

1. The candidate-supply criteria for a wearable-bearing foreign user
   are too narrow to satisfy on the v0.2.0 timeline ("the criteria
   for what is needed is too difficult for me to find").
2. A wearable-less foreign-user install had already happened
   (maintainer's father, post-v0.1.18, verbatim "it worked for him").

That combination forced re-evaluation of the gate definition.
W-2U-GATE was found to conflate three empirical claims with different
candidate-supply costs. CP-2U-GATE-SPLIT formalizes the split and
re-tiers two of the three to opportunistic-not-blocking.

## What replaces it (per CP-2U-GATE-SPLIT)

W-2U-GATE splits into three gates:

- **W-2U-INSTALL** — install + onboarding + abstain-without-wearable
  produces coherent output for a non-maintainer. **Closed**
  (verbal-only) by the post-v0.1.18 father session.
- **W-2U-WEARABLE** — full pipeline (pull adapter → classification
  → cross-domain synthesis → daily plan with non-trivial coverage)
  produces useful output for a wearable-bearing foreign user.
  **Deferred** to v0.4 review (MCP read-surface prereq).
- **W-2U-DOGFOOD** — non-maintainer uses the system daily for ≥7
  consecutive days. **Deferred** to v0.4 review.

The empirical workstreams originally scoped here are re-destinated:

- **W-2U-FIX-P1 / P2** — fold into whatever cycle opens against the
  next available foreign-user session (likely v0.2.x post-publish
  carry-forward).
- **W-EXPLAIN-UX-2** — re-destinated to v0.2.0 PLAN as a non-blocking
  carry-forward workstream.
- **W-FPV14-SYM** (conditional) — re-destinated to v0.2.0 PLAN as a
  non-blocking carry-forward (still conditional on a friction signal
  surfacing).
- **W-OB-FU-RESIDUAL** (conditional) — closed-by-default; absorbed
  into W-2U-INSTALL closure (no residual surfaced in the father
  session).

## Closure provenance — verbal-only

The W-2U-INSTALL closure is **verbal-only**. No transcript at
`reporting/plans/v0_1_19/foreign_machine_session_<YYYY-MM-DD>.md` and
none planned (maintainer chat 2026-05-06: "I cannot get father
transcript").

This residual is named in:

- AGENTS.md D16.
- v0.2.0 PLAN.md §-residual-risks (when authored).
- CP-2U-GATE-SPLIT "Residual claim — W-2U-INSTALL closure quality
  (verbal-only)".

Future cycles' D14 may flag the closure as weak provenance. That is
correct behaviour — the residual is real and is named explicitly to
short-circuit the round-2 finding.

## v0.2.0 hard-dep impact

v0.2.0 hard-dep on v0.1.19 is **dropped** per CP-2U-GATE-SPLIT.
v0.2.0's only remaining hard dep is v0.1.14 substrate (W-PROV-1 +
W-AJ judge harness), already shipped.

## Cross-references

- `reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md` — the CP that
  authorizes this cancellation.
- `AGENTS.md` D16 — the settled decision.
- `reporting/plans/v0_1_16/README.md` — prior cancellation precedent.
- `reporting/plans/tactical_plan_v0_1_x.md` §1 — v0.2.0 hard-deps row
  reflects the drop.
- `reporting/plans/strategic_plan_v1.md` §7 Wave 1 — footnote naming
  the gate split.

## Pattern note

This is the second cancelled-cycle README in the v0.1.x track. The
pattern (v0.1.16 → v0.1.19) confirms the "empirical-by-design cycles
cannot be built on synthetic evidence" lesson from
`reporting/plans/v0_1_16/README.md` and adds a refinement:
**empirical cycles also cannot be built on over-specified candidate
criteria**. CP-2U-GATE-SPLIT operationalizes the refinement by
splitting one over-specified gate into three claims with explicit
candidate-supply differentials.

Do not use this directory as an open implementation checklist.
