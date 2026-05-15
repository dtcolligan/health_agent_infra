# Codex External Audit — v0.1.13 PLAN.md (pre-cycle plan review)

> **Why this round.** v0.1.13 is the public-surface hardening +
> first-time-user onboarding cycle. It composes three sources into a
> 16-workstream catalogue: (a) v0.1.12 RELEASE_PROOF §5 named-defers
> (W-Vb persona-replay end-to-end, W-N-broader 50-site sqlite3 leak
> fix, W-FBC-2 multi-domain F-B-04 closure, CP6 §6.3 strategic-plan
> edit application); (b) the originally-scoped onboarding scope from
> `tactical_plan_v0_1_x.md` §4.1 (W-AA through W-AG); (c) cross-
> cycle additions per CP1 / reconciliation §6 / Codex IR rounds
> (W-29-prep, W-LINT, W-AK, W-A1C7). One pre-cycle ship is recorded
> for catalogue completeness only: W-CF-UA shipped in v0.1.12.1
> hotfix prior to this cycle's open.
>
> **Scope-shaping inputs to verify:**
>
> - Reconciliation §6 v0.1.13+ named-defers (`v0_1_12/CARRY_OVER.md` §3).
> - v0.1.12 RELEASE_PROOF §5 inheritance.
> - Maintainer adjudication 2026-04-29 (this conversation): keep all
>   16 workstreams; no risk-driven cuts pre-cycle; ship hotfix
>   simultaneously with cycle open.
> - CP1 (W-29-prep mandate), CP6 (deferred application).
>
> **No settled-decision reversal proposed.** v0.1.13 is the
> first cycle since CP1-CP6 landed (v0.1.12 ship) where the W-29
> deferral becomes actionable; but W-29 itself remains v0.1.14 scope
> per CP1. v0.1.13 only does W-29-prep.
>
> **D14 is a settled decision** (added at v0.1.11 ship). Empirical
> norm: 2-4 rounds for a substantive PLAN, settling at the
> `10 → 5 → 3 → 0` halving signature. v0.1.11 + v0.1.12 both settled
> at 4 rounds with that signature; budget the same here.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 (D11) bug-hunt has not
> started. The CF-UA fix is already on the cycle/v0.1.13 branch
> (cherry-picked from hotfix/v0.1.12.1) but is recorded as a pre-
> cycle ship — NOT a v0.1.13 deliverable. The audit is on the *plan
> document itself* — its coherence, sequencing, sizing honesty,
> hidden coupling.
>
> **You are starting fresh.** This prompt and the artifacts it cites
> are everything you need; do not assume context from a prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: cycle/v0.1.13
git log --oneline -5
# expect: most recent commit is the cherry-picked W-CF-UA fix
# (subject "fix(pull/intervals_icu): set User-Agent to bypass
# Cloudflare bot block"); previous commit is the v0.1.12-cycle
# CLAUDE.md docs commit on main
ls reporting/plans/v0_1_13/
# expect: PLAN.md, CARRY_OVER.md, codex_plan_audit_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**. Ignore any
tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts

In order:

1. **`AGENTS.md`** — operating contract. Pay attention to:
   - "Governance Invariants" — none reversed this cycle, but verify.
   - "Settled Decisions" D1-D15 — note the W-29 / W-30 schedule
     (D from CP1 + CP2) which v0.1.13 W-29-prep operates within.
   - "Do Not Do" — none reversed this cycle.
   - **"Patterns the cycles have validated"** — provenance discipline,
     summary-surface sweep, honest partial-closure naming, audit-chain
     empirical shape. **Apply these as you audit.** v0.1.12 IR caught
     6 partial-closure summary-surface drift findings at round 2;
     watch for the same shape on this PLAN's inherited-partial items
     (W-Vb, W-FBC-2).
2. **`reporting/plans/strategic_plan_v1.md`** — vision. v0.1.13 only
   touches §6.3 (verbatim CP6 application) — verify the proposed
   replacement text in `v0_1_12/cycle_proposals/CP6.md` "Proposed
   delta" section is what `PLAN.md §2.A` claims will land at v0.1.13
   ship.
3. **`reporting/plans/tactical_plan_v0_1_x.md` §4** — v0.1.13
   originally-scoped block (W-AA through W-AG). PLAN.md §1.2 catalogue
   B should match.
