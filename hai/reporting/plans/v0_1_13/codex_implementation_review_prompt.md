# Codex Implementation Review — v0.1.13 cycle

> **Why this round.** v0.1.13 implementation is complete on the
> `cycle/v0.1.13` branch (15 commits since `main` — 6 implementation
> commits + 5 D14 plan-audit commits + 1 Phase 0 commit + 2
> cherry-picks from `hotfix/v0.1.12.1` + 1 PLAN-open commit). The
> D14 pre-cycle plan-audit chain settled at `PLAN_COHERENT` in
> round 5 (signature 11 → 7 → 3 → 1-nit → 0; the 1-nit round is a
> mild deviation from the empirical 4-round shape but still inside
> the 2-4 round budget for substantive cycles). Phase 0 (D11)
> bug-hunt cleared with one in-scope finding (F-PHASE0-01,
> absorbed by W-N-broader). **The branch has not been merged or
> pushed.** Per the maintainer's standing instruction, Codex
> reviews implementation against the branch diff before any merge
> or PyPI publish.
>
> **Cycle order deviation worth noting upfront:** v0.1.12 authored
> RELEASE_PROOF.md + REPORT.md before IR opened; v0.1.13 inverts
> that — IR runs first, RELEASE_PROOF + REPORT + CHANGELOG land
> only after this audit closes at SHIP or SHIP_WITH_NOTES. So
> orientation Step 1 below cites PLAN + audit_findings +
> CARRY_OVER + commit messages as the "what shipped" surface;
> RELEASE_PROOF / REPORT / CHANGELOG do not yet exist for this
> cycle. Treat their absence as expected, not a finding.
>
> **What you're auditing.** The cycle's *implementation* — that
> the code that landed actually delivers what PLAN.md promised,
> that the ship gates pass, and that no defect is hiding in the
> diff. **Not** the plan itself (D14 already settled that),
> **not** the v0.1.12 surface (already shipped to PyPI),
> **not** the v0.1.12.1 hotfix (cherry-picked from a separate
> tier-hotfix audit).
>
> **Empirical norm:** 2-3 rounds, settling at the `5 → 2 → 1-nit`
> shape for substantive cycles. v0.1.13 is the largest cycle in
> the v0.1.x track (17 W-ids), so the round-1 finding count may
> exceed the v0.1.12 baseline — the budget is 5-7 substantive
> findings, not the v0.1.12 round-1 figure.
>
> **You are starting fresh.** This prompt and the artifacts it
> cites are everything you need; do not assume context from a
> prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: cycle/v0.1.13
git log --oneline cycle/v0.1.13 ^main
# expect 15 commits, most-recent-first:
#   68d1169 v0.1.13 W-CARRY: disposition pass + acceptance check tick
#   bd11be3 v0.1.13 W-FBC-2: F-B-04 full closure (option A) across 6 domains
#   6ea9ea4 v0.1.13 W-N-broader: close 50 sqlite3 + 1 file-handle + 1 HTTPError leak sites
#   afffb45 v0.1.13 W-Vb: persona-replay end-to-end (P1+P4+P5 ship-set)
#   03fab4f v0.1.13 W-AA: hai init --guided onboarding flow
#   45319da v0.1.13 batch 1: ship 11 of 17 workstreams (small + medium scope)
#   f0ebe65 phase 0 (D11): pre-implementation gate fires green; 1 in-scope finding
#   57460a6 codex D14 r5: PLAN_COHERENT (0 findings) — chain closes formally
#   81aa41f codex D14 r4: 1 nit → fix; chain closes at effective PLAN_COHERENT
#   cbc00da codex D14 r3: 3 findings → revisions; PLAN_COHERENT_WITH_REVISIONS
#   cc3d859 codex D14 r2: 7 findings → revisions; PLAN_COHERENT_WITH_REVISIONS
#   547d355 codex D14 r1: 11 findings → revisions; PLAN_COHERENT_WITH_REVISIONS
#   a10a238 docs(release): v0.1.12.1 lightweight RELEASE_PROOF       (cherry-pick)
#   e5a15d4 docs(plan): open v0.1.13 cycle — public-surface hardening + onboarding
#   636f5d3 fix(pull/intervals_icu): set User-Agent to bypass Cloudflare bot block (cherry-pick)
git status
# expect: clean
```

If any expectation doesn't match, stop and surface the discrepancy.
Ignore any tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts (in this order)

1. **`AGENTS.md`** — operating contract. Pay attention to:
   - "Settled Decisions" D1-D15. **No new D-entry this cycle**;
     verify nothing was added or silently mutated. CP6 (applied
     this cycle) is a strategic-plan §6.3 wording change, NOT a
     new settled decision.
   - "Patterns the cycles have validated" — provenance
     discipline, summary-surface sweep, honest partial-closure
     naming, audit-chain empirical settling shape. Apply these as
     you audit.
2. **`reporting/plans/v0_1_13/PLAN.md`** — the cycle's contract.
   The W-id catalogue is in §1.2 (4 inherited + 7 originally
   planned + 5 added + 1 pre-cycle = 17); per-workstream
   contracts §2.A through §2.C; ship gates §3; risks §4.
3. **`reporting/plans/v0_1_13/audit_findings.md`** — Phase 0
   (D11) probe results. F-PHASE0-01 (W-N-broader baseline -1
   drift) is the only finding.
4. **`reporting/plans/v0_1_13/CARRY_OVER.md`** — W-CARRY register.
   §1 disposes the v0.1.12 RELEASE_PROOF §5 inheritance; §2
   disposes the reconciliation v0.1.13+ items; §3 records the
   originally-planned scope; §6 records Phase 0 absorption; §9
   prepares the summary-surface sweep trace for the upcoming
   RELEASE_PROOF/REPORT step.
5. **No `cycle_proposals/`** dir for v0.1.13 — none authored
   this cycle. CP6 from v0.1.12 was *applied* this cycle (the
   strategic-plan §6.3 verbatim edit) but no new proposals
   landed.
6. **No `RELEASE_PROOF.md` / `REPORT.md` / `CHANGELOG.md` v0.1.13
   entry** — these are authored after IR closes per the
   maintainer's chosen order. Their absence is expected.

Then open the diff:

```bash
git diff main...cycle/v0.1.13 -- src/ verification/ reporting/docs/
git diff main...cycle/v0.1.13 -- AGENTS.md ROADMAP.md AUDIT.md \
    pyproject.toml \
    reporting/plans/strategic_plan_v1.md \
    reporting/plans/tactical_plan_v0_1_x.md \
    reporting/plans/success_framework_v1.md \
    reporting/plans/risks_and_open_questions.md
