# Changelog

All notable changes to Health Agent Infra will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the v0.x caveat that breaking changes can land in minor releases
until v1.0.

Per-release detail lives under `reporting/plans/<version>/`.

---

## [0.1.8] — 2026-04-25

> **Theme.** Plan-aware feedback visibility. Adds the intent +
> target + data-quality ledgers, the code-owned review-summary
> tokens, four new `hai stats` modes (outcomes / baselines / funnel
> / data-quality), config validate + diff, the `hai daily --auto
> --explain` thick JSON, and the synthesis-skill scoring harness.
> Outcomes are visibility-only — they never silently mutate
> thresholds, classifiers, policy, X-rules, confidence, intent, or
> targets in v0.1.8.

### Added

- **Test fixture-factory module** (`safety/tests/_fixtures/`) — pure
  dict builders `make_intent_row`, `make_target_row`,
  `make_outcome_chain`, `make_data_quality_row` plus a SQLite
  `seed_outcome_chain` helper for the existing
  `recommendation_log → review_event → review_outcome` chain. Lands
  ahead of v0.1.8 W48–W51 per `reporting/plans/v0_1_8/PLAN.md` § 0
  fixture-factory precondition so the ~80–120 forthcoming tests share
  one seeding API. Smoke-covered by
  `safety/tests/test_fixture_factory.py`.

### Changed

- **`reporting/docs/non_goals.md`** (W57) — distinguishes
  *autonomous* training/diet plan generation (still forbidden) from
  *user-authored intent and targets* (now allowed via the W49 intent
  ledger and W50 target ledger). Adds an explicit "what is allowed"
  section so contributors don't misread the upcoming intent / target
  CLI surfaces as agent-proposed planning. Also clarifies what
  bounded wellness plan suggestions could look like later under new
  governance — none of which v0.1.8 ships.
- **`hai daily --user-id` help text** rephrased from "User whose
  plan to generate" to "User whose daily pipeline to orchestrate"
  (W57 acceptance — no CLI help implies autonomous plan generation).
- **Snapshot `schema_version` bumped from `state_snapshot.v1` →
  `state_snapshot.v2`** (W48). Additive transition: every v1 field
  is preserved unchanged; the v2 bump signals new
  `snapshot.<domain>.review_summary` blocks (W48). Future v0.1.8
  workstreams (W49/W50/W51) attach further additive blocks behind
  the same v2 signal.

### Added (cont'd)

- **Code-owned review summary builder** (W48,
  `core/review/summary.build_review_summary`). Reads
  `recommendation_log` + `review_event` + `review_outcome` for a
  rolling window and emits per-domain (or aggregate) summaries with
  stable visibility-only tokens
  (`outcome_pattern_recent_negative`,
  `outcome_pattern_recent_positive`, `outcome_pattern_mixed`,
  `outcome_pattern_insufficient_denominator`). Token thresholds live
  in `[policy.review_summary]` in `DEFAULT_THRESHOLDS` and are
  user-tunable via `thresholds.toml`. Skills can narrate the tokens
  but MUST NOT compute them or mutate actions from them — visibility
  only in v0.1.8.
- **`snapshot.<domain>.review_summary`** field attached to all six
  per-domain blocks by `build_snapshot` (W48). 13 regression tests
  in `safety/tests/test_review_summary.py` cover every token rule,
  window scoping, per-domain isolation, aggregate roll-up, re-link
  counter, threshold overrides, and snapshot integration.
- **`hai stats --outcomes [--domain <d>] [--since N] [--json]`**
  (W38). Read-only mode-switch on the existing `hai stats` command;
  emits the W48 review-summary either as the per-domain bundle plus
  aggregate roll-up (default) or as one summary scoped to a single
  domain. Markdown table on TTY, structured dict on `--json`.
  Capability manifest documents the new flags;
  `agent_cli_contract.md` regenerated.
