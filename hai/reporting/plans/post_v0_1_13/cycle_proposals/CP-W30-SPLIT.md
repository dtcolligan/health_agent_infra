# CP-W30-SPLIT — Move W-30 capabilities-manifest schema freeze to v0.2.3

**Cycle:** v0.2.0 PLAN authoring upcoming (final ship destination v0.2.3).
**Author:** Claude (delegated by maintainer; OQ-B 2026-05-01).
**Codex verdict:** applied at v0.1.14 D14 round 1
(PLAN_COHERENT_WITH_REVISIONS); AGENTS.md D4 + "Do Not Do" line
updated 2026-05-01 pre-cycle. F-PLAN-10 surfaced that the D4 schema-
group list omitted W58D claim-block from v0.2.0; corrected at
v0.1.14 D14 round 1 (W52 + W58D claim-block ship together in v0.2.0,
followed by W53 v0.2.1 and W58J v0.2.2 before W-30 v0.2.3).
**Application timing:** at v0.2.0 PLAN.md authoring — companion to
CP-PATH-A; updates AGENTS.md D4 + tactical_plan_v0_1_x.md to place
W-30 at v0.2.3 (Path A) instead of "last act of v0.2.0" (CP2 + CP5).
**Source:** Strategic-research report 2026-05-01 §11 R-2; Codex
research-audit round-1 F-RES-03; reconciliation §3.B; OQ-B answered
Path A 2026-05-01.

---

## Rationale

Settled decision D4 (v0.1.8 origin, v0.1.12 paired-acceptance
update) schedules W-30 (capabilities-manifest schema freeze) for
v0.2.0 "after W52/W58 schema additions land" (per AGENTS.md:
124-127). CP5 (v0.1.12) confirmed this placement as "the last act
of the cycle" within the single substantial release shape.

CP-PATH-A (this batch) splits v0.2.0 into v0.2.0 / v0.2.1 / v0.2.2 /
v0.2.3 to honor reconciliation C6 (one schema group per release).
W-30 has no schema coupling to any of W52 / W53 / W58D / W58J
substrate work; it is hygiene that ships *after* substrate. Under
Path A, the last cycle in the v0.2.x sequence is v0.2.3 (judge
promotion + freeze), and W-30 fits naturally there as a no-new-
schema hardening item alongside the W58J flag flip.

This is a destination change for a workstream the maintainer
already owns. AGENTS.md D4's "scheduled for v0.2.0 after W52/W58
schema additions land" condition is satisfied by v0.2.3 — by then,
W52 (v0.2.0), W53 (v0.2.1), W58D (v0.2.0), and W58J (v0.2.2) have
all shipped, so all v0.2.x schema additions are present.

## Current AGENTS.md text (verbatim, verified on disk 2026-05-01)

`AGENTS.md:124-127`:

```
- **W29 / W30 scheduled.** cli.py split scheduled for v0.1.14
  conditional on v0.1.13 boundary-audit verdict (parser /
  capabilities regression test mandatory regardless).
  Capabilities-manifest schema freeze scheduled for v0.2.0 after
  W52 / W58 schema additions land. (Origin: v0.1.12 CP1 + CP2,
  paired acceptance.)
```

## Proposed delta — AGENTS.md D4

**Replace `:127`:**

> Capabilities-manifest schema freeze scheduled for v0.2.0 after
> W52 / W58 schema additions land. (Origin: v0.1.12 CP1 + CP2,
> paired acceptance.)

**With:**

> Capabilities-manifest schema freeze scheduled for **v0.2.3**
> after all v0.2.x schema additions land (**W52 + W58D claim-block
> (v0.2.0), W53 (v0.2.1), W58J (v0.2.2)**). (Origin: v0.1.12 CP1 +
> CP2, paired acceptance; v0.2.x destination updated by
> post-v0.1.13 CP-PATH-A + CP-W30-SPLIT, OQ-B answered Path A
> 2026-05-01; W58D claim-block added to v0.2.0 schema-group list
> per v0.1.14 D14 round 1 F-PLAN-10 + round 2 F-PLAN-R2-02.)

## Proposed delta — AGENTS.md "Do Not Do" line

`AGENTS.md:396-397` reads:

```
- Do not split `cli.py` or freeze the capabilities manifest schema before
  their scheduled cycles (v0.1.14 / v0.2.0). (Origin: v0.1.12 CP1 + CP2.)
```

**Replace:**

> their scheduled cycles (v0.1.14 / v0.2.0).

**With:**

> their scheduled cycles (v0.1.14 / **v0.2.3**).

## Proposed delta — tactical_plan_v0_1_x.md

CP-PATH-A handles the v0.2.0-v0.2.3 split. CP-W30-SPLIT confirms
W-30 placement in the new §9 (v0.2.3) per CP-PATH-A's delta.

## Proposed delta — strategic_plan_v1.md

Wave 2 entry (where it cites v0.2.0 capabilities-manifest schema
freeze as the cycle's last act) updates to v0.2.3.

## Affected files

- `AGENTS.md` D4 (line 127) and "Do Not Do" line (line 396-397).
- `reporting/plans/tactical_plan_v0_1_x.md` (handled jointly with
  CP-PATH-A).
- `reporting/plans/strategic_plan_v1.md` Wave 2 reference.
- `reporting/plans/v0_2_3/PLAN.md` (new at v0.2.3 PLAN authoring).

## Dependent cycles

- **v0.2.0**: W-30 NOT in scope (was previously "last act of cycle").
- **v0.2.1**: W-30 NOT in scope.
- **v0.2.2**: W-30 NOT in scope.
- **v0.2.3**: W-30 ships as one of two workstreams (alongside W58J
  flag flip). Cycle tier: hardening.

## Acceptance gate

- `accepted`: AGENTS.md D4 + "Do Not Do" line updated to v0.2.3;
  W-30 lands in v0.2.3 PLAN.
- `accepted-with-revisions`: destination cycle revised within Path A
  (e.g., v0.2.2 if maintainer decides W-30 fits with W58J shadow
  rather than blocking-flip). The "after substrate ships" property
  is load-bearing.
- `rejected`: CP-PATH-A also implicitly rejected (since W-30
  destination depends on the split shape). CP archived; D4 stands;
  W-30 ships at v0.2.0 single-release per CP5.

## Round-N codex verdict

**Applied at v0.1.14 D14 round 1 (PLAN_COHERENT_WITH_REVISIONS,
2026-05-01).** AGENTS.md D4 + "Do Not Do" line updated 2026-05-01
pre-cycle. F-PLAN-10 surfaced that the D4 schema-group list omitted
W58D claim-block from v0.2.0; corrected at v0.1.14 D14 round 1
(W52 + W58D claim-block ship together in v0.2.0, followed by W53
v0.2.1 and W58J v0.2.2 before W-30 v0.2.3). F-PLAN-R2-02 (round 2)
caught that this CP's own "Proposed delta — AGENTS.md D4" body still
omitted W58D claim-block; corrected at round 2.

## Companion CP

This CP is paired with CP-PATH-A. Acceptance state should remain
synchronized: if Path A is accepted, W-30 → v0.2.3; if Path A is
rejected, W-30 → v0.2.0 single-release (CP5 default).
