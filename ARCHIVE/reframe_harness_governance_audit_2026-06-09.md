# Reframe dossier: AI-control → AI-engineering "harness governance"

**Status:** decision-in-progress, 2026-06-09. NOT yet reflected in
`PAPER.md`, `AGENTS.md`, or any README. This file exists so a second
agent (Codex) can independently deep-research and AUDIT the proposed
reframe before any repo edits. It is provenance/working material under
`ARCHIVE/`, not an active planning doc (D-13 holds).

The audit's job is to **re-derive and disagree where warranted**, not to
ratify. If the framing is wrong, say so with citations.

---

## 1. The proposed decision

Pivot the preprint's **external framing** from AI-control / AI-safety to
**pure AI-engineering "harness governance."** The empirical core does NOT
change: M4-M8 mechanism ablation, deterministic offline scorer, 28 tasks,
static/live evidence tiers, calendar, USD-300 cost ceiling, model roster
(Qwen2.5-7B/32B) all stay frozen. This is prose / positioning only.

**Current (to be replaced):**
- Title: *Deterministic Software Contracts as Trusted Monitors in AI Control Protocols*
- Home lineage: Greenblatt et al. AI control protocols; OpenAI/Anthropic
  model specs; Constitutional Classifiers / Hierarchical Summarization as
  LLM-monitor contrast.
- Invariant: "this is an AI control paper under the AI safety umbrella; do
  not soften."

