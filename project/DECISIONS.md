# Project Decisions

**Status:** Canonical post-reframe decision log, aligned to framing v2
on 2026-05-11.

This file records project-level decisions made during the runtime-contract
reframe. It is the place to recover decisions that otherwise lived only in
conversation. It overrides historical HAI product plans when they conflict,
but it does not replace runtime-specific invariants in `AGENTS.md` or the
HAI operator docs under `hai/docs/`.

## Decision Index

| ID | Decision | Current effect |
|---|---|---|
| D-PROJ-001 | The repo is a runtime-contract research repo, not a HAI product repo. | Root docs lead with the paper, GovernedAgentBench, and the runtime contract. |
| D-PROJ-002 | The north star is governed local operation over sensitive user-owned data. | Health is a demonstrator, not the paper's topic. |
| D-PROJ-003 | HAI remains active as the first reference runtime. | Runtime work continues only when it supports the paper, benchmark, HAI paper-readiness, or maintenance. |
| D-PROJ-004 | GovernedAgentBench is the benchmark name and artifact. | Do not revive HACO-Bench naming without a new maintainer decision. |
| D-PROJ-005 | The paper title leads with the claim, not the benchmark. | Historical working-title package; superseded by D-PROJ-018's locked merged-paper title. |
| D-PROJ-006 | The paper is conservative and measurement-first. | Claims are conditional on benchmark results; null results narrow the claim. |
| D-PROJ-007 | The health boundary is part of the contract. | No diagnosis, treatment, prescribing, autonomous medical decisions, or private health rows in public fixtures. |
| D-PROJ-008 | Experiments include local, cloud, fine-tuned, rule, and scaffold-ablation conditions. | Avoid optimizing only for local-vs-cloud rhetoric. |
| D-PROJ-009 | The minimum benchmark path does not require all six HAI domains. | Prioritize task families that test the contract honestly; domain breadth is support evidence. |
| D-PROJ-010 | Documentation alignment is the current work gate. | If a cold agent would recover the old objective, fix docs before new implementation. |
| D-PROJ-011 | Current docs and historical provenance must stay separated. | Active docs live under `project/`, `research/`, `benchmark/`, and `hai/`; `hai/reporting/` is HAI proof/history. |
| D-PROJ-012 | The repo shape is owner-based, not support-function-based. | `project/`, `hai/`, `benchmark/`, and `research/` are the physical top-level lanes; root tooling files remain only because tools discover them there. |
| D-PROJ-013 | Runtime is the primary axis of variation in the headline experiment. | `runtime_mode` × `model_class` cross-product replaces the prompt-vs-no-prompt comparison as the workhorse experiment. Supersedes the prompt-first reading of D-PROJ-008 for the headline experiment. |
| D-PROJ-014 | The deployment-realistic prompt is held constant across every benchmark condition. | No `with_manifest` vs `without_manifest` ablation in v1. Withholding the manifest produces a sandbagged baseline; the comparison is uninformative for the runtime claim. |
| D-PROJ-015 | Benchmark schemas split `condition` into `runtime_mode` and `model_class`. | `trajectory.schema.json`, `score.schema.json`, and `task.schema.json` are bumped to v2. The single `condition` enum is removed. Pre-existing (v1) trajectories cannot be loaded by the v2 scorer; clean break. |
| D-PROJ-016 | HAI is frozen as a product (2026-05-08). v0.2.0 PyPI is the reference snapshot the paper and benchmark pin against. No v0.2.1/v0.2.2/v0.2.3 product cycles. | HAI runtime changes ship only via the `WP-RUNTIME-FIX-NNN` template in service of paper or benchmark work. No HAI release ladder. |
| D-PROJ-017 | Round-1 audit outcome locks six architectural answers for the runtime-first reframe. | (a) HAI capabilities-manifest schema bumps to `agent_cli_contract.v2` for paper-readiness; the v0.2.3 freeze rule retired. (b) M5 (`agent_safe`) and M6 (`proposal_gate`) stay separate; Phase 2 builds a real CLI-dispatch-level `agent_safe` enforcer. (c) M7 refusal is built as a centralized `core/refusal/` runtime seam. (d) Transaction integrity is held-constant non-ablatable invariant (M9-TX); M8 narrowed to evidence-reference emission. (e) Tier 5 (fine-tuning) moves to a future-work appendix in CLAIM_LADDER.md. (f) `no_runtime` runtime mode renamed to `no_runtime_enforcement`. |
| D-PROJ-018 | Merged paper trajectory locked. | Paper 1 and the Engels extension merge into one NeurIPS 2027 main-conference submission titled "Deterministic Software Contracts as Trusted Monitors in AI Control Protocols." Supersedes D-PROJ-005's working-title package. |
| D-PROJ-019 | Engels pilot July 2026 is the merge-decision gate. | Run the locked July 2026 pilot protocol; keep the merged-paper trajectory only if the six-clause commit rule passes, otherwise revert to separate trajectories. |
| D-PROJ-020 | Predeclared model roster and USD 1,500 cost ceiling are locked. | Paper-claim runs use the D-FRAME-020 roster discipline and D-FRAME-023 hard model-API ceiling. |
| D-PROJ-021 | The targeted adversarial layer is constitutive. | The threat model is capability failure plus targeted adversarial testing, with paper-killer preempts built into the design. |
| D-PROJ-022 | Paper 2 redirects to S1 fine-tuning of bounded operators. | Fine-tuning is future work for ICML 2028 or NeurIPS 2028; paper 1 sets up the recipe but makes no fine-tuned performance claim. |
| D-PROJ-023 | Phase 2 documentation alignment is the current cycle. | `framing_v2/CONVERGED.md` is the top source of truth; Phase 2 propagates it across paper, benchmark, project, HAI, operating, and historical docs before final repo-wide audit. |

