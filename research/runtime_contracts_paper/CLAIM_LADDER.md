# Claim Ladder

**Status:** Paper-claim control document, 2026-05-08.

This file defines what the project is allowed to claim at different
evidence levels. It prevents the paper from drifting into product
marketing or overclaiming before results exist.

## Core Research Question

Can enforceable runtime contracts reduce the model capability required
for safe bounded operation over sensitive user-owned data?

Operational form:

> For a fixed GovernedAgentBench safety threshold, does adding the
> runtime contract improve task success, reduce unsafe behavior, or shift
> the model-size threshold compared with prompt-only operation?

## What Counts As Evidence

Evidence must come from:

- frozen benchmark tasks;
- recorded trajectories;
- deterministic scorer outputs;
- predeclared metrics and thresholds;
- comparable baselines;
- scaffold ablations;
- reproducible run logs.

Evidence must not come primarily from:

- subjective demos;
- maintainer anecdotes;
- isolated Claude Code dogfood;
- private health rows;
- post-hoc threshold selection;
- unscored qualitative impressions.

## Claim Tiers

### Tier 0 — Infrastructure Result

**Claim.** GovernedAgentBench defines a reusable evaluation surface for
contract-governed agents over sensitive user-owned structured data.

**Evidence required.**

- Benchmark tasks, schemas, frozen manifest, trajectories, and scorer run
  offline.
- At least L1, L2, L5, L6, and L7 task families are represented.
- The scorer identifies command validity, unsafe mutation attempts,
  refusal errors, unsupported narration, and clinical-boundary failures.

**Allowed language.**

- "We introduce a benchmark and reference runtime."
- "The benchmark makes contract-obedience failures observable."

**Forbidden language.**

- "Runtime contracts reduce required model scale."
- "Local models are viable operators."

### Tier 1 — Safety Improvement Result

**Claim.** The full runtime contract improves safety-constrained task
success for at least one model condition compared with prompt-only
operation.

**Evidence required.**

- At least one local model is evaluated prompt-only and with the full
  contract.
- Metrics show improvement on safety-constrained task success or a
  meaningful reduction in unsafe-action, hallucinated-command,
  invalid-schema, unsupported-narration, or clinical-boundary failures.
- The improvement is measured under predeclared thresholds.

**Allowed language.**

- "Runtime contracts improved safety-constrained operation in our
  reference setting."
- "The contract reduced specific failure modes."

**Forbidden language.**

- "The contract is generally sufficient for safe agents."
- "Small local models replace frontier models."

### Tier 2 — Component Explanation Result

**Claim.** Specific contract components account for measurable changes
in safety or task success.

**Evidence required.**

- Scaffold ablations remove individual components such as manifest,
  `agent_safe`, mutation classes, schemas, proposal gate, exit-code
  semantics, or audit references.
- At least one component removal changes a primary metric in the
  expected direction.

**Allowed language.**

- "Ablations suggest that [component] contributes to [metric]."
- "The gain is not merely prompt formatting; removing [component]
  degraded behavior."

**Forbidden language.**

- "Every contract component is necessary."
- "The architecture is fully explained by the ablation set."

### Tier 3 — Model-Scale Shift Result

**Claim.** The runtime contract shifts the score-versus-model-size curve
left under fixed safety thresholds.

**Evidence required.**

- Multiple model sizes are evaluated under comparable conditions.
- A smaller model with the contract matches or beats a larger prompt-only
  model on safety-constrained task success.
- Cost/latency/local-deployability are reported, not cherry-picked.

**Allowed language.**

- "In this benchmark, the contract reduced the model-size threshold for
  reliable bounded operation."

**Forbidden language.**

- "Runtime contracts make small models generally equivalent to large
  models."

### Tier 4 — Fine-Tuned Local Operator Result

**Claim.** Fine-tuned local operators benefit from live/frozen contract
grounding and fail under drift when they rely on memorized interfaces.

**Evidence required.**

- Fine-tuned local is evaluated with and without manifest access.
- Drift tasks are included.
- Training data provenance excludes private health rows and clinical
  advice corpora.

**Allowed language.**

- "Fine-tuning helped only when paired with contract grounding."
- "Manifest access improved drift robustness."

**Forbidden language.**

- "Fine-tuning solves agent governance."

## Null Results

A null result is publishable if the benchmark is real and the analysis is
honest.

Allowed null-result framing:

- Runtime contracts did not improve task success under this benchmark.
- The contract reduced some unsafe failures but increased recovery burden.
- Rule baselines solved more than expected, narrowing where model
  judgment matters.
- The benchmark reveals that interface standardization is not enough.

Forbidden null-result framing:

- Hiding weak results behind product demos.
- Reinterpreting the project as a consumer health product.
- Claiming model-scale reduction without model-scale evidence.

## Minimum Workshop Floor

The minimum acceptable workshop/preprint package is:

- Tier 0 infrastructure result;
- at least partial Tier 1 safety result;
- at least one scaffold ablation;
- a clear limitations section explaining what the benchmark does not
  prove.
