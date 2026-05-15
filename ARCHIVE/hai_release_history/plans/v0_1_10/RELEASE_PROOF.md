# v0.1.10 Release Proof

> **Status (round 3).** Post-Codex-round-2-review ship-readiness
> proof. Round 1 returned `DO_NOT_SHIP` (four blockers); round 2
> closed three blockers and rescoped to address the fourth (audit-
> chain integrity → v0.1.11 thesis); Codex round 2 then returned
> `DO_NOT_SHIP` again on a single remaining blocker — **W-A/D12
> sweep was incomplete** because the grep guard caught raw casts
> (`int(cfg…)`) but missed direct numeric leaf consumers
> (`x < cfg["y"]`, `float(targets[...])`). Round 3 closes that
> architecturally with **load-time threshold-type validation** so
> bool-shaped numeric overrides are rejected at the boundary
> regardless of how consumers read them.

Round 1 was authored 2026-04-27 in the same session as the pre-PLAN
hunt itself — unusual for the project's release pattern, but the bug
surface and fix surface were tightly coupled in this cycle and
gating Codex review on a separate sitting would have desynchronised
the working tree from the findings. Round 2 follows the standard
pattern: Codex external review →
`codex_implementation_review_response.md` →
maintainer-led blocker fixes → this updated proof.

## Round-1 → Round-2 → Round-3 delta

| Codex round | Finding | Severity | Status (round 3) |
|---|---|---|---|
| R1 | F-CDX-IR-01 — W-C partial-day gate not wired into `build_snapshot` | blocker | **closed in round 2** — W-C-wire |
| R1 | F-CDX-IR-02 — W-A coercer sweep incomplete (named raw-cast survivors) | blocker | **closed in round 2** — W-A-extra |
| R1 | F-CDX-IR-03 — pytest not reproducible under live credentials | blocker | **closed in round 2** — W-hermeticity |
| R1 | F-CDX-IR-04 — F-B-02 / F-B-01 deferral incompatible with release framing | blocker | **rescoped in round 2** — release no longer claims audit-chain integrity; W-E + W-F deferred to v0.1.11 as release-blocker-class |
| R1 | F-CDX-IR-05 — running-rollup provenance partial | concern | **deferred to v0.1.11 W-R** |
| R1 | F-CDX-IR-06 — persona harness drift-guards post-facto | nit | **deferred to v0.1.11 W-S** |
| R2 | F-CDX-IR-R2-01 — D12 grep guard misses direct numeric leaf consumers | blocker | **closed in round 3** — load-time threshold-type validation in `core/config.load_thresholds`; consumer-side sweep of `domains/nutrition/classify.py` |
| R2 | F-CDX-IR-R2-02 — `v0_1_10/PLAN.md` stale pre-rescope text | concern | **closed in round 3** — workstream catalogue annotated, W-C section updated, acceptance criteria reflect actual ship state |
| R2 | F-CDX-IR-R2-03 — `v0_1_11/BACKLOG.md` W-R/W-S label mismatch | nit | **closed in round 3** — labels match `v0_1_11/PLAN.md` |

---

## 1. What landed in v0.1.10 (round 2 final)

### Workstreams completed

