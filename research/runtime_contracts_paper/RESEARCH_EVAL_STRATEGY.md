# Research Evaluation Strategy

**Status:** Current project-wide evaluation strategy, 2026-05-07.

This document is distinct from
`reporting/plans/eval_strategy/v1.md`, which is the pre-reframe HAI
runtime correctness strategy. This file defines the evaluation strategy
for the runtime-contract paper and GovernedAgentBench.

## Evaluation Object

The object being evaluated is not "does HAI give good health advice?"

The object is:

> Can a model operate a bounded runtime through an explicit software
> contract while preserving mutation boundaries, schema validity,
> evidence faithfulness, refusal behavior, and auditability?

HAI supplies the first concrete runtime. Personal wellness supplies a
sensitive-data reference domain. The benchmark should be framed so that
other governed runtimes could be plugged in later.

## Primary Question

For a fixed safety threshold, does the runtime contract reduce the model
capability required for reliable bounded operation?

Operational form:

> For a target GovernedAgentBench score, estimate the smallest model
> condition that reaches the score while unsafe-action rate,
> clinical-claim rate, unsupported-narration rate, invalid-schema rate,
> and direct-state-mutation attempts remain below fixed thresholds.

## Systems To Compare

| System | Purpose |
|---|---|
| Rule baseline | Establish which tasks are deterministic routing rather than model judgment. |
| Local prompt-only | Measures what a local model does without the runtime contract. |
| Local + manifest/contract | Measures contract benefit for local models. |
| Cloud prompt-only | Strong unconstrained model baseline. |
| Cloud + manifest/contract | Separates model strength from contract grounding. |
| Fine-tuned local | Tests whether a small operator can learn benchmark behavior. |
| Fine-tuned local + live manifest | Tests whether fine-tuning remains robust under contract drift. |

Cloud versus local is not the sole motivation. The motivation is bounded
operation over sensitive data; local models make privacy, cost, and
user-owned deployment constraints sharper.

## Scaffold Ablations

The full contract should be compared against component removals:

- no manifest;
- stale manifest;
- no `agent_safe`;
- no mutation classes;
- no exit-code semantics;
- no output schemas;
- no proposal gate;
- no audit/evidence references.

These ablations are the engineering explanation for any observed result.
If full-contract performance improves but no component ablation matters,
the claim is under-explained.

## Metrics

Primary metrics:

- safety-constrained task success;
- valid command rate;
- correct command rate;
- hallucinated command rate;
- schema validity;
- unsafe-action rate;
- direct-state-write attempt rate;
- refusal accuracy;
- clinical-boundary violation rate;
- unsupported narration rate;
- exit-code recovery accuracy;
- audit-reference faithfulness;
- contract-drift robustness.

Secondary metrics:

- latency;
- token / compute cost;
- local deployability;
- intervention burden on the human;
- error recovery depth.

## Task Families

GovernedAgentBench should cover at least:

- intent-to-command routing;
- setup and `USER_INPUT` recovery;
- daily-loop orchestration;
- schema-valid proposal generation;
- faithful narration from runtime read surfaces;
- governance preservation and adversarial refusal;
- contract drift adaptation.

The first MVP does not need all six HAI domains. It needs enough task
families to test the contract claim honestly.

## Fine-Tuning Scope

Fine-tuning is in scope, but must not train on private health rows.

Allowed data:

- synthetic tasks;
- public fixture rows;
- generated trajectories from frozen manifests;
- schema-repair examples;
- `USER_INPUT` recovery examples;
- unsafe-request refusal examples;
- drift-aware examples.

Excluded data:

- private wearable rows;
- unredacted personal notes;
- clinical advice corpora;
- diagnosis/treatment/prescribing examples.

Fine-tuning should be evaluated with and without live manifest retrieval.
A memorized operator that fails under contract drift is not sufficient.

## Result Interpretation

Minimum useful result:

- GovernedAgentBench is well-defined and reproducible.
- Full contract improves at least one local model condition over
  prompt-only local operation on safety-constrained task success.
- Ablations identify which components contribute to the improvement.

Strong result:

- A smaller local model plus the contract matches or beats a larger
  prompt-only local model on safety-constrained task success.
- Fine-tuned local plus live manifest beats fine-tuned local without live
  manifest under drift.

Best result:

- The contract shifts the score-versus-model-size curve left under fixed
  safety thresholds.

Null result:

- If the contract does not improve task success or safety, the paper
  should report that and narrow to lessons about runtime-contract
  evaluation, failure modes, and benchmark design.

## Safety Boundary

The evaluation must treat the non-clinical health boundary as part of the
contract:

- no diagnosis;
- no treatment;
- no prescribing;
- no autonomous medical decisions;
- no benchmark fixture requiring private health disclosure.

Clinical-boundary obedience is not a note in limitations. It is a scored
behavior.

## Anti-Patterns

- Evaluating health recommendation quality instead of contract obedience.
- Choosing safety thresholds after seeing results.
- Letting the cloud baseline be artificially weak.
- Training on private health rows.
- Letting fine-tuning memorize a stale CLI.
- Treating HAI product breadth as benchmark validity.
- Using an LLM judge as the primary safety oracle before deterministic
  scoring exists.
