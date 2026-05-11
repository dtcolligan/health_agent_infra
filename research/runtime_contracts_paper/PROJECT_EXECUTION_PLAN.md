# Project Execution Plan

**Status:** Merged-paper execution plan, aligned to
`framing_v2/CONVERGED.md` on 2026-05-11.

This plan coordinates the paper titled **Deterministic Software
Contracts as Trusted Monitors in AI Control Protocols** for the NeurIPS
2027 main conference, May 2027 submission deadline.

## Objective

Deliver a defensible main-conference paper showing that deterministic
software contracts can act as trusted monitors for bounded agent
operation. The paper merges the runtime-contract architecture and
GovernedAgentBench work with the Engels Backdoor Code extension. The
Engels pilot remains the July/August 2026 decision gate.

## Non-Negotiables

- Source of truth: `framing_v2/CONVERGED.md` and locked decisions
  D-FRAME-001 through D-FRAME-027.
- Headline framing: deterministic software contract operationalizes a
  safety spec as the trusted monitor in an AI control protocol for
  bounded agent operation.
- HAI is a reference runtime, not a consumer health-product bet.
- Personal wellness is a non-clinical instantiation; no clinical claims.
- Prompt is held constant; runtime mode is the intervention.
- M4-M8 are ablatable; M9-TX transaction integrity is held constant.
- Cost ceiling: USD 1,500 for model API calls.
- Sonnet 4 retirement binding: `claude-sonnet-4-20250514` retires on
  2026-06-15; Section 7.5 paper-claim runs must complete before then or
  re-anchor to `claude-sonnet-4-6` under a new roster hash.

## Calendar

| Date | Milestone | Required outcome |
|---|---|---|
| 2026-05-11 | Phase 1 convergence | DONE: 27 locked framing decisions |
| 2026-06-15 | Sonnet 4 retirement | Finish any Section 7.5 Sonnet 4 paper-claim run before this date or re-anchor |
| 2026-07-15 target | Phase 2 doc alignment | Batch 1-6 docs, audit-findings closure, and final repo-wide audit complete |
| 2026-07-20 to 2026-08-05 target | Engels pilot | 60 APPS competition samples, DRG-0 + Haiku Guard, three Houdinis |
| 2026-08-10 target | Pilot decision gate | Commit merged paper if six-clause rule passes; otherwise revert to Trajectory A |
| 2026-11 target | Mechanism ablations complete | T1/T2/T3 GovernedAgentBench evidence complete |
| 2027-02 target | Full Engels run | Section 7.5 full Backdoor Code extension complete |
| 2027-03 target | Red-team complete | 50 targeted trajectories complete |
| 2027-03 target | Bounded HS contrast complete | Section 7.6 L6 contrast complete or demoted |
| 2027-04 target | Manuscript v1 | Full draft ready for internal review |
| 2027-05 target | NeurIPS 2027 submission | Main-conference submission package ready |

## Workstreams

### W0 - Phase 2 Documentation Alignment

Purpose: make the repo internally consistent with the locked framing
before more implementation work resumes.

Deliverables:

- Batch 1 paper-planning files aligned.
- Batch 2 benchmark specs aligned.
- Batch 3 project cold-start docs aligned.
- Batch 4 HAI runtime docs lightly aligned.
- Batch 5 operating contracts aligned.
- Batch 6 historical provenance marked superseded.
- F-CDX-RFR-R1-01..11 explicitly closed against merged framing.
- Final repo-wide audit checks terminology, calendar, title, threat
  model, scope, and stale A2/B1 references.

### W1 - HAI Paper-Readiness Support

Purpose: freeze HAI as the paper reference runtime.

Deliverables:

- HAI v0.2.0 manifest snapshot at
  `benchmark/governed_agent_bench/manifests/hai_0_2_0.json` (about
  189 KB).
- Contract schema `agent_cli_contract.v2`.
- Runtime modes and mechanism-disabled audit markers.
- Refusal behavior in runtime code, not skill prose.
- Hermetic fixtures and no live wearable dependency.

This is support work. It exists to stabilize the contract, unblock the
benchmark, and make baselines reproducible.

### W2 - GovernedAgentBench Measurement Readiness

Purpose: produce deterministic benchmark/scorer artifacts before model
runs.

Deliverables:

- Task families L1-L7 with explicit mechanism coverage.
- Trajectory and score schemas requiring `claim_tier` and roster/config
  references for T3/T4 claims.
- Scorer config file and `scorer_config_hash`.
- Predeclared model roster hash.
- Prompt template hash and manifest snapshot binding.
- Baseline harness that varies `runtime_mode` while holding prompt
  constant.

