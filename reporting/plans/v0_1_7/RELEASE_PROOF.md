# Release Proof Pack — v0.1.7

> **Purpose.** Single proof artifact captured immediately before a
> release tag. Replaces the scattered v0.1.4 release_qa pinning and
> stale `PUBLISH_CHECKLIST.md` references. Carry this template
> forward to v0.1.8+.
>
> **Codex r2 W36.** Asked for a short proof artifact with branch,
> version, full-suite result, wheel install result, capability
> contract regen, drift validator result, and known deferrals.

---

## Branch + commit

- **Branch.** `v0.1.4-release` (continuation; v0.1.6/v0.1.7 ship
  from this branch, will merge to `main` post-tag).
- **Base commit before release-prep commit.** `ff77aff`
  (`v0.1.5: sync release QA + handoff docs to v0.1.5 reality`).
- **Tag target.** The release-prep commit that contains this proof pack
  and the v0.1.6/v0.1.7 implementation files.
- **Working tree before upload.** `git status --short` should be clean
  after committing this proof pack. Ignored `dist/` may contain only
  the v0.1.7 wheel and sdist listed below.

## Version

- **`pyproject.toml`** declares `version = "0.1.7"`. _(Bump from
  0.1.6 immediately before tag.)_
- **`hai --version`** reports `hai 0.1.7` after `pip install -e .`
  + after `pipx install --force
  dist/health_agent_infra-0.1.7-py3-none-any.whl`.
- **Generated contract preamble** at
  `reporting/docs/agent_cli_contract.md` reports the same version.

## Test results

| Pass | Result |
|---|---|
| Full suite (`python3 -m pytest safety/tests/ -q`) | 1943 passed, 4 skipped, 0 failed |
| Targeted v0.1.7 workstream suite | All W21–W36 regression tests green |
| Drift validator (`python3 scripts/check_skill_cli_drift.py`) | `OK: no skill ↔ CLI drift detected.` |
| `git diff --check` | clean |

## Wheel install + smoke (v0.1.7 publish event)

_(Per Codex r2: stronger than current CI's `hai --version` /
`hai --help` only.)_

- `python -m build` — wheel + sdist produced under `dist/`.
- `python -m twine check dist/*` — passes for:
  `health_agent_infra-0.1.7-py3-none-any.whl` and
  `health_agent_infra-0.1.7.tar.gz`.
- `pipx install dist/health_agent_infra-0.1.7-py3-none-any.whl
  --force` — succeeds.
- `hai --version` — reports `hai 0.1.7`.
- `hai capabilities` — emits the manifest.
- `hai capabilities --json` — emits the same JSON (v0.1.7 alias).
- `hai eval run --domain recovery --json` — 3 passed, 0 failed.
- `hai doctor --json` — runs and reports `overall_status: ok` on the
  maintainer machine.
- Wheel listing has no state DB, SQLite, JSONL, `.env`, PEM, or key
  files. The only release-prep grep hit was the expected fixture name
  `strength_003_unmatched_token_caps.json`.

## Capabilities contract regeneration

- `python3 -m health_agent_infra.cli capabilities --markdown >
  reporting/docs/agent_cli_contract.md` succeeds. Use the module
  entrypoint here so stale PATH shims cannot regenerate the contract
  with an old package version.
- `safety/tests/test_capabilities.py::test_committed_contract_doc_matches_generated`
  passes.

## Known deferrals (carried to v0.1.8)

From v0.1.7 PLAN.md § 5b reconciliation table:

- **W29** (`cli.py` split) — deferred (Codex r2 verdict).
- **W30** (public Python API stability snapshot) — deferred (needs
  supported-API definition first).
- **W27** (property-based projector tests) — partially scoped; can
  ship in v0.1.7 if implementation budget allows, otherwise carries
  to v0.1.8.
- **W28** (`hai stats --funnel`) — depends on W21 telemetry. Telemetry
  ships in v0.1.7; the user-facing funnel surface may slip to v0.1.8
  if implementation budget runs out.

From v0.1.6 PLAN.md (still deferred):

- **W6** code-side nutrition supersede stderr warning (W34 supersedes
  this with a hard guard; the warning form is no longer needed).
- **W8** planned-session-type CLI helper (shipped as W33 in v0.1.7).
- **W14** deeper per-domain cold-start matrix (shipped as W24 in
  v0.1.7).
- **W16** synthesis-skill allowed-tools order test (shipped as W25
  in v0.1.7).

## Audit cycle artifacts

- v0.1.6: 4 docs at `reporting/plans/v0_1_6/` — codex_audit_prompt
  (3 rounds), codex responses (3 rounds), internal audit response,
  PLAN.md.
- v0.1.7: 4 docs at `reporting/plans/v0_1_7/` — codex_audit_prompt,
  codex_audit_response, REPORT.md, PLAN.md, this proof pack.

## What this proof DOESN'T cover

- Live PyPI upload. The maintainer runs `twine upload dist/*` after
  this proof is recorded; the proof timestamp predates the upload.
- Live agent end-to-end test (the manifest-only fixture test
  `test_daily_auto_manifest_fixture.py` is the closest stand-in;
  real Claude Code agent transcripts are deferred to the
  skill-harness work — see `safety/evals/skill_harness_blocker.md`).
- Performance characterisation. v0.1.7 is correctness-focused; perf
  characterisation is a v0.2 candidate.

## Sign-off

- **Maintainer (Dom Colligan):** _initial at tag time_
- **Codex round-3 verdict:** SHIP_WITH_FIXES → all must-fix items
  shipped (see `reporting/plans/v0_1_6/codex_implementation_review_response.md`
  + the v0.1.7 implementation log in `reporting/plans/v0_1_7/PLAN.md`
  § 6).
