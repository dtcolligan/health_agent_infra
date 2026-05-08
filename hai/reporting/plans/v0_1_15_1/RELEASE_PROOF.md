**Cycle tier (D15): hotfix.**

# v0.1.15.1 RELEASE PROOF - Linux keyring fall-through hardening

**Status.** shipped and published; PyPI current version verified as
`0.1.15.1`.
**Date.** 2026-05-03.
**Branch.** `main`.
**Scope source.** [`HOTFIX_SCOPE.md`](HOTFIX_SCOPE.md).

## 1. Workstream shipped

| W-id | Status | Detail |
|---|---|---|
| W-KEYRING-FALLTHROUGH | **closed-this-cycle** | Linux CI exposed `keyring.errors.NoKeyringError` when `keyring` imported successfully but no backend was registered. v0.1.15.1 adds `keyrings.alt` and probes the imported backend in `_default_backend()`, degrading to `_NullBackend` on `NoKeyringError` or another backend-read error. Non-credential commands now report missing credentials instead of crashing. |

**Closed-this-cycle: 1.** **Partial-closure: 0.** **Deferred: 0.**

## 2. Quality gates

| Gate | Target | Result |
|---|---|---|
| Pytest full suite | v0.1.15 baseline + hotfix regression | **2631 passed, 3 skipped, 0 failed** |
| Mypy | 0 errors | **Success: no issues found in 128 source files** |
| Bandit -ll | 0 medium/high | **0 Medium / 0 High** |
| Capabilities markdown | generated doc matches committed mirror | **clean diff** |
| Doc freshness | current doc-freshness assertions pass | **3 passed** |
| Whitespace | no trailing whitespace / conflict markers | **clean** |

## 3. Files changed

| File | Change |
|---|---|
| `src/health_agent_infra/core/pull/auth.py` | `_default_backend()` now catches runtime keyring backend failures and returns `_NullBackend` |
| `pyproject.toml` / `uv.lock` | version `0.1.15 -> 0.1.15.1`; add `keyrings.alt` runtime dependency |
| `verification/tests/test_pull_auth.py` | regression test for importable-keyring / no-backend `NoKeyringError` path |
| `README.md` | first-install command pins `0.1.15.1` and bypasses the PyPI CDN cache window |
| `reporting/docs/architecture.md` | nutrition target-aware path documented: W-A presence block, W-D arm-1 suppression, snapshot wiring, W-E skill consumption |
| `CHANGELOG.md`, `AUDIT.md`, `ROADMAP.md`, planning docs | v0.1.15.1 entry + cross-doc freshness updates |
| public v0.1.15/v0.1.16 planning artifacts | named foreign-user candidate personal identifier scrubbed; private memory remains the identity source |
| `reporting/docs/agent_cli_contract.md` | regenerated for `hai 0.1.15.1` version line |

## 4. Audit chain

D14 and external Codex IR skipped per AGENTS.md D15 hotfix latitude:
single bug class, no schema change, no governance change. The scope
doc records the maintainer-ratified Option B bundle: keyring fix + two
small doc items + public candidate-name scrub.

## 5. Out of scope

- No migration; schema head remains 25.
- No source changes outside `core/pull/auth.py`.
- No `garmin_status()` / `intervals_icu_status()` deeper audit; if a
  future backend fails after the initial probe, that broader status
  method hardening can land in v0.1.16 or later.
- No CI-green-before-publish workflow redesign; defer to v0.1.16+
  planning if the maintainer wants a process change.
- Push and PyPI upload were maintainer-owned.

## 6. Publish verification

Post-publish verification:

```bash
curl -s https://pypi.org/pypi/health-agent-infra/json | python3 -c "import json,sys; print('latest:', json.load(sys.stdin)['info']['version'])"
```

Expected and observed: `latest: 0.1.15.1`.
