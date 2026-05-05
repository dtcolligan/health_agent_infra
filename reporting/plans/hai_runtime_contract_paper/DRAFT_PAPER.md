# Testing Whether the HAI Runtime Contract Reduces Model Scale for Personal-Health Agents

**Subtitle:** HACO-Bench and a Governed Local Runtime for Contract-Obedient Health Agent Operation

**Status:** Draft skeleton, 2026-05-05.

## Abstract

Personal-health agents must reason over sensitive longitudinal data while avoiding unsafe actions, unsupported claims, opaque state mutation, and clinical overreach. Most current approaches rely on larger frontier models, tool-use scaffolds, or domain-specific fine-tuning to improve reliability. This paper studies a complementary hypothesis: an enforceable runtime contract can shift reliability burden from the model into software.

We introduce **HAI**, a local plugin/runtime wrapper around a shell-capable personal-health agent. HAI exposes and enforces a runtime contract: a capabilities manifest, command schemas, mutation classes, `agent_safe` boundaries, exit-code semantics, output schemas, proposal/commit separation, validation gates, deterministic policy, and audit logs. We also introduce **HACO-Bench**, a benchmark for Health Agent Contract Operation, measuring whether models can operate HAI safely and correctly.

We evaluate local models from 1B to 7B parameters, prompt-only cloud models, manifest-grounded systems, fine-tuned local operators, and rule-based baselines. Across scaffold ablations, we test whether the full HAI runtime contract lowers the minimum parameter count required to reach target HACO-Bench performance while keeping unsafe-action, clinical-claim, unsupported-narration, and direct-state-mutation rates below fixed thresholds.

Result placeholder: [RESULTS TO BE FILLED AFTER EXPERIMENTS].

## 1. Introduction

### 1.1 Motivation

Wearables and user intake create rich personal-health context, but personal-health agents operate in a risky setting. Health data is sensitive, recommendations can influence behavior, and fluent explanations can hide unsupported claims. A model that is useful in conversation may still be unsafe if it owns memory, state mutation, validation, policy, and explanation at once.

HAI explores a different allocation. The model remains the conversational operator. The runtime owns truth, validation, mutation, policy, and audit.

### 1.2 Central Hypothesis

An enforceable runtime contract can reduce the model scale required for safe and effective personal-health agent operation.

Here, **model scale** means the minimum model parameter count needed to reach a target HACO-Bench score under fixed safety thresholds.

### 1.3 Research Question

Given a personal-health runtime with explicit contracts, how small can the operating model be while remaining safe, faithful, and task-effective?

### 1.4 Contributions

1. **The HAI runtime contract:** a local governed runtime surface for personal-health agent operation.
2. **HACO-Bench:** a benchmark for contract-obedient health agent operation.
3. **A model-scale study:** comparison of local small models, cloud models, rule baselines, manifest-grounded systems, and fine-tuned adapters.
4. **Scaffold ablations:** experiments isolating the effect of manifest fields, schemas, mutation classes, safety flags, exit codes, proposal gates, and audit evidence.
5. **Health-agent safety metrics:** unsafe mutation attempts, clinical-claim rate, direct-state-write attempts, unsupported narration, refusal accuracy, and drift robustness.

## 2. Related Work

### 2.1 Personal Health Agents

Discuss PHIA, Google Personal Health Agent, PH-LLM, and Health-LLM.

Positioning: prior work shows that LLM agents can reason over wearable health data. This work instead studies whether a governed local runtime can reduce the model capability required to operate bounded personal-health workflows safely.

Key sources:

- PHIA: https://www.nature.com/articles/s41467-025-67922-y
- Google Personal Health Agent: https://research.google/pubs/the-anatomy-of-a-personal-health-agent/
- PH-LLM: https://arxiv.org/pdf/2406.06474
- Health-LLM: https://proceedings.mlr.press/v248/kim24b.html

### 2.2 Tool-Using and Function-Calling Agents

Discuss API-Bank, ToolLLM, Gorilla, BFCL, tau-bench, and MCP-AgentBench.

Positioning: existing benchmarks measure API/tool competence. HACO-Bench focuses on health-specific contract obedience: safety flags, mutation classes, proposal gates, auditability, clinical-boundary refusal, and evidence-faithful narration.

Key sources:

- API-Bank: https://arxiv.gg/abs/2304.08244
- ToolLLM: https://arxiv.org/abs/2307.16789
- Gorilla: https://arxiv.org/abs/2305.15334
- BFCL: https://www2.eecs.berkeley.edu/Pubs/TechRpts/2025/EECS-2025-184.html
- tau-bench: https://arxiv.gg/abs/2406.12045
- MCP-AgentBench: https://huggingface.co/papers/2509.09734

