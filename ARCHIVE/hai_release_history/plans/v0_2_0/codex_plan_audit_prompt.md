# Codex External Audit — v0.2.0 PLAN.md (pre-cycle plan review)

> **Why this round.** v0.2.0 is the Wave 2 gateway: weekly review (W52)
> + deterministic factuality gate (W58D) + 4 doc-only adjuncts.
> Substantive tier; 25-37d estimate; 11 W-ids; one schema group
> (evidence-card family + weekly aggregation tables). Foreign-user
> empirical hard dep dropped per D16 (CP-2U-GATE-SPLIT,
> post-v0.1.18). v0.2.0's only hard dep is v0.1.14 substrate
> (W-PROV-1 + W-AJ judge harness), already shipped.
>
> Phase 0 (D11) closed 2026-05-06 with 13 F-PHASE0-* findings
> consolidated (8 Claude internal sweep + audit-chain probe; 5 Codex
> round 1; persona matrix 13/13 with 0 findings + 0 crashes).
> Maintainer adjudicated 3 Codex open questions:
> 1. Daily + weekly carrier (max rigor; both ship in v0.2.0).
> 2. Percentage thresholds over a larger corpus for W58D
>    (`block ≥97% / pass ≥99%` over ≥150 fixtures proposed).
> 3. W-2U-GATE-2 honors D16's v0.4 destination (NOT v0.2.1).
>
> **D14 is a settled decision** (added at v0.1.11 ship). Empirical
> norm: 2-4 rounds for a substantive PLAN, settling at the
> `10 → 5 → 3 → 0` halving signature.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 is closed; PLAN.md is
> authored. The audit is on the *plan document itself* — its
> coherence, sequencing, sizing honesty, hidden coupling. Phase 0
> findings are out of scope for re-discovery (already audited);
> Phase-0-derived PLAN dispositions ARE in scope (did the PLAN
> absorb each finding faithfully?).
>
> **You are starting fresh.** This prompt and the artifacts it
> cites are everything you need; do not assume context from a
> prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main (or chore/v0_2_0_plan if pre-cycle authoring)
git log --oneline -5
# expect: most recent should mention v0.2.0 PLAN.md authoring +
#         Phase 0 close + v0.2.0 cycle workspace seed
ls reporting/plans/v0_2_0/
# expect: README.md, PLAN.md, audit_findings.md,
#         codex_audit_findings_prompt.md, codex_audit_findings_response.md,
#         codex_plan_audit_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**. Ignore
any tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts

In order:

1. **`AGENTS.md`** — operating contract. Pay attention to:
   - "Governance Invariants" (W57, three-state audit chain,
     review-summary bool-as-int hardening D6/D12/D13).
   - "Settled Decisions" D1-D16 — note D16
     (CP-2U-GATE-SPLIT, foreign-user empirical hard-dep drop)
     and D14 (this audit's pattern).
   - "Do Not Do" — note that v0.2.0 ships W58D **deterministic
     only**; W58J at v0.2.2; no autonomous threshold mutation;
     no clinical claims; no MCP autoload mechanism.
   - **"Patterns the cycles have validated"** — provenance
     discipline (verify file:line on disk before citing),
     summary-surface sweep on partial closure, honest partial-
     closure naming, audit-chain empirical settling shape. Apply
     these as you audit.

2. **`reporting/plans/post_v0_1_18/strategic_plan_v2.md`** §7 Wave 2
   — strategic context. Note that v0.2.0 is release 1 of 4 in
   Path A (post-v0.1.13 CP-PATH-A); reconciliation C6 caps each
   release at one schema group.

3. **`reporting/plans/tactical_plan_v0_1_x.md`** §6 — release-by-
   release detail for v0.2.0. The PLAN must align with the
   tactical plan's row, or name + justify any divergence.

4. **`reporting/plans/post_v0_1_18/v0_1_x_retro.md`** §3 — five
   lessons; especially Lesson 1 (audit chains settle), Lesson 2
   (two-LLM disagreement productive), Lesson 5 (honest partial-
   closure naming).

5. **`reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md`** — D16.
   Note the named residual (W-2U-INSTALL closure verbal-only).

6. **`reporting/plans/v0_2_0/audit_findings.md`** — Phase 0
   findings (13 F-PHASE0-* items + maintainer adjudication of
   3 Codex open questions). The PLAN must absorb each
   `revises-scope` finding faithfully + name informational
   findings' dispositions.

7. **`reporting/plans/v0_2_0/codex_audit_findings_response.md`** —
   your prior round's response. The PLAN should reflect Codex's
   F-PHASE0-09..13 findings.

8. **`reporting/plans/v0_2_0/PLAN.md`** — the artifact under
   review (this audit). 774 LOC; 11 W-ids; 5 risks; 7 OQs.

9. **The W-PROV-1 contract substrate the cycle leans on:**
   - `src/health_agent_infra/core/provenance/locator.py:23` —
     `_ALLOWED_TABLES_PK` whitelist (currently 2 tables).
   - `reporting/docs/archive/cycle_artifacts/source_row_provenance.md:42-46`
     — W-PROV-1 contract: locators name evidence/accepted-state
     tables, **never** write-side tables.
   - `src/health_agent_infra/domains/recovery/policy.py:215-230`
     — recovery R6 reference shape (the only currently-firing
     locator emission path).

10. **The v0.2.0 schema-group target:**
    - `reporting/plans/future_strategy_2026-04-29/review_codex.md:1480-1632`
      — `recommendation_evidence_card.v1` schema sketch + weekly
      claim-card distinction at `:1614-1615`.
    - `src/health_agent_infra/core/state/migrations/` — current
      head `026_body_comp.sql`. v0.2.0 migrations land at 027 +
      028.

Cross-check that everything PLAN.md cites actually exists in the
tree at the cited line. **Broken cross-references count as
findings.** v0.1.x retro Lesson 1 (provenance discipline) explicitly
calls this out as the canonical round-2-finds-it pattern.

---

## Step 2 — The audit questions

### Q1. Cycle thesis coherence

PLAN.md §1.4 names the thesis: "v0.2.0 ships when claims about the
past week resolve to source rows or audit-chain references,
deterministically, with no LLM in the gate."

Do the 11 W-ids add up to that thesis, or has scope drifted?

- W-PROV-2 + W-EVCARD-DAILY + W-EVCARD-WEEKLY are the substrate.
- W52 is the aggregation.
- W-FACT-ATOM + W58D are the gate.
- W-MCP-THREAT + W-COMP-LANDSCAPE + W-NOF1-METHOD + W-2U-GATE-2 are
  doc-only adjuncts (not core thesis; positioning + Wave-3 prereq).
- W-EXPLAIN-UX-CARRY folds into W52.

Are any of these orthogonal to the thesis? Are any thesis-load-
bearing items missing from the catalogue?

### Q2. Sequencing honesty

PLAN.md §1.3 names a 5-phase DAG:

- Phase 1: W-PROV-2 + 3 doc-only adjuncts (parallel).
- Phase 2: W-EVCARD-DAILY → W-EVCARD-WEEKLY.
- Phase 3: W52 → W-FACT-ATOM → W58D.
- Phase 4: W-2U-GATE-2 (opportunistic, any time).
- Phase 5: D15 IR + ship.

Are there hidden ordering dependencies the DAG doesn't capture?

- Does W-EVCARD-DAILY need W-EVCARD-WEEKLY's claim_id hash design
  before its payload schema solidifies? (Or vice versa?)
- Does W52 actually need both carriers, or could it ship against
  weekly-only with daily-card consumption deferred to v0.2.1?
- Is W-FACT-ATOM really sequenced after W52? The atom parser is a
  pure function over W52 prose shape; arguably it can author in
  parallel once the prose-shape schema is locked.

### Q3. Effort estimate honesty

PLAN.md §5 names 25-37d range with mid-point 30d. v0.1.x retro
data: v0.1.17 (the comparable largest cycle) was 25-40d catalogue.

- Is W-PROV-2 actually 2-4d? The recovery R6 reference shape took
  v0.1.14 a non-trivial amount of work; replicating across 5
  domains is the same code path × 5, but each domain may have
  domain-specific complexity.
- Is W58D actually 5-8d given the corpus has to be ≥150 fixtures
  with 5 sub-categories? Corpus-construction effort is often
  under-estimated.
- Are doc-only adjuncts realistic at 4-7d combined? W-MCP-THREAT
  is OWASP MCP Top 10 mapping — that's reading + structured
  authorship, not stub.

### Q4. Hidden coupling

PLAN.md §4 names 5 risks. Are there coupling issues not in the
risks register?

- W-EVCARD-DAILY + W-EVCARD-WEEKLY share the schema-group budget
  (one group per C6). If 027 migration introduces unexpected
  coupling with recommendation_log, does 028 inherit?
- W52's prose-shape schema is consumed by W-FACT-ATOM. If W52
  iterates the prose during D14 IR, does W-FACT-ATOM's parser
  break? Is there a contract document?
- W58D's threshold values (97% / 99%) live in `thresholds.toml`.
  If the user overrides via TOML, does the override go through
  D13 validation? PLAN says yes; verify.
- W-2U-GATE-2 firing absorbs effort during cycle. Is the
  budget-vs-firing-cost trade-off named explicitly?

### Q5. Acceptance criterion bite

PLAN.md per-WS sections (§2.A through §2.K) each have numbered
acceptance items. Are they specific enough to fail on?

Spot-check:
- §2.A acceptance #4 ("recommendation_log.evidence_locators_json
  populated in ≥80% of new rows post-W-PROV-2 across the 5 dormant
  domains"): is 80% the right threshold? Why not 100%?
- §2.D acceptance #1 ("byte-stable output assertion: same fixture
  week → same JSON output across 3 consecutive runs"): is 3 runs
  enough? Some non-determinism shows up only at run-N where N is
  large.
- §2.F acceptance #3 (`block ≥97% / pass ≥99%`): per OQ-2, no
  published baseline. Is the proposal defensible?
- §2.J acceptance for W-2U-GATE-2 doesn't-fire path: "RELEASE_PROOF
  explicitly names 'W-2U-GATE-2 did not fire'." Is the
  no-transcript closure shape strong enough given D16's named
  residual on W-2U-INSTALL closure quality?

### Q6. Settled-decision integrity

PLAN.md cites D13 (threshold-injection seam), D14 (this audit's
pattern), D15 (cycle-weight tiering), D16 (foreign-user gate
split). Do the citations match AGENTS.md current text?

- D13 citation in §2.A acceptance #5 (validator-roundtrip negative
  test) — verify the contract is "production callers always
  validate user-supplied thresholds via `core.config.load_thresholds`."
