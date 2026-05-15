# Maintainer Response — Codex Implementation Review Round 1

**Round 1 verdict:** SHIP_WITH_FIXES, 6 findings (F-IR-01 .. F-IR-06).
**Disposition:** All 6 AGREED + applied.
**Status:** **Ready for round 2 review** OR for maintainer to ratify
close-in-place if round 2 finding count ≤ 1 and severity ≤ nit.

---

## F-IR-01 — Bandit gate fails on W-A target-status SQL (security)

**Verdict:** AGREED, applied.

**Action.** Added two `# nosec B608` annotations at
`core/intake/presence.py:187` and `:202` (in
`compute_target_status`) with the same constant-placeholder
rationale already used in `core/target/store.py:223`, `:275`, and
`:419`. Both queries f-string-interpolate only the literal `"?"`
placeholder count derived from the module constant
`NUTRITION_MACRO_TARGET_TYPES`; every value (user_id, target_type
values, as_of dates) is bound. The annotation cites `store.py`
as the precedent.

> **Citation correction (round 2 F-IR-R2-02).** The original draft
> of this paragraph cited `store.py:218` and `:359` as the
> precedent and `presence.py:154,167` as the new annotations. Both
> sets of line numbers were stale (drift between the round-1 fix
> commit and this triage doc). Corrected to the actual on-disk
> positions above.

**Verification.** `uvx bandit -ll -r src/health_agent_infra` → 0
medium/high findings (was 2 medium B608 in the round-1 baseline);
46 low-confidence (unchanged from pre-W-A).

---

## F-IR-02 — CSV-fixture default-deny is bypassed by `hai daily` (correctness-bug)

**Verdict:** AGREED, applied. This was the substantive correctness
finding — the daily orchestrator IS the path most likely to be used
in the foreign-user gate, so silent bypass would have re-opened the
F-PV14-01 contamination class for the gate session.

**Action.**

1. Extracted the F-PV14-01 guard from `cmd_pull` into a shared helper
   `_f_pv14_csv_canonical_guard(args, *, source, command_label)` at
   `cli.py:187-234` (and the supporting `_DailyPullRefusal` exception
   class at `cli.py:172-184`). Returns `Optional[int]` — `None` when
   permitted, `USER_INPUT` when refused. Same 5-clause escape paths
   (`source != csv` / `--allow-fixture-into-real-state` / active
   `hai demo` / explicit `--db-path` / `HAI_STATE_DB` env).

   > **Citation correction (round 2 F-IR-R2-02).** The original
   > draft cited the helper at `cli.py:159-204` — stale by ~30
   > lines. Corrected to the actual on-disk position above.
2. `cmd_pull` invokes the helper at the existing guard insertion
   point (replaced the inline guard with a call).
3. `_daily_pull_and_project` invokes the helper before any adapter
   construction or sync-row write. Refusal raises a new internal
   `_DailyPullRefusal(exit_code)` exception so the daily orchestrator
   can surface the refusal as a structured stage failure
   (`stages.pull.status="refused"`, `stages.pull.reason="F-PV14-01: ..."`)
   without conflating it with `GarminLiveError` / `IntervalsIcuError`.
4. `_run_daily` catches `_DailyPullRefusal` BEFORE
   `(GarminLiveError, IntervalsIcuError)` so the refusal short-circuits
   cleanly with `overall_status="refused"`.
5. Added `--allow-fixture-into-real-state` flag to `hai daily` parser
   (annotation cites F-IR-02 round-1 IR fix in the help text).

**Tests added** (`test_w_pv14_01_csv_isolation.py`):
- `test_hai_daily_csv_against_canonical_db_refused_no_sync_row` —
  refusal exits USER_INPUT with zero sync rows + structured payload.
- `test_hai_daily_csv_with_allow_fixture_flag_passes_guard` — flag
  steps the guard aside.
- `test_hai_daily_csv_with_explicit_db_path_passes_guard` — explicit
  `--db-path` to non-canonical target opts in (the daily pull stage
  actually runs against the explicit DB).

