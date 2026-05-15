# Phase 2 Final Repo-Wide Audit Response

**Auditor:** Claude Code Agent (general-purpose subagent)
**Date:** 2026-05-11
**Scope:** Mechanical-consistency audit of merged-paper framing v2
across active docs after Phase 2 batches 1-6 + audit-findings-closure.

## Verdict: SHIP_WITH_NOTES

The cross-repo state is internally consistent on every load-bearing
invariant: title, venue, threat model, mechanism inventory, model
roster, cost ceiling, bounded-HS, ST-WAB axis, schemas, and audit-
findings closure all check out. Batches 1-6 propagated D-FRAME-001..027
cleanly into the active surfaces they touched. The five residual
findings below are concentrated in files that Phase 2 did not list as
in-scope (notably `AUTONOMOUS_PROJECT_EXECUTION_PLAN.md`,
`AUTONOMOUS_GATE_HANDOFF.md`, `CODEX_WORK_INSPECTION_INDEX.md`,
`IMPLEMENTATION_PLAN.md`, `METHODS_SYSTEM_DRAFT.md`, `SCAFFOLD_VIEW.md`,
`PRIOR_ART_POSITIONING.md`, `RELATED_WORK_DRAFT.md`, `prior_art_matrix.md`),
plus one stray phrasing in `README.md`. None are paper-§-level. None
block Phase 2 closure. All can land in the pre-pilot execution carry-
over.

## Findings

### F-AUDIT-PHASE2-01 — `README.md` still uses "sensitive user-owned structured data" as current framing

- **Severity:** minor
- **Where:** `README.md:112` — "It is not the paper's topic by itself.
  It is the demonstrator domain for bounded operation over sensitive
  user-owned structured data."
- **Finding:** D-FRAME-012 explicitly closed dropping the
  "user-owned structured data" phrasing from current framing
  (closed under round 1-2 of framing v2). Batch 5 rewrote the README
  but left this one paragraph carrying the pre-merge phrasing. The
  README is the highest-visibility public surface; this is the kind of
  drift a fresh reader notices first.
- **Suggested fix:** Replace "sensitive user-owned structured data"
  with the locked phrasing — e.g. "bounded operation over local
  user-owned state" or, mirroring the rest of the README, "bounded
  agent operation in a non-clinical reference domain."
- **Provenance check:** D-FRAME-012 in `framing_v2/CONVERGED.md` +
  `framing_v2/ORCHESTRATOR_STATE.md` locked-decisions table. Batch 5
  EDITS_SUMMARY claims conservative re-pitch; this string survived.

### F-AUDIT-PHASE2-02 — Five paper-lane planning files still teach workshop-floor as the current target

- **Severity:** minor
- **Where:**
  - `research/runtime_contracts_paper/AUTONOMOUS_PROJECT_EXECUTION_PLAN.md`
    ("workshop-ready runtime-contract paper", `WP-AUDIT-001 final
    workshop audit`, "workshop finalization")
  - `research/runtime_contracts_paper/AUTONOMOUS_GATE_HANDOFF.md`
    ("workshop-ready paper", "rule-baseline-only workshop path")
  - `research/runtime_contracts_paper/CODEX_WORK_INSPECTION_INDEX.md`
    ("workshop-complete", "T0 workshop path")
  - `research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md`
    ("Out of workshop floor", "ML systems/agent workshop")
  - `research/runtime_contracts_paper/METHODS_SYSTEM_DRAFT.md`
    ("workshop-floor infrastructure")
- **Finding:** These five active paper-lane planning files were
  authored 2026-05-10 (or earlier) and were not in any Phase 2 batch
  scope. They still describe the project as moving toward a
  workshop-ready paper. After D-FRAME-008 (NeurIPS 2027 main) +
  D-FRAME-009 (merged trajectory), workshop-as-target language survives
  only as a *fallback* (Trajectory A revert if the Engels pilot fails).
  These files use it as the current goal.
- **Suggested fix:** Add a top-of-file supersession header pointing to
  `framing_v2/CONVERGED.md` (matching the batch-6 pattern) OR queue a
  targeted batch-7 rewrite of the workshop-as-current passages. The
  header approach is the lower-risk option since these are autonomous-
  execution planning artifacts whose interior structure is still useful
  provenance.
