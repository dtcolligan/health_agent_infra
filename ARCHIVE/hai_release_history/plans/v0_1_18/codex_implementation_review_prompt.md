# Codex Implementation Review — v0.1.18 cycle

> **Why this round.** v0.1.18 implementation is complete on `main`
> (8 commits since v0.1.17 ship: `caf3fb2` W-OB-1 → `1711676` W-OB-4b).
> The D14 pre-cycle plan-audit chain settled at PLAN_COHERENT
> close-in-place in round 2 (R1 7 findings → R2 3 findings; matches
> empirical norm `10 → 5 → 3 → 0`). Phase 0 (D11) bug-hunt cleared
> with 4 records (F-OB-PRE-01 absorbed as W-OB-7; F-PHASE0-01..03
> informational). RELEASE_PROOF + REPORT authored. **The branch has
> not been pushed to origin/main.** Per the maintainer's standing
> instruction, Codex reviews implementation against the diff before
> any push or PyPI publish.
>
> **What you're auditing.** The cycle's *implementation* — that the
> code that landed actually delivers what PLAN.md promised, that the
> ship gates pass, and that no defect is hiding in the diff. **Not**
> the plan itself (D14 already settled that), **not** the prior-
> cycle surface (v0.1.17 already shipped to PyPI).
>
> **Empirical norm:** 2-3 rounds, settling at the `5 → 2 → 1-nit`
> shape for substantive cycles. v0.1.18 is structurally low-density
> (small catalogue, additive changes, no governance edits beyond
> closure-side); realistic round expectation 2.
>
> **What's distinct about this cycle.** v0.1.18 ran end-to-end
> autonomously under Claude Opus 4.7 (1M context) per the maintainer's
> "execute every phase you can do without maintainer input or Codex
> audit" mandate. All 7 W-id commits + 2 dogfood gates + ship-prep
> bundled in a single autonomous session (~1-2 days of maintainer-
> work-equivalent compressed). The IR is the first independent
> review of the implementation. **Specifically watch for:**
>
> 1. **W-OB-2 default-flip path**: `cmd_init` lines ~580-625
>    introduce TTY check + `check_onboarding_readiness` invocation.
>    Verify the predicate doesn't break for any of the 5 test cases
>    + the bonus explicit-`--guided` case + edge cases the test
>    surface might miss (pseudo-TTY, headless containers, etc.).
> 2. **W-OB-7 seam additivity**: `open_connection_with_migrations`
>    is intentionally NOT a global replacement for `open_connection`.
>    Verify no read-path that was relying on bare `open_connection`
>    accidentally got migrated.
> 3. **W-OB-5 manifest-consistency invariant**: the registry caught
>    + corrected 3 entries pre-impl. Verify the test still catches
>    drift (mutate a registry entry; expect the test to fail).
> 4. **W-OB-4b deferral honesty**: TTY default-flip UX confirmation
>    is deferred to maintainer ship-time manual gate. Is this an
>    honest deferral or a hidden gap? Should the IR ratify the
>    autonomous-mode-substitution shape?
>
> **You are starting fresh.** This prompt and the artifacts it cites
> are everything you need; do not assume context from a prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd                                          # /Users/domcolligan/health_agent_infra
git branch --show-current                    # main (cycle ran on main, not a branch)
git log --oneline 9c651da..HEAD              # expect 9 commits: D14 closure + 7 W-id work + ship-prep
git status                                   # clean (uv.lock untouched pre-existing)
```

Top of `git log` should show:
```
<sha>  release(v0.1.18): ship-prep bundled commit (version bump + AGENTS-edit-free + AUDIT/CHANGELOG/RELEASE_PROOF/REPORT/freshness sweep)
1711676 docs(W-OB-4b): Phase 2 local-wheel smoke ...
f78ebdd feat(W-OB-5): hai doctor next_action ...
4ac917e feat(W-OB-2): hai init default-flip ...
9ff74c6 feat(W-OB-3): --guided post-prompt next_action_hint ...
a79f78b docs(W-OB-4a): Phase 1 upgrade-dogfood ...
817aa6e feat(W-OB-7): intake-handler migration parity ...
caf3fb2 docs(W-OB-1): README pivot ratified ...
3726056 docs(plans): v0.1.18 Phase 0 (D11) closed ...
8e762c2 docs(plans): v0.1.18 D14 settled — R1 7 findings + R2 3 findings ...
9c651da docs: v0.1.17 ship-time freshness sweep + v0.1.18 F-OB-PRE-01 finding
```

If anything mismatches, stop and surface. Ignore any tree under
`/Users/domcolligan/Documents/`.

---

## Step 1 — Read orientation artifacts (in order)

1. **`AGENTS.md`** — operating contract. v0.1.18 proposed **no** new
   D-entries and **no** "Do Not Do" edits. Verify the AGENTS.md text
   is unchanged across the cycle (the only mutation should be at
   ship-prep for closure-side updates if any).
2. **`reporting/plans/v0_1_18/PLAN.md`** — cycle contract (post-R2).
3. **`reporting/plans/v0_1_18/RELEASE_PROOF.md`** — what shipped, with
   the manual ship-time TTY gate documented in §3.
4. **`reporting/plans/v0_1_18/REPORT.md`** — narrative summary +
   lessons-learned.
5. **`reporting/plans/v0_1_18/audit_findings.md`** — Phase 0 findings
   (F-OB-PRE-01 + F-PHASE0-01..03).
6. **`reporting/plans/v0_1_18/dogfood_findings.md`** — W-OB-4a + W-OB-4b
   evidence-gate output (8 cumulative findings).
7. **`reporting/plans/v0_1_18/codex_plan_audit_response.md`** + R2 +
   response_responses — D14 audit chain.
8. **`CHANGELOG.md`** § [0.1.18].

Then open the diff:

```bash
git diff 9c651da..HEAD -- src/ verification/ reporting/docs/ \
    AGENTS.md ROADMAP.md AUDIT.md CHANGELOG.md pyproject.toml \
    reporting/plans/strategic_plan_v1.md \
    reporting/plans/tactical_plan_v0_1_x.md
