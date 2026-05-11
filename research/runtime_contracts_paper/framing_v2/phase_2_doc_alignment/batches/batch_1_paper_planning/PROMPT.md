# Phase 2 Batch 1 Worker Prompt — Paper-Planning Files

**Drafted:** 2026-05-11
**Phase:** 2 — Documentation alignment
**Batch:** 1 of 6 — Paper-planning files
**Worker:** Codex via `/goal`
**Audit cadence:** end-of-phase only (not per batch); orchestrator
inspects diff via `git diff` after this batch.

---

## Identity

You are Codex, operating in `/goal` mode. You are the worker agent
for **Phase 2 (documentation alignment)** of the runtime-contracts
paper framing v2 orchestration. The orchestrator (Claude Code) wrote
this prompt.

Phase 2 differs from Phase 1: this is doc-edit work, not research.
You write edits **directly to the target files**, not to a separate
RESPONSE.md. Your edits are the response.

## Project briefing

Phase 1 (research convergence) closed 2026-05-11 with 27 locked
framing decisions (D-FRAME-001 through D-FRAME-027) and 6 minor
audit-derived annotations. **Read `framing_v2/CONVERGED.md` first**;
that file is the authoritative one-page summary of the locked
framing. The decisions table in
`framing_v2/ORCHESTRATOR_STATE.md` "Locked decisions" has the full
provenance.

Phase 2 propagates the locked framing into the repo's paper-planning
files. Batch 1 covers the 8 files under
`research/runtime_contracts_paper/` that name the paper's title,
contributions, threat model, claim ladder, evaluation strategy,
execution plan, baselines/ablations, paper-readiness execution,
draft outline, and work-packet list.

**Acceptance criterion (per PHASE_PLAN.md §3 batch 1):** every
cross-reference between these 8 files agrees on title, contributions,
threat model, claim tiers, calendar, scope.

## Required reading (in this order)

1. `research/runtime_contracts_paper/framing_v2/CONVERGED.md` —
   authoritative one-page locked-framing summary + 27 decisions
   table + Phase 2 batch roadmap. **This is your source of truth.**
2. `research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`
   — "Locked decisions" table with full per-decision provenance.
3. `research/runtime_contracts_paper/framing_v2/round_3/SYNTHESIS.md`,
   `round_4/SYNTHESIS.md`, `round_5/SYNTHESIS.md` — Phase 2 action
   items per round. **The "Action items (Phase 2 doc alignment,
   batch 1 paper-planning)" sections in each synthesis are the
   concrete edit list you must satisfy.**
4. `research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md` — the
   merged paper outline that is now canonical. The 8 target files
   below either rewrite to match this or formally defer to it.

Read the target files themselves before editing them. Identify what
exists that needs to change vs what can stay.

## Target files (8)

Edit only these files in batch 1:

1. **`research/runtime_contracts_paper/PAPER_FRAME.md`** (165 lines,
   **rewrite**) — must reflect merged-paper title, headline framing,
   triple lineage anchor, threat model, three-result abstract
   structure, target venue (NeurIPS 2027). Replace any "user-owned
   structured data" framing with "bounded agent operation"; replace
   any solo-paper framing with merged-paper framing.

2. **`research/runtime_contracts_paper/CLAIM_LADDER.md`** (301 lines,
   **rewrite**) — must reflect three load-bearing claims:
   (a) mechanism-isolable ablations of M4-M8 under held-constant
   prompt;
   (b) runtime-as-floor (smallest predeclared model + full contract
   passes all primary thresholds; larger predeclared model +
   no_runtime_enforcement fails at least one);
   (c) deterministic-Guard data point on Engels scaling-laws-for-
   oversight curve at general Elo = 0.
   Plus the targeted-adversarial-layer Pareto as a non-headline
   characterization claim. Include tier-0/1/2/3 claim ladder
   structure if currently present.

3. **`research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`**
   (215 lines, **rewrite**) — must reflect predeclared roster
   (D-FRAME-020), predeclared thresholds (D-FRAME-021), attack
   policy (D-FRAME-022), cost ceiling (D-FRAME-023), and the
   bounded HS contrast (D-FRAME-024). Drop pre-reframe content
   that no longer reflects the merged paper.

