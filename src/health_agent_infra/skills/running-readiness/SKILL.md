---
name: running-readiness
description: Produce a bounded RunningProposal for today's run by consuming the runtime-computed `classified_state` + `policy_result` and applying judgment-only steps — action matrix, rationale prose, vendor cross-check, follow-up composition. The runtime already did every band, every score, and every R-rule; this skill does not re-derive them.
allowed-tools: Read, Bash(hai state snapshot *), Bash(hai state read *), Bash(hai clean *), Bash(hai propose *)
disable-model-invocation: false
---

# Running Readiness

All arithmetic happens in code. Your job is: read the bundle, honour the policy result, pick an action, write the rationale, persist.

## Load the bundle

```
hai state snapshot --as-of <today> --user-id <u> --evidence-json <hai clean output>
```

Under `snapshot.running` you receive:

- `today` / `history` — daily rollup rows (distance, intensity minutes).
- `activities_today` / `activities_history` — per-session intervals.icu rows (`type='Run'`), newest-first. Each carries `distance_m`, `moving_time_s`, `hr_zone_times_s` ([Z1..Z7] seconds), `interval_summary`, `trimp`, `warmup_time_s`, `cooldown_time_s`, `feel`, `icu_rpe`. Empty on rest days.
- `signals` — runtime-derived dict. Classic: `weekly_mileage_m`, `weekly_mileage_baseline_m`, `recent_hard_session_count_7d`, `acwr_ratio`, `training_readiness_pct`, `sleep_debt_band`, `resting_hr_band`. Structural (v0.1.4): `z4_plus_seconds_today`, `z4_plus_seconds_7d`, `last_hard_session_days_ago`, `today_interval_summary`, `activity_count_14d`. Context only; never re-derive.
- `classified_state` — **source of truth**. Carries `weekly_mileage_trend_band`, `hard_session_load_band`, `freshness_band`, `recovery_adjacent_band`, `coverage_band`, `running_readiness_status`, `readiness_score`, `uncertainty`.
- `policy_result` — **source of truth** for `policy_decisions[]`, `forced_action`, `forced_action_detail`, `capped_confidence`.
- `missingness` — per state_model_v1.md §5.

Reach into `activities_today` / `activities_history` for qualitative context — "did today's session match what I planned?" (compare `today_interval_summary` to `evidence.planned_session_type`), or session-level colour in rationale ("Z4 for 4:42"). Never recompute a band the classifier already decided.

## Protocol

### 1. If the policy forced an action, use it

If `policy_result.forced_action` is set, `action` is that value and `action_detail` is `policy_result.forced_action_detail`. Confidence: `low` for `defer_decision_insufficient_signal`, else `moderate`. Skip the action matrix; jump to rationale.

### 2. Otherwise, pick from the action matrix

Keyed on `classified_state.running_readiness_status` × planned session character. The planned character comes from `evidence.planned_session_type` if present, else infer from history (last hard day, weekly progression).

| status | planned character | action + action_detail |
|---|---|---|
| `ready` | any | `proceed_with_planned_run` — if `active_goal` present, `action_detail = {"active_goal": <goal>}` |
| `conditional` | intervals \| race | `downgrade_intervals_to_tempo` with `{"target_zone": "tempo", "reason_token": "conditional_readiness"}` |
| `conditional` | tempo \| long | `downgrade_to_easy_aerobic` with `{"target_zone": "easy_aerobic"}` |
| `conditional` | easy \| recovery | `proceed_with_planned_run` with `{"caveat": "keep_effort_conversational"}` |
| `hold` | hard \| intervals \| tempo \| long | `cross_train_instead` with `{"reason_token": "hold_status_avoid_impact"}` |
| `hold` | easy \| recovery | `rest_day_recommended` with `{"suggested_activity": "walk_or_mobility"}` |

### 3. Confidence

Default from `classified_state.coverage_band`: `full → high`, `partial → moderate`, `sparse → moderate`, `insufficient → low`. If `policy_result.capped_confidence` is set, it lowers the default but never raises it. The vendor cross-check below may lower further.

### 4. Vendor cross-check

The snapshot also carries Garmin's own running signals under `recovery.today` and the running `signals` block:

- `acwr_status` (on `recovery.today` / `raw_summary`) — Garmin's vendor band (e.g. `"PRODUCTIVE"`, `"OVERREACHING"`). If `acwr_status` is overreaching/unproductive but `freshness_band` is `fresh` or `neutral`, cap confidence at `moderate` and add `agent_vendor_acwr_disagreement` to `uncertainty`.
- `training_readiness_pct` (on `signals`) — locally-computed mean of Garmin's component pcts. The vendor's categorical level can disagree because Garmin applies internal weighting; if it does, add `training_readiness_weighting_disagreement`.

### 5. Rationale (5–8 lines)

One line per band that informed the decision. Name the band; do not re-derive it.

Examples: `weekly_mileage_trend=<band>`, `hard_session_load=<band>`, `freshness=<band>`, `recovery_adjacent=<band>`, `acwr_status=<vendor_label>` (informational), `active_goal=<goal>` (if present), `agent_vendor_acwr_disagreement` (if applicable).

### 6. Uncertainty

Start with `classified_state.uncertainty` (already sorted + deduped). Append any tokens you added (e.g. `*_unavailable_at_source` derived from the snapshot's `missingness` token, vendor-disagreement tokens). Re-sort alphabetically; deduplicate.

### 7. Follow-up

Running emits a `RunningProposal`, not a recommendation, so it has no `follow_up` field. The synthesis layer assigns review semantics per finalised plan. Skip this step.

When the action is `defer_decision_insufficient_signal`, synthesis uses the running-domain template `"Did you go for a run yesterday? How did it feel?"` (owned by `core.narration.templates.DEFER_REVIEW_QUESTION_TEMPLATES`) so the question never leaks recovery session-language.

## Output

Emit a `RunningProposal` JSON and call `hai propose --domain running --proposal-json <path>`. The propose tool validates the shape and appends to `proposal_log`; it is your determinism check.

`proposal_id` = `prop_<for_date>_<user_id>_running_01` (idempotent on `(for_date, user_id, domain)`; re-running on the same day does not produce a new row).

Copy `policy_result.policy_decisions` into the output's `policy_decisions` verbatim — the runtime decided them; you do not re-edit or add new ones.

## Invariants

- You never compute a band, a score, or a ratio. `classified_state` is the source of truth.
- You never evaluate an R-rule (require_min_coverage, acwr_spike_escalation, no_high_confidence_on_sparse_signal). `policy_result` is the source of truth; you honour `forced_action` and `capped_confidence`.
- You never apply X-rule mutations. Synthesis owns all cross-domain reasoning; this skill emits one domain's bounded proposal.
- You never emit an `action` outside the v1 enum (`proceed_with_planned_run`, `downgrade_intervals_to_tempo`, `downgrade_to_easy_aerobic`, `cross_train_instead`, `rest_day_recommended`, `defer_decision_insufficient_signal`, `escalate_for_user_review`). `hai propose` enforces this.
- You never fabricate values for missing evidence; missing stays missing.
- If a decision isn't reasoned in `rationale[]` or `policy_decisions[]`, it didn't happen.
