# Running Domain

Running decides whether today's planned run is appropriate given recent
running load, freshness, hard-session density, and adjacent recovery signals.
It is a bounded daily-readiness domain, not a training-plan generator.

## Runtime Surface

| Surface | Path |
|---|---|
| Schemas | `src/health_agent_infra/domains/running/schemas.py` |
| Classifier | `src/health_agent_infra/domains/running/classify.py` |
| Policy | `src/health_agent_infra/domains/running/policy.py` |
| Signals | `src/health_agent_infra/domains/running/signals.py` |
| Projector | `src/health_agent_infra/core/state/projectors/running_activity.py` plus accepted daily projection in `core/state/projector.py` |
| Skill | `src/health_agent_infra/skills/running-readiness/SKILL.md` |

## Evidence And Accepted State

Running uses accepted daily running rollups and per-session
`running_activity` rows when available. The classifier consumes precomputed
signals: `weekly_mileage_m`, `weekly_mileage_baseline_m`,
`weekly_mileage_ratio`, `recent_hard_session_count_7d`, `acwr_ratio`,
`activity_count_14d`, `training_readiness_pct`, `sleep_debt_band`, and
`resting_hr_band`.

Adjacent recovery inputs let the running domain reason about readiness without
duplicating recovery classification.

## Classifier Reference

`ClassifiedRunningState` exposes:

| Field | Values |
|---|---|
| `weekly_mileage_trend_band` | `very_low`, `low`, `moderate`, `high`, `very_high`, `unknown` |
| `hard_session_load_band` | `none`, `light`, `moderate`, `heavy`, `unknown` |
| `freshness_band` | `fresh`, `neutral`, `fatigued`, `overreaching`, `unknown` |
| `recovery_adjacent_band` | `favourable`, `neutral`, `compromised`, `unknown` |
| `coverage_band` | `full`, `partial`, `sparse`, `insufficient` |
| `running_readiness_status` | `ready`, `conditional`, `hold`, `unknown` |
| `readiness_score` | `0.0..1.0`, or `None` when coverage is insufficient |

Coverage is insufficient when the runtime cannot establish a mileage trend.
Structural activity can relax baseline requirements when enough recent
activities exist, but absent mileage remains a defer signal.

## Policy / R-rules

`RunningPolicyResult` contains `policy_decisions`, optional
`forced_action`, optional `forced_action_detail`, optional
`capped_confidence`, and cold-start `extra_uncertainty`.

| Rule id | Effect |
|---|---|
| `require_min_coverage` | Forces `defer_decision_insufficient_signal` when required running inputs are missing. |
| `no_high_confidence_on_sparse_signal` | Caps confidence at `moderate` when ACWR/freshness is missing. |
| `acwr_spike_escalation` | Forces `escalate_for_user_review` when ACWR reaches the spike threshold. |
| `cold_start_relaxation` | In the first 14 days, may lift the coverage defer when recovery is not impaired and a planned session type is present; confidence remains capped. |

## Proposal Actions

- `proceed_with_planned_run`
- `downgrade_intervals_to_tempo`
- `downgrade_to_easy_aerobic`
- `cross_train_instead`
- `rest_day_recommended`
- `defer_decision_insufficient_signal`
- `escalate_for_user_review`

## X-rule Participation

Running hard proposals can be targeted by X1a/X1b sleep-debt rules, X3a/X3b
load-spike rules, X4 lower-body sequencing, X6a/X6b body-battery rules, and
X7 confidence capping. A hard running draft can trigger X9's nutrition
protein-target adjustment.

X2 intentionally does **not** target running in v1. Nutrition
underfuelling softens strength and recovery only; endurance fuelling is a
separate product question.

## Missingness And V1 Limits

- Missing weekly mileage or baseline generally means insufficient coverage,
  with the structural-activity relaxation noted above.
- Missing ACWR means sparse coverage and a confidence cap.
- Missing hard-session history or recovery-adjacent inputs means partial
  coverage.
- Running does not prescribe a training plan; it adjusts or escalates the
  user's planned run.

## Tests

- `verification/tests/test_running_classify.py`
- `verification/tests/test_running_policy.py`
- `verification/tests/test_running_cold_start_policy.py`
- `verification/tests/test_running_skill_gates.py`
- `verification/tests/test_synthesis_x3_x4_x5_strength.py`
- `verification/tests/test_synthesis_x2_x9_nutrition.py`
