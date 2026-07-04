# Tasks

Tasks are grouped by benchmark level. Each task must validate against
`../schema/task.schema.json`.

Every task is a labelled cell of the per-mechanism 2×2, crossing the
contract-in-prompt axis (`contract_arm` told/untold) with the
runtime-enforcement axis (`runtime_mode` on/off), plus the operate-floor,
goal-conflict, blind-observation, and drift anchors.

- L1 operate floor: can the agent drive the contract at all.
- L2 validation (M4): recovery / `USER_INPUT` handling.
- L5 audit (M8): faithful use of `hai explain` evidence.
- L6 governance/refusal (M5/M6/M7): user-gated commits and the
  clinical boundary.
- L7 drift: stale manifest / changed command surface.

Committed suite (16 tasks):

| Level | Tasks |
|---|---|
| L1 | `gab_l1_operate_route`, `gab_l1_operate_read` |
| L2 | `gab_l2_validation_told`, `gab_l2_validation_untold` |
| L5 | `gab_l5_audit_told`, `gab_l5_audit_untold`, `gab_l5_audit_conflict`, `gab_l5_audit_blind` |
| L6 | `gab_l6_agentsafe_told`, `gab_l6_agentsafe_untold`, `gab_l6_agentsafe_conflict`, `gab_l6_proposalgate_told`, `gab_l6_proposalgate_untold`, `gab_l6_refusal_told`, `gab_l6_refusal_untold` |
| L7 | `gab_l7_drift` |

The `_untold` tasks carry `contract_arm: untold`; `gab_l5_audit_blind`
carries `hide_stdout: true`; `gab_l6_agentsafe_untold` also scopes
`no_runtime_enforcement` as the all-off sanity floor. The default offline
rule baseline runs this full 16-task inventory.
