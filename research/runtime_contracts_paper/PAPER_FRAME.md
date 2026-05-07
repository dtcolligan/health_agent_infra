# Runtime Contracts Paper Frame

**Status:** Locked framing note, 2026-05-07.

This file is the stable reference for the research-paper direction. It
supersedes the earlier HACO-Bench / health-agent-first framing.

## Title Package

**Runtime Contracts for Local Agents Over Sensitive User-Owned Data**

**Subtitle:** A Personal-Wellness Reference Runtime, GovernedAgentBench,
and Model-Scale Study

## North Star

Runtime contracts can make smaller local models viable operators for
bounded workflows over sensitive user-owned data by moving authority,
validation, and audit from the model into enforceable software.

## Paper Identity

Research-engineering systems/evals paper. Conservative,
measurement-first. Architecture first, benchmark second, experiments
third.

## Terminology

| Term | Meaning |
|---|---|
| Runtime contract | The architecture/intervention: manifest, typed commands, mutation classes, `agent_safe`, schemas, proposal/commit separation, deterministic validation, policy gates, and audit. |
| HAI | The personal-wellness reference implementation. |
| GovernedAgentBench | The benchmark/eval artifact for contract-governed agent operation. |
| Model-scale study | The empirical result: whether the contract shifts safety-constrained performance across model sizes. |
| Personal wellness | The reference domain. Explicitly non-clinical: no diagnosis, treatment, prescribing, or autonomous medical decisions. |

## Abstract

Agents operating over sensitive user-owned data must do more than
produce plausible responses: they must call valid tools, respect
mutation boundaries, recover from setup failures, avoid unsupported
claims, and leave an auditable record of state changes. Today, much of
this reliability burden is placed on model capability, prompt design, or
post-hoc review.

We study a complementary intervention: shifting reliability from the
model into an enforceable local runtime contract. The contract exposes
a capabilities manifest, typed command schemas, mutation classes,
`agent_safe` boundaries, exit-code semantics, proposal/commit
separation, deterministic validation gates, policy rules, and audit
logs. Under this design, the model proposes and explains; the runtime
owns truth, validation, mutation, and audit.

We instantiate this architecture in HAI, a local personal-wellness
runtime over wearable and user-authored data. HAI is explicitly
non-clinical: it does not diagnose, treat, prescribe, or make
autonomous medical decisions. This boundary is not a disclaimer but
part of the governed runtime contract being evaluated.

We introduce GovernedAgentBench, a benchmark for contract-governed
agent operation over sensitive user-owned data. The benchmark measures
command validity, mutation-boundary obedience, schema-valid proposal
generation, exit-code recovery, refusal accuracy, unsupported
narration, clinical-boundary violations, and robustness to contract
drift. We evaluate local models, cloud models, fine-tuned local
operators, and scaffold ablations that remove individual contract
components.

Our goal is measurement rather than demonstration by assertion: we ask
whether runtime contracts reduce unsafe operation and improve task
success, and whether they shift the model-size threshold required for
reliable bounded agent operation.

## Contributions

1. **Runtime-contract architecture.** A contract-governed architecture
   for bounded agents in which the model proposes and explains while
   local software owns validation, mutation, policy, and audit.
2. **HAI reference implementation.** A local personal-wellness runtime
   implementing this contract over user-owned structured data, with
   explicit non-clinical safety boundaries.
3. **GovernedAgentBench.** A benchmark for evaluating whether models
   can operate a governed runtime through its public contract, rather
   than relying on implicit prompt adherence or private implementation
   knowledge.
4. **Model-scale study.** A comparison of local models, cloud models,
   fine-tuned local operators, manifest-grounded prompting, and
   prompt-only baselines under fixed safety thresholds.
5. **Scaffold ablations.** Experiments isolating the contribution of
   manifest access, mutation classes, `agent_safe` flags, output
   schemas, proposal gates, exit-code semantics, and audit references.
6. **Error taxonomy.** Failure modes for contract-governed agents:
   hallucinated commands, invalid proposals, unsafe mutation attempts,
   unsupported narration, clinical-boundary violations, drift failures,
   and refusal errors.

## Empirical Result Tiers

Minimum publishable result:

- The full runtime contract materially reduces unsafe mutation attempts,
  hallucinated commands, invalid proposal outputs, and unsupported
  narration versus prompt-only operation for at least one local model
  class.
- GovernedAgentBench is well-defined, reusable, and reproducible.
- Scaffold ablations identify which contract components affect safety
  and task success.

Strong result:

- A small local model plus the full runtime contract matches or beats a
  larger local model or cloud prompt-only baseline on safety-constrained
  task success.
- Fine-tuned local plus live manifest is better than fine-tuned local
  alone under contract drift.

Best result:

- The full runtime contract shifts the score-vs-model-size curve left:
  a smaller model reaches the same safety-constrained operating
  threshold as a larger model without the contract.

## Health-Safety Boundary

The paper should strongly foreground the boundary:

- HAI is not clinical software.
- HAI does not diagnose.
- HAI does not treat.
- HAI does not prescribe.
- HAI does not make autonomous medical decisions.
- The reference domain is personal wellness over user-owned wearable
  and user-authored data.

This is part of the runtime contract being evaluated, not a footnote.
