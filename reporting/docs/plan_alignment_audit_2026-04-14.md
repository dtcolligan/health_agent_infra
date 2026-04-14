# Health Lab plan-alignment audit

Date: 2026-04-14
Source of truth: `reporting/docs/health_lab_repo_transformation_plan_2026-04-09.md`

## Hard rule

This repo should be operated against the transformation plan above.
If the live repo contains surfaces that are not helping that plan, those surfaces are drift, not doctrine.

## Current phase position

- Phase 1 — identity and contract correction: partly landed
- Phase 2 — canonical data model introduction: partly landed
- Phase 3 — adapter reframing: active but not cleanly aligned
- Phase 4 — gym ingestion introduction: not yet landed as a clean phase deliverable
- Phase 5 — nutrition surface cleanup: not yet landed as a clean phase deliverable
- Phase 6 — ClawSuite-facing outputs: not yet landed as a clean phase deliverable

Blunt truth: the recent local work mostly hardened Phase 2 and the handoff into Phase 3. It did **not** cleanly advance the repo through the later MVP phases in an interpretable way.

## What already aligns with the plan

1. The repo now reads primarily through bucketed top-level current-work directories:
   - `pull/`
   - `clean/`
   - `merge_human_inputs/`
   - `research/`
   - `interpretation/`
   - `reporting/`
   - `safety/`
   - `writeback/`
2. Repo-root `bot/` has been removed as the live current-work package.
3. Repo-root `health_model/` has been removed as a fake top-level current-work layer.
4. There is a real daily-snapshot path under `clean/health_model/`, which is at least directionally consistent with Phase 2.
5. The repo now has one checked-in proof root under `reporting/artifacts/`.

## Current plan drift

These are the main mismatches between the repo and the plan.

### Drift A — connector exploration has leaked into repo-facing truth
The plan says the repo should move toward a Health Lab product with Garmin as one adapter, manual gym ingestion, nutrition as a first-class pillar, and a unified health model.

Current repo drift included:
- `pull/hevy/`
- `reporting/artifacts/protocol_layer_proof/2026-04-12-hevy-api-viability/`
- connector-specific proof material that can dominate the repo story if it is not clearly subordinated to the plan

Rule from now on:
- connectors not explicitly needed by the plan must not be taught as the live product direction
- per `reporting/docs/wger_connector_plan_v1.md`, `wger` may remain only as a bounded exploratory non-flagship connector prototype while manual structured gym logs remain the source-of-truth path for this doctrine interval
- exploratory connectors outside that doctrine should be archived, demoted, or clearly marked non-canonical

### Drift B — repo status has been explaining local proof lanes instead of the phased plan
The user needs to know where the repo stands in the report phases, not just which local reconciliation slice passed.

Rule from now on:
- status must lead with phase position
- each active slice must name which phase it serves
- work that does not clearly serve a phase should be treated as suspect

### Drift C — gym and nutrition are still not clean first-class pillars
The plan explicitly wants:
- manual gym logging as the first non-Garmin ingestion path
- nutrition as a first-class pillar rather than a sidecar

Current truth:
- manual logging surfaces exist under `merge_human_inputs/`
- but the repo story still overweights connector/proof drift rather than clean Phase 4 and Phase 5 deliverables

### Drift D — too much repo truth is still expressed through proof residue rather than clean product structure
The plan wants a repo that reads like a coherent Health Lab system.
A large amount of current readability still depends on historical proof bundles and compatibility surfaces rather than a clean product-facing phase structure.

## Keep / cut / defer guidance

### Keep
- bucket-native current-work layout
- Garmin as one input adapter
- manual logging under `merge_human_inputs/`
- daily health model work under `clean/health_model/`
- canonical checked-in proof root under `reporting/artifacts/`
- `wger` only in the bounded exploratory role defined by `reporting/docs/wger_connector_plan_v1.md`

### Cut or demote
- any connector or proof surface that implies a live direction not supported by the transformation plan
- any repo-facing teaching that makes removed or leftover connector exploration look like the current MVP path
- status language that substitutes local proof-lane updates for phase tracking

### Defer
- broader archive cleanup not needed for immediate interpretability
- deeper refactors that do not clearly advance the current report phase

## Immediate next corrective move

Use the transformation plan as the only operating law and perform one bounded repo-alignment slice:
1. remove or demote non-plan connector teaching from repo-facing docs/status
2. label exploratory connector surfaces as non-canonical where they remain
3. restate the current phase and exact next phase deliverable in root status
4. continue only with slices that obviously advance the plan

## Acceptance test for the realignment

A new reader should be able to answer all of these from the repo itself:
- what phase of the transformation plan is the repo currently in?
- what has actually been completed?
- what is the next planned deliverable?
- which surfaces are canonical product direction versus exploratory residue?
