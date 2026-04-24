---
name: stress-regulation
description: Produce a bounded StressProposal for today by consuming the runtime-computed `classified_state` + `policy_result` and applying judgment-only steps — action matrix, rationale prose, vendor cross-check. The runtime already did every band, every score, and every R-rule; this skill does not re-derive them.
allowed-tools: Read, Bash(hai state snapshot *), Bash(hai state read *), Bash(hai propose *)
disable-model-invocation: false
---

# Stress Regulation

All arithmetic happens in code. Your job is: read the bundle, honour the policy result, pick an action, write the rationale, persist.

## Load the bundle

```
hai state snapshot --as-of <today> --user-id <u> --evidence-json <hai clean output>
```

Under `snapshot.stress` you receive these blocks:

- `today` — today's `accepted_stress_state_daily` row (garmin_all_day_stress, manual_stress_score, body_battery_end_of_day, stress_event_count, stress_tags_json), or null.
- `history` — recent days of stress rows for context.
- `signals` — the runtime-derived dict the classifier consumed: `garmin_all_day_stress`, `manual_stress_score`, `body_battery_end_of_day`, `body_battery_prev_day`, `stress_history_garmin_last_7`. Context only; never re-derive.
- `classified_state` — `garmin_stress_band`, `manual_stress_band`, `body_battery_trend_band`, `coverage_band`, `stress_state`, `stress_score`, `body_battery_delta`, `uncertainty`. **Source of truth.**
- `policy_result` — `policy_decisions[]`, `forced_action`, `forced_action_detail`, `capped_confidence`. **Source of truth.**
- `missingness` — per state_model_v1.md §5.

## Protocol

### 1. If the policy forced an action, use it

If `policy_result.forced_action` is set, `action` is that value and `action_detail` is `policy_result.forced_action_detail`. Confidence: `low` for `defer_decision_insufficient_signal`, else `moderate`. Skip the action matrix; jump to rationale.

Note: when R-sustained-very-high-stress fires, it forces `escalate_for_user_review` and the corresponding `policy_decisions[]` entry carries an `escalate` tier. Copy the decision verbatim — severity is already recorded there.

### 2. Otherwise, pick from the action matrix

Keyed on `classified_state.stress_state`:

| state | action + action_detail |
|---|---|
| `calm` | `maintain_routine` |
| `manageable` | `maintain_routine` with `{"caveat": "minor_variation"}` when any band is not favourable |
| `elevated` | `add_low_intensity_recovery` with `{"reason_token": "<primary_driver_band>"}` — choose the band doing the most work (garmin_stress_band=high → `garmin_stress_band`; manual_stress_band=high → `manual_stress_band`; body_battery_trend_band=declining → `body_battery_trend_band`) |
| `overloaded` | `schedule_decompression_time` with `{"reason_token": "<primary_driver_band>"}` — same driver-band selection |

### 3. Confidence

Default from `classified_state.coverage_band`: `full → high`, `partial → moderate`, `sparse → moderate`, `insufficient → low`. If `policy_result.capped_confidence` is set, it lowers the default but never raises it. The vendor cross-check below may lower further.

### 4. Vendor cross-check

The snapshot carries Garmin's own stress signals under `stress.today`:

- `garmin_all_day_stress` vs `classified_state.garmin_stress_band` — informational; the classifier already turned the score into a band. If the user's `manual_stress_score` band lands in a meaningfully different band than Garmin (e.g. manual `very_high` but Garmin `moderate`), cap confidence at `moderate` and add `agent_vendor_stress_disagreement` to `uncertainty`.
- `body_battery_delta` — informational in rationale; never action-bearing on its own.

### 5. Rationale (5–8 lines)

One line per band that informed the decision. Name the band; do not re-derive it.

Examples: `garmin_stress=<band>`, `manual_stress=<band>`, `body_battery_trend=<band>`, `stress_state=<state>`, `sustained_very_high_stress` (if R-sustained fired), `agent_vendor_stress_disagreement` (if applicable).

### 6. Uncertainty

Start with `classified_state.uncertainty` (already sorted + deduped). Append any tokens you added (e.g. `*_unavailable_at_source` derived from the snapshot's `missingness` token, vendor-disagreement tokens). Re-sort alphabetically; deduplicate.

### 7. Follow-up

Stress emits a `StressProposal`, not a recommendation, so it has no `follow_up` field. Synthesis assigns review semantics per finalised plan. Skip this step.

On `defer_decision_insufficient_signal`, synthesis uses the stress-domain template `"How were your stress levels yesterday?"` (owned by `core.narration.templates.DEFER_REVIEW_QUESTION_TEMPLATES`).

## Output

Emit a `StressProposal` JSON and call `hai propose --domain stress --proposal-json <path>`. The propose tool validates the shape and appends to `proposal_log`; it is your determinism check.

`proposal_id` = `prop_<for_date>_<user_id>_stress_01` (idempotent on `(for_date, user_id, domain)`; re-running on the same day does not produce a new row).

Copy `policy_result.policy_decisions` into the output's `policy_decisions` verbatim — the runtime decided them; you do not re-edit or add new ones.

## Invariants

- You never compute a band, a score, or a ratio. `classified_state` is the source of truth.
- You never evaluate an R-rule (require_min_coverage, no_high_confidence_on_sparse_signal, sustained_very_high_stress_escalation). `policy_result` is the source of truth; you honour `forced_action` and `capped_confidence`.
- You never apply X-rule mutations. Synthesis owns all cross-domain reasoning; this skill emits one domain's bounded proposal.
- You never emit an `action` outside the v1 enum (`maintain_routine`, `add_low_intensity_recovery`, `schedule_decompression_time`, `escalate_for_user_review`, `defer_decision_insufficient_signal`). `hai propose` enforces this.
- You never fabricate values for missing evidence; missing stays missing.
- If a decision isn't reasoned in `rationale[]` or `policy_decisions[]`, it didn't happen.
