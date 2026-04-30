# v0.1.13 Cycle Report

**Tier:** substantive (per CP3 D15 four-tier classification).
**Authored 2026-04-30** at cycle close, post-IR-SHIP.

---

## 1. What this cycle was for

v0.1.13 was the largest cycle in the v0.1.x track at 17
workstreams. Three distinct themes ran in parallel:

1. **Close v0.1.12 named-deferred items.** W-Vb persona-replay
   end-to-end (P1+P4+P5 ship-set), W-N-broader 50-site sqlite3
   leak fix, W-FBC-2 multi-domain F-B-04 closure, CP6 §6.3
   strategic-plan edit application.
2. **Make the first-time-user experience credible.** The
   originally-planned v0.1.13 onboarding scope (W-AA through
   W-AG): `hai init --guided`, `hai capabilities --human`,
   README rewrite + smoke test, error-message quality pass,
   `hai doctor` expansion with live-API probe, cold-start prose
   on `hai today`.
3. **Land governance prerequisites for v0.1.14 + v0.2.0.**
   W-29-prep cli.py boundary audit (CP1 prerequisite), W-LINT
   regulated-claim lint, W-AK declarative persona expected-
   actions, W-A1C7 trusted-first-value rename + acceptance
   matrix.

End-state: `pipx install health-agent-infra && hai init --guided`
produces a working setup in under 5 minutes for a recreational
athlete with intervals.icu credentials; every USER_INPUT exit
code carries actionable next-step prose; `hai doctor` flags
every common onboarding gap including F-DEMO-01-shape probe-pull
failures; `hai daily --re-propose-all` enforces the option-A
supersede-all-domains semantics across all six domains with
audit-chain-visible carryover-uncertainty tokens.

## 2. Empirical settling pattern

**D14 plan-audit chain — 5 rounds, 11 → 7 → 3 → 1-nit → 0.**

| Round | v0.1.11 | v0.1.12 | v0.1.13 |
|---|---|---|---|
| 1 | 10 | 10 | 11 |
| 2 | 5 | 5 | 7 |
| 3 | 3 | 3 | 3 |
| 4 | 0 (`PLAN_COHERENT`) | 0 (`PLAN_COHERENT`) | 1-nit (`COHERENT_WITH_REVISIONS`) |
| 5 | — | — | 0 (`PLAN_COHERENT`) |

The 11 → 7 → 3 head matches the v0.1.11/v0.1.12 halving signature
even though scope grew from 10 to 17 W-ids. Round 4 closed at
1-nit rather than 0 because the cycle's scope bloat introduced
one second-order propagation issue across artifacts; round 5
absorbed it cleanly. **The empirical pattern is now thrice-
validated for substantive PLANs**: budget 4-5 rounds rather
than expecting one-shot coherence, and use the head shape
(round 1 ≈ scope-driven; round 2 ≈ half of round 1; round 3 ≈
3) as the stability signal.

**Codex IR chain — 3 rounds, 6 → 2 → 0.**

| Round | v0.1.13 |
|---|---|
| 1 | 6 (SHIP_WITH_FIXES) |
| 2 | 2 (SHIP_WITH_FIXES) |
| 3 | 0 (SHIP) |

Slightly cleaner than the documented `5 → 2 → 1-nit` empirical
norm — round 3 closed outright at SHIP rather than 1-nit. Both
round-2 findings were doc/lint surfaces (no correctness shape),
which is the standard precondition for a clean round-3 close.

## 3. What shipped — highlights

- **F-B-04 closed across all 6 domains** (W-FBC-2). Option A
  default per `reporting/docs/supersede_domain_coverage.md`:
  `hai daily --re-propose-all` now emits a per-domain
  `<domain>_proposal_carryover_under_re_propose_all` token in
  the recommendation's `uncertainty[]` when the proposal envelope
  is older than 60 seconds. The token surfaces in `hai today`
  prose + JSON + `hai explain` rows. Recovery prototype +
  multi-domain rollout shipped in one piece because the runtime
  logic is domain-agnostic via `_carryover_token_for_domain()`.
- **Broader-warning ship-gate restored** (W-N-broader). 50
  sqlite3 connection-lifecycle sites + 1 file-handle + 1
  HTTPError leak closed via structural `try/finally` +
  context-manager fixes (no `nosec`/`noqa`/`type: ignore`
  shortcuts). `pytest -W error::Warning` is now a green ship
  target — a v0.1.12 fork-defer fully repaid.
- **`hai init --guided` onboarding flow** (W-AA). 7-step
  orchestrator that walks a fresh user from `pipx install` to a
  rendered first plan. Each step idempotent; KeyboardInterrupt
  mid-flow surfaces USER_INPUT exit code (post-IR-r1 F-IR-02
  closure). Operator demo SLO target (≤5 min wall-clock)
  documented in `reporting/docs/onboarding_slo.md` per F-PLAN-08
  — target, not CI gate.
