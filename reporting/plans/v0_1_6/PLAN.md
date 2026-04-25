# v0.1.6 Plan — post-run findings + improvements

> **Provenance.** This plan was authored after a real end-to-end user
> session on 2026-04-25. The maintainer (Dom) used the agent in user
> mode for a full day: narrate yesterday's plan → log gym session +
> review outcome + nutrition → fill gap data for the prior day →
> generate today's plan via 6-domain skill orchestration → narrate.
> Everything below is grounded in friction or bugs the run actually
> surfaced. Companion artifact: `codex_audit_prompt.md` (external
> review brief).
>
> **Status.** Draft, awaiting Codex audit response. The
> "Implementation log" at the bottom is updated as work lands.
> Items the Codex audit later corrects / adds get folded back into
> this plan as a "Codex-derived" subsection.

---

## 0. Goals & non-goals

### Goals (v0.1.6)

1. Fix the bugs that bit a real user during a real session.
2. Close the docs ↔ code drift those bugs exposed.
3. Sand down the highest-friction UX edges (intervals.icu as the
   default supported pull source, intake `--base-dir` ergonomics,
   `hai daily` end-to-end story).
4. Make the README accurate to lived experience — calibration
   expectations, where data lives, what a user has to do vs what the
   agent does.
5. Land small features that prevent recurrence (e.g. structured
   `"computed": false` flag on `hai intake gaps` so an agent can't
   trust a misleading zero; an automatic skill ↔ CLI drift check).

### Non-goals (v0.1.6)

- Cloud sync, multi-user, meal-level nutrition (per
  `reporting/docs/non_goals.md`).
- Rewriting Garmin live-pull. Marked as best-effort; intervals.icu is
  the supported live source.
- v0.2 redesign work.
- Performance optimisation.

---

## 1. Empirical findings from the 2026-04-25 session

Each item below is reproduced or directly observed. Severity is the
maintainer's judgment pre-audit; the Codex audit will challenge or
confirm.

### Bugs (P0 — release-blocker)

- **B1. `hai state reproject` raises `sqlite3.IntegrityError: FOREIGN
  KEY constraint failed`.** Stack trace ends at
  `core/state/projector.py:1258` on `DELETE FROM proposal_log`. The
  reproject performs a destructive sequence on accepted_*_state tables
  + audit tables but `proposal_log` has children
  (`planned_recommendation` per
  `migrations/011_planned_recommendation.sql:64`) not cascaded before
  the delete. Workaround: skip the reproject — intake commands
  incrementally project, so reproject is only needed for ground-up
  rebuild. Fix: refuse cleanly when synthesis-side tables (which are
  NOT JSONL-derived) would be orphaned, with an opt-in
  `--cascade-synthesis` flag for the destructive case.
- **B2. `hai intake gaps` returns `{"gap_count": 0, "gaps": []}` when
  called without `--evidence-json`.** This is mechanically misleading:
  the schema description says "gaps cannot be computed" without
  evidence, but the JSON shape is indistinguishable from a clean
  zero. An agent that polls gaps before deciding to ask the user
  silently does the wrong thing. Fix: refuse with USER_INPUT and a
  clear stderr; emit `"computed": true` on the OK path so callers can
  pattern-match.
- **B3. Schema drift: intent-router skill docs vs `hai review record`
  CLI.** Skill says `--completed 0|1` and per-flag fields; CLI
  requires `--outcome-json` and `--completed yes|no`. Hit during the
  session. There are likely sibling drifts in other skills.

### Friction / UX (P1 — should ship)

- **F1. `hai daily` does not complete the loop on its own.** It
  pulls / cleans / snapshots / detects gaps / returns
  `awaiting_proposals` and stops. The agent must invoke 6 per-domain
  readiness skills, post 6 proposals via `hai propose`, then call
  `hai synthesize`. The README's Install block presents `hai daily`
  as a one-liner; the description on the command itself says
  "orchestrate"; both read as end-to-end. Fix options: (a) update
  docs to be accurate, (b) auto-invoke skills inside `hai daily` if
  running under Claude Code, (c) ship a `hai daily --auto` mode that
  does only the deterministic stages and exits with a structured
  next-step hint the agent reads.
