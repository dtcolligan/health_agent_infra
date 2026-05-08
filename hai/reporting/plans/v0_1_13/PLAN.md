# v0.1.13 — Public-surface hardening + onboarding

> **Status.** Authored 2026-04-29 by Claude. **D14 plan-audit chain
> in progress** — round-1 closed `PLAN_COHERENT_WITH_REVISIONS` (11
> findings, all accepted; revisions applied at commit 547d355).
> Round 2 closed `PLAN_COHERENT_WITH_REVISIONS` (7 findings, all
> accepted; revisions applied at commit cc3d859 on 2026-04-30).
> Round 3 closed `PLAN_COHERENT_WITH_REVISIONS` (3 findings, all
> accepted; revisions applied 2026-04-30). The 11 → 7 → 3 sequence
> matches the empirical 10 → 5 → 3 → 0 halving signature; round 4
> is expected to close at PLAN_COHERENT.
>
> **Cycle tier (per CP3 D15 four-tier classification): substantive.**
> Rationale: 17 workstreams (per F-PLAN-01), multi-day per-site
> refactor in W-N-broader (50 sites), governance edits via CP6
> application, new public CLI surfaces (W-AA, W-AB, W-AE), new lint
> surface (W-LINT). Multi-round D14 active; full Phase 0 (D11)
> bug-hunt required after the chain closes.
>
> **Cycle pattern (D11 + D14 active).**
>
> 1. PLAN.md draft (this file).
> 2. Codex plan-audit → revise until `PLAN_COHERENT`. Empirical norm
>    for substantive cycles is 2-4 rounds.
> 3. Phase 0 (D11) pre-PLAN bug-hunt → `audit_findings.md`.
> 4. Pre-implementation gate. `revises-scope` findings may revise
>    PLAN.md (loop back to step 2 if large). `aborts-cycle` findings
>    may end the cycle.
> 5. Implementation rounds with Codex review until verdict is
>    SHIP / SHIP_WITH_NOTES.
> 6. `RELEASE_PROOF.md` + `REPORT.md`.
>
> **Source.**
> - `reporting/plans/tactical_plan_v0_1_x.md` §4 (originally-planned
>   v0.1.13 scope: W-AA through W-AG).
> - `reporting/plans/v0_1_12/RELEASE_PROOF.md` §5 (named-deferred
>   inheritance: W-Vb, W-N-broader, W-FBC-2, CP6 application).
> - `reporting/plans/v0_1_12/CARRY_OVER.md` §3 (reconciliation
>   v0.1.13+ named-defers: A1+C7, A5/W-AK, C2/W-LINT, W-29-prep,
>   CP6 application, W-FBC-2 — the last also overlaps the
>   RELEASE_PROOF §5 inheritance row above and is dispositioned in
>   CARRY_OVER §1 + §2 with cross-reference per F-PLAN-02).
> - 2026-04-29 user session: F-DEMO-01 root-cause investigation
>   produced W-CF-UA (intervals.icu Cloudflare User-Agent block);
>   shipped in v0.1.12.1 hotfix prior to this cycle's open. Recorded
>   here for catalogue completeness.
>
> **Branch:** `cycle/v0.1.13` opened off `main` HEAD on 2026-04-29.
> Two commits cherry-picked from `hotfix/v0.1.12.1` (per F-PLAN-03):
> the W-CF-UA code+test diff (`636f5d3`) and the v0.1.12.1
> lightweight RELEASE_PROOF doc (`a10a238`). Both are present in
> this branch; the version bump + CHANGELOG hotfix entry remain
> on the hotfix branch only.

---

## 1. What this release ships

### 1.1 Theme

**Make the first-time-user experience credible.** v0.1.10 → v0.1.12
hardened the maintainer's daily-driver surface; the new-user
experience has rough edges that the maintainer doesn't hit because
his state is well-formed and his credentials work. v0.1.13 closes
those gaps without changing the runtime contract.

End-state: `pipx install health-agent-infra && hai init` produces a
working setup in under 5 minutes for a recreational athlete with
intervals.icu credentials, AND every USER_INPUT exit code carries
actionable next-step prose, AND `hai doctor` flags every common
onboarding gap (including the F-DEMO-01-shape probe-pull gap).

Three things this cycle is for:

1. **Close v0.1.12 named-deferred items.** W-Vb persona-replay end-
   to-end, W-N-broader 50-site sqlite3 leak fix, W-FBC-2 multi-
   domain F-B-04 closure, CP6 §6.3 strategic-plan edit.
2. **Ship onboarding scope.** W-AA through W-AG — the seven-
   workstream block originally scoped for v0.1.13 in
   `tactical_plan_v0_1_x.md` §4.1.
3. **Land governance prerequisites for v0.1.14 + v0.2.0.** W-29-prep
   (cli.py boundary audit + parser/capabilities regression test
   scaffold), W-LINT (regulated-claim lint), W-AK (declarative
   persona expected-actions).

W-CF-UA (intervals.icu Cloudflare UA fix) shipped pre-cycle in
v0.1.12.1 and is recorded in §1.2 for catalogue completeness; it is
NOT a v0.1.13 deliverable.

### 1.2 Workstream catalogue

#### A. Inherited from v0.1.12 RELEASE_PROOF §5 (named-deferred, hard input)

