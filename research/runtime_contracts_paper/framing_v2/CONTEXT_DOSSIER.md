# Context Dossier — Full Briefing for the Orchestrator

**Read this entire file before doing anything else.** It captures the
project state, history, decisions, and constraints that the
orchestrator needs to know to operate. The prior conversation that
produced this dossier is gone; this file is the durable replacement.

## 1. Who the user is

**Dom Colligan.** First-year EFDS (Economics, Finance & Data Science)
student at Imperial College London. Graduating summer 2028. Based in
London. Strong quantitative reasoning, comfortable with
ML/foundations (Karpathy NN: Zero to Hero), built micrograd from
scratch.

**Career strategy** (load-bearing for every framing decision):

- Primary target: **Research Engineer / ML Engineer hybrid at Anthropic
  London**, specifically in the agent safety / evals / runtime
  governance subspecialty (not pretraining-systems, not interpretability).
- Application window: autumn 2027 for summer 2028 RE start.
- Open London role currently posted: Research Engineer / Scientist,
  Alignment Science, names "AI Control" and "Alignment Stress-testing"
  as focus areas (£260-370K).
- Anthropic London expanding 200 → 800 staff at One Triton Square.
- Paper is being optimized as a legibility artifact for this RE
  application track.

**Communication preferences:**

- Direct, terse register.
- Dislikes hedging, em dashes, AI stylistic markers.
- Values pushback and honest assessment over validation.
- Socratic / definition-first learning style.
- He drives the Codex terminal himself, manually.

**Bandwidth:**

- Summer 2026: heavy commitments (Cyber Mangrove + Lettingweb,
  IDEA Lab). ~15-20 effective hours/week for paper work.
- Academic year 2026-2027: coursework dominates. ~12 hrs/week.
- Total available bandwidth May 2026 → May 2027: ~720 hours.

## 2. The project

Public repo: github.com/dtcolligan/health_agent_infra. MIT-licensed.
Project name "Health Lab" / HAI.

**Three artifacts:**

- **Runtime contract** — architecture/intervention: capabilities
  manifest, typed commands, mutation classes, `agent_safe`, schemas,
  proposal/commit separation, deterministic gates, policy, audit.
- **HAI** — personal-wellness reference runtime, packaged as
  `health-agent-infra` Python wheel, exposed via local `hai` CLI.
  Currently v0.2.0 on PyPI. **Frozen as product** as of 2026-05-08
  per D-PROJ-016; no v0.2.1 cycle. Runtime fixes only via
  WP-RUNTIME-FIX-NNN packets.
- **GovernedAgentBench** — benchmark for contract-governed agent
  operation. Pre-measurement-ready as of v0.2.0.

**Eight-bucket architecture model** (canonical): `pull`, `clean`,
`merge_human_inputs`, `research`, `interpretation`, `reporting`,
`writeback`, `safety`.

**Six health domains** (subordinate to bucket model): recovery,
running, sleep, stress, strength, nutrition. Nutrition is macros-only
v1.

**Research reframe** (D-PROJ-017, 2026-05-07): The repo's active
objective is the runtime-contract paper plus GovernedAgentBench. HAI
continues as personal-wellness reference runtime, subordinate to the
research artifacts unless directly supporting them.

## 3. Where the paper was, where it is now

### Pre-reframe (before 2026-05-09)

"Runtime Contracts for Local Agents Over Sensitive User-Owned Data."
Workshop-tier paper, AI Safety adjacent, narrow domain framing.

### Round-1 conversation (this dossier captures rounds 1+2 from 2026-05-11)

Started with three framing options:
- A1 — AI Control direct (Greenblatt et al. 2024 lineage)
- A2 — capability-elicitation reframe (Greenblatt + Burns et al.
  weak-to-strong)
- A3 — "pure ML research" pivot

Initial recommendation: A2 + B1 (no red-team) at workshop venue.

### Round-2 conversation findings (4 parallel agents)

Substantial updates that invalidated initial recommendation:

1. **A2 is overclaimed.** The weak-monitor/strong-executor claim is
   already published (arXiv:2508.19461). The Burns connection
   misreads the paper (Burns is about finetuning-generalization, not
   oversight architecture). "Capability elicitation" has a specific
   Redwood-anchored meaning (anti-sandbagging) — term collision.
   **Drop A2.**

2. **B1 is fatal.** AI Control venues require adversarial red-team
   substitution as constitutive. Zero capability-failure-only papers
   in the lineage have been accepted. Quote-worthy from ControlArena:
   *"an adversarial game between teams: Blue Team... Red Team:
   Creates attack policies."* A1+B1 gets desk-rejected on framing.

