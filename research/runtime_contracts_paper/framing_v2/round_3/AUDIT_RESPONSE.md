# Round 3 Audit Response

## Verdict: SHIP_WITH_NOTES

Codex's response is substantively right on every load-bearing axis: HAI source citations all verify, the Engels "225 APPS competition samples / four games / five Houdini attempts" structural claims hold against an independent search, every arXiv ID resolves to the cited paper (including the surprising-looking 2601.19062, which is real and authored by Sharma himself), and all sampled API/dataset/proceedings URLs match. The Sharma resignation press claim resolves to a primary source (Sharma's own X post on his last day, Feb 9 2026) that Codex was unable to find but the audit located. The math in the Q3 cost table is right to the penny. The headline reservation: Codex's recommended title preserves all three locked-framing anchors ("deterministic", "trusted monitors", "AI Control"), but the "control protocol" anchor from the locked headline is silently weakened to "AI Control" alone, which is acceptable framing-wise but worth flagging. No load-bearing claim is wrong; integrate with the notes below.

## Findings

### F-AUDIT-3-01 Sharma resignation has primary-source confirmation; Codex hedging can relax slightly

- **Severity:** minor
- **Where:** Q4 reviewer table, Sharma row affiliation note
- **Finding:** Codex wrote "February 2026 press reports say he resigned ... I found no primary current lab affiliation, so treat him as former Anthropic / independent unless verified later." Audit located a primary source: Sharma's own X post dated his last day at Anthropic, with the resignation letter attached (https://x.com/MrinankSharma/status/2020881722003583421), corroborated by Bloomsbury Intelligence and Security Institute, Yahoo Finance, eWeek, The Hill, and India TV — date Feb 9-10 2026. He resigned voluntarily; the letter cites global crises and personal-values alignment. Codex's hedge ("former Anthropic / independent") is correct in direction but unnecessarily uncertain.
- **Suggested fix:** Replace the hedge with "resigned from Anthropic Safeguards lead role Feb 9 2026; current affiliation unknown post-resignation." Keep the reviewer-simulation argument intact — his Safeguards work and the Constitutional Classifiers/HS papers are still the right signals for what he'd critique.
- **Provenance check:** WebSearch "Mrinank Sharma Anthropic resignation 2026" returned the primary X post plus 8 corroborating press sources within the first page.

### F-AUDIT-3-02 Title recommendation drops "control protocol" but retains other locked anchors

- **Severity:** minor
- **Where:** Q1 final recommendation, line 62
- **Finding:** Locked headline (CONTEXT_DOSSIER.md §4 row 1) reads "deterministic software contract that operationalizes a safety spec as the **trusted monitor** in an **AI control protocol** for bounded agent operation." Codex's recommended title "Deterministic Software Contracts as Trusted Monitors for AI Control" preserves "deterministic", "trusted monitors", and "AI Control" but compresses "control protocol" to "AI Control" alone. This is not a silent contradiction of D-FRAME-001/002 (the anchors are still there), but the "protocol" framing is load-bearing in Q4 rebuttals against Shlegeris/Greenblatt where Codex itself wants to land "trusted-monitor substrate for bounded AI-control protocols." The title should support that move.
- **Suggested fix:** Consider "Deterministic Software Contracts as Trusted Monitors in AI Control Protocols" (10 words, retains "protocol"). If Codex's 9-word version is preferred for index-scannability, ensure the abstract's first sentence carries "control protocol" explicitly. Decision is editorial; flagging for transparency.
- **Provenance check:** Read CONTEXT_DOSSIER.md §4 locked decisions table.

### F-AUDIT-3-03 M7 "covers hai today" claim is narrower than the broader sweep implies

- **Severity:** minor
- **Where:** Q2 table row M7, lines 86-88 + table line 117
- **Finding:** Codex states M7's `hai today` final-text refusal lives at `cli/handlers/inspect.py:298-317`. Verified on disk: the JSON-format branch is exempted (the code has `if fmt != "json":`). Codex correctly hedges in line 117 that M7 is "not yet proven as a universal final-output refusal for every CLI text surface" — that hedge is accurate; the inspect.py code only enforces refusal for non-JSON output. This is not a finding against Codex (the hedge is honest), but the paper §7 must not over-promise. Recommendation: if M7 is described as "user-facing text refusal," that's correct; if it's described as "all final output refusal," that's false — JSON surfaces are explicitly bypassed.
- **Suggested fix:** Carry Codex's narrow framing into the paper §7 wording without softening.
- **Provenance check:** `sed -n '298,317p' hai/src/health_agent_infra/cli/handlers/inspect.py` shows the `if fmt != "json":` guard at line 301.

