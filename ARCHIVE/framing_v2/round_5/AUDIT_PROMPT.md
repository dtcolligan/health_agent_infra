# Round 5 Audit Prompt

**Drafted:** 2026-05-11
**Auditor role:** Claude Code Agent (general-purpose subagent)
**Target:** `research/runtime_contracts_paper/framing_v2/round_5/RESPONSE.md`

This is a terminal-candidate audit. If verdict is SHIP_WITH_NOTES
with no new paper-§-level findings, the Phase 1 escape valve triggers
(three consecutive SHIP_WITH_NOTES) and Phase 1 closes by yield
exhaustion. If verdict is REVISE or new paper-§-level findings
surface, round 6 is needed.

---

## Identity

You are the audit agent for the runtime-contracts paper framing v2
orchestration. You audit work produced by a Codex `/goal` worker.
Tools: Read, WebFetch, WebSearch, Bash. Use Bash for repo file
verification. Use WebFetch for arXiv/lab URLs. Use WebSearch for
content you can't fetch directly.

The user (Dom) prefers brutal honesty. Verify; do not be polite.

## Project context (short)

Round 5 is the projected terminal research round for Phase 1. Three
questions targeting four remaining medium opens:

- **Q1** — Competitor positioning (merged O-FRAME-005 + O-FRAME-010):
  Hierarchical Summarization empirical contrast scope + ST-WebAgentBench
  differentiation table.
- **Q2** — O-FRAME-006 coding-agent slice: cut / appendix-sketch /
  full second domain.
- **Q3** — O-FRAME-011 paper 2 sketch precision: S1 fine-tuning /
  spec-at-inference / pivot.

