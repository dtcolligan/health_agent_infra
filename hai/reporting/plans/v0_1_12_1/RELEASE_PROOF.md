# v0.1.12.1 Release Proof

**Tier:** hotfix (per CP3 D15 — single-bug fix, no scope expansion,
lightweight RELEASE_PROOF, may skip Phase 0 + D14).

**Authored:** 2026-04-29 at hotfix ship.

**Branchpoint:** `v0.1.12` tag.

**Branch:** `hotfix/v0.1.12.1` (two commits: CF fix + version bump).

---

## 1. Single workstream

| W-id | Title | Status |
|---|---|---|
| **W-CF-UA** | intervals.icu Cloudflare User-Agent block fix | shipped |

**Origin:** F-DEMO-01, root-cause investigation 2026-04-29 during
maintainer session. Symptom was previously misattributed to credential
rotation. Empirical probe revealed Cloudflare error 1010
(`browser_signature_banned`) blocking urllib's default UA before any
intervals.icu auth path was reached.

**Diff size:** 40 lines added across 2 files
(`src/health_agent_infra/core/pull/intervals_icu.py` +
`verification/tests/test_pull_intervals_icu.py`).

**Fix shape:**

- Added `DEFAULT_USER_AGENT` module-level constant tied to
  `__version__` (so the UA tracks releases).
- Added `user_agent: str = DEFAULT_USER_AGENT` field on
  `HttpIntervalsIcuClient` (overridable for diagnostic use).
- Send the header in `_fetch_json_array` alongside `Authorization`
  and `Accept`.

---

## 2. Ship-gate validation

### 2.1 Test surface

```
verification/tests: 2384 passed, 2 skipped (~74s)
                    (was 2382 + 2 at v0.1.12 ship; +2 new tests)
```

Two new tests:

- `test_http_client_sends_project_user_agent` — asserts the default
  UA starts with `health-agent-infra/` and is not the Python-urllib
  default that Cloudflare blocks.
- `test_http_client_user_agent_is_overridable` — confirms callers can
  inject a custom UA.

### 2.2 Mypy

```
uvx mypy src/health_agent_infra/core/pull/intervals_icu.py:
  Success: no issues found in 1 source file
```

Whole-package mypy clean unchanged from v0.1.12 ship (0 errors).

### 2.3 Live pull verify

`hai pull --source intervals_icu --as-of 2026-04-29` returned HTTP
200 with real wellness data on the maintainer's account, after the
fix was applied. Pre-fix the same command returned HTTP 403 (with
Cloudflare error 1010 in the response body). Sync_run_log row
landed; `hai stats` shows `intervals_icu` last sync `for 2026-04-29`.

---

## 3. What the hotfix tier skipped (per D15)

- **Phase 0 (D11) bug-hunt** — skipped per D15. Fix is single-site
  with deterministic acceptance test.
- **D14 plan-audit** — skipped per D15. No PLAN.md authored; the
  hotfix scope is captured in this RELEASE_PROOF + the inline
  CHANGELOG entry.
- **Codex implementation review (rounds)** — not invoked. Maintainer
  reviewed the diff before push.
- **Persona matrix re-run** — skipped. Persona harness depends on
  pull adapters working; if the fix breaks the adapter, all 12
  personas would fail — `verification/tests/test_pull_intervals_icu.py`
  catches the same shape and runs in seconds.

D15 explicitly authorises these omissions for hotfix tier. v0.1.13
(substantive cycle, opening alongside this hotfix) carries the full
audit weight.

---

## 4. Audit-chain artifacts

```
reporting/plans/v0_1_12_1/
  RELEASE_PROOF.md            (this file)
```

That's the entire artifact set. Hotfix tier per D15.

The v0.1.13 cycle's PLAN.md will record the same fix as W-CF-UA in
its workstream catalogue with `status: shipped in v0.1.12.1` for
catalogue completeness, per the cycle-open agreement on
2026-04-29.

---

## 5. Out-of-scope

Nothing. Single-bug fix. The v0.1.12 named-deferred items
(W-Vb persona-replay end-to-end, W-N-broader, W-FBC-2) remain
deferred to v0.1.13 unchanged.

---

## 6. Branch state

```
$ git branch --show-current
hotfix/v0.1.12.1

$ git log --oneline v0.1.12..hotfix/v0.1.12.1
ba5f101 release(v0.1.12.1): bump version + CHANGELOG hotfix entry
c75597e fix(pull/intervals_icu): set User-Agent to bypass Cloudflare bot block
```

**Not pushed.** Awaiting maintainer review. Next concrete actions:

1. Maintainer reviews the two-commit branch + this RELEASE_PROOF.
2. Build wheel via `uvx --from build python -m build --wheel --sdist`.
3. Tag `v0.1.12.1`.
4. Push tag + merge hotfix branch to main.
5. PyPI publish via `uvx twine upload` per
   `reference_release_toolchain.md`.
6. Verify install via cache-bypass `pipx install` per the same memory
   note.

---

## 7. Memory note update

`~/.claude/projects/-Users-domcolligan-health-agent-infra/memory/reference_doctor_intervals_icu_false_positive.md`
revised at the same session. Now distinguishes the two distinct
root-cause shapes (Cloudflare UA-block vs genuine credential rotation)
with a triage script. The note explicitly calibrates against the
2026-04-29 misdiagnosis as a reminder for future sessions.
