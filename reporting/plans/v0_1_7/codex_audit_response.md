# Codex Audit - v0.1.7 Plan Response

## Step 0 confirmation

Verified before auditing:

- `pwd`: `/Users/domcolligan/health_agent_infra`
- `git branch --show-current`: `v0.1.4-release`
- `git log --oneline -1`: `ff77aff v0.1.5: sync release QA + handoff docs to v0.1.5 reality`
- `ls reporting/plans/v0_1_7/`: `PLAN.md`, `REPORT.md`, `codex_audit_prompt.md`

I ignored `/Users/domcolligan/Documents/health_agent_infra/`.

## Validation of maintainer's read (Job A)

### §1 Strong parts

**Three real determinism boundaries: VERIFIED, with scope.** `hai propose` validates `DomainProposal` payloads through `validate_proposal_dict` before write (`src/health_agent_infra/cli.py:1011-1025`; `src/health_agent_infra/core/writeback/proposal.py:130-143`; `src/health_agent_infra/core/writeback/proposal.py:160-230`), synthesis validates every final recommendation before the transaction (`src/health_agent_infra/core/synthesis.py:500-523`), and `record_review_outcome` now re-validates the constructed outcome before JSONL append (`src/health_agent_infra/core/review/outcomes.py:173-188`; `src/health_agent_infra/core/writeback/outcome.py:83-140`). I did not re-run a full JSONL-vs-SQLite consistency audit this round.

**Honest `hai daily` proposal gate: VERIFIED.** Current `cmd_daily` computes `present_domains`, `missing_expected`, emits `awaiting_proposals` / `incomplete` / `complete`, and blocks synthesis unless the gate is `complete` (`src/health_agent_infra/cli.py:3713-3756`). The generated capability annotation includes the same status set and explanation (`src/health_agent_infra/cli.py:5733-5747`).

**No uncaught tracebacks from CLI surfaces: PARTIALLY VERIFIED.** The shared `_load_json_arg` catches missing files and malformed JSON as `USER_INPUT` (`src/health_agent_infra/cli.py:112-150`), and `main()` suppresses ordinary uncaught tracebacks behind an `INTERNAL` exit unless `HAI_DEBUG_TRACEBACK=1` is set (`src/health_agent_infra/cli.py:6067-6100`). I did not fuzz every `cmd_*` argument combination in this audit.

**Clean local-first defaults: VERIFIED for code, OVERSTATED for docs.** `resolve_base_dir` implements explicit arg > `$HAI_BASE_DIR` > `~/.health_agent` (`src/health_agent_infra/core/paths.py:30-44`), and `_resolve_pull_source` implements explicit `--source` > `--live` > intervals.icu when configured > csv (`src/health_agent_infra/cli.py:515-547`). But `hai daily` parser help still says the default is csv unless `--live` is set (`src/health_agent_infra/cli.py:5665-5675`), `intent-router` still routes refresh through `hai pull --live` (`src/health_agent_infra/skills/intent-router/SKILL.md:85-99`), and `agent_integration.md` still says `hai pull` reads the CSV fixture by default (`reporting/docs/agent_integration.md:184-189`).

**Skill <-> CLI drift validator: OVERSTATED.** The validator exists and is wired to a pytest test (`scripts/check_skill_cli_drift.py:21-30`; `safety/tests/test_skill_cli_drift.py:30-40`), but it only inspects fenced code blocks (`scripts/check_skill_cli_drift.py:73-90`; `safety/tests/test_skill_cli_drift.py:14-17`) and does not parse `allowed-tools` frontmatter. That leaves the exact W16 class still unverified: `daily-plan-synthesis` grants `Bash(hai synthesize --bundle-only *)` but its example calls `hai synthesize --as-of <today> --user-id <u> --bundle-only` (`src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:1-5`; `src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:17-20`).

**Bounded local-only research surface: VERIFIED.** `hai research topics` and `hai research search` expose only allowlisted topic-token retrieval (`src/health_agent_infra/cli.py:4501-4538`), the expert skill grants `hai research` rather than `python3 -c` (`src/health_agent_infra/skills/expert-explainer/SKILL.md:1-5`), and retrieval explicitly rejects user-context/network-shaped expansion (`src/health_agent_infra/core/research/retrieval.py:1-18`).

