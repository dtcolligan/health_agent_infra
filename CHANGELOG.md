# Changelog

All notable changes to Health Agent Infra will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Per-release detail lives under `reporting/plans/<version>/release_notes.md`.

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

[0.1.5]: https://pypi.org/project/health-agent-infra/0.1.5/
[0.1.4]: https://pypi.org/project/health-agent-infra/0.1.4/
[0.1.3.dev0]: https://pypi.org/project/health-agent-infra/0.1.3.dev0/
[0.1.2]: https://pypi.org/project/health-agent-infra/0.1.2/
[0.1.1]: https://pypi.org/project/health-agent-infra/0.1.1/
[0.1.0]: https://pypi.org/project/health-agent-infra/0.1.0/