- **Persona-replay end-to-end for the P1+P4+P5 ship-set**
  (W-Vb). `apply_fixture()` flipped from boundary-stop to
  proposal-write branch; full DomainProposal seeds for 3
  personas; `hai demo start --persona <slug> && hai daily`
  reaches `synthesized`. The 9 non-ship-set personas honestly
  fork-deferred to v0.1.14 W-Vb-3.
- **Regulated-claim lint** (W-LINT). Static skill scan + runtime
  CLI-rendering check; banned terms (clinical-grade, biomarker,
  diagnose, etc.) blocked from user-facing prose. Four-constraint
  exception path (allowlisted skill + citation + quoted context +
  CLI-rendering-still-strict). Meta-document pragma bounded to
  3-skill allowlist after IR r1 F-IR-04 caught the wholesale
  loophole.
- **Declarative persona expected-actions** (W-AK). 12 packaged
  personas now declare per-domain action whitelists in their own
  file (post-IR-r1 F-IR-03 closure). v0.1.14 W58 prep has the
  ground-truth shape it needs.
- **`hai doctor --deep`** (W-AE). Live intervals.icu probe-pull
  classified into 5 outcome classes (OK / CAUSE_1_CLOUDFLARE_UA
  / CAUSE_2_CREDS / NETWORK / OTHER) per
  `reporting/docs/intervals_icu_403_triage.md`. Closes the
  original F-DEMO-01 detection gap that the W-CF-UA hotfix
  patched at the symptom layer in v0.1.12.1.
- **CP6 §6.3 strategic-plan edit applied.** Verbatim 4-element
  load-bearing-whole framing replaces the 3-sentence
  DSL-as-moat framing per `v0_1_12/cycle_proposals/CP6.md`.

## 4. What's named-deferred

| Item | Defer to | Why |
|---|---|---|
| W-Vb-3 (9 non-ship-set personas) | v0.1.14 W-Vb-3 | partial-closure per F-PLAN-06 — long-term universe is 12 personas; v0.1.13 ships P1+P4+P5; v0.1.14 covers the 9-persona residual (may further partial-close) |
| W-29 cli.py mechanical split | v0.1.14 | per CP1, conditional on W-29-prep verdict |
| L2 W-DOMAIN-SYNC scoped contract test | v0.1.14 | per Codex F-PLAN-09 |
| A12 judge-adversarial fixtures | v0.1.14 | folds into W-AI |
| A2/W-AL calibration scaffold | v0.1.14 | schema/report shape only |
| W-30 capabilities-manifest schema freeze | v0.2.0 | per CP2; after W52/W58 land |
| MCP server plan / read-surface ship | v0.3 / v0.4 / v0.5 | per CP4 staging |
| W52 / W53 / W58 (weekly review + insight ledger + factuality gate) | v0.2.0 | strategic plan Wave 2 |

The cycle's honesty contract is satisfied across all
deferrals — every entry has destination cycle + reason.

## 5. What was learned

### 5.1 Second-order fixes need re-running static gates

IR round 2 caught three F541 ruff errors (F-IR-R2-01) introduced
by the W-AD interlock fix at IR r1. The interlock fix itself was
correct; it was added under the pressure of closing F-IR-02 and
not re-checked against the project's static gates. Round 1's
maintainer response listed ruff as green, but the response file
was authored before the W-AD interlock edit landed.

**Lesson for future cycles:** every local edit, even one that
is "obviously a string literal change", must be followed by a
re-run of the project-level static gate set, not just the
test-suite for the surface being edited. The project's standard
gate set is small enough to re-run cheaply: `pytest -q && uvx
mypy && uvx ruff check && uvx bandit -ll`. AGENTS.md
"Patterns the cycles have validated" should add this to the
provenance-discipline pattern.

### 5.2 PLAN-text contracts beat implementation drift

IR round 1 caught two scope-mismatch findings where the
implementation had silently drifted from the PLAN's contract:

- **F-IR-01 W-AG threshold.** PLAN.md §1.2 + §2.B both said
  "day-30+ established users"; render.py shipped 7-day. The
  PLAN had been reviewed across all 5 D14 rounds at 30; the
  implementation drift was the bug, not the PLAN.
- **F-IR-03 W-AK persona declarations.** PLAN said "each persona
  declares an `expected_actions` dict in its `p<N>_<slug>.py`
  file"; implementation auto-derived in `base.py` with a
  fallback. The runner assertion was real, but the per-persona
  ground-truth shape v0.1.14 W58 needs lived in the fallback,
  not in the persona file.

**Lesson:** when the PLAN says X and the implementation does Y,
the PLAN wins by default. Revising the PLAN to match Y requires
explicit maintainer adjudication, not silent acceptance during
implementation. The IR audit catches this every time —
round 1's job IS to verify PLAN ↔ code consistency.

