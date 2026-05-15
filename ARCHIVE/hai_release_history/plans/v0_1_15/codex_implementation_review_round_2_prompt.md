# Codex Implementation Review — v0.1.15 (D15 IR round 2)

> **Why this round.** D15 IR round 1 returned `SHIP_WITH_FIXES` with
> 6 findings (`F-IR-01` .. `F-IR-06`). All 6 AGREED + applied in
> commit `9e113b4` (single fix-batch commit). Round 2 audits whether
> the fixes actually close their target findings, whether the F-IR-02
> centralised guard refactor introduced any second-order issues, and
> whether the suite + gates remain green.
>
> **Empirical norm:** round 2 typically lands at 1-3 findings (5 → 2
> → 1-nit substantive-cycle halving). Recommend close-in-place if
> finding count ≤ 1 and severity ≤ nit/acceptance-weak; otherwise
> round 3.
>
> **Phase 3 still held.** W-2U-GATE recorded session does NOT fire
> until IR closes SHIP / SHIP_WITH_NOTES.
>
> **You are starting fresh.** This prompt and the artifacts it cites
> are everything you need; do not assume context from a prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd                         # /Users/domcolligan/health_agent_infra
git branch --show-current   # main
git log --oneline -3        # top: 9e113b4 (IR round 1 fixes); then
                            # 90f666e (IR round 1 prompt); then
                            # 0fd5179 (W-E)
git status                  # clean (or maintainer's untracked
                            # anthropic_personal_guidance_report.md)
```

The dual-repo discriminator (stale checkout HEAD `2811669` under
`/Users/domcolligan/Documents/`) still applies.

---

## Step 1 — Read orientation artifacts (in order)

1. **`reporting/plans/v0_1_15/codex_implementation_review_response.md`**
   — round 1's findings catalog (6 items).
2. **`reporting/plans/v0_1_15/codex_implementation_review_response_response.md`**
   — maintainer's per-finding triage. AGREED + applied for all 6.
3. **`reporting/plans/v0_1_15/PLAN.md`** — cycle contract (round-4
   final). §2.B / §2.C / §2.D / §2.E are the surfaces the fixes
   touched.
4. **The fix-batch commit diff:**

   ```bash
   git diff 90f666e..9e113b4 -- src/ verification/
   git diff 90f666e..9e113b4 -- reporting/plans/v0_1_15/PLAN.md \
       reporting/plans/tactical_plan_v0_1_x.md \
       reporting/docs/agent_cli_contract.md \
       verification/tests/snapshots/
   ```

   14 files changed, 809 insertions, 56 deletions. Source surface:
   `cli.py` (F-IR-02 helper extraction + `hai daily` flag),
   `core/config.py` (F-IR-03 threshold defaults),
   `core/intake/presence.py` (F-IR-01 nosec + F-IR-03 threshold
   loading), `domains/nutrition/classify.py` (F-IR-06 docstring),
   `skills/nutrition-alignment/SKILL.md` (F-IR-06 skill update),
   `PLAN.md` + `tactical_plan_v0_1_x.md` (F-IR-05 prose).

---

## Step 2 — Audit questions

### Q-IR-R2.1 — F-IR-01 bandit gate close

**Q-IR-R2.1.a** Run `uvx bandit -ll -r src/health_agent_infra` and
confirm 0 medium/high findings (was 2 medium B608 in round 1). The
maintainer applied two `# nosec B608` annotations at
`core/intake/presence.py:154,167` with the same constant-placeholder
rationale used in `core/target/store.py:218,359`. Are the annotations
narrow (suppressing only the f-string SQL line, not the broader
function) and is the comment justification accurate?

**Q-IR-R2.1.b** Are there any OTHER bandit findings (low confidence,
out-of-`-ll`-scope) that the round-1 fix surfaced as collateral?
Spot-check the unsuppressed-warning count.

### Q-IR-R2.2 — F-IR-02 daily-orchestrator guard

**Q-IR-R2.2.a** Verify the centralised helper at
`cli.py:_f_pv14_csv_canonical_guard` (lines 159-204 post-fix) is
invoked by both `cmd_pull` AND `_daily_pull_and_project`. The helper
takes a `command_label` kwarg so the refusal message names the right
surface.

**Q-IR-R2.2.b** The daily orchestrator catches the new
`_DailyPullRefusal` exception in `_run_daily` BEFORE
`(GarminLiveError, IntervalsIcuError)`. Verify the catch order is
correct (the refusal is a custom exception not inheriting from
`RuntimeError` or the live-pull error classes — should not collide).

