# Phase 2.5 — Track A gate: food retrieval prototype

- Date: 2026-04-17
- Author: Claude Opus 4.7 (Phase 2.5 session on branch `rebuild`)
- Branch: `rebuild @ 8ca2ca2` (Phase 2 complete)
- Experiment: `reporting/experiments/nutrition_retrieval_prototype/`

## Gate outcome

**Top-1 strict accuracy: 5/20 = 25%.**
Top-1 generous (match + partial): 11/20 = 55%.

Per the plan's decision rule:

| Range      | Phase 5 scope                              |
|------------|--------------------------------------------|
| ≥80%       | proceed as planned                         |
| 60–80%     | suggest+confirm UX                         |
| **<60%**   | **defer meal-level; ship macros-only**     |

The gate lands firmly in the third bucket on both strict and generous
measures. **Decision: defer meal-level intake; compress Phase 5 to
macros-only plus micronutrient-column expansion.**

## Method summary

- 20 natural-language meal/food-string queries, authored blind to the
  USDA slice. Ground truth (`expected_intent`) written at authoring time.
- Retrieval: transparent alias-aware token-overlap heuristic. Locked
  before any query was scored — no tuning against the 20 queries.
- Slice: USDA SR Legacy 2018-04 CSV, 7793 foods. Real USDA data, not
  hand-curated.
- Manual verdicts: match / partial / miss, with failure-mode tags.

See `reporting/experiments/nutrition_retrieval_prototype/findings.md`
for the full write-up and per-query analysis.

## Why below 60%

Three structural failure classes (not fixable by better tuning):

1. **Aliasing** — user vocabulary (`toast`, `fillet`, `brown rice`,
   `oatmeal`) diverges from USDA naming (`Bread, ..., toasted`;
   `Fish, salmon, ..., filets`; `Rice, brown, ...`;
   `Cereals, oats, ...`). No synonym layer.
2. **Composite meals** — `chicken wrap with cucumber`,
   `peanut butter sandwich`, `coffee with milk` need decomposition
   into component food-strings *before* retrieval. Single-lookup-per-
   meal is structurally wrong.
3. **Brand + processing preference** — generic queries (`greek yogurt`,
   `protein shake`) surface branded or heavily-processed variants
   (Chobani apricot, SlimFast RTD) because the scorer has no way to
   distinguish a "canonical generic" entry from a "specific product"
   entry.

## Scope impact on Phase 5

Drops from Phase 5 scope (move to post-v1 point release):
- `hai intake meal` command
- `meal_log` raw table
- `food_taxonomy` + USDA FDC import (`domains/nutrition/food_db_loader.py`)
- `skills/nutrition-intake/SKILL.md`
- `hai food search` command
- meal-log-vs-daily-macros precedence logic in the projector
- divergence-tracking columns (`meal_log_coverage_band`,
  `daily_macros_vs_meal_log_delta_json`)
- Migration 006 compresses: just the micronutrient column additions

Stays in Phase 5 scope:
- Expand `accepted_nutrition_state_daily` with micronutrient columns
  (nullable; filled when a later release adds meal-level intake)
- `domains/nutrition/classify.py` + `policy.py` against the macros-only
  shape; micronutrients return `unavailable_at_source`
- `skills/nutrition-alignment/SKILL.md`
- X2 + X9 synthesis wiring against macros-only data
- `NutritionProposal` + `NutritionRecommendation` schemas

Phase 5 effort estimate drops from 3 weeks to roughly 1 week.

## Re-gate condition for meal-level

Before meal-level retrieval returns to a release plan:

1. Fix the three structural failure classes (synonym layer,
   composite decomposition in the narration skill, canonical-generic
   preference). `findings.md` item list gives a concrete starting point.
2. Re-run the 20-query gate (plus new adversarial queries).
3. Meal-level proceeds only if strict top-1 ≥ 80%.

## Caveats

- Single session, single scorer. `findings.md` records the bias risk
  explicitly; a re-gate should use a different agent.
- Gate tests retrieval floor with a simple scorer. A production-grade
  retrieval stack would do better — but not enough to move 25% above
  60% without addressing the structural issues above. The failures are
  not rankings-tuning problems.
