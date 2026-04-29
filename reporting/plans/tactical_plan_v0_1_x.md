# Tactical Plan — v0.1.11 through v0.2.0

> **Status.** Authored 2026-04-27 by Claude. Companion to
> `strategic_plan_v1.md`. Covers concrete workstreams across the
> next 6-8 releases (~6-9 months of execution).
>
> **Reading intent.** When the maintainer is opening a new release
> cycle, this is the doc that tells them what to scope. The strategic
> plan answers "why"; this answers "what next."
>
> **Refresh cadence.** Updated per release. After each ship, the
> shipped release moves from "in-flight" to "shipped" with a brief
> retro line; the next release-in-flight gets fully fleshed.

---

## Table of contents

1. Release timeline + dependency chain
2. v0.1.11 — Audit-cycle deferred items + persona expansion
3. v0.1.12 — Type-checker + security + UX polish
4. v0.1.13 — Public-surface hardening + onboarding
5. v0.1.14 — Eval expansion + LLM-judge prep
6. v0.2.0 — Weekly review + insight ledger + factuality gate
7. Cross-cutting workstreams (run alongside any release)
8. v0.1.x release pattern playbook

---

## 1. Release timeline + dependency chain

| Release | Theme | Earliest start | Earliest ship | Hard dependencies |
|---|---|---|---|---|
| **v0.1.10** | Pre-PLAN audit + persona harness + correctness | shipped 2026-04-27 | shipped | none (substrate) |
| **v0.1.11** | Audit-cycle deferred items (W-B/E/F/H/K/L/N) + persona expansion | 2026-04-28 | 2026-05-15 | v0.1.10 (audit findings input) |
| **v0.1.12** | Mypy strict baseline + bandit closure + state-change UX | post-v0.1.11 + 1-2 weeks | 2026-06 | v0.1.11 (W-B coverage gate must land first) |
| **v0.1.13** | Public surface hardening + first-time-user onboarding | post-v0.1.12 + 1-2 weeks | 2026-Q3 early | v0.1.12 (mypy clean + W-E supersession) |
| **v0.1.14** | Eval expansion + LLM-judge factuality gate scaffolding | post-v0.1.13 + 2-3 weeks | 2026-Q3 mid | v0.1.13 (CLI surface stable) |
| **v0.2.0** | Weekly review + insight proposal ledger + W58 factuality gate | post-v0.1.14 + 2-4 weeks | 2026-Q3 late / Q4 | v0.1.14 (judge harness) |

**Total v0.1.x → v0.2.0 horizon:** 6-9 months from 2026-04-27.
This puts v0.2.0 ship at late 2026-Q3 to 2026-Q4 — consistent with
strategic plan §7 Wave-2 timing.

**No hard schedule.** Each release ships when its acceptance
criteria are met; the timeline is a planning aid, not a commitment.

---

## 2. v0.1.11 — Audit-cycle deferred items + persona expansion

> **Theme.** Close every workstream v0.1.10 deferred. Expand the
> persona matrix from 8 → 12. Introduce property-based testing
> for the policy DSL. End-state: every named finding from
> `audit_findings.md` is either fixed or formally deferred to
> v0.2+.

### 2.1 In scope

| W-id | Title | From | Severity | Effort |
|---|---|---|---|---|
| **W-B** | R-volume-spike minimum-coverage gate | v0.1.10 deferred | band-miscalibration | 1-2 days |
| **W-E** | `hai daily` re-run state-change supersession | v0.1.10 deferred | audit-chain-break | 2-3 days |
| **W-F** | Audit-chain version-counter integrity | v0.1.10 deferred | audit-chain-break | 1-2 days |
| **W-H1** | Mypy critical-class fixes (correctness) | v0.1.10 deferred | correctness | 2-3 days |
| **W-K** | Bandit B608 site-by-site verdict | v0.1.10 deferred | security review | 1-2 days |
| **W-L** | Bandit B310 url-scheme audit | v0.1.10 deferred | security | 0.5 day |
| **W-N** | Pytest unraisable warning cleanup | v0.1.9 backlog | nit | 0.5 day |
| **W-O** | Persona matrix expansion (8 → 12) | NEW | infrastructure | 2-3 days |
| **W-P** | Property-based tests for policy DSL | NEW | testing infrastructure | 2-3 days |
| **W-Q** | F-B-03 review-schedule auto-run gap investigation | v0.1.10 deferred (investigative) | audit-chain integrity | 1-2 days |
| **W-R** | F-C-03 historical-rollup edge cases | v0.1.10 (post-fix observations) | correctness polish | 1 day |

