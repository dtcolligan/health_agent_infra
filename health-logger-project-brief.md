# Project: ML-Powered Food Logger

## Concept

A food logging app where users type or speak what they ate, and a **locally-trained ML pipeline** parses the input and estimates calories and macros — no external LLM API calls at inference time.

The core ML challenge: turn unstructured natural language food descriptions into structured nutrition estimates, using models trained on USDA data and synthetic + real user logs.

## Core Problem

Health tracking today has two failure modes:
- **Manual logging apps** (MyFitnessPal, Cronometer) require per-meal, per-item entry. High friction → low adherence.
- **LLM-powered alternatives** depend on expensive API calls per message, aren't reproducible, and don't let you own the model.

This project builds an **offline-capable, self-trained ML pipeline** that handles the full estimation — from raw text to calories and macros — with no external API dependency at inference.

## Architecture

```
User input (text or voice)
        │
        ▼
┌──────────────────────────┐
│  Text Parser (NLP)       │  Splits message into individual food items
│  - Meal segmentation     │  + portion descriptions
│  - Item extraction       │  "oats and a wrap for lunch" → [("oats","a bowl"), ("wrap","one")]
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Food Matcher            │  Sentence embeddings → cosine similarity
│  (embedding similarity)  │  Matches item to nearest food in USDA DB
│                          │  "chicken caesar wrap" → closest entry in 1000+ food DB
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Portion Estimator       │  GBM (already trained, 21g MAE)
│  (existing ml/model.py)  │  "a big bowl" + density_class → grams
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Nutrition Lookup        │  Deterministic: grams × per_100g
│  (foods_reference.csv)   │  → calories, protein, carbs, fat
└──────────────────────────┘
           │
           ▼
       SQLite → Web UI (daily totals, charts)
```

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Interface | Web app (Flask + vanilla JS) | Already built, mobile-first responsive UI |
| Text parsing | spaCy / custom NLP | Splits messages into food items, no API needed |
| Food matching | sentence-transformers | Embed descriptions, match to USDA food DB via cosine similarity |
| Portion estimation | sklearn HistGradientBoostingRegressor | Already trained, handles portion ambiguity |
| Nutrition data | USDA FoodData Central | 1000+ foods with per-100g macros |
| Database | SQLite | Single-user local app |
| Backend | Python (Flask) | Existing stack |
| Voice input | Whisper (local) or browser Speech API | Transcription → same text pipeline |

## Key Design Decisions

1. **No LLM at inference**: The entire pipeline runs locally with trained models. Claude is only used during training data generation if needed, never at runtime.
2. **Accuracy vs friction tradeoff**: Accept ±15-20% calorie estimation error in exchange for zero-friction input. Directional accuracy over precision.
3. **Hybrid ML pipeline**: Each stage (parsing, matching, portion estimation) is a separate model/module. Easier to debug, evaluate, and improve individually.
4. **USDA-grounded nutrition**: Macro values come from USDA FoodData Central, not model predictions. The model predicts *what* and *how much* — nutrition per 100g is a lookup.
5. **Source tagging**: Every data point tagged with its source and confidence level.

## Build Phases

### Phase 1: Food Database & Training Data
- Expand `foods_reference.csv` from 126 → 1000+ foods using USDA FoodData Central.
- Cover UK-specific foods (JCR meals, Tesco items, common British dishes).
- Generate synthetic training pairs: (description, food_name, grams).

### Phase 2: Food Matching Model
- Embed all foods in the reference DB using sentence-transformers.
- Train/evaluate a retrieval model: text description → nearest food match.
- Handle composite foods ("chicken caesar wrap" → multiple ingredients or single entry).

### Phase 3: Text Parser (NLP)
- Parse full messages into individual food items with portion descriptions.
- Handle meal labels ("for breakfast", "at lunch"), conjunctions, lists.
- Extract portion modifiers ("big bowl", "two slices", "200g").

### Phase 4: Integration & Web UI
- Wire the full pipeline: text → parser → matcher → portion → nutrition → SQLite.
- Web UI already exists — connect it to the new ML pipeline instead of Claude API.
- Voice input via browser Speech API or Whisper.

### Phase 5: Real Data & Retraining
- Collect real user logs through the app.
- Retrain models on actual (description → food, portion) pairs.
- Evaluate improvement over synthetic-only training.

## Existing Assets

| Asset | Status |
|-------|--------|
| Web UI (`web/`) | Working — Flask app, mobile-first, Chart.js charts |
| Portion estimator (`ml/`) | Trained — GBM, 21g MAE, 70% Acc@20% |
| Foods reference DB | 126 foods — needs expansion to 1000+ |
| SQLite schema (`bot/db.py`) | Working — meal_items, daily_summary, targets |
| Garmin data pipeline | Working — daily metrics, activities, EDA notebooks |
| Dashboard | Working — HTML dashboard with export pipeline |

## Context
- Builder: Dom Colligan, Year 1 at Imperial, Python-primary, learning ML/DL.
- Personal use case: interested in nutrition tracking but finds existing apps too high-friction.
- Portfolio project demonstrating NLP, ML, data engineering, and applied ML.