```

The cycle touches code AND governance docs AND public-facing docs.
All three surfaces are in scope.

---

## Step 2 — Audit questions (per workstream + cross-cutting)

The 17 W-ids cluster into four buckets by audit weight: the four
inherited release-blockers (W-Vb / W-N-broader / W-FBC-2 / CP6
application) get individual Qs, the originally-planned + added
W-ids cluster, and W-CARRY closes. A final cross-cutting block
covers ship gates + provenance + summary-surface sweep.

### Q1. W-FBC-2 — F-B-04 full closure (option A) across 6 domains

Per PLAN §2.A "W-FBC-2 — F-B-04 full closure" + commit `bd11be3`
+ design doc `reporting/docs/supersede_domain_coverage.md`:

- **Option-fork honesty.** PLAN §2.A names three sub-deliverables
  (recovery prototype + multi-domain rollout + per-domain
  fingerprint primitive only if option B selected). Verify the
  shipped diff implements option A only; option B's per-domain
  fingerprint primitive should NOT be present. Check
  `core/synthesis.py` for the absence of a per-domain fingerprint
  function (the global `_compute_state_fingerprint` is the
  v0.1.11 W-E primitive and should remain unchanged in scope).
- **Token shape.** Each domain emits a
  `<domain>_proposal_carryover_under_re_propose_all` token.
  Verify the helper at `core/synthesis.py::_carryover_token_for_domain`
  returns this exact pattern; verify all 6 domains
  (recovery + running + sleep + stress + strength + nutrition)
  produce their own token under the test fixtures. A hardcoded
  recovery branch would be a finding.
- **Freshness threshold.** PLAN says default 1 minute. Verify
  `core/synthesis.py::RE_PROPOSE_ALL_FRESHNESS_THRESHOLD` =
  `timedelta(seconds=60)`. The threshold should be a module
  constant, not buried inline in `run_synthesis`.
- **Phase ordering.** Per the design doc, the carryover token
  lives in the canonical recommendation row's `uncertainty[]`.
  Verify the emission point is AFTER skill_drafts overlay but
  BEFORE Phase B; verify Phase B does not mutate `uncertainty`
  (read `apply_phase_b` in `core/synthesis_policy.py:1335-1362`).
  An emission before skill overlay would be wrong because the
  skill might wipe the token; an emission after Phase B works
  but is fragile to future Phase B scope expansion.
- **Envelope-metadata seam.** The freshness check needs
  `produced_at` from the proposal_log table envelope, NOT from
  `payload_json` (the agent-authored payload doesn't carry
  produced_at by schema). Verify
  `_load_proposal_envelope_authored_at` reads the table columns;
  verify the fallback chain is `produced_at → validated_at`
  (validated_at is non-nullable per schema, so the fallback is
  load-bearing).
- **Defensive default.** When both envelope timestamps are NULL
  (impossible by schema but defensive): the code treats the
  proposal as stale. Verify the comment justifies the defensive
  default (operator passed `--re-propose-all`, runtime has no
  positive evidence of freshness, so honest signal is the
  carryover token).
- **Persona scenarios P1/P5/P9.** Per the design doc + PLAN:
  P1 = morning fresh-state (flag set, no token); P5 = thin-history
  with state delta (recovery stale, only recovery emits token);
  P9 = supersede-after-intake-change (flag absent, no token
  regardless). Verify
  `verification/tests/test_re_propose_all_recovery.py` covers
  these three persona shapes faithfully (NOT just any three
  test cases tagged P1/P5/P9).
- **Multi-domain coverage.** Verify
  `verification/tests/test_re_propose_all_multi_domain.py` is
  parameterised across all 6 domains. The cross-domain
  isolation assertion (token doesn't leak between domains)
  is load-bearing.
- **Rendering layer.** PLAN acceptance: "carryover-uncertainty
  token in `proposal_log` rows AND in rationale prose surfaced
  via `hai today`." Verify
  `verification/tests/test_re_propose_all_rendering.py` covers
  markdown + plain + JSON; verify the negative test (flag
  absent, token absent in render) holds.
- **Help-text update.** `cli.py` `--re-propose-all` parser
  registration. Pre-`bd11be3` text said "no synthesis-side
  runtime effect at v0.1.12... deferred to v0.1.13 W-FBC-2";
  post should say closure is shipped. Verify the wording
  matches the actual runtime semantics (carryover token, not
  hard re-propose).
- **CLI wiring.** `cli.py:_run_daily` calls
  `run_synthesis(..., re_propose_all=re_propose_all_requested)`.
  Verify the arg is plumbed; verify the report-surface field
  `re_propose_all_requested` is preserved (back-compat with
  v0.1.12 partial closure).
- **Capabilities snapshot regen.** The W-29-prep snapshot
  `verification/tests/snapshots/cli_capabilities_v0_1_13.json`
  is intentionally regenerated for the help-text change. Verify
  this is the only post-W-29-prep regeneration on the cycle and
  that the diff is scoped to the `--re-propose-all` flag's help
  field (not other commands).

### Q2. W-Vb — persona-replay end-to-end (partial-closure)

Per PLAN §2.A "W-Vb — Persona-replay end-to-end" + commit
`afffb45` + CARRY_OVER §1:

- **Ship-set honesty.** P1+P4+P5 only; the 9 non-ship-set
  personas (P2/P3/P6/P7/P8/P9/P10/P11/P12) are fork-deferred to
  v0.1.14 W-Vb-3. Verify:
  - `RELEASE_PROOF.md` (when authored) §1 row says
    `partial-closure → v0.1.14 W-Vb-3`.
  - The committed PLAN.md catalogue row + ship-gate row say
    "P1+P4+P5 ship-set", not "all 12 personas".
  - CARRY_OVER §1 W-Vb row carries the destination cycle.
- **Three personas actually reach `synthesized`.** Run the
  test: `uv run pytest verification/tests/test_demo_persona_replay_end_to_end.py -q`.
  Confirm 3 ship-set personas reach `synthesized` state; the
  9 non-ship-set personas should NOT be tested.
- **Clean-wheel subprocess test.** PLAN acceptance names a
  clean-wheel build → install in subprocess → run replay test.
  Verify
  `verification/tests/test_demo_clean_wheel_persona_replay.py`
  exists and exercises the wheel install path; verify the
  test does not leave artifacts in `~/.health_agent`.
- **Isolation contract.** The original `~/.health_agent`
  isolation contract (v0.1.11) must hold. Verify the demo
  fixture-write path uses the demo session's isolated dir,
  not the user's real DB.
- **Apply_fixture flip.** `core/demo/fixtures.py` previously
  returned a deferred-to-v0.1.13 marker. Post-`afffb45`, it
  should write proposals (the proposal-write branch). Verify
  the previous marker semantics didn't survive in dead code.

### Q3. W-N-broader — broader-gate ship target

Per PLAN §2.A "W-N-broader — Resource-warning gate fix" + commit
`6ea9ea4` + audit_findings.md F-PHASE0-01:

- **Surface size honesty.** PLAN named the surface at "49 fail
  + 1 error" (50 sites); audit_findings.md F-PHASE0-01 confirmed
  49 sites at Phase 0 open (-1 drift); commit message says
  "close 50 sqlite3 + 1 file-handle + 1 HTTPError leak sites"
  = 52 sites. Reconcile the count: which is right? Walk the
  actual diff and count per-site fixes.
- **Per-site fix shape.** The PLAN acceptance states: "No new
  `nosec` / `noqa` / `type: ignore` suppressions; the fix is
  structural (close connections in finally / context manager),
  not warning-suppression." Spot-check a sample of 5-10
  per-site fixes and verify they use `try / finally conn.close()`
  or `with` context-managers, NOT a warning filter.
- **Broader-gate green.** Run
  `uv run pytest verification/tests -W error::Warning -q` and
  confirm 0 failures, 0 errors. PLAN promises this is the
  v0.1.13 ship-gate target.
- **Narrow-gate held.** Run
  `uv run pytest verification/tests -W error::pytest.PytestUnraisableExceptionWarning -q`
  to confirm the v0.1.12 narrow gate is still green. The
  broader-gate fix should not have re-broken the narrower
  gate.
- **Per-site table absence.** PLAN acceptance: "Per-site
  resolution table in `RELEASE_PROOF.md` §2.X with one row per
  site." RELEASE_PROOF doesn't exist yet (cycle order
  inversion). Note as expected absence; do not raise as a
  finding.

### Q4. CP6 application — strategic-plan §6.3 verbatim edit

Per PLAN §2.A "CP6 application" + commit `45319da` (in batch 1):

- **Verbatim accuracy.** Read
  `reporting/plans/v0_1_12/cycle_proposals/CP6.md` "Proposed
  delta" section, then read `reporting/plans/strategic_plan_v1.md`
  §6.3 (lines 407-411 per PLAN). The post-cycle text should
  match CP6's proposed-delta text byte-for-byte (modulo
  whitespace).
- **No collateral edit.** The CP6 acceptance gate said the
  v0.1.10-update line at `:413-416` should be preserved
  unchanged. Verify against `git diff main...cycle/v0.1.13 --
  reporting/plans/strategic_plan_v1.md`.

### Q5. W-AA — `hai init --guided` onboarding flow

Per PLAN §2.B "W-AA — First-time-user onboarding flow" + commit
`03fab4f`:

- **Flow correctness.** PLAN §2.B names 7 steps (thresholds,
  state DB migrations, skills copy, intervals.icu credential
  prompt OR skip, initial intent + target rows, `hai pull` for
  initial wellness window, `hai today` with day-1 prose).
  Verify the implementation in
  `src/health_agent_infra/core/init/onboarding.py` (new) walks
  these 7 steps in order; verify each step's failure mode
  surfaces a `USER_INPUT` exit code with actionable next-step
  prose (W-AD interlock).
- **Interrupt-resumable.** PLAN acceptance:
  "KeyboardInterrupt mid-flow does not corrupt state — asserted
  by injecting `KeyboardInterrupt` at each step boundary and
  verifying the partial state is recoverable on next `hai init`
  invocation." Verify
  `verification/tests/test_init_onboarding_flow.py` covers this
  with at least one Interrupt-injection test per step boundary.
- **SLO split honesty.** PLAN §2.B specifies a deterministic
  test gate (the ship-gate) and an operator demo SLO (NOT a
  CI gate, documented in `reporting/docs/onboarding_slo.md`).
  Verify the new SLO doc exists and that it explicitly says
  "manual demo protocol, not a CI gate." A CI test enforcing
  wall-clock <5min would be a finding (over-promised).
- **`--guided` flag.** Commit message names "hai init --guided".
  PLAN says "hai init walks the user through". Verify the flag
  exists; verify a non-`--guided` `hai init` still works (the
  v0.1.12 idempotent-non-interactive path must remain intact
  for tests + agents).

### Q6. Batch-1 cluster (11 workstreams in `45319da`)

Per PLAN §2.B + §2.C + commit `45319da`:

- **Per-workstream presence.** The commit message lists 11
  workstreams: CP6 / W-AB / W-AC / W-AD / W-AE / W-AF / W-AG /
  W-AK / W-LINT / W-A1C7 / W-29-prep. Walk the diff and confirm
  each workstream's named files actually changed. A workstream
  named-but-not-shipped is a finding.
- **W-AB `--human` mode.** PLAN §2.B names
  `core/capabilities/render.py:render_human` (new). Verify
  output is workflow-grouped and human-readable; verify
  `--json` and `--markdown` modes are byte-stable.
- **W-AC README rewrite.** PLAN §2.B names orientation +
  quickstart + troubleshooting structure. Verify the
  troubleshooting block names F-DEMO-01-shape probe-pull
  failures (the W-CF-UA cycle's lesson).
- **W-AD USER_INPUT next-steps.** PLAN §2.B: every USER_INPUT
  exit code carries actionable next-step. Verify
  `verification/tests/test_user_input_messages_actionable.py`
  walks every site; spot-check 3-5 USER_INPUT raises in
  cli.py and confirm prose contains a verb + a likely-next
  command.
- **W-AE `hai doctor --deep`.** PLAN §2.B: 5 outcome classes
  (OK + CAUSE_1_CLOUDFLARE_UA + CAUSE_2_CREDS + NETWORK +
  OTHER), all documented at
  `reporting/docs/intervals_icu_403_triage.md`. Verify the doc
  exists; verify the classification logic actually distinguishes
  the four failure classes (a common bug shape: catching all
  exceptions as `OTHER`).
- **W-AF README quickstart smoke.** Verify
  `verification/tests/test_readme_quickstart_smoke.py` parses
  the `bash quickstart` fenced block and runs it.
- **W-AG `hai today` cold-start prose.** Day-1 vs day-30+
  prose differs in opening sentence + closing prompt. Verify
  the streak metric resolution (uses `hai stats` streak per
  PLAN). A streak threshold of "≥7" (per the renderer doc)
  vs "≥30" (per the PLAN theme) would be a finding.
- **W-AK declarative persona expected_actions.** Per PLAN §2.C:
  "all 12 personas have non-empty `expected_actions`; harness
  asserts." Verify all 12 persona files have
  `expected_actions` declared; verify the runner asserts on
  ALL 12 (not just the 3 ship-set personas from W-Vb).
- **W-LINT regulated-claim lint.** PLAN §2.C specifies the
  4-constraint exception path: allowlisted packaged-skill
  (only `expert-explainer`) + citation + quoted-context +
  CLI-rendering-still-strict. Verify
  `test_regulated_claim_exception_bounded` covers all four
  failure modes (each constraint individually violated +
  the four-all-hold success case). A wholesale loophole would
  be a finding.
- **W-A1C7 trusted-first-value rename + acceptance matrix.**
  Verify `test_acceptance_matrix.py` exists; verify naming is
  consistent across docs/code (grep for old name to confirm
  zero residual references).
- **W-29-prep cli.py boundary audit.** Per PLAN §2.C:
  - `reporting/docs/cli_boundary_table.md` derived live from
    parser, NOT hardcoded subcommand list. Verify the doc is
    derived (the count should match the live parser's
    subcommand count, not a frozen tally).
  - `verification/tests/test_cli_parser_capabilities_regression.py`
    has byte-stability snapshots frozen against
    post-W-AB/W-AE state per F-PLAN-11 sequencing.
  - The capabilities snapshot was legitimately regenerated at
    `bd11be3` for the `--re-propose-all` help-text change
    (W-FBC-2 closure). Verify this is the only post-W-29-prep
    regen on the cycle.

### Q7. W-CARRY — carry-over register honesty

Per PLAN §2.C + commit `68d1169`:

- **Disposition vocabulary.** Every row in
  `reporting/plans/v0_1_13/CARRY_OVER.md` §1, §2, §3 carries a
  terminal disposition (`closed-this-cycle` /
  `partial-closure → v0.1.14 W-Vb-3` /
  `fork-deferred → v0.1.X+1`), NOT the cycle-open `in-cycle`
  placeholder. A residual `in-cycle` row is a finding.
- **Commit citations.** Each `closed-this-cycle` row cites the
  commit SHA. Spot-check 5 rows; if the SHA cited doesn't
  match the actual git history, that's a finding.
- **Acceptance checks.** All 4 checks in CARRY_OVER §"Acceptance
  check (W-CARRY)" are ticked. Verify the prose under each
  ticked box holds (e.g., the "Verified 2026-04-30" claim
  should be supportable by the actual file contents).
- **Summary-surface sweep §9.** The trace is honest: W-Vb is
  the only partial-closure workstream; every other workstream
  closed fully. Verify by reading PLAN §1.2 catalogue + commit
  messages; if any workstream other than W-Vb partial-shipped,
  §9 missed it.

### Q8. Cross-cutting — provenance discipline

Walk the cycle artifacts and spot-verify on-disk claims:

- **PLAN.md file-path / line-number citations.** PLAN §2.A and
  §2.B name specific files for each workstream. Pick 5
  citations at random; confirm the file exists and the named
  function/class is at the cited path.
- **CARRY_OVER §1 commit-SHA citations.** All four §1 rows
  cite a commit SHA. Verify each SHA exists in
  `git log cycle/v0.1.13`.
- **F-PHASE0-01 reproduction.** `audit_findings.md` claims
  Phase 0 saw "48 fail + 1 error" under the broader gate at
  HEAD `57460a6`. Re-run that command at HEAD `57460a6` (or
  trust the W-N-broader fix sequence) — does the count match,
  or has it drifted to a different baseline?
- **D14 chain-close consistency.** PLAN.md status line says
  D14 round 5 closed at PLAN_COHERENT (0 findings). Read
  `codex_plan_audit_round_5_response.md` and confirm the
  verdict is `PLAN_COHERENT` with 0 findings. A
  `PLAN_COHERENT_WITH_REVISIONS` close would be a finding.

### Q9. Cross-cutting — summary-surface sweep

Per AGENTS.md "Summary-surface sweep on partial closure":

- **W-Vb is the only partial.** Confirmed in CARRY_OVER §9.
  Walk every named summary surface and verify the W-Vb
  partial-closure language is consistent:
  - PLAN §1.1 / §1.2 / §1.3 / §2.A / §3 / §4 — all present
    "P1+P4+P5 ship-set" + v0.1.14 W-Vb-3 destination.
  - `tactical_plan_v0_1_x.md` — v0.1.14 row mentions W-Vb-3.
  - `risks_and_open_questions.md` — if it references the
    persona-replay scope, the language matches the partial.
  - **No RELEASE_PROOF / REPORT / CHANGELOG yet** (cycle
    order inversion). Authored after IR closes.

### Q10. Cross-cutting — ship gates

Re-run the full gate set:

```bash
uv run pytest verification/tests -q
# expect: 2486 passed, 3 skipped (or higher; W-FBC-2 added 16)

