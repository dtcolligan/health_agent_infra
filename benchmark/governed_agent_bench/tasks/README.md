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

Committed suite (**51 tasks**). The count is derived from the reviewed
inventory in `../../verification/tests/test_task_seed_set.py`; update that map
when adding a task so only one number moves.

| Level | Count | Tasks |
|---|---|---|
| L1 | 2 | `gab_l1_operate_route`, `gab_l1_operate_read` |
| L2 | 4 | `gab_l2_validation_{told,untold}`, `gab_l2_validation_notfound_{told,untold}` |
| L5 | 8 | `gab_l5_audit_{told,untold}`, `gab_l5_audit_running_{told,untold}`, `gab_l5_audit_sleep_{told,untold}`, `gab_l5_audit_conflict`, `gab_l5_audit_blind` |
| L6 | 36 | `gab_l6_agentsafe_{told,untold}`, `gab_l6_agentsafe_intent_{told,untold}`, `gab_l6_agentsafe_auth_{told,untold}`, `gab_l6_agentsafe_authorized_{told,untold}`, `gab_l6_agentsafe_assumed_{told,untold}`, `gab_l6_agentsafe_archivetarget_{told,untold}`, `gab_l6_agentsafe_archiveintent_{told,untold}`, `gab_l6_agentsafe_setactivetarget_{told,untold}`, `gab_l6_agentsafe_setactiveintent_{told,untold}`, `gab_l6_agentsafe_conflict`, `gab_l6_proposalgate_{told,untold}`, `gab_l6_proposalgate_intent_{told,untold}`, `gab_l6_proposalgate_archive_{told,untold}`, `gab_l6_refusal_{told,untold}`, `gab_l6_refusal_credential_{told,untold}`, `gab_l6_refusal_export_{told,untold}`, `gab_l6_refusal_diagnose_{told,untold}`, `gab_l6_refusal_dose_{told,untold}`, `gab_l6_refusal_conflict` |
| L7 | 1 | `gab_l7_drift` |

Two later additions are why earlier drafts said 28, 36 or 39: a concentration
pass added the five clinical-refusal tasks (`diagnose`, `dose`, and a
goal-conflict), and on 2026-07-17 the powered-run breadth pass added twelve
mutation-gate tasks (`archivetarget`, `archiveintent`, `setactivetarget`,
`setactiveintent`, `authorized`, `assumed`, each told and untold) so a model's
rate is characterised over the whole boundary rather than one phrasing.

**The paid within-family run used a 16-task subset of L6**, the eight
mutation-gate decisions in both arms: `agentsafe` and `agentsafe_intent` (the
commit boundary), `archivetarget` and `archiveintent`, `setactivetarget` and
`setactiveintent`, and the two commit framings. Four repeats a cell.

The `_untold` tasks carry `contract_arm: untold`; `gab_l5_audit_blind`
carries `hide_stdout: true`; `gab_l6_agentsafe_untold` and `gab_l6_proposalgate_untold` scope
`no_runtime_enforcement` as the all-off sanity floor (canary carriers). The default offline
rule baseline runs the full inventory.
