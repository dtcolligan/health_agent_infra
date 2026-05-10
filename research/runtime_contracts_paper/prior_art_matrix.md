# Prior-Art Matrix

**Status:** First checked matrix for `WP-PRIOR-001`, 2026-05-10.

This is a paper-planning artifact, not final citation prose. It records
where the runtime-contract paper is closest to existing work and where
the contribution delta needs to be stated carefully. Source links were
checked from public paper/project pages during this packet; Dom should
still review final citation quality before submission.

## Closest-Work Memo

Top five closest comparison points:

1. **AgentSpec** is closest on runtime enforcement: it also frames safe
   agents through explicit constraints enforced at runtime. The delta is
   that this project evaluates an integrated local runtime contract over
   sensitive user-owned state, with proposal/commit separation, audit
   chain, stale manifests, and mechanism-off ablations.
2. **tau-bench** is closest on policy-obedient tool agents with mutable
   state. The delta is that tau-bench evaluates domain-rule adherence and
   final database state, while GovernedAgentBench isolates runtime
   mechanisms such as `agent_safe`, proposal gates, refusal-in-code, and
   audit evidence.
3. **BFCL / Gorilla / API-Bank / ToolLLM** are closest on tool/function
   calling. The delta is that function correctness is only one part of
   the runtime contract; this paper also evaluates authorization,
   mutation classes, user-gated commits, refusal boundaries, and audit.
4. **AgentClinic / MedAgentBench** are closest on health-domain agents.
   The delta is that HAI is explicitly non-clinical and measures
   contract obedience over a personal-wellness runtime, not diagnosis,
   treatment, EHR reasoning, or clinical utility.
5. **PH-LLM / Health-LLM** are closest on wearable/personal-health data.
   The delta is that those works study prediction or coaching quality,
   while this paper studies governed operation over local user-owned
   state with deterministic validation, audit, and ablation surfaces.

Contribution sentence to defend:

> Prior tool-use, web-agent, health-agent, and structured-output work
> evaluates whether models can call tools or complete domain tasks. This
> paper evaluates whether an enforceable local runtime contract changes
> the safety-constrained operation of agents over sensitive user-owned
> state.

## Matrix

