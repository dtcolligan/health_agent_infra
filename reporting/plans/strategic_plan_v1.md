# Strategic Plan v1 — Health Agent Infra

> **Status.** Authored 2026-04-27 by Claude in extended planning
> session. Supersedes `historical/multi_release_roadmap.md`
> (2026-04-25). The previous doc lives under `historical/` with a
> pointer here; its hypotheses (H1-H5), category claim, and settled
> decisions are lifted forward intact.
>
> **Audience.** Portfolio-grade — readable to a senior engineer
> opening the project cold; dense enough for the maintainer to
> use as the canonical strategic reference.
>
> **Companion docs.**
> - `tactical_plan_v0_1_x.md` — release-by-release execution.
> - `eval_strategy/v1.md` — how we measure correctness.
> - `success_framework_v1.md` — how we measure project value.
> - `risks_and_open_questions.md` — what could derail this.
> - `README.md` — reading order index.
>
> **Refresh cadence.** Strategic plan reviewed every two minor
> releases (next refresh: post-v0.1.12 ship) or whenever a settled
> decision needs revisiting. Tactical plan refreshed per release.

---

## Table of contents

1. What this project is, in one paragraph
2. Where the project sits in the landscape
3. The thesis: five falsifiable bets
4. Settled decisions (do not reopen casually)
5. Settled-but-now-falsifiable: what v0.1.10 changed
6. Strategic posture for the next 18 months
7. Major waves to v1.0
8. Scope-expansion exploration (speculative)
9. What v1.0 looks like, written today
10. The decision branches between here and v1.0
11. Provenance + how this doc evolves

---

## 1. What this project is, in one paragraph

**Health Agent Infra is a local-first governed runtime + skill set
for daily personal-health decisions across six domains, where a
deterministic Python policy engine owns every band, score, and rule,
and the LLM is allowed only to compose bounded, typed, reviewable
proposals.** The unit of shipping is a Python wheel
(`health-agent-infra`) plus markdown skills consumed by the agent at
runtime. The maintainer's daily-driver loop is Claude Code over the
project's own `hai` CLI; the project is its own dogfood.

A user talks to a host agent in natural language; the agent operates
the local `hai` CLI, reads governed snapshots, uses packaged skills
to compose bounded proposals, and relies on the Python runtime to
validate, reconcile, and commit decisions to local SQLite state.
Three-state audit chain (`proposal_log` → `planned_recommendation` →
`daily_plan` + `recommendation_log` → `review_outcome`) makes every
decision reconstructable.

---

## 2. Where the project sits in the landscape

### 2.1 The category claim

The project occupies a category that does not yet have a name in
public usage. Nearest neighbours:

- **Quantified-self trackers** (QS Ledger, Bearable, Heads Up Health,
  Levels) collect data; do not reason or recommend.
- **Athlete analytics platforms** (TrainingPeaks, intervals.icu,
  Golden Cheetah, RUNALYZE) reason inside one domain (training
  load); do not unify nutrition, sleep, stress, recovery, strength.
- **Health MCP servers** (Garmy, garmin-mcp, whoop-mcp, Open
  Wearables, Pierre, Apple Health MCP) expose raw rows to a host
  LLM with no governance layer.
- **Vendor coaches** (WHOOP Coach, Oura Advisor, Fitbit AI Coach)
  narrate over a fixed proprietary metrics stack on cloud
  infrastructure.
- **Multi-agent personal-health frameworks** (Google PHA, Bloom,
  PHIA, SePA) exist as research papers; none ships in production
  for daily-driver use.

The project is none of these. The accurate description: **a
local-first governed runtime + skill set for daily personal-health
decisions across six domains, where a deterministic policy engine
owns every band, score, and rule, and the LLM is allowed only to
compose bounded, typed, reviewable proposals.**

For brevity in the rest of this doc: **"governed personal-health-agent
runtime."**

### 2.2 What's defensibly differentiated

Cross-checked against the comparable-OSS survey carried forward
from the 2026-04-25 roadmap, four things remain unique:

1. **Deterministic policy engine separated from LLM judgment.** No
   surveyed competitor has both an R-rule layer (per-domain
   forced-action / capped-confidence rules) and an X-rule layer
   (cross-domain Phase A mutations) implemented in code with
   skill-level invariants enforcing they never run in prose. The
   v0.1.9 hardening + v0.1.10 type-coercer make this contract
   robust against bool-as-int silent coercion.

