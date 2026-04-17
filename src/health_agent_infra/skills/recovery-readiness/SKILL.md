---
name: recovery-readiness
description: Classify recovery state, apply safety policy, and shape a training recommendation from the cross-domain state snapshot plus the day's cleaned Garmin evidence. Use when the user needs a bounded recommendation for today's session.
allowed-tools: Read, Bash(hai state snapshot *), Bash(hai state read *), Bash(hai clean *), Bash(hai writeback *), Bash(hai review *)
disable-model-invocation: false
---

# Recovery Readiness

You produce a single `TrainingRecommendation` JSON object from a day's state. Your job is three things, in order:

1. **Load state** — run `hai state snapshot` to load the cross-domain envelope the runtime has already projected. Supplement with `hai clean` deltas/ratios for the signals the snapshot doesn't compute (baseline ratios, spike-day counts, coverage fractions).
2. **Classify + apply policy** — from the loaded state, decide where the athlete sits on sleep, resting HR, HRV, training load, soreness, and overall recovery status. Apply the six policy gates.
3. **Shape the recommendation** — choose an action, attach goal-aware detail, compute confidence, write the rationale, and call `hai writeback --recommendation-json <path>`. The writeback tool validates the shape before persisting; it is your determinism check.

## Step 0 — Load state

**Primary read.** Call:

```
hai state snapshot --as-of <today> --user-id <user>
```

The JSON that comes back is governed by `reporting/docs/state_model_v1.md` and carries **per-domain missingness tokens**. You must read these tokens before reasoning about any field; they distinguish four cases (`absent`, `partial:<fields>`, `pending_user_input[:fields]`, `present`) per §5. A `null` field without its token is never safe to interpret.

Fields you rely on live under:

- `recovery.today` — `sleep_hours`, `resting_hr`, `hrv_ms`, `all_day_stress`, `manual_stress_score`, `acute_load`, `chronic_load`, `acwr_ratio`, `body_battery_end_of_day`.
- `running.today` — `total_distance_m`, `moderate_intensity_min`, `vigorous_intensity_min` (plus `derivation_path`; `session_count` is legitimately NULL when `derivation_path='garmin_daily'`).
- `goals_active` — list of active goals with optional `domain` scope.
- `recommendations.recent` — last N days' recommendations.
- `reviews.recent` — last N days' outcomes.
- `stress.today_garmin` / `stress.today_manual` — the two stress signals with their own missingness token.

If any required domain is `absent` or `partial`, surface that fact in your `uncertainty[]` and let the policy layer (R1, R5) do its work.

**Secondary read (optional).** For per-domain introspection use:

```
hai state read --domain <recovery|running|gym|nutrition|stress|notes|recommendations|reviews|goals> --since <date> [--until <date>]
```

Use this when you need a narrower slice than `snapshot` gives — e.g. to inspect one recent recommendation in full. Not the normal path.

**Raw summary supplement.** `hai state snapshot` does **not** include baseline ratios or coverage fractions. If you need `resting_hr_ratio_vs_baseline`, `hrv_ratio_vs_baseline`, `resting_hr_spike_days`, `training_load_ratio_vs_baseline`, or the coverage fractions, run `hai clean --evidence-json <path>` against the pulled evidence JSON. The `raw_summary` block in its stdout supplies these.

Missing fields mean the source did not report that signal. Do not fabricate.

## Richer Garmin signals (7B)

7B adds more fields, but **they don't all come from the same read surface**. Read this table carefully before you reach for a field:

### Fields on `snapshot.recovery.today`

The snapshot-level recovery view carries these Garmin-sourced fields. No secondary call needed:

- `sleep_hours`, `resting_hr`, `hrv_ms` — the original 7A.1 signals.
- `all_day_stress` (0–100, int) — Garmin's passive all-day stress integration.
- `acute_load`, `chronic_load`, `acwr_ratio` — Garmin's raw load values + a locally-computed `acute/chronic` ratio.
- `training_readiness_component_mean_pct` (0–100, float) — **locally-computed arithmetic mean** of Garmin's five Training Readiness component pcts. This is **not** Garmin's own overall Training Readiness score; Garmin doesn't export that number in its daily CSV. Garmin weights the components internally, so this mean can disagree with `training_readiness_level` (see below). Treat it as a rough summary, not as Garmin's own judgment.
- `body_battery_end_of_day` (0–100, int) — Garmin's energy reserve proxy at day-end.
- `manual_stress_score` — always NULL in v1 (user-reported intake ships with 7C).

