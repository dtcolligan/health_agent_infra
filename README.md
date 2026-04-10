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
python3 garmin/import_export.py /path/to/garmin-export.zip
python3 garmin/analyze_export.py
python3 web/app.py
```

Then open `http://localhost:5001/garmin-export` for the first bounded visual + interpretation layer over the normalized export outputs.

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
- `garmin/analyze_export.py` creates a summary, recent trend payload, and conservative interpretation layer from those normalized outputs
- `/garmin-export` renders a product-facing recovery + running overview directly from the local runtime artifacts
- `docs/offline_garmin_export_adapter.md` documents the supported offline ingest path and its limits

## Canonical Health Lab daily snapshot core

The repo now includes a first bounded canonical snapshot layer under `health_model/`.

Inputs:
- Garmin export daily + activity runtime files under `data/garmin/export/`
- manual gym logs in `data/health/manual_gym_sessions.json` using `health_model/manual_gym_sessions.example.json` as the v1 format reference
- nutrition totals from `data/health_log.db` when that SQLite file exists

Run:

```bash
python3 health_model/daily_snapshot.py
```

Outputs:
- `data/health/daily_snapshot_latest.json`
- `data/health/daily_snapshot_YYYY-MM-DD.json`

This v1 snapshot keeps unsupported fields explicit as `null` and separates data-backed observations from generic guidance.

## Shared input backbone proof

The repo now also includes the bounded shared input backbone validator in `health_model/shared_input_backbone.py`.

It implements:
- base canonical model validation for `source_artifact`, `input_event`, `subjective_daily_entry`, and `manual_log_entry`
- semantic checks for the frozen shared-input contract rule set
- a focused proof target in `tests/test_shared_input_backbone.py`

Run:

```bash
python3 -m unittest tests.test_shared_input_backbone
```

## Atomic manual append + regenerate entrypoint

Health Lab now includes a single bounded agent-facing transaction surface in `health_model/agent_interface.py`:

- `append_fragment_and_regenerate_daily_context(...)`
- accepts one validated same-day `meal` or `hydration` fragment
- appends it to the persisted shared-input bundle
- regenerates both `agent_readable_daily_context_YYYY-MM-DD.json` and `agent_readable_daily_context_latest.json` from disk in the same call
- returns the bundle path, dated/latest artifact paths, and accepted provenance ids
- fails closed for invalid, wrong-day, or unsupported fragments without mutating persisted state

Proof:

```bash
python3 -m unittest tests.test_persisted_bundle_append_regenerate
```

## Stable agent-facing submit-and-regenerate CLI

External agents can now drive the same bounded transaction without importing Python directly:

```bash
python3 -m health_model.agent_submit_cli hydration \
  --bundle-path data/health/shared_input_bundle_2026-04-09.json \
  --output-dir data/health \
  --user-id user_1 \
  --date 2026-04-09 \
  --collected-at 2026-04-09T18:20:00+01:00 \
  --ingested-at 2026-04-09T18:20:03+01:00 \
  --raw-location healthlab://manual/hydration/2026-04-09/evening \
  --confidence-score 0.98 \
  --completeness-state complete \
  --amount-ml 750 \
  --beverage-type water \
  --notes "Evening refill after training."
```

```bash
python3 -m health_model.agent_submit_cli meal \
  --bundle-path data/health/shared_input_bundle_2026-04-09.json \
  --output-dir data/health \
  --user-id user_1 \
  --date 2026-04-09 \
  --collected-at 2026-04-09T20:10:00+01:00 \
  --ingested-at 2026-04-09T20:10:04+01:00 \
  --raw-location healthlab://manual/nutrition/2026-04-09/dinner \
  --confidence-score 0.94 \
  --completeness-state complete \
  --note-text "Chicken rice bowl and fruit after run." \
  --meal-label dinner \
  --estimated true
```

Each call returns machine-readable JSON with:

- `ok`
- `bundle_path`
- `dated_artifact_path`
- `latest_artifact_path`
- `accepted_provenance`
- `validation`
- `error`

The CLI fails closed with a non-zero exit code and the same JSON error envelope for invalid payloads, unsupported commands, parser-level argument or choice errors, and timestamp/date mismatches, and leaves the persisted bundle and generated artifacts unchanged on rejection.

## End-to-end external agent write then read flow