### 2.2 Out of scope (deferred to v0.1.12+)

- W-H2: mypy stylistic findings (Literal abuse, redefinition
  warnings, scenario-result type confusion). Different class than
  W-H1; v0.1.12 scope.
- F-B-04: domain-coverage drift across supersession (semantic
  question, needs design discussion before code).
- F-C-05: strength_status enum surfaceability (needs CLI
  capabilities-manifest extension; v0.1.13 scope).
- F-C-06: persona matrix elevated-stress coverage (covered by W-O).

### 2.3 Per-workstream contracts

#### W-B — R-volume-spike minimum-coverage gate

Add `min_sessions_last_28d` threshold to R-volume-spike. Default 8.
Below threshold: rule emits `coverage_band: 'insufficient'` rather
than firing as spike.

**Files:** `core/synthesis_policy.py`, `domains/strength/policy.py`,
`core/config.py` (DEFAULT_THRESHOLDS).

**Tests:** new `verification/tests/test_xrule_volume_spike_coverage.py`
covering boundary behaviour. Persona matrix re-run shows P1, P4,
P5, P6, P7 stop escalating on regular training pattern.

**Acceptance:** persona matrix findings drop from 3 → ≤ 1.

#### W-E — `hai daily` re-run state-change supersession

State-fingerprint computation in `core/synthesis.py`. If a canonical
plan exists for `(for_date, user_id)`, compare its captured
fingerprint to current. Mismatch → produce `_v<N>` supersession
with fresh proposal_log rows + rationale prose.

**Files:** `core/synthesis.py`, `cli.py` daily handler, `core/state/`
(fingerprint storage column).

**Tests:** new `verification/tests/test_daily_supersede_on_state_change.py`
reproduces the v0.1.10 morning-briefing scenario.

**Acceptance:** state-change re-run produces `_v2` plan id with
refreshed prose. Idempotent re-run with no state change is no-op.

#### W-F — Audit-chain version-counter integrity

Investigate root cause of skipped `_v2` / `_v3` versions in
historical chains (F-B-01). Likely fix: counter increments only
after successful commit.

**Files:** `core/synthesis.py` supersession path.

**Tests:** new test asserting sequential version numbers across
contrived re-synthesise loop.

**Acceptance:** no skipped versions in any chain post-fix.

#### W-H1 — Mypy critical-class fixes

Six high-impact mypy errors flagged correctness in `audit_findings.md`:
F-A-03 (adapter type confusion), F-A-04 (None propagation),
F-A-05 (eval scenario type confusion), F-A-06 (None comparisons),
F-A-07 (exercise None-into-str), F-A-11 (int-of-Optional 4 sites).

**Files:** `cli.py`, `core/synthesis.py`, `evals/runner.py`,
`core/state/runtime_event_log.py`, `core/state/projector.py`,
`core/doctor/checks.py`.

**Acceptance:** mypy correctness-class errors → 0. Stylistic-class
errors (~10 remaining) deferred to v0.1.12 W-H2.

#### W-K — Bandit B608 site-by-site verdict

Per-site determination on each B608 SQL string-construction finding:
either a `# nosec B608` comment with reason, or a refactor.

**Files:** `core/explain/queries.py`, `core/intent/store.py`,
`core/memory/store.py`, `core/state/projector.py`,
`core/state/projectors/running_activity.py`, `core/state/snapshot.py`,
`core/target/store.py`, `evals/runner.py`.

**Acceptance:** bandit -ll: 0 unsuppressed B608 findings.

#### W-L — Bandit B310 url-scheme audit

Confirm `core/pull/intervals_icu.py:310` URL is fully constant +
trusted. Document with `# nosec B310 # reason: ...` OR add allowed-
schemes whitelist.

**Acceptance:** bandit -ll: 0 unsuppressed findings of any kind.

#### W-N — Pytest unraisable warning cleanup

Find HTTP response not closed in finally block in
`safety/tests/test_snapshot_bundle.py::test_snapshot_v1_0_recovery_block_has_three_keys`.

