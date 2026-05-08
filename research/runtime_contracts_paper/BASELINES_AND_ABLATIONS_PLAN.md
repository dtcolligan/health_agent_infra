# Baselines And Ablations Plan

**Status:** Experiment planning document, 2026-05-08.

This file defines the systems to compare once GovernedAgentBench has a
working offline scorer. It is not a run log and does not authorize model
experiments before the benchmark vertical slice is complete.

## Experimental Principle

All systems must produce the same trajectory format and be scored by the
same deterministic scorer. The comparison is invalid if each system uses
a different evaluator, task wording, hidden context, or safety threshold.

## Required Conditions

| Condition | Description | Purpose |
|---|---|---|
| Rule baseline | Deterministic router/refusal/command selector for simple tasks. | Establish what does not require model judgment. |
| Local prompt-only | Local model sees task text but no manifest/contract context. | Measures unguided local behavior. |
| Local + contract | Local model sees task plus manifest/contract context. | Measures runtime-contract benefit for local models. |
| Cloud prompt-only | Cloud model sees task text but no manifest/contract context. | Strong model baseline without contract grounding. |
| Cloud + contract | Cloud model sees task plus manifest/contract context. | Separates model strength from contract grounding. |
| Fine-tuned local | Local model trained on synthetic/public trajectories, no live manifest. | Tests learned operator behavior. |
| Fine-tuned local + contract | Fine-tuned local model with manifest/contract context. | Tests whether fine-tuning still needs live contract grounding. |

## Scaffold Ablations

The full-contract condition should be compared against:

| Ablation | Removed signal | Expected failure class |
|---|---|---|
| no manifest | command list, args, safety metadata | hallucinated/invalid commands |
| stale manifest | current contract replaced by older or mutated snapshot | drift failures |
| no `agent_safe` | command safety flags | unsafe mutation attempts |
| no mutation classes | read/proposal/commit/destructive classification | boundary confusion |
| no exit-code semantics | recovery guidance | poor `USER_INPUT` / error recovery |
| no output schemas | proposal/output shape constraints | schema-invalid actions |
| no proposal gate | proposal/commit separation | user-owned state violations |
| no audit references | explain/read provenance | unsupported narration |

Each ablation must change exactly one context feature where possible. If
the ablation requires changing more than one feature, document that it is
a compound ablation.

## Model Scope

Initial workshop-sized scope:

- one small local model;
- one larger local model if compute allows;
- one cloud model;
- rule baseline;
- full contract plus two to four ablations.

Stretch scope:

- three local sizes;
- two cloud models;
- fine-tuned local operator;
- full ablation suite.

The project should not block the workshop floor on the stretch scope.

## Thresholds

Thresholds must be chosen before model-result interpretation. Suggested
initial thresholds are placeholders until the scorer is implemented:

| Metric | Minimum expectation |
|---|---|
| unsafe-action rate | 0 for pass-critical tasks |
| clinical-boundary violation rate | 0 for all tasks |
| direct-state-write attempt rate | 0 for all tasks |
| schema validity | high enough to avoid repair-only success |
| task success | reported with confidence intervals or clear counts |

## Reporting

Every experiment report should include:

- task set version;
- manifest snapshot;
- model ids and decoding settings;
- prompt/context condition;
- number of tasks and trajectories;
- scorer version;
- raw metric table;
- violation taxonomy counts;
- representative failures;
- limitations.

## Stop Conditions

Stop and re-plan if:

- task wording leaks the expected command too directly;
- rule baseline solves nearly everything;
- prompt-only cloud fails because the prompt is under-specified rather
  than because it lacks the contract;
- local model failures are dominated by output-format parsing rather
  than contract reasoning;
- ablation results are uninterpretable because multiple components were
  removed at once.
