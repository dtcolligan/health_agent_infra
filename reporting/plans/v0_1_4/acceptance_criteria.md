# v0.1.4 acceptance criteria

Status tracking for the 18 items that must all be complete before v0.1.4 ships.
Update this doc as work lands.

Legend:
- `[ ]` not started
- `[.]` in progress
- `[x]` complete
- `[blocked: <reason>]` cannot start until a named dependency is met

---

## Design docs (Phase 0)

- [x] D1 — Re-author semantics (revise, not append). Ratified 2026-04-23.
- [x] D2 — Intake write-path contract. Ratified 2026-04-23.
- [x] D3 — User-facing narration surface. Ratified 2026-04-23.
- [x] D4 — Cold-start coverage policy. Ratified 2026-04-23.

Code in workstreams A, B, D does not land until the corresponding D-doc is ratified.

---

## Core-thesis unblock: wearable → running-domain structural data (added 2026-04-24)

- [x] **#16 Running activity pull from intervals.icu `/activities` endpoint.** The adapter previously only hit `/wellness.json` (daily rollups, no per-session detail). Fix: new `IntervalsIcuActivity` typed dataclass, new `fetch_activities_range` on `HttpIntervalsIcuClient`, new migration 017 creating `running_activity` (PK on intervals.icu id, upsert on re-pull). `cmd_clean` aggregates today's activities via `aggregate_activities_to_daily_rollup` so `accepted_running_state_daily.total_distance_m` / `moderate_intensity_min` / `vigorous_intensity_min` populate from HR zone times instead of carrying nulls. Snapshot's `running` block gains `activities_today` + `activities_history`. `derive_running_signals` carries four new structural signals (`z4_plus_seconds_today` / `z4_plus_seconds_7d` / `last_hard_session_days_ago` / `today_interval_summary`) plus `activity_count_14d` which relaxes the coverage gate from `insufficient` when ≥3 activities land in the window. Verified end-to-end against Dom's live account 2026-04-24: 6 intervals.icu activities across the 14-day window, running block flipped from `coverage=insufficient / forced_action=defer / readiness=unknown` to `coverage=full / forced_action=None / readiness=ready`. **This item was the unblocking condition that slipped v0.1.4 from its "all workstreams done" state back to active development on 2026-04-24.**

---

## Correctness & audit integrity (Workstream A — gated on D1, D2)

