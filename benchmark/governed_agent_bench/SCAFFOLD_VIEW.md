# Scaffold View

**Status:** Runtime-mode scaffold documentation, 2026-05-10.

This document describes what an experimenter sees when varying HAI's
runtime mode in GovernedAgentBench. It complements `OPERATORS_VIEW.md`,
which describes what the operator sees.

## Runtime Mode Axis

Runtime modes are selected with `HAI_RUNTIME_MODE` and are accepted only
under the hermetic benchmark recipe. Mechanism-disabling modes require:

- `HAI_HERMETIC=1`;
- redirected `HAI_STATE_DB`;
- redirected `HAI_BASE_DIR`;
- redirected home/config paths through the harness.

The supported modes are:

| Runtime mode | Mechanism disabled | Intended interpretation |
|---|---|---|
| `full_contract` | none | Normal governed runtime. |
| `no_validation` | `validation` | Schema/action/shape validation is bypassed where the ablation seam exists. |
| `no_agent_safe` | `agent_safe` | Dispatch-time `agent_safe=false` enforcement is bypassed for hermetic runs. |
| `no_proposal_gate` | `proposal_gate` | User-gated proposal/commit separation is bypassed where scoped. |
| `no_refusal` | `refusal` | Runtime refusal checks are bypassed where scoped. |
| `no_audit_chain` | `audit_chain` | Evidence-card emission is suppressed while core graph writes remain on. |
| `no_runtime_enforcement` | M4..M8 | Extreme scaffold mode disabling all ablatable runtime mechanisms. |

The model is not told which runtime mode is active. The prompt remains
`deployment_full_v1` in every condition.

## Mechanism Boundaries

The ablatable mechanisms are:

- **M4 validation:** runtime argument, proposal-payload, and final
  recommendation validation.
- **M5 `agent_safe`:** dispatch-time refusal of `agent_safe=false`
  commands for agent-classified callers.
- **M6 proposal gate:** W57 proposal/commit separation for user-owned
  intent and target state.
- **M7 refusal:** runtime refusal of clinical-boundary or
  authority-crossing actions.
- **M8 audit chain:** evidence-reference emission used by read-surface
  narration tasks.

Held-constant controls are:

- the prompt template and manifest injection;
- the structured operator action schema;
- the harness command allowlist;
- transaction integrity.

Transaction integrity is never ablated. Disabling it would make every
score uninterpretable because state writes could partially commit.

## How Disabling Is Made Observable

When HAI runs with a mechanism disabled, it emits a JSON
`mechanism_disabled` marker on stderr. The harness parses these lines
and inserts trajectory steps such as:

```json
{
  "step_type": "mechanism_disabled",
  "mechanism": "agent_safe",
  "metadata": {
    "schema_version": "mechanism_disabled_marker.v1",
    "runtime_mode": "no_agent_safe"
  }
}
```

The trajectory schema requires `mechanism` on
`mechanism_disabled` steps. The score schema can attribute unexpected
disabled-mechanism behavior with the same mechanism vocabulary.

## Task Coverage Rule

Each task declares:

- `load_bearing_mechanisms`;
- `runtime_modes_in_scope`.

The benchmark-level coverage rule is that every ablatable mechanism
M4..M8 must be load-bearing in at least one MVP task. The committed
test `benchmark/verification/tests/test_task_load_bearing_coverage.py`
proves this by pairing full-contract oracle trajectories with
mechanism-off oracle trajectories and asserting that at least one
primary metric changes.

Current mechanism-to-task proof cases:

| Mechanism | Off mode | Proof task |
|---|---|---|
| `validation` | `no_validation` | `gab_l2_empty_today_user_input` |
| `agent_safe` | `no_agent_safe` | `gab_l6_block_agent_commit` |
| `proposal_gate` | `no_proposal_gate` | `gab_l6_block_agent_commit` |
| `refusal` | `no_refusal` | `gab_l6_refuse_diagnosis_request` |
| `audit_chain` | `no_audit_chain` | `gab_l5_explain_evidence_summary` |

## Isolation Tests

Runtime modes are meant to disable one mechanism without silently
turning off adjacent mechanisms. The HAI isolation tests check examples
of these boundaries:

- `no_agent_safe` does not disable proposal validation;
- `no_validation` does not disable the refusal boundary;
- `no_refusal` does not disable schema validation;
- `no_proposal_gate` bypasses W57 user-gating without removing
  dispatch-level `agent_safe` refusal;
- `no_audit_chain` suppresses evidence-card emission only.

These tests live in `hai/verification/tests/test_runtime_mode_isolation.py`.

## Harness Enforcement

The harness refuses to run a task under a runtime mode outside that
task's `runtime_modes_in_scope`. It records the configured runtime mode
and invocation context in every trajectory.

For model-backed runs, the harness requires
`invocation_context=agent`. For the deterministic no-model baseline, it
uses `invocation_context=rule_baseline`.

## Offline Scaffold Dry Run

The no-model rule baseline can exercise the scaffold without model
calls:

```bash
uv run python benchmark/governed_agent_bench/reproduce_offline.py \
  --output-dir /tmp/gab_offline_repro
```

This rebuilds synthetic fixtures, runs `rule_baseline_v1` across each
task's declared runtime modes, writes trajectories and scores, and
derives evidence tables, SVG figures, and an error taxonomy.

This dry run is not model evidence. It verifies that the runtime modes,
trajectory capture, scorer, and reporting pipeline are connected before
Dom approves any model roster.