## Open Project Decisions

No open project decisions block Phase 2 documentation alignment.
Venue, title, trajectory, model roster, threat model, cost ceiling, and
paper-2 disposition are locked by D-PROJ-018 through D-PROJ-023.

## D-PROJ-001: Research Repo, Not HAI Product Repo

**Decision.** This repository is no longer best understood as "the HAI
product repo." It is a research-engineering repo studying runtime
contracts for bounded agents.

**Rationale.** The career and application leverage comes from a paper,
benchmark, and reproducible systems/evals artifact. HAI alone is strong
engineering, but the new objective is to extract the research artifact
from it.

**Implications.**

- The root `README.md` is research-facing.
- HAI operator documentation lives under `hai/docs/`.
- HAI v1 polish is subordinate unless it directly supports the paper,
  GovernedAgentBench, HAI paper-readiness, or reproducible baselines.

## D-PROJ-002: North Star

**Decision.** The north star is:

> Runtime contracts can make smaller local models viable operators for
> bounded workflows over sensitive user-owned data by moving authority,
> validation, and audit from the model into enforceable local software.

**Rationale.** This is broader than personal health and maps to
research-engineering work on agent safety, evals, and runtime governance.

**Implications.**

- Personal wellness is the first sensitive-data reference domain.
- The paper should generalize to bounded operation over structured
  user-owned data.
- The model proposes, routes, clarifies, and explains; the runtime owns
  truth, validation, mutation, policy, and audit.

## D-PROJ-003: HAI As Reference Runtime

**Decision.** HAI continues as active software, but its project role is
reference runtime and demonstrator.

**Rationale.** The runtime makes the paper testable. It also gives
reviewers a real system rather than a purely notional benchmark.

**Implications.**

- Keep HAI maintenance that protects the contract, tests, install path,
  privacy posture, and benchmark reproducibility.
- Defer new user-product breadth unless it is paper-critical.
- Do not delete historical HAI plans; classify them as provenance or
  support-lane backlog.

## D-PROJ-004: GovernedAgentBench

**Decision.** The benchmark is named GovernedAgentBench.

**Rationale.** The name leads with governed operation rather than health,
which keeps the benchmark aligned with the research claim.

**Implications.**

- Use `benchmark/governed_agent_bench/` as the benchmark root.
- Use GovernedAgentBench in the paper, roadmap, eval strategy, and
  reports.
- Do not reopen HACO-Bench naming without an explicit maintainer
  decision.

## D-PROJ-005: Title Leads With Claim

**Decision.** The working paper title package is:

**Runtime Contracts for Local Agents Over Sensitive User-Owned Data**

**Subtitle:** A Personal-Wellness Reference Runtime, GovernedAgentBench,
and Model-Scale Study

**Rationale.** The benchmark matters, but the paper should lead with the
research claim and architecture. GovernedAgentBench is the evaluation
artifact supporting that claim.

**Current caveat.** Superseded by D-PROJ-018. The current title is
**Deterministic Software Contracts as Trusted Monitors in AI Control
Protocols**.

## D-PROJ-006: Conservative Measurement Posture

**Decision.** The paper should be conservative and measurement-first.