- D16 citation in §1.1 + §2.J + §8 — verify v0.2.0's hard-dep
  drop is faithful + W-2U-GATE-2 destination is v0.4 review.
- W-PROV-1 contract citation in §2.A + §2.C (`source_row_provenance.md:42-46`)
  — verify the contract text matches the citation.

Does the PLAN propose any settled-decision reversals? If yes, is a
CP authored or referenced? PLAN-author claim: no reversals; only
F-PHASE0-11 wording-drift fixes during PLAN authoring touch-up
(§8). Verify.

### Q7. What the plan doesn't say

Conventional absence sweeps:
- **Abort path.** PLAN §4 R-V0.2.0-01 names "abort trigger >6d for
  W-PROV-2, fork-defer late-domains to v0.2.1." Is that the only
  abort condition? What if W58D corpus can't hit thresholds?
  R-V0.2.0-02 names threshold-revision but not cycle-abort.
- **Rollback shape.** PLAN doesn't explicitly name "forward-only
  migrations; v0.2.0.1 hotfix pattern; never `git revert`." Per
  F-PHASE0-13 disposition, it should. Where?
- **Conditional scope.** PLAN proposes W-EVCARD-DAILY stub-then-fill
  split in R-V0.2.0-03 if effort tightens. Is the criterion
  explicit enough? "30d wall-clock at W52 IR open" — vague.
