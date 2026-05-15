# Codex Implementation Review — v0.1.17 cycle, Round 2

> **Why this round.** Round 1 closed `SHIP_WITH_FIXES` with 6
> findings (F-IR-01 Bandit, F-IR-02 `_find_in_corpus`, F-IR-03 W-D
> arm-2 explain, F-IR-04 W-AH-2 vacuous classifier-axis, F-IR-05
> wheel cli.py shadow, F-IR-06 runtime-contract paper docs). The
> maintainer's R1 disposition + fix-and-reland trail is at
> `codex_implementation_review_round_1_response.md`. Round 2 audits
> the R1 fixes specifically — that they actually closed the cited
> defects, that no second-order issue snuck in, and that the
> RELEASE_PROOF / REPORT honesty restamp is accurate.
>
> **What you're auditing.** R1-fix delta only — six commits expected
> in the IR-R1 fix-and-reland series (see R1 response §3). Plus the
> RELEASE_PROOF.md §2 + §7 + REPORT.md §5.4 / §6 honesty edits.
>
> **NOT auditing:** the R0 implementation surface (R1 already
> covered that); the D14 plan-audit chain (closed at PLAN_COHERENT
> at v0.1.17 cycle-open); prior-cycle implementation (already
> shipped to PyPI).
>
> **Empirical norm:** R2 typically returns ~2 findings or 1 nit
> per AGENTS.md "Audit-chain empirical settling shape" (5 → 2 →
> 1-nit). If R2 returns *more* than R1, re-read your own R1 — the
> R1 disposition introduced second-order issues.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd                                          # /Users/domcolligan/health_agent_infra
git branch --show-current                    # main
git log --oneline e04c86f..HEAD              # IR-R1 fix-and-reland commits since the IR-R1 prompt commit
git status                                   # uv.lock M is pre-existing per R1 §2; otherwise clean
```

If the commit count is not roughly 6, ask the maintainer before
proceeding — the R1 fix-and-reland series should be exactly the
six topology commits enumerated in
`codex_implementation_review_round_1_response.md` §3.

---

## Step 1 — Read the R1 disposition + restamped artifacts (in order)

1. **`reporting/plans/v0_1_17/codex_implementation_review_round_1_response.md`** —
   per-finding disposition, fix descriptions, what was deliberately
   deferred to R2.
2. **`reporting/plans/v0_1_17/RELEASE_PROOF.md` §2 + §7** — restamped
   ship-gate values; restamped maintainer notes naming the IR-R1
   close.
3. **`reporting/plans/v0_1_17/REPORT.md` §5.4 + §6** — runtime-contract
   paper disposition + open-items-for-IR list updated.

Then walk the R1 fix delta:

```bash
git diff e04c86f..HEAD -- src/ verification/ reporting/
git diff e04c86f..HEAD -- AGENTS.md ROADMAP.md AUDIT.md \
    CHANGELOG.md pyproject.toml \
    reporting/plans/strategic_plan_v1.md \
    reporting/plans/tactical_plan_v0_1_x.md
```

---

## Step 2 — Audit questions

### Per-IR-R1-finding verification

- **Q F-IR-01 closure (Bandit B608).** Re-run
  `uvx bandit -ll -r src/health_agent_infra` and verify 0 Medium /
  0 High. Confirm the three suppressions are same-line, carry
  brief rationales, and follow the established
  `intent/store.py` / `intake/presence.py` style. Specifically:
  - `core/body_comp/store.py:174` — same-line `# nosec B608` on the
    first SQL string literal.
  - `core/sync/purge.py:110` — same shape.
  - `core/target/store.py:469` — relocated from comment-block above
    the f-string to same-line on the f-string.

  Defect to look for: any nosec annotation that's MORE permissive than
  the actual risk surface (e.g. one that hides a future user-input
  injection by precedent).

- **Q F-IR-02 closure (`_find_in_corpus`).** Verify the fix is
  symmetrical with `_walk_corpus`'s id contract:
  `scenario_id ∨ fixture_id ∨ stem`. Confirm
  `test_show_resolves_judge_adversarial_fixture_id` and
  `test_tag_then_dismiss_roundtrip_judge_adversarial` cover the
  contract that was broken. Defect to look for: id collisions —
  could a domain fixture's `scenario_id` ever match a
  judge_adversarial fixture's `fixture_id` and resolve to the wrong
  body? Spot-check by listing all
  scenario_id / fixture_id / stem values across the corpus.

