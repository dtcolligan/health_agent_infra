# Strategic Plan v2 — Health Agent Infra

> **Superseded as current planning (2026-05-11).** This file describes a
> pre-reframe project shape. The active framing is
> `framing_v2/CONVERGED.md` — "Deterministic Software Contracts as
> Trusted Monitors in AI Control Protocols" (D-FRAME-016; NeurIPS 2027
> main conference). Decisions in this file may be inconsistent with the
> merged-paper framing; treat the body as **historical provenance only**,
> not as current planning truth. For current project decisions, read
> `framing_v2/CONVERGED.md`, `framing_v2/ORCHESTRATOR_STATE.md`, and
> `project/DECISIONS.md`.

---

> **Status.** Authored 2026-05-06 by Claude (delegated by maintainer)
> in extended planning session. Fresh authorship; supersedes
> `reporting/plans/strategic_plan_v1.md` (2026-04-27).
>
> **2026-05-07 research-reframe note.** This document is no longer the
> project-wide strategic plan. It is preserved as the HAI
> reference-runtime strategy immediately before the runtime-contract
> research reframe. Current project-wide strategy lives in
> [`../../../../project/FRAME.md`](../../../../project/FRAME.md),
> [`../../../../project/DECISIONS.md`](../../../../project/DECISIONS.md), and
> [`../../../../project/OPERATING_MODEL.md`](../../../../project/OPERATING_MODEL.md).
> Current paper/evaluation strategy lives in
> [`../../../research/runtime_contracts_paper/PAPER_FRAME.md`](../../../research/runtime_contracts_paper/PAPER_FRAME.md)
> and
> [`../../../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`](../../../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md).
>
> **Why fresh, not patched.** v1 was authored after v0.1.10 shipped.
> Since then, 10 release cycles have shipped (v0.1.11–v0.1.18 + two
> hotfixes), 2 cycles have been cancelled (v0.1.16, v0.1.19), 4 new
> settled decisions have been added (D13–D16; D10–D12 were already
> in v1), the cli.py split has landed, the docs overhaul has
> ratified an "agent-wrapper" framing sharper than v1 articulated,
> and the foreign-user empirical contract has bifurcated into three
> claims. v1 is preserved as evidence; this doc derived the HAI
> strategic posture from then-current state before the research reframe.
>
> **Audience.** HAI support-lane provenance — readable to a senior
> engineer opening the HAI runtime cold, but superseded for repo-wide
> project strategy.
>
> **Reading rule after the research reframe.** Every Wave, version, and
> v1.0 reference below is a conditional HAI reference-runtime support-lane
> roadmap. Do not treat it as the active project calendar. The active
> project calendar is the paper / GovernedAgentBench / runtime-contract
> path in `project/FRAME.md`, `project/DECISIONS.md`,
> `project/OPERATING_MODEL.md`, and `project/ROADMAP.md`.
>
> **Companion docs.**
> - `tactical_plan_v0_1_x.md` — release-by-release execution.
> - `eval_strategy/v1.md` — HAI runtime correctness strategy.
> - `success_framework_v1.md` — HAI runtime value framework.
> - `risks_and_open_questions.md` — HAI runtime risk register.
> - `post_v0_1_18/v0_1_x_retro.md` — operational retro on what 18
>   cycles taught us.
> - `README.md` — reading order index.
>
> **Refresh cadence.** Strategic plan reviewed every two minor
> releases (next refresh: post-v0.2.0 ship) or whenever a settled
> decision needs revisiting. Tactical plan refreshed per release.
> v1 is preserved as evidence at `strategic_plan_v1.md` and is not
> revised in place. As of 2026-05-07, this doc is support-lane
> provenance, not the active forward reference.

---

## Table of contents

1. What this project is, in one paragraph
2. Where the project sits in the landscape
3. The thesis: five falsifiable bets (refreshed)
4. Settled decisions D1–D16 (do not reopen casually)
5. What v0.1.x changed
6. Strategic posture for the next 12–18 months
7. Major waves to v1.0 (re-baselined from 2026-05-06)
8. Scope-expansion exploration (speculative, with new evidence)
9. What v1.0 looks like, written today
10. Decision branches between here and v1.0
11. Provenance + how this doc evolves

---

## 1. What this project is, in one paragraph

**Health Agent Infra is the local plugin/runtime wrapper around a
shell-capable personal-health agent.** A user talks to a host agent
in natural language; the agent invokes the local `hai` CLI; the
runtime absorbs passive evidence (wearable data via intervals.icu
today; bloodwork and richer sources next), validates and reconciles
proposals, and commits decisions to local SQLite + JSONL audit logs.
`hai` is the governed tool surface that declares what commands
exist, which substrates each may mutate, what each output validates
against, and which authority is refused to the agent.

The unit of shipping is a Python wheel (`health-agent-infra`) plus
markdown skills consumed by the agent at runtime. The contract is
one line:

> **The agent proposes and explains; the runtime validates and commits.**

The maintainer's daily-driver loop is Claude Code over the project's
own `hai` CLI; the project is its own dogfood. v1 of this strategic
plan called this category "governed personal-health-agent runtime";
the post-v0.1.15 docs overhaul (32 files changed, 1942 insertions)
sharpened the framing to **agent-wrapper** — the agent stays the
conversational operator, `hai` stays the governed tool surface.
That framing is now load-bearing across `README.md`,
`ARCHITECTURE.md`, `AGENTS.md`, and the six per-domain reference
docs.

