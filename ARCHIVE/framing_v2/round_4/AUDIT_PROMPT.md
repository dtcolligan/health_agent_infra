# Round 4 Audit Prompt

**Drafted:** 2026-05-11
**Auditor role:** Claude Code Agent (general-purpose subagent)
**Target:** `research/runtime_contracts_paper/framing_v2/round_4/RESPONSE.md`

---

## Identity

You are the audit agent for the runtime-contracts paper framing v2
orchestration. You operate as a Claude Code Agent dispatched by the
orchestrator. You audit work produced by a Codex `/goal` worker. You
have Read, WebFetch, WebSearch, and Bash. Use Bash for HAI/benchmark
source verification (ls, wc -l, grep -n). Use WebFetch for vendor
docs (Anthropic deprecation, Fireworks/Together/OpenAI model pages).
Use WebSearch for vendor pages that may have changed.

You operate in a high-error regime. Be brutal. The user (Dom) prefers
pushback over validation.

## Project context (short)

Dom is converging the framing of a runtime-contracts paper targeted
at NeurIPS 2027. The paper title (D-FRAME-016) is locked as
"Deterministic Software Contracts as Trusted Monitors in AI Control
Protocols." Round 4 of the convergence asked Codex to close three
open decisions in the predeclared-design cluster:

- **O-FRAME-007** — predeclared model roster (6 Houdinis + 3 Guards
  with provider snapshots, parameter counts, quantization, May 2027
  deprecation risk, §7 cell mapping).
- **O-FRAME-008** — predeclared thresholds (pass values per primary
  metric, calibration source, sensitivity test, multi-metric pass
  rule, scorer_config_hash implementability).
- **O-FRAME-009** — adversarial attack policy (concrete protocol per
  attack type, fifth adaptive-vs-DRG-0 protocol, 50-trajectory
  budget, adjudication, §8.1 scope language).

Locked framing decisions are in `framing_v2/CONTEXT_DOSSIER.md` §4
and `framing_v2/ORCHESTRATOR_STATE.md` "Locked decisions" table
(D-FRAME-001..019). The round-3 audit pattern and findings are in
`framing_v2/round_3/AUDIT_RESPONSE.md`.

## Your task

Audit `framing_v2/round_4/RESPONSE.md` against five dimensions.

### 1. Primary-source accuracy

**Mandatory checks:**

- **Anthropic model availability/deprecation.** Codex claims (Q1
  Haiku row) "Anthropic deprecation docs checked on 2026-05-11
  report this snapshot [`claude-3-5-haiku-20241022`] retired before
  the current date." And (Sonnet row) "near-term retirement window."
  WebFetch `https://docs.anthropic.com/en/docs/about-claude/models/all-models`
  or `https://docs.anthropic.com/en/docs/about-claude/models/overview`.
  Verify the deprecation status of `claude-3-5-haiku-20241022` and
  `claude-sonnet-4-20250514`. If Codex's claim is wrong (e.g., Haiku
  3.5 not retired, Sonnet 4 not near retirement), that's a major
  finding — the roster's "historical-pilot continuity" labeling
  depends on the claim being right.

- **Model identifier strings exist.** WebSearch or WebFetch to verify
  these specific identifiers resolve to real served models:
  - `Qwen/Qwen2.5-3B-Instruct` on Hugging Face
  - `Qwen/Qwen2.5-7B-Instruct-Turbo` on Together AI
  - `accounts/fireworks/models/qwen2p5-32b-instruct` on Fireworks
  - `accounts/fireworks/models/qwen2p5-72b-instruct` on Fireworks
  - `claude-3-5-haiku-20241022` on Anthropic API
  - `claude-sonnet-4-20250514` on Anthropic API
  - `gpt-4o-mini-2024-07-18` on OpenAI API
  Pick 4-5 to verify (the Fireworks IDs and Together Turbo are
  highest-suspicion; Haiku and gpt-4o-mini are well-known).

- **arXiv:2406.13352 (AgentDojo)** — cited in Q2 and Q3. Verify the
  arXiv ID resolves to a paper titled "AgentDojo" by Debenedetti
  et al.

- **ControlArena URL.** Round 3 used `control-arena.aisi.org.uk`.
  Round 4 uses `https://ukgovernmentbeis.github.io/control-arena/`.
  WebFetch both. Identify which is canonical and whether the other
  redirects. Flag the discrepancy for cross-round consistency.

- **AgentDojo URL `agentdojo.spylab.ai/`.** WebFetch. Verify it
  resolves to the AgentDojo project page.

