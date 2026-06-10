# Prior Art Notes

Citation notes for the preprint §2 background and related work. Aligned
to the lineage anchor in [`/PAPER.md`](../PAPER.md).

Full distillation from `RELATED_WORK_DRAFT.md`, `PRIOR_ART_POSITIONING.md`,
and `prior_art_matrix.md` is in
[`/ARCHIVE/paper_planning/`](../ARCHIVE/paper_planning/). This file
keeps only what the §2 draft needs.

## Lineage Triple

The contribution sits at the intersection of three literatures (reframed
per D-26: AI-engineering agent-harness governance, not AI control).

### Agent Harnesses and Scaffolding

| Citation | Role |
|---|---|
| ReAct, Toolformer, CoALA (arXiv:2309.02427) | Vocabulary for the agent's structured action space and the runtime it operates in. |
| SWE-agent / ACI (arXiv:2405.15793, NeurIPS 2024) | Establishes the harness/interface, not only the model, as a load-bearing design surface via a held-model interface ablation (capability, not governance). |
| Agent Harness Engineering survey (ETCLOVG taxonomy; under TMLR review) | Names "Governance" and "Verification" as first-class harness layers — the taxonomic home of HAI's contract. Source of the coupling-problem caveat. |

### Runtime Enforcement and Guardrails

| Citation | Role |
|---|---|
| AgentSpec (arXiv:2503.18666) | DSL of (trigger, predicate, enforcement) runtime rules. Rule-modular but no per-mechanism causal ablation. |
| Invariant Guardrails; Guardrails AI | Rule/validator-composable runtime layers. Separable, not ablation-measured. |
| NeMo Guardrails (arXiv:2310.10501) | Direct contrast: its safety/self-check rails are LLM-prompt-based and non-deterministic; ours are deterministic. |

### Software Contracts and Capability Security

| Citation | Role |
|---|---|
| Design-by-contract (Meyer/Eiffel); typed command schemas | The engineering substrate the governance contract instantiates. |
| Object-capability model | Capability-based constraint on what the operator may invoke; maps onto `agent_safe` + the proposal/commit gate. |

## Closest Neighbors (cite and distinguish in §2)

| Citation | Closeness / delta |
|---|---|
| Agent Behavioral Contracts (arXiv:2602.22302) | **Closest prior.** Runtime contracts C=(P,I,G,R), contracted-vs-uncontracted ×7 models, AgentContract-Bench. Delta: LLM-judge extraction (not purely deterministic), patent-pending benchmark, no hidden `runtime_mode` intervention under a held prompt with an offline scorer. |
| Life-Harness (arXiv:2605.22166) | Fixed-model harness adaptation with leave-one-layer-out ablation. Delta: evolved interventions, capability outcome, deterministic *environments* (not deterministic governance). |
| ALIGN (arXiv:2505.21055) | Generated interface wrapper, agent/env held constant, component ablations. Delta: enriches observations (capability), not governance/constraint. |
| NLAH (arXiv:2603.25723), AHE, HARBOR, Meta-Harness, AutoHarness | Fixed-model harness attribution / ablation. Kill any "first to ablate the harness" claim; all capability-oriented and LLM/evolved, not deterministic governance. |
| Guardrails-as-Infrastructure (arXiv:2603.18059), ContextCov (arXiv:2603.00822), Verifier Tax (arXiv:2603.19328) | Deterministic-policy / runtime-mediation neighbors. Delta: model-agnostic trace replay or LLM-mediated, not held-prompt per-mechanism runtime-mode ablation. |

**Novelty is the conjunction** (per D-26): held model and prompt + hidden
`runtime_mode` intervention + deterministic governance mechanisms toggled
individually + offline deterministic scorer + released mechanism-isolable
benchmark. No "first X" claims; causal language conditional on this fixed
controller.

## Model-Based Governance (demoted contrast, not the home lineage)

Retained as a §2 contrast showing deterministic governance differs from
model-/prompt-based governance. Not the contribution's home.

