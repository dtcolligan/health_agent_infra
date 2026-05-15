# v0.1.14 D14 Plan Audit — Round 2 Maintainer Response

**Round:** 2
**Codex verdict:** PLAN_COHERENT_WITH_REVISIONS
**Maintainer disposition:** ACCEPT 7 / PARTIAL-ACCEPT 0 / DISAGREE 0
**Action:** apply revisions in place across PLAN.md + tactical_plan +
5 CP files; close D14 round 2; await round-3 audit (verification
pass).

---

## Summary

7 findings, all accepted. Round-1 follow-through per Codex: 9 clean,
3 partial, 0 missed. Round-2 findings are entirely mechanical /
propagation / cross-reference fixes — no challenge to strategic
posture or scope. Settling shape: 12 → 7 (top of expected 5-7 band).
Round 3 expected: 0-2 findings.

The three partials Codex caught are exactly the second-order class
D14 round 2 was designed to surface:

- **F-PLAN-02 sizing** — body updated, metadata + tactical §5.3
  missed.
- **F-PLAN-10 W-30 schema-group** — AGENTS.md D4 + tactical §6/§9
  updated, CP-W30-SPLIT body delta missed.
- **F-PLAN-11 CP status** — top header updated, bottom "Round-N
  codex verdict" footers missed.

These are exactly the kind of summary-surface-sweep failures the
post-v0.1.13 strategic-research round 2 also caught (F-RES-R2-04
CALM, F-RES-R2-05 Apple appendix label). Confirms the AGENTS.md
"Summary-surface sweep on partial closure" pattern is a real blind
spot; the eventual W-FRESH-EXT (P1) test extension should encode
some of these checks mechanically.

---

## Per-finding disposition

### F-PLAN-R2-01 — 32-45 sizing didn't reach all surfaces

**Disposition:** ACCEPT.

**Verification:**
- PLAN.md line 8 metadata still says `Estimated effort: 30-40 days`.
- tactical_plan §5.3 lines 474-480 still says `30-40 days. ... round
  to 30-40 days with contingency.`
- PLAN body (§1.2 + §5) was correctly updated to 32-45.

**Action:**
- PLAN.md line 8: `30-40 days` → `32-45 days`.
- tactical_plan §5.3: rewrite to match PLAN §5 — 32-45 envelope,
  31.5-44.5 arithmetic note, 45-day scope-cut trigger.

### F-PLAN-R2-02 — CP-W30-SPLIT proposed delta omits W58D claim-block

**Disposition:** ACCEPT.

**Verification:** CP-W30-SPLIT.md "Proposed delta — AGENTS.md D4"
section (lines 63-69) still proposes "W52 v0.2.0, W53 v0.2.1, W58J
v0.2.2" — the original wording before F-PLAN-10. AGENTS.md and
tactical §6/§9 reflect the corrected wording, but the CP body that
documents the delta is now internally inconsistent with the actually-
applied delta.

**Action:**
- CP-W30-SPLIT.md "Proposed delta — AGENTS.md D4" body: update to
  include W58D claim-block, matching the now-applied AGENTS.md text
  exactly: "W52 + W58D claim-block (v0.2.0), W53 (v0.2.1), W58J
  (v0.2.2)".

### F-PLAN-R2-03 — 5 CP files have stale "Round-N codex verdict pending" sections

**Disposition:** ACCEPT.

**Verification:** F-PLAN-11 updated the top `**Codex verdict:**`
header field in all 5 CP files. But each CP file also has a footer
section titled "Round-N codex verdict" with body text "pending — CP
not yet submitted to Codex review" — left unchanged. Internal
contradiction between header (applied at v0.1.14 D14 round 1) and
footer (pending).

**Action:** for each of 5 CP files, replace the footer "Round-N codex
verdict" section with the same applied-status text as the header,
or delete the footer section entirely. Choosing to **replace** for
audit-chain traceability (the round-1 application + round-2
correction history is preserved).

### F-PLAN-R2-04 — Candidate-absence gate timing too early

**Disposition:** ACCEPT.

**Verification:** PLAN §1.3.1 says "candidate must be on file by
**Phase 0 gate**." But Phase 0 (D11 bug-hunt: internal sweep,
audit-chain probe, 12-persona matrix) does not depend on a foreign
user — only W-2U-GATE (the first implementation workstream after
Phase 0 + pre-implementation gate) does. Requiring the candidate
before Phase 0 unnecessarily blocks a useful bug-hunt that could
otherwise run.

**Action:**
- §1.3.1 hard rule: "candidate by **Phase 0 gate**" → "candidate by
  the **pre-implementation gate**, before W-2U-GATE opens."
