# Stress Domain

Stress converts Garmin stress, manual stress, and body-battery trend into a
bounded readiness signal. It prevents the agent from treating sustained high
stress as vague context.

## Runtime Surface

| Surface | Path |
|---|---|
| Schemas | `hai/src/health_agent_infra/domains/stress/schemas.py` |
| Classifier | `hai/src/health_agent_infra/domains/stress/classify.py` |
| Policy | `hai/src/health_agent_infra/domains/stress/policy.py` |
| Signals | `hai/src/health_agent_infra/domains/stress/signals.py` |
| Intake | `hai/src/health_agent_infra/domains/stress/intake.py` |
| Projector | `hai/src/health_agent_infra/core/state/projectors/stress.py` |
| Skill | `hai/src/health_agent_infra/skills/stress-regulation/SKILL.md` |

## Evidence And Accepted State

Stress reads wearable all-day stress and body-battery values where available,
plus manual stress observations recorded through `hai intake stress`.
Classifier inputs include `garmin_all_day_stress`, `manual_stress_score`,
`body_battery_end_of_day`, `body_battery_prev_day`, and
`stress_history_garmin_last_7` for policy evaluation.

Manual stress is a first-class fallback when Garmin stress is absent. Body
battery alone is not enough to anchor the domain.

## Classifier Reference

`ClassifiedStressState` exposes:

| Field | Values |
|---|---|
| `garmin_stress_band` | `low`, `moderate`, `high`, `very_high`, `unknown` |
| `manual_stress_band` | `low`, `moderate`, `high`, `very_high`, `unknown` |
| `body_battery_trend_band` | `improving`, `steady`, `declining`, `depleted`, `unknown` |
| `coverage_band` | `full`, `partial`, `sparse`, `insufficient` |
| `stress_state` | `calm`, `manageable`, `elevated`, `overloaded`, `unknown` |
| `stress_score` | `0.0..1.0`, or `None` when coverage is insufficient |
| `body_battery_delta` | Today minus previous day, or `None` |

Coverage is insufficient when both Garmin and manual stress are absent. A
single direct stress signal without body battery is sparse; one direct signal
plus body battery or both direct signals without body battery is partial.

## Policy / R-rules

`StressPolicyResult` contains `policy_decisions`, optional `forced_action`,
optional `forced_action_detail`, optional `capped_confidence`, and cold-start
`extra_uncertainty`.

| Rule id | Effect |
|---|---|
| `require_min_coverage` | Forces `defer_decision_insufficient_signal` when no direct stress signal is present. |
| `no_high_confidence_on_sparse_signal` | Caps confidence at `moderate` on sparse stress coverage. |
| `sustained_very_high_stress_escalation` | Forces `escalate_for_user_review` when Garmin stress is very high across the configured trailing run. |
| `cold_start_relaxation` | In the first 14 days, an energy self-report can lift the coverage defer at low confidence. |

## Proposal Actions

- `maintain_routine`
- `add_low_intensity_recovery`
- `schedule_decompression_time`
- `escalate_for_user_review`
- `defer_decision_insufficient_signal`

## X-rule Participation

Stress contributes X6a/X6b body-battery rules and X7 confidence capping. Low
body battery can soften hard training-domain proposals; depleted body battery
can block hard proposals. Elevated Garmin stress can cap confidence across
domains.

## Missingness And V1 Limits

- Body battery alone is insufficient because it is an indirect proxy.
- Missing previous-day body battery makes trend unknown but does not block if
  direct stress evidence exists.
- Cold-start relaxation depends on explicit energy self-report; without that,
  the honest answer is still defer.
- Stress guidance is readiness support, not mental-health triage.

## Tests

- `hai/verification/tests/test_stress_classify.py`
- `hai/verification/tests/test_stress_policy.py`
- `hai/verification/tests/test_stress_cold_start_policy.py`
- `hai/verification/tests/test_stress_skill_gates.py`
- `hai/verification/tests/test_synthesis_policy.py`
