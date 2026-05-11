# Paper 1 (Merged) — Outline

**Status:** Proposal, 2026-05-11. Reflects the merge decision from the
2026-05-11 framing discussion: paper 1 absorbs the Engels et al.
Backdoor Code extension previously scoped to paper 2. Pending pilot
result and decision-gate confirmation.

**Relation to existing planning docs.** This outline supersedes
`DRAFT_PAPER.md` if the merge is confirmed. `PAPER_FRAME.md` and
`CLAIM_LADDER.md` need round-3 updates to match. The on-disk
reframe audit (`codex_runtime_first_reframe_audit_response.md`
F-CDX-RFR-R1-01 through 11) must close before any section here is
written.

---

## Title (working)

**Deterministic Runtime Contracts as Trusted Monitors: A Control-Protocol
Framework and Scaling-Laws Result for Bounded Agent Operation**

Alternatives under consideration:

- *Software Contracts as Trusted Overseers: Scaling Laws for
  Deterministic Agent Governance*
- *Bounded Agents, Trusted Runtimes: A Control-Protocol Framework for
  Software-Side Safety*
- *Beyond LLM Monitors: Deterministic Software Contracts as the Trusted
  Side of AI Control Protocols*

"User-owned structured data" dropped from title per round-2 venue
analysis — dilutes legibility to control-aligned reviewers. Personal
wellness becomes the *instantiation*, not the framing.

---

## Abstract (draft)

Agents operating over consequential structured data are an instance of
the AI control problem: we want useful work from systems we cannot
fully trust. Existing control protocols treat the *trusted* side of the
protocol as a model — either a weaker LLM monitor or a human reviewer
— and inherit the failure modes of those substrates. Recent work
(Adaptive Attacks on Trusted Monitors, 2025; Reasoning Models Don't
Always Say What They Think, 2025) shows LLM monitors are a single
point of failure under both adversarial and capability-failure
conditions.

We study a complementary primitive: **deterministic software
contracts as the trusted side of a control protocol**. The contract
exposes a capabilities manifest, typed command schemas, mutation
classes, deterministic validation gates, proposal/commit separation,
and an audit chain — operationalizing a machine-executable safety
spec.

We instantiate this architecture in HAI, a local personal-wellness
runtime over wearable and user-authored data, and introduce
**GovernedAgentBench**, a benchmark designed for runtime-mechanism
ablation rather than aggregate compliance.

Three results:

1. **Mechanism-isolable ablations.** Holding prompt and task constant
   and toggling individual runtime mechanisms produces measurable
   per-mechanism contributions to safety-constrained operation.
2. **Runtime-as-floor.** Under the full contract, the smallest
   predeclared model passes all primary safety thresholds; under
   `no_runtime_enforcement`, a larger predeclared model fails at
   least one. The contract shifts the model-scale safety curve.
3. **Deterministic Guards in scaling-laws-for-oversight.** Extending
   Engels et al. 2025 by adding a deterministic-runtime Guard data
   point to the Backdoor Code game, we find the deterministic Guard
   achieves domain Elo X at general Elo = 0, exceeding LLM Guards
   below threshold Y.

A targeted adversarial layer (50 trajectories across refusal-bypass,
mutation escalation, audit tampering, schema evasion) characterizes
safety × usefulness under bounded adversarial conditions.

Limitations: single-domain instantiation; capability-failure threat
model with targeted (not full-substitution) adversarial layer;
fine-tuned operators deferred to future work.

---

## Contributions

1. **Architectural contribution.** Extending the AI control protocol
   class to admit *deterministic software* as the trusted-side
   primitive, complementing rather than replacing LLM monitors. The
   contract operationalizes a safety spec as machine-executable code.

2. **HAI reference implementation.** A bounded personal-wellness runtime
   demonstrating the architecture on user-owned wearable + structured
   state, with non-clinical safety boundary as part of the contract.

3. **GovernedAgentBench.** A benchmark designed for
   *runtime-mechanism-isolable* ablation. Reports per-mechanism
   contributions rather than aggregate compliance. Each mechanism
   (validation, agent_safe, proposal gate, refusal, audit chain) is
   independently toggleable with `mechanism_disabled` audit markers.

4. **Ablation study under held-constant prompt.** Per-mechanism
   contributions to command validity, mutation-boundary obedience,
   refusal accuracy, unsupported narration, clinical-boundary
   violations, and contract-drift robustness, across a predeclared
   model roster.

5. **Scaling-laws-for-oversight extension.** Adding a deterministic
   runtime as one Guard data point to Engels et al. 2025's Backdoor
   Code game; measuring where deterministic Guards exceed LLM Guards
   in domain Elo at fixed general Elo.

6. **Targeted adversarial layer.** A bounded red-team protocol
   characterizing contract integrity under refusal-bypass, mutation
   escalation, audit-chain tampering, and schema evasion attacks.