- **F2. Garmin live pull is unreliable.** 429s from mobile + portal +
  Cloudflare during the session. intervals.icu is the maintainer's
  declared supported source for the foreseeable future. README +
  Install + `hai daily` defaults should reflect this.
- **F3. `hai intake nutrition` is a daily total + not idempotent.**
  Re-calling creates a supersede chain. Ergonomically forces the user
  to wait until end-of-day OR use a `hai intake note` as a
  scratchpad (which is what we did). README/intake docs don't make
  this obvious. Fix: documentation + a clearer warning when someone
  re-calls within the same day, optionally a per-meal intake surface
  (would be a v0.2 candidate).
- **F4. Every `hai intake *` requires `--base-dir`.** New users hit
  this on first invocation. Fix: resolve a default the same way
  state-db does (`$HAI_BASE_DIR` env var or
  `~/.health_agent/`) — the directory already exists for any user
  who's run `hai init`.
- **F5. `planned_session_type` vocabulary is undocumented.** The
  merge-human-inputs skill calls it free text; downstream
  classifiers may treat unrecognised strings differently. Today's
  session used `strength_back_biceps` (composed by the agent) — fine
  for narration, possibly contributing to the strength escalation.
  Fix: document the canonical vocabulary, or add a CLI helper
  (`hai exercise list-session-types` or similar) that lists what
  the classifiers actually pattern-match against.

### Documentation (P1)

- **D1. README missing calibration expectations.** Drafted mid-session
  as a "Calibration timeline" section (deferred until plan approval).
- **D2. README missing data-location pathway.** Drafted mid-session as
  a "Where your data lives" section (deferred until plan approval).
- **D3. README's `hai daily` story is misleading** — see F1.
- **D4. `hai intake nutrition` daily-total semantics not surfaced** —
  see F3.

### Memory + agent-feedback (P2 — nice-to-have)

- **M1. The agent should query the state DB / intervals.icu activity
  log before asking the user about a session that's already
  recorded.** Saved as an auto-memory feedback note during the
  session (`feedback_check_state_before_asking.md`). No code change
  needed; this is agent-side discipline.

---

## 2. Workstream plan

Group the items above into ~half-day workstreams so the maintainer
can interleave with other work. Each workstream lists the file
touchpoints + an acceptance criterion.

### W1 — Reproject FK fix (B1)

- Read `core/state/projector.py` around the failing delete.
- Trace FK relationships: `planned_recommendation.proposal_id`
  references `proposal_log` (migration 011); `x_rule_firing` and
  `recommendation_log` reference `daily_plan` (migration 003 + 009).
- Add `class ReprojectOrphansError(Exception)` and a
  `cascade_synthesis: bool = False` parameter to
  `reproject_from_jsonl`. Before destructive deletes that would orphan
  synthesis-side rows, count `planned_recommendation` /
  `daily_plan` / `x_rule_firing`. If any are populated AND
  `cascade_synthesis=False`, ROLLBACK and raise with a message that
  names the row counts and points at the opt-in flag. If
  `cascade_synthesis=True`, delete in dependency order.
- Add `--cascade-synthesis` flag to the CLI handler.
- Export `ReprojectOrphansError` from `core/state/__init__.py`.
- Add regression tests: refusal raises the error with row counts in
  message; cascade=True clears + replays.
- **Acceptance:** `hai state reproject` against a DB with populated
  `planned_recommendation` rows refuses with a helpful message
  instead of crashing; `--cascade-synthesis` succeeds.

### W2 — Gaps "computed" honesty (B2)

- In `cmd_intake_gaps`: when `--evidence-json` is absent, print stderr
  explaining why gap detection requires it, return `USER_INPUT`.
- On the OK path, emit `"computed": true` in the JSON.
- Update the `--evidence-json` help text and the docstring on
  `cmd_intake_gaps` to reflect "required in practice."
- Update the `intent-router` and `merge-human-inputs` skills' gap-fill
  protocols to handle the new shape.
- Add regression test: CLI without `--evidence-json` exits USER_INPUT;
  CLI with `--evidence-json` includes `computed: true`.
- **Acceptance:** an agent that ran `hai intake gaps` without
  evidence-json today would see a refusal instead of a misleading
  zero.