**Acceptance:** pytest run with `-W error::Warning` passes clean.

#### W-O — Persona matrix expansion (8 → 12)

Add four personas to fill matrix gaps:

| New persona | Stresses |
|---|---|
| **P9 — Older female endurance (52F)** | Female + age-50+ band edge + endurance — gap in current matrix |
| **P10 — Adolescent recreational (17M)** | Below-spec age band; expected to error gracefully or document the gap |
| **P11 — Elevated-stress hybrid (28M, persistent stress)** | F-C-06 — current matrix has uniform low-stress; need a persona stressing the stress domain |
| **P12 — Vacation-returner (35F, 14d gap then back)** | Comeback-from-gap edge; tests classifier behaviour after data discontinuity |

P10 explicitly probes the user-set boundary to confirm graceful
failure rather than silent acceptance.

**Files:** `verification/dogfood/personas/p9_*.py` through
`p12_*.py`, plus `personas/__init__.py` update.

**Acceptance:** all 12 personas run cleanly through the harness.
P10's expected behaviour documented (likely: defer everything OR
explicit "out of supported user set" message).

#### W-P — Property-based tests for policy DSL

Hypothesis-based tests asserting policy-DSL invariants:

- For all classified_state inputs in valid ranges, `evaluate_*_policy`
  returns a result whose `forced_action` (if not None) is in the
  domain's action enum.
- For all proposal inputs, `apply_phase_a` returns `mutated` with
  `action` in the domain's action enum.
- For all snapshots, X-rule `recommended_mutation.action` (when
  present) is in the target domain's enum.

**Files:** new `verification/tests/test_policy_dsl_invariants.py`.

**Acceptance:** hypothesis-based tests find ≥ 0 new bugs (zero is
informative — it confirms the invariants hold). Any bug found =
fix-now scope.

#### W-Q — F-B-03 review-schedule auto-run investigation

Investigate why 2026-04-25 + 2026-04-26 had 0 reviews scheduled
despite 6 recommendations each. Determine: regression, intended-
manual, or schedule-failure.

**Acceptance:** clear verdict + either fix-now (regression) or doc
update + UX surface (intended-manual).

#### W-R — F-C-03 historical-rollup edge cases

v0.1.10 W-D-ext fixed historical-activity rollup but left some
fields unfilled (`session_count`, `total_duration_s` hardcoded
None). Decide whether to populate them from the aggregator OR keep
the v1 contract intentional.

**Acceptance:** explicit decision documented + (if populating)
projection updated + tests added.

### 2.4 Acceptance criteria for v0.1.11 ship

- All 11 workstreams complete OR formally deferred with reason.
- Pytest count ≥ 2200 (was 2169 at v0.1.10 ship; +30+ from new
  tests across W-B, W-E, W-F, W-O, W-P, W-Q, W-R).
- Persona matrix: 12 personas, ≤ 1 finding total post-fix.
- mypy correctness-class errors: 0.
- bandit -ll: 0 unsuppressed.
- ruff: 0.
- Codex audit round 1: SHIP or SHIP_WITH_NOTES.
- CHANGELOG.md updated; RELEASE_PROOF.md emitted.

### 2.5 Effort estimate

13-16 days of focused single-maintainer work. Realistic ship: 3-4
calendar weeks from open.

---

## 3. v0.1.12 — Carry-over closure + trust repair

> **Theme (rebaselined 2026-04-29 per W-AC freshness sweep + post-
> reconciliation rescope).** Trust repair, not feature push. Close
> v0.1.11 named-defers; fix stale public docs + a packaging bug;
> document six cycle proposals (CP1-CP6) that the v0.1.13+ roadmap
> depends on. **The authoritative scope of record is
> [`reporting/plans/v0_1_12/PLAN.md`](v0_1_12/PLAN.md)** (D14 plan-
> audit closed at `PLAN_COHERENT` round 4). This section
> summarises; the PLAN holds the contract.

### 3.1 In scope

