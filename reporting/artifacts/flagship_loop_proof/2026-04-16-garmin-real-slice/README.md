# Flagship Loop Proof — Real Garmin Slice

Captured: 2026-04-16. As-of date of the data: 2026-04-08 (most recent day in
the committed Garmin export). Adopted under
[reporting/docs/canonical_doctrine.md](../../../docs/canonical_doctrine.md),
[reporting/docs/flagship_loop_spec.md](../../../docs/flagship_loop_spec.md),
and Phase 2 of [reporting/docs/plan_2026-04-16.md](../../../docs/plan_2026-04-16.md).

This artifact is the Phase 2 proof that the flagship
`recovery_readiness_v1` loop runs end-to-end against **real Garmin evidence**,
not synthetic fixtures. The same runtime path —

```
PULL -> CLEAN -> STATE -> POLICY -> RECOMMEND -> ACTION -> REVIEW
```

— executes unchanged; only the PULL source is swapped.

## What changed vs. the eight-scenario synthetic capture

| layer | synthetic proof | real-slice proof |
|---|---|---|
| PULL | `clean/health_model/recovery_readiness_v1/fixtures/synthetic.py` | `pull/garmin/recovery_readiness_adapter.py` over `pull/data/garmin/export/daily_summary_export.csv` |
| CLEAN | unchanged | unchanged |
| STATE | unchanged | unchanged |
| POLICY | unchanged | unchanged |
| RECOMMEND | unchanged | unchanged |
| ACTION | unchanged | unchanged |
| REVIEW | unchanged | unchanged |

The adapter is bounded: it reads the already-committed CSV export (offline,
no credentials, no live API) and emits the same input dict shape the
synthetic fixtures emit. Everything downstream is the production runtime.

## What the capture shows

Run: `--source real --date 2026-04-08`.

| field | value |
|---|---|
| source | `real` |
| recovery_status | `recovered` |
| readiness_score | `0.95` |
| coverage | `sparse` |
| uncertainties | `training_load_window_incomplete` |
| action | `proceed_with_planned_session` |
| confidence | `moderate` (softened from `high` by R2) |
| policy trace | `require_min_coverage: allow`, `no_high_confidence_on_sparse_signal: soften` |

The R2 soften rule fired because the committed export has training-load
coverage that is incomplete over the 14-day window. That is the exact
policy-bounded behavior the flagship specifies: when signal is sparse,
confidence is visibly softened — not hidden.

## How to reproduce

From repo root:

```bash
PYTHONPATH=clean:safety:pull python -m health_model.recovery_readiness_v1.cli run \
  --source real \
  --base-dir /tmp/recovery_readiness_v1 \
  --date 2026-04-08 \
  --now 2026-04-08T07:15:00+00:00 \
  --user-id u_garmin_real_slice_2026-04-08 \
  --record-review-outcome followed_and_improved
```

The manual readiness intake in the real-source path is a neutral default
(see `pull/garmin/recovery_readiness_adapter.py::default_manual_readiness`).
Real manual readiness would come from a typed intake surface in a production
flow; the proof capture leaves that slice deliberately flat.

## Files

- `captured/real_garmin_slice_2026-04-08.json` — full run artifact.
- `summary/real_garmin_slice_2026-04-08.txt` — human-readable summary.
- `writeback/recovery_readiness_v1/` — the ACTION layer's local writebacks,
  isolated from the synthetic eight-scenario writeback bundle to keep real
  evidence and synthetic evidence visibly separated.

## Scope and honesty

- The export is a committed offline CSV, not a live API pull. Wiring a
  scheduled live pull is beyond this proof's scope.
- The manual readiness intake is a neutral default for the real capture.
  Goal-conditioned tailoring is demonstrated separately in the synthetic
  capture (`tailoring_recovered_*` rows).
- The readiness-score formula is a first-pass deterministic heuristic.
  Confidence calibration against review outcomes is a founder-authored
  stub (see `clean/health_model/recovery_readiness_v1/review.py::derive_confidence_adjustment`).
- No diagnostic, clinical, or nutrition outputs are produced.