**Rationale.** The aim is not to assert that runtime contracts prove a
grand thesis. The aim is to measure whether the contract improves bounded
operation, reduces unsafe behavior, and shifts the model-size threshold
under fixed metrics.

**Implications.**

- Prefer "we test whether..." over "we show..." until results exist.
- Predefine metrics and thresholds before interpreting outcomes.
- Report weak or null results honestly and narrow the claim.
- Do not rely on product anecdotes as the primary evidence.

## D-PROJ-007: Non-Clinical Health Boundary

**Decision.** The health boundary is part of the evaluated contract.

**Rationale.** The reference runtime touches wellness data. The research
claim must not depend on diagnosis, treatment, prescribing, or autonomous
medical decisions.

**Implications.**

- Public fixtures and fine-tuning data must not include private health
  rows.
- Benchmark tasks must not require clinical interpretation.
- Clinical-boundary obedience is a scored behavior, not a footnote.

## D-PROJ-008: Experimental Scope

**Decision.** The empirical program includes:

- rule baselines;
- local prompt-only models;
- local models with manifest / contract access;
- cloud prompt-only models;
- cloud models with manifest / contract access;
- fine-tuned local operators;
- fine-tuned local operators with live manifest access;
- scaffold ablations.

**Rationale.** The motivation is bounded operation over sensitive data.
Local models sharpen the privacy, cost, and deployment story, but the
benchmark must separate model capability from runtime governance.

## D-PROJ-009: Domain Scope For MVP

**Decision.** The minimum benchmark and paper path does not require all
six HAI domains.

**Rationale.** The empirical claim is about contract-governed operation,
not wellness-domain coverage. A smaller domain set can be sufficient if
the task families test command validity, schema validity, mutation
boundaries, refusal, evidence faithfulness, recovery, and drift.

**Implications.**

- Do not add domains or data sources before submission merely to make HAI
  feel more product-complete.
- Use six-domain breadth as demonstrator evidence when it is cheap and
  already present.
- Prioritize benchmark task families over domain count.

## D-PROJ-010: Documentation Alignment Gate

**Decision.** Internal documentation alignment is the current gate before
substantial new implementation.

**Rationale.** The project was reframed heavily. If a fresh session
recovers the old objective, future work will optimize the wrong target.

**Exit condition.** A cold agent can answer from repo docs alone:

- What is the research claim?
- What is the runtime contract?
- What does GovernedAgentBench measure?
- Why is HAI still active?
- Which docs are current versus historical?
- What is out of scope before submission?
- What empirical systems are compared?
- What health boundary is non-negotiable?

## D-PROJ-011: Documentation Architecture

**Decision.** The repo separates current docs from historical provenance.

**Current roots.**

- `project/`: project frame, decisions, operating model, roadmap,
  hypotheses, repo map, and project-level alignment tests.
- `research/runtime_contracts_paper/`: paper and eval strategy.
- `benchmark/`: benchmark artifact and benchmark-specific verification.
- `hai/`: HAI source, docs, verification, assets, release proof,
  historical plans, archives, and frozen prototypes.
- Root: tool-discovered entrypoints and metadata only.

**Implications.**

- Do not add new current HAI docs under `hai/reporting/docs/`.
- Do not rewrite historical cycle records to pretend they had the new
  frame.
- Fix indexes and active control docs when old plans might be mistaken
  for current priority.

## D-PROJ-016: HAI Frozen As A Product

**Decision.** HAI is frozen as a product as of 2026-05-08. The
v0.2.0 PyPI release is the reference-runtime snapshot the paper and
GovernedAgentBench will pin against. There is no v0.2.1, v0.2.2, or
v0.2.3 product cycle.

**Rationale.** Career strategy bets on the runtime-contract paper +
GovernedAgentBench as the legible artifacts. Continuing the HAI
v0.2.x release ladder (insight ledger W53, LLM-judge W58J,
capabilities-manifest schema freeze) burns calendar on product
polish that does not move the paper or benchmark. The reframe at
D-PROJ-003 ranked HAI v1 polish below research; the freeze converts
that ranking into an explicit stop, not just a deprioritisation.

**Implications.**

- HAI runtime changes ship only via the `WP-RUNTIME-FIX-NNN`
  template in service of paper or benchmark work. No new HAI
  release cycles, no new tactical-plan rows, no PyPI uploads.
- The v0.2.0 PyPI release stays as the reference snapshot.
- AGENTS.md "Settled Decisions" entries that reference the v0.2.3
  schema freeze and the v0.2.x schema-additions ladder (W52, W53,
  W58J) are obsolete; D-PROJ-017 retires them.