- **Q F-IR-03 closure (W-D arm-2 explain rendering).**
  - Confirm `core/synthesis.py` writes
    `synthesis_meta["domain_classified_states"]["nutrition"]` only
    when the classifier emitted bands; pre-W-D-arm-2 plans (no
    nutrition signals → empty `nutrition_classified`) should not
    pollute synthesis_meta.
  - Confirm `core/explain/render.py` returns empty-string from
    `_format_domain_classified_states_section` for plans that lack
    `domain_classified_states`, so byte-stable text contract for
    pre-W-D-arm-2 plans holds.
  - Confirm the regression test
    `test_hai_explain_renders_observed_and_projected_eod_for_arm2`
    exercises the full integration path (build_snapshot →
    project_proposal → run_synthesis → load_bundle_for_date →
    bundle_to_dict + render_bundle_text).
  - Defect to look for: any pre-existing test that snapshots the
    text output of `render_bundle_text` for a W-D-arm-1 / no-arm-2
    plan that now has the new section silently appended (would be
    a byte-stability break on a snapshot file). The contract is
    "empty-string when the section has no data" — verify by
    grepping snapshot files.

- **Q F-IR-04 closure (W-AH-2 classifier axis).** Spot-check the
  Level-1 backfill on 5 fixtures of your choice (one per non-
  synthesis domain): does the dumped `expected.classified` match
  what the live classifier produces for the fixture's `input`? Run
  the spot check the maintainer ran (mutate one band, expect FAIL)
  on a different fixture. Surface any case where the backfilled
  bands are incoherent with the fixture name (the v0.1.18 W-AH-3
  candidate raised in R1 §4 — but R2 may name specific instances).

- **Q F-IR-05 closure (wheel-content smoke).**
  - Confirm `verification/tests/test_wheel_artifact_no_pre_split_cli.py`
    uses parametrize over `dist/*.whl` and skips pre-W-29 wheels
    (no `cli/__init__.py` → pytest.skip).
  - Confirm the v0.1.17 wheel under `dist/` doesn't contain
    `health_agent_infra/cli.py` at top-level (just
    `health_agent_infra/cli/__init__.py` + the W-29 split tree).
  - Defect to look for: the smoke is dist-driven; if `dist/` is
    empty in CI, the test silently no-ops. Is that the right
    behavior, or should there be a maintainer-only "fail loudly
    when no wheel to check" mode? (R2 may surface this as a nit.)

- **Q F-IR-06 closure (runtime-contract paper docs).** Confirm
  `REPORT.md §5.4` names the subtree explicitly. The maintainer
  deferred relocation; if R2 wants to push for relocation, name
  the destination cycle (and explain why now vs later).

### Cross-cutting

- **Q ship-gate honesty.** Re-run all gates. Compare actual values
  to RELEASE_PROOF.md §2's restamped numbers. The maintainer claimed:
  - pytest: 2688 passed, 5 skipped.
  - mypy: clean (147 source files).
  - bandit: 0 medium / 0 high; 27 suppressions.
  - eval scenario set: 135/135 PASS.
  - capabilities markdown: byte-stable.
  - wheel-content smoke: PASSED on rebuilt v0.1.17 wheel.
  Any divergence is a R2 finding.

- **Q second-order issues from R1 fixes.** Did any R1 fix introduce a
  new defect? Specifically:
  - The `synthesis_meta["domain_classified_states"]` extension: any
    test that pinned the exact synthesis_meta shape (e.g. on a
    snapshot file) would now be drift?
  - The Level-1 backfill of 106 fixtures: did any fixture file
    shape change (other than the new `expected.classified` block)
    that could surprise the corpus-coverage test?
  - The wheel-content smoke: any pytest collection-side warning
    on the parametrize-over-glob pattern?

- **Q deferral honesty.** R1 §4 routed F-IR-04 Level 2 (intent ↔
  computation semantic audit) as a candidate for v0.1.18+. Is
  that the right destination? Is there any case where it must be
  closed before publish (e.g. a fixture name promising a band
  combination that would mislead a foreign user reading the
  fixture corpus)?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_17/codex_implementation_review_round_2_response.md`:

```markdown
# Codex Implementation Review — v0.1.17 Round 2

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES
**Round:** 2

