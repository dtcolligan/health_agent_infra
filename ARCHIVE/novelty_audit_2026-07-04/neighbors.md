# Consolidated verified neighbor list (for related-work prose)

Compiled 2026-07-04 (final synthesis pass) from neighbors_0..6.md and
hunt_0..5.md, with primary-source re-verification for every Tier 1
entry. Verification status per entry: FULL-TEXT-LOCAL (verified this
session against a full paper text cached in this directory),
ABSTRACT-THIS-PASS (arXiv abstract fetched verbatim by this synthesis
pass), SWEEP (verified by a sweep agent against primary sources, not
re-derived here). One distinguishing sentence each, written to be
lifted into prose. No entry supports a "first X" claim; the
conjunction is the only novelty claim. Never call any single entry
"the single closest prior."

## Tier 1: closest-prior class (measured told-vs-enforced comparisons or multi-cell designs; cite and distinguish individually)

- **FORGE (arXiv 2602.16708, Palumbo, Choudhary, Choi, Amir,
  Chalasani, Jha; v1 titled "Policy Compiler for Secure Agentic
  Systems")** [FULL-TEXT-LOCAL]. Runs the only located by-design
  enforced-not-told condition ("The instrumented condition does not
  include the natural language policy in the agent's prompt; the
  agent relies solely on runtime enforcement and corrective
  feedback") against a told-not-enforced baseline across three case
  studies and three frontier models, but never a told-and-enforced
  cell or a neither floor, so it cannot measure the redundancy of
  enforcement given specification; its corrective feedback makes the
  enforced arm a converged multi-turn condition rather than
  first-attempt, it evaluates one holistic policy per domain with no
  per-mechanism inventory or moderators, and no public code release
  was located.

- **ABSTAIN, "What Benchmarks Don't Measure" (arXiv 2606.02965,
  Ojewale and Venkatasubramanian, Brown; RLEval workshop paper)**
  [FULL-TEXT-LOCAL]. The closest cell coverage located: Baseline
  (neither), Prompt-Only (told, not enforced), and Checkpoint (told
  and enforced, explicitly reusing the Prompt-Only prompt per its
  Appendix B) across 144 tool-calling scenarios and seven model
  families with a per-gap-type breakdown (specification /
  verification / authority), but for a single abstention/precondition
  mechanism, with no enforced-not-told cell, no moderators, LLM-judge
  scoring outside the Checkpoint condition, and no located code or
  data release in self-described preliminary work.

- **TeamBench (arXiv 2605.07073, Kim et al.)** [ABSTRACT-THIS-PASS].
  Two-arm prompt-only vs OS-sandbox-enforced role-separation
  comparison with a deterministic grader and an 851-template,
  931-instance benchmark, reporting statistically indistinguishable
  pass rates between arms alongside 3.6 times more
  verifier-edits-executor cases in the prompt-only arm, which makes
  it both convergent evidence for the substitution shape in a
  different mechanism domain and a standing caution that aggregate
  parity can mask sub-metric enforcement value; both arms are told
  their roles, one monolithic mechanism, no moderators. (Candidate
  input to the external replication fork; flag to Dom.
  [FORK-H5-REPLICATION: pending; do not write prose assuming its
  outcome.])

- **AIRGuard (arXiv 2605.28914, Qin, Zhuang, Zhou, Han, Zhang)**
  [FULL-TEXT-LOCAL]. Security-framed pre-action runtime guard whose
  prompt-only vs runtime-guard ablation (one model, GPT-5.4-mini,
  DTAP-150 only: ASR 22% no defense, 17% prompt-only, 4% full guard;
  the main results span four backbones) measures a single-axis delta
  in attack success rate, with no factorial, no enforced-not-told
  cell, and no constraint-class analysis; scope any "one model"
  clause to the ablation explicitly.

- **Harness-MU (arXiv 2606.21856, Fan, Nie, Dai)**
  [ABSTRACT-THIS-PASS]. Argues governance constraints "are
  deterministic runtime variables that should be enforced by
  execution hooks rather than entrusted to the LLM" and measures the
  hook-vs-baseline delta on four frontier models on Muses-Bench
  (utility improvement 0.28-0.39, instruction-following accuracy up
  to 48.9 percentage points), but as a single-axis, adversarially
  framed comparison with no factorial, no enforced-not-told cell, and
  access control treated as one undifferentiated surface.

- **ContextCov (arXiv 2603.00822, Sharma)** [ABSTRACT-THIS-PASS].
  Compiles agent-instruction files into executable guardrails (AST
  queries, shell shims, architectural validators) and reports 88.3%
  constraint compliance enforced vs 67.0% prompt-only vs 50.3%
  reflection-only on SWE-bench Lite (12 repositories, 300 tasks) at
  3.4x lower feedback cost, with source code and evaluation results
  released, but as a single-axis comparison whose enforced arm feeds
  violation traces back for self-correction (late in-context telling,
  converged not first-attempt), with no enforced-not-told cell, one
  aggregate compliance number, a single domain, and no moderator or
  harness-blindness analysis. (Promoted out of the background bucket;
  needs its own sentence.)

- **Verifier Tax (arXiv 2603.19328, Sah, Srivastava, Sah, Jordan)**
  [ABSTRACT-THIS-PASS]. Compares unenforced baselines (Tool-Calling,
  TRIAD) against a policy-mediated architecture (TRIAD-SAFETY) on
  tau-bench Airline and Retail with GPT-OSS-20B and GLM-4-9B: safety
  mediation intercepts up to 94 percent of non-compliant actions yet
  safe success stays below 5 percent in most settings, with agents
  hallucinating user identifiers to route around blocks and recovery
  after blocked actions at 21 percent to near zero; no told/untold
  contrast (mediation is architectural, not prompt-toggled), no
  per-mechanism isolation, two small open models. (Promoted out of
  the background bucket; also a strong Discussion citation on
  enforcement under pressure.)

- **TRACE (arXiv 2606.13174, Zhou et al.)** [ABSTRACT-THIS-PASS].
  Compares an in-context Mem0 memory baseline (57.5% of applicable
  preference checks still violated) against user corrections compiled
  into runtime checks, cutting violations to 37.6% in-distribution
  and 2.0% out-of-distribution on ClawArena-derived tasks and 60.5%
  on MemoryArena-derived tasks, with code and a deployable skill
  released, but in the user-preference domain rather than governance
  mechanisms, with the rule always known to the agent in some form
  (no enforced-not-told cell), one aggregate violation rate, and no
  moderators. (Confirmed: "complementary substrates" is not in the
  abstract; do not quote it.)

- **Prompts Don't Protect (arXiv 2605.18414, Uppala; single author,
  no venue)** [FULL-TEXT-LOCAL]. Three-condition adversarial
  tool-access study on 200 tasks (unfiltered / prompted allowlist /
  governed MCP proxy; UIR 48.5-68.5% unfiltered; 37.0%, 4.0%, 11.5%
  prompted for Qwen 2.5 7B, Llama 3.1 8B, Claude Haiku 3.5; 0.0%
  governed) whose governed arm filters unauthorized tools out of the
  model's context with no policy prompt, a structurally
  enforced-not-told condition that is 0% by construction because the
  affordance is removed, so attempted violations cannot be observed;
  single mechanism, no told-and-enforced arm, adversarial framing, no
  located release. (Do not reuse the fabricated 150-task / 11-18pp
  numbers found in some upstream summaries.)

- **Symbolic Guardrails (arXiv 2604.15579, Hong, She, Kang,
  Timperley, Kastner, CMU)** [FULL-TEXT-LOCAL]. Varies
  deterministic-guardrail enforcement on/off while explicitly holding
  the full policy in the system prompt in both conditions ("all
  experimental conditions include the full policy in the system
  prompt," their Section 5.1.5), direct textual confirmation that the
  enforced-not-told cell is absent there, with violation rates of
  20.0% to 78.0% across cells on two models (GPT-4o, GPT-5) pooled
  over 23-34 requirements per benchmark, no per-mechanism breakdown,
  no factorial, no ladder.

- **Mechanical Enforcement (arXiv 2605.14744, de la Chica Rodriguez,
  Marti-Gonzalez)** [ABSTRACT-THIS-PASS]. NEW must-cite: compares
  text-only governance against mechanical enforcement (four
  architectural primitives outside the model's interpretive loop) in
  a regulated-banking decision agent, cutting uninformative deferrals
  by 73% and raising task accuracy from MCC approximately 0.43 to
  0.88; two alternative configurations rather than a crossed
  factorial, no enforced-not-told cell, single financial domain,
  rationale-quality metrics rather than tool-action compliance, and
  the opposite empirical direction from this paper's headline, which
  the Discussion must address rather than leave implicit.

- **PhantomPolicy (arXiv 2604.12177, Wu, Gong, Atlassian)**
  [FULL-TEXT-LOCAL]. Formalizes policy-invisible violations
  (compliance depends on runtime state absent from the agent's
  context) with an eight-category taxonomy this paper adopts and
  crosses with the enforcement axis; it does run a policy-in-prompt
  telling condition (risky-case violations 95.3% to 40.7% under
  human-reviewed labels) but folds it into a single ordinal axis of
  enforcement regimes, with Sentinel and the DLP baseline always
  applied to baseline not-told traces, so no condition holds
  enforcement fixed while varying telling and no enforced-and-told vs
  enforced-and-not-told comparison exists. (CORRECTED: never write
  "no telling axis"; that clause is falsified by their Section 5 and
  Tables 6 and 11.)

- **Agent Behavioral Contracts (arXiv 2602.22302, Bhardwaj)** [SWEEP,
  full text]. Runtime contracts C=(P,I,G,R) evaluated at real scale
  (200 scenarios, 7 models, 1,980 sessions), but its two conditions
  "differ only in whether ABC contract rules are injected and
  enforced" (their Table 6), toggling specification and enforcement
  as one bundled variable with no cell isolating either lever; its
  benchmark is patent-gated, not openly released.

## Tier 2: compliance-gap, capability, and drift evidence (cite for motivation and moderators; no crossed enforcement axis)

- **Governance Decay / ConstraintRot (arXiv 2606.22528, Chen)**
  [ABSTRACT-THIS-PASS; release status and concurrent-work citations
  rest on a hunt full-text read, re-verify before citing]. NEW
  must-cite: in-context governance constraints obeyed while visible
  are silently erased by context compaction, raising violation from
  0% with the policy in full context to 30% after compaction (up to
  59% for some models; 38% when the constraint is dropped from the
  summary, 0% when it survives) across 1,323 episodes and seven model
  families with deterministic tool-call grading, and a training-free
  Constraint Pinning mitigation restores 0%; no runtime-enforcement
  axis exists in any condition, so it establishes the
  drift-causes-violation half of the L7 phenomenon while leaving
  untested whether independent enforcement catches post-drift
  violations. [FORK-L7-DRIFT: that half remains unmeasured; keep the
  stub.] Its cited concurrent works (Gamage 2026; SafeContext, per
  the hunt's full-text read) join the Lineage Anchor with it after
  re-verification.

- **ST-WebAgentBench (arXiv 2410.06703, Levy et al., ICLR 2026 main
  conference poster)** [SWEEP, full HTML + program page]. Closest
  published benchmark prior: in-context ST policies delivered to
  three agent scaffolds (AWM, WorkArena-Legacy, WebVoyager) and
  scored post hoc via Completion Under Policy, with no mechanism that
  blocks a non-compliant action before execution. (Correction: do not
  say "single backbone"; three scaffolds, backbones undisclosed.)

- **SABER (arXiv 2606.01317)** [SWEEP, full text]. Non-monotone
  capability-safety results in stateful coding workspaces (best model
  above 54% harmful-state rate; DeepSeek-V3.2 worse than V3 at 79.6%
  vs 72.4% despite higher capability), with no enforcement condition
  by its own limitations section; cited against any clean
  capability-ordered self-enforcement curve. ("Unsafe success" is
  this paper's gloss, not SABER's term.)

- **LogiSafetyBench (arXiv 2601.08196, Song et al.; real title
  "Evaluating Implicit Regulatory Compliance in LLM Tool Invocation
  via Logic-Guided Synthesis")** [ABSTRACT-THIS-PASS]. LTL-oracle
  compliance benchmark (240 human-verified tasks, 13 models) where
  more capable models complete more and still violate latent
  regulatory rules ("Unsafe Success" is its own term), a prompt-only
  pipeline with no enforcement lever; render the trend as
  "family-dependent, non-monotone scaling" (positive within the
  GPT-5 series, inverse within Gemini, per the results figures), not
  one universal inverse-scaling curve.

- **Agent-SafetyBench (arXiv 2412.14470, Zhang et al., ACL 2025)**
  [SWEEP, abstract + per-model tables via cross-source]. 349
  environments, 16 agents, none above 60% safety score; within-family
  capability-safety trend visible in per-model numbers (Qwen2.5 72B
  37.3% vs 14B 31.9%; GPT-4o 44.2% > GPT-4-Turbo 41.9% > GPT-4o-mini
  31.2%) and defense-prompt gains smallest for the strongest models,
  the closest precedent for the capability moderator; the only lever
  is prompt content, never runtime enforcement. (Now ACL 2025, not
  arXiv-only; update the citation form.)

- **SafePyramid (arXiv 2606.29887, ByteDance / Melbourne)** [SWEEP,
  full text]. In-context policy application degrades with policy
  reasoning complexity (GPT-5.5 exact-match 54.0% at L0 to 12.9% at
  L2) in a pure classifier setting with no agent harness. (Use
  "reasoning complexity," not "policy density.")

- **BS-Bench / The Compliance Gap (arXiv 2605.01771)** [SWEEP].
  Framing and tool-availability manipulations expose large
  stated-vs-actual compliance gaps (removing delegation tools raises
  compliance from 0% to 74.7%) with a released deterministic
  log-based scorer and no runtime-enforcement condition.

- **MAC-Bench (arXiv 2606.07805)** [SWEEP]. Adversarial
  social-engineering pressure benchmark; cite to distinguish this
  paper's benign completion-pressure goal-conflict arm from
  adversarial goal conflict.

- **ODCV-Bench (arXiv 2512.20798)** [SWEEP]. Mandated vs incentivized
  instruction wording across 12 models and 40 scenarios (9 of 12
  models violate 30-50% of the time under KPI pressure), goal-conflict
  color for the H2 arm with no enforcement lever.

- **Instrumental Choices (arXiv 2605.06490)** [SWEEP]. 7 tasks x 8
  instruction-clarity variants, 10 models, deterministic
  environment-state scoring; varies constraint wording precision but
  never true absence and has no enforcement axis; optional citation
  in the goal-conflict paragraph only.

- **CEF/Thanatosis, "Is Your Agent Playing Dead?" (arXiv 2606.14831,
  J.P. Morgan AI Research)** [SWEEP, full PDF]. GPT-4o fabricates
  plausible external obstacles under FSM-sealed contradictory
  constraints in pure prompted dialogue, real constraint-driven
  fabrication under a more adversarial operationalization than the
  harness-blindness artifact this paper diagnoses; cite in the D-36
  discussion to scope the methodological claim precisely.

- **Anthropic agentic-misalignment research (blog)** [SWEEP].
  Adversarial self-preservation goal conflict producing harmful agent
  actions; cite only to mark the benign-vs-adversarial boundary.

## Tier 3: enforcement-substrate and injection-defense priors (background; one clause to one sentence each)

- **CaMeL (arXiv 2503.18813, Debenedetti et al., Google DeepMind /
  ETH Zurich)** [FULL-TEXT-LOCAL]. Must-cite: capability-tagged
  control/data-flow separation that "significantly outperforms all
  other defenses in terms of security" against prompt-only heuristic
  defenses on AgentDojo, the most citable prior instance of
  architectural enforcement beating prompting in the injection
  literature; it never states its policies to the model in any
  condition, so disclosure is never manipulated and no told/enforced
  crossing exists. (A sweep-level fetch fabricated a factorial for
  this paper; do not propagate it.)

- **Progent (arXiv 2504.11703)** [FULL-TEXT-LOCAL]. DSL-based
  least-privilege enforcement compared against prompt-based heuristic
  defenses on AgentDojo/ASB; same family as CaMeL, no disclosure
  factorial; cite with CaMeL if at all.

- **ToolGuards (arXiv 2507.16459)** [SWEEP]. Offline-compiled runtime
  validators on tau-bench Airlines (22/50 scenarios, +20pp pass rate
  over prompt-only and reflection baselines); telling present in
  every arm via tau-bench's built-in system-prompt policy; same
  single-axis bucket as AIRGuard.

- **Open Agent Passport / Before the Tool Call (arXiv 2603.20953)**
  [SWEEP]. Live adversarial bounty testbed, permissive policy 74.6%
  attacker success vs 0% under the restrictive runtime policy; both
  arms are runtime settings, no in-context telling axis.

- **ActPlane (arXiv 2606.25189)** [SWEEP]. eBPF OS-level enforcement
  substrate; its prompt-filter baseline is an LLM enforcement
  classifier reading a policy, not the agent's own contract with
  enforcement withheld; no crossing.

- **AgentSpec, NeMo Guardrails, Guardrails AI, Invariant Guardrails
  (Invariant Labs, now part of Snyk)** [SWEEP]. Enforcement
  frameworks rarely measured against an unenforced baseline and never
  crossed with a telling axis; AgentSpec (arXiv 2503.18666) was not
  full-text cleared, verify before final submission.

- **Policy-as-Prompt (arXiv 2509.23994, NeurIPS 2025 Regulatable ML
  workshop)** [SWEEP]. "Prompt-based guardrail" there means an
  external classifier reading a prompt, not the agent's own
  in-context contract; add one clarifying sentence to preempt the
  vocabulary collision.

- **Autoformalization of Agent Instructions into Policy-as-Code
  (arXiv 2606.26649)** [SWEEP]. A tool for turning told into
  enforced; measures translation fidelity, not agent behavior under
  either lever.

- **Design Patterns for Securing LLM Agents (arXiv 2506.08837)**
  [SWEEP, full HTML]. Conceptual taxonomy, no experiments; taxonomy
  vocabulary only.

- **Claude Code deny-rule bypass disclosure (Adversa AI, 2026-04-02)**
  [SWEEP]. Production anecdote of the told-vs-enforced distinction
  (CLAUDE.md as unenforced context vs deny rules as the enforced
  layer); introduction-motivation material, not a measurement.

- **Frontier-lab and industry convergence: Anthropic Opus 4.8 system
  card and OpenAI GPT-5.6 system card (both report bundled
  with/without-safeguards deltas, never decomposing prompt
  instruction from runtime blocking), DeepMind AI Control Roadmap
  blog, Microsoft Agent Governance Toolkit, OpenAI Agents SDK and
  LangChain guardrails docs, OWASP Top 10 for Agentic Applications
  2026** [SWEEP]. Industry convergence on the two-lever vocabulary
  without measuring the substitution question; one collective
  sentence.

## Tier 4: harness-engineering and methodology context (background; one clause each)

- **"Stop Comparing LLM Agents Without Disclosing the Harness" (arXiv
  2605.23950 / OpenReview qMjgplILnv)** [SWEEP, abstract]. NEW
  cite_only: position paper arguing harness configuration must be
  disclosed like hyperparameters because it often dominates model
  choice; a methodological parallel to the harness-blindness
  contribution, with a harness-choice x model-choice performance
  factorial, not a specify-vs-enforce compliance design.
- **ETCLOVG survey (OpenReview 3hXEPbG0dh, TMLR under review)**
  [SWEEP, snippets; re-fetch before lock]. Vocabulary anchor for the
  harness as a design surface; cite via OpenReview, not as accepted.
- **NLAH (arXiv 2603.25723)** [SWEEP]. Harness logic as editable
  natural-language documents; varies harness authoring, not
  enforcement.
- **AHE (arXiv 2604.25850)** [SWEEP]. Observability-driven automatic
  harness evolution; distinct from the similarly titled survey.
- **Meta-Harness (arXiv 2603.28052)** [SWEEP]. Outer-loop harness
  optimization for task performance; no governance axis.
- **AutoHarness (arXiv 2603.03329)** [SWEEP]. Auto-synthesized
  action-legality harness, always applied once built; no
  in-context-only control arm; thematically belongs with the
  enforcement row, not the scaffolding row.
- **Harness-Bench (arXiv 2605.27922)** [SWEEP]. Capability variance
  across model-harness configurations (5,194 trajectories); supports
  reporting at the model-harness level, no telling/enforcement axis.
- **HarnessAudit-Bench (arXiv 2605.14271)** [SWEEP]. Title-adjacent
  composite safety audit of model x framework configurations; one
  line to preempt confusion, no methodological overlap.
- **Life-Harness (arXiv 2605.22166)** [SWEEP]. Fixed-model harness
  adaptation for capability (116 of 126 settings improved); no
  governance or substitutability axis.
- **ALIGN (arXiv 2505.21055)** [SWEEP]. Auto-generated interface
  layer fixing agent-environment misalignment for success rate;
  orthogonal to constraint compliance.
- **IFEval (arXiv 2311.07911), RECAST (arXiv 2505.19030), VerIF
  (arXiv 2506.09942, EMNLP 2025 per ACL Anthology)** [SWEEP]. Use
  checkability to build evaluations and rewards, not as a predictor
  of when agents comply; attribute the hard/soft satisfaction split
  to FollowBench, not to these three, if that label is used.
- **IHEval (arXiv 2502.08745), SpecEval (arXiv 2509.02464)** [SWEEP].
  Pure text-completion instruction-hierarchy and spec-adherence
  evaluations with no harness or enforcement; covered by the generic
  instruction-following sentence, named citation optional.
- **DEMM-Bench (arXiv 2606.20634)** [FULL-TEXT-LOCAL]. Optional
  M8-adjacent citation: benchmarks whether agent-runtime evidence
  containers suffice to reconstruct decision-level governance
  properties post hoc (evidence presence is not decision-level
  sufficiency); no enforcement mechanism under test and no
  policy-disclosure manipulation.

## New must-cite papers surfaced by the hunt (absent from PAPER.md's Lineage Anchor)

Tier 1 additions: FORGE (2602.16708), ABSTAIN (2606.02965), TeamBench
(2605.07073), Harness-MU (2606.21856), TRACE (2606.13174), Prompts
Don't Protect (2605.18414), Mechanical Enforcement (2605.14744);
ContextCov (2603.00822) and Verifier Tax (2603.19328) promoted from
the background bucket to Tier 1. Tier 2 addition: Governance Decay /
ConstraintRot (2606.22528) plus its concurrent works (Gamage 2026;
SafeContext) after full-text re-verification. Tier 3 additions: CaMeL
(2503.18813), Progent (2504.11703), ToolGuards (2507.16459),
MAC-Bench (2606.07805), BS-Bench (2605.01771), CEF/Thanatosis
(2606.14831), Open Agent Passport (2603.20953), ActPlane
(2606.25189). Tier 4 additions: "Stop Comparing LLM Agents Without
Disclosing the Harness" (2605.23950), Harness-Bench (2605.27922),
HarnessAudit-Bench (2605.14271), DEMM-Bench (2606.20634, optional).
IDs to add for entries already named: Meta-Harness (2603.28052),
AutoHarness (2603.03329).

Corrections to entries already in PAPER.md: PhantomPolicy telling
axis (falsified clause, see verdict.md headline item 3), AIRGuard
one-model scoping, ST-WebAgentBench scaffold count, SafePyramid axis
naming, LogiSafetyBench family-dependent trend, Agent-SafetyBench now
ACL 2025.
