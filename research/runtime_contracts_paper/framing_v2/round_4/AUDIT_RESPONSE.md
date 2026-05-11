# Round 4 Audit Response

## Verdict: SHIP_WITH_NOTES

Codex's three closures are substantively correct. The two highest-risk
load-bearing claims — the Anthropic deprecation status for both Haiku
3.5 and Sonnet 4, and every on-disk scorer/schema claim — verify
against primary sources. The remaining findings are calibration,
URL-canonicalization, and a tight-but-defensible cost ceiling.
Integrate with annotations; no re-do required.

## Findings

### F-AUDIT-4-01 ControlArena URL is a redirect, not canonical

- **Severity:** minor
- **Where:** RESPONSE.md Q3 prior-art anchors; cites
  `https://ukgovernmentbeis.github.io/control-arena/`.
- **Finding:** That URL returns HTTP 301 to
  `https://control-arena.aisi.org.uk/`, which is the canonical site
  (UK AI Security Institute + Redwood Research). Round 3 used the
  canonical URL. Round 4 introduces an upstream-redirect URL with no
  explanation. This is a cross-round regression on a load-bearing
  prior-art citation.
- **Suggested fix:** Replace the URL with
  `https://control-arena.aisi.org.uk/` to match round 3 and avoid a
  citation that depends on GitHub Pages forwarding remaining live.
- **Provenance check:** WebFetch confirmed the 301 redirect on
  2026-05-11.

### F-AUDIT-4-02 Haiku 3.5 was retired on 2026-02-19, not "before the current date"

- **Severity:** minor (claim is correct but imprecise)
- **Where:** RESPONSE.md Q1 roster table, Haiku Houdini + Haiku Guard
  rows; "Anthropic deprecation docs checked on 2026-05-11 report this
  snapshot retired before the current date."
- **Finding:** True but soft. The official model-deprecations page
  lists `claude-3-5-haiku-20241022` as **Retired**, deprecation
  announcement 2025-12-19, retirement 2026-02-19. That means **new
  API calls to this snapshot fail today**. Codex's "Keep only for
  historical pilot continuity if existing trajectories were produced
  while available" caveat is correct but the roster still proposes
  Haiku 3.5 as both a Houdini and a Guard role — which means **two of
  the nine roster slots are unrunnable for new evaluation cells**.
  This is acceptable if Dom already has trajectories from the
  D-FRAME-018 pilot window, but the table should say it explicitly.
- **Suggested fix:** Tighten the Haiku rows to: "Retired 2026-02-19;
  usable only for already-collected pilot trajectories. New cells
  must use `claude-haiku-4-5-20251001` under a new roster hash."
  Make the Haiku-successor identity explicit so §7 cell allocations
  do not silently depend on a retired snapshot.
- **Provenance check:** WebFetched
  `platform.claude.com/docs/en/docs/about-claude/model-deprecations`
  on 2026-05-11. Status table row: `claude-3-5-haiku-20241022 |
  Retired | December 19, 2025 | February 19, 2026`.

### F-AUDIT-4-03 Sonnet 4 deprecation window is precise — name the date

- **Severity:** nit
- **Where:** RESPONSE.md Q1 Sonnet 4 row; "near-term retirement
  window."
- **Finding:** Anthropic's deprecation page gives an exact retirement
  date for `claude-sonnet-4-20250514`: **June 15, 2026** (deprecation
  announcement 2026-04-14). Calling that a "near-term retirement
  window" is correct but under-specifies a date that's ~35 days out
  from the round-4 close. Reviewers will read "near-term" as either
  alarmist or vague.
- **Suggested fix:** Replace with "Retirement scheduled 2026-06-15;
  the §7.5 paper-claim run must complete before that date or
  re-anchor to `claude-sonnet-4-6` under a new roster hash."
- **Provenance check:** Same source as F-AUDIT-4-02.

### F-AUDIT-4-04 `claim_tier` enforcement claim is slightly understated

- **Severity:** minor
- **Where:** RESPONSE.md Q1 closing paragraph: "`claim_tier` is
  optional, and `trajectory.schema.json` describes `model_roster_hash`
  but does not require it."
