# Codex Implementation Review — v0.1.6 Response

## Step 0 confirmation

Verified before review:

- `pwd`: `/Users/domcolligan/health_agent_infra`
- `git branch --show-current`: `v0.1.4-release`
- `git log --oneline -1`: `ff77aff v0.1.5: sync release QA + handoff docs to v0.1.5 reality`
- `git status --short | head -20`: 14 modified files plus new untracked v0.1.6 files under `reporting/plans/v0_1_6/`, `safety/tests/`, `scripts/`, and `src/`.

I ignored `/Users/domcolligan/Documents/health_agent_infra/`.

Verification run:

- Targeted v0.1.6 workstream suite: `132 passed in 4.19s` with `HAI_STATE_DB=/tmp/hai-review-nonexistent-state.db`.
- Full suite outside the sandbox: `1928 passed, 2 skipped in 44.65s`.
- `git diff --check`: clean.
- `hai capabilities --markdown` matches `reporting/docs/agent_cli_contract.md` byte-for-byte, but some annotations that feed the generated doc are stale; see Documentation / capabilities-manifest correctness.

## Per-workstream verification (Job A)

### W1. Reproject FK orphan guard

Status: VERIFIED

Evidence: `reproject_from_jsonl` now checks synthesis-side row counts before destructive recommendation/proposal deletes, raises `ReprojectOrphansError` unless `cascade_synthesis=True`, and deletes `planned_recommendation` / `x_rule_firing` first on cascade (`src/health_agent_infra/core/state/projector.py:1242-1290`). The CLI exposes `--cascade-synthesis` with the right refusal/cascade language (`src/health_agent_infra/cli.py:5615-5622`). Regression tests cover refusal, rollback, cascade, and empty-synthesis success (`safety/tests/test_reproject_proposal_recovery.py:411-480`).

Notes: Behavior is fixed. One stale internal comment still says `proposal_log` has no inbound FK from synthesis-side tables (`src/health_agent_infra/core/state/projector.py:1325-1340`); fix the comment, not the code path.

### W2. Intake gaps computed honesty

Status: VERIFIED

Evidence: `cmd_intake_gaps` now refuses when `--evidence-json` is absent (`src/health_agent_infra/cli.py:2969-2980`) and emits `"computed": True` on the OK path (`src/health_agent_infra/cli.py:3000-3007`). Parser help describes the required-in-practice evidence bundle (`src/health_agent_infra/cli.py:5479-5486`). Tests cover both computed output and refusal (`safety/tests/test_intake_gaps.py:358-361`, `safety/tests/test_intake_gaps.py:374-400`).

Notes: No ship concern.

### W3+W18. Skill/CLI drift validator and reporting drift

Status: UNDER-DELIVERED

Evidence: The validator checks fenced code blocks for `hai` invocations, unknown flags, and choice-hint mismatches (`scripts/check_skill_cli_drift.py:73-182`), and CI wraps it (`safety/tests/test_skill_cli_drift.py:30-39`). The known `intent-router` review-record block is now aligned with `--outcome-json`, strict booleans, and real override flags (`src/health_agent_infra/skills/intent-router/SKILL.md:139-175`). The reporting skill no longer documents `--since`; it uses `hai review summary --user-id <id> [--domain <d>] [--base-dir <root>]` (`src/health_agent_infra/skills/reporting/SKILL.md:47-50`).

Notes: The validator explicitly does not inspect inline/prose references (`safety/tests/test_skill_cli_drift.py:14-17`) and it does not validate `allowed-tools` patterns (`scripts/check_skill_cli_drift.py:143-182`). That leaves real drift uncaught: `intent-router` still tells agents to consult `hai capabilities --json` (`src/health_agent_infra/skills/intent-router/SKILL.md:21-24`, `src/health_agent_infra/skills/intent-router/SKILL.md:281-282`), while the parser only supports `--markdown` on `hai capabilities` (`src/health_agent_infra/cli.py:6009-6018`).

