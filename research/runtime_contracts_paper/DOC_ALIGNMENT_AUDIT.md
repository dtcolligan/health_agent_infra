# Documentation Alignment Audit

**Status:** Internal audit, updated 2026-05-07.

## Problem

The repo had the right new artifacts (`research/` and
`benchmarks/governed_agent_bench/`) but many cold-start docs still
taught a HAI-first product roadmap. A future agent entering without
conversation memory would likely optimize v0.2.x / v1 HAI polish
instead of the paper, benchmark, and model-scale study.

## Target Frame

The repo should communicate this hierarchy consistently:

1. Runtime-contract research question.
2. GovernedAgentBench benchmark artifact.
3. Paper and model-scale / scaffold-ablation experiments.
4. HAI as personal-wellness reference runtime.
5. HAI product polish as subordinate unless paper-critical.

## Audit Findings

| Area | Finding | Fix direction |
|---|---|---|
| Root orientation | `README.md` was partially reframed but still behaved like the HAI product manual after the first screen. | Add `PROJECT_FRAME.md`, rewrite root `README.md` as the research-facing landing page, and move HAI operator material to `reporting/docs/hai_reference_runtime.md`. |
| Agent onboarding | `AGENTS.md` and `CLAUDE.md` still opened with HAI as the whole project and routed readers to old HAI strategy docs. | Update session-start reading order and add a settled research-reframe decision. |
| Repo map | `REPO_MAP.md` did not classify `research/` or `benchmarks/` as first-class active roots. | Add both and demote old HAI release plans to reference-runtime / historical scope. |
| Roadmap | `ROADMAP.md` was a HAI release chain, not the project roadmap under the new objective. | Recast as research-first roadmap with HAI runtime backlog as a support lane. |
| Reporting indexes | `reporting/README.md` and `reporting/docs/README.md` called themselves current v1 docs, which reads as project-wide. | Clarify that `reporting/docs/` is HAI reference-runtime documentation and make `hai_reference_runtime.md` the HAI manual. |
| Current truth | `current_system_state.md` mixed stale v0.1.18 status with v0.2.0 source state and lacked research status. | Add repo-level research status and fix HAI source-truth table. |
| Paper/benchmark | New frame existed but was isolated. | Keep `PAPER_FRAME.md` as locked research frame; link from root and agent docs. |
| Operating memory | Several ideas from the reframe existed only in conversation: documentation-first gate, external research-engineering audience, local/cloud/fine-tune scope, scaffold ablations, and HAI polish subordination. | Add `PROJECT_OPERATING_MODEL.md` and `RESEARCH_EVAL_STRATEGY.md`. |
| Hypotheses | Root `HYPOTHESES.md` still carried HAI product/runtime hypotheses, despite being a top-level active doc. | Rewrite root `HYPOTHESES.md` as current research hypotheses; preserve HAI hypotheses in historical strategy docs. |
| Pre-reframe planning docs | `strategic_plan_v2.md`, `success_framework_v1.md`, `eval_strategy/v1.md`, and `risks_and_open_questions.md` could be mistaken for current project-wide strategy. | Add explicit research-reframe notes and mark them as HAI support-lane/provenance docs. |
| Market context | Vendor-coach context shifted on 2026-05-07 with Google Health Coach and Bevel's AI layer. | Update competitive landscape with dated primary-source links, without making HAI a consumer-product bet. |

## Non-Fixes

Historical cycle artifacts under `reporting/plans/v0_*`,
`reporting/artifacts/archive/`, and `reporting/docs/archive/` should not
be rewritten. They are provenance. Alignment should happen in indexes
and current control docs, not by editing historical records into a
story they did not originally tell.

## Success Criteria

After this audit, a fresh agent should know:

- The repo's objective is the runtime-contract paper + GovernedAgentBench.
- The current work gate is internal documentation alignment before new
  implementation.
- HAI remains active, but as the reference runtime.
- Personal wellness is the demonstrator domain, not the paper's topic.
- The health boundary is non-clinical and experimental, not a disclaimer.
- HAI v1 polish is not the default priority unless it supports the paper
  or benchmark.
