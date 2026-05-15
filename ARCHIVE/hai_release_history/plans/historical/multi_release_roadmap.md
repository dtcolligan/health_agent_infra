# Multi-release roadmap (v0.1.9 → v1.0+) — SUPERSEDED

> ## ⚠️ SUPERSEDED 2026-04-27
>
> This doc is preserved as historical provenance. The current
> canonical strategic + tactical plans are:
>
> - **Strategic plan:** `reporting/plans/strategic_plan_v1.md`
> - **Tactical plan (next 6-8 releases):** `reporting/plans/tactical_plan_v0_1_x.md`
> - **Reading-order index:** `reporting/plans/README.md`
>
> The hypotheses (H1-H5), category claim, and settled decisions
> from this doc were lifted forward intact where still load-bearing.
> Three claims were falsified by v0.1.10 evidence and are addressed
> in `strategic_plan_v1.md` § 5 ("Settled-but-now-falsifiable").
>
> Do not act on this doc's release schedule (§ 4) — it predates
> v0.1.10 reality. Use the tactical plan instead.
>
> ---
>
> **Original status.** Draft authored 2026-04-25 by Claude. Supersedes the
> "Multi-release roadmap" + "Workstreams the plan missed" sections of
> `reporting/plans/v0_1_8/codex_audit_response.md` and the older
> `reporting/plans/historical/post_v0_1_roadmap.md`. This is the canonical
> forward plan; the audit file becomes immutable history once
> v0.1.8 ships.
>
> **Provenance.** Synthesised from eight parallel research briefs
> (personal-health-agent literature 2024–2026, JITAI/BCT, N-of-1
> infrastructure, privacy/local-first, consumer wearable accuracy,
> FHIR + Open mHealth + Open Wearables ecosystem, comparable OSS,
> causal inference + LLM-as-judge). Bibliography in § 9.
>
> **Audience.** Dom (owner + user), Codex (auditor), future
> contributors deciding whether to invest. This doc explains the
> strategic shape of the project over the next 12–18 months and
> names the bets — including bets that may turn out wrong.

---

## 1. Why this doc exists

The project just shipped v0.1.8 ("plan-aware feedback visibility").
Everything in the audit-response roadmap is now either built,
in-flight, or settled-deferred. The next plausible question is
"what does the project do over the next year, and which of those
directions is the credible bet vs the speculative one?"

Four things drove a fresh document instead of incremental edits to
the audit response:

1. **The audit response was scoped to refute v0.1.8's pre-revision
   plan.** It got the post-v0.1.8 sequence directionally right but
   stopped at a one-paragraph-per-release outline.

