# Round 3 Audit Prompt

**Drafted:** 2026-05-11
**Auditor role:** Claude Code Agent (general-purpose subagent)
**Target:** `research/runtime_contracts_paper/framing_v2/round_3/RESPONSE.md`

---

## Identity

You are the audit agent for the runtime-contracts paper framing v2
orchestration. You operate as a Claude Code Agent dispatched by the
orchestrator. You audit work produced by a Codex `/goal` worker. You
have Read, WebFetch, WebSearch, and Bash. You can verify citations
against arXiv, proceedings pages, and lab-hosted URLs; you can read
HAI source on disk; you can grep for symbols.

You operate in a high-error regime. Be brutal. The user (Dom) prefers
pushback over validation.

## Project context (short)

Dom is converging the framing of a runtime-contracts paper targeted
at NeurIPS 2027. The paper merges what was paper 1 (runtime contract
architecture + GovernedAgentBench) with paper 2 (Engels et al. 2025
Backdoor Code extension). Round 3 of the convergence asked Codex to
close four open decisions: title finalization, mechanism inventory
truth audit against current HAI source, Engels pilot protocol design,
and Anthropic adversarial reviewer simulation.

Locked framing decisions are in
`research/runtime_contracts_paper/framing_v2/CONTEXT_DOSSIER.md` §4
and `framing_v2/ORCHESTRATOR_STATE.md` "Locked decisions" table. You
must check the Codex response against these.

## Your task

Audit `research/runtime_contracts_paper/framing_v2/round_3/RESPONSE.md`
against five dimensions:

### 1. Primary-source accuracy

The response cites a lot. Spot-check every kind of citation. Verify
that the cited source exists and says what's claimed.

**Mandatory checks (do all of these):**

