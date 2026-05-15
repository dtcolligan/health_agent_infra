# Codex Implementation Review - Round 2 - v0.1.8

## Step 0 confirmation

- `pwd`: `/Users/domcolligan/health_agent_infra`
- `git branch --show-current`: `v0.1.4-release`
- `git status --short`: 51 modified/new paths, matching the claimed round-2 tree.
- `hai --version`: `hai 0.1.8`
- `python3 -m pytest safety/tests/ -q`: `2058 passed, 4 skipped in 59.70s`
- `python3 scripts/check_skill_cli_drift.py`: `OK: no skill <-> CLI drift detected.`

## Executive verdict

**SHIP_WITH_FIXES.** The two round-1 blockers are closed at the original agent-facing surfaces: `hai stats --data-quality` no longer writes, and agent-safe intent/target inserts can no longer land agent-proposed rows as active. The round-1 P2/P3 fixes are also present and tested. I found three residual issues introduced or exposed by the fixes: data-quality projection errors are silently swallowed in `hai clean`, agent-proposed supersede helpers can deactivate the old active row before user commit, and config validation still accepts TOML booleans as numbers. None reopens the exact round-1 CLI bypass, but they should be fixed before calling the implementation fully clean.

## Per-finding re-audit

### P1-1 - `hai stats --data-quality` no longer writes state

**Status: NEW_ISSUE_FROM_FIX.**

Check A - original violation addressed:
- `_emit_data_quality_stats` now opens the DB and calls only `read_data_quality_rows`; no projector call remains in the stats path (`src/health_agent_infra/cli.py:5626`, `src/health_agent_infra/cli.py:5650`, `src/health_agent_infra/cli.py:5658`).
- `hai clean` now invokes `project_data_quality_for_date(..., commit_after=False)` in the write path (`src/health_agent_infra/cli.py:771`, `src/health_agent_infra/cli.py:783`).
- The projector supports outer transactions via `commit_after` (`src/health_agent_infra/core/data_quality/projector.py:62`, `src/health_agent_infra/core/data_quality/projector.py:127`).
- Capability contract still marks `hai stats` read-only (`reporting/docs/agent_cli_contract.md:107`).

Check B - regression coverage:
- `test_cli_data_quality_is_read_only_on_fresh_db` asserts stats returns empty rows and leaves `data_quality_daily` at count 0 (`safety/tests/test_data_quality_ledger.py:122`, `safety/tests/test_data_quality_ledger.py:144`).
- `test_cli_data_quality_returns_rows_after_projection` verifies stats reads rows after projection (`safety/tests/test_data_quality_ledger.py:158`, `safety/tests/test_data_quality_ledger.py:174`).

Check C - residual from fix:
- **should-fix:** `hai clean` catches all exceptions from snapshot/data-quality projection and silently `pass`es, then commits the transaction (`src/health_agent_infra/cli.py:771`, `src/health_agent_infra/cli.py:786`, `src/health_agent_infra/cli.py:792`). Since stats is now purely read-only, a projector/schema regression can make the data-quality ledger silently empty. Suggested remediation: either let the exception hit the outer rollback/warning path, or emit a stderr warning and record projection failure explicitly.
- **nit:** `_emit_data_quality_stats` docstring still says empty windows are built on-the-fly from the snapshot, which is now false (`src/health_agent_infra/cli.py:5636`, `src/health_agent_infra/cli.py:5650`).

### P1-2 - agent-proposed intent/target rows cannot land as active

**Status: NEW_ISSUE_FROM_FIX.**

Check A - original violation addressed:
- Intent validator rejects `source != "user_authored"` with `status == "active"` on insert (`src/health_agent_infra/core/intent/store.py:172`, `src/health_agent_infra/core/intent/store.py:177`).
- Target validator has the same store-level guard (`src/health_agent_infra/core/target/store.py:160`, `src/health_agent_infra/core/target/store.py:163`).
- CLI add paths surface validation failures as `USER_INPUT` (`src/health_agent_infra/cli.py:2101`, `src/health_agent_infra/cli.py:2317`).
- New commit commands are annotated `agent_safe=False` (`src/health_agent_infra/cli.py:6744`, `src/health_agent_infra/cli.py:6750`, `src/health_agent_infra/cli.py:6875`, `src/health_agent_infra/cli.py:6881`), and the contract renders them as not agent-safe (`reporting/docs/agent_cli_contract.md:85`, `reporting/docs/agent_cli_contract.md:110`).

