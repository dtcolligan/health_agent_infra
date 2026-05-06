# Codex Implementation Review — v0.1.18 (D15 IR round 2)

> **Why round 2.** R1 closed SHIP_WITH_FIXES with 4 findings (F-IR-01
> stale `agent_cli_contract.md` post version-bump → standard ship gate
> failure; F-IR-02 README quickstart pre-W-OB-2 wording; F-IR-03
> W-OB-5 missed 5 doctor checks across 7 hint paths; F-IR-04
> `next_action_hint` correctness bug saying `hai daily` when targets
> were skipped). All 4 accepted; all fixed in a single fix-and-reland
> commit. Per-finding triage + post-fix verification trail in
> `codex_implementation_review_response_response.md`.
>
> **R2's job:** verify the fix-and-reland is honest. Specifically:
>
> 1. **F-IR-01 fix landed and gates green.** `agent_cli_contract.md`
>    regenerated; both pytest gates pass; manifest version embed
>    matches `pyproject.toml`.
> 2. **F-IR-02 fix is comprehensive.** README quickstart shows bare
>    `hai init` as primary; opt-out paths documented; no stale
>    `--guided`-as-only-correct-path wording remains. Other docs
>    that cite the install sequence (e.g. `agent_integration.md`
>    line 27 was already updated in W-OB-1) stay coherent.
> 3. **F-IR-03 fix covers all concrete-command hint paths.** The 7
>    paths Codex enumerated all emit `next_action`. Did the fix
>    catch every concrete-command hint, or did the implementer miss
>    additional paths? Walk `core/doctor/checks.py` hint emissions
>    end-to-end.
> 4. **F-IR-04 fix is mathematically correct.** The new branch
>    structure handles all 8 combinations of {creds, intent, target}
>    × ready/missing. Specifically: do the corner cases
>    (`{"intent","target"}` w/o creds; `{"credentials","intent"}`;
>    `{"credentials","target"}`) route to the catch-all re-run hint
>    correctly?
> 5. **Provenance discipline across the fix-and-reland.** Are the
>    test counts in RELEASE_PROOF §2 consistent with CHANGELOG +
>    AUDIT + current_system_state? Are the file-level claims in
>    response_response §"Files modified" accurate?
>
> **Empirical norm:** R1 4 findings → R2 expected 0-2 findings per
> AGENTS.md `5 → 2 → 1-nit` settling shape. v0.1.18 is text-and-
> small-fix-only post-R1 (no scope shift; no new W-id); a clean R2
> close with verdict SHIP or SHIP_WITH_NOTES close-in-place is the
> realistic expectation.
>
> **What's NOT in scope for R2:** any of the 4 R1 findings reopened
> (settled at fix-and-reland); any new W-id-class scope (cycle is
> closed at fix-and-reland boundary); the maintainer's manual TTY
> ship gate (RELEASE_PROOF §3 — that fires AFTER R2 closes).

---

## Step 0 — Confirm you're in the right tree

```bash
pwd                                          # /Users/domcolligan/health_agent_infra
git branch --show-current                    # main
git log --oneline 9c651da..HEAD              # expect 11 commits: R1 work (10) + fix-and-reland (1)
git status                                   # clean (uv.lock pre-existing untouched)
```

Top of `git log` should now show:
```
<sha>   fix(IR-R1): close 4 findings — agent_cli_contract.md regen + README post-W-OB-2 wording + W-OB-5 broader doctor coverage (F-IR-03) + W-OB-3 next_action_hint primitive-readiness logic (F-IR-04)
aa418d5 release(v0.1.18): ship-prep ...
1711676 docs(W-OB-4b): ...
... (rest of R1 cycle commits)
```

If anything mismatches, stop and surface.

---

## Step 1 — Read the fix-and-reland artifacts

In order:

1. **`reporting/plans/v0_1_18/codex_implementation_review_response.md`**
   — R1 findings (your prior input).
2. **`reporting/plans/v0_1_18/codex_implementation_review_response_response.md`**
   — maintainer triage + per-finding fix description.
3. **The fix-and-reland diff:**

   ```bash
   git diff aa418d5..HEAD -- src/ verification/ reporting/docs/agent_cli_contract.md README.md
   git diff aa418d5..HEAD -- reporting/plans/v0_1_18/RELEASE_PROOF.md \
       reporting/plans/v0_1_18/REPORT.md CHANGELOG.md AUDIT.md \
       reporting/docs/current_system_state.md
   ```

