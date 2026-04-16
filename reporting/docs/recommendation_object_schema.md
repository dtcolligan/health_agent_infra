# Recommendation Object Schema — `training_recommendation` v1

Status: Phase 1 doctrine. Adopted 2026-04-16. Derived from [canonical_doctrine.md](canonical_doctrine.md) and [flagship_loop_spec.md](flagship_loop_spec.md).

This is the authoritative shape of the output emitted by the RECOMMEND layer of the flagship loop. Recommendations are typed and bounded, not free prose. Each one is constructed from exactly one `recovery_state` object under exactly one set of policy decisions.

## Object

`training_recommendation`

## Version

`v1`. Breaking changes require a new version and a migration note.

## Fields

| field | type | required | description |
|---|---|---|---|
| `schema_version` | string | yes | fixed value `"training_recommendation.v1"` |
| `recommendation_id` | string | yes | stable id; used by REVIEW to link outcome back |
| `user_id` | string | yes | opaque user id |
| `issued_at` | ISO-8601 timestamp | yes | time of emission |
| `for_date` | ISO-8601 date | yes | the date this recommendation applies to |
| `state_ref` | object | yes | see below |
| `action` | enum | yes | see action enum below |
| `action_detail` | object or null | yes | optional structured detail matched to `action` |
| `rationale` | array of strings | yes | short ordered bullet-sized reasons, human-readable |
| `confidence` | enum | yes | one of: `low`, `moderate`, `high` |
| `uncertainty` | array of strings | yes | tokens propagated from `recovery_state.uncertainties`, possibly extended |
| `follow_up` | object | yes | see below |
| `policy_decisions` | array of objects | yes | which policy rules fired and how — see below |
| `bounded` | boolean | yes | always `true` in this phase; asserts this recommendation fits the flagship's safety envelope |

### `state_ref` object

| field | type | description |
|---|---|---|
| `schema_version` | string | e.g. `"recovery_state.v1"` |
| `computed_at` | ISO-8601 timestamp | copied from the source state |
| `as_of_date` | ISO-8601 date | copied from the source state |
| `hash` | string or null | optional content hash of the state object for tamper-evidence |

### `action` enum (v1)

Closed set for this phase. Adding a value is a schema change.

- `proceed_with_planned_session` — inputs support today's planned session as-is
- `downgrade_hard_session_to_zone_2` — reduce intensity of a planned hard session to easy aerobic
- `downgrade_session_to_mobility_only` — replace planned session with mobility / light movement
- `rest_day_recommended` — take a rest day
- `defer_decision_insufficient_signal` — state quality is insufficient to recommend; user decides, system does not
- `escalate_for_user_review` — pattern detected that deserves user attention beyond today's session

### `action_detail` object (optional, shape depends on action)

Examples:

- for `downgrade_hard_session_to_zone_2`: `{ "target_intensity": "zone_2", "target_duration_minutes": 45 }`
- for `rest_day_recommended`: `{ "suggested_activity": "walk_or_mobility" }`
- for `escalate_for_user_review`: `{ "reason_token": "resting_hr_spike_3_days_running" }`

`action_detail` is `null` when no structured detail is needed.

### `follow_up` object

| field | type | description |
|---|---|---|
| `review_at` | ISO-8601 timestamp | when the REVIEW layer should prompt the user |
| `review_question` | string | short human-readable question to ask at review time |
| `review_event_id` | string | id of the scheduled review event for later linkage |

### `policy_decisions` array

Each element:

| field | type | description |
|---|---|---|
| `rule_id` | string | id of the policy rule that fired |
| `decision` | enum | one of: `allow`, `soften`, `block`, `escalate` |
| `note` | string | short reason string suitable for the audit log |

The `policy_decisions` array is the auditable trace that POLICY actually ran.

## Construction rules

1. The RECOMMEND layer reads only the `recovery_state` object and the policy layer's decisions. No side-channel state.
2. If `recovery_state.signal_quality.coverage` is `insufficient`, the only permissible `action` values are `defer_decision_insufficient_signal` or `escalate_for_user_review`. `confidence` must be `low`.
3. If `recovery_state.signal_quality.coverage` is `sparse`, `confidence` must be `low` or `moderate`. It may not be `high`.
4. `uncertainty` must include every token from `recovery_state.uncertainties`. Additional tokens may be appended (for example, `rationale_relies_on_single_source`).
5. `rationale` must be short ordered strings derived from explicit state fields. No free-form paragraphs.
6. `bounded` is always `true` in this phase. If any policy rule emits `block`, the recommendation is not emitted at all — a `defer_decision_insufficient_signal` is emitted in its place.

## ACTION layer contract

Consumers in the ACTION layer must:

- treat this object as the only source of truth for the writeback
- write idempotently, keyed by `recommendation_id`
- never perform an action whose side effects exceed appending to a local note or recommendation log in this phase
- carry `recommendation_id` through to the review event

## REVIEW layer contract

Consumers in the REVIEW layer must:

- fire at `follow_up.review_at`
- ask `follow_up.review_question`
- link the resulting `review_outcome` back via `recommendation_id`

## Example

Illustrative only. Not validated.

```json
{
  "schema_version": "training_recommendation.v1",
  "recommendation_id": "rec_2026-04-16_u_local_1_01",
  "user_id": "u_local_1",
  "issued_at": "2026-04-16T07:16:00Z",
  "for_date": "2026-04-16",
  "state_ref": {
    "schema_version": "recovery_state.v1",
    "computed_at": "2026-04-16T07:15:00Z",
    "as_of_date": "2026-04-16",
    "hash": null
  },
  "action": "downgrade_hard_session_to_zone_2",
  "action_detail": {
    "target_intensity": "zone_2",
    "target_duration_minutes": 45
  },
  "rationale": [
    "sleep_debt=moderate",
    "soreness_signal=high",
    "resting_hr_vs_baseline=above",
    "training_load_trailing_7d=high"
  ],
  "confidence": "moderate",
  "uncertainty": ["hrv_unavailable"],
  "follow_up": {
    "review_at": "2026-04-17T07:00:00Z",
    "review_question": "Did yesterday's downgrade to Zone 2 improve how today feels?",
    "review_event_id": "rev_2026-04-17_rec_2026-04-16_u_local_1_01"
  },
  "policy_decisions": [
    { "rule_id": "require_min_coverage", "decision": "allow", "note": "coverage=partial, required inputs present" },
    { "rule_id": "no_high_confidence_on_sparse_signal", "decision": "soften", "note": "capped confidence to moderate due to hrv_unavailable" }
  ],
  "bounded": true
}
```

## Related

- [flagship_loop_spec.md](flagship_loop_spec.md)
- [state_object_schema.md](state_object_schema.md)
- [minimal_policy_rules.md](minimal_policy_rules.md)