4. **Cycle-specific input — these are the "bug hunt at cycle open"
   findings:**
   - `reporting/plans/v0_1_12/RELEASE_PROOF.md` §5 — every line must
     have a row in `v0_1_13/CARRY_OVER.md` §1.
   - `reporting/plans/v0_1_12/CARRY_OVER.md` §3 — every reconciliation
     v0.1.13+ item must have a row in `v0_1_13/CARRY_OVER.md` §2.
   - `reporting/plans/v0_1_12_1/RELEASE_PROOF.md` — the W-CF-UA
     hotfix RELEASE_PROOF, branchpoint v0.1.12 tag. Cycle/v0.1.13
     inherits its single fix-commit via cherry-pick.
   - `reporting/plans/v0_1_12/cycle_proposals/CP1.md` and `CP6.md` —
     CP1 establishes W-29-prep; CP6 is the deferred application.
5. **`reporting/plans/v0_1_12/RELEASE_PROOF.md`** — prior-cycle
   carry-overs (§5 named-defers). The W-CARRY register at
   `v0_1_13/CARRY_OVER.md` §1 should account for every line.
6. **`reporting/plans/v0_1_13/PLAN.md`** — the artifact under review.
7. **`reporting/plans/v0_1_13/CARRY_OVER.md`** — companion register;
   audit it alongside the PLAN.

Cross-check that everything PLAN.md cites actually exists in the
tree. Broken cross-references count as findings (provenance
discipline; v0.1.12 D14 round 1 caught `core/credentials.py:171`
when the file was at `core/pull/auth.py:171`).

---

## Step 2 — The audit questions

### Q1. Cycle thesis coherence

Does the 16-workstream catalogue add up to "public-surface hardening +
first-time-user onboarding," or has scope drifted?

- The four inherited W-ids (W-Vb, W-N-broader, W-FBC-2, CP6) are
  technical-debt closure, not onboarding. Is the theme honest, or
  is "onboarding" a label hung on a maintenance cycle?
- W-LINT (regulated-claim lint) is safety/regulatory, not
  onboarding. Justifiable in this cycle, or scope drift?
- W-29-prep is governance prerequisite for v0.1.14, not onboarding.
  Justifiable, or scope drift?

### Q2. Sequencing honesty

The PLAN doesn't lay out workstream order explicitly. Hidden
ordering dependencies?

- W-AA (`hai init` flow) depends on W-AG (`hai today` cold-start
  prose) — W-AA's step 7 surfaces day-1 prose. Is this dependency
  named? (Spot-check `PLAN.md §2.B W-AA` step 7.)
- W-AE (`hai doctor` expansion) probes intervals.icu live-API; W-CF-UA
  fix is a precondition. Cycle/v0.1.13 has the fix via cherry-pick —
  but if the cherry-pick were skipped or reverted, W-AE would be
  testing against a broken pull adapter. Should W-CF-UA inheritance
  be more prominent than "catalogue completeness only"?
- W-Vb (persona-replay) and W-FBC-2 (re-propose-all multi-domain)
  both write proposal_log rows. Do they have shared infrastructure
  that should be sequenced?
- W-AK (declarative persona expected-actions) is precondition for
  v0.1.14 W58 prep. Within v0.1.13, does it block any in-cycle
  workstream?

### Q3. Effort estimate honesty

Per-WS sizing realistic? Total claim: 22-32 days.

- W-N-broader: 4-6 days for 50 sites. Per-site cost: ~1-2 hours.
  Realistic given each site needs read + decide-fix-or-suppress +
  test + verify? V0.1.12 audit named the 50 sites; was per-site
  effort estimated then?
- W-FBC-2: 3-4 days for "recovery prototype + multi-domain rollout
  + per-domain fingerprint primitive (option B/C)." Three sub-
  deliverables, all touching synthesis-side code. Realistic?
- W-Vb: 3-4 days. v0.1.12 estimated W-Vb at 3-4d and ran into the
  partial-closure split. Does v0.1.13's W-Vb continuation account
  for design surface that was hidden at v0.1.12 estimation?
- W-AA onboarding flow: 2-3 days. Includes thresholds + migrations
  + skills + auth + intent + target + pull + render. Realistic
  for a single contributor in 2-3 days?

### Q4. Hidden coupling

Workstream-to-workstream interactions not documented in PLAN.md §4
risks register?

