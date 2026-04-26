# Falsifiable hypotheses

Five bets the project is making. Each can turn out wrong; each has a
falsification criterion. Stated explicitly so future audits can ask
"is this still true?" rather than re-derive the entire strategic
case.

This file is a stable lift from
[`reporting/plans/multi_release_roadmap.md § 3`](reporting/plans/multi_release_roadmap.md).
The roadmap is the working document; this file is the citable
artifact.

---

## H1. The hard problem in personal health AI is interpretability of outcomes, not better recommendations

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

## H2. Local-first beats hosted for the daily-runtime use case

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

## H3. User-authored intent + targets + bounded supersession is the right substrate for governed adaptation

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

## H4. LLM agents driving deterministic CLIs > LLM agents reasoning end-to-end

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

## H5. A small set of governed ledgers + a strict code-vs-skill boundary scales further than a multi-agent prose-driven architecture

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

## Inspiration

This project's framing draws on **AgentSpec** (arXiv 2503.18666) for
runtime enforcement, **PHIA** (Nature Communications 2025) for the
single-agent + code-execution shape, **SePA** (arXiv 2509.04752) for
the personalisation-lives-downstream finding, and **Bloom / GPTCoach**
(arXiv 2510.05449) for the user-owned mutation primitive. None of
these are direct ancestors; the project is an independent take on a
research direction these papers help characterise.
