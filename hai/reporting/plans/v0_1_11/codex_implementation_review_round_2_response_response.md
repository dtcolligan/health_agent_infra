# Maintainer Response — Codex Implementation Review Round 2

> **Authored 2026-04-29** by Claude in response to Codex's
> `codex_implementation_review_round_2_response.md` (verdict:
> `DO_NOT_SHIP`, 1 blocker + 2 important).
>
> **Status.** All 3 findings addressed in additional commits on
> `cycle/v0.1.11`. Branch ready for round 3 review.

---

## 1. Triage summary

| Finding | Severity | Disposition | Resolution |
|---|---|---|---|
| F-IR2-01 W-E timestamp-sensitive fingerprint | blocker | accept-fix | rework fingerprint to hash semantic content columns; exclude `projected_at`/`corrected_at`/`derived_from`/`ingest_actor` |
| F-IR2-02 demo regression proof overstates | important | accept-fix | RELEASE_PROOF § 2.7 + PLAN scoped to boundary-stop demo; subprocess test extended to exercise `daily` + `today` + `--supersede` |
| F-IR2-03 W-W narrowing partial | important | accept-fix | PLAN § 2.16 test list aligned with shipped reality; concurrency claim corrected; no-history now refuses by default |

No disagreements. All three are real follow-on gaps the round-1
fixes introduced or left.

---

## 2. Per-finding response

### F-IR2-01 — W-E fingerprint timestamp-sensitive

**Accept (blocker).** Codex caught a real second-order bug
introduced by my round-1 fix. By including `projected_at` +
`corrected_at` directly in the hash, I made the fingerprint
sensitive to wall-clock churn — a daily reproject of byte-
identical raw evidence bumps those timestamps and would now
incorrectly mint `_v2`. The function's own docstring carried
the contradiction (hash these because they update on every
UPSERT — but exclude wall-clock fields because they churn).

**Revision applied** in `core/synthesis.py`:

