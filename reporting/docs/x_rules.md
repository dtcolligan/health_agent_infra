# X-rule catalogue

Cross-domain synthesis rules — the runtime's mechanical mediation
between per-domain proposals. Implemented in
``src/health_agent_infra/core/synthesis_policy.py`` with one
evaluator per rule.

X-rules run in two phases:

- **Phase A** — ``(snapshot, proposals) → firings``. Runs BEFORE
  the synthesis skill composes rationale. Tiers:
  ``soften | block | cap_confidence``. Output firings drive
  mechanical mutation of copy-on-write drafts.
- **Phase B** — ``(snapshot, drafts) → firings``. Runs AFTER the
  skill returns. Tier: ``adjust``. Restricted by a write-surface
  guard to mutating ``action_detail`` on a fixed registry of target
  domains; cannot change any action or touch non-target domains.

All thresholds are read from ``~/.config/hai/thresholds.toml`` under
the ``[synthesis.x_rules]`` section. Defaults live in
``core/config.py :: DEFAULT_THRESHOLDS``.

## Rule naming

Every rule has two names. The **internal id** (``X1a``, ``X3b``, ``X9``)
is the stable handle — it appears in DB rows, JSONL audit records,
eval-scenario fixtures, and the ``plan.x_rules_fired`` array. The
**public name** is a readable slug that shows up in ``hai explain``
output, agent-facing JSON (``firing["public_name"]``), and the tables
below. Renaming an internal id would break audit continuity; the public
name is free to evolve.

The mapping lives in ``X_RULE_PUBLIC_NAMES`` in
``src/health_agent_infra/core/synthesis_policy.py``. Adding a rule
means appending a row there and adding the **Public name** column entry
in the relevant table here so the two never drift apart. Slug pattern:
``<trigger>-<tier_verb>-<target>`` — the tier verb mirrors the tier
taxonomy (``softens`` / ``blocks`` / ``caps-confidence`` / ``bumps``).

## Phase A rules

| ID | Public name | Trigger | Target | Tier | Mutation |
|---|---|---|---|---|---|
| X1a | sleep-debt-softens-hard | ``sleep.classified_state.sleep_debt_band == moderate`` AND a hard proposal exists | each hard proposal's domain | soften | action → domain's ``downgrade_action`` |
| X1b | sleep-debt-blocks-hard | ``sleep.classified_state.sleep_debt_band == elevated`` AND a hard proposal exists | each hard proposal's domain | block | action → domain's ``escalate_action`` |
| X2 | underfuelling-softens-hard | ``nutrition.classified_state.calorie_deficit_kcal ≥ 500`` OR ``protein_ratio < 0.7`` AND a hard strength or recovery proposal exists | strength / recovery | soften | action → domain's ``downgrade_action`` |
| X3a | load-spike-softens-hard | ``1.3 ≤ recovery.today.acwr_ratio < 1.5`` AND a hard proposal exists | each hard proposal's domain | soften | action → domain's ``downgrade_action`` |
| X3b | load-spike-blocks-hard | ``recovery.today.acwr_ratio ≥ 1.5`` AND a hard proposal exists | each hard proposal's domain | block | action → domain's ``escalate_action`` |
| X4 | lower-body-sequencing-softens-run | Yesterday's strength = heavy lower body AND running intervals/tempo proposed today | running | soften | action → ``downgrade_to_easy_aerobic`` |
| X5 | endurance-fatigue-softens-strength | Yesterday's running = long run or hard intervals AND lower-body strength proposed today | strength | soften | action → ``downgrade_to_technique_or_accessory`` |
| X6a | body-battery-low-softens-hard | ``stress.today_body_battery < 30`` AND a hard proposal exists | each hard proposal's domain | soften | action → domain's ``downgrade_action`` |
| X6b | body-battery-depleted-blocks-hard | ``stress.today_body_battery < 15`` AND a hard proposal exists | each hard proposal's domain | block | action → domain's ``escalate_action`` |
| X7 | stress-elevated-caps-confidence | ``stress.classified_state.garmin_stress_band ∈ {high, very_high}`` | every proposal's domain | cap_confidence | confidence → ``moderate`` (no action mutation) |

## Phase B rules

| ID | Public name | Trigger | Target | Tier | Mutation |
|---|---|---|---|---|---|
| X9 | training-intensity-bumps-protein | Any training-domain (recovery / running / strength) draft carries a hard baseline action AND a nutrition draft exists | nutrition | adjust | action_detail appended with protein-target multiplier + ``reason_token=x9_training_intensity_bump`` (action unchanged) |

## Tier precedence

When two Phase A firings target the same proposal on the same field:

- ``block`` > ``soften`` > ``allow`` / no-op
- ``cap_confidence`` is independent of soften/block — it layers on
  top.
- ``adjust`` (Phase B) is scoped so narrowly (one field, one
  registered domain) that collisions don't arise with Phase A
  tiers.

See ``core/synthesis_policy.py :: TIER_PRECEDENCE`` for the
authoritative map.

## Orphan-firing invariant

Every X-rule evaluator emits firings only for domains that appear in
the proposal set, so by construction no firing is "orphaned" (target
= a domain not in the bundle). The runtime still stamps each
firing's row in ``x_rule_firing`` with an ``orphan`` flag so a
future rule that emits from snapshot-only signals without iterating
proposals can be caught at audit time rather than silently leaving
dead rows. See Phase 2.5 Track B Condition 1.

## Demoted / rejected rules

The rebuild plan previously scoped two rules that were cut:

- **X8** (≥3 domains independently propose rest → restructure into a
  unified recovery day): demoted to pure synthesis judgment. There
  is no mechanical ``restructure`` transform that survives audit.
- **X10** (sleep-recommendation-tracks-next-day-plan): rejected as
  too opinionated; stays as ambient synthesis judgment.

Neither appears in the runtime. If either is re-added they get a
new id.

## Config keys

Representative keys under ``[synthesis.x_rules]``:

```toml
[synthesis.x_rules.x1a]
sleep_debt_trigger_band = "moderate"

[synthesis.x_rules.x1b]
sleep_debt_trigger_band = "elevated"

[synthesis.x_rules.x2]
deficit_kcal_min = 500.0
protein_ratio_max = 0.7

[synthesis.x_rules.x3a]
acwr_ratio_lower = 1.3
acwr_ratio_upper = 1.5

[synthesis.x_rules.x3b]
acwr_ratio_min = 1.5

[synthesis.x_rules.x6a]
body_battery_max = 30

[synthesis.x_rules.x6b]
body_battery_max = 15

[synthesis.x_rules.x7]
very_high_min_score = 80
high_min_score = 60
moderate_min_score = 40
stress_trigger_bands = ["high", "very_high"]
```

Run ``hai config show`` to print the effective merged config
(defaults + user overrides).

## Eval coverage

Every Phase A rule above (X1a, X1b, X2, X3a, X3b, X6a, X7) plus the
Phase B rule (X9) has at least one scenario under
``safety/evals/scenarios/synthesis/``. ``safety/tests/test_eval_scenarios.py
:: test_synthesis_scenarios_cover_key_x_rules`` is the floor-check
that asserts this set is always exercised.

X4 and X5 currently have Phase A evaluators but no dedicated
scenario — they require proposals for strength and running on
sequential days with the right prior-day volume / session shape.
Adding them requires extending the scenario authoring layer to
support prior-day state, which is tracked as a Phase 7 follow-up,
not a v1 gap.
