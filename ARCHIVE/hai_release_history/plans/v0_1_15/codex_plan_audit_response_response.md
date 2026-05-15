# Maintainer Response — Codex Plan Audit Round 1

**Round 1 verdict:** PLAN_COHERENT_WITH_REVISIONS (12 findings).
**Round 1 close:** 2026-05-03 with all 12 findings applied to PLAN.md round 2 + cross-doc fan-out.
**Status:** ready for Codex D14 round-2 audit against the revised PLAN.

This file records per-finding triage so an auditor can cross-reference the round-1 response against the round-2 PLAN without re-deriving the disposition.

---

## F-PLAN-01 — W-D arm-1 unreachable under W-A's predicate

**Verdict:** AGREED, applied verbatim.

**Action.** Split W-A's predicate per Codex's recommendation. PLAN.md §2.B now defines `is_partial_day` as time/intake-only (`(local_now < end_of_day_cutoff) AND (meals_count < expected_for_day_complete)`) and adds a separate `target_present` field returned by querying `nutrition_target` (W-C's table). PLAN.md §2.E W-D arm-1 fires on `is_partial_day == true && target_present == false`. Three new acceptance tests cover the split.

**Cross-doc fan-out.** Risk note §4.1 updated to reflect the split. Sequencing §1.3 unchanged (W-A and W-C still parallelizable in Phase 1; W-A's `target_present` query handles the W-C-empty case via `target_present: "unavailable"`).

---

## F-PLAN-02 — Tactical detailed sections still describe the rejected split

**Verdict:** AGREED, applied with shape extension.

**Action.** Rewrote `tactical_plan_v0_1_x.md` §5B (v0.1.15 — now combined gate cycle), §5C (v0.1.16 — now empirical post-gate bug fixes), and added §5D (v0.1.17 — maintainability + eval consolidation). Detail sections now match the post-restructure rows 46-48 + horizon paragraph that landed in the round-1 fan-out.

**Cross-doc fan-out.** §5B/§5C/§5D now self-consistent with PLAN.md and v0.1.17/README.md. §6 (v0.2.0) was not touched — its row already correctly states "NOT dependent on v0.1.17."

---

## F-PLAN-03 — AGENTS.md Do Not Do schedules cli.py split for v0.1.15

**Verdict:** AGREED, applied verbatim.

**Action.** AGENTS.md "Do Not Do" lines 416-420 updated to reference `(v0.1.17 / v0.2.3)` and inherited the same provenance chain as the Settled Decisions D124-135 entry (mid-day v0.1.15 destination → evening v0.1.17 redestination, with rationale).

**Note.** This finding caught a real cross-doc miss in the round-1 fan-out — only Settled Decisions was updated, not the parallel "Do Not Do" entry. Round-2 PLAN's §1.4 provenance table now mentions both AGENTS.md surfaces explicitly to prevent recurrence.

---

## F-PLAN-04 — Round-0 provenance arithmetic doesn't reconcile

**Verdict:** AGREED, applied with shape extension.

**Action.** Added a 16-row disposition table to PLAN.md §1.4 listing every round-0 catalogued slot with kept/cut destination + reason. Reconciliation: 16 slots = 7 kept (v0.1.15) + 9 deferred (v0.1.17, including W-D arm-2). All slots accounted for; no orphans.

**Disagreement with Codex's count.** Codex's response said "14 W-ids" in one place and "8 deferred" in another (per the original PLAN's text — the original PLAN was inconsistent). The round-2 reconciliation lands on 16 catalogued slots; the original "14 W-ids" claim was the round-0 PLAN's mis-count, which the round-2 disposition table now corrects.

**Did not preserve a separate `round_0_draft.md`.** The provenance table inside PLAN.md travels with the cycle and is durable; a separate draft would duplicate. If Codex round-2 disagrees and wants a separate file, easy revision.

---

## F-PLAN-05 — W-2U-GATE acceptance dropped v0.1.14 hard threshold

**Verdict:** AGREED, applied verbatim with extension.

**Action.** PLAN.md §2.G W-2U-GATE acceptance restored the v0.1.14 PLAN §2.A "one full session reaches `synthesized` with at most one brief in-session question; multiple interventions or any maintainer keyboard time = failure" load-bearing threshold (was silently weakened in round-1 PLAN). Added explicit P0/P1/P2 definitions and the "cheap" threshold (≤0.5 maintainer-day, no D14 re-run, no state-model schema touch).

**Cross-doc fan-out.** `tactical_plan_v0_1_x.md` §5B.2 now references the same threshold + P-tier definitions. v0.1.16's tactical row 47 says P1 picks up "named-deferred" findings; round-2 PLAN's "close inline if cheap, else defer" makes the boundary explicit so the v0.1.16 / v0.1.15 split of P1 work is unambiguous.

---

## F-PLAN-06 — "Candidate package" not defined as a package artifact

**Verdict:** AGREED, applied verbatim.

**Action.** PLAN.md §2.G now specifies: build wheel + sdist from the final v0.1.15 branch (post-merge to main, tagged commit). Install the wheel into a clean Python 3.11+ environment on the foreign device. Record exact version + commit SHA. No editable installs, no PyPI pre-release.

**Cross-doc fan-out.** §2.G files-of-record adds `verification/dogfood/foreign_user/install_record_<YYYY-MM-DD>.json` for the version/commit/install-command/environment-hash record.

---

## F-PLAN-07 — W-GYM-SETID migration acceptance assumes a fixture and a non-SQL recovery path

**Verdict:** AGREED, applied with scope split.

**Action.** PLAN.md §2.A rewritten to split:
- **Schema/data migration (in-scope):** SQL-only — rewrite `set_id` PKs for rows already in `gym_set`, preserve supersession chains in-SQL.
- **JSONL-recovery (out of scope; operator path):** documented as the maintainer's pre-gate procedure (`hai backup` → `hai state reproject --cascade-synthesis` → `hai synthesize`). Foreign user starts fresh, so doesn't apply.
- **Required fixture (no longer "if any"):** `verification/tests/fixtures/multi_exercise_session.jsonl` (4-exercise, 11-set leg+back fixture) authored as part of the WS.

**Sizing impact.** W-GYM-SETID effort widened from 1-2d to 1.5-3d in §5 to absorb fixture authoring + JSONL-recovery acceptance test + backup round-trip test.

**Cross-doc fan-out.** PLAN.md §4.3 documents the maintainer pre-gate procedure (backup + reproject + re-synthesize). Tactical §5B unchanged (the split is internal to the WS).

---

## F-PLAN-08 — Effort headline contradicts the PLAN's own arithmetic

**Verdict:** AGREED, applied with reconciliation.

**Action.**
- Single headline range: **16-25 days** (was 14-20 / 13-22 / 14-18-23 in three different places).
- §5 effort table updated with explicit per-WS Δ vs round-1 sizing, summing to 14.5-19-25 best/mid/worst, adjusted to 16-20-26 with coordination overhead, headlined as 16-25.
- D14 expectation widened from "2-3 rounds" to "budget 2-4 rounds; round 1 = 12 findings; round 2 should drop to 4-7 if halving signature holds." Per AGENTS.md lines 201-208 + 351-357.

**Sizing additions.** W-GYM-SETID +0.5/+0.5/+1d (per F-PLAN-07). W-2U-GATE +1/+1/+2d (foreign-user coordination + inline P0/P1 fix risk + threshold-restoration session-rigor budget).

**Cross-doc fan-out.** v0.1.15/README.md effort line updated (was "14-20 days") to match. Tactical §5B.3 updated to match (was "13-22 days").

---

## F-PLAN-09 — W-E requires a weigh-in token while W-B is deferred

**Verdict:** AGREED, applied with surfaced OQ for maintainer call.

**Action.** PLAN.md §2.F W-E acceptance now explicitly excludes `weigh_in` from the required `present.*.logged` check. W-A emits `weigh_in: {logged: false, reason: "intake_surface_not_yet_implemented"}` consistently in v0.1.15. The morning-ritual skill (optional W-E component) verbalizes a weigh-in prompt without expecting state-write.

**OQ-1 raised for maintainer.** If the foreign-user gate exposes friction without canonical weigh-in (e.g., user really wants to log a weigh-in in their first session), pull W-B forward into v0.1.15. PLAN documents this as reversible.

**Cross-doc fan-out.** v0.1.17/README.md unchanged (W-B still in scope there). Round-2 PLAN's §4 risks would need a new entry only if W-B is pulled forward; current shape doesn't require it.

---

## F-PLAN-10 — F-PV14-01 / F-PV14-02 split drops the source doc's paired-cleanup warning

**Verdict:** AGREED, applied verbatim.

**Action.** PLAN.md §4.5 added: "F-PV14-02 deferred — interim cleanup procedure." Names the residual risk (recurrence between F-PV14-01 prevention and F-PV14-02 cleanup tool) and the operator's sanctioned cleanup paths (`hai backup` + selective `hai restore`, OR leave cosmetic `sync_run_log` rows in place). Raw SQL DELETE remains prohibited per AGENTS.md Do Not Do.

**Foreign-user blast radius assessment.** Low — F-PV14-01 prevents new contamination; existing contamination only affects maintainer's state, not the foreign-user's fresh DB. Documented in §4.5.

---

## F-PLAN-11 — Candidate-absence procedure no longer maps cleanly

**Verdict:** AGREED, applied with v0.1.15-specific procedure.

**Action.** PLAN.md §4.6 rewritten with v0.1.15-specific candidate-absence procedure:
- Hard rule: candidate on file by **Phase 0 close** (D11 bug-hunt complete, before Phase 1 opens).
- Three options if absent at Phase 0 close: (a) hold cycle open, (b) downgrade to non-shipping candidate-package cycle (re-D14), (c) defer the gate to v0.1.18 with cycle renaming. Path (a) preferred.
- Note: more aggressive than v0.1.14 path 2 because v0.1.15's W-2U-GATE is the ship claim, not a Phase 1 workstream.

**Cross-doc fan-out.** Tactical §5B.4 unchanged (high-level strategic context); §4.6 in PLAN is the operative procedure.

---

## F-PLAN-12 — Dual-repo mitigation is prompt-local, not durable

**Verdict:** AGREED, applied verbatim.

**Action.** AGENTS.md "Authoritative orientation" preamble now declares the active repo path explicitly: "This contract applies to checkouts at `/Users/domcolligan/health_agent_infra/`. A stale checkout exists at `/Users/domcolligan/Documents/health_agent_infra/` (months behind, head at commit `2811669 Phase H: implement conversational intake`); ignore it unless explicitly working on historical provenance. Every session should `pwd` and `git log -1` before reading or writing planning/source files." Cites PLAN §4.6 + this finding's number for provenance.

**Cross-doc fan-out.** D14 audit prompt Step 0 unchanged (per-prompt check stays as the active-runtime guard); AGENTS.md addition is the durable operating-contract layer.

---

## Summary

12/12 findings applied. No disagreement-with-reason; one shape extension (F-PLAN-04 used in-PLAN table instead of separate draft file). One open question raised for maintainer (OQ-1 — pull W-B forward or accept verbalize-without-state-write).

**Round-2 expected verdict.** PLAN_COHERENT or PLAN_COHERENT_WITH_REVISIONS with 4-7 nit-class findings (per the empirical halving signature). Cross-doc consistency was the largest round-1 surface; round-2 should focus on per-WS contract rigor (especially W-2U-GATE acceptance bite under the new P-tier definitions).

**Pending maintainer ratification before Phase 0 opens:**
- OQ-1: W-B pull-forward decision.
- OQ-5: Round-0 self-audit pattern → AGENTS.md D-entry CP.
- OQ-6: Foreign-device OS choice (Mac / Windows / Linux).
