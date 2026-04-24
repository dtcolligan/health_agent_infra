# How to add a domain

This is a contributor guide for adding a seventh domain to the
runtime. It describes the stabilized six-domain architecture that
shipped in the post-v0.1.x cycle — recovery, running, sleep,
stress, strength, nutrition — and assumes those domains are the
reference implementations you should read alongside this doc.

A shorter checklist-style companion lives at
[`domains/README.md`](domains/README.md); this doc is the conceptual
reference it points at. The two intentionally overlap on the
"required files" list; if they drift, this doc is authoritative on
wiring and the checklist is authoritative on "did I forget
anything."

## When this doc applies

Use this guide when you want to add a new reasoning domain — a new
thing the runtime can classify, evaluate policy over, and commit a
per-domain recommendation for (e.g. hydration, cycling, mobility,
resistance-conditioning cross-training). It does **not** apply to:

- adding a new **signal within an existing domain** — that's a
  projector / classifier change inside one of the existing six, not
  a new domain;
- adding a new **pull source** — that's an adapter, see
  [`how_to_add_a_pull_adapter.md`](how_to_add_a_pull_adapter.md);
- adding a new **X-rule** over existing domains — that's a
  synthesis change, see [`x_rules.md`](x_rules.md).

Adding a domain is the largest extension surface in the runtime. It
touches intake, projection, snapshot, classify, policy, synthesis,
writeback, skill, tests, evals, and docs. Expect the diff to cross
roughly a dozen files even for a small domain.

## Minimum domain contract (required)

Every v1 domain ships the same shape. The minimum is:

```
src/health_agent_infra/domains/<d>/
    __init__.py                # re-exports classify / policy / schemas
    schemas.py                 # <Domain>Proposal + <Domain>Recommendation
    classify.py                # deterministic bands + coverage + status
    policy.py                  # R-rule evaluator
```

…plus the matching wiring in `core/`:

```
core/writeback/proposal.py     # SUPPORTED_DOMAINS, PROPOSAL_SCHEMA_VERSIONS, DOMAIN_ACTION_ENUMS
core/synthesis.py              # RECOMMENDATION_SCHEMA_BY_DOMAIN
core/synthesis_policy.py       # _DOMAIN_ACTION_REGISTRY (if domain has hard actions)
core/state/snapshot.py         # new block in build_snapshot output
```

…and one skill:

```
src/health_agent_infra/skills/<d>-readiness/SKILL.md
```

…and tests + evals under `safety/`. Everything below is a
walkthrough of these files in the order you'd write them.

### 1. Schemas

[`domains/<d>/schemas.py`](../../src/health_agent_infra/domains/running/schemas.py)
defines two frozen dataclasses:

- **`<Domain>Proposal`** — the shape the skill emits and `hai
  propose` validates. Its field set must equal
  `DOMAIN_PROPOSAL_FIELDS` from
  [`core/schemas.py`](../../src/health_agent_infra/core/schemas.py).
  `action` narrows to a domain-specific `Literal`; `domain`
  defaults to the string name.
- **`<Domain>Recommendation`** — the post-synthesis shape the
  runtime writes. Its field set must equal
  `BOUNDED_RECOMMENDATION_FIELDS`. Same action enum, plus
  `recommendation_id`, `daily_plan_id`, `follow_up`.