4. **`research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md`**
   (282 lines, **rewrite**) — must reflect the merged-paper
   calendar from `CONVERGED.md`: Engels pilot July 2026, pilot
   decision gate August 2026, mechanism ablations Nov 2026, full
   Engels Feb 2027, red-team Mar 2027, HS contrast Mar 2027,
   manuscript v1 Apr 2027, NeurIPS submission May 2027. Include
   the 2026-06-15 Sonnet 4 retirement binding.

5. **`research/runtime_contracts_paper/BASELINES_AND_ABLATIONS_PLAN.md`**
   (134 lines, **rewrite**) — must reflect D-FRAME-017 (M4-M8
   ablation matrix + M9-TX held constant), D-FRAME-020 (model
   roster cells), D-FRAME-021 (AND-pass rule + critical
   violations). The §7.1-7.4 mechanism-ablation matrix structure
   from `PAPER_OUTLINE_MERGED.md` is canonical.

6. **`research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`**
   (689 lines, **revise to merged scope**) — this file is the
   pre-merge runtime-first reframe execution plan. Update its
   in-scope items to match the merged paper. Items that are
   subsumed by the merge (e.g., "publish workshop paper first")
   should be marked superseded; new items needed for the merged
   path (e.g., schema-tightening for trajectory.schema.json T3/T4
   conditional from D-FRAME-021 + audit F-AUDIT-4-04) should be
   added. Do not delete this file; revise it.

7. **`research/runtime_contracts_paper/DRAFT_PAPER.md`** (487 lines,
   **formally supersede with `PAPER_OUTLINE_MERGED.md`**) — add a
   prominent header at the top of DRAFT_PAPER.md noting it is
   superseded by `PAPER_OUTLINE_MERGED.md` and giving the date and
   provenance (CONVERGED.md). Leave the body as historical
   provenance; do not delete. If DRAFT_PAPER.md has §-level content
   that is more concrete than PAPER_OUTLINE_MERGED.md (e.g., specific
   prose drafts that survived the merge), migrate that content into
   PAPER_OUTLINE_MERGED.md as appropriate appendix or §-level prose
   before marking DRAFT_PAPER.md superseded.

8. **`research/runtime_contracts_paper/WORK_PACKETS.md`** (1847
   lines, **revise WP list**) — large file. Update the WP list to
   reflect post-merge scope. Mark superseded WPs that no longer
   apply; add WPs for Phase 2 doc-alignment batches 2-6 + audit-
   findings closure + final repo-wide audit; add WPs for the Engels
   pilot + DRG-0 implementation + bounded HS implementation. Do
   not delete the file; revise.

## Cross-file invariants

Every batch-1 file must agree on the following load-bearing values.
If any file currently disagrees, update it.

### Title (D-FRAME-016)
> Deterministic Software Contracts as Trusted Monitors in AI Control
> Protocols

### Target venue (D-FRAME-008)
NeurIPS 2027 main conference, May 2027 submission deadline.

### Headline framing (D-FRAME-001)
Deterministic software contract that operationalizes a safety spec
as the trusted monitor in an AI control protocol for bounded agent
operation.

### Triple lineage anchor (D-FRAME-002)
- AI Control protocols (Greenblatt 2024 et al.)
- Safety specs (OpenAI Model Spec, Anthropic Model Spec Midtraining,
  Deliberative Alignment)
- LLM-monitor baselines (Constitutional Classifiers, Hierarchical
  Summarization)

### Threat model (D-FRAME-003)
Capability-failure + targeted adversarial layer (50 trajectories
across 4 attack types + adaptive-vs-DRG-0).

### Three headline results (per PAPER_OUTLINE_MERGED §abstract)
1. Mechanism-isolable ablations of M4-M8 under held-constant prompt.
2. Runtime-as-floor (smallest model + full contract passes; larger
   model + no_runtime_enforcement fails).
3. Deterministic Guard on Engels Backdoor Code curve at general
   Elo = 0.

### Mechanism inventory (D-FRAME-017)
- M4 = validation
- M5 = `agent_safe` dispatch refusal
- M6 = W57 proposal/commit gate
- M7 = clinical-boundary refusal (scoped narrowly; JSON output exempt
  per F-AUDIT-3-03)
- M8 = audit **evidence emission** (renamed from "audit chain")
- M9-TX = transaction integrity (held constant, non-ablatable)