2. **Two years of relevant literature have landed since the prior
   roadmap.** Personal-health-agent papers (PHIA, SePA, Bloom),
   memory architectures (A-MEM, Mnemosyne), N-of-1 frameworks (StudyU
   active development, Piccininni & Stensrud's U-CATE), behaviour
   ontology (BCTO replacing BCTv1), wearable-accuracy benchmarks
   (Birrer 2025, Dial 2025), and runtime governance (AgentSpec) all
   change the calculus.

3. **The competitive landscape clarified.** Six+ Garmin → SQLite ETL
   repos, ten+ single-vendor MCP servers, multiple self-hosted
   training dashboards. None ship a deterministic policy engine plus
   bounded judgment surface plus typed Proposals plus writeback /
   review loop. The project is in a new category and should plan
   like one.

4. **Two industry data points sharpened scope.** Apple shelved its
   "Mulberry" / Health+ AI coach in February 2026 after attempting
   clinical-decision-tree-encoded coaching trained on staff
   physicians — the most-resourced effort in the consumer category
   hit the wall. Meanwhile, single-agent systems with code-execution
   tools (PHIA) match three-agent debate (Google PHA) on equal
   token budgets while shipping in production. Scope discipline is
   not under-ambition; it is the only shape anyone has actually
   shipped.

This roadmap commits to that scope discipline and proposes specific
new work where the evidence supports it.

---

## 2. Strategic positioning

### 2.1 The category claim

The project occupies a category that does not yet have a name in
public usage. Nearest neighbours:

- **Quantified-self trackers** (QS Ledger, Bearable, Heads Up
  Health, Levels) collect data; do not reason or recommend.
- **Athlete analytics platforms** (TrainingPeaks, intervals.icu,
  Golden Cheetah, RUNALYZE) reason inside one domain (training
  load); do not unify nutrition, sleep, stress, recovery, strength.
- **Health MCP servers** (Garmy, garmin-mcp, whoop-mcp, Open
  Wearables, Pierre, Apple Health MCP) expose raw rows to a host
  LLM with no governance layer.
- **Vendor coaches** (WHOOP Coach, Oura Advisor, Fitbit AI Coach)
  narrate over a fixed proprietary metrics stack on cloud
  infrastructure.
- **Multi-agent personal-health frameworks** (Google PHA, Bloom)
  exist as research papers; none ships in production for daily
  driver use.

The project is none of these. The accurate description is **a
local-first governed runtime + skill set for daily personal-health
decisions across six domains, where a deterministic policy engine
owns every band, score, and rule, and the LLM is allowed only to
compose bounded, typed, reviewable proposals.**

For brevity in the rest of this doc: **"governed personal-health-agent
runtime."**

### 2.2 What's defensibly differentiated

Cross-checked against every comparable project surveyed in the
research briefs, four things are unique:

1. **Deterministic policy engine separated from LLM judgment.** No
   competitor surveyed has both an R-rule layer (per-domain
   forced-action / capped-confidence rules) and an X-rule layer
   (cross-domain Phase A mutations) implemented in code with
   skill-level invariants enforcing they never run in prose.

2. **Domain-typed Proposals with explicit safety/abstain semantics.**
   `defer_decision_insufficient_signal` is a first-class action enum
   value in every domain. Nothing in the survey ships abstention as
   action.

3. **Writeback + review-outcome loop closing the recommendation
   cycle.** Every comparable MCP exposes raw data; none persist a
   user-confirmed outcome and link it back to the originating
   recommendation, much less re-link across superseded plans (D1
   re-author semantics).

4. **Capabilities manifest treating CLI as the agent contract.** `hai
   capabilities --json` exposes mutation classes, idempotency,
   exit-code semantics, agent-safety flags. This is what makes the
   project's CLI legible to *another* agent rather than just to a
   human reading help text. No competitor ships an equivalent.

The W51 data-quality ledger (v0.1.8) is also ahead of the published
state of the art — Identifying Data Quality Dimensions for
Person-Generated Wearable Device Data (PMC8738984) defines the
dimensions but stops short of implementation. Worth flagging because
it's the lowest-cost place to widen the lead.

### 2.3 Strategic posture for the next 18 months

**Lead with the governance contract, not the data ingest.** Adding
new wearable adapters is undifferentiated work that a six-line
Garmin-to-SQLite repo can do. The moat is the runtime + skills +
writeback/review loop. Every release should make the governance
contract more legible, more credible, more inspectable, more
exportable — *not* expand the surface area of what the project
ingests.

**Borrow the commodity, defend the decision layer.** Open mHealth /
IEEE 1752.1 / FHIR R4 are commodity vocabularies for data shape.
Adopt them where they let third parties consume the project's data
without rewriting integration glue. Do not adopt them where they
force the policy/judgment layer into a clinical interoperability
shape that contradicts the project's wellness-only positioning.

**Ship the credible artifact.** The R-rule + X-rule policy DSL is the
thing no competitor has and academia (AgentSpec, policy-as-prompt,
Bloom's structured mutations) is converging toward. It is publishable
prior art. Treat it as one.

---

## 3. Five falsifiable hypotheses the project is making

Each of these is a bet. Each can turn out wrong; each has a
falsification criterion. Stating them explicitly so future audits can
ask "is this still true?" rather than re-derive the entire strategic
case.

### H1. The hard problem in personal health AI is interpretability of outcomes, not better recommendations

**Bet.** The marginal value of a 5% better daily recommendation is
tiny compared to the marginal value of being able to answer "did
anything I changed actually help, and why do I think so?" The
project's core competence should be the *evidence-and-audit chain*,
not the recommendation algorithm.

**Evidence.** SePA (arXiv 2509.04752) shows personalisation lives in
the per-user predictor; LLM is downstream narration. Apple Mulberry's
shelving (Feb 2026) shows that a better recommendation engine alone
does not ship a product. JITAI meta-analysis (PMC12481328) finds
between-group g=0.15 — the recommendation effect is small; the
review/learning loop is where compound gain lives. WHOOP Coach,
Oura Advisor, and Fitbit AI Coach all narrate over fixed metrics
stacks and do not silently re-personalise.

**Falsification.** Structural caveat first: the project has N=1
user (Dom) today, so any "users find X more useful than Y"
criterion is unmeasurable until the project has a community.
The honest near-term proxy: *if Dom himself, after using v0.5's
N-of-1 substrate for ≥ 90 days, consistently consults the
underlying metrics in preference to the personal-evidence
verdicts, the bet is wrong*. Promotes to a population criterion
(≥ a handful of users in same direction) only post-v1.0 when a
community exists. Without that community, the H1 review is a
self-report check at the v0.5 retro, not a population claim.

### H2. Local-first beats hosted for the daily-runtime use case

**Bet.** Privacy + ownership + offline reliability + zero
data-egress beats centralised model freshness for a daily driver
that touches every domain of personal health.

**Evidence.** Cactus + Ollama + MLX clear 38–58 tok/s for 4B-class
models on M2 Pro; Llama 3.1 8B and Phi-7B are usable as judgment
models without a cloud round-trip
([SitePoint Apple-silicon LLM guide 2026](https://www.sitepoint.com/local-llms-apple-silicon-mac-2026/)).
EU Digital Omnibus + EDPB Opinion (2025) raise the GDPR bar on
training-data lawfulness, making "data never leaves the device" a
legitimate marketing posture
([Petrie-Flom](https://petrieflom.law.harvard.edu/2025/02/24/europe-tightens-data-protection-rules-for-ai-models-and-its-a-big-deal-for-healthcare-and-life-sciences/)).
Solid + sovereignty platforms still lack health PMF — lesson is
"useful local utility drives adoption, not standards." Comparable-OSS
survey: every shipping vendor coach is cloud; the local-first niche
is empty.

**Falsification.** If consumer hardware regresses on local LLM
performance OR a regulator forces a server-side audit trail
incompatible with local-first, the architecture is wrong.

### H3. User-authored intent + targets + bounded supersession is the right substrate for governed adaptation

**Bet.** The W49 intent ledger + W50 target ledger + the existing
proposal/plan supersession discipline form the substrate that makes
*future* governed adaptation possible without becoming a black-box
auto-tuning system. Adaptation belongs on top of this substrate, not
in place of it.

**Evidence.** AgentSpec (arXiv 2503.18666) is the closest published
prior art for runtime enforcement with user-approval-gated rule
mutation; it depends on a substrate of user-authored constraints
exactly like W49/W50. Bloom / GPTCoach (arXiv 2510.05449) shows
LLMs proposing structured mutations to user-owned plans is a working
shape. The project's `hai propose --replace` revision-chain is the
same primitive at a smaller scope.

**Falsification.** If, after v0.7 ships governed adaptation, users
either (a) routinely approve every proposed mutation without
reviewing or (b) routinely reject so many that the channel is
unused, the substrate is the wrong shape. The check is at the
v0.7 review.

### H4. LLM agents driving deterministic CLIs > LLM agents reasoning end-to-end

**Bet.** A CLI that exposes typed mutation classes + capability
manifest + exit-code contract is a *better* substrate for an LLM
agent than letting the LLM directly access the database, the model
weights, or the policy engine.

**Evidence.** PHIA (Nature Communications 2025) shows a single agent
with a code-execution tool matches a three-agent specialist team on
equal token budgets. Single-Agent vs Multi-Agent (arXiv 2604.02460)
shows multi-agent advantage shrinks as base-model capability rises.
The project's `hai capabilities --json` + `hai daily --auto`
next-actions manifest (v0.1.7) already operationalises this. Cactus +
Ollama show local single-agent inference is fast enough for
interactive loops.

**Falsification.** Two reachable signals:
(1) *Internal:* the project's own daily loop (Claude Code over the
CLI, today) starts shelling into SQLite directly because the CLI
can't surface what's needed. Detectable now via Codex audit of
session transcripts.
(2) *External (post-v0.4):* once the MCP ships, second agents that
integrate either bypass governed surfaces in favour of the
maintainer raw-access escape hatch, OR refuse to integrate because
the governed surface is too narrow. Both indicate the contract
shape is wrong.

### H5. A small set of governed ledgers + a strict code-vs-skill boundary scales further than a multi-agent prose-driven architecture

**Bet.** The project's invariants — append-only evidence, archive /
supersede over UPDATE, every row has provenance, skills never run
arithmetic — let one maintainer ship a runtime that a multi-agent
team cannot match for governance, audit, and reproducibility per
unit of complexity.

**Evidence.** Apple Mulberry's failure (Feb 2026) at multi-domain
clinical-decision-tree-encoded coaching with the largest engineering
team in consumer health. Google PHA paper concedes 6.5 LLM calls per
query and >3 minute latency — not a daily-driver shape. The shipping
vendor coaches (WHOOP, Oura, Fitbit) are all narration-over-fixed-
metrics, structurally similar to the project's classify+policy=code
+ skill=narration boundary.

**Falsification.** Structural caveat: the project lacks
retention / "did this help" telemetry today (N=1, no instrumented
comparison set). The reachable near-term signal is the *opposite
direction*: if the project itself starts to need a multi-agent
shape to ship the next release (e.g. v0.7 governed adaptation
proves intractable inside the single-runtime + skill boundary),
that's the falsification. Population-comparison criteria
(competitor-X vs project on retention) are post-v1.0 only and
contingent on the project having any external user comparison
data — which it does not today.

---

## 4. Multi-release roadmap

Each release names: **goal** (the strategic outcome), **ships**
(workstreams), **does not ship** (explicit non-goals to prevent
scope creep), **acceptance** (when we know we're done), and
**evidence anchor** (which research finding supports the shape).

### 4.0 Release timeline + dependency chain (read first)

The releases are not all parallelisable. Three hard dependencies
chain the back half of the roadmap:

- **v0.6 estimator depends on ≥ 90 days of v0.5 substrate.**
  v0.5 ships the (recommendation, compliance, outcome,
  classified_state) triple ledger; v0.6 adds the analyzer that
  reads it. The analyzer is uninteresting without ~3 months of
  clean triples to operate on.
- **v0.7 governed adaptation depends on v0.6 estimator output.**
  Without the estimator, threshold-mutation proposals have no
  evidence to cite.
- **v1.0 acceptance is "≥ 3 months of zero-incident operation
  post-v0.7."** This means v1.0 cannot ship sooner than ~3 months
  after v0.7.

Working backward from v1.0:

| Release | Earliest start | Reason |
|---|---|---|
| v0.1.9 | 2026-Q2 (post v0.1.8 ship) | No upstream dependency |
| v0.2 | v0.1.9 ship + ~4-8 weeks | Depends on W52 weekly review for chart inputs |
| v0.3 | v0.2 ship + ~4-8 weeks | No upstream feature dependency; pure infra |
| v0.4 | v0.3 ship + ~4-8 weeks | No upstream feature dependency |
| v0.5 | v0.4 ship + ~2-4 weeks | Substrate-only, small surface |
| v0.6 | **v0.5 ship + 90+ days** | Estimator needs accumulated triples |
| v0.7 | **v0.6 ship + 30-60 days** | Adaptation needs estimator-validated patterns |
| v1.0 | **v0.7 ship + 90+ days** | Stability proof window |

**Total minimum: ≈ 14–18 months from v0.1.9 ship to v1.0 ship.**
This is the optimistic case — solo maintainer, no slip on any
release, no extraordinary review cycles. Realistic case is 18-24
months. The roadmap is a multi-year commitment, not a multi-quarter
one. If that timeline doesn't fit the maintainer's bandwidth,
the right move is to scope-cut v0.4–v0.7 not to compress the
substrate-maturation gates (which are evidence-driven, not
willpower-driven).

The two pure-infra releases (v0.3 extension contracts, v0.4
runtime portability) can in principle ship in either order; the
sequence above puts them before the substrate clock starts so
that a future contributor or second integration can exist by the
time v0.5+ work is in flight.

### v0.1.9 — Weekly review + insight proposals + factuality gate

**Goal.** Make the runtime useful beyond one day. Surface what
happened over a week as a code-owned summary that a skill can
narrate and a local LLM judge can verify for factual grounding
before delivery.

**Ships.**
- **W52: `hai review weekly --week YYYY-Www [--json|--markdown]`.**
  Code-owned aggregation across accepted state, intent, target,
  recommendation, X-rule firing, review outcome, data quality.
  Outputs: planned vs completed, target adherence, recommendation
  adherence, missing data, repeated blockers, "not enough evidence"
  sections.
- **W53: Insight proposal ledger** (`insight_proposal` +
  `insight` tables). Evidence window, source ids, statement,
  caveat, confidence (low/moderate/high), claim_type
  (observation/correlation/hypothesis/experiment_result), status
  (proposed/committed/rejected/archived). Default to observation /
  hypothesis, never causal claims. User commits insights
  explicitly.
- **W58 (NEW): LLM-judge factuality gate for weekly review, with
  agent-judge negotiation loop.** Local Prometheus-2-7B (or
  comparable) pinned by SHA. One rubric: every quantitative claim
  in the weekly review must be derivable from cited state-DB rows.
  Flow on flag: (1) judge flags specific unsupported claims;
  (2) flag goes back to the *agent*, not the user; (3) agent must
  either correct the claim and resubmit OR defend the original
  claim with explicit evidence the judge missed; (4) the negotiation
  exchange (claim, flag, response) is logged alongside the final
  summary; (5) only after the loop converges does the user see the
  summary. Explicit non-goal: judge does NOT score helpfulness or
  tone — factual grounding only. (Decision 1, settled 2026-04-25.)

**Does not ship.**
- No silent insight commits. Insight visibility-only until user
  approves.
- No causal claims in the weekly review surface ("X caused Y" is
  forbidden; "X correlated with Y in this window" is allowed).
- No LLM-judge for tone, helpfulness, or skill quality. Factual
  grounding only.

**Acceptance.**
- Weekly review runs deterministically over fixture weeks, output
  byte-stable.
- Insight proposal ledger has migration + CLI + snapshot
  integration + capability manifest entry.
- Factuality judge runs on every weekly review, blocks delivery
  when ≥ 1 unsupported quantitative claim is found, judge model
  SHA + score logged with the review.
- Test count grows ≥ 30 vs v0.1.8.

**Evidence anchor.** Codex audit response §
"v0.1.9 — Weekly review and insight proposals." Brief 3
(personal-health-agent literature): A-MEM-style longitudinal
memory and PDSQI-9 LLM-as-judge results
([npj Digital Medicine 2025](https://www.nature.com/articles/s41746-025-02005-2)).
Brief 8 (causal + LLM-judge): local Prometheus-2 as factuality
judge, pinned weights for drift mitigation
([Prometheus 2 paper](https://arxiv.org/abs/2405.01535),
[arXiv 2511.07585 LLM Output Drift](https://arxiv.org/pdf/2511.07585)).

---

### v0.2 — Visualisation artifacts + behaviour-change ontology

**Goal.** Make state interpretable without SQL or chat. Tag the
runtime's recommendations with the standardised vocabulary of
digital behaviour change so weekly review can aggregate "what kind
of support actually got followed."

**Ships.**
- **W54: Artifact ledger** (`artifact` table). Artifact id, type,
  format, path, generated_at, input query, source row ids or source
  hash, generator version. Used for charts, weekly reports, release
  proof packs, explainability bundles, future eval transcripts.
- **`hai chart sleep | recovery | training-load | adherence
  [--since N] [--out PATH]`**. Static SVG/PNG via matplotlib;
  every chart specifies its source rows so it is reproducible from
  state.
- **`hai report weekly --html | --markdown | --json`**. Composes
  the W52 weekly review with W53 insights and W54 charts into a
  single self-contained artifact for sharing or printing.
- **W56-revised: Behaviour-Change Technique Ontology (BCTO) tags
  on recommendations.** Adopt the 2023 BCTO instead of BCTv1
  ([Wellcome Open Research 2023](https://wellcomeopenresearch.org/articles/8-308)).
  Five v1 BCTs supported, all mappable to existing fields with no
  new instrumentation: 2.3 (self-monitoring of behaviour, ←
  `completed` + `intensity_delta`), 2.2 (feedback on behaviour, ←
  reporting skill narration), 2.4 (self-monitoring of outcome, ←
  `pre/post_energy_score`), 1.5 (review behaviour goals, ←
  `disagreed_firing_ids`), 1.2 (problem solving, ← X-rule mutation
  in response to disagreement). Tags are descriptive metadata, not
  efficacy claims.

**Does not ship.**
- No claim of clinical efficacy from BCTO tags. They describe what
  the system does, not what works.
- No interactive charts (Plotly/Bokeh) in v0.2. Static is the bar
  for reproducibility.
- No live dashboard server. Reports generate, get saved, get
  inspected. Deferred to v0.4 if at all.

**Acceptance.**
- Artifact ledger has migration + integration with chart/report
  commands.
- Every chart and report carries its source row ids; regenerating
  from the same state produces a byte-equivalent artifact.
- BCTO tags appear on recommendations and are queryable; weekly
  review aggregates "followed-recommendation rate by BCT tag"
  without taking a position on which BCTs are causally helpful.
- Standards mapping doc (W55, shipped in v0.1.8) updated with BCTO
  reference.

**Evidence anchor.** Brief 2 (JITAI / BCT): BCTO supersedes BCTv1
with computer-readable structure and 281 techniques, inter-rater
reliability 0.79–0.82
([PubMed 37593567](https://pubmed.ncbi.nlm.nih.gov/37593567/)).
Brief 8 (comparable OSS): visualisation gap — no competitor ships
reproducible-from-state charts with provenance.

---

### v0.3 — Extension contracts + data-quality drift detection

**Goal.** Let contributors add domains/adapters without corrupting
governance. Make the W51 data-quality ledger handle vendor
algorithm drift — the silent-but-measurable failure mode that
nothing in the published consumer-runtime literature addresses.

**Ships.**
- **Domain extension template.** Step-by-step path for adding a
  seventh domain, with a contract checklist (intake, projection,
  snapshot, classify, policy, synthesis, writeback, skill, tests,
  evals, docs).
- **Adapter conformance tests.** Mechanical assertions every new
  pull adapter must pass before it can be advertised as a source:
  per-field degradation honesty, retry+backoff knobs respected,
  credential-rotation surface, freshness reporting.
- **W51 evolution: vendor-algorithm-drift detection.** Add
  `source_algorithm_version` axis to `data_quality_daily`. When a
  Garmin firmware bump / Whoop recovery rev / Oura major version
  is detected, the projector resets `cold_start_window_state =
  in_window` for that (domain, source) for N days regardless of
  total tenure. Brain-imaging is the only field that has formally
  solved this problem; no consumer-wearable runtime does.
- **W51 evolution: per-metric calibration progress.** Add
  `calibration_progress` field per metric, not per domain. Per the
  Oura-published windows: HRV baseline 14 days, 24-hour HR baseline
  30 days, Resilience 10 days
  ([Oura Help](https://support.ouraring.com/hc/en-us/articles/360025589793-Readiness-Score)).
- **W51 evolution: multi-source reconciliation block.** When a
  second source comes online, record per (user, date, metric):
  `agreement_state ∈ {single_source, agree, disagree,
  only_one_reporting}`, `primary_source`, `secondary_source`,
  `delta_vs_primary`. Do NOT fuse — record the disagreement and
  let the agent narrate it.
- **W59 (NEW): First-run UX triad.** Third-party adoption is the
  v1.0 acceptance criterion; v0.3 builds the substrate.
  - **`hai init` enriched.** Beyond the existing config/DB
    scaffold, emit a one-screen "next 3 commands to run" output
    on a fresh install (the Hugo / Zola / pre-commit pattern).
  - **`hai demo`.** New command that seeds a synthetic 30-day
    intervals.icu-shaped dataset behind an explicit flag. Goal:
    `pipx install` → `hai init` → `hai demo` → `hai daily` returns
    a real recommendation in under 60 seconds with no wearable
    account. Synthetic data is documented as non-PII and gated
    behind the flag so it never contaminates a real user DB.
    Closes the "time-to-first-value" gap (industry target 5-15
    minutes; 68% of devs cite setup time as the top abandonment
    cause).
  - **`hai next-step --json`.** Agent-facing first-run contract.
    Returns `{state, suggested_command, why}` so a downstream
    agent (Claude Desktop, Cursor, etc.) can drive a fresh install
    to first useful output without parsing prose. Pairs with the
    existing capability manifest + intent-router skill.
  - **Bundled onboarding skill** at
    `share/hai/agent_skills/onboarding.md`. Documents the
    canonical install → init → doctor → demo → daily flow with
    exit-code contracts, so an agent driving a fresh install gets
    the operational protocol, not just `--help`. Mirrors the
    "Ship the Prompt" pattern from AgentSpec / Deep Agents CLI.

**Does not ship.**
- No second-domain implementation in v0.3. Template + contract
  only. The first contributor-added domain is the proof.
- No second-vendor adapter in v0.3. Conformance tests + adapter
  template only.
- No numeric "trust score" rolling everything into a single 0–1.
  The literature's UQ work doesn't support a defensible weighting.
- No hard-coded Bland-Altman priors from the consumer-wearable
  validation literature. Studies are n=13 — directional, not
  calibrated enough to bake into runtime arithmetic.

**Acceptance.**
- Domain extension template + adapter conformance tests live in
  `reporting/docs/`. A third party could realistically use them.
- `data_quality_daily` carries `source_algorithm_version` +
  `calibration_progress` + multi-source reconciliation fields;
  migration 022 lands; `hai stats --data-quality` surfaces the new
  fields.
- Cold-start consistency test extended: a vendor algorithm version
  change resets `cold_start_window_state = in_window` for the
  affected (domain, source) and the test pins this behaviour for
  all six domains.

**Evidence anchor.** Brief 5 (wearable accuracy): vendor algorithm
drift is the silent enemy
([npj Digital Medicine 2024](https://www.nature.com/articles/s41746-024-01016-9),
[SLEEP 2025](https://academic.oup.com/sleep/article/48/4/zsaf011/7953384));
W51 ledger is ahead of published state-of-the-art
([PMC8738984](https://pmc.ncbi.nlm.nih.gov/articles/PMC8738984/)).
Brief 6 (FHIR/interop): defer adopters; ensure schema is
projectable to OMH / IEEE 1752.1 / FHIR R4 without remodelling.

---

### v0.4 — Runtime portability + cryptographic provenance

**Goal.** Let other agents drive the runtime safely; let the user
prove what their agent told them and when.

**Ships.**
- **MCP server exposing Proposals + capabilities manifest, with a
  documented personal raw-access switch** (Decision 3, settled
  2026-04-25, Option C). Default mode is the inversion of the
  standard pattern: every comparable MCP server (Garmy, Pierre,
  Open Wearables, Apple Health MCP) exposes raw rows; this MCP
  exposes typed Proposals, the capabilities manifest, the exit-code
  contract, and the existing `hai stats --outcomes / --baselines /
  --funnel / --data-quality` JSON outputs (already code-owned
  governance-respecting summaries). A separate explicit mode —
  e.g. `HAI_MCP_RAW_ACCESS=1` env-var or `--unsafe-raw` flag —
  exposes raw rows for the maintainer's own use of host LLMs (e.g.
  Dom asking Claude Desktop "show me my last 14 days of sleep").
  The contract: governed surfaces are the public face; raw access
  is private, explicit, and never default.
- **SQLCipher-backed state DB with OS-keychain key custody.**
  AES-256 transparent encryption, no query changes, key in macOS
  Keychain / libsecret. ~1-day implementation against existing
  schema. Encrypted backup + tested restore is the hard part
  ([Turso writeup](https://turso.tech/blog/fully-open-source-encryption-for-sqlite-b3858225)).
- **User-signed append-only audit log.** Every `hai writeback` /
  `hai review` / intake event signed with a user-held Ed25519 key,
  hash-chained Rekor-style. Tamper-evident, locally verifiable,
  ~50 LOC + one key-management UX
  ([Rekor design](https://docs.sigstore.dev/logging/overview/),
  [tamper-evident logging CCS 2025](https://dl.acm.org/doi/10.1145/3719027.3765024)).
- **Local-LLM optional pathway.** First-class support for Ollama /
  MLX as the judgment-skill runtime. Defaults stay cloud-Claude;
  the env-var flip makes the runtime fully local. No new
  capabilities, just runtime substitutability.

**Architectural note — two surfaces, one runtime.** The project's
own daily loop today runs Claude Code as the driving agent over
the `hai` CLI. After v0.4, two host-LLM paths exist over the
*same* runtime instance:
- **The maintainer path:** Claude Code (or another local agent)
  drives `hai daily` / `hai propose` / `hai synthesize` directly
  via the CLI. Has access to the raw-access escape hatch via
  `HAI_MCP_RAW_ACCESS=1` for the maintainer's own ad-hoc
  inspection.
- **The third-party path:** A second agent connects via MCP and
  sees only governed surfaces (typed Proposals, capabilities
  manifest, governed `hai stats` JSON outputs). No raw rows, no
  arbitrary SQL.
Both paths share one state DB, one capability contract, and one
skill set. The MCP server is an additional projection of the
runtime's governance, not a separate runtime instance. This
matters because if a future audit asks "which path drove this
recommendation?", the answer is auditable: every `runtime_event_log`
entry already carries `command` + `actor` provenance.

**Does not ship.**
- No general-purpose MCP write surface (e.g. arbitrary SQL).
  Other agents drive *through* the CLI contract, not around it.
- No federated cohort comparison. Privacy-preserving multi-user
  is post-v1 and depends on ≥ 2 users existing; not the case for a
  long time.
- No public REST API. CLI + MCP are the surfaces.
- No threshold-mutation channel yet. Adaptation is v0.5+.

**Acceptance.**
- MCP server passes a fresh-install smoke test against Claude
  Desktop using only Proposal-shaped tools.
- Encrypted state DB round-trips through `hai init` → `hai daily`
  → `hai review record` → restart with no manual key-handling.
- Signed audit log reconstructs from JSONL + signing key; tamper
  detection test green.
- A Llama 3.1 8B-class local model can produce a `RecoveryProposal`
  via the recovery-readiness skill that passes the W41 harness's
  schema_valid + action_matches checks.

**Evidence anchor.** Brief 4 (privacy / local-first): SQLCipher +
signed audit log are the two highest-leverage architecture moves
for low complexity. Local LLMs are production-ready on M-series
([SitePoint 2026](https://www.sitepoint.com/local-llms-apple-silicon-mac-2026/),
[Cactus](https://www.infoq.com/news/2025/12/cactus-on-device-inference/)).
Brief 8 (comparable OSS): MCP-over-Proposals is the inversion
that distinguishes governance from data-exposure servers.

---

### v0.5 — Personal evidence ledger + N-of-1 substrate

**Goal.** Stop guessing whether anything is helping. Build the
evidence substrate for N-of-1 self-experimentation; defer the
estimator until the substrate has matured.

**Ships.**
- **`hai experiment` table + CLI** as a thin schema over what
  already exists. An experiment is: `hypothesis_text`,
  `intervention` (a target ledger delta or intent ledger entry),
  `outcome_metric` (a ledger field already collected), `schedule`
  (alternating ABAB or randomized blocks over N days),
  `min_observations`. The intent ledger already records what was
  proposed; the target ledger already records what was committed;
  review-outcome already records what happened. An experiment is
  just a *named span* over those rows with an assignment vector.
- **Randomization-test analyzer in pure Python / SciPy.** Permute
  the assignment vector, compute the mean-difference null
  distribution, return p-value + effect size + the actual data
  plot. No external services, deterministic, auditable. The one
  statistical method where "single user, ~20–60 observations,
  local" is the *intended* use case
  ([nof1sced analysis page](https://www.nof1sced.org/analysis)).
- **User-readable verdict via the reporting skill.** "Over 28
  days alternating between A and B, your sleep efficiency was
  4.2 pp higher on B days (randomization-test p=0.04, n=14 vs 14).
  Confidence: moderate. Caveats: you missed 3 measurement days;
  carryover not modeled."
- **Personal evidence ledger.** Every TrainingRecommendation
  persists its `classified_state` snapshot and the X-rule
  mutations that fired. Every ReviewOutcome records compliance +
  next-day state delta. The result: a clean (recommendation,
  compliance, outcome, classified_state) triple ledger that an
  estimator can later consume.

**Does not ship.**
- No Bayesian multilevel / distributed-lag analyzer. Requires MCMC,
  prior elicitation, convergence diagnostics, and statistical
  literacy on the user side. Defer to v0.7+ or never.
- No causal claims surfaced to the user from the v0.5 surface.
  "Your data showed B was higher, here's the p-value, here's the
  caveats" is the bar — not "B caused better sleep."
- No IRB-compliant research-platform features. The differentiator
  is local-first single-user; do not chase StudyU's path.
- No g-methods / target trial emulation in v0.5. Substrate first;
  estimator in v0.6+ when there are ≥ 90 days of clean triples.

**Acceptance.**
- `hai experiment` migration + CLI + snapshot integration.
- Randomization-test analyzer produces deterministic output for
  fixture inputs; tested across known-positive, known-null, and
  insufficient-data cases.
- Personal evidence ledger captures the (recommendation,
  compliance, outcome, classified_state) triple for every
  recommendation in the test suite.
- Reporting skill renders the user-readable verdict in markdown
  and JSON; output reviewed for "operator-debug failure mode"
  per saved feedback memory (`feedback_user_facing_narration.md`).
- **`MAINTAINERS.md` exists** naming maintainer + handoff contact
  + license posture + 90-day-disappearance protocol (§ 5b.3).

**Evidence anchor.** Brief 3 (N-of-1): StudyU is server-backed →
project differentiated. Randomization tests are tractable for
local single-user; methods ranked tractable per nof1sced.
[BMC Med Res Methodol 2025 alcohol-abstinence case study](https://link.springer.com/article/10.1186/s12874-025-02738-4)
shows the data plumbing: timestamped self-report rows, intervention
indicator, covariate columns. Brief 8 (causal): substrate-first
beats estimator-first; defer estimator to v0.6+.

---

### v0.6 — Bounded N-of-1 estimator + causal-impact substrate matures

**Goal.** Add the estimator on top of the v0.5 substrate, scoped to
methods that are tractable and defensible for N=1 observational
data.

**Ships.**
- **Segmented / piecewise-regression analyzer** for "before vs
  after" on a single time series with a clear intervention point.
  Interpretable level + slope change at each phase boundary
  ([Springer 2023](https://link.springer.com/chapter/10.1007/978-3-031-19964-6_20)).
- **CausalImpact-style Bayesian structural time-series** for "did
  this intervention shift the trajectory." Closest fit to the
  project's data shape; the published precedent on wearable HRV /
  sleep is Prometheus' VAR + Granger study
  ([PMC9823534](https://pmc.ncbi.nlm.nih.gov/articles/PMC9823534/)).
- **Target trial emulation framing** for the user-facing report.
  TARGET reporting statement (JAMA 2025) is the dominant 2025
  framing
  ([TARGET](https://jamanetwork.com/journals/jama/fullarticle/2837724)).
  Define the target trial protocol, then estimate. The framing
  itself is the value-add; the estimation is small once it's
  framed correctly.

**Does not ship.**
- No g-methods (marginal structural models, time-varying g-formula).
  Built for populations; adapting to N=1 means stationarity
  assumptions about the person that are usually not testable.
- No IV estimators using weather / travel / work-calendar as
  natural experiments. Validity hinges on exclusion restriction
  (weather affects only compliance, not directly HRV) which is
  fragile (heat stresses HRV directly). Sanity check, not primary
  estimator.
- No public publication of the estimator framework. Internal use
  first; publish only after the v0.6 → v1.0 cycle has produced a
  defensible track record.

**Acceptance.**
- Segmented regression + CausalImpact analyzers ship behind `hai
  experiment analyze --method {randomization, segmented, causal-
  impact}`.
- All estimators report effect size + uncertainty interval +
  caveats; never a single point estimate without uncertainty.
- Output passes the W58 (v0.1.9) factuality gate with an extended
  rubric: "no causal claim that exceeds what the chosen estimator
  supports."

**Evidence anchor.** Brief 8 (causal): TARGET framing, CausalImpact
as drop-in tool, methods ranked by tractability for solo
maintainer.

---

### v0.7+ — Governed adaptation + longitudinal user belief graph

**Goal.** Let the system *propose* changes to its own thresholds /
rules / classifiers from accumulated evidence. Every change is
explicit, user-approved, before/after-evaluated, and reversible.

**Ships (proposed; final scope set at v0.6 retro).**
- **AgentSpec-style governed-adaptation channel.** Extend `hai
  propose --replace` to threshold/rule mutations. Skill proposes
  "raise the strength readiness X-rule cutoff for Dom from 60 to
  65 based on 14 weeks of evidence"; user reviews + approves +
  commits or rejects. Every mutation persisted with provenance,
  before/after window, and an explicit revert path
  ([AgentSpec arXiv 2503.18666](https://arxiv.org/html/2503.18666v3)).
- **Longitudinal user-belief graph (`hai memory`-like).**
  A-MEM-style typed beliefs about the user, retroactively editable
  on new evidence. Stored as a graph in SQLite, not a vector blob.
  Belief example: "Dom's running RPE on Z2 days has drifted +1
  over 6 weeks; this changes how 'easy' should be scoped in
  recommendations"
  ([A-MEM NeurIPS 2025](https://arxiv.org/abs/2502.12110),
  [Mnemosyne 2025]).
- **Insight-derived experiment proposals.** A pattern-detection
  surface on top of the v0.5 evidence ledger surfaces candidate
  hypotheses. User reviews + commits; commit creates an experiment
  via the v0.5 substrate. Pattern detection is mechanical (stable
  changes in a metric over a window), not LLM-judged.

**Does not ship.**
- No silent threshold tuning. Every mutation is user-approved.
- No model retraining of any kind. Adaptation moves thresholds
  and rules; it does not learn weights.
- No diagnostic claims. The belief graph carries observations and
  user-confirmed hypotheses; it never carries diagnoses.

**Acceptance criteria** to be set at v0.6 retro based on evidence
about whether the v0.5 + v0.6 substrate is producing useful
candidate adaptations or noise.

**Evidence anchor.** Brief 3 (personal-health-agent literature):
A-MEM, Mnemosyne, AgentSpec all 2025; memory + governed adaptation
are the unsolved problems where a small-team local-first runtime is
well-positioned. Brief 1 (privacy): graph-structured local memory is
inspectable in a way embedding stores are not.

---

### v1.0 — Public stable release

**Goal.** Declare the local-first governed personal-health-agent
runtime stable. Commit to backward compatibility on the CLI
contract, capability manifest, ledger schemas, and exit-code
semantics.

**Ships.**
- Versioned CLI contract with documented deprecation policy.
- Capability-manifest schema versioning.
- All ledger schemas hit normative status (no further breaking
  migrations without a v2.0 release).
- A first contributor-added domain (proof of v0.3 extension
  contract).
- A first contributor-added pull adapter (proof of v0.3 conformance
  tests).

**Acceptance.**
- Three months of zero-incident operation post-v0.7 across
  governed-adaptation channel.
- Independent third-party install + daily-driver use for ≥ 30
  days produces no schema-breaking issues.
- Standards mapping doc references at least one shipped exporter
  (Open mHealth JSON, FHIR R4 Observation bundle, or Apple
  HealthKit-shaped JSON) that a third party has consumed.
- **Fork survivability:** someone who has not previously
  interacted with the maintainer can clone the repo,
  `pipx install`, and reach first useful output in < 30 minutes
  using only the project's own docs (§ 5b.3).
- **Round-trip contributor flow:** a hypothetical first
  contributor-added domain (v1.0 ships criterion above) was
  reviewed + merged using only the materials the project ships,
  not maintainer hand-holding.

---

## 5. Novel / risky bets (the "outside-the-box" layer)

These are speculative. Some belong in the roadmap above; some are
options that may or may not make the cut. Stated here so they don't
get lost between releases.

### 5.1 Vendor algorithm drift as a first-class research surface

**Status (Decision 2, settled 2026-04-25).** *Cautious yes.*
Internal detection is committed (v0.3, W51 evolution above). Public
dataset is committed *in principle* but publication is gated on
explicit legal review with real data in hand. The substrate
accumulates from v0.3 onward; the publish/no-publish decision is
deferred to v0.7+ when there is actual multi-vendor multi-window
evidence to evaluate. A v0.7 retro item: take legal advice on the
specific dataset shape before any public release.

**The bet.** The project becomes the credible reference for "how
does silent vendor algorithm drift affect longitudinal personal
health data?" by *measuring* it. When Garmin / Whoop / Oura push
an update, the runtime detects it (W51 v0.3 evolution), persists
the before/after window, and over time builds a dataset of "what
happened to the same user's metrics across an algorithm change."

**Risk.** Vendors may not appreciate this. Could draw legal
attention. Could also be exactly the artifact that makes the
project credible to the wearable-research community. The v0.7
legal-review gate is the mitigation.

**Why it's worth considering.** Brain imaging is the only field
that has formally solved the algorithm-drift problem. The consumer
wearable space is wide open and the W51 substrate is the obvious
foundation.

### 5.2 Local LLM-judge as the project's release-gate eval

**Status.** *Partially committed.* W58 ships the per-weekly-review
factuality gate in v0.1.9 (Decision 1). Promoting the same judge
to a *release-gate* metric over a fixed fixture set is the
speculative extension. Decide at v0.2 retro after W58 has 3
months of operating data.

**Bet.** Every release ships only after a local Prometheus-2-7B
judge, pinned by SHA, scores the candidate weekly review +
synthesis output above threshold on a fixed fixture set. This
becomes the project's headline quality bar, replacing the current
"1943 → 2038 tests passed" metric with "Prometheus-judged
factuality score of 4.6/5 over fixture set X."

**Risk.** Judge drift if the local model is ever updated. Mitigation:
pin the SHA and update only with a deliberate re-baseline cycle.

**Why it's worth considering.** PDSQI-9 demonstrates LLM-as-judge
at ICC=0.818 vs human raters
([npj Digital Medicine 2025](https://www.nature.com/articles/s41746-025-02005-2)).
Replacing or augmenting test counts with grounded-faithfulness
scores is a credibility upgrade for a runtime claiming to do
serious work.

### 5.3 Personal evidence as research export

**Status.** *Speculative — post-v1.0 candidate.* Depends on (a) the
v0.5 evidence ledger being mature, (b) at least one user beyond
Dom existing, (c) the Open Humans / equivalent integration being
worth the privacy review burden. Decide at v1.0 retro.

**Bet.** v1.0+ ships a "research export" mode: with explicit user
opt-in, the (recommendation, compliance, outcome, classified_state)
triple ledger exports as a citable N-of-1 dataset in a research-grade
format (Open mHealth + de-identified). Users can contribute their
data to public repositories like
[Open Humans](https://www.openhumans.org/) without leaving the
local-first runtime.

**Risk.** Privacy footgun if the de-identification is weak. Heavy
review burden.

**Why it's worth considering.** No personal-health platform offers
this. The evidence ledger is uniquely well-shaped for it. Could
become a flagship "your data became citable science" affordance.

### 5.4 Voice / ambient intake

**Status.** *v0.4 candidate* — slot-in alongside the local-LLM
optional pathway already committed for v0.4. Tractable because
Whisper local transcription is mature and the structured-extraction
step lands naturally on top of `hai intake nutrition` /
`hai intake context-note`. Decide concrete scope at v0.3 retro
once the local-LLM substrate is real.

**Bet.** A voice intake surface (Whisper local transcription →
structured extraction via local LLM → typed `hai intake` call) makes
nutrition + subjective-state logging frictionless enough to actually
happen. Currently the project depends on the user typing into a CLI;
nutrition logging is the failure mode.

**Risk.** Speech recognition errors propagate into typed ledgers if
the structured-extraction step is too lenient.

**Why it's worth considering.** Brief 4 (privacy): Whisper runs
locally. Brief 1 (privacy): low-friction intake is what makes a
daily-driver actually used. Brief 3 (personal-health-agent): Bloom /
GPTCoach show LLMs editing structured plans via dialogue is a
working shape.

### 5.5 Multi-modal evidence

**Status.** *Speculative — post-v0.5 candidate at earliest.*
Depends on (a) 5.4 voice intake having shipped and shown value,
(b) consumer multi-modal local models being demonstrably accurate
on food / exercise images. Macro-from-photo is unsolved even in
commercial apps; not worth committing to before v0.5.

**Bet.** Photo of food → structured macro estimate via a local
multi-modal model. Photo of a barbell setup → exercise + plate count
estimate. Voice note from a run → `hai intake context-note`
structured into the runtime.

**Risk.** Compute hungrier than text-only paths; accuracy of food
macro estimation is currently weak even in commercial apps.

**Why it's worth considering.** Multi-modal local models cleared the
threshold for usability in 2026
([Cactus](https://www.infoq.com/news/2025/12/cactus-on-device-inference/)).
Nutrition logging is the persistent hole in the runtime's evidence
chain; lowering its friction is the highest-leverage UX move.

### 5.6 Federated cohort comparison (post-v1.0)

**Bet.** Local Differential Privacy lets opt-in users contribute
noised aggregates to a "people like me" comparison surface without
exfiltrating raw data ([Apple ML
Research](https://machinelearning.apple.com/research/differential-privacy-aggregate-trends)).
A user opts in to "compare my recovery distribution to other
40-year-old runners" and gets a band, not a leaderboard.

**Risk.** Requires multiple users — N=1 today. Cohort surface only
becomes meaningful at N≥100. Defer until the project has a community.

**Why it's worth considering.** It's the first serious
post-single-user move that doesn't require giving up local-first.

### 5.7 Reasoning trace as research artifact

**Status.** *v0.4 candidate.* The per-recommendation reasoning trace
falls naturally out of the existing X-rule provenance + the v0.4
signed audit log. Cheap to ship if v0.4 is shipping anyway. Decide
concrete scope at v0.3 retro.

**Bet.** Every X-rule firing already has provenance (which signals
triggered, which thresholds were crossed). Surface this as a
"reasoning trace" exportable per-recommendation: an inspectable
chain showing the system's logic from raw evidence to final action.
Pair with the v0.4 signed audit log, the trace becomes
cryptographically attributable.

**Risk.** Adds a per-recommendation cost (storage + render).

**Why it's worth considering.** No competitor provides this. It's
the literal embodiment of the project's "audit-chain over chatbot"
positioning. AgentSpec's runtime enforcement model is the closest
prior art ([arXiv 2503.18666](https://arxiv.org/html/2503.18666v3)).

### 5.8 Inverted MCP — expose Proposals, not data

**Status (Decision 3, settled 2026-04-25).** *Committed to v0.4
as Option C.* Default mode is governance-only (Proposals,
capabilities, governed `hai stats` summaries); a documented
personal raw-access switch handles the maintainer's own host-LLM
use without weakening the public face.

**Bet.** Most personal-health MCP servers (Garmy, Pierre, Open
Wearables, Apple Health MCP, ten others) expose raw rows to a
host LLM. The project's MCP defaults to typed Proposals + the
capabilities manifest + the exit-code contract. Other agents
consume the project's *governance*, not its data.

**Risk.** Smaller adoption surface; some agents will want the raw
rows the project refuses to expose by default. Mitigation: the
opt-in raw-access mode preserves personal-use ergonomics without
making governance optional for third-party agents.

**Why it's worth considering.** Brief 8 (comparable OSS): the
inversion is what defines the new category. The project's
compounding advantage is the governance contract, not the data.

---

## 5b. Organizational substrate (added round-2)

The technical roadmap above describes 14-18 months of focused work
by a solo maintainer. The single biggest predictor of whether any
of that ships is the *organizational* substrate, not the technical
one. This section names the gap and takes positions on it.

### 5b.1 What the survivor evidence says

From the round-2 sustainability research (cited bibliography in
§ 9):

- **Golden Cheetah** (2006-present, 20 years, v3.6+) survived
  because Sean Rhea handed leadership to Mark Liversedge in 2010
  *when his life changed*, rather than walking away silently.
  Successor named before it was needed.
- **Nightscout / OpenAPS** are the only personal-health OSS that
  unambiguously hit v1.0+ with mass adoption. Three reasons:
  life-or-death problem (T1D) created a contributor flywheel,
  Nightscout Foundation 501(c)(3) holds infra and IP, and
  governance is volunteer-DIY with explicit "we are not waiting"
  cultural norms.
- **GarminDB** (solo-led, 30 contributors, ~2k commits) survives
  because the maintainer enforced low-friction contribution rules:
  PRs to `develop`, mandatory `make flake8`, contributors file.
  Codebase is small enough to fork — bus-factor is survivable.
- **Booklore** (10k stars, deleted overnight in early 2026 by
  solo maintainer after AI-PR controversy + planned rug-pull
  license change). Pattern: solo + no governance + monetization
  pivot under stress = sudden death. Forked as Grimmory by
  ex-contributors.
- **RUNALYZE** killed its OSS edition in 2019 because server/infra
  costs outpaced the freemium model; hosted variant survives.

### 5b.2 Funding reality

Brutal but specific:
- **NIH SBIR Phase I** ($275k, 6-12 months) requires a for-profit
  US small biz; sole proprietors not eligible without
  incorporating ([SBIR FAQs](https://sbir.org/nih/nih-sbir-program-faqs/)).
- **Sloan Foundation "Better Software for Science"** is *closed
  to new proposals*; "Open Source in Science" funds institutions
  and OSPOs, not solo developers
  ([Sloan](https://sloan.org/programs/digital-technology/open-source-in-science)).
- **GitHub Sponsors / Open Collective** is realistically a tip
  jar; viable as a signal, not as compensation.
- **60% of OSS maintainers are unpaid; 60% have considered
  quitting** ([Socket](https://socket.dev/blog/the-unpaid-backbone-of-open-source)).

Wishful planning ("we'll get a Sloan grant") is the failure mode
the doc avoids.

### 5b.3 Positions taken (provisional, audit-ready)

The following are positions, not commitments. Each can be revisited
at the v0.5 retro at latest.

- **Project posture: hobby project with successor protocol.** The
  project is not currently incorporated and not currently funded
  beyond the maintainer's time. Any release-proof should state
  this honestly so a third-party install carries no implied SLA.
- **Successor protocol must exist by v0.5 ship.** Modeled on
  Golden Cheetah's named-handoff. A `MAINTAINERS.md` file should
  name (a) the maintainer, (b) the contact for handoff, (c) the
  fork-friendly license posture, (d) the explicit "if I disappear
  for 90 days, do X" instruction. Cheap to write; high-value when
  needed.
- **Contributor-friendliness as v1.0 release gate.** Borrow
  GarminDB's pattern: typed contracts at the `hai` CLI boundary
  (already shipped), `CONTRIBUTING.md` with a 10-minute
  onboarding, mandatory lint, and a `develop` branch. Add a "fork
  survivability" criterion: *can someone clone this and run it in
  < 30 min without the maintainer's help?* If no, that's a v1.0
  blocker.
- **Funding stance: tip-jar, not grant-funded.** GitHub Sponsors
  / Open Collective open by v0.5 with no expectation of revenue.
  Strike NIH SBIR / Sloan / EU Horizon from any future planning
  unless the maintainer chooses to incorporate (which is itself a
  separate decision).
- **No monetization pivot under stress.** This is the rule, not a
  forecast. Booklore's failure mode is well-documented; the
  prophylactic is a written-down commitment to the OSS license
  and self-host posture before the project is ever profitable.

### 5b.4 What this changes in the roadmap

- v0.5 acceptance gains a new criterion: `MAINTAINERS.md` exists
  and names the successor protocol.
- v1.0 acceptance gains a new criterion: third-party clone +
  `pipx install` + first useful output in < 30 min by someone
  who has not previously interacted with the maintainer.
- The v0.3 "First-run UX triad" workstream (§ 4) directly feeds
  the v1.0 fork-survivability criterion.

---

## 6. Risk register

Cross-cutting risks not specific to any release.

### R1. Scope creep into clinical territory

**Risk.** Outcomes accumulate, the system becomes more useful, the
temptation to make claims about diagnosis or treatment grows.

**Mitigation.** Hard line in `non_goals.md` (refreshed in W57). Every
release proof has an "no clinical claims" check. Codex audits each
release for non-goal drift.

### R2. Maintainer burnout

**Risk.** One maintainer; a multi-release roadmap of this scope.

**Mitigation.** v0.3 ships extension contracts so contributor onboarding
is feasible. Skip-or-defer is always allowed; "shipped less than
planned" is fine; "shipped wrong" is not.

### R3. Vendor (Garmin / intervals.icu) breakage

**Risk.** Garmin's CSV export changes shape; intervals.icu's API
changes. The runtime breaks downstream.

**Mitigation.** Adapter conformance tests (v0.3) catch shape drift
on every CI run. Multiple-source reconciliation (v0.3) lets the
runtime degrade gracefully when one source disappears.

### R4. Local LLM regressions

**Risk.** A future Llama / Phi update degrades on the project's
factuality-judge fixture set. Releases stop passing the W58 gate.

**Mitigation.** Pin the local judge model SHA. Re-baseline only on a
deliberate cycle. Treat the judge as a load-bearing dependency.

### R5. Codex audit cadence drops

**Risk.** Project ships changes without external review; quality
slowly drifts.

**Mitigation.** Every release has a Codex audit with structured
prompt (template established v0.1.6 → v0.1.8). The audit cadence is
non-negotiable; if Codex isn't available, ship is delayed.

### R6. Regulatory shift

**Risk.** EU AI Act enforcement clarifies in a way that classifies
the runtime as a regulated medical device.

**Mitigation.** Wellness positioning + non-clinical claims doctrine
+ explicit "wellness support, not medical prescription" in user-
facing surfaces. Track 
[EDPB AI guidance](https://petrieflom.law.harvard.edu/2025/02/24/europe-tightens-data-protection-rules-for-ai-models-and-its-a-big-deal-for-healthcare-and-life-sciences/)
and FDA software-as-medical-device thresholds.

### R7. Hypothesis falsification

**Risk.** One of the five H-hypotheses turns out wrong (e.g. memory
is *not* the unsolved problem; multi-agent ships at consumer scale).

**Mitigation.** Each hypothesis has a falsification criterion. If
any H-hypothesis fails, an extraordinary roadmap re-audit is
triggered before the next release.

### R8. Sustainability anti-patterns (added round-2)

**Risk.** Three specific failure modes from the survivor-vs-failure
research that have killed comparable solo OSS:
1. **AI-generated PR floods** overwhelming the maintainer's review
   bandwidth (Booklore, early 2026). Hostile contribution velocity
   drains review time without producing usable code.
2. **Silent scope expansion** past the maintainer's actual hardware
   (e.g. adding adapters for wearables they don't own; adding
   domains they don't personally use). The runtime can't be
   dog-fooded on data the maintainer doesn't have.
3. **Monetization pivot under burnout stress** (Booklore again).
   Switching from OSS to license-restricted under stress kills
   community trust faster than slow decline does.

**Mitigation.**
- (1) `CONTRIBUTING.md` requires PRs to cite the issue they
  address; AI-generated PRs without prior issue acknowledgement
  are closed by default.
- (2) New domain / adapter contributions require the contributor
  to be the primary user of the affected hardware for ≥ 30 days
  *before* the PR is reviewed. The maintainer-as-user rule applies
  to contributors too.
- (3) The § 5b.3 written-down commitment to the OSS license + self-
  host posture is the prophylactic. Reviewed at every Codex audit.

---

## 7. Falsification criteria

Things that, if observed, should make us cut a feature mid-cycle.

| Feature | Cut if |
|---|---|
| W58 LLM-judge factuality gate | After 3 months of operation, the gate has never blocked a delivery — it's not catching real failures. |
| BCTO tagging | After 6 months, the weekly-review aggregation by BCT tag is never user-consulted — the abstraction isn't earning its weight. |
| Adapter conformance tests | After v0.3 lands, no third party uses the template within 6 months — the contract is too rigid or the audience doesn't exist. |
| MCP server (v0.4) | A real second-agent integration produces no measurable value over the CLI surface — the inversion isn't paying off. |
| `hai experiment` (v0.5) | After 6 months, fewer than 3 distinct experiments have been run — the substrate is sound but the workflow isn't real. |
| Causal estimator (v0.6) | The estimator's output disagrees with the user's lived experience more often than it agrees — the model is wrong for personal data. |
| Governed adaptation (v0.7) | User approves every proposed mutation without reading, OR rejects so many that the channel is unused. Both indicate the substrate is wrong. |
| Vendor algorithm drift detection | After 12 months, no detected algorithm change has correlated with a measurable user-facing metric shift — the signal isn't real. |

---

## 8. Open questions

Intentionally unresolved decisions for Dom + future Codex audits.

1. **Should `hai memory` (v0.7) use a graph database or stay on
   SQLite with a graph projection?** A-MEM uses a knowledge graph;
   the project's existing SQLite substrate is the strongest local
   primitive. Defer until v0.6 when the substrate's evidence load
   is known.

2. **What's the policy for re-baselining the LLM judge?** Once a
   year? On a measurable accuracy drop? Only on user request? The
   answer affects whether v0.1.9's W58 gate is a moving target.

3. **Should the v0.2 BCTO tags be skill-authored or runtime-stamped?**
   Skill-authored matches the code-vs-skill boundary; runtime-stamped
   is more deterministic. Both are defensible.

4. **Does the v0.4 MCP server expose `hai stats` reads or only
   Proposal writes?** Strictly Proposal-only is the cleanest
   inversion; allowing read-only stats is more useful for second
   agents.

5. **Is the v0.5 experiment ledger user-facing or agent-facing?**
   I.e. does Dom-the-user click "start an experiment" via CLI, or
   does the agent propose experiments based on observed patterns?
   Both are possible; both have UX implications.

6. **Does v0.7's governed adaptation operate on per-user thresholds
   only, or can it propose adapting the *default* thresholds the
   project ships with?** The latter is a contributor-feedback channel;
   the former is per-user only. Different governance shapes.

7. **At what point is "v1.0" the right label?** Tied to feature-
   completeness, to a public-API stability commitment, to a marketing
   moment, or to evidence the runtime is being daily-used by
   third parties?

8. **Should the project publish the policy DSL (R-rules + X-rules)
   as an artifact independently of the runtime?** Comparable-OSS
   brief flagged this as a credibility move. Is it worth the
   maintenance cost of two artifacts?

9. **Is the runtime's eventual home a single repository, or does
   `health-agent-infra` become "the runtime + skills" with
   `health-agent-research` as a sibling for evals + N-of-1
   datasets?** Affects how v0.5+ research artifacts get versioned
   and shared.

---

## 9. Source bibliography

Grouped by the research brief that surfaced each. Brief titles
match the eight parallel research agents that produced this
synthesis.

### Personal-health-agent literature (Brief 3)
- [The Anatomy of a Personal Health Agent (Google, arXiv 2508.20148, Aug 2025)](https://arxiv.org/abs/2508.20148)
- [PHIA: Transforming Wearable Data into Personal Health Insights (Merrill et al., Nature Comm. 2025)](https://www.nature.com/articles/s41467-025-67922-y)
- [SePA: Search-enhanced Predictive Agent for Personalized Health Coaching (arXiv 2509.04752, Sep 2025)](https://arxiv.org/abs/2509.04752)
- [Bloom / GPTCoach: LLM-augmented behaviour change (arXiv 2510.05449, Oct 2025)](https://arxiv.org/html/2510.05449v1)
- [Offline Policy Evaluation of Multi-Turn LLM Health Coaching (arXiv 2510.17173, Oct 2025)](https://arxiv.org/html/2510.17173)
- [LifeAgentBench (arXiv 2601.13880, Jan 2026)](https://arxiv.org/abs/2601.13880)
- [A-MEM: Agentic Memory for LLM Agents (NeurIPS 2025, arXiv 2502.12110)](https://arxiv.org/abs/2502.12110)
- [Enabling Personalized Long-term Interactions (arXiv 2510.07925)](https://arxiv.org/abs/2510.07925)
- [AgentSpec: Customizable Runtime Enforcement (arXiv 2503.18666)](https://arxiv.org/html/2503.18666v3)
- [Single-Agent vs Multi-Agent Systems Under Equal Token Budgets (arXiv 2604.02460)](https://arxiv.org/html/2604.02460v1)
- [PDSQI-9 LLM-as-Judge (npj Digital Medicine 2025)](https://www.nature.com/articles/s41746-025-02005-2)
- [WHOOP Coach + OpenAI](https://openai.com/index/whoop/)
- [Oura Advisor announcement](https://ouraring.com/blog/oura-advisor/)
- [Apple Health+ shelved (Feb 2026)](https://livity-app.com/en/blog/apple-health-ai-coach-shelved)
- [Cactus on-device LLM runtime](https://www.infoq.com/news/2025/12/cactus-on-device-inference/)

### JITAI + behaviour change ontology (Brief 2)
- [The Behaviour Change Technique Ontology (Wellcome Open Research 2023)](https://wellcomeopenresearch.org/articles/8-308)
- [JITAI/EMI mental health meta-analysis 2025 (PMC12481328)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12481328/)
- [Sleep JITAI MRT (JMIR 2024)](https://www.jmir.org/2024/1/e49669)
- [Workplace stress JITAI tailoring variables (JMIR Mental Health 2024)](https://mental.jmir.org/2024/1/e48974)
- [Beyond JITAIs in mental health (Frontiers Digital Health 2025)](https://www.frontiersin.org/journals/digital-health/articles/10.3389/fdgth.2025.1460167/full)
- [Social-support JITAI for depression (JMIR Mental Health 2025)](https://mental.jmir.org/2025/1/e74103)
- [AI in clinical trials gap, CONSORT 2025 (Lancet)](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(25)01268-1/fulltext)

### N-of-1 infrastructure (Brief 4)
- [StudyMe paper (Trials 2022)](https://link.springer.com/article/10.1186/s13063-022-06893-7)
- [StudyU GitHub](https://github.com/hpi-studyu/studyu)
- [International Collaborative Network for N-of-1 Trials and SCED](https://www.nof1sced.org/)
- [HDSR Special Issue 3: Personalized N-of-1 Trials (2024)](https://hdsr.mitpress.mit.edu/pub/b6efwlql)
- [Bayesian Models for N-of-1 Trials (PMC 10817775)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10817775/)
- [Alcohol-abstinence N-of-1 case study (BMC Med Res Methodol 2025)](https://link.springer.com/article/10.1186/s12874-025-02738-4)

### Privacy / local-first (Brief 1)
- [Local-first software (Kleppmann 2019)](https://martin.kleppmann.com/2019/10/23/local-first-at-onward.html)
- [Local-first apps overview 2025](https://debugg.ai/resources/local-first-apps-2025-crdts-replication-edge-storage-offline-sync)
- [FAItH federated analytics (Nature Sci Rep 2025)](https://www.nature.com/articles/s41598-025-94501-4)
- [Inrupt VITO health-data case study](https://www.inrupt.com/case-study/vito-securely-shares-personal-health-data-using-solid)
- [Apple ML Research on differential privacy](https://machinelearning.apple.com/research/differential-privacy-aggregate-trends)
- [SQLCipher / Turso writeup](https://turso.tech/blog/fully-open-source-encryption-for-sqlite-b3858225)
- [Rekor design](https://docs.sigstore.dev/logging/overview/)
- [Tamper-evident logging (CCS 2025)](https://dl.acm.org/doi/10.1145/3719027.3765024)
- [Local LLMs on Apple Silicon 2026](https://www.sitepoint.com/local-llms-apple-silicon-mac-2026/)
- [Petrie-Flom on EU AI / health](https://petrieflom.law.harvard.edu/2025/02/24/europe-tightens-data-protection-rules-for-ai-models-and-its-a-big-deal-for-healthcare-and-life-sciences/)

### Wearable accuracy + data quality (Brief 5)
- [Birrer et al., six wearables vs PSG (SLEEP Advances 2025)](https://academic.oup.com/sleepadvances/article/6/2/zpaf021/8090472)
- [Lee et al., 11 sleep trackers (JMIR mHealth 2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10654909/)
- [Dial et al., HRV/RHR validation (Physiological Reports 2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12367097/)
- [Reliability in wearable sleep staging (npj Digital Medicine 2024)](https://www.nature.com/articles/s41746-024-01016-9)
- [Vendor algorithm customisation (SLEEP 2025)](https://academic.oup.com/sleep/article/48/4/zsaf011/7953384)
- [Multisensor data fusion review (arXiv 2412.05895)](https://arxiv.org/abs/2412.05895)
- [Identifying Data Quality Dimensions for Person-Generated Wearable Data (PMC8738984)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8738984/)
- [Missingness mechanism in wearable sleep data (JMIR mHealth 2026)](https://mhealth.jmir.org/2026/1/e81123)
- [Oura calibration windows](https://support.ouraring.com/hc/en-us/articles/360025589793-Readiness-Score)

### FHIR / interop (Brief 6)
- [Open@Epic announcement](https://www.epic.com/epic/post/openepic-highlights-expanded-data-connections-for-developers-and-patients/)
- [Apple Health Records technical requirements](https://support.apple.com/guide/healthregister/technical-requirements-specifications-health-apd12d144779/web)
- [Apple Share with Provider FAQ](https://support.apple.com/guide/healthregister/health-app-data-share-with-provider-faq-apd531bc6215/web)
- [openmhealth/schemas GitHub](https://github.com/openmhealth/schemas)
- [IEEE 1752.1-2021 standard](https://standards.ieee.org/ieee/1752.1/6982/)
- [the-momentum/open-wearables](https://github.com/the-momentum/open-wearables)
- [FHIR R4 Goal.lifecycleStatus value set](https://hl7.org/fhir/R4/valueset-goal-status.html)

### Causal inference + LLM-as-judge (Brief 8)
- [Causal inference for N-of-1 trials (Piccininni & Stensrud, arXiv 2406.10360)](https://arxiv.org/abs/2406.10360)
- [Person as Population (Daza, arXiv 1901.03423)](https://arxiv.org/abs/1901.03423)
- [Causal Analysis of Self-tracked Time Series (Daza, PMC6087468)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6087468/)
- [TARGET Statement for Target Trial Emulation (JAMA 2025)](https://jamanetwork.com/journals/jama/fullarticle/2837724)
- [DoWhy](https://github.com/py-why/dowhy)
- [CausalImpact (Brodersen et al.)](https://research.google.com/pubs/archive/41854.pdf)
- [N-of-1 wearable HRV/sleep VAR study (PMC9823534)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9823534/)
- [LLM-as-Judge survey (arXiv 2411.15594)](https://arxiv.org/abs/2411.15594)
- [LLM Output Drift (arXiv 2511.07585)](https://arxiv.org/pdf/2511.07585)
- [Prometheus 2 paper](https://arxiv.org/abs/2405.01535)
- [Prometheus-eval repo](https://github.com/prometheus-eval/prometheus-eval)
- [Mozilla local LLM-as-judge stack](https://blog.mozilla.ai/local-llm-as-judge-evaluation-with-lm-buddy-prometheus-and-llamafile/)

### Comparable OSS landscape (Brief 7)
- [GarminDB](https://github.com/tcgoetz/GarminDB)
- [garmin-grafana](https://github.com/arpanghosh8453/garmin-grafana)
- [Open Wearables (the-momentum)](https://github.com/the-momentum/open-wearables)
- [Endurain (self-hosted Strava alternative)](https://github.com/joaovitoriasilva/endurain)
- [Golden Cheetah](https://github.com/GoldenCheetah/GoldenCheetah)
- [Garmy (CLI + MCP for Garmin)](https://github.com/bes-dev/garmy)
- [openCHA / CHA](https://github.com/Institute4FutureHealth/CHA)
- [Pierre (multi-vendor MCP)](https://www.pierre.dev/)

### OSS sustainability (Round-2 brief)
- [Golden Cheetah handoff history](https://nyvelocity.com/articles/coachingfitness/golden-cheetah-open-source-goodness/)
- [Nightscout Foundation](https://www.nightscoutfoundation.org/about)
- [Nightscout Wikipedia](https://en.wikipedia.org/wiki/Nightscout)
- [OpenAPS](https://openaps.org/)
- [Open Humans Foundation](https://www.openhumans.org/about/)
- [RUNALYZE OSS abandonment forum thread](https://forum.runalyze.com/viewtopic.php?t=1176)
- [Booklore postmortem (XDA)](https://www.xda-developers.com/single-maintainer-open-source-ticking-time-bomb/)
- [QS Access stalled](https://forum.quantifiedself.com/t/a-note-about-the-qs-access-app-and-ios-13/7355)
- [NIH SBIR FAQs (eligibility)](https://sbir.org/nih/nih-sbir-program-faqs/)
- [Sloan Open Source in Science](https://sloan.org/programs/digital-technology/open-source-in-science)
- [Socket: 60% of OSS maintainers unpaid](https://socket.dev/blog/the-unpaid-backbone-of-open-source)

### First-run UX (Round-2 brief)
- [Hugo Quick Start](https://gohugo.io/getting-started/quick-start/)
- [Pre-commit setup guide](https://stefaniemolin.com/articles/devx/pre-commit/setup-guide/)
- [Ruff Linter docs](https://docs.astral.sh/ruff/linter/)
- [Litestream getting started](https://litestream.io/getting-started/)
- [Datasette getting started](https://docs.datasette.io/en/stable/getting_started.html)
- [Daily.dev 15-Minute Rule (TTFV)](https://business.daily.dev/resources/15-minute-rule-time-to-value-kpi-developer-growth/)
- [AgentSpec capability discovery](https://agents-oss.github.io/agentspec/)
- [Deep Agents CLI](https://docs.langchain.com/oss/python/deepagents/cli/overview)
- ["Ship the Prompt" CLI agent onboarding](https://understandingdata.com/posts/ship-the-prompt-cli-agent-onboarding/)
- [WP-CLI doctor command](https://github.com/wp-cli/doctor-command)
- [BetterCLI help-page design](https://bettercli.org/design/cli-help-page/)
- [Seedfast (synthetic seed data)](https://www.ddaccelerator.com/news/seedfast-makes-database-seeding-fast-clean-and-reliable-straight-from-the-cli)

---

## 10. Implementation log

(Append as work lands.)

- 2026-04-25 — initial draft authored by Claude after v0.1.8
  implementation completed. Synthesised from 8 parallel research
  briefs covering: personal-health-agent literature, JITAI/BCT,
  N-of-1 infrastructure, privacy/local-first, wearable accuracy,
  FHIR ecosystem, comparable OSS, causal-inference/LLM-judge.
  Ready for Codex audit on v0.1.8 ship + this roadmap together.
- 2026-04-26 — round-2 self-review + targeted research before Codex
  audit. Six weak spots surfaced from a critical re-read; two
  research briefs commissioned (OSS sustainability + first-run UX
  for governed CLIs). Doc updates folded in:
  - § 4.0 release-timeline + dependency-chain table (14-18 month
    minimum from v0.1.9 ship to v1.0 ship; § 4 had been silent on
    this).
  - § 4 v0.3: W59 First-run UX triad added (`hai init` + `hai
    demo` + `hai next-step --json` + bundled onboarding agent
    skill). Closes the gap between v1.0's "third-party install +
    30-day daily-driver use" acceptance and the doc being silent
    on the install path.
  - § 4 v0.4: architectural note clarifying the two host-LLM
    paths (maintainer Claude Code vs third-party MCP) share one
    runtime instance; provenance auditable via runtime_event_log.
  - H1 / H4 / H5 falsification criteria reworded to acknowledge
    the structural unmeasurability of population claims at N=1
    and to name the reachable near-term proxies.
  - § 5 novel bets: triage status added to 5.2, 5.3, 5.4, 5.5,
    5.7. Each now carries an explicit committed / candidate /
    speculative / decide-at-vN-retro tag.
  - § 5b NEW "Organizational substrate" section + R8 anti-pattern
    added to risk register. Successor protocol (`MAINTAINERS.md`
    by v0.5 ship), funding-stance honest about NIH SBIR / Sloan
    being closed to solo individuals, fork-survivability as v1.0
    blocker.
  - v0.5 + v1.0 acceptance criteria gain successor-protocol +
    fork-survivability lines.
  - § 9 bibliography extended with round-2 sources.
- 2026-04-25 — three strategic decisions taken with Dom:
  - **Decision 1 (W58, v0.1.9):** factuality judge with
    agent-judge negotiation loop — judge flags → agent fixes or
    defends → exchange logged → only then user sees summary.
  - **Decision 2 (§ 5.1 + W51):** internal vendor-algorithm-drift
    detection in v0.3 (committed). Public dataset committed in
    principle, publication gated on legal review with real data
    (deferred to v0.7+ retro).
  - **Decision 3 (v0.4 MCP):** Option C — governed Proposals +
    capability manifest + governed stats summaries as the public
    face; a documented personal raw-access switch for the
    maintainer's own host-LLM use.
  - **Deferred:** the foundational H1 hypothesis review
    ("interpretability of outcomes > better recommendations") to
    a future session; Dom flagged it deserves more time. Tagged
    in memory as `project_h1_hypothesis_review_deferred.md`.
