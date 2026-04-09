# Health Lab repo transformation plan

Date: 2026-04-09
Status: first transformation plan

## Objective

Transform the current `garmin_lab` GitHub project into the broader `Health Lab` project.

Execution locks from Dom:
- this should become the new version of the existing `garmin_lab` repo, not a separate new repo
- Health Lab can be public from the start
- gym v1 should use manual structured logs inside Health Lab
- nutrition v1 should start from the existing food pipeline and be improved/tailored as needed
- build Health Lab first, then connect it to ClawSuite afterward
- optimize in a balanced way, with priority on daily usefulness, then strong GitHub/readme/demo, then ML sophistication, then technical depth

This is not a cosmetic rename only.
The repo should be reshaped so the product identity, structure, ingestion model, and outputs all reflect a broader health system covering:
- sleep
- running
- gym
- food
- recovery/readiness

Garmin should become one input adapter rather than the defining identity of the whole repository.

## Why this transformation is needed

Current truth:
- the README already describes a broader health product
- food logging is already first-class
- nutrition ML already exists
- Garmin export and live ingestion are already only one part of the repo

But the structure is still biased toward Garmin:
- a top-level `garmin/` module remains central
- dashboards and proof surfaces are Garmin-named
- some outputs still imply a Garmin-first project identity
- the next ingestion gap, gym data, does not fit cleanly into a Garmin-shaped mental model

So the repo is already partly Health Lab in substance, but not yet in structure.

## Transformation goals

1. make `Health Lab` the explicit product identity everywhere
2. preserve Garmin work as a valuable ingestion adapter
3. elevate food logging and nutrition to equal first-class pillars
4. add a clean place for gym ingestion and lifting data
5. add a unified daily health model that can feed ClawSuite
6. improve portfolio clarity so the repo reads as a coherent health system rather than a wearable side-project plus food tooling

## Desired end-state

The repo should read like this:

- Health Lab is the product
- data sources feed Health Lab
- health domains are the organizing structure
- ClawSuite-facing daily health outputs are explicit deliverables

## Recommended architectural shift

### From provider-shaped
Current rough shape:
- `garmin/` as central health engine
- food pipeline beside it
- dashboards partly Garmin-specific

### To domain-shaped
Target rough shape:
- health domains and canonical outputs at the center
- data-source adapters beneath them
- Garmin as one adapter
- gym/manual lifting input as another adapter
- nutrition pipeline as another adapter

## Recommended target structure

This does **not** all need to be done in one pass, but this is the target direction.

```text
.
├── adapters/
│   ├── garmin/
│   ├── gym/
│   └── nutrition/
├── domains/
│   ├── sleep/
│   ├── training/
│   ├── nutrition/
│   └── recovery/
├── health_model/
│   ├── daily_snapshot.py
│   ├── readiness.py
│   └── schemas/
├── web/
├── dashboard/
├── ml/
├── docs/
└── data/
```

If a lighter migration is preferred, an acceptable intermediate shape is:

```text
.
├── garmin/          # keep for now, but explicitly as an adapter layer
├── gym/             # new structured gym ingestion/logging layer
├── nutrition/       # optional extraction from bot/ml over time
├── health_model/    # new canonical unified outputs
├── web/
├── dashboard/
├── ml/
├── docs/
└── data/
```

## Transformation phases

### Phase 1 — identity and contract correction
Goal:
- make the repo direction explicit before large code movement

Tasks:
- update README so the project identity is unmistakably Health Lab
- document Garmin as an adapter/input source
- document gym ingestion as a required new input path
- document the canonical daily health model
- keep existing code working

Definition of done:
- a new reader understands this as a health platform, not a Garmin-only project

### Phase 2 — canonical data model introduction
Goal:
- create the unified Health Lab layer without breaking current flows

Tasks:
- add a shared schema for:
  - daily health snapshot
  - sleep daily
  - training session
  - gym set log
  - nutrition daily
  - readiness daily
