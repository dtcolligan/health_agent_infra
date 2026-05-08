# Codex Implementation Review — v0.1.17 cycle

> **Why this round.** v0.1.17 implementation is complete on `main`
> (26 commits since cycle-open commit `df6a13c`). The D14 pre-cycle
> plan-audit chain settled at `PLAN_COHERENT_WITH_REVISIONS` close-
> in-place at round 3 (halving signature 11 → 5 → 3, thrice-
> validated against AGENTS.md empirical norm). Phase 0 (D11) bug-
> hunt cleared (9 findings, all nit/none). RELEASE_PROOF.md +
> REPORT.md authored. **The branch has not been pushed to PyPI.**
> Per the maintainer's standing instruction, Codex reviews
> implementation against the branch diff before any PyPI publish.
>
> **What you're auditing.** The cycle's *implementation* — that
> the code that landed actually delivers what PLAN.md promised,
> that the ship gates pass, and that no defect is hiding in the
> diff. **Not** the plan itself (D14 already settled that),
> **not** the prior-cycle surface (already shipped to PyPI).
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
git log --oneline main ^main         # N commits, top-down
git status                                   # clean
```

If anything mismatches, stop and surface. Ignore
`/Users/domcolligan/Documents/`.

---

## Step 1 — Read orientation artifacts (in order)

1. **`AGENTS.md`** — operating contract. Note any new D-entries
   this cycle added; confirm the AGENTS.md text matches the CP
   proposal docs verbatim. Read **"Patterns the cycles have
   validated"** — provenance discipline, summary-surface sweep,
   honest partial-closure naming. Apply these as you audit.
2. **`reporting/plans/v0_1_17/PLAN.md`** — cycle contract.
3. **`reporting/plans/v0_1_17/RELEASE_PROOF.md`** — what shipped,
   with named-defers in §5.
4. **`reporting/plans/v0_1_17/REPORT.md`** — narrative summary.
5. **`reporting/plans/v0_1_17/audit_findings.md`** — Phase 0
   findings.
6. **`reporting/plans/v0_1_17/CARRY_OVER.md`** — W-CARRY register.
7. **`reporting/plans/v0_1_17/cycle_proposals/CP{1..N}.md`** —
   governance proposals (if any).
8. **`CHANGELOG.md`** § [0.1.X].

Then open the diff:

```bash
git diff main...main -- src/ verification/ reporting/docs/
git diff main...main -- AGENTS.md ROADMAP.md AUDIT.md \
    CHANGELOG.md pyproject.toml \
    reporting/plans/strategic_plan_v1.md \
    reporting/plans/tactical_plan_v0_1_x.md \
    reporting/plans/success_framework_v1.md
