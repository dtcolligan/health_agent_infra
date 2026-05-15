# v0.1.15.1 REPORT - Linux keyring fall-through hardening

**Tier (D15):** hotfix.
**Date:** 2026-05-03.
**Status:** shipped and published; PyPI current version verified as
`0.1.15.1`.

## 1. Why this hotfix existed

v0.1.15 published to PyPI, then Linux CI immediately failed with an
uncaught `NoKeyringError`. macOS was green because the native Keychain
backend is available. On Linux runners the `keyring` package imports,
but no backend is registered, so the first credential read raises
instead of returning "no credentials configured."

That made setup and status surfaces brittle on Linux: `hai init`,
`hai doctor`, `hai stats`, `hai pull`, and `hai daily` could crash
before reaching their normal no-credential or source-selection logic.

## 2. What changed

- Added `keyrings.alt` as a runtime dependency. It is the documented
  fallback backend when no desktop keyring is available.
- Hardened `_default_backend()` in `core/pull/auth.py`: after importing
  `keyring`, it imports `NoKeyringError`, probes `get_password()`, and
  returns `_NullBackend` if the backend is missing or broken.
- Added a regression test that fakes an importable `keyring` module
  whose first read raises `NoKeyringError`.
- Kept schema unchanged at migration head 25.

## 3. Scope bundle

The maintainer ratified Option B from `HOTFIX_SCOPE.md`: the hotfix
also carries two small doc fixes and the public candidate-name scrub.

- README first-install instructions now pin `health-agent-infra==0.1.15.1`
  and use the PyPI CDN-cache bypass command for the immediate
  post-publish window.
- `reporting/docs/architecture.md` now documents the v0.1.15 nutrition
  target-aware path: W-A presence signals, snapshot wiring, W-D arm-1
  `insufficient_data` suppression, and W-E skill consumption.
- Public repo artifacts no longer expose the foreign-user candidate's
  personal identifier. Private memory remains the operational source
  for the candidate identity.

## 4. Verification

- `uv run pytest verification/tests -q` -> 2631 passed, 3 skipped.
- `uvx mypy src/health_agent_infra` -> success.
- `uvx bandit -ll -r src/health_agent_infra` -> 0 medium/high.
- `uv run hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md`
  -> clean.
- `uv run pytest verification/tests/test_doc_freshness_assertions.py -q`
  -> 3 passed.
- `git diff --check` -> clean.

## 5. Deferrals

- Broader status-method catch coverage remains deferred. The backend
  probe closes the CI-visible failure; status-method wrapping is a
  broader resilience improvement.
- CI-green-before-publish workflow governance remains deferred to
  v0.1.16+ planning.

## 6. Ship sequence

1. Post-v0.1.15 internal-docs sweep committed separately.
2. v0.1.15.1 hotfix implemented and verified locally.
3. Maintainer pushed `main`.
4. Maintainer published the wheel/sdist from `dist/`.
5. Maintainer verified PyPI reports `0.1.15.1`.