```

Cycle artifact diff (for completeness):
```bash
git diff 9c651da..HEAD -- reporting/plans/v0_1_18/
```

---

## Step 2 — Audit questions

### Q-W-OB-1. README pivot ratification (commit `caf3fb2`)

W-OB-1 acceptance items 1-4 (PLAN §2.A). Mostly pre-staged on `main`
2026-05-04 alongside the v0.1.18 README scaffold; this commit is
docs-only verification + cross-reference sweep + CHANGELOG entry.

- **Q-1.1.** Verify README "Install and quickstart" (lines 206-244 at
  HEAD) is internally consistent post-W-OB-2. Does the README cite
  `hai init --guided` (pre-W-OB-2 user instruction) OR bare `hai init`
  (post-W-OB-2 default-flip user instruction)? Does it reflect the
  current ship state, or is it stale?
- **Q-1.2.** Cross-reference sweep: did W-OB-1 catch every stale
  `hai init` reference? `agent_integration.md:27` was updated in this
  commit; were any docs missed? `grep -rn "hai init" reporting/docs/
  README.md CHANGELOG.md` should not surface stale `hai init && hai
  auth intervals-icu` install-time sequences.
- **Q-1.3.** Launch directory under `reporting/docs/launch/` was
  intentionally left as-is (v0.1.0-era historical material per
  AGENTS.md provenance discipline). Is that the right disposition,
  or should the launch directory be touched?

### Q-W-OB-2. `hai init` default-flip (commit `4ac917e`)

W-OB-2 is the cycle's release-blocker leg of substantive tier. PLAN
§2.B acceptance items 1-7. Six tests in
`test_cli_init_default_flip.py` (5 cases per OQ-2 + bonus
explicit-`--guided` case).

- **Q-2.1.** Read `cli/handlers/config_init.py:cmd_init` lines ~580-625
  (the new default-flip block). Does the predicate ordering match
  PLAN §2.B? Specifically: explicit `--guided` honoured first, then
  `--non-interactive` flag, then env var, then no-TTY, then
  `check_onboarding_readiness` predicate. Are any opt-out paths
  missed (e.g. `HAI_INIT_NON_INTERACTIVE=0` should NOT opt out — only
  `=1` does; verify)?
- **Q-2.2.** Test surface: 5 cases + 1 bonus = 6. Are there edge
  cases not covered? Pseudo-TTY (CI runners that present TTY but
  don't have user input)? `isatty()` raising AttributeError on
  exotic stdin? Containerized environments? PLAN §4 risk 1
  acknowledged the pseudo-TTY case but didn't gate it with a test.
- **Q-2.3.** Manifest snapshot regenerated for the new
  `--non-interactive` flag. Verify
  `verification/tests/snapshots/cli_capabilities_v0_1_13.json` and
  `cli_help_tree_v0_1_13.txt` both contain the new flag and nothing
  else changed (`hai init` flag count: 11 expected post-W-OB-2;
  total command count unchanged at 67).
- **Q-2.4.** F-PHASE0-01 mitigation: `verification/tests/conftest.py`
  autouse fixture sets `HAI_INIT_NON_INTERACTIVE=1` for the suite.
  Verify (a) the fixture is correctly autouse, (b) it doesn't leak
  into other tests' assertions about env state, (c) the new W-OB-2
  test correctly `monkeypatch.delenv`'s before exercising the
  predicate.
- **Q-2.5.** `default_flip_decision` is exposed in the JSON report at
  `report["default_flip"]["decision"]` for post-hoc visibility. Is
  this an intentional schema add to the `hai init` JSON contract?
  If so, should it be documented somewhere (CHANGELOG, capabilities
  manifest, etc.)?

### Q-W-OB-3. `--guided` post-prompt + skip-input (commit `9ff74c6`)

W-OB-3 acceptance items 1-6 (PLAN §2.C). New `next_action_hint` field
on `OnboardingResult` + 6 new tests.

- **Q-3.1.** `OnboardingResult.next_action_hint` is populated based
  on auth + intent status (4 branches: full success, no creds, no
  intent, neither). Is the branch coverage complete? What if `auth_status`
  is `failed` (not `configured` / `already_configured` / `user_skipped`)?
- **Q-3.2.** F-PLAN-06 round-1 disposition was "no literal `skip`
  keyword added — content-only review." Verify the W-OB-3 commit
  doesn't accidentally add a literal `skip` keyword affordance to
  the prompt copy or input parsing.
- **Q-3.3.** Existing 9 tests in `test_init_onboarding_flow.py` still
  pass (9/9 green at HEAD). The new field is additive in `to_dict()`;
  any downstream test asserting an exact dict shape would have caught
  the addition. Verify nothing in the suite asserts `OnboardingResult.to_dict()`
  exact contents and breaks silently.

### Q-W-OB-4a. Phase 1 upgrade dogfood (commit `a79f78b`)

W-OB-4a is an evidence gate, not a code commit. Output:
`dogfood_findings.md` § W-OB-4a + 4 findings.

- **Q-4a.1.** F-OB-4A-01 (cross-cycle field-naming convention with
  `hai daily`'s `intake_command`) is documented but not test-enforced.
  Is the alignment honest in the W-OB-5 implementation (`next_action.command`
  vs `intake_command`)? They use different field names; should they?
- **Q-4a.2.** F-OB-4A-02 (umbrella preference for multi-missing) IS
  enforced in W-OB-5 via the `len(missing) > 1` branch. Verify the
  branch fires correctly across all 7 combinations of {intent, target,
  wellness_pull} missing.
- **Q-4a.3.** Synthetic schema-25 DB construction used OQ-3 priority
  option (b) (apply-migrations-filtered) rather than option (c)
  (snapshot maintainer's real pre-v0.1.17 DB). Is this a fidelity gap
  (the real DB has more state than just the schema)? Per RELEASE_PROOF
  §7 note 1, the maintainer's manual TTY gate would substitute the
  real-state evidence; is that substitution honest?

### Q-W-OB-4b. Phase 2 local-wheel smoke (commit `1711676`)

W-OB-4b is an evidence gate; documented in `dogfood_findings.md` §
W-OB-4b + 4 findings.

- **Q-4b.1.** Wheel built as `health_agent_infra-0.1.17-py3-none-any.whl`
  even though the cycle is v0.1.18 work. The pyproject version bump to
  0.1.18 happens at ship-prep (the bundled commit). Is the wheel-version
  mismatch a problem for the smoke (the wheel CONTENTS reflect v0.1.18
  work but the version label doesn't)? Will RELEASE_PROOF §3 manual gate
  catch this?
- **Q-4b.2.** Autonomous-mode safety substitution: `pipx install` against
  the user's primary environment was substituted with isolated venv
  install. Is this an acceptable substitution, or should the maintainer
  rebuild the wheel + run `pipx install` against their primary env at
  ship time (per RELEASE_PROOF §3)?
- **Q-4b.3.** F-OB-4B-02 (TTY default-flip UX deferred to maintainer)
  is the largest deferral in the cycle. Is the deferral shape honest
  (autonomous-mode subshell genuinely cannot exercise real TTY) or is
  there an automation path that should have been attempted (e.g. `expect`,
  pseudo-tty libraries)?

### Q-W-OB-5. `hai doctor next_action` (commit `f78ebdd`)

W-OB-5 acceptance items 1-6 (PLAN §2.E). New
`_NEXT_ACTION_REGISTRY` table + 5 doctor checks gain `next_action`
+ 12 new tests.

- **Q-5.1.** Registry entries for 9 commands. The manifest-consistency
  test caught + corrected 3 drift entries pre-impl
  (`hai state migrate`, `hai intent training add-session`, `hai target
  set` were registry-False but manifest-True). Verify the corrected
  values are actually correct (not just consistent with a wrong manifest):
  is `hai state migrate` honestly `agent_safe=True`? It mutates schema
  state without user gating. Same question for `hai intent training
  add-session` + `hai target set` (both write user-gated rows).
- **Q-5.2.** Registry exhaustiveness vs hint coverage: per
  F-PHASE0-02, `core/doctor/checks.py` emits 16 hint strings across
  ≥6 checks. W-OB-5 covers 5 checks (`onboarding_readiness`,
  `state_db`, `auth_intervals_icu`, `auth_garmin`, `skills`). Are
  any hint-emitting checks missed where the hint maps to a concrete
  command? Read `check_today`, `check_intake_gaps`, `check_config`
  hint emissions and judge.
- **Q-5.3.** `_render_next_action_lines` helper emits a `next:` line
  per check. Verify every check that emits `next_action` correctly
  goes through the renderer (the generic `_render_check` path
  handles it; the special-case `_render_onboarding_readiness` was
  also updated). Are there other special-case renderers
  (`_render_today`, `_render_intake_gaps`, `_render_sources`) that
  bypass the generic loop and miss the `next_action` line?
- **Q-5.4.** OQ-4 disposition: `next_action` is runtime-only, NOT in
  `hai capabilities --json`. Verify the manifest schema is unchanged
  (no new `doctor_check_schema` block; no manifest delta). The
  v0.1.17 W-30 schema-regression test (`test_capabilities_manifest_schema.py`)
  should catch a regression here.

### Q-W-OB-7. Intake-handler migration parity (commit `817aa6e`)

W-OB-7 closes F-OB-PRE-01. PLAN §2.G acceptance items 1-6. New
`open_connection_with_migrations` helper + 9 call-site updates +
10 new tests.

- **Q-7.1.** Helper additivity: `open_connection` is unchanged
  globally per OQ-1. Verify by `grep -rn "open_connection(" src/
  health_agent_infra/` — every non-intake-handler caller of
  `open_connection` (e.g. `core/init/onboarding.py`, `evals/runner.py`,
  `core/doctor/checks.py`) intentionally still uses the bare variant.
  Are any of those CALLS that SHOULD migrate (i.e. silently broken
  by F-OB-PRE-01-shape failures on schema-behind DBs)?
- **Q-7.2.** All 8 `cmd_intake_*` handlers verified routing through
  the migrating helper. Verify with `grep -nE "open_connection" src/
  health_agent_infra/cli/handlers/intake.py` — every call should be
  `open_connection_with_migrations`, not bare `open_connection`. The
  per-handler classification table in PLAN §2.G claims readiness uses
  the helper at line 1149 (via `_project_readiness_submission_into_state`)
  and gaps uses lines 1025 + 1093 (presence + write). Verify both.
- **Q-7.3.** Test surface: 10 tests in `test_intake_migration_parity.py`.
  Are the per-handler test invocations honest (using the actual CLI
  flag shapes the handlers expect, not aspirational shapes)? Run them
  and inspect any failure mode that surfaces.
- **Q-7.4.** Reproducer test (`test_intake_weight_on_pre_v0_1_17_db`):
  this is the F-OB-PRE-01 regression gate. Verify it actually
  reproduces the original failure mode (i.e., would FAIL without
  W-OB-7's fix). Mutation test: temporarily revert
  `cmd_intake_weight` to use `open_connection` directly; the test
  should fail with `OperationalError: no such table: body_comp`.
- **Q-7.5.** Migration application semantics: `apply_pending_migrations`
  emits a `runtime_event_log` row when called from `cmd_state_migrate`
  but NOT when called from the new auto-migrate seam. Is this the
  honest deferral W-OB-7 §"What this WS does NOT do" claims, or is
  there an audit-trail gap that should be closed in W-OB-7 itself?

### Q-cross-cycle. Cross-cutting code quality

- **Q-X.1.** Unused imports in any commit? Lazy imports in hot paths?
  New error paths fail open or fail closed correctly?
- **Q-X.2.** F-PHASE0-01 conftest.py fixture: does it leak across
  test boundaries? Does any test that creates its own pytest
  subprocess inherit the env var (potentially masking a bug)?
- **Q-X.3.** Provenance discipline (per AGENTS.md "Patterns the
  cycles have validated"): spot-verify every file path / line number /
  function name cited in PLAN.md, RELEASE_PROOF.md, REPORT.md, or
  CHANGELOG.md against HEAD.

### Q-ship-gates. Re-run the gates

- **Q-G.1.** `uv run pytest verification/tests -q` — expect 2722 pass,
  5 skipped.
- **Q-G.2.** `uv run pytest verification/tests -W error::Warning -q`
  (broader gate per AGENTS.md D13/W-N-broader) — expect same.
- **Q-G.3.** `uvx mypy src/health_agent_infra` — expect "Success: no
  issues found in 147 source files".
- **Q-G.4.** `uvx bandit -ll -r src/health_agent_infra` — expect
  "0 medium / 0 high severity".
- **Q-G.5.** `hai capabilities --json` byte-stable against snapshot.
- **Q-G.6.** `hai capabilities --markdown > reporting/docs/agent_cli_contract.md`
  — does the markdown contract regenerate cleanly post-W-OB-2?
- **Q-G.7.** Persona matrix: 13/13, 0 findings, 0 crashes.
- **Q-G.8.** `hai eval run --scenario-set all` — 135/135 PASS.

### Q-absences. What did the cycle NOT do

- **Q-A.1.** PLAN promised W-OB-6 conditional. Per
  `dogfood_findings.md` §W-OB-4a + §W-OB-4b, W-OB-6 did NOT fire (no
  W-OB-6-class structural findings). Is the "no fire" disposition
  honest, or did a structural finding silently route into a
  W-OB-3/5 absorption that should have been a discrete W-OB-6 commit?
- **Q-A.2.** AGENTS.md edits: PLAN §3 said "no CP-shape governance
  edits this cycle." Verify AGENTS.md is unchanged across the
  9-commit diff (the only AGENTS.md mention is closure-side
  freshness updates, NOT CP-shape edits).
- **Q-A.3.** Manual ship-time gate (RELEASE_PROOF §3): is this an
  honest deferral or a hidden gap? Should the IR ratify the substitution
  shape (autonomous unit-test + maintainer manual TTY = acceptance)?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_18/codex_implementation_review_response.md`:

```markdown
# Codex Implementation Review — v0.1.18

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES
**Round:** 1

## Verification summary
- Tree state: 9 commits since v0.1.17 (`9c651da..HEAD`).
- Test surface: <stamped>
- Ship gates: <stamped per Q-G.1..8>

## Findings

### F-IR-01. <short title>
**Q-bucket:** Q-W-OB-X / Q-X / Q-G / Q-A
**Severity:** correctness-bug | security | scope-mismatch | provenance-gap | acceptance-weak | nit
**Reference:** <commit SHA / file:line> or "absent"
**Argument:** <what + citations>
**Recommended response:** <fix-and-reland | accept-as-known | ...>

### F-IR-02. ...

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-OB-1 | ... | ... |
| W-OB-2 | ... | ... |
| W-OB-3 | ... | ... |
| W-OB-4a | ... | ... |
| W-OB-4b | ... | ... |
| W-OB-5 | ... | ... |
| W-OB-7 | ... | ... |

## Open questions for maintainer

(Including F-OB-4B-02 ratification: is the autonomous-mode unit-test +
maintainer manual TTY gate substitution acceptable?)

## Closure recommendation

Verdict + named must-fix list (if any) + recommended next-round budget.
```

Each finding triageable. Vague feedback is not a finding; "PLAN §2.E
acceptance item 1 says coverage extends to `check_credentials` but
that function doesn't exist; the registry covers `check_auth_garmin`
+ `check_auth_intervals_icu` instead — verify all hint-emitting checks
are covered" is.