3. **Lineage anchor was too narrow.** Anthropic's 2025-2026 vocabulary
   has shifted to **triple-anchor**: control protocols + safety specs
   + LLM-monitor baselines.

4. **NeurIPS Safe GenAI Workshop may not run in 2026.** Single-point
   venue dependency is risky.

5. **ST-WebAgentBench is closest competitor** (Levy et al., ICML 2025,
   arXiv:2410.06703). Must differentiate explicitly.

6. **Hierarchical Summarization** (Anthropic Feb 2025) is direct
   competitor as Anthropic's own LLM-based runtime monitor.

7. **Engels et al. 2025 "Scaling Laws For Scalable Oversight"**
   (arXiv:2504.18530, NeurIPS 2025 spotlight) — extending it with a
   deterministic-runtime Guard at general Elo = 0 is the single best
   ML-research-flavored contribution.

### Final framing (locked at end of round 2)

**Headline framing:** *"A deterministic software contract that
operationalizes a safety spec as the trusted monitor in an AI control
protocol for bounded agent operation."*

**The novel claim that survives literature contact:** extending the
trusted/untrusted decomposition in AI control protocols so the
trusted side can be **deterministic software**, not a model or human.
No published control paper has done this. Adaptive Attacks on Trusted
Monitors (arXiv:2510.09462) explicitly identifies LLM monitors as a
single point of failure — that's the opening.

### Merge decision (2026-05-11)

Dom decided to **merge paper 1 + paper 2** into a single
main-conference paper. The Engels Backdoor Code extension (previously
paper 2 headline) becomes paper 1's §7.5 empirical climax. Target
venue: **NeurIPS 2027 main conference, May 2027 deadline.**

**Decision gate:** 2-week Engels pilot in July 2026 determines whether
the merge commits or reverts to Trajectory A (separate workshop +
conference papers). ~$30-50 USD cost, ~80 hours of pilot work.

### Current draft outline

The merged paper structure is captured in
`research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md` (315
lines). Read it for: title candidates, abstract draft, contributions
list, 11-section structure, scope deltas vs current
`DRAFT_PAPER.md`, calendar checkpoints, decision gates.

## 4. Locked decisions (as of 2026-05-11, pre-round-3)

| Decision | Locked value | Provenance |
|---|---|---|
| Headline framing | "Deterministic software contract that operationalizes a safety spec as the trusted monitor in an AI control protocol for bounded agent operation" | Round 2 synthesis |
| Lineage anchor | Triple-anchor (control + safety spec + LLM-monitor baselines) | Round 2 R2 agent |
| Threat model | Capability-failure + targeted adversarial layer | Round 2 R1 agent |
| Headline empirical | Engels Backdoor Code extension at general Elo = 0 | Round 2 R4 agent + merge decision |
| Direct competitor | Hierarchical Summarization (Anthropic Feb 2025) — explicit contrast required | Round 2 R2 agent |
| Closest prior on benchmark | ST-WebAgentBench (Levy et al., ICML 2025) — Framing D differentiation | Round 2 R3 agent |
| Benchmark framing | "Contract-as-intervention with measured model-scale substitution" (Framing D) | Round 2 R3 agent |
| Target venue | NeurIPS 2027 main conference (May 2027 deadline) | Merge decision |
| Trajectory | Merged paper 1+2, paper 2 redirects to S1 fine-tuning (RBR + Deliberative Alignment lineage) for ICML 2028 / NeurIPS 2028 | Merge decision |
| Decision gate | Engels pilot July 2026; revert to Trajectory A if pilot fails | Merge decision |
| Domain extension | Coding-agent slice → appendix sketch only OR cut. **Open.** | Round 3 to lock |
| Drop from title | "User-owned structured data" (dilutes legibility) | Round 2 R2 agent |
| Personal wellness role | Instantiation, not framing | Round 2 R2 agent |

## 5. Open decisions for round 3+

High-priority (round 3 candidates):

1. **Title finalization** — 4 candidates in PAPER_OUTLINE_MERGED.md, no
   convergence.
2. **Mechanism inventory truth audit** — F-CDX-RFR-R1-08/09/10 flagged
   that M5 (`agent_safe`), M6 (proposal gate), M7 (refusal) may not
   be independently ablatable in current HAI source. If they're
   entangled, the §7 ablation structure must collapse.
