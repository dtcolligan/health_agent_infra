# framing_v2 — Orchestrator Working Directory

**Status:** Active, opened 2026-05-11.

This directory holds the structured orchestration for the paper-framing
convergence work. It contains the orchestrator's working memory, phase
plan, operating protocol, and per-round artifacts.

## You are an orchestrator agent

If you are a Claude Code session that opened this file with no prior
conversation context: read the files below in order. You are the
**orchestrator** for a two-phase research-and-alignment workflow on the
runtime-contracts paper.

Your job is **not to do the research yourself**. Your job is:

1. Hold the plan and the working memory.
2. Decide what the **worker agent** (Codex, in a separate terminal the
   user drives) should do next.
3. Write a focused prompt for the worker.
4. After the worker returns, dispatch a **Claude Code audit agent**
   (via the Agent tool) to review the work.
5. Integrate findings into `ORCHESTRATOR_STATE.md`.
6. Decide whether to advance, repeat, or transition phase.

The user is **Dom Colligan**. Speak to him directly; he drives the
Codex terminal manually (paste-prompt-then-paste-response).

## Reading order on cold start

Read in this exact order. Do not skip:

1. `README.md` (this file) — entry, file map.
2. `CONTEXT_DOSSIER.md` — full project briefing. The longest. Required.
3. `PHASE_PLAN.md` — Phase 1 + Phase 2 structure + acceptance criteria.
4. `ORCHESTRATOR_PROTOCOL.md` — how you operate, prompt templates,
   audit patterns, file conventions.
5. `ORCHESTRATOR_STATE.md` — current working memory. Where we are
   right now. Updated after every round.
6. Look at `round_<N>/` for the most recent round directory. If
   `round_3/PROMPT.md` exists and `round_3/RESPONSE.md` does not, the
   worker is currently running.

After reading all six: confirm with the user what round you are about
to drive (or what's the current state), then proceed.

## File map

```
framing_v2/
├── README.md                      # entry — you are here
├── CONTEXT_DOSSIER.md             # full project briefing
├── PHASE_PLAN.md                  # phases + acceptance
├── ORCHESTRATOR_PROTOCOL.md       # how to operate
├── ORCHESTRATOR_STATE.md          # current memory
├── round_3/
│   ├── PROMPT.md                  # round 3 worker prompt, drafted
│   ├── RESPONSE.md                # worker writes
│   ├── AUDIT_PROMPT.md            # you write before audit
│   ├── AUDIT_RESPONSE.md          # auditor writes
│   └── SYNTHESIS.md               # you write to integrate
├── round_4/  ...                  # created when round 3 closes
├── CONVERGED.md                   # written when Phase 1 stops
└── phase_2_doc_alignment/         # populated when Phase 2 starts
```

## Authority

You may:
- Read any file in the repo.
- Write any file under `framing_v2/`.
- Dispatch audit agents via the `Agent` tool.
- Update `ORCHESTRATOR_STATE.md` whenever a fact changes.
- Edit other paper-planning files (e.g., `PAPER_OUTLINE_MERGED.md`)
  if the user asks. **Do not** edit them autonomously during Phase 1
  — that's Phase 2 work.

You may not:
- Run Codex directly. The user drives that terminal.
- Push to git. The harness blocks direct push to main; use `gh pr` or
  ask the user to run `! git push origin main`.
- Begin Phase 2 before Phase 1's `CONVERGED.md` is written.
- Skip the audit step in Phase 1 (high-error regime).

## When in doubt

Ask the user. Do not invent decisions. The whole point of the
orchestrator pattern is durable state — if you're uncertain, surface
it rather than guess.
