# Phase 2 Batch 6 Worker Prompt — Historical Provenance Supersession

**Drafted:** 2026-05-11
**Phase:** 2 — Documentation alignment
**Batch:** 6 of 6 — Historical provenance (mark superseded)
**Worker:** Codex via `/goal`
**Audit cadence:** end-of-phase only.

---

## Identity

You are Codex in `/goal` mode, executing Phase 2 batch 6 of the
runtime-contracts paper framing v2 orchestration. Phase 2 is doc-edit
work; write edits directly to target files.

## Project briefing

Phase 1 closed 2026-05-11 with 27 locked framing decisions
(D-FRAME-001..027). Batches 1-5 closed clean: paper-planning,
benchmark spec + schemas, project cold-start, HAI runtime docs (light
touch), operating contracts.

Batch 6 is **the lightest batch.** Per `PHASE_PLAN.md` §3 batch 6:

> Action: add header noting "superseded by merged-paper framing v2;
> preserved as historical provenance." Do not rewrite. Do not delete.

These 4 files are pre-reframe HAI planning artifacts that survive on
disk as provenance. They describe earlier shapes of the project's
research direction (HAI value framework, pre-reframe eval strategy,
HAI risks register, HAI strategic plan v2). The merged-paper framing
v2 supersedes them at the project level, but they are not deletable —
they are the audit trail for past decisions.

## Required reading

1. `research/runtime_contracts_paper/framing_v2/CONVERGED.md` — locked
   framing summary (cite this in each supersession header).
2. `AGENTS.md` (now framing-v2-aligned after batch 5) — confirms the
   active framing.
3. `project/REPO_MAP.md` — historical/active classifications.
4. A quick skim of each target file's existing top-of-file content
   so the supersession header is grammatically inserted, not
   stapled awkwardly.

## Target files (4)

For each file, **prepend a supersession header at the top.** Do NOT
rewrite the body. Do NOT delete content. Do NOT update inline
references in the body even if they're stale — the supersession
header explicitly disclaims those.

The header pattern:

```markdown
# [original title]

> **Superseded as current planning:** This file describes a
> pre-reframe project shape. The active framing as of 2026-05-11 is
> `research/runtime_contracts_paper/framing_v2/CONVERGED.md` —
> "Deterministic Software Contracts as Trusted Monitors in AI
> Control Protocols" (NeurIPS 2027 main conference). Decisions in
> this file may be inconsistent with the merged-paper framing; treat
> the body as **historical provenance only**, not as current
> planning truth. For the current project decisions, read
> `framing_v2/CONVERGED.md`, `framing_v2/ORCHESTRATOR_STATE.md`,
> and `project/DECISIONS.md`.

---

[existing body, unchanged]
```

If the existing top-of-file already has a YAML frontmatter or
status marker, insert the supersession header **after** the
frontmatter but **before** the body proper. Match the file's
existing header style (e.g., if the file uses `> ` blockquote
style elsewhere, keep that; if it uses callout boxes, adapt).

### The 4 target files

1. **`hai/reporting/plans/post_v0_1_18/strategic_plan_v2.md`** (~41
   KB) — pre-reframe HAI strategic plan v2. Supersession header.

2. **`hai/reporting/plans/success_framework_v1.md`** (~19 KB) —
   pre-reframe HAI value framework. Supersession header.

3. **`hai/reporting/plans/eval_strategy/v1.md`** (~21 KB) —
   pre-reframe HAI correctness strategy. Supersession header.

4. **`hai/reporting/plans/risks_and_open_questions.md`** (~28 KB) —
   pre-reframe HAI risk register. Supersession header. Note:
   this file is named in `AGENTS.md` as "pre-reframe HAI risk
   register; useful provenance/support-lane input" — that AGENTS.md
   note remains valid; the supersession header just makes the
   provenance status explicit at the top of the file itself.

## Cross-file invariants

Each supersession header must:

- Name `framing_v2/CONVERGED.md` as the active framing source.
- Quote the locked title D-FRAME-016.
- Name the NeurIPS 2027 venue.
- Date the supersession as 2026-05-11.
- Direct readers to `framing_v2/CONVERGED.md`,
  `framing_v2/ORCHESTRATOR_STATE.md`, and `project/DECISIONS.md`
  for current planning truth.

## Deliverable format

**Write your edits directly to the 4 target files.** Do NOT write a
separate RESPONSE.md.

After all 4 files are updated, write a summary at:

```
research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/batches/batch_6_historical_provenance/EDITS_SUMMARY.md
```

Structure:

```markdown
# Batch 6 Edits Summary

## Files touched
| File | Supersession header inserted? | Body modified? | Lines added |

## Header content verification
- All 4 headers cite `framing_v2/CONVERGED.md`? yes/no
- All 4 headers quote D-FRAME-016 title? yes/no
- All 4 headers name NeurIPS 2027 venue? yes/no
- All 4 headers dated 2026-05-11? yes/no

## Body sanity check
- Was any body content modified? Should be NO.
- Was any body content deleted? Should be NO.

## Carry-over for audit-findings-closure batch
[anything noticed]

## Open issues
[anything you couldn't resolve cleanly]
```

## What NOT to do

- **Do NOT rewrite the bodies of these files.** Supersession headers
  ONLY.
- **Do NOT delete content.** Even stale prose inside the body must
  remain — the supersession header disclaims it.
- Do not edit files outside the 4 named targets.
- Do not update inline references inside the body that are stale —
  that defeats the purpose of historical provenance.
- Do not invent a new D-FRAME or D-PROJ number.
- Do not write a separate RESPONSE.md.

## When done

1. All 4 target files have a supersession header at the top.
2. `EDITS_SUMMARY.md` written.
3. Notify Dom: "Phase 2 batch 6 complete. Files updated, summary at
   `framing_v2/phase_2_doc_alignment/batches/batch_6_historical_provenance/EDITS_SUMMARY.md`."
4. Stop. After batch 6, the orchestrator handles the
   audit-findings-closure batch (F-CDX-RFR-R1-01..11) and the final
   repo-wide audit.

---

## Orchestrator notes

After Codex returns, the orchestrator inspects via:

```bash
git diff hai/reporting/plans/
```

The diff should be **very small.** If any body content was modified
beyond the supersession header insertion, Codex overstepped.