### W4. Daily honesty/docs

Status: UNDER-DELIVERED

Evidence: README's new daily section correctly documents `awaiting_proposals`, `incomplete`, and `complete` (`README.md:95-123`). But the generated capabilities annotation still describes `hai daily` as `pull -> clean -> reproject -> propose -> synthesize -> daily_plan in one invocation` (`src/health_agent_infra/cli.py:5709-5712`), and its output schema omits the new `"incomplete"` status (`src/health_agent_infra/cli.py:5724-5730`) even though code returns it (`src/health_agent_infra/cli.py:3723-3735`, `src/health_agent_infra/cli.py:3749-3756`). The generated contract therefore repeats the stale one-invocation description (`reporting/docs/agent_cli_contract.md:69`). `intent-router` also still says `hai daily` runs `pull -> clean -> reproject -> propose -> synthesize` (`src/health_agent_infra/skills/intent-router/SKILL.md:101-107`).

Notes: This is agent-facing contract drift. Fix before tag.

### W5. Intervals.icu default source

Status: OVERSTATED

Evidence: `_resolve_pull_source` now defaults to `intervals_icu` only when credentials are configured, otherwise `csv` (`src/health_agent_infra/cli.py:515-547`). Parser help says the same for `--source` (`src/health_agent_infra/cli.py:4587-4598`). Tests pin explicit CSV and no-auth fallback (`safety/tests/test_cli_pull_live_and_auth.py:217-262`).

Notes: The original plan also said to soften `--live` to prefer Intervals.icu unless `--source garmin_live` is explicit (`reporting/plans/v0_1_6/PLAN.md:212-224`). The implementation keeps `--live` equivalent to `garmin_live` (`src/health_agent_infra/cli.py:537-542`) and documents that behavior (`src/health_agent_infra/cli.py:4581-4586`). That is acceptable if intentional, but the workstream claim should not imply `--live` was softened.

### W7. Default base-dir

Status: VERIFIED

Evidence: `resolve_base_dir` implements explicit arg > `$HAI_BASE_DIR` > `~/.health_agent` (`src/health_agent_infra/core/paths.py:25-44`). Agent-facing base-dir parser declarations are now optional (`src/health_agent_infra/cli.py:4734`, `src/health_agent_infra/cli.py:5114`, `src/health_agent_infra/cli.py:5135`, `src/health_agent_infra/cli.py:5214`, `src/health_agent_infra/cli.py:5274`, `src/health_agent_infra/cli.py:5348`, `src/health_agent_infra/cli.py:5380`, `src/health_agent_infra/cli.py:5410`, `src/health_agent_infra/cli.py:5441`, `src/health_agent_infra/cli.py:5602`, `src/health_agent_infra/cli.py:5649`). Tests cover resolver order and two CLI smoke paths (`safety/tests/test_default_base_dir.py:25-51`, `safety/tests/test_default_base_dir.py:58-91`).

Notes: No ship concern.

### W9. README rewrite

Status: UNDER-DELIVERED

Evidence: The new README sections landed (`README.md:80-123`), and the daily section is materially better. But the README's later CLI cheat sheet still says `hai capabilities --json` (`README.md:431-434`), `hai daily` is the whole loop and includes `propose` inline (`README.md:355-356`), `hai pull [--live]` is "Garmin CSV / live pull" without the Intervals.icu default (`README.md:343-346`), and `hai review schedule | record | summary [--domain <d>]` still implies `--domain` applies to `record` (`README.md:360-361`) even though `review record` only has `--outcome-json`, `--base-dir`, `--db-path`, and enrichment flags (`src/health_agent_infra/cli.py:5133-5165`).

Notes: This is not cosmetic; it contradicts the exact agent-facing fixes v0.1.6 is shipping.

### W10. Daily proposal-completeness gate

Status: VERIFIED

