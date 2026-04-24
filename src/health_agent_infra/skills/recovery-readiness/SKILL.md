---
name: recovery-readiness
description: Produce a bounded RecoveryProposal for today's session by consuming the runtime-computed `classified_state` + `policy_result` and applying judgment-only steps — action matrix, rationale prose, vendor cross-check, follow-up composition. The runtime already did every band, every score, and every policy rule; this skill does not re-derive them.
allowed-tools: Read, Bash(hai state snapshot *), Bash(hai state read *), Bash(hai clean *), Bash(hai propose *), Bash(hai review *)
disable-model-invocation: false
---

# Recovery Readiness

All arithmetic happens in code. Your job is: read the bundle, honour the policy result, pick an action, write the rationale, persist.

## Load the bundle

```
hai state snapshot --as-of <today> --user-id <u> --evidence-json <hai clean output>
```

Under `snapshot.recovery` you receive five blocks:

- `evidence` — cleaned inputs (`sleep_hours`, `resting_hr`, `hrv_ms`, `soreness_self_report`, `planned_session_type`, `active_goal`, …).
- `raw_summary` — deltas / ratios / coverage fractions. Context only; never re-derive.
- `classified_state` — `sleep_debt_band`, `resting_hr_band`, `hrv_band`, `training_load_band`, `soreness_band`, `coverage_band`, `recovery_status`, `readiness_score`, `uncertainty`. **Source of truth.**
- `policy_result` — `policy_decisions[]`, `forced_action`, `forced_action_detail`, `capped_confidence`. **Source of truth.**
- `missingness` — per state_model_v1.md §5.

## Protocol

### 1. If the policy forced an action, use it

If `policy_result.forced_action` is set, `action` is that value and `action_detail` is `policy_result.forced_action_detail`. Confidence: `low` for `defer_decision_insufficient_signal`, else `moderate`. Skip the action matrix; jump to rationale.

### 2. Otherwise, pick from the action matrix

Keyed on `classified_state.recovery_status` × `evidence.planned_session_type`:

| status | planned_session_type | action + action_detail |
|---|---|---|
| `recovered` | any | `proceed_with_planned_session` — if `active_goal` present, `action_detail = {"active_goal": <goal>}` |
| `mildly_impaired` | hard \| intervals \| race | `downgrade_hard_session_to_zone_2` with `{"target_intensity": "zone_2", "target_duration_minutes": 45}` |
| `mildly_impaired` | other | `proceed_with_planned_session` with `{"caveat": "keep_effort_conversational"}` |
| `impaired` | hard \| intervals \| race | `downgrade_session_to_mobility_only` with `{"reason_token": "impaired_recovery_with_hard_plan"}` |
| `impaired` | other | `rest_day_recommended` with `{"suggested_activity": "walk_or_mobility"}` |

### 3. Confidence

Default from `classified_state.coverage_band`: `full → high`, `partial → moderate`, `sparse → moderate`, `insufficient → low`. If `policy_result.capped_confidence` is set, it lowers the default but never raises it. The vendor cross-check below may lower further.

### 4. Vendor cross-check

The snapshot also carries Garmin's own signals under `recovery.today`:

- `training_readiness_level` — vendor-authored categorical band (e.g. `"High"`, `"LOW"`). Pair it with `training_readiness_component_mean_pct`, which is a **locally-computed arithmetic mean** of five Garmin component pcts (`training_readiness_sleep_pct`, `_hrv_pct`, `_stress_pct`, `_sleep_history_pct`, `_load_pct`) and can disagree with the vendor level because Garmin applies internal weighting.
- `all_day_stress`, `body_battery_end_of_day` — passive aggregates. Informational only in rationale.
- `garmin_acwr_ratio` + `acwr_status` — vendor load band.
- `moderate_intensity_min`, `vigorous_intensity_min`, `total_distance_m` — running activity for the day.

If `training_readiness_level` disagrees with `classified_state.recovery_status`, cap confidence at `moderate` and add `agent_vendor_readiness_disagreement` to `uncertainty`. If the local mean and the categorical level diverge, add `training_readiness_weighting_disagreement` — do not trust the local mean alone.

### 5. Rationale (5–8 lines)

One line per band that informed the decision. Name the band; do not re-derive it.

Examples: `sleep_debt=<band>`, `resting_hr_vs_baseline=<band>`, `hrv_vs_baseline=<band>`, `soreness_signal=<band>`, `training_load=<band>`, `body_battery_end_of_day=<int>` (informational), `active_goal=<goal>` (if present), `agent_vendor_readiness_disagreement` (if applicable).

### 6. Uncertainty

Start with `classified_state.uncertainty` (already sorted + deduped). Append any tokens you added (e.g. `*_unavailable_at_source` derived from the snapshot's `missingness` token, `agent_vendor_readiness_disagreement`, `training_readiness_weighting_disagreement`). Re-sort alphabetically; deduplicate.

### 7. Follow-up

`review_at` = next morning **after `issued_at`** at `07:00:00+00:00` (not after `for_date`; R4 measures from `issued_at`).

`review_question` by action:

- `proceed_with_planned_session` → "Did today's session feel appropriate for your recovery?"
- `downgrade_hard_session_to_zone_2` → "Did yesterday's downgrade to Zone 2 improve how today feels?"
- `downgrade_session_to_mobility_only` → "Did yesterday's mobility-only day help your recovery?"
- `rest_day_recommended` → "Did yesterday's rest day help your recovery?"
- `defer_decision_insufficient_signal` → "Did you decide on a session yesterday? How did it go?"
- `escalate_for_user_review` → "You had a persistent signal we flagged. Did you take any action?"

`review_event_id` format: `rev_<review_date>_<user_id>_<recommendation_id>`.

## Output

Emit a `RecoveryProposal` JSON and call `hai propose --domain recovery --proposal-json <path> --base-dir <root>`. The propose tool validates the shape and appends to `proposal_log`; it is your determinism check.

`proposal_id` = `prop_<for_date>_<user_id>_recovery_01` on first write; revisions get `_02`, `_03`. Use `hai propose --replace` when revising the same day's proposal with new skill output — the runtime creates a new revision leaf and forward-links the prior one. Identical-payload replay under `--replace` is a no-op.

Copy `snapshot.recovery.policy_result.policy_decisions` into the output's `policy_decisions` verbatim. Synthesis owns downstream: `daily_plan_id`, `recommendation_id`, X-rule-applied `action_detail`, review scheduling. This skill emits one domain's bounded proposal and stops.

## Invariants

- You never compute a band, a score, or a ratio. `classified_state` is the source of truth.
- You never evaluate a policy rule (R1 – R6). `policy_result` is the source of truth; you honour `forced_action` and `capped_confidence`.
- You never apply X-rule mutations. Synthesis owns that in Phase 2; this skill emits one domain's bounded proposal.
- You never emit an `action` outside the v1 enum. `hai propose` enforces this.
- You never fabricate values for missing evidence; missing stays missing.
- If a decision isn't reasoned in `rationale[]` or `policy_decisions[]`, it didn't happen.
