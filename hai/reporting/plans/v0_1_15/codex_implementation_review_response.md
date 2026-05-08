# Codex Implementation Review - v0.1.15 (Phase 1+2)

**Verdict:** SHIP_WITH_FIXES
**Round:** 1

## Verification summary

- Tree state: active tree confirmed at `/Users/domcolligan/health_agent_infra` on `main`. HEAD is `90f666e` (the D15 IR prompt commit) followed by the expected six implementation commits through `0fd5179`; this is not the stale `/Users/domcolligan/Documents/...` checkout. Worktree has unrelated pre-existing research-note changes: `reporting/plans/README.md` and `reporting/plans/post_v0_1_14/anthropic_personal_guidance_report.md`.
- Test surface: `2624 passed, 3 skipped` verified via `uv run pytest verification/tests -q`.
- Type check: `uvx mypy src/health_agent_infra` passed (`Success: no issues found in 128 source files`).
- Security gate: `uvx bandit -ll -r src/health_agent_infra` failed with 2 medium B608 findings in the new W-A presence queries.
- Capabilities: `uv run hai capabilities --json | ...["hai_version"]` reports `0.1.14.1`, as expected pre-RELEASE_PROOF. `uv run hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md` is identical.
- AGENTS.md settled decisions: unchanged from `f593b5a`.

## Findings

### F-IR-01. Bandit gate fails on W-A target-status SQL

**Q-bucket:** Q-IR-X.a / Q-IR-X.d / Q-IR-W-A
**Severity:** security
**Reference:** `src/health_agent_infra/core/intake/presence.py:152-172`; `uvx bandit -ll -r src/health_agent_infra`

**Argument:** The requested ship gate is red. Bandit reports two medium B608 findings for `compute_target_status()` because both target-table queries are f-strings with an interpolated placeholder list. This appears to be a false positive in substance: the placeholder count is derived from the module constant `NUTRITION_MACRO_TARGET_TYPES`, and all target values are still bound parameters. But the release gate is defined mechanically as "0 high/medium new findings", so Phase 3 should not open while this command exits non-zero.

**Recommended response:** Rewrite the query to avoid f-string SQL construction, or add narrow `# nosec B608` annotations with the same constant-placeholder rationale already used in `core/target/store.py`. Re-run Bandit and record the clean output in the round-2 IR response.

### F-IR-02. CSV-fixture default-deny is bypassed by `hai daily`

**Q-bucket:** Q-IR-F-PV14-01.a / Q-IR-F-PV14-01.b / Q-IR-X.d
**Severity:** correctness-bug
**Reference:** `src/health_agent_infra/cli.py:172-209`, `src/health_agent_infra/cli.py:5113-5144`, `src/health_agent_infra/cli.py:9003-9044`

**Argument:** F-PV14-01's guard exists only in `cmd_pull()`. The production daily path calls `_daily_pull_and_project()`, resolves the same source, directly chooses `GarminRecoveryReadinessAdapter()` for `source == "csv"`, opens a sync row, and loads the fixture without checking demo state, `--allow-fixture-into-real-state`, or canonical DB posture. `hai daily` exposes `--source csv` and also auto-falls back to CSV when Intervals.icu credentials are absent, but it has no matching allow flag. This recreates the original contamination class for the daily orchestrator: fixture-shaped rows can land in canonical `sync_run_log` / accepted state through the path most likely to be used in a foreign-user gate.

**Recommended response:** Centralize the F-PV14 CSV/canonical refusal into a helper used before any CSV adapter writes through `_open_sync_row`, then call it from `cmd_pull()` and `_daily_pull_and_project()`. Add `hai daily --source csv` tests proving canonical/no-demo/no-allow exits `USER_INPUT` with zero sync rows, plus positive tests for demo, explicit allow, and explicit non-canonical DB. Also revisit the source finding's symmetry rule for commands that accept both `--db-path` and `--base-dir`; daily is still an asymmetric override surface.

### F-IR-03. W-A partial-day cutoff is not configurable through thresholds

**Q-bucket:** Q-IR-W-A.c
**Severity:** scope-mismatch
**Reference:** `reporting/plans/v0_1_15/PLAN.md:131`; `src/health_agent_infra/core/intake/presence.py:50-54`; `src/health_agent_infra/cli.py:4114-4116`

**Argument:** PLAN §2.B says `is_partial_day` uses a cutoff "configurable via thresholds; default 18:00 user-local." The implementation hard-codes `DEFAULT_CUTOFF_HOUR = 18` and `DEFAULT_EXPECTED_MEALS = 3`, and its own comment defers thresholds wiring to a future cycle. `cmd_intake_gaps()` calls `compute_presence_block()` without loading thresholds, and `DEFAULT_THRESHOLDS` has no W-A keys. This is a direct implementation-vs-PLAN drift on a behavior that W-D arm-1 consumes.

**Recommended response:** Add threshold keys for the W-A cutoff and expected-meal count, scaffold them into `thresholds.toml`, load/coerce them at `hai intake gaps` and snapshot call sites, and add tests proving a user override changes `is_partial_day`. If the maintainer intentionally wants constants for v0.1.15, revise the PLAN/REPORT wording explicitly; as written, code should be fixed.