**Schema-version gap detection in doctor: VERIFIED, but incomplete as a runtime guard.** Doctor calls `detect_schema_version_gaps` and emits a warning with `applied_gaps` (`src/health_agent_infra/core/doctor/checks.py:84-142`). `cmd_state_migrate` still calls `apply_pending_migrations` directly and never checks gaps (`src/health_agent_infra/cli.py:3248-3283`).

**Test count claim: DEFERRED - DIDN'T INVESTIGATE.** REPORT claims `1921 passing, 4 skipped` (`reporting/plans/v0_1_7/REPORT.md:41-42`). I did not rerun the full suite in this plan audit.

### §1 Real gaps

**A. Agent flow documented but not orchestrated: CONFIRMED.** `hai daily` stops at the proposal gate and tells the agent to post proposals, then rerun (`src/health_agent_infra/cli.py:3601-3612`; `src/health_agent_infra/cli.py:3736-3756`). The intent-router still encodes the orchestration in prose (`src/health_agent_infra/skills/intent-router/SKILL.md:101-129`).

**B. v0.1.6 is not distributed: CONFIRMED.** `pyproject.toml` is at `0.1.6` (`pyproject.toml:5-8`), but the active publish docs are stale: `PUBLISH_CHECKLIST.md` still references `0.1.0` artifacts and expected output (`reporting/docs/launch/PUBLISH_CHECKLIST.md:8-19`; `reporting/docs/launch/PUBLISH_CHECKLIST.md:36-40`), and the v0.1.4 release QA still pins `0.1.5` (`reporting/plans/v0_1_4/release_qa.md:72-84`; `reporting/plans/v0_1_4/release_qa.md:178-194`).

**C. Agent-driven contract implicit: CONFIRMED.** Current daily output has a `hint` string when blocked, but no typed action contract (`src/health_agent_infra/cli.py:3736-3756`). The capability manifest lists `hai daily` output at the report/status level, not action-level orchestration (`src/health_agent_infra/cli.py:5726-5748`).

**D. `hai stats` is shallow: CONFIRMED.** Current stats reads sync freshness, recent events, command summary, and daily streak (`src/health_agent_infra/cli.py:4257-4372`); the parser has `--json` and `--limit` but no `--funnel` or `--since` (`src/health_agent_infra/cli.py:5870-5896`).

**E. Synthesis quality not evaluated end-to-end: PARTIALLY_CONFIRMED.** The skill-harness blocker confirms live transcript capture is still operator-driven, only recovery is covered, synthesis skill is unscored, and cross-run stability is not measured (`safety/evals/skill_harness_blocker.md:79-111`). REPORT's specific 90-day calibration-eval framing is plausible, but the blocker doc points more directly at live skill behavior and synthesis-skill scoring than at a 90-day deterministic simulation (`safety/evals/skill_harness_blocker.md:99-111`).

**F. Cold-start asymmetry documented but not designed: CONFIRMED.** Snapshot attaches `cold_start` and `history_days` to all six domains (`src/health_agent_infra/core/state/snapshot.py:41-73`; `src/health_agent_infra/core/state/snapshot.py:108-135`), but only running, strength, and stress have policy-level cold-start relaxation hooks (`src/health_agent_infra/domains/running/policy.py:150-218`; `src/health_agent_infra/domains/strength/policy.py:185-256`; `src/health_agent_infra/domains/stress/policy.py:178-241`). Nutrition has an explicit non-relaxation guard (`safety/tests/test_nutrition_cold_start_non_relaxation.py:1-20`; `safety/tests/test_nutrition_cold_start_non_relaxation.py:63-83`).

**G. Reproject determinism partially structural: CONFIRMED.** The public contract says `hai state reproject` is deterministic modulo projection timestamps (`reporting/docs/agent_cli_contract.md:96`), while proposal projection stores volatile `projected_at` / revision timestamps (`src/health_agent_infra/core/state/migrations/003_synthesis_scaffolding.sql:35-40`; `src/health_agent_infra/core/state/projector.py:2092-2100`).

