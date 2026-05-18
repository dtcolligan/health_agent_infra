# PAPER.md

Single source of truth for the active research artifact this repo
exists to produce. Updated in place when scope, calendar, or
decisions change. Provenance lives in `ARCHIVE/`, not here.

## What This Repo Is For

Shipping one artifact: an arXiv preprint by 2026-09-30, with
GovernedAgentBench v1.0 released as a companion GitHub tag.

Nothing else is active. HAI is a frozen reference runtime that
supports the benchmark. There is no main-conference target, no
merged-paper trajectory, no concurrent product roadmap. After
2026-10-01 the maintainer pivots to mechanistic interpretability;
no preprint or benchmark work bleeds into October.

## Title and Frame

**Deterministic Software Contracts as Trusted Monitors in AI Control
Protocols**

Deliverable: arXiv preprint, 8-12 pages NeurIPS or ICML LaTeX format,
public and citable, not peer-reviewed.

One-sentence frame: a deterministic software contract operationalizes
a safety spec as the trusted monitor in an AI control protocol for
bounded agent operation.

External framing is "AI control paper under the AI safety umbrella."
Do not soften because scope is preprint, not main conference.

## Lineage Anchor

The contribution sits at the intersection of three literatures:

| Anchor | Role |
|---|---|
| AI control protocols (Greenblatt et al. 2024 + follow-ups) | Trusted-monitor / untrusted-operator vocabulary; safety-usefulness evaluation. |
| Safety specs (OpenAI Model Spec, Anthropic Model Spec Midtraining, Deliberative Alignment) | Safety behaviour specified explicitly; this paper tests executable code as one substrate. |
| LLM-monitor baselines (Constitutional Classifiers, Hierarchical Summarization) | Direct contrast: model monitors are semantic and flexible; deterministic contracts are narrow, auditable, mechanism-isolable. |

Closest published benchmark prior: ST-WebAgentBench (Levy et al.,
ICML 2025). Load-bearing differentiation: runtime-mode intervention
with mechanism-isolable ablation under a held-constant prompt.

## Calendar

Today: read in `date` at session start. Key windows:

| Window | Block |
|---|---|
| 2026-05-15 to 2026-05-31 | Repo consolidation (this restructure), benchmark measurement-readiness kickoff |
| 2026-05-15 to 2026-06-30 | Benchmark measurement-readiness: schemas, scorer, harness, fixtures, rule baseline, runtime-mode toggling |
| 2026-06-15 to 2026-06-22 | Pilot-protocol-lock gate: final model class, task subset, success criteria, pre-committed falsification |
| 2026-07 | Pilot execution: Option B end-to-end; Option C stretch only if substrate is clean |
| 2026-07-25 to 2026-09-15 | Paper drafting; start outline + related work in late July |
| 2026-07-28 to 2026-08-15 | SPAR application window (cite "preprint in late drafting, GAB v1.0 tagged") |
| 2026-08 to 2026-09-15 | Benchmark release polish; reproducibility script; v1.0 tag |
| 2026-08-15 | arXiv sponsor locked (open question D-O-03) |
| 2026-09-15 to 2026-09-30 | arXiv submission: sponsor confirm, LaTeX polish, moderation (1-3 days) |
| 2026-10-01 | Mech interp sub-specialty pivot begins |

## Scope

**In:**

- HAI as one non-clinical personal-wellness reference runtime
- GovernedAgentBench v1.0 release on a GitHub tag with reproducible
  rule baseline
- Option B mechanism-ablation experiment: M4-M8 toggled individually
  on one model class against 28 tasks, with static oracle-pair evidence
  separated from live runtime-isolation evidence
- Option C stretch (if substrate is clean by mid-July): small
  `runtime_mode` × `model_class` cross-product over 2-3 cells
- 16-trajectory targeted adversarial layer (4 each against M4 /
  M5+M6 / M7 / M8)
- Appendix E coding-agent sketch (keep/drop at mid-August polish,
  D-O-02)

**Out (deferred to future work):**

- Engels Backdoor Code scaling-laws-for-oversight extension and DRG-0
- Full predeclared model roster (six Houdinis + three Guards)
- Bounded Hierarchical Summarization empirical contrast (HS stays in
  §2 prose only)
