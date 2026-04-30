# Changelog

All notable changes to Health Agent Infra will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the v0.x caveat that breaking changes can land in minor releases
until v1.0.

Per-release detail lives under `reporting/plans/<version>/`.

---

## [0.1.13] - 2026-04-30

> **Theme.** Largest cycle in the v0.1.x track at 17 workstreams.
> Three parallel themes: close v0.1.12 named-deferred items
> (W-Vb persona-replay end-to-end, W-N-broader 50-site sqlite3
> leak fix, W-FBC-2 multi-domain F-B-04 closure, CP6 application);
> ship the originally-planned onboarding scope (W-AA through
> W-AG); land governance prerequisites for v0.1.14 + v0.2.0
> (W-29-prep, W-LINT, W-AK, W-A1C7).
>
> **Tier (per CP3 D15):** substantive.
>
> **D14 plan-audit:** PLAN_COHERENT at round 5 with the
> 11 → 7 → 3 → 1-nit → 0 settling signature (22 findings
> cumulative; thrice-validated halving head). Mild deviation
> from the 4-round empirical norm reflects the 17-W-id scope.
>
> **Phase 0 (D11) bug-hunt:** internal sweep + audit-chain probe
> + persona matrix all clean. One in-scope finding (F-PHASE0-01,
> W-N-broader baseline -1 drift, absorbed by W-N-broader). Pre-
> implementation gate fired green.
>
> **Codex IR chain:** SHIP at round 3 with the 6 → 2 → 0 settling
> shape (8 findings cumulative). Round 1 SHIP_WITH_FIXES, round 2
> SHIP_WITH_FIXES, round 3 SHIP outright. Both round-2 findings
> were doc/lint surfaces; no correctness-bug shape across any
> round.

### Added

- **`hai init --guided`** (W-AA) — 7-step interactive onboarding
  orchestrator. Walks thresholds + state DB + skills + intervals.icu
  auth + initial intent/target rows + first wellness pull +
  `hai today` surface. Each step idempotent; KeyboardInterrupt
  mid-flow surfaces `USER_INPUT` exit code with actionable
  next-step prose. Operator demo SLO target ≤5 min wall-clock
  documented in `reporting/docs/onboarding_slo.md` (target, not
  CI gate, per F-PLAN-08).
- **`hai capabilities --human`** (W-AB) — workflow-grouped
  one-page rendering of the CLI surface. Existing `--json` and
  `--markdown` modes unchanged.
- **`hai doctor --deep`** (W-AE) — live intervals.icu probe-pull
  classified into 5 outcome classes: `OK`, `CAUSE_1_CLOUDFLARE_UA`,
  `CAUSE_2_CREDS`, `NETWORK`, `OTHER`. Each carries a specific
  actionable next-step. Documented at
  `reporting/docs/intervals_icu_403_triage.md`. Closes the
  original F-DEMO-01 detection gap (W-CF-UA fixed the symptom in
  v0.1.12.1).
- **`hai daily --re-propose-all` runtime semantics** (W-FBC-2,
  full F-B-04 closure across 6 domains). Per-domain
  `<domain>_proposal_carryover_under_re_propose_all` token in the
  recommendation's `uncertainty[]` when the proposal envelope is
  older than `RE_PROPOSE_ALL_FRESHNESS_THRESHOLD` (60s default).
  Token surfaces in `hai today` markdown / plain / JSON +
  `hai explain`. Option A default per
  `reporting/docs/supersede_domain_coverage.md`; option B
  per-domain fingerprint primitive NOT shipped (runtime is
  domain-agnostic via `_carryover_token_for_domain()`); option C
  remains out-of-v0.1.x scope per F-PLAN-07.
- **`hai today` cold-start prose** (W-AG) — different framing
  for day-1 users (no streak history) vs day-30+ established
  users. Threshold corrected to 30 days at IR r1 F-IR-01 from
  a transient 7-day implementation drift.
- **Regulated-claim lint** (W-LINT) at
  `core/lint/regulated_claims.py`. Static + runtime helpers;
  banned terms ("abnormal HRV", "clinical-grade", "biomarker",
  "risk score", "diagnose", "diagnosis", "disease",
  "medical advice", "treatment", "therapy", "cure"). Four-
  constraint exception path (allowlisted skill `expert-explainer`
  + provenance citation + quoted/attributed context + CLI-
  rendering boundary always strict per F-PLAN-09 constraint 4).
  `META_DOCUMENT_ALLOWLIST` (safety / reporting / expert-explainer)
  bounds the meta-document pragma per IR r1 F-IR-04 closure.
- **Persona-replay end-to-end for P1+P4+P5 ship-set** (W-Vb).
  `apply_fixture()` flipped from boundary-stop to proposal-write
  branch; full DomainProposal seeds for each ship-set persona
  across all 6 domains. Clean-wheel build-install-subprocess test
  at `test_demo_clean_wheel_persona_replay.py` asserts the wheel
  ships fixtures correctly. The 9 non-ship-set personas
  (P2/P3/P6/P7/P8/P9/P10/P11/P12) are honestly fork-deferred to
  v0.1.14 W-Vb-3.
- **Declarative persona expected-actions** (W-AK). Three public
  helpers in `personas/base.py`:
  `established_expected_actions()`, `day_one_expected_actions()`,
  `established_forbidden_actions()`. Each of the 12 packaged
  personas declares an inline `expected_actions=` keyword in its
  own file. P11 overrides stress to legitimately allow escalation
  per the W-O elevated-stress scenario; P8 uses the day-1
  conservative-only shape. Base-class auto-derive retained as
  safety net only.
- **Trusted-first-value acceptance matrix** (W-A1C7) at
  `test_acceptance_matrix.py` — codifies the gate-language
  contract as a contract test.
- **README quickstart smoke test** (W-AF) — parses `bash
  quickstart` fenced block from README; runs each command in a
  temp dir with stubbed intervals.icu fixture. Catches README
  drift within one CI build of any README change.
- **`reporting/docs/cli_boundary_table.md`** (W-29-prep) —
  derived live from `hai capabilities --json`, names the proposed
  v0.1.14 W-29 mechanical-split handler-group assignment per
  subcommand. Three legitimate post-baseline snapshot
  regenerations recorded (45319da freeze → 03fab4f W-AA `--guided`
  → bd11be3 W-FBC-2 `--re-propose-all` help text).
- **`reporting/docs/onboarding_slo.md`** — operator demo SLO
  reference (manual demo protocol per F-PLAN-08).
- **`reporting/docs/intervals_icu_403_triage.md`** — in-tree
  triage doc for `hai doctor --deep`.

### Changed

- **README.md** rewritten for orientation → quickstart →
  troubleshooting (W-AC). Test-count surface tracks the actual
  gate result (2493 at v0.1.13 ship).
- **Every `USER_INPUT` exit-code site in `cli.py`** carries
  actionable next-step prose (W-AD). New
  `test_user_input_messages_actionable.py` AST-walks every
  USER_INPUT raise. W-AA's USER_INPUT exit on guided-onboarding
  interrupt/partial paths added the same interlock at IR r1.
- **Pytest broader-warning gate** (`-W error::Warning`) restored
  as the v0.1.13 ship target (W-N-broader). 50 sqlite3
  connection-lifecycle + 1 file-handle + 1 HTTPError leak sites
  closed via structural `try/finally` + context-manager fixes;
  no `nosec`/`noqa`/`type: ignore` shortcuts.
