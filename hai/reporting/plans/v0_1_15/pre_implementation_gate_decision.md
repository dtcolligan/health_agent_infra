# v0.1.15 pre-implementation gate decision

**Cycle:** v0.1.15 (foreign-user candidate package + recorded gate).
**Phase:** Pre-implementation gate, fires after Phase 0 (D11) bug-hunt closes; before Phase 1 implementation opens.
**Authored:** 2026-05-03 evening.
**Status:** **OPEN for Phase 1 once D14 round 4 closes.** F-PHASE0-01 Option A revisions applied 2026-05-03 evening; round-4 codex prompt authored. **Q2 (foreign-user candidate) closed 2026-05-03 evening** — maintainer named the named foreign-user candidate as the named candidate. Path (a) — cycle proceeds without holding or downgrading. Phase 3 (W-2U-GATE recorded session) targets the candidate on file.

---

## §1. Gate inputs (per AGENTS.md D11 + D14 pattern)

Three things must be on file before the gate can fire green:

| Input | State | Source |
|---|---|---|
| `audit_findings.md` consolidated | ✅ DONE | `reporting/plans/v0_1_15/audit_findings.md` |
| Foreign-user candidate on file | ❓ UNKNOWN | maintainer to confirm; PLAN §4 risk 6 (F-PLAN-11) requires by Phase 0 close |
| OQ-7/8/9 ratifications | ✅ DONE in PLAN round 3 | PLAN §8 + `codex_plan_audit_round_3_response_response.md` |

## §2. Audit-findings disposition

Per `audit_findings.md` §4 summary:

- **Aborts-cycle count: 0.**
- **Revises-scope count: 1** (F-PHASE0-01 — W-C duplicates `target` table).
- **Nit count: 3** (F-PHASE0-02, F-PHASE0-03, F-PHASE0-04).
- **None count: 3** (F-PHASE0-AC-01 audit chain, F-PHASE0-AC-02 doctor WARN, persona matrix 13/13 clean).

**The cycle does not abort.** No P0-shaped blocker found in source verification, the audit chain, or the persona matrix.

**The cycle holds at this gate.** F-PHASE0-01 requires maintainer decision before Phase 1 opens because:

- W-C, W-A, W-D arm-1 all touch the chosen surface (existing `target` table vs new `nutrition_target` table).
- The cleaner-shape alternative (extend the existing `target` table) is *smaller* than the PLAN-as-written approach.
- The cleaner-shape alternative also dissolves PLAN §4 risk 2 (W-A ↔ W-C race + table-missing escape hatch) and removes one `OperationalError` catch-and-emit branch from W-A's read-side query.
- Choosing the duplicate-table path leaves the maintainer's *current* state DB in a self-mis-classification mode at v0.1.15 ship: three nutrition target rows already live in the existing `target` table; W-A's `target_status` query against `nutrition_target` would return `unavailable` and W-D arm-1 would fire suppression on a user who has clearly set targets.

## §3. Foreign-user candidate gate (PLAN §4 risk 6 + F-PLAN-11)

PLAN §4 risk 6 requires a named candidate on file by Phase 0 close. **This session cannot answer that question** — only the maintainer can. The decision tree if no candidate is named:

- **(a) Hold cycle open** — preferred. Continue persona-runner / dogfood work + apply F-PHASE0-01 revision; resume Phase 1 once a candidate is named.
- **(b) Downgrade to non-shipping candidate-package cycle** — ship Phase 1+2 fixes as v0.1.15 without the recorded session; defer W-2U-GATE to a new v0.1.16; re-D14 to formalize.
- **(c) Defer the gate entirely** — rename v0.1.15 + v0.1.16 + v0.1.17 with a new gate destination (e.g. v0.1.18).

**This document does NOT close the candidate-gate question.** It is surfaced for maintainer response in §6 below.

## §4. OQ ratification

PLAN §8 closed OQ-7 / OQ-8 / OQ-9 at D14 round 3 with Codex's recommended defaults ratified:

- **OQ-7** (`target_status="unavailable"` semantics): suppress is the v0.1.15 default. ✅
- **OQ-8** (gate-candidate tag shape): commit SHA only. ✅
- **OQ-9** (candidate-withdrawal mid-cycle procedure): pre-Phase-3 gate per PLAN §4.6 + mid-Phase-3 abort sentence. ✅

No fresh OQs surfaced from Phase 0 that need maintainer re-ratification — F-PHASE0-01's three options ARE a fresh OQ but it is a scope-revising decision, not a parameter ratification.

## §5. Nit-class fixes ready to apply at gate close

