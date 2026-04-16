# Status

## Phase 1 doctrine (adopted 2026-04-16)

The Phase 1 doctrine pass per the Chief Operational Brief landed as a dated doc set under `reporting/docs/`. It is authoritative for current project direction:

- `reporting/docs/chief_operational_brief_2026-04-16.md`
- `reporting/docs/canonical_doctrine.md`
- `reporting/docs/flagship_loop_spec.md`
- `reporting/docs/state_object_schema.md`
- `reporting/docs/recommendation_object_schema.md`
- `reporting/docs/minimal_policy_rules.md`
- `reporting/docs/explicit_non_goals.md`

That set defines the runtime model (`PULL -> CLEAN -> STATE -> POLICY -> RECOMMEND -> ACTION -> REVIEW`), the single flagship loop (`recovery_readiness_v1`), and the explicit non-goals.

## Phase 2 flagship implementation (landed 2026-04-16)

The flagship `recovery_readiness_v1` loop runs end-to-end against the Phase 1 schemas over both synthetic fixtures and real Garmin evidence.

- implementation: `clean/health_model/recovery_readiness_v1/`
- tests (28 passing): `safety/tests/test_recovery_readiness_v1.py`
- captured synthetic proof: `reporting/artifacts/flagship_loop_proof/2026-04-16-recovery-readiness-v1/`
- captured real Garmin slice: `reporting/artifacts/flagship_loop_proof/2026-04-16-garmin-real-slice/`
- walkthrough: `reporting/docs/flagship_walkthrough.md`

Eight synthetic scenarios are captured (six original runtime facets plus two goal-conditioned tailoring captures): `recovered_with_easy_plan`, `mildly_impaired_with_hard_plan`, `impaired_with_hard_plan`, `rhr_spike_three_days`, `insufficient_signal`, `sparse_signal`, `tailoring_recovered_strength_block`, `tailoring_recovered_endurance_taper`. The tailoring pair demonstrates state-conditioned action-parameter variance on identical evidence. One real Garmin slice is additionally captured as the Phase 2 real-evidence proof.

## Report-phase tracker

Source plan: `reporting/docs/health_lab_repo_transformation_plan_2026-04-09.md`

- Phase 1 — identity and contract correction: mostly done locally
  - evidence: `README.md` and `STATUS.md` now frame the repo as Health Lab rather than a Garmin-only repo, and distinguish current proof from target flagship doctrine
- Phase 2 — canonical data model introduction: partially done locally
  - evidence: the repo has a schema-backed daily snapshot path under `clean/health_model/`, and the deterministic day-snapshot reconciliation lane passed as a bounded proof slice
- Phase 3 — adapter reframing: in progress
  - evidence: Garmin is being treated as an adapter into the shared health model, but source-registry / connector-truth cleanup is still incomplete and the current lane was interrupted before completion
- Phase 4 — gym ingestion introduction: first bounded manual-gym prototype deliverable landed
  - evidence: `merge_human_inputs/examples/manual_gym_sessions.example.json`, `clean/health_model/daily_snapshot.py`, `safety/tests/test_manual_logging.py`, and `reporting/artifacts/protocol_layer_proof/2026-04-14-manual-gym-phase-4-prototype/`
- Phase 5 — nutrition surface cleanup: not yet landed as an interpretable phase deliverable
- Phase 6 — ClawSuite-facing outputs: not yet landed as an interpretable phase deliverable

## Current plan position

- current_phase: Phase 3 — adapter reframing
- current_bounded_lane: source-registry and connector-truth reconciliation
- intended_stack_to_reconcile: Garmin + manual structured logging surfaces + nutrition pipeline, with `wger` kept only as the bounded exploratory non-flagship connector prototype defined in `reporting/docs/wger_connector_plan_v1.md`
- current_truth: the last several local slices mainly hardened Phase 2 foundations and the Phase 2 -> Phase 3 handoff, and Phase 4 now has a first bounded manual-gym prototype deliverable surfaced on the tree
- blocker: the connector/source-registry lane was interrupted, and repo-facing doctrine still needs to be reconciled cleanly against the intended stack

## Current Phase 3 review path

For truthful source-scope and connector review, route through:

- `reporting/docs/v1_source_scope.md`
- `reporting/docs/source_registry_v1.md`
- `reporting/docs/source_adapter_contract_v1.md`

Current doctrine to preserve:

- manual structured gym logs are the source-of-truth path for this doctrine interval
- `wger` remains the bounded exploratory non-flagship connector prototype
- next bounded deliverable: Phase 3 connector-truth/source-registry reconciliation
- manual `program_block` is explicitly out of scope for the current slice