---

## 2. Where the project sits in the landscape

### 2.1 The category claim (refreshed)

The project occupies a category that does not yet have a canonical
name in public usage. Nearest neighbours, with v0.1.x evidence
updates:

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

The accurate description, sharpened post-docs-overhaul: **a
local-first agent-wrapper for daily personal-health decisions across
six domains, where a deterministic policy engine owns every band,
score, and rule, and the LLM is allowed only to compose bounded,
typed, reviewable proposals.**

### 2.2 What's defensibly differentiated (refreshed v0.1.x evidence)

Cross-checked against the comparable-OSS survey carried forward
from v1, **five things remain unique**, each strengthened by
v0.1.x evidence:

1. **Deterministic policy engine separated from LLM judgment.** R-rule
   + X-rule layer in code, skill-level invariants enforce that
   neither runs in prose. v0.1.10 W-A's bool-as-int silent-coercion
   closure (D12) hardened this contract durably; v0.1.13 D13
   formalised the threshold-injection seam as trusted-by-design.

2. **Domain-typed Proposals with explicit safety/abstain semantics.**
   `defer_decision_insufficient_signal` is a first-class action in
   every domain. v0.1.10 W-C partial-day gate; v0.1.15 W-A
   `is_partial_day` + `target_status` presence block; v0.1.15 W-C
   `hai target nutrition` macro target commit (W57-gated). The
   abstain-when-uncertain contract is now four-deep in the runtime,
   not one-deep.

3. **Writeback + review-outcome loop.** Three-state audit chain
   (`proposal_log → planned_recommendation → daily_plan +
   recommendation_log → review_outcome`) survives 18 cycles. D1
   re-author semantics intact. `hai explain` reconciles end-to-end.

4. **Capabilities manifest as agent contract.** `hai capabilities
   --json` exposes mutation classes, `agent_safe` flags,
   idempotency, exit-code semantics. v0.1.14.1 W-GARMIN-MANIFEST-SIGNAL
   added structured `choice_metadata.reliability` fields; v0.1.17 W-30
   pinned the schema with a regression test (full freeze v0.2.3).
   Now byte-stable across the v0.1.17 cli.py mechanical split — the
   manifest survived a 9,927-LOC refactor without a single field
   move.

5. **Persona-driven regression infrastructure.** v0.1.10 shipped 8
   archetypes; v0.1.11 expanded to 12; v0.1.14 W-EXPLAIN-UX added P13
   for low-domain-knowledge readers; v0.1.17 W-Vb-4 closed
   12-of-12 P1..P12 closure with P13 matrix-only (0 findings, 0
   crashes). No surveyed competitor ships persona-driven regression
   testing for their decision layer at this scale.

### 2.3 Agent-wrapper framing (new in v2)

The post-v0.1.15 docs overhaul (`reporting/plans/post_v0_1_15/docs_overhaul_report.md`)
established a five-element wrapper contract that v1 understated:

- The agent declares what commands exist via `hai capabilities --json`.
- The runtime declares which substrates each command may mutate
  (the nine mutation classes documented at
  `docs/hai/host_agent_contract.md`).
- The runtime declares which outputs must validate against schema.
- The runtime declares which authority is refused to the agent
  (W57 invariant; `agent_safe == false` flags).
- The runtime declares how the agent may compose multi-step
  proposals via the proposal-gate three-state machine.

This isn't a feature list; it's a **published operational contract**
that an external host agent can program against. It's also the
strongest evidence the project ships a governance-contract product,
not a coaching feature. v0.2-v0.4 work extends this contract; it
does not replace it.

---

## 3. The thesis: five falsifiable bets (refreshed)

Lifted from v1; evidence updated through v0.1.18.

### H1. The hard problem in personal health AI is interpretability of outcomes, not better recommendations

**Bet.** The marginal value of a 5% better daily recommendation is
tiny compared to being able to answer "did anything I changed
actually help, and why do I think so?" Core competence is the
*evidence-and-audit chain*, not the recommendation algorithm.

**Evidence.** SePA (arXiv 2509.04752) shows personalisation lives
in the per-user predictor; LLM is downstream narration. Apple
Mulberry's shelving (Feb 2026). JITAI meta-analysis (PMC12481328)
between-group g=0.15. WHOOP / Oura / Fitbit Coach narrate over
fixed metrics stacks.

**v0.1.x evidence accumulation:**
- **v0.1.10:** morning-briefing dogfood — agent's honest defer on
  partial nutrition data was more valuable than a confident wrong
  answer.
- **v0.1.15 W-D arm-1:** partial-day nutrition suppression to
  `nutrition_status='insufficient_data'` codified the abstention
  behaviour as a runtime contract.
- **v0.1.18 (today):** the maintainer's father installed v0.1.18 on
  a foreign machine **without a wearable** and reported "it worked
  for him." With every recovery / running / sleep classifier
  forced to defer for lack of signal, the system still produced
  coherent output. **This is the strongest H1 evidence yet** — a
  non-maintainer user found honest silence useful.

**Falsification.** Per v1: if Dom (after v0.5 substrate + 90 days)
consistently consults underlying metrics in preference to
personal-evidence verdicts, the bet is wrong. Population criterion
deferred until post-v1.0.

**Status:** active, three positive evidence points, no falsification
signal.

