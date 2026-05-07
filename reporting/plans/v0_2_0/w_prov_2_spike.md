# W-PROV-2 spike — recovery-R6 transferability across the 5 dormant domains

**Date.** 2026-05-07.

**Scope.** Anchor PLAN §2.A's "2-4d" effort estimate. Read the recovery
R6 reference shape (`domains/recovery/policy.py:215-230` + the
`_r6_spike_locators` builder + the `_accepted_recovery_state_versions`
snapshot-side helper) and the policy.py + classify.py + accepted-state-
table schemas of the 5 dormant domains. Decide whether the R6 pattern
maps cleanly. Pre-code; no commits beyond this note.

---

## 1. Verdict

**R6 transferability is HIGH. PLAN §2.A 2-4d holds for the per-rule
conditional path; always-emit is faster (≈2-3d) and a better fit for
W52's quantitative-claim coverage goal.**

The architectural pattern is uniformly applicable across all 5 dormant
domains. The only domain-specific work is per-rule column citation +
single-day vs multi-day window length.

---

## 2. What's uniform across all 6 domains (verified)

### 2.1 Policy-result dataclass shape

Each domain's policy.py exposes a frozen `<D>PolicyResult` carrying:

```
forced_action: Optional[str]
forced_action_detail: Optional[dict[str, Any]]
capped_confidence: Optional[str]
policy_decisions: tuple[PolicyDecision, ...]
```

Recovery's already-shipped `evidence_locators: Optional[tuple[dict, ...]]`
slot at `domains/recovery/policy.py:237` is the field to mirror; the 5
dormant `<D>PolicyResult` dataclasses do not yet have this field.

### 2.2 R-rule structure

Every domain has an R-cov + R-sparse + ≥1 spike-shaped rule that fires
`forced_action="escalate_for_user_review"` (or a domain-specific
escalate-shape) with `forced_action_detail = {reason_token, metric_value,
threshold}`:

| Domain | Spike rule | Window | Single locator or N? |
|---|---|---|---|
| recovery | `_r6_resting_hr_spike` | 3 days | N (trailing) |
| running | `_r_acwr_spike` | today | 1 |
| sleep | `_r_chronic_deprivation` | 7 nights | up to N |
| stress | `_r_sustained_stress` | 7 days (presumed) | up to N |
| strength | `_r_volume_spike` | today (28d denominator stored in 1 row) | 1 |
| nutrition | `_r_extreme_deficiency` | today | 1 |

Most dormant rules are single-day (running, strength, nutrition) → simpler
than R6 (1 locator, not N). Multi-day rules (sleep, stress) use the R6
verbatim shape.

### 2.3 Accepted-state-table grain

All six accepted-state tables share:

- **Composite PK** `(as_of_date, user_id)` — verified at:
  `migrations/001_initial.sql:251` (recovery), `:275` (running), `:296`
  (strength), `:319` (nutrition); `migrations/004_sleep_stress_tables.sql:74`
  (sleep), `:105` (stress).
- `projected_at TEXT NOT NULL` — every table carries the row_version
  source for locator emission.
- Domain-specific metric columns the rules cite — e.g.,
  `accepted_running_state_daily.acwr_ratio` doesn't exist (acwr is in
  recovery; running's row carries `total_distance_m`,
  `total_duration_s`, `moderate_intensity_min`, `vigorous_intensity_min`
  — see §3.3 below).

### 2.4 Snapshot.py central call site

`core/state/snapshot.py:702-980` is the single call site that imports
and invokes all 6 `evaluate_<d>_policy` functions. The recovery branch
(`:744-758`) builds `recovery_state_versions` via
`_accepted_recovery_state_versions(...)` (`:1377-1404`) and passes
`for_date_iso`, `user_id`, `accepted_state_versions`. The 5 dormant
branches (`:792, :814, :834, :868, :978`) currently take 1-3 args and
skip the version map.

---

## 3. Domain-by-domain transferability

### 3.1 running (single-day; trivial)