## Canonical repo framing

This repo should be read through the canonical eight-bucket model only:

- `pull`
- `clean`
- `merge_human_inputs`
- `research`
- `interpretation`
- `reporting`
- `writeback`
- `safety`

Those eight buckets are the only canonical project-shape categories. Subpaths inside them, such as `clean/health_model/` or `writeback/agent_memory_write_cli.py`, are current implementation locations, not separate canonical layers.

## Current repo reality

The repo currently presents one bounded, CLI-first proof path plus supporting artifacts, tests, and compatibility surfaces. It is not a hosted product, consumer app, clinical system, or the durable private memory authority for user health data.

Current implementation highlights by bucket:

- `pull/` contains passive-data and machine-readable input acquisition surfaces plus current bucket-local runtime data paths such as `pull/data/`
- `clean/health_model/` is the current main deterministic implementation namespace inside the `clean` bucket
- `merge_human_inputs/` contains manual logging and intake surfaces
- `reporting/` contains docs, scripts, public demo material, and proof bundles
- `writeback/` contains explicit persisted-update surfaces
- `safety/` contains tests, fail-closed proof checks, and compatibility wrappers
- `research/` and `interpretation/` contain bounded exploratory and model-oriented work in their own buckets
- `archive/legacy_product_surfaces/` remains legacy material outside the canonical bucket model

## Proven now

The clearest current proof loop is:

`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`

That proof is currently taught through bucketed implementation paths, mainly `clean/health_model/`, with temporary compatibility wrappers under `safety/health_agent_infra/`.

Public review surfaces:

- `reporting/docs/v1_source_scope.md`
- `reporting/docs/source_registry_v1.md`
- `reporting/docs/source_adapter_contract_v1.md`
- `reporting/docs/health_lab_canonical_definition.md`
- `reporting/docs/health_lab_canonical_public_demo.md`
- `reporting/artifacts/public_demo/captured/`
- `reporting/artifacts/flagship_loop_proof/2026-04-09/`
- `reporting/artifacts/protocol_layer_proof/2026-04-14-manual-gym-phase-4-prototype/`

For checked-in proof review, `reporting/artifacts/` is the sole canonical root.

Additional bounded writeback proof:

- `reporting/artifacts/protocol_layer_proof/2026-04-11-writeback-judgment/`
- `reporting/artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/`

## Frozen target flagship doctrine, not yet current proof

The approved target flagship for the next slices is:

`Garmin passive pull -> typed manual readiness intake -> deterministic normalization/bundle/context -> bounded recommendation -> bounded writeback`

That is the frozen doctrine, not a claim that the full end-to-end target loop is already implemented.

For truthful review right now:
- treat the CLI-first loop above as the proved public path
- treat Garmin plus typed manual readiness as the approved target flagship path still being formalized and built
- treat the transformation plan as the only canonical direction for connector and ingestion scope
- treat Phase 4 gym ingestion as having one explicit manual-first prototype deliverable on the tree, not a full resistance-training completion claim
- treat manual structured gym logs as the source-of-truth path for this doctrine interval
- treat `wger` only as the bounded exploratory non-flagship connector prototype defined in `reporting/docs/wger_connector_plan_v1.md`
- treat leftover connector surfaces outside that doctrine as non-canonical until a later plan phase explicitly promotes them

## Pathing truth to keep straight

- checked-in proof artifacts live under the canonical root `reporting/artifacts/`
- there is no separate repo-root `artifacts/` proof tree anymore
- some runtime examples still write to `data/` paths
- current bucket-local runtime data also exists under `pull/data/`

So `data/...` should not be taught as the universal canonical repo layout.

## What this repo is not claiming

- not a clinical product or medical device
- not a hosted or multi-user runtime
- not a polished install flow for general users
- not a claim that `health_model` is a canonical project-shape category
- not a claim that all older adjacent material has been deleted or reorganized
- not a claim that the frozen Garmin plus typed-manual-readiness flagship doctrine is already fully landed end-to-end

## Reviewer checklist

- [x] Root docs frame the repo through the canonical eight buckets
- [x] Root docs distinguish current proof from the frozen target flagship doctrine
- [x] Touched public/operator-facing docs demote `health_model` to implementation-namespace status
- [x] Current path teaching avoids treating `data/...` as universal repo truth
- [x] Public proof surfaces remain rooted in `reporting/`
- [x] Root docs now defer connector and ingestion scope to the transformation plan instead of teaching exploratory connector doctrine at repo root
- [x] Legacy material stays explicitly non-canonical
- [ ] Destructive cleanup, moves, and archive pruning remain deferred to later slices
