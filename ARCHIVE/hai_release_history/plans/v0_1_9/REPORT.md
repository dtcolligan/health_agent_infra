# v0.1.9 Report - hardening the v0.1.8 surface

> **Date.** 2026-04-26
> **Release type.** Hardening release, not a feature release.
> **Base commit.** `04a3d31` (`docs: sharpen public project presentation`)

---

## Summary

v0.1.9 closes the highest-risk findings from the parallel 2026-04-26
Codex and Claude reviews of the v0.1.8-shipped surface. The release
tightens governance gates, synthesis safety closure, validator shape
checks, direct-synthesis parity, and pull/clean provenance. It does not
add product features.

The final Codex implementation review found three accepted issues in the
maintainer's first B1-B8 pass:

1. `hai daily` recorded partial adapter pulls as `sync_run_log.status='ok'`.
2. Skill-overlay drafts rejected out-of-lane keys but still ignored
   malformed in-lane fields.
3. Recommendation/proposal validation accepted `policy_decisions[].note =
   None`.

All three were fixed before this report and covered by focused regression
tests.

## Shipped Work

- **B1 - W57 closure.** Intent/target commit/archive handlers are
  runtime-gated by `--confirm` or interactive stdin, and all four are
  marked `agent_safe=False`.
- **B2 - skill overlay fail-loud.** Skill overlays can only modify prose
  surfaces. Out-of-lane keys, unknown recommendation ids, malformed
  rationale/uncertainty lists, and malformed follow-up review questions
  raise `skill_overlay_out_of_lane` before the transaction opens.
- **B3 - validator hardening.** Proposal and recommendation validators
  share banned-token surface walking and now enforce strict text-shape
  contracts for rationale, uncertainty, policy decisions, and review
  questions.
- **B4 - direct synthesize parity.** Direct `hai synthesize` requires the
  expected six-domain proposal set by default and snapshots always carry
  classified state plus policy results.
- **B5 - pull/clean provenance.** Daily pull writes `sync_run_log`,
  projection failures fail closed, clean evidence ids are deterministic,
  and intervals.icu activity failures set partial telemetry.
- **B6 - safety skill prose.** Safety guidance now matches nutrition v1
  macro-action scope and X-rule block-tier escalation semantics.
- **B7 - plan.** `PLAN.md` records the merged review scope and explicit
  deferrals.
- **B8 - hygiene.** Phase B registry coverage is tested, dead code was
  removed, README daily-loop wording was tightened, and data-quality
  coverage-band behavior is pinned.

## Not Shipped

- W52 `hai review weekly`.
- W53 insight proposal ledger.
- W58 LLM-judge factuality gate.
- Global threshold-runtime type hardening outside the already-shipped
  review-summary bool-as-int path.
- `cli.py` split or frozen capabilities schema.
- New nutrition scope beyond macros-only v1.

## Evidence

| Check | Result |
|---|---|
| Focused Codex-fix regressions | 63 passed |
| Full suite | 2133 passed, 2 skipped |
| Drift validator | `OK: no skill ↔ CLI drift detected.` |
| Version smoke | `hai 0.1.9` |
| Build | `health_agent_infra-0.1.9` wheel + sdist built |
| Twine check | wheel and sdist passed |

Build artifacts:

- `dist/health_agent_infra-0.1.9-py3-none-any.whl`
- `dist/health_agent_infra-0.1.9.tar.gz`

## Release Stance

Verdict: **SHIP**.

The working tree is ready for a release commit, tag, push, and PyPI
upload after maintainer confirmation.
