# Maintainer response to Codex implementation review - v0.1.9

> **Audit reviewed:** v0.1.9 hardening implementation review,
> 2026-04-26.
> **Verdict received:** `SHIP_WITH_FIXES`.
> **Response by:** Codex implementation owner, 2026-04-26.

---

## Executive summary

Codex found three ship-blocking or should-fix issues after the B1-B8
implementation:

1. `hai daily` wrote `sync_run_log.status='ok'` even when the adapter
   reported a partial pull.
2. Skill-overlay allow-listed fields with malformed shape were silently
   ignored rather than rejected.
3. `policy_decisions[].note = null` was accepted despite the stricter
   shape contract.

All three findings were accepted and fixed. The full verification suite is
green at **2133 passed, 2 skipped**.

---

## Finding responses

### F1 - daily partial sync status lost - ACCEPTED, FIXED

`cmd_pull` already maps `adapter.last_pull_partial` to
`sync_run_log.status='partial'`, but `_daily_pull_and_project` closed the
new daily sync row with the default `ok` status. That made a partial
intervals.icu pull look fully fresh.

Fix:

- `_daily_pull_and_project` now mirrors `cmd_pull`: reads
  `last_pull_partial` and passes `status='partial'` to
  `_close_sync_row_ok` when set.
- Added `test_daily_sync_row_records_partial_when_adapter_partial`.

### F2 - malformed allowed skill-overlay fields fail soft - ACCEPTED, FIXED

The B2 overlay gate rejected out-of-lane keys, but allow-listed keys with
the wrong type, such as `rationale="raw string"`, were ignored because the
merge only copied lists. The final recommendation stayed valid, hiding the
skill drift.

Fix:

- `_overlay_skill_drafts` now rejects malformed `rationale`,
  `uncertainty`, and `follow_up.review_question` values with
  `skill_overlay_out_of_lane` before the synthesis transaction opens.
- Added regression tests for string rationale, non-string uncertainty
  item, and non-string review question.

### F3 - null policy note accepted - ACCEPTED, FIXED

`policy_decisions[].note` is optional, but when present it must be a string.
The validator accepted `None`.

Fix:

- `check_policy_decisions_shape` now rejects present-but-null notes.
- Added proposal and recommendation tests for `note: null`.

---

## Verification

```
uv run pytest verification/tests/test_b5_pull_clean_provenance.py \
  verification/tests/test_synthesis_safety_closure.py \
  verification/tests/test_validator_shape_hardening.py -q
# 63 passed

uv run pytest verification/tests -q
# 2133 passed, 2 skipped

uv run hai --version
# hai 0.1.9

uv run python scripts/check_skill_cli_drift.py
# OK: no skill ↔ CLI drift detected.

python3 -m build --wheel --sdist
# Successfully built health_agent_infra-0.1.9-py3-none-any.whl and
# health_agent_infra-0.1.9.tar.gz

python3 -m twine check dist/health_agent_infra-0.1.9*
# PASSED for wheel and sdist
```

## Re-verdict request

With the three findings fixed and release proof captured, v0.1.9 is ready
for commit/tag/publish.