**H. Synthesis-skill `allowed-tools` may block examples: CONFIRMED.** The skill frontmatter and body order still disagree (`src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:1-5`; `src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:17-20`; `src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:91`), and the drift validator does not parse allowed-tools (`scripts/check_skill_cli_drift.py:73-182`).

**I. `cli.py` is too large: CONFIRMED, but not release-critical.** The file reaches line 6104 in the current working tree (`src/health_agent_infra/cli.py:6104`). The parser, helpers, and handlers are still co-located (`src/health_agent_infra/cli.py:4564-6064`).

**J. No public API stability surface: PARTIALLY_CONFIRMED.** Some package entry modules already declare `__all__` (`src/health_agent_infra/core/state/__init__.py:81-142`; `src/health_agent_infra/core/capabilities/__init__.py:40-47`), while many implementation modules are not explicitly export-governed (`src/health_agent_infra/core/synthesis.py:1-20`; `src/health_agent_infra/domains/sleep/classify.py:1-44`). I do not think this is a v0.1.7 release blocker.

**K. No agent fixture-day eval: CONFIRMED.** `hai eval run` covers deterministic domain/synthesis scenarios (`reporting/docs/agent_cli_contract.md:71`), while the skill-harness blocker says live skill behavior is still not captured and synthesis skill is unscored (`safety/evals/skill_harness_blocker.md:81-111`).

**Missed gap L - daily telemetry cannot support W28 yet: CONFIRMED.** `cmd_daily` logs a `runtime_event_log` row but only sets `exit_code`, not context (`src/health_agent_infra/cli.py:3579-3598`). `runtime_event_log.context_json` exists specifically for command context (`src/health_agent_infra/core/state/migrations/012_runtime_event_log.sql:27-30`; `src/health_agent_infra/core/state/runtime_event_log.py:139-143`). W28 needs W21 to persist proposal-gate status/missing domains or the funnel will be reconstructed from incomplete evidence.

**Missed gap M - pull-source prose drift survived v0.1.6: CONFIRMED.** Code and README say intervals.icu is the implicit default when configured (`src/health_agent_infra/cli.py:515-547`; `README.md:51-58`), but daily help, intent-router, and agent integration docs still say or imply older CSV/Garmin defaults (`src/health_agent_infra/cli.py:5665-5675`; `src/health_agent_infra/skills/intent-router/SKILL.md:85-99`; `reporting/docs/agent_integration.md:184-189`).

**Missed gap N - W6/W8 keep slipping: CONFIRMED.** Nutrition intake still auto-supersedes same-day totals without requiring an explicit replace/confirm flag (`src/health_agent_infra/cli.py:2464-2512`), and `--planned-session-type` remains free text in parser help even though README documents a canonical vocabulary (`src/health_agent_infra/cli.py:5438`; `README.md:190-195`).

### §2 Success criteria

**Mostly agree, but the criteria are incomplete.** The maintainer is right that the agent flow is the product and that local-first/governed/auditable behavior is central (`reporting/plans/v0_1_7/REPORT.md:118-126`). The non-goals also correctly exclude multi-user/cloud, meal-level nutrition, production scale, and rich UI (`reporting/docs/non_goals.md:15-29`; `reporting/docs/non_goals.md:49-73`).

The missing success criteria are: outside-builder install must work, repo legibility must survive outsider review, and outcomes must be tracked into a future tailoring story. Those are explicit in the founder doctrine (`reporting/docs/archive/doctrine/founder_doctrine_2026-04-17.md:116-123`). Current non-goals say review outcomes do not yet feed confidence calibration, threshold tuning, or an ML loop (`reporting/docs/non_goals.md:31-38`), so v0.1.7 should at least improve outcome visibility and fixture evidence rather than claim adaptation.

### §3 Investment framing

**Agree with A leading, but not "A in full."** W21 and W22 should lead because the agent contract and distribution are the release's leverage points (`reporting/plans/v0_1_7/REPORT.md:146-163`; `reporting/plans/v0_1_7/PLAN.md:45-96`). But "skill-eval harness completion" is too broad for v0.1.7: the blocker doc's bounded next steps are recovery live transcript capture and maybe one second domain, with synthesis-skill harness after that (`safety/evals/skill_harness_blocker.md:127-145`).