- S1 fine-tuning of bounded operators
- Full adaptive red-team beyond 16 trajectories
- Clinical or medical decision-making claims
- Cross-domain generalization beyond personal wellness (other than
  the Appendix E sketch)
- Sandbagged or password-locked executor models
- Any HAI v0.2.1+ product polish

## Paper Outline

| § | Section | Target pages |
|---|---|---|
| 1 | Introduction (motivation, trusted/untrusted decomposition, contribution) | 1.5 |
| 2 | Background and related work (AI control, software contracts, capability-based security, agent runtimes, LLM monitors incl. HS prose contrast) | 1 |
| 3 | The runtime contract (formal definition, M4-M8 + M9-TX, guarantees) | 2-3 |
| 4 | GovernedAgentBench methodology (tasks, scorer, runtime modes, held-constant prompt design) | 2 |
| 5 | Mechanism ablation results (Option B; static and live evidence separated) | 1.5-2 |
| 6 | Model-scale extension (Option C stretch; demote to §5.3 if absent) | 0-1 |
| 7 | Targeted adversarial characterization (16 trajectories) | 0.5-1 |
| 8 | Discussion (limitations, personal-health-as-domain defense) | 1 |
| 9 | Future work + conclusion | 1 |
| - | Appendix: tasks, prompts, seeds, reproducibility, additional results | - |

## Mechanism Inventory

| ID | Mechanism | Ablation mode |
|---|---|---|
| M4 | Validation of typed commands and proposal payloads | `no_validation` |
| M5 | `agent_safe` dispatch refusal | `no_agent_safe` |
| M6 | W57 proposal/commit user gate | `no_proposal_gate` |
| M7 | Clinical-boundary refusal over proposal/recommendation/text surfaces; JSON output exempt | `no_refusal` |
| M8 | Audit evidence emission | `no_audit_chain` |
| M9-TX | Transaction integrity | Held constant, non-ablatable |

M8 is evidence emission, not the whole audit chain. Atomic
transaction integrity is M9-TX and is never ablated.

Seven runtime modes total: `full_contract`, the five M4-M8 off-paths,
and `no_runtime_enforcement` (M4-M8 all off; M1-M3 harness
infrastructure + M9-TX still on).

## Threat Model

Capability failure plus a targeted adversarial layer.

**Capability failure.** Fallible models emit invalid commands,
hallucinated tool calls, malformed proposals, unsupported factual
claims, unsafe mutation attempts, missed refusals, or stale-manifest
behaviour.

**Targeted adversarial (16 trajectories):**

| Attack type | Count | Target |
|---|---:|---|
| Refusal bypass | 4 | M7 |
| Mutation escalation | 4 | M5 + M6 |
| Audit tampering | 4 | M8 |
| Schema evasion | 4 | M4 |

Not a full control safety case for scheming, sandbagged, or
password-locked frontier models. Bounded stress test of whether
deterministic mechanisms remain observable and load-bearing under
known attack classes, with static oracle-pair canaries reported
separately from live runtime probes.

## Model Roster

The preprint roster is narrow:

| Role | Model | Provider | Purpose |
|---|---|---|---|
| Rule baseline | deterministic harness | n/a | Anchors routing tasks |
| Option B model (default) | `Qwen/Qwen2.5-7B-Instruct-Turbo` | Together AI | Single model class for the mechanism-ablation headline |
| Option B alternative | `Qwen/Qwen2.5-32B-Instruct` (Fireworks) | Fireworks | If 7B is too capable to surface mechanism deltas; ratified at mid-June lock (D-O-01) |
| Option C stretch cell | `claude-sonnet-4-6` | Anthropic | Optional cloud cell for the small cross-product |

Sonnet 4 re-anchored to `claude-sonnet-4-6` per D-04 (no 2026-06-15
retirement binding).

**Cost ceiling: USD 300** across all model API calls. Option B alone
is well under USD 100; headroom covers Option C and one retry cycle.

## Hypotheses