4. **`reporting/plans/v0_1_18/RELEASE_PROOF.md` §2** — re-stamped
   ship-gate counts.
5. **`reporting/plans/v0_1_18/REPORT.md` §5.5 + §5.6** — new
   lessons-learned for the fix-and-reland.

---

## Step 2 — R2 audit questions

### Q-R2-01. F-IR-01 closure

- **Q-R2-01.1.** `reporting/docs/agent_cli_contract.md` line ~66 should
  now read `hai 0.1.18` (or wherever the version embed lives in the
  current generator output). Verify against `pyproject.toml:7`.
- **Q-R2-01.2.** `test_committed_contract_doc_matches_generated`
  passes under both narrow and broader pytest gates.
- **Q-R2-01.3.** Did the fix-and-reland ALSO bring forward any
  generator changes that pre-existed but weren't shipped? (i.e., is
  the regen byte-stable beyond the version line, or does it surface
  any drift from prior cycles?)

### Q-R2-02. F-IR-02 closure

- **Q-R2-02.1.** README "Install and quickstart" no longer instructs
  "New users on an interactive terminal should always pass `--guided`."
- **Q-R2-02.2.** Bare `hai init` is shown as the primary first-run
  command; the auto-promotion behaviour is documented inline; opt-outs
  are enumerated.
- **Q-R2-02.3.** `--guided` is retained as an explicit-force spelling,
  not the only-correct-new-user-path.
- **Q-R2-02.4.** Cross-reference sweep: are there other docs that
  cite the install-time `hai init --guided` sequence and would
  contradict the new README post-W-OB-2? `grep -rn "hai init --guided"
  reporting/docs/ README.md CHANGELOG.md` — flag any survivors that
  treat `--guided` as the required new-user path rather than the
  explicit-force spelling.

### Q-R2-03. F-IR-03 closure

- **Q-R2-03.1.** `_NEXT_ACTION_REGISTRY` extended with `hai config
  init --force` + `hai doctor` entries. Manifest-consistency test
  still green for the new entries.
- **Q-R2-03.2.** All 7 R1-enumerated hint paths now emit `next_action`:
  `check_config` (×2), `check_sources` (no-DB), `check_today` (×2),
  `check_intake_gaps` (×2). Verify by inspection of
  `core/doctor/checks.py`.
- **Q-R2-03.3.** Special-case renderers updated:
  `_render_sources`, `_render_intake_gaps`, `_render_today` now
  surface `next_action` lines. Verify by inspection of
  `core/doctor/render.py`.
- **Q-R2-03.4.** Are there ADDITIONAL hint-emitting checks the R1
  enumeration missed? Walk `grep -B1 -A1 '"hint":'
  src/health_agent_infra/core/doctor/checks.py` and judge whether
  any hint-with-concrete-command path was overlooked again.

### Q-R2-04. F-IR-04 closure

- **Q-R2-04.1.** New branch structure in `onboarding.py:run_guided_onboarding`
  reads `intent_ids` + `target_ids` lists (or `already_present`
  status) directly. Verify the logic.
- **Q-R2-04.2.** All 8 combinations of {creds, intent, target} ×
  ready/missing have a route. Specifically test the corner cases:
  - `{"intent","target"}` w/o creds → catch-all re-run hint
  - `{"credentials","intent"}` → catch-all re-run hint
  - `{"credentials","target"}` → catch-all re-run hint
  - `{"credentials","intent","target"}` → catch-all (already covered
    by existing test).
- **Q-R2-04.3.** The 2 new regression tests (`...all_targets_skipped...`
  + `...intent_skipped_but_targets_authored...`) actually fail without
  the F-IR-04 fix. Verify by mutation: temporarily revert
  `next_action_hint` to the pre-fix `intent_target.status`-based
  branching; both new tests should fail.

### Q-R2-05. Provenance discipline across the fix-and-reland

- **Q-R2-05.1.** Test counts consistent across all surfaces:
  RELEASE_PROOF §2 (2729), CHANGELOG (2729), AUDIT (2729),
  current_system_state (2729), response_response (2729).
- **Q-R2-05.2.** `response_response` §"Files modified" table accurately
  enumerates the diff: 5 source files + 2 test files + 5 doc files +
  2 cycle artifacts = 14 file-level changes (modulo path counting).
  Spot-verify each cited file actually changed in the fix-and-reland
  commit.
