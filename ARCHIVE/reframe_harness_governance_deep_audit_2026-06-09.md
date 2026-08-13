# Deep audit: proposed AI-control to harness-governance reframe

Date: 2026-06-09

Role: independent auditor. This report re-derived the claims from repo
state and primary sources rather than ratifying the prior dossier.

## Repo-state checks

- `pwd`: `/Users/domcolligan/health_agent_infra`.
- `git status --short --branch`: active tree already contained modified
  `PAPER.md`, `benchmark/governed_agent_bench/PILOT_PROTOCOL.md`,
  `benchmark/governed_agent_bench/schema/README.md`, several untracked
  benchmark/orchestrator files, and the prior reframe dossier. I did not
  edit those files.
- Read `AGENTS.md`, `PAPER.md`, then
  `ARCHIVE/reframe_harness_governance_audit_2026-06-09.md`; section 10
  was read last.
- Current active paper framing remains AI Control Protocols. `PAPER.md`
  locks the title as "Deterministic Software Contracts as Trusted
  Monitors in AI Control Protocols" and states that the headline
  experiment varies the runtime, not the prompt. `AGENTS.md` still says
  not to soften the external framing without Dom's decision.

## Verdict

**REFINE the proposed reframe.**

I would not keep the current trusted-monitor / AI-control north star as
the external lead, because the empirical core does not evaluate
scheming, untrusted-monitor collusion, trusted-labor protocols, or
control against intentional model subversion in the Greenblatt et al.
sense. That title overpromises.

I would also not accept the dossier's "pure AI-engineering" pivot as
written. "Improve Agent Performance" is too broad and collides directly
with Life-Harness, ALIGN, SWE-agent, AHE, HARBOR, Meta-Harness, and
AutoHarness. The defensible register is **runtime governance as an
AI-engineering harness layer**, not generic capability harnessing and
not an AI-control protocol.

North-star framing:

> GovernedAgentBench measures how deterministic runtime-governance
> mechanisms inside an agent harness affect reliable,
> constraint-respecting operation when the model and prompt are held
> fixed.

One-sentence thesis:

> Holding the model and deployment prompt fixed, GovernedAgentBench
> treats `runtime_mode` as the intervention and estimates the marginal
> contribution of deterministic harness-governance mechanisms to
> reliable, constraint-respecting agent operation.

Ranked title candidates:

1. **Ablating Runtime Governance in Agent Harnesses**
2. **Measuring Deterministic Governance Mechanisms in Agent Harnesses**
3. **Runtime-Mode Ablations for Reliable LLM Agent Operation**
4. **Mechanism-Level Evidence for Agent Harness Governance**
5. **Which Harness Governance Mechanisms Make Agents Reliable?**

I would drop the dossier title. It is grammatically heavy and its
"Improve Agent Performance" phrase invites reviewers to compare against
capability-harness papers where the paper is less novel.

## Bottom-line novelty finding

No primary source I found pre-empts the full narrow claim:

> held model and prompt; hidden `runtime_mode` intervention; deterministic
> governance mechanisms toggled individually; offline deterministic
> scorer; released mechanism-isolable benchmark.

But the novelty margin is much narrower than the dossier says. The
paper must avoid claiming any of:

- first agent harness ablation;
- first fixed-model harness attribution;
- first runtime enforcement / governance layer;
- first software-contract framing for LLM agents;
- first released safety/governance benchmark.

The viable novelty claim is a conjunction claim: **runtime-mode
mechanism isolation for deterministic governance mechanisms under a
held deployment prompt, with static/live evidence tiers kept separate.**

## Source ledger / prior-art matrix

Legend: Pre-empts = contains every material element of the narrow claim;
Weakens = occupies an important slice and constrains wording; Adjacent =
nearby benchmark/tooling but not a direct novelty threat; Background =
terminology or field context.

Search coverage: I used the requested adversarial query families around
LLM agent harness ablation, runtime-mode ablation, deterministic
guardrail ablation, governance layers, interface-wrapper ablations,
held-prompt runtime interventions, agent safety runtime enforcement,
software contracts, verification layers, and NLAH/Pan harness ablation.
I also followed stronger nearby leads found during search: Agent
Behavioral Contracts, Guardrails as Infrastructure, ProbGuard, and Code
as Agent Harness.

