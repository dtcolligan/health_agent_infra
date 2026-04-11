# Health Lab

Health Lab is a protocol and contract layer for agent-mediated personal health workflows: it gives an agent truthful ways to retrieve bounded health evidence from a user-owned private memory layer, produce inspectable outputs, and write structured updates back.

Note: the repository directory is still named `garmin_lab` for historical reasons, while the current project framing is Health Lab.

## Architecture boundary

- Health Lab is the protocol and specification layer in this repo.
- Private health data belongs in a user-owned memory layer outside Health Lab.
- Agents perform retrieval, synthesis, recommendation generation, and writeback against that external memory layer.
- The checked-in CLIs and proof bundles in this repo are reference implementation surfaces, not a claim that Health Lab itself is the full runtime or durable data host.

## What works today

The clearest shipped proof in this repo is a CLI-first reference protocol loop:

`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`

That loop is implemented under `health_model/`, covered by CLI integration tests, and produces JSON artifacts with explicit scope and fail-closed error envelopes.

## Canonical sample demo path

Start with the one-command canonical public demo from repo root:

```bash
python3 scripts/run_canonical_public_demo.py
```

The canonical public demo surface for this slice is:
- one-command walkthrough doc: `docs/health_lab_canonical_public_demo.md`
- disposable generated runtime outputs: `artifacts/public_demo/generated/`
- checked-in public demo bundle: `artifacts/public_demo/captured/`
- audited flagship proof bundle: `artifacts/flagship_loop_proof/2026-04-09/`
- deterministic synthetic stress harness: `python3 scripts/run_synthetic_recommendation_stress_harness.py` with outputs under `artifacts/synthetic_stress_harness/latest/`

The checked-in public demo bundle includes:
- `artifacts/public_demo/captured/shared_input_bundle_2026-04-09.json`
- `artifacts/public_demo/captured/agent_readable_daily_context_2026-04-09.json`
- `artifacts/public_demo/captured/agent_readable_daily_context_latest.json`
- `artifacts/public_demo/captured/agent_recommendation_2026-04-09.json`
- `artifacts/public_demo/captured/agent_recommendation_latest.json`
- `artifacts/public_demo/captured/recommendation_success_envelope.json`
- `artifacts/public_demo/captured/recommendation_rejection_envelope_bad_evidence.json`
- `artifacts/public_demo/captured/recommendation_rejection_non_mutation_proof.json`

Use the one-command wrapper for a fresh disposable run, then inspect the captured bundle for the frozen public-safe proof, including explicit non-mutation evidence for the fail-closed rejection case.

These checked-in bundles are proof objects for the protocol layer, not evidence that this repo is the durable home for private user health data.

The broader CLI walkthroughs later in this README remain useful runtime examples, but they are not the canonical public demo proof object for this slice.

## Self-usage day runner

For the bounded one-day self-usage validation path, run from repo root:

```bash
python3 scripts/run_self_usage_day.py \
  --date 2026-04-10 \
  --user-id user_dom \
  --voice-note-payload-path artifacts/self_usage/week1/2026-04-10/voice_note_payload.json \
  --recommendation-payload-path artifacts/self_usage/templates/recommendation_payload_example_2026-04-10.json \
  --judgment-label useful \
  --action-taken "Chose a lighter evening and skipped extra training load." \
  --why "The recommendation matched the low-energy and soreness context and was specific enough to act on immediately." \
  --caveat "No passive wearable or sleep-duration signals were present in this same-day proof run." \
  --time-cost-note "About 10 minutes including one payload review." \
  --friction-points "manual recommendation payload review" "proof copy now automated"
```

This wrapper stays thin on purpose. It does not generate recommendation content. It verifies repo-root preflight checks, reads the scoped context, validates that the recommendation artifact only references ids present in the day context, copies the proof bundle into `artifacts/self_usage/week1/YYYY-MM-DD/`, rewrites `judgment_log.csv`, and writes compact friction/usefulness capture to `runner_capture_YYYY-MM-DD.json`.

Treat this as a reference proof of agent-operated retrieval, synthesis handoff, and judgment capture, not as an embedded always-on coaching runtime.

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
- Same-day recommendation judgment writeback via `python3 -m health_model.agent_memory_write_cli recommendation-judgment`

### Legacy and adjacent repo surfaces
- Older Garmin, food logging, dashboard, and web-app surfaces remain in-tree as legacy or adjacent code, but they are not part of the current flagship proof path.

### Not yet
- No claim of clinical-grade guidance, diagnosis, or monitoring
- No public multi-user product, hosted API, or polished install flow
- No claim that private runtime data in local `data/` directories is demo-safe for sharing
- No claim that the broader repo has been refactored around this CLI loop yet

## Quick repo orientation

The current flagship loop lives in `health_model/`. Older project surfaces for Garmin ingestion, dashboards, and the web app still exist in the repo as legacy or adjacent code, but they are not part of the current flagship proof path.

If you want the smallest trustworthy slice first, run `python3 scripts/run_canonical_public_demo.py`, inspect `artifacts/public_demo/generated/`, then compare that disposable run with `artifacts/public_demo/captured/` and the audited flagship proof bundle at `artifacts/flagship_loop_proof/2026-04-09/` or regenerate the stricter proof audit with `python3 scripts/run_flagship_loop_proof_audit.py`.

For repo-level trust and contribution boundaries, see `STATUS.md`, `CONTRIBUTING.md`, and `LICENSE` at the repo root.

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

## Day-scoped nutrition brief

For a compact read-only nutrition view in the self-usage lane, run:

```bash
python3 -m health_model.day_nutrition_brief \
  --date 2026-04-08 \
  --user-id 1
```

Outputs:
- `data/health/day_nutrition_brief_YYYY-MM-DD.json`
- `data/health/day_nutrition_brief_latest.json`

This brief uses only accepted daily snapshot nutrition fields, keeps missing nutrition coverage explicit, and marks personalized bedtime guidance plus micronutrient-gap detection as unsupported in this slice.

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

The current thin writeback extension for this loop is one same-day recommendation judgment op only:

```bash
python3 -m health_model.agent_memory_write_cli recommendation-judgment \
  --output-dir data/health \
  --payload-path artifacts/protocol_layer_proof/2026-04-11-writeback-judgment/writeback_recommendation_judgment_request.json
```

This writes `recommendation_judgment_YYYY-MM-DD.json` plus the latest alias, validates the referenced recommendation artifact scope and id, and fails closed without mutating existing judgment artifacts on rejection.

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
