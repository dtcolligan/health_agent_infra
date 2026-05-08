# Launch notes — Health Agent Infra v0.1.0

This is the launch artifact for the v1 rebuild. It describes the
runtime as it exists in the shipped `v0.1.0` release on `main`.
Read it alongside [`README.md`](../../README.md),
[`STATUS.md`](../../STATUS.md), and the docs under
[`reporting/docs/`](../docs/).

Anything not described here is not shipped.

## What this is

**Health Agent Infra is a governed runtime for a multi-domain
personal health agent.** It runs locally on a single user's machine,
backs a Claude Code (or equivalent) agent with deterministic Python
tools, and ships markdown skills the agent loads to compose
rationale.

Six domains are first-class in v1:

- recovery
- running
- sleep
- stress
- strength
- nutrition (macros-only — see [non-goals](../docs/non_goals.md))

Each domain owns a typed schema, a deterministic classifier, a
mechanical R-rule policy, and a judgment-only readiness skill. A
synthesis layer reconciles per-domain proposals through a fixed
catalogue of cross-domain X-rules and atomically commits one daily
plan with N per-domain recommendations.

It is not a chatbot, a hosted service, a wearable API, an ML
product, or a clinical surface.

## The thesis

The product is an opinion about where the line between code and
skills should sit:

- **Deterministic logic lives in code.** Band classification,
  scoring, R-rules per domain, X-rule evaluation and mutation,
  schema validation, atomic transactions, taxonomy lookup ranking,
  and projector arithmetic are all Python. Code is the only thing
  that mutates state.
- **Judgment lives in skills.** Skills compose rationale prose for
  an already-fixed action, surface uncertainty the runtime cannot
  resolve, and ask clarifying questions during user narration.
  Skills never change an action and never run arithmetic the
  runtime already ran.
- **The boundary is a typed schema.** Two reject-loudly contracts
  (`hai propose`, `hai synthesize`) validate every payload at the
  seam, plus a legacy recovery-only direct-commit contract
  (`hai writeback`). Non-recovery domains reach
  `recommendation_log` only via `hai synthesize`, which validates
  each `BoundedRecommendation` inside the atomic transaction.
- **Synthesis is auditable.** Every X-rule firing is persisted with
  its tier, its target domain, the inputs it read, and the mutation
  it applied. The whole transaction (daily_plan + firings + N
  recommendations) commits atomically or rolls back.

The architecture diagram lives in
[`reporting/docs/architecture.md`](../docs/architecture.md); the
X-rule catalogue in [`reporting/docs/x_rules.md`](../docs/x_rules.md).

## What is actually shipped

### Runtime surfaces

- **State + migrations.** SQLite store under platformdirs; six
  forward-only migrations (001–006) cover the initial 15 tables, a
  field rename, synthesis scaffolding (`proposal_log`,
  `daily_plan`, `x_rule_firing`), sleep/stress tables, strength
  expansion + `exercise_taxonomy`, and macros-only nutrition.
  `hai state init | migrate | read | snapshot | reproject` cover
  init through idempotent rebuild.
- **Pull / clean / projection.** Garmin CSV adapter ships as the
  default; `hai pull --live` uses `python-garminconnect` against
  credentials in the OS keyring (set via `hai auth garmin`). `hai
  clean` produces `CleanedEvidence + RawSummary`; per-domain
  projectors derive every `accepted_*_state_daily` table.
- **Per-domain debug.** `hai classify` and `hai policy` dump the
  classifier output and R-rule firings for an evidence payload.
- **Agent loop.** `hai propose` validates a `DomainProposal` and
  appends it to `proposal_log`. `hai synthesize` runs Phase A
  X-rules over `(snapshot, proposals)`, invokes the
  `daily-plan-synthesis` skill for rationale overlay, runs Phase B
  X-rules under a write-surface guard, and atomically commits.
- **Writeback + review.** `hai writeback` is the recovery-only
  legacy direct path that validates a `TrainingRecommendation`
  payload and appends to the recovery JSONL audit. For the five
  other domains the canonical commit is inside `hai synthesize`'s
  atomic transaction (see above). `hai review
  schedule | record | summary [--domain <d>]` captures outcomes
  per domain.
