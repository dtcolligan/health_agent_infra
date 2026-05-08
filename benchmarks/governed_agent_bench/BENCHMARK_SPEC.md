# GovernedAgentBench Specification

**Status:** Benchmark specification, 2026-05-08.

GovernedAgentBench evaluates whether a model can operate a governed
runtime through an explicit software contract. HAI is the first
reference runtime. Personal wellness is the first reference domain, but
the benchmark should not collapse into health-advice evaluation.

## Evaluation Object

The benchmark evaluates contract-governed operation:

- selecting valid commands;
- respecting `agent_safe` and mutation boundaries;
- producing schema-valid proposals;
- recovering from `USER_INPUT` and other expected runtime feedback;
- refusing unsupported or unsafe requests;
- narrating only from allowed runtime read surfaces;
- adapting to contract drift.

It does not evaluate:

- whether HAI gives good health advice;
- clinical correctness;
- consumer UX quality;
- Claude Code as a product;
- MCP as a transport protocol;
- private wearable data.

## Task Levels

| Level | Name | What it tests |
|---|---|---|
| L1 | Intent-to-command routing | Can the model map a user request to an allowed runtime command? |
| L2 | Setup and recovery | Can the model respond correctly to setup gaps and `USER_INPUT` outputs? |
| L3 | Daily-loop orchestration | Can the model choose the correct sequence of read/propose/synthesize/review operations? |
| L4 | Schema-valid proposal generation | Can the model produce valid proposal payloads under bounded schemas? |
| L5 | Faithful narration | Can the model summarize `hai today` / `hai explain` without unsupported claims? |
| L6 | Governance/refusal | Can the model refuse unsafe, clinical, or forbidden mutation requests? |
| L7 | Contract drift | Can the model adapt when a manifest changes or a stale command is invalid? |

## MVP Task Mix

Minimum vertical slice:

- 2 L1 tasks;
- 2 L2 tasks;
- 2 L5 tasks;
- 2 L6 tasks;
- 2 L7 tasks.

L3 and L4 can enter after the scorer can grade simple trajectories.

## Task Anatomy

Each task should include:

- task id;
- level;
- runtime;
- contract version;
- user prompt;
- allowed context;
- expected behavior;
- metrics;
- tags.

The task should not include private rows or hidden expected answers that
only HAI maintainers can interpret.

## Trajectory Anatomy

A trajectory is the recorded behavior of one system on one task:

- system/model id;
- condition;
- messages;
- structured operator actions;
- command observations;
- refusals/finals;
- stdout/stderr references or embedded safe excerpts;
- metadata needed for reproducibility.

Trajectories are the unit of scoring. Model transcripts that are not
converted into trajectories are not benchmark evidence.

## Score Anatomy

A score contains:

- overall pass/fail;
- metric-level values and pass/fail flags;
- violations;
- notes.

Scores must be deterministic for the same task and trajectory.

## Versioning

Version these independently:

- task schema;
- trajectory schema;
- score schema;
- manifest snapshot;
- task set;
- scorer.

The paper should report all of them.

## Benchmark Card Requirements

The benchmark card should eventually state:

- intended use;
- non-use / misuse;
- data provenance;
- private-data exclusions;
- clinical-boundary exclusions;
- task family coverage;
- known blind spots;
- model conditions tested;
- scorer limitations.
