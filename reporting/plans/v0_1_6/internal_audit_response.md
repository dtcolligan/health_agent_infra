# Internal Audit Response — health-agent-infra v0.1.5 → v0.1.6

> **Provenance.** Conducted on branch `v0.1.4-release` (15 commits ahead
> of `main`, including the entire v0.1.4 + v0.1.5 release work). Same
> audit prompt structure given to Codex; cross-validates every Codex
> finding against the current branch (Codex audited the older `main`
> snapshot from `/Users/domcolligan/Documents/health_agent_infra/`)
> and adds findings the branch divergence hid from Codex.
>
> Companion: `codex_audit_response.md` (external view, on `main`),
> `PLAN.md` (maintainer draft, on `v0.1.4-release`).

---

## Executive summary

- **Codex caught structural bugs the maintainer's plan missed.** Five of
  Codex's findings remain real on `v0.1.4-release` and are
  architecturally more serious than the UX paper-cuts the maintainer
  collected from the 2026-04-25 session. Two Codex findings (recovery
  legacy path; classify/policy hard-limited to recovery) are stale —
  fixed in v0.1.4.
- **Top three issues by severity (P0):**
  1. `hai daily` proposal gate is `bool(proposals)`, not "all expected
     domains present." A 1-of-6 plan commits as `complete`. The
     "atomic six-domain commit" framing depends on this not being
     possible. (`cli.py:3496`)
  2. `cmd_propose` / `cmd_writeback` / `cmd_review_record` /
     `cmd_review_schedule` all do bare `json.loads(Path().read_text())`
     before any try/except, AND `main()` has no top-level exception
     guard. Bad path or malformed JSON escapes as a Python traceback
     instead of a governed exit-2. (`cli.py:914, 1658, 1688, 5655-5657`)
  3. `cmd_review_record` accepts non-boolean `followed_recommendation`
     payloads. JSONL keeps the raw string (`"definitely"`); the SQLite
     projector coerces any truthy object to `1` via `_bool_to_int()`.
     The audit chain is no longer self-consistent across storage
     layers. (`cli.py:1787`, `core/state/projectors/_shared.py:20-27`)
- **Top architectural concern:** the runtime promises a single
  six-domain proposal-first contract but enforces it asymmetrically —
  cold-start relaxation is implemented in only 3 of 6 domains
  (running, strength, stress), and the proposal-completeness invariant
  is unenforced on the synthesis-side gate. The skill-vs-CLI surface
  is closer to coherent than Codex feared on `main`, but the
  invariants the docs claim aren't all enforced in code.
- **Top roadmap recommendation:** before v0.2 work, lock the v1
  invariants in code (proposal completeness gate, governed exit codes,
  schema-validated review outcomes). The current state is a runtime
  that almost-keeps its promises — operationally fine for the
  maintainer who knows the gaps, dangerous for any third party who
  takes the architecture doc at face value.

---

## Findings — validated bugs

For each: **status** (CONFIRMED / NOT_REPRODUCED / PARTIALLY_CONFIRMED
/ STALE — FIXED ON v0.1.4-release), **evidence**, **fix**,
**effort** (S/M/L), **risk** (LOW / MED / HIGH / RELEASE_BLOCKER).

### B1. `hai daily` accepts partial-domain plans as "complete" (Codex)

- **Status:** CONFIRMED.
- **Evidence:** `cli.py:3494-3502`. `present_domains` and
  `missing_expected` are computed but never used to gate. Line 3496
  is literally `gate_ok = bool(proposals)`. The `proposal_gate.status`
  emits `"complete"` for any non-zero proposal count. Tests
  (`safety/tests/test_cli_daily.py:271-303`) lock this behaviour.
- **Recommended fix:** make `gate_ok = not missing_expected` and
  surface a new `proposal_gate.status = "incomplete"` between
  `awaiting_proposals` (zero) and `complete` (all expected present).
  The `--domains` filter (which Codex correctly identifies as a
  reporting filter, not an execution scope — `cli.py:5356-5362`)
  needs to be re-purposed: either delete it, or make it the
  authoritative scope so an honest "I asked for 3 domains, I got 3"
  semantic exists.
- **Effort:** M (touches the daily orchestrator + 1–2 tests + the
  contract description).
