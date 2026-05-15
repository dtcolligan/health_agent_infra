# Standards mapping (W55, v0.1.8)

> **Status.** Inspirational reference, NOT a dependency surface.
> health-agent-infra is a local-first governed runtime; we read
> external standards for vocabulary alignment, not as a contract
> we adopt.

This doc maps the project's ledger concepts to four well-known
external standards so a contributor can decide whether to *align*
a new field with FHIR / Open mHealth / Open Wearables vocabulary
without thinking they MUST.

The project deliberately does NOT depend on any of these
standards. The reasons are documented at the bottom under
"NOT a FHIR dependency."

---

## Mapping table

| HAI ledger / surface | FHIR analogue | Open mHealth / Open Wearables analogue | Notes |
|---|---|---|---|
| **Evidence Ledger** (`source_daily_garmin`, `nutrition_intake_raw`, `gym_session`, etc.) | [Observation](https://www.hl7.org/fhir/observation.html) | [Open mHealth datapoint schemas](https://github.com/openmhealth/schemas) — `physical-activity`, `heart-rate`, `sleep-duration`, `body-weight` | Both standards model "an observed measurement at a point in time with provenance." HAI carries the same shape under a flat per-source table; provenance lives on every row (`source` + `ingest_actor`). |
| **Accepted State Ledger** (`accepted_recovery_state_daily`, etc.) | Observation (with `derivedFrom`) | Aggregated datapoints in Open mHealth | HAI's accepted-state rows are a projector-authored canonical view of evidence; FHIR's `derivedFrom` reference + `Observation.component` parallel the `derived_from` JSON array we carry. |
| **Recommendation Ledger** (`recommendation_log`) | [CarePlan.activity.detail](https://www.hl7.org/fhir/careplan.html) | n/a — Open mHealth doesn't model recommendations | A CarePlan activity detail names a planned intervention with a status; HAI carries the same shape (action enum, action_detail, confidence) plus a stronger audit chain via supersede links. |
| **Plan Ledger** (`daily_plan`) | [CarePlan](https://www.hl7.org/fhir/careplan.html) | n/a | A CarePlan is a versioned bundle of planned activities for a subject. HAI's `daily_plan` is the same shape narrowed to a one-day grain plus the supersession discipline FHIR omits. |
| **Review Ledger** (`review_event`, `review_outcome`) | [Procedure](https://www.hl7.org/fhir/procedure.html) (performed) + [Observation](https://www.hl7.org/fhir/observation.html) (outcome question) | n/a | FHIR splits "did the activity happen" and "what did the patient/clinician observe" across two resources. HAI carries both on `review_outcome` with the M4 enrichment columns (completed / intensity_delta / pre_energy / post_energy). |
| **Intent Ledger** (`intent_item`, W49) | [Goal](https://www.hl7.org/fhir/goal.html) (where intent is target-shaped) or `CarePlan.activity` (where intent is session-shaped) | n/a | FHIR Goal models a desired achievement with status / start_date / due_date; HAI Intent generalises this to user-authored sessions, sleep windows, rest days, travel, constraints — the union of "intended state" the runtime can interpret outcomes against. |
| **Target Ledger** (`target`, W50) | [Goal](https://www.hl7.org/fhir/goal.html) | n/a | A FHIR Goal carries `target.measure` + `target.detail` + `target.due`. HAI Target carries `target_type` + `value_json` + `unit` + `lower_bound` / `upper_bound` + `effective_from` / `effective_to` / `review_after`. Same shape; HAI is opinionated about the v1 vocabulary (hydration_ml, protein_g, calories_kcal, sleep_duration_h, sleep_window, training_load, other). |
| **Data Quality Ledger** (`data_quality_daily`, W51) | [Observation.dataAbsentReason](https://www.hl7.org/fhir/datatypes.html#dataAbsentReason) | n/a | FHIR uses `dataAbsentReason` codes on Observation to mark missing data. HAI surfaces missingness + cold-start + freshness as a first-class row instead of burying it inside per-domain uncertainty (per Lee et al., PMC10654909, on consumer-wearable accuracy). |
| **Provenance** (every ledger row's `source`, `ingest_actor`, `ingested_at`, `corrected_at`) | [Provenance](https://www.hl7.org/fhir/provenance.html) | Open mHealth `acquisition_provenance` | FHIR Provenance is a separate resource referenced by activity records; HAI inlines the two-dimension provenance per-row (fact origin + transport actor). Same intent, denser shape. |
| **Configuration** (`thresholds.toml`, `policy.review_summary`, etc.) | n/a | n/a | Configuration is intentionally HAI-local — neither standard models classifier-band thresholds. |

---

## When to align with a standard

A new field should align with the listed standard's vocabulary when:

1. **The field will likely cross a clinical / interoperability
   boundary later.** Things named like FHIR fields are easier to
   surface to a Provider Resource Server in v0.5+ when we get there.
2. **The standard's vocabulary is more precise than ours.** E.g.
   FHIR `Goal.lifecycleStatus` includes `proposed | active |
   accepted | on-hold | completed | cancelled | entered-in-error |
   rejected` — strictly richer than HAI's `proposed | active |
   superseded | archived`. If the runtime needs `on-hold` later,
   adopt the FHIR token rather than inventing a new one.

A new field should NOT align with a standard when:

1. **The standard would force a heavier schema than the runtime
   needs.** FHIR Observation has 30+ optional fields; HAI's per-
   source tables are flat and that's a feature, not a regression.
2. **The standard would obscure HAI's invariants.** FHIR Provenance
   would let provenance be a separate resource; that breaks our
   "every row carries its own provenance" invariant which keeps the
   audit chain readable in SQL.
3. **The standard implies clinical claims HAI refuses to make.**
   Anything FHIR-Goal-like that suggests medical-grade tracking
   should NOT be adopted; HAI's targets are wellness support.

---

## NOT a FHIR dependency

The project deliberately does not import FHIR, Open mHealth, or
Open Wearables as dependencies. Reasoning:

- **Local-first.** FHIR's reference model assumes a server at the
  other end of every resource link. HAI keeps everything local; we
  can't satisfy a FHIR Provider Resource Server contract from a
  SQLite file on the user's machine.
- **Governed runtime.** HAI's invariants — append-only evidence,
  archive/supersede over UPDATE, every row has provenance — are a
  superset of what the standards require. Importing a standard
  would commit us to its weaker invariants in places we have
  stronger ones.
- **Small-team-maintainable.** FHIR Observation alone has more
  optional fields than HAI's entire raw evidence layer. Keeping the
  schema small is what lets one maintainer ship reproducibly.
- **No medical claims.** FHIR is primarily a clinical
  interoperability standard. HAI's `non_goals.md` explicitly
  forbids clinical / diagnostic / training-prescription claims.
  Adopting FHIR vocabulary as a dependency would undermine that
  positioning.

If a bounded clinical export is ever explicitly scoped, a "FHIR projection
layer" would land as a separate optional module — not as a dependency on the
core runtime.
