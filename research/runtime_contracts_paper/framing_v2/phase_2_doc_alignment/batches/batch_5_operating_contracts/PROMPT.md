# Phase 2 Batch 5 Worker Prompt — Operating Contracts

**Drafted:** 2026-05-11
**Phase:** 2 — Documentation alignment
**Batch:** 5 of 6 — Operating contracts (AGENTS.md, CLAUDE.md, README.md)
**Worker:** Codex via `/goal`
**Audit cadence:** end-of-phase only.

---

## Identity

You are Codex in `/goal` mode, executing Phase 2 batch 5 of the
runtime-contracts paper framing v2 orchestration. Phase 2 is doc-edit
work; write edits directly to target files.

## Project briefing

Phase 1 closed 2026-05-11 with 27 locked framing decisions
(D-FRAME-001..027). Batches 1-4 closed clean: paper-planning files
(batch 1), benchmark spec + schemas (batch 2), project cold-start
docs (batch 3), HAI runtime docs (batch 4, light touch).

Batch 5 propagates the locked framing into the **operating contracts**.
These three files are the highest-leverage docs in the repo:

- `AGENTS.md` is the universal operating contract every AI agent
  (Codex, Claude Code, future agents) reads on session start.
- `CLAUDE.md` imports `AGENTS.md` and adds Claude-Code-specific
  patterns.
- `README.md` is the top-level research-facing overview.

A misaligned `AGENTS.md` causes every future session to operate from
stale assumptions until the next doc-alignment cycle. Batch 5 must
land clean.

The acceptance criterion (per `PHASE_PLAN.md` §3 batch 5):

> Terminology matches Phase 1 (control protocol + safety spec
> vocabulary); decision records updated; cycle-pattern signposts
> updated if Phase 2 changes the cycle vocabulary.

## Required reading (in this order)

1. `research/runtime_contracts_paper/framing_v2/CONVERGED.md` — locked
   framing summary + 27 decisions.
2. `research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`
   — full decisions table.
3. `research/runtime_contracts_paper/framing_v2/PHASE_PLAN.md` and
   `ORCHESTRATOR_PROTOCOL.md` — framing-v2 orchestration shape
   (worker/auditor/orchestrator roles, batch cadence).
4. `research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/batches/batch_3_project_cold_start/EDITS_SUMMARY.md`
   — what changed in `project/` (D-PROJ-018..023 references should
   carry forward into AGENTS.md "Settled Decisions").
5. Current state of all 3 target files (read each before editing).

## Target files (3)

