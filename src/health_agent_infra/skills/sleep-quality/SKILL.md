---
name: sleep-quality
description: Produce a bounded SleepProposal for today by consuming the runtime-computed `classified_state` + `policy_result` and applying judgment-only steps — action matrix, rationale prose, vendor cross-check. The runtime already did every band, every score, and every R-rule; this skill does not re-derive them.
allowed-tools: Read, Bash(hai state snapshot *), Bash(hai state read *), Bash(hai propose *)
disable-model-invocation: false
---

# Sleep Quality

All arithmetic happens in code. Your job is: read the bundle, honour the policy result, pick an action, write the rationale, persist.

## Load the bundle

```
hai state snapshot --as-of <today> --user-id <u> --evidence-json <hai clean output>
```

Under `snapshot.sleep` you receive these blocks:

- `today` — last night's `accepted_sleep_state_daily` row (sleep_hours, score, minute breakdowns, awake_count, avg_sleep_respiration, …), or null.
- `history` — recent nights of sleep rows for context.
- `signals` — the runtime-derived dict the classifier consumed: `sleep_hours`, `sleep_score_overall`, `sleep_awake_min`, `sleep_start_variance_minutes`, `sleep_history_hours_last_7`. Context only; never re-derive.
- `classified_state` — `sleep_debt_band`, `sleep_quality_band`, `sleep_timing_consistency_band`, `sleep_efficiency_band`, `coverage_band`, `sleep_status`, `sleep_score`, `sleep_efficiency_pct`, `uncertainty`. **Source of truth.**
- `policy_result` — `policy_decisions[]`, `forced_action`, `forced_action_detail`, `capped_confidence`. **Source of truth.**
- `missingness` — per state_model_v1.md §5.

## Protocol

### 1. If the policy forced an action, use it

If `policy_result.forced_action` is set, `action` is that value and `action_detail` is `policy_result.forced_action_detail`. Confidence: `low` for `defer_decision_insufficient_signal`, else `moderate`. Skip the action matrix; jump to rationale.

Note: when R-chronic-deprivation fires, it forces `sleep_debt_repayment_day` and the corresponding `policy_decisions[]` entry carries an `escalate` tier. Copy the decision verbatim — severity is recorded in the audit record, not in the action.

### 2. Otherwise, pick from the action matrix

Keyed on `classified_state.sleep_status`:

| status | action + action_detail |
|---|---|
| `optimal` | `maintain_schedule` |
| `adequate` | `maintain_schedule` with `{"caveat": "minor_variation"}` when any band is not favourable |
| `compromised` | `prioritize_wind_down` with `{"reason_token": "<primary_weak_band>"}` — choose the band doing the most work (quality=fair/poor → `sleep_quality_band`; efficiency=fair/poor → `sleep_efficiency_band`; consistency=highly_variable → `sleep_timing_consistency_band`; sleep_debt=mild/moderate → `sleep_debt_band`) |
| `compromised` (debt-driven) | if `sleep_debt_band` in {mild, moderate} and the other bands are favourable, use `earlier_bedtime_target` with `{"target_shift_minutes": 30}` |
| `impaired` | `sleep_debt_repayment_day` with `{"reason_token": "impaired_sleep_status"}` |

### 3. Confidence

Default from `classified_state.coverage_band`: `full → high`, `partial → moderate`, `sparse → moderate`, `insufficient → low`. If `policy_result.capped_confidence` is set, it lowers the default but never raises it. The vendor cross-check below may lower further.

### 4. Vendor cross-check

The snapshot carries Garmin's own sleep signals under `sleep.today`:

- `sleep_score_overall` vs `classified_state.sleep_quality_band` — if the vendor score lands in a meaningfully different band than the classifier reports (e.g. vendor 88 "Good" but classifier band is "fair" after a threshold tweak), cap confidence at `moderate` and add `agent_vendor_sleep_quality_disagreement` to `uncertainty`.
- `avg_sleep_respiration`, `avg_sleep_stress` — informational only in rationale; never action-bearing.

### 5. Rationale (5–8 lines)

One line per band that informed the decision. Name the band; do not re-derive it.

Examples: `sleep_debt=<band>`, `sleep_quality=<band>`, `sleep_efficiency=<band> (<pct>%)`, `sleep_timing_consistency=<band>`, `sleep_status=<status>`, `chronic_deprivation_detected` (if R-chronic fired), `agent_vendor_sleep_quality_disagreement` (if applicable).

### 6. Uncertainty

Start with `classified_state.uncertainty` (already sorted + deduped). Append any tokens you added (e.g. `*_unavailable_at_source` derived from the snapshot's `missingness` token, vendor-disagreement tokens). Re-sort alphabetically; deduplicate.

### 7. Follow-up

Sleep emits a `SleepProposal`, not a recommendation, so it has no `follow_up` field. Synthesis assigns review semantics per finalised plan. Skip this step.

On `defer_decision_insufficient_signal`, synthesis uses the sleep-domain template `"Did anything shift in your sleep last night worth noting?"` (owned by `core.narration.templates.DEFER_REVIEW_QUESTION_TEMPLATES`).

## Output

Emit a `SleepProposal` JSON and call `hai propose --domain sleep --proposal-json <path>`. The propose tool validates the shape and appends to `proposal_log`; it is your determinism check.

`proposal_id` = `prop_<for_date>_<user_id>_sleep_01` (idempotent on `(for_date, user_id, domain)`; re-running on the same night does not produce a new row).

Copy `policy_result.policy_decisions` into the output's `policy_decisions` verbatim — the runtime decided them; you do not re-edit or add new ones.

## Invariants

- You never compute a band, a score, or a ratio. `classified_state` is the source of truth.
- You never evaluate an R-rule (require_min_coverage, no_high_confidence_on_sparse_signal, chronic_deprivation_escalation). `policy_result` is the source of truth; you honour `forced_action` and `capped_confidence`.
- You never apply X-rule mutations. Synthesis owns all cross-domain reasoning; this skill emits one domain's bounded proposal.
- You never emit an `action` outside the v1 enum (`maintain_schedule`, `prioritize_wind_down`, `sleep_debt_repayment_day`, `earlier_bedtime_target`, `defer_decision_insufficient_signal`). `hai propose` enforces this. Chronic-deprivation severity is recorded in the policy_decision tier, not in the action.
- You never fabricate values for missing evidence; missing stays missing.
- If a decision isn't reasoned in `rationale[]` or `policy_decisions[]`, it didn't happen.
