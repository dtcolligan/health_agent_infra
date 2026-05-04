# v0.1.19 cycle — workspace

**Status:** scoped as **empirical-by-design**, not yet open. PLAN.md
authored when the cycle opens, after v0.1.18 closes and a real
foreign-user candidate runs the install.

**Tier (anticipated):** substantive. Empirical post-session cycles
typically close 4-9 days but the cycle pattern still fires full
Phase 0 + multi-round D14 because what's being audited is the
session-output triage, not a fixed workstream catalogue.

**Provenance.** Originally scoped as **v0.1.16** (created 2026-05-03
alongside the v0.1.15 D14 close). v0.1.16 was cancelled on 2026-05-04
when its named foreign-user candidate became unavailable; the
empirical scope was preserved and renumbered to v0.1.19 to ship after
v0.1.18's onboarding-quality improvements. The maintainer's
restructure logic: do v0.1.17 (maintainability) → v0.1.18
(onboarding) → v0.1.19 (foreign-user empirical) → v0.2.0. See
`reporting/plans/v0_1_16/README.md` for the cancellation note.

## Why no PLAN.md yet

v0.1.19's scope is literally "the bugs the post-publish foreign-user
session surfaces" — authoring a PLAN.md before the session fires
would either be (a) speculative scope (guessing what bugs will
appear), or (b) trivial restate of "TBD per session output." Neither
helps. The PLAN authors when the cycle opens, with the session
transcript as input.

## Scope (provisional, finalised in PLAN.md after gate)

| W-id (anticipated) | Title | Source |
|---|---|---|
| **W-2U-FIX-P1** | All P1 fixes from the recorded foreign-user session | foreign-user session output |
| **W-2U-FIX-P2** | All P2 fixes from the recorded session (or named further deferrals) | foreign-user session output |
| **W-EXPLAIN-UX-2** | Empirical foreign-user pass over `hai explain` (deferred from v0.1.14 W-EXPLAIN-UX) consuming the v0.1.14 review doc's `carries-forward` section | v0.1.14 W-EXPLAIN-UX |
| **W-FPV14-SYM** *(conditional)* | Broader F-PV14-01 symmetry rule: every CLI command consuming both `--db-path` and `--base-dir` refuses asymmetric overrides. Land **only if the foreign-user session surfaces a friction point with the asymmetric-override pattern.** Otherwise defer. Source: v0.1.15 D15 IR round 1 F-IR-02 named-defer. | v0.1.15 IR round 1 F-IR-02 disposition |
| **W-OB-FU-RESIDUAL** *(conditional)* | If v0.1.18's onboarding work lands but the foreign user still gets stuck on an onboarding step, absorb the fix here. (v0.1.18 closes the *known* onboarding gaps; v0.1.19 catches the unknown ones.) | foreign-user session output |

**Effort estimate (anticipated):** 4-9 days. Bounded by session
output (~10 P-class findings if v0.1.18 + the package version current
at cycle open is reasonably prepared).

## Hard dependencies

- **v0.1.18 must be shipped to PyPI** — the foreign user installs the
  post-onboarding-cycle package, not pre.
- The foreign user's transcript at
  `reporting/plans/v0_1_19/foreign_machine_session_<YYYY-MM-DD>.md`
  must exist (or in a session log file the cycle session points to).
- The foreign user's install record + state DB snapshot archived per
  the convention v0.1.15 established.

## What's explicitly OUT of scope for v0.1.19

- **No new feature work.** Empirical fixes only.
- **No mechanical refactor** — that's v0.1.17.
- **No eval-substrate work** — v0.1.17.
- **No state-model schema additions** (v0.2.x territory).
- **No v0.2.x scope.**

If a finding from the session reveals a need for one of the above,
**the maintainer's call is whether to (a) defer that finding to
v0.2.x with named scope, or (b) cut a focused patch hotfix if the
issue is small and release-blocking** — not silently absorb it.

## First actions for the cycle session (when it opens)

1. Confirm v0.1.18 published (RELEASE_PROOF.md + REPORT.md present).
2. Confirm the foreign-user session transcript exists.
3. Read the transcript end-to-end before scoping.
4. Author `PLAN.md` per the empirical findings. First line: tier
   annotation. Sections: theme + per-finding W-id + ship gates +
   risks.
5. Copy `_templates/codex_plan_audit_prompt.template.md` and
   customise for the empirical-cycle audit shape (D14 questions
   focus on whether the empirical findings are correctly triaged,
   not whether the workstream catalogue is right).
6. Hand to maintainer for D14 round-1 launch.

## D14 plan-audit settled expectation (empirical cycles)

Substantive tier still applies. Empirical cycles tend to settle in
2-3 rounds (catalogue is bounded by session output; less surface
area for cross-doc consistency findings than restructure cycles).

## Phase 0 (D11) scope (empirical cycles)

Substantive tier requires Phase 0, but for an empirical cycle the
bug-hunt is narrower: re-run the persona matrix against the
post-v0.1.18 state model, audit-chain probe, internal sweep on the
named-deferred fix surfaces. Codex external bug-hunt audit is
optional per maintainer.

## Ship gate

- All session P1 findings either fixed or re-deferred with a
  specific destination.
- All session P2 findings fixed or deferred.
- W-EXPLAIN-UX-2 dispositions filed against the v0.1.14 review doc's
  carries-forward section.
- Standard substantive-cycle gates (pytest, mypy, bandit,
  capabilities round-trip).
- AUDIT.md + CHANGELOG entries authored.
- Ship-time freshness checklist from AGENTS.md.

## Cross-references

- `reporting/plans/v0_1_16/README.md` — cancellation note for the
  original empirical slot.
- `reporting/plans/v0_1_18/README.md` — the precursor onboarding
  cycle this cycle empirically validates.
- `reporting/plans/v0_1_15/PLAN.md` §2.G — original W-2U-GATE
  acceptance.
- `reporting/plans/tactical_plan_v0_1_x.md` — track table.
