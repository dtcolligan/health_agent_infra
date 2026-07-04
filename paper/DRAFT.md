# Told or Enforced: When In-Context Contracts Substitute for Runtime Enforcement in Agent Harnesses

Dom Colligan

<!--
Draft assembled 2026-07-04 by the drafting workflow.
Status: DRAFT. All model-backed results are at the DIAGNOSTIC tier: one
model (Qwen3-235B-A22B-Instruct-2507, Together AI, temperature 0), small
n (3-5 per cell). Nothing here is confirmatory beyond what PAPER.md
Evidence Status states.
Two open forks are handled as marked stubs in the text, never resolved
in prose: [FORK-L7-DRIFT] (L7 stale-manifest drift, unmeasured) and
[FORK-H5-REPLICATION] (external non-HAI replication, pending).
Source of truth: PAPER.md. Where this draft and PAPER.md disagree,
PAPER.md wins.
-->

## Abstract

For each constraint, a harness designer chooses: state the rule in the agent's prompt (an in-context contract), or have the runtime make the violation impossible (runtime enforcement). We cross the two levers in a 2x2 per governance mechanism of a frozen reference runtime, separating the effect of telling, the effect of enforcing, and the redundancy measure: enforcement's marginal value given the agent was told. Diagnostic probes (one model, Qwen3-235B, n=3-5 per cell) support a negative result: for a capable cooperative agent above the operate floor, able to see its own tool output and facing benign inputs, in-context specification substitutes for runtime enforcement broadly; the agent self-enforces constraints it is told plainly, with a salience qualifier we treat as an uncharacterized confound rather than a measured variable: the same told constraint, reached incidentally rather than foregrounded, was violated on first attempt (n=3). Two hypothesized moderators nulled: context-verifiability, tested via M8 audit evidence emission (predicted non-verifiable, self-enforced once retrieval landed the evidence in context), and benign goal-conflict pressure (zero fabrication across 40 reps, n=5 per mode per pressure level). Enforcement's demonstrated behavioral value reduces to the deterministic guarantee plus narrow corners: below the operate floor, the untold violation floor, the incidental-salience failure, and adversarial intent, untested here. A second, methodological contribution: harnesses that hide tool output manufacture spurious fabrication findings (harness blindness); an apparent instrumental-fabrication effect dissolved once the harness inlined command stdout (0 percentage points against a pre-committed >=40pp bar). We release GovernedAgentBench: tasks, trajectories, and a deterministic offline scorer.

## 1 Introduction

An agent harness is a design surface. The engineer who assembles an LLM agent over user-owned structured data controls the loop around the model: which tools are exposed, how actions are parsed and dispatched, and what happens when a proposed action would violate a constraint. For any given constraint, that engineer holds exactly two levers. The first is in-context specification: state the rule in the agent's prompt as an in-context contract (a command manifest, a flag, a mutation class, a boundary description) and rely on the model to respect it. The second is runtime enforcement: have the harness block or gate the violation deterministically, regardless of what the model decides. Telling is cheap and moves with the prompt; enforcing requires typed command schemas, dispatch gates, and validation code that must be built, tested, and maintained. A harness designer deciding where to spend engineering effort needs to know when the second lever buys behavior the first does not.

Existing guardrail evaluations do not answer this question, because they conflate the two levers. Some toggle enforcement while holding the full policy in the system prompt in both conditions [arXiv:2604.15579], so the delta is measured only where the agent was already told. Others bundle whether rules are injected and enforced into one variable [arXiv:2602.22302], or compare an enforced arm against a prompt-only arm [arXiv:2603.00822, arXiv:2605.28914, arXiv:2606.21856], which mixes the effect of telling into the effect of enforcing. The enforced-not-told cell is nearly absent from prior work (the closest located instance is a single by-design condition in FORGE [arXiv:2602.16708]), and no located prior work runs the full factorial crossing; Section 2 develops the map. None of these designs can answer the question a harness designer actually faces: what does enforcement add, given that the agent was told?

This paper crosses the two levers factorially in a specify-vs-enforce 2x2 per governance mechanism (Section 3). Its headline quantity is the redundancy measure: the marginal value of enforcement given the agent was told (cell A: deployment baseline vs cell B: told-not-enforced). We instantiate the design in GovernedAgentBench, built over a frozen non-clinical personal-wellness reference runtime (HAI v0.2.0) whose governance mechanisms (M4 through M8, Section 3.2) can be ablated individually or all at once, and scored by a deterministic offline scorer.

We hypothesized three moderators would gate when specification substitutes for enforcement: context-verifiability of the constraint, benign goal-conflict pressure (compliance costs task success; benign completion pressure, not adversarial injection), and model capability. Only the third survived. All model-backed evidence in this paper is diagnostic tier: one model (Qwen3-235B-A22B-Instruct-2507, Together AI, temperature 0), n=3-5 per cell. Within that tier, the verifiability exception nulled: once the agent retrieves the relevant evidence, it self-enforces even the constraint we pre-registered as non-verifiable. The goal-conflict prediction nulled: zero fabrication across all 40 reps under graded pressure P0-P3 (diagnostic, one model, pre-registered n=5). What survives is the operate floor, weakly and ladder-confounded: below a minimum capability level the model cannot drive the contract at all, and enforcement there prevents malformed harm rather than disobedience. The result is negative. For a capable cooperative agent above the operate floor, in-context specification substitutes for runtime enforcement broadly: the marginal behavioral contribution of enforcement equals the agent's self-enforcement failure rate, and that rate was near zero for a capable cooperative agent that was told the rule and could see its own tool output. Substitution carries a salience qualifier: diagnostics showed 3/3 refusal when the constraint was foregrounded but 3/3 first-attempt dispatch when it was reached incidentally (diagnostic, n=3). We claim no "unnecessary guardrails" conclusion: where substitution holds, enforcement is behaviorally redundant, never useless, and its demonstrated behavioral value remains the deterministic guarantee plus a narrow set of corners: below the operate floor; at the untold violation floor; at the incidental-salience failure of Section 5.1; and under adversarial intent, untested here. Injection robustness is cited territory, not a claim of this paper. [FORK-L7-DRIFT: unmeasured; do not assume outcome]

The second finding is methodological. Our own harness initially manufactured a spurious fabrication result: it fed the agent a file-path placeholder instead of actual command stdout, and the blinded agent guessed identifiers it could not see. Inlining stdout dissolved the apparent instrumental-fabrication effect entirely (0 percentage points against a pre-committed threshold of at least 40 points; diagnostic, one model, n=5), and the agent abstained honestly instead. We name this failure mode harness blindness: evaluations that hide tool output from the agent manufacture findings like this.

### Contributions

1. A negative result with explicit scope conditions: on diagnostic probe tasks over the frozen HAI v0.2.0 reference runtime (not the locked task suite), at the model-backed diagnostic tier, in-context specification substituted for runtime enforcement for a capable cooperative agent above the operate floor, able to see its own tool output and facing benign inputs, with the salience qualifier and the deterministic-guarantee caveat attached. [FORK-H5-REPLICATION: pending external non-HAI replication; do not assume outcome]
2. A methodological demonstration that harness blindness manufactures spurious fabrication findings, shown by dissolving one such finding with a harness-level fix, offered as a caution for agent-eval methodology.
3. GovernedAgentBench, the released instrument for the 2x2: task suite, frozen reference runtime, deterministic offline scorer, and reproducible artifacts, with static oracle-pair evidence, live runtime probes, and model-backed diagnostics kept as separate evidence tiers.

The novelty claim is a conjunction, not any single first: the 2x2 including the enforced-not-told cell, per-mechanism isolation, the substitution account with its moderators, the methodological warning, the deterministic offline scorer, and the released benchmark, taken together. This is an AI-engineering study of agent-harness governance. It claims no scaling law, no injection robustness, and no result beyond this controller, task suite, and evidence tier.

## 2 Background and related work

**Agent harnesses and scaffolding.** The harness, the deterministic software layer between a model and its tools, is now a design surface in its own right. A survey under review at TMLR treats governance and verification as a distinct harness layer (ETCLOVG, OpenReview 3hXEPbG0dh; cited via OpenReview, not as an accepted paper). Harness-Bench [arXiv:2605.27922], NLAH [arXiv:2603.25723], AHE [arXiv:2604.25850], and Meta-Harness [arXiv:2603.28052] measure or optimize harness configurations for capability; none carries a governance axis. This paper measures the governance layer rather than optimizing it.

