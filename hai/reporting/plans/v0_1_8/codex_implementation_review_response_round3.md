# Maintainer response to Codex implementation review (round 3)

> **Audit reviewed:** `codex_implementation_review_round2_response.md`
> (Codex round 2, SHIP_WITH_FIXES, 3 should-fix + 1 nit).
> **Response by:** Claude (maintainer-implementer), 2026-04-26.
> **Verdict on the audit:** All four findings accepted and shipped.
> No findings refuted.

---

## Executive summary

Codex round-2 verified the round-1 P1 blockers were closed at the
CLI boundary and resolved P2-1, P2-2, P3-1. Three NEW_ISSUE_FROM_FIX
residuals were surfaced under P1-1 / P1-2 / P2-3 plus one nit. All
four are now fixed. Suite grew **2058 → 2066** (+8 new regression
tests pinning the residuals). Drift validator OK. Capability
contract regenerated.

---

## Per-finding response

### R2-1 — `hai clean` silently swallows data-quality projection failures — **ACCEPTED, FIXED**

**Codex finding.** The data-quality projection in `cmd_clean` was
wrapped in `except Exception: pass`. Result: a projector or schema
regression would make the data-quality ledger silently empty, and
because the stats surface is now strictly read-only (round-1 P1-1
fix), the user has no path to discover the failure.

**Fix shipped.** Replaced the bare `except Exception: pass` with a
stderr warning naming the date, user, exception class, and message,
plus an explicit user-facing instruction that
`hai stats --data-quality` will report empty rows for the date until
the projection is re-run
(`src/health_agent_infra/cli.py:783-806`).

The accepted-state writes (recovery / running / sleep / stress)
remain committed — data-quality is genuinely best-effort and we do
not roll back accepted state on a projection error — but the failure
is now visible.

**Why accepted without challenge.** The original "best-effort, never
block clean" intent was right, but Codex correctly flagged that
"best-effort" without a visibility path is the same as "broken." A
stderr warning is the minimum credible surface.

### R2-2 — agent-proposed supersede deactivates old active row before user commit — **ACCEPTED, FIXED**

**Codex finding.** `supersede_intent` and `supersede_target` flipped
the old row to `superseded` immediately, regardless of whether the
new row was user-authored or agent-proposed. An agent-proposed
supersede with `status="proposed"` would pass the round-1 P1-2
validator (because the proposed-status invariant is not violated),
but the old user-authored active row would be silently deactivated
in the same transaction. Net: no active row, agent's proposal not
yet promoted, W57 governance bypassed.

**Fix shipped.** Defence-in-depth, two-step:

- **`supersede_intent` / `supersede_target` no longer flip the old
  row when `new_record.source != "user_authored"`.** The new row is
  inserted with its `supersedes_*_id` link; the old row's status is
  unchanged
  (`src/health_agent_infra/core/intent/store.py:362-407`,
  `src/health_agent_infra/core/target/store.py:312-348`).
- **`commit_intent` / `commit_target` look up `supersedes_*_id`
  on the row being promoted** and atomically flip the parent row to
  `superseded` in the same transaction
  (`src/health_agent_infra/core/intent/store.py:298-348`,
  `src/health_agent_infra/core/target/store.py:275-318`). The
  user's commit is what authorises both the promotion AND the
  parent's deactivation.

User-authored supersede preserves the immediate-deactivation
behaviour (user is explicitly authorising both actions in one call).

**Regression tests added** (5 new tests):
- `test_agent_supersede_leaves_old_active_row_alone` (×2 intent +
  target) — agent-proposed supersede leaves the old row's
  `status='active'` and `superseded_by_intent_id=None` untouched.
- `test_commit_intent_with_supersedes_link_atomically_deactivates_parent`
  (×2 intent + target) — when user commits, both rows transition
  atomically.
- `test_user_authored_supersede_still_immediately_deactivates`
  (intent) — sanity check the user-authored fast path didn't
  regress.

**Why accepted without challenge.** The W57 invariant is "agent
cannot deactivate user state without explicit user commit." The
round-1 P1-2 fix enforced this on `add_intent` / `add_target`;
Codex correctly identified that `supersede_*` was an unenforced
back-door. Defence-in-depth now closes both insert paths *and* the
commit-time atomic deactivate.

