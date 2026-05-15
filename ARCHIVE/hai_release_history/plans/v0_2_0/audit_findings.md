# v0.2.0 — pre-PLAN audit findings

This file accumulates Phase 0 (D11) findings as they surface, plus
any pre-cycle observations that should be visible to PLAN.md
authoring. Per AGENTS.md "Pre-PLAN bug-hunt" pattern, items here
are tagged with a `cycle_impact` disposition that the
pre-implementation gate (D11) consumes.

**Status.** Phase 0 (D11) bug-hunt active 2026-05-06. Internal
sweep + audit-chain probe complete (Claude). Persona matrix
running. Codex external Phase 0 audit pending — see
`codex_audit_findings_prompt.md`.

**Cycle theme reminder.** v0.2.0 makes claims about the past week
deterministically checkable. W52 weekly review + W58D factuality
gate + W-FACT-ATOM atomic decomposition + 4 doc-only adjuncts.
Substantive tier; 18-24d estimate; one schema group (weekly-review
tables + W58D claim-block).

**`cycle_impact` taxonomy.**
- **`revises-scope`** — finding shifts what the cycle commits to.
  PLAN.md cannot author honestly without addressing it.
- **`aborts-cycle`** — finding invalidates the cycle thesis. End
  the cycle (or restructure scope) before opening.
- **`informational`** — finding is real but doesn't shift scope.
  Worth recording so future audit rounds don't re-discover it.

---

## F-PHASE0-01 — W-PROV-1 substrate is dormant; locator emission must be wired before W52's source-row contract is satisfiable

**Surfaced.** 2026-05-06 internal sweep against HEAD `4c267cc`.

**`cycle_impact` tag.** **`revises-scope`** — substantively. W52
effort line likely grows.

### Evidence

`src/health_agent_infra/core/provenance/locator.py:23` —
`_ALLOWED_TABLES_PK` whitelist contains 2 tables only:

```python
_ALLOWED_TABLES_PK: dict[str, tuple[str, ...]] = {
    "accepted_recovery_state_daily": ("as_of_date", "user_id"),
    "source_daily_garmin": (
        "as_of_date",
        "user_id",
        "export_batch_id",
        "csv_row_index",
    ),
}
```

The whitelist comment names this as "v0.1.14 demo whitelist —
recovery domain only. Other domains add entries here as they adopt
locator emission."

`core/state/projector.py` and `core/writeback/proposal.py` import
the locator module. Grep for actual locator construction at
projection / writeback time:

- `core/state/projector.py:1466` references
  `serialize_locators as _serialize_locators_jsonl` for the JSONL
  re-projection path only.
- `core/writeback/proposal.py:278-287` accepts
  `evidence_locators` *if present in proposal data*
  (`if "evidence_locators" in data:`) — opt-in, not enforced.

**Empirical confirmation.** Direct query against the maintainer's
canonical state DB:

```
SELECT COUNT(*), COUNT(CASE WHEN evidence_locators_json IS NOT NULL THEN 1 END)
FROM recommendation_log;
→ 86, 0
```

**0 of 86 recommendation_log rows carry locators.** No domain
classifier currently emits them at proposal time.

### Why this matters for v0.2.0

W52's contract per `reporting/plans/v0_2_0/README.md` §6.1 (Scope
table row 1): "Source-row locators required for every quantitative
claim." W58D's contract per row 2: "Every quoted quantitative
claim in weekly-review prose must resolve to a source-row locator.
Blocking from day 1."

Both contracts assume a *consumable* substrate. The substrate is
*capable* (validate, dedupe, serialize, deserialize all work) but
*not currently filled*. W52 cannot ship its source-row claim
without first wiring locator emission across the 5 currently-
dormant domains' classify / projector / writeback paths.

### Likely fix shape

Two reasonable absorption paths:

- **Absorb into W52's effort line** as the first sub-acceptance
  criterion — W52 cannot ship without locator emission across the
  6 domains it aggregates over. Effort line moves from 6-8d to
  8-12d.
- **Split into W-PROV-2** — pre-W52 substrate-readiness workstream.
  Expand `_ALLOWED_TABLES_PK` to include accepted-state tables for
  all 6 domains + `intent_log`, `target_log`, `recommendation_log`,
  `x_rule_firing_log`, `review_outcome`, `data_quality_log`.
  Wire locator construction into each domain's projector /
  classify / writeback path. ~2-4d. W52 then consumes a fully-
  populated substrate.

