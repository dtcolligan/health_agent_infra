# Codex External Audit — v0.2.0 PLAN.md (D14 round 2)

> **Why this round.** D14 round 1 closed `PLAN_COHERENT_WITH_REVISIONS`
> with 10 findings — clean settling shape matching the v0.1.11 +
> v0.1.12 + v0.1.17 substantive-PLAN R1 baseline. **All 10 findings
> accepted; PLAN.md revised in place.** Round 2 reads the revised
> PLAN to verify (a) round-1 fixes propagated cleanly through the
> 821-LOC document and (b) no second-order incoherence introduced
> by round-1 revisions.
>
> **Empirical norm per v0.1.x retro Lesson 1:** R2 settles at
> 3-5 findings (`10 → 5 → 3 → 0` halving signature).
> **The canonical R2 catch:** stale propagation — fix lands at §A
> but breaks a reference at §B that round-1 didn't touch. Apply
> provenance discipline aggressively: every claim PLAN.md makes
> should be checked against current code state, not against the
> pre-revision state.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 closed; D14 R1
> closed; PLAN.md revised. The audit is on the *revised PLAN
> document* — its coherence post-R1, not the R1 dispositions
> themselves.
>
> **You are starting fresh.** This prompt and the artifacts it
> cites are everything you need; do not assume context from a
> prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main
git log --oneline -5
# expect: most recent should mention v0.2.0 D14 R1 close +
#         PLAN.md revisions
ls reporting/plans/v0_2_0/
# expect: README.md, PLAN.md, audit_findings.md,
#         codex_audit_findings_prompt.md, codex_audit_findings_response.md,
#         codex_plan_audit_prompt.md, codex_plan_audit_response.md,
#         codex_plan_audit_response_response.md (R1 closure),
#         codex_plan_audit_round_2_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**.

---

## Step 1 — Read the round-2 orientation artifacts

In order:

1. **`reporting/plans/v0_2_0/codex_plan_audit_response.md`** — your
   round-1 findings (10 items + 3 OQs).

2. **`reporting/plans/v0_2_0/codex_plan_audit_response_response.md`**
   — Claude's round-1 dispositions. **All 10 findings accepted; 3
   OQs adjudicated; PLAN.md revised in place.** Read the
   "PLAN.md revisions" subsection per finding to know exactly what
   to verify.

3. **`reporting/plans/v0_2_0/PLAN.md`** — the **revised** artifact
   (821 LOC; was 774 LOC pre-R1). Round-1 corrections are inline-
   marked with "**(Round-1 correction per F-PLAN-N: ...)**" notes.

4. **`AGENTS.md`** "Patterns the cycles have validated" — provenance
   discipline + summary-surface sweep + honest partial-closure
   naming + audit-chain settling shape. R2 is the canonical
   second-order-issue round per the empirical norm; apply
   discipline accordingly.

5. **`reporting/plans/post_v0_1_18/v0_1_x_retro.md`** §3 Lesson 1.
   The patterns: stale propagation (fix at §A breaks §B), new
   incoherence introduced by R1 wording, missing acceptance tests
   for new behaviour.

6. **The W-PROV-1 contract substrate the cycle leans on:**
   - `src/health_agent_infra/core/provenance/locator.py:23` —
     `_ALLOWED_TABLES_PK` whitelist (currently 2 tables; v0.2.0
     extends).
   - `src/health_agent_infra/core/synthesis.py:466-473` —
     `_ACCEPTED_STATE_TABLES` mapping (the round-1 F-PLAN-01
     correction source). Verify PLAN.md's §2.A whitelist matches.
   - `src/health_agent_infra/core/state/migrations/008_sync_run_log.sql:37-52`
     — `sync_run_log` schema with existing `mode` column (the
     round-1 F-PLAN-04 correction source). Verify PLAN.md's
     §2.D data-quality rollup uses `mode`.

7. **The v0.2.0 schema-group target:**
   - `reporting/plans/future_strategy_2026-04-29/review_codex.md:1480-1632`
     — `recommendation_evidence_card.v1` schema sketch +
     conflict-vocabulary at `:1597-1602` (the round-1 F-PLAN-06
     provenance source). Verify PLAN.md's §2.F sub-category table
     attributes 3-from-source / 2-W58D-added correctly.

Cross-check that every PLAN.md citation post-revision actually
exists in the tree at the cited line. **Broken cross-references
introduced by R1 fixes are the canonical R2 finding.**

---

## Step 2 — The audit questions (round 2)

### Q1. R1 fixes — did each propagate cleanly?

Verify each F-PLAN-01 through F-PLAN-10 fix per the dispositions
in `codex_plan_audit_response_response.md`:

- **F-PLAN-01 propagation.** §2.A whitelist code block (line ~166)
  uses `accepted_resistance_training_state_daily`. **Anywhere
  else in PLAN.md** that references the strength accepted-state
  table: §1.1 Thread 1, §2.D §-Aggregation queries, §4 risks
  register, §5 effort arithmetic. Did any reference get missed?