An external agent can now write through the submit CLI, then read back the exact scoped daily artifact through a separate read-only CLI without importing Python internals or guessing paths:

```bash
python3 -m health_model.agent_submit_cli hydration \
  --bundle-path data/health/shared_input_bundle_2026-04-09.json \
  --output-dir data/health \
  --user-id user_1 \
  --date 2026-04-09 \
  --collected-at 2026-04-09T18:20:00+01:00 \
  --ingested-at 2026-04-09T18:20:03+01:00 \
  --raw-location healthlab://manual/hydration/2026-04-09/evening \
  --confidence-score 0.98 \
  --completeness-state complete \
  --amount-ml 750 \
  --beverage-type water
```

Then read the dated artifact:

```bash
python3 -m health_model.agent_context_cli get \
  --artifact-path data/health/agent_readable_daily_context_2026-04-09.json \
  --user-id user_1 \
  --date 2026-04-09
```

Or read the latest scoped artifact:

```bash
python3 -m health_model.agent_context_cli get-latest \
  --artifact-path data/health/agent_readable_daily_context_latest.json \
  --user-id user_1
```

The read CLI returns a machine-readable JSON envelope with:

- `ok`
- `artifact_path`
- `context`
- `validation`
- `error`

It fails closed with a non-zero exit code and the same JSON envelope for missing files, invalid JSON, artifact type mismatch, and user/date scope mismatches.

## Voice-note intake proof

The repo also includes a bounded voice-note intake path in `health_model/voice_note_intake.py`.

It implements:
- one transcribed daily voice note to one canonical `source_artifact`
- bounded derived `input_event` extraction with transcript-span provenance
- optional `subjective_daily_entry` generation with explicit confidence

Run:

```bash
python3 -m unittest tests.test_voice_note_intake
```

## Stable daily context artifact entrypoint

The first stable external agent-consumption surface is the artifact writer entrypoint below. It validates a canonical shared-input bundle, fails closed on invalid input, and writes the exact daily context artifact files for `2026-04-09`:

```bash
python3 -m health_model.build_daily_context_artifact \
  --bundle-path tests/fixtures/agent_readable_daily_context/fixture_day_bundle.json \
  --user-id user_1 \
  --date 2026-04-09 \
  --output-dir data/health
```

This writes:

- `data/health/agent_readable_daily_context_2026-04-09.json`
- `data/health/agent_readable_daily_context_latest.json`

## Canonical manual intake to daily context flow

For the bounded manual nutrition + hydration golden path, use `health_model.agent_interface` to submit same-day fragments, merge them, then build the agent-facing daily artifact:

```python
from health_model.agent_interface import (
    build_daily_context,
    merge_bundle_fragments,
    submit_hydration_log,
    submit_nutrition_text_note,
)

hydration = submit_hydration_log(
    user_id="user_1",
    date="2026-04-09",
    amount_ml=750,
    beverage_type="water",
    completeness_state="complete",
    collected_at="2026-04-09T18:20:00+01:00",
    ingested_at="2026-04-09T18:20:03+01:00",
    raw_location="healthlab://manual/hydration/2026-04-09/evening",
    confidence_score=0.98,
)
meal = submit_nutrition_text_note(
    user_id="user_1",
    date="2026-04-09",
    note_text="Chicken rice bowl and fruit after run.",
    meal_label="dinner",
    estimated=True,
    completeness_state="complete",
    collected_at="2026-04-09T20:10:00+01:00",
    ingested_at="2026-04-09T20:10:04+01:00",
    raw_location="healthlab://manual/nutrition/2026-04-09/dinner",
    confidence_score=0.94,
)

bundle = merge_bundle_fragments(existing_bundle, hydration["bundle_fragment"], meal["bundle_fragment"])
context = build_daily_context(bundle=bundle, user_id="user_1", date="2026-04-09")
```

The resulting `agent_readable_daily_context` keeps same-day scoping, preserves provenance IDs in `generated_from`, and exposes grounded nutrition and hydration signals with explicit evidence refs.

## Next steps

- Improve the dashboard and daily readiness views
- Expand the health analytics layer using engineered Garmin features
- Tighten the bridge between offline export outputs and the live-pull feature pipeline
- Add richer coaching logic on top of readiness scoring and subjective recovery signals
- Improve food logging UX and input flexibility
- Tighten deployment/dev setup for easier reproducibility