- **Q-R2-05.3.** Per-W-id verdict updates in `response_response`
  table: every W-OB-X marked as moving from FIX → PASS reflects the
  actual fix landing.

### Q-R2-06. New surfaces / no-scope-creep check

- **Q-R2-06.1.** Did the fix-and-reland touch any source file NOT
  enumerated in `response_response` §"Files modified"? `git diff
  aa418d5..HEAD --stat -- src/` should match the table.
- **Q-R2-06.2.** Did the fix-and-reland introduce any new W-id, new
  acceptance items beyond R1 finding closures, or new scope? Should
  be no — the cycle is closed at fix-and-reland; only the 4 R1
  findings should land.
- **Q-R2-06.3.** Did the fix-and-reland change any AGENTS.md
  governance? Should be no.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_18/codex_implementation_review_round_2_response.md`:

```markdown
# Codex Implementation Review — v0.1.18 (D15 IR round 2)

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES
**Round:** 2

## Verification summary
- Tree state: <11 commits since v0.1.17 (`9c651da..HEAD`)>
- Fix-and-reland diff: <stamped>
- Both pytest gates: <stamped — expect 2729 passed, 5 skipped>
- Static gates: <stamped>

## R1 closure verification

| Finding | Closure status | Note |
|---|---|---|
| F-IR-01 (agent_cli_contract.md) | CLOSED | doc regenerated; gate test green |
| F-IR-02 (README post-W-OB-2) | CLOSED | quickstart rewritten |
| F-IR-03 (W-OB-5 broader coverage) | CLOSED | 7 paths + 5 tests + renderer fixes |
| F-IR-04 (next_action_hint correctness) | CLOSED | primitive-readiness logic + 2 regression tests |

## Findings (R2)

### F-IR-R2-01. <short title>
**Q-bucket:** Q-R2-XX
**Severity:** ...
**Reference:** <commit SHA / file:line>
**Argument:** ...
**Recommended response:** ...

(Or "no findings" if R2 closes clean.)

## Closure recommendation

(Verdict + named must-fix list (if any) + recommended next-round
budget. Ratifies R1's "remaining work small and localized"
expectation.)
```

If R2 closes with no findings: SHIP. If 1-2 nit-class findings:
SHIP_WITH_NOTES close-in-place. If anything substantive:
SHIP_WITH_FIXES → R3 (very surprising at this stage of the cycle).

---

## Step 4 — Verdict scale

- **SHIP** — push origin/main + PyPI publish (post maintainer manual
  TTY gate per RELEASE_PROOF §3).
- **SHIP_WITH_NOTES** — same as SHIP; named follow-ups carry to v0.1.19.
- **SHIP_WITH_FIXES** — fix-and-reland-2; round 3 launches.
- **DO_NOT_SHIP** — only on a correctness/security bug warranting
  reverts.

---

## Step 5 — Out of scope

- The 4 R1 findings (settled at fix-and-reland).
- Any new W-id scope (cycle closed at fix-and-reland boundary).
- The maintainer's manual TTY ship gate (RELEASE_PROOF §3 — fires
  AFTER R2 closes).
- v0.1.19 / v0.2.0 scope.
- AGENTS.md governance edits (none in fix-and-reland; should be none
  in any post-cycle).

---

## Step 6 — Cycle pattern (R2 placement)

```
D14 ✓ (R1+R2 close-in-place)
Phase 0 ✓
Implementation ✓ (7 W-id commits + 2 dogfood gates + ship-prep)
D15 IR R1 ✓ (4 findings SHIP_WITH_FIXES; all accepted)
D15 IR R1 fix-and-reland ✓ (single commit)
D15 IR R2 ← you are here
  → SHIP / SHIP_WITH_NOTES → maintainer manual TTY gate → PyPI publish
  → SHIP_WITH_FIXES (unlikely) → R3
RELEASE_PROOF.md + REPORT.md ✓ (re-stamped post-fix)
```

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_18/codex_implementation_review_round_2_response.md`
  (new) — your findings.
- `reporting/plans/v0_1_18/codex_implementation_review_round_3_prompt.md`
  (only if R2 verdict requires R3 — surprising).

**No code changes. No source commits.** Maintainer applies any R2
fixes; you do not edit source directly.
