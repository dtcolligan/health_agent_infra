# v0.1.8 Plan - plan-aware feedback visibility

> **Provenance.** Drafted after v0.1.7 completed and revised after
> Codex audit in `codex_audit_response.md`.
>
> **Status.** Revised and implementation-ready. This replaces the
> pre-audit W37-W47 draft. Do not implement the original W37/W39/W47
> shapes; they were corrected or cut by the audit.

---

## 0. Goals & non-goals

### Goals (v0.1.8)

1. **Make v0.1.7 real for external users.** Publish the already-built
   v0.1.7 package and capture fresh-install proof.
2. **Close the outcome visibility loop without adaptation.** The
   runtime should summarize recent outcomes deterministically and
   expose stable uncertainty tokens. Skills may narrate those tokens;
   they must not compute them or change actions from them.
3. **Add minimal intent and target state.** The next useful jump is not
   "smarter daily prose"; it is structured state for what the user
   intended and what targets were active, so future reviews can compare
   intended vs recommended vs performed vs helped.
4. **Make longitudinal state inspectable.** Add outcomes, funnel, and
   baseline surfaces backed by persisted local state.
5. **Keep evaluation ahead of capability.** Extend the skill harness and
   replay/property tests before richer weekly review or adaptation work.

### Non-goals (v0.1.8)

- No ML, hidden learning, silent threshold tuning, or automatic
  confidence calibration from outcomes.
- No policy/action mutation from outcomes. Outcome-derived tokens are
  visibility only.
- No autonomous training-plan generation or diet-plan generation.
  Intent and target MVPs record user-authored or explicitly confirmed
  state.
- No MCP, public Python API snapshot, UI, new adapters, or new domains.
- No broad `cli.py` split. Move code only where required for the new
  command families.
- No per-meal nutrition. Nutrition remains macros-only.

### Guardrails

- **Code owns deterministic summaries.** Review summary tokens, counts,
  denominators, baseline windows, and data-quality fields are runtime
  logic.
- **Skills own narration.** Skills can surface uncertainty and rationale
  over code-owned facts, but cannot compute bands, thresholds, or
  outcome classifications.
- **Every new durable state has provenance.** New intent/target rows
  must carry source, ingest actor, reason, effective date, and
  supersession/archive semantics.
- **Every new command appears in the capabilities manifest.** Mutation
  class, idempotency, JSON behavior, exit codes, and agent-safety flags
  are part of the release.

### Snapshot schema_version v1 → v2 (additive transition)

W48 + W49 + W50 + W51 add fields to the snapshot bundle:

- `snapshot.<domain>.review_summary` (W48)
- `snapshot.intent` — top-level, active rows at as-of date (W49)
- `snapshot.target` — top-level, active rows at as-of date (W50)
- `snapshot.<domain>.data_quality` (W51)

Bump `snapshot.schema_version` from `"v1"` to `"v2"` in the same
release. Document in `reporting/docs/agent_integration.md` that v1
consumers ignore the new fields gracefully (the additions are
purely additive — no v1 field is removed or changed in shape) but
should bump pinned versions when ready to consume them.

### Fixture-factory precondition (from `MAINTAINER_ANALYSIS.md` § 6.5)

Before W49 + W50 + W51 land, add `safety/tests/_fixtures/` with
helpers like `make_intent_row(...)`, `make_target_row(...)`,
`make_outcome_chain(...)`, `make_data_quality_row(...)`. The
~80–120 new tests across W48–W51 + W38 + W39 + W40 + W43 + W45 +
W46 would otherwise reinvent seeding boilerplate per file. ~1
day investment that saves ~3–5 days across v0.1.8.

---

## 1. Codex audit integration

Codex audit response: `reporting/plans/v0_1_8/codex_audit_response.md`.

Accepted audit decisions:

- **W37 original shape is rejected.** Per-domain skills must not read raw
  `review_outcome` rows and compute pattern tokens. Replace with W48, a
  code-owned review summary builder.
- **W39 original premise is false.** Threshold override loading already
  exists through `load_thresholds()` and `hai config show`; v0.1.8 work
  is validation, diffing, authoring, and auditability.
- **W41 second domain changes from strength-preferred to
  running-preferred.** Running better exercises planned-session
  vocabulary, ACWR, activity-source quality, and the daily-planning wedge.
  Strength remains acceptable only if live-session evidence makes it more
  practical.
- **W43 remains attached to `hai daily --auto` for v0.1.8.** Emit a
  thicker explain block in JSON without changing behavior. Preserve
  `hai explain` as the read-only audit surface; defer `hai explain run`
  until runtime-event explainability is ready.
- **W44 is P0.** CI release automation can wait until one manual PyPI
  release is proven end-to-end.
- **W47 is cut.** Keep release-proof/changelog discipline, but do not add
  a brittle working-tree-sensitive changelog test.
- **W29 and W30 remain deferred.** Do not split `cli.py` or freeze a
  public Python API during this state-contract release.

---

## 2. Workstream catalogue

### W44 - PyPI publish of v0.1.7 (P0)