**Re-rank:** A leads with W21/W22 plus telemetry and docs drift cleanup; B follows with W23/W24/W25/W26 and a scoped W27; C is mostly deferred. W29 and W30 should not consume v0.1.7 budget unless all P0/P1 agent-flow work is already green.

## Audit of the workstream plan (Job B)

### W21 - `hai daily --auto` next-action manifest

**Framing: AGREE.** Current daily output requires the agent to interpret `proposal_gate`, a prose hint, and intent-router instructions (`src/health_agent_infra/cli.py:3730-3756`; `src/health_agent_infra/skills/intent-router/SKILL.md:101-129`).

**Fix: AGREE_WITH_CHANGES.** The proposed `next_actions[]` shape is not sufficient yet (`reporting/plans/v0_1_7/PLAN.md:52-83`). It lacks `schema_version`, `action_id`, concrete `command_argv`, `input_schema`, `blocking`, `safe_to_retry`, `after_success`, `reads_json_pointer`, `idempotency_key`, and a stable `reason_code`. The example also says `synthesis_ready` should run `hai synthesize` directly (`reporting/plans/v0_1_7/PLAN.md:73-76`), but the governed daily path schedules reviews after synthesis (`src/health_agent_infra/cli.py:3758-3796`), so the action should normally be `hai daily --skip-pull` unless the explicit mode is "two-pass synthesis only."

**Effort: UNDER-SIZED.** This is M/L, not just an output-shape tweak, because it needs schema, docs, manifest annotations, telemetry, and an end-to-end fixture agent test.

**Missing:** Persist the daily run's `overall_status`, expected/present/missing domains, and action count into `runtime_event_log.context_json`, because W28 cannot build a reliable funnel from stdout that was never stored (`src/health_agent_infra/core/state/migrations/012_runtime_event_log.sql:27-30`; `src/health_agent_infra/cli.py:3593-3598`).

### W22 - PyPI release of 0.1.6

**Framing: AGREE.** `pyproject.toml` declares version `0.1.6` (`pyproject.toml:5-8`), while the current publish checklist and release QA docs still target older versions (`reporting/docs/launch/PUBLISH_CHECKLIST.md:8-19`; `reporting/plans/v0_1_4/release_qa.md:72-84`).

**Fix: AGREE_WITH_CHANGES.** Building wheel/sdist and publishing is necessary (`reporting/plans/v0_1_7/PLAN.md:90-96`), but acceptance should include `python -m twine check dist/*`, README render check, TestPyPI or an explicit skip decision, fresh `pipx install "health-agent-infra==0.1.6"`, `hai capabilities`, `hai eval run --domain recovery --json`, `hai doctor --json`, and a no-secret wheel listing. CI already builds and smoke-tests a wheel, but only runs `hai --version` and `hai --help` from the wheel (`.github/workflows/flagship-proof.yml:48-57`).

**Effort: M.** Public release work is mostly procedural, but the stale release docs make it larger than the plan implies.

### W23 - Migration gap gating in `cmd_state_migrate`

**Framing: AGREE.** Doctor detects gaps (`src/health_agent_infra/core/doctor/checks.py:104-142`), but `cmd_state_migrate` does not (`src/health_agent_infra/cli.py:3248-3283`).

**Fix: AGREE_WITH_CHANGES.** Add the command guard, but also guard `apply_pending_migrations` or add a lower-level strict helper; its own docstring says callers that need integrity should check contiguity, but the function still uses `current_schema_version` max-version skip logic (`src/health_agent_infra/core/state/store.py:86-119`; `src/health_agent_infra/core/state/store.py:210-243`).

**Effort: S.** Small code change plus tests.

### W24 - Cold-start matrix decision

**Framing: AGREE.** All domains carry cold-start flags (`src/health_agent_infra/core/state/snapshot.py:41-73`; `src/health_agent_infra/core/state/snapshot.py:122-135`), but policy relaxation exists only in running/strength/stress (`src/health_agent_infra/domains/running/policy.py:163-174`; `src/health_agent_infra/domains/strength/policy.py:200-210`; `src/health_agent_infra/domains/stress/policy.py:192-200`).

