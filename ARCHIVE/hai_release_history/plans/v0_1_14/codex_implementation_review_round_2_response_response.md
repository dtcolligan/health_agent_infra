# v0.1.14 Codex IR Round 2 — Maintainer Response

**Round:** 2
**Codex verdict:** SHIP_WITH_FIXES (2 findings)
**Maintainer disposition:** ACCEPT 2 / DISAGREE 0
**Action:** both findings fixed-and-relanded.

---

## Summary

Round 2 surfaced exactly the empirical IR pattern: 2 second-order
issues introduced by round-1 fixes (F-IR-05 ordering bug + F-IR-03
DemoMarkerError propagation gap). Both ACCEPTED; fixes applied.

The settling shape **5 → 2** matches the twice-validated empirical
norm (v0.1.12 + v0.1.13). Round 3 should land at SHIP or
SHIP_WITH_NOTES per the empirical 1-nit close.

---

## Per-finding disposition

### F-IR-R2-01 — `restore_backup` mutates destination logs before proving the bundle is restorable

**Disposition:** ACCEPT (correctness-bug; round-1 fix introduced
ordering regression).
**Open question Codex raised:** "should a manifest-listed JSONL
member ever be optional?" — **maintainer answer: no.** The manifest
is the bundle's contract; if a basename is listed, the tar must
ship that member. Absence is malformed and refuses the whole
restore. The round-1 code's silent-skip for missing manifest-listed
members was incorrect, and the fix below treats them as fatal
(matching Codex's recommendation).

**Fix.** Refactored `restore_backup` to a strict preflight-then-write
shape:

1. **Preflight pass over the tar** (read-only, in-memory):
   - `state.db` member must exist and be readable → reads payload
     into memory.
   - Every `manifest.jsonl_files` entry must have a corresponding
     `jsonl/<basename>` member in the tar; absence is fatal.
     Each member's payload is read into memory.
   - Every destination write path is checked via
     `dest.relative_to(base_dir.resolve())` — defence-in-depth.

2. **Destination-mutation pass** (only if preflight passed):
   - Stale `*.jsonl` clearing.
   - `state.db` write from in-memory payload.
   - Each manifest-listed jsonl write from in-memory payload.

The in-memory staging makes refusal atomic with respect to the
destination — a malformed bundle never modifies the destination
even by accident.

**Tests added** in `verification/tests/test_backup_restore_roundtrip.py`:

- `test_restore_refuses_missing_state_db_without_mutating_destination`
  — pre-populates a stale destination jsonl, builds a bundle that
  drops `state.db`, asserts refusal AND that the stale log is still
  present (preflight refused before clearing).
- `test_restore_refuses_manifest_listed_jsonl_missing_from_tar` —
  builds a bundle whose manifest lists `review_outcomes.jsonl` but
  the tar doesn't include it; pre-populates a same-named stale log
  at destination; asserts refusal AND that the same-named stale log
  preserves its old content (preflight refused before writing).

The pre-existing roundtrip + path-traversal + stale-clearing tests
still pass under the new preflight shape.

### F-IR-R2-02 — Demo preflight corrupt-marker path bypasses cleanup and `SystemExit(2)`

**Disposition:** ACCEPT (acceptance-weak; round-1 fix's
`get_active_marker()` call propagated `DemoMarkerError` instead of
falling through to cleanup).
**Fix.** `_preflight_demo_session_check` in
`verification/dogfood/runner.py` now catches `DemoMarkerError`
explicitly:

```python
if is_demo_active():
    try:
        marker = get_active_marker()
    except DemoMarkerError as exc:
        cleaned = cleanup_orphans()
        print(<refuse with explicit DemoMarkerError + cleaned list>)
        raise SystemExit(2) from exc
    # ... valid-marker refusal path ...
```

The preflight now refuses on three failure modes: valid active
marker (round 1 covered), corrupt/schema-mismatched marker
(round 2 fix), orphan marker (round 1 covered).

**Tests added** in `verification/tests/test_runner_demo_preflight.py`:

- `test_preflight_refuses_on_corrupt_marker_json` — hand-writes
  `{not valid json` at `demo_marker_path()`; asserts `SystemExit(2)`,
  not `DemoMarkerError` propagation.
- `test_preflight_refuses_on_marker_with_missing_scratch_root` —
  writes a valid-shape marker pointing at a nonexistent
  `scratch_root`; asserts `SystemExit(2)`.

The pre-existing valid-active-marker + no-marker tests still pass.

---

## Verification (post-r2-fix gates)

| Gate | Result |
|---|---|
| Pytest narrow | **2565 passed, 3 skipped, 0 failed** (+4 from r2 regression tests vs r1's 2561) |
| Pytest broader (-W error::Warning) | **2565 passed, 3 skipped, 0 failed, 0 errors** |
| Mypy | 0 errors @ 127 source files |
| Bandit -ll | 46 Low / 0 Medium / 0 High |
| Ruff | clean |
| Capabilities byte-stability | held |
| `agent_cli_contract.md` | held |
| `hai eval run --scenario-set all` | 35/35 passing |

---

## Per-W-id round-3 disposition

| W-id | Round-2 verdict | Round-3 disposition |
|---|---|---|
| W-2U-GATE | clean | clean |
| W-PROV-1 | clean | clean |
| W-EXPLAIN-UX | clean | clean |
| W-BACKUP | fix | **fixed-and-relanded** (F-IR-R2-01 closed via preflight refactor) |
| W-FRESH-EXT | fix | **fixed-and-relanded** (F-IR-R2-02 closed via DemoMarkerError catch) |
| W-AH | clean | clean |
| W-AI | clean | clean |
| W-AJ | clean | clean |
| W-AL | clean | clean |
| W-AM | clean | clean |
| W-AN | clean | clean |
| W-29 | clean | clean |
| W-Vb-3 | clean | clean |
| W-DOMAIN-SYNC | clean | clean |
| Ship gates | clean | clean |

---

## Round 3 readiness

Both R2 findings closed. Round 3 should audit the post-r2 state.
Empirical IR settling shape (twice-validated) predicts round 3
finds 0 (`SHIP`) or 1 nit (`SHIP_WITH_NOTES`).

---

## Settling shape so far

```
Round 0 (implementation):  no formal count; codex IR opens here
Round 1 (Codex):           7 findings  → SHIP_WITH_FIXES
Round 2 (Codex):           2 findings  → SHIP_WITH_FIXES
Round 3 (Codex, expected): 0-1 finding → SHIP or SHIP_WITH_NOTES
```

Mirrors v0.1.12 IR (5 → 2 → 0) + v0.1.13 IR (6 → 2 → 0), with
v0.1.14's higher round-1 count reflecting the larger surface
(F-IR-01..07 covers ship-gate + scope-mismatch + security +
provenance).