- **Intent ledger MVP** (W49, migration 019). New `intent_item`
  table + `core/intent/` module (`add_intent`, `list_intent`,
  `list_active_intent`, `archive_intent`, `supersede_intent`).
  CLI: `hai intent training add-session`, `hai intent training list`,
  `hai intent sleep set-window`, `hai intent list`, `hai intent
  archive`. Records user-authored or `agent_proposed` intent only —
  outcomes never auto-mutate intent. Replacements use
  archive/supersession, not destructive UPDATE. Snapshot integration:
  new top-level `snapshot.intent` block carries every active row
  whose `[scope_start, scope_end]` covers `as_of_date`. Per-domain
  readiness skills' `allowed-tools` extended with
  `Bash(hai intent list *)` so they can consume the snapshot's
  intent context. 13 new tests in
  `safety/tests/test_intent_ledger.py`.
- **Target ledger MVP** (W50, migration 020). New `target` table
  + `core/target/` module (`add_target`, `list_target`,
  `list_active_target`, `archive_target`, `supersede_target`).
  CLI: `hai target set`, `hai target list`, `hai target archive`.
  Wellness support, NOT medical prescriptions — every row has
  reason, source, effective date, and review date. Outcomes may
  propose target *review* later (post-v0.1.8) but must NEVER
  auto-mutate a target value. Snapshot integration: new top-level
  `snapshot.target` block carries every active row whose effective
  window covers `as_of_date`. Per-domain readiness skills'
  `allowed-tools` extended with `Bash(hai target list *)`. 13 new
  tests in `safety/tests/test_target_ledger.py`.
- **Data quality ledger** (W51, migration 021). New
  `data_quality_daily` table + `core/data_quality/` projector +
  `hai stats --data-quality` CLI mode. Per-source / per-domain row
  shape: `coverage_band`, `missingness`, `source_unavailable`,
  `user_input_pending`, `cold_start_window_state`. Snapshot
  integration: `snapshot.<domain>.data_quality` block carries the
  fields without requiring the projector to have run. Subsumes the
  v0.1.7 cold-start visibility gap — `cold_start_window_state` is
  pinned by `safety/tests/test_data_quality_cold_start_consistency.py`
  to match `snapshot.<domain>.cold_start` per the W51 maintainer
  refinement. 7 new tests across `test_data_quality_ledger.py` +
  `test_data_quality_cold_start_consistency.py`.
- **`hai stats --baselines [--domain <d>] [--json]`** (W40). Mode
  on `hai stats` that emits today's per-domain bands, classified
  state, missingness, cold-start state, and threshold source paths
  so the user can inspect what numbers the runtime is using without
  reading SQL. Read-only; no recomputation in the CLI — every band
  is the snapshot's classification. 3 new tests in
  `safety/tests/test_cli_stats_baselines.py`.
- **`hai config validate` + `hai config diff`** (W39). Discoverable
  authoring + diffing for the user's `thresholds.toml`. Validate
  parses the TOML, walks every leaf, and reports `unknown_key` /
  `type_mismatch` / `toml_parse_error` issues with paths. Default
  mode warns on unknown keys; `--strict` makes them blocking. Diff
  shows default vs override vs effective for every overridden leaf
  (and flags unknown keys with `key_known=false`). Outcomes never
  write thresholds — those paths only land via the existing
  `hai config init` scaffold. 7 new tests in
  `safety/tests/test_cli_config_validate_diff.py`.
- **`hai stats --funnel [--since N] [--json]`** (W46). Mode on
  `hai stats` that aggregates `runtime_event_log.context_json` for
  `command='daily'` runs in the window: daily run count,
  overall_status histogram, missing-domain frequency,
  blocking-action count. Closes the v0.1.7 proposal-gate telemetry
  carry-over. 2 new tests in
  `safety/tests/test_cli_stats_funnel.py`.
