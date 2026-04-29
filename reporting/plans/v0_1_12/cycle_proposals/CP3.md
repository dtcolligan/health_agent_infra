# CP3 — Adopt 4-tier cycle-weight classification (D15)

**Cycle:** v0.1.12.
**Author:** Claude (delegated by maintainer).
**Codex round-4 verdict:** `accept`.
**Application timing:** at v0.1.12 ship — adds D15 to AGENTS.md
"Settled Decisions" + v0.1.12 RELEASE_PROOF declares
`tier: substantive`.
**Self-application note:** v0.1.12 declares its own tier under
the new D15 classification before D15 is itself shipped. This is
intentional — see "Self-application paradox resolution" below.

---

## Rationale

Maintainer adjudication 2026-04-29 (chat): four tiers vs three.
Codex's reasoning: "codifying 'hotfix' prevents the hardening
tier from absorbing legitimate hotfix work and inflating its
audit cost." Maintainer agreed.

The cycle-pattern audit weight (D11 Phase 0 bug-hunt + D14
plan-audit rounds) currently scales loosely with maintainer
judgement. v0.1.11 ran a substantive-class load (4 D14 rounds, 18
findings; full Phase 0 substituted by demo-run findings). v0.1.10
ran similarly. Smaller cycles should run lighter audit weight
without being implicitly forced through the substantive
machinery.

## Current AGENTS.md text

No tier classification exists. The "Settled Decisions" section
ends at D14.

## Proposed delta — add to AGENTS.md "Settled Decisions"

```
- **(D15, v0.1.12) Cycle-weight tiering.** Substantive /
  hardening / doc-only / hotfix.

  - **Substantive** (≥1 release-blocker workstream, ≥3 governance
    or audit-chain edits, OR ≥10 days estimated): full Phase 0
    bug-hunt (D11) + multi-round D14 plan-audit until
    PLAN_COHERENT (empirical norm 2-4 rounds).
  - **Hardening** (correctness/security only, no governance, ≤1
    week): abbreviated Phase 0 (internal sweep + audit-chain
    probe; persona matrix optional); single-round D14 plan-audit
    target.
  - **Doc-only** (no code change, no test surface change): may
    skip Phase 0 + D14. RELEASE_PROOF still required if version
    bumps.
  - **Hotfix** (reverts, single-bug fixes, named-defer
    propagation, no scope expansion): may skip Phase 0 + D14.
    Lightweight RELEASE_PROOF.

  RELEASE_PROOF.md declares the chosen tier as the first line
  of the document, before any per-W-id reporting. The tier
  declaration is a load-bearing artifact: future audit-cycle
  retros cite it.
```

## Self-application paradox resolution

v0.1.12 declares `tier: substantive` *before* CP3 is itself
shipped. Three resolutions per Q2 (chat 2026-04-29):

- **CP3 `accepted`:** v0.1.12 RELEASE_PROOF declares
  `tier: substantive`. D15 is in AGENTS.md by then. No paradox
  in retrospect.
- **CP3 `accepted-with-revisions`:** v0.1.12 RELEASE_PROOF
  declares per the revised D15 wording.
- **CP3 `rejected`:** v0.1.12 RELEASE_PROOF omits the tier line.
  D11/D14 audit weight follows the pre-v0.1.12 norm. No retro-
  fitted classification.

## Affected files

- `AGENTS.md` — add D15 entry to "Settled Decisions" (after D14).
- `reporting/plans/v0_1_12/RELEASE_PROOF.md` (authored at v0.1.12
  ship) — first line declares `tier: substantive`.
- `reporting/plans/tactical_plan_v0_1_x.md` — future cycle rows
  gain a tier annotation column.

## Dependent cycles

- **v0.1.13 onwards** — every cycle's RELEASE_PROOF declares
  tier; future audit-cycle retros use the tier annotation as
  filter.

## Acceptance gate

- `accepted`: AGENTS.md gains D15; v0.1.12 RELEASE_PROOF
  declares `tier: substantive`. **Editorial convention (per
  F-IR-04 round 1):** the applied D15 entry may carry editorial
  refinements over the proposal text — formatted backticks
  around `PLAN_COHERENT`, condensed RELEASE_PROOF wording, and a
  trailing `Origin: v0.1.12 CP3.` provenance line. The CP names
  the *replacement text core*; the editorial polish is allowed
  under the `accepted` gate.
- `accepted-with-revisions`: revised D15 applied; v0.1.12
  RELEASE_PROOF declares per revised text.
- `rejected`: AGENTS.md unchanged; v0.1.12 RELEASE_PROOF omits
  tier line; downstream cycles inherit pre-v0.1.12 norm.

## Round-4 codex verdict

`accept`. Codex round-4 confirmed the four-tier scheme is
internally coherent and the self-application fallback is
explicit.
