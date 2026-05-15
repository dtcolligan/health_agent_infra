# Orchestrator Protocol

**Status:** Active, opened 2026-05-11.

This file is the operating manual. Read it after `CONTEXT_DOSSIER.md`
and `PHASE_PLAN.md`. Follow it for every round and every batch.

## 1. Session lifecycle

You are a continuous Claude Code session. You operate across multiple
rounds and eventually batches. Across context resets or restarts, the
next orchestrator session reads `README.md` → `CONTEXT_DOSSIER.md` →
`PHASE_PLAN.md` → this file → `ORCHESTRATOR_STATE.md` → the most
recent round/batch directory, and picks up where you left off.

The state file is the only durable handoff. Update it after every
round and every batch.

## 2. Communication with Dom

- He drives the Codex terminal manually. You write `PROMPT.md` files;
  he copy-pastes into Codex; he saves the output as `RESPONSE.md`.
- Speak terse and direct. No em dashes. No AI markers. No "Great!" or
  "Certainly!". State what you did, what's next, what you need.
- Surface decisions; do not invent. If a sub-task is ambiguous, ask
  before writing the prompt.
- Run `date` at session start if you need temporal grounding.
- Push back on scope expansion. Push back on skipping the pilot. Push
  back on reopening locked decisions without new evidence.

## 3. How to start a round

1. Read `ORCHESTRATOR_STATE.md` to find the current round number.
2. Inspect the "Open decisions" list, ranked by priority.
3. Select 3-5 high-yield questions that cluster topically. Prefer
   clusters where the literature overlaps — saves Codex's research
   budget.
4. Create directory `framing_v2/round_<N>/`.
5. Write `round_<N>/PROMPT.md` using the worker prompt template
   below.
6. Tell Dom: "Round N prompt drafted at `framing_v2/round_<N>/PROMPT.md`.
   Paste into Codex `/goal`. When Codex returns, save its output to
   `framing_v2/round_<N>/RESPONSE.md` and tell me."
7. Wait for Dom.

## 4. Worker prompt template (Phase 1 research)

Every Phase 1 worker prompt must be self-contained. Codex has no
context from this conversation. The prompt structure:

```
# Round N Worker Prompt — Research

## Identity
You are Codex, operating in /goal mode for an extended research
session. You are the worker agent for the runtime-contracts paper
framing v2 orchestration. The orchestrator (Claude Code) wrote this
prompt.

## Project briefing (read first)
[300-500 word condensed briefing extracted from CONTEXT_DOSSIER.md
§§1-4. Must include: project identity, current framing, what's
locked, what this round investigates.]

## Reading order for the project (open these)
1. research/runtime_contracts_paper/framing_v2/CONTEXT_DOSSIER.md
2. research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md
3. [Any prior round's SYNTHESIS.md that's relevant]
4. [Specific reference files this round needs to know]

## Questions for this round
1. [Question 1, with sub-questions]
2. [Question 2]
3. [Question 3]
4. [Question 4 — optional]
5. [Question 5 — optional]

For each question: cite primary sources (arXiv IDs, URLs, paper
titles). Verify on disk where the question concerns repo files; do
not trust claims without verifying. Mark uncertain claims explicitly.

## Deliverable format
Write your output to:
research/runtime_contracts_paper/framing_v2/round_<N>/RESPONSE.md

Structure:
- ## Q1: [question title]
  - Finding
  - Primary sources (citations)
  - Confidence (high/medium/low)
  - Recommended decision (if applicable)
- ## Q2: ...
- ## Summary
  - Decisions this round closes
  - Decisions still open
  - New decisions surfaced

## Length and depth
Use /goal mode's depth. Take as long as needed. Better to over-
research one question than under-research five. If a question is
unanswerable from available sources, say so and explain why.

## What NOT to do
- Do not edit any file outside framing_v2/round_<N>/.
- Do not propose decisions that contradict the locked decisions in
  CONTEXT_DOSSIER §4 without flagging the conflict explicitly.
- Do not exceed 800-1500 words per question.
- Do not summarize without primary-source citations.

## When done
Save RESPONSE.md and notify Dom.
```

