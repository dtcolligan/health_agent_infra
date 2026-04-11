# Health Lab memory write contract v1

Date: 2026-04-11

## Purpose

This contract defines one bounded writeback protocol an external agent may use to capture same-day recommendation judgment into the user-owned memory layer.

Health Lab remains the protocol, CLI, and proof surface only. It does not host the private memory layer.

## Architecture boundary

- Private health memory remains external to Health Lab.
- Health Lab publishes protocol discovery, request semantics, response envelopes, and proof artifacts.
- This slice writes one scoped recommendation judgment artifact only.
- This slice must not broaden into hosted memory, embedded coaching, analytics expansion, or recommendation rewriting.

## Discovery surface

Machine-readable discovery is published by `python3 -m health_model.agent_contract_cli describe`.

## Supported writeback operation

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

## Common response envelope

Each writeback response uses this stable shape:
- `ok`
- `artifact_path`
- `latest_artifact_path`
- `writeback`
- `validation`
- `error`

The `writeback` object contains:
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

## Proof expectation for v1

The frozen proof bundle for this slice lives under:
- `artifacts/protocol_layer_proof/2026-04-11-writeback-judgment/`

The bundle includes:
- writeback request artifact
- copied accepted input artifacts
- success envelope
- fail-closed wrong-scope envelope
- fail-closed missing-artifact envelope
- explicit non-mutation proof
- proof manifest

## Explicit out-of-scope items for this slice

- broader memory-write framework
- hosted writeback service
- recommendation generation changes
- multi-day feedback analytics
- embedded-coach framing