Verification note: every arXiv identifier listed below was either opened
on arXiv or downloaded as a PDF and converted to text locally. Source
availability flags: Agent Behavioral Contracts says its implementation
and benchmark are available subject to IP clearance; I did not
independently verify a public downloadable AgentAssert/AgentContract-
Bench release. Guardrails as Infrastructure claims a reproducible
benchmark in the paper; I did not locate an external artifact beyond the
arXiv paper during this audit. Product/tooling pages were treated as
near-primary ecosystem evidence, not peer-reviewed evidence.

| Source | Primary URL | Verified identity | Full text read | Intervention varied | Prompt held constant | Model held constant | Runtime/harness varied | Deterministic vs learned/LLM-generated | Governance/safety vs capability | Per-mechanism vs whole-layer | Released benchmark/scorer | Threat to GAB novelty | Classification |
|---|---|---:|---:|---|---|---|---|---|---|---|---|---|---|
| Life-Harness, arXiv:2605.22166 | https://arxiv.org/abs/2605.22166 | Yes | Yes | Runtime harness layers evolved from trajectories | No; contract/skill layers are prompt-visible | Yes for many comparisons | Yes | Mixed: learned/evolved harness plus deterministic validation/canonicalization | Capability | Layer ablation: Contract, Skill, Action, Trajectory | Code linked | Very close on fixed-model harness adaptation and layer ablation; not held-prompt deterministic governance | Weakens |
| ALIGN, arXiv:2505.21055 | https://arxiv.org/abs/2505.21055 | Yes | Yes | Generated interface wrapper components | No; richer static/step-wise interface changes what agent sees | Yes/mostly, across agent architectures and backbones | Yes | LLM-generated wrapper code/modules | Capability | Component ablation: InferRules and WrapStep | Code linked | Close on interface wrapper and component ablation; not governance/runtime-mode | Weakens |
| Natural-Language Agent Harnesses, arXiv:2603.25723 | https://arxiv.org/abs/2603.25723 | Yes | Yes | NLAH/IHR vs code/prompted harness; module ablations | No; natural-language policy is part of intervention | Same IHR/model in main experiments | Yes | Natural-language policy executed by IHR with deterministic hooks | Capability plus harness science | Module ablation | Not a GAB-like scorer | Refutes dossier landmine; very strong broad-harness-ablation prior | Weakens |
| Agent Harness Engineering: A Survey | https://openreview.net/forum?id=eONq7FdiHa | Yes | Yes | Survey | N/A | N/A | N/A | N/A | Field taxonomy | N/A | N/A | Establishes Governance and Verification layers plus coupling problem | Background |
| SWE-agent/ACI, arXiv:2405.15793 | https://arxiv.org/abs/2405.15793 | Yes | Yes | Agent-computer interface components | No | Yes in ACI comparisons | Yes | Hand-authored interface/guardrails | Capability | Interface component ablations | SWE-bench-based eval | Shows fixed-model interface/guardrail ablation predates GAB | Weakens |
| AgentSpec, arXiv:2503.18666 | https://arxiv.org/abs/2503.18666 | Yes | Yes | Runtime enforcement rules | Not the main controlled axis | Yes in domain evals | Yes | Developer rules; some LLM-generated rules studied | Safety/governance | Rule/framework, not GAB M4-M8 ablation | GitHub linked | Directly precludes "first runtime enforcement/governance" | Weakens |
| ContextCov, arXiv:2603.00822 | https://arxiv.org/abs/2603.00822 | Yes | Yes | Active executable guardrails vs prompt/reflection | Prompt-only baseline differs | Agent task setup held in benchmark | Yes | LLM-assisted check generation, deterministic runtime checks | Governance/compliance | Constraint/check classes, not GAB mechanisms | Code/eval claimed | Very close to executable AGENTS.md constraints and runtime interception | Weakens |
| SafeAgent, arXiv:2604.17562 | https://arxiv.org/abs/2604.17562 | Yes | Yes | Runtime controller and decision-core parameters | No | Yes in benchmark comparisons | Yes | Runtime controller plus semantic decision core | Security/governance | Ablates confidence and policy weighting | Uses ASB/InjecAgent | Runtime governance with ablations, but not deterministic mechanism isolation | Weakens |
| The Verifier Tax, arXiv:2603.19328 | https://arxiv.org/abs/2603.19328 | Yes | Yes | Tool-calling vs Triad vs Triad-Safety architecture | No; verifier prompt/policy differs | Yes; same base model weights and policy docs | Yes | LLM verifier plus deterministic audit script | Safety/governance | Architecture-level | tau-bench evaluation | Strong on runtime safety mediation under same models; not deterministic M4-M8 | Weakens |
| Agent Behavioral Contracts, arXiv:2602.22302 | https://arxiv.org/abs/2602.22302 | Yes | Yes | Contracted/uncontracted plus ABC component ablations | Claims identical prompts/tasks for contracted vs uncontracted sessions, but contract rules are active intervention | Yes, across 7 models | Yes | ContractSpec/AgentAssert runtime plus LLM judge extraction | Governance/contracts | Component ablation: hard, soft, drift, recovery | AgentContract-Bench claimed; availability subject to IP clearance | Closest contract/governance threat; not hidden runtime-mode deterministic scorer | Weakens |
| Guardrails as Infrastructure, arXiv:2603.18059 | https://arxiv.org/abs/2603.18059 | Yes | Yes | Policy packs P0-P4 | LLM-independent trace replay | N/A | Yes | Deterministic policy DSL and PEP/PDP | Governance/security | Policy-pack ablation | Reproducible benchmark claimed | Very close on model-agnostic deterministic policy ablation, but not LLM prompt/model held | Weakens |
| ProbGuard, arXiv:2508.00500 | https://arxiv.org/abs/2508.00500 | Yes | Yes | Probabilistic runtime monitor vs baselines | No; intervenes by prompt augmentation or stopping | Yes in evals | Yes | Learned DTMC/probabilistic monitor | Safety | Monitor framework | Code/data repository claimed | Runtime monitoring but learned/probabilistic, not deterministic mechanism ablation | Adjacent |
| ST-WebAgentBench, arXiv:2410.06703 | https://arxiv.org/abs/2410.06703 | Yes | Yes | Agents and policy dimensions; policy injection/scoring | No; policies injected into prompt/context | Models/agents compared | Not primary intervention | Modular policy evaluators | Safety/trustworthiness | Dimension deletion, not runtime mechanism toggles | Benchmark/evaluators | Differs from GAB: scoring/policy benchmark, not runtime-mode intervention | Adjacent |
| AgentDojo, arXiv:2406.13352 | https://arxiv.org/abs/2406.13352 | Yes | Yes | Attacks and defenses | Defense prompts/modules vary | Models/agents compared | Some defenses alter tools | Mixed | Security | Attack/defense components | Benchmark/code released | Dynamic security benchmark; no GAB-style deterministic mechanism isolation | Adjacent |
| tau-bench, arXiv:2406.12045 | https://arxiv.org/abs/2406.12045 | Yes | Yes | Models and agent methods | Domain policy prompt varies in ablation | Models compared | API/environment fixed | Deterministic DB/API reward | Reliability/rule-following | Method/model | Benchmark released | Important substrate; policies in prompt/API, not runtime_mode toggles | Adjacent |
| OS-Harm, arXiv:2506.14866 | https://arxiv.org/abs/2506.14866 | Yes | Yes | Computer-use agents and judge variants | No | Agents/models compared; judge model ablated | No | LLM semantic judge | Safety | Judge/model ablation | GitHub benchmark | Safety benchmark, no runtime-mode ablation | Adjacent |
| SafeAgentBench, arXiv:2412.13178 | https://arxiv.org/abs/2412.13178 | Yes | Yes | Agent designs, LLMs, simple defenses | Baseline prompts omit safety hints; defenses alter design | LLM varied | Agent architecture varied | LLM planner/evaluator | Embodied safety | Agent config/defense ablations | Benchmark claimed | Safety benchmark, no deterministic runtime mechanism intervention | Adjacent |
| Agent-SafetyBench, arXiv:2412.14470 | https://arxiv.org/abs/2412.14470 | Yes | Yes | 16 agents and defense prompts | No | Models/agents varied | No | Model-backed scorer | Agent safety | Agent/defense prompt | Benchmark | Broad safety evaluation, not runtime-mode mechanism isolation | Adjacent |
| AutoHarness, arXiv:2603.03329 | https://arxiv.org/abs/2603.03329 | Yes | Yes | Synthesized code harness / action verifier / policy | Same optimized prompt reported for experiments, but harness is learned | Yes for harness-policy tests | Yes | LLM-synthesized code harness | Capability/reliability | Harness form, not governance components | TextArena eval | Strong on code harness as verifier under fixed prompt; game domain and learned harness | Weakens |
| Meta-Harness, arXiv:2603.28052 | https://arxiv.org/abs/2603.28052 | Yes | Yes | Searches over harness code | Prompt may be rewritten; prompt confounds discussed | Fixed language model objective | Yes | LLM/proposer rewrites harness code | Capability | Ablates feedback/access; qualitative confound isolation | TerminalBench/text evals | Strong fixed-model harness credit-assignment prior | Weakens |
| Agentic Harness Engineering, arXiv:2604.25850 | https://arxiv.org/abs/2604.25850 | Yes | Yes | Harness components evolved and ablated | No; prompt is editable component | Same base model in main loop | Yes | LLM-evolved components | Capability with self-modification governance | Component-level ablations | Terminal-Bench/SWE-bench eval | Very close on harness attribution; not governance and not held prompt | Weakens |
| HARBOR, arXiv:2604.20938 | https://arxiv.org/abs/2604.20938 | Yes | Yes | Flag-gated harness configs | Not prompt-centered; flags change harness | Same model/task set in case study | Yes | Hand/optimizer-selected flags | Capability/cost with safety check | Flag/config ablations | Reproducible task suite | Close on flag-gated harness ablation; not governance benchmark | Weakens |
| NeMo Guardrails, arXiv:2310.10501 | https://arxiv.org/abs/2310.10501 | Yes | Yes | Programmable rails | Prompt/runtime rails affect app behavior | Model-agnostic | Yes | Colang runtime plus LLM rails | Safety/control | Rails categories, not per-mechanism benchmark | Toolkit/eval tools | Background against "first programmable runtime guardrails" | Background |
| CoALA, arXiv:2309.02427 | https://arxiv.org/abs/2309.02427 | Yes | Yes | Conceptual architecture | N/A | N/A | N/A | N/A | Agent architecture/safety discussion | Modular framework | No | Background for modular action/control framing | Background |
| Code as Agent Harness, arXiv:2605.18747 | https://arxiv.org/abs/2605.18747 | Yes | Yes | Survey | N/A | N/A | N/A | N/A | Harness mechanisms/verification | Survey | No | Supports field vocabulary, not direct pre-emption | Background |
| AI Control, arXiv:2312.06942 | https://arxiv.org/abs/2312.06942 | Yes | Abstract and cited framing read | Protocols against intentional subversion | N/A | Trusted/untrusted models differ | Protocols | Model and protocol safety | AI safety/control | Protocol-level | Eval in paper | Shows current title promises a different safety problem | Background |
| Guardrails AI | https://github.com/guardrails-ai/guardrails | Yes | Repo/docs read | Input/output guards and validators | N/A | Model-agnostic | App guard layer | Validators, some ML/LLM | Reliability/governance | Validator composition | Guardrails Index/Hub | Guardrail ecosystem background, not agent runtime-mode ablation | Background |
| Invariant Guardrails | https://github.com/invariantlabs-ai/invariant | Yes | Repo/docs read | Rule-based layer between app and MCP/LLM | N/A | Model-agnostic | Yes | Rule-based guardrails | Security/governance | Rule layer | Product/tooling | Confirms runtime governance is production vocabulary | Background |
| OpenAI Harness Engineering | https://openai.com/index/harness-engineering/ | Yes | Page read | Engineering practice | N/A | Codex-focused | Yes | Repo docs, linters, feedback loops | Reliability/capability | Practice patterns | No | Broad harness-engineering claim is not novel | Background |
| Anthropic Effective Harnesses | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents | Yes | Page read | Long-running harness patterns | N/A | Claude-focused | Yes | Structured files, self-verification, tests | Reliability/capability | Practice patterns | Demo/codebook | Broad harness-improves-agents claim is not novel | Background |
| LangChain Anatomy of an Agent Harness | https://www.langchain.com/blog/the-anatomy-of-an-agent-harness | Yes | Page read | Conceptual/practitioner framing | N/A | N/A | Yes | Harness components | Capability/reliability | Component taxonomy | No | Establishes "Agent = Model + Harness" vocabulary | Background |

