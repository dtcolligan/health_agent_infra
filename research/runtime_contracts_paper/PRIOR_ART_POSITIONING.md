# Prior-Art Positioning Plan

**Status:** Research-planning document, 2026-05-08.

This file defines the prior-art work needed before the paper can claim a
defensible contribution. It is a planning document, not a completed
literature review.

## Positioning Risk

The obvious reviewer objection is:

> This is just tool use, schemas, guardrails, and logging around an
> agent. What is new?

The paper must answer that directly. The contribution is not any single
component. The contribution must be positioned as the integrated runtime
contract, the bounded agent operation setting, the benchmark, and the
model-scale / ablation measurement.

## Prior-Art Buckets

### Agent Tool Use And Planning

Purpose: distinguish GovernedAgentBench from general tool-use benchmarks
and agent-planning papers.

Representative areas to cover:

- ReAct-style reasoning and acting.
- Toolformer-style tool-use learning.
- API/tool-use benchmarks such as API-Bank, ToolLLM, Gorilla, BFCL.
- Web/task agents and long-horizon agent benchmarks.

Positioning question:

> Do these works evaluate contract obedience over user-owned sensitive
> state with enforceable mutation boundaries and audit?

### Structured Output And Constrained Generation

Purpose: distinguish runtime contracts from output formatting alone.

Representative areas to cover:

- JSON mode / function calling.
- JSON schema generation benchmarks.
- Constrained decoding libraries and grammar-guided decoding.
- Repair loops for malformed structured outputs.

Positioning question:

> Does structured generation alone enforce command authorization,
> mutation boundaries, proposal/commit separation, and audit?

### Agent Safety, Guardrails, And Runtime Governance

Purpose: position runtime contracts against safety wrappers and policy
layers.

Representative areas to cover:

- Guardrails frameworks.
- Tool-permissioning and sandboxing.
- Runtime monitors.
- Constitutional / policy-based agent control.
- MCP and agent-tool protocol work.

Positioning question:

> Are safety and audit treated as part of the evaluated contract, or as
> separate post-hoc infrastructure?

### Local / On-Device / Private Agents

Purpose: connect to local models and user-owned state under a governed runtime contract.

Representative areas to cover:

- On-device assistant work.
- Local LLM deployment constraints.
- Privacy-preserving personal agents.
- User-owned data stores and personal data agents.

Positioning question:

> Is the paper's setting about local bounded operation over structured
> user-owned state, or about hosted API access?

### Health And Clinical-Agent Benchmarks

Purpose: avoid accidentally claiming clinical capability.

Representative areas to cover:

- Health LLM evaluation.
- Medical hallucination and clinical reasoning benchmarks.
- AgentClinic / MedAgentBench-like clinical agent evaluations.
- Personal health assistant papers and product-adjacent systems.

Positioning question:

> Is this paper evaluating health advice quality, or non-clinical
> contract obedience in a sensitive-data reference domain?

### Factuality, Faithfulness, And Audit

Purpose: support L5 narration and audit-reference metrics.

Representative areas to cover:

- FActScore-style factuality.
- Citation/grounding faithfulness.
- Claim extraction and unsupported narration detection.
- Audit-log based explainability.

Positioning question:

> Does the model narrate only from runtime read surfaces and audit
> references?

## Contribution Delta To Defend

The paper should defend this delta:

1. **Integrated intervention.** The runtime contract is evaluated as a
   combined software intervention, not as isolated prompt/tool features.
2. **Sensitive user-owned state.** The setting is local structured data
   with mutation boundaries, not arbitrary web/API tasks.
3. **Reference runtime.** HAI makes the contract concrete and inspectable.
4. **Benchmark.** GovernedAgentBench makes the behavior measurable and
   reusable.
5. **Ablations.** Component removals test which parts of the contract
   matter.
6. **Model-scale question.** The empirical target is whether governance
   changes required model capability.

## Literature Matrix Template

Each prior-art item should be entered with this schema:

| Field | Question |
|---|---|
| Citation key | Stable short key for paper draft. |
| Artifact type | Paper, benchmark, framework, product, protocol. |
| Task setting | Web, code, API, health, local data, other. |
| Agent interface | Tool call, API, browser, function call, MCP, CLI, other. |
| Safety mechanism | Prompt, schema, sandbox, runtime monitor, human approval, audit. |
| State ownership | Hosted service, synthetic state, local user-owned state. |
| Mutation model | Free-form, tool mutation, proposal/commit, human-gated, none. |
| Scoring | Success, safety, factuality, audit, cost, latency, other. |
| Difference from this paper | One to three concrete sentences. |
| Must cite? | yes/no. |

## Work Packet

`WP-PRIOR-001` in `WORK_PACKETS.md` owns the first matrix. It should not
write the paper's related-work section directly. It should produce a
checked matrix and a short memo that future paper-writing packets can
consume.