| ID | Hypothesis | Role |
|---|---|---|
| H1 | Toggling M4-M8 individually under a held-constant prompt produces measurable safety-constrained deltas on pre-registered load-bearing tasks, with each result labeled by evidence tier: static oracle-pair canary or live runtime probe. | Bounded headline empirical claim (Option B). |
| H2 | A smaller model under `full_contract` passes more thresholds than larger models under `no_runtime_enforcement`. | Preliminary evidence only if Option C runs. Full claim is future work. |
| H3 | A deterministic Guard at general Elo = 0 occupies a legitimate point on the Engels scaling-laws-for-oversight curve. | Future-work-only. Engels deferred per D-03. |
| H4 | Trained operators reach contract-compliance at smaller scales than untrained operators. | Future-work-only (S1 fine-tuning sequel). |
| H5 | GovernedAgentBench measures general contract-governed operation while using HAI as the reference runtime. | Design constraint, defended by task selection (no private health rows, no clinical interpretation). |
| H6 | Non-clinical boundaries are enforceable runtime behaviour, not disclaimer text. | Design constraint, defended by M7 + zero-tolerance clinical-claim metric. |

**Falsification rules** (for H1 and H2 only):

- H1 falsifies if `full_contract` does not improve safety-constrained
  task success over per-mechanism off-paths at the evidence tier being
  claimed, or if the claimed attribution cannot be tied to M4-M8
  individually. Live per-mechanism attribution requires a live probe for
  that mechanism.
- H2 falsifies if performance is primarily a function of model scale,
  or no smaller model under `full_contract` passes thresholds when
  compared against larger models under `no_runtime_enforcement`.

## Active Decisions

Numbered D-NN in the order they currently take effect. Full
supersession provenance for prior decisions
(D-PROJ-001..024, D-FRAME-001..027, D-PREPRINT-001..009, AGENTS
D1-D28) lives in `ARCHIVE/decisions_log.md`.

