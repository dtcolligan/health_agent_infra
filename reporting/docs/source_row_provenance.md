# Source-row provenance (W-PROV-1)

**Status.** v0.1.14 W-PROV-1; one-domain demo (recovery R6 firing).
**Lands in v0.1.14; consumed by v0.2.0 W52 (weekly review) +
v0.2.0 W58D (deterministic factuality gate).**
**Origin.** `reporting/plans/future_strategy_2026-04-29/reconciliation.md`
§4 C10 named source-row provenance as non-deferrable for v0.2.0 W52.
v0.1.14 PLAN §2.B sequences the substrate ahead of W52 to avoid the
"retrofit provenance into weekly review" sequencing error.

## What this is

A `source_row_locator` is a typed pointer back to a row in the
evidence layer (`accepted_*_state_daily` tables, `*_manual_raw`
tables, `source_daily_garmin`). Every quantitative claim emitted
by an R-rule, X-rule, recommendation prose, or future weekly-review
prose can carry the locator(s) that justify the claim. A consumer
(the user, `hai explain`, v0.2.0 W58D, an external auditor) can
resolve the locator back to the originating row and verify the
claim is honest.

This is not a new audit chain. It is the **typing** of the existing
audit chain. Today, `accepted_recovery_state_daily.derived_from` is
a JSON-encoded list of opaque row refs (per
`001_initial.sql:245`). W-PROV-1 names the schema of the entries in
that list and propagates the schema down to recommendation +
proposal write paths.

## Schema

```jsonc
{
    "table":       "accepted_recovery_state_daily",
    "pk":          {"as_of_date": "2026-04-28", "user_id": "u_local_1"},
    "column":      "resting_hr",
    "row_version": "2026-04-28T19:26:05.234Z"
}
```

Field rules:

- `table` (str, required) — table name in the local SQLite database.
  Must be one of the *evidence* or *accepted-state* tables; never
  a write-side table (no `recommendation_log`, no `proposal_log`,
  no `daily_plan`). Self-citation is meaningless and a
  classification bug; the validator rejects it.
- `pk` (object, required) — composite primary key as
  `{column_name: column_value}` for every PK column of the named
  table. Must match the schema's PK definition exactly. `pk` is
  ordered alphabetically by key name when serialised, so
  byte-stable JSON roundtrip is preserved.
- `column` (str, optional) — name of the specific column being
  cited. If omitted, the locator points at the whole row.