Evidence: `cmd_daily` parses expected domains, computes missing expected domains, returns `awaiting_proposals` / `incomplete` / `complete`, and gates synthesis on complete only (`src/health_agent_infra/cli.py:3629-3635`, `src/health_agent_infra/cli.py:3710-3756`). The flipped test now blocks `--domains recovery,sleep` when only recovery/running proposals exist (`safety/tests/test_cli_daily.py:272-318`), and the happy-path companion runs synthesis when every expected domain is present (`safety/tests/test_cli_daily.py:320-348`).

Notes: Code behavior is fixed. Contract annotations/docs still need W4/W9 cleanup.

### W11. JSON-arg helper and main guard

Status: VERIFIED

Evidence: `_load_json_arg` handles missing paths, unreadable paths, and malformed JSON as `USER_INPUT` (`src/health_agent_infra/cli.py:112-154`). `cmd_pull`, `cmd_clean`, `cmd_propose`, `cmd_review_schedule`, and `cmd_review_record` are migrated (`src/health_agent_infra/cli.py:218-225`, `src/health_agent_infra/cli.py:572-578`, `src/health_agent_infra/cli.py:1011-1017`, `src/health_agent_infra/cli.py:1829-1835`, `src/health_agent_infra/cli.py:1870-1876`). `main()` passes `SystemExit`, maps `KeyboardInterrupt` to `USER_INPUT`, and maps unexpected exceptions to `INTERNAL` without a default traceback (`src/health_agent_infra/cli.py:6038-6071`). Tests cover bad path, malformed JSON, helper behavior, and main guard behavior (`safety/tests/test_cli_json_arg_handling.py:56-145`, `safety/tests/test_cli_json_arg_handling.py:152-217`, `safety/tests/test_cli_json_arg_handling.py:225-271`).

Notes: Full suite passes outside the sandbox. Inside the sandbox, default DB/keychain/loopback limitations produced false failures; those disappeared outside sandbox.

### W12. Review-outcome validation

Status: UNDER-DELIVERED

Evidence: The new validator enforces strict booleans and enrichment-field types (`src/health_agent_infra/core/writeback/outcome.py:83-211`), and `cmd_review_record` rejects invalid payloads before writing (`src/health_agent_infra/cli.py:1870-1884`). Tests cover strict-bool rejection and no JSONL write from the CLI (`safety/tests/test_review_outcome_validation.py:68-85`, `safety/tests/test_review_outcome_validation.py:202-231`).

Notes: The round-2 punch list explicitly asked to enforce in `record_review_outcome` too. That did not land: `record_review_outcome` still constructs `ReviewOutcome` and appends JSONL with no call to `validate_review_outcome_dict` (`src/health_agent_infra/core/review/outcomes.py:153-176`). CLI users are protected; direct Python callers can still recreate the JSONL/SQLite truth fork.

### W13. Bundle-only no-proposals refusal

Status: VERIFIED

Evidence: `cmd_synthesize --bundle-only` now rejects combinations with `--drafts-json` / `--supersede`, requires at least one proposal for `(for_date, user_id)`, and returns `USER_INPUT` when none exist (`src/health_agent_infra/cli.py:1249-1294`). The regression test covers the empty-proposal refusal (`safety/tests/test_synthesize_bundle_only_gate.py:24-40`).

Notes: No ship concern.

### W15. cmd_propose projection contract

Status: VERIFIED

Evidence: `cmd_propose` no longer uses `_dual_write_project`; it projects inline and distinguishes DB absent, `ProposalReplaceRequired`, and unexpected projection errors (`src/health_agent_infra/cli.py:1057-1112`). Successful stdout includes `db_projection_status` and DB-landed proposal metadata (`src/health_agent_infra/cli.py:1128-1147`). Tests cover OK status, DB-absent status, and unexpected projection failure returning `INTERNAL` instead of silent success (`safety/tests/test_propose_dual_write_contract.py:57-80`, `safety/tests/test_propose_dual_write_contract.py:83-107`, `safety/tests/test_propose_dual_write_contract.py:110-149`).

