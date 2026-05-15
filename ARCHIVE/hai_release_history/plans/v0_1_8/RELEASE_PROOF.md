# Release Proof Pack — v0.1.8

> **Purpose.** Single proof artifact captured immediately before the
> v0.1.8 release tag. Mirror of the v0.1.7 template with v0.1.8
> content.

---

## Branch + commit

- **Branch.** `v0.1.4-release` (continuation; v0.1.7 + v0.1.8 ship from
  this branch).
- **Base commit before v0.1.8 implementation.** `1579357`
  (`v0.1.7: finalize release prep and v0.1.8 plan`).
- **Tag target.** The release-prep commit that contains this proof
  pack and the v0.1.8 implementation files (W44, W48, W38, W49, W50,
  W51, W40, W39, W46, W43, W41, W42, W45, W55).
- **Working tree before upload.** `git status --short` should be clean
  after committing this proof pack.

## Version

- **`pyproject.toml`** declares `version = "0.1.8"` (bumped from
  `0.1.7`).
- **`hai --version`** reports `hai 0.1.8` after `pip3 install
  --force-reinstall --no-deps .` and after `pipx install --force
  /Users/domcolligan/health_agent_infra`.
- **Generated contract preamble** at
  `reporting/docs/agent_cli_contract.md` regenerated post-bump.

## Test results

| Pass | Result |
|---|---|
| Full suite (`python3 -m pytest safety/tests/ -q`) | 2072 passed, 4 skipped, 0 failed |
| Drift validator (`python3 scripts/check_skill_cli_drift.py`) | `OK: no skill ↔ CLI drift detected.` |
| Targeted v0.1.8 workstream tests | All W37–W57 regression tests green (per `PLAN.md` § 6 implementation log) |
| Codex round-1 audit response | All 6 findings (P1-1, P1-2, P2-1, P2-2, P2-3, P3-1) accepted and fixed; see `codex_implementation_review_response_round2.md`. +20 regression tests pinning the invariants. |
| Codex round-2 audit response | All 4 residual findings (R2-1, R2-2, R2-3, R2-4) accepted and fixed; see `codex_implementation_review_response_round3.md`. +8 regression tests. W57 invariant now enforced at insert + supersede + commit boundaries. |
| Codex round-3 audit response | NEW_ISSUE_DISCOVERED_LATE (R3-1) accepted and fixed; see `codex_implementation_review_response_round4.md`. +6 regression tests. Bool-as-number bug class closed at runtime boundary plus validator boundary (defence-in-depth). |

### Test count growth across v0.1.8

| Workstream | Suite count after |
|---|---|
| Pre-v0.1.8 (v0.1.7 baseline) | 1943 |
| Fixture factories | 1954 |
| W57 non-goals | 1954 |
| W48 review summary | 1967 |
| W38 hai stats --outcomes | 1973 |
| W49 intent ledger MVP | 1986 |
| W50 target ledger MVP | 1999 |
| W51 data quality ledger | 2006 |
| W40 hai stats --baselines | 2009 |
| W39 hai config validate/diff | 2016 |
| W46 hai stats --funnel | 2018 |
| W43 hai daily --auto --explain | 2021 |
| W41 skill harness running | 2025 |
| W42 synthesis-skill scoring | 2032 |
| W45 deterministic replay/property | 2038 |
| W55 standards mapping doc | 2038 |
| Codex round-1 audit fixes (P1-P2-P3) | 2058 |
| Codex round-2 audit fixes (R2-1 to R2-4) | 2066 |
| Codex round-3 audit fix (R3-1) | 2072 |

Net new tests: **+129**.

## Migrations added

- `019_intent_item.sql` (W49) — intent ledger.
- `020_target.sql` (W50) — target ledger.
- `021_data_quality.sql` (W51) — data-quality ledger.

DB head: **21**. `test_state_store.py::test_schema_migrations_has_one_row_per_applied_migration` pins the explicit (version, filename) list end-to-end.

## Snapshot schema bump

- `snapshot.schema_version` bumped `state_snapshot.v1` →
  `state_snapshot.v2`. Additive transition: every v1 field is preserved
  unchanged. New v2 fields:
  - `snapshot.<domain>.review_summary` (W48)
  - `snapshot.intent` (W49, top-level)
  - `snapshot.target` (W50, top-level)
  - `snapshot.<domain>.data_quality` (W51)

## Wheel install + smoke (v0.1.8 publish event)

**Status: PUBLISHED 2026-04-26.**

### Build artifacts

```
$ python3 -m build
Successfully built health_agent_infra-0.1.8.tar.gz and
                   health_agent_infra-0.1.8-py3-none-any.whl

$ twine check dist/health_agent_infra-0.1.8*
Checking dist/health_agent_infra-0.1.8-py3-none-any.whl: PASSED
Checking dist/health_agent_infra-0.1.8.tar.gz:           PASSED

$ ls -la dist/health_agent_infra-0.1.8*
-rw-r--r--  domcolligan  staff  509578  health_agent_infra-0.1.8-py3-none-any.whl
-rw-r--r--  domcolligan  staff  422877  health_agent_infra-0.1.8.tar.gz
```

### PyPI upload

