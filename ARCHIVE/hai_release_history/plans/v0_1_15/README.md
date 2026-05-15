# v0.1.15 cycle - frozen post-ship entry point

**Status:** shipped and published on 2026-05-03. v0.1.15 was the
external-user package cycle; v0.1.15.1 later hotfixed Linux
keyring fall-through without changing schema.

**Tier:** substantive. D14 plan audit settled at round 4 after the
Phase 0 F-PHASE0-01 revision; D15 implementation review settled at
round 3 with one nit-class note. The cycle is closed. Do not use this
directory as an open implementation checklist.

## What shipped

- W-GYM-SETID: `gym_set.set_id` includes exercise slug; migration 024
  rewrites old-format ids while preserving correction rows.
- F-PV14-01: CSV fixture pulls are default-denied against canonical
  state unless the caller opts in or uses a demo/non-canonical target.
- W-A: `hai intake gaps` emits the presence block, partial-day signal,
  and nutrition target-status enum.
- W-C: `hai target nutrition` writes four atomic macro target rows
  over the existing `target` table; migration 025 extends nutrition
  target types with `carbs_g` and `fat_g`.
- W-D arm-1: partial-day/no-target nutrition suppresses to
  `nutrition_status='insufficient_data'`.
- W-E: `merge-human-inputs` consumes the W-A presence block for
  recap-vs-forward-march framing.

## Read in order

1. `RELEASE_PROOF.md` - ship proof, gates, and workstream closure.
2. `REPORT.md` - post-ship narrative.
3. `PLAN.md` - final scoped plan and acceptance criteria.
4. `audit_findings.md` - Phase 0 findings, especially F-PHASE0-01.
5. `codex_plan_audit_round_4_response.md` and
   `codex_plan_audit_round_4_response_response.md` - final D14 close.
6. `codex_implementation_review_round_3_response.md` - final D15 IR
   close.

Earlier prompts and response files remain provenance. They are not
current instructions.

## What moved forward

- v0.1.16 owns empirical fixes from the recorded foreign-user session
  against the published package, plus the `hai explain` foreign-user
  pass.
- v0.1.17 owns maintainability and eval consolidation work that was
  deliberately removed from v0.1.15 scope.

For current shipped truth, start at
`reporting/docs/current_system_state.md`.