- **`strategic_plan_v1.md` §6.3** updated to the 4-element
  load-bearing-whole framing per `v0_1_12/cycle_proposals/CP6.md`
  (CP6 application). v0.1.10-update line preserved unchanged
  per CP6 acceptance gate.
- **`run_synthesis()`** signature gained `re_propose_all: bool`
  parameter; existing callers unaffected.

### Fixed

- **F-IR-01 W-AG threshold drift.** `_STREAK_ESTABLISHED_THRESHOLD`
  shipped at 7 against PLAN-contracted 30. Corrected to 30; tests
  re-baselined to 30/29 boundaries + 45 for format-consistency.
- **F-IR-02 `hai init --guided` exit code.** Pre-fix returned `OK`
  even when guided flow reported `interrupted` or `partial` — a
  user-facing false green for CI / doctor / agent callers.
  Mapped both to `USER_INPUT` exit code with actionable stderr
  prose; `ok_with_skips` retained as `OK` (intentional user
  skip is not an error).
- **F-IR-03 W-AK persona declarations.** Initial implementation
  satisfied PLAN's per-persona contract via base-class fallback
  only. Added inline `expected_actions=` declarations to all 12
  packaged persona files; new
  `test_every_persona_file_declares_expected_actions_inline`
  asserts the inline declaration.
- **F-IR-04 `META_DOCUMENT_PRAGMA` wholesale loophole.** Pre-fix,
  any text containing the magic comment bypassed the static
  scan. Bounded to `META_DOCUMENT_ALLOWLIST` = {safety, reporting,
  expert-explainer}; pragma alone is now insufficient for bypass.
  Negative test asserts arbitrary skills with the pragma still
  scan.
- **F-IR-05 W-29-prep snapshot provenance gap.**
  `cli_boundary_table.md` + CARRY_OVER §2 W-29-prep row now name
  all three legitimate post-W-29-prep snapshot regenerations
  (45319da → 03fab4f → bd11be3); v0.1.14 W-29's go/no-go
  provenance is corrected.
- **F-IR-R2-01 ruff F541** on three non-interpolating f-string
  literals in `cli.py` introduced by the W-AA/W-AD interlock fix
  at IR r1.
- **Carry-over closure (v0.1.12 RELEASE_PROOF §5):**

| Item | Disposition |
|---|---|
| W-Vb persona-replay end-to-end | partial-closure → v0.1.14 W-Vb-3 (P1+P4+P5 ship-set closed) |
| W-N-broader (49 sqlite3 leaks) | closed-this-cycle (50 sites + 2 ancillary) |
| W-FBC-2 (multi-domain F-B-04) | closed-this-cycle (option A, all 6 domains) |
| CP6 §6.3 strategic-plan edit | closed-this-cycle (verbatim application) |

### Notes

- 16 of 17 W-ids closed-this-cycle; 1 partial-closure (W-Vb,
  9-persona residual fork-deferred to v0.1.14 W-Vb-3 with explicit
  destination cycle); 1 pre-cycle ship (W-CF-UA, catalogue
  completeness only — shipped in v0.1.12.1 hotfix, cherry-picked
  to this branch for code+test parity).
- No new Settled Decisions (D-entries) this cycle. D14's
  empirical-settling shape commentary is now thrice-validated
  across substantive cycles.
- No new SQLite migrations.
- Cycle-order inversion: IR ran *before* RELEASE_PROOF / REPORT /
  CHANGELOG authoring, allowing Codex's findings to shape the
  ship artifacts directly. Worth carrying to v0.1.14 by default.

---

## [0.1.12] - 2026-04-29

> **Theme.** Carry-over closure + trust repair. No release-blocker
> workstream by design. Ten workstreams across docs / governance
> / per-domain code / mypy / demo packaging.
>
> **Tier (per CP3 D15 introduced this cycle):** substantive.
>
> **D14 plan-audit:** PLAN_COHERENT at round 4, matching the
> v0.1.11 empirical 10 → 5 → 3 → 0 settling signature across 4
> rounds (18 findings cumulative). All six cycle proposals
> (CP1-CP6) accepted.
>
> **Phase 0 (D11) bug-hunt:** internal sweep + audit-chain probe
> + persona matrix all clean. Two findings absorbed (mypy +1/+1
> drift; W-N audit count 49+1 with deliberate fork to v0.1.13).
> Pre-implementation gate fired green.

### Added

- **`hai auth remove [--source garmin|intervals-icu|all]`**
  (W-PRIV) — subcommand on the existing `auth` namespace. Closes
  the privacy-doc claim that no removal command existed.
  Idempotent; only touches keyring (env-var creds untouched).
- **`hai today --verbose`** (W-FCC) — surfaces the
  `strength_status` enum surface as a footer. Closes F-C-05.
  Live classified-state-of-the-day rendering deferred to
  v0.1.13.
- **`hai daily --re-propose-all`** (W-FBC, partial closure of
  F-B-04) — flag accepted by the parser; round-trips through the
  daily report JSON as `re_propose_all_requested: bool`;
  capabilities-manifest-listed. **Report-surface only at v0.1.12;
  recovery prototype + multi-domain runtime enforcement deferred
  to v0.1.13 W-FBC-2** per F-IR-01 (originally framed as v0.1.12
  deliverable; synthesis-side wiring did not land — artifact set
  realigned at implementation review).
- **`STRENGTH_STATUS_VALUES`** constant + capabilities-manifest
  `enum_surface` annotation on `hai today` (W-FCC).
- **Packaged demo-fixture path + loader** (W-Vb partial closure,
  reconciliation C3) at `src/health_agent_infra/demo/fixtures/`
  + `core/demo/fixtures.py`. Wheel-install-reachable via
  `importlib.resources`. End-to-end persona-replay deferred to
  v0.1.13.
- **Six cycle proposals (CP1-CP6)** at
  `reporting/plans/v0_1_12/cycle_proposals/CP{1..6}.md`.
  CP1+CP2 paired AGENTS.md edit (lift cli.py-split + manifest-
  freeze deferrals). CP3 four-tier cycle-weight classification
  (D15). CP4 staged MCP-exposure plan (extends Wave 3). CP5
  v0.2.0 single-substantial-with-shadow shape. CP6 §6.3 framing
  edit (authored v0.1.12, applied v0.1.13).
- **`reporting/docs/supersede_domain_coverage.md`** (W-FBC) —
  policy decision doc.

### Changed

- **D13 consumer-site symmetry** (W-D13-SYM) — recovery, running,
  sleep, stress `policy.py` now wrap every `t["policy"][...]`
  read in `coerce_int / coerce_float`. AST contract test prevents
  regression.
- **Mypy clean baseline** (W-H2) — 22 errors → 0 across 12 files
  (target was ≤5).
- **AGENTS.md "Settled Decisions"** updated per CP1+CP2 (W29/W30
  scheduled, no longer deferred) + CP3 (D15 four-tier
  classification added). Ship-time freshness checklist appended
  to "Release Cycle Expectation."
- **strategic_plan_v1.md** Wave 3 row extended with MCP staging
  (CP4); Wave 2 theme extended with shadow-by-default judge
  framing (CP5).
- **tactical_plan_v0_1_x.md** §3 rebaselined to actual carry-over
  scope; §6 v0.2.0 reshaped per CP5 (W58D + W58J split,
  `HAI_W58_JUDGE_MODE` flag).