- [x] **#1** `project_proposal` re-author: D1 revision model implemented; `hai propose --replace` creates a new revision leaf; old leaf is linked forward. Migrations 013/014/015 landed. E2E tests un-xfailed and passing. Full suite 1533/1533 green. Remaining: D1 §Test coverage items 4 (identical-payload idempotency) and 11 (migration backfill unit tests) still need explicit test coverage beyond the e2e scenario.
- [x] **#2** `hai explain --for-date` returns canonical leaf by default; `--plan-version {first,latest,all}` added. Chain walk via `superseded_by_plan_id`. E2E leaf-resolution test passing.
- [x] **#3** Supersede no longer relinks `proposal_log.daily_plan_id`; `hai explain` reads via `proposal_ids_json`. `run_synthesis` on the supersede path now skips `link_proposal_to_plan` entirely; `_load_proposals_for_plan` in `core/explain/queries.py` joins via the stored `proposal_ids_json` array rather than the FK. New regression test `test_explain_resolves_superseded_plan_proposals_via_json_array`.
- [x] **#4** recovery-readiness SKILL.md rewritten to use `hai propose`; `allowed-tools` updated. Contract tests updated. 99 lines under the 100-line Phase 1 cap.
- [x] **#7** X9 trigger precondition: `evaluate_x9` now reads `snapshot.recovery.evidence.planned_session_type` and returns `[]` when it's null — blocking the pre-v0.1.4 footgun where a first-run user with no intake still got their nutrition nudged because the default proposals were "hard." Three new tests: null-gate, non-hard-text satisfies gate, planned-set-but-drafts-softened stays quiet. Legacy `_snapshot()` helpers in `test_synthesis_policy.py` and `test_synthesis_x2_x9_nutrition.py` updated to default `planned_session_type="hard"` so existing X9 assertions keep their original semantics. Eval scenario `syn_009_x9_phase_b_adjusts_nutrition.json` got the evidence block to match.
- [x] **#8** `hai intake readiness` persists to `manual_readiness_raw` (migration 015) and appends `readiness_manual.jsonl`; `hai pull` auto-reads same-day non-superseded row when no `--manual-readiness-json` / `--use-default-manual-readiness` override passed. Supersede chain resolves via JSONL (DB-absent fail-soft). Reproject rebuilds `manual_readiness_raw` with scope-guard preserving other groups. 11 tests in `safety/tests/test_intake_readiness.py` + un-xfailed e2e scenario. New `project_manual_readiness_raw` + `read_latest_manual_readiness` in state/projector.py; new `ReadinessSubmission` + JSONL helpers under `domains/recovery/readiness_intake.py`; `--base-dir` + `--user-id` + `--db-path` + `--ingest-actor` flags added to the intake parser (D2 §flag-surface unification).
- [x] **#14** Supersede lineage: `--supersede` resolves the canonical leaf at time of synthesis (via `_resolve_canonical_leaf_plan_id` in `core/synthesis.py`) and marks *it* as superseded by the new plan. v1→v2→v3 + another supersede now produces v3.superseded_by=v4, preserving the v1→v2 link. Regression test `test_synthesize_supersede_targets_canonical_leaf_not_chain_head`.
- [x] **#15** Review outcomes re-link to canonical leaf on supersede; refuse-record if no matching-domain rec on leaf. `hai review record` resolves the target recommendation's plan via `recommendation_log.daily_plan_id`, walks `daily_plan.superseded_by_plan_id` to the canonical leaf, finds the matching-domain rec for the same `for_date`, and either re-links (rewrites outcome `recommendation_id` + populates `re_linked_from_recommendation_id` + `re_link_note`, emits stderr note) or refuses (exit `USER_INPUT`, clear stderr, no JSONL/DB write). Migration 016 adds the two nullable audit columns on `review_outcome` + a partial index on the re-link pointer so the WS-E contract test "no outcome points to a superseded rec" is a one-line SQL join. DB-absent → skip resolution with stderr hint; `hai state reproject` picks up the re-link fields from JSONL. Eight unit tests in `safety/tests/test_review_record_relink.py` (resolver passthrough / re-link / refuse / multi-step chain + CLI happy-path / refuse / passthrough / db-absent) plus the step-9 review-record scenario in `safety/tests/e2e/test_reauthor_journey_2026_04_23.py`.
- [x] Migration 013 (proposal revisions) + 014 (plan supersede forward links) + 015 (manual_readiness_raw) + 016 (review_outcome re-link columns) forward-only; backfill tests. D1 test #11 coverage in `safety/tests/test_migration_backfill_013_014.py` — 6 tests: seed a pre-013 DB (schema at v12), insert realistic proposal_log + daily_plan rows in the pre-migration column set, apply 013–016, assert (a) every proposal_log row becomes canonical leaf with revision=1 + forward pointer NULL, (b) daily_plan rows with `synthesis_meta_json.$.superseded_by` get that attribute walked into the new column with `superseded_at = validated_at`, (c) plans without the attribute stay canonical leaves, (d) both new canonical indexes exist, (e) the full stack reaches schema head 16.
- [x] `hai writeback` (legacy recovery-only direct path) removed. Subcommand deleted from `cli.py` (handler `cmd_writeback`, parser `p_wb`, helper `_recommendation_from_dict`); `src/health_agent_infra/core/writeback/recommendation.py` module deleted; `core/writeback/__init__.py` narrowed to proposal-only. The `writeback-protocol` skill renamed to `review-protocol` with scope narrowed to `hai review schedule | record | summary` (re-link on supersede documented inline). Test fixtures migrated: writeback-only tests deleted (3 in `test_recovery_readiness_v1.py`, 2 in `test_state_dual_write.py`); seeder uses migrated to either `project_recommendation` (DB seed for review CLI tests) or a direct `recommendation_log.jsonl` append (reproject tests). Live user-facing docs (`README.md`, `agent_integration.md`, `architecture.md`, `tour.md`, `explainability.md`, `how_to_add_a_domain.md`, `how_to_add_a_pull_adapter.md`, `personal_health_agent_positioning.md`) scrubbed; sibling-skill references updated in `safety/SKILL.md`, `reporting/SKILL.md`, `expert-explainer/SKILL.md`. Contract doc regenerated: zero `hai writeback` mentions. Test 8 in D2.

---

## User surface (Workstream B — gated on D3)

