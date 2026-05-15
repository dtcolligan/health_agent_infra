# v0.1.10 — Pre-PLAN Findings Cleanup + Persona Harness

> **Status.** Authored 2026-04-27 after the structured pre-PLAN bug
> hunt completed (`PRE_AUDIT_PLAN.md`, `audit_findings.md`). This
> file replaces the "scope a release on opportunistic findings"
> approach with scope built on systematic audit output.
>
> **Cycle pattern.** v0.1.10 follows the v0.1.8 / v0.1.9 four-round
> audit/response convention (PLAN.md → Codex audit → response →
> implementation review → ship proof). The pre-PLAN bug hunt is
> Phase 0; this PLAN.md opens Phase 1.
>
> **Rescope (2026-04-28).** The original framing as "correctness +
> audit-chain integrity release" was challenged by Codex
> implementation review round 1 (`codex_implementation_review_response.md`).
> The audit-chain integrity workstreams W-E (state-change re-synth)
> and W-F (version-counter integrity) did not land cleanly and the
> review correctly flagged that deferring them while keeping the
> "audit-chain integrity" framing was dishonest.
>
> **v0.1.10 is now scoped as: persona harness landed, threshold
> consumer hardening (D12), partial-day nutrition gate, running-
> activity rollup wire, gym schema alias, ruff cleanup, test-suite
> hermeticity.** Audit-chain integrity is the **v0.1.11 thesis**,
> not a deferred extra.

---

## 1. What this release ships

v0.1.10 is a **correctness + persona-harness release** (rescoped
2026-04-28; see banner above). No new features. No new domains.
The release closes the highest-impact correctness findings from
the pre-PLAN hunt, lands the permanent persona regression
infrastructure, and hardens the threshold-consumer surface against
bool-as-int silent coercion. The two audit-chain integrity items
(W-E, W-F) are the v0.1.11 thesis.

### 1.1 Workstream catalogue

> **Catalogue note (rescope, 2026-04-28).** This table is the
> ORIGINAL pre-rescope plan. Workstreams that did not land cleanly
> were deferred — see § 1.2 for the authoritative split. Specifically
> W-B / W-E / W-F / W-H / W-K / W-L / W-N moved to v0.1.11. The
> "shipped in v0.1.10" view of record is `RELEASE_PROOF.md § 1`.

| W-id | Title | Severity | Files | Source | Round-2 status |
|---|---|---|---|---|---|
| **W-A** | **Threshold consumer type hardening** | type-safety | `core/config.py` (helpers + load-time validator), `core/synthesis_policy.py`, `domains/nutrition/policy.py`, `domains/nutrition/classify.py`, `core/pull/garmin_live.py` | F-A-01, v0.1.9 backlog B1, F-CDX-IR-02, F-CDX-IR-R2-01 | shipped |
| **W-B** | R-volume-spike minimum-coverage gate | band-miscalibration | `core/synthesis_policy.py`, `domains/strength/policy.py` | F-C-04, B2 (memory) | **deferred → v0.1.11** |
| **W-C** | **R-extreme-deficiency partial-day gate** | band-miscalibration | `domains/nutrition/policy.py`, `core/state/snapshot.py` (W-C-wire), `core/config.py` | B1 (memory), F-CDX-IR-01 | shipped |
| **W-D** | **Activity projector input validation** | correctness | `core/state/projectors/running_activity.py` | F-C-01, F-C-02 | shipped |
| **W-D-ext** | **Running activity → daily rollup wire** | correctness | `cli.py` clean handler, `core/state/projector.py` | F-C-03 | shipped |
| **W-E** | `hai daily` re-run state-change detection | audit-chain integrity | `core/synthesis.py`, `cli.py` daily handler | F-B-02, B7 (memory) | **deferred → v0.1.11 release-blocker-class** |
| **W-F** | Audit-chain version-counter integrity | audit-chain integrity | `core/synthesis.py` supersession path | F-B-01 | **deferred → v0.1.11 release-blocker-class** |
| **W-G** | **`hai intake gym` schema alias for `exercise`** | type-safety / UX | `domains/strength/intake.py` | F-C-08 | shipped |
| **W-H** | Type-checker findings sweep (35 mypy errors) | type-safety / correctness | many | F-A-03 through F-A-12 | **deferred → v0.1.11 (W-H1) + v0.1.12 (W-H2)** |
| **W-I** | **Ruff cleanup (24 findings)** | maintenance | many files | F-A-15 | shipped |
| **W-J** | **`applied_action_mutation` deletion** | correctness | `core/synthesis_policy.py` | F-A-02 | shipped |
| **W-K** | Bandit B608 audit pass | security review | 16 SQL sites | F-A-13 | **deferred → v0.1.11** |
| **W-L** | Bandit B310 url-scheme audit | security | `core/pull/intervals_icu.py:310` | F-A-14 | **deferred → v0.1.11** |
| **W-M** | **Persona harness landed** | infrastructure | `verification/dogfood/` | done in pre-PLAN | shipped |
| **W-N** | Pytest unraisable warning cleanup | nit | `safety/tests/test_snapshot_bundle.py` | v0.1.9 backlog B2 | **deferred → v0.1.11** |
| **W-hermeticity** | **Test-suite hermeticity (autouse fixture)** | testing infrastructure | `verification/tests/conftest.py` | F-CDX-IR-03 | shipped |