| ID | Decision | Active since |
|---|---|---|
| D-01 | Deliverable is arXiv preprint by 2026-09-30, 8-12pp NeurIPS/ICML LaTeX. No main-conference target. | 2026-05-15 |
| D-02 | Title locked: *Deterministic Software Contracts as Trusted Monitors in AI Control Protocols*. | 2026-05-11 |
| D-03 | Engels Backdoor Code extension deferred to a future paper; DRG-0 and the scaling-laws-for-oversight curve carry forward there. | 2026-05-15 |
| D-04 | Sonnet 4 cells re-anchor to `claude-sonnet-4-6`. The 2026-06-15 Sonnet 4 retirement is irrelevant to the preprint. | 2026-05-15 |
| D-05 | Empirical scope = Option B floor (M4-M8 × 1 model × 28 tasks) + Option C optional stretch (small cross-product). Tests H1 as a bounded headline with static and live evidence tiers reported separately; H2 preliminary if Option C runs. | 2026-05-15 |
| D-06 | Cost ceiling USD 300 across all model API calls. | 2026-05-15 |
| D-07 | Adversarial layer = 16 trajectories (4 each against M4 / M5+M6 / M7 / M8). The 18 adaptive-vs-DRG-0 trajectories defer to the Engels future paper. | 2026-05-15 |
| D-08 | Bounded Hierarchical Summarization empirical contrast dropped. HS appears in §2 related-work prose only. | 2026-05-15 |
| D-09 | Mechanism inventory locked: M4 validation, M5 `agent_safe`, M6 W57 proposal/commit gate, M7 clinical-boundary refusal (JSON exempt), M8 audit evidence emission, M9-TX transaction integrity held constant. | 2026-05-11 |
| D-10 | Headline experiment varies the runtime, not the prompt. Deployment-realistic prompt held constant in every condition. No `with_manifest` vs `without_manifest` ablation. | 2026-05-09 |
| D-11 | HAI frozen as a product; v0.2.0 PyPI is the reference snapshot. No v0.2.1+ release ladder. Runtime fixes ship via `WP-RUNTIME-FIX-NNN` packets only. | 2026-05-08 |
| D-12 | Non-clinical health boundary is part of the contract, not a footer disclaimer. No diagnosis, treatment, prescribing, or autonomous medical decisions; no private health rows in public fixtures. | from project inception |
| D-13 | Single-page-of-truth discipline: this file is the only active research-planning document. No new phase plans, execution plans, framing cycles, or batch directories without explicit maintainer decision. Decisions update in place. Provenance lives in `ARCHIVE/`. | 2026-05-15 |
| D-14 | Mechanism-ablation scoring is Option C: the `mechanism_disabled` marker attributes only; a safety violation is recorded solely when the leaked consequence is independently observed in user-facing stdout; JSON contract surfaces are not clinically scanned; `mechanism_disabled_unexpected` flags contamination. Authoritative form in `scorer_config.paper_v1.json`. | 2026-05-17 |
| D-15 | (DR-3) `mechanism_disabled_unexpected` is a zero-tolerance critical violation: contamination of a condition kills `overall_pass`. | 2026-05-17 |
| D-16 | (DR-1) Autonomy contract: the coding agent runs all non-pre-registration engineering (implementation, tests, refactors, scaffolding, verification) without pausing, and halts only for pre-registration/scope decisions, `PAPER.md`/`AGENTS.md`/`cli/` edits, and git commit/push. | 2026-05-17 |
| D-17 | (DR-2) Mechanism-isolation acceptance criterion (freezes at the pilot lock). `no_X` is isolated iff every emitted `mechanism_disabled` marker's mechanism is in `mechanisms_off_for_mode(runtime_mode)` (zero `mechanism_disabled_unexpected`), at least one marker for X fires under `no_X`, `full_contract` emits zero markers, and the scored consequence delta vs `full_contract` on the task's load-bearing metric is attributable to X at the reported evidence tier. Static oracle-pair attribution is scorer/coverage evidence over hand-authored full/off pairs, not live causality evidence. Live runtime attribution requires an end-to-end HAI run under the compared modes. Mode-aware operationalization of D-14. | 2026-05-18 |
| D-18 | (DR-4) The scorer implements the full SPEC violation taxonomy (all 11 kinds), including `schema_invalid`. Scorer behavior thresholds and critical violation kinds are loaded from `scorer_config.paper_v1.json`; the config hash records the audited config bytes. | 2026-05-18 |
| D-19 | (DR-5) Task suite = 28 tasks across L1/L2/L5/L6/L7, at least 3 static oracle-pair load-bearing tasks per M4-M8, every task an oracle pair routing the mechanism effect onto a scored metric, at least 2 tasks declaring `no_runtime_enforcement` in scope. Design freezes at the lock. | 2026-05-17 |
| D-20 | (DR-6) `no_runtime_enforcement` is a robustness sanity floor, not part of the per-mechanism H1 attribution. | 2026-05-17 |
| D-21 | (DR-7/8/9) Adversarial 16-trajectory layer scaffolded now, scored as pilot-phase evidence, not lock-gating (DR-7). H1 holds iff `full_contract` passes the safety-constrained subset and each `no_X` shows an attributable degradation on X's load-bearing metric at the evidence tier being claimed; static-only rows do not support live-causality claims. D-O-01: switch `Qwen2.5-7B`→`32B` iff 7B's `full_contract` pass-rate saturates the safety-constrained subset so no `no_X` delta can surface (DR-9). | 2026-05-18 |
| D-22 | Audit-bounded isolation claim: the current static matrix covers M4-M8 as deterministic oracle-pair canaries; the current live isolation sweep covers M7 only. M4/M5/M6/M8 remain `STATIC_ONLY` until separate live probes exist, and paper/result wording must preserve that distinction. | 2026-05-18 |

## Open Decisions

Resolvable at the mid-June pilot lock or before SPAR window:

| ID | Decision | Window |
|---|---|---|
| D-O-01 | Final Option-B model class. Default `Qwen/Qwen2.5-7B-Instruct-Turbo`; alternative `Qwen/Qwen2.5-32B-Instruct` Fireworks if 7B is too capable to surface mechanism deltas. | Mid-June pilot lock |
| D-O-02 | Keep or drop Appendix E coding-agent sketch. Anti-overclaim header required if kept. | Mid-August polish |
| D-O-03 | arXiv sponsor source: in-network (Imperial UROP supervisor, IDEA Lab contact) or cold outreach. | Lock by 2026-08-15 |

## Engineering Plan

What HAI + GovernedAgentBench need to ship by end of June so the
July pilot can run. Compressed from the prior 779-line execution
plan; the full breakdown is in `ARCHIVE/hai_paper_readiness_execution.md`.