The second is cleaner from an audit-chain perspective (W-PROV-2
becomes its own WS with its own acceptance) but adds an extra W-id
to the cycle. PLAN.md author makes the call.

### What changes the answer

A reading of `core/synthesis.py` + the per-domain `classify.py`
files that I haven't yet done could surface that locators are
*conceptually* derivable from the classified-state structure
(every band cites a metric → every metric cites a column on a
known accepted-state table → locator = (table, pk={as_of_date,
user_id}, row_version, column=metric_column)). If derivation is
mechanical, the wiring is closer to 2d than 4d.

---

## F-PHASE0-02 — Calendar-coverage gaps in maintainer dogfood; W52 weekly aggregation must abstain at weekly grain

**Surfaced.** 2026-05-06 audit-chain probe via `hai explain`.

**`cycle_impact` tag.** **`revises-scope`** — W52 design must
include partial-week semantics.

### Evidence

`hai explain --for-date YYYY-MM-DD --user-id u_local_1` for each
day in the prior 14:

| Date | Plan? |
|---|---|
| 2026-05-06 | ✓ |
| 2026-05-05 | ✗ no plan |
| 2026-05-04 | ✓ |
| 2026-05-03 | ✗ no plan |
| 2026-05-02 | ✓ |
| 2026-05-01 | ✗ no plan |
| 2026-04-30 | ✓ |
| 2026-04-29 | ✗ no plan |
| 2026-04-28 | ✓ (also `_v2`, both canonical) |
| 2026-04-27 | ✓ |
| 2026-04-26 | ✓ |
| 2026-04-25 | ✓ |
| 2026-04-24 | ✓ (5-version supersession chain — see F-PHASE0-07) |
| 2026-04-23 | ✓ (also `_v2`, `_v3`) |

Alternating-day gap pattern in early May — likely the maintainer
not running `hai daily` on weekend / off days, not a runtime bug.
But it's the empirical shape W52 will encounter.

### Why this matters for v0.2.0

W52 aggregates *across* days within a week. If a week has 4 of 7
days plan-populated, W52 must define behaviour:

- **Render-with-coverage-band.** Render the prose with an explicit
  coverage qualifier ("4 of 7 days analyzed").
- **Abstain-at-weekly-grain.** Set `weekly_status='insufficient_data'`
  if coverage < threshold (e.g., < 5 of 7 days), refuse to render
  prose. Mirrors v0.1.15 W-D arm-1's
  `nutrition_status='insufficient_data'` shape at weekly granularity.
- **Hybrid.** Render with coverage band if coverage ≥ 4 of 7, abstain
  if < 4.

PLAN.md must specify the threshold + the rendering branch. W58D's
factuality contract piles on: every numeric claim must resolve to
a source row, so the abstain branch must also abstain on numeric
claims (no "average HRV: 52 ms" if 3 of 7 days are missing).

### Likely fix shape

Add a §-acceptance line to W52: "Weekly review specifies coverage
threshold + abstain branch. Threshold value lives in
`thresholds.toml` per D13. Abstain branch tested against the
maintainer's own state DB (calendar-gap fixture)."

---

## F-PHASE0-03 — `hai doctor` surfaces F-PV14-01 source-contamination warning on canonical state DB; W52 data-quality rollup must distinguish stale-pull from genuinely-old-data

**Surfaced.** 2026-05-06 audit-chain probe via `hai doctor`.

**`cycle_impact` tag.** **`revises-scope`** — W52 data-quality
semantics must be specified.

### Evidence

`hai doctor` output:

```
## sources  [WARN] warn
  reason: one or more sources have a sync row whose for_date is >48h
  before the run timestamp (F-PV14-01 contamination shape — may indicate
  fixture data was projected into the canonical DB)
  garmin: last=2026-05-06T09:52:26.718171+00:00 stale=14.1h
  garmin_live: last=2026-05-06T09:52:26.659973+00:00 stale=14.1h
  ...
```

`hai stats` cross-reference (specific stale-decoration rows):

```
garmin           last 2026-05-06 ok        for 2026-02-10  (~86 days gap)
garmin_live      last 2026-05-06 ok        for 2026-04-17  (~19 days gap)
readiness_manual last 2026-05-06 ok        for 2026-04-08  (~28 days gap)
```