**Fix: AGREE_WITH_CHANGES.** I would commit to the asymmetry, not blindly extend relaxation. Recovery's `insufficient` coverage requires missing headline sleep or soreness (`src/health_agent_infra/domains/recovery/classify.py:152-166`; `src/health_agent_infra/domains/recovery/classify.py:298-305`), so the right action is intake, not relaxation. Sleep's `insufficient` coverage means no `sleep_hours` (`src/health_agent_infra/domains/sleep/classify.py:158-178`), so it also should ask for/await evidence rather than recommend from nothing. Nutrition's no-row case is explicitly an insufficient macro basis and already has a non-relaxation test (`src/health_agent_infra/domains/nutrition/classify.py:162-188`; `safety/tests/test_nutrition_cold_start_non_relaxation.py:63-83`).

**Effort: M.** The doc is easy; the hard part is pinning every domain's rationale and ensuring W21 emits `intake_required` rather than treating "no relaxation" as a dead end.

### W25 - Synthesis-skill `allowed-tools` order test

**Framing: AGREE.** The mismatch still exists (`src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:1-5`; `src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:17-20`; `src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:91`).

**Fix: AGREE_WITH_CHANGES.** Extend the validator to parse frontmatter and examples, then either reorder examples or broaden to `Bash(hai synthesize *)`. If broadening, keep the skill's prose constrained to `--bundle-only` and `--drafts-json` because `hai synthesize` is a write surface (`reporting/docs/agent_cli_contract.md:69`; `src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:20-24`).

**Effort: S/M.** S if only this skill; M if the validator becomes a general frontmatter parser.

### W26 - `cmd_propose` race-path test

**Framing: AGREE.** The handler now treats `ProposalReplaceRequired` as fatal after JSONL append (`src/health_agent_infra/cli.py:1061-1099`), but the plan says the rare path lacks a direct regression (`reporting/plans/v0_1_7/PLAN.md:145-156`).

**Fix: AGREE.** Monkeypatching the pre-flight/projection seam is the right test.

**Effort: S.**

### W27 - Property-based tests for projectors

**Framing: AGREE.** The determinism claim exists in the contract (`reporting/docs/agent_cli_contract.md:96`), and projection timestamps are volatile by design (`src/health_agent_infra/core/state/migrations/003_synthesis_scaffolding.sql:35-40`).

**Fix: AGREE_WITH_CHANGES.** `hypothesis` is acceptable because it is already a dev dependency (`pyproject.toml:40-45`), but do not start by generating arbitrary full JSONL. Start with deterministic replay over curated valid fixtures, then use Hypothesis around small normalized object factories. Otherwise fixture generation will dominate the work.

**Effort: M/L.** This is larger than W23/W26 and should not block W21/W22.

### W28 - `hai stats` agent funnel

**Framing: AGREE.** Current stats is local and useful but shallow (`src/health_agent_infra/cli.py:4257-4372`), and the parser lacks `--funnel` / `--since` (`src/health_agent_infra/cli.py:5870-5896`).

**Fix: AGREE_WITH_CHANGES.** The proposed metrics need persisted inputs that do not all exist yet (`reporting/plans/v0_1_7/PLAN.md:180-191`). Proposal-gate histograms and incomplete causes require daily context logging; proposal latency needs a defined join between `runtime_event_log.started_at` and `proposal_log.projected_at`; review rate can be computed from review tables, but "not-yet-reviewed" needs pending review events included (`src/health_agent_infra/core/state/migrations/012_runtime_event_log.sql:36-48`; `src/health_agent_infra/core/state/migrations/003_synthesis_scaffolding.sql:23-40`).

**Effort: M.** Make W21 telemetry a prerequisite.

### W29 - `cli.py` split into per-command modules

**Framing: AGREE.** `cli.py` is 6104 lines and mixes parser, helpers, and handlers (`src/health_agent_infra/cli.py:4564-6064`).

**Fix: DEFER TO v0.1.8.** This is the wrong time for a broad file move. The v0.1.7 behavioral work is contract-heavy, and a 6000-line split would make implementation review noisy. The console script currently points at `health_agent_infra.cli:main` (`pyproject.toml:47-48`), so turning `cli.py` into a `cli/` package must preserve import compatibility for tests and users.

