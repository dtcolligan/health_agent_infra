# Codex Implementation Review — v0.1.15 (D15 IR round 3)

> **Why this round.** D15 IR round 2 returned `SHIP_WITH_FIXES` with
> 2 findings (`F-IR-R2-01` acceptance-weak + `F-IR-R2-02`
> provenance-gap). All round-1 findings (`F-IR-01..06`) were verified
> CLOSED or CLOSED_WITH_RESIDUAL. Both round-2 findings AGREED + applied
> in commit `48eb3e2` (single fix-batch).
>
> **Empirical norm:** round 3 closes substantive cycles. Per AGENTS.md
> "5 → 2 → 1-nit" shape, round 3 should land at 0-1 nits. Recommend
> close-in-place if finding count == 0 OR ≤1 nit-class.
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
git log --oneline -3        # top: 48eb3e2 (round 2 fixes); then
                            # da078a9 (round 2 prompt); then
                            # 9e113b4 (round 1 fixes)
git status                  # clean (or maintainer's untracked
                            # anthropic_personal_guidance_report.md)
```

Stale-checkout discriminator: ignore `/Users/domcolligan/Documents/`.

---

## Step 1 — Read orientation artifacts (in order)

1. **`reporting/plans/v0_1_15/codex_implementation_review_round_2_response.md`**
   — round 2's findings catalog (2 items: F-IR-R2-01 + F-IR-R2-02).
2. **`reporting/plans/v0_1_15/codex_implementation_review_response_response.md`**
   — maintainer's per-finding triage. Round-1 + round-2 disposition
   in the same doc; round-2 disposition lives below the
   `# Round 2 disposition (post-Codex round-2 review)` header.
3. **The fix-batch commit diff:**

   ```bash
   git diff da078a9..48eb3e2 -- verification/tests/test_w_pv14_01_csv_isolation.py
   git diff da078a9..48eb3e2 -- reporting/plans/v0_1_15/codex_implementation_review_response_response.md
   git diff da078a9..48eb3e2 -- reporting/plans/v0_1_16/README.md \
       reporting/plans/v0_1_17/README.md
   ```

   5 files changed, 275 insertions, 32 deletions. Source surface:
   `test_w_pv14_01_csv_isolation.py` (vacuous helper deleted +
   rewrite of allow-flag test + new demo-marker test); response
   triage doc citation corrections + round-2-disposition section;
   v0.1.16 README + v0.1.17 README named-defer landings.

---

## Step 2 — Audit questions

### Q-IR-R3.1 — F-IR-R2-01 closure verification

**Q-IR-R3.1.a** Verify `_last_stdout_overall_status_is_not_refused`
helper is gone from `verification/tests/test_w_pv14_01_csv_isolation.py`.
The vacuous-helper-then-tautological-assertion shape was the
acceptance-weak gap; deletion is the cleanest closure.

**Q-IR-R3.1.b** `test_hai_daily_csv_with_allow_fixture_flag_passes_guard`
now uses `capsys` to capture stdout, parses the daily payload, and
asserts BOTH `payload["overall_status"] != "refused"` AND
`payload["stages"]["pull"]["status"] != "refused"`. Plus a stronger
positive proof: at least one sync row in the canonical-redirected
DB. Is the assertion shape robust against the regression Codex
described (guard regresses → returns refusal payload → test should
catch)?

**Q-IR-R3.1.c** `test_hai_daily_csv_with_active_demo_marker_passes_guard`
is new. It monkeypatches `HAI_DEMO_MARKER_PATH`, sanity-checks
`is_demo_active()` returns True, then invokes `hai daily --source csv`
without the allow flag or explicit --db-path. Asserts the F-PV14
refusal shape is NOT present. Does the test correctly exercise the
demo-marker escape path through the shared `_f_pv14_csv_canonical_guard`
helper?

### Q-IR-R3.2 — F-IR-R2-02 closure verification

**Q-IR-R3.2.a** Citation corrections in
`codex_implementation_review_response_response.md`:
- `cli.py:159-204` → `:187-234` (`_f_pv14_csv_canonical_guard`) +
  `:172-184` (`_DailyPullRefusal`).
- `core/target/store.py:218,359` → `:223, :275, :419` (3 nosec
  precedent lines).
- `presence.py:154,167` → `:187, :202`.

  Verify each corrected line citation matches the on-disk position
  TODAY. Spot-check via grep.

**Q-IR-R3.2.b** Each corrected paragraph carries a `>` quote-block
"Citation correction (round 2 F-IR-R2-02)" note showing the audit
chain of what the stale citation was vs the corrected one. Is that
shape useful (shows the drift), or is it redundant with the round-2
review file?

**Q-IR-R3.2.c** Named-defer landings:
- `reporting/plans/v0_1_16/README.md` §scope adds `W-FPV14-SYM
  (conditional)` row with the empirical-only-if-gate-friction
  trigger.
