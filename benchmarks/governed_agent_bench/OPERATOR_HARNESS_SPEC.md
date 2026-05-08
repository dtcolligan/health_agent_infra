# Operator Harness Specification

**Status:** Model-agnostic harness specification, 2026-05-08.

The operator harness is the bridge between arbitrary models and the HAI
runtime. It replaces the Claude-Code-specific dogfood loop with a neutral
benchmark interface.

## Core Idea

The model does not need shell access, Claude Code, or MCP. The harness
acts as the executor:

```text
task + manifest + allowed context
        |
        v
model produces structured operator action
        |
        v
harness validates action shape
        |
        v
harness runs allowed HAI CLI command or records refusal/final
        |
        v
harness records observation and trajectory
        |
        v
scorer grades trajectory
```

## Model Input

Each model call should receive:

- system instructions for the benchmark condition;
- task user prompt;
- allowed manifest/context excerpts;
- output schema for the next operator action;
- prior observations if multi-step.

Prompt-only conditions omit manifest/contract context except what the
user prompt naturally contains. Contract conditions include the frozen
manifest and relevant contract notes.

## Operator Action Schema

The model should emit exactly one JSON object per turn:

```json
{
  "action_type": "command|refusal|final",
  "command": "hai doctor",
  "args": {
    "--json": true
  },
  "reason": "short rationale",
  "final_text": null
}
```

Rules:

- `command` is required when `action_type == "command"`.
- `args` must be a JSON object, not a shell string.
- `refusal` must include a concise reason.
- `final` must not invent runtime state.
- Direct shell commands outside `hai` are invalid unless a specific task
  explicitly tests forbidden direct-state access.

## Trajectory Encoding

The harness records each accepted operator action in
`trajectory.schema.json` without collapsing it into a shell string:

- `step_type: "command"` uses `command` plus structured `args`, and may
  include `reason`.
- `step_type: "refusal"` uses `reason` and may include `final_text` when
  the refusal is user-facing.
- `step_type: "final"` uses `final_text` and may include `reason`.
- Observation steps record `exit_code`, `stdout_ref`, and `stderr_ref`.

Every trajectory must carry the experiment `condition`. Model-backed
conditions should also carry `model_id`; `rule_baseline` may omit it or
use `model_id: "rule_baseline"`.

## Harness Responsibilities

The harness owns:

- prompt construction;
- model invocation;
- action JSON parsing;
- command allowlist enforcement;
- CLI execution;
- stdout/stderr/exit-code capture;
- trajectory writing;
- retry policy for malformed model output;
- deterministic scoring handoff.

The model owns:

- choosing the next valid action;
- deciding when to refuse;
- deciding when a final answer is supported by observations.

The HAI runtime owns:

- validation;
- mutation boundaries;
- state persistence;
- audit logs;
- command outputs.

## Execution Safety

The harness must:

- run only against synthetic fixture state;
- never use live credentials;
- never run arbitrary shell text from the model;
- translate structured `command` + `args` into subprocess invocations;
- block non-`hai` commands by default;
- record blocked direct-state attempts as violations;
- use temp or fixture-specific DB paths where possible.

## Conditions

| Condition | Context policy |
|---|---|
| rule_baseline | No model call; deterministic rules emit actions. |
| local_prompt_only | User prompt and generic action schema only. |
| local_manifest | User prompt, action schema, frozen manifest/context. |
| cloud_prompt_only | Same as local prompt-only with cloud model. |
| cloud_manifest | Same as local manifest with cloud model. |
| fine_tuned_local | Fine-tuned local with action schema, no live manifest unless condition says so. |
| fine_tuned_local_manifest | Fine-tuned local with action schema and manifest/context. |

## MVP Harness Exit Criteria

- Can load a task and frozen manifest reference.
- Can accept a hand-authored action JSON without calling a model.
- Can execute at least one read-only HAI command against fixture state.
- Can write a trajectory.
- Can hand the trajectory to the scorer.

Model API adapters come after this MVP.
