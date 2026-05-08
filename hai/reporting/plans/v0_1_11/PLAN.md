# v0.1.11 — Audit-cycle deferred items + persona expansion + property tests

> **Status.** **D14 plan-audit chain closed: PLAN_COHERENT at
> round 4 (2026-04-28).** Rounds 1-3 verdicts
> `PLAN_COHERENT_WITH_REVISIONS` (10 + 5 + 3 = 18 findings, all
> closed); round 4 verdict `PLAN_COHERENT`, no findings.
> Audit-chain artifacts in this folder:
> `codex_plan_audit_response.md`,
> `codex_plan_audit_response_round_1_response.md`,
> `codex_plan_audit_round_2_response.md`,
> `codex_plan_audit_round_2_response_response.md`,
> `codex_plan_audit_round_3_response.md`,
> `codex_plan_audit_round_3_response_response.md`,
> `codex_plan_audit_round_4_response.md`.
>
> **Next gate: Phase 0 (D11) pre-PLAN bug-hunt.** Authored as
> `PRE_AUDIT_PLAN.md` in this folder when the cycle opens.
> Findings consolidate to `audit_findings.md` with `cycle_impact`
> tags; pre-implementation gate fires after consolidation.
>
> **Revised 2026-04-28** five times: twice to absorb all 7
> demo-run findings (see
> `reporting/plans/post_v0_1_10/demo_run_findings.md`), then
> after Codex rounds 1, 2, and 3 plan-audits. 14 → 20
> workstreams; W-S, W-F, W-B extended; W-V split into W-Va
> (early, blocker-class) + W-Vb (late, deferrable with W-Z +
> demo-gate degradation paths); W-W gained row-level JSONL
> consistency contract; W-X gained `Probe` protocol split for
> live vs fixture-stub probes; demo archive moved outside real
> `~/.health_agent` tree with resolved-path guard. Estimate:
> 22-30 days (~50-100% on the original 15-20).
>
> **Release-blocker class** (cycle cannot ship without all three):
> **W-E**, **W-F**, **W-Va**. W-Va added because half-broken demo
> isolation actively pollutes real user state — worse than no demo
> mode.
>
> **Source.** Tactical plan §2 (companion). Pulls deferred items
> from v0.1.10 + v0.1.9 backlog + targeted new infrastructure work
> + 2026-04-28 demo-run findings + 2026-04-28 Codex plan-audit
> revisions.
>
> **Cycle pattern (revised — D14 candidate).** Promoted to a named
> pre-cycle gate, with an explicit **pre-implementation gate after
> Phase 0** so Phase 0 findings can revise or abort scope before
> code lands. Sequence:
>
> 1. **PLAN.md draft authored** (this file).
> 2. **Codex plan-audit** → `codex_plan_audit_response.md`.
> 3. **Maintainer response + PLAN.md revisions** (one or more
>    rounds until Codex returns `PLAN_COHERENT`).
> 4. **Phase 0 (D11) pre-PLAN bug-hunt opens.** Internal sweep +
>    audit-chain probe + persona matrix + Codex external bug-hunt
>    in parallel; findings consolidate to `audit_findings.md`.
>    Each finding is tagged
>    `cycle_impact: "in-scope" | "revises-scope" | "aborts-cycle"`.
> 5. **Pre-implementation gate.** Maintainer reads
>    `audit_findings.md`. If `revises-scope` findings warrant a
>    PLAN.md revision OR `aborts-cycle` findings warrant abandoning
>    the cycle, the gate fires. Otherwise the cycle opens for
>    implementation.
> 6. **Implementation rounds** with Codex round 1 / round 2 reviews
>    until verdict is SHIP or SHIP_WITH_NOTES.
> 7. **RELEASE_PROOF.md + REPORT.md.**
>
> Steps 2 + 3 are the new D14 gate. Step 5 is the D11 gate, made
> explicit per Codex F-PLAN-01.

---

## 1. What this release ships

v0.1.11 closes every workstream v0.1.10 deferred, expands the
persona matrix from 8 → 12, introduces property-based testing
for the policy DSL, and absorbs all 7 demo-run findings from
2026-04-28. End-state: every named finding from
`v0_1_10/audit_findings.md` and the demo-run findings is either
fixed or formally deferred to v0.2+ with named-defer gate.

### 1.1 Workstream catalogue

| W-id | Title | Severity | Files (primary) | Source |
|---|---|---|---|---|
| **W-B** | R-volume-spike minimum-coverage gate | band-miscalibration | `core/synthesis_policy.py`, `domains/strength/policy.py`, `core/config.py` | F-C-04, B2 (memory) |
| **W-E** | `hai daily` re-run state-change supersession | audit-chain-break | `core/synthesis.py`, `cli.py` daily handler | F-B-02, B7 (memory) |
| **W-F** | Audit-chain version-counter integrity | audit-chain-break | `core/synthesis.py` supersession path | F-B-01 |
| **W-H1** | Mypy correctness-class fixes | correctness | `cli.py`, `core/synthesis.py`, `evals/runner.py`, `core/state/runtime_event_log.py`, `core/state/projector.py`, `core/doctor/checks.py` | F-A-03, F-A-04, F-A-05, F-A-06, F-A-07, F-A-11 |
| **W-K** | Bandit B608 site-by-site verdict | security review | 8 files (16 sites) | F-A-13 |
| **W-L** | Bandit B310 url-scheme audit | security | `core/pull/intervals_icu.py:310` | F-A-14 |
| **W-N** | Pytest unraisable warning cleanup | nit | `safety/tests/test_snapshot_bundle.py` | v0.1.9 backlog |
| **W-O** | Persona matrix expansion (8 → 12) | infrastructure | `verification/dogfood/personas/p9-p12_*.py` | NEW |
| **W-P** | Property-based tests for policy DSL | testing infrastructure | `verification/tests/test_policy_dsl_invariants.py` | NEW |
| **W-Q** | F-B-03 review-schedule auto-run investigation | audit-chain integrity (investigative) | `cli.py` daily handler, `core/review/outcomes.py` | F-B-03 |
| **W-R** | F-C-03 / F-CDX-IR-05 — running-rollup provenance + completeness | correctness polish | `cli.py` clean handler, `core/state/projector.py` | v0.1.10 W-D-ext follow-up + Codex round 1 |
| **W-S** | F-CDX-IR-06 — persona harness drift guards | testing infrastructure | `verification/dogfood/synthetic_skill.py`, new contract test | Codex round 1 |
| **W-T** | F-CDX-IR-R3-N1 — in-memory threshold injection seam audit | trusted-seam audit | `core/config.py`, every `evaluate_*` / classify / policy entry point | Codex round 3 |
| **W-Va** | S-DEMO-01 — `hai demo` mode core: marker, fail-closed resolver, base-dir + DB + config isolation, refusal matrix, banner. **Release-blocker class.** | demo isolation / state safety | `cli.py`, `core/demo/*` (new), DB + base-dir + config resolvers, `core/credentials.py`, `core/capabilities/walker.py` | demo run 2026-04-28 + Codex round 1 |
| **W-Vb** | S-DEMO-01 follow-on: persona fixture loading, archive policy, cleanup polish, `hai demo end --archive` behaviour. **Deferrable to v0.1.12 with named-defer gate.** | demo polish / dogfood UX | `core/demo/fixtures.py` (new), `verification/dogfood/personas/__init__.py` | demo run 2026-04-28 |
| **W-W** | F-DEMO-04 — `hai intake gaps` state-snapshot fallback mode (with single-read-transaction consistency contract) | session-start protocol resilience | `cli.py`, `core/intake/gaps.py`, `core/config.py`, `core/capabilities/walker.py` | demo run 2026-04-28 + Codex round 1 |
| **W-X** | F-DEMO-01 — `hai doctor` probe extension for live-API auth check | diagnostic-trust | `core/doctor/checks.py`, `cli.py` doctor handler, `core/capabilities/walker.py` | demo run 2026-04-28 |
| **W-Y** | F-DEMO-03 — CLI civil-date flag harmonisation (`--as-of` canonical alias on `pull` + `explain`) | UX polish | `cli.py` (pull, explain handlers), `core/capabilities/walker.py` | demo run 2026-04-28 |
| **W-Z** | S-DEMO-02 — Demo-flow guide doc. **Requires W-Va. W-Vb required only for § A (full persona flow); § B (blank-demo flow) ships as canonical if W-Vb defers.** | doc-only | `reporting/docs/demo_flow.md` (new) | demo run 2026-04-28 |

**Plus extensions to existing workstreams:**

- **W-S extended** to include F-DEMO-02 (proposal schemas + per-domain action enums exposed via `hai capabilities --json`). W-S already pulls from `ALLOWED_ACTIONS_BY_DOMAIN` for the persona harness drift guards; the additive manifest emit fits the same primitive.
- **W-F extended** to include F-DEMO-05 (orphan `_v2` plan from `--supersede` on a fresh day). Same counter-integrity issue, same code path; the state-fingerprint primitive being added in W-E incidentally fixes it.

### 1.2 Out-of-scope (deferred)

