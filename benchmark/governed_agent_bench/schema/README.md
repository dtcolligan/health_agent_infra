# Benchmark Schemas

`model_roster.schema.json` defines the machine-readable fields required
inside the predeclared `benchmark/governed_agent_bench/model_roster.md`
gate artifact. It does not choose models and does not authorize model
runs. A roster becomes valid only after Dom explicitly approves the
model, compute, provider, cost, and data-boundary fields it records.

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

`pilot_manifest.schema.json` defines the top-level record one model-backed
pilot run writes to `runs/pilot/<run>/pilot_manifest.json`. It is the spine
of the `PILOT_PROTOCOL.md` §14 hash lock: the lock is defined by the SHA-256
set the manifest carries. A `status` field gates two states. A `draft`
manifest requires only the §12 runtime fields (run-start UTC, git SHA,
replication n, conditions executed, D-O-01 selection, run outcome) and is used
for pre-lock dry runs. A `locked` manifest additionally requires the full §14
freeze block: `locked_hashes` (the 5 fixed input-file and 28 per-task SHA-256
rows, sourced from `scripts/lock_hashes.json`), `lock_date`,
`lock_commit_sha`, and a settled `d_o_01_selection`. `PILOT_PROTOCOL.md`
itself is excluded from the embedded hash set because a file cannot contain
its own final SHA-256; record that protocol hash in external lock evidence.
The schema records hashes but does not compute them and does not execute the
lock; `pilot_manifest.py` writes the manifest and the orchestrator populates it
at run time.

`condition_summary.schema.json`, `condition_index.schema.json`, and
`rep_ledger.schema.json` define the A2 pilot-orchestrator artifacts. The
summary is a per-runtime-mode cell record with raw cost/wall contribution,
final disposition, per-mechanism cost allocation, a diagnostic
non-load-bearing cost bucket, and reconciliation fields proving that allocated
per-step USD matches the summed trajectory step costs when per-step USD is
available. Condition-level systems keep those allocation fields null rather
than fabricating token-level cost. The index records the complete mode/task
coverage matrix, including out-of-scope and not-run-after-stop cells. The
ledger is the durable per-rep incident trail and carries every disposition
trigger observed for the rep, even when a higher-severity trigger wins the
system outcome.