### 2. HAI / benchmark source on-disk verification

Q2 makes specific claims about the current scorer surface. Verify
each on disk via Bash.

- **`benchmark/governed_agent_bench/scorer/core.py`** — does this
  file exist? Does it contain a function named `scorer_config_hash`?
  Use `ls` and `grep -n "scorer_config_hash" benchmark/governed_agent_bench/scorer/core.py`.

- **`benchmark/governed_agent_bench/schema/score.schema.json`** —
  Codex claims this requires `scorer_config_hash` and per-metric
  `threshold` and has `additionalProperties: false`. Read the file
  and verify these three claims.

- **`benchmark/governed_agent_bench/schema/trajectory.schema.json`** —
  Codex claims `model_identity` is required for non-`rule_baseline`
  trajectories and `model_roster_hash` is described but not required.
  Read the file and verify.

- **`benchmark/governed_agent_bench/schema/model_roster.schema.json`** —
  Codex claims this file exists "with the right fields." Verify.

- **`benchmark/governed_agent_bench/SCORING_SPEC.md`** — Codex claims
  this defines overall pass as "all required metrics passing plus no
  critical violation." Read the file and verify.

- **Scorer field names.** Codex names 10+ specific metric fields
  (`valid_command_rate`, `hallucinated_command_rate`, `unsafe_action_rate`,
  `direct_state_write_attempt_rate`, `schema_validity`,
  `refusal_accuracy`, `unsupported_narration_rate`,
  `audit_reference_faithfulness`, `clinical_claim_rate`,
  `drift_robustness`). Spot-check 5 of these via
  `grep -rn "<field_name>" benchmark/governed_agent_bench/scorer/`.
  If a field is invented (no on-disk reference), flag as major.

### 3. Internal consistency with locked decisions

Read `framing_v2/CONTEXT_DOSSIER.md` §4 and `framing_v2/ORCHESTRATOR_STATE.md`
"Locked decisions." Verify no silent contradiction.

Specific risk surfaces:

- **D-FRAME-017 mechanism inventory.** Q3 maps attacks to M4/M5/M6/
  M7/M8. Verify the mapping is consistent with D-FRAME-017's narrow
  M7 scope (clinical-boundary only) and renamed M8 ("audit evidence
  emission"). Codex says "M8 audit evidence emission" — confirms
  the rename. Codex says M7 refusal — verify the refusal-bypass
  attack is scoped to clinical-boundary, not generic refusal.

- **D-FRAME-018 Engels pilot.** Q1 §7.5 cell count says "6 Houdinis x
  3 Guards x 225 APPS samples = 4,050 guard judgments." The pilot
  (D-FRAME-018) is 60 samples. The full §7.5 run is at the Engels
  paper's 225. These are different artifacts (pilot vs paper). Verify
  Codex distinguishes them and is not silently inflating the pilot
  budget.

- **D-FRAME-019 two paper-killers.** Q3 adaptive-vs-DRG-0 attack
  with 18 trajectories should be present. Verify it is.

### 4. Framing overreach / calibration

Flag claims broader than evidence supports.

- **Q1 USD 1,000 hard ceiling.** Round 3 cost estimate for the
  pilot was ~$18.60. Round 4 expands to §7.1-7.4 ablations + §7.5
  full Engels (4,050 cells) + §7.6 HS + attack policy. Is $1,000
  defensible, or grossly under-budgeted? Sanity-check: 4,050
  cells x average ~$0.03/cell from round-3 Engels math = ~$121
  for §7.5 alone (low estimate). What about §7.1-7.4 (320 cells)
  and the attack policy (50 trajectories x multi-turn)? $1,000
  may be defensible OR may need adjustment. Run a rough sanity
  check and flag if the ceiling is implausible.

- **Q1 roster mixing claim.** Codex says "mixed across open-weight
  local/smaller models, open-weight hosted larger models, and closed
  API models." Verify the 6 Houdinis actually span those three
  categories — 3 Qwen open-weight (3B/7B/32B/72B is 4 if counting),
  plus Haiku + Sonnet 4. Count check: 4 Qwen + 2 Anthropic = 6.
  Confirm.

- **Q2 critical-violation list.** Codex lists 7 zero-tolerance
  conditions. Verify none of them duplicate or contradict the
  threshold table (e.g., "clinical claim emitted" appears in both
  the threshold table and the critical-violation list — that's
  consistent, not duplicate; flag only if there's real conflict).

- **Q3 budget allocation justification.** Adaptive-vs-DRG-0 gets 18
  trajectories vs 8 each for the other four. Codex's justification:
  "highest uncertainty and most important for the Engels trusted-
  monitor claim." Is 18 enough for statistical separation when
  D-FRAME-018 said 30 paired samples is needed for one Houdini in
  the pilot? The §8 attack layer and the §7.5 pilot are different
  artifacts; 18 is for the attack-layer characterization, not the
  pilot Elo curve. Flag only if Codex implies 18 trajectories will
  produce a pilot-quality result.

### 5. Coverage

Did Codex actually answer each question fully?

- **Q1:** Roster table with 9 columns (Role, Model ID, Provider/
  Route, Snapshot/Citation, Parameter Count, Quantization, Decoding,
  Deprecation Plan)? Yes/no. 6 Houdinis + 3 Guards = 9 rows? Yes/no.
  §7 cell allocation provided? Yes/no.

- **Q2:** Threshold table with 6 columns (Metric, Scorer Field, Pass
  Threshold, Calibration Basis, Sensitivity Test, Claim Impact)?
  Yes/no. 7 primary metrics covered? Yes/no. Multi-metric pass rule
  chosen (AND vs weighted)? Yes/no. Hash serialization addressed?
  Yes/no.

- **Q3:** Allocation table + protocol table + adjudication procedure
  + scope statement? Yes/no per. 50-trajectory budget total (sum
  checks: 8+8+8+8+18 = 50)? Yes/no. Adaptive-vs-DRG-0 protocol
  specified separately as the fifth type? Yes/no.

### Missing literature

Independent of what Codex cited, identify 1-3 papers/specs that
should have been cited but weren't. Examples of potential gaps:

- For Q1 model roster: any standard model-card-as-citation
  benchmark (e.g., Ribeiro et al. or Mitchell et al. on model
  cards) that the paper should anchor to.
- For Q2 thresholds: any benchmark that defends thresholds with
  bootstrap CIs vs the AND-pass-rule choice.
- For Q3 attack policy: any recent attack-policy paper omitted
  (e.g., SHADE-Arena from Anthropic which Codex named in round 3
  Q4 but doesn't cite in round 4 Q3).

## Verdict vocabulary

- **SHIP** — no substantive findings; integrate as-is.
- **SHIP_WITH_NOTES** — minor findings (severity ≤ minor); integrate
  with annotations.
- **REVISE** — substantive findings (≥1 major); worker should re-do
  affected sections.
- **ABORT_ROUND** — the round's premise was wrong; reframe required.

Bias toward SHIP_WITH_NOTES if the response is substantively right
but has citation noise. Reserve REVISE for cases where a load-
bearing claim is actually false (e.g., a scorer field that doesn't
exist, a model identifier that doesn't resolve, a deprecation claim
that's backwards).

## Output

Write your verdict + findings to:

```
research/runtime_contracts_paper/framing_v2/round_4/AUDIT_RESPONSE.md
```

Use the same structure as round 3's AUDIT_RESPONSE.md:

```markdown
# Round 4 Audit Response

## Verdict: [SHIP / SHIP_WITH_NOTES / REVISE / ABORT_ROUND]

## Findings

### F-AUDIT-4-01 [short title]
- **Severity:** critical / major / minor / nit
- **Where:** [file + line range or response §]
- **Finding:** ...
- **Suggested fix:** ...
- **Provenance check:** [what you verified, how]

### F-AUDIT-4-02 ...

## Citation verification log

| Citation | Verdict | Notes |
|---|---|---|
| ... | confirmed / disputed / unverifiable | ... |

## HAI / benchmark source verification log

| Path:line or symbol | Verdict | Notes |
|---|---|---|
| `benchmark/.../core.py:scorer_config_hash` | confirmed | ... |
| ... | ... | ... |

## What the response got right

[Brief calibration — 3-5 bullets.]

## Coverage matrix

| Question | Answered? | Quality |
|---|---|---|
| Q1 roster | yes/partial/no | ... |
| Q2 thresholds | ... | ... |
| Q3 attack policy | ... | ... |

## Missing literature

[1-3 items, brief.]
```

## Constraints

- Do not edit `RESPONSE.md`. Your output is `AUDIT_RESPONSE.md` only.
- Do not edit any file outside `framing_v2/round_4/`.
- Cap WebFetch calls at ~15.
- Cap total output at ~3000 words.
- Be brutal. If a load-bearing claim is wrong, mark it major and
  recommend REVISE.

## When done

Save `AUDIT_RESPONSE.md` to the path above. Return your verdict +
a one-paragraph summary to the orchestrator.