### F-IR-04. W-C migration preservation is claimed but not tested

**Q-bucket:** Q-IR-W-C.b
**Severity:** acceptance-weak
**Reference:** `src/health_agent_infra/core/state/migrations/025_target_macros_extension.sql:18-19`; `verification/tests/test_w_c_target_nutrition.py:55-98`; `reporting/plans/v0_1_15/PLAN.md:192`

**Argument:** Migration 025's SQL uses the correct recreate-and-copy shape and appears to preserve rows byte-stable. The shipped test, however, only verifies that the new SQL CHECK admits `carbs_g` / `fat_g` and that `_VALID_TARGET_TYPE` includes them. PLAN acceptance also required existing target rows to survive byte-stable, the maintainer's live nutrition rows being the motivating case, and index rebuild/query-plan stability. That part is currently asserted by prose, not tests.

**Recommended response:** Add a migration test that seeds pre-025 target rows covering active and archived nutrition targets, applies migration 025, and asserts every shared column is identical after migration. Also assert the three indexes exist, and either check `EXPLAIN QUERY PLAN` for the W-A active-window query or explicitly document why index-presence is sufficient.

### F-IR-05. W-C migration renumbering still has stale `024` prose

**Q-bucket:** Q-IR-W-C.c / Q-IR-X.e
**Severity:** provenance-gap
**Reference:** `reporting/plans/v0_1_15/PLAN.md:149`, `reporting/plans/v0_1_15/PLAN.md:184`, `reporting/plans/v0_1_15/PLAN.md:192`, `reporting/plans/v0_1_15/PLAN.md:370`, `reporting/plans/tactical_plan_v0_1_x.md:605`

**Argument:** The implementation correctly lands W-C as migration 025 because W-GYM-SETID claimed 024 first. Several docs still describe the W-C target CHECK extension as "migration 024" despite adjacent lines naming 025. This is exactly the renumbering drift Q-IR-4.c / Q-IR-X.e asked to verify.

**Recommended response:** Replace these W-C-specific `024` references with `025`, preserving the note that the round-4 draft originally said 024. The tactical §5B W-C row should also say migration 025.

### F-IR-06. W-D adds `insufficient_data` without updating the nutrition contract docs

**Q-bucket:** Q-IR-W-D arm-1.b
**Severity:** provenance-gap
**Reference:** `src/health_agent_infra/domains/nutrition/classify.py:35-39`, `src/health_agent_infra/domains/nutrition/classify.py:70`, `src/health_agent_infra/domains/nutrition/classify.py:330`, `src/health_agent_infra/skills/nutrition-alignment/SKILL.md:22-48`

**Argument:** The runtime suppression path returns `nutrition_status="insufficient_data"`, and the tests cover that. The module-level status enum prose and `NutritionStatus` alias still list only `aligned / deficit_caloric / protein_gap / under_hydrated / surplus / unknown`. The nutrition-alignment skill also says `signals` contains only `today_row` and `goal_domain`, even though snapshot now passes `is_partial_day` and `target_status`, and its status matrix does not name `insufficient_data`. The skill still has a viable forced-action path because `coverage_band="insufficient"` triggers `defer_decision_insufficient_signal`, so this is not a runtime blocker, but the audit-visible contract is stale.

**Recommended response:** Add `insufficient_data` to the classifier docstring/type alias, update nutrition-alignment's snapshot signal list, and add a short note that `insufficient_data` is handled via the policy forced-action path rather than the normal status action matrix.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-GYM-SETID | PASS | Prospective set IDs include the exercise slug; migration 024 preserves custom IDs and rewrites supersession references; backup round-trip covers post-migration row survival. |
| F-PV14-01 | FIX | `hai pull` is guarded, but `hai daily` bypasses the CSV/canonical default-deny path. |
| W-A | FIX | Output shape and target-status semantics are correct, but Bandit gate fails and threshold configurability is not implemented. |
| W-C | NOTES | Core command shape is faithful: atomic helper, W57 pairing, idempotency, parser choices, and migration 025 exist. Preservation tests and docs need tightening. |
| W-D arm-1 | NOTES | Snapshot wiring outside `domains/nutrition/` is acceptable because it is required for production suppression. Contract docs need the new status/signal shape. |
| W-E | PASS | Skill operationalizes recap-first vs forward-march over the four in-scope domains and explicitly excludes `present.weigh_in.logged`; standalone morning-ritual deferral is documented. |

## Open questions for maintainer

None. The findings are triageable fixes rather than design forks.

## Closure recommendation

Hold Phase 3 until at least F-IR-01 and F-IR-02 are fixed and the gates are rerun. F-IR-03 is also a PLAN contract mismatch and should be fixed before the foreign-user session unless the maintainer explicitly revises the v0.1.15 contract to make the cutoff constant-only. F-IR-04 through F-IR-06 are close-in-place documentation/test hardening items that can land with the same fix batch; no source revert is indicated.
