# Codex Plan Audit Response — v0.2.0 PLAN.md (R2)

**Verdict:** PLAN_COHERENT_WITH_REVISIONS

**Round:** 2 / 4

## Findings (R2)

### F-PLAN-R2-01. "Every atomic claim" survived in summary surfaces

**Q-bucket:** Q1 / Q3
**Severity:** stale-propagation
**Reference:** `PLAN.md` §1.1, lines 48 and 70; `PLAN.md` §1.4, line 146; `PLAN.md` §2.E, lines 435-438; `PLAN.md` §2.F, lines 461-472
**Argument:** F-PLAN-10 was fixed in the honesty boundary and cycle thesis, but the §1.1 W58D bullet and §1.2 catalogue row still say "Every atomic claim resolves to a locator OR audit-chain reference; otherwise the gate blocks." That conflicts with the revised W-FACT-ATOM/W58D contract, where qualitative atoms pass through and only quantitative/comparative factual atoms are gated.
**Recommended response:** Replace both summary-surface claims with "Every quantitative or comparative factual atom resolves to a locator OR audit-chain reference; otherwise the gate blocks. Qualitative atoms are constrained to non-factual narration and are not gated."

### F-PLAN-R2-02. Deferred-domain W-PROV-2 suppression lacks a W52 acceptance test

**Q-bucket:** Q2 / Q4
**Severity:** missing-test
**Reference:** `PLAN.md` §2.A, line 203; `PLAN.md` §2.D, lines 404-422; `PLAN.md` §3.4, line 670; `PLAN.md` §4 R-V0.2.0-01, line 688
**Argument:** Codex Q3 was adjudicated as "W52 suppresses quantitative claims for deferred domains" if W-PROV-2 partial-closes to v0.2.1 W-PROV-3. The behavior is named in §2.A and §3.4, but W52 acceptance has no fixture proving suppression, and R-V0.2.0-01 still says v0.2.0 ships W52/W58D "against partial substrate" without restating the suppression requirement. That leaves the new partial-closure behavior untestable.
**Recommended response:** Add a W52 release-blocker acceptance item with a fixture DB where one dormant domain is marked W-PROV-3-deferred; assert the weekly review emits the "insufficient provenance" disposition and no quantitative/comparative atoms or claim cards for that domain. Update R-V0.2.0-01 to reference the same suppression behavior.

### F-PLAN-R2-03. Append-only weekly cards make current-output count assertions ambiguous

**Q-bucket:** Q2 / Q3
**Severity:** new-incoherence
**Reference:** `PLAN.md` §2.C, lines 302-313; `PLAN.md` §2.D, line 410
**Argument:** The append-only change is correct, but the downstream assertions still read like latest-only semantics. §2.C acceptance #5 says `hai review weekly --json` includes one entry per card for the requested week; with append-only history that could include superseded historical cards. §2.D acceptance #6 says "count cards = count of atoms"; that fails on rerun unless the count is over the current invocation or canonical latest-card view, not all rows for the week.
**Recommended response:** Define `claim_cards` in the weekly JSON as either (a) canonical latest cards per `(iso_week, user_id, claim_id)`, or (b) cards created by the current W52 invocation. Add a rerun fixture proving historical rows remain in `weekly_claim_card` while `hai review weekly --json` still returns exactly one current card per quantitative/comparative atom.

### F-PLAN-R2-04. Carrier fork-defer path conflicts with the dependency DAG

**Q-bucket:** Q3
**Severity:** new-incoherence
**Reference:** `PLAN.md` §1.3, lines 88-97; `PLAN.md` §3.4, lines 672 and 674; `PLAN.md` §4 R-V0.2.0-03, lines 706-708; `PLAN.md` §4 R-V0.2.0-05, line 732
**Argument:** The R1 correction rightly removed stub-then-fill, but the replacement says the maintainer can fork-defer "ONE carrier (daily OR weekly)" while the DAG says W-EVCARD-WEEKLY lands after W-EVCARD-DAILY because weekly aggregates over daily, and W52/W58D consume the Phase 2 carriers. Deferring either carrier is not a neutral contingency: deferring weekly removes the W52/W58D claim-card surface; deferring daily contradicts the stated weekly-over-daily dependency unless W52 is reauthored to use weekly-only evidence.
**Recommended response:** Narrow the contingency. Either state that carrier deferral triggers D14 re-authoring before cycle open/continuation, or name a single valid fallback design with revised dependencies and acceptance tests. Do not leave "daily OR weekly" as an interchangeable maintainer call.

### F-PLAN-R2-05. R1-added verification work did not propagate to file/count gates

**Q-bucket:** Q1 / Q4
**Severity:** stale-propagation
**Reference:** `PLAN.md` §1.3, lines 109-117; `PLAN.md` §2.D, lines 328-335, 389, and 412; `PLAN.md` §2.F, lines 451-456 and 500-513; `PLAN.md` §3.1, lines 624 and 628
**Argument:** Two R1 fixes add verification work but only partially surface it. F-PLAN-03 adds `test_review_weekly_abstain_metadata.py`, yet the W52 files-of-record list and W52/G2 test-count projections still show the old W52 test surface. F-PLAN-07 says W58D acceptance should include the `--scenario-set all` semantics extension; the note exists in G4a, but §2.F acceptance has no item for it, and the cross-phase merge-friction list omits `evals/cli.py` even though W58D modifies it.
**Recommended response:** Add `verification/tests/test_review_weekly_abstain_metadata.py` to W52 files of record and either increase W52/G2 counts or explicitly state it is included in the existing abstain count. Add a W58D acceptance item for `--scenario-set all` fan-out to factuality while preserving judge_adversarial shape-only behavior, and list `evals/cli.py` in cross-phase merge friction.

## Open questions for maintainer

1. For weekly JSON, should `claim_cards` expose canonical latest cards only, or should it expose current-invocation cards plus a separate history query?
2. If a carrier must fork-defer, is the intended fallback weekly-only, daily-only, or "do not proceed without D14 re-authoring"?