- **Stub-then-fill default.** Per the maintainer-rigor preference
  saved as feedback memory ("if effort tightens, defer with named
  destination cycle"), is the stub-then-fill split honest, or is
  it really partial-closure that needs to ship as
  partial-closure → v0.2.1 W-EVCARD-DAILY-2?

### Q8. Provenance / external-source skepticism

Spot-verify the load-bearing external citations in PLAN.md:

- `core/provenance/locator.py:23` — confirm whitelist current.
- `domains/recovery/policy.py:215-230` — confirm R6 reference
  shape current.
- `core/state/migrations/` — confirm head 026, 027 + 028 are
  next slots.
- `review_codex.md:1551-1566` — confirm `recommendation_evidence_card`
  table sketch is at this line.
- `review_codex.md:1614-1615` — confirm "use weekly claim cards,
  not daily recommendation cards" wording.
- `source_row_provenance.md:42-46` — confirm "never a write-side
  table" contract.

Any drift between cited line and actual content is a Q8 finding.

### Q9 (cycle-specific). Schema-group claim

PLAN.md holds "one schema group" per F-PHASE0-09 + reconciliation
C6. R-V0.2.0-05 names this as a risk. Independent assessment:

- Does migration 027 + migration 028 + W52 weekly aggregation
  tables all belong to "evidence-card family"?
- The W52 aggregation tables aren't explicitly named in PLAN; is
  that a gap? (W52 may use only existing tables + the new
  `weekly_claim_card`; clarify.)
- If D14 disagrees and forces a 2-group split, which carrier defers
  to v0.2.1? PLAN R-V0.2.0-05 names the daily card as the deferral
  candidate, but this contradicts maintainer Q1's "always more
  rigorous" + "daily + weekly both ship."

### Q10 (cycle-specific). W58D corpus construction

The 150-fixture corpus has 5 sub-categories per `review_codex.md:1597-1602`:
source-quality, X-rule-conflict, source-signal-conflict, source-row
drift, audit-ref orphan.

- Are these the right 5 categories?
- Are the per-category counts (≥30, ≥15, ≥15, ≥15, ≥10) defensible?
  They sum to 85, leaving 65 across known-good — but PLAN says ≥75
  known-good. Math?
- Is the corpus authorable in 5-8d, or does corpus construction
  alone need its own W-id?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_2_0/codex_plan_audit_response.md` matching the
existing convention:

```markdown
# Codex Plan Audit Response — v0.2.0 PLAN.md

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
"PLAN.md §2.A claims `core/provenance/locator.py:23` but the actual
whitelist is at line 27 because of imports added 2026-05-04" is a
finding.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. Revisions list every must-fix finding.
- **PLAN_INCOHERENT** — do not open. Re-author the named sections
  before re-running this audit.

---

## Step 5 — Out of scope

- **Prior-cycle implementation** (already audited and shipped at
  v0.1.18; no v0.2.0 PLAN exists yet to revise its predecessor's work).
- **Code changes against this PLAN** (Phase 0 is closed but
  implementation hasn't started).
- **v0.2.1 / v0.2.2 / v0.2.3 / v0.3+ scope** — named in tactical
  plan §7-§9 but not in v0.2.0's commitments. v0.2.0 deferrals to
  v0.2.1 (e.g., W-RUNTIME-EVENT-OBSERVABILITY per R-V0.2.0-04) are
  in scope to evaluate as deferral honesty; the v0.2.1 design itself
  is not.
- **The strategic + tactical + eval + success + risks docs beyond
  the deltas this cycle proposes.** PLAN §8 names doc-only fixes to
  README.md:39 + tactical §6.1:880-882 (F-PHASE0-11 drift); evaluate
  whether these are honest fixes vs settled-decision changes.
- **F-PHASE0-* findings as such** — already audited in Phase 0;
  this audit is on PLAN's *absorption* of them.
- **Non-maintainer foreign-user empirical evidence** — D16 settled
  this; W-2U-WEARABLE + W-2U-DOGFOOD are deferred to v0.4 review.

---

## Step 6 — Cycle pattern (this audit's place)

```
v0.1.18 ship → 2026-05-06 ✓
post-v0.1.18 strategic refresh → 2026-05-06 ✓
v0.2.0 cycle workspace seeded → 2026-05-06 ✓
Phase 0 (D11) closed → 2026-05-06 ✓ (13 findings consolidated;
                                      maintainer adjudication on
                                      3 Codex open questions)
PLAN.md authored → 2026-05-06 ✓ (774 LOC, 11 W-ids, 25-37d est.)

D14 plan-audit (this round):
  Round 1 ← you are here
  Maintainer responds
  PLAN.md revises if warranted
  (loop until PLAN_COHERENT — empirical 2-4 rounds for substantive
   PLANs; v0.1.x retro Lesson 1 + 5 → 3 → 0 settling shape)

Phase 2 — Implementation:
  W-PROV-2 (foundational; W-EVCARD-* + W52 + W58D depend)
  W-EVCARD-DAILY → W-EVCARD-WEEKLY
  W52 → W-FACT-ATOM → W58D
  Doc-only adjuncts in parallel
  W-EXPLAIN-UX-CARRY consumed during W52

Phase 3 — D15 IR + ship:
  D15 IR rounds (empirical 2-3 rounds, 5 → 2 → 1-nit)
  RELEASE_PROOF + REPORT + AUDIT.md + CHANGELOG + freshness sweep
  Manual TTY ship gate → git push origin main → uvx twine upload
```

Estimated review duration: 2-4 sessions per round (PLAN is large;
774 LOC + cross-references).

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_2_0/codex_plan_audit_response.md` (new) —
  your findings.
- `reporting/plans/v0_2_0/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response.
- `reporting/plans/v0_2_0/codex_plan_audit_round_N_response.md`
  (subsequent rounds, if revisions warrant another pass).

**No code changes.** No test runs. No state mutations. No
implementation work — that opens after PLAN_COHERENT settles.

---

*D14 round 1 plan-audit prompt authored 2026-05-06 by Claude.
Ready for Codex.*
