# Synthesis eval rubric

Every synthesis scenario is scored along up to five deterministic axes
plus one explicitly-skipped skill-narration axis.

## Axis 1 — x_rules_fired

The scenario's ``expected.x_rules_fired`` lists the set of X-rule ids
(``X1a``, ``X1b``, ``X2``, ``X3a``, ``X3b``, ``X4``, ``X5``, ``X6a``,
``X6b``, ``X7``, ``X9``) that must fire. Comparison is
order-insensitive and deduplicated (a rule that emits multiple
per-domain firings still shows once).

## Axis 2 — final_actions

Per-domain mapping of ``{domain: expected_action}``. Scenarios
commonly assert on the domain the X-rule targets (e.g. X1a soften
flipping recovery or running from ``proceed_with_planned_*`` to
``downgrade_hard_session_to_zone_2`` / ``downgrade_to_easy_aerobic``).

Nutrition's Phase-B ``X9`` does **not** change the action; scenarios
that exercise X9 should assert the action is unchanged and instead
check ``action_detail`` via the rubric's prose notes (or extend
``score_synthesis_result`` in a later phase).

## Axis 3 — final_confidences

Per-domain mapping of ``{domain: expected_confidence}``. The only
confidence-mutating rule in v1 is ``X7`` (``cap_confidence``),
capping to ``moderate``. Scenarios without ``cap_confidence`` firings
inherit the proposal's confidence.

## Axis 4 — validation_errors

For scenarios that carry a ``_defect`` marker on a proposal (stale
``schema_version``, out-of-enum ``action``, missing required field,
etc.), the axis asserts the writeback validator rejected the proposal
with the correct ``invariant`` id. The scenario can carry a list of
expected rejections; the axis fails on the first mismatch.

## Axis 5 — synthesis_error

Scenarios that expect ``run_synthesis`` to refuse (e.g. s4-style: all
proposals rejected at writeback, so synthesis has nothing to consume)
set ``expected.synthesis_error = "expected"``. The axis passes when
``SynthesisError`` was raised and fails when no error was raised.

Inverse assertion ``"none"`` is supported for scenarios that expect
synthesis to succeed.

## Axis 6 — rationale_quality (skipped)

The daily-plan-synthesis skill is an agent artifact that the runner
does not invoke. Phase 2.5 Track B Condition 3 attached a
skill-harness follow-up to Phase 3; Phase 6 inherits the gap. Each
scenario carries this axis with the
``skipped_requires_agent_harness`` marker to keep the gap visible.
