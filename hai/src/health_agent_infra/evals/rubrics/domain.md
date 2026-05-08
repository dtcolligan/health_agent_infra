# Domain eval rubric (classify + policy)

Every domain scenario is scored along three axes. Axes the runner can
evaluate deterministically get ``pass`` / ``fail`` verdicts; the
skill-narration axis is marked ``skipped_requires_agent_harness`` per
the v1 scope.

## Axis 1 — classified_bands

The scenario's ``expected.classified`` dict lists one or more band /
score keys. The axis passes iff every listed key has an exact match in
the classify result. Unasserted keys are ignored.

Typical keys asserted per domain:

- recovery: ``sleep_debt_band``, ``resting_hr_band``, ``hrv_band``,
  ``training_load_band``, ``coverage_band``, ``recovery_status``.
- running: ``intensity_band``, ``recent_hard_count_band``,
  ``acwr_freshness_band``, ``running_status``, ``coverage_band``.
- sleep: ``sleep_duration_band``, ``sleep_quality_band``,
  ``sleep_timing_band``, ``sleep_efficiency_band``, ``coverage_band``.
- stress: ``garmin_stress_band``, ``manual_stress_band``,
  ``body_battery_trend_band``, ``composite_stress_state``, ``coverage_band``.
- strength: ``recent_volume_band``, ``lower_body_freshness_band``,
  ``upper_body_freshness_band``, ``coverage_band``.
- nutrition (macros-only in v1): ``calorie_balance_band``,
  ``protein_sufficiency_band``, ``hydration_band``,
  ``micronutrient_coverage`` (must be ``unavailable_at_source``),
  ``coverage_band``, ``nutrition_status``.

## Axis 2 — policy_decisions

The scenario's ``expected.policy`` dict can assert any combination of:

- ``forced_action`` — policy's R-rule-forced action, e.g.
  ``rest_day_recommended`` for recovery R6 or
  ``sleep_debt_repayment_day`` for sleep chronic deprivation.
- ``capped_confidence`` — set to ``"moderate"`` when the R-sparse-
  signal cap fires, ``null`` otherwise.
- ``fired_rule_ids`` — set of rule ids (e.g. ``R1``, ``R5``, ``R6``,
  ``R-chronic-deprivation``) that fired, compared order-insensitively.

The axis fails on the first mismatch. Missing keys are ignored.

## Axis 3 — rationale_quality (skipped)

Rationale prose, review_question phrasing, and uncertainty prose live
in the domain skill markdown, not in ``policy.py``. The runner never
invokes skills. This axis is marked
``skipped_requires_agent_harness`` so the gap is visible. A
skill-harness follow-up would run the domain skill via Claude Code
subprocess and score narration against a per-domain prose rubric.