Both are frozen dataclasses. Both carry `bounded=True`. Both reject
`follow_up` / `daily_plan_id` on the proposal shape (that's
synthesis's job to assign).

`<Domain>Proposal` is the contract the `<d>-readiness` skill emits,
`hai propose` validates, and `proposal_log` persists. Breaking it
breaks every downstream caller — this is the tightest part of the
domain surface.

Action enum: a short, finite set of v1 actions. Every domain's enum
includes at least `defer_decision_insufficient_signal` and an
escalate path (either `escalate_for_user_review` or a
domain-specific equivalent, like sleep's
`sleep_debt_repayment_day`). See the six existing enums in
[`core/writeback/proposal.py :: DOMAIN_ACTION_ENUMS`](../../src/health_agent_infra/core/writeback/proposal.py)
for prior art.

### 2. Classify

[`domains/<d>/classify.py`](../../src/health_agent_infra/domains/running/classify.py)
exposes `classify_<d>_state(signals_or_evidence, thresholds=None)`
returning a frozen `Classified<Domain>State` with:

- one or more band fields (e.g. `freshness_band`,
  `weekly_mileage_trend_band`) — each a small string enum including
  a `"unknown"` variant.
- a `coverage_band` ∈ {`full`, `partial`, `sparse`,
  `insufficient`} with the same meaning as every other domain:
  `insufficient` blocks via R-coverage; `sparse` caps confidence via
  R-sparse.
- a composite `<d>_status` ∈ {`ready`, `conditional`, `hold`,
  `unknown`} (naming may vary by domain — see sleep's
  `sleep_readiness_status`).
- a numeric `readiness_score` ∈ [0.0, 1.0] or `None` when
  `coverage=insufficient`.
- a sorted, deduped `uncertainty` tuple of stable reason tokens.

Every threshold flows from
[`core/config.py :: DEFAULT_THRESHOLDS`](../../src/health_agent_infra/core/config.py)
under a `classify.<d>.*` namespace. No literal cutoffs. A
user-TOML override at load time retunes triggers without editing
code; this is a non-negotiable rule, and tests pin it for the
existing six domains.

The classifier is the runtime's authority on "what is the state of
this domain today." Any domain-level narration a skill produces
later has to refer to these bands by name — never recompute them.

### 3. Policy (R-rules)

[`domains/<d>/policy.py`](../../src/health_agent_infra/domains/running/policy.py)
exposes `evaluate_<d>_policy(classified, signals_or_empty,
thresholds=None)` returning a frozen `<Domain>PolicyResult` with:

- `policy_decisions`: a tuple of
  `PolicyDecision(rule_id, decision, note)` rows, one per R-rule
  evaluated (both firing and non-firing decisions are recorded).
- `forced_action`: the v1-enum action the skill MUST honour when set,
  else `None`.
- `forced_action_detail`: structured context the skill copies onto
  the proposal's `action_detail`.
- `capped_confidence`: `"moderate"` when R-sparse-signal fires,
  else `None`.

At minimum implement:

- `require_min_coverage` (R1) — insufficient inputs forces
  `defer_decision_insufficient_signal`.
- `no_high_confidence_on_sparse_signal` (R5) — sparse coverage caps
  confidence to `moderate`.
- at least one domain-specific escalation rule (an RHR-spike
  analogue — recovery has one, running has
  `acwr_spike_escalation`, sleep has chronic-deprivation, stress
  has sustained-high, etc). The rule ID is a stable string; tests,
  eval scenarios, and `hai explain` all reference it.

R-rules are **domain-internal**. Cross-domain behaviour belongs in
synthesis (X-rules), not here. An R-rule that coincidentally
overlaps with an X-rule (e.g. the running R-acwr-spike at ratio ≥ 1.5
and X3b at the same threshold) is fine — both fire, and `hai
explain` surfaces both.

Rule ordering matters. Escalations override coverage-defer because
"louder signal wins"; sparse caps apply independently of action.
Read `running/policy.py :: evaluate_running_policy` as the
reference.

### 4. Registry wiring

Three registries in `core/` drive dispatch. Every one of them must
learn the new domain or the runtime will refuse its proposals:

- [`core/writeback/proposal.py`](../../src/health_agent_infra/core/writeback/proposal.py):
  add the domain to `SUPPORTED_DOMAINS`, add its schema version to
  `PROPOSAL_SCHEMA_VERSIONS`, and add its action enum to
  `DOMAIN_ACTION_ENUMS`. `hai propose --domain <d>` rejects anything
  missing from these three.
- [`core/synthesis.py`](../../src/health_agent_infra/core/synthesis.py):
  add the recommendation schema version to
  `RECOMMENDATION_SCHEMA_BY_DOMAIN`. Synthesis stamps this onto
  drafts at `_mechanical_draft` time.
- [`core/synthesis_policy.py`](../../src/health_agent_infra/core/synthesis_policy.py):
  if the domain has a baseline "hard" action that cross-domain
  rules may soften or block, add an entry to
  `_DOMAIN_ACTION_REGISTRY` with `hard_actions`,
  `downgrade_action`, `escalate_action`. Domains without a hard
  action (sleep, stress, nutrition v1) are absent from this
  registry by design — skip this step for them.

Drift between these three is a common failure mode for a
half-landed domain. The `test_cli_propose*` and `test_synthesis_*`
tests pin them in lockstep; run them early.

### 5. Snapshot wiring

[`core/state/snapshot.py :: build_snapshot`](../../src/health_agent_infra/core/state/snapshot.py)
builds the cross-domain object skills read. A new domain must
appear as a top-level block with the same shape as the existing six:

```python
snapshot["<d>"] = {
    "today":             <accepted-state row or None>,
    "history":           <list of accepted-state rows, lookback window>,
    "missingness":       "<state_model_v1.md §5 token>",
    # When evidence_bundle is supplied:
    "signals":           <derived dict feeding classify>,
    "classified_state":  <classified.to_dict()>,
    "policy_result":     <policy.to_dict()>,
}
```

The `_DOMAIN_TABLES`, `_DOMAIN_DATE_COLUMN`, `_DOMAIN_HAS_USER_ID`,
`_V1_REQUIRED_FIELDS`, and `_USER_REPORTED_DOMAINS` registries at
the top of `snapshot.py` drive the `read_domain` / missingness
machinery. Missing a required-fields entry silently marks every
NULL as partial; double-check it against the new accepted table.

If the domain reads from an accepted table that doesn't exist yet,
add one with a migration (see §7 below) and a projector (§6).

### 6. Projectors and migrations

If the domain introduces a new `accepted_<d>_state_daily` table:

- Add a migration under
  [`core/state/migrations/`](../../src/health_agent_infra/core/state/migrations/).
  Migrations are append-only and numeric-ordered (001…007). Follow
  the idioms in `004_sleep_stress_tables.sql` and
  `005_strength_expansion.sql`.
- Add a projector module under
  [`core/state/projectors/`](../../src/health_agent_infra/core/state/projectors/).
  Model it on
  [`sleep.py`](../../src/health_agent_infra/core/state/projectors/sleep.py)
  (UPSERT, first-write stamps `projected_at`, rewrite stamps
  `corrected_at`, `commit_after=False` for composition inside an
  outer transaction).
- Re-export it from
  [`projectors/__init__.py`](../../src/health_agent_infra/core/state/projectors/__init__.py)
  and from the top-level
  [`core/state/projector.py`](../../src/health_agent_infra/core/state/projector.py)
  re-export list.
- Update `state_model_v1.md` with the new table's column set,
  `derivation_path`, and any new `source` / `ingest_actor` values.

If the domain reuses an existing accepted table (rare — most new
domains want their own), skip this step entirely.

### 7. Skill

[`skills/<d>-readiness/SKILL.md`](../../src/health_agent_infra/skills/running-readiness/SKILL.md)
is the judgment layer. Its job is tightly bounded:

1. Read `snapshot.<d>.classified_state` and
   `snapshot.<d>.policy_result`. Both are source-of-truth.
2. If `policy_result.forced_action` is set, use it verbatim. Skip
   the action matrix.
3. Otherwise pick an action from the domain enum based on a small
   action matrix keyed on band composites. The matrix is documented
   in prose in the skill, not computed — the bands already encode
   the numeric work.
4. Compose 3–6 lines of rationale naming the bands that drove the
   decision. Do not recompute arithmetic.
5. Populate `uncertainty` from `classified.uncertainty` plus any
   skill-level tokens (e.g. vendor-disagreement flags). Sort and
   dedupe.
6. Copy `policy_result.policy_decisions` onto the output verbatim.
7. Emit a `<Domain>Proposal` JSON and call `hai propose --domain
   <d> --proposal-json <path>`.

Hard constraints:

- The skill stays under ~100 lines. If it grows past that,
  deterministic work is leaking in; move it to `classify.py` or
  `signals.py`.
- The skill never mutates `forced_action` or raises confidence above
  `capped_confidence`. `safety/tests/test_<d>_skill_gates.py`
  verifies this contract.
- The skill may lower confidence below the cap (vendor-disagreement,
  missingness the classifier missed) but never raise it.

### 8. Synthesis touchpoints (required if the domain has hard
   actions or co-owns a cross-domain signal)

