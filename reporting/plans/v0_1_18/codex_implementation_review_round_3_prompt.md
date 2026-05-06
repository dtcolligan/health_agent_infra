# Codex Implementation Review — v0.1.18 (D15 IR round 3)

> **Why round 3.** R2 closed SHIP_WITH_FIXES with 2 findings:
> F-IR-R2-01 (deep-probe `check_auth_intervals_icu` outcomes still
> without `next_action` — concrete-command paths CAUSE_2_CREDS +
> NETWORK), and F-IR-R2-02 (release-summary surface propagation gap
> across 7 stale citations). Both accepted; both fixed in fix-and-
> reland-2 commit. Per-finding triage + post-fix verification trail
> in `codex_implementation_review_round_2_response_response.md`.
>
> **R3's job:** narrow verification per Codex's R2 closure
> recommendation: "one narrow R3 pass focused on the deep-probe
> branch, docs propagation, and stamped gate counts."
>
> Specifically:
>
> 1. **F-IR-R2-01 closure.** Deep-probe `next_action` correctly
>    emitted for CAUSE_2_CREDS + NETWORK; correctly absent for
>    CAUSE_1_CLOUDFLARE_UA + OTHER (the prose-only-by-design pair).
>    The 4 new regression tests cover both positive and negative
>    cases.
> 2. **F-IR-R2-02 closure.** The 7 enumerated stale surfaces all
>    moved in lockstep; no NEW provenance drift introduced.
> 3. **Stamped gate counts.** RELEASE_PROOF §2 + CHANGELOG + AUDIT +
>    current_system_state all show **2733 passed, 5 skipped** post-
>    fix-and-reland-2. The +50-tests-vs-v0.1.17 claim
>    (W-OB-2: 6, W-OB-3: 8, W-OB-5: 21, W-OB-7: 10 = 45 + auxiliary)
>    arithmetically matches.
> 4. **No new scope creep.** Fix-and-reland-2 touched 8 files +
>    2 new (per response_response §"Files modified" table); no AGENTS.md
>    edits; no new W-id; no PLAN-level scope expansion.
>
> **Settling shape so far:** R1 4 → R2 2 → R3 expected 0-1.
> AGENTS.md empirical norm `5 → 2 → 1-nit`; v0.1.18 tracks this
> exactly. R3 verdict expected SHIP or SHIP_WITH_NOTES close-in-
> place. SHIP_WITH_FIXES at R3 would be a surprise (R4 budget not
> reserved).
>
> **What's NOT in scope for R3:**
>
> - The 4 R1 findings (settled at R1 fix-and-reland).
> - The 2 R2 findings (settled at fix-and-reland-2).
> - Any new W-id-class scope.
> - The maintainer's manual TTY ship gate (RELEASE_PROOF §3 — fires
>   AFTER R3 closes).

---

## Step 0 — Confirm you're in the right tree

```bash
pwd                                          # /Users/domcolligan/health_agent_infra
git branch --show-current                    # main
git log --oneline 9c651da..HEAD              # expect 13 commits: 11 R1+ship + 1 R1-fix + 1 R2-fix
git status                                   # clean (uv.lock pre-existing untouched)
```

Top of `git log` should show:
```
<sha>  fix(IR-R2): close 2 findings — deep-probe next_action (F-IR-R2-01) + release-summary surface sweep (F-IR-R2-02); 2733 pass / 5 skipped
4de4306 fix(IR-R1): close 4 findings ...
aa418d5 release(v0.1.18): ship-prep ...
... (rest of cycle)
```

If anything mismatches, stop and surface.

---

## Step 1 — Read the R2 fix-and-reland artifacts

In order:

1. **`reporting/plans/v0_1_18/codex_implementation_review_round_2_response.md`**
   — R2 findings (your prior input).
2. **`reporting/plans/v0_1_18/codex_implementation_review_round_2_response_response.md`**
   — maintainer triage + per-finding fix description.
