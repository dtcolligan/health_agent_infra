# Codex Implementation Review - v0.1.15 (Round 2)

**Verdict:** SHIP_WITH_FIXES
**Round:** 2

## Round-1 finding closure verification

| Finding | Closure | Rationale |
|---|---|---|
| F-IR-01 | CLOSED | Bandit now exits cleanly at `-ll`: 0 medium/high, 46 low unchanged. The two W-A `# nosec B608` annotations are narrow to the SQL-string lines and the constant-placeholder rationale is accurate. |
| F-IR-02 | CLOSED_WITH_RESIDUAL | The shared guard exists and is called by both `cmd_pull` and `_daily_pull_and_project`; refusal happens before adapter construction/sync-row write; `_DailyPullRefusal` is caught before live-source errors; the daily refusal report is structured and parseable. Residual: one daily positive-path test is vacuous and the daily demo-marker escape path is still unpinned. |
| F-IR-03 | CLOSED | Threshold defaults were added under `gap_detection`, `compute_presence_block()` loads/coerces them when kwargs are omitted, callers are keyword-only, and the override test proves the default cutoff can be changed. The broad fallback on load/coerce failure is acceptable for this user-config surface. |
| F-IR-04 | CLOSED_WITH_RESIDUAL | Migration 025 now has a byte-stable preservation test for the three live-shape target rows and asserts the three rebuilt index names. Residual: `EXPLAIN QUERY PLAN` remains a named deferred stronger assertion, not a blocker for this round. |
| F-IR-05 | CLOSED | Active W-C prose now says migration 025; the remaining `024` references in PLAN provenance and historical audit artifacts correctly describe the earlier round-4 draft or W-GYM-SETID migration 024. |
| F-IR-06 | CLOSED | `insufficient_data` is now documented in the nutrition classifier docstring/type alias, W-A signal keys are documented, and the nutrition-alignment skill names the unreachable matrix row with the policy-forced-action path. |

## New round-2 findings

### F-IR-R2-01. Daily CSV allow-flag test is vacuous

**Q-bucket:** Q-IR-R2.2.f
**Severity:** acceptance-weak
**Reference:** `verification/tests/test_w_pv14_01_csv_isolation.py:295`

**Argument:** `test_hai_daily_csv_with_allow_fixture_flag_passes_guard` does not actually prove that `--allow-fixture-into-real-state` steps the F-PV14 guard aside. If the guard regressed and returned the same `USER_INPUT` / `overall_status="refused"` shape as the negative test, the assertion at lines 318-319 would still pass because `_last_stdout_overall_status_is_not_refused()` always returns `True` and intentionally reads no stdout. The explicit `--db-path` positive path is pinned by sync rows, and the negative path is pinned, but the new daily allow-flag escape path is not. The active demo-marker escape path is also not directly tested for `hai daily`; that is lower risk because the helper is shared, but it is still one of the documented escape paths.

**Recommended response:** Change the allow-flag test to capture stdout with `capsys` and assert the daily payload is not the F-PV14 refusal shape, or assert that the canonical redirected DB receives a sync row. Add a small daily demo-marker positive test, or document why the shared-helper coverage is sufficient and keep the test matrix intentionally at negative / allow-flag / explicit-db.

### F-IR-R2-02. Round-1 fix notes have stale citations and non-durable deferrals

**Q-bucket:** Q-IR-R2.2.e / Q-IR-R2.7.b
**Severity:** provenance-gap
**Reference:** `reporting/plans/v0_1_15/codex_implementation_review_response_response.md:17`, `reporting/plans/v0_1_15/codex_implementation_review_response_response.md:39`, `reporting/plans/v0_1_15/codex_implementation_review_response_response.md:67`, `reporting/plans/v0_1_15/codex_implementation_review_response_response.md:132`

**Argument:** The code is in the right shape, but the audit trail is not. The response says the guard helper is at `cli.py:159-204`; current source has `_DailyPullRefusal` at `cli.py:172-184` and `_f_pv14_csv_canonical_guard` at `cli.py:187-234`. It says the precedent `# nosec B608` lines are `core/target/store.py:218` and `:359`; current nosec lines are `:223`, `:275`, and `:419`, while `:359` is not a nosec line. It says the new presence annotations are at `presence.py:154,167`; current annotations are at `presence.py:187,202`. Separately, the broader symmetric `--db-path` / `--base-dir` rule and the stronger `EXPLAIN QUERY PLAN` check are only named in this response file; they are absent from the v0.1.16/v0.1.17 planning surfaces and tactical plan rows a future cycle author is instructed to read.

**Recommended response:** Correct the line citations in `codex_implementation_review_response_response.md`. Add durable follow-up bullets for the two named deferrals: put the broader F-PV14 symmetry rule in the v0.1.16 empirical-fix intake surface or v0.1.17 carry-over list, and put the query-plan stability check next to W-C/W-A follow-up provenance or explicitly mark it as not worth carrying forward.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-GYM-SETID | PASS | Unchanged from round 1; no regression found. |
| F-PV14-01 | FIX | Runtime guard is fixed, but the daily allow/demo positive escape coverage and follow-up provenance need tightening. |
| W-A | PASS | Threshold wiring and Bandit closure verified. |
| W-C | NOTES | Migration preservation coverage is materially improved; query-plan stability remains a documented residual rather than a blocker. |
| W-D arm-1 | PASS | Enum/skill documentation is now coherent. |
| W-E | PASS | Unchanged from round 1; no regression found. |

## Closure recommendation

Round 3. The runtime gates are green and there is no new correctness/security blocker, but round 2 surfaced 2 findings. Per the round-2 prompt's closure rule, that exceeds the close-in-place threshold. The fix batch should be small: tighten the daily allow/demo tests, correct the stale citations, and place the two named deferrals on a durable planning surface. Phase 3 should remain held until round 3 returns SHIP or SHIP_WITH_NOTES.