| Item | Why deferred |
|---|---|
| **W-H2** mypy stylistic fixes (Literal abuse, redefinition, scenario type confusion) | v0.1.12 scope per tactical plan — different class than W-H1 correctness |
| **F-B-04** domain-coverage drift across supersession | Semantic question, needs design discussion; v0.1.12 |
| **F-C-05** strength_status enum surfaceability | Capabilities-manifest extension; bundled with v0.1.12 alongside W-S follow-on work |
| **F-C-06** persona matrix elevated-stress coverage | Rolled into W-O (persona expansion includes elevated-stress P11) |
| **W52 / W53 / W58** | v0.2.0 wave per strategic plan |

---

## 2. Per-workstream contract

### 2.1 W-B — R-volume-spike minimum-coverage gate

**Goal.** Stop R-volume-spike escalating for users with regular but
sparse strength training. Confirmed across 6 personas in v0.1.10
and Dom's real state in the 2026-04-28 demo run (volume_ratio=4.0
on 2 sessions / 28d).

**Approach.**
- Add `r_volume_spike_min_sessions_last_28d` threshold to the rule.
  Default `8` (≥2 sessions/week sustained).
- **D12 compliance (per Codex F-PLAN-10).** Resolve the threshold
  via `core.config.coerce_int` at every consumer site. Bool-shaped
  numeric input (`true` / `false`) must reject. This is the same
  bool-as-int class v0.1.10 hardened against; new threshold without
  the coercer would re-open it.
- Below threshold → rule emits `coverage_band: 'insufficient'`
  rather than firing as spike.
- Rule firing path checks gate first; classification stays as-is.

**Files:**
- `src/health_agent_infra/core/synthesis_policy.py` — X-rule body
  (uses `coerce_int`).
- `src/health_agent_infra/domains/strength/policy.py` — R-rule body
  if it shares the trigger (uses `coerce_int`).
- `src/health_agent_infra/core/config.py` — DEFAULT_THRESHOLDS new
  entry; document the coercer requirement inline.

**Tests:**
- `verification/tests/test_xrule_volume_spike_coverage.py` (new) —
  boundary tests around `min_sessions_last_28d` at 7, 8, 9
  sessions.
- `verification/tests/test_xrule_volume_spike_coercer.py` (new) —
  user override of `true` / `false` rejected as a numeric
  threshold; mirrors the v0.1.10 pattern.
- Persona matrix re-run shows P1, P4, P5, P6, P7 stop escalating
  on regular training pattern (current 6 personas escalate; target
  ≤ 1).
- Demo-data fixture: replay the 2026-04-28 case
  (sessions_last_28d=2, sessions_last_7d=2, volume_ratio=4.0,
  subjective signals favourable) — assert post-fix outcome is
  `coverage_band: 'insufficient'` rather than escalate.

**Acceptance:**
- Persona harness findings drop from 3 → ≤ 1.
- New unit tests cover boundary at 7, 8, 9 sessions.
- Bool-as-int rejection test green.
- DEFAULT_THRESHOLDS gains `r_volume_spike_min_sessions_last_28d`
  with documented rationale + coercer requirement.

### 2.2 W-E — `hai daily` re-run state-change supersession

**Goal.** When `hai daily` is re-run on the same date and state
materially differs, produce a superseded `_v<N>` plan with refreshed
rationale prose.

**Approach.**
- `core/synthesis.py` computes a state fingerprint (hash of
  nutrition_intake, readiness, gym intake, clean-evidence row,
  manual readiness/stress) before synthesis.
- If a canonical plan already exists for `(for_date, user_id)`,
  compare its captured fingerprint to current.
- Match → no-op (correct idempotent behaviour).
- Mismatch → produce `_v<N>` supersession with fresh proposal_log
  rows + regenerated rationale prose.

**Schema:** add `state_fingerprint` column to `daily_plan` table
(nullable, populated from v0.1.11 forward; backfilled to NULL for
existing rows). Add migration `NNN_daily_plan_state_fingerprint.sql`.

**Files:**
- `core/synthesis.py` — fingerprint computation + comparison.
- `cli.py` — daily handler invocation surface.
- `core/state/migrations/NNN_*.sql` — new migration.
- `core/schemas.py` — DailyPlan dataclass field.

**Tests:**
- `verification/tests/test_daily_supersede_on_state_change.py`
  (new) — reproduces v0.1.10 morning-briefing scenario.
- Migration round-trip test.

**Acceptance:**
- Reproduce: log nutrition A → daily → log nutrition B (replace) →
  daily again → observe `_v2` plan id with fresh prose.
- Idempotent re-run with no state change is a true no-op (no new
  plan_id, no new proposal_log rows).

### 2.3 W-F — Audit-chain version-counter integrity

**Goal.** Eliminate `_v3` jumps from `_v0` (skipped `_v2`) observed
in F-B-01. Plus: handle `--supersede` on a fresh day correctly so it
does not produce an orphan `_v2` row when no canonical `_v1` exists
(F-DEMO-05).

**Approach.**
1. Investigate root cause first. Hypothesis: counter increments on
   attempt, not on commit.
2. Audit `core/synthesis.py` supersession path.
3. Fix: counter increments only after successful commit of the
   superseding row.
4. Regression test: contrived re-synthesise loop with rollback in
   the middle MUST NOT advance the version counter.
5. **F-DEMO-05 fold-in (contract concretised per Codex F-PLAN-09
   round 1, maintainer answer Q-A: option b).** When
   `--supersede` is passed but no canonical plan exists for
   `(for_date, user_id)`, **exit USER_INPUT** with a clear error
   message: `"--supersede requires an existing canonical plan for
   <for_date>/<user_id>; none found. Re-run without --supersede
   to write the first-version plan."` No write, no plan id
   minted. Aligns with audit-chain-integrity thesis: explicit
   contract violations beat silent behaviour drift.
6. **Cleanup pass.** Document the existing orphan
   `plan_2026-04-28_u_local_1_v2` row and either supersede-archive
   it under the new canonical or leave a code comment explaining
   why it was left in place.

**Files:**
- `core/synthesis.py` supersession version-increment path.
- `cli.py` daily handler `--supersede` branch (pre-flight canonical-
  exists check).

**Tests:**
- `verification/tests/test_supersede_version_counter.py` (new) —
  sequential version assertion + rollback-isolation assertion.
- `verification/tests/test_supersede_on_fresh_day.py` (new, F-DEMO-05)
  — reproduces the demo scenario: `--supersede` on a date with no
  canonical plan → asserts the command exits USER_INPUT with the
  prescribed error message and that **no write** occurs (no row
  in `daily_plan`, no row in `proposal_log`, no JSONL append).

**Acceptance:**
- No skipped versions in any chain post-fix.
- Audit-chain probe (manual `hai explain --plan-version all` walk)
  passes for every recent date.
- `--supersede` on a fresh day exits USER_INPUT with the prescribed
  error and never produces an unreachable `_v2`.

### 2.4 W-H1 — Mypy correctness-class fixes

**Goal.** Address the six mypy errors flagged correctness in
`v0_1_10/audit_findings.md` Phase A.

**Per-finding:**
- **F-A-03** `cli.py:204, 4389` adapter type confusion → fix the
  assignment type using a Protocol or union.
- **F-A-04** `synthesis.py:373` `dict|None` assigned to non-None
  typed var → narrow the type or guard None.
- **F-A-05** `evals/runner.py:668-669` scenario type confusion →
  fix the type annotations OR fix the runtime path if mis-typed.
- **F-A-06** `cli.py:4075, 4083` None-comparison operators → guard.
- **F-A-07** `cli.py:2957-2963` exercise None-into-required-str →
  argparse-required validation OR explicit None guard.
- **F-A-11** `core/state/runtime_event_log.py:54` int-of-Optional
  pattern (4 sites total: state/projector.py:302, 2219;
  doctor/checks.py:276) → guard.

**Tests:** existing tests stay green; add boundary tests for any
None path that wasn't previously exercised.

**Acceptance:**
- mypy default pass: 0 correctness-class errors.
- Stylistic-class errors (~10 remaining) deferred to v0.1.12 W-H2.

### 2.5 W-K — Bandit B608 site-by-site verdict

**Goal.** Per-site determination on each of 16 SQL string-construction
findings from `v0_1_10/audit_findings.md` F-A-13.

**Approach.** For each site:
1. Read the call site.
2. Verify the dynamic part is column-whitelisted from a constant tuple
   (the placeholder-templating IN-clause pattern is safe).
3. Add `# nosec B608  # reason: <specific>` comment.
4. If a site is genuinely unsafe, refactor.

**Files (16 sites):**
```
core/explain/queries.py:452, 572, 585
core/intent/store.py:239, 402
core/memory/store.py:208
core/state/projector.py:390, 617
core/state/projectors/running_activity.py:151, 162
core/state/snapshot.py:97, 348, 352
core/target/store.py:219, 360
evals/runner.py:514
```

**Acceptance:** bandit -ll on `src/`: 0 unsuppressed B608.

### 2.6 W-L — Bandit B310 url-scheme audit

**Goal.** Confirm `core/pull/intervals_icu.py:310` URL is fully
constant + does not accept user input.

**Approach.** Read the call site. If safe, document with
`# nosec B310 # reason: <specific>`. If user input contributes,
restrict via `urllib.parse.urlparse` allowed-schemes check.

**Acceptance:** bandit -ll on `src/`: 0 unsuppressed of any kind.

