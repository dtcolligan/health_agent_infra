# Codex Implementation Review Response - v0.1.10

## Findings

### F-CDX-IR-01. Partial-day nutrition gate is not wired into the runtime snapshot path

**Question:** Q3
**Severity:** blocker
**File:** src/health_agent_infra/core/state/snapshot.py:875
**Description:** `_r_extreme_deficiency` now accepts `meals_count` and `is_end_of_day`, and the direct unit tests pass. The production snapshot path still calls `evaluate_nutrition_policy(nutrition_classified)` without passing the accepted nutrition row's `meals_count` or any end-of-day signal. Because `meals_count=None` is treated as the backward-compatible path, the original breakfast-only false positive still fires in normal `hai state snapshot` / `hai daily` flows. I reproduced this with a one-meal nutrition intake at midday: `today.meals_count` was `1`, but `policy_result.forced_action` was still `escalate_for_user_review`.
**Recommendation:** fix-before-ship

### F-CDX-IR-02. W-A coercer sweep missed live threshold consumers

**Question:** Q2
**Severity:** blocker
**File:** src/health_agent_infra/core/synthesis_policy.py:811
**Description:** The helper bodies correctly reject bools before ints, but the application sweep is incomplete. The requested grep still finds threshold-consumer survivors: `float(cfg.get("heavy_lower_body_min_volume"...))`, `int(cfg.get("vigorous_intensity_min"...))`, `int(cfg.get("long_run_min_duration_s"...))`, `int(cfg.get("body_battery_max"...))`, plus the Garmin retry config casts in `core/pull/garmin_live.py:160`. These are the same bool-as-int class W-A set out to close.
**Recommendation:** fix-before-ship

### F-CDX-IR-03. Release-proof pytest command is not reproducible

**Question:** Q6
**Severity:** blocker
**File:** verification/tests/test_intake_readiness.py:177
**Description:** `uv run pytest verification/tests -q` did not match `RELEASE_PROOF.md`; it returned `8 failed, 2161 passed, 2 skipped`. The failures come from pull/daily tests that expect deterministic fixture behavior but do not force `--source csv`; when intervals.icu credentials are configured, `_resolve_pull_source` selects the live intervals.icu path and the tests fail with HTTP 403. This invalidates the proof claim as written.
**Recommendation:** fix-before-ship

### F-CDX-IR-04. Audit-chain break deferral is not sound for a ship verdict

**Question:** Q1
**Severity:** blocker
**File:** reporting/plans/v0_1_10/RELEASE_PROOF.md:35
**Description:** `PLAN.md` still names F-B-02 and F-B-01 as ship acceptance items, including "`F-B-02 ... produces _v2 plan id`", while `RELEASE_PROOF.md` defers both W-E and W-F to v0.1.11. Deferring F-C-04 is defensible because the fix shape interacts with strength freshness. Deferring the same-day state-change re-synth issue is not: it is a known audit-chain/correctness break where a user can correct state and still keep a stale same-day plan.
**Recommendation:** fix-before-ship

### F-CDX-IR-05. Running activity rollup only partially reaches accepted running state

**Question:** Q4
**Severity:** concern
**File:** src/health_agent_infra/core/state/projector.py:437
**Description:** The clean flow invokes `aggregate_activities_to_daily_rollup`, and persona results show the running defer-forever problem improved for P2/P7. The wire is still partial: the aggregator computes `total_duration_s` and `session_count`, but `project_accepted_running_state_daily` hardcodes both to `None` and stamps `derivation_path="garmin_daily"` even for historical rows derived from `running_activity`. That leaves provenance and rollup completeness weaker than the W-D-ext claim suggests.
**Recommendation:** document-and-defer

### F-CDX-IR-06. Persona harness drift checks are post-facto, not contract-linked

**Question:** Q5
**Severity:** nit
**File:** verification/dogfood/synthetic_skill.py:27
**Description:** The harness currently hardcodes `_DOMAIN_DEFAULT_ACTION`, `_STATUS_TO_ACTION`, and `schema_version=f"{domain}_proposal.v1"`. The current tokens are valid; I checked them against `ALLOWED_ACTIONS_BY_DOMAIN`, and `hai propose` would fail if the schema version drifted. Still, the harness does not import or test against the runtime contract directly, so drift is detected only as noisy persona setup failures after the fact.
**Recommendation:** document-and-defer

## Q1 - Triage soundness

Verdict: UNSOUND