**Q-IR-R2.2.c** The daily report shape on refusal is
`{"stages": {"pull": {"status": "refused", "reason": "F-PV14-01: ..."}},
"overall_status": "refused"}`. Is the report shape inspectable for
agents that drive `hai daily` programmatically? Verify the JSON
emit on stderr/stdout matches the expected pattern (the test
`test_hai_daily_csv_against_canonical_db_refused_no_sync_row`
asserts `payload.get("overall_status") == "refused"` post-stdout-
parse).

**Q-IR-R2.2.d** The `--allow-fixture-into-real-state` flag is now on
`hai daily` parser too. Verify capabilities-manifest updated and
agent_cli_contract.md regenerated. Run
`uv run hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md`
expecting clean diff.

**Q-IR-R2.2.e** F-IR-02 disposition response named-deferred the
broader symmetry rule (asymmetric `--db-path` / `--base-dir`
override) to v0.1.16-or-later. Is the named-defer documented in a
place a future cycle author would find (e.g., in
`pre_implementation_gate_decision.md` follow-ups, or in
`tactical_plan_v0_1_x.md` v0.1.16/17 row)? If not, the deferral risks
falling off the planning surface.

**Q-IR-R2.2.f** Three new tests added to
`test_w_pv14_01_csv_isolation.py`. Do they cover the full
positive/negative space?
  - Refused: `test_hai_daily_csv_against_canonical_db_refused_no_sync_row` ✓
  - Allow flag: `test_hai_daily_csv_with_allow_fixture_flag_passes_guard`
  - Explicit --db-path: `test_hai_daily_csv_with_explicit_db_path_passes_guard`

  Missing: explicit demo-marker active path (test exists for
  `hai pull` but not `hai daily`). Acceptance gap or out-of-scope?

### Q-IR-R2.3 — F-IR-03 thresholds wiring

**Q-IR-R2.3.a** `core/config.py:DEFAULT_THRESHOLDS["gap_detection"]`
adds two new keys:
- `presence_partial_day_cutoff_hour: 18`
- `presence_partial_day_expected_meals: 3`

  Are the defaults consistent with the module constants in
  `presence.py:DEFAULT_CUTOFF_HOUR=18` / `DEFAULT_EXPECTED_MEALS=3`?
  (They should be, but the two-source-of-truth shape is a future
  drift risk.)

**Q-IR-R2.3.b** `presence.py:_load_partial_day_thresholds()` defends
against any load/coerce failure with a bare `except Exception`. Is
the bare-except too broad — would a `KeyError` / `TypeError` /
`coerce_int` `ValueError` all warrant fall-through to defaults?

**Q-IR-R2.3.c** `compute_presence_block` signature changed:
`cutoff_hour` / `expected_meals` are now `Optional[int]` defaulting
to `None`. Existing callers that passed positional defaults
(no test in the repo does this, but spot-check) — would they
regress? Use `git grep compute_presence_block` to enumerate callers.

**Q-IR-R2.3.d** Test
`test_compute_presence_block_honours_threshold_override`
monkeypatches `core.config.DEFAULT_THRESHOLDS` directly. Is the
monkeypatch surface stable across the cycle (i.e., does
`load_thresholds()` actually read from `DEFAULT_THRESHOLDS` when no
user override is configured)?

### Q-IR-R2.4 — F-IR-04 migration preservation test

**Q-IR-R2.4.a**
`test_migration_025_preserves_pre_existing_target_rows_byte_stable`
seeds three rows mirroring the maintainer's live state, applies
migration 025, asserts byte-stable equality on every column.
Verify the seed shape matches the actual schema (no missing columns
that would cause an INSERT fail).

**Q-IR-R2.4.b** Index-existence assertion checks 3 indexes from
migration 020. Codex round 1 also suggested `EXPLAIN QUERY PLAN`
verification — the maintainer named-deferred that as a heavier
test refactor. Is index-name-existence sufficient for the round-2
verdict, or should the query-plan check be a blocker?

### Q-IR-R2.5 — F-IR-05 prose cleanup

**Q-IR-R2.5.a** Codex round 1 named 5 lines in the v0.1.15 PLAN +
tactical with stale "024" references. The maintainer fixed 4 (PLAN
:149, :184, :192; tactical :605); preserved 2 as historical
provenance (PLAN :147 narrating the renumber; PLAN :370 round-4-
close provenance). Verify the preservation choices are accurate
(historical / provenance-only) and don't introduce reader confusion.

**Q-IR-R2.5.b** Are there OTHER stale "024" references in the W-C
context that the round-1 audit missed? Run
`grep -n "migration 024" reporting/` and audit each match for
historical-vs-active context.

### Q-IR-R2.6 — F-IR-06 enum documentation