- HAI defects discovered while executing the paper plan are fixed
  through `WP-RUNTIME-FIX-NNN` packets. The fixes can land on the
  v0.2.0 line, but they are not "v0.2.1 product work" — they are
  research-support runtime patches.
- Personal-use intake, recommendations, and daily-loop usage are
  not affected. The freeze is on the product development surface,
  not on the maintainer's daily HAI use.

## D-PROJ-017: Round-1 Audit Locks Six Architectural Answers

**Decision.** The Codex round-1 audit of the runtime-first reframe
returned `PLAN_INCOHERENT` with 20 findings. Round-1 closeout locks
six architectural answers that round-2 work executes against:

1. **Manifest schema bump authorized.** HAI's
   `agent_cli_contract.v1` bumps to `v2` for paper-readiness work.
   The pre-existing v0.2.3 freeze rule is retired (D-PROJ-016
   already removed v0.2.3 as a cycle anyway).
2. **M5 + M6 stay separate.** Phase 2 builds a real
   CLI-dispatch-level `agent_safe` enforcer so `no_agent_safe` and
   `no_proposal_gate` are independently ablatable. This adds ~2-3
   weeks to Phase 2 versus the cheaper merge-into-one path.
3. **M7 refusal built as one canonical seam.** A new
   `core/refusal/` module owns the refusal contract. Existing
   per-domain validators may inform the design, but the deliverable
   is a centralized runtime-owned surface, not an incremental
   augmentation of skills.
4. **Transaction integrity held constant.** Atomic state-graph
   writes are a non-ablatable invariant called `M9-TX` in the
   inventory. M8 (`audit_chain`) narrows to evidence-reference
   emission only. The `no_audit_chain` mode disables evidence
   pointers, not transactions.
5. **Tier 5 moves to a future-work appendix.** Fine-tuning is
   deferred per D-PROJ-T; the workshop floor is Tier 0 + partial
   Tier 1. Tier 5 stays in `CLAIM_LADDER.md` as a clearly-labeled
   appendix, not as the top of the headline ladder.
6. **`no_runtime` runtime mode renamed to `no_runtime_enforcement`.**
   M1-M3 are explicitly held-constant harness infrastructure; the
   ablation only disables M4-M8.

**Rationale.** Round-1 audit caught real architectural issues with
the same-session reframe. The maintainer adjudicated each call
explicitly. The locked answers are the round-2 execution baseline.

**Implications.**

- AGENTS.md "Settled Decisions" entries about the v0.2.3 capabilities-
  manifest freeze and the W52/W53/W58J schema-additions ladder are
  obsolete and removed by this decision.
- Phase 2 of `HAI_PAPER_READINESS_EXECUTION.md` grows: dispatch
  enforcer added; calendar grows ~2-3 weeks.
- `MECHANISM_INVENTORY.md` is rewritten with the M5/M6 separation,
  the M7 build path, M8 narrowed, and the new M9-TX held-constant
  invariant.
- Schema enums rename `no_runtime` → `no_runtime_enforcement`.
- `CLAIM_LADDER.md` moves Tier 5 to an appendix.
- `WP-DISPATCH-001` is a new packet under Phase 2 owning the
  dispatch-level enforcer.

## D-PROJ-013: Runtime As Primary Axis Of Variation

**Decision.** The headline experiment in the runtime-contracts paper
varies the runtime, not the prompt. The prompt is held constant at
deployment-realistic full information.

**Rationale.** The paper claim is about the runtime contract. Varying
the prompt by withholding the manifest produces a sandbagged baseline:
"model with full info beats model with no info" is already in the
literature (BFCL, ToolLLM, Gorilla) and does not differentiate this
work. Holding the prompt constant and varying the runtime makes any
score gap attributable to the runtime alone.

**Implications.**

- The `runtime_mode` × `model_class` cross-product is the workhorse
  experiment.
- D-PROJ-008's "local prompt-only" condition is *not* part of the
  headline experiment. It may resurface as a future defense-in-depth
  experiment but is out of scope for v1.
- `HAI_PAPER_READINESS_EXECUTION.md` is the operational plan for this.

## D-PROJ-014: Deployment-Realistic Prompt Held Constant

**Decision.** Every benchmark condition emits the full
deployment-realistic prompt to the model: manifest + contract notes +
refusal taxonomy. There is no `with_manifest` vs `without_manifest`
condition.

