# Health Lab canonical definition

Health Lab should be described through the repo's canonical eight-bucket model only:

- `pull`
- `clean`
- `merge_human_inputs`
- `research`
- `interpretation`
- `reporting`
- `writeback`
- `safety`

These eight buckets are the only canonical project-shape categories.

Implementation namespaces inside those buckets may still be important and should be described truthfully, but they do not become extra canonical layers. For example, `clean/health_model/` is a current implementation namespace inside `clean`, and `writeback/agent_memory_write_cli.py` is a current implementation location inside `writeback`.

## Bucket definitions

### `pull`
Deterministic acquisition of passive-data and other machine-readable inputs.

### `clean`
Deterministic normalization, validation, bundle assembly, retrieval shaping, and preparation of interpretation-ready artifacts.

### `merge_human_inputs`
User notes, voice-note intake, manual logs, typed manual readiness intake, and related merge surfaces that sit between deterministic infra and later interpretation.

### `research`
Bounded exploratory work, notebooks, and research material.

### `interpretation`
Model-oriented interpretation and synthesis work.

### `reporting`
Docs, review surfaces, scripts, proofs, and public/operator-facing artifacts.

### `writeback`
Explicit persisted state or memory update entrypoints.

### `safety`
Tests, compatibility wrappers, fail-closed checks, and trust-boundary enforcement.

## Current repo truth

The repo currently exposes a narrow, CLI-first proof path plus supporting docs, tests, proof bundles, and compatibility surfaces. It is not a hosted product, consumer app, clinical service, or the durable private memory authority for user health data.

Current implementation locations worth naming truthfully:

- `clean/health_model/` is the main present implementation namespace for much of the deterministic CLI-first path
- `safety/health_agent_infra/` contains temporary compatibility wrappers and safety-oriented surfaces
- `writeback/agent_memory_write_cli.py` is the explicit writeback entrypoint
- `merge_human_inputs/` contains migrated human-input surfaces
- `reporting/` contains the reviewed proof and demo surfaces

Those path references explain current repo reality. They do not override the bucket model.

## Current public proof path

The clearest shipped proof is the `recovery_readiness_v1` flagship loop (delivered 2026-04-16):

`PULL -> CLEAN -> STATE -> POLICY -> RECOMMEND -> ACTION -> REVIEW`

Implemented in `clean/health_model/recovery_readiness_v1/`. Runs end-to-end over both synthetic fixtures and a committed real Garmin CSV export.

Key flagship review surfaces:

- `reporting/docs/flagship_walkthrough.md`
- `reporting/artifacts/flagship_loop_proof/2026-04-16-recovery-readiness-v1/` (synthetic, 8 scenarios)
- `reporting/artifacts/flagship_loop_proof/2026-04-16-garmin-real-slice/` (real Garmin CSV)

The older CLI-first loop (`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`) remains in the tree as compatibility. Review surfaces for that older lineage:

- `reporting/docs/health_lab_canonical_public_demo.md`
- `reporting/artifacts/public_demo/captured/`
- `reporting/artifacts/flagship_loop_proof/2026-04-09/`
- `reporting/artifacts/protocol_layer_proof/2026-04-11-writeback-judgment/`
- `reporting/artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/`

## Flagship path, delivered 2026-04-16

The narrow flagship path `Garmin passive pull -> typed manual readiness intake -> deterministic normalization -> typed state -> policy -> bounded recommendation -> bounded local writeback -> review` was delivered 2026-04-16 as `recovery_readiness_v1`. Proof bundles live at `reporting/artifacts/flagship_loop_proof/2026-04-16-recovery-readiness-v1/` (synthetic, 8 scenarios) and `reporting/artifacts/flagship_loop_proof/2026-04-16-garmin-real-slice/` (real Garmin CSV).

The older CLI-first lineage (`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`) remains present as compatibility, not as current flagship proof.

Classification for this interval:
- Garmin is the passive-data anchor for the delivered flagship path (via the thin `pull/garmin/recovery_readiness_adapter.py`)
- typed manual readiness intake is the human-input anchor for the delivered flagship path (via the manual-readiness dict shape consumed by `clean_inputs`)
- manual structured gym logs remain the source-of-truth path for resistance training, distinct from the flagship loop
- `pull/sources/wger/` remains only a bounded exploratory non-flagship connector prototype for later convergence into Health Lab canonical gym objects
- leftover connector surfaces outside that doctrine are non-canonical unless later promoted by the plan

## Bridge and exploratory connectors

Some connector-facing work exists or may be named in repo docs because it is useful bounded platform work.

That includes surfaces such as Cronometer export support and the bounded `pull/sources/wger/` prototype.

Those surfaces should be described explicitly as bridge/reference or bounded exploratory connector work when that is the truth. They should not be described as the current flagship proof path, and leftover connector residue outside this doctrine should not be allowed to define repo-facing truth.

## What Health Lab is not claiming

- It is not a claim that `health_model` is a canonical project-shape category.
- It is not a claim that local runtime outputs under `data/` are the universal canonical repo layout.
- It is not already a hosted multi-user runtime, public SaaS product, or polished consumer app.
- It is not the durable private memory authority for user health data.
- It is not a claim that all legacy or adjacent repo surfaces have already been removed or redesigned.
- It is not a claim that the frozen Garmin plus typed-manual-readiness flagship path is already fully shipped end-to-end.

## Legacy and adjacent surfaces

Legacy or adjacent product surfaces remain under `archive/legacy_product_surfaces/`. They are not part of the canonical current project shape and should not be described as such. Their presence is repo history, not a reason to add more canonical layers beyond the eight buckets.

## Review path

For the clearest repo-visible review path, read this doc alongside:

- `README.md`
- `STATUS.md`
- `CONTRIBUTING.md`
- `reporting/docs/health_lab_canonical_public_demo.md`
- `reporting/artifacts/public_demo/captured/`
- `reporting/artifacts/flagship_loop_proof/2026-04-09/`