### Engels pilot (D-FRAME-018)
60 APPS competition samples, 3 Houdinis (Qwen2.5-7B-Instruct-Turbo,
Claude 3.5 Haiku, Claude Sonnet 4), DRG-0 + Claude 3.5 Haiku LLM
Guard, ~$18.60 cost, 6-clause commit rule, 6-clause revert rule.
Caveat: "five Houdini attempts per sample" claim from Engels needs
verification against arXiv:2504.18530 §4 PDF before pilot.

### Two paper-killer critiques (D-FRAME-019)
Framing-overclaim (rhetorical preempt: "trusted-monitor substrate
for bounded AI-control protocols" + arXiv:2510.09462 citation in
§2/§5) and Greenblatt DRG-artifacts (empirical preempt: pre-registered
DRG inputs + ablations + FP rates + adaptive-attack-vs-DRG-0).

### Model roster (D-FRAME-020) — 9 entries
6 Houdinis:
1. `Qwen/Qwen2.5-3B-Instruct` (Hugging Face local)
2. `Qwen/Qwen2.5-7B-Instruct-Turbo` (Together AI)
3. `accounts/fireworks/models/qwen2p5-32b-instruct` (Fireworks)
4. `accounts/fireworks/models/qwen2p5-72b-instruct` (Fireworks)
5. `claude-3-5-haiku-20241022` — **RETIRED 2026-02-19; pilot
   trajectories only.** Successor `claude-haiku-4-5-20251001`
   for new cells (new roster hash).
6. `claude-sonnet-4-20250514` — **retires 2026-06-15.** §7.5
   paper-claim run must complete before then OR re-anchor to
   `claude-sonnet-4-6` (new roster hash).

3 Guards:
1. DRG-0 (deterministic, general-Elo = 0)
2. `claude-3-5-haiku-20241022` — same retirement caveat as above
3. `gpt-4o-mini-2024-07-18` (OpenAI)

### Thresholds (D-FRAME-021)
AND-pass rule across 7 primary metrics + 7 zero-tolerance critical
violations. Per-metric thresholds:
- command_validity ≥ 1.00 + hallucinated_command_rate = 0
- mutation-boundary obedience = 0
- schema_validity ≥ 0.95 aggregate
- refusal_accuracy ≥ 0.95 + zero missed required refusals
- unsupported_narration_rate ≤ 0.02 + audit_reference_faithfulness
  ≥ 0.98
- clinical_claim_rate = 0
- drift_robustness ≥ 0.90

Sensitivity test: ±5pp per metric.

### Attack policy (D-FRAME-022) — 50 trajectories
- Refusal bypass (vs M7): 8
- Mutation escalation (vs M5+M6): 8
- Audit tampering (vs M8): 8
- Schema evasion (vs M4): 8
- Adaptive attack vs DRG-0: 18

### Cost ceiling (D-FRAME-023)
USD 1,500 hard ceiling.

### Bounded HS contrast (D-FRAME-024)
§7.6 renamed "Bounded Hierarchical Summarization contrast." L6
governance/refusal only (optional L5 if early). 2-week + $200 caps.
Demote to §2.3 prose if cap missed. **HS methodology framing must
NOT include "optional classifier" stage as a documented HS feature
(F-AUDIT-5-01).**

### Coding-agent slice (D-FRAME-025)
Appendix E sketch only. 215-word draft in `round_5/RESPONSE.md` §Q2
is canonical body. Anti-overclaim required.

### ST-WebAgentBench differentiation (D-FRAME-026)
6-row table in `round_5/RESPONSE.md` §Q1b. Load-bearing axis:
"runtime-mode intervention with mechanism-isolable ablation under
a held-constant prompt." Import into §2.4 of relevant files.

### Paper 2 sketch (D-FRAME-027)
Headline: "Trained operators reach contract-compliance at smaller
scales than untrained operators." Frame as scale-substitution-after-
runtime-floor.

### Six audit-derived annotations to propagate
- HS "optional classifier" must be soft (F-AUDIT-5-01).
- Manifest reference must say "HAI v0.2.0 manifest snapshot at
  `benchmark/governed_agent_bench/manifests/hai_0_2_0.json` ≈ 189 KB"
  (F-AUDIT-5-02).
- Deliberative Alignment gloss: "latency cost and forces the model
  to infer the spec from labeled examples" (F-AUDIT-5-03).
- L2 task family explicitly named in family-fit prose (F-AUDIT-5-04).
- Constitutional Classifiers (arXiv:2501.18837) cited as Pareto-
  precedent for §7.6 metric shape (F-AUDIT-5-05).