**Rationale.** Withholding the manifest is a sandbagged-baseline
critique reviewers will land. The realistic deployment context always
gives the agent its API spec; testing what happens when you don't is a
trivial result. The runtime's contribution is what we're measuring;
that requires holding the prompt constant.

**Implications.**

- Harness has exactly one prompt-build path (see
  `WP-HARNESS-PROMPT-001`).
- The trajectory and score schemas drop the prompt-condition axis.
- The CLAIM_LADDER's Tier 1 is rephrased around mechanism effect, not
  prompt-help.

## D-PROJ-015: Benchmark Schema Split

**Decision.** Trajectory, score, and task schemas split the single
`condition` enum into two orthogonal fields: `runtime_mode` and
`model_class`. All three schemas bump to `v2`.

**Rationale.** The v1 `condition` enum mixed two axes (prompt
condition × model class) into one string, obscuring the experimental
structure. Splitting them makes the cross-product visible in the data
layer; reviewers reading the dataset can see the design without
reading the paper.

**Implications.**

- `benchmark/governed_agent_bench/schema/trajectory.schema.json` v2
  requires `runtime_mode` and `model_class`.
- `benchmark/governed_agent_bench/schema/score.schema.json` v2 same;
  also adds `mechanism` to violations.
- `benchmark/governed_agent_bench/schema/task.schema.json` v2 adds
  optional `load_bearing_mechanisms` and `runtime_modes_in_scope`.
- The schema-contract test in `benchmark/verification/tests/` is
  updated to assert the new shape.

## D-PROJ-012: Repository Ownership Model

**Decision.** The repo shape is owner-based:

- `project/` — project memory, decisions, roadmap, operating model, and
  repo-shape documentation.
- `hai/` — HAI reference runtime lane: runtime implementation, HAI docs,
  HAI verification, HAI assets, and HAI reporting/provenance.
- `benchmark/` — GovernedAgentBench lane: benchmark specs, schemas,
  tasks, scorer, baselines, reports, and benchmark verification.
- `research/` — paper lane: paper frame, draft, prior art, claims,
  experiment design, and release package planning.

**Rationale.** Support functions such as verification and reporting are
not first-class project artifacts. They should be owned by the artifact
they verify or report on. The highest-level repo shape should teach the
new objective: project frame, HAI reference runtime, benchmark
measurement instrument, and research paper.

**Current shape.** The physical tree now follows the owner model:

- `hai/src/health_agent_infra/`, `hai/docs/`, `hai/verification/`,
  `hai/assets/`, and `hai/reporting/` are owned by `hai/`.
- `benchmark/governed_agent_bench/` and `benchmark/verification/` are
  owned by `benchmark/`.
- `project/*.md` and `project/tests/` are owned by `project/`.
- `pyproject.toml`, `uv.lock`, `AGENTS.md`, and `CLAUDE.md` remain at
  root because external tools discover them there.

**Implications.**

- Do not recreate root `verification/`, root `reporting/`, root `src/`,
  root `docs/`, or root `benchmarks/` as permanent project-level
  artifacts.
- New planning docs should state their owner lane.
- Future file moves should preserve the owner model unless there is an
  explicit project-level decision to change it.

## D-PROJ-018: Merged Paper Trajectory Locked

**Decision.** Paper 1 and the Engels Backdoor Code extension are merged
into a single NeurIPS 2027 main-conference submission titled:

**Deterministic Software Contracts as Trusted Monitors in AI Control
Protocols**

**Provenance.** `research/runtime_contracts_paper/framing_v2/CONVERGED.md`
2026-05-11; inherits D-FRAME-009, D-FRAME-016, and D-FRAME-008.

**Rationale.** The merged trajectory is stronger than maintaining a
separate architecture paper and later Engels paper: it gives the paper a
clear AI-control lineage, one benchmark intervention, and a concrete
scaling-laws-for-oversight extension.

**Implications.**

- D-PROJ-005's working-title package is historical.
- Project cold-start docs should lead with the merged-paper title and
  NeurIPS 2027 main-conference target.
- HAI remains a reference runtime, not the top-level product objective.
- The July 2026 Engels pilot is the gate that can still revert the
  merged trajectory.

## D-PROJ-019: Engels Pilot As Merge-Decision Gate

**Decision.** The July 2026 Engels pilot is the decision gate for
keeping the merged-paper trajectory.

**Provenance.** `framing_v2/CONVERGED.md` 2026-05-11; inherits
D-FRAME-011 and D-FRAME-018.