- Rule: `_r_acwr_spike` (`policy.py:108-148`) cites
  `running_signals["acwr_ratio"]`.
- **acwr is computed cross-domain** from recovery substrate
  (`acute_load`/`chronic_load` live in `accepted_recovery_state_daily`,
  not running). Locator citation should resolve to the **recovery** row
  the acwr was derived from, OR to today's `accepted_running_state_daily`
  row keyed by the policy invocation. F-PHASE0-12 architecturally
  permits either; the per-domain doc must name the choice.
- Recommendation: cite `accepted_running_state_daily` for the
  always-emit path (covers all running rules); cite the recovery row
  for `_r_acwr_spike` if going per-rule conditional.

### 3.2 sleep (multi-day; R6 verbatim)

- Rule: `_r_chronic_deprivation` (`policy.py:108-170`) consumes
  `sleep_signals["sleep_history_hours_last_7"]` — exactly the R6 shape.
  Detail carries `short_nights`, `window_nights`, threshold values.
- R6 builder transfers verbatim to a `_chronic_deprivation_locators`
  helper that emits 1 locator per night in the trailing window where
  `sleep_hours < threshold_hours`.

### 3.3 stress (multi-day; R6 verbatim)

- Rule: `_r_sustained_stress` (`policy.py:109-186`; not fully read
  but signature shape matches sleep + recovery). Trailing window of
  daily `garmin_all_day_stress` from `accepted_stress_state_daily`.
- R6 mirror.

### 3.4 strength (single-day; trivial)

- Rule: `_r_volume_spike` (`policy.py:113-185`) cites
  `classified.volume_ratio` + `sessions_last_28d`.
  `accepted_resistance_training_state_daily` carries
  `total_sets`, `total_volume_kg_reps`, `session_count`. The 28d
  denominator is implicit (rolling window in classify); the locator
  cites today's row only — `column="total_volume_kg_reps"` or similar.
- Plus `_r_unmatched_exercise_cap` — caps confidence; doesn't fire
  escalate; no locator semantics under per-rule conditional.

### 3.5 nutrition (single-day; partial-day caveat)

- Rule: `_r_extreme_deficiency` (`policy.py:120-200`) cites
  `classified.calorie_deficit_kcal` + `classified.protein_ratio`
  derived from `accepted_nutrition_state_daily`.
- **Partial-day gate** (`:142-178`): the rule explicitly suppresses
  firing on `meals_count < min` and `is_end_of_day != True`. Suppressed
  paths don't fire escalate, so per-rule conditional never builds a
  locator. Always-emit path still cites today's row but the
  partial-day caveat is preserved at the classify level.

---

## 4. Per-rule conditional vs always-emit — the actual decision

PLAN §2.A acceptance #2 leaves the choice to the implementer per-domain
with a doc artifact at `reporting/docs/per_domain_locator_emission.md`.
Recommendation for the per-domain doc:

| Path | Pro | Con |
|---|---|---|
| **Per-rule conditional (R6 mirror)** | Granular column citation; only fires when the rule fires; matches recovery R6 architecture verbatim. | Non-spike rules (R-cov, R-sparse) emit no locators → recovery R-cov firings already have this gap. W52's "every quantitative claim resolves" goal is harder to meet domain-wide. |
| **Always-emit** | Every classified state cites the accepted-state row(s) it was derived from, regardless of which rule fired. Closes the W52 quantitative-claim coverage goal cleanly. | Coarser (cites the row, not the column). `column=None` semantics or `column="<derived>"` placeholder for the meta-row case. |

**Spike recommendation: always-emit for the 5 dormant domains.** The
W52/W58D contract benefits from row-level provenance for every
recommendation, and the partial column granularity is a fair trade.
Recovery's already-shipped per-rule R6 emission stays as-is (don't
re-touch shipped code); the dormant domains additionally always-emit a
"row-of-derivation" locator on every classification result.

This still mirrors the R6 pattern — the locator builder, the
snapshot-side `_accepted_state_versions` helper, the `evidence_locators`
field on `<D>PolicyResult`, and the proposal-acceptance plumbing
(`core/writeback/proposal.py:278`) all transfer.

