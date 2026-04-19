# Adding a domain

Domain modules are the v1 runtime's primary extension surface. Each
domain ships six files and one skill. This doc is the **checklist**
— for the full conceptual walk-through (required vs optional
extension points, synthesis touchpoints, state-shape expectations,
what not to change) see
[`../how_to_add_a_domain.md`](../how_to_add_a_domain.md). Reference
implementations are the six v1 domains (recovery, running, sleep,
stress, strength, nutrition).

## The six-part pattern

```
src/health_agent_infra/domains/<d>/
    __init__.py
    schemas.py     # DomainProposal + DomainRecommendation dataclasses
    classify.py    # bands, scores, coverage, status
    policy.py      # R-rule mechanical evaluator → PolicyResult
    signals.py     # (optional) snapshot-level signal extraction helper
    intake.py      # (optional) raw-table CLI intake helper
```

Plus one skill:

```
src/health_agent_infra/skills/<d>-readiness/SKILL.md
```

(skills named by what they reason about: ``recovery-readiness``,
``sleep-quality``, ``stress-regulation``, ``strength-readiness``,
``nutrition-alignment``).

## Step 1 — schema

``schemas.py`` defines two frozen dataclasses:

- ``<Domain>Proposal`` — the shape the skill emits. Mirrors
  ``BoundedRecommendation`` but with ``proposal_id`` instead of
  ``recommendation_id``. ``action`` is constrained to a
  domain-specific enum.
- ``<Domain>Recommendation`` — the shape the runtime writes after
  synthesis. Carries the same action enum plus
  ``recommendation_id``, ``daily_plan_id``, ``follow_up``.

Both should use ``bounded=True`` in every instance and list
``policy_decisions`` as a non-empty tuple of ``PolicyDecision`` rows.

Register the new schema + action enum in:

- ``core/writeback/proposal.py :: SUPPORTED_DOMAINS +
  PROPOSAL_SCHEMA_VERSIONS + DOMAIN_ACTION_ENUMS``
- ``core/synthesis.py :: RECOMMENDATION_SCHEMA_BY_DOMAIN``

If the domain has a baseline "hard" action that cross-domain X-rules
may soften or block, register it in
``core/synthesis_policy.py :: _DOMAIN_ACTION_REGISTRY``.

## Step 2 — classify

``classify.py :: classify_<d>_state(signals_or_evidence, thresholds)``
returns a frozen ``Classified<Domain>State`` dataclass with per-band
fields, a composite ``<d>_status``, a ``readiness_score`` (or
``None`` when coverage=insufficient), a ``coverage_band``, and a
sorted tuple of uncertainty tokens.

Every band threshold must come from ``thresholds`` (config-driven);
no literal cutoffs. Add the new thresholds to
``core/config.py :: DEFAULT_THRESHOLDS`` under
``classify.<d>.*`` namespaces.

## Step 3 — policy

``policy.py :: evaluate_<d>_policy(classified, signals_or_empty,
thresholds)`` returns a frozen ``<Domain>PolicyResult`` with:

- ``policy_decisions`` — tuple of ``PolicyDecision(rule_id,
  decision, note)`` rows, one per R-rule checked.
- ``forced_action`` — the v1-enum action the skill MUST honour, or
  ``None`` if no R-rule forced one.
- ``forced_action_detail`` — structured context the skill surfaces
  on the proposal's ``action_detail``.
- ``capped_confidence`` — ``"moderate"`` when R-sparse-signal
  fires, else ``None``.

At minimum implement:

- ``require_min_coverage`` (R1) — sufficient inputs present.
- ``no_high_confidence_on_sparse_signal`` (R5) — sparse coverage
  caps confidence.
- one domain-specific escalation rule (spike / deprivation / etc).

Rule ids are stable strings; reusing an id means tests + eval
scenarios referring to that id keep working.

## Step 4 — skill

``skills/<d>-readiness/SKILL.md`` is the judgment layer. Shape:

1. Read the snapshot block's ``classified_state`` +
   ``policy_result``. Honour ``forced_action`` and
   ``capped_confidence`` — these are runtime-fixed.
2. Pick an action from the domain enum consistent with the policy
   constraints. If ``forced_action`` is set, use it.
3. Compose 3–6 lines of rationale referencing the bands that drove
   the decision. Don't recompute arithmetic the classifier already
   ran.
4. List uncertainty tokens from ``classified.uncertainty``.
5. Emit a ``DomainProposal`` and call ``hai propose``.

Hard constraint: the skill must stay under ~100 lines. If it grows
past that, deterministic work is leaking in — move it to code.

## Step 5 — snapshot wiring

``core/state/snapshot.py :: build_snapshot`` must include the new
domain's block: ``{evidence, raw_summary, classified_state,
policy_result, missingness}``. If the domain requires a new
accepted_*_state_daily table, add a projector under
``core/state/projectors/`` and a migration under
``core/state/migrations/``.

## Step 6 — tests + evals

Add:

- ``safety/tests/test_<d>_schemas.py`` — schema validation.
- ``safety/tests/test_<d>_classify.py`` — one test per band
  boundary per signal.
- ``safety/tests/test_<d>_policy.py`` — one test per R-rule
  firing + non-firing.
- ``safety/tests/test_<d>_skill_gates.py`` — skill-boundary
  contract (the skill does NOT change forced actions, DOES compose
  rationale, etc).
- ``safety/evals/scenarios/<d>/*.json`` — ≥ 3 scenarios (baseline,
  R-rule firing, coverage gap).

``safety/tests/test_eval_scenarios.py`` has a parametrized test
that runs every ``SUPPORTED_DOMAINS`` member through the eval
runner, so a new domain is picked up automatically once its
scenarios are committed.

## Cross-domain hooks

Consider whether the new domain should participate in an X-rule:

- Does a hard session in this domain consume the same recovery
  reserve as recovery / running / strength? Then X1 / X6 should
  include it.
- Does this domain produce a signal that should soften another
  domain? Add a new X-rule in ``synthesis_policy.py`` following the
  X1a pattern.

Every new X-rule needs a scenario under
``safety/evals/scenarios/synthesis/`` and an entry in the
``test_synthesis_scenarios_cover_key_x_rules`` floor check.

## Checklist

- [ ] ``domains/<d>/{schemas,classify,policy}.py``
- [ ] ``skills/<d>-readiness/SKILL.md`` under 100 lines
- [ ] Thresholds added to ``core/config.py``
- [ ] Writeback registry + synthesis registry updated
- [ ] ``hai state snapshot`` returns the new block
- [ ] Migrations committed (if new tables)
- [ ] Tests for schema / classify / policy / skill-gates
- [ ] Eval scenarios ≥ 3 committed
- [ ] ``reporting/docs/state_model_v1.md`` updated with the new table
- [ ] ``reporting/docs/architecture.md`` pipeline ASCII updated
- [ ] ``reporting/docs/x_rules.md`` updated if an X-rule changed
