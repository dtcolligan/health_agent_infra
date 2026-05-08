# Nutrition Domain

Nutrition is macros-only in v1. It evaluates calories, protein, hydration,
and target availability without pretending to understand micronutrients,
food taxonomy, meal composition, or diet plans.

## Runtime Surface

| Surface | Path |
|---|---|
| Schemas | `hai/src/health_agent_infra/domains/nutrition/schemas.py` |
| Classifier | `hai/src/health_agent_infra/domains/nutrition/classify.py` |
| Policy | `hai/src/health_agent_infra/domains/nutrition/policy.py` |
| Signals | `hai/src/health_agent_infra/domains/nutrition/signals.py` |
| Intake | `hai/src/health_agent_infra/domains/nutrition/intake.py` |
| Projector | `hai/src/health_agent_infra/core/state/projectors/nutrition.py` |
| Skill | `hai/src/health_agent_infra/skills/nutrition-alignment/SKILL.md` |

## Evidence And Accepted State

Nutrition reads daily macro intake rows and active nutrition target rows.
`hai intake nutrition` records daily macros; `hai target nutrition` writes
four macro target rows (`calories_kcal`, `protein_g`, `carbs_g`, `fat_g`) over
the existing `target` table.

Classifier inputs include `today_row`, `goal_domain`, `is_partial_day`, and
`target_status`. `today_row` is the accepted nutrition row with calories,
protein, carbs, fat, optional hydration, optional meals count, and
`derivation_path`.

## Classifier Reference

`ClassifiedNutritionState` exposes:

| Field | Values |
|---|---|
| `calorie_balance_band` | `met`, `mild_deficit`, `moderate_deficit`, `high_deficit`, `surplus`, `unknown` |
| `protein_sufficiency_band` | `met`, `low`, `very_low`, `unknown` |
| `hydration_band` | `met`, `low`, `unknown` |
| `micronutrient_coverage` | `unavailable_at_source`, `unknown` |
| `coverage_band` | `insufficient`, `sparse`, `partial`, `full` |
| `nutrition_status` | `aligned`, `deficit_caloric`, `protein_gap`, `under_hydrated`, `surplus`, `unknown`, `insufficient_data` |
| `nutrition_score` | `0.0..1.0`, or `None` when coverage is insufficient |
| `calorie_deficit_kcal`, `protein_ratio`, `hydration_ratio` | Derived numeric audit fields, or `None` |

For `derivation_path='daily_macros'`, micronutrients are always
`unavailable_at_source`. That is the only legitimate v1 derivation path.

## Policy / R-rules

`NutritionPolicyResult` contains `policy_decisions`, optional
`forced_action`, optional `forced_action_detail`, and optional
`capped_confidence`.

| Rule id | Effect |
|---|---|
| `require_min_coverage` | Forces `defer_decision_insufficient_signal` when no accepted nutrition row exists or macros are malformed. |
| `no_high_confidence_on_sparse_signal` | Caps confidence at `moderate` when hydration or meals-count optional fields are missing. |
| `extreme_deficiency_escalation` | Forces `escalate_for_user_review` when calorie deficit and protein ratio are both extreme after the partial-day gate allows evaluation. |

The extreme-deficiency rule suppresses escalation when the user has only
logged too few meals and the day is not over. A breakfast-only day should not
look like a full-day deficiency.

## Proposal Actions

- `maintain_targets`
- `increase_protein_intake`
- `increase_hydration`
- `reduce_calorie_deficit`
- `defer_decision_insufficient_signal`
- `escalate_for_user_review`

## X-rule Participation

Nutrition underfuelling can soften hard recovery and strength proposals
through X2. Running is intentionally not an X2 target in v1.

Hard training-domain drafts can cause X9 to append a protein-target
adjustment to a nutrition recommendation's `action_detail` without changing
the nutrition action. Phase B guards enforce that action-detail-only write
surface.

## Missingness And V1 Limits

- No nutrition row or malformed macro row means insufficient coverage.
- Present macros with neither hydration nor meals count is sparse; one optional
  field is partial; both optional fields is full.
- `is_partial_day=True` with `target_status` of `absent` or `unavailable`
  short-circuits to `nutrition_status='insufficient_data'` with
  `partial_day_no_target` uncertainty.
- Meal-level intake, food taxonomy, micronutrients, body-composition targets,
  and autonomous diet plans are out of scope for v1.

## Tests

- `hai/verification/tests/test_nutrition_classify.py`
- `hai/verification/tests/test_nutrition_policy.py`
- `hai/verification/tests/test_nutrition_skill_gates.py`
- `hai/verification/tests/test_partial_day_nutrition_gate.py`
- `hai/verification/tests/test_synthesis_x2_x9_nutrition.py`