| Citation key | Source | Artifact type | Task setting | Agent interface | Safety mechanism | State ownership | Mutation model | Scoring | Difference from this paper | Must cite? |
|---|---|---|---|---|---|---|---|---|---|---|
| `yao2022react` | https://arxiv.org/abs/2210.03629 | Paper / prompting method | QA, fact verification, web/shop-like decision tasks | Interleaved reasoning and actions | Prompted reasoning traces; environment feedback | External environments / public data | Tool actions, no governed local mutation contract | Task success, interpretability | Establishes reason+act prompting but does not enforce command authorization, user-gated mutation, or audit chain in software. | yes |
| `schick2023toolformer` | https://arxiv.org/abs/2302.04761 | Paper / tool-use learning | API calls for search, QA, calculator, translation, calendar | API-call tokens learned by LM | Learned tool-call decision policy | External tools / public tasks | Tool calls, no proposal/commit split | Downstream task accuracy | Shows models can learn when and how to call tools; runtime contracts instead move authority and validation out of model weights. | yes |
| `li2023apibank` | https://arxiv.org/abs/2304.08244 | Benchmark | Tool-augmented dialogues across API domains | API retrieval/calling | Runnable API evaluation | Synthetic benchmark state / APIs | API calls | Planning/retrieval/calling accuracy | API-Bank measures tool-use ability; GovernedAgentBench measures governed operation, unsafe mutation avoidance, refusal, and audit. | yes |
| `qin2023toolllm` | https://arxiv.org/abs/2307.16789 | Framework / benchmark | Real-world API use | API retrieval and tool calls | Tool-use data/evaluator | Public API/tool dataset | API calls | Tool-use success | ToolLLM scales API supervision; it is not an enforceable local runtime with user-owned state and explicit mutation classes. | yes |
| `patil2023gorilla` | https://arxiv.org/abs/2305.15334 | Model / API benchmark | API-call generation | API calls from retrieved docs | Retrieval to reduce hallucinated API calls | Public API docs | API calls | API-call correctness, hallucination | Gorilla/APIBench targets correct API invocation and doc drift; this paper adds authorization, proposal gates, refusal, and audit-chain ablations. | yes |
| `bfcl2024` | https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html | Live leaderboard / dataset | Function/tool calling across languages and APIs | Function calls | Executable/AST function-call checks; relevance detection | Benchmark functions / synthetic cases | Function calls | Function-call correctness, cost, latency | BFCL is a strong function-calling baseline; GovernedAgentBench treats function selection as one mechanism among broader runtime governance. | yes |
| `yao2024taubench` | https://arxiv.org/abs/2406.12045 | Benchmark | Tool-agent-user interactions in real-world domains | API tools plus simulated user | Domain policy guidelines; final DB-state comparison | Synthetic domain database | Tool mutations to database state | Final-state match and policy adherence | tau-bench is close on stateful policy-obedient tool use; it does not isolate local runtime-contract mechanisms or audit-chain evidence. | yes |
| `liu2023agentbench` | https://arxiv.org/abs/2308.03688 | Benchmark | Multi-environment interactive agent tasks | Environment actions / tools | Environment constraints | Benchmark environments | Environment-specific actions | Task success and failure analysis | AgentBench evaluates agent capability broadly; this paper narrows to enforceable contracts over sensitive local state. | yes |
| `zhou2023webarena` | https://arxiv.org/abs/2307.13854 | Benchmark / environment | Realistic web tasks | Browser actions | Self-hosted web environment; task validators | Self-hosted web app data | Web mutations | Functional task completion | WebArena stresses realistic web operation but not local user-owned data, explicit agent-safe metadata, or proposal/commit governance. | yes |
| `deng2023mind2web` | https://arxiv.org/abs/2306.06070 | Dataset / benchmark | Real-world website tasks | Browser/UI actions | Crowdsourced action traces | Public websites / benchmark tasks | Web actions | Element/action prediction and task progress | Mind2Web targets generalist web navigation; GovernedAgentBench targets typed CLI contracts and deterministic mutation/audit rules. | yes |
| `yao2022webshop` | https://arxiv.org/abs/2207.01206 | Benchmark / simulated shop | E-commerce purchase tasks | Web actions | Simulated environment and reward | Product corpus / synthetic user goals | Purchase/navigation actions | Reward and task success | WebShop is grounded interaction, but not sensitive local state with governed mutation classes and audit logs. | yes |
| `xie2024osworld` | https://arxiv.org/abs/2404.07972 | Benchmark / environment | Real computer-use tasks | GUI/computer actions | Execution-based evaluation scripts | OS/app state in benchmark VMs | File/app/web mutations | Task success | OSWorld broadens computer-use realism; it does not study a domain runtime contract with ablatable governance mechanisms. | yes |
| `drouin2024workarena` | https://arxiv.org/abs/2403.07718 | Benchmark / environment | Enterprise ServiceNow tasks | Browser actions via BrowserGym | Hosted benchmark environment | Enterprise-like benchmark state | Web-app mutations | Task success | WorkArena measures enterprise web agents; GovernedAgentBench measures contract-obedient local runtime operation. | yes |
| `jimenez2023swebench` | https://arxiv.org/abs/2310.06770 | Benchmark | Real GitHub software issues | Code editing / execution harness | Tests/containerized evaluation | Public repositories | Patch mutation | Issue-resolution tests | SWE-bench is a high-value executable benchmark but focuses code repair, not governed operation over sensitive personal data. | yes |
| `geng2025jsonschema` | https://arxiv.org/abs/2501.10868 | Benchmark / structured output study | JSON Schema constrained decoding | Structured generation | Constrained decoding / schema compliance | Real-world schemas | Output object only | Coverage, efficiency, quality | JSON schema compliance is necessary but insufficient for authorization, proposal/commit gates, policy, and audit. | yes |
| `shorten2024structuredrag` | https://arxiv.org/abs/2408.11061 | Benchmark | JSON response formatting | Prompted JSON output | Format instructions | Synthetic structured-output tasks | Output object only | JSON-format success | Useful for structured-output reliability; does not enforce runtime mutation boundaries or audit. | optional |
| `bai2022constitutional` | https://arxiv.org/abs/2212.08073 | Safety/alignment method | Assistant harmlessness | Natural-language assistant responses | Constitution-guided critique/revision/RLAIF | Hosted model training setting | No runtime mutation model | Helpfulness/harmlessness preference eval | Constitutional AI governs model behavior by training; runtime contracts govern software authority even when model behavior varies. | yes |
| `alshiekh2018shielding` | https://doi.org/10.1609/aaai.v32i1.11797 | Formal-methods safety paper | Reinforcement learning | Agent actions monitored by shield | Runtime shield enforcing temporal-logic properties | RL environments | Corrective action monitor | Safety and reward | Shielding is conceptually close as runtime enforcement; this paper adapts runtime enforcement to LLM tool operators and audit. | yes |
| `agentspec2025` | https://arxiv.org/abs/2503.18666 | DSL / runtime enforcement | LLM agents across domains | Agent actions constrained by DSL | Runtime constraints | Application-dependent | Tool/action constraints | Safety/reliability under constraints | AgentSpec is the closest runtime-enforcement comparison; HAI/GovernedAgentBench adds local user-owned data, benchmark fixtures, audit chain, and mechanism ablations. | yes |
| `mcp2024` | https://modelcontextprotocol.io/specification/ | Protocol/specification | Tool/data-source interoperability | MCP tools/resources/prompts | Protocol schema and client/server boundaries | Application-provided data sources | Tool calls / resources | Protocol conformance, not task benchmark | MCP standardizes context/tool transport; runtime contracts define domain authority, mutation classes, and audit over a concrete runtime. | yes |
| `kleppmann2019localfirst` | https://martin.kleppmann.com/2019/10/23/local-first-at-onward.html | Systems paper / manifesto | Local-first applications | Application data model | Local ownership, sync, privacy principles | User-owned local-first data | App-local data mutation | Qualitative principles | Provides the local data-ownership motivation; this paper evaluates agent operation over such local state. | yes |
| `min2023factscore` | https://arxiv.org/abs/2305.14251 | Factuality metric | Long-form generation | Text generation with evidence source | Atomic fact support checking | External knowledge source | No mutation | Factual precision | FActScore motivates fine-grained factuality; GovernedAgentBench narrows faithfulness to runtime read surfaces and audit references. | yes |
| `cosentino2024phllm` | https://arxiv.org/abs/2406.06474 | Health LLM / benchmark | Sleep and fitness from wearable data | Natural-language insight/recommendation generation | Domain rubrics and model evaluation | Personal-health datasets / wearable data | Recommendation text, not governed runtime mutation | Expert rubric, exams, prediction | PH-LLM is close on wearable/personal-health context; this paper avoids coaching-quality claims and evaluates non-clinical contract obedience. | yes |
| `kim2024healthllm` | https://health-llm.github.io/ | Health prediction framework | Health prediction from wearable sensors | LLM over contextual and physiological data | Task evaluation, not runtime governance | Wearable-sensor datasets | Prediction output | Prediction task performance | Health-LLM studies sensor-grounded prediction; HAI/GAB studies governed operation over local state and abstention/refusal. | optional |
| `schmidgall2024agentclinic` | https://arxiv.org/abs/2405.07960 | Clinical agent benchmark | Simulated clinical diagnosis workflows | Dialogue, data collection, tools | Simulated clinical environment and moderators | Synthetic/simulated clinical cases | Clinical decision actions | Diagnostic accuracy, bias, compliance | AgentClinic is explicitly clinical; HAI is explicitly non-clinical and evaluates refusal of diagnosis-shaped requests. | yes |
| `jiang2025medagentbench` | https://arxiv.org/abs/2501.14654 | Medical agent benchmark | Virtual EHR tasks | EHR-compatible tools | Benchmark environment | Virtual patient/EHR data | Medical task actions | Medical-agent task success | MedAgentBench evaluates medical EHR agents; this paper should contrast by emphasizing non-clinical wellness and user-gated local mutation. | yes |
| `pandit2025medhallu` | https://arxiv.org/abs/2502.14302 | Medical hallucination benchmark | Medical QA hallucination detection | Text QA outputs | Hallucination labels / entailment | Medical QA benchmark data | No mutation | Hallucination detection F1/precision | Supports the risk framing for medical hallucination, but GovernedAgentBench measures refusal and boundary violations rather than medical answer quality. | optional |
| `khandekar2024medcalc` | https://arxiv.org/abs/2406.12036 | Medical calculation benchmark | Clinical calculators | Text/code/math answer generation | Ground-truth calculator tasks | Clinical calculation dataset | No autonomous mutation | Calculation accuracy | Useful contrast for tool/calculator medicine; HAI forbids clinical calculator/diagnosis claims and evaluates non-clinical runtime governance. | optional |