### 2.3 Runtime Enforcement and Agent Safety

Discuss AgentSpec and runtime-enforcement approaches for LLM agents.

Positioning: HAI uses runtime enforcement not only as a guardrail, but as the experimental intervention whose effect on model-scale requirements is measured.

Key source:

- AgentSpec: https://ink.library.smu.edu.sg/sis_research/10278

### 2.4 Medical and Health-Agent Benchmarks

Discuss MedAgentBench, AgentClinic, OpenMedCalc, and MedHallu.

Positioning: HAI is not a clinical EHR or diagnostic agent. It targets bounded local personal-health operation over wearable and intake data, with explicit non-goals around diagnosis and treatment.

Key sources:

- MedAgentBench: https://stanfordmlgroup.github.io/projects/medagentbench/
- AgentClinic: https://www.nature.com/articles/s41746-026-02674-7
- OpenMedCalc: https://www.nature.com/articles/s41746-025-01475-8
- MedHallu: https://aclanthology.org/2025.emnlp-main.143/

### 2.5 Factuality and Structured Outputs

Discuss FActScore, MedHallu, JSONSchemaBench, and constrained decoding.

Positioning: HACO-Bench combines structured command validity with evidence-faithful narration and abstention/refusal metrics.

Key sources:

- FActScore: https://arxiv.gg/abs/2305.14251
- JSONSchemaBench: https://huggingface.co/papers/2501.10868

## 3. HAI: A Governed Local Runtime for Personal-Health Agents

### 3.1 System Definition

HAI is the local plugin/runtime wrapper around a shell-capable personal-health agent. The agent converses and routes. HAI owns truth.

### 3.2 Runtime Contract

The HAI runtime contract includes:

- `hai capabilities --json`
- command schemas
- mutation classes
- `agent_safe` flags
- idempotency metadata
- stable exit-code semantics
- JSON-output and output-schema declarations
- proposal/commit separation
- deterministic classifiers and policy rules
- X-rule synthesis
- local SQLite state
- audit logs
- read-only explanation surfaces such as `hai today` and `hai explain`

### 3.3 Authority Boundary

| Component | Model owns | HAI owns |
|---|---:|---:|
| Conversation | yes | no |
| Intent routing | yes | contract-constrained |
| Health data truth | no | yes |
| State mutation | no | yes |
| Policy rules | no | yes |
| Clinical boundary | must obey | enforced |
| Audit trail | no | yes |
| User-facing narration | yes | evidence-bounded |

### 3.4 Safety Scope

HAI explicitly does not diagnose, treat, prescribe, or make autonomous clinical decisions. It does not allow direct SQLite mutation by the agent. Commit/archive actions that change user-governed intent or targets are user-gated.

## 4. HACO-Bench: Health Agent Contract Operation Benchmark

### 4.1 Benchmark Goal

HACO-Bench measures whether a model can operate HAI through the runtime contract rather than relying on implicit repo knowledge or free-form guessing.

### 4.2 Task Levels

| Level | Task |
|---|---|
| L1 | Intent-to-command routing |
| L2 | Setup and `USER_INPUT` recovery |
| L3 | Daily-loop orchestration |
| L4 | Schema-valid proposal generation |
| L5 | Faithful narration from `hai today` and `hai explain` |
| L6 | Governance preservation and adversarial refusal |
| L7 | Contract drift adaptation |

### 4.3 Dataset Construction

Use synthetic and redacted fixtures only. Split by task template, persona, manifest version, and drift condition. Training data must not include private health rows.

### 4.4 Metrics

Primary metrics:

- task success
- valid command rate
- correct command rate
- unsafe-action rate
- refusal accuracy
- clinical-claim rate
- direct-state-mutation attempt rate
- unsupported narration rate
- exit-code recovery accuracy
- schema validity
- drift robustness

Secondary metrics:

- latency
- cost
- local memory footprint
- tokens used
- retry count

### 4.5 Target Score

A model reaches **HACO-X** if it achieves at least X aggregate task score while keeping all safety violation rates below fixed thresholds.

Example:

```text
HACO-80:
  task_success >= 80%
  unsafe_action_rate <= 1%
  clinical_claim_rate <= 1%
  unsupported_narration_rate <= 3%
  direct_state_write_attempt_rate = 0%
```

## 5. Experimental Setup

### 5.1 Models

Local:

- 1B-1.5B proof model
- 3B main model
- 7B stretch model

Cloud:

- prompt-only cloud
- cloud plus HAI manifest
- cloud plus HAI manifest plus runtime validation

Baselines:

- rule-based router
- rule-based refusal classifier
- simple manifest lookup baseline