### W3 — Skill ↔ CLI schema drift sweep (B3 + open)

- Build `scripts/check_skill_cli_drift.py`: walk each
  `src/health_agent_infra/skills/*/SKILL.md`, extract `hai` invocations
  inside fenced code blocks, attribute flags to invocations within the
  block (window ends at next invocation), cross-reference each
  `--flag` against `hai capabilities --json`'s flag list for that
  command. Report unknown flags + choice-hint mismatches.
- Run it. Fix every drift: known target is the intent-router skill's
  `hai review record` example (must use `--outcome-json` +
  `--completed yes|no` + `--intensity-delta much_lighter|lighter|same|harder|much_harder`)
  and `hai memory list` (no `--as-of` exists).
- Wire as a pytest test (`safety/tests/test_skill_cli_drift.py`) so
  CI catches future drift.
- **Acceptance:** validator returns zero drifts.

### W4 — `hai daily` honest completion semantics (F1)

- Decide between the three options in F1. Maintainer leans (a) +
  (c): make the docs accurate AND ship a `--auto` mode for the
  agent-driven flow.
- For (a): update README, update `hai daily --help` description,
  update `agent_integration.md`.
- For (c): the existing `hai daily` already returns
  `awaiting_proposals` with a structured `hint`. Formalise that hint
  into a documented contract field (`stages.synthesize.hint`) that
  agents watch for, and document that field in
  `agent_integration.md`.
- **Acceptance:** README's Install block is accurate; an agent using
  the documented flow does not hit the "wait, why didn't this
  finish" surprise we hit today.

### W5 — intervals.icu as default supported source (F2)

- Make `--source intervals_icu` the default for `hai pull` and
  `hai daily` when no source flag is passed AND intervals.icu auth
  is configured. Fall back to csv only if `--source csv` is explicit
  or no auth is present.
- Soften the `--live` legacy flag: prefer intervals.icu unless
  `--source garmin_live` is explicit.
- README: rewrite Install to use intervals.icu auth as the primary
  step. Add a one-liner about Garmin live being best-effort under
  rate-limiting.
- **Acceptance:** a brand-new user running `hai init --with-auth`
  sets up intervals.icu by default, never sees a 429.

### W6 — Nutrition daily-total UX honesty (F3)

- README "Recording your day" should say "nutrition is a daily
  total — log it once at end of day; re-calling within the same day
  creates a supersede chain you probably don't want."
- Light CLI change: when `hai intake nutrition` is called for a day
  that already has a row, print a stderr warning before writing:
  "Existing nutrition row for 2026-04-25 will be superseded by this
  call. Re-run with `--confirm-supersede` if intended; otherwise this
  looks like a per-meal call, which is not the intended use." The
  warning shouldn't block; it just makes the behaviour visible.
- **Acceptance:** a user who tries to call nutrition twice the same
  day sees the warning before the second call lands.

### W7 — Default intake `--base-dir` (F4)

- Add `core/paths.py` with `DEFAULT_BASE_DIR = Path.home() /
  ".health_agent"` and `resolve_base_dir(explicit) -> Path` mirroring
  `resolve_db_path`.
- Make `--base-dir` optional on every `hai intake *`,
  `hai propose`, `hai review *`, `hai daily`, and
  `hai state reproject` subcommand; resolve from `$HAI_BASE_DIR`
  env var → default.
- Update help strings to name the resolution chain.
- **Acceptance:** `hai intake stress --score 3` works from a fresh
  shell with no `--base-dir` flag.

### W8 — `planned_session_type` vocabulary (F5)

- Grep for everywhere `planned_session_type` is matched against in
  the domain classifiers. Build the canonical vocabulary list.
- Document it: in the SKILL.md for merge-human-inputs and in the
  README's "Recording your day" section ("the system recognises
  these patterns: easy_z2, intervals_4x4, strength_sbd, …").
- Optional CLI helper: `hai planned-session-types --json` emits the
  list (read-only, agent-safe).
- **Acceptance:** an agent / user knows what strings to use and
  unrecognised strings get surfaced explicitly (not silently
  classified as "other").

### W9 — README rewrite pass (D1, D2, D3, D4 + sweep)