| Citation | Role |
|---|---|
| Greenblatt et al. 2024 (AI Control); ControlArena; Adaptive Attacks on Trusted Monitors (arXiv:2510.09462) | Control-framed contrast and trusted-monitor vocabulary. The preprint does NOT make a control safety case. |
| OpenAI Model Spec, Anthropic MSM, Deliberative Alignment (arXiv:2412.16339) | Safety behaviour specified for the model; the preprint tests executable code as a deterministic substrate instead. |
| Constitutional Classifiers (arXiv:2501.18837) | Pareto-frontier reporting precedent (metric shape reuse, NOT a head-to-head). |
| Hierarchical Summarization (Anthropic Feb 2025) | LLM-monitor approach; §2 prose contrast only, empirical contrast deferred (D-08). |

## Closest Benchmark Prior

**ST-WebAgentBench** (Levy et al., ICLR 2026, arXiv:2410.06703).
Load-bearing differentiation axis: GovernedAgentBench is runtime-mode
intervention with mechanism-isolable ablation under a held-constant
prompt. ST-WebAgentBench varies tasks but not runtime mechanism
state, and does not isolate which contract component contributes to
which metric. The 6-row differentiation table is in
`/ARCHIVE/framing_v2/round_5/RESPONSE.md` §Q1b.

## Other Benchmark Prior to Cite

| Citation | Use |
|---|---|
| AgentDojo (arXiv:2406.13352) | Agent-safety benchmark prior; cited in §2.4. |
| SafeAgentBench | Agent-safety benchmark prior; cited in §2.4. |
| Agent-SafetyBench | Agent-safety benchmark prior; cited in §2.4. |
| OS-Harm | OS-level agent harm benchmark; cited in §2.4. |
| SHADE-Arena | Adversarial agent benchmark; cited in §8 adversarial layer prior art. |

## Reasoning About Capability Failure

| Citation | Role |
|---|---|
| Reasoning Models Don't Always Say What They Think (2025) | LLM monitors are a single point of failure under capability conditions. Cited in §1 motivation. |
| BFCL, ToolLLM, Gorilla | Establish that "model with full info beats model with no info" is already known — the preprint does not vary the prompt, only the runtime, to avoid that trivial result. |

## Engels Backdoor Code (Future Work Citation)

| Citation | Role |
|---|---|
| Engels et al. 2025 (Backdoor Code, scaling laws for oversight, arXiv:2504.18530) | Future-work paper anchor (deferred per D-03). Preprint may cite as future direction; no empirical claim. |

## Banned-In-Preprint Citations

The following are referenced in the deferred-work bucket only and
should NOT appear as in-scope citations in the abstract, §1, or §5:

- Constitutional Classifiers as a head-to-head competitor (it's a
  Pareto-reporting precedent, not a baseline we run);
- HS as an empirical comparator (prose only in §2.3);
- Engels Backdoor Code as an experiment we ran (future work).

## Drafting Order

When §2 drafting begins (late July):

1. Agent-harness and scaffolding subsection (ReAct/CoALA/SWE-agent ACI,
   the Agent Harness Engineering survey + ETCLOVG; harness as a
   load-bearing design surface).
2. Runtime enforcement and software-contracts subsection (AgentSpec,
   Invariant/Guardrails-AI, NeMo as the non-deterministic contrast;
   design-by-contract and object-capability substrate).
3. Closest-neighbors subsection (Agent Behavioral Contracts, Life-Harness,
   ALIGN, NLAH; state the conjunction delta). Demoted model-based
   governance contrast (Greenblatt, Model Specs, Constitutional
   Classifiers, HS) folded in here, not as the home.
4. Agent benchmarks subsection (ST-WAB load-bearing differentiation on
   runtime-mode ablation, AgentDojo/tau-bench/OS-Harm for context).
5. Future-work bridge sentence pointing at Engels + scaling-laws-for-
   oversight + S1 fine-tuning.

Full bibliographic detail (authors, years, venues) is in the archived
`prior_art_matrix.md` at `/ARCHIVE/paper_planning/`.