Cross-domain behaviour lives in
[`core/synthesis_policy.py`](../../src/health_agent_infra/core/synthesis_policy.py).
For a new domain, consider two questions:

1. **Does a hard session in this domain consume the same recovery
   reserve as recovery / running / strength?** If yes, the existing
   X-rules (X1a/X1b sleep debt, X6 body-battery, X7 sustained-stress)
   likely need to include the new domain. Extend the affected
   rules' `for domain in targets` loops and add a scenario under
   [`src/health_agent_infra/evals/scenarios/synthesis/`](../../src/health_agent_infra/evals/scenarios/synthesis/).
2. **Does this domain produce a cross-domain signal that should
   soften another domain?** If yes, add a new X-rule following the
   X1a pattern. Register it in the catalogue
   ([`x_rules.md`](x_rules.md)) and add a
   `test_synthesis_scenarios_cover_key_x_rules` floor entry.

A domain that is purely self-contained (e.g. a pure
tracking/observability domain) touches neither path; leave synthesis
alone. Nutrition is the escape hatch case — it participates in
Phase A (X2 softens hard training on large deficits) and Phase B (X9
adjusts its own action_detail based on finalised training).

### 9. Intake (optional)

If the domain is **user-reported** (not projected from a passive
source), add an intake surface:

- [`domains/<d>/intake.py`](../../src/health_agent_infra/domains/nutrition/intake.py)
  for the parse/validate helpers.