2. **Domain-typed Proposals with explicit safety/abstain semantics.**
   `defer_decision_insufficient_signal` is a first-class action enum
   value in every domain. Nothing in the surveyed landscape ships
   abstention as action. The v0.1.10 partial-day gate on
   R-extreme-deficiency strengthens this — abstain when uncertain
   is now a runtime-enforced behaviour, not just an option.

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

**New as of v0.1.10:** the **persona dogfood harness** under
`verification/dogfood/` is fifth differentiated capability —
permanent regression infrastructure that drives synthetic users
across 8 archetypes through the full pipeline, surfacing
classifier-assumption bugs that single-user dogfood cannot. No
surveyed competitor ships persona-driven regression testing for
their decision layer.

The W51 data-quality ledger (v0.1.8) remains ahead of published
state of the art. Worth flagging because it's the lowest-cost
place to widen the lead.

---

## 3. The thesis: five falsifiable bets

Each is a strategic bet. Each can turn out wrong; each has a
falsification criterion. Stated explicitly so future audits can
ask "is this still true?" rather than re-derive the case. These
are lifted from `historical/multi_release_roadmap.md` (2026-04-25)
with v0.1.10 evidence updates.

### H1. The hard problem in personal health AI is interpretability of outcomes, not better recommendations

**Bet.** The marginal value of a 5% better daily recommendation is
tiny compared to the marginal value of being able to answer "did
anything I changed actually help, and why do I think so?" Core
competence should be the *evidence-and-audit chain*, not the
recommendation algorithm.

**Evidence.** SePA (arXiv 2509.04752) shows personalisation lives in
the per-user predictor; LLM is downstream narration. Apple Mulberry's
shelving (Feb 2026) shows that a better recommendation engine alone
does not ship a product. JITAI meta-analysis (PMC12481328) finds
between-group g=0.15 — the recommendation effect is small. WHOOP
Coach, Oura Advisor, and Fitbit AI Coach all narrate over fixed
metrics stacks and do not silently re-personalise.

**v0.1.10 update.** The morning-briefing dogfood session (memory
B1) demonstrated H1 in action: the agent's *honest defer* on partial
nutrition data was more valuable than a confident wrong answer. The
W-C partial-day gate explicitly encodes "abstention beats false
escalation" as runtime contract.

**Falsification.** Structural caveat: the project has N=1 user (Dom)
today, so "users find X more useful than Y" is unmeasurable until
there's a community. Honest near-term proxy: *if Dom himself, after
using v0.5's N-of-1 substrate for ≥ 90 days, consistently consults
the underlying metrics in preference to the personal-evidence
verdicts, the bet is wrong*. Promotes to a population criterion (≥ a
handful of users in same direction) only post-v1.0 when a community
exists.

**Status:** active, validated by v0.1.10 dogfood.

### H2. Local-first beats hosted for the daily-runtime use case

**Bet.** Privacy + ownership + offline reliability + zero data-egress
beats centralised model freshness for a daily driver that touches
every domain of personal health.

**Evidence.** Cactus + Ollama + MLX clear 38–58 tok/s for 4B-class
models on M2 Pro; Llama 3.1 8B and Phi-7B are usable as judgment
models without cloud round-trip. EU Digital Omnibus + EDPB Opinion
(2025) raise the GDPR bar on training-data lawfulness, making "data
never leaves the device" a legitimate marketing posture. Solid +
sovereignty platforms still lack health PMF — lesson is "useful
local utility drives adoption, not standards." Comparable-OSS
survey: every shipping vendor coach is cloud; the local-first niche
is empty.

**Falsification.** If consumer hardware regresses on local LLM
performance OR a regulator forces a server-side audit trail
incompatible with local-first, the architecture is wrong.

**Status:** active, no v0.1.10 update.

### H3. User-authored intent + targets + bounded supersession is the right substrate for governed adaptation

**Bet.** The W49 intent ledger + W50 target ledger + the existing
proposal/plan supersession discipline form the substrate that makes
*future* governed adaptation possible without becoming a black-box
auto-tuning system. Adaptation belongs on top of this substrate, not
in place of it.

