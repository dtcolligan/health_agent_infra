# Maintainer response — Codex IR round 1 (v0.1.13)

**Round:** 1
**Codex verdict:** SHIP_WITH_FIXES, 6 findings.
**Maintainer disposition:** all 6 findings accepted; all 6 applied
in the same commit. Per-finding disposition + commit reference
below.

**Branch state at response time.** `cycle/v0.1.13` HEAD at IR
round 1 close: `bdc4396` (codex_implementation_review_prompt.md).
Round-1 fixes land in a single commit on top.

**Test surface delta.** 2486 → 2493 (+7 new tests), 3 skipped.
Broader gate (`-W error::Warning`) holds. Mypy 0 errors.
Persona matrix 12 / 0 findings / 0 crashes (re-run after fixes).

---

## Per-finding response

### F-IR-01 — W-AG threshold 7 → 30 (fix-and-reland)

**Disposition:** **fix-and-reland.** Codex correctly identified the
contract drift: PLAN.md §1.2 + §2.B both specify "day-30+ users",
the IR prompt explicitly named ≥7 as a finding, and
`render.py:_STREAK_ESTABLISHED_THRESHOLD` shipped at 7 with tests
locking that behavior. The PLAN was reviewed across 5 D14 rounds
at the 30-day language; the implementation drift is the bug, not
the PLAN.

**Applied:** `src/health_agent_infra/core/narration/render.py`
threshold changed to 30; module + function docstrings updated.
`verification/tests/test_today_streak_prose.py` boundary tests
shifted to streak_days=30 (engages established voice) and
streak_days=29 (negative boundary, stays in pre-W-AG voice).
Format-consistency tests use streak_days=45 to stay safely above
the new threshold.

**Verification:** the 10-test W-AG file passes including the new
`test_threshold_below_thirty_does_not_engage_established_voice`
negative-boundary case. No second-order regressions.

### F-IR-02 — `hai init --guided` exit code on interrupt/partial (fix-and-reland)

**Disposition:** **fix-and-reland.** Codex correctly identified
the false-green: pre-fix, `cmd_init` returned `OK` even when the
guided flow reported `status: "interrupted"` or
`overall_status: "partial"`. CI / doctor / agent callers couldn't
detect incomplete onboarding without parsing the JSON body —
exactly the contract the IR prompt called out.

**Applied:** `cli.py:cmd_init` now reads `guided_status` (top-level
`status` for the KeyboardInterrupt path; `overall_status` for the
normal-path `partial`) and returns `USER_INPUT` for both. The
`ok` and `ok_with_skips` shapes still return `OK` — intentional
user skip is not an error.

