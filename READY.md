# READY.md — Pickup Guide

**For:** Dom, picking up the repo on GitHub after exams (~2026-05-13).
**Written:** 2026-05-11.
**Status of the repo:** Framing closed, doc-aligned, ready for
pre-pilot execution. Three concrete actions remain before §7-§8
paper-claim runs (none take more than half a day).

---

## 60-second orientation

The repo is in a **reframed and aligned state**. The merged
NeurIPS 2027 paper is fully scoped. 27 framing decisions are
locked, schemas are tightened (15/15 tests pass), 33 docs across
paper / benchmark / project / HAI / operating lanes all carry the
locked framing.

You are not starting from a blank slate. You are starting from a
pre-pilot state with three artifacts to verify and three sweeps of
work already done that you should validate before running anything.

---

## Read in this order on pickup

1. **`research/runtime_contracts_paper/framing_v2/CONVERGED.md`** —
   one-page locked-framing summary. Title, venue, threat model,
   mechanism inventory, roster, thresholds, attack policy, paper-
   killer preempts, calendar. **Single source of truth.**

2. **`research/runtime_contracts_paper/framing_v2/ORCHESTRATION_COMPLETE.md`**
   — what was done in the framing-v2 orchestration; locked-paper-at-
   a-glance table; outstanding carry-over.

3. **`research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/COMPLETE.md`**
   — Phase 2 batch log + final-audit residuals + carry-over.

4. **`research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/FINAL_AUDIT_RESPONSE.md`**
   — what the final audit found, what was fixed inline, what was
   carried.

5. **`research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md`** —
   the canonical paper outline (315 lines, 11 sections + appendices).

6. **`AGENTS.md`** — universal operating contract. New Settled
   Decisions D19-D27 import D-FRAME-001..027 at universal-contract
   level. Framing-v2 orchestration pattern in "Patterns the cycles
   have validated."

After these 6 files, you have the complete framing in your head.

---

## What's locked

| Aspect | Value |
|---|---|
| Title | Deterministic Software Contracts as Trusted Monitors in AI Control Protocols |
| Venue | NeurIPS 2027 main conference, May 2027 deadline |
| Trajectory | Merged Paper 1 + Paper 2; paper 2 → S1 fine-tuning sequel |
| Decision gate | Engels pilot July 2026 (~$18.60 cost) |
| Threat model | Capability-failure + 50-trajectory targeted adversarial layer |
| Mechanism inventory | M4-M8 ablatable + M9-TX held constant |
| Model roster | 6 Houdinis + 3 Guards; Haiku 3.5 retired, Sonnet 4 retires 2026-06-15 |
| Cost ceiling | USD 1,500 |
| Calendar | Sonnet 4 retirement 2026-06-15 → Engels pilot July → decision gate Aug → ablations Nov → full run Feb 2027 → red-team Mar → manuscript Apr → submit May 2027 |

---

## What's still on you before pilot kickoff

### Quick wins (~ 1 hour total)

1. **Verify the drafted `model_roster.md`.** Path:
   `benchmark/governed_agent_bench/model_roster.md`. Marked
   `status: "draft"`. Walk through the 9-row table; verify every
   model ID resolves on its named provider as of pickup-date pricing;
   then `sha256sum` the file and record the hash in
   `framing_v2/ORCHESTRATOR_STATE.md` "Decisions journal" as the
   frozen roster reference.

2. **Verify the drafted `scorer_config.paper_v1.json`.** Path:
   `benchmark/governed_agent_bench/scorer_config.paper_v1.json`.
   Marked `status: "draft"`. Walk through the per-metric thresholds
   + critical-violation list; confirm they match D-FRAME-021; then
   `sha256sum` and pin the hash.

3. **Walk the existing `deployment_full_v1.md` prompt template.**
   Path: `benchmark/governed_agent_bench/prompts/deployment_full_v1.md`.
   Committed at `caad0b8` (pre-merge) but the spec is mature and
   aligned with D-FRAME-001 in spirit. Confirm it carries the
   sections you want and the 5-placeholder substitution discipline.
   No edits expected — just a read-and-confirm.

### Single time-bound thing (~ 30 min)

4. **Read arXiv:2504.18530 §4 and confirm "5 Houdini attempts per
   sample" claim.** D-FRAME-018 pilot protocol depends on this
   number. The framing-v2 audit could not verify (binary PDF was
   unrenderable). If Engels caps at a different number, update
   D-FRAME-018 attempt count in `framing_v2/ORCHESTRATOR_STATE.md`.

### Hermetic-mode E2E (~ 30-60 min)

5. **Verify hermetic-mode isolation end-to-end.** Run a small attack-
   policy trajectory in hermetic mode (HAI_STATE_DB redirected,
   HAI_BASE_DIR redirected, no network) and confirm `runtime_mode`
   guards block production-state mutations as designed. The harness
   spec at `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`
   documents the discipline; you need to verify it actually holds in
   a live run.

---

## What's deferred to Engels pilot prep proper (~July 2026)

These are not pickup-blockers but should be in your head as you
approach July:

- Materialize 60 APPS competition samples per D-FRAME-018 selection
  procedure (sha256 seed + manifest freeze).