### 2.7 W-N — Pytest unraisable warning cleanup (narrowed)

**Goal.** `verification/tests` runs clean under
`-W error::pytest.PytestUnraisableExceptionWarning`.

**Scope-narrowing note (cycle-internal, 2026-04-28).** The original
v0.1.9 backlog targeted a single test file (referenced as
`safety/tests/test_snapshot_bundle.py` — a path that does not
exist in the current tree; the file lives at
`verification/tests/test_snapshot_bundle.py`). The original draft
acceptance was the catch-all `-W error::Warning`, which a tree-
wide audit revealed surfaces 47 unrelated `ResourceWarning`
failures rooted in unclosed `sqlite3.Connection` and HTTP-response
patterns scattered across the codebase. That broader cleanup is a
multi-day systemic refactor (context-managed `open_connection`
helper + audit of every CLI handler), not a 30-min smoke-clearer.

**v0.1.11 W-N ships the narrow gate.** The broader
`-W error::Warning` cleanup is deferred to v0.1.12 as a new
workstream candidate (call it `W-N-broad` when scoped); see
demo-run-findings § 7 follow-up.

**Approach.** Confirm the suite passes
`-W error::pytest.PytestUnraisableExceptionWarning`. If a regression
appears mid-cycle, fix the offending site (likely an HTTP-client
lifecycle in `core/pull/intervals_icu.py` if intervals.icu probe
work in W-X surfaces it).

**Acceptance:**
- `uv run pytest verification/tests -W error::pytest.PytestUnraisableExceptionWarning` exits 0.
- Top-level § 3 ship gate updated to reference the narrow form
  rather than the catch-all (see § 3 update below).

### 2.8 W-O — Persona matrix expansion (8 → 12)

**Goal.** Add four personas to fill matrix gaps.

**New personas:**

| ID | Persona | Why |
|---|---|---|
| **P9** | Older female endurance (52F, 60kg, 165cm, masters runner, 12mo Garmin history) | Female + age-50+ + endurance — none of the above in current matrix |
| **P10** | Adolescent recreational (17M, 65kg, 170cm, casual sport, 6mo) | Below-spec age band. Tests graceful failure or out-of-supported-set surface. |
| **P11** | Elevated-stress hybrid (28M, 78kg, 178cm, persistent elevated stress + body-battery low) | F-C-06 — current matrix is uniform low-stress. Need persona stressing the stress domain. |
| **P12** | Vacation-returner (35F, 65kg, 168cm, 14d gap then back to baseline) | Comeback-from-gap edge. Tests classifier behaviour after data discontinuity. |

**Files:**
- `verification/dogfood/personas/p9_older_female_endurance.py`
- `verification/dogfood/personas/p10_adolescent_recreational.py`
- `verification/dogfood/personas/p11_elevated_stress_hybrid.py`
- `verification/dogfood/personas/p12_vacation_returner.py`
- `verification/dogfood/personas/__init__.py` updated `ALL_PERSONAS`.

**Acceptance:**
- All 12 personas run cleanly through the harness.
- P10's expected behaviour explicitly documented (likely defer
  everything OR explicit "out of supported user set" surface).
- P11 surfaces stress-domain `elevated` band → stress action
  `schedule_decompression_time` or equivalent.

### 2.9 W-P — Property-based tests for policy DSL

**Goal.** Hypothesis-based tests asserting policy-DSL invariants
across ranges of inputs.

**Invariants:**
- For all classified_state inputs in valid ranges,
  `evaluate_<domain>_policy` returns a result whose
  `forced_action` (if not None) is in the domain's action enum.
- For all proposal inputs, `apply_phase_a` returns `mutated` with
  `action` in the domain's action enum.
- For all snapshots, X-rule `recommended_mutation.action` (when
  present) is in the target domain's enum.

**Files:**
- `verification/tests/test_policy_dsl_invariants.py` (new).

**Acceptance:**
- Hypothesis-based tests pass on all 6 domains' policy entry points.
- Any failing case = fix-now scope (likely surfaces a real bug or a
  miscoded enum).

### 2.10 W-Q — F-B-03 review-schedule auto-run investigation

**Goal.** Determine whether 2026-04-25 + 2026-04-26 missing reviews
is regression, intended-manual, or bug.

**Approach.** Read `cli.py` daily handler review-schedule path.
Read `core/review/outcomes.py` schedule entry. Trace whether
`hai daily` auto-schedules reviews unconditionally, or only when
flags align.

**Acceptance:**
- Verdict documented in cycle response.
- If regression: fix + regression test.
- If intended-manual: doc update + UX surface (`hai today` mentions
  review schedule status).

### 2.11 W-R — F-C-03 / F-CDX-IR-05 — running-rollup provenance + completeness

**Goal.** Decide whether `aggregate_activities_to_daily_rollup`
output's `session_count` and `total_duration_s` should populate
`accepted_running_state_daily` (currently hardcoded None per v1
contract per `state_model_v1.md §8`); fix the `derivation_path`
provenance string to distinguish activity-rollup origins from
true `garmin_daily` origins.

**Approach.**
1. Read `state_model_v1.md §8` to understand original intent.
2. Decide: extend v1 contract (populate these fields) OR keep
   intentional NULL.
3. If populating: update projector + tests.
4. If keeping NULL: document the reason explicitly + update
   `state_model_v1.md`.
5. Fix `derivation_path` so rows derived via
   `aggregate_activities_to_daily_rollup` stamp a distinct enum
   value (e.g. `activity_rollup`); rows pulled directly from
   `/wellness.json` keep `garmin_daily` (or `intervals_icu_wellness`).

**Acceptance:**
- Explicit decision documented; if populating, test coverage for
  both fields.
- A new `verification/tests/test_running_provenance.py` asserts
  that personas P2 and P7 (with logged activities) produce rows
  whose `derivation_path` reflects the rollup origin.

### 2.12 W-S — F-CDX-IR-06 persona harness drift guards (+ F-DEMO-02)

**Goal.** Replace hardcoded action-token + schema-version
mappings in `verification/dogfood/synthetic_skill.py` with imports
from the runtime contract, and add a contract test that catches
drift directly rather than via downstream `hai propose` failure.

**Plus (F-DEMO-02 fold-in):** expose the same per-domain proposal
contracts via `hai capabilities --json` so agents composing
proposals from scratch don't need to grep `schemas.py` or mimic
prior `*_proposals.jsonl` rows. Same primitive
(`ALLOWED_ACTIONS_BY_DOMAIN` + proposal schema registry), two
consumers (harness + capabilities manifest).

**Approach.**
1. Replace `_DOMAIN_DEFAULT_ACTION` and `_STATUS_TO_ACTION`
   constants with values pulled from
   `core/validate.ALLOWED_ACTIONS_BY_DOMAIN` plus the proposal
   schema registry.
2. Replace `f"{domain}_proposal.v1"` with the actual schema-version
   constant from the validator module.
3. Add `verification/tests/test_persona_harness_contract.py`
   asserting:
   - Every domain in `ALLOWED_ACTIONS_BY_DOMAIN` appears in the
     harness's status mapping.
   - Every status the harness emits is a valid action for its
     domain.
   - The schema versions match the runtime registry.
4. **F-DEMO-02 fold-in.** Extend `hai capabilities --json` output
   with a new `domain_proposal_contracts` top-level block:
   ```json
   {
     "domain_proposal_contracts": {
       "<domain>": {
         "schema_version": "<domain>_proposal.v1",
         "action_enum": [...],
         "required_fields": [...]
       }
     }
   }
   ```
   Sourced from the same primitive as step 1. Pure read-side, no
   behaviour change. Backwards-compatible additive; does not freeze
   the manifest schema (W30 settled decision still holds).
5. Add `verification/tests/test_capabilities_proposal_contracts.py`
   asserting every domain in `ALLOWED_ACTIONS_BY_DOMAIN` appears in
   the manifest with matching action enum + schema version.

**Files (corrected per Codex F-PLAN-07; the previous draft cited
the non-existent `core/cli/capabilities.py`):**
- `verification/dogfood/synthetic_skill.py` — drift-guard imports.
- `src/health_agent_infra/core/capabilities/walker.py` — top-level
  `domain_proposal_contracts` emission.
- `src/health_agent_infra/core/capabilities/render.py` — markdown
  representation if the generated doc should mention top-level
  blocks.
- `verification/tests/test_persona_harness_contract.py` (new).
- `verification/tests/test_capabilities_proposal_contracts.py`
  (new).
- `reporting/docs/agent_cli_contract.md` — regenerated from the
  manifest.
- `reporting/docs/agent_integration.md` — touched if it references
  the manifest shape.

**Acceptance (per Codex F-PLAN-07 ship-gate reword):**
- Harness no longer hardcodes runtime contract values.
- Contract test catches a deliberate mutation in either direction
  (proposal schema version bump, action token rename).
- Persona harness re-run produces the same matrix as v0.1.10.
- `hai capabilities --json | jq '.domain_proposal_contracts'`
  emits all 6 domains with action enums + schema versions.
