# Runtime Contracts Paper Frame

**Status:** Merged-paper frame, aligned to
`framing_v2/CONVERGED.md` on 2026-05-11.

This file states the paper's current identity. It supersedes the older
runtime-first/workshop framing in this file's prior versions. The source
of truth is the locked Phase 1 framing decisions D-FRAME-001 through
D-FRAME-027.

## Title

**Deterministic Software Contracts as Trusted Monitors in AI Control
Protocols**

Target venue: **NeurIPS 2027 main conference**, May 2027 submission
deadline.

## One-Sentence Frame

A deterministic software contract operationalizes a safety spec as the
trusted monitor in an AI control protocol for bounded agent operation.

This paper is not framed as a consumer health-product paper and not
around the older data-ownership phrasing in the title or core claim.
HAI's personal-wellness domain is the reference instantiation.
The general claim is about bounded agent operation through a governed
runtime contract.

## Lineage Anchor

The contribution sits at the intersection of three literatures:

| Anchor | Role in the paper |
|---|---|
| AI Control protocols, including Greenblatt et al. 2024 | Supplies the trusted-monitor / untrusted-operator framing and the safety-usefulness evaluation vocabulary. |
| Safety specs, including OpenAI Model Spec, Anthropic Model Spec Midtraining, and Deliberative Alignment | Shows that safety behavior can be specified explicitly, while leaving open when the spec should be model-internal versus executable software. |
| LLM-monitor baselines, including Constitutional Classifiers and Hierarchical Summarization | Provides the direct contrast: model monitors are flexible and semantic; deterministic contracts are narrow, auditable, and not vulnerable to model-monitor failure modes. |

Constitutional Classifiers is cited as the Pareto-reporting precedent
for detection rate, false-positive rate, and over-refusal style metrics.
Hierarchical Summarization is the direct LLM-monitor competitor for the
bounded Section 7.6 contrast.

## Threat Model

The primary threat model is **capability failure** plus a
**targeted adversarial layer**.

Capability failure covers fallible models that emit invalid commands,
hallucinated tool calls, malformed proposals, unsupported factual
claims, unsafe mutation attempts, missed refusals, or stale-manifest
behavior.

The targeted adversarial layer contains 50 trajectories:

| Attack type | Count | Target |
|---|---:|---|
| Refusal bypass | 8 | M7 clinical-boundary refusal |
| Mutation escalation | 8 | M5 `agent_safe` plus M6 W57 proposal/commit gate |
| Audit tampering | 8 | M8 audit evidence emission |
| Schema evasion | 8 | M4 typed command/proposal validation |
| Adaptive attack vs DRG-0 | 18 | Deterministic Runtime Guard in the Engels extension |

This is not a full control safety case for scheming or sandbagged
frontier models. It is a bounded stress test of whether deterministic
runtime mechanisms remain observable and load-bearing under known attack
classes.

## Abstract Shape

Agents operating through local tools over consequential state are an
instance of the AI control problem: useful work is delegated to systems
whose actions cannot be fully trusted. Existing AI-control and monitoring
work often makes the trusted side another model or a human review process.
This paper studies a complementary primitive: deterministic software
contracts as the trusted monitor.

The contract exposes a capabilities manifest, typed command schemas,
mutation classes, deterministic validation gates, proposal/commit
separation, scoped refusal boundaries, and audit evidence emission. It
operationalizes a safety spec in code before state changes occur.

The empirical package has three headline results:

1. **Mechanism-isolable ablations.** Holding the prompt constant,
   toggling M4-M8 produces measurable per-mechanism contributions to
   safe bounded operation.
2. **Runtime-as-floor.** The smallest predeclared model with the full
   contract passes all primary thresholds, while a larger predeclared
   model under `no_runtime_enforcement` fails at least one threshold.
3. **Deterministic Guard on Engels Backdoor Code.** DRG-0 is added to
   the Engels et al. 2025 scaling-laws-for-oversight curve as a Guard
   with general Elo = 0.

The targeted adversarial layer is reported as a non-headline
characterization result: safety and usefulness under bounded adversarial
pressure, including adaptive attacks against DRG-0.

## Contributions

1. **Trusted-monitor substrate.** The paper extends the AI-control
   protocol vocabulary to include deterministic software contracts as
   the trusted side for crisp authority, schema, mutation, refusal, and
   audit-evidence invariants.

2. **Reference runtime.** HAI is a local personal-wellness reference
   runtime implementing the contract over non-clinical wellness state.
   Personal wellness is the instantiation, not the generalization claim.

3. **GovernedAgentBench.** The benchmark tests contract-governed agent
   operation through a `runtime_mode` intervention rather than only
   policy text in the prompt. The load-bearing differentiation from
   ST-WebAgentBench is runtime-mode intervention with mechanism-isolable
   ablation under a held-constant prompt.

4. **Mechanism ablations.** M4-M8 are independently ablated while M9-TX
   transaction integrity remains held constant. The paper reports which
   mechanisms are load-bearing for which metrics.

