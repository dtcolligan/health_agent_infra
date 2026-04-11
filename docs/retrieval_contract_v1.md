# Health Lab retrieval contract v1

Date: 2026-04-11

## Purpose

This contract defines the bounded read-only retrieval protocol an external agent may use to discover and request health evidence from a user-owned private memory layer.

Health Lab is the protocol, CLI, and proof surface only. It does not host the private memory layer.

## Architecture boundary

- Private health memory remains external to Health Lab.
- Health Lab publishes protocol discovery, request semantics, response envelopes, and proof artifacts.
- Retrieval payloads must stay evidence-first, scope-bounded, and fail closed on scope or contract violations.
- Retrieval payloads must not contain diagnosis, coaching recommendations, fabricated backfills, or hidden out-of-scope aggregation.

## Discovery surface

Machine-readable discovery is published by `python3 -m health_model.agent_contract_cli describe`.

## Supported retrieval operations

### `retrieve.day_context`
- Purpose: return one scoped `agent_readable_daily_context` artifact.
- Current implementation status: proof-complete in v1.
- Required scope: `user_id`, `date`, `artifact_path`, `request_id`, `requested_at`.
- Semantics:
  - validate `request_id` as a non-empty string and `requested_at` as an ISO 8601 datetime with timezone information, then echo both under `validation.request_echo`
  - fail closed if the artifact is missing, invalid JSON, wrong `artifact_type`, wrong `user_id`, or wrong `date`
  - preserve `generated_from`, `important_gaps`, and `conflicts` exactly
  - do not invent unsupported metrics

### `retrieve.day_nutrition_brief`
- Purpose: return a bounded day-scoped nutrition brief from an accepted day nutrition brief artifact.
- Current implementation status: proof-complete in v1.
- Required scope: `user_id`, `date`, `artifact_path`, `request_id`, `requested_at`.
- Semantics:
  - validate `request_id` as a non-empty string and `requested_at` as an ISO 8601 datetime with timezone information, then echo both under `validation.request_echo`
  - fail closed if the artifact is missing, invalid JSON, wrong `artifact_type`, wrong `user_id`, or wrong `date`
  - explicit missingness, never fabricated zeros
  - no unsupported micronutrient or coaching claims

### `retrieve.sleep_review`
- Purpose: return a bounded one-day sleep evidence review.
- Current implementation status: proof-complete in v1.
- Required scope: `user_id`, `date`, `artifact_path`, `request_id`, `requested_at`.
- Semantics:
  - validate `request_id` as a non-empty string and `requested_at` as an ISO 8601 datetime with timezone information, then echo both under `validation.request_echo`
  - review-only, not advisory
  - distinguish grounded, subjective-only, and missing sleep evidence
  - partial coverage is valid when scope matches but evidence is sparse
  - fail closed if the artifact is missing, invalid JSON, wrong `artifact_type`, wrong `user_id`, or wrong `date`

### `retrieve.weekly_pattern_review`
- Purpose: return a bounded seven-day pattern review over already accepted daily surfaces.
- Current implementation status: discovery-visible, implementation-thin.
- Required scope: `user_id`, `start_date`, `end_date`, `memory_locator`, `request_id`, `requested_at`.
- Semantics:
  - capped to seven contiguous dates in v1
  - aggregate only already-supported daily evidence
  - no causal inference, diagnosis, or coaching logic

## Accepted scope fields

Required common retrieval fields:
- `user_id`
- `request_id`
- `requested_at`
- scope selector: `date` or `start_date` plus `end_date`
- locator: `artifact_path` or `memory_locator`

Optional retrieval fields for accepted daily retrieval ops:
- `include_conflicts`
- `include_missingness`

Optional retrieval fields still used by discovery-visible weekly retrieval only:
- `timezone`
- `max_evidence_items`

## Missingness and conflict rules

Accepted missingness states:
- `present`
- `partial`
- `missing`
- `not_supported`

Accepted conflict states:
- `none`
- `source_conflict`
- `scope_conflict`
- `resolution_required`

Rules:
- sparse evidence stays explicit
- conflicts are carried through, not silently resolved
- retrieval may succeed with partial coverage when scope validation passes
- retrieval fails closed only on contract, scope, or artifact validation failure

## Common response envelope

Each retrieval response uses this stable shape:
- `ok`
- `artifact_path` or `result_artifact_path`
- `retrieval`
- `validation`
- `error`

The `retrieval` object contains:
- `operation`
- `scope`
- `coverage_status`
- `generated_from`
- `evidence`
- `important_gaps`
- `conflicts`
- `unsupported_claims`

## Proof expectation for v1

The frozen proof bundles for this slice live under:
- `artifacts/protocol_layer_proof/2026-04-11/` for `retrieve.day_context`
- `artifacts/protocol_layer_proof/2026-04-11-day-nutrition-brief/` for `retrieve.day_nutrition_brief`
- `artifacts/protocol_layer_proof/2026-04-11-sleep-review/` for `retrieve.sleep_review`

Each bundle includes:
- retrieval request artifact
- copied day-context artifact
- success envelope
- fail-closed wrong-scope envelope
- proof manifest

## Explicit out-of-scope items for this slice

- hosted retrieval service
- weekly analytics implementation beyond thin discovery metadata
- memory-write contract work
- embedded-coach framing