If the maintainer chooses F-PHASE0-01 Option A (preferred), all four nit-class items can land in the same PLAN edit:

1. **F-PHASE0-01 Option A revision** — rewrite §2.D to extend-existing-table; rewrite §2.B W-A query to read `target` not `nutrition_target`; remove §2.B parallelization escape hatch + §2.E acceptance test 4's "table-missing-because-pre-W-C" case; update §4 risks 1 + 2 + §5 effort table.
2. **F-PHASE0-02** — §2.A line 108 citation `cli.py:3041-3049` → `cmd_state_reproject` at `cli.py:4111`; `--cascade-synthesis` flag at `cli.py:8526`.
3. **F-PHASE0-03** — §2.A line 104 path `projectors/strength.py` → `core/state/projectors/strength.py:66`.
4. **F-PHASE0-04** — prepend SUPERSEDED-for-F-AV-03 header to `agent_state_visibility_findings.md` (mirror F-AV-01 supersede shape from round-2).

If Option B is chosen, only items 2-3 apply to the PLAN; item 1 is replaced by the duplicate-table justification + data-move migration; item 4 does not apply.

## §6. Maintainer decision needed (escalation)

Per `cycle_open_session_prompt.md` Step 6, this session escalates and holds. Two questions for the maintainer:

### Q1 — F-PHASE0-01 disposition

Choose one:

- **(A)** Revise PLAN §2.D to extend the existing `target` table (add `carbs_g` + `fat_g` to CHECK; ship `hai target nutrition` as a 4-atomic-row convenience macro; W-A reads `target`). Re-fire D14 round 4 against the revised §2.B + §2.D + §2.E + §4 + §5. Effort delta: −0.5d to −1d net.
- **(B)** Ship PLAN as-written with explicit duplicate-table justification + data-move migration for the existing nutrition rows in `target`. Re-fire D14 round 4 against the new §2.D justification + the data-move migration acceptance. Effort delta: +1d to +1.5d.
- **(C)** Maintainer has intent for `nutrition_target` that this finding is missing (e.g., richer schema for macro-cycling, periodization). Document inline; proceed.

### Q2 — Foreign-user candidate

Per PLAN §4 risk 6: is there a named candidate on file?

- **Yes** — provide identifier; cycle proceeds to Phase 1 once Q1 is answered.
- **No** — choose (a) hold open / (b) downgrade non-shipping / (c) defer the gate.

## §7. Until maintainer responds

Phase 1 implementation does not start. The gate is held. The audit chain is queryable, the test surface is intact, the wheel is buildable from main HEAD, and Phase 0 has produced an honest finding catalog. Holding the gate before implementation is the AGENTS.md-mandated path; D14 round 4 (if needed) is cheaper than untangling W-A / W-C / W-D after they ship against the wrong surface.

---

## §8. Provenance

- 2026-05-02 evening: D14 round 3 close-in-place per `codex_plan_audit_round_3_response.md`. PLAN final.
- 2026-05-02 evening: cycle-open prompt authored at `cycle_open_session_prompt.md` (commit `0bd534e`).
- 2026-05-03 evening: this session opened against the prompt; Phase 0 internal sweep + audit-chain probe + persona matrix executed.
- 2026-05-03 evening: F-PHASE0-01 surfaced from the internal sweep; persona matrix returned 13/13 clean; this gate-decision document authored.
- 2026-05-03 evening (post-maintainer-response): maintainer chose **F-PHASE0-01 Option A** ("Proceed based on your recommendations, I agree that revisions should be made"). PLAN revisions applied to §2.B / §2.D / §2.E / §4 / §5 / §1.2 / §1.3 / §1.4 / §3 / §8 / §9 / header. Three nit-class findings (F-PHASE0-02 / F-PHASE0-03 / F-PHASE0-04) applied at the same gate close. Cross-doc fan-out applied to README.md + tactical_plan_v0_1_x.md + agent_state_visibility_findings.md. See `audit_findings.md` §6 for the full disposition.
- 2026-05-03 evening: D14 round 4 codex audit prompt authored at `codex_plan_audit_round_4_prompt.md`. **NEXT:** maintainer fires Codex round 4; small-surface revision means single-round close expected (PLAN_COHERENT or 1-2 nits close-in-place). Q2 (foreign-user candidate) re-surfaces to maintainer before Phase 3 opens.
- 2026-05-03 evening: Q2 closed — maintainer named the W-2U-GATE foreign-user candidate. Path (a) confirmed; cycle proceeds without holding or downgrading. Phase 3 acceptance per PLAN §2.G targets this candidate.