- **Manifest JSON and regenerated markdown are deterministic
  across runs (same source state → byte-identical output).
  Expected additive rows/fields are present and pass their
  per-W-id capabilities tests:**
  - W-S: `domain_proposal_contracts` top-level block.
  - W-Va: `hai demo start / end / cleanup` rows.
  - W-W: `--from-state-snapshot` + `--allow-stale-snapshot` flags
    on `hai intake gaps`.
  - W-X: `--deep` flag on `hai doctor`; `auth_*.probe` field on
    auth-row schema.
  - W-Y: `--as-of` aliases on `hai pull` + `hai explain`.

  **No frozen-schema check** — W30's "manifest schema not yet
  frozen" decision is preserved; the gate verifies presence of
  expected additive content + determinism, not closure of the
  schema (per Codex F-PLAN-R2-05).

### 2.13 W-T — F-CDX-IR-R3-N1 in-memory threshold injection audit

**Goal.** Resolve the trusted-seam concern Codex round 3 raised
(`SHIP_WITH_NOTES` note 1). `load_thresholds()` validates the
user-TOML boundary, but every `evaluate_*` / classify / policy
entry point accepts a `thresholds: Optional[dict]` argument that
bypasses `_validate_threshold_types` when a caller constructs the
dict in-memory.

**Approach.**

1. Audit every call site that passes a non-`None` `thresholds`
   argument. Categorise: production flow (transitively
   validated), test (trusted by design), other.
2. If only production + test callers exist (the likely outcome),
   document the seam explicitly in:
   - `core/config.py` module docstring.
   - The docstring of every `evaluate_*` / classify / policy
     entry point that accepts the arg.
   - `AGENTS.md` "Settled Decisions" as D13 so the trust
     boundary is load-bearing knowledge.
3. If a non-test, non-production-flow caller exists, choose:
   - Extend `_validate_threshold_types` to support partial
     defaults so it can run at every internal entry point; OR
   - Wrap each entry point with a load-or-pass-through helper.

**Acceptance:**
- Audit summary in `v0_1_11/W_T_audit.md` enumerates every call
  site + its category.
- If documentation-only outcome: AGENTS.md D13 added; module +
  function docstrings updated.
- If extended-validation outcome: validator handles partial
  defaults; new tests cover bool-on-numeric rejection through
  every entry point.
- No regression in existing 2202 + new tests.

### 2.14 W-Va — `hai demo` mode core: marker, fail-closed resolver, isolation, refusal

**Release-blocker class** (per maintainer answer Q-B). Half-broken
demo isolation actively pollutes real user state — strictly worse
than no demo mode. Cycle cannot ship without W-Va.

**Goal.** A first-class demo workflow that **provably** does not
touch real persistence surfaces. Source: S-DEMO-01 from the demo-
run findings, plus Codex F-PLAN-02 (base_dir isolation), F-PLAN-03
(fail-closed marker), F-PLAN-04 (early sequencing), F-PLAN-05
(resize).

**Approach.**

1. **New `hai demo` subcommand group:**
   - `hai demo start [--persona <name>] [--blank]` — opens a demo
     session. Creates a scratch root at
     `/tmp/hai_demo_<timestamp>/` containing
     `state.db`, `health_agent_root/` (the equivalent of the real
     `~/.health_agent` tree), and `config/thresholds.toml` (a
     copied or fixture-supplied override). Writes a marker file
     at `~/.health_agent/demo_session.json` containing:
     `{schema_version: "demo_marker.v1", marker_id, db_path,
     base_dir_path, config_path, persona, started_at}`.
     **Persona fixture loading is W-Vb scope** — W-Va opens an
     empty scratch session if no W-Vb is loaded, with a clear
     stderr note that the session is unpopulated.
   - `hai demo end` — closes the active session. Removes the
     marker. **Archive behaviour is W-Vb scope.**
   - `hai demo cleanup` — finds and removes any stale demo
     directories and orphan markers. Safety net.
2. **Multi-resolver override (per Codex F-PLAN-02).** Every CLI
   command checks for the marker at startup. If present **and
   valid**, the resolvers return scratch paths instead of real
   paths:
   - `resolve_db_path()` → scratch `state.db`.
   - `resolve_base_dir()` → scratch `health_agent_root/`.
   - Config resolver (the helper that loads `thresholds.toml`)
     → scratch `config/thresholds.toml` (per maintainer answer
     Q-C: config writes are isolated; keyring stays refused; skill
     install dir is install-time-only and not isolated).
   - Any other persistence-root resolver discovered during
     implementation gets enumerated in
     `verification/tests/test_demo_isolation_surfaces.py` and
     routed through the marker.
3. **Fail-closed marker (per Codex F-PLAN-03).** If the marker
   file exists but **any** of the following hold, every CLI
   command **except** `hai demo end` and `hai demo cleanup`
   exits USER_INPUT with a clear error and **does not touch real
   state**:
   - File parse failure (corrupt JSON).
   - Missing required fields (`db_path`, `base_dir_path`,
     `config_path`, `marker_id`).
   - Schema-version mismatch.
   - `db_path` or `base_dir_path` points at a missing path.
   - Marker is older than the cleanup-suggest threshold AND the
     scratch surfaces are missing (stale-orphan shape).
4. **Refusal matrix.** In demo mode, commands fall into four
   buckets (full table per Codex F-PLAN-03):

   | Behaviour | Commands |
   |---|---|
   | Allowed (against scratch state) | `hai today`, `hai daily --skip-pull --source csv`, `hai propose`, `hai intake *`, `hai explain`, `hai state read/snapshot`, `hai memory *`, `hai intent list`, `hai target list`, `hai stats`, `hai capabilities`, `hai doctor` (no flag), **`hai doctor --deep`** (per Q-3: routed to fixture-stub probe; live network forbidden), `hai demo *` |
   | Refused — live network | `hai pull --source intervals_icu`, `hai pull --source garmin_live`, `hai pull --live`, `hai daily --source intervals_icu`, `hai daily --source garmin_live`, `hai daily --live` |
   | Refused — credentials/keyring | `hai auth garmin`, `hai auth intervals-icu`, `hai init --with-auth`, `hai init --with-first-pull` |
   | Refused — operator/installer | `hai state init/migrate/reproject`, `hai setup-skills`, `hai config init`, `hai intent commit/archive`, `hai target commit/archive` |
   | Cleanup-only (still allowed when marker is invalid) | `hai demo end`, `hai demo cleanup` |

   **`hai doctor --deep` exception (per Q-3 / F-PLAN-R2-03).**
   In demo mode, the probe surface is a fixture-backed stub, not
   the live API. The probe response is supplied by the persona
   fixture (or the `--blank` session's default stub). A hard
   no-network assertion guards the demo path: any attempt to
   open a real network connection from `--deep` while a demo
   marker is active fails the test suite. This preserves the
   diagnostic-trust demo moment (showing how `--deep` catches a
   403 against a stubbed credential surface) without leaking
   network calls.

5. **Stderr banner** on every CLI invocation in demo mode (when
   the marker is valid):
   ```
   [demo session active — marker_id <id>, scratch root /tmp/hai_demo_<ts>/,
    persona: <name|"unpopulated">, started: 2026-04-28T13:00Z]
   ```
6. **Stale-session surfacing (no auto-delete).** On every CLI
   invocation, if `started_at` is more than 24h old, surface a
   one-line stderr note: `stale demo session — run 'hai demo
   end' or 'hai demo cleanup' to clear`. The user remains in
   demo mode (the marker is still authoritative); no real state
   is touched.

**Files (new + edits):**
- `cli.py` — `hai demo` subcommand handlers (start, end,
  cleanup); stderr banner injection; demo-mode refusal enforcement
  per the matrix; pull-source / auth / operator-command guards.
- `core/demo/session.py` (new) — marker schema (`demo_marker.v1`),
  parse + validate + fail-closed helpers, lifecycle (start /
  end / cleanup), scratch root provisioning.
- `core/demo/resolver.py` (new, OR extend the existing path
  resolver helpers) — multi-surface resolver override gated on
  the marker.
- `core/credentials.py` (or wherever the keyring helper lives —
  enumerate during implementation; **NOT** `core/auth/*.py`,
  which does not exist; corrected per Codex F-PLAN-03) — refuse
  mutations when marker is valid.
- `core/capabilities/walker.py` (per Codex F-PLAN-07; **NOT**
  `core/cli/capabilities.py` which does not exist) — emit
  `hai demo start / end / cleanup` rows + flag enumeration.
- `core/capabilities/render.py` — markdown regeneration.
- `reporting/docs/agent_cli_contract.md` — regenerated.

**Tests:**
- `verification/tests/test_demo_session_lifecycle.py` (new) —
  start → use → end happy path; marker created/removed;
  scratch root provisioned; banner on stderr.
- `verification/tests/test_demo_isolation_surfaces.py` (new, per
  Codex F-PLAN-02) — run `hai intake nutrition`, `hai propose`,
  `hai review schedule`, `hai daily` in demo mode; assert
  byte-for-byte stability of: real `state.db` checksum, real
  `~/.health_agent` tree (recursive checksum), real
  `thresholds.toml`, real keyring (introspection that no key
  was added/changed/deleted).
- `verification/tests/test_demo_marker_fail_closed.py` (new,
  per Codex F-PLAN-03) — corrupt JSON → refusal; missing
  required field → refusal; schema-version mismatch → refusal;
  `db_path` points at missing file → refusal; `hai demo end`
  and `hai demo cleanup` still allowed under each failure.
- `verification/tests/test_demo_refusal_matrix.py` (new) —
  exhaustively walk every command in the refusal matrix; assert
  the prescribed behaviour.
- `verification/tests/test_demo_capabilities_emission.py` (new)
  — assert `hai capabilities --json` emits `hai demo *` rows
  with correct mutation classifications and that the manifest
  regenerator produces deterministic output.

**Acceptance:**
- `hai demo start` opens an isolated session; real DB +
  `~/.health_agent` tree + `thresholds.toml` checksums stable
  across every command in the allowed bucket.
- Refusal matrix tests green for all four buckets.
- Fail-closed tests green: corrupt marker → no real state
  touched, every command except cleanup exits USER_INPUT.
- Banner visible on every demo-mode invocation.
- Capabilities manifest correctly enumerates the new commands.

**Sequencing.** **Lands at item #5 (after the smoke-clearers
W-N, W-L, W-K, W-Q).** All later workstreams compose against the
multi-resolver override from the start. Per Codex F-PLAN-04 — the
"early seam" claim is now matched by the actual sequencing.