### 5.3 Wholesale-loophole shapes need bounded exception paths

IR round 1 F-IR-04 caught the `META_DOCUMENT_PRAGMA` design as
a wholesale loophole: any text containing the magic comment
bypassed the static lint, regardless of source skill. PLAN's
risk row had explicitly named "wholesale loophole" as the thing
to prevent, but the initial implementation traded the
four-constraint exception path's narrowness for a separate,
unbounded pragma path.

**Lesson:** when the PLAN's risk row names a failure mode, the
implementation should explicitly cite that risk row in the code
that addresses it, with a test that demonstrates the failure
mode is closed. The fix added `META_DOCUMENT_ALLOWLIST` and a
negative test (`test_meta_document_pragma_bounded_to_allowlist`)
that asserts arbitrary skills with the pragma still scan; the
allowlist is auditable on diff.

### 5.4 Honest partial-closure naming continues to scale

W-Vb shipped 3 of 12 personas as the v0.1.13 ship-set. The
disposition language stayed consistent across all 14
summary-surface sites named in CARRY_OVER §9 (`partial-closure
→ v0.1.14 W-Vb-3` everywhere it appeared). No surface drifted,
no surface implied full closure. Codex IR rounds 1-3 raised no
W-Vb-related findings.

The pattern is now thrice-validated (v0.1.11 W-PRIV.1,
v0.1.12 W-Vb + W-FBC, v0.1.13 W-Vb). Future cycles can rely on
the convention without re-deriving it: residuals carry
destination cycle (`partial-closure → v0.1.X+1 W-X-N`) in
every artifact at ship time.

### 5.5 Cycle-order inversion has documentation cost

v0.1.13 inverted the v0.1.12 convention by running IR before
authoring RELEASE_PROOF / REPORT / CHANGELOG. The inversion
let Codex's findings shape the RELEASE_PROOF directly rather
than forcing artifact re-edits, and the round-2/round-3 cycle
proceeded faster as a result (no RELEASE_PROOF to revise after
each round).

The cost: the IR round-1 prompt had to explicitly note that
RELEASE_PROOF/REPORT/CHANGELOG don't yet exist — a cycle-
specific footnote. Codex r1 raised it via the cycle-order
deviation but did not flag the absence as a finding.

**Lesson:** the inversion is structurally cleaner for
substantive cycles. Worth carrying forward to v0.1.14 by
default, with the IR prompt template updated to reflect the
inverted order as the new baseline.

## 6. Cycle metrics

| Metric | v0.1.12 ship | v0.1.13 ship | Δ |
|---|---|---|---|
| Tests passing | 2384 | 2493 | +109 |
| Pytest broader gate | 49 fail + 1 error (fork-deferred) | 0 / 0 (closed) | -50 |
| Mypy errors | 0 | 0 | held |
| Mypy source files | 116 | 120 | +4 |
| Bandit Low | 46 | 46 | held |
| Bandit Medium/High | 0 / 0 | 0 / 0 | held |
| W-ids in cycle | 10 | 17 | +7 |
| D14 rounds | 4 | 5 | +1 |
| IR rounds | (assumed 2-3 empirical) | 3 | held |
| New CLI subsurfaces | 3 (`auth remove`, `today --verbose`, `daily --re-propose-all` plumbing) | 4 (`init --guided`, `capabilities --human`, `doctor --deep`, `daily --re-propose-all` runtime) | +1 |
| New SQLite migrations | 0 | 0 | held |
| Cycle tier | substantive | substantive | held |

## 7. v0.1.14 inherited backlog

Per CARRY_OVER §4 (v0.1.14+ pass-through fork-defers):

- **W-Vb-3** persona-replay extension to the 9 non-ship-set
  personas (P2/P3/P6/P7/P8/P9/P10/P11/P12).
- **W-29** cli.py mechanical split (gated by W-29-prep verdict;
  parser/capabilities regression test scaffold ships in v0.1.13).
- **L2 W-DOMAIN-SYNC** scoped contract test.
- **A12 judge-adversarial fixtures** (folds into W-AI).
- **A2/W-AL** calibration scaffold (schema/report shape only).

Tactical plan §4 will be updated to reflect this inherited
backlog at the freshness sweep step.

## 8. Branch state

`cycle/v0.1.13` not pushed at IR-chain close (per maintainer
standing instruction). Final ship commit (RELEASE_PROOF + REPORT
+ CHANGELOG + version bump + ship-time freshness sweep) follows
this artifact. After the ship commit lands, the maintainer
pushes to `main` and runs PyPI publish per
`reference_release_toolchain.md` (build → smoke-test wheel →
`twine upload` → bypass-CDN-cache `pipx install`).
