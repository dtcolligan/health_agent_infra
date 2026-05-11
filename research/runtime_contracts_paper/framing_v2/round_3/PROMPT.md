# Round 3 Worker Prompt — Research

**Drafted:** 2026-05-11
**Worker:** Codex via `/goal`
**Target:** Close O-FRAME-001, O-FRAME-002, O-FRAME-003, O-FRAME-004

---

## Identity

You are Codex, operating in `/goal` mode for an extended research
session. You are the worker agent for the runtime-contracts paper
framing v2 orchestration. The orchestrator (Claude Code) wrote this
prompt. Take your time; depth over speed.

## Project briefing

The user is publishing a paper on **deterministic software contracts
as trusted monitors in AI control protocols for bounded agent
operation**. Target venue: NeurIPS 2027 main conference, May 2027
deadline. The paper merges what was previously paper 1 (runtime
contract architecture + GovernedAgentBench) with paper 2 (Engels et
al. Backdoor Code extension).

Locked framing decisions:

- **Headline framing:** "A deterministic software contract that
  operationalizes a safety spec as the trusted monitor in an AI
  control protocol for bounded agent operation."
- **Lineage anchor:** Triple-anchor — AI control protocols (Greenblatt
  et al. 2024), safety specs (OpenAI Model Spec, Anthropic Model Spec
  Midtraining, Deliberative Alignment), LLM-monitor baselines
  (Constitutional Classifiers, Hierarchical Summarization).
- **Threat model:** Capability-failure + targeted adversarial layer
  (50 trajectories across 4 attack types).
- **Headline empirical:** Engels et al. 2025 (arXiv:2504.18530)
  Backdoor Code game; deterministic runtime as Guard at general
  Elo = 0.
- **Direct competitor (must contrast explicitly):** Anthropic's
  Hierarchical Summarization (Feb 2025).
- **Closest published benchmark prior:** ST-WebAgentBench (Levy
  et al., ICML 2025, arXiv:2410.06703).

Two earlier rounds of research already closed most framing decisions.
This round closes the remaining four high-priority decisions.

## Required reading

Read these before answering. Verify on disk where the question
concerns repo files.

1. `research/runtime_contracts_paper/framing_v2/CONTEXT_DOSSIER.md` —
   full project briefing.
2. `research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`
   — current decisions, open questions.
3. `research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md` — the
   merged paper outline; 4 title candidates listed.
4. `research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response.md`
   — specifically F-CDX-RFR-R1-08, F-CDX-RFR-R1-09, F-CDX-RFR-R1-10
   (mechanism inventory findings).
5. For mechanism question:
   - `research/runtime_contracts_paper/MECHANISM_INVENTORY.md`
   - `hai/src/health_agent_infra/core/validate.py` (lines 105-256,
     352-439)
   - `hai/src/health_agent_infra/core/writeback/proposal.py`
     (lines 121-270)
   - `hai/src/health_agent_infra/cli/handlers/intent.py` (lines
     180-246)
   - `hai/src/health_agent_infra/cli/handlers/target.py` (lines
     168-295)
   - `hai/src/health_agent_infra/cli/handlers/intake.py` (line
     1184-1189)
   - `hai/src/health_agent_infra/cli/__init__.py` (parser entries
     around lines 1508-2323)

---

## Questions for this round

### Q1 — Title finalization (closes O-FRAME-001)

The merged paper outline lists four title candidates:

- (a) *Deterministic Runtime Contracts as Trusted Monitors: A
  Control-Protocol Framework and Scaling-Laws Result for Bounded
  Agent Operation*
- (b) *Software Contracts as Trusted Overseers: Scaling Laws for
  Deterministic Agent Governance*
- (c) *Bounded Agents, Trusted Runtimes: A Control-Protocol
  Framework for Software-Side Safety*
- (d) *Beyond LLM Monitors: Deterministic Software Contracts as the
  Trusted Side of AI Control Protocols*

**Task:**

1. Survey titles of accepted papers at NeurIPS 2024, NeurIPS 2025,
   ICLR 2025 in the AI safety / agent safety / AI control space.
   Find 10-15 representative titles.
2. Identify the conventions: noun-phrase headline + colon +
   descriptive subtitle? Or single descriptive phrase? Or
   question-form? Length? Use of "Towards"?
3. Evaluate the four candidates against those conventions: which
   reads as a NeurIPS-main-conference title vs a workshop title vs a
   pre-print?