- **Six judgment-only skills**, plus `daily-plan-synthesis`,
  `strength-intake`, `merge-human-inputs`, `writeback-protocol`,
  `safety`, `reporting`. Packaged with the wheel; copied to
  `~/.claude/skills/` by `hai setup-skills`.

### Phase 7 ergonomics (this release)

- `hai daily` — one-shot morning orchestration: pull → clean →
  snapshot → proposal-gate → synthesize → schedule reviews. The
  proposal gate is the agent seam: when no proposals exist for the
  day the command exits 0 with `overall_status=awaiting_proposals`
  rather than fabricating proposals. Reruns are idempotent because
  `synthesize` keys on `(for_date, user_id)` and review scheduling
  keys on `review_event_id`.
- `hai init` — first-run wizard. Idempotent and non-interactive:
  scaffolds the thresholds TOML, initialises + migrates the state
  DB, copies skills into the Claude skills directory, and reports
  Garmin credential status (without prompting — `hai auth garmin`
  owns that).
- `hai doctor` — read-only diagnostics. Reports config, schema
  version, credentials, skills install, and package version. Returns
  exit 0 for `ok`/`warn`, exit 2 only for malformed config — so
  agents can chain `hai doctor && hai daily` without false blocks
  before first credential setup.
- `hai --version` — prints the package version.

### Eval harness