- **ROADMAP.md** rewritten Now/Next per CP4 + CP5.
- **AUDIT.md** added v0.1.10 + v0.1.11 entries.
- **success_framework_v1.md** §3.5 anti-gaming note on defer rate
  (reconciliation C9).
- **`reporting/docs/privacy.md`** updated for `hai auth remove`
  and "forget one day" deferral.

### Carry-over closure (v0.1.11 named-defers)

| Item | Disposition |
|---|---|
| W-Vb (demo polish) | partial-closure; persona-replay → v0.1.13 |
| W-H2 (mypy stylistic) | closed (22 → 0) |
| W-N broader gate | named-deferred to v0.1.13 W-N-broader |
| F-A-04 / F-A-05 | closed (W-H2 covers) |
| F-B-04 (supersede coverage) | partial-closure (W-FBC); multi-domain → v0.1.13 W-FBC-2 |
| F-C-05 (strength_status surface) | closed (W-FCC) |

### Deferred (named-deferred to next cycle)

- **W-N-broader** (49 sqlite3 connection-lifecycle leaks) →
  v0.1.13.
- **W-Vb persona-replay end-to-end** → v0.1.13.
- **W-FBC-2 multi-domain F-B-04 closure** → v0.1.13.
- **CP6 §6.3 strategic-plan edit application** → v0.1.13.

### Settled decisions added

- **D15 (v0.1.12) Cycle-weight tiering** — substantive / hardening
  / doc-only / hotfix. RELEASE_PROOF declares chosen tier.
- D14 confirmed at the v0.1.11 4-round halving signature for the
  second time — empirically validated norm.

---

## [0.1.11] - 2026-04-28

> **Theme.** Audit-chain integrity (W-E + W-F release-blockers)
> + the `hai demo` mode introduced for safe demos and onboarding
> + 7 demo-run findings absorbed from the 2026-04-28 live demo.

> **Cycle pattern note.** First release shipped under the D14
> pre-cycle Codex plan-audit pattern. Plan-audit settled at round
> 4 (PLAN_COHERENT) with 18 findings closed before any code
> changed. See `reporting/plans/v0_1_11/codex_plan_audit_response*.md`.

### Added

- **`hai demo {start, end, cleanup}`** (W-Va, release-blocker) —
  isolated demo sessions with multi-resolver override. Real
  `~/.health_agent` tree, real `state.db`, and real
  `thresholds.toml` stay byte-identical for the duration of any
  demo session. Fail-closed marker contract.
- **`hai doctor --deep`** (W-X) — live-API auth probe via the
  new `Probe` protocol. `LiveProbe` for real mode; `FixtureProbe`
  with hard no-network assertion in demo mode.
- **`hai intake gaps --from-state-snapshot`** (W-W) — derive gaps
  from latest accepted state without fresh wearable evidence.
  48h staleness gate. Single-read-transaction contract.
- **`--as-of` canonical alias on `hai pull` + `hai explain`** (W-Y).
- **State-fingerprint primitive** on `daily_plan` (W-E,
  release-blocker; migration 022). Re-run with same state is
  no-op; with different state auto-supersedes with `_v<N>`.
- **Capabilities manifest exposes `domain_proposal_contracts`**
  (W-S, F-DEMO-02). Backwards-compatible additive (W30 preserved).
- **R-volume-spike minimum-coverage gate** (W-B) — closes the
  false-spike-on-first-session-back pattern that hit 6 personas +
  Dom's real state in the 2026-04-28 demo.
- **Persona matrix expanded 8 → 12** (W-O): P9 older female
  endurance, P10 adolescent recreational, P11 elevated-stress
  hybrid, P12 vacation-returner.
- **Property-based tests for the policy DSL** (W-P).
- **Persona harness drift guards** (W-S, F-CDX-IR-06).
- **`reporting/docs/demo_flow.md`** (W-Z).

### Changed

- **`hai {daily, synthesize} --supersede`** on a date with no
  canonical plan now exits USER_INPUT (W-F, release-blocker).
- **`hai daily` re-run against changed state** auto-supersedes
  with `_v<N>` instead of overwriting the canonical (W-E).
- **Running rollup provenance** (W-R): rollup-derived rows stamp
  `derivation_path='running_sessions'` and populate
  `session_count` + `total_duration_s`.

### Fixed

- **Mypy correctness errors** (W-H1, F-A-03/06/07/11): 39 → 21
  errors (remaining 21 stylistic-class, deferred to v0.1.12).
- **Bandit security findings**: B608 (16 sites) + B310 + B108
  audited site-by-site with rationale. `bandit -ll` on `src/`: 0
  unsuppressed.

### Deferred (named to v0.1.12)

- **W-Vb** (`hai demo` polish: persona fixtures + archive +
  cleanup polish) — per the named-defer ship-gate.
- **W-N broader gate** — `-W error::Warning` cleanup is a multi-
  day systemic refactor.
- **F-A-04 / F-A-05 + remaining mypy stylistic** errors deferred
  to v0.1.12 W-H2.

### Settled decisions added to AGENTS.md

- **D13** — Threshold-injection seam is trusted-by-design.
- **D14** — Pre-cycle Codex plan-audit is permanent pattern.

### Test surface

2202 → 2347 passing (+145 across 13 new test files). 0 regressions.

---

## [0.1.10] - 2026-04-28

> **Theme.** Persona harness, running-activity rollup wire, and
> threshold-consumer type hardening. v0.1.10 introduces the
> `verification/dogfood/` persona harness as permanent regression
> infrastructure, wires the existing-but-unused `running_activity`
> daily aggregator into the clean flow (closes a load-bearing gap
> that affected every intervals.icu user), and hardens threshold
> consumers against bool-as-int silent coercion (D12).
>
> **Scope discipline.** Two audit-chain integrity items uncovered in
> the pre-PLAN bug hunt (W-E same-day state-change re-synth and W-F
> version-counter sequencing) are explicitly **deferred to v0.1.11**.
> The original v0.1.10 framing as a "correctness + audit-chain
> integrity release" overpromised on that second axis; this release
> ships the correctness work and the persona infrastructure.
> Audit-chain integrity is the v0.1.11 thesis.
>
> **Audit history.** Codex round 1 returned `DO_NOT_SHIP` against
> the initial cut, surfacing four blockers: W-C was tested at the
> policy boundary but never wired into `build_snapshot`; the W-A
> sweep missed live threshold consumers; the test suite was not
> hermetic under configured live credentials; and the audit-chain
> deferral did not match the release framing. Round 2 closes all
> four. Detail in `reporting/plans/v0_1_10/`.

### Added

- **Persona dogfood harness** — `verification/dogfood/` with 8 synthetic
  user personas spanning age, sex, sport mix, data source, and history
  length. Drives each persona through `pull → clean → daily → today →
  explain` against an isolated state DB. Permanent regression
  infrastructure; not part of CI today (matrix runs take minutes), but
  available as a pre-flight check on every release.
- **`coerce_int` / `coerce_float` / `coerce_bool` helpers** in
  `core/config.py` with new `ConfigCoerceError`. Strict numeric
  coercion that rejects bools (closes v0.1.9 backlog B1 type-hardening).
- **Pre-PLAN audit pattern** — `reporting/plans/v0_1_10/PRE_AUDIT_PLAN.md`
  introduces a structured bug-hunt phase before formal PLAN.md, ensuring
  release scope reflects systematic audit output rather than opportunistic
  findings.

### Fixed