**Problem.** v0.1.7 is tag-ready, but external install proof is still
operator-only and outstanding.

**Fix.** Operator runs the release flow and captures proof in
`reporting/plans/v0_1_8/RELEASE_PROOF.md`:

- branch, commit, and version
- `python -m build`
- `twine check dist/*`
- `twine upload dist/*` or explicit reason if TestPyPI is used first
- fresh `pipx install health-agent-infra==0.1.7`
- `hai --version`
- `hai capabilities --json`
- `hai init` in isolated temp config/data dirs
- `hai doctor --json`

**Acceptance.** A fresh user can install `health-agent-infra==0.1.7`
and run `hai doctor` successfully. Proof artifact is referenced from
the changelog.

### W48 - Code-owned review summary builder (P0)

**Problem.** Review outcomes are validated and persisted, but the
runtime has no deterministic summary layer. The original W37 would have
made skills compute recent-outcome patterns, which violates the
code-vs-skill boundary.

**Fix.** Add `core/review/summary.py` with a pure query/summarize layer.
It reads:

- `review_event`
- `review_outcome`
- `recommendation_log`
- `daily_plan`
- `proposal_log`
- `x_rule_firing`

It emits per-domain and aggregate windows:

- eligible recommendation count
- scheduled review count
- due review count
- recorded outcome count
- pending and overdue counts
- followed-recommendation rate
- self-reported-improvement rate
- intensity-delta distribution
- relinked outcome count
- missing-improvement count
- source recommendation ids, review event ids, outcome ids
- stable tokens:
  - `outcome_pattern_recent_negative`
  - `outcome_pattern_recent_positive`
  - `outcome_pattern_mixed`
  - `outcome_pattern_insufficient_denominator`

**Maintainer refinement (`MAINTAINER_ANALYSIS.md` § 4.4 / § 6.2):**
the four token thresholds MUST live in `thresholds.toml` under a
new `[policy.review_summary]` block, NOT hardcoded — so users can
tune sensitivity via the standard config overlay. Defaults to
seed in `DEFAULT_THRESHOLDS`:

```toml
[policy.review_summary]
window_days = 7
min_denominator = 3
recent_negative_threshold = 4
recent_positive_threshold = 4
```

Expose the result under `snapshot.<domain>.review_summary` for skills to
read and under shared query helpers for stats/weekly-review callers.

**Acceptance.**

- Seeded 7-day and 14-day fixtures cover positive, negative, mixed,
  insufficient denominator, no outcomes, and pending reviews.
- Superseded-plan/relinked-outcome fixture proves canonical leaf
  resolution is reflected in source ids.
- Snapshot JSON includes `review_summary` without changing actions.
- Per-domain skills can copy/surface summary tokens but do not compute
  them.

### W38 - `hai stats --outcomes` (P0)

**Problem.** Users cannot inspect outcome history without SQL.

**Fix.** Add `hai stats --outcomes [--domain <d>] [--since N] [--json]`
backed by W48 summary code. Output structured JSON by default when
requested and markdown/table text on TTY.

Report:

- counts and denominators from W48
- followed and improvement rates by domain
- intensity-delta distribution
- pending/overdue review rate
- relinked outcome count
- missing-improvement count
- top uncertainty tokens over the window

**Acceptance.**

- Fixture DB with 14 seeded days emits stable JSON.
- Markdown/text output is snapshot-tested.
- `hai capabilities --json` documents flags, output schema, mutation
  class `read-only`, and agent-safe status.

### W49 - Intent Ledger MVP (P0/P1)

**Problem.** The runtime can shape today's recommendation, but it cannot
persist what the user intended across a day or week. That makes outcome
review ambiguous.

**Fix.** Add an `intent_item` table and minimal CLI surfaces.

Minimum table fields:

- `intent_id`
- `user_id`
- `domain`
- `scope_type`: `day | week | date_range`
- `scope_start`
- `scope_end`
- `intent_type`: `training_session | sleep_window | rest_day | travel | constraint | other`
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

Snapshot/explain integration:

- active intent rows at `as_of_date` appear in `hai state snapshot`
- `hai explain` includes active intent for the plan date
- `hai today --format json` includes intent context if present

**Rules.**

- This records user-authored or explicitly confirmed intent. It is not
  autonomous training-plan generation.
- Agent-proposed intent must be clearly marked `source=agent_proposed`
  or equivalent and must not become active without an explicit commit
  path.
- Replacements use archive/supersession, not destructive update.

**Acceptance.**

- Migration creates the table and indexes.
- Add/list/archive/supersede commands have tests.
- Active-at-date snapshot semantics are tested.
- Capability manifest documents all new commands.

**Maintainer refinement (`MAINTAINER_ANALYSIS.md` § 6.3):** in the
same release, every per-domain readiness skill (`recovery-readiness`,
`running-readiness`, `sleep-quality`, `strength-readiness`,
`stress-regulation`, `nutrition-alignment`) MUST extend its
`allowed-tools` frontmatter to include `Bash(hai intent list *)`.
Otherwise skills can't consume intent context the snapshot now
exposes.