### 2.15 W-Vb — `hai demo` polish: persona fixtures + archive + cleanup polish

**Deferrable to v0.1.12 with named-defer ship gate** (per
maintainer answer Q-B). If the cycle runs hot OR W-P property
tests surface >3 correctness-class findings, defer W-Vb;
W-Va alone is sufficient to ship the safe demo mode.

**Goal.** Ergonomic completion of the `hai demo` workflow:
persona-pre-populated scratch sessions, archive-on-end behaviour,
stale-session policy refinement.

**Approach.**

1. **Persona fixture loading.** `hai demo start --persona <name>`
   reads `verification/dogfood/personas/<persona>.py`'s
   `build_demo_fixture()` function and pre-populates the scratch
   root with 14d of evidence + manual intakes + history. Default
   persona on `hai demo start` (no flag) is `p1_endurance_runner`.
   `--blank` opt-out for an empty session.
2. **Persona fixture contract.** Every persona in
   `verification/dogfood/personas/__init__.py::ALL_PERSONAS`
   exposes a `build_demo_fixture(scratch_root: Path) -> None`
   function. v0.1.10 personas P1-P8 plus W-O's P9-P12 all
   conform.
3. **Archive on `hai demo end` (per maintainer answer Q-2 of
   plan-audit round 2; resolved-path guard per Codex
   F-PLAN-R3-02).** When ended, scratch root is archived to a
   path **outside the real `~/.health_agent` tree**.
   Resolution order:
   1. If `XDG_CACHE_HOME` is set:
      `$XDG_CACHE_HOME/hai/demo_archives/<marker_id>__<persona>__<ended_at>/`.
   2. Else: `/tmp/hai_demo_archives/<marker_id>__<persona>__<ended_at>/`.

   **Resolved-path guard.** After resolving the archive root,
   compute its real path (resolving symlinks) and assert it is
   **not** under the real base dir's real path. If the resolved
   archive root would land under the real tree (e.g., a user has
   set `XDG_CACHE_HOME=~/.health_agent/cache`), fall back to
   `/tmp/hai_demo_archives/...`. If the `/tmp` fallback also
   fails the guard (e.g., `/tmp` symlinks under the real tree on
   an exotic system), exit USER_INPUT with a clear error rather
   than archiving inside the real tree. The guard runs at every
   `hai demo end` invocation that writes an archive; not a
   one-time check.

   Removed entirely if `--no-archive` is passed. Archive
   directory has a configurable rotation policy
   (`thresholds.toml::demo.archive_max_count`, default 10).
   **Real `~/.health_agent` is never mutated by demo mode under
   any configuration** — the resolved-path guard is the load-
   bearing assertion for that invariant.
4. **Cleanup polish.** `hai demo cleanup` enumerates orphan
   archives + stale scratch roots; reports each with size, age,
   marker-id; prompts for confirmation before deletion.

**Files:**
- `core/demo/fixtures.py` (new) — persona → scratch root
  pre-population helper.
- `verification/dogfood/personas/__init__.py` — expose
  `ALL_PERSONAS` to the fixture loader.
- Each `verification/dogfood/personas/p<N>_*.py` — gain
  `build_demo_fixture()` if not already present (some may
  already have an equivalent helper from W-O groundwork).
- `core/demo/session.py` — extend with archive-on-end logic.
- `core/config.py` — `demo.archive_max_count` threshold (use
  `core.config.coerce_int` per D12).

**Tests:**
- `verification/tests/test_demo_persona_fixtures.py` (new) —
  every persona in `ALL_PERSONAS` loads cleanly; `hai today`
  succeeds against the freshly-populated scratch root.
- `verification/tests/test_demo_archive.py` (new) — archive
  on end happy path; `--no-archive` skips; rotation policy
  enforced.
- `verification/tests/test_demo_archive_path_guard.py` (new, per
  Codex F-PLAN-R3-02) — `XDG_CACHE_HOME` set to a path under
  the real base dir → archive resolves to `/tmp` fallback;
  both candidates landing under the real base dir → exit
  USER_INPUT with the prescribed error and no write. Symlink
  edge-cases covered (resolved real path, not lexical).
- `verification/tests/test_demo_cleanup_polish.py` (new) —
  cleanup prompts, dry-run mode, recovery from rotation
  edge cases.

**Acceptance:**
- All 12 personas load via `hai demo start --persona <name>`
  without crash; `hai today` succeeds.
- Archive lands at the resolved path **outside the real
  `~/.health_agent` tree** (default
  `$XDG_CACHE_HOME/hai/demo_archives/<marker_id>__...` if
  `XDG_CACHE_HOME` is set, else
  `/tmp/hai_demo_archives/<marker_id>__...`) per the rotation
  policy. **Resolved-path guard test green:** when
  `XDG_CACHE_HOME` is set to a path under the real base dir
  (e.g., `~/.health_agent/cache`), archive falls back to
  `/tmp/hai_demo_archives/...` rather than landing inside the
  real tree. When both candidates fail the guard, `hai demo
  end` exits USER_INPUT and writes nothing.
- Real `~/.health_agent` checksum byte-identical before and
  after `hai demo end` under every archive configuration.
- `hai demo cleanup --dry-run` enumerates without deleting.
- Threshold compliance: `demo.archive_max_count` resolved via
  `coerce_int`, bool-as-int rejection test green (D12).

**Sequencing.** Lands at item #14 (after W-O delivers P9–P12).
Hard-deps on W-Va's marker schema + resolver. **Hard-precedes
W-Z's § A (full persona flow) only.** W-Z's § B (blank-demo
flow) is independent of W-Vb and ships even when W-Vb defers.

**W-O × W-Vb fixture-contract coordination (cycle day 1).**
Before W-Vb implementation begins, agree on
`build_demo_fixture()` signature so W-O authors P9–P12 with the
contract from the start. Otherwise W-O ships personas without
the helper and W-Vb adds it retroactively across 12 files.

### 2.16 W-W — `hai intake gaps` state-snapshot fallback mode

**Goal.** Make session-start gap-detection robust to broken pull.
Source: F-DEMO-04 from the demo-run findings; on 2026-04-28 the
intervals.icu 403 cascaded into a broken `hai intake gaps` chain
because the protocol requires `--evidence-json` from a successful
`hai clean`.

**Approach (per maintainer answers Q1–Q3).**

1. **New `--from-state-snapshot` flag** on `hai intake gaps`.
   Mutually exclusive with `--evidence-json`. Caller opts in
   explicitly — the flag makes the source visible in the audit
   trail rather than auto-falling-back silently (Q1: explicit B).
2. **Derive gaps from the latest accepted state.** Use the
   in-memory snapshot helper (the same primitive `hai state
   snapshot` calls under the hood); do not shell out. Walk the
   same gap-rule logic as the pull-evidence path, but consume
   `accepted_*_state_daily` rows + manual intake jsonl tails
   instead of fresh-evidence dicts.
3. **Distinguished output shape.** Each gap object carries a new
   `derived_from: "pull_evidence" | "state_snapshot"` field
   (Q2: distinguished). Existing pull-evidence callers keep
   the same effective behaviour but now see `derived_from:
   "pull_evidence"` explicitly. Backwards-compatible additive.
4. **Staleness gate.** Refuse to derive gaps if no successful
   `sync_run_log` entry exists within the last 48h (Q3: 48h).
   Override via `--allow-stale-snapshot`. Default is configurable
   via `thresholds.toml`:
   `gap_detection.snapshot_staleness_max_hours = 48`. Use
   `core.config.coerce_int` per D12.

   **No-history behaviour (Codex F-IR2-03):** when no
   `sync_run_log` entry exists at all, the gate refuses unless
   `--allow-stale-snapshot` is passed. "Within the last 48h"
   strictly implies the user has at least one successful sync;
   the no-history case fails-closed.