- **Provenance check:** D-FRAME-008/009 in `framing_v2/CONVERGED.md`.
  Phase 2 batch 1 scope (per `batches/batch_1_paper_planning/`) did not
  include any of these files.

### F-AUDIT-PHASE2-03 — `SCAFFOLD_VIEW.md` still names M8 as "audit chain"

- **Severity:** nit
- **Where:** `benchmark/governed_agent_bench/SCAFFOLD_VIEW.md:46` —
  "M8 audit chain: evidence-reference emission used by read-surface
  narration tasks."
- **Finding:** D-FRAME-017 renamed M8 to "audit evidence emission" and
  added M9-TX as separate held-constant non-ablatable. Every other
  benchmark/paper-planning file (PAPER_FRAME, RESEARCH_EVAL_STRATEGY,
  CLAIM_LADDER, BASELINES_AND_ABLATIONS_PLAN, HAI_PAPER_READINESS_EXECUTION,
  BENCHMARK_SPEC, SCORING_SPEC, AGENTS.md, project/FRAME.md) uses the
  new M8 name. SCAFFOLD_VIEW.md was not in any Phase 2 batch.
  SCAFFOLD_VIEW.md also does not name M9-TX, where its sibling files
  do.
- **Suggested fix:** One-line rename + add M9-TX bullet to the
  held-constant list. The file already lists transaction integrity in
  the held-constant block (line 54), so the rename is the only edit
  strictly required.
- **Provenance check:** D-FRAME-017 in `framing_v2/CONVERGED.md`.

### F-AUDIT-PHASE2-04 — Three prior-art docs retain "sensitive user-owned data/state" as current framing

- **Severity:** minor
- **Where:**
  - `research/runtime_contracts_paper/PRIOR_ART_POSITIONING.md:18,76`
  - `research/runtime_contracts_paper/RELATED_WORK_DRAFT.md:26`
  - `research/runtime_contracts_paper/prior_art_matrix.md:18,43`
  - `research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md:24`
- **Finding:** Same drift as F-01 but in prior-art / related-work docs.
  These files were not in any Phase 2 batch and still treat "sensitive
  user-owned data/state" as the load-bearing setting language. D-FRAME-
  012 dropped that phrasing from the title; D-FRAME-001 reframed the
  setting to "bounded agent operation." Prior-art docs are paper-
  facing artifacts that a reviewer might inspect; alignment here
  matters more than in maintainer-only planning files.
- **Suggested fix:** Single targeted sweep replacing "sensitive user-
  owned data/state" with the D-FRAME-001 phrasing. Can fold into the
  same batch-7 / pre-pilot pass as F-02.
- **Provenance check:** D-FRAME-001 + D-FRAME-012 in
  `framing_v2/CONVERGED.md`.

### F-AUDIT-PHASE2-05 — project/FRAME.md cold-start-reading list puts CONVERGED.md fourth, not first

- **Severity:** nit
- **Where:** `project/FRAME.md:138-154` "Cold-Start Reading Rule":
  1. `project/FRAME.md`
  2. `project/DECISIONS.md`
  3. `project/OPERATING_MODEL.md`
  4. `../research/runtime_contracts_paper/framing_v2/CONVERGED.md`
  5. `AGENTS.md`
  ...
- **Finding:** The audit prompt §1 reads "cold-start file ordering:
  framing_v2/CONVERGED.md is FIRST in the cold-start reading order in
  AGENTS.md, CLAUDE.md, and project/FRAME.md." AGENTS.md and CLAUDE.md
  both put CONVERGED.md first; project/FRAME.md does not. There is a
  legitimate reading of "project-first → paper-frame second" for a
  project-rooted FRAME doc, and the same file *does* put CONVERGED.md
  first in its "Paper Source-Of-Truth Order" block (line 121-127). But
  the literal cold-start reading list does not match the AGENTS.md /
  CLAUDE.md shape. This is the kind of minor inconsistency a fresh
  agent might trip on; it's nit-level because both orderings are
  internally defensible.
- **Suggested fix:** Either (a) reorder the cold-start list to put
  `CONVERGED.md` first, matching AGENTS.md and CLAUDE.md, or (b) add an
  explicit note that project-rooted readers may start with
  project/FRAME.md and resolve paper-framing questions via the source-
  of-truth block. Option (a) is cleaner.