### 1.2 Out-of-scope (deferred)

#### Release-blocker-class for v0.1.11 (audit-chain integrity)

These items appeared in the pre-PLAN bug hunt and were originally
in v0.1.10 scope. They did not land cleanly. v0.1.11 is the
audit-chain integrity release; they gate that ship.

| Item | Why deferred to v0.1.11 |
|---|---|
| **W-E / F-B-02** — `hai daily` re-run state-change detection | Synthesis-path semantic; needs design discussion before code lands. Same-day re-logged intake should produce a `_v<N>` superseded plan with refreshed prose; today the rationale is stale. |
| **W-F / F-B-01** — Audit-chain version-counter integrity | A `_v0 → _v3` jump (skipping `_v2`) was observed in the audit-chain probe. Root cause not localised yet. |

#### Backlog (lower priority)

| Item | Why deferred |
|---|---|
| **F-C-03** — running daily aggregator from `running_activity` | Landed (W-D-ext); see § 2.4 |
| **F-CDX-IR-05** — running-rollup provenance completeness | Aggregator computes `total_duration_s` + `session_count` but the projector hardcodes them to `None`; provenance string is also stale |
| **F-CDX-IR-06** — persona harness drift guards | Synthetic-skill action tokens validated post-facto via `hai propose` failure rather than against the runtime contract directly |
| **F-B-03** — review schedule auto-run gap | Investigation needed before triage |
| **F-B-04** — domain coverage drift across supersession | needs-design-discussion |
| **F-A-08** — shadowed `days_touched` name | nit — verify intentional, no fix |
| **F-C-05** — strength_status enum surfaceability | needs-design-discussion |
| **F-C-06** — persona matrix elevated-stress coverage | matrix expansion, not runtime |
| **W52 / W53 / W58** | Already deferred per v0.1.9 backlog roadmap |

---

## 2. Per-workstream contract

### 2.1 W-A — Threshold consumer type hardening

**Goal.** Eliminate `int(cfg)` / `float(cfg)` / `bool(cfg)` patterns
that silently coerce booleans into numeric thresholds.

**Approach.** Centralise typed access. Add a new module
`src/health_agent_infra/core/config/coerce.py` exporting:
- `coerce_int(value, *, name)` — raises if value is bool or non-numeric.
- `coerce_float(value, *, name)` — same.
- `coerce_bool(value, *, name)` — strict bool, no truthy coercion.

Each helper logs at the boundary and raises a typed
`ConfigCoerceError(invariant_id="config_coerce", ...)`.

Replace all `int(cfg.get(...))` / `float(cfg.get(...))` /
`bool(cfg.get(...))` sites listed in F-A-01 (≥22) with the new
helpers.

**Acceptance.**
- Every site in `core/synthesis_policy.py`, `domains/nutrition/policy.py`,
  `domains/nutrition/classify.py`, `core/pull/garmin_live.py` switched.
- New `verification/tests/test_config_coerce.py` covers
  bool-as-int, string-as-int, float-as-int rejection.
- Existing test suite stays green.

### 2.2 W-B — R-volume-spike minimum-coverage gate

