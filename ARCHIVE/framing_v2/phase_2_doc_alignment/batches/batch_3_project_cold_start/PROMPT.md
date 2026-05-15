# Phase 2 Batch 3 Worker Prompt — Project Cold-Start Files

**Drafted:** 2026-05-11
**Phase:** 2 — Documentation alignment
**Batch:** 3 of 6 — Project cold-start files
**Worker:** Codex via `/goal`
**Audit cadence:** end-of-phase only.

---

## Identity

You are Codex in `/goal` mode, executing Phase 2 batch 3 of the
runtime-contracts paper framing v2 orchestration. Phase 2 is doc-edit
work; write edits directly to target files.

## Project briefing

Phase 1 closed 2026-05-11 with 27 locked framing decisions
(D-FRAME-001..027). Batch 1 (paper-planning files) and batch 2
(benchmark spec + schemas) closed clean.

Batch 3 propagates the locked framing into the **project cold-start
files** under `project/`. These are the files Dom reads first in a
fresh Claude Code session (per `AGENTS.md` and `CLAUDE.md` session-
start orientation). They are the highest-leverage docs in the repo:
if cold-start docs disagree with the locked framing, the next session
will operate from stale assumptions.

The acceptance criterion (per `PHASE_PLAN.md` §3 batch 3):

> Cold-start docs tell the merged-paper story; no references to A2
> framing or B1 threat model survive.

**A2 reframe** (D-FRAME-014, locked): the "capability-elicitation /
weak-to-strong" reframe that was considered and rejected. Any
remaining A2 references must be removed or marked superseded.

**B1 threat model** (D-FRAME-015, locked): the "no red-team / pure
capability-failure" threat model that was considered and rejected.
Any remaining B1 references must be removed; the locked threat model
is D-FRAME-003 (capability-failure + targeted adversarial layer).

## Required reading (in this order)

1. `research/runtime_contracts_paper/framing_v2/CONVERGED.md` — locked
   framing summary + 27 decisions.
2. `research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`
   — full decisions table.
3. `research/runtime_contracts_paper/framing_v2/round_3/SYNTHESIS.md`,
   `round_4/SYNTHESIS.md`, `round_5/SYNTHESIS.md` — Phase 2 action
   items.
4. Current state of all 6 target files (read each before editing).
5. `research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/batches/batch_1_paper_planning/EDITS_SUMMARY.md`
   and `batches/batch_2_benchmark_spec/EDITS_SUMMARY.md` — what
   was already changed so you can reference rather than restate.

## Target files (6)

1. **`project/FRAME.md`** (106 lines, **rewrite**) — the canonical
   research framing file. Must reflect the merged-paper title
   (D-FRAME-016), headline framing (D-FRAME-001), triple lineage
   anchor (D-FRAME-002), three load-bearing claims, and the priority
   order: paper + benchmark first, HAI reference runtime second.
   Replace any pre-merge "Paper 1 vs Paper 2" framing with the
   merged-paper framing.

2. **`project/DECISIONS.md`** (522 lines, **append new D-PROJ-018+
   records**) — this file is the project-level decision log. The
   current head is D-PROJ-017. Append new D-PROJ-NNN records that
   import the framing-v2 locked decisions as project-level decisions:

   - **D-PROJ-018:** Merged paper trajectory locked. Provenance:
     `framing_v2/CONVERGED.md` 2026-05-11. Inherits D-FRAME-009 (merge)
     + D-FRAME-016 (title) + D-FRAME-008 (NeurIPS 2027 main venue).
   - **D-PROJ-019:** Engels pilot July 2026 as merge-decision gate.
     Inherits D-FRAME-011 + D-FRAME-018.
   - **D-PROJ-020:** Predeclared model roster + cost ceiling
     ($1,500). Inherits D-FRAME-020 + D-FRAME-023.
   - **D-PROJ-021:** Adversarial layer is constitutive (not optional).
     Inherits D-FRAME-015 (B1 closed) + D-FRAME-022 + D-FRAME-019
     paper-killer preempts.
   - **D-PROJ-022:** Paper 2 = S1 fine-tuning of bounded operators
     at ICML 2028 / NeurIPS 2028. Inherits D-FRAME-010 + D-FRAME-027.
   - **D-PROJ-023:** Phase 2 documentation-alignment cycle
     2026-05-11. Inherits the framing-v2 orchestration; cite
     `framing_v2/CONVERGED.md` as source-of-truth.

   Do NOT rewrite existing D-PROJ-001 through D-PROJ-017 entries.
   Append only.