| W-id | Title | Effort |
|---|---|---|
| **W-AC** | Public-doc freshness sweep + ship-checklist | 0.5d |
| **W-CARRY** | Carry-over register | 0.5d |
| **W-Vb** *(partial closure)* | `hai demo` packaged-fixture path + skeleton-loader integration. Persona-replay end-to-end (proposal pre-population so `hai daily` reaches synthesis) deferred to v0.1.13 W-Vb per F-IR-02. | 3-4d |
| **W-H2** | Mypy stylistic-class fixes (target ≤ 5 errors; achieved 0) | 2-3d |
| **W-N-broader** *(fork-deferred)* | `-W error::Warning` gate audit: 49 + 1 sqlite3 leak sites surfaced. Audit-time fork to ">150-branch behaviour deliberately" — v0.1.12 ships v0.1.11 narrow `PytestUnraisableExceptionWarning` gate unchanged; broader-gate fix deferred to v0.1.13 W-N-broader. | 3-4d |
| **W-D13-SYM** | D13-symmetry contract test + `coerce_*` fix in 4 domain `policy.py` files | 0.5-1d |
| **W-PRIV** | Privacy doc updates + `hai auth remove` subcommand | 0.5-1d |
| **W-FBC** *(partial closure)* | F-B-04 design doc + `--re-propose-all` flag (CLI parser + capabilities + report-surface field only). **Recovery prototype + multi-domain runtime enforcement deferred to v0.1.13 W-FBC-2** per F-IR-01 (synthesis-side wiring did not land at v0.1.12 ship). | 0.5-1d |
| **W-FCC** | F-C-05 `strength_status` enum surface in capabilities + `hai today --verbose` | 1d |
| **W-CP** | Six cycle proposals CP1-CP6 (governance docs) | 1d |

### 3.2 Acceptance

- All ship gates green per
  [`reporting/plans/v0_1_12/PLAN.md`](v0_1_12/PLAN.md) §3.
- v0.1.11 named-defers closed or partial-closed with each
  residual named in §4 (this plan) and
  [`reporting/plans/v0_1_12/RELEASE_PROOF.md`](v0_1_12/RELEASE_PROOF.md)
  §5. v0.1.12 inherits *three* residuals to v0.1.13:
  W-FBC-2 (F-B-04 recovery prototype + multi-domain), W-Vb
  persona-replay end-to-end, and W-N-broader broader-warning gate.
- CP1-CP5 deltas applied to AGENTS.md / strategic plan / tactical
  plan at v0.1.12 ship; CP6 application deferred to v0.1.13
  strategic-plan rev.

### 3.3 Effort estimate

13-20 days single-contributor.

### 3.4 Tier (CP3, D15)

`substantive` — multiple cycle-proposal docs, demo packaging
contract change, broader test gate.

---

## 4. v0.1.13 — Public-surface hardening + onboarding

> **Theme.** Make first-time-user experience credible. The
> maintainer's daily-driver experience is well-tuned; new-user UX
> has rough edges (state init, credential auth, intake discovery).
> v0.1.13 closes those without changing the runtime contract.
> End-state: `pipx install health-agent-infra && hai init` produces
> a working setup in under 5 minutes for a recreational athlete
> with intervals.icu.

### 4.1 In scope

| W-id | Title | Effort |
|---|---|---|
| **W-AA** | First-time-user onboarding flow — `hai init` walks profile + targets + auth | 2-3 days |
| **W-AB** | `hai capabilities --human` mode for end-users (not agents) | 1 day |
| **W-AC** | README rewrite — orientation, quickstart, troubleshooting | 1-2 days |
| **W-AD** | Error-message quality pass — every USER_INPUT exit code carries actionable next step | 1-2 days |
| **W-AE** | `hai doctor` expansion — onboarding-readiness check + gap diagnostics | 1-2 days |
| **W-AF** | Public README quickstart smoke test (CI-runnable) | 1 day |
| **W-AG** | `hai today` cold-start prose — different language for day-1 vs day-30 users | 1 day |

**Added at v0.1.12 ship per CP1 + reconciliation §6 + Codex F-PLAN-R2-04 + Codex implementation review F-IR-01/02/03:**