The eval framework ships **inside the wheel** at
`src/health_agent_infra/evals/` (runner + CLI + scenarios +
rubrics). 28 frozen-rubric scenarios (18 domain + 10 synthesis)
plus a runner. `hai eval run --domain <d>` and `hai eval run
--synthesis` execute them and work in every install (source or
wheel) from any working directory. All deterministic axes pass at
this checkpoint. The skill-narration axis (`rationale_quality`) is
explicitly marked `skipped_requires_agent_harness` per scenario —
see [Limitations](#limitations-and-open-follow-ups).

### Tests + packaging

- 1247 passing, 0 failing across `safety/tests`.
- `pyproject.toml` declares `health_agent_infra` 0.1.0 with
  `requires-python = ">=3.11"` and dependencies pinned to
  `pandas`, `platformdirs`, `keyring`, `garminconnect`. Skills,
  CSV fixtures, migrations, and the strength taxonomy seed are
  packaged via `package-data`.
- A wheel and sdist are buildable via `python -m build` and live
  under `dist/`.
- CI (`.github/workflows/flagship-proof.yml`) runs the full test
  suite on Python 3.11 and 3.12 plus a build job that produces a
  wheel + sdist and smoke-tests the installed `hai` console script
  on every push and PR.

## Why the architecture is credible

- **Frozen contracts.** Schema validation at two public reject-loud
  points (`hai propose`, `hai synthesize`) plus a legacy recovery-
  only direct path (`hai writeback`) — every failure carries a
  named `invariant` id and exits 2. See `core/writeback/proposal.py`
  and `core/writeback/recommendation.py`. Non-recovery
  `BoundedRecommendation` validation runs inside the
  `hai synthesize` transaction.
- **X-rules as data + tier precedence.** Ten evaluators
  (X1a/b, X2, X3a/b, X4, X5, X6a/b, X7, X9) implemented in
  `core/synthesis_policy.py` with a fixed precedence
  (`block > soften > allow`, `cap_confidence` independent,
  `adjust` Phase B-only). Phase B firings are constrained by a
  write-surface guard that rejects any firing that would change an
  action or touch a non-target domain.
- **Eval coverage as a floor.** Every Phase A rule with a feasible
  scenario plus X9 has at least one synthesis scenario;
  `safety/tests/test_eval_scenarios.py ::
  test_synthesis_scenarios_cover_key_x_rules` enforces that this
  set is always exercised. Domain classifiers and policies are
  scored end-to-end against frozen rubrics.
- **Atomic synthesis persistence.** `daily_plan` row, every
  `x_rule_firing` row, and every `recommendation_log` row commit in
  a single SQLite transaction. A failure anywhere in the chain
  rolls the whole plan back; nothing partial reaches state.
- **Documented non-goals.** Scope discipline is explicit and
  load-bearing — see [`reporting/docs/non_goals.md`](../docs/non_goals.md).

## Out of scope (intentional)

These are deliberate cuts, not unfinished work. Reversing any of
them is a product decision.

- **Macros-only nutrition.** Per the Phase 2.5 retrieval-gate
  outcome (see
  [`reporting/plans/historical/phase_2_5_retrieval_gate.md`](phase_2_5_retrieval_gate.md)),
  v1 ships nutrition as a macros-only domain:
  - No `hai intake meal` command.
  - No `meal_log` raw table.
  - No `food_taxonomy`, no USDA FoodData Central import, no `hai
    food search`.
  - No `nutrition-intake` skill.
  - `accepted_nutrition_state_daily.derivation_path` is exclusively
    `'daily_macros'`.
  - `micronutrient_coverage` always resolves to
    `'unavailable_at_source'`. X-rules dependent on micronutrient
    signals degrade to `unavailable` rather than inferring deficiency
    from absence.
  Meal-level returns to a release plan only after the three
  structural retrieval failure classes flagged in the gate are fixed
  and a re-gate passes strict top-1 ≥ 80%.
- **No ML / learning loop in the runtime.** Review records outcomes
  but the runtime never feeds them back into thresholds, confidence
  calibration, or any model.
- **No clinical claims.** Bands, scores, and escalations support
  training-adjustment judgment. They are not biomarkers, not
  diagnostic, not provider-integrated.
- **No hosted multi-user product.** Everything runs locally against
  a single `user_id`. The schema carries the field but auth, row-
  level isolation, and tenant separation are not in scope.
- **No second wearable in v1.** Garmin only (CSV + live). Apple
  Health / Oura / Whoop / Strava are out of scope; the pull-adapter
  protocol leaves a clean seam to add one but doing so is a product
  decision.
- **No general AI health UI.** Surface is the `hai` CLI plus a
  typed Claude Code conversation. No web app, no mobile, no voice,
  no push notifications.

## Limitations and open follow-ups

Honestly outstanding work past v0.1.0:

- **Skill-narration eval harness still blocked.** The deterministic
  runner does not invoke the synthesis or readiness skills; the
  `rationale_quality` axis is marked
  `skipped_requires_agent_harness` on every synthesis scenario. The
  blockers (live agent runtime, skill-contract serialisation,
  judge rubric, CI secrets) are documented in
  [`safety/evals/skill_harness_blocker.md`](../../safety/evals/skill_harness_blocker.md).
  Until the harness lands, skill quality is governed only by the
  schema + write-surface contracts and by author review.
- **Release completed, but operational follow-ups remain.** `v0.1.0`
  is tagged on GitHub and published to both TestPyPI and PyPI, with
  clean-venv install smoke tests completed. Future release work is
  operational rather than architectural.
- **MCP server wrapper not built.** Phase 7 listed `hai mcp serve`
  as optional. CLI + Claude Code skills surface is sufficient for
  initial release; the MCP wrapper is deferred.
- **X4 / X5 lack dedicated synthesis scenarios.** Both X-rules have
  Phase A evaluators and unit-test coverage but no eval scenario,
  because the scenario authoring layer cannot yet seed a prior-day
  state for sequential-day rules. Tracked as a Phase 7 follow-up
  in [`reporting/docs/x_rules.md`](../docs/x_rules.md).
- **Apple Health adapter, learning loop, goal-aware periodisation,
  food-database refresh cadence, RDA/DRI reference data,
  multi-user.** All deliberately deferred — see §8 of the
  [comprehensive rebuild plan](comprehensive_rebuild_plan.md).

## What "shipped" means here

`v0.1.0` is the source-of-truth checkpoint of the rebuild: the
runtime works end-to-end on a fresh `pip install health-agent-infra`
+ `hai init` + `hai daily` with credentials configured, the test
suite is green, CI builds installable artifacts, and the package is
published on PyPI.