- §1.3.1 option 1 ("Hold the cycle. Defer Phase 0 until a
  candidate surfaces") → "Hold W-2U-GATE / implementation. Phase 0
  bug-hunt may proceed; pre-implementation gate withholds
  implementation start until candidate surfaces or option 2/3
  fires."
- §2.A candidate-absence reference updated accordingly.

### F-PLAN-R2-05 — D14 round-count rescope cross-references stale

**Disposition:** ACCEPT.

**Verification:**
- PLAN §4 risks row "D14 exceeds 5 rounds" mitigation references
  "§1.3 sequencing constraint + §1.3.1 candidate-absence procedure"
  — but §1.3.1 is about candidate absence, not round count. The
  actual round-count gate lives in §3 ship gate + §5 D14 expectation.
- PLAN §6 line 495: "per §1.4 acceptance" — but §1.4 is the
  deferrals table, not an acceptance section. Acceptance lives in
  §3 ship gate.

**Action:**
- §4 risks "D14 exceeds 5 rounds" mitigation: drop §1.3.1 reference;
  point to §3 ship gate + §5 D14 expectation.
- §6 line 495: "per §1.4 acceptance" → "per §3 ship gate".

### F-PLAN-R2-06 — Reconciliation citation file-path ambiguity

**Disposition:** ACCEPT.

**Verification:** PLAN §2.B says "Reconciliation §4 C10 named this
as non-deferrable." tactical_plan §6.1 says "carrier:
`recommendation_evidence_card.v1` schema per reconciliation C8."
But there are now **two reconciliation files**:

- `reporting/plans/post_v0_1_13/reconciliation.md` (post-v0.1.13
  audit chain, which I authored)
- `reporting/plans/future_strategy_2026-04-29/reconciliation.md`
  (the original Claude/Codex deep-strategy review with C1..C10 rows)

The C8/C10 rows live in the **2026-04-29** file, not the post-v0.1.13
file. The unqualified "Reconciliation §4 C10" in PLAN.md ambiguously
points to either, and the post-v0.1.13 file doesn't have C-rows so
the unqualified citation fails verification against the wrong file.

**Action:**
- PLAN §2.B: "Reconciliation §4 C10" → "`reporting/plans/future_strategy_2026-04-29/reconciliation.md` §4 C10".
- tactical_plan §6.1: "reconciliation C8" → "`reporting/plans/future_strategy_2026-04-29/reconciliation.md` §4 C8".

### F-PLAN-R2-07 — tactical §11.3 mixes verdict scales

**Disposition:** ACCEPT.

**Verification:** tactical_plan §11.3 (after F-PLAN-07 renumber)
reads: "External audit of PLAN.md + working tree state. Verdict:
SHIP / SHIP_WITH_NOTES / DO_NOT_SHIP." But this section is part of
the v0.1.x release pattern playbook describing the **D14 PLAN
audit**, which uses `PLAN_COHERENT / PLAN_COHERENT_WITH_REVISIONS /
PLAN_INCOHERENT` (per AGENTS.md D14, lines 223-225). SHIP /
SHIP_WITH_NOTES is the **implementation review (IR) verdict scale**
that fires *after* the cycle opens.

The renumber landed; the verdict-scale content was inherited from
the pre-D14-decision template and never updated when D14 settled
at v0.1.11.

**Action:**
- tactical_plan §11.3: rewrite to split D14 PLAN-audit (PLAN_COHERENT
  scale) from IR rounds (SHIP scale). The D14 phase comes first;
  IR rounds come after the cycle opens.

---

## Summary-surface sweep (per AGENTS.md "Summary-surface sweep on partial closure")

Round 2 fixes propagation gaps from round 1. The sweep:

| Surface | Change |
|---|---|
| PLAN.md line 8 metadata | 30-40 → 32-45 days (R2-01) |
| PLAN.md §1.3.1 hard rule | "Phase 0 gate" → "pre-implementation gate, before W-2U-GATE opens" (R2-04) |
| PLAN.md §1.3.1 option 1 | Phase 0 may proceed; implementation held (R2-04) |
| PLAN.md §2.A candidate-absence ref | mirror §1.3.1 update (R2-04) |
| PLAN.md §2.B citation | qualify with full path `future_strategy_2026-04-29/reconciliation.md §4 C10` (R2-06) |
| PLAN.md §4 risks "D14 exceeds 5 rounds" | drop §1.3.1 ref; point to §3 + §5 (R2-05) |
| PLAN.md §6 line 495 | "per §1.4 acceptance" → "per §3 ship gate" (R2-05) |
| tactical §5.3 | 30-40 → 32-45 days; arithmetic note + 45-day scope-cut (R2-01) |
| tactical §6.1 | qualify "reconciliation C8" with full path (R2-06) |
| tactical §11.3 | split D14 / IR verdict scales (R2-07) |
| CP-W30-SPLIT body delta | add W58D claim-block to D4 proposed text (R2-02) |
| 5 CP files Round-N footer sections | replace "pending" with applied status (R2-03) |

---

## Round-3 expectations

Round 1: 12 findings. Round 2: 7. On track for 0-2 round 3, then
close at PLAN_COHERENT.

Round 3 should catch:

- Any propagation gap from this round (e.g., the §1.3.1 timing fix
  must propagate consistently across §2.A, §4 risks, §6, and the
  candidate-absence procedure body).
- The §11.3 verdict-scale split — verify the new wording reads
  coherently against AGENTS.md D14 + IR phase descriptions.
- Spot-check 5+ remaining citations not covered in r1 or r2.

Expected yield: **0-2 findings**. PLAN's ≤5-round acceptance gate
holds; on track to close at round 3 (= 4 rounds total, mid-band of
the 4-5 expected).

---

## Open questions answered (none)

Codex round-2 response did not surface new open questions for the
maintainer. All 7 findings have unambiguous acceptance paths. Round
3 will verify the revisions land cleanly.
