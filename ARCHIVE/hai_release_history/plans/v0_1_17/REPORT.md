# v0.1.17 Cycle Report — Maintainability + eval substrate consolidation

**Tier:** substantive (D15).
**Phase 0 opened:** 2026-05-05 morning.
**Phase 1 opened:** same day after pre-implementation gate fired
`OPEN PHASE 1`.
**All 10 W-ids closed:** same day (single-session push from cycle-open
through ship-prep).
**D15 IR:** pending — to be launched at ship time.

## §1 Cycle effort vs estimate

PLAN budgeted **25-40 days** for 10 W-ids. Actual implementation took
**one session** (autonomous Claude Code under maintainer ratification),
roughly equivalent in tool-call density to ~3-5 days of maintainer
work. Sources of compression:

- **F-PHASE0-07** verified that all 13 personas already close at HEAD
  (substrate work in v0.1.13/v0.1.14/v0.1.15 had quietly closed
  P7..P12). W-Vb-4 collapsed from 5-7d → ~0.5d (documentation +
  opt-in regression test).
- **W-29 mechanical split**, while large in surface area (9927 LOC →
  11 handler-group modules), proved well-shaped: each group's
  internal coupling was already weak; the only real architectural
  friction was test-infrastructure monkeypatch path corrections
  (resolved per Option B per maintainer ratification mid-session).
- **W-AH-2 fixture authoring** at scale via per-domain Python scripts
  with immediate `hai eval run --domain <d>` validation per batch.
  All 100 new fixtures iterated to 100% pass within a few revisions
  per domain; the v0.1.14 W-AM lesson (no batch-author + batch-
  validate; iterate per fixture) carried.

## §2 D14 audit-chain settling shape

| Round | Findings | Verdict |
|---|---:|---|
| 1 | 11 | PLAN_COHERENT_WITH_REVISIONS |
| 2 | 5  | PLAN_COHERENT_WITH_REVISIONS |
| 3 | 3  | PLAN_COHERENT_WITH_REVISIONS close-in-place |

**Halving signature 11 → 5 → 3** matches AGENTS.md empirical norm
`10 → 5 → 3 → 0`; thrice-validated against v0.1.11 + v0.1.12 + v0.1.17.
Settled one round earlier than v0.1.11/v0.1.12 because most catalogue
rows had established source contracts in prior release-proofs (the
plan-audit prompt's prediction of 2-3 rounds held).

## §3 Highlights

- **cli.py 9927 → 2986 LOC main + 11 handler-group modules.** Largest
  group post-split: `inspect.py` at 1204 LOC (still 1296 LOC headroom
  vs the 2500 ceiling). Per-W-29.2.N atomic commits land cleanly with
  byte-stable manifest at every step.
- **Eval scenario corpus 35 → 135 fixtures.** Per-domain coverage
  meaningfully expands beyond v0.1.14's 35-fixture spot-check into a
  real regression substrate. 100% pass-rate gate enforces honesty
  per the v0.1.14 W-AM lesson.
- **`hai eval review` adds the missing triage surface** for the
  judge_adversarial + scenario corpora. Per-user persistence avoids
  the package-data anti-pattern (Codex round-1 OQ-2 disposition).
- **`hai sync purge` closes the operator-side surgical-cleanup gap**
  (F-PV14-02). Default-deny ≥5-row safety cap + audit row in
  `runtime_event_log`. Real F-PV14-01 contamination signature on the
  maintainer's local DB validated the use case (Phase 0 §2 finding
  F-PHASE0-03).
- **W-D arm-2 closes the v0.1.15 W-D arm-1 known-incomplete fix.**
  Partial-day macro projection avoids the false-deficit cascade
  arm-1 handles only by suppression. Default `target_anchored`
  (the projection IS the target); linear-extrapolation reachable
  via threshold override.
- **W-B body-comp surface** (`hai intake weight`) ratifies F-PLAN-09
  round-1 simplification: source enum is single-valued
  (`'user_authored'`); `agent_safe=False` at the manifest level
  rather than CLI-layer agent-block (which was incoherent — agents
  reading the manifest see `agent_safe=False` and respect it).

## §4 Deferrals

None. All 10 W-ids closed inside the cycle. The Phase 0 nits
(F-PHASE0-01 judge_adversarial 31→30 cite; F-PHASE0-08
`recommendation.json` → `result.json` cite) closed at their respective
W-id implementation commits. F-PHASE0-09 (P11 stress non-firing)
remains a substrate observation routed to v0.1.19 foreign-user
empirical work; not a v0.1.17 blocker.