- `reporting/plans/v0_1_17/README.md` §scope adds `W-C-EQP (small)`
  row with 0.5 d effort estimate.

  Verify both landings are in the right §scope tables (not just
  prose paragraphs that a future cycle author might miss). The
  v0.1.16 README's scope table is at line 13-22; v0.1.17's at line
  10-22.

**Q-IR-R3.2.d** Are there OTHER round-1 / round-2 disposition
references in the response_response.md or elsewhere that named-
deferred something to a future cycle but didn't land it on the
durable surface? Spot-check the doc for "defer" / "named-defer" /
"v0.1.16" / "v0.1.17" mentions.

### Q-IR-R3.3 — Cross-cutting

**Q-IR-R3.3.a Ship gates re-run.** Confirm:

```bash
uv run pytest verification/tests -q          # expect 2630 pass, 3 skipped
uvx mypy src/health_agent_infra              # expect Success
uvx bandit -ll -r src/health_agent_infra     # expect 0 medium/high
uv run hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md  # expect identical (no surface change in this fix batch)
```

**Q-IR-R3.3.b Second-order regressions.** The round-2 fixes touched
2 test cases and 4 documentation surfaces. No source code changes
to `cli.py` / `core/` / `domains/`. Verify the test-only change
didn't break any other existing test (the suite count went 2629 →
2630, +1 from the new demo-marker test; the rewritten allow-flag
test should still pass).

**Q-IR-R3.3.c Round-3 specific: any *new* deferrals from the
round-2 fix batch?** The fix batch was small. Did it introduce
any new "we'll defer X to v0.1.16" or "v0.1.17" notes that need
durable surfaces?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_15/codex_implementation_review_round_3_response.md`:

```markdown
# Codex Implementation Review — v0.1.15 (Round 3)

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES
**Round:** 3

## Round-2 finding closure verification

| Finding | Closure | Rationale |
|---|---|---|
| F-IR-R2-01 | CLOSED | … |
| F-IR-R2-02 | CLOSED | … |

## New round-3 findings (if any)

(Expected: 0-1 nits per the empirical norm.)

### F-IR-R3-01. <short title>
**Q-bucket:** Q-IR-R3.X.Y
**Severity:** nit / acceptance-weak / ...
**Reference:** <file:line>
**Argument:** …
**Recommended response:** …

## Per-W-id verdicts

(Carry forward from round 2 unless a regression surfaced.)

## Closure recommendation

SHIP | SHIP_WITH_NOTES | round 4.
```

---

## Step 4 — Verdict scale

Same as rounds 1 + 2. For round 3 specifically:

- **SHIP** — round 3 finds 0 issues; cycle is ship-ready for Phase 3.
- **SHIP_WITH_NOTES** — round 3 finds 1 nit-class issue that can
  defer to v0.1.16 named-fix; cycle is ship-ready.
- **SHIP_WITH_FIXES** — round 3 finds correctness or scope-mismatch
  issues that warrant a round 4.
- **DO_NOT_SHIP** — only on correctness/security bug.

For the 5 → 2 → 1-nit empirical halving, round 3 SHIP or
SHIP_WITH_NOTES (with ≤1 nit) is the natural close.

---

## Step 5 — Out of scope

Same as rounds 1 + 2:
- Phase 3 W-2U-GATE recorded session.
- RELEASE_PROOF / REPORT.
- PyPI publish.
- The two named-defers (W-FPV14-SYM in v0.1.16; W-C-EQP in v0.1.17)
  — they have destination cycles. Findings only about deferrals
  that should NOT be deferred.

---

## Step 6 — Cycle pattern

```
D14 plan-audit (rounds 1-4) ✓
Phase 0 (D11) ✓
Pre-implementation gate ✓
Phase 1 + 2 implementation ✓ 6 commits
D15 IR round 1 ✓ (SHIP_WITH_FIXES, 6 findings, all AGREED + applied)
D15 IR round 2 ✓ (SHIP_WITH_FIXES, 2 findings, all AGREED + applied)
D15 IR round 3 ← you are here
  → SHIP / SHIP_WITH_NOTES → proceed to Phase 3
  → SHIP_WITH_FIXES → maintainer + new commits → round 4 (unusual)
Phase 3 W-2U-GATE recorded session (the named foreign-user candidate)
  → RELEASE_PROOF + REPORT
  → version bump 0.1.14.1 → 0.1.15
  → PyPI publish
```

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_15/codex_implementation_review_round_3_response.md`
  (new) — your findings.

**No code changes.** Maintainer applies any agreed fixes.

If round 3 returns SHIP / SHIP_WITH_NOTES, the cycle proceeds to
Phase 3 (W-2U-GATE recorded session against the named foreign-user candidate, the named
foreign-user candidate). The IR chain is then complete for v0.1.15.