### Why this matters for v0.2.0

W52's "data quality" rollup column reads `for_date` per source per
day. It must distinguish:

- **Stale because pull is stale** — `garmin_live` for_date=2026-04-17
  with last_pull_at=2026-05-06: pull was attempted but no fresher
  data was returned. W52 should surface this as "data freshness
  warning."
- **Stale because data is genuinely about an older day** —
  `readiness_manual` for_date=2026-04-08 reflects a manual
  retrospective entry. W52 should NOT flag this as freshness
  warning; it should flag it as "manual entry, retrospective" if
  flagging at all.

The `for_date` column alone doesn't disambiguate. W52 needs either
an additional `entry_mode` column or a heuristic (manual sources
treated retrospective by default; auto-pull sources treated stale
when for_date < last_pull_at − 48h).

### Likely fix shape

Add §-acceptance line to W52: "Data-quality rollup specifies
`stale_pull` vs `retrospective_manual` distinction. Tested against
the maintainer's own state DB (F-PV14-01 contamination shape
present)."

May also surface a v0.2.0 hardening sub-task: "rerun source-
contamination cleanup on the maintainer's canonical state DB
before W52 fixture-build" — but that's maintainer-action, not
runtime change.

---

## F-PHASE0-04 — `recommendation_evidence_card.v1` carrier exists only in proposal docs; v0.2.0 schema group must include it

**Surfaced.** 2026-05-06 internal sweep, grep for
`recommendation_evidence_card`.

**`cycle_impact` tag.** **`informational`** — already implied by
README §6.1, flagging for explicit naming in PLAN.md.

### Evidence

Grep across `src/`: no hits.
Grep across `reporting/plans/future_strategy_2026-04-29/`:

```
reconciliation.md:149: | C8 | **Evidence-card schema** as concrete
deterministic audit artifact (`recommendation_evidence_card.v1`). |
review_codex.md:1484: "schema_version": "recommendation_evidence_card.v1",
review_codex.md:1551: CREATE TABLE recommendation_evidence_card (
```

Schema sketched at `review_codex.md:1551`. No runtime table.

### Why this matters for v0.2.0

v0.2.0 README §6.1 names
`recommendation_evidence_card.v1` as the carrier for source-row
locators. v0.2.0's "one schema group" includes weekly-review tables
+ W58D claim-block — PLAN.md must explicitly name the
`recommendation_evidence_card` migration as part of the group, not
silently fold it into W58D acceptance.

### Likely fix shape

PLAN.md §2 W58D contract section must include "migration adds
`recommendation_evidence_card` table per
`future_strategy_2026-04-29/review_codex.md:1551` schema sketch."
Schema-group count remains 1 (claim-block + evidence-card carrier
are conceptually one group per reconciliation C6).

---

## F-PHASE0-05 — Existing `hai review` surface is `record/schedule/summary`; weekly aggregation is greenfield

**Surfaced.** 2026-05-06 internal sweep + capabilities manifest
probe.

**`cycle_impact` tag.** **`informational`** — confirms README §6.1
greenfield assumption.

### Evidence

`uv run hai capabilities --json` filtered to `hai review`:

```
review_cmds: ['hai review record', 'hai review schedule', 'hai review summary']
```

No `hai review weekly` exists. Total `hai` commands: 67 (unchanged
from v0.1.18 baseline).

### Why this matters for v0.2.0

Confirms the cycle's W52 commitment. PLAN.md should not assume
ANY pre-existing `weekly` scaffolding to lift; everything is new
code. Capabilities manifest count grows from 67 → 68 (or more if
`hai review weekly` introduces sub-flags as separate manifest
entries — likely not, single command + flag combinations).

---

## F-PHASE0-06 — `core/review/summary.py` (W48, 515 LOC) is per-domain outcome-token builder, not a W52 building block

**Surfaced.** 2026-05-06 internal sweep, read
`core/review/summary.py:1-60`.

**`cycle_impact` tag.** **`informational`** — establishes the
boundary between W48 and W52.

### Evidence

`core/review/summary.py` docstring lines 1-23 describe the W48
contract: emit per-domain outcome-pattern tokens
(`outcome_pattern_recent_negative`, etc.) over a rolling window
ending at `as_of_date`. Visibility-only; never mutates thresholds,
classifiers, policy, X-rules, confidence, intent, or targets.