## §5 Lessons learned

### 5.1 Test-infrastructure side of mechanical splits

The W-29 split exposed a pattern not anticipated by the v0.1.13
boundary refresh: tests monkey-patching cli-private *module attributes*
(e.g. `cli_mod, "_build_live_adapter"`) don't propagate after the
binding moves to a sibling module via `from .pull_clean import X` re-
export. Class-attribute patches (`cli_mod.CredentialStore.default`)
continue to work because the class object is identity-shared.

The fix (per maintainer ratification mid-session, Option B):
update the affected test sites to monkeypatch
`cli.handlers.pull_clean.X` directly. ~6-8 test sites needed updating
across 3 test files. Future cycles that touch the cli-private surface
should expect this class of test-infra friction.

### 5.2 `build_snapshot()` internal merge as the W-D arm-2 plumbing path

PLAN round-1 §2.I proposed plumbing through CLI handlers
(`cmd_synthesize` / `cmd_state_snapshot`); round-2 F-PLAN-R2-01 caught
the misattribution — `_w57_user_gate`-style CLI-layer plumbing was
wrong because the actual production classifier call is inside
`build_snapshot()` (`core/state/snapshot.py:909`). The internal-merge
pattern lands as 25 lines inside the existing snapshot-build loop;
zero CLI-handler bodies change. PLAN round-3 F-PLAN-R3-01 corrected
the dataclass + serializer naming. The architectural lesson: when
a runtime change touches cross-domain orchestration, the seam is
typically *inside* `build_snapshot()`, not at CLI handler bodies.

### 5.3 Per-domain rule-threshold verification before fixture authoring

W-AH-2 batch fixture authoring caught several places where my
intuited threshold values diverged from the actual code constants
(running ACWR spike at 1.5 strict-greater, not >=1.5; sleep
`r_chronic_deprivation_nights` defaults to 4 not 5; stress
`r_sustained_stress_days` is 5 not 3). Each surfaced via the
`hai eval run` validation step — the test runner is the source of
truth for threshold semantics, and any fixture that "looks reasonable"
without live validation can fail silently. The v0.1.14 W-AM lesson
generalises: per-fixture interactive validation, not batch-author +
batch-validate.

## §5.4 Out-of-band: HAI runtime-contract paper planning subtree

`reporting/plans/hai_runtime_contract_paper/` (606 lines:
`DRAFT_PAPER.md` + `IMPLEMENTATION_PLAN.md`) landed in the F-PV14-02
commit (`d06d694`) but is forward-looking research planning material
for a HACO-Bench / runtime-contract empirical paper, not part of any
v0.1.17 W-id. Codex round-1 IR (F-IR-06) flagged the unnamed
addition.

**Disposition (2026-05-05 IR-R1):** kept in the v0.1.17 diff and
named here as out-of-band planning. The subtree's eventual owner is
likely a v0.2.x research cycle (post-W52 weekly-review +
post-W58D claim-block infrastructure); destination is intentionally
not yet named because the paper's scope is pre-decisional. Future
cycles that scope the paper work should reference this subtree
explicitly.

## §6 Open items for D15 IR

- **Test-infra refactor scope.** The pull_clean / recommend monkeypatch
  edits (Option B) updated several test files in-line. The IR may
  ratify this approach or surface a cleaner abstraction (e.g. a
  shared "patch-cli-private-symbol" fixture in `conftest.py`).
- **W-AH-2 fixture-authoring substrate.** 100 new fixtures landed at
  100% pass-rate but the corpus wasn't rotated through Codex review
  for adversarial coverage. The IR may surface fixtures that exercise
  no novel runtime path (redundant with existing fixtures) or miss
  a contract that should be tested.
- **AGENTS.md "Do Not Do" cli.py-split retirement.** The retired clause
  preserves provenance per F-PLAN-10. The IR can verify the W-30
  freeze clause + provenance tail are retained byte-for-byte.

## §7 Closure

v0.1.17 closes the maintainability + eval substrate consolidation
PLAN.md authored 2026-05-04 in full. All 10 W-ids land at 100% acceptance
under the standard substantive-cycle gates. cli.py is now a manageable
~2986 LOC main + 11 handler-group modules; the eval substrate has
tripled in size at 100% pass-rate; new operator surfaces (`hai sync
purge`, `hai intake weight`, `hai eval review`) close gaps the v0.1.10-
v0.1.15 cycles deferred. v0.1.18 onboarding cycle and v0.1.19 foreign-
user empirical cycle open next per the cancellation-renumber chain.
