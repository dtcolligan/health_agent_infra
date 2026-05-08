# Strength Domain

Strength evaluates recent resistance-training volume, muscle-group freshness,
exercise taxonomy confidence, and unmatched exercise tokens. It exists because
strength intake is structurally richer than a free-text workout note.

## Runtime Surface

| Surface | Path |
|---|---|
| Schemas | `hai/src/health_agent_infra/domains/strength/schemas.py` |
| Classifier | `hai/src/health_agent_infra/domains/strength/classify.py` |
| Policy | `hai/src/health_agent_infra/domains/strength/policy.py` |
| Signals | `hai/src/health_agent_infra/domains/strength/signals.py` |
| Intake | `hai/src/health_agent_infra/domains/strength/intake.py` |
| Taxonomy match | `hai/src/health_agent_infra/domains/strength/taxonomy_match.py` |
| Projector | `hai/src/health_agent_infra/core/state/projectors/strength.py` |
| Skill | `hai/src/health_agent_infra/skills/strength-readiness/SKILL.md` |

## Evidence And Accepted State

Strength reads structured `gym_session` and `gym_set` rows, canonical
exercise-taxonomy entries, muscle-group mapping, recent volume history, and
today-only rationale fields. Classifier inputs include
`volume_ratio_7d_vs_28d_week_mean`, `sessions_last_7d`,
`sessions_last_28d`, `days_since_heavy_by_group`,
`unmatched_exercise_tokens`, `today_volume_by_muscle_group`,
`estimated_1rm_today`, and optional `goal_domain`.

`hai intake gym` and the `strength-intake` skill turn user narration into
structured sets. Taxonomy matching is code-owned.

## Classifier Reference

`ClassifiedStrengthState` exposes:

| Field | Values |
|---|---|
| `recent_volume_band` | `very_low`, `low`, `moderate`, `high`, `very_high`, `unknown` |
| `freshness_band_by_group` | per muscle group: `fresh`, `recent`, `fatigued`, `unknown` |
| `coverage_band` | `insufficient`, `sparse`, `partial`, `full` |
| `strength_status` | `progressing`, `maintaining`, `undertrained`, `overreaching`, `unknown` |
| `strength_score` | `0.0..1.0`, or `None` when coverage is insufficient |
| `volume_ratio` | last 7d volume divided by 28d weekly mean, or `None` |
| `unmatched_exercise_tokens` | sorted tuple of unresolved free-text exercise names |

Coverage is based on `sessions_last_28d`: absent or too few sessions are
insufficient, then sparse, partial, and full as history accumulates.

## Policy / R-rules

`StrengthPolicyResult` contains `policy_decisions`, optional
`forced_action`, optional `forced_action_detail`, optional
`capped_confidence`, and cold-start `extra_uncertainty`.

| Rule id | Effect |
|---|---|
| `require_min_coverage` | Forces `defer_decision_insufficient_signal` when strength history is insufficient. |
| `no_high_confidence_on_sparse_signal` | Caps confidence at `moderate` on sparse session history. |
| `volume_spike_escalation` | Forces `escalate_for_user_review` when volume ratio crosses the spike threshold after enough 28d history exists. |
| `unmatched_exercise_confidence_cap` | Caps confidence when unresolved exercise tokens are present. |
| `cold_start_relaxation` | In the first 14 days, may lift the coverage defer only when recovery is not impaired and planned session type explicitly indicates strength. |

## Proposal Actions

- `proceed_with_planned_session`
- `downgrade_to_technique_or_accessory`
- `downgrade_to_moderate_load`
- `rest_day_recommended`
- `defer_decision_insufficient_signal`
- `escalate_for_user_review`

## X-rule Participation

Strength hard proposals can be targeted by X1a/X1b sleep-debt rules, X2
nutrition-underfuelling, X3a/X3b load-spike rules, X5 endurance-fatigue
sequencing, X6a/X6b body-battery rules, and X7 confidence capping. Heavy
lower-body strength history can trigger X4 against running. A hard strength
draft can trigger X9's nutrition protein-target adjustment when it remains
hard after Phase A.

## Missingness And V1 Limits

- No session history means insufficient coverage unless cold-start relaxation
  applies.
- Too little 28d history suppresses the volume-spike escalation rather than
  treating every early session as a spike.
- Unmatched exercise names are intake-quality uncertainty; they cap
  confidence but do not mutate actions by themselves.
- Strength does not generate a lifting program; it adjusts the user's planned
  session or asks for review.

## Tests

- `hai/verification/tests/test_strength_classify.py`
- `hai/verification/tests/test_strength_policy.py`
- `hai/verification/tests/test_strength_cold_start_policy.py`
- `hai/verification/tests/test_strength_projector.py`
- `hai/verification/tests/test_strength_signals.py`
- `hai/verification/tests/test_strength_taxonomy_match.py`
- `hai/verification/tests/test_intake_gym.py`
- `hai/verification/tests/test_synthesis_x3_x4_x5_strength.py`
