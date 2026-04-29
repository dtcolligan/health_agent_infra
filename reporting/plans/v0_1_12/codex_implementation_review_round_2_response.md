# Codex Implementation Review — v0.1.12

**Verdict:** SHIP_WITH_FIXES
**Round:** 2

## Verification summary

- Tree state: `cycle/v0.1.12`, working tree clean at review start. Local
  `git rev-list --count main..cycle/v0.1.12` reports **13** commits, not
  the 12 stated in the round-2 handoff; the extra visible commit is
  `233bd5d chore: reorganise reporting/plans/ for human readability`.
- Test surface: `uv run pytest verification/tests -q` passed:
  **2382 passed, 2 skipped**. Focused W-FBC/W-Vb tests passed:
  **38 passed** for `test_cli_daily.py`, `test_demo_fixtures_packaging.py`,
  `test_demo_session_lifecycle.py`, and `test_demo_isolation_surfaces.py`.
- Warning gates: narrow ship gate
  `uv run pytest verification/tests -W error::pytest.PytestUnraisableExceptionWarning -q`
  passed (**2382 passed, 2 skipped**). Broader audit gate
  `uv run pytest verification/tests -W error::Warning -q` failed as expected:
  **47 failed, 2334 passed, 2 skipped, 1 error**, with sampled failures all
  sqlite3 connection-lifecycle `ResourceWarning` / unraisable warnings.
- Ship gates: `uvx mypy src/health_agent_infra` returned 0 errors;
  `uvx bandit -ll -r src/health_agent_infra` returned 46 Low, 0 Medium,
  0 High; capabilities markdown was byte-stable across two runs and matched
  `reporting/docs/agent_cli_contract.md`; wheel build succeeded and unpacked
  `health_agent_infra/demo/fixtures/p1_dom_baseline.json`.
- Provenance spot-checks: W-PRIV helper citations are correct
  (`core/pull/auth.py:171` and `:261`); `STRENGTH_STATUS_VALUES` is a typed
  `tuple[str, ...]` with the five documented values; CP4 MCP URLs are
  reachable (the security-best-practices URL redirects, but is not a 404).

## Findings

### F-IR-R2-01. W-FBC recovery-prototype claims remain in release-facing artifacts

**Q-bucket:** Q2, Q3, Q10, Q13, Q15
**Severity:** scope-mismatch
**Reference:** e5c8b96 / `reporting/plans/v0_1_12/PLAN.md:94`,
`reporting/plans/v0_1_12/PLAN.md:113`,
`reporting/plans/v0_1_12/PLAN.md:191`,
`reporting/plans/v0_1_12/PLAN.md:851`,
`reporting/docs/supersede_domain_coverage.md:3`,
`reporting/plans/v0_1_12/RELEASE_PROOF.md:211`,
`reporting/plans/v0_1_12/REPORT.md:80`,
`reporting/plans/v0_1_12/REPORT.md:119`,
`ROADMAP.md:23`,
`reporting/plans/tactical_plan_v0_1_x.md:271`

**Argument:** Round 1's blocking finding was that W-FBC claimed a recovery
prototype that did not exist. Commit e5c8b96 correctly realigned the core
implementation surface and some central release rows: `cli.py:8125-8133`
now says `--re-propose-all` is report-surface-only, `PLAN.md §2.8` now
says no synthesis-side enforcement landed, and `RELEASE_PROOF.md §1` now
marks W-FBC as partial-closure.

But the artifact set is still internally inconsistent. Multiple active,
release-facing summaries still say v0.1.12 shipped "design + recovery
prototype" or equivalent:

- PLAN catalogue says W-FBC is "design + recovery prototype" and still lists
  `core/synthesis.py` plus a missing `verification/tests/test_supersede_domain_coverage.py`.
- PLAN out-of-scope and carry-over rows still say v0.1.12 delivers "design
  + recovery prototype only" / "design doc + recovery prototype + flag".
- PLAN risks still say W-FBC shipped a one-domain prototype.
- `supersede_domain_coverage.md` status line says "design + recovery
  prototype + override flag", while the body correctly says no prototype.
- RELEASE_PROOF §5 and REPORT §§4/6 still say v0.1.12 delivers a recovery
  prototype.
- ROADMAP and tactical plan §3.1 repeat the recovery-prototype claim.