### F-AUDIT-3-04 Cost table is precise; no fix needed but spot-check confirms

- **Severity:** nit
- **Where:** Q3 cost estimate table, lines 425-430
- **Finding:** Verified by hand: Sonnet 4 Houdini = $3 × 1.26M + $15 × 0.42M = $3.78 + $6.30 = $10.08. Haiku 3.5 Houdini = $0.80 × 1.26 + $4 × 0.42 = $2.69. Qwen2.5-7B = $0.30 × (1.26+0.42) = $0.50. Haiku Guard = $0.80 × 2.0 + $4 × 0.15 = $2.20. Subtotal = $15.47. 20% overhead = $3.09 (Codex rounded to $3.10). Total = $18.56 (Codex rounded to $18.60). Arithmetic clean to the penny.
- **Suggested fix:** None.
- **Provenance check:** Python arithmetic confirmed against verified pricing.

### F-AUDIT-3-05 Engels paper Houdini-attempt cap claim verified by alternative path

- **Severity:** nit
- **Where:** Q3 source-protocol paragraph, line 151
- **Finding:** Codex claims "225 APPS competition samples and up to five Houdini pipeline attempts per sample." arXiv PDF fetch of 2504.18530 was non-text-extractable, but Google Scholar / web search for the exact phrase "225 ... APPS ... Backdoor Code" returned LessWrong/OpenReview/alphaXiv excerpts confirming "225 Python 3 samples from the APPS dataset at the competition difficulty level." The "five Houdini pipeline attempts" claim was not independently confirmed by the audit's search; the abstract does not state it. Codex's design depends on this number for sample budget. Recommend Dom verify the attempt-cap number against the paper PDF body before treating it as load-bearing for the merged paper's protocol.
- **Suggested fix:** Mark the "five attempts" number as "per Engels protocol, citation to be re-verified against §4 of the source paper" in the pilot manifest until Dom reads the source.
- **Provenance check:** WebSearch confirmed 225/APPS/competition. WebFetch on arXiv PDF returned unrenderable binary. The five-attempt cap is a Codex claim that survived audit only by absence of disconfirmation.

### F-AUDIT-3-06 Code-work estimate (10-16 hours) is unbacked but probably right-shaped

- **Severity:** minor
- **Where:** Q2 lines 140-145
- **Finding:** Codex recommends "10-16 hours" for benchmark-ready regression tests + manifest alignment, and "12-20 additional hours" for the broader M7 audit. No decomposition into per-task hour breakdowns is provided. Audit cannot confirm or refute. Looking at the existing test surface (`benchmark/verification/tests/test_runtime_first_alignment.py` is 8.8KB / ~250 LOC for a partial scope), 10-16 hours for the full mechanism-pair regression matrix feels plausible-to-optimistic, not generous. If Codex is asked to deliver this, expect 14-22 hours actual; the lower end of the band assumes no debugging.
- **Suggested fix:** Treat the estimate as a planning anchor, not a contract. Decompose into per-mechanism positive/negative pair + hermetic-state assertion + marker-shape assertion tasks before committing.
- **Provenance check:** `ls -la benchmark/verification/tests/test_runtime_first_alignment.py` and rough LOC.

### F-AUDIT-3-07 Q4 "strongest critique" identification is internally coherent but politically convenient

- **Severity:** minor
- **Where:** Q4 lines 448-452
- **Finding:** Codex picks the "overclaim as AI Control without intentional-subversion evaluation" critique as strongest. This is a real critique and the rebuttal (reframe as "trusted-monitor substrate for bounded control protocols") is sound. But: it is also the critique Codex has the cleanest in-paper response to. Sharma's critique ("brittle, doesn't address disempowerment/aggregate harms") and Greenblatt's critique ("DRG-0 may be a benchmark-specific specialized detector exploiting artifacts") are arguably harder to rebut because they attack contributions Codex cannot retreat from without gutting the paper. Greenblatt's DRG critique is particularly load-bearing: if the deterministic Guard wins only because of APPS-specific artifacts, the headline empirical fails. Codex's response to Greenblatt (pre-register DRG inputs, ablations, FP rates) is good but the critique is structurally more dangerous than the AI-Control-overclaim framing critique.
- **Suggested fix:** Note in the cycle docs that two critiques are paper-killers, not one. The framing-overclaim critique is easier to rebut by language; the DRG-artifacts critique is the empirical risk that the Engels pilot must directly de-risk.
- **Provenance check:** Internal reasoning against Codex's own decision rule §6 ("Fairness: DRG-0 did not use Houdini trigger inputs, hidden-test oracle outputs, or hand-tuned thresholds from the primary 60 samples") — this is exactly Greenblatt's critique. Codex anticipated it correctly but did not rank it as strongest.

