# v0.1.14 Codex IR Round 1 — Maintainer Response

**Round:** 1
**Codex verdict:** SHIP_WITH_FIXES (7 findings)
**Maintainer disposition:** ACCEPT 7 / DISAGREE 0
**Action:** all 7 findings fixed-and-relanded in the same branch.

---

## Summary

Codex round 1 surfaced 7 findings. Disposition: every finding ACCEPTED;
fixes applied in commits on top of `cycle/v0.1.14`. Round 2 audits the
post-fix state.

The most load-bearing finding was **F-IR-02** (W-PROV-1 not wired
into the live agent path). The cycle's published claim — "Recovery
domain emits source-row locators on R-rule firing" — was true only
for the unit-test direct-helper path; `build_snapshot` →
recovery skill → proposal → synthesize → explain did not actually
carry locators end-to-end. The fix wires `build_snapshot` to compute
the trailing-window `accepted_state_versions` map and pass it into
`evaluate_recovery_policy`; updates `_policy_to_dict` to surface
`evidence_locators` on the snapshot dict; updates the recovery skill
SKILL.md to copy locators verbatim from `policy_result` onto the
proposal; adds a snapshot-level test that asserts an R6 spike
fixture surfaces 3 locators on the live path.

---

## Per-finding disposition

### F-IR-01 — `-W error::Warning` ship gate fails on unclosed DB handles

**Disposition:** ACCEPT.
**Fix:** wrapped every `open_connection()` call in
`verification/tests/test_source_row_locator_recovery.py` with
`try/finally: conn.close()`. The 3 leaking sites were
`test_resolve_locator_returns_row_when_present`,
`test_resolve_locator_returns_none_when_row_missing`,
`test_migration_023_adds_evidence_locators_column`, plus the
`test_project_recommendation_writes_evidence_locators_json_column`
case.
**Verification:** `uv run pytest verification/tests -W error::Warning -q`
post-fix: **2561 passed, 3 skipped, 0 failed, 0 errors**.

### F-IR-02 — W-PROV-1 locator emission not wired into the live agent path

**Disposition:** ACCEPT (highest-severity finding).
**Fix:** three coordinated edits:

1. **`core/state/snapshot.py`:**
   - New helper `_accepted_recovery_state_versions(conn, *, user_id,
     end_date, lookback_days=7)` queries `accepted_recovery_state_daily`
     for the trailing window and returns `{as_of_date: projected_at}`.
   - `build_snapshot` now passes `for_date_iso` + `user_id` +
     `accepted_state_versions=recovery_state_versions` into
     `evaluate_recovery_policy`.
   - `_policy_to_dict` now surfaces `evidence_locators` on the result
     dict when present (recovery R6 firing); other policy results
     leave the field absent.

2. **`src/health_agent_infra/skills/recovery-readiness/SKILL.md`:**
   - Bundle-load section now lists `evidence_locators[]` as an
     optional field on `policy_result` with the v0.1.14 W-PROV-1
     citation.
   - Output section instructs the skill to copy
     `snapshot.recovery.policy_result.evidence_locators` verbatim
     onto the proposal's `evidence_locators` field when present, and
     to omit it when absent. Explicitly forbids the skill from
     deriving locators itself.

3. **New tests in `test_source_row_locator_recovery.py`:**
   - `test_build_snapshot_emits_evidence_locators_on_r6_spike`:
     constructs a 3-day spike fixture, runs `build_snapshot`,
     asserts `snapshot.recovery.policy_result.evidence_locators`
     contains 3 entries with the expected `as_of_date` / `column` /
     `row_version` shape.
   - `test_build_snapshot_omits_evidence_locators_when_no_r6_spike`:
     baseline-day fixture with `resting_hr_spike_days=0` —
     locators field is absent from policy_result.

**Verification:** the new tests pass. The end-to-end claim "Recovery
domain emits source-row locators on R-rule firing" is now true on the
live `build_snapshot → policy_result` path that the recovery skill
consumes. The synthesis-side copy to recommendation_log already worked
in round 0 (Codex verified).

### F-IR-03 — F-PHASE0-01 preflight misses valid active demo markers

**Disposition:** ACCEPT.
**Fix:** rewrote `_preflight_demo_session_check` in
`verification/dogfood/runner.py` to refuse on **any** active marker
(via `is_demo_active()`), not only orphans. Order of checks:

1. `is_demo_active()` — refuse with explicit `marker_id` in the error
   message; emit `hai demo end` / `hai demo cleanup` recovery hint.
2. `cleanup_orphans()` — refuse if it returns a non-empty list (the
   narrow corrupted-marker case `is_demo_active` returns False for).

Added `verification/tests/test_runner_demo_preflight.py`:
- `test_preflight_refuses_on_valid_active_marker` — opens a session
  with an explicit `scratch_root` (so the marker is valid, not
  orphan), asserts `_preflight_demo_session_check` raises
  `SystemExit(2)`.
- `test_preflight_passes_when_no_marker` — confirms baseline behaviour.

**Verification:** both tests pass under `-W error::Warning`.

### F-IR-04 — `restore_backup` trusts manifest jsonl filenames; path traversal possible

**Disposition:** ACCEPT (security finding).
**Fix:** `core/backup/bundle.py::restore_backup` now validates every
`manifest.jsonl_files` entry before extraction:

```python
if (
    not isinstance(entry, str)
    or entry == ""
    or Path(entry).name != entry
    or not entry.endswith(".jsonl")
):
    raise BackupError("bundle manifest contains an unsafe jsonl_files entry ...")
```

Plus defence-in-depth: every resolved write path is checked via
`dest.relative_to(base_dir.resolve())` and refuses on traversal.

