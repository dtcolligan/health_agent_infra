# Recovery Domain

Recovery is the readiness anchor for the v1 runtime. It decides whether the
body appears recovered enough for today's planned training day, using sleep,
resting heart rate, HRV, recent load, and manual soreness/energy context.

## Runtime Surface

| Surface | Path |
|---|---|
| Schemas | `src/health_agent_infra/domains/recovery/schemas.py` |
| Classifier | `src/health_agent_infra/domains/recovery/classify.py` |
| Policy | `src/health_agent_infra/domains/recovery/policy.py` |
| Projector | `src/health_agent_infra/core/state/projectors/recovery.py` |
| Manual intake | `src/health_agent_infra/domains/recovery/readiness_intake.py` |
| Skill | `src/health_agent_infra/skills/recovery-readiness/SKILL.md` |

## Evidence And Accepted State

Recovery reads the `accepted_recovery_state_daily` row plus raw-summary trend
fields built during pull/clean/projection. Inputs include sleep hours,
resting HR, resting-HR baseline/ratio, HRV ratio, trailing training load,
training-load baseline/ratio, resting-HR spike days, and manual soreness.

Manual soreness is optional for the user to record, but it is currently
coverage-critical: absent sleep or absent soreness makes classifier coverage
`insufficient`. The runtime chooses honesty over guessing because soreness is
the user-closeable signal that wearable recovery cannot observe directly.

## Classifier Reference

`ClassifiedRecoveryState` exposes:

| Field | Values |
|---|---|
| `sleep_debt_band` | `none`, `mild`, `moderate`, `elevated`, `unknown` |
| `resting_hr_band` | `below`, `at`, `above`, `well_above`, `unknown` |
| `hrv_band` | `below`, `at`, `above`, `well_above`, `unknown` |
| `training_load_band` | `low`, `moderate`, `high`, `spike`, `unknown` |
| `soreness_band` | `low`, `moderate`, `high`, `unknown` |
| `coverage_band` | `full`, `partial`, `sparse`, `insufficient` |
| `recovery_status` | `recovered`, `mildly_impaired`, `impaired`, `unknown` |
| `readiness_score` | `0.0..1.0`, or `None` when coverage is insufficient |

Uncertainty tokens call out missing sleep, manual check-in, HRV, baseline, or
training-load windows. Thresholds come from `core/config.py`; skills must not
recompute bands.

## Policy / R-rules

`RecoveryPolicyResult` contains `policy_decisions`, optional
`forced_action`, optional `forced_action_detail`, optional
`capped_confidence`, and optional `evidence_locators`.

| Rule id | Effect |
|---|---|
| `require_min_coverage` | Forces `defer_decision_insufficient_signal` when coverage is insufficient. |
| `no_high_confidence_on_sparse_signal` | Caps confidence at `moderate` when coverage is sparse. |
| `resting_hr_spike_escalation` | Forces `escalate_for_user_review` when consecutive resting-HR spike days cross the configured threshold. |

When `resting_hr_spike_escalation` fires with
`reason_token=resting_hr_spike_3_days_running`, the policy may include
source-row locators so future explanation surfaces can point back to the
accepted recovery rows.

## Proposal Actions

- `proceed_with_planned_session`
- `downgrade_hard_session_to_zone_2`
- `downgrade_session_to_mobility_only`
- `rest_day_recommended`
- `defer_decision_insufficient_signal`
- `escalate_for_user_review`

## X-rule Participation

Recovery hard proposals are training-domain proposals. They can be targeted
by X1a/X1b sleep-debt rules, X2 nutrition-underfuelling, X3a/X3b load-spike
rules, X6a/X6b body-battery rules, and X7 confidence capping. Recovery also
provides adjacent readiness signals to running and strength classifiers.

## Missingness And V1 Limits

- No sleep or no soreness means `coverage_band=insufficient`.
- Missing resting HR or training load means sparse recovery coverage.
- Missing HRV or baseline windows means partial coverage and uncertainty, not
  invented baselines.
- Recovery is not a clinical screen. `escalate_for_user_review` means the
  runtime wants explicit user review, not medical diagnosis.

## Tests

- `verification/tests/test_recovery_classify.py`
- `verification/tests/test_recovery_policy.py`
- `verification/tests/test_source_row_locator_recovery.py`
- `verification/tests/test_recovery_skill_gates.py`
