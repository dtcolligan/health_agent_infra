# Batch 1 Edits Summary

## Files touched

| File | Edit type | Lines changed (rough) | Notes |
|---|---|---:|---|
| `PAPER_FRAME.md` | rewrite | ~340 diff lines | Replaced runtime-first/workshop frame with merged NeurIPS 2027 paper frame, title, lineage, threat model, results, mechanisms, Engels pilot, and scope. |
| `CLAIM_LADDER.md` | rewrite | ~339 diff lines | Rebuilt claim ladder around mechanism effects, runtime-as-floor, Engels DRG-0 result, targeted-adversarial characterization, thresholds, HS contrast, and future-work tiers. |
| `RESEARCH_EVAL_STRATEGY.md` | rewrite | ~330 diff lines | Replaced pre-merge eval plan with roster, thresholds, attack policy, Engels, HS, cost ceiling, task-family, and safety-boundary plan. |
| `PROJECT_EXECUTION_PLAN.md` | rewrite | ~421 diff lines | Replaced old milestone structure with merged-paper calendar from convergence, including Sonnet 4 retirement and pilot/full-run gates. |
| `BASELINES_AND_ABLATIONS_PLAN.md` | rewrite | ~186 diff lines | Aligned Section 7.1-7.4 ablation matrix to M4-M8, M9-TX held constant, D-FRAME-020 roster, and D-FRAME-021 thresholds. |
| `HAI_PAPER_READINESS_EXECUTION.md` | revise | ~90 added/changed lines | Revised pre-merge runtime-first plan into HAI support-lane plan; added merged-scope responsibilities, schema tightening, adversarial support, exact manifest reference, and superseded workshop-first items. |
| `DRAFT_PAPER.md` | supersede header | ~24 added lines | Added top supersession notice pointing to `PAPER_OUTLINE_MERGED.md` and `framing_v2/CONVERGED.md`; left historical body intact. |
| `WORK_PACKETS.md` | revise WP list | ~365 diff lines | Added Phase 2 batch 2-6, audit-closure, final-audit, DRG-0, Engels pilot, and bounded-HS packets; updated roster packet and superseded stale ablation placeholder. |

## Cross-file invariant check

- Title (D-FRAME-016): present in `PAPER_FRAME.md`, `CLAIM_LADDER.md`,
  `RESEARCH_EVAL_STRATEGY.md`, `PROJECT_EXECUTION_PLAN.md`,
  `BASELINES_AND_ABLATIONS_PLAN.md`, `HAI_PAPER_READINESS_EXECUTION.md`,
  `DRAFT_PAPER.md`, and `WORK_PACKETS.md`; all use
  "Deterministic Software Contracts as Trusted Monitors in AI Control
  Protocols."
- Target venue (D-FRAME-008): present in `PAPER_FRAME.md`,
  `PROJECT_EXECUTION_PLAN.md`, `HAI_PAPER_READINESS_EXECUTION.md`, and
  `WORK_PACKETS.md`; all say NeurIPS 2027 main / May 2027.
- Headline framing (D-FRAME-001): present in the five rewritten planning
  files and reflected in the HAI/WP updates; all use deterministic
  software contract as trusted monitor for bounded agent operation.
- Triple lineage anchor (D-FRAME-002): explicit in `PAPER_FRAME.md` and
  reflected in `RESEARCH_EVAL_STRATEGY.md` prior-art anchors.
- Threat model (D-FRAME-003): explicit in `PAPER_FRAME.md`,
  `RESEARCH_EVAL_STRATEGY.md`, `CLAIM_LADDER.md`, and
  `PROJECT_EXECUTION_PLAN.md`; consistent as capability-failure plus
  targeted adversarial layer.
- Three headline results: explicit in `PAPER_FRAME.md`,
  `CLAIM_LADDER.md`, `PROJECT_EXECUTION_PLAN.md`, and
  `BASELINES_AND_ABLATIONS_PLAN.md`.
- Mechanism inventory (D-FRAME-017): aligned across `PAPER_FRAME.md`,
  `CLAIM_LADDER.md`, `RESEARCH_EVAL_STRATEGY.md`,
  `BASELINES_AND_ABLATIONS_PLAN.md`, `HAI_PAPER_READINESS_EXECUTION.md`,
  and `WORK_PACKETS.md`; M8 is audit evidence emission and M9-TX is
  held constant.
- Engels pilot (D-FRAME-018): explicit in `PAPER_FRAME.md`,
  `RESEARCH_EVAL_STRATEGY.md`, `PROJECT_EXECUTION_PLAN.md`, and
  `WORK_PACKETS.md`, including 60 APPS samples, 3 Houdinis, DRG-0 +
  Haiku Guard, about USD 18.60, commit/revert rules, and five-attempt
  verification caveat.