| W-id | Title | Effort | Source |
|---|---|---|---|
| **W-29-prep** | cli.py boundary audit (boundary-table verification + parser/capabilities regression test scaffold) | 0.5d | CP1 |
| **W-FBC-2** | F-B-04 — full closure inherited from v0.1.12 W-FBC partial. v0.1.13 ships: (1) recovery prototype: synthesis-side `--re-propose-all` enforcement on the recovery domain with the `recovery_proposal_carryover_under_re_propose_all` carryover-uncertainty token + persona-style scenario tests P1/P5/P9; (2) multi-domain rollout to all 6 domains; (3) per-domain fingerprint primitive if option B/C is chosen at design. | 3-4d | Codex F-PLAN-R2-04 + F-IR-01 + F-IR-R2-01 (the v0.1.12 cycle delivered design doc + flag plumbing only; both the recovery prototype and the multi-domain enforcement carry to v0.1.13) |
| **W-Vb** (persona-replay end-to-end) | Author full-shape persona fixtures (DomainProposal seeds across all 6 domains per persona) + flip `apply_fixture()` to the proposal-write branch; wire so `hai demo start --persona <slug>` + `hai daily` reaches `synthesized`; clean-wheel build-install-subprocess test | 3-4d | F-IR-02 (loader + skeleton fixtures shipped at v0.1.12; full replay deferred) |
| **W-N-broader** | `-W error::Warning` gate fix — audit each of the 49 + 1 sqlite3 connection-lifecycle leak sites surfaced by the v0.1.12 Phase 0 audit; close conn correctly on every CLI command + helper path; restore the broader-gate ship target | 4-6d | F-IR-03 (v0.1.12 fork-deferred at audit time per cycle-budget reasoning; v0.1.13 inherits the 49 + 1 site count as hard input) |
| **W-LINT** | Regulated-claim lint (FDA general-wellness boundary — block "abnormal HRV", "clinical-grade marker", "risk score", "biomarker", etc. in user-facing prose) | 1-2d | Reconciliation C2 |
| **W-AK** | Declarative persona expected-actions (pulled forward from v0.1.14; precondition for v0.1.14 W58 prep) | 1d | Reconciliation A5 |
| **CP6 application** | Apply strategic plan §6.3 framing edit per `reporting/plans/v0_1_12/cycle_proposals/CP6.md` | 0.25d | CP6 deferred application |

### 4.2 Acceptance

- Time-from-install-to-first-recommendation < 5 min for fresh user
  with intervals.icu credentials.
- 100% of CLI exit codes carry actionable next-step prose for
  USER_INPUT class.
- `hai doctor` flags all common onboarding gaps.

### 4.3 Effort estimate

8-12 days.

### 4.4 Strategic context

This release is the bridge to inviting external users. v0.1.13's
onboarding flow is what determines whether the "second user"
experiment in `risks_and_open_questions.md` § "single-user
assumptions failing" can be run cleanly.

---

## 5. v0.1.14 — Eval expansion + LLM-judge prep

> **Theme.** Build the eval substrate for v0.2.0's W58 factuality
> gate. Expand scenario fixtures, add ground-truth methodology, prep
> the local-LLM judge harness without lighting it up.
> End-state: eval surface is rich enough that v0.2.0 W58 is a
> wire-up release, not a build-and-ship.

### 5.1 In scope

| W-id | Title | Effort |
|---|---|---|
| **W-AH** | Scenario fixture expansion: 30+ new per-domain scenarios | 3-4 days |
| **W-AI** | Ground-truth labelling methodology + maintainer review tool | 2-3 days |
| **W-AJ** | LLM-judge harness scaffold (no model invocation yet) | 2-3 days |
| **W-AK** | Per-persona expected-behaviour assertions in dogfood harness | 2 days |
| **W-AL** | Calibration eval — confidence vs. ground truth correlation | 2 days |
| **W-AM** | Adversarial scenario fixtures — explicit "should escalate" cases | 1-2 days |
| **W-AN** | `hai eval run --scenario-set <set>` CLI surface for batch eval | 1-2 days |

**Added at v0.1.12 ship per CP1 + reconciliation §6 + Codex F-PLAN-09:**

| W-id | Title | Effort | Source |
|---|---|---|---|
| **W-29** | cli.py mechanical split (1 main + 1 shared + 11 handler-group, <2500 each) — conditional on v0.1.13 W-29-prep verdict; parser/capabilities regression test mandatory | 3-4d | CP1 |
| **W-DOMAIN-SYNC** | Scoped contract test (single truth table + expected-subset assertions; not all 8 named tables are six-domain registries — `_DOMAIN_ACTION_REGISTRY` is intentionally Phase-A-only) | 0.5d | Reconciliation L2 + Codex F-PLAN-09 |

