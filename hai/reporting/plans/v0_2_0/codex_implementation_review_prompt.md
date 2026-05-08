# Codex Implementation Review — v0.2.0 cycle (round 1)

> **Why this round.** v0.2.0 implementation is complete on `main`
> (37+ commits since v0.1.18 ship-prep close at HEAD `7c22203`-or-
> earlier — the cycle ran across multiple sessions; Phase 1 +
> Phase 2 + Phase 3 + Phase 5 prep all on `main`, never moved to a
> cycle branch). The D14 pre-cycle plan-audit chain settled at
> `PLAN_COHERENT` in round 4 (10 → 5 → 3 → 1-nit; settling shape
> validated again). Phase 0 (D11) bug-hunt cleared. RELEASE_PROOF
> + REPORT authored. **No version bump yet.** Per the maintainer's
> standing instruction, Codex reviews implementation against the
> diff before any merge or PyPI publish.
>
> **What you're auditing.** The cycle's *implementation* — that
> the code that landed actually delivers what PLAN.md promised
> (11 W-ids), that the ship gates pass, and that no defect is
> hiding in the diff. **Not** the plan itself (D14 already settled
> that), **not** the prior-cycle surface (v0.1.18 already shipped).
>
> **Empirical norm:** 2-3 rounds, settling at the `5 → 2 → 1-nit`
> shape for substantive cycles.
>
> **You are starting fresh.** This prompt and the artifacts it
> cites are everything you need; do not assume context from a
> prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd                                          # /Users/domcolligan/health_agent_infra
git branch --show-current                    # main
git log --oneline 7c22203..HEAD              # the v0.2.0 Phase-3 + Phase-5 commits
git status                                   # clean (untracked planning artifacts ok)
```

If anything mismatches, stop and surface. Ignore
`/Users/domcolligan/Documents/`.

---

## Step 1 — Read orientation artifacts (in order)

1. **`AGENTS.md`** — operating contract. Note any new D-entries
   this cycle added (D16 already shipped post-v0.1.18; v0.2.0 did
   not introduce new D-entries). Read **"Patterns the cycles have
   validated"** — provenance discipline, summary-surface sweep,
   honest partial-closure naming. Apply these as you audit.
2. **`reporting/plans/v0_2_0/PLAN.md`** — cycle contract (11 W-ids).
3. **`reporting/plans/v0_2_0/RELEASE_PROOF.md`** — what shipped,
   with named-defers in §5.
4. **`reporting/plans/v0_2_0/REPORT.md`** — narrative summary.
5. **`reporting/plans/v0_2_0/audit_findings.md`** — Phase 0
   findings.
6. **`reporting/plans/v0_2_0/codex_plan_audit_round_4_response.md`**
   — D14 final round (PLAN_COHERENT).
7. **`CHANGELOG.md`** § [Unreleased] — v0.2.0 in flight.

Then open the diff:

```bash
git diff 7c22203..HEAD -- src/ verification/ reporting/docs/
git diff 7c22203..HEAD -- AGENTS.md ROADMAP.md AUDIT.md \
    CHANGELOG.md pyproject.toml \
    reporting/plans/strategic_plan_v1.md \
    reporting/plans/tactical_plan_v0_1_x.md
