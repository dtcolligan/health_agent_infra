# State Object Schema — `recovery_state` v1

Status: Phase 1 doctrine. Adopted 2026-04-16. Derived from [canonical_doctrine.md](canonical_doctrine.md) and [flagship_loop_spec.md](flagship_loop_spec.md).

This is the authoritative shape of the live user state emitted by the STATE layer of the flagship loop. State is first-class: typed, versioned, inspectable, and the single input to the RECOMMEND layer.

## Object

`recovery_state`

## Version

`v1`. Breaking changes require a new version and a migration note.

## Purpose

Compress today's cleaned evidence into one typed summary of the user's recovery picture, accompanied by explicit uncertainty accounting and explicit signal quality. The RECOMMEND layer must be able to make decisions from this object alone; no implicit context may leak in.

## Fields

| field | type | required | description |
|---|---|---|---|
| `schema_version` | string | yes | fixed value `"recovery_state.v1"` |
| `user_id` | string | yes | opaque identifier for the user in local memory |
| `computed_at` | ISO-8601 timestamp | yes | when this state was computed |
| `as_of_date` | ISO-8601 date | yes | the subjective day this state describes |
| `recovery_status` | enum | yes | one of: `recovered`, `mildly_impaired`, `impaired`, `unknown` |
| `readiness_score` | number or null | yes | 0.0–1.0 scalar if derivable; null if not derivable under current inputs |
| `sleep_debt` | enum | yes | one of: `none`, `mild`, `moderate`, `elevated`, `unknown` |
| `soreness_signal` | enum | yes | one of: `low`, `moderate`, `high`, `unknown` (sourced from manual intake) |
| `resting_hr_vs_baseline` | enum | yes | one of: `below`, `at`, `above`, `well_above`, `unknown` |
| `hrv_vs_baseline` | enum | yes | one of: `below`, `at`, `above`, `well_above`, `unknown` |
| `training_load_trailing_7d` | enum | yes | one of: `low`, `moderate`, `high`, `spike`, `unknown` |
| `active_goal` | string or null | no | user's stated current training goal if provided |
| `signal_quality` | object | yes | see below |
| `uncertainties` | array of strings | yes | short machine-readable tokens describing what is unknown or noisy |
| `inputs_used` | object | yes | see below |

### `signal_quality` object

| field | type | description |
|---|---|---|
| `coverage` | enum | one of: `full`, `partial`, `sparse`, `insufficient` |
| `required_inputs_present` | boolean | whether all flagship-required inputs are present |
| `notes` | array of strings | optional short reasons for downgraded quality |

### `inputs_used` object

| field | type | description |
|---|---|---|
| `garmin_sleep_record_id` | string or null | id of the cleaned sleep record consumed |
| `garmin_resting_hr_record_id` | string or null | id of the cleaned resting HR record consumed |
| `garmin_hrv_record_id` | string or null | id of the cleaned HRV record consumed if available |
| `training_load_window` | string | label for the window summarized (e.g. `"trailing_7d"`) |
| `manual_readiness_submission_id` | string or null | id of today's manual readiness intake |
| `optional_context_note_ids` | array of strings | ids of any optional workload / context notes consumed |

## Enumerations

All enumerations are closed sets. Adding a new value is a schema change.

- `recovery_status`: `recovered | mildly_impaired | impaired | unknown`
- `sleep_debt`: `none | mild | moderate | elevated | unknown`
- `soreness_signal`: `low | moderate | high | unknown`
- `resting_hr_vs_baseline`: `below | at | above | well_above | unknown`
- `hrv_vs_baseline`: `below | at | above | well_above | unknown`
- `training_load_trailing_7d`: `low | moderate | high | spike | unknown`
- `signal_quality.coverage`: `full | partial | sparse | insufficient`

## Uncertainty tokens

`uncertainties` holds machine-readable short tokens. Consumers may display human-readable versions. Suggested initial token vocabulary:

- `hrv_unavailable`
- `sleep_record_missing`
- `resting_hr_record_missing`
- `manual_checkin_missing`
- `training_load_window_incomplete`
- `baseline_window_too_short`
- `single_source_only`

Additional tokens may be added only once the runtime emits them. Tokens that describe data the runtime does not actually consume (for example, nutrition) should not appear on this list.

The vocabulary is extensible. Each new token is documented in this file before being emitted.

## Construction rules

1. State is constructed only from cleaned evidence objects emitted by the CLEAN layer. PULL-shaped raw records are not read directly by STATE.
2. Every required field must resolve to a value. When evidence is missing, `unknown` (or `null` where typed) is used and a corresponding `uncertainties` token is appended.
3. `signal_quality.coverage` follows this hierarchy:
   - `full` — all flagship-required inputs present and fresh
   - `partial` — all required inputs present but at least one is stale or low-quality
   - `sparse` — at least one required input missing
   - `insufficient` — manual check-in missing OR sleep record missing
4. `readiness_score` is only populated when `signal_quality.coverage` is `full` or `partial`. Otherwise it is null.
5. `recovery_status = unknown` is valid and expected when coverage is `insufficient`.

## Consumer contract

The RECOMMEND layer must:

- read only from this object
- treat `unknown` / null as first-class, never silently default
- refuse to emit a high-confidence recommendation when `signal_quality.coverage` is `sparse` or worse
- surface relevant `uncertainties` tokens in the resulting recommendation's `uncertainty` field

## Example

Illustrative only. Not validated.

```json
{
  "schema_version": "recovery_state.v1",
  "user_id": "u_local_1",
  "computed_at": "2026-04-16T07:15:00Z",
  "as_of_date": "2026-04-16",
  "recovery_status": "mildly_impaired",
  "readiness_score": 0.58,
  "sleep_debt": "moderate",
  "soreness_signal": "high",
  "resting_hr_vs_baseline": "above",
  "hrv_vs_baseline": "unknown",
  "training_load_trailing_7d": "high",
  "active_goal": "spring_10k_base_build",
  "signal_quality": {
    "coverage": "partial",
    "required_inputs_present": true,
    "notes": ["hrv not reported by source today"]
  },
  "uncertainties": ["hrv_unavailable"],
  "inputs_used": {
    "garmin_sleep_record_id": "g_sleep_2026-04-15",
    "garmin_resting_hr_record_id": "g_rhr_2026-04-16",
    "garmin_hrv_record_id": null,
    "training_load_window": "trailing_7d",
    "manual_readiness_submission_id": "m_ready_2026-04-16",
    "optional_context_note_ids": []
  }
}
```

## Related

- [flagship_loop_spec.md](flagship_loop_spec.md)
- [recommendation_object_schema.md](recommendation_object_schema.md)
- [minimal_policy_rules.md](minimal_policy_rules.md)