## Corrections to the prior dossier

| Dossier claim | Audit correction | Evidence |
|---|---|---|
| "NLAH / Pan et al. 2026" is likely hallucinated and should not be cited. | False. arXiv:2603.25723 exists: *Natural-Language Agent Harnesses*, Linyue Pan et al. It explicitly says harness logic is hard to ablate in code, introduces NLAH/IHR, and reports module ablations. | https://arxiv.org/abs/2603.25723 |
| Life-Harness does not report per-mechanism/layer ablation. | Overstated. It reports leave-one-layer-out ablations over Environment Contract, Procedural Skill, Action Realization, and Trajectory Regulation. | https://arxiv.org/abs/2605.22166 |
| ALIGN does not report per-mechanism ablation. | Overstated. It reports component ablations for InferRules and WrapStep. The delta is that the components are interface-enrichment/capability mechanisms, not deterministic governance runtime modes. | https://arxiv.org/abs/2505.21055 |
| Closest neighbors are only Life-Harness and ALIGN. | Incomplete. ABC, Guardrails as Infrastructure, AgentSpec, ContextCov, Verifier Tax, AHE, HARBOR, Meta-Harness, and AutoHarness are all load-bearing neighbors for different pieces of the claim. | URLs in ledger |
| "No prior work exists" on harness mechanism attribution can be defended broadly. | Too broad. Several papers already do fixed-model harness/interface attribution or component ablation. The defensible claim must be conjunctive and specific to deterministic governance runtime modes under held prompt. | Life-Harness, AHE, HARBOR, Meta-Harness, ABC |
| "Governance retained as an engineering layer; AI-control/safety umbrella dropped" is enough. | Needs refinement. Dropping AI-control as the title is wise; dropping safety/governance context entirely would hide the closest priors and ignore ETCLOVG's Governance/Verification layers. | https://openreview.net/forum?id=eONq7FdiHa |
| ST-WebAgentBench is listed as ICML 2025 in the dossier source list. | Incorrect for the verified arXiv text I read. arXiv:2410.06703v7 says "Published as a conference paper at ICLR 2026." | https://arxiv.org/abs/2410.06703 |