- **Running domain reads zero history despite logged activities (F-C-03)** —
  `aggregate_activities_to_daily_rollup` was implemented but never invoked
  in the clean flow. Wired into `cmd_clean` for both today and historical
  dates with field-name mapping (`total_distance_m` → `distance_m`).
  Personas with logged runs now produce useful running recommendations
  instead of universal defer. Affects every intervals.icu user.
- **R-extreme-deficiency partial-day false positives (B1, F-CDX-IR-01)** —
  `_r_extreme_deficiency` gains `meals_count` + `is_end_of_day` parameters
  with new `r_extreme_deficiency_min_meals_count: 2` threshold default.
  Suppresses escalation when fewer than the minimum meals have been
  logged unless the caller has asserted end-of-day. Reproduces +
  fixes the morning-briefing 06:32 false alarm. The Codex round-1
  audit caught that the initial cut wired the gate at the policy
  boundary only; round 2 plumbs `meals_count` + a clock-derived
  `is_end_of_day` through `build_snapshot` so the gate activates
  in normal `hai daily` flow. New
  `r_extreme_deficiency_end_of_day_local_hour: 21` threshold
  controls the cutover (past dates always treated as end-of-day).
- **Activity projector `KeyError` rollbacks (F-C-01, F-C-02)** —
  `project_activity` now validates required fields up front via
  `_validate_activity_payload` and raises typed
  `ActivityProjectorInputError` instead of a generic `KeyError` that
  bubbles up as a "rolled back" warning. Validates `activity_id`,
  `user_id`, `as_of_date`, `raw_json`.
- **Threshold consumer type hardening (F-A-01, F-CDX-IR-02,
  F-CDX-IR-R2-01)** — Three rounds, ending with an architectural
  fix.
  - **Round 1** added `coerce_int` / `coerce_float` / `coerce_bool`
    helpers in `core/config.py` and applied them to ≥12 threshold-
    consumer sites across `core/synthesis_policy.py` (x7, x2, x3a,
    x3b), `domains/nutrition/policy.py`, and
    `domains/nutrition/classify.py`. Closes the named raw-cast
    survivors at the call site.
  - **Round 2** swept additional named survivors per Codex audit:
    `synthesis_policy.py` x4 / x5 / x6a / x6b, plus
    `core/pull/garmin_live.py` retry config (4 helpers). Added a
    runtime grep guard `test_d12_no_raw_cfg_coerce.py` for
    `(int|float|bool)(cfg…)` patterns.
  - **Round 3 (architectural close).** Codex round 2 caught that
    the grep guard misses direct numeric leaf consumers
    (`protein_ratio < cfg["low_max_ratio"]`,
    `float(targets["protein_target_g"])`) — Python bools are
    numeric, so a TOML override of `low_max_ratio = true` would
    silently flow as `1` regardless of the helper sweep. Round 3
    adds **load-time threshold-type validation** in
    `core/config.load_thresholds`: after the user TOML is
    deep-merged over `DEFAULT_THRESHOLDS`, every leaf is checked
    against the default's type with strict bool detection
    (`type(x) is bool`). Bool-on-numeric and numeric-on-bool
    overrides raise `ConfigCoerceError` at load time. Consumers
    never see a bool-shaped numeric value regardless of how they
    read the leaf — coercer call, comparison, arithmetic, or dict
    indexing. Test surface: 28 new validator unit + integration
    tests in `test_load_time_threshold_validation.py`. Also
    finished the consumer-side W-A sweep in
    `domains/nutrition/classify.py` (ratio thresholds, targets,
    nutrition-score penalties) for self-documenting consistency.
- **`hai intake gym --session-json` accepts `exercise` alias (F-C-08)** —
  Schema normalisation: `exercise` is accepted as alias for the
  `exercise_name` per-set key, matching the per-set CLI flag name.
- **Ruff cleanup** — 24 of 24 findings closed (`ruff check`: 0).
  23 auto-fixed (unused imports + unused locals). One required manual
  intervention: `applied_action_mutation` in `core/synthesis_policy.py`
  was confirmed dead code via grep, deleted with explanatory comment.
- **Test-suite hermeticity (F-CDX-IR-03)** — `verification/tests/`
  now sets an autouse pytest fixture in `conftest.py` that disables
  `_intervals_icu_configured()` by default. Eight tests in
  `test_intake_readiness`, `test_intake_gaps`, and
  `test_recovery_readiness_v1` previously hit the live intervals.icu
  API with `HTTP 403` whenever the developer machine had real
  credentials configured, invalidating the `2169 passed` proof claim
  for anyone running on a populated keychain. Tests that exercise
  the resolver's auto-default path opt back in via their own
  monkeypatch.

### Documented

- **27 audit findings** consolidated in
  `reporting/plans/v0_1_10/audit_findings.md` across Phase A (internal
  sweep), Phase B (audit-chain integrity probe), and Phase C (persona
  dogfood matrix). 9 fixed in v0.1.10, 18 deferred to v0.1.11.
- **`verification/dogfood/README.md`** — harness usage + isolation
  discipline + persona authorship guide.
- **`reporting/plans/v0_1_10/PLAN.md`** — workstream catalogue,
  acceptance criteria, sequencing.
- **`reporting/plans/v0_1_10/codex_audit_prompt.md`** — external audit
  prompt for the post-fix Codex review. Bug-hunt question stays
  scoped to bugs the internal sweep + persona matrix did not catch.

### Explicitly deferred to v0.1.11

The pre-PLAN bug hunt surfaced two audit-chain integrity issues
that were initially in-scope but did not land cleanly. Codex round 1
challenged the deferral as incompatible with the original release
framing; round 2 accepts the challenge by **rescoping v0.1.10 away
from the audit-chain integrity claim**. v0.1.11 is the audit-chain
integrity release.

Tagged **release-blocker-class** for v0.1.11 — these are not
opportunistic backlog items, they gate the next ship:

- **Same-day state-change re-synth (W-E / B7 / F-B-02)** — When the
  user re-logs intake the same day, `hai daily` should produce a
  superseded `_v<N>` plan with refreshed rationale. Today the
  rationale prose is stale. Synthesis-path semantic; needs design
  discussion before code.
- **Audit-chain version-counter integrity (W-F / F-B-01)** — A
  `_v0 → _v3` jump (skipping `_v2`) was observed during the
  audit-chain probe. Root cause not yet localised; v0.1.11 starts
  with the investigation.

Tagged backlog (lower priority):

- **R-volume-spike minimum-coverage gate (W-B / B2 / F-C-04)** —
  Confirmed across 6 personas; fix shape needs strength-domain
  freshness-model alignment.
- **Running-rollup provenance completeness (F-CDX-IR-05)** —
  `aggregate_activities_to_daily_rollup` computes `total_duration_s`
  + `session_count` but `project_accepted_running_state_daily`
  hardcodes both to `None` and stamps `derivation_path="garmin_daily"`
  even for rows derived from `running_activity`.
- **Persona harness drift guards (F-CDX-IR-06)** — synthetic-skill
  action tokens + schema versions are validated post-facto via
  `hai propose` failure rather than directly against the runtime
  contract.
- **Mypy sweep (W-H)** — ~30 errors remaining; W-A coercer addressed
  several incidentally.
- **Bandit B608/B310 audits (W-K, W-L)** — 17 findings to triage.
- **Pytest unraisable warning (W-N)** — v0.1.9 carry-over.

### Test surface

```
Pre-cycle:    2133 passed, 2 skipped
Post-round-1: 2169 passed, 2 skipped   (+36 tests)
Post-round-2: 2174 passed, 2 skipped   (+5 tests)
Post-round-3: 2202 passed, 2 skipped   (+28 tests)
```

