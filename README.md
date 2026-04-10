# Health Lab

Health Lab is a local-first personal health lab for turning bounded daily inputs into machine-readable artifacts that another agent can inspect safely.

## What works today

The clearest shipped proof in this repo is a CLI-first loop:

`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`

That loop is implemented under `health_model/`, covered by CLI integration tests, and produces JSON artifacts with explicit scope and fail-closed error envelopes.

## Canonical sample demo path

The approved evaluator-checkable proof for this slice is the frozen context-to-recommendation audit bundle under `artifacts/flagship_loop_proof/2026-04-09/`.

Regenerate it from repo root with:

```bash
python3 scripts/run_flagship_loop_proof_audit.py
```

Frozen proof inputs:
- context fixture: `tests/fixtures/agent_readable_daily_context/generated_fixture_day_context.json`
- successful payload: `artifacts/flagship_loop_proof/payloads/recommendation_positive_payload_2026-04-09.json`
- fail-closed payload: `artifacts/flagship_loop_proof/payloads/recommendation_negative_payload_2026-04-09.json`

Checked-in proof outputs:
- `artifacts/flagship_loop_proof/2026-04-09/agent_recommendation_2026-04-09.json`
- `artifacts/flagship_loop_proof/2026-04-09/agent_recommendation_latest.json`
- `artifacts/flagship_loop_proof/2026-04-09/negative_fail_closed_result.json`
- `artifacts/flagship_loop_proof/2026-04-09/negative_artifact_state_preservation.json`

The broader CLI walkthroughs later in this README remain useful runtime examples, but they are not the proof object for this audit slice.

## Non-clinical and privacy boundaries

- This is a personal software project, not a clinical product or medical device.
- The checked-in flagship proof bundle is fixture-backed and does not require private health data.
- Runtime outputs belong under local `data/` paths or another local directory such as `/tmp/health_lab_demo/`; those files are disposable runtime outputs, not the public proof object.
- The repo should be read as artifact-generation infrastructure, not diagnosis or treatment advice.

## Real now vs not yet

### Real now
- Contract discovery via `python3 -m health_model.agent_contract_cli describe`
- Fresh bundle bootstrap via `python3 -m health_model.agent_bundle_cli init`
- Voice-note submission into a persisted bundle via `python3 -m health_model.agent_voice_note_cli submit`
- Scoped context reads via `python3 -m health_model.agent_context_cli get`
- Recommendation artifact creation via `python3 -m health_model.agent_recommendation_cli create`
- Older Garmin, food logging, dashboard, and web-app surfaces elsewhere in the repo

### Not yet
- No claim of clinical-grade guidance, diagnosis, or monitoring
- No public multi-user product, hosted API, or polished install flow
- No claim that private runtime data in local `data/` directories is demo-safe for sharing
- No claim that the broader repo has been refactored around this CLI loop yet

## Quick repo orientation

The current flagship loop lives in `health_model/`. Older project surfaces for Garmin ingestion, dashboards, and the web app still exist in the repo, but they are not the cleanest stranger-safe proof path today.

If you want the smallest trustworthy slice first, run `python3 scripts/run_flagship_loop_proof_audit.py`, inspect `artifacts/flagship_loop_proof/2026-04-09/`, then use the broader CLI walkthroughs below as adjacent context.

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

Zero-to-one bootstrap flow from fresh local state:

```bash
python3 -m health_model.agent_bundle_cli init \
  --bundle-path data/health/shared_input_bundle_2026-04-09.json \
  --user-id user_dom \
  --date 2026-04-09
```

```bash
python3 -m health_model.agent_voice_note_cli submit \
  --bundle-path data/health/shared_input_bundle_2026-04-09.json \
  --output-dir data/health \
  --user-id user_dom \
  --date 2026-04-09 \
  --payload-path tests/fixtures/voice_note_intake/daily_voice_note_input.json
```

```bash
python3 -m health_model.agent_context_cli get \
  --artifact-path data/health/agent_readable_daily_context_2026-04-09.json \
  --user-id user_dom \
  --date 2026-04-09
```

```bash
python3 -m health_model.agent_contract_cli describe
```

This bounded flow proves an external agent can discover the contract, initialize a canonical empty shared-input bundle from zero local state, submit one same-day transcribed voice note, and read back the regenerated daily context using only CLI surfaces.

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

## CLI-driven contract discovery

External agents can discover the current Health Lab contract from the CLI alone, without scraping this README or importing Python modules:

```bash
python3 -m health_model.agent_contract_cli describe
```

The discovery output is stable machine-readable JSON and includes:

- `contract_id` and `contract_version`
- supported operations for `health_model.agent_submit_cli`, `health_model.agent_context_cli`, and the discovery CLI itself
- required arguments and accepted enum values
- consumed and produced artifact types
- default path conventions for the shared input bundle and generated daily context artifacts
- response envelope keys for success and fail-closed errors

The contract discovery CLI is read-only and currently supports one bounded command, `describe`.

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
