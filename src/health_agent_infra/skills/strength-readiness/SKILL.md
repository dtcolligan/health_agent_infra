---
name: strength-readiness
description: Produce a bounded StrengthProposal for today by consuming the runtime-computed `classified_state` + `policy_result` and applying judgment-only steps — action matrix, rationale prose, cross-checks. The runtime already did every band, every score, every R-rule; this skill does not re-derive them.
allowed-tools: Read, Bash(hai state snapshot *), Bash(hai state read *), Bash(hai propose *)
disable-model-invocation: false
---

# Strength Readiness

All arithmetic happens in code. Your job is: read the bundle, honour the policy result, pick an action, write the rationale, persist.

## Load the bundle

```
hai state snapshot --as-of <today> --user-id <u> --evidence-json <hai clean output>
```

Under `snapshot.strength` you receive these blocks:

- `today` — today's `accepted_resistance_training_state_daily` row (session_count, total_sets, total_reps, total_volume_kg_reps, exercises, volume_by_muscle_group_json, estimated_1rm_json, unmatched_exercise_tokens_json), or null.
- `history` — trailing rows for 28-day context.
- `signals` — runtime-derived dict the classifier consumed: `volume_ratio_7d_vs_28d_week_mean`, `sessions_last_7d`, `sessions_last_28d`, `days_since_heavy_by_group`, `today_volume_by_muscle_group`, `estimated_1rm_today`, `unmatched_exercise_tokens`, `goal_domain`. Context only; never re-derive.
- `classified_state` — `recent_volume_band`, `freshness_band_by_group`, `coverage_band`, `strength_status`, `strength_score`, `volume_ratio`, `sessions_last_7d`, `sessions_last_28d`, `unmatched_exercise_tokens`, `uncertainty`. **Source of truth.**
- `policy_result` — `policy_decisions[]`, `forced_action`, `forced_action_detail`, `capped_confidence`. **Source of truth.**
- `missingness` — per state_model_v1.md §5.

## Protocol

### 1. If the policy forced an action, use it

If `policy_result.forced_action` is set, `action` is that value and `action_detail` is `policy_result.forced_action_detail`. Confidence: `low` for `defer_decision_insufficient_signal`, else `moderate`. Skip the action matrix; jump to rationale.

Specifically:
- `defer_decision_insufficient_signal` → R-coverage fired; record the decision verbatim.
- `escalate_for_user_review` → R-volume-spike fired; record the `volume_ratio` + `threshold_ratio` in the action_detail so the user can inspect.

### 2. Otherwise, pick from the action matrix

Keyed on `classified_state.strength_status`:

| status | action + action_detail |
|---|---|
| `progressing` | `proceed_with_planned_session` |
| `maintaining` | `proceed_with_planned_session` with `{"caveat": "steady_state"}` when every freshness band for the session's target groups is `fresh` |
| `maintaining` (fatigued group) | `downgrade_to_technique_or_accessory` with `{"reason_token": "fatigued_group:<group>"}` when the session targets a group whose freshness band is `fatigued` |
| `undertrained` | `proceed_with_planned_session` with `{"caveat": "undertrained_resume_gradually"}` |
| `overreaching` | this path is unreachable — R-volume-spike already forced `escalate_for_user_review` in step 1 |

### 3. Confidence

Default from `classified_state.coverage_band`: `full → high`, `partial → moderate`, `sparse → moderate`, `insufficient → low`. If `policy_result.capped_confidence` is set, it lowers the default but never raises it.

### 4. Cross-checks (no arithmetic)

- If `classified_state.unmatched_exercise_tokens` is non-empty, surface it in the rationale — the agent should invite the user to extend the taxonomy via `hai intake exercise` so those sets participate in classification next time.
- If `classified_state.uncertainty` contains `goal_domain_is_resistance_training`, frame the rationale around progression: current 1RM estimates, volume trend, per-group freshness.

### 5. Rationale (5–8 lines)

One line per band or signal that informed the decision. Name the band; do not re-derive it.

Examples: `recent_volume_band=<band>`, `strength_status=<status>`, `freshness_band[quads]=<band>`, `unmatched_exercise_tokens_present`, `volume_spike_detected` (if R-volume-spike fired), `goal_domain_is_resistance_training` (if flagged).

### 6. Uncertainty

Start with `classified_state.uncertainty` (already sorted + deduped). Append any tokens you added (e.g. `*_unavailable_at_source` derived from the snapshot's `missingness` token). Re-sort alphabetically; deduplicate.

### 7. Follow-up

Strength emits a `StrengthProposal`, not a recommendation, so it has no `follow_up` field. Synthesis assigns review semantics per finalised plan. Skip this step.

On `defer_decision_insufficient_signal`, synthesis uses the strength-domain template `"Did you train yesterday? Anything worth logging?"` (owned by `core.narration.templates.DEFER_REVIEW_QUESTION_TEMPLATES`).

## Output

Emit a `StrengthProposal` JSON and call `hai propose --domain strength --proposal-json <path>`. The propose tool validates the shape and appends to `proposal_log`; it is your determinism check.

`proposal_id` = `prop_<for_date>_<user_id>_strength_01` (idempotent on `(for_date, user_id, domain)`; re-running on the same day does not produce a new row).

Copy `policy_result.policy_decisions` into the output's `policy_decisions` verbatim — the runtime decided them; you do not re-edit or add new ones.

## Invariants

- You never compute a band, a score, a ratio, or a 1RM. `classified_state` is the source of truth.
- You never evaluate an R-rule (require_min_coverage, no_high_confidence_on_sparse_signal, volume_spike_escalation, unmatched_exercise_confidence_cap). `policy_result` is the source of truth; you honour `forced_action` and `capped_confidence`.
- You never apply X-rule mutations. Synthesis owns all cross-domain reasoning (X3 ACWR caps strength; X4 yesterday's heavy lower body caps running; X5 yesterday's long run caps lower-body strength). This skill emits one domain's bounded proposal; synthesis mutates the draft mechanically, based on `x_rule_firing` rows, before the skill ever sees it as "final."
- You never emit an `action` outside the v1 enum (`proceed_with_planned_session`, `downgrade_to_technique_or_accessory`, `downgrade_to_moderate_load`, `rest_day_recommended`, `defer_decision_insufficient_signal`, `escalate_for_user_review`). `hai propose` enforces this.
- You never fabricate values for missing evidence; missing stays missing.
- If a decision isn't reasoned in `rationale[]` or `policy_decisions[]`, it didn't happen.
