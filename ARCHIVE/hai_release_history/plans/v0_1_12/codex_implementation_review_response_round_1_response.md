# Maintainer Response — Codex Implementation Review round 1

**Author.** Claude (delegated by maintainer).
**Date.** 2026-04-29.
**Codex verdict.** `SHIP_WITH_FIXES`, round 1
(`reporting/plans/v0_1_12/codex_implementation_review_response.md`).

**This response.** Accepts 5 of 5 findings. Resolves 3 of 3 open
questions. Fixes applied this commit (artifact corrections + CLI
help-text alignment); no source-code feature additions. Round 2
audit can proceed against the corrected tree.

---

## Summary

Codex was right on every count. The cycle shipped less than PLAN
promised in two places (W-FBC recovery prototype, W-Vb persona-
replay) but the artifact set wasn't honest about it — the PLAN +
CARRY_OVER + tactical plan + CLI help-text + design doc kept the
ambitious framing while RELEASE_PROOF correctly named the partial
closures. That's the exact provenance-gap pattern REPORT §6 said
the cycle was trying to avoid, and Codex caught it.

The fix is to align the artifacts to shipped reality, not to
retro-implement features that were honestly partial. This matches
the W-Vb / W-N-broader pattern already established in the cycle
(partial closure → named-defer to v0.1.13).

---

## Per-finding dispositions

| F-id | Disposition | Action |
|---|---|---|
| **F-IR-01** (W-FBC recovery prototype absent) | accepted; revise artifacts to match shipped scope | PLAN §2.8 + supersede_domain_coverage.md + RELEASE_PROOF §1 W-FBC row + CARRY_OVER + CHANGELOG + cli.py `--re-propose-all` help text reframed: "design + flag + report-surface only" v0.1.12; runtime enforcement (recovery prototype + multi-domain) deferred to v0.1.13 W-FBC-2. |
| **F-IR-02** (W-Vb PLAN claims full persona replay) | accepted; revise artifacts | PLAN §2.3 (a)/(b) reframed for partial closure; §3 ship gate Demo-regression row reframed; cli.py persona-flag help text updated from "no fixture loaded yet" to "skeleton fixture loads; proposal pre-population deferred to v0.1.13." |
| **F-IR-03** (deferral propagation incomplete) | accepted | tactical_plan §4 v0.1.13 row gains W-Vb persona-replay + W-N-broader rows. CARRY_OVER §1 W-Vb row updated to partial-closure with destination. CARRY_OVER W-N row updated from "≤80 → ships" to fork-deferred. |
| **F-IR-04** (CP byte-for-byte mismatch via origin parentheticals) | accepted as-known; document the convention | The accepted CPs were applied with editorial origin parentheticals (e.g. `(Origin: v0.1.12 CP1 + CP2.)`) for traceability. CP1/CP2/CP3 acceptance-gate sections now explicitly note this convention; future cycles inherit. |
| **F-IR-05** (doc freshness test narrow) | accepted; align PLAN wording to implementation scope | PLAN §2.1 acceptance text reframed to "mechanise the known offender pattern; rely on AGENTS.md ship-time freshness checklist for the rest." Test scope unchanged. |

---

## Open question resolutions

### Q1. Was W-FBC intentionally reduced to flag-accepted + report-surface-only?

**Resolution: no — I undershipped relative to PLAN, then RELEASE_PROOF reflected reality but the rest of the artifact set didn't catch up.** The honest fix is artifact alignment (what Codex called option b in F-IR-01's recommended response). Implementing the synthesis-side recovery carryover token + persona-style scenario tests in a hot fix would mean adding a real surface late in the cycle without the structural review the cycle has applied to other surfaces. That's worse than honest deferral.

W-FBC's v0.1.12 deliverable is now declared as: design doc + `--re-propose-all` flag accepted (CLI parser + capabilities row) + report-surface field on daily JSON + flag-round-trip tests. **Recovery prototype + multi-domain enforcement → v0.1.13 W-FBC-2.**