**Goal.** Stop R-volume-spike escalating for users with regular but
sparse strength training.

**Approach.** Add a `min_sessions_last_28d` threshold to the rule.
Default to `8` (≥2 sessions/week sustained for the lookback). Below
the threshold, the rule emits `coverage_band: 'insufficient'` rather
than firing as a spike.

Updated paths:
- `core/synthesis_policy.py` — X-rule definition gains coverage gate.
- `domains/strength/policy.py` — band classification stays as-is;
  rule firing path checks gate first.
- Default threshold added to `DEFAULT_THRESHOLDS` so users can
  override.

**Acceptance.**
- Persona harness no longer fires R-volume-spike on P1, P4, P5,
  P6, P7. Re-run shows `defer` or `proceed_with_planned_session`
  for these personas.
- New test `verification/tests/test_xrule_volume_spike_coverage.py`
  asserts gate behaviour at the boundary.
- Existing strength tests stay green.

### 2.3 W-C — R-extreme-deficiency partial-day gate

**Goal.** Stop R-extreme-deficiency firing on a single
breakfast-only nutrition row.

**Approach.** Two-part gate:
- `meals_count` minimum: rule cannot fire unless
  `nutrition_intake.meals_count >= 2` (or absent — backward
  compatibility) OR
- Time-of-day: rule cannot fire before
  `r_extreme_deficiency_end_of_day_local_hour` local time on
  ``as_of_date``. Default 21 (set in `RELEASE_PROOF`); past dates
  are always treated as end-of-day.

Either gate satisfied → rule is allowed to evaluate. Both unsatisfied
→ rule emits `partial_day_caveat` flag and yields without forcing
escalation.

**Round-2 wire (F-CDX-IR-01).** The gate must be plumbed through
``build_snapshot``, not just exercised at the policy boundary —
otherwise the production runtime path bypasses it. Round 1 missed
this; round 2 reads ``meals_count`` from the accepted nutrition
row and derives ``is_end_of_day`` from ``now_local`` against the
threshold.

**Acceptance.**
- Reproduce the morning-briefing 06:32 scenario: log breakfast +
  protein shake, run `hai daily` at 06:33 — observe nutrition does
  not escalate.
- Log one meal, run `hai daily` at 21:30 — observe escalation
  fires (end-of-day threshold reached).
- Log one meal for a past date — observe escalation fires
  regardless of clock.
- Tests: `verification/tests/test_partial_day_nutrition_gate.py`
  (policy boundary) +
  `verification/tests/test_partial_day_nutrition_snapshot_wire.py`
  (round-2 build_snapshot integration).

### 2.4 W-D — Activity projector input validation

**Goal.** Replace `KeyError` failures from `project_activity` with
typed validation errors.

**Approach.** At the projector entry, validate:
- Required: `activity_id`, `user_id`, `raw_json`, `as_of_date`.
- Each missing field → `ProjectorInputError(invariant_id=
  "activity_required_fields", ...)`.

Also wrap the existing direct dict access in `.get()` plus explicit
None checks for resilience even after validation.

**Acceptance.**
- Reproduce: pass `activity` dict missing `user_id` → typed error,
  not `KeyError`.
- New test `verification/tests/test_running_activity_projector.py`.

### 2.5 W-E — `hai daily` re-run state-change detection

**Goal.** When `hai daily` is re-run on the same date and state
materially differs, produce a superseded `_v<N>` plan with refreshed
rationale prose.

**Approach.**
- `core/synthesis.py` computes a state fingerprint
  (`hash` of nutrition_intake / readiness / gym intake / clean
  evidence row) before synthesis.
- If a canonical plan already exists for `(for_date, user_id)`,
  compare its captured fingerprint to the current.
- Match → no-op (correct idempotent behaviour).
- Mismatch → produce `_v<N>` supersession with fresh proposal_log
  rows and rationale prose.

**Acceptance.**
- Reproduce F-B-02:
  1. Log nutrition intake A.
  2. Run `hai daily`. Capture plan_id.
  3. `hai intake nutrition --replace` with intake B.
  4. Run `hai daily` again.
  5. Observe new `_v2` plan id, fresh rationale prose.
- New test `verification/tests/test_daily_supersede_on_state_change.py`.

