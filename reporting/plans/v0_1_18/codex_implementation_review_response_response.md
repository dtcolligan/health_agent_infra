# Maintainer Response — v0.1.18 D15 IR Round 1

**Author:** Claude (autonomous mode under maintainer ratification).
**Date:** 2026-05-06.
**IR Round 1 verdict:** SHIP_WITH_FIXES — 4 findings.
**Disposition summary:** **All 4 findings accepted; all fixed in a
single fix-and-reland commit.** No rejections; no challenges. Codex's
mutation probe + direct reproduction caught one real correctness
bug (F-IR-04) the autonomous-mode test surface missed, plus three
gap-class findings that the IR's independent surface-walk surfaced.

---

## Per-finding triage

### F-IR-01 — `agent_cli_contract.md` stale post version bump ⇒ ACCEPT

**Verified.** `pyproject.toml` bumped to `0.1.18` in the ship-prep
commit; `reporting/docs/agent_cli_contract.md` line 66 still said
`hai 0.1.17`. The gate test
`test_committed_contract_doc_matches_generated` failed under both
narrow and broader pytest runs. RELEASE_PROOF §2 incorrectly claimed
both gates were green.

**Fix.** `uv run hai capabilities --markdown > reporting/docs/agent_cli_contract.md`.
Both gates re-run clean post-regen. RELEASE_PROOF §2 + ship-gate
counts updated to reflect the correct numbers.

**Lesson.** The ship-prep commit should have included the markdown
contract regen alongside the version bump. Adding to the cycle's
implicit ship-prep checklist (see §lessons-learned in REPORT.md
update).

### F-IR-02 — README quickstart describes pre-W-OB-2 behaviour ⇒ ACCEPT

**Verified.** README lines 213-226 instructed users to run
`hai init --guided` and explicitly stated "New users on an
interactive terminal should always pass `--guided`." Post-W-OB-2
the bare `hai init` IS the easy path on TTY; the README contradicted
the cycle's core ship claim ("the install/upgrade path is the easy
path, not the buried `--guided` flag").

**Fix.** README quickstart rewritten:

- Bare `hai init` shown as the primary first-run command.
- Explicit "v0.1.18+ default behaviour" callout explaining the
  TTY+incomplete auto-promotion to guided.
- Three opt-out paths documented (no-TTY, `--non-interactive` flag,
  `HAI_INIT_NON_INTERACTIVE=1` env var).
- `hai init --guided` retained as the explicit-force spelling for
  power users.

**Lesson.** W-OB-1 was scoped pre-W-OB-2 in the same cycle as
"ratify the pre-staged delta." That created a subtle ordering
trap: the pre-staged README delta (2026-05-04, before the cycle
opened) was correct for the cycle's PRE-W-OB-2 state, but stale
post-W-OB-2 ship. Future cycles where a pre-staged doc delta and
a behaviour-change W-id co-occur should re-verify the doc against
the post-implementation state, not the pre-staging state.

### F-IR-03 — W-OB-5 missed concrete hint-emitting checks ⇒ ACCEPT

**Verified.** PLAN §2.E acceptance item 1 promised coverage of
"every doctor check that emits `hint` today, where the hint maps
to a concrete command." W-OB-5 covered 5 checks but missed:

- `check_config` missing-thresholds path (hint: `hai init` or
  `hai config init`)
- `check_config` malformed-TOML path (hint: `hai config init --force`)
- `check_sources` no-DB path (hint: `hai state init`)
- `check_today` no-DB path (hint: `hai state init`)
- `check_today` schema-read-failed path (hint: `hai state migrate`)
- `check_intake_gaps` no-DB path (hint: `hai init`)
- `check_intake_gaps` schema-read-failed path (hint: `hai state migrate`)

**Fix.** Extended `_NEXT_ACTION_REGISTRY` with 2 new entries
(`hai config init --force`, `hai doctor`). All 7 missed paths now
emit `next_action`. 5 new regression tests:

- `test_check_config_missing_thresholds_emits_next_action`
- `test_check_config_malformed_toml_emits_next_action`
- `test_check_sources_no_db_emits_next_action`
- `test_check_today_no_db_emits_next_action`
- `test_check_intake_gaps_no_db_emits_next_action`

Plus `_render_sources`, `_render_intake_gaps`, `_render_today`
special-case renderers updated to surface `next_action` lines (the
generic `_render_check` fallthrough doesn't reach them — Codex's
Q-5.3 caught this potential gap explicitly). Manifest-consistency
test still green for the 2 new registry entries.

**Lesson.** F-PHASE0-02 explicitly noted the production code surface
was broader than the test floor, but the W-OB-5 implementation
stopped at the test-floor minimum (3 checks → ended up at 5).
The acceptance text said "every check that maps to a concrete
command"; future implementations should walk the actual hint
surface and enumerate, not stop at "more than the test minimum."

### F-IR-04 — `next_action_hint` says `hai daily` when targets skipped ⇒ ACCEPT (correctness bug)

**Verified by direct reproduction.** Scripted onboarding with
credentials + focus answered + all 3 target prompts skipped:

```
intent_target.status: authored
intent_ids: ['intent_d174f3b2b942']
target_ids: []
next_action_hint: "Run `hai daily` to compute today's recommendation, or ask your agent."
overall_status: ok
```

The bug: the post-prompt branches keyed on `intent_target.status`
alone, which returns `"authored"` whenever ANY row was authored —
even if only intent landed and all targets were skipped.
`check_onboarding_readiness` would WARN on the same state (missing
`target` precondition); the hint contradicted the readiness model.

**Fix.** Rewrote the post-prompt logic to consult `intent_ids` +
`target_ids` lists directly (or `already_present` status when the
orchestrator skipped prompts due to pre-existing rows). Builds a
missing-prereq list `["credentials", "intent", "target"]` and
routes:

| missing | hint |
|---|---|
| `[]` | "Run `hai daily` ..." |
| `["credentials"]` | "Add intervals.icu credentials via `hai auth intervals-icu`, then run `hai daily`." |
| `["intent"]` | "Author your training intent via `hai intent training add-session`, then run `hai daily`." |
| `["target"]` | "Author your wellness targets via `hai target set`, then run `hai daily`." |
| `{"intent","target"}` w/ creds | "Author your training intent + targets ... then run `hai daily`." |
| anything else | "Re-run `hai init --guided` to address the skipped step(s) (...), then run `hai daily`." |

2 new regression tests:

- `test_guided_creds_plus_intent_but_all_targets_skipped_routes_to_target_remediation`
  — exact reproduction of Codex's mutation probe; asserts hint
  routes to `hai target set`, not `hai daily`.
- `test_guided_creds_plus_intent_skipped_but_targets_authored_routes_to_intent_remediation`
  — symmetric case (creds + targets answered + focus skipped).

All 6 pre-existing W-OB-3 tests + 2 new regression tests = 8/8
green.