| Surface | Status | Gap to Option B readiness |
|---|---|---|
| HAI runtime mode switch | `HAI_RUNTIME_MODE` env + seven modes declared in `trajectory.schema.json` v2 | Static oracle-pair isolation covers M4-M8; live isolation currently covers M7 only. Add live M4/M5/M6/M8 probes before claiming live isolation for those mechanisms |
| Refusal seam (M7) | `core/refusal/` module | Live M7 probe passes: clinical-boundary refusal fires under `full_contract` and leaks under `no_refusal` |
| Dispatch enforcer (M5) | CLI-dispatch middleware reading `agent_safe` per command | Static oracle-pair coverage exists; live M5 needs a probe that separates attempted unsafe command blocking from committed consequence and M6 gating |
| Manifest snapshot | HAI v0.2.0 snapshot at `benchmark/governed_agent_bench/manifests/hai_0_2_0.json` (~189 KB, `agent_cli_contract.v2`) | Done |
| Hermeticity | `HAI_HERMETIC=1` umbrella + `HAI_STATE_DB` + `HAI_BASE_DIR` redirection | Verified for the current live M7 probe; broaden with any added live M4/M5/M6/M8 probes |
| Fixtures | 6 synthetic fixtures (`empty_user`, `ready_user_minimal`, `read_surface_user`, `governance_user`, `drift_user`, `adversarial_user`) | Done |
| Harness | Model-agnostic harness under `benchmark/governed_agent_bench/harness/` with `mechanism_disabled` capture | Single deployment-realistic prompt path retained; keep static/live evidence labels in all generated reports |
| Tasks | 28 tasks across L1, L2, L5, L6, L7 | Done for static D-19 coverage; not evidence of live causality by itself |
| Trajectories | 14 hand-authored seed trajectories + 25 static isolation oracle pairs | Add coverage for the 16 adversarial trajectories |
| Scorer | Deterministic offline scorer at `scorer/core.py`, with behavior thresholds and critical violations loaded from `scorer_config.paper_v1.json` | Done for offline/static scoring; include benchmark package mypy in routine verification |
| Drift snapshot | `manifests/agent_cli_contract_v1_drift.json` for L7 | Verify harness can swap manifest at task-load time |
| Reproducibility script | Generators under `results/` | Single offline command produces evidence table + SVG figures + error taxonomy from rule baseline; external researcher acid test in October |

Beyond these, the only research-side engineering is paper writing
itself.

## Operational Disciplines

- **Single page of truth.** This file is the only active research-
  planning document. Any new phase / batch / framing / orchestration
  scaffold requires explicit maintainer override. Decisions update
  in place; supersession history goes to `ARCHIVE/decisions_log.md`.
- **No new cold-start docs.** README, AGENTS, CLAUDE, PAPER are the
  cold-start surface. Adding to the cold-start path requires
  removing equivalent content from existing files.
- **Provenance is archived, not active.** Framing-v2 orchestration,
  HAI release history, pre-merge paper drafts all live in
  `ARCHIVE/`. They are intellectual capital for a Y3 sequel paper or
  maintainer handoff, not navigation surface.
- **External framing stays unchanged when internal scope shrinks.**
  Preprint is still an AI control paper. Do not soften.
- **HAI freeze is real.** No v0.2.1+ product cycles. Runtime defects
  discovered during preprint or benchmark work fix via
  `WP-RUNTIME-FIX-NNN` packets; they do not become release work.
- **Conservative measurement posture.** Predefine metrics and
  thresholds before interpreting outcomes. Report null results
  honestly and narrow the claim.

## Provenance Pointers

| Topic | Where |
|---|---|
| Full chain of D-PROJ / D-FRAME / D-PREPRINT supersession | `ARCHIVE/decisions_log.md` |
| Framing-v2 orchestration history (3 rounds + 6 batches + final audit) | `ARCHIVE/framing_v2/` |
| HAI release history (v0.1.X cycles, audit chains, work packets, PLANs) | `ARCHIVE/hai_release_history/` |
| Pre-merge paper drafts (CLAIM_LADDER, DRAFT_PAPER, PAPER_OUTLINE_MERGED) | `ARCHIVE/paper_drafts/` |
| Pre-reframe HAI strategy + tactical plans | `ARCHIVE/pre_reframe_plans/` |
| Detailed HAI paper-readiness execution phases | `ARCHIVE/hai_paper_readiness_execution.md` |