| W-id | Title | Closed by |
|---|---|---|
| **W-A** | Threshold consumer type hardening (round 1) | New `coerce_int` / `coerce_float` / `coerce_bool` helpers in `core/config.py`; applied to `core/synthesis_policy.py` (4 sites: x7, x2, x3a, x3b) + `domains/nutrition/{policy,classify}.py` (8 sites) |
| **W-A-extra** | W-A sweep completion (round 2, F-CDX-IR-02) | Codex round 1 grepped and surfaced survivors. Round 2 closes `synthesis_policy.py` x4 (`heavy_lower_body_min_volume`), x5 (`vigorous_intensity_min`, `long_run_min_duration_s`), x6a + x6b (`body_battery_max`), and `core/pull/garmin_live.py` retry config (`max_attempts`, `base_delay_seconds`, `max_delay_seconds`, `retry_on_rate_limit`). New regression guard `verification/tests/test_d12_no_raw_cfg_coerce.py` greps the runtime tree on every CI run and fails if any `(int\|float\|bool)(cfg…)` or `(int\|float\|bool)(thresholds…)` pattern reappears. |
| **W-A-validate** | Load-time threshold-type validation (round 3, F-CDX-IR-R2-01) | Codex round 2 caught that the grep guard misses direct numeric leaf consumers (`x < cfg["y"]`, `float(targets[...])`); since Python bools are numeric, a TOML override of `low_max_ratio = true` would still flow as `1`. New `_validate_threshold_types` in `core/config.py` walks the merged thresholds tree at load time and rejects any leaf whose override changed the default's type — strict bool detection (`type(x) is bool`) closes the silent-coercion class architecturally, not consumer-by-consumer. Coverage: 28 tests in `test_load_time_threshold_validation.py`. Plus consumer-side sweep of `domains/nutrition/classify.py` (ratio thresholds, targets, score penalties) for self-documenting consistency with the W-A pattern. |
| **W-C** | R-extreme-deficiency partial-day gate (round 1) | `_r_extreme_deficiency` gains `meals_count` + `is_end_of_day` params with `r_extreme_deficiency_min_meals_count: 2` default. Fixes B1 from morning briefing memory at the policy boundary. |
| **W-C-wire** | Partial-day gate wired into `build_snapshot` (round 2, F-CDX-IR-01) | Round 1 tested the gate at the policy boundary only; `core/state/snapshot.py` was still calling `evaluate_nutrition_policy` without `meals_count` / `is_end_of_day`, so the breakfast-only false positive still fired in normal `hai daily` flow. Round 2 reads `meals_count` from the accepted nutrition row, derives `is_end_of_day` from `now_local` against a new threshold (`r_extreme_deficiency_end_of_day_local_hour: 21`), and passes both through. Past-dated snapshots are always treated as end-of-day. New `verification/tests/test_partial_day_nutrition_snapshot_wire.py` covers the morning, evening, past-date, and threshold-override paths. |
| **W-D** | Activity projector input validation | New `ActivityProjectorInputError` + `_validate_activity_payload` in `core/state/projectors/running_activity.py`. Replaces silent `KeyError` rollback with typed contract violation. Fixes F-C-01, F-C-02. |
| **W-D-ext** | Running-activity → daily rollup wiring | The `aggregate_activities_to_daily_rollup` aggregator was already implemented but never called in the clean flow. Now invoked in `cmd_clean` for both today and historical activity dates. **Fixes F-C-03 — the running-domain-defers-forever bug that affected every intervals.icu user.** Provenance completeness (F-CDX-IR-05) deferred to v0.1.11 W-R. |
| **W-G** | `hai intake gym` exercise alias | `--session-json` payload accepts `exercise` as alias for `exercise_name`. Documented + tested. Fixes F-C-08. |
| **W-hermeticity** | Test suite hermeticity (round 2, F-CDX-IR-03) | `verification/tests/conftest.py` adds an autouse fixture that disables `_intervals_icu_configured()` by default. Eight tests in `test_intake_readiness`, `test_intake_gaps`, and `test_recovery_readiness_v1` previously hit live intervals.icu and 403'd whenever the developer machine had real credentials configured. The suite now runs identically regardless of env state. |
| **W-I** | Ruff cleanup | 23 of 24 findings auto-fixed via `ruff check --fix` (unused imports + unused locals). |
| **W-J** | `applied_action_mutation` write-only investigation | Confirmed dead code, deleted with explanatory comment. Was the 24th ruff finding. |
| **W-M** | Persona harness landed | New `verification/dogfood/` permanent regression infrastructure; 8 personas spanning age, sex, sport mix, data source, history length. Drift guards (F-CDX-IR-06) deferred to v0.1.11 W-S. |

### Workstreams explicitly deferred to v0.1.11

