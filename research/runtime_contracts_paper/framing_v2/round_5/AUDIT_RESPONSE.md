# Round 5 Audit Response

## Verdict: SHIP_WITH_NOTES

The response is substantively correct across all three questions. Every
primary-source claim that is load-bearing for a paper § verified — RBR
arXiv ID, Haiku 4.5 pricing, ST-WebAgentBench 222 tasks + CuP + Risk
Ratio metric names, Deliberative Alignment latency-cost framing, MSM
OOD-generalization-including-agentic-settings, the cost arithmetic, the
L1–L7 family mapping, and consistency with locked decisions D-FRAME-010,
-013, -020, -022 and D-PROJ-016. The findings below are minor: one HS
methodology overgloss (Codex's "optional classifier prompt" stage is its
own elaboration, not in Anthropic's HS post), one manifest-path
ambiguity (the "v2" label has no on-disk artifact under that name, but
the size matches `hai_0_2_0.json`), and a handful of editorial notes.
None of these would change a § in the paper outline or re-open a locked
Phase 1 decision. Two consecutive prior rounds returned
SHIP_WITH_NOTES with no paper-§-level findings; this is the third.

## Findings

### F-AUDIT-5-01 HS "optional classifier" overglossed

- **Severity:** minor
- **Where:** RESPONSE §Q1a "What HS actually is" paragraph + step 3 of
  the call structure (`Optional classifier prompt`).
- **Finding:** The Anthropic post at
  `https://alignment.anthropic.com/2025/summarization-for-monitoring/`
  describes a two-stage pipeline: per-interaction summary →
  aggregate summary for human review. It does not describe a
  third optional classifier stage that "attach[es] a discrete harm
  classification at either the interaction or usage level." Codex's
  step 3 is a reasonable engineering extension but is not in the
  source post. The phrase "It can also attach a discrete harm
  classification at either the interaction or usage level" reads
  as a documented HS feature when it is Codex's own elaboration.
- **Suggested fix:** When Q1a graduates to §2.3 / §7.6 prose, soften
  to: "We extend HS with an optional classifier stage so the
  aggregate can emit a discrete monitor verdict suitable for
  scoring." Or drop step 3 from the methodology recap entirely
  since Codex recommends not using it in the bounded cell anyway.
- **Provenance check:** WebFetched the Anthropic HS post twice (once
  for general structure, once specifically for classifier language).
  Both passes returned summarization + human review only, no
  discrete-classification stage.
- **Paper-§-level?** no — methodology framing only, no § shape
  changes; bounded HS cell is unchanged.

### F-AUDIT-5-02 Manifest "v2" path ambiguity

- **Severity:** minor
- **Where:** RESPONSE §Q1a HS cost-estimate paragraph: "the committed
  v2 manifest is about 189 KB."
- **Finding:** No file named `agent_cli_contract.v2.json` or with a
  "v2" suffix exists in `benchmark/governed_agent_bench/manifests/`.
  The closest match by size is
  `benchmark/governed_agent_bench/manifests/hai_0_2_0.json`
  (188,751 bytes = 188.75 KB decimal, ~184.3 KB binary). If
  Codex means "the v0.2.0 HAI manifest snapshot," 189 KB is
  accurate (decimal). If Codex means "the paper-intended
  `agent_cli_contract.v2` manifest schema" (referenced in Phase 3 of
  HAI_PAPER_READINESS_EXECUTION), no such file exists yet and the
  size estimate is speculative. Round 4 PROMPT.md §199 mentions
  `agent_cli_contract.v2` as a future schema; the v0.2.0 frozen
  snapshot was committed as `hai_0_2_0.json`.
- **Suggested fix:** Reword §Q1a to: "the committed HAI v0.2.0
  manifest snapshot at
  `benchmark/governed_agent_bench/manifests/hai_0_2_0.json` is about
  189 KB." Drop "v2" or clarify it refers to the paper-intended
  manifest schema bump, not the on-disk snapshot.
- **Provenance check:** `find benchmark -name "*v2*"` returned only
  `tasks/l7/gab_l7_stale_v1_manifest_shape.json` (an L7 task
  fixture, not a manifest). `ls manifests/` shows
  `agent_cli_contract_v1_drift.json` (180,625 B / ~177 KB) and
  `hai_0_2_0.json` (188,751 B / ~184 KB binary / ~189 KB decimal).