- **`hai daily --auto --explain` thick JSON** (W43). New
  `--explain` flag on `hai daily` adds a per-stage `explain` block
  to the output (pull / clean / snapshot / gaps / proposal_gate /
  synthesize) with `schema_version="daily_explain.v1"`. Reads
  already-computed stage data; never recomputes or fabricates
  fields. Plain `hai daily` and `hai daily --auto` (no `--explain`)
  remain byte-identical — the block is opt-in via the explicit
  flag. 3 new tests in `safety/tests/test_cli_daily_auto_explain.py`.
- **Skill harness extended to running** (W41). Added `running` to
  `SUPPORTED_DOMAINS`, `_running_snapshot_block` driving the real
  `derive_running_signals` + `classify_running_state` +
  `evaluate_running_policy`, 4 scenarios covering clean /
  insufficient-signal / policy-forced (R-acwr-spike) / cross-domain
  coupling (recovery=impaired → running holds), and
  `rubrics/running.md`. Replay mode runs in normal CI; live capture
  remains operator-gated via `HAI_SKILL_HARNESS_LIVE=1`.
- **Synthesis-skill scoring harness** (W42). New
  `safety/evals/synthesis_harness/` with `runner.py`,
  `rubrics/synthesis.md`, and 3 fixture scenarios (clean / partial
  X1a soften / escalated X3b block). Scorer applies four rubric
  invariants over a candidate synthesis output: every Phase A firing
  cited or summarised, no invented X-rule, no invented band, no
  action mutation claimed by prose. 7 new tests in
  `safety/tests/test_synthesis_harness.py` exercise both
  passing-output and each failure mode so the rubric localises the
  broken rationale line.
- **W0.1.8 replay / property tests** (W45). New
  `safety/tests/property/test_v0_1_8_replay_properties.py` pins
  determinism contracts for the new state surfaces: intent
  supersession-chain replay, late-arriving target does not
  retroactively change a past snapshot, intent / target
  active-at-date are stable across repeated calls, review-summary
  replay against the same outcome chain produces identical
  counts/tokens, and the same summary call is order-stable. 6 new
  tests.
- **Standards mapping doc** (W55,
  `reporting/docs/standards_mapping.md`). Maps HAI's evidence /
  accepted-state / recommendation / plan / review / intent /
  target / data-quality / provenance ledgers to FHIR + Open
  mHealth + Open Wearables analogues with explicit "NOT a FHIR
  dependency" disclaimer + reasoning (local-first, governed
  invariants, small-team-maintainable, no medical claims). Doc-only
  addition; helps a new contributor decide whether to align a new
  field with FHIR vocabulary without thinking they MUST.

### Fixed (Codex round-1 audit response)

- **`hai stats --data-quality` no longer mutates state** (Codex
  P1-1). Lazy-projection moved out of the read-only stats surface
  into the `hai clean` write path where it belongs per PLAN.md
  § 2 W51. Read-only contract restored; pinned by
  `test_cli_data_quality_is_read_only_on_fresh_db` which asserts
  zero rows in `data_quality_daily` after a stats call against a
  fresh DB.
- **Agent-proposed intent / target rows can no longer land
  active** (Codex P1-2). W57 invariant enforced at both the store
  (validators raise `IntentValidationError` /
  `TargetValidationError` on `source != "user_authored"` +
  `status="active"`) and the CLI (USER_INPUT exit + stderr
  message). New `hai intent commit --intent-id ID` and `hai target
  commit --target-id ID` commands provide the user-gated
  promotion path; both are explicitly marked `agent_safe=False`
  in the capability manifest. 12 new regression tests across
  intent + target ledgers.
- **`hai daily --auto --explain` snapshot block now carries the
  W48 signals it promised** (Codex P2-1). Snapshot stage write
  populated with `domains_present`, `missingness_per_domain`,
  `classified_bands_per_domain`, `review_summary_tokens_per_domain`.
  Test asserts values, not just keys.