uv run pytest verification/tests -W error::Warning -q
# expect: 2486 passed, 3 skipped — broader-gate ship target

uvx mypy src/health_agent_infra
# expect: 0 errors, 120 source files

uvx bandit -ll -r src/health_agent_infra
# expect: ≤ 50 Low, 0 Medium, 0 High (D10 threshold)

uvx ruff check src/health_agent_infra
# expect: 178 errors (the v0.1.12 baseline; v0.1.13 W-LINT did
# not commit to a ruff reduction, so static-baseline parity is
# the gate, not a delta)

uv run hai capabilities --json | wc -c
# expect: byte-stable against
# verification/tests/snapshots/cli_capabilities_v0_1_13.json
# (the snapshot regen at bd11be3 is the only legitimate change)

uv run python -m verification.dogfood.runner /tmp/persona_run_ir
# expect: 12 personas, 0 findings, 0 crashes
```

### Q11. Cross-cutting — settled-decision integrity

- **No new D-entry expected.** PLAN says no new D-entries
  this cycle. Verify AGENTS.md "Settled Decisions" section
  has D1-D15 and nothing else added or deleted.
- **CP6 application is wording, not a new D-entry.** Verify
  the §6.3 edit lives in `strategic_plan_v1.md`, not
  AGENTS.md.

### Q12. Cross-cutting — absences

- **Anything the cycle didn't say it shipped that the diff
  actually changed?** Walk the diff for unrelated edits.
- **Any deferral that should be named but isn't?** Particularly
  watch for v0.1.13 RELEASE_PROOF §5 inheritance into v0.1.14;
  CARRY_OVER §4 should already cover this.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_13/codex_implementation_review_response.md`:

```markdown
# Codex Implementation Review — v0.1.13

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES
**Round:** 1

## Verification summary
- Tree state: …
- Test surface: …
- Ship gates: …

## Findings

### F-IR-01. <short title>
**Q-bucket:** Q1 / Q2 / ...
**Severity:** correctness-bug | security | scope-mismatch | provenance-gap | acceptance-weak | nit
**Reference:** <commit SHA / file:line> or "absent"
**Argument:** <what + citations>
**Recommended response:** <fix-and-reland | accept-as-known | revise-artifact | ...>

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-Vb | ... | ... |
| W-N-broader | ... | ... |
| W-FBC-2 | ... | ... |
| CP6 | ... | ... |
| W-AA | ... | ... |
| W-AB | ... | ... |
| W-AC | ... | ... |
| W-AD | ... | ... |
| W-AE | ... | ... |
| W-AF | ... | ... |
| W-AG | ... | ... |
| W-AK | ... | ... |
| W-LINT | ... | ... |
| W-A1C7 | ... | ... |
| W-29-prep | ... | ... |
| W-CARRY | ... | ... |
| W-CF-UA | (catalogue completeness only — not v0.1.13 deliverable) | n/a |

## Open questions for maintainer
```

Each finding triageable. Vague feedback is not a finding; "PLAN
§2.A says option A only but `core/synthesis.py:NNN` ships a
per-domain fingerprint that looks like option B at commit `bd11be3`"
is. Cite file:line + commit SHA wherever possible.

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
next-cycle follow-up set is the natural shape; `SHIP` outright
is celebrated; `SHIP_WITH_FIXES` means a real bug got past D14
+ Phase 0; `DO_NOT_SHIP` would be very surprising.