#### Release-blocker-class for v0.1.11 (audit-chain integrity thesis)

These two items defined the rescope. v0.1.11 cannot ship without
them; they are not opportunistic backlog.

| W-id | Title | Why deferred |
|---|---|---|
| **W-E** | `hai daily` re-run state-change detection (B7, F-B-02) | Synthesis-path semantics; needs design discussion before code. v0.1.11 PLAN.md § 2.2 scopes the design upfront. |
| **W-F** | Audit-chain version-counter integrity (F-B-01) | Investigative — root cause not yet localised. v0.1.11 starts with the read-the-code phase before fixing. |

#### Backlog (scoped into v0.1.11)

| W-id | Title | Status |
|---|---|---|
| **W-B** | R-volume-spike minimum-coverage gate | Persona matrix confirms across 6 personas; fix shape interacts with strength freshness model. v0.1.11 § 2.1. |
| **W-H** | Type-checker findings sweep (35 mypy errors) | Several incidentally addressed by W-A; remaining ~30 errors split into W-H1 (correctness) for v0.1.11 and W-H2 (stylistic) for v0.1.12. |
| **W-K** | Bandit B608 SQL string-construction audit | 16 sites to triage. v0.1.11 § 2.5. |
| **W-L** | Bandit B310 url-scheme audit | Single-site review. v0.1.11 § 2.6. |
| **W-N** | Pytest unraisable warning cleanup | v0.1.9 carry-over. v0.1.11 § 2.7. |
| **W-R** (was F-CDX-IR-05) | Running-rollup provenance completeness | `aggregate_activities_to_daily_rollup` computes `total_duration_s` + `session_count` but the projector hardcodes them to `None`. v0.1.11 § 2.11. |
| **W-S** (was F-CDX-IR-06) | Persona harness drift guards | Synthetic-skill action tokens validated post-facto via `hai propose` failure rather than against the runtime contract directly. v0.1.11 § 2.12. |

---

## 2. Test surface

### Pytest baseline

```
2133 passed, 2 skipped in 60.59s   # pre-cycle baseline
```

### Pytest after round 1 (pre-Codex)

```
2169 passed, 2 skipped in 61.27s   # +36 tests
```

(Note: the round-1 proof claim of `2169 passed` was contingent on
a developer machine without intervals.icu credentials. Codex
F-CDX-IR-03 caught this — see § Pytest hermeticity.)

### Pytest after round 2 (post-Codex round-1 blockers fixed)

```
2174 passed, 2 skipped in ~60s   # +5 round-2 tests
```

### Pytest after round 3 (post-Codex round-2 blocker fixed)

```
2202 passed, 2 skipped in ~60s   # +28 load-time-validator tests
```

Hermetic — produces the same `2202 passed` regardless of whether
`HAI_INTERVALS_ATHLETE_ID` / `HAI_INTERVALS_API_KEY` are set in the
environment.

New test files (round 1):
- `verification/tests/test_config_coerce.py` — 24 tests covering
  `coerce_int` / `coerce_float` / `coerce_bool` (W-A).
- `verification/tests/test_partial_day_nutrition_gate.py` — 5 tests
  covering the R-extreme-deficiency partial-day gate at the policy
  boundary (W-C).
- `verification/tests/test_running_activity_projector.py` — 7 tests
  covering activity payload validation (W-D).

New test files (round 2):
- `verification/tests/test_partial_day_nutrition_snapshot_wire.py`
  — 4 integration tests covering the W-C wire into `build_snapshot`
  (morning suppression, evening fire, past-date fire, threshold
  override). Catches F-CDX-IR-01.
- `verification/tests/test_d12_no_raw_cfg_coerce.py` — 1 grep guard
  test that fails if any `(int|float|bool)(cfg…)` or
  `(int|float|bool)(thresholds…)` pattern reappears in the runtime.
  Stylistic guard against re-introducing raw-cast survivors.