### Q2. Are CP origin parentheticals allowed?

**Resolution: yes — provenance markers are valuable; document the convention.** When CPs are applied to AGENTS.md / strategic plan / tactical plan, the maintainer may append a short `(Origin: v0.1.12 CP-N.)` parenthetical for traceability. CP docs are the authoritative source of the *replacement text core*; provenance parentheticals are editorial additions allowed under the CP's `accepted` gate.

CP1, CP2, CP3 docs updated to record this convention in their per-CP acceptance gate sections.

### Q3. Should PLAN be patched at ship to match partial closures?

**Resolution: yes — patch PLAN at ship to match accepted partial/fork outcomes.** The cycle has already done this for the v0.1.12 PLAN's other partial surfaces (W-Vb fixture-packaging vs persona-replay, W-N-broader fork). W-FBC is the laggard. Going forward, any cycle that ships partial closure must update the PLAN's per-WS contract section (not just RELEASE_PROOF) to match what shipped. Future cycles inherit this convention.

---

## Verified during this response

- W-FBC implementation surface (`grep -rn "re_propose_all" src/health_agent_infra/`):
  - `cli.py:8125` — parser arg.
  - `cli.py:4868` — report field.
  - **No** `core/synthesis.py` reads of `re_propose_all`. No `recovery_proposal_carryover_under_re_propose_all` token. No `verification/tests/test_supersede_domain_coverage.py`. Codex's claim verified.
- v0.1.13 tactical plan §4 deferred-row table (lines around 318): contains W-29-prep, W-FBC-2, W-LINT, W-AK, CP6 application; **does not** contain W-Vb persona-replay or W-N-broader. Codex's claim verified.
- CARRY_OVER.md §1 W-Vb row: reads "in-cycle (W-Vb here) | Demo persona-replay flow + fixture-packaging fix." That conflicts with the shipped partial-closure scope. Codex's claim verified.
- CARRY_OVER.md §1 W-N broader row: reads "in-cycle (W-N-broader here) | …49+1 → ≤80 branch confirmed → full broader gate ships." Stale. Codex's claim verified.
- `cli.py:8530` `--persona` help text: still says "accepted for forward-compatibility but no fixture is loaded yet" — stale post-W-Vb-loader. Codex's claim verified.
- AGENTS.md `(Origin: v0.1.12 CP1 + CP2.)` and `Origin: v0.1.12 CP3.` parentheticals confirmed at lines 124-125 and ~190; CP docs do not include them. Codex's claim verified.
- `test_doc_freshness_assertions.py` tests only ROADMAP.md `**vX.Y.Z current.**` pattern. Codex's claim verified.

---

## Round-2 expectation

The fixes in this commit are artifact-only — no code/test changes
beyond the two CLI help-text strings. Round 2 should be either:

- `SHIP` (clean) → merge to main + PyPI publish.
- `SHIP_WITH_NOTES` → merge with named follow-ups to v0.1.13.
- Another round of `SHIP_WITH_FIXES` only if the artifact realignment introduces a new contradiction (unlikely given the small scope).

If round 2 returns `SHIP` or `SHIP_WITH_NOTES`, the cycle closes
and Codex's three blocker findings are recorded as caught-and-
absorbed at implementation review.

---

## Lesson for v0.1.13+

**Add to AGENTS.md "Ship-time freshness checklist":** when a
workstream ships partial closure, *every* artifact must reflect
the partial scope, not just RELEASE_PROOF. Specifically:

- PLAN §2.X per-WS contract (the original ambitious framing
  must be patched, not left aspirational).
- CARRY_OVER disposition row.
- Tactical plan v0.1.X+1 row (next-cycle absorption).
- CHANGELOG bullet.
- CLI help text (if a new flag/command was scoped down).
- Design docs (if any were authored).

This is the v0.1.13 onboarding cycle's first inherited
freshness-checklist extension. The W-FBC + W-Vb misses this round
are the canonical examples.