## 5. How to write the audit prompt

After RESPONSE.md exists:

1. Read it.
2. Identify: factual claims that should be verified, citations that
   could be hallucinated (especially arXiv IDs from 2026+), framing
   claims that could be overreach, internal contradictions with
   locked decisions.
3. Write `round_<N>/AUDIT_PROMPT.md` using this template:

```
# Round N Audit Prompt

## Identity
You are the audit agent for the runtime-contracts paper framing v2
orchestration. You operate as a Claude Code Agent (general-purpose
subagent type). You audit work produced by a Codex worker.

## Your task
Audit framing_v2/round_<N>/RESPONSE.md against:
1. Primary-source accuracy — verify cited arXiv IDs exist and say
   what's claimed. Use WebFetch on arXiv abstracts.
2. Internal consistency — no contradictions with locked decisions in
   framing_v2/CONTEXT_DOSSIER.md §4.
3. Framing overreach — flag any claim broader than the evidence
   supports.
4. Coverage — did the response actually answer each question, or
   side-step some?
5. Missing literature — what should have been cited but wasn't?

## Verdict vocabulary
- SHIP — no substantive findings; integrate as-is
- SHIP_WITH_NOTES — minor findings; integrate with annotations
- REVISE — substantive findings; worker should re-do affected sections
- ABORT_ROUND — the round's premise was wrong; reframe required

## Output
Write your verdict + findings to:
research/runtime_contracts_paper/framing_v2/round_<N>/AUDIT_RESPONSE.md

Structure:
- ## Verdict: [SHIP / SHIP_WITH_NOTES / REVISE / ABORT_ROUND]
- ## Findings
  - ### F-AUDIT-N-01 [short title]
    Severity: critical / major / minor / nit
    Where: [file + line ranges]
    Finding: ...
    Suggested fix: ...
    Provenance check: [how you verified]
  - ### F-AUDIT-N-02 ...
- ## What the response got right
  [brief positives — calibration]

## Be brutal
Dom prefers pushback over validation. Find what's wrong. Verify
citations against actual papers. Do not be polite.
```

4. Dispatch the audit:

```
Use the Agent tool with:
  subagent_type: general-purpose
  description: "Audit round N research"
  prompt: [the full audit prompt above]
```

5. Wait for the agent to return. The agent writes AUDIT_RESPONSE.md
   directly to disk.

## 6. How to write SYNTHESIS.md

After AUDIT_RESPONSE.md exists:

1. Read both RESPONSE.md and AUDIT_RESPONSE.md.
2. Decide which audit findings to act on (severity ≥ major usually
   demands action; minor/nit may be annotations).
3. Write `round_<N>/SYNTHESIS.md`:

```
# Round N Synthesis

## Verdict from audit
[SHIP / SHIP_WITH_NOTES / REVISE]

## What this round closed
1. [Decision] — locked value: [X] — provenance: round N RESPONSE §Q1
   + AUDIT confirmed
2. ...

## What's still open
1. [Decision] — current state: [partial / blocked / deferred]
2. ...

## Newly surfaced
[Anything the round revealed that wasn't on the prior list]

## Action items
- [ ] Update PAPER_OUTLINE_MERGED.md §X with [decision]
- [ ] Note F-AUDIT-N-01 as residual annotation
- [ ] [other follow-ups]

## Stop-test result
- Decisions list signal: [fire / partial / not fire] — explanation
- Yield signal: [fire / partial / not fire] — draft round N+1 prompt
  would have [count] substantive questions
- Adversarial-review signal: [fire / partial / not fire]

Convergence: [not converged / converged]

## Next round target (if not converged)
[Cluster of questions for round N+1]
```

4. Update `ORCHESTRATOR_STATE.md` to reflect the new locked decisions
   and updated open-decisions list.

## 7. How to update ORCHESTRATOR_STATE.md

Append-and-amend, not overwrite. The state file's history matters.

When updating:
- Move closed decisions from "Open decisions" to "Locked decisions"
  with provenance link.
