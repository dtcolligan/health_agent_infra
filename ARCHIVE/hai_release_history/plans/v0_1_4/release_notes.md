# v0.1.5 — Release Notes

**Status:** code-complete; TestPyPI dogfood + Codex round-2 audit + Codex r2 pushback fixes all closed; one Codex round-3 gate + real-PyPI push remain.
**Package version:** `0.1.5` (internally planned as v0.1.4; PyPI 0.1.4 was shipped earlier from commit `81997aa` before this work landed and is immutable, so this release ships as `0.1.5`)
**Schema head:** 18 (was 16 in v0.1.3.devN)
**Test suite:** 1,841 passing, 4 skipped, 0 failing (was 1,489 at v0.1.2)

The v0.1.4 release was originally scoped around four design docs (D1–D4) covering re-author semantics, intake write paths, user-facing narration, and cold-start coverage. During the 2026-04-24 dogfood it surfaced three more thesis-critical gaps that blocked release: the wearable wasn't actually feeding running data to the agent, the agent's onboarding was high-friction, and a Codex strategic review revealed the canonical synthesis path had been silently bypassing safety validation since the D2 retirement of `hai writeback`. v0.1.4 closes all of them.

The thesis: this is the runtime that makes serious personal health agency possible through open, local, agentic infrastructure. v0.1.4 is the first release where that claim survives an audit.

---

## Headline changes

### 1. Activity pull pipeline — wearable runs reach the agent

Before: the intervals.icu adapter only hit `/wellness.json` (daily rollups). Per-session detail (HR zones, interval structure, TRIMP, distance, duration) never reached the running domain — every run deferred at `coverage=insufficient` because the daily-rollup `total_distance_m` / `vigorous_intensity_min` columns were always null.

After: the adapter also calls `/activities`, parses the per-session payload into a typed `IntervalsIcuActivity` dataclass, persists it through migration 017's `running_activity` table, aggregates today's sessions into the daily rollup so the existing classifier sees real numbers, and threads structural signals (`z4_plus_seconds_today`, `z4_plus_seconds_7d`, `last_hard_session_days_ago`, `today_interval_summary`, `activity_count_14d`) through `derive_running_signals` for downstream skill reasoning. New classifier coverage relaxation: when `activity_count_14d >= 3` and weekly mileage is present, coverage no longer forces defer.

Verified end-to-end against the live intervals.icu account: 6 runs across the 14-day window, the 4×4 Z4/Z2 session's interval structure (`['4x 9m29s 156bpm', '1x 2m7s 146bpm']`) flowing through verbatim, running block flipped from `coverage=insufficient / forced_action=defer / readiness=unknown` to `coverage=full / forced_action=None / readiness=ready`.

### 2. Intake-gaps surface — low-friction agent onboarding

Before: the agent dripped check-in questions one domain at a time (or missed them entirely — the dogfood surfaced sleep being asked about even though sleep was fully covered passively).

After: new `core/intake/gaps.py` exposes a curated mapping from classifier uncertainty tokens to user-closeable intake commands, deliberately distinguishing manual-closeable gaps from history-dependent or source-level ones. New `hai intake gaps` CLI emits the gap list as JSON; `hai daily` output gains a `gaps` stage with the same shape. The `merge-human-inputs` skill now codifies the protocol: at session start, read the gaps list, compose ONE consolidated question in the agent's own voice, parse the free-text answer, route to the right `hai intake <X>` commands, retry synthesis. Zero-gap days produce no question.

Code owns the inventory ("these fields are missing, here's how to log each"); agent owns the prose. That separation is what makes this a long-term contract rather than agent-personality.

### 3. Synthesis safety closure (Codex P1 #1) — release blocker

Before: D2 retired `hai writeback` in v0.1.4 and the safety validator (`core/validate.py` with `BANNED_TOKENS` + `validate_recommendation_dict`) lost its caller. The canonical `hai synthesize` path persisted final recommendations without running them through the validator. The project's first stated success criterion — "no final recommendation can bypass safety validation" — was silently false on the canonical write path.

