# Codex Implementation Review — v0.2.0 cycle (round 3)

> **Why this round.** Round 2 returned `SHIP_WITH_FIXES` with one
> finding (F-IR-R2-01: round-1 fixes added 3 tests but seven
> summary surfaces still published the 2940 / +184 numbers; the
> CHANGELOG also did not record the round-1 IR fixes). The
> maintainer landed two commits on `main` to close it: the
> doc-only freshness propagation + CHANGELOG bug-fix block, and
> the round-2 response artifact. This round verifies the fix
> closed cleanly and that no new freshness gap or second-order
> issue rode along.
>
> **Empirical settling shape (twice-validated).** Implementation
> review settles `5 → 2 → 1-nit` for substantive cycles. Round 3
> is expected to land at SHIP or SHIP_WITH_NOTES with at most a
> single nit. If round 3 surfaces a fresh substantive finding,
> something in the round-2 response introduced second-order
> drift — re-read your own diff before adding findings.
>
> **You are starting fresh.** This prompt and the round-2
> artifacts it cites are everything you need; do not assume
> context from a prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd                                          # /Users/domcolligan/health_agent_infra
git branch --show-current                    # main
git log --oneline 22eb6d5..HEAD              # round-2 fix commits + this prompt
git status                                   # clean (untracked planning artifacts ok)
```

The round-2 → round-3 commit window starts at the round-2 prompt
Step-0 tolerance fix (`22eb6d5`). The required content is one
fix commit (`fix(v0.2.0): IR R2 F-IR-R2-01 — propagate +3 IR R1
test delta + CHANGELOG entries`) plus one response-artifact
commit (`docs(v0.2.0): D15 IR round 2 response — SHIP_WITH_FIXES
(F-IR-R2-01)`). This prompt rides on top.

Confirm by content-grep:

```bash
git log --oneline --grep='^fix(v0.2.0): IR R2 F-IR-R2-01' 22eb6d5..HEAD
git log --oneline --grep='IR round 2 response' 22eb6d5..HEAD
```

Each must list **exactly 1** commit. If either count is wrong,
stop and surface. Ignore `/Users/domcolligan/Documents/`.

---

## Step 1 — Read orientation artifacts (in order)

1. **`AGENTS.md`** — operating contract; "Patterns the cycles
   have validated" → summary-surface sweep.
2. **`reporting/plans/v0_2_0/PLAN.md`** — cycle contract.
3. **`reporting/plans/v0_2_0/codex_implementation_review_response.md`**
   — round-1 findings (5).
4. **`reporting/plans/v0_2_0/codex_implementation_review_round_2_response.md`**
   — round-2 finding (1: F-IR-R2-01).
5. **`reporting/plans/v0_2_0/RELEASE_PROOF.md`** — §2 now carries
   both "Phase 3 close" and "Post-IR R1 close" empirical blocks.
6. **`reporting/plans/v0_2_0/REPORT.md`** — §4 test surface
   updated with ship-time + per-W-id IR R1 closure row.

Open the diff:

```bash
git diff 22eb6d5..HEAD -- README.md ROADMAP.md CHANGELOG.md \
    reporting/docs/current_system_state.md \
    reporting/plans/README.md \
    reporting/plans/v0_2_0/
```

---

## Step 2 — Audit questions (this round)

### Q-IR-R2-fix — verify F-IR-R2-01 closed correctly

Round-2 claim: 7 surfaces published `2940` / `2,940` / `2940_passing`
or `+184` when the actual ship-time count is 2943 / +187. CHANGELOG
also did not record the 5 round-1 IR fixes.

Walk each surface and assert the published count matches the
post-IR R1 ship-time count, AND that the CHANGELOG carries the
required bug-fix entries.

Required surfaces — each must publish 2943 (not 2940):

1. `README.md` line ~20 badge: `tests-2943_passing`.
2. `README.md` status block: `2,943-test gate`.
3. `ROADMAP.md` "Now" v0.2.0 line: `2,943 passed, 4 skipped`,
   `+187 vs v0.1.18 baseline of 2,756`, `2.2×` ratio.
4. `reporting/docs/current_system_state.md` "Test gate at
   release" row: `2943 passed, 4 skipped`, `+187`, `2.2×`.
5. `reporting/plans/README.md` v0.2.0 cycle entry: `2943
   passed`, `+187`.
6. `reporting/plans/v0_2_0/RELEASE_PROOF.md` §2: keep "Phase 3
   close empirical" 2940 block; new "Post-IR R1 close
   empirical (ship-time)" 2943 block present; §6 cycle-stats
   line updated to 2943 + delta +187 + 2.2×.
7. `reporting/plans/v0_2_0/REPORT.md` §4: Phase-3 close 2940
   preserved; ship-time 2943 row added; total delta +187 with
   "Phase-3 close +184 + IR R1 regression +3" breakdown; new
   "IR R1 closure" per-W-id growth row.

CHANGELOG bug-fix entries (under `## [Unreleased] — v0.2.0 in
flight` → `### Bug fix`):
- W58D real-schema row-version drift (F-IR-01).
- W52 multi-canonical disposition reachable (F-IR-05).
- Repo-wide mypy clean (F-IR-02).
- Repo-wide bandit clean (F-IR-03).
- Summary-surface freshness sweep (F-IR-04).

If any of the 7 surfaces still publishes 2940 / +184 / 2.1×
where it shouldn't (excluding the Phase-3 close historical
anchors deliberately kept in RELEASE_PROOF.md §2 + REPORT.md
§4): F-IR-R2-01 is partially closed → fix-and-reland.

If the CHANGELOG misses any of the 5 IR fix entries:
fix-and-reland.