- **Provenance check:** `AGENTS.md:55-66`, `CLAUDE.md:21-32`,
  `project/FRAME.md:121-154`.

## Internal consistency report

| Invariant | Status | Notes |
|---|---|---|
| Title (D-FRAME-016) | OK | Identical "Deterministic Software Contracts as Trusted Monitors in AI Control Protocols" in PAPER_FRAME, CLAIM_LADDER, RESEARCH_EVAL_STRATEGY, PROJECT_EXECUTION_PLAN, BASELINES_AND_ABLATIONS_PLAN, HAI_PAPER_READINESS_EXECUTION, WORK_PACKETS, README, AGENTS.md, CLAUDE.md, project/FRAME, DECISIONS, OPERATING_MODEL, HYPOTHESES, current_system_state, batch-6 supersession headers. |
| Venue (D-FRAME-008) | OK | "NeurIPS 2027 main conference, May 2027 deadline" consistent across 24 active docs. |
| Threat model (D-FRAME-003) | OK | "Capability-failure + targeted adversarial layer (50 trajectories, 4 attack types + adaptive-vs-DRG-0)" consistent in PAPER_FRAME, RESEARCH_EVAL_STRATEGY, CLAIM_LADDER, PROJECT_EXECUTION_PLAN, OPERATING_MODEL, ROADMAP, DECISIONS. No "no red-team" / "pure capability-failure" residuals as current framing. |
| Mechanism inventory (D-FRAME-017) | OK with 1 nit (F-03) | M4-M8 + M9-TX consistent everywhere except SCAFFOLD_VIEW.md (M8 still named "audit chain"). M8 = "audit evidence emission" + M9-TX = transaction integrity held-constant non-ablatable confirmed in all 7 paper-planning files + AGENTS.md + benchmark spec files. |
| Model roster (D-FRAME-020) | OK | 6 Houdinis + 3 Guards consistent in PAPER_FRAME, RESEARCH_EVAL_STRATEGY, PROJECT_EXECUTION_PLAN, DECISIONS. Haiku 3.5 retired pilot-only + Sonnet 4 retirement 2026-06-15 + successor names (`claude-haiku-4-5-20251001`, `claude-sonnet-4-6`) consistent. |
| Cost ceiling (D-FRAME-023) | OK | USD 1,500 hard ceiling consistent in PAPER_FRAME, RESEARCH_EVAL_STRATEGY, PROJECT_EXECUTION_PLAN, AGENTS.md, DECISIONS. |
| Bounded HS (D-FRAME-024) | OK | L6 only + 2-week + USD 200 caps + demote-fallback consistent in PAPER_FRAME, RESEARCH_EVAL_STRATEGY, CLAIM_LADDER, AGENTS.md. |
| ST-WAB axis (D-FRAME-026) | OK | "Runtime-mode intervention with mechanism-isolable ablation under a held-constant prompt" verbatim in PAPER_FRAME, BENCHMARK_SPEC, README of the benchmark dir, RESEARCH_EVAL_STRATEGY. |
| Cold-start ordering | OK in AGENTS.md / CLAUDE.md, nit in project/FRAME.md | See F-05. |
| Version-tag freshness | OK | AGENTS.md reaches D27 (line 417), CLAUDE.md says D1-D27 (line 33), DECISIONS.md reaches D-PROJ-023 (line 38), ORCHESTRATOR_STATE.md lists D-FRAME-001..027. |

## Terminology drift report

