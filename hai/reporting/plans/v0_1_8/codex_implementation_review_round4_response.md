# Codex Implementation Review - Round 4 - v0.1.8

## Step 0 confirmation

- `pwd`: `/Users/domcolligan/health_agent_infra`
- `git branch --show-current`: `v0.1.4-release`
- `git status --short`: 55 modified/new paths before this report was written, matching the claimed round-4 tree.
- `hai --version`: `hai 0.1.8`
- `python3 -m pytest safety/tests/ -q`: `2072 passed, 4 skipped, 1 warning in 55.72s`
- `python3 scripts/check_skill_cli_drift.py`: `OK: no skill <-> CLI drift detected.`

## Executive verdict

**SHIP_WITH_NOTES.** R3-1 is resolved: the runtime resolver now rejects bool-shaped and non-numeric `policy.review_summary` threshold overrides before any `int()` / `float()` coercion, and the six new regression tests pass. I found no must-fix issue and no W57 regression. The only new items are v0.1.9 backlog notes, not blockers; v0.1.8 is cleared to tag and publish.

## R3-1 re-audit

**Status: RESOLVED.**

Check A - fix addresses violation:
- `ReviewSummaryThresholdError` exists as a typed runtime config error with guidance for skipped validation (`src/health_agent_infra/core/review/summary.py:62`, `src/health_agent_infra/core/review/summary.py:65`).
- `_coerce_int` handles missing values via default, rejects bool before the numeric check, rejects non-numeric types, and names `hai config validate` in both error paths (`src/health_agent_infra/core/review/summary.py:77`, `src/health_agent_infra/core/review/summary.py:78`, `src/health_agent_infra/core/review/summary.py:80`, `src/health_agent_infra/core/review/summary.py:83`, `src/health_agent_infra/core/review/summary.py:86`, `src/health_agent_infra/core/review/summary.py:89`).
- `_coerce_float` mirrors the same bool-before-number guard and diagnostic (`src/health_agent_infra/core/review/summary.py:95`, `src/health_agent_infra/core/review/summary.py:96`, `src/health_agent_infra/core/review/summary.py:98`, `src/health_agent_infra/core/review/summary.py:101`, `src/health_agent_infra/core/review/summary.py:104`, `src/health_agent_infra/core/review/summary.py:107`).
- `_resolve_thresholds` now routes every `policy.review_summary` numeric leaf through those helpers (`src/health_agent_infra/core/review/summary.py:126`, `src/health_agent_infra/core/review/summary.py:130`, `src/health_agent_infra/core/review/summary.py:133`, `src/health_agent_infra/core/review/summary.py:137`, `src/health_agent_infra/core/review/summary.py:141`, `src/health_agent_infra/core/review/summary.py:145`, `src/health_agent_infra/core/review/summary.py:149`).
- `build_review_summary` uses `_resolve_thresholds` before applying review-summary policy (`src/health_agent_infra/core/review/summary.py:434`).

Check B - regression coverage:
- The six claimed tests exist: bool `window_days`, bool threshold, bool mixed bound, non-numeric string, real-number acceptance, and missing-key defaults (`safety/tests/test_review_summary.py:488`, `safety/tests/test_review_summary.py:508`, `safety/tests/test_review_summary.py:523`, `safety/tests/test_review_summary.py:538`, `safety/tests/test_review_summary.py:553`, `safety/tests/test_review_summary.py:577`).
- The primary bool test asserts the error message includes the key, `bool`, and `hai config validate` (`safety/tests/test_review_summary.py:500`, `safety/tests/test_review_summary.py:503`, `safety/tests/test_review_summary.py:505`).
- `python3 -m pytest safety/tests/test_review_summary.py -q`: `19 passed`.
- These would fail against round 3 because `_resolve_thresholds` used bare `int()` / `float()` and returned `1`, `0`, or `1.0` for bool values.

