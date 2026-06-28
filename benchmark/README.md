# Benchmark Lane

GovernedAgentBench is the benchmark companion to the preprint
*Measuring Deterministic Governance Mechanisms in Agent Harnesses*.

It measures the harness layer directly: the model, prompt, task suite,
manifest, and scorer are held constant while `runtime_mode` is varied.
The treatment is the deterministic runtime contract; the scored
responses are task success and contract-violation metrics.

The benchmark lives at [`governed_agent_bench/`](governed_agent_bench/).
The inner namespace is also the Python package and JSON schema-version
prefix (`governed_agent_bench.trajectory.v2`,
`governed_agent_bench.score.v2`, and related schemas).

Benchmark-specific tests live under
[`verification/`](verification/).

Read [`/PAPER.md`](../PAPER.md) for active scope and decisions. Start at
[`governed_agent_bench/README.md`](governed_agent_bench/README.md) for
the benchmark itself, and
[`governed_agent_bench/BENCHMARK_CARD.md`](governed_agent_bench/BENCHMARK_CARD.md)
for intended use, non-use, data provenance, limitations, and
reproducibility boundaries.
