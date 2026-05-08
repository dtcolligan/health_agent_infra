# v0.1.17 PLAN — Maintainability + eval substrate consolidation

**Tier (D15):** **substantive** — W-29 is a release-blocker workstream AND estimated effort is 25-40 days; either criterion independently satisfies AGENTS.md D15 "substantive" threshold (`≥1 release-blocker workstream` OR `≥10 days estimated`). W-B schema/state-model + W-AH-2 substrate expansion + audit-chain doc edits are scope facts, not D15 tier triggers; D15's three-edit threshold counts only governance or audit-chain edits, of which §3 has two (cli.py-split entry retirement + W-29 closure addition). Round-1 PLAN claimed "≥3 governance/state-model/audit-chain edits" — F-PLAN-11 corrected; state-model is not a D15 tier trigger.

**Status:** **authored 2026-05-04, pre-D14 round 1.** PLAN.md is the artifact under audit; no code has changed against it. Phase 0 (D11) bug-hunt has not started. Cycle workspace at `reporting/plans/v0_1_17/`.

**Authored:** 2026-05-04 against HEAD `df6a13c` (post-v0.1.16-cancellation restructure commit). v0.1.17 promoted to next-active 2026-05-04 when v0.1.16's named foreign-user candidate became unavailable; the former v0.1.16-must-close precondition retired the same day.

**Estimated effort:** **25-40 days** (1 maintainer). See §5 arithmetic.

**D14 expectation:** budget **2-4 rounds** per AGENTS.md empirical norm (twice-validated 10 → 5 → 3 → 0 settling at v0.1.11 + v0.1.12; v0.1.14 closed 12 → 7 → 3 → 1-nit; v0.1.15 4-round close including post-Phase-0 ratification round). v0.1.17's catalogue is mostly inherited from prior release-proofs, so cross-cutting consistency findings should be lower density than restructure cycles — author may settle one round early. Don't bet on it.

**Theme.** Land the maintainability + eval-substrate work the v0.1.15 round-0 PLAN deferred so the deferred items don't accumulate further drift, and lift the W-29 cli.py mechanical split that's been on the AGENTS.md "Settled Decisions" books since v0.1.12 CP1. **Ship claim:** internal correctness + maintainer-side cleanup; eval substrate expansion against synthetic + dogfood evidence; mechanical refactor cli.py 9927 → handler-group split; new body-comp intake surface. Parallelizable with v0.2.0 since v0.2.0's hard dependencies do not include this cycle.

**Source inputs:**
- `reporting/plans/v0_1_17/README.md` — provisional scope catalogue (10 W-ids).
- `reporting/plans/v0_1_15/PLAN.md` §1.4 disposition table — round-0 → round-1 cuts assigned destination v0.1.17 (9 of 16 slots).
- `reporting/plans/v0_1_14/RELEASE_PROOF.md` §carry-overs — W-29, W-AH-2, W-AI-2, W-AM-2 (absorbed-into-W-AI), W-Vb-4 inheritance chain.
- `reporting/plans/post_v0_1_14/carry_over_findings.md` §F-PV14-02 — `hai sync purge` surgical-cleanup CLI.
- `reporting/plans/post_v0_1_14/agent_state_visibility_findings.md` §F-AV-02 (W-B) + §F-AV-04 arm 2 (W-D arm-2). Note: doc has SUPERSEDED header notes for the v0.1.15-shipped portions; only F-AV-02 + F-AV-04 arm 2 remain in scope here.
- `reporting/plans/v0_1_15/codex_implementation_review_response.md` §F-IR-04 + `codex_implementation_review_round_2_response.md` §F-IR-R2-02 — W-C-EQP query-plan-stability named-defer landed durably at v0.1.17.
- `reporting/docs/archive/cycle_artifacts/cli_boundary_table.md` — v0.1.13 W-29-prep boundary audit (the proposed split table; LOC numbers must be re-derived against current cli.py at Phase 1 open).
- `reporting/plans/tactical_plan_v0_1_x.md` §5D — tactical row reflecting the v0.1.17 scope post-restructure.
- `reporting/plans/v0_1_18/README.md` + `v0_1_19/README.md` — downstream cycle scope (out of v0.1.17 reach; PLAN must not pull onboarding or empirical work forward).
- `reporting/plans/v0_1_16/README.md` — cancellation note (the precondition retirement chain).

---

## 1. What this release ships

### 1.1 Theme

Internal correctness and maintainer-side cleanup over a single cycle, against the package shape v0.1.15.1 published. The cycle has three phases:

**Phase 1 — Mechanical foundation.** The cli.py 9927-line single-file is the largest source-tree liability. W-29 splits it into 1 main + 1 shared + 11 handler-group modules (per the v0.1.13 boundary audit's go-verdict, refreshed against current LOC at Phase 1 open). The byte-stable `hai capabilities --json` manifest contract is the gate. W-30 lands the lightweight regression-test scaffold for the eventual v0.2.3 capabilities-manifest schema freeze.

**Phase 2 — Eval substrate.** W-AH-2 expands the synthetic scenario fixture pack from 35 to 120+ across the six domains + synthesis. W-AI-2 ships the `hai eval review` CLI surface for triaging the expanded corpus + the v0.1.14 judge_adversarial fixtures. W-AM-2 lands the four fork-deferred escalate-tagged scenarios (sleep / strength / stress / nutrition) authored against the live classify+policy stack. W-Vb-4 closes the persona-replay residual P7..P12 against the post-v0.1.15 schema.

**Phase 3 — Carry-overs + nice-to-haves.** F-PV14-02 ships the `hai sync purge` surgical-cleanup CLI (paired-but-deferred from v0.1.15 F-PV14-01). W-B adds `hai intake weight` + the new `body_comp` table + migration 026. W-D arm-2 lands the partial-day nutrition end-of-day projection (gated on W-A + W-C in tree from v0.1.15). W-C-EQP adds the EXPLAIN QUERY PLAN stability assertion for the W-A active-window query.

**Honesty boundary.** W-AH-2's "evidence-grounded" claim reads against the existing synthetic persona matrix + dogfood evidence — **not** a foreign-user transcript. The v0.1.16 cancellation (2026-05-04) retired the foreign-user precondition that the v0.1.14 RELEASE_PROOF originally chained into v0.1.16; the empirical work moved to v0.1.19 (post-v0.1.18 onboarding). v0.1.17 ships honestly as "synthetic-coverage expansion," **not** "foreign-user-validated coverage." See §1.4 for the renumber narrative and §4 for the residual risk.

### 1.2 Workstream catalogue (10 W-ids)

| Section | W-id | Title | Effort | Source | Severity |
|---|---|---|---|---|---|
| §2.A | **W-29** | cli.py 9927-line mechanical split (1 main + 1 shared + 11 handler-group, byte-stable manifest) | 4-6 d | v0.1.14 RELEASE_PROOF §carry-overs; AGENTS.md "Settled Decisions" (v0.1.12 CP1, redestinated v0.1.15 → v0.1.17 on 2026-05-02 evening) | release-blocker (workstream gate; the mechanical-split itself is the deliverable) |
| §2.B | **W-30** | Capabilities-manifest schema-freeze regression test (test only; freeze itself ships at v0.2.3) | 0.5 d | AGENTS.md "Settled Decisions" v0.1.12 CP2; redestinated post-v0.1.13 CP-W30-SPLIT | hardening |
| §2.C | **W-AH-2** | Synthetic scenario fixture expansion 35 → 120+ across six domains + synthesis | 4-6 d | v0.1.14 RELEASE_PROOF §carry-overs (W-AH partial-closure) | substrate-gap |
| §2.D | **W-AI-2** | `hai eval review` CLI surface (triage + filter + tag + export over judge_adversarial + scenario corpus) | 3-4 d | v0.1.14 RELEASE_PROOF §carry-overs (W-AI partial-closure) | substrate-gap |
| §2.E | **W-AM-2** | 4 fork-deferred escalate-tagged scenarios (sleep / strength / stress / nutrition), per-scenario interactive-author-then-validate | 2-3 d | v0.1.14 RELEASE_PROOF §carry-overs (W-AM absorbed-into-W-AI partial-closure); v0.1.14 REPORT.md §5.3 workflow | substrate-gap |
| §2.F | **W-Vb-4** | Persona-replay residual P7..P12 (6 personas) against post-v0.1.15 schema (W-A presence + W-C target + migration 025) | 5-7 d | v0.1.14 RELEASE_PROOF §carry-overs (W-Vb-3 partial-closure: 3 of 9 personas closed; cumulative 6 of 12) | correctness-residual |
| §2.G | **F-PV14-02** | `hai sync purge` surgical-cleanup CLI (refuses unless selectors resolve to ≤5 rows; writes `runtime_event_log` audit row) | 1.5 d | `post_v0_1_14/carry_over_findings.md` §F-PV14-02 (paired-but-deferred from v0.1.15 F-PV14-01) | doctrine-gap |
| §2.H | **W-B** | `hai intake weight --kg <X> [--body-fat-pct <Y>] --as-of <Z>` + new `body_comp` table + migration 026 | 3-4 d | `agent_state_visibility_findings.md` §F-AV-02 (deferred from v0.1.15 round-0 cut) | ship-impact (re-raise of B3 from 2026-04-27) |
| §2.I | **W-D arm-2** | Partial-day nutrition end-of-day projection (gated on W-A `is_partial_day` + `target_status="present"` from v0.1.15) | 2-3 d | `agent_state_visibility_findings.md` §F-AV-04 arm 2 (gated on W-C shipped in v0.1.15) | ship-impact (completes the v0.1.15 W-D arm-1 known-incomplete fix) |
| §2.J | **W-C-EQP** *(small)* | EXPLAIN QUERY PLAN stability assertion for the W-A active-window query against `target` post-migration 025 | 0.5 d | v0.1.15 IR round 1 §F-IR-04 named-defer; round 2 §F-IR-R2-02 durable-tracking confirmation | acceptance-tightening |

**Total:** 10 W-ids, **25-40 days estimated effort** (per-WS arithmetic 26-37, +inter-WS coordination overhead ~5%; see §5), substantive tier.

### 1.3 Sequencing (DAG)

**Phase 1 — Mechanical foundation (lands first; serialises with everything that touches cli.py):**

1. **W-29** — cli.py mechanical split per refreshed boundary table. Lands first because every Phase 2 + Phase 3 W-id that adds a CLI surface (W-AI-2 `hai eval review`, F-PV14-02 `hai sync purge`, W-B `hai intake weight`, W-D arm-2's classifier wiring) would create merge friction against an unsplit cli.py. Phase 1 → Phase 2 dependency: W-29 must commit before any Phase 2/3 cli.py edit lands.
2. **W-30** — capabilities-manifest schema-freeze regression test. Independent of W-29 mechanically (test only). Sequenced after W-29 so the test asserts against the post-split parser shape — that's the byte-stability the W-29 acceptance also asserts; double-asserting from two test surfaces is the v0.2.3 freeze posture.

**Phase 2 — Eval substrate (parallelizable after Phase 1 closes):**

3. **W-AH-2** — scenario expansion. Touches only `src/health_agent_infra/evals/scenarios/<domain>/*.json` + scenario-runner contract; doesn't touch cli.py. Can run in parallel with W-AI-2 + W-AM-2.
4. **W-AI-2** — `hai eval review` CLI surface. Touches cli.py (post-W-29 split, lands in `cli/handlers/tools.py` per the v0.1.13 boundary-audit grouping for `hai eval run` + `hai validate`). New JSON schema for review-state persistence. Independent of W-AH-2 + W-AM-2 mechanically.
5. **W-AM-2** — 4 fork-deferred escalate-tagged scenarios. Touches only `src/health_agent_infra/evals/scenarios/<sleep|strength|stress|nutrition>/*.json` + scenario-runner. Per-scenario interactive author-then-validate against live classify+policy stack per v0.1.14 REPORT.md §5.3 workflow.
6. **W-Vb-4** — persona-replay residual P7..P12. Persona runner reads post-v0.1.15 schema (W-A presence + W-C target + migration 025). Independent of W-AH-2 / W-AI-2 / W-AM-2 mechanically. Three-at-a-time partial-closure pattern remains available per v0.1.14 PLAN §2.M.

**Phase 3 — Carry-overs + nice-to-haves (parallelizable after Phase 1 closes; can overlap with Phase 2):**

7. **F-PV14-02** — `hai sync purge` CLI. Touches cli.py (post-W-29 split, new subcommand under `hai sync` group — TBD whether `hai sync` becomes its own handler group or merges into `cli/handlers/state.py`; OQ-1). Independent of all other W-ids.
8. **W-B** — `hai intake weight` + `body_comp` table + migration 026. Touches cli.py (post-W-29 split, lands in `cli/handlers/intake.py`) + `core/state/migrations/026_body_comp.sql` + new `core/body_comp/store.py` + capabilities manifest. Independent of all other W-ids.
9. **W-D arm-2** — partial-day nutrition end-of-day projection. Touches `domains/nutrition/classify.py` + `domains/nutrition/policy.py` + `synthesis_policy.py` + audit-chain rendering in `hai explain`. **Gated on v0.1.15 W-A + W-C in tree** (verified at v0.1.15.1 ship; both surfaces present). Independent of all other v0.1.17 W-ids.
10. **W-C-EQP** — EXPLAIN QUERY PLAN assertion. Touches `verification/tests/test_w_c_target_nutrition.py` (extends the F-IR-04 byte-stable preservation test). Independent of all other W-ids.

**Cross-phase merge friction.** The serialisation dependency is W-29 → everything-else-that-touches-cli.py. Phase 2 + Phase 3 are otherwise independent and can land in any order after W-29 commits. Recommended commit cadence: atomic per-W-id commits (10 commits, plus the W-29 split itself which is necessarily larger).

### 1.4 Source provenance + renumber narrative

This cycle's catalogue inherits from three independent provenance chains:

**Chain A — v0.1.14 RELEASE_PROOF carry-overs.** W-29, W-AH-2, W-AI-2, W-AM-2 (absorbed-into-W-AI), W-Vb-4 were named-deferred from v0.1.14 to v0.1.15 at v0.1.14 ship. The v0.1.15 round-0 self-audit (2026-05-02 evening) cut all five from v0.1.15 and reassigned to v0.1.17 — see `v0_1_15/PLAN.md` §1.4 disposition table rows 1, 12, 13, 14, 15. The cut rationale was "would create merge friction with the v0.1.15 W-A/W-C/W-D/W-E user-facing daily-loop hardening if combined."

**Chain B — v0.1.15 round-0 disposition cuts.** F-PV14-02, W-B, W-D arm-2 were also assigned destination v0.1.17 in the v0.1.15 round-0 self-audit (rows 5, 7, 10 in `v0_1_15/PLAN.md` §1.4). These were always carry-over candidates from `post_v0_1_14/agent_state_visibility_findings.md` + `post_v0_1_14/carry_over_findings.md`; v0.1.15 deferred them as orthogonal to the foreign-user gate.

**Chain C — v0.1.15 IR named-defer.** W-C-EQP was named-deferred from v0.1.15 IR round 1 §F-IR-04; round 2 §F-IR-R2-02 confirmed durable destination at v0.1.17. The v0.1.15 PLAN W-C migration shipped a byte-stable preservation test + index-name-existence assertion; the EXPLAIN QUERY PLAN stability check is the stronger assertion deferred here.

**Renumber narrative (post-v0.1.16-cancellation, 2026-05-04).** The original v0.1.17 README (created 2026-05-02 evening) named v0.1.16 as a hard precondition: "v0.1.16 must close so that any P0/P1 bugs the foreign-user gate surfaces have landed before W-AH-2's eval-substrate work, so scenarios wouldn't encode the wrong runtime contract." That precondition retired 2026-05-04 when v0.1.16's named foreign-user candidate became unavailable (`v0_1_16/README.md`). The empirical scope was preserved and renumbered to **v0.1.19**, with a new **v0.1.18** onboarding cycle inserted before it (`v0_1_18/README.md`). v0.1.17 now runs without the foreign-user precondition.

**Implication for W-AH-2 specifically.** The original chained precondition assumed v0.1.16's foreign-user transcript would inform what runtime contracts the expanded scenario corpus needs to encode. Without that transcript, W-AH-2 consolidates against (a) the existing synthetic persona matrix (12 personas + P13 matrix-only), (b) the maintainer's dogfood-session evidence in memory (`project_morning_briefing_v0_1_x_bugs_2026-04-27.md` + `project_demo_run_findings_2026-04-28.md`), and (c) the v0.1.15-shipped runtime contracts (W-A presence + W-C target + W-D arm-1 suppression). The ship-claim language in §2.C and §6 is **"synthetic-coverage expansion"**, not "foreign-user-validated coverage" — the latter remains v0.1.19's claim. Honest naming per AGENTS.md "Honest partial-closure naming."

---

## 2. Per-workstream contracts

### §2.A W-29 — cli.py 9927-line mechanical split (release-blocker)

**Source.** v0.1.14 RELEASE_PROOF §carry-overs; AGENTS.md "Settled Decisions" v0.1.12 CP1 (redestinated v0.1.13 → v0.1.14 → v0.1.15 → v0.1.17 over the cycle chain); v0.1.13 W-29-prep boundary audit at `reporting/docs/archive/cycle_artifacts/cli_boundary_table.md`.

**Files of record:**
- `src/health_agent_infra/cli.py` (9927 LOC at HEAD `df6a13c`) → split into:
  - `src/health_agent_infra/cli/__init__.py` (new `main` — parser-tree builder + dispatch)
  - `src/health_agent_infra/cli/shared.py` (helpers: `_emit_json`, `_emit_text`, `_resolve_db_path`, `_resolve_user_id`, `annotate_contract` re-export, common arg-parsing helpers)
  - `src/health_agent_infra/cli/handlers/auth.py` (~230 LOC at v0.1.13 estimate; 4 leaf commands)
  - `src/health_agent_infra/cli/handlers/pull_clean.py` (~600 LOC)
  - `src/health_agent_infra/cli/handlers/state.py` (~240 LOC)
  - `src/health_agent_infra/cli/handlers/config_init.py` (~360 LOC)
  - `src/health_agent_infra/cli/handlers/intake.py` (~1080 LOC at v0.1.13; **largest group, +W-A intake gaps already absorbed post-v0.1.13, +W-B intake weight will absorb further** — §4 risk 1)
  - `src/health_agent_infra/cli/handlers/intent.py` (~180 LOC)
  - `src/health_agent_infra/cli/handlers/target.py` (~195 LOC; **+W-C `target nutrition` already absorbed post-v0.1.13**)
  - `src/health_agent_infra/cli/handlers/recommend.py` (~710 LOC)
  - `src/health_agent_infra/cli/handlers/review.py` (~225 LOC)
  - `src/health_agent_infra/cli/handlers/inspect.py` (~280 LOC)
  - `src/health_agent_infra/cli/handlers/tools.py` (~250 LOC at v0.1.13; **+`hai eval review` from W-AI-2 will absorb further**)
- `verification/tests/test_cli_parser_capabilities_regression.py` — existing test pins `hai capabilities --json` (excluding volatile `hai_version`) and parser-tree shape against `verification/tests/snapshots/cli_capabilities_v0_1_13.json` (5065 LOC) + `cli_help_tree_v0_1_13.txt` (60 LOC). Snapshots have been regenerated post-v0.1.13 to track v0.1.13/v0.1.14/v0.1.15 intentional surface adds; **the W-29 split must produce zero drift against the current snapshot at Phase 1 open**.

**Pre-flight (Phase 1 open, before W-29 split commits).** The v0.1.13 boundary table's LOC numbers are stale: cli.py was 8891 LOC at v0.1.13 cycle-open, 9927 LOC at v0.1.17 cycle-open (+1036 LOC across v0.1.13/v0.1.14/v0.1.15/v0.1.15.1 surface adds — the most material drift is in `intake.py` from W-A `intake gaps` and in `target.py` from W-C `target nutrition`).

**Dual-baseline note (per F-PLAN-R2-05 round-2 fix).** Two historical cli.py LOC baselines exist in source docs and both are correctly cited in their own contexts: **8891 LOC at v0.1.13 W-29-prep boundary-table author-time** (the archived spec doc `reporting/docs/archive/cycle_artifacts/cli_boundary_table.md:55` — this PLAN §2.A uses 8891 because the boundary table is the architectural spec the W-29 split executes against, and 8891 is its baseline) and **9217 LOC at v0.1.14 RELEASE_PROOF deferred-W-29 cite** (`reporting/plans/v0_1_14/RELEASE_PROOF.md:25` — tactical §5D + §5G top row use 9217 because that's the v0.1.14 deferral baseline the redestination chain inherits). Round-1 source-doc refresh per F-PLAN-08 mistakenly attributed "9217 at v0.1.13 W-29-prep" in tactical §5D — F-PLAN-R2-05 round-2 caught and corrected. Current LOC at HEAD `df6a13c` is **9927** regardless of which historical baseline a doc cites.

Pre-flight is a **gated acceptance item** (item 1 below), not prose-only — Phase 1 implementation does not commit until the refreshed boundary note lands and returns a non-`do-not-split` verdict.

**Acceptance.**
1. **Refreshed boundary note** authored at `reporting/plans/v0_1_17/w29_boundary_refresh.md` before any W-29 split commit. Required content: (a) current command inventory cross-checked against `hai capabilities --json` at HEAD; (b) per-handler-group estimated LOC against current cli.py (9927 LOC); (c) shared-helper extraction list (the helpers that move to `cli/shared.py`); (d) contested groupings (any leaf command whose handler-group placement is non-obvious); (e) explicit verdict per the v0.1.13 boundary-table convention: `split` (above table coherent, no group ≥2500 LOC, no command obviously mis-grouped) / `split-with-revisions` (mostly coherent but ≥1 group at LOC ceiling OR ≥1 grouping contested) / `do-not-split` (split itself wrong-shaped, e.g. hidden cross-handler shared state pattern).
2. **`do-not-split` abort path (round-2 collapsed per F-PLAN-R2-03 to a single halt branch).** If item 1 returns `do-not-split`, the cycle **halts at Phase 1 open**. PLAN.md re-authors through D14 round 2+ before resuming, with **all of the following reconsidered**: W-29 release-blocker status (drops or rescopes — currently the cycle's only release-blocker), §3 ship-time AGENTS.md edits (the "append `W-29 closed at v0.1.17`" + retire cli.py-split "Do Not Do" clause both don't fire), §6 W-29-specific release-blocker gates (drop), §7 v0.1.18 onboarding-cycle dependency text (v0.1.18 W-OB-2 hard-depends on W-29 closing per `v0_1_18/README.md:57-60` — that dependency renegotiates with v0.1.18 PLAN.md author at that cycle's open), README + tactical §5D + tactical §5E rows (refresh), and W-29-3 destination cycle assignment (assigned during PLAN re-author). **The round-1 alternative branch — "Phase 2 + Phase 3 ship without W-29" — was retired at round 2 per F-PLAN-R2-03 as unsafe**: Phase 2/3 W-AI-2 / F-PV14-02 / W-B all add CLI surfaces that depend on the split landing first; without the split, they merge into pre-split cli.py and create the exact merge friction §1.3 sequencing was designed to prevent. Cycle does NOT silently degrade to no-op or to ship-Phase-2/3-without-W-29.
3. Mechanical split commits as a single atomic commit OR a tightly-coupled 3-commit series labelled `W-29.1` (shared module extraction) / `W-29.2` (handler-group split) / `W-29.3` (cli/__init__.py refactor) per OQ-8 default. **Every commit in the W-29 series must individually pass acceptance items 4-7; the final commit closes the byte-stability gate.** Every leaf command relocates to exactly one handler-group module; no command lives in `cli/__init__.py`.
4. `hai capabilities --json` (excluding `hai_version`) is byte-identical against the snapshot current at W-29 Phase 1 open. Asserted by `test_cli_parser_capabilities_regression.py` running clean. **No snapshot regeneration during the W-29 series** — intentional CLI-surface adds in Phase 2/3 regenerate the snapshot per-W-id (per F-PLAN-07 fix in §3 + §6).
5. Parser-tree shape (deterministic textual summary per the existing test) is byte-identical against the snapshot current at W-29 Phase 1 open. **Plus**: a new test surface `test_cli_handler_dispatch_smoke.py` exercises **one non-default flag per moved handler group** (≥11 smoke tests, one per handler-group module) asserting the handler resolves correctly and produces non-error output. This catches subtle argparse `dest` renames or handler-namespace breaks the manifest-shape test would miss (per F-PLAN-06 — the existing parser-tree snapshot does not capture `dest`; the manifest walker at `core/capabilities/walker.py:437-459` records flag name/kind/choices/default but not `dest`).
6. `hai capabilities --markdown > reporting/docs/agent_cli_contract.md` regenerates with zero diff against the markdown current at W-29 Phase 1 open (the markdown contract is a derived view of the same manifest).
7. No handler-group module exceeds 2500 LOC. Asserted by a new `test_cli_handler_group_loc_ceiling.py` test that walks `cli/handlers/*.py` and refuses any module ≥2500 LOC. **2500 ceiling rationale:** matches the v0.1.13 boundary-table CP1 contract; gives ~700 LOC headroom against the largest current group (`intake.py` ~1080 LOC pre-W-A absorption, projected to ~1200-1400 LOC post-W-A/W-B absorption). Future cycles that approach the ceiling sub-split per item 1's contested-grouping path.
8. Full pytest suite (narrow + broader warning gates) green post-split.
9. `uvx mypy src/health_agent_infra` clean post-split.
10. `uvx bandit -ll -r src/health_agent_infra` clean post-split.

**What this WS does NOT do.**
- Does not freeze the capabilities-manifest schema (W-30 + v0.2.3 territory).
- Does not introduce new commands or new flags. Pure mechanical refactor.
- Does not rename leaf commands. The user-facing CLI surface is byte-identical.
- Does not change the `from health_agent_infra.cli import ...` import contract. Existing test imports against module paths must continue to work; if any test imports a private helper that moved to `cli/shared.py`, the test gets updated to import from the new path in the same commit — these are test-only edits, not contract changes.

**Ship-claim gate:** acceptance items 4-6 (manifest + parser-tree-with-dispatch-smoke + markdown byte-stability) are **release-blocker**. If any fails after the split, the W-29 commit reverts and the cycle holds for re-shape via item 2's abort path.

### §2.B W-30 — capabilities-manifest schema-freeze regression test (test only)

**Source.** AGENTS.md "Settled Decisions" v0.1.12 CP2; redestinated post-v0.1.13 CP-W30-SPLIT — the schema-freeze itself is v0.2.3, but the regression-test scaffold lands earlier so v0.2.x cycles can build against it.

**Files of record.**
- `verification/tests/test_capabilities_manifest_schema.py` (new) — asserts the structural keys of `hai capabilities --json` against an inline schema (top-level `hai_version`, `commands[]`; per-command `command`, `flags[]`, `mutation`, `agent_safe`, `idempotent`, `json_output`; per-flag `name`, `kind`, `choices`, `choice_metadata`).
- `verification/tests/snapshots/cli_capabilities_v0_1_17_schema.json` (new) — derived schema document, not a full snapshot.

**Acceptance.**
1. Test imports the live manifest, walks every command + every flag, asserts that every required key is present with the expected type. Failure mode: a future cycle adds a per-command field without updating the schema, the test fails, the cycle author updates the schema in lockstep.
2. Test does NOT pin field *values* (that's `test_cli_parser_capabilities_regression.py`'s job). It pins field *names* + types only.
3. Test passes against current HEAD before W-30 commits (sanity check that the schema document matches reality at v0.1.17 cycle-open).

**What this WS does NOT do.** Does not freeze the schema (no commitment that v0.2.x can't extend it). Does not change manifest output. Test-only.

### §2.C W-AH-2 — synthetic scenario fixture expansion 35 → 120+

**Source.** v0.1.14 RELEASE_PROOF §carry-overs (W-AH partial-closure: 28 → 35 scenarios shipped at v0.1.14; original 120+ target deferred to W-AH-2).

**Current baseline (verified at HEAD).** `src/health_agent_infra/evals/scenarios/` contains 35 scenarios across the six domains + synthesis: recovery=5, running=7, sleep=4, strength=3, nutrition=3, stress=3, synthesis=10. (Plus 31 judge_adversarial scenarios that are W-AI's corpus, not counted toward W-AH.)

**Target shape.** **120+ total** distributed roughly 18-20 per domain × 6 domains + 10-15 synthesis = 118-135. Exact target distribution:

| Domain | Current | Target | Δ |
|---|---|---|---|
| recovery | 5 | 20 | +15 |
| running | 7 | 20 | +13 |
| sleep | 4 | 20 | +16 |
| strength | 3 | 20 | +17 |
| nutrition | 3 | 20 | +17 |
| stress | 3 | 20 | +17 |
| synthesis | 10 | 12-15 | +2 to +5 |
| **Total** | **35** | **132-135** | **+97 to +100** |

**Evidence-grounding.** Per §1.4 honesty boundary, scenarios encode the *current* runtime contract — post-v0.1.15 W-A presence + W-C target + W-D arm-1 suppression + migration 025 — derived from (a) the existing 35 scenarios (template shapes), (b) the 12-persona dogfood matrix (current baseline distribution), (c) maintainer dogfood evidence in memory (`project_morning_briefing_v0_1_x_bugs_2026-04-27.md`, `project_demo_run_findings_2026-04-28.md`). Scenarios that would require runtime-contract extensions beyond v0.1.15.1 (e.g. body-comp signals before W-B lands; end-of-day projections before W-D arm-2 lands) are sequenced last in this WS, after their dependencies commit, OR named-deferred to v0.1.18+.

**Files of record.**
- `src/health_agent_infra/evals/scenarios/{recovery,running,sleep,strength,nutrition,stress}/*.json` (new fixtures, per per-domain target).
- `src/health_agent_infra/evals/scenarios/synthesis/*.json` (small expansion).
- Scenario-runner contract: no changes (existing harness consumes the fixture shape unchanged).

**Harness-contract alignment (per F-PLAN-02 round-1 fix).** New fixtures align to the **existing** scenario-runner contract at `evals/runner.py:71-86` (loader) + `:300-380` (scoring): every fixture has `scenario_id`, `kind`, `description`, `expected.classified` (per-domain band assertions), `expected.policy.forced_action` and/or `expected.policy.fired_rule_ids` (policy-firing assertions). **No new fields** like `expected_*_token` or `expected_escalate_token` (those don't exist in the current runner). Per-fixture tag uses the **singular `"tag"` field** matching v0.1.14-shipped fixtures (`rec_004_should_escalate_compound_signals.json:35`, `run_004_should_escalate_acwr_max.json:25`), not a `tags[]` array. **Round-1 PLAN claimed `tags[]` + `expected_*_token`; corrected here per Codex F-PLAN-02.**

**Acceptance.**
1. Per-domain count meets target (≥20 per domain except synthesis ≥12). Asserted by a new `test_scenario_corpus_coverage.py` that walks `evals/scenarios/` and refuses if any domain falls below the per-domain floor.
2. Every new scenario fixture's `expected.classified` + `expected.policy` blocks pass against the live runtime via the existing `evals/runner.py` scoring path. Validated via `hai eval run --scenario-set all` (or per-domain). Fixtures that fail their own expected blocks are dropped + logged in the W-AH-2 commit message as runtime-contract findings, **not silently shipped** (this is the v0.1.14 W-AM lesson: 4 of 6 escalate scenarios failed live validation in v0.1.14; honest count was 2-of-6).
3. Per-fixture `tag` field (singular) reuses the v0.1.14-shipped vocabulary (`w-am-adversarial-escalate`, `w-aj-judge-adversarial`, etc.); no new top-level tags introduced without an explicit governance edit (tags are a substrate convention).
4. Scenario provenance: every new fixture's `provenance.source_doc` field cites the dogfood-evidence memory or the existing fixture template it was derived from. No fabricated scenarios.
5. **Eval-corpus replay** (per F-PLAN-03 round-1 fix — replaces "persona-matrix replay against the post-W-AH-2 corpus" which was wrong-mechanism: persona runner does not consume `evals/scenarios/`; the two are independent code paths). `hai eval run --scenario-set all` against the post-W-AH-2 tree returns **OK exit code** (i.e. **100% pass-rate**, matching the existing CLI's `failed == 0` contract per `evals/cli.py:cmd_eval_run`). **v0.1.14 baseline:** the 35-fixture corpus passed at 100% at v0.1.14 ship (the cycle wouldn't have shipped otherwise). W-AH-2 inherits the 100% contract and grows the corpus 35 → 132+ within that contract. Round-1 PLAN proposed ≥95% — F-PLAN-R2-02 round-2 caught: `hai eval run` has no aggregate-percentage mode (any failed scenario returns non-zero), so 95% is unaachievable through the existing CLI without a `--summary` extension that's not in v0.1.17 scope. Tightened to 100% pass; per-fixture validation discipline (acceptance item 2) means fixtures that can't fire are dropped + logged, not silently shipped at <100%. Persona matrix runs separately as a standard substantive-cycle ship gate (per §6) — independent of the eval-corpus gate.

**What this WS does NOT do.**
- Does not author scenarios that require runtime contracts not yet in tree (defers those to the cycle that ships the contract; e.g., body-comp scenarios wait for W-B's commit in this same cycle; partial-day projection scenarios wait for W-D arm-2).
- Does not extend the scenario-runner harness contract or fixture schema (per F-PLAN-02 alignment to existing `expected.classified` + `expected.policy` shape + singular `tag` field).
- Does not introduce a persona-by-scenario replay harness (per F-PLAN-03; persona matrix and eval-corpus are independent gates).
- Does not assume a foreign-user transcript exists. Synthetic + dogfood evidence only — see §1.4 honesty boundary.

### §2.D W-AI-2 — `hai eval review` CLI surface

**Source.** v0.1.14 RELEASE_PROOF §carry-overs (W-AI partial-closure: 30 judge-adversarial fixtures + 7 contract tests shipped at v0.1.14; `hai eval review` CLI deferred to W-AI-2).

**Files of record.**
- `src/health_agent_infra/cli/handlers/tools.py` (post-W-29 split — adds `hai eval review` subcommand alongside existing `hai eval run`). `cmd_eval_review` handler + parser.
- `src/health_agent_infra/evals/review.py` (new) — review-state persistence layer (loads + saves per-scenario triage state).
- `src/health_agent_infra/data/eval_review/state.json` OR `~/.local/share/health_agent_infra/eval_review.json` (new persistence path — OQ-2 below).
- Capabilities manifest annotation for the new subcommand.

**Subcommand shape (provisional v1).**

```
hai eval review list [--corpus <judge_adversarial|scenarios|all>] [--tag <t>] [--filter <f>] [--json]
hai eval review show --scenario-id <id> [--json]
hai eval review tag --scenario-id <id> --tag <t> [--note <free-text>]
hai eval review dismiss --scenario-id <id> --reason <free-text>
hai eval review export --output <path> [--format json|csv]
```

**Acceptance — split into commit-gate + ship-gate per F-PLAN-04 round-1 fix** (W-AI-2 sequencing in §1.3 says "independent of W-AH-2 + W-AM-2 mechanically," so its commit gate cannot depend on their fixtures existing yet):

**Commit gate (W-AI-2 itself; runs at W-AI-2 commit time):**
1. `hai eval review list --corpus all` returns whatever corpus exists at W-AI-2 commit time — judge_adversarial (31 fixtures from v0.1.14) + whatever W-AH-2 / W-AM-2 fixtures have already landed if those W-ids commit first. JSON shape includes `scenario_id`, `domain`, `tag` (singular per F-PLAN-02), `last_run_outcome` (if available), `triage_state` (none / tagged / dismissed). **List behaviour is dynamic over the at-commit corpus, not hard-coded against any specific count.**
2. `hai eval review tag --scenario-id <id> --tag <t>` writes the triage state to the persistence layer; subsequent `list` reflects the tag.
3. `hai eval review dismiss --scenario-id <id> --reason <free-text>` writes a dismiss record with the reason; the scenario remains in the corpus but is filtered out of default `list` output.
4. `hai eval review export --output <p>` produces a JSON file (default) with the full triage state for offline analysis. CSV format optional v1.
5. Capabilities manifest entry annotated with `mutation="writes-state"` (the review state file is mutable), `agent_safe=True`, `idempotent="depends-on-subcommand"`, `json_output=True`.
6. Test surface: round-trip test (`tag` → `list` → `dismiss` → `list` → `export`) covers persistence + filtering. Test uses an at-commit-time corpus, **not** hard-coded fixture counts.
7. **Snapshot regeneration lockstep (per F-PLAN-R2-04 round-2 fix).** The W-AI-2 commit regenerates `verification/tests/snapshots/cli_capabilities_v0_1_13.json` + `verification/tests/snapshots/cli_help_tree_v0_1_13.txt` + `reporting/docs/agent_cli_contract.md` **in the same commit** as the `hai eval review` surface adds. `test_cli_parser_capabilities_regression.py` runs clean against the regenerated snapshots. (§3 + §6 specify the lockstep rule; this acceptance item makes it commit-local.)

**Ship gate (verified at end-of-cycle, in §6):** `hai eval review list --corpus all` returns the post-W-AH-2 expansion (132+ scenarios, per §2.C target) + W-AM-2 escalate fixtures (6 of 6 cumulative, per §2.E acceptance) + the 31 judge_adversarial fixtures from v0.1.14. This gate verifies the completed W-AH-2 + W-AM-2 additions are visible through `hai eval review`; it is **not** W-AI-2's own commit gate.

**OQ-2 disposition (closed via Codex round-1 opinion).** Persistence path is **user's local state dir** (`~/.local/share/health_agent_infra/eval_review.json`) — Codex round-1 opinion: "Agree with user local state dir. A packaged data dir would be wrong for mutable per-user triage." Removed from §8 open list.

**What this WS does NOT do.** Does not auto-run scenarios (`hai eval run` is unchanged). Does not change the judge_adversarial corpus structure. Does not feed into v0.2.2 W58J's blocking-judge contract (substrate work; W58J consumes whatever review state exists).

### §2.E W-AM-2 — 4 fork-deferred escalate-tagged scenarios

**Source.** v0.1.14 RELEASE_PROOF §carry-overs (W-AM absorbed-into-W-AI partial-closure: 2 of 6 escalate scenarios shipped at v0.1.14; 4 fork-deferred to W-AM-2 because mid-cycle authors failed live classify+policy assertions); v0.1.14 REPORT.md §5.3 documents the per-scenario interactive-author-then-validate workflow.

**Target.** Author 4 escalate-tagged scenarios across sleep / strength / stress / nutrition. Each fires the runtime's escalate path (R-rule firing or X-rule mutation triggering an escalate-class action like `escalate_recovery_focus`, `escalate_load_taper`, `escalate_stress_breath`, etc. — exact taxonomy per the live `synthesis_policy.py` + per-domain `policy.py`).

**Files of record.**
- `src/health_agent_infra/evals/scenarios/sleep/<name>_should_escalate_<reason>.json`
- `src/health_agent_infra/evals/scenarios/strength/<name>_should_escalate_<reason>.json`
- `src/health_agent_infra/evals/scenarios/stress/<name>_should_escalate_<reason>.json`
- `src/health_agent_infra/evals/scenarios/nutrition/<name>_should_escalate_<reason>.json`

Tag: `w-am-adversarial-escalate` (matches the v0.1.14-shipped recovery + running fixtures).

**Workflow (per v0.1.14 REPORT.md §5.3).** For each domain:
1. Author the scenario fixture against the live classify+policy contract — fixture shape is `expected.classified` (per-domain band assertions) + `expected.policy.forced_action` (the escalate-class action like `escalate_recovery_focus`, `escalate_load_taper`) and/or `expected.policy.fired_rule_ids` (R-rule firings). Per F-PLAN-02 round-1 fix, the fixture **does not** add an `expected_escalate_token` field — that field doesn't exist in the v0.1.15.1 runner.
2. Run scenario through the live runtime via `hai eval run --scenario-id <id>` (or per-domain), which exercises the existing `evals/runner.py:300-380` scoring path against the fixture's `expected.policy` block.
3. Verify the firing pattern matches the fixture's `expected.policy.forced_action`. If mismatch, iterate (adjust scenario inputs OR diagnose runtime contract drift).
4. Commit only after live validation passes.

This is the lesson from v0.1.14: do NOT batch-author + batch-validate; per-scenario interactive validation is the only way to avoid the 4-of-6 silent-failure shape.

**Acceptance.**
1. 4 new fixtures committed, one per domain (sleep / strength / stress / nutrition).
2. Each fires its expected escalate forced-action against the live runtime via `expected.policy.forced_action` (matches the v0.1.14-shipped escalate fixtures' contract — `recovery/rec_004_should_escalate_compound_signals.json` + `running/run_004_should_escalate_acwr_max.json`). **Validated by the existing scenario-runner harness** (`evals/runner.py:300-380`); no harness extension required.
3. Per-fixture `tag: "w-am-adversarial-escalate"` (singular field per F-PLAN-02) matches the v0.1.14-shipped fixtures' tag (no new tag introduced).
4. Cumulative escalate-tagged count: **6 of 6** (2 v0.1.14-shipped + 4 W-AM-2-shipped). Per-domain coverage: recovery + running + sleep + strength + stress + nutrition.
5. Scenario-runner harness covers all 6 escalate scenarios via the existing `evals/runner.py` scoring path; no new test surface required (the existing `hai eval run --scenario-set all` covers them).

**What this WS does NOT do.** Does not author non-escalate scenarios (W-AH-2 territory). Does not extend the scenario-runner harness or fixture schema (per F-PLAN-02 alignment to existing `expected.policy.forced_action` contract). Does not change the policy/classify stack to make scenarios fire (if a scenario can't fire its expected forced-action, it gets dropped + logged as a runtime-contract finding, not silent absorption).

### §2.F W-Vb-4 — persona-replay residual P7..P12

**Source.** v0.1.14 RELEASE_PROOF §carry-overs (W-Vb-3 partial-closure: 3 of 9 personas closed in v0.1.14 — P2 + P3 + P6; cumulative 6 of 12: v0.1.13 closed P1+P4+P5; v0.1.14 closed P2+P3+P6; **P7..P12 residual to v0.1.15 W-Vb-4**, redestinated to v0.1.17).

**Target.** Close P7..P12 (6 personas) against the post-v0.1.15 schema (W-A presence + W-C target + W-D arm-1 + migration 025). Cumulative target: 12 of 12.

**Files of record.**
- `verification/dogfood/personas/p7_high_volume_hybrid.py` (in tree)
- `verification/dogfood/personas/p8_day1_female_lifter.py` (in tree)
- `verification/dogfood/personas/p9_older_female_endurance.py` (in tree)
- `verification/dogfood/personas/p10_adolescent_recreational.py` (in tree)
- `verification/dogfood/personas/p11_elevated_stress_hybrid.py` (in tree)
- `verification/dogfood/personas/p12_vacation_returner.py` (in tree)
- `verification/dogfood/runner.py` — persona runner; reads post-v0.1.15 schema unchanged.

**Acceptance.**
1. Each persona reaches `synthesized` end-state (or honest `defer_decision_insufficient_signal` per the per-persona expected outcome) when run through `verification.dogfood.runner` against `/tmp/persona_run`.
2. No persona crashes (Python exception, SQL error, validation failure).
3. Per-persona JSON output landed at `/tmp/persona_run/p<N>_*/recommendation.json` (or equivalent harness path).
4. Cumulative count: P1..P12 all close (12 of 12). P13 (low-domain-knowledge) is matrix-only per v0.1.13 F-PLAN-06 and not part of W-Vb closure.
5. **Three-at-a-time partial-closure pattern available** per v0.1.14 PLAN §2.M: if a persona surfaces a runtime-contract issue too large to fix in-cycle, it can fork-defer to v0.1.18+ with named scope. **Honest partial-closure naming:** the cycle does NOT silently ship "5 of 6" or "5 of 6 plus a stub." Defer or close.
6. Persona-matrix run time documented (was ~5 min at v0.1.14; if W-AH-2 + W-AM-2 corpus expansion increases runtime materially, document the new runtime in REPORT.md).

**What this WS does NOT do.** Does not introduce a new persona archetype. Does not change the persona-runner harness contract. Does not run as part of CI (per AGENTS.md D10).

### §2.G F-PV14-02 — `hai sync purge` surgical-cleanup CLI

**Source.** `post_v0_1_14/carry_over_findings.md` §F-PV14-02. Paired-but-deferred from v0.1.15 F-PV14-01: F-PV14-01 ships prevention (CSV-fixture isolation marker), F-PV14-02 ships surgical cleanup (when prevention fails or pre-prevention contamination exists).

**Files of record.**
- `src/health_agent_infra/cli/handlers/state.py` (post-W-29 split — adds `hai sync purge` subcommand) OR a new `cli/handlers/sync.py` if `hai sync` becomes its own group (OQ-1).
- `src/health_agent_infra/core/sync/purge.py` (new) — selector-resolution + safety-cap helper.
- Capabilities manifest annotation.

**Subcommand shape.**

```
hai sync purge --source <s> --for-date <d> [--started-after <ts>] [--user-id <u>] [--db-path <p>] [--dry-run] [--json]
```

**Behaviour (per F-PV14-02).**
- Refuses unless all selectors resolve to **≤5 rows** (prevents bulk-delete footgun).
- Writes a single `runtime_event_log` row tagged `sync_purge` with the deleted-row payloads as JSON, so the audit chain remains queryable.
- `--dry-run` returns the rows that *would* be deleted without committing.
- Help text recommends `hai backup` before invocation.

**Acceptance.**
1. Unit test: creates 3 fixture rows in `sync_run_log` matching a selector; invokes `hai sync purge --source garmin --for-date 2026-02-10`; verifies exactly the 3 rows are gone + 1 `runtime_event_log` row written with `event_type=sync_purge` + `payload` containing all 3 deleted rows.
2. Refusal test: selector matches 6 rows; CLI exits with USER_INPUT exit code; no rows deleted; no runtime_event_log row written.
3. `--dry-run` test: invocation lists the matching rows on stdout (or as JSON if `--json`); zero rows deleted; zero runtime_event_log rows written.
4. Capabilities manifest entry: `mutation="writes-state"`, `agent_safe=False` (this is a maintainer-side surgical tool; agent invocation would bypass W57-equivalent care), `idempotent="no"`, `json_output=True`.
5. **Snapshot regeneration lockstep (per F-PLAN-R2-04 round-2 fix; round-1 had markdown-only).** The F-PV14-02 commit regenerates `verification/tests/snapshots/cli_capabilities_v0_1_13.json` + `verification/tests/snapshots/cli_help_tree_v0_1_13.txt` + `reporting/docs/agent_cli_contract.md` **in the same commit** as the `hai sync purge` surface adds. `test_cli_parser_capabilities_regression.py` runs clean against the regenerated snapshots. (§3 + §6 specify the lockstep rule; this acceptance item makes it commit-local. Round-1 wording named only the markdown contract — F-PLAN-R2-04 caught the JSON + parser-tree omission.)

**What this WS does NOT do.**
- Does not extend to other tables. `sync_run_log` only.
- Does not auto-purge. Selectors are required.
- Does not implement the broader `--db-path / --base-dir` symmetry rule (F-IR-02 named-defer to v0.1.19 W-FPV14-SYM).

### §2.H W-B — `hai intake weight` body-comp surface + `body_comp` table + migration 026

**Source.** `agent_state_visibility_findings.md` §F-AV-02 (deferred from v0.1.15 round-0 cut per `v0_1_15/PLAN.md` §1.4 row 7).

**Files of record.**
- `src/health_agent_infra/cli/handlers/intake.py` (post-W-29 split — adds `hai intake weight` subcommand).
- `src/health_agent_infra/core/state/migrations/026_body_comp.sql` (new — creates `body_comp` table).
- `src/health_agent_infra/core/body_comp/store.py` (new — `BodyCompRecord` dataclass + `add_body_comp` + `list_body_comp` helpers, mirrors the `core/target/store.py` shape but simpler — no W57 gate per OQ-3).
- Capabilities manifest annotation.

**Schema (round-1 ratified per F-PLAN-09 — user-authored-only v1; no `agent_proposed` enum).**

```sql
CREATE TABLE body_comp (
  body_comp_id     TEXT PRIMARY KEY,
  user_id          TEXT NOT NULL,
  measured_at      TEXT NOT NULL,                -- ISO8601 timestamp
  as_of_date       TEXT NOT NULL,                -- YYYY-MM-DD (denormalised for active-day queries)
  weight_kg        REAL NOT NULL,
  body_fat_pct     REAL,                          -- optional (v1 may always be NULL)
  source           TEXT NOT NULL DEFAULT 'user_authored' CHECK(source = 'user_authored'),
  ingest_actor     TEXT NOT NULL DEFAULT 'cli',
  notes            TEXT,
  created_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_body_comp_user_asof ON body_comp(user_id, as_of_date);
CREATE INDEX idx_body_comp_user_measured ON body_comp(user_id, measured_at);
```

**Source enum simplified at round 1 (per F-PLAN-09):** `'user_authored'` only. The original round-1 PLAN proposed `'user_authored' | 'agent_proposed' | 'wearable_pull'` with an `--ingest-actor`-based agent-block at the CLI layer. Codex F-PLAN-09 caught the contradiction: marking the command `agent_safe=True` but blocking agents at the CLI is incoherent — a capable agent reading the manifest sees `agent_safe=True` and invokes; a self-reported `--ingest-actor` block is bypassable by simply omitting the flag. Cleaner v1 shape: command is **`agent_safe=False`** at the manifest level (agents respect the flag and don't invoke), `source` enum is single-valued, no agent-proposal/commit ceremony required. A future cycle (post-v0.2.x once agent-proposed body-comp is a real use case) can extend the source enum + add a W57-style commit gate.

**Subcommand shape.**

```
hai intake weight \
  --kg <X> [--body-fat-pct <Y>] \
  [--measured-at <ISO8601>] [--as-of <YYYY-MM-DD>] \
  [--notes <free-text>] [--user-id <u>] [--ingest-actor <a>]
```

If `--measured-at` not provided: defaults to current UTC. If `--as-of` not provided: defaults to local date of `measured_at`. `--ingest-actor` is a per-record provenance field (defaults to `cli`; not a security boundary — agents respect `agent_safe=False` at the manifest level).

**Idempotency.** A second `hai intake weight` for the same `(user_id, as_of_date)` does NOT replace the first. It appends a new row (a user might weigh themselves twice on the same day; both are valid — fasted morning + post-meal evening are different observations). Down-stream queries that need "latest weight for day" use `ORDER BY measured_at DESC LIMIT 1`. **OQ-4 ratified per Codex round-1: append (matches measurement reality).**

**Audit chain.** Every `hai intake weight` invocation writes a JSONL audit log entry to `~/.health_agent/body_comp_intake.jsonl` mirroring the existing intake-jsonl pattern.

**Acceptance.**
1. Migration 026 test: applies migration against an empty DB; asserts `body_comp` table exists with the named columns + 2 indexes + the `CHECK(source = 'user_authored')` constraint. Applies migration against a v0.1.15.1-shaped DB (with `target` table at migration 025 and three nutrition rows from the maintainer's live state); asserts existing tables byte-stable; asserts existing migration-025 indexes (`idx_target_active_window`, `idx_target_domain_type`, `idx_target_supersedes`) survive migration 026 with no plan-stability drift.
2. Intake test: `hai intake weight --kg 84.0 --as-of 2026-05-04` writes 1 row to `body_comp`, 1 row to JSONL, returns the new `body_comp_id`. JSON output asserted shape. Asserts `source='user_authored'` regardless of `--ingest-actor` value.
3. Multi-measurement-per-day test: two `hai intake weight` invocations same day write 2 rows; `list_body_comp(as_of_date=2026-05-04)` returns both ordered by `measured_at`.
4. Capabilities manifest entry: `mutation="writes-state"`, **`agent_safe=False`** (per F-PLAN-09 ratification), `idempotent="no"` (each invocation appends), `json_output=True`.
5. Validation: `--kg` must be in (20, 250) inclusive; `--body-fat-pct` in (0, 75) if provided; `as_of_date` must parse as YYYY-MM-DD.
6. JSONL audit log appended on successful intake; absent on validation failure.
7. **Snapshot regeneration lockstep (per F-PLAN-R2-04 round-2 fix).** The W-B commit regenerates `verification/tests/snapshots/cli_capabilities_v0_1_13.json` + `verification/tests/snapshots/cli_help_tree_v0_1_13.txt` + `reporting/docs/agent_cli_contract.md` **in the same commit** as the `hai intake weight` surface adds. `test_cli_parser_capabilities_regression.py` runs clean against the regenerated snapshots. (§3 + §6 specify the lockstep rule; this acceptance item makes it commit-local.)

**What this WS does NOT do.**
- Does not introduce a body-composition target (no `target_type='body_weight_kg'` extension to the `target` table). That's a follow-on feature; v0.1.17 ships only the *measurement* surface.
- Does not auto-pull from wearables (no `hai pull --source garmin --domain body-comp`). Manual intake only in v1.
- Does not surface a 7-day moving average (the F-AV-02 finding mentioned this as optional; v1 ships measurements only; agent or `hai stats` extension can compute trends from the raw rows).
- **Does not introduce an agent-proposal path.** v1 is user-authored measurement only. A future cycle (post-v0.2.x) can extend the source enum + add a W57-style commit gate if agent-proposed body-comp becomes a real use case.

**OQ-3 + OQ-4 closed at round 1** per F-PLAN-09 + Codex round-1 OQ disposition. Removed from §8 open list.

### §2.I W-D arm-2 — partial-day nutrition end-of-day projection

**Source.** `agent_state_visibility_findings.md` §F-AV-04 arm 2 (deferred from v0.1.15 round-0 cut per `v0_1_15/PLAN.md` §1.4 row 10). Completes the v0.1.15 W-D arm-1 known-incomplete fix (arm-1: suppress when no target; arm-2: project when target present).

**Gating dependencies (verified at HEAD).**
- W-A `is_partial_day` signal in tree (v0.1.15.1 — `core/intake/presence.py`).
- W-C `target_status="present"` query against `target` table (v0.1.15.1 — `core/intake/presence.py:163-213` `compute_target_status`).
- W-D arm-1 suppression path in tree (v0.1.15.1 — `domains/nutrition/classify.py` returns `nutrition_status="insufficient_data"` when arm-1 fires).

All three are present at HEAD `df6a13c`. arm-2 fires when `is_partial_day == true && target_status == "present"`.

**Plumbing path (per F-PLAN-01 round-1 fix; F-PLAN-R2-01 round-2 fix — round-1 PLAN had no data path between committed `target` rows and the nutrition classifier; round-2 corrected the actual production call site from "CLI handlers" to `core/state/snapshot.py:909`).**

Verified at HEAD `df6a13c`: 

- **Production classifier call site:** `core/state/snapshot.py:909` `nutrition_classified = classify_nutrition_state(nutrition_signals)` — single call, no thresholds arg currently passed. CLI handlers (`cmd_state_snapshot`, `cmd_synthesize`, `cmd_today`, `cmd_explain`) all consume `build_snapshot()` output; **none call `classify_nutrition_state` directly**. Round-1 §2.I had this wrong — F-PLAN-R2-01 round-2 caught it.
- `core/intake/presence.py:163-213` `compute_target_status()` returns `Literal["present", "absent", "unavailable"]` — the enum string only, no target values.
- `domains/nutrition/classify.py:327` threshold seam: `t = thresholds if thresholds is not None else load_thresholds()`. Treats non-None `thresholds` arg as the **full tree**; subsequent reads at `:362-373` index `t["classify"]["nutrition"]["targets"]` etc. **A partial-dict thresholds override would KeyError** — the override must be a deep-merged full tree (per F-PLAN-R2-01).

**Plumbing shape adopted (round-2 corrected — internal merge inside `build_snapshot()`).** AGENTS.md D13 trusted-by-design seam: `classify_nutrition_state` accepts `thresholds: Optional[dict]`. Production path threads the override through `build_snapshot()`, not through CLI handlers.

1. **New helper** `core/target/store.py::get_active_macro_targets(conn, *, user_id, as_of_date) -> dict[str, float]` reads the four active macro target rows from `target` (post-migration 025) and returns `{"calorie_target_kcal": <kcal>, "protein_target_g": <g>, "carbs_target_g": <g>, "fat_target_g": <g>}`. Same key shape as `DEFAULT_THRESHOLDS["classify"]["nutrition"]["targets"]` (extended with `carbs_target_g` + `fat_target_g`).
2. **Internal merge inside `build_snapshot()`.** When `is_partial_day == true && target_status == "present"`, `build_snapshot()` (a) calls `load_thresholds()` to get a full tree, (b) calls `get_active_macro_targets()` to fetch the four macro values, (c) deep-merges those values into the tree's `classify.nutrition.targets` block, and (d) calls `classify_nutrition_state(nutrition_signals, thresholds=merged_tree)`. When arm-2 conditions don't hold, `build_snapshot()` continues to call `classify_nutrition_state(nutrition_signals)` (no thresholds arg) — pre-W-D-arm-2 behaviour preserved.
3. **No public API change to `build_snapshot()`.** No new external arg; the merge is an internal branch. CLI handlers are unchanged at this layer (they call `build_snapshot()` as before; the snapshot internally selects the projection or pass-through path).
4. **`DEFAULT_THRESHOLDS` extension.** `core/config.py` `DEFAULT_THRESHOLDS["classify"]["nutrition"]` gains a new leaf `"projection_mode": "target_anchored"` (v1 default). The leaf existing in defaults is what makes the linear-extrapolation override (acceptance item 5 below) reachable without a code change — a deep-merged full tree with `projection_mode="linear_extrapolation"` selects the alternative.

**Files of record.**
- `src/health_agent_infra/core/target/store.py` — adds `get_active_macro_targets()` helper (~25 LOC; reads same rows W-A's `compute_target_status` enumerates against, but returns values instead of an enum).
- `src/health_agent_infra/core/state/snapshot.py` — **the production call site for `classify_nutrition_state`.** Adds the internal merge step at lines ~895-909. When arm-2 conditions hold, builds the merged threshold tree + passes to `classify_nutrition_state(thresholds=merged_tree)`; otherwise unchanged. **Also extends `_nutrition_classified_to_dict()` at `:1183-1209`** (per F-PLAN-R3-01 round-3 fix — the serializer is the surface that flows the new fields into `build_snapshot(...).nutrition.classified_state`; without serializer extension the new dataclass fields would only exist in the in-process classifier object).
- `src/health_agent_infra/core/config.py` — adds `classify.nutrition.projection_mode = "target_anchored"` default leaf to `DEFAULT_THRESHOLDS`.
- `src/health_agent_infra/domains/nutrition/classify.py` — adds projection branch reading `t["classify"]["nutrition"]["projection_mode"]` + `t["classify"]["nutrition"]["targets"]`. Emits `projected_eod_kcal`, `projected_eod_protein_g`, `projected_eod_carbs_g`, `projected_eod_fat_g` alongside the observed values. **Also extends the `ClassifiedNutritionState` dataclass at `:94`** with 4 new optional fields (`projected_eod_kcal: Optional[float]`, `projected_eod_protein_g: Optional[float]`, `projected_eod_carbs_g: Optional[float]`, `projected_eod_fat_g: Optional[float]`; default `None` for non-arm-2 paths) per F-PLAN-R3-01 round-3 explicit dataclass-contract fix.
- `src/health_agent_infra/domains/nutrition/policy.py` — no body change; consumes projection-side bands automatically via the existing band-eval seam.
- `src/health_agent_infra/core/synthesis_policy.py` — surfaces projection vs observed in synthesis output.
- `src/health_agent_infra/cli/handlers/inspect.py` (post-W-29 split) — `hai explain` rendering for projection.
- `src/health_agent_infra/cli/handlers/state.py` (post-W-29 split) — **`cmd_state_snapshot` lives here** per v0.1.13 boundary table (round-1 §2.I attributed to `recommend.py` — F-PLAN-R2-01 caught the misattribution). No body edit required; the snapshot path is via `build_snapshot()` internal merge.
- `src/health_agent_infra/cli/handlers/recommend.py` (post-W-29 split) — `cmd_synthesize` lives here. No body edit required for the same reason; `cmd_synthesize` consumes `build_snapshot()` output.

**Projection function (round-1 formula corrected per F-PLAN-01).** Round-1 PLAN proposed `projected_eod = intake_so_far + (target - intake_so_far) * remaining_day_fraction` with `remaining_day_fraction = (target - intake_so_far) / target`. For 1344 kcal intake / 3100 kcal target, that yields **2338.69**, not 3100 — the formula is mathematically inconsistent with the round-1 acceptance assertion `projected_eod_kcal == target_kcal`. Real bug.

**Corrected formula (target-anchored, v1 default):** when `is_partial_day == true && target_status == "present"`, the runtime emits

```
projected_eod_kcal     = target_kcal       (assumes user closes the gap to target by EOD)
projected_eod_protein_g = target_protein_g
projected_eod_carbs_g   = target_carbs_g
projected_eod_fat_g     = target_fat_g
```

The projection IS the target — the user is assumed to close the gap. Calorie-balance evaluation operates on `(target - projected_eod) = 0`, so the band fires `aligned` cleanly.

**Linear-extrapolation alternative** (rejected as v1 default; reachable via threshold override):

```
projected_eod_kcal_linear = intake_so_far_kcal / fraction_of_day_elapsed
                          = intake_so_far_kcal / ((current_local_hour - 0) / 24)
```

Catches the silent-underconsumption case (user is on track to undershoot, projection flags it pre-EOD) but false-flags morning-only intake against any positive midday-intake gap. Trade-off: target-anchored is conservative against partial-day classification noise; linear-extrapolation surfaces underconsumption pre-EOD. **Round-1 PLAN's `remaining_day_fraction_at_target_pace` derivation was a confused hybrid; not retained.** A future cycle can flip the default if dogfood evidence shows the alternative is better-shaped (post-v0.1.18 onboarding or v0.2.x).

**Macro projection scope (round-2 clarified per F-PLAN-R2-01).** v1 projects four macros (kcal, protein, carbs, fat) when target_status=present. **Band classification operates against the projection** for: `calorie_balance_band` (kcal — exists in `DEFAULT_THRESHOLDS`), `protein_sufficiency_band` (protein — exists). **Bands do not exist for carbs and fat** in v0.1.17 (`DEFAULT_THRESHOLDS["classify"]["nutrition"]` has no carbs / fat band defaults; adding them is post-v0.1.17 scope). `projected_eod_carbs_g` and `projected_eod_fat_g` are emitted as **informational fields** in the classified state + `hai explain` rendering; they do not drive a band classification or affect the recommendation. **Hydration is held observed** in v1 (no hydration target in the W-C-shipped 4-row group; W-A's `target_status="present"` is defined over the four macro rows only, per `core/intake/presence.py:NUTRITION_MACRO_TARGET_TYPES`). Hydration-band classification continues to operate on observed values regardless of `is_partial_day`.

**Acceptance — 7 items (round-1 had 6; F-PLAN-01 split target-row lookup + projection emission + classified-band assertions into separate items; F-PLAN-R2-01 round-2 corrected item 5's threshold-override shape).**

1. **Plumbing test** (new `test_w_d_arm2_target_plumbing.py`): Seed `target` rows for `calories_kcal=3100`, `protein_g=160`, `carbs_g=350`, `fat_g=90` (active, covering today). Call `get_active_macro_targets(conn, user_id="u_local_1", as_of_date=today)`. Assert returned dict matches the seeded values. Test uses `core/target/store.py::add_target` to seed and the new `get_active_macro_targets` helper to read.
2. **Projection emission test (against `build_snapshot()` directly)**: Seed the same target rows + record `is_partial_day=true` partial-day intake (1344 kcal, 38 g protein at 10am). Call `build_snapshot(conn, as_of_date=today, user_id="u_local_1", ...)`. Assert the emitted classified-state includes `projected_eod_kcal=3100`, `projected_eod_protein_g=160`, `projected_eod_carbs_g=350`, `projected_eod_fat_g=90` AND `nutrition_status="aligned"` AND `calorie_balance_band="met"` (calorie-deficit at projection = 0) AND `protein_sufficiency_band="met"` (protein-ratio at projection = 1.0; valid band vocabulary per `domains/nutrition/classify.py:86` is `met / low / very_low / unknown` — round-2 PLAN said `"adequate"` which is not a valid band value, F-PLAN-R3-01 round-3 corrected). Currently (v0.1.15.1 W-D arm-1 fallback) misclassifies as `high_deficit`. **Asserts the new fields appear in `build_snapshot(...).nutrition.classified_state`** (i.e., flowed through the `_nutrition_classified_to_dict()` serializer at `core/state/snapshot.py:1183-1209`), not only in the function-level `classify_nutrition_state()` return — per F-PLAN-R3-01 round-3 fix that explicitly named the dataclass + serializer surface.
3. **arm-2/arm-1 boundary test**: With `target_status="absent"` and `target_status="unavailable"`, assertion is `nutrition_status="insufficient_data"`, reason `"partial_day_no_target"` (arm-1 fires; arm-2 does not). No `projected_eod_*` fields emitted.
4. **Day-closed test**: 19:00 intake at `is_partial_day=false`; falls through to existing classifier (no projection branch fires). No `projected_eod_*` fields emitted.
5. **Linear-extrapolation reachability test (round-2 corrected per F-PLAN-R2-01).** Build a **deep-merged full thresholds tree** via `load_thresholds()` (returns `DEFAULT_THRESHOLDS`-shape) and override the `projection_mode` leaf to `"linear_extrapolation"`. Pass that full tree to `classify_nutrition_state(nutrition_signals, thresholds=merged_full_tree)`. Assert the linear-extrapolation projection shape emits (`projected_eod_kcal = intake_so_far / fraction_of_day_elapsed`); assert that the target-anchored shape does NOT emit. Round-1 PLAN passed a partial dict `{"classify": {"nutrition": {"projection_mode": "linear_extrapolation"}}}` — the existing seam at `domains/nutrition/classify.py:327` (`t = thresholds if thresholds is not None else load_thresholds()`) treats non-None as full tree replacement, so the partial dict would KeyError on `t["classify"]["nutrition"]["targets"]`. F-PLAN-R2-01 caught this; round 2 corrected. The override mechanism does NOT require a code change beyond the new `projection_mode` default leaf in `DEFAULT_THRESHOLDS` (which makes `load_thresholds()` return a tree with the leaf already populated; the test override flips the leaf without breaking the tree's structural completeness).
6. **`hai explain` rendering test**: After arm-2 fires, `hai explain --as-of <today>` renders both observed (`calories=1344`) and projected (`projected_eod_kcal=3100`) in the audit-chain bundle. Asserted by an explain-snapshot test (extends or new).
7. **Synthesis-policy integration test**: `cmd_synthesize` consuming arm-2-classified state produces a daily plan that operates against the projected band, not the observed band. The daily-plan recommendation does not propose a recovery/escalation against the false (observed) deficit.

**What this WS does NOT do.**
- Does not introduce a `--running-total` flag on `hai intake nutrition` (the F-AV-04 finding mentioned this as alternative; v1 relies on auto-detection via `is_partial_day`).
- Does not change `target_status="present"` query or W-A's output shape (W-A territory; already in tree).
- Does not change the band thresholds (band tuning is a separate concern from the projection mechanism).
- Does not flip the projection-mode default. Target-anchored is v1; linear-extrapolation is a future-reversible threshold override.

**OQ-5 (closed at round 3, D14 close).** Target-anchored ratified as v1 default per F-PLAN-01 corrected-formula fix + F-PLAN-R3-01 round-3 wording-nit fixes (`protein_sufficiency_band="met"` band-vocabulary correction; `ClassifiedNutritionState` + `_nutrition_classified_to_dict` explicit naming; §4 risk 6 build_snapshot internal-merge prose). Linear-extrapolation reachable via full-tree `projection_mode` threshold override per AGENTS.md D13 seam (now executable). v0.1.18+ can flip the default if dogfood evidence shows it's wrong-shaped.

### §2.J W-C-EQP — EXPLAIN QUERY PLAN stability assertion (small)

**Source.** v0.1.15 IR round 1 §F-IR-04 (acceptance-weak): the v0.1.15-shipped W-C migration test asserts byte-stable row preservation + index-name existence, but the *stronger* EXPLAIN QUERY PLAN stability check was named-deferred. Round 2 §F-IR-R2-02 confirmed durable destination at v0.1.17 W-C-EQP.

**Files of record.**
- `verification/tests/test_w_c_target_nutrition.py` — extends `test_migration_025_preserves_pre_existing_target_rows_byte_stable` with a new assertion block.

**Acceptance.**
1. Test seeds the same three pre-migration rows the v0.1.15 byte-stability test uses (`calories_kcal=3300` archived, `=3100` active, `protein_g=160` active).
2. Applies migration 025.
3. Issues the W-A active-window query: `SELECT 1 FROM target WHERE user_id=? AND domain='nutrition' AND target_type IN ('calories_kcal','protein_g','carbs_g','fat_g') AND status='active' AND superseded_by_target_id IS NULL AND date(effective_from) <= date(?) AND (effective_to IS NULL OR date(effective_to) >= date(?)) LIMIT 1`.
4. Captures the EXPLAIN QUERY PLAN output.
5. Asserts the plan uses `idx_target_active_window` (or whichever rebuilt index covers the predicate). The exact assertion shape: `"USING INDEX idx_target_active_window"` substring in the EXPLAIN output (SQLite's plan-output format).
6. Test fails if the plan falls back to a full table scan (would happen if migration 025's recreate-and-copy didn't rebuild the index correctly, or if a future migration drops the index).

**What this WS does NOT do.** Does not refactor the existing test. Adds a 10-20 LOC assertion block. Doesn't extend to other queries (those are different acceptance items, not in v0.1.17 scope).

---

## 3. Cross-cutting work + governance edits

- **AGENTS.md "Settled Decisions" — W-29 closure update at v0.1.17 ship (provenance-preserving append per F-PLAN-10 round-1 fix).** The current entry is a multi-line block carrying the full multi-cycle redestination chain (v0.1.12 CP1/CP2 origin, v0.2.x CP-PATH-A/CP-W30-SPLIT, v0.1.13 → v0.1.14 → v0.1.15 → v0.1.17 redestination, v0.1.16 cancellation insertion). The ship-time edit **appends** `W-29 closed at v0.1.17 (mechanical split landed; cli.py 9927 LOC → 1 main + 1 shared + 11 handler-group modules, all <2500 LOC; manifest byte-stable; refreshed boundary note at \`reporting/plans/v0_1_17/w29_boundary_refresh.md\`).` to the existing entry. **Retains** the full redestination prose verbatim. **Retains** the W-30 destination clause (`v0.2.3 capabilities-manifest schema freeze remains scheduled`) verbatim — W-30 stays scheduled, only W-29 closes. The audit chain that justified W-29's multi-cycle redestination is preserved, not collapsed.
- **AGENTS.md "Do Not Do" — cli.py-split clause retired at v0.1.17 ship (provenance-preserving clause-removal per F-PLAN-10 round-1 fix).** The current entry is a multi-paragraph block: `"Do not split \`cli.py\` or freeze the capabilities manifest schema before their scheduled cycles (v0.1.17 / v0.2.3)."` followed by an origin/destination provenance tail (CP1/CP2/CP-PATH-A/CP-W30-SPLIT, multi-cycle redestination history). The ship-time edit retires **only the cli.py clause**; the W-30 freeze clause + its full provenance tail stay. Rewritten lead sentence: `"Do not freeze the capabilities manifest schema before its scheduled cycle (v0.2.3)."` Provenance tail unchanged.
- **`reporting/docs/architecture.md`** — extend with body-comp surface (W-B) + projection branch in nutrition (W-D arm-2) + the cli/handlers/ module layout (W-29).
- **`reporting/docs/state_model_v1.md`** — document the new `body_comp` table (W-B / migration 026).
- **Capabilities manifest snapshot regeneration (per F-PLAN-07 round-1 fix — round-1 PLAN had inconsistent "lockstep" vs "end-of-cycle" wording).** **Each intentional CLI-surface commit** (W-AI-2 `hai eval review`, F-PV14-02 `hai sync purge`, W-B `hai intake weight`) regenerates the manifest snapshot (`verification/tests/snapshots/cli_capabilities_v0_1_13.json`) + parser-tree snapshot (`verification/tests/snapshots/cli_help_tree_v0_1_13.txt`) **in the same commit**. The `test_cli_parser_capabilities_regression.py` test runs every pytest invocation and asserts equality against the snapshot files; if a CLI-surface commit lands without a co-committed snapshot regeneration, the test gate is red until the next commit. The W-29 byte-stability gate (§2.A acceptance items 4-6) is the **pre-add comparison**: W-29 must be byte-identical against the snapshot current at Phase 1 open; later intentional adds update the baseline as part of those same W-id commits. **Final cycle state**: snapshot matches the post-W-29 + post-Phase-2/3-additions cli.py exactly.
- **`tactical_plan_v0_1_x.md`** — §5D updated at v0.1.17 ship (status: shipped); §5E v0.1.18 row reflects "v0.1.17 close confirmed" precondition.
- **`reporting/plans/README.md` reading-order index** — v0.1.17 marked shipped at ship-time; cycle dir referenced in the "current cycle" section.
- **`AUDIT.md`** — new row for v0.1.17 (round-by-round D14 + IR table + outcome verdict + RELEASE_PROOF link).
- **`CHANGELOG.md`** — v0.1.17 entry summarising W-29 + W-30 + W-AH-2 + W-AI-2 + W-AM-2 + W-Vb-4 + F-PV14-02 + W-B + W-D arm-2 + W-C-EQP.
- **`README.md` "Now / Next"** — reflects v0.1.17 → v0.1.18.

---

## 4. Risks + hidden coupling

1. **W-29 boundary table drift + abort paths (the largest cycle risk; F-PLAN-05 round-1 fix; F-PLAN-R2-03 round-2 single-halt simplification).** The v0.1.13 W-29-prep boundary table assumed cli.py at 8891 LOC + 56 leaf commands; v0.1.17 cycle-open has cli.py at 9927 LOC + 60 leaf commands (+1036 LOC, +4 commands). The most material drift is in `intake.py` (W-A `intake gaps` added post-v0.1.13) and `target.py` (W-C `target nutrition` 4-row convenience handler added post-v0.1.13). **Mitigation:** §2.A acceptance item 1 requires a refreshed boundary note at `reporting/plans/v0_1_17/w29_boundary_refresh.md` BEFORE any split commit, with explicit `split` / `split-with-revisions` / `do-not-split` verdict. Three abort branches: **(a)** if the refreshed verdict is `do-not-split` (e.g. hidden cross-handler shared state pattern that prevents clean separation), §2.A acceptance item 2 **halts the cycle**; PLAN.md re-authors through D14 round 2+ with W-29 release-blocker status, §3 governance edits, §6 W-29 gates, §7 v0.1.18 dependency, README, tactical §5D/§5E, and W-29-3 destination all reconsidered. **The round-1 "Phase 2 + Phase 3 ship without W-29" branch was retired at round 2** per F-PLAN-R2-03 as unsafe (Phase 2/3 CLI-surface adds depend on the split). **(b)** if the refreshed verdict is `split-with-revisions` (e.g. `intake.py` exceeds 2500 LOC), sub-split per the v0.1.13 boundary table's "may further split" footnote (e.g. `intake_food.py` for gym/exercise/nutrition + `intake_subjective.py` for stress/readiness/note/gaps). Acceptance item 7 (no group ≥2500 LOC asserted by `test_cli_handler_group_loc_ceiling.py`) catches the breach mechanically. **(c)** if even the sub-split breaches 2500 LOC for any group, escalate to maintainer for re-shape. The W-29 split landing at all is the cycle's release-blocker; the LOC ceiling is the second-order risk.

2. **W-29 ↔ Phase 2/3 commit serialisation.** Every Phase 2/3 W-id that adds a CLI surface (W-AI-2, F-PV14-02, W-B) must commit AFTER W-29 to avoid merging into pre-split cli.py. **Mitigation:** Phase 1 (W-29 + W-30) is gated to commit before Phase 2/3 fires. Implementer enforces by working in cycle-branch order: W-29 commit → W-30 commit → Phase 2/3 commits. If two implementers work in parallel (not expected for a 1-maintainer cycle), the post-W-29-commit branch is the merge base.

3. **W-AH-2 evidence-grounding honesty (the v0.1.16-cancellation residual).** §1.4 honesty boundary names this risk: W-AH-2's "evidence-grounded" claim reads against synthetic + dogfood evidence, not foreign-user transcript. **Risk:** scenarios encode runtime contracts that *appear* correct but miss the foreign-user friction patterns v0.1.19 will surface. **Mitigation:** (a) Acceptance item 2 — every fixture validates against live runtime before commit. (b) §6 ship-claim language explicitly says "synthetic-coverage expansion," not "foreign-user-validated coverage." (c) v0.1.19 cycle still authors PLAN.md against actual transcript — if W-AH-2 fixtures encoded a wrong contract, v0.1.19's empirical work will catch it and surface the delta as a finding to feed back into a future scenario-corpus update. **Residual:** v0.1.17's W-AH-2 ships honest-but-bounded coverage; the foreign-user empirical proof remains v0.1.19's claim.

4. **W-AM-2 per-scenario validation friction (the v0.1.14 lesson).** v0.1.14 W-AM authored 6 escalate-tagged scenarios but only 2 fired their expected tokens against live runtime; honest count was 2-of-6, the remaining 4 fork-deferred to W-AM-2. **Risk:** the same shape recurs at v0.1.17 — scenarios that look right in isolation fail live validation. **Mitigation:** Per-scenario interactive author-then-validate workflow per v0.1.14 REPORT.md §5.3 (mandated in §2.E). If a scenario can't fire its expected token after iteration, drop it + log as a runtime-contract finding (not silent absorption). Cumulative count gate: 6 of 6 in §2.E acceptance — if it slips to 5 of 6, partial-closure gets a destination (e.g. v0.1.18 or v0.2.0) rather than silent ship.

5. **W-B ↔ v0.2.x schema-group plan (cohesion check).** AGENTS.md "Settled Decisions" v0.1.12 CP1 + post-v0.1.13 CP-PATH-A names the v0.2.x schema groups: v0.2.0 = W52 + W58D claim-block, v0.2.1 = W53, v0.2.2 = W58J, v0.2.3 = W-30 freeze. **Risk:** W-B introduces a new `body_comp` table at v0.1.17 — does this collide with a planned v0.2.x schema group? **Verification:** strategic_plan_v1.md §10 (Wave 3) enumerates v0.2.x schema additions — review/factuality/insight ledger/judge schema — none touch `body_comp` or any body-composition surface. **Mitigation:** W-B's migration 026 lands as an isolated table addition; it does NOT touch `target` (already extended at migration 025), does NOT touch `proposal_log` / `daily_plan` / `recommendation_log` / `review_outcome` (the existing audit-chain four-table contract), does NOT extend the capabilities-manifest schema beyond adding one new command annotation. The v0.2.x schema-freeze plan at v0.2.3 will encompass `body_comp` as a settled-by-then table. **Residual:** none.

6. **W-D arm-2 projection-function default (semantics call) + plumbing path (round-1 F-PLAN-01 fix; F-PLAN-R2-01 round-2 fix; F-PLAN-R3-01 round-3 fix).** OQ-5 ratified at round 3 close (target-anchored as v1 default). **Risk (semantics):** target-anchored projection assumes user will close the gap to target by end of day — if the user persistently undereats, the projection silently classifies as aligned when the user is actually drifting toward deficit. Linear-extrapolation catches that case but false-flags morning-intake-only against any positive midday-intake gap. **Mitigation:** target-anchored ratified as v1 default per F-PLAN-01 corrected formula (`projected_eod = target` directly; round-1's `remaining_day_fraction_at_target_pace` derivation was mathematically inconsistent with its own acceptance test — 1344/3100 yielded 2338, not 3100). Linear-extrapolation reachable via full-tree `projection_mode` threshold override per AGENTS.md D13 seam. Both observed and projected emitted in `hai explain`; user reads both. v0.1.18+ can flip the default if dogfood evidence shows it's wrong-shaped. **Risk (plumbing):** round-1 PLAN had no data path between committed `target` rows and the nutrition classifier (`compute_target_status` returns enum string only; classifier reads from thresholds config). **Mitigation:** §2.I "Plumbing path" specifies new helper `core/target/store.py::get_active_macro_targets()` + **internal merge inside `build_snapshot()`** at `core/state/snapshot.py` (round-2 F-PLAN-R2-01 corrected the round-1 claim that the merge happened at `cmd_synthesize` / `cmd_state_snapshot` call sites — the actual production classifier call is in `build_snapshot()` at `:909`; CLI handlers consume `build_snapshot()` output unchanged). Macro projection scope: calories + protein + carbs + fat (hydration held observed; no hydration target in W-C 4-row group).

7. **Eval-corpus runtime expansion (F-PLAN-03 round-1 fix — round-1 PLAN claimed persona-matrix runtime expansion driven by scenario corpus growth; mechanism doesn't exist).** W-AH-2 + W-AM-2 expand the scenario corpus 35 → 132+ (3.7×). The actual runtime mechanism is `hai eval run --scenario-set all` (not the persona matrix — those are independent code paths: persona runner reads CLI workflows, `hai eval run` reads `evals/scenarios/`). **Risk:** `hai eval run --scenario-set all` runtime grows roughly linearly with corpus size; v0.1.14 baseline runtime is per-domain bounded. Post-W-AH-2 runtime may push the full-corpus run from ~minutes to ~tens-of-minutes. **Mitigation:** `hai eval run` is not a CI gate (per AGENTS.md D10 — "full matrix runs are not part of CI"; same posture as persona matrix). Runtime expansion is acceptable. Document the post-W-AH-2 runtime in REPORT.md if it materially exceeds the v0.1.14 baseline. **Persona matrix runs separately as a standard substantive-cycle ship gate** (per §6) — independent of the eval-corpus gate; persona runtime is not affected by scenario corpus growth.

8. **W-29 mid-split test isolation hazard.** The pytest suite has documented assumptions about test isolation (CLAUDE.md "Plan-mode triggers" — "the suite has documented assumptions about test isolation; large additions need a sanity check"). **Risk:** moving handlers to new module paths could break test imports or fixture-loader paths in subtle ways. **Mitigation:** acceptance items 8-10 (full pytest + mypy + bandit clean post-split) catch import-shape breakage. New `test_cli_handler_dispatch_smoke.py` (acceptance item 5) covers the more subtle case — `dest` rename or handler-namespace break that the manifest-shape test would miss. If a test breaks, the W-29 commit reverts and re-shapes; doesn't ship a partially-passing suite.

9. **F-PV14-02 ↔ `hai sync purge` agent_safe annotation.** §2.G acceptance item 4 marks the new subcommand `agent_safe=False`. **Risk:** an agent invokes `hai sync purge` because it sees the command in the manifest; the ≤5-row safety cap and runtime_event_log audit prevent silent corruption, but the agent action is not user-gated. **Mitigation:** `agent_safe=False` in the manifest is the contract — capable agents respect the flag. Help text recommends `hai backup` first. Audit chain (`runtime_event_log`) records every invocation. **Residual:** an agent that ignores the manifest can still invoke this; the audit record + safety cap are the second-line defence.

10. **Sizing residual.** **25-40 days** at this PLAN's draft. v0.1.14 was estimated 30-43 d, closed at 35 d; v0.1.15 was 15-24 d, closed at ~16 d. **Mitigation:** no W-id is solo-release-blocker except W-29; if W-29 lands cleanly and Phase 2/3 surfaces unexpected friction, individual W-ids can fork-defer to v0.1.18+ with named scope per AGENTS.md "Honest partial-closure naming." Cycle does NOT silently ship 8-of-10.

11. **Dual-repo confusion (carry-over invariant).** Stale checkout at `/Users/domcolligan/Documents/health_agent_infra/`. AGENTS.md "Active repo path" preamble + the v0.1.15 PLAN §4 risk 8 mitigation propagate forward. D14 audit prompt Step 0 requires `pwd == /Users/domcolligan/health_agent_infra`. No new mitigation needed; existing durable contract holds.

---

## 5. Effort arithmetic

| WS | Best | Mid | Worst |
|---|---|---|---|
| W-29 | 4 | 5 | 6 |
| W-30 | 0.5 | 0.5 | 0.5 |
| W-AH-2 | 4 | 5 | 6 |
| W-AI-2 | 3 | 3.5 | 4 |
| W-AM-2 | 2 | 2.5 | 3 |
| W-Vb-4 | 5 | 6 | 7 |
| F-PV14-02 | 1 | 1.5 | 2 |
| W-B | 3 | 3.5 | 4 |
| W-D arm-2 | 2 | 2.5 | 3 |
| W-C-EQP | 0.5 | 0.5 | 0.5 |
| **Total** | **25** | **30.5** | **36** |

Adjusted for inter-WS coordination overhead (~5%) + Phase 0 + D14 + IR cycle overhead (~10%): **25 - 32 - 40 days**, headlined as **25-40**.

D14 expectation: budgeted **2-4 rounds** per AGENTS.md empirical norm. v0.1.17 is structurally lower-density than v0.1.14 (35 d, 4 D14 rounds) and v0.1.12 (substantive governance edits, 4 D14 rounds) — most of v0.1.17's catalogue is inherited from prior release-proofs with established source contracts, so cross-cutting consistency findings should be lower density. **Realistic round expectation: 2-3 rounds.** 1-round is unlikely (the renumber narrative + W-AH-2 honesty boundary alone give round-1 surface area); 4-round would indicate a problem in PLAN-author craft or a missing cross-doc consistency sweep.

IR expectation: 2-3 rounds at the 5 → 2 → 1-nit empirical norm.

---

## 6. Ship gates

Standard substantive-cycle gates:
- Full pytest suite green (narrow + broader warning gates).
- `uvx mypy src/health_agent_infra` clean.
- `uvx bandit -ll -r src/health_agent_infra` clean.
- `uv run hai capabilities --json` round-trip stable. **Byte-identical against W-29 Phase 1-open snapshot for §2.A acceptance items 4-6** (release-blocker, asserted at the W-29 commit). **Per-W-id regeneration** for subsequent intentional CLI-surface commits (W-AI-2 / F-PV14-02 / W-B): each commit updates the snapshot **in the same commit**, per F-PLAN-07 round-1 fix. Final cycle state: snapshot matches the post-W-29 + post-Phase-2/3-additions cli.py exactly.
- `uv run hai capabilities --markdown > reporting/docs/agent_cli_contract.md` regenerated per intentional CLI-surface commit (same per-commit cadence as the JSON snapshot).
- Full persona matrix run (12 personas; P1..P12 close; P13 matrix-only; **W-Vb-4 brings P7..P12 into closure scope this cycle**). Persona matrix is independent of `hai eval run --scenario-set all` (per F-PLAN-03 round-1 fix; the two run separate code paths).
- **`hai eval run --scenario-set all`** returns OK exit code / 100% pass-rate against the post-W-AH-2 corpus (per F-PLAN-03 round-1 fix — eval-corpus gate replaces the round-1 PLAN's incorrect "persona-matrix-as-scenario-corpus-gate" claim; per F-PLAN-R2-02 round-2 fix — tightened from round-1's `≥95%` because `hai eval run` has no aggregate-percentage mode and any failed scenario returns non-zero).
- AGENTS.md "Settled Decisions" updates per §3 — **provenance-preserving append** per F-PLAN-10 round-1 fix (W-29 closure appended; W-30 destination + full multi-cycle redestination chain retained verbatim).
- AGENTS.md "Do Not Do" cli.py-split clause retired per §3 — **provenance-preserving clause-removal** per F-PLAN-10 round-1 fix (W-30 freeze clause + provenance tail retained).
- AUDIT.md + CHANGELOG entries authored.
- Ship-time freshness checklist from AGENTS.md fully ticked.
- pyproject.toml version bumped to `0.1.17`.
- `RELEASE_PROOF.md` authored; first line declares **Tier: substantive** per D15.
- `REPORT.md` authored.

W-29-specific gates (release-blocker):
- §2.A acceptance items 1-10 all pass (round-1 had 8 items; expanded to 10 per F-PLAN-05 + F-PLAN-06 round-1 fixes — added item 1 refreshed-boundary-note gate, item 2 do-not-split abort path, item 5 handler-dispatch-smoke test).
- `reporting/plans/v0_1_17/w29_boundary_refresh.md` (new pre-flight artifact) returns `split` or `split-with-revisions` verdict; if `do-not-split`, cycle halts per item 2.
- `test_cli_handler_group_loc_ceiling.py` (new) ships and asserts no group ≥2500 LOC.
- `test_cli_handler_dispatch_smoke.py` (new) ships and exercises one non-default flag per moved handler group (≥11 smoke tests).

W-AH-2-specific gates:
- §2.C acceptance items 1-5 all pass.
- New `test_scenario_corpus_coverage.py` ships and asserts per-domain ≥20 + synthesis ≥12.
- **`hai eval run --scenario-set all` returns OK exit code (100% pass-rate)** (per F-PLAN-03; eval-corpus gate, not persona-matrix gate; per F-PLAN-R2-02 round-2 — tightened from round-1's `≥95%` to match the existing CLI's `failed == 0` exit-code contract).

W-AI-2-specific gates:
- §2.D acceptance commit-gate items 1-7 all pass at W-AI-2 commit time (against the at-commit corpus, not a hard-coded count; including snapshot regeneration lockstep at item 7) — per F-PLAN-04 round-1 split + F-PLAN-R2-04 round-2 lockstep + F-PLAN-R3-02 round-3 item-range correction.
- §2.D acceptance ship-gate item passes at end-of-cycle (`hai eval review list --corpus all` returns post-W-AH-2 132+ + W-AM-2 6 + judge_adversarial 31).

W-AM-2-specific gates:
- §2.E acceptance items 1-5 all pass.
- Cumulative escalate count: 6 of 6 OR honest partial-closure with named destination.

W-Vb-4-specific gates:
- §2.F acceptance items 1-5 all pass.
- 12-of-12 cumulative persona closure (or honest partial-closure with named destination per AGENTS.md "Honest partial-closure naming").

W-B-specific gates:
- §2.H acceptance items 1-7 all pass (including snapshot regeneration lockstep at item 7) — per F-PLAN-R2-04 round-2 lockstep + F-PLAN-R3-02 round-3 item-range correction.
- Migration 026 head bumped; v0.1.15.1-shaped DBs migrate cleanly.
- Capabilities manifest entry registers `agent_safe=False` (per F-PLAN-09 round-1 ratification).

W-D arm-2-specific gates:
- §2.I acceptance items 1-7 all pass (round-1 had 6; expanded to 7 per F-PLAN-01 round-1 fix splitting plumbing-test + projection-emission-test + classified-band assertions).
- New `test_w_d_arm2_target_plumbing.py` ships.
- `core/target/store.py::get_active_macro_targets()` helper ships.

PyPI publish gates (post-IR-close):
- D15 IR closes SHIP / SHIP_WITH_NOTES.
- All standard + WS-specific gates above green.
- `uvx --from build python -m build --wheel --sdist` clean.
- Wheel smoke-tested locally (`uv run pip install --force-reinstall dist/...whl` then `uv run hai capabilities --json` round-trips and shows the new commands).
- PyPI upload via `uvx twine upload`.
- Verify install via `pipx install --force --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" 'health-agent-infra==0.1.17'`.

---

## 7. What this PLAN does NOT cover

- **v0.1.18 onboarding work** (W-OB-1 .. W-OB-6) — `reporting/plans/v0_1_18/README.md`. README quickstart pivot is partly pre-staged on main as a low-risk in-flight delta authored 2026-05-04, but **W-OB-2 default-flip explicitly depends on the W-29 cli.py split landing first** (v0.1.18 §1.3 sequencing). v0.1.17 PLAN does NOT pull onboarding work forward.
- **v0.1.19 foreign-user empirical** (W-2U-FIX-P1, W-2U-FIX-P2, W-EXPLAIN-UX-2, W-FPV14-SYM, W-OB-FU-RESIDUAL) — `reporting/plans/v0_1_19/README.md`. Renumbered from cancelled v0.1.16 on 2026-05-04. No transcript exists; cycle opens when one does.
- **v0.2.0 scope:** weekly review (W52) + deterministic factuality (W58D) + 4 doc-only adjuncts (Path A) per `tactical_plan_v0_1_x.md` §5G. v0.2.0 hard deps are v0.1.19 (foreign-user session fixes consolidated) + v0.1.14 substrate. v0.1.17 work is parallelizable with v0.2.0; not a hard dep.
- **v0.2.1+ scope:** W53 insight ledger, W58J judge shadow, W-30 capabilities-manifest schema freeze (final destination v0.2.3 per CP-W30-SPLIT).
- **Apple Health / Whoop adapters** — post-v0.2.x.
- **AGENTS.md governance edits beyond §3.** No new D-entries proposed in v0.1.17. No "Do Not Do" reversals beyond the cli.py-split retirement at ship.
- **AGENTS.md "Active repo path" preamble** (settled v0.1.15 W-PLAN-12) — unchanged.

---

## 8. Open questions (D14 closed at round 3)

**D14 closed at round 3.** 7 of 8 OQs ratified across rounds 1-3; 1 OQ holds to W-29 Phase 1 close (no longer a D14 question — it's a Phase 1 implementation decision).

**Closed at round 1:**
- ~~OQ-2 (W-AI-2 persistence path)~~ — closed: user state dir per Codex round-1 opinion.
- ~~OQ-3 (W-B W57 / agent_safe)~~ — closed via F-PLAN-09 PLAN edit: `agent_safe=False`, `source='user_authored'` only, no `agent_proposed` enum.
- ~~OQ-4 (W-B same-day collision)~~ — closed: append per Codex round-1 opinion.
- ~~OQ-7 (W-AM-2 mechanisation)~~ — closed via F-PLAN-02 PLAN edit: stay on existing `expected.policy.forced_action` contract; no harness extension.

**Closed at round 3 (per Codex round-3 disposition + F-PLAN-R3-01/02/03 close-in-place):**
- ~~OQ-5 (W-D arm-2 projection-function default)~~ — closed: target-anchored ratified as v1 default. Linear-extrapolation reachable via full-tree `projection_mode` threshold override per AGENTS.md D13 seam (the seam is now executable per F-PLAN-R2-01 round-2 fix + F-PLAN-R3-01 round-3 wording-nit fixes). v0.1.18+ can flip the default if dogfood evidence shows it's wrong-shaped.
- ~~OQ-6 (W-AH-2 per-domain distribution)~~ — closed: 20/domain × 6 domains + 12-15 synthesis = 132-135 total ratified. 100% eval-corpus gate matches the existing CLI contract per F-PLAN-R2-02 round-2 tightening.
- ~~OQ-8 (W-29 atomic commit vs series)~~ — closed: 3-commit series ratified. §2.A acceptance item 3: "every commit in the W-29 series must individually pass acceptance items 4-7; the final commit closes the byte-stability gate." `do-not-split` branch halts for re-authoring per F-PLAN-R2-03 round-2 fix.

**Carrying to W-29 Phase 1 close (no longer a D14 question):**

- **OQ-1 — `hai sync` handler-group placement (W-29 + F-PV14-02 cross-cut).** Should `hai sync purge` (and any future `hai sync ...` subcommand) live in `cli/handlers/state.py` (as a sibling of `hai state migrate` / `read` / `snapshot`) or get its own `cli/handlers/sync.py` group? **Provisional default:** state.py — `hai sync purge` is a state-mutation surgical surface that fits the state-handlers shape. **Codex round-3 opinion:** "Keep open until W-29 Phase 1 boundary refresh. The current default (`state.py`, with `sync.py` available if the boundary note says so) is coherent." **Decision destination:** §2.A acceptance item 1's refreshed boundary note (`reporting/plans/v0_1_17/w29_boundary_refresh.md`) — if `state.py` is near the 2500-LOC ceiling or conceptually muddy after the boundary refresh, use `sync.py`; otherwise default to `state.py`. Phase 1 implementation decision, not D14.

---

## 9. Provenance + evolution

- 2026-05-02 evening: `reporting/plans/v0_1_17/README.md` authored as part of the v0.1.15 scope-restructure round-0 self-audit. 9 of 16 catalogued slots assigned to v0.1.17 (W-29 + W-30 + W-AH-2 + W-AI-2 + W-AM-2 + W-Vb-4 + F-PV14-02 + W-B + W-D arm-2). Provisional scope, not yet open.
- 2026-05-03 evening: v0.1.15 IR round 1 §F-IR-04 named-deferred W-C-EQP to v0.1.17. Round 2 §F-IR-R2-02 ratified durable destination. Catalogue grows from 9 to 10 W-ids.
- 2026-05-04: v0.1.16 cancelled (named foreign-user candidate unavailable). v0.1.17 promoted to next-active. Foreign-user precondition retired. v0.1.18 inserted (onboarding cycle, new); v0.1.19 created (renumbered from cancelled v0.1.16, foreign-user empirical). v0.1.17 README updated to reflect: (a) precondition retirement, (b) W-AH-2 honesty boundary (synthetic + dogfood evidence, not foreign-user transcript). Tactical plan §5C (cancellation) + §5D (this cycle) + §5E (v0.1.18) + §5F (v0.1.19) + §5G (v0.2.0) updated. AGENTS.md "Settled Decisions" cli.py-split destination chain updated. Cycle workspace prepped for cycle-open session.
- 2026-05-04: this PLAN authored (round 1). Pre-D14 round 1.
- 2026-05-04 (D14 round 1 closed PLAN_COHERENT_WITH_REVISIONS): 11 findings (F-PLAN-01..11). All AGREED + applied. Triage detail in `codex_plan_audit_response_response.md`.
- 2026-05-04 (D14 round 2 closed PLAN_COHERENT_WITH_REVISIONS): **5 findings** (F-PLAN-R2-01..05). All AGREED + applied in this round-3 edit pass. Halving signature **11 → 5** matches AGENTS.md empirical norm `10 → 5 → 3 → 0`. Round-1 closure verdicts: 6 of 11 CLOSED outright (F-PLAN-02 / F-PLAN-04 / F-PLAN-06 / F-PLAN-09 / F-PLAN-10 / F-PLAN-11); 5 CLOSED_WITH_RESIDUAL (F-PLAN-01 / F-PLAN-03 / F-PLAN-05 / F-PLAN-07 / F-PLAN-08). Round-2 findings were second-order from round-1 revisions per AGENTS.md "Audit-chain empirical settling shape": F-PLAN-R2-01 W-D arm-2 plumbing-path corrections (production classifier call site is `core/state/snapshot.py:909`, not CLI handlers; threshold seam treats non-None as full tree so partial-dict override KeyErrors; `cmd_state_snapshot` lives in `state.py` not `recommend.py` per v0.1.13 boundary table; `projection_mode` default leaf added to `DEFAULT_THRESHOLDS`); F-PLAN-R2-02 ≥95% eval-corpus gate retired (existing `hai eval run` has no aggregate-percentage mode; `cmd_eval_run` returns OK only when `failed == 0`; tightened to 100% pass — v0.1.14 baseline); F-PLAN-R2-03 W-29 `do-not-split` fork-defer branch retired (Phase 2/3 CLI-surface adds depend on the split landing first; collapsed to single halt-and-re-author branch with all downstream surfaces named); F-PLAN-R2-04 per-WS snapshot-lockstep acceptance items added to §2.D / §2.G / §2.H (round-1 had the rule in §3 + §6 only); F-PLAN-R2-05 tactical LOC baseline corrected (8891 vs 9217 dual-baseline note added; tactical §5D row 703 reattributed; tactical line 49 top-row LOC updated). Triage detail in `codex_plan_audit_round_2_response_response.md`. Round-2 OQ dispositions: OQ-1 held to W-29 Phase 1 close; OQ-5/6/8 closeable at round 3 if revisions hold.
- 2026-05-04: D14 round 3 prompt authored at `codex_plan_audit_round_3_prompt.md`; narrow surface per Codex round-2 closure recommendation.
- 2026-05-05 (D14 round 3 closed PLAN_COHERENT_WITH_REVISIONS, **close in place — no round 4**): **3 findings** (F-PLAN-R3-01..03). All AGREED + applied in this final D14 edit pass. Halving signature **11 → 5 → 3** matches AGENTS.md empirical norm `10 → 5 → 3 → 0` exactly — thrice-validated (v0.1.11, v0.1.12, v0.1.17). Round-2 closure verdicts: 3 of 5 CLOSED outright (F-PLAN-R2-02, F-PLAN-R2-03, F-PLAN-R2-05); 2 CLOSED_WITH_RESIDUAL (F-PLAN-R2-01 → F-PLAN-R3-01; F-PLAN-R2-04 → F-PLAN-R3-02). Round-3 findings were third-order text/contract nits: F-PLAN-R3-01 W-D arm-2 stale classifier-contract details (`protein_sufficiency_band="adequate"` → `"met"` per actual band vocabulary at `domains/nutrition/classify.py:86`; §4 risk 6 prose still cited retired `cmd_synthesize`/`cmd_state_snapshot` call sites — corrected to build_snapshot internal-merge; §2.I files-of-record + acceptance item 2 explicit `ClassifiedNutritionState` dataclass + `_nutrition_classified_to_dict` serializer naming so `projected_eod_*` fields actually flow through to `build_snapshot(...).nutrition.classified_state`); F-PLAN-R3-02 §6 W-AI-2 + W-B item-range 1-6 → 1-7 sweep (round-2 added item 7 snapshot-lockstep but didn't sweep §6 gate text); F-PLAN-R3-03 round-status / OQ wording stale (README "round 2 pending" → D14 closed; §8 subheading "Carrying to round 2" → "Carrying to W-29 Phase 1 close"; OQ-5/6/8 closed at round 3 per Codex disposition; OQ-1 held to W-29 Phase 1 boundary refresh). Triage detail in `codex_plan_audit_round_3_response_response.md`. **D14 closes; no round 4 prompt authored** per Codex round-3 closure recommendation ("After applying them, the maintainer can close D14 round 3 without scheduling round 4"). OQ count at D14 close: **OQ-1 only** (W-29 Phase 1 implementation decision; not D14).
- **D14 closed 2026-05-05 at round 3.** PLAN.md ratified for cycle open. **Phase 0 (D11) bug-hunt opens next** per AGENTS.md substantive-cycle pattern: internal sweep + audit-chain probe + persona matrix (12 personas; baseline pre-W-Vb-4) + optional Codex external bug-hunt audit, consolidating to `audit_findings.md`. Pre-implementation gate fires after; Phase 1 W-29 + W-30 commits open after the gate.
