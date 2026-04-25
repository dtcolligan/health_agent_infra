# Changelog

All notable changes to Health Agent Infra will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the v0.x caveat that breaking changes can land in minor releases
until v1.0.

Per-release detail lives under `reporting/plans/<version>/`.

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

[0.1.7]: https://pypi.org/project/health-agent-infra/0.1.7/
[0.1.6]: https://pypi.org/project/health-agent-infra/0.1.6/
[0.1.5]: https://pypi.org/project/health-agent-infra/0.1.5/
[0.1.4]: https://pypi.org/project/health-agent-infra/0.1.4/
[0.1.3.dev0]: https://pypi.org/project/health-agent-infra/0.1.3.dev0/
[0.1.2]: https://pypi.org/project/health-agent-infra/0.1.2/
[0.1.1]: https://pypi.org/project/health-agent-infra/0.1.1/
[0.1.0]: https://pypi.org/project/health-agent-infra/0.1.0/