### W50 - Target Ledger MVP (P0/P1)

**Problem.** Hydration, protein, calorie, sleep-window, and training-load
targets should not live only in prose memory. They need units, dates,
review semantics, provenance, and supersession.

**Fix.** Add a `target` table and minimal CLI surfaces.

Minimum table fields:

- `target_id`
- `user_id`
- `domain`
- `target_type`: `hydration_ml | protein_g | calories_kcal | sleep_duration_h | sleep_window | training_load | other`
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

Optional if implementation time allows:

- `hai target propose`, if the maintainer wants a strict proposed vs
  committed separation for agent-authored changes.

Snapshot/explain integration:

- active targets at `as_of_date` appear in `hai state snapshot`
- `hai explain` includes target state active for the plan date
- `hai today --format json` includes active targets if present

**Rules.**

- Targets are wellness support, not medical prescriptions.
- Every target has reason, source, effective date, and review date.
- Outcomes may propose target review later; they must not auto-change a
  target in v0.1.8.

**Acceptance.**

- Migration creates table and indexes.
- Active target selection by date is tested.
- Invalid units/types fail with named invariants.
- Archive and supersession chains are inspectable.
- Capability manifest documents all new commands.

**Maintainer refinement (`MAINTAINER_ANALYSIS.md` § 6.3):** in the
same release, every per-domain readiness skill MUST extend its
`allowed-tools` frontmatter to include `Bash(hai target list *)`.
Same reasoning as W49.

### W51 - Data Quality Ledger (P1)

**Problem.** The runtime tracks `missingness` and provenance per
domain (`reporting/docs/state_model_v1.md:152-175`), but there's
no first-class user surface answering "was this recommendation
data-limited?" Consumer-wearable accuracy evidence (Lee et al.,
PMC10654909) supports making this explicit instead of burying it
inside per-domain uncertainty.

This also subsumes the v0.1.7 cold-start visibility gap
(REPORT.md gap I) — first-week users would have a single
data-quality view that turns "green" when calibration is done,
instead of having to read the calibration timeline and infer.

**Fix.** Add `migration 021_data_quality.sql` with table:

```
CREATE TABLE data_quality_daily (
  user_id TEXT NOT NULL,
  as_of_date TEXT NOT NULL,
  domain TEXT NOT NULL,
  source TEXT NOT NULL,
  freshness_hours REAL,
  coverage_band TEXT,              -- full | partial | sparse | insufficient
  missingness TEXT,                -- absent | unavailable_at_source | pending_user_input
  source_unavailable INTEGER NOT NULL DEFAULT 0,
  user_input_pending INTEGER NOT NULL DEFAULT 0,
  suspicious_discontinuity INTEGER NOT NULL DEFAULT 0,
  cold_start_window_state TEXT,    -- in_window | recently_closed | post_cold_start
  computed_at TEXT NOT NULL,
  PRIMARY KEY (user_id, as_of_date, domain, source)
);
```

CLI: `hai stats --data-quality [--domain <d>] [--since N] [--json]`.
Snapshot: `snapshot.<domain>.data_quality`.

**Maintainer refinement (`MAINTAINER_ANALYSIS.md` § 3.3):** the
`cold_start_window_state` column MUST agree with
`reporting/docs/cold_start_policy_matrix.md`. Add
`safety/tests/test_data_quality_cold_start_consistency.py` —
for any day where `snapshot.<domain>.cold_start = True`, the
`data_quality_daily` row for `(user, date, domain, *)` reports
`cold_start_window_state = "in_window"`. Catches silent drift
between the matrix doc and the data-quality projection.

**Acceptance.**

- Migration creates table and PK.
- Per-source / per-domain rows populated by a code-owned projector
  that runs alongside `hai clean`.
- Cold-start consistency test (above) passes for all six domains.
- `hai stats --data-quality` emits structured JSON + markdown
  table.
- Capability manifest entry agent-safe + read-only.

### W55 - Standards mapping note (P2, doc-only)

**Problem.** Contributors lack vocabulary alignment to industry
standards (FHIR, Open mHealth, Open Wearables) and may either
ignore them entirely or accidentally adopt one as a dependency.

**Fix.** Ship `reporting/docs/standards_mapping.md` mapping
HAI's ledger concepts to inspirational external standards
WITHOUT introducing them as dependencies:

- Evidence Ledger → FHIR Observation / Open mHealth datapoint inspiration
- Target Ledger → FHIR Goal inspiration
- Plan Ledger → FHIR CarePlan inspiration
- Review/Outcome → performed activity / outcome inspiration
- Provenance → FHIR Provenance inspiration

Includes explicit "NOT a FHIR dependency" disclaimer + reasoning
(local-first + governed + small-team-maintainable).

**Acceptance.**

- Doc exists and references each ledger.
- A new contributor reading the doc can decide whether to align
  a new field with FHIR vocabulary without thinking they MUST.

### W40 - `hai stats --baselines` (P1)

**Problem.** Users cannot inspect the rolling values and coverage behind
classification bands without reading snapshot JSON or SQL.