Notes: The rare `ProposalReplaceRequired` race path is not directly tested in the new file, but the normal duplicate path is preflighted before JSONL append (`src/health_agent_infra/cli.py:1030-1055`).

### W17. Bounded research CLI

Status: VERIFIED

Evidence: `hai research topics` emits the allowlist and `hai research search --topic <t>` builds a `RetrievalQuery(topic=args.topic)` only (`src/health_agent_infra/cli.py:4501-4538`). Parser annotations mark both commands read-only and agent-safe (`src/health_agent_infra/cli.py:5965-6007`). Retrieval refuses user-context flags in core and imports no network client (`src/health_agent_infra/core/research/retrieval.py:15-18`, `src/health_agent_infra/core/research/retrieval.py:81-132`). `expert-explainer` removed `Bash(python3 -c *)` and grants `hai research` instead (`src/health_agent_infra/skills/expert-explainer/SKILL.md:1-5`). Tests cover command output, capabilities presence, no user-context flags, and no `python3 -c` permission (`safety/tests/test_research_cli.py:24-99`, `safety/tests/test_research_cli.py:102-118`).

Notes: One invariant sentence in the skill is stale: it still says the only allowed `hai` subcommands are `hai explain` and `hai state snapshot` (`src/health_agent_infra/skills/expert-explainer/SKILL.md:125-131`), even though the frontmatter now also grants `hai research`.

### W19. Reproject determinism wording

Status: VERIFIED

Evidence: The reproject contract annotation now says "deterministic modulo projection timestamps" and names `projected_at` / `corrected_at` as wall-clock columns (`src/health_agent_infra/cli.py:5631-5636`). The generated contract carries the updated wording because `agent_cli_contract.md` matches `hai capabilities --markdown`.

Notes: No ship concern.

### W20. Schema-version gap detection

Status: UNDER-DELIVERED

Evidence: `applied_schema_versions` and `detect_schema_version_gaps` exist (`src/health_agent_infra/core/state/store.py:86-119`), and `doctor` surfaces gaps before the pending-migrations check (`src/health_agent_infra/core/doctor/checks.py:102-152`). Tests cover clean init, one gap, multiple gaps, empty table, and doctor warning (`safety/tests/test_schema_version_gap_detection.py:44-107`).

Notes: The final consolidated plan asked for contiguous-set checking in `migrate` and `doctor` (`reporting/plans/v0_1_6/PLAN.md:441-442`, `reporting/plans/v0_1_6/PLAN.md:464`). `cmd_state_migrate` still calls `apply_pending_migrations` directly and reports OK (`src/health_agent_infra/cli.py:3248-3283`), while `apply_pending_migrations` still computes `current = current_schema_version(conn)` and skips every migration `version <= current` (`src/health_agent_infra/core/state/store.py:210-243`). A gappy DB is warned by doctor but not refused or repaired by migrate.

## New bugs introduced (Job B)

### P1. `hai daily` manifest schema omits the new `incomplete` status

Severity: P1

Evidence: Code returns `overall_status = gate_status`, including `"incomplete"` (`src/health_agent_infra/cli.py:3723-3756`). The capabilities output schema lists only `"complete"`, `"awaiting_proposals"`, and `"failed"` (`src/health_agent_infra/cli.py:5724-5726`). The generated contract repeats the stale daily description (`reporting/docs/agent_cli_contract.md:69`).

Recommended fix: Update the `annotate_contract` block for `hai daily`: description should say proposal-gate seam, `overall_status_values` must include `"incomplete"`, and notes should mention both `awaiting_proposals` and `incomplete`.

Effort: S

Risk if shipped: Agents that trust `hai capabilities` do not know about a status the command now emits.

### P1. Agent docs still require `hai capabilities --json`, but the CLI has no `--json`

Severity: P1