### Why this matters for v0.2.0

W52 is a *different* aggregation from W48:

- **W48 aggregation** — per-domain outcome tokens over a rolling
  window. Surface: `hai review summary`. Substrate consumed:
  `recommendation_log` + `review_event` + `review_outcome`.
- **W52 aggregation** — week-scoped multi-axis aggregation. Surface:
  `hai review weekly`. Substrate consumed: accepted-state +
  intent_log + target_log + recommendation_log + x_rule_firing_log
  + review_outcome + data_quality_log.

PLAN.md should reference W48 for *outcome-tokens* (W52 may surface
them as part of weekly review prose) but build W52's aggregation
on its own queries. Do NOT lift W48 code as a W52 starting point —
the substrate-consumed shape differs.

---

## F-PHASE0-07 — 5-version supersession chain at 2026-04-24; useful test fixture for W52 supersession-reconciliation

**Surfaced.** 2026-05-06 audit-chain probe via direct sqlite read.

**`cycle_impact` tag.** **`informational`** — fixture material,
not a bug.

### Evidence

`SELECT for_date, daily_plan_id, superseded_by_plan_id FROM daily_plan WHERE for_date='2026-04-24';`:

```
2026-04-24 | plan_2026-04-24_u_local_1     | plan_2026-04-24_u_local_1_v4
2026-04-24 | plan_2026-04-24_u_local_1_v2  | plan_2026-04-24_u_local_1_v3
2026-04-24 | plan_2026-04-24_u_local_1_v3  | (NULL - canonical)
2026-04-24 | plan_2026-04-24_u_local_1_v4  | plan_2026-04-24_u_local_1_v5
2026-04-24 | plan_2026-04-24_u_local_1_v5  | (NULL - canonical)
```

Two parallel chains: `_v1 → _v4 → _v5` (canonical) and
`_v2 → _v3` (canonical). **Both `_v3` and `_v5` have `NULL`
superseded_by — so the day has TWO non-superseded plans.**

This is the v0.1.14 D1 re-author shape; both chains are valid
audit history.

### Why this matters for v0.2.0

W52's weekly query must:
1. Filter on `superseded_by_plan_id IS NULL` to skip mid-chain rows.
2. Handle the multi-canonical case (one day with multiple non-
   superseded plans). Either rolling-window-takes-latest-by-
   synthesized_at OR explicit "multiple plans this day, ambiguous,
   surface both" disposition.

PLAN.md should specify which. The maintainer's own DB is the
fixture.

---

## F-PHASE0-08 — Failed `hai daily` runs at 2026-05-06T09:28 emit no `error_class` or `error_message`; observability hole in W52's data-quality input

**Surfaced.** 2026-05-06 audit-chain probe via direct sqlite read.

**`cycle_impact` tag.** **`informational`** — observability gap;
absorption path TBD by PLAN.md author.

### Evidence

```
SELECT started_at, command, status, error_class, error_message
FROM runtime_event_log
WHERE started_at LIKE '2026-05-06T09:28%';

2026-05-06T09:28:07.614296+00:00 | daily | failed | (NULL) | (NULL)
2026-05-06T09:28:08.547825+00:00 | daily | failed | (NULL) | (NULL)
2026-05-06T09:28:09.791648+00:00 | daily | failed | (NULL) | (NULL)
2026-05-06T09:28:10.706523+00:00 | daily | failed | (NULL) | (NULL)
```

4 failures in 3 seconds. Both `error_class` and `error_message` are
NULL. Cannot determine root cause from the log alone.

### Why this matters for v0.2.0

W52's data-quality rollup will read `runtime_event_log` for "what
percentage of daily runs failed this week, and why?" If failed-run
rows lack error_class / error_message, the rollup will undercount
runtime issues (N rows with status='failed' but no signal as to
why → narrative is "N failures, root cause unknown").

### Likely fix shape

Two reasonable paths:

- **Defer** — file as v0.2.1 carry-forward (W-RUNTIME-EVENT-OBSERVABILITY).
  W52 surfaces "N failures, error_class missing in M of N rows" as
  honest data-quality narrative.
- **Absorb into v0.2.0** — fix the runtime_event_log emission path
  in `cli/__init__.py` exception handler so error_class +
  error_message always populate on `status='failed'` rows. Likely
  a small W-id (~0.5-1d). Would let W52's data-quality narrative
  be sharper from day 1.