| W-id | Title | Severity | Files (primary) | Source | Effort |
|---|---|---|---|---|---|
| **W-Vb** | Persona-replay end-to-end for the P1+P4+P5 named ship-set (DomainProposal seeds per persona across all 6 domains; flip `apply_fixture()` to proposal-write branch; wire `hai demo start --persona <slug>` + `hai daily` to reach `synthesized`; clean-wheel build-install-subprocess test). The 9 non-ship-set personas (P2/P3/P6/P7/P8/P9/P10/P11/P12) are fork-deferred to v0.1.14 W-Vb-3 (see §1.3). | demo correctness | `src/health_agent_infra/core/demo/fixtures.py`, `src/health_agent_infra/demo/fixtures/p1_dom_baseline.json` (extend) + `p4_strength_only_cutter.json` + `p5_female_multisport.json` (new), `verification/tests/test_demo_persona_replay_end_to_end.py` (new) | v0.1.12 F-IR-02 | 3-4d |
| **W-N-broader** | `-W error::Warning` gate fix — audit and close the 49 fail + 1 error sqlite3 connection-lifecycle leak surface surfaced by v0.1.12 Phase 0 audit; close conn correctly on every CLI command + helper path; restore broader-gate ship target | correctness | initial search surface (to validate during Phase 0 against the actual `-W error::Warning` failure list): `src/health_agent_infra/core/state/store.py`, `src/health_agent_infra/core/explain/queries.py`, `src/health_agent_infra/core/intent/store.py`, `src/health_agent_infra/core/memory/store.py`, `src/health_agent_infra/core/state/projector.py`, `src/health_agent_infra/core/state/projectors/running_activity.py`, `src/health_agent_infra/core/state/snapshot.py`, `src/health_agent_infra/core/target/store.py`, `src/health_agent_infra/evals/runner.py`, `src/health_agent_infra/cli.py` handlers. Authoritative file list to be derived from a fresh `pytest -W error::Warning` run at Phase 0 open and recorded in `audit_findings.md` before per-site fixes begin. | v0.1.12 fork-defer per F-IR-03 | 4-6d |
| **W-FBC-2** | F-B-04 full closure: (1) recovery prototype synthesis-side `--re-propose-all` enforcement on the recovery domain with `recovery_proposal_carryover_under_re_propose_all` carryover-uncertainty token + persona-style scenario tests P1/P5/P9; (2) multi-domain rollout to all 6 domains; (3) per-domain fingerprint primitive **only if option B is selected at design** (option A is the documented default per `reporting/docs/supersede_domain_coverage.md`; option C is explicitly out-of-v0.1.x-scope per the same doc and is NOT reopened by this cycle) | audit-chain | `src/health_agent_infra/core/synthesis.py`, `src/health_agent_infra/domains/<d>/policy.py` (all 6), `verification/tests/test_re_propose_all_*.py` (new) | v0.1.12 F-IR-01 + F-IR-R2-01 | 3-4d |
| **CP6 application** | `strategic_plan_v1.md §6.3` verbatim edit per `v0_1_12/cycle_proposals/CP6.md` — replace 3-sentence DSL-as-moat framing with 4-element load-bearing-whole framing | governance | `reporting/plans/strategic_plan_v1.md` lines 407-411 | CP6 deferred application | 0.25d |

#### B. Originally planned v0.1.13 scope (tactical plan §4.1)

| W-id | Title | Severity | Files (primary) | Source | Effort |
|---|---|---|---|---|---|
| **W-AA** | First-time-user onboarding flow — `hai init` walks profile + targets + auth | UX (release-blocker for theme) | `src/health_agent_infra/cli.py` init handler, `src/health_agent_infra/core/init/onboarding.py` (new) | tactical §4.1 | 2-3d |
| **W-AB** | `hai capabilities --human` mode (end-user-readable, not agent-manifest) | UX | `src/health_agent_infra/cli.py` capabilities handler, `src/health_agent_infra/core/capabilities/render.py` (new human-mode formatter) | tactical §4.1 | 1d |
| **W-AC** | README rewrite — orientation, quickstart, troubleshooting | trust / docs | `README.md` | tactical §4.1 | 1-2d |
| **W-AD** | Error-message quality pass — every USER_INPUT exit code carries actionable next-step | UX | `src/health_agent_infra/cli.py` error-rendering paths; new `verification/tests/test_user_input_messages_actionable.py` | tactical §4.1 | 1-2d |
| **W-AE** | `hai doctor` expansion — onboarding-readiness check + gap diagnostics + intervals.icu probe-pull live-API check (closes the original F-DEMO-01 gap; the W-CF-UA hotfix patches the symptom, W-AE prevents recurrence detection-wise) | UX / operability | `src/health_agent_infra/core/doctor/checks.py`, `src/health_agent_infra/cli.py` doctor handler, new doctor probe shape | tactical §4.1 + F-DEMO-01 prevention | 1-2d |
| **W-AF** | Public README quickstart smoke test (CI-runnable) | trust / regression | `verification/tests/test_readme_quickstart_smoke.py` (new), `.github/workflows/ci.yml` if CI integration is in scope | tactical §4.1 | 1d |
| **W-AG** | `hai today` cold-start prose — different language for day-1 vs day-30 users (uses streak metric from `hai stats`) | UX | `src/health_agent_infra/cli.py` today handler, `src/health_agent_infra/core/render/today.py` if exists | tactical §4.1 | 1d |

#### C. Added at v0.1.12 ship per CP1 / reconciliation / Codex IR