New test files (round 1): `test_config_coerce.py` (24),
`test_partial_day_nutrition_gate.py` (5),
`test_running_activity_projector.py` (7).
New test files (round 2):
`test_partial_day_nutrition_snapshot_wire.py` (4),
`test_d12_no_raw_cfg_coerce.py` (1).
New test files (round 3):
`test_load_time_threshold_validation.py` (28).

The v0.1.10 suite is hermetic regardless of whether the developer
machine has live intervals.icu credentials configured.

---

## [0.1.9] - 2026-04-26

> **Theme.** Hardening and governance closure. v0.1.9 closes the
> post-v0.1.8 P0/P1 findings from parallel Codex + Claude reviews
> without adding new product features.

### Fixed

- **W57 runtime gate closure** - `hai intent archive` and
  `hai target archive` are now marked `agent_safe=false`, and all four
  intent/target activation/deactivation handlers (`commit` + `archive`)
  require either interactive stdin or `--confirm`. Non-interactive
  callers without confirmation exit `USER_INPUT` without mutating state.
- **Skill overlay fail-loud** - synthesis skill overlays may only set
  `rationale`, `uncertainty`, and `follow_up.review_question`. Attempts
  to edit runtime-owned fields, reference unknown recommendation ids, or
  pass malformed allowed fields now raise
  `skill_overlay_out_of_lane` before the synthesis transaction opens.
- **Proposal/recommendation validator hardening** - `rationale` and
  `uncertainty` must be `list[str]`; `policy_decisions[]` entries must
  have string `rule_id` / `decision` and string `note` when present; and
  recommendation `follow_up.review_question` must be a non-empty string.
  Proposal and recommendation banned-token sweeps now share the same
  text-surface walker.
- **Direct synthesize parity** - direct `hai synthesize` now enforces the
  same expected-domain proposal completeness gate as `hai daily` by
  default, while `--domains <csv>` narrows and `--domains ''` explicitly
  opts out. Snapshots always populate per-domain `classified_state` and
  `policy_result`, so direct synthesis sees the same Phase A X-rule
  inputs as daily.
- **Pull/clean provenance** - `hai daily` writes `sync_run_log` rows like
  `hai pull`, including partial-pull status; clean projection failures
  now fail closed instead of allowing planning over stale accepted state;
  identical evidence replays produce deterministic raw provenance ids;
  intervals.icu activities failures mark the pull partial.
- **Safety skill prose** - the safety skill now distinguishes
  R-rule coverage blocks from X-rule block-tier escalation, and it
  describes nutrition v1 as bounded macro alignment rather than blanket
  "no macros" advice.

### Changed

- Promoted the README daily-loop explanation above install and tightened
  it around v0.1.9 fail-closed clean and direct-synthesize completeness
  semantics.
- Regenerated `reporting/docs/agent_cli_contract.md` for `hai 0.1.9`.

### Deferred

- W52 weekly review, W53 insight proposal ledger, and W58 LLM-judge
  factuality remain post-hardening work. Global threshold-runtime type
  hardening also remains tracked in the v0.1.9 backlog for follow-up.

## [0.1.8] — 2026-04-25

> **Theme.** Plan-aware feedback visibility. Adds the intent +
> target + data-quality ledgers, the code-owned review-summary
> tokens, four new `hai stats` modes (outcomes / baselines / funnel
> / data-quality), config validate + diff, the `hai daily --auto
> --explain` thick JSON, and the synthesis-skill scoring harness.
> Outcomes are visibility-only — they never silently mutate
> thresholds, classifiers, policy, X-rules, confidence, intent, or
> targets in v0.1.8.

### Added

- **Test fixture-factory module** (`verification/tests/_fixtures/`) — pure
  dict builders `make_intent_row`, `make_target_row`,
  `make_outcome_chain`, `make_data_quality_row` plus a SQLite
  `seed_outcome_chain` helper for the existing
  `recommendation_log → review_event → review_outcome` chain. Lands
  ahead of v0.1.8 W48–W51 per `reporting/plans/v0_1_8/PLAN.md` § 0
  fixture-factory precondition so the ~80–120 forthcoming tests share
  one seeding API. Smoke-covered by
  `verification/tests/test_fixture_factory.py`.

### Changed

- **`reporting/docs/non_goals.md`** (W57) — distinguishes
  *autonomous* training/diet plan generation (still forbidden) from
  *user-authored intent and targets* (now allowed via the W49 intent
  ledger and W50 target ledger). Adds an explicit "what is allowed"
  section so contributors don't misread the upcoming intent / target
  CLI surfaces as agent-proposed planning. Also clarifies what
  bounded wellness plan suggestions could look like later under new
  governance — none of which v0.1.8 ships.
- **`hai daily --user-id` help text** rephrased from "User whose
  plan to generate" to "User whose daily pipeline to orchestrate"
  (W57 acceptance — no CLI help implies autonomous plan generation).
- **Snapshot `schema_version` bumped from `state_snapshot.v1` →
  `state_snapshot.v2`** (W48). Additive transition: every v1 field
  is preserved unchanged; the v2 bump signals new
  `snapshot.<domain>.review_summary` blocks (W48). Future v0.1.8
  workstreams (W49/W50/W51) attach further additive blocks behind
  the same v2 signal.

### Added (cont'd)

- **Code-owned review summary builder** (W48,
  `core/review/summary.build_review_summary`). Reads
  `recommendation_log` + `review_event` + `review_outcome` for a
  rolling window and emits per-domain (or aggregate) summaries with
  stable visibility-only tokens
  (`outcome_pattern_recent_negative`,
  `outcome_pattern_recent_positive`, `outcome_pattern_mixed`,
  `outcome_pattern_insufficient_denominator`). Token thresholds live
  in `[policy.review_summary]` in `DEFAULT_THRESHOLDS` and are
  user-tunable via `thresholds.toml`. Skills can narrate the tokens
  but MUST NOT compute them or mutate actions from them — visibility
  only in v0.1.8.
- **`snapshot.<domain>.review_summary`** field attached to all six
  per-domain blocks by `build_snapshot` (W48). 13 regression tests
  in `verification/tests/test_review_summary.py` cover every token rule,
  window scoping, per-domain isolation, aggregate roll-up, re-link
  counter, threshold overrides, and snapshot integration.
- **`hai stats --outcomes [--domain <d>] [--since N] [--json]`**
  (W38). Read-only mode-switch on the existing `hai stats` command;
  emits the W48 review-summary either as the per-domain bundle plus
  aggregate roll-up (default) or as one summary scoped to a single
  domain. Markdown table on TTY, structured dict on `--json`.
  Capability manifest documents the new flags;
  `agent_cli_contract.md` regenerated.
- **Intent ledger MVP** (W49, migration 019). New `intent_item`
  table + `core/intent/` module (`add_intent`, `list_intent`,
  `list_active_intent`, `archive_intent`, `supersede_intent`).
  CLI: `hai intent training add-session`, `hai intent training list`,
  `hai intent sleep set-window`, `hai intent list`, `hai intent
  archive`. Records user-authored or `agent_proposed` intent only —
  outcomes never auto-mutate intent. Replacements use
  archive/supersession, not destructive UPDATE. Snapshot integration:
  new top-level `snapshot.intent` block carries every active row
  whose `[scope_start, scope_end]` covers `as_of_date`. Per-domain
  readiness skills' `allowed-tools` extended with
  `Bash(hai intent list *)` so they can consume the snapshot's
  intent context. 13 new tests in
  `verification/tests/test_intent_ledger.py`.