- **Risk:** RELEASE_BLOCKER. The whole architecture story claims
  atomic six-domain commits.

### B2. `cmd_propose` / `cmd_writeback` / `cmd_review_record` / `cmd_review_schedule` crash on bad JSON (Codex)

- **Status:** CONFIRMED.
- **Evidence:**
  - `cli.py:914` — `data = json.loads(Path(args.proposal_json).read_text(...))` bare; no try/except. The error-handling block at 915–925 only handles `ProposalValidationError` after the read.
  - `cli.py:1658` — `cmd_review_schedule` same shape.
  - `cli.py:1688` — `cmd_review_record` same shape.
  - `cli.py:5655-5657` — `main()` is `args.func(args)` with no guard.
  - The drafts-json path at `cli.py:1127-1137` DOES wrap in
    `(json.JSONDecodeError, OSError)` — proves the codebase knows
    how, just hasn't applied it consistently.
- **Recommended fix:** add a small `_load_json_arg(path, *,
  arg_name)` helper that does the load + try/except + USER_INPUT
  return, and route every JSON-arg call site through it. Add a
  top-level guard in `main()` that catches `Exception`, prints
  `internal: <type>: <msg>`, returns `exit_codes.INTERNAL`.
- **Effort:** S (4 call sites + the helper + main guard + a pytest
  parametrised test).
- **Risk:** HIGH. Violates the agent contract that promises
  governed exit codes; an agent calling these would see a
  malformed shell exit.

### B3. `cmd_review_record` truth-fork: JSONL keeps raw payload, SQLite coerces to `1` (Codex)

- **Status:** CONFIRMED.
- **Evidence:** `cli.py:1787` passes
  `data["followed_recommendation"]` to `record_review_outcome()`
  with no type validation. `core/review/outcomes.py` serialises
  whatever it received into JSONL. The projector at
  `core/state/projector.py:230-270` coerces via `_bool_to_int()` /
  `_opt_bool_to_int()` from `_shared.py:20-27` — Python truthiness,
  so `"definitely"` (truthy string) → `1`.
- **Recommended fix:** validate the outcome shape before either
  write. Add `validate_review_outcome_dict(data)` in a new
  `core/writeback/outcome.py` parallel to
  `core/writeback/proposal.py`'s `validate_proposal_dict`. Reject
  with named invariants (`followed_recommendation_must_be_bool`,
  `self_reported_improvement_must_be_bool_or_null`,
  `review_event_id_required`). Wire into both the CLI handler AND
  `record_review_outcome()` for defence-in-depth.
- **Effort:** M.
- **Risk:** HIGH (data integrity — the audit chain no longer agrees
  with itself across storage layers).

### B4. `hai synthesize --bundle-only` returns `proposals: []` with no proposals gate (Codex)

- **Status:** CONFIRMED.
- **Evidence:** `cli.py:1107-1123`. The `--bundle-only` branch calls
  `build_synthesis_bundle()` directly with no proposal-count check.
  `core/synthesis.py:488-515` happily returns
  `{"snapshot", "proposals": [], "phase_a_firings": []}`. Contradicts
  `architecture.md:295-312` and `agent_integration.md` framing of
  every determinism boundary as "rejecting loudly."
- **Recommended fix:** decide explicitly. Two paths:
  1. **Keep bundle-only as a post-proposal skill seam only.** Reject
     when `proposal_log` has no rows for `(for_date, user_id)`.
  2. **Bless bundle-only as a pre-proposal inspection surface.** Add
     a `bundle.status: "no_proposals_yet"` field and document it.
  Maintainer should pick one; I'd lean (1) — bundle-only is named
  for skill-overlay use, not for inspection.
- **Effort:** S.
- **Risk:** MED.

### B5. `hai state reproject` raises FK constraint failure (maintainer's session, 2026-04-25)

- **Status:** CONFIRMED.
- **Evidence:** Reproduced this morning at
  `core/state/projector.py:1258` on `DELETE FROM proposal_log`.
  `planned_recommendation.proposal_id` references `proposal_log`
  (`migrations/011_planned_recommendation.sql:64`); reproject doesn't
  cascade. Live DB had 38 planned_recommendation rows; delete
  blocked.