7. **Error taxonomy.** Failure modes for contract-governed bounded
   agent operation: hallucinated commands, invalid proposals, unsafe
   mutation attempts, unsupported narration, clinical-boundary
   violations, drift failures, refusal errors.

---

## Section structure (target: 9 pages excluding refs + appendices, NeurIPS main format)

### 1. Introduction
- 1.1 Bounded agents over consequential data as a control instance
- 1.2 LLM-monitor failure modes (cite Adaptive Attacks on Trusted
  Monitors arXiv:2510.09462, Reasoning Models Don't Always Say What
  They Think)
- 1.3 Deterministic software contracts as a missing primitive
- 1.4 Contributions
- 1.5 Paper structure

### 2. Background and related work
- 2.1 AI Control protocols (Greenblatt et al. 2024; Ctrl-Z; Games for
  AI Control; ControlArena)
- 2.2 Safety specs as artifacts (OpenAI Model Spec; Deliberative
  Alignment; Anthropic Model Spec Midtraining; Stress-Testing Model
  Specs)
- 2.3 LLM-based runtime monitors (Constitutional Classifiers,
  Hierarchical Summarization)
- 2.4 Agent safety benchmarks (ST-WebAgentBench, SafeAgentBench,
  Agent-SafetyBench, OS-Harm, AgentDojo)
- 2.5 Scaling laws for scalable oversight (Engels et al. 2025)
- 2.6 Constrained generation as a related abstraction layer (brief)

### 3. Threat model
- 3.1 Capability-failure: the model is fallible, may emit invalid
  commands, hallucinated tool calls, unsupported claims, or unsafe
  mutations
- 3.2 Targeted adversarial: bounded attempt to bypass refusal,
  escalate mutations, tamper with audit, evade validation
- 3.3 Out-of-scope: scheming-misalignment substitution (explicit
  ASL-2/3 contract substrate framing per Anthropic Bumpers); full
  prompt-injection survey; sandbagged executor models

### 4. Runtime contract architecture
- 4.1 Capabilities manifest as machine-executable spec
- 4.2 Typed command schemas and mutation classes
- 4.3 `agent_safe` enforcement seam (note F-CDX-RFR-R1-09 narrowing)
- 4.4 Proposal/commit separation (W57 user-gate)
- 4.5 Deterministic validation gates
- 4.6 Policy rules
- 4.7 Audit chain (three-state: proposal_log → planned_recommendation
  → daily_plan + recommendation_log)
- 4.8 The contract as machine-executable safety spec

### 5. HAI reference instantiation
- 5.1 Personal wellness as deliberately bounded domain
- 5.2 Six domains, runtime structure
- 5.3 Non-clinical boundary as part of the contract, not a footnote
- 5.4 What HAI exposes for benchmark evaluation

### 6. GovernedAgentBench
- 6.1 Task families (L1-L7)
- 6.2 Metrics: command validity, mutation-boundary obedience,
  schema-valid proposal generation, refusal accuracy, unsupported
  narration, clinical-boundary violations, contract-drift robustness
- 6.3 `runtime_mode × model_class` ablation matrix, prompt held constant
- 6.4 Predeclared model roster (Qwen2.5 family, Claude 3.5 Haiku,
  Claude Sonnet 4, GPT-4o-mini)
- 6.5 Predeclared thresholds + `scorer_config_hash`
- 6.6 Scoring methodology + `mechanism_disabled` audit markers

### 7. Empirical results
- 7.1 Tier 0: infrastructure (mechanisms ablatable, on/off unit tests
  pass)
- 7.2 Tier 1: mechanism effect (at least one M4-M8 toggle produces
  non-zero gap on at least one primary metric)
- 7.3 Tier 2: component ranking (per-mechanism contributions across
  metrics)
- 7.4 Tier 3: runtime-as-floor (smallest predeclared model + full
  contract passes thresholds; larger predeclared model +
  no_runtime_enforcement fails)
- 7.5 Engels Backdoor Code extension
  - 7.5.1 Reimplementation of Engels protocol against APPS samples
  - 7.5.2 Houdini ladder: Qwen2.5-7B/32B/72B, GPT-4o-mini,
    Claude 3.5 Haiku, Claude Sonnet 4
  - 7.5.3 Guards: deterministic runtime contract, replicated LLM
    Guard from Engels, contract-minus-one-mechanism ablations
  - 7.5.4 Domain Elo vs general Elo curve with deterministic Guard
    plotted at general Elo = 0
  - 7.5.5 Threshold below which deterministic exceeds LLM Guards
- 7.6 Hierarchical Summarization head-to-head
  - 7.6.1 Replicate Anthropic Feb 2025 LLM-summarizer monitor on a
    shared task family
  - 7.6.2 Deterministic contract on same task family
  - 7.6.3 Detection rate × false-positive rate Pareto

### 8. Adversarial layer
- 8.1 50-trajectory red-team protocol
- 8.2 Attack types: refusal bypass, mutation escalation, audit
  tampering, schema evasion