1. **`AGENTS.md`** (623 lines, **revise + append**) — the universal
   operating contract. Highest-leverage file.

   Required updates:

   - **Top-of-file orientation section** (read-this-first): add
     `framing_v2/CONVERGED.md` as the FIRST file in the cold-start
     reading order. Currently the orientation likely lists
     `project/FRAME.md`, `project/DECISIONS.md`, etc. Insert
     CONVERGED.md above those.
   - **"What This Project Is" section**: update the paper title to
     the locked D-FRAME-016 title. Update the active objective
     statement to reflect the merged paper + benchmark direction.
   - **"Settled Decisions" section**: add new entries D19-D27
     mapping to D-FRAME-016 through D-FRAME-027 (or use a
     consolidated form: "D19 — Framing v2 orchestration locked all
     paper-framing decisions 2026-05-11; canonical source
     `framing_v2/CONVERGED.md`; do not reopen D-FRAME-001..027
     without a new framing-v2-class cycle"). Keep existing D1-D18
     entries; append D19+. If D19+ already exists as a different
     decision, use the next free number.
   - **"Do Not Do" section**: ensure the list reflects locked
     decisions — A2 reframe closed (D-FRAME-014), B1 (no red-team)
     closed (D-FRAME-015), HAI freeze (D-PROJ-016), no automatic
     threshold mutation, etc. If any "Do Not Do" entry was
     pre-merge and is now superseded, update it.
   - **"Patterns the cycles have validated" section**: add the
     framing-v2 orchestration pattern as a validated cycle pattern:
     two-phase (research convergence + documentation alignment),
     worker-auditor-orchestrator triad, escape valve via three
     consecutive SHIP_WITH_NOTES with zero paper-§-level findings,
     batch dispatch in Phase 2 with end-of-phase audit only.
   - **"Cycle pattern signposts" / file conventions**: add the
     `framing_v2/` directory shape (CONVERGED.md, ORCHESTRATOR_STATE.md,
     PHASE_PLAN.md, ORCHESTRATOR_PROTOCOL.md, round_*/, phase_2_doc_alignment/).
   - **Title sweep**: any reference to the paper by title must use
     the D-FRAME-016 locked title.
   - **Venue sweep**: NeurIPS 2027 main conference. NOT workshop.
   - **Mechanism inventory references**: if AGENTS.md describes the
     contract architecture, the M-numbering must match D-FRAME-017
     (M4-M8 + M9-TX held constant).

2. **`CLAUDE.md`** (186 lines, **light revise**) — Claude-Code-
   specific operational layer over AGENTS.md.

   Required updates:

   - **Session-start orientation section** (the bulleted list of
     files to read on cold start): add `framing_v2/CONVERGED.md`
     as the first item.
   - **References to AGENTS.md "Settled Decisions"**: if CLAUDE.md
     names specific D-numbers, ensure they still match AGENTS.md
     after batch 5 D19+ additions.
   - **Cycle pattern signposts**: if CLAUDE.md describes the
     release-cycle pattern, note that the framing-v2 research-lane
     pattern is distinct from the HAI-release-cycle pattern (HAI
     is frozen per D-PROJ-016, so the HAI-release-cycle pattern
     is dormant; the framing-v2 pattern is the active research
     pattern).
   - Do NOT rewrite Claude-Code-specific operational content
     (slash-command behavior, plan-mode triggers, release toolchain
     reference) — that's specific to Claude Code usage discipline,
     not paper framing.

3. **`README.md`** (185 lines, **revise**) — top-level research-
   facing overview.

   Required updates:

   - **Title and one-paragraph pitch**: replace any pre-merge
     framing with the merged-paper title (D-FRAME-016) + headline
     framing (D-FRAME-001). The repo is the active artifact for
     "Deterministic Software Contracts as Trusted Monitors in AI
     Control Protocols," with HAI as the reference runtime and
     GovernedAgentBench as the benchmark.
   - **Status section**: state Phase 1 closed 2026-05-11; Phase 2
     in progress; NeurIPS 2027 submission target.
   - **Repo orientation**: name `framing_v2/CONVERGED.md` as the
     canonical paper-framing source-of-truth.
   - **Pitch language**: should not over-claim. The paper is in
     pre-pilot stage (Engels pilot July 2026 is the decision gate);
     the runtime contract is implemented in HAI v0.2.0; the
     benchmark is pre-measurement-ready. Do not claim "we have
     results" — claim "we have an architecture + benchmark + pilot
     protocol."

## Cross-file invariants

### Title (D-FRAME-016)
> Deterministic Software Contracts as Trusted Monitors in AI Control
> Protocols

Present in AGENTS.md, CLAUDE.md (via AGENTS.md import + own
references), and README.md.

### Venue (D-FRAME-008)
NeurIPS 2027 main conference, May 2027 deadline.

### Locked-decisions source-of-truth ordering
1. `framing_v2/CONVERGED.md`
2. `framing_v2/ORCHESTRATOR_STATE.md`
3. `project/DECISIONS.md` (D-PROJ-018..023 import the framing-v2
   locks at project level)
4. `AGENTS.md` "Settled Decisions" (D19+ import D-FRAME-001..027
   at universal-contract level)
5. `PAPER_OUTLINE_MERGED.md` (canonical paper outline)
6. Derivative paper-planning files

### Cycle-pattern vocabulary
- **HAI release cycle pattern** (PLAN.md → D14 plan audit → Phase 0
  bug-hunt → implementation → IR rounds → ship). **DORMANT** — HAI
  is frozen per D-PROJ-016.
- **Framing-v2 research-lane pattern** (Phase 1 research + Phase 2
  doc alignment; worker-auditor-orchestrator triad; round_N
  artifacts in Phase 1; batch_N artifacts in Phase 2; escape valve
  via three consecutive SHIP_WITH_NOTES with zero paper-§-level
  findings). **ACTIVE.**

Both patterns can coexist in AGENTS.md; HAI cycle pattern is
historical/dormant, framing-v2 is current.

### Closed reframes
A2 (capability-elicitation) and B1 (no red-team) closed and must not
appear as current claims. Closed-marker mentions in the decisions
log are acceptable.

### HAI freeze (D-PROJ-016)
HAI is frozen as a product. AGENTS.md's "Do Not Do" list should
include "Do not reopen HAI freeze for non-paper-critical work" or
equivalent.

## Deliverable format

**Write your edits directly to the 3 target files.** Do NOT write a
separate RESPONSE.md.

After all 3 files are updated, write a summary at:

```
research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/batches/batch_5_operating_contracts/EDITS_SUMMARY.md
```

Structure:

```markdown
# Batch 5 Edits Summary

## Files touched
| File | Edit type | Lines changed (rough) | Notes |

## AGENTS.md additions
- New "Settled Decisions" entries: D19, D20, ... (or consolidated D19)
- Updated "What This Project Is" pitch?
- "Patterns the cycles have validated" — framing-v2 pattern added?
- "Cycle pattern signposts" — framing-v2 directory shape added?
- "Do Not Do" — A2/B1 closed-reframe entries updated?
- Title + venue + mechanism inventory consistency?

## CLAUDE.md updates
- Session-start orientation — CONVERGED.md added as first item?
- AGENTS.md cross-references still aligned post-D19+ additions?
- HAI vs framing-v2 cycle pattern distinction made?

## README.md updates
- Title + headline framing replaced?
- Status section reflects Phase 1 closed / Phase 2 in progress?
- Pitch language conservative (no "we have results" overclaim)?

## Cycle-pattern vocabulary
- Both HAI release cycle pattern (dormant) and framing-v2 pattern
  (active) named correctly?

## Cold-start file ordering check
List the cold-start reading order from AGENTS.md and CLAUDE.md;
verify CONVERGED.md is first.

## Carry-over for batch 6 + audit-findings-closure
[anything noticed]

## Open issues
[anything you couldn't resolve cleanly]
```

## What NOT to do

- Do not edit files outside the 3 named targets. If a cross-batch
  issue surfaces (e.g., a HAI doc reference is now stale), flag in
  EDITS_SUMMARY.md carry-over for batch 6 or the audit-findings-
  closure batch.
- Do not rewrite Claude-Code-specific operational discipline in
  CLAUDE.md (slash-command behavior, plan-mode triggers, common
  commands). Only update paper-framing references and cycle-pattern
  signposts.
- Do not delete prior "Settled Decisions" D1-D18 entries from
  AGENTS.md. Append D19+ only.
- Do not invent new D-FRAME or D-PROJ numbers — those are locked
  in `framing_v2/CONVERGED.md` and `project/DECISIONS.md`.
- Do not reopen D-FRAME-014 / D-FRAME-015 / D-PROJ-016.
- Do not write a separate RESPONSE.md.

## When done

1. All 3 target files updated.
2. `EDITS_SUMMARY.md` written.
3. Notify Dom: "Phase 2 batch 5 complete. Files updated, summary at
   `framing_v2/phase_2_doc_alignment/batches/batch_5_operating_contracts/EDITS_SUMMARY.md`."
4. Stop. Do not start batch 6.

---

## Orchestrator notes

After Codex returns, the orchestrator inspects via:

```bash
git diff AGENTS.md CLAUDE.md README.md
```

and runs a title + venue + cold-start-ordering sweep:

```bash
rg -n "Deterministic Software Contracts as Trusted" AGENTS.md CLAUDE.md README.md
rg -n "NeurIPS 2027" AGENTS.md CLAUDE.md README.md
rg -n "framing_v2/CONVERGED.md" AGENTS.md CLAUDE.md README.md
```

before advancing to batch 6 (historical provenance, mark superseded).
