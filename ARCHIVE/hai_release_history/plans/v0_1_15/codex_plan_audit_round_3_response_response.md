# Maintainer Response — Codex Plan Audit Round 3

**Round 3 verdict:** PLAN_COHERENT_WITH_REVISIONS, 3 nit-class findings, **closed in-place** per round-3 prompt Step 4.
**Round 3 close:** 2026-05-03 with all 3 findings applied to PLAN final + minor cross-doc fan-out.
**Status:** **D14 closed.** Phase 0 (D11) bug-hunt opens next per the substantive-cycle pattern.

Halving signature held end-to-end: round 1 = 12, round 2 = 7, round 3 = 3. The cycle settles within the empirical norm (2-4 rounds for substantive PLANs).

---

## F-PLAN-R3-01 — PLAN §4 still uses old `target_present` contract

**Verdict:** AGREED, applied verbatim.

**Action.** PLAN §4 risks 1-2 rewritten to use the typed `target_status: "present" | "absent" | "unavailable"` enum that PLAN §2.B / §2.E already use. Risk 1 now correctly says W-D arm-1 fires on `target_status in ("absent", "unavailable")`. Risk 2 now describes the catch-and-emit-`unavailable` shape for the W-A read-side query when the `nutrition_target` table doesn't exist (pre-W-C migration), and explicitly names the four fixture cases for parallelization.

**Why this slipped.** I updated §2.B and §2.E correctly in round-2 but copy-pasted the old §4 risk language. Same fan-out failure mode as F-PLAN-03 round-1 (Settled Decisions vs Do Not Do) and F-PLAN-R2-02 round-2 (per-WS effort table). When updating a typed contract, future edits should `grep` for the old type-name across the whole PLAN, not just touch the implementation sections.

---

## F-PLAN-R3-02 — Gate contract still drifts in §2.G and tactical §5B

**Verdict:** AGREED, applied verbatim.

**Action.**
- PLAN §2.G "Candidate-package shape" replaced "post-merge to main, tagged commit" with "post-merge to main commit. Commit SHA recorded in the install record; no gate-candidate tag required." OQ-8 ratified per Codex round-3 opinion.
- Tactical §5B P-tier definitions rewritten to match PLAN §2.G: P0 explicitly includes acceptance-1 threshold breach (multiple interventions, maintainer keyboard time, >1 in-session question); P1 is reserved for trust-degrading findings within a threshold-met session; "cheap" excludes capabilities-manifest changes alongside state-model schema changes.

**Cross-doc fan-out.** Tactical §5B was the last surface still describing maintainer-intervention breach as P1; round-2 fixed PLAN §2.G but didn't propagate to tactical. Same shape as F-PLAN-R2-02 — when updating a load-bearing definition, propagate to every alternate view in one batch.

---

## F-PLAN-R3-03 — Final provenance and citation cleanup

**Verdict:** AGREED, applied verbatim with one shape extension.

**Action.**
- **PLAN header status:** updated from "D14 round-2 ready" to "D14 closed in-place at round 3." Removed the "15-slot" stray (the canonical accounting is 16 slots).
- **PLAN §9 provenance:** updated "deferred 8 W-ids + W-D arm-2" to "deferred 9 slots (W-D arm-2 + 8 others)" matching the canonical 16-slot accounting. Corrected the F-PLAN-R2-04 disposition line — round-2 added a SUPERSEDED header note to the findings doc, did NOT update the F-AV-01 in-doc example (preserves provenance per the maintainer disposition).
- **PLAN §4 nonexistent reference:** "F-PLAN-R2-11" replaced with "round-2 OQ-9 + Codex round-3 ratification" — this was a round-2 closing OQ, not a finding. The mid-Phase-3 abort sentence per Codex round-3 OQ-9 opinion appended to the §4.6 procedure.
- **Tactical §5B status:** updated from "D14 round-1 in flight" to "D14 closed in-place at round 3 (2026-05-03)." Halving signature noted.
- **Tactical §5D typo:** `w0.2.0` → `v0.2.0`.
- **PLAN §4.5 restore citation:** expanded from `cli.py:8588-8599` (parser flags only) to "handler at `cmd_restore` lines 4289-4321; parser flags lines 8588-8599 accept only `--bundle` / `--db-path` / `--base-dir`." Both ranges cited; the original `8588-8599` parser citation was useful but incomplete.

**Shape extension.** The §9 provenance entry for round 3 lists each F-PLAN-R3-NN by name, mirroring the round-1 + round-2 entries, so the audit chain remains queryable from the PLAN itself.

---

## Codex's OQ opinions all ratified

- **OQ-7 (`target_status="unavailable"` semantics):** suppress is the right v0.1.15 default per Codex. PLAN §2.E acceptance test 2 covers `unavailable` → `insufficient_data` outcome. No N-day blocker; host-agent prose can recommend setting a target if `unavailable` persists, but the gate doesn't fail closed.
- **OQ-8 (gate-candidate tag):** commit SHA only per Codex. PLAN §2.G now reads "commit SHA recorded in the install record; no gate-candidate tag required."
- **OQ-9 (candidate withdrawal mid-cycle):** pre-Phase-3 procedure right per Codex. Mid-Phase-3 abort case added as one sentence to PLAN §4.6 per Codex's recommendation: existing acceptance-1 threshold already fails (no full session reaches `synthesized`); archive partial transcript as non-gate evidence; fix/retry if product-side; re-enter §4.6 (a)/(b)/(c) if candidate is no longer available.

---

## Summary

3/3 findings applied. No new OQs raised. No round 4 needed.

**D14 closed in-place at round 3.** The cycle is open for Phase 0 (D11) bug-hunt:
- Internal sweep (substantive cycle pattern per AGENTS.md).
- Audit-chain probe.
- 12-persona matrix run against the post-W-A/C/D/E state model (round-2 PLAN §6 ship gate).
- Codex external bug-hunt audit (optional per maintainer).

Findings consolidate to `audit_findings.md`. Pre-implementation gate fires after Phase 0 closes; revises-scope findings may revise PLAN (loop back to D14); aborts-cycle findings may end the cycle. Otherwise PLAN.md opens the cycle and Phase 1 implementation begins.

**Empirical halving signature retrospective:** round-1 12 findings, round-2 7, round-3 3, round-4 not needed. Closure within 3 rounds at the lower band of the AGENTS.md 2-4 norm. Cycle restructure (round 0 16 slots → round 1 7 slots) was the largest scope shift but absorbed cleanly through the audit chain because the cuts were defensible against a stated objective ("foreign user reaches `synthesized`").