```

---

## Step 2 — Audit questions

Per W-id, walking the PLAN promise vs the shipped diff. Note: this
round opens after Phase 5 prep (RELEASE_PROOF + freshness sweep
already authored), so freshness checks are also in scope.

### Q-W52 — `hai review weekly` aggregation surface

PLAN §2.D promised 12 acceptance items. Q for each:
1. Byte-stable JSON output across 3 runs (`test_render_json_byte_stable_across_three_runs`)?
2. Partial-week abstain branch when fewer than coverage_threshold days have plans?
3. D13 threshold-injection-seam validates `policy.review_weekly`?
4. Multi-canonical day handling surfaces both rows (F-PHASE0-07)?
5. Data-quality rollup distinguishes stale_pull / retrospective_manual / fresh / unclassifiable from the existing `sync_run_log.mode` column (no new schema, F-PLAN-04)?
6. Weekly claim-card emission: 1 card per quantitative + comparative atom + qualitative-non-factual mechanical assertion (F-PLAN-10)?
7. W-EXPLAIN-UX-CARRY 6 obligations consumed inline?
8. Deferred-domain suppression: no quantitative or comparative atoms for a deferred domain; literal disposition string pinned in test?
9. `--include-history` flag toggles canonical-latest vs full append-only history view?
10. ≥23 tests grown vs W52 baseline?
11. `hai capabilities --json` exposes `hai review weekly` with all flags?
12. CHANGELOG entry?

Spot-check: `prose_builder.py` deferred-domain disposition reads
"pending the next provenance cycle" (NOT "v0.2.1 W-PROV-3" — the
F-PLAN-10 alignment fix landed in `bfc8722`). The W-FACT-ATOM
parser surfaced 4 alignment holes; verify all 4 are closed
(deferred disposition, goal-abstain shell, goal-abstain "below"
positional, footer conditional count).

### Q-W-FACT-ATOM — atomic-claim parser

PLAN §2.E acceptance items 1-4:
1. ≥98% precision over 30-fixture corpus? **RELEASE_PROOF claims
   100% precision (243/243). Verify by reading
   `verification/tests/test_atomic_claims.py::test_corpus_precision_meets_98_percent_threshold`.**
2. Each atom carries `(atom_text, atom_type, derivation_path)`?
3. Deterministic byte-stable atom output across 3 runs?
4. ≥8 tests grown? (RELEASE_PROOF says 24 tests — verify file count.)

Provenance discipline: parser source at
`src/health_agent_infra/core/eval/atomic_claims.py`; corpus at
`src/health_agent_infra/evals/scenarios/atomic_claims/`.

### Q-W58D — deterministic factuality gate

PLAN §2.F acceptance items 1-8 (round-2 added item 6 + raised item
7 count to ≥26):
1. `core/eval/factuality_gate.py` implements gate logic per the
   PLAN-author proposal? Five lanes: locator-validate, row-version-
   drift, source-signal-conflict (column-value-NULL), audit-ref-
   orphan, x-rule-conflict-user-disagreed. **Verify the
   x-rule-conflict lane requires `user_id` on `ClaimGateInput` —
   without user_id the lane is a no-op (backward-compat path).**
2. Deterministic corpus ≥150 fixtures (≥85 known-bad across 5
   sub-categories + ≥75 known-good)? **RELEASE_PROOF claims 160:
   30 source_quality + 15 x_rule_conflict + 15
   source_signal_conflict + 15 source_row_drift + 10
   audit_ref_orphan = 85 known-bad + 75 known-good. Verify per-
   sub-category by reading `evals/scenarios/factuality/index.json`
   `.categories`.**
3. `hai eval run --scenario-set factuality` reports `block ≥97% /
   pass ≥99%`? **RELEASE_PROOF claims 100/100 — verify by running
   the command.**
4. `hai review weekly` invokes the gate by default; `--bypass-
   factuality-gate` developer-only override; INTERNAL exit on
   blocked atom? **Verify the bypass flag's help text contains
   `"DEVELOPER-ONLY"` and `"agents must not use"`.**
5. Threshold values in `thresholds.toml [policy.factuality_gate]`;
   D13 bool-as-numeric rejection? **Verify by reading
   `core/config.py` for the new dict block + the SCAFFOLD_THRESHOLDS_TOML
   block.**
6. `--scenario-set all` extends to deterministic + factuality
   scoring; `--scenario-set judge_adversarial` stays shape-only?
7. Test count grows ≥26? **RELEASE_PROOF claims +46 — verify file
   count in `test_factuality_gate.py`.**
8. CHANGELOG entry names "deterministic factuality gate"?

### Q-W-PROV-2, W-EVCARD-DAILY, W-EVCARD-WEEKLY (Phases 1+2 closure verification)

These shipped earlier sessions on the same `main` branch. Verify
the per-domain locator emission whitelist still holds; migration
027 + 028 schemas still match RELEASE_PROOF.md descriptions.

### Q-doc-only adjuncts (W-MCP-THREAT, W-COMP-LANDSCAPE, W-NOF1-METHOD)

Confirm each doc exists at the named path with the specified line
count. No code expected.

### Q-W-EXPLAIN-UX-CARRY

`reporting/plans/v0_2_0/explain_ux_obligations.md` disposition
tracker carries 6 entries, all `implemented-in-W52`?

### Q-W-2U-GATE-2

Did NOT fire per RELEASE_PROOF §4. No transcript expected. The
"did not fire" naming is the closure.

### Q-ship-gates

Re-run from a clean tree:

```bash
uv run pytest verification/tests -W error::Warning -q
uv run pytest verification/tests -W error::pytest.PytestUnraisableExceptionWarning -q
uvx mypy src/health_agent_infra
uvx bandit -ll -r src/health_agent_infra
uv run hai capabilities --json | uv run python -c \
    "import json,sys; print(len(json.load(sys.stdin)['commands']))"  # 68
