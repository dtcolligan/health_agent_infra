# Phase 2 Batch 4 Worker Prompt — HAI Runtime Docs (Light Touch)

**Drafted:** 2026-05-11
**Phase:** 2 — Documentation alignment
**Batch:** 4 of 6 — HAI runtime docs
**Worker:** Codex via `/goal`
**Audit cadence:** end-of-phase only.

---

## Identity

You are Codex in `/goal` mode, executing Phase 2 batch 4 of the
runtime-contracts paper framing v2 orchestration. Phase 2 is doc-edit
work; write edits directly to target files.

## Project briefing

Phase 1 closed 2026-05-11 with 27 locked framing decisions
(D-FRAME-001..027). Batches 1 (paper-planning), 2 (benchmark spec +
schemas), and 3 (project cold-start) closed clean.

Batch 4 is **deliberately a light touch.** Per `PHASE_PLAN.md` §3
batch 4:

> Acceptance: only references to paper framing updated; HAI runtime
> architecture content NOT touched (HAI is frozen as product).

D-PROJ-016 (HAI freeze, 2026-05-08) means **HAI runtime architecture
is locked.** Do not rewrite installation steps, operator workflow,
domain definitions, CLI surface descriptions, schema head, migration
discipline, or any HAI-internal architecture content. Only update
**references to paper framing** that appear inside these files.

The risk this batch addresses: HAI runtime docs may currently cite
pre-merge paper framing (workshop venue, "sensitive user-owned data"
phrasing, A2 / B1 framing), which would mislead cold-start readers
who land on these files first.

## Required reading (in this order)

1. `research/runtime_contracts_paper/framing_v2/CONVERGED.md` — locked
   framing summary.
2. `research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`
   — locked decisions table.
3. `research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/batches/batch_3_project_cold_start/EDITS_SUMMARY.md`
   — what just landed in `project/`.
4. Current state of all 5 target files.
5. `AGENTS.md` "Do Not Do" section + D-PROJ-016 entry — confirms the
   HAI freeze posture you must honor.

## Target files (5)

For each file, the rule is the same: **update paper-framing
references only.** Identify any prose that:

- Names a pre-merge paper title.
- Refers to "workshop venue" / "workshop preprint" as the current
  target.
- Uses the dropped "sensitive user-owned data" framing.
- References A2 (capability-elicitation reframe) or B1 (no red-team)
  as current.
- Cites the pre-reframe roadmap or pre-reframe operating model.

For each such reference: update the prose to point at the merged-
paper framing OR mark the prose as superseded provenance with a
pointer to `framing_v2/CONVERGED.md`. Do not delete content;
update or annotate.

The 5 target files:

1. **`hai/docs/hai_reference_runtime.md`** (346 lines, **light
   touch**) — HAI install, operator workflow, domains, CLI surface.
   The bulk of this file is HAI runtime architecture content —
   leave alone. Only update any paragraphs that name the paper, its
   venue, its framing, or its prior names. Add a one-line header
   note clarifying "This file describes the HAI reference runtime;
   for the active paper framing, see
   `research/runtime_contracts_paper/framing_v2/CONVERGED.md`."

2. **`hai/docs/runtime_contract_overview.md`** (167 lines, **light
   touch**) — one-page architecture overview. This is the closest
   HAI doc to the paper subject matter, so it may have the most
   paper-framing references. Update each one. Critical: the M4-M8
   mechanism names must match D-FRAME-017 (M7 narrow to
   clinical-boundary refusal; M8 renamed "audit evidence emission";
   M9-TX held constant). If this file uses pre-merge mechanism
   naming, update.

3. **`hai/docs/current_system_state.md`** (198 lines, **light
   touch**) — latest shipped truth (version, schema head, command
   count, next-cycle posture). Bulk is runtime state; leave alone.
   The "next cycle" / "future work" sections may name pre-merge
   paper work — update those to reflect the merged-paper objective
   (NeurIPS 2027) and Phase 2 doc-alignment cycle (current).

4. **`hai/docs/architecture.md`** (603 lines, **light touch**) —
   full pipeline + code-vs-skill boundary. Largest file but mostly
   HAI architecture content (do not touch). Search for any paper-
   framing prose and update. Mechanism naming (M4-M8 + M9-TX) must
   match D-FRAME-017 if mentioned.

