# Benchmark Lane

GovernedAgentBench is the benchmark companion to the preprint
*Told or Enforced: When In-Context Contracts Substitute for Runtime
Enforcement in Agent Harnesses*.

It separates two levers per mechanism: whether the constraint is specified
in the in-context contract (the manifest in the prompt) and whether the
runtime enforces it. The scored responses are task success and
contract-violation metrics. (Detailed methodology docs are mid-sync to the
2x2 design; see `PAPER.md` D-31/D-32 and "Downstream Sync Pending.")

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