### 2.6 W-F — Audit-chain version-counter integrity

**Goal.** Eliminate the `_v3` jump from `_v0` (skipped `_v2`)
observed in F-B-01.

**Approach.** Investigate root cause first. Hypothesis: the version
counter increments on attempt rather than on commit. Audit the
supersession path to confirm. Fix: counter increments only after
successful commit of the superseding row.

**Acceptance.**
- Re-run a contrived re-synthesise loop: every supersede produces
  the next sequential version.
- Audit-chain probe (Phase B) re-runs cleanly across recent days.

### 2.7 W-G — `hai intake gym` exercise alias

**Goal.** `--session-json` payload accepts both `exercise` and
`exercise_name` keys per set.

**Approach.** Schema normalisation at the intake handler — accept
`exercise` as alias for `exercise_name`, log a deprecation warning,
behaviour identical.

### 2.8 W-H — Type-checker findings sweep

**Goal.** Address each of the 35 mypy errors from the default-strict
pass that represent real correctness concerns.

**Per-finding triage:**
- `cli.py:204, 4389` adapter type confusion → fix the assignment
  type (use Protocol).
- `cli.py:4075, 4083` None comparison → guard.
- `cli.py:2957-2963` exercise None-into-str → argparse-required
  validation.
- `cli.py:1963-1964` Literal abuse → broaden Literal or drop
  `'total'` index.
- `cli.py:372` Literal status arg → narrow.
- `cli.py:3735` unused `exc` (ruff F841) → use or remove.
- `core/state/runtime_event_log.py:54` int-of-Optional → guard.
- `core/state/projector.py:302, 2219` int-of-Optional → guard.
- `core/state/projector.py:1608` shadowed `days_touched` → verify
  + rename if accidental (deferred per § 1.2 if intentional).
- `core/memory/projector.py:61-62` Literal abuse → broaden.
- `core/synthesis.py:373` None-propagation → narrow / guard.
- `core/doctor/checks.py:276` fromisoformat-of-Optional → guard.
- `evals/runner.py:354` sorted-on-None → strip None.
- `evals/runner.py:668-669` scenario type confusion → fix the type.

**Acceptance.** mypy default pass ≤ 5 remaining errors (intentional
or deferred to v0.2 with reasons documented).

### 2.9 W-I — Ruff cleanup

**Goal.** 24 ruff findings → 0.

**Approach.** `ruff check --fix` covers 23 of 24 (auto-fixable F401
unused imports + 1 F841). The remaining one (`applied_action_mutation`
F841) is W-J.

### 2.10 W-J — `applied_action_mutation` investigation

**Goal.** Determine if this write-only variable represents a missing
return path or true dead code, then fix accordingly.

**Approach.**
- Git blame the variable's introduction.
- Read PR / commit message for original intent.
- If intended as a return value: wire it through.
- If true dead code: delete + comment in the commit message.

### 2.11 W-K — Bandit B608 audit

**Goal.** Per-site determination on each B608 SQL string-construction
finding.

**Approach.** For each of the 16 sites, produce a verdict:
- `# nosec B608  # reason: column-whitelisted from constant tuple`
  for the placeholder-templating IN-clause pattern.
- `# nosec B608  # reason: <other-reason>` if intentional otherwise.
- Refactor only if a site is genuinely unsafe.

### 2.12 W-L — Bandit B310 audit

**Goal.** Confirm `core/pull/intervals_icu.py:310` URL is
fully constant + does not accept user input.

**Approach.** Read the call site. If safe, document with a
`# nosec B310` comment. If user input contributes, restrict to
allowed schemes via `urllib.parse.urlparse`.

### 2.13 W-M — Persona harness landed

Already done in the pre-PLAN phase. v0.1.10's release proof includes
a re-run of the harness post-fixes to demonstrate finding-by-finding
resolution.

### 2.14 W-N — Pytest unraisable warning

Cleanup of `safety/tests/test_snapshot_bundle.py` HTTP response
not closed in finally.

---

## 3. Acceptance criteria (rescoped 2026-04-28)

v0.1.10 ships when (status of record: `RELEASE_PROOF.md`):

- [x] **In-scope workstreams** (W-A + extras, W-C + wire, W-D,
      W-D-ext, W-G, W-I, W-J, W-M, W-hermeticity) complete.
