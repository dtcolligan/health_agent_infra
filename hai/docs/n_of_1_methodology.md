# N-of-1 methodology — substrate-then-estimator chain

**Cycle of record.** v0.2.0 W-NOF1-METHOD.

**Research-reframe status.** This is an HAI reference-runtime
support-lane methodology note, not the current project calendar. The
project-wide objective is the runtime-contract paper plus
GovernedAgentBench; see [`../../project/FRAME.md`](../../project/FRAME.md),
[`../../project/DECISIONS.md`](../../project/DECISIONS.md), and
[`../../project/OPERATING_MODEL.md`](../../project/OPERATING_MODEL.md).
All v0.5/v0.6/v0.7/v1.0 references below are conditional HAI-runtime
forward plans that resume only when they support, or no longer compete
with, the paper / benchmark push.

**Forward-looking.** This doc is a positioning artifact for Wave 4
(v0.5–v0.6 per `hai/reporting/plans/superseded/strategic_plan_v2.md`
§7). v0.2.0 ships none of the surface this doc describes; the HAI
support-lane goal is to preserve a methodologically-honest contract
for the substrate + estimator before any future HAI PLAN-audit
authors code.

**The single load-bearing claim.** HAI's v0.5–v0.6 N-of-1 surface
will not be a fast layer. It will be a **substrate-first chain**:
the recommendation / compliance / outcome / classified-state
quadruple ledger must mature for ≥90 days of clean operation
*before* the v0.6 estimator runs any analysis on it. A user cannot
"turn on N-of-1" the day they install HAI; the data needs to
exist first.

This is the HAI support lane's strongest commitment to *not* shipping
unfounded individualised inference: the calendar gate is the
methodological honesty layer if and when this surface becomes active
again.

---

## 1. What N-of-1 means in HAI