**Note:** A12 judge-adversarial fixtures fold into W-AI (above), and
A2/W-AL calibration scaffold ships schema/report-shape only;
real correlation work defers to v0.5+ per reconciliation
action 15.

### 5.2 Acceptance

- Scenario fixtures grow from current ~50 → 120+.
- Per-persona expected-behaviour table in dogfood harness covers
  all 12 personas across all 6 domains.
- LLM-judge harness has clean invocation interface; v0.2.0 W58 just
  needs to plug in the model.
- Calibration eval reports confidence-vs-truth correlation per
  domain.

### 5.3 Effort estimate

13-18 days. Largest release in the v0.1.x track.

---

## 6. v0.2.0 — Weekly review + insight ledger + factuality gate

> **Theme.** Make the runtime useful beyond one day. Original v0.1.9
> scope (cut to hardening); now lands as v0.2.0. Detail in strategic
> plan § 7 Wave 2.

### 6.1 In scope

Lifted from `historical/multi_release_roadmap.md` § 4 v0.1.9 (cut),
now v0.2.0. **Reshaped at v0.1.12 per CP5 (single substantial
release with shadow-by-default LLM judge):**

- **W52: `hai review weekly --week YYYY-Www [--json|--markdown]`.**
  Code-owned aggregation across accepted state, intent, target,
  recommendation, X-rule firing, review outcome, data quality.
  **Source-row locators required for every quantitative claim**
  (carrier: `recommendation_evidence_card.v1` schema per
  reconciliation C8).
- **W53: Insight proposal ledger** (`insight_proposal` + `insight`
  tables).
- **W58D: Deterministic factuality gate.** Every quoted
  quantitative claim in weekly-review prose must resolve to a
  source-row locator. Blocking from day 1. No LLM in this layer.
- **W58J: LLM judge layer.** Residual judgment on causal framing,
  missing uncertainty, overconfident tone. Local Prometheus-2-7B
  (or comparable) pinned by SHA. Builds on v0.1.14's harness.
  Ships **shadow-by-default** with `HAI_W58_JUDGE_MODE = shadow |
  blocking` env flag. Logs every shadow-mode judgement to
  `judge_decision_log` table for evidence accumulation. Flag flip
  to blocking happens within v0.2.0 (or v0.2.0.x patch) once
  shadow-mode evidence shows ≤ 5% false-block rate over ≥ 50
  weekly reviews. Memory-poisoning fixtures land alongside shadow
  mode.
- **W-30: capabilities-manifest schema freeze** as the last act
  of the cycle, after W52/W58D/W58J schema additions land
  (per CP2).

### 6.2 Acceptance

- Weekly review runs deterministically over fixture weeks,
  output byte-stable.
- Insight proposal ledger has migration + CLI + snapshot
  integration + capability manifest entry.
- Factuality judge: deterministic claim-block (W58D) enforces
  from day 1. LLM judge (W58J) ships shadow-by-default; logs
  every decision to `judge_decision_log`; flag-flip threshold
  + procedure documented in v0.2.0 PLAN. Memory-poisoning
  fixtures present.
- Capabilities-manifest schema frozen as last cycle act
  (W-30 / per CP2).
- Test count grows ≥ 30 vs v0.1.14.

### 6.3 Effort estimate

15-20 days. Last v0.1.x-style release; v0.2 is a major version
bump because the schema changes (new tables) are ledger-shape
mutations, not pure additions.

### 6.4 Strategic context

v0.2.0 is the gateway to Wave 3 (MCP + extension contracts) per
strategic plan §7. After v0.2.0 ships and weekly reviews accumulate
~3 months of clean data, v0.3+ can begin.

---

## 7. Cross-cutting workstreams (run alongside any release)

These are "always available, never the headline" workstreams. Pick
them up when a primary workstream blocks or when the release has
slack capacity.

### 7.1 Documentation freshness

- AGENTS.md kept current — every release adds a "settled decisions"
  delta if any.
- ARCHITECTURE.md re-pass at every minor release boundary.
- REPO_MAP.md update when directory structure changes.
- CHANGELOG.md entry per release (already disciplined).

### 7.2 Refactor backlog

