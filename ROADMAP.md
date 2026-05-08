# Roadmap

**Status:** Research-first roadmap, reframed 2026-05-07.

The project roadmap now has two lanes:

1. **Research lane** - paper, GovernedAgentBench, model baselines,
   fine-tuning, and scaffold ablations.
2. **Reference-runtime lane** - HAI maintenance and contract work
   needed to make the research lane credible.

When the lanes compete, default to the research lane unless the HAI
task is on the paper / benchmark critical path. The canonical project
frame is [`PROJECT_FRAME.md`](PROJECT_FRAME.md); the locked paper frame
is [`research/runtime_contracts_paper/PAPER_FRAME.md`](research/runtime_contracts_paper/PAPER_FRAME.md).

## Now

- **Planning Gate 1.** Current focus. Documentation alignment is now
  sufficient to recover the new objective; before implementation resumes,
  the project needs end-to-end research-program specs and bounded work
  packets so coding agents can execute slices without making strategic
  decisions. Gate docs:
  [`PROJECT_OPERATING_MODEL.md`](PROJECT_OPERATING_MODEL.md) and
  [`research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md`](research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md).
- **Freeze the HAI operator contract for research.** Stabilize the
  public manifest, command schemas, mutation classes, exit-code
  semantics, proposal/commit separation, validation gates, privacy caveat,
  and non-clinical boundary that benchmark tasks will consume.
- **GovernedAgentBench MVP.** Build the offline benchmark skeleton into a
  runnable artifact: frozen manifest snapshot, 10+ pilot tasks across
  L1/L2/L5/L6/L7, recorded trajectories, and a scorer that needs no
  network access or private health rows.
- **Paper scaffold.** Convert the draft skeleton into a live paper outline
  with related-work matrix, contribution list, experimental definitions,
  and pre-registered safety thresholds.

## Next

- **Benchmark pilot report.** Publish a small GovernedAgentBench pilot
  covering rule baselines and hand-recorded agent trajectories before
  adding model backends.
- **Model baselines.** Run local prompt-only, local+manifest,
  cloud prompt-only, cloud+manifest, and rule-based baselines under the
  same scorer.
- **Fine-tuned local operator.** Generate synthetic/public training data
  from manifests, tasks, trajectories, error recovery, and refusal cases;
  train a small LoRA/QLoRA adapter without private health rows.
- **Scaffold ablations.** Measure full contract versus no manifest,
  stale manifest, no `agent_safe`, no mutation classes, no exit-code
  semantics, no output schemas, no proposal gate, and no audit/evidence
  references.
- **Paper draft and release package.** Produce the preprint, benchmark
  card, model card, reproducibility appendix, public fixtures, and demo
  script.

## HAI Runtime Support Lane

These HAI tasks remain valuable but are subordinate to the research lane
unless explicitly needed for benchmark validity or paper experiments:

| HAI item | Research relevance | Default disposition |
|---|---|---|
| v0.2.1 insight ledger (W53) | Useful if the paper evaluates longer-horizon review faithfulness; not required for the minimum benchmark MVP. | Defer unless chosen as a benchmark task family. |
| v0.2.2 LLM judge shadow (W58J) | Potential secondary evaluation axis; the paper should not depend on an LLM judge for primary safety claims. | Optional after deterministic scorer exists. |
| v0.2.3 capabilities-manifest schema freeze | Valuable for reproducibility and drift tests. | Keep if it stabilizes GovernedAgentBench manifests. |
| MCP read surface | Interesting runtime portability artifact. | Defer unless it becomes the benchmark plug-in API. |
| Additional health domains / sources | Mostly product polish for the paper's minimum empirical claim. | Defer before submission unless a specific ablation requires them. |

## Explicitly Out Of Scope Before Submission

- Hosted multi-user product work.
- Web/mobile/dashboard frontend.
- Meal-level nutrition, food taxonomy, or micronutrient inference.
- New wearable-source breadth unless needed for synthetic benchmark tasks.
- Clinical claims, diagnosis, treatment, prescribing, or autonomous medical
  decisions.
- Hidden learning loop or automatic threshold mutation from outcomes.

## Research Milestones

| Milestone | Exit criterion |
|---|---|
| Frame locked | `PROJECT_FRAME.md`, `PROJECT_DECISIONS.md`, `PAPER_FRAME.md`, and cold-start docs agree. |
| Planning Gate 1 | Master plan, benchmark specs, contract-freeze plan, baseline/ablation plan, and work packets exist. |
| Contract freeze | A model or human can operate HAI from the manifest and docs without private repo knowledge. |
| Benchmark MVP | Schemas, pilot tasks, frozen manifests, trajectories, and scorer run offline. |
| Baselines | Rule, local, cloud, and manifest-grounded systems scored under one harness. |
| Fine-tuning | Public/synthetic training data + reproducible local-operator recipe. |
| Ablations | Contract-component removals measured against fixed safety thresholds. |
| Paper release | Draft + benchmark card + reproducibility appendix + public fixtures. |

## Historical Roadmaps

HAI release history remains under [`reporting/plans/`](reporting/plans/).
The old release-by-release tactical plan is still useful for provenance and
HAI runtime backlog, but it is no longer the project-wide priority order.