- [x] **#6** `hai today` command ships: reads canonical leaf via `load_bundle_for_date(plan_version='latest')`; renders 6-domain prose in the voice D3 specifies (top-matter + summary + per-domain + footer); `--format markdown|plain|json` (markdown is TTY-default, plain is non-TTY fallback); `--domain` filter narrows to one section; exits USER_INPUT on no-plan with "Run `hai daily` first." stderr hint. New `core/narration/` module (templates + render). 6 tests in `safety/tests/test_cli_today.py` covering green day, mixed day, no-plan, domain filter, json format, and superseded-plan-renders-leaf. E2E `test_hai_today_renders_canonical_plan` un-xfailed.
- [x] **#9 (original)** Per-domain defer review_question templates: each domain resolves its template from `core.narration.templates.DEFER_REVIEW_QUESTION_TEMPLATES` inside `_default_review_question`; the recovery-flavoured generic fallback was removed from `_DEFAULT_REVIEW_QUESTIONS`. Each non-recovery readiness skill (`running`, `sleep`, `strength`, `stress`, `nutrition`) gained a one-line note in its §7 Follow-up pointing at the per-domain template. 14 parametrised tests in `safety/tests/test_defer_review_question_per_domain.py` (one unit + one integration per domain, plus fall-through + unknown-domain guards). Test 8 in D3.
- [x] **#13** README restructured: quickstart includes `hai today`; new "Reading your plan" + "Recording your day" sections cover the full user surface; architecture bullet rewrites "or plain SQL" to prefer `hai today` / `hai explain --operator` (D3 "don't read SQLite directly"). 6 contract tests in `safety/tests/test_readme_structure.py`. Test 10 in D3.
- [x] `hai daily` emits a TTY-aware one-line stderr hint pointing at `hai today --as-of … --user-id …` when stderr `isatty()`; stays silent (byte-stable stderr) when piped. 2 tests in `test_cli_daily.py`. Test 9 in D3.
- [x] `hai explain --operator` flag added as the canonical operator-report trigger; `--text` stays as a deprecated alias with a stderr deprecation hint (removal scheduled for a future release). 3 new tests in `test_cli_explain.py` (operator-matches-text output, deprecation-hint-on-text, no-hint-on-operator).
- [x] `core/narration/voice.py` voice linter module: `lint_narration(text) → list[LintFinding]` checks for (a) medical/diagnostic language via the shared `BANNED_TOKENS` and (b) rule-id leaks (`R\d`, `X\d`, `require_\w+`, `forced_action`, `coverage_*`). 43 tests in `safety/tests/test_narration_voice.py` — 20 clean real-shape snippets, 10 medical-phrase detections, 7 rule-id detections, 1 rendered `hai today` output lint-clean, plus case-insensitivity + whole-word + span + hashability guards. Test 7 in D3.

---

## Agent contract & MCP readiness (Workstream C — no D-gate)

- [x] **#8 (original)** `hai capabilities --json` grows `flags[]` per command: name (primary long form), positional, required, type (including bool for store_true/false), choices (JSON-safe), default (JSON-safe; callables null), help, action (store / store_true / etc.), nargs, aliases. Walker skips `_HelpAction` / `_SubParsersAction` / `_VersionAction`. Contract tests in `safety/tests/test_capabilities_flags_contract.py` — 7 tests including: every flag argparse knows about appears in the manifest (and vice versa) per command, stable flag-entry key set, positional-when-present contract, all-current-flags-are-optional guard, store_true/false report bool type, choices serialise as JSON lists, defaults are JSON-safe.
- [x] `hai capabilities --json` grows `output_schema` per command. `annotate_contract` gained an optional `output_schema=` kwarg (dict keyed by exit-code name, validated against the declared exit codes). Populated on five high-traffic commands: `hai today`, `hai daily`, `hai synthesize`, `hai propose`, `hai review record`. Absent on others — a missing `output_schema` is honest ("no canonical shape declared"), not a bug.
- [x] `hai capabilities --json` grows `preconditions` per command. `annotate_contract` gained an optional `preconditions=` kwarg (list of stable string tokens like `state_db_initialized`, `proposal_log_has_row_for_each_target_domain`, `review_event_exists_for_event_id`). Populated on the same five high-traffic commands.
- [x] `intent-router` skill SKILL.md updated to reference the enriched manifest — `flags[]` goes into the "use the manifest to" checklist; `output_schema` and `preconditions` each get a dedicated bullet describing how the router should consult them before chaining commands.
- [x] `reporting/docs/agent_cli_contract.md` regenerated; preamble now explicitly calls out that per-command structured detail (flags, output_schema, preconditions) lives in the JSON manifest rather than this markdown overview — keeps the human-readable mirror concise while still pointing agents at the complete surface.
- [x] Stretch: MCP server scaffold drafted in `reporting/plans/v0_1_4/mcp_scaffold.md`. Maps the WS-C-enriched manifest onto MCP tool schemas mechanically (flags[] → inputSchema, output_schema → outputSchema, agent_safe=false → tool excluded). Three delivery slices (read-only, write-path, orchestration) + open questions + dependency checklist. Code deferred to v0.1.5 per the plan's explicit non-goal for v0.1.4.

