# Competitive landscape — 2026-Q2 evidence refresh

**Cycle of record.** v0.2.0 W-COMP-LANDSCAPE.

**Source.** Refreshes the comparable-OSS survey from
`hai/reporting/plans/historical/multi_release_roadmap.md` (2026-04-25)
with 2026-Q2 evidence. The five competitor categories below match
`hai/reporting/plans/post_v0_1_18/strategic_plan_v2.md` §2.1; the five
defensibly-unique HAI elements at the end match §2.2.

**Date-checked.** All cited URLs verified accessible during the
v0.2.0 PLAN-authoring window (2026-05-06 → 2026-05-07). Where a
competitor has a published roadmap or recent release, the cited
date reflects the most recent observation.

**What this doc is.** A positioning artifact for v0.3+ external
narrative work. It says where HAI sits relative to the nearest
neighbours and what's defensibly unique. It is **not** a
disparagement of the competitors — most of them have shipped years
of useful work, and HAI inherits design debts (state-DB schema
shape, audit-chain discipline) the OSS forerunners proved out.

---

## 1. The category claim

HAI's category does not yet have a canonical public name. The five
nearest neighbours, in order of how closely they touch the
"governed personal-health agent" surface:

1. **Quantified-self trackers** — collect data; do not reason.
2. **Athlete analytics platforms** — reason inside one domain
   (training load); do not unify nutrition / sleep / stress /
   recovery / strength.
3. **Health MCP servers** — expose raw rows to a host LLM with no
   governance layer.
4. **Vendor coaches** — narrate over a fixed proprietary metrics
   stack on cloud infrastructure.
5. **Multi-agent personal-health frameworks** — exist as research
   papers; none ships in production for daily-driver use.

The accurate description, sharpened post-docs-overhaul:
**a local-first agent-wrapper for daily personal-health decisions
across six domains, where a deterministic policy engine owns every
band, score, and rule, and the LLM is allowed only to compose
bounded, typed, reviewable proposals.**

---

## 2. Category 1 — Quantified-self trackers

These ship data collection + visualisation. None reasons over the
data; all expect the user to interpret what they see.