**Evidence.** AgentSpec (arXiv 2503.18666) is the closest published
prior art for runtime enforcement with user-approval-gated rule
mutation; it depends on a substrate of user-authored constraints
exactly like W49/W50. Bloom / GPTCoach (arXiv 2510.05449) shows LLMs
proposing structured mutations to user-owned plans is a working
shape. The project's `hai propose --replace` revision-chain is the
same primitive at a smaller scope.

**v0.1.10 update.** The intent + target commit flow demonstrated in
the morning-briefing session (agent proposes 3300 kcal target →
maintainer commits via `--confirm`) is an N=1 confirmation that the
substrate works for the proposed-by-agent-then-user-commits pattern.

**Falsification.** If, after v0.7 ships governed adaptation, users
either (a) routinely approve every proposed mutation without
reviewing or (b) routinely reject so many that the channel is
unused, the substrate is the wrong shape. Check at the v0.7 review.

**Status:** active.

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
next-actions manifest already operationalises this. Cactus + Ollama
show local single-agent inference is fast enough for interactive
loops.

**v0.1.10 update.** During the morning-briefing dogfood, Claude
followed the W57 governance loop (agent proposes → user commits) for
the first time end-to-end with `--confirm`. The CLI surface
correctly forced the boundary; no shell-into-SQLite escape was
needed for any user-mode workflow.

**Falsification.** Two reachable signals:
1. *Internal:* the project's own daily loop starts shelling into
   SQLite directly because the CLI can't surface what's needed.
   v0.1.10 dogfood session: zero such occurrences (the maintainer's
   one attempt was correctly blocked by AGENTS.md inspection-
   surface rules; agent rerouted to `hai explain`).
2. *External (post-v0.4):* once the MCP ships, second agents that
   integrate either bypass governed surfaces in favour of the
   maintainer raw-access escape hatch, OR refuse to integrate
   because the governed surface is too narrow. Both indicate the
   contract shape is wrong.

**Status:** active, validated by v0.1.10 dogfood.

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

**v0.1.10 update.** v0.1.10 cycle shipped 9 closed workstreams + 36
new tests + a permanent regression harness in a single
single-maintainer session, with the four-round audit pattern intact
and the three-state audit chain unbroken. This is a positive proof
point — the architecture absorbed substantial new work without
ledger-shape changes.

**Falsification.** Structural caveat: the project lacks retention /
"did this help" telemetry today (N=1, no instrumented comparison
set). Reachable near-term signal is the *opposite direction*: if the
project itself starts to need a multi-agent shape to ship the next
release (e.g. v0.7 governed adaptation proves intractable inside the
single-runtime + skill boundary), that's the falsification.
Population-comparison criteria are post-v1.0 only.

**Status:** active.

---

## 4. Settled decisions (do not reopen casually)

These were decided across audit cycles. If you think one needs
revisiting, write a cycle proposal in `reporting/plans/`; do not act
unilaterally. Lifted from AGENTS.md "Settled Decisions" + 2026-04-25
roadmap, refreshed for v0.1.10.

| # | Decision | Why | First settled |
|---|---|---|---|
| **D1** | W37 original shape is dead. Skills do not compute review-outcome pattern tokens. W48 replaced it with code-owned `core/review/summary.py`. | Skill arithmetic violates code-vs-skill boundary. | v0.1.8 |
| **D2** | W39 narrowed: threshold override loading already exists. v0.1.8 scope was validation/diff/auditability, not re-implementation. | Avoid re-implementing solved problem. | v0.1.8 |
| **D3** | W47 cut: keep release-proof/changelog discipline, do not add a working-tree-sensitive changelog test. | Test would be flaky against the cycle pattern itself. | v0.1.8 |
| **D4** | W29 / W30 deferred: do not split `cli.py`, do not freeze the capabilities manifest schema yet. | Refactor cost > benefit until external integration arrives. | v0.1.8 |
| **D5** | Garmin Connect is not the default live source. | Login is rate-limited and unreliable. Default to intervals.icu when configured. | v0.1.6 |
| **D6** | Nutrition v1 is macros-only. | Micronutrients require taxonomy + lookup infrastructure not justified by N=1 utility. | v0.1.x |
| **D7** | No `STATUS.md` parallel file. | Status lives in CHANGELOG, AUDIT, ROADMAP, ARCHITECTURE. | v0.1.x |
| **D8** | LLM-judge for weekly review = factuality only. | Helpfulness/tone judgement is out of scope; clinical claims forbidden. | v0.1.9 (pre-cut) |
| **D9** | Two-shot agent-judge negotiation loop, not infinite. | Bounded resource use; if convergence fails, surface to user as a flagged review. | v0.1.9 (pre-cut) |
| **D10 *(NEW v0.1.10)*** | Persona harness lives in `verification/dogfood/`, not `verification/tests/`. Full matrix runs are not part of CI. | Matrix runtime is minutes-class, not seconds; CI stays fast. | v0.1.10 |
| **D11 *(NEW v0.1.10)*** | The pre-PLAN bug-hunt phase is a permanent pattern, not a one-off. Future substantive releases run a structured hunt before scoping PLAN.md. | v0.1.10 demonstrated the hunt produces ~3× more findings than opportunistic scoping. | v0.1.10 |
| **D12 *(NEW v0.1.10)*** | Every `int(cfg)` / `float(cfg)` / `bool(cfg)` in the runtime must use `core.config.coerce_*` helpers. | Bool-as-int silent coercion is the highest-impact silent bug class; W-A closes it durably. | v0.1.10 |