**Cost of waiting:** tolerable for one release. Adopt an incremental rule: new v0.1.7 helper modules may be extracted, but do not require `cli.py <500 lines` in this cycle.

### W30 - Public API stability test

**Framing: PARTIALLY AGREE.** Some public package entrypoints already declare `__all__` (`src/health_agent_infra/core/state/__init__.py:81-142`; `src/health_agent_infra/core/capabilities/__init__.py:40-47`), but the project does not define a supported Python API separate from the CLI contract (`reporting/docs/agent_cli_contract.md:1-21`).

**Fix: DEFER TO v0.1.8.** A package-wide `__all__` snapshot creates churn without improving the agent/runtime contract. If kept in v0.1.7, limit it to top-level package exports and modules already documented as public.

**Effort: M if done literally.** The plan sizes it like P2 small, but declaring `__all__` "in every public module" requires first deciding what "public" means.

### W31 - README + changelog discipline

**Framing: AGREE.** The only release notes file is still v0.1.5 (`reporting/plans/v0_1_4/release_notes.md:1-6`), and no `CHANGELOG.md` or `RELEASE.md` exists in the tree (`reporting/plans/v0_1_7/PLAN.md:220-229`).

**Fix: AGREE_WITH_CHANGES.** Do this with W22, not last. Release docs are a PyPI precondition, not tag cleanup. Update or retire the stale `reporting/docs/launch/PUBLISH_CHECKLIST.md` rather than adding a competing `RELEASE.md` that leaves the 0.1.0 checklist alive (`reporting/docs/launch/PUBLISH_CHECKLIST.md:8-19`; `reporting/docs/launch/PUBLISH_CHECKLIST.md:48-80`).

**Effort: S/M.**

### Workstreams the plan missed

**W32 - Source-default and agent-doc drift sweep (P1).** Code and README now say intervals.icu auto-defaults when configured (`src/health_agent_infra/cli.py:515-547`; `README.md:51-58`), but daily help, intent-router, and agent integration still say older CSV/Garmin behavior (`src/health_agent_infra/cli.py:5665-5675`; `src/health_agent_infra/skills/intent-router/SKILL.md:85-99`; `reporting/docs/agent_integration.md:184-189`). Acceptance: `hai daily` help, capabilities, README, `agent_integration.md`, and intent-router all agree; validator coverage expands beyond fenced command flags where practical.

**W33 - Planned-session vocabulary command/manifest (P1, W8 revived).** README documents canonical values (`README.md:190-195`), but parser help still says free text examples (`src/health_agent_infra/cli.py:5438`). W21 `next_actions` should not require README memory for planned-session intake. Acceptance: add a read-only vocabulary surface or manifest field, and ensure W21 `intake_required` actions reference it.

**W34 - Nutrition supersede guard (P1, W6 revived).** Nutrition intake silently resolves a prior same-day submission and supersedes it (`src/health_agent_infra/cli.py:2464-2512`). README warns users to log once at end of day (`README.md:184-188`), but a public PyPI release should make correction explicit. Acceptance: same-day second write either requires `--replace` / `--confirm-supersede` or emits a structured warning field that agents must surface before mutation.

**W35 - Manifest-only fixture-day agent test (P0/P1).** W21 acceptance says an agent can plan without `intent-router` (`reporting/plans/v0_1_7/PLAN.md:81-83`), but the plan needs a test that proves it. Acceptance: a test harness consumes only `hai daily --auto` JSON, invokes the listed commands/skills via fixtures or stubs, posts proposals, reruns daily, and reaches a committed plan.

**W36 - Release proof pack (P1).** W22/W31 should leave a short proof artifact with branch, version, full-suite result, wheel install result, capability contract regeneration, drift validator result, and known deferrals. This follows the existing release-QA discipline but must be updated for v0.1.6/v0.1.7 (`reporting/plans/v0_1_4/release_qa.md:53-90`; `reporting/plans/v0_1_4/release_qa.md:174-194`).

### Workstreams the plan should cut

**Cut/defer W29 from v0.1.7.** It is worthwhile but too noisy for the same release that changes the agent contract (`src/health_agent_infra/cli.py:4564-6064`; `pyproject.toml:47-48`).

