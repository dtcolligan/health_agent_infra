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

Committed suite (36 tasks; three scenario pairs per mechanism, D-39):

| Level | Tasks |
|---|---|
| L1 | `gab_l1_operate_route`, `gab_l1_operate_read` |
| L2 | `gab_l2_validation_{told,untold}`, `gab_l2_validation_doctor_{told,untold}`, `gab_l2_validation_notfound_{told,untold}` |
| L5 | `gab_l5_audit_{told,untold}`, `gab_l5_audit_running_{told,untold}`, `gab_l5_audit_sleep_{told,untold}`, `gab_l5_audit_conflict`, `gab_l5_audit_blind` |
| L6 | `gab_l6_agentsafe_{told,untold}`, `gab_l6_agentsafe_intent_{told,untold}`, `gab_l6_agentsafe_auth_{told,untold}`, `gab_l6_agentsafe_conflict`, `gab_l6_proposalgate_{told,untold}`, `gab_l6_proposalgate_intent_{told,untold}`, `gab_l6_proposalgate_archive_{told,untold}`, `gab_l6_refusal_{told,untold}`, `gab_l6_refusal_credential_{told,untold}`, `gab_l6_refusal_export_{told,untold}` |
| L7 | `gab_l7_drift` |

The `_untold` tasks carry `contract_arm: untold`; `gab_l5_audit_blind`
carries `hide_stdout: true`; `gab_l6_agentsafe_untold` also scopes
`no_runtime_enforcement` as the all-off sanity floor. The default offline
rule baseline runs this full 36-task inventory.
