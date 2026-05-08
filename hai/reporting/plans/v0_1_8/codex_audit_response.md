# Codex Audit - v0.1.8 Plan Response

## Step 0 confirmation

- `pwd`: `/Users/domcolligan/health_agent_infra`
- `git branch --show-current`: `v0.1.4-release`
- `git log --oneline -1`: `ff77aff v0.1.5: sync release QA + handoff docs to v0.1.5 reality`
- `reporting/plans/v0_1_8/` exists and contains `REPORT.md`, `PLAN.md`, and `codex_audit_prompt.md`.
- Working tree is dirty with v0.1.7/v0.1.8 implementation artifacts. I treated those as in-flight maintainer work and did not edit runtime code.

## Executive verdict

The north star is correct: this should become a governed local runtime infrastructure layer for personal health agents, not just a better daily recommendation script. The README already frames the project as "a governed local agent runtime for personal health data" with local SQLite persistence and no off-device state (`README.md:3`, `README.md:6-9`), and the positioning doc anchors the same idea as a governed local runtime with deterministic tools, typed contracts, and auditable persisted state (`reporting/docs/personal_health_agent_positioning.md:13-18`).

The proposed ledger direction is also correct, but the current v0.1.8 draft is misordered. It jumps from "outcomes exist" to "skills consume outcomes" before the system has enough explicit intent, target, plan, and data-quality state to interpret those outcomes. A negative review outcome means different things depending on what the user intended, what target was active, what recommendation changed, what signal quality was present, and whether the plan was followed. Today the repo has raw evidence, accepted state, decision state, and outcome state (`reporting/docs/state_model_v1.md:24-38`), but it does not yet have first-class intent or target ledgers.

My recommendation: revise v0.1.8 to lead with a code-owned outcome summary plus minimal intent/target ledgers, not direct skill consumption of raw `review_outcome` rows. Keep adaptation non-silent and non-learning. Defer full weekly review, insights, charts, MCP, UI, and new adapters until the next cycles.

Plan verdict: **REVISE BEFORE IMPLEMENTATION**.

## External evidence reviewed

These sources shaped the recommendations below:

- Google Research, [The Anatomy of a Personal Health Agent](https://research.google/pubs/the-anatomy-of-a-personal-health-agent/): supports role separation across data science, domain expert, and coach agents; also emphasizes multi-level evaluation of health agents. HAI should use this as an evaluation and role-separation lens, not copy the multi-agent architecture.
- Kleppmann et al., [Local-first software](https://martin.kleppmann.com/2019/10/23/local-first-at-onward.html): supports the project's local-first stance: data ownership, offline durability, privacy, and user control.
- Nahum-Shani et al., [JITAI design principles](https://academic.oup.com/abm/article-abstract/52/6/446/4733473): decision points, intervention options, tailoring variables, and decision rules map cleanly onto HAI's daily plan, domains, state snapshot, and policy/X-rule layers.
- Michie et al., [BCT Taxonomy v1](https://academic.oup.com/abm/article/46/1/81/4563254): behavior-change systems need precise, inspectable descriptions of active ingredients. HAI should tag recommendations/reviews with behavior-change technique metadata where useful, without turning that into clinical claims.
- FDA, [General Wellness: Policy for Low Risk Devices](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/general-wellness-policy-low-risk-devices): reinforces the boundary between healthy lifestyle support and diagnosis/treatment claims.
- WHO, [Safe and ethical AI for health](https://www.who.int/news/item/16-05-2023-who-calls-for-safe-and-ethical-ai-for-health): reinforces autonomy, transparency, accountability, safety, and rigorous evaluation as health-AI design constraints.
- HL7 FHIR [Observation](https://www.hl7.org/fhir/observation.html), [Goal](https://www.hl7.org/fhir/goal.html), and [CarePlan](https://www.hl7.org/fhir/careplan.html): useful naming and lifecycle references for evidence, goals/targets, planned activities, and performed activities. Do not adopt FHIR as a dependency now; align concepts lightly.
- [Open mHealth schemas](https://github.com/openmhealth/schemas): useful precedent for structured health data schemas, validators, and test data.
- [Open Wearables](https://github.com/the-momentum/open-wearables): comparable open-source project focused on unified wearable ingestion, self-hosting, normalized APIs, and MCP. HAI should not compete by rushing adapters; its stronger position is governed local decision/runtime state.
- [QS Ledger](https://github.com/markwk/qs_ledger): comparable quantified-self project focused on local aggregation, notebooks, analysis, and dashboards. HAI's opportunity is to make this auditable and agent-operable rather than notebook-centric.
- Lee et al., [Accuracy of 11 consumer sleep trackers](https://pmc.ncbi.nlm.nih.gov/articles/PMC10654909/): consumer wearable measures vary materially against polysomnography. This supports explicit missingness, provenance, and data-quality ledgers rather than overconfident inference.
- Konigorski et al., [StudyMe user-centric N-of-1 trials](https://link.springer.com/article/10.1186/s13063-022-06893-7): supports a future governed self-experimentation layer, but only after the project can represent goals, interventions, measures, schedules, and outcomes explicitly.

## Validation of the maintainer's read (Job A)

### Structural gaps A-I

**A. No feedback loop from outcomes - CONFIRMED, but fix the ownership boundary.**

`review_event` and `review_outcome` are first-class outcome-state tables (`reporting/docs/state_model_v1.md:143-150`), and `record_review_outcome` persists followed/improvement booleans plus enrichment fields such as completion, intensity delta, energy scores, and disagreed firings (`src/health_agent_infra/core/review/outcomes.py:110-188`). The non-goals doc says review outcomes do not feed calibration, thresholds, or models yet (`reporting/docs/non_goals.md:31-38`), and the query taxonomy says longitudinal review does not feed thresholds or models (`reporting/docs/query_taxonomy.md:139-141`).

The gap is real. The proposed fix is wrong at the first boundary if skills read raw recent outcomes and compute pattern tokens. Code owns deterministic arithmetic, scoring, signal counting, and schema validation (`reporting/docs/architecture.md:121-146`). Skills own rationale, uncertainty surfacing, and clarifying questions (`reporting/docs/architecture.md:135-142`). Outcome summary tokens should be computed by code, then exposed in the snapshot for skills to narrate.

**B. No multi-day pattern surface - CONFIRMED.**

The shipped longitudinal surface is `hai review schedule / record / summary`, plus direct reads of accepted state history (`reporting/docs/query_taxonomy.md:120-137`). The CLI contract says `hai review summary` summarizes review counts and `hai stats` summarizes sync/runtime telemetry, not multi-day adherence or plan-vs-actual patterns (`reporting/docs/agent_cli_contract.md:90-99`). The gap is real.

**C. No confidence calibration - CONFIRMED, but keep it read-only for now.**

The memory model explicitly forbids feeding `review_outcome` into confidence calibration, thresholds, classifiers, policy, or X-rules (`reporting/docs/memory_model.md:232-266`). That is a correct safety constraint for v0.1.x. v0.1.8 should surface calibration evidence, not alter confidence automatically.

**D. No self-tuning thresholds - PARTIALLY WRONG AS WRITTEN.**

The report claims the runtime ignores user-side threshold overrides (`reporting/plans/v0_1_8/REPORT.md:89-94`) and W39 repeats that claim (`reporting/plans/v0_1_8/PLAN.md:91-106`). That is false on this tree. `core/config.py` says `load_thresholds()` returns default thresholds deep-merged with user TOML (`src/health_agent_infra/core/config.py:1-15`), `user_config_path()` resolves platformdirs config (`src/health_agent_infra/core/config.py:431-438`), and `load_thresholds()` reads the effective path if present (`src/health_agent_infra/core/config.py:460-484`). `hai config show` prints the merged effective thresholds (`src/health_agent_infra/cli.py:3362-3375`), and the generated CLI contract documents `hai config show` as merged defaults plus overrides (`reporting/docs/agent_cli_contract.md:67-68`).

The real gap is not loading. The real gap is authoring, validating, explaining, diffing, and auditing threshold overrides.

**E. No agent-side memory of "what worked" - CONFIRMED, but rename it.**

The explicit memory table stores goals, preferences, constraints, and context (`reporting/docs/memory_model.md:189-226`). Outcome memory records what happened but deliberately does not feed thresholds or policy (`reporting/docs/memory_model.md:163-185`). The missing thing should not be "agent-side memory." It should be a code-owned review summary/insight proposal ledger. "Agent memory" is the wrong vocabulary for this project because the repo explicitly rejects hidden chat memory and opaque profiles (`reporting/docs/personal_health_agent_positioning.md:103-105`).

**F. No multi-day plan surface - CONFIRMED and strategically important.**

Action planning today is daily and proposal-gated (`reporting/docs/query_taxonomy.md:63-88`). The current daily orchestrator plans one date and requires domain proposals before synthesis (`README.md:95-125`). The non-goals doc currently forbids training plan and diet plan generation (`reporting/docs/non_goals.md:86-93`). A future multi-day surface is possible, but the plan must distinguish user-authored intent/targets from agent-authored training or diet plan generation.

**G. No agent self-evaluation - CONFIRMED.**

The skill-harness blocker says live transcript capture remains operator-driven, only recovery is covered, synthesis is unscored, and cross-run stability is not measured (`safety/evals/skill_harness_blocker.md:79-112`). The generated CLI contract includes deterministic `hai eval run`, but that is not the same as live skill behavior scoring (`reporting/docs/agent_cli_contract.md:70-71`).

**H. No data-quality surface - CONFIRMED, and more important than the draft says.**

The runtime already distinguishes `absent`, `partial`, `unavailable_at_source`, and `pending_user_input` missingness (`reporting/docs/state_model_v1.md:152-162`) and tracks source vs ingest actor provenance (`reporting/docs/state_model_v1.md:164-175`). But there is no first-class data-quality ledger or user surface that answers "was this recommendation data-limited?" Consumer-wearable accuracy evidence supports making this explicit rather than burying it inside per-domain uncertainty.

**I. No graceful onboarding - CONFIRMED.**

The README documents a calibration timeline and says steady state is around 90 days (`README.md:206-221`), with cold-start asymmetry for running, strength, and stress only (`README.md:223-228`). That is honest but not ergonomic. v0.1.8 or v0.1.9 should surface cold-start status through `hai stats`, `hai daily --auto`, and weekly review, not force new users to infer it from docs.

### Gaps the report missed

**J. No explicit Intent Ledger.**

The state model has raw evidence, accepted state, decision state, and outcome state (`reporting/docs/state_model_v1.md:24-38`). It does not have durable planned training sessions, target sleep windows, travel constraints, rest days, or user-stated weekly intent. This is the biggest missing piece for moving from reactive advice to planning.

**K. No explicit Target Ledger.**

The repo has `user_memory` goals/preferences/constraints (`reporting/docs/memory_model.md:189-226`) and nutrition accepted-state daily rows (`reporting/docs/state_model_v1.md:87-95`), but it lacks versioned targets with units, bounds, effective dates, review dates, source, reason, and supersession. Hydration/protein/calorie/sleep-window targets belong here, not inside prose memory.

**L. No Insight Proposal Ledger.**

The memory model intentionally forbids adaptive memory (`reporting/docs/memory_model.md:232-266`). That is correct. The next safe step is not adaptation. It is an insight-proposal ledger: code or skills can propose "pattern observed," with evidence windows and caveats; the user can commit or reject it; committed insights remain inspectable.

**M. No Artifact Ledger.**

`hai explain` reconstructs plans from SQLite and fabricates nothing (`reporting/docs/explainability.md:14-31`), but charts/reports/proof bundles are not first-class state. Future SVG/HTML/Markdown/JSON reports should be recorded with input query, source rows/hash, generated_at, tool version, and file path.

**N. No behavior-change vocabulary.**

The project has actions and rationale but no inspectable way to say whether a recommendation is goal setting, action planning, feedback, self-monitoring, problem solving, or a prompt. BCT tagging should be optional metadata in recommendation/review surfaces, not a clinical intervention claim.

**O. No N-of-1/self-experiment protocol layer.**

Future governed adaptation should not start as "late bedtime correlates with poor readiness, so tune threshold." It should start as "propose an experiment," with goal, intervention, measure, schedule, analysis window, and user approval. This belongs after intent/target/review maturity, not in v0.1.8.

### Refined success criteria

The report's refined success criteria are directionally right (`reporting/plans/v0_1_8/REPORT.md:131-145`), but I would rewrite them:

- The runtime should learn from outcomes only in the sense of surfacing deterministic, inspectable summaries and proposals. It must not silently retune thresholds, confidence, classifiers, X-rules, or skills (`reporting/docs/memory_model.md:232-266`).
- The runtime should respect user-specific state through explicit targets, constraints, and threshold overrides. Threshold override loading already exists (`src/health_agent_infra/core/config.py:460-484`); authoring and auditability are the missing parts.
- Multi-day continuity should be a first-class state concept, but v0.1.8 should start with intent/target records and review summaries, not full training or diet plan generation because current non-goals forbid that (`reporting/docs/non_goals.md:86-93`).
- Onboarding should be a runtime surface, not just documentation. Cold-start state already has explicit domain asymmetry (`README.md:223-228`), so it can be made visible in `stats`, `daily --auto`, and weekly review.

### Investment framing

Current framing:

- X: outcome-aware agent
- Y: per-user calibration
- Z: agent regression eval
- W: daily explain, PyPI, changelog

Re-rank:

1. **P0: Distribution and release proof.** v0.1.7 must actually install from PyPI before v0.1.8 claims external usability. v0.1.7 still lists actual PyPI publish as outstanding (`reporting/plans/v0_1_7/PLAN.md:420`).
2. **P0: Outcome summary in code, not skills.** This closes the feedback visibility loop while respecting the code-vs-skill boundary.
3. **P0/P1: Intent and Target Ledger MVP.** Without this, outcome summaries remain weak because the runtime cannot compare intended vs recommended vs performed.
4. **P1: Multi-day stats and baselines.** Useful, but not as foundational as intent/target.
5. **P1: Skill-harness expansion.** Necessary as skill surfaces grow.
6. **P2: `hai daily --explain`, funnel stats, property tests.** Useful and mostly independent.
7. **Cut: changelog per-commit test.** Too process-heavy for v0.1.8.

## Audit of the workstream plan (Job B)

### W37 - `review_outcome` consumption in per-domain skills

Call: **AGREE WITH CHANGES**.

Framing is real: outcomes are persisted and not consumed (`reporting/docs/non_goals.md:31-38`, `reporting/docs/query_taxonomy.md:139-141`). Fix is wrong: W37 asks skills to read recent raw outcomes and add pattern tokens (`reporting/plans/v0_1_8/PLAN.md:52-65`). That makes skills run a deterministic windowed classifier, which belongs to code (`reporting/docs/architecture.md:121-146`).

Revised W37:

- Add a code-owned `review_summary` builder.
- Inputs: `review_event`, `review_outcome`, `recommendation_log`, `daily_plan`, `proposal_log`, `x_rule_firing`.
- Output per domain/window: counts, denominators, pending review rate, followed rate, improvement rate, negative pattern token, positive pattern token, insufficient-denominator token, and source recommendation ids.
- Expose summary under `snapshot.<domain>.review_summary`.
- Skills may mention tokens and uncertainty. Skills must not compute them and must not mutate actions from them.

Acceptance should include fixture windows for no outcomes, insufficient denominator, followed-but-worse, followed-and-better, mixed, and superseded-plan relink.

### W38 - `hai stats --outcomes`

Call: **AGREE WITH CHANGES**.

The surface is needed. Current W38 reports followed rate, improvement rate, intensity deltas, and defer-followed rows (`reporting/plans/v0_1_8/PLAN.md:72-89`). Add denominators and data-quality:

- eligible recommendations
- scheduled reviews
- due reviews
- recorded outcomes
- pending/overdue rate
- relinked outcome count
- missing self-reported improvement count
- by-domain and aggregate views
- JSON stable schema in the capabilities manifest

This should consume the same code-owned review summary as W37 so stats and snapshots cannot diverge.

### W39 - Per-user threshold override loading

Call: **REWRITE**.

The problem statement is wrong because user override loading already exists (`src/health_agent_infra/core/config.py:1-15`, `src/health_agent_infra/core/config.py:460-484`), and `hai config show` already emits effective merged thresholds (`src/health_agent_infra/cli.py:3362-3375`, `reporting/docs/agent_cli_contract.md:67-68`).

Replace W39 with:

- `hai config validate [--path]`: validates TOML structure, known keys, leaf types, and allowed numeric ranges.
- `hai config diff [--path]`: shows defaults vs user overrides.
- `hai config set <dotted-key> <value> --reason <text>`: optional; writes TOML and appends a local config-change audit row or JSONL line.
- `hai config show --resolved` can remain as alias if needed, but do not claim it is new functionality.

Do not ship self-tuning thresholds in v0.1.8. Do not auto-write threshold values from outcomes.

### W40 - `hai stats --baselines`

Call: **AGREE WITH CHANGES**.

Useful and evidence-grounded. It should not imply the user has "different bands" unless the classifier actually computes personal baselines. The README says baseline windows stabilize over 14, 28, 60, and 90 day windows (`README.md:214-221`). W40 should surface current observed baseline values, coverage, missingness, and the exact threshold source used.

Add:

- source path for threshold config
- window coverage numerator/denominator
- missingness state
- source freshness
- "not enough history" reason tokens
- JSON output with domain-keyed rows

### W41 - Skill-harness recovery + strength live capture

Call: **AGREE WITH CHANGES**.

Skill-harness expansion is needed because recovery-only coverage and operator-driven live capture remain open (`safety/evals/skill_harness_blocker.md:79-112`). I would choose **running** as the second domain unless the maintainer has a specific strength-transcript reason. Running better exercises planned-session vocabulary, ACWR, activity-source quality, and the flagship daily planning wedge. Strength is still valuable, but running is higher leverage for user trust.

Acceptance should require replay mode, live transcript capture instructions, stable transcript schema, rubric results, and no live LLM execution in normal CI.

### W42 - Synthesis-skill scoring

Call: **AGREE WITH CHANGES**.

This fills a known gap: synthesis skill is unscored (`safety/evals/skill_harness_blocker.md:99-105`). Add negative tests for invented X-rules, invented bands, omitted Phase A firings, and action mutation in prose. The existing architecture says synthesis skill composes rationale over already-fixed actions, while runtime applies mutations mechanically (`reporting/docs/architecture.md:86-107`).

### W43 - `hai daily --explain` per-stage explainability

Call: **AGREE WITH CHANGES, BUT KEEP IT READ-ONLY WHERE POSSIBLE**.

The need is real, but `hai daily` is a writes-state orchestrator in the CLI contract (`reporting/docs/agent_cli_contract.md:69`), while `hai explain` is the read-only audit surface (`reporting/docs/explainability.md:1-31`, `reporting/docs/agent_cli_contract.md:73`). Avoid creating two competing explainability concepts.

Preferred shape:

- v0.1.8: `hai daily --auto --explain` may add thicker per-stage JSON to the existing run output, with no behavior change.
- v0.1.9: add `hai explain run --runtime-event-id <id>` or equivalent read-only run explanation once `runtime_event_log` is stable enough.

Acceptance must prove plain `hai daily` output is unchanged and `--explain` does not recompute or invent fields.

### W44 - PyPI publish of v0.1.6 + v0.1.7

Call: **AGREE AS P0**.

This is operator-only but release-critical. README install points users to `pipx install health-agent-infra` (`README.md:33-37`), and v0.1.7 still lists actual PyPI publish as outstanding (`reporting/plans/v0_1_7/PLAN.md:420`). Add proof:

- `python -m build`
- `twine check dist/*`
- TestPyPI or real PyPI upload transcript
- fresh `pipx install health-agent-infra==0.1.7`
- `hai capabilities --json`
- `hai init` in a temp home/config/data dir
- `hai doctor --json`

Release automation can wait until the manual release has been proven once.

### W45 - Property-based projector tests

Call: **AGREE, P1 NOT P2 IF NEW LEDGERS LAND**.

State integrity is the project. `state reproject` claims deterministic replay modulo timestamps in the CLI contract (`reporting/docs/agent_cli_contract.md:97`). If v0.1.8 adds intent/target/review summary ledgers, property or deterministic replay tests become more important, not less.

Scope narrowly:

- one raw source fixture
- one correction/supersede fixture
- one late-arriving row fixture
- exclude volatile timestamp columns
- assert stable accepted state and stable linkage ids

### W46 - `hai stats --funnel`

Call: **AGREE, P1**.

v0.1.7 says W21 wrote proposal-gate telemetry and W35 proved manifest-only flow (`reporting/plans/v0_1_7/PLAN.md:413-414`), but the user-facing funnel surface remained outstanding (`reporting/plans/v0_1_7/PLAN.md:420`). This should ship because it proves the agent-operable runtime is observable.

Add next-action schema counts, blocking-action counts, intake-vs-skill-vs-synthesize transitions, and stage latency where available.

### W47 - CHANGELOG per-commit discipline

Call: **CUT**.

The project needs release discipline, but a test that depends on whether the working tree has uncommitted structural changes (`reporting/plans/v0_1_8/PLAN.md:228-239`) is brittle and hostile to active audit/implementation cycles. Keep release-proof and changelog checklist. Do not add a noisy safety test.

### W29 - `cli.py` split

Call: **DEFER AGAIN**.

`cli.py` is large, but v0.1.8 should avoid cosmetic or risky dispatcher refactors while adding new state contracts. The prompt itself scopes out cosmetic refactors (`reporting/plans/v0_1_8/codex_audit_prompt.md:127-131`). Split only when a new command family can move cleanly behind a thin dispatcher without behavior change.

### W30 - Public Python API stability

Call: **DEFER, BUT DEFINE SUPPORTED INTERNAL BOUNDARIES**.

Do not publish a broad public API yet. However, if review summaries, intent, and target ledgers land, define internal module boundaries and test them as if they will become public later.

## Workstreams the plan missed

### W48 - Code-owned review summary builder (P0)

Purpose: replace W37's skill-side raw outcome consumption.

Implementation shape:

- Module: `core/review/summary.py`.
- CLI consumers: `hai stats --outcomes`, future weekly review, snapshot builder.
- Snapshot field: `snapshot.<domain>.review_summary`.
- Stable tokens: `outcome_pattern_recent_negative`, `outcome_pattern_recent_positive`, `outcome_pattern_insufficient_denominator`, `outcome_pattern_mixed`.
- Include exact source ids: recommendation ids, review event ids, outcome ids, relink source ids.

Tests:

- seeded 7-day and 14-day fixtures
- superseded plan relink fixture
- incomplete review fixture
- insufficient denominator fixture
- JSON schema fixture

### W49 - Intent Ledger MVP (P0/P1)

Purpose: let the runtime know what the user intended before judging whether a recommendation helped.

Minimum table:

- `intent_item`
- `intent_id`
- `user_id`
- `domain`
- `scope_type`: `day | week | date_range`
- `scope_start`
- `scope_end`
- `intent_type`: e.g. `training_session`, `sleep_window`, `rest_day`, `travel`, `constraint`
- `status`: `proposed | active | superseded | archived`
- `priority`: `low | normal | high`
- `flexibility`: `fixed | flexible | optional`
- `payload_json`
- `reason`
- `source`
- `ingest_actor`
- `created_at`
- `effective_at`
- `review_after`
- `supersedes_intent_id`
- `superseded_by_intent_id`

Minimum CLI:

- `hai intent training add-session`
- `hai intent training list`
- `hai intent sleep set-window`
- `hai intent list`
- `hai intent archive`

Rules:

- Agent may propose intent rows, but committed active intent must carry explicit source/reason and actor.
- No agent-generated training plan yet. This records user intent and constraints. That keeps faith with current non-goals (`reporting/docs/non_goals.md:86-93`).
- Intent appears in `hai state snapshot`, `hai today`, and `hai explain`.

Tests:

- migration
- add/list/archive
- supersession chain
- snapshot active-at-date semantics
- explain includes active intent
- agent CLI manifest mutation classes

### W50 - Target Ledger MVP (P0/P1)

Purpose: represent hydration, protein, calories, sleep window, weekly training load, and other targets as structured state instead of prose memory.

Minimum table:

- `target`
- `target_id`
- `user_id`
- `domain`
- `target_type`: `hydration_ml`, `protein_g`, `calories_kcal`, `sleep_duration_h`, `sleep_window`, `training_load`, etc.
- `status`: `proposed | active | superseded | archived`
- `value_json`
- `unit`
- `lower_bound`
- `upper_bound`
- `effective_from`
- `effective_to`
- `review_after`
- `reason`
- `source`
- `ingest_actor`
- `created_at`
- `supersedes_target_id`
- `superseded_by_target_id`

Minimum CLI:

- `hai target set`
- `hai target list`
- `hai target archive`
- optional `hai target propose` if the maintainer wants stricter agent/user separation

Rules:

- Targets are not medical prescriptions.
- Every target has a reason, source, effective date, and review date.
- No silent adaptation. Outcome summaries may propose target review; they must not change targets.

Tests:

- active target at date
- archived target excluded by default
- superseded target visible with `--include-archived`
- invalid units refused
- target appears in snapshot and explain

### W51 - Data Quality Ledger (P1)

Purpose: make signal reliability inspectable.

Minimum:

- `data_quality_daily`
- per source/domain/date: freshness, coverage, missingness, source unavailable, user-input pending, suspicious discontinuity, calibration window state
- read-only `hai stats --data-quality [--domain] [--since N]`

Why: the state model already represents missingness and provenance (`reporting/docs/state_model_v1.md:152-175`), but the user needs a surface. Wearable accuracy evidence makes this non-optional if the project wants to avoid overclaiming.

### W52 - Weekly Review MVP (P1, likely v0.1.9 if v0.1.8 is full)

Minimum CLI:

- `hai review weekly --week YYYY-Www --json`
- `hai review weekly --week YYYY-Www --markdown`

Inputs:

- accepted state history
- intent items
- targets
- recommendations
- X-rule firings
- review outcomes
- data quality

Output:

- planned vs completed
- target adherence
- recommendation adherence
- missing data
- repeated blockers
- "not enough evidence" sections

No insight commits in MVP. Weekly review can propose insights, but user approval is separate.

### W53 - Insight Proposal Ledger (P1/P2)

Minimum:

- `insight_proposal`
- `insight`
- evidence window
- evidence source ids
- statement
- caveat
- confidence: `low | moderate | high`
- claim_type: `observation | correlation | hypothesis | experiment_result`
- status: `proposed | committed | rejected | archived`

Rules:

- Default to observation/hypothesis, not causal claims.
- User commits insights explicitly.
- Committed insights can be read by snapshots/skills but cannot mutate policy.

### W54 - Artifact Ledger (P2)

Minimum:

- `artifact`
- artifact id, type, format, path, generated_at, input query, source row ids or source hash, generator version

Use for:

- charts
- weekly reports
- release proof packs
- explainability bundles
- future eval transcripts

### W55 - Standards mapping note (P2)

Do not implement FHIR. Add `reporting/docs/standards_mapping.md` mapping:

- Evidence Ledger -> FHIR Observation / Open mHealth datapoint inspiration
- Target Ledger -> FHIR Goal inspiration
- Plan Ledger -> FHIR CarePlan inspiration
- Review/Outcome -> performed activity / outcome inspiration
- Provenance -> FHIR Provenance inspiration

This improves contributor vocabulary without adding clinical interoperability burden.

### W56 - Recommendation metadata: behavior-change tags (P2)

Add optional metadata to recommendations or review summaries:

- `bct_tags`: e.g. `goal_setting_behavior`, `action_planning`, `feedback_on_behavior`, `self_monitoring`, `problem_solving`, `prompts_cues`

Rules:

- Tags are descriptive metadata, not claims of clinical efficacy.
- Skills may use tags in rationale only if code/schema exposes them.
- Weekly review can aggregate what kinds of support the user actually followed.

### W57 - Scope document update before plan generation (P0 before any plan proposals)

Current non-goals forbid training plan generation and diet plan generation (`reporting/docs/non_goals.md:86-93`). Before the project ships any agent-proposed weekly plan, update non-goals to distinguish:

- still forbidden: autonomous clinical/training/diet prescriptions
- allowed: user-authored intent, user-authored targets, and governed agent proposals requiring explicit user approval
- allowed later: bounded wellness plan suggestions inside fixed enums with audit and supersession

Do this before, not after, adding plan-generation language.

## Workstreams the plan should cut

- Cut W47 as a test. Keep changelog/release proof as checklist.
- Cut W39's "runtime ignores overrides" framing. Replace with config validate/diff/set.
- Do not add full `cli.py` split in v0.1.8.
- Do not add MCP, public SDK, UI, new adapters, or new domains in v0.1.8.
- Do not add hidden adaptation, automatic threshold tuning, or policy changes from outcomes.

## Revised plan (Job C)

### Reconciliation table

| WS | Maintainer call | Codex call | Reason |
|---|---|---|---|
| W37 | Outcome consumption in skills | Agree with changes | Outcome gap real, but code must compute summary tokens; skills narrate only. |
| W38 | `hai stats --outcomes` | Agree with changes | Needed, but share code path with review summary and add denominators. |
| W39 | Per-user threshold loading | Rewrite | Loading already exists; missing authoring/validation/diff/audit. |
| W40 | `hai stats --baselines` | Agree with changes | Add coverage, missingness, threshold source, and cold-start status. |
| W41 | Recovery + strength skill harness | Agree with changes | Use running as second domain unless strength has stronger live-session evidence. |
| W42 | Synthesis skill scoring | Agree with changes | Known unscored skill gap. |
| W43 | `hai daily --explain` | Agree with changes | Add as thicker JSON only; preserve read-only `hai explain` as primary audit surface. |
| W44 | PyPI publish | Agree as P0 | External usability depends on actual install. |
| W45 | Projector property tests | Agree, raise priority if ledgers land | State replay is core credibility. |
| W46 | `hai stats --funnel` | Agree | v0.1.7 telemetry needs user surface. |
| W47 | Changelog per-commit discipline | Cut | Too brittle for active worktree and audit cycles. |
| W48 | New | Add P0 | Code-owned review summary builder. |
| W49 | New | Add P0/P1 | Intent Ledger MVP. |
| W50 | New | Add P0/P1 | Target Ledger MVP. |
| W51 | New | Add P1 | Data Quality Ledger. |
| W52 | New | Add P1/v0.1.9 | Weekly Review MVP. |
| W53 | New | Add P1/P2 | Insight Proposal Ledger. |
| W54 | New | Add P2 | Artifact Ledger. |
| W55 | New | Add P2 | Standards mapping note. |
| W56 | New | Add P2 | Behavior-change tags. |
| W57 | New | Add P0 before plan proposals | Non-goals update for governed planning. |

### Re-sequenced v0.1.8 punch list

1. **W44 - PyPI publish and install proof for v0.1.7.**
2. **W48 - Code-owned review summary builder.**
3. **W38 - `hai stats --outcomes`, backed by W48.**
4. **W49 - Intent Ledger MVP, limited to user-authored intent.**
5. **W50 - Target Ledger MVP, limited to user-authored targets.**
6. **W40 - `hai stats --baselines`, with coverage/missingness/cold-start status.**
7. **W39 rewrite - `hai config validate/diff/set`, no self-tuning.**
8. **W46 - `hai stats --funnel`.**
9. **W43 - `hai daily --auto --explain` thick JSON, no behavior change.**
10. **W41 - skill harness second domain. Prefer running.**
11. **W42 - synthesis skill scoring.**
12. **W45 - deterministic replay/property tests for projectors and any new ledgers.**
13. **W57 - update non-goals if any plan-proposal language enters docs.**
14. Defer W52-W56 unless v0.1.8 is intentionally expanded beyond a normal release.

### If v0.1.8 must stay smaller

If the maintainer wants a tighter release, keep:

1. W44
2. W48
3. W38
4. W49 minimal intent only
5. W50 minimal targets only
6. W46
7. W45 focused replay tests

Then defer baselines/config UX/skill harness/daily explain to v0.1.9. Do not ship outcome-aware skills without W48.

## Multi-release roadmap

### v0.1.8 - Plan-aware feedback visibility

Goal: make the daily loop outcome-aware and minimally intent/target-aware without adaptation.

Ship:

- PyPI release proof
- code-owned review summaries
- stats outcomes/funnel
- intent ledger MVP
- target ledger MVP
- baseline/data-quality visibility
- config validation/diff
- focused replay tests

Do not ship:

- automatic tuning
- plan generation
- MCP
- UI
- new adapters
- new domains

### v0.1.9 - Weekly review and insight proposals

Goal: make the runtime useful beyond one day.

Ship:

- `hai review weekly`
- insight proposal/commit/list/archive
- data-quality ledger if not already shipped
- weekly golden fixtures
- outcome/intent/target linkage in weekly output

### v0.2 - Local reports and visualization artifacts

Goal: make state interpretable without SQL.

Ship:

- artifact ledger
- `hai chart sleep/recovery/training-load/adherence`
- `hai report weekly --html --markdown --json`
- chart specs from persisted state only
- visual/regression fixtures for generated artifacts

### v0.3 - Extension contracts

Goal: let contributors add domains/adapters without corrupting governance.

Ship:

- domain extension template
- adapter conformance tests
- standards mapping doc
- first carefully chosen extension only if the current loop is boringly reliable

The repo already documents how large a new domain is: it touches intake, projection, snapshot, classify, policy, synthesis, writeback, skill, tests, evals, and docs (`reporting/docs/how_to_add_a_domain.md:31-64`). It also already documents the adapter contract and per-field degradation behavior (`reporting/docs/how_to_add_a_pull_adapter.md:30-57`, `reporting/docs/how_to_add_a_pull_adapter.md:88-108`). Use those as gates.

### v0.4 - Runtime portability

Goal: let other agents drive HAI safely.

Ship MCP only after the CLI contract has stabilized. The CLI contract already has mutation classes, idempotency, JSON modes, and agent-safe flags (`reporting/docs/agent_cli_contract.md:23-55`). MCP should wrap those contracts, not replace them.

### v0.5+ - Governed adaptation and N-of-1 experiments

Goal: let the system propose changes from evidence without hidden learning.

Allowed:

- threshold-change proposals
- target-review proposals
- insight-derived experiment proposals
- explicit user approval
- before/after evaluation
- visible confidence calibration reports

Forbidden:

- hidden model training
- silent threshold tuning
- chat-memory adaptation
- diagnostic inference
- unreviewable behavior drift

Best long-term adaptation loop:

`observe -> summarize -> propose insight/experiment/change -> user approves -> commit -> evaluate -> keep or retire`

## Ledger architecture recommendation

The nine-ledger architecture is directionally right, but revise the names and dependencies:

1. **Evidence Ledger**: existing raw evidence/user intake. Keep append-only and provenance-rich (`reporting/docs/state_model_v1.md:53-65`).
2. **Accepted State Ledger**: existing projector-authored state. Keep one canonical row per domain/day with missingness (`reporting/docs/state_model_v1.md:83-101`).
3. **Intent Ledger**: new. User-authored plans/constraints/rest/travel/session intent.
4. **Target Ledger**: new. Versioned targets with source/reason/effective/review dates.
5. **Recommendation Ledger**: existing proposal/planned/daily/X-rule/recommendation chain (`reporting/docs/state_model_v1.md:112-142`).
6. **Plan Ledger**: partially existing `daily_plan`; expand later to week/day plan items only after intent/target are mature.
7. **Review Ledger**: existing outcome state, expanded with review summaries (`reporting/docs/state_model_v1.md:143-150`).
8. **Insight Ledger**: new, but proposal-first and user-approved.
9. **Artifact Ledger**: new, for charts/reports/proof bundles.
10. **Data Quality Ledger**: add explicitly. It should not be hidden inside evidence/state. It is a first-class trust surface.

## Ship verdict criteria

I would vote SHIP on the eventual v0.1.8 implementation only if:

- v0.1.7 is actually installable from PyPI with a recorded fresh-install proof.
- W37 is implemented as code-owned review summary, not raw skill-side outcome arithmetic.
- The W39 false premise is removed from plan/docs, and any config work targets validation/diff/authoring rather than "loading overrides."
- If intent/target ledgers ship, they have migrations, CLI surfaces, snapshot/explain integration, supersession/archive semantics, and tests.
- No outcome, insight, or baseline path silently changes thresholds, classifiers, policy, X-rules, or confidence.
- `hai stats --outcomes` and `hai stats --funnel` share deterministic query code with tests over seeded data.
- Skill-harness additions are replayable in normal CI and live-only behind explicit operator action.
- Non-goals are updated before any docs or commands imply agent-generated training or diet plans.
- Every new mutation surface appears in `hai capabilities --json` with correct mutation class, idempotency, JSON mode, and agent-safe flag.
- Release proof includes test count, skipped tests, command transcripts, generated capabilities manifest status, and known deferrals.

Final verdict: **REVISE_BEFORE_IMPLEMENTATION**. The project is capable of the larger vision, but v0.1.8 should build the ledgers that make planning and review truthful before it asks skills to act more "intelligently" from outcomes.