---

## 5. Settled-but-now-falsifiable: what v0.1.10 changed

Three claims in the 2026-04-25 roadmap turned out false or
needed update after v0.1.10. Naming them so future audits don't
treat them as still-load-bearing.

### 5.1 "Running domain works for intervals.icu users"

The 2026-04-25 roadmap implicitly assumed the running domain
produced useful recommendations for any user with a synced
intervals.icu account. **F-C-03 falsified that.** The
`accepted_running_state_daily` projection read only from the daily
summary row; per-activity rows were never aggregated. Every
intervals.icu user defaulted to "running deferred — insufficient
signal" regardless of how rich their activity log was.

v0.1.10 W-D-ext fixed this. The aggregator existed in code but was
never called. The fix is a 30-line glue change — wire
`aggregate_activities_to_daily_rollup` into the clean flow with
field-name mapping.

**Strategic implication:** assume similar gaps exist elsewhere.
Other "obvious" projection paths may have similar implemented-but-
never-wired aggregators. The v0.1.11 audit phase should sweep for
them explicitly.

### 5.2 "Single-user dogfood is sufficient for catching classifier-assumption bugs"

The 2026-04-25 roadmap treated maintainer dogfood as the primary
quality signal. **The v0.1.10 persona harness falsified that** —
running 8 synthetic personas through the pipeline surfaced 6 bugs
the single-user flow had not exposed across multiple weeks (F-C-01,
F-C-02, F-C-03, F-C-04 reproductions, F-C-05, F-C-08).

**Strategic implication:** persona-driven regression is now
load-bearing infrastructure. The eval strategy doc treats it as a
first-class signal alongside unit tests + scenario fixtures.

### 5.3 "Type-checker findings are nits, not correctness concerns"

The 2026-04-25 roadmap deferred mypy work as polish. **35 mypy
errors discovered in v0.1.10 Phase A include real correctness
concerns** (F-A-03 adapter type confusion, F-A-04 None
propagation, F-A-05 scenario type confusion, F-A-06 None
comparisons, F-A-07 exercise None-into-str, F-A-09 Literal abuse).
W-H is a deferred v0.1.11 workstream now treated as correctness,
not maintenance.

**Strategic implication:** type-checker output is now a first-class
audit signal. Future cycles include mypy delta as a phase A
artifact.

---

## 6. Strategic posture for the next 18 months

Three postures, lifted from 2026-04-25 with v0.1.10 evidence:

### 6.1 Lead with the governance contract, not the data ingest

Adding new wearable adapters is undifferentiated work that a
six-line Garmin-to-SQLite repo can do. The moat is the runtime +
skills + writeback/review loop. Every release should make the
governance contract more legible, more credible, more inspectable,
more exportable — *not* expand the surface area of what the project
ingests.

**Concrete v0.1.10 evidence:** W-D-ext fixed the running-domain gap
by wiring an existing aggregator, NOT by adding a new ingest source.
The fix produced more strategic value than another wearable adapter
would have.

### 6.2 Borrow the commodity, defend the decision layer

Open mHealth / IEEE 1752.1 / FHIR R4 are commodity vocabularies for
data shape. Adopt them where they let third parties consume the
project's data without rewriting integration glue. Do not adopt them
where they force the policy/judgment layer into a clinical
interoperability shape that contradicts the project's wellness-only
positioning.