- **F-PLAN-02 propagation.** §2.A acceptance #4 metric is "5 of 5
  dormant domains." **Ship-claim gate** at §2.A end now lists
  items 1, 2, 4, 5, 6 as release-blocker — not items 1, 4, 5.
  Did the metric change reach §3.1 G1 ("All 10 active W-ids'
  release-blocker acceptance items pass")? §5 effort row?
- **F-PLAN-03 propagation.** §2.D abstain section reframes abstain
  metadata as quantitative-but-validated-outside-W58D. Does the
  new test (`test_review_weekly_abstain_metadata.py`) appear in
  §2.D acceptance items count? In §5 test-count projection? Does
  §3.1 G2 test-count target reflect?
- **F-PLAN-04 propagation.** §2.D data-quality rollup uses
  `sync_run_log.mode`. **R-V0.2.0-04 risk register** still
  references "absorb runtime_event_log error_class fix" — does
  that interact with the F-PLAN-04 mode-column choice? Any
  hidden coupling?
- **F-PLAN-05 propagation.** §1.4 schema-group description is
  "evidence-card family" = 027 + 028 only. **§4 R-V0.2.0-05** now
  says W52 ships no migration. Does §1.3 sequencing DAG (Phase 2:
  W-EVCARD-DAILY → W-EVCARD-WEEKLY) implicitly assume W52 needs a
  migration too? §-Cross-phase merge friction list?
- **F-PLAN-06 propagation.** §2.F sub-category table attributes 3
  from `review_codex.md:1599-1602`, 2 W58D-added. Headline ≥85
  known-bad. **Acceptance #2 in §2.F** raised from ≥75 to ≥85
  (was caught proactively in R1 fix-applying). Does the §3.1 G3
  threshold-formula `block_count / known_bad_count ≥ 0.97`
  correctly compute against the new ≥85 denominator? **(R2 spot-
  check: 0.97 × 85 = 82.45 → ≥83 must block. PLAN claim?)**
- **F-PLAN-07 propagation.** §3.1 G4 split into G4a + G4b. Did
  §2.F W58D acceptance gain the implementation note about
  `--scenario-set all` semantics extension? Does §-Cross-phase
  merge friction list `evals/cli.py` as a touched file?
- **F-PLAN-08 propagation.** §3.4 Abort + rollback shape
  subsection is new (37-line addition). **Does it reference each
  R-V0.2.0-* risk** by id, or just by description? Does the
  abort-trigger table cover all 5 risks consistently?
- **F-PLAN-09 propagation.** §4 R-V0.2.0-03 mitigation rewritten
  to fork-defer instead of stub-then-fill. **§3.4 abort table**
  has the matching row. **Does §2.B (W-EVCARD-DAILY) acceptance
  list any item that's secretly the stub form?** Or §2.C
  (W-EVCARD-WEEKLY)?
- **F-PLAN-10 propagation.** §1.1 Honesty boundary + §1.4 cycle
  thesis now both say "quantitative or comparative factual claim";
  §2.D acceptance #6 split (cards for quant + comp; mechanical
  qualitative-non-factual assertion). **Does W58D §2.F gate logic
  step 1 still say "atom_type ∈ {quantitative, comparative}"?
  Does W-FACT-ATOM §2.E acceptance still say "qualitative atoms
  passed through (informational, not gated)"?** Cross-check.

### Q2. Round-1 dispositions on Codex Q1-Q3 OQs — implemented?

- **Codex Q1 (append-only weekly cards).** §2.C migration 028
  schema: UNIQUE constraint dropped, `card_id` UUID-suffixed.
  §2.C acceptance #4: append-only audit history. **Does the
  §2.D W52 acceptance #6 ("weekly claim cards populated for every
  quantitative + comparative claim") interact with append-only?
  When W52 re-runs for the same week, the count assertion may
  break if old cards remain.** Verify.
- **Codex Q2 (W52 data-quality column).** Folded into F-PLAN-04;
  same propagation question as Q1.F-PLAN-04 above.
- **Codex Q3 (W-PROV-2 abort + deferred-domain shape).** §2.A
  partial-closure path names W52 suppression. **Does §2.D W52
  acceptance include a test for deferred-domain suppression?**
  PLAN proposes W52 must suppress quantitative claims for
  deferred domains; the test should fixture a W-PROV-2 partial-
  closure state DB + assert the suppression.

### Q3. New incoherence introduced by R1 fixes

The biggest risk per v0.1.x retro Lesson 1: round-1 fix introduces
new wording that conflicts with elsewhere. Spot-check:

- **§2.F sub-category table** has 3+2 split; §-Manifest-contract
  block follows. Does the §3.1 G3 acceptance threshold computation
  align with the manifest-driven approach, or does it still
  reference fixed examples? **(Round-1 fix removed "73 of 75"
  examples; verify nothing else hard-codes counts.)**
- **§3.4 Abort + rollback shape** is a 37-line new subsection.
  Did §-Cycle-pattern in any other doc reference §3 only as
  "ship gates" without the §3.4 abort half? Does §6 OQs reference
  §3.4 if relevant?