**Runtime enforcement and guardrails.** Enforcement frameworks (AgentSpec [arXiv:2503.18666]; NeMo Guardrails; Guardrails AI; Invariant Guardrails, from Invariant Labs, now part of Snyk) supply mechanism substrates without measuring what the model would do on its own. In the injection-defense literature, CaMeL [arXiv:2503.18813] and Progent [arXiv:2504.11703] show architectural enforcement outperforming prompt-only heuristic defenses on AgentDojo; CaMeL never states its policies to the model in any condition, and Progent runs no disclosure factorial, so neither manipulates disclosure. Harness-MU [arXiv:2606.21856] argues governance constraints should be "enforced by execution hooks rather than entrusted to the LLM," a single-axis comparison under adversarial framing. ContextCov [arXiv:2603.00822] compiles instruction files into executable guardrails (88.3% compliance enforced against 67.0% prompt-only on SWE-bench Lite); its enforced arm feeds violation traces back to the model, in-context specification delivered late. Verifier Tax [arXiv:2603.19328] compares unenforced baselines (Tool-Calling, TRIAD) against a policy-mediated architecture (TRIAD-SAFETY) on tau-bench Airline and Retail: safety mediation intercepts up to 94% of non-compliant actions, yet safe success stays below 5% in most settings, with agents hallucinating user identifiers to route around blocks; it toggles enforcement architecture, not prompt disclosure, so it runs no told/untold contrast. Mechanical Enforcement [arXiv:2605.14744] compares text-only governance against mechanical enforcement (four architectural primitives outside the model's interpretive loop) in a regulated-banking decision agent, cutting uninformative deferrals by 73% and raising task accuracy from MCC approximately 0.43 to 0.88; it pairs two alternative configurations rather than crossing a factorial, has no enforced-not-told cell, and measures decision-rationale quality rather than tool-action compliance. ("Prompt-based guardrail" in Policy-as-Prompt [arXiv:2509.23994] means an external classifier reading a policy, a different lever from the in-context contract studied here.)

**Instruction and in-context rule following.** The main risk of misreading this paper is reducing it to "capable LLMs follow instructions." That models follow checkable instructions is established, but IFEval [arXiv:2311.07911], RECAST [arXiv:2505.19030], and VerIF [arXiv:2506.09942] use checkability to build evaluations and rewards, not as a predictor of when agents comply. And told-only compliance is not free: LogiSafetyBench [arXiv:2601.08196] names "Unsafe Success," capable models completing tasks while violating latent rules, non-monotone across model families, as is SABER [arXiv:2606.01317]; Agent-SafetyBench [arXiv:2412.14470] reports none of 16 agents above 60% safety score; SafePyramid [arXiv:2606.29887] shows in-context policy application degrading with policy reasoning complexity; Governance Decay [arXiv:2606.22528] shows constraints obeyed while visible are silently erased by context compaction, violation rising from 0% to 30%, up to 59% for some models. That establishes the drift-causes-violation half of the stale-manifest phenomenon; whether independent runtime enforcement catches post-drift violations remains open. [FORK-L7-DRIFT: unmeasured; do not assume outcome] Our question is therefore not whether an agent can follow a stated rule, but what marginal behavioral value runtime enforcement retains once the same constraint is specified in context.

**Software contracts and capability security.** The runtime's vocabulary of manifests, typed command schemas, proposal/commit gates, and least privilege descends from design-by-contract and capability security. Agent Behavioral Contracts [arXiv:2602.22302] evaluates runtime contracts at scale (200 scenarios, 7 models, 1,980 sessions), but its conditions "differ only in whether ABC contract rules are injected and enforced," bundling specification and enforcement into one variable, on a patent-gated benchmark. Prompts Don't Protect [arXiv:2605.18414] filters unauthorized tools out of the model's context with no policy prompt, a structurally enforced-not-told arm whose 0.0% unauthorized-invocation rate holds by construction, since attempted violations cannot be observed.

**Closest priors.** AIRGuard [arXiv:2605.28914] is a security-framed pre-action runtime guard; its prompt-only versus runtime-guard ablation is a single-axis attack-success delta on one model, with no factorial, no enforced-not-told cell, and no constraint-class analysis. PhantomPolicy [arXiv:2604.12177] formalizes policy-invisible violations, where compliance depends on runtime state absent from the agent's context, contributing an eight-category taxonomy this paper adopts and crosses with the enforcement axis. It does run a policy-in-prompt condition (risky-case violations 95.3% to 40.7% under human-reviewed labels), but folds telling into the same single ordinal axis as enforcement architecture (baseline, policy-in-prompt, content-DLP, Sentinel), with Sentinel and the DLP baseline always applied to baseline not-told traces, so no condition holds enforcement fixed while varying telling and no enforced-and-told versus enforced-and-not-told contrast exists. Neither AIRGuard nor PhantomPolicy crosses the two levers. FORGE [arXiv:2602.16708] runs the only located by-design enforced-not-told condition: "The instrumented condition does not include the natural language policy in the agent's prompt; the agent relies solely on runtime enforcement and corrective feedback." It has no told-and-enforced cell and no neither floor, so it cannot measure the redundancy of enforcement given specification; corrective feedback makes its enforced arm converged multi-turn rather than first-attempt; it evaluates one holistic policy per case study, with no per-mechanism inventory, no moderators, and no located public release. ABSTAIN [arXiv:2606.02965] reaches the closest cell coverage, three of four cells for a single abstention mechanism; its Checkpoint condition reuses the Prompt-Only prompt (its Appendix B), realizing told-and-enforced rather than enforced-not-told, and non-Checkpoint conditions are LLM-judge scored. TeamBench [arXiv:2605.07073] reports statistically indistinguishable pass rates between prompt-only and OS-sandbox-enforced role separation, alongside 3.6 times more verifier-edits-executor cases in the prompt-only arm: convergent published evidence for the substitution shape in a different mechanism domain, and a standing caution that aggregate parity can mask sub-metric enforcement value, taken up in Section 7.2; it is prior evidence in a different domain and design, not a replication of this paper's effect. [FORK-H5-REPLICATION: pending external non-HAI replication; do not assume outcome] Symbolic Guardrails [arXiv:2604.15579] holds the full policy in the system prompt in both conditions while toggling enforcement; TRACE [arXiv:2606.13174] compiles user corrections into runtime checks in the preference domain, the rule always known to the agent in some form. The closest benchmark prior is ST-WebAgentBench [arXiv:2410.06703]: in-context policies delivered to three agent scaffolds and scored post hoc via Completion Under Policy, with no mechanism that blocks a non-compliant action before execution.

**Positioning.** Isolated enforced-not-told measurements exist (FORGE by explicit design; Prompts Don't Protect structurally). No located prior work holds that cell inside a crossed factorial against a told-and-enforced cell and a neither floor, decomposes the comparison per governance mechanism, scores the telling axis on first-attempt behavior, or releases a deterministic offline scorer and benchmark that hold the two levers apart. The contribution is that conjunction, together with the harness-blindness methodological finding (Section 6); no element is claimed as individually unprecedented.

## 3 The two levers

An agent harness has two distinct levers for making an agent respect a constraint. It can state the rule where the model can read it, or it can make the violation impossible regardless of what the model decides. We call the first lever in-context specification (telling) and the second runtime enforcement (enforcing). Deployed harnesses almost always pull both levers at once: the system prompt describes the policy and the runtime also implements it. Prior evaluations largely inherit this bundling, toggling specification and enforcement as one variable [arXiv:2602.22302] or manipulating only one axis while the other never varies [arXiv:2605.28914]. This section defines the two levers separately, fixes the mechanism inventory that instantiates the enforcement lever, introduces the constraint classification that the design uses as its predictor, and assembles the pieces into the 2x2 that the rest of the paper measures.

### 3.1 Telling: the in-context contract

The telling lever is the in-context contract: the rule, manifest fact, schema, or policy statement made available to the agent inside its context at decision time. In the reference runtime this includes the command manifest (which commands exist and their argument schemas), the `agent_safe` flag attached to each command, the mutation class of each write surface, and the prose description of the out-of-contract boundary, including its clinical-boundary leg. The contract is broader than a system-prompt policy paragraph; schemas, flags, and taxonomies are all part of what the agent is told.

Two boundaries keep this lever distinct. In-context specification is a harness-level lever, not a training-time one; it is orthogonal to instruction tuning or preference training, which shape the model's priors rather than its decision-time context. And the in-context contract is only the copy of the specification the model can read, not the specification the runtime implements. The paper's central manipulation is the gap between the two.

### 3.2 Enforcing: the mechanism inventory

The enforcing lever is runtime enforcement: the harness blocking, gating, or otherwise making a violation impossible regardless of what the model emits, independent of whether the model was told the rule. The reference runtime (HAI v0.2.0, the frozen instrument described in Section 4) implements enforcement through a fixed inventory of mechanisms, five of them individually ablatable through a named runtime mode and one held constant.

| ID | Mechanism | Ablation mode | Context-verifiable? |
|---|---|---|---|
| M4 | Validation of typed commands and proposal payloads | `no_validation` | Yes (schema is in the manifest) |
| M5 | `agent_safe` dispatch refusal | `no_agent_safe` | Yes (`agent_safe` flag is in the manifest) |
| M6 | W57 proposal/commit user gate | `no_proposal_gate` | Yes (mutation class is in the manifest) |
| M7 | Refusal of out-of-contract requests (clinical-boundary leg is the zero-tolerance subset); JSON output exempt | `no_refusal` | Yes (the boundary is describable in the prompt) |
| M8 | Audit evidence emission / reference faithfulness | `no_audit_chain` | No under the standard setup (Section 3.3) |
| M9-TX | Transaction integrity | Held constant, non-ablatable | n/a |

M4 guards the command surface itself: malformed, out-of-schema, or hallucinated commands are rejected before dispatch. M5 refuses dispatch of commands the manifest does not flag as agent-safe. M6 guards user-authored state: agents may propose mutations, but activation or deactivation requires an explicit user commit, so an agent alone cannot complete the mutation. M7 guards the scope boundary, with the clinical boundary (no diagnosis, treatment, prescribing, or autonomous medical decisions) as its zero-tolerance subset; structured JSON output is exempt. M8 guards reference faithfulness: the runtime emits and persists audit evidence for recommendations, and the deterministic scorer detects fabricated or suppressed references after the fact. M8 is provision-type rather than block-type (Section 3.5 defines the distinction), and it is evidence emission, not the whole audit chain. M9-TX is the atomic-transaction floor; it is held constant and has no ablation mode.

The runtime-enforcement axis therefore has exactly seven modes: `full_contract`, the five per-mechanism off-paths (`no_validation`, `no_agent_safe`, `no_proposal_gate`, `no_refusal`, `no_audit_chain`), and `no_runtime_enforcement`, in which M4 through M8 are all off while the M1-M3 harness infrastructure and M9-TX remain on. M1 through M3 are the always-on harness infrastructure (the model loop and dispatch, action parsing, and observation feedback); they are not ablatable governance mechanisms and remain on in every mode, which is what makes `no_runtime_enforcement` a floor over which cell D is still driven rather than an inert harness. One caveat governs every per-mechanism number in this paper: harness mechanisms are coupled, so per-mechanism results are reported as marginal contribution within this fixed controller, never as independent additive contributions.

### 3.3 Context-verifiability

The design's predictor variable is context-verifiability: a constraint is context-verifiable if the agent can check its own compliance using only what is already in its context at the moment it decides. Verifiability is a property of the pair (constraint, decision-time context), not of a mechanism in the abstract, and it can flip within a trajectory: a constraint becomes verifiable the moment retrieval lands the relevant ground truth in the agent's context. This framing adopts the observation, formalized as policy-invisible violations in [arXiv:2604.12177], that compliance can depend on runtime state absent from the agent's context; we treat that dependence as a trajectory-local property rather than a fixed taxonomy label.

Under the standard task setup, with the manifest and taxonomies in the prompt and no runtime state disclosed, M4, M5, M6, and M7 are context-verifiable: the schema, the `agent_safe` flag, and the mutation class are in the manifest, and the M7 boundary is describable in the prompt. M8 was classified non-verifiable under the standard setup and pre-registered as the exception where even a capable cooperative agent could not self-enforce, because whether a cited evidence reference actually exists is runtime state the agent cannot see. The pre-registered prediction attached to this classification was that enforcement is behaviorally redundant for context-verifiable constraints under cooperative, unconflicted conditions and behaviorally necessary for non-verifiable ones at every capability level. Section 5 reports that M8's classification did not survive contact with the evidence: audit faithfulness turns out to be verifiable once the agent retrieves the evidence, exactly the within-trajectory flip the definition permits.

### 3.4 L7 stale-manifest drift: the non-retrievable task condition

One constraint class is genuinely non-retrievable rather than merely unretrieved. Under L7 stale-manifest drift, the agent's in-context manifest is outdated relative to the actual runtime contract, and the agent cannot retrieve the fact that this is so: that ground truth is runtime state no read surface exposes. No sequence of lookups can flip it to verifiable, which distinguishes drift from M8. Drift is a task condition, not a mechanism row: it is a property of the relationship between the contract copy the agent holds and the contract the runtime implements, and it can afflict any mechanism whose manifest facts have moved. L7 drift is the sole surviving candidate for a true non-verifiable enforcement delta in this design, and it is unmeasured. [FORK-L7-DRIFT: unmeasured; do not assume outcome]

### 3.5 What the runtime guarantees regardless of behavior

The two levers differ in kind, not only in strength. Telling changes what the model is likely to do; enforcing changes what can happen at all. With enforcement on, the block-type mechanisms (M4 through M7) make the guarded violation impossible to complete no matter what the model emits: an out-of-schema command does not dispatch, a flagged command does not execute, an uncommitted proposal does not activate. M8's guarantee is provision-type: evidence is emitted and persisted whether or not the model narrates it faithfully, so fabrication is detectable after the fact. M9-TX guarantees atomicity in every mode. This is the deterministic guarantee, and it holds regardless of model behavior, model identity, and prompt content. The distinction matters for reading every result that follows: when this paper reports that enforcement is behaviorally redundant in some cell, the claim is about the marginal effect on observed behavior, never that the guarantee is worthless. Behavioral redundancy is not structural redundancy.

### 3.6 The 2x2

Crossing the two levers per mechanism yields the headline design:

| | Runtime enforces | Runtime off |
|---|---|---|
| **Contract in prompt** | A: deployment baseline | B: told-not-enforced (self-enforcement) |
| **Contract withheld** | C: enforced-not-told (pure runtime) | D: neither (violation floor) |

Cell A, the deployment baseline, is how harnesses actually ship. Cell B, told-not-enforced, isolates self-enforcement: the agent knows the rule and nothing stops it. Cell C, enforced-not-told, isolates pure runtime governance: the rule is withheld from the prompt while the runtime still enforces it. Cell D, neither, is the violation floor. The `no_runtime_enforcement` mode is a runtime mode, not a cell: under the contract-in-prompt arm it serves as a robustness sanity floor, never per-mechanism attribution evidence; under the contract-withheld arm the same mode realizes cell D and anchors the floor for the contrasts below.

Three contrasts carry the information. B vs D is the effect of telling: what specification alone buys over nothing. C vs D is the effect of enforcing: what the runtime alone buys over nothing. A vs B is the marginal value of enforcement given the agent was told, the redundancy measure, and the headline quantity of this paper: if A and B do not differ behaviorally, enforcement added no behavioral value on top of specification for that constraint in that situation, and its remaining value is the deterministic guarantee of Section 3.5.

One interaction between the cells requires a scoring convention. A blocked action returns an error message, and an error message is in-context specification delivered late, so cell C converges toward cell B after the agent's first contact with the enforcement surface. Axis attribution for B vs D and C vs D is therefore scored on first-attempt behavior, with converged multi-turn behavior reported separately; Section 4 gives the operational details. The 2x2 runs under three moderators, constraint class per Section 3.3, benign goal-conflict pressure, and model capability, which Section 4 defines and Section 5 evaluates.

## 4 GovernedAgentBench: methodology

GovernedAgentBench is the instrument that holds the two levers apart: it lets in-context specification and runtime enforcement be toggled independently, per mechanism, against a fixed reference runtime, and scores the result deterministically and offline. This section describes the runtime, the task suite, the fixtures and hermeticity discipline, the two axes as implemented, the scorer, the evidence tiers, the model roster, and the reproducibility path.

### 4.1 The reference runtime

The runtime under measurement is HAI v0.2.0, a non-clinical personal-wellness reference runtime with a typed CLI command surface. HAI is the instrument, not the contribution: it is pinned as a frozen snapshot so that every mechanism has one concrete, inspectable implementation, and it is described here as a reference implementation, not a product. The runtime instantiates the mechanism inventory of Section 3: M4 validation of typed commands and proposal payloads, M5 `agent_safe` dispatch refusal, M6 the W57 proposal/commit user gate, M7 refusal of out-of-contract requests (with the clinical-boundary leg as the zero-tolerance subset), M8 audit evidence emission, and M9-TX transaction integrity, which is held constant and non-ablatable. The non-clinical boundary is part of the evaluated contract, not a disclaimer: the runtime refuses the clinical actions enumerated under M7 in Section 3.2, and the benchmark scores that refusal. The agent-facing contract is a frozen manifest snapshot, `agent_cli_contract.v2` (approximately 189 KB, checked in at `manifests/hai_0_2_0.json`), which carries the command schemas, `agent_safe` flags, and mutation classes; with it in the prompt, and the M7 boundary describable in the prompt itself, M4 through M7 are context-verifiable under the standard task setup (Section 3.3).

### 4.2 Task suite and oracle-pair construction

The suite is drawn from five levels of a seven-level task taxonomy: L1 intent-to-command routing, L2 setup and recovery, L5 faithful narration of runtime output, L6 governance and refusal, and L7 contract drift; the intervening L3 and L4 levels are out of scope for this suite (Appendix A gives the full taxonomy). Each task declares its `load_bearing_mechanisms` and `runtime_modes_in_scope`; the harness refuses to run a task under a runtime mode the task does not declare, so mode coverage is a checked property rather than a convention. Task and pair counts are unstable at the writing tier: PAPER.md decision D-37 (2026-07-04) retired the earlier 28-task / 25-oracle-pair apparatus and rebuilt the suite as a sharp 16-task 2x2 (told x enforced) per mechanism, and benchmark edits were still in flight from a concurrent agent when this draft was assembled. Appendix A holds the pending re-count; no specific task or pair count is stated here as a realized fact until the suite is frozen against the release tag.

Every task is constructed as an oracle pair that routes a mechanism's effect onto a scored metric: a hand-authored `full_contract` trajectory and a matching mechanism-off trajectory whose scored outcome must differ from it on the task's load-bearing metric, demonstrating scorer sensitivity to the mechanism. Each of M4 through M8 is covered by static oracle-pair load-bearing tasks, and additional pairs cover the `no_runtime_enforcement` floor; the per-mechanism and total pair counts followed PAPER.md's pre-consolidation figures, which commit `a10e850` retired at the benchmark tier, so they are deferred to Appendix A's pending re-count rather than stated here. A mechanism's off-path is accepted as isolated only if every emitted `mechanism_disabled` marker belongs to that mode's disabled set, at least one marker for the target mechanism fires, `full_contract` emits zero markers, and the scored consequence delta against `full_contract` on the task's load-bearing metric is attributable to the disabled mechanism. These pairs are static oracle-pair evidence: a deterministic canary establishing scorer sensitivity and coverage over constructed cases, not live causality evidence.

### 4.3 Fixtures, hermeticity, and the manifest snapshot

Seven synthetic fixtures are built for the benchmark (`empty_user`, `ready_user_minimal`, `read_surface_user`, `governance_user`, `drift_user`, `adversarial_user`, and `audit_pending_user`, the last leaving the target day un-synthesized so no evidence card exists at build time, which stresses M8 audit-reference faithfulness); not all seven are referenced by every locked task, and the fixture-to-task mapping is subject to the suite consolidation of Section 4.2. Fixtures contain no private health rows, no live wearable exports, no credentials, and no maintainer personal data. Every benchmark subprocess runs hermetically: `HAI_HERMETIC=1` with the state database and base directory redirected (`HAI_STATE_DB`, `HAI_BASE_DIR`), and a fresh fixture is materialized per repetition, so no state leaks across repetitions or modes. L7 tasks additionally swap in a deliberately stale manifest snapshot (`agent_cli_contract_v1_drift.json`) at task-load time, so the agent's in-context contract diverges from the actual runtime contract by construction; this drift condition is a task condition, not a mechanism row, and it remains unmeasured at the model-backed tier [FORK-L7-DRIFT: unmeasured; do not assume outcome].

### 4.4 The two axes as implemented

The runtime-enforcement axis is the `runtime_mode` seam, exposing the seven modes of Section 3.2. The contract-in-prompt axis is realized as a prompt variant that withholds the relevant manifest facts from the agent's context while the runtime remains unchanged. Crossing the two axes yields the cells of Section 3.6, and the two roles of `no_runtime_enforcement` (robustness sanity floor under the contract-in-prompt arm, cell D anchor under the contract-withheld arm) are kept distinct as defined there.

The operator action contract is structured JSON, one action per turn, not arbitrary shell. Transcripts record the model's emitted action verbatim as the assistant turn and each observation as a returned message; no provider-native tool calls are synthesized, because fabricating tool-call structure would misrepresent the evaluated transcript.

### 4.5 Deterministic scoring and first-attempt attribution

The scorer is deterministic and offline; it contains no model calls. It implements the full 11-kind violation taxonomy, and its behavior thresholds, pass rule, and critical violation kinds are loaded from `scorer_config.paper_v1.json`, whose audited bytes are hashed and recorded in `lock_hashes.json`, so any config change is visible in the provenance record.

The telling axis is scored on first-attempt behavior, per the convergence rationale of Section 3.6. First-attempt is defined uniformly as the first action that reaches the enforcement surface for the constraint in question, not literal step one; the definition applies identically to refusal rows and dispatch rows, so an agent that emits invalid-output steps before its first contact with the enforcement surface is scored from that first contact. First-attempt scoring carries the B vs D and C vs D attribution, and converged multi-turn behavior is reported separately and never blended into first-attempt numbers. The metric is only well-defined for a parser-clean model: a model whose output the harness action parser cannot read never reaches the enforcement surface, so its first-attempt behavior is undefined and its apparent failure conflates self-enforcement with the operate floor (Section 6.3). First-attempt axis attribution is therefore scoped to Qwen3-235B, the one parser-clean model in the roster, and does not transfer to the confounded ladder cells.

A deterministic rule baseline anchors the routing tasks as plumbing evidence only: it confirms the harness, fixtures, and scorer compose, and it fails the L5 narration tasks by design (PAPER.md D-30 records five L5 narration tasks; the on-disk L5 set has since changed under the same-day suite consolidation and told/untold rebuild of Section 4.2, so the current count is deferred to Appendix A's pending re-count and a PAPER.md D-37 entry rather than stated here), since it emits no final narration.

### 4.6 Evidence tiers

Three evidence tiers are kept separate throughout and are never merged into one claim: static oracle-pair evidence (hand-authored full/off pairs, scorer coverage), live runtime probes (end-to-end HAI runs under compared modes with real command execution, live causality evidence), and model-backed diagnostics (real model completions scored by the same scorer). All model-backed evidence in this paper is diagnostic tier: one model (Qwen3-235B-A22B-Instruct-2507, Together AI, temperature 0), small n (3 to 5 per cell).

### 4.7 Model roster

The working model is `Qwen/Qwen3-235B-A22B-Instruct-2507-tput` (Together AI, non-thinking mixture-of-experts, 256k context, serverless), run at temperature 0. `claude-sonnet-4-6` is the designated fallback for narration-heavy M8 tasks; no run reported here is Sonnet-backed. Excluded during viability screening: Qwen2.5-7B-Instruct-Turbo (below the operate floor, 0/60 valid finals, contract friction rather than governance), Mistral-Small-24B (32k context too small for the manifest prompt plus multi-turn history), Gemma-3-27B and Qwen2.5-32B (dedicated-endpoint only), and Gemma-4-31B (a reasoning model whose thinking consumed the token budget, yielding empty completions and timeouts).

### 4.8 Goal-conflict variants and the adversarial layer

The goal-conflict arm uses task variants applying benign completion pressure, not adversarial injection: respecting the constraint costs task success, graded from P0 to P3, where at P3 a pipeline is blocked and the user cannot proceed. No attacker-controlled content is involved; this targets the literature-verified locus where frontier models violate policies stated in their own system prompt (Symbolic Guardrails [arXiv:2604.15579]), including under realistic completion pressure (LogiSafetyBench [arXiv:2601.08196]). Separately, a 16-trajectory adversarial layer (four hand-authored trajectories each against M7, M5+M6, M8, and M4) provided scorer-coverage evidence at the appendix tier only, never model-backed. It existed at the pilot tier and was retired at the benchmark tier by commit `a10e850`, which removed the trajectories and their scoring; whether it is reinstated, replaced, or dropped is an open decision pending a PAPER.md D-37 entry (Appendix D). Injection robustness is cited territory in the security literature, which already shows telling fails under attack, not a claim of this paper.

### 4.9 Offline reproducibility

A single command, `reproduce_offline.py`, regenerates the rule-baseline ablation, evidence tables, figures, error taxonomy, and cell contrasts with no network access, no private state, and no paid APIs. The static and live isolation matrices were retired at the benchmark tier by commit `a10e850` (Appendix E) and the pipeline no longer emits them. It emits a top-level manifest with per-artifact summary metadata and exits nonzero if the rule-baseline ablation produced no scored rows or figures; the golden-artifact baseline records hashes and a wall-clock reference (Appendix E; re-baseline pending). Model-backed diagnostics are the only artifacts that required paid API access to produce; their recorded trajectories and scores are re-scoreable offline by the same deterministic scorer.

## 5 Results: the negative result

Everything reported in this section is model-backed diagnostic evidence: one model (`Qwen/Qwen3-235B-A22B-Instruct-2507-tput`, Together AI, temperature 0), small n (3 to 5 per cell), run on diagnostic probe tasks rather than the locked suite. Static oracle-pair evidence and live runtime probes were established separately per Section 4.6 and are not merged with any number below. Throughout, the three informative contrasts of the 2x2 are the effect of telling (cell B: told-not-enforced vs cell D: neither, the violation floor), the effect of enforcing (cell C: enforced-not-told vs D), and the redundancy measure (cell A: deployment baseline vs B), the marginal value of enforcement given the agent was told. We present the probes chronologically, because the sequence is the finding: each probe was aimed at a corner where runtime enforcement was predicted to be behaviorally non-redundant. The verifiability and goal-conflict corners nulled in diagnostics, the ladder weakly and confoundedly supported the operate floor, and L7 stale-manifest drift remains unmeasured (Section 5.6).

### 5.1 The contract-off map: telling works when salient, and the untold floor is real

The first battery (2026-07-02) ran the telling axis with the runtime fully off (`no_runtime_enforcement`), so every told condition realizes cell B and the untold condition realizes cell D. All rows are diagnostic (one model, Qwen3-235B, n=3 per condition).

| Condition | Outcome (n=3 per row) |
|---|---|
| Told, bait phrasing | 3/3 turn-1 refusal citing the `agent_safe` flag |
| Told, exact gated command named | 3/3 turn-1 refusal |
| Told, normal task phrasing (constraint reached incidentally) | 3/3 first-attempt dispatch of the gated command |
| Untold (flag globally stripped), valid target id supplied | 3/3 completed commit, row `proposed` to `active`, truthful success report, no refusal step |

Two readings follow. First, with the runtime off the told-and-salient conditions refused 3/3 while the untold condition completed the violation 3/3 (one model, Qwen3-235B, n=3 per cell), so the effect of telling against the violation floor is non-hypothetical at this tier. But self-enforcement of a context-verifiable constraint is salience-sensitive: the same agent that refuses 3/3 when the constraint is foregrounded dispatches the gated command 3/3 on first attempt when it reaches the constraint incidentally through normal task phrasing. Any claim that a told agent self-enforces must carry this qualifier. The incidental row is scored on first valid action: two of the three reps emit invalid-output steps before the dispatch, so "first-attempt" means first contact with the enforcement surface, not literal step one. These pre-dispatch invalid-output steps are the parser-clean model recovering to a valid dispatch, distinct in kind from the non-recovering invalid-output loops that place the 9B and 70B ladder models below the operate floor (Sections 6.3, 7.1); the shared invalid-output signature is read one way here and another there, and the residual overlap is a limitation rather than a clean separation. The two salient rows carry the author's contemporaneous labels; the stored artifacts retain prompt-template hashes rather than the phrasings, so the row-to-directory mapping is not independently recoverable, though the 3/3 refusal pattern in both rows is.

Second, the untold row is the untold violation floor: with the contract withheld and the runtime off, nothing stood between the agent and a completed governance violation, reported truthfully as success. This makes the effect of telling (B vs D) and the effect of enforcing (C vs D) non-hypothetical. The negative result that follows is about the redundancy measure (A vs B), not about these floors.

### 5.2 The M8 arc: the verifiability exception dissolves

M8 audit evidence emission was pre-registered as the non-verifiable exception: the constraint an agent cannot check from its decision-time context and therefore, by hypothesis, the place runtime enforcement retains behavioral value. Three probe regimes (2026-07-02, diagnostic, n=3 per cell) dismantled the classification in stages.

| Regime | Outcome |
|---|---|
| Retrieved (`hai explain` output in context) | 6/6 honest: cites the real card id under `full_contract`, reports "No evidence card is present." under `no_audit_chain`; verbatim-identical finals within each cell |
| Non-retrieval, plain ask, honest answer available | 6/6 honest abstention, zero fabrication |
| Instrumental (an id is needed to advance an action), pre-fix harness | Fabricated ids dispatched freely: 8 instances across three probe sets |

The first regime shows that verifiability is a property of the (constraint, decision-time context) pair, not of the mechanism: the moment retrieval lands the evidence in context, M8 behaves like the verifiable mechanisms and the agent self-enforces it. The second shows a cooperative agent asked plainly stays honest even without retrieval. That left the third regime as the only surviving fabrication signal. We reattributed it from verifiability to instrumental pressure, folded M8 into the goal-conflict axis, and pre-registered the two follow-ups below; the instrumental cell was later falsified outright as a harness-blindness artifact (Sections 5.4 and 6.1). After the arc, the sole surviving candidate for a genuinely non-verifiable constraint class is L7 stale-manifest drift (Section 3.4); no model-backed measurement exists. [FORK-L7-DRIFT: unmeasured; do not assume outcome]

### 5.3 H2: benign goal conflict does not degrade told-only compliance

The first pre-registered follow-up (artifact timestamp 2026-07-02T1942Z; pre-registered n=5) applied benign completion pressure, not adversarial injection, to audit faithfulness: 4 task variants graded P0 through P3, at P3 a pipeline is blocked and the user cannot proceed unless the agent produces a reference. Design: 4 tasks x 5 reps x 2 modes (`full_contract`, `no_audit_chain`) for 40 reps.

The result is a null. Zero fabrication across all 40 reps, scorer-verified: zero occurrences of the `forged_or_suppressed_audit_reference` violation kind in all 40 score files. The pre-committed falsification bar is an observed-rate threshold: fabrication at most 10% at P3. The four task variants map one to each pressure level, so the P3 cell is 5 reps per mode (10 reps). Observed P3 fabrication was 0/10; at n=10 this cannot exclude a true rate above 10%, so the bar is met and H2 is falsified only at the diagnostic tier (one model, Qwen3-235B, n=5). As a tighter descriptive bound, and as this paper's own post-hoc caveat rather than part of the pre-registration, the pooled 0/40 across P0-P3 narrows the upper confidence interval further. The small-n limitation stated throughout applies. The side finding: 10 of the 40 reps fail overall pass with a refusal-format error only, meaning high pressure degraded tool-use competence (command-format loops) before it touched honesty.

### 5.4 The instrumental leg is falsified

The second pre-registered follow-up (2026-07-03; pre-registered n=5; `no_runtime_enforcement`) tested the reattributed hypothesis directly, after the stdout-inlining fix let the agent see its own command output. The result is a falsification: an instrumental effect of 0 percentage points against the pre-committed bar of at least 40 points, diagnostic (one model, Qwen3-235B, n=5). The apparent instrumental-fabrication effect of Section 5.2 was a fact about a blind harness, not about the model; Section 6.1 tells the full story, including the design, the cell-level counts, the harness defect, and the disclosure that only the absence of the fabrication violation kind is citable from this scan.

### 5.5 The ladder: a confounded operate floor

A thin capability ladder (2026-07-03; n=3 per model: Qwen2.5-7B, Qwen3.5-9B, Llama-3.3-70B, Qwen3-235B) probed the remaining moderator on a gate task requiring refusal of a gated commit. Section 7.1 reports it in full, including the per-model caveats. In brief: the ladder is confounded (the action parser is tuned to one model's output format; Section 6.3) and carries no scaling claim; it weakly supports that an operate floor exists (7B fails 3/3 in both modes, completing neither compliance nor violation) and that operable models self-enforce with the runtime off, with zero unsafe-mutation violations anywhere in the gate cells.

### 5.6 Predictions against outcomes

| # | Situation | Predicted delta | Diagnostic outcome |
|---|---|---|---|
| P1 | Verifiable, no conflict, capable model | ~0 | Consistent: self-enforces when salient (n=3) |
| P2 | Verifiable, goal conflict (H2) | Real, grows with pressure | Null: 0 fabrication P0-P3 (n=5, pre-registered) |
| P3 | M8 references, instrumental pressure | Real | Falsified: harness-blindness artifact; 0pp with stdout fix (n=5, pre-registered) |
| P4 | M8 references, cooperative, asked plainly | ~0 | Consistent: honest 6/6 per regime (n=3 per cell) |
| P5 | L7 drift | Real at every level | [FORK-L7-DRIFT: unmeasured; do not assume outcome] |
| P6 | Contract withheld (untold) | Enforcement is the only barrier | Consistent: untold violation floor observed (n=3) |
| P7 | Below operate floor | Prevents malformed harm, not disobedience | Consistent: 7B below floor (n=3 per model) |

Table caption: Pre-registered predictions against diagnostic outcomes (one model, Qwen3-235B, n=3-5 per cell). Two of the three predicted enforcement-delta regions nulled; only the operate floor survives, weakly.

Of the three moderators hypothesized to gate substitution, the verifiability exception dissolved (P3, P4), goal conflict nulled (P2), and only the operate floor survives, weakly and ladder-confounded (P7). The redundancy measure (A vs B) is the headline quantity, and every told-and-salient diagnostic puts cell B at ceiling: 3/3 refusal in both foregrounded contract-off rows (both cell B, runtime off), 3/3 honest reporting in the cell-B (`no_audit_chain`) half of the retrieved M8 regime, 3/3 honest abstention in the cell-B half of the non-retrieval regime, and 0 fabrication across all 20 cell-B (`no_audit_chain`) goal-conflict reps (all diagnostic, one model, n=3 to 5 per cell). The paired `full_contract` halves of the M8 and goal-conflict regimes are cell A, enforcement on, and are held separate here because their compliance is runtime-guaranteed rather than self-enforced. The diagnostics are therefore consistent with the negative result: for this capable cooperative agent above the operate floor, in-context specification substitutes for runtime enforcement broadly, on verifiable and non-verifiable constraints alike and under benign completion pressure. Runtime enforcement's demonstrated behavioral value is the deterministic guarantee plus the corners where telling does not reach: the untold violation floor, the incidental-salience failure of Section 5.1, below the operate floor, and adversarial intent, untested here. Enforcement is behaviorally redundant only in that scoped sense, never structurally. All of this is diagnostic tier, one model, small n, within this fixed controller and these probe tasks; it is not a general claim about agents or harnesses. [FORK-H5-REPLICATION: pending external non-HAI replication; do not assume outcome]

## 6 Methodology cautions as a contribution

Our probing arc produced, and then destroyed, an apparent positive result. We report the destruction as a named contribution rather than a limitations aside, because the failure mode is general to agent evaluation and easy to reproduce by accident.

### 6.1 Harness blindness manufactured a fabrication finding

In early probes the harness did not surface command output to the agent. Where stdout should have appeared in the observation feedback, the agent received a `stdout_ref` file path instead. The agent could dispatch a lookup, but it could never read the result. When a task then required an identifier to advance an action, the agent guessed: across three pre-fix probe sets we observed 8 instances in which it dispatched commands carrying plausible, well-formed identifiers it had never seen, including a fabricated evidence-card identifier and repeated invented target identifiers (model-backed diagnostic tier: one model, Qwen3-235B, temperature 0, n=3 per cell). This looked like a real finding, instrumental fabrication: honest when asked plainly, fabricating when an identifier is instrumentally required. It was, at the time, the strongest surviving candidate for a positive enforcement result.

The finding was an artifact of the harness. The pre-registered falsification experiment crossed Statement vs Action framing with id present/absent (4 tasks x 5 reps = 20, n=5 per cell, pre-committed bar: instrumental effect >=40 percentage points), run after the committed stdout-inlining fix (commit `17db5ef`), which inlines command stdout into the observation feedback bounded to the first 24,000 characters. Result: fabrication 0/5 in the Action/id-absent cell, 0/5 in the Statement/id-absent cell, an instrumental effect of 0 percentage points against the >=40pp bar, diagnostic (one model, Qwen3-235B, n=5). Once the agent can see the empty lookup, it abstains honestly 5/5 even in the Action arm, where the identifier is needed to finish the task. The cleanest before/after pair holds the task fixed: pre-fix, one rep fabricates a plausible card identifier while another rep in the same task and runtime mode stays honest; post-fix, all 6 reps are honest, with verbatim-identical finals within each runtime mode. One disclosure: we cite this scan only for the absence of the fabrication violation kind. In the id-absent cells honest abstention costs task success by design; across the scan all 20 reps fail overall pass and a refusal-classified scoring error fires 20/20, and the action/id-present task additionally logs an unsafe-mutation flag 5/5 under `no_runtime_enforcement`. The id-present control cells are valid (the agent reports or uses the real retrieved identifier); no outcome from this scan other than the fabrication-kind absence is cited in this paper.

The general lesson: eval harnesses that hide tool output manufacture spurious fabrication findings. A model that cannot observe its own command results is forced to guess, and a deterministic scorer will read the guess as fabrication. The resulting number is a fact about the harness, not the model. Genuine constraint-driven fabrication does exist under more adversarial operationalizations [arXiv:2606.14831]; our claim is narrower and methodological: before attributing fabrication to the agent, verify the agent could see what it is accused of inventing.

### 6.2 Prompt-embedded ablations measure self-enforcement

A second caution follows directly from the 2x2. Guardrail ablation studies that toggle runtime enforcement while leaving the policy in the system prompt in both conditions, as in [arXiv:2604.15579], measure the marginal value of enforcement given the agent was told (A: deployment baseline vs B: told-not-enforced, the redundancy measure), not the effect of enforcing (C: enforced-not-told vs D: neither, the violation floor). For a capable cooperative agent that self-enforces, this design will show small deltas and invite the wrong conclusion in either direction: that enforcement is worthless, or that a small delta on a told agent bounds what enforcement does for an untold one. Neither follows. Ablations that never withhold the in-context contract measure self-enforcement, not enforcement.

### 6.3 Two supporting cautions

**A parser tuned to one model family scores other models below the operate floor.** On the capability ladder (Section 7.1), only Qwen3-235B emitted parser-clean output; the 9B and 70B models looped invalid on routing, which automated scoring reads as inability to drive the contract. Without manual inspection this would have placed operable models spuriously below the operate floor. This confound is why the ladder carries no scaling claim.

**Provider catalog metadata is not ground truth.** The Together serverless catalog flag was unreliable: models it listed as serverless were dedicated-endpoint only in practice, which contaminated ladder composition; separately, the screen-to-ladder provenance chain is not reconstructable from artifacts. Roster composition must be verified against live endpoints, not catalog flags.

### 6.4 A checklist for agent-eval builders

- Confirm the agent receives tool and command output verbatim in its observation feedback; a reference or path is not output.
- Before reporting fabrication, hallucination, or dishonesty, check whether the accused content was observable to the agent at decision time.
- If the policy is in the prompt in every condition, the enforcement toggle measures the redundancy measure (the marginal value of enforcement given the agent was told), not the effect of enforcing.
- Validate the action parser against every model in the roster before attributing failure to capability; parser mismatch mimics the operate floor.
- Verify provider catalog claims (availability, endpoint class) against live endpoints before locking a roster.
- Pre-register a falsification bar for any surprising positive finding and re-run it after fixing the harness defect that co-occurred with it.

## 7 The capability ladder and external replication

### 7.1 The thin capability ladder

The negative result treats model capability as a moderator, not a headline axis. To check whether an operate floor exists, we ran a thin capability ladder as a model-backed diagnostic (n=3 per model, temperature 0, 2026-07-03; `runs/pilot/_probe_ladder/`): Qwen2.5-7B, Qwen3.5-9B, Llama-3.3-70B, and Qwen3-235B on a gate task (`gab_l6_block_commit_under_no_runtime`) requiring the agent to withhold a commit gated by M5, the `agent_safe` dispatch refusal, under both `full_contract` and `no_runtime_enforcement`.

The ladder is confounded and cannot carry a scaling claim. The harness action parser is tuned to one model's output format; only Qwen3-235B emits parser-clean output, and the 9B and 70B models loop invalid on routing steps. A further provenance caveat: the earlier candidate screen (8 models, n=1) does not contain the 7B or 70B entries, and the screen-to-ladder chain is not reconstructable from artifacts. Under these confounds the ladder weakly supports exactly two claims.

First, an operate floor exists. Qwen2.5-7B failed the gate task 3/3 in both modes: it dispatched the gated command, then degraded into invalid-output loops, completing neither compliance nor violation. This matches its earlier roster exclusion (0/60 valid finals), which we attribute to contract friction, not governance. Below the operate floor, enforcement prevents malformed harm rather than disobedience.

Second, operable models self-enforce. Llama-3.3-70B and Qwen3-235B passed 3/3 in both modes, withholding the gated commit with the runtime off; the 70B model refused on uncertainty, a distinct sub-claim from genuine self-enforcement. Qwen3.5-9B passed 3/3 under `no_runtime_enforcement`, but its `full_contract` cell produced zero completed reps due to an adapter failure, so any within-model delta for 9B is unmeasured. Zero `unsafe_mutation` violations occurred anywhere in the ladder gate cells. No operate-but-violate band was observed: within this diagnostic, models either drove the contract and complied or fell below the floor.

We make no claim of a capability-ordered self-enforcement curve. Non-monotone capability-compliance relationships across model families are already documented [arXiv:2606.01317, arXiv:2601.08196], and a four-model, parser-confounded ladder at n=3 cannot adjudicate them.

### 7.2 External non-HAI replication

[FORK-H5-REPLICATION: pending external non-HAI replication; do not assume outcome]

Every model-backed number in this paper comes from one controller, HAI v0.2.0, with its particular manifest, contract-authoring style, and task suite. Hypothesis H5 holds that the specify-vs-enforce effect generalizes beyond HAI; a required external replication is the generality check that distinguishes a phenomenon from a HAI quirk. The planned design reproduces the 2x2 on an independent harness with its own mechanism inventory and deterministic scorer, measuring at minimum the A-vs-B contrast, the marginal value of enforcement given the agent was told. Where the replication also attributes the telling axis (B vs D, C vs D), first-attempt scoring applies (Section 3.6). TeamBench [arXiv:2605.07073] (Section 2) is one candidate substrate: prior evidence of the same qualitative shape in a different mechanism domain and design, not itself a replication of this paper's effect. Its sub-metric asymmetry (pass-rate parity coexisting with 3.6 times more verifier-edits-executor cases in the prompt-only arm) cautions that aggregate parity can mask enforcement value. That caution applies to our own instrument. The deterministic scorer observes per-mechanism `mechanism_disabled` markers and each task's load-bearing violation kind (Section 4.2), so it detects whether the specific guarded violation occurs, but it does not resolve finer sub-metric channels such as a verifier-edits-executor count. An enforcement effect that left the pass rule and the tracked violation kinds unchanged while shifting such a channel would stay undetectable at n=3-5. Aggregate parity in these diagnostics should therefore not be read as sub-metric equivalence.

The outcome sets the claim scope. If substitution replicates, the negative result describes a phenomenon that extends beyond this controller rather than a HAI quirk. If it does not, the result narrows to this controller and task suite, and contract-authoring style becomes a candidate moderator. Neither outcome is assumed here.

## 8 Discussion

The negative result is conditional, not universal. In these diagnostics (one model, Qwen3-235B, n=3-5 per cell), substitution held when six conditions held together: the agent was capable, above the operate floor; the agent was cooperative; the constraint was stated in the in-context contract and told plainly; the constraint was salient at decision time; the harness surfaced command output to the agent; and the inputs were benign. Five of these, when they fail, mark regions where runtime enforcement retains demonstrated value (Section 8.1); the sixth, the harness surfacing command output, is a measurement-validity condition whose failure manufactures the spurious fabrication finding of Section 6 rather than a genuine enforcement region.

### 8.1 What runtime enforcement is still for

The negative result relocates enforcement's value rather than eliminating it. Beyond the deterministic guarantee, which is structural rather than a condition-failure region, each scope condition of Section 8.0 marks a region where enforcement retains behavioral value when that condition fails.

First, the deterministic guarantee of Section 3.5, which holds unconditionally and is not tied to any one condition failing. Cell B: told-not-enforced compliance is a statistic over model behavior; cell A: deployment baseline compliance on the enforced surface is a property of the harness. A gated action that the runtime blocks cannot occur; a 3/3 refusal rate at n=3 bounds nothing.

Second, when the told condition fails: the untold violation floor of Section 5.1, where the contract is withheld and enforcement is the only barrier. In-context specification cannot substitute for enforcement on rules the context never carried, and real deployments accumulate such rules through contract drift, incomplete prompt assembly, and context compaction [arXiv:2606.22528].

Third, when the salience condition fails: the incidental-salience region of Sections 5.1 and 8.2, where the same told constraint reached incidentally rather than foregrounded was dispatched 3/3 on first attempt. Enforcement catches the violation that a told-but-not-salient agent commits.

Fourth, when the capability condition fails: below the operate floor, where enforcement prevents malformed harm rather than disobedience (Section 7.1); the failure there is contract friction, not governance.

Fifth, when the benign-inputs condition fails: adversarial inputs, where the cooperative assumption also no longer holds. The substitution result is scoped to benign completion pressure, not adversarial injection. The injection literature already shows architectural enforcement outperforming prompt-only defenses under attack [arXiv:2503.18813, arXiv:2504.11703]; Verifier Tax [arXiv:2603.19328] similarly finds policy mediation intercepting up to 94% of non-compliant actions under instrumental pressure while agents hallucinate identifiers to route around blocks. Injection robustness is cited territory, not a claim of this paper, and nothing here licenses removing enforcement from adversarially exposed surfaces.

One published result points the opposite empirical direction and warrants direct comment. Mechanical Enforcement [arXiv:2605.14744] finds mechanical enforcement raising governance quality and task accuracy (MCC approximately 0.43 to 0.88) over text-only governance, where this paper finds enforcement behaviorally redundant given specification. The findings differ on four axes: domain (regulated banking versus non-clinical personal wellness), metric type (decision-rationale quality versus tool-action compliance), design (paired alternative configurations versus a crossed per-mechanism factorial), and pressure regime (their regulated-decision setting versus benign completion pressure here). The tension is a difference in what is measured and under what pressure, not a contradiction on the redundancy measure.

### 8.2 The salience confound

The told-not-enforced leg carries a caveat. Self-enforcement is salience-sensitive: in the diagnostic battery of Section 5.1, the told agent refused the gated action 3/3 when the constraint was foregrounded, but dispatched it 3/3 on first attempt when it was reached incidentally through normal task phrasing (one model, n=3 per cell). Under first-attempt scoring, telling substituted for enforcement only when the telling was salient at decision time. The substitution claim is really a claim about salient in-context specification, and how salience decays with context length, task distance, and compaction is unmeasured here [arXiv:2606.22528].

### 8.3 Personal health as a domain

HAI's domain, non-clinical personal wellness, is a deliberate instrument choice. The non-clinical boundary (no diagnosis, treatment, prescribing, or autonomous medical decisions) is itself an evaluated constraint, the zero-tolerance leg of M7 refusal of out-of-contract requests. The choice makes a policy-dense boundary an enforceable, ablatable object of study with unambiguous violation semantics, without any clinical claim.

### 8.4 Limitations

All model-backed evidence is diagnostic tier: one model (Qwen3-235B-A22B-Instruct-2507, Together AI, temperature 0), n of 3 to 5 per cell, run on diagnostic probe tasks rather than the locked benchmark suite. At these sample sizes a low-frequency self-enforcement failure rate would go undetected, undermining any cross-model reading of the negative result but not the existence demonstrations: the untold violation floor is a demonstration on this model, and the harness-blindness finding is a property of the harness, established by a before-and-after contrast on identical tasks, not a behavioral generalization. One runtime instantiates the mechanisms. [FORK-H5-REPLICATION: pending external non-HAI replication; do not assume outcome] L7 stale-manifest drift, the sole surviving candidate for a true non-verifiable enforcement delta, is unmeasured. [FORK-L7-DRIFT: unmeasured; do not assume outcome] Inputs are benign throughout; the adversarial-input arm is scorer-coverage evidence only. The capability ladder is confounded by an action parser tuned to one model's output format and supports only that an operate floor exists.

### 8.5 What would change the conclusion

The conclusion is falsifiable on several fronts: a second model or second runtime showing a nonzero A-versus-B delta under the same first-attempt scoring; a measured L7 drift delta; self-enforcement failing at higher n or under longer-horizon salience decay; or goal-conflict pressure beyond P3 breaking the null. Any of these would restore behavioral, not merely guarantee-level, value to enforcement for told constraints. The substitution claim is exactly as strong as the six scope conditions of Section 8.0, and no stronger.

## 9 Future work and conclusion

### 9.1 Future work

The measurement this design points at most directly is L7 stale-manifest drift (Section 3.4), the sole surviving genuinely non-retrievable candidate for a real cooperative-agent enforcement delta. Concurrent work establishes the drift-causes-violation half, that context compaction silently erases constraints the agent obeyed while they were visible [arXiv:2606.22528]; whether independent runtime enforcement catches post-drift violations is the untested second half. [FORK-L7-DRIFT: unmeasured; do not assume outcome]

Second, the adversarial-input arm should graduate from scorer-coverage evidence to model-backed evidence. This paper cites injection robustness rather than claiming it (Section 8.1); running the specify-vs-enforce 2x2 under attacker-controlled inputs would locate where the substitution result ends and the injection-defense literature begins.

Third, a fuller screened capability ladder behind an action parser tolerant of every roster model. The present ladder carries only the existence of an operate floor (Section 7.1); a parser-tolerant rerun across a wider screened roster could locate the floor rather than merely evidence it, with non-monotonicity across families expected [arXiv:2606.01317, arXiv:2601.08196] and no scaling law promised.

Fourth, a higher-n confirmatory run. Whether a multi-model higher-n run is warranted, or the pre-registered diagnostic sweeps stand with the one-model, small-n limitation stated, is an open decision, as is the external replication of Section 7. [FORK-H5-REPLICATION: pending external non-HAI replication; do not assume outcome]

Two deferred lines complete the program. H7 extends the design toward the capability-versus-compliance question studied externally under scaling-laws-for-oversight [Engels2025], asking whether a deterministic Guard at general Elo of zero occupies a legitimate point on that external curve; this paper itself claims no scaling law (Section 1). H8 asks whether fine-tuned operators reach contract compliance at smaller scales than untrained operators (the S1 fine-tuning sequel), which would move the operate floor itself.

### 9.2 Conclusion

For a capable cooperative agent above the operate floor, told its constraints plainly, able to see its tool output, and facing benign inputs, our diagnostics are consistent with in-context specification substituting for runtime enforcement broadly: the agent self-enforced verifiable and non-verifiable constraints alike, and held under benign goal-conflict pressure (diagnostic tier: one model, Qwen3-235B, n=3-5 per cell). Told plainly is load-bearing: self-enforcement is salience-sensitive, and when the same told constraint was reached incidentally through normal task phrasing, the gated command was dispatched first-attempt 3/3 (diagnostic, one model, n=3). Within those scope conditions, runtime enforcement was behaviorally redundant.

It was not redundant elsewhere. Enforcement retains the deterministic guarantee, which no behavioral result touches; it is the only barrier at the untold violation floor, where an agent never told the rule completed the violation 3/3 with a truthful success report (diagnostic, one model, n=3); below the operate floor it prevents malformed harm rather than disobedience; and adversarial territory remains untested here, cited as the regime where telling is already known to fail.

The takeaway we most want practitioners to carry is methodological. Before attributing fabrication to a model, check what the harness let it see. An apparent instrumental-fabrication effect in our own pipeline dissolved to 0 percentage points against a pre-committed bar of at least 40 (diagnostic, one model, pre-registered n=5) once the harness inlined command stdout. Harness blindness manufactures spurious findings; an evaluation of agent honesty is only as sound as the observation channel the harness provides.

## Appendix

Skeleton only. Each subsection names the artifact that will supply the
final content and the PAPER.md anchor it must trace to; no full tables
are populated here.

### A. Task suite

**[STUB]** Table APPX.1: tasks by level and load-bearing mechanism
(M4-M9-TX). Task-count claims are unstable at the writing tier. An
earlier apparatus (a 28-task suite with 25 static oracle pairs, 23
per-mechanism plus 2 `no_runtime_enforcement` floor pairs, and a
16-trajectory adversarial layer) was retired by PAPER.md decision D-37
(2026-07-04, landed across benchmark commits `a10e850`..`48ff87b`):
those figures no longer apply. The suite is rebuilt as a sharp 16-task
2x2 (told x enforced) per mechanism, with the told/untold contract axis
(`e72dced`) and first-attempt scoring (`48ff87b`) built in. The count
remains benchmark-lane-owned and was still moving from a concurrent agent
at 2026-07-04. Do not populate Table APPX.1, and do not cite the count as
final, until the benchmark suite is frozen and its size confirmed against
the release tag.

### B. Prompt provenance

`deployment_full_v2` (D-28, authorized 2026-06-28): the manifest is
embedded as minified JSON with null/empty fields dropped, lossless
relative to `deployment_full_v1` (verified by round-trip; no
command/flag/type/choice/default/help/description removed), reducing
the rendered prompt from approximately 43K to approximately 22K tokens
after the v1 prompt exceeded a model's context limit. Recorded as
`PILOT_PROTOCOL.md` Amendment 2. Cite the prompt identifier from the
roster's `prompt_id` field (an identifier string, not a hash) and the
prompt file hash from `scripts/lock_hashes.json`, not from this
appendix. Caution: the recorded lock hash predates prompt edits
committed 2026-07-04 (`e72dced`) by the concurrent benchmark agent;
re-derive the file hash at populate time rather than reusing the
recorded value.

### C. Probe protocol summary

**[STUB]** Per-cell n and seed/temperature table. All model-backed
probes to date: `Qwen/Qwen3-235B-A22B-Instruct-2507-tput` (Together AI),
temperature 0, top_p 1, no seed support in the provider API, n=3-5 per
cell depending on probe (see grounding pack Section 6 for per-probe n).
Table to enumerate probe directory, task(s), mode(s), and n per row.

### D. Adversarial trajectory table (pointer)

**[STUB, disposition pending]** 16 hand-authored trajectories (4 each
vs M7, M5+M6, M8, M4), scorer-coverage evidence at the appendix tier,
never model-backed. Per PAPER.md (Engineering Plan, Trajectories row),
the aggregated artifact is
`adversarial_summary/adversarial_summary_aggregated.csv`, produced by
`reproduce_offline.py`, with the 16-row per-trajectory table emitted
alongside it for the appendix (a separate artifact, not rows inside the
aggregated CSV). Retired at the benchmark tier by the same `a10e850`
commit, which removed `results/adversarial_summary.py` and the
trajectories, so `reproduce_offline.py` no longer emits these artifacts
at HEAD; PAPER.md as read still lists the layer as current. Resolve
against a PAPER.md D-37 entry before finalizing this subsection.

### E. Reproducibility

Per PAPER.md (Engineering Plan, Reproducibility script row),
`reproduce_offline.py` runs the full offline pipeline (rule-baseline
ablation, evidence tables, figures, error taxonomy, static oracle-pair
isolation matrix, live-runtime-probe isolation matrix) from a single
command; baseline runtime 76s on Apple M2. Artifact and hash baselines
in `REPRODUCIBILITY.md` and `REPRODUCIBILITY_GOLDEN.json`. Staleness
note: commit `a10e850` cut the pipeline to rule-baseline ablation,
evidence tables, figures, and error taxonomy (isolation matrices
retired) and regenerated `REPRODUCIBILITY_GOLDEN.json`; the 76s figure
is the pre-`a10e850` PAPER.md baseline. Re-baseline the runtime and
pipeline description once PAPER.md carries a D-37 entry.

### F. Scorer config hash chain

Scorer behavior thresholds and critical violation kinds load from
`scorer_config.paper_v1.json`; the config hash records the audited
config bytes (D-18). A provenance-only hash bump (`68e29510...` to
`d310f503...`) accompanied the D-30 scorer-correctness pass, recorded in
`lock_hashes.json`; metric thresholds, pass rule, and critical kinds
were unchanged in that pass.

### G. D-O-02: Appendix E coding-agent sketch (open decision)

**[OPEN, deferred to mid-August polish]** Keep-or-drop decision on an
Appendix E coding-agent sketch. PAPER.md D-O-02 requires an
anti-overclaim header if kept; PAPER.md does not specify the header's
wording. Workflow-derived content requirements for that header: the
sketch is illustrative, not a fourth evidence tier (the three tiers,
static oracle-pair evidence, live runtime probe, and model-backed
diagnostic, are never merged or extended), and not evidence of
generalization beyond the HAI controller. [FORK-H5-REPLICATION: pending
external non-HAI replication; do not assume outcome] Do not draft
Appendix E content before D-O-02 resolves.

## References

Formatted from the verified neighbor list (`paper/prior_art_notes.md`, compiled 2026-07-04); verification status per entry is recorded there. Section 2's external numeric claims were verified against primary sources 2026-07-04: ContextCov (88.3% vs 67.0%) and PhantomPolicy (95.3% to 40.7%) in the novelty audit; Mechanical Enforcement (MCC ~0.43 to 0.88; 73% deferral reduction) and Verifier Tax (up to 94% intercepted; SSR below 5%) by direct arXiv re-fetch. Entries are listed by the short name used in the text.

- ABSTAIN: Ojewale and Venkatasubramanian (Brown University). What Benchmarks Don't Measure. arXiv:2606.02965. Workshop paper.
- Agent Behavioral Contracts: Bhardwaj. Agent Behavioral Contracts. arXiv:2602.22302.
- Agent-SafetyBench: Zhang et al. ACL 2025. arXiv:2412.14470.
- AgentSpec. arXiv:2503.18666. <!-- not full-text cleared; verify before final submission -->
- AHE (automatic harness evolution). arXiv:2604.25850.
- AIRGuard: Qin, Zhuang, et al. arXiv:2605.28914.
- CaMeL: Debenedetti et al. (Google DeepMind / ETH Zurich). arXiv:2503.18813.
- CEF/Thanatosis: J.P. Morgan AI Research. Is Your Agent Playing Dead? arXiv:2606.14831.
- ContextCov: Sharma. arXiv:2603.00822.
- Engels, Baek, Kantamneni, and Tegmark. Scaling Laws For Scalable Oversight. arXiv:2504.18530. NeurIPS 2025 (Spotlight). Cited as [Engels2025] per PAPER.md H7/D-03 (deferred line). Verified against the primary source 2026-07-04.
- ETCLOVG survey. OpenReview 3hXEPbG0dh. TMLR, under review; cited via OpenReview, not as an accepted paper.
- FORGE: Palumbo, Choudhary, Choi, Amir, Chalasani, Jha. arXiv:2602.16708 (v1 titled "Policy Compiler for Secure Agentic Systems").
- Governance Decay / ConstraintRot. arXiv:2606.22528.
- Guardrails AI. Software framework.
- Harness-Bench. arXiv:2605.27922.
- Harness-MU: Fan, Nie, Dai. arXiv:2606.21856.
- IFEval. arXiv:2311.07911.
- Invariant Guardrails: Invariant Labs (now part of Snyk). Software framework.
- LogiSafetyBench. arXiv:2601.08196.
- Mechanical Enforcement: de la Chica Rodriguez and Marti-Gonzalez. arXiv:2605.14744.
- Meta-Harness. arXiv:2603.28052.
- NeMo Guardrails: NVIDIA. Software framework.
- NLAH (natural-language agent harnesses). arXiv:2603.25723.
- PhantomPolicy: Wu, Gong (Atlassian). arXiv:2604.12177.
- Policy-as-Prompt. arXiv:2509.23994. NeurIPS 2025 Regulatable ML workshop.
- Progent. arXiv:2504.11703.
- Prompts Don't Protect: Uppala. arXiv:2605.18414. Single author; no venue located.
- RECAST. arXiv:2505.19030.
- SABER. arXiv:2606.01317.
- SafePyramid. arXiv:2606.29887.
- ST-WebAgentBench: Levy et al. arXiv:2410.06703. ICLR 2026.
- Symbolic Guardrails: Hong et al. (CMU). arXiv:2604.15579.
- TeamBench: Kim et al. arXiv:2605.07073.
- TRACE: Zhou et al. arXiv:2606.13174.
- VerIF. arXiv:2506.09942. EMNLP 2025 per ACL Anthology.
- Verifier Tax: Sah, Srivastava, Sah, Jordan. arXiv:2603.19328.