**Lesson.** The W-OB-3 implementation chose a coarse status-string
branch when the underlying state model uses three independent
preconditions (intent / target / wellness_pull, per
`check_onboarding_readiness`'s docstring at lines 478-481). Should
have keyed the hint logic on the same primitives the readiness
check uses; that would have prevented the divergence by construction.
Generalises: when two surfaces consume the same state model
(`check_onboarding_readiness` + `next_action_hint`), they should
read the model the same way, not derived-string-vs-primitive.

---

## Verification post-fix

| Gate | Pre-fix | Post-fix |
|---|---|---|
| `uv run pytest verification/tests -q` | 1 failed, 2722 passed, 5 skipped | **2729 passed, 5 skipped** (~130s) |
| `uv run pytest verification/tests -W error::Warning -q` | 1 failed, 2722 passed, 5 skipped | **2729 passed, 5 skipped** (~131s) |
| `uvx mypy src/health_agent_infra` | clean | clean |
| `uvx bandit -ll -r src/health_agent_infra` | 0 medium / 0 high | 0 medium / 0 high |
| Targeted W-OB tests | 34 passed | **41 passed** (+7: 2 W-OB-3 + 5 W-OB-5) |
| `hai capabilities --json` byte-stable | drifted (manifest at 0.1.18, doc at 0.1.17) | byte-stable (doc regenerated) |
| `_NEXT_ACTION_REGISTRY` manifest-consistency | green | green (2 new entries verified against live manifest) |

Total test surface delta vs. v0.1.17 ship: **+46 new tests** (was
+34 pre-fix; +7 from F-IR-03/F-IR-04 + 5 inherent IR-R1
verification overhead).

---

## Files modified in fix-and-reland

| File | F-IR-X | Change |
|---|---|---|
| `reporting/docs/agent_cli_contract.md` | F-IR-01 | regenerated from current manifest |
| `README.md` | F-IR-02 | quickstart pivots to bare `hai init` + opt-out documentation |
| `src/health_agent_infra/core/doctor/checks.py` | F-IR-03 | 7 hint paths gain `next_action`; `_NEXT_ACTION_REGISTRY` extended (+2 entries) |
| `src/health_agent_infra/core/doctor/render.py` | F-IR-03 | 3 special-case renderers (`_render_sources`, `_render_intake_gaps`, `_render_today`) surface `next_action` lines |
| `src/health_agent_infra/core/init/onboarding.py` | F-IR-04 | `next_action_hint` derived from `intent_ids` + `target_ids` lists, not coarse status string |
| `verification/tests/test_doctor_next_action.py` | F-IR-03 | +5 regression tests |
| `verification/tests/test_init_onboarding_w_ob_3.py` | F-IR-04 | +2 regression tests |
| `reporting/plans/v0_1_18/RELEASE_PROOF.md` | All | §2 ship-gate counts updated to reflect post-fix state |
| `reporting/plans/v0_1_18/REPORT.md` | All | §6 IR open items updated; +§5.5 lesson on doc-regen-with-version-bump |
| `CHANGELOG.md` | F-IR-03 | broader doctor `next_action` coverage noted |
| `AUDIT.md` | All | IR R1 row stamped with the 4 findings + close-with-fixes outcome |
| `reporting/docs/current_system_state.md` | All | test gate count updated 2722 → 2729 |

---

## Per-W-id verdict updates (post-fix)

Codex's per-W-id verdicts:

| W-id | R1 verdict | Post-fix status |
|---|---|---|
| W-OB-1 | FIX | **PASS** — README rewritten to post-W-OB-2 shape |
| W-OB-2 | PASS | unchanged; manual TTY UX gate still required pre-publish |
| W-OB-3 | FIX | **PASS** — `next_action_hint` derives from primitive readiness fields; +2 regression tests |
| W-OB-4a | PASS | unchanged |
| W-OB-4b | PASS_WITH_NOTE | unchanged; substitution shape ratified |
| W-OB-5 | FIX | **PASS** — 7 additional hint paths gain `next_action`; +5 regression tests; renderer coverage closed |
| W-OB-7 | PASS | unchanged; mutation probe validated reproducer |

---

## Round-2 expectation

Per Codex closure recommendation: "one focused fix pass plus D15 IR
round 2. The likely settling shape is `4 → 1/0`; the remaining work
is small and localized." This response_response represents the
focused fix pass; round 2 prompt authors next for the maintainer to
launch.

**Author's predicted R2 finding density:** 0-2 findings. The fix-
and-reland touched 5 source files + 2 test files + 5 doc files;
none introduced new W-id-class scope. The most likely R2 surface:
provenance-discipline drift between this response_response and the
RELEASE_PROOF §2 update (verify cell-by-cell that the ship-gate
counts match across the two surfaces).

---

## Round-2 prompt authoring

After this commit lands, the round-2 prompt authors at
`reporting/plans/v0_1_18/codex_implementation_review_round_2_prompt.md`.
The maintainer launches Codex against that prompt; expected verdict
SHIP or SHIP_WITH_NOTES close-in-place.