- **Recommended fix:** add `class ReprojectOrphansError` in
  `core/state/projector.py`; before destructive deletes, check
  `planned_recommendation` / `daily_plan` / `x_rule_firing` row
  counts; refuse with a clear message naming the row counts and a
  `--cascade-synthesis` opt-in flag for the destructive case.
  Re-export from `core/state/__init__.py`. Wire the flag into
  `cmd_state_reproject`.
- **Effort:** M (~80 LoC change + 2 regression tests covering refusal
  + cascade-success).
- **Risk:** MED. There's a workaround (don't reproject; intake
  commands project incrementally), but the trace is opaque to a
  user who doesn't know that.

### B6. `hai intake gaps` returns misleading `gap_count: 0` without `--evidence-json` (maintainer's session, 2026-04-25)

- **Status:** CONFIRMED.
- **Evidence:** `cli.py:cmd_intake_gaps` doesn't refuse when
  `--evidence-json` is absent. `compute_intake_gaps` then sees a
  snapshot with no `classified_state` and returns `[]` per
  `core/intake/gaps.py:230-234` (the function correctly documents
  this as "caller is expected to have already built a full
  snapshot," but the CLI doesn't enforce it).
- **Recommended fix:** add a precondition check at the top of
  `cmd_intake_gaps`: if `--evidence-json` is absent, refuse with
  USER_INPUT and a clear stderr explaining why. On the OK path,
  emit `"computed": true` so callers can pattern-match.
- **Effort:** S.
- **Risk:** MED — silent agent footgun. An agent that polls gaps
  before deciding to ask the user does the wrong thing.

### B7. Schema drift: `intent-router` SKILL.md vs `hai review record` CLI (maintainer's session)

- **Status:** CONFIRMED.
- **Evidence:** Skill says `--completed 0|1`, `--domain`,
  `--recommendation-id`, `--followed-recommendation`,
  `--pre-energy-score`, `--post-energy-score`,
  `--disagreed-firing-ids`. CLI requires `--outcome-json` and
  takes `--completed yes|no`, `--pre-energy`, `--post-energy`,
  `--disagreed-firings`. Hit during this morning's session.
- **Recommended fix:** rewrite the skill's "Outcome logging"
  section to match the actual CLI (use `--outcome-json` payload +
  the override flags by their real names). Build a static drift
  validator (`scripts/check_skill_cli_drift.py`) that walks every
  SKILL.md, extracts `hai <command>` invocations from fenced code
  blocks, and cross-references each `--flag` against
  `hai capabilities --json`. Wire as a pytest test so future drift
  fails CI.
- **Effort:** S (skill text fix) + M (validator + test).
- **Risk:** LOW per occurrence, MED in aggregate (silent
  divergence accumulates).

---

## Findings — UX / friction

### F1. `hai daily` does not complete the loop on its own (maintainer's session)

- **Status:** CONFIRMED. Hits at `cli.py:3503-3514` —
  `awaiting_proposals` short-circuit when `gate_ok` is False.
- **Recommendation:** README + `hai daily --help` description
  should make explicit that the agent must invoke 6 per-domain
  skills + 6 `hai propose` calls before re-running `hai daily`.
  Optionally ship a `--auto` mode that emits the structured
  next-step hint in a stable contract field, so the agent can
  pattern-match on it without parsing prose.
- **Effort:** S (docs) + L (`--auto` mode if pursued).

### F2. Garmin live pull is unreliable; intervals.icu is the supported source (maintainer's session)

- **Status:** CONFIRMED. `hai pull --live` got 429s today from
  Garmin's mobile + portal + Cloudflare endpoints in succession.
  intervals.icu pulled cleanly.
- **Recommendation:** make `--source intervals_icu` the implicit
  default for `hai pull` and `hai daily` when no source flag is
  passed AND intervals.icu auth is configured. Update README's
  Install block accordingly.
- **Effort:** M (default-resolution change + Install rewrite + 1
  test).

### F3. `hai intake nutrition` is a daily total, not per-meal, and is not idempotent

- **Status:** CONFIRMED. Hit during today's session — had to use
  `hai intake note` as a scratchpad for lunch macros until dinner
  arrived.
- **Recommendation:** README + a stderr warning when
  `hai intake nutrition` is called for a day that already has a
  row. The warning should not block; it should make the supersede
  visible.
- **Effort:** S.

### F4. Every `hai intake *` requires `--base-dir`

- **Status:** CONFIRMED. New users hit this on first invocation.
- **Recommendation:** mirror `resolve_db_path`. Add
  `core/paths.py:DEFAULT_BASE_DIR = Path.home() / ".health_agent"`
  + `resolve_base_dir()`; make `--base-dir` optional on every
  intake / propose / review / daily / reproject subcommand.
- **Effort:** M (1 new module + ~12 argparse declarations + ~12
  handler call-sites).

### F5. `planned_session_type` vocabulary is undocumented

- **Status:** CONFIRMED. Today's session used
  `strength_back_biceps` (composed by the agent) — fine for
  narration, possibly contributing to today's strength escalation.
- **Recommendation:** grep for everywhere `planned_session_type`
  is matched in the domain classifiers, document the canonical
  vocabulary, surface via a `hai planned-session-types --json`
  read-only helper.
- **Effort:** S.

### F6. `hai review record --domain` documented but doesn't exist (Codex)

- **Status:** CONFIRMED. `hai capabilities` confirms only
  `review summary --domain` exists. Skill docs (intent-router,
  agent_integration.md) reference the wrong flag.
- **Recommendation:** strike `--domain` from the docs. Domain is
  read from the outcome-json payload (`cli.py:1689`).
- **Effort:** S.

### F7. `hai daily --domains` is a reporting filter, not an execution scope (Codex)

- **Status:** CONFIRMED. `cli.py:5356-5362` help text confirms
  this. Codex was right that the name misleads.
- **Recommendation:** rename to `--report-domains` to make the
  semantic explicit, OR (if the maintainer's true intent is
  scoped synthesis) make it actually filter `expected_domains`
  before the gate runs. Coordinate with B1.
- **Effort:** S.

---

## Findings — calibration timeline validation

> The maintainer drafted "Calibration timeline" + "Where your data
> lives" sections during the session (subsequently reset; will land
> as part of W9). Validating the windows below.

