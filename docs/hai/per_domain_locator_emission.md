# Per-domain locator emission — W-PROV-2 design choices

**Cycle.** v0.2.0 W-PROV-2.

**Provenance.** PLAN §2.A acceptance #3 + the W-PROV-2 spike note at
`reporting/plans/v0_2_0/w_prov_2_spike.md`. The maintainer adopted
option (C) hybrid in the chat at cycle open — always-emit a row-level
locator, plus a column-level citation when the spike-shaped R-rule
fires.

This doc captures the per-domain decisions concretely so future audit
rounds, IR, and W52/W58D consumers have a single page to consult.

---

## Architecture

Each domain emits zero, one, or many `SourceRowLocator` entries on its
`<D>PolicyResult.evidence_locators` field. Locators are validated
against `core/provenance/locator.py:_ALLOWED_TABLES_PK` and serialised
through to `recommendation_log.evidence_locators_json` via the
proposal-acceptance path the skill drives.

The hybrid emission contract:

- **Row-level baseline.** When the policy receives identity args
  (`for_date_iso`, `user_id`, and the today-row version) it emits one
  locator citing the domain's accepted-state table at row level
  (`column` omitted). This baseline is what closes W52's
  every-quantitative-claim-resolves goal across non-spike R-rule
  firings (R-coverage, R-sparse, etc.).
- **Column-level spike citation.** When the domain's spike-shaped
  R-rule fires, additional column-level locators are appended citing
  the specific metric column the rule reasoned over. For multi-day
  rules these mirror recovery R6's per-window-day shape; for
  single-day rules they collapse to today's row with a column
  qualifier.

Days missing from the version map are silently skipped — the
safe-default that mirrors `_r6_spike_locators` and stays honest about
what the runtime actually had access to at policy time.

---

## Per-domain choices

| Domain | Rule shape | Row-level cite | Column-level spike cite | Window length |
|---|---|---|---|---|
| **recovery** | per-rule conditional (already shipped at v0.1.14) | none — R6 is per-rule only | `accepted_recovery_state_daily.resting_hr` for each spike day | trailing N days from `for_date_iso` per `consecutive_days` |
| **running** | hybrid (always-emit + ACWR cross-cite) | `accepted_running_state_daily` (today, row-level) | `accepted_recovery_state_daily.acwr_ratio` (today) — the ACWR ratio is computed from recovery's `acute_load`/`chronic_load`, so the spike's source row lives in recovery, not running | single-day |
| **sleep** | hybrid (always-emit + chronic-deprivation window) | `accepted_sleep_state_daily` (today, row-level) | `accepted_sleep_state_daily.sleep_hours` per night in the trailing-7 window | up to 7 nights |
| **stress** | hybrid (always-emit + sustained-stress run) | `accepted_stress_state_daily` (today, row-level) | `accepted_stress_state_daily.garmin_all_day_stress` per consecutive day in the trailing run | up to `consecutive_days` |
| **strength** | hybrid (always-emit + volume-spike) | `accepted_resistance_training_state_daily` (today, row-level) | `accepted_resistance_training_state_daily.total_volume_kg_reps` (today) — 28-day baseline implicit in `volume_ratio` + `threshold_ratio` detail; citing all 28 historical rows would over-cite | single-day |
| **nutrition** | hybrid (always-emit + extreme-deficiency two-metric cite, partial-day preserves row-level) | `accepted_nutrition_state_daily` (today, row-level) | `accepted_nutrition_state_daily.calories` + `accepted_nutrition_state_daily.protein_g` (today) — two columns matching the rule's two source metrics (`calorie_deficit_kcal` + `protein_ratio`) | single-day |

### Recovery — the v0.1.14 shape (unchanged)

Recovery's R6 spike-locator emission shipped at v0.1.14 W-PROV-1 and is
intentionally **per-rule conditional**, not always-emit. The reason is
historical: v0.1.14 was the substrate-prove cycle, and the maintainer
judgement was to ship the narrowest possible emission path that proved
the locator dataclass + validator + serializer worked end-to-end. The
non-spike R-rule firings (R1 coverage, R5 sparse) emit no locators on
the recovery domain.

