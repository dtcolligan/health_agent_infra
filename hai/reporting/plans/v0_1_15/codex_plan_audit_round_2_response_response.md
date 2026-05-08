# Maintainer Response — Codex Plan Audit Round 2

**Round 2 verdict:** PLAN_COHERENT_WITH_REVISIONS (7 findings, halving signature held: 12 → 7 → projected 2-4 at round 3).
**Round 2 close:** 2026-05-03 with all 7 findings applied to PLAN.md round 3 + cross-doc fan-out.
**Status:** ready for Codex D14 round-3 audit against the revised PLAN.

This file records per-finding triage. Round-1 closure verification (Codex's table at the top of the round-2 response) confirmed F-PLAN-03 + F-PLAN-09 fully CLOSED; the other 10 round-1 findings were CLOSED_WITH_RESIDUAL or NOT_CLOSED — those residuals collapse into the 7 new round-2 findings below.

---

## F-PLAN-R2-01 — `target_present` not a coherent W-A/W-D contract

**Verdict:** AGREED, applied verbatim.

**Action.** Replaced the type-mixing `target_present: bool` (which I'd then said could also be `"unavailable"` — a string, not a bool) with a typed three-valued enum: `target_status: "present" | "absent" | "unavailable"`. PLAN §2.B output contract spells out each value's meaning. PLAN §2.E W-D arm-1 fires on `is_partial_day && target_status in ("absent", "unavailable")`. Acceptance now covers four fixture states (present / absent / unavailable / table-missing-pre-W-C-migration).

**Default behavior on `unavailable` (raised as new OQ-7).** Treating `unavailable` as a no-target trigger (suppress) for v0.1.15. Codex's recommendation surfaced this as an open question; I picked "suppress" because the foreign user shouldn't hit a hard fail before they've set targets. Reversible to fail-closed if maintainer prefers.

---

## F-PLAN-R2-02 — Effort reconciliation still inconsistent across summary surfaces

**Verdict:** AGREED, applied verbatim with full cross-surface propagation.

**Action.** F-PLAN-08 round-1 fix updated PLAN header + §5 arithmetic table but missed §1.2 catalogue, v0_1_15/README.md, and tactical §5B. Round-3 propagates: all four surfaces now show 16-25 days + 2-4 D14 rounds, with W-GYM-SETID at 1.5-3d and W-2U-GATE at 4-7d in every per-WS table.

**Why this missed in round 1.** I updated the per-WS arithmetic table thinking it was the source of truth, without realizing the catalogue table at §1.2 had its own per-WS column that was independent. Same shape as F-PLAN-03 round-1 miss (Settled Decisions vs Do Not Do). Both are "I edited the canonical surface and didn't propagate to the alternate-views." Memory note: when the same fact appears in multiple tables, edit all of them in one batch.

---

## F-PLAN-R2-03 — Provenance accounting still mixes 14, 15, 16-slot stories

**Verdict:** AGREED, applied verbatim.

**Action.** Picked one accounting sentence: **"16 catalogued slots = 7 kept (v0.1.15) + 9 deferred (v0.1.17). W-D counted as two slots (arm-1 + arm-2) because the arms ship in different cycles."** Applied to PLAN §1.4 prose, v0_1_15/README.md "Scope provenance" section, v0_1_17/README.md provenance paragraph. AGENTS.md citation fixed to point to PLAN §4 item 8 (was incorrectly §4.6).

**Disagreement note.** None — Codex's accounting recommendation matched what I'd intended; the round-1 fix had ambiguous prose around the table.

---

## F-PLAN-R2-04 — Source findings doc still contradicts the W-A predicate split

**Verdict:** AGREED, applied with shape extension.

**Action.** Added a "SUPERSEDED for cycle scoping" + "W-A predicate is also superseded" header note at the top of `post_v0_1_14/agent_state_visibility_findings.md`. The note cites PLAN round-3 §2.B as the source of truth for the W-A output contract. Did NOT rewrite the F-AV-01 example output in-place because the doc's value is original-finding provenance — rewriting the example would erase the audit trail of how the W-A contract evolved. The header note explicitly tells future readers "PLAN.md is canonical; this doc is provenance."

**Cross-doc fan-out.** No further fan-out needed — the findings doc is referenced by PLAN.md and v0_1_17/README.md but the supersede note covers both reading paths.

---

## F-PLAN-R2-05 — P0/P1 gate semantics overlap

**Verdict:** AGREED, applied with structural reframing.

**Action.** Clarified the P0/P1 boundary per Codex's recommendation: **any breach of the §2.G acceptance-1 session threshold (multiple interventions / maintainer keyboard time / >1 in-session question) is P0**, not P1. P1 is reserved for trust-degrading findings that occur **within** a threshold-met session. The overlap was real — round-2 PLAN had both tiers naming "user notices trust loss" with slightly different qualifiers. Round-3 PLAN §2.G now states: "All P1 findings occur within a session that satisfies acceptance-1; if the threshold is breached, that's P0, not P1."

**"Cheap" extension.** Per Codex: capabilities-manifest changes are now explicitly excluded from the "cheap" inline-fix budget (same tier as state-model schema changes). PLAN §2.G updated. Rationale: the capabilities manifest is the agent-contract surface; changes there propagate to every consumer and deserve the audit overhead.

---

## F-PLAN-R2-06 — F-PV14-02 interim cleanup names a nonexistent selective restore

**Verdict:** AGREED, applied verbatim. Most embarrassing finding of round 2.

**Action.** Replaced "selective `hai restore`" with the actual options: full point-in-time restore from `hai backup` bundle (verified against `cli.py:8588-8599` — `hai restore` accepts only `--bundle` / `--db-path` / `--base-dir`), OR leave cosmetic `sync_run_log` rows in place until F-PV14-02. Raw SQL DELETE remains prohibited. PLAN §4.5 now cites the CLI source range explicitly so a future reader can verify.

**Memory entry saved.** `feedback_verify_cli_surface_before_recommending.md` — when authoring operator procedures, run `hai <cmd> --help` first to verify the surface exists. This was the same failure mode as the v0.1.15 round-0 stale-tree mistake (asserting facts without verification).

---

## F-PLAN-R2-07 — Candidate-package details not carried into ship gates and tactical acceptance

**Verdict:** AGREED, applied verbatim.

**Action.** PLAN §6 ship gates now restate the full §2.G W-2U-GATE contract: acceptance-1 threshold, P0/P1/P2 disposition, candidate-package shape, install record, transcript, state DB snapshot. Tactical §5B archive bullet now includes the install record path. Picked "commit SHA only" over "non-release gate-candidate tag" per Codex's options (raised as OQ-8 for maintainer ratification — see PLAN §8).

**Why commit SHA over tag.** The install record carries the SHA; a non-release tag adds bookkeeping (when to delete, what to do if the gate session needs re-running) without giving any verification benefit beyond the SHA. Reversible if maintainer prefers a gate-candidate tag for human-readability.

---

## Summary

7/7 findings applied. No disagreement-with-reason; one shape extension (F-PLAN-R2-04 added a header supersede note instead of rewriting the F-AV-01 example in-place — preserves audit trail).

**Codex's OQ opinions all ratified:**
- OQ-1 (W-B pull-forward) — defer per Codex; reversible if Phase 0 candidate workflow needs body-weight persistence.
- OQ-5 (round-0 self-audit pattern as D-entry) — do NOT promote yet; record as pattern at v0.1.15 ship.
- OQ-6 (foreign-device OS) — single OS sufficient; install record carries OS + Python + shell + env hash.

**New OQ-7/8/9 raised by round 2 (need maintainer ratification before round-3 close):**
- OQ-7: `target_status="unavailable"` semantics — confirm "treat as no-target / suppress" default.
- OQ-8: gate-candidate tag — confirm "commit SHA only" choice.
- OQ-9: candidate-withdrawal mid-cycle — confirm the §4.6 procedure-reentry sentence.

**Round-3 expected verdict.** PLAN_COHERENT (likely) or PLAN_COHERENT_WITH_REVISIONS with ≤3 nit-class findings. Round-3 PLAN_COHERENT_WITH_REVISIONS at ≤3 may close in-place per the round-2 prompt's Step 4 ("If finding count is ≤ 3 and severity ≤ acceptance-criterion-weak, the maintainer may close in-place without round 4").

**Pending maintainer action before D14 round-3 prompt fires:**
- Ratify OQ-7 / OQ-8 / OQ-9 defaults (or override with rationale).
- Confirm round-3 audit prompt regeneration (mirrors round-2 prompt structure with round-3-specific framing).