| Term | Active-doc residuals | Closed-marker mentions OK? |
|---|---|---|
| "workshop venue" / "workshop preprint" | None as current target. Workshop appears as (a) Trajectory A fallback path in PROJECT_EXECUTION_PLAN / DECISIONS / ROADMAP / PAPER_OUTLINE_MERGED (legitimate; locked under D-FRAME-009 pilot-failure revert), (b) "4-8 pages (workshop) vs 9 (main)" comparison in PAPER_OUTLINE_MERGED (legitimate), (c) `fine_tuned_local` "future work, not part of the workshop floor" language in baselines/README + OPERATOR_HARNESS_SPEC (legitimate; refers to the original workshop-floor scoping prior to the merge, used to delimit the future-work cell). HOWEVER, AUTONOMOUS_PROJECT_EXECUTION_PLAN, AUTONOMOUS_GATE_HANDOFF, CODEX_WORK_INSPECTION_INDEX, IMPLEMENTATION_PLAN, METHODS_SYSTEM_DRAFT still treat workshop-floor as the current target — see F-02. | Yes for legitimate cases; F-02 covers the residuals. |
| "sensitive user-owned data" / "sensitive user-owned structured data" | 1 in README (F-01), 4 in prior-art docs (F-04), 2 in project/DECISIONS.md (line 17, 69 — but both in *pre-merge* D-PROJ-002 / D-PROJ-005 context which the appended D-PROJ-018+ supersedes; legitimate historical record). | Closed-marker mentions in DECISIONS.md are OK; F-01 + F-04 are real drift. |
| "capability elicitation" / "weak-to-strong" / "A2 reframe" | 0 in active docs (verified via grep). AGENTS.md:670 mentions A2 in closed-marker context ("A2 and B1 are closed by..."). | Clean. |
| "no red-team" / "pure capability-failure" / "B1 threat model" | 0 in active docs. Unrelated "B1" labels exist in HAI v0.1.x backlog tracking; not B1-threat-model. | Clean. |
| Pre-merge title "Runtime Contracts for Local Agents Over Sensitive User-Owned Data" | 0 in active docs. | Clean. |

## Schema check

| Schema | Parses? | Critical fields present? |
|---|---|---|
| `trajectory.schema.json` | yes | T3/T4 conditional present (allOf clause 1: `if claim_tier in [T3,T4] then required: [model_roster_hash]`). `runtime_mode` enum includes 7 values incl. `no_runtime_enforcement`. `mechanism_disabled` step-type requires `mechanism`. |
| `score.schema.json` | yes | `claim_tier` in top-level required (verified). `scorer_config_hash`, `manifest_version`, `runtime_mode`, `model_class` all required. |
| `task.schema.json` | yes | `load_bearing_mechanisms` description explicitly excludes M1-M3 (line 121); 7-value runtime_modes_in_scope enum present (line 145). |
| `operator_action.schema.json` | yes | const `governed_agent_bench.operator_action.v1`; not gated by Phase 2. |
| `model_roster.schema.json` | yes | Parses cleanly. |

Schema-contracts test: **15 / 15 passed** (`uv run pytest
benchmark/verification/tests/test_governed_agent_bench_schema_contracts.py -q`,
0.15s).

## Audit-findings spot-check

Sampled 4 of 20 F-CDX-RFR-R1-NN closure claims against the actual cited
files:

- **F-CDX-RFR-R1-04** ("`no_runtime` misnamed"): closure cites
  `runtime_mode` enum using `no_runtime_enforcement` not `no_runtime`,
  and task.schema.json `load_bearing_mechanisms` description noting
  M1-M3 are not part of the enum. Verified: enum value present at
  `task.schema.json:145`; M1-M3 exclusion note present at line 121.
  **Closure verified.**
- **F-CDX-RFR-R1-06** ("predeclared thresholds not enforced"): closure
  cites `claim_tier` required at top level + T3/T4 conditional on
  `model_roster_hash`. Verified: `score.schema.json` required list
  includes `claim_tier`; trajectory.schema.json allOf clause 1 is the
  T3/T4 conditional. 15/15 tests pass. **Closure verified.**
- **F-CDX-RFR-R1-10** ("M5 + M6 not independently meaningful"): closure
  cites `HAI_INVOCATION_CONTEXT` discipline in OPERATOR_HARNESS_SPEC.
  Verified: `HAI_INVOCATION_CONTEXT` mentioned at line 153 of the spec.
  **Closure verified.**
- **F-CDX-RFR-R1-19** ("M8 audit-chain ignores transaction integrity"):
  closure cites D-FRAME-017 rename to "audit evidence emission" + M9-TX
  introduction. Verified: PAPER_FRAME, RESEARCH_EVAL_STRATEGY,
  CLAIM_LADDER, BASELINES_AND_ABLATIONS_PLAN all use the new naming
  with M9-TX called out as held-constant. SCAFFOLD_VIEW.md is the lone
  exception (F-AUDIT-PHASE2-03). **Closure substantially verified; one
  outlier flagged separately.**