Evidence: README says agents read metadata via `hai capabilities --json` (`README.md:20-23`, `README.md:290-293`, `README.md:431-434`). `intent-router` says the same in its description and invariants (`src/health_agent_infra/skills/intent-router/SKILL.md:1-4`, `src/health_agent_infra/skills/intent-router/SKILL.md:21-24`, `src/health_agent_infra/skills/intent-router/SKILL.md:281-282`). The generated contract preamble says regenerate by invoking `hai capabilities --json` (`reporting/docs/agent_cli_contract.md:3-8`). The parser only defines `--markdown`; JSON is the default, but `--json` is not accepted (`src/health_agent_infra/cli.py:6009-6018`).

Recommended fix: Add `--json` as a no-op alias for the default JSON output, or update every doc/skill mention to `hai capabilities`. The alias is safer and backward-compatible.

Effort: S

Risk if shipped: The authoritative router skill tells agents to run a command that exits argparse error 2.

### P2. Pull/stat tests are environment-sensitive to real default DB/keychain when not isolated

Severity: P2

Evidence: `_open_sync_row` skips when the DB path does not exist, but if the default DB exists and `open_connection` raises before `begin_sync`, that `sqlite3.OperationalError` is not caught (`src/health_agent_infra/cli.py:311-341`). `cmd_stats` always queries the real credential store unless tests monkeypatch it (`src/health_agent_infra/cli.py:4312-4326`); several stats tests only pass a temp DB and do not inject a fake credential store (`safety/tests/test_cli_stats.py:63-88`, `safety/tests/test_cli_stats.py:259-304`).

Recommended fix: Make sync-row opening catch `sqlite3.Error` around `open_connection`, and make stats tests inject a fake credential store globally or set a test-safe keyring backend.

Effort: S

Risk if shipped: CI is probably fine, but local test runs can fail based on the operator's real default DB/keychain state. This was observable in the sandbox; the full suite passed outside sandbox.

## Things still missing (Job C)

### P0. Release metadata still says 0.1.5

Severity: P0

Evidence: `pyproject.toml` still declares `version = "0.1.5"` (`pyproject.toml:5-8`), and `health_agent_infra.__version__` is derived from installed distribution metadata (`src/health_agent_infra/__init__.py:12-21`). The generated contract currently reports `hai 0.1.5` (`reporting/docs/agent_cli_contract.md:58`).

Recommended fix: Bump package metadata to `0.1.6`, reinstall/regenerate the contract doc if its version field changes, and verify `hai --version` reports `0.1.6` before tagging.

Effort: S

Risk if shipped: A `v0.1.6` tag would install/report as `0.1.5`.

### P1. Review-outcome validation is not defense-in-depth

Severity: P1

Evidence: CLI validation happens before write (`src/health_agent_infra/cli.py:1870-1884`), but the core writer still accepts raw values and appends JSONL without validation (`src/health_agent_infra/core/review/outcomes.py:153-176`).

Recommended fix: Call `validate_review_outcome_dict(outcome.to_dict())` or validate the input kwargs inside `record_review_outcome` before opening/appending the JSONL. Add a direct unit test that `record_review_outcome(... followed_recommendation="definitely")` raises and writes nothing.

Effort: S

Risk if shipped: Direct Python integrations can still recreate the truth fork W12 was meant to close.

### P1. Agent-integration docs still describe removed review-record and incomplete determinism-boundary behavior

Severity: P1

Evidence: `agent_integration.md` still says next-morning outcome logging uses `hai review record --domain <d>` (`reporting/docs/agent_integration.md:73-76`), but `review record` has no `--domain` flag and requires `--outcome-json` (`src/health_agent_infra/cli.py:5133-5165`). Its determinism-boundary section still names only `hai propose` and `hai synthesize` (`reporting/docs/agent_integration.md:105-128`), while W12 made `hai review record` the third validation boundary (`src/health_agent_infra/core/writeback/outcome.py:1-17`).

Recommended fix: Update `agent_integration.md` before tag because README links to it as the skill-driven completion doc (`README.md:124-125`).

Effort: S

Risk if shipped: A fresh agent following the linked integration doc will use the old review-record protocol.