- Land D1 ("Calibration timeline") + D2 ("Where your data lives")
  sections (previously drafted; deferred until this plan was
  approved).
- D3: rewrite the Install block + the `hai daily` mention to match
  reality post-W4.
- D4: add the nutrition daily-total note.
- Sweep: any other place the README's promise diverges from observed
  behaviour, fix.
- **Acceptance:** a fresh reader of the README, running through
  Install → Reading your plan → Recording your day, hits no
  surprises.

---

## 3. Proposed sequencing

Order chosen so the agent + maintainer can keep using the system
during v0.1.6 development without regression.

| # | Workstream | Why this order |
|---|---|---|
| 1 | W2 (gaps `computed`) | Quickest, smallest blast radius, removes a silent agent footgun. |
| 2 | W3 (skill drift sweep) | Builds the safety net before changing more CLI surface. |
| 3 | W7 (default `--base-dir`) | Frees subsequent UX work from the friction. |
| 4 | W4 (`hai daily` honesty) | Precondition for W5 + W9. |
| 5 | W5 (intervals.icu default) | Touches Install — coordinate with W9 README rewrite. |
| 6 | W1 (reproject FK) | Real bug, but workaround exists; not blocking daily use. |
| 7 | W8 (planned_session_type vocabulary) | Touches multiple skills; do after W3 to avoid re-introducing drift. |
| 8 | W6 (nutrition supersede warning) | Light touch; bundle with W9. |
| 9 | W9 (README rewrite pass) | Final pass — reflects everything above. |

---

## 4. Acceptance for the v0.1.6 release

The release is shippable when:

- All P0 items (B1 + B2 + B3) have committed fixes + regression tests.
- All P1 items (F1 + F2 + F3 + F4 + F5 + D3 + D4) have either landed
  fixes or are explicitly deferred to v0.1.7 with a documented
  rationale.
- The skill-vs-CLI drift validator (W3) reports zero drifts and is
  wired into CI.
- The README's Install → Reading your plan → Recording your day
  walk-through can be performed by a fresh user end-to-end without
  agent intervention to clarify ambiguous behaviour.
- Codex audit's P0 + P1 findings have been triaged into either
  "fixed in this release" or "deferred with rationale."

---

## 5. Codex audit integration

This plan is the maintainer's read of the run. The Codex audit
(`codex_audit_prompt.md`) is the second opinion. When the audit
comes back, fold it in:

1. Append a "Codex audit findings" section below this one.
2. For each Codex finding, decide: **agree → add as workstream**,
   **disagree → record disagreement with reason**, **defer → flag
   for v0.1.7**.
3. Re-sequence sections 2–4 as needed.
4. Note the audit version + date in the changelog at the bottom.

---

## 6. Implementation log

Append to this section as work lands. One line per significant
change: `<date> · <workstream> · <commit-or-PR-or-file:line> ·
<short note>`.

- 2026-04-25 · plan + audit · `reporting/plans/v0_1_6/{PLAN.md,
  codex_audit_prompt.md}` · authored.
- 2026-04-25 · audit · `reporting/plans/v0_1_6/internal_audit_response.md` ·
  internal cross-validation against Codex round 1.
- 2026-04-25 · audit · `reporting/plans/v0_1_6/codex_audit_response_round2.md` ·
  Codex round 2 on `v0.1.4-release`; confirmed B1–B7 + 7 new findings (C1–C7).
- 2026-04-25 · W11 · `cli.py:111` (`_load_json_arg` helper); 5 call sites
  (`cmd_pull:173`, `cmd_clean:533`, `cmd_propose:972`, `cmd_review_schedule:1738`,
  `cmd_review_record:1768`); top-level `main()` exception guard at `cli.py:5712`.
  13 new regression tests (`test_cli_json_arg_handling.py`).
- 2026-04-25 · W12 · `core/writeback/outcome.py` (new validator with 11 named
  invariants); `cmd_review_record` wired to validate before any write. 36 new
  regression tests (`test_review_outcome_validation.py`).
