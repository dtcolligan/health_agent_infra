# Codex Implementation Review — v0.2.0 (round 1)

**Verdict:** SHIP_WITH_FIXES
**Round:** 1

## Verification summary

- Tree state: `/Users/domcolligan/health_agent_infra`, branch `main`. Pre-report status was clean except the existing untracked planning artifact `reporting/plans/v0_2_0/next_session_prompt_w_fact_atom.md`; this review file is the only audit artifact added by this pass.
- Test surface: `uv run pytest verification/tests -W error::Warning -q` and `uv run pytest verification/tests -W error::pytest.PytestUnraisableExceptionWarning -q` both passed at `2940 passed, 4 skipped`.
- Ship gates: `hai capabilities --json` reports 68 commands; `hai eval run --scenario-set all` and `--scenario-set factuality` pass the factuality thresholds at 100/100; `--scenario-set judge_adversarial` remains shape-only; persona matrix passed 13/13 with 0 findings and 0 crashes. `uvx mypy src/health_agent_infra` and `uvx bandit -ll -r src/health_agent_infra` failed.
- Persona matrix: `HAI_RUN_PERSONA_MATRIX=1 uv run python -m verification.dogfood.runner /tmp/v0_2_0_ir_persona_run` wrote `/tmp/v0_2_0_ir_persona_run/summary.json`; total personas 13, findings 0, crashes 0.

## Findings

### F-IR-01. W58D row-version drift lane does not work against the real accepted-state schema

**Q-bucket:** Q-W58D / Q-provenance discipline  
**Severity:** correctness-bug  
**Reference:** `src/health_agent_infra/core/eval/factuality_gate.py:268`; `src/health_agent_infra/core/state/migrations/001_initial.sql:230`; `src/health_agent_infra/core/state/snapshot.py:1467`; `verification/tests/test_factuality_gate.py:51`; `src/health_agent_infra/evals/scenarios/factuality/_seed.py:45`  
**Argument:** PLAN §2.F requires a row-version-drift lane. The gate compares `locator["row_version"]` to `row.get("row_version")`, but real accepted-state rows have `projected_at`, not `row_version`. The project-local row-version convention explicitly maps accepted-state `row_version` to `projected_at` (`snapshot.py:1467-1476`), and the real recovery schema has `projected_at` (`001_initial.sql:230-251`). The W58D tests and factuality seed mask this by creating synthetic `accepted_recovery_state_daily` tables with a non-real `row_version` column. A repro using `initialize_database()` plus a stale locator returned `GateOutcome.PASS None None` instead of `LOCATOR_ROW_VERSION_DRIFT`.  
**Recommended response:** fix-and-reland. Compare the locator row_version to the table's real version source (`projected_at` for accepted-state rows; the documented source-table equivalent where applicable) and add a real-migration regression test.

### F-IR-02. Mypy ship gate fails

**Q-bucket:** Q-ship-gates / Q-cross-cutting code quality  
**Severity:** acceptance-weak  
**Reference:** command `uvx mypy src/health_agent_infra`  
**Argument:** The requested ship gate exits non-zero with 11 errors. The errors include new-cycle surfaces: `src/health_agent_infra/evals/scenarios/factuality/_build_corpus.py:221`, `src/health_agent_infra/evals/scenarios/atomic_claims/_build_corpus.py:203-205`, and `src/health_agent_infra/cli/handlers/review.py:387,426,428`. There are also errors in `core/synthesis.py:1255,1257` and `core/explain/queries.py:456`. This contradicts RELEASE_PROOF's clean ship-gate posture.  
**Recommended response:** fix-and-reland with `uvx mypy src/health_agent_infra` clean before version bump.

### F-IR-03. Bandit ship gate fails

**Q-bucket:** Q-ship-gates / Q-cross-cutting code quality  
**Severity:** security  
**Reference:** `src/health_agent_infra/core/eval/factuality_gate.py:383`; `src/health_agent_infra/core/state/snapshot.py:1499`; command `uvx bandit -ll -r src/health_agent_infra`  
**Argument:** Bandit exits non-zero with two B608 findings. The W58D audit-ref query has the `# nosec B608` comment on the preceding line, but Bandit reports the f-string line anyway (`factuality_gate.py:382-383`). The accepted-state versions query has the same pattern (`snapshot.py:1498-1503`). Bandit reports `0` skipped lines, so the intended suppressions are not taking effect. The whitelist mitigates actual injection risk, but the release-blocking gate still fails.  
**Recommended response:** fix-and-reland. Either refactor the dynamic SQL or place effective Bandit suppressions on the reported lines, with the whitelist rationale preserved.

