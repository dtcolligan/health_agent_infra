# Flagship Loop Spec — Recovery and Training-Readiness

Status: Phase 1 doctrine. Adopted 2026-04-16. Derived from [canonical_doctrine.md](canonical_doctrine.md) and the Chief Operational Brief.

This spec defines the single flagship loop Health Lab will prove end-to-end. It is the only flagship. Any additional loops are out of scope until this one is complete and legibly public.

## Name

`recovery_readiness_v1`

## Purpose

On a daily cadence, turn passively pulled wearable evidence plus a short manual check-in into one structured recovery state, one bounded training recommendation, and one next-day review event.

## Why this loop

- narrow enough to build in one sprint
- legible to an outsider in under two minutes
- naturally suited to consumer wearables already pulled from
- safety-bounded compared with broader medical or nutrition coaching
- reusable pattern once proved: evidence -> state -> policy -> recommendation -> action -> review

## Loop shape

```
PULL        -> Garmin passive pull + typed manual readiness intake
CLEAN       -> canonical cleaned evidence objects
STATE       -> recovery_state object (see state_object_schema.md)
POLICY      -> minimal executable policy rules (see minimal_policy_rules.md)
RECOMMEND   -> training_recommendation object (see recommendation_object_schema.md)
ACTION      -> bounded writeback (daily plan note + recommendation log entry)
REVIEW      -> next-day follow-up event asking whether the intervention helped
```

## Inputs

### Required
- Garmin sleep record for the most recent night
  - total sleep duration
  - sleep stages if available
  - sleep quality score if reported by source
- Garmin resting heart rate (most recent daily value)
- Garmin recovery proxy (HRV if available; otherwise resting HR trend vs baseline)
- prior training load or activity summary for the trailing 7 days
- manual readiness check-in submitted today
  - subjective soreness
  - subjective energy
  - subjective mood
  - planned session type for today (easy / moderate / hard / rest)

### Optional
- short workload or calendar context note

Nutrition is explicitly out of scope for this flagship loop (see [explicit_non_goals.md](explicit_non_goals.md)).

### Missingness handling
See [minimal_policy_rules.md](minimal_policy_rules.md). The loop must degrade gracefully when non-required inputs are absent, and must refuse to produce a confident recommendation when required inputs are too sparse.

## Outputs

### Per run
1. one `recovery_state` object conforming to [state_object_schema.md](state_object_schema.md)
2. one `training_recommendation` object conforming to [recommendation_object_schema.md](recommendation_object_schema.md)
3. one `action_record` describing the writeback performed (path, timestamp, idempotency key)
4. one `review_event` scheduled for the next-day follow-up

### Per review
One `review_outcome` record linking back to the originating `training_recommendation` via `recommendation_id`, capturing whether the user followed the recommendation and whether recovery or session quality improved.

## Worked example

Illustrative shape only. Field names and types are authoritative in the schema docs, not here.

- state: `recovery_status = mildly_impaired`
- recommendation: `action = downgrade_hard_session_to_zone_2`
- rationale: sleep debt elevated, soreness high, resting HR above 7-day baseline
- confidence: `moderate`
- uncertainty: `hrv_unavailable`
- action: append recommendation entry to today's plan note via bounded writeback
- review: tomorrow morning, prompt user with a yes/no on whether the downgrade helped recovery or session quality

## Conditions for this to count as proof

All six must be visible and inspectable:

1. **Deterministic evidence path** — clear traceable route from raw Garmin + manual check-in inputs through cleaned objects
2. **Explicit state object** — typed, versioned, readable; not prose
3. **Policy gate** — executable rules run; their decisions are logged
4. **Structured recommendation object** — typed fields: action, rationale, confidence, uncertainty, follow-up
5. **Bounded writeback** — reversible, auditable, low-risk only
6. **Review loop** — review event is scheduled and review outcomes are captured

If any of the six is missing, the flagship proof is not yet real.

## Boundaries

- no diagnosis
- no medical claims
- no nutrition prescription
- no strength-training programming
- no multi-day autonomous planning
- no writebacks to external services in this phase (local writebacks only)
- no auto-execution of anything beyond writing notes

## Phase relationship

This spec is the contract that Phase 2 (narrow end-to-end implementation) builds against. Phase 3 (public proof and legibility) shapes its presentation. Phase 4 (controlled expansion) cannot start until this loop is complete and legibly public.

## Ownership of downstream schemas

Data shapes referenced here are authoritative in the named schema docs:

- `recovery_state` -> [state_object_schema.md](state_object_schema.md)
- `training_recommendation` -> [recommendation_object_schema.md](recommendation_object_schema.md)
- policy rules -> [minimal_policy_rules.md](minimal_policy_rules.md)
