# Roadmap

**Status:** Research-first roadmap, aligned to framing v2 on
2026-05-11.

The project roadmap has two lanes:

1. **Research lane** - merged NeurIPS 2027 paper,
   GovernedAgentBench, model baselines, mechanism ablations, Engels,
   bounded Hierarchical Summarization contrast, and paper release.
2. **Reference-runtime lane** - HAI maintenance and contract work
   needed to make the research lane credible.

When the lanes compete, default to the research lane unless the HAI task
is on the paper or benchmark critical path. The canonical framing source
is
[`../research/runtime_contracts_paper/framing_v2/CONVERGED.md`](../research/runtime_contracts_paper/framing_v2/CONVERGED.md).

## Now (2026-05)

- **Phase 2 documentation alignment.** Current focus. Phase 1 framing
  is closed; batches 1-2 are closed; batches 3-6 remain in progress,
  followed by the audit-findings-closure batch and final repo-wide
  audit.
- **Planning Gate 1.** The old planning-gate label now maps to Phase 2
  closure: cold-start docs and work packets must agree on the locked
  merged-paper frame before new implementation becomes the default.
- **Cold-start consistency.** Project docs, benchmark specs, HAI docs,
  and operating contracts must tell the merged-paper story:
  deterministic software contracts as trusted monitors in AI control
  protocols.
- **Benchmark and runtime support.** Keep GovernedAgentBench and HAI
  aligned to the locked `runtime_mode` intervention, M4-M8/M9-TX
  mechanism inventory, predeclared thresholds, and no-private-health-row
  fixture rule.

## Next (2026-06)

- **Phase 2 closure.** Finish batches 3-6, close
  F-CDX-RFR-R1-01..11 against the merged framing, and run the final
  repo-wide audit.
- **Sonnet 4 retirement binding.** Claude Sonnet 4 retires on
  2026-06-15. Any Section 7.5 claim cell using Sonnet 4 must complete
  before that date or re-anchor to `claude-sonnet-4-6` under a new
  roster hash.
- **Pre-pilot readiness.** Prepare the Engels pilot manifest,
  deterministic DRG-0 modules, frozen configuration hashes, and smoke
  sample workflow.

## Then (2026-07 to 2026-08)

- **Engels pilot.** Run the July 2026 pilot: 60 APPS competition
  samples, 10 smoke samples separate, three Houdinis, DRG-0, Haiku LLM
  Guard, and the six-clause commit/revert rule.
- **Pilot decision gate.** By August 2026, either keep the merged-paper
  trajectory or revert to separate workshop/conference trajectories if
  the pilot fails the locked rule.

## Out (Post-August 2026)

| Window | Work |
|---|---|
| 2026-11 | Mechanism ablations complete. |
| 2027-02 | Full Engels Backdoor Code run. |
| 2027-03 | Targeted adversarial red-team layer complete. |
| 2027-03 | Bounded Hierarchical Summarization contrast complete or demoted to related-work prose under its cap rule. |
| 2027-04 | Manuscript v1. |
| 2027-05 | NeurIPS 2027 main-conference submission. |

## HAI Runtime Support Lane

These HAI tasks remain valuable only when they directly support the
paper, benchmark, or reproducibility:

| HAI item | Research relevance | Default disposition |
|---|---|---|
| HAI v0.2.0 reference snapshot | The pinned reference runtime for paper and benchmark work. | Maintain only through paper-critical runtime-fix packets. |
| HAI v0.2.1+ product cycles | Product-lane work after D-PROJ-016. | Out of scope unless a specific paper-critical bug fix requires a narrow patch. |
| MCP read surface | Interesting runtime portability artifact. | Defer unless it becomes the benchmark plug-in API. |
| Additional health domains / sources | Mostly product polish for the paper's minimum empirical claim. | Defer before submission unless a specific ablation requires them. |

## Explicitly Out Of Scope Before Submission

- HAI v0.2.1+ product work unless paper-critical.
- Cross-domain reference runtimes beyond the Appendix E sketch.
- Hosted-product deployment.
- Web/mobile/dashboard frontend.
- Meal-level nutrition, food taxonomy, or micronutrient inference.
- New wearable-source breadth unless needed for synthetic benchmark tasks.
- Clinical claims, diagnosis, treatment, prescribing, or autonomous
  medical decisions.
- Hidden learning loop or automatic threshold mutation from outcomes.
- Full control safety case for scheming, sandbagged, or
  password-locked frontier models.

## Research Milestones

| Milestone | Exit criterion |
|---|---|
| Framing v2 locked | `CONVERGED.md` and `ORCHESTRATOR_STATE.md` close D-FRAME-001..027. |
| Phase 2 doc alignment | Batches 1-6, audit-findings closure, and final repo-wide audit complete. |
| GovernedAgentBench measurement-readiness | Known-good and known-bad trajectories score as expected across schemas, pilot tasks, frozen manifests, and offline scorer. |
| HAI paper-readiness | A model or human can operate the benchmark subset of HAI from fixtures, manifest, and docs without private repo knowledge. |
| Baselines | Predeclared roster scored under `runtime_mode` × `model_class` with the deployment prompt held constant. |
| Ablations | M4-M8 off-paths measured against fixed safety thresholds with M9-TX held constant. |
| Engels | Pilot gate passes, then full Backdoor Code run lands under predeclared information boundaries. |
| Paper release | Draft + benchmark card + reproducibility appendix + public fixtures. |

## Historical Roadmaps

HAI release history remains under
[`../hai/reporting/plans/`](../hai/reporting/plans/). The old
release-by-release tactical plan is still useful for provenance and HAI
runtime backlog, but it is no longer the project-wide priority order.
