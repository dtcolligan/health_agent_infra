# Codex Implementation Review — v0.1.12 cycle

> **Why this round.** v0.1.12 implementation is complete on the
> `cycle/v0.1.12` branch (10 commits since `main`). The D14 pre-cycle
> plan-audit chain settled at `PLAN_COHERENT` in round 4 (matching the
> v0.1.11 empirical 10 → 5 → 3 → 0 halving signature). Phase 0 (D11)
> bug-hunt cleared. RELEASE_PROOF + REPORT authored. **The branch has
> not been merged or pushed.** Per the maintainer's standing
> instruction, Codex reviews implementation against the branch diff
> before any merge or PyPI publish.
>
> **What you're auditing.** The cycle's *implementation* — that the
> code that landed actually delivers what PLAN.md promised, that the
> ship gates pass, and that no defect is hiding in the diff. **Not**
> the plan itself (D14 already settled that), **not** the strategic
> direction (the post-v0.1.11 reconciliation already settled that),
> and **not** the v0.1.11 surface (already shipped to PyPI).
>
> **You are starting fresh.** This prompt and the artifacts it cites
> are everything you need; do not assume context from a prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: cycle/v0.1.12
git log --oneline cycle/v0.1.12 ^main
# expect 10 commits, most-recent-first:
#   ship: v0.1.12 — version bump + CHANGELOG + RELEASE_PROOF + REPORT
#   W-Vb: packaged-fixture loader + p1_dom_baseline skeleton fixture
#   W-N-broader: smoke gate + audit-time fork decision …
#   W-H2: mypy stylistic-class fixes — 22 → 0 errors
#   W-FBC: F-B-04 partial closure — design doc + --re-propose-all flag
#   W-FCC: surface strength_status enum via capabilities + hai today --verbose
#   W-PRIV: hai auth remove subcommand + privacy doc updates
#   W-D13-SYM: route recovery/running/sleep/stress policy thresholds …
#   W-CP + W-AC: cycle proposals (CP1-CP6) + apply CP1-CP5 deltas …
#   v0.1.12 scope: PLAN.md + D14 plan-audit chain (10→5→3→0, …)
git status
# expect: clean
```

If any expectation doesn't match, stop and surface the discrepancy.
Ignore any tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts (in this order)

The cycle is documented top-down. Read these before opening any
diff:

1. **`AGENTS.md`** — operating contract. Pay attention to:
   - "Governance Invariants" — the W57 user-gated commit, the
     three-state audit chain, D12 threshold-coercer discipline,
     D13 trusted seam.
   - "Settled Decisions" D1-D15. **D15 is new this cycle** —
     four-tier cycle-weight classification (origin: v0.1.12 CP3).
     The `W29 / W30 deferred` entry has been replaced by
     `W29 / W30 scheduled` (origin: paired CP1 + CP2).
   - "Do Not Do" — the `cli.py` split / manifest freeze entry was
     reworded paired with CP1 + CP2.
   - "Release Cycle Expectation" gained a "Ship-time freshness
     checklist" subsection (origin: W-AC + reconciliation A8).
2. **`reporting/plans/v0_1_12/PLAN.md`** — the cycle's contract
   document. 870-ish lines. The W-id catalogue is in §1.2; the
   per-workstream contracts are §2.1-§2.10; ship gates §3; risks
   §4; DoD §5; Phase 0 outline §6.
3. **`reporting/plans/v0_1_12/RELEASE_PROOF.md`** — what the cycle
   says it shipped, including the named-defers and fork-decisions.
   §5 explicitly lists every deferral with destination cycle.
4. **`reporting/plans/v0_1_12/REPORT.md`** — narrative summary;
   §6 ("What was learned") names the meta-failures the cycle
   tried to avoid.
5. **`reporting/plans/v0_1_12/audit_findings.md`** — Phase 0 (D11)
   probe results + the W-N audit-time fork decision.
6. **`reporting/plans/v0_1_12/CARRY_OVER.md`** — the W-CARRY
   register. Every v0.1.11 named-defer + every reconciliation §6
   v0.1.12 item has a disposition row.
7. **`reporting/plans/v0_1_12/cycle_proposals/CP1.md`** through
   **`CP6.md`** — the six governance proposals. CP1+CP2 are paired
   (same AGENTS.md bullet); CP3 introduces D15; CP4 extends
   strategic plan §10 Wave 3; CP5 reshapes v0.2.0; CP6 application
   is deferred to v0.1.13 strategic-plan rev.
8. **`CHANGELOG.md` § [0.1.12]** — the user-facing summary.

Then open the diff:

```bash
git diff main...cycle/v0.1.12 -- src/ verification/ reporting/docs/
git diff main...cycle/v0.1.12 -- AGENTS.md ROADMAP.md AUDIT.md \
    CHANGELOG.md pyproject.toml \
    reporting/plans/strategic_plan_v1.md \
    reporting/plans/tactical_plan_v0_1_x.md \
    reporting/plans/success_framework_v1.md
