# Superseded — Research Lane

**Status:** Historical provenance for pre-merge planning artifacts.
**Moved:** 2026-05-11.

Files here are **not current planning truth.** They were authored
before the 2026-05-11 framing-v2 merge that locked the paper as
*Deterministic Software Contracts as Trusted Monitors in AI Control
Protocols* (NeurIPS 2027 main conference). Each file's body still
contains useful provenance for past decisions but should not be
treated as the source of truth for any current decision.

For current planning, read:

- `../framing_v2/CONVERGED.md` — locked framing summary + 27 decisions
- `../framing_v2/ORCHESTRATOR_STATE.md` — full decisions table
- `../PAPER_OUTLINE_MERGED.md` — canonical paper outline
- `../PAPER_FRAME.md`, `../CLAIM_LADDER.md`,
  `../RESEARCH_EVAL_STRATEGY.md`, `../PROJECT_EXECUTION_PLAN.md`,
  `../BASELINES_AND_ABLATIONS_PLAN.md`, `../WORK_PACKETS.md`,
  `../HAI_PAPER_READINESS_EXECUTION.md` — active paper-planning files
  (all rewritten in Phase 2 batch 1 to align with the merged framing)

## What's in here

| File | Why superseded |
|---|---|
| `AUTONOMOUS_PROJECT_EXECUTION_PLAN.md` | Workshop-floor autonomous-execution plan; target replaced by D-FRAME-008 (NeurIPS 2027 main). Trajectory A fallback only. |
| `AUTONOMOUS_GATE_HANDOFF.md` | Workshop-floor gate audit; same. |
| `CODEX_WORK_INSPECTION_INDEX.md` | Workshop-floor Codex inspection guide; replaced by `../framing_v2/phase_2_doc_alignment/`. |
| `METHODS_SYSTEM_DRAFT.md` | Workshop-floor methods/system draft; replaced by `../PAPER_OUTLINE_MERGED.md` §4-§5. |
| `IMPLEMENTATION_PLAN.md` | Coarse pre-merge phase plan; replaced by `../PROJECT_EXECUTION_PLAN.md`. |
| `DRAFT_PAPER.md` | Pre-merge paper skeleton; replaced by `../PAPER_OUTLINE_MERGED.md`. |
| `HAI_PAPER_READINESS_PLAN.md` | Pre-merge HAI paper-readiness plan; replaced by `../PROJECT_EXECUTION_PLAN.md` + `../HAI_PAPER_READINESS_EXECUTION.md`. |
| `MECHANISM_INVENTORY.md` | Pre-merge mechanism brief; replaced by D-FRAME-017 in `../framing_v2/CONVERGED.md`. |
| `MODEL_ROSTER_DECISION_BRIEF.md` | Pre-merge roster brief; replaced by D-FRAME-020 + `../../../benchmark/governed_agent_bench/model_roster.md`. |
| `DOC_ALIGNMENT_AUDIT.md` | Pre-merge doc-alignment audit; replaced by `../framing_v2/phase_2_doc_alignment/FINAL_AUDIT_RESPONSE.md`. |
| `CLAUDE_CODE_COMPREHENSIVE_AUDIT_PROMPT.md` | Pre-merge one-off audit prompt; framing-v2 orchestration pattern in AGENTS.md "Patterns the cycles have validated" supersedes it. |
| `codex_runtime_first_reframe_audit_prompt.md` | Pre-merge runtime-first reframe audit prompt (round 1); chain superseded by `../framing_v2/round_*/AUDIT_PROMPT.md`. |
| `codex_runtime_first_reframe_audit_prompt_round_2.md` | Same (round 2). |
| `codex_runtime_first_reframe_audit_response.md` | Pre-merge runtime-first reframe audit response (round 1). Contains the F-CDX-RFR-R1-01..20 closure annotations added in framing-v2 audit-findings-closure batch. |
| `codex_runtime_first_reframe_audit_response_response.md` | Maintainer response to round 1 audit. |
| `codex_runtime_first_reframe_audit_response_round_2.md` | Round 2 audit response. |
| `codex_runtime_first_reframe_audit_response_round_2_response.md` | Maintainer response to round 2 audit. |

## Do not edit

These files are preserved as-is. If a future framing cycle needs
provenance from them, the git history is the audit trail. Do not
rewrite the bodies; the supersession headers (if present) disclaim
the content.

If you find a reference to one of these files in an active doc that
should point to a current artifact, fix the active doc rather than
modifying anything in this directory.
