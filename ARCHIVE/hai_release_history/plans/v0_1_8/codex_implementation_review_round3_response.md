# Codex Implementation Review - Round 3 - v0.1.8

## Step 0 confirmation

- `pwd`: `/Users/domcolligan/health_agent_infra`
- `git branch --show-current`: `v0.1.4-release`
- `git status --short`: 53 modified/new paths before this report was written, matching the claimed round-3 tree.
- `hai --version`: `hai 0.1.8`
- `python3 -m pytest safety/tests/ -q`: `2066 passed, 4 skipped, 1 warning in 54.48s`
- `python3 scripts/check_skill_cli_drift.py`: `OK: no skill <-> CLI drift detected.`

## Executive verdict

**SHIP_WITH_FIXES.** The four round-2 residual fixes are present and the claimed regression tests pass. R2-1, R2-2, R2-3's validator surface, and R2-4 are resolved at the cited boundaries. I found one late issue in the same R2-3 bool-as-number area: runtime review-summary threshold resolution still casts bools through `int()` / `float()` if invalid TOML is loaded without running `hai config validate` first. No must-fix issue was found in the round-3 patches themselves.

## Per-finding re-audit

### R2-1 - `hai clean` no longer silently swallows data-quality projection failures

**Status: RESOLVED.**

Check A - fix addresses violation:
- The previous bare `except: pass` is now a stderr warning that includes `as_of_date`, `user_id`, exception class/message, and the `hai stats --data-quality` consequence (`src/health_agent_infra/cli.py:786`, `src/health_agent_infra/cli.py:794`, `src/health_agent_infra/cli.py:797`, `src/health_agent_infra/cli.py:799`, `src/health_agent_infra/cli.py:802`).
- Accepted-state writes still commit after a data-quality projection failure; the warning catch falls through to `conn.commit()` (`src/health_agent_infra/cli.py:783`, `src/health_agent_infra/cli.py:786`, `src/health_agent_infra/cli.py:804`).
- The broader accepted-state projection failure path still rolls back and warns separately (`src/health_agent_infra/cli.py:805`, `src/health_agent_infra/cli.py:810`).

Check B - regression coverage:
- No regression test was claimed for R2-1. I am not treating that as a blocker: this was a fail-soft visibility fix, the warning is directly on `stderr`, and stdout remains the existing JSON emit after projection (`src/health_agent_infra/cli.py:628`).

Check C - new failure mode:
- No new failure found. Warning output is on `stderr`; stdout-parseable `hai clean` output is unchanged (`src/health_agent_infra/cli.py:628`, `src/health_agent_infra/cli.py:802`).

### R2-2 - agent-proposed supersede defers deactivation to user commit

**Status: RESOLVED.**

Check A - fix addresses violation:
- `supersede_intent` now inserts the replacement with `supersedes_intent_id` but only flips the old row immediately for `source == "user_authored"` (`src/health_agent_infra/core/intent/store.py:396`, `src/health_agent_infra/core/intent/store.py:405`, `src/health_agent_infra/core/intent/store.py:412`).
- `commit_intent` reads `supersedes_intent_id`, promotes the proposed row, and updates the parent to `superseded` before the same `conn.commit()` (`src/health_agent_infra/core/intent/store.py:323`, `src/health_agent_infra/core/intent/store.py:333`, `src/health_agent_infra/core/intent/store.py:338`, `src/health_agent_infra/core/intent/store.py:348`).
- `supersede_target` and `commit_target` mirror the same shape (`src/health_agent_infra/core/target/store.py:354`, `src/health_agent_infra/core/target/store.py:363`, `src/health_agent_infra/core/target/store.py:294`, `src/health_agent_infra/core/target/store.py:304`, `src/health_agent_infra/core/target/store.py:309`, `src/health_agent_infra/core/target/store.py:316`).
- CLI commit commands remain not agent-safe in the parser and rendered contract (`src/health_agent_infra/cli.py:6783`, `src/health_agent_infra/cli.py:6914`, `reporting/docs/agent_cli_contract.md:85`, `reporting/docs/agent_cli_contract.md:110`).

Check B - regression coverage:
- Intent tests pin agent-proposed supersede leaves the old row active, commit-time parent deactivation, and user-authored immediate deactivation (`safety/tests/test_intent_ledger.py:540`, `safety/tests/test_intent_ledger.py:587`, `safety/tests/test_intent_ledger.py:597`, `safety/tests/test_intent_ledger.py:647`, `safety/tests/test_intent_ledger.py:656`, `safety/tests/test_intent_ledger.py:699`).
- Target tests pin agent-proposed supersede deferral and commit-time parent deactivation (`safety/tests/test_target_ledger.py:488`, `safety/tests/test_target_ledger.py:534`, `safety/tests/test_target_ledger.py:543`, `safety/tests/test_target_ledger.py:584`).
- These tests would have failed against round 2 because `supersede_*` immediately marked the parent `superseded`, and `commit_*` did not own the parent transition.

Check C - new failure mode:
- No new failure found in the audited path. Project connections use SQLite's default deferred isolation, not autocommit (`src/health_agent_infra/core/state/store.py:44`, `src/health_agent_infra/core/state/store.py:48`, `src/health_agent_infra/core/state/store.py:53`), so the two DML updates in `commit_*` share the same commit boundary on the CLI/store path.
- No extra code path to set intent/target `status='superseded'` surfaced outside `commit_*` and user-authored `supersede_*` (`src/health_agent_infra/core/intent/store.py:343`, `src/health_agent_infra/core/intent/store.py:407`, `src/health_agent_infra/core/target/store.py:311`, `src/health_agent_infra/core/target/store.py:365`).