### Fields on `snapshot.running.today`

The snapshot-level running view (daily-grain, `derivation_path='garmin_daily'`) carries:

- `total_distance_m` — aggregate distance for the day.
- `moderate_intensity_min`, `vigorous_intensity_min` — intensity-minute counts.
- `session_count`, `total_duration_s` — NULL by design on the `garmin_daily` derivation path (they'd require per-activity source data). Not a partial signal; do not flag.

### Fields only in `hai clean`'s `raw_summary`

These are **not** on the snapshot today-row yet. To read them, run `hai clean --evidence-json <path> --db-path <db>` against the pulled evidence JSON; the fields appear under the `raw_summary` key on stdout:

- `training_readiness_level` (categorical string — e.g. `"High"`, `"LOW"`, `"Moderate"`). Garmin's own categorical readiness band. **This is vendor-authored**, unlike the component mean above. When it disagrees with your agent-computed recovery status or with `training_readiness_component_mean_pct`, surface the disagreement in rationale and treat confidence cautiously.
- The five Training Readiness component pcts: `training_readiness_sleep_pct`, `_hrv_pct`, `_stress_pct`, `_sleep_history_pct`, `_load_pct`. Inspect components directly when the mean and level disagree.
- `garmin_acwr_ratio` — duplicate of `snapshot.recovery.today.acwr_ratio`, kept alongside:
- `acwr_status` (categorical string — e.g. `"Optimal"`). Garmin's own band for the acute/chronic ratio.

### How to use these in classification

Your existing deterministic bands (sleep debt, RHR, HRV, load) remain authoritative. The Garmin signals give you:

1. **A sanity cross-check.** If `recovery_status='impaired'` but `training_readiness_level='High'` (vendor-banded, not your local mean), name the disagreement in `rationale[]` as `agent_vendor_readiness_disagreement` and lower confidence from `high` to `moderate`.
2. **Extra context you couldn't derive yourself.** `body_battery_end_of_day`, `all_day_stress`, and intensity minutes are passive aggregates that your own bands don't try to reproduce. Surface them as informational lines in `rationale[]` when they support the conclusion (e.g., `all_day_stress=72 supports elevated sleep debt band`).
3. **Disagreement handling.** If your local `training_readiness_component_mean_pct` diverges from `training_readiness_level` (e.g., mean=70.0 but level="LOW"), that means Garmin's internal weighting prioritized a component you didn't. Do not trust the local mean alone; pair it with the categorical level in rationale and add `training_readiness_weighting_disagreement` to uncertainty.

### What you do NOT do

- Do not override your agent bands with Garmin bands; both are signals, neither is ground truth.
- Do not invent weighted blends.
- Do not treat `training_readiness_component_mean_pct` as a vendor score. It's a local arithmetic mean.

### Missingness semantics for these fields

Per state_model_v1.md §5, the snapshot's `missingness` token distinguishes:

- `unavailable_at_source:<fields>` — Garmin was queried and didn't return that field (common for overnight HRV, single-component readiness pcts, etc.). **This is the expected tag for passive Garmin gaps.** Do not treat it as "data collection failure"; it's "Garmin didn't record."
- `partial:<fields>` — day closed and user-reported fields are still missing.
- `pending_user_input:<fields>` — today before 23:30, user may still log.
- `absent` — no row at all.

When you see `unavailable_at_source:training_readiness_component_mean_pct` on `snapshot.recovery.missingness`, that means Garmin didn't record at least one of the five readiness components for that day (usually because overnight sleep wasn't tracked). Add a specific uncertainty token per such field (e.g. `training_readiness_unavailable_at_source`, `body_battery_unavailable_at_source`).

## Step 1 — Classify state

Produce these intermediate classifications before you reach for a recommendation. They are not persisted; they inform your reasoning and should appear in your `rationale[]`.

### Sleep debt band

| `sleep_hours` | Band |
|---|---|
| ≥ 7.5 | `none` |
| 7.0 – 7.4 | `mild` |
| 6.0 – 6.9 | `moderate` |
| < 6.0 | `elevated` |
| missing | `unknown` — add `sleep_record_missing` to uncertainty |

### Resting-HR baseline band (high-is-bad)

Compute `ratio = resting_hr / resting_hr_baseline`.

| Ratio | Band |
|---|---|
| ≥ 1.15 | `well_above` |
| 1.05 – 1.149 | `above` |
| 0.95 – 1.049 | `at` |
| < 0.95 | `below` |
| value or baseline missing | `unknown` — add `resting_hr_record_missing` or `baseline_window_too_short` |