**Q-IR-R2.6.a** `domains/nutrition/classify.py` docstring now
documents the `insufficient_data` enum value + its W-D arm-1
trigger. Verify the documentation paragraph is accurate (the
short-circuit fires when `is_partial_day=True` AND
`target_status in ("absent", "unavailable")`).

**Q-IR-R2.6.b** The skill at `nutrition-alignment/SKILL.md` action
matrix gains an `insufficient_data` row. Codex round 1 noted the
row is unreachable in normal flow because the policy forced-action
path (`defer_decision_insufficient_signal`) fires first via Step 1.
Is the skill prose's note about the unreachability accurate?

**Q-IR-R2.6.c** Are there other audit-visible contract surfaces
that name the `nutrition_status` enum and would benefit from the
`insufficient_data` addition? E.g., `reporting/docs/architecture.md`
nutrition section, persona-runner expectations, schema validators.

### Q-IR-R2.7 — Cross-cutting

**Q-IR-R2.7.a Ship gates re-run.** Confirm:

```bash
uv run pytest verification/tests -q          # expect 2629 pass, 3 skipped
uvx mypy src/health_agent_infra              # expect Success
uvx bandit -ll -r src/health_agent_infra     # expect 0 medium/high
uv run hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md  # expect identical
```

**Q-IR-R2.7.b Provenance re-check.** Spot-verify the new citations
in `codex_implementation_review_response_response.md`:
- `cli.py:159-204` for `_f_pv14_csv_canonical_guard` — verify
  the function lives at this range post-fix.
- `core/target/store.py:218,359` for the constant-placeholder
  rationale precedent — verify both lines have `# nosec B608`.
- `presence.py:154,167` for the new nosec annotations — verify both
  lines exist and have the right rationale comment.

**Q-IR-R2.7.c Second-order regressions.** The F-IR-02 helper
extraction moved logic from inline (in `cmd_pull`) to a shared
helper. Did any other cli.py call site that touched `cmd_pull` /
`_daily_pull_and_project` need updating but was missed?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_15/codex_implementation_review_round_2_response.md`:

```markdown
# Codex Implementation Review — v0.1.15 (Round 2)

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES
**Round:** 2

## Round-1 finding closure verification

| Finding | Closure | Rationale |
|---|---|---|
| F-IR-01 | CLOSED / CLOSED_WITH_RESIDUAL / OPEN | … |
| F-IR-02 | … | … |
| F-IR-03 | … | … |
| F-IR-04 | … | … |
| F-IR-05 | … | … |
| F-IR-06 | … | … |

## New round-2 findings (if any)

### F-IR-R2-01. <short title>
**Q-bucket:** Q-IR-R2.X.Y
**Severity:** correctness-bug | security | scope-mismatch | provenance-gap | acceptance-weak | nit
**Reference:** <commit SHA / file:line>
**Argument:** …
**Recommended response:** …

## Per-W-id verdicts

(unchanged from round 1 unless a regression surfaced)

## Closure recommendation

Close in place / round 3 / SHIP_WITH_NOTES.
```

---

## Step 4 — Verdict scale

(Same as round 1 — see `codex_implementation_review_prompt.md`
Step 4.)

For round 2, recommend **close-in-place** if:
- Finding count ≤ 1
- Severity ≤ nit / acceptance-weak
- All round-1 findings verified CLOSED or CLOSED_WITH_RESIDUAL

Otherwise **round 3** with the same fix-and-verify cycle.

---

## Step 5 — Out of scope

Same as round 1. Specifically:
- Phase 3 W-2U-GATE recorded session.
- RELEASE_PROOF / REPORT (post-Phase-3).
- PyPI publish.
- Strategic/tactical plan content beyond the F-IR-05 stale-prose deltas.
- The named-deferrals (broader symmetry rule per F-IR-02 disposition;
  EXPLAIN QUERY PLAN per F-IR-04 disposition) — both have
  v0.1.16/v0.1.17 destinations.

---

## Step 6 — Cycle pattern

```
D14 plan-audit (rounds 1-4) ✓
Phase 0 (D11) ✓
Pre-implementation gate ✓
Phase 1 + 2 implementation ✓ 6 commits
D15 IR round 1 ✓ (SHIP_WITH_FIXES, 6 findings, all AGREED + applied)
D15 IR round 2 ← you are here
  → SHIP_WITH_FIXES → maintainer + new commits → round 3
  → SHIP / SHIP_WITH_NOTES → proceed to Phase 3
Phase 3 W-2U-GATE recorded session (the named foreign-user candidate)
  → RELEASE_PROOF + REPORT
  → version bump 0.1.14.1 → 0.1.15
  → PyPI publish
```

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_15/codex_implementation_review_round_2_response.md`
  (new) — your findings.

**No code changes.** Maintainer applies any agreed fixes.