3. **Engels pilot protocol design** — exact sample sizes, prompts,
   hashing, decoding settings, Houdini/Guard pairings.
4. **Anthropic adversarial reviewer simulation** — what's the single
   strongest critique a Mrinank Sharma / Ethan Perez / Buck Shlegeris
   reviewer would land?

Medium-priority (round 4-5 candidates):

5. **Hierarchical Summarization empirical contrast** — full
   reimplementation OR rhetorical-only? Cost and feasibility.
6. **Coding-agent slice** — appendix sketch (5-10 hrs), full
   second-domain (3-6 weeks), or cut entirely?
7. **Predeclared model roster** — exact 6 Houdinis + 3 Guards with
   provider snapshots, parameter counts, quantization. Per
   F-CDX-RFR-R1-07.
8. **Predeclared thresholds** — exact pass values for each primary
   metric. Per F-CDX-RFR-R1-06.
9. **Adversarial attack policy** — 50 trajectories across 4 attack
   types → concrete protocol per attack type.
10. **ST-WebAgentBench detailed positioning** — concrete comparison
    table.
11. **Paper 2 sketch precision** — S1 fine-tuning direction concrete or
    pivot.
12. **Constitutional Classifiers head-to-head** — additional baseline
    or skip?

Lower-priority (later rounds):

13. **Reproducibility surface** — what makes this replicable for an
    external team?
14. **Cross-domain extension appendix** — what does the coding-agent
    sketch look like exactly?
15. **Scope-cut decisions** pre-committed for pilot-fail or
    experiment-fail.
16. **Threat model formalization** — precise scope language for
    §3.1/§3.2/§3.3.

## 6. Reference files

The orchestrator must know what's where.

### Authoritative paper-planning files (current state)

- `research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md` — the
  merged paper outline. **Source of truth for the paper structure**
  until Phase 2 supersedes the older files.
- `research/runtime_contracts_paper/PAPER_FRAME.md` — pre-merge frame.
  Will be rewritten in Phase 2.
- `research/runtime_contracts_paper/CLAIM_LADDER.md` — pre-merge
  ladder. Will be rewritten in Phase 2.
- `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`
  — execution plan for runtime-first reframe. Pre-merge. Will be
  rewritten in Phase 2.
- `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`,
  `PROJECT_EXECUTION_PLAN.md`, `BASELINES_AND_ABLATIONS_PLAN.md` —
  pre-merge. Phase 2.
- `research/runtime_contracts_paper/DRAFT_PAPER.md` — pre-merge draft
  skeleton. Will be either rewritten or formally superseded by
  `PAPER_OUTLINE_MERGED.md` in Phase 2.

### Audit findings still open (pre-Phase-2 cleanup)

- `research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response.md`
  — 11 findings F-CDX-RFR-R1-01 through F-CDX-RFR-R1-11 against the
  pre-merge runtime-first reframe. **All 11 must close as part of
  Phase 2 doc alignment.**

### Benchmark spec files

- `benchmark/governed_agent_bench/README.md`
- `benchmark/governed_agent_bench/BENCHMARK_SPEC.md`
- `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`
- `benchmark/governed_agent_bench/SCORING_SPEC.md`
- `benchmark/governed_agent_bench/schema/trajectory.schema.json`
- `benchmark/governed_agent_bench/schema/score.schema.json`

All pre-merge. Phase 2.

### Project cold-start files

- `project/FRAME.md` — canonical research framing
- `project/DECISIONS.md` — decision log (D-PROJ-001..017 currently)
- `project/OPERATING_MODEL.md` — operating model + doc-alignment gate
- `project/HYPOTHESES.md` — current hypotheses
- `project/ROADMAP.md` — now/next
- `project/REPO_MAP.md` — file map

All currently aligned to runtime-first reframe (pre-merge). Will need
Phase 2 updates.

### Operating contracts

- `AGENTS.md` — universal operating contract. ~600 lines.
- `CLAUDE.md` — Claude-Code-specific layer on top of AGENTS.md.
- `README.md` — top-level research-facing overview.

Vocabulary alignment in Phase 2.

### HAI runtime docs (light touch in Phase 2)

- `hai/docs/hai_reference_runtime.md` — install, workflow, domains
- `hai/docs/runtime_contract_overview.md` — one-page architecture
- `hai/docs/current_system_state.md` — version, schema head, etc.
- `hai/docs/architecture.md` — full pipeline

Most don't need rewriting. Update references to paper framing only.

### Historical provenance (mark superseded in Phase 2)

