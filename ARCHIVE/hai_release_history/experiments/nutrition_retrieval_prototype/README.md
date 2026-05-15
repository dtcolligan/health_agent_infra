# Nutrition Retrieval Prototype — Phase 2.5 Track A

Disposable experiment. Tests food-string → candidate food match quality
against a real USDA slice, before Phase 5 commits to meal-level intake.

## Contents

- `queries.json` — 20 realistic meal/food narration queries (authored
  blind to the slice; ground truth in `expected_intent` field)
- `usda_sr_legacy_food.csv` — USDA SR Legacy slice (7793 foods,
  2018-04 publication, public domain)
- `usda_sr_legacy_food_category.csv` — USDA food category lookup
- `search.py` — transparent retrieval heuristic (alias-aware token
  overlap + phrase bonus, no fuzzy distance)
- `run.py` — runs all queries, writes `results.json`
- `results.json` — raw top-5 per query
- `scoring.json` — manual verdict (match/partial/miss) + failure mode
  per query
- `findings.md` — prose write-up

## Reproduce

    python3 run.py

## Status

Complete. See `findings.md` for the gate decision.
Gate document: `../../plans/historical/phase_2_5_retrieval_gate.md`.