### 5.2 Conditions

| Condition | Description |
|---|---|
| No contract | Model prompted with general task only |
| Static docs | Model receives human docs |
| Manifest only | Model receives live `hai capabilities --json` |
| Manifest plus schemas | Adds schema/output constraints |
| Full HAI contract | Full runtime contract and validation |
| Fine-tuned | Local model trained on contract-operation trajectories |
| Fine-tuned plus manifest | Behavioral adapter plus live contract |

### 5.3 Scaffold Ablations

Remove one component at a time:

- no `agent_safe`
- no mutation classes
- no exit-code semantics
- no output schemas
- no proposal gate
- no audit/evidence references
- no manifest
- stale manifest

### 5.4 Training Data

Generate training data from public manifests, synthetic user intents, fixture-based runtime states, command trajectories, error-recovery examples, and adversarial refusals.

No private health rows are used for training.

## 6. Results

### 6.1 Main Result: Model Scale vs HACO Score

| System | Params | HACO score | Safety pass? | Cost | Local? |
|---|---:|---:|---:|---:|---:|
| Rule baseline | 0 | TBD | TBD | low | yes |
| Local prompt-only | 3B | TBD | TBD | low | yes |
| Local plus manifest | 3B | TBD | TBD | low | yes |
| Fine-tuned local | 3B | TBD | TBD | low | yes |
| Fine-tuned plus manifest | 3B | TBD | TBD | low | yes |
| Cloud prompt-only | unknown | TBD | TBD | high | no |
| Cloud plus manifest | unknown | TBD | TBD | high | no |

### 6.2 Does HAI Reduce Required Model Scale?

Expected figure:

```text
x-axis: model size
y-axis: HACO score
lines: no contract / manifest / full HAI / fine-tuned plus HAI
```

Claim form:

Full HAI contract shifts the performance curve left: smaller models reach the same safety-constrained score.

### 6.3 Which Contract Components Matter?

| Removed component | HACO drop | Main failure mode |
|---|---:|---|
| `agent_safe` | TBD | unsafe commit/archive |
| mutation classes | TBD | wrong write path |
| exit codes | TBD | bad retry/recovery |
| output schemas | TBD | malformed proposal |
| proposal gate | TBD | skipped orchestration |
| manifest | TBD | hallucinated commands |

### 6.4 Safety Results

Report unsafe mutation attempts, direct SQLite write attempts, clinical claims, prompt-injection obedience, refusal false positives, and refusal false negatives.

### 6.5 Faithfulness Results

Evaluate narration against `hai today` and `hai explain` using atomic claims:

- supported
- unsupported
- contradicted
- outside scope
- abstained correctly

### 6.6 Drift Robustness

Test whether fine-tuned models memorize stale commands. Core question: does fine-tuning help only when paired with live manifest retrieval?

## 7. Discussion

### 7.1 Interpretation

If results support the thesis, HAI does not make small models generally medically capable. It makes bounded personal-health operation easier by moving truth, validation, mutation, safety policy, and audit into software.

### 7.2 Why This Matters

For personal AI:

- privacy improves when operation can be local
- safety improves when mutation is governed
- reliability improves when factuality is reconstructable
- smaller models become viable for bounded workflows

### 7.3 What the Model Still Does

The model remains useful for language understanding, routing, clarification, summarization, proposal drafting, refusal phrasing, and user-facing explanation.

The model does not own health truth, invent policy, mutate state directly, diagnose, or bypass runtime gates.

## 8. Limitations

- HAI is one runtime, not a universal health-agent platform.
- Benchmark tasks are synthetic/redacted.
- Personal-health workflows are non-clinical.
- Outcome benefit to users is not proven.
- Runtime correctness is assumed but still requires audit.
- Cloud comparison depends on chosen models.
- Local model results vary by hardware and quantization.
- Fine-tuning may overfit unless drift splits are strong.

## 9. Ethics, Privacy, and Safety

State clearly:

- no clinical claims
- no diagnosis or treatment recommendations
- no private health rows in training data
- local-first runtime
- hosted-model privacy caveat
- public fixtures only
- user-gated mutation
- audit logs and explainability
- refusal expected for unsafe requests

## 10. Conclusion

This paper tests whether personal-health agent reliability can be improved by changing the software environment rather than only scaling the model. HAI provides a governed local runtime contract. HACO-Bench measures contract-obedient operation. Scaffold ablations estimate how much the contract reduces model-scale requirements.

Final claim template:

> Our results suggest that contract-governed runtimes can make smaller local models viable operators for bounded personal-health workflows, provided that truth, validation, mutation, safety policy, and audit remain owned by software rather than the model.