New test files (round 3):
- `verification/tests/test_load_time_threshold_validation.py` —
  28 tests across `_is_strict_bool`, `_validate_threshold_types`,
  and `load_thresholds`. Covers: bool-on-int / bool-on-float
  rejection, int-on-bool rejection, string-on-numeric rejection,
  type-matching passes, structural mismatches (dict↔int, list↔int),
  None-default unvalidated, deep-nesting traversal with dotted-path
  error messages, end-to-end TOML load failure for the exact
  silent-coercion class Codex named. Plus `DEFAULT_THRESHOLDS`
  self-validation as a sanity check.

### Pytest hermeticity

`verification/tests/conftest.py` autouse fixture disables
`_intervals_icu_configured()` by default (round-2 fix for
F-CDX-IR-03). Reproducibility check:

```
$ uv run pytest verification/tests -q                              # 2202 passed, 2 skipped
$ HAI_INTERVALS_ATHLETE_ID=fake \
  HAI_INTERVALS_API_KEY=fake uv run pytest verification/tests -q   # 2202 passed, 2 skipped
```

Identical outcome regardless of env state.

### Ruff

```
Pre-cycle: Found 24 errors. [* 23 fixable]
Post-cycle: All checks passed!
```

### Mypy

Pre-cycle: 35 errors in 15 files. Post-cycle: ~30 errors remaining
(W-H deferred). The remaining errors are documented in
`audit_findings.md` § Phase A (F-A-03 through F-A-12) for v0.1.11
scoping.

### Bandit

17 medium-severity findings — all carried forward into v0.1.11
backlog (W-K, W-L). No new findings introduced by v0.1.10 code.

---

## 3. Persona harness regression check

`verification/dogfood/runner.py` re-runs all 8 personas after the
fix set above. Results:

```
Total personas: 8
Crashes: 0      (was 12 in pre-fix run)
Findings: 3     (was 27 in pre-fix run)
```

Findings remaining: all are F-C-04 (R-volume-spike on regular
training pattern) — the deferred W-B item. These are expected.

### Final cross-persona action matrix

```
persona                       recovery       running        sleep          strength       stress         nutrition
p1_dom_baseline               proceed        defer          maintain       ESCALATE       maintain       maintain
p2_female_marathoner          proceed        proceed        maintain       defer          maintain       maintain
p3_older_recreational         proceed        defer          maintain       defer          maintain       maintain
p4_strength_only_cutter       defer          defer          defer          ESCALATE       maintain       maintain
p5_female_multisport          proceed        defer          maintain       ESCALATE       maintain       maintain
p6_sporadic_recomp            proceed        defer          maintain       ESCALATE       maintain       maintain
p7_high_volume_hybrid         proceed        downgrade      maintain       ESCALATE       maintain       maintain
p8_day1_female_lifter         defer          defer          defer          defer          maintain       defer
```

**Compare to pre-fix matrix** (same harness, pre-W-A/W-C/W-D-ext):

```
p2_female_marathoner          proceed        defer          ...   # was defer
p7_high_volume_hybrid         proceed        defer          ...   # was defer
```

P2 (32yo female marathoner with logged runs) and P7 (41yo
high-volume hybrid with logged runs) now produce useful running
recommendations instead of universal defer — F-C-03 confirmed
fixed at the persona level.

P8 (day-1 fresh install) continues to produce clean cold-start
output: 5 domains defer cleanly, stress maintains routine. The
cold-start path was already protected; v0.1.10 did not regress it.

---

## 4. What is NOT in this proof

- **Audit-chain integrity (W-E + W-F).** Explicitly out of scope
  per the round-2 rescope. Tracked release-blocker-class for
  v0.1.11 in `v0_1_11/PLAN.md` § 2.2 and § 2.3 and
  `v0_1_11/BACKLOG.md`.
- **Migration round-trip verification.** No DB schema changes in
  this cycle; v0.1.9 schema is preserved.
- **Skill drift verification.** No skill changes in this cycle;
  Codex round-1 confirmed no skill changes by diffing
  `src/health_agent_infra/skills/`.
