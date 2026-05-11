# Phase 2 Documentation Alignment — COMPLETE

**Status:** Phase 2 closed.
**Closed:** 2026-05-11
**Final audit verdict:** SHIP_WITH_NOTES (5 findings; 0 critical, 0
major, 3 minor, 2 nit; 3 fixed in-line at closure, 2 carried to a
post-Phase-2 polish pass)
**Phase 1 reference:** `framing_v2/CONVERGED.md` (2026-05-11)

---

## Phase 2 summary

Six batches + audit-findings-closure + final repo-wide audit ran on
2026-05-11.

| Batch | Files | Lines | Status | Provenance |
|---|---|---|---|---|
| 1 — paper planning | 8 | +1,374 / -779 | clean | `batches/batch_1_paper_planning/EDITS_SUMMARY.md` |
| 2 — benchmark spec + 2 schemas | 6 named + 1 collateral | +372 / -64 | clean; 15/15 schema-contract tests pass | `batches/batch_2_benchmark_spec/EDITS_SUMMARY.md` |
| 3 — project cold-start | 6 | +737 / -332 | clean; A2/B1 sweep clean | `batches/batch_3_project_cold_start/EDITS_SUMMARY.md` |
| 4 — HAI runtime docs (light touch) | 5 | +28 / -13 | clean; HAI freeze honored | `batches/batch_4_hai_runtime_docs/EDITS_SUMMARY.md` |
| 5 — operating contracts (AGENTS / CLAUDE / README) | 3 | +268 / -94 | clean; D19-D27 added to AGENTS.md | `batches/batch_5_operating_contracts/EDITS_SUMMARY.md` |
| 6 — historical provenance | 4 | +48 / -0 | clean; supersession headers only | `batches/batch_6_historical_provenance/EDITS_SUMMARY.md` |
| Audit-findings-closure | 1 (in-place annotation) | +closure section | clean | `research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response.md` |
| Final repo-wide audit | 1 (FINAL_AUDIT_RESPONSE.md) | — | **SHIP_WITH_NOTES** | `phase_2_doc_alignment/FINAL_AUDIT_RESPONSE.md` |

**Total Phase 2 doc-alignment delta:** ~2,827 insertions, ~1,282
deletions across ~33 files. Plus the audit-findings-closure annotation
on the 20-finding F-CDX-RFR-R1 audit response.

---

## Closure-time fixes (3 of 5 final-audit findings)

The final audit's three "one-line edit" findings were applied at
closure time rather than carried over:

