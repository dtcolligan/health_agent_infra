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

Machine-readable discovery is published by `python3 -m health_model.agent_contract_cli describe` (`health_agent_infra.agent_contract_cli` remains temporarily compatible).

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

### `retrieve.recommendation`
- Purpose: return one scoped `agent_recommendation` artifact.
- Current implementation status: proof-complete in v1.
- Required scope: `user_id`, `date`, `artifact_path`, `request_id`, `requested_at`.
- Semantics:
  - validate `request_id` as a non-empty string and `requested_at` as an ISO 8601 datetime with timezone information, then echo both under `validation.request_echo`
  - fail closed if the artifact is missing, invalid JSON, wrong `artifact_type`, wrong `user_id`, or wrong `date`
  - preserve the accepted recommendation payload fields under `retrieval.evidence`, especially `recommendation_id`, `summary`, `rationale`, `evidence_refs`, `confidence_score`, `context_artifact_path`, and `context_artifact_id`
  - remain read-only and artifact-scoped with no new synthesis, coaching, or aggregation

### `retrieve.recommendation_judgment`
- Purpose: return one scoped `recommendation_judgment` artifact.
- Current implementation status: proof-complete in v1.
- Required scope: `user_id`, `date`, `artifact_path`, `request_id`, `requested_at`.
- Semantics:
  - validate `request_id` as a non-empty string and `requested_at` as an ISO 8601 datetime with timezone information, then echo both under `validation.request_echo`
  - fail closed if the artifact is missing, invalid JSON, wrong `artifact_type`, wrong `user_id`, or wrong `date`
  - preserve the accepted judgment payload fields under `retrieval.evidence`, especially `judgment_id`, `judgment_label`, `action_taken`, `why`, `recommendation_artifact_path`, `recommendation_artifact_id`, and `recommendation_evidence_refs`
  - remain read-only and artifact-scoped with no new synthesis, coaching, or aggregation

### `retrieve.recommendation_feedback`
- Purpose: return one linked read-only feedback object built from one accepted `agent_recommendation` artifact and one same-day `recommendation_judgment` artifact.
- Current implementation status: proof-complete in v1.
- Required scope: `user_id`, `date`, `recommendation_artifact_path`, `judgment_artifact_path`, `request_id`, `requested_at`.
- Semantics:
  - validate `request_id` as a non-empty string and `requested_at` as an ISO 8601 datetime with timezone information, then echo both under `validation.request_echo`
  - fail closed if either artifact is missing, invalid JSON, wrong `artifact_type`, wrong `user_id`, or wrong `date`
  - fail closed if `judgment.recommendation_artifact_id` does not match `recommendation.recommendation_id`
  - fail closed if `judgment.recommendation_artifact_path` does not resolve to the supplied recommendation artifact path
  - return `retrieval.evidence.recommendation`, `retrieval.evidence.judgment`, and explicit linkage fields, with no new synthesis, coaching, or aggregation

### `retrieve.recommendation_feedback_window`
- Purpose: return a bounded seven-day read-only window of linked recommendation plus same-day judgment pairs aggregated only from an accepted memory locator fixture.
- Current implementation status: proof-complete in v1.
- Required scope: `user_id`, `start_date`, `end_date`, `memory_locator`, `request_id`, `requested_at`.
- Optional scope: `timezone`, `max_feedback_items`, `include_conflicts`, `include_missingness`.
- Semantics:
  - validate `request_id` as a non-empty string and `requested_at` as an ISO 8601 datetime with timezone information, then echo both under `validation.request_echo`
  - fail closed if `start_date` or `end_date` is invalid, the inclusive range exceeds seven contiguous dates, or the bounded `memory_locator` fixture cannot be resolved
  - aggregate only accepted same-day recommendation plus judgment pairs listed by the bounded `memory_locator`
  - fail closed if any listed pair is malformed, wrong-scope, missing, or has mismatched recommendation id or recommendation artifact path linkage
  - allow truthful partial coverage when some in-range dates legitimately have no linked pair listed in the locator
  - no scoring, ranking, recommendation rewriting, coaching logic, or analytics