### H2. Local-first beats hosted for the daily-runtime use case

**Bet.** Privacy + ownership + offline reliability + zero
data-egress beats centralised model freshness for a daily driver.

**Evidence.** Cactus + Ollama + MLX clear 38–58 tok/s for 4B-class
models on M2 Pro. EU Digital Omnibus + EDPB Opinion (2025) raise
the GDPR bar on training-data lawfulness. Comparable-OSS survey:
every shipping vendor coach is cloud; the local-first niche is
empty.

**v0.1.x evidence accumulation:**
- **v0.1.13 W-OB-1 / v0.1.18 W-OB-2:** README pivot to "local-only
  by construction" lead. No telemetry, no hosted backend, no cloud
  sync. State lives on user's machine in SQLite + JSONL.
- **v0.1.15.1:** Linux keyring fall-through hotfix proved the
  local-first path works on Linux without a registered keyring
  backend (degrades to env-var/no-credential mode).
- **v0.1.18 W-OB-7:** intake-handler migration parity ensured the
  local install path stays consistent across schema changes.

**Falsification.** Consumer hardware regresses on local LLM
performance OR a regulator forces server-side audit incompatible
with local-first.

**Status:** active, no v0.1.x update on falsification signal.

### H3. User-authored intent + targets + bounded supersession is the right substrate for governed adaptation

**Bet.** W49 intent ledger + W50 target ledger + proposal/plan
supersession discipline form the substrate that makes future
governed adaptation possible without becoming a black-box
auto-tuning system.

**Evidence.** AgentSpec (arXiv 2503.18666) closest published prior
art for runtime enforcement with user-approval-gated rule
mutation. Bloom / GPTCoach (arXiv 2510.05449) shows LLMs proposing
structured mutations to user-owned plans is a working shape.

**v0.1.x evidence accumulation:**
- **v0.1.10:** intent + target commit flow demonstrated end-to-end
  (agent proposes 3300 kcal target → maintainer commits via
  `--confirm`).
- **v0.1.15 W-C:** `hai target nutrition` extends the existing
  target table with macro rows (carbs_g + fat_g via migration 025).
  W57-gated end-to-end.
- **v0.1.17 W-B:** `hai intake weight` adds body-composition
  intake with `body_comp` table + migration 026.
- **D13 (v0.1.11):** threshold-injection seam settled as
  trusted-by-design — production callers always validate via
  `core.config.load_thresholds`. Adaptation can build on this
  without reopening.

**Falsification.** Per v1: post-v0.7, users either approve every
proposed mutation without reviewing OR routinely reject so many
that the channel is unused. Check at v0.7 review.

**Status:** active.

### H4. LLM agents driving deterministic CLIs > LLM agents reasoning end-to-end

**Bet.** A CLI that exposes typed mutation classes + capabilities
manifest + exit-code contract is a *better* substrate for an LLM
agent than letting the LLM directly access the database, model
weights, or policy engine.

**Evidence.** PHIA (Nature Communications 2025): single agent with
code-execution tool matches three-agent specialist team. Single-Agent
vs Multi-Agent (arXiv 2604.02460): multi-agent advantage shrinks as
base-model capability rises. Cactus + Ollama show local
single-agent inference is fast enough.

**v0.1.x evidence accumulation:**
- **18 cycles** of maintainer dogfood without a single
  shell-into-SQLite escape for any user-mode workflow. The
  capability surface absorbed every workflow the maintainer
  attempted.
- **v0.1.13 W-AA / v0.1.18 W-OB-2:** `hai init --guided` orchestrator
  proved end-to-end onboarding can run agent-driven without the
  maintainer touching state directly.
- **v0.1.17 W-29:** cli.py 9,927-LOC mechanical split into 11
  handler modules; **manifest byte-stable** through the split.
  This is the strongest H4 evidence — the agent contract survived
  the largest refactor in project history without a field move.
- **v0.1.18 W-OB-5:** `hai doctor next_action` field across 9
  hint-emitting paths gives agents a structured companion to the
  existing prose hints.

**Falsification.**
1. *Internal:* the project's own daily loop starts shelling into
   SQLite directly because the CLI can't surface what's needed.
   v0.1.10–v0.1.18 dogfood: zero such occurrences.
2. *External (post-v0.4):* once the MCP ships, second agents either
   bypass governed surfaces in favour of raw access OR refuse to
   integrate because the surface is too narrow.

**Status:** active, validated by 18 cycles of dogfood and the W-29
split.

### H5. A small set of governed ledgers + a strict code-vs-skill boundary scales further than a multi-agent prose-driven architecture

**Bet.** Append-only evidence, archive/supersede over UPDATE, every
row has provenance, skills never run arithmetic — let one
maintainer ship a runtime that a multi-agent team cannot match for
governance, audit, and reproducibility per unit of complexity.

**Evidence.** Apple Mulberry's failure (Feb 2026) at multi-domain
clinical-decision-tree-encoded coaching with the largest
engineering team in consumer health. Google PHA paper concedes 6.5
LLM calls per query and >3-minute latency.

**v0.1.x evidence accumulation:**
- **16 shipped releases plus 2 cancelled empirical cycles** disposed
  by a single maintainer (18 cycle outcomes total). v0.1.13 was the
  largest cycle in the track at 17 workstreams, with 16 closed and
  one honest partial-closure (W-Vb → v0.1.14 residual).
