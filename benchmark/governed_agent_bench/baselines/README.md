# Baselines

Baseline implementations live here once the scorer can grade recorded
trajectories.

Planned baseline families (round-2; see
`../../research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`
and `../../project/DECISIONS.md` D-PROJ-013..017). The deployment-
realistic prompt (`prompts/deployment_full_v1.md`) is held constant
across every condition; baselines vary `runtime_mode` and
`model_class`, not the prompt.

| `model_class` | Notes |
|---|---|
| `rule_baseline` | Deterministic router/refusal/command selector. No model call. |
| `local` | Local LM under `runtime_mode` ∈ {full_contract, no_validation, no_agent_safe, no_proposal_gate, no_refusal, no_audit_chain, no_runtime_enforcement}. |
| `cloud` | Cloud LM under same `runtime_mode` set. |
| `fine_tuned_local` | **Future work**, not part of the workshop floor. |

The pre-reframe families "Local prompt-only model", "Cloud prompt-
only model", and "Fine-tuned local operator plus live manifest" are
retired — they referenced the prompt-axis ablation that the project
no longer varies.