## Direct answers to audit questions

### 1. KEEP / REFINE / REPLACE?

**REFINE.** Replace the AI-control/trusted-monitor title and lead claim.
Do not replace it with generic "agent performance" harness capability
framing. Use runtime governance / verification as the engineering frame.

### 2. Does prior art pre-empt the narrow claim?

Not fully. I found no primary source with all required elements:
held model and prompt, hidden runtime-mode intervention, deterministic
governance mechanisms toggled individually, offline deterministic scorer,
and released mechanism-isolable benchmark.

The closest threats are:

- **Agent Behavioral Contracts**: contract governance, runtime
  enforcement, benchmark, contracted/uncontracted runs, true component
  ablation. It uses LLM-as-judge evaluation and contract components
  rather than hidden deterministic runtime modes.
- **Guardrails as Infrastructure**: deterministic model-agnostic policy
  layer with policy-pack ablations and trace replay. It is
  LLM-independent, so it does not test held-prompt/model agent behavior.
- **NLAH**: module ablations and explicit harness representation. It
  gives up hard determinism of code harness policy and does not study
  GAB-style governance mechanisms.
- **Life-Harness / ALIGN / AHE / HARBOR / Meta-Harness**: all weaken
  broad harness-attribution claims, but are capability/interface
  optimization papers.

