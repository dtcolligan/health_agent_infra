# D14 Round 4 Maintainer + Claude Response — v0.2.0 PLAN.md

**Source.** `reporting/plans/v0_2_0/codex_plan_audit_round_4_response.md`
(Codex verdict `PLAN_COHERENT` with 1 nit; **0 OQs**).

**Round 4 outcome.** Round 4 returned **1 nit + verdict `PLAN_COHERENT`**
— matches the empirical norm `0-1 findings at verdict-only round`.
The full settling shape is now `10 → 5 → 3 → 1nit → 0` (effectively
`10 → 5 → 3 → 0` per the v0.1.x retro signature, with the nit absorbed
in cycle-open commit per Codex's verdict framing).

**Verdict accepted: PLAN_COHERENT.** PLAN.md nit absorbed in place;
**D14 chain closed**; **cycle opens for Phase 2 implementation.**

---

## F-PLAN-R4-01 — accepted (nit; deferred-domain disposition string)

**Disposition.** Accept fully. The R3 fix to F-PLAN-R3-01 reworded
prose around the deferred-domain suppression scope (quantitative +
comparative) at §2.A line 203 + §3.4 line 700, but the literal
quoted disposition string at §2.D acceptance #8 stayed
"quantitative claims suppressed pending v0.2.1 W-PROV-3." That string
is what the test (`test_review_weekly_deferred_domain_suppression.py`)
will pin as the markdown assertion — pinning the stale narrower
wording.

**This is a textbook R4 nit:** R3 reached almost every site but one
that's load-bearing (the test-pinned literal). Codex's R4 spot-check
caught it precisely.

**PLAN.md revision:**
- §2.D acceptance #8 (line ~421): the quoted disposition changed
  from `"quantitative claims suppressed pending v0.2.1 W-PROV-3"`
  to `"quantitative and comparative claims suppressed pending v0.2.1
  W-PROV-3"` to match §2.A line 203 + §3.4 line 700.

---

## D14 chain closure summary

**4 rounds; 18 cumulative findings; settling shape `10 → 5 → 3 → 1nit`.**

| Round | Findings | Verdict | OQs | Settling shape |
|---|---|---|---|---|
| R1 | 10 | PLAN_COHERENT_WITH_REVISIONS | 3 | First-order architectural + provenance |
| R2 | 5 | PLAN_COHERENT_WITH_REVISIONS | 2 | Second-order from R1 fixes (canonical: F-PLAN-R2-04 carrier-DAG conflict) |
| R3 | 3 | PLAN_COHERENT_WITH_REVISIONS | 0 | Third-order propagation (canonical: F-PLAN-R3-01 narrower-stale-survives-broader-fix) |
| R4 | 1 nit | **PLAN_COHERENT** | 0 | Fourth-order test-pinned literal (canonical R4 nit) |

The settling shape `10 → 5 → 3 → 1` is now **four-times empirically
validated** at substantive PLANs (v0.1.11, v0.1.12, v0.1.17, v0.2.0).
The thrice-validated retro claim is now four-times.

**Codex OQs decreased monotonically** — R1 had 3, R2 had 2, R3 had 0,
R4 had 0. The narrowing OQ count was itself the settling signal that
materialised in R3 + held in R4.

**Cumulative PLAN evolution:**
- Pre-D14: 774 LOC
- Post-R1 fixes: 821 LOC (+47 — biggest delta; absorbing 10 findings)
- Post-R2 fixes: 833 LOC (+12)
- Post-R3 fixes: 851 LOC (+18)
- Post-R4 nit: 851 LOC (literal substitution; no LOC delta)

The PLAN.md is now stable and ready for cycle open.

---

## Cycle open: Phase 2 implementation

Per the v0.2.0 cycle pattern + PLAN §1.3 sequencing DAG:

**Phase 1 — Substrate (parallelisable):**
1. **W-PROV-2** (foundational; W-EVCARD-* + W52 + W58D depend) — 2-4d
2. **W-MCP-THREAT** (doc-only, parallel) — 2-3d
3. **W-COMP-LANDSCAPE** (doc-only, parallel) — 1-2d
4. **W-NOF1-METHOD** (doc-only, parallel) — 1-2d

**Phase 2 — Carriers** (after W-PROV-2):
5. **W-EVCARD-DAILY** (mig 027) — 3-5d
6. **W-EVCARD-WEEKLY** (mig 028) — 2-4d

**Phase 3 — Aggregation + factuality**:
7. **W52** — 6-9d (W-EXPLAIN-UX-CARRY consumed inline)
8. **W-FACT-ATOM** — 2-3d
9. **W58D** — 5-8d

**Phase 4 — Opportunistic**:
10. **W-2U-GATE-2** — 0-2d (fires if candidate surfaces; per D16 v0.4
    re-eval if not)

**Phase 5 — Ship** (D15 IR + RELEASE_PROOF + freshness sweep + manual
TTY ship gate → push → twine).

**Total estimated effort: 25-37 days** substantive tier.

---

## Cross-cutting observations

**Four rounds, four canonical patterns:**
- R1 (10 findings): provenance-discipline failures + first-order
  architecture issues. F-PLAN-01 (wrong table name caught by Q8
  spot-verify) was the most embarrassing.
- R2 (5 findings): second-order issues from R1 fixes. F-PLAN-R2-04
  (fork-defer DAG conflict introduced by R1 fix to F-PLAN-09) was
  the canonical R2 catch.
- R3 (3 findings): third-order propagation. F-PLAN-R3-01 (narrower
  stale wording surviving broader R2 fix) was the canonical R3
  catch.
- R4 (1 nit): fourth-order test-pinned literal. F-PLAN-R4-01 (the
  test asserts a literal string that R3's prose rewrite missed).

**The two-LLM disagreement-without-consensus-collapse posture
earned its keep across all 4 rounds.** Each round caught what the
previous round's fix introduced. Without adversarial review, the
PLAN would have shipped with R1-class findings uncaught at minimum;
R3-class issues would have surfaced at IR or implementation time.

**The settling shape is reliable enough to budget against.** Future
substantive PLANs should budget 4 D14 rounds for R1+R2+R3+R4-nit-
verdict. Doc-only or hardening cycles can budget 1-2 rounds.

---

*D14 round 4 response_response authored 2026-05-07 by Claude.
PLAN.md final-state revised in place. **D14 chain closed at R4
with PLAN_COHERENT verdict.** Cycle opens for Phase 2 implementation.*