4. Identify the strongest single critique of each candidate. (e.g.,
   "(a) is too long for NeurIPS template", "(b) hides the control
   contribution", etc.)
5. Recommend the strongest candidate OR propose a fifth title that
   reads more cleanly. The recommended title must:
   - Foreground "deterministic" or "software" (the novel substrate
     claim).
   - Foreground "control" or "trusted monitor" (the lineage anchor).
   - Be ≤ 14 words.
   - Survive being scanned in a NeurIPS proceedings index.

**Deliverable:** A specific recommendation with reasoning. If you
recommend a fifth title, draft it and explain why it beats the four.

### Q2 — Mechanism inventory truth audit (closes O-FRAME-002)

The runtime-first reframe audit
(`codex_runtime_first_reframe_audit_response.md`) flagged three
findings that may break the paper's mechanism-isolable ablation
methodology:

- **F-CDX-RFR-R1-08**: M7 (refusal-in-code) is not purely aspirational
  — HAI already has runtime validators that reject banned clinical
  tokens.
- **F-CDX-RFR-R1-09**: M5 (`agent_safe`) is not a general runtime
  enforcement mechanism — enforcement is concentrated in W57
  intent/target commit gates; other commands trust the manifest.
- **F-CDX-RFR-R1-10**: M5 and M6 (proposal gate) are not independently
  meaningful on the write path — they're functionally entangled
  through W57 user-gated commits.

**Task:**

1. Read the cited HAI source files. Verify each finding empirically
   against the actual code. Do not trust the audit response without
   verification — confirm or contradict each.
2. For each mechanism M4-M8, answer:
   - Is there an actual seam in the code where this mechanism can be
     toggled off independently of the others? Cite the seam (file +
     line range).
   - If not, what's the smallest set of co-toggleable mechanisms that
     is empirically separable?
   - If M5 and M6 are entangled, propose merging them into a single
     "write-authority" mechanism in the paper, OR propose a concrete
     decoupling test (new code seam) that would make them
     independently ablatable.
3. Recommend a revised mechanism inventory: which mechanisms in the
   paper's ablation matrix are real, which need merging, which need
   code work before being ablatable.
4. Estimate the code-work cost (hours) for any mechanisms that need
   new seams before paper experiments can run.

**Deliverable:** A revised mechanism inventory table:

| Mechanism | Currently independently toggleable? | Code seam (file:lines) | Action |
|---|---|---|---|
| M4 (validation) | ... | ... | ... |
| M5 (agent_safe) | ... | ... | ... |
| M6 (proposal gate) | ... | ... | ... |
| M7 (refusal) | ... | ... | ... |
| M8 (audit chain) | ... | ... | ... |

Plus: total code-work hours estimated to make the ablation matrix
real.

### Q3 — Engels pilot protocol design (closes O-FRAME-003)

The merged paper plan includes a 2-week pilot in July 2026
(~$30-50 USD, ~80 hours) to de-risk the merge commit. The pilot must
produce a clean enough signal to decide: commit to merged scope, or
revert to Trajectory A.

**Task:**

1. Read Engels et al. 2025 ("Scaling Laws For Scalable Oversight,"
   arXiv:2504.18530) in detail. The full text, methodology, exact
   protocols for each of the four games (Mafia, Debate, Backdoor
   Code, Wargames).
2. Focus on **Backdoor Code** specifically — the cleanest port for
   a deterministic Guard.
3. Specify the pilot protocol exactly:
   - APPS sample selection: which subset of APPS samples, how
     selected, how many.
   - Houdini ladder for pilot: minimum viable set (likely 2-3 models
     spanning general-Elo range — Qwen2.5-7B, Claude Haiku, Claude
     Sonnet 4 — but justify).
   - Guards: deterministic-runtime Guard implementation specifics —
     what specific code seams are involved, what static analysis is
     done.
   - LLM Guard calibration anchor: which Engels-paper LLM Guard to
     replicate, how to replicate it exactly.
   - Prompts: exact prompt structures for Houdini and Guards.
     Templated text would be useful.
   - Decoding settings: temperature, max_tokens, sampling, seed
     handling.
   - Trial count per pair: how many samples per (Houdini × Guard)
     pair needed for statistical significance of the gap claim.
   - Metrics: domain Elo computation, win/loss adjudication,
     statistical tests.
4. Define the **decision rule**: what pilot result triggers commit to
   merge? What result triggers revert to Trajectory A? Be quantitative
   — e.g., "if deterministic Guard's domain Elo at general Elo = 0
   exceeds LLM Guard's domain Elo at general Elo ≤ X by ≥ Y points
   with p < 0.05, commit."

**Deliverable:** A complete pilot specification readable by Codex (or
the user) to execute in July 2026 without further design work. Include
estimated total token spend in USD.

### Q4 — Anthropic adversarial reviewer simulation (closes O-FRAME-004)

The most likely reviewers for an Anthropic-targeted AI Control paper
are aligned with: Mrinank Sharma (until Feb 2026), Ethan Perez, Buck
Shlegeris (Redwood, not Anthropic but adversarial-control adjacent),
Ryan Greenblatt (Redwood), and the Alignment Science team
generally.

**Task:**

1. For each of these researchers, find 3-5 recent papers (2024-2026)
   that show what they care about, what they critique, what they
   praise. Use their personal sites, Anthropic Alignment Science
   blog, OpenReview reviews if discoverable, and arXiv.
2. Identify the **single strongest critique** each would land against
   the current framing. Specific framings to test:
   - "Deterministic software as the trusted side of a control
     protocol" — is this a legitimate extension or a category error?
   - "Capability-failure threat model with targeted (50-trajectory)
     adversarial layer" — does this clear the bar for AI Control
     publication?
   - "Engels Backdoor Code extension at general Elo = 0" — does the
     deterministic-Guard-at-zero-Elo move read as principled or as a
     gimmick?
   - "Personal-wellness instantiation, non-clinical boundary" — does
     the bounded-domain framing strengthen or weaken the contribution
     in their eyes?
3. Identify the **strongest paper-killer critique** across all of
   them — the one most likely to land at NeurIPS 2027 review.
4. For each critique: pre-commit a rebuttal. What's the response in
   the paper itself? What's the response in author-response?
5. Identify any framing adjustment that would preempt the strongest
   critique. (e.g., "add an explicit comparison to
   AGENT_NAME's framework", or "drop X claim", or "add Y experiment").

**Deliverable:**

| Reviewer | Recent work signals | Strongest critique | Pre-committed rebuttal |
|---|---|---|---|
| Mrinank Sharma | ... | ... | ... |
| Ethan Perez | ... | ... | ... |
| Buck Shlegeris | ... | ... | ... |
| Ryan Greenblatt | ... | ... | ... |
| Generic Alignment Science | ... | ... | ... |

Plus: the single critique to preempt, and the framing adjustment (if
any) that does so.

---

## Deliverable format

Write your output to:

```
research/runtime_contracts_paper/framing_v2/round_3/RESPONSE.md
```

Structure:

```
# Round 3 Research Response

## Q1 — Title finalization
[Findings, citations, recommended title, reasoning]

## Q2 — Mechanism inventory truth audit
[Empirical verification of each finding, revised inventory table,
code-work hours estimate]

## Q3 — Engels pilot protocol design
[Complete pilot specification including decision rule]

## Q4 — Anthropic adversarial reviewer simulation
[Per-reviewer analysis, strongest critique, rebuttals, framing
adjustment recommendation]

## Summary

### Decisions this round closes
- O-FRAME-001 (title): [recommendation]
- O-FRAME-002 (mechanism inventory): [recommendation]
- O-FRAME-003 (pilot protocol): [complete spec]
- O-FRAME-004 (adversarial reviewer): [strongest critique + rebuttal]

### Decisions still open
- [list any of the above that the round couldn't close, with reasons]

### New decisions surfaced
- [anything else the round revealed needs deciding]
```

## Length and depth

Use `/goal` mode. Each question is substantive — expect 800-1500
words per question. Q3 (pilot protocol) is the longest. Q2 requires
actual code inspection — do not skip the source-file verification.

Q4 requires real research on the named researchers — do not invent.

## What NOT to do

- Do not edit any file outside `framing_v2/round_3/`.
- Do not propose decisions that contradict locked decisions in
  `CONTEXT_DOSSIER.md` §4 without flagging the conflict explicitly.
- Do not hallucinate arXiv IDs. If unsure of a citation, omit it
  and note the gap.
- Do not exceed depth on Q1 (title) at the cost of Q2-Q4 depth.

## When done

1. Save `RESPONSE.md` to the path above.
2. Notify Dom that round 3 research is complete.
3. Stop. Do not also write SYNTHESIS.md or AUDIT_RESPONSE.md — those
   are orchestrator-driven.

---

## Orchestrator notes for the fresh session

If you (orchestrator) are reading this for the first time and the
round 3 prompt has not been dispatched yet, you may revise this
prompt before handing it to Dom. If you revise:

1. Update `ORCHESTRATOR_STATE.md` "Sub-state" to note the revision.
2. Keep the four high-priority questions; do not drop them.
3. Do not add a fifth question — round size discipline matters.

If RESPONSE.md already exists when you read this, skip the dispatch
and proceed to drafting `AUDIT_PROMPT.md` per the protocol.
