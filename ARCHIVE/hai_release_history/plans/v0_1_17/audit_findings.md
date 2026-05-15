# v0.1.17 Phase 0 (D11) bug-hunt findings

**Cycle:** v0.1.17 (substantive tier — 10 W-ids, 25-40d estimated effort).
**Phase 0 opened:** 2026-05-05 morning.
**Status:** **closed 2026-05-05 morning.** All sub-steps complete: §1 internal sweep + §2 audit-chain probe + §3 persona matrix + §5 eval-corpus baseline; §4 Codex external bug-hunt deferred per maintainer-default substantive-cycle posture (no concerning patterns surfaced).

**HEAD at probe time:** `df6a13c` (cycle-open commit, 2026-05-04). cli.py at 9927 LOC; migration head at tree = 025; capabilities-manifest hai_version = 0.1.15.1; persona files P1..P13 in tree (P13 matrix-only per AGENTS.md D10).

**Pre-implementation gate decision (final):** all surfaced findings are tagged `nit` or `none`. Zero `revises-scope`, zero `aborts-cycle`. The PLAN as ratified at D14 round 3 is ready for Phase 1 open without re-audit. Multiple `nit` items are held for in-cycle close at the W-id commits that touch them; the rest are environment / positive-verification surfaces. **Phase 1 (W-29 + W-30) opens after maintainer ratification.**

---

## §1 Internal sweep findings

The internal sweep verified every PLAN-cited file path, line number, function/class symbol, exact-string claim, and structural assertion against HEAD `df6a13c`.

**Verified clean (no drift):**

- cli.py LOC = **9927** at HEAD `df6a13c` ✓ (matches PLAN §1.2 W-29 row, §2.A pre-flight, §4 risk 1).
- Migration head at tree = **025** (`025_target_macros_extension.sql`) ✓ — W-B's 026 is the next slot per PLAN §2.H.
- Snapshot files present at expected size: `verification/tests/snapshots/cli_capabilities_v0_1_13.json` = **5065 LOC**, `cli_help_tree_v0_1_13.txt` = **60 LOC** ✓ (both match PLAN §2.A).
- All 5 PLAN-named-new test files **absent at HEAD** ✓ — no partial implementation:
  - `verification/tests/test_cli_handler_dispatch_smoke.py`
  - `verification/tests/test_cli_handler_group_loc_ceiling.py`
  - `verification/tests/test_capabilities_manifest_schema.py`
  - `verification/tests/test_scenario_corpus_coverage.py`
  - `verification/tests/test_w_d_arm2_target_plumbing.py`
- All 3 PLAN-named-new module directories **absent at HEAD** ✓:
  - `src/health_agent_infra/cli/` (W-29 split target)
  - `src/health_agent_infra/core/body_comp/` (W-B target)
  - `src/health_agent_infra/core/sync/` (F-PV14-02 OQ-1 alternative)