### 6.3 Ship the credible artifact

The R-rule + X-rule policy DSL is the thing no competitor has and
academia (AgentSpec, policy-as-prompt, Bloom's structured mutations)
is converging toward. It is publishable prior art. Treat it as one.

**v0.1.10 update:** The pre-PLAN bug-hunt pattern + persona harness
are also publishable — "structured pre-release audit with synthetic
personas" is a credible methodology contribution alongside the
runtime architecture.

---

## 7. Major waves to v1.0

The 2026-04-25 roadmap committed to release-by-release detail.
v0.1.10 ships earlier than that doc anticipated; the strategic
shape stays intact. Five waves, each spanning 2-4 minor releases.

### Wave 1 — Hardening + dogfood credibility (v0.1.10–v0.1.13, ~3 months)

**Theme.** Make the existing runtime trustworthy enough to point at.
Persona harness lands (v0.1.10), deferred audit findings close
(v0.1.11–v0.1.12), public surface tightens (v0.1.13). End-state:
external reviewer reading the project cold can verify the governance
contract holds.

**Evidence anchor:** v0.1.10 audit findings + tactical plan v0.1.x.

### Wave 2 — Weekly review + insight ledger (v0.2, ~4-8 weeks post Wave 1)

**Theme.** Make the runtime useful beyond one day. W52 weekly
review + W53 insight proposal ledger + W58 factuality gate
(deterministic claim-block from day 1; LLM-judge layer ships
shadow-by-default with feature-flag flip to blocking once
shadow-mode evidence supports it). Was scoped as v0.1.9 in the
2026-04-25 roadmap; v0.1.9 cut to hardening only, so it slips here.

**Evidence anchor:** Roadmap §4 v0.1.9 (entire scope migrates).
v0.1.12 CP5 reshape: single substantial v0.2.0 with shadow-by-
default LLM judge, not the 3-release split the reconciliation
initially recommended.

### Wave 3 — MCP surface + extension contract (v0.3–v0.4, ~3-4 months)

**Theme.** Make the runtime accessible to second agents and second
data sources. Was v0.3 (extension contracts) + v0.4 (runtime
portability) in the 2026-04-25 roadmap. Sequence preserved.

**Evidence anchor:** Roadmap §4 v0.3 + v0.4. PHIA + Bloom integration
prior art.

**Staging within Wave 3 (added v0.1.12 CP4).**

- **v0.3** — *plans* MCP server. Read-surface design only (no
  write surface). Threat-model artifact authored at
  `reporting/docs/mcp_threat_model.md`. Provenance import
  contract drafted (extends the agent-CLI capabilities manifest
  with provenance fields per imported row).
- **v0.4** — *prereqs land*. Least-privilege read-scope model
  documented (per-table read scopes, no cross-table joins
  exposed). Threat-model doc completes with mitigations for
  resource audience validation, confused-deputy risk, token-
  passthrough risk, SSRF risk. Provenance contract enforced
  through one full domain end-to-end (recovery is the smallest
  surface).
- **v0.4-or-v0.5** — *ships* MCP read surface. Gated on the
  prereqs above. **No write surface ever.** All mutating CLI
  commands (`hai propose`, `hai daily`, `hai review record`,
  `hai intent commit`, `hai target commit`, all `hai intake *`)
  remain agent-CLI-only (W57 invariant preserved at the MCP
  boundary).

**Security gate (non-negotiable).** No MCP read surface ships
before the threat-model artifact, the least-privilege scope
model, and the one-domain provenance proof are all in place.
Sources for threat-model authoring (verify current at v0.4):

- <https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization>
- <https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices>

### Wave 4 — N-of-1 substrate + estimator (v0.5–v0.6, requires ≥ 90d v0.5 substrate)

**Theme.** The (recommendation, compliance, outcome,
classified_state) triple ledger + the analyzer that reads it.
Substrate-then-estimator dependency chain is intact from
2026-04-25. Earliest end-of-Wave-4 ship: 2027-Q1 in optimistic case.

**Evidence anchor:** Roadmap §4 v0.5 + v0.6. SePA (predictor lives
per-user) + StudyU (N-of-1 trial substrate).

### Wave 5 — Governed adaptation + v1.0 stability (v0.7–v1.0)

**Theme.** Substrate-validated mutation proposals + 90-day
zero-incident stability proof. v1.0 is the operational claim, not a
feature claim.

**Evidence anchor:** Roadmap §4 v0.7 + v1.0. AgentSpec runtime
enforcement.

### Total horizon

Optimistic: 14-18 months from v0.1.10 (April 2026) to v1.0 ship —
late 2027. Realistic: 18-24 months — early-to-mid 2028. The
substrate-maturation gates (v0.5 → 90d → v0.6, v0.7 → 90d → v1.0)
cannot be compressed; they are evidence-driven, not willpower-driven.

---

## 8. Scope-expansion exploration (speculative)

Maintainer authorised speculative scope-expansion thinking provided
each candidate is flagged speculative-not-committed and carries an
explicit "decision needed by" date. None of the below is in scope
for v0.1.x or v0.2; they are decision-points for v0.3+.

### 8.1 New domains

| Candidate | What it would mean | Maintainer instinct (rough) | Decision needed by |
|---|---|---|---|
| **Mental health proxy domain** (mood, anxiety, mindfulness consistency) | Add seventh domain with its own classifier + skill. Tight scope: subjective mood scale + meditation logging. | Defer to v0.7+. The data-source gap is severe; subjective-only domain produces low-coverage recommendations. Reconsider if Apple Health / Garmin start exposing mood-stamping cleanly. | v0.6 review |
| **Cycling-specific running-equivalent** | Distinguish run from cycle in the running domain (currently `cross_train` is a catch-all). | Yes for v0.5+ — the persona matrix already includes a triathlete (P5) where this gap is visible. | v0.4 review |
| **Rehab / return-to-sport domain** | Track a specific injury recovery curve, downgrade load recommendations against rehab-aware thresholds. | Hard no for v1.0. Crosses the no-clinical-claims invariant. Defer to a v2.0 medical-grade fork OR a separate project. | Not before v1.0 |

### 8.2 New data sources

| Candidate | What it would mean | Decision needed by |
|---|---|---|
| **Whoop adapter** | Per-strap whoop-mcp-style ingestion with WHOOP-specific HRV/recovery semantics. | v0.4 (extension contract) |
| **Oura adapter** | Same shape, ring-specific sleep + readiness scores. | v0.4 |
| **Apple Health** | Aggregator-not-source — Apple Health pulls in everything else. Sourcing chain matters: Apple Health is downstream of vendor adapters. | v0.4 + careful scoping |
| **CGM / continuous glucose** | Adds a metabolic axis the project does not currently model. Dietary recommendation interaction is non-trivial; could violate no-clinical-claims. | Defer; revisit at v0.7 |
| **Manual fitness apps (Strava, Hevy, MyFitnessPal)** | Already partially supported via `hai intake gym|nutrition`; importer for Strava activities + MyFitnessPal totals would broaden manual surface. | v0.3 — small-scope, high-utility |

### 8.3 New surfaces

| Candidate | What it would mean | Decision needed by |
|---|---|---|
| **Web UI** | Browser-rendered "today" view + history visualisation. Wraps `hai today` / `hai explain` JSON. | v0.5+ — only if user feedback indicates CLI-only is a hard ceiling for second user adoption |
| **Mobile companion** | Read-only mobile app surfacing the same `today` JSON. Posts back via the host agent. | Defer past v1.0; Apple Health integration probably comes first |
| **Voice (read-out)** | "Hey Siri, what does my agent say?" — hooks today's plan to a voice surface. | Defer; cute but not load-bearing |
| **Anthropic API skill / Claude.ai connector** | A first-party Claude.ai integration that surfaces the project's CLI as an agent skill. | v0.4 — most natural distribution path given maintainer's primary loop is already Claude Code |

### 8.4 AI capability changes

| Candidate | What it would mean | Decision needed by |
|---|---|---|
| **Local LLM judge (Prometheus-2-7B)** | Already scoped as W58 in v0.2 wave (factuality gate for weekly review). | v0.2 |
| **Local LLM for skill judgment** | Replace cloud Claude with local Llama 3.1 8B or Phi-7B for the skill layer. Cuts cloud dependency entirely. | v0.5 — only if local capability matures + cost/utility ratio favours it. Honest current take: cloud Claude + local-first state is the right shape today. |
| **Per-user fine-tuning** | Train a thin adapter on the user's own state DB after ≥90 days. The "personalisation lives in the per-user predictor" claim from H1 made concrete. | v0.6+ — depends on N-of-1 substrate maturity |
| **RAG over personal history** | Retrieval-augmented generation over the user's accepted state + reviews + insights. Different from fine-tuning; cheaper to ship; more interpretable. | v0.5 — pairs naturally with the insight ledger |
| **Agent ensembles** | Replace the single host-agent with multiple specialist agents (per Google PHA). Project has explicitly bet against this (H4). Speculative reconsideration if H4 falsifies. | Conditional — only if H4 falsification fires |

### 8.5 User-set expansion

The current scope bound is recreational/technical athletes,
AI-familiar, age 18-50, no medical conditions. Expansion candidates:

| Candidate | Why it's speculative | Decision needed by |
|---|---|---|
| **Older recreational (50-70)** | BMR formulas remain valid to 65 in Mifflin-St Jeor. HRV / RHR baselines drift with age but the classifier is band-based, not absolute. The persona harness (P3) already includes 48yo so the architecture supports it. | v0.4 — would need a 50-65 persona archetype + threshold review |
| **Female cyclists** | The persona matrix includes one female cyclist (P5 multi-sport). Any cycling-specific adaptation in v0.5 would need archetype expansion. | v0.5 |
| **Adolescent (under 18)** | BMR formulas don't fit; growth-related deltas are clinically distinct; consent surface is non-trivial. | Hard no before v1.0 |
| **Clinical conditions** | Crosses the no-clinical-claims invariant. Defer indefinitely or fork. | Not before v2.0 |

---

## 9. What v1.0 looks like, written today

A maintainer-confident prediction of what shipping v1.0 means. By
the time we get there this will need refresh; capturing it now so
future-you can compare.

### v1.0 ships when

- **All five hypotheses (H1-H5) have either (a) survived their
  falsification window with positive evidence or (b) been formally
  retired with a successor hypothesis.**
- **90 days zero-incident operation post-v0.7** governed adaptation
  ship.
- **External reviewer** (Codex, or a different LLM with separate
  training) verifies:
  - Audit-chain reconciles end-to-end across ≥ 30 days.
  - No state-vs-render divergence.
  - All R-rule + X-rule firings derive from cited classified_state.
  - All recommendations honour the bounded-action contract.
  - All confidence values are honestly capped per coverage.
  - All forced actions cite a policy decision.
- **Persona matrix passes** all 8 archetypes with zero crashes,
  zero validator rejections, classifier-assumption findings ≤ 2
  per archetype.
- **Public README + ARCHITECTURE.md + AGENTS.md** are accurate to
  the shipped state. Any settled decision in this file remains
  settled.
- **Wheel + docs** publish to PyPI cleanly with an `pipx install`
  smoke test passing on macOS + Linux.

### v1.0 does NOT ship

- A web UI, mobile app, or voice surface.
- A multi-tenant deployment.
- Clinical claims.
- Any user-set expansion beyond recreational/technical athletes.
- Cloud telemetry of any kind.
- An LLM-driven recommendation engine that bypasses the policy DSL.

### What "ship" means at v1.0

The project becomes the credible reference implementation of a
**governed personal-health-agent runtime**. Anyone reading the repo
can:
1. Install the wheel on their own machine.
2. Connect their own data sources.
3. Run `hai daily` and get auditable, abstain-when-uncertain,
   clinically-bounded recommendations.
4. Inspect every decision via `hai explain`.
5. Disagree with any recommendation and have the disagreement land
   in `review_outcome` for future calibration.

The maintainer's daily loop continues uninterrupted across the v1.0
boundary; v1.0 is a snapshot, not a release in the disruptive sense.

---

## 10. The decision branches between here and v1.0

Five branches the maintainer (or a successor) will need to choose
between. Each carries a "decision needed by" milestone.

### Branch 1 — Local LLM vs. cloud Claude for skill judgment

**Decision needed by:** v0.5 review.

**Status quo:** cloud Claude via Claude Code is the agent harness;
skills run as markdown protocols Claude reads.

**Branch:** at v0.5, evaluate whether local LLM (Llama 3.1 8B, Phi-7B)
on M-series silicon produces equivalent skill output. If yes,
ship local-by-default (cloud Claude as fallback). If no, defer
to v0.7.

### Branch 2 — Single-user shape vs. multi-user

**Decision needed by:** v0.7 review.

**Status quo:** single-user-per-DB. State DB at
`~/.local/share/health_agent_infra/state.db`.

**Branch:** if external interest indicates multi-user demand,
evaluate adding a `user_id` partition discipline. Currently
implicit in many tables; upgrading to enforced tenant separation is
a non-trivial schema change.

### Branch 3 — Open-source contribution model

**Decision needed by:** v0.4 review.

**Status quo:** maintainer-only project, MIT licence, GitHub repo
public but no contribution discipline.

**Branch:** at v0.4 (when MCP surface ships), evaluate whether to
invite contributors (per-domain skill authors, additional adapter
authors). Requires CONTRIBUTING.md, code-of-conduct, PR review
discipline, security policy. Net-positive if at least one
high-quality external contributor materialises; net-negative
otherwise.

### Branch 4 — Publication / academic surface

**Decision needed by:** v0.6 review.

**Status quo:** no publications. The R-rule + X-rule DSL +
audit-chain approach is unpublished prior art.

**Branch:** at v0.6 (post-estimator ship), evaluate whether to
write a workshop / preprint covering the architecture. Cost: ~2
weeks of maintainer time. Benefit: credibility artifact, citation
pull, attracts contributors.

### Branch 5 — Hosted offering vs. tools-only

**Decision needed by:** v1.0 review (post-stability proof).

**Status quo:** Tools-only. Local-first, no hosted component.

**Branch:** at v1.0, decide whether a thin hosted service that
makes the local install easier (auth pass-through to vendor APIs,
cross-device state sync, group/community features) makes sense.
Strong default: stay tools-only. Hosted requires re-deciding H2;
H2 says local-first wins for the daily-driver use case, so a
hosted wrapper is conditional on a specific user-research signal,
not a default.

---

## 11. Provenance + how this doc evolves

### Provenance

This doc is built on:

- **`reporting/plans/historical/multi_release_roadmap.md`**
  (2026-04-25, Claude). Source of H1-H5, settled decisions D1-D9,
  comparable-OSS survey, category claim. Lifted forward intact where
  still load-bearing; updated where v0.1.10 evidence falsified.
- **`reporting/plans/v0_1_10/audit_findings.md`** (2026-04-27,
  Claude). Source of v0.1.10 strategic updates (§5).
- **`reporting/plans/v0_1_10/RELEASE_PROOF.md`** (2026-04-27,
  Claude). Source of test-surface + persona-matrix claims.
- **AGENTS.md** (project canonical). Source of operating contract
  alignment.
- **Memory: morning-briefing v0.1.x runtime bugs** (2026-04-27,
  auto-saved). Source of B1-B7 grounded findings.

### What's lifted from 2026-04-25 vs. new

| Material | Source |
|---|---|
| H1-H5 hypotheses | Lifted intact, v0.1.10 updates added |
| Category claim | Lifted intact |
| Settled decisions D1-D9 | Lifted intact |
| Settled decisions D10-D12 | NEW v0.1.10 |
| Strategic posture (§6) | Lifted intact, v0.1.10 evidence added |
| Major waves (§7) | Re-shaped — 2026-04-25 used v0.1.9 release boundaries; this doc re-shapes around v0.1.10 reality |
| Settled-but-now-falsifiable (§5) | NEW |
| Scope-expansion exploration (§8) | NEW |
| What v1.0 looks like (§9) | NEW |
| Decision branches (§10) | NEW |

### Refresh cadence

- Strategic plan reviewed every two minor releases. Next: post-v0.1.12.
- Hypotheses (H1-H5) re-evaluated annually OR when their
  falsification criterion is reachable.
- Settled decisions never reopened casually. To reopen: write a
  cycle proposal in `reporting/plans/`, run an audit round, get
  external review.
- Decision branches (§10) updated as their "decision needed by"
  milestones approach.

### What this doc does NOT cover

- Per-release execution detail → `tactical_plan_v0_1_x.md`.
- How to evaluate correctness → `eval_strategy/v1.md`.
- How to measure project value → `success_framework_v1.md`.
- What could derail this plan → `risks_and_open_questions.md`.

---

*Last reviewed: 2026-04-27 by Claude in extended planning session.
Next scheduled review: post-v0.1.12 ship.*
