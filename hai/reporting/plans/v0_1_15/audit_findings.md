# v0.1.15 Phase 0 (D11) bug-hunt — audit findings

**Cycle:** v0.1.15 (foreign-user candidate package + recorded gate).
**Tier:** substantive.
**Phase:** Phase 0 (D11) bug-hunt, opens after D14 close-in-place at round 3 (2026-05-03 afternoon).
**Authored:** 2026-05-03 evening, fresh Claude session opened against `cycle_open_session_prompt.md`.
**Active repo:** `/Users/domcolligan/health_agent_infra` (verified per AGENTS.md "Active repo path"). HEAD `0bd534e` (cycle-open prompt) at session start.

## Phase 0 scope executed

Per AGENTS.md D11 substantive-cycle pattern + `cycle_open_session_prompt.md` Step 2:

- **Internal sweep** — re-read PLAN.md against the active source tree; spot-check every cited file path, line range, function name, and proposed-fix shape against `git ls-files` reality. Verify no scope leaked from v0.1.16 / v0.1.17. **DONE.**
- **Audit-chain probe** — `hai explain --as-of 2026-04-30 --user-id u_local_1 --operator` against the maintainer's live state DB; verify proposal_log → planned_recommendation → daily_plan + recommendation_log + review_outcome chain renders end-to-end. **DONE — chain queryable, no structural gaps.**
- **Persona matrix (P1..P12, optionally P13)** — `verification/dogfood/runner` against the post-v0.1.14.1 wheel. Runner is monolithic (no persona filter) so the full P1..P13 matrix runs; P7..P12 findings are advisory per PLAN §6. **IN-FLIGHT at the time of writing; results appended to §3 below when complete.**
- **Codex external bug-hunt audit** — optional per maintainer at substantive tier; default is skip when D14 closed in 3 rounds with halving signature held. **SKIPPED** (no maintainer request to fire).

## Cycle-impact tag legend

Per AGENTS.md D11 pattern:

- `aborts-cycle` — finding is bad enough that the cycle should not proceed; maintainer escalation required.
- `revises-scope` — finding requires a PLAN.md edit material enough that D14 should re-fire (loop back to round 4 if the revision is large; in-place text-only edit otherwise).
- `nit` — citation imprecision, typo, stale prose. Apply in-place at pre-implementation gate; no D14 re-fire.
- `none` — observation only, no PLAN action.

---

## §1. Internal sweep findings

### F-PHASE0-01 — W-C `nutrition_target` table duplicates existing `target` table infrastructure

**Cycle impact:** **revises-scope** — material enough that the maintainer should choose between table-reuse vs new-table before Phase 1 opens. Either path is implementable; the cleaner-shape choice is not the maintainer's stated path in PLAN §2.D.