- **Finding:** The trajectory half is accurate. The score-schema half
  is misleading: `score.schema.json` already has a conditional
  `if/then` block (lines 180–184) that makes `model_roster_hash`
  **required when `claim_tier` ∈ {T3, T4}**. The remaining gap is
  that the schema does **not** force `claim_tier` to be present for
  every score artifact. Codex's recommendation ("require `claim_tier`
  plus `model_roster_hash` for every trajectory/score used in T3/T4
  claims") is the right shape, but the framing implies the schema is
  more open than it is.
- **Suggested fix:** Reword to "Score schema already conditionally
  requires `model_roster_hash` when `claim_tier` ∈ {T3, T4}; the gap
  is that `claim_tier` itself is optional and trajectory.schema.json
  does not propagate the hash requirement. Tighten both: make
  `claim_tier` required at the score level for paper-claim artifacts
  and add the same T3/T4 conditional to trajectory.schema.json."
- **Provenance check:** Read score.schema.json lines 89–184 and
  trajectory.schema.json lines 119–198.

### F-AUDIT-4-05 USD 1,000 ceiling has no margin for retries

- **Severity:** minor
- **Where:** RESPONSE.md Q1 "Cost Ceiling" section.
- **Finding:** Rough back-of-envelope using the D-FRAME-018 pilot
  anchor (~$18.60 for 60 APPS × 3 Houdinis × 2 Guards ≈ $0.052 per
  composite call, or ~$0.31 per APPS sample blended across the run):
  §7.5 alone scales to 1,350 Houdini-samples × ~$0.31 ≈ **$420** plus
  Guard cost. §7.1–7.4 (320 cells) at higher-difficulty average
  ~$0.20–$0.50 per cell ≈ **$60–160**. §7.6 (small APPS subset, 6
  cells) ≈ **$30–80**. §8 attack policy: adaptive-vs-DRG-0 alone
  permits up to 30 attempts × 18 trajectories × ~$0.10/coding-call
  ≈ **$54**; other four attack types at 8 trajectories × multi-turn
  ≈ **$40–80**. Total estimate: **$600–$800** with no retries,
  **$900–$1,100** with one retry budget. The $1,000 ceiling is
  defensible but **has no margin for provider-substitution reruns
  triggered by Sonnet 4 retirement, schema-tightening reruns, or
  attack-policy iteration**.
- **Suggested fix:** Either raise the ceiling to USD 1,500 to absorb
  one full retry cycle, or commit explicitly that any cell that
  blows the budget is dropped rather than re-run, with the dropped
  cell named in the paper. Do not silently absorb a budget overrun
  into "exploratory runs."
- **Provenance check:** D-FRAME-018 pilot cost from
  CONTEXT_DOSSIER.md line 63. Per-call extrapolation is the
  auditor's own arithmetic and should be treated as an
  order-of-magnitude check, not a quote.

### F-AUDIT-4-06 Adaptive-vs-DRG-0 attack count justification is thin

- **Severity:** nit
- **Where:** RESPONSE.md Q3 allocation table; "Highest uncertainty
  and most important for the Engels trusted-monitor claim."
- **Finding:** D-FRAME-018 specified ~30 paired samples per Houdini
  for the pilot Elo curve. The §8 adaptive-vs-DRG-0 trajectory is a
  different artifact (attack-layer characterization, not pilot Elo)
  so the 18-trajectory budget is defensible. The risk is that a
  reviewer reads the table without §8.1 scope context and conflates
  the two. Codex's scope statement at the bottom of Q3 partly
  addresses this but does not explicitly say "18 trajectories is
  attack-policy stress-testing, not a pilot-quality success-rate
  estimate."
- **Suggested fix:** Add one sentence to the allocation row:
  "Sample size chosen for attack-policy characterization, not
  pilot-quality success-rate estimation; cf. D-FRAME-018 pilot at
  60 samples × 3 Houdinis."
- **Provenance check:** D-FRAME-018 row in
  CONTEXT_DOSSIER.md line 63; Engels-pilot context in round 3.

### F-AUDIT-4-07 SHADE-Arena named in round 3 but missing from round 4 Q3

