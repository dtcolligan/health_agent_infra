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

Every rule has three surfaces. The **internal id** (``X1a``, ``X3b``,
``X9``) is the stable handle — it appears in DB rows, JSONL audit
records, eval-scenario fixtures, and the ``plan.x_rules_fired``
array. The **public name** is a machine-readable slug that shows up in
``hai explain`` output, agent-facing JSON (``firing["public_name"]``),
and the tables below. The **human explanation** (see §"Human
explanations" below) is a one-sentence description used when an agent
or skill narrates the firing back to the user, surfaced as
``firing["human_explanation"]`` on the explain bundle and in the
``--text`` render. Renaming an internal id would break audit
continuity; the public name and human explanation are free to evolve.

The mappings live in ``X_RULE_PUBLIC_NAMES`` and
``X_RULE_DESCRIPTIONS`` in
``src/health_agent_infra/core/synthesis_policy.py``. Adding a rule
means appending a row in both maps and adding the relevant column
entries below so code and docs never drift apart. Slug pattern:
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

## Human explanations

Each rule has a one-sentence description surfaced by ``hai explain``
(JSON field ``firing["human_explanation"]`` and the text-render
``explanation:`` line). Sentences never name raw threshold numbers —
they describe the *qualitative state* synthesis already classified
("moderate", "elevated", "depleted"), so a future threshold change
doesn't invalidate the sentence.

| ID | Human explanation |
|---|---|
| X1a | Sleep debt is moderate, so hard sessions are softened to reduce injury risk while sleep recovers. |
| X1b | Sleep debt is elevated, so hard sessions are blocked until sleep catches up. |
| X2 | Fuelling is low (calorie deficit or insufficient protein), so hard strength or recovery sessions are softened to protect adaptation. |
| X3a | Training load is spiking above recent baseline, so hard sessions are softened to reduce injury risk. |
| X3b | Training load is spiking well above recent baseline, so hard sessions are blocked until load settles. |
| X4 | Yesterday's heavy lower-body strength means today's hard run is softened to an easy aerobic effort. |
| X5 | Yesterday's long run or hard intervals means today's lower-body strength is softened to technique or accessory work. |
| X6a | Body battery is low, so hard sessions are softened to match available capacity. |
| X6b | Body battery is depleted, so hard sessions are blocked — today should be rest or very light. |
| X7 | Stress is elevated today, so recommendation confidence is capped at moderate because the signal is noisier than usual. |
| X9 | Training is hard today, so the nutrition target bumps protein to support adaptation. |

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

The packaged synthesis scenario floor currently covers X1a, X1b, X2, X3a,
X3b, X6a, X7, and X9 under
``src/health_agent_infra/evals/scenarios/synthesis/``.
``verification/tests/test_eval_scenarios.py ::
test_synthesis_scenarios_cover_key_x_rules`` is the floor-check for that
scenario set.

X4 and X5 have dedicated unit/integration tests in
``verification/tests/test_synthesis_x3_x4_x5_strength.py`` because they need
prior-day running/strength state that the scenario authoring layer does not
yet model cleanly. X6b has direct synthesis-policy coverage in
``verification/tests/test_synthesis_policy.py``. Moving X4/X5/X6b into
packaged JSON scenarios is future eval-authoring work, not a runtime v1 gap.