- W-LINT runtime check at the CLI rendering boundary may collide
  with W-AB (`hai capabilities --human`) prose surfaces. Coupling?
- W-AE (`hai doctor` expansion) may collide with W-AD (USER_INPUT
  message quality) — both touch CLI surface. Coupling?
- W-A1C7 trusted-first-value rename — if it touches identifiers
  in `core/synthesis.py`, it collides with W-FBC-2 (synthesis-side
  re-propose-all branch). Risk: rename + new branch in same file
  produces merge conflicts and audit-chain confusion.
- W-29-prep regression test on `hai capabilities --json` byte-
  stability — does this collide with W-AE doctor expansion (which
  may add capability-manifest rows for new doctor checks)?

### Q5. Acceptance criterion bite

Is each acceptance criterion specific enough to fail on? Spot-check:

- W-AA "≤ 5 minutes wall-clock for new user." Wall-clock measured
  how, by whom, on what hardware? Network-dependent (intervals.icu
  pull). Is the SLO measurable as written, or aspirational?
- W-AC "tells a new user the project's purpose, who it's for, and
  how to be running in <5 minutes." Subjective. What's the test?
- W-LINT "0 violations in packaged skills." How many skills exist?
  What's the violation surface? Is the term-list complete (the PLAN
  lists 11 starter terms — is that the full v0.1.13 surface, or
  expansion-during-cycle expected)?
- W-A1C7 "rename consistent across all surfaces." What surfaces?
  How is "all" verified?

### Q6. Settled-decision integrity

CP6 verbatim text edit at `strategic_plan_v1.md:407-411`.

- Does the proposed replacement text in
  `v0_1_12/cycle_proposals/CP6.md` "Proposed delta" exactly match
  what PLAN.md §2.A "CP6 application" claims will land?
- Is the line-range still 407-411, or has the strategic plan
  shifted since CP6 was authored on 2026-04-29?
- v0.1.10 update line at `:413-416` preserved unchanged per CP6
  acceptance gate. PLAN.md notes this; verify the line number is
  still correct.

### Q7. What the plan doesn't say

Absences — abort path, rollback, conditional scope.

- W-29-prep verdict could be "do not split" — PLAN §4 risks lists
  this as "low likelihood, acceptable outcome." Is the rollback
  documented? If verdict is "do not split," does v0.1.14 W-29
  defer to v0.2.0 or get cancelled? Tactical plan implications?
- W-LINT runtime check may break existing skill outputs that quote
  regulated terms with provenance citations (research /
  expert-explainer). The exception path is mentioned in §2.C but
  not in §3 ship-gates or §4 risks. How is the exception path
  validated to not become a wholesale loophole?
- W-Vb persona-replay end-to-end requires DomainProposal seeds
  across all 6 domains per packaged persona. PLAN says "start
  with P1, P4, P5; expand if budget allows." Is "P1, P4, P5
  only" sufficient for the ship-gate "demo regression"? What if
  budget doesn't allow expansion?
- The cycle has 16 W-ids but no explicit "release-blocker"
  designation. v0.1.11 had release-blockers (W-E, W-F); v0.1.12
  did not. v0.1.13: which W-ids would block ship if cut?

### Q8. Provenance / external-source skepticism

Spot-verify cited file:line claims.

- PLAN.md §2.A W-N-broader files list. Verify each path exists in
  current `cycle/v0.1.13` tree.
- PLAN.md §2.A W-Vb claims `apply_fixture()` returns a "deferred-
  to-v0.1.13 marker on DemoMarker." Verify against the actual
  v0.1.12 ship: read `src/health_agent_infra/core/demo/fixtures.py`.
- PLAN.md §2.B W-AE claim "reuses the existing `Probe` protocol
  from v0.1.11 W-X." Verify by grep: does `Probe` protocol exist?
- PLAN.md §2.A CP6 claim "lines 407-411 of
  `reporting/plans/strategic_plan_v1.md`." Verify the line range
  is still 407-411.
- PLAN.md §1.2 "Total scope: 16 workstreams — 4 inherited, 7
  originally planned, 4 added-this-cycle, 1 pre-cycle ship."
  Recount and verify.

### Q9. Sizing-vs-budget honesty (cycle-specific)

22-32 days at single-contributor pace = 5-7 calendar weeks at
4 hours/day. PLAN.md §5 acknowledges this is the "largest cycle in
the v0.1.x track." Is this honest, or is it the v0.1.7-shape
"under-promised + over-delivered" failure mode where the cycle
silently drops scope mid-flight?