### HRV baseline band (low-is-bad)

Compute `ratio = hrv_ms / hrv_baseline`.

| Ratio | Band |
|---|---|
| ≤ 0.95 | `below` |
| 1.02 – 1.099 | `above` |
| ≥ 1.10 | `well_above` |
| 0.95 – 1.019 | `at` |
| missing | `unknown` — add `hrv_unavailable` |

### Training load band

Compute `ratio = trailing_7d_training_load / training_load_baseline`.

| Ratio | Band |
|---|---|
| ≥ 1.4 | `spike` |
| 1.1 – 1.399 | `high` |
| 0.7 – 1.099 | `moderate` |
| < 0.7 | `low` |
| trailing missing | `unknown` — add `training_load_window_incomplete` |

If baseline is missing but trailing is present, fall back to absolute thresholds: `≥ 500` → `high`, `≥ 200` → `moderate`, otherwise `low`.

### Soreness signal

Pass through `cleaned_evidence.soreness_self_report` as the band. If missing, it's `unknown` and add `manual_checkin_missing` to uncertainty.

### Coverage band

| Condition | Coverage |
|---|---|
| sleep_hours OR soreness_self_report missing | `insufficient` |
| resting_hr OR trailing_7d_training_load missing | `sparse` |
| hrv_ms missing OR resting_hr_baseline missing | `partial` |
| all four present + baselines present | `full` |

### Recovery status

Count impaired and mild signals from the above bands:

- `impaired_signals += 1` for: `sleep_debt = elevated`, `soreness = high`, `resting_hr_band = well_above`, `load_band = spike`
- `mild_signals += 1` for: `sleep_debt = mild|moderate`, `soreness = moderate`, `resting_hr_band = above`, `hrv_band = below`, `load_band = high`

Derive:

| Signal counts | Status |
|---|---|
| impaired ≥ 2 | `impaired` |
| impaired ≥ 1 OR mild ≥ 2 | `mildly_impaired` |
| else | `recovered` |
| coverage = `insufficient` | `unknown` — skip further classification |

### Readiness score (0.0 – 1.0)

Only compute if coverage ≠ `insufficient`. Start at 1.0 and apply penalties:

| Signal | Penalty (subtract from score) |
|---|---|
| `sleep_debt = mild` | 0.05 |
| `sleep_debt = moderate` | 0.15 |
| `sleep_debt = elevated` | 0.25 |
| `soreness = moderate` | 0.10 |
| `soreness = high` | 0.20 |
| `resting_hr_band = above` | 0.10 |
| `resting_hr_band = well_above` | 0.20 |
| `resting_hr_band = below` | −0.02 (adds to score) |
| `hrv_band = below` | 0.15 |
| `hrv_band = above` or `well_above` | −0.05 |
| `load_band = high` | 0.05 |
| `load_band = spike` | 0.15 |

Clamp to `[0.0, 1.0]` and round to 2 decimals.

## Step 2 — Apply policy

Apply these six gates **in order**. The first block short-circuits evaluation. Every rule fire — block, soften, escalate, or allow — appends a `PolicyDecision` to `policy_decisions[]` in the output.

### R1 — require_min_coverage
If coverage = `insufficient`, block immediately. Emit:
```json
{"rule_id": "require_min_coverage", "decision": "block", "note": "coverage=insufficient; required inputs missing"}
```
and set action = `defer_decision_insufficient_signal`, confidence = `low`, action_detail = `{"reason": "policy_block"}`.

Otherwise emit an `allow` decision noting the coverage band and whether required inputs are all present.

### R2 — no_diagnosis
Check every string value in `rationale[]` and `action_detail` values (case-insensitive) for any of these banned tokens: `diagnosis`, `diagnose`, `diagnosed`, `syndrome`, `disease`, `disorder`, `condition`, `infection`, `illness`, `sick`. If any match, block with note naming the token. Rewrite your rationale instead of using banned words.

### R3 — bounded_action_envelope
The `action` field must be one of: `proceed_with_planned_session`, `downgrade_hard_session_to_zone_2`, `downgrade_session_to_mobility_only`, `rest_day_recommended`, `defer_decision_insufficient_signal`, `escalate_for_user_review`. If you proposed something else, block with note `action '<name>' not in v1 enum`.

### R4 — review_required
`follow_up` must be present and `review_at` must be within 24 hours of `issued_at`. If not, block.

