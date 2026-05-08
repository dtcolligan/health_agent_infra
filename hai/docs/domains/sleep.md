# Sleep Domain

Sleep evaluates last night's sleep and short-term sleep debt so the agent
does not treat poor sleep as a generic note. It is both a direct daily
domain and a cross-domain readiness signal.

## Runtime Surface

| Surface | Path |
|---|---|
| Schemas | `hai/src/health_agent_infra/domains/sleep/schemas.py` |
| Classifier | `hai/src/health_agent_infra/domains/sleep/classify.py` |
| Policy | `hai/src/health_agent_infra/domains/sleep/policy.py` |
| Signals | `hai/src/health_agent_infra/domains/sleep/signals.py` |
| Projector | `hai/src/health_agent_infra/core/state/projectors/sleep.py` |
| Skill | `hai/src/health_agent_infra/skills/sleep-quality/SKILL.md` |

## Evidence And Accepted State

Sleep uses accepted nightly state from wearable-derived sleep rows. The
classifier consumes `sleep_hours`, `sleep_score_overall`, `sleep_awake_min`,
`sleep_start_variance_minutes`, and policy history
`sleep_history_hours_last_7` when available.

In v1 production, `sleep_start_variance_minutes` is normally unavailable
because `sleep_start_ts` is a v1.1 enrichment. Timing consistency therefore
surfaces as `unknown` with `sleep_start_ts_unavailable_in_v1`; this is a known
limit, not a failed sync.

## Classifier Reference

`ClassifiedSleepState` exposes:

| Field | Values |
|---|---|
| `sleep_debt_band` | `none`, `mild`, `moderate`, `elevated`, `unknown` |
| `sleep_quality_band` | `excellent`, `good`, `fair`, `poor`, `unknown` |
| `sleep_timing_consistency_band` | `consistent`, `variable`, `highly_variable`, `unknown` |
| `sleep_efficiency_band` | `excellent`, `good`, `fair`, `poor`, `unknown` |
| `coverage_band` | `full`, `partial`, `sparse`, `insufficient` |
| `sleep_status` | `optimal`, `adequate`, `compromised`, `impaired`, `unknown` |
| `sleep_score` | `0.0..1.0`, or `None` when coverage is insufficient |

No `sleep_hours` means insufficient coverage. Duration-only evidence is
sparse. Duration plus one of score/efficiency is partial. Duration plus score
and efficiency is full; timing consistency is not coverage-gating in v1.

## Policy / R-rules

`SleepPolicyResult` contains `policy_decisions`, optional `forced_action`,
optional `forced_action_detail`, and optional `capped_confidence`.

| Rule id | Effect |
|---|---|
| `require_min_coverage` | Forces `defer_decision_insufficient_signal` when sleep duration is absent. |
| `no_high_confidence_on_sparse_signal` | Caps confidence at `moderate` when only duration is available. |
| `chronic_deprivation_escalation` | Uses the `escalate` decision tier and forces `sleep_debt_repayment_day` when the trailing window shows enough short nights. |

Sleep has no `escalate_for_user_review` action in v1. Chronic deprivation is
represented as a forced remedial sleep action plus an escalation-tier policy
decision.

## Proposal Actions

- `maintain_schedule`
- `prioritize_wind_down`
- `sleep_debt_repayment_day`
- `earlier_bedtime_target`
- `defer_decision_insufficient_signal`

## X-rule Participation

Sleep drives X1a/X1b. Moderate sleep debt can soften hard training-domain
proposals; elevated sleep debt can block hard proposals into escalation. Sleep
state also feeds adjacent recovery/running interpretation.

## Missingness And V1 Limits

- Missing duration is insufficient; no other field can compensate.
- Missing sleep score or awake minutes reduces coverage but does not fabricate
  a score.
- Timing consistency is usually unknown in v1 because production sleep-start
  timestamps are not populated.
- Sleep recommendations are sleep-habit support, not clinical sleep advice.

## Tests

- `hai/verification/tests/test_sleep_classify.py`
- `hai/verification/tests/test_sleep_policy.py`
- `hai/verification/tests/test_sleep_skill_gates.py`