3. **`project/OPERATING_MODEL.md`** (196 lines, **revise**) — internal
   operating model + documentation-alignment gate. Update to reflect:
   - The merged-paper objective (replaces any pre-merge two-paper
     framing).
   - The documentation-alignment gate is **PARTIALLY MET** as of
     2026-05-11: Phase 1 framing closed, Phase 2 doc alignment in
     progress (batches 1-2 closed, batches 3-6 + audit-findings-
     closure + repo-wide audit pending).
   - Reference `framing_v2/CONVERGED.md` as the cold-start authority
     for the paper framing.
   - The artifact hierarchy must name `framing_v2/CONVERGED.md` and
     `framing_v2/ORCHESTRATOR_STATE.md` as the top-level paper-
     framing authority above `PAPER_OUTLINE_MERGED.md`.

4. **`project/HYPOTHESES.md`** (158 lines, **refactor H1 around
   contract-as-trusted-monitor**) — the hypotheses file. H1 was the
   foundational hypothesis "runtime contracts reduce required model
   scale for safe bounded agent operation." Refactor it to align
   with the locked headline framing:
   - **H1 (refactored):** *Deterministic software contracts can
     serve as the trusted monitor in an AI control protocol for
     bounded agent operation, with measurable per-mechanism
     contributions to safety-constrained operation under a held-
     constant deployment prompt.*
   - **H2 (new or kept):** *Under the full contract, the smallest
     predeclared model passes all primary thresholds; under
     `no_runtime_enforcement`, a larger predeclared model fails at
     least one. The contract shifts the model-scale safety curve.*
   - **H3 (new or kept):** *A deterministic Guard at general Elo = 0
     occupies a legitimate point on the Engels scaling-laws-for-
     oversight curve for the Backdoor Code game.*
   - Add an explicit "out-of-scope hypotheses" section naming what
     this paper does NOT claim: full control safety case for
     scheming models, cross-domain generalization, semantic
     monitoring beyond clinical-boundary refusal, MCP server
     contract composition.

5. **`project/ROADMAP.md`** (116 lines, **revise**) — now/next
   roadmap. Must reflect:
   - **Now (2026-05):** Phase 2 documentation alignment in progress
     (batches 1-2 closed; batches 3-6 in progress).
   - **Next (2026-06):** Phase 2 closure + final repo-wide audit.
     Sonnet 4 retirement 2026-06-15 binding.
   - **Then (2026-07):** Engels pilot. Decision gate August 2026.
   - **Out (post-Aug):** mechanism ablations (Nov 2026), full Engels
     (Feb 2027), red-team (Mar 2027), bounded HS (Mar 2027),
     manuscript v1 (Apr 2027), NeurIPS 2027 submission (May 2027).
   - **Explicitly out-of-scope:** HAI v0.2.1+ unless paper-critical
     (D-PROJ-016 HAI freeze); cross-domain reference runtimes;
     hosted-product deployment.

6. **`project/REPO_MAP.md`** (104 lines, **only if active/historical
   reclassification needed**) — every top-level entry classified
   active/historical. Update only if framing-v2 work has changed
   the active/historical status of a directory. The `framing_v2/`
   directory should be classified as **active**. The `round_*/`
   subdirectories are **active provenance**. Other paths likely
   unchanged. If nothing needs reclassification, leave the file
   alone but state that in EDITS_SUMMARY.md.

## Cross-file invariants

Every batch-3 file must agree on:

### Title (D-FRAME-016)
> Deterministic Software Contracts as Trusted Monitors in AI Control
> Protocols

### Active objective
Runtime-contract paper + GovernedAgentBench at NeurIPS 2027 main
conference (May 2027 deadline). HAI as reference runtime,
subordinate to paper artifacts unless directly supporting them.