## Verification summary
- Tree state: …
- Test surface: …
- Ship gates: …

## Findings

### F-IR-R2-01. <short title>
**Q-bucket:** ...
**Severity:** correctness-bug | security | scope-mismatch | provenance-gap | acceptance-weak | nit
**Reference:** <commit SHA / file:line> or "absent"
**Argument:** <what + citations>
**Recommended response:** <fix-and-reland | accept-as-known | ...>

## Per-finding R1-closure verdicts

| Finding | R2 verdict | Note |
|---|---|---|
| F-IR-01 | CLOSED | ... |
| F-IR-02 | CLOSED | ... |
| F-IR-03 | CLOSED | ... |
| F-IR-04 | CLOSED_PARTIAL | Level 2 routed v0.1.18 |
| F-IR-05 | CLOSED | ... |
| F-IR-06 | CLOSED_NAMED | ... |

## Open questions for maintainer
```

Each finding triageable per the R1 prompt's same template.

---

## Step 4 — Verdict scale

- **SHIP** — merge + publish, no further work.
- **SHIP_WITH_NOTES** — merge + publish; named follow-ups carry
  to next cycle. Notes enumerate every non-blocking finding.
- **SHIP_WITH_FIXES** — fix-and-reland. Notes enumerate every
  blocking finding. Round-3 review after maintainer addresses.
- **DO_NOT_SHIP** — only on correctness/security bug warranting
  commit reverts.

For R2 specifically, the canonical shape is `SHIP` (clean close)
or `SHIP_WITH_NOTES` (1-nit close-in-place). `SHIP_WITH_FIXES`
on R2 means a real bug got past R1 — investigate carefully.

---

## Step 5 — Out of scope

- R0 implementation that R1 already audited. (Re-cite an R1 finding
  only if its R1 disposition was incomplete.)
- D14 plan-audit chain (closed at PLAN_COHERENT at cycle-open).
- Prior-cycle surfaces (already shipped to PyPI).
- F-IR-04 Level 2 semantic audit beyond surface naming — that's
  v0.1.18+ scope per R1 §4.
- The R1 commit topology itself; if six commits land cleanly with
  byte-stable manifest, the topology is fine.

---

## Step 6 — Cycle pattern

```
D14 plan-audit ✓
Phase 0 (D11) ✓
Pre-implementation gate ✓
Implementation ✓ 27 commits at e04c86f
IR Round 1 ✓ SHIP_WITH_FIXES; 6 findings
IR-R1 fix-and-reland ✓ 6 commits + RELEASE_PROOF/REPORT honesty
IR Round 2 ← you are here
  → SHIP / SHIP_WITH_NOTES → publish to PyPI
  → SHIP_WITH_FIXES → maintainer + R2 fix-and-reland → R3 review
RELEASE_PROOF.md + REPORT.md restamped at IR-R1 close ✓
PyPI publish (per reference_release_toolchain.md)
```

Estimated: 1 session per round.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_17/codex_implementation_review_round_2_response.md`
  (new) — your findings.

**No code changes.** No source commits. No state mutations.

If you find a correctness/security bug warranting `DO_NOT_SHIP`,
name it explicitly and stop the review for maintainer adjudication.

---

## Per-cycle close-out

**Round-2 expected verdict:** `SHIP_WITH_NOTES` or `SHIP`. The
maintainer expects R2 to surface ≤2 findings (per the empirical
5 → 2 → 1-nit shape) — most plausibly:

- A second-order issue from the F-IR-03 explain rendering (e.g. a
  pre-existing snapshot-file consumer of render_bundle_text that
  drifted).
- A nit from the F-IR-04 Level-1 backfill (e.g. an obviously
  misnamed fixture caught during spot-check).
- A nit from the F-IR-05 smoke (e.g. should-be-louder when dist/ is
  empty).

If R2 returns *more* than R1, re-read your own R1 disposition — R1
introduced a second-order regression somewhere.

**Out-of-scope for R2:** PyPI publish (held until R2 closes
SHIP/SHIP_WITH_NOTES); v0.1.18 onboarding cycle scope (opens after
v0.1.17 ships); v0.1.19 foreign-user empirical work.
