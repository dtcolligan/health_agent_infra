# Round 5 Worker Prompt — Research

**Drafted:** 2026-05-11
**Worker:** Codex via `/goal`
**Target:** Close O-FRAME-005 + O-FRAME-010 (merged), O-FRAME-006,
O-FRAME-011 (paper-positioning + scope-cleanup cluster)
**Likely terminal round** for Phase 1 research convergence.

---

## Identity

You are Codex, operating in `/goal` mode for an extended research
session. You are the worker agent for the runtime-contracts paper
framing v2 orchestration. The orchestrator (Claude Code) wrote this
prompt. Take your time; depth over speed.

This is the projected terminal research round of Phase 1. The
orchestrator's stop test requires three signals — two are partial or
marginal, one (decisions list) requires this round to close. If this
round returns SHIP_WITH_NOTES with no new paper-§-level findings,
Phase 1 closes by yield-exhaustion escape valve and moves to Phase 2
documentation alignment.

## Project briefing

The paper is **"Deterministic Software Contracts as Trusted Monitors
in AI Control Protocols"** (D-FRAME-016). Target venue: NeurIPS 2027
main conference, May 2027 deadline. The paper merges paper 1 (runtime
contract + GovernedAgentBench) with paper 2 (Engels Backdoor Code
extension as §7.5).

**Rounds 3 + 4 closed seven decisions.** Locked outcomes you must
not reopen (full table in `framing_v2/ORCHESTRATOR_STATE.md`):

- **D-FRAME-016 title.** "Deterministic Software Contracts as Trusted
  Monitors in AI Control Protocols."
- **D-FRAME-017 mechanism inventory.** M4-M8 ablatable; M7 narrow to
  clinical-boundary surfaces; M8 renamed "audit evidence emission";
  M9-TX held constant non-ablatable.
- **D-FRAME-018 Engels pilot protocol.** 60 APPS competition samples,
  3 Houdinis, DRG-0 module breakdown, 6-clause commit rule, ~$18.60.
- **D-FRAME-019 two paper-killer critiques.** Framing-overclaim
  (rhetorical preempt: "trusted-monitor substrate for bounded AI
  control protocols") and Greenblatt DRG-artifacts (empirical
  preempt: pre-registered DRG inputs + ablations + FP rates +
  adaptive attack).
- **D-FRAME-020 model roster.** 6 Houdinis + 3 Guards; Haiku 3.5
  retired (pilot-only), Sonnet 4 retires 2026-06-15.
- **D-FRAME-021 thresholds.** AND-pass rule + 7 critical violations
  + per-metric thresholds.
- **D-FRAME-022 attack policy.** 50 trajectories across 5 attack
  types including adaptive-vs-DRG-0 (18 trajectories).
- **D-FRAME-023 cost ceiling.** USD 1,500 hard ceiling.

**Round 5 targets four remaining medium opens, clustered into three
questions.**

These are paper-positioning and scope-cleanup decisions. They affect
§2 (related work), §7.6 (HS head-to-head), Appendix E (cross-domain
sketch), and the paper-2 sequel framing. None requires new
empirical work.

## Required reading

1. `research/runtime_contracts_paper/framing_v2/CONTEXT_DOSSIER.md`
   — full project briefing.
2. `research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`
   — current locked decisions D-FRAME-001..023; remaining opens.
3. `research/runtime_contracts_paper/framing_v2/round_3/SYNTHESIS.md`
   and `round_4/SYNTHESIS.md` — round closures + action items.
4. `research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md` — §2.3
   (HS in related work), §7.6 (HS head-to-head), §2.4 (agent safety
   benchmarks incl. ST-WebAgentBench), Appendix E (cross-domain
   sketch).

For Q1 (HS + ST-WebAgentBench):

- **Hierarchical Summarization** (Anthropic Feb 2025):
  `https://alignment.anthropic.com/2025/summarization-for-monitoring/`.
  Confirmed in round 3 audit. Read the methodology section.
- **ST-WebAgentBench** (Levy et al., ICML 2025): arXiv:2410.06703.

For Q2 (coding-agent slice):

