# Codex Implementation Review — v0.1.X cycle

<!--
TEMPLATE — copy to reporting/plans/v0_1_X/codex_implementation_review_prompt.md
and customise the per-cycle sections marked {{TEMPLATE}}. Do not
modify Step 0, Step 3, Step 4, Step 5, Step 6, Step 7 — they are
the stable contract surface across cycles. See
reporting/plans/_templates/README.md for the workflow.
-->

> **Why this round.** v0.1.X implementation is complete on the
> `cycle/v0.1.X` branch ({{TEMPLATE: N commits since main}}). The
> D14 pre-cycle plan-audit chain settled at `PLAN_COHERENT` in
> round {{TEMPLATE: K}}. Phase 0 (D11) bug-hunt cleared.
> RELEASE_PROOF + REPORT authored. **The branch has not been
> merged or pushed.** Per the maintainer's standing instruction,
> Codex reviews implementation against the branch diff before any
> merge or PyPI publish.
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
git branch --show-current                    # cycle/v0.1.X
git log --oneline cycle/v0.1.X ^main         # N commits, top-down
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
2. **`reporting/plans/v0_1_X/PLAN.md`** — cycle contract.
3. **`reporting/plans/v0_1_X/RELEASE_PROOF.md`** — what shipped,
   with named-defers in §5.
4. **`reporting/plans/v0_1_X/REPORT.md`** — narrative summary.
5. **`reporting/plans/v0_1_X/audit_findings.md`** — Phase 0
   findings.
6. **`reporting/plans/v0_1_X/CARRY_OVER.md`** — W-CARRY register.
7. **`reporting/plans/v0_1_X/cycle_proposals/CP{1..N}.md`** —
   governance proposals (if any).
8. **`CHANGELOG.md`** § [0.1.X].

Then open the diff:

```bash
git diff main...cycle/v0.1.X -- src/ verification/ reporting/docs/
git diff main...cycle/v0.1.X -- AGENTS.md ROADMAP.md AUDIT.md \
    CHANGELOG.md pyproject.toml \
    reporting/plans/strategic_plan_v1.md \
    reporting/plans/tactical_plan_v0_1_x.md \
    reporting/plans/success_framework_v1.md
```

---

## Step 2 — Audit questions

{{TEMPLATE: per-WS audit questions. Pattern from v0.1.11 + v0.1.12:
one Q per W-id, walking through the workstream's PLAN promise
versus the shipped code. See
reporting/plans/v0_1_12/codex_implementation_review_prompt.md for
the canonical example.

Standard cross-cutting Qs that recur:

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

Cycle-specific questions — add as appropriate per W-id.}}

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_X/codex_implementation_review_response.md`:

```markdown
# Codex Implementation Review — v0.1.X

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

- `reporting/plans/v0_1_X/codex_implementation_review_response.md`
  (new) — your findings.
- `reporting/plans/v0_1_X/codex_implementation_review_round_N_response.md`
  (subsequent rounds).

**No code changes.** No source commits. No state mutations.
Maintainer applies fixes; you do not edit source directly.

If you find a correctness/security bug warranting `DO_NOT_SHIP`,
name it explicitly and stop the review for maintainer
adjudication.