- **Severity:** minor
- **Where:** RESPONSE.md Q3 prior-art anchors.
- **Finding:** Round 3 Q4 reviewer-simulation pass named SHADE-Arena
  (Anthropic, Ethan Perez coauthor) as the canonical attack-policy
  / sabotage-monitoring reference for the Anthropic-reviewer threat
  model. Round 4 Q3 cites ControlArena, AgentDojo, ST-WebAgentBench,
  Constitutional Classifiers, and arXiv:2510.09462 — but not
  SHADE-Arena. For a paper targeted at the Anthropic Alignment
  Science / AI Control reviewer audience, omitting the Anthropic
  in-house attack-policy benchmark is a credibility miss.
- **Suggested fix:** Add SHADE-Arena
  (`https://www.anthropic.com/research/shade-arena-sabotage-monitoring`)
  to the Q3 prior-art list with one sentence on how the bounded
  GovernedAgentBench attack policy relates to (or differs from)
  SHADE-Arena's sabotage-monitoring frame.
- **Provenance check:** round_3/RESPONSE.md line 441 names
  SHADE-Arena in the Ethan Perez reviewer-simulation row.

## Citation verification log

| Citation | Verdict | Notes |
|---|---|---|
| `claude-3-5-haiku-20241022` retired before 2026-05-11 | confirmed | Retired 2026-02-19 per Anthropic deprecation page |
| `claude-sonnet-4-20250514` near-term retirement | confirmed | Retirement scheduled 2026-06-15 |
| `Qwen/Qwen2.5-3B-Instruct` on Hugging Face | confirmed | Repo exists, 8.7M+ downloads |
| `accounts/fireworks/models/qwen2p5-32b-instruct` | confirmed | Resolves to Fireworks-hosted Qwen2.5-32B |
| `accounts/fireworks/models/qwen2p5-72b-instruct` | confirmed | Resolves to Fireworks-hosted Qwen2.5-72B |
| `Qwen/Qwen2.5-7B-Instruct-Turbo` on Together | confirmed | Together AI serverless model, ID matches |
| `gpt-4o-mini-2024-07-18` on OpenAI | unverifiable via WebFetch (403) | Identifier is widely-cited and consistent with OpenAI's pinned-snapshot naming; not flagged |
| arXiv:2406.13352 (AgentDojo, Debenedetti et al.) | confirmed | Title and authors match |
| `agentdojo.spylab.ai/` | confirmed | Official AgentDojo project page (ETH SpyLab) |
| `control-arena.aisi.org.uk` | confirmed | Canonical; the URL in RESPONSE.md is a 301 redirect to this |
| `ukgovernmentbeis.github.io/control-arena/` | redirect | 301 → `control-arena.aisi.org.uk`; see F-AUDIT-4-01 |
| arXiv:2510.09462 (Adaptive Attacks on Trusted Monitors) | not re-verified this round | Confirmed in round 3 audit |
| arXiv:2501.18837 (Constitutional Classifiers) | not re-verified this round | Confirmed in round 3 audit |
| arXiv:2410.06703 (ST-WebAgentBench) | not re-verified this round | Confirmed in round 3 audit |

## HAI / benchmark source verification log