After: `core/validate.py` extended with per-domain `ALLOWED_ACTIONS_BY_DOMAIN` + `SCHEMA_VERSION_BY_DOMAIN` tables; banned-token sweep widened to cover `rationale` + `action_detail` + `uncertainty` + `follow_up.review_question`. `run_synthesis` validates every final recommendation BEFORE the `BEGIN EXCLUSIVE` transaction. Defensive guard rejects multiple active proposals for the same `(for_date, user_id, domain)` chain key before commit. Failed validation → `SynthesisError` with stable `invariant=...` field, atomic rollback by construction (no partial commits possible).

### 4. Proposal JSONL recovery (Codex P1 #2)

Before: `hai propose` wrote `<domain>_proposals.jsonl` per the pre-D1 contract that JSONL is the durable audit boundary, but `hai state reproject` ignored those files. Audit logs you can't replay are decorative.

After: `reproject_from_jsonl` extended with a proposals group: discovers all six per-domain JSONLs, truncates `proposal_log`, validates each line via `validate_proposal_dict`, replays via `project_proposal(replace=True)` so D1 revision chains rebuild from JSONL append order. Counts surface as `proposals` (replayed) and `proposals_skipped_invalid` (corrupt or validation-failing lines, skipped not raised — a bad line in a long log can't abort the whole reproject).

### 5. Privacy hardening (Codex Phase D)

Before: state DB and JSONL audit logs were created with default umask (typically 0o644 on POSIX — readable by other users on the same machine). Packaged Garmin CSV fixture was undocumented as synthetic.

After: new `core/privacy.py` enforces 0o700 directories + 0o600 files on POSIX (no-op on Windows; best-effort with warn-once on chmod failure). Wired into `initialize_database` (DB + WAL/SHM/journal siblings) and every JSONL writer (readiness, gym, nutrition, stress, notes, proposal writeback, review event/outcome). Idempotent — re-running doesn't loosen. New `reporting/docs/privacy.md` covers what's stored / where / inspect / export / delete / migrate / no-telemetry. New `data/garmin/export/README.md` documents the packaged CSV as synthetic with regression-test pointer. PII regression test scans for emails, phones, GPS coordinates, device serials, identity columns.

### 6. D1–D4 (carried from earlier v0.1.4 work, recap)

- **D1 re-author semantics** — proposals revise via `hai propose --replace` with a forward-link revision chain; daily plans supersede via `hai synthesize --supersede` with `superseded_by_plan_id`; review outcomes auto-re-link to the canonical leaf. Migrations 013–016.
- **D2 intake write paths** — `hai writeback` removed entirely; every `hai intake <X>` now persists to state via JSONL → projector dual-write; new `manual_readiness_raw` table (migration 015); recovery-readiness skill aligned with the other five.
- **D3 user-facing narration** — `hai today` ships as a first-class non-agent-mediated prose renderer over the canonical plan; new `core/narration/` module shared between `hai today` and the `reporting` skill; per-domain defer review-question templates; voice linter (`core/narration/voice.py`) sweeps for banned medical language and rule-id leaks.
- **D4 cold-start** — 14-day cold-start window per domain keyed on accumulated-signal history; running + strength + stress get coverage relaxation when intent is declared; nutrition stays strict (no relaxation); `hai today` cold-start footer per domain.

---

## CLI surface changes

### Added

- `hai intake gaps --as-of --user-id --evidence-json [--db-path]` — read-only structured surface for agent-driven prompting
- `hai today --as-of --user-id [--format markdown|plain|json] [--domain ...]` — first-class user surface (added in earlier v0.1.4 work, restated here for completeness)
- `hai daily` output gains `gaps` stage + `snapshot.full_bundle` field
- `hai pull` output gains `pull.activities` array (intervals.icu source only)
- `hai clean` enriches `accepted_running_state_daily` from activities when present

### Removed

- `hai writeback` — retired per D2; `hai propose` + `hai synthesize` is the canonical commit path. Migration tests + e2e fixtures updated accordingly.
- `hai classify`, `hai policy` — debug CLIs deleted per ADR `adr_classify_policy_cli.md`; their behaviour is subsumed by `hai state snapshot --evidence-json`.

### Changed

- `hai propose --replace` — new flag for D1 revision semantics; pre-flight rejects without `--replace` when canonical leaf exists
- `hai synthesize --supersede` — keeps prior canonical plan; writes new plan at `<canonical_id>_v<N>`; flips `superseded_by_plan_id` on prior leaf
- `hai explain --operator` — canonical operator-report flag (`--text` retained as deprecated alias with stderr hint)
- `hai pull --source intervals_icu` — now also calls `/activities`; daily-rollup intensity minutes derived from HR zone times
- `hai daily` — TTY-aware stderr hint (`next: read today's plan …`) appended on terminal stdouts

---

## Schema changes (migrations 013–017)

| Version | Migration | Purpose |
|---|---|---|
| 013 | `proposal_log` revision columns | D1 revision-chain bookkeeping |
| 014 | `daily_plan.superseded_by_plan_id` forward-link | D1 plan-supersession audit |
| 015 | `manual_readiness_raw` table | D2 readiness intake landing |
| 016 | `review_outcome` re-link columns | D1 outcome auto-re-link to canonical leaf |
| 017 | `running_activity` table | Per-session structural data from intervals.icu `/activities` |

All migrations apply forward cleanly from any prior schema version (verified in `test_migration_backfill_013_014.py` and `test_migrations_roundtrip.py`).

---

## Breaking changes

- **`hai writeback` removed.** Recovery proposals + synthesis is the canonical path. If you have a script that calls `hai writeback`, replace with `hai propose --domain recovery` followed by `hai synthesize`.
- **Recovery proposal `schema_version` is now `recovery_proposal.v1`** (was `training_recommendation.v1` on the legacy writeback path). Same for nutrition (`nutrition_proposal.v1` not `nutrition_recommendation.v1`). Hand-authored proposals must use the new schema_version per domain — the per-domain validator will reject mismatches.
- **`hai classify` / `hai policy` debug CLIs removed.** Use `hai state snapshot --evidence-json <path>` instead.
- **JSONL audit files now ship at 0o600 on POSIX.** Existing files are re-locked on next write; no data is lost. If you script-reads any JSONL with a different uid, the read will fail — chmod manually if you have a deliberate sharing arrangement.

---

## Deferred to v0.1.5+

Per Codex strategic-report sequencing, the following are intentional v0.1.4 non-goals:

- **Formal contract documentation layer** — public `contracts/` section with snapshot / proposal / synthesis bundle / recommendation / review / memory / explainability / error contracts. The `agent_cli_contract.md` + JSON capabilities manifest are the v0.1.4 surface; the prose contract docs land in v0.1.5.
- **Agent ecosystem docs** — generic agent loop + Codex / Claude Code / OpenClaw integration docs. The runtime is contract-driven and works from any agent today; vendor-specific scaffolding can wait.
- **Goal-aware planning + weekly review** — adds product surface but not safety surface; v0.1.5+.
- **MCP wrapper** — scaffolded in `mcp_scaffold.md`; implementation deferred until contracts stabilize.
- **CI hygiene** — uv lockfile, Bandit advisory, lint cleanup. Operational, not thesis-critical.
- **Per-intake / classifier contract audit** — scope expansion that duplicates existing per-domain unit coverage.
- **README walkthrough CI automation** — manual dogfood ritual covers it for v0.1.4.

---

## Known limitations

- **Garmin-direct `/activities` fallback not wired.** When intervals.icu hasn't synced an activity yet, the agent can't see it from any other source. Garmin Connect direct is currently rate-limited (429) on real-world use anyway. Separate fix.
- **`all_day_stress` and `body_battery` unavailable from intervals.icu.** Stress domain leans entirely on manual `hai intake stress` until garmin-direct lands.
- **Sleep efficiency + start-time unavailable from intervals.icu wellness.** Sleep block caps coverage at `partial`. Source-level gap, not a runtime bug.
- **Soreness intake is whole-body.** No per-region tagging in v1; users who report leg-only soreness lose the specificity. Documented as v2 work.
- **Breakfast question missing from morning gap surface.** Nutrition gap is curated as priority-2 (EOD full macros only); morning context for partial intake routes through `hai intake note`. v0.1.5 split into `breakfast_unlogged` + `no_nutrition_row_for_day`.
- **Strength gap mislabels as P1 BLOCK when planned_session_type already declares strength intent.** Cold-start relaxation closes coverage downstream; gap inventory should respect that. Refinement queued.
- **Schema-version naming inconsistency** — recovery uses `training_recommendation.v1` (legacy); other five domains use `<domain>_recommendation.v1`. Documented; rename is a v0.2 concern.

---

## Test-suite delta

- v0.1.2: 1,489 tests
- v0.1.4 entering 2026-04-24: 1,710 tests (D1–D4 + WS-A through WS-E)
- v0.1.4 mid-session: 1,824 tests (+ activity pull, intake gaps, Phase A, Phase B, Phase D)
- v0.1.5 shipping (post Codex r2 absorptions): **1,841 tests** (+ banned-token whole-word regression guards, days_ago anchor, propose contract-shape)
- All passing, 4 deliberately skipped (Windows-only privacy tests on POSIX), 0 failing

New test files:

- `safety/tests/test_pull_intervals_icu.py` (extended +16) — adapter activities endpoint
- `safety/tests/test_projector_running_activity.py` (+17) — projector + reads + aggregator
- `safety/tests/test_intake_gaps.py` (+20) — gap inventory + CLI + hai daily integration
- `safety/tests/test_synthesis_safety_closure.py` (+13) — Phase A regression suite
- `safety/tests/test_reproject_proposal_recovery.py` (+11) — Phase B regression suite
- `safety/tests/test_privacy_hardening.py` (+18) — Phase D regression suite
- `safety/tests/e2e/test_running_activity_journey.py` (+5) — end-to-end activity journey

---

## Release-readiness checklist

- [x] All 18 v0.1.4 acceptance criteria green (see `acceptance_criteria.md`)
- [x] All four D-docs ratified
- [x] Each workstream's artifact list complete
- [x] Codex P1 #1 + P1 #2 closed; Codex Phase D closed
- [x] Activity pull verified end-to-end against live intervals.icu account
- [x] Intake gaps surface verified against live data
- [x] Synthesis safety validation enforced on canonical path
- [x] Proposal JSONL replay verified
- [x] File permissions hardened on every user-data write site
- [x] Privacy doc + fixture README shipped
- [x] Test suite green (1,841 passing)
- [x] `agent_cli_contract.md` regenerated
- [x] Phase 2 regression spot-checks (revert each landmark fix locally, confirm CI fails; results in `release_qa.md` Phase-2 table)
- [x] TestPyPI upload + fresh-pipx dogfood — `0.1.5` installs cleanly, 18 migrations apply, 37 commands in capabilities manifest, `hai doctor` 8/8 green, gaps stage emits
- [x] Codex round-2 audit completed 2026-04-24; three pushback items (whole-word banned-token matcher, days_ago plan-date anchor, hai propose output/contract alignment) absorbed in follow-up commits
- [ ] **Manual:** Codex round-3 audit (confirms r2 pushbacks cleanly closed)
- [ ] **Manual:** Real PyPI push (Phase 4 of `release_qa.md`)

When the two remaining gates close, tag `v0.1.5` and `twine upload dist/*` to real PyPI.

---

## Strategic positioning

v0.1.5 establishes the project's identity as **open-source infrastructure for data-sovereign personal health agents**, not a health app or chatbot. The runtime is the product; agents are the consumers; users own their data and recommendations.

The next release (v0.1.6) earns the right to expand intelligence: formal contracts, agent ecosystem docs, goal-aware planning, weekly review. v0.1.5 earns the right to ship to PyPI by closing the safety, recovery, privacy, and core-thesis (wearable→agent) gaps that would have made the project's stated success criteria silently false on the earlier 0.1.4 release.