- Search the repo for any existing coding-agent material:
  - `research/runtime_contracts_paper/WORK_PACKETS.md`
  - `research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md`
  - `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`
- Engels §7.5 already uses APPS coding samples but as Houdini-Guard
  task, not as "coding agent operates a runtime."
- No coding-agent reference runtime exists in the HAI repo. HAI is
  frozen as personal-wellness instantiation per D-PROJ-016.

For Q3 (paper 2 sketch precision):

- **D-FRAME-010 locked paper 2 redirect.** S1 fine-tuning lineage
  (RBR + Deliberative Alignment) at ICML 2028 or NeurIPS 2028.
- **RBR** (Rule-Based Rewards for Language Model Safety): NeurIPS
  2024 (already cited in round 3 Q1 title-survey table).
- **Deliberative Alignment** (OpenAI): arXiv:2412.16339.
- **Model Spec Midtraining** (Anthropic):
  `https://alignment.anthropic.com/2026/msm/` (confirmed in round 3
  audit).

---

## Questions for this round

### Q1 — Competitor positioning (closes O-FRAME-005 + O-FRAME-010)

The paper has two direct competitor anchors named in locked decisions:

- **Hierarchical Summarization** (D-FRAME-005, locked round 2) — the
  paper's direct LLM-monitor competitor. §7.6 of PAPER_OUTLINE_MERGED
  says "head-to-head on shared task family."
- **ST-WebAgentBench** (D-FRAME-006, locked round 2) — the closest
  published benchmark prior. §2.4 of PAPER_OUTLINE_MERGED lists it
  among agent-safety benchmarks but no concrete differentiation.

Both opens require concrete positioning decisions before Phase 2.

**Task 1a — Hierarchical Summarization empirical contrast
(O-FRAME-005).**

The PAPER_OUTLINE_MERGED §7.6 commits to "head-to-head on shared
task family." This is binary: either implement HS as a working
LLM-monitor on GovernedAgentBench tasks (empirical contrast) or
contrast in §2.3 prose only (rhetorical contrast).

1. Read the HS methodology. What is the actual implementation cost
   for a faithful HS reimplementation against GovernedAgentBench
   task families? Specifically:
   - How many LLM calls per trajectory does HS require?
   - What's the prompt structure (chunk → summary → aggregate)?
   - What's the dollar cost per trajectory at May 2026 pricing for
     Claude 3.5 Haiku or successor?
   - What's the engineering cost in hours for Dom to reimplement?

2. Specify what "shared task family" means concretely. Which of the
   L1-L7 task families is HS most usable on? Which is it least
   usable on?

3. Recommend one of:
   - **Full empirical contrast** at §7.6: HS reimplementation on
     shared task family, with detection-rate × FP-rate Pareto.
     Justify as paper-improving despite cost.
   - **Demoted rhetorical contrast** at §2.3: prose-only contrast,
     no §7.6 empirical cell. Justify as cost-bound scope discipline.
   - **Bounded empirical contrast** at §7.6: HS reimplementation on
     a narrow subset (e.g., L6 clinical-boundary only) for ≤ 2 weeks
     of work and ≤ $200 of API spend. Justify as paper-improving
     within budget.

   Pick one. Defend against the strongest critique.

**Task 1b — ST-WebAgentBench differentiation table (O-FRAME-010).**

The paper's §2.4 names ST-WebAgentBench but does not specify what
differentiates GovernedAgentBench. Without a concrete table, a
reviewer will read GovernedAgentBench as a derivative.