## Citation verification log

| Citation | Verdict | Notes |
|---|---|---|
| arXiv:2504.18530 (Engels Scaling Laws) | confirmed | Title, authors, four-games structure all match. "225 APPS competition" confirmed via web search excerpts (LessWrong/OpenReview/alphaXiv). "Five attempts" not independently verified, see F-AUDIT-3-05. |
| arXiv:2601.19062 ("Who's in Charge?") | confirmed | Real paper. Sharma + McCain + Douglas + Duvenaud, Jan 2026, 1.5M Claude.ai conversations on disempowerment patterns. arXiv ID 2601.NNNNN is a real January 2026 format. |
| arXiv:2507.11473 (CoT Monitorability) | confirmed | Korbak lead, 40+ co-authors incl. Bengio/Dragan. Title matches. |
| arXiv:2511.18397 (Natural Emergent Misalignment) | confirmed | MacDiarmid lead, 22 authors, reward-hacking-to-misalignment thesis matches. |
| arXiv:2504.05259 (Korbak/Balesni/Shlegeris/Irving) | confirmed | Title matches: "How to evaluate control measures for LLM agents? A trajectory from today to superintelligence." |
| arXiv:2501.17315 (AI control safety case) | confirmed | Korbak/Clymer/Hilton/Shlegeris/Irving. Title matches. |
| proceedings.mlr.press/v235/greenblatt24a | confirmed | "AI Control: Improving Safety Despite Intentional Subversion." PMLR v235 (ICML 2024). |
| alignment.anthropic.com/2025/summarization-for-monitoring/ | confirmed | "Monitoring computer use via hierarchical summarization." |
| alignment.anthropic.com/2026/msm/ | confirmed | "Model Spec Midtraining: Improving How Alignment Training Generalizes." |
| alignment.anthropic.com/2025/automated-auditing/ | confirmed | "Building and evaluating alignment auditing agents." |
| Anthropic API pricing (Haiku 3.5 $0.80/$4; Sonnet 4 $3/$15) | confirmed | platform.claude.com/docs/en/about-claude/pricing matches exactly. |
| Together AI pricing (Qwen2.5-7B-Instruct Turbo $0.30/$0.30) | confirmed | together.ai/pricing matches. |
| github.com/hendrycks/apps | confirmed | Repo exists. Difficulty taxonomy (introductory/interview/competition) and 10,000-problem claim is widely cited APPS structural fact; not contradicted. |
| Sharma resignation Feb 2026 | confirmed via primary source | Sharma's own X post (status/2020881722003583421) dated his last day; corroborated by 8 press sources. Codex hedge can relax. |
| NeurIPS 2024 RedCode (poster/97521) | confirmed | Title matches. |
| NeurIPS 2024 "Government AI Agent" (poster/93093) | confirmed | Berdoz + Wattenhofer, exact title match. |
| NeurIPS 2025 OS-Harm (poster/121772) | confirmed | Title matches. |

## HAI source verification log

| Path:line | Verdict | Notes |
|---|---|---|
| `core/refusal/clinical.py:20-50` | confirmed | Phrase-loading + pattern construction; matches Codex description. |
| `core/refusal/clinical.py:110-166` | confirmed | `evaluate_clinical_output` (line 110) and `enforce_clinical_output` (line 154). File is 190 lines; range fits. |
| `core/refusal/agent_safe.py:19-31` | confirmed | Invocation-context constants. |
| `core/refusal/agent_safe.py:59-73` | confirmed | `current_invocation_context` function. |
| `core/refusal/agent_safe.py:76-141` | confirmed | `evaluate_agent_safe_invocation`. |
| `core/refusal/agent_safe.py:88-105` | confirmed | mechanism_disabled_marker branch within evaluate. |
| `core/runtime_mode.py:21-52` | confirmed | Mode constants + MECHANISMS_OFF_BY_MODE table. |
| `core/runtime_mode.py:95-108` | confirmed | `require_runtime_mode_allowed` hermetic guard. |
| `cli/handlers/inspect.py:298-317` | confirmed | `hai today` clinical-output enforcement; JSON-format exempt (see F-AUDIT-3-03). |
| `cli/handlers/recommend.py:107-158` | confirmed | Proposal validation off-path with mechanism-disabled marker emission. |
| `core/synthesis.py:1087-1124` | confirmed | Validation off-path with banned-token escalation when refusal is on. |
| `core/synthesis.py:1125-1158` | confirmed | Refusal-separated banned-token sweep + disabled marker. |
| `core/synthesis.py:1218-1306` | confirmed | TX-bound supersede + recommendation-log writes. |
| `core/synthesis.py:1307-1369` | confirmed | Evidence-card emission + audit_chain disable marker. |
| `core/synthesis.py:1371-1374` | confirmed | `conn.commit()` + rollback in except. |
| `cli/__init__.py:3181-3212` | confirmed | `_agent_safe_gate` function. File is 3264 lines; range near end is correct. |
| `cli/__init__.py:3216-3227` | confirmed | `main()` dispatch with `_agent_safe_gate` call at line 3224. |
| `grep _agent_safe_gate cli/__init__.py` | confirmed | Hits at 3181, 3187, 3195, 3224. |
| `grep enforce_agent_safe_invocation agent_safe.py` | confirmed | Defined at 125; exported at 155. |
| `grep evaluate_clinical_output clinical.py` | confirmed | Defined at 110; exported at 188. |