The deferral path is fine; the absorb path is preferable if the
maintainer values having clean fixture data for W52 from day 1.
PLAN.md author makes the call.

---

## Phase 0 sweep coverage so far (Claude — 2026-05-06)

| Sweep step | Status | Findings surfaced |
|---|---|---|
| 1. Internal sweep | DONE | F-PHASE0-01, F-PHASE0-04, F-PHASE0-05, F-PHASE0-06 |
| 2. Audit-chain probe | DONE | F-PHASE0-02, F-PHASE0-03, F-PHASE0-07, F-PHASE0-08 |
| 3. Persona matrix | DONE | 13/13 with **0 findings + 0 crashes** (baseline holds; matches v0.1.18 close) |
| 4. Codex external Phase 0 audit | DONE — verdict `PROCEED_WITH_REVISIONS`; round 1 sufficient | F-PHASE0-09..13 (5 findings: 2 revises-scope, 3 informational) + agree-with-additions on F-PHASE0-01, F-PHASE0-03, F-PHASE0-04, F-PHASE0-08 |
| 5. Pre-implementation gate | NOT YET FIRED | maintainer reads consolidated findings |

---

## Codex round 1 — additions, agreements, corrections

**Source.** `reporting/plans/v0_2_0/codex_audit_findings_response.md`
(verdict `PROCEED_WITH_REVISIONS`; 5 new findings, all verified
by Claude against cited file:line on 2026-05-06 before
consolidation).

### F-PHASE0-09 — Weekly claim-cards are NOT daily evidence-cards (revises-scope, F-PHASE0-04 corrects)

**Codex Q-bucket Q2 / Q4. Severity revises-scope.**

`reporting/plans/future_strategy_2026-04-29/review_codex.md:1486`
sets `recommendation_evidence_card.v1` `scope="daily_recommendation"`.
Line 1614 explicitly says: "Future `hai review weekly`: use weekly
claim cards, not daily recommendation cards, for
quantitative/comparative weekly claims."

**Impact on F-PHASE0-04.** My F-PHASE0-04 named
`recommendation_evidence_card.v1` as the W52 carrier. That's wrong
— the carrier is daily-scoped per the proposal docs. **W52 needs
a separate weekly claim-card schema**, keyed by week + user +
claim_id + prose span + derivation + locator-set. The
`recommendation_evidence_card` table (if it lands in v0.2.0)
serves W58D's daily-recommendation factuality lane, not W52's
aggregate claims.

**PLAN.md scope-shape change.** The schema-group description
"weekly-review tables + W58D claim-block" must be unpacked into:
- weekly-review aggregation tables (W52),
- weekly claim-card carrier (W52 + W58D — keys per weekly claim),
- daily `recommendation_evidence_card` (optional in v0.2.0; if
  scoped, scope explicitly).

**Maintainer open question (Codex Q1):** "Should v0.2.0 land
daily `recommendation_evidence_card` plus weekly claim cards, or
only the weekly claim-block carrier needed for W52/W58D?"

### F-PHASE0-10 — Existing judge_adversarial corpus is shape-only; W58D needs its own deterministic scoring corpus (revises-scope, missed by Claude internal sweep)

**Codex Q-bucket Q1 / Q5. Severity revises-scope.**

`src/health_agent_infra/evals/cli.py:26-29` (verbatim): "judge_adversarial
which is fixture-only (W-AI corpus; no scoring path until v0.2.2
W58J wires the judge harness)." Lines 100-102 confirm
`_emit_judge_adversarial_summary` is shape-only.
`verification/tests/test_judge_adversarial_fixtures.py` only pins
fixture shape and counts, not pass/fail scoring.

**Impact.** v0.2.0 README §6.1 W58D acceptance says "tested against
a corpus of known-good and known-bad examples" without naming
the corpus. The 30-fixture judge_adversarial corpus does NOT
satisfy this — it's W58J prep, not W58D substrate.

**PLAN.md scope-shape change.** W58D needs:
- A separate deterministic factuality corpus (likely seeded from
  source-conflict fixtures the existing eval tree already has),
- A deterministic scoring runner (no LLM, no shape-only),
- Quantitative acceptance: `block ≥X% known-bad / pass ≥Y%
  known-good` thresholds.