- **Target ledger MVP** (W50, migration 020). New `target` table
  + `core/target/` module (`add_target`, `list_target`,
  `list_active_target`, `archive_target`, `supersede_target`).
  CLI: `hai target set`, `hai target list`, `hai target archive`.
  Wellness support, NOT medical prescriptions — every row has
  reason, source, effective date, and review date. Outcomes may
  propose target *review* later (post-v0.1.8) but must NEVER
  auto-mutate a target value. Snapshot integration: new top-level
  `snapshot.target` block carries every active row whose effective
  window covers `as_of_date`. Per-domain readiness skills'
  `allowed-tools` extended with `Bash(hai target list *)`. 13 new
  tests in `verification/tests/test_target_ledger.py`.
- **Data quality ledger** (W51, migration 021). New
  `data_quality_daily` table + `core/data_quality/` projector +
  `hai stats --data-quality` CLI mode. Per-source / per-domain row
  shape: `coverage_band`, `missingness`, `source_unavailable`,
  `user_input_pending`, `cold_start_window_state`. Snapshot
  integration: `snapshot.<domain>.data_quality` block carries the
  fields without requiring the projector to have run. Subsumes the
  v0.1.7 cold-start visibility gap — `cold_start_window_state` is
  pinned by `verification/tests/test_data_quality_cold_start_consistency.py`
  to match `snapshot.<domain>.cold_start` per the W51 maintainer
  refinement. 7 new tests across `test_data_quality_ledger.py` +
  `test_data_quality_cold_start_consistency.py`.
- **`hai stats --baselines [--domain <d>] [--json]`** (W40). Mode
  on `hai stats` that emits today's per-domain bands, classified
  state, missingness, cold-start state, and threshold source paths
  so the user can inspect what numbers the runtime is using without
  reading SQL. Read-only; no recomputation in the CLI — every band
  is the snapshot's classification. 3 new tests in
  `verification/tests/test_cli_stats_baselines.py`.
- **`hai config validate` + `hai config diff`** (W39). Discoverable
  authoring + diffing for the user's `thresholds.toml`. Validate
  parses the TOML, walks every leaf, and reports `unknown_key` /
  `type_mismatch` / `toml_parse_error` issues with paths. Default
  mode warns on unknown keys; `--strict` makes them blocking. Diff
  shows default vs override vs effective for every overridden leaf
  (and flags unknown keys with `key_known=false`). Outcomes never
  write thresholds — those paths only land via the existing
  `hai config init` scaffold. 7 new tests in
  `verification/tests/test_cli_config_validate_diff.py`.
- **`hai stats --funnel [--since N] [--json]`** (W46). Mode on
  `hai stats` that aggregates `runtime_event_log.context_json` for
  `command='daily'` runs in the window: daily run count,
  overall_status histogram, missing-domain frequency,
  blocking-action count. Closes the v0.1.7 proposal-gate telemetry
  carry-over. 2 new tests in
  `verification/tests/test_cli_stats_funnel.py`.
- **`hai daily --auto --explain` thick JSON** (W43). New
  `--explain` flag on `hai daily` adds a per-stage `explain` block
  to the output (pull / clean / snapshot / gaps / proposal_gate /
  synthesize) with `schema_version="daily_explain.v1"`. Reads
  already-computed stage data; never recomputes or fabricates
  fields. Plain `hai daily` and `hai daily --auto` (no `--explain`)
  remain byte-identical — the block is opt-in via the explicit
  flag. 3 new tests in `verification/tests/test_cli_daily_auto_explain.py`.
- **Skill harness extended to running** (W41). Added `running` to
  `SUPPORTED_DOMAINS`, `_running_snapshot_block` driving the real
  `derive_running_signals` + `classify_running_state` +
  `evaluate_running_policy`, 4 scenarios covering clean /
  insufficient-signal / policy-forced (R-acwr-spike) / cross-domain
  coupling (recovery=impaired → running holds), and
  `rubrics/running.md`. Replay mode runs in normal CI; live capture
  remains operator-gated via `HAI_SKILL_HARNESS_LIVE=1`.
- **Synthesis-skill scoring harness** (W42). New
  `verification/evals/synthesis_harness/` with `runner.py`,
  `rubrics/synthesis.md`, and 3 fixture scenarios (clean / partial
  X1a soften / escalated X3b block). Scorer applies four rubric
  invariants over a candidate synthesis output: every Phase A firing
  cited or summarised, no invented X-rule, no invented band, no
  action mutation claimed by prose. 7 new tests in
  `verification/tests/test_synthesis_harness.py` exercise both
  passing-output and each failure mode so the rubric localises the
  broken rationale line.
- **W0.1.8 replay / property tests** (W45). New
  `verification/tests/property/test_v0_1_8_replay_properties.py` pins
  determinism contracts for the new state surfaces: intent
  supersession-chain replay, late-arriving target does not
  retroactively change a past snapshot, intent / target
  active-at-date are stable across repeated calls, review-summary
  replay against the same outcome chain produces identical
  counts/tokens, and the same summary call is order-stable. 6 new
  tests.
- **Standards mapping doc** (W55,
  `reporting/docs/standards_mapping.md`). Maps HAI's evidence /
  accepted-state / recommendation / plan / review / intent /
  target / data-quality / provenance ledgers to FHIR + Open
  mHealth + Open Wearables analogues with explicit "NOT a FHIR
  dependency" disclaimer + reasoning (local-first, governed
  invariants, small-team-maintainable, no medical claims). Doc-only
  addition; helps a new contributor decide whether to align a new
  field with FHIR vocabulary without thinking they MUST.

### Fixed (Codex round-1 audit response)

- **`hai stats --data-quality` no longer mutates state** (Codex
  P1-1). Lazy-projection moved out of the read-only stats surface
  into the `hai clean` write path where it belongs per PLAN.md
  § 2 W51. Read-only contract restored; pinned by
  `test_cli_data_quality_is_read_only_on_fresh_db` which asserts
  zero rows in `data_quality_daily` after a stats call against a
  fresh DB.
- **Agent-proposed intent / target rows can no longer land
  active** (Codex P1-2). W57 invariant enforced at both the store
  (validators raise `IntentValidationError` /
  `TargetValidationError` on `source != "user_authored"` +
  `status="active"`) and the CLI (USER_INPUT exit + stderr
  message). New `hai intent commit --intent-id ID` and `hai target
  commit --target-id ID` commands provide the user-gated
  promotion path; both are explicitly marked `agent_safe=False`
  in the capability manifest. 12 new regression tests across
  intent + target ledgers.
- **`hai daily --auto --explain` snapshot block now carries the
  W48 signals it promised** (Codex P2-1). Snapshot stage write
  populated with `domains_present`, `missingness_per_domain`,
  `classified_bands_per_domain`, `review_summary_tokens_per_domain`.
  Test asserts values, not just keys.
- **Skill-harness live mode dispatches on scenario domain**
  (Codex P2-2). `_LIVE_SKILL_BY_DOMAIN` table + helper select the
  correct SKILL.md for each domain; running scenarios now invoke
  `running-readiness` rather than silently falling back to
  recovery.
- **`hai config validate` enforces numeric ranges on
  `[policy.review_summary]`** (Codex P2-3). New `range_violation`
  issue kind covers `window_days >= 1`, non-negative
  denominators / thresholds, mixed-token bounds in `[0, 1]` with
  `lower <= upper`. Always blocking; not gated on `--strict`.