### Closed reframes (D-FRAME-014 + D-FRAME-015)
A2 (capability-elicitation/weak-to-strong) and B1 (no red-team) are
closed and must not appear as current proposals. Any historical
mentions must be marked clearly as "closed in Round 2" or
"superseded by D-FRAME-014/015."

### Threat model (D-FRAME-003)
Capability-failure + targeted adversarial layer (50 trajectories
across 4 attack types + adaptive-vs-DRG-0). NOT pure capability-
failure (B1); NOT full attack-policy substitution.

### Mechanism inventory (D-FRAME-017)
M4 validation / M5 agent_safe / M6 proposal-commit gate / M7
clinical-boundary refusal (narrow, JSON exempt) / M8 audit evidence
emission / M9-TX transaction integrity (held constant).

### Source-of-truth ordering for the paper
The cold-start files should name this ordering:

1. `framing_v2/CONVERGED.md` (top-level locked framing)
2. `framing_v2/ORCHESTRATOR_STATE.md` (decisions table with
   provenance)
3. `research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md`
   (canonical paper outline)
4. The batch-1 paper-planning files (PAPER_FRAME, CLAIM_LADDER,
   etc.) — derivative of CONVERGED.md, kept aligned per Phase 2
   batch 1.
5. The batch-2 benchmark spec files — derivative.

Older files (DRAFT_PAPER.md, pre-merge PAPER_FRAME, etc.) are
historical provenance only.

## Deliverable format

**Write your edits directly to the target files.** Do NOT write a
separate RESPONSE.md.

After all 6 target files are updated, write a summary at:

```
research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/batches/batch_3_project_cold_start/EDITS_SUMMARY.md
```

Use the same structure as prior batches. Include:

```markdown
# Batch 3 Edits Summary

## Files touched
| File | Edit type | Lines changed (rough) | Notes |

## Cross-file invariant check
For each invariant (title, active objective, closed reframes,
threat model, mechanism inventory, source-of-truth ordering):
- ...

## New D-PROJ records appended
- D-PROJ-018: ...
- D-PROJ-019: ...
- D-PROJ-020: ...
- D-PROJ-021: ...
- D-PROJ-022: ...
- D-PROJ-023: ...

## H1 refactor confirmation
- H1 previous wording: ...
- H1 new wording: ...
- H2/H3 status: kept / added / refactored
- Out-of-scope hypotheses section: present / absent

## REPO_MAP.md changes
- Reclassifications performed: [list, or "none — file unchanged"]

## A2 / B1 residual sweep
- Files searched: project/*.md
- Residual A2 mentions outside historical-marker context: [list, or "none"]
- Residual B1 mentions outside historical-marker context: [list, or "none"]

## Carry-over for batch 4+
[anything noticed]

## Open issues
[anything you couldn't resolve cleanly]
```

## What NOT to do

- Do not edit files outside `project/`. If a cross-batch issue
  surfaces (e.g., `AGENTS.md` or `CLAUDE.md` reference the wrong
  cold-start path), flag in EDITS_SUMMARY.md carry-over — AGENTS.md
  and CLAUDE.md are batch 5 (operating contracts).
- Do not rewrite existing D-PROJ-001 through D-PROJ-017 records;
  append D-PROJ-018+ only.
- Do not delete prior hypotheses; refactor H1 in place and mark
  any superseded sub-points clearly.
- Do not change `framing_v2/` files or the merged paper outline.
- Do not reopen D-FRAME-014 (A2 closed) or D-FRAME-015 (B1 closed).
- Do not write a separate RESPONSE.md.

## When done

1. All 6 target files updated.
2. `EDITS_SUMMARY.md` written.
3. Notify Dom: "Phase 2 batch 3 complete. Files updated, summary at
   `framing_v2/phase_2_doc_alignment/batches/batch_3_project_cold_start/EDITS_SUMMARY.md`."
4. Stop. Do not start batch 4.

---

## Orchestrator notes

After Codex returns, the orchestrator inspects via:

```bash
git diff project/
```

and runs an A2/B1 residual sweep:

```bash
rg -ni "capability.elicitation|weak.to.strong" project/  # A2 residuals
rg -ni "no red.team|capability.failure only" project/    # B1 residuals
```

before advancing to batch 4 (HAI runtime docs light touch).
