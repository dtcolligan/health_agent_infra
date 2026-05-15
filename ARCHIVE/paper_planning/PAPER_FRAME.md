# Runtime Contracts Paper Frame

**Status:** Preprint-scope paper frame, aligned to
`framing_v2/PREPRINT_RESCOPE.md` on 2026-05-15.

This file states the paper's current identity. It supersedes the older
runtime-first/workshop and the merged NeurIPS-2027-main framing in
this file's prior versions. The current source of truth is
`framing_v2/PREPRINT_RESCOPE.md`, which preserves
`framing_v2/CONVERGED.md` as historical NeurIPS-2027-main framing
record.

## Title

**Deterministic Software Contracts as Trusted Monitors in AI Control
Protocols**

Target deliverable: **arXiv preprint, 8-12 pages NeurIPS or ICML LaTeX
format, public and citable, not peer-reviewed.** Submission target
2026-09-30.

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

The primary threat model class is **capability failure** plus a
**targeted adversarial layer**.

Capability failure covers fallible models that emit invalid commands,
hallucinated tool calls, malformed proposals, unsupported factual
claims, unsafe mutation attempts, missed refusals, or stale-manifest
behavior.

The targeted adversarial layer for the preprint contains 16
trajectories (D-PREPRINT-006):

| Attack type | Preprint count | Target |
|---|---:|---|
| Refusal bypass | 4 | M7 clinical-boundary refusal |
| Mutation escalation | 4 | M5 `agent_safe` plus M6 W57 proposal/commit gate |
| Audit tampering | 4 | M8 audit evidence emission |
| Schema evasion | 4 | M4 typed command/proposal validation |
| Adaptive attack vs DRG-0 | 0 (deferred) | Future Engels paper |

The 18 adaptive-vs-DRG-0 trajectories carry forward to a future
Engels paper alongside DRG-0 and the scaling-laws-for-oversight curve
extension.

This is not a full control safety case for scheming or sandbagged
frontier models. It is a bounded stress test of whether deterministic
runtime mechanisms remain observable and load-bearing under known
attack classes.

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

The preprint's empirical package has one headline result and one
optional stretch:

1. **Mechanism-isolable ablations (headline).** Holding the prompt
   constant, toggling M4-M8 individually on one model class across
   ~25-30 GovernedAgentBench tasks in the HAI reference domain
   produces measurable per-mechanism contributions to safe bounded
   operation.
2. **Runtime-as-floor (preliminary, optional).** If a small
   `runtime_mode` × `model_class` cross-product runs, the smaller
   predeclared model under `full_contract` passes more thresholds than
   larger models under `no_runtime_enforcement`. Reported as
   preliminary evidence, not headline.

A bounded targeted adversarial layer (16 trajectories: 4 each against
M4, M5+M6, M7, M8) is reported as a non-headline characterization
result: safety and usefulness under bounded adversarial pressure.

Future work threads explicitly deferred:

- **Deterministic Guard on Engels Backdoor Code.** DRG-0 on the
  scaling-laws-for-oversight curve. Future paper.
- **Full predeclared model roster (six Houdinis + three Guards).**
  Future paper.
- **S1 fine-tuning of bounded operators.** Future paper.
- **Bounded Hierarchical Summarization empirical contrast.** Future
  work; HS remains in §2 related-work prose only in the preprint.
- **Full adaptive red-team beyond 16 trajectories.** Future work.

## Contributions

1. **Trusted-monitor substrate.** The paper extends the AI-control
   protocol vocabulary to include deterministic software contracts as
   the trusted side for crisp authority, schema, mutation, refusal, and
   audit-evidence invariants.

2. **Reference runtime.** HAI is a local personal-wellness reference
   runtime implementing the contract over non-clinical wellness state.
   Personal wellness is the instantiation, not the generalization claim.

3. **GovernedAgentBench v1.0 release.** The benchmark tests contract-
   governed agent operation through a `runtime_mode` intervention
   rather than only policy text in the prompt. The load-bearing
   differentiation from ST-WebAgentBench is runtime-mode intervention
   with mechanism-isolable ablation under a held-constant prompt.
   Released as a GitHub tag alongside the preprint; reproducible by an
   external researcher without maintainer involvement.

4. **Mechanism ablations.** M4-M8 are independently ablated on one
   model class while M9-TX transaction integrity remains held constant.
   The preprint reports which mechanisms are load-bearing for which
   metrics. This is the headline empirical contribution.

