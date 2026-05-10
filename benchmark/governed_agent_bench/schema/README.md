# Benchmark Schemas

`operator_action.schema.json` defines the structured JSON object a model
emits for one harness turn. It is narrower than a trajectory step:
the harness validates the action, executes or records it, then appends
the corresponding step to `trajectory.schema.json`.

Mapping:

- `action_type: "command"` becomes a `step_type: "command"` trajectory
  row with the same `command`, structured `args`, and optional `reason`.
- `action_type: "refusal"` becomes `step_type: "refusal"` with `reason`
  and optional user-facing `final_text`.
- `action_type: "final"` becomes `step_type: "final"` with `final_text`
  and optional `reason`.

The action schema does not allow arbitrary shell text. Commands are HAI
command names, and arguments are a JSON object keyed by CLI flags.