| Window | Maintainer claim | Validation |
|---|---|---|
| 1–14 | Cold-start mode; `cold_start_relaxation` softens R-coverage blocks | **PARTIALLY CONFIRMED.** `cold_start_relaxation` is implemented in `running/policy.py:233`, `strength/policy.py:269`, `stress/policy.py` only. Recovery, sleep, nutrition do NOT have an equivalent rule. The 14-day cutoff is hardcoded in those 3 domains as `history_days < 14`. |
| Day 14 | Cold-start window closes | **CONFIRMED for the 3 domains that have it.** For recovery/sleep/nutrition there's no observable transition because they don't have the relaxation rule at all. |
| 14–28 | Recovery/sleep/stress trailing-7d signals stabilise | **REASONED, not code-cited.** Plausible but not anchored to a constant. |
| Day 28 | ACWR's 28-day chronic-load denominator full; strength `volume_ratio` (7d ÷ 28d) stabilises | **CONFIRMED.** `domains/running/classify.py:178` references the 28-day window; `domains/strength/classify.py` uses `volume_ratio_7d_vs_28d_week_mean`. |
| Day 60+ | Trend bands need ≥2 cycles | **REASONED.** Plausible. |
| ~Day 90 | Steady state | **REASONED.** Pure judgment. |

**Calibration finding to add:** the asymmetry of cold-start handling
across the 6 domains is itself a v0.1.6 candidate. A user in days 1–14
sees inconsistent recommendation behaviour: running/strength/stress
get explicitly relaxed, recovery/sleep/nutrition don't. Either extend
`cold_start_relaxation` to the other 3 domains or document the
asymmetry as intentional.

---

## A. Boundary integrity

- **`hai propose`:** real hard boundary. `validate_proposal_dict()`
  (`core/writeback/proposal.py`) enforces named invariants and the
  CLI prints `invariant=<id>` on rejection (`cli.py:919`). Strong.
- **`hai synthesize`:** partially a boundary. Rejects empty proposal
  set (`core/synthesis.py:341-349`) but doesn't enforce
  proposal-completeness — see B1. Returns plain `SynthesisError` text
  rather than invariant-coded failures (Codex finding, confirmed at
  `cli.py:648-655`).