3. **The R2 fix-and-reland diff:**

   ```bash
   git diff 4de4306..HEAD -- src/ verification/ reporting/docs/ \
       AGENTS.md AUDIT.md CHANGELOG.md \
       reporting/plans/v0_1_18/RELEASE_PROOF.md \
       reporting/plans/v0_1_18/REPORT.md
   ```

4. **`reporting/plans/v0_1_18/RELEASE_PROOF.md` §2** — re-stamped
   ship-gate counts (2729 → 2733).

---

## Step 2 — R3 audit questions

### Q-R3-01. F-IR-R2-01 closure verification

- **Q-R3-01.1.** `core/doctor/checks.py` deep-probe failure branch:
  CAUSE_2_CREDS sets `next_action.command == "hai auth intervals-icu"`;
  NETWORK sets `next_action.command == "hai doctor"`. Verify both
  by inspection.
- **Q-R3-01.2.** CAUSE_1_CLOUDFLARE_UA + OTHER paths intentionally
  omit `next_action`. Verify the test surface
  (`test_doctor_next_action.py`) has explicit negative coverage:
  `test_auth_intervals_icu_deep_probe_cause_1_stays_prose_only` +
  `test_auth_intervals_icu_deep_probe_other_stays_prose_only`.
- **Q-R3-01.3.** Manifest-consistency invariant: the 2 newly-emitted
  commands (`hai auth intervals-icu`, `hai doctor`) were already in
  `_NEXT_ACTION_REGISTRY` post-R1. No new registry rows needed for
  R2; verify the manifest-consistency test still green.

### Q-R3-02. F-IR-R2-02 closure verification

For each of the 7 surfaces R2 enumerated:

- **Q-R3-02.1.** `agent_integration.md:27` no longer says "leads
  with `hai init --guided`"; now describes bare `hai init` +
  W-OB-2 auto-promotion + opt-outs.
- **Q-R3-02.2.** `CHANGELOG.md` W-OB-1 entry no longer recommends
  `hai init --guided` as the primary form; rewritten to bare
  `hai init` with R1 fix-and-reland callout.
- **Q-R3-02.3.** `RELEASE_PROOF.md:18` (W-OB-1 row) no longer says
  "README already shows `hai init --guided`"; updated.
- **Q-R3-02.4.** `RELEASE_PROOF.md:20` (W-OB-3 row) reflects 8
  tests + primitive readiness logic, not 6 tests + auth/intent
  status logic.
- **Q-R3-02.5.** `RELEASE_PROOF.md:23` (W-OB-5 row) reflects 11-
  command registry + 9 doctor check paths (including R1+R2 adds),
  not 9-command + 5 checks.
- **Q-R3-02.6.** `REPORT.md` §6 "W-OB-5 registry exhaustiveness"
  is marked CLOSED; "concrete command vs prose" rule codified.
- **Q-R3-02.7.** `current_system_state.md` v0.1.18-shipped section
  W-OB-1 + W-OB-5 paragraphs reflect post-R1+R2 state.

### Q-R3-03. Stamped gate counts consistency

- **Q-R3-03.1.** RELEASE_PROOF §2 "Full pytest suite (narrow gate):
  2733 passed, 5 skipped" matches CHANGELOG "Full suite at v0.1.18
  ship: 2733 passed, 5 skipped" + AUDIT "2733 pass / 5 skipped" +
  current_system_state "2733 passed, 5 skipped".
- **Q-R3-03.2.** Per-W-id test counts: W-OB-2: 6, W-OB-3: 8, W-OB-5:
  21, W-OB-7: 10. Total +45 vs. v0.1.17. Sum: 6+8+21+10 = 45 ✓.
- **Q-R3-03.3.** RELEASE_PROOF §2 R2 closure callout cites all 4
  R1 closures + 2 R2 closures correctly.

### Q-R3-04. No new scope creep