Check B - regression coverage:
- Intent tests cover store rejection, allowed shapes, commit promotion, idempotent active no-op, CLI rejection, and CLI commit (`safety/tests/test_intent_ledger.py:381`, `safety/tests/test_intent_ledger.py:404`, `safety/tests/test_intent_ledger.py:424`, `safety/tests/test_intent_ledger.py:445`, `safety/tests/test_intent_ledger.py:474`, `safety/tests/test_intent_ledger.py:495`, `safety/tests/test_intent_ledger.py:514`).
- Target tests cover store rejection, commit promotion, CLI rejection, and CLI commit (`safety/tests/test_target_ledger.py:390`, `safety/tests/test_target_ledger.py:411`, `safety/tests/test_target_ledger.py:438`, `safety/tests/test_target_ledger.py:458`).

Check C - residual from fix:
- **should-fix:** `supersede_intent` / `supersede_target` can still insert an `agent_proposed` replacement with `status="proposed"` and immediately mark the old active row `superseded`, before user commit. The validators reject only active non-user-authored inserts (`src/health_agent_infra/core/intent/store.py:177`, `src/health_agent_infra/core/target/store.py:163`); supersede then updates the old row immediately (`src/health_agent_infra/core/intent/store.py:353`, `src/health_agent_infra/core/intent/store.py:362`, `src/health_agent_infra/core/target/store.py:318`, `src/health_agent_infra/core/target/store.py:327`). `commit_intent` / `commit_target` only flips the new row from proposed to active and does not own the old-row supersede transition (`src/health_agent_infra/core/intent/store.py:313`, `src/health_agent_infra/core/target/store.py:288`). Suggested remediation: reject non-user-authored proposed replacements in `supersede_*`, or defer the old-row supersede update into `commit_*` when `supersedes_*_id` is present.

### P2-1 - `--auto --explain` snapshot block carries W48 signals

**Status: RESOLVED.**

Check A:
- Snapshot stage now populates `domains_present`, `missingness_per_domain`, `classified_bands_per_domain`, and `review_summary_tokens_per_domain` from the built snapshot (`src/health_agent_infra/cli.py:4409`, `src/health_agent_infra/cli.py:4418`, `src/health_agent_infra/cli.py:4421`, `src/health_agent_infra/cli.py:4425`, `src/health_agent_infra/cli.py:4435`, `src/health_agent_infra/cli.py:4440`).
- Explain block now surfaces those fields (`src/health_agent_infra/cli.py:5264`, `src/health_agent_infra/cli.py:5266`, `src/health_agent_infra/cli.py:5268`, `src/health_agent_infra/cli.py:5271`).

Check B:
- `test_auto_explain_snapshot_block_carries_w48_signals` asserts non-null `domains_present`, dict-shaped missingness/bands/tokens, and a real recovery insufficient-denominator token on empty DB (`safety/tests/test_cli_daily_auto_explain.py:77`, `safety/tests/test_cli_daily_auto_explain.py:98`, `safety/tests/test_cli_daily_auto_explain.py:104`, `safety/tests/test_cli_daily_auto_explain.py:112`).

Check C:
- No new failure found. Missing `classified_state` degrades to an empty per-domain bands dict rather than raising (`src/health_agent_infra/cli.py:4429`, `src/health_agent_infra/cli.py:4431`).

### P2-2 - live capture dispatches on scenario domain

**Status: RESOLVED.**

Check A:
- `_LIVE_SKILL_BY_DOMAIN` maps recovery/running to their own skills and unknown domains raise (`safety/evals/skill_harness/runner.py:61`, `safety/evals/skill_harness/runner.py:70`).
- `invoke_live` reads `scenario["domain"]`, resolves the skill, and uses that skill in the prompt (`safety/evals/skill_harness/runner.py:327`, `safety/evals/skill_harness/runner.py:336`, `safety/evals/skill_harness/runner.py:337`, `safety/evals/skill_harness/runner.py:350`).

Check B:
- Tests pin recovery/running dispatch and unknown-domain refusal without launching live mode (`safety/tests/test_skill_harness.py:105`, `safety/tests/test_skill_harness.py:110`, `safety/tests/test_skill_harness.py:114`).

