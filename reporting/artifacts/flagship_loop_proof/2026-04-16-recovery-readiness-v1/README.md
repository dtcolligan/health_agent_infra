# Flagship Loop Proof — recovery_readiness_v1

Captured: 2026-04-16. Adopted under [reporting/docs/canonical_doctrine.md](../../../docs/canonical_doctrine.md) and [reporting/docs/flagship_loop_spec.md](../../../docs/flagship_loop_spec.md).

This artifact is the first inspectable end-to-end proof of the flagship
`recovery_readiness_v1` loop. It runs the full runtime path:

```
PULL -> CLEAN -> STATE -> POLICY -> RECOMMEND -> ACTION -> REVIEW
```

across six scenarios, using synthetic PULL-layer fixtures. Every other layer
is the real implementation under `clean/health_model/recovery_readiness_v1/`.

## Scenarios captured

| scenario | recovery_status | action | coverage | demonstrates |
|---|---|---|---|---|
| recovered_with_easy_plan | recovered | proceed_with_planned_session | full | green-path behavior |
| mildly_impaired_with_hard_plan | mildly_impaired | downgrade_hard_session_to_zone_2 | full | bounded downgrade for mild signals + hard plan |
| impaired_with_hard_plan | impaired | downgrade_session_to_mobility_only | full | stronger downgrade for impaired signals + hard plan |
| rhr_spike_three_days | mildly_impaired | escalate_for_user_review | full | R4 persistent-RHR-spike escalation |
| insufficient_signal | unknown | defer_decision_insufficient_signal | insufficient | R1 block on missing required inputs |
| sparse_signal | mildly_impaired | proceed_with_planned_session (confidence: low) | sparse | confidence downgrade under sparse coverage |

## Files

- `captured/*.json` — one full run artifact per scenario (run metadata,
  cleaned evidence, recovery state, training recommendation with policy
  decisions, action record, review event, review outcome). These files are
  the authoritative per-scenario evidence.
- `summary/*.txt` — human-readable one-screen summaries from the CLI's
  default output.
- `writeback/recovery_readiness_v1/` — the actual local writeback targets
  the ACTION layer produced during this capture:
  - `recommendation_log.jsonl` — six typed recommendation records
  - `daily_plan_2026-04-16.md` — six daily-plan entries, one per scenario
  - `review_events.jsonl` — six scheduled review events
  - `review_outcomes.jsonl` — six synthetic `followed_and_improved` outcomes
    recorded via the REVIEW layer

## How to reproduce

From repo root:

```bash
PYTHONPATH=clean:safety python -m health_model.recovery_readiness_v1.cli run \
  --scenario mildly_impaired_with_hard_plan \
  --base-dir /tmp/recovery_readiness_v1 \
  --date 2026-04-16 \
  --now 2026-04-16T07:15:00+00:00 \
  --record-review-outcome followed_and_improved
```

Change `--scenario` to replay any row of the table above. The fixtures and
loop implementation live under
`clean/health_model/recovery_readiness_v1/`. Tests covering each layer live
in `safety/tests/test_recovery_readiness_v1.py`.

## Proof conditions from the flagship spec

The flagship spec requires six visible proof conditions. This capture
satisfies them:

1. **Deterministic evidence path** — `captured/*.json` contain `cleaned_evidence`
   showing the inputs that produced each state.
2. **Explicit state object** — `captured/*.json > recovery_state` is a typed
   object conforming to `recovery_state.v1` including `signal_quality` and
   `uncertainties`.
3. **Policy gate** — `captured/*.json > training_recommendation.policy_decisions`
   shows each rule that fired, including R1 block (insufficient_signal),
   R4 escalate (rhr_spike_three_days).
4. **Structured recommendation** — typed fields: `action`, `rationale`,
   `confidence`, `uncertainty`, `follow_up`, `policy_decisions`, `bounded=true`.
5. **Bounded writeback** — `writeback/recovery_readiness_v1/` shows only
   local JSONL appends and a local daily-plan markdown note. No external
   writes. The writeback function enforces this at the I/O boundary via the
   `writeback_locality` check.
6. **Review loop** — `review_events.jsonl` and `review_outcomes.jsonl`
   show scheduled events and recorded outcomes linked via `recommendation_id`.

## Scope and honesty

- PULL is a synthetic fixture, not a live Garmin API call. Wiring real
  pulls is a Phase 2 follow-on slice; the cleaned-evidence shape is
  stable and real pulls plug into it directly.
- The readiness-score formula is a first-pass deterministic heuristic.
  Confidence in the score itself is not yet calibrated against user
  outcomes; review data is the intended input to that calibration over
  time.
- No diagnostic, clinical, or nutrition outputs are produced, per the
  doctrine's explicit non-goals.
