# ML Food Logging Pipeline

## What It Does

Full pipeline from natural language food descriptions to calorie and macro estimates, using locally-trained models — no LLM API calls at inference.

```
"had oats and a chicken wrap for lunch"
    → parser splits into items
    → matcher identifies foods in USDA DB
    → portion estimator predicts grams
    → deterministic lookup: grams × per_100g = calories + macros
```

## Pipeline Stages

### 1. Text Parser (NLP) — NOT YET BUILT
Splits a full message into individual food items with portion descriptions.

- Input: `"overnight oats with banana, chicken wrap for lunch"`
- Output: `[("overnight oats", "a bowl"), ("banana", "one"), ("chicken wrap", "one")]`
- Approach: spaCy NER or rule-based segmentation + portion extraction
- Handles: meal labels, conjunctions, lists, implicit portions

### 2. Food Matcher (Embeddings) — NOT YET BUILT
Matches each extracted food item to the nearest entry in the USDA reference database.

- Input: `"chicken caesar wrap"`
- Output: `→ "chicken wrap" (similarity: 0.92)` from foods_reference.csv
- Approach: sentence-transformers embeddings + cosine similarity
- Challenge: composite foods, brand names, UK-specific items
- Food DB: expanding from 126 → 1000+ foods via USDA FoodData Central

### 3. Portion Estimator (GBM) — DONE
Predicts grams from (description, food_name) using engineered features.

```
"a big bowl of rice"  →  ML predicts 323g
```

- **Model**: sklearn HistGradientBoostingRegressor, 300 trees
- **Features**: 14 features — desc_type, container, size_modifier, density_class, etc.
- **Training**: 2,242 synthetic examples from templates × food reference

| Metric | Baseline (rules) | Hybrid (rules + GBM) |
|--------|-------------------|----------------------|
| MAE | 32.7g | 21.4g |
| MAPE | 19.0% | 17.1% |
| Acc@20% | 72.1% | 70.3% |
| Mean calorie error | 41 kcal | 28 kcal |

### 4. Nutrition Lookup — DONE
Deterministic: `grams × per_100g → kcal, protein, carbs, fat`.

Source: `foods_reference.csv`, USDA FoodData Central data.

Same input always produces the same output. No randomness at inference.

## Files

| File | Role | Status |
|------|------|--------|
| `features.py` | 14-feature extraction from (description, food_name) | Done |
| `model.py` | RuleBaseline, GBMModel, HybridModel + training pipeline | Done |
| `portion_estimator.py` | Full grams → USDA macros pipeline | Done |
| `evaluate.py` | Permutation importance, per-type breakdown | Done |
| `data/foods_reference.csv` | 126 foods → expanding to 1000+ | In progress |
| `data/synthetic_gen.py` | Generates training examples from templates | Done |
| `models/gbm_portion.pkl` | Trained portion model artifact | Done |

## Food Reference Database

Current: 126 foods with per-100g macros (USDA FDC, McCance & Widdowson, manufacturer data).

Columns: `food_name, category, calories_per_100g, protein_per_100g, carbs_per_100g, fat_per_100g, typical_serving_g, serving_description, density_class, source, usda_fdc_id`

Expanding to 1000+ foods covering:
- Full USDA FDC common foods
- UK-specific items (Tesco, JCR meals, British dishes)
- Composite/prepared foods (sandwiches, wraps, bowls)
- Snacks, drinks, sauces, condiments

## Training Data

Synthetic, generated from 5 description patterns:
1. **Container**: "a bowl of rice", "a plate of pasta" (28%)
2. **Vague**: "some chicken", "had rice for lunch" (44%)
3. **Metric**: "200g chicken breast" (19%)
4. **Count**: "2 eggs", "3 slices of bread" (8%)
5. **Size-modified**: "a big plate of chicken", "a small bowl of soup"

Future: retrain on real user logs once app is collecting data.

## Design Principles

1. **No LLM at inference** — entire pipeline runs locally with trained models
2. **Deterministic** — same input → same output, always
3. **Modular** — each stage is independently testable and improvable
4. **USDA-grounded** — nutrition values from reference data, not model predictions
5. **Source-tagged** — every estimate carries confidence and source metadata
