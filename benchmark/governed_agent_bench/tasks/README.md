# Tasks

Tasks are grouped by benchmark level. Each task must validate against
`../schema/task.schema.json`.

Preprint task-suite target:

- L1 routing tasks: natural-language intent to valid `hai` command.
- L2 recovery tasks: setup failure or `USER_INPUT` handling.
- L5 narration tasks: faithful use of `hai today` / `hai explain`.
- L6 governance/refusal tasks: forbidden commands and clinical-boundary
  pressure.
- L7 drift tasks: stale manifest or changed command surface.

Committed preprint seed set:

| Level | Tasks |
|---|---|
| L1 | `gab_l1_capabilities_route`, `gab_l1_doctor_status_route`, `gab_l1_explain_route`, `gab_l1_today_json_route` |
| L2 | `gab_l2_empty_today_user_input`, `gab_l2_governance_intent_list`, `gab_l2_governance_pending_list`, `gab_l2_recover_user_input` |
| L5 | `gab_l5_audit_card_reference`, `gab_l5_explain_evidence_summary`, `gab_l5_explain_recovery_audit`, `gab_l5_today_audit_summary`, `gab_l5_today_faithful_summary` |
| L6 | `gab_l6_block_agent_commit`, `gab_l6_block_agent_intent_commit`, `gab_l6_block_agent_target_commit`, `gab_l6_block_commit_under_no_runtime`, `gab_l6_block_dual_commit`, `gab_l6_block_intent_proposal_commit`, `gab_l6_block_proposal_commit`, `gab_l6_refuse_credential_request`, `gab_l6_refuse_diagnosis_request`, `gab_l6_refuse_forbidden_export`, `gab_l6_refuse_under_no_runtime`, `gab_l6_refuse_unsafe_protocol` |
| L7 | `gab_l7_stale_capabilities_drift`, `gab_l7_stale_missing_weekly_command`, `gab_l7_stale_v1_manifest_shape` |

The default offline rule baseline runs this full 28-task inventory.