- **Q-R3-04.1.** `git diff 4de4306..HEAD --stat -- src/` should
  show only `core/doctor/checks.py` modified (the deep-probe
  branch). No unintended source changes.
- **Q-R3-04.2.** `git diff 4de4306..HEAD --stat -- verification/`
  should show only `test_doctor_next_action.py` modified (4 new
  tests). No unintended test changes.
- **Q-R3-04.3.** `git diff 4de4306..HEAD -- AGENTS.md` should be
  empty (no governance edits in R2 fix-and-reland-2).
- **Q-R3-04.4.** No new W-id introduced; no PLAN.md scope additions.

### Q-R3-05. Manifest stability

- **Q-R3-05.1.** `hai capabilities --json` byte-stable against
  `verification/tests/snapshots/cli_capabilities_v0_1_13.json`
  (R2 didn't change the manifest).
- **Q-R3-05.2.** `reporting/docs/agent_cli_contract.md` byte-stable
  against `hai capabilities --markdown` output.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_18/codex_implementation_review_round_3_response.md`:

```markdown
# Codex Implementation Review — v0.1.18 (D15 IR round 3)

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES
**Round:** 3

## Verification summary
- Tree state: 13 commits since v0.1.17 (`9c651da..HEAD`)
- Both pytest gates: <stamped — expect 2733 passed, 5 skipped>
- Static gates: <stamped>

## R2 closure verification

| Finding | Closure status | Note |
|---|---|---|
| F-IR-R2-01 (deep-probe next_action) | CLOSED | CAUSE_2_CREDS + NETWORK emit; CAUSE_1 + OTHER prose-only by design + negative tests |
| F-IR-R2-02 (release-summary sweep) | CLOSED | 7 surfaces moved in lockstep |

## Findings (R3)

(Or "no findings" — preferred verdict path is SHIP / SHIP_WITH_NOTES.)

## Closure recommendation

(Verdict + named must-fix list (if any). Ratifies Codex's R2 prediction
of "narrow R3 pass" settling clean.)
```

If R3 closes with no findings: SHIP. If 1 nit-class finding:
SHIP_WITH_NOTES close-in-place. SHIP_WITH_FIXES at R3 would be
surprising.

---

## Step 4 — Verdict scale

- **SHIP** — push origin/main + PyPI publish (post manual TTY gate).
- **SHIP_WITH_NOTES** — same as SHIP; named follow-ups carry to v0.1.19.
- **SHIP_WITH_FIXES** — fix-and-reland-3; would require R4 budget
  reservation.
- **DO_NOT_SHIP** — only on a correctness/security bug.

---

## Step 5 — Out of scope

- The 4 R1 findings (settled at R1 fix-and-reland).
- The 2 R2 findings (settled at R2 fix-and-reland-2).
- Any new W-id scope.
- The maintainer's manual TTY ship gate (RELEASE_PROOF §3 — fires
  AFTER R3 closes).
- v0.1.19 / v0.2.0 scope.
- AGENTS.md governance edits (none in R2 fix-and-reland-2; should
  be none in any future R3+).

---

## Step 6 — Cycle pattern (R3 placement)

```
D14 ✓ (R1+R2 close-in-place)
Phase 0 ✓
Implementation ✓
D15 IR R1 ✓ (4 findings → fix-and-reland)
D15 IR R2 ✓ (2 findings → fix-and-reland-2)
D15 IR R3 ← you are here
  → SHIP / SHIP_WITH_NOTES → maintainer manual TTY gate → PyPI publish
  → SHIP_WITH_FIXES (unlikely) → R4
RELEASE_PROOF.md + REPORT.md ✓ (re-stamped post-R2 fix)
```

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_18/codex_implementation_review_round_3_response.md`
  (new) — your findings.
- `reporting/plans/v0_1_18/codex_implementation_review_round_4_prompt.md`
  (only if R3 verdict requires R4 — surprising).

**No code changes. No source commits.** Maintainer applies any R3
fixes; you do not edit source directly.