### 2.1 QS Ledger
- **Primary source.** [Mark Wilson's QS Ledger (GitHub)](https://github.com/markwk/qs_ledger).
- **Shape.** Python ETL pipelines for personal data ingestion
  (Apple Health, Last.fm, Strava, Pocket, Withings, etc.) + Jupyter
  notebooks for analysis. Active 2017-present.
- **Where it touches HAI.** The ETL pattern (per-source connectors
  feeding a unified personal data pool) prefigured HAI's pull-source
  architecture. HAI inherits the discipline; differs in shipping a
  governed reasoning layer on top.

### 2.2 Bearable
- **Primary source.** [bearable.app](https://bearable.app/).
- **Shape.** Mobile-first symptom + mood + activity tracker; users
  log structured tags daily, app produces correlation insights.
- **Where it touches HAI.** Symptom-tagged structured input is the
  closest analog to HAI's `hai intake` shape. Bearable's
  correlation surface is exploratory (the user reads charts); HAI
  ships a deterministic policy + recommendation surface on top.

### 2.3 Heads Up Health
- **Primary source.** [headsuphealth.com](https://headsuphealth.com/).
- **Shape.** Web-based tracker for keto / carnivore / functional-
  medicine users; aggregates labs + wearables + manual logs.
- **Where it touches HAI.** Multi-source aggregation pattern; HAI
  differs in governance posture (HAI refuses to make clinical
  claims; Heads Up Health centres on lab-driven coaching).

### 2.4 Levels
- **Primary source.** [levelshealth.com](https://levelshealth.com/).
- **Shape.** CGM-forward (Continuous Glucose Monitor) consumer
  product; meal-tag and activity-tag log + glucose-response
  analysis.
- **Where it touches HAI.** CGM as a daily-driver substrate
  validates the "single source per domain, daily grain" thesis HAI
  applies to wearables. Levels ships vertical-only (glucose); HAI
  ships horizontal-six-domain.

**Verdict for category 1.** HAI is not a tracker. The QS bucket
ships data collection; HAI ships governed reasoning over data
collected by others (intervals.icu, Garmin, manual intake).

---

## 3. Category 2 — Athlete analytics platforms

These reason inside the training-load domain. They are excellent
at running / cycling / triathlon load management; they do not
unify nutrition, sleep, stress, recovery, or strength.

### 3.1 TrainingPeaks
- **Primary source.** [trainingpeaks.com](https://www.trainingpeaks.com/).
- **Shape.** Coach-facing platform for endurance athletes;
  acute:chronic workload ratio + Performance Management Chart
  (TSS-based).
- **Where it touches HAI.** ACWR is HAI's `_r_acwr_spike` rule
  (running domain); the substrate-shape ancestry is direct.
  TrainingPeaks is closed-source SaaS; HAI is local-first OSS.

### 3.2 intervals.icu
- **Primary source.** [intervals.icu](https://intervals.icu/) +
  [intervals.icu API docs](https://intervals.icu/api/v1).
- **Shape.** Free web platform; Garmin Connect / Strava / Apple
  Health sync; ACWR + form/fitness/fatigue + per-activity power
  + HR analysis.
- **Where it touches HAI.** **HAI's primary live-data source.**
  intervals.icu is what HAI's `core/pull/` adapters fetch from;
  the read-only API is the project's data backbone. HAI does not
  compete with intervals.icu — it sits on top.

### 3.3 Golden Cheetah
- **Primary source.** [GoldenCheetah/GoldenCheetah (GitHub)](https://github.com/GoldenCheetah/GoldenCheetah)
  + [handoff history](https://nyvelocity.com/articles/coachingfitness/golden-cheetah-open-source-goodness/).
- **Shape.** OSS desktop training-load analyser; 2006-present
  (~20 years), v3.6+. Survived multiple maintainer transitions.
- **Where it touches HAI.** Validates that long-run desktop OSS
  in this category is possible (counter-example to RUNALYZE
  killing its OSS edition; see §3.4). HAI's
  `MAINTAINERS.md` discipline borrows from Golden Cheetah's
  named-handoff pattern.

### 3.4 RUNALYZE
- **Primary source.** [forum.runalyze.com — OSS abandonment thread](https://forum.runalyze.com/viewtopic.php?t=1176).
- **Shape.** Web-based training analytics; killed its OSS edition
  in 2019 because server / infra cost outpaced single-maintainer
  capacity; commercial-only since.
- **Where it touches HAI.** **Negative example.** RUNALYZE's
  OSS-to-commercial pivot informs HAI's local-first posture
  (no server costs, no SaaS uptime burden). HAI's wheel-only
  distribution + zero hosted infrastructure is a deliberate
  response to this failure mode.

**Verdict for category 2.** HAI inherits ACWR + load reasoning
patterns from this category; ships them as one domain among six,
not as the sole product.

---

## 4. Category 3 — Health MCP servers

These expose raw wearable rows over the Model Context Protocol
to a host LLM. None ships a governance / policy layer; the LLM
sees the data and is expected to reason.

### 4.1 Garmy
- **Primary source.** [bes-dev/garmy (GitHub)](https://github.com/bes-dev/garmy).
- **Shape.** Python CLI + MCP server for Garmin Connect; exposes
  steps, sleep, HR, activities to a host LLM as MCP tools.
- **Where it touches HAI.** Direct comparable for any future HAI
  MCP read-surface (v0.3-v0.4). Garmy's posture: raw rows out,
  reasoning is the LLM's job. HAI's posture (per
  `hai/docs/mcp_threat_model.md`): governance layer first;
  MCP surface as a structured-output channel after.

### 4.2 Open Wearables (the-momentum)
- **Primary source.** [the-momentum/open-wearables (GitHub)](https://github.com/the-momentum/open-wearables).
- **Shape.** Multi-vendor wearable normalisation (Apple
  HealthKit, Garmin, Whoop, Oura) with self-hosted deployment +
  optional MCP / AI reasoning layer.
- **Where it touches HAI.** Open Wearables documents the
  "normalised wearable ingestion" pattern HAI may consume
  upstream rather than reimplement per-vendor (post-v0.1.13
  strategic research §16 / Brief 5 risk-mapping).

### 4.3 Pierre (multi-vendor MCP)
- **Primary source.** [pierre.dev](https://www.pierre.dev/).
- **Shape.** Multi-vendor MCP server; exposes activity + sleep +
  recovery rows from multiple wearables.
- **Where it touches HAI.** Same posture as Garmy: row-level
  exposure, no governance layer. Pierre is the most
  feature-complete in this category as of 2026-Q2.

### 4.4 garmin-mcp + whoop-mcp + Apple Health MCP
- **Shape.** Single-vendor MCP servers; pattern repeats across
  the wearable space. Each ~few-hundred-LOC adapter; same
  raw-rows-to-LLM model.
- **Where it touches HAI.** Demonstrates the **default pattern in
  this category** — every comparable MCP server exposes raw
  rows; **none ships a governance layer**. HAI's deferred MCP
  surface (v0.3+) is the exception, not the rule.

**Verdict for category 3.** HAI does not currently expose an MCP
surface; v0.3-v0.4 will, with the explicit governance posture
documented in `hai/docs/mcp_threat_model.md`.

---

## 5. Category 4 — Vendor coaches

These narrate over a fixed proprietary metrics stack on cloud
infrastructure. The user does not control the data, the rules,
the prompts, or the model.

### 5.1 WHOOP Coach
- **Primary source.** [WHOOP Coach + OpenAI announcement](https://openai.com/index/whoop/).
- **Shape.** Conversational AI coach inside the WHOOP app;
  narrates strain / recovery / sleep recommendations based on
  WHOOP's proprietary stack.
- **Where it touches HAI.** Vendor lock-in via proprietary metrics
  + cloud-only. HAI's local-first posture and pluggable pull
  adapters are a direct alternative for users who want to retain
  data sovereignty.

### 5.2 Oura Advisor
- **Primary source.** [Oura Advisor announcement](https://ouraring.com/blog/oura-advisor/) +
  [Oura Readiness calibration documentation](https://support.ouraring.com/hc/en-us/articles/360025589793-Readiness-Score).
- **Shape.** Conversational AI advisor inside the Oura ring app;
  narrates over Oura's readiness + sleep + activity scores.
- **Where it touches HAI.** Same posture as WHOOP Coach. Oura's
  Readiness algorithm is closed; HAI's recovery readiness is
  open + R-rule-driven, with `hai explain` reconciling every
  decision.

### 5.3 Google Health Coach / Google Health
- **Primary source.** [Google Health app announcement, 2026-05-07](https://blog.google/products-and-platforms/products/google-health/google-health-app/)
  + [Google Health Coach availability and pricing, 2026-05-07](https://blog.google/products-and-platforms/products/google-health/google-health-coach/)
  + [Fitbit Air announcement, 2026-05-07](https://blog.google/products-and-platforms/devices/fitbit/fitbit-air/).
- **Shape.** Fitbit app rebrands into Google Health on 2026-05-19;
  Gemini-built Google Health Coach exits preview as part of Google
  Health Premium ($9.99/month or $99/year, bundled into Google AI
  Pro/Ultra). The app centralizes wearable, app, Apple Health /
  Health Connect, and U.S. medical-record data; Fitbit Air is a
  $99.99 screenless wearable designed to feed the coach.
- **Where it touches HAI.** This is the clearest consumer-market
  signal that the paid layer is AI synthesis over personal data, not
  governance. HAI should not compete as a consumer coach. Its defensible
  value is the research claim: local contract-governed operation,
  reproducible evaluation, and auditable mutation boundaries.

### 5.4 Bevel
- **Primary source.** [Bevel website](https://www.bevel.health/) +
  [App Store listing](https://apps.apple.com/us/app/bevel-all-in-one-health-app/id6456176249).
- **Shape.** iOS / Apple Watch health companion with recovery,
  sleep, strain, nutrition, health records, and Bevel Intelligence
  as the AI guidance layer. The public site presents Bevel as a
  connected health coach with wearable and bloodwork support and
  `4.8 / 28.6k` global ratings.
- **Where it touches HAI.** Bevel validates demand for cross-domain
  AI synthesis over user health data and shows that consumer apps will
  push toward proactive coaching, health records, generated plans, and
  polished mobile UX. That makes HAI-as-consumer-product less credible,
  and HAI-as-research-artifact more credible.

### 5.5 (Cancelled comparable) Apple Health+
- **Primary source.** [Apple Health AI coach shelved (Feb 2026)](https://livity-app.com/en/blog/apple-health-ai-coach-shelved).
- **Shape.** Apple's planned AI coaching layer (codename
  Mulberry); shelved Feb 2026.
- **Where it touches HAI.** **Negative example for vendor coaches
  shipping multi-domain.** Apple's failure at multi-domain
  coaching at vendor scale is the load-bearing precedent for HAI's
  "small set of governed ledgers + strict code-vs-skill boundary"
  thesis (strategic_plan_v2 H5). Even Apple's resources couldn't
  ship the multi-domain prose-driven architecture; HAI's narrower
  scope + tighter contract is the alternative path.

**Verdict for category 4.** Vendor coaches and Bevel-like consumer
companions compete on polished AI synthesis, app UX, and proprietary
or cloud-backed data aggregation. HAI should not try to win that
market. Its live value is as a governed local reference runtime and
research substrate for GovernedAgentBench.

---

## 6. Category 5 — Multi-agent personal-health frameworks (research)

Each of these exists as a research paper or research code repo;
**none ships in production for daily-driver use.** They are the
academic competitive surface, not the daily-driver one.

### 6.1 Google PHA — The Anatomy of a Personal Health Agent
- **Primary source.** [arXiv 2508.20148 (Aug 2025)](https://arxiv.org/abs/2508.20148).
- **Shape.** Three-sub-agent framework (data-science agent +
  domain-expert agent + coach agent); 6.5 LLM calls per query
  median.
- **Where it touches HAI.** Validates user demand spans data
  science + domain expertise + coaching — but at 6.5 LLM
  calls/query, the cost shape is incompatible with daily-driver
  use. HAI's H4 thesis (LLM agents driving deterministic CLIs >
  multi-agent reasoning) is the alternative.

### 6.2 PHIA — Personal Health Insights Agent
- **Primary source.** [Merrill et al., Nature Communications 2025](https://www.nature.com/articles/s41467-025-67922-y).
- **Shape.** Single tool-using agent over wearable data; 84%
  objective accuracy on explicit data-reasoning tasks; reduces
  code errors compared to free-form LLM.
- **Where it touches HAI.** **Strongest external validation for
  HAI's H4.** PHIA shows tool-using agents beat raw LLM reasoning;
  HAI is the local-first, deterministic-CLI version of the same
  bet. The numeric provenance pattern PHIA establishes is the
  precursor to HAI's W-PROV-1 + W-PROV-2 + W58D layer.

### 6.3 Bloom / GPTCoach
- **Primary source.** [arXiv 2510.05449 (Oct 2025)](https://arxiv.org/html/2510.05449v1).
- **Shape.** LLM-augmented behaviour change with structured
  mutations; the closest published comparable for HAI's
  proposal-then-commit shape.
- **Where it touches HAI.** Bloom's structured-mutations pattern
  is what HAI's three-state audit chain
  (`proposal_log → planned_recommendation → daily_plan +
  recommendation_log`) productionises. Bloom is research-stage;
  HAI ships the same shape as runtime.

### 6.4 SePA — Search-enhanced Predictive Agent for Personalized Health Coaching
- **Primary source.** [arXiv 2509.04752 (Sep 2025)](https://arxiv.org/abs/2509.04752).
- **Shape.** Search-augmented LLM for personalised health
  coaching; demonstrates personalisation lives in the
  review/learning loop, not just in initial recommendation
  generation.
- **Where it touches HAI.** Validates HAI's review-outcome ledger
  thesis (`recommendation_log → review_outcome → adjusted future
  recommendations`). HAI's W48 + W52 + W53 surface is the local
  productionisation of SePA's research insight.

**Verdict for category 5.** Research literature validates HAI's
architectural direction; the production gap exists because moving
from research codebase to daily-driver runtime is itself the hard
problem.

---

## 7. The five things that remain defensibly unique to HAI

Cross-checked against the surveyed comparable-OSS landscape above,
**five things remain unique** (matching strategic_plan_v2 §2.2):

### 7.1 Deterministic policy engine separated from LLM judgment

R-rule + X-rule layer in code; skill-level invariants enforce that
neither runs in prose. Hardened by:

- v0.1.10 W-A bool-as-int silent-coercion closure (D12).
- v0.1.13 D13 threshold-injection seam formalised as
  trusted-by-design.
- v0.2.0 W-PROV-2 source-row provenance now populated for the 5
  dormant domains (this cycle).

**No comparable ships this.** WHOOP Coach / Oura Advisor / Fitbit
AI Coach are LLM-narration over fixed scores; PHA / Bloom mix
reasoning + judgment in the same agent.

### 7.2 Domain-typed Proposals with explicit safety/abstain semantics

`defer_decision_insufficient_signal` is a first-class action in
every domain. Hardened by:

- v0.1.10 W-C partial-day gate (nutrition).
- v0.1.15 W-A `is_partial_day` + `target_status` presence block.
- v0.1.15 W-C `hai target nutrition` macro target commit
  (W57-gated).

The abstain-when-uncertain contract is now four-deep in the
runtime, not one-deep. **No comparable ships this** —
abstain-as-first-class-action requires the policy/skill boundary
HAI ships.

### 7.3 Three-state audit chain with review-outcome reconciliation

`proposal_log → planned_recommendation → daily_plan +
recommendation_log → review_outcome` survives 18 cycles. D1
re-author semantics intact. `hai explain` reconciles end-to-end.

**Strong differentiator.** No competitor ships an analog. Open
Wearables / WHOOP Coach / PHA / Bloom each ship a *fragment* (Open
Wearables ships ingestion provenance; Bloom ships proposal shape;
none ship the full chain).

### 7.4 Capabilities manifest as agent contract

`hai capabilities --json` exposes mutation classes, `agent_safe`
flags, idempotency, exit-code semantics. Hardened by:

- v0.1.14.1 W-GARMIN-MANIFEST-SIGNAL — `choice_metadata.reliability`
  fields surface vendor unreliability.
- v0.1.17 W-30 — schema pinned with regression test
  (full freeze v0.2.3).
- Byte-stable across the v0.1.17 cli.py 9,927-LOC mechanical
  split.

**No comparable ships this.** Garmy / Pierre / Open Wearables
expose tools as MCP entries with no programmatic flag for "is
this safe for an agent to call without user confirmation."

### 7.5 Persona-driven regression infrastructure

12 archetypes (P1-P12) plus P13 (matrix-only) for the decision
layer. v0.1.17 W-Vb-4 closed 12-of-12 P1-P12 closure with P13
matrix-only (0 findings, 0 crashes).

**No surveyed competitor ships persona-driven regression testing
for their decision layer at this scale.** This is HAI's
v-of-v test surface; it's load-bearing for the
substantive-cycle Phase 0 D11 bug-hunt pattern.

---

## 8. What this doc deliberately does **not** do

- Does not declare HAI superior to any of the surveyed competitors.
  Each ships valuable work HAI inherits design discipline from.
- Does not freeze the competitor list. The MCP server space in
  particular is moving fast (>30 CVEs filed Jan-Feb 2026 per Check
  Point research); a v0.4 refresh will likely add 3-5 new MCP
  entries and possibly remove 1-2 abandoned ones.
- Does not argue HAI is mature. The five unique elements above are
  the **shipped** differentiators as of v0.2.0; H1-H5 (the five
  falsifiable bets) are not yet validated against external
  empirical evidence. Foreign-user empirical validation is
  re-scheduled to opportunistic-not-blocking under D16.

---

## 9. Cross-references

- **`hai/reporting/plans/post_v0_1_18/strategic_plan_v2.md`** §2.1
  (category claim) + §2.2 (defensibly differentiated).
- **`hai/reporting/plans/historical/multi_release_roadmap.md`**
  (2026-04-25) — the source survey this doc refreshes.
- **`hai/reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`**
  — the deeper-research artifact backing the
  category claims.
- **`hai/docs/mcp_threat_model.md`** (this cycle, v0.2.0
  W-MCP-THREAT) — the governance posture HAI brings to the MCP
  category.
- **`hai/docs/non_goals.md`** — what HAI deliberately does
  not do, complementing what it does.

---

*W-COMP-LANDSCAPE closes when this doc exists with ≥3 named
competitors per category, primary-source URLs, and the 5
unique-to-HAI elements cross-referenced to v0.1.x evidence.*