- **Paper-§-level?** no — cost-estimate prose only; total spend
  conclusion ($10 raw model spend / $200 cap) is unchanged.

### F-AUDIT-5-03 Deliberative Alignment gloss slightly overspecified

- **Severity:** nit
- **Where:** RESPONSE §Q3 paragraph 2: "Deliberative Alignment …
  explicitly argues that simply putting the full spec in the
  deployment prompt has latency and instruction-following
  weaknesses."
- **Finding:** The DA paper (arXiv:2412.16339) explicitly argues
  about **latency cost** of running deliberation over a long
  spec at inference time and about **inferring desired behavior
  from labeled examples** vs from text directly. The
  "instruction-following weaknesses" phrasing is Codex's gloss —
  DA frames the alternative as "inferring indirectly from
  examples" and as latency-overhead at inference. It does not use
  "instruction-following" as the canonical critique.
- **Suggested fix:** When this lands in paper §10 / paper-2 sketch,
  rephrase to "has latency cost and forces the model to infer the
  spec from labeled examples rather than learn it directly" — that
  is closer to DA's own argument.
- **Provenance check:** WebSearch returned DA's own framing:
  "reasoning over pages of safety specifications is overkill for
  benign user prompts" (latency) and "must infer desired behavior
  indirectly from large sets of labeled examples … forces models
  to reverse engineer the ideal behavior" (data efficiency, not
  instruction following).
- **Paper-§-level?** no — paper-2 sketch headline survives intact;
  one-word fix in eventual §11 prose.

### F-AUDIT-5-04 L2 omitted from family-fit lists

- **Severity:** nit
- **Where:** RESPONSE §Q1a "Most usable task families" and "Least
  usable task families" lists.
- **Finding:** Codex enumerates L1, L3, L4, L5, L6, L7 across the
  two lists and omits L2 (setup and recovery / USER_INPUT outputs)
  entirely. BENCHMARK_SPEC.md §44–62 names L2 explicitly as a
  task family with two tasks in the minimum-viable phase. L2
  pattern-fits HS reasonably (HS can summarize whether the agent
  correctly surfaced setup gaps), so silent omission is the wrong
  signal.