Check C:
- No new failure found; live invocation remains env-gated before subprocess work (`safety/evals/skill_harness/runner.py:327`).

### P2-3 - `hai config validate` enforces numeric ranges

**Status: NEW_ISSUE_FROM_FIX.**

Check A:
- `_review_summary_range_issues` checks `window_days >= 1`, non-negative denominator/thresholds, mixed bounds in `[0, 1]`, and `lower <= upper` (`src/health_agent_infra/cli.py:3837`, `src/health_agent_infra/cli.py:3861`, `src/health_agent_infra/cli.py:3868`, `src/health_agent_infra/cli.py:3875`, `src/health_agent_infra/cli.py:3883`, `src/health_agent_infra/cli.py:3894`).
- `cmd_config_validate` appends range issues and treats `range_violation` as blocking (`src/health_agent_infra/cli.py:3989`, `src/health_agent_infra/cli.py:3991`).

Check B:
- Four tests cover the original negative/inverted/out-of-unit cases (`safety/tests/test_cli_config_validate_diff.py:89`, `safety/tests/test_cli_config_validate_diff.py:104`, `safety/tests/test_cli_config_validate_diff.py:119`, `safety/tests/test_cli_config_validate_diff.py:136`).

Check C - residual from fix:
- **should-fix:** booleans still pass as numeric values because both the type checker and range helper use `isinstance(value, (int, float))`; in Python, `bool` is a subclass of `int` (`src/health_agent_infra/cli.py:3964`, `src/health_agent_infra/cli.py:3863`, `src/health_agent_infra/cli.py:3889`). A TOML override like `window_days = true` can avoid `type_mismatch` and range checks. Suggested remediation: use a local `is_number = isinstance(v, (int, float)) and not isinstance(v, bool)` helper, and add boolean-as-number regression tests.

### P3-1 - snapshot v2 transition documented

**Status: RESOLVED.**

Check A:
- `agent_integration.md` now has "Snapshot schema v2 (v0.1.8 transition note)" between "What an agent should NOT do" and "MCP" (`reporting/docs/agent_integration.md:166`, `reporting/docs/agent_integration.md:181`, `reporting/docs/agent_integration.md:218`).
- The section names the additive guarantee and pin/ignore guidance (`reporting/docs/agent_integration.md:183`, `reporting/docs/agent_integration.md:185`, `reporting/docs/agent_integration.md:187`).
- It lists the four additive fields (`reporting/docs/agent_integration.md:192`, `reporting/docs/agent_integration.md:200`, `reporting/docs/agent_integration.md:205`, `reporting/docs/agent_integration.md:209`).
- `build_snapshot` and RELEASE_PROOF now point at a real documented transition (`src/health_agent_infra/core/state/snapshot.py:938`, `src/health_agent_infra/core/state/snapshot.py:943`, `reporting/plans/v0_1_8/RELEASE_PROOF.md:74`, `reporting/plans/v0_1_8/RELEASE_PROOF.md:77`).

Check B:
- Doc-only fix; no runtime regression expected. The committed contract doc still passes in the full suite.

Check C:
- No new failure found.

## New issues found in round 2

1. **should-fix - data-quality projection failures are silent in `hai clean`.** Evidence and remediation under P1-1 Check C.
2. **should-fix - agent-proposed supersede helpers can deactivate old active rows before commit.** Evidence and remediation under P1-2 Check C.
3. **should-fix - config validator accepts booleans as numeric threshold values.** Evidence and remediation under P2-3 Check C.
4. **nit - stale data-quality stats docstring.** Evidence and remediation under P1-1 Check C.

## What's clean

- Full safety suite is green at the claimed count: `2058 passed, 4 skipped`.
- Drift validator is green.
- Original stats read-only violation would be caught by the new fresh-DB SQL row-count test.
- Original agent-proposed-active CLI bypass would be caught for both intent and target.
- `agent_safe=False` serializes correctly from source when running the local tree (`hai intent commit` / `hai target commit` render as "no" in `agent_cli_contract.md`).
- `--auto --explain`, skill live dispatch, and snapshot v2 docs now match the round-1 requested shape.

## Final verdict criteria

No round-1 must-fix remains open at the original CLI boundary. To move from **SHIP_WITH_FIXES** to **SHIP**, fix or consciously defer the three should-fix residuals above, especially the supersede/commit transition if agent-proposed replacements are meant to be supported in v0.1.8.
