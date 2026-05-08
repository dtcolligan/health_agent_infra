# Benchmarks

Benchmarks in this repo measure contract-governed agent operation. The
first benchmark is GovernedAgentBench, which uses HAI as the reference
runtime while keeping the benchmark schema separate from HAI internals.

This is the owner lane for benchmark work. GovernedAgentBench lives under
`governed_agent_bench/`, and benchmark-specific tests live under
`verification/`.

Read [`../project/FRAME.md`](../project/FRAME.md),
[`../project/DECISIONS.md`](../project/DECISIONS.md),
[`../project/OPERATING_MODEL.md`](../project/OPERATING_MODEL.md),
[`../research/runtime_contracts_paper/PAPER_FRAME.md`](../research/runtime_contracts_paper/PAPER_FRAME.md),
and
[`../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`](../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md)
for the research frame before adding benchmark tasks.

See `governed_agent_bench/`.