- A new `hai intake <d> …` subcommand in
  [`cli.py`](../../src/health_agent_infra/cli.py).
- A raw table (`<d>_submission`, `<d>_manual_raw`, …) and a
  projector from raw → accepted.
- An entry in `_USER_REPORTED_DOMAINS` in `snapshot.py` so
  missingness routes to `pending_user_input` pre-cutover instead of
  `partial`.

Passive-source domains (recovery, running, sleep) skip this step.

### 10. Signals helper (optional)

Some domains pre-compute derived signals before calling `classify`.
[`signals.py`](../../src/health_agent_infra/domains/running/signals.py)
is where that lives — e.g. `derive_running_signals` assembles
weekly mileage, baseline, acwr, recovery-adjacent tokens. Create one
if `build_snapshot` would otherwise inline too much derivation.

Keep it pure (no DB access, plain dicts in and out). The snapshot
bundler calls it during bundle expansion; the classifier reads only
its output.

## State shape expectations (required)

Two invariants every domain must honour in its accepted-state
shape:

- **Every `accepted_<d>_state_daily` row carries the full metadata
  column set**: `as_of_date`, `user_id`, `derived_from` (JSON list
  of source row ids), `source`, `ingest_actor`, `projected_at`,
  `corrected_at`, `derivation_path`. See `state_model_v1.md` §4 for
  exact semantics.
- **First insert stamps `projected_at`; any rewrite stamps
  `corrected_at`**. This is the "hybrid correction grammar" —
  tests like
  [`test_state_dual_write.py`](../../safety/tests/test_state_dual_write.py)
  pin it.

`_V1_REQUIRED_FIELDS[<d>]` in `snapshot.py` must name the fields
that a fully-populated day carries. NULLs on non-required fields do
not count toward `partial:<fields>` — they're enrichments, not
missing data. Getting this set right is how the snapshot's
missingness tokens stay honest.

## Synthesis touchpoints (summary)

The synthesis layer never invents behaviour for a new domain — it
reads the registries above. Wiring a new domain means, at minimum:

- `RECOMMENDATION_SCHEMA_BY_DOMAIN` has the right schema version
  (synthesis stamps it onto drafts at `_mechanical_draft`).
- `_DOMAIN_ACTION_REGISTRY` knows the domain's hard/downgrade/escalate
  triple if X-rules should be able to soften or block its proposals.
- `PHASE_B_TARGETS` knows the domain if a new Phase B rule mutates
  its `action_detail`.

The Phase B write-surface guard
([`guard_phase_b_mutation`](../../src/health_agent_infra/core/synthesis_policy.py))
rejects any firing that tries to touch `action` or a non-target
domain. If a new X-rule needs to change more than `action_detail`
on a Phase B target, that's a design conversation — not a domain
change.

## Test expectations (required)

Ship these test files with the domain:

- `safety/tests/test_<d>_schemas.py` — proposal shape == field set,
  action enum membership, `bounded=True` invariants, rejection of
  `follow_up` / `daily_plan_id` / `recommendation_id` on proposals.
- `safety/tests/test_<d>_classify.py` — one test per band boundary
  per signal (the recovery/running tests are the reference — aim
  for that density).
- `safety/tests/test_<d>_policy.py` — one firing + one non-firing
  test per R-rule. Verify `forced_action`, `capped_confidence`,
  `policy_decisions` contents.
- `safety/tests/test_<d>_skill_gates.py` — the skill-boundary
  contract: skill never raises confidence, never mutates
  forced_action, always copies policy_decisions verbatim. Mirrors
  `test_running_skill_gates.py`.
- `safety/tests/test_cli_propose.py` — add the domain to the
  existing parametrized coverage so `hai propose --domain <d>`
  accept/reject paths are pinned.

And eval scenarios:

- `src/health_agent_infra/evals/scenarios/<d>/*.json` — at least three: a baseline
  "happy path," an R-rule firing case, and a coverage-gap case.
  [`safety/tests/test_eval_scenarios.py`](../../safety/tests/test_eval_scenarios.py)
  parametrizes over `SUPPORTED_DOMAINS`, so the new domain is picked
  up automatically once its scenarios exist.

