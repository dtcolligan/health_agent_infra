# Documentation Alignment Audit

**Status:** Internal audit, updated 2026-05-08.

## Problem

The repo had the right new artifacts (`research/` and
`benchmark/governed_agent_bench/`) but many cold-start docs still
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

| Area | Finding | Current state |
|---|---|---|
| Root orientation | `README.md` was partially reframed but still behaved like the HAI product manual after the first screen. | Fixed: root `README.md` is research-facing; HAI operator material lives in `hai/docs/hai_reference_runtime.md`. |
| Agent onboarding | `AGENTS.md` and `CLAUDE.md` still opened with HAI as the whole project and routed readers to old HAI strategy docs. | Fixed: cold-start reading order begins with project frame, decision log, operating model, paper frame, eval strategy, and benchmark scope. |
| Repo map | `project/REPO_MAP.md` did not classify `research/` or `benchmark/` as first-class active roots. | Fixed: `project/`, `research/`, `benchmark/`, and `hai/` are the owner lanes; root is tooling/metadata only. |
| Roadmap | `project/ROADMAP.md` was a HAI release chain, not the project roadmap under the new objective. | Fixed: roadmap is research-first, with HAI runtime support lane. |
| Reporting indexes | `hai/reporting/README.md` and HAI docs called themselves current v1 docs, which read as project-wide. | Fixed: active HAI docs moved to `hai/docs/`; `hai/reporting/docs/` is legacy archive / launch drafts only. |
| Current truth | `current_system_state.md` mixed stale v0.1.18 status with v0.2.0 source state and lacked research status. | Fixed: `hai/docs/current_system_state.md` names the runtime-contract reframe, source version, research priority, and next cycles. |
| Paper/benchmark | New frame existed but was isolated. | Fixed: `PAPER_FRAME.md`, `RESEARCH_EVAL_STRATEGY.md`, `IMPLEMENTATION_PLAN.md`, and benchmark docs are linked from root and agent docs. |
| Operating memory | Several ideas from the reframe existed only in conversation: documentation-first gate, external research-engineering audience, local/cloud/fine-tune scope, scaffold ablations, and HAI polish subordination. | Fixed: `project/OPERATING_MODEL.md`, `RESEARCH_EVAL_STRATEGY.md`, and `project/DECISIONS.md` capture the internal memory. |
| Hypotheses | The project-wide hypothesis ledger still carried HAI product/runtime hypotheses. | Fixed: `project/HYPOTHESES.md` now describes runtime-contract research hypotheses. Historical HAI hypotheses remain in planning provenance. |
| Pre-reframe planning docs | `strategic_plan_v2.md`, `success_framework_v1.md`, `eval_strategy/v1.md`, and `risks_and_open_questions.md` could be mistaken for current project-wide strategy. | Fixed via indexes and headers: these are HAI support-lane/provenance docs, not current project-wide strategy. |
| Market context | Vendor-coach context shifted on 2026-05-07 with Google Health Coach and Bevel's AI layer. | Fixed in `hai/docs/competitive_landscape.md`, without turning HAI back into a consumer-product bet. |
| Project decisions | The new frame's choices were spread across multiple files and conversation memory. | Fixed: `project/DECISIONS.md` records post-reframe decisions and is wired into cold-start docs. |

## Current Alignment State

As of 2026-05-08, the repo's current documentation architecture is:

- `project/` for project memory, governance, and project-level alignment
  tests;
- `research/runtime_contracts_paper/` for the paper and evaluation
  strategy;
- `benchmark/` for GovernedAgentBench and benchmark-specific verification;
- `hai/` for HAI source, docs, verification/evals, assets, release proof,
  historical planning, archives, and frozen prototypes;
- root for tool-discovered entrypoints and repository metadata only.

The highest-risk drift class is no longer "root README says the wrong
thing." It is subtler: a future agent could treat historical HAI planning
docs as active priority, or could add HAI polish before benchmark tasks
because the polish feels concrete. The guardrails for that risk are
`project/FRAME.md`, `project/DECISIONS.md`,
`project/OPERATING_MODEL.md`, `project/ROADMAP.md`, and `project/REPO_MAP.md`.

## Non-Fixes

Historical cycle artifacts under `hai/reporting/plans/v0_*`,
`hai/reporting/artifacts/archive/`, and `hai/reporting/docs/archive/` should not
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