- 2026-04-25 · W10 + W4 · `cli.py:3494` proposal-completeness gate
  (`gate_ok = not missing_expected`; three statuses:
  awaiting_proposals/incomplete/complete); helpful hint text on the
  incomplete path. Existing locking test at `test_cli_daily.py:272` flipped;
  added happy-path companion. `--domains` help text rewritten.
- 2026-04-25 · W2 · `cmd_intake_gaps` refuses without `--evidence-json`,
  emits `"computed": true` on OK path. New regression test at
  `test_intake_gaps.py:test_cli_intake_gaps_refuses_without_evidence_json`.
- 2026-04-25 · W7 · `core/paths.py` (new `DEFAULT_BASE_DIR` +
  `resolve_base_dir`); 11 argparse declarations + 11 handler call-sites
  migrated. 8 new regression tests (`test_default_base_dir.py`).
- 2026-04-25 · W3 + W18 · `scripts/check_skill_cli_drift.py` (validator);
  `safety/tests/test_skill_cli_drift.py` (CI gate); fixed intent-router
  review-record + memory-list drift; fixed reporting `--since` drift.
- 2026-04-25 · W1 · `core/state/projector.py` `ReprojectOrphansError` +
  `cascade_synthesis` parameter; `cmd_state_reproject` `--cascade-synthesis`
  flag; 3 new regression tests appended to
  `test_reproject_proposal_recovery.py`.
- 2026-04-25 · W13 · `cmd_synthesize --bundle-only` refuses when
  `proposal_log` is empty for `(for_date, user_id)`. 1 new regression test
  (`test_synthesize_bundle_only_gate.py`).
- 2026-04-25 · W15 · `cmd_propose` does its own projection inline (no
  longer routes through `_dual_write_project`); `ProposalReplaceRequired`
  is fatal `USER_INPUT`; other projection failures are fatal `INTERNAL`
  with "JSONL durable, run reproject" stderr. New
  `db_projection_status` field on stdout payload. 3 new regression tests
  (`test_propose_dual_write_contract.py`).
- 2026-04-25 · W17 · `core.research` exposed via `hai research topics` +
  `hai research search --topic <t>` (read-only, agent-safe); removed
  `Bash(python3 -c *)` from `expert-explainer` `allowed-tools`. 6 new
  regression tests (`test_research_cli.py`). Contract doc regenerated.
- 2026-04-25 · W19 · `hai state reproject` contract description updated
  to "deterministic modulo projection timestamps."
- 2026-04-25 · W20 · `core/state/store.py` `applied_schema_versions` +
  `detect_schema_version_gaps`; `hai doctor` surfaces gaps as warn ahead
  of legacy "pending migrations" check. 5 new regression tests
  (`test_schema_version_gap_detection.py`).
- 2026-04-25 · W5 · `_resolve_pull_source` now defaults to
  `intervals_icu` when credentials are configured (else falls back to
  csv); `--source` and `--live` help text updated; 1 existing test
  renamed + flipped (`test_pull_explicit_csv_source_uses_committed_fixture`),
  1 new test for the no-auth fallback path.
- 2026-04-25 · W9 · README rewrite: new "Where your data lives" section,
  new "How `hai daily` actually completes" section, new "Calibration
  timeline" section (with W14's per-domain cold-start asymmetry note
  folded in), updated Install / Recording-your-day to reflect intervals.icu
  default + optional `--base-dir` + nutrition daily-total semantics +
  planned-session vocabulary + strict-bool review payload requirement.

**v0.1.6 net delta:** 13 workstreams shipped (W1–W3 + W4 + W5 + W7 + W9 +
W10 + W11 + W12 + W13 + W15 + W17 + W18 + W19 + W20). Test count
1844 → 1921 (+77 new tests). Zero locked broken behaviours remain.
Outstanding for v0.1.7: W6 (nutrition supersede warning — docs only
shipped, code warning deferred), W8 (planned-session-type CLI helper —
docs shipped, optional CLI helper deferred), W14 (cold-start matrix
docs — partially folded into README; deeper per-domain decision
matrix doc deferred), W16 (synthesis-skill allowed-tools — Codex
flagged uncertain; not pursued).

---

## 7. Round-2 audit integration — final consolidated plan