### W3 - Mechanism Ablations

Purpose: support Claims A and B.

Deliverables:

- Section 7.1 infrastructure checks.
- Section 7.2 mechanism-effect evidence.
- Section 7.3 component ranking evidence.
- Section 7.4 runtime-as-floor result.

The Section 7.1-7.4 matrix follows `PAPER_OUTLINE_MERGED.md`: M4-M8
single-mechanism ablations, `no_runtime_enforcement`, M9-TX held
constant, and prompt held constant.

### W4 - Engels Pilot And Full Run

Purpose: decide whether the merged paper remains viable and, if so,
produce the Section 7.5 headline result.

Pilot deliverables:

- APPS competition sample manifest: 60 primary + 10 smoke, selected by
  frozen sha256 seed.
- DRG-0 modules 1-6 implemented with config hash.
- Houdinis: Qwen2.5-7B-Instruct-Turbo, Claude 3.5 Haiku, Claude
  Sonnet 4.
- Guards: DRG-0 and Claude 3.5 Haiku LLM Guard.
- Estimated API cost note with May 2026 pricing snapshot, about USD
  18.60.
- Six-clause commit rule and six-clause revert rule evaluated.
- Pre-pilot verification of the "five Houdini attempts per sample"
  claim against arXiv:2504.18530 Section 4.

Full-run deliverables if pilot passes:

- Full predeclared roster/guard matrix.
- DRG-0 false-positive analysis on clean and benign rewrite samples.
- DRG-0 ablations: static-only, fuzz-only, combined.
- Adaptive attacks against DRG-0.
- Domain Elo curve with DRG-0 at general Elo = 0.

### W5 - Targeted Adversarial Layer

Purpose: preempt the AI-control overclaim and Greenblatt DRG-artifact
critiques.

Deliverables:

- 50 trajectories: refusal bypass 8, mutation escalation 8, audit
  tampering 8, schema evasion 8, adaptive-vs-DRG-0 18.
- Deterministic adjudication where possible.
- Fixed rubric for ambiguous cases.
- Dom blind adjudication and secondary `gpt-4o-mini-2024-07-18` judge.
- Safety/usefulness Pareto by attack type.

### W6 - Bounded Hierarchical Summarization Contrast

Purpose: make the direct LLM-monitor contrast concrete without letting
it absorb the paper.

Deliverables:

- L6 governance/refusal contrast, optional L5 only if early.
- Two-week Dom-time cap and USD 200 API cap.
- `hs_monitor_v1`, prompt hashes, verdict schema.
- Detection rate, false-positive rate, uncertain rate, and
  citation-validity rate.
- Constitutional Classifiers cited as Pareto-reporting precedent.

If the cap is missed, demote to Section 2.3 prose.

### W7 - Manuscript

Purpose: produce the NeurIPS paper.

Deliverables:

- Section 1 introduces deterministic contracts as trusted-monitor
  substrate for bounded AI-control protocols.
- Section 2 uses the triple lineage anchor.
- Section 3 locks the capability-failure + targeted-adversarial threat
  model.
- Sections 4-6 define architecture, HAI, and GovernedAgentBench.
- Sections 7-8 report mechanism ablations, Engels, HS, and adversarial
  layer.
- Section 10 names the pilot-null and HS-cap fallback clauses.
- Section 11 states the S1 fine-tuning sequel headline.
- Appendix D includes the fine-tuning recipe as future work only.
- Appendix E includes the coding-agent sketch with anti-overclaim
  header.

## Decision Gates

### Engels Pilot Gate

Commit to merged scope only if the six-clause pilot rule passes:
feasibility, separation, nontrivial adversary, Elo signal, usefulness,
and fairness.

Revert to Trajectory A if DRG-0 is null, worse than Haiku Guard,
statistically unsupported, unfair, too false-positive-prone, or too
sample-starved.

### HS Cap Gate

If bounded HS misses the two-week or USD 200 cap, it demotes to related
work. Do not expand Section 7.6.

### Budget Gate

All model API calls fit within USD 1,500. Cells that cannot fit are
dropped or demoted, not silently rerun into scope creep.

## Explicitly Out Of Scope

- Clinical or medical decision-making.
- Consumer health-product positioning.
- A second coding-agent runtime before paper 1.
- Fine-tuned local operator results in paper 1.
- Full attack-policy substitution red-team.
- Sandbagged or password-locked executor models.
- Cross-domain generalization as a result.

## Agent Execution Rule

Agents should work from the bounded work packets in `WORK_PACKETS.md`.
Do not start broad implementation work from this plan alone. Each
packet must name allowed files, dependencies, acceptance criteria, and
non-goals.