- **D11 + D14 + D15** audit cycle pattern twice/thrice-validated:
  - **D14 plan-audit:** 10 → 5 → 3 → 0 settling shape twice-validated
    (v0.1.11, v0.1.12); 11 → 5 → 3 thrice-validated (v0.1.17).
  - **D15 IR cycle:** 5 → 2 → 1-nit twice-validated (v0.1.11,
    v0.1.12); 6 → 1 (v0.1.17, one round shorter when R1 was
    mechanical); 4 → 2 → 1-nit (v0.1.18, full canonical settling).
- **v0.1.17 W-AH-2:** scenario fixture corpus tripled from 35 → 135
  at 100% pass-rate. Eval-substrate scaled without ledger reshape.
- **Post-v0.1.15 docs overhaul:** ratified the agent-wrapper
  thesis durably across operating docs.

**Falsification.** If the project itself starts to need a multi-agent
shape to ship the next release (e.g., v0.7 governed adaptation
proves intractable inside the single-runtime + skill boundary).
Population-comparison criteria post-v1.0 only.

**Status:** active. Eighteen-cycle proof point.

---

## 4. Settled decisions D1–D16 (do not reopen casually)

Lifted from AGENTS.md "Settled Decisions" current state. v1 had
D1–D12; v2 adds D13–D16. To reopen any of these: write a cycle
proposal, run an audit round, get external review.

| # | Decision | First settled |
|---|---|---|
| **D1** | W37 original shape is dead. Skills do not compute review-outcome pattern tokens. W48 replaced with code-owned `core/review/summary.py`. | v0.1.8 |
| **D2** | W39 narrowed: threshold override loading already exists. v0.1.8 scope was validation/diff/auditability. | v0.1.8 |
| **D3** | W47 cut: keep release-proof/changelog discipline, no working-tree-sensitive changelog test. | v0.1.8 |
| **D4** | W29 / W30 deferred (then). **Updated:** W29 cli.py split CLOSED at v0.1.17 (mechanical split landed); W30 capabilities-manifest schema regression test landed v0.1.17, full freeze remains v0.2.3. | v0.1.8 / v0.1.17 |
| **D5** | Garmin Connect is not the default live source. **v0.1.14.1 update:** unreliability now structured manifest signal + stderr warning. | v0.1.6 |
| **D6** | Nutrition v1 is macros-only. | v0.1.x |
| **D7** | No `STATUS.md` parallel file. | v0.1.x |
| **D8** | LLM-judge for weekly review = factuality only. | v0.1.9 (pre-cut) |
| **D9** | Two-shot agent-judge negotiation loop, not infinite. | v0.1.9 (pre-cut) |
| **D10** | Persona harness lives in `verification/dogfood/`, not `verification/tests/`. CI stays fast. | v0.1.10 |
| **D11** | Pre-PLAN bug-hunt phase is permanent pattern. | v0.1.10 |
| **D12** | Every `int(cfg)` / `float(cfg)` / `bool(cfg)` in the runtime must use `core.config.coerce_*` helpers. | v0.1.10 |
| **D13** | Threshold-injection seam is trusted-by-design. Production callers validate via `core.config.load_thresholds`. | v0.1.11 |
| **D14** | Pre-cycle Codex plan-audit is permanent pattern for substantive PLAN.md revisions. Multi-round normal. | v0.1.11 |
| **D15** | Cycle-weight tiering: substantive / hardening / doc-only / hotfix. RELEASE_PROOF.md declares tier as first line. | v0.1.12 |
| **D16** | W-2U-GATE split into W-2U-INSTALL (closed verbal-only) + W-2U-WEARABLE + W-2U-DOGFOOD (deferred to v0.4 review). v0.2.0 hard-dep on foreign-user empirical dropped. | post-v0.1.18 (today) |

---

## 5. What v0.1.x changed

