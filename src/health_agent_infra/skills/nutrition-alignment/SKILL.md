---
name: nutrition-alignment
description: Produce a bounded NutritionProposal for today by consuming the runtime-computed `classified_state` + `policy_result` and applying judgment-only steps — action matrix, rationale prose, honest handling of micronutrient unavailability. The runtime already did every band, every score, and every R-rule; this skill does not re-derive them. Macros-only v1 per the Phase 2.5 retrieval-gate outcome.
allowed-tools: Read, Bash(hai state snapshot *), Bash(hai state read *), Bash(hai propose *)
disable-model-invocation: false
---

# Nutrition Alignment

All arithmetic happens in code. Your job is: read the bundle, honour the policy result, pick an action, write the rationale, persist.

## Load the bundle

```
hai state snapshot --as-of <today> --user-id <u> --evidence-json <hai clean output>
```

Under `snapshot.nutrition` you receive these blocks:

- `today` — today's `accepted_nutrition_state_daily` row (calories, protein_g, carbs_g, fat_g, hydration_l, meals_count, derivation_path), or null.
- `history` — trailing rows for lookback context.
- `signals` — runtime-derived dict the classifier consumed: `today_row`, `goal_domain`. Context only; never re-derive.
- `classified_state` — `calorie_balance_band`, `protein_sufficiency_band`, `hydration_band`, `micronutrient_coverage`, `coverage_band`, `nutrition_status`, `nutrition_score`, `calorie_deficit_kcal`, `protein_ratio`, `hydration_ratio`, `derivation_path`, `uncertainty`. **Source of truth.**
- `policy_result` — `policy_decisions[]`, `forced_action`, `forced_action_detail`, `capped_confidence`. **Source of truth.**
- `missingness` — per state_model_v1.md §5.

## Protocol

### 1. If the policy forced an action, use it

If `policy_result.forced_action` is set, `action` is that value and `action_detail` is `policy_result.forced_action_detail`. Confidence: `low` for `defer_decision_insufficient_signal`, else `moderate`. Skip the action matrix; jump to rationale.

Specifically:
- `defer_decision_insufficient_signal` → R-coverage fired (no row / macros missing); record the decision verbatim.
- `escalate_for_user_review` → R-extreme-deficiency fired (big calorie gap AND very-low protein on the same day); record `calorie_deficit_kcal` + `protein_ratio` in `action_detail` so the user can inspect.

### 2. Otherwise, pick from the action matrix

Keyed on `classified_state.nutrition_status`:

| status | action + action_detail |
|---|---|
| `aligned` | `maintain_targets` |
| `deficit_caloric` | `reduce_calorie_deficit` with `{"reason_token": "<calorie_balance_band>", "calorie_deficit_kcal": <value>}` — the band names the severity (moderate_deficit or high_deficit) |
| `protein_gap` | `increase_protein_intake` with `{"reason_token": "<protein_sufficiency_band>", "protein_ratio": <value>}` |
| `under_hydrated` | `increase_hydration` with `{"hydration_ratio": <value>}` |
| `surplus` | `maintain_targets` with `{"caveat": "calorie_surplus_trend"}` — surplus alone does not force a correction, only surfaces for awareness |

### 3. Confidence

Default from `classified_state.coverage_band`: `full → high`, `partial → moderate`, `sparse → moderate`, `insufficient → low`. If `policy_result.capped_confidence` is set, it lowers the default but never raises it.

### 4. Micronutrient honesty

`classified_state.micronutrient_coverage` is always `unavailable_at_source` in v1 because the daily-macros derivation carries no micronutrient evidence. Do not surface any claim about a specific micronutrient's status — no nutrient-name-qualified "low," "inadequate," or "deficient" prose, no mineral-ratio commentary. Those signals are structurally unavailable until a later release lands meal-level intake. The only allowable micronutrient-adjacent mention is the honest one: `micronutrients_unavailable_at_source` is already on `classified_state.uncertainty`; carry it through so downstream knows this domain's proposal speaks only to macros + hydration.

### 5. Rationale (4–7 lines)

One line per band or signal that informed the decision. Name the band; do not re-derive it.

Examples: `calorie_balance_band=<band>` with `calorie_deficit_kcal=<value>`, `protein_sufficiency_band=<band>` with `protein_ratio=<value>`, `hydration_band=<band>`, `nutrition_status=<status>`, `extreme_deficiency_detected` (if R-extreme-deficiency fired), `micronutrients_unavailable_at_source` (always, in v1).

### 6. Uncertainty

Start with `classified_state.uncertainty` (already sorted + deduped). Append any tokens you added (e.g. `*_unavailable_at_source` derived from the snapshot's `missingness` token). Re-sort alphabetically; deduplicate. `micronutrients_unavailable_at_source` is already included by the classifier under v1; do not duplicate it.

### 7. Follow-up

Nutrition emits a `NutritionProposal`, not a recommendation, so it has no `follow_up` field. Synthesis assigns review semantics per finalised plan. Skip this step.

On `defer_decision_insufficient_signal`, synthesis uses the nutrition-domain template `"How did yesterday's eating go? Anything worth logging as macros?"` (owned by `core.narration.templates.DEFER_REVIEW_QUESTION_TEMPLATES`).

## X9 post-adjust contract

After synthesis commits the training recommendation, Phase B runs X9: if the final training action is a hard session, the runtime appends a protein/carb-target bump to the nutrition recommendation's `action_detail` — NOT to the `action`. This is runtime-owned; the skill must not second-guess it or fold its effect into the proposal. The proposal you emit is the pre-synthesis view; the X9 adjustment lives downstream, run by the runtime after synthesis.

## Output

Emit a `NutritionProposal` JSON and call `hai propose --domain nutrition --proposal-json <path>`. The propose tool validates the shape and appends to `proposal_log`; it is your determinism check.

`proposal_id` = `prop_<for_date>_<user_id>_nutrition_01` (idempotent on `(for_date, user_id, domain)`; re-running on the same day does not produce a new row).

Copy `policy_result.policy_decisions` into the output's `policy_decisions` verbatim — the runtime decided them; you do not re-edit or add new ones.

## Invariants

- You never compute a band, a score, a ratio, or a deficit. `classified_state` is the source of truth.
- You never evaluate an R-rule (require_min_coverage, no_high_confidence_on_sparse_signal, extreme_deficiency_escalation). `policy_result` is the source of truth; you honour `forced_action` and `capped_confidence`.
- You never apply X-rule mutations. Synthesis owns all cross-domain reasoning (X2 nutrition deficit softens strength/recovery; X9 training intensity bumps nutrition targets post-commit). This skill emits one domain's bounded proposal; synthesis mutates the draft mechanically, based on `x_rule_firing` rows, before the skill ever sees it as "final."
- You never emit an `action` outside the v1 enum (`maintain_targets`, `increase_protein_intake`, `increase_hydration`, `reduce_calorie_deficit`, `defer_decision_insufficient_signal`, `escalate_for_user_review`). `hai propose` enforces this.
- You never fabricate micronutrient claims. The data layer does not carry that evidence in v1; silence about micros is the honest state.
- You never fabricate values for missing evidence; missing stays missing (a missing hydration log is `unknown`, not `low`).
- If a decision isn't reasoned in `rationale[]` or `policy_decisions[]`, it didn't happen.