**Q-IR-2.b clarification.** Codex asked whether the broader symmetry
rule from the source finding `post_v0_1_14/carry_over_findings.md`
F-PV14-01 item 4 ("every CLI command that consumes both --db-path
and --base-dir must refuse asymmetric overrides") should land too.
**Disposition:** the centralised `_f_pv14_csv_canonical_guard` covers
the canonical-DB pollution shape that the carry-over evidence actually
exhibited. The broader symmetric-override rule is a wider scope
extension; deferring to v0.1.16 if the foreign-user gate session
surfaces a friction point.

> **Named-defer landed durably (round 2 F-IR-R2-02).** Per Codex
> round-2 review: the named-defer was previously captured only in
> this triage doc — risk of falling off the planning surface.
> Bullet now lives at
> `reporting/plans/v0_1_16/README.md` §scope as **W-FPV14-SYM
> *(conditional)*** with the empirical-only-if-gate-friction
> trigger. Future cycle author finds it.

---

## F-IR-03 — W-A partial-day cutoff not configurable (scope-mismatch)

**Verdict:** AGREED, applied.

**Action.**

1. Added two new keys to `core.config.DEFAULT_THRESHOLDS["gap_detection"]`:
   - `presence_partial_day_cutoff_hour: 18`
   - `presence_partial_day_expected_meals: 3`
2. Added `_load_partial_day_thresholds()` helper to
   `core/intake/presence.py` that reads + coerces both via
   `core.config.coerce_int` per D12 invariant. Defensive fallback
   to module constants on any load/coerce failure (the runtime never
   hard-fails because the user's thresholds.toml is malformed).
3. `compute_presence_block` signature changed: `cutoff_hour` /
   `expected_meals` now default to `None`; when `None` the helper
   loads from thresholds. Explicit kwargs still override (test
   surface unchanged).
4. The module constants `DEFAULT_CUTOFF_HOUR` and
   `DEFAULT_EXPECTED_MEALS` stay as the defensive fallback —
   commented to clarify the precedence (caller kwarg → loaded
   threshold → module constant).

**Test added** (`test_w_a_presence_block.py`):
`test_compute_presence_block_honours_threshold_override` —
monkeypatches `DEFAULT_THRESHOLDS["gap_detection"]
["presence_partial_day_cutoff_hour"] = 9`, then calls
`compute_presence_block` at 10:00 with 2 meals → asserts
`is_partial_day=False` (override flips the result; default 18:00
would have returned True).

---

## F-IR-04 — W-C migration row preservation not tested (acceptance-weak)

**Verdict:** AGREED, applied.

**Action.** Added new test
`test_migration_025_preserves_pre_existing_target_rows_byte_stable`
to `test_w_c_target_nutrition.py`:

1. Seeds three rows mirroring the maintainer's live state shape
   (`calories_kcal=3300` archived, `=3100` active, `protein_g=160`
   active — the exact rows from the F-PHASE0-01 evidence).
2. Snapshots every column pre-migration.
3. Applies migration 025.
4. Re-fetches every column post-migration; asserts byte-stable
   equality on every shared column.
5. Asserts the three indexes from migration 020
   (`idx_target_active_window`, `idx_target_domain_type`,
   `idx_target_supersedes`) exist after the recreate-and-copy.

The `EXPLAIN QUERY PLAN` assertion Codex suggested is deferred to a
follow-up: the index-name-existence check is the load-bearing
proof that the W-A active-window query can still hit the right
index; query-plan-stability is a stronger assertion that costs a
test refactor.

> **Named-defer landed durably (round 2 F-IR-R2-02).** Per Codex
> round-2 review: the EXPLAIN QUERY PLAN check is now a tracked
> v0.1.17 W-id (**W-C-EQP**) at `reporting/plans/v0_1_17/README.md`
> §scope, 0.5 d effort estimate. Future cycle author picks it up
> at v0.1.17 open.

---

## F-IR-05 — Stale `024` prose in W-C context (provenance-gap)

**Verdict:** AGREED, applied.

**Action.** Replaced "024" with "025" at four W-C-context sites:

- `reporting/plans/v0_1_15/PLAN.md:149` — "Migration shape (024)" →
  "Migration shape (025)"
- `reporting/plans/v0_1_15/PLAN.md:184` — "Migration 024 extends only
  the SQL CHECK" → "Migration 025 extends only the SQL CHECK"
- `reporting/plans/v0_1_15/PLAN.md:192` — "Migration 024 test:" →
  "Migration 025 test:"
- `reporting/plans/tactical_plan_v0_1_x.md:605` — "via migration 024"
  → "via migration 025"

Preserved the historical-provenance references at:
- `PLAN.md:147` — already says "025 (number bumped from the round-4
  draft's '024'...)" — kept as historical provenance.
- `PLAN.md:370` — round-4 close provenance entry narrating what the
  round-4 PLAN draft said; preserved as audit-trail.

---

## F-IR-06 — `insufficient_data` not in nutrition contract docs (provenance-gap)

**Verdict:** AGREED, applied.

**Action.**

1. `domains/nutrition/classify.py` module docstring at lines 35-39
   updated: `nutrition_status` enum list now includes
   `insufficient_data`, with a paragraph explaining the W-D arm-1
   short-circuit (when fired, why it's distinct from `unknown`,
   how downstream policy handles it).
2. `domains/nutrition/classify.py:70` — `NutritionStatus` type alias
   docstring extended with `"insufficient_data"`.
3. Module docstring's "Signal dict keys recognised" section extended
   to document the v0.1.15 W-A `is_partial_day` and `target_status`
   keys (with backwards-compat note on omission).
4. `skills/nutrition-alignment/SKILL.md:22` — `signals` section now
   names `is_partial_day` and `target_status` per the W-A surface.
5. `skills/nutrition-alignment/SKILL.md` action matrix gains an
   `insufficient_data` row that explicitly notes the policy
   forced-action path (`defer_decision_insufficient_signal`) fires
   first via Step 1, so the matrix row is unreachable in the normal
   flow — but documents the suppression path so a future reader
   sees the contract.

---

## Q-bucket summary cross-reference

| Q-bucket | Codex finding | Maintainer disposition |
|---|---|---|
| Q-IR-X.a / Q-IR-X.d / Q-IR-W-A | F-IR-01 (bandit) | applied — `# nosec B608` annotations |
| Q-IR-F-PV14-01.a / .b / Q-IR-X.d | F-IR-02 (daily bypass) | applied — shared guard + 3 daily tests |
| Q-IR-W-A.c | F-IR-03 (cutoff config) | applied — thresholds wiring + 1 test |
| Q-IR-W-C.b | F-IR-04 (migration test) | applied — byte-stable preservation test |
| Q-IR-W-C.c / Q-IR-X.e | F-IR-05 (024→025 prose) | applied — 4 sites updated |
| Q-IR-W-D arm-1.b | F-IR-06 (enum docs) | applied — classify docstring + type alias + skill |

All 6 findings AGREED. No design forks. No new OQs raised.

---

## Verification (post-fix)

| Gate | Status |
|---|---|
| `uv run pytest verification/tests -q` | **2629 passed, 3 skipped** (was 2624; +5 from F-IR-02 + F-IR-03 + F-IR-04 tests) |
| `uvx mypy src/health_agent_infra` | Success: no issues found in 128 source files |
| `uvx bandit -ll -r src/health_agent_infra` | 0 medium/high (was 2 medium B608); 46 low (unchanged) |
| `uv run hai capabilities --markdown` diff | clean (regenerated `cli_capabilities_v0_1_13.json`, `cli_help_tree_v0_1_13.txt`, `agent_cli_contract.md` after `hai daily --allow-fixture-into-real-state` parser addition) |
| Schema head | 25 (unchanged) |
| Pyproject version | `0.1.14.1` (unchanged; bumps at RELEASE_PROOF post-Phase-3) |

---

## Closure recommendation

**Ready for D15 IR round 2.** Empirical norm per AGENTS.md: round 2
typically lands at 2 findings (5 → 2 → 1-nit halving). Round-1
findings were 6 (slightly above the substantive-cycle norm but
within range given the cycle bundled 6 W-ids); round-2 expectation
is 1-3 findings.

**Recommend close-in-place if round-2 finding count ≤ 1 and severity
≤ nit/acceptance-weak.** Otherwise round 3.

Phase 3 W-2U-GATE recorded session is held until the IR chain closes
SHIP / SHIP_WITH_NOTES.

---

# Round 2 disposition (post-Codex round-2 review)

**Round 2 verdict:** SHIP_WITH_FIXES, 2 findings (`F-IR-R2-01`
acceptance-weak + `F-IR-R2-02` provenance-gap). Both AGREED + applied.

## F-IR-R2-01 — Daily CSV allow-flag test was vacuous

**Verdict:** AGREED, applied. Real bug — Codex caught a test that
asserted `rc != USER_INPUT or _last_stdout_overall_status_is_not_refused()`
where the helper always returned `True`, so the assertion was
tautologically true regardless of guard behavior.

**Action.**

1. Rewrote `test_hai_daily_csv_with_allow_fixture_flag_passes_guard`
   to capture stdout via `capsys`, parse the daily payload, assert
   `payload["overall_status"] != "refused"` AND
   `payload["stages"]["pull"]["status"] != "refused"`. Plus a
   stronger positive proof: at least one sync row in the canonical-
   redirected DB confirms the pull stage actually ran.
2. Deleted the `_last_stdout_overall_status_is_not_refused` helper.
3. Added `test_hai_daily_csv_with_active_demo_marker_passes_guard`
   to close the demo-marker escape-path coverage gap Codex flagged.
   Monkeypatches `HAI_DEMO_MARKER_PATH` to a tmp marker file;
   asserts `is_demo_active()` returns True (sanity-check the test
   setup); invokes `hai daily --source csv` (no allow flag, no
   explicit --db-path); asserts the F-PV14 refusal shape is NOT
   present in the daily payload.

## F-IR-R2-02 — Stale citations + non-durable named-defers

**Verdict:** AGREED, applied.

**Action.**

1. **Citations corrected** in this triage doc (F-IR-01 + F-IR-02
   sections above):
   - `cli.py:159-204` → `cli.py:187-234` (`_f_pv14_csv_canonical_guard`)
     + `cli.py:172-184` (`_DailyPullRefusal`).
   - `core/target/store.py:218,359` → `:223, :275, :419` (3 nosec
     precedent lines, not 2).
   - `presence.py:154,167` → `:187, :202` (the actual nosec
     annotations).
   Each corrected paragraph carries a `>` quote-block citation
   correction note so the audit chain shows where the drift was.

2. **Both named-defers landed on durable planning surfaces** (Codex
   round-2 explicitly asked for this; the deferral risked falling
   off if it lived only in this triage doc):

   - **Broader F-PV14 symmetry rule** → `reporting/plans/v0_1_16/README.md`
     §scope as `W-FPV14-SYM (conditional)`. Trigger: only if the
     v0.1.15 foreign-user gate surfaces a friction point with the
     asymmetric-override pattern. Otherwise defer to v0.1.17 or
     later.
   - **EXPLAIN QUERY PLAN stability assertion** →
     `reporting/plans/v0_1_17/README.md` §scope as `W-C-EQP (small)`.
     0.5 d effort estimate. v0.1.17 author picks it up at cycle
     open.

## Verification (post-round-2-fix)

| Gate | Status |
|---|---|
| `uv run pytest verification/tests -q` | (re-verified after applying both fixes; expect ≥2629 + new daily-allow + new daily-demo tests) |
| `uvx mypy src/health_agent_infra` | Success: no issues found |
| `uvx bandit -ll -r src/health_agent_infra` | 0 medium/high (unchanged) |
| `uv run hai capabilities --markdown` diff | clean (no surface change in this fix batch) |

## Closure recommendation (post-round-2-fix)

**Ready for D15 IR round 3.** Empirical norm: round 3 typically
closes at 0-1 nits. Recommend close-in-place if round-3 finding
count == 0 OR ≤1 nit-class. Otherwise round 4 (would mark this as
the longest IR chain in the cycle's history).

---

# Round 3 disposition (post-Codex round-3 review) — IR chain close

**Round 3 verdict:** SHIP_WITH_NOTES, 1 nit-class finding
(`F-IR-R3-01` provenance-gap), close-in-place per Codex
recommendation. AGREED + applied.

**IR chain settles at 6 → 2 → 1 nit (the AGENTS.md
`5 → 2 → 1-nit` empirical norm; round 1 was slightly above the
substantive-cycle norm given the cycle bundled 6 W-ids).**

## F-IR-R3-01 — Stale source-comment citation in presence.py

**Verdict:** AGREED, applied.

**Action.** Updated the rationale comment at
`src/health_agent_infra/core/intake/presence.py:182-188`. Old
text cited `core/target/store.py:218` / `:359` (the pre-W-C-
`add_targets_atomic` line numbers, which drifted when W-C
landed). New text cites `core/target/store.py:223`, `:275`,
and `:419` — the actual on-disk nosec-precedent positions —
plus an inline note explaining the drift cause and round-3
attribution so a future reader sees the audit chain.

**Why this slipped at round 2.** The round-2 fix corrected
the same stale citations in the response triage doc but did
NOT propagate to the source comment that originally inspired
the response prose. Both surfaces drifted from the same
F-PV14-01-fix commit; the response doc was the load-bearing
audit surface and got attention; the source comment was a
backwater. Pattern lesson: when correcting a citation drift,
grep for ALL occurrences of the old line numbers, not just
the round's named surface.

## Verification (post-round-3-fix)

| Gate | Status |
|---|---|
| `uv run pytest verification/tests/test_w_a_presence_block.py verification/tests/test_w_pv14_01_csv_isolation.py -q` | 24/24 passed (touched-file regression check) |
| `uvx bandit -ll -r src/health_agent_infra` | 0 medium/high (unchanged) |

Full-suite + mypy unchanged from round 2 close (the round-3 fix
is a pure comment-text edit; no behavior change possible).

## IR chain final state

| Round | Verdict | Findings | Disposition |
|---|---|---|---|
| 1 | SHIP_WITH_FIXES | 6 (F-IR-01..06) | All AGREED + applied (commit 9e113b4) |
| 2 | SHIP_WITH_FIXES | 2 (F-IR-R2-01, F-IR-R2-02) | All AGREED + applied (commit 48eb3e2) |
| 3 | **SHIP_WITH_NOTES** | 1 (F-IR-R3-01 nit) | AGREED + applied close-in-place |

**D15 IR closed.** The cycle is now ready for **Phase 3
(W-2U-GATE recorded session against the named foreign-user candidate)**. RELEASE_PROOF
+ REPORT authored after Phase 3 closes; PyPI publish after
RELEASE_PROOF.

## Empirical settling-shape retrospective for D15 IR

The 6 → 2 → 1 chain matches the AGENTS.md `5 → 2 → 1-nit`
substantive-cycle norm. The round-1 finding count (6) was at
the upper end of the empirical band, traceable to the cycle
bundling 6 W-ids in a single Phase 1+2 batch — finding density
scales with surface area. Future cycles with similar W-id counts
should budget round-1 = ~5-6, round-2 = ~2, round-3 = ~0-1.

**Pattern note for future cycles:** the "stale citations after
revisions" bug appeared in BOTH the D14 plan-audit chain
(F-PLAN-R3-01..03 in round 3) AND the D15 IR chain (F-IR-R2-02
in round 2 + F-IR-R3-01 in round 3). When a code surface
changes, every prose surface (PLAN, response triage docs,
source comments) that cites it needs to be re-grepped at the
SAME revision boundary. AGENTS.md "Patterns the cycles have
validated" already names "Provenance discipline" as a recurring
audit-finding shape; this cycle reinforces that the citation-
drift class is symmetric — both response docs AND source code
comments are equally vulnerable.