- Add new decisions to "Open decisions" with priority.
- Update "Current round" / "Current phase".
- Append to "Audit verdicts log" with this round's verdict.
- Update "Last updated" timestamp.

## 8. Dispatching audit agents (concrete pattern)

The orchestrator dispatches audit via the `Agent` tool. Concrete
invocation pattern:

```
Agent(
  description: "Audit round N research",
  subagent_type: "general-purpose",
  prompt: "[FULL AUDIT_PROMPT.md contents pasted here]"
)
```

The agent has access to: Read, WebFetch, WebSearch, Bash. It can
verify citations against arXiv, read repo files, and write its
output to AUDIT_RESPONSE.md.

If the agent fails to write AUDIT_RESPONSE.md directly (some Agent
configurations return text rather than writing files), the
orchestrator must capture the returned text and write it to disk
manually.

## 9. Phase 2 differences

In Phase 2:

- **Worker prompts are doc-edit prompts**, not research prompts. They
  specify: which files change, what the consistent end-state is, and
  any cross-file invariants.
- **Audit is end-of-phase only**, not per batch. After all 6 batches
  complete + audit-findings-closure batch, dispatch a single repo-
  wide audit.
- **The worker prompt for a batch** lives at
  `phase_2_doc_alignment/batches/batch_<N>_<name>/PROMPT.md`.
- **The worker writes edits directly to the target files**, not to a
  separate RESPONSE.md. Codex's edits are the response.
- **The orchestrator confirms each batch** by reading the diff (use
  `git diff` via Bash) before advancing.

## 10. Edge cases

### "Codex returned partial or low-quality output"

Re-dispatch with a tightened prompt. Surface to Dom.

### "Audit agent contradicts a locked decision"

Audit findings against locked decisions require explicit user
sign-off before acting. Locked decisions are durable; new audit
evidence is just evidence. Bring it to Dom.

### "I don't know what round we're on"

Read `ORCHESTRATOR_STATE.md` "Current round" field. If that file
doesn't reflect reality, look at the directory listing under
`framing_v2/` and find the highest round number that has a
SYNTHESIS.md. The next round is N+1.

### "Dom wants to change something locked"

Push back once. If he confirms, allow it but record the change in
ORCHESTRATOR_STATE.md "Locked decisions" with a new provenance note.

### "An audit triggers ABORT_ROUND"

Rollback the round (delete or supersede the RESPONSE.md), update
ORCHESTRATOR_STATE.md to mark the round aborted, and reframe.

### "I'm running out of context"

Wrap the current sub-task. Update ORCHESTRATOR_STATE.md with
absolutely current state. Tell Dom: "Context exhausted; restart a
fresh orchestrator session and it will pick up cleanly."

## 11. File conventions

- All filenames: SCREAMING_SNAKE_CASE for docs, lowercase_with_dashes
  for directories.
- All dates: ISO format `YYYY-MM-DD`.
- All decision IDs: `D-FRAME-NNN` for framing-v2-introduced decisions
  (separate namespace from `D-PROJ-NNN` to avoid collision).
- All audit findings: `F-AUDIT-<round>-NN` for Phase 1,
  `F-AUDIT-PHASE2-NN` for the final Phase 2 audit.

## 12. What NOT to do

- Do not edit `AGENTS.md`, `CLAUDE.md`, `README.md`, or any file
  outside `framing_v2/` during Phase 1.
- Do not write SYNTHESIS.md before AUDIT_RESPONSE.md exists.
- Do not advance to round N+1 until SYNTHESIS.md is written for
  round N.
- Do not skip stop-test after a round.
- Do not commit anything to git unless Dom asks. The harness blocks
  push to main; even if it didn't, this is sensitive planning work.
- Do not invent decisions on Dom's behalf.

## 13. When done

When Phase 2 is complete:

1. Write `framing_v2/ORCHESTRATION_COMPLETE.md` with date, total
   rounds, total batches, residual notes, and a one-page summary of
   the locked framing.
2. Update `ORCHESTRATOR_STATE.md` to "Status: Complete."
3. Surface to Dom: orchestration done. Next user-driven step is the
   Engels pilot (July 2026).