The personal-trial methodology was introduced into modern medicine
by Lillie et al. 2011 ([The n-of-1 clinical trial: the ultimate
strategy for individualizing medicine?](https://pmc.ncbi.nlm.nih.gov/articles/PMC3118090/),
Personalized Medicine 8(2):161–173). The defining shift: **the
single patient is the unit of observation**, not a sampled
member of a population. Inference is about *this person's* effect,
across crossover periods and washouts that they themselves
contribute.

In HAI's surface, the equivalents are:

- **The patient** = the local user. Single-user-by-design per
  `SECURITY.md`.
- **The intervention period** = a daily plan with a specific
  recommendation (`recommendation_log` row).
- **The outcome** = the user's review-outcome record + downstream
  classified-state for the relevant domain
  (`review_outcome` + `accepted_*_state_daily`).
- **The compliance signal** = whether the user followed the
  recommendation (`review_outcome.followed_recommendation`).
- **The crossover** = HAI's daily recommendations vary
  day-to-day across the six domains. The ledger captures every
  recommendation + every outcome; analysis later reasons over
  whether intervention X correlated with outcome Y for *this*
  user.

The v0.5 ledger is therefore a **structurally honest N-of-1
substrate** — it captures the four elements (recommendation,
compliance, outcome, classified-state) the methodology requires
without pretending to run analysis prematurely.

---

## 2. The (recommendation, compliance, outcome, classified-state) quadruple ledger

### 2.1 The four lanes — already shipping

Three of the four lanes are already shipped through v0.1.x; v0.5
formalises the fourth and ties them into a single audit chain.

**Lane 1 — recommendation.** `recommendation_log` rows. One row
per shipped recommendation per domain per day. Carries the
forced action, action detail, confidence, the audit chain back to
proposal_log + planned_recommendation, and (post-v0.2.0 W-PROV-2)
source-row locators.

**Lane 2 — compliance.** `review_outcome.followed_recommendation`.
Boolean reflecting whether the user followed the recommendation.
v0.1.10 W-A hardened the bool-as-int-coercion contract on this
column. Per-domain compliance rates are derivable from existing
queries today.

**Lane 3 — outcome.** `review_outcome.self_reported_improvement`
+ free-text `note`. v0.2.0 W52 weekly review aggregates these.

**Lane 4 — classified-state evolution.** `accepted_*_state_daily`
rows. Already shipping; v0.5 pins the contract that **the
classified-state on day N+1 is the post-treatment outcome of the
recommendation issued on day N** for the relevant domain.

### 2.2 What v0.5 adds

The four-lane substrate is implicit in v0.1.x — the data exists,
but no integrity contract names it as a quadruple ledger yet. v0.5
ships:

- An explicit *quadruple-ledger view* in `hai explain`'s output,
  showing the four lanes lined up by date for the requested
  domain.
- A reconciliation regression test that asserts every
  `recommendation_log` row has exactly one `review_outcome` row
  scheduled (or marked "no-outcome-applicable") + the
  classified-state evolution for the next day exists or is
  marked-missing.
- An integrity test: zero orphan rows; every recommendation flows
  through to outcome + classified-state-evolution within a bounded
  window.

The v0.5 release is not the estimator. It is the **substrate
maturation milestone**: ≥90 days of clean reconciled data must
accumulate before v0.6 estimator code runs against it.

### 2.3 Why ≥90 days

The 90-day gate has three justifications:

1. **Statistical power.** Senn 2019 ([Sample size considerations
   for n-of-1 trials](https://journals.sagepub.com/doi/10.1177/0962280217726801),
   Stat Methods Med Res 28(2):372–383) shows adequate statistical
   power in N-of-1 trials depends not only on the number of
   participants, but on the number of *cycles* of trial conditions
   the participant completes. 90 days at a daily recommendation
   grain across six domains is approximately 540 recommendation /
   outcome cycles — large enough to detect medium effect sizes
   per-domain.
2. **Substrate-bug shake-out.** v0.1.x cycle history shows
   audit-chain bugs surface in second + third order over weeks of
   real data, not in test fixtures. The 90-day operational window
   is the empirical-bugs-found-zero gate.
3. **No "look-ahead bias."** v0.6 estimator code that ran against
   substrate freshly-emitted on day 0 would conflate the
   estimator's correctness with the substrate's correctness.
   Calendar separation isolates the two concerns.

This is why the 90-day gate **cannot be compressed.** It is
evidence-driven, not feature-driven.

---

## 3. The v0.6 estimator

### 3.1 What it is

A read-only analyzer that consumes the matured quadruple ledger
and produces individualised treatment-effect estimates for
*this user*, per domain. v0.6 ships:

- The estimator code at (proposed)
  `hai/src/health_agent_infra/core/n_of_1/estimator.py`.
- A new `hai n_of_1` CLI surface for read-only analysis.
- A required substrate-maturity gate at the CLI boundary: the
  command refuses to run if `<90` days of consecutive substrate
  exist for the requested domain (the gate fires *runtime-side*,
  not just at install time).
- Result-emission with explicit uncertainty quantification —
  Bayesian posterior interval estimates, never point claims.

### 3.2 What it is NOT

- **Not** an automated threshold-mutation surface. The v0.7
  governed-adaptation cycle ships that separately, with explicit
  user-commit per change. Per AGENTS.md "Do Not Do":
  "Do not allow automatic threshold mutation by an LLM agent
  without an explicit user-commit step."
- **Not** a clinical-claims engine. Per AGENTS.md governance
  invariant 3: "No diagnosis-shaped language in recommendations
  or rationales." The estimator outputs effect-magnitude estimates
  with uncertainty; the user reads them and decides what to do.
- **Not** a population-level inference engine. The user is the
  unit of observation; inference about other users requires
  pooling, which has its own contract (see §6 below).

### 3.3 Estimator candidate methods

v0.6 ships **one** estimator method, chosen at PLAN authoring
time. Three candidates, with primary-source citations, that the
v0.6 PLAN-audit will pressure-test:

**Bayesian hierarchical with weakly-informative priors.**
[Bayesian Models for N-of-1 Trials (PMC10817775)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10817775/)
documents the parameter-shrinkage benefits when the user has
relatively few cycles. Strong fit when 90 days yields ~540
cycle-instances; weaker fit if a domain has fewer outcomes.

**Causal-impact / Bayesian structural time series.** Brodersen
et al.'s [CausalImpact](https://research.google.com/pubs/archive/41854.pdf)
applied per-user. Strong fit for "did X intervention shift Y
outcome trend?"; weaker fit when interventions overlap (which
they do, across six domains).

**Vector-autoregression on self-tracked time series.** Daza
([Causal Analysis of Self-tracked Time Series, PMC6087468](https://pmc.ncbi.nlm.nih.gov/articles/PMC6087468/);
[Person as Population, arXiv 1901.03423](https://arxiv.org/abs/1901.03423);
[N-of-1 wearable HRV/sleep VAR study, PMC9823534](https://pmc.ncbi.nlm.nih.gov/articles/PMC9823534/))
ships the directly-applicable methodology for daily self-tracked
data.

The v0.6 PLAN-audit picks one. Picking more than one is a
v0.7+ candidate.

---

## 4. Methodological discipline borrowed from existing literature

### 4.1 The Lillie 2011 / Senn 2007 framework

Lillie et al. 2011 establishes the theoretical foundation;
Stephen Senn's 2007 *[Statistical Issues in Drug Development](https://onlinelibrary.wiley.com/doi/book/10.1002/9780470723586),
2nd edition* (Wiley) is the source for individualised effect
estimation. HAI's contract aligns with both:

- **Single user is the unit of observation** (Lillie 2011).
- **Effect estimates are individualised, not population-pooled
  per-default** (Senn 2007).
- **Uncertainty quantification is mandatory output** (both).
- **Intervention/control crossover handled via daily
  recommendation variation across domains** (HAI's adaptation
  of the methodology).

### 4.2 Causal inference for N-of-1

Piccininni & Stensrud 2024 ([Causal inference for N-of-1 trials,
arXiv 2406.10360](https://arxiv.org/abs/2406.10360)) addresses
the assumptions required to make causal — not merely
correlational — claims from N-of-1 data.

HAI's commitment: v0.6 estimator output language is
**"associated with"** unless the explicit causal-identification
assumptions (no unmeasured confounders within the user's daily
context, stable unit treatment value, positivity) hold. The
estimator emits the assumption-set check alongside the estimate;
when assumptions fail, the output drops to "associated with"
language explicitly.

### 4.3 Target trial emulation

The TARGET Statement ([JAMA 2025](https://jamanetwork.com/journals/jama/fullarticle/2837724))
formalises target-trial-emulation methodology. HAI's v0.6
estimator borrows the explicit-protocol shape: every analysis
declares **(a)** eligibility, **(b)** treatment strategies,
**(c)** assignment, **(d)** outcomes, **(e)** follow-up, before
running.

### 4.4 Existing N-of-1 platforms

Two existing platforms validate that local-first N-of-1 is
implementable:

- **StudyMe / StudyU** ([Trials 2022 paper](https://link.springer.com/article/10.1186/s13063-022-06893-7)
  + [GitHub](https://github.com/hpi-studyu/studyu)) — open-source
  HPI-backed N-of-1 study app. Strong precedent for the
  user-driven design + interventional-period handling. HAI is
  not StudyU; HAI is a daily-driver runtime that *also*
  produces N-of-1-shaped substrate.
- **International Collaborative Network for N-of-1 Trials and
  SCED** ([nof1sced.org](https://www.nof1sced.org/)) — the
  community-of-practice anchor. v0.6 PLAN authoring should
  cross-check the network's published methodology guidance.

### 4.5 The HDSR Special Issue 3 (2024)

[Personalized N-of-1 Trials (HDSR Special Issue 3, 2024)](https://hdsr.mitpress.mit.edu/pub/b6efwlql)
collects 12+ papers on contemporary N-of-1 methodology including
Bayesian methods, multimorbidity-handling, and infrastructure.
This is the canonical citation for "what 2024-state-of-the-art
N-of-1 methodology looks like" — v0.6 PLAN-audit will benchmark
against it.

---

## 5. Substrate-maturation gates in detail

### 5.1 The two calendar gates

```
v0.5 ship  ──► 90 days substrate accumulation ──► v0.6 ship
                                                   │
v0.7 ship  ──► 90 days zero-incident operation ──► v1.0 ship
```

**Gate 1: v0.5 → v0.6 (substrate maturity).** v0.6 PLAN-audit
runs only after ≥90 days of consecutive clean ledger operation.
"Clean" means: zero orphan recommendation rows, zero unmatched
review-outcome rows, zero violations of the audit-chain
reconciliation regression. If a substrate bug surfaces during
the 90-day window, the clock restarts.

**Gate 2: v0.7 → v1.0 (zero-incident maturity).** v1.0 ships
only after ≥90 days of zero-incident operation post-v0.7
governed-adaptation surface. "Zero-incident" means: no
governance-invariant violation, no autonomous threshold
mutation, no clinical-claim leakage in user-facing outputs. A
single incident restarts the clock.

### 5.2 Why these are evidence-driven, not feature-driven

Both gates are *negative-evidence* gates: the absence of bugs /
incidents is what passes them. There is no feature-completion
checkbox to skip the wait.

This is the HAI support lane's strongest concession to the
**maturity-vs-velocity tradeoff**. The strategic plan v2 §7 is
explicit: "the substrate-maturation gates (v0.5 → 90d → v0.6,
v0.7 → 90d → v1.0) cannot be compressed; they are
evidence-driven."

### 5.3 What happens if a single-user (the maintainer) cannot
generate substrate fast enough

Currently, the only user generating substrate is the maintainer.
At a median 1.5 days/week with logged daily plans (per the
current state DB), the substrate-maturity calendar may stretch
beyond the optimistic 14-18 month v1.0 horizon.

**This is acknowledged.** v0.5 PLAN-audit will likely revise the
total-horizon estimate based on observed substrate-density at
v0.5 ship. The post-v0.1.18 strategic plan v2 §7 already says
"realistic 18-24 months" for v1.0 — that range absorbs this
risk.

---

## 6. Population-level pooling — explicit non-scope

### 6.1 What HAI does not do

HAI does not pool data across users to produce population-level
inference. There are several reasons:

- **Single-user-by-design** (`SECURITY.md` "Out of scope:
  multi-user installations").
- **No telemetry path** (AGENTS.md "Local-first package
  posture").
- **No data-sharing infrastructure.** A user's local SQLite
  state never crosses the package boundary.

### 6.2 What this means for the estimator

The v0.6 estimator produces **individualised effect estimates
for the local user only**. It does not:

- Compare this user's effect estimate to a "typical user."
- Pool data across users to tighten priors.
- Publish anything to a centralised registry.

This is a deliberate methodological *and* governance choice. A
future cycle (v0.8+, hypothetical) could ship federated-analytics
infrastructure (cf. [FAItH federated analytics, Nature Sci Rep
2025](https://www.nature.com/articles/s41598-025-94501-4)) but
that's outside any currently-scheduled wave.

---

## 7. v0.5 + v0.6 acceptance shape (forward-looking)

### 7.1 v0.5 release-blocker contract (proposed; v0.5 PLAN authors)

- Quadruple-ledger view in `hai explain --quadruple` (or similar
  flag).
- Reconciliation regression test passing for the maintainer's
  state DB.
- Integrity test: zero orphan rows over the full state DB at v0.5
  ship.
- Substrate-maturity counter exposed via
  `hai stats --quadruple-days`.

### 7.2 v0.6 release-blocker contract (proposed; v0.6 PLAN authors)

- Estimator method picked + cited.
- ≥90-day substrate-maturity gate enforced at the CLI boundary.
- TARGET-statement-style protocol declaration for every
  estimator analysis.
- Causal-claim-vs-association language gate (per Piccininni &
  Stensrud 2024).
- Bayesian posterior interval output for every effect estimate.
- v0.6 PLAN-audit cross-checks against HDSR Special Issue 3
  (2024) methodology recommendations.

These are forward-looking; v0.5 / v0.6 PLAN authoring will
revise them.

---

## 8. What this doc deliberately does **not** do

- Does not implement the substrate or the estimator. v0.5 / v0.6
  territory.
- Does not pick the estimator method. The three candidates in
  §3.3 are equally valid until v0.6 PLAN-audit picks one.
- Does not pool across users. Single-user by design.
- Does not change the substrate-maturity gates. The 90-day gate
  is settled per strategic_plan_v2 §7.
- Does not declare HAI N-of-1-compliant. Compliance presupposes
  a surface to audit; HAI doesn't have one yet. This doc maps
  the *posture* the surface will inherit when it lands.

---

## 9. Cross-references

- **`hai/reporting/plans/superseded/strategic_plan_v2.md`** §7
  Wave 4 — substrate-then-estimator chain framing.
- **`AGENTS.md`** "Do Not Do" — the autonomous-threshold-mutation
  prohibition (post-v0.1.13 strategic research §18) is the
  governance-side complement to this doc's methodological-side
  posture.
- **`hai/docs/competitive_landscape.md`** §6 — multi-agent
  research frameworks (PHA, PHIA, Bloom, SePA) are the academic
  competitive surface for N-of-1; HAI's substrate-first chain
  is the local-first equivalent.
- **`hai/docs/mcp_threat_model.md`** — security posture
  the MCP read-surface (Wave 3) will bring; v0.5 substrate is
  what the v0.4 surface ultimately exposes data from.

---

## 10. Reference list

### Core methodology

- Lillie et al., 2011. *The n-of-1 clinical trial: the ultimate
  strategy for individualizing medicine?* Personalized Medicine
  8(2):161–173.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3118090/
- Senn, S. 2007. *Statistical Issues in Drug Development*, 2nd
  ed. Wiley.
  https://onlinelibrary.wiley.com/doi/book/10.1002/9780470723586
- Senn, S. 2019. *Sample size considerations for n-of-1 trials*.
  Stat Methods Med Res 28(2):372–383.
  https://journals.sagepub.com/doi/10.1177/0962280217726801

### Causal inference + analysis methods

- Piccininni, M. & Stensrud, M. J. 2024. *Causal inference for
  N-of-1 trials*. arXiv 2406.10360.
  https://arxiv.org/abs/2406.10360
- Daza, E. J. 2018. *Causal Analysis of Self-tracked Time
  Series*. PMC6087468.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6087468/
- Daza, E. J. 2019. *Person as Population*. arXiv 1901.03423.
  https://arxiv.org/abs/1901.03423
- Bayesian Models for N-of-1 Trials. PMC10817775.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC10817775/
- N-of-1 wearable HRV/sleep VAR study. PMC9823534.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC9823534/
- Brodersen et al. *CausalImpact*.
  https://research.google.com/pubs/archive/41854.pdf

### Implementation precedents

- Zenner et al. 2022. *StudyMe: a new mobile app for user-centric
  N-of-1 trials*. Trials.
  https://link.springer.com/article/10.1186/s13063-022-06893-7
- StudyU GitHub.
  https://github.com/hpi-studyu/studyu
- International Collaborative Network for N-of-1 Trials and SCED.
  https://www.nof1sced.org/

### Frameworks + standards

- HDSR Special Issue 3 (2024). *Personalized N-of-1 Trials*.
  https://hdsr.mitpress.mit.edu/pub/b6efwlql
- TARGET Statement for Target Trial Emulation. JAMA 2025.
  https://jamanetwork.com/journals/jama/fullarticle/2837724

---

*W-NOF1-METHOD closes when this doc lands documenting the
substrate-then-estimator chain, the academic citations, and the
substrate-maturation gates. v0.5 / v0.6 PLAN-audits pressure-test
the proposals here against actual ship-readiness when those cycles
open.*