**Maintainer open question (Codex Q2):** "What W58D corpus
threshold is acceptable for PLAN.md: exact 100% over a smaller
deterministic corpus, or a larger corpus with explicit
block/pass percentages?"

### F-PHASE0-11 — D16 destination wording drift in v0.2.0 README and tactical plan (informational, doc-only fix)

**Codex Q-bucket Q6. Severity informational.**

Two drift sites verified by Claude:

- `reporting/plans/v0_2_0/README.md:39` — "otherwise carries
  forward to v0.2.1." **D16 says re-evaluation is at v0.4 review,
  not v0.2.1.** Authored by Claude in the workspace stub before
  the strategic_plan_v2 + D16 propagation sweep was complete.
- `reporting/plans/tactical_plan_v0_1_x.md:880-882` — "sequenced
  after the v0.1.15 foreign-user candidate session and v0.1.16
  empirical-fix consolidation." **v0.1.16 was cancelled; v0.1.19
  was cancelled per CP-2U-GATE-SPLIT D16.** Pre-D16 wording the
  refresh sweep didn't catch.

**PLAN.md scope-shape change.** Doc-only — fix the two sites
during the v0.2.0 README + tactical-plan §6.1 touch-up that the
PLAN authoring will trigger. **No PLAN scope delta**; this is a
freshness-sweep oversight, not a cycle-design issue.

### F-PHASE0-12 — F-PHASE0-01 fix recommendation conflates source-row locators with write-side audit-chain references (informational; corrects F-PHASE0-01)

**Codex Q-bucket Q8. Severity informational. SUBSTANTIVELY
RESHAPES F-PHASE0-01.**

`reporting/docs/archive/cycle_artifacts/source_row_provenance.md:42-46`
specifies the W-PROV-1 contract: "`table` ... must be one of the
*evidence* or *accepted-state* tables; never a write-side table
(no `recommendation_log`, no `proposal_log`, no `daily_plan`).
Self-citation is meaningless and a classification bug; the
validator rejects it."

**My F-PHASE0-01 fix recommendation said** to expand
`_ALLOWED_TABLES_PK` with `intent_log`, `target_log`,
`recommendation_log`, `x_rule_firing_log`, `review_outcome`,
`data_quality_log`. **That violates the W-PROV-1 contract** —
those are write-side audit-chain tables.

Additional drift Codex caught: actual table names are
`intent_item` (migration 019), `target` (020), `x_rule_firing`
(003), `data_quality_daily` (021). Verified via direct
`.tables` query against the maintainer's state DB.

**Correct architecture (per Codex + `review_codex.md:1529-1537`):**
- `_ALLOWED_TABLES_PK` extends with **accepted-state tables**
  for the 5 dormant domains (running, sleep, stress, strength,
  nutrition). Source-row locators stay source/evidence-only.
- Write-side audit-chain references (recommendation_id,
  planned_id, proposal_id, firing_id, outcome_id) go inside
  the **weekly claim-card / evidence-card provenance payload**
  as separate fields, NOT as `SourceRowLocator` instances.

**Impact on F-PHASE0-01 fix recommendation.** The "expand
whitelist with audit-chain tables" path is wrong. The correct
W-PROV-2 (or W52 sub-acceptance) shape:
1. Extend `_ALLOWED_TABLES_PK` with 5 accepted-state-table
   entries (one per dormant domain).
2. Wire locator construction into each domain's classify /
   projector / writeback path. Recovery R6 spike-locator path
   (`domains/recovery/policy.py:215-230`) is the existing
   reference shape; replicate per domain.
3. Design the weekly claim-card payload structure with separate
   lanes for source-row locators AND audit-chain references.
4. The card validates locators per W-PROV-1 contract; validates
   audit-chain refs as plain primary keys (no
   `SourceRowLocator` shape).

**Recovery R6 reference path:** `domains/recovery/policy.py:180-188`
docstring + `:215-230` conditional emission. R6 fires
`escalate_for_user_review` with `resting_hr_spike_3_days_running`
token AND optional args; emits one locator per spike day. **My
F-PHASE0-01 "0 of 86 rows" empirical was correct, but the prose
"no domain currently emits locators at writeback time" was
overclaim — recovery R6 does emit conditionally; it just hasn't
fired against the maintainer's data.**

### F-PHASE0-13 — v0.2.0-specific abort/rollback/conditional-absorb criteria are not yet named (informational, missed by Claude)