5. **`hai/docs/non_goals.md`** (161 lines, **light touch**) — scope
   discipline. If any non-goal statement is now paper-relevant
   (e.g., "no clinical claims" relates to D-FRAME-013 personal-
   wellness-as-instantiation + the non-clinical safety boundary in
   the merged paper §10 limitations), add a one-line cross-reference
   to the paper §. Otherwise leave alone.

## Cross-file invariants

### Title (D-FRAME-016)
If any of these files names the paper by title, the title must be:
> Deterministic Software Contracts as Trusted Monitors in AI Control
> Protocols

### Venue (D-FRAME-008)
NeurIPS 2027 main conference. NOT workshop / NOT NeurIPS Safe GenAI
workshop.

### Mechanism inventory (D-FRAME-017)
If any file references M-numbers:
- M4 = validation
- M5 = `agent_safe` dispatch refusal
- M6 = W57 proposal/commit gate
- M7 = clinical-boundary refusal (narrow; JSON exempt)
- M8 = audit **evidence emission** (renamed from "audit chain")
- M9-TX = transaction integrity (held constant, non-ablatable)

### Cold-start ordering
HAI runtime docs are not the cold-start authority for the paper.
The cold-start authority is `framing_v2/CONVERGED.md`. Each of these
5 files should make that clear at the top OR in a "for paper framing
see..." pointer.

### HAI freeze (D-PROJ-016)
HAI is frozen as a product. These docs describe the v0.2.0 PyPI
snapshot. Do not update HAI version numbers, command counts, schema
heads, or runtime architecture; those are HAI artifact state, not
paper-framing references.

## Audit-derived annotations

- **F-AUDIT-5-02 manifest reference:** if any of these files cites
  the HAI manifest size, it must read "HAI v0.2.0 manifest snapshot
  at `benchmark/governed_agent_bench/manifests/hai_0_2_0.json` ≈ 189 KB."
- **F-AUDIT-5-01 HS gloss:** if any of these files describes
  Hierarchical Summarization (unlikely but possible — HAI docs
  generally don't discuss HS), the methodology framing must NOT
  include "optional classifier" as a documented HS feature.

## Deliverable format

**Write your edits directly to the 5 target files.** Do NOT write a
separate RESPONSE.md.

After all 5 files are updated, write a summary at:

```
research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/batches/batch_4_hai_runtime_docs/EDITS_SUMMARY.md
```

Structure:

```markdown
# Batch 4 Edits Summary

## Files touched
| File | Edit type | Lines changed (rough) | Notes |

## Paper-framing references updated
For each file, list the specific references found and the change:
- `hai/docs/X.md`:
  - Found "workshop venue" reference at line N → updated to "NeurIPS 2027 main conference"
  - Found "Paper 1" framing at line N → updated to "merged paper"
  - ...

## HAI runtime architecture content touched?
yes/no. If yes, list what and why. Should normally be NO.

## Mechanism inventory consistency
If M4-M8 named anywhere, list the file + line + verification that
naming matches D-FRAME-017.

## Cold-start pointer to framing_v2/CONVERGED.md
List which files now point to CONVERGED.md as the paper-framing
authority.

## Carry-over for batch 5+
[anything noticed]

## Open issues
[anything you couldn't resolve cleanly]
```

## What NOT to do

- **Do NOT rewrite HAI runtime architecture.** The HAI freeze
  (D-PROJ-016) means installation steps, operator workflow, domain
  definitions, CLI surface, schema head, migration discipline, and
  HAI-internal architecture content are out of scope.
- Do not edit files outside `hai/docs/`. If a cross-batch issue
  surfaces (e.g., AGENTS.md or CLAUDE.md reference HAI docs that
  need realignment), flag in EDITS_SUMMARY.md carry-over — those
  are batch 5.
- Do not update HAI version numbers, command counts, schema heads.
  These reflect actual HAI artifact state.
- Do not reopen D-FRAME-014 / D-FRAME-015 (A2 / B1 closed).
- Do not write a separate RESPONSE.md.

## When done

1. All 5 target files updated (light touch).
2. `EDITS_SUMMARY.md` written.
3. Notify Dom: "Phase 2 batch 4 complete. Files updated, summary at
   `framing_v2/phase_2_doc_alignment/batches/batch_4_hai_runtime_docs/EDITS_SUMMARY.md`."
4. Stop. Do not start batch 5.

---

## Orchestrator notes

After Codex returns, the orchestrator inspects via:

```bash
git diff hai/docs/
```

The diff should be **small.** If the diff is large (e.g., > 200
lines changed), Codex likely overstepped into HAI runtime architecture
content. The orchestrator will inspect and potentially send back.