## Stale-test status

`project/tests/test_project_reframe_docs_alignment.py`:
- Total: **6 pass, 2 fail**.
- Failures: `test_research_frame_content_is_pinned_on_primary_surfaces`
  and `test_hai_paper_readiness_is_the_active_runtime_planning_label`.
- Both failures are for the documented stale-assertion reason: the
  tests assert "HAI Paper-Readiness Engineering" appears in
  `PROJECT_EXECUTION_PLAN.md`, which is now structured around the
  merged-paper trajectory (D-FRAME-009) rather than the older HAI
  paper-readiness label. Failure mode is pure string-mismatch, not a
  regression. **Match documented stale-assertion shape: yes.**
- Recommendation: update or retire these two test bodies in pre-pilot
  cleanup; not blocking Phase 2.

## What the repo got right

- **Title propagation is clean.** Verified in 24 active docs + the 4
  batch-6 supersession headers. Identical 11-word form everywhere.
- **Mechanism inventory is uniform in the load-bearing surfaces.** All
  paper-planning files use M4-M8 + M9-TX with the M8 = "audit evidence
  emission" rename; the lone holdout (SCAFFOLD_VIEW.md) is a benchmark-
  internal doc, not a paper surface.
- **Schemas are tight.** `claim_tier` is top-level required in score;
  T3/T4 conditional on `model_roster_hash` is present in trajectory;
  M1-M3 explicitly excluded from the mechanism enum in task.schema.json.
  15/15 schema-contract tests pass.
- **Audit-findings closure is real.** Spot-checked 4 of 20 closure
  annotations; all four trace to verifiable file evidence. The closure
  batch is not paper-vapor.
- **Cold-start surface is correctly ordered in the two operating-
  contract files.** AGENTS.md and CLAUDE.md both put CONVERGED.md
  first; this is the surface a fresh AI agent reads on session start.

## Carry-over (post-Phase-2)

Items that should land in pre-pilot execution work, not blocking Phase
2 closure:

1. **Batch-7-or-pre-pilot:** F-AUDIT-PHASE2-02 + F-AUDIT-PHASE2-04
   workshop-floor + "sensitive user-owned data" sweep across
   `AUTONOMOUS_PROJECT_EXECUTION_PLAN.md`, `AUTONOMOUS_GATE_HANDOFF.md`,
   `CODEX_WORK_INSPECTION_INDEX.md`, `IMPLEMENTATION_PLAN.md`,
   `METHODS_SYSTEM_DRAFT.md`, `PRIOR_ART_POSITIONING.md`,
   `RELATED_WORK_DRAFT.md`, `prior_art_matrix.md`. Lightweight
   supersession header per file, or targeted rewrite. Per-file token
   cost is small; the question is whether to header-supersede or
   rewrite.
2. **One-line edits:** F-AUDIT-PHASE2-01 (README phrasing) +
   F-AUDIT-PHASE2-03 (SCAFFOLD_VIEW M8 rename + M9-TX bullet) +
   F-AUDIT-PHASE2-05 (project/FRAME.md cold-start reorder). All three
   are < 20-line diffs.
3. **Test cleanup:** retire or update the 2 failing assertions in
   `project/tests/test_project_reframe_docs_alignment.py`. Not blocking;
   they fail for the right reason.
4. **From F-CDX-RFR-R1 closure annotations (already noted there):**
   commit `benchmark/governed_agent_bench/prompts/deployment_full_v1.md`,
   `scorer_config.paper_v1.json`, `model_roster.md` with frozen
   roster + pricing snapshot, and hermetic-mode resolver E2E
   validation before §7.5 paper-claim runs. Pre-pilot work, not Phase 2.
5. **Work-packet template completeness pass** (F-CDX-RFR-R1-14/15
   carry-overs from the closure annotations).

These five items are doc-alignment polish + paper-claim-run
prerequisites. None of them are paper-§-level. None of them change a
D-FRAME-NNN decision. None of them change the schemas, scorer, harness,
or claim ladder.

Phase 2 closes clean modulo these annotations.
