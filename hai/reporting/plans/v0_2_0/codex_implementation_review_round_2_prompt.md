# Codex Implementation Review — v0.2.0 cycle (round 2)

> **Why this round.** Round 1 returned `SHIP_WITH_FIXES` with 5
> findings (F-IR-01 through F-IR-05). The maintainer landed 6
> commits on `main` addressing every finding (one commit per
> finding plus the round-1 IR-response artifact); each fix ran
> the full pytest broader-warning gate green before the commit.
> This round verifies the fixes, watches for second-order issues
> the response may have introduced (per AGENTS.md "If round N
> has *more* findings than round N-1, the previous response
> introduced second-order issues — re-read your own diff"), and
> re-runs the ship gates against the new tree.
>
> **Empirical settling shape (twice-validated).** Implementation
> review settles `5 → 2 → 1-nit` for substantive cycles. If
> round 2 surfaces ≥5 net-new substantive findings, that's an
> alarm bell — re-read the round-1 response diff before adding
> findings.
>
> **You are starting fresh.** This prompt and the round-1
> artifacts it cites are everything you need; do not assume
> context from a prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd                                          # /Users/domcolligan/health_agent_infra
git branch --show-current                    # main
git log --oneline 20c2129..HEAD              # round-1 fix commits + this prompt + any meta
git status                                   # clean (untracked planning artifacts ok)
```

The round-1 → round-2 commit window starts at the round-1 IR
prompt commit (`20c2129`). The required content is the 5 fix
commits + 1 IR-response artifact commit; this prompt and any
subsequent doc-only meta-commits ride on top and are expected
extras, not Step-0 mismatches. Confirm the 5 + 1 are present:

```bash
git log --oneline --grep='^fix(v0.2.0): IR R1' 20c2129..HEAD
git log --oneline --grep='IR round 1 response' 20c2129..HEAD
```

The first command must list **exactly 5** commits with subjects
matching `fix(v0.2.0): IR R1 F-IR-{01,02,03,04,05}`. The second
command must list **exactly 1** commit (`docs(v0.2.0): D15 IR
round 1 response — SHIP_WITH_FIXES verdict`). The diff window
also includes this round-2 prompt and any doc-only follow-ups
the maintainer added (e.g., a Step-0 tolerance fix); those are
the expected meta-commits, not findings.

If the `--grep` searches return the wrong count (≠ 5 / ≠ 1),
stop and surface. Ignore `/Users/domcolligan/Documents/`.

---

## Step 1 — Read orientation artifacts (in order)

1. **`AGENTS.md`** — operating contract; provenance discipline.
2. **`reporting/plans/v0_2_0/PLAN.md`** — cycle contract (11 W-ids).
3. **`reporting/plans/v0_2_0/codex_implementation_review_response.md`**
   — round-1 findings (5).
4. **`reporting/plans/v0_2_0/RELEASE_PROOF.md`** — what shipped.
5. **`reporting/plans/v0_2_0/REPORT.md`** — narrative summary.

Then open the round-1 → round-2 diff:

```bash
git diff 20c2129..HEAD -- src/ verification/ reporting/docs/
git diff 20c2129..HEAD -- README.md \
    reporting/plans/README.md \
    reporting/docs/current_system_state.md
git log -p 20c2129..HEAD -- reporting/plans/v0_2_0/
```

The full v0.2.0 implementation review (Phase 1 + 2 + 3 + 5)
already happened in round 1; round 2 is scoped to the
round-1 → round-2 delta plus second-order regression checks.

---

## Step 2 — Audit questions (this round)

### Q-IR-R1-fixes — verify each round-1 finding closed correctly

For every round-1 finding, walk the cited fix commit and
assert (a) the bug is gone, (b) no second-order regression
landed alongside.

#### F-IR-04 freshness sweep (`ea4c432`)

Round-1 claim: README.md, reporting/plans/README.md, and
current_system_state.md "Next cycles" table all over-claimed
ship-prep status.

Verify:
1. `README.md` badge reads `tests-2940_passing` (not 2733).
2. `README.md` status block names "v0.2.0 ship-prep complete
   2026-05-07" + "v0.2.1 (insight ledger — W53) is next-active
   post-v0.2.0 ship". Command count says 68 (not 67).
3. `reporting/plans/README.md` header dated 2026-05-07. Tree
   listing includes `v0_2_0/` row. Cycle directory list has a
   v0.2.0 entry. "Scope next release" section points at v0.2.0
   PLAN + RELEASE_PROOF (not v0.1.18 / v0.1.19).
4. `current_system_state.md` "Next cycles" table now has
   v0.2.0 marked ship-prep complete + v0.2.1 row added as
   next-active.

If any surface is still stale: F-IR-04 is partially closed →
fix-and-reland.

#### F-IR-03 bandit (`ccf3cbd`)

Round-1 claim: `# nosec B608` on different line from f-string;
gate exited non-zero with 2 findings.

Verify:
1. `uvx bandit -ll -r src/health_agent_infra` exits 0.
2. The output reports 0 Medium / 0 High issues; `Total
   potential issues skipped due to specifically being disabled
   (e.g., #nosec BXXX)` ≥ 37 (was 35 before fix; +2 from the
   2 sites this commit moved).
3. `core/eval/factuality_gate.py:382-383` has nosec on the
   f-string line itself, not the line above.
4. `core/state/snapshot.py:1499` SQL collapsed into one
   f-string line with nosec on it (was 4-line concat with nosec
   on closing paren).

If bandit still exits non-zero: F-IR-03 not closed.

#### F-IR-02 mypy (`bc3ba80`)

Round-1 claim: 11 errors across 5 files.

Verify:
1. `uvx mypy src/health_agent_infra` exits 0 with `Success: no
   issues found in 158 source files`.
2. Spot-check that the per-file fixes match the IR finding's
   recommendation:
   - `evals/scenarios/factuality/_build_corpus.py:221` →
     `bad_locators: list[dict[str, Any]]` annotation present.
   - `core/synthesis.py:1255-1257` → `proposal_id` /
     `planned_id` local vars hold the lookup; mypy narrows.
   - `core/explain/queries.py` → new `_make_row_getter` helper
     with `Callable[[str], Any]` return; per-iteration lambda
     gone.
   - `evals/scenarios/atomic_claims/_build_corpus.py:203-205`
     → parameter type `Sequence[T]` not `list[T]`; default
     `()` valid.
   - `cli/handlers/review.py:387` → `if conn is not None / else`
     split with scoped `# type: ignore[arg-type]` on the
     duck-typed `_NullConn()` call.
   - `cli/handlers/review.py:426-428` → `assert first is not
     None` after `not outcome.all_passed`.

If mypy still has errors: F-IR-02 not closed.

#### F-IR-05 W52 multi-canonical disposition (`7a5f7ac`)

Round-1 claim: `_multi_canonical_day_count()` always returned 0
because `WeeklyCoverage` carried no metadata; the markdown
disposition footer was unreachable.

Verify:
1. `core/review/weekly.py` `WeeklyCoverage` carries
   `multi_canonical_dates: list[str]` (default `field(default_factory=list)`).
2. `evaluate_weekly_coverage` populates the field by counting
   plans per `for_date` in the aggregation.
3. `core/review/render.py` `_multi_canonical_day_count` reads
   `coverage.multi_canonical_dates` (not literal `0`).
4. `render_json` carries `multi_canonical_dates` inside the
   `coverage` block.
5. New tests in `verification/tests/test_review_weekly.py` —
   positive case asserts the markdown disposition prose
   ("Multiple plans on this day") AND
   `multi_canonical_dates: ["2026-04-29"]` in JSON; negative
   case asserts neither appears when no date has multiple
   plans.

Run the targeted tests:
```bash
uv run pytest verification/tests/test_review_weekly.py::test_multi_canonical_disposition_surfaces_in_markdown_and_json -v
uv run pytest verification/tests/test_review_weekly.py::test_multi_canonical_disposition_absent_when_no_collision -v
```

Both should pass.

#### F-IR-01 W58D row-version drift (`294e82d`)

Round-1 claim (the strongest): the drift lane was tested
against a synthetic schema with a literal `row_version`
column, but the real `accepted_recovery_state_daily` schema
uses `projected_at`. A repro using `initialize_database()`
with a stale locator returned `GateOutcome.PASS` instead of
`LOCATOR_ROW_VERSION_DRIFT`.

Verify:
1. `core/provenance/locator.py` carries `_ROW_VERSION_COLUMN`
   mapping: every accepted-state table → `projected_at`,
   `source_daily_garmin` → `None`. Doc-comment cites
   state_model_v1.md + `_accepted_state_versions` snapshot
   helper + `domains/recovery/policy.py:273` emitter.
2. `core/eval/factuality_gate.py` drift check resolves the
   comparison column via `_ROW_VERSION_COLUMN.get(table)`.
   Comparison coerces with `str()` so `sqlite3.Row` types
   survive intact. Function docstring rewritten to cite the
   IR R1 F-IR-01 origin.
3. `evals/scenarios/factuality/_seed.py` synthetic schema
   renamed `row_version` → `projected_at`. The locator field
   stays `row_version` (per W-PROV-1 contract).
4. `verification/tests/test_factuality_gate.py` synthetic
   conn fixture matches the seed rename. New
   `test_gate_claim_drift_runs_against_real_accepted_state_schema`
   uses `initialize_database()` to spin up the real schema,
   inserts one row with a known `projected_at`, and asserts
   stale locator → BLOCK + LOCATOR_ROW_VERSION_DRIFT, matching
   locator → PASS.

Run:
```bash
uv run pytest verification/tests/test_factuality_gate.py -v
uv run hai eval run --scenario-set factuality
```

`hai eval run --scenario-set factuality` should still report
`known-bad: 85/85 blocked (100.00%)` and `known-good: 75/75
passed (100.00%)` — schema rename should not perturb corpus.

If the regression test would have passed *without* the fix
(i.e., `_ROW_VERSION_COLUMN` always returns the same column the
old code looked up), that's an alarm bell — verify by reading
the test carefully against the old behavior.

### Q-second-order — did round-1 fixes introduce new defects?

Per AGENTS.md "If round N has *more* findings than round N-1,
the previous response introduced second-order issues."

Walk the round-1 → round-2 diff and ask:

1. **F-IR-02 cascades.** The mypy fixes touched 5 files with
   active runtime use. Did any `cli/handlers/review.py`
   behavior change beyond the type annotation? The `assert
   first is not None` raises `AssertionError` if Python is
   run with `-O` (asserts disabled). Is that an acceptable
   posture for v0.2.0? Argue.
2. **F-IR-05 cascades.** The new `multi_canonical_dates`
   field appears in JSON output. Does any byte-stable JSON
   test pin the prior schema and now silently break? Run:
   ```bash
   uv run pytest verification/tests/test_review_weekly_byte_stable.py -v
   ```
3. **F-IR-01 cascades.** Did the `_seed.py` schema rename
   break the W-FACT-ATOM corpus generator (which imports
   `SEED_DATE`, `SEED_USER_ID`, `SEED_ROW_VERSION`)? Is the
   `evals/scenarios/factuality/index.json` byte-stable across
   the rename, or does the corpus need re-generation?
4. **F-IR-04 cascades.** The README badge now claims
   `tests-2940_passing`. After F-IR-05 + F-IR-01 added 3
   tests, the actual count is 2,943. Mismatch is a freshness
   gap (a finding on a finding) — verify against `pytest -q`
   final line.

### Q-ship-gates — re-run from clean tree

```bash
uv run pytest verification/tests -W error::Warning -q
uv run pytest verification/tests -W error::pytest.PytestUnraisableExceptionWarning -q
uvx mypy src/health_agent_infra
uvx bandit -ll -r src/health_agent_infra
uv run hai capabilities --json | uv run python -c \
    "import json,sys; print(len(json.load(sys.stdin)['commands']))"  # 68
uv run hai eval run --scenario-set all
uv run hai eval run --scenario-set factuality
HAI_RUN_PERSONA_MATRIX=1 uv run python -m verification.dogfood.runner /tmp/v0_2_0_ir_r2_persona_run
```

Expected:
- pytest broader gate: **2,943 passed, 4 skipped** (was 2,940
  before round-1 fixes; +1 from F-IR-01 regression test, +2
  from F-IR-05 disposition tests).
- mypy: clean.
- bandit: clean.
- factuality eval: 100/100.
- Persona matrix: 13/13, 0 findings, 0 crashes.

If any drifts: that's the round-2 finding.

### Q-honesty-boundary-gates (G15, G16, G17) — unchanged

Round-1 verified these. Re-confirm RELEASE_PROOF wasn't
mutated this round to walk back any claim:
- G15: NO foreign-user empirical claim.
- G16: NO LLM-judge factuality claim.
- G17: NO insight-ledger persistence claim.

### Q-provenance discipline

Round-1 caught no provenance drift. Spot-verify the round-2
diff's claims (commit messages, RELEASE_PROOF deltas if any)
against on-disk truth.

### Q-summary-surface — F-IR-04 fixed three; check the rest

The full freshness checklist (AGENTS.md):
- ROADMAP.md "Now" — already updated pre-IR-R1.
- AUDIT.md — already updated pre-IR-R1.
- README.md — F-IR-04 fixed.
- current_system_state.md — F-IR-04 fixed (Next-cycles row).
- reporting/plans/README.md — F-IR-04 fixed.
- tactical_plan_v0_1_x.md — already updated pre-IR-R1
  (commit `20c2129`).
- success_framework_v1.md — spot-check for stale references.
- risks_and_open_questions.md — spot-check for stale references.
- CHANGELOG.md — `[Unreleased] — v0.2.0 in flight` should
  cover W52 + W-FACT-ATOM + W58D + the round-1 IR fixes
  (factuality gate drift fix + multi-canonical disposition
  + mypy + bandit + freshness).

If any new freshness gap appears (e.g., the test count moved
from 2,940 → 2,943 and a doc says 2,940), that's a fix-and-reland.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_2_0/codex_implementation_review_round_2_response.md`:

```markdown
# Codex Implementation Review — v0.2.0 (round 2)

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES | DO_NOT_SHIP
**Round:** 2

## Verification summary
- Round-1 → round-2 delta: 6 commits …
- Test surface: …
- Ship gates: …
- Persona matrix: …
- Round-1 finding closures: F-IR-01 closed | F-IR-02 closed | …

## Findings (this round only)

### F-IR-R2-01. <short title>
**Q-bucket:** Q-IR-R1-fixes / Q-second-order / Q-summary-surface / …
**Severity:** correctness-bug | security | scope-mismatch | provenance-gap | acceptance-weak | nit
**Reference:** <commit SHA / file:line>
**Argument:** <what + citations>
**Recommended response:** <fix-and-reland | accept-as-known | …>

## Round-1 finding disposition

| F-IR | Closure | Notes |
|---|---|---|
| F-IR-01 | closed / open / partial | … |
| F-IR-02 | … | … |
| F-IR-03 | … | … |
| F-IR-04 | … | … |
| F-IR-05 | … | … |

## Open questions for maintainer
```

A finding is triageable; a vague concern is not. "F-IR-01 fix
references `_ROW_VERSION_COLUMN["source_daily_garmin"] = None`,
but the doc-comment claims source-table emission is out of
v0.1.14 scope — verify the W-PROV-2 deltas didn't open a
source-table emission path on accepted-state-only domains" is.

---

## Step 4 — Verdict scale

Standard. SHIP / SHIP_WITH_NOTES / SHIP_WITH_FIXES / DO_NOT_SHIP.
Most-likely outcome given round-1 closed cleanly: `SHIP_WITH_NOTES`
or `SHIP`. The `5 → 2 → 1-nit` empirical settling shape predicts
≤2 substantive findings this round.

---

## Step 5 — Out of scope

- Round-1 findings themselves (those are reviewed for closure,
  not re-litigated).
- Cycle scope (PLAN.md is closed at PLAN_COHERENT round 4).
- Strategic-plan / tactical-plan content beyond the deltas the
  cycle applied.
- Named-deferrals (W-2U-WEARABLE, W-2U-DOGFOOD, W58J, W53).
- Next-cycle scope (v0.2.1 W53).

---

## Step 6 — Cycle pattern

```
D14 plan-audit ✓ (4 rounds, PLAN_COHERENT)
Phase 0 (D11) ✓
Pre-implementation gate ✓
Implementation ✓
RELEASE_PROOF + REPORT + freshness sweep ✓
Codex implementation review round 1 ✓ SHIP_WITH_FIXES (5 findings)
Maintainer round-1 response ✓ (6 commits closing all 5 findings)
Codex implementation review round 2 ← you are here
…
Maintainer ship-time manual TTY gate (only after IR settles)
```

---

## Step 7 — Verdict-routing reminder

- `SHIP` → maintainer proceeds to version bump + manual TTY ship gate.
- `SHIP_WITH_NOTES` → maintainer authors a `_response_response.md`
  enumerating disposition (carry-to-v0.2.1 vs accept-as-known)
  and proceeds to ship.
- `SHIP_WITH_FIXES` → maintainer fixes-and-relands, then round 3
  fires.
- `DO_NOT_SHIP` → maintainer adjudicates; cycle may abort.