If the domain added an X-rule or extended an existing one, also add
a `src/health_agent_infra/evals/scenarios/synthesis/<name>.json` scenario and an
entry in `test_synthesis_scenarios_cover_key_x_rules`.

## What not to change casually

These boundaries exist for a reason. A new domain should not force
changes to any of them; if it seems to, pause and re-scope.

- **The code-vs-skill boundary.** Skills compose rationale; code
  does arithmetic. A skill that computes a band, a score, or a
  threshold comparison has regressed into code's territory — move
  the logic into `classify.py` or `signals.py`. See
  [`architecture.md`](architecture.md) §"Code-vs-skill boundary."
- **`core/schemas.py :: BoundedRecommendation` / `DomainProposal`
  base shapes.** These are the write-surface contracts; every
  domain's schemas must *match* them, not *mutate* them.
- **`hai synthesize` is the only write path for recommendations.**
  All six domains land in `recommendation_log` atomically inside the
  synthesis transaction. (The legacy recovery-only `hai writeback`
  direct path was removed in v0.1.4 D2.) Don't add per-domain
  writeback entry points.
- **Phase B write-surface guard.** `guard_phase_b_mutation` is the
  reason Phase B rules can't silently mutate `action`. Don't widen
  the guard — add a new Phase A rule instead.
- **The synthesis transaction.** `run_synthesis` commits `daily_plan
  + x_rule_firing + recommendation_log` rows atomically; a failure
  rolls back everything. Don't inject per-domain writes outside that
  transaction.
- **`hai daily` and `hai synthesize` orchestration.** These are
  stable in the post-v0.1.x shape; locked decision 3.1.6 in the
  roadmap pins them. A new domain participates through the
  registries — it does not change orchestration.
- **Adaptive / learning-from-outcomes behaviour.** Explicitly out of
  scope for this cycle (roadmap §2.3, decision 3.1.4). A new
  domain's policy is static config-driven thresholds, not a learned
  function of review outcomes.

## Required extension points vs optional refinement points

Required (no domain ships without these):

- `schemas.py`, `classify.py`, `policy.py`
- entries in `SUPPORTED_DOMAINS`, `PROPOSAL_SCHEMA_VERSIONS`,
  `DOMAIN_ACTION_ENUMS`, `RECOMMENDATION_SCHEMA_BY_DOMAIN`
- a new block in `build_snapshot`
- a `<d>-readiness` skill under 100 lines
- test files for schemas / classify / policy / skill gates and a CLI
  propose test
- at least three eval scenarios
- `state_model_v1.md` updated with any new table

Optional (ship only if the domain actually needs them):

- `signals.py` — if derivation is non-trivial and cluttering the
  snapshot bundler
- `intake.py` + `hai intake <d>` — if the domain is user-reported
- a new `accepted_<d>_state_daily` table + migration + projector —
  if no existing accepted table fits
- `_DOMAIN_ACTION_REGISTRY` entry — only if the domain has a hard
  action cross-domain rules should soften or block
- a new X-rule — only if the domain produces a cross-domain signal
  worth acting on

## Definition of done

A new domain is ready to land when all of the following are true:

1. `domains/<d>/{schemas,classify,policy}.py` exist and follow the
   shape of the existing six domains.
2. `<d>-readiness/SKILL.md` is under ~100 lines and never
   recomputes what classify/policy already produced.
3. The three registries (proposal / synthesis / synthesis_policy)
   all know the domain, and `hai propose --domain <d>` validates a
   correct payload end-to-end on a fresh DB.
4. `hai state snapshot` returns a `<d>` block with today / history /
   missingness / (when an evidence bundle is supplied) signals /
   classified_state / policy_result.
5. `hai synthesize` commits per-domain recommendations atomically
   alongside the daily plan.
6. `hai eval run --domain <d>` runs the three or more committed
   scenarios cleanly.
7. Tests cover schemas, classify bands, policy rules, skill gates,
   and the CLI propose path.
8. `state_model_v1.md` reflects any new table; `architecture.md`'s
   pipeline ASCII is updated if the domain added a new accepted
   table; `x_rules.md` reflects any new or extended X-rule.
9. No runtime change was needed to `BoundedRecommendation` /
   `DomainProposal` base shapes, the synthesis transaction boundary,
   or the code-vs-skill boundary.
10. `reporting/docs/domains/README.md`'s domain list still matches
    the shipping set — update it with the new domain and its
    short description.
