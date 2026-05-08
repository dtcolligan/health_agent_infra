# Runtime Contracts Paper - Implementation Plan

**Status:** Coarse research phase plan, reframed 2026-05-07. See
`PAPER_FRAME.md` for the locked framing note and
`PROJECT_EXECUTION_PLAN.md` for the operational master plan.

The dates below are planning estimates, not authoritative gates. The
milestone exits in `PROJECT_EXECUTION_PLAN.md` control sequencing. If
calendar pressure forces scope cuts, drop optional 7B runs first, then
fine-tuning, then ablation depth, then model count. Preserve the
GovernedAgentBench measurement-readiness, scorer, paper floor, and
non-clinical safety boundary.

## Working Thesis

Runtime contracts may reduce the model scale required for safe bounded
agent operation over sensitive user-owned data.

Measured version:

> For a target GovernedAgentBench score X, estimate the smallest local
> model that reaches X while unsafe-action rate, clinical-claim rate,
> unsupported-narration rate, and direct-state-mutation attempts remain
> below fixed thresholds.

## Target Artifact Set

1. `hai`: governed local personal-wellness reference runtime.
2. GovernedAgentBench: benchmark, fixtures, scorer, and baseline report.
3. `hai-operator`: local small-model adapter or model recipe.
4. Paper: empirical study of whether the runtime contract reduces model scale.

## Phase 1 - Literature and Framing

**Timing:** May 13-24.

Deliverables:

- Related-work matrix covering PHIA, Google PHA, PH-LLM, Health-LLM, API-Bank, ToolLLM, Gorilla, BFCL, tau-bench, MCP-AgentBench, AgentSpec, OpenMedCalc, MedAgentBench, AgentClinic, FActScore, MedHallu, and JSONSchemaBench.
- One-page paper thesis.
- Draft contribution list.
- Risk register for novelty, baselines, privacy, and personal-wellness safety claims.

Decision gate:

- Confirm that the paper is about model-scale reduction from runtime
  contracts, not about building a general health coach.

## Phase 2 - Engineer HAI For Paper Use

**Timing:** May 25-June 10.

Deliverables:

- Stable `hai capabilities --json` ABI for research runs.
- Contract docs aligned with the paper: manifest, command schemas, mutation classes, `agent_safe`, exit codes, output schemas, proposal/commit separation, validation, and audit.
- Public synthetic demo fixtures.
- Explicit hosted-agent privacy caveat.
- Explicit non-goals around diagnosis, treatment, and autonomous clinical decisions.

Acceptance criteria:

- A model or human can read the manifest and operate HAI without implicit repo knowledge.
- No benchmark task requires private health rows.

## Phase 3 - Build GovernedAgentBench

**Timing:** June 11-July 1.

Task levels:

- L1: intent-to-command routing
- L2: setup and `USER_INPUT` recovery
- L3: daily-loop orchestration
- L4: schema-valid proposal generation
- L5: faithful narration from `hai today` and `hai explain`
- L6: governance preservation and adversarial refusal
- L7: contract drift adaptation

Deliverables:

- Benchmark schema.
- Synthetic user tasks.
- Adversarial tasks.
- Golden command trajectories.
- Drift variants across manifest versions.
- Scoring scripts.
- Initial benchmark card.

Metrics:

- task success
- valid command rate
- correct command rate
- hallucinated command rate
- schema validity
- refusal accuracy
- unsafe-action rate
- direct-state-write attempt rate
- clinical-claim rate
- unsupported narration rate
- exit-code recovery accuracy
- drift robustness

## Phase 4 - Baselines

**Timing:** July 2-18.

Systems:

- rule-based router
- rule-based refusal classifier
- local prompt-only model
- local plus live manifest
- cloud prompt-only model
- cloud plus live manifest
- cloud plus manifest plus runtime validation

Deliverables:

- Baseline report.
- Error taxonomy.
- First model-scale curve.
- Strawman check: cloud prompt-only must not be the only cloud comparison.

Decision gate:

- If rule-based baselines solve too much, narrow the paper toward which parts require learning versus deterministic routing.
- If cloud plus manifest dominates all local systems, keep the paper focused on safety/privacy/cost tradeoffs rather than claiming parity.

## Phase 5 - Fine-Tune Local Operator

**Timing:** July 19-August 10.

Targets:

- 1B-1.5B proof model.
- 3B main model.
- 7B optional stretch.

Training data:

- generated from manifests
- generated from synthetic tasks
- fixture-based command trajectories
- error-recovery examples
- unsafe-request refusal examples
- drift-aware examples

Exclusions:

- no private health rows
- no unredacted wearable data
- no clinical advice corpus

Deliverables:

- LoRA/QLoRA training configs.
- Dataset generator.
- Evaluation harness.
- Model card.
- Reproducible run logs.

## Phase 6 - Scaffold Ablations

**Timing:** August 11-31.

Ablations:

- full runtime contract
- no manifest
- stale manifest
- no `agent_safe`
- no mutation classes
- no exit-code semantics
- no output schemas
- no proposal gate
- no audit/evidence references

Main analysis:

- Does the full contract shift the score-vs-parameter curve left?
- Which contract fields account for the largest safety improvement?
- Does fine-tuning help without harming drift robustness?
- Does fine-tuning require live manifest retrieval to remain valid?

Deliverables:

- Ablation report.
- Safety report.
- Faithfulness report.
- Drift robustness report.

## Phase 7 - Write and Release

**Timing:** September.

Deliverables:

- Full paper draft.
- Reproducibility appendix.
- Benchmark card.
- Model card.
- Public fixtures.
- Demo script.
- arXiv-ready repository structure.

Venue strategy:

- First goal: strong Imperial-supervised preprint and public artifact.
- Then target a health-AI or ML systems/agent workshop depending on results.
- A main-track submission is realistic only if GovernedAgentBench is
  reusable, baselines are fair, scaffold ablations are strong, and the
  model-scale reduction result is clear.

## Scientific Success Criteria

Minimum publishable result:

- GovernedAgentBench is well-defined and reusable.
- The HAI reference runtime contract is documented and enforceable.
- Scaffold ablations show which contract components affect safety and task success.
- At least one local model condition improves materially over prompt-only local operation.

Strong result:

- 3B local plus full runtime contract beats cloud prompt-only on safety.
- 3B local plus full runtime contract competes with cloud plus manifest on bounded task success.
- Fine-tuned local plus live manifest is better than fine-tuned local alone under drift.

Best result:

- The full runtime contract reduces the minimum model size needed to
  reach GovernedAgent-X while satisfying strict safety thresholds.

## Failure Modes to Watch

- Benchmark too coupled to HAI implementation details.
- Fine-tuned model memorizes stale CLI commands.
- Synthetic tasks are too template-like.
- Cloud baseline is unfairly weak.
- Safety thresholds are chosen after seeing results.
- Health claims drift toward diagnosis or treatment.
- Privacy claim overstates hosted-agent conditions.

## Immediate Next Steps

0. Finish the documentation-alignment gate in
   `project/OPERATING_MODEL.md` so the repo can recover the new objective
   without conversation memory.
1. Convert the paper skeleton into a live outline with citation keys.
2. Create a related-work reading tracker.
3. Define GovernedAgentBench task JSON schema.
4. Decide GovernedAgent-X thresholds before model experiments.
5. Build a small pilot benchmark for L1, L2, L5, L6, and L7 before any fine-tuning.