- `hai/reporting/plans/post_v0_1_18/strategic_plan_v2.md`
- `hai/reporting/plans/success_framework_v1.md`
- `hai/reporting/plans/eval_strategy/v1.md`
- `hai/reporting/plans/risks_and_open_questions.md`

## 7. Key external references

Cited heavily across the framing rounds. The orchestrator should know
these exist:

| Reference | URL / arXiv | Why it matters |
|---|---|---|
| Greenblatt et al. 2024, AI Control | arXiv:2312.06942 | Primary lineage anchor |
| Engels et al. 2025, Scaling Laws For Scalable Oversight | arXiv:2504.18530 | Paper §7.5 headline empirical |
| ST-WebAgentBench (Levy et al.) | arXiv:2410.06703 | Closest published benchmark prior |
| Hierarchical Summarization | alignment.anthropic.com/2025/summarization-for-monitoring/ | Direct competitor |
| Adaptive Attacks on Trusted Monitors | arXiv:2510.09462 | Motivates deterministic alternative |
| Constitutional Classifiers | arXiv:2501.18837 | Anthropic LLM-classifier monitor baseline |
| OpenAI Model Spec | model-spec.openai.com | Safety-spec vocabulary anchor |
| Anthropic Model Spec Midtraining | arXiv:2605.02087 | Anthropic adopting spec vocabulary |
| Deliberative Alignment | arXiv:2412.16339 | Spec-at-inference lineage |
| Ctrl-Z (Bhatt et al.) | arXiv:2504.10374 | Agent-environment control extension |
| ControlArena | control-arena.aisi.org.uk | UK AISI control framework |
| Reliable Weak-to-Strong Monitoring of LLM Agents | arXiv:2508.19461 | Closest prior on weak-monitor framing |

## 8. Codex `/goal` command

Per the user: `/goal` is a Codex slash command that runs research/work
for extended durations. The user invokes Codex in a separate terminal
he drives manually. The orchestrator writes prompts; the user
paste-loads them into Codex; Codex produces output; the user pastes
the output back into the orchestrator's session (or saves to file).

**This means the orchestrator cannot dispatch Codex automatically.**
The orchestrator writes `PROMPT.md` files in round directories and
tells Dom when to paste them. Dom returns `RESPONSE.md` content
(either by pasting or by Codex writing directly to disk).

## 9. The orchestration architecture

Two phases. Within each phase, a worker-audit-integrate loop.

**Phase 1: Research.** Open-ended depth, mechanical convergence stop.
Worker = Codex. Auditor = Claude Code agent (via Agent tool dispatch).

**Phase 2: Documentation alignment.** Batched per file group. Audit
only at the end of the phase (mechanical edits are lower error than
research). Worker = Codex. Auditor = Claude Code agent.

For both phases:
- Orchestrator writes `PROMPT.md`.
- Worker (Codex) produces `RESPONSE.md`.
- Auditor (Claude Code Agent) produces `AUDIT_RESPONSE.md`.
- Orchestrator writes `SYNTHESIS.md` and updates `ORCHESTRATOR_STATE.md`.

## 10. What "done" looks like

**Phase 1 done:** `CONVERGED.md` exists. Every framing decision listed
in this dossier's §5 is locked. No round-N+1 prompt has high-yield
questions left to ask.

**Phase 2 done:** Every file in §6 reflects the locked framing. The
F-CDX-RFR-R1-01..11 audit findings are explicitly closed. Repo-wide
final audit (dispatched once at end of Phase 2) returns clean.

**Overall done:** Dom has a paper plan that survives adversarial
review and a repo that internally agrees with the plan, ready for the
implementation cycles toward the May 2027 NeurIPS submission.

## 11. Things to push back on

The user explicitly wants pushback. Push back if:

- A proposed sub-task expands scope outside the locked decisions.
- A round's audit returns clean too quickly — re-check whether the
  audit was thorough enough.
- The user proposes skipping the Engels pilot.
- The user proposes reopening A2 (capability-elicitation reframe).
- The user proposes adding adversarial-full-substitution red-team to
  paper 1 (that's paper 2 / paper 3 territory now).
- Anyone proposes reopening the HAI freeze for non-paper-critical work.

## 12. What is explicitly OUT OF SCOPE for this orchestration

- Implementing the runtime contract or benchmark code.
- Running the Engels pilot.
- Editing HAI source.
- Anything not directly serving the paper framing or doc alignment.

If Dom asks for something outside scope, surface it and ask whether to
suspend the orchestration or defer the request.
