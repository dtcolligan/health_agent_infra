# Phase Plan

**Status:** Active, opened 2026-05-11.

This file defines the two-phase structure and acceptance criteria. The
orchestrator follows this plan; deviations require explicit user
sign-off.

## Phase 1 — Research convergence

**Goal:** lock every open framing decision in the merged paper plan.

**Worker:** Codex, invoked via `/goal` (long-running research mode).
The user drives the Codex terminal manually.

**Auditor:** Claude Code agent dispatched via the `Agent` tool with
`subagent_type=general-purpose`. The audit agent reads the worker's
output, verifies primary sources, checks for overreach, returns
verdict + findings.

**Round structure:**

1. **Orchestrator selects 3-5 high-yield questions** from the open
   decisions list in `CONTEXT_DOSSIER.md` §5. Cluster by topic, not
   by priority alone — questions that share literature should share a
   round.
2. **Orchestrator writes `round_N/PROMPT.md`** for Codex. Self-
   contained: includes briefing, questions, deliverable format, exact
   output location.
3. **User pastes prompt into Codex `/goal`.** Codex researches at
   length. User saves output to `round_N/RESPONSE.md`.
4. **Orchestrator writes `round_N/AUDIT_PROMPT.md`** for the audit
   agent. Specific instructions: verify these citations, check for
   these failure modes, return verdict.
5. **Orchestrator dispatches audit via `Agent` tool.** Audit agent
   writes `round_N/AUDIT_RESPONSE.md`.
6. **Orchestrator writes `round_N/SYNTHESIS.md`.** Integrates response
   + audit. Lists: what closed (with provenance), what's still open,
   what newly opened.
7. **Orchestrator updates `ORCHESTRATOR_STATE.md`** to reflect new
   state.
8. **Stop check.** Run the Phase 1 stop test (see below).

### Phase 1 stop test (run after each round's SYNTHESIS)

Three signals must all fire to declare convergence:

1. **Decisions list signal.** The "Open decisions" list in
   `ORCHESTRATOR_STATE.md` has zero entries marked
   `priority: high` or `priority: medium`.
2. **Yield signal.** The next round's draft `PROMPT.md` (you write
   one and inspect it) would have fewer than 3 substantive questions
   to ask. "Substantive" = could change a §-level decision in the
   paper.
3. **Adversarial-review signal.** A simulated hostile reviewer of the
   current locked framing would have no paper-killer critique that
   isn't already in the limitations section.

If all three fire: write `CONVERGED.md` with the date, the round
count, and a one-page summary of the locked framing. Move to Phase 2.

If two of three fire: run one more round targeting the missing
signal.

If fewer than two fire: continue normally.

### Phase 1 escape valve

If a round's audit verdict is `ABORT_ROUND` (the round's premise was
wrong), the orchestrator must:

1. Roll back any changes to `ORCHESTRATOR_STATE.md` from that round.
2. Surface the reason to the user.
3. Reframe the round's prompt OR open a different question.

If three consecutive rounds return `SHIP_WITH_NOTES` with no new
substantive findings, declare Phase 1 done by yield exhaustion even
if signal 1 hasn't fully fired.

## Phase 2 — Documentation alignment

**Goal:** every file in the repo touched by paper framing reflects
the locked plan from Phase 1.

**Worker:** Codex with `/goal`. Same invocation pattern.

**Auditor:** Claude Code agent. **Audit cadence: only at the end of
Phase 2**, not per batch. Mechanical edits are lower error than
research; per-batch audit is friction without proportional yield.

**Batch structure** (file groups, executed in dependency order):

### Batch 1 — Paper planning files

Files (~8):
- `research/runtime_contracts_paper/PAPER_FRAME.md` (rewrite)
- `research/runtime_contracts_paper/CLAIM_LADDER.md` (rewrite)
- `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md` (rewrite)
- `research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md` (rewrite)
- `research/runtime_contracts_paper/BASELINES_AND_ABLATIONS_PLAN.md` (rewrite)
- `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md` (revise to merged scope)
- `research/runtime_contracts_paper/DRAFT_PAPER.md` (formally supersede with PAPER_OUTLINE_MERGED.md OR rewrite)
- `research/runtime_contracts_paper/WORK_PACKETS.md` (revise WP list)

**Acceptance:** every cross-reference between these files agrees on
title, contributions, threat model, claim tiers, calendar, scope.

### Batch 2 — Benchmark spec files

