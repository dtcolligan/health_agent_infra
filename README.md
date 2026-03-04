# Health Lab

A personal health tracking platform that combines Garmin wearable data with an ML-powered food logging system. The food logger accepts natural language input and estimates calories and macronutrients using locally-trained models grounded in USDA nutritional data -- no external LLM calls at inference time.

Built as an applied ML and data engineering portfolio project.

## Architecture

```
User input (text)
       |
       v
+------------------------+      +--------------------+
|  Claude API (parsing)  | ---> |  Text Parser       |
|  Identifies food items |      |  Splits into items  |
|  + portion descriptions|      |  + portions         |
+------------------------+      +--------+-----------+
                                         |
                                         v
                                +--------+-----------+
                                |  Food Matcher       |
                                |  Fuzzy match to     |
                                |  USDA reference DB  |
                                +--------+-----------+
                                         |
                                         v
                                +--------+-----------+
                                |  Portion Estimator  |
                                |  GBM model (21g MAE)|
                                |  description -> g   |
                                +--------+-----------+
                                         |
                                         v
                                +--------+-----------+
                                |  Nutrition Lookup   |
                                |  grams x per_100g   |
                                |  -> kcal, P, C, F   |
                                +--------+-----------+
                                         |
                                         v
                                   SQLite + Web UI
```

The ML model's only job is estimating portion size in grams. All nutritional values (calories, protein, carbs, fat per 100g) come from USDA FoodData Central and are deterministic lookups. Same input always produces the same output.

## Tech Stack

| Component | Technology | Notes |
|---|---|---|
| Backend | Python, Flask | REST API serving the web UI |
| ML (portion estimation) | scikit-learn HistGradientBoostingRegressor | 14 engineered features, 2242 training examples |
| NLP (parsing) | Anthropic Claude API (tool use) | Structured extraction via function calling |
| Nutrition data | USDA FoodData Central | 126 foods with per-100g macros |
| Database | SQLite | Single-user, WAL mode |
| Frontend | Vanilla JS, Chart.js | Mobile-first responsive UI |
| Garmin pipeline | garminconnect (Python) | Daily metrics, activities, sleep, HRV |
| Data analysis | pandas, NumPy, Jupyter | EDA notebooks for Garmin and ML data |

## Project Structure

```
.
├── bot/                    # Core backend logic
│   ├── config.py           #   Environment config, day boundary logic
│   ├── db.py               #   SQLite schema, data access layer
│   ├── parser.py           #   Claude API integration, ML refinement
│   ├── formatter.py        #   Response formatting
│   └── service.py          #   Business logic layer
│
├── ml/                     # ML pipeline (portion estimation)
│   ├── model.py            #   RuleBaseline, GBM, HybridModel + training
│   ├── features.py         #   14-feature extraction from descriptions
│   ├── portion_estimator.py#   Full grams -> macros pipeline
│   ├── evaluate.py         #   Permutation importance, per-type breakdown
│   ├── data/
│   │   ├── foods_reference.csv   # 126 foods, USDA sourced
│   │   ├── synthetic_gen.py      # Training data generator
│   │   ├── build_foods_db.py     # USDA DB builder
│   │   └── pull_usda.py          # USDA FoodData Central API
│   └── models/
│       └── gbm_portion.pkl       # Trained model artifact
│
├── web/                    # Flask web application
│   ├── app.py              #   Routes and API endpoints
│   └── static/
│       └── index.html      #   Single-page app (mobile-first)
│
├── garmin/                 # Garmin data pipeline
│   ├── pull_garmin.py      #   Pull daily metrics + activities
│   ├── clean_garmin.py     #   Extract flat daily features from raw JSON
│   └── build_features.py   #   ML-ready feature engineering
│
├── dashboard/              # Health dashboard
│   ├── dashboard.html      #   Standalone HTML dashboard
│   └── export_data.py      #   SQLite + CSV -> dashboard JSON
│
├── notebooks/              # Exploratory analysis
│   ├── eda_notebook.ipynb          # Garmin data EDA
│   ├── analysis_01_baseline.ipynb  # Baseline health metrics analysis
│   ├── ml_01_eda.ipynb             # ML training data exploration
│   └── ml_02_model_eval.ipynb      # Model evaluation and comparison
│
├── data/                   # Runtime data (git-ignored)
│   ├── health_log.db       #   SQLite database
│   └── garmin/             #   Raw + clean Garmin data
│
├── requirements.txt
├── .env.example
└── health-logger-project-brief.md
```

## Component Status

| Component | Status | Description |
|---|---|---|
| Portion estimator (ML) | Working | Hybrid model: 21g MAE, 70% accuracy within 20% of true weight |
| Food reference DB | Working (126 foods) | USDA-sourced per-100g macros. Expansion to 1000+ foods planned |
| Web UI | Working | Mobile-first Flask app with Chart.js charts, daily/weekly views |
| Garmin data pipeline | Working | 60-day daily pulls: sleep, HRV, stress, body battery, activities |
| Dashboard | Working | HTML dashboard with Garmin + nutrition data overlay |
| SQLite data layer | Working | Multi-user schema, WAL mode, audit trail |
| Text parser (NLP) | Planned | Splits full messages into individual food items. Currently handled by Claude API |
| Food matcher (embeddings) | Planned | Sentence-transformer similarity matching to USDA DB |

## ML Model Performance

Portion estimation evaluated on a held-out test set (n=337):

| Model | MAE | MAPE | Accuracy (within 20%) |
|---|---|---|---|
| Rule baseline | 32.7g | 19.0% | 72.1% |
| GBM (HistGBR) | 23.0g | 18.3% | 69.4% |
| Hybrid (rules + GBM) | 21.4g | 17.1% | 70.3% |

The hybrid model routes metric descriptions (e.g. "200g chicken") through rules and everything else through the gradient boosted model. Mean calorie error: 28 kcal.

## Setup

```bash
# Clone and set up environment
git clone git@github.com:dtcolligan/garmin_lab.git
cd garmin_lab
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Initialize database and start the web app
python -m bot.main
python -m web.app
# Open http://localhost:5001
```

## Key Design Decisions

1. **No LLM at inference for nutrition**: The ML pipeline runs locally with trained models. Claude is used only for parsing natural language into structured data, not for estimating calories.
2. **USDA-grounded nutrition**: Macro values come from USDA FoodData Central, not model predictions. The model predicts *what* and *how much* -- nutrition per 100g is a deterministic lookup.
3. **Hybrid ML pipeline**: Each stage (parsing, matching, portion estimation) is a separate module. Easier to debug, evaluate, and improve individually.
4. **Accuracy vs friction tradeoff**: Accept +/-15-20% calorie estimation error in exchange for zero-friction natural language input.

## License

This project is not currently licensed for reuse.
