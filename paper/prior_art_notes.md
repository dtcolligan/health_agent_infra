# Prior Art Notes

Citation notes for the preprint §2 background and related work. Aligned
to the lineage anchor in [`/PAPER.md`](../PAPER.md).

Full distillation from `RELATED_WORK_DRAFT.md`, `PRIOR_ART_POSITIONING.md`,
and `prior_art_matrix.md` is in
[`/ARCHIVE/paper_planning/`](../ARCHIVE/paper_planning/). This file
keeps only what the §2 draft needs.

## Lineage Triple

The contribution sits at the intersection of three literatures:

### AI Control Protocols

| Citation | Role |
|---|---|
| Greenblatt et al. 2024 (AI Control: Improving Safety Despite Intentional Subversion) | Source of the trusted-monitor / untrusted-operator vocabulary and the safety-usefulness evaluation pattern. |
| Ctrl-Z, Games for AI Control, ControlArena (`control-arena.aisi.org.uk`) | Follow-up infrastructure. The preprint cites ControlArena as the canonical evaluation framework but does not run on it. |
| Adaptive Attacks on Trusted Monitors (arXiv:2510.09462, 2025) | The framing-overclaim preempt. Cited in §1 and §2; reinforces that "trusted-monitor substrate" framing is bounded, not a complete control safety case. |

### Safety Specs

| Citation | Role |
|---|---|
| OpenAI Model Spec | Explicit safety-behaviour specification; the preprint frames the runtime contract as one substrate. |
| Anthropic Model Spec Midtraining (MSM) | Same role; explicit safety spec. |
| Deliberative Alignment (arXiv:2412.16339) | Prompt-only spec use has latency cost and forces the model to infer the spec from labeled examples. The preprint tests executable code as an alternative substrate. |

### LLM-Monitor Baselines

| Citation | Role |
|---|---|
| Constitutional Classifiers (arXiv:2501.18837) | Pareto-frontier reporting precedent for detection rate × false-positive rate. GovernedAgentBench reuses the metric shape; **not** a head-to-head. |
| Hierarchical Summarization (Anthropic Feb 2025) | The direct LLM-monitor competitor by design. §2.3 prose contrast only in the preprint; bounded empirical contrast deferred to future work per D-08. |

## Closest Benchmark Prior

**ST-WebAgentBench** (Levy et al., ICML 2025, arXiv:2410.06703).
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

1. AI control protocols subsection (Greenblatt, ControlArena, Adaptive
   Attacks).
2. Safety specs subsection (OpenAI/Anthropic Model Specs, Deliberative
   Alignment).
3. LLM-monitor baselines subsection (Constitutional Classifiers, HS).
4. Agent safety benchmarks subsection (ST-WAB load-bearing
   differentiation, AgentDojo and others for context).
5. Future-work bridge sentence pointing at Engels + scaling-laws-for-
   oversight + S1 fine-tuning.

Full bibliographic detail (authors, years, venues) is in the archived
`prior_art_matrix.md` at `/ARCHIVE/paper_planning/`.