- add one generator that produces a daily snapshot from available inputs
- keep unsupported inputs explicitly null / missing, not fabricated

Definition of done:
- one schema-backed daily health snapshot artifact exists

### Phase 3 — adapter reframing
Goal:
- reclassify Garmin as one adapter instead of the main product engine

Tasks:
- rename/document `garmin/` as adapter-oriented in code and docs
- preserve live pull + offline export ingest
- route adapter outputs into the canonical Health Lab model
- keep Garmin-specific analysis surfaces only where they are still useful as diagnostics or proofs

Definition of done:
- Garmin outputs feed the shared health model instead of acting like the final product shape

### Phase 4 — gym ingestion introduction
Goal:
- add the first non-Garmin training ingestion path

Tasks:
- create manual gym session + set logging surface
- define minimal v1 required fields:
  - exercise name
  - set number
  - reps
  - weight
- add optional fields later:
  - RPE / RIR
  - notes
  - lift focus
- roll gym sessions into training and daily snapshot outputs

Definition of done:
- one real logged gym session can appear in the unified health model

### Phase 5 — nutrition surface cleanup
Goal:
- ensure food/nutrition reads as a first-class pillar, not a sidecar

Tasks:
- decide whether `bot/` remains the long-term package name or should be gradually renamed/split
- make nutrition outputs map directly into `nutrition_daily`
- expose nutrition summaries to the main health outputs

Definition of done:
- nutrition is visibly part of the main health model and daily surface

### Phase 6 — ClawSuite-facing outputs
Goal:
- make the repo useful to daily mission control

Tasks:
- create a compact daily output artifact specifically meant for ClawSuite
- include:
  - sleep summary
  - readiness/recovery summary
  - running summary
  - gym summary
  - food summary
  - one data-backed observation
  - one clearly labeled generic suggestion

Definition of done:
- one generated health summary can be rendered directly in ClawSuite

## Recommended naming decisions

### Product name
- `Health Lab`

### Keep vs change
- keep `garmin` only if explicitly treated as the Garmin adapter module
- add `gym` as a new ingestion/logging module
- consider introducing `health_model` or `healthlab` as the canonical integration layer

### Dashboards
- treat `dashboard/garmin_export.html` as a transitional proof artifact
- long-term direction should be a broader health dashboard / daily health surface

## Code movement recommendation

Do **not** start with a giant rename/refactor across the whole repo.
That is a good way to create noise and break proof.

Better order:
1. introduce the shared health model first
2. plug current Garmin outputs into it
3. add gym logging into it
4. plug food outputs into it
5. only then rename/move modules where it materially improves clarity

## Immediate next concrete build target

Create the first canonical Health Lab daily snapshot artifact from:
- Garmin export-derived inputs
- current nutrition outputs where available
- placeholder/manual gym inputs

Suggested artifact examples:
- `data/health/daily_snapshot.json`
- `data/health/daily_snapshot.csv`

This gives the repo a real Health Lab center of gravity before deeper refactors.

## Recommended first execution packet after this plan

1. implement `health_model/` with the daily snapshot schema
2. build a generator that maps current Garmin export outputs into that snapshot
3. add a minimal manual gym-log input file format
4. add nutrition-to-snapshot mapping from the existing food pipeline
5. emit one real daily snapshot artifact
6. update README/docs enough that the repo already reads as Health Lab in direction, even before deeper structural refactors

## What not to do

- do not pretend Garmin disappears; it remains valuable
- do not do a huge rename-only pass and call it transformation
- do not block progress on perfect gym integrations
- do not mix data-backed and generic guidance without explicit labels
- do not make ClawSuite integration the only success criterion; the repo itself must become structurally coherent first

## Success test

This transformation is successful when all of the following are true:
- a new reader sees a Health Lab project, not a Garmin project
- Garmin is clearly one adapter among several health inputs
- gym data has a legitimate path into the system
- food/nutrition is visibly first-class
- one unified daily health artifact exists
- that artifact can feed a ClawSuite health page cleanly
