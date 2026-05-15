# Flagship Loop Proof — Real Garmin Slice (2026-04-16, captured pre-reshape)

Captured: 2026-04-16 by the pre-reshape Python runtime. As-of date of the data: 2026-04-08 (most recent day in the committed Garmin export).

**Post-reshape status:** this bundle is retained as a reference input+output for the real Garmin slice. The input side — `pull/data/garmin/export/daily_summary_export.csv` flowing through the thin Garmin adapter — still works under the current tools-plus-skills flow. The output side (the captured `recovery_state` and `training_recommendation`) was produced by Python modules that no longer exist; those shapes are now an agent's responsibility, guided by `skills/recovery-readiness/SKILL.md`.

## What this proves

The `hai pull` adapter can read a real Garmin CSV export and emit the same PULL dict shape the synthetic fixtures emit. Downstream `hai clean` produces a valid `CleanedEvidence` + `RawSummary` from that real evidence. An agent, reading those outputs plus the recovery-readiness skill, produces a `TrainingRecommendation`.

The capture in `captured/real_garmin_slice_2026-04-08.json` shows what the pre-reshape Python produced on this input. Key takeaways (still instructive):

| field | value |
|---|---|
| source | `real` |
| action | `proceed_with_planned_session` |
| confidence | `moderate` (softened from high by R5 — no-high-confidence-on-sparse-signal) |
| coverage | `sparse` |
| uncertainty | `training_load_window_incomplete` |
| policy trace | `require_min_coverage: allow`, `no_high_confidence_on_sparse_signal: soften` |

The R5 soften rule fires because the committed export has incomplete training-load coverage over the 14-day window. Under the reshape, the agent reads `raw_summary.coverage_training_load_fraction` and applies R5 per the skill — same logic, different execution path.

## How to reproduce (post-reshape)

```bash
hai pull --date 2026-04-08 --use-default-manual-readiness --user-id u_garmin_real_slice > /tmp/evidence.json
hai clean --evidence-json /tmp/evidence.json > /tmp/prep.json
# agent reads /tmp/prep.json + skills/recovery-readiness/SKILL.md
# agent produces /tmp/rec.json matching TrainingRecommendation
hai writeback --recommendation-json /tmp/rec.json --base-dir /tmp/recovery_readiness_v1
hai review schedule --recommendation-json /tmp/rec.json --base-dir /tmp/recovery_readiness_v1
```

The manual readiness is a neutral default (see `default_manual_readiness` in `src/health_agent_infra/pull/garmin.py`). A production flow would use a typed intake surface — the merge-human-inputs skill covers that partitioning.

## Files

- `captured/real_garmin_slice_2026-04-08.json` — full run artifact from the pre-reshape Python runtime.
- `summary/real_garmin_slice_2026-04-08.txt` — human-readable summary.
- `writeback/recovery_readiness_v1/` — the writeback outputs from the pre-reshape run: `recommendation_log.jsonl`, `review_events.jsonl`, `review_outcomes.jsonl`, `daily_plan_2026-04-08.md`. Shape remains valid under the current runtime.

## Scope and honesty

- The export is a committed offline CSV, not a live API pull. Wiring a scheduled live pull remains out of scope per the explicit non-goals.
- The manual readiness intake is a neutral default here. A real user session would collect typed manual readiness via the merge-human-inputs skill.
- Pre-reshape `recovery_state` classification fields in the capture reference types that no longer exist in `src/health_agent_infra/schemas.py`. Treat as legacy context, not current schema.
- Review-history summarization is bookkeeping-only (counts), not calibration. See `src/health_agent_infra/review/outcomes.py::summarize_review_history`.
- No diagnostic, clinical, or nutrition outputs.