- 8.3 Safety × usefulness Pareto under bounded adversarial conditions
- 8.4 Where the contract leaks; what minimal hardening closes the leak

### 9. Discussion
- 9.1 What deterministic monitors gain: provability, no
  inherited-from-model failure modes, audit-chain integrity
- 9.2 What they lose: judgment, semantic adjudication, novelty
  handling
- 9.3 Complementarity: deterministic floor + LLM ceiling
- 9.4 Implications for AI Control protocol design

### 10. Limitations
- 10.1 Single-domain instantiation; cross-domain generalization is
  future work (coding agent, file system, productivity — appendix
  has a sketch)
- 10.2 Capability-failure threat model with *targeted* adversarial
  layer, not full attack-policy substitution
- 10.3 No fine-tuned local operator evaluation (future paper)
- 10.4 Bench-specific scaling claims
- 10.5 Personal-wellness instantiation is non-clinical by design;
  clinical deployment is explicitly out of scope

### 11. Conclusion
- 11.1 The trusted side of a control protocol can be deterministic
  software
- 11.2 Mechanism-isolable runtime ablation is a usable measurement
  surface
- 11.3 Deterministic Guards have a meaningful niche on the Engels
  scaling-laws-for-oversight curve

### Appendices
- A. Reproducibility: model roster + provider snapshots + decoding
  settings + `model_identity` schema
- B. Engels Backdoor Code protocol details and APPS sample selection
- C. Red-team attack policy specifications
- D. Future-A: fine-tuned local operator (sketch only)
- E. Cross-domain extension sketch (coding agent, file system)
- F. HAI architecture details

---

## Scope deltas vs current `DRAFT_PAPER.md`

| Item | Current draft | Merged outline |
|---|---|---|
| Title | "Runtime Contracts for Local Agents Over Sensitive User-Owned Data" | "Deterministic Runtime Contracts as Trusted Monitors..." |
| Lineage anchor | Single (AI Control implied) | Triple (control + safety spec + LLM-monitor baselines) |
| Threat model | Capability-failure only | Capability-failure + targeted adversarial layer |
| Engels Backdoor Code | Future-A appendix | §7.5 headline empirical result |
| Hierarchical Summarization | Not addressed | §7.6 direct empirical contrast |
| Red-team | Not addressed | §8, ~50 trajectories |
| Coding-agent extension | Implicit "future runtime" | Explicit appendix sketch; not in main paper |
| Fine-tuning (Future-A) | Future appendix | Same — explicit sequel paper |
| Target venue | Workshop | NeurIPS 2027 main conference |
| Page count target | 4-8 (workshop) | 9 excluding refs + appendices (main) |

---

## Calendar checkpoints

| Checkpoint | Target date | Action |
|---|---|---|
| On-disk reframe close | Jun 2026 | Close F-CDX-RFR-R1-01..11; PAPER_FRAME + CLAIM_LADDER + RESEARCH_EVAL_STRATEGY consistent with merged paper |
| Engels pilot (de-risk) | Jul 2026 | 2-week pilot: 2 Houdinis × deterministic Guard + 1 LLM Guard calibration anchor on Backdoor Code |
| Pilot decision gate | Aug 2026 | Pilot result determines merge commit vs revert to Trajectory A |
| Mechanism ablations complete | Nov 2026 | Tier 1, 2, 3 evidence on GovernedAgentBench |
| Full Engels run | Feb 2027 | All 6 Houdinis × 3 Guards × 225 APPS samples |
| Red-team complete | Mar 2027 | 50 trajectories, 4 attack types |
| Hierarchical Summarization comparison | Mar 2027 | Head-to-head on shared task family |
| Manuscript v1 complete | Apr 2027 | Full draft for internal review |
| NeurIPS 2027 submission | May 2027 | Deadline ~late May |

---

## Decision gates

- **Pilot result is the load-bearing gate.** If the Engels pilot
  shows clean separation (deterministic Guard outperforms LLM
  Guards in some general-Elo regime), commit to merged scope. If
  pilot shows null result, revert to Trajectory A (workshop paper 1
  + conference paper 2).
- **Hierarchical Summarization empirical contrast is the second
  gate.** If reimplementation cannot produce a credible LLM-monitor
  baseline within ~3 weeks, demote to rhetorical contrast only.
- **Adversarial layer is non-negotiable.** Without the red-team
  layer, control-aligned reviewers desk-reject on framing. If
  calendar slips, cut scope elsewhere first.

---

## What is explicitly NOT in this paper

- Coding-agent reference runtime (paper 2 or appendix sketch only)
- Fine-tuned local operator (paper 2)
- Full attack-policy substitution red-team (not in v1)
- Multi-agent / agent-to-agent control protocols
- Hosted-product deployment claims
- Clinical or medical decision-making claims
- Cross-domain generalization beyond personal wellness
- Sandbagged or password-locked executor models