- **§2.A partial-closure path** introduces W-PROV-3 (v0.2.1
  destination). Does any other doc reference W-PROV-2 without
  acknowledging the W-PROV-3 fork-defer possibility? Tactical
  plan §6.1 row?
- **§2.C append-only schema** drops UNIQUE on `(iso_week, user_id,
  claim_id)`. Does §2.D's "count cards = count atomic claims"
  acceptance test still work? It should — count of atoms in a
  given W52 invocation maps to count of new card rows for that
  invocation, not total cards in table.

### Q4. Missing acceptance tests for new behaviour

R1 introduced new behaviour in several places. Verify each has a
test:

- F-PLAN-02 partial-closure W52 suppression: test fixture?
- F-PLAN-03 abstain-metadata deterministic-substitution: test
  named (`test_review_weekly_abstain_metadata.py`)?
- F-PLAN-09 fork-defer named-partial-closure: structural,
  documented in CARRY_OVER.md template? Per AGENTS.md "Patterns
  the cycles have validated" the convention is `partial-closure →
  v0.X+1 W-X-2`; verify PLAN matches.
- F-PLAN-10 qualitative-non-factual mechanical assertion: test
  named in §2.D acceptance #6?

### Q5. Provenance spot-verify (Q8 from R1, re-applied to revised PLAN)

Spot-verify the load-bearing external citations in revised PLAN.md:

- `core/synthesis.py:466-473` — confirm `_ACCEPTED_STATE_TABLES`
  current. F-PLAN-01 source.
- `core/state/migrations/008_sync_run_log.sql:41` — confirm `mode
  TEXT NOT NULL` current. F-PLAN-04 source.
- `core/state/migrations/001_initial.sql:281` — confirm
  `accepted_resistance_training_state_daily` table exists at this
  line. F-PLAN-01 source.
- `evals/cli.py:26-29` + `:100-138` — confirm shape-only summary +
  "no scoring until v0.2.2 W58J" wording current. F-PLAN-07 source.
- `review_codex.md:1597-1602` — confirm the 3 conflict categories
  (source-quality, x-rule, source-signal) cited. F-PLAN-06 source.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_2_0/codex_plan_audit_round_2_response.md`
matching R1's convention:

```markdown
# Codex Plan Audit Response — v0.2.0 PLAN.md (R2)

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT

**Round:** 2 / 4

## Findings (R2)

### F-PLAN-R2-01. <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4 / Q5
**Severity:** stale-propagation | new-incoherence | missing-test |
provenance-gap | nit
**Reference:** PLAN.md § X.Y, line N
**Argument:** <why this is a finding>
**Recommended response:** <revise PLAN.md as follows>

### F-PLAN-R2-02. ...

## Open questions for maintainer
```

If R2 finds 0 findings, the verdict is `PLAN_COHERENT` and the
cycle opens. Per empirical norm, expect 3-5 findings; 0-2 is
possible but unusual for a substantive PLAN at this scope.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written. 0-1 findings
  typical at this verdict level.
- **PLAN_COHERENT_WITH_REVISIONS** — 2-5 findings; revisions named;
  cycle opens after revisions land.
- **PLAN_INCOHERENT** — ≥6 findings OR ≥1 plan-incoherence-severity
  finding; PLAN re-authors before cycle opens.

---

## Step 5 — Out of scope

- **R1 dispositions themselves** — already accepted by the
  maintainer; R2 is on the *revised PLAN*, not on the R1 closure.
- **Code changes** — Phase 0 closed; implementation hasn't started.
- **v0.2.1 / v0.2.2+ scope.**
- **Phase 0 F-PHASE0-* findings.**
- **Non-maintainer foreign-user empirical evidence** — D16
  settled this.

---

## Step 6 — Cycle pattern (this audit's place)

```
v0.1.18 ship → 2026-05-06 ✓
post-v0.1.18 strategic refresh → 2026-05-06 ✓
v0.2.0 cycle workspace seeded → 2026-05-06 ✓
Phase 0 (D11) closed → 2026-05-06 ✓
PLAN.md authored → 2026-05-06 ✓
D14 R1 closed PLAN_COHERENT_WITH_REVISIONS → 2026-05-07 ✓
  (10 findings; all accepted; PLAN revised)

D14 R2 (this round):
  Round 2 ← you are here
  Empirical norm: 3-5 findings expected
  PLAN.md revises if warranted
  (loop until PLAN_COHERENT — empirical 2-4 rounds total)

(Round 3 and 4 conditional on R2 findings)

Phase 2 — Implementation (after PLAN_COHERENT)
Phase 3 — D15 IR + ship
```

Estimated review duration: 1-2 sessions (R2 is a propagation check;
faster than R1).

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_2_0/codex_plan_audit_round_2_response.md`
  (new) — your findings.
- `reporting/plans/v0_2_0/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response.
- `reporting/plans/v0_2_0/codex_plan_audit_round_3_prompt.md`
  (conditional; only if R2 returns ≥3 findings).

**No code changes.** No test runs. No state mutations.

---

*D14 round 2 plan-audit prompt authored 2026-05-07 by Claude.
Ready for Codex.*