- Implement DRG-0 six modules with frozen JSON config hash.
- Tune DRG-0 thresholds on the 10 smoke samples only, never the
  primary 60.
- Calendar binding: §7.5 cells using Sonnet 4 must complete before
  2026-06-15 OR re-anchor to `claude-sonnet-4-6` under a new
  roster hash.

---

## What's NOT in scope (do not reopen)

- **HAI runtime work** beyond `WP-RUNTIME-FIX-NNN` packets per
  D-PROJ-016 freeze.
- **A2 reframe** (capability-elicitation / weak-to-strong). Closed
  by D-FRAME-014.
- **B1 threat model** (no red-team / pure capability-failure).
  Closed by D-FRAME-015. The adversarial layer is constitutive.
- **Pre-merge paper title** ("Runtime Contracts for Local Agents
  Over Sensitive User-Owned Data") and "user-owned structured data"
  framing. Closed by D-FRAME-012/013.
- **Workshop venue** as the current target. Closed by D-FRAME-008
  (NeurIPS 2027 main); workshop is the Trajectory A fallback only.

---

## Recently-touched files (last few hours, 2026-05-11)

After Phase 2 closed, three small follow-ups landed:

- 5 paper-lane planning files got supersession headers
  (`AUTONOMOUS_PROJECT_EXECUTION_PLAN.md`, `AUTONOMOUS_GATE_HANDOFF.md`,
  `CODEX_WORK_INSPECTION_INDEX.md`, `METHODS_SYSTEM_DRAFT.md`,
  `IMPLEMENTATION_PLAN.md`).
- 4 prior-art docs got "sensitive user-owned data" → merged-framing
  string fixes (`PRIOR_ART_POSITIONING.md`, `RELATED_WORK_DRAFT.md`,
  `prior_art_matrix.md`, `IMPLEMENTATION_PLAN.md`).
- 2 stale test assertions in
  `project/tests/test_project_reframe_docs_alignment.py` updated to
  the merged framing (8/8 tests now pass).
- 3 inline final-audit fixes (README phrasing, SCAFFOLD_VIEW M8
  rename + M9-TX bullet, project/FRAME cold-start reorder).
- 2 new drafted artifacts: `model_roster.md` and
  `scorer_config.paper_v1.json` (both status: "draft" — see quick
  wins above).

All of the above are uncommitted in the worktree as of this READY.md
write. The next action is yours: review the diff, then commit + push.

---

## Suggested first commit on pickup

```bash
# After reading the framing files:
git status
git diff --stat

# Suggested commit groupings (or one bulk commit; your call):
git add research/runtime_contracts_paper/AUTONOMOUS_*.md \
        research/runtime_contracts_paper/CODEX_WORK_INSPECTION_INDEX.md \
        research/runtime_contracts_paper/METHODS_SYSTEM_DRAFT.md \
        research/runtime_contracts_paper/IMPLEMENTATION_PLAN.md
git commit -m "docs(research): mark pre-merge planning files as superseded"

git add research/runtime_contracts_paper/PRIOR_ART_POSITIONING.md \
        research/runtime_contracts_paper/RELATED_WORK_DRAFT.md \
        research/runtime_contracts_paper/prior_art_matrix.md
git commit -m "docs(research): replace pre-merge 'sensitive user-owned data' framing in prior-art docs"

git add project/tests/test_project_reframe_docs_alignment.py
git commit -m "test(project): update reframe-alignment assertions to merged-paper framing"

git add README.md benchmark/governed_agent_bench/SCAFFOLD_VIEW.md project/FRAME.md
git commit -m "docs: phase-2 final-audit inline fixes (README phrasing, SCAFFOLD_VIEW M8 rename, FRAME cold-start reorder)"

git add benchmark/governed_agent_bench/model_roster.md \
        benchmark/governed_agent_bench/scorer_config.paper_v1.json
git commit -m "feat(benchmark): draft model roster + paper-v1 scorer config (status=draft; maintainer to verify+freeze)"

git add research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response.md \
        research/runtime_contracts_paper/framing_v2/
git commit -m "docs(research): annotate F-CDX-RFR-R1 closure + add framing-v2 orchestration artifacts"

git push origin main
```

Or one bulk commit if you prefer the smaller history footprint.

---

## If something feels wrong

The repo is internally consistent on the merged framing, but the
docs include some redundancy from supersession (DRAFT_PAPER.md is
superseded by PAPER_OUTLINE_MERGED.md but body kept as provenance;
5 paper-lane files have supersession headers but full bodies
preserved). This is intentional. Don't clean it up unless you have
a reason — historical provenance protects against future framing
re-opens.

If the framing itself feels wrong: write your concern as a one-line
in `framing_v2/ORCHESTRATOR_STATE.md` "Decisions journal" with a
date. Don't silently rewrite a D-FRAME entry. Locked decisions are
durable.

If you find a real bug in the merged framing (not "I'd prefer
different wording" but "this is internally inconsistent or
factually wrong"): open a new framing-v2.1 round under
`framing_v2/round_6/PROMPT.md` and re-engage the orchestration
pattern. The pattern is in AGENTS.md "Patterns the cycles have
validated."

---

## The next substantive step

Engels pilot, July 2026. Sonnet 4 retirement 2026-06-15 means your
prep window is ~5 weeks from pickup. Use it.