- New constant `_FINGERPRINT_EXCLUDED_COLUMNS` enumerates the
  per-table columns to skip: `projected_at`, `corrected_at`,
  `derived_from` (encodes submission_id with wall-clock at
  composition time), and `ingest_actor` (provenance metadata
  that doesn't reflect content changes).
- `_compute_state_fingerprint` now uses `PRAGMA table_info` to
  enumerate each accepted-state table's columns and selects all
  EXCEPT the excluded set. Hashes a sorted-keys JSON dump of
  the resulting row dict per table.
- This handles every accepted-state table generically — no
  hardcoded column lists per domain. A future schema change
  that adds content columns gets included automatically; a
  change that adds another timestamp column needs to be added
  to the excluded set.

**New regression test** in
`test_daily_supersede_on_state_change.py::test_reproject_with_same_content_different_timestamps_is_noop`:

1. Seed accepted_nutrition_state_daily with content X at T0.
2. Run synthesis → canonical plan (fingerprint computed).
3. UPDATE the same row: ONLY `projected_at` + `corrected_at`
   change; content fields stay byte-identical.
4. Re-run synthesis → assert canonical plan id returned, no
   `_v2` minted, only one daily_plan row.

Pre-fix this test would have failed. Post-fix it passes
alongside the existing
`test_rerun_after_intake_nutrition_change_auto_supersedes`
that asserts a real content change DOES auto-supersede. Both
contracts hold simultaneously.

### F-IR2-02 — Demo regression proof overstates

**Accept (important).** RELEASE_PROOF + PLAN claimed things the
boundary-stop transcript doesn't deliver: "scripted intakes
populate enough state for `hai today` to render", "re-run
auto-supersedes `_v2`", "`hai daily --supersede` on a fresh
date exits USER_INPUT", "`hai intake gaps --from-state-snapshot`
emits gaps", "`hai doctor --deep` routes to FixtureProbe."
Some of those are unit-tested elsewhere; the proof made it
sound like the demo flow exercises them, which it doesn't
without proposal seeding.

**Revision applied** in `RELEASE_PROOF.md § 2.7`:

- Rewritten to scope the gate explicitly to the **boundary-stop
  demo** for v0.1.11. What runs:
  `demo start → intakes → daily (returns awaiting_proposals) →
  today (no plan signal) → demo end → real-state byte-identical`.
- Items deferred to v0.1.12 W-Vb explicitly enumerated:
  `hai daily reaching synthesis with proposals seeded`,
  `re-run auto-supersede via _v2 end-to-end through the demo
  session`, `hai today rendering a populated plan`.
- W-W and W-X contracts noted as **independently verified** by
  their own tests, NOT as part of the demo regression gate's
  executable transcript.

**Subprocess test extended** in
`test_demo_isolation_surfaces.py::test_subprocess_cli_writes_under_demo_isolate_real_state`:

Now exercises (in order):
1. `demo start --blank`
2. `intake readiness`
3. `intake nutrition`
4. `intake stress`
5. `daily --skip-pull --source csv` — asserts
   `overall_status == "awaiting_proposals"` (the canonical
   boundary signal).
6. `today` — asserts exit-code 1 with "no plan" stderr (the
   visible signal that the runtime/skill boundary has not
   been crossed).
7. `daily --supersede --as-of 2027-01-01` — asserts no crash;
   `--supersede` short-circuits at awaiting_proposals before
   reaching the W-F gate.
8. `demo end`.
9. Real DB checksum + real base_dir recursive checksum
   byte-identical pre/post.

The transcript and the test now agree on what the gate covers.

### F-IR2-03 — W-W narrowing partial

**Accept (important).** Three concrete mismatches:

1. **PLAN § 2.16 listed 4 test files that don't exist**
   (`test_intake_gaps_source_parity.py`,
   `test_intake_gaps_concurrency.py`,
   `test_intake_gaps_jsonl_old_rows_kept.py`,
   `test_intake_gaps_capabilities_emission.py`).
2. **PLAN acceptance claimed "100/100 trials produce one of two
   valid shapes"** (concurrent write/read assertion) but the
   landed test is sequential determinism over an unchanged DB.
3. **PLAN said no-history-refuses, impl/test allowed it.**

**Revisions applied**:

- `PLAN.md § 2.16` "Files" + "Tests" + "Acceptance" sections
  rewritten to match what actually shipped. The 4 deferred test
  files are explicitly listed as "Out of scope for v0.1.11"
  with brief reasons (each one ties to the JSONL-tail consumer
  that doesn't exist in v0.1.11). Accepted as a partial-narrow
  outcome of the F-IR-03 round-1 fix.
- The "100/100 trials" line replaced with the accurate
  "100 trials produce byte-identical output (the SQLite
  read-isolation guarantee)."
- `core/intake/gaps.py:compute_intake_gaps_from_state_snapshot`
  no-history branch now refuses with `StalenessRefusal` unless
  `allow_stale=True` is passed. The error message names the
  override flag.
- `test_intake_gaps_from_snapshot.py`:
  - Replaced `test_no_sync_run_history_passes_gate` with
    `test_no_sync_run_history_refuses_without_override` (the
    fail-closed variant) and
    `test_no_sync_run_history_passes_with_override` (the
    explicit override variant with `staleness_warning` field).
  - Updated `test_top_level_payload_carries_audit_fields` to
    seed a recent successful sync (otherwise the new no-history
    refusal fires before the audit-fields check).

PLAN.md, RELEASE_PROOF.md, and the test surface now agree on
the same narrowed contract.

---

## 3. Net cycle impact

| Metric | Pre-R2-fixes | Post-R2-fixes |
|---|---|---|
| Test surface | 2354 passing | **2356 passing** (+2; 2 tests replaced + 1 added) |
| Mypy errors | 21 | 21 (unchanged) |
| Bandit -ll medium/high | 0 | 0 |
| Blocker-class findings | 1 (F-IR2-01) | 0 (verify in R3) |
| Branch state | clean | clean (additional commits on cycle/v0.1.11) |

The W-E fingerprint rework is the load-bearing change. The
demo-flow + W-W revisions are honest narrowings that align
the proof and tests with the shipped behaviour.

---

## 4. Outstanding actions

Branch `cycle/v0.1.11` ready for **Codex implementation review
round 3**. Both W-E contracts now hold simultaneously:

1. **State change → auto-supersede** via `_v<N>` (proven by
   `test_rerun_after_intake_nutrition_change_auto_supersedes`).
2. **Same content + churned timestamps → true no-op** (proven
   by
   `test_reproject_with_same_content_different_timestamps_is_noop`).

Worth re-checking in round 3:

- F-IR2-01 fingerprint truly hashes content only — verify the
  excluded set covers every wall-clock-bearing column without
  excluding semantic ones. The `PRAGMA table_info` approach is
  generic; a misclassified column would be visible as a
  test-suite regression.
- F-IR2-02 RELEASE_PROOF and PLAN no longer claim runnable items
  the v0.1.11 demo flow doesn't exercise.
- F-IR2-03 PLAN.md § 2.16 test list matches the shipped test
  files; the no-history fail-closed contract is consistent
  across PLAN, impl, and tests.
