# Research Hypotheses

**Status:** Current project-wide hypothesis ledger, 2026-05-07.

This file replaces the old root-level HAI product hypothesis ledger.
The pre-reframe HAI bets remain preserved in
`reporting/plans/post_v0_1_18/strategic_plan_v2.md` and historical plan
docs. The active project now tests runtime contracts for local agents over
sensitive user-owned data.

## H1. Runtime contracts improve safety-constrained operation

**Hypothesis.** A model operating through a runtime contract will make
fewer unsafe mutation attempts, hallucinated command calls,
schema-invalid proposals, unsupported narrations, and clinical-boundary
violations than the same model operating prompt-only.

**Why it matters.** This is the minimum empirical reason for the project.
If the contract does not improve bounded operation, the architecture may
still be useful engineering, but the paper claim narrows sharply.

**Falsification.** Prompt-only baselines match or beat full-contract
baselines on safety-constrained task success across the MVP benchmark,
without increased unsafe-action or unsupported-narration rates.

## H2. Contract components have separable effects

**Hypothesis.** Scaffold ablations will show that individual contract
components contribute measurable safety or task-success gains.

Candidate components:

- manifest access;
- `agent_safe`;
- mutation classes;
- exit-code semantics;
- output schemas;
- proposal/commit gates;
- audit/evidence references;
- drift-aware manifest retrieval.

**Why it matters.** A useful research-engineering result should explain
which parts of the contract matter, not only that the full system works.

**Falsification.** The full contract improves scores, but ablations cannot
identify any component-level contribution or the improvement comes only
from benchmark-specific prompt wording.

## H3. Runtime contracts can reduce required model scale

**Hypothesis.** For bounded operation over sensitive user-owned data, a
smaller local model plus the runtime contract can reach a safety-constrained
operating threshold that requires a larger model without the contract.

**Why it matters.** This is the paper's strongest possible result:
reliability shifts out of the model and into local software.

**Falsification.** Performance remains primarily a function of model scale,
with the contract adding little or no safety-constrained advantage for
smaller models.

## H4. Fine-tuned local operators need live contract grounding

**Hypothesis.** Fine-tuning can improve local operator behavior, but a
fine-tuned model without live manifest/contract grounding will be brittle
under contract drift.

**Why it matters.** This separates learned operational habits from
current-authority awareness. A memorized CLI operator is not enough for a
governed runtime.

**Falsification.** Fine-tuned local models retain high performance under
manifest drift without live contract retrieval, or live manifest retrieval
does not improve drift robustness.

## H5. GovernedAgentBench can stay domain-general while using HAI

**Hypothesis.** A benchmark can use HAI as the first reference runtime
while measuring general properties of contract-governed operation rather
than health-product quality.

**Why it matters.** The paper should be about bounded agents over
sensitive data. If the benchmark collapses into personal-wellness advice
quality, the research contribution weakens.

**Falsification.** Benchmark tasks require private health rows, clinical
judgment, personal coaching quality, or HAI-internal implementation
knowledge rather than public contract obedience.

## H6. Non-clinical boundaries are enforceable runtime behavior

**Hypothesis.** Diagnosis, treatment, prescribing, and autonomous medical
decision boundaries can be represented and scored as part of the runtime
contract.

**Why it matters.** The health boundary must be more than a disclaimer.
It should shape tasks, refusals, metrics, and error analysis.

**Falsification.** Models can pass benchmark tasks while producing
diagnosis-shaped, treatment-shaped, prescribing-shaped, or autonomous
medical-decision outputs; or the benchmark cannot distinguish compliant
wellness support from clinical claims.

## Review Rule

These hypotheses should be reviewed when:

- GovernedAgentBench MVP results exist;
- first local/cloud baselines exist;
- scaffold ablation results exist;
- fine-tuning results exist;
- the paper frame changes.

Do not use old HAI product hypotheses as project-wide strategy unless a
new maintainer decision explicitly restores that priority.
