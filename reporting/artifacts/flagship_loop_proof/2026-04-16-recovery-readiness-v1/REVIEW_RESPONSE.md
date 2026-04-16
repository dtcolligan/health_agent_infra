# Review Response — 2026-04-16

External review by a second agent flagged two holes in the initial capture:

1. **R4 doc/code mismatch** — doctrine said escalate when
   `state.resting_hr_vs_baseline == "well_above"` for 3+ days, but CLEAN
   used a looser `>= 1.10× baseline` threshold. The captured spike
   scenario had state say `above`, not `well_above`, yet escalation still
   fired.
2. **R2 not actually demonstrated** — the sparse-signal scenario
   produced confidence `low` before policy ran, so the
   `no_high_confidence_on_sparse_signal` soften rule had nothing to do.
   The captured artifact had no R2 audit entry.

Both are fixed in this re-capture.

## R4 alignment

- CLEAN's spike threshold raised to 1.15× baseline (module constant
  `WELL_ABOVE_RESTING_HR_RATIO`), matching the STATE `well_above` band.
- CLEAN now dedupes raw records by date so overlapping fixture entries
  can't contaminate the baseline.
- Spike fixture bumped from 60 → 64 bpm so, against a (now clean)
  baseline ~53.7, today's ratio is ~1.19 → `well_above`.
- Verified in `captured/rhr_spike_three_days.json`:
  - `recovery_state.resting_hr_vs_baseline == "well_above"`
  - `cleaned_evidence.resting_hr_spike_days == 3`
  - `training_recommendation.action == "escalate_for_user_review"`

## R2 genuine soften

- RECOMMEND's `_propose` now returns `confidence = "high"` unconditionally
  when coverage is not `insufficient`. Pre-softening is removed — policy
  is the governor, not the proposer.
- Verified in `captured/sparse_signal.json`:
  - proposal confidence arrives as `high`
  - policy decision array contains
    `{"rule_id": "no_high_confidence_on_sparse_signal", "decision": "soften"}`
  - `training_recommendation.confidence == "moderate"` after soften

## Tests added

- `test_policy_softens_high_to_moderate_on_sparse_scenario` —
  end-to-end, asserts the R2 soften audit entry is present in the
  recommendation's `policy_decisions`.
- `test_policy_r2_soften_is_proven_directly` — unit-style, constructs a
  high-confidence proposal and asserts `evaluate_policy` softens it and
  records the decision.
- `test_policy_escalates_on_rhr_spike_three_days` expanded to assert
  `state.resting_hr_vs_baseline == "well_above"` first, tying the R4
  escalation back to the state's own band.

Test count: 20/20 passing.

## Other adjustments

- `state._derive_band` had a dead duplicate branch in the `low_is_bad`
  direction; cleaned up.
- `nutrition_incomplete` removed from state and recommendation examples
  and from the recommended uncertainty-token vocabulary. Nutrition is
  entirely out of scope per `explicit_non_goals.md` and the runtime
  does not consume it.
