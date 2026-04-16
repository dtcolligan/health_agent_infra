<!-- rec_2026-04-16_u_recovered_with_easy_plan_01 -->
## 2026-04-16 — proceed_with_planned_session

- confidence: high
- rationale: sleep_debt=none, soreness_signal=low, resting_hr_vs_baseline=at, training_load_trailing_7d=high, hrv_vs_baseline=above
- uncertainty: (none)
- review_at: 2026-04-17T07:00:00+00:00
- issued_at: 2026-04-16T07:15:00+00:00

<!-- rec_2026-04-16_u_mildly_impaired_with_hard_plan_01 -->
## 2026-04-16 — downgrade_hard_session_to_zone_2

- confidence: high
- rationale: sleep_debt=mild, soreness_signal=moderate, resting_hr_vs_baseline=above, training_load_trailing_7d=high, hrv_vs_baseline=below
- uncertainty: (none)
- detail: `{"target_duration_minutes": 45, "target_intensity": "zone_2"}`
- review_at: 2026-04-17T07:00:00+00:00
- issued_at: 2026-04-16T07:15:00+00:00

<!-- rec_2026-04-16_u_impaired_with_hard_plan_01 -->
## 2026-04-16 — downgrade_session_to_mobility_only

- confidence: high
- rationale: sleep_debt=elevated, soreness_signal=high, resting_hr_vs_baseline=well_above, training_load_trailing_7d=spike, hrv_vs_baseline=below
- uncertainty: (none)
- detail: `{"reason_token": "impaired_recovery_with_hard_plan"}`
- review_at: 2026-04-17T07:00:00+00:00
- issued_at: 2026-04-16T07:15:00+00:00

<!-- rec_2026-04-16_u_rhr_spike_three_days_01 -->
## 2026-04-16 — escalate_for_user_review

- confidence: high
- rationale: sleep_debt=none, soreness_signal=moderate, resting_hr_vs_baseline=well_above, training_load_trailing_7d=high, hrv_vs_baseline=below
- uncertainty: (none)
- detail: `{"consecutive_days": 3, "reason_token": "resting_hr_spike_3_days_running"}`
- review_at: 2026-04-17T07:00:00+00:00
- issued_at: 2026-04-16T07:15:00+00:00

<!-- rec_2026-04-16_u_insufficient_signal_01 -->
## 2026-04-16 — defer_decision_insufficient_signal

- confidence: low
- rationale: policy blocked substantive recommendation, hrv_unavailable, manual_checkin_missing, resting_hr_record_missing, sleep_record_missing
- uncertainty: hrv_unavailable, manual_checkin_missing, resting_hr_record_missing, sleep_record_missing
- detail: `{"reason": "policy_block"}`
- review_at: 2026-04-17T07:00:00+00:00
- issued_at: 2026-04-16T07:15:00+00:00

<!-- rec_2026-04-16_u_sparse_signal_01 -->
## 2026-04-16 — proceed_with_planned_session

- confidence: moderate
- rationale: sleep_debt=none, soreness_signal=moderate, resting_hr_vs_baseline=unknown, training_load_trailing_7d=high
- uncertainty: hrv_unavailable, resting_hr_record_missing
- detail: `{"caveat": "keep_effort_conversational"}`
- review_at: 2026-04-17T07:00:00+00:00
- issued_at: 2026-04-16T07:15:00+00:00

<!-- rec_2026-04-16_u_tailoring_recovered_strength_block_01 -->
## 2026-04-16 — proceed_with_planned_session

- confidence: high
- rationale: sleep_debt=none, soreness_signal=low, resting_hr_vs_baseline=at, training_load_trailing_7d=high, hrv_vs_baseline=above, active_goal=strength_block, strength_block tailoring: RPE<=8, <=5 working sets, compound focus
- uncertainty: (none)
- detail: `{"active_goal": "strength_block", "rpe_cap": 8, "session_focus": "compound_heavy", "set_cap": 5}`
- review_at: 2026-04-17T07:00:00+00:00
- issued_at: 2026-04-16T07:15:00+00:00

<!-- rec_2026-04-16_u_tailoring_recovered_endurance_taper_01 -->
## 2026-04-16 — proceed_with_planned_session

- confidence: high
- rationale: sleep_debt=none, soreness_signal=low, resting_hr_vs_baseline=at, training_load_trailing_7d=high, hrv_vs_baseline=above, active_goal=endurance_taper, endurance_taper tailoring: Z2 ceiling, <=45 min, easy aerobic focus
- uncertainty: (none)
- detail: `{"active_goal": "endurance_taper", "duration_cap_min": 45, "session_focus": "aerobic_easy", "zone_cap": 2}`
- review_at: 2026-04-17T07:00:00+00:00
- issued_at: 2026-04-16T07:15:00+00:00