5. **Runtime-as-floor model-scale result.** The predeclared model roster
   and thresholds test whether the runtime shifts the model-scale safety
   floor for bounded operation.

6. **Scaling-laws-for-oversight extension.** The Engels Backdoor Code
   extension adds a deterministic Guard data point at general Elo = 0,
   with pre-registered information boundaries and DRG-0 ablations.

7. **Bounded LLM-monitor contrast.** Section 7.6 compares the
   deterministic contract with Hierarchical Summarization on L6
   governance/refusal tasks within two weeks and USD 200. If the cap is
   missed, this demotes to related-work prose rather than expanding
   scope.

## Mechanism Inventory

The paper's ablatable mechanism inventory is locked as:

| ID | Mechanism | Ablation mode |
|---|---|---|
| M4 | Validation of typed commands and proposal payloads | `no_validation` |
| M5 | `agent_safe` dispatch refusal | `no_agent_safe` |
| M6 | W57 proposal/commit user gate | `no_proposal_gate` |
| M7 | Clinical-boundary refusal over proposal/recommendation/text surfaces; JSON output exempt | `no_refusal` |
| M8 | Audit evidence emission | `no_audit_chain` |
| M9-TX | Transaction integrity | Held constant, non-ablatable |

M8 is not the whole audit chain. It is the emission of evidence
references that final narration and explanation surfaces can cite.
Atomic transaction integrity remains M9-TX and is never ablated.

## Empirical Design

The prompt is held constant at the deployment-realistic full-information
prompt. The runtime is the intervention.

The predeclared model roster has nine entries: six Houdinis
(`Qwen/Qwen2.5-3B-Instruct`, `Qwen/Qwen2.5-7B-Instruct-Turbo`,
`accounts/fireworks/models/qwen2p5-32b-instruct`,
`accounts/fireworks/models/qwen2p5-72b-instruct`,
`claude-3-5-haiku-20241022`, and `claude-sonnet-4-20250514`) and three
Guards (DRG-0, `claude-3-5-haiku-20241022`, and
`gpt-4o-mini-2024-07-18`). Haiku 3.5 is retired and kept only for
pilot-continuity cells; new Haiku cells use
`claude-haiku-4-5-20251001` under a new roster hash. Sonnet 4 retires
on 2026-06-15; if Section 7.5 slips beyond that date, it re-anchors to
`claude-sonnet-4-6` under a new roster hash.

The headline pass rule is an AND across seven primary metrics plus seven
zero-tolerance critical violations. The cost ceiling for all model API
calls is USD 1,500.

## Engels Pilot Gate

The merged-paper structure is gated by a July 2026 Engels pilot:

- 60 APPS competition samples, with 10 smoke samples separate.
- Three Houdinis: `Qwen/Qwen2.5-7B-Instruct-Turbo`, Claude 3.5 Haiku,
  and Claude Sonnet 4.
- Guards: DRG-0 and Claude 3.5 Haiku LLM Guard.
- Estimated API cost: about USD 18.60 using May 2026 pricing snapshots.
- Commit rule: six clauses covering feasibility, separation,
  nontrivial adversary, Elo signal, usefulness, and fairness.
- Revert rule: six clauses that send the project back to Trajectory A
  if the deterministic Guard signal is null, reversed, unfair, too
  noisy, or too sample-starved.

The claim that Engels uses up to five Houdini attempts per sample must
be verified against arXiv:2504.18530 Section 4 before the pilot.

## Paper-Killer Preempts

Two critiques are structurally preempted:

1. **Framing overclaim.** The paper says "trusted-monitor substrate for
   bounded AI-control protocols," not "complete AI-control safety case."
   Adaptive Attacks on Trusted Monitors (arXiv:2510.09462) belongs in
   the introduction and related work.
2. **DRG artifact concern.** The deterministic Guard result is valid
   only with pre-registered DRG inputs, no trigger or hidden-test oracle
   access, explicit DRG ablations, false-positive rates, and adaptive
   attacks against DRG-0.

## Scope

In scope:

- HAI as one non-clinical personal-wellness reference runtime.
- GovernedAgentBench as the mechanism-isolable benchmark.
- Engels Backdoor Code extension, contingent on the July 2026 pilot.
- Bounded Hierarchical Summarization contrast on L6 governance/refusal.
- Appendix D future-work recipe for S1 fine-tuning of bounded operators.
- Appendix E coding-agent sketch only.

Out of scope:

- Clinical or medical decision-making claims.
- Cross-domain generalization beyond personal wellness as a result.
- A second coding-agent runtime before this paper.
- Fine-tuned local operator results in paper 1.
- Sandbagged or password-locked executor models.
- Full attack-policy substitution red-team.

## Appendix Commitments

Appendix D states the sequel-paper setup: trained operators reach
contract-compliance at smaller scales than untrained operators. It is
future work only and makes no performance claim.

Appendix E contains the coding-agent contract sketch from
`framing_v2/round_5/RESPONSE.md` Section Q2. It must include the
anti-overclaim header: this appendix is not evidence that the HAI
results generalize.