### R5 — no_high_confidence_on_sparse_signal
If coverage = `sparse` and your confidence = `high`, soften to `moderate`. Emit a `soften` decision with note `capped confidence to moderate on sparse signal (<uncertainty-tokens>)`.

### R6 — resting_hr_spike_escalation
If `raw_summary.resting_hr_spike_days >= 3`, override the action to `escalate_for_user_review` with `action_detail = {"reason_token": "resting_hr_spike_3_days_running", "consecutive_days": <N>}`. Emit an `escalate` decision.

## Step 3 — Shape the recommendation

If policy blocked (R1–R4), you're done — output the defer. Otherwise pick an action:

| Recovery status | Planned session | Action |
|---|---|---|
| `recovered` | any | `proceed_with_planned_session` |
| `mildly_impaired` | hard / intervals / race | `downgrade_hard_session_to_zone_2` with `{"target_intensity": "zone_2", "target_duration_minutes": 45}` |
| `mildly_impaired` | other | `proceed_with_planned_session` with caveat `{"caveat": "keep_effort_conversational"}` |
| `impaired` | hard / intervals / race | `downgrade_session_to_mobility_only` with `{"reason_token": "impaired_recovery_with_hard_plan"}` |
| `impaired` | other | `rest_day_recommended` with `{"suggested_activity": "walk_or_mobility"}` |

R6 overrides any of the above to `escalate_for_user_review`.

### Goal-conditioned detail

If `cleaned_evidence.active_goal` is set AND action = `proceed_with_planned_session`, attach `{"active_goal": <goal>}` to `action_detail`. **Do not** invent numeric caps (RPE, zone, duration, set count). Periodization judgment belongs to the session-planning agent that consumes this recommendation, not to you. Surfacing the goal in the output is enough.

### Rationale

Include one line per band and one line per signal that meaningfully informed the decision. Example rationale entries: `sleep_debt=none`, `soreness_signal=moderate`, `resting_hr_vs_baseline=above`, `training_load_trailing_7d=high`, `hrv_vs_baseline=below`, `active_goal=strength_block`. Keep to 5–8 lines.

### Confidence

Start at `high` if coverage = `full`, `moderate` if coverage = `partial`, `moderate` if coverage = `sparse` (R5 will enforce). Use `low` on insufficient-signal blocks. Do not exceed `moderate` when any baseline-window token is in uncertainty.

### Uncertainty

Pass through every uncertainty token you collected during classification. Sort alphabetically, deduplicate.

### Follow-up

Set `review_at` to next morning at `07:00:00+00:00`. `review_question` depends on the action:

- `proceed_with_planned_session` → "Did today's session feel appropriate for your recovery?"
- `downgrade_hard_session_to_zone_2` → "Did yesterday's downgrade to Zone 2 improve how today feels?"
- `downgrade_session_to_mobility_only` → "Did yesterday's mobility-only day help your recovery?"
- `rest_day_recommended` → "Did yesterday's rest day help your recovery?"
- `defer_decision_insufficient_signal` → "Did you decide on a session yesterday? How did it go?"
- `escalate_for_user_review` → "You had a persistent signal we flagged. Did you take any action?"

`review_event_id` format: `rev_<review_date>_<user_id>_<recommendation_id>`.

## Output schema

Emit a single JSON object matching `TrainingRecommendation` (see `schemas.py`). `hai writeback` will validate it:

```json
{
  "schema_version": "training_recommendation.v1",
  "recommendation_id": "rec_<as_of_date>_<user_id>_01",
  "user_id": "<user_id>",
  "issued_at": "<now ISO-8601>",
  "for_date": "<as_of_date>",
  "action": "<ActionKind>",
  "action_detail": {...} | null,
  "rationale": ["..."],
  "confidence": "low" | "moderate" | "high",
  "uncertainty": ["..."],
  "follow_up": {
    "review_at": "<ISO-8601 UTC>",
    "review_question": "...",
    "review_event_id": "..."
  },
  "policy_decisions": [
    {"rule_id": "...", "decision": "allow|soften|block|escalate", "note": "..."}
  ],
  "bounded": true
}
```

`recommendation_id` is idempotent on `(for_date, user_id)` so re-running on the same day doesn't produce a new row.

## Invariants

- You never fabricate values for missing evidence. Missing means missing.
- You never emit an `action` outside the six-value enum.
- You never produce a recommendation without a follow-up within 24 hours.
- You never use diagnosis-shaped language (R2).
- Your rationale is the audit trail — if a decision isn't reasoned in `rationale[]` or `policy_decisions[]`, it didn't happen.