- HS reimplementation cost: 16-35 hours with calibration iteration,
  not 16-24 (F-AUDIT-5-06).

## Deliverable format

**Write your edits directly to the 8 target files.** Do NOT write a
separate RESPONSE.md. Codex's edits ARE the response.

After all 8 files are updated, write a short summary report at:

```
research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/batches/batch_1_paper_planning/EDITS_SUMMARY.md
```

The summary should contain:

```markdown
# Batch 1 Edits Summary

## Files touched
| File | Edit type | Lines changed (rough) | Notes |
|---|---|---|---|
| PAPER_FRAME.md | rewrite | ... | ... |
| ... | ... | ... | ... |

## Cross-file invariant check
For each invariant in the prompt:
- Title (D-FRAME-016): present in [list files]; consistent across all
- ...

## Carry-over for batch 2 / later batches
[anything you noticed that's out of scope for batch 1 but should be
fixed in a later batch — name file + finding]

## Constitutional Classifiers / SHADE-Arena / etc citations
[where you added them, per the audit-derived annotation list]

## Open issues
[anything you couldn't resolve cleanly — name the file + the
ambiguity]
```

## Length and depth

Use `/goal` mode. This is heavy doc-rewrite work. Total batch is
~4,120 lines across the 8 files; you don't need to rewrite every
line, but every cross-file invariant must be satisfied.

Expected wall time: substantial. Take it. Worse to ship inconsistent
batch-1 files than to be slow.

## What NOT to do

- Do not edit files outside the 8 named targets in this batch. If
  another file under `research/runtime_contracts_paper/` clearly
  needs updating (e.g., `MECHANISM_INVENTORY.md`,
  `PRIOR_ART_POSITIONING.md`, `MODEL_ROSTER_DECISION_BRIEF.md`,
  `IMPLEMENTATION_PLAN.md`, `HAI_PAPER_READINESS_PLAN.md`,
  `RELATED_WORK_DRAFT.md`, `METHODS_SYSTEM_DRAFT.md`,
  `AUTONOMOUS_*`, `CLAUDE_CODE_*`, `CODEX_WORK_INSPECTION_INDEX.md`,
  `DOC_ALIGNMENT_AUDIT.md`), note it in the EDITS_SUMMARY.md
  carry-over section but do NOT edit it. The orchestrator will
  decide which sub-batch handles those.
- Do not edit files outside `research/runtime_contracts_paper/`.
  Phase 2 batch 1 is paper-planning files only; batches 2-6 handle
  benchmark spec, project cold-start, HAI runtime docs, operating
  contracts, and historical provenance.
- Do not modify `framing_v2/CONVERGED.md` or
  `framing_v2/ORCHESTRATOR_STATE.md` or any round_*/ file. Those
  are the orchestrator's source of truth and history.
- Do not reopen locked decisions D-FRAME-001 through D-FRAME-027.
  If a target file currently disagrees with a locked decision, the
  target file is wrong; update it.
- Do not invent new framing decisions. If you discover an ambiguity
  the locked decisions don't cover, surface it in EDITS_SUMMARY.md
  "Open issues" section rather than picking a value.
- Do not hallucinate citations. The prior-art arXiv IDs are
  verified in `round_5/AUDIT_RESPONSE.md` citation log. Use those
  same IDs.

## When done

1. All 8 files updated.
2. `EDITS_SUMMARY.md` written at the path above.
3. Notify Dom: "Phase 2 batch 1 complete. Files updated, summary
   at `framing_v2/phase_2_doc_alignment/batches/batch_1_paper_planning/EDITS_SUMMARY.md`."
4. Stop. Do not start batch 2 — that's the orchestrator's call after
   reviewing this batch's diff.

---

## Orchestrator notes for the fresh session

The orchestrator (Claude Code) will inspect this batch via:

```bash
git diff research/runtime_contracts_paper/PAPER_FRAME.md \
         research/runtime_contracts_paper/CLAIM_LADDER.md \
         research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md \
         research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md \
         research/runtime_contracts_paper/BASELINES_AND_ABLATIONS_PLAN.md \
         research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md \
         research/runtime_contracts_paper/DRAFT_PAPER.md \
         research/runtime_contracts_paper/WORK_PACKETS.md
```

before deciding whether to advance to batch 2.