| W-id | Title | Severity | Files (primary) | Source | Effort |
|---|---|---|---|---|---|
| **W-29-prep** | cli.py boundary audit (boundary-table verification + parser/capabilities regression test scaffold) | governance prerequisite | `verification/tests/test_cli_parser_capabilities_regression.py` (new), `reporting/docs/cli_boundary_table.md` (new) | CP1 | 0.5d |
| **W-LINT** | Regulated-claim lint — block "abnormal HRV", "clinical-grade", "biomarker", "risk score", and similar in user-facing prose surfaces (skill outputs + CLI rendered text) | safety / regulatory | `verification/tests/test_regulated_claim_lint.py` (new), `src/health_agent_infra/core/lint/regulated_claims.py` (new) | Reconciliation C2 | 1-2d |
| **W-AK** | Declarative persona expected-actions (pulled forward from v0.1.14; precondition for v0.1.14 W58 prep) | testing infrastructure | `verification/dogfood/personas/p*.py` add `expected_actions` declarations; harness asserts | Reconciliation A5 | 1d |
| **W-A1C7** | Trusted-first-value rename + acceptance matrix — A1 names the gate language consistently across docs/code; C7 codifies the acceptance matrix as a contract test | governance / trust | `AGENTS.md`, `src/health_agent_infra/core/synthesis.py` if rename touches identifiers, `verification/tests/test_acceptance_matrix.py` (new) | Reconciliation A1+C7 | 1-2d (estimate; may revise post-design) |
| **W-CARRY** | v0.1.13 carry-over register (this cycle's CARRY_OVER.md) | audit-chain | `reporting/plans/v0_1_13/CARRY_OVER.md` (this dir) | convention | 0.5d |

#### D. Pre-cycle ships (catalogue completeness only)

| W-id | Title | Status | Notes |
|---|---|---|---|
| **W-CF-UA** | intervals.icu Cloudflare UA-block fix | **shipped in v0.1.12.1** (hotfix tier per D15) | Branchpoint `v0.1.12` tag; lightweight RELEASE_PROOF at `reporting/plans/v0_1_12_1/RELEASE_PROOF.md`. Cycle/v0.1.13 inherits both the code+test diff (commit 636f5d3) and the RELEASE_PROOF doc (commit a10a238, cherry-picked at D14 round 1 per F-PLAN-03 to make the in-tree provenance citation honest) from `hotfix/v0.1.12.1`. Listed here so the workstream catalogue covers every code change between v0.1.12 ship and v0.1.13 ship. |

**Total scope: 17 workstreams** — 4 inherited, 7 originally planned,
5 added-this-cycle, 1 pre-cycle ship for catalogue completeness.

(Revised at D14 round 1 per F-PLAN-01: W-CARRY is a real workstream
with its own per-WS contract in §2.C, not cycle scaffolding.)

**Approximate effort:** 22.5-32.5 days, single-contributor. **Largest
cycle in the v0.1.x track if it lands as scoped.**

### 1.3 Out of scope (named-deferred to later cycles)

| Item | Defer to | Reason |
|---|---|---|
| **W-Vb-3** persona-replay extension to the 9 non-ship-set personas (P2/P3/P6/P7/P8/P9/P10/P11/P12) | v0.1.14 | fork-deferred per F-PLAN-06 (revised at D14 round 2 per F-PLAN-R2-02). Long-term universe is all 12 personas in the matrix; v0.1.13 W-Vb closes 3 of 12 (P1+P4+P5). v0.1.14 W-Vb-3 may further partial-close (e.g., 3-at-a-time) but the destination cycle owns the full residual |
| W-29 cli.py mechanical split (1 main + 1 shared + 11 handler-group, <2500 each) | v0.1.14 | per CP1, conditional on W-29-prep verdict |
| L2 W-DOMAIN-SYNC scoped contract test | v0.1.14 | per reconciliation L2 + Codex F-PLAN-09 |
| A12 judge-adversarial fixtures | v0.1.14 | folds into W-AI |
| A2/W-AL calibration scaffold | v0.1.14 | schema/report shape only at v0.1.14; correlation work to v0.5+ |
| W-30 capabilities-manifest schema freeze | v0.2.0 | per CP2; after W52/W58 schema additions land |
| MCP server plan (read-surface design + threat-model + provenance prereqs) | v0.3 | per CP4 |
| MCP read-surface ship | v0.4 or v0.5 | per CP4; gated by prereqs |
| W52 / W53 / W58 (weekly review + insight ledger + factuality gate) | v0.2.0 | strategic plan Wave 2 |

### 1.4 Cross-cutting concerns

**v0.1.12 patterns (AGENTS.md "Patterns the cycles have validated") apply throughout:**

- **Provenance discipline:** every file:line citation in this PLAN
  + downstream artifacts must be verified on disk before claim.
- **Summary-surface sweep on partial closure:** if any v0.1.13
  workstream ships partial, all 14 sites in AGENTS.md "Summary-
  surface sweep" must move in lockstep at ship time.
- **Honest partial-closure naming:** residuals carry destination
  cycle (`partial-closure → v0.1.14 W-X-2` or
  `fork-deferred → v0.1.14 W-X`).
- **Audit-chain empirical settling shape:** budget 2-4 D14 rounds
  + 2-3 IR rounds. If round N has more findings than round N-1,
  re-read your own diff before Codex's.

---

## 2. Per-workstream contracts

### 2.A — Inherited W-ids (full contracts)

#### W-Vb — Persona-replay end-to-end

**Inherited from v0.1.12 partial-closure (F-IR-02).** v0.1.12 shipped
the packaged-fixture path + skeleton-loader + `apply_fixture()`
that returns a deferred-to-v0.1.13 marker on DemoMarker. v0.1.13
flips `apply_fixture()` to the proposal-write branch and ships the
end-to-end persona-replay so `hai demo start --persona <slug>` + `hai
daily` reaches `synthesized` (not `proposal_log_empty`).

**Files:**

- `src/health_agent_infra/core/demo/fixtures.py` — flip
  `apply_fixture()` from boundary-stop to proposal-write branch.
- `src/health_agent_infra/demo/fixtures/p1_dom_baseline.json`
  (extend; currently a skeleton),
  `src/health_agent_infra/demo/fixtures/p4_strength_only_cutter.json`
  (new),
  `src/health_agent_infra/demo/fixtures/p5_female_multisport.json`
  (new) — author full DomainProposal seeds across all 6 domains per
  packaged persona. Single-JSON-per-persona shape preserved (no
  loader / package-data migration); the existing loader contract
  at `src/health_agent_infra/core/demo/fixtures.py` resolves
  `health_agent_infra/demo/fixtures/<slug>.json` via
  `importlib.resources`. **Ship set is P1+P4+P5** (concrete slugs
  per the persona registry); the 9 non-ship-set personas
  (P2/P3/P6/P7/P8/P9/P10/P11/P12) are fork-deferred to v0.1.14
  W-Vb-3 per §1.3 + F-PLAN-06 + F-PLAN-R2-02.
- `verification/tests/test_demo_persona_replay_end_to_end.py` (new)
  — assert `hai demo start --persona <slug> && hai daily` reaches
  `synthesized` state with a non-empty `proposal_log` and a
  committed `daily_plan` for **each** of the three ship-set
  personas.
- `verification/tests/test_demo_clean_wheel_persona_replay.py` (new)
  — clean-wheel build → install in subprocess → run replay; asserts
  `importlib.resources` fixture path resolves and demo session
  reaches synthesis without `~/.health_agent` mutation.

**Tests:** 8-12 new test cases. Existing `test_demo_*` 25 cases must
all pass unchanged.

**Acceptance (revised at D14 round 1 per F-PLAN-06):**

- `hai demo start --persona p1_dom_baseline && hai daily` produces a
  `synthesized` daily plan.
- `hai demo start --persona p4_strength_only_cutter && hai daily`
  produces a `synthesized` daily plan.
- `hai demo start --persona p5_female_multisport && hai daily`
  produces a `synthesized` daily plan.
- All three ship-set personas asserted via `hai today` rendering
  text + `hai explain` audit-chain shape.
- Clean-wheel subprocess test passes for at least P1 (no editable-
  install dependencies leak into the test path).
- Original `~/.health_agent` tree byte-identical before/after demo
  session per existing isolation-contract tests.
- The 9 non-ship-set personas (P2/P3/P6/P7/P8/P9/P10/P11/P12) NOT
  covered by v0.1.13 acceptance; recorded as fork-defer in PLAN
  §1.3 + CARRY_OVER §4 with destination cycle `v0.1.14 W-Vb-3`.

#### W-N-broader — Resource-warning gate fix

**Inherited from v0.1.12 fork-defer (F-IR-03).** v0.1.12 Phase 0
audit returned 49 fail + 1 error under `pytest -W error::Warning`.
v0.1.13 audits each site, closes the connection-lifecycle bug at the
helper path, and restores the broader-gate ship target.

**Files (initial search surface; authoritative list derived from a
fresh `pytest -W error::Warning` run at Phase 0 open and recorded in
`audit_findings.md` before per-site fixes begin — per F-PLAN-04
provenance correction):**

- `src/health_agent_infra/core/state/store.py` (primary connection-
  helper site)
- `src/health_agent_infra/core/explain/queries.py`
- `src/health_agent_infra/core/intent/store.py`
- `src/health_agent_infra/core/memory/store.py`
- `src/health_agent_infra/core/state/projector.py`
- `src/health_agent_infra/core/state/projectors/running_activity.py`
- `src/health_agent_infra/core/state/snapshot.py`
- `src/health_agent_infra/core/target/store.py`
- `src/health_agent_infra/evals/runner.py`
- `src/health_agent_infra/cli.py` per-handler connection lifecycle

**Tests:** Restore the broader-gate as the v0.1.13 ship-gate target:

```bash
uv run pytest verification/tests -W error::Warning -q
```

Must pass clean. The narrow gate
(`-W error::pytest.PytestUnraisableExceptionWarning`) remains green
unchanged.

**Acceptance:**

- Broader-gate ship-target green: 0 ResourceWarnings, 0
  PytestUnraisableExceptionWarnings, 0 sqlite3-connection-leak
  warnings under `-W error::Warning`.
- Per-site resolution table in `RELEASE_PROOF.md` §2.X with one row
  per site.
- No new `nosec` / `noqa` / `type: ignore` suppressions; the fix is
  structural (close connections in finally / context manager), not
  warning-suppression.

#### W-FBC-2 — F-B-04 full closure

**Inherited from v0.1.12 partial-closure (F-IR-01 + F-IR-R2-01).**
v0.1.12 shipped the design doc + `--re-propose-all` flag (CLI parser
+ capabilities + report-surface only). v0.1.13 ships the synthesis-
side runtime enforcement on all 6 domains.

**Three sub-deliverables:**

1. **Recovery prototype.** Synthesis-side `--re-propose-all`
   enforcement on the recovery domain with the
   `recovery_proposal_carryover_under_re_propose_all` carryover-
   uncertainty token. Persona-style scenario tests P1/P5/P9.
2. **Multi-domain rollout.** Same enforcement applied to running,
   sleep, stress, strength, nutrition.
3. **Per-domain fingerprint primitive** — **option A is the
   documented default** per `reporting/docs/supersede_domain_coverage.md`
   (supersede means all domains re-propose, no per-domain
   fingerprint required). Option B (per-domain fingerprints) is
   the only design fork available; ship it ONLY if explicitly
   selected at W-FBC-2 design phase. **Option C is explicitly
   out-of-v0.1.x scope** per the same design doc and is not
   reopened by v0.1.13 (revised at D14 round 1 per F-PLAN-07).

**Files:**

- `src/health_agent_infra/core/synthesis.py` — `--re-propose-all`
  synthesis-side branch.
- `src/health_agent_infra/domains/<d>/policy.py` (all 6) —
  carryover-uncertainty token emission.
- `verification/tests/test_re_propose_all_recovery_*.py`,
  `..._running_*.py`, etc. (new, ~6 files)

**Acceptance:**

- `hai daily --re-propose-all` produces re-proposed daily-plan rows
  across all 6 domains under verifiable test fixtures.
- Persona scenarios P1/P5/P9 demonstrate carryover-uncertainty token
  in `proposal_log` rows and rationale prose.
- Audit-chain integrity preserved (no skipped versions).

#### CP6 application — strategic plan §6.3 edit

**Mechanical:** replace lines 407-411 of
`reporting/plans/strategic_plan_v1.md` with the verbatim text in
`reporting/plans/v0_1_12/cycle_proposals/CP6.md` "Proposed delta"
section.

**Acceptance:** `git diff strategic_plan_v1.md` shows exactly the
4-element load-bearing-whole framing per CP6 verbatim. v0.1.10
update line at `:413-416` preserved unchanged per CP6 acceptance
gate.

### 2.B — Originally planned W-ids (contracts)

#### W-AA — First-time-user onboarding flow

`hai init` walks the user through:

1. Confirm + scaffold thresholds.toml.
2. Apply state DB migrations.
3. Copy skills.
4. Prompt for intervals.icu credentials (or skip).
5. Author initial `hai intent` + `hai target` rows for the user's
   training plan.
6. Run `hai pull` to fetch initial wellness window.
7. Surface `hai today` with day-1 prose (W-AG dependency).

**Files:** `src/health_agent_infra/cli.py` init handler (extend
existing init), new `src/health_agent_infra/core/init/onboarding.py`
for the prompt flow + state-write sequencing.

**Acceptance (revised at D14 round 1 per F-PLAN-08 — SLO split into
deterministic test gate + operator demo SLO):**

*Deterministic test gate (this is the ship-gate):*

- `verification/tests/test_init_onboarding_flow.py` (new) walks the
  prompt sequence with stubbed input AND a stubbed intervals.icu
  fixture (replay-client shape, same as the existing
  `ReplayWellnessClient`). Asserts the flow reaches a `synthesized`
  daily plan in a single test invocation.
- Each step is interrupt-resumable (KeyboardInterrupt mid-flow does
  not corrupt state) — asserted by injecting `KeyboardInterrupt` at
  each step boundary and verifying the partial state is recoverable
  on next `hai init` invocation.

*Operator demo SLO (target, not ship-gate):*

- New user on broadband (≥10 Mbps), modern macOS / Linux, with
  intervals.icu credentials at hand: `pipx install
  health-agent-infra && hai init` reaches a `synthesized` daily
  plan in under 5 minutes elapsed wall-clock.
- If intervals.icu pull is slow (e.g., the documented Cloudflare-
  rate-limit-window failure mode), the flow surfaces a "still
  pulling — your watch may not have synced today's data yet" UX
  message. **This is an allowed degraded state**, not an SLO
  failure; the user can re-run `hai today` once the pull completes.
- This SLO is documented in `reporting/docs/onboarding_slo.md`
  (new) for operator reference; its measurement is a manual demo
  protocol, not a CI gate. The risk register at §4 reflects this
  split.

#### W-AB — `hai capabilities --human`

Render the agent-CLI-contract manifest as human-readable prose
instead of JSON / Markdown agent-manifest format.

**Acceptance:** `hai capabilities --human` outputs a 1-page
overview of every command + key flags, suitable for a new user to
print or skim. Existing `--json` and `--markdown` modes unchanged.

#### W-AC — README rewrite

Rewrite for orientation (what is this, who is it for) → quickstart
(install + init + first day) → troubleshooting (the 5 most common
gotchas including F-DEMO-01-shape probe-pull failures).

**Acceptance:** README.md tells a new user the project's purpose,
who it's for, and how to be running in <5 minutes. Existing
"Now/Next" status block + governance/architecture references
preserved. CHANGELOG/AUDIT/ARCHITECTURE links updated to current
versions.

#### W-AD — Error-message quality pass

Every `USER_INPUT` exit-code path in `src/health_agent_infra/cli.py`
must surface a next-step prose hint. Audit current `USER_INPUT`
raises; add hint text where missing.

**Acceptance:** new
`verification/tests/test_user_input_messages_actionable.py` walks
every `src/health_agent_infra/cli.py` USER_INPUT exit code; asserts
the printed message contains a specific actionable verb ("run",
"set", "remove", "check", etc.) and references the user's likely
next command.

#### W-AE — `hai doctor` expansion

Add to existing `hai doctor`:

1. **Onboarding-readiness check** — does the user have intent,
   target, and at least one wellness pull?
2. **Gap diagnostics** — what intake surfaces have stale data, and
   what's the likely cause?
3. **intervals.icu probe-pull check** — `--deep` mode performs a
   live API call (single request) to verify auth ACTUALLY works,
   not just credentials present. **Closes the original F-DEMO-01
   detection gap that W-CF-UA fixed at the symptom layer.**

**Files:** `src/health_agent_infra/core/doctor/checks.py` extension.
Reuses the existing `Probe` protocol from v0.1.11 W-X.

**Acceptance (revised at D14 round 1 per F-PLAN-10 — triage script
moved into the repo):**

- `hai doctor` (default) flags onboarding gaps with actionable
  hints. Test surface covers "no intent rows", "no target rows",
  "no fresh wellness pull", "stale intervals.icu auth".
- `hai doctor --deep` performs a live-API check against
  intervals.icu and classifies the response into one of **five
  outcome classes (one success + four failure classes)**, all
  documented at `reporting/docs/intervals_icu_403_triage.md` (now
  an in-repo versioned artifact, not a private memory note):
  `OK` (success) / `CAUSE_1_CLOUDFLARE_UA` / `CAUSE_2_CREDS` /
  `NETWORK` / `OTHER` (the four failure classes). Each class
  carries a specific actionable next-step in the rendered output.
  Wording revised at D14 round 2 per F-PLAN-R2-05 (round 1
  inconsistently said "four cause classes" while listing five).

#### W-AF — README quickstart smoke test

CI-runnable test that asserts the README's quickstart block
literally works. Parses the README for fenced shell blocks tagged
`bash quickstart`; runs them in a temp directory with a stubbed
intervals.icu fixture; asserts each command exits 0.

**Acceptance:** README quickstart drift caught by CI within one
build cycle of any README change.

#### W-AG — `hai today` cold-start prose

Different prose for day-1 (no streak, no recent plans) vs day-30+
(established streak, history). Uses `hai stats` streak metric to
choose voice.

**Acceptance:** test surface covers both states; rendered prose
differs in opening sentence + closing prompt.

### 2.C — Added W-ids (contracts)

#### W-29-prep — cli.py boundary audit

Per CP1: scaffold the parser/capabilities regression test that
v0.1.14 W-29 (cli.py mechanical split) requires; produce the
boundary table that names which handler-group each subcommand
belongs to.

**Files:**

- `verification/tests/test_cli_parser_capabilities_regression.py`
  (new) — byte-stability assertion on `hai capabilities --json` +
  snapshot assertion on `hai --help` parser tree. Snapshot baseline
  established AFTER intentional v0.1.13 surface changes (W-AB
  `--human` mode, W-AE `--deep` doctor extension) land — see
  sequencing note below.
- `reporting/docs/cli_boundary_table.md` (new) — name every
  subcommand + its target handler-group + estimated LOC. Subcommand
  count derived from the parser/capabilities manifest (NOT
  hardcoded — initial enumeration found 24 top-level
  `sub.add_parser(...)` registrations in `src/health_agent_infra/cli.py`
  + 1 from `src/health_agent_infra/evals/cli.py` lines 84-90, but
  the boundary table must read live from the parser).

**Sequencing (revised at D14 round 1 per F-PLAN-11):**

W-29-prep snapshot baseline is frozen AFTER W-AB and W-AE land,
not before. Rationale: those workstreams add legitimate CLI surface
(`hai capabilities --human`, `hai doctor --deep` classification
output) that would otherwise produce false byte-equality
regressions. Implementation order in v0.1.13:

1. W-AB ships `--human` mode → capabilities manifest grows by one
   row's flag list.
2. W-AE ships `--deep` extension → doctor manifest entry expands.
3. Other added W-ids (W-LINT, W-AK, W-A1C7) ship — these don't
   touch capabilities.
4. **W-29-prep snapshot frozen against post-(1+2+3) capabilities
   state.** Regression test then catches v0.1.14 W-29 mechanical-
   split-induced drift, which is its actual purpose.

**Acceptance:** regression test in place + green against the
post-W-AB/W-AE capabilities baseline; boundary table covers every
subcommand the live parser registers (count derived, not
hardcoded); v0.1.14 W-29 has a clear go/no-go verdict from the
boundary audit. The verdict outcome (split / do-not-split / split-
with-revisions) is recorded in v0.1.13 RELEASE_PROOF; v0.1.14 W-29
gates on it per CP1.

#### W-LINT — Regulated-claim lint

Static + runtime lint blocking regulated-claim phrasing in user-
facing prose. Static catches code-author surfaces; runtime catches
skill-rendered prose at write time.

**Banned phrasings (start list, expandable):** "abnormal HRV",
"clinical-grade", "biomarker", "risk score", "diagnose", "diagnosis",
"medical advice", "treatment", "therapy", "cure", "disease".

**Files:**

- `src/health_agent_infra/core/lint/regulated_claims.py` (new) —
  static + runtime helpers.
- `verification/tests/test_regulated_claim_lint.py` (new) — every
  packaged skill's rationale block scanned + asserted clean.
- `src/health_agent_infra/cli.py` rendering paths — runtime check
  on text crossing the CLI rendering boundary, with `USER_INPUT`
  exit when violated.

**Exception path constraints (revised at D14 round 1 per F-PLAN-09 —
prevents the exception from becoming a wholesale loophole):**

The exception path allows quoting regulated terms ONLY when ALL
four constraints hold:

1. **Allowlisted surface only.** The skill emitting the text must
   be in a hard-coded **packaged-skill** allowlist (initially:
   `expert-explainer` only — the one packaged skill whose explicit
   purpose is bounded definitional / quoted explanation). The
   allowlist contains skill names only; code-owned research
   surfaces (the `src/health_agent_infra/core/research/` registry,
   the `hai research` CLI) are NOT allowlisted because they are
   CLI/runtime surfaces
   and run strict regime per constraint (4) below. The allowlist
   is expandable per future packaged skills that need it; the
   v0.1.13 ship-set is `expert-explainer` alone. (Revised at D14
   round 2 per F-PLAN-R2-06: round 1 erroneously named a
   non-existent `research` skill.)
2. **Citation required.** Each occurrence of a regulated term
   must be accompanied by a provenance citation in the same
   rationale block. The lint helper resolves the citation against
   the allowlisted research source registry under
   `src/health_agent_infra/core/research/`.
3. **Quoted-term context only.** The regulated term must appear
   inside an explicit quote, attribution, or definitional context
   (e.g., "the literature defines biomarker as ..."), not as a
   first-person claim.
4. **Ordinary user-facing prose still blocked.** Rationale blocks
   from non-allowlisted skills + all CLI rendering paths run
   under the strict regime; no exception path applies there.

**Acceptance (revised at D14 round 1 per F-PLAN-09):**

- Lint test green on current packaged skills (no regressions).
- Runtime check fires test-fixture violation correctly for the
  strict regime.
- **Negative test (`test_regulated_claim_exception_bounded`):**
  asserts (a) a non-allowlisted skill quoting a regulated term
  with provenance still fails the lint; (b) an allowlisted skill
  quoting a regulated term WITHOUT provenance fails the lint;
  (c) an allowlisted skill quoting a regulated term in first-
  person framing (no quoted/attributed context) fails the lint;
  (d) only the four-constraints-all-hold case passes.
- **CLI rendering boundary test:** asserts the runtime lint
  applies regardless of skill provenance — even an allowlisted
  skill's output, IF it's about to cross into CLI prose, runs
  under the strict regime.

#### W-AK — Declarative persona expected-actions

Each persona declares an `expected_actions` dict in its
`p<N>_<slug>.py` file: per domain, what action class(es) are
acceptable for the persona's state. Harness asserts the actual
recommendation matches.

**Files:** `verification/dogfood/personas/p*.py` — add
`expected_actions` dict. Harness asserts.

**Acceptance:** all 12 personas have non-empty `expected_actions`;
harness asserts; v0.1.14 W58 prep is unblocked.

#### W-A1C7 — Trusted-first-value rename + acceptance matrix

**A1 (rename):** identify "trusted-first-value" (the gate language
naming the moment when a runtime trusts a user-supplied value as
the source-of-truth) and apply consistent naming across docs +
code if drift exists.

**C7 (acceptance matrix):** codify the acceptance matrix for the
trusted-first-value contract as a contract test.

**Files:** TBD pending design — initial scope estimate:
`AGENTS.md` (gate-language naming section), possibly identifiers in
`src/health_agent_infra/core/synthesis.py` if a rename is required,
new `verification/tests/test_acceptance_matrix.py`.

**Acceptance:** rename consistent across all surfaces; matrix
contract test green; v0.1.13 cycle is the canonical naming source
referenced by future cycles.

**Note:** scope may revise post-design. v0.1.12 CARRY_OVER named
this as a v0.1.13 deferral without a per-W-id contract; this PLAN
is the first time the workstream is fully scoped.

#### W-CARRY — Carry-over register

Per cycle convention: this cycle's CARRY_OVER.md disposes every
v0.1.12 RELEASE_PROOF §5 item + every reconciliation v0.1.13
named-defer.

**Files:** `reporting/plans/v0_1_13/CARRY_OVER.md` (new, this dir).

**Acceptance:** every v0.1.12 §5 line has a disposition row; every
reconciliation v0.1.13+ item from v0.1.12 CARRY_OVER §3 has a row.

---

## 3. Ship gates

| Gate | Target |
|---|---|
| **Test surface** | ≥ 2384 + (estimate +60-80 from new tests across W-Vb, W-N-broader, W-FBC-2, W-AA, W-AD, W-AE, W-AF, W-LINT, W-AK, W-A1C7) → **target ≥ 2444** |
| **Pytest broader gate** | `uv run pytest verification/tests -W error::Warning` exits 0 (currently fork-deferred per W-N-broader) |
| **Pytest narrow gate** | `uv run pytest verification/tests -W error::pytest.PytestUnraisableExceptionWarning` exits 0 (current ship-gate, must remain green) |
| **Mypy** | `uvx mypy src/health_agent_infra` reports 0 errors (held from v0.1.12) |
| **Bandit** | `bandit -ll`: 0 unsuppressed Medium/High; Low ≤ 50 (D10 settled threshold) |
| **Capabilities byte-stability** | `hai capabilities --json` deterministic against the post-W-AB/W-AE baseline (W-29-prep regression test green; baseline frozen AFTER intentional v0.1.13 surface changes per F-PLAN-11 sequencing) |
| **Persona matrix** | 12 personas, ≤ 1 finding total post-cycle, all with `expected_actions` declared (W-AK) |
| **Demo regression** | `hai demo start --persona <slug> && hai daily` reaches `synthesized` for **each** of `p1_dom_baseline`, `p4_strength_only_cutter`, `p5_female_multisport` (W-Vb end-to-end ship-set; the 9 non-ship-set personas P2/P3/P6/P7/P8/P9/P10/P11/P12 fork-deferred to v0.1.14 W-Vb-3 per F-PLAN-06 + F-PLAN-R2-02) |
| **Onboarding deterministic test gate** | `test_init_onboarding_flow.py` green: stubbed-input + stubbed-intervals.icu run reaches `synthesized` (W-AA; this is the ship-gate, not the wall-clock SLO per F-PLAN-08) |
| **Onboarding operator demo SLO** | Target: new-user `pipx install` → `hai init` → `synthesized` plan ≤ 5 min on broadband + modern hardware. Documented in `reporting/docs/onboarding_slo.md` (new); manual demo protocol, NOT a CI gate |
| **README smoke test** | `test_readme_quickstart_smoke` green (W-AF) |
| **Regulated-claim lint** | `test_regulated_claim_lint` green; `test_regulated_claim_exception_bounded` green (negative tests prove the exception path is non-loophole per F-PLAN-09); 0 violations in packaged skills under the strict regime (W-LINT) |
| **intervals.icu triage doc** | `reporting/docs/intervals_icu_403_triage.md` exists in-tree and is cited from W-AE acceptance (per F-PLAN-10 — moved out of private memory note into versioned project artifact) |
| **Codex IR verdict** | SHIP or SHIP_WITH_NOTES at empirical settling (3 rounds typical) |
| **CHANGELOG.md** | v0.1.13 entry with full Added/Changed/Fixed sections |
| **RELEASE_PROOF.md** | declares `tier: substantive` per CP3/D15 |

---

## 4. Risks register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| W-N-broader 50-site refactor reveals deeper connection-lifecycle bug requiring schema-touching fix | medium | scope-expand | Phase 0 D11 audit will surface before implementation; authoritative file list derived from a fresh `pytest -W error::Warning` run at Phase 0 open per F-PLAN-04; if found, escalate to substantive-substantive (cycle re-scope) |
| W-Vb persona-replay reveals proposal-log shape gaps in current state-snapshot contract | medium | scope-expand | Implement P1 first as smoke test; if gap found, route through `cycle_proposals/CP7.md` (new) before continuing P4/P5; never route mid-cycle to any of the 9 non-ship-set personas (P2/P3/P6/P7/P8/P9/P10/P11/P12 are honestly fork-deferred to v0.1.14 W-Vb-3 per F-PLAN-06 + F-PLAN-R2-02) |
| W-FBC-2 multi-domain rollout exposes design choice (option A default vs option B fork) | medium | architectural-decision | Per F-PLAN-07 + the design doc at `reporting/docs/supersede_domain_coverage.md`: option A is the default; option B is the only documented fork available; option C is explicitly out-of-v0.1.x scope. If option B is selected at design phase, add the per-domain fingerprint-primitive sub-W-id; otherwise option A carries cleanly |
| W-LINT exception path becomes a wholesale loophole | low | safety / regulatory | Four-constraints-all-hold gate per F-PLAN-09 (allowlist + citation + quoted-context + ordinary-prose-still-blocked) + `test_regulated_claim_exception_bounded` negative test asserting each individual constraint fails when violated. CLI rendering boundary always runs strict regime regardless of skill provenance |
| W-AA onboarding wall-clock SLO conflict between deterministic gate + operator SLO | low | governance / UX | SLO split per F-PLAN-08: deterministic test gate (stubbed) is the ship-gate; operator wall-clock SLO is a documented target with "still pulling" allowed degraded state, recorded in `reporting/docs/onboarding_slo.md` and not a CI gate |
| W-29-prep capabilities byte-stability collides with W-AB/W-AE intentional CLI surface changes | medium | hidden-coupling | Per F-PLAN-11 sequencing: W-AB + W-AE land FIRST; W-29-prep snapshot baseline frozen AFTER. The regression test then catches v0.1.14 W-29 split-induced drift (its actual purpose), not v0.1.13's intentional surface growth |
| Post-W-29-prep boundary audit verdict says "do not split" | low | governance | Acceptable outcome; v0.1.14 W-29 gates on the verdict per CP1 |
| 17-workstream scope exceeds single-contributor 5-week budget (revised count per F-PLAN-01) | medium | timeline-slip | Risk-driven scope cuts per tactical_plan §9: cut W-AC + W-AF first (saves 2-3d); cut W-AK second (saves 1d); never cut W-N-broader / W-FBC-2 / W-Vb (inherited release-blocker shape) |

---

## 5. Effort estimate

**22.5-32.5 days, single-contributor** (revised at D14 round 1
per F-PLAN-01 — W-CARRY's 0.5d roll-up included). Largest cycle in
the v0.1.x track if all 17 W-ids land. Realistic ship: **5-7
calendar weeks** from open assuming 4 hours/day average.

If risk-driven cuts engage (cut W-AC at 1-2d + W-AF at 1d + W-AK
at 1d, total savings 3-4d), effort drops to **19.5-28.5 days**
(revised at D14 round 2 per F-PLAN-R2-07 — round 1 reported
18.5-25.5d, which implied 4-7d of savings rather than the actual
3-4d the named cuts produce).

---

## 6. Cycle pattern compliance (D11 + D14)

Phase 0 (D11) bug-hunt opens after this PLAN.md reaches
`PLAN_COHERENT` per Codex D14 audit. Probes:

1. Internal sweep: `pytest verification/tests -q`, `uvx mypy`,
   `bandit -ll`, `ruff check`.
2. Audit-chain integrity probe: spot-check three recent days of
   `hai explain` output against `daily_plan` rows.
3. Persona matrix run: 12 personas through harness; record
   findings.
4. Codex external bug-hunt: prompt at `codex_audit_prompt.md` (when
   authored at Phase 0 open).

Findings consolidated to `audit_findings.md` with `cycle_impact`
tags. Pre-implementation gate fires after consolidation.

---

## 7. Provenance

- **Authored:** 2026-04-29 by Claude in extended user session.
- **Co-authored data:** intervals.icu Cloudflare diagnostic +
  W-CF-UA root-cause investigation.
- **Templates used:** `reporting/plans/_templates/codex_plan_audit_prompt.template.md`.
- **Ship-time freshness checklist (AGENTS.md "Release Cycle Expectation"):**
  applies at v0.1.13 ship; not yet relevant at cycle open.