- **Snapshot schema v2 transition documented in
  `agent_integration.md`** (Codex P3-1). New section lists the
  four additive fields (`review_summary`, `data_quality`,
  `intent`, `target`) and gives v1 consumers explicit
  pin-or-ignore guidance.

### Fixed (Codex round-2 audit response)

- **`hai clean` no longer silently swallows data-quality
  projection failures** (Codex R2-1). Replaces the bare
  `except: pass` with a stderr warning that names the date,
  user, exception class, and instructs the reader that
  `hai stats --data-quality` will report empty rows for the date
  until the projection is re-run. Accepted-state writes still
  commit (data-quality is best-effort), but the failure is
  visible.
- **Agent-proposed supersede defers deactivation to user commit**
  (Codex R2-2). `supersede_intent` and `supersede_target` no
  longer flip the old row to `superseded` when the new row's
  `source != "user_authored"`. The new row is inserted as
  `proposed` with the supersedes link; `commit_intent` /
  `commit_target` look up the link and atomically flip the parent
  to `superseded` in the same transaction at user-commit time.
  The W57 invariant ("agent cannot deactivate user state without
  explicit user commit") is now enforced at three boundaries:
  insert, supersede, commit. 5 new regression tests.
- **`hai config validate` rejects booleans as numeric thresholds**
  (Codex R2-3). Python's `isinstance(True, (int, float))` is
  True; without the guard a user could land `window_days = true`
  silently coerced to 1. Both the type check and the range helper
  now use a `_is_real_number(v)` predicate that excludes bools.
  3 new regression tests.
- **`_emit_data_quality_stats` docstring updated** (Codex R2-4
  nit) to reflect the strictly-read-only contract instead of the
  removed lazy-projection behaviour.

### Fixed (Codex round-3 audit response)

- **Runtime threshold resolver rejects bool-shaped numeric
  overrides** (Codex R3-1, NEW_ISSUE_DISCOVERED_LATE). The R2-3
  fix blocked bools at the validator surface; this closes the
  same class of bug at the runtime surface. New
  `ReviewSummaryThresholdError` raised by `_coerce_int` /
  `_coerce_float` in `core/review/summary.py` whenever a
  `policy.review_summary` leaf is a bool or a non-numeric type.
  Error message names `hai config validate` as the diagnostic
  tool so users hitting the runtime error have a clear next
  action. Defence-in-depth: every entry point that touches
  `policy.review_summary` (validator + runtime resolver + test
  fixtures) now rejects the same input shape. 6 new regression
  tests pinning the runtime bool / non-numeric rejection.

---

## [0.1.7] — 2026-04-25

### Added

- **`hai daily --auto`** emits a versioned `next_actions[]` manifest
  (`schema_version: next_actions.v1`) alongside the stage report
  (W21). Each action carries a typed `kind`, `reason_code`,
  `command_argv` (or `command_root` + `command_template`), `blocking`
  / `safe_to_retry` hints, and an `after_success` routing pointer. An
  agent can plan a fixture day end-to-end from the manifest alone —
  proven by `verification/tests/test_daily_auto_manifest_fixture.py` (W35).
- **`hai planned-session-types`** read-only command surfaces the
  canonical vocabulary for `--planned-session-type` so agents can
  discover the recognised tokens without README lookup (W33).
- **`hai capabilities --json`** alias accepted (Codex r3 must-fix:
  was previously argparse error 2 even though docs cited it).
- **`hai state migrate`** now refuses on a DB with gaps in the
  applied migration set (W23). New
  `apply_pending_migrations(..., strict=True)` +
  `SchemaVersionGapError` for library callers.
- **Cold-start policy matrix** documented at
  `reporting/docs/cold_start_policy_matrix.md` (W24) with a test
  pinning the per-domain decisions.
- **`runtime_event_log.context_json`** carries the daily
  proposal-gate outcome so future telemetry surfaces can query
  durable state (W21 prerequisite for W28).

### Changed

- **`hai intake nutrition`** now requires `--replace` to overwrite
  an existing same-day row (W34). Same-day silent supersede was a
  data-integrity footgun for agents treating the command as a
  per-meal logger.
- **`hai daily` capabilities annotation** correctly lists
  `incomplete` as a possible `overall_status` (Codex r3 must-fix).
- **`record_review_outcome`** validates the constructed payload
  before the JSONL append — defence-in-depth so direct Python
  callers can't bypass the v0.1.6 W12 validator (Codex r3 P1).
- **`daily-plan-synthesis` skill** `allowed-tools` broadened from
  flag-constrained patterns to `Bash(hai synthesize *)` (W25 +
  Codex r2 W16). The flag-constrained patterns may have silently
  blocked the skill's own examples under Claude Code's permission
  matcher; broadening + a prose invariant is the safer fix.
- **Source-default semantics** sweep across `hai daily` parser
  help, `intent-router` skill, `agent_integration.md`, and the
  generated capabilities manifest (W32). All now describe the
  v0.1.6+ resolution chain consistently.
- **README cheat sheet** rewritten to reflect every v0.1.6 +
  v0.1.7 surface change.

### Fixed

- **`hai propose` race-path regression** (W26): when
  `project_proposal` raises `ProposalReplaceRequired` past the
  pre-flight canonical-leaf check, the handler returns
  `USER_INPUT` with a clear "JSONL durable, run --replace or
  reproject" stderr instead of silently logging success.
- **Stale comments** in projector.py + expert-explainer skill +
  intent-router rewritten (Codex r3 nits).

### Skill ↔ CLI drift validator

- Extended to inspect `allowed-tools` frontmatter for
  order-sensitive permission patterns that may block their own
  skill-body examples (W25 / Codex r2 W16).

---

## [0.1.6] — 2026-04-25

### Major: post-audit-cycle release

13 workstreams shipped against the consolidated punch list from
three audit rounds (Codex r1 stale-branch + internal
cross-validation + Codex r2 on the correct branch + Codex r3
implementation review):

- **W11** — `_load_json_arg` helper + `main()` exception guard. No
  CLI handler can produce an uncaught Python traceback.
- **W12** — Review-outcome validation: `core/writeback/outcome.py`
  + `validate_review_outcome_dict`. Strict-bool
  `followed_recommendation` enforcement closes the JSONL/SQLite
  truth-fork bug.
- **W10 + W4** — `hai daily` proposal-completeness gate. Three
  statuses (`awaiting_proposals` / `incomplete` / `complete`).
- **W2** — `hai intake gaps` refuses without `--evidence-json`,
  emits `"computed": true` on OK path.
- **W7** — `core/paths.py` — `--base-dir` is now optional
  everywhere; defaults to `$HAI_BASE_DIR` or `~/.health_agent/`.
- **W3 + W18** — `scripts/check_skill_cli_drift.py` validator + CI
  gate. Fixed intent-router + reporting + expert-explainer drift.
- **W1** — `ReprojectOrphansError` + `--cascade-synthesis` flag.
- **W13** — `hai synthesize --bundle-only` refuses when
  `proposal_log` is empty.
- **W15** — `cmd_propose` does its own projection inline.
  `ProposalReplaceRequired` is fatal `USER_INPUT`; other failures
  fatal `INTERNAL`.
- **W17** — `hai research topics` + `hai research search`. Removed
  `Bash(python3 -c *)` from `expert-explainer`.
- **W19** — Reproject contract: "deterministic modulo projection
  timestamps."
- **W20** — `applied_schema_versions` + `detect_schema_version_gaps`;
  `hai doctor` warns on gaps below head.
- **W5** — `intervals_icu` is the implicit default when configured.
- **W9** — README rewrite: "Where your data lives," "How `hai daily`
  actually completes," "Calibration timeline."

Test count: 1844 → 1921 (+77 new tests). Zero locked broken
behaviours remain. v0.1.7 lifts the count to 1943.

---

## [0.1.5] — 2026-04-24

Supersedes the earlier `0.1.4` that shipped to PyPI from commit
`81997aa` before this work landed. PyPI release versions are immutable
(can't overwrite or unpublish cleanly), so the v0.1.4 planning scope
(safety closure + activity pull + proposal recovery + privacy
hardening) ships to users as `0.1.5`. Internal planning documents
retain the `v0_1_4` path for historical continuity; public package
version is `0.1.5`.

The first release where the project's stated success criteria survive
an end-to-end audit. Closes the safety, recovery, privacy, and
wearable-data-reaches-agent gaps that the earlier `0.1.4` implicitly
assumed.

Full detail: [`reporting/plans/v0_1_4/release_notes.md`](reporting/plans/v0_1_4/release_notes.md).

### Added

- **Activity pull pipeline** — intervals.icu `/activities` endpoint wired through pull → clean → snapshot. New `running_activity` table (migration 017), `IntervalsIcuActivity` typed dataclass, structural signals (`z4_plus_seconds_today`, `z4_plus_seconds_7d`, `last_hard_session_days_ago`, `today_interval_summary`, `activity_count_14d`) for the running classifier.
- **Intake-gaps surface** — new `core/intake/gaps.py` + `hai intake gaps` CLI + `hai daily` `gaps` stage. Agent-driven session-start protocol in `merge-human-inputs` skill: read gaps, compose ONE consolidated question, route the answer.
- **`hai today`** — first-class non-agent-mediated user surface (renders the canonical plan in markdown / plain / json).
- **`hai propose --replace`** — explicit revision of the canonical leaf per D1 re-author semantics.
- **`hai synthesize --supersede`** — keeps prior plan, writes new at `<canonical_id>_v<N>`.
- **`hai explain --operator`** — canonical operator-report flag.
- **Privacy hardening** — `core/privacy.py` enforces 0o700 directories + 0o600 files on POSIX across DB, JSONL audit logs, intake roots. `reporting/docs/privacy.md` covers what's stored / where / inspect / export / delete / migrate.
- **D1–D4 design docs** — re-author semantics, intake write paths, user-facing narration, cold-start coverage.
- **Five new e2e test scenarios** — re-author journey, first-run user, credential lifecycle, multi-day review, running activity journey.
- **Snapshot golden tests** — five `hai today --format plain` goldens (green, mixed, no-plan, cold-start, superseded).
- **Cold-start mode** — 14-day per-domain detection; running + strength + stress get coverage relaxation when intent is declared; nutrition stays strict.
- **`hai stats`** — credential-aware sync freshness; `stale_credentials` status when latest sync's source is now uncredentialed.
- **`hai capabilities` `flags[]`** — every argparse flag round-trips into the manifest; `output_schema` + `preconditions` opt-ins on five high-traffic commands.

### Changed

- **Synthesis safety closure** — `run_synthesis` now validates every final recommendation against `core/validate.py` before any partial commit. Per-domain `ALLOWED_ACTIONS_BY_DOMAIN` + `SCHEMA_VERSION_BY_DOMAIN` dispatch. Banned-token sweep covers `rationale` + `action_detail` + `uncertainty` + `follow_up.review_question`. Defensive guard rejects multiple active proposals per chain key. **Closes the safety regression introduced when D2 retired `hai writeback`.**
- **`hai state reproject`** — replays per-domain proposal JSONLs into `proposal_log`, preserving D1 revision chains in JSONL append order. Counts surface as `proposals` and `proposals_skipped_invalid`.
- **`hai pull --source intervals_icu`** — also calls `/activities`; daily-rollup intensity minutes derived from HR zone times.
- **`hai clean`** — aggregates today's activities into `accepted_running_state_daily` so the existing classifier sees real numbers.
- **Recovery-readiness skill** — rewritten to use `hai propose` (D2 contract); aligned with the other five domain skills.
- **README** — restructured with "Reading your plan" + "Recording your day" sections.

### Removed

- **`hai writeback`** — retired. `hai propose` + `hai synthesize` is the canonical commit path. `core/writeback/recommendation.py` deleted; `writeback-protocol` skill renamed to `review-protocol`.
- **`hai classify` / `hai policy`** — debug CLIs deleted per ADR. Use `hai state snapshot --evidence-json <path>`.

### Fixed

- Defer review questions are now per-domain (sleep no longer asks "Did today's session feel appropriate for your recovery?").
- `hai daily` no longer crashes on duplicate same-domain proposals (pre-flight rejection per D1; defensive guard in synthesis).
- Review outcomes against superseded plans auto-re-link to the canonical leaf instead of orphaning.
- Migration 015 backfill applies cleanly to pre-013 DBs.
- `hai capabilities --markdown` regenerated via in-process `cli.main` (not pipx) to avoid stale-install drift.
- Intake fail-soft messages reference `hai state reproject` correctly.

### Security / Privacy

- DB + WAL/SHM/journal siblings locked to 0o600 on POSIX.
- Every JSONL audit log + base directory locked to 0o600 / 0o700 on POSIX after each write.
- Packaged Garmin CSV fixture documented as synthetic; PII regression test scans for emails, phones, GPS, device serials, identity columns.
- `reporting/docs/privacy.md` covers what's stored / where / how to inspect / export / delete / migrate.

### Migrations applied (forward-only)

- 013 — `proposal_log` revision columns
- 014 — `daily_plan.superseded_by_plan_id` forward-link
- 015 — `manual_readiness_raw` table
- 016 — `review_outcome` re-link columns
- 017 — `running_activity` table

Schema head: 16 → 17.

### Test-suite delta

1,489 (v0.1.2) → 1,710 (v0.1.4 mid-development) → **1,824** (v0.1.4 shipping). 0 failing, 4 deliberately skipped (Windows-only privacy tests on POSIX).

---

## [0.1.3.dev0] — 2026-04-23

Bump from v0.1.2; never released. Superseded by v0.1.4.

## [0.1.2] — pre-2026-04-24

Hidden `--with-auth` prompt fix; backfill loop replaced with single pull.

## [0.1.1] — pre-2026-04-24

Phase A onboarding UX + local telemetry.

## [0.1.0] — pre-2026-04-24

Initial release.

[0.1.8]: https://pypi.org/project/health-agent-infra/0.1.8/
[0.1.7]: https://pypi.org/project/health-agent-infra/0.1.7/
[0.1.6]: https://pypi.org/project/health-agent-infra/0.1.6/
[0.1.5]: https://pypi.org/project/health-agent-infra/0.1.5/
[0.1.4]: https://pypi.org/project/health-agent-infra/0.1.4/
[0.1.3.dev0]: https://pypi.org/project/health-agent-infra/0.1.3.dev0/
[0.1.2]: https://pypi.org/project/health-agent-infra/0.1.2/
[0.1.1]: https://pypi.org/project/health-agent-infra/0.1.1/
[0.1.0]: https://pypi.org/project/health-agent-infra/0.1.0/