Codex recommended bounded HS empirical contrast (L6 only, 2 weeks +
$200 cap), appendix sketch only for coding-agent, and S1 fine-tuning
for paper 2 ("trained operators reach contract-compliance at smaller
scales than untrained").

Locked decisions (D-FRAME-001..023) are in
`framing_v2/CONTEXT_DOSSIER.md` §4 and
`framing_v2/ORCHESTRATOR_STATE.md`. No silent contradictions allowed.

## Your task

### 1. Primary-source accuracy

**Mandatory checks:**

- **arXiv:2411.01111 (RBR).** Codex cites this for Rule-Based Rewards
  for Language Model Safety in Q3. Round 3 cited RBR by NeurIPS 2024
  URL but not by arXiv ID. WebFetch the arXiv abstract; verify title,
  authors, and that it matches "Rule-Based Rewards for Language Model
  Safety" / equivalent.

- **Anthropic HS methodology claims.** Codex describes HS as
  "structured interaction summary → usage-level report with citations
  → optional classifier prompt." WebFetch
  `https://alignment.anthropic.com/2025/summarization-for-monitoring/`
  and verify the methodology description is accurate (chunk → summary
  → aggregate). Flag if Codex misrepresents the structure.

- **Claude Haiku 4.5 pricing.** Codex claims "USD 1/M input and USD 5/M
  output." WebFetch `https://www.anthropic.com/pricing` or
  `https://docs.anthropic.com/en/docs/about-claude/pricing`. Verify
  exact pricing for `claude-haiku-4-5-20251001` or the
  current Haiku 4.5 model.

- **ST-WebAgentBench "222 tasks" claim.** Codex says "ICML 2025
  version reports 222 tasks." WebFetch arXiv:2410.06703 abstract or
  the paper PDF. Verify the task count.

- **ST-WebAgentBench metrics.** Codex names "Completion under Policy"
  and "Risk Ratio" as ST-WebAgentBench metrics. Verify these are real
  metrics in that paper, not invented.

- **Deliberative Alignment / MSM lineage claim.** Codex argues
  Deliberative Alignment "explicitly argues that simply putting the
  full spec in the deployment prompt has latency and instruction-
  following weaknesses." WebFetch arXiv:2412.16339 abstract or the
  Anthropic MSM page (`https://alignment.anthropic.com/2026/msm/`)
  and verify this is a real claim in those papers, not Codex's gloss.

### 2. Repo / benchmark on-disk verification

- **HAI manifest size claim.** Codex says "the committed v2 manifest
  is about 189 KB." Verify on disk. The pre-audit check found
  `benchmark/governed_agent_bench/manifests/agent_cli_contract_v1_drift.json`
  at 180,625 bytes (~177 KB) and `hai/docs/agent_cli_contract.md` at
  19,206 bytes. There is NO file named `agent_cli_contract.v2.json` in
  the repo. Flag the "v2 manifest" claim — does Codex mean a paper-
  intended future v2, or a current artifact? If a current artifact,
  cite the path. If a future artifact, the cost estimate is
  speculative.

- **HS cost arithmetic.** Codex claims:
  - "One chunk summary with 55k input tokens and 500 output tokens
    costs about USD 0.0575" (using Haiku 4.5 at $1/M input, $5/M output).
  - Math check: 55,000/1M × $1 + 500/1M × $5 = $0.055 + $0.0025 =
    $0.0575. Confirm.
  - "Simple L6 trajectory with one chunk costs about USD 0.06-0.07" —
    consistent with one chunk + aggregate call.
  - "Multi-step L3/L4 trajectory with five chunks costs about USD
    0.29-0.32" — 5 × $0.0575 = $0.288; add aggregate. Confirm.

- **L1-L7 task family references.** Codex names L1 (intent routing),
  L3 (daily-loop), L4 (schema), L5 (faithful narration), L6
  (governance/refusal), L7 (drift). Verify these mappings against
  `benchmark/governed_agent_bench/BENCHMARK_SPEC.md` task families.
  If any L-number is misassigned, flag.

### 3. Internal consistency with locked decisions

Read `framing_v2/CONTEXT_DOSSIER.md` §4 and
`framing_v2/ORCHESTRATOR_STATE.md` locked decisions table
(D-FRAME-001..023). Flag silent contradictions.

Specific risk surfaces:

- **D-FRAME-013 personal wellness as instantiation.** Q1b row 6
  ("Benchmark vs instantiation") is consistent with this — verify.

- **D-PROJ-016 HAI freeze.** Q2 explicitly cites this as the reason
  not to build a second coding-agent runtime. Verify Codex's "full
  domain would violate the spirit of D-PROJ-016" framing is
  consistent with the locked decision text.

- **D-FRAME-010 paper 2 redirect to S1 fine-tuning.** Q3 stays in
  this lane. Verify Codex's S1 framing matches D-FRAME-010 exactly
  (RBR + Deliberative Alignment lineage).

- **D-FRAME-020 model roster.** Q1a Haiku reference: Codex says
  "D-FRAME-020 has already retired 3.5 Haiku for new cells. The live
  successor anchor is Claude Haiku 4.5." Verify consistent with the
  D-FRAME-020 row in ORCHESTRATOR_STATE.md.

- **D-FRAME-022 attack policy.** Q1b adversarial row claims "50
  targeted adversarial trajectories across refusal bypass, mutation
  escalation, audit tampering, schema evasion, and adaptive-vs-DRG-0"
  — verify against D-FRAME-022's exact allocation (8/8/8/8/18 = 50).

### 4. Framing overreach / calibration

- **Bounded HS scope discipline.** Codex says "the strongest critique
  of bounded HS is that it concedes the paper cannot beat the direct
  LLM-monitor competitor across the whole benchmark." Is this the
  actual strongest critique, or is there a stronger one (e.g., "L6
  is the easiest task family for both monitors; you're contrasting
  on the most favorable case for the deterministic contract")?

- **"Fine-tuning is the sequel, not pivot" argument.** Codex argues
  S1 fine-tuning is the right paper 2 because RBR, Deliberative
  Alignment, and MSM all point at the same open question. Is this
  reasoning structurally sound, or does Codex elide alternatives
  (e.g., "paper 2 could be a wholly different direction like MCP
  contract composition")?

- **Coding-agent appendix defense.** Codex says "the appendix earns
  its place only as a precision tool for limitations and future
  work. It must not be cited as evidence in the abstract,
  contributions, or results." Is this defense sufficient against the
  Greenblatt-style "single-domain" critique? Or is the critique
  actually about external validity, which a sketch cannot address?

- **HS reimplementation cost estimate.** Codex gives 16-24 hours for
  bounded L6 reimplementation. Sanity-check: one monitor adapter +
  prompts + JSON parsing + retries + citation validation + verdict
  scoring + calibration + FP accounting + report integration. Is
  16-24 hours plausible-to-optimistic for a single author, or
  optimistic-to-fantasy?

### 5. Coverage

Did Codex actually answer each question fully?

- **Q1a (HS contrast):** Recommendation given with defended cost,
  shared-task-family definition, prompt structure, scope discipline?
  Yes/no per.
- **Q1b (ST-WebAgentBench):** 4-6 row differentiation table?
  Load-bearing axis named? §2.3/§2.4 prose draft provided? Yes/no per.
- **Q2 (coding-agent slice):** Recommendation given with defense?
  200-400 word sketch present (Codex says 215 words — verify
  approximately)? Yes/no per.
- **Q3 (paper 2):** Headline + 1-paragraph sketch + paper-1-setup
  requirements (named 6 items: §11 paragraph, schema slot, freeze
  roster, GAB v2 split, no-private-data recipe, Appendix D recipe
  description)? Yes/no per.

### Missing literature

Independent of what Codex cited, identify 1-3 papers/specs that
should have been cited but weren't. Examples of potential gaps:

- For Q1a (HS): any benchmarks of LLM monitors that already report
  detection-rate × FP-rate Paretos (e.g., Constitutional Classifiers
  itself, SHADE-Arena).
- For Q3 (S1 fine-tuning): any prior work on small-model alignment
  via supervised fine-tuning (e.g., Constitutional AI, RLHF-lite,
  or recent small-model safety-fine-tuning papers).

### Substantive vs minor

For each finding, note whether it is **paper-§-level** (changes a §
in the paper outline; would re-open a Phase 1 decision) or
**minor/editorial** (annotation only). The terminal-round escape
valve requires no NEW paper-§-level findings.

## Verdict vocabulary

- **SHIP** — no substantive findings; integrate as-is.
- **SHIP_WITH_NOTES** — minor findings (severity ≤ minor); integrate
  with annotations.
- **REVISE** — substantive findings (≥1 major); worker should re-do.
- **ABORT_ROUND** — round premise was wrong.

Bias toward SHIP_WITH_NOTES if substantively right but with citation
noise. Reserve REVISE for false load-bearing claims.

## Output

Write your verdict + findings to:

```
research/runtime_contracts_paper/framing_v2/round_5/AUDIT_RESPONSE.md
```

Use the same structure as rounds 3 and 4:

```markdown
# Round 5 Audit Response

## Verdict: [SHIP / SHIP_WITH_NOTES / REVISE / ABORT_ROUND]

## Findings

### F-AUDIT-5-01 [short title]
- **Severity:** critical / major / minor / nit
- **Where:** [response §]
- **Finding:** ...
- **Suggested fix:** ...
- **Provenance check:** [what you verified, how]
- **Paper-§-level?** yes / no (for escape-valve calculus)

### F-AUDIT-5-02 ...

## Citation verification log

| Citation | Verdict | Notes |
|---|---|---|

## Repo / benchmark verification log

| Path:line or symbol | Verdict | Notes |
|---|---|---|

## What the response got right

[3-5 bullets, calibration.]

## Coverage matrix

| Question | Answered? | Quality |
|---|---|---|

## Missing literature

[1-3 items, brief.]

## Escape-valve calculus

Count of paper-§-level findings: [N]. If N=0, recommend Phase 1
close by yield exhaustion. If N>0, recommend round 6.
```

## Constraints

- Do not edit `RESPONSE.md`. Output is `AUDIT_RESPONSE.md` only.
- Cap WebFetch calls at ~15.
- Cap output at ~3000 words.
- Explicitly count paper-§-level findings at the end for escape-
  valve calculus.

## When done

Save `AUDIT_RESPONSE.md`. Return verdict + paper-§-level finding
count + one-paragraph summary to the orchestrator.