Reasoning: F-C-04/W-B is safe to defer with a clear v0.1.11 design note. W-K/W-L are also reasonable to defer if v0.1.11 explicitly audits them. F-B-02 is not safe to ship as a known residual in an audit-chain integrity release, and F-B-01 should remain tied to that investigation rather than treated as an acceptable unresolved release note.

## Q2 - W-A correctness

Verdict: FAIL

Reasoning: `coerce_int`, `coerce_float`, and `coerce_bool` reject bool-shaped values correctly. The 36 new tests pass. The blocker is application coverage: live `int(cfg...)`, `float(cfg...)`, and `bool(cfg...)` threshold reads remain in `synthesis_policy.py` and `garmin_live.py`.

## Q3 - W-C partial-day gate correctness

Verdict: FAIL

Reasoning: The policy function boundary behaves for explicit `meals_count` / `is_end_of_day` inputs, including `meals_count=2` and `is_end_of_day=True`. The runtime caller does not pass those values, so the actual snapshot/daily path still escalates one-meal partial-day nutrition rows.

## Q4 - W-D / W-D-ext correctness

Verdict: SOUND_WITH_CONCERNS

Reasoning: `_validate_activity_payload` covers the required fields emitted by `IntervalsIcuActivity.as_dict()` and replaces the intended `KeyError` cases with `ActivityProjectorInputError`. The persona harness exercises the clean rollup path via a synthetic pull payload and confirms P2/P7 improve. The accepted-state rollup/provenance is incomplete as noted in F-CDX-IR-05.

## Q5 - Persona harness load-bearing-ness

Verdict: SOUND_WITH_CONCERNS

Reasoning: The runner uses per-persona `HAI_STATE_DB` and `HAI_BASE_DIR`; each persona ran isolated in `/tmp/hai_dogfood_run_codex_review` with 0 crashes. Coverage matches the intended recreational/technical athlete scope and the README names exclusions. The action/schema drift guard should be made more explicit, but current mappings are valid and schema drift would fail through `hai propose`.

## Q6 - Cross-cutting integrity

Verdict: FAIL

Reasoning: No skill changes were present, `reporting/docs/agent_cli_contract.md` has zero drift against regenerated markdown, and W57 agent-safety flags remain intact for intent/target commit/archive. The cross-cutting release proof still fails because the main pytest command is not reproducible and the known F-B-02 audit-chain break remains unresolved.

## Reproduction

- `uv run pytest verification/tests -q` - failed: `8 failed, 2161 passed, 2 skipped`.
- `uv run pytest verification/tests/test_config_coerce.py verification/tests/test_partial_day_nutrition_gate.py verification/tests/test_running_activity_projector.py -q` - passed: `36 passed`.
- `uvx ruff check src/health_agent_infra/` - passed.
- `uv run hai capabilities --json` - emitted valid JSON with `hai_version` `0.1.10`.
- `uv run hai capabilities --markdown` diffed against `reporting/docs/agent_cli_contract.md` - zero drift.
- `uv run python -m verification.dogfood.runner /tmp/hai_dogfood_run_codex_review` - passed proof envelope: 8 personas, 0 crashes, 3 findings.

## Overall verdict

**DO_NOT_SHIP** - blockers: F-CDX-IR-01, F-CDX-IR-02, F-CDX-IR-03, and F-CDX-IR-04.

Required before ship:

- Wire `meals_count` and an explicit end-of-day signal into the snapshot/daily nutrition policy call.
- Replace the remaining `int/float/bool(cfg...)` threshold consumers with `core.config.coerce_*`.
- Make `verification/tests/` hermetic under configured live credentials, or document and enforce the required test environment.
- Resolve F-B-02 before v0.1.10, or explicitly re-scope the release so it is not claiming audit-chain integrity readiness.

## What I did NOT review

- I did not read or use the Phase 4 planning files under `reporting/plans/strategic_plan_v1.md`, `tactical_plan_v0_1_x.md`, `eval_strategy/`, `success_framework_v1.md`, `risks_and_open_questions.md`, `README.md`, or `v0_1_11/`.
- I did not perform a Bandit or mypy audit beyond the v0.1.10 proof claims and W-A grep requested in the prompt.
- I did not inspect private live intervals.icu credentials or vendor-side state; the 403 failures were treated as proof-repro failures, not upstream debugging targets.

## What I expected to find but did not

- No skill drift in `src/health_agent_infra/skills/`.
- No W57 regression in intent/target commit/archive capabilities; they remain `agent_safe=false`.
- No capabilities markdown drift after regenerating from the current CLI.
- No persona harness crash after W-D activity validation.
