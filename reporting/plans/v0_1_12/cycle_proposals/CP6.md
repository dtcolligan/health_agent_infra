# CP6 — Strategic plan §6.3 framing edit (L3)

**Cycle:** v0.1.12.
**Author:** Claude (delegated by maintainer).
**Codex round-4 verdict:** `accept`.
**Application timing:** **proposal authored at v0.1.12 ship;
text edit applied at v0.1.13 strategic-plan revision.** This is
the only CP whose application is deferred — it bundles with
other tactical adjustments at the v0.1.13 strategic-plan rev.

---

## Rationale

The reconciliation L3 finding (Claude-only catch):

> The actual moat is narrower than "publishable rule DSL". R-rule
> + X-rule code is competent engineering, not novel theory. What's
> genuinely defensible: (a) the audit chain, (b) the skill-overlay
> invariant (`_overlay_skill_drafts` whitelists 3 keys, raises on
> anything else, no skill imports in runtime code), (c) the Phase
> B write-surface guard (`guard_phase_b_mutation`).

The current §6.3 wording overstates the DSL's novelty. The DSL is
real engineering and worth publishing, but the moat — the thing
that no other comparable runtime has — is the *governance contract
+ audit chain + skill-overlay seam + Phase B write-surface guard*
acting as a load-bearing whole.

CP6 rebalances §6.3 to honor the DSL's contribution alongside the
other defensible substrate, rather than centring the DSL as "the
thing no competitor has."

## Current strategic plan §6.3 text (verbatim, verified on disk 2026-04-29)

**`strategic_plan_v1.md:407-411`:**

```
### 6.3 Ship the credible artifact

The R-rule + X-rule policy DSL is the thing no competitor has and
academia (AgentSpec, policy-as-prompt, Bloom's structured mutations)
is converging toward. It is publishable prior art. Treat it as one.
```

**`strategic_plan_v1.md:413-416` — v0.1.10 update line (preserved
unchanged by CP6):**

```
**v0.1.10 update:** The pre-PLAN bug-hunt pattern + persona harness
are also publishable — "structured pre-release audit with synthetic
personas" is a credible methodology contribution alongside the
runtime architecture.
```

## Proposed delta — replace `:407-411` with

```
### 6.3 Ship the credible artifact

The defensible substrate is a **load-bearing whole** of four
elements, no one of which is the moat alone:

1. **The governance contract + audit chain.** Three-state
   `proposal_log → planned_recommendation → daily_plan`
   reconciliation; every recommendation cites its evidence
   chain back to the source rows.
2. **The skill-overlay invariant.** `_overlay_skill_drafts`
   whitelists 3 keys, raises on anything else; no skill imports
   in runtime code. This keeps judgment-prose authorship
   bounded — skills cannot mutate the recommendation surface.
3. **The Phase B write-surface guard.** `guard_phase_b_mutation`
   enforces that Phase B (skill-overlay drafting) cannot reach
   the daily-plan write path.
4. **The R-rule + X-rule policy DSL.** Competent engineering
   that names the policy decisions in code. AgentSpec + policy-
   as-prompt + Bloom's structured mutations are converging
   toward similar shapes; the DSL is publishable prior art
   alongside (1)-(3), not above them.

All four are publishable. The contribution is that they hold
together as a single contract, not that any one of them is
novel theory.
```

The v0.1.10 update line (`:413-416`) is **preserved unchanged**
by CP6 — the methodology contribution claim about pre-PLAN bug-
hunt + persona harness still holds.

## Application timing — deferred to v0.1.13

CP6 is uniquely deferred-in-application among CP1-CP6. Reason:
the §6.3 edit is a quality-of-prose adjustment to the strategic
plan, not a structural decision. The v0.1.13 strategic-plan
revision (which will absorb other tactical adjustments per the
A1 trusted-first-value rename + CP5 wording carry-over + general
freshness work) is the natural application moment.

v0.1.12 ship records CP6 as `accepted` with the proposal doc
authored. v0.1.13 strategic-plan rev applies the §6.3 edit
verbatim from this proposal doc.

## Affected files

- `reporting/plans/v0_1_12/cycle_proposals/CP6.md` (this file)
  — authored at v0.1.12 ship.
- `reporting/plans/strategic_plan_v1.md` (lines 407-411) —
  edited at **v0.1.13 strategic-plan rev**, not at v0.1.12 ship.
- `reporting/plans/v0_1_12/RELEASE_PROOF.md` — records CP6
  verdict + applied-vs-deferred status.

## Dependent cycles

- **v0.1.13** — strategic-plan rev applies the §6.3 edit per
  this proposal's verbatim delta.

## Acceptance gate

- `accepted`: proposal doc authored at v0.1.12 ship; v0.1.13
  strategic-plan rev applies the §6.3 edit verbatim from above.
- `accepted-with-revisions`: revised wording applied at
  v0.1.13. Open for stylistic revision; the four-element
  framing (audit chain + skill-overlay + write-surface guard +
  DSL alongside) is non-negotiable — the rebalancing away from
  "DSL is the moat" is the core of the proposal.
- `rejected`: proposal doc archived in
  `reporting/plans/v0_1_12/cycle_proposals/`; strategic plan
  §6.3 unchanged.

## Round-4 codex verdict

`accept`. Codex round-4 confirmed the author-now / apply-at-
v0.1.13 split is internally coherent (no longer deferred-and-
required as round 1 caught).
