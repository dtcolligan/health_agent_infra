# Release Proof Pack - v0.1.9

> **Purpose.** Proof artifact captured before the v0.1.9 release commit.
> v0.1.9 is a hardening release, not a feature release.

---

## Branch + commit

- **Branch.** `main`.
- **Base commit before v0.1.9 implementation.** `04a3d31`
  (`docs: sharpen public project presentation`).
- **Tag target.** The release-prep commit containing B1-B8 hardening,
  the Codex implementation-review fixes, this proof pack, and the
  v0.1.9 version bump.
- **Working tree before upload.** Should be clean after committing the
  release-prep changes.

## Version

- **`pyproject.toml`** declares `version = "0.1.9"`.
- **`hai --version`** reports `hai 0.1.9`.
- **Generated contract preamble** at
  `reporting/docs/agent_cli_contract.md` says
  `52 commands; hai 0.1.9; schema agent_cli_contract.v1`.

## Scope

Shipped:

- B1 - W57 runtime gate closure for intent/target commit/archive.
- B2 - skill overlay fail-loud for out-of-lane and malformed overlay
  fields.
- B3 - validator shape hardening and shared banned-token surface walker.
- B4 - direct `hai synthesize` expected-domain completeness and snapshot
  classified-state parity.
- B5 - pull/clean provenance, deterministic evidence hash, fail-closed
  projection, and intervals.icu partial telemetry.
- B6 - safety skill prose refresh for nutrition v1 and X-rule block tiers.
- B7 - v0.1.9 cycle plan.
- B8 - Phase B registry coverage, dead-code cleanup, README daily-loop
  wording, and data-quality coverage-band consistency.

Explicitly not shipped:

- W52 `hai review weekly`.
- W53 insight proposal ledger.
- W58 LLM-judge factuality gate.
- Global threshold-runtime type hardening outside the review-summary path.

## Test results

| Pass | Result |
|---|---|
| Focused Codex-fix regressions | 63 passed |
| Full suite (`uv run pytest verification/tests -q`) | 2133 passed, 2 skipped |
| Drift validator (`uv run python scripts/check_skill_cli_drift.py`) | `OK: no skill ↔ CLI drift detected.` |
| Whitespace check (`git diff --check`) | clean |
| Version smoke (`uv run hai --version`) | `hai 0.1.9` |

### Test count delta

- v0.1.8 release proof: 2072 passed, 4 skipped.
- v0.1.9 hardening implementation review before Codex fixes: 2127 passed,
  2 skipped.
- v0.1.9 release proof after Codex fixes: 2133 passed, 2 skipped.
- Net v0.1.9 growth from v0.1.8: +61 passing tests.
- Net growth from the pre-review v0.1.9 implementation: +6 passing tests.

## Build artifacts

```
$ python3 -m build --wheel --sdist
Successfully built health_agent_infra-0.1.9-py3-none-any.whl and
health_agent_infra-0.1.9.tar.gz

$ python3 -m twine check dist/health_agent_infra-0.1.9*
Checking dist/health_agent_infra-0.1.9-py3-none-any.whl: PASSED
Checking dist/health_agent_infra-0.1.9.tar.gz:           PASSED

$ ls -lh dist/health_agent_infra-0.1.9*
-rw-r--r--  health_agent_infra-0.1.9-py3-none-any.whl  501K
-rw-r--r--  health_agent_infra-0.1.9.tar.gz            412K
```

Build emitted setuptools deprecation warnings for the existing
`project.license` table and license classifier. Those are warnings only;
they should be cleaned up before the 2027 setuptools cutoff but do not block
v0.1.9.

## Acceptance criteria

- [x] All B1-B6 tests are green.
- [x] Capabilities manifest and W57 `agent_safe` posture match runtime
      behavior for intent/target commit/archive.
- [x] Direct `hai synthesize` and `hai daily` parity is covered by the
      Phase A/snapshot tests.
- [x] `hai clean` on identical evidence produces one raw provenance row.
- [x] Codex implementation review returned `SHIP_WITH_FIXES`; all three
      findings accepted and fixed.
- [x] Release proof exists before commit/tag/publish.

## Known deferrals

- W52, W53, W58 remain post-hardening roadmap work.
- Global threshold-runtime type hardening remains in
  `reporting/plans/v0_1_9/BACKLOG.md`.
- The pytest unraisable warning cleanup item in BACKLOG did not reproduce in
  this release proof run: full suite completed with 2 skips and no warnings
  summary.
- `cli.py` split and RAW_DAILY_ROW_COLUMNS coupling remain deferred per
  AGENTS.md / PLAN.md.

## Publish checklist

After the release commit:

1. `git tag v0.1.9`
2. `git push origin main`
3. `git push origin v0.1.9`
4. `python3 -m twine upload dist/health_agent_infra-0.1.9*`
5. Fresh install smoke after PyPI propagation:
   `pipx install --force --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" health-agent-infra==0.1.9 && hai --version`