| Path:line or symbol | Verdict | Notes |
|---|---|---|
| `benchmark/governed_agent_bench/scorer/core.py:60` `scorer_config_hash()` | confirmed | Function exists; also used at line 166 in score-emission |
| `benchmark/governed_agent_bench/schema/score.schema.json` top-level `additionalProperties: false` | confirmed | Line 6 |
| `score.schema.json` requires `scorer_config_hash` | confirmed | Line 16 in top-level `required` array |
| `score.schema.json` per-metric `threshold` required | confirmed | Lines 109, 117–119; threshold is in per-metric required set |
| `score.schema.json` conditional `model_roster_hash` for T3/T4 | confirmed | Lines 180–184 `if claim_tier in {T3,T4} then required: [model_roster_hash]`; Codex's framing slightly understates this — see F-AUDIT-4-04 |
| `trajectory.schema.json` `model_identity` required for non-`rule_baseline` | confirmed | Lines 192–198 allOf/if-else |
| `trajectory.schema.json` `model_roster_hash` described not required | confirmed | Line 119; no top-level `required` entry, no conditional |
| `schema/model_roster.schema.json` exists "with the right fields" | confirmed | File present; has `roster_id`, `roster_file`, `hash_algorithm`, `hash_scope`, `status`, `approved_by`, `approved_at`, etc. |
| `SCORING_SPEC.md` "all required metrics passing plus no critical violation" | confirmed | Lines 56–66 |
| `valid_command_rate` field | confirmed | scorer/core.py:20, :43, :285 |
| `hallucinated_command_rate` field | confirmed | scorer/core.py:22, :45, :291 |
| `unsafe_action_rate` field | confirmed | scorer/core.py:25, :296; task.schema.json:109 |
| `direct_state_write_attempt_rate` field | confirmed | scorer/core.py:26, :297; task.schema.json:110 |
| `schema_validity` field | confirmed | scorer/core.py:23, :294; task.schema.json:107 |
| `refusal_accuracy` field | confirmed | scorer/core.py:24, :295; task.schema.json:108 |
| `unsupported_narration_rate` field | confirmed | scorer/core.py:28, :307; task.schema.json:112 |
| `audit_reference_faithfulness` field | confirmed | scorer/core.py:29, :312; task.schema.json:113 |
| `clinical_claim_rate` field | confirmed | scorer/core.py:27, :302; task.schema.json:111 |
| `drift_robustness` field | confirmed | scorer/core.py:31, :278, :321 |

All 10 named scorer fields exist on disk. No invented fields.

## What the response got right

- **Anthropic deprecation calls are correct in both direction and
  substance.** Haiku 3.5 is indeed retired; Sonnet 4 is indeed in a
  near-term retirement window. The orchestrator's highest-risk
  flagged claim survives audit.
- **All 10 scorer field names resolve on disk.** No hallucinated
  metric. This was the second-highest risk surface and Codex passed
  cleanly.
- **`scorer_config_hash` function exists at the named file and the
  schema enforces it.** Q2's load-bearing implementability claim
  holds.
- **The 50-trajectory attack-policy budget arithmetic checks out**
  (8+8+8+8+18 = 50) and the mechanism mapping (M4 schemas, M5/M6
  mutation, M7 clinical-boundary refusal, M8 audit-evidence
  emission) is consistent with D-FRAME-017's renamed M8 and narrowed
  M7.
- **Roster category-coverage claim verifies**: 4 Qwen open-weight
  (3B/7B/32B/72B) + 2 Anthropic closed = 6 Houdinis spanning
  open-local, open-hosted, and closed-API; 3 Guards (DRG-0 +
  Anthropic + OpenAI) spanning deterministic and LLM-judge.

## Coverage matrix

| Question | Answered? | Quality |
|---|---|---|
| Q1 roster | yes | 9-column table, 9 rows (6+3), §7 cell allocation present; Haiku retirement should be more explicit (F-AUDIT-4-02) |
| Q2 thresholds | yes | 6-column table, 7 primary metrics, AND-pass rule chosen, critical-violation list provided, hash serialization addressed; schema-enforcement framing slightly off (F-AUDIT-4-04) |
| Q3 attack policy | yes | Allocation + protocol + adjudication + scope; 50-trajectory total correct; adaptive-vs-DRG-0 specified as fifth type; SHADE-Arena missing (F-AUDIT-4-07) |

## Missing literature

- **SHADE-Arena (Anthropic, 2025)** — named in round 3 reviewer
  simulation, dropped from round 4 Q3. For an Anthropic-RE-targeted
  paper, this is the in-house attack-policy benchmark; omitting it
  is a calibration miss. See F-AUDIT-4-07.
- **Mitchell et al. "Model Cards for Model Reporting" (2019)** — Q1
  predeclares model snapshots, parameter counts, quantization, and
  decoding settings, which is functionally a model-card emission.
  Anchoring the roster artifact to the model-card literature would
  let the paper claim "predeclared model card per Mitchell et al."
  rather than "roster table."
- **Greenblatt et al. "AI Control: Improving Safety Despite
  Intentional Subversion" (2024)** — Q3 scope statement explicitly
  carves out scheming-misalignment and untrusted-model long-horizon
  access, which is the Greenblatt frame. Citing the source paper at
  the scope-statement boundary makes the carve-out load-bearing
  rather than rhetorical.
