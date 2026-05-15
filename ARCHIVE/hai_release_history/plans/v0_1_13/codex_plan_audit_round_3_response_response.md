# Maintainer Response — v0.1.13 D14 Round 3

**Date:** 2026-04-30.
**Author:** Claude (delegated by maintainer Dom Colligan).
**Round under response:** 3
**Codex round-3 verdict:** PLAN_COHERENT_WITH_REVISIONS (3 findings).
**This response disposition summary:** all 3 findings accepted; 0
disputed; 0 deferred. Codex returned 0 open questions for the
maintainer.

The 3-finding count matches the empirical 10 → 5 → 3 → 0 settling
shape exactly. v0.1.11 + v0.1.12 + now v0.1.13 are all consistent
with that pattern across the first three rounds; round 4 is
expected to close at PLAN_COHERENT.

---

## Finding-by-finding disposition

### F-PLAN-R3-01 — W-Vb catalogue row still defers only P9/P11/P12

**Disposition:** ACCEPT.

The W-Vb catalogue row at §1.2.A line 92 was the only summary
surface I missed when expanding the W-Vb-3 fork-defer to all 9
non-ship-set personas in round 2. The other surfaces (PLAN §1.3,
§2.A acceptance, §3 ship gate, §4 risk row, CARRY_OVER §4) were
all updated; the catalogue row was overlooked despite being the
*primary* summary surface.

Pattern note: this is the **same shape** as F-PLAN-R3-02 — I
revised internal sections + auxiliary surfaces but missed the
top-of-doc summary. The summary-surface-sweep discipline catches
~5 of ~6 sites consistently; Codex catches the missed one. The
fix is to make summary surfaces the FIRST sweep target, not the
last.

**Edit sites:** PLAN.md §1.2.A W-Vb catalogue row (full enumeration
of 9 non-ship-set personas + concrete fixture filenames
`p4_strength_only_cutter.json` and `p5_female_multisport.json`
inline so the row is self-contained).

### F-PLAN-R3-02 — CARRY_OVER §1 still presents W-Vb as full closure

**Disposition:** ACCEPT.

CARRY_OVER §1 W-Vb row used "in-cycle" disposition with notes
describing "full-shape persona DomainProposal seeds" — language
that read as full all-persona closure rather than the P1+P4+P5
narrowed ship-set. The 9-persona residual at CARRY_OVER §4 is
correct, but a reader of §1 alone would miss it.

Disposition tag changed from "in-cycle" to "**partial-closure**"
with explicit cross-reference to v0.1.14 W-Vb-3 in §4. Notes
expanded to name the P1+P4+P5 ship set and the 9 non-ship-set
personas explicitly.

This makes CARRY_OVER §1 self-honest: the disposition column says
the work is partial, the W-id column shows the destination cycle,
and the notes enumerate both the in-scope and deferred sets.

**Edit sites:** CARRY_OVER §1 W-Vb row (disposition + notes).

### F-PLAN-R3-03 — F-PLAN-R2-04 token ambiguity + missing W-FBC-2 in source list

**Disposition:** ACCEPT.

Two distinct nits, both accepted:

**(a) PLAN source-block list incomplete.** The list at lines 36-38
named A1+C7, A5/W-AK, C2/W-LINT, W-29-prep, and CP6 application as
the v0.1.12 CARRY_OVER §3 named-defers, but the source table also
contained W-FBC-2 at line 59. W-FBC-2 was already accounted for in
the RELEASE_PROOF §5 inheritance row above, so it's not a missing
disposition — but the source block read as if v0.1.12 §3 had only
five rows. Fix: extended the list to name W-FBC-2 explicitly with
a note that it overlaps the RELEASE_PROOF §5 row and is
dispositioned in CARRY_OVER §1 + §2 per F-PLAN-02.