The per-domain doc per PLAN §2.A acceptance #3 should document this:
"recovery: per-rule conditional (already shipped). 5 dormant domains:
always-emit row-of-derivation; spike rules add column citation when
they fire."

---

## 5. Implementation sequence (post-spike)

1. **Whitelist extension** — `core/provenance/locator.py:23` extends
   `_ALLOWED_TABLES_PK` with the 5 accepted-state tables (verified PK
   tuples per `core/synthesis.py:466-473` `_ACCEPTED_STATE_TABLES`).
2. **Generic state-versions helper** — replace
   `_accepted_recovery_state_versions` with a parameterised
   `_accepted_state_versions(conn, table, user_id, end_date, lookback_days)`.
   Recovery's call site uses it without behavior change.
3. **Per-domain emission** — 5 atomic commits, one per domain. Each:
   - Add `evidence_locators` field to `<D>PolicyResult`.
   - Build the locator(s) inside `evaluate_<d>_policy` from the
     classified state's accepted-state-table identity.
   - Extend `evaluate_<d>_policy` signature to accept
     `for_date_iso, user_id, accepted_state_versions`.
   - Wire the snapshot.py call site to pass them.
4. **Whitelist-introspection regression test**
   (`test_provenance_whitelist_against_synthesis.py`) per PLAN §2.A
   acceptance #5.
5. **Per-domain emission tests** — fixture state DB seeded for one
   classification path per domain; assert `evidence_locators_json` on
   the recommendation_log row.
6. **`reporting/docs/per_domain_locator_emission.md`** captures the
   per-domain choice (recovery: per-rule; 5 dormant: always-emit).

---

## 6. Effort estimate refined

| Path | Estimate | Notes |
|---|---|---|
| Per-rule conditional, R6 verbatim mirror (5×) | 4-5d | 5 helpers, 5 detail-token wirings, 5 tests; sleep + stress get the multi-day R6 shape |
| Always-emit (recommended) | 2-3d | 1 generic helper, 5 thin emit-on-classify wirings, 5 tests |
| **Hybrid** (always-emit base + per-rule column citation when spike rules fire) | 3-4d | Single-pass implementation; column citation is a field-on-locator decision per rule |

PLAN §2.A's 2-4d holds for **always-emit** or **hybrid**. The 6d abort
budget per R-V0.2.0-01 has slack at all paths.

---

## 7. Risks / unknowns the spike did NOT close

- **acwr cross-domain citation** (running's `_r_acwr_spike` cites a
  metric that lives in `accepted_recovery_state_daily`) — the
  per-domain doc needs to land the choice explicitly. Cite running's
  row + reference recovery in the audit-chain payload? Or cite recovery
  directly? Both options viable; doc decision deferred to W-PROV-2
  authoring.
- **`derivation_path` interaction in running** — `accepted_running_
  state_daily.derivation_path` toggles between `garmin_daily` and
  `running_sessions`. Locators referencing the running row need to
  carry enough context for W58D to know which derivation produced the
  metric; likely a `column` choice, not a separate field.
- **Stress sustained-stress rule** (`_r_sustained_stress`) read only at
  signature level; if its window-length is computed at runtime (not
  fixed 7), the locator builder needs `lookback_days` parameterised.
- **Partial-day nutrition** — the suppressed firing path emits no
  escalate, so per-rule conditional has no locator anyway. Always-emit
  still cites today's row; the caveat is in the classified state, not
  the locator.

These do not change the verdict; they're per-domain authoring decisions
inside the W-PROV-2 effort budget.

---

## 8. Spike conclusion

**PLAN §2.A 2-4d holds. R6 pattern transfers. Recommended path:
always-emit row-of-derivation across the 5 dormant domains, with
per-domain doc capturing the choice. Recovery R6 stays as-is.**

Cycle proceeds to W-PROV-2 implementation. No PLAN scope revision
required.