- Paper-killer critiques (D-FRAME-019): explicit in `PAPER_FRAME.md`
  and represented in `PROJECT_EXECUTION_PLAN.md` / `WORK_PACKETS.md`
  through adversarial and DRG artifact mitigations.
- Model roster (D-FRAME-020): aligned in `PAPER_FRAME.md`,
  `RESEARCH_EVAL_STRATEGY.md`, `BASELINES_AND_ABLATIONS_PLAN.md`, and
  `WORK_PACKETS.md`, including Haiku retirement and Sonnet 4 2026-06-15
  binding.
- Thresholds (D-FRAME-021): aligned in `CLAIM_LADDER.md`,
  `RESEARCH_EVAL_STRATEGY.md`, `BASELINES_AND_ABLATIONS_PLAN.md`, and
  `HAI_PAPER_READINESS_EXECUTION.md`.
- Attack policy (D-FRAME-022): aligned in `PAPER_FRAME.md`,
  `CLAIM_LADDER.md`, `RESEARCH_EVAL_STRATEGY.md`,
  `PROJECT_EXECUTION_PLAN.md`, `HAI_PAPER_READINESS_EXECUTION.md`, and
  `WORK_PACKETS.md`.
- Cost ceiling (D-FRAME-023): present in `PAPER_FRAME.md`,
  `RESEARCH_EVAL_STRATEGY.md`, `PROJECT_EXECUTION_PLAN.md`, and
  `HAI_PAPER_READINESS_EXECUTION.md`; all use USD 1,500.
- Bounded HS contrast (D-FRAME-024): present in `PAPER_FRAME.md`,
  `CLAIM_LADDER.md`, `RESEARCH_EVAL_STRATEGY.md`,
  `PROJECT_EXECUTION_PLAN.md`, and `WORK_PACKETS.md`; all keep L6 scope,
  2-week + USD 200 caps, and demotion fallback.
- Coding-agent slice (D-FRAME-025): present in `PAPER_FRAME.md`,
  `CLAIM_LADDER.md`, `PROJECT_EXECUTION_PLAN.md`, and
  `HAI_PAPER_READINESS_EXECUTION.md`; appendix sketch only, no evidence
  claim.
- ST-WebAgentBench differentiation (D-FRAME-026): explicit in
  `PAPER_FRAME.md`, `CLAIM_LADDER.md`, and
  `BASELINES_AND_ABLATIONS_PLAN.md`.
- Paper 2 / S1 fine-tuning (D-FRAME-027): explicit in
  `CLAIM_LADDER.md`, `RESEARCH_EVAL_STRATEGY.md`,
  `PROJECT_EXECUTION_PLAN.md`, and `HAI_PAPER_READINESS_EXECUTION.md`.

## Carry-over for batch 2 / later batches

- `PAPER_OUTLINE_MERGED.md` is out of batch-1 scope but still has the
  pre-final working title and older calendar wording in places. Batch 1
  did not edit it because the prompt forbids editing outside the 8
  target files.
- `IMPLEMENTATION_PLAN.md`, `HAI_PAPER_READINESS_PLAN.md`,
  `MECHANISM_INVENTORY.md`, `PRIOR_ART_POSITIONING.md`, and related
  non-target paper docs may still contain pre-merge or runtime-first
  wording. They should be handled by later orchestrator batches.
- `DRAFT_PAPER.md` was marked superseded. Its historical body still
  contains stale workshop/user-owned-data prose by design.
- `WORK_PACKETS.md` intentionally preserves historical stale terms only
  inside superseded packet provenance.

## Constitutional Classifiers / SHADE-Arena / etc citations

- Constitutional Classifiers (arXiv:2501.18837): added as the
  Pareto-reporting precedent in `PAPER_FRAME.md`, `CLAIM_LADDER.md`,
  `RESEARCH_EVAL_STRATEGY.md`, and `WORK_PACKETS.md`.
- SHADE-Arena: added to adversarial/prior-art anchors in
  `CLAIM_LADDER.md` and `RESEARCH_EVAL_STRATEGY.md`.
- Adaptive Attacks on Trusted Monitors (arXiv:2510.09462): added as the
  framing-overclaim/monitor-attack preempt in `PAPER_FRAME.md` and the
  adversarial prior-art list in `RESEARCH_EVAL_STRATEGY.md`.
- ST-WebAgentBench (arXiv:2410.06703): added as the closest benchmark
  contrast in `PAPER_FRAME.md`, `CLAIM_LADDER.md`,
  `BASELINES_AND_ABLATIONS_PLAN.md`, and `RESEARCH_EVAL_STRATEGY.md`.
- Deliberative Alignment: `RESEARCH_EVAL_STRATEGY.md` uses the audited
  gloss about latency cost and forcing the model to infer the spec from
  labeled examples.

## Open issues

- None requiring a new framing decision in batch 1.
