# v0.1.17 Codex IR Round 1 — Maintainer response

**Cycle:** v0.1.17 (substantive, D15-tiered).
**Round-1 verdict from Codex:** `SHIP_WITH_FIXES`, 6 findings.
**Maintainer disposition:** all 6 closed at IR-R1; cycle re-stamped.
**Date:** 2026-05-05.

Codex round-1 review at
`reporting/plans/v0_1_17/codex_implementation_review_response.md`.

---

## §1 Per-finding disposition

### F-IR-01 — Bandit gate red on 3 Medium B608

**Disposition:** Fix-and-reland.

**Diagnosis:** RELEASE_PROOF §2 claimed "0 medium / 0 high" but I
never re-ran Bandit after W-B (`body_comp/store.py`),
F-PV14-02 (`sync/purge.py`), and W-D arm-2's
`get_active_macro_targets` site landed. All three are real B608
trips. The pre-existing `# nosec B608` annotation on
`target/store.py:469` was placed three lines above the f-string —
Bandit only honors same-line annotations, so it was effectively
dead.

**Fix:**
- `core/body_comp/store.py:174`: same-line `# nosec B608` with
  rationale (where[] entries are literal predicates from this
  function's source; values bind via params).
- `core/sync/purge.py:110`: same pattern.
- `core/target/store.py:469`: relocated the existing nosec from a
  comment-block 3 lines above the f-string to same-line on the
  f-string.

Pattern matches the established `intent/store.py:239` /
`intake/presence.py:190` style. All three sites' WHERE-clause
construction is from literal predicates in module source; user
values continue to bind via `?` placeholders.

**Verification:** `uvx bandit -ll -r src/health_agent_infra` →
0 Medium / 0 High; total skipped suppressions 27 (was 24).

---

### F-IR-02 — `hai eval review show/tag/dismiss` broken on judge_adversarial

**Disposition:** Fix-and-reland.

**Diagnosis:** Real correctness bug. `_walk_corpus()` (review.py:298)
listed judge_adversarial fixtures via
`fixture.get("scenario_id") or fixture_path.stem`, so `list --corpus
judge_adversarial` surfaced their `fixture_id`. But
`_find_in_corpus()` (review.py:308) only matched
`fixture.get("scenario_id") == scenario_id`, and judge_adversarial
fixtures carry only `fixture_id`. show/tag/dismiss were broken for
that corpus.

**Fix:** Normalised `_find_in_corpus()` to the same id contract as
`_walk_corpus()`: a fixture is selectable by its `scenario_id` (domain
convention) ∨ `fixture_id` (judge_adversarial convention) ∨ file stem.
Updated docstring to make the contract explicit.

**Regression test:** Added two new tests to
`test_w_ai_2_eval_review.py`:
- `test_show_resolves_judge_adversarial_fixture_id` — verifies show
  returns the ja_bp_001 fixture body keyed by fixture_id.
- `test_tag_then_dismiss_roundtrip_judge_adversarial` — full
  tag → dismiss → list with --include-dismissed round-trip.

**Verification:** 13/13 W-AI-2 tests pass.

---

### F-IR-03 — W-D arm-2 missed `hai explain` projection rendering

**Disposition:** Fix-and-reland.

**Diagnosis:** Real scope-mismatch. PLAN §2.I item 6 mandated
`hai explain --as-of <today>` surfaces both observed calories and
`projected_eod_kcal`. The implementation shipped the classifier
extension + snapshot serializer + integration tests for items 1-5
and item 7, but the explain rendering path was never extended.

**Architectural choice:** The fix had three viable paths:

1. **Recompute snapshot at explain time** — clean but violates the
   `core/explain/queries.py` "no recomputation" contract.
2. **Persist projection in `proposal_log.payload_json`** — requires
   synthesis to receive + thread the classified state into proposal
   construction; touches the agent-authored proposal payload contract.
3. **Persist in `daily_plan.synthesis_meta`** — already a flexible
   JSON column on the plan row that explain already reads via
   `ExplainPlan.synthesis_meta`. Synthesis already has the snapshot
   in scope.

Chose Path 3 — minimum surface, audit-chain-honest, no schema change.

**Fix:**
- `core/synthesis.py:~1024`: when building `plan_dict`, extract
  `snapshot["nutrition"]["classified_state"]` + the observed
  `today_row` from `nutrition_signals` and embed in
  `synthesis_meta["domain_classified_states"]["nutrition"]` (under
  `classified` and `observed` sub-keys).
- `core/explain/render.py`: new `_format_domain_classified_states_section()`
  helper. After the plan header, render observed values + projection
  + headline bands when `synthesis_meta.domain_classified_states.nutrition`
  is present. Empty-string return preserves byte-stable text output for
  pre-W-D-arm-2 plans (no domain_classified_states → no section).
- `bundle_to_dict()` was already serializing `synthesis_meta` verbatim
  via `_plan_to_dict()`, so the JSON view inherits the new field with
  no code change.

**Regression test:** Added
`test_hai_explain_renders_observed_and_projected_eod_for_arm2` to
`test_w_d_arm2_target_plumbing.py` (acceptance item 6 was previously
declared in the file's docstring but never implemented). Tests the
end-to-end path: seed targets + partial-day intake → build_snapshot
→ project_proposal → run_synthesis → load_bundle_for_date →
bundle_to_dict and render_bundle_text. Asserts both
`observed.calories=1344` and `classified.projected_eod_kcal=3100`
appear in the JSON view; asserts the text view contains
`"calories     : 1344"` and `"projected_eod_kcal      : 3100"`.

**Verification:** 7/7 W-D arm-2 tests pass (was 6/7).

---

### F-IR-04 — W-AH-2 fixtures pass classifier axis vacuously

**Disposition:** Fix-and-reland (mechanical).

**Diagnosis:** Real acceptance-weak. The runner treats missing
`expected.classified` as `{}` and silently passes the
`classified_bands` axis. 121 of 135 non-judge fixtures (or, of the
100 added in W-AH-2: 95 domain - 1 already-having = 94 missing per
Codex's count; my full survey including pre-existing fixtures with
the same gap) lacked `expected.classified`, so `135/135 PASS` was
not actually validating the classifier paths.

This is the v0.1.14 W-AM lesson rediscovered in a different shape:
not "batch-validate without per-fixture iteration" but "per-fixture
iteration without verifying the validation surface is non-vacuous."
Generalisation: **validate that your validator validates.**

**Fix (Level 1, mechanical):** A one-shot script
(`/tmp/backfill_classified.py`, not committed — script is a build
tool, not a fixture artifact) walked every domain fixture missing
`expected.classified`, ran the live classifier on the fixture's
`input` block, then wrote a stable per-domain subset of the actual
classifier output back as `expected.classified`. Backfilled 106
fixtures across 6 domains; skipped 14 already-curated; 0 failures.
Per-domain key sets cover the bands policy actually consumes (e.g.
nutrition: calorie_balance_band + protein_sufficiency_band +
hydration_band + coverage_band + nutrition_status +
micronutrient_coverage).

Synthesis fixtures are intentionally outside this backfill —
`run_synthesis_scenario` doesn't go through `_domain_classify` and
asserts on `x_rules_fired` / `final_actions` / `final_confidences`
instead.

**Mutation spot-check** (verifying the axis is now non-vacuous):
flipped `nutrition_011_under_hydration_macros_met`'s
`hydration_band` from `"low"` → `"definitely_wrong_band"`; re-ran
`hai eval run --domain nutrition --json`. Result: 19/20 passed,
1/20 failed, with the failure correctly tagged
`axes.classified_bands="fail"` and the diff naming the band. Restored.

**What this does NOT catch:** semantic intent/computation mismatches.
If a fixture named `nutrition_011_under_hydration_macros_met` actually
classifies as `hydration_band="met"` (computation diverges from
intent), the Level-1 backfill freezes the divergence rather than
catching it. Level 2 would be a per-fixture intent ↔ computation
audit; that's a substrate-quality pass that warrants its own
workstream and is not in IR-R1 scope. Surfaced as an open item for
R2 and as a candidate workstream for v0.1.18+ (the W-AH-3 candidate).

**Verification:** `hai eval run --scenario-set all` → 135/135 PASS
with non-vacuous classifier-axis assertions.

---

### F-IR-05 — Wheel ships deleted `cli.py` from stale build/ cache

**Disposition:** Fix-and-reland (build-artifact hygiene + smoke).

**Diagnosis:** Real provenance gap. `build/lib/health_agent_infra/cli.py`
(385 KB) survived from a pre-W-29 build run on May 3; setuptools picked
it up on the v0.1.17 rebuild and shipped it inside the wheel alongside
the new `cli/__init__.py` package. Python's import resolver picks the
package over the module, so installs imported the right surface — but
the artifact still shipped 385 KB of dead source.

**Fix:**
- New `verification/tests/test_wheel_artifact_no_pre_split_cli.py`
  parametrizes over wheels under `dist/` and refuses any wheel that
  contains both `health_agent_infra/cli.py` AND
  `health_agent_infra/cli/__init__.py` at the package root. Pre-W-29
  wheels (no `cli/__init__.py`) are skipped — not the smoke's scope.
- Pre-publish hygiene: `rm -rf build/ dist/health_agent_infra-0.1.17*
  src/health_agent_infra.egg-info`, then
  `uvx --from build python -m build --wheel --sdist`. Verified — the
  rebuilt v0.1.17 wheel no longer contains the pre-split cli.py;
  smoke passes.

**Verification:** Smoke PASSED on the freshly rebuilt
`health_agent_infra-0.1.17-py3-none-any.whl`; SKIPPED on the
pre-existing `health_agent_infra-0.1.15.1-py3-none-any.whl` (correct —
pre-W-29 era, no cli/ package, smoke not applicable).

---

### F-IR-06 — `reporting/plans/hai_runtime_contract_paper/` landed unnamed

**Disposition:** Maintainer call accepted; named in REPORT.md §5.4.

**Diagnosis:** The 606-line `DRAFT_PAPER.md` + `IMPLEMENTATION_PLAN.md`
subtree landed in the F-PV14-02 commit (`d06d694`). It's forward-
looking research planning material for a HACO-Bench / runtime-contract
empirical paper — not part of any v0.1.17 W-id, not named in PLAN /
RELEASE_PROOF / REPORT.

**Disposition rationale:** The subtree's eventual owner is likely a
v0.2.x research cycle (post-W52 weekly-review + post-W58D claim-block
infrastructure), but the paper's scope is pre-decisional and naming
a specific destination cycle right now would silently commit the
maintainer to that scope. Lowest-disruption disposition: keep in tree,
name in `REPORT.md §5.4` as out-of-band research planning so it's
findable by future cycles, defer the destination decision.

If the maintainer prefers to relocate the subtree before publish (e.g.
to `reporting/plans/v0_2_x_research/`), this is a one-line `git mv`
that I can run on instruction.

---

## §2 Tree state at IR-R1 close

- All 6 IR-R1 findings closed in tree (uncommitted).
- pytest: **2688 passed, 5 skipped** (was 2683 + 4; +5 new tests, +1
  pre-W-29 wheel skip).
- mypy: clean (147 source files).
- bandit: 0 medium / 0 high (was 3 medium / 0 high).
- `hai eval run --scenario-set all`: 135/135 PASS with non-vacuous
  classifier-axis assertions.
- Capabilities markdown: byte-stable.
- Wheel-content smoke: PASSED on clean-rebuild v0.1.17 wheel.

`uv.lock` remains modified-in-tree from a pre-IR session; not touched
by IR-R1 work.

## §3 Suggested commit topology for IR-R1 fix-and-reland

Six commits, ordered by severity:

1. `fix(security): close 3 Bandit B608 trips with same-line nosec` —
   F-IR-01 sites in body_comp/store.py + sync/purge.py + target/store.py.
2. `fix(eval-review): _find_in_corpus matches walk_corpus id contract` —
   F-IR-02 review.py + test_w_ai_2_eval_review.py additions.
3. `feat(explain): surface W-D arm-2 nutrition projection in explain` —
   F-IR-03 synthesis.py + render.py + test_w_d_arm2_target_plumbing.py.
4. `chore(evals): backfill expected.classified across 106 fixtures` —
   F-IR-04 mass fixture edit (single commit per "scripted backfill"
   convention; backfill script is /tmp/ scratch, not committed).
5. `test(packaging): wheel-content smoke refuses pre-W-29 cli.py shadow` —
   F-IR-05 new test file; clean-rebuild artifact replacement.
6. `docs(plans): name runtime-contract-paper subtree as out-of-band; IR-R1 close` —
   F-IR-06 REPORT.md §5.4 + RELEASE_PROOF.md §2 / §7 honesty restamp +
   this response artifact.

## §4 Open items for IR-R2

- **Test-infra abstraction.** Codex round 2 may still want a shared
  `patch-cli-private-symbol` fixture in conftest.py (raised from R1
  REPORT.md §6 as a possible cleaner abstraction over the inline
  source-module patches). I deferred this in R1 because the inline
  edits are minimally invasive and easy to grep; introducing a shared
  fixture is a refactor that could be done at any time without
  blocking publish.

- **F-IR-04 Level 2 (semantic intent ↔ computation audit).** The
  Level-1 backfill pins the current classifier behavior but freezes
  any pre-existing intent ↔ computation divergences. R2 may surface
  specific fixtures where the name implies one band but the classifier
  emits another — those are real fixture-quality bugs, not classifier
  bugs. Routed as a candidate for v0.1.18+ rather than R2 in-cycle
  if they materialise.

- **F-IR-06 destination.** If the maintainer wants the paper subtree
  relocated rather than named-in-place, R2 will close the loop.

## §5 IR settling shape so far

| Round | Findings | Verdict |
|---|---:|---|
| 1 | 6 | SHIP_WITH_FIXES |

R1 returned 6 findings (within the AGENTS.md empirical norm of "round
1 typically returns 5-6 findings"). All closed in-place. R2 expected
to settle at the `5 → 2 → 1-nit` shape per the cumulative R1 →
R2 → R3 pattern.
