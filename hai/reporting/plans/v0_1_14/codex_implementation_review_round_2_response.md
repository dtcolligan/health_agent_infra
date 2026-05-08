# Codex Implementation Review — v0.1.14

**Verdict:** SHIP_WITH_FIXES  
**Round:** 2

## Verification summary

- Tree state: clean before writing this file; branch `cycle/v0.1.14`; HEAD `c4ac1d0` (`v0.1.14 IR r1: fixes for F-IR-01..F-IR-07`); 10 commits ahead of `main`.
- Test surface: `uv run pytest verification/tests -q` -> **2561 passed, 3 skipped**. `uv run pytest verification/tests -W error::Warning -q` -> **2561 passed, 3 skipped**.
- Ship gates: mypy clean (`0 errors @ 127 source files`); ruff clean; bandit **46 Low / 0 Medium / 0 High**; `hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md` empty; `hai capabilities --json` command count **59**; `hai eval run --scenario-set all` **35/35 passed**.
- Round-1 fix status: F-IR-01, F-IR-02, F-IR-04, F-IR-06, and F-IR-07 are closed. F-IR-03 and F-IR-05 each introduced one second-order regression below.

## Findings

### F-IR-R2-01. `restore_backup` mutates destination logs before proving the bundle is restorable

**Q-bucket:** Q-BACKUP / Q-cross-cutting code quality  
**Severity:** correctness-bug  
**Reference:** `c4ac1d0`; `src/health_agent_infra/core/backup/bundle.py:212`; `src/health_agent_infra/core/backup/bundle.py:228`; `src/health_agent_infra/core/backup/bundle.py:243`  
**Argument:** The F-IR-05 fix clears stale destination `*.jsonl` files before the restore code opens the tarball and verifies that the required payload exists. Lines 212-224 delete destination logs based only on the manifest. The code does not check for `state.db` until lines 228-235, and it treats manifest-listed JSONL members as optional at lines 243-248. A malformed bundle with a valid manifest but no `state.db` now deletes destination audit logs and then raises `BackupError("bundle missing 'state.db'")`; I reproduced that in a scratch temp dir with `stale_exists_after: False`. The same ordering lets a malformed bundle preserve a stale same-name destination log if `manifest.jsonl_files` names it but the tar member is absent, because that filename is excluded from stale deletion and the missing member is silently skipped. This breaks point-in-time restore and the no-mutation-on-refusal expectation for invalid bundles.  
**Recommended response:** fix-and-reland. Validate bundle completeness before any destination mutation: require `state.db`, require every manifest-listed `jsonl/<basename>` member or explicitly make missing listed logs fatal, and then write via a staging directory or otherwise perform deletion/replacement only after the preflight succeeds. Add tests for "missing `state.db` does not delete destination logs" and "manifest-listed missing JSONL does not leave stale same-name logs."

### F-IR-R2-02. Demo preflight corrupt-marker path bypasses cleanup and `SystemExit(2)`

**Q-bucket:** Q-FRESH-EXT  
**Severity:** acceptance-weak  
**Reference:** `c4ac1d0`; `verification/dogfood/runner.py:838`; `verification/dogfood/runner.py:856`; `src/health_agent_infra/core/demo/session.py:126`; `src/health_agent_infra/core/demo/session.py:138`; `src/health_agent_infra/core/demo/session.py:363`; `verification/tests/test_runner_demo_preflight.py:27`  
**Argument:** The F-IR-03 fix correctly refuses valid active demo markers, but it now checks `is_demo_active()` first and immediately calls `get_active_marker()`. `is_demo_active()` is only a marker-file presence check; for corrupt JSON, schema mismatch, or missing scratch root, `get_active_marker()` raises `DemoMarkerError` before `_preflight_demo_session_check()` reaches `cleanup_orphans()`. I reproduced the corrupt-marker case: `_preflight_demo_session_check()` raised `DemoMarkerError`, did not raise `SystemExit(2)`, and left the marker file in place. That violates the W-FRESH-EXT acceptance shape from the prompt: the preflight should call the cleanup hook and raise `SystemExit(2)` when `cleanup_orphans()` returns a non-empty list. Existing round-1 tests cover only a valid active marker and the no-marker case, so this regression is unpinned.  
**Recommended response:** fix-and-reland. Preserve the valid-marker refusal, but handle invalid/orphan markers through the cleanup path: either run `cleanup_orphans()` before the valid-marker check and then re-check for a valid marker, or catch `DemoMarkerError`, call `cleanup_orphans()`, print the stale-marker refusal, and raise `SystemExit(2)`. Add tests for corrupt marker JSON and valid marker whose scratch root is missing.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-2U-GATE | clean | v0.1.15 deferral remains documented. |
| W-PROV-1 | clean | Live snapshot path now surfaces recovery R6 locators; warning-gate leak fixed. |
| W-EXPLAIN-UX | clean | P13 and maintainer-substitute carry-forward docs held. |
| W-BACKUP | fix | F-IR-R2-01: restore can mutate destination logs before malformed-bundle refusal. |
| W-FRESH-EXT | fix | F-IR-R2-02: corrupt/orphan demo marker path bypasses cleanup/SystemExit contract. |
| W-AH | clean | Scenario count and partial destination held. |
| W-AI | clean | 30 judge-adversarial fixtures and W-AI-2 deferral held. |
| W-AJ | clean | Harness scaffold held; `bias_panel_results` preallocation remains present. |
| W-AL | clean | Calibration schema and stub decomposer held. |
| W-AM | clean | RELEASE_PROOF now honestly names 2-of-6 plus v0.1.15 W-AM-2. |
| W-AN | clean | `--scenario-set all` gate passes 35/35. |
| W-29 | clean | Deferral remains named; no cli.py split landed. |
| W-Vb-3 | clean | P2/P3/P6 partial closure remains named to W-Vb-4. |
| W-DOMAIN-SYNC | clean | Contract-test surface held. |
| Ship gates | clean | All requested gates pass locally; findings are behavioral regressions not caught by current tests. |

## Open questions for maintainer

1. For W-BACKUP, should a manifest-listed JSONL member ever be optional? The manifest field is described as files included in the bundle, so this review assumes absence is malformed and should refuse before mutation.