**Fix.** Add `hai stats --baselines [--domain <d>] [--since N] [--json]`.

Report:

- HRV mean windows where available
- RHR mean windows where available
- training load 7d and 28d-week-mean windows
- sleep hours 7d mean
- domain-specific baseline values already computed by the runtime
- threshold source path
- threshold value used
- observed value
- resulting band
- coverage numerator/denominator
- missingness state
- cold-start/calibration-window state

**Acceptance.**

- Seeded data tests cover full history, partial history, and missing
  source signals.
- Output distinguishes fixed threshold values from observed baselines.
- JSON shape is stable and documented in capabilities.

### W39 - Config validate/diff/set (P1)

**Problem.** Threshold override loading and `hai config show` already
exist. The missing piece is discoverable authoring, validation, diffing,
and auditability.

**Fix.** Replace the original W39 with:

- `hai config validate [--path <p>]`
- `hai config diff [--path <p>]`
- optional `hai config set <dotted-key> <value> --reason <text>`

Validation rules:

- TOML parse errors surface as `USER_INPUT`
- unknown keys are refused or warned with explicit mode
- scalar leaf types match defaults
- numeric values satisfy local range checks where possible
- list replacement behavior is documented

Audit:

- If `config set` lands, append a local config-change audit row or JSONL
  line containing key, old value, new value, reason, actor, timestamp,
  and config path.

**Acceptance.**

- Tests prove existing user TOML merge still works.
- Tests prove invalid keys/types fail.
- `config diff` shows default vs override vs effective value.
- No outcome path writes threshold values.

### W46 - `hai stats --funnel` user surface (P1)

**Problem.** v0.1.7 persists proposal-gate telemetry, but the user-facing
funnel command did not ship.

**Fix.** Add `hai stats --funnel [--since N] [--json]`.

Report:

- daily run count
- `overall_status` histogram
- missing-domain frequency
- intake-required count
- skill-invocation-required count
- synthesize-ready count
- narrate-ready count
- blocking-action count
- proposal-gate-to-synthesis latency where available

**Acceptance.**

- Seeded `runtime_event_log.context_json` fixture pins JSON shape.
- Markdown/text output is snapshot-tested.
- Capability manifest documents the surface.

### W43 - `hai daily --auto --explain` thick JSON (P1)

**Problem.** During agent-driven daily operation, users and agents need
stage-level explanation without parsing prose or re-running SQL.

**Fix.** Add an explain block to `hai daily --auto --explain`. It must not
change ordinary `hai daily` or ordinary `hai daily --auto` behavior.

Explain block:

- `pull`: source resolution, auth/source reason, freshness
- `clean`: evidence rows/sources merged
- `snapshot`: per-domain classified bands, missingness, review_summary
  tokens when W48 has data
- `gaps`: gap tokens and intake commands
- `proposal_gate`: present/missing domains and proposal ids
- `synthesize`: Phase A/B firings and mutations when synthesis runs

**Acceptance.**

- Fixture proves plain `hai daily` and `hai daily --auto` output are
  unchanged.
- `--auto --explain` JSON contains per-stage blocks.
- Explain block reads already-computed/persisted data; it does not
  recompute, mutate, or fabricate fields.

### W41 - Skill-harness second domain live capture (P1)

**Problem.** The skill harness remains recovery-only, live capture is
operator-driven, synthesis is unscored, and cross-run stability is not
measured.

**Fix.** Extend the existing harness to a second domain. Default choice:
running. Strength may be substituted only if the maintainer records why
it is more practical for available live transcripts.

Rubric:

- schema version matches
- action is in documented enum
- rationale references snapshot bands/firings actually present
- uncertainty tokens are known
- policy-forced decisions are preserved
- no invented threshold or band

**Acceptance.**

- Replay mode runs in normal CI.
- Live transcript capture remains operator-gated.
- New domain scenarios cover at least one clean path, one insufficient
  signal path, one policy-forced path, and one cross-domain coupling path
  where applicable.

### W42 - Synthesis-skill scoring (P1)

**Problem.** The daily-plan-synthesis skill emits overlay rationale but
has no scoring harness.

**Fix.** Add a synthesis-skill rubric over fixture bundles:

- every Phase A firing is cited or intentionally summarized
- no invented X-rule
- no invented band
- no action mutation claimed by prose
- no missing high-severity block/soften explanation

**Acceptance.**

- At least three fixture days: clean, partial, escalated.
- Failures identify the broken rationale line or omitted firing.
- Live mode is optional/operator-gated; replay mode is CI-safe.

### W45 - Deterministic replay/property tests (P1)

**Problem.** State replay is core credibility, and new ledgers increase
the surface where nondeterminism can creep in.

**Fix.** Add narrow replay/property tests:

- projector replay over one valid raw source fixture
- correction/supersede replay fixture
- late-arriving row fixture
- intent active-at-date fixture
- target active-at-date fixture
- review summary fixture

Exclude volatile timestamp columns where documented. Do not generate
arbitrary full JSONL; start with small factories.

**Acceptance.**