Check C - new failure mode:
- Legitimate zero/one numeric values still resolve correctly via `_coerce_int` / `_coerce_float`; the bool guard is type-specific, not value-specific (`src/health_agent_infra/core/review/summary.py:80`, `src/health_agent_infra/core/review/summary.py:92`, `src/health_agent_infra/core/review/summary.py:98`, `src/health_agent_infra/core/review/summary.py:110`).
- Missing keys fall back to documented defaults rather than raising (`src/health_agent_infra/core/review/summary.py:78`, `src/health_agent_infra/core/review/summary.py:96`, `safety/tests/test_review_summary.py:582`).
- The exception is accessible as a module-level public class and is directly imported by tests/callers that need to catch it (`src/health_agent_infra/core/review/summary.py:62`, `safety/tests/test_review_summary.py:494`).
- No other source path reads `policy.review_summary` thresholds independently of `_resolve_thresholds`; the remaining references are validator checks, comments, tests, and uses of the resolved summary values (`src/health_agent_infra/cli.py:3850`, `src/health_agent_infra/core/review/summary.py:278`, `src/health_agent_infra/core/review/summary.py:292`).

## New issues found in round 4

1. **should-fix -> v0.1.9 backlog - runtime type hardening is still per-surface, not global for all `DEFAULT_THRESHOLDS`.** `load_thresholds` still deep-merges user TOML leaves without type validation (`src/health_agent_infra/core/config.py:486`, `src/health_agent_infra/core/config.py:510`). Outside `policy.review_summary`, several runtime paths still cast or compare threshold leaves directly, e.g. nutrition band thresholds via `float(cfg[...])` (`src/health_agent_infra/domains/nutrition/classify.py:99`, `src/health_agent_infra/domains/nutrition/classify.py:100`) and synthesis policy thresholds via bare `float()` / `int()` (`src/health_agent_infra/core/synthesis_policy.py:668`, `src/health_agent_infra/core/synthesis_policy.py:872`). This is not a v0.1.8 blocker because `hai config validate` catches bools by type when users run it, and the round-4 fix only claimed the `policy.review_summary` runtime boundary. Proposed v0.1.9 fix: centralize typed threshold access or validate merged `DEFAULT_THRESHOLDS` leaves at `load_thresholds` time.
2. **nit -> v0.1.9 backlog - pre-existing pytest unraisable warning persists.** The suite still emits `PytestUnraisableExceptionWarning` from `safety/tests/test_snapshot_bundle.py::test_snapshot_v1_0_recovery_block_has_three_keys`; it does not affect pass/fail and is unrelated to R3-1. Clean up test isolation in v0.1.9.

## Prior findings reconsidered

None. R3-1 was real and the round-4 fix addresses it.

## What's clean

- PLAN, changelog, release proof, and maintainer response all describe the same R3-1 fix and +6 tests (`reporting/plans/v0_1_8/PLAN.md:754`, `CHANGELOG.md:260`, `reporting/plans/v0_1_8/RELEASE_PROOF.md:40`, `reporting/plans/v0_1_8/codex_implementation_review_response_round4.md:31`).
- Source-built JSON capability manifest includes `hai intent commit` and `hai target commit` with `agent_safe=false`; parser annotations set that bit, and the manifest walker serializes `_contract_agent_safe` into `agent_safe` (`src/health_agent_infra/cli.py:6777`, `src/health_agent_infra/cli.py:6783`, `src/health_agent_infra/cli.py:6908`, `src/health_agent_infra/cli.py:6914`, `src/health_agent_infra/core/capabilities/walker.py:291`, `src/health_agent_infra/core/capabilities/walker.py:298`).
- W57 supersede/commit status mutation paths remain constrained to commit-time parent deactivation or user-authored supersede; grep found no new third-party status updater for intent/target (`src/health_agent_infra/core/intent/store.py:338`, `src/health_agent_infra/core/intent/store.py:405`, `src/health_agent_infra/core/target/store.py:309`, `src/health_agent_infra/core/target/store.py:363`).
- Full safety suite and skill/CLI drift validator are green at the claimed counts.

## Final verdict + ship instruction

**SHIP_WITH_NOTES: ship now.** No must-fix blocker remains for v0.1.8. Defer the global threshold-runtime hardening and the pytest warning cleanup to v0.1.9 backlog; neither justifies an extraordinary round-5 audit.