```

---

## Step 2 — Audit questions

This cycle ships 10 W-ids. Walk each PLAN §2.X workstream contract
against the shipped code and call out misses. The cycle was
implemented as one autonomous push (Phase 0 → ship-prep) under
maintainer ratification; bandwidth for second-order issues was
finite. Empirical IR norm is 5 → 2 → 1-nit; the maintainer expects
substantive findings on round 1 and progressively smaller rounds.

### Per-W-id audit questions

- **Q W-29 (cli.py mechanical split).**
  - Inspect the 11 handler-group modules under `src/health_agent_infra/cli/handlers/`.
    Confirm every leaf command relocates to exactly one module
    (PLAN §2.A item 3) and no `cmd_*` lives in `cli/__init__.py`.
  - Verify the `w29_boundary_refresh.md` verdict (`split`) holds:
    every group <2500 LOC at HEAD; `test_cli_handler_group_loc_ceiling.py`
    asserts mechanically.
  - Verify the W-29.2.N commit series did not silently regenerate
    snapshots mid-series (PLAN §2.A item 4: byte-stable manifest at
    every W-29 commit). Snapshot regen is allowed for Phase 2/3
    intentional adds only (W-AI-2 / F-PV14-02 / W-B / W-AM-2).
  - Test-infra question: the maintainer ratified Option B (update
    test sites that monkeypatch cli-private *module attributes* to
    target source modules) at W-29.2.9 mid-implementation. Confirm
    the test edits are surgical (just the affected sites, not a
    broader test refactor).

- **Q W-30 (capabilities-manifest schema regression test).**
  Confirm `test_capabilities_manifest_schema.py` pins field *names*
  + *types* but NOT values (acceptance item 2). The schema-freeze
  itself ships at v0.2.3, not now.

- **Q W-AH-2 (scenario corpus 35 → 135).**
  - Walk the 100 new fixtures across 6 domains + synthesis.
    Are any redundant (exercise a runtime path another fixture
    already covers)? Are any missing a meaningful path?
  - Per-fixture validation discipline: every fixture must fire its
    `expected.policy.forced_action` / `fired_rule_ids` against the
    live runtime (PLAN §2.C item 2; lesson from v0.1.14 W-AM).
    `hai eval run --scenario-set all` returns 135/135 PASS — confirm
    by running.
  - Singular `tag` field (not `tags[]` array); no
    `expected_*_token` field invented (PLAN §2.C item 3 + F-PLAN-02).

- **Q W-AI-2 (`hai eval review` CLI).**
  - 5 subcommands (list/show/tag/dismiss/export) annotated with the
    correct contracts (PLAN §2.D commit-gate item 5).
  - Persistence at `~/.local/share/health_agent_infra/eval_review.json`
    per OQ-2.
  - Snapshot lockstep at the W-AI-2 commit (PLAN §2.D commit-gate
    item 7 / F-PLAN-R2-04).

- **Q W-AM-2 (4 escalate scenarios).**
  Cumulative `w-am-adversarial-escalate` count is 6/6. Each fires
  via the existing scenario-runner contract (no harness extension).

- **Q W-Vb-4 (persona-replay residual).**
  F-PHASE0-07 collapsed this from 5-7d → ~0.5d at Phase 0. Pin is
  `test_w_vb_4_persona_matrix_baseline.py` (opt-in;
  `HAI_RUN_PERSONA_MATRIX=1`). Confirm the test runs cleanly when
  invoked explicitly.

- **Q F-PV14-02 (`hai sync purge`).**
  - 5-row safety cap is enforced (acceptance item 2: 6 rows → refuse).
  - Audit row in `runtime_event_log` carries the deleted-row
    payloads (acceptance item 1).
  - `agent_safe=False` in the manifest.

- **Q W-B (`hai intake weight`).**
  - Migration 026 applies cleanly against an empty DB AND against
    a v0.1.15.1-shaped DB (acceptance item 1).
  - `source` enum is single-valued (`'user_authored'`); `agent_safe=False`
    per F-PLAN-09 round-1 ratification.
  - Multi-measurement-per-day appends rather than replaces (OQ-4).

- **Q W-D arm-2 (partial-day macro projection).**
  - Plumbing path: internal merge inside `build_snapshot()` at
    `core/state/snapshot.py:~895-952`, NOT CLI-handler bodies
    (per F-PLAN-R2-01 round-2 fix).
  - `ClassifiedNutritionState` extends with 4 optional `projected_eod_*`
    fields; `_nutrition_classified_to_dict()` serializes them when
    present, omits otherwise (per F-PLAN-R3-01 round-3 fix).
  - Linear-extrapolation reachable via deep-merged full threshold
    tree with `projection_mode="linear_extrapolation"` (acceptance
    item 5; per F-PLAN-R2-01).
  - protein_sufficiency_band is `"met"` not `"adequate"` (band
    vocab `met|low|very_low|unknown` per `domains/nutrition/classify.py:86`).

- **Q W-C-EQP (EXPLAIN QUERY PLAN stability).**
  Test `test_migration_025_preserves_pre_existing_target_rows_byte_stable`
  extended with EXPLAIN QUERY PLAN check. Asserts one of the
  migration-020 indexes is used (not strictly `idx_target_active_window`
  — the planner picks `idx_target_domain_type` for the IN-filter
  predicate which is the correct selectivity behaviour).

### Cross-cutting

Standard cross-cutting Qs:

- **Q ship-gates.** Re-run the gates the PLAN promised:
  `uv run pytest verification/tests -q`, `uvx mypy
  src/health_agent_infra`, `uvx bandit -ll -r
  src/health_agent_infra`, `hai capabilities --markdown` byte-
  stable, agent_cli_contract.md matches, wheel ships expected
  data files.
- **Q settled-decision integrity.** If the cycle introduces new
  D-entries, AGENTS.md must contain them verbatim from the CP
  doc. If the cycle reverses settled decisions, the strike-text
  must be exact.
- **Q provenance discipline.** Spot-verify on-disk claims (file
  paths, line numbers, function names, exact strings cited in
  PLAN/RELEASE_PROOF). v0.1.12 IR rounds 1+2 caught multiple
  provenance errors — be the independent skeptical pass.
- **Q cross-cutting code quality.** Unused new imports? Lazy
  imports in hot paths? New error paths fail open or fail closed
  correctly?
- **Q absences.** Anything the cycle didn't say it shipped that
  the diff actually changed? Any deferral that should be named
  but isn't?

Cycle-specific questions — add as appropriate per W-id.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_17/codex_implementation_review_response.md`:

```markdown
# Codex Implementation Review — v0.1.17

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES
**Round:** 1 / 2 / 3 / ...

## Verification summary
- Tree state: …
- Test surface: …
- Ship gates: …

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
| ... | ... | ... |

## Open questions for maintainer
```

Each finding triageable. Vague feedback is not a finding; "PLAN
§1.2 W-X catalogue row says 'recovery prototype' but commit SHA
shipped only the flag plumbing per `cli.py:8125`" is.

---

## Step 4 — Verdict scale

- **SHIP** — merge + publish, no further work.
- **SHIP_WITH_NOTES** — merge + publish; named follow-ups carry
  to next cycle. Notes enumerate every non-blocking finding.
- **SHIP_WITH_FIXES** — fix-and-reland. Notes enumerate every
  blocking finding. Round-2 review after maintainer addresses.
- **DO_NOT_SHIP** — only on correctness/security bug warranting
  commit reverts.

For most substantive cycles, `SHIP_WITH_NOTES` with a small
next-cycle follow-up set is the natural shape; `SHIP` outright is
celebrated; `SHIP_WITH_FIXES` means a real bug got past D14 +
Phase 0; `DO_NOT_SHIP` would be very surprising.

---

## Step 5 — Out of scope

- Prior-cycle implementation (already shipped to PyPI).
- D14 plan-audit chain itself (closed at PLAN_COHERENT).
- Strategic-plan / tactical-plan content beyond the deltas this
  cycle applied.
- The named-deferrals themselves — they have destination cycles.
  Findings only about deferrals that should NOT be deferred.
- Next-cycle scope (named in tactical_plan_v0_1_x.md §4).

---

## Step 6 — Cycle pattern

```
D14 plan-audit ✓
Phase 0 (D11) ✓
Pre-implementation gate ✓
Implementation ✓ N commits
Codex implementation review ← you are here
  → SHIP_WITH_FIXES → maintainer + new commits
  → SHIP / SHIP_WITH_NOTES → merge to main
RELEASE_PROOF.md + REPORT.md ✓
PyPI publish (per reference_release_toolchain.md)
```

Estimated: 1-2 sessions per round.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_17/codex_implementation_review_response.md`
  (new) — your findings.
- `reporting/plans/v0_1_17/codex_implementation_review_round_N_response.md`
  (subsequent rounds).

**No code changes.** No source commits. No state mutations.
Maintainer applies fixes; you do not edit source directly.

If you find a correctness/security bug warranting `DO_NOT_SHIP`,
name it explicitly and stop the review for maintainer
adjudication.


---

## Per-cycle close-out

**Round-1 expected verdict:** `SHIP_WITH_NOTES` if findings exist,
or `SHIP` if none. Per AGENTS.md "Audit-chain empirical settling
shape," round 1 typically returns 5-6 findings; round 2 ~2; round
3 either 1-nit close-in-place or `SHIP`.

**Maintainer expects findings on:** the W-29 split correctness
(provenance discipline check), the W-AH-2 fixture quality (any
fixture exercising no novel runtime path?), and the W-D arm-2
classifier-state shape (the 4 new optional dataclass fields +
serializer omit-when-None contract).

**Out-of-scope for this round:** PyPI publish (held until IR
settles), v0.1.18 onboarding cycle scope (open after v0.1.17 ships),
v0.1.19 foreign-user empirical work (renumbered from cancelled
v0.1.16).