1. Read ST-WebAgentBench (arXiv:2410.06703). Identify the 4-6 axes
   on which GovernedAgentBench differs:
   - Task domain (web vs personal-wellness/structured-data)
   - Mechanism isolability (ST-WebAgentBench's coarse pass/fail vs
     GovernedAgentBench's per-mechanism ablation)
   - Runtime mode vs no-runtime baseline (does ST-WebAgentBench
     even have this?)
   - Predeclared model roster + threshold + scorer hash
     (D-FRAME-020/021)
   - Adversarial layer (D-FRAME-022 5-attack-type vs ST-WebAgentBench's)
   - Bench-vs-instantiation (HAI as reference runtime, not the
     benchmark itself)

2. Build the differentiation table. Format:

| Axis | ST-WebAgentBench (Levy et al. 2025) | GovernedAgentBench (this paper) | Why this matters for the claim |
|---|---|---|---|
| Task domain | ... | ... | ... |
| ... | ... | ... | ... |

3. State which axis is the **load-bearing differentiation** — the
   single difference that makes GovernedAgentBench non-redundant
   with ST-WebAgentBench.

**Deliverable for Q1:**

- HS empirical contrast recommendation (one of three options) with
  defended cost/feasibility.
- ST-WebAgentBench differentiation table (4-6 rows).
- One-paragraph §2.3 + §2.4 contrast prose draft that goes in the
  paper.

### Q2 — Coding-agent slice (closes O-FRAME-006)

PAPER_OUTLINE_MERGED §10.1 names "cross-domain generalization is
future work (coding agent, file system, productivity — appendix has
a sketch)." Appendix E was scoped as "cross-domain extension sketch
(coding agent, file system)." But the locked HAI freeze (D-PROJ-016)
means there is no coding-agent reference runtime in the repo. The
question is whether to:

- **Cut.** Drop Appendix E entirely. Limit the paper to personal-
  wellness as the sole instantiation. Move "future cross-domain"
  language to §10 limitations.
- **Appendix sketch only (5-10 hours of writing).** Keep Appendix E
  as a sketch with no implementation. Describe what a coding-agent
  runtime contract would look like (typed commands for git/diff/test;
  mutation classes for write/delete/rebase; agent_safe seams for
  destructive ops; refusal for credential exposure). Cite no working
  code.
- **Full second domain (3-6 weeks of engineering before paper).**
  Implement a minimal coding-agent reference runtime. Make Appendix
  E or a §11 section concrete with reproducible code.

**Task:**

1. Estimate the marginal paper credibility from each option:
   - Cut: clean scope discipline, but invites "single-domain"
     reviewer critique (Greenblatt-style).
   - Appendix sketch: hedges single-domain critique with cheap
     pages, but may read as "promissory note" if reviewers care.
   - Full domain: addresses single-domain critique directly, but
     costs 3-6 weeks Dom doesn't have (D-PROJ-016 HAI freeze +
     Summer 2026 commitments).

2. The Greenblatt critique (D-FRAME-019 second prong) is empirical
   (DRG-artifacts), not domain-scope. The Sharma critique
   (D-FRAME-019, F-AUDIT-3-01) is about brittleness in the
   instantiation, not about single-domain generalization. So
   single-domain is a real but secondary critique.

3. Recommend one option. Defend against the strongest critique of
   that option.

4. If "Appendix sketch," draft the §11 / Appendix E sketch in 200-
   400 words: what does a coding-agent runtime contract look like?
   What are its mutation classes? Where's the refusal boundary?

**Deliverable:** Recommendation with defense + (if appendix-sketch)
the 200-400 word draft sketch.

### Q3 — Paper 2 sketch precision (closes O-FRAME-011)

D-FRAME-010 locked paper 2 redirect to "S1 fine-tuning (RBR +
Deliberative Alignment lineage) at ICML 2028 or NeurIPS 2028." This
is the sequel paper after this paper's NeurIPS 2027 submission.
Currently the redirect is a destination but not a research question.

**Task:**

1. Read RBR (Rule-Based Rewards for LM Safety, NeurIPS 2024) and
   Deliberative Alignment (arXiv:2412.16339). Identify the open
   research question they leave that aligns with this project's
   contributions.

2. Sharpen paper 2's headline contribution. Options:
   - **S1 fine-tuning of bounded operators on the contract.** Train
     a small open-weight model (Qwen2.5-3B or similar) to be a
     better contract-operator. Show that fine-tuning improves
     command-validity / mutation-boundary-obedience at smaller
     model scale, complementing this paper's runtime-as-floor claim.
     Headline: "Trained operators reach contract-compliance at
     smaller scales than untrained."
   - **Spec-at-inference for runtime contracts.** Apply Deliberative
     Alignment lineage to teach a model the safety spec (the
     contract) at inference time without fine-tuning. Headline:
     "Inference-time spec injection reduces contract violations
     without weight updates."
   - **Pivot away from S1 fine-tuning entirely.** Frame paper 2 as
     a different direction (e.g., MCP-server contract surface,
     multi-agent contract composition, contract synthesis from spec).
     Justify the pivot.

