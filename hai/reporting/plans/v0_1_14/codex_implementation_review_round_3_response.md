# Codex Implementation Review — v0.1.14

**Verdict:** SHIP_WITH_NOTES  
**Round:** 3

## Verification summary

- Tree state: clean before writing this file; branch `cycle/v0.1.14`; HEAD `2e1fe7f` (`v0.1.14 IR r2: fixes for F-IR-R2-01 + F-IR-R2-02`); 11 commits ahead of `main`.
- Test surface: targeted round-2 regression tests pass (`19 passed`). `uv run pytest verification/tests -q` passed on rerun with **2565 passed, 3 skipped**. `uv run pytest verification/tests -W error::Warning -q` passed on rerun with **2565 passed, 3 skipped**.
- Ship gates: mypy clean (`0 errors @ 127 source files`); ruff clean; bandit **46 Low / 0 Medium / 0 High**; `hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md` empty; `hai capabilities --json` command count **59**; `hai eval run --scenario-set all` **35/35 passed**.
- Gate note: the first narrow and first warning full-suite runs each hit the same transient `test_path_5_failure_path_surfaces_user_input_not_crash` `TimeoutError`; the isolated test passed immediately, and both final full-suite reruns passed. I did not treat this as an in-scope round-2-fix defect.

## Findings

### F-IR-R3-01. Backup restore preflight still creates destination directories before bundle completeness is proven

**Q-bucket:** Q-BACKUP / Q-provenance discipline  
**Severity:** nit  
**Reference:** `2e1fe7f`; `src/health_agent_infra/core/backup/bundle.py:219`; `src/health_agent_infra/core/backup/bundle.py:220`; `src/health_agent_infra/core/backup/bundle.py:222`  
**Argument:** The round-2 fix closes the load-bearing data-loss bug: `restore_backup` now reads `state.db` and every manifest-listed `jsonl/<basename>` into memory before deleting or overwriting JSONL logs. However, the implementation still performs `state_db_path.parent.mkdir(...)` and `base_dir.mkdir(...)` at lines 219-220 before opening the tar and proving required members exist at line 222 onward. I reproduced a malformed bundle missing `state.db`: it now refuses correctly and leaves `state.db`/logs untouched, but it creates the destination parent directories first. This is not a ship blocker because no audit data or DB payload is deleted or overwritten, but it makes the round-2 response's "malformed bundle never modifies the destination" wording slightly too strong.  
**Recommended response:** accept-as-known or polish before merge. If the contract is literal no destination mutation on malformed bundle, move the two `mkdir` calls after the member preflight and path-resolution checks. Otherwise, revise the wording to "no destination data mutation" and leave the current implementation.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-2U-GATE | clean | v0.1.15 deferral held. |
| W-PROV-1 | clean | Live locator path and warning-gate fix held. |
| W-EXPLAIN-UX | clean | P13 + maintainer-substitute review held. |
| W-BACKUP | note | F-IR-R3-01 is a non-blocking directory-creation nit; data mutation preflight is fixed. |
| W-FRESH-EXT | clean | Valid, corrupt, and missing-scratch demo marker paths now refuse with `SystemExit(2)`. |
| W-AH | clean | Scenario partial closure held. |
| W-AI | clean | Judge-adversarial corpus held. |
| W-AJ | clean | Harness scaffold held. |
| W-AL | clean | Calibration schema held. |
| W-AM | clean | 2-of-6 honesty + W-AM-2 destination held. |
| W-AN | clean | `--scenario-set all` passed 35/35. |
| W-29 | clean | Deferral held; no cli.py split landed. |
| W-Vb-3 | clean | P2/P3/P6 partial closure held. |
| W-DOMAIN-SYNC | clean | Contract-test surface held. |
| Ship gates | clean | Final local gate runs match RELEASE_PROOF §2 numbers. |

## Open questions for maintainer

None blocking.