- **Skill-harness live mode dispatches on scenario domain**
  (Codex P2-2). `_LIVE_SKILL_BY_DOMAIN` table + helper select the
  correct SKILL.md for each domain; running scenarios now invoke
  `running-readiness` rather than silently falling back to
  recovery.
- **`hai config validate` enforces numeric ranges on
  `[policy.review_summary]`** (Codex P2-3). New `range_violation`
  issue kind covers `window_days >= 1`, non-negative
  denominators / thresholds, mixed-token bounds in `[0, 1]` with
  `lower <= upper`. Always blocking; not gated on `--strict`.
- **Snapshot schema v2 transition documented in
  `agent_integration.md`** (Codex P3-1). New section lists the
  four additive fields (`review_summary`, `data_quality`,
  `intent`, `target`) and gives v1 consumers explicit
  pin-or-ignore guidance.

### Fixed (Codex round-2 audit response)

- **`hai clean` no longer silently swallows data-quality
  projection failures** (Codex R2-1). Replaces the bare
  `except: pass` with a stderr warning that names the date,
  user, exception class, and instructs the reader that
  `hai stats --data-quality` will report empty rows for the date
  until the projection is re-run. Accepted-state writes still
  commit (data-quality is best-effort), but the failure is
  visible.
- **Agent-proposed supersede defers deactivation to user commit**
  (Codex R2-2). `supersede_intent` and `supersede_target` no
  longer flip the old row to `superseded` when the new row's
  `source != "user_authored"`. The new row is inserted as
  `proposed` with the supersedes link; `commit_intent` /
  `commit_target` look up the link and atomically flip the parent
  to `superseded` in the same transaction at user-commit time.
  The W57 invariant ("agent cannot deactivate user state without
  explicit user commit") is now enforced at three boundaries:
  insert, supersede, commit. 5 new regression tests.
- **`hai config validate` rejects booleans as numeric thresholds**
  (Codex R2-3). Python's `isinstance(True, (int, float))` is
  True; without the guard a user could land `window_days = true`
  silently coerced to 1. Both the type check and the range helper
  now use a `_is_real_number(v)` predicate that excludes bools.
  3 new regression tests.
- **`_emit_data_quality_stats` docstring updated** (Codex R2-4
  nit) to reflect the strictly-read-only contract instead of the
  removed lazy-projection behaviour.

### Fixed (Codex round-3 audit response)

- **Runtime threshold resolver rejects bool-shaped numeric
  overrides** (Codex R3-1, NEW_ISSUE_DISCOVERED_LATE). The R2-3
  fix blocked bools at the validator surface; this closes the
  same class of bug at the runtime surface. New
  `ReviewSummaryThresholdError` raised by `_coerce_int` /
  `_coerce_float` in `core/review/summary.py` whenever a
  `policy.review_summary` leaf is a bool or a non-numeric type.
  Error message names `hai config validate` as the diagnostic
  tool so users hitting the runtime error have a clear next
  action. Defence-in-depth: every entry point that touches
  `policy.review_summary` (validator + runtime resolver + test
  fixtures) now rejects the same input shape. 6 new regression
  tests pinning the runtime bool / non-numeric rejection.

---

## [0.1.7] — 2026-04-25

### Added

- **`hai daily --auto`** emits a versioned `next_actions[]` manifest
  (`schema_version: next_actions.v1`) alongside the stage report
  (W21). Each action carries a typed `kind`, `reason_code`,
  `command_argv` (or `command_root` + `command_template`), `blocking`
  / `safe_to_retry` hints, and an `after_success` routing pointer. An
  agent can plan a fixture day end-to-end from the manifest alone —
  proven by `safety/tests/test_daily_auto_manifest_fixture.py` (W35).
- **`hai planned-session-types`** read-only command surfaces the
  canonical vocabulary for `--planned-session-type` so agents can
  discover the recognised tokens without README lookup (W33).
- **`hai capabilities --json`** alias accepted (Codex r3 must-fix:
  was previously argparse error 2 even though docs cited it).
- **`hai state migrate`** now refuses on a DB with gaps in the
  applied migration set (W23). New
  `apply_pending_migrations(..., strict=True)` +
  `SchemaVersionGapError` for library callers.
- **Cold-start policy matrix** documented at
  `reporting/docs/cold_start_policy_matrix.md` (W24) with a test
  pinning the per-domain decisions.
- **`runtime_event_log.context_json`** carries the daily
  proposal-gate outcome so future telemetry surfaces can query
  durable state (W21 prerequisite for W28).

### Changed

- **`hai intake nutrition`** now requires `--replace` to overwrite
  an existing same-day row (W34). Same-day silent supersede was a
  data-integrity footgun for agents treating the command as a
  per-meal logger.
- **`hai daily` capabilities annotation** correctly lists
  `incomplete` as a possible `overall_status` (Codex r3 must-fix).
- **`record_review_outcome`** validates the constructed payload
  before the JSONL append — defence-in-depth so direct Python
  callers can't bypass the v0.1.6 W12 validator (Codex r3 P1).
- **`daily-plan-synthesis` skill** `allowed-tools` broadened from
  flag-constrained patterns to `Bash(hai synthesize *)` (W25 +
  Codex r2 W16). The flag-constrained patterns may have silently
  blocked the skill's own examples under Claude Code's permission
  matcher; broadening + a prose invariant is the safer fix.
- **Source-default semantics** sweep across `hai daily` parser
  help, `intent-router` skill, `agent_integration.md`, and the
  generated capabilities manifest (W32). All now describe the
  v0.1.6+ resolution chain consistently.
- **README cheat sheet** rewritten to reflect every v0.1.6 +
  v0.1.7 surface change.

### Fixed

- **`hai propose` race-path regression** (W26): when
  `project_proposal` raises `ProposalReplaceRequired` past the
  pre-flight canonical-leaf check, the handler returns
  `USER_INPUT` with a clear "JSONL durable, run --replace or
  reproject" stderr instead of silently logging success.
- **Stale comments** in projector.py + expert-explainer skill +
  intent-router rewritten (Codex r3 nits).

### Skill ↔ CLI drift validator

- Extended to inspect `allowed-tools` frontmatter for
  order-sensitive permission patterns that may block their own
  skill-body examples (W25 / Codex r2 W16).

---

## [0.1.6] — 2026-04-25

### Major: post-audit-cycle release

13 workstreams shipped against the consolidated punch list from
three audit rounds (Codex r1 stale-branch + internal
cross-validation + Codex r2 on the correct branch + Codex r3
implementation review):

- **W11** — `_load_json_arg` helper + `main()` exception guard. No
  CLI handler can produce an uncaught Python traceback.
- **W12** — Review-outcome validation: `core/writeback/outcome.py`
  + `validate_review_outcome_dict`. Strict-bool
  `followed_recommendation` enforcement closes the JSONL/SQLite
  truth-fork bug.
- **W10 + W4** — `hai daily` proposal-completeness gate. Three
  statuses (`awaiting_proposals` / `incomplete` / `complete`).
- **W2** — `hai intake gaps` refuses without `--evidence-json`,
  emits `"computed": true` on OK path.
- **W7** — `core/paths.py` — `--base-dir` is now optional
  everywhere; defaults to `$HAI_BASE_DIR` or `~/.health_agent/`.
- **W3 + W18** — `scripts/check_skill_cli_drift.py` validator + CI
  gate. Fixed intent-router + reporting + expert-explainer drift.
- **W1** — `ReprojectOrphansError` + `--cascade-synthesis` flag.
- **W13** — `hai synthesize --bundle-only` refuses when
  `proposal_log` is empty.
- **W15** — `cmd_propose` does its own projection inline.
  `ProposalReplaceRequired` is fatal `USER_INPUT`; other failures
  fatal `INTERNAL`.
- **W17** — `hai research topics` + `hai research search`. Removed
  `Bash(python3 -c *)` from `expert-explainer`.
- **W19** — Reproject contract: "deterministic modulo projection
  timestamps."
- **W20** — `applied_schema_versions` + `detect_schema_version_gaps`;
  `hai doctor` warns on gaps below head.
- **W5** — `intervals_icu` is the implicit default when configured.
- **W9** — README rewrite: "Where your data lives," "How `hai daily`
  actually completes," "Calibration timeline."

Test count: 1844 → 1921 (+77 new tests). Zero locked broken
behaviours remain. v0.1.7 lifts the count to 1943.

---

## [0.1.5] — 2026-04-24

Supersedes the earlier `0.1.4` that shipped to PyPI from commit
`81997aa` before this work landed. PyPI release versions are immutable
(can't overwrite or unpublish cleanly), so the v0.1.4 planning scope
(safety closure + activity pull + proposal recovery + privacy
hardening) ships to users as `0.1.5`. Internal planning documents
retain the `v0_1_4` path for historical continuity; public package
version is `0.1.5`.

The first release where the project's stated success criteria survive
an end-to-end audit. Closes the safety, recovery, privacy, and
wearable-data-reaches-agent gaps that the earlier `0.1.4` implicitly
assumed.

Full detail: [`reporting/plans/v0_1_4/release_notes.md`](reporting/plans/v0_1_4/release_notes.md).

### Added

- **Activity pull pipeline** — intervals.icu `/activities` endpoint wired through pull → clean → snapshot. New `running_activity` table (migration 017), `IntervalsIcuActivity` typed dataclass, structural signals (`z4_plus_seconds_today`, `z4_plus_seconds_7d`, `last_hard_session_days_ago`, `today_interval_summary`, `activity_count_14d`) for the running classifier.
- **Intake-gaps surface** — new `core/intake/gaps.py` + `hai intake gaps` CLI + `hai daily` `gaps` stage. Agent-driven session-start protocol in `merge-human-inputs` skill: read gaps, compose ONE consolidated question, route the answer.
- **`hai today`** — first-class non-agent-mediated user surface (renders the canonical plan in markdown / plain / json).
- **`hai propose --replace`** — explicit revision of the canonical leaf per D1 re-author semantics.
- **`hai synthesize --supersede`** — keeps prior plan, writes new at `<canonical_id>_v<N>`.
- **`hai explain --operator`** — canonical operator-report flag.
- **Privacy hardening** — `core/privacy.py` enforces 0o700 directories + 0o600 files on POSIX across DB, JSONL audit logs, intake roots. `reporting/docs/privacy.md` covers what's stored / where / inspect / export / delete / migrate.
- **D1–D4 design docs** — re-author semantics, intake write paths, user-facing narration, cold-start coverage.
- **Five new e2e test scenarios** — re-author journey, first-run user, credential lifecycle, multi-day review, running activity journey.
- **Snapshot golden tests** — five `hai today --format plain` goldens (green, mixed, no-plan, cold-start, superseded).
- **Cold-start mode** — 14-day per-domain detection; running + strength + stress get coverage relaxation when intent is declared; nutrition stays strict.
- **`hai stats`** — credential-aware sync freshness; `stale_credentials` status when latest sync's source is now uncredentialed.
- **`hai capabilities` `flags[]`** — every argparse flag round-trips into the manifest; `output_schema` + `preconditions` opt-ins on five high-traffic commands.

### Changed

- **Synthesis safety closure** — `run_synthesis` now validates every final recommendation against `core/validate.py` before any partial commit. Per-domain `ALLOWED_ACTIONS_BY_DOMAIN` + `SCHEMA_VERSION_BY_DOMAIN` dispatch. Banned-token sweep covers `rationale` + `action_detail` + `uncertainty` + `follow_up.review_question`. Defensive guard rejects multiple active proposals per chain key. **Closes the safety regression introduced when D2 retired `hai writeback`.**
- **`hai state reproject`** — replays per-domain proposal JSONLs into `proposal_log`, preserving D1 revision chains in JSONL append order. Counts surface as `proposals` and `proposals_skipped_invalid`.
- **`hai pull --source intervals_icu`** — also calls `/activities`; daily-rollup intensity minutes derived from HR zone times.
- **`hai clean`** — aggregates today's activities into `accepted_running_state_daily` so the existing classifier sees real numbers.
- **Recovery-readiness skill** — rewritten to use `hai propose` (D2 contract); aligned with the other five domain skills.
- **README** — restructured with "Reading your plan" + "Recording your day" sections.

### Removed

- **`hai writeback`** — retired. `hai propose` + `hai synthesize` is the canonical commit path. `core/writeback/recommendation.py` deleted; `writeback-protocol` skill renamed to `review-protocol`.
- **`hai classify` / `hai policy`** — debug CLIs deleted per ADR. Use `hai state snapshot --evidence-json <path>`.

### Fixed

- Defer review questions are now per-domain (sleep no longer asks "Did today's session feel appropriate for your recovery?").
- `hai daily` no longer crashes on duplicate same-domain proposals (pre-flight rejection per D1; defensive guard in synthesis).
- Review outcomes against superseded plans auto-re-link to the canonical leaf instead of orphaning.
- Migration 015 backfill applies cleanly to pre-013 DBs.
- `hai capabilities --markdown` regenerated via in-process `cli.main` (not pipx) to avoid stale-install drift.
- Intake fail-soft messages reference `hai state reproject` correctly.

### Security / Privacy

- DB + WAL/SHM/journal siblings locked to 0o600 on POSIX.
- Every JSONL audit log + base directory locked to 0o600 / 0o700 on POSIX after each write.
- Packaged Garmin CSV fixture documented as synthetic; PII regression test scans for emails, phones, GPS, device serials, identity columns.
- `reporting/docs/privacy.md` covers what's stored / where / how to inspect / export / delete / migrate.

### Migrations applied (forward-only)

- 013 — `proposal_log` revision columns
- 014 — `daily_plan.superseded_by_plan_id` forward-link
- 015 — `manual_readiness_raw` table
- 016 — `review_outcome` re-link columns
- 017 — `running_activity` table

Schema head: 16 → 17.

### Test-suite delta

1,489 (v0.1.2) → 1,710 (v0.1.4 mid-development) → **1,824** (v0.1.4 shipping). 0 failing, 4 deliberately skipped (Windows-only privacy tests on POSIX).

---

## [0.1.3.dev0] — 2026-04-23

Bump from v0.1.2; never released. Superseded by v0.1.4.

## [0.1.2] — pre-2026-04-24

Hidden `--with-auth` prompt fix; backfill loop replaced with single pull.

## [0.1.1] — pre-2026-04-24

Phase A onboarding UX + local telemetry.

## [0.1.0] — pre-2026-04-24

Initial release.

[0.1.8]: https://pypi.org/project/health-agent-infra/0.1.8/
[0.1.7]: https://pypi.org/project/health-agent-infra/0.1.7/
[0.1.6]: https://pypi.org/project/health-agent-infra/0.1.6/
[0.1.5]: https://pypi.org/project/health-agent-infra/0.1.5/
[0.1.4]: https://pypi.org/project/health-agent-infra/0.1.4/
[0.1.3.dev0]: https://pypi.org/project/health-agent-infra/0.1.3.dev0/
[0.1.2]: https://pypi.org/project/health-agent-infra/0.1.2/
[0.1.1]: https://pypi.org/project/health-agent-infra/0.1.1/
[0.1.0]: https://pypi.org/project/health-agent-infra/0.1.0/
