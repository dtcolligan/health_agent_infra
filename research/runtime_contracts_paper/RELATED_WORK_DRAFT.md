# Related Work Draft

**Status:** Draft section for `WP-PAPER-001`, 2026-05-10.

This section is written against `prior_art_matrix.md`. It is intended
for later integration into `DRAFT_PAPER.md` after Dom reviews citation
quality and the paper's final claim tier. Citation keys refer to the
matrix rows.

## Related Work

### Tool-Using Language Agents

Language-model agents can already interleave reasoning with actions,
learn when to call tools, and generate API or function calls. ReAct
showed that reasoning traces and environment actions can be interleaved
to improve interactive problem solving [@yao2022react], while
Toolformer studied how a model can learn API-use behavior from
self-supervised tool-call annotations [@schick2023toolformer]. A large
line of tool-use benchmarks and systems has since focused on whether
models can retrieve, select, and call APIs correctly, including
API-Bank [@li2023apibank], ToolLLM [@qin2023toolllm], Gorilla
[@patil2023gorilla], and BFCL [@bfcl2024].

This paper treats correct tool selection as necessary but not
sufficient. Governed operation over sensitive user-owned state also
requires command authorization, mutation classes, proposal/commit
separation, deterministic validation, refusal boundaries, and audit
references. In other words, the runtime contract is not just a function
signature. It is the software authority boundary around what the model
may propose, what the runtime may commit, and what evidence the operator
can cite.

### Agent Benchmarks And Stateful Environments

Agent benchmarks increasingly evaluate interactive behavior in more
realistic environments. AgentBench covers multiple agent environments
[@liu2023agentbench]. WebArena, Mind2Web, WebShop, OSWorld, and
WorkArena evaluate browser, web, shopping, operating-system, and
enterprise workflows [@zhou2023webarena; @deng2023mind2web;
@yao2022webshop; @xie2024osworld; @drouin2024workarena]. SWE-bench
uses real software issues and executable tests to evaluate code-repair
agents [@jimenez2023swebench].

The closest benchmark comparison is tau-bench, which evaluates
tool-agent-user interactions with domain rules and mutable database
state [@yao2024taubench]. GovernedAgentBench shares tau-bench's concern
with stateful tool use, but its intervention is different: the benchmark
varies runtime mechanisms such as validation, `agent_safe` dispatch,
proposal gates, refusal-in-code, and audit-chain evidence. The primary
question is therefore not only whether an agent completes a task, but
whether enforcing the runtime contract changes safety-constrained
operation.

### Structured Output, Guardrails, And Runtime Enforcement

Structured-output work shows that models can be constrained toward
valid JSON or schema-shaped responses. JSONSchemaBench evaluates
constrained decoding over real-world schemas [@geng2025jsonschema],
and StructuredRAG studies JSON response formatting behavior
[@shorten2024structuredrag]. These efforts are directly relevant to
typed operator actions, but schema-valid output alone does not enforce
which commands are authorized, whether a mutation requires human
approval, or whether a final explanation is grounded in audit rows.

Safety and runtime-enforcement work offers a second comparison point.
Constitutional AI studies model behavior shaped by critique, revision,
and AI feedback [@bai2022constitutional]. Shielding in reinforcement
learning studies runtime monitors that prevent unsafe actions with
formal constraints [@alshiekh2018shielding]. AgentSpec is especially
close to this paper's framing because it specifies and enforces
constraints on LLM-agent behavior at runtime [@agentspec2025]. The
runtime-contract contribution here is narrower and more concrete:
enforcement is instantiated in HAI, exposed through a capabilities
manifest and CLI surface, measured with synthetic local fixtures, and
ablated mechanism by mechanism.

Protocol work such as the Model Context Protocol standardizes how tools
and data sources are exposed to agents [@mcp2024]. Runtime contracts are
complementary to such protocols. A protocol can transport tool metadata;
the runtime contract defines the domain authority model, mutation
classes, refusal envelope, validation gates, and audit chain that make a
tool surface governable.

### Local User-Owned Data And Personal Health Context

The project is motivated by local-first software values: user-owned
state should remain locally available and under user control, rather
than being treated as a hosted service side effect [@kleppmann2019localfirst].
This matters for personal agents because the data being operated on may
be sensitive even when the task is not clinical.

Recent health and wearable LLM work studies prediction, coaching, and
question-answering over personal or sensor data. PH-LLM focuses on sleep
and fitness insights from wearable data [@cosentino2024phllm], and
Health-LLM studies health prediction from contextual and physiological
sensor data [@kim2024healthllm]. HAI uses a personal-wellness domain as
a reference runtime, but the paper does not claim health-advice quality.
The measured behavior is contract obedience: valid commands, safe
mutation boundaries, refusal of clinical requests, and faithful
narration from runtime read surfaces.

Clinical-agent benchmarks are therefore a contrast class rather than the
target setting. AgentClinic evaluates simulated clinical workflows
[@schmidgall2024agentclinic], MedAgentBench evaluates medical-agent
tasks over virtual EHR-style environments [@jiang2025medagentbench],
and MedHallu studies medical hallucination detection [@pandit2025medhallu].
MedCalc-Bench evaluates medical calculation accuracy
[@khandekar2024medcalc]. GovernedAgentBench should not be read as a
medical benchmark. Its health boundary is part of the contract: the
operator must refuse diagnosis- or treatment-shaped requests and remain
inside non-clinical wellness operation.

### Factuality, Faithfulness, And Audit

Factuality metrics such as FActScore decompose generated text into
atomic claims and check whether those claims are supported by evidence
[@min2023factscore]. GovernedAgentBench adopts the same broad concern
with unsupported claims but grounds it in a runtime-specific evidence
model. L5 tasks ask whether an operator narrates only from `hai today`,
`hai explain`, and audit-chain references. Unsupported narration is not
just a language-generation error; it is a failure to respect the
runtime's source-of-truth boundary.

### Summary Of The Delta

Prior work shows substantial progress on tool use, web agents,
structured outputs, stateful task environments, guardrails, and
health-domain LLM evaluation. This paper's contribution is the
integration and measurement of a local runtime contract: the model sees
the deployment-realistic contract, but the runtime owns validation,
authorization, mutation, refusal, and audit. GovernedAgentBench then
asks whether those enforceable mechanisms change agent behavior under a
held-constant prompt and synthetic sensitive-data fixtures.
