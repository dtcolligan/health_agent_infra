# HAI Paper-Readiness Plan

**Status:** Paper-critical HAI engineering plan, 2026-05-08.

This file defines the minimum HAI engineering work needed for the paper
and GovernedAgentBench. In plain terms: make HAI usable as the reference
runtime in a model-agnostic benchmark without relying on Claude Code,
private repo knowledge, real credentials, or private health rows.

This is broader than taking a manifest snapshot and narrower than
"finish HAI."

## Goal

Engineer a paper-ready HAI runtime slice that a model-agnostic benchmark
harness can operate through documented public interfaces.

The benchmark should not depend on Claude Code, private repo knowledge,
or MCP. It should depend on:

- a frozen capabilities manifest;
- documented command/argument/output behavior;
- deterministic exit-code semantics;
- fixture state setup and reset;
- read surfaces;
- validation and audit surfaces.

## Paper-Ready HAI Components

| Component | Paper-readiness requirement |
|---|---|
| Capabilities manifest | A committed `hai capabilities --json` snapshot with provenance command, source version, schema version, and generation date. |
| Command set | Benchmark-eligible commands identified; non-agent-safe commands marked and tested as forbidden when relevant. |
| Arguments | Required and optional args represented in the manifest or documented alongside it. |
| Output schemas | JSON/plain read surfaces documented enough for scoring. |
| Exit codes | `OK`, `USER_INPUT`, validation errors, and refusal/error behavior documented for benchmark subset. |
| Mutation classes | Read-only, proposal, commit, review, backup, and destructive classes identified. |
| Proposal/commit split | User-owned intent/target activation remains outside agent-safe paths. |
| Audit | Trajectories can reference outputs and audit rows without private data. |
| Fixtures | Synthetic fixture state can be created, reset, and used without external credentials. |

## Manifest Snapshot Envelope

The frozen manifest should not be committed as a raw
`hai capabilities --json` dump. It should be wrapped in a provenance
envelope so later scorers and drift tasks can distinguish manifest
content from snapshot origin.

Required envelope fields:

```json
{
  "schema_version": "governed_agent_bench.manifest_snapshot.v1",
  "manifest_version": "hai_0_2_0",
  "generated_at": "2026-05-08T00:00:00Z",
  "generated_by": "hai capabilities --json",
  "source_commit": "<git commit hash>",
  "hai_version": "0.2.0",
  "contract_schema_version": "agent_cli_contract.v2",
  "manifest": {}
}
```

`manifest` contains the exact command output. Stability tests should
compare the embedded manifest and stable provenance fields while ignoring
`generated_at`.

## Benchmark-Eligible Command Families

Initial MVP should prefer commands that are already stable and useful for
contract-obedience tasks:

- `hai capabilities` — manifest access.
- `hai doctor` — setup/status and `USER_INPUT` recovery.
- `hai today` — read surface for narration and state awareness.
- `hai explain` — audit/faithfulness read surface.
- `hai propose` — schema-valid proposal generation.
- `hai intent` / `hai target` proposal paths — useful for user-owned
  proposal/commit boundary tasks, with commit paths forbidden to agents.
- `hai intake` read/write paths — only where synthetic fixture state is
  safe and deterministic.

MVP should avoid:

- live wearable pulls;
- real credentials;
- backup/restore as first tasks;
- MCP;
- N-of-1 and future HAI support-lane surfaces.

## Fixture-State Requirements

The benchmark needs fixture states that are:

- synthetic;
- small enough to inspect manually;
- deterministic under repeated runs;
- non-clinical;
- free of private rows;
- compatible with `hai today`, `hai doctor`, `hai explain`, and proposal
  validation.

Fixture categories:

| Fixture | Purpose |
|---|---|
| `empty_user` | L2 setup recovery and `USER_INPUT` behavior. |
| `ready_user_minimal` | L1 routing and L3 daily-loop tasks. |
| `read_surface_user` | L5 faithful narration from `today` / `explain`. |
| `governance_user` | L6 refusal and forbidden mutation attempts. |
| `drift_user` | L7 stale manifest / changed command behavior. |

## Paper-Readiness Acceptance Criteria

- A human can read the manifest and operate the benchmark subset without
  reading HAI internals.
- A model can be prompted with the frozen manifest and asked to emit a
  structured operator action.
- The operator harness can execute benchmark-eligible commands through
  the CLI and record observations.
- No benchmark task requires a real wearable account, real credentials,
  private health rows, or clinical judgment.

## Runtime Work Allowed Before GovernedAgentBench Measurement-Readiness

Allowed:

- manifest snapshot command/documentation;
- narrow JSON output consistency fixes for benchmark subset;
- deterministic fixture setup/reset utilities if no existing path is
  sufficient;
- docs clarifying command behavior;
- tests proving fixture/reset determinism.

Not allowed:

- MCP transport;
- additional health domains;
- new wearable integrations;
- HAI v1 product surfaces;
- N-of-1 features;
- broad CLI refactors not required for the paper-ready runtime slice.