- **`hai review record`:** NOT a boundary. No schema gate. See B3.
- **`hai propose --replace`:** does enforce the canonical-leaf
  uniqueness invariant per `migration 018`. Good.
- **`main()` exception handling:** absent. Any uncaught exception
  escapes as a Python traceback. See B2.

---

## B. Skill-vs-code drift

- **Recovery skill (Codex flagged as legacy):** **STALE FINDING.**
  On `v0.1.4-release`, the recovery-readiness SKILL.md frontmatter
  allows `Bash(hai propose *)` and the body says "call `hai propose
  --domain recovery --proposal-json`." The skill emits
  `RecoveryProposal`, not `TrainingRecommendation`. Codex was
  correct about `main` but the migration landed in v0.1.4.
- **Intent-router schema drift:** REAL, see B7.
- **Other skills:** I don't have a clean drift validator on disk
  (the one I built earlier got reset). Recommend rebuilding it
  (W3 in the plan) and running it as part of the v0.1.6 acceptance
  criteria.
- **Synthesis-skill boundary:** still correctly narrow per Codex's
  observation.

---

## C. Cold-start correctness

- **Asymmetry:** `cold_start_relaxation` lives in 3 of 6 domains
  (running, strength, stress). Recovery, sleep, nutrition have no
  equivalent. Either intentional (document) or a gap (extend).
- **14-day cutoff consistency:** `history_days < 14` is hardcoded
  in three places (`domains/{running,strength,stress}/policy.py`).
  Not a shared constant. If the cutoff ever changes, three edits
  required.
- **Recommendation:** factor `COLD_START_HISTORY_DAYS = 14` into
  `core/config.py` (or thresholds.toml). Decide whether to extend
  cold-start relaxation to the other 3 domains.

---

## D. Reproject correctness

- **FK orphan bug:** REAL, see B5.
- **Determinism:** the projector iterates JSONL in file order +
  uses ISO-8601 timestamps from the input rows + no RNG. Should
  be deterministic for fixed inputs. Not exhaustively verified.
- **Recommendation:** add a property-style test that runs reproject
  twice on the same JSONL and asserts identical SQLite state
  (excluding `projected_at` columns).

---

## E. Migration safety

- 18 migrations applied (per `hai doctor`). Spot checks:
  - 011: `planned_recommendation` adds FKs to `daily_plan` +
    `proposal_log`. The reproject doesn't cascade — see B5.
  - 009: `recommendation_log.daily_plan_id` added without a
    REFERENCES constraint (SQLite ALTER TABLE limitation). Codex
    correctly flagged this as operational debt at
    `core/state/projector.py:1698-1728` (json_extract used to
    traverse the edge).
  - 015: `manual_readiness_raw` shipped (Codex's "transient" claim
    is stale).
  - 018: canonical leaf uniqueness — well-named, well-scoped.
- **No data-loss risk identified** in the migrations themselves.
- **Forward-compat concern:** if a future migration adds a column
  to a table the reproject rebuilds, the projector's INSERT
  statement must list columns explicitly (it does — verified
  spot-checked at `projector.py:153, 1344, 1858, 2053, 2111, 2228`).

---

## F. Test coverage gaps

The v0.1.6 P0 bugs above all have **zero direct test coverage**:

- **B1 (partial-domain plans):** `test_cli_daily.py:271-303` LOCKS
  the current behaviour ("subset-driven `hai daily` completion"). A
  fix here requires the test to flip from "asserts subset is fine"
  to "asserts subset is incomplete." This is intentional behaviour
  per the test, not an oversight.
- **B2 (JSON crash bugs):** no test verifies that bad-JSON / bad-path
  arguments produce USER_INPUT instead of an uncaught exception.
- **B3 (review truth-fork):** no test verifies that JSONL and
  SQLite serialisations agree on `followed_recommendation` for
  non-boolean inputs.
- **B4 (bundle-only with no proposals):** `test_cli_synthesize.py:1061-1098`
  may cover the happy path; no test confirms the rejection (or
  lack thereof) for zero-proposal bundle requests.
- **B5 (reproject FK):** no test seeds `planned_recommendation` rows
  before reproject; this is exactly the gap that let the bug ship.
- **B6 (gaps misleading zero):** no test asserts CLI refusal without
  `--evidence-json`.

Fix order: each P0 fix should ship with its regression test in the
same commit.

---

## G. Architecture observations

- **The "atomic six-domain commit" framing is half-real.** Synthesis
  IS atomic (single `BEGIN EXCLUSIVE` transaction). But the
  proposal-completeness gate is unenforced (B1) and bundle-only
  bypasses the no-proposals contract (B4). Either tighten the
  invariants OR weaken the language in `architecture.md` /
  `agent_integration.md` to match what's actually enforced.
- **Code-vs-skill boundary is generally clean.** Skills produce
  bounded enums; code produces bands and ratios; the synthesis
  layer's write-surface guard correctly rejects skill attempts to
  mutate `action`. Good.
- **Path-resolution duplication.** `DEFAULT_DB_PATH` exists, but
  `--base-dir` is required everywhere — no equivalent default.
  Asymmetry. Fixed by F4.
- **Constant duplication.** 14-day cold-start cutoff lives in three
  files. 28-day chronic-load window lives in two (running +
  strength). Both should be config constants.

---

## H. CLI ergonomics observations

- **Date-flag naming inconsistency:** `--as-of` is used by 11
  commands; `--for-date` by 1 (`hai explain`); `--date` by 1
  (`hai pull`). Three names for the same concept. Recommendation:
  rename to `--as-of` everywhere (with `--for-date` / `--date` kept
  as deprecated aliases for one release).
- **`--base-dir` required everywhere:** F4.
- **`--domains` reporting-only filter on `hai daily`:** F7.
- **Capabilities surface:** `hai capabilities --json` is well-
  structured and stable. Strong.

---

## I. Roadmap recommendations (v0.1.6 sized)

1. **Lock the v1 invariants in code** (B1, B2, B3) — the runtime
   should match its docs.
2. **Cold-start symmetry** — either extend relaxation to the other
   3 domains, or document the intentional asymmetry. The user
   experience in days 1–14 is currently inconsistent across
   domains.
3. **Skill drift validator + CI gate** — prevent W3-class
   regressions from accumulating again.
4. **`--auto` mode for `hai daily`** — make the agent-driven
   completion contract explicit so a fresh agent can pattern-match
   without prose-reading.

**Beyond v0.1.6 (named candidates, not P0/P1):**

- Per-meal nutrition intake surface (currently macros-only,
  daily-total-only).
- Skill harness completion (skill-eval still operator-driven and
  recovery-only per `safety/evals/skill_harness_blocker.md`).
- Recommendation-to-plan FK column on `recommendation_log`
  (Codex's D1 operational debt).

---

## Severity-ranked punch list for v0.1.6

```
[P0] hai daily proposal gate accepts partial-domain plans — make gate_ok = not missing_expected, status: complete|incomplete|awaiting_proposals — M
[P0] cmd_propose / cmd_writeback / cmd_review_record / cmd_review_schedule crash on bad JSON; main() has no exception guard — _load_json_arg helper + main() guard — S
[P0] cmd_review_record truth-fork between JSONL and SQLite — add validate_review_outcome_dict + invariant gates — M
[P0] hai state reproject FK orphan crash — add ReprojectOrphansError + --cascade-synthesis flag — M
[P1] hai synthesize --bundle-only bypasses no-proposals gate — refuse when proposal_log empty — S
[P1] hai intake gaps misleading zero — refuse without --evidence-json + emit computed: true — S
[P1] intent-router schema drift on hai review record — rewrite skill text + ship drift validator + pytest gate — S+M
[P1] Garmin live unreliable, intervals.icu should be default — flip default source resolution + Install rewrite — M
[P1] --base-dir required everywhere — DEFAULT_BASE_DIR + resolve_base_dir + flip 12 argparse declarations — M
[P1] README missing Calibration timeline + Where your data lives — re-add the drafted sections — S
[P1] hai daily one-liner promise misleading — README + --help description rewrite — S
[P1] hai intake nutrition daily-total semantics not surfaced — README + same-day supersede warning — S
[P1] planned_session_type vocabulary undocumented — grep + document + optional CLI helper — S
[P2] cold-start asymmetry across 6 domains — extend or document — M
[P2] 14-day + 28-day windows duplicated across files — factor to config — S
[P2] --as-of / --for-date / --date naming inconsistency — rename outliers with deprecated aliases — S
[P2] hai daily --domains is reporting filter not scope — rename or re-purpose (coordinate with B1) — S
[P2] hai review record --domain documented but missing — strike from docs — S
[P2] Cold-start cutoff isn't a shared constant — factor COLD_START_HISTORY_DAYS — S
```

---

## Things the maintainer's plan likely got wrong

- **My initial plan led with UX paper-cuts (default `--base-dir`,
  Garmin reliability, calibration docs).** Codex correctly identified
  that the structural bugs (B1, B2, B3) are more urgent. Re-sequence
  the plan so structural fixes lead.
- **My plan treated W1 (reproject FK) as P0 alongside B2/B3.** It IS
  a real bug, but the workaround (don't reproject; intake projects
  incrementally) makes it less urgent than the JSON-crash and
  truth-fork issues. Demote from "release blocker" to "should ship."
- **My plan didn't include a proposal-completeness invariant.** That's
  the biggest miss in retrospect — it's the one finding that says the
  whole architecture story is currently aspirational rather than
  enforced.
- **My plan's W4 (`hai daily` honesty) was framed as a docs problem.**
  Codex's analysis suggests it's a contract problem: the gate is
  wrong, not just the prose around it. Bump to a code change as well.

---

## Things the maintainer didn't ask about

- **Cold-start asymmetry across the 6 domains.** Days 1–14 produce
  inconsistent behaviour because only 3 domains relax. This isn't
  a bug per se but it's a coherence issue worth deciding on.
- **Date-flag naming inconsistency** (`--as-of` vs `--for-date` vs
  `--date`). Small, but affects every agent that has to learn the
  surface.
- **Hardcoded threshold constants** (14, 28) duplicated across
  files. Will bite the next time anyone tunes them.
- **The drift validator is recursive.** Once it's in CI, the next
  time someone updates a SKILL.md they get fast feedback. This
  pays for itself within ~3 PRs.
- **Codex's audit was on the wrong branch.** Worth ensuring future
  external audits are pointed at the live branch (`v0.1.4-release`
  while the v0.1.5 release branch is in flight, then `main` once
  merged). The two-checkout situation (`/Users/domcolligan/`
  vs `/Users/domcolligan/Documents/`) is an environment issue, not
  a code issue, but it cost us 15 commits of audit signal.

---

## Reconciliation: maintainer's draft `PLAN.md` vs this audit

| PLAN.md item | Action |
|---|---|
| W1 (reproject FK) | Keep as P1 (was P0). Workaround exists. |
| W2 (gaps `computed`) | Keep as P1. |
| W3 (skill drift sweep) | Keep as P1. |
| W4 (`hai daily` honesty — docs) | Upgrade to P0 — also covers code change for B1. |
| W5 (intervals.icu default) | Keep as P1. |
| W6 (nutrition supersede warning) | Keep as P1. |
| W7 (default `--base-dir`) | Keep as P1. |
| W8 (planned_session_type vocab) | Keep as P1. |
| W9 (README rewrite) | Keep as P1. |
| **NEW W10** | Proposal-completeness gate (B1). **P0**. |
| **NEW W11** | JSON-arg load + main() exception guard (B2). **P0**. |
| **NEW W12** | Review-outcome validation (B3). **P0**. |
| **NEW W13** | bundle-only no-proposals refusal (B4). **P1**. |
| **NEW W14** | Cold-start symmetry / config constants (P2 architecture cleanup). |

**Recommended new sequencing:** W11 → W12 → W10 → W2 → W3 → W7 → W1 →
W13 → W4+W5 → W6 → W8 → W14 → W9.

W11 first because it's the smallest blast-radius P0 (one helper
function, four call sites, one main() guard). W12 second because the
truth-fork is data-integrity. W10 third because it changes a tested
contract (test flips required). W2/W3/W7 are the small UX wins that
don't depend on anything. W1 next because it has a workaround. W13
covers a determinism leak. W4+W5 are paired (Install rewrite needs
both). W6/W8/W14/W9 close out.