### `retrieve.recommendation_resolution_window`
- Purpose: return a bounded seven-day read-only window of accepted recommendations listed by a scoped memory locator, separating judged recommendations, pending_judgment recommendations, and dates with no recommendation.
- Current implementation status: proof-complete in v1.
- Required scope: `user_id`, `start_date`, `end_date`, `memory_locator`, `request_id`, `requested_at`.
- Optional scope: `timezone`, `max_recommendation_items`, `include_conflicts`, `include_missingness`.
- Semantics:
  - validate `request_id` as a non-empty string and `requested_at` as an ISO 8601 datetime with timezone information, then echo both under `validation.request_echo`
  - fail closed if `start_date` or `end_date` is invalid, the inclusive range exceeds seven contiguous dates, or the bounded `memory_locator` fixture cannot be resolved
  - aggregate only accepted recommendation artifacts listed by the bounded `memory_locator`
  - if a locator entry includes a judgment artifact path, validate same-day scope plus id/path linkage exactly as in `retrieve.recommendation_feedback`
  - return `resolution_status` as `judged` or `pending_judgment` per recommendation, and surface uncovered dates separately as `no_recommendation`
  - fail closed if any listed recommendation entry is malformed, wrong-scope, missing, or claims a malformed linked judgment artifact
  - no scoring, ranking, recommendation rewriting, coaching logic, or analytics

### `retrieve.weekly_pattern_review`
- Purpose: return a bounded seven-day pattern review over already accepted daily context artifacts.
- Current implementation status: proof-complete in v1.
- Required scope: `user_id`, `start_date`, `end_date`, `memory_locator`, `request_id`, `requested_at`.
- Optional scope: `timezone`, `max_evidence_items`, `include_conflicts`, `include_missingness`.
- Semantics:
  - validate `request_id` as a non-empty string and `requested_at` as an ISO 8601 datetime with timezone information, then echo both under `validation.request_echo`
  - fail closed if `start_date` or `end_date` is invalid, the inclusive range exceeds seven contiguous dates, or the bounded `memory_locator` fixture cannot be resolved
  - aggregate only accepted `agent_readable_daily_context` artifacts listed by the bounded `memory_locator`
  - return per-day sleep evidence summaries, repeated important gaps, and surfaced conflicts only
  - partial weekly coverage is valid when accepted daily artifacts are sparse but in scope
  - no causal inference, diagnosis, coaching logic, or memory writes

## Accepted scope fields

Required common retrieval fields:
- `user_id`
- `request_id`
- `requested_at`
- scope selector: `date` or `start_date` plus `end_date`
- locator: `artifact_path`, `recommendation_artifact_path` plus `judgment_artifact_path`, or `memory_locator`

Optional retrieval fields still used by bounded window retrieval ops:
- `timezone`
- `max_feedback_items`
- `max_recommendation_items`


Optional retrieval fields for accepted daily retrieval ops:
- `include_conflicts`
- `include_missingness`

Optional retrieval fields still used by weekly retrieval:
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
- `artifacts/protocol_layer_proof/2026-04-11-recommendation-retrieval/` for `retrieve.recommendation`
- `artifacts/protocol_layer_proof/2026-04-11-recommendation-judgment-retrieval/` for `retrieve.recommendation_judgment`
- `artifacts/protocol_layer_proof/2026-04-11-recommendation-feedback/` for `retrieve.recommendation_feedback`
- `artifacts/protocol_layer_proof/2026-04-11-recommendation-feedback-window/` for `retrieve.recommendation_feedback_window`
- `artifacts/protocol_layer_proof/2026-04-11-recommendation-resolution-window/` for `retrieve.recommendation_resolution_window`
- `artifacts/protocol_layer_proof/2026-04-11-weekly-pattern-review/` for `retrieve.weekly_pattern_review`

Each bundle includes:
- retrieval request artifact
- copied accepted input artifacts for the bounded proof slice
- success envelope
- fail-closed envelopes for the named scope or contract violations
- proof manifest

## Explicit out-of-scope items for this slice

- hosted retrieval service
- weekly analytics beyond the bounded accepted-daily-artifact review slice
- memory-write contract work
- embedded-coach framing
