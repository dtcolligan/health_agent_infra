# Health Lab

Health Lab is a personal health analytics platform that combines Garmin wearable data, food logging, and lightweight ML models into one system for tracking recovery, nutrition, and day-to-day health trends.

Built as an applied ML + data engineering portfolio project.

## Highlights

- Built an end-to-end health tracking system combining **Garmin biometrics**, **nutrition logging**, and **interactive dashboards**
- Added a **bounded offline Garmin GDPR export adapter**, so the project can produce usable datasets without depending on fragile live login flows
- Trained a **portion-estimation model** to convert natural-language food logs into gram estimates
- Grounded nutrition estimates in **deterministic USDA lookups**, avoiding LLM hallucinated macros at inference time
- Built a **Python + Flask + SQLite** application with a web UI, ML pipeline, and Garmin ingestion flow
- Engineered a personal system that connects **data collection, modelling, storage, and presentation**

## What the system does

Health Lab has two main parts:

1. **Food logging pipeline**
   - Parses food descriptions into structured items
   - Estimates portion size in grams with a trained model
   - Maps foods to USDA references
   - Computes calories and macros via deterministic lookup

2. **Garmin health pipeline**
   - Pulls wearable data from Garmin when live access is available
   - Ingests Garmin GDPR export zips offline when live access is unreliable
   - Cleans and flattens daily metrics
   - Builds engineered features for analysis
   - Exports data into dashboards and analysis workflows

Together, these create a personal health data stack for analysing recovery, nutrition, and behavioural trends.

## Architecture

```text
User input (text)
       |
       v
+------------------------+      +--------------------+
|  Claude API (parsing)  | ---> |  Text Parser       |
|  Identifies food items |      |  Splits into items |
|  + portion descriptions|      |  + portions        |
+------------------------+      +--------+-----------+
                                         |
                                         v
                                +--------+-----------+
                                |  Food Matcher      |
                                |  Fuzzy match to    |
                                |  USDA reference DB |
                                +--------+-----------+
                                         |
                                         v
                                +--------+-----------+
                                | Portion Estimator  |
                                | GBM model          |
                                +--------+-----------+
                                         |
                                         v
                                +--------+-----------+
                                | Nutrition Lookup   |
                                | deterministic USDA |
                                +--------+-----------+
                                         |
                                         v
                                   SQLite + Web UI
```

## Tech stack

| Component | Technology | Notes |
|---|---|---|
| Backend | Python, Flask | REST API serving the web UI |
| ML | scikit-learn HistGradientBoostingRegressor | Portion-size estimation |
| Parsing | Anthropic Claude API | Structured food extraction |
| Nutrition data | USDA FoodData Central | Deterministic calorie/macronutrient lookup |
| Database | SQLite | Single-user local persistence |
| Frontend | Vanilla JS, Chart.js | Mobile-first UI |
| Garmin ingestion | Python + garminconnect | Daily metrics, activities, sleep, HRV |
| Analysis | pandas, NumPy, Jupyter | EDA and model evaluation |

## Project structure

```text
.
├── bot/            # Backend logic and business layer
├── ml/             # Portion-estimation model and data pipeline
├── web/            # Flask app + frontend
├── garmin/         # Garmin ingestion and feature engineering
├── dashboard/      # Dashboard export and standalone dashboard files
├── notebooks/      # Exploratory and evaluation notebooks
└── data/           # Runtime data (git-ignored)
```

## Quickstart

### Requirements

- Python 3.10+
- `pip`
- Anthropic API key for parsing
- Garmin credentials if using the Garmin ingestion pipeline

### Install

```bash
pip install -r requirements.txt
```

### Run the web app

```bash
python web/app.py
```

### Run the Garmin pipeline

Live pull path:

```bash
python garmin/pull_garmin.py
python garmin/clean_garmin.py
python garmin/build_features.py
```

Offline export path:

```bash
python garmin/import_export.py /path/to/garmin-export.zip
python garmin/analyze_export.py
```

The offline path writes derived runtime outputs under `data/garmin/export/` and keeps raw personal export contents out of tracked files.

## Current capabilities

### Shipped
- Food logging with structured parsing
- Portion estimation model
- USDA-based calorie and macro lookup
- SQLite-backed storage
- Web UI for logging and viewing data
- Garmin ingestion and feature-building pipeline
- Offline Garmin export normalization path for messy GDPR exports
- First bounded runtime analysis artifact from normalized export outputs
- Daily readiness / recovery scoring from engineered Garmin features, nutrition logs, and training context
- Dashboard export flow

### Experimental / analysis-facing
- Exploratory notebooks for health and ML analysis
- Iteration on feature engineering and model evaluation
- Ongoing refinement of the health analytics layer

## Why this project is interesting

This repo is not just a notebook or toy model. It demonstrates:
- applied machine learning in a real use case
- data engineering across multiple sources
- product thinking around a usable health tool
- system design from ingestion to UI
- proof-first handling of messy real-world health exports instead of relying on perfect APIs

## Current proof-first Garmin surfaces

- `garmin/import_export.py` normalizes a bounded Garmin GDPR export into runtime datasets
- `garmin/analyze_export.py` creates the first bounded analysis artifact from those normalized outputs
- `docs/offline_garmin_export_adapter.md` documents the supported offline ingest path and its limits

## Next steps

- Improve the dashboard and daily readiness views
- Expand the health analytics layer using engineered Garmin features
- Tighten the bridge between offline export outputs and the live-pull feature pipeline
- Add richer coaching logic on top of readiness scoring and subjective recovery signals
- Improve food logging UX and input flexibility
- Tighten deployment/dev setup for easier reproducibility