**Locked shape.**

- 60 APPS competition samples, with 10 smoke samples separate.
- Three Houdinis: Qwen2.5-7B-Instruct Turbo, Claude 3.5 Haiku, and
  Claude Sonnet 4.
- Guards: DRG-0 and Claude 3.5 Haiku LLM Guard.
- Estimated pilot API cost: about USD 18.60 under May 2026 pricing
  snapshots.
- Six-clause commit rule and six-clause revert rule.

**Implications.**

- If the pilot passes the commit rule, continue the merged
  main-conference trajectory.
- If the pilot fails, revert to Trajectory A: separate workshop and
  conference papers.
- The "five Houdini attempts per sample" claim remains a pre-pilot
  verification item against arXiv:2504.18530 Section 4.

## D-PROJ-020: Predeclared Model Roster And Cost Ceiling

**Decision.** Paper-claim runs use the locked D-FRAME-020 model roster
and a hard USD 1,500 ceiling across model API calls.

**Provenance.** `framing_v2/CONVERGED.md` 2026-05-11; inherits
D-FRAME-020 and D-FRAME-023.

**Locked shape.**

- Six Houdinis: Qwen2.5-3B local HF, Qwen2.5-7B-Instruct-Turbo
  Together, Qwen2.5-32B Fireworks, Qwen2.5-72B Fireworks, Haiku 3.5
  retired pilot-only, and Sonnet 4 with 2026-06-15 retirement binding.
- Three Guards: DRG-0 deterministic, Haiku 3.5 retired pilot-only, and
  `gpt-4o-mini-2024-07-18`.
- Successor names are locked for future cells: `claude-haiku-4-5-20251001`
  and `claude-sonnet-4-6` if the Sonnet 4 window is missed.

**Implications.**

- Model selection is predeclared, not chosen after observing results.
- T3/T4 paper-claim score artifacts require the relevant roster hash.
- Any cell that would breach the USD 1,500 ceiling must be dropped or
  re-scoped rather than silently expanding spend.

## D-PROJ-021: Adversarial Layer Is Constitutive

**Decision.** The paper's threat model is capability failure plus a
targeted adversarial layer. The no-red-team option considered in
D-FRAME-015 is closed and should not reappear as a current proposal.

**Provenance.** `framing_v2/CONVERGED.md` 2026-05-11; inherits
D-FRAME-015, D-FRAME-022, and D-FRAME-019.

**Locked shape.**

- 50 trajectories total.
- Refusal bypass: 8.
- Mutation escalation: 8.
- Audit tampering: 8.
- Schema evasion: 8.
- Adaptive attack against DRG-0: 18.

**Implications.**

- The adversarial layer is not optional garnish; it is part of making
  the AI-control framing legible.
- The paper still does not claim a full control safety case for
  scheming, sandbagged, or password-locked frontier models.
- The two paper-killer preempts are mandatory: framing-overclaim and
  Greenblatt DRG-artifact concerns.

## D-PROJ-022: Paper 2 Redirects To S1 Fine-Tuning

**Decision.** Paper 2 becomes the S1 fine-tuning sequel:

> Trained operators reach contract-compliance at smaller scales than
> untrained operators.

Target venue is ICML 2028 or NeurIPS 2028. Paper 1 sets up the recipe
but makes no fine-tuned performance claim.

**Provenance.** `framing_v2/CONVERGED.md` 2026-05-11; inherits
D-FRAME-010 and D-FRAME-027.

**Implications.**

- Keep the `fine_tuned_local` schema slot.
- Reserve GovernedAgentBench v2 split language for the sequel.
- Pre-register the no-private-data recipe as future work only.
- Do not let paper 1 imply fine-tuned operator results.

## D-PROJ-023: Phase 2 Documentation Alignment Cycle

**Decision.** Phase 2 documentation alignment is the current
cross-repo cycle. `framing_v2/CONVERGED.md` is the top-level paper
framing source of truth until a later maintainer decision supersedes it.

**Provenance.** `framing_v2/CONVERGED.md` 2026-05-11 and
`framing_v2/ORCHESTRATOR_STATE.md`.

**Implications.**

- Cold-start docs must tell the merged-paper story before further
  implementation work becomes the default.
- The capability-elicitation reframe closed by D-FRAME-014 must not
  appear as a current claim.
- The no-red-team threat model closed by D-FRAME-015 must not appear as
  a current claim.
- Phase 2 uses batch edits with one end-of-phase audit, not a separate
  audit after every batch.