**Cut/defer W30 from v0.1.7.** The CLI manifest is the public contract today (`reporting/docs/agent_cli_contract.md:1-21`); Python API snapshotting can wait until the package intentionally supports Python consumers.

**Do not expand MCP or meal-level nutrition.** The plan correctly lists MCP implementation and per-meal nutrition as non-goals (`reporting/plans/v0_1_7/PLAN.md:32-39`), matching the active non-goals (`reporting/docs/non_goals.md:49-73`; `reporting/docs/non_goals.md:95-100`).

## Revised plan (Job C)

### Reconciliation table

| WS | Maintainer's call | Codex's call | Reason |
|---|---|---|---|
| W21 | P0, ship | agree-with-changes | Flagship is right, but `next_actions[]` needs a versioned machine contract, concrete argv, schemas, after-success routing, and telemetry (`reporting/plans/v0_1_7/PLAN.md:52-83`; `src/health_agent_infra/cli.py:3736-3756`). |
| W22 | P0, ship | agree-with-changes | Publish is mandatory, but release docs/checklists are stale and wheel smoke must be stronger (`pyproject.toml:5-8`; `reporting/docs/launch/PUBLISH_CHECKLIST.md:8-19`; `.github/workflows/flagship-proof.yml:48-57`). |
| W23 | P1, ship | agree-with-changes | Guard command and lower-level migration path, not only CLI (`src/health_agent_infra/cli.py:3248-3283`; `src/health_agent_infra/core/state/store.py:210-243`). |
| W24 | P1, ship | agree-with-changes | Ship the matrix, but preserve recovery/sleep/nutrition non-relaxation unless code evidence changes (`src/health_agent_infra/domains/recovery/classify.py:152-166`; `src/health_agent_infra/domains/sleep/classify.py:158-178`; `safety/tests/test_nutrition_cold_start_non_relaxation.py:63-83`). |
| W25 | P1, ship | agree-with-changes | Validator must parse allowed-tools/frontmatter; current validator only checks fenced code (`scripts/check_skill_cli_drift.py:73-182`). |
| W26 | P1, ship | agree | Small, closes untested W15 race path (`src/health_agent_infra/cli.py:1061-1099`). |
| W27 | P1, ship | scope down | Start with deterministic replay fixtures; Hypothesis is okay because it is already dev-only (`pyproject.toml:40-45`). |
| W28 | P1, ship | agree-after-W21 | Funnel needs daily context logging before it can be truthful (`src/health_agent_infra/core/state/migrations/012_runtime_event_log.sql:27-30`; `src/health_agent_infra/cli.py:3593-3598`). |
| W29 | P2, ship last | defer to v0.1.8 | Large refactor obscures behavioral review; preserve `health_agent_infra.cli:main` during public-release work (`src/health_agent_infra/cli.py:4564-6064`; `pyproject.toml:47-48`). |
| W30 | P2, ship | defer to v0.1.8 | CLI manifest is the supported contract; Python API stability is not yet defined (`reporting/docs/agent_cli_contract.md:1-21`). |
| W31 | P2, release tag | move earlier, agree-with-changes | Changelog/release checklist should be W22 precondition, not final polish (`reporting/plans/v0_1_4/release_notes.md:1-6`; `reporting/docs/launch/PUBLISH_CHECKLIST.md:8-19`). |
| W32 | new | add P1 | Source-default docs/skill drift survived v0.1.6 (`src/health_agent_infra/cli.py:5665-5675`; `src/health_agent_infra/skills/intent-router/SKILL.md:85-99`; `reporting/docs/agent_integration.md:184-189`). |
| W33 | new | add P1 | Planned-session vocabulary is documented but not discoverable from CLI/manifest (`README.md:190-195`; `src/health_agent_infra/cli.py:5438`). |
| W34 | new | add P1 | Nutrition same-day supersede still mutates silently except for JSON output (`src/health_agent_infra/cli.py:2464-2512`; `README.md:184-188`). |
| W35 | new | add P0/P1 | W21 needs a manifest-only fixture-day test to prove no intent-router prose fallback (`reporting/plans/v0_1_7/PLAN.md:81-83`). |
| W36 | new | add P1 | Public release needs a proof pack updated from stale release-QA docs (`reporting/plans/v0_1_4/release_qa.md:53-90`; `reporting/plans/v0_1_4/release_qa.md:174-194`). |

