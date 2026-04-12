# Health Lab canonical definition

Health Lab is the trust layer for agent-mediated personal health work over user-owned memory. In repo terms, it is a bounded contract and proof system that gives external agents truthful ways to retrieve scoped health evidence, produce inspectable artifacts, and write structured updates back safely. For the current reset slice, `health_model/` is the truthful implementation center and `health_agent_infra/` is a temporary compatibility wrapper namespace.

## Canonical three-part split

### 1. CLI / data plane / reporting layer
This layer owns contract discovery, bundle bootstrap, intake, scoped retrieval, validation entrypoints, replayable manifests, and generated artifacts. In current repo truth it is grounded in:

- `health_model/agent_contract_cli.py` (canonical)
- `health_agent_infra/agent_contract_cli.py` (temporary compatibility)
- `health_model/agent_bundle_cli.py` (canonical)
- `health_agent_infra/agent_bundle_cli.py` (temporary compatibility)
- `health_model/agent_voice_note_cli.py` (canonical)
- `health_agent_infra/agent_voice_note_cli.py` (temporary compatibility)
- `health_model/agent_submit_cli.py` (canonical)
- `health_agent_infra/agent_submit_cli.py` (temporary compatibility)
- `health_model/agent_context_cli.py` (canonical)
- `health_agent_infra/agent_context_cli.py` (temporary compatibility)
- `health_model/agent_retrieval_cli.py` (canonical)
- `health_agent_infra/agent_retrieval_cli.py` (temporary compatibility)
- `health_model/agent_memory_write_cli.py` (canonical)
- `health_agent_infra/agent_memory_write_cli.py` (temporary compatibility)
- `health_model/daily_snapshot.py` (canonical)
- `health_agent_infra/daily_snapshot.py` (temporary compatibility)
- `health_model/day_nutrition_brief.py` (canonical)
- `health_agent_infra/day_nutrition_brief.py` (temporary compatibility)

This layer does not own core cognition. It exposes bounded interfaces and produces inspectable artifacts.

### 2. Agent layer
This layer owns interpretation, synthesis, prioritisation, explanation, and recommendation generation. In current repo truth, agents operate externally to the repo's durable storage boundary, use the repo's reference payloads and artifact shapes, and interact through the bounded CLI surfaces documented in `README.md` and `STATUS.md`.

This layer must not be described as the same thing as the CLI/data plane/reporting layer, and it does not make Health Lab the durable private memory authority.

### 3. Policy / proof layer
This layer owns evidence-ref validation, scope checks, missingness and conflict handling, fail-closed rejection, non-mutation guarantees, and replayable proof bundles. In current repo truth it is grounded in these checked-in proof surfaces:

- `artifacts/public_demo/captured/`
- `artifacts/flagship_loop_proof/2026-04-09/`
- `artifacts/protocol_layer_proof/2026-04-11-writeback-judgment/`
- `artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition/`

This layer is the trust-enforcement boundary. It is not generic product marketing copy and it should stay tied to inspectable proof objects.

## Current flagship loop

The clearest shipped proof in this repo remains the CLI-first reference loop:

`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`

That loop is implemented canonically under `health_model/`, with `health_agent_infra/` preserved as a temporary compatibility namespace, backed by focused tests and checked-in proof artifacts, and should be read as the current flagship Health Lab slice.

## What Health Lab is not claiming

- It is not the durable private memory authority for user health data. Private memory remains user-owned and outside this repo and outside Health Lab.
- It is not already a hosted multi-user runtime, public SaaS product, or polished consumer app.
- It is not a claim that the CLI/data plane/reporting layer owns agent cognition.
- It is not a claim that local runtime outputs under `data/` are the canonical public proof object.
- It is not a claim that the whole repo has already been reorganised around the flagship loop.

## Legacy and adjacent repo surfaces

Legacy or adjacent directories remain in-tree, including `dashboard/`, `web/`, and `garmin/`. They should be treated as quarantined legacy or adjacent repo surfaces, not as the canonical current Health Lab product slice. In particular, Garmin-first web and dashboard flows are out of the flagship review path for this slice. Their presence should not redefine the three-part boundary above, and this doc does not claim they are removed or redesigned.

## Review path

For the clearest repo-visible review path, read this doc alongside:

- `README.md`
- `STATUS.md`
- `docs/health_lab_canonical_public_demo.md`
- `artifacts/public_demo/captured/`
- `artifacts/flagship_loop_proof/2026-04-09/`

This keeps the current project definition anchored to exact repo-visible files and proof surfaces rather than broader repo archaeology.