**W-AD interlock.** The new USER_INPUT exit needed an actionable
stderr print to satisfy `test_user_input_messages_actionable`
(`W-AD`). Added stderr prose for both shapes:
- `interrupted` → "guided onboarding interrupted. {guided['hint']}"
  (the orchestrator's existing hint surface).
- `partial` → "guided onboarding partially failed. Check the JSON
  report for per-step status; rerun `hai init --guided` to retry
  the failed step(s)."

**Verification:** existing `test_guided_keyboardinterrupt_mid_flow_*`
test renamed + flipped to assert `USER_INPUT`. Added a
parametrised `test_guided_keyboardinterrupt_at_each_step_boundary_returns_user_input`
covering `raise_at` ∈ {1, 2, 3, 5} — start-of-auth, mid-auth,
start-of-intent/target, mid-intent/target. All 5 boundary tests
green.

### F-IR-03 — explicit `expected_actions` per persona (fix-and-reland)

**Disposition:** **fix-and-reland.** Codex correctly identified
that the PLAN's per-persona declaration contract was satisfied
only by base-class auto-derivation, not by inline declarations
in `p<N>_<slug>.py`. The runner assertion existed, but the
ground-truth shape v0.1.14 W58 prep depends on lived in the
fallback path, not in the persona file the maintainer reads to
understand the persona's contract.

**Applied:**

1. Promoted `_derive_default_*` to public helpers
   `established_expected_actions()`, `day_one_expected_actions()`,
   `established_forbidden_actions()` in
   `verification/dogfood/personas/base.py`. Auto-derivation kept
   as a safety net for future personas that forget to declare;
   docstrings updated to reflect the fallback-only role.
2. Each of 12 persona files (`p1_*` through `p12_*`) now imports
   the relevant helper and inlines an explicit `expected_actions=`
   keyword (and `forbidden_actions=` where it adds value):
   - 10 established personas spread `established_expected_actions()`
     + `established_forbidden_actions()`.
   - P8 (day-1 fresh install) uses `day_one_expected_actions()`
     with empty `forbidden_actions` (the day-1 whitelist is
     already exclusive).
   - P11 (elevated-stress hybrid) overrides stress to legitimately
     allow `escalate_for_user_review`, since the W-O scenario
     specifically tests the elevated-band escalation path.

3. Added `test_every_persona_file_declares_expected_actions_inline`
   to `test_persona_expected_actions.py` — text-scans each
   `p*.py` file for the literal `expected_actions=` keyword. The
   text-scan is the right shape because `__post_init__` post-fills
   empty dicts; introspection cannot distinguish "declared empty"
   from "post-filled by base."

**Verification:** 7 W-AK tests green, including the new
inline-declaration assertion. Persona matrix 12/0/0.

### F-IR-04 — `META_DOCUMENT_PRAGMA` bounded to allowlist (fix-and-reland)

**Disposition:** **fix-and-reland.** Codex correctly identified
the wholesale loophole: pre-fix, ANY skill text containing the
pragma comment bypassed the static scan, regardless of source
skill. The four-constraint exception path the PLAN described
applied only to the regular `ALLOWLISTED_SKILLS` route; the
pragma was a separate broader bypass that the PLAN's risk row
explicitly named as something to prevent.

**Applied:**

1. Added `META_DOCUMENT_ALLOWLIST: frozenset[str] = frozenset({
   "safety", "reporting", "expert-explainer"})` constant in
   `core/lint/regulated_claims.py`. Module + helper docstrings
   updated to name the bound + the F-IR-04 origin.
2. The pragma-honoring branch in `scan_skill_text` now requires
   BOTH the pragma AND `source_skill in META_DOCUMENT_ALLOWLIST`.
   Either alone is insufficient.
3. Added `test_meta_document_pragma_bounded_to_allowlist` covering
   three failure modes: pragma + non-allowlisted real skill,
   pragma + `source_skill=None`, pragma + invented future-skill
   name. Sanity case: each of the 3 allowlisted skills DOES
   bypass (the bound is on the source, not on the pragma).
4. Re-exported `META_DOCUMENT_ALLOWLIST` from
   `core/lint/__init__.py` so future allowlist edits are visible
   to callers.

**Verification:** 14 W-LINT tests green, including the new
bounded-allowlist negative test.

### F-IR-05 — W-29-prep snapshot provenance gap (revise-artifact)

**Disposition:** **revise-artifact.** Codex correctly identified
the provenance gap: CARRY_OVER §2 W-29-prep row + the W-FBC-2
commit message both stated `bd11be3` was the only post-W-29-prep
snapshot regeneration, but `git log --oneline --
verification/tests/snapshots/...` shows three commits touching
the snapshot files: `45319da` (initial freeze) → `03fab4f`
(W-AA `--guided` surface addition) → `bd11be3` (W-FBC-2
`--re-propose-all` help-text update). v0.1.14 W-29's go/no-go
provenance has to name both legitimate post-baseline
regenerations.

**Applied:**

1. `reporting/docs/cli_boundary_table.md`: added a 3-row provenance
   table naming each commit + workstream + reason.
2. `reporting/plans/v0_1_13/CARRY_OVER.md` §2 W-29-prep row:
   rewrote to acknowledge both legitimate regenerations; named
   F-IR-05 as the provenance correction trigger.

No code change. The actual snapshot files are correct; the
artifact provenance trail is what was incomplete.

### F-IR-06 — README test count 2455 → 2486 (fix-and-reland)

**Disposition:** **fix-and-reland.** Stale W-AC count. Updating to
**2493** (the post-IR-r1-fixes count, which is +7 from the 2486
post-W-FBC-2 figure Codex round 1 verified). The badge + table
share the value via `replace_all`.

**Applied:** `README.md:14` (badge) + `README.md:52` (What ships
today table). Update applied as `2455 → 2486` per Codex's
recommended value, since 2486 was the verified post-W-FBC-2
ship state at IR-round-1 open. The +7 round-1 additions are
invisible at the README level until the next ship.

**Note for ship-time freshness sweep:** if the suite count grows
further before v0.1.13 ships, the README badge + table need
another touch as part of the standard freshness pass per
AGENTS.md "Ship-time freshness checklist." Not a finding shape —
expected drift between IR close and RELEASE_PROOF authoring.

---

## Open-questions answers

**Q1.** *Is W-AG's established-user threshold supposed to be
day-30+ as planned, or did v0.1.13 intentionally lower it to
day 7?* — Day-30+ as planned. Implementation drift; corrected
per F-IR-01.

**Q2.** *Should `hai init --guided` communicate partial/interrupted
progress via exit 0 plus JSON status, or should those paths be
USER_INPUT?* — USER_INPUT, per F-IR-02. The JSON body still
carries the canonical hint; the exit code is the
script-detectable signal. Stderr also surfaces the actionable
prose for human / CI readers per the W-AD interlock.

**Q3.** *Is W-LINT's meta-document pragma intended as a second,
separately bounded exception class? If yes, it needs an explicit
allowlist and plan text so it is not confused with the
`expert-explainer` exception.* — Yes, it's a second bounded
exception class with a different purpose: `ALLOWLISTED_SKILLS`
permits bounded definitional prose (cited / quoted in user-
visible context); `META_DOCUMENT_ALLOWLIST` permits scope-
statement / negation-list files (where regulated terms appear by
design). Now hardcoded per F-IR-04. Plan-text update can land at
the next PLAN revision; in the meantime the source-of-truth is
the constants in `core/lint/regulated_claims.py` and the negative
test in `test_regulated_claim_lint.py`.

---

## Round-1 close

All six findings applied. Ship gates verified clean post-fixes:

| Gate | Status |
|---|---|
| Pytest narrow | 2493 passed, 3 skipped (+7 from round-1 open) |
| Pytest broader (`-W error::Warning`) | 2493 passed, 3 skipped — held |
| Mypy | 0 errors / 120 source files — held |
| Persona matrix | 12 personas / 0 findings / 0 crashes |

**Recommended next step:** Codex IR round 2 against the post-fix
diff. Empirical settling shape per AGENTS.md is 5 → 2 → 1-nit
across 3 rounds for substantive cycles; round 2 is expected to
catch ≤2 second-order findings (typically introduced by round-1
fixes themselves). If round 2 closes at SHIP / SHIP_WITH_NOTES,
RELEASE_PROOF + REPORT + CHANGELOG follow.