---

## Step 4 — Verdict scale

- **SHIP** — push to origin/main + publish to PyPI, no further work.
  Maintainer must still run RELEASE_PROOF §3 manual TTY gate before
  publish.
- **SHIP_WITH_NOTES** — push + publish; named follow-ups carry to
  v0.1.19. Notes enumerate every non-blocking finding.
- **SHIP_WITH_FIXES** — fix-and-reland. Notes enumerate every
  blocking finding. Round-2 review after maintainer addresses.
- **DO_NOT_SHIP** — only on correctness/security bug warranting
  commit reverts.

For v0.1.18, `SHIP_WITH_NOTES` with a small follow-up set is the
natural shape; `SHIP` outright is celebrated; `SHIP_WITH_FIXES`
means a real bug got past D14 + Phase 0 + autonomous-mode
implementation; `DO_NOT_SHIP` would be very surprising.

---

## Step 5 — Out of scope

- v0.1.17 implementation (already shipped to PyPI 2026-05-05).
- D14 plan-audit chain itself (closed at PLAN_COHERENT close-in-place).
- Strategic-plan / tactical-plan content beyond the §5E ship-time
  freshness updates this cycle applied.
- v0.1.19 / v0.2.0 scope (named in tactical_plan_v0_1_x.md).
- The maintainer's manual TTY ship gate (RELEASE_PROOF §3) — that
  fires AFTER IR settles, not during it.

