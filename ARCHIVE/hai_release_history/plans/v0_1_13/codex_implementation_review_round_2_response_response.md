# Maintainer response — Codex IR round 2 (v0.1.13)

**Round:** 2
**Codex verdict:** SHIP_WITH_FIXES, 2 findings.
**Maintainer disposition:** both findings accepted; both applied
in a single commit. Per AGENTS.md "audit-chain empirical settling
shape", round 2 catching 2 second-order findings (5 → 2) matches
the substantive-cycle norm exactly; both are clean fixes,
neither is correctness-bug-shaped.

**Branch state at response time.** `cycle/v0.1.13` HEAD at IR
round 2 close: `ca0b986` (IR r1 fixes). Round-2 fixes land in a
single commit on top.

**Test surface.** 2493 passed, 3 skipped (held from IR r1
close). No new tests this round — the findings are documentation
+ lint-shape fixes, not behavior changes.

---

## Per-finding response

### F-IR-R2-01 — three F541 f-strings in cli.py (fix-and-reland)

**Disposition:** **fix-and-reland.** Round-1's F-IR-02 fix added
a stderr-prose block for the `partial` branch of `cmd_init`'s
guided-onboarding outcome. Three of the four lines used the `f""`
prefix without any `{}` placeholders — a textbook F541. The
single line that legitimately interpolates `{hint}` (in the
`interrupted` branch) keeps its `f` prefix.

**Applied:** stripped the `f` prefix from the three continuation-
line literals at `cli.py:5447-5449`. The string content is
unchanged; the three previously-implicit no-op f-string evaluations
are gone.

**Why the regression escaped IR r1.** The W-AD interlock fix at
round 1 was added under time pressure as a second-order
adjustment to the F-IR-02 fix; ruff was not re-run after that
specific local edit. Ruff IS one of the round-1 ship gates per
the IR prompt's Q10, so this is a clean miss on my side, not a
hole in the audit contract. The fix is one line of textual
edits.

### F-IR-R2-02 — README count + CARRY_OVER W-AK row drift (fix-and-reland)

**Disposition:** **fix-and-reland.** Both surfaces are stale
relative to the post-IR-r1 state.

**README.** Round 1's F-IR-06 response explicitly deferred the
+7 round-1 delta (2486 → 2493) to "ship-time freshness sweep"
on the rationale that the IR audit was verifying the
post-W-FBC-2 baseline and the round-1 additions were "invisible
at the README level until the next ship." Codex's round 2
correctly pushes back: the IR's authority is current state,
including round-1 fixes, and the README is one of the documented
summary surfaces per AGENTS.md "Patterns the cycles have
validated → Summary-surface sweep on partial closure." Updating
to 2493 now closes the surface drift inside the IR cycle, not
outside it.

**CARRY_OVER §2 W-AK row.** The row described the shipped W-AK
as "auto-derived from runtime's `ALLOWED_ACTIONS_BY_DOMAIN`...
Precondition for v0.1.14 W58 prep now in place." That wording
matched the pre-F-IR-03 state (auto-derive on `base.py`) and
did not reflect the round-1 closure — which moved the
ground-truth shape to inline declarations in every persona file.
A future cycle (or v0.1.14 W58 author) reading this row would
reason from a stale shape.

**Applied:**

1. `README.md` (badge at line 14 + What ships today table at
   line 52): both occurrences updated `2486 → 2493` via
   `replace_all`.
2. `reporting/plans/v0_1_13/CARRY_OVER.md` §2 W-AK row rewritten
   to name the two-stage shipping ("Shipped at `45319da` + revised
   at `ca0b986`"), the round-1 finding's argument (PLAN's
   per-persona contract was satisfied by base-class fallback
   only), the three new public helpers, the 12-persona inline
   declaration set with P8 / P11 specifics, and the new
   inline-declaration text-scan test. The base-class auto-derive
   role is now correctly named as a safety net.

No code change. The artifact provenance trail is what was
incomplete.

---

## Summary-surface sweep — round 2 self-check

Per AGENTS.md "Summary-surface sweep on partial closure" + this
cycle's CARRY_OVER §9: the only partial-closure workstream is
W-Vb (P1+P4+P5 of 12 personas; 9 fork-deferred). Verifying the
named summary surfaces still hold post-IR-r1+r2:

- PLAN.md §1.1 / §1.2 / §1.3 / §2.A / §3 / §4 — language fixed
  at PLAN-author time; not touched by IR fixes.
- CARRY_OVER §1 W-Vb row — unchanged; says
  `partial-closure → v0.1.14 W-Vb-3` with commit citation.
- CARRY_OVER §4 — unchanged; W-Vb-3 fork-deferred to v0.1.14.
- CARRY_OVER §9 — unchanged; trace honest.
- README — round-2 update touches the test count only; no
  W-Vb-related prose change.
- ROADMAP / tactical_plan / risks — not touched by IR rounds;
  v0.1.13 PLAN-author state holds.
- RELEASE_PROOF / REPORT / CHANGELOG — not yet authored
  (cycle order inversion). Scheduled for after IR closes.

No new partial-closure introduced by the round-1 or round-2 fixes.
W-Vb's shape is unchanged.

---

## Round-2 close

Both findings applied. Ship gates verified clean post-fixes:

| Gate | Status |
|---|---|
| Pytest narrow | 2493 passed, 3 skipped (held) |
| Pytest broader (`-W error::Warning`) | 2493 passed, 3 skipped (re-run; held) |
| Mypy | 0 errors / 120 source files (held) |
| Ruff | All checks passed (was the round-2 finding; now closed) |
| Bandit `-ll` | 0 Medium / 0 High (held) |
| Persona matrix | 12 personas / 0 findings / 0 crashes |

**Recommended next step:** Codex IR round 3 against the post-fix
diff. Empirical settling shape per AGENTS.md is `5 → 2 → 1-nit`
across 3 rounds. Round 3 typically catches a single nit (or
closes at SHIP outright). Round 2's findings were both clean
non-correctness shapes (ruff lint + doc drift), which suggests
round 3 is most likely SHIP or SHIP_WITH_NOTES with no further
findings.

If round 3 closes at SHIP / SHIP_WITH_NOTES, RELEASE_PROOF.md +
REPORT.md + CHANGELOG.md follow per the maintainer's chosen
order, with the ship-time freshness sweep against ROADMAP /
AUDIT / README / HYPOTHESES / planning-tree README /
tactical_plan / success_framework / risks per AGENTS.md.