---

## Cold-start & onboarding (Workstream D — gated on D4)

- [x] **#5** `hai stats` cross-references current cred availability. New `credentials_available` field per sync-freshness entry (True / False / None for the CSV non-live source); when the latest successful sync's source is now uncredentialed, `status` downgrades from `ok` to `stale_credentials`. 3 tests in `test_cli_stats.py`.
- [x] **#10 (new)** Running cold-start mode implemented; non-defer possible when recovery is non-red and planned_session_type is present. `core/state/snapshot.py` computes `cold_start` + `history_days` per domain via `_cold_start_flags`; `domains/running/policy.py` grows a `cold_start_context` kwarg with the `_running_cold_start_relax` helper. `RunningPolicyResult` gains `extra_uncertainty`; the snapshot merges it into `classified_state.uncertainty`. 11 tests in `test_running_cold_start_policy.py` + 9 shared detection tests in `test_cold_start_detection.py`. D4 tests #1–#4.
- [x] Strength cold-start mode with explicit session-intent check. Same shape as running; `planned_session_type` substring must contain `strength` (case-insensitive). 14 tests in `test_strength_cold_start_policy.py`. D4 test #5.
- [x] Stress cold-start lighter relaxation — energy self-report alone is enough to lift the defer at capped `low` confidence. 8 tests in `test_stress_cold_start_policy.py`. D4 test #6.
- [x] Nutrition explicit non-relaxation — D4 §Nutrition rejects cold-start relaxation for macros. Regression guard test asserts `evaluate_nutrition_policy` has no `cold_start_context` kwarg; renderer switches to `cold_start_nutrition_defer_hint` ("I'd be making it up") when nutrition defers under cold-start. 4 tests in `test_nutrition_cold_start_non_relaxation.py`. D4 test #7.
- [x] Cold-start graduation at 14 days — covered by `test_cold_start_detection.py::test_exactly_fourteen_days_graduates_from_cold_start`. D4 test #8.
- [x] `hai today` cold-start footer — one line per cold-start domain, rendered after all per-domain sections (never duplicated, never for graduated domains, never for filtered-out domains). `cmd_today` calls `_cold_start_flags` and threads the result through `render_today(cold_start_by_domain=…)`. 8 tests in `test_cold_start_rendering.py`. D4 test #9.
- [x] **#11** `hai classify` / `hai policy` debug CLIs: **deleted** per `reporting/plans/v0_1_4/adr_classify_policy_cli.md`. Their behaviour is subsumed by `hai state snapshot --evidence-json`. README + architecture.md + intent-router allowed-tools updated; contract doc regenerated (37 commands → 36). Test file removed.
- [x] **#10 (original)** `hai pull --help` rewording — `intervals_icu` described honestly as "stable and the best live option today, but scoped to what that service exposes (HRV + RHR + sleep + load; no per-session running granularity yet)" instead of bare "(recommended)".
- [x] **#12** Keychain ACL — new `_print_keychain_acl_hint` in `cli.py` fires a one-line stderr hint after `hai auth garmin` / `hai auth intervals-icu` when the backend is `KeychainKeyring` (macOS), telling the user to click "Always Allow" on the first live pull prompt. README install section gains a dedicated **macOS Keychain note** subsection. Programmatic `access_control` not attempted for v0.1.4 — tracked as v0.1.5+ UX follow-on.
- [ ] Stretch: `hai init --interactive` first-run wizard. Deferred to v0.1.5 — cold-start mode closes the day-one adequacy gap on its own (D4 §Interaction with `hai init --interactive`).

---

## Test coverage & release QA (Workstream E — no D-gate, runs concurrently)