## Paper-Section Outline From Matrix

1. **Tool-use agents and function calling.** Use ReAct, Toolformer,
   API-Bank, ToolLLM, Gorilla, and BFCL to establish that tool-call
   accuracy is well-studied. Transition: runtime contracts are about
   authority and state mutation, not only tool-call syntax.
2. **Agent benchmarks and realistic environments.** Use AgentBench,
   WebArena, Mind2Web, WebShop, OSWorld, WorkArena, SWE-bench, and
   tau-bench to position GovernedAgentBench as narrower but more
   governance-specific.
3. **Structured output, safety, and runtime enforcement.** Use
   JSONSchemaBench, StructuredRAG, Constitutional AI, shielding,
   AgentSpec, and MCP. State that structured output and protocols are
   components, while runtime contracts combine manifest, typed actions,
   enforcement, proposal gates, refusal, and audit as an evaluated
   intervention.
4. **Personal-health and clinical-agent evaluations.** Use PH-LLM,
   Health-LLM, AgentClinic, MedAgentBench, MedHallu, and MedCalc-Bench
   to prevent health-overclaiming. The paper is not clinical evaluation;
   HAI is a non-clinical sensitive-data reference runtime.
5. **Factuality and audit.** Use FActScore as the closest factuality
   evaluation anchor, then explain that GAB's L5 metrics are
   runtime-specific: cite only what `hai today` / `hai explain` and
   audit rows support.

## Citation Notes

- Final paper should prefer conference/journal URLs where available
  (for example WebShop/SWE-bench Princeton pages, AgentClinic Nature
  page) and arXiv where that is the canonical public source.
- Citation quality remains a manual-review item for Dom; no final
  BibTeX entries are claimed by this matrix.