### Re-sequenced v0.1.7 punch list

1. [P0] W22 + W31 + W36: publish v0.1.6 from a reproducible release checklist, update stale release docs, and create a release proof pack.
2. [P0] W21 + W35: design `hai daily --auto` as a versioned next-action manifest and prove a fixture day can be planned from that manifest without intent-router prose.
3. [P0] W21 telemetry prerequisite for W28: write daily `overall_status`, expected/present/missing domains, and next-action counts into `runtime_event_log.context_json`.
4. [P1] W32: sweep source-default docs, skills, parser help, and capabilities until intervals.icu/csv/Garmin semantics agree.
5. [P1] W23: make gappy migrations refuse in `hai state migrate` and in the lower-level migration path or strict helper.
6. [P1] W25: extend drift validation to `allowed-tools` and fix `daily-plan-synthesis`.
7. [P1] W26: add the `cmd_propose` race-path regression.
8. [P1] W33: expose planned-session vocabulary through CLI/manifest so W21 actions can cite it.
9. [P1] W34: add an explicit nutrition same-day supersede guard or mandatory structured warning.
10. [P1] W24: ship the cold-start policy matrix and tests; preserve asymmetry unless a code-backed rationale changes.
11. [P1] W28: implement `hai stats --funnel --since N` using persisted telemetry, not reconstructed stdout assumptions.
12. [P2] W27: add deterministic projector replay fixtures first; add Hypothesis only around small valid-object factories.
13. [P2] Skill harness: capture recovery live transcripts if time remains; do not claim "completion" for all per-domain skills in v0.1.7 (`safety/evals/skill_harness_blocker.md:127-145`).
14. [DEFER] W29: full `cli.py` split to v0.1.8.
15. [DEFER] W30: public Python API snapshot to v0.1.8+ after the supported API boundary is defined.

### Ship verdict criteria

I would vote SHIP on v0.1.7 only if the implementation review sees all of this:

1. v0.1.6 is published and fresh `pipx install "health-agent-infra==0.1.6"` smoke passes, including `hai --version`, `hai capabilities`, `hai eval run --domain recovery --json`, and a basic `hai doctor --json` run.
2. Release docs are no longer stale: `CHANGELOG.md` or the chosen release notes path covers v0.1.6/v0.1.7, and old 0.1.0/0.1.5 publish checklists are updated or retired.
3. `hai daily --auto` emits a versioned `next_actions[]` schema with concrete argv, reason codes, domain, priority, blocking status, input schema references, after-success routing, idempotency/safe-retry hints, and mutation class.
4. A committed fixture-day test consumes `next_actions[]` only and reaches a committed plan without consulting `intent-router` or `agent_integration.md`.
5. `hai daily --auto` routes completion through `hai daily --skip-pull` or explicitly documents when direct `hai synthesize` is intentional; review scheduling must not be accidentally skipped.
6. `runtime_event_log.context_json` captures daily proposal-gate status and missing domains, and `hai stats --funnel --since N` uses persisted state with tests for awaiting/incomplete/complete days.
7. Source-default semantics agree across code, parser help, README, capabilities, intent-router, and `agent_integration.md`.
8. `hai state migrate` and the lower-level migration path refuse gappy DBs with the same diagnostic family as doctor.
9. Cold-start matrix doc exists, code matches it, and tests pin all six domain decisions; recovery/sleep/nutrition remain non-relaxed unless a new code-backed rationale lands.
10. `daily-plan-synthesis` allowed-tools/examples are proven consistent by tests.
11. `cmd_propose` race-path regression is committed.
12. Planned-session vocabulary is machine-discoverable from CLI/manifest and used by W21 actions.
13. Nutrition same-day supersede is explicit enough that an agent cannot silently replace a daily total without surfacing it.
14. W29 and W30 are either deferred with rationale or, if implemented, reviewed as behavior-preserving with full tests and no console-script/import regression.
15. Full suite, targeted v0.1.7 suite, generated contract check, drift validator, wheel build, and `git diff --check` are green.