3. Recommend one. Cite the prior art that justifies the pick.

4. Specify what *this paper* (NeurIPS 2027) must do to set up paper
   2 cleanly. Examples:
   - §11 future-work paragraph naming the headline.
   - Reserve a benchmark task family in GovernedAgentBench v2 for
     paper 2's evaluation.
   - Pre-register the S1 fine-tuning recipe so paper 2 can directly
     compare against paper 1's predeclared roster.

**Deliverable:** Paper 2 headline + 1-paragraph sketch + the
specific paper-1-setup decisions needed for the sequel.

---

## Deliverable format

Write your output to:

```
research/runtime_contracts_paper/framing_v2/round_5/RESPONSE.md
```

Structure:

```markdown
# Round 5 Research Response

## Q1 — Competitor positioning
### Q1a HS empirical contrast
[Cost/feasibility analysis, recommendation, defense]
### Q1b ST-WebAgentBench differentiation
[4-6 row table, load-bearing differentiation axis, paper prose draft]

## Q2 — Coding-agent slice
[Cut / appendix-sketch / full-domain recommendation + defense
+ (if appendix) 200-400 word sketch]

## Q3 — Paper 2 sketch precision
[Headline + 1-paragraph sketch + paper-1-setup requirements]

## Summary

### Decisions this round closes
- O-FRAME-005 (HS empirical contrast): [recommendation]
- O-FRAME-006 (coding-agent slice): [recommendation]
- O-FRAME-010 (ST-WebAgentBench positioning): [differentiation table]
- O-FRAME-011 (paper 2 sketch): [headline + setup]

### Decisions still open
- [list any of the above that the round couldn't close, with reasons]

### New decisions surfaced
- [anything else the round revealed needs deciding]
```

## Length and depth

Use `/goal` mode but be disciplined. This is a positioning round, not
an empirical round. Expected length:
- Q1: 1200-1800 words (HS analysis is the longest sub-part).
- Q2: 600-1000 words.
- Q3: 800-1200 words.

Total target: 2600-4000 words. Be concrete; the deliverables go
directly into Phase 2 doc-alignment edits.

## What NOT to do

- Do not edit any file outside `framing_v2/round_5/`.
- Do not propose decisions that contradict locked D-FRAME-001..023
  without flagging the conflict explicitly.
- Do not propose options that violate D-PROJ-016 HAI freeze (e.g.,
  "build a coding-agent reference runtime in HAI" is out — HAI is
  frozen).
- Do not propose options that exceed Dom's Summer 2026 bandwidth
  (~15-20 effective hours/week per CONTEXT_DOSSIER.md §1).
- Do not hallucinate citations. arXiv IDs for older papers (RBR,
  Deliberative Alignment, ST-WebAgentBench) are already confirmed in
  prior rounds; use them.

## When done

1. Save `RESPONSE.md` to the path above.
2. Notify Dom that round 5 research is complete.
3. Stop. Do not also write SYNTHESIS.md or AUDIT_RESPONSE.md.

---

## Orchestrator notes for the fresh session

If you (orchestrator) are reading this for the first time and the
round 5 prompt has not been dispatched yet, you may revise this
prompt before handing it to Dom. If you revise:

1. Update `ORCHESTRATOR_STATE.md` "Sub-state" to note the revision.
2. Keep the three questions; do not drop them.

If RESPONSE.md already exists when you read this, skip the dispatch
and proceed to drafting `AUDIT_PROMPT.md` per the protocol.

If this round returns SHIP_WITH_NOTES with no new paper-§-level
findings, the orchestrator should consider invoking the Phase 1
escape valve (two prior consecutive SHIP_WITH_NOTES + this one = 3)
and writing `framing_v2/CONVERGED.md` to move into Phase 2.