This means the round-1 recommended response ("revise artifacts to state
design doc + flag accepted + report-surface field only, with all runtime
enforcement deferred") is only partially applied.

**Recommended response:** fix-and-reland artifacts only. Replace every
current/release-facing W-FBC summary with the actual shipped scope:
design doc + `--re-propose-all` parser/capabilities/report-surface field
only; recovery prototype and multi-domain enforcement deferred to v0.1.13
W-FBC-2. Remove `core/synthesis.py` and the absent supersede-domain test
from v0.1.12 W-FBC primary-file/test claims unless explicitly described as
deferred.

### F-IR-R2-02. W-Vb and W-N-broader deferral propagation is still incomplete in summary docs

**Q-bucket:** Q2, Q3, Q4, Q6, Q15
**Severity:** provenance-gap
**Reference:** e5c8b96 / `ROADMAP.md:20`,
`ROADMAP.md:21`, `reporting/plans/tactical_plan_v0_1_x.md:266`,
`reporting/plans/tactical_plan_v0_1_x.md:268`,
`reporting/plans/tactical_plan_v0_1_x.md:279`,
`reporting/plans/v0_1_12/PLAN.md:91`,
`reporting/plans/v0_1_12/PLAN.md:186`,
`reporting/plans/v0_1_12/PLAN.md:188`,
`reporting/plans/v0_1_12/PLAN.md:844`

**Argument:** The central W-Vb implementation and W-N fork are sound:
`apply_fixture()` returns the skeleton/deferred marker, the wheel ships
`p1_dom_baseline.json`, `PLAN.md §2.5` honestly records the W-N fork, and
`RELEASE_PROOF.md §1` names W-Vb partial-closure and W-N fork-deferral.

However the public/tactical summaries still carry the old story:

- ROADMAP "Now" says v0.1.12 includes "demo persona-replay" and the
  broader `-W error::Warning` gate, without naming the partial/fork outcome.
- Tactical plan §3.1 still says W-Vb is "persona-replay + fixture-packaging"
  and W-N is "49 + 1 error -> <= 80 branch -> full broader gate ships".
- Tactical plan §3.2 says residuals are named only for F-B-04, omitting the
  W-Vb and W-N inherited residuals now added to v0.1.13 §4.
- PLAN catalogue/carry-over summary still labels W-Vb and W-N as "in-cycle",
  and the PLAN risks section still says W-Vb changes the demo contract to
  "reaches synthesis" in v0.1.12.

These stale summaries directly contradict the fixed RELEASE_PROOF and the
actual code behavior. They are not source bugs, but they are the same class
of artifact-truth failure the round-1 fix was meant to close.

**Recommended response:** fix-and-reland artifacts only. Update ROADMAP,
tactical plan §3.1/§3.2, and PLAN summary/risk rows so W-Vb is consistently
"packaged skeleton fixture loader; end-to-end persona replay deferred to
v0.1.13 W-Vb" and W-N-broader is consistently "narrow gate ships; broader
`-W error::Warning` fix fork-deferred to v0.1.13 W-N-broader".

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-CP | pass | CP1-CP3 now document the origin-parenthetical convention; CP6 application remains deferred; CP4 URLs reachable. |
| W-AC | fixes | Freshness test scope is now honestly described, but active public docs still contain stale W-FBC/W-Vb/W-N claims. |
| W-CARRY | pass | `CARRY_OVER.md §1` now names W-Vb partial-closure, W-N fork-deferral, and W-FBC report-surface-only partial closure. |
| W-Vb | fixes (partial) | Code, tests, and wheel packaging pass; summary artifacts still claim persona replay/reaches-synthesis in places. |
| W-H2 | pass | mypy is clean; no new broad `# type: ignore` expansion observed. |
| W-N-broader | fixes (fork-deferred) | Fork rationale and gates are technically sound; summary artifacts still say full broader gate ships in places. |
| W-D13-SYM | pass | Coercer routing and AST contract surface remain green. |
| W-PRIV | pass | `hai auth remove` routes to the cited keyring clear helpers; env creds are not touched. |
| W-FCC | pass | Constant, capabilities enum surface, and verbose flag surface are present and tested. |
| W-FBC | fixes (partial) | Runtime/report-surface implementation is honest; artifact realignment is still incomplete. |

## Open questions for maintainer

1. The branch is 13 commits ahead of local `main`, not 12. Is
   `233bd5d chore: reorganise reporting/plans/ for human readability`
   intentionally part of the v0.1.12 release branch, or should the review
   base be updated?
2. Should the round-2 patch be a narrow artifact-only commit? I do not see
   evidence that source code needs to change; the blocker is that public and
   release-proof artifacts still contradict the shipped implementation.