5. **Read-consistency contract (per Codex F-PLAN-06; revised
   after Codex F-IR-03 to match the actual code path).**
   Snapshot-derived gaps run inside a **single read transaction
   over SQLite**, with an `as_of_read_ts: <ISO-8601>` captured at
   transaction start. The resulting `Gap` objects carry a new
   `snapshot_read_at: <ISO-8601>` field matching `as_of_read_ts`.

   **JSONL tail reads are out of scope for v0.1.11 W-W.** Gap
   derivation runs entirely off SQLite via `build_snapshot`; the
   gap detector's input (`classified_state.uncertainty`) flows
   from `accepted_*_state_daily` rows which are SQLite-only.
   F-PLAN-R2-04's row-level `recorded_at` filter contract was
   authored against a hypothetical JSONL-tail consumer that
   doesn't exist in this code path. If a future workstream adds
   JSONL reads to gap derivation, the row-level filter +
   inode-and-byte-range capture must land alongside it.

**Files (as actually shipped after Codex F-IR2-03 narrowing):**
- `cli.py` — `hai intake gaps` handler; `--from-state-snapshot`
  + `--allow-stale-snapshot` flags + mutual-exclusion guard.
- `core/intake/gaps.py` — `compute_intake_gaps_from_state_snapshot()`
  entry point. Wraps derivation in `BEGIN IMMEDIATE TRANSACTION`
  and captures `as_of_read_ts`.
- `core/config.py` — `DEFAULT_THRESHOLDS["gap_detection"][
  "snapshot_staleness_max_hours"] = 48`.
- `core/capabilities/walker.py` — new flags surface in the
  manifest.

**Tests (as actually shipped — Codex F-IR2-03 alignment):**

- `verification/tests/test_intake_gaps_from_snapshot.py`:
  - **Happy path:** 30h-old pull (`test_recent_pull_within_48h_passes_gate`).
  - **Boundary at 47h:** under threshold, derivation succeeds
    (`test_pull_at_47h_passes_gate`).
  - **Boundary at 49h:** over threshold, refused with
    `StalenessRefusal` (`test_pull_at_49h_refused_by_gate`).
  - **50h + override:** `--allow-stale-snapshot` lets it through
    with a `staleness_warning` field
    (`test_allow_stale_lets_old_pull_through_with_warning`).
  - **No-history (post-Codex-F-IR2-03):** refuses unless
    `--allow-stale-snapshot` is passed
    (`test_no_sync_run_history_refuses_without_override`).
  - **Sequential determinism:** 100 sequential trials over a
    stable DB produce the byte-identical gap shape, exercising
    the SQLite read-isolation guarantee `BEGIN IMMEDIATE`
    provides (`test_concurrency_100_trials_deterministic`).
  - **Audit fields:** every gap carries `derived_from:
    "state_snapshot"` and `snapshot_read_at`; top-level payload
    too.

  **Out of scope for v0.1.11 (deferred from earlier draft):**
  - `test_intake_gaps_source_parity.py` — would require the
    pull-evidence and state-snapshot paths to share a contract
    test surface. The state-snapshot path's audit fields
    (`derived_from`, `snapshot_read_at`) are documented; the
    parity test isn't necessary for v0.1.11.
  - `test_intake_gaps_concurrency.py` (concurrent write/read
    cross-process) — defers with the JSONL-tail consumer that
    doesn't exist in v0.1.11. A real concurrent test requires
    the JSONL-tail surface; the SQLite-only path is covered by
    the determinism test above.
  - `test_intake_gaps_jsonl_old_rows_kept.py` — defers with the
    JSONL-tail consumer.
  - `test_intake_gaps_capabilities_emission.py` — folded into
    `test_capabilities_proposal_contracts.py`'s per-W-id
    coverage (the W-W flags appear in the manifest determinism
    + W30 preservation tests).

**Acceptance (post-F-IR2-03 alignment):**
- `hai intake gaps --from-state-snapshot --user-id u_local_1
  --as-of 2026-04-28` produces a valid gap manifest derived
  purely from state, with `derived_from="state_snapshot"` and
  `snapshot_read_at` populated on every gap.
- 48h staleness gate enforced; overridable via
  `--allow-stale-snapshot`.
- No-history fails closed; passes only with
  `--allow-stale-snapshot`.
- Pull-evidence path unchanged in observable behaviour.
- Threshold default lives in `DEFAULT_THRESHOLDS`; user can
  override via `thresholds.toml`.
- Sequential-determinism test green: 100 trials produce
  byte-identical output (the SQLite read-isolation guarantee).
- Capabilities manifest reflects the new flags.

**Adjacency to W-E (state-change supersession).** Both consume
"latest accepted state". W-E adds a state fingerprint primitive;
W-W reads accepted state for gap derivation. **Do not pre-engineer
a shared abstraction.** Implement W-W against the existing
snapshot helper; if W-E's fingerprint primitive lands in a way
that W-W could naturally consume, opportunistically refactor at
the end of the cycle. If not, ship them independent.

### 2.17 W-X — `hai doctor` probe extension for live-API auth

**Goal.** Eliminate the diagnostic-trust gap surfaced by F-DEMO-01:
`hai doctor` reports `auth_intervals_icu: ok` when credentials are
present in the keyring, even if the API itself rejects them
(observed live: HTTP 403 mid-demo with green doctor row).

**Approach.**
1. Add a `--deep` flag to `hai doctor`. Default off so the cheap
   path stays cheap; on for explicit pre-flight.
2. When set, the auth-doctor checks for intervals.icu and Garmin
   invoke a `Probe` protocol — see step 4.
3. Probe outcome surfaces in the doctor row alongside the existing
   credentials-present check. HTTP status code included on failure.
4. **`Probe` protocol split (per Codex F-PLAN-R2-03 / maintainer
   Q-3 = b).** Define a `Probe` protocol with two
   implementations:
   - `LiveProbe` — real network call (HEAD or minimal-scope
     wellness fetch with short timeout). Used in real (non-demo)
     mode.
   - `FixtureProbe` — returns a pre-supplied response without
     touching the network. Used in demo mode; response is
     supplied by the active persona fixture (or a default
     200-OK stub for `--blank` sessions).
   - Resolution: if a demo marker is active, the auth-doctor
     uses `FixtureProbe`; otherwise `LiveProbe`. **A hard
     no-network assertion guards `FixtureProbe`** — any attempt
     to open a real socket while a demo marker is active fails
     the test suite. Implemented via a `socket`-monkeypatch
     guard in the demo-mode integration tests.

**Files:**
- `core/doctor/checks.py` auth-check helpers; `Probe` protocol
  + `LiveProbe` / `FixtureProbe` implementations + resolution
  based on demo-marker presence.
- `cli.py` doctor handler (new flag).
- `core/pull/intervals_icu.py` (expose a probe-only entry point if
  one doesn't exist; reuse the existing fetch path with a
  trivial-scope query — feeds `LiveProbe`).
- `core/demo/session.py` — expose a `get_active_marker()` helper
  used by the auth-doctor for `Probe` resolution (already
  authored in W-Va).
- `core/capabilities/walker.py` (per Codex F-PLAN-07) — emit the
  new `--deep` flag and the `auth_*.probe` row schema.
- `core/capabilities/render.py` — markdown regeneration.
- `reporting/docs/agent_cli_contract.md` — regenerated.

**Tests:**
- `verification/tests/test_doctor_deep_probe_live.py` (new) —
  mocks 200, 401, 403, network-error responses for `LiveProbe`;
  asserts the doctor row reports each correctly. Asserts demo
  marker absent during the test.
- `verification/tests/test_doctor_deep_probe_fixture.py` (new) —
  with a demo marker active, `--deep` routes to `FixtureProbe`;
  the persona fixture supplies a 403 stub; doctor row reflects
  the stubbed status; **socket-monkeypatch guard asserts no real
  network call** for the duration of the test.
- `verification/tests/test_doctor_capabilities_emission.py` (new)
  — assert the new flag + row schema appear in the manifest.

**Acceptance:**
- `hai doctor --deep` (real mode) returns failed status when
  credentials are configured but the API rejects them.
- `hai doctor --deep` (demo mode) returns the fixture-stubbed
  status with no network call (assertion enforced by socket
  guard).
- Default `hai doctor` behaviour unchanged (no probe, no new
  network call).
- Doctor JSON schema gains an optional `probe` field on auth rows
  (with `probe.source: "live" | "fixture"` for audit clarity).
- Capabilities manifest reflects the new flag and row schema.

### 2.18 W-Y — CLI civil-date flag harmonisation

**Goal.** Unify the civil-date flag name across `hai` subcommands
so agents and users do not have to remember three variants
(F-DEMO-03).

**Current surface:**
- `hai daily`, `hai today`, `hai intake *` — `--as-of`
- `hai explain` — `--for-date`
- `hai pull` — `--date`
- `hai clean`, `hai state read` — neither (different shape)

**Approach.**
1. `--as-of` becomes the canonical civil-date flag.
2. Add `--as-of` as an alias on `hai pull` (alongside `--date`).
3. Add `--as-of` as an alias on `hai explain` (alongside
   `--for-date`).
4. Old flags kept for one cycle with a deprecation warning to
   stderr; removed in v0.1.13 per a tactical-plan note.
5. `hai capabilities --json` lists both names in the alias array
   for affected flags so contract consumers see them.

**Files (corrected per Codex F-PLAN-07; the previous draft cited
the non-existent `core/cli/capabilities.py`):**
- `cli.py` (pull, explain handlers; add `--as-of` alias).
- `core/capabilities/walker.py` — alias enumeration if not already
  inferred from argparse.
- `core/capabilities/render.py` — markdown regeneration.
- `reporting/docs/agent_cli_contract.md` — regenerated.