### R2-3 — `hai config validate` accepts booleans as numeric thresholds — **ACCEPTED, FIXED**

**Codex finding.** Python's `isinstance(True, (int, float))` returns
True because `bool` is a subclass of `int`. The validator's type
check and the range helper both used naked `isinstance(v, (int,
float))`, so `[policy.review_summary]\nwindow_days = true` would
silently coerce to 1 and pass both checks.

**Fix shipped.**
- Type check: explicit `not isinstance(value, bool)` guard added
  to the numeric branch
  (`src/health_agent_infra/cli.py:3970-3984`).
- Range helper: new `_is_real_number(v)` local that excludes
  bools; every range check uses it instead of bare `isinstance`
  (`src/health_agent_infra/cli.py:3870-3920`).

**Regression tests added** (3 new tests):
- `test_config_validate_rejects_bool_for_numeric_window_days`
- `test_config_validate_rejects_bool_for_numeric_threshold`
- `test_config_validate_rejects_bool_for_mixed_bound`

Each verifies a TOML override of `true` / `false` for a numeric
key is surfaced as `type_mismatch` and blocks the validate exit
code.

### R2-4 — stale docstring on `_emit_data_quality_stats` — **ACCEPTED, FIXED**

**Codex finding.** Docstring still described the removed
lazy-projection behaviour ("the today block is constructed
on-the-fly from the snapshot"), which contradicted the actual
read-only-only implementation.

**Fix shipped.** Docstring rewritten to describe the read-only
contract explicitly + cite the round-1 P1-1 + round-2 R2-4 audit
chain as the authority for the contract
(`src/health_agent_infra/cli.py:5664-5673`).

---

## Maintainer findings beyond Codex's audit

None this round. Every finding Codex surfaced was correct and
actionable.

---

## Suite + verification deltas

| Metric | Round 2 ship | Round 3 ship |
|---|---:|---:|
| Tests passed | 2058 | 2066 |
| Tests skipped | 4 | 4 |
| Tests added (this round) | — | +8 |
| Drift validator | OK | OK |
| Capability contract regenerated | yes | yes |
| `hai --version` | hai 0.1.8 | hai 0.1.8 |

Round-3 tests focus narrowly on the four residuals: agent-proposed
supersede behaviour (5 tests), bool-as-number rejection (3 tests).
Every fix has at least one regression test that would have failed
against the round-2 implementation.

---

## What changed by file

```
src/health_agent_infra/cli.py
  - cmd_clean: stderr warning replaces bare except: pass (R2-1)
  - _emit_data_quality_stats: docstring rewrite (R2-4)
  - cmd_config_validate type check: bool guard (R2-3)
  - _review_summary_range_issues: _is_real_number helper (R2-3)

src/health_agent_infra/core/intent/store.py
  - supersede_intent: agent-proposed leaves old row alone (R2-2)
  - commit_intent: detects supersedes_intent_id, atomic
    deactivate-on-promotion (R2-2)

src/health_agent_infra/core/target/store.py
  - supersede_target: parallel R2-2 fix
  - commit_target: parallel R2-2 fix

safety/tests/test_intent_ledger.py
  - 3 new tests pinning agent-supersede deferral + atomic
    commit-time deactivate + user-authored fast-path preservation

safety/tests/test_target_ledger.py
  - 2 new tests pinning the same on targets

safety/tests/test_cli_config_validate_diff.py
  - 3 new bool-as-number rejection tests
```

---

## Re-verdict request

Round-2 verdict: SHIP_WITH_FIXES. With the four residuals fixed
and regression-tested, the maintainer requests a final round-3
audit confirming the fixes match the findings. If confirmed, ship
verdict on v0.1.8 should move to **SHIP**.

The W57 governance invariant ("agent cannot deactivate user state
without explicit user commit") is now enforced at *three*
boundaries: insert (validators reject agent-proposed-active),
supersede (defers agent-proposed deactivation), and commit
(performs the atomic deactivate-on-promotion). Defence-in-depth
across the full row lifecycle.