---

## Step 6 — Cycle pattern

```
D14 plan-audit ✓ (R1 7 → R2 3 close-in-place)
Phase 0 (D11) ✓ (4 records; pre-implementation gate fired GREEN)
Pre-implementation gate ✓
Implementation ✓ 7 W-id commits + 2 dogfood gates
Codex implementation review ← you are here
  → SHIP_WITH_FIXES → maintainer + new commits
  → SHIP / SHIP_WITH_NOTES → ship-prep bundled commit (already authored)
RELEASE_PROOF.md + REPORT.md ✓ (pre-stamped)
Maintainer manual TTY gate (RELEASE_PROOF §3) — ship-time
PyPI publish (per reference_release_toolchain.md)
```

Estimated: 1-2 sessions per round. v0.1.18 expected 1-2 IR rounds
given the autonomous-mode origin (less institutional context for
implicit shortcuts that human-driven cycles sometimes ship).

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_18/codex_implementation_review_response.md`
  (new) — your findings.
- `reporting/plans/v0_1_18/codex_implementation_review_round_N_response.md`
  (subsequent rounds).

**No code changes.** No source commits. No state mutations. Maintainer
applies fixes; you do not edit source directly.

If you find a correctness/security bug warranting `DO_NOT_SHIP`, name
it explicitly and stop the review for maintainer adjudication.
