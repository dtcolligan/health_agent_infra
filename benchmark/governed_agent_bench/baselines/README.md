# Baselines

Baseline implementations live here once the scorer can grade recorded
trajectories.

Planned baseline families per [`/PAPER.md`](../../../PAPER.md)
"Active Decisions" D-10 (prompt held constant) and D-05 (Option B
empirical scope). The deployment-realistic prompt
(`../prompts/deployment_full_v1.md`) is held constant across every
condition; baselines vary `runtime_mode` and `model_class`, not the
prompt.

| `model_class` | Notes |
|---|---|
| `rule_baseline` | Deterministic router/refusal/command selector. No model call. |
| `local` | Local LM under `runtime_mode` ∈ {full_contract, no_validation, no_agent_safe, no_proposal_gate, no_refusal, no_audit_chain, no_runtime_enforcement}. |
| `cloud` | Cloud LM under same `runtime_mode` set. |
| `fine_tuned_local` | **Future work**, not in the preprint scope. |

The pre-reframe families "Local prompt-only model", "Cloud prompt-
only model", and "Fine-tuned local operator plus live manifest" are
retired — they referenced the prompt-axis ablation that the project
no longer varies.