```

The cycle touches code AND governance docs AND public-facing docs.
All three surfaces are in scope.

---

## Step 2 — The audit questions (per workstream + cross-cutting)

### Q1. W-CP — six cycle proposals (CP1-CP6)

Per `reporting/plans/v0_1_12/cycle_proposals/CP{1..6}.md`:

- **Strike-text accuracy.** Each CP that proposes an AGENTS.md or
  strategic-plan edit quotes the *current* text verbatim and names
  a *replacement* verbatim. Verify against the actual files:
  - CP1+CP2 paired bullet replacement at AGENTS.md "Settled
    Decisions" + "Do Not Do" — does the post-cycle AGENTS.md text
    match the CP's proposed delta byte-for-byte (modulo
    whitespace)?
  - CP3 D15 entry — does AGENTS.md now contain the four-tier text
    from CP3 verbatim, including the per-tier audit-weight
    mapping?
  - CP4 — does `strategic_plan_v1.md:444` Wave 3 row contain the
    "Staging within Wave 3" subsection + the security gate
    language verbatim from CP4? Verify the MCP-spec URLs are still
    valid (treat 404s as findings).
  - CP5 — does `strategic_plan_v1.md:436` Wave 2 theme line +
    `tactical_plan_v0_1_x.md §6.1` v0.2.0 row contain the W58D /
    W58J split + `HAI_W58_JUDGE_MODE` flag language verbatim?
  - CP6 — verify the proposal file exists and that its target
    `strategic_plan_v1.md §6.3` text-delta is recorded verbatim;
    crucially, the §6.3 edit should *not* have been applied yet
    (deferred to v0.1.13). Confirm `strategic_plan_v1.md:407-411`
    still reads the v0.1.11 wording.
- **Per-CP acceptance gate compliance.** Each CP names an
  `accepted / accepted-with-revisions / rejected` gate. The
  RELEASE_PROOF table in §2.10 records the round-4 verdicts as
  all `accepted`. Verify the "applied at ship" status matches
  the gate text (CP6 should be authored-but-not-applied).
- **Self-application paradox.** CP3 introduces D15 *and* the cycle
  declares `tier: substantive` under D15 in RELEASE_PROOF. Verify
  the resolution per CP3 §"Self-application paradox" is honoured.

### Q2. W-AC — public-doc freshness sweep + ship-checklist

Per PLAN.md §2.1:

- **Stale instances closed.** `ROADMAP.md:13` no longer says
  "v0.1.8 current"; instead Now/Next reflects v0.1.11 shipped +
  v0.1.12 in flight. Verify the "Next" section's v0.1.13-v0.5+
  chain is consistent with CP4 (MCP staging) + CP5 (single
  substantial v0.2.0).
- **`AUDIT.md`** has new entries for v0.1.10 and v0.1.11 (were
  missing per the PLAN). Verify the round/outcome tables aren't
  fabricated — they should match the corresponding RELEASE_PROOF
  files.
- **`success_framework_v1.md` §3.5**: contains the anti-gaming
  note (reconciliation C9). Verify the wording doesn't accidentally
  weaken the existing target metric.
- **Freshness checklist.** AGENTS.md "Release Cycle Expectation"
  has a new subsection. Verify the listed docs are the right set
  (ROADMAP, AUDIT, README, HYPOTHESES, reporting/plans/README,
  tactical, success_framework, risks).
- **Test:** `verification/tests/test_doc_freshness_assertions.py`
  must catch a *future* "v0.1.X current" string for any X older
  than the package version. Mentally test: if someone forgets to
  update ROADMAP.md at v0.1.13 ship, does this test fail? (Read
  the regex; check the parse logic for v0.1.X.)

### Q3. W-CARRY — carry-over register

Per PLAN.md §2.2:

- **Completeness.** Every line in
  `reporting/plans/v0_1_11/RELEASE_PROOF.md §5` has a row in
  `CARRY_OVER.md §1`. Spot-check by name (W-Vb, W-H2, W-N broader,
  F-A-04, F-A-05, F-B-04, F-C-05, W52/W53/W58).
- **Honesty.** Where the disposition is "partial-closure", verify
  the destination cycle is named (F-B-04 → v0.1.13 W-FBC-2;
  W-Vb → v0.1.13 W-Vb).
- **Reconciliation §6 items.** §2 of the register covers C1, A8,
  C9, F-FS-02, C3, L1, C4 — verify each is in the right scope.

### Q4. W-Vb — packaged-fixture path (partial closure)

Per PLAN.md §2.3 + RELEASE_PROOF §1:

- **Packaging.** `pyproject.toml [tool.setuptools.package-data]`
  includes `demo/fixtures/*.json`. Build a wheel:
  ```bash
  uvx --from build python -m build --wheel --outdir /tmp/v0_1_12_audit_wheel
  uvx wheel unpack /tmp/v0_1_12_audit_wheel/health_agent_infra-0.1.12-py3-none-any.whl -d /tmp/v0_1_12_audit_unpack
  find /tmp/v0_1_12_audit_unpack -name "p1_dom_baseline.json"
  ```
  Confirm the fixture file ships in the wheel under
  `health_agent_infra/demo/fixtures/`.
- **Loader.** `core/demo/fixtures.py` uses `importlib.resources`
  (not a hardcoded path). `load_fixture("p1_dom_baseline")` returns
  the JSON dict; `apply_fixture(fixture, ...)` returns the
  deferred-to-v0.1.13 marker (does NOT actually pre-populate
  proposals — that's v0.1.13 W-Vb).
- **`open_session()` integration.** `core/demo/session.py` calls
  the loader when `--persona` is set; records result on
  `DemoMarker.fixture_application` (new optional field). Verify
  that an unknown persona slug does not crash the demo flow —
  `DemoFixtureError` is caught and recorded as
  `{"applied": false, "scope": "error", ...}` (non-fatal at v0.1.12
  scope per the comment).
- **Marker schema compatibility.** `demo_marker.v1` is unchanged;
  `fixture_application` is parsed via `data.get(...)` so older
  marker JSON still validates. Test:
  `verification/tests/test_demo_session_lifecycle.py` and
  `test_demo_isolation_surfaces.py` should still pass.
- **Persona-replay end-to-end.** Verify it is *not* claimed
  shipped. `RELEASE_PROOF §1` should say "partial-closure" and
  §5 should name v0.1.13 W-Vb as the destination.

### Q5. W-H2 — mypy 22 → 0

Per PLAN.md §2.4:

- **Final state.** `uvx mypy src/health_agent_infra` should return
  0 errors (115+ files checked). Run it and confirm.
- **Per-site review.** The W-H2 commit (`36687b9`) lists 12 files
  changed. Read each fix and verify it's behaviour-preserving:
  - `core/pull/garmin.py:22` — `# type: ignore[import-untyped]` for
    pandas. Acceptable (pandas-stubs is third-party).
  - `core/config.py:35` — `# type: ignore[import-not-found]` for
    platformdirs. Acceptable (third-party stub gap).
  - `core/state/projector.py:1642` — drop redundant annotation on
    `days_touched`. Verify the gym-branch and nutrition-branch
    semantics remain identical.
  - `core/pull/garmin_live.py:605, 617` — explicit
    `dict[str, Any]` annotations. No runtime change.
  - `core/validate.py:204, 214` — `data.get("domain") or ""`
    pattern. **Verify this doesn't change validation semantics**
    — empty string still hits the registry default in both
    `SCHEMA_VERSION_BY_DOMAIN.get` and
    `ALLOWED_ACTIONS_BY_DOMAIN.get`?
  - `core/clean/recovery_prep.py:315` — filter Nones inline before
    sum. Verify the math is unchanged when all components are
    not None (the existing gate guarantees this).
  - `core/synthesis_policy.py:415` — same `or ""` pattern as
    validate.py. Same semantic question.
  - `core/synthesis.py:368-385` — rename `skill_draft` to
    `matched_draft` in the by-id branch to dodge mypy's
    non-Optional inference from the prior `for` loop. **Verify
    no other references to `skill_draft` got missed in the
    rename.**
  - `core/memory/projector.py:57` and `cli.py:2114-2122` — widen
    `dict[str, int]` for the `_memory_counts` "total" key.
    Mechanical.
  - `domains/nutrition/policy.py:179-186` — assert-narrow before
    `round()`. Behaviour-preserving since the `_triggers`
    predicates above already gated on `is not None`.
  - `cli.py:4283-4296` — assert-narrow `val` for the [0, 1]
    range check.
  - `cli.py:374, 251, 4691` — `Literal["ok","partial","failed"]`
    typing on the status param + the call sites. Verify no other
    sync-status pass-through site is using `str` (would be a
    silent regression).
  - `evals/runner.py:354, 668-669` — None-filter for sorted();
    rename per-branch result vars. Verify the score-dispatch
    semantics didn't shift.
- **Beat-the-target margin.** Target was ≤5 errors; achieved 0.
  Did W-H2 silently widen the type-coverage scope (e.g., add
  `# type: ignore` blanket suppressions that hide future
  regressions)? Audit the count of new `# type: ignore` comments
  in the diff vs the count of fixed errors.

### Q6. W-N-broader — fork decision (broader gate deferred)

Per PLAN.md §2.5 (post-fork) + audit_findings.md F-PHASE0-02 +
RELEASE_PROOF §2.2:

- **Audit honesty.** PLAN §2.5 records 49 fail + 1 error under
  `-W error::Warning -q`, all sqlite3 connection-lifecycle leaks.
  Re-run the audit command and confirm the count is still in the
  same neighbourhood (treat ±5 as expected variance):
  ```bash
  uv run pytest verification/tests -W error::Warning -q
  ```
- **Fork rationale.** PLAN §2.5 declares the fork to ">150-branch
  behaviour deliberately" despite count being ≤80, on the grounds
  that 49 connection-lifecycle bugs is multi-day per-site work.
  Is this an honest cycle-budget call or a regression dressed up?
  Specifically: did the fork change behaviour for v0.1.11-shipped
  surfaces, or only for the not-yet-shipped broader gate?
- **Smoke gate ships.** `verification/tests/test_warning_gate_smoke.py`
  exercises one canonical state-DB workflow under
  `simplefilter("error", ResourceWarning)` and is green. Verify
  the smoke test isn't a recursive full-suite invocation (round-3
  F-PLAN-R3-01 caught that pattern).
- **Named-defer recorded.** RELEASE_PROOF §5 lists W-N-broader as
  v0.1.13 destination. Tactical plan §4 has W-N-broader on the
  v0.1.13 row.
- **Narrow-gate-still-green.** Run the v0.1.11 narrow gate against
  the v0.1.12 tree:
  ```bash
  uv run pytest verification/tests \
      -W error::pytest.PytestUnraisableExceptionWarning -q
  ```
  Should pass at the v0.1.11 ship-baseline level (~2374 passed +
  2 skipped). If it regresses, the cycle introduced new
  unraisable-warning sites and the fork is not honest.

### Q7. W-D13-SYM — coercer routing + AST contract test

Per PLAN.md §2.6:

- **Per-domain fix.** Recovery, running, sleep, stress
  `policy.py` files now route every `t["policy"][...]` read
  through `coerce_int / coerce_float` with `name=...` per the
  strength + nutrition pattern. Spot-check each file's `R-rule`
  section to confirm.
- **AST contract test.**
  `verification/tests/test_d13_symmetry_contract.py`:
  - 7 tests (6 domains × 1 contract assertion + 1
    all-domains-present sanity).
  - The `_has_uncoerced_policy_reads` walker correctly
    distinguishes "leaf threshold read" from "sub-dict bind"
    (the `cfg = t["policy"]["nutrition"]` pattern in
    nutrition/policy.py).
  - The walker correctly identifies `coerce_*` calls whether
    the function is imported as `coerce_int` (Name) or
    accessed as `health_agent_infra.core.config.coerce_int`
    (Attribute).
  - **Future-7th-domain detection.** Mentally: if someone adds a
    `domains/sleep_apnea/policy.py` with a raw threshold read,
    does the parameterized test catch it? (The
    `test_all_six_domains_present` asserts the count and
    membership.)

### Q8. W-PRIV — `hai auth remove` subcommand + privacy doc

Per PLAN.md §2.7:

- **Implementation.** `cmd_auth_remove` in `cli.py` calls the
  existing `core/pull/auth.py:171` (`clear_garmin`) and
  `core/pull/auth.py:261` (`clear_intervals_icu`) helpers (verify
  both line numbers — round 2 caught this same provenance error).
- **CLI grammar.** Subcommand under `auth` namespace
  (`hai auth remove --source garmin|intervals-icu|all`), not a
  flag on the parent `auth` parser (round-2 F-PLAN-R2-03 caught
  this).
- **Idempotency.** Removing absent credentials is a no-op (one of
  the 5 W-PRIV tests asserts this).
- **Env-var safety.** Env-supplied creds are NEVER touched by
  `clear_garmin/clear_intervals_icu` (PLAN claim). Verify by
  reading the source — env-vars are read in `load_*` but the
  `clear_*` helpers only delete keyring entries.
- **Privacy doc.** `reporting/docs/privacy.md:59-60` no longer
  claims "no `hai auth --remove` command in v0.1.8"; the new
  paragraph names the v0.1.12 surface. Verify the doc doesn't
  promise more than the implementation delivers.
- **Capabilities.** `hai capabilities --json` includes a row for
  `hai auth remove` with the `--source` flag listed under
  `flags[]` (verified by the integration test added in this
  cycle).

### Q9. W-FCC — `strength_status` enum surface + `hai today --verbose`

Per PLAN.md §2.9:

- **Constant.** `domains/strength/classify.py` defines
  `STRENGTH_STATUS_VALUES: tuple[str, ...]` containing the 5
  values (`progressing, maintaining, undertrained, overreaching,
  unknown`). Verify the constant is exported (importable from
  `health_agent_infra.domains.strength.classify`).
- **Capabilities annotation.** `cli.py`'s `p_today` annotation
  now includes `output_schema.OK.enum_surface.strength_status`
  with the same 5 values. Run `hai capabilities --json` and grep
  for the surface.
- **`--verbose` flag.** `cmd_today` accepts `--verbose` (no
  argument, store_true). When set, prepends a "classified state"
  footer. Verify the footer doesn't fire under `--format json`
  (would break JSON consumers).
- **Contract test.**
  `verification/tests/test_capabilities_strength_status_enum_surface.py`:
  asserts the manifest enum_surface matches the
  `STRENGTH_STATUS_VALUES` tuple, and a separate sanity test
  asserts the constant covers the documented enum. Future
  drift gets caught.
- **Forward-compat.** PLAN claims "live classified-state-of-the-
  day rendering deferred to v0.1.13+". Verify the verbose-mode
  footer doesn't accidentally call `build_snapshot` or any
  heavyweight loader in v0.1.12 — it should be a static enum
  surface only.

### Q10. W-FBC — F-B-04 partial closure

Per PLAN.md §2.8 + Codex F-PLAN-R2-04 + F-PLAN-R3-03:

- **Doc.** `reporting/docs/supersede_domain_coverage.md` exists,
  names option A as the default policy with rationale, names
  options B and C as deferred alternatives. Verify the doc's
  v0.1.12 partial-closure scope is *unconditional* about the
  multi-domain defer (round-3 F-PLAN-R3-03 caught a stale
  conditional).
- **CLI flag.** `hai daily --re-propose-all` accepted; surfaces
  in the daily report JSON as `re_propose_all_requested: bool`;
  capabilities-manifest-listed.
- **Runtime semantic.** PLAN says the v0.1.12 runtime effect is
  scoped to recovery only. Verify the daily-handler doesn't
  silently apply the flag to other domains (would be a scope
  expansion). Specifically: does
  `re_propose_all_requested = bool(getattr(args, "re_propose_all", False))`
  feed any synthesis-side enforcement, or is it purely a
  report-surface field at v0.1.12?
- **Tests.** Three new tests in `test_cli_daily.py` cover flag
  round-trip, default false, and capabilities-row presence.
- **Honest scope.** RELEASE_PROOF §1 + §5 + CARRY_OVER §1 all
  agree F-B-04 is partial-closure with multi-domain → v0.1.13
  W-FBC-2. The cycle theme statement in §1.1 says
  "close-or-honestly-partial-close." Verify this isn't a mask
  for incomplete work.

### Q11. Ship gates (cross-cutting)

Per PLAN.md §3 and RELEASE_PROOF §2:

- **Tests.** Re-run `uv run pytest verification/tests -q`. Expect
  ~2382 passed, 2 skipped. Note any deviation.
- **Mypy.** `uvx mypy src/health_agent_infra` — 0 errors.
- **Bandit.** `uvx bandit -ll -r src/health_agent_infra` —
  0 Medium / 0 High; Low count ≤ 50 (policy threshold).
- **Capabilities byte-stability.** `hai capabilities --markdown`
  produces byte-identical output across two consecutive runs.
- **Capabilities ↔ doc match.** `reporting/docs/agent_cli_contract.md`
  matches `hai capabilities --markdown`. The committed-doc test
  (`test_committed_contract_doc_matches_generated`) should pass.
- **Demo regression.** v0.1.11's `test_demo_isolation_surfaces.py`
  remains green against the v0.1.12 tree (the W-Vb fixture work
  did not break the v0.1.11 isolation contract).

### Q12. Settled-decision integrity (D15 self-application)

CP3 introduces D15 *and* this cycle declares `tier: substantive`
under D15. Mechanically:

1. AGENTS.md must contain D15 verbatim from CP3 by ship-time.
2. RELEASE_PROOF.md must declare `tier: substantive` as the first
   line of the document.
3. Future cycles must pick up the convention.

Verify all three. Also: if the cycle forfeits the substantive-
tier requirement (e.g., by skipping D14 — which we know it didn't,
but as a mental check), the fallback per CP3 was "v0.1.12
RELEASE_PROOF omits the tier line." Confirm this is internally
consistent with the cycle as actually shipped.

### Q13. Provenance discipline (the cycle's named lesson)

Per REPORT §6, the cycle's first named lesson was provenance
discipline — round 1 / round 2 / round 3 of D14 each surfaced
PLAN claims that turned out to be wrong on disk (HYPOTHESES.md
already fixed; `core/credentials.py` doesn't exist; strategic
plan §10 *does* have an MCP row). Be the independent skeptical
pass. **Spot-check at least three of the cycle's on-disk claims**:

- W-PRIV cites `core/pull/auth.py:171` and `:261` for the
  `clear_*` helpers. Verify by line number.
- W-FCC cites `STRENGTH_STATUS_VALUES` as a tuple constant.
  Confirm the type and contents.
- W-Vb cites the wheel-packaging path. Verify the wheel actually
  ships the fixture (per the build instructions in Q4).
- (Optional) Pick one additional citation and verify.

If any of the on-disk citations turn out to be false, that's a
finding equivalent in severity to the round-1/2/3 plan-audit
provenance errors.

### Q14. Cross-cutting code quality

- **Imports.** New imports added in this cycle: any unused?
  Any lazy imports inside hot paths that should be top-level?
  (W-Vb's `core/demo/fixtures` is correctly lazy-imported in
  `open_session`.)
- **Error handling.** New error paths added (DemoFixtureError,
  W-PRIV's idempotent removals): do they fail open or fail
  closed correctly per the runtime contract?
- **Test surface.** +35 tests over v0.1.11. Verify each new test
  file has a clear single-responsibility framing and the
  assertions are not just "did it run" smoke checks.

### Q15. What the cycle doesn't say

Surface the absences:

- The cycle declares `tier: substantive` but the four-tier
  classification was just introduced. Should v0.1.12 itself have
  qualified as substantive given its theme is carry-over closure
  + trust repair? (CP3's substantive criteria: ≥1 release-blocker
  workstream OR ≥3 governance edits OR ≥10 days estimated.
  v0.1.12 hits ≥3 governance edits — correct.)
- The cycle has 4 named-deferrals (W-Vb persona-replay, W-N-
  broader, W-FBC-2, CP6 application). Is v0.1.13's tactical-plan
  row honest about absorbing them? Read
  `tactical_plan_v0_1_x.md §4` and confirm.
- Are there code surfaces touched by W-CP / W-AC that aren't
  mentioned anywhere? Spot-check by reading the full diff for
  the W-CP + W-AC commit.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_12/codex_implementation_review_response.md`
matching the v0.1.11 implementation-review-response convention:

```markdown
# Codex Implementation Review — v0.1.12

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES
**Round:** 1 / 2 / 3 ...

## Verification summary

- Tree state: confirmed cycle/v0.1.12, 10 commits since main,
  working tree clean.
- Test surface: <number> passed / skipped (verified locally).
- Ship gates: <pass/fail per gate>.

## Findings

### F-IR-01. <short title>

**Q-bucket:** Q1-Q15 from prompt
**Severity:** correctness-bug | security | scope-mismatch |
provenance-gap | acceptance-weak | nit
**Reference:** <commit SHA / file:line> or "absent"
**Argument:** <what the issue is, with citations>
**Recommended response:** <fix-and-reland | accept-as-known | ...>

### F-IR-02. ...

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-CP | SHIP | … |
| W-AC | … | … |
| W-CARRY | … | … |
| W-Vb | … (partial) | … |
| W-H2 | … | … |
| W-N-broader | … (fork-deferred) | … |
| W-D13-SYM | … | … |
| W-PRIV | … | … |
| W-FCC | … | … |
| W-FBC | … (partial) | … |

## Open questions for maintainer

(Things you couldn't decide without Dom's input.)
```

Each finding must be triageable. Vague feedback ("the cycle feels
heavy on docs") is not a finding; "W-AC's
test_doc_freshness_assertions.py only catches the 'v0.1.X current'
pattern in ROADMAP.md but the spec implies AUDIT.md and README.md
should also be scanned" is a finding.

---

## Step 4 — Verdict scale

- **SHIP** — merge to main + PyPI publish without further work.
- **SHIP_WITH_NOTES** — merge + publish; named follow-ups carry to
  v0.1.13 backlog. Notes must enumerate every non-blocking
  finding.
- **SHIP_WITH_FIXES** — fix-and-reland. Notes must enumerate every
  blocking finding. Maintainer addresses each, you re-review at
  round 2.
- **DO_NOT_SHIP** — only if a correctness or security bug is
  found that warrants reverting commits.

For v0.1.12, the cycle theme is "carry-over closure + trust
repair." A SHIP_WITH_NOTES outcome with a small set of v0.1.13
follow-ups is the natural shape; SHIP outright is the celebrated
shape; SHIP_WITH_FIXES means a real bug got past D14 + Phase 0.
DO_NOT_SHIP would be very surprising.

---

## Step 5 — Out of scope

- v0.1.11 implementation (already shipped to PyPI 2026-04-28).
- The D14 plan-audit chain itself (closed at PLAN_COHERENT round
  4). Findings about the *plan* belong in next cycle's D14, not
  here.
- Strategic-plan / tactical-plan content beyond the deltas this
  cycle applied (CP4 Wave 3 extension, CP5 Wave 2 + §6 reshape).
- The deferrals themselves — they're named, with destination
  cycles. Findings must be about what's named-deferred but
  shouldn't be (e.g., a hidden surface not mentioned anywhere).
- v0.1.13+ scope (named in tactical_plan_v0_1_x.md §4).

---

## Step 6 — Cycle pattern (this round's place)

```
D14 plan-audit ✓ closed
Phase 0 (D11) bug-hunt ✓ closed
Pre-implementation gate ✓ fired green
Implementation ✓ 10 commits
Codex implementation review ← you are here
  → SHIP_WITH_FIXES loops back to maintainer + new commits
  → SHIP / SHIP_WITH_NOTES → merge to main
RELEASE_PROOF.md + REPORT.md ✓ authored
PyPI publish (per reference_release_toolchain.md)
```

Estimated review duration: 1-2 sessions. The cycle has 10 commits
+ 2-3k lines of changes. The W-CP + W-AC commit is the largest
single surface (cycle-proposal docs + governance edits across
many files).

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_12/codex_implementation_review_response.md`
  (new) — your findings.
- (If round 2+ becomes necessary)
  `reporting/plans/v0_1_12/codex_implementation_review_round_2_response.md`
  + maintainer-response companion files.

**No code changes.** No commits to source. No state mutations.
The maintainer applies any fixes; you do not edit the source
tree directly.

If you find a correctness/security bug serious enough to warrant
DO_NOT_SHIP, name it explicitly and stop the review for
maintainer adjudication before continuing other audits.