**Tests:**
- `verification/tests/test_cli_flag_aliases.py` (new) — asserts
  `--as-of` accepted on every subcommand that takes a civil date,
  and `--date` / `--for-date` still work with a deprecation note.

**Acceptance:**
- `hai pull --as-of 2026-04-28` works; same outcome as `--date`.
- `hai explain --as-of 2026-04-28 --user-id u_local_1` works; same
  outcome as `--for-date`.
- Deprecation warnings visible on stderr for old flags.
- Capabilities manifest reflects the alias surface.

### 2.19 W-Z — Demo-flow guide doc

**Goal.** Repeatable demo-run sequence captured in a doc so future
demos don't depend on agent session memory (S-DEMO-02 from the
2026-04-28 demo-run findings).

**Approach (per maintainer answer Q-1 of plan-audit round 2 —
two-variant doc for the W-Vb deferral path).** Author
`reporting/docs/demo_flow.md` with two clearly-marked sections:

**§ A — Full demo flow (canonical when W-Vb has shipped):**
1. **Open a demo session** — `hai demo start --persona p1`.
2. Pre-flight check — `hai doctor --deep` (routes to fixture
   stub probe; verifies diagnostic-trust feature on a stubbed
   403).
3. In-character capabilities recap (refusal posture as the
   feature).
4. Walking the past day's plan (from the persona fixture) as a
   live audit-chain example.
5. Free-text intake → typed intake routing.
6. Per-domain proposal composition + synthesis.
7. User-facing narration via `hai today`.
8. Same-day correction path (supersession via re-running an
   intake).
9. **Close the demo session** — `hai demo end` (archives outside
   real tree per Q-2).

**§ B — Blank demo flow (canonical when W-Vb has deferred):**
1. **Open a blank demo session** — `hai demo start --blank`.
2. Pre-flight check — `hai doctor --deep` (fixture stub probe
   even on `--blank`; default 200-OK stub unless overridden).
3. In-character capabilities recap.
4. **Manual seed** — script `hai intake readiness`,
   `hai intake gym`, `hai intake nutrition` against the empty
   scratch state to populate enough for `hai today` to render.
5. `hai daily --skip-pull --source csv` to synthesise.
6. Walk the resulting plan as the audit-chain example (in
   place of "the past day's plan" since there is no past).
7. Same-day correction path.
8. **Close the demo session** — `hai demo end`.

Doc preface names which section is canonical based on the
shipped scope; the unshipped section is annotated as deferred.
Include exact command snippets in both sections so each is
execution-ready.

**Hard dependencies:**

- **W-Va** (safe demo isolation) — required regardless. § A and
  § B both depend on it; without W-Va, every snippet pollutes
  real state.
- **W-Vb** (persona fixtures) — required for § A only. If W-Vb
  defers, § A is annotated "deferred to v0.1.12" and § B
  becomes the canonical demo flow for v0.1.11.
- **W-X** — the `--deep` snippets in both § A and § B depend on
  the `Probe` protocol's `FixtureProbe` (per Q-3).

**Files:**
- `reporting/docs/demo_flow.md` (new).
- `reporting/docs/README.md` index update if one exists.

**Tests:** none (doc-only).

**Acceptance:**
- Doc reads coherently top-to-bottom.
- Every command snippet executes against a current `hai`
  installation without modification.

---

## 3. Acceptance criteria (ship gates)

v0.1.11 ships when:

- [ ] All 20 workstreams (W-B, W-E, W-F, W-H1, W-K, W-L, W-N, W-O,
      W-P, W-Q, W-R, W-S, W-T, W-Va, W-Vb, W-W, W-X, W-Y, W-Z,
      plus the v0.1.10 round-2 / round-3 carry-overs if any
      reopen) complete OR explicitly deferred with documented
      reason. **W-Vb is the only deferrable-as-a-whole item**
      (named-defer to v0.1.12 if cycle runs hot). When W-Vb
      defers, **W-Z still ships** (its § B blank-demo variant
      becomes canonical) and the **demo regression gate still
      runs** (in isolation-replay mode). Acceptable shipped
      counts: 20 (W-Vb shipped) or 19 (W-Vb deferred) — both
      pass this gate.
- [ ] **W-E, W-F, and W-Va are tagged release-blocker-class.**
      v0.1.11 cannot ship without all three. W-E + W-F are the
      audit-chain-integrity thesis. W-Va is blocker-class because
      half-broken demo isolation actively pollutes real user state
      (per Codex F-PLAN-02 + F-PLAN-03; maintainer answer Q-B).
- [ ] **Pre-implementation gate (per Codex F-PLAN-01).** Phase 0
      `audit_findings.md` reviewed by maintainer. Findings tagged
      `revises-scope` resolved into PLAN.md revisions; findings
      tagged `aborts-cycle` either resolved or trigger cycle abort
      with documented reason. Implementation does not start until
      this gate explicitly fires.
- [ ] **Demo regression gate (per Codex F-PLAN-08 + F-PLAN-R2-01;
      two modes per maintainer answer Q-1 of plan-audit round 2).**
      The gate runs in **persona-replay mode** when W-Vb has
      shipped, and **isolation-replay mode** when W-Vb has
      deferred. Both modes assert:
      - Every command snippet in the canonical section of
        `reporting/docs/demo_flow.md` executes without
        modification.
      - **No live network call attempted** for the duration of the
        replay. Enforced by socket-monkeypatch guard; any real
        socket open fails the gate. Live sources rejected per
        the W-Va refusal matrix; `hai doctor --deep` routed to
        `FixtureProbe` per W-X.
      - **Real `state.db` checksum + real `~/.health_agent` tree
        (recursive checksum) + real `thresholds.toml`
        byte-identical before / after.** No exclusions — archives
        live outside the real tree per Q-2 + the resolved-path
        guard in W-Vb, so there is no `demo_archives/` path
        inside the recursion to exclude.
      - **Archive root assertion (separate, per Codex F-PLAN-R3-02).**
        After `hai demo end` runs, the resolved archive path is
        outside the real base dir's resolved real path. Verified
        by `os.path.commonpath`-style check on the resolved real
        paths (not lexical paths).
      - `hai intake gaps --from-state-snapshot` emits gaps with
        `derived_from: "state_snapshot"` and `snapshot_read_at`
        populated.
      - `hai daily --supersede` on a fresh demo-day exits
        USER_INPUT (not `_v2`).

      **Persona-replay mode** (W-Vb shipped) additionally
      asserts:
      - `hai demo start --persona p1_endurance_runner` populates
        the scratch root with 14d of history; `hai today`
        renders.
      - `hai doctor --deep` against the persona fixture's stubbed
        403 credential surface correctly reports failed-auth
        status.
      - The 2026-04-28 demo can be replayed end-to-end (against
        the persona fixture) without real-state pollution,
        false-green doctor output, broken gaps, flag mismatch,
        or orphan supersede ids.

      **Isolation-replay mode (boundary-stop demo)** (W-Vb
      deferred; per Codex F-IR3-01 alignment) additionally
      asserts:
      - `hai demo start --blank` opens an empty scratch session
        with the scratch state.db initialised.
      - The scripted manual-seed sequence (readiness + nutrition
        + stress intakes per § B of the demo-flow doc) writes to
        scratch DB + scratch base_dir.
      - `hai daily --skip-pull --source csv` returns
        `overall_status: "awaiting_proposals"` — the canonical
        boundary signal. Proposal authoring is the runtime/skill
        boundary; full synthesis defers to v0.1.12 W-Vb.
      - `hai today` shows "no plan for <date>" (exit 1 with the
        no-plan stderr signal) — the visible signal that the
        runtime/skill boundary has not yet been crossed.
      - End-to-end replay of § B without real-state pollution.

      **Independently verified (NOT part of the v0.1.11 isolation-
      replay sequence)** — covered by their own dedicated tests:
      - W-X `hai doctor --deep` FixtureProbe in demo mode
        (`test_doctor_deep_probe.py::test_demo_mode_deep_probe_does_not_open_a_socket`).
      - W-W `hai intake gaps --from-state-snapshot` derived_from +
        snapshot_read_at + 47/49h boundary + 100-trial determinism
        (`test_intake_gaps_from_snapshot.py`).
      - W-F fresh-day `hai daily --supersede` USER_INPUT refusal
        with proposals seeded
        (`test_supersede_on_fresh_day.py`). Note: in the demo
        flow path (a), `daily --supersede` short-circuits at
        `awaiting_proposals` BEFORE the W-F gate fires (no
        proposals to synthesize over). Demonstrating W-F via the
        demo flow requires path (b) proposal seeding and is
        forward-compat to v0.1.12 W-Vb.

      **Forward-compat to v0.1.12 W-Vb** (NOT runnable in v0.1.11):
      - `hai daily` reaching synthesis with proposals seeded by
        the persona-fixture loader.
      - `hai today` rendering a populated plan.
      - Re-run-with-intake-change auto-supersede via `_v2`
        end-to-end through the demo session (the W-E contract is
        unit-tested in
        `test_daily_supersede_on_state_change.py`; the demo
        flow does not exercise it without proposals).
- [ ] `verification/tests/` green: ≥ 2200 tests passing (was 2169
      at v0.1.10 ship; +30+ from new tests).