**Codex Q-bucket Q7. Severity informational.**

`reporting/plans/v0_2_0/README.md:59-62` names the generic
`aborts-cycle` tag; lines 83-91 give the ship sequence but no
v0.2.0-specific abort triggers or rollback shape.
`tactical_plan_v0_1_x.md:906-910` confirms v0.2.0 is schema-
bearing (new tables = ledger-shape mutations, hence rollback is
not `git revert`-shaped).

My F-PHASE0-08 left "absorb into v0.2.0 vs defer to v0.2.1" as
PLAN-author choice without naming the criterion.

**Impact on PLAN.md authoring.** Add a small risk/decision
section per Codex's recommendation:
- **Abort triggers:** if W-PROV-2 cannot produce locators within
  the agreed budget (≤4d). If W58D cannot hit its corpus
  threshold (per F-PHASE0-10 maintainer answer).
- **Rollback shape:** forward-only migrations. A v0.2.0.1 hotfix
  can introduce a forward migration that null-defaults new
  columns or drops a flag; **never** `git revert` of a schema-
  bearing release.
- **F-PHASE0-08 absorb criterion:** absorb if missing
  `error_class` / `error_message` rows affect W52 fixture weeks
  OR exceed N% of failed runs in the past 30 days. Defer
  otherwise.

### Codex review of Claude's F-PHASE0-01..08

For audit-chain integrity, Codex's verdicts on Claude's findings:

- **F-PHASE0-01 agree-with-additions.** Recovery R6 path partially
  emits (see F-PHASE0-12); whitelist proposal corrected by F-PHASE0-12.
- **F-PHASE0-02 agree.**
- **F-PHASE0-03 agree-with-additions.** `data_quality_daily`
  stores freshness hours, coverage, missingness, flags — but NOT
  `last_successful_sync_at`, `for_date`, entry mode, or runtime
  failure cause (`core/data_quality/projector.py:90-123`;
  `migrations/021_data_quality.sql:20-40`). W52 will need joins
  to `sync_run_log` / `runtime_event_log` OR a schema extension.
- **F-PHASE0-04 agree-with-additions.** Schema-group count can
  remain one, but the carrier shape must resolve daily vs
  weekly per F-PHASE0-09 first.
- **F-PHASE0-05 agree.** Cited `cli/__init__.py:1141-1253`.
- **F-PHASE0-06 agree.**
- **F-PHASE0-07 agree.**
- **F-PHASE0-08 agree-with-additions.** Defer path viable only
  if W52 explicitly surfaces "failure cause unknown" prose AND
  PLAN names the threshold (per F-PHASE0-13).

### Open questions Codex surfaced for maintainer

1. **W52 carrier scope:** v0.2.0 lands daily
   `recommendation_evidence_card` PLUS weekly claim cards, OR
   only the weekly claim-block carrier needed for W52/W58D?
2. **W58D corpus threshold:** exact 100% over a smaller
   deterministic corpus, OR larger corpus with explicit
   block/pass percentages?
3. **W-2U-GATE-2 destination:** v0.2.0-only opportunistic window
   with v0.4 re-evaluation per D16, OR deliberate v0.2.1
   carry-forward row despite D16?

### Maintainer adjudication (2026-05-06 chat)

1. **Daily + weekly carrier.** Both ship in v0.2.0. Reasoning
   (paraphrased): "always make it more rigourous." v0.2.0
   schema group becomes the evidence-card family — daily
   `recommendation_evidence_card` (W52 substrate; v0.2.2 W58J
   consumer) plus weekly claim-card carrier (W52 + W58D).
   Schema-group count stays at 1 per reconciliation C6 (the
   carriers are conceptually one family). Effort moves
   v0.2.0 toward 28-31d.
2. **Percentage over larger corpus.** W58D acceptance specifies
   `block ≥X% known-bad / pass ≥Y% known-good` thresholds.
   PLAN.md proposes actual X / Y percentages + corpus size;
   D14 round pressure-tests the proposal.
3. **Honor D16 + fix README drift.** Maintainer answer "the
   second user is TBC" interpreted as: candidate availability
   is TBC, gate destination is D16's default
   (opportunistic-not-blocking during v0.2.0, formal re-eval
   at v0.4 review). README:39 + tactical §6.1:880-882 drift
   per F-PHASE0-11 fixes during PLAN authoring. AGENTS.md D16
   unchanged. If W-2U-GATE-2 fires (a candidate appears),
   v0.2.0 runs the session; if not, RELEASE_PROOF names "did
   not fire" + carries opportunistic flag forward to v0.2.1
   per D16 wording.