Files (~6):
- `benchmark/governed_agent_bench/README.md`
- `benchmark/governed_agent_bench/BENCHMARK_SPEC.md`
- `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`
- `benchmark/governed_agent_bench/SCORING_SPEC.md`
- `benchmark/governed_agent_bench/schema/trajectory.schema.json` (F-CDX-RFR-R1-07 model_identity fields, F-CDX-RFR-R1-04 runtime_mode rename)
- `benchmark/governed_agent_bench/schema/score.schema.json` (F-CDX-RFR-R1-06 required thresholds + scorer_config_hash)

**Acceptance:** schemas validate against locked methodology;
operator harness names match Phase 1 mechanism inventory; runtime_mode
enum reflects locked ablation set.

### Batch 3 — Project cold-start files

Files (~6):
- `project/FRAME.md`
- `project/DECISIONS.md` (append new D-PROJ-018+ records)
- `project/OPERATING_MODEL.md`
- `project/HYPOTHESES.md` (refactor H1 around contract-as-trusted-monitor)
- `project/ROADMAP.md`
- `project/REPO_MAP.md` (only if active/historical reclassification needed)

**Acceptance:** cold-start docs tell the merged-paper story; no
references to A2 framing or B1 threat model survive.

### Batch 4 — HAI runtime docs (light touch)

Files (~5):
- `hai/docs/hai_reference_runtime.md`
- `hai/docs/runtime_contract_overview.md`
- `hai/docs/current_system_state.md`
- `hai/docs/architecture.md`
- `hai/docs/non_goals.md`

**Acceptance:** only references to paper framing updated; HAI runtime
architecture content NOT touched (HAI is frozen as product).

### Batch 5 — Operating contracts

Files (3):
- `AGENTS.md`
- `CLAUDE.md`
- `README.md` (top-level)

**Acceptance:** terminology matches Phase 1 (control protocol +
safety spec vocabulary); decision records updated; cycle-pattern
signposts updated if Phase 2 changes the cycle vocabulary.

### Batch 6 — Historical provenance (mark superseded)

Files (4):
- `hai/reporting/plans/post_v0_1_18/strategic_plan_v2.md`
- `hai/reporting/plans/success_framework_v1.md`
- `hai/reporting/plans/eval_strategy/v1.md`
- `hai/reporting/plans/risks_and_open_questions.md`

**Action:** add header noting "superseded by merged-paper framing
v2; preserved as historical provenance." Do not rewrite. Do not
delete.

### Audit-findings-closure batch

Close all 11 findings in
`research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response.md`
explicitly. Each finding gets a closure annotation: "Closed by
framing_v2 doc alignment, batch N, file X." This is a mechanical
sweep across all 11 findings.

### Final repo-wide audit

After all 6 batches plus audit-findings-closure complete:

1. Orchestrator writes a `phase_2_doc_alignment/FINAL_AUDIT_PROMPT.md`
   instructing the audit agent to: read every file in batches 1-5,
   check for internal consistency, terminology drift, version-tag
   drift, broken cross-references, and stale references to A2/B1
   framing.
2. Dispatch audit via `Agent` tool.
3. If verdict is `SHIP` or `SHIP_WITH_NOTES`: close Phase 2.
4. If verdict is `REVISE`: spawn a targeted fix batch for the
   findings.

### Phase 2 done

When the final audit verdict is `SHIP` or `SHIP_WITH_NOTES`:

1. Write `phase_2_doc_alignment/COMPLETE.md` with date, batches, and
   any residual `SHIP_WITH_NOTES` annotations.
2. Update `ORCHESTRATOR_STATE.md` to reflect both phases complete.
3. Surface to Dom: orchestration done; next step is the Engels pilot
   (July 2026) and beyond.

## Cross-phase invariants

- **Never edit files outside `framing_v2/`** during Phase 1 (except
  audit-response files if explicitly closing a finding).
- **Never run Codex directly**; always write `PROMPT.md` and hand off
  to Dom.
- **Always update `ORCHESTRATOR_STATE.md`** after every round and
  every batch. State drift is the failure mode.
- **Always cite provenance** when locking a decision: link to the
  round number and synthesis file.

## Calendar binding

- Phase 1 target completion: end of June 2026 (4-6 rounds estimated;
  open-ended depth via `/goal` may compress this).
- Phase 2 target completion: mid-July 2026 (before Engels pilot
  window).
- Engels pilot: late July 2026 (de-risks merge commit).
- Pilot decision gate: August 2026.
- NeurIPS 2027 submission: May 2027.

The orchestrator should flag if any phase is slipping against these
markers.
