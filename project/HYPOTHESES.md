# Research Hypotheses

**Status:** Current project-wide hypothesis ledger, aligned to framing
v2 on 2026-05-11.

This file replaces the old root-level HAI product hypothesis ledger.
The pre-reframe HAI bets remain preserved in
`../hai/reporting/plans/post_v0_1_18/strategic_plan_v2.md` and
historical plan docs.

The active paper is **Deterministic Software Contracts as Trusted
Monitors in AI Control Protocols**. Hypotheses below are about
deterministic software contracts as the trusted monitor in an AI control
protocol for bounded agent operation. HAI is the reference
instantiation, not the generalization claim.

## H1. Contract-as-trusted-monitor mechanism hypothesis

**Hypothesis.** Deterministic software contracts can serve as the
trusted monitor in an AI control protocol for bounded agent operation,
with measurable per-mechanism contributions to safety-constrained
operation under a held-constant deployment prompt.

**Why it matters.** This is the minimum architectural claim. The paper
needs evidence that runtime-owned mechanisms, not only prompt wording or
model scale, contribute to safe bounded operation.

**Falsification.** `full_contract` fails to improve safety-constrained
task success over per-mechanism off-paths, or the observed gains cannot
be attributed to M4-M8 under a held-constant prompt.

**Superseded mapping.** The previous H1 ("runtime contracts improve
safety-constrained operation") and previous H2 ("contract components
have separable effects") are folded into this refactored H1. The
comparison remains `runtime_mode`, not prompt access.

## H2. Runtime-as-floor model-scale hypothesis

**Hypothesis.** Under the full contract, the smallest predeclared model
passes all primary thresholds; under `no_runtime_enforcement`, a larger
predeclared model fails at least one. The contract shifts the
model-scale safety curve.

**Why it matters.** This is the strongest model-scale result the paper
can claim: reliability shifts partly from the model into deterministic
software.

**Falsification.** Performance remains primarily a function of model
scale, or no smaller predeclared model under `full_contract` passes the
locked thresholds when compared with larger models under
`no_runtime_enforcement`.

**Superseded mapping.** This refactors the previous H3 ("runtime
contracts can reduce required model scale") into the exact
predeclared-roster form used by the merged paper.

## H3. Deterministic Guard hypothesis

**Hypothesis.** A deterministic Guard at general Elo = 0 occupies a
legitimate point on the Engels scaling-laws-for-oversight curve for the
Backdoor Code game.

**Why it matters.** This extends the runtime-contract claim beyond HAI:
it tests whether deterministic software can be evaluated as a trusted
Guard in an established oversight scaling setup.

**Falsification.** The July 2026 pilot fails the commit rule, DRG-0
does not produce a meaningful domain-Elo signal, or the deterministic
Guard result depends on unfair information unavailable to LLM Guards.

## H4. Fine-tuned local operators need live contract grounding

**Status.** Future work only. Paper 1 sets up the S1 sequel on
fine-tuning bounded operators, but makes no performance claim about
fine-tuned local operators.

**Hypothesis.** Trained operators reach contract-compliance at smaller
scales than untrained operators when evaluated against the same runtime
contract, prompt template, scorer, manifests, runtime modes, and
thresholds.

**Why it matters.** This is the sequel-paper hypothesis: scale
substitution after a runtime floor, not "alignment training makes the
model safe."

**Falsification.** Fine-tuned local operators do not improve
contract-compliance under the same fixed runtime and scoring protocol,
or gains depend on private data or prompt changes rather than the
declared training recipe.

## H5. GovernedAgentBench can stay domain-general while using HAI

**Hypothesis.** A benchmark can use HAI as the first reference runtime
while measuring general properties of contract-governed operation rather
than health-product quality.

**Why it matters.** The paper is about bounded agents and trusted
monitors. If the benchmark collapses into personal-wellness advice
quality, the research contribution weakens.

**Falsification.** Benchmark tasks require private health rows,
clinical judgment, personal coaching quality, or HAI-internal
implementation knowledge rather than public contract obedience.

## H6. Non-clinical boundaries are enforceable runtime behavior

**Hypothesis.** Diagnosis, treatment, prescribing, and autonomous
medical-decision boundaries can be represented and scored as part of
the runtime contract.

**Why it matters.** The health boundary must be more than a disclaimer.
It should shape tasks, refusals, metrics, and error analysis.

**Falsification.** Models can pass benchmark tasks while producing
diagnosis-shaped, treatment-shaped, prescribing-shaped, or autonomous
medical-decision outputs; or the benchmark cannot distinguish compliant
wellness support from clinical claims.

## Out-Of-Scope Hypotheses

This paper does not test or claim:

- a full AI-control safety case for scheming, sandbagged, or
  password-locked frontier models;
- cross-domain generalization beyond the personal-wellness reference
  runtime;
- semantic monitoring beyond the narrow clinical-boundary refusal
  surfaces in M7;
- MCP server contract composition;
- a second coding-agent reference runtime before this paper;
- fine-tuned local operator results in paper 1.

## Review Rule

These hypotheses should be reviewed when:

- GovernedAgentBench MVP results exist;
- first local/cloud baselines exist;
- mechanism ablation results exist;
- the July 2026 Engels pilot closes;
- bounded Hierarchical Summarization contrast results exist;
- the paper frame changes.

Do not use old HAI product hypotheses as project-wide strategy unless a
new maintainer decision explicitly restores that priority.