- [x] **Out-of-scope workstreams** (W-B, W-E, W-F, W-H, W-K, W-L,
      W-N) explicitly deferred with documented reason in § 1.2 +
      `RELEASE_PROOF.md` § 1 + `v0_1_11/BACKLOG.md`. W-E + W-F
      tagged release-blocker-class for v0.1.11.
- [x] `verification/tests/` green: ≥ 2133 baseline + 28 (W-A
      coerce/load-time validation) + 5 (W-C policy + wire) + 7
      (W-D activity validator) + 4 (W-C-wire integration) + 1
      (D12 grep guard) = ≥ 2178 total. Round-2 ship state: 2202
      passed, 2 skipped (hermetic across env states).
- [x] Persona harness re-runs show:
  - F-C-01 / F-C-02 produce typed validation errors not crashes.
  - F-C-03 (W-D-ext) — P2 + P7 produce running actions instead of
    universal defer.
  - F-C-04 (W-B / volume_spike on regular training) — three
    expected residuals on P1, P4, P6 (deferred to v0.1.11 W-B).
- [x] ruff strict pass: 0 findings.
- [x] `hai capabilities --json` regenerates without diff against
      committed `reporting/docs/agent_cli_contract.md`.
- [x] `verification/tests/conftest.py` autouse hermeticity fixture
      makes the suite produce identical results regardless of
      configured live credentials.
- [x] CHANGELOG.md v0.1.10 section + per-W-id summary updated;
      audit-history note records Codex round 1 `DO_NOT_SHIP`.
- [x] `RELEASE_PROOF.md` emitted with full reproducibility recipe.
- [ ] Codex audit round 3 returns SHIP or SHIP_WITH_NOTES.

**Out of scope for v0.1.10 acceptance** (do not block ship on these
— they are the v0.1.11 thesis):

- F-B-02 same-day state-change re-synth (W-E)
- F-B-01 audit-chain version-counter integrity (W-F)
- F-CDX-IR-05 running-rollup provenance completeness (v0.1.11 W-R)
- F-CDX-IR-06 persona harness drift guards (v0.1.11 W-S)

---

## 4. Sequencing

Recommended execution order (parallelisable where flagged):

1. **W-I** (ruff cleanup) — 30 min, auto-fix.
2. **W-A** (threshold coercer) — foundational, blocks W-B + W-C
   tests.
3. **W-D** (activity projector) — independent, parallel with W-A.
4. **W-G** (gym schema alias) — independent, ~30 min.
5. **W-K** (bandit B608 sweep) — independent, ~1-2 hours.
6. **W-L** (bandit B310 audit) — ~30 min.
7. **W-N** (pytest unraisable) — ~30 min.
8. **W-B** (volume_spike gate) — depends on W-A (uses coerce
   helpers in threshold reads).
9. **W-C** (extreme-deficiency gate) — depends on W-A.
10. **W-E** (state-change re-synth) — independent.
11. **W-F** (version-counter integrity) — independent.
12. **W-J** (applied_action_mutation investigation) — independent.
13. **W-H** (mypy sweep) — last, picks up incidental fixes from
    earlier work.
14. **Persona harness re-run** — confirm fixes visible.
15. **Codex round 1 audit** — opens after all workstreams.

Estimated total: 4-6 working days. Pre-PLAN hunt added ~3 days,
total v0.1.10 cycle ~7-9 days plus audit rounds.

---

## 5. Provenance

This PLAN.md is built on:

- `reporting/plans/v0_1_10/PRE_AUDIT_PLAN.md` — the pre-PLAN
  scope discipline doc.
- `reporting/plans/v0_1_10/audit_findings.md` — Phase A + B + C
  findings (29 total).
- `reporting/plans/v0_1_9/BACKLOG.md` § "Items deferred from v0.1.8
  Codex audits" — B1 (threshold hardening) + B2 (pytest unraisable).
- Project memory (auto-saved 2026-04-27): morning-briefing
  v0.1.x runtime bugs B1-B7.

Out-of-scope items (§ 1.2) carry their deferred-because reasons
forward to `reporting/plans/v0_1_10/BACKLOG.md` after v0.1.10 ships.
