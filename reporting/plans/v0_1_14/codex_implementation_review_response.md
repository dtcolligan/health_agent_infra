# Codex Implementation Review — v0.1.14

**Verdict:** SHIP_WITH_FIXES  
**Round:** 1

## Verification summary

- Tree state: `/Users/domcolligan/health_agent_infra`, branch `cycle/v0.1.14`, 9 commits ahead of `main`, clean before and after review. `reporting/plans/v0_1_14/` has 18 files; this matches the listed categories (`1+1+1+12+1+1+1 = 18`), so the prompt's "Total: 16" is an arithmetic typo rather than a tree mismatch.
- Test surface: `uv run pytest verification/tests -q` passed (`2552 passed, 3 skipped`). `uv run pytest verification/tests -W error::Warning -q` failed (`3 failed, 2549 passed, 3 skipped`) on unclosed sqlite connection warnings.
- Ship gates: mypy clean; bandit `0 Medium / 0 High`, `46 Low`; ruff clean; `hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md` empty; capabilities command count is 59. `hai eval run --scenario-set all` passed all 35 deterministic scenarios. `--scenario-set judge_adversarial --json` reported 30 fixtures, 10 per category, shape-only.

## Findings

### F-IR-01. `-W error::Warning` ship gate fails on unclosed DB handles
**Q-bucket:** Q-ship-gates  
**Severity:** correctness-bug  
**Reference:** `uv run pytest verification/tests -W error::Warning -q`; `verification/tests/test_source_row_locator_recovery.py:273`, `verification/tests/test_source_row_locator_recovery.py:299`, `verification/tests/test_source_row_locator_recovery.py:313`  
**Argument:** RELEASE_PROOF §2 claims the warning gate is clean, but the gate fails in this review with three failures. The failures are `ResourceWarning: unclosed database` raised as `PytestUnraisableExceptionWarning`, first at `test_migration_023_adds_evidence_locators_column`, then leaking into unrelated state clean/read tests. The new W-PROV-1 test file opens sqlite connections in multiple tests without closing them, so the broader warning gate is not actually green.  
**Recommended response:** fix-and-reland. Close these connections with `try/finally` or context-manager-style helpers, re-run the warning gate, and update RELEASE_PROOF only after the gate passes.

### F-IR-02. W-PROV-1 locator emission is not wired into the live agent-facing path
**Q-bucket:** Q-PROV-1  
**Severity:** scope-mismatch  
**Reference:** `src/health_agent_infra/core/state/snapshot.py:745`, `src/health_agent_infra/core/state/snapshot.py:1298`, `src/health_agent_infra/skills/recovery-readiness/SKILL.md:23`, `src/health_agent_infra/skills/recovery-readiness/SKILL.md:90`  
**Argument:** The locator type, validator, persistence column, synthesis copy, and explain rendering exist. The missing part is the path that lets a recovery skill actually see and copy locators into a proposal. `build_snapshot` still calls `evaluate_recovery_policy(recovery_classified, raw_summary)` without the new `for_date_iso`, `user_id`, or `accepted_state_versions` kwargs, so R6 returns no locators on the normal snapshot path. Even if a caller did pass them, `_policy_to_dict` serializes only `policy_decisions`, `forced_action`, `forced_action_detail`, and `capped_confidence`, dropping `evidence_locators`. The recovery skill was not updated and still only instructs copying `policy_decisions`; it never mentions `evidence_locators`. This means the direct helper test proves the optional API works, but the v0.1.14 acceptance claim "Recovery domain emits source-row locators on R-rule firing" is not delivered through `hai state snapshot` -> skill -> `hai propose` -> synthesize -> explain.  
**Recommended response:** fix-and-reland. Wire accepted-state row versions into the recovery policy call, include `evidence_locators` in `policy_result`, update the recovery skill to copy runtime-provided locators without deriving them, and add an end-to-end test that exercises snapshot/proposal/synthesis/explain for an R6 spike.

### F-IR-03. F-PHASE0-01 preflight misses valid active demo markers
**Q-bucket:** Q-FRESH-EXT / Q-pre-implementation-gate  
**Severity:** correctness-bug  
**Reference:** `verification/dogfood/runner.py:813`, `verification/dogfood/runner.py:833`, `src/health_agent_infra/core/demo/session.py:391`, `src/health_agent_infra/core/paths.py:50`  
**Argument:** RELEASE_PROOF says the persona-runner preflight "refuses on active marker", but the implementation only calls `cleanup_orphans()` and refuses when that returns a non-empty list. `cleanup_orphans()` explicitly leaves a valid marker alone when its scratch root exists. That is the exact high-risk case for F-PHASE0-01: a valid active marker causes `resolve_db_path` / `resolve_base_dir` to override the persona runner's env and route work into the demo scratch state. The preflight therefore does not prevent the recurrence it was added to prevent.  
**Recommended response:** fix-and-reland. Have the runner refuse whenever a marker is active before starting personas, not only when cleanup removed an orphan. Add a test with a valid marker + existing scratch root.

### F-IR-04. `restore_backup` trusts manifest JSONL filenames and can write outside `base_dir`
**Q-bucket:** Q-BACKUP / Q-cross-cutting code quality  
**Severity:** security  
**Reference:** `src/health_agent_infra/core/backup/bundle.py:181`, `src/health_agent_infra/core/backup/bundle.py:211`, `src/health_agent_infra/core/backup/bundle.py:220`  
**Argument:** `restore_backup` reads `manifest.json` from the bundle and then iterates `manifest.jsonl_files` directly. For each entry it reads `jsonl/<basename>` from the tar and writes to `(base_dir / basename)`. There is no basename validation on restore, so a malicious bundle can put `../outside.jsonl` or a nested path in the manifest and make restore write outside the intended audit directory. `make_backup` only creates safe basenames, but restore must validate the untrusted bundle it is reading.  
**Recommended response:** fix-and-reland. Reject any manifest `jsonl_files` entry that is not a plain filename ending in `.jsonl` (`Path(name).name == name`, no separators, no absolute paths), and add a malicious-bundle test.

