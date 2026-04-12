# Status

## Repo status

This repo currently presents a truthful public shell around one proved flagship Health Lab slice. In public-facing terms, `health_agent_infra` is the Health Lab infrastructure repository: the deterministic `PULL` plus `CLEAN` layer for agent-mediated personal health work over user-owned memory, with later human-input merge and model-owned interpretation/reporting outside the infra boundary. It is implemented here as a bounded contract-and-proof system rather than a hosted product.

The frozen canonical definition for this repo-visible slice lives at `docs/health_lab_canonical_definition.md`.

The current flagship loop is:

`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`

Canonical public-truth surfaces:
- walkthrough doc: `docs/health_lab_canonical_public_demo.md`
- checked-in public demo bundle: `artifacts/public_demo/captured/`
- audited flagship proof bundle: `artifacts/flagship_loop_proof/2026-04-09/`

The flagship loop is real, CLI-first, locally runnable, and backed by checked-in proof artifacts plus focused unittest coverage. It should be read as the current flagship proof path, not as a claim that this repo already provides a polished consumer app, hosted runtime, or durable private memory layer.

The current bounded writeback proof slice is `writeback.recommendation_judgment`, frozen under `artifacts/protocol_layer_proof/2026-04-11-writeback-judgment/` with success, wrong-scope rejection, missing-artifact rejection, and non-mutation evidence.

The current bounded closed-loop transition proof is `protocol_proof.recommendation_resolution_transition`, frozen under `artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/` with one recommendation shown as `pending_judgment` before writeback, `judged` after accepted writeback, visible in post-write feedback retrieval, plus a rejected non-mutating writeback replay.

## Architecture truth

- PULL layer: this repo defines deterministic connectors, intake surfaces, and scoped acquisition paths for passive-data and machine-readable health inputs.
- CLEAN layer: this repo defines deterministic normalization, validation, bundle assembly, retrieval shaping, and interpretation-ready dataset preparation.
- Human-input merge: subjective user input is a separate lane that should merge after PULL/CLEAN and before interpretation.
- Interpretation + report layers: an external model/agent performs synthesis, recommendation generation, explanation, guidance structure, and final reporting against the merged context.
- Writeback layer: bounded persisted memory/state updates live behind explicit write surfaces.
- Policy / proof layer: checked-in proof bundles and fail-closed enforcement own scope validation, rejection behavior, grounding, and non-mutation guarantees.
- Private memory layer: user-owned health memory lives outside this repo and outside Health Lab.

## What is proven now

- contract discovery via `health_model.agent_contract_cli`, with `health_agent_infra.agent_contract_cli` retained temporarily for compatibility
- bundle initialization via `health_model.agent_bundle_cli`, with `health_agent_infra.agent_bundle_cli` retained temporarily for compatibility
- same-day voice-note submission via `health_model.agent_voice_note_cli`, with `health_agent_infra.agent_voice_note_cli` retained temporarily for compatibility
- slice-1 human-input migration landed under `merge_human_inputs/`, with `health_model.manual_logging`, `health_model.voice_note_intake`, and `bot.*` preserved as compatibility wrappers
- scoped context reads via `health_model.agent_context_cli`, with `health_agent_infra.agent_context_cli` retained temporarily for compatibility
- recommendation creation with fail-closed behavior via `health_model.agent_recommendation_cli`, with `health_agent_infra.agent_recommendation_cli` retained temporarily for compatibility
- same-day recommendation judgment writeback with fail-closed non-mutation via `health_model.agent_memory_write_cli`, with `health_agent_infra.agent_memory_write_cli` retained temporarily for compatibility
- one closed-loop recommendation resolution transition proof from `pending_judgment` to judged and feedback-visible state, with rejected non-mutation replay

## What this repo is not claiming

- not a clinical product or medical device
- not a hosted or multi-user product
- not a polished install flow for general users
- not the durable private memory authority for user health data
- not yet a repo fully reorganized around the flagship loop

## Repo-readiness audit note

Unresolved truths that still matter:
- older Garmin, dashboard, web, and adjacent project surfaces have been moved under `archive/legacy_product_surfaces/`, which reduces root-level review noise but does not make those archived surfaces part of the canonical current slice
- the cleanest public review path is the checked-in demo and proof bundles, not the whole repo
- local runtime outputs under `data/` are not public-safe proof artifacts unless explicitly curated

## Current reviewer checklist

- [x] Root README points explicitly to the canonical demo and proof surfaces
- [x] `LICENSE`, `CONTRIBUTING.md`, and this `STATUS.md` exist
- [x] Proof-facing wording stays within current repo reality
- [x] Frozen flagship CLI smoke-test command is defined for CI
- [x] Root-level archive move for `dashboard/`, `web/`, and `garmin/` completed under `archive/legacy_product_surfaces/`
- [ ] Any broader legacy-root wording cleanup beyond this bounded slice remains pending