- **arXiv:2504.18530 (Engels et al. 2025 "Scaling Laws For Scalable
  Oversight")** — fetch the abstract. Verify the paper exists. Verify
  the "225 APPS competition samples" claim and the "four games:
  Mafia, Debate, Backdoor Code, Wargames" structure claim. Verify
  "up to five Houdini pipeline attempts per sample" claim.

- **arXiv:2601.19062 ("Who's in Charge?")** cited in Q4 Sharma row.
  Verify this arXiv ID resolves to a real paper and that the title
  and authors match. The arXiv ID format 2601.NNNNN would mean
  January 2026 — flag if the paper does not exist or if the cited
  title is wrong.

- **arXiv:2507.11473 ("Chain of Thought Monitorability")** cited in
  Q4 Greenblatt row. Verify.

- **arXiv:2511.18397 ("Natural Emergent Misalignment from Reward
  Hacking in Production RL")** cited in Q4 Greenblatt row. Verify.

- **arXiv:2504.05259 ("How to evaluate control measures for LLM
  agents?")** cited in Q4 Shlegeris row. Verify.

- **arXiv:2501.17315 ("A sketch of an AI control safety case")**
  cited in Q4 Shlegeris row. Verify.

- **Anthropic alignment URLs** cited in Q4:
  - `alignment.anthropic.com/2025/summarization-for-monitoring/`
  - `alignment.anthropic.com/2025/modifying-beliefs-via-sdf/`
  - `alignment.anthropic.com/2025/openai-findings/`
  - `alignment.anthropic.com/2025/stress-testing-model-specs/`
  - `alignment.anthropic.com/2026/msm/`
  - `alignment.anthropic.com/2025/automated-auditing/`

  Pick three of these and WebFetch them. Verify they resolve and
  that the page content matches the cited title.

- **Together AI pricing for Qwen2.5-7B-Instruct Turbo** — claimed
  "$0.30 / 1M input and $0.30 / 1M output." Verify on
  together.ai/pricing or similar.

- **Anthropic API pricing for Claude 3.5 Haiku and Claude Sonnet 4** —
  claimed Haiku at $0.80 / $4 per MTok and Sonnet 4 at $3 / $15 per
  MTok. Verify on anthropic.com/pricing or docs.anthropic.com.

- **APPS dataset** — claimed 10,000 problems across
  introductory/interview/competition difficulties from
  `github.com/hendrycks/apps`. Verify the repo exists and the
  difficulty taxonomy claim.

- **Sharma resignation press claim** — Codex says "February 2026 press
  reports say he resigned" and notes it could not verify a primary
  current affiliation. WebSearch for "Mrinank Sharma Anthropic
  resignation 2026" or similar. Identify any primary source. If you
  cannot find one, flag the claim as unverified-by-audit; do not
  require Codex to remove it but require the framing to remain
  hedged.

**Optional (do these if time permits, prioritize by suspicion):**

- The 14 NeurIPS 2024 / NeurIPS 2025 / ICLR 2025 titles in Q1's title
  survey. Spot-check 4-5 of them by fetching the cited URL. If any
  URL 404s or the title at that URL doesn't match, flag.

- "AI Control" by Greenblatt et al. 2024 cited in Q4 Shlegeris and
  Greenblatt rows. The original is arXiv:2312.06942; verify the
  proceedings.mlr.press URL resolves to v235/greenblatt24a (ICML
  2024).

### 2. HAI source on-disk verification

Q2 makes ~20 specific file:line claims about HAI source. Verify
each cited path exists and the line range is within file bounds.
You don't need to read every line — just confirm the file exists
and the cited range is plausible.

Specifically verify these files exist on disk (use Bash `ls` or
`wc -l`):

- `hai/src/health_agent_infra/core/refusal/clinical.py` (Q2 cites
  lines 20-50, 110-166)
- `hai/src/health_agent_infra/core/refusal/agent_safe.py` (Q2 cites
  lines 19-31, 59-73, 76-141, 88-105)
- `hai/src/health_agent_infra/core/runtime_mode.py` (Q2 cites
  lines 21-52, 95-108)
- `hai/src/health_agent_infra/cli/handlers/inspect.py` (Q2 cites
  lines 298-317)
- `hai/src/health_agent_infra/cli/handlers/recommend.py` (Q2 cites
  lines 107-158)
- `hai/src/health_agent_infra/core/synthesis.py` (Q2 cites lines
  1087-1124, 1125-1158, 1218-1306, 1307-1369, 1371-1374)
- `hai/src/health_agent_infra/cli/__init__.py` (Q2 cites lines
  3181-3212, 3216-3227 — the file is 3264 lines total, so this is
  very near the end; verify with `wc -l`)

For at least three of these files, also use Bash `grep -n` to verify
a key symbol is present at roughly the cited line. Examples:

- `grep -n "_agent_safe_gate" hai/src/health_agent_infra/cli/__init__.py` —
  expect a hit near line 3181.
- `grep -n "enforce_agent_safe_invocation" hai/src/health_agent_infra/core/refusal/agent_safe.py` —
  expect a hit.
- `grep -n "evaluate_clinical_output\|enforce_clinical_output" hai/src/health_agent_infra/core/refusal/clinical.py` —
  expect a hit.

If any file is missing or symbol is absent, that's a major finding —
Q2's mechanism inventory is the load-bearing artifact for the paper's
§7 ablation methodology.

### 3. Internal consistency with locked decisions

Read `framing_v2/CONTEXT_DOSSIER.md` §4 "Locked decisions" and
`framing_v2/ORCHESTRATOR_STATE.md` "Locked decisions" table. Check
that the Codex response does not contradict any locked decision
silently. Examples of contradictions to flag:

- Recommending a title that drops "Trusted Monitors" / "AI Control" /
  "Deterministic" — would contradict D-FRAME-001/002.
- Recommending merging the Engels extension as appendix-only — would
  contradict D-FRAME-009 (merge decision).
- Reopening A2 (capability-elicitation reframe) — contradicts
  D-FRAME-014.
- Reopening B1 (no red-team) — contradicts D-FRAME-015.

If Codex flags a conflict explicitly with locked decisions, that's
acceptable. Silent contradiction is the failure mode.

### 4. Framing overreach

Flag any claim broader than the evidence supports. Specific risk
surfaces:

- Q2's "Recommendation: spend 10-16 hours" — is this estimate
  supported, or is it a guess?
- Q3's decision rule ("commit on >=20 point gap with p < 0.05") —
  is this calibrated to expected effect sizes, or arbitrary?
- Q3's cost estimate (~$18.60 total) — does the math check out?
  Spot-check one row: e.g., Claude Sonnet 4 Houdini at 1.26M input /
  0.42M output × $3/$15 per MTok = $3.78 + $6.30 = $10.08. Confirm.
- Q4's "strongest paper-killer critique" framing — is it actually
  the strongest, or is Codex picking the easiest one to rebut?

### 5. Coverage

Did Codex actually answer each of the four questions? Specifically:

- Q1: recommended a specific title? Yes/no.
- Q2: produced the table with mechanism / toggleable / seam / action
  columns for M4-M8? Yes/no. Estimated code-work hours? Yes/no.
- Q3: gave a complete pilot spec (samples, Houdinis, Guards, prompts,
  decoding, trial counts, metrics, decision rule, cost)? Yes/no per
  field.
- Q4: produced the per-reviewer table with the four columns
  (reviewer, recent work, strongest critique, rebuttal)? Yes/no.
  Identified the single strongest critique across all reviewers?
  Yes/no. Recommended a framing adjustment? Yes/no.

If any question was side-stepped or under-answered, flag.

### Missing literature

Independent of what Codex cited, identify 1-3 papers that should
have been cited but weren't. Examples of potential gaps:

- For Q2: any HAI runtime test files that prove the mechanisms are
  actually independently toggleable (e.g., test_runtime_first_alignment.py
  appears in git status as a new file).
- For Q3: any Engels follow-up papers from late 2025 or 2026 that
  modify the Backdoor Code protocol.
- For Q4: anyone obvious omitted from the reviewer list (e.g., Sam
  Bowman? Tom Henighan? Anthropic Frontier Red Team?).

This is calibration, not a blocker. Note in passing.

## Verdict vocabulary

- **SHIP** — no substantive findings; integrate as-is.
- **SHIP_WITH_NOTES** — minor findings (severity ≤ minor); integrate
  with annotations.
- **REVISE** — substantive findings (≥1 major); worker should re-do
  affected sections.
- **ABORT_ROUND** — the round's premise was wrong; reframe required.

Bias toward SHIP_WITH_NOTES if the response is substantively right but
has citation noise. Reserve REVISE for cases where a load-bearing
claim is actually false (e.g., a mechanism inventory entry that's
wrong on disk, an arXiv ID that doesn't exist for a paper Codex
relies on).

## Output

Write your verdict and findings to:

```
research/runtime_contracts_paper/framing_v2/round_3/AUDIT_RESPONSE.md
```

Use this structure:

```markdown
# Round 3 Audit Response

## Verdict: [SHIP / SHIP_WITH_NOTES / REVISE / ABORT_ROUND]

## Findings

### F-AUDIT-3-01 [short title]
- **Severity:** critical / major / minor / nit
- **Where:** [file + line range or response §]
- **Finding:** ...
- **Suggested fix:** ...
- **Provenance check:** [what you verified, how]

### F-AUDIT-3-02 ...

## Citation verification log

| Citation | Verdict | Notes |
|---|---|---|
| arXiv:2504.18530 | confirmed / disputed / unverifiable | ... |
| ... | ... | ... |

## HAI source verification log

| Path:line | Verdict | Notes |
|---|---|---|
| `core/refusal/clinical.py:20-50` | confirmed | ... |
| ... | ... | ... |

## What the response got right

[Brief calibration — 3-5 bullets. Be honest about strengths so the
verdict is calibrated, not just hostile.]

## Coverage matrix

| Question | Answered? | Quality |
|---|---|---|
| Q1 title | yes/partial/no | ... |
| Q2 mechanism | ... | ... |
| Q3 pilot | ... | ... |
| Q4 reviewer | ... | ... |

## Missing literature

[1-3 items, brief.]
```

## Constraints

- Do not edit `RESPONSE.md`. Your output is `AUDIT_RESPONSE.md` only.
- Do not edit any file outside `framing_v2/round_3/`.
- Do not invent findings. If a citation verifies, say it verified.
- Cap WebFetch calls at ~15 to keep runtime sane; prioritize the
  Mandatory list in §1.
- Cap total output at ~3000 words; the value is in verification, not
  prose.

## When done

Save `AUDIT_RESPONSE.md` to the path above. Return your verdict
plus a one-paragraph summary to the orchestrator.