- **Suggested fix:** Add one L2 line ("usable but not best-fit:
  HS can summarize whether the agent surfaced setup gaps, but
  deterministic USER_INPUT-shape checks are already cheap"). Or
  state explicitly that L2 is out of scope for bounded contrast.
- **Provenance check:** Read BENCHMARK_SPEC.md §44–62.
- **Paper-§-level?** no — bounded contrast scope (L6 only) is
  unchanged; this is a coverage-prose nit for §7.6.

### F-AUDIT-5-05 Constitutional Classifiers Pareto-precedent un-cited in Q1a

- **Severity:** nit (missing literature)
- **Where:** RESPONSE §Q1a cost / methodology block.
- **Finding:** Constitutional Classifiers (arXiv:2501.18837) is the
  cleanest precedent for the exact metric pair Codex names
  ("detection rate and false-positive rate against deterministic
  contract enforcement"). It is already in CONTEXT_DOSSIER §313 and
  ORCHESTRATOR_STATE D-FRAME-002 prior-art row, so this is
  framing-internal; Codex's §Q1a does not cite it as the canonical
  precedent for that metric shape. The Pareto-frontier framing
  (detection × FP-rate × over-refusal) is exactly what
  Constitutional Classifiers reports.
- **Suggested fix:** When §7.6 prose lands, one sentence: "We
  report detection rate × false-positive rate × uncertain rate
  against the deterministic contract, following the Pareto-frontier
  reporting style of Constitutional Classifiers (arXiv:2501.18837)."
- **Provenance check:** Grep CONTEXT_DOSSIER + ORCHESTRATOR_STATE
  for Constitutional Classifiers — present. WebSearch confirmed CC
  reports detection rate (95.6% jailbreak refusal) + FP rate (0.38%
  over-refusal increase) — the exact metric pair Codex proposes.
- **Paper-§-level?** no — citation density only.

### F-AUDIT-5-06 16–24-hour bounded reimplementation estimate is optimistic

- **Severity:** nit
- **Where:** RESPONSE §Q1a paragraph after the cost table: "Bounded
  L6 reimplementation is much cheaper: 16-24 hours."
- **Finding:** The list — monitor adapter, prompt/scorer pair,
  calibration, FP accounting, citation-validation, integration —
  is realistic for a competent single author at 16–24h *if the
  L6 harness is already done and no iteration is needed*. Iteration
  on the aggregate prompt to get a calibrated binary verdict
  alone is usually a half-day per pass. A more honest range is
  20–35 hours including one calibration loop and FP-accounting
  pass. The two-week wall-clock cap is the real backstop, not the
  hour estimate; the cap absorbs slippage cleanly.
- **Suggested fix:** When this lands in §7.6 implementation notes,
  state the cap rather than the optimistic hour estimate. Or widen
  to 16–35 hours with a calibration-iteration caveat.
- **Provenance check:** Engineering-judgment finding (no primary
  source). Single-author L6-only reimplementation of an LLM
  monitor with calibration is a known underestimation hazard.
- **Paper-§-level?** no — operational note for the cycle plan, not
  a paper claim.

## Citation verification log

| Citation | Verdict | Notes |
|---|---|---|
| arXiv:2411.01111 (RBR) | confirmed | Title "Rule Based Rewards for Language Model Safety", Mu/Helyar/Heidecke/Achiam/Vallone/Kivlichan/Lin/Beutel/Schulman/Weng, NeurIPS 2024. WebFetch verified. |
| HS Anthropic alignment Feb 2025 | confirmed core, F-AUDIT-5-01 on optional-classifier elaboration | Two-stage chunk → aggregate verified; no documented classifier stage. |
| Claude Haiku 4.5 $1/M input, $5/M output | confirmed | Verified at `platform.claude.com/docs/en/about-claude/pricing` model-pricing table. Also Haiku 3.5 confirmed at $0.80/$4. |
| arXiv:2410.06703 (ST-WebAgentBench) | confirmed | Title "ST-WebAgentBench: A Benchmark for Evaluating Safety and Trustworthiness in Web Agents", 222 tasks confirmed, Completion under Policy + Risk Ratio metric names confirmed. |
| arXiv:2412.16339 (Deliberative Alignment) | confirmed core, F-AUDIT-5-03 on "instruction-following" gloss | Latency-cost framing confirmed; "instruction-following weaknesses" is Codex's phrasing, not DA's. |
| MSM `alignment.anthropic.com/2026/msm/` | confirmed | "What and why" of spec, AFT failure-to-generalize, agentic-misalignment reduction all verified. |
| Cost arithmetic | confirmed | One chunk = $0.0575 exact; 5-chunk + aggregate range $0.29–$0.30 verified; simple L6 $0.06–$0.07 verified. |

## Repo / benchmark verification log

| Path:line or symbol | Verdict | Notes |
|---|---|---|
| `benchmark/governed_agent_bench/manifests/hai_0_2_0.json` | exists, 188,751 B (~189 KB decimal) | This is the most likely referent of Codex's "v2 manifest." F-AUDIT-5-02 flags the label ambiguity. |
| `benchmark/governed_agent_bench/manifests/agent_cli_contract.v2.json` | does not exist | Codex's literal phrase has no on-disk artifact. |
| `benchmark/governed_agent_bench/manifests/agent_cli_contract_v1_drift.json` | exists, 180,625 B (~180 KB decimal / ~177 KB binary) | Pre-existing drift manifest, smaller than Codex's 189 KB claim — not the referent. |
| BENCHMARK_SPEC.md §44–50 L1–L7 family rows | matches Codex's mapping | L1 intent routing ✓, L3 daily loop ✓, L4 schema-valid proposal ✓, L5 faithful narration ✓, L6 governance/refusal ✓, L7 contract drift ✓. L2 omitted by Codex (F-AUDIT-5-04). |
| D-FRAME-020 (Haiku 4.5 successor) | matches | ORCHESTRATOR_STATE.md row confirms "claude-haiku-4-5-20251001 named for new cells." |
| D-FRAME-022 (50 trajectories 8/8/8/8/18) | matches | Codex Q1b adversarial row uses the exact allocation breakdown. |
| D-PROJ-016 (HAI freeze) | matches | `project/DECISIONS.md` §30: "HAI is frozen as a product (2026-05-08)." Codex's "violate the spirit of D-PROJ-016" framing is consistent. |
| D-FRAME-010 (paper 2 = S1 fine-tuning RBR + DA lineage) | matches | Codex's S1 framing names exactly RBR + Deliberative Alignment + MSM. |
| D-FRAME-013 (personal wellness = instantiation) | matches | Q1b row 6 ("Benchmark vs instantiation: HAI is one frozen reference runtime and personal wellness is the first instantiation") is consistent. |

## What the response got right

- **Sharpened the load-bearing GAB axis.** "Runtime-mode intervention
  with mechanism-isolable ablation under a held-constant prompt" is
  the right one-sentence positioning against ST-WebAgentBench.
  Reviewers who skim §2.3 will take the right thing away.
- **Bounded HS empirical contrast is the calibrated choice.** Cut
  concedes too much; full L1–L7 reimplementation would not change
  the paper's claim shape. L6 is the right empirical overlap.
- **Coding-agent appendix sketch is the right scope discipline.**
  D-PROJ-016 alignment is correct; the appendix is anti-overclaim
  in tone, and the "must not be cited in abstract / contributions /
  results" guardrail is correctly stated.
- **Paper 2 framing as scale substitution after a runtime floor.**
  This is the right slogan: keeps paper 2 tied to paper 1's claim
  rather than drifting into generic safety fine-tuning. Smaller-
  parameter-count comparison is the load-bearing y-axis.
- **Strongest-critique self-defense reads as honest.** "L6 is the
  right empirical overlap because it tests semantic safety-boundary
  detection without degenerating into exact JSON/schema checking"
  acknowledges the real overlap zone instead of overclaiming
  benchmark-wide dominance.

## Coverage matrix

| Question | Answered? | Quality |
|---|---|---|
| Q1a HS contrast | yes | Recommendation defended with cost arithmetic, two-stage methodology, shared-task-family definition, prompt structure, and scope discipline. F-AUDIT-5-01 (HS classifier gloss) + F-AUDIT-5-02 (manifest path) are minor. |
| Q1b ST-WebAgentBench | yes | 6-row differentiation table with load-bearing axis named ("runtime-mode intervention with mechanism-isolable ablation under a held-constant prompt"). §2.3/§2.4 prose draft provided and ready for related-work edits. |
| Q2 coding-agent | yes | Recommendation (appendix sketch only) defended against cut and full-second-domain alternatives. Sketch is present, ~215 words (verified by reading the prose block — count is in the same order). Appendix earns its place; D-PROJ-016 alignment is explicit. |
| Q3 paper 2 | yes | Headline + 1-paragraph sketch + paper-1-setup requirements (§11 paragraph, schema slot, freeze roster, GAB v2 split, no-private-data recipe, Appendix D recipe description — all six named). F-AUDIT-5-03 (DA gloss) is a one-word fix in eventual prose. |

## Missing literature

- **Constitutional Classifiers (arXiv:2501.18837)** as Pareto-
  reporting precedent for §7.6 metric shape (F-AUDIT-5-05). Already
  in dossier prior-art list — citation density only.
- **Apollo Research "Stress Testing Deliberative Alignment for
  Anti-Scheming Training"** is a natural §11 paper-2 citation for
  the spec-training failure-mode literature. Not blocking.
- For paper 2 small-model alignment via SFT: **Constitutional AI
  (Bai et al. 2022, arXiv:2212.08073)** is the obvious anchor.
  Codex's RBR + DA + MSM trio is correct but anchors heavily on the
  reasoning-model lineage; one CAI mention would strengthen the
  small-model SFT angle.

## Escape-valve calculus

**Count of paper-§-level findings: 0.**

Definition recap: a paper-§-level finding is one that changes a §
in the paper outline or re-opens a locked Phase 1 decision
(D-FRAME-001..023, D-PROJ-016). All six findings above are
editorial / citation-density / methodology-gloss / operational-
estimate. None change §2.3, §2.4, §7.6, §10, §11, Appendix D, or
Appendix E in shape. None re-open a locked decision.

Round 3 returned SHIP_WITH_NOTES with no paper-§-level findings.
Round 4 returned SHIP_WITH_NOTES with no paper-§-level findings.
Round 5 returns SHIP_WITH_NOTES with no paper-§-level findings.

This is the third consecutive SHIP_WITH_NOTES with zero
paper-§-level findings. Recommend: **Phase 1 close by yield
exhaustion.** Phase 2 (paper outline → §-by-§ drafting) should
inherit the six minor findings above as editorial annotations on
the relevant §s, not as Phase 1 open decisions.