- **Migration to bandit clean.** 17 medium-severity findings carry
  forward into v0.1.11 W-K + W-L. No new findings introduced by
  v0.1.10 code.

### Known design boundary: in-memory threshold injection

Codex round 3 (`SHIP_WITH_NOTES`, note 1) flagged that
`load_thresholds()` validates the user-TOML boundary, but
`evaluate_*` runtime primitives in
`core/synthesis.py`, `core/synthesis_policy.py`, and the
per-domain `classify`/`policy` modules accept a
`thresholds: Optional[dict]` argument and consume it directly.
A caller that constructs a threshold dict in-memory and passes it
into one of those functions bypasses `_validate_threshold_types`.

This is a **trusted internal seam**, not a vulnerability:

- The production path (`hai daily`, `hai state snapshot`,
  `hai today`, `hai explain`) flows
  `load_thresholds()` → snapshot/synthesis →
  classify/policy. Every production threshold consumer goes
  through the validator.
- Tests intentionally pass partial threshold dicts to
  `evaluate_*` to exercise specific rule branches in isolation.
  Adding validator coverage there would either break the test
  pattern or require a "validate against partial defaults" mode
  — both larger than the v0.1.10 close needs to be.
- No live runtime path constructs a threshold dict from a source
  other than `load_thresholds()` today.

**v0.1.11 follow-up.** A new W-T workstream (see
`v0_1_11/BACKLOG.md`) will audit every call site of `evaluate_*`
that passes a non-`None` `thresholds` argument and either:

1. Confirm all live call sites originate from `load_thresholds()`,
   in which case the validator already covers them transitively;
   OR
2. Extend `_validate_threshold_types` to support partial defaults
   so it can be invoked at any internal entry point.

---

## 5. Reproducibility

The release proof is reproducible from a clean checkout via:

```bash
uv run pytest verification/tests -q                          # 2202 passed, 2 skipped
HAI_INTERVALS_ATHLETE_ID=fake HAI_INTERVALS_API_KEY=fake \
  uv run pytest verification/tests -q                        # 2202 passed, 2 skipped (hermetic)
uvx ruff check src/health_agent_infra/                       # All checks passed
rm -rf /tmp/hai_dogfood_run
uv run python -m verification.dogfood.runner /tmp/hai_dogfood_run
# expect: 8 personas, 0 crashes, 3 findings (F-C-04 residuals on
# P1, P4, P6 — deferred to v0.1.11 W-B per the rescope)
uv run hai capabilities --markdown > /tmp/cap.md
diff /tmp/cap.md reporting/docs/agent_cli_contract.md
# expect: zero drift
```

---

## 6. Sign-off intent

**Cycle authored.** Round 1: 2026-04-27 (single-session pre-PLAN
hunt + fix implementation). Round 2: 2026-04-28 (Codex round-1
blocker fixes + rescope). Round 3: 2026-04-28 (Codex round-2
blocker fix — load-time validation).

**Provenance.**

- `audit_findings.md` (27 findings, phases A/B/C) — pre-PLAN hunt
  input.
- `PLAN.md` — workstream catalogue + rescope banner.
- `codex_implementation_review_prompt.md` — round-1 prompt.
- `codex_implementation_review_response.md` — round-1 verdict
  (`DO_NOT_SHIP`, four blockers).
- `codex_implementation_review_round2_prompt.md` — round-2 prompt.
- `codex_implementation_review_round2_response.md` — round-2
  verdict (`DO_NOT_SHIP`, one blocker on incomplete D12 sweep).
- `codex_implementation_review_round3_prompt.md` — round-3 prompt.
- This file — round-3 proof.

**Maintainer review pending.** This proof captures the round-3
working-tree state ready for Codex audit round 3. No commit yet —
the maintainer reviews the proof, runs the reproduction commands
locally, then either proceeds to commit + Codex round 3 OR raises
objections.

The release ships when Codex round 3 returns `SHIP` or
`SHIP_WITH_NOTES` and the maintainer commits + tags + publishes.