W-PROV-2 does **not** retouch recovery. The W52 quantitative-claim
coverage gap that recovery R-cov firings expose under per-rule
conditional is a known residual — if W52 needs to surface a
provenance-backed claim about a recovery-domain non-spike day, W-PROV-3
(v0.2.1+) is the destination for an "always-emit on recovery" upgrade.

### Running — cross-domain ACWR citation

The running-domain `_r_acwr_spike` rule cites `acwr_ratio`, which is
computed from `acute_load` ÷ `chronic_load` — both columns live on
`accepted_recovery_state_daily`, not `accepted_running_state_daily`.
The hybrid emission therefore points the column-level locator at the
recovery row.

This is honest about the substrate boundary: the running domain
*decided* to escalate, but the *number that triggered the decision*
sits in the recovery domain's table. W58D resolving an ACWR-spike
claim resolves the locator to recovery's row and reads `acwr_ratio`
back from there. F-PHASE0-12 (Codex) reaffirmed this kind of
cross-domain citation is in-contract for the W-PROV-1 whitelist.

### Sleep + stress — multi-day mirror of recovery R6

Both rules consume trailing-window signals
(`sleep_history_hours_last_7`, `stress_history_garmin_last_7`). The
spike emission cites one column-level locator per window day present
in the version map. The window length is `forced_action_detail`'s
`window_nights` (sleep) or `consecutive_days` (stress) — both set by
the rule itself when it fires.

### Strength — single-day with implicit baseline

`_r_volume_spike` cites `volume_ratio` (today's volume / 28-day
average). The spike emission cites today's `total_volume_kg_reps`
column-level only; the 28-day baseline is implicit in
`forced_action_detail.threshold_ratio` and the `volume_ratio` value
itself. A verifier can re-aggregate the trailing 28 rows from the
table independently to reproduce the ratio.

This is a deliberate "today's row only with column citation"
trade-off recommended by the W-PROV-2 spike note §3.4: citing all 28
historical rows on every spike firing would over-cite without adding
verifier signal beyond what the threshold detail already carries.

### Nutrition — partial-day preserves row-level

The `_r_extreme_deficiency` rule has a partial-day suppression branch:
when `meals_count < min` AND `is_end_of_day` is not True, the rule
yields with `partial_day_caveat` instead of firing escalate. Under
suppression, the always-emit row-level locator stays intact (today's
row exists regardless of partial-day status); only the column-level
`calories` + `protein_g` citations are skipped. This keeps W52's
quantitative-claim coverage for partial-day nutrition days while
honestly flagging that the deficiency-spike claim itself wasn't
validated.

---

## Whitelist contract reaffirmed

Per W-PROV-1 (`reporting/docs/archive/cycle_artifacts/source_row_provenance.md:42-46`)
and F-PHASE0-12, the locator whitelist contains **only** evidence +
accepted-state tables. Write-side audit-chain references
(recommendation_id, planned_id, proposal_id, x_rule_firing.id,
review_outcome.id, data_quality_daily, runtime_event_log,
sync_run_log) belong in the v0.2.0 evidence-card payload lanes
(W-EVCARD-DAILY + W-EVCARD-WEEKLY), not in `SourceRowLocator`
instances.

The introspection regression at
`verification/tests/test_provenance_whitelist_against_synthesis.py`
guards both directions of this invariant.

---

## v0.2.1+ candidates (deliberately out of W-PROV-2)

- **Recovery always-emit upgrade.** Lift recovery from per-rule
  conditional to hybrid so non-spike R-rule firings carry row-level
  provenance. Reopens v0.1.14 emission code; out-of-scope for v0.2.0.
- **Strength 28-day baseline citations on demand.** A future
  `--explain-deep` surface could resolve a volume-spike claim by
  citing all 28 historical rows. Out-of-scope for v0.2.0; W58D's
  deterministic gate doesn't need the over-cite.
- **Cross-domain locator dedup at synthesis.** When multiple domains
  cite the same recovery row (running ACWR + recovery R6 firing the
  same day), synthesis-side dedup may want to consolidate. Out of
  W-PROV-2 scope; the existing `dedupe_locators` already runs at
  serialise time.