This section replaces v1 §5 ("Settled-but-now-falsifiable: what
v0.1.10 changed"). It covers the full v0.1.10–v0.1.18 track and
names what shifted strategically.

### 5.1 cli.py rot risk closed

v1's `risks_and_open_questions.md` named R-T-03 ("cli.py rot") with
trip-wire `wc -l > 10000`. v0.1.13 W-29-prep landed the boundary
audit; **v0.1.17 W-29 shipped the mechanical split** — 9,927 LOC →
1 main + 1 shared + 11 handler-group modules (each <2,500 LOC).
Manifest byte-stable through the split. R-T-03 is **resolved**, not
deferred. v0.2+ work on `cli/` no longer carries the rot risk.

### 5.2 Persona harness load-bearing, not optional

v1's success_framework_v1.md §3.3 named persona pass-rate as a
Tier 1 metric with target ≥0.95 by v0.1.11. Reality: v0.1.17 W-Vb-4
closed **12-of-12 P1..P12 + P13 matrix-only** with **0 findings, 0
crashes**. v0.1.14 added P13 (low-domain-knowledge persona for
`hai explain` review). v0.1.17 added an opt-in regression test
pinning the contract.

The harness is now HAI's strongest non-maintainer signal
surface — it absorbs assumption bugs the single-user dogfood can't
catch. The original v1 framing ("informally given findings detector
heuristics") understated this; the harness is now load-bearing
infrastructure, not eval polish.

### 5.3 Foreign-user empirical contract bifurcated (D16, today)

v1 treated foreign-user evidence as a single monolithic gate. The
v0.1.16 cancellation (named candidate became unavailable) and the
v0.1.19 cancellation (today, candidate-supply criteria too narrow)
forced the realisation that W-2U-GATE conflates three empirical
claims:

- **W-2U-INSTALL** — install + onboarding + abstain-without-wearable
  produces coherent output. Closed verbal-only by the post-v0.1.18
  father session.
- **W-2U-WEARABLE** — full pipeline produces useful output for a
  wearable-bearing foreign user. Deferred to v0.4 review.
- **W-2U-DOGFOOD** — non-maintainer uses the system daily for ≥7
  consecutive days. Deferred to v0.4 review.

v0.2.0 hard-dep on foreign-user empirical evidence dropped per
CP-2U-GATE-SPLIT. v0.2.0 ships against W58D factuality-gate
mitigation, not against foreign-user evidence.

### 5.4 Docs overhaul retroactively closed §6.3 of v1

v1 §6.3 ("Ship the credible artifact") named four load-bearing
elements (governance contract + audit chain; skill-overlay
invariant; Phase B write-surface guard; R-rule + X-rule policy
DSL). v1 said "all four are publishable."

The post-v0.1.15 docs overhaul (committed `c86f80b`, 32 files
changed) made the agent-wrapper thesis durable across operating
docs. Five Mermaid diagrams ratified the architecture visually. A
new `host_agent_contract.md` consolidated the manifest discovery,
mutation taxonomy, proposal-gate machine, and refusal handling
into one external-readable contract.

§6.3 is now **a current claim**, not a future one. The credible
artifact ships today; v0.2-v0.4 extends it but does not invent it.

### 5.5 Audit-chain settling shapes thrice-validated

v1 §11 referenced "the four-round audit pattern" loosely. v0.1.x
empirically validated the pattern with concrete settling shapes:

- **D14 plan-audit:** 10 → 5 → 3 → 0 (v0.1.11), 10 → 5 → 3 → 0
  (v0.1.12), 11 → 5 → 3 (v0.1.17 — one round shorter), 7 → 3
  (v0.1.18 — halving close-in-place at 2 rounds).
- **D15 IR cycle:** 5 → 2 → 1-nit (v0.1.11), 5 → 2 → 1-nit (v0.1.12),
  6 → 1 (v0.1.17, mechanical), 4 → 2 → 1-nit (v0.1.18).

Future cycles can budget audit rounds against these empirical
norms. v0.2.0 substantive cycle should budget 2–4 D14 rounds + 2–3
IR rounds. Doc-only cycles single round.

### 5.6 Eval scenario corpus tripled

v0.1.14 moved the deterministic scenario corpus from 28 → 35
(W-AH) and shipped 30 judge-adversarial fixtures (W-AI). v0.1.17
W-AH-2 then expanded the deterministic corpus from 35 → **135
deterministic fixtures** (20 per domain × 6 + 15 synthesis), 100%
pass-rate. The eval-substrate v0.2.0 W58D factuality gate consumes
is now order-of-magnitude larger than v1 anticipated.

### 5.7 Onboarding ergonomics ratified

v0.1.13 W-AA shipped `hai init --guided` 7-step orchestrator.
v0.1.18 W-OB-2 made `hai init` **interactive by default** (auto-
promote to `--guided` when stdin is TTY + state incomplete).
v0.1.18 W-OB-7 closed the schema-behind-DB intake crash class via
the additive `open_connection_with_migrations` helper.

These shipped *before* the foreign-user gate fired — exactly the
"close known onboarding gaps proactively before exposing to a
foreign user" sequence v0.1.16 cancellation forced.

---

## 6. HAI support-lane strategic posture for the next 12–18 months

> **Reframe reading rule.** This section is not the project-wide
> strategy after 2026-05-07. It is the HAI reference-runtime support-lane
> posture preserved for provenance and future resumption.

Three postures, refreshed with v0.1.x evidence.

### 6.1 Lead with the governance contract (still load-bearing)

Adding new wearable adapters is undifferentiated work. The moat is
the runtime + skills + writeback/review loop. Every release should
make the governance contract more legible, more credible, more
inspectable, more exportable — *not* expand the surface area of
what the project ingests.

**v0.1.x reinforcement:** v0.1.10 W-D-ext fixed the running-domain
gap by wiring an existing aggregator. v0.1.17 W-29 split cli.py
without expanding ingest. v0.1.18 W-OB work hardened onboarding
without adding sources. The next 12 months continue this discipline.

### 6.2 Borrow the commodity, defend the decision layer

Open mHealth / IEEE 1752.1 / FHIR R4 are commodity vocabularies for
data shape. Adopt where they let third parties consume the project's
data without rewriting glue. Do not adopt where they force the
policy/judgment layer into a clinical interoperability shape that
contradicts wellness-only positioning.

### 6.3 The credible artifact ships today

v1 framed §6.3 as a future-tense claim. Post-v0.1.18 it's
present-tense. The four load-bearing elements ship now:

1. **Governance contract + audit chain.** Three-state reconciliation;
   every recommendation cites evidence chain back to source rows.
2. **Skill-overlay invariant.** `_overlay_skill_drafts` whitelists 3
   keys, raises on anything else; no skill imports in runtime.
3. **Phase B write-surface guard.** `guard_phase_b_mutation`.
4. **R-rule + X-rule policy DSL.** Code-owned; v0.1.10 D12 +
   v0.1.11 D13 hardened the threshold seam.

The two new load-bearing elements as of v0.1.x:

5. **Persona-driven regression infrastructure** (D10).
6. **Pre-cycle audit pattern** (D11 + D14 + D15).

Wave 2-5 work *extends* the artifact; Wave 1 *shipped* it.

### 6.4 The publishable contribution (sharpened)

v1 §6.3 named four elements as publishable prior art. v0.1.x
adds two methodology contributions:

- **Pre-PLAN bug-hunt + plan-audit + multi-round IR pattern** (D11
  + D14 + D15). Twice-or-thrice-validated empirical settling shapes.
- **Persona-driven regression for AI agent decision layers** (D10).
  No surveyed competitor ships this.

A v0.6 workshop / preprint (decision-needed-by Branch 4) covers the
governance contract, the policy DSL, the audit-chain pattern, and
the methodology contribution as one coherent submission.

---

## 7. HAI support-lane waves to v1.0 (re-baselined from 2026-05-06)

> **Reframe reading rule.** The waves below are parked HAI runtime
> roadmap material. They are subordinate to the runtime-contract paper
> and GovernedAgentBench unless a specific item is declared
> paper-critical.

v1's wave structure stays intact. Timeline re-baselines from
2026-05-06 (v0.1.18 ship + v0.1.19 cancellation).

### Wave 1 — Hardening + dogfood credibility (v0.1.10–v0.1.18, ~10 days actual)

**Theme.** Make the existing runtime trustworthy enough to point at.
**Status: SHIPPED through v0.1.18.** Persona harness landed
(v0.1.10), deferred audit findings closed (v0.1.11–v0.1.12), public
surface hardened (v0.1.13), eval substrate + provenance + recovery
path (v0.1.14), foreign-user-ready package (v0.1.15), maintainability
+ eval substrate consolidation (v0.1.17), onboarding-quality + intake-
handler migration parity (v0.1.18).

End-state: external reviewer reading the project cold can verify the
governance contract holds. **Achieved through v0.1.18** with the
named residual that W-2U-WEARABLE + W-2U-DOGFOOD evidence is missing
(D16, deferred to v0.4 review). The Wave 1 end-state is
*partly* validated; full foreign-user wearable-bearing + multi-day
dogfood evidence moves to Wave 3 prereq territory.

**Evidence anchor:** v0.1.10 audit findings + v0.1.11–v0.1.18
RELEASE_PROOFs + post_v0_1_15 docs overhaul + post_v0_1_18 retro.

### Wave 2 — Weekly review + insight ledger + factuality gate (v0.2.0–v0.2.3, ~3 months)

**Theme.** Make the runtime useful beyond one day.

- **v0.2.0** — W52 weekly review + W58D deterministic factuality
  gate + 4 doc-only adjuncts (W-MCP-THREAT, W-COMP-LANDSCAPE,
  W-NOF1-METHOD, W-2U-GATE-2). One schema group.
- **v0.2.1** — W53 insight ledger only. One schema group.
- **v0.2.2** — W58J LLM judge shadow-by-default + W-JUDGE-BIAS
  bias panel. One schema group.
- **v0.2.3** — W58J flip to blocking + W-30 capabilities-manifest
  schema freeze. No new schema.

Path A total v0.2.x effort: 39–56 days across four cycles
(post-v0.1.13 reconciliation C6 honored: one schema group per
release).

**v0.2.0 hard deps post-D16:** v0.1.14 substrate (W-PROV-1 + W-AJ
judge harness), already shipped. **Foreign-user empirical evidence
re-tiered to opportunistic-not-blocking per D16.**

### Wave 3 — MCP surface + extension contract (v0.3–v0.4, ~3-4 months)

**Theme.** Make the runtime accessible to second agents and second
data sources.

- **v0.2.0** — *threat-model artifact authored* at
  `docs/hai/mcp_threat_model.md` as W-MCP-THREAT (doc-only
  adjunct). Pre-requisite for v0.3 PLAN-audit.
- **v0.3** — *plans* MCP server. Read-surface design only. Provenance
  import contract drafted.
- **v0.4** — *prereqs land*. Least-privilege read-scope model
  documented. **W-2U-WEARABLE + W-2U-DOGFOOD re-evaluated as hard
  gates here (D16).** Threat-model doc completes with mitigations.
- **v0.4-or-v0.5** — *ships* MCP read surface. **No write surface
  ever** (W57 invariant preserved at the MCP boundary).

**Security gate (non-negotiable).** No MCP read surface ships
before threat-model artifact, least-privilege scope model, and
one-domain provenance proof are all in place.

### Wave 4 — N-of-1 substrate + estimator (v0.5–v0.6, ≥90d substrate gate)

**Theme.** The (recommendation, compliance, outcome,
classified_state) triple ledger + the analyzer that reads it.
Substrate-then-estimator dependency chain. Earliest end-of-Wave-4
ship: 2027-Q1-Q2.

### Wave 5 — Governed adaptation + v1.0 stability (v0.7–v1.0)

**Theme.** Substrate-validated mutation proposals + 90-day
zero-incident stability proof. v1.0 is the operational claim, not a
feature claim.

### Total horizon (re-baselined)

**Optimistic:** 14–18 months from 2026-05-06 to v1.0 — late 2027.
**Realistic:** 18–24 months — early-to-mid 2028.

The substrate-maturation gates (v0.5 → 90d → v0.6, v0.7 → 90d →
v1.0) cannot be compressed; they are evidence-driven.

**v1 said "14-18 months optimistic from v0.1.10 (April 2026) to
v1.0 ship — late 2027."** v2 holds the same horizon — Wave 1
shipped roughly 2-3 months ahead of v1's "~3 months" Wave 1
estimate (actual: ~10 days from v0.1.10 to v0.1.18), but the total
v1.0 horizon is unchanged because the back-half calendar gates
(v0.5 → 90d → v0.6, v0.7 → 90d → v1.0) dominate.

---

## 8. HAI support-lane scope-expansion exploration (speculative, with new evidence)

> **Reframe reading rule.** This is not current project scope. Treat it
> as HAI backlog/provenance until the research lane no longer owns the
> priority.

Same shape as v1 §8. New empirical evidence integrated.

### 8.1 New domains

| Candidate | Decision needed by | v0.1.x update |
|---|---|---|
| Mental health proxy domain | v0.6 review | unchanged |
| Cycling-specific running-equivalent | v0.4 review | P5 triathlete persona still surfaces this gap |
| Rehab / return-to-sport | Not before v1.0 | unchanged |

### 8.2 New data sources

| Candidate | Decision needed by | v0.1.x update |
|---|---|---|
| Whoop adapter | v0.4 | unchanged |
| Oura adapter | v0.4 | unchanged |
| Apple Health | v0.4 + careful scoping | unchanged |
| CGM / continuous glucose | v0.7+ | unchanged |
| Hevy / MyFitnessPal | v0.3 | unchanged |
| **Strava** | **PROHIBITED per AGENTS.md "Do Not Do"** | unchanged |

### 8.3 New surfaces

| Candidate | Decision needed by | v0.1.x update |
|---|---|---|
| Web UI | v0.5+ | unchanged |
| Mobile companion | Defer past v1.0 | unchanged |
| Voice (read-out) | Defer | unchanged |
| Anthropic API skill / Claude.ai connector | v0.4 | unchanged |

### 8.4 AI capability changes

Per v1; no v0.1.x update.

### 8.5 User-set expansion (NEW evidence today)

| Candidate | Decision needed by | v0.1.x update |
|---|---|---|
| **Older recreational (50–70)** | **PULL FORWARD: v0.3 review** (was v0.4) | **v0.1.18 father session — unplanned-empirical evidence that the install + abstain path works for someone in this band. The decision-needed-by date may be earlier than v1 anticipated; flag for v0.3 review consideration.** |
| Female cyclists | v0.5 | unchanged |
| Adolescent (under 18) | Hard no before v1.0 | unchanged |
| Clinical conditions | Not before v2.0 | unchanged |

The father-session evidence is unplanned-empirical: **a 50–70 user
ran the install on a non-maintainer machine post-v0.1.18 and it
worked.** This isn't sufficient evidence to formally expand
user-set scope, but it's evidence the architecture doesn't *fight*
the band, which is the question §8.5 was waiting for. v0.3
review (when MCP threat model authors) is the natural reconsideration
point.

---

## 9. What HAI v1.0 looked like before the research reframe

> **Reframe reading rule.** This is a preserved HAI target-state sketch,
> not an active commitment to ship HAI v1.0 before the paper,
> GovernedAgentBench, and reproducible baselines.

Refresh of v1 §9. Most criteria hold; v0.1.x changes the
provenance for several.

### v1.0 ships when

- **All five hypotheses (H1–H5) have either (a) survived their
  falsification window with positive evidence or (b) been formally
  retired with a successor hypothesis.**
- **90 days zero-incident operation post-v0.7** governed adaptation
  ship.
- **External reviewer** verifies:
  - Audit-chain reconciles end-to-end across ≥30 days.
  - No state-vs-render divergence.
  - All R-rule + X-rule firings derive from cited classified_state.
  - All recommendations honour the bounded-action contract.
  - All confidence values are honestly capped per coverage.
  - All forced actions cite a policy decision.
- **Persona matrix passes** all archetypes (currently 13) with zero
  crashes, zero validator rejections, classifier-assumption findings
  ≤2 per archetype. **Already passing as of v0.1.17 (12-of-12 P1..P12
  + P13 matrix-only).** Maintain through Wave 4.
- **Public README + ARCHITECTURE.md + AGENTS.md** accurate to
  shipped state. Any settled decision in this file remains settled.
  **Currently true as of v0.1.18 + the post-v0.1.15 docs overhaul.**
- **Wheel + docs** publish to PyPI cleanly with `pipx install` smoke
  test passing on macOS + Linux. **Currently true as of v0.1.15.1.**
- **W-2U-WEARABLE + W-2U-DOGFOOD evidence** captured per D16
  (re-evaluated at v0.4 review). New criterion vs v1.

### v1.0 does NOT ship

- A web UI, mobile app, or voice surface.
- A multi-tenant deployment.
- Clinical claims.
- Any user-set expansion beyond recreational/technical athletes
  (extends to 50-70 if §8.5 v0.3-review pulls forward).
- Cloud telemetry of any kind.
- An LLM-driven recommendation engine that bypasses the policy DSL.

### What "ship" means at v1.0

Same as v1: anyone reading the repo can install the wheel, connect
their data sources, run `hai daily`, get auditable
abstain-when-uncertain clinically-bounded recommendations, inspect
every decision via `hai explain`, and disagree with any
recommendation via `review_outcome`.

The maintainer's daily loop continues uninterrupted across the v1.0
boundary; v1.0 is a snapshot, not a release in the disruptive sense.

---

## 10. HAI support-lane decision branches between here and v1.0

> **Reframe reading rule.** These branches are dormant unless they become
> paper-critical, benchmark-critical, or are explicitly reopened by the
> maintainer after the research push.

Same five branches as v1; dates updated.

### Branch 1 — Local LLM vs. cloud Claude for skill judgment

**Decision needed by:** v0.5 review.

**v0.1.x update flag:** local-LLM landscape moves faster than
v1 anticipated. The v0.5 decision date may be too late if a
mid-2026 capable open-weight model lands and the project hasn't
benchmarked. **Consider pulling forward to v0.3 review**
(opportunistic — only if a credible candidate ships).

### Branch 2 — Single-user shape vs. multi-user

**Decision needed by:** v0.7 review. Unchanged.

### Branch 3 — Open-source contribution model

**Decision needed by:** v0.4 review. Unchanged.

### Branch 4 — Publication / academic surface

**Decision needed by:** v0.6 review.

**v0.1.x update:** the publishable surface broadened — methodology
contribution (D10 + D11 + D14 + D15) joins the architecture
contribution. Workshop / preprint scope is now larger but more
defensible.

### Branch 5 — Hosted offering vs. tools-only

**Decision needed by:** v1.0 review (post-stability proof).
Unchanged.

---

## 11. Provenance + how this doc evolves

### Provenance

This doc is built on:

- **`reporting/plans/strategic_plan_v1.md`** (2026-04-27, Claude).
  Source of H1–H5, settled decisions D1–D12, comparable-OSS survey,
  category claim, wave structure. Lifted forward where still
  load-bearing; updated where v0.1.11–v0.1.18 evidence shifted.
- **`docs/hai/current_system_state.md`** (2026-05-06).
  Source of v0.1.18 shipped baseline.
- **`reporting/plans/post_v0_1_15/docs_overhaul_report.md`**
  (2026-05-04). Source of agent-wrapper framing + diagram surface
  + host_agent_contract.md.
- **`AUDIT.md`** (2026-05-06). Source of audit-cycle settling
  shapes across v0.1.11–v0.1.18.
- **`AGENTS.md`** "Settled Decisions" (2026-05-06). Source of D1–D16.
- **`reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md`** (today).
  Source of D16.
- **`reporting/plans/tactical_plan_v0_1_x.md`** (2026-05-06).
  Source of current v0.2.x row state + v0.2.0 hard-deps post-D16.
- **`reporting/plans/risks_and_open_questions.md`** (2026-05-06
  freshness header). Source of R-T-03 RESOLVED status (cli.py rot
  closed at v0.1.17 W-29) + active risk/open-question posture.
- **`reporting/plans/v0_1_10/audit_findings.md`** through
  **v0_1_18/RELEASE_PROOF.md**. Source of per-cycle evidence.

### What's lifted from v1 vs. new

| Material | Source |
|---|---|
| H1–H5 hypotheses | Lifted; v0.1.11–v0.1.18 evidence integrated |
| Category claim | Lifted; sharpened to "agent-wrapper" |
| Settled decisions D1–D12 | Lifted; D4 status updated |
| Settled decisions D13–D16 | NEW v0.1.11–post-v0.1.18 |
| Strategic posture (§6) | Lifted; §6.3 promoted to present-tense; §6.4 publishable contribution sharpened |
| Major waves (§7) | Re-baselined timeline from 2026-05-06 |
| Settled-but-now-falsifiable (§5) | NEW shape — covers full v0.1.x track |
| Scope-expansion §8.5 | Updated with father-session evidence |
| What v1.0 looks like (§9) | Lifted; provenance updated; W-2U-WEARABLE/DOGFOOD criterion added |
| Decision branches (§10) | Lifted; Branch 1 + Branch 4 updated |

### Refresh cadence

- Strategic plan v2 reviewed every two minor releases. Next:
  post-v0.2.0 ship.
- Hypotheses (H1–H5) re-evaluated annually OR when their
  falsification criterion is reachable.
- Settled decisions never reopened casually.
- Decision branches (§10) updated as their "decision needed by"
  milestones approach.

### What this doc does NOT cover

- Per-release execution detail → `tactical_plan_v0_1_x.md`.
- How to evaluate correctness → `eval_strategy/v1.md`.
- How to measure project value → `success_framework_v1.md`.
- What could derail this plan → `risks_and_open_questions.md`.
- Operational lessons from 18 cycles → `post_v0_1_18/v0_1_x_retro.md`
  (companion doc to this one).

### What v1 still does that v2 doesn't replace

`strategic_plan_v1.md` remains the historical snapshot of strategic
posture at v0.1.10. It is preserved unedited as evidence — both
because the doc itself documents how the project's thesis converged,
and because v2 cites it as a primary source. **Do not edit v1
in place.** If a future cycle needs to refer to "what we believed
at v0.1.10," v1 is that record.

---

*Authored: 2026-05-06 by Claude in extended planning session.
Next scheduled review: post-v0.2.0 ship.*