uv run hai eval run --scenario-set all
uv run hai eval run --scenario-set factuality
uv run hai eval run --scenario-set judge_adversarial
HAI_RUN_PERSONA_MATRIX=1 uv run python -m verification.dogfood.runner /tmp/v0_2_0_ir_persona_run
```

RELEASE_PROOF claims:
- Test surface: 2,940 passed, 4 skipped (broader gate)
- Persona matrix: 13/13, 0 findings, 0 crashes
- Scenario sets: 100% across the board

Verify each.

### Q-honesty-boundary-gates (G15, G16, G17)

PLAN §3.3 + RELEASE_PROOF §3 honesty boundaries. Confirm:
- G15: RELEASE_PROOF does NOT claim foreign-user empirical.
- G16: RELEASE_PROOF does NOT claim LLM-judge factuality.
- G17: RELEASE_PROOF does NOT claim insight-ledger persistence.

If any of these claims sneaked in, that's a fix-and-reland.

### Q-provenance discipline

Spot-verify on-disk claims (file paths, line numbers, function
names, exact strings cited in PLAN/RELEASE_PROOF). v0.1.12 IR
rounds 1+2 caught multiple provenance errors — be the
independent skeptical pass.

### Q-cross-cutting code quality

- Unused new imports? Lazy imports in hot paths (the gate's
  scoring runner has lazy imports — verify they don't degrade
  startup)?
- New error paths fail open or fail closed correctly?
- Capabilities-manifest snapshot + parser-tree snapshot +
  agent_cli_contract.md regenerated in lockstep with the new
  CLI surface adds (`--scenario-set factuality`, `hai review
  weekly --bypass-factuality-gate`)?

### Q-summary-surface sweep

The cycle made cross-cutting changes that touch the 8-surface
freshness checklist (AGENTS.md ship-time discipline). Check:
- ROADMAP.md "Now" names v0.2.0 ship-prep complete + v0.2.1
  next-active.
- AUDIT.md has a v0.2.0 entry.
- README.md "Now/Next" reflects v0.2.0.
- `current_system_state.md` reflects v0.2.0 schema head 28, +184
  test delta, +160 factuality fixtures.
- `reporting/plans/README.md` marks v0.2.0 as shipped.
- `reporting/plans/tactical_plan_v0_1_x.md` next-cycle row
  reflects v0.2.1.
- `success_framework_v1.md` and `risks_and_open_questions.md`
  spot-checked.
- CHANGELOG entry under [Unreleased] — v0.2.0 in flight names
  W52, W-FACT-ATOM, W58D + the F-PLAN-10 fix.

Missing one is the canonical IR-round-1-finds-it bug.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_2_0/codex_implementation_review_response.md`:

```markdown
# Codex Implementation Review — v0.2.0 (round 1)

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES | DO_NOT_SHIP
**Round:** 1

## Verification summary
- Tree state: …
- Test surface: …
- Ship gates: …
- Persona matrix: …

## Findings

### F-IR-01. <short title>
**Q-bucket:** ...
**Severity:** correctness-bug | security | scope-mismatch | provenance-gap | acceptance-weak | nit
**Reference:** <commit SHA / file:line> or "absent"
**Argument:** <what + citations>
**Recommended response:** <fix-and-reland | accept-as-known | ...>

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-PROV-2 | ... | ... |
| W-EVCARD-DAILY | ... | ... |
| W-EVCARD-WEEKLY | ... | ... |
| W52 | ... | ... |
| W-FACT-ATOM | ... | ... |
| W58D | ... | ... |
| W-MCP-THREAT | ... | ... |
| W-COMP-LANDSCAPE | ... | ... |
| W-NOF1-METHOD | ... | ... |
| W-EXPLAIN-UX-CARRY | ... | ... |
| W-2U-GATE-2 | did-not-fire | per D16 |

## Open questions for maintainer
```

Each finding triageable. Vague feedback is not a finding; "PLAN
§2.F acceptance #2 says ≥85 known-bad with 5 sub-categories;
`evals/scenarios/factuality/index.json:categories.source_quality`
shows only 25 IDs" is.

---

## Step 4 — Verdict scale

Standard. SHIP / SHIP_WITH_NOTES / SHIP_WITH_FIXES / DO_NOT_SHIP.
Most-likely outcome for v0.2.0 given the corpus + persona-matrix
clean reads is `SHIP_WITH_NOTES` with a small follow-up set; `SHIP`
outright is the celebration outcome.

---

## Step 5 — Out of scope

- Prior-cycle implementation (v0.1.18 already shipped).
- D14 plan-audit chain itself (closed at PLAN_COHERENT round 4).
- Strategic-plan / tactical-plan content beyond the deltas this
  cycle applied.
- The named-deferrals themselves (W-2U-WEARABLE, W-2U-DOGFOOD,
  W58J, W53). Findings only about deferrals that should NOT be
  deferred — e.g., if the bool-as-int W-PROV-1 finding warrants
  in-cycle closure (it doesn't per RELEASE_PROOF §5; argue if
  you disagree).
- Next-cycle scope (v0.2.1 W53 — named in tactical_plan).

---

## Step 6 — Cycle pattern

```
D14 plan-audit ✓ (4 rounds, PLAN_COHERENT)
Phase 0 (D11) ✓
Pre-implementation gate ✓
Implementation ✓ 13 commits this Phase 3 + 5 session (more from
                  Phase 1 + 2 earlier sessions on same `main`)
RELEASE_PROOF + REPORT + freshness sweep ✓
Codex implementation review ← you are here (round 1)
  → SHIP_WITH_FIXES → maintainer + new commits
  → SHIP / SHIP_WITH_NOTES → version bump + manual TTY ship gate
PyPI publish (per reference_release_toolchain.md)
```

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_2_0/codex_implementation_review_response.md`
  (new) — your findings.
- `reporting/plans/v0_2_0/codex_implementation_review_round_N_response.md`
  (subsequent rounds).

**No code changes.** No source commits. No state mutations.
Maintainer applies fixes; you do not edit source directly.

If you find a correctness/security bug warranting `DO_NOT_SHIP`,
name it explicitly and stop the review for maintainer
adjudication.
