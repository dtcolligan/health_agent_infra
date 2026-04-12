# Health Lab memory write contract v1

Date: 2026-04-11

## Purpose

This contract defines bounded writeback protocols an external agent may use to capture same-day recommendation judgment and promote one already-written judgment into one scoped recommendation-resolution locator transition inside the user-owned memory layer.

Health Lab remains the protocol, CLI, and proof surface only. It does not host the private memory layer.

## Architecture boundary

- Private health memory remains external to Health Lab.
- Health Lab publishes protocol discovery, request semantics, response envelopes, and proof artifacts.
- These slices write one scoped recommendation judgment artifact and one scoped locator transition only.
- These slices must not broaden into hosted memory, embedded coaching, analytics expansion, recommendation rewriting, or cognition ownership.

## Discovery surface

Machine-readable discovery is published by `python3 -m health_model.agent_contract_cli describe` (`health_agent_infra.agent_contract_cli` remains temporarily compatible).

## Supported writeback operations

### `writeback.recommendation_judgment`
- Purpose: write one same-day `recommendation_judgment` artifact grounded in one accepted `agent_recommendation` artifact.
- Current implementation status: proof-complete in v1.
- Required fields: `user_id`, `date`, `recommendation_artifact_path`, `recommendation_artifact_id`, `judgment_id`, `judgment_label`, `action_taken`, `why`, `written_at`, `request_id`, `requested_at`.
- Optional fields: `caveat`, `time_cost_note`, `friction_points`, `gym_note`.
- Accepted `judgment_label` values: `useful`, `obvious`, `wrong`, `ignored`.
- Semantics:
  - validate `request_id` as a non-empty string and `requested_at` as an ISO 8601 datetime with timezone information
  - validate `written_at` as an ISO 8601 datetime with timezone information
  - fail closed if the recommendation artifact is missing, invalid JSON, wrong `artifact_type`, wrong `user_id`, wrong `date`, or wrong `recommendation_id`
  - fail closed on invalid `judgment_label` or malformed payload
  - preserve a direct link to the referenced recommendation artifact and its evidence refs for inspectability
  - rejection must be non-mutating for any preexisting dated or latest judgment artifacts

### `writeback.recommendation_resolution_transition`
- Purpose: write one updated `recommendation_resolution_window_memory` locator by attaching one already-written same-day `recommendation_judgment` artifact to one targeted pending recommendation entry inside one bounded seven-day window.
- Current implementation status: proof-complete in v1.
- Required fields: `user_id`, `start_date`, `end_date`, `recommendation_artifact_path`, `recommendation_artifact_id`, `judgment_artifact_path`, `judgment_artifact_id`, `resolution_window_memory_path`, `written_at`, `request_id`, `requested_at`.
- Optional fields: `feedback_window_memory_path`.
- Semantics:
  - validate `request_id` as a non-empty string and `requested_at` as an ISO 8601 datetime with timezone information
  - validate `written_at` as an ISO 8601 datetime with timezone information
  - validate the supplied recommendation artifact and judgment artifact using the existing scope and linkage rules
  - validate the input locator as one bounded `recommendation_resolution_window_memory` artifact for the same user and exact requested window
  - mutate only the targeted recommendation entry by attaching the exact `judgment_artifact_path`
  - fail closed if the target recommendation is absent, duplicated, or already linked, or if the locator is malformed or out of scope
  - when `feedback_window_memory_path` is supplied, emit a paired `recommendation_feedback_window_memory` locator for the same bounded window
  - rejection must be non-mutating for any preexisting dated or latest written locator artifacts

## Common response envelope

Each writeback response uses this stable shape:
- `ok`
- `artifact_path`
- `latest_artifact_path`
- `writeback`
- `validation`
- `error`

For `writeback.recommendation_judgment`, the `writeback` object contains:
- `artifact_type`
- `user_id`
- `date`
- `judgment_id`
- `judgment_label`
- `action_taken`
- `why`
- `written_at`
- `request_id`
- `requested_at`
- `recommendation_artifact_path`
- `recommendation_artifact_id`
- `recommendation_evidence_refs`

For `writeback.recommendation_resolution_transition`, the `writeback` object contains:
- `operation`
- `user_id`
- `start_date`
- `end_date`
- `recommendation_artifact_path`
- `recommendation_artifact_id`
- `judgment_artifact_path`
- `judgment_artifact_id`
- `resolution_window_memory_path`
- `feedback_window_memory_path`
- `written_at`
- `request_id`
- `requested_at`
- `written_locator_artifacts`
- `transition_target`

## Path conventions

- `recommendation_judgment` dated: `{output_dir}/recommendation_judgment_{date}.json`
- `recommendation_judgment` latest: `{output_dir}/recommendation_judgment_latest.json`
- `recommendation_resolution_window_memory` dated: `{output_dir}/recommendation_resolution_window_memory_{start_date}_{end_date}.json`
- `recommendation_resolution_window_memory` latest: `{output_dir}/recommendation_resolution_window_memory_latest.json`
- `recommendation_feedback_window_memory` dated: `{output_dir}/recommendation_feedback_window_memory_{start_date}_{end_date}.json`
- `recommendation_feedback_window_memory` latest: `{output_dir}/recommendation_feedback_window_memory_latest.json`

## Proof expectation for v1

The frozen proof bundles for these slices live under:
- `artifacts/protocol_layer_proof/2026-04-11-writeback-judgment/`
- `artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-transition-writeback/`

The transition bundle includes:
- input locator before transition
- successful transition request
- success envelope
- output locator after transition
- derived post-write `recommendation-resolution-window` retrieval envelope
- derived post-write `recommendation-feedback-window` retrieval envelope
- rejected transition request
- rejected envelope
- explicit non-mutation proof
- explicit selective-neighbor-stability proof
- proof manifest with deterministic replay commands

## Explicit out-of-scope items for these slices

- broader memory-write framework
- hosted writeback service
- recommendation generation changes
- multi-day feedback analytics
- embedded-coach framing