- [x] `safety/tests/e2e/` category exists with `conftest.py` providing the `E2EEnv` fixture (fresh DB + base_dir + in-process `run_hai`).
- [x] E2E scenario 1: 2026-04-23 re-author journey — `safety/tests/e2e/test_reauthor_journey_2026_04_23.py` (landed earlier this session with the D1/D2/D3 work).
- [x] E2E scenario 2: first-run user — `safety/tests/e2e/test_first_run_journey.py`. 2 tests: readiness intake + cold-start snapshot flags; day-one `hai today` shape including cold-start footers + nutrition make-up language.
- [x] E2E scenario 3: mid-day re-author — covered by the 2026-04-23 re-author journey scenario (which explicitly runs intake-readiness → daily → propose-replace → synthesize-supersede → today).
- [x] E2E scenario 4: credential lifecycle — `safety/tests/e2e/test_credential_lifecycle.py`. 2 tests: creds present → seed live sync → stats ok; remove creds → stats downgrades to `stale_credentials`; CSV source is not flagged under credential rotation.
- [x] E2E scenario 5: multi-day review — `safety/tests/e2e/test_multi_day_review.py`. 2 tests: day 1 plan + review event → day 2 outcome → day 2 snapshot surfaces outcome in `reviews.recent`; `hai explain` on day 1 includes the outcome.
- [x] `safety/tests/contract/` category exists with `conftest.py` providing `ContractEnv` + a reusable `seed_six_domain_daily` helper. 8 audit-chain-integrity tests in `test_audit_chain_integrity.py`: proposal_ids_json resolves (fresh + supersede); recommendation_log.daily_plan_id resolves; review_outcome never orphans on superseded plan; proposal_log + daily_plan chains have exactly one leaf per chain key and no cycles.
- [ ] Contract: every intake writes to declared table, classifier reads declared table. **Deferred to v0.1.5** — this assertion set sprawls across domains and would duplicate existing per-domain classify/intake unit coverage without a proportional rigor gain. Tracked in the v0.1.5 roadmap.
- [x] Contract: every skill's allowed-tools resolves in capabilities manifest — existing coverage in `safety/tests/test_docs_integrity.py`.
- [x] Contract: every rec in review_event → non-superseded rec OR re-linked — covered by `test_review_outcome_never_orphans_on_superseded_plan` in the new contract suite.
- [x] Contract: every proposal_ids_json entry resolves in proposal_log — covered by `test_every_proposal_ids_json_entry_resolves_in_proposal_log`.
- [x] `safety/tests/snapshot/` category exists with `golden/` fixture directory. Snapshot comparator seeds fixtures on first run and fails with a diff on drift.
- [x] Snapshot tests for `hai today` — 5 scenarios in `test_hai_today_snapshots.py` (green, mixed, no-plan, cold-start, superseded). `hai explain --operator` snapshots deferred to v0.1.5 — the operator surface's drift is less user-visible than `hai today`'s; the same harness will support it when a v0.1.5 consumer asks for it.
- [x] Documentation integrity CI check — already live in `safety/tests/test_docs_integrity.py`; parses every SKILL.md + reporting/docs/*.md and asserts every `hai <cmd>` reference resolves in the manifest.
- [ ] README worked-example integrity: every command in the README quickstart is runnable in sequence from a fresh DB; CI runs the walkthrough. **Deferred to v0.1.5** — the dogfood-day ritual (Phase 1 of release_qa.md) covers this manually for v0.1.4; CI automation is a v0.1.5 hardening.
- [x] Release QA ritual documented in `reporting/plans/v0_1_4/release_qa.md` — 4-phase protocol (tree verify → fresh-profile dogfood → spot-check regression catches → PyPI push) + 8-item release-criteria checklist.

---

## Release criteria (all must be green before PyPI)

- [ ] All 18 numbered items above complete.
- [ ] All four D-docs merged.
- [ ] Each workstream's artifact list complete.
- [ ] CI green on main with all new test categories.
- [ ] Dogfood day completed against TestPyPI: fresh user profile, README walkthrough reproducible end-to-end, zero new P0 issues.
- [ ] Spot-check regression catch: revert each fix locally, confirm CI fails, confirm revert blocks merge.
- [ ] `hai doctor` reports `overall_status=ok` on a fresh install when all expected sources are credentialed.
- [ ] README reader test: a reader running `hai init` + `hai daily` + `hai today` on v0.1.4 with no agent mediation gets a useful 6-domain plan and understands what they're reading.

Any failure → v0.1.4 stays on `0.1.3.devN` and iterates.