**Proposed (refined after the Codex audit, 2026-06-09 — see §11):**
- **Title:** *Measuring Deterministic Governance Mechanisms in Agent
  Harnesses.* (Earlier draft "Isolating the Deterministic Governance
  Mechanisms That Improve Agent Performance" was dropped: "Improve Agent
  Performance" re-collides with the capability-harness crowd.)
- **Thesis (one sentence):** *Agent harnesses are usually engineered to
  make models more capable; holding the model and prompt fixed, we treat
  the runtime mode as the intervention and measure the marginal
  contribution of individual deterministic governance mechanisms to
  reliable, constraint-respecting operation.*
- **North star:** HAI is the first deterministic, mechanism-isolable
  **governance layer** of an agent harness, evaluated by *measured
  per-mechanism attribution*. AI-engineering register; vocabulary is
  **"harness"** (not "environment"/"scaffold"). Governance is **retained
  as an engineering layer** (the ETCLOVG Governance/Verification layer),
  NOT as an AI-control / trusted-monitor / safety umbrella.

## 2. Reasoning chain (how we got here)

1. **Why pivot at all.** The AI-control title promises a control safety
   case the experiment explicitly disclaims (threat model is capability
   failure + a bounded 16-trajectory adversarial layer, *not* scheming /
   sandbagged / password-locked models). A reviewer reads that mismatch
   as "this isn't a real control eval." Dropping the AI-control frame
   removes that overclaim attack surface. Dom is also more invested in the
   harness-engineering thesis and more likely to finish it.
2. **Career trade-off, accepted.** The AI-control frame was the most
   Anthropic-safety-RE-legible thing about the project; the
   AI-engineering frame trades that for general AI-engineering legibility.
   Dom made this call consciously.
3. **First instinct ("pure AI-engineering, no safety umbrella at all")
   was refined.** "Governance" is a first-class layer in the field's own
   harness taxonomy (ETCLOVG) and is exactly where HAI's contract sits;
   the benchmark is already *GovernedAgentBench*. So governance returns
   *as engineering*, not as a safety umbrella. The Greenblatt /
   trusted-monitor / model-spec apparatus is gone.
4. **The novelty axis is capability-vs-governance, not harness-vs-model.**
   "The harness matters more than the model" is already established and
   occupied (see §3). The unoccupied axis is: harnesses have been studied
   as *capability* instruments; nobody has treated the harness as a
   *governance* instrument and measured it per-mechanism. The thesis hook
   is anchored there deliberately.

## 3. Deep-research findings (workflow run 2026-06-09)

A 5-angle deep-research workflow (24 sources fetched, 114 claims
extracted, 25 adversarially verified, 5 killed) returned:

- **The broad "optimise the harness, not the model" thesis is NOT novel.**
  Established by SWE-agent (ACI), the Agent Harness Engineering survey
  ("harness is the binding constraint"), OpenAI "harness engineering,"
  LangChain DeepAgents. A paper restating this as its contribution reads
  as derivative.
- **Closest prior art: Life-Harness** (arXiv 2605.22166), literally titled
  *"Adapting the Interface, Not the Model."* Near-collision on vocabulary
  (environment contracts, action realization) and the held-model premise.
- **Second: ALIGN** (arXiv 2505.21055), generates an interface wrapper
  while holding agent logic + environment constant.
- **Deterministic enforcement systems** (AgentSpec, Invariant Guardrails,
  Guardrails AI) are rule-modular but do NOT publish per-mechanism causal
  ablations; LLM-based guardrails (NeMo safety rails) are non-deterministic.
- **Methodological threat: the harness coupling problem** (survey §11.3):
  mechanisms are coupled; one can look beneficial in isolation while
  degrading the full rollout, so per-mechanism attribution can mislead.
- **REFUTED / do-not-cite:** a claimed "NLAH / Pan et al. 2026" harness-
  ablation framework was almost certainly hallucinated by a search agent
  (1-2 on re-vote, unverifiable). Do not chase or cite it. Also softened:
  claims that AgentSpec/Invariant are *purely* deterministic.

## 4. Direct primary-source verification (read the papers, not the summary)

- **Life-Harness (2605.22166):** confirmed title. Frozen model; interface
  interventions are **evolved** from trajectories (not hand-authored);
  dependent variable is **capability** (88.5% avg relative improvement);
  **no** governance/validation/refusal/audit vocabulary; their
  "deterministic" modifies the *environments*, not the enforcement layer.
  Collision is real on the broad thesis + layer-name vocabulary, bounded
  on method and dependent variable.
- **ALIGN (2505.21055):** holds agent + environment constant; the
  generated interface **enriches observations** (additive/informational),
  does NOT constrain/refuse; capability gain (+45.67% ALFWorld); no
  per-mechanism ablation. Weak collision.
- **Benchmarks:** ST-WebAgentBench (2410.06703) scores policy compliance
  **post-hoc** (no runtime enforcement, no ablation); AgentDojo
  (2406.13352) is prompt-injection attack/defense; tau-bench (2406.12045)
  varies the **model** (deterministic DB-state outcome check, but policies
  are guidelines not ablated runtime gates). **No benchmark uses
  runtime-mode mechanism ablation as its intervention.**

## 5. The three differentiators (what HAI uniquely owns)

1. **Deterministic governance** — vs Life-Harness/ALIGN/SWE-agent
   (capability) and vs LLM-based guardrails (non-deterministic).
2. **Per-mechanism isolation under a held prompt** — vs whole-layer /
   aggregate (Life-Harness, ALIGN) and vs post-hoc scoring
   (ST-WebAgentBench).
3. **A released mechanism-isolable benchmark** (GovernedAgentBench) whose
   intervention is the runtime mode — unoccupied territory.

Positioning rule: cite Life-Harness + ALIGN up front, state the delta in
one sentence. Do NOT use any "X, Not the Model" title (Life-Harness's
verbatim title).

## 6. Threat to defend in the paper

The coupling problem (§5/§3 above) is the real risk to the headline
attribution claim (H1). Planned defense: report BOTH isolated-mechanism
deltas AND full-stack rollouts, and frame every attribution as "marginal
contribution within this fixed controller," not context-free causality.

## 7. Frozen vs reframed

| Frozen (byte-for-byte) | Reframed (prose only) |
|---|---|
| M4-M8/M9-TX IDs, scorer, `scorer_config.paper_v1.json`, `safety_constrained_subset.json`, 28 tasks, trajectories, test names, calendar, cost ceiling, model roster, H1-H6 IDs + substance | Title, thesis, North Star, lineage/related-work, §1/§2 outline labels, threat-model caveat, "safety-constrained" → "constraint-enforcing", M7 "clinical-boundary refusal" → "scope-boundary enforcement", the safety-umbrella invariant |

## 8. Decision reversals this entails

- **D-02** (locked title) superseded by a new **D-26** (framing pivot).
- The "AI control paper under the safety umbrella, do not soften"
  invariant in `AGENTS.md` and `PAPER.md` is reversed (governance retained
  as an *engineering* layer, AI-control/trusted-monitor apparatus dropped).

## 9. Sources (for the auditor to re-verify)

- Life-Harness — arXiv 2605.22166
- ALIGN — arXiv 2505.21055
- SWE-agent — arXiv 2405.15793 (NeurIPS 2024)
- Agent Harness Engineering survey (ETCLOVG taxonomy; coupling problem
  §11.3) — OpenReview, under TMLR review (cite as preprint)
- CoALA — arXiv 2309.02427 (TMLR)
- AgentSpec — arXiv 2503.18666
- Invariant Guardrails — github.com/invariantlabs-ai/invariant
- Guardrails AI — github.com/guardrails-ai/guardrails
- NeMo Guardrails — arXiv 2310.10501
- ST-WebAgentBench — arXiv 2410.06703 (ICML 2025)
- AgentDojo — arXiv 2406.13352
- tau-bench — arXiv 2406.12045
- DO NOT CITE: "NLAH / Pan et al. 2026" (likely hallucinated; unverifiable)

## 10. What the audit must decide

Independently (re-derive, do not echo §1-§9):

1. Is the proposed framing **correct**? Keep / refine / replace.
2. Is there prior art we missed that pre-empts the *narrow* claim
   (per-mechanism causal attribution of deterministic governance
   mechanisms under a held prompt + released benchmark)? Search hard.
3. Is the **coupling problem** fatal to the per-mechanism attribution, or
   is the planned defense sufficient?
4. Is dropping the safety/AI-control umbrella **wise**, given governance
   is a first-class harness layer? Or should some governance/verification
   framing be retained more strongly?
5. Are the **title** and **thesis** optimal, or can they be sharpened?
6. Does **GovernedAgentBench** genuinely differentiate from the named
   benchmarks on runtime-mode ablation?

Output: a clear recommendation with citations to primary sources, flagging
anything that cannot be verified.

---

## 11. Audit reconciliation (Codex, 2026-06-09)

Codex ran the audit end-to-end and returned a **REFINE** verdict. It
corrected real errors in §1-§10 above; the maintainer side-verified the
two most load-bearing corrections directly (NLAH and Agent Behavioral
Contracts, both confirmed real by reading the arXiv pages). The audit's
corrections are accepted. §1's title/thesis already reflect the refinement.

**Accepted corrections to this dossier:**

1. **"NLAH / Pan et al." is NOT hallucinated.** *Natural-Language Agent
   Harnesses*, Pan et al., **arXiv 2603.25723** is real: treats the
   harness as a first-class object, ablates harness modules. It is
   LLM-executed (Intelligent Harness Runtime interpreting natural-language
   policy) and capability-focused, so it does not pre-empt deterministic
   governance, but it kills any "first to ablate the harness" claim. The
   deep-research workflow's verifier false-refuted it; do NOT repeat that.
2. **The field is much more crowded than §3-§5 implied.** Load-bearing
   neighbors the workflow missed, all verified by Codex (and to be
   re-checked before citing): Agent Behavioral Contracts (2602.22302),
   Guardrails as Infrastructure (2603.18059), ContextCov (2603.00822),
   Verifier Tax (2603.19328), SafeAgent (2604.17562), Agentic Harness
   Engineering (2604.25850), HARBOR (2604.20938), Meta-Harness (2603.28052),
   AutoHarness (2603.03329), NLAH (2603.25723), plus AgentSpec/Invariant/
   Guardrails-AI/NeMo already known.
3. **Closest prior to our novelty: Agent Behavioral Contracts** (arXiv
   2602.22302), confirmed real. Runtime-enforceable contracts
   `C = (P, I, G, R)` (G = Governance), contracted-vs-uncontracted across
   7 models, AgentAssert runtime enforcement, AgentContract-Bench (200
   scenarios). Deltas that keep us distinct: it is patent-pending (benchmark
   availability unclear), uses LLM-judge extraction (not purely
   deterministic), and does NOT do a hidden `runtime_mode` intervention
   under a held deployment prompt with an offline deterministic scorer.
   This must be cited and distinguished in §2.
4. **Life-Harness and ALIGN DO ablate** (layer-level / component-level).
   §4's "no per-mechanism ablation" was overstated. The real delta is
   capability-vs-governance and evolved/LLM-generated-vs-deterministic.
5. **Venue fix:** ST-WebAgentBench is **ICLR 2026** (arXiv 2410.06703 v7),
   not ICML 2025. PAPER.md's Lineage Anchor cites it as ICML 2025 — fix on
   the reframe pass.

**Refined novelty claim (narrower than §3 said).** No single source has
the full conjunction: held model AND prompt + hidden `runtime_mode`
intervention + deterministic governance mechanisms toggled individually +
offline deterministic scorer + released mechanism-isolable benchmark. That
conjunction survives. But the paper must avoid every "first X" claim
(first harness ablation, first fixed-model attribution, first runtime
governance, first software-contract framing, first governance benchmark)
and report causal language as conditional on this one fixed controller,
prompt, runtime, task suite, and evidence tier.

**Coupling-problem defense (sufficiency conditions per the audit).** Not
fatal, but fatal to additive/context-free attribution. The paper must
report: isolated `full_contract` vs `no_X` contrasts; full-stack rollouts;
`no_runtime_enforcement` only as a sanity floor; explicit
interaction/coupling limitations; and NO additive "M4 contributes A plus
M5 contributes B" language.

**Biggest underweighted risk (audit's headline).** Not "no prior work
exists" — the opposite. Too much prior work exists for every *broad*
version of the claim. The paper survives only by narrowing to the
conjunction above and keeping causal language conditional.

**Framing confirmed:** drop the AI-control umbrella (it promises a
scheming/subversion safety problem GAB does not test); retain governance/
verification as the *engineering* object (ETCLOVG Governance/Verification
layers); do not drop governance context entirely (it would hide the
closest priors). GovernedAgentBench differentiates from ST-WebAgentBench /
AgentDojo / tau-bench / OS-Harm / SafeAgentBench on `runtime_mode` as the
intervention — confirmed.