- Risk-driven cuts in §4 risks register: "cut W-AC + W-AF + W-AK
  saves 3-4d." Is the cut order honest? Tactical plan §9 lists
  W-AC at top of cut order — does PLAN §4 match?
- W-N-broader at 4-6d is the longest single workstream. If it
  blows out to 8-10d, what does the PLAN say? Currently no
  contingency named.

### Q10. Pre-cycle ship integration

W-CF-UA shipped in v0.1.12.1 hotfix. PLAN.md §1.2 catalogue D records
it for completeness; CARRY_OVER.md §5 records the cherry-pick.

- Is this the right convention, or should the hotfix be invisible
  to v0.1.13 PLAN entirely (cycle starts from main HEAD which
  doesn't include the hotfix)?
- The fix IS on cycle/v0.1.13 via cherry-pick. If a future audit
  asks "what changed between v0.1.12 and v0.1.13?", the answer is
  16 W-ids OR "everything in the v0.1.13 cycle branch including
  W-CF-UA." Which framing is canonical?
- Should W-CF-UA appear in v0.1.13 CHANGELOG.md (alongside the
  v0.1.12.1 entry), or is the v0.1.12.1 entry sufficient?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_13/codex_plan_audit_response.md` matching the
existing convention:

```markdown
# Codex Plan Audit Response — v0.1.13 PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT (state which workstreams need rework before open)

**Round:** 1 / 2 / 3 / 4

## Findings

### F-PLAN-01. <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4 / Q5 / Q6 / Q7 / Q8 / Q9 / Q10
**Severity:** plan-incoherence | sizing-mistake | dependency-error |
acceptance-criterion-weak | hidden-coupling | settled-decision-conflict |
absence | provenance-gap | nit
**Reference:** PLAN.md § X.Y, line N (or "absent")
**Argument:** <why this is a finding, with citations>
**Recommended response:** <revise PLAN.md as follows / accept and
note as known limitation / disagree with reason>

### F-PLAN-02. ...

## Open questions for maintainer
```

Each finding must be triageable. Vague feedback is not a finding;
"PLAN.md §2.X claims `core/foo.py:171` but `foo.py` is at
`core/bar/foo.py:171`" is a finding.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. Revisions list every must-fix finding.
- **PLAN_INCOHERENT** — do not open. Re-author the named sections
  before re-running this audit.

---

## Step 5 — Out of scope

- Prior-cycle implementation (v0.1.12 already audited and shipped;
  v0.1.12.1 hotfix already reviewed by maintainer pre-publish).
- Code changes against this PLAN (Phase 0 D11 hasn't started).
- v0.1.14+ scope (named in tactical_plan_v0_1_x.md but not in this
  PLAN's commitments).
- The strategic + tactical + eval + success + risks docs beyond
  the deltas this cycle proposes (only CP6 §6.3 verbatim edit).
- W-CF-UA implementation review — already shipped in v0.1.12.1
  with its own (lightweight) RELEASE_PROOF.

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14] Codex plan audit ← you are here
  Maintainer response to plan audit
  PLAN.md revised if warranted
  (loop until PLAN_COHERENT — empirical 2-4 rounds for substantive
   PLANs at the 10 → 5 → 3 → 0 halving signature)

Phase 0 (D11):
  Internal sweep
  Audit-chain probe
  Persona matrix
  Codex external bug-hunt audit (optional per maintainer)
  → audit_findings.md consolidates

Pre-implementation gate:
  revises-scope findings may revise PLAN (loop back to D14)
  aborts-cycle findings may end the cycle

PLAN.md → opens cycle

Implementation rounds:
  Codex implementation review (post-implementation, IR)
  ... until SHIP / SHIP_WITH_NOTES (empirical 2-3 rounds)

RELEASE_PROOF.md + REPORT.md → ship to PyPI
```

Estimated review duration: 1-2 sessions per round.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_13/codex_plan_audit_response.md` (new) —
  your findings.
- `reporting/plans/v0_1_13/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response.
- `reporting/plans/v0_1_13/CARRY_OVER.md` (revisions, if warranted)
  — same.
- `reporting/plans/v0_1_13/codex_plan_audit_round_N_response.md`
  (subsequent rounds, if revisions warrant another pass).

**No code changes.** No test runs. No state mutations.