### 3. Life-Harness and ALIGN deltas

Life-Harness:

- Correct: frozen model, runtime harness, broad harness vocabulary,
  capability/performance outcome.
- Correction: it has leave-one-layer-out ablation. The delta is not
  "no ablation"; the delta is that its harness is evolved from training
  trajectories, includes prompt-visible environment contracts/skills,
  and optimizes capability in deterministic environments rather than
  deterministic governance enforcement.

ALIGN:

- Correct: lightweight wrapper, no modification to agent logic or
  environment code, capability/performance objective.
- Correction: it has component ablations for InferRules and WrapStep.
  The delta is that ALIGN enriches static environment information and
  step-wise observations, not governance enforcement; it does not hold a
  deployment prompt fixed while secretly toggling runtime governance.

### 4. Is harness coupling fatal?

Not fatal, but fatal to additive or context-free attribution.

The Agent Harness Engineering survey says harness layers are coupled,
local improvements may degrade whole rollout, and scores cannot be
cleanly attributed without specifying the surrounding controller. That
does not invalidate GAB if the claim is:

> marginal effect of disabling mechanism X inside this fixed controller,
> prompt, scorer, task suite, evidence tier, and runtime implementation.

The planned defense is sufficient only if the paper reports:

- isolated `full_contract` vs `no_X` contrasts;
- full-stack rollouts;
- `no_runtime_enforcement` only as a sanity floor;
- interaction/coupling limitations;
- no additive "M4 contributes A plus M5 contributes B" language.

