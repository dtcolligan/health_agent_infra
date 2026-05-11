# Runtime Contracts Paper - Implementation Plan

> **Superseded as current planning:** This file was authored 2026-05-09
> as a coarse research-phase plan targeting a workshop-floor paper.
> The active framing as of 2026-05-11 is
> `research/runtime_contracts_paper/framing_v2/CONVERGED.md` —
> "Deterministic Software Contracts as Trusted Monitors in AI Control
> Protocols" (NeurIPS 2027 main conference). The active execution
> calendar is `PROJECT_EXECUTION_PLAN.md` (rewritten in Phase 2 batch
> 1). Body is preserved as **historical provenance only**.

---

**Status:** Coarse research phase plan, reframed 2026-05-09 (round-2
note appended). See `PAPER_FRAME.md` for the locked framing note,
`HAI_PAPER_READINESS_EXECUTION.md` for the round-2 master execution
plan, and `PROJECT_EXECUTION_PLAN.md` for the milestone-level plan.

**Round-2 reframe note (2026-05-09).** Phase 4 below lists prompt-
only baselines as comparison conditions. Those are dropped. The
benchmark compares `runtime_mode` values with the deployment-
realistic prompt held constant. See `HAI_PAPER_READINESS_EXECUTION.md`
and `../../project/DECISIONS.md` D-PROJ-013..017.

The dates below are planning estimates, not authoritative gates. The
milestone exits in `PROJECT_EXECUTION_PLAN.md` control sequencing. If
calendar pressure forces scope cuts, drop optional 7B runs first, then
fine-tuning, then ablation depth, then model count. Preserve the
GovernedAgentBench measurement-readiness, scorer, paper floor, and
non-clinical safety boundary.

## Working Thesis

Deterministic software contracts can serve as the trusted monitor in an
AI control protocol for bounded agent operation, reducing the model
scale required for safety-constrained operation under a held-constant
deployment prompt.

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

## Phase 4 - Baselines (round-2: prompt held constant)

**Timing:** July 2-18.

Systems (`model_class` × `runtime_mode`, with the prompt template
held at `deployment_full_v1`):

- `rule_baseline` × `full_contract`
- `local` × `full_contract`
- `local` × `no_runtime_enforcement`
- `cloud` × `full_contract`
- `cloud` × `no_runtime_enforcement`

The model entries come from `model_roster.md` (per
`WP-MODEL-ROSTER-001`), which is committed before any model run.
There are no "prompt-only" or "with vs without manifest" conditions
(per D-PROJ-014; see `CLAIM_LADDER.md` forbidden phrasings).

Deliverables:

- Baseline report.
- Error taxonomy.
- First model-scale curve under `full_contract` vs
  `no_runtime_enforcement`.

Decision gate:

- If rule-baselines solve too much, narrow the paper toward which
  task families require learning versus deterministic routing.
- If `cloud × full_contract` dominates all local systems, keep the
  paper focused on safety/privacy/cost tradeoffs rather than
  claiming parity.

## Phase 5 - Fine-Tune Local Operator (Future-A appendix)

**Timing:** July 19-August 10. **Out of workshop floor** per
`CLAIM_LADDER.md` Future-A.

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
- Fine-tuned-local entries appended to `model_roster.md` Future-A
  appendix section before any fine-tuned trajectory.

## Phase 6 - Scaffold Ablations (round-2: per-mechanism off-paths)

**Timing:** August 11-31.

Off-paths along the canonical `runtime_mode` axis (the prompt is
held constant in every condition):

- `full_contract` (all on)
- `no_validation` (M4 off)
- `no_agent_safe` (M5 off)
- `no_proposal_gate` (M6 off)
- `no_refusal` (M7 off)
- `no_audit_chain` (M8 off; transactions remain on)
- `no_runtime_enforcement` (M4..M8 all off; M1..M3 + M9-TX on)

L7 drift tasks vary stale-manifest content as task content, not as
a runtime-mode axis. There are no "no manifest", "stale manifest",
"no exit-code semantics", or "no output schemas" conditions in
round-2.

Main analysis:

- Does `full_contract` shift the score-vs-parameter curve left
  versus `no_runtime_enforcement`?
- Which per-mechanism off-path accounts for the largest safety
  delta?
- (Future-A only) Does fine-tuning augment but not replace the
  runtime under L7 drift?

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
- At least one ablatable mechanism (M4..M8) shows a non-zero effect under one `model_class` on the MVP task set, with the deployment-realistic prompt held constant (per `CLAIM_LADDER.md` T1).

Strong result:

- Smallest predeclared-roster local model under `full_contract`
  passes thresholds that a larger predeclared-roster model fails
  under `no_runtime_enforcement` (`CLAIM_LADDER.md` T3).
- (Future-A appendix only) Fine-tuned-local under `full_contract`
  matches or exceeds the same model under `no_runtime_enforcement`
  on L7 drift robustness.

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