**(b) Bare F-PLAN-R2-04 token.** CARRY_OVER §2 line 35 quoted
v0.1.12 source text containing "F-PLAN-R2-04," which collides
with this cycle's F-PLAN-R2-04 (the W-AD path-prefix miss). The
quoted token referred to the v0.1.12 D14 round-2 finding, not the
v0.1.13 round-2 one. Fix: qualified the in-quote token as
"**v0.1.12 Codex F-PLAN-R2-04**" with explicit disambiguation
inline. The original quote is preserved in spirit; the
qualification just makes the cycle context unambiguous for any
future audit chain that walks F-PLAN-R2 citations.

This is the kind of nit that becomes a real provenance error if
v0.1.13 round-2's F-PLAN-R2-04 ever needs to be cited in a future
cycle's CARRY_OVER alongside the v0.1.12 one. Disambiguating now
prevents a future audit-chain error.

**Edit sites:** PLAN.md source block (line 36-38 expansion),
CARRY_OVER §2 W-FBC-2 row (in-quote disambiguation).

---

## What round 4 should re-verify (anti-self-introduced-regression)

Round 4 expectation: 0 findings → PLAN_COHERENT close. The
specific risks for round 4:

1. **F-PLAN-R3-01 propagation.** The W-Vb catalogue row at §1.2.A
   now enumerates 9 non-ship-set personas. Verify the enumeration
   matches the other 5 surfaces (no new drift between catalogue
   row and §1.3 / §2.A / §3 / §4 / CARRY_OVER §4). Quick spot-check:
   `grep -n "P2/P3/P6/P7/P8/P9/P10/P11/P12" reporting/plans/v0_1_13/`
   should show consistent enumeration across all hits.
2. **F-PLAN-R3-02 disposition tag consistency.** CARRY_OVER §1
   W-Vb row now says "partial-closure" — verify other partial-
   closure entries in this register use the same tag wording (the
   only other partial-closure shape in v0.1.13 is the W-CARRY
   surface naming, but those are in §5; v0.1.13 doesn't have other
   partial-closure inheritance items).
3. **F-PLAN-R3-03 source-block list completeness.** PLAN source
   block at lines 36-38 now names six rows from v0.1.12 CARRY_OVER
   §3 (A1+C7, A5/W-AK, C2/W-LINT, W-29-prep, CP6 application,
   W-FBC-2). Verify the v0.1.12 source actually has those six and
   not seven (i.e., I haven't missed another row).
4. **Round-marker timestamps.** Multiple rows in PLAN/CARRY_OVER
   now carry "F-PLAN-R3-NN" markers in addition to "F-PLAN-R2-NN"
   and "F-PLAN-NN" markers. Verify no surface still says "round 1"
   or "round 2" in a way that's now stale (e.g., the
   PLAN.md "Status" block status sentence was updated at round 2
   to say "round 1 closed"; round 3 close means it should now say
   "round 1 closed, round 2 closed, round 3 closed").

If round 4 returns 0 findings, the verdict should be PLAN_COHERENT
and the audit chain closes. If it returns 1-2 findings, those are
likely tertiary nits introduced by this round's revisions — fix
them and consider whether to run a round 5 or close PLAN_COHERENT
with notes. Per the empirical settling shape, 0 is the modal
outcome at round 4.

---

## Provenance — files modified in response to round 3

| File | Change shape | Codex finding(s) |
|---|---|---|
| `reporting/plans/v0_1_13/PLAN.md` | §1.2.A W-Vb row updated; source block expanded | F-PLAN-R3-01, R3-03(a) |
| `reporting/plans/v0_1_13/CARRY_OVER.md` | §1 W-Vb row disposition + notes; §2 W-FBC-2 row in-quote disambiguation | F-PLAN-R3-02, R3-03(b) |
| `reporting/plans/v0_1_13/codex_plan_audit_round_3_response_response.md` | This file | (response convention) |

All edits committed as a single commit on cycle/v0.1.13 alongside
this response. Branch state ready for D14 round 4.