- [ ] Persona harness re-runs show:
  - W-B: persona matrix findings drop from 3 → ≤ 1.
  - All 12 personas run without crashes.
- [ ] mypy correctness-class errors: 0 (stylistic-class deferred).
- [ ] ruff strict pass: 0 findings.
- [ ] bandit -ll: 0 unsuppressed findings.
- [ ] **Capabilities manifest gate (per Codex F-PLAN-R2-05 +
      F-PLAN-R3-03; mirrors the W-S § 2.12 contract).**
      `hai capabilities --json` and the regenerated markdown are
      deterministic across runs (same source state →
      byte-identical output). The expected additive content for
      W-S, W-Va, W-W, W-X, and W-Y is present and passes its
      per-W-id capabilities tests. **No frozen-schema check** —
      W30's "manifest schema not yet frozen" decision is
      preserved.
- [ ] `verification/tests` runs with `-W error::pytest.PytestUnraisableExceptionWarning` clean (narrowed from the original `-W error::Warning` catch-all per W-N scope-narrowing — broader gate deferred to v0.1.12 W-N-broad).
- [ ] CHANGELOG.md updated with v0.1.11 section + per-W-id summary.
- [ ] `RELEASE_PROOF.md` emitted with full pytest log + persona
      harness re-run output.
- [ ] Codex audit round 1 returns SHIP or SHIP_WITH_NOTES.

---

## 4. Sequencing (recommended)

1. **W-N** (pytest warning) — 30 min, smoke-clearer.
2. **W-L** (bandit B310) — 30 min, single-site review.
3. **W-K** (bandit B608) — half-day, all 16 sites in one pass.
4. **W-Q** (review-schedule investigation) — 1-2 days, may inform
   W-E decisions.
5. **W-Va** (`hai demo` mode core: marker, fail-closed resolver,
   isolation, refusal matrix) — 2-3 days. **Release-blocker class.
   Lands first among non-smoke-clearers** so every later workstream
   composes against the multi-resolver override (per Codex
   F-PLAN-04). Includes the W-O × W-Vb fixture-contract agreement
   (signature only at this stage).
6. **W-B** (volume_spike gate, with D12 coercer) — 1-2 days.
   Independent.
7. **W-O** (persona expansion 8 → 12) — 2-3 days. Parallel with
   W-B. Authors P9-P12 against the agreed
   `build_demo_fixture()` signature.
8. **W-P** (property tests) — 2-3 days. May surface bugs that
   reshape later workstreams.
9. **W-H1** (mypy correctness) — 2-3 days. Picks up incidental
   fixes from earlier work.
10. **W-R** (rollup edge cases) — 1 day. Decision + test.
11. **W-Y** (CLI flag harmonisation + capabilities update) — 2
    hours. Drop in any convenient slot.
12. **W-X** (doctor probe extension + capabilities update) — 0.5
    day. Independent.
13. **W-W** (gaps state-snapshot fallback, with read-consistency
    contract + capabilities update) — 1-2 days. Independent.
    Adjacent to W-E (both consume "latest accepted state") but
    don't pre-engineer a shared abstraction.
14. **W-Vb** (`hai demo` polish: persona fixtures, archive,
    cleanup polish) — 2-3 days. **Deferrable as a whole** if
    cycle runs hot. Lands after W-O so all 12 personas are
    available for fixture loading.
15. **W-S extended** (persona harness drift + capabilities expose
    proposal contracts) — 1 day. Pulls one primitive, two
    consumers.
16. **W-E** (state-change supersession) — 2-3 days. Schema
    migration + synthesis path; do this when other workstreams
    are stable.
17. **W-F extended** (version counter + supersede-on-fresh-day
    USER_INPUT contract) — 1-2 days. Builds on W-E investigation.
18. **W-Z** (demo-flow doc) — 0.5 day. Doc-only. **Hard-deps on
    W-Va; conditionally uses W-Vb for § A (full persona
    flow).** When W-Vb defers, § A is annotated "deferred to
    v0.1.12" and § B (blank-demo flow) becomes canonical.
19. Persona harness re-run → confirm fixes visible.
20. **Demo regression gate** (per Codex F-PLAN-08 + F-PLAN-R2-01;
    new ship gate) — runs in **persona-replay mode** (W-Vb
    shipped: replay against `hai demo start --persona p1`) **OR
    isolation-replay mode** (W-Vb deferred: `hai demo start
    --blank` + scripted manual-seed sequence). Both modes assert
    real state untouched per the gate spec in §3.
21. Codex implementation-review round 1.

Total: **22-30 days. Realistic ship: 4-6 calendar weeks from open.**
Demo-finding fold-ins + Codex plan-audit revisions added ~7-10
days to the v0.1.10-era estimate.

**Headroom note (per Codex F-PLAN-05 + F-PLAN-R2-01).** If W-P
property tests surface >3 correctness-class findings, cycle
absorbs them by **deferring W-Vb to v0.1.12** (named-defer ship
gate). When W-Vb defers:
- W-Z **still ships**: its § B blank-demo variant becomes
  canonical for v0.1.11; § A is annotated "deferred to v0.1.12".
- Demo regression gate **still runs**: in isolation-replay mode
  (W-Va isolation + scripted manual-seed) instead of
  persona-replay mode.
- Cycle workstream count drops to 19 (still passes ship gate).
- W-Va, W-E, W-F all must ship; partial unsafe demo mode also
  blocks ship.

If cycle still slips beyond 30 focused days post-W-Vb-defer,
escalate to maintainer for further scope cuts before exhausting
the 6-week calendar window.

---

## 5. Risk register (cycle-specific)

- **W-E schema migration** is the highest-risk item. Touches the
  daily_plan table. Migration round-trip test is a hard gate.
- **W-P property tests** may surface bugs that bloat scope. If
  hypothesis finds something the deterministic tests missed,
  triage it: fix-now if correctness, defer to v0.1.12 if
  edge-case stylistic.
- **W-O P10 (adolescent)** is deliberately out-of-supported-set.
  The test isn't "P10 produces good recommendations" — it's "P10
  fails gracefully." Expected output language matters; cycle
  must align on what "out of supported set" looks like at the CLI
  surface.
- **W-K bandit verdicts** may reveal a genuine SQL-injection vector
  (very unlikely given the patterns surveyed in v0.1.10, but the
  pass exists to prove it). If so, it becomes the highest-priority
  fix and reshapes the cycle.
- **W-Va multi-resolver seam** is the second-highest-risk item
  after W-E. Every CLI command's read + write path threads through
  it; a regression makes the maintainer's real state unreachable
  OR (worse) leaks demo writes into real state. Mitigation: land
  the seam at sequencing item #5 so all later work composes
  against it; `test_demo_isolation_surfaces.py` asserts byte-
  identical real-state checksums across the matrix; integration
  test that asserts *with no demo session active* every existing
  CLI command resolves to the canonical real-state paths byte-
  for-byte.
- **W-Va fail-closed marker contract** (per Codex F-PLAN-03) —
  any branch in the resolver that falls open to real state on
  marker-parse-failure is the failure mode the feature must NOT
  have. Mitigation: explicit fail-closed tests for every marker
  invalid-shape; tests assert no real-state mutation under each
  failure.
- **W-Va × W-O × W-Vb fixture contract** must be agreed before
  W-O or W-Vb implementation begins. Coordination point at
  cycle day 1: nail the `build_demo_fixture(scratch_root: Path)`
  signature so W-O authors P9-P12 with the helper from the start
  rather than W-Vb retroactively adding it across 12 files.
- **W-W staleness threshold (48h default)** is configurable via
  thresholds.toml; if the persona matrix reveals 48h is too tight
  or too loose under realistic usage, adjust during the cycle and
  document the rationale rather than tightening to a hardcoded
  bound.
- **W-W concurrency contract** (per Codex F-PLAN-06) — single-
  read-transaction semantics over SQLite plus `as_of_read_ts`-
  bounded JSONL tail reads. Without these, gap output can mix old
  accepted-state with new manual-tails. Mitigation: dedicated
  `test_intake_gaps_concurrency.py` runs 100 trials with race-
  condition simulation; asserts every trial produces one of two
  valid shapes, never a third.
- **Capabilities-manifest path correction** (per Codex F-PLAN-07)
  — the prior PLAN draft cited `core/cli/capabilities.py` which
  does not exist. Corrected to `core/capabilities/walker.py` +
  `core/capabilities/render.py`. Implementation must pull the
  current manifest builder, not chase the stale path. Mitigation:
  every workstream that touches the CLI surface (W-S, W-Va, W-W,
  W-X, W-Y) explicitly enumerates the capabilities update in its
  files-changed list.

---

## 6. Provenance

This PLAN.md is built on:

- `reporting/plans/strategic_plan_v1.md` § 7 Wave 1.
- `reporting/plans/tactical_plan_v0_1_x.md` § 2.
- `reporting/plans/v0_1_10/audit_findings.md` (deferred items).
- `reporting/plans/v0_1_10/RELEASE_PROOF.md` (test surface baseline).
- `reporting/plans/v0_1_9/BACKLOG.md` (W-N carry-over).

Out-of-scope items (§ 1.2) carry their deferred-because reasons
forward into the v0.1.11 BACKLOG.md after this cycle ships.