### F-IR-04. Ship-time freshness checklist overclaims README and planning-index updates

**Q-bucket:** Q-summary-surface sweep / Q-provenance discipline  
**Severity:** provenance-gap  
**Reference:** `reporting/plans/v0_2_0/RELEASE_PROOF.md:153`; `README.md:20`; `reporting/plans/README.md:3`; `reporting/docs/current_system_state.md:136`  
**Argument:** RELEASE_PROOF §7 checks off README, `current_system_state.md`, and `reporting/plans/README.md`. The repo does not match that claim. `README.md` still advertises `2733_passing`, status `0.1.18`, a 67-command CLI, and v0.2.0 as next-active. `reporting/plans/README.md` still says v0.2.0 is next-active and its tree listing omits `v0_2_0/`. `current_system_state.md` has an updated top table, but its "Next cycles" table still lists v0.2.0 as next-active. ROADMAP, AUDIT, tactical plan, current-state top table, and CHANGELOG were updated; these three stale surfaces remain.  
**Recommended response:** fix-and-reland the summary-surface sweep and update RELEASE_PROOF if any checklist item is intentionally partial.

### F-IR-05. W52 loads multi-canonical rows but the explicit disposition prose is unreachable

**Q-bucket:** Q-W52 / Q-summary-surface sweep  
**Severity:** acceptance-weak  
**Reference:** `reporting/plans/v0_2_0/PLAN.md:409`; `src/health_agent_infra/core/review/weekly.py:604`; `src/health_agent_infra/core/review/render.py:125`; `src/health_agent_infra/core/review/render.py:156`; `verification/tests/test_review_weekly.py:215`  
**Argument:** PLAN §2.D says multi-canonical days should surface both rows with explicit "multiple plans on this day" disposition. The query path does load both non-superseded rows (`weekly.py:604-620`), and the test covers that loader behavior. The renderer contains the intended footer (`render.py:125-138`), but `_multi_canonical_day_count()` always returns `0` because `WeeklyCoverage` carries no multi-canonical metadata (`render.py:156-162`; coverage fields at `weekly.py:331-336`). As implemented, the explicit disposition can never render.  
**Recommended response:** fix-and-reland if PLAN §409 is treated as in-cycle acceptance. Carry a multi-canonical count or date list into the bundle and add a markdown/JSON assertion for the disposition.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-PROV-2 | pass | Dormant-domain locator whitelist/emission tests are present; real-schema row-version semantics become a W58D integration bug, not a locator-emission closure bug. |
| W-EVCARD-DAILY | pass | Migration 027 schema matches RELEASE_PROOF description: daily recommendation cards, payload separation, and transaction-coupled intent. |
| W-EVCARD-WEEKLY | pass | Migration 028 schema matches append-only weekly claim-card carrier, `card_id` PK only, and quantitative/comparative CHECK. |
| W52 | fixes | Main aggregation surface is broad and tested, but explicit multi-canonical disposition prose is unreachable. |
| W-FACT-ATOM | pass | 30-fixture corpus present; precision test enforces >=98% and corpus count is 243 parsed atoms / 243 correct per RELEASE_PROOF. |
| W58D | fixes | Factuality corpus and eval runner pass, x-rule lane requires `user_id`, and review-weekly gate is wired by default; real-schema row-version drift is not detected, and mypy/bandit gates fail. |
| W-MCP-THREAT | pass | Doc exists at 399 lines. |
| W-COMP-LANDSCAPE | pass | Doc exists at 420 lines. |
| W-NOF1-METHOD | pass | Doc exists at 469 lines. |
| W-EXPLAIN-UX-CARRY | pass | Disposition tracker has 6 entries, all `implemented-in-W52`. |
| W-2U-GATE-2 | did-not-fire | Matches RELEASE_PROOF/D16 naming; no transcript expected. |

## Open questions for maintainer

- Should F-IR-05 be treated as release-blocking acceptance closure, or accepted as a known W52 note because the query layer already surfaces both rows? My recommendation is fix-and-reland because PLAN §409 explicitly required the disposition string.
- Are any of the mypy errors intentionally out of scope for v0.2.0? The gate in the prompt is repository-wide, so the review treats all 11 as blocking until the command is clean.