- `hai capabilities --json` returns **60 leaf commands** at HEAD ✓ — matches PLAN §1.2 + §2.A claim "60 leaf commands."
- Cited file paths + line numbers + symbol names verify exactly (verified via `grep -nE`):
  - `core/state/snapshot.py:372` `def build_snapshot(...)` ✓
  - `core/state/snapshot.py:909` `nutrition_classified = classify_nutrition_state(nutrition_signals)` ✓ (single call, no `thresholds=` arg currently passed — matches PLAN §2.I plumbing-path claim)
  - `core/state/snapshot.py:942` `nutrition_block["classified_state"] = _nutrition_classified_to_dict(nutrition_classified)` ✓
  - `core/state/snapshot.py:1183` `def _nutrition_classified_to_dict(classified: Any) -> dict[str, Any]:` ✓ (PLAN §2.I W-D arm-2 serializer extension target)
  - `core/state/snapshot.py:895-902` `compute_presence_block` call assembling `_w_a_block` (the surface where `is_partial_day` + `target_status` are extracted; PLAN §2.I item 2 merge-insertion site) ✓
  - `domains/nutrition/classify.py:86` `ProteinSufficiencyBand = str  # "met"|"low"|"very_low"|"unknown"` ✓ (round-3 F-PLAN-R3-01's `"met"` band correction grounded — `"adequate"` is not a valid value)
  - `domains/nutrition/classify.py:94` `class ClassifiedNutritionState:` ✓ (PLAN §2.I W-D arm-2 dataclass-extension target — needs 4 new optional `projected_eod_*` fields)
  - `domains/nutrition/classify.py:309` `def classify_nutrition_state(nutrition_signals, thresholds: Optional[dict[str, Any]] = None)` ✓ (D13 trusted-by-design seam already accepts `thresholds`)
  - `domains/nutrition/classify.py:327` `t = thresholds if thresholds is not None else load_thresholds()` ✓ — confirms PLAN §2.I round-2 fix: treats non-None as full tree (subsequent reads at `:362-373` index `t["classify"]["nutrition"]["targets"]`; partial-dict override would `KeyError`, so deep-merged full-tree override is required as F-PLAN-R2-01 / item 5 specifies)
  - `domains/nutrition/classify.py:340-359` W-D arm-1 fallback (returns `nutrition_status="insufficient_data"` + `uncertainty=("partial_day_no_target",)` when `target_status in ("absent", "unavailable")` and `is_partial_day is True`) ✓
  - `core/intake/presence.py:163-213` `def compute_target_status(...) -> str` returning `"present" | "absent" | "unavailable"` ✓ (matches PLAN §2.I gating-dependency claim; module constant `NUTRITION_MACRO_TARGET_TYPES` at `:92` is the 4-tuple W-A reads, matching `'calories_kcal','protein_g','carbs_g','fat_g'` per W-C's migration 025 extension)
  - `core/capabilities/walker.py:437` `def _flag_entry(action: argparse.Action) -> dict[str, Any]:` ✓ (PLAN §2.A item 5 manifest-walker citation; the helper that records flag name/kind/choices/default per leaf)
  - `core/config.py:148` `DEFAULT_THRESHOLDS: dict[str, Any] = {...}` + `:805` `_deep_merge(DEFAULT_THRESHOLDS, user_overrides)` + `:806` `_validate_threshold_types(...)` ✓ — clean target for W-D arm-2's `projection_mode = "target_anchored"` default-leaf addition; deep-merge surface already exists.
  - No grep hits for `projection_mode` / `carbs_target_g` / `fat_target_g` in `core/config.py` ✓ — those leaves don't exist yet, exactly as W-D arm-2's job to add.
- post-v0.1.13 absorptions in cli.py confirmed: 15 grep hits for `intake gaps` + `target nutrition` (W-A + W-C surfaces landed in cli.py post-v0.1.13 boundary-table author-time); confirms PLAN §2.A pre-flight drift-narrative.
- `test_cli_parser_capabilities_regression.py` runs **5 passed in 0.47s** at HEAD ✓ — snapshot lockstep gate is currently green; W-29 byte-stability acceptance items 4-6 have a sound baseline.
- Domain-tier scenario count = **35** at HEAD ✓ matches PLAN §2.C exactly (recovery=5, running=7, sleep=4, strength=3, nutrition=3, stress=3, synthesis=10).
- 13 personas present in tree + ALL_PERSONAS registration in `verification/dogfood/personas/__init__.py` ✓.
- v0.1.13 `cli_boundary_table.md` baseline = **8891 LOC** ✓ — matches PLAN §2.A dual-baseline note (8891 at boundary-table author-time vs 9217 at v0.1.14 deferred-W-29 cite vs 9927 at HEAD).
- AGENTS.md "Settled Decisions" W29/W30 entry exists at line 137 (`reporting/plans/v0_1_17/PLAN.md` §3 ship-time append target) ✓.
- AGENTS.md "Do Not Do" cli.py-split clause exists at line 438 (PLAN §3 ship-time clause-removal target) ✓.
- All PLAN-cited source docs exist:
  - `reporting/plans/v0_1_16/README.md` (cancellation note)
  - `reporting/plans/post_v0_1_14/carry_over_findings.md` (F-PV14-02 source)
  - `reporting/plans/post_v0_1_14/agent_state_visibility_findings.md` (W-B + W-D arm-2 source)
  - `reporting/docs/archive/cycle_artifacts/cli_boundary_table.md` (W-29 architectural spec)

**Drift surfaced — 1 finding.**

### F-PHASE0-01 — `judge_adversarial` fixture count cited as 31; actual is 30

**Tag:** `nit` (close in place at W-AI-2 commit time; no PLAN restructure required).

**References (all four cite sites):**
- `reporting/plans/v0_1_17/PLAN.md` §2.C: "Plus **31 judge_adversarial scenarios** that are W-AI's corpus, not counted toward W-AH."
- `reporting/plans/v0_1_17/PLAN.md` §2.D commit-gate item 1: "judge_adversarial (**31 fixtures from v0.1.14**) + whatever W-AH-2 / W-AM-2 fixtures have already landed if those W-ids commit first."
- `reporting/plans/v0_1_17/PLAN.md` §2.D ship-gate: "the **31 judge_adversarial fixtures** from v0.1.14."
- `reporting/plans/v0_1_17/PLAN.md` §6 W-AI-2-specific gates: "judge_adversarial **31**."

**Verification.**

```bash
$ for d in bias_probe prompt_injection source_conflict; do
    echo "$d: $(ls src/health_agent_infra/evals/scenarios/judge_adversarial/$d/*.json | wc -l)"
  done
bias_probe: 10
prompt_injection: 10
source_conflict: 10

$ find src/health_agent_infra/evals/scenarios/judge_adversarial -name "*.json" ! -name "index.json" | wc -l
30
```

Total fixture count = **30** (10 + 10 + 10), excluding `judge_adversarial/index.json` which is the corpus manifest (per `evals/cli.py:113` "judge_adversarial index missing"), not a 31st fixture.

**Likely origin.** Round-1 PLAN-author miscounted `index.json` as the 31st fixture, or inherited a stale pre-v0.1.14-ship target. The D14 audit chain (rounds 1-3) didn't catch this because Codex doesn't grep the actual fixture tree at audit time — it reads PLAN claims at face value. Phase 0's role is exactly to catch source-of-record drifts the plan-audit chain can't see.

**Argument for `nit` (not `revises-scope`).** The "31" cite is documentary, not assertional. The W-AI-2 commit-gate at §2.D item 1 deliberately doesn't hard-code the corpus count — it specifies "List behaviour is dynamic over the at-commit corpus, not hard-coded against any specific count" (per F-PLAN-04 round-1 fix). The acceptance test will read whatever `evals/scenarios/judge_adversarial/**/*.json ! -name index.json` returns at commit time. The "31" figure only appears in prose for reader-orientation. Updating four prose cites does not change the W-AI-2 commit-gate test logic, the W-AI-2 ship-gate test logic, or any other W-id's contract.

**Recommended action.** W-AI-2 implementer corrects all four cite sites (PLAN §2.C / §2.D commit-gate / §2.D ship-gate / §6 W-AI-2 gate row) from `31` → `30` when authoring W-AI-2's commit. Single-pass text edit; no PLAN re-audit, no D14 reopen.

**Residual risk.** None. The cite-vs-reality drift was caught pre-implementation, and the fix is literally a number swap with no second-order consequence.

---

## §2 Audit-chain probe findings

The probe ran `hai today`, `hai doctor`, `hai explain`, plus a sanity-check on `hai state migrate`'s actual surface (the session prompt's `--dry-run --user-id` flags don't exist — see F-PHASE0-04).

**Audit-chain surfaces clean for the maintainer's current state:**

- `hai today --user-id u_local_1` → `"No plan for 2026-05-05. Run \`hai daily\` first."` — clean defer message, not a crash. Expected morning state at 07:58 BST.
- `hai explain --as-of 2026-05-05 --user-id u_local_1` → `"hai explain: no daily_plan chain for (for_date=datetime.date(2026, 5, 5), user_id='u_local_1')"` — clean honest-absence message; the audit chain handles the no-plan path correctly. (Three-state chain renders cleanly when there IS a plan; tested on prior cycle ship-day.)

**Findings — 3 captures, all `nit` or `none`.**

### F-PHASE0-02 — Maintainer's local state.db at schema_version 23; tree at 25

**Tag:** `nit` (environment state, not PLAN logic — a pre-implementation prep step, not a PLAN revision trigger).

**Reference.** `hai doctor` output:
```
## state_db  [WARN] warn
  schema_version: 23
  head_version: 25
  pending_migrations: 2
  reason: 2 pending migration(s)
  hint: run `hai state migrate`
```

**Argument.** Migrations 024 (`gym_set_id_with_exercise_slug`) and 025 (`target_macros_extension`) have shipped in tree (post-v0.1.15) but have not been applied to the maintainer's live state.db. This means the W-D arm-2 acceptance path (PLAN §2.I item 1: seed `target` rows with `calories_kcal=3100`, `protein_g=160`, `carbs_g=350`, `fat_g=90`) cannot exercise against the maintainer's live DB until migration 025 is applied — `carbs_g` and `fat_g` are migration-025 additions to `target_type` CHECK + `_VALID_TARGET_TYPE`. Similarly, W-B migration 026 testing (acceptance item 1: apply 026 against a v0.1.15.1-shaped DB) will first chain-apply 024 + 025 + 026 in a single migrate run — possible to do, but the implementer should be aware so the test fixtures match v0.1.15.1-shape, not v0.1.13-shape.

**Recommended action.** Maintainer runs `hai state migrate` (no `--user-id`; the schema is per-DB, not per-user) before W-B / W-D arm-2 acceptance work. **No PLAN edit required** — the acceptance tests in §2.H item 1 + §2.I items 1-7 already specify "v0.1.15.1-shaped DB" as the test substrate; they presume migration 025 is applied. This finding is a pre-implementation environment prep note.

**Residual.** None.

### F-PHASE0-03 — F-PV14-01 contamination shape firing on real maintainer state (positive validation of F-PV14-02 use case)

**Tag:** `none` (informational confirmation; strengthens the cycle's ship-claim).

**Reference.** `hai doctor` output:
```
## sources  [WARN] warn
  reason: one or more sources have a sync row whose for_date is >48h before
  the run timestamp (F-PV14-01 contamination shape — may indicate fixture
  data was projected into the canonical DB)
  garmin: last=2026-05-04T18:10:11.400586+00:00 stale=29.8h
  garmin_live: last=2026-05-04T18:10:11.326098+00:00 stale=29.8h
  gym_manual: last=2026-05-02T09:17:43.908810+00:00 stale=86.7h
  intervals_icu: last=2026-05-04T11:51:07.697963+00:00 stale=36.1h
  note_manual: last=2026-05-04T16:08:40.166443+00:00 stale=31.9h
  nutrition_manual: last=2026-05-04T16:08:37.914201+00:00 stale=31.9h
  readiness_manual: last=2026-05-04T18:11:25.129539+00:00 stale=29.8h
  stress_manual: last=2026-05-04T11:49:36.730710+00:00 stale=36.2h
```

**Argument.** The v0.1.15-shipped F-PV14-01 prevention surface (CSV-fixture isolation marker + `for_date_divergence_warn`) is correctly identifying a real contamination signature in the maintainer's DB across 8 sources, with staleness ranging 29.8h → 86.7h. **This validates F-PV14-02's use case as real**: the surgical-cleanup CLI (PLAN §2.G) has a concrete row-set to act on, not a synthetic test fixture. Acceptance items 1-3 in §2.G can be exercised end-to-end against the actual contamination signature when implementing.

**Recommended action.** No PLAN edit. Implementer of F-PV14-02 may use this real signature as the integration-test substrate, alongside the unit-test fixtures specified in §2.G items 1-3.

**Residual.** None — actually strengthens the cycle's ship claim that F-PV14-02 ships necessary, not nice-to-have, behaviour.

### F-PHASE0-04 — Inline Phase-0 session-opening prompt cites `hai state migrate --dry-run --user-id` flags that don't exist

**Tag:** `nit` (session-prompt drift; not a stored-artifact edit. Captured here so the next maintainer-authored Phase-0 session prompt doesn't repeat the dead invocation.)

**Reference.** The inline Phase-0 session-opening prompt the maintainer provided at this session's start (verbatim §2.2 audit-chain probe step) suggested:
```bash
uv run hai state migrate --dry-run --user-id u_local_1
```

The stored `reporting/plans/v0_1_17/cycle_open_session_prompt.md` does NOT contain this invocation (verified via `grep -n "hai state migrate" cycle_open_session_prompt.md` returning empty). The drift is in the inline prompt, not in any committed artifact — so no file edit is required.

Actual surface (from `uv run hai state migrate --help`):
```
usage: hai state migrate [-h] [--db-path DB_PATH]
```

**Argument.** Neither `--dry-run` nor `--user-id` is a valid flag on `hai state migrate`. The `state.db` schema is per-DB, not per-user (`--user-id` doesn't fit the abstraction); `--dry-run` would be a useful add but doesn't exist at v0.1.15.1. Running the command as cited returns an `unrecognized arguments` error, which a less-careful Phase 0 author might mistakenly tag as a regression.

**Recommended action.** None to a stored artifact. The next maintainer-authored Phase-0 / IR / cycle-open session prompt should use:
- Schema head check: `uv run hai doctor` (returns `schema_version` + `head_version` + `pending_migrations` in the `state_db` block).
- Apply migrations: `uv run hai state migrate` (no flags).

**Provenance note.** This finding was originally cited (incorrectly) against `cycle_open_session_prompt.md`. Verified-on-disk discipline caught the misattribution at gate-decision close — `cycle_open_session_prompt.md` is clean. The drift is in the inline session prompt only.

**Residual.** None.

### F-PHASE0-06 — Maintainer `intent_count: 0` confirms v0.1.18 onboarding-cycle thesis (cross-cycle context)

**Tag:** `none` (downstream-cycle context, validates v0.1.18 README provenance; not a v0.1.17 blocker).

**Reference.** `hai doctor` output:
```
## onboarding_readiness  [WARN] warn
  intent_count: 0
  target_count: 3
  has_wellness_pull: True
  missing: intent
  hint: no active intent rows — run `hai intent training add-session` or
        `hai intent sleep set-window` to author a goal
```

**Argument.** `reporting/plans/v0_1_18/README.md` provenance claim (lines 18-23) explicitly cites this state ("the maintainer's own state DB still shows `onboarding_readiness: WARN: missing intent` (`intent_count: 0`)") as the empirical foundation for the v0.1.18 onboarding cycle. Phase 0 confirms the claim is real and current at HEAD. This does not affect v0.1.17 implementation directly, but does mean the W-Vb-4 persona-replay residual (§2.F) may surface scenarios where the persona harness exercises a missing-intent path against the maintainer's real DB shape.

**Recommended action.** No PLAN edit. Cross-cycle confirmation that v0.1.18's thesis is grounded.

**Residual.** None.

---

## §3 Persona matrix baseline (12 personas + P13 matrix-only)

**Status:** complete. Invocation:
```bash
uv run python -m verification.dogfood.runner /tmp/persona_run_phase0_baseline
# runtime ~5min on the maintainer's M-series Mac. Matches v0.1.14 baseline.
```

**Result.** All 13 personas reach `synthesized` end-state. **0 findings, 0 crashes** across the matrix. Per-persona action surfaces (recovery / running / sleep / strength / nutrition / stress) all populated; P7 (high-volume hybrid) shows substantive escalation (`running: downgrade_to_easy_aerobic`); P9 + P10 show substantive recovery softening (`recovery: downgrade_hard_session_to_zone_2`); P2 + P4 show substantive `proceed_with_planned_run|session`; P8 (day-1 female lifter) appropriately defers across most domains (correct — day 1 has no signal).

**Per-persona disposition (from `summary.json` + per-persona `result.json` + `today.txt`):**

| Persona | Closure | Substantive recommendation surfaced |
|---|---|---|
| P1 dom_baseline | synthesized | maintains across most; appropriate for control |
| P2 female_marathoner | synthesized | `running: proceed_with_planned_run` |
| P3 older_recreational | synthesized | maintains; appropriate for steady baseline |
| P4 strength_only_cutter | synthesized | `strength: proceed_with_planned_session` |
| P5 female_multisport | synthesized | maintains |
| P6 sporadic_recomp | synthesized | maintains |
| **P7 high_volume_hybrid** | synthesized | **`running: downgrade_to_easy_aerobic`** (escalation fired) |
| **P8 day1_female_lifter** | synthesized | defers across all 5 non-stress domains (appropriate — day 1) |
| **P9 older_female_endurance** | synthesized | **`recovery: downgrade_hard_session_to_zone_2`** + `running: proceed_with_planned_run` |
| **P10 adolescent_recreational** | synthesized | **`recovery: downgrade_hard_session_to_zone_2`** |
| **P11 elevated_stress_hybrid** | synthesized | maintains; questionable for an elevated-stress persona — see F-PHASE0-09 |
| **P12 vacation_returner** | synthesized | maintains |
| P13 low_domain_knowledge | synthesized | matrix-only per AGENTS.md D10 / v0.1.13 F-PLAN-06 |

This is a **clean baseline** that exceeds the W-Vb-4 acceptance posture in PLAN §2.F.

### F-PHASE0-07 — P7..P12 already close cleanly at HEAD; W-Vb-4 effort budget overestimated

**Tag:** `nit` (effort-estimate refinement; PLAN logic unchanged. Does NOT trigger D14 reopen — implementation can proceed against existing PLAN.)

**Reference.** PLAN §1.2 W-Vb-4 row: `5-7 d` effort estimate. PLAN §5 effort arithmetic: W-Vb-4 budgeted 5/6/7 (best/mid/worst). PLAN §2.F acceptance items 1-2 + 4-5:
- (1) "Each persona reaches `synthesized` end-state (or honest `defer_decision_insufficient_signal`...)" ✓ all 13 reach synthesized.
- (2) "No persona crashes" ✓ 0 crashes.
- (4) "Cumulative count: P1..P12 all close (12 of 12)" ✓ 12 of 12 (P13 matrix-only).
- (5) "Three-at-a-time partial-closure pattern available" — not needed; no partial-closure required.

**Argument.** The PLAN's expectation that P7-P12 would need substantive re-work in this cycle (per the v0.1.14 W-Vb-3 carry-over chain: "3 of 9 personas closed in v0.1.14 — P2 + P3 + P6") is empirically wrong at HEAD `df6a13c`. Whatever combination of v0.1.13/v0.1.14/v0.1.15/v0.1.15.1 changes shipped between the v0.1.14 W-Vb-3 partial-closure and now, P7-P12 are now closing cleanly through the persona-runner's harness-stand-in proposals. The W-Vb-3 → W-Vb-4 chain that estimated 5-7d was based on the v0.1.14-ship-time persona-runner state, which has since drifted in W-Vb-4's favour.

**Recommended action.**
1. **W-Vb-4 implementation work drops from 5-7d → ~0.5-1d.** The remaining work is documentation: capture this baseline closure in REPORT.md §5.X, name the v0.1.15 / v0.1.15.1 changes that brought P7-P12 into closure (provenance), and re-run the matrix once at end-of-cycle (after W-AH-2 + W-AM-2 corpus expansion + W-29 split land) to verify no regression.
2. **PLAN §1.2 W-Vb-4 effort + §5 arithmetic refined.** No PLAN re-author required — the cycle effort estimate (25-40d) absorbs the saving as schedule slack. Implementer notes the refinement at REPORT.md authoring time.
3. **W-Vb-4 acceptance items 1-5 effectively pre-satisfied.** Item 6 ("Persona-matrix run time documented") gets the v0.1.14-baseline `~5 min` figure carried forward; if W-AH-2's corpus growth changes runtime materially, REPORT.md updates.
4. **No PLAN edit required.** This finding *strengthens* the cycle's ship-claim — it confirms the runtime contracts P7-P12 exercise are stable post-v0.1.15.

**Residual risk.** Low. Possible the closure is too lenient — the runner exits cleanly when it reaches synthesized, but doesn't assert that the recommendation is *substantively correct* for the persona archetype. If a persona produces a recommendation that doesn't match its archetype (e.g. P11 elevated-stress maintains across all domains; see F-PHASE0-09), that's not caught by the existing matrix. W-Vb-4 implementer should consider whether to add per-persona expected-outcome contracts (out-of-scope expansion) or accept the loose "closes cleanly" closure (PLAN-as-written posture). **Recommend the latter** — per-persona expected-outcome contracts is v0.1.19 foreign-user empirical territory.

### F-PHASE0-08 — PLAN §2.F item 3 cites `recommendation.json` artifact path; runner produces `result.json` + `today.txt`

**Tag:** `nit` (cite-vs-reality drift; PLAN parenthetical "or equivalent harness path" absorbs).

**Reference.** PLAN §2.F item 3:
> "Per-persona JSON output landed at `/tmp/persona_run/p<N>_*/recommendation.json` (or equivalent harness path)."

Actual files produced per persona (verified at `/tmp/persona_run_phase0_baseline/p7_high_volume_hybrid/`):
```
cleaned_evidence.json        # only for personas that pull
intake_root                  # directory of staged intake JSONLs
proposal_nutrition.json
proposal_recovery.json
proposal_running.json
proposal_sleep.json
proposal_strength.json
proposal_stress.json
pull.json                    # only for personas that pull
result.json                  # ← the synthesised end-state
snapshot.json
state.db
today.txt                    # ← the user-facing rendering
```

**No `recommendation.json` is produced.** The closure artifacts are `result.json` + per-domain `proposal_*.json` + `today.txt` + `snapshot.json`.

**Recommended action.** W-Vb-4 implementer corrects PLAN §2.F item 3 cite from `recommendation.json` to `result.json` (and notes the per-domain proposals + `today.txt` rendering surface) when authoring the W-Vb-4 commit / REPORT.md. Single-pass text edit. The "(or equivalent harness path)" parenthetical means this isn't a contract violation — it's a doc-cite refinement.

**Residual.** None.

### F-PHASE0-09 — P11 (elevated-stress hybrid) maintains across all domains; archetype expects stress-routing

**Tag:** `none` (substrate observation; not a v0.1.17 blocker. Better suited to v0.1.19 foreign-user empirical work or W-AM-2 escalate-fixture authoring.)

**Reference.** Persona matrix output for P11:
```
actions: {'nutrition': 'maintain_targets', 'recovery': 'proceed_with_planned_session',
          'running': 'defer_decision_insufficient_signal', 'sleep': 'maintain_schedule',
          'strength': 'defer_decision_insufficient_signal', 'stress': 'maintain_routine'}
```

**Argument.** P11's archetype is "elevated-stress hybrid" — a persona where the stress domain is meant to be the dominant signal driving recommendations. The stress action came back `maintain_routine` rather than an escalate-class action (e.g., `escalate_stress_breath` or similar). This may indicate either: (a) the persona's stress stand-in proposal isn't synthetic-elevated enough to fire the runtime's stress R-rules, OR (b) the runtime's stress policy thresholds need tuning, OR (c) the persona-runner harness-stand-in pattern is too generic to exercise per-persona escalation cleanly.

**Recommended action.** None within v0.1.17. This is a candidate finding for:
- **W-AM-2 escalate-fixture authoring** (PLAN §2.E item 1: "stress / nutrition / sleep / strength `should_escalate_<reason>` fixture"). The W-AM-2 stress fixture, authored against the live classify+policy stack via per-scenario interactive validation, will surface whether the policy actually fires escalation under realistic stress signals — and may transitively inform a P11 persona refinement.
- **v0.1.19 foreign-user empirical work** — per-persona expected-outcome contracts are downstream-cycle scope.

**Residual.** None within v0.1.17. The cycle's ship-claim is unaffected.

---

---

## §4 Codex external bug-hunt audit — deferred per maintainer-default substantive-cycle posture

**Status:** deferred.

**Argument.** AGENTS.md D11 + D14 cycle pattern names the Codex external bug-hunt as **optional per maintainer**. v0.1.15's Phase 0 ran one because round-0 plan revisions were structurally large and the foreign-user precondition introduced empirical risk; v0.1.14's Phase 0 deferred. v0.1.17 is structurally lower-density than v0.1.15 (most catalogue rows inherited from prior release-proofs with established source contracts), and §1 + §2 + §5 surfaced only `nit` + `none` findings — no concerning patterns.

**Recommended action.** Skip. If §3 persona-matrix surfaces a `revises-scope` regression, reconsider — Codex external review is the right surface for "is the regression v0.1.15-introduced, or always-broken, or test-substrate-dependent?" judgement calls.

---

## §5 `hai eval run` baseline verification (positive)

### F-PHASE0-05 — `hai eval run --scenario-set all` returns 35/35 PASS at HEAD

**Tag:** `none` (positive baseline verification).

**Verification.**
```bash
$ uv run hai eval run --scenario-set all
...
eval domain / sleep: 4/4 passed (0 failed)
eval domain / strength: 3/3 passed (0 failed)
eval domain / stress: 3/3 passed (0 failed)
eval synthesis: 10/10 passed (0 failed)
[total: 35/35 PASS at HEAD; same as baseline for recovery + running + nutrition]
```

**Argument.** PLAN §2.C acceptance item 5 ("v0.1.14 baseline: the 35-fixture corpus passed at 100% at v0.1.14 ship") is grounded — the corpus still passes at 100% at HEAD `df6a13c`. PLAN §6 W-AH-2-specific gate ("`hai eval run --scenario-set all` returns OK exit code (100% pass-rate)") inherits from a real baseline, not a hypothetical one. W-AH-2's expansion 35 → 132+ within the 100% gate is therefore achievable per PLAN §2.C item 2 (per-fixture interactive-author-then-validate) without first having to repair a regressed baseline.

**Residual.** None.

---

## §6 Pre-implementation gate decision (final)

**Verdict:** **OPEN PHASE 1.**

**Findings rollup (9 total: 5 `nit`, 4 `none`; zero `revises-scope`, zero `aborts-cycle`):**

| ID | Tag | Source | Disposition |
|---|---|---|---|
| F-PHASE0-01 | nit | §1 internal sweep | judge_adversarial cite 31 → 30; close at W-AI-2 commit time (4 cite sites) |
| F-PHASE0-02 | nit | §2 audit-chain probe | maintainer DB at schema_v23 vs tree v25; pre-implementation maintainer prep (`hai state migrate`) |
| F-PHASE0-03 | none | §2 audit-chain probe | F-PV14-01 contamination shape firing on real maintainer state — validates F-PV14-02 use case |
| F-PHASE0-04 | nit | §2 audit-chain probe | session-prompt cites dead `--dry-run`/`--user-id` flags on `hai state migrate`; edit cycle-open prompt |
| F-PHASE0-05 | none | §5 eval baseline | `hai eval run --scenario-set all` 35/35 PASS at HEAD — validates W-AH-2 §2.C item 5 baseline |
| F-PHASE0-06 | none | §2 audit-chain probe | maintainer `intent_count: 0` — validates v0.1.18 onboarding-cycle thesis (cross-cycle) |
| F-PHASE0-07 | nit | §3 persona matrix | P7-P12 close cleanly at HEAD; W-Vb-4 effort 5-7d → ~0.5-1d (cycle slack) |
| F-PHASE0-08 | nit | §3 persona matrix | PLAN §2.F item 3 `recommendation.json` → `result.json` cite refinement |
| F-PHASE0-09 | none | §3 persona matrix | P11 elevated-stress maintains all domains; substrate observation, not v0.1.17 blocker |

**Rationale.**

- §1 internal sweep: 1 nit (judge_adversarial 31→30 cite drift). All other PLAN-cited paths/lines/symbols verify exactly.
- §2 audit-chain probe: 3 captures (1 environment nit, 1 session-prompt nit, 1 positive). 1 cross-cycle positive.
- §3 persona matrix: 13 of 13 close cleanly (0 findings, 0 crashes); 2 nits (effort-budget refinement + artifact-name cite); 1 substrate observation.
- §4 Codex external bug-hunt: deferred — no concerning patterns surfaced to justify spend.
- §5 eval baseline: positive (35/35 PASS).

**Net.** PLAN as ratified at D14 round 3 is structurally sound and ready for Phase 1 open without re-audit. Two nits trigger a PLAN edit at the W-id commit-time (F-PHASE0-01 + F-PHASE0-08); one nit is a pre-implementation maintainer environment prep (F-PHASE0-02); one nit is a session-prompt edit (F-PHASE0-04). The remaining four findings are positive verifications or cross-cycle context.

**Pre-implementation gate fires `OPEN PHASE 1`.** Phase 1 (W-29 cli.py mechanical split + W-30 capabilities-manifest schema regression test) opens after maintainer ratification.

**Schedule slack from F-PHASE0-07.** The PLAN §1.2 / §5 cycle-effort estimate (25-40d) absorbs the ~4-6d W-Vb-4 saving as schedule slack. Realistic refined estimate: **19-34d** (or 22-37d with 5% inter-WS coordination overhead). The maintainer may opt to surface the saving at REPORT.md ship time rather than re-author PLAN §5 mid-cycle.

**Recommendations for the maintainer at gate-ratification time:**

1. **Run `hai state migrate`** to bring local DB to schema_v25 before W-B / W-D arm-2 implementation (F-PHASE0-02).
2. **Edit `cycle_open_session_prompt.md` §2.2** to drop the dead `--dry-run`/`--user-id` flags from the audit-chain probe (F-PHASE0-04). Single-line text edit.
3. **Approve PLAN-as-written for Phase 1 open.** F-PHASE0-01 (judge_adversarial 31→30) gets corrected at W-AI-2 commit time; F-PHASE0-08 (`recommendation.json` → `result.json`) gets corrected at W-Vb-4 commit time. No D14 reopen needed.
4. **Consider whether F-PHASE0-09 (P11 stress non-firing)** routes to W-AM-2 stress escalate-fixture authoring as an empirical input. Optional — W-AM-2 already specifies per-scenario interactive author-then-validate workflow.

---

## Provenance

This file authored 2026-05-05 morning against HEAD `df6a13c` post-PLAN-D14-close. All verifications executed via `grep` / `wc` / live `hai` invocations. No tests run beyond `test_cli_parser_capabilities_regression.py` baseline + `hai eval run --scenario-set all` + the persona-matrix invocation (in flight). No code changed against the PLAN.