Acceptable historical anchors in cycle artifacts (not
findings):
- RELEASE_PROOF.md "Phase 3 close empirical" block — `2940
  passed` lines stay for provenance; the post-IR R1 block is
  the ship-time substitute.
- REPORT.md `v0.2.0 Phase-3 close: 2940` row — provenance
  anchor; the ship-time row underneath is the ship surface.

### Q-second-order — did the round-2 fix introduce new defects?

Per AGENTS.md: a round-N fix can introduce a round-N+1 finding.

1. **CHANGELOG entry accuracy.** Each new entry should match
   what actually landed. Spot-check:
   - F-IR-01 entry cites `_ROW_VERSION_COLUMN` registry +
     `state_model_v1.md` §0/§8 + `domains/recovery/policy.py:273`
     emitter — verify on disk.
   - F-IR-05 entry cites `multi_canonical_dates: list[str]`
     field on `WeeklyCoverage` — verify on disk.
   - F-IR-02 entry names 11 errors across 5 files closed
     via `_make_row_getter`, `Sequence[T]`, narrowing locals,
     `# type: ignore[arg-type]`, `assert first is not None` —
     verify each cited fix shape.
   - F-IR-03 entry says "moved both to the f-string lines" —
     verify `core/eval/factuality_gate.py:382` and
     `core/state/snapshot.py:1499` shapes.
   - F-IR-04 entry says round-2 surfaced second-order
     test-count drift from F-IR-04 itself — verify the
     round-2 response file actually carried that finding.
2. **Doc edits introducing typos or broken Markdown.** Spot-
   check the `2.2×` ratio — 187/86 = 2.174…; rounding to
   2.2× is correct. Spot-check the post-IR R1 block in
   RELEASE_PROOF.md renders cleanly (no broken code-fence
   nesting).
3. **No new stale references.** Grep `grep -rn "2940 passed\|2,940
   passed\|+184\b\|2\\.1×" README.md ROADMAP.md CHANGELOG.md
   reporting/docs/current_system_state.md
   reporting/plans/README.md reporting/plans/v0_2_0/RELEASE_PROOF.md
   reporting/plans/v0_2_0/REPORT.md` — should return only the
   Phase-3 close anchors documented above.

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
HAI_RUN_PERSONA_MATRIX=1 uv run python -m verification.dogfood.runner /tmp/v0_2_0_ir_r3_persona_run
```

Round-3 fix was doc-only; gates should match round-2 numbers
exactly:
- pytest broader: 2943 passed, 4 skipped.
- mypy: clean.
- bandit: clean (37 nosec-suppressed).
- factuality eval: 100/100.
- persona matrix: 13/13, 0 findings, 0 crashes.

### Q-honesty-boundary-gates (G15, G16, G17) — unchanged

Re-confirm RELEASE_PROOF wasn't mutated this round to walk
back any claim:
- G15: NO foreign-user empirical claim.
- G16: NO LLM-judge factuality claim.
- G17: NO insight-ledger persistence claim.

### Q-provenance discipline

Spot-verify the round-3 diff's claims (commit messages,
RELEASE_PROOF + REPORT deltas) against on-disk truth.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_2_0/codex_implementation_review_round_3_response.md`:

```markdown
# Codex Implementation Review — v0.2.0 (round 3)

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES | DO_NOT_SHIP
**Round:** 3

## Verification summary
- Round-2 → round-3 delta: 2 commits …
- Test surface: …
- Ship gates: …
- Persona matrix: …
- Round-2 finding closure: F-IR-R2-01 closed | open | partial

## Findings (this round only)

(none expected; if any, follow F-IR-R2-NN naming)

## Round-2 finding disposition

| F-IR-R2 | Closure | Notes |
|---|---|---|
| F-IR-R2-01 | closed / open / partial | … |

## Open questions for maintainer
```

A finding is triageable; a vague concern is not.

---

## Step 4 — Verdict scale

Standard. SHIP / SHIP_WITH_NOTES / SHIP_WITH_FIXES / DO_NOT_SHIP.
Most-likely outcome given round-2 closed cleanly with a doc-only
fix: `SHIP` outright. `SHIP_WITH_NOTES` with a single nit is the
secondary outcome. `SHIP_WITH_FIXES` would mean the round-2 fix
introduced new substantive drift — re-read the round-2 → round-3
diff carefully before issuing this verdict.

---

## Step 5 — Out of scope

- Round-1 + round-2 findings themselves (closure verified, not
  re-litigated).
- Cycle scope (PLAN.md closed at PLAN_COHERENT round 4).
- Strategic-plan / tactical-plan content beyond cycle deltas.
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
Codex IR round 1 ✓ SHIP_WITH_FIXES (5 findings)
Maintainer round-1 response ✓ (6 commits)
Codex IR round 2 ✓ SHIP_WITH_FIXES (1 finding: test-count drift)
Maintainer round-2 response ✓ (2 commits: doc-only freshness
                                + response artifact)
Codex IR round 3 ← you are here
…
Maintainer ship-time manual TTY gate (only after IR settles)
```

---

## Step 7 — Verdict-routing reminder

- `SHIP` → maintainer proceeds to version bump + manual TTY ship gate.
- `SHIP_WITH_NOTES` → maintainer authors a `_response_response.md`
  enumerating disposition (carry-to-v0.2.1 vs accept-as-known)
  and proceeds to ship.
- `SHIP_WITH_FIXES` → maintainer fixes-and-relands, then round 4
  fires (unusual; this would mean round-2 introduced second-order
  drift).
- `DO_NOT_SHIP` → maintainer adjudicates; cycle may abort
  (extremely unlikely at this stage).