### 5. Is dropping AI-control/safety wise?

Dropping **AI-control as the external umbrella** is wise. The current
title invokes a literature about intentionally subversive untrusted
models and safety protocols. GAB does not test that.

Dropping **governance/safety context entirely** is unwise. Governance is
explicitly a first-class ETCLOVG harness layer, and the closest priors
are runtime enforcement, contracts, guardrails, safety mediation, and
compliance papers. The paper should be framed as AI engineering, but the
object being engineered is runtime governance.

### 6. Title and thesis

The dossier title is not optimal. Use a shorter measured-finding title:

1. **Ablating Runtime Governance in Agent Harnesses**
2. **Measuring Deterministic Governance Mechanisms in Agent Harnesses**
3. **Runtime-Mode Ablations for Reliable LLM Agent Operation**
4. **Mechanism-Level Evidence for Agent Harness Governance**
5. **Which Harness Governance Mechanisms Make Agents Reliable?**

Recommended thesis:

> Holding the model and deployment prompt fixed, GovernedAgentBench
> treats runtime mode as the intervention and measures how deterministic
> harness-governance mechanisms change reliable, constraint-respecting
> agent operation.

### 7. Does GAB differentiate from the named benchmarks?

Yes, on runtime-mode ablation as intervention.

- ST-WebAgentBench scores policy compliance under policy-injection and
  policy evaluators; it does not toggle deterministic runtime mechanisms.
- AgentDojo varies attacks, defenses, agents, and tools in a dynamic
  security environment; it does not isolate M4-M8-style runtime modes.
- tau-bench evaluates tool-agent-user reliability with deterministic
  DB rewards and domain policies; policies are prompt/API substrate, not
  hidden runtime governance toggles.
- OS-Harm evaluates computer-use safety with an LLM judge and judge/model
  ablations; it is not a deterministic scorer/runtime-mode benchmark.
- SafeAgentBench evaluates embodied safety-aware planning across agent
  designs, LLMs, and simple defenses; it does not run hidden
  mechanism-off governance modes.

Local GAB evidence supporting the difference:

- `BENCHMARK_CARD.md` says GAB measures runtime-mode ablations under a
  held-constant prompt, with 28 tasks and static oracle-pair canaries.
- `prompts/deployment_full_v1.md` says the template is byte-stable, held
  constant, and does not tell the model which runtime mode is active.
- `schema/trajectory.schema.json` makes `runtime_mode` a required field
  with `full_contract`, five mechanism-off modes, and
  `no_runtime_enforcement`.
- `oracles.py` says static oracle pairs are pure/deterministic/no-model
  and that `no_runtime_enforcement` is a robustness sanity floor, not
  per-mechanism attribution.

## Biggest underweighted risk

The biggest risk is **not** that no prior work exists. The risk is that
too much prior work exists for every broad version of the claim.

NLAH alone invalidates the dossier's "likely hallucinated" assumption.
Life-Harness and ALIGN have component/layer ablations. AHE and HARBOR
make fixed-model harness attribution an active topic. AgentSpec,
ContextCov, ABC, Guardrails as Infrastructure, SafeAgent, and Verifier
Tax already occupy runtime governance/enforcement. If the paper claims
"first harness governance," "first runtime enforcement," "first harness
ablation," or "agent harnesses as performance instruments are novel,"
reviewers can reject the framing without reaching the benchmark.

The paper survives if it narrows the contribution to a released,
mechanism-isolable benchmark and reports causal language as conditional
on one fixed controller, prompt, runtime, task suite, and evidence tier.