5. **Runtime-as-floor (preliminary, optional).** If the Option C
   stretch runs, a small `runtime_mode` × `model_class` cross-product
   reports preliminary evidence that the runtime shifts the model-scale
   safety floor for bounded operation. Full claim is future work.

Deferred to future work (not in the preprint):

- Engels Backdoor Code scaling-laws-for-oversight extension.
- Bounded Hierarchical Summarization empirical contrast on L6.
- Full predeclared model roster cross-product.
- S1 fine-tuning of bounded operators.
- Full adaptive red-team beyond 16 trajectories.

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

The preprint model roster narrows to one Option-B model class (default
`Qwen/Qwen2.5-7B-Instruct-Turbo`, final choice ratified at the mid-June
pilot lock) for the headline mechanism-ablation experiment. If the
Option C stretch runs, the roster adds the rule baseline plus optionally
one cloud cell (`claude-sonnet-4-6` re-anchor per D-PREPRINT-003 from
the retiring Sonnet 4) for a small `runtime_mode` × `model_class`
cross-product. The full D-FRAME-020 roster (six Houdinis + three
Guards including DRG-0) carries forward to future work.

The headline pass rule is an AND across the primary metrics with
zero-tolerance critical violations, applied at the smaller preprint
experiment scale. The cost ceiling for all model API calls is
**USD 300** (D-PREPRINT-005).

## Pilot Protocol Lock

The preprint experiments are gated by a mid-June 2026 pilot-protocol
lock — a single Dom decision point that produces a frozen document
naming:

- the final Option-B model class;
- the task subset (~25-30 tasks from L1, L2, L5, L6, L7);
- per-mechanism success criteria and pre-committed falsification;
- whether the Option C stretch is in or out;
- the hard cost ceiling and a stop-spending rule.

Pilot execution runs in July 2026. The full Engels pilot protocol
(60 APPS + DRG-0 + LLM Guard) carries forward as the de-risk step
for a future Engels paper, not as a gate on this preprint.

## Paper-Killer Preempts

One critique is structurally preempted in the preprint:

1. **Framing overclaim.** The preprint says "trusted-monitor substrate
   for bounded AI-control protocols," not "complete AI-control safety
   case." Adaptive Attacks on Trusted Monitors (arXiv:2510.09462)
   belongs in the introduction and related work. This preempt is more
   load-bearing in the preprint than it was in the merged paper because
   Engels no longer provides the empirical bridge to the AI control
   vocabulary; the connection is defended in prose plus the §1/§2
   citation only.

The Greenblatt DRG-artifacts critique preempt (was D-FRAME-019 clause
2) carries forward to the future Engels paper with DRG-0.

## Scope

In scope for the preprint:

- HAI as one non-clinical personal-wellness reference runtime.
- GovernedAgentBench v1.0 release as the mechanism-isolable benchmark.
- Option B mechanism-ablation experiment on one model class.
- Option C stretch (small model-scale cross-product) only if July
  substrate holds.
- 16-trajectory targeted adversarial layer.
- Appendix: tasks, prompts, seeds, reproducibility, additional results.
- Appendix D future-work recipe for S1 fine-tuning of bounded operators
  (keep / drop is O-PREPRINT-002 at mid-August polish).
- Appendix E coding-agent sketch only (keep / drop is O-PREPRINT-002).

Out of scope for the preprint:

- Engels Backdoor Code extension (deferred to future paper).
- Bounded Hierarchical Summarization empirical contrast (HS remains
  in §2 prose only).
- Full predeclared roster cross-product.
- 18 adaptive-vs-DRG-0 adversarial trajectories.
- Clinical or medical decision-making claims.
- Cross-domain generalization beyond personal wellness as a result.
- A second coding-agent runtime before this paper.
- Fine-tuned local operator results.
- Sandbagged or password-locked executor models.
- Full attack-policy substitution red-team.

## Appendix Commitments

Appendix D, if kept, states the sequel-paper setup: trained operators
reach contract-compliance at smaller scales than untrained operators.
It is future work only and makes no performance claim.

Appendix E, if kept, contains the coding-agent contract sketch from
`framing_v2/round_5/RESPONSE.md` Section Q2. It must include the
anti-overclaim header: this appendix is not evidence that the HAI
results generalize.

Both appendices are subject to a keep / drop call at the mid-August
polish gate (O-PREPRINT-002).