- W29 (cli.py split) — deferred per D4. Revisit when cli.py
  exceeds 10kloc OR when external integration arrives.
- W30 (capabilities manifest schema freeze) — deferred per D4.
  Revisit when first external consumer lands.
- W57 architectural delete-vs-archive review — periodically
  audit that no path bypasses the archive discipline.

### 7.3 Performance regression watch

- `hai daily` end-to-end < 1s for typical state DB.
- `hai today` rendering < 200ms.
- Persona matrix full run < 2 min.

If any of these regress, open a PR with a regression-test
attached, not a fix-and-go.

### 7.4 Security posture

- Quarterly dep audit (`pip-audit`).
- Annual review of credential storage paths.
- Secret-handling smoke test in CI.

### 7.5 External-eyes pulses

- Once per major version, run a Codex audit of the entire
  `src/health_agent_infra/` for findings the maintainer + Claude
  audit cycles missed.
- Once per year, a full repo read by a different LLM (Gemini,
  GPT-X) for fresh-eyes review.

---

## 8. v0.1.x release pattern playbook

The four-round audit cycle is now standardised. Each release follows:

### 8.1 Phase 0 — Pre-PLAN bug hunt (NEW v0.1.10 pattern)

For substantive releases. Optional for doc-only or small-scope.

- Internal sweep (pytest, ruff, mypy, bandit)
- Audit-chain integrity probe
- Persona matrix run
- Codex external bug-hunt (parallel)
- Findings consolidated to `audit_findings.md`

Output: structured findings list informs PLAN.md scope.

### 8.2 Phase 1 — PLAN.md authoring

Per-workstream contract per `v0_1_10/PLAN.md` template:
- W-id + title + severity + effort
- Files affected
- Tests authored
- Acceptance criteria
- Dependencies

### 8.3 Phase 2 — Codex audit round 1

External audit of PLAN.md + working tree state. Verdict: SHIP /
SHIP_WITH_NOTES / DO_NOT_SHIP.

### 8.4 Phase 3 — Maintainer response + implementation rounds

Each Codex finding gets one of: fix, defer with reason,
disagreement with reason. Implementation rounds continue until
verdict is SHIP.

### 8.5 Phase 4 — RELEASE_PROOF.md + ship

Full pytest log + persona harness re-run + per-workstream
acceptance check. CHANGELOG.md updated. Wheel built. PyPI publish
gated on maintainer review.

### 8.6 Phase 5 — Post-ship retro

Brief retro section appended to CHANGELOG entry: what worked, what
didn't, what to keep, what to change next cycle.

---

## 9. Risk-driven scope cuts

If maintainer bandwidth tightens, scope-cut order (lowest-
strategic-cost first):

1. v0.1.13 W-AC (README rewrite) — defer; keep current README.
2. v0.1.14 W-AM (adversarial scenarios) — defer; merge into v0.2.0.
3. v0.1.12 W-Y (CI persona subset) — defer; persona harness stays
   maintainer-invoked.
4. v0.1.11 W-O (persona expansion) — partial; ship 2 of 4 new
   personas instead of all 4.
5. v0.1.13 ENTIRELY — skip; jump straight to v0.1.14 eval expansion.

DO NOT cut: any of W-B, W-E, W-F, W-H1 (correctness floor); W52,
W53, W58 from v0.2.0 (strategic Wave 2 anchor).

---

## 10. Provenance + evolution

**Authored:** 2026-04-27 by Claude in extended planning session.

**Sources:**
- Strategic plan v1 § 7 (waves to v1.0).
- v0.1.10 audit_findings.md (deferred items list).
- v0.1.10 RELEASE_PROOF.md (test surface baseline).
- AGENTS.md (settled decisions D1-D12).
- 2026-04-25 historical/multi_release_roadmap.md (release pattern).

**Refresh:** updated per release. After v0.1.11 ships, the v0.1.11
section becomes "shipped" with a 1-paragraph retro, and v0.1.12
becomes the "in-flight" detail.

**Boundary:** this doc covers v0.1.11 → v0.2.0. v0.3+ is in the
strategic plan as wave-level themes; tactical detail will be
authored when v0.2.0 ships.

---

*Last reviewed: 2026-04-27 by Claude. Next review: post-v0.1.11 ship.*
