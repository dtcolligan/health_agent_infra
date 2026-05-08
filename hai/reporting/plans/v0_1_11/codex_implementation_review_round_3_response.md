# Codex Implementation Review — v0.1.11 cycle/v0.1.11

**Verdict:** SHIP_WITH_NOTES

**Round:** 3

## Findings

### F-IR3-01. Boundary-stop demo narrowing still leaves stale PLAN/demo-flow assertions

**Q-bucket:** Q4 / Q6
**Severity:** important
**Reference:** `reporting/plans/v0_1_11/PLAN.md:1220`, `reporting/plans/v0_1_11/PLAN.md:1223`, `reporting/plans/v0_1_11/PLAN.md:1226`, `reporting/docs/demo_flow.md:14`, `reporting/docs/demo_flow.md:110`, `reporting/docs/demo_flow.md:189`, `reporting/docs/demo_flow.md:242`, `reporting/plans/v0_1_11/RELEASE_PROOF.md:175`, `verification/tests/test_demo_isolation_surfaces.py:283`
**Argument:** The blocker-class W-E issue from round 2 is fixed: `_compute_state_fingerprint` now hashes accepted-state content columns while excluding the projection/correction/provenance churn columns, and the new no-op regression test covers refreshed timestamps with unchanged content. PLAN § 2.16, W-W implementation, and the W-W tests are also aligned on the narrowed SQLite-only/no-history-fail-closed contract. The remaining mismatch is in the demo gate documentation. RELEASE_PROOF § 2.7 now correctly describes the v0.1.11 runnable path as a boundary-stop demo (`hai daily` returns `awaiting_proposals`, and `hai today` has no plan), but PLAN § 3 still says isolation-replay mode's manual seed populates enough state for `hai today` to render and that `hai doctor --deep` is part of that isolation replay (`PLAN.md:1220-1229`). The canonical demo doc also still introduces § B as populating enough state for `hai today` to render (`demo_flow.md:14-17`, `demo_flow.md:110-113`) even though its later section says the canonical path stops at `awaiting_proposals`. More concretely, § B still says path (a) can demonstrate W-F's fresh-day `--supersede` USER_INPUT refusal (`demo_flow.md:189-191`, `demo_flow.md:242-251`), while the updated subprocess test acknowledges the opposite: without proposals, `daily --supersede` short-circuits before synthesis/W-F and the test only asserts it does not crash (`test_demo_isolation_surfaces.py:283-294`). RELEASE_PROOF's transcript is also a subset of the test sequence: it stops after `daily` and `demo end`, while the permanent subprocess test additionally runs `today` and `daily --supersede`.
**Recommended response:** Before merge, finish propagating the boundary-stop narrowing through PLAN § 3 and `reporting/docs/demo_flow.md`. The isolation-replay bullets should say the manual seed reaches `awaiting_proposals`, `hai today` shows the no-plan boundary signal, and fresh-date `daily --supersede` does not demonstrate W-F unless proposals/canonical state are seeded first. Either remove the W-F demo claim from § B or add an explicit proposal-seeding path before it. Update RELEASE_PROOF's transcript or surrounding prose so it is clear whether the transcript is the complete subprocess replay or an illustrative subset. This is not a blocker because W-E/W-F/W-Va are independently tested and the real-state pollution guard remains covered, but the ship-gate narrative should not contradict the runnable branch behaviour.

## Verification

- `uv run pytest verification/tests/test_daily_supersede_on_state_change.py verification/tests/test_intake_gaps_from_snapshot.py verification/tests/test_demo_isolation_surfaces.py -q` — 24 passed.

## Notes

No blocker-class findings remain. The round-2 W-E regression is closed under inspection and targeted tests: same accepted-state content with refreshed timestamps is a true no-op, while changed nutrition content still auto-supersedes. W-W's narrowed contract now agrees across PLAN § 2.16, implementation, and tests.