- Replaying the same inputs produces identical semantic rows and linkage
  ids.
- Deliberate nondeterminism injection fails the test.

### W57 - Non-goals update for governed planning (conditional P0)

**Problem.** Current non-goals forbid training plan generation and diet
plan generation. If v0.1.8 docs or CLI help imply plan proposals, the
scope line must be updated first.

**Fix.** Update `reporting/docs/non_goals.md` before any plan-generation
language ships:

- still forbidden: autonomous clinical/training/diet prescriptions
- allowed now: user-authored or explicitly confirmed intent and targets
- allowed later: bounded wellness plan suggestions inside fixed enums,
  with audit, user approval, and supersession

**Acceptance.**

- Docs distinguish user-authored intent/targets from autonomous plan
  generation.
- No command help or skill text implies autonomous training or diet plan
  generation.

---

## 3. Deferred or cut

- **W37 original skill-side outcome consumption:** superseded by W48.
- **W47 changelog per-commit test:** cut. Keep release-proof checklist.
- **W29 `cli.py` split:** defer. Do only local module extraction needed
  for new command families.
- **W30 public Python API:** defer. Keep internal modules clean but do not
  promise public API stability.
- **Weekly review / insight / artifact ledgers:** defer to v0.1.9/v0.2
  unless v0.1.8 intentionally expands. Planned follow-ons are W52-W56 in
  `codex_audit_response.md`.
- **Release automation:** defer until after one manual PyPI release is
  proven. Do not block W44 on GitHub Actions automation.

---

## 4. Proposed sequencing

| # | Workstream | Why this order |
|---|---|---|
| 1 | **Fixture-factory precondition** | `safety/tests/_fixtures/` lands first; ~80–120 v0.1.8 tests reuse it. |
| 2 | W57 | Update non-goals to allow user-authored intent/targets BEFORE the W49/W50 surfaces ship (avoids contributor confusion). |
| 3 | W44 | v0.1.7 must be installable before v0.1.8 builds on its release claims. Operator-only; runs in parallel with W48 development. |
| 4 | W48 | Code-owned review summaries are the corrected foundation for outcome visibility. Bumps `snapshot.schema_version` v1 → v2. |
| 5 | W38 | User-facing outcome stats should reuse W48 immediately. |
| 6 | W49 | Intent state makes future outcome interpretation meaningful. Migration 019. |
| 7 | W50 | Target state pairs with intent and unlocks adherence/review surfaces. Migration 020. |
| 8 | W51 | Data-quality ledger surfaces cold-start visibility for new users. Migration 021. |
| 9 | W40 | Baselines become more useful once targets and outcomes are inspectable. |
| 10 | W39 | Config validation/diff is independent and should land before calibration claims. |
| 11 | W46 | Funnel surface closes the v0.1.7 telemetry carry-over. |
| 12 | W43 | Thick daily JSON is easier once W48 fields exist in snapshot/stage output. |
| 13 | W41 | Skill harness expansion can run in parallel after schemas settle. |
| 14 | W42 | Synthesis scoring builds on harness/rubric conventions. |
| 15 | W45 | Replay/property tests should close the release after new ledgers stabilize. |
| 16 | W55 | Standards mapping doc — cheap doc-only addition; bundle with release-prep. |

---

## 5. Acceptance for the v0.1.8 release

The release is shippable when:

- v0.1.7 is on PyPI and a fresh install proof passes (W44).
- Outcome summaries are computed by code and exposed to snapshots/stats
  without skill-side arithmetic (W48).
- `hai stats --outcomes` and `hai stats --funnel` emit stable JSON and
  markdown/text output from seeded fixtures (W38, W46).
- Intent and target MVPs have migrations, CLI surfaces, archive or
  supersession behavior, snapshot integration, explain/today integration,
  capability-manifest entries, and tests (W49, W50).
- Baseline stats distinguish observed baselines, fixed thresholds,
  threshold source, coverage, missingness, and cold-start state (W40).
- Config validation/diff/set work does not claim threshold loading is new
  and does not allow outcomes to write thresholds (W39).
- `hai daily --auto --explain` is additive only; ordinary daily outputs
  are unchanged (W43).
- Skill-harness replay covers recovery plus one second domain, preferably
  running; synthesis-skill scoring has fixtures and failure localization
  (W41, W42).
- Replay/property tests cover projector, correction, late-arrival,
  intent, target, and review-summary semantics (W45).
- No v0.1.8 path silently changes thresholds, classifiers, policy,
  X-rules, confidence, intent, or targets based on outcomes.
- All P0/P1 workstreams have regression tests, docs or capability
  manifest updates where applicable, and release-proof entries.
- W51 cold-start consistency test
  (`safety/tests/test_data_quality_cold_start_consistency.py`) is
  green: every `cold_start=True` snapshot block matches the
  `data_quality_daily.cold_start_window_state="in_window"` row.
- `snapshot.schema_version` is `"v2"` post-release; `agent_integration.md`
  documents the additive transition.
- W55 standards mapping doc exists.

---

## 6. Implementation log

(Append as work lands.)

