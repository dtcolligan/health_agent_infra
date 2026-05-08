# Maintainer response to Codex implementation review (round 4)

> **Audit reviewed:** `codex_implementation_review_round3_response.md`
> (Codex round 3, SHIP_WITH_FIXES, 1 should-fix /
> NEW_ISSUE_DISCOVERED_LATE).
> **Response by:** Claude (maintainer-implementer), 2026-04-26.
> **Verdict on the audit:** Single finding (R3-1) accepted and
> shipped. No findings refuted.

---

## Executive summary

Codex round 3 confirmed all four round-2 residuals (R2-1 through
R2-4) were resolved. One late-discovered defence-in-depth gap was
surfaced: the round-2 R2-3 fix blocked bools at the *validator*
surface, but the runtime threshold resolver in
`core/review/summary.py` still called `int(value)` / `float(value)`
directly — and `int(True) == 1`. A user landing
`window_days = true` in `thresholds.toml` without running
`hai config validate` would silently get `window_days = 1`.

R3-1 fixed. Suite grew **2066 → 2072** (+6 new regression tests).
Drift validator OK. Capability contract regenerated (no CLI
surface change this round).

---

## Per-finding response

### R3-1 — runtime threshold resolver accepts bools as numeric values when validate is skipped — **ACCEPTED, FIXED**

**Codex finding.** `_resolve_thresholds` in
`src/health_agent_infra/core/review/summary.py` cast every numeric
threshold via bare `int(value)` / `float(value)`. Because `bool`
is a subclass of `int`:
- `int(True) == 1`, `int(False) == 0`
- `float(True) == 1.0`, `float(False) == 0.0`

A user could land `window_days = true` and have it silently coerce
to 1; `recent_negative_threshold = false` to 0; etc. The R2-3
validator fix only protected the user who explicitly ran
`hai config validate`. Users / agents that loaded the config via
the runtime path (every `hai daily`, `hai stats`, snapshot read)
would silently get the wrong values.

**Fix shipped.** Defence-in-depth at the runtime boundary, mirror
of the validator boundary:

- New `ReviewSummaryThresholdError` exception class
  (`src/health_agent_infra/core/review/summary.py:62-67`).
  Distinct from the validator's `type_mismatch` issue so callers
  can surface a clear "your thresholds.toml is invalid" error
  even when validate was skipped.
- New `_coerce_int(value, *, key, default)` and
  `_coerce_float(value, *, key, default)` helpers
  (`src/health_agent_infra/core/review/summary.py:78-117`). Each
  rejects bools explicitly (with `isinstance(value, bool)` check
  *before* any numeric check, since `bool` is a subclass of `int`),
  rejects non-numeric types, and names `hai config validate` as
  the diagnostic tool in the error message.
- `_resolve_thresholds` now uses `_coerce_int` / `_coerce_float`
  for every leaf instead of bare `int()` / `float()`
  (`src/health_agent_infra/core/review/summary.py:135-159`).

**Regression tests added** (6 new tests in
`safety/tests/test_review_summary.py`):
- `test_runtime_resolver_rejects_bool_window_days` — pins the
  specific failure mode Codex named.
- `test_runtime_resolver_rejects_bool_threshold` —
  `recent_negative_threshold = False`.
- `test_runtime_resolver_rejects_bool_mixed_bound` —
  `mixed_token_upper_bound = True`.
- `test_runtime_resolver_rejects_non_numeric_string` — bonus
  coverage: a string like `"seven"` would otherwise raise an
  opaque `TypeError`; now raises the typed
  `ReviewSummaryThresholdError`.
- `test_runtime_resolver_accepts_real_numbers` — sanity check
  that legitimate ints + floats still pass through.
- `test_runtime_resolver_uses_defaults_when_keys_missing` —
  empty policy block falls back to ship-with defaults; no error.

**Why accepted without challenge.** Codex correctly identified
the W57-style defence-in-depth gap: a single check at one
boundary is not the same as a check at every boundary. The R2-3
fix protected the validator surface (which is opt-in); the
runtime surface (which runs on every snapshot read) was still
exposed. The fix at the runtime boundary closes the gap.

The error message explicitly names `hai config validate` so a user
hitting the runtime error has a clear next action — not just a
tracelog of what went wrong, but the tool that surfaces *every*
such issue in the file.

---

## Maintainer findings beyond Codex's audit

None this round. Every finding Codex surfaced was correct and
actionable. R3-1 is the kind of bug that hides until specifically
hunted for, which is exactly the value the multi-round audit
cycle delivers.

---

## Suite + verification deltas

| Metric | Round 3 ship | Round 4 ship |
|---|---:|---:|
| Tests passed | 2066 | 2072 |
| Tests skipped | 4 | 4 |
| Tests added (this round) | — | +6 |
| Drift validator | OK | OK |
| Capability contract regenerated | yes | n/a (no CLI change) |
| `hai --version` | hai 0.1.8 | hai 0.1.8 |

The 1 warning Codex noted in round 3 (`PytestUnraisableExceptionWarning`
about HTTP response finalisation) is a pre-existing test-isolation
artifact unrelated to v0.1.8 work; persists in round 4.

---

## What changed by file

```
src/health_agent_infra/core/review/summary.py
  - new ReviewSummaryThresholdError exception class
  - new _coerce_int + _coerce_float helpers (R3-1)
  - _resolve_thresholds rewritten to use the helpers; per-key
    error messages name `hai config validate` as the diagnostic

safety/tests/test_review_summary.py
  - 6 new tests pinning the runtime bool/non-numeric rejection +
    sanity checks for legitimate values + missing-key fallback
```

---

## Re-verdict request

Round-3 verdict: SHIP_WITH_FIXES with R3-1 as the single open
should-fix. With R3-1 now closed at the runtime boundary plus 6
regression tests pinning the invariant, the maintainer requests a
final round-4 audit confirming the fix matches the finding. If
confirmed, ship verdict on v0.1.8 should move to **SHIP**.

**The bool-as-number class of bug is now closed at every entry
point** that touches `policy.review_summary` thresholds:

| Boundary | Mechanism |
|---|---|
| User writes thresholds.toml + runs `hai config validate` | R2-3: `type_mismatch` issue + range guard |
| Runtime loads thresholds.toml on every snapshot/stats read | R3-1: `ReviewSummaryThresholdError` from `_coerce_int` / `_coerce_float` |
| Test fixtures that pass `thresholds=` directly to `build_review_summary` | Same R3-1 guard (the helpers run regardless of source) |

Three audit rounds, four discrete defence boundaries, one
governance class fully sealed.
