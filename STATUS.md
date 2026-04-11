# Status

## Repo status

This repo currently presents a truthful public shell around one proved flagship Health Lab loop. The frozen canonical definition for this repo-visible slice lives at `docs/health_lab_canonical_definition.md`.

The current flagship loop is:

`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`

Canonical public-truth surfaces:
- walkthrough doc: `docs/health_lab_canonical_public_demo.md`
- checked-in public demo bundle: `artifacts/public_demo/captured/`
- audited flagship proof bundle: `artifacts/flagship_loop_proof/2026-04-09/`

The flagship loop is real, CLI-first, locally runnable, and backed by checked-in proof artifacts plus focused unittest coverage.

The current bounded writeback proof slice is `writeback.recommendation_judgment`, frozen under `artifacts/protocol_layer_proof/2026-04-11-writeback-judgment/` with success, wrong-scope rejection, missing-artifact rejection, and non-mutation evidence.

The current bounded closed-loop transition proof is `protocol_proof.recommendation_resolution_transition`, frozen under `artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/` with one recommendation shown as `pending_judgment` before writeback, `judged` after accepted writeback, visible in post-write feedback retrieval, plus a rejected non-mutating writeback replay.

## Architecture truth

- CLI / data plane / reporting layer: this repo defines bounded contracts, CLI surfaces, reporting entrypoints, and generated artifacts for the current flagship loop.
- Agent layer: an external agent performs retrieval, synthesis, recommendation generation, prioritisation, explanation, and writeback decisions against user-owned memory.
- Policy / proof layer: checked-in proof bundles and fail-closed enforcement own scope validation, rejection behavior, and non-mutation guarantees.
- Private memory layer: user-owned health memory lives outside this repo and outside Health Lab.

## What is proven now

- contract discovery via `health_model.agent_contract_cli`
- bundle initialization via `health_model.agent_bundle_cli`
- same-day voice-note submission via `health_model.agent_voice_note_cli`
- scoped context reads via `health_model.agent_context_cli`
- recommendation creation with fail-closed behavior via `health_model.agent_recommendation_cli`
- same-day recommendation judgment writeback with fail-closed non-mutation via `health_model.agent_memory_write_cli`
- one closed-loop recommendation resolution transition proof from `pending_judgment` to judged and feedback-visible state, with rejected non-mutation replay

## What this repo is not claiming

- not a clinical product or medical device
- not a hosted or multi-user product
- not a polished install flow for general users
- not the durable private memory authority for user health data
- not yet a repo fully reorganized around the flagship loop

## Repo-readiness audit note

Unresolved truths that still matter:
- Note: the repository directory is still named `garmin_lab` for historical reasons, while the current project framing is Health Lab.
- older Garmin, dashboard, web, and adjacent project surfaces remain in-tree and can still distract from the flagship proof path, so `dashboard/`, `web/`, and `garmin/` are explicitly constrained as legacy or adjacent surfaces rather than the canonical current slice
- the cleanest public review path is the checked-in demo and proof bundles, not the whole repo
- local runtime outputs under `data/` are not public-safe proof artifacts unless explicitly curated

## Current reviewer checklist

- [x] Root README points explicitly to the canonical demo and proof surfaces
- [x] `LICENSE`, `CONTRIBUTING.md`, and this `STATUS.md` exist
- [x] Proof-facing wording stays within current repo reality
- [x] Frozen flagship CLI smoke-test command is defined for CI
- [ ] Any repo directory rename and broader legacy-root wording cleanup remain pending beyond this bounded slice