**Severity:** ship-impact-coupled (the choice cascades into W-A's read-side query in §2.B and into how W-D arm-1 in §2.E queries `target_status`).

**Reference:**
- PLAN §2.D (W-C contract, lines 143-148)
- PLAN §2.B (W-A `target_status` query, lines 130-134)
- `src/health_agent_infra/core/state/migrations/020_target.sql` (existing target table, lines 15-59)
- `src/health_agent_infra/cli.py:2668-2843` (`cmd_target_set / cmd_target_list / cmd_target_commit / cmd_target_archive`)
- `src/health_agent_infra/cli.py:7987` (`--domain` flag accepts "nutrition")
- Live state evidence: `hai target list --user-id u_local_1 --all` returns three nutrition rows already on disk (`calories_kcal=3300` archived, `calories_kcal=3100` active, `protein_g=160` active), all `agent_proposed → committed`, demonstrating the existing W57 path works for nutrition targets.

**Argument.** PLAN §2.D proposes a NEW `nutrition_target` table + migration + `hai target nutrition --kcal --protein-g --carbs-g --fat-g --phase --effective-from` command. But migration `020_target.sql` already defined a generic `target` table four cycles ago whose schema is a near-perfect superset:

- `target_type` CHECK already includes `'calories_kcal'`, `'protein_g'`, `'sleep_duration_h'`, `'training_load'`, etc. **Missing:** `'carbs_g'`, `'fat_g'`. Adding two values to the CHECK is a one-line migration.
- `status` CHECK already includes `'proposed', 'active', 'superseded', 'archived'` — exact match for PLAN §2.D's required lifecycle.
- `supersedes_target_id` / `superseded_by_target_id` columns + `idx_target_supersedes` index already implement the supersession discipline PLAN §2.D requires.
- W57 commit gate already shipped: `cmd_target_commit` at `cli.py:2790-2823` invokes `_w57_user_gate`. `agent_proposed` rows stay `proposed` until explicit user commit.
- `domain="nutrition"` is already a first-class value of the `domain` column.

The maintainer is *currently using* this pathway in their live state. The two active rows visible in `hai target list` were committed via the existing surface; agent-proposed; W57-gated; survived to `active`. There is no functional gap that motivates a new parallel table.

**Practical consequence of the duplicate-table approach (PLAN as-written).** Two read surfaces for "what is the user's nutrition target?": the existing `target` table (where current production data lives) AND the new `nutrition_target` table. W-A's `target_status` query in PLAN §2.B reads `nutrition_target` only (line 132). On the live DB at v0.1.15 ship, W-A would return `target_status="unavailable"` even though three nutrition target rows exist in `target`. W-D arm-1 would then fire suppression on a user who has set targets. Foreign-user blast radius depends on whether they migrate any state, but the maintainer's own state would self-mis-classify on day one.

**Cleaner alternative.** Extend the existing `target` table:

1. Migration 024 — `ALTER TABLE target` to extend the `target_type` CHECK with `'carbs_g'` and `'fat_g'` (SQLite requires recreate-and-copy; the migration shape is already standard for this codebase — see migrations 010 / 016).
2. New convenience command `hai target nutrition --kcal --protein-g --carbs-g --fat-g [--phase <name>] [--effective-from <date>]` that emits 4 atomic `target` rows in a single transaction with the same `phase` token captured in `reason` and the same `effective_from`. Idempotent on re-invocation with identical args (matches existing `cmd_target_set` discipline). All rows `source='agent_proposed'` if invoked by an agent, `'user_authored'` otherwise.
3. `hai target commit --target-id <id>` already promotes proposed → active. No change needed.
4. W-A `target_status` query rewrites to `SELECT 1 FROM target WHERE user_id=? AND domain='nutrition' AND target_type IN ('calories_kcal','protein_g','carbs_g','fat_g') AND status='active' AND superseded_by_target_id IS NULL AND date(effective_from) <= date(?) LIMIT 1`. Single read surface.
5. The pre-W-C "table-missing → `target_status='unavailable'`" branch in PLAN §2.B disappears — the `target` table is in tree since v0.1.8. W-A is fully testable independent of W-C without the `OperationalError` catch.

**Effort delta.** The cleaner path is *smaller*, not larger:
- W-C drops from "new table + migration + new CLI command + integration tests" to "extend CHECK + convenience command + integration tests." Estimated 2-3 d (was 3-4 d).
- W-A's parallelization story simplifies (no table-missing escape hatch needed). Estimated unchanged.
- W-D arm-1 unchanged.
- Risks register §4 risk 2 (W-A ↔ W-C race condition + pre-W-C table-missing handling) collapses to "no race; table is in tree."

**Why the PLAN missed this.** The source finding (`agent_state_visibility_findings.md` F-AV-03) was authored without recognizing that `cmd_target_*` already supports nutrition targets — it cited "`hai target commit` exists but is training-target-shaped, not nutrition-shaped" (line 200). That premise is wrong: `target` is domain-agnostic. The D14 audit chain (round 1 → 2 → 3) propagated the misframing rather than catching it because all three rounds focused on internal coherence (typed contract, P-tier, ship-gate completeness) rather than re-validating against migration 020. This is a **provenance-discipline failure** of exactly the shape AGENTS.md "Patterns the cycles have validated" warns against ("Verify *file paths*, *line numbers*, *function/class names*, and *exact strings* before citing them") — F-AV-03's premise was never verified against `cmd_target_set`'s actual surface.

**Recommended response.**

- **Option A (preferred):** revise PLAN §2.D to the cleaner alternative above. Update PLAN §2.B W-A query. Update PLAN §4 risk 2 to remove the table-missing branch. Update effort table §5. Update `agent_state_visibility_findings.md` F-AV-03 with a SUPERSEDED note (mirrors the F-AV-01 supersede shape from round-2). Re-fire D14 round 4 to confirm the revision is coherent — small target surface, single round expected.
- **Option B:** ship PLAN as-written; accept the duplicate-table path; add an explicit §2.D paragraph justifying the duplication (e.g., "the new table exists for forward-compatibility with v0.2.x macro-level targeting"); add a §4 risk for the live-DB self-mis-classification scenario; add migration data move for the existing nutrition rows in `target` → `nutrition_target`. Larger D14 round-4 surface than Option A.
- **Option C (escalation):** maintainer may have intent for `nutrition_target` that this finding is missing (e.g., richer schema for macro-cycling, phase enums, weekly periodization). If so, document the intent inline and proceed.

**Until decision:** Phase 1 cannot start. W-C, W-A, W-D arm-1 all touch the chosen surface.

---

### F-PHASE0-02 — PLAN §2.A `cli.py:3041-3049` citation points to wrong function

**Cycle impact:** **nit** — citation accuracy fix only; no scope change.

**Severity:** documentation accuracy.

**Reference:**
- PLAN §2.A "Schema migration scope" paragraph, line 108: "`hai state reproject --base-dir ~/.health_agent --cascade-synthesis` (`cli.py:3041-3049`)"
- Actual code: `cli.py:3041-3049` is `_project_gym_submission_into_state` (a gym-intake projection helper).
- Actual reproject command: `cmd_state_reproject` at `cli.py:4111`.
- Actual `--cascade-synthesis` flag: `cli.py:8526`.

**Argument.** The cited line range is an internal helper that gets called from the gym-intake path; it is not the reproject command. A reader following the citation to understand the "operator-only recovery path" lands on the wrong function. The error originated from confusing the docstring at `cli.py:3048-3049` (which mentions reproject as the recovery path) with the reproject command itself.

**Recommended response.** PLAN §2.A line 108 changes from "(`cli.py:3041-3049`)" to "(`cmd_state_reproject` at `cli.py:4111`; `--cascade-synthesis` flag at `cli.py:8526`)." Same shape as F-PLAN-R3-03's restore citation expansion — handler + parser ranges, both cited.

---

### F-PHASE0-03 — PLAN §2.A `_norm` path-shorthand drop

**Cycle impact:** **nit** — citation accuracy fix only.

**Severity:** documentation accuracy.

**Reference:**
- PLAN §2.A fix-shape paragraph, line 104: "`exercise_name_slug` is `_norm(exercise_name)` from `projectors/strength.py`."
- Actual path: `core/state/projectors/strength.py:66`. The `projectors/` directory at `src/health_agent_infra/projectors/` does not exist; the active module lives under `core/state/projectors/`.

**Argument.** Path-shorthand drop. A reader following the citation to confirm the function exists has to re-search.

**Recommended response.** PLAN §2.A line 104 changes from "from `projectors/strength.py`" to "from `core/state/projectors/strength.py:66`."

---

### F-PHASE0-04 — `agent_state_visibility_findings.md` F-AV-03 premise is incorrect (cross-doc fan-out of F-PHASE0-01)

**Cycle impact:** **nit** — only material if Option A in F-PHASE0-01 is chosen, in which case the source-finding doc needs the same SUPERSEDED treatment F-AV-01 received in round-2.

**Severity:** documentation accuracy + provenance.

**Reference:** `reporting/plans/post_v0_1_14/agent_state_visibility_findings.md` lines 200-204:
> **Shape.** `hai intent commit` covers training intent. `hai target commit` exists but is training-target-shaped, not nutrition-shaped. There is no equivalent for "this is my daily macro target while I'm in this phase" — so partial-day intake has no reference to project against.

This premise is incorrect — `hai target commit` is generic (W57 gate, all domains). See F-PHASE0-01 evidence.

**Recommended response.** If F-PHASE0-01 Option A is chosen, prepend a "**SUPERSEDED for F-AV-03**" header note to the findings doc pointing to the revised PLAN §2.D, mirroring the F-AV-01 SUPERSEDED treatment from round-2 fan-out.

---

## §2. Audit-chain probe findings

### F-PHASE0-AC-01 — `hai explain --as-of 2026-04-30 --user-id u_local_1 --operator` returns full chain

**Cycle impact:** **none** — chain healthy, observation only.

**Evidence.** Command returns:
- 6 proposal_log entries (nutrition / recovery / running / sleep / strength / stress) with full rationale + uncertainty + policy_decisions.
- 6 planned_recommendation rows (pre-X-rule aggregate).
- Phase A X-rule firings: none recorded.
- Phase B X-rule firings: X9 [training-intensity-bumps-protein] fired against the nutrition recommendation.
- 6 final recommendation rows with review_event_id + review_question.
- daily_plan_id `plan_2026-04-30_u_local_1`, x_rules_fired = "X9".

The post-v0.1.14.1 audit chain is queryable end-to-end. No P0/P1 surface visible at this probe.

### F-PHASE0-AC-02 — `hai doctor` overall WARN is expected morning-state, not a Phase 0 finding

**Cycle impact:** **none** — observation only.

**Evidence.** `hai doctor` returns overall WARN with two warnings:
- `onboarding_readiness` WARN: 0 active intent rows. Maintainer-state shape; the user has 2 active target rows but no active intent rows.
- `intake_gaps` WARN: 3 blocking gaps for today (2026-05-03): recovery / stress / nutrition. All are normal pre-morning-ritual gaps.

Both are expected for a fresh morning before the maintainer's daily ritual fires. Not a code defect; not a Phase 0 finding requiring action.

---

## §3. Persona matrix findings

**Run.** `uv run python -m verification.dogfood.runner /tmp/hai_dogfood_v0_1_15_phase0`, full P1-P13 matrix. Runner takes no `--persona` filter, so all 13 personas execute; P7..P12 results are advisory per PLAN §6 (the residual is v0.1.17 W-Vb-4 scope), P13 is the low-domain-knowledge reader added at v0.1.14 W-EXPLAIN-UX.

**Result.** **13 personas, 0 findings, 0 crashes.** Every persona reached final recommendations across all six domains. `findings_by_kind = {}`. Summary file at `/tmp/hai_dogfood_v0_1_15_phase0/summary.json`.

| Persona | Findings | Crashes | Notes |
|---|---|---|---|
| p1_dom_baseline | 0 | 0 | control |
| p2_female_marathoner | 0 | 0 | running domain proceeds; nutrition/recovery/sleep/stress maintain |
| p3_older_recreational | 0 | 0 | conservative across all domains |
| p4_strength_only_cutter | 0 | 0 | strength proceeds; cardio defers as expected |
| p5_female_multisport | 0 | 0 | multi-domain coverage clean |
| p6_sporadic_recomp | 0 | 0 | sparse-history defer behavior intact |
| p7_high_volume_hybrid | 0 | 0 | running downgrades to easy aerobic; recovery proceeds |
| p8_day1_female_lifter | 0 | 0 | day-1 cold-start; all domains defer per coverage rules |
| p9_older_female_endurance | 0 | 0 | recovery downgrades hard → zone-2; running proceeds |
| p10_adolescent_recreational | 0 | 0 | recovery downgrades hard → zone-2; below-spec contract holds |
| p11_elevated_stress_hybrid | 0 | 0 | stress band escalation absorbed; no fail-open |
| p12_vacation_returner | 0 | 0 | data-discontinuity gap handled |
| p13_low_domain_knowledge | 0 | 0 | reader contract holds |

**Cycle impact:** **none** — the post-v0.1.14.1 wheel reproduces the v0.1.11 W-O matrix expectations cleanly. No persona-replay regression to fold into Phase 1.

**Implication for §1 findings.** The persona matrix exercises the runtime end-to-end, but every persona uses *synthetic seeded state* without any agent-driven `hai target` rows. So the matrix would not have surfaced F-PHASE0-01's duplicate-table concern even if it existed in a more concrete form — the personas don't author targets, they consume runtime classifications against the threshold defaults. F-PHASE0-01 stands; the matrix's clean sheet does not relax it.

---

## §4. Findings summary

| Finding | Cycle impact | Severity | Owner | Disposition |
|---|---|---|---|---|
| F-PHASE0-01 (W-C duplicates target table) | **revises-scope** | ship-impact-coupled | maintainer | escalate at pre-implementation gate; choose Option A / B / C |
| F-PHASE0-02 (cli.py:3041-3049 wrong citation) | nit | documentation | applied at gate | edit PLAN §2.A line 108 in-place |
| F-PHASE0-03 (`_norm` path-shorthand drop) | nit | documentation | applied at gate | edit PLAN §2.A line 104 in-place |
| F-PHASE0-04 (F-AV-03 premise incorrect) | nit (Option-A-conditional) | documentation | applied at gate if Option A | SUPERSEDED header on findings doc |
| F-PHASE0-AC-01 (audit chain queryable) | none | observation | n/a | n/a |
| F-PHASE0-AC-02 (`hai doctor` WARN expected) | none | observation | n/a | n/a |
| Persona matrix (P1-P13) | none | observation | n/a | 13/13 clean, 0 findings, 0 crashes (see §3) |

**Aborts-cycle count:** 0.
**Revises-scope count:** 1 (F-PHASE0-01).

## §5. Pre-implementation gate disposition

Phase 0 closes with **one revises-scope finding** (F-PHASE0-01), plus three nit-class findings and zero aborts-cycle findings.

Per AGENTS.md D11 pattern: revises-scope findings may revise PLAN.md and loop back to D14. F-PHASE0-01 is large enough that a D14 round 4 is the right next step if Option A or B is chosen.

The pre-implementation gate cannot fire cleanly until the maintainer chooses among F-PHASE0-01 Options A/B/C. **The cycle is held at the pre-implementation gate** per `cycle_open_session_prompt.md` Step 6 ("Phase 0 surfaces an `aborts-cycle` finding" was not the trigger, but the spirit applies — the implementation surface is materially in question).

See `pre_implementation_gate_decision.md` for the full gate-decision record once the maintainer responds.

---

## §6. Disposition (2026-05-03 evening, post-maintainer-response)

**Maintainer choice:** F-PHASE0-01 **Option A** (extend existing `target` table). Authorized 2026-05-03 evening with "Proceed based on your recommendations, I agree that revisions should be made."

**Applied at gate close (this session):**

| Finding | Disposition | Touched files |
|---|---|---|
| F-PHASE0-01 (Option A) | applied | PLAN §2.B (W-A query rewrite + escape-hatch removal), §2.D (full W-C rewrite — extend `target` table; migration 024 CHECK extension; 4-row convenience handler; 6 acceptance tests; OQ-10 raised), §2.E (W-D arm-1 acceptance test 4 narrowed; `unavailable` redefined), §4 risks 1 + 2 (table-missing branch removed), §5 effort table (W-C −1d), §1.2 catalogue cell + total (16-25 → 15-24), §1.4 disposition table W-C row, §1.3 sequencing note, §3 cross-cutting (state_model_v1.md), §8 OQ-7 redefinition + new OQ-10, §9 round-4 provenance entry, header status |
| F-PHASE0-02 (cli.py:3041-3049) | applied | PLAN §2.A line 108 (citation expanded to `cmd_state_reproject` at `cli.py:4111` + flag at `cli.py:8526`) |
| F-PHASE0-03 (`_norm` path-shorthand) | applied | PLAN §2.A fix-shape paragraph (`projectors/strength.py` → `core/state/projectors/strength.py:66`) |
| F-PHASE0-04 (F-AV-03 SUPERSEDED) | applied | `agent_state_visibility_findings.md` (SUPERSEDED-for-F-AV-03 header note added; mirrors F-AV-01 supersede shape) |

**Cross-doc fan-out:**
- `reporting/plans/v0_1_15/README.md` — status updated (D14 round 4 ready); Phase 0 close entry added.
- `reporting/plans/tactical_plan_v0_1_x.md` — §5B W-C row + effort estimate updated; v0.1.15 row in main release table updated with round-4 revision note.

**Q2 (foreign-user candidate) status:** **CLOSED 2026-05-03 evening** — maintainer named a foreign-user candidate. Path (a) — cycle proceeds without holding or downgrading. Phase 3 W-2U-GATE acceptance per PLAN §2.G now has a named candidate to target.

**Next step:** D14 round 4 codex audit fires against the round-4-revised PLAN. Codex prompt at `codex_plan_audit_round_4_prompt.md` (this session authored). Maintainer fires Codex; response file pattern follows the round-1/2/3 chain.