```
$ twine upload dist/health_agent_infra-0.1.8*
Uploading distributions to https://upload.pypi.org/legacy/
Uploading health_agent_infra-0.1.8-py3-none-any.whl
100% ━━━━━━━━━━━━━━━━━━━━━━━ 542.0/542.0 kB • 00:00 • 1.2 MB/s
Uploading health_agent_infra-0.1.8.tar.gz
100% ━━━━━━━━━━━━━━━━━━━━━━━ 455.3/455.3 kB • 00:00 • 123.4 MB/s

View at: https://pypi.org/project/health-agent-infra/0.1.8/
```

### Fresh-install verification (PyPI install, not local source)

```
$ pipx install --force --pip-args="--no-cache-dir --index-url \
  https://pypi.org/simple/" health-agent-infra==0.1.8 && hai --version
installed package health-agent-infra 0.1.8, installed using Python 3.14.3
hai 0.1.8

$ hai doctor --json | head -30
{
  "checks": {
    "auth_garmin":        { "credentials_source": "keyring", "status": "ok" },
    "auth_intervals_icu": { "credentials_source": "keyring", "status": "ok" },
    "config":             { "path": "...thresholds.toml",     "status": "ok" },
    "domains":            { "domains": [<all 6>],             "status": "ok" },
    "skills":             { "installed_count": 15, "packaged_count": 14,
                            "status": "ok" },
    ...
  }
}
```

All `hai doctor` checks reported `status: ok`. The fresh PyPI install
of 0.1.8 produced a working runtime against the operator's existing
Garmin + intervals.icu credentials and existing skills tree.

### Notes from the publish event

- First `pipx install --force health-agent-infra==0.1.8` (without
  `--no-cache-dir`) hit a PyPI-CDN propagation lag — pip's index was
  serving the pre-0.1.8 versions list for ~2 minutes after upload.
  The cache-bypass flag worked immediately. Worth flagging for the
  v0.1.9 publish: the standard `pipx install` may need a one-minute
  wait or the `--no-cache-dir --index-url` combo right after upload.
- Build + upload + verification ran clean on Python 3.14.3.
- The wheel is universal2 (macOS 10.15+); no platform-specific
  binaries.

## Skill `allowed-tools` updates

All six per-domain readiness skills' frontmatter extended:

- recovery-readiness, running-readiness, sleep-quality,
  strength-readiness, stress-regulation, nutrition-alignment

Added `Bash(hai intent list *)` (W49 maintainer refinement) and
`Bash(hai target list *)` (W50 maintainer refinement).

## Known deferrals

Per PLAN.md § 3:

- W29 `cli.py` split — deferred.
- W30 public Python API stability — deferred.
- W47 changelog per-commit test — cut (kept release-proof discipline).
- Weekly review / insight / artifact ledgers (W52–W56 in
  `codex_audit_response.md`) — deferred to v0.1.9 / v0.2 per the
  multi-release roadmap.
- Release automation — deferred until after this manual upload proves
  out.

## Codex audit + maintainer refinements applied

- Codex audit response: `codex_audit_response.md`.
- Maintainer refinements: `MAINTAINER_ANALYSIS.md` (six refinements,
  all folded into PLAN.md and shipped):
  1. Snapshot v2 transition (applied W48).
  2. Fixture-factory precondition (applied — 11 smoke tests).
  3. `[policy.review_summary]` thresholds block (applied W48).
  4. W49/W50 skill `allowed-tools` extensions (applied).
  5. W51 cold-start consistency test (applied —
     `test_data_quality_cold_start_consistency.py`).
  6. W55 standards-mapping doc (applied).

## Acceptance criteria (PLAN.md § 5)

- [x] Outcome summaries computed by code, exposed to snapshots/stats
      without skill-side arithmetic (W48).
- [x] `hai stats --outcomes` and `hai stats --funnel` emit stable JSON
      and markdown/text from seeded fixtures (W38, W46).
- [x] Intent + target MVPs have migrations, CLI, archive/supersession,
      snapshot integration, capability-manifest entries, tests (W49,
      W50).
- [x] Baseline stats distinguish observed vs threshold vs band vs
      coverage vs missingness vs cold-start (W40).
- [x] Config validate/diff doesn't claim threshold loading is new and
      doesn't allow outcomes to write thresholds (W39).
- [x] `hai daily --auto --explain` is additive only; ordinary daily
      outputs unchanged (W43).
- [x] Skill-harness replay covers recovery + running; synthesis-skill
      scoring has fixtures + failure localisation (W41, W42).
- [x] Replay/property tests cover projector, correction, late-arrival,
      intent, target, review-summary semantics (W45).
- [x] No v0.1.8 path silently changes thresholds, classifiers, policy,
      X-rules, confidence, intent, or targets based on outcomes.
- [x] All P0/P1 workstreams have regression tests + capability-manifest
      updates + release-proof entries.
- [x] W51 cold-start consistency test green for all six domains.
- [x] `snapshot.schema_version` is `"v2"`.
- [x] W55 standards mapping doc exists.

The remaining acceptance item (W44 — fresh PyPI install proof for
v0.1.8) is operator-gated; capture once `twine upload` runs.