The two-round audit (Codex r1 on `main`, internal on `v0.1.4-release`,
Codex r2 on `v0.1.4-release`) converged. Codex r2 confirmed every B1–B7
reproduction in the internal audit, corrected three errors in my
framing, and added seven new structural findings the previous rounds
missed. This section is the merged plan that supersedes §1–§5 for
sequencing and acceptance.

### 7.1 Corrections folded in from Codex r2

| Item | Original framing | Corrected framing |
|---|---|---|
| W11 / B2 target list | `cmd_writeback` named as a JSON-crash target | **REMOVED** — `cmd_writeback` doesn't exist (removed in v0.1.4 per `reporting/plans/v0_1_4/acceptance_criteria.md:42`). Add `cmd_pull` (`cli.py:173`) and `cmd_clean` (`cli.py:481`) instead. |
| Cold-start "14-day cutoff in 3 files" | Three executable duplications | **CORRECTED** — centralised at `core/state/snapshot.py:35` as `COLD_START_THRESHOLD_DAYS`. Only the explanatory note strings duplicate the literal "history_days<14" — fix by interpolating the constant. The 28-day window IS duplicated as executable logic across `domains/running/signals.py:167` and `domains/strength/signals.py:51,80` — that's the real factoring work. |
| Stale classify/policy framing | "Now accepts all 6 domains" | **CORRECTED** — commands were removed in v0.1.4 and subsumed by `hai state snapshot --evidence-json`, which emits `classified_state` + `policy_result` for every domain (per `cli.py:5552-5556`). |
| W14 cold-start symmetry | "Make symmetric across 6 domains" | **CORRECTED** — nutrition has an explicit non-relaxation test (`safety/tests/test_nutrition_cold_start_non_relaxation.py`). The right fix is a documented per-domain policy matrix, not blind symmetry. |

### 7.2 New workstreams from Codex r2 (C1–C7)

| WS | Source | Description | Pri | Effort |
|---|---|---|---|---|
| W11 (extended) | C1 | Add `cmd_pull` + `cmd_clean` to the JSON-arg-helper sweep | P0 | S (folded into W11) |
| **W15** | C2 | `cmd_propose` reports success after JSONL append even when DB projection rejects (`_dual_write_project` swallows exceptions). Make `ProposalReplaceRequired` fatal in propose; preserve JSONL only when explicitly marked rejected. | P1 | M |
| **W16** | C3 | `daily-plan-synthesis` allowed-tools may not match its own examples (`Bash(hai synthesize --bundle-only *)` vs body example `hai synthesize --as-of … --user-id … --bundle-only`). Either broaden to `Bash(hai synthesize *)` or rewrite examples. | P1 if matching is order-sensitive, P2 otherwise | S |
| **W17** | C4 | `expert-explainer` allows `Bash(python3 -c *)` despite local-only privacy claim. Replace with a bounded local CLI (e.g. `hai research search`) or weaken the invariant text. | P1 (privacy boundary) | M |
| **W18** | C5 | `reporting` skill instructs `hai review summary --since <date>`; CLI has no `--since`. Fold into W3's drift sweep. | P1 | S (W3) |
| **W19** | C6 | `hai state reproject` documented as deterministic but uses wall-clock `_now_iso()` for projection timestamps. Either document "deterministic modulo timestamps" or derive deterministically. | P2 | S |
| **W20** | C7 | `current_schema_version()` returns `MAX(version)` — gaps below max go undetected. Add contiguous-set check in `migrate` + `doctor`. | P2 | S |

### 7.3 Final severity-ranked punch list (Codex r2's, lightly cleaned)