### R2-3 - `hai config validate` rejects booleans as numeric thresholds

**Status: RESOLVED for the validator surface; see late issue R3-1 below.**

Check A - fix addresses violation:
- The validator numeric type branch now rejects bool values even though bool subclasses int (`src/health_agent_infra/cli.py:3987`, `src/health_agent_infra/cli.py:3991`, `src/health_agent_infra/cli.py:3992`).
- `_review_summary_range_issues` now uses `_is_real_number`, which excludes bools, for every range comparison (`src/health_agent_infra/cli.py:3877`, `src/health_agent_infra/cli.py:3882`, `src/health_agent_infra/cli.py:3889`, `src/health_agent_infra/cli.py:3897`, `src/health_agent_infra/cli.py:3908`, `src/health_agent_infra/cli.py:3914`).
- `type_mismatch` remains blocking (`src/health_agent_infra/cli.py:4021`, `src/health_agent_infra/cli.py:4023`).

Check B - regression coverage:
- The three claimed bool-as-number tests exist and assert `type_mismatch` for `window_days`, a threshold, and a mixed bound (`safety/tests/test_cli_config_validate_diff.py:136`, `safety/tests/test_cli_config_validate_diff.py:151`, `safety/tests/test_cli_config_validate_diff.py:157`, `safety/tests/test_cli_config_validate_diff.py:168`, `safety/tests/test_cli_config_validate_diff.py:174`, `safety/tests/test_cli_config_validate_diff.py:183`).
- These tests would have failed against round 2 because bools passed both the numeric type branch and range helper.

Check C - new failure mode:
- No new validator failure found. However, see R3-1: the runtime threshold resolver still accepts the same bool-as-number shape if invalid config is loaded without first running `hai config validate`.

### R2-4 - `_emit_data_quality_stats` docstring updated

**Status: RESOLVED.**

Check A - fix addresses violation:
- The docstring now states the read-only contract, says it reads only from `data_quality_daily`, never invokes the projector, returns empty rows honestly, and cites the Codex round-1 P1-1 plus round-2 R2-4 chain (`src/health_agent_infra/cli.py:5664`, `src/health_agent_infra/cli.py:5666`, `src/health_agent_infra/cli.py:5668`, `src/health_agent_infra/cli.py:5670`, `src/health_agent_infra/cli.py:5671`).

Check B - regression coverage:
- Doc-only fix; no regression test expected.

Check C - new failure mode:
- No new failure found.

## New issues found in round 3

1. **should-fix - NEW_ISSUE_DISCOVERED_LATE - review-summary runtime still accepts bools as numeric thresholds when validate is skipped.** `load_thresholds` deep-merges TOML leaves without type validation (`src/health_agent_infra/core/config.py:486`, `src/health_agent_infra/core/config.py:502`, `src/health_agent_infra/core/config.py:510`). `_resolve_thresholds` then casts `policy.review_summary` values through `int()` / `float()`, so `window_days = true` becomes `1`, `recent_negative_threshold = false` becomes `0`, and `mixed_token_upper_bound = true` becomes `1.0` (`src/health_agent_infra/core/review/summary.py:72`, `src/health_agent_infra/core/review/summary.py:73`, `src/health_agent_infra/core/review/summary.py:75`, `src/health_agent_infra/core/review/summary.py:81`). `build_review_summary` applies those values in snapshots/stats without rechecking bools (`src/health_agent_infra/core/review/summary.py:368`, `src/health_agent_infra/core/review/summary.py:370`, `src/health_agent_infra/core/state/snapshot.py:869`). Suggested fix: share the strict numeric predicate with runtime threshold resolution, or make `load_thresholds` reject bools for numeric `policy.review_summary` leaves.

## What's clean

- Round-3 documentation is consistent across maintainer response, PLAN implementation log, and changelog (`reporting/plans/v0_1_8/codex_implementation_review_response_round3.md:24`, `reporting/plans/v0_1_8/PLAN.md:752`, `CHANGELOG.md:230`).
- Full suite and drift validator are green at the claimed round-3 counts.
- `hai clean` warning is visible on stderr and does not pollute stdout JSON (`src/health_agent_infra/cli.py:628`, `src/health_agent_infra/cli.py:802`).
- W57 supersede lifecycle is closed for the audited `superseded` path: insert validators reject agent-proposed-active rows, agent-proposed supersede leaves the parent active, and user commit performs the parent transition (`src/health_agent_infra/core/intent/store.py:177`, `src/health_agent_infra/core/intent/store.py:405`, `src/health_agent_infra/core/intent/store.py:338`; `src/health_agent_infra/core/target/store.py:163`, `src/health_agent_infra/core/target/store.py:363`, `src/health_agent_infra/core/target/store.py:309`).
- The config validator's own bool/range checks now use the right bool-excluding shape (`src/health_agent_infra/cli.py:3877`, `src/health_agent_infra/cli.py:3991`).

## Final verdict criteria

No must-fix blocker remains in the four round-2 residual fixes. To move from **SHIP_WITH_FIXES** to **SHIP**, fix or explicitly defer R3-1 so the bool-as-number class is either rejected at runtime or documented as guarded only by `hai config validate`.