- 2026-04-25 - plan + report - `reporting/plans/v0_1_8/{REPORT.md, PLAN.md, codex_audit_prompt.md}` - authored at close of v0.1.7 cycle.
- 2026-04-25 - Codex audit - `reporting/plans/v0_1_8/codex_audit_response.md` - audit rejects original W37/W39/W47 shapes, adds W48-W57, and votes REVISE_BEFORE_IMPLEMENTATION.
- 2026-04-25 - plan revision - `reporting/plans/v0_1_8/PLAN.md` - integrates Codex audit into an implementation-ready v0.1.8 punch list.
- 2026-04-25 - maintainer analysis - `reporting/plans/v0_1_8/MAINTAINER_ANALYSIS.md` - independent verification of Codex's W39 + W37 + W48 corrections against the codebase; spot-check of external sources (Google PHA paper resolves); architectural points beyond Codex (snapshot v2 transition, migration staging, fixture-factory scaling, token-threshold defaults, intent+target as outcome-interpretation precondition); risk register. Folds 6 refinements into PLAN.md (snapshot v2 + fixture factories + W48 thresholds block + W49/W50 skill `allowed-tools` updates + W51 cold-start consistency + W55 standards-mapping doc + W51/W55 added to sequencing).
- 2026-04-25 - sequencing item #1 (fixture-factory precondition) - `safety/tests/_fixtures/{__init__.py, builders.py, seeders.py}` + `safety/tests/test_fixture_factory.py` - pure dict builders for `intent_item` / `target` / `data_quality_daily` / outcome chain, plus a SQLite `seed_outcome_chain` helper for the already-landed review tables. 11 smoke tests pin shape + override + round-trip contracts. Suite: 1943 → 1954 passed; drift validator OK.
- 2026-04-25 - sequencing item #2 (W57 non-goals update) - `reporting/docs/non_goals.md` + `src/health_agent_infra/cli.py:5783` - non-goals doc now distinguishes autonomous prescriptions (still forbidden) from user-authored intent/targets (W49/W50, now allowed) plus future bounded wellness plan suggestions (post-v0.1.8, governance pending). `hai daily --user-id` help reworded so no CLI text implies autonomous plan generation. Skill audit clean (`safety/SKILL.md` already aligned). Suite: 1954 passed; drift validator OK.
- 2026-04-25 - sequencing item #3 (W44 PyPI publish) - already complete per v0.1.7 RELEASE_PROOF.md; no action needed in v0.1.8 implementation cycle.
- 2026-04-25 - sequencing item #4 (W48 code-owned review summary) - `src/health_agent_infra/core/review/summary.py` (new module, ~360 LOC) + `core/review/__init__.py` re-exports + `[policy.review_summary]` block added to `DEFAULT_THRESHOLDS` (`core/config.py:362`) + `core/state/snapshot.py:build_snapshot` attaches `review_summary` to all six per-domain blocks + bumped `snapshot.schema_version` `v1` → `v2`. 13 new tests in `safety/tests/test_review_summary.py` cover empty DB, all four token rules, 7d/14d window scoping, per-domain isolation, aggregate roll-up, re-link count, threshold overrides, intensity-delta distribution, snapshot integration. 12 existing snapshot tests updated for the additive v2 keys. Suite: 1954 → 1967 passed; drift validator OK.
- 2026-04-25 - sequencing item #5 (W38 `hai stats --outcomes`) - `src/health_agent_infra/cli.py` adds `--outcomes`, `--domain`, `--since` flags to `p_stats` + `_emit_outcomes_stats` + `_render_outcomes_text` helpers. Markdown table on TTY, structured JSON via `--json`. Capability manifest entry updated and `reporting/docs/agent_cli_contract.md` regenerated. 6 new tests in `safety/tests/test_cli_stats_outcomes.py`. Suite: 1967 → 1973 passed; drift validator OK.
- 2026-04-25 - sequencing item #6 (W49 intent ledger MVP) - migration `019_intent_item.sql` (new table with 17 columns, 3 indexes, CHECK constraints on status/scope_type/intent_type/priority/flexibility) + `src/health_agent_infra/core/intent/{__init__.py, store.py}` (CRUD layer with archive/supersede discipline) + `cli.py` adds `hai intent {training add-session, training list, sleep set-window, list, archive}` subparsers. Snapshot: new top-level `snapshot.intent` block via `list_active_intent`. All 6 per-domain readiness skills' `allowed-tools` extended with `Bash(hai intent list *)`. 13 new tests in `safety/tests/test_intent_ledger.py`. Migration count tests bumped 18→19 across `test_state_store.py` + `test_migration_backfill_013_014.py`. Suite: 1973 → 1986 passed; drift validator OK.
- 2026-04-25 - sequencing item #7 (W50 target ledger MVP) - migration `020_target.sql` (new table with 17 columns, 3 indexes, CHECK constraints on status/target_type) + `src/health_agent_infra/core/target/{__init__.py, store.py}` (CRUD layer mirroring W49's archive/supersede shape) + `cli.py` adds `hai target {set, list, archive}` subparsers. Snapshot: new top-level `snapshot.target` block via `list_active_target`. All 6 per-domain readiness skills' `allowed-tools` extended with `Bash(hai target list *)`. 13 new tests in `safety/tests/test_target_ledger.py`. Migration count tests bumped 19→20. Suite: 1986 → 1999 passed; drift validator OK.
- 2026-04-25 - sequencing item #8 (W51 data-quality ledger) - migration `021_data_quality.sql` (new table per (user, date, domain, source) PK) + `src/health_agent_infra/core/data_quality/{__init__.py, projector.py}` (snapshot-driven projection, idempotent INSERT OR REPLACE) + `cli.py` adds `--data-quality` flag to `hai stats` with lazy-projection of today. Snapshot: every per-domain block now carries an in-memory `data_quality` block. 7 new tests including `safety/tests/test_data_quality_cold_start_consistency.py` (the W51 maintainer-required matrix consistency test). Snapshot key-set tests updated to expect `data_quality` alongside `review_summary`. Migration count tests bumped 20→21. Suite: 1999 → 2006 passed; drift validator OK.
- 2026-04-25 - sequencing item #9 (W40 `hai stats --baselines`) - `cli.py` adds `--baselines` flag + `_emit_baselines_stats` + `_render_baselines_text`. Reads snapshot + `load_thresholds()` + `user_config_path()`. Per-domain JSON or markdown view. 3 new tests in `safety/tests/test_cli_stats_baselines.py`. Suite: 2006 → 2009 passed; drift validator OK.
- 2026-04-25 - sequencing item #10 (W39 config validate/diff) - `cli.py` adds `cmd_config_validate` + `cmd_config_diff` + `_walk_keys` / `_lookup` helpers. `hai config validate` reports `toml_parse_error` / `unknown_key` / `type_mismatch` issues; `--strict` makes unknown keys blocking. `hai config diff` shows default-vs-override-vs-effective per leaf. No `hai config set` — outcomes never write thresholds in v0.1.8. 7 new tests in `safety/tests/test_cli_config_validate_diff.py`. Suite: 2009 → 2016 passed; drift validator OK.
- 2026-04-25 - sequencing item #11 (W46 `hai stats --funnel`) - `cli.py` adds `--funnel` flag + `_emit_funnel_stats` + `_render_funnel_text`. Reads `runtime_event_log.context_json` for `command='daily'` rows in the window; aggregates daily run count, overall_status histogram, missing-domain frequency, blocking-action count. 2 new tests in `safety/tests/test_cli_stats_funnel.py`. Suite: 2016 → 2018 passed; drift validator OK.
- 2026-04-25 - sequencing item #12 (W43 `hai daily --auto --explain`) - `cli.py` adds `--explain` flag to `hai daily` + `_build_daily_explain_block` helper. When both `--auto` and `--explain` are set, the report dict gains an `explain` block with `schema_version="daily_explain.v1"` containing per-stage projections (pull/clean/snapshot/gaps/proposal_gate/synthesize). 3 new tests in `safety/tests/test_cli_daily_auto_explain.py` pin (a) plain daily unchanged, (b) auto-without-explain unchanged, (c) auto+explain attaches the block. Suite: 2018 → 2021 passed; drift validator OK.
- 2026-04-25 - sequencing item #13 (W41 skill harness 2nd domain = running) - `safety/evals/skill_harness/runner.py` extended: `SUPPORTED_DOMAINS = ("recovery", "running")`, new `_running_snapshot_block` calling real `derive_running_signals`/`classify_running_state`/`evaluate_running_policy`, dispatch in `compose_snapshot`. New scenarios: `run_h01_ready_baseline`, `run_h02_insufficient_defers`, `run_h03_acwr_spike_escalates`, `run_h04_recovery_coupling_holds`. New rubric doc `rubrics/running.md`. 4 new tests in `safety/tests/test_skill_harness.py` cover doc presence, expected-block sanity, classifier integration, and the W41 4-path coverage requirement. Suite: 2021 → 2025 passed; drift validator OK.
- 2026-04-25 - sequencing item #14 (W42 synthesis-skill scoring) - new `safety/evals/synthesis_harness/{__init__.py, runner.py, rubrics/synthesis.md}` + 3 fixture scenarios (`syn_d01_clean`, `syn_d02_partial_x1a`, `syn_d03_escalated_x3b`). Scorer enforces four rubric invariants: all firings cited, no invented X-rule, no invented band, no action mutation by prose. 7 new tests in `safety/tests/test_synthesis_harness.py` cover the rubric doc, three-scenario coverage, passing-output for clean and escalated, and one failure mode per axis. Suite: 2025 → 2032 passed; drift validator OK.
- 2026-04-25 - sequencing item #15 (W45 deterministic replay/property tests) - new `safety/tests/property/test_v0_1_8_replay_properties.py` covers intent supersession-chain replay, late-arriving target does not change past snapshot, intent + target active-at-date stability, review-summary replay equality across DBs, review-summary call-order stability. 6 new tests. Suite: 2032 → 2038 passed; drift validator OK.
- 2026-04-25 - sequencing item #16 (W55 standards mapping doc) - new `reporting/docs/standards_mapping.md` mapping every HAI ledger to FHIR + Open mHealth + Open Wearables analogues with explicit "NOT a FHIR dependency" disclaimer. Doc-only addition; no test surface change. Suite: 2038 passed; drift validator OK.
- 2026-04-25 - release prep - `pyproject.toml` bumped 0.1.7 → 0.1.8; `CHANGELOG.md` `[Unreleased]` block promoted to `[0.1.8] — 2026-04-25` with theme summary; `reporting/plans/v0_1_8/RELEASE_PROOF.md` written from the v0.1.7 template (pre-upload — operator captures `twine upload` output post-release). `pip3 install --force-reinstall --no-deps .` + `pipx install --force` confirmed `hai 0.1.8`. `agent_cli_contract.md` regenerated under v0.1.8. Final: 2038 passed, 4 skipped, drift OK.
- 2026-04-25 - Codex round-1 audit (`codex_implementation_review_response.md`) - REVISE_BEFORE_SHIP, two P1 must-fix governance violations (P1-1: `hai stats --data-quality` writes state; P1-2: agent-proposed rows can land active), three P2 should-fix items (P2-1: `--auto --explain` snapshot block thin; P2-2: live capture wired to recovery skill always; P2-3: config validate skips range checks), one P3 doc miss (P3-1: snapshot v2 transition undocumented).
- 2026-04-25 - Codex round-1 maintainer response (`codex_implementation_review_response_round2.md`) - all 6 findings accepted and shipped same-cycle. P1-1: lazy-write removed from stats; data-quality projection wired into `hai clean`. P1-2: store + CLI defence-in-depth on agent-proposed-active rejection; new `hai intent commit` + `hai target commit` user-gated promotion commands marked `agent_safe=False`. P2-1: snapshot stage enriched with W48 tokens / bands / missingness. P2-2: `_LIVE_SKILL_BY_DOMAIN` dispatch table. P2-3: `range_violation` issue kind for `[policy.review_summary]` bounds. P3-1: "Snapshot schema v2" section added to `agent_integration.md`. 20 new regression tests (8 intent / 4 target / 2 data-quality / 4 config-validate / 2 skill-harness). Suite: 2038 → 2058 passed; drift validator OK; contract regenerated.
- 2026-04-26 - Codex round-2 audit (`codex_implementation_review_round2_response.md`) - SHIP_WITH_FIXES. Round-1 P1 blockers confirmed closed; three NEW_ISSUE_FROM_FIX residuals + one nit: R2-1 (`hai clean` silently swallows dq projection failures), R2-2 (agent-proposed supersede deactivates old active before user commit), R2-3 (config validator accepts bools as numbers because `bool` is a subclass of `int` in Python), R2-4 (stale `_emit_data_quality_stats` docstring).
- 2026-04-26 - Codex round-2 maintainer response (`codex_implementation_review_response_round3.md`) - all 4 findings accepted and shipped same-cycle. R2-1: stderr warning replaces bare `except: pass`. R2-2: defence-in-depth — `supersede_*` defers agent-proposed deactivation; `commit_*` performs atomic deactivate-on-promotion. W57 invariant now enforced at insert + supersede + commit boundaries. R2-3: `_is_real_number` helper excludes bools from numeric checks. R2-4: docstring rewritten. 8 new regression tests (5 supersede behaviour, 3 bool-as-number rejection). Suite: 2058 → 2066 passed; drift validator OK; contract regenerated.
- 2026-04-26 - Codex round-3 audit (`codex_implementation_review_round3_response.md`) - SHIP_WITH_FIXES. All 4 round-2 residuals confirmed RESOLVED. One NEW_ISSUE_DISCOVERED_LATE: R3-1 (runtime threshold resolver in `core/review/summary.py` accepts bools as numeric values via `int()` / `float()` coercion when `hai config validate` is skipped).
- 2026-04-26 - Codex round-3 maintainer response (`codex_implementation_review_response_round4.md`) - R3-1 accepted and shipped same-cycle. New `ReviewSummaryThresholdError` exception + `_coerce_int` / `_coerce_float` helpers in `core/review/summary.py` reject bools and non-numeric types at the runtime boundary; error message names `hai config validate` as the diagnostic. 6 new regression tests. Bool-as-number bug class now closed at every entry point (validator + runtime resolver + test fixtures). Suite: 2066 → 2072 passed; drift validator OK.
- 2026-04-26 - Codex round-4 audit (`codex_implementation_review_round4_response.md`) - **SHIP_WITH_NOTES: ship now**. R3-1 confirmed RESOLVED; no must-fix issue and no W57 regression. Two v0.1.9 backlog notes only: (B1) global threshold-runtime type hardening outside `policy.review_summary`, (B2) pre-existing pytest unraisable warning. Both logged to `reporting/plans/v0_1_9/BACKLOG.md`. Final: 2072 passed, 4 skipped, drift OK. **v0.1.8 cleared for tag.**
