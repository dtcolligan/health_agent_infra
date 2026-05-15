# Codex Implementation Review — v0.1.12

**Verdict:** SHIP_WITH_NOTES
**Round:** 3

## Verification summary

- Tree state: `cycle/v0.1.12`, working tree clean at review start,
  `main..cycle/v0.1.12` = **14 commits**. The 13-vs-12 question from
  round 2 is resolved: `233bd5d` is intentional v0.1.12 substrate.
- Test surface: `uv run pytest verification/tests -q` passed:
  **2382 passed, 2 skipped**. Focused W-FBC/W-Vb checks passed:
  **38 passed** for `test_cli_daily.py`, `test_demo_fixtures_packaging.py`,
  `test_demo_session_lifecycle.py`, and `test_demo_isolation_surfaces.py`.
- Warning gates: narrow ship gate
  `uv run pytest verification/tests -W error::pytest.PytestUnraisableExceptionWarning -q`
  passed (**2382 passed, 2 skipped**). Broader audit gate
  `uv run pytest verification/tests -W error::Warning -q` failed in the
  expected inherited shape: **47 failed, 2334 passed, 2 skipped, 1 error**,
  with sqlite connection-lifecycle `ResourceWarning` / unraisable warnings.
- Ship gates: `uvx mypy src/health_agent_infra` returned 0 errors;
  `uvx bandit -ll -r src/health_agent_infra` returned 46 Low, 0 Medium,
  0 High; capabilities markdown was byte-stable across two runs and matched
  `reporting/docs/agent_cli_contract.md`.
- Round-2 sweep: commit `5796303` realigns the blocking stale W-FBC,
  W-Vb, and W-N summary surfaces in ROADMAP, tactical plan, PLAN §1.1 /
  §1.2 / §1.3 / §4, RELEASE_PROOF §5, REPORT §4/§6, the supersede design
  doc, audit findings, and CHANGELOG. No source-code behavior changed.
- CP4 URL check: both cited MCP URLs are reachable. The security-best-
  practices URL redirects to the current docs path, but is not a 404.

## Findings

### F-IR-R3-N1. PLAN §2.2 mini carry-over table still uses shorthand for W-Vb and W-N

**Q-bucket:** Q3, Q6, Q15
**Severity:** nit
**Reference:** `reporting/plans/v0_1_12/PLAN.md:194`,
`reporting/plans/v0_1_12/PLAN.md:196`

**Argument:** The authoritative carry-over register is correct:
`CARRY_OVER.md §1` marks W-Vb as partial-closure and W-N broader gate as
fork-deferred. The active public/release summaries are now also correct
after `5796303`. One compact PLAN §2.2 summary table still says
`W-Vb | in-cycle (W-Vb here)` and `W-N broader gate | in-cycle
(W-N-broader here)`. In context, this can be read as "the workstream
exists in this cycle"; it is not the source of truth and is contradicted
by the immediately broader PLAN, ROADMAP, RELEASE_PROOF, tactical plan,
and CARRY_OVER surfaces. Still, it is the same shorthand class that caused
rounds 1-2 drift.

**Recommended response:** accept-as-known. This does not block merge or
publish. When the v0.1.13 checklist extension lands, include PLAN §2.2
mini disposition rows in the partial-closure summary-surface sweep. If a
doc-only touch happens before merge, the ideal wording is
`partial-closure -> v0.1.13 W-Vb` and `fork-deferred -> v0.1.13
W-N-broader`.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-CP | pass | CP1-CP5 applied; CP6 correctly deferred. CP4 links reachable. |
| W-AC | pass with note | Round-2 summary-surface sweep is now coherent; carry the new summary-surface checklist extension to v0.1.13. |
| W-CARRY | pass | `CARRY_OVER.md` accurately records W-Vb partial-closure, W-N fork-deferral, W-FBC partial-closure, and all reconciliation items. |
| W-Vb | pass (partial) | Wheel/package path and skeleton-loader marker verified by tests; full persona replay honestly deferred. |
| W-H2 | pass | mypy is clean at 0 errors. |
| W-N-broader | pass (fork-deferred) | Narrow gate passes; broader gate fails in the expected inherited sqlite leak shape; v0.1.13 destination is documented. |
| W-D13-SYM | pass | Coercer routing and contract test remain green. |
| W-PRIV | pass | Auth removal surface, idempotency, env-var safety, and capabilities row remain intact. |
| W-FCC | pass | Strength enum constant, capabilities enum surface, and verbose mode remain intact. |
| W-FBC | pass (partial) | Artifacts now consistently say report-surface-only at v0.1.12; recovery prototype + multi-domain enforcement deferred to W-FBC-2. |

## Open questions for maintainer

None blocking. The release can merge and publish with the note above carried
to v0.1.13.