- **F-AUDIT-PHASE2-01** (README "sensitive user-owned structured
  data"): replaced with "bounded agent operation in a non-clinical
  reference runtime." 2 lines changed in `README.md:111-112`.
- **F-AUDIT-PHASE2-03** (SCAFFOLD_VIEW.md M8 "audit chain"): renamed
  to "M8 audit evidence emission" + added M9-TX transaction-integrity
  bullet to the held-constant list. 5 lines changed in
  `benchmark/governed_agent_bench/SCAFFOLD_VIEW.md:46-54`.
- **F-AUDIT-PHASE2-05** (project/FRAME.md cold-start ordering):
  reordered the cold-start reading list to put
  `framing_v2/CONVERGED.md` first, matching AGENTS.md and CLAUDE.md.
  ~15 lines changed in `project/FRAME.md:138-155`.

---

## Carry-over to pre-pilot execution (not blocking Phase 2)

### From the final audit (2 of 5 findings — sweep-sized)

- **F-AUDIT-PHASE2-02 — workshop-as-current in 5 paper-lane planning
  files.** `AUTONOMOUS_PROJECT_EXECUTION_PLAN.md`,
  `AUTONOMOUS_GATE_HANDOFF.md`, `CODEX_WORK_INSPECTION_INDEX.md`,
  `IMPLEMENTATION_PLAN.md`, `METHODS_SYSTEM_DRAFT.md` still describe
  workshop-floor as the current target. Recommendation: targeted
  batch-7 supersession-header pass (matching the batch-6 pattern) or
  small per-file rewrites. Per-file cost is low; the decision is
  whether to header-supersede or rewrite.

- **F-AUDIT-PHASE2-04 — "sensitive user-owned data" residuals in 4
  prior-art docs.** `PRIOR_ART_POSITIONING.md`,
  `RELATED_WORK_DRAFT.md`, `prior_art_matrix.md`,
  `IMPLEMENTATION_PLAN.md`. Single sed-grade replacement pass; can
  fold into the same batch-7.

### From the audit-findings-closure annotations

- Commit `benchmark/governed_agent_bench/prompts/deployment_full_v1.md`
  before §7-§8 paper-claim runs (F-CDX-RFR-R1-05 residual).
- Commit `benchmark/governed_agent_bench/scorer_config.paper_v1.json`
  before paper-claim runs (F-CDX-RFR-R1-06 residual).
- Commit `benchmark/governed_agent_bench/model_roster.md` with
  frozen D-FRAME-020 roster + May 2026 pricing snapshot date
  (F-CDX-RFR-R1-07 residual).
- Hermetic-mode resolver E2E validation before §7-§8 attack-policy
  runs against synthetic fixtures (F-CDX-RFR-R1-11 residual).
- Work-packet template completeness pass for
  `research/runtime_contracts_paper/WORK_PACKETS.md`
  (F-CDX-RFR-R1-14 + F-CDX-RFR-R1-15 partial closures).

### From batch 3 EDITS_SUMMARY carry-over

- **Test alignment:** 2 stale tests in
  `project/tests/test_project_reframe_docs_alignment.py` assert
  pre-reframe strings ("HAI Paper-Readiness Engineering",
  pre-framing-v2 title). Final audit confirmed both fail for the
  documented string-mismatch reason only, not a regression. Update
  or retire the assertions in pre-pilot cleanup.

---

## Phase 1 + Phase 2 cumulative output

| Surface | Phase 1 (research) | Phase 2 (doc alignment) |
|---|---|---|
| Framing decisions | 27 locked (D-FRAME-001..027) | propagated across 33 files |
| Audit rounds | 3 (R3 / R4 / R5) | 1 (final repo-wide) |
| Audit verdicts | 3 × SHIP_WITH_NOTES (0 paper-§-level findings in R5 → escape valve) | SHIP_WITH_NOTES (5 nit/minor, 0 paper-§-level) |
| Audit-findings closure | — | F-CDX-RFR-R1-01..20 annotated |
| Schema state | spec-only | 15/15 schema-contract tests pass; `claim_tier` required; T3/T4 conditional on `model_roster_hash` |
| Cold-start ordering | introduced framing_v2/CONVERGED.md | first in AGENTS.md, CLAUDE.md, project/FRAME.md |
| Stale test status | — | 2 known-stale assertions, fail for documented reason only |

---

## Calendar binding

Phase 2 closed ahead of the calendar target (mid-July 2026 originally
estimated). Phase 1 + 2 ran end-to-end on 2026-05-11.

| Date | Event | Status |
|---|---|---|
| 2026-05-11 | Phase 1 convergence (escape valve) | DONE |
| 2026-05-11 | Phase 2 documentation alignment closed | **DONE** |
| 2026-06-15 | Sonnet 4 retirement; §7.5 paper-claim cells must complete OR re-anchor | Pending |
| 2026-07-20 to 2026-08-05 | Engels pilot (de-risk merge) | Pending |
| 2026-08-10 | Pilot decision gate | Pending |
| 2027-05-15 (approx) | NeurIPS 2027 main submission deadline | Pending |

---

## What changed in the repo

The merged-paper framing v2 is now propagated across **all active
surfaces**:

- **Cold-start authority:** `framing_v2/CONVERGED.md` →
  `framing_v2/ORCHESTRATOR_STATE.md` → `project/FRAME.md` →
  `project/DECISIONS.md` (D-PROJ-018..023) → `AGENTS.md` "Settled
  Decisions" D19-D27.
- **Paper-planning lane:** 8 files rewritten / revised / superseded
  in batch 1.
- **Benchmark spec lane:** 6 files (4 markdown + 2 schemas) updated
  in batch 2; schemas tightened with `claim_tier` required + T3/T4
  conditional on `model_roster_hash`; 15/15 schema-contract tests
  pass.
- **Project cold-start lane:** 6 files updated in batch 3; H1
  refactored around contract-as-trusted-monitor; A2/B1 framing
  retained only in closed-marker context.
- **HAI runtime docs:** 5 files updated in batch 4 with light touch
  (+28/-13 total); HAI freeze (D-PROJ-016) honored — no runtime
  architecture content touched.
- **Operating contracts:** AGENTS.md / CLAUDE.md / README.md updated
  in batch 5; framing-v2 orchestration pattern added to "Patterns
  the cycles have validated"; pre-pilot pitch in README.md.
- **Historical provenance:** 4 pre-reframe HAI planning files marked
  with supersession headers in batch 6.
- **Audit-findings:** F-CDX-RFR-R1-01..20 explicitly closed in the
  original audit-response file.

---

## Next step

Phase 2 is closed. The orchestration's job ends here. The next
substantive project step is the **Engels pilot** in July 2026, with
the pre-pilot execution items in the carry-over list above as
prerequisites.

The framing_v2 orchestration directory remains on disk as the
authoritative record of the convergence-and-alignment cycle. Future
framing-class cycles should follow the same two-phase shape:

1. Phase 1 research convergence with worker-auditor-orchestrator
   triad + escape valve at three consecutive SHIP_WITH_NOTES with
   zero paper-§-level findings.
2. Phase 2 batched documentation alignment with end-of-phase audit
   only.

This pattern is recorded in AGENTS.md "Patterns the cycles have
validated" (added at batch 5) and is now project-standard for
framing-class work.