---

## Step 5 — Out of scope

- Prior-cycle implementation (v0.1.12 already shipped to PyPI;
  v0.1.12.1 hotfix audited at hotfix tier).
- D14 plan-audit chain itself (closed at PLAN_COHERENT round 5).
- Strategic-plan / tactical-plan content beyond the deltas this
  cycle applied (CP6 §6.3 is the only strategic-plan delta).
- The v0.1.14 named-deferrals — they have destination cycles.
  Findings only about deferrals that should NOT be deferred to
  v0.1.14.
- Next-cycle scope (named in `tactical_plan_v0_1_x.md` §4).
- RELEASE_PROOF / REPORT / CHANGELOG content (these don't exist
  yet; their authoring follows IR close per the maintainer's
  chosen order). If you would have raised a finding against
  these, name it as a "next-step constraint for the
  RELEASE_PROOF/REPORT step" rather than a v0.1.13 IR finding.

---

## Step 6 — Cycle pattern

```
D14 plan-audit (5 rounds, 11 → 7 → 3 → 1-nit → 0) ✓
Phase 0 (D11) — 1 in-scope finding (F-PHASE0-01) ✓
Pre-implementation gate ✓
Implementation ✓ 6 implementation commits across 17 W-ids
Codex implementation review ← you are here (round 1)
  → SHIP_WITH_FIXES → maintainer + new commits
  → SHIP / SHIP_WITH_NOTES → RELEASE_PROOF + REPORT + CHANGELOG
RELEASE_PROOF.md + REPORT.md + CHANGELOG.md (post-IR for v0.1.13)
Merge to main
PyPI publish (per reference_release_toolchain.md)
```

Estimated: 1-2 sessions per round; budget 2-3 rounds.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_13/codex_implementation_review_response.md`
  (new) — your round-1 findings.
- `reporting/plans/v0_1_13/codex_implementation_review_round_N_response.md`
  (subsequent rounds, if needed).

**No code changes.** No source commits. No state mutations.
Maintainer applies fixes; you do not edit source directly.

If you find a correctness/security bug warranting `DO_NOT_SHIP`,
name it explicitly and stop the review for maintainer
adjudication.