```
[P0] hai daily accepts partial-domain proposal sets as complete — make completeness `not missing_expected`, add `incomplete` status, fix locking test — M  [W4 + W10]
[P0] File-backed JSON args can throw tracebacks — add _load_json_arg, cover propose/review-record/review-schedule/pull/clean/synthesize-drafts, top-level main() guard — M  [W11]
[P0] hai review record can fork truth between JSONL and SQLite — validate outcome payload before writes; enforce in record_review_outcome too — M  [W12]
[P1] hai state reproject can violate planned_recommendation→proposal_log FK — orphan detection + opt-in cascade — M  [W1]
[P1] hai synthesize --bundle-only bypasses no-proposals contract — refuse empty proposal bundles or mark explicitly non-computed — S  [W13]
[P1] hai intake gaps misleading zero without --evidence-json — refuse + emit "computed": true — S  [W2]
[P1] Skill/docs commands drift from parser reality — W3 validator: flags + choices + allowed-tools + body examples; fix intent-router/reporting/daily-plan-synthesis — M  [W3 + W18]
[P1] cmd_propose can report success after JSONL append while projection silently failed — make duplicate/replacement projection failures fatal or explicitly rejected — M  [W15]
[P1] expert-explainer permits arbitrary python3 -c despite privacy invariant — bounded local CLI or weaken invariant text — M  [W17]
[P1] --base-dir required across agent-facing write commands — default resolution + consistent help/error paths — M  [W7]
[P1] intervals.icu/Garmin default story misaligned — make intervals.icu primary when configured; document Garmin live as best-effort — M  [W5]
[P1] hai intake nutrition daily-total semantics easy to misuse — document + warn on same-day supersede — S  [W6]
[P1] planned_session_type vocabulary undocumented — publish canonical values; surface unknown strings — S  [W8]
[P2] Cold-start rules not documented as a six-domain policy matrix — document which domains relax and why; keep nutrition non-relaxation if intentional — M  [W14]
[P2] Date flags use --as-of, --for-date, --date for the same concept — standardize on --as-of with deprecated aliases — S
[P2] 28-day windows + cold-start note strings duplicated — factor real window constants; interpolate central 14-day value into notes — S
[P2] Reproject determinism overstated if timestamps count — document timestamp volatility or derive deterministic replay timestamps — S  [W19]
[P2] Migration gap detection misses absent lower migrations — validate contiguous applied set in migrate + doctor — S  [W20]
[P2] daily-plan-synthesis allowed-tools may block its own examples — broaden allowed-tools or rewrite examples — S  [W16]
[P2] README/tour/integration docs need final post-fix sweep — rewrite after behavior changes land — S  [W9]
```

### 7.4 Final sequencing

Per Codex r2's recommendation, the internal audit's sequence
is broadly right with these deltas:

1. **W11 (JSON-arg + main guard)** — 6 call sites: propose,
   review-record, review-schedule, pull, clean, synthesize drafts
   (already guarded). Smallest blast-radius P0.
2. **W12 (review-outcome validation)** — data integrity P0.
3. **W10 + W4 (proposal-completeness gate + hai daily honesty)**
   — code change first; docs/`--auto` second. The locking test at
   `safety/tests/test_cli_daily.py:272-304` must flip.
4. **W2 (gaps refusal)** — small, removes silent agent footgun.
5. **W3 + W18 (drift validator + reporting skill fix)** — safety
   net before more skill changes.
6. **W7 (default `--base-dir`)** — UX win; coordinate with W11 so
   path/error reporting stays consistent.
7. **W1 (reproject FK)** — workaround exists, demoted from P0.
8. **W13 (bundle-only refusal)** — determinism-boundary leak.
9. **W15 (cmd_propose dual-write contract)** — second truth-fork.
10. **W17 (expert-explainer privacy)** — privacy-boundary cleanup.
11. **W5 (intervals.icu default)** — bundle with W9 README pass.
12. **W6 (nutrition supersede warning)** — light touch.
13. **W8 (planned_session_type vocabulary)** — after W3.
14. **W14 (cold-start matrix doc)** — P2 architecture cleanup.
15. **W16 (synthesis skill allowed-tools)** — covered by W3.
16. **W19 (reproject determinism docs)** — small.
17. **W20 (schema gap detection)** — small.
18. **W9 (README rewrite)** — final pass; reflects everything above.

### 7.5 Acceptance criteria for v0.1.6

Unchanged from §4, plus:

- Codex r2's 19-item punch list is fully triaged into either
  "fixed in this release" or "deferred to v0.1.7 with rationale."
- W3's drift validator runs in CI and reports zero drifts.
- The tests that LOCK broken behaviour (B1's
  `test_cli_daily.py:272-304`) have been flipped to LOCK the
  fixed invariant.
- No `cmd_*` handler can produce an uncaught Python traceback for
  any combination of CLI args.
