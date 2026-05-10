# Tasks

Tasks are grouped by benchmark level. Each task must validate against
`../schema/task.schema.json`.

Initial MVP target:

- L1 routing tasks: natural-language intent to valid `hai` command.
- L2 recovery tasks: setup failure or `USER_INPUT` handling.
- L5 narration tasks: faithful use of `hai today` / `hai explain`.
- L6 governance/refusal tasks: forbidden commands and clinical-boundary
  pressure.
- L7 drift tasks: stale manifest or changed command surface.

Committed MVP seed set:

| Level | Tasks |
|---|---|
| L1 | `gab_l1_doctor_status_route`, `gab_l1_today_json_route` |
| L2 | `gab_l2_empty_today_user_input`, `gab_l2_governance_pending_list` |
| L5 | `gab_l5_today_faithful_summary`, `gab_l5_explain_evidence_summary` |
| L6 | `gab_l6_refuse_diagnosis_request`, `gab_l6_block_agent_commit` |
| L7 | `gab_l7_stale_missing_weekly_command`, `gab_l7_stale_v1_manifest_shape` |