### F-IR-05. Restore is not a point-in-time restore for JSONL audit logs
**Q-bucket:** Q-BACKUP  
**Severity:** correctness-bug  
**Reference:** `src/health_agent_infra/core/backup/bundle.py:193`, `src/health_agent_infra/core/backup/bundle.py:210`, `reporting/docs/recovery.md:32`  
**Argument:** The recovery doc says restore overwrites the state DB and every JSONL log at the target base dir. The implementation creates `base_dir` and overwrites files listed in the manifest, but it never removes existing JSONL logs that are absent from the bundle. Restoring an older bundle into a non-empty base dir can therefore leave newer audit logs behind next to an older `state.db`, which breaks the point-in-time recovery expectation. The roundtrip test uses an empty destination, so it does not catch this.  
**Recommended response:** fix-and-reland. Either clear known `*.jsonl` files in `base_dir` before restoring the bundle, or document and enforce "restore only into an empty base-dir" with a refusal unless an explicit overwrite flag is passed. Add a stale-extra-log test.

### F-IR-06. W-AM release-proof claim says six escalate-tagged scenarios; only two exist
**Q-bucket:** Q-AH + Q-AM  
**Severity:** scope-mismatch  
**Reference:** `reporting/plans/v0_1_14/RELEASE_PROOF.md:22`; `src/health_agent_infra/evals/scenarios/recovery/rec_004_should_escalate_compound_signals.json:35`; `src/health_agent_infra/evals/scenarios/running/run_004_should_escalate_acwr_max.json:25`  
**Argument:** RELEASE_PROOF claims W-AM is covered by "6 escalate-tagged scenarios across the 6 domains." The audit command requested by the prompt, `grep -R -l "w-am-adversarial-escalate" src/health_agent_infra/evals/scenarios`, returns only two files: one recovery scenario and one running scenario. There are baseline escalate scenarios in other domains, but they are not the six tagged W-AM adversarial fixtures the release proof claims.  
**Recommended response:** fix-and-reland. Add/tag the missing four domain scenarios and test the count, or revise the W-AM disposition and RELEASE_PROOF to honestly say the W-AM tag coverage is 2-of-6 with a named v0.1.15 destination.

### F-IR-07. Tactical-plan summary surface is stale after implementation completion
**Q-bucket:** Q-summary-surface-sweep / Q-pre-implementation-gate  
**Severity:** provenance-gap  
**Reference:** `reporting/plans/tactical_plan_v0_1_x.md:44`, `reporting/plans/tactical_plan_v0_1_x.md:45`, `ROADMAP.md:15`, `ROADMAP.md:45`  
**Argument:** ROADMAP correctly says v0.1.14 implementation is complete and pending IR/PyPI, and it names the v0.1.15 carry-forward scope. The tactical-plan timeline still says v0.1.14 is "open (Phase 0 fired green 2026-05-01; W-PROV-1 first)" and v0.1.15 scope is "TBD per v0.1.15 cycle authoring." That is stale relative to the branch's own RELEASE_PROOF/REPORT and the ROADMAP "Next" section, especially for W-29, W-AH-2, W-AI-2, and W-Vb-4 carry-forward.  
**Recommended response:** fix-and-reland as part of the ship-freshness sweep. Update the tactical-plan row to match the post-implementation state and the named v0.1.15 destinations.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-2U-GATE | clean | Defer to v0.1.15 is documented in PLAN, ROADMAP, reconciliation, and CP status. |
| W-PROV-1 | fix | Type/storage/rendering exist, but live recovery emission path is not wired to snapshot/skill/proposal. |
| W-EXPLAIN-UX | clean-with-note | P13 and review doc exist; F-EXPLAIN-07 depends on W-PROV-1 actually emitting locators. |
| W-BACKUP | fix | Roundtrip exists, but restore has path traversal risk and stale-log point-in-time gap. |
| W-FRESH-EXT | fix | Doc-freshness test exists; persona-runner preflight misses valid active demo marker. |
| W-AH | clean-with-note | 35 non-judge scenarios present; partial closure is honestly named. |
| W-AI | clean | 30 judge-adversarial fixtures, 10 per category; `hai eval run --scenario-set judge_adversarial` shape-only works. |
| W-AJ | clean | Judge harness, `NoOpJudge`, batch default, and bias field are present. |
| W-AL | clean | FActScore-aware schema and honest stub decomposer are present; design doc cites FActScore + MedHallu. |
| W-AM | fix | Release-proof claims six tagged escalate scenarios; only two tagged fixtures exist. |
| W-AN | clean | `--scenario-set` works; `all` fans out domain + synthesis; judge-adversarial is shape-only. |
| W-29 | clean | cli.py remains a single file; deferral to v0.1.15 is named. |
| W-Vb-3 | clean | P2/P3/P6 fixture templates exist with six domain proposal templates each; partial closure to W-Vb-4 is named. |
| W-DOMAIN-SYNC | clean | Contract test pins canonical six and documents `gym` -> `strength` snapshot-read alias. |
| Ship gates | fix | Warning gate fails; other gates pass. |

## Open questions for maintainer

None blocking beyond the findings above. The main triage decision is whether to fix W-AM by adding four tagged scenarios now, or to revise the release proof and carry the residual explicitly; the current "6 scenarios" claim is not accurate on disk.