- `row_version` (str, required) — a stable identifier for *this
  version* of the row. Conventionally the row's `projected_at` /
  `ingested_at` / `corrected_at` ISO timestamp; for source tables
  with no version column, a deterministic hash of the row's
  content. Required so a downstream supersession of the row can be
  detected (the resolved row's current `row_version` differs from
  the locator's `row_version` → "this claim cited a row that has
  since been corrected"; v0.2.0 W58D will surface that case).

## Allowed source tables (v0.1.14)

The v0.1.14 demo only emits locators for one domain (recovery).
The validator at `core/provenance/locator.py` whitelists tables by
domain. The v0.1.14 whitelist:

| Domain | Allowed tables | PK shape |
|---|---|---|
| recovery | `accepted_recovery_state_daily` | `(as_of_date, user_id)` |
| recovery | `source_daily_garmin` | `(as_of_date, user_id, export_batch_id, csv_row_index)` |

Other domains' allowed-table lists land when those domains adopt
emission (out of v0.1.14 scope; tracked for v0.1.15+).

## Where locators surface

### Proposal layer (`proposal_log` / `*_proposals.jsonl`)

A new optional field on the proposal payload:

```jsonc
{
    "schema_version": "recovery_proposal.v1",
    "...": "...",
    "policy_decisions": [...],
    "evidence_locators": [
        {"table": "accepted_recovery_state_daily",
         "pk": {"as_of_date": "2026-04-28", "user_id": "u_local_1"},
         "column": "resting_hr",
         "row_version": "2026-04-28T19:26:05.234Z"},
        {"table": "accepted_recovery_state_daily",
         "pk": {"as_of_date": "2026-04-29", "user_id": "u_local_1"},
         "column": "resting_hr",
         "row_version": "2026-04-29T19:26:05.234Z"},
        {"table": "accepted_recovery_state_daily",
         "pk": {"as_of_date": "2026-04-30", "user_id": "u_local_1"},
         "column": "resting_hr",
         "row_version": "2026-04-30T19:26:05.234Z"}
    ]
}
```

`evidence_locators` is **optional** and **additive** — proposals
without locators continue to validate. Recovery is the only domain
that emits locators in v0.1.14; the field is absent on
running/sleep/strength/stress/nutrition proposals.

The schema_version remains `recovery_proposal.v1`. Adding a new
optional field is backwards-compatible per the v0.1.x additive
proposal contract; v0.2.0 W52 may bump to `.v2` if it makes
locators required.

### Recommendation layer (`recommendation_log`)

A new column on `recommendation_log`:

```sql
ALTER TABLE recommendation_log ADD COLUMN evidence_locators_json TEXT;
```

Backwards-compatible additive (NULL on existing rows). Carries the
same JSON array as the proposal layer. Synthesis copies the
proposal's `evidence_locators` onto the resulting recommendation.

### Future surfaces (out of v0.1.14 scope)

- **`weekly_review` (v0.2.0 W52).** Every quantitative claim in
  the weekly-review prose carries an `evidence_locators` list. The
  W58D factuality gate rejects the row if any quantitative claim
  is missing locators (deterministic, no LLM).
- **`claim_block` (v0.2.0 W58D).** The schema name is provisional
  per v0.1.14 D14 round 1 F-PLAN-10. The locator schema in this
  doc is the canonical contract; W58D builds on it without
  re-design.

## Validation

`core/provenance/locator.py::validate_locator(d)` enforces:

1. Object with the four named keys (`table`, `pk`, `column`,
   `row_version`); `column` may be absent or `None`.
2. `table` is a string and is on the v0.1.14 whitelist.
3. `pk` is an object whose keys match the named table's PK schema
   exactly (same set, no extras).
4. `pk` values are scalars (str / int / float; no nested objects).
5. `column` (if present) is a string.
6. `row_version` is a string.

Locator lists are deduplicated by `(table, sorted-pk-pairs, column)`
before serialisation; duplicate locators are a no-op.

## Emission contract (v0.1.14 — recovery R6 only)

When `evaluate_recovery_policy` returns a `RecoveryPolicyResult`
where `forced_action == "escalate_for_user_review"` AND the
forced_action_detail's `reason_token == "resting_hr_spike_3_days_running"`,
the recovery skill must emit `evidence_locators` on the proposal,
listing one locator per `accepted_recovery_state_daily` row that
contributed to the spike count. The locators cite the
`resting_hr` column.

Other R-rule firings (R1 / R5 / R6 with non-spike reason tokens)
**may** emit locators in future cycles but are not required in
v0.1.14.

## Rendering

`hai explain` renders locators in two surfaces:

- **JSON mode** (`hai explain --for-date <d> --user-id <u>`) —
  raw JSON object including the `evidence_locators` array on
  proposal_log + recommendation_log entries (transparently surfaces
  the field; no rendering transform).
- **Markdown mode** (`hai explain --markdown`) — locators rendered
  as a bulleted list under each cited claim:

  ```markdown
  ### Recovery — escalate_for_user_review
  *Resting HR elevated 3 days running.* Source rows:
  - accepted_recovery_state_daily / 2026-04-28 / resting_hr
  - accepted_recovery_state_daily / 2026-04-29 / resting_hr
  - accepted_recovery_state_daily / 2026-04-30 / resting_hr
  ```

## Roundtrip test

`verification/tests/test_source_row_locator_recovery.py` asserts:

1. Construct a fixture with 3 days of `accepted_recovery_state_daily`
   rows, all with elevated resting_hr.
2. Run the recovery domain through `propose` → confirm
   `evidence_locators` appears on the proposal.
3. Synthesize → confirm locators copy to `recommendation_log`.
4. Render `hai explain` JSON → confirm locators present.
5. Render `hai explain` markdown → confirm bulleted-list shape.
6. Resolve each locator back to its row via `provenance.locator.resolve()`
   — confirm the locator → DB-row resolution returns the expected
   resting_hr value.

## Capabilities-manifest impact

`hai capabilities --json` gains a new entry under `domains.recovery`:

```jsonc
{
    "domains": {
        "recovery": {
            "...": "...",
            "emits_evidence_locators": true,
            "evidence_tables": ["accepted_recovery_state_daily",
                                "source_daily_garmin"]
        }
    }
}
```

Per v0.1.14 PLAN.md §3 ship gate "expected diff classes" (F-PLAN-04):
W-PROV-1 is a **named parser/capabilities surface change accepted**;
the `test_cli_parser_capabilities_regression.py` byte-stability
gate accepts the diff via the named-change exemption.

## Why now (vs v0.2.0)

v0.2.0 W52 weekly review aggregates accepted state into prose;
W58D blocks unsupported claims. Building W52 / W58D on the
assumption that provenance can be retrofitted is the most expensive
sequencing error available — v0.2.0 would either ship without
provenance and earn a "provenance retrofit" cycle in v0.2.4, or
spend its 18-24 day budget on substrate work it should have
inherited.

W-PROV-1 v0.1.14 demos the type on **one domain** (recovery R6);
v0.1.15+ extends it to other R-rules; v0.2.0 W52 consumes the
substrate without re-design.

## Out of v0.1.14 scope

- Other domains' R-rule emission (running R-rules, sleep
  R-chronic-deprivation, strength R-rules, nutrition R-vol-spike).
- Locator emission on X-rules.
- Hash-based `row_version` for source tables without timestamp
  columns (v0.1.14 only emits for `accepted_recovery_state_daily`
  which has `projected_at`).
- W58D claim-block schema (v0.2.0 W58D — references this doc as
  the canonical locator contract).
- FActScore-style atomic-claim decomposition over locators
  (v0.2.0 W-FACT-ATOM).