---

## Pre-implementation gate dispositions (consolidated, post-Codex)

**`revises-scope` cluster (5 findings):**

- **F-PHASE0-01** (sharpened by F-PHASE0-12): PLAN.md must
  include explicit W-PROV-2 workstream OR W52 sub-acceptance for
  **accepted-state-table** locator emission across 5 dormant
  domains. Audit-chain references go in the claim-card payload,
  NOT in `_ALLOWED_TABLES_PK`. W52 effort grows ~2-4d.
- **F-PHASE0-02**: W52 acceptance specifies coverage threshold
  + abstain branch.
- **F-PHASE0-03** (sharpened by Codex review): W52 data-quality
  acceptance specifies `stale_pull` vs `retrospective_manual`
  distinction. Either a schema extension OR explicit joins to
  `sync_run_log` / `runtime_event_log`.
- **F-PHASE0-09**: PLAN.md scopes weekly claim-card carrier
  separate from daily `recommendation_evidence_card`. Maintainer
  adjudicates whether daily carrier ships in v0.2.0 (Codex
  open-question 1).
- **F-PHASE0-10**: PLAN.md adds W58D deterministic corpus +
  scoring runner + quantitative acceptance threshold. Maintainer
  adjudicates threshold shape (Codex open-question 2).

**`informational` cluster (6 findings):**

- **F-PHASE0-04** (subsumed by F-PHASE0-09): no separate action;
  PLAN.md authoring resolves via F-PHASE0-09.
- **F-PHASE0-05**: no PLAN delta; confirms greenfield.
- **F-PHASE0-06**: PLAN.md notes W48 vs W52 boundary.
- **F-PHASE0-07**: W52 acceptance includes supersession-
  reconciliation test using maintainer's 04-24 DB fixture.
- **F-PHASE0-08** (sharpened by F-PHASE0-13): absorb-vs-defer
  criterion named in PLAN.md per F-PHASE0-13 recommendation.
- **F-PHASE0-11**: doc-only fix on README.md:39 + tactical
  §6.1:880-882 during PLAN authoring touch-up.
- **F-PHASE0-12**: architectural correction folded into
  F-PHASE0-01 fix recommendation; no new W-id.
- **F-PHASE0-13**: PLAN.md adds risk/decision section with
  v0.2.0-specific abort triggers + rollback shape +
  F-PHASE0-08 absorb criterion.

**No `aborts-cycle` findings.** v0.2.0 thesis (make claims about
the past week deterministically checkable) holds. Five findings
sharpen scope; the cycle absorbs them in PLAN.md authoring after
the maintainer adjudicates the three Codex open questions.

**Updated effort estimate (post-adjudication).** README §6.3
baseline was 18-24d. Post-Codex + maintainer adjudication
(daily+weekly carrier per Q1):
- W52 ≈ 6-8d → 9-13d (locator emission + supersession-
  reconciliation + abstain-at-weekly-grain + weekly claim-
  card writeback).
- W58D ≈ 4-6d → 5-8d (deterministic corpus + scoring runner +
  percentage-threshold acceptance).
- W-PROV-2 (separate workstream, accepted-state tables only) ≈
  2-4d.
- Daily `recommendation_evidence_card` carrier (added by Q1
  adjudication) ≈ 3-5d.
- Doc-only adjuncts: 4-7d combined.
- Total: **23-37d**, substantive tier. **Calibration concern:**
  the upper bound brushes the 6-week PR-fatigue threshold; PLAN
  authoring should consider whether the daily-card carrier
  could ship as a stub-then-fill split (skeleton in v0.2.0,
  full population in v0.2.1) if effort tightens.

---

*Phase 0 sweep authored 2026-05-06 by Claude. Codex round 1
appended 2026-05-06 verdict `PROCEED_WITH_REVISIONS`. All Codex
findings verified by Claude against cited file:line before
consolidation. Maintainer adjudication of 3 Codex open
questions appended 2026-05-06 chat. Pre-implementation gate
**FIRED 2026-05-06**: scope locked, PLAN.md authoring opens
against the consolidated scope-shape.*