### P2. Schema-gap check is doctor-only, not migrate-safe

Severity: P2

Evidence: See W20. `cmd_state_migrate` does not check `detect_schema_version_gaps` (`src/health_agent_infra/cli.py:3248-3283`), and migration application still uses max-version skip logic (`src/health_agent_infra/core/state/store.py:210-243`).

Recommended fix: Before applying pending migrations, refuse with `USER_INPUT` when `detect_schema_version_gaps(conn)` is non-empty.

Effort: S

Risk if shipped: Operators running `hai state migrate` on a gappy DB get an OK-looking no-op instead of the same warning doctor provides.

## Deferred items — agree or disagree

- W6 nutrition supersede warning: agree with deferral if README's daily-total warning is considered sufficient for v0.1.6. The code warning remains deferred (`reporting/plans/v0_1_6/PLAN.md:405-406`), and nutrition intake still writes a superseding JSONL row without requiring confirmation (`src/health_agent_infra/cli.py:2460-2506`). Not a tag blocker.
- W8 planned-session-type CLI helper: agree with deferral. README documents the vocabulary in this release per the implementation log (`reporting/plans/v0_1_6/PLAN.md:395-400`), while the optional helper is explicitly deferred (`reporting/plans/v0_1_6/PLAN.md:405-407`). Not a tag blocker.
- W14 deeper cold-start matrix: agree with deferral. The README now documents the high-level calibration story (`README.md:95-123` covers the daily gate; the implementation log says cold-start asymmetry was folded into README at `reporting/plans/v0_1_6/PLAN.md:395-400`). A deeper per-domain matrix can wait.
- W16 synthesis-skill allowed-tools: disagree if the two-pass skill overlay is meant to be advertised in v0.1.6. The skill still grants `Bash(hai synthesize --bundle-only *)` / `Bash(hai synthesize --drafts-json *)`, while its examples put `--as-of` and `--user-id` before those flags (`src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:1-5`, `src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:14-20`, `src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md:88-94`). If permission matching is order-sensitive, the skill blocks itself. If the default v0.1.6 path is runtime-only `hai daily`, deferral is acceptable but should stay explicit.

## Documentation / capabilities-manifest correctness

- The generated contract file matches current `hai capabilities --markdown`; no regeneration drift was found.
- The manifest content is still wrong for `hai daily`: code emits `incomplete`, but the schema omits it (`src/health_agent_infra/cli.py:3723-3756`, `src/health_agent_infra/cli.py:5724-5730`).
- The manifest content is stale for `hai pull`: the annotation says CSV default/live via `--live` (`src/health_agent_infra/cli.py:4617-4620`), but source resolution now defaults to Intervals.icu when credentials exist (`src/health_agent_infra/cli.py:515-547`).
- `hai capabilities --json` is documented in README, `intent-router`, and the generated contract preamble, but the parser has no `--json` (`README.md:20-23`, `src/health_agent_infra/skills/intent-router/SKILL.md:21-24`, `reporting/docs/agent_cli_contract.md:3-8`, `src/health_agent_infra/cli.py:6009-6018`).
- README's top daily section is correct, but the CLI cheat sheet remains stale for daily, pull, and review record (`README.md:95-123`, `README.md:343-364`).
- `expert-explainer` frontmatter is fixed, but its invariant text still omits `hai research` from the allowed read-only commands (`src/health_agent_infra/skills/expert-explainer/SKILL.md:1-5`, `src/health_agent_infra/skills/expert-explainer/SKILL.md:125-131`).

## Ship verdict

SHIP_WITH_FIXES - must-fix before tag: [P0] bump release metadata/contract version to 0.1.6; [P1] add `hai capabilities --json` alias or remove all docs/skill references; [P1] fix `hai daily` capabilities output schema/description for `incomplete`; [P1] update README cheat sheet + `agent_integration.md` stale daily/review-record protocol; [P1] add validation inside `record_review_outcome` or explicitly document direct Python writers as unsupported.