Added 4 malicious-bundle tests:
- `test_restore_refuses_jsonl_entry_with_path_traversal` (`../`)
- `test_restore_refuses_jsonl_entry_with_absolute_path` (`/etc/...`)
- `test_restore_refuses_jsonl_entry_with_separator` (`nested/log.jsonl`)
- `test_restore_refuses_jsonl_entry_without_jsonl_extension` (wrong suffix)

**Verification:** all 4 pass. Roundtrip test still passes.

### F-IR-05 — Restore is not a point-in-time restore for JSONL audit logs

**Disposition:** ACCEPT.
**Fix:** `restore_backup` now clears stale `*.jsonl` files at
`base_dir` before extracting the bundle's logs. Files outside the
bundle's manifest set are unlinked; non-`.jsonl` files (e.g.,
`config.toml`) are preserved.

Added `test_restore_clears_stale_jsonl_files_not_in_bundle`:
- Pre-populates destination with a stale `*.jsonl` not in the bundle
  + a non-`.jsonl` keepsake.
- Restores the bundle.
- Asserts bundle's logs landed, stale jsonl is gone, keepsake intact.

**Verification:** passes.

### F-IR-06 — W-AM release-proof claim says six escalate-tagged scenarios; only two exist

**Disposition:** ACCEPT.
**Fix:** revised RELEASE_PROOF.md §1 W-AM row to honestly name the
state: 2-of-6 tagged scenarios shipped (recovery + running), 4
fork-deferred to v0.1.15 W-AM-2 (sleep / strength / stress /
nutrition). Reason for the 4-deferral is documented inline: the
removed scenarios failed their own expected-firing-token assertions
against the live classify+policy stack and were dropped mid-cycle
rather than re-authored under time pressure (the same root cause as
the W-AH partial — bulk authoring without per-scenario validation
produces fixtures that don't match the runtime).

Added `W-AM-2` to RELEASE_PROOF.md §5 "Out of scope" with the v0.1.15
named destination.

### F-IR-07 — Tactical-plan summary surface stale after implementation completion

**Disposition:** ACCEPT.
**Fix:** `reporting/plans/tactical_plan_v0_1_x.md` v0.1.14 / v0.1.15
rows updated to match RELEASE_PROOF + ROADMAP post-implementation
state:

- v0.1.14 row now reads "implementation complete; pending Codex IR
  + PyPI publish" (was "open (Phase 0 fired green)") and enumerates
  the 8 closed + 3 partial + 2 deferred + 1 absorbed shape.
- v0.1.15 row now enumerates the 6 named carry-forward items
  (W-2U-GATE, W-29, W-AH-2, W-AI-2, W-AM-2, W-Vb-4) instead of
  "scope TBD".

---

## Verification (post-fix gates)

| Gate | Result |
|---|---|
| Pytest narrow | **2561 passed, 3 skipped, 0 failed** (+9 from new regression tests vs round 0's 2552) |
| Pytest broader (-W error::Warning) | **2561 passed, 3 skipped, 0 failed, 0 errors** (F-IR-01 closed) |
| Mypy | 0 errors @ 127 source files |
| Bandit -ll | 46 Low / 0 Medium / 0 High |
| Ruff | clean |
| Capabilities byte-stability | held |
| `agent_cli_contract.md` | held |
| `hai eval run --scenario-set all` | 35/35 passing |

---

## Per-W-id round-2 disposition

| W-id | Round-1 verdict | Round-2 disposition |
|---|---|---|
| W-2U-GATE | clean | clean (unchanged) |
| W-PROV-1 | fix | **fixed-and-relanded** (F-IR-02 wired end-to-end + tested) |
| W-EXPLAIN-UX | clean-with-note | **clean** (locator emission depended on F-IR-02; now lands) |
| W-BACKUP | fix | **fixed-and-relanded** (F-IR-04 + F-IR-05 closed) |
| W-FRESH-EXT | fix | **fixed-and-relanded** (F-IR-03 closed) |
| W-AH | clean-with-note | clean (unchanged) |
| W-AI | clean | clean (unchanged) |
| W-AJ | clean | clean (unchanged) |
| W-AL | clean | clean (unchanged) |
| W-AM | fix | **fixed-and-relanded** (F-IR-06 RELEASE_PROOF revised honestly) |
| W-AN | clean | clean (unchanged) |
| W-29 | clean | clean (unchanged) |
| W-Vb-3 | clean | clean (unchanged) |
| W-DOMAIN-SYNC | clean | clean (unchanged) |
| Ship gates | fix | **fixed-and-relanded** (F-IR-01 closed; warning gate green) |

---

## Round 2 readiness

All 7 findings closed. Round 2 should audit:

1. F-IR-02 wiring: spot-verify `build_snapshot` → `policy_result.evidence_locators`
   surfaces correctly; SKILL.md copy contract is honest;
   end-to-end test exercises the full path.
2. F-IR-04 path-traversal: malicious bundle tests pass;
   defence-in-depth `relative_to` check is correct.
3. F-IR-05 stale-log clearing: stale-extra-log test asserts the
   point-in-time semantics.
4. F-IR-06 W-AM honesty: 2-of-6 in RELEASE_PROOF; W-AM-2 named in §5.
5. F-IR-07 tactical_plan: v0.1.14 + v0.1.15 rows match
   RELEASE_PROOF + ROADMAP state.

Empirical IR settling shape predicts round 2 finds 1-2 second-order
issues (the typical "summary surface caught up to the body but body
introduced new drift" shape). Round 2 verdict expected `SHIP_WITH_NOTES`
or `SHIP`.

---

## Next concrete step

Maintainer: commit the round-1 fixes + this response file, then send
the round-2 audit prompt to Codex.