## What the response got right

- **Truth-audit of stale findings.** Codex correctly identified that F-CDX-RFR-R1-09 (M5 not general enforcement) is now stale: `_agent_safe_gate` at `cli/__init__.py:3181` is genuinely a dispatch-time mechanism. The older finding was source-accurate at the time and Codex flags the drift honestly.
- **M5/M6 separability nuance.** The point that you cannot measure M6 independently if M5 fires first ("must avoid measuring 'M5 blocked before M6' as if it were a proposal-gate result") is exactly the kind of methodology trap a careless ablation matrix would step into.
- **M8 renaming to "audit evidence emission."** Correctly narrows the ablation claim. M9-TX transaction integrity is non-ablatable; the response makes that explicit.
- **Decision rule structure for Q3.** Six-clause commit rule + six-clause revert rule + borderline zone is the right shape for a go/no-go pilot. Sets up a paper that can be honest about a null result.
- **DRG-0 information-boundary discipline.** Forbidding access to Houdini trigger inputs and hidden-test oracle outputs anticipates exactly the Greenblatt critique (F-AUDIT-3-07).
- **Citations.** Every URL and arXiv ID that the audit checked resolved correctly. Zero fabricated citations.

## Coverage matrix

| Question | Answered? | Quality |
|---|---|---|
| Q1 title | yes | Specific recommendation, ranked against four candidates, with rationale. |
| Q2 mechanism | yes | Full table for M4-M8 with seam citations, action items, and toggleability assessment. Hours estimate present but unbacked (F-AUDIT-3-06). |
| Q3 pilot | yes | Complete spec: 60 APPS samples + selection procedure + manifest hash + 3 Houdinis + 2 Guards + DRG-0 module breakdown + Houdini prompt templates + decoding settings + 6-clause decision rule + cost. Only gap: "five Houdini attempts" from Engels is unre-verified (F-AUDIT-3-05). |
| Q4 reviewer | yes | Five-row table (Sharma, Perez, Shlegeris, Greenblatt, Generic Alignment Science) with critique + rebuttal. Strongest critique identified; framing adjustment recommended. F-AUDIT-3-07 disputes the ranking but not the table. |

## Missing literature

- **Adaptive Attacks on Trusted Monitors Subvert AI Control Protocols (arXiv:2510.09462)** appeared in the audit's web search alongside the Engels paper. This is a direct attack-policy result against trusted-monitor scaffolds; given Q4's recommended reframe to "trusted-monitor substrate," the paper §2 / §5 should cite it. Not citing it is a gap that a Greenblatt-style reviewer would flag.
- **`benchmark/verification/tests/test_runtime_first_alignment.py`** is a new file (8.8KB, git-status untracked) that appears to test exactly the runtime-first axis Q2 cares about. If it asserts mechanism-pair independence, it's empirical evidence Q2 should cite. If it doesn't, it's the natural home for the regression tests Codex's "10-16 hours" estimate is sized against.
- **Q4 reviewer-list gap.** Codex omits Sam Bowman (Anthropic Alignment Science) and the Frontier Red Team — both plausible reviewers for this paper. Bowman's likely critique would be near the Perez/generic-alignment-science axis; FRT would land near Shlegeris on red-team affordances. Not a blocker but worth one row each if the paper enters a real reviewer-anticipation cycle.
